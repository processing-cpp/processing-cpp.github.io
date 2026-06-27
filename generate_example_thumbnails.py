"""
Renders a real PNG thumbnail for every CppMode example sketch by actually
running each one in a headless browser for a moment and capturing what it
draws. These are used by the examples/index.html gallery grid (built by
regen.py) instead of any third-party screenshots.

Requires (on whichever machine actually runs this):
    pip install playwright pillow --break-system-packages
    playwright install chromium

Usage:
    python3 generate_example_thumbnails.py

Reads every example .js file from:
    /home/pep/Projects/processing-cpp.github.io/assets/examples_js/Basics/<category>/<Example_Name>/<Example_Name>.js

Writes one PNG per example to:
    /home/pep/Projects/processing-cpp.github.io/assets/examples_thumbs/<category>/<example-slug>.png

Each sketch renders at its OWN actual size (read from its createCanvas/size
call, same convention regen.py already uses), not forced into a square --
forcing non-square sketches into THUMB_SIZE x THUMB_SIZE distorted their
framing and cropped content out. The full-size screenshot is then scaled
down and letterboxed into a THUMB_SIZE x THUMB_SIZE square afterward (black
bars added on whichever axis is shorter), so the entire original drawing
is always visible in the thumbnail, never cropped or squished.

Sketches are given RENDER_DELAY_MS to actually draw a few frames (important
for noise/animation-based sketches that build up visual complexity over
time rather than looking right on frame 0), then the canvas is captured
and the browser page is closed before moving to the next sketch.

Sketches that call loadImage/loadFont/loadModel have their asset paths
rewritten to the real hosted URL (same fix_asset_paths() approach already
used for the full example pages in regen.py), so they render with their
real images instead of being skipped. Sketches that load actual *data*
(loadStrings/loadJSON/loadTable/loadXML/requestImage) or fetch external
non-canvas content (fetch()/noCanvas()) still get a placeholder tile,
since there's nothing meaningfully visual to screenshot for those in this
standalone context.
"""
import os
import re
import json
import base64
import socket
import threading
import http.server
import functools
from playwright.sync_api import sync_playwright
from PIL import Image
import io

REPO_ROOT = "/home/pep/Projects/processing-cpp.github.io"
BASE_JS = os.path.join(REPO_ROOT, "assets/examples_js/Basics")
OUT_DIR = os.path.join(REPO_ROOT, "assets/examples_thumbs")
ASSETS_DIR = os.path.join(REPO_ROOT, "assets")

THUMB_SIZE = 220          # px, square -- the final letterboxed thumbnail size
MAX_RENDER_DIM = 800      # cap on native width/height actually rendered, for speed
RENDER_DELAY_MS = 600     # let the sketch draw a few frames before capturing
PAGE_TIMEOUT_MS = 8000    # safety cutoff per sketch in case something hangs

# Sketches that load actual *data* (not images) -- nothing meaningfully
# visual to screenshot for these in a standalone context, so they get a
# placeholder tile instead of being attempted. Note: fetch() alone is NOT
# included here -- several real examples (e.g. Shape_Vertices) use fetch()
# to load SVG path data while still drawing normally to a real canvas, so
# excluding on fetch() alone would wrongly skip a renderable sketch. Only
# noCanvas() reliably means there's no canvas to capture at all, which is
# handled separately below via a page-level (not canvas) screenshot.
_data_loading_re = re.compile(
    r"loadStrings|loadJSON|loadTable|requestImage|loadXML"
)

_no_canvas_re = re.compile(r"\bnoCanvas\s*\(")

# loadImage/loadFont/loadModel ARE attempted (not skipped) -- their asset
# paths just need rewriting to a real reachable URL first, same general
# idea as fix_asset_paths() in regen.py, except this points at a LOCAL
# server (see start_local_asset_server below) reading straight from disk,
# not the live deployed site. Using the live URL would mean thumbnails
# silently 404 for any asset that's been added/changed locally but not
# yet pushed -- exactly what happened with rocket.obj. Reading from disk
# means thumbnails always reflect what's actually on disk right now.
_asset_load_re = re.compile(r"""load(Image|Font|Model)\s*\(\s*["']([^"']+)["']\s*((?:,[^)]*)?)\)""")


def fix_asset_paths(js_code, asset_base_url):
    """Rewrite relative loadImage/loadFont/loadModel filenames to a real
    reachable asset URL, so sketches that load their own images actually
    have something to load when rendered standalone (outside the real
    example page, which normally handles this rewrite itself)."""
    def replacer(m):
        return f'load{m.group(1)}("{asset_base_url}{m.group(2)}"{m.group(3)})'
    return _asset_load_re.sub(replacer, js_code)


class _CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler, but with Access-Control-Allow-Origin: *
    on every response. Plain SimpleHTTPRequestHandler sends no CORS
    headers at all, which works fine for plain <img>/<script> tag loads
    but breaks anything using fetch() or an Image with crossOrigin set --
    both of which several real example sketches do (e.g. SVG-loading
    shape examples use fetch() directly, and p5's own loadImage() sets
    crossOrigin='anonymous', which then requires a real CORS header even
    though the request would otherwise succeed). The live, deployed site
    works for these today because GitHub Pages sends
    Access-Control-Allow-Origin: * for all public content by default;
    this matches that behavior locally."""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # quiet -- the per-request access log lines aren't useful here


def start_local_asset_server(directory, preferred_port=8765):
    """
    Starts a small local HTTP server serving `directory` (the repo's
    assets/ folder) in a background thread, on the first free port found
    starting at preferred_port. Returns (base_url, httpd) -- base_url is
    e.g. "http://127.0.0.1:8765/data/", already including the trailing
    "data/" so it can be used as a drop-in ASSET_BASE_URL. Call
    httpd.shutdown() when done.

    Sends Access-Control-Allow-Origin: * on every response (see
    _CORSRequestHandler), matching how the real deployed site behaves
    (GitHub Pages sends the same header for all public content) -- without
    this, fetch()-based loads and p5's own crossOrigin-tagged image loads
    get blocked by the browser even though the file itself loads fine.

    Using a real http:// origin (rather than page.set_content()'s null
    origin) also means no opaque-origin edge cases for canvas tainting,
    on top of the main benefit of reading straight from disk.
    """
    handler = functools.partial(_CORSRequestHandler, directory=directory)

    port = preferred_port
    httpd = None
    for _ in range(20):
        try:
            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            port += 1
    if httpd is None:
        raise RuntimeError("Could not find a free port for the local asset server.")

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}/data/"
    return base_url, httpd

# Catches files that are actually still Processing/Java (.pde) source sitting
# in the examples_js tree by mistake -- e.g. "int xvals[640];" or
# "void setup() {" -- rather than real JavaScript. Attempting to run these
# as JS produces a confusing "Unexpected identifier" page error; this lets
# us flag it clearly as a content/data bug instead.
_non_js_source_re = re.compile(
    r"^\s*(int|float|boolean|void|String|char)\s+\w+(\[\d*\])?\s*(=|;|\()"
    r"|^\s*void\s+(setup|draw)\s*\(\s*\)\s*\{",
    re.M,
)

_canvas_size_detect_re = re.compile(r"(?:createCanvas|size)\s*\(\s*(\d+)\s*,\s*(\d+)")


def detect_canvas_size(js_code):
    """Read the sketch's own requested width/height (without rewriting
    it) so it can be rendered at its real native size and aspect ratio,
    instead of being forced into a square that distorts framing and
    crops content out. Falls back to 640x360 (the common Processing
    default) if no createCanvas/size call is found."""
    m = _canvas_size_detect_re.search(js_code)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        # Cap render size for speed/sanity; the letterbox step downscales
        # afterward regardless, so a huge native canvas doesn't need to
        # be rendered at full resolution to produce a good thumbnail.
        scale = min(1.0, MAX_RENDER_DIM / max(w, h))
        return max(1, int(w * scale)), max(1, int(h * scale))
    return 640, 360


def letterbox_to_square(png_bytes, size):
    """Scales the given PNG image down (preserving aspect ratio) to fit
    entirely within a size x size square, then pads the shorter axis with
    black bars so the result is exactly square and the whole original
    image is always visible -- never cropped, never squished."""
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    img.thumbnail((size, size), Image.LANCZOS)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    canvas.paste(img, offset, img if img.mode == "RGBA" else None)
    return canvas


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


def render_thumbnail(browser, js_code, out_path, asset_base_url, debug_label="", is_no_canvas=False):
    """Renders one sketch in a brand-new, isolated page (never reused
    across sketches -- p5 in global mode attaches setup/draw/state onto
    window, and reusing a page via set_content() can leak the previous
    sketch's globals into the next one, which is why earlier runs saw
    every sketch after the first one fail to produce a canvas).

    Renders at the sketch's own native canvas size/aspect ratio (see
    detect_canvas_size), then letterboxes the result down to a
    THUMB_SIZE x THUMB_SIZE square afterward, so nothing gets cropped or
    squished regardless of the sketch's original proportions.

    Also simulates some mouse movement and a couple of key presses partway
    through the render delay, so sketches that react to mouseX/mouseY,
    mousePressed, or keyPressed look more like what a person would
    actually see, rather than a frozen idle/default frame.

    is_no_canvas: set for sketches that call noCanvas() and render
    directly into the page (e.g. injecting an <svg> into document.body)
    instead of drawing to a <canvas>. These are captured via a normal
    page screenshot of the viewport instead of canvas.toDataURL(), since
    there's no canvas element to read pixels from.
    """
    render_w, render_h = detect_canvas_size(js_code)
    fixed_js = fix_asset_paths(js_code, asset_base_url)
    safe = fixed_js.replace("</script>", "<\\/script>").replace("`", "\\`")

    html = f"""<!DOCTYPE html>
<html><head><style>*{{margin:0;padding:0;}}body{{overflow:hidden;background:#000;}}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"></script>
</head><body><script>{safe}</script></body></html>"""

    page = browser.new_page(viewport={"width": render_w, "height": render_h})
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
        # default position. Scaled to the sketch's own render size now
        # that it's no longer forced to a fixed square.
        center_x, center_y = render_w / 2, render_h / 2
        try:
            steps = [
                (render_w * 0.2, render_h * 0.8),
                (render_w * 0.5, render_h * 0.3),
                (render_w * 0.8, render_h * 0.6),
            ]
            for x, y in steps:
                page.mouse.move(x, y, steps=8)
                page.wait_for_timeout(80)
            # A short press-and-release at center, for
            # mousePressed()/mouseReleased()-driven sketches.
            page.mouse.move(center_x, center_y, steps=8)
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

        # Explicitly rest the mouse at the exact canvas center right
        # before the final wait + capture, regardless of where the wander
        # sequence above left it. This is what mouseX/mouseY will read as
        # of the screenshot, for any sketch whose draw() loop reacts to
        # cursor position -- centered rather than wherever the simulated
        # wander happened to end up. Note: this only sets a synthetic
        # coordinate p5 reads; no actual OS cursor icon is rendered in a
        # headless screenshot regardless, so there's nothing to hide.
        try:
            page.mouse.move(center_x, center_y, steps=4)
        except Exception:
            pass

        page.wait_for_timeout(RENDER_DELAY_MS // 2)

        if is_no_canvas:
            # No <canvas> element exists -- the sketch draws straight into
            # the page (e.g. injecting an <svg>). Capture the viewport
            # itself via a normal page screenshot instead.
            try:
                png_bytes = page.screenshot(timeout=PAGE_TIMEOUT_MS)
            except Exception as e:
                print(f"    [{debug_label}] page screenshot failed: {e}")
                if console_errors:
                    print(f"    [{debug_label}] console errors: {console_errors[:3]}")
                return False
            thumb = letterbox_to_square(png_bytes, THUMB_SIZE)
            thumb.save(out_path)
            return True

        canvas = page.query_selector("canvas")
        if canvas is None:
            if console_errors:
                print(f"    [{debug_label}] no canvas; console errors: {console_errors[:3]}")
            return False

        # Capture via canvas.toDataURL() inside the page rather than
        # Playwright's element.screenshot(). The latter first waits for
        # the element to be considered "visible" (stable layout, nonzero
        # opacity, in the viewport, etc.) before it will take the shot --
        # a check that WebGL canvases (createCanvas(..., WEBGL)) can fail
        # or take a very long time to satisfy in headless mode, which is
        # what caused the 30s timeout / "element is not visible" retries.
        # Reading pixels directly via toDataURL has no such visibility
        # precondition and works the same way for both 2D and WebGL
        # canvases.
        try:
            data_url = page.evaluate(
                "() => document.querySelector('canvas').toDataURL('image/png')"
            )
        except Exception as e:
            print(f"    [{debug_label}] toDataURL capture failed: {e}")
            return False

        if not data_url or not data_url.startswith("data:image/png;base64,"):
            print(f"    [{debug_label}] toDataURL returned unexpected content (possibly a tainted "
                  f"canvas from cross-origin content).")
            return False

        png_bytes = base64.b64decode(data_url.split(",", 1)[1])
        thumb = letterbox_to_square(png_bytes, THUMB_SIZE)
        thumb.save(out_path)
        return True
    finally:
        page.close()


def main():
    examples = discover_examples()
    print(f"Found {len(examples)} example sketches.")

    os.makedirs(OUT_DIR, exist_ok=True)

    if not os.path.isdir(ASSETS_DIR):
        print(f"ERROR: {ASSETS_DIR} not found -- can't serve local assets.")
        return

    asset_base_url, asset_httpd = start_local_asset_server(ASSETS_DIR)
    print(f"Serving {ASSETS_DIR} locally at {asset_base_url} "
          f"(reads straight from disk -- no dependency on what's been pushed live).")

    manifest = []
    rendered = 0
    skipped = 0
    failed = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            for ex in examples:
                cat_out_dir = os.path.join(OUT_DIR, ex["category"])
                os.makedirs(cat_out_dir, exist_ok=True)
                out_path = os.path.join(cat_out_dir, ex["slug"] + ".png")

                with open(ex["js_path"], errors="replace") as f:
                    js_code = strip_comment(f.read())

                if _non_js_source_re.search(js_code):
                    # This .js file looks like it's actually still Processing/Java
                    # (.pde) source -- e.g. "int xvals[640];" -- not real
                    # JavaScript. This is a content bug in examples_js (the .js
                    # translation likely was never generated for this example),
                    # not something to paper over silently.
                    print(f"  WARNING: {ex['category']}/{ex['slug']} -- {ex['js_path']} looks like "
                          f"unconverted Processing/Java source, not JavaScript. Skipping with a "
                          f"placeholder; fix the .js file at the source to get a real thumbnail.")
                    svg = make_placeholder_svg(ex["name"], THUMB_SIZE)
                    with open(out_path.replace(".png", ".svg"), "w") as f:
                        f.write(svg)
                    manifest.append({**ex, "thumb": ex["slug"] + ".svg", "placeholder": True, "reason": "non_js_source"})
                    skipped += 1
                    continue

                if _data_loading_re.search(js_code):
                    # Don't attempt to render -- write a placeholder so the
                    # grid tile exists, but flag it clearly in the manifest.
                    svg = make_placeholder_svg(ex["name"], THUMB_SIZE)
                    with open(out_path.replace(".png", ".svg"), "w") as f:
                        f.write(svg)
                    manifest.append({**ex, "thumb": ex["slug"] + ".svg", "placeholder": True})
                    skipped += 1
                    continue

                is_no_canvas = bool(_no_canvas_re.search(js_code))

                try:
                    ok = render_thumbnail(
                        browser, js_code, out_path, asset_base_url,
                        debug_label=f"{ex['category']}/{ex['slug']}",
                        is_no_canvas=is_no_canvas,
                    )
                    if ok:
                        manifest.append({**ex, "thumb": ex["slug"] + ".png", "placeholder": False})
                        rendered += 1
                        print(f"  rendered: {ex['category']}/{ex['slug']}" + (" (page capture, no canvas)" if is_no_canvas else ""))
                    else:
                        failed.append(ex["slug"])
                        reason = "page screenshot failed" if is_no_canvas else "no canvas found"
                        print(f"  FAILED ({reason}): {ex['category']}/{ex['slug']}")
                except Exception as e:
                    failed.append(ex["slug"])
                    print(f"  FAILED ({e}): {ex['category']}/{ex['slug']}")

            browser.close()
    finally:
        asset_httpd.shutdown()

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
