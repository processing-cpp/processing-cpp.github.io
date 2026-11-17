import os, html, yaml

DATA_FILE = os.path.join(os.path.dirname(__file__), "assets", "errors.yml")
OUT_DIR = os.path.join(os.path.dirname(__file__), "error")

shared_css = '''* { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111; background: #fff; }
    a { color: #111; text-decoration: none; }
    nav { border-bottom: 1px solid #e0e0e0; padding: 0 2rem; display: flex; align-items: center; justify-content: space-between; height: 60px; position: sticky; top: 0; background: #fff; z-index: 100; }
    .nav-logo { display: flex; align-items: center; gap: 10px; color: #111; }
    .nav-logo img { width: 28px; height: 28px; }
    .hamburger { background: none; border: none; cursor: pointer; font-size: 22px; padding: 4px 8px; display: none; }
    .layout { display: flex; min-height: calc(100vh - 60px); }
    .sidebar-outer { width: 220px; min-width: 220px; border-right: 1px solid #e0e0e0; display: flex; flex-direction: column; position: sticky; top: 60px; height: calc(100vh - 60px); }
    #site-sidebar { padding: 1.5rem 1.5rem 1rem; border-bottom: 1px solid #e0e0e0; display: flex; flex-direction: column; }
    #site-sidebar a { font-size: 14px; color: #555; padding: 0.4rem 0; display: block; }
    #site-sidebar a:hover { color: #111; }
    #site-sidebar a.active { color: #111; font-weight: 500; }
    .err-sidebar { flex: 1; overflow-y: auto; padding: 0.5rem 0; }
    .err-sidebar-title { font-size: 11px; font-weight: 700; color: #111; text-transform: uppercase; letter-spacing: 0.08em; padding: 0.85rem 1.5rem 0.25rem; }
    .err-sidebar a { display: block; font-size: 12px; color: #555; padding: 0.25rem 1.5rem; font-family: "SF Mono","Fira Code",monospace; }
    .err-sidebar a:hover { color: #111; background: #f8f8f8; }
    .err-sidebar a.active { color: #111 !important; font-weight: 600; background: #f4f4f4; }
    .content { flex: 1; padding: 3rem 4rem; max-width: 820px; }
    .content h1 { font-size: 1.6rem; font-weight: 600; margin-bottom: 0.25rem; font-family: "SF Mono","Fira Code",monospace; }
    .err-code { font-size: 12px; color: #aaa; margin-bottom: 2rem; display: block; font-family: "SF Mono","Fira Code",monospace; }
    .content h2 { font-size: 11px; font-weight: 700; color: #aaa; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2rem; margin-bottom: 0.75rem; }
    .content p { color: #444; line-height: 1.8; margin-bottom: 1rem; font-size: 0.95rem; }
    .code-block { background: #f8f8f8; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.5rem; font-family: "SF Mono","Fira Code",monospace; font-size: 13px; line-height: 1.8; white-space: pre; overflow-x: auto; }
    .code-block.before { border-left: 3px solid #d4534f; }
    .code-block.after { border-left: 3px solid #2f9e5c; }
    .code-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.4rem; display: block; }
    .code-label.before { color: #d4534f; }
    .code-label.after { color: #2f9e5c; }
    .code-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 0.5rem; }
    footer { border-top: 1px solid #e0e0e0; padding: 2rem; text-align: center; font-size: 13px; color: #888; }
    @media (max-width: 768px) {
      .hamburger { display: block; }
      .sidebar-outer { position: fixed; top: 60px; left: -240px; width: 240px; height: calc(100vh - 60px); background: #fff; z-index: 200; transition: left 0.25s ease; box-shadow: 2px 0 12px rgba(0,0,0,0.08); }
      .sidebar-outer.open { left: 0; }
      .content { padding: 2rem 1.25rem; }
      .code-pair { grid-template-columns: 1fr; }
    }'''


def esc(s):
    return html.escape(s.strip() if s else "")


def build_sidebar(errors, active_code=""):
    s = '<div class="err-sidebar-title">Compiler Errors</div>'
    for e in errors:
        active = " active" if e["code"] == active_code else ""
        s += f'<a href="{e["code"]}.html" class="{active.strip()}">{e["code"]} &middot; {esc(e["title"])}</a>'
    return s


def render_page(e, errors, depth=1):
    prefix = "../" * depth
    sidebar_links = build_sidebar(errors, e["code"])

    code_pair = ""
    if e.get("before") or e.get("after"):
        code_pair = '<h2>Example</h2><div class="code-pair">'
        if e.get("before"):
            code_pair += f'<div><span class="code-label before">Before</span><div class="code-block before">{esc(e["before"])}</div></div>'
        if e.get("after"):
            code_pair += f'<div><span class="code-label after">After</span><div class="code-block after">{esc(e["after"])}</div></div>'
        code_pair += '</div>'

    notes_html = f'<h2>Notes</h2><p>{esc(e["notes"])}</p>' if e.get("notes") else ""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e["code"]}: {esc(e["title"])} - Processing for C++</title>
  <style>{shared_css}</style>
</head>
<body>
<nav id="site-nav"></nav>
<div class="layout">
  <div class="sidebar-outer">
    <div id="site-sidebar"></div>
    <div class="err-sidebar">{sidebar_links}</div>
  </div>
  <div class="content">
    <h1>{e["code"]}: {esc(e["title"])}</h1>
    <span class="err-code">{esc(e.get("type", "Compiler Error"))}</span>
    <h2>What it means</h2>
    <p>{esc(e["summary"])}</p>
    <h2>How to fix it</h2>
    <p>{esc(e["fix"])}</p>
    {code_pair}
    {notes_html}
  </div>
</div>
<footer><p>Processing for C++</p></footer>
<script src="{prefix}assets/nav.js"></script>
</body>
</html>
'''


def render_index(errors, depth=1):
    prefix = "../" * depth
    rows = ""
    for e in errors:
        rows += f'''<a href="{e["code"]}.html" class="err-list-item">
      <span class="err-list-code">{e["code"]}</span>
      <span class="err-list-title">{esc(e["title"])}</span>
    </a>'''

    extra_css = '''
    .err-list { border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden; }
    .err-list-item { display: flex; gap: 1.25rem; align-items: baseline; padding: 1rem 1.5rem; border-bottom: 1px solid #e0e0e0; }
    .err-list-item:last-child { border-bottom: none; }
    .err-list-item:hover { background: #f8f8f8; }
    .err-list-code { font-family: "SF Mono","Fira Code",monospace; font-size: 13px; font-weight: 700; color: #111; min-width: 70px; }
    .err-list-title { font-size: 14px; color: #555; }
    .prelude { font-size: 1rem; color: #555; line-height: 1.8; margin-bottom: 2rem; max-width: 640px; }
    '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Processing C++ error codes index</title>
  <style>{shared_css}
    .content {{ max-width: 900px; }}
    {extra_css}</style>
</head>
<body>
<nav id="site-nav"></nav>
<div class="layout">
  <div class="sidebar-outer">
    <div id="site-sidebar"></div>
    <div class="err-sidebar">{build_sidebar(errors)}</div>
  </div>
  <div class="content">
    <h1>Processing C++ error codes index</h1>
    <div class="err-list">
    {rows}
    </div>
  </div>
</div>
<footer><p>Processing for C++</p></footer>
<script src="{prefix}assets/nav.js"></script>
</body>
</html>
'''


def main():
    with open(DATA_FILE) as f:
        errors = yaml.safe_load(f)

    errors = sorted(errors, key=lambda e: e["code"])

    os.makedirs(OUT_DIR, exist_ok=True)

    # error/index.html -> listing page
    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(render_index(errors))

    # error/<CODE>.html -> one flat page per error (e.g. error/E0002.html)
    for e in errors:
        with open(os.path.join(OUT_DIR, f"{e['code']}.html"), "w") as f:
            f.write(render_page(e, errors))

    print(f"Generated error/index.html and {len(errors)} error pages:")
    for e in errors:
        print(f"  error/{e['code']}.html")


if __name__ == "__main__":
    main()
