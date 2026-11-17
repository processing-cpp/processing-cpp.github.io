#!/usr/bin/env python3
"""Clone the C++ site 1:1 into the Lua, Rust and Scheme site folders.

Same pages, same UI. Branding (name, colors, logo path, site URL) is swapped.
Per-item reference and example pages are dropped, so links to them 404 on
purpose until each mode has its own docs.

Run from the root of processing-cpp.github.io:
    python3 clone_mode_sites.py            # all three
    python3 clone_mode_sites.py lua        # just one
Each target keeps its own .git folder; everything else is replaced.
"""
import re
import shutil
import sys
from pathlib import Path

AUTHOR = "llamasjc"
SRC_SITE = "https://processing-cpp.github.io"
MODES = {
    "cpp":    {"name": "C++",    "camel": "Cpp",    "ext": "cpp", "site": SRC_SITE,                               "color": "#e8b400", "dark": "#b8860b"},
    "lua":    {"name": "Lua",    "camel": "Lua",    "ext": "lua", "site": "https://processing-lua.github.io",    "color": "#2c6bd6", "dark": "#1d4a96"},
    "rust":   {"name": "Rust",   "camel": "Rust",   "ext": "rs",  "site": "https://processing-rust.github.io",   "color": "#ce422b", "dark": "#93301f"},
    "scheme": {"name": "Scheme", "camel": "Scheme", "ext": "scm", "site": "https://processing-scheme.github.io", "color": "#8a4fd1", "dark": "#5f3394"},
}

# Never copied into the clones.
SKIP_NAMES = {".git", "make_mode_sites.py", "clone_mode_sites.py", "retry.py", "CNAME"}
SKIP_GLOBS = ["regen*.py", "regen*.sh", "*.backup", "*.bak"]
# Dropped so the mode has no C++ docs or examples: every page in these
# folders except the index.
DROP_ITEM_PAGES = ["reference", "examples"]
TEXT_EXT = {".html", ".js", ".css", ".md", ".json", ".txt", ".yml", ".svg"}
ORDER = ["cpp", "rust", "lua", "scheme"]
START, END = "/*modes-start*/", "/*modes-end*/"
OLD_SWITCHER = "/* mode-switcher */"
OLD_LOGO = """      <a href="${SITE}" class="nav-logo">
        <img src="${prefix}assets/cpp-logo.png" alt="Processing for C++">
        <div class="nav-title">
          <span class="nav-title-top">Processing</span>
          <span class="nav-title-bottom">C++</span>
        </div>
      </a>"""
NAV_ANCHOR = "  const nav = document.getElementById('site-nav');"

# Copy that only makes sense for C++. Swapped before the generic rebrand.
HERO_OLD = ("C++ Mode takes that same idea further. You write sketches exactly the way you always have, "
            "but they compile to native C++ under the hood.")
ABOUT_HARD_OLD = ("Getting started with C++ is hard. Before you can draw anything on screen you need to set up "
                  "a build system, open a window, initialize OpenGL, and write a lot of setup code.")
ABOUT_STEPS_OLD = "structs, vectors, pointers, templates"
COPY = {
    "lua": {
        HERO_OLD: "Lua Mode brings that same idea to Lua. It is a small language that reads almost like "
                  "plain English, and your sketches run on the same native engine as C++ Mode.",
        ABOUT_HARD_OLD: "Lua is easy to learn, but drawing with it usually means picking a game framework, "
                        "wiring up a window, and learning its way of doing things before anything shows up.",
        ABOUT_STEPS_OLD: "tables, closures, metatables, coroutines",
    },
    "rust": {
        HERO_OLD: "Rust Mode brings that same idea to Rust. You get Rust's speed and safety, and your "
                  "sketches run on the same native engine as C++ Mode.",
        ABOUT_HARD_OLD: "Getting started with Rust is hard. Before you can draw anything you need to set up "
                        "Cargo, pick a graphics crate, fight the borrow checker, and write a lot of setup code.",
        ABOUT_STEPS_OLD: "structs, enums, ownership, traits",
    },
    "scheme": {
        HERO_OLD: "Scheme Mode brings that same idea to Scheme. You write sketches as plain s-expressions, "
                  "and they run on the same native engine as C++ Mode.",
        ABOUT_HARD_OLD: "Scheme is a great first language, but it almost never comes with a way to draw. "
                        "Most courses stay in the terminal, and the fun part never shows up.",
        ABOUT_STEPS_OLD: "lists, recursion, lambdas, macros",
    },
}


def modes_block(current):
    rows = ",\n".join(
        f"    ['{k}', '{MODES[k]['name']}', '{MODES[k]['site']}', '{MODES[k]['color']}', '{MODES[k]['camel'].lower()}-logo.png']"
        for k in ORDER)
    return f"""{START}
  const MODES_CURRENT = '{current}';
  const MODES_LIST = [
{rows}
  ];
  const modeBar = '<div class="mode-bar">' + MODES_LIST.map(function (m) {{
    return '<a href="' + m[2] + '/" class="nav-logo mode-tab' + (m[0] === MODES_CURRENT ? ' current' : '') + '" style="--mc:' + m[3] + '">' +
      '<img src="' + m[2] + '/assets/' + m[4] + '" alt="Processing for ' + m[1] + '">' +
      '<div class="nav-title"><span class="nav-title-top">Processing</span>' +
      '<span class="nav-title-bottom" style="color:' + m[3] + '">' + m[1] + '</span></div></a>';
  }}).join('') + '</div>';
  if (!document.getElementById('mode-bar-style')) {{
    const ms = document.createElement('style');
    ms.id = 'mode-bar-style';
    ms.textContent =
      '.mode-bar{{display:flex;align-items:center;gap:1.25rem;margin-right:auto;min-width:0;}}' +
      '.mode-bar .nav-logo{{margin:0 !important;text-decoration:none;opacity:.45;transition:opacity .15s;}}' +
      '.mode-bar .nav-logo:hover,.mode-bar .nav-logo.current{{opacity:1;}}' +
      'body.dark-mode .mode-bar .nav-title-bottom{{color:var(--mc) !important;}}' +
      '@media(max-width:800px){{.mode-bar{{gap:.6rem;}}.mode-bar .nav-logo:not(.current) .nav-title{{display:none;}}}}';
    document.head.appendChild(ms);
  }}
  {END}"""


def patch_source_nav(src):
    """Move the mode links from the sidebar into the top bar of the C++ nav.js."""
    nav = src / "assets" / "nav.js"
    text = nav.read_text()
    if START in text:
        return
    if OLD_SWITCHER in text:
        text = text[:text.index(OLD_SWITCHER)].rstrip() + "\n"
    if OLD_LOGO not in text or NAV_ANCHOR not in text:
        sys.exit("nav.js layout changed; top bar not patched")
    text = text.replace(OLD_LOGO, "      ${modeBar}")
    text = text.replace(NAV_ANCHOR, modes_block("cpp") + "\n\n" + NAV_ANCHOR)
    nav.write_text(text)
    print("patched C++ assets/nav.js")


def skip(path, root):
    rel = path.relative_to(root)
    if any(part in SKIP_NAMES for part in rel.parts):
        return True
    if any(path.match(g) for g in SKIP_GLOBS):
        return True
    if (len(rel.parts) == 2 and rel.parts[0] in DROP_ITEM_PAGES
            and rel.suffix == ".html" and rel.name != "index.html"):
        return True
    return False


def rebrand(text, m):
    reps = [
        (SRC_SITE, m["site"]),
        ("processing-cpp/processing-cpp.github.io", f"processing-{m['camel'].lower()}/processing-{m['camel'].lower()}.github.io"),
        ("CppMode", f"{m['camel']}Mode"),
        ("cppmode", f"{m['camel'].lower()}mode"),
        ("cpp-logo", f"{m['camel'].lower()}-logo"),
        ("sketch.cpp", f"sketch.{m['ext']}"),
        ("C++", m["name"]),
        ("#e8b400", m["color"]), ("#E8B400", m["color"]),
        ("#b8860b", m["dark"]), ("#B8860B", m["dark"]),
    ]
    for a, b in reps:
        text = text.replace(a, b)
    return text


def fix_modes(text, key):
    a, b = text.index(START), text.index(END) + len(END)
    return text[:a] + modes_block(key) + text[b:]


def readme(key):
    m = MODES[key]
    lines = [f"# Processing {m['name']} Mode website", "",
             f"Source for [{m['site'].replace('https://', '')}]({m['site']}).", "",
             f"{m['name']} Mode is in active development. This site mirrors the C++ Mode site; "
             "docs and examples are not written yet, so some links lead nowhere for now.", "",
             "Other modes:", ""]
    lines += [f"- [{mm['name']} Mode]({mm['site']})" for k, mm in MODES.items() if k != key]
    lines += ["", f"Maintained by [{AUTHOR}](https://github.com/{AUTHOR}).", ""]
    return "\n".join(lines)


def clone(key, src):
    m = MODES[key]
    dst = src.parent / f"processing-{key}.github.io"
    dst.mkdir(exist_ok=True)
    for child in dst.iterdir():
        if child.name == ".git":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    count = 0
    for path in sorted(src.rglob("*")):
        if path.is_dir() or skip(path, src):
            continue
        rel = path.relative_to(src)
        rel = Path(rebrand(str(rel), m))  # e.g. assets/cppmode-theme.css -> luamode-theme.css
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() in TEXT_EXT:
            text = path.read_text(errors="surrogateescape")
            for old, new in COPY[key].items():
                text = text.replace(old, new)
            text = rebrand(text, m)
            if START in text:
                text = fix_modes(text, key)
            out.write_text(text, errors="surrogateescape")
        else:
            shutil.copy2(path, out)
        count += 1
    (dst / "README.md").write_text(readme(key))
    print(f"{key}: {count} files -> {dst}")


if __name__ == "__main__":
    src = Path.cwd()
    if not (src / "assets" / "nav.js").exists():
        sys.exit("Run this from the root of processing-cpp.github.io")
    patch_source_nav(src)
    for k in (sys.argv[1:] or ["lua", "rust", "scheme"]):
        clone(k, src)
