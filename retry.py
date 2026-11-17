"""
Retries thumbnail generation for any example that failed or was skipped
in the last run of generate_example_thumbnails.py.

An example is considered "needs retry" if:
  - It exists in examples_js/ but has no entry in manifest.json at all
    (crashed before it could be recorded, or was never attempted)
  - Its manifest entry has placeholder=True with reason="non_js_source"
    is NOT retried -- that's a real content bug, not a transient failure
  - Its manifest entry has placeholder=True without a reason IS retried
    if --retry-placeholders flag is passed (off by default, since most
    placeholders are intentional skips for data-loading sketches)

Usage:
    python3 retry_thumbnails.py
    python3 retry_thumbnails.py --retry-placeholders
"""

import os
import sys
import json
import argparse

# ── reuse everything from the main script ──────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
import generate_example_thumbnails as gen
from playwright.sync_api import sync_playwright

MANIFEST_PATH = os.path.join(gen.OUT_DIR, "manifest.json")


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        print("No manifest found -- run generate_example_thumbnails.py first.")
        return {}
    with open(MANIFEST_PATH) as f:
        entries = json.load(f)
    # Key on (section, slug) matching the new multi-section format
    return {
        (e.get("section", "Basics"), e["slug"]): e
        for e in entries
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--retry-placeholders",
        action="store_true",
        help="Also retry intentional placeholder entries (sketches that load "
             "external assets). Off by default since most are genuine skips.",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    all_examples = gen.discover_examples()

    to_retry = []
    for ex in all_examples:
        key = (ex["section"], ex["slug"])
        entry = manifest.get(key)

        if entry is None:
            # Never made it into the manifest at all -- definite failure
            to_retry.append((ex, "not in manifest"))
            continue

        if entry.get("placeholder"):
            reason = entry.get("reason", "")
            if reason == "non_js_source":
                # Real content bug -- skip, can't fix by retrying
                continue
            if args.retry_placeholders:
                to_retry.append((ex, "placeholder retry requested"))

    if not to_retry:
        print("Nothing to retry. All examples are in the manifest.")
        return

    print(f"Retrying {len(to_retry)} example(s):")
    for ex, reason in to_retry:
        print(f"  {ex['section']}/{ex['category']}/{ex['slug']}  ({reason})")
    print()

    # Load the full manifest to update it in place
    all_entries = list(manifest.values())
    all_keys = set(manifest.keys())

    asset_base_url, asset_httpd = gen.start_local_asset_server(gen.ASSETS_DIR)
    print(f"Serving assets locally at {asset_base_url}")

    succeeded = 0
    still_failed = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            for ex, _ in to_retry:
                cat_out_dir = os.path.join(gen.OUT_DIR, ex["section"], ex["category"])
                os.makedirs(cat_out_dir, exist_ok=True)
                out_path = os.path.join(cat_out_dir, ex["slug"] + ".png")

                with open(ex["js_path"], errors="replace") as f:
                    js_code = gen.strip_comment(f.read())

                if gen._non_js_source_re.search(js_code):
                    print(f"  SKIP (unconverted source): {ex['section']}/{ex['slug']}")
                    continue

                if gen._data_loading_re.search(js_code):
                    svg = gen.make_placeholder_svg(ex["name"], gen.THUMB_SIZE)
                    with open(out_path.replace(".png", ".svg"), "w") as f:
                        f.write(svg)
                    new_entry = {**ex, "thumb": ex["slug"] + ".svg", "placeholder": True}
                    _upsert(all_entries, all_keys, ex, new_entry)
                    print(f"  placeholder: {ex['section']}/{ex['slug']}")
                    continue

                is_no_canvas = bool(gen._no_canvas_re.search(js_code))

                try:
                    ok = gen.render_thumbnail(
                        browser, js_code, out_path, asset_base_url,
                        debug_label=f"{ex['section']}/{ex['category']}/{ex['slug']}",
                        is_no_canvas=is_no_canvas,
                    )
                    if ok:
                        new_entry = {**ex, "thumb": ex["slug"] + ".png", "placeholder": False}
                        _upsert(all_entries, all_keys, ex, new_entry)
                        succeeded += 1
                        print(f"  rendered: {ex['section']}/{ex['slug']}")
                    else:
                        still_failed.append(ex["slug"])
                        print(f"  FAILED: {ex['section']}/{ex['slug']}")
                except Exception as e:
                    still_failed.append(ex["slug"])
                    print(f"  FAILED ({e}): {ex['section']}/{ex['slug']}")

            browser.close()
    finally:
        asset_httpd.shutdown()

    with open(MANIFEST_PATH, "w") as f:
        json.dump(all_entries, f, indent=2)

    print()
    print(f"Succeeded: {succeeded}")
    print(f"Still failed: {len(still_failed)}")
    for slug in still_failed:
        print(f"  - {slug}")
    print(f"Manifest updated: {MANIFEST_PATH}")


def _upsert(all_entries, all_keys, ex, new_entry):
    """Replace an existing manifest entry in-place, or append if new."""
    key = (ex.get("section", "Basics"), ex["slug"])
    for i, e in enumerate(all_entries):
        if (e.get("section", "Basics"), e["slug"]) == key:
            all_entries[i] = new_entry
            return
    all_entries.append(new_entry)
    all_keys.add(key)


if __name__ == "__main__":
    main()
