"""
Renders a real PNG thumbnail for every CppMode example sketch by actually
running each one in a headless browser for a moment and capturing what it
draws. These are used by the examples/index.html gallery grid (built by
regen.py) instead of any third-party screenshots.

Requires (on whichever machine actually runs this):
    pip install playwright --break-system-packages
    playwright install chromium

Usage:
    python3 generate_example_thumbnails.py

Reads every example .js file from:
    /home/pep/Projects/processing-cpp.github.io/assets/examples_js/Basics/<category>/<Example_Name>/<Example_Name>.js

Writes one PNG per example to:
    /home/pep/Projects/processing-cpp.github.io/assets/examples_thumbs/<category>/<example-slug>.png

Each sketch runs at THUMB_SIZE x THUMB_SIZE (its own createCanvas/size call
is overridden, same square-forcing approach used for the homepage preview
cards), is given RENDER_DELAY_MS to actually draw a few frames (important
for noise/animation-based sketches that build up visual complexity over
time rather than looking right on frame 0), then the canvas is captured
to a PNG and the browser page is closed before moving to the next sketch.

Sketches that load external assets (images, fonts, models, data files) are
skipped, since pointing them at the right asset path is a separate concern
from thumbnail generation and the live example pages already handle that
via fix_asset_paths() in regen.py; a half-loaded broken-image thumbnail is
worse than no thumbnail for those, so they get a generated placeholder
image instead.
"""
import os
import re
import json
from playwright.sync_api import sync_playwright

BASE_JS = "/home/pep/Projects/processing-cpp.github.io/assets/examples_js/Basics"
OUT_DIR = "/home/pep/Projects/processing-cpp.github.io/assets/examples_thumbs"

THUMB_SIZE = 220          # px, square -- the rendered thumbnail's pixel size
RENDER_DELAY_MS = 600     # let the sketch draw a few frames before capturing
PAGE_TIMEOUT_MS = 8000    # safety cutoff per sketch in case something hangs

_data_loading_re = re.compile(r"loadImage|loadFont|loadModel|loadStrings|loadJSON|loadTable|requestImage|loadXML")
_canvas_size_re = re.compile(r"(createCanvas|size)\s*\(\s*\d+\s*,\s*\d+\s*((?:,[^)]*)?)\)")


def force_square_canvas(js_code, size):
    return _canvas_size_re.sub(lambda m: f"{m.group(1)}({size},{size}{m.group(2)})", js_code, count=1)


def strip_comment(code):
    code = code.strip()
    if code.startswith("/**"):
        end = code.find("*/")
        if end != -1:
            code = code[end + 2:].strip()
    return code


def discover_examples():
    """Walk BASE_JS and return a list of {category, slug, name, js_path}."""
    examples = []
    if not os.path.isdir(BASE_JS):
        print(f"ERROR: {BASE_JS} not found.")
        return examples
    for cat in sorted(os.listdir(BASE_JS)):
        cat_path = os.path.join(BASE_JS, cat)
        if not os.path.isdir(cat_path):
            continue
        for example in sorted(os.listdir(cat_path)):
            ex_path = os.path.join(cat_path, example)
            if not os.path.isdir(ex_path):
                continue
            js_file = os.path.join(ex_path, example + ".js")
            if not os.path.exists(js_file):
                continue
            examples.append({
                "category": cat,
                "slug": example.replace("_", "-").lower(),
                "name": example.replace("_", " "),
                "js_path": js_file,
            })
    return examples


def make_placeholder_svg(label, size):
    """A plain, neutral placeholder used for sketches we deliberately skip
    (external-asset-dependent ones), so the grid still has a tile instead
    of a broken image, but it's visually distinct from a real thumbnail."""
    safe_label = (label[:18] + "…") if len(label) > 18 else label
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
        f'<rect width="100%" height="100%" fill="#1a1a1a"/>'
        f'<text x="50%" y="50%" fill="#666" font-family="monospace" font-size="13" '
        f'text-anchor="middle" dominant-baseline="middle">{safe_label}</text>'
        f"</svg>"
    )


def render_thumbnail(browser, js_code, out_path, debug_label=""):
    """Renders one sketch in a brand-new, isolated page (never reused
    across sketches -- p5 in global mode attaches setup/draw/state onto
    window, and reusing a page via set_content() can leak the previous
    sketch's globals into the next one, which is why earlier runs saw
    every sketch after the first one fail to produce a canvas).

    Also simulates some mouse movement and a couple of key presses partway
    through the render delay, so sketches that react to mouseX/mouseY,
    mousePressed, or keyPressed look more like what a person would
    actually see, rather than a frozen idle/default frame.
    """
    sized_js = force_square_canvas(js_code, THUMB_SIZE)
    safe = sized_js.replace("</script>", "<\\/script>").replace("`", "\\`")

    html = f"""<!DOCTYPE html>
<html><head><style>*{{margin:0;padding:0;}}body{{overflow:hidden;background:#000;}}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"></script>
</head><body><script>{safe}</script></body></html>"""

    page = browser.new_page(viewport={"width": THUMB_SIZE, "height": THUMB_SIZE})
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: console_errors.append(f"pageerror: {exc}"))

    try:
        page.set_content(html, timeout=PAGE_TIMEOUT_MS)

        # Let the sketch initialize and draw its first few frames before
        # any simulated input, so setup() has definitely finished.
        page.wait_for_timeout(RENDER_DELAY_MS // 3)

        # Simulate smooth mouse movement across the canvas in a few steps
        # (not one big jump) so mouseX/mouseY-driven sketches, easing,
        # and drag-style examples show motion rather than a static
        # default position. Centered roughly so off-canvas-only-reacting
        # sketches still get a representative pass through the middle.
        try:
            steps = [
                (THUMB_SIZE * 0.2, THUMB_SIZE * 0.8),
                (THUMB_SIZE * 0.5, THUMB_SIZE * 0.3),
                (THUMB_SIZE * 0.8, THUMB_SIZE * 0.6),
                (THUMB_SIZE * 0.5, THUMB_SIZE * 0.5),
            ]
            for x, y in steps:
                page.mouse.move(x, y, steps=8)
                page.wait_for_timeout(80)
            # A short press-and-release partway through, for
            # mousePressed()/mouseReleased()-driven sketches.
            page.mouse.down()
            page.wait_for_timeout(60)
            page.mouse.up()
        except Exception:
            pass  # input simulation is best-effort; never let it abort the render

        # A couple of representative key presses for keyPressed()-driven
        # sketches (arrow keys are common in the Basics examples for
        # movement/selection; space is common for toggling/advancing).
        try:
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(60)
            page.keyboard.press("Space")
        except Exception:
            pass

        page.wait_for_timeout(RENDER_DELAY_MS // 2)

        canvas = page.query_selector("canvas")
        if canvas is None:
            if console_errors:
                print(f"    [{debug_label}] no canvas; console errors: {console_errors[:3]}")
            return False
        canvas.screenshot(path=out_path)
        return True
    finally:
        page.close()


def main():
    examples = discover_examples()
    print(f"Found {len(examples)} example sketches.")

    os.makedirs(OUT_DIR, exist_ok=True)

    manifest = []
    rendered = 0
    skipped = 0
    failed = []

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for ex in examples:
            cat_out_dir = os.path.join(OUT_DIR, ex["category"])
            os.makedirs(cat_out_dir, exist_ok=True)
            out_path = os.path.join(cat_out_dir, ex["slug"] + ".png")

            with open(ex["js_path"], errors="replace") as f:
                js_code = strip_comment(f.read())

            if _data_loading_re.search(js_code):
                # Don't attempt to render -- write a placeholder so the
                # grid tile exists, but flag it clearly in the manifest.
                svg = make_placeholder_svg(ex["name"], THUMB_SIZE)
                with open(out_path.replace(".png", ".svg"), "w") as f:
                    f.write(svg)
                manifest.append({**ex, "thumb": ex["slug"] + ".svg", "placeholder": True})
                skipped += 1
                continue

            try:
                ok = render_thumbnail(browser, js_code, out_path, debug_label=f"{ex['category']}/{ex['slug']}")
                if ok:
                    manifest.append({**ex, "thumb": ex["slug"] + ".png", "placeholder": False})
                    rendered += 1
                    print(f"  rendered: {ex['category']}/{ex['slug']}")
                else:
                    failed.append(ex["slug"])
                    print(f"  FAILED (no canvas found): {ex['category']}/{ex['slug']}")
            except Exception as e:
                failed.append(ex["slug"])
                print(f"  FAILED ({e}): {ex['category']}/{ex['slug']}")

        browser.close()

    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print()
    print(f"Rendered: {rendered}")
    print(f"Skipped (external-asset placeholder): {skipped}")
    print(f"Failed: {len(failed)}")
    for slug in failed:
        print(f"  - {slug}")
    print(f"Manifest written to {manifest_path}")
    print("Run regen.py next to rebuild examples/index.html using these thumbnails.")


if __name__ == "__main__":
    main()
