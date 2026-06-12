import os, re

base_cpp = "/home/pep/Projects/processing-cpp.github.io/assets/examples/Basics"
base_js  = "/home/pep/Projects/processing-cpp.github.io/assets/examples_js/Basics"
categories = sorted(os.listdir(base_cpp))

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

data = {}
for cat in categories:
    cat_path = os.path.join(base_cpp, cat)
    if not os.path.isdir(cat_path): continue
    data[cat] = []
    for example in sorted(os.listdir(cat_path)):
        ex_path = os.path.join(cat_path, example)
        if not os.path.isdir(ex_path): continue
        pde = os.path.join(ex_path, example + ".pde")
        if not os.path.exists(pde): continue
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
        data[cat].append({"id": cat+"_"+example, "name": example.replace("_"," "), "slug": slug, "code": code, "js": js_code, "w": w, "h": h})

def build_page_sidebar(active_id=""):
    s = '<div class="section-header" onclick="toggleSection(\'basics\')"><span>Basics</span><span class="arrow" id="basics-arrow">▾</span></div><div id="basics-section">'
    for cat, examples in data.items():
        s += f'<div class="category"><div class="category-title">{cat.replace("_"," ").title()}</div>'
        for ex in examples:
            active = 'class="active"' if ex["id"] == active_id else ""
            s += f'<a href="{ex["slug"]}.html" {active}>{ex["name"]}</a>'
        s += '</div>'
    s += '</div><div class="section-header" onclick="toggleSection(\'topics\')"><span>Topics</span><span class="arrow" id="topics-arrow">▸</span></div><div id="topics-section" style="display:none"><div class="category"><div class="category-title" style="color:#ccc;">Coming soon</div></div></div>'
    return s

shared_css = '''* { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111; background: #fff; }
    a { color: #111; text-decoration: none; }
    nav { border-bottom: 1px solid #e0e0e0; padding: 0 2rem; display: flex; align-items: center; justify-content: space-between; height: 60px; position: sticky; top: 0; background: #fff; z-index: 100; }
    .nav-logo { display: flex; align-items: center; gap: 10px; color: #111; }
    .nav-logo img { width: 28px; height: 28px; }
    .nav-logo span { font-size: 15px; font-weight: 500; }
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
    .content h1 { font-size: 1.8rem; font-weight: 600; margin-bottom: 0.75rem; }
    .preview-wrap { border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; margin-bottom: 2rem; display: inline-block; }
    .preview-wrap iframe { display: block; border: none; }
    .code-block { background: #f8f8f8; border-radius: 8px; overflow: hidden; }
    .code-header { padding: 0.75rem 1.25rem; border-bottom: 1px solid #e0e0e0; font-size: 12px; color: #888; font-family: monospace; display: flex; align-items: center; justify-content: space-between; }
    .copy-btn { font-size: 12px; color: #555; background: #fff; border: 1px solid #ddd; border-radius: 4px; padding: 3px 10px; cursor: pointer; font-family: inherit; }
    .copy-btn:hover { background: #f0f0f0; }
    .copy-btn.copied { color: #090; border-color: #090; }
    pre { padding: 1.5rem; font-family: "SF Mono","Fira Code",monospace; font-size: 13px; line-height: 1.7; overflow-x: auto; white-space: pre; }
    .welcome h1 { font-size: 1.8rem; font-weight: 600; margin-bottom: 1rem; }
    .welcome p { color: #555; line-height: 1.8; max-width: 500px; }
    footer { border-top: 1px solid #e0e0e0; padding: 2rem; text-align: center; font-size: 13px; color: #888; }
    @media (max-width: 768px) {
      .hamburger { display: block; }
      .sidebar-outer { position: fixed; top: 60px; left: -240px; width: 240px; height: calc(100vh - 60px); background: #fff; z-index: 200; transition: left 0.25s ease; box-shadow: 2px 0 12px rgba(0,0,0,0.08); }
      .sidebar-outer.open { left: 0; }
      .content { padding: 2rem 1.25rem; }
      .preview-wrap { max-width: 100%; }
      .preview-wrap iframe { max-width: 100%; }
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
    pat = re.compile(r"""load(Image|Font|Model)\s*\(\s*["']([^"']+)["']\s*\)""")
    def replacer(m):
        return f'load{m.group(1)}("{base}{m.group(2)}")'
    return pat.sub(replacer, js_code)

def make_iframe(js_code, w, h):
    js_code = fix_asset_paths(js_code)
    safe = js_code.replace('</script>', '<\\/script>').replace('`','\\`')
    return f'''<div class="preview-wrap"><iframe id="sketch-frame" width="{w}" height="{h}"></iframe></div>
<script>(function(){{const iframe=document.getElementById('sketch-frame');const doc=iframe.contentDocument||iframe.contentWindow.document;doc.open();doc.write(`<!DOCTYPE html><html><head><style>*{{margin:0;padding:0;}}body{{overflow:hidden;}}</style><script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"><\\/script></head><body><script>{safe}<\\/script></body></html>`);doc.close();}})();</script>'''

out_dir = "/home/pep/Projects/processing-cpp.github.io/examples"
for fname in os.listdir(out_dir):
    if fname != "index.html":
        os.remove(os.path.join(out_dir, fname))

for cat, examples in data.items():
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
  <a href="../" class="nav-logo"><img src="../assets/cpp-logo.png" alt="C++ Mode"><span>C++ Mode</span></a>
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
</div>
<footer><p>C++ Mode for Processing</p></footer>
<script>{shared_js}</script>
<script src="../assets/nav.js"></script>
</body>
</html>'''
        with open(os.path.join(out_dir, ex["slug"]+".html"),"w") as f:
            f.write(page)

ex_sidebar = build_page_sidebar()
with open(os.path.join(out_dir,"index.html"),"w") as f:
    f.write(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Examples - C++ Mode for Processing</title>
  <style>{shared_css}</style>
</head>
<body>
<nav id="site-nav">
  <a href="/" class="nav-logo"><img src="../assets/cpp-logo.png" alt="C++ Mode"><span>C++ Mode</span></a>
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
  <div class="content"><div class="welcome"><h1>Examples</h1><p>Short programs exploring the basics of creative coding with C++ Mode. Select an example from the left.</p></div></div>
</div>
<footer><p>C++ Mode for Processing</p></footer>
<script>{shared_js}</script>
<script src="../assets/nav.js"></script>
</body>
</html>''')

print(f"done — {sum(len(v) for v in data.values())} examples generated")
