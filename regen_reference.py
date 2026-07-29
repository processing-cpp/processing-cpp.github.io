"""
Generates reference/*.html and reference/index.html from a single data
file at assets/reference.yml.

Usage:
    python3 regen_reference.py

Edit assets/reference.yml to add, remove, or change reference entries,
then re-run this script. Do not hand-edit files under reference/ directly;
they are overwritten every run.
"""
import os
import glob
import html
import yaml

DATA_FILE = os.path.join(os.path.dirname(__file__), "assets", "reference.yml")
OUT_DIR = os.path.join(os.path.dirname(__file__), "reference")

shared_css = '''* { margin: 0; padding: 0; box-sizing: border-box; } body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111; background: #fff; } a { color: #111; text-decoration: none; } nav { border-bottom: 1px solid #e0e0e0; padding: 0 2rem; display: flex; align-items: center; justify-content: space-between; height: 60px; position: sticky; top: 0; background: #fff; z-index: 100; } .nav-logo { display: flex; align-items: center; gap: 10px; color: #111; } .nav-logo img { width: 28px; height: 28px; } .hamburger { background: none; border: none; cursor: pointer; font-size: 22px; padding: 4px 8px; display: none; } .layout { display: flex; min-height: calc(100vh - 60px); } .sidebar-outer { width: 220px; min-width: 220px; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; position: sticky; top: 60px; height: calc(100vh - 60px); } #site-sidebar { padding: 1.5rem 1.5rem 1rem; border-bottom: 1px solid #e0e0e0; display: flex; flex-direction: column; } #site-sidebar a { font-size: 14px; color: #555; padding: 0.4rem 0; display: block; } #site-sidebar a:hover { color: #111; } #site-sidebar a.active { color: #111; font-weight: 500; } .ref-sidebar { flex: 1; overflow-y: auto; padding: 0.5rem 0; } .ref-cat-title { font-size: 11px; font-weight: 700; color: #111; text-transform: uppercase; letter-spacing: 0.08em; padding: 0.85rem 1.5rem 0.25rem; } .ref-subcat-title { font-size: 10px; font-weight: 600; color: #aaa; padding: 0.5rem 1.5rem 0.1rem; } .ref-sidebar a { display: block; font-size: 12px; color: #555; padding: 0.2rem 1.5rem; font-family: "SF Mono","Fira Code",monospace; } .ref-sidebar a.ref-sidebar-sub { padding-left: 2rem; } .ref-sidebar a:hover { color: #111; background: #f8f8f8; } .ref-sidebar a.active { color: #111 !important; font-weight: 600; background: #f4f4f4; } .content { flex: 1; padding: 3rem 4rem; max-width: 860px; } .content h1 { font-size: 1.8rem; font-weight: 600; margin-bottom: 0.25rem; font-family: "SF Mono","Fira Code",monospace; } .cat-tag { font-size: 12px; color: #aaa; margin-bottom: 2rem; display: block; } .content h2 { font-size: 11px; font-weight: 700; color: #aaa; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2rem; margin-bottom: 0.75rem; } .content p { color: #444; line-height: 1.8; margin-bottom: 1rem; font-size: 0.95rem; } .syntax-block { background: #f8f8f8; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.5rem; font-family: "SF Mono","Fira Code",monospace; font-size: 13px; line-height: 1.8; white-space: pre; overflow-x: auto; } .params-table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; font-size: 13px; } .params-table th { text-align: left; font-size: 11px; font-weight: 700; color: #aaa; text-transform: uppercase; letter-spacing: 0.06em; padding: 0.5rem 0.75rem; border-bottom: 1px solid #e0e0e0; } .params-table td { padding: 0.55rem 0.75rem; border-bottom: 1px solid #f0f0f0; vertical-align: top; } .params-table td:first-child { font-family: "SF Mono","Fira Code",monospace; font-size: 12px; color: #333; width: 130px; } .params-table td:nth-child(2) { color: #888; font-family: "SF Mono","Fira Code",monospace; font-size: 12px; width: 90px; } .returns-badge { font-family: "SF Mono","Fira Code",monospace; font-size: 12px; background: #f0f0f0; border-radius: 4px; padding: 3px 10px; color: #555; display: inline-block; margin-bottom: 1rem; } .related-links { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 2rem; } .related-links a { font-family: "SF Mono","Fira Code",monospace; font-size: 12px; background: #f4f4f4; border-radius: 4px; padding: 3px 10px; color: #555; } .related-links a:hover { background: #e0e0e0; color: #111; } .methods-table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; font-size: 13px; } .methods-table td { padding: 0.55rem 0.75rem; border-bottom: 1px solid #f0f0f0; } .methods-table td:first-child { font-family: "SF Mono","Fira Code",monospace; font-size: 12px; color: #333; width: 280px; } .impl-block { background: #0d0d0d; border-radius: 6px; padding: 1rem 1.25rem; font-family: "SF Mono","Fira Code",monospace; font-size: 12px; line-height: 1.7; color: #ccc; white-space: pre; overflow-x: auto; max-height: 400px; overflow-y: auto; } .topic-block { margin-bottom: 3rem; } .topic-title { font-size: 1.1rem; font-weight: 700; color: #111; margin-bottom: 1.25rem; padding-bottom: 0.5rem; border-bottom: 2px solid #111; } .subtopic { margin-bottom: 1.5rem; } .subtopic-title { font-size: 11px; font-weight: 700; color: #aaa; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; } .fn-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)); gap: 0.2rem 1.5rem; } .fn-list a { font-family: "SF Mono","Fira Code",monospace; font-size: 12px; color: #555; padding: 0.15rem 0; display: block; } .fn-list a:hover { color: #111; } footer { border-top: 1px solid #e0e0e0; padding: 2rem; text-align: center; font-size: 13px; color: #888; } @media (max-width: 768px) { .hamburger { display: block; } .sidebar-outer { position: fixed; top: 60px; left: -240px; width: 240px; height: calc(100vh - 60px); background: #fff; z-index: 200; transition: left 0.25s ease; box-shadow: 2px 0 12px rgba(0,0,0,0.08); } .sidebar-outer.open { left: 0; } .content { padding: 2rem 1.25rem; } }'''


def esc(s):
    return html.escape(s, quote=False) if s else ""


def label_for(slug, entries_by_slug):
    """Sidebar label for a slug: prefer the entry's display name, else the slug itself."""
    e = entries_by_slug.get(slug)
    return esc(e["name"]) if e else esc(slug)


def build_sidebar(sidebar_tree, entries_by_slug, active_slug=""):
    out = []
    for cat in sidebar_tree:
        out.append(f'<div class="ref-cat-title">{esc(cat["category"])}</div>')
        for sub in cat["subcats"]:
            css_class = "ref-sidebar-sub" if sub.get("name") else "ref-sidebar-item"
            if sub.get("name"):
                out.append(f'<div class="ref-subcat-title">{esc(sub["name"])}</div>')
            for slug in sub["slugs"]:
                active = "active " if slug == active_slug else ""
                out.append(
                    f'<a href="{slug}.html" class="{active}{css_class}">{label_for(slug, entries_by_slug)}</a>'
                )
    return "".join(out)


def render_params(params):
    if not params:
        return '<p style="color:#aaa;font-size:13px;">None</p>'
    rows = "<tr><th>Name</th><th>Type</th><th>Description</th></tr>"
    for p in params:
        rows += f'<tr><td>{esc(p.get("name",""))}</td><td>{p.get("type","")}</td><td>{esc(p.get("desc",""))}</td></tr>'
    return f'<table class="params-table">{rows}</table>'


def render_methods(methods):
    if not methods:
        return ""
    rows = "".join(
        f'<tr><td>{m.get("sig","")}</td><td>{m.get("desc","")}</td></tr>' for m in methods
    )
    return f'<h2>Methods</h2><table class="methods-table">{rows}</table>'


def render_related(related, entries_by_slug):
    if not related:
        return ""
    links = "".join(f'<a href="{slug}.html">{esc(slug)}</a>' for slug in related)
    return f'<h2>Related</h2><div class="related-links">{links}</div>'


def render_returns(returns):
    if not returns:
        return ""
    return f'<h2>Returns</h2>\n    <span class="returns-badge">{returns}</span>'


def render_under_the_hood_block(label, code):
    if not code:
        return ""
    return (
        '<h2>Under the Hood</h2>'
        f'<p style="font-size:13px;color:#888;margin-bottom:0.75rem;">From {label}:</p>'
        f'<div class="impl-block">{esc(code)}</div>'
    )


def render_impl(entry):
    h_code = entry.get("under_the_hood_h")
    cpp_code = entry.get("under_the_hood_cpp")
    if h_code or cpp_code:
        return render_under_the_hood_block("Processing.h", h_code) + render_under_the_hood_block(
            "Processing.cpp", cpp_code
        )
    # Fall back to the legacy single field for entries not yet migrated
    # by regen_under_the_hood.py.
    legacy = entry.get("impl")
    if not legacy:
        return ""
    return render_under_the_hood_block("Processing.cpp", legacy)


def render_page(entry, sidebar_tree, entries_by_slug):
    sidebar_html = build_sidebar(sidebar_tree, entries_by_slug, entry["slug"])

    syntax_html = (
        f'<h2>Syntax</h2>\n    <div class="syntax-block">{esc(entry["syntax"])}</div>'
        if entry.get("syntax") else ""
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(entry["name"])} - Processing for C++ Reference</title>
  <style>{shared_css}</style>
  <link rel="stylesheet" href="../assets/cppmode-theme.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
  <link rel="stylesheet" href="../assets/cppmode-theme.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
</head>
<body>
<nav id="site-nav"></nav>
<div class="layout">
  <div class="sidebar-outer">
    <div id="site-sidebar"></div>
    <div class="ref-sidebar">{sidebar_html}</div>
  </div>
  <div class="content">
    <h1>{esc(entry["name"])}</h1>
    <span class="cat-tag">{esc(entry.get("cat_tag", ""))}</span>
    <h2>Description</h2>
    <p>{esc(entry.get("description", ""))}</p>
    {syntax_html}
    <h2>Parameters</h2>
    {render_params(entry.get("params"))}
    {render_returns(entry.get("returns"))}
    {render_methods(entry.get("methods"))}
    {render_related(entry.get("related"), entries_by_slug)}
    {render_impl(entry)}
  </div>
</div>
<footer><p>Processing for C++</p></footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="../assets/cppmode-keywords.js"></script>
<script src="../assets/cm-cppmode.js"></script>
<script src="../assets/code-highlight.js"></script>
<script src="../assets/nav.js"></script>
</body>
</html>
'''


def render_index(sidebar_tree, entries_by_slug):
    sidebar_html = build_sidebar(sidebar_tree, entries_by_slug)

    topic_blocks = []
    for cat in sidebar_tree:
        subtopics = []
        for sub in cat["subcats"]:
            title_html = f'<div class="subtopic-title">{esc(sub["name"])}</div>' if sub.get("name") else ""
            links = "".join(
                f'<a href="{slug}.html">{label_for(slug, entries_by_slug)}</a>' for slug in sub["slugs"]
            )
            subtopics.append(f'<div class="subtopic">{title_html}<div class="fn-list">{links}</div></div>')
        topic_blocks.append(
            f'<div class="topic-block"><div class="topic-title">{esc(cat["category"])}</div>{"".join(subtopics)}</div>'
        )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reference - Processing for C++</title>
  <style>{shared_css}</style>
</head>
<body>
<nav id="site-nav"></nav>
<div class="layout">
  <div class="sidebar-outer">
    <div id="site-sidebar"></div>
    <div class="ref-sidebar">{sidebar_html}</div>
  </div>
  <div class="content">
    <h1 style="font-family:inherit;font-size:2rem;margin-bottom:0.5rem;">Reference</h1>
    <p style="color:#888;font-size:0.95rem;margin-bottom:3rem;">Full API reference for Processing for C++.</p>
    {"".join(topic_blocks)}
  </div>
</div>
<footer><p>Processing for C++</p></footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="../assets/cppmode-keywords.js"></script>
<script src="../assets/cm-cppmode.js"></script>
<script src="../assets/code-highlight.js"></script>
<script src="../assets/nav.js"></script>
</body>
</html>
'''


def main():
    with open(DATA_FILE) as f:
        data = yaml.safe_load(f)

    sidebar_tree = data["sidebar"]
    entries = data["entries"]
    entries_by_slug = {e["slug"]: e for e in entries}

    os.makedirs(OUT_DIR, exist_ok=True)

    existing = glob.glob(os.path.join(OUT_DIR, "*.html"))
    for fp in existing:
        os.remove(fp)
    print(f"Deleted {len(existing)} existing file(s) in {OUT_DIR}/.")

    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(render_index(sidebar_tree, entries_by_slug))

    for entry in entries:
        with open(os.path.join(OUT_DIR, f'{entry["slug"]}.html'), "w") as f:
            f.write(render_page(entry, sidebar_tree, entries_by_slug))

    print(f"Generated reference/index.html and {len(entries)} reference pages.")


if __name__ == "__main__":
    main()
