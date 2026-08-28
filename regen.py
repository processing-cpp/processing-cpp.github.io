import os, re, json

EXAMPLES_ROOT = "/home/pep/Projects/processing-cpp.github.io/assets/examples"
EXAMPLES_JS_ROOT = "/home/pep/Projects/processing-cpp.github.io/assets/examples_js"

def strip_comment(code):
    code = code.strip()
    if code.startswith("/**"):
        end = code.find("*/")
        if end != -1:
            code = code[end+2:].strip()
    return code

def get_canvas_size(js_code):
    m = re.search(r'createCanvas\s*\(\s*(\d+)\s*,\s*(\d+)', js_code)
    if m: return int(m.group(1)), int(m.group(2))
    m = re.search(r'\bsize\s*\(\s*(\d+)\s*,\s*(\d+)', js_code)
    if m: return int(m.group(1)), int(m.group(2))
    return 640, 360

def scan_section(section_name):
    """
    Scans assets/examples/<section_name>/<category>/<Example>/<Example>.pde
    (and the matching assets/examples_js/<section_name>/... for the JS
    translation, if it exists yet) into the same {category: [examples]}
    shape the rest of this script already expects from `data`.

    Used for both "Basics" (the only section with content today) and
    "Topics" (currently empty placeholder folders -- this picks it up
    automatically the moment real .pde/.js files are added, with zero
    further changes needed here).
    """
    base_cpp = os.path.join(EXAMPLES_ROOT, section_name)
    base_js = os.path.join(EXAMPLES_JS_ROOT, section_name)
    if not os.path.isdir(base_cpp):
        return {}

    section_data = {}
    for cat in sorted(os.listdir(base_cpp)):
        cat_path = os.path.join(base_cpp, cat)
        if not os.path.isdir(cat_path):
            continue
        examples = []
        for example in sorted(os.listdir(cat_path)):
            ex_path = os.path.join(cat_path, example)
            if not os.path.isdir(ex_path):
                continue
            pde = os.path.join(ex_path, example + ".pde")
            if not os.path.exists(pde):
                continue
            with open(pde) as f:
                code = f.read()
            js_file = os.path.join(base_js, cat, example, example + ".js")
            js_code = ""
            w, h = 640, 360
            if os.path.exists(js_file):
                with open(js_file) as f:
                    js_code = strip_comment(f.read())
                w, h = get_canvas_size(js_code)
            slug = example.replace("_", "-").lower()
            examples.append({
                "id": section_name + "_" + cat + "_" + example,
                "name": example.replace("_", " "),
                "slug": slug,
                "code": code,
                "js": js_code,
                "w": w,
                "h": h,
            })
        if examples:  # skip categories that exist as empty folders with no real content yet
            section_data[cat] = examples
    return section_data


# Every top-level folder under assets/examples/ is treated as a section
# (e.g. "Basics", "Topics") -- discovered automatically, not hardcoded, so
# adding real content under an existing empty Topics/<category>/ folder
# is all that's needed to make it show up here; no script change required.
SECTION_NAMES = sorted(os.listdir(EXAMPLES_ROOT)) if os.path.isdir(EXAMPLES_ROOT) else []
sections = {}
for _section_name in SECTION_NAMES:
    if not os.path.isdir(os.path.join(EXAMPLES_ROOT, _section_name)):
        continue
    scanned = scan_section(_section_name)
    if scanned:  # only keep sections that actually have at least one real example
        sections[_section_name] = scanned

# `data` is kept as an alias for the first/primary section (normally
# "Basics") for backwards compatibility with anything below that hasn't
# been updated to iterate over `sections` yet.
data = sections.get("Basics", {})

def build_page_sidebar(active_id=""):
    s = ""
    for i, (section_name, section_data) in enumerate(sections.items()):
        key = section_name.lower()
        # First section starts open, the rest start collapsed -- matches
        # the original Basics-open/Topics-collapsed behavior.
        open_by_default = True
        arrow = "▾"
        display = "block"
        s += (
            f'<div class="section-header" onclick="toggleSection(\'{key}\')">'
            f'<span>{section_name}</span><span class="arrow" id="{key}-arrow">{arrow}</span></div>'
            f'<div id="{key}-section" style="display:{display}">'
        )
        for cat, examples in section_data.items():
            s += f'<div class="category"><div class="category-title">{cat.replace("_"," ").title()}</div>'
            for ex in examples:
                active = 'class="active"' if ex["id"] == active_id else ""
                s += f'<a href="{ex["slug"]}.html" {active}>{ex["name"]}</a>'
            s += '</div>'
        s += '</div>'

    # Any section folder that exists but has no real example content yet
    # (e.g. Topics before its .pde/.js files are added) still gets a
    # collapsed "Coming soon" entry, so the sidebar doesn't just silently
    # omit it.
    empty_sections = [
        name for name in SECTION_NAMES
        if name not in sections and os.path.isdir(os.path.join(EXAMPLES_ROOT, name))
    ]
    for name in empty_sections:
        key = name.lower()
        s += (
            f'<div class="section-header" onclick="toggleSection(\'{key}\')">'
            f'<span>{name}</span><span class="arrow" id="{key}-arrow">▸</span></div>'
            f'<div id="{key}-section" style="display:none">'
            f'<div class="category"><div class="category-title" style="color:#ccc;">Coming soon</div></div></div>'
        )
    return s

shared_css = '''* { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111; background: #fff; }
    a { color: #111; text-decoration: none; }
    nav { border-bottom: 1px solid #e0e0e0; padding: 0 2rem; display: flex; align-items: center; justify-content: space-between; height: 60px; position: sticky; top: 0; background: #fff; z-index: 100; }
    .hamburger { background: none; border: none; cursor: pointer; font-size: 22px; padding: 4px 8px; display: none; }
    .layout { display: flex; min-height: calc(100vh - 60px); }
    .sidebar-outer { width: 220px; min-width: 220px; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; position: sticky; top: 60px; height: calc(100vh - 60px); }
    #site-sidebar { padding: 1.5rem 1.5rem 1rem; border-bottom: 1px solid #e0e0e0; display: flex; flex-direction: column; }
    #site-sidebar a { font-size: 14px; color: #555; padding: 0.4rem 0; display: block; }
    #site-sidebar a:hover { color: #111; }
    #site-sidebar a.active { color: #111; font-weight: 500; }
    .sidebar-examples { flex: 1; overflow-y: auto; }
    .section-header { display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 1.5rem; font-size: 13px; font-weight: 600; color: #111; cursor: pointer; border-bottom: 1px solid #e0e0e0; user-select: none; }
    .section-header:hover { background: #f8f8f8; }
    .arrow { font-size: 11px; color: #aaa; }
    .category { margin-bottom: 0.25rem; }
    .category-title { font-size: 11px; font-weight: 600; color: #aaa; text-transform: uppercase; letter-spacing: 0.08em; padding: 0.75rem 1.5rem 0.25rem; }
    .category a { display: block; font-size: 13px; color: #555; padding: 0.3rem 1.5rem; }
    .category a:hover { color: #111; background: #f8f8f8; }
    .category a.active { color: #111; font-weight: 500; background: #f4f4f4; }
    .content { flex: 1; padding: 3rem 4rem; max-width: 900px; }
    .content h1 { font-size: 1.8rem; font-weight: 600; margin-bottom: 0.75rem; color: #e8b400; }
    .preview-wrap { border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; margin-bottom: 2rem; display: block; max-width: 100%; width: fit-content; }
    .preview-wrap iframe { display: block; border: none; max-width: 100%; }
    .code-block { background: #f8f8f8; border-radius: 8px; overflow: hidden; }
    .code-header { padding: 0.75rem 1.25rem; border-bottom: 1px solid #e0e0e0; font-size: 12px; color: #888; font-family: monospace; display: flex; align-items: center; justify-content: space-between; }
    .copy-btn { font-size: 12px; color: #555; background: #fff; border: 1px solid #ddd; border-radius: 4px; padding: 3px 10px; cursor: pointer; font-family: inherit; }
    .copy-btn:hover { background: #f0f0f0; }
    .copy-btn.copied { color: #090; border-color: #090; }
    pre { padding: 0.75rem 1rem; font-family: "SF Mono","Fira Code",monospace; font-size: 13px; line-height: 1.6; overflow-x: auto; white-space: pre; background: #0d0d0d; color: #ccc; border-radius: 8px; margin-bottom: 1.25rem; }
    .welcome h1 { font-size: 1.8rem; font-weight: 600; margin-bottom: 1rem; }
    .welcome p { color: #555; line-height: 1.8; max-width: 500px; }
    footer { border-top: 1px solid #e0e0e0; padding: 2rem; text-align: center; font-size: 13px; color: #888; }
    .footer-contact { margin-top: 0.4rem; font-size: 12px; }
    .footer-contact a { color: #aaa; border-bottom: 1px solid transparent; }
    .footer-contact a:hover { color: #111; border-bottom-color: #111; }
    .footer-sep { color: #ccc; margin: 0 0.5rem; }
    @media (max-width: 768px) {
      .hamburger { display: block; }
      .sidebar-outer { position: fixed; top: 60px; left: -240px; width: 240px; height: calc(100vh - 60px); background: #fff; z-index: 200; transition: left 0.25s ease; box-shadow: 2px 0 12px rgba(0,0,0,0.08); }
      .sidebar-outer.open { left: 0; }
      .content { padding: 2rem 1.25rem; }
      .preview-wrap { max-width: 100%; }
      pre { font-size: 12px; }
    }'''

shared_js = '''function copyCode() {
  navigator.clipboard.writeText(document.getElementById('code-pre').innerText).then(() => {
    const btn = document.querySelector('.copy-btn');
    btn.textContent = 'Copied!'; btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}
function toggleSection(name) {
  const sec = document.getElementById(name+'-section');
  const arrow = document.getElementById(name+'-arrow');
  const open = sec.style.display !== 'none';
  sec.style.display = open ? 'none' : 'block';
  arrow.textContent = open ? '▸' : '▾';
}'''

def fix_asset_paths(js_code):
    base = "https://processing-cpp.github.io/assets/data/"
    pat = re.compile(r"""load(Image|Font|Model)\s*\(\s*["']([^"']+)["']\s*((?:,[^)]*)?)\)""")
    def replacer(m):
        return f'load{m.group(1)}("{base}{m.group(2)}"{m.group(3)})'
    return pat.sub(replacer, js_code)

def make_iframe(js_code, w, h):
    js_code = fix_asset_paths(js_code)
    safe = js_code.replace('</script>', '<\\/script>').replace('`','\\`')
    return f'''<div class="preview-wrap" style="aspect-ratio:{w}/{h};max-width:{w}px;"><iframe id="sketch-frame" width="{w}" height="{h}" style="display:block;border:none;"></iframe></div>
<script>(function(){{const iframe=document.getElementById('sketch-frame');const doc=iframe.contentDocument||iframe.contentWindow.document;doc.open();doc.write(`<!DOCTYPE html><html><head><style>*{{margin:0;padding:0;}}body{{overflow:hidden;}}</style><script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"><\\/script></head><body><script>{safe}<\\/script></body></html>`);doc.close();}})();</script>'''

out_dir = "/home/pep/Projects/processing-cpp.github.io/examples"
for fname in os.listdir(out_dir):
    if fname != "index.html":
        os.remove(os.path.join(out_dir, fname))

for section_name, section_data in sections.items():
    for cat, examples in section_data.items():
        for ex in examples:
            escaped = ex["code"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            has_js = bool(ex["js"].strip())
            preview = make_iframe(ex["js"], ex["w"], ex["h"]) if has_js else ""
            page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{ex["name"]} - C++ Mode Examples</title>
  <style>{shared_css}</style>
</head>
<body>
<nav id="site-nav">
  
  <button class="hamburger" onclick="document.querySelector('.sidebar-outer').classList.toggle('open')">☰</button>
</nav>
<div class="layout">
  <div class="sidebar-outer">
    <div id="site-sidebar">
      <a href="../libraries">Libraries</a>
      <a href="../reference">Reference</a>
      <a href="../examples">Examples</a>
      <a href="../about">About</a>
    </div>
    <div class="sidebar-examples">{build_page_sidebar(ex["id"])}</div>
  </div>
  <div class="content">
    <h1>{ex["name"]}</h1>
    {preview}
    <div class="code-block">
      <div class="code-header">
        <span>{ex["name"].lower().replace(" ","-")}.pde</span>
        <button class="copy-btn" onclick="copyCode()">Copy</button>
      </div>
      <pre id="code-pre">{escaped}</pre>
  </div>
</div>
<footer>
  <p>C++ Mode for Processing</p>
  <p class="footer-contact">
    <a href="mailto:hello@pepc84.com">hello@pepc84.com</a>
    <span class="footer-sep">&middot;</span>
    <a href="https://discord.gg/vShSrPegJT">Discord</a>
  </p>
</footer>
<script>{shared_js}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="../assets/cppmode-keywords.js"></script>
<script src="../assets/cm-cppmode.js"></script>
<script src="../assets/code-highlight.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<link rel="stylesheet" href="../assets/cppmode-theme.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="../assets/cppmode-keywords.js"></script>
<script src="../assets/cm-cppmode.js"></script>
<script src="../assets/code-highlight.js"></script>
<script src="../assets/nav.js"></script>
</body>
</html>'''
            with open(os.path.join(out_dir, ex["slug"]+".html"),"w") as f:
                f.write(page)

THUMBS_MANIFEST = "/home/pep/Projects/processing-cpp.github.io/assets/examples_thumbs/manifest.json"


def load_thumb_manifest():
    if not os.path.exists(THUMBS_MANIFEST):
        print(f"NOTE: {THUMBS_MANIFEST} not found -- run generate_example_thumbnails.py "
              f"first to populate the examples gallery with real thumbnails. "
              f"examples/index.html will fall back to the plain placeholder text for now.")
        return None
    with open(THUMBS_MANIFEST) as f:
        return json.load(f)


def build_examples_gallery(manifest, sections):
    """Build the Processing.org-style thumbnail gallery: one heading per
    section (Basics, Topics, ...), with one sub-section per category
    inside it, each example shown as a clickable card with its
    thumbnail -- grouped and ordered the same way the sidebar does."""
    if not manifest:
        return '<div class="welcome"><h1>Examples</h1></div>'

    thumb_by_key = {}
    for m in manifest:
        # Key on (section, slug) so Basics and Topics can have same-named
        # examples without one overwriting the other in the lookup table.
        key = (m.get("section", "Basics"), m["slug"])
        thumb_by_key[key] = m

    section_blocks = []
    for section_name, section_data in sections.items():
        cat_blocks = []
        for cat, examples in section_data.items():
            cards = []
            for ex in examples:
                thumb = thumb_by_key.get((section_name, ex["slug"]))
                if thumb:
                    thumb_src = f'../assets/examples_thumbs/{thumb.get("section", "Basics")}/{thumb["category"]}/{thumb["thumb"]}'
                else:
                    thumb_src = ""  # no thumbnail generated yet for this example
                img_html = (
                    f'<img src="{thumb_src}" alt="{ex["name"]}" loading="lazy">'
                    if thumb_src else
                    '<div class="gallery-thumb-missing"></div>'
                )
                cards.append(
                    f'<a class="gallery-card" href="{ex["slug"]}.html">'
                    f'<div class="gallery-thumb">{img_html}</div>'
                    f'<div class="gallery-card-title">{ex["name"]}</div>'
                    f"</a>"
                )
            cat_blocks.append(
                f'<div class="gallery-section"><h2>{cat.replace("_"," ").title()}</h2>'
                f'<div class="gallery-grid">{"".join(cards)}</div></div>'
            )
        section_blocks.append(
            f'<div class="gallery-section-group"><h1 class="gallery-section-title">{section_name}</h1>'
            + "".join(cat_blocks) + "</div>"
        )

    return (
        '<div class="gallery-intro"><h1>Examples</h1></div>'
        + "".join(section_blocks)
    )


gallery_css = '''
    .gallery-intro { margin-bottom: 2.5rem; }
    .gallery-intro h1 { font-size: 1.8rem; font-weight: 600; margin-bottom: 0.5rem; color: #e8b400; }
    .gallery-intro p { color: #555; }
    .gallery-section-group { margin-bottom: 2rem; }
    .gallery-section-title { font-size: 1.4rem; font-weight: 700; margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 2px solid #111; color: #e8b400; }
    .gallery-section { margin-bottom: 3rem; }
    .gallery-section h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #e0e0e0; color: #b8860b; }
    .gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1.25rem; }
    .gallery-card { display: block; }
    .gallery-thumb { width: 100%; background: #111; border-radius: 6px; overflow: hidden; border: 1px solid #e0e0e0; line-height: 0; }
    .gallery-thumb img { width: 100%; height: auto; display: block; }
    .gallery-thumb-missing { width: 100%; aspect-ratio: 16/9; background: #1a1a1a; }
    .gallery-card-title { font-size: 13px; color: #555; margin-top: 0.5rem; text-align: center; }
    .gallery-card:hover .gallery-thumb { border-color: #aaa; }
    .gallery-card:hover .gallery-card-title { color: #111; }
'''

thumb_manifest = load_thumb_manifest()
gallery_html = build_examples_gallery(thumb_manifest, sections)

ex_sidebar = build_page_sidebar()
with open(os.path.join(out_dir,"index.html"),"w") as f:
    f.write(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Examples - C++ Mode for Processing</title>
  <style>{shared_css}{gallery_css}</style>
</head>
<body>
<nav id="site-nav">
  
  <button class="hamburger" onclick="document.querySelector('.sidebar-outer').classList.toggle('open')">☰</button>
</nav>
<div class="layout">
  <div class="sidebar-outer">
    <div id="site-sidebar">
      <a href="../libraries">Libraries</a>
      <a href="../reference">Reference</a>
      <a href="../examples" class="active">Examples</a>
      <a href="../about">About</a>
    </div>
    <div class="sidebar-examples">{ex_sidebar}</div>
  </div>
  <div class="content">{gallery_html}</div>
</div>
<footer>
  <p>C++ Mode for Processing</p>
  <p class="footer-contact">
    <a href="mailto:hello@pepc84.com">hello@pepc84.com</a>
    <span class="footer-sep">&middot;</span>
    <a href="https://discord.gg/vShSrPegJT">Discord</a>
  </p>
</footer>
<script>{shared_js}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="../assets/cppmode-keywords.js"></script>
<script src="../assets/cm-cppmode.js"></script>
<script src="../assets/code-highlight.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<link rel="stylesheet" href="../assets/cppmode-theme.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="../assets/cppmode-keywords.js"></script>
<script src="../assets/cm-cppmode.js"></script>
<script src="../assets/code-highlight.js"></script>
<script src="../assets/nav.js"></script>
</body>
</html>''')

print(f"done — {sum(len(v) for section_data in sections.values() for v in section_data.values())} examples generated across {len(sections)} section(s): {', '.join(sections.keys())}")

# ---------------------------------------------------------------------------
# Homepage random example previews
#
# Picks 3 random examples (from the same `data` built above) that have no
# external asset dependencies (loadImage/loadFont/etc.), forces their
# canvas to a small fixed square (so they fit the homepage's tiny preview
# boxes regardless of what size the original sketch requests), and embeds
# each one as an isolated iframe -- same technique already used for the
# full-size example pages, just shrunk down. This replaces the old
# hand-written instance-mode sketches that used to live inline in
# index.html (which had a p.document bug and weren't randomized at all).
# ---------------------------------------------------------------------------
import random

HOMEPAGE_PREVIEW_SIZE = 300  # px, square; matches .example-canvas's CSS aspect-ratio:1 box

_data_loading_re = re.compile(r"loadImage|loadFont|loadModel|loadStrings|loadJSON|loadTable|requestImage|loadXML")
_canvas_size_re = re.compile(r"(createCanvas|size)\s*\(\s*\d+\s*,\s*\d+\s*((?:,[^)]*)?)\)")


def force_square_canvas(js_code, size):
    """Rewrite any createCanvas(w,h[,...])/size(w,h) call to a fixed
    square size, so the sketch renders at the small homepage preview size
    regardless of what resolution it originally asked for. Any extra
    arguments after the width/height (e.g. a renderer like WEBGL) are
    preserved. If the sketch has neither call (rare), nothing is changed
    -- p5 defaults to 100x100 in that case, an acceptable degraded
    fallback rather than a crash."""
    return _canvas_size_re.sub(lambda m: f"{m.group(1)}({size},{size}{m.group(2)})", js_code, count=1)


def make_preview_iframe(js_code, canvas_id, size):
    js_code = fix_asset_paths(js_code)
    js_code = force_square_canvas(js_code, size)
    safe = js_code.replace("</script>", "<\\/script>").replace("`", "\\`")
    return (
        f'<iframe class="example-canvas" id="{canvas_id}" width="{size}" height="{size}" '
        f'style="width:100%;aspect-ratio:1;border:none;display:block;background:#000;" '
        f'scrolling="no"></iframe>'
        f"<script>(function(){{"
        f"const iframe=document.getElementById('{canvas_id}');"
        f"const doc=iframe.contentDocument||iframe.contentWindow.document;"
        f"doc.open();"
        f'doc.write(`<!DOCTYPE html><html><head><style>*{{margin:0;padding:0;}}body{{overflow:hidden;}}</style>'
        f'<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"><\\/script></head>'
        f"<body><script>{safe}<\\/script></body></html>`);"
        f"doc.close();"
        f"}})();</script>"
    )


def pick_random_homepage_examples(sections, count=3):
    pool = []
    for section_name, section_data in sections.items():
        for cat, examples in section_data.items():
            for ex in examples:
                if not ex["js"].strip():
                    continue
                if _data_loading_re.search(ex["js"]):
                    continue  # skip anything that loads external assets -- too
                              # likely to render blank/broken in a tiny decorative box
                pool.append({**ex, "category": cat.replace("_", " ").title()})
    if len(pool) < count:
        return pool
    return random.sample(pool, count)


def update_homepage_examples(repo_root, sections, fixed_picks=None):
    index_path = os.path.join(repo_root, "index.html")
    if not os.path.exists(index_path):
        print(f"WARNING: {index_path} not found, skipping homepage example update.")
        return

    with open(index_path) as f:
        html = f.read()

    picks = fixed_picks if fixed_picks is not None else pick_random_homepage_examples(sections, count=3)
    if len(picks) < 3:
        print(f"WARNING: only found {len(picks)} eligible examples for the homepage, expected 3.")

    canvas_ids = ["c1", "c2", "c3"]
    replaced_count = 0
    card_num = 1
    for canvas_id, ex in zip(canvas_ids, picks):
        iframe_html = make_preview_iframe(ex["js"], canvas_id, HOMEPAGE_PREVIEW_SIZE)
        replacement = (
            f'<a class="example-card" href="/examples/{ex["slug"]}.html" id="card{card_num}">\n'
            f"          {iframe_html}\n"
            f'          <div class="example-info"><h3>{ex["name"]}</h3>'
            f'<p>{ex["category"]} example</p></div>\n'
            f'        </a>'
        )
        # Match either the original <canvas> card or an already-replaced <iframe> card
        card_re = re.compile(
            rf'<a\s+class="example-card"[^>]*id="card{card_num}"[^>]*>'
            rf'.*?'
            rf'</a>',
            re.DOTALL
        )
        html, n = card_re.subn(replacement, html, count=1)
        if n == 0:
            print(f"WARNING: could not find homepage card markup for {canvas_id}, skipping.")
        else:
            replaced_count += 1
        card_num += 1

    # Only remove the old inline <script>...new p5(...)...</script> block
    # if every card was actually replaced with a working iframe -- if the
    # eligible example pool ever comes up short (fewer than 3 candidates),
    # leave the old script in place so any un-replaced canvas still has
    # something driving it, rather than going permanently blank.
    if replaced_count == len(canvas_ids):
        html = re.sub(
            r"<script>\s*new p5\(function\(p\)[\s\S]*?</script>\s*(?=<script src=\"\./assets/nav\.js\"></script>)",
            "",
            html,
            count=1,
        )
    else:
        print(f"NOTE: only {replaced_count}/{len(canvas_ids)} homepage cards replaced; keeping the old inline sketch script as a fallback for the rest.")

    with open(index_path, "w") as f:
        f.write(html)

    label = "pinned" if fixed_picks is not None else "random"
    print(f"Updated homepage with {len(picks)} {label} example preview(s): " + ", ".join(p["name"] for p in picks))


def find_examples_by_slug(sections, slugs):
    """Look up specific examples by slug for the --examples flag.
    Slugs are matched case-insensitively so you don't have to worry
    about exact capitalisation. Warns if a slug isn't found."""
    all_examples = {
        ex["slug"]: {**ex, "category": cat.replace("_", " ").title()}
        for section_data in sections.values()
        for cat, examples in section_data.items()
        for ex in examples
    }
    result = []
    for slug in slugs:
        match = all_examples.get(slug) or all_examples.get(slug.lower())
        if match:
            result.append(match)
        else:
            # Try partial match on name too
            fuzzy = [e for s, e in all_examples.items() if slug.lower() in s]
            if fuzzy:
                result.append(fuzzy[0])
                print(f"NOTE: '{slug}' matched '{fuzzy[0]['slug']}'")
            else:
                print(f"WARNING: could not find example with slug '{slug}' -- skipping.")
                print(f"  Available slugs: {', '.join(sorted(all_examples.keys()))}")
    return result


import argparse
parser = argparse.ArgumentParser(description="Rebuild examples pages and update the homepage.")
parser.add_argument(
    "--examples",
    nargs="+",
    metavar="SLUG",
    help=(
        "Slugs of exactly the examples to show on the homepage, e.g. "
        "--examples sine-wave noise-2d flocking. "
        "Use the hyphenated lowercase name (same as the URL). "
        "If omitted, 3 examples are picked at random as usual."
    ),
)
args = parser.parse_args()

if args.examples:
    picked = find_examples_by_slug(sections, args.examples)
    print(f"Found {len(picked)} of {len(args.examples)} requested: {[p['slug'] for p in picked]}")
    if len(picked) < 3:
        print(f"WARNING: only {len(picked)} of the requested examples were found -- filling the rest randomly.")
        picked += pick_random_homepage_examples(sections, count=3 - len(picked))
    picked = picked[:3]
    update_homepage_examples(os.path.dirname(out_dir), sections, fixed_picks=picked)
else:
    update_homepage_examples(os.path.dirname(out_dir), sections)
