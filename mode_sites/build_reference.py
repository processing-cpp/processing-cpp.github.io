#!/usr/bin/env python3
"""Makes content/reference.yml for the Lua and Rust sites from the C++ one.

Same entries, names, categories and descriptions (Processing's API), with
the syntax, types and "Under the Hood" code taken from the mode itself:
the RustMode engine (src/*.rs) for Rust, and LuaMode's prelude.lua and
runner bindings for Lua. An entry the mode doesn't have is left out (and
listed at the end), so the site never documents something that isn't there.

    python3 mode_sites/build_reference.py RUSTMODE_DIR LUAMODE_DIR

Run from the root of processing-cpp.github.io; writes into
../processing-{rust,lua}.github.io/content/reference.yml.
"""
import json, re, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
RUST = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "sketchbook/modes/RustMode")
LUA = Path(sys.argv[2] if len(sys.argv) > 2 else Path.home() / "sketchbook/modes/LuaMode")


def snake(n):
    n = {"heading2D": "heading", "random2D": "random_2d", "random3D": "random_3d"}.get(n, n)
    n = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", n)
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", n).lower()


# ── description text: C++ words to plain Processing words ─────────────────
def plain(text, lang):
    reps = [
        (r"std::vector<std::string>", "a list of strings"), (r"std::vector<[^>]*>", "a list"),
        (r"std::string", "a string" if lang == "lua" else "String"), (r"std::map<[^>]*>", "a map"),
        (r"std::function<[^>]*>", "a function"), (r"\bnullptr\b", "nil" if lang == "lua" else "None"),
        (r"\bpointer\b", "handle"), (r"\bstd::(\w+)", r"\1"),
        (r"\bC\+\+", "Lua" if lang == "lua" else "Rust"), (r"->", "."),
    ]
    for a, b in reps:
        text = re.sub(a, b, text)
    return text


# ── Rust: the engine's functions ──────────────────────────────────────────
def rust_sources():
    files = {}
    for f in sorted((RUST / "src").glob("*.rs")):
        files[f.name] = f.read_text()
    return files


def block_at(text, i):
    """from text[i] (start of a line) to the end of its {...} (or ;)"""
    j = i
    depth = 0
    started = False
    while j < len(text):
        c = text[j]
        if c == "{":
            depth += 1
            started = True
        elif c == "}":
            depth -= 1
            if started and depth == 0:
                return text[i:j + 1]
        elif c == ";" and not started:
            return text[i:j + 1]
        elif c == "\n" and not started and text[i:j].rstrip().endswith(";"):
            return text[i:j]
        j += 1
    return text[i:j]


def rust_defs(files, name):
    """every `pub fn name(...)` (free function) in the engine, with its body"""
    out = []
    pat = re.compile(r"^(?:#\[inline\]\s*)?pub fn " + re.escape(name).replace("r\\#", "r#") + r"\s*[<(]", re.M)
    for fn, text in files.items():
        for m in pat.finditer(text):
            # doc comments right above
            start = m.start()
            lines = text[:start].split("\n")
            doc = []
            while lines and lines[-1].strip().startswith("///"):
                doc.insert(0, lines.pop().strip())
            code = block_at(text, m.start())
            out.append((fn, "\n".join(doc + [code]) if doc else code, code.split("{")[0].strip()))
    return out


def rust_const(files, name):
    pat = re.compile(r"^pub (?:const|static) " + re.escape(name) + r"\s*:[^=]*=.*$", re.M)
    for fn, text in files.items():
        m = pat.search(text)
        if m:
            return fn, m.group(0)
    if name in ("PI", "TAU"):
        return "lib.rs", f"pub use std::f32::consts::{name};"
    return None


def rust_method_defs(files, typename, method):
    """`fn method` inside `impl Type` / trait impl for the type"""
    out = []
    for fn, text in files.items():
        for m in re.finditer(r"^\s*impl(?:<[^>]*>)?\s+(?:[\w:]+\s+for\s+)?" + re.escape(typename) + r"\b[^{]*\{", text, re.M):
            body = block_at(text, m.start())
            for mm in re.finditer(r"^\s*(?:#\[inline\]\s*)?(?:pub )?fn " + re.escape(method) + r"\s*[<(]", body, re.M):
                out.append((fn, block_at(body, mm.start()).strip()))
    return out


RTYPES = {"float": "f32", "int": "i32", "boolean": "bool", "bool": "bool", "char": "char", "color": "Color",
          "String": "&str", "std::string": "&str", "PImage": "u64 (image)", "PImage*": "u64 (image)",
          "PGraphics": "u64 (layer)", "PGraphics*": "u64 (layer)", "PFont": "u64 (font)", "PShape": "PShape",
          "PVector": "PVector", "long": "i64", "double": "f32", "byte": "u8", "any": "impl Display"}
LTYPES = {"float": "number", "int": "number", "boolean": "boolean", "bool": "boolean", "char": "string",
          "color": "color", "String": "string", "std::string": "string", "long": "number", "double": "number",
          "byte": "number", "any": "any", "PImage": "PImage", "PImage*": "PImage", "PGraphics": "PGraphics",
          "PGraphics*": "PGraphics", "PFont": "PFont", "PShape": "PShape", "PVector": "PVector", "T": "any"}


def map_type(t, table, lang):
    if t is None:
        return None
    t = t.strip().replace("const ", "").replace("&", "").strip()
    if t in table:
        return table[t]
    if t.startswith("std::vector"):
        inner = re.sub(r"^std::vector<(.*)>$", r"\1", t)
        return "table" if lang == "lua" else f"&[{RTYPES.get(inner.strip(), inner.strip())}]"
    if t.endswith("*"):
        return map_type(t[:-1], table, lang)
    if t.startswith("std::function"):
        return "function" if lang == "lua" else "impl Fn()"
    return t


def rust_param_types(sig):
    m = re.search(r"\((.*)\)", sig, re.S)
    if not m:
        return []
    out = []
    depth = 0
    cur = ""
    for c in m.group(1):
        if c in "<([":
            depth += 1
        elif c in ">)]":
            depth -= 1
        if c == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
    if cur.strip():
        out.append(cur)
    res = []
    for p in out:
        if ":" in p:
            n, t = p.split(":", 1)
            res.append((n.strip().lstrip("_"), t.strip()))
    return res


def build_rust(entries, files, overloads, sig):
    out, missing = [], []
    for e in entries:
        name = e["name"].rstrip("()").lstrip("_")
        slug = e["slug"]
        is_fn = e["name"].endswith("()")
        ne = dict(slug=slug, name=e["name"].lstrip("_") if e["name"].startswith("_") else e["name"],
                  cat_tag=e.get("cat_tag", ""), description=plain(e.get("description", ""), "rust"),
                  related=e.get("related") or [])
        if slug.endswith("_class") or e.get("methods"):
            tname = {"XML": "Xml", "JSONObject": "Json", "JSONArray": "Json"}.get(name, name)
            meths = []
            uth = []
            for mth in e.get("methods") or []:
                mname = re.match(r"(\w+)", mth.get("sig", ""))
                if not mname:
                    continue
                sn = snake(mname.group(1))
                defs = rust_method_defs(files, tname, sn) or rust_method_defs(files, "PImageExt", sn) \
                    if tname in ("PImage", "PGraphics") else rust_method_defs(files, tname, sn)
                if defs:
                    sigline = defs[0][1].split("{")[0].strip().replace("pub fn ", "fn ")
                    meths.append({"sig": sigline.replace("fn ", "", 1), "desc": plain(mth.get("desc", ""), "rust")})
                    if len(uth) < 6:
                        uth.append(defs[0])
            if not meths and tname not in ("PImage", "PGraphics", "PFont"):
                missing.append(e["name"])
                continue
            ne["syntax"] = {"PImage": "let img: u64 = load_image(\"file.png\");",
                            "PGraphics": "let pg: u64 = create_graphics(w, h);",
                            "PFont": "let font: u64 = create_font(\"name\", size);",
                            "PVector": "let v = PVector::new(x, y);",
                            "PShape": "let s = create_shape();  // or load_shape(\"file.svg\") for a u64 id"}.get(tname, f"let x: {tname} = ...;")
            ne["params"] = []
            ne["returns"] = tname if tname not in ("PImage", "PGraphics", "PFont") else "u64"
            ne["methods"] = meths
            ne["uth"] = [[f"src/{fn}", code] for fn, code in uth]
            out.append(ne)
            continue
        # a variable or constant
        if not is_fn:
            if re.fullmatch(r"[A-Z_][A-Z0-9_]*", name):
                c = rust_const(files, name)
                if not c:
                    missing.append(e["name"])
                    continue
                ne.update(syntax=name, params=[], returns="f32" if "PI" in name or name == "TAU" else "u32",
                          uth=[[f"src/{c[0]}", c[1]]])
                out.append(ne)
                continue
            fname = snake(name)
            defs = rust_defs(files, fname)
            if not defs:
                missing.append(e["name"])
                continue
            ret = re.search(r"->\s*([^{]+)", defs[0][2])
            ne.update(syntax=f"{fname}()", params=[], returns=ret.group(1).strip() if ret else "",
                      uth=[[f"src/{d[0]}", d[1]] for d in defs[:2]])
            ne["description"] += f" In Rust it is the function {fname}()" + (
                f"; inside setup(), draw() and the event functions the bare name {name} works too." if name in (
                    "width", "height", "mouseX", "mouseY", "pmouseX", "pmouseY", "frameCount", "key", "keyCode",
                    "mousePressed", "keyPressed", "millis", "focused") else ".")
            out.append(ne)
            continue
        # a function: the engine's own names for it
        fname = snake(name)
        if slug.endswith("_fn") and name in ("mousePressed", "keyPressed", "mouseReleased", "keyReleased"):
            ne.update(syntax=f"fn {fname}() {{\n    // runs once each time it happens\n}}", params=[], returns="",
                      description=plain(e.get("description", ""), "rust"), uth=[])
            out.append(ne)
            continue
        if name in ("sin", "cos", "tan", "asin", "acos", "atan", "atan2"):
            arg = "y.atan2(x)" if name == "atan2" else f"angle.{name}()"
            ne.update(syntax=f"{arg}  // a method of f32, from Rust's standard library",
                      params=[{"name": p.get("name"), "type": "f32", "desc": plain(p.get("desc", ""), "rust")} for p in e.get("params") or []],
                      returns="f32", uth=[])
            ne["description"] += f" In Rust it is the f32 method {name}(): write {arg}."
            out.append(ne)
            continue
        if name == "pixels[]" or slug.startswith("pixels"):
            pass
        if name == "match":
            d = rust_defs(files, "match_re")
            ne.update(syntax="match_(text, pattern)  // match is a Rust keyword; match_re() is the same",
                      params=[{"name": p.get("name"), "type": "&str", "desc": plain(p.get("desc", ""), "rust")} for p in e.get("params") or []],
                      returns="Option<Vec<String>>", uth=[[f"src/{x[0]}", x[1]] for x in d[:1]])
            out.append(ne)
            continue
        if name == "loop":
            fname = "r#loop"
        if name == "mask":
            d = rust_method_defs(files, "u64", "mask")
            ne.update(syntax="img.mask(mask_img)", params=[{"name": "maskImg", "type": "u64 (image)", "desc": "the image whose brightness becomes the alpha"}],
                      returns="bool", uth=[[f"src/{f}", c] for f, c in d[:1]])
            out.append(ne)
            continue
        names = [fname] + [v for k, v in sorted(overloads.get(fname, {}).items())]
        if fname == "random":
            names = ["random", "random_range"]
        defs = []
        seen = set()
        for n in names:
            for d in rust_defs(files, n):
                if d[2] not in seen:
                    seen.add(d[2])
                    defs.append(d)
        if not defs:
            # callbacks the sketch defines
            if name in ("setup", "draw", "settings", "mouseClicked", "mouseMoved", "mouseDragged", "mouseWheel",
                        "keyTyped", "mouseReleased", "keyReleased", "windowMoved", "windowResized"):
                ne.update(syntax=f"fn {fname}() {{\n    ...\n}}", params=[], returns="", uth=[])
                out.append(ne)
                continue
            missing.append(e["name"])
            continue
        # Syntax: how a sketch calls it (Processing's argument lists) and the engine functions behind it
        calls = []
        for line in (e.get("syntax") or "").split("\n"):
            m = re.match(r"\s*[\w:<>,* ]*?\b" + re.escape(name) + r"\s*\((.*)\)\s*$", line)
            if m:
                args = [re.sub(r".*?(\w+)\s*$", r"\1", a.strip()) for a in m.group(1).split(",") if a.strip()]
                calls.append(f"{fname}({', '.join(args)})")
        sigs = [d[2].replace("#[inline] ", "").replace("pub fn ", "fn ") for d in defs]
        ne["syntax"] = "\n".join(dict.fromkeys(calls)) + ("\n\n// " + ("the engine functions behind it:" if len(sigs) > 1 else "the engine function:") + "\n" if calls else "") + "\n".join(sigs)
        ptypes = {}
        for d in defs:
            for n, t in rust_param_types(d[2]):
                ptypes.setdefault(n, t)
        params = []
        for p in e.get("params") or []:
            t = ptypes.get(p.get("name")) or map_type(p.get("type"), RTYPES, "rust")
            params.append({"name": p.get("name"), "type": t, "desc": plain(p.get("desc", ""), "rust")})
        ne["params"] = params
        ret = re.search(r"->\s*(.+)$", defs[0][2])
        ne["returns"] = ret.group(1).strip() if ret else ""
        ne["uth"] = [[f"src/{d[0]}", d[1]] for d in defs[:4]]
        out.append(ne)
    return out, missing


# ── Lua: prelude.lua functions and the runner's bindings ──────────────────
def lua_defs(prelude, main_rs, name):
    out = []
    lines = prelude.split("\n")
    for i, l in enumerate(lines):
        m = re.match(r"^(\s*)(?:local\s+)?function\s+([\w.:]+)\s*\(", l)
        if m and m.group(2) in (name, f"_G.{name}"):
            ind = m.group(1)
            j = i
            if re.search(r"\bend\s*$", l) and l.count("function") == 1 and l.strip().endswith("end"):
                out.append(("runner/src/prelude.lua", l.strip()))
                continue
            while j < len(lines) and not (lines[j].startswith(ind + "end") and j > i):
                j += 1
            doc = []
            k = i - 1
            while k >= 0 and lines[k].strip().startswith("--"):
                doc.insert(0, lines[k].strip())
                k -= 1
            body = "\n".join(x[len(ind):] if x.startswith(ind) else x for x in lines[i:j + 1])
            out.append(("runner/src/prelude.lua", "\n".join(doc[-6:] + [body])))
        elif re.match(r"^\s*" + re.escape(name) + r"\s*=\s*(print|function)", l):
            out.append(("runner/src/prelude.lua", l.strip()))
    if out:
        return out
    ml = lua_multi(prelude, name)
    if ml:
        return [("runner/src/prelude.lua", ml)]
    m = re.search(r'g\.set\("' + re.escape(name) + r'",', main_rs)
    if m:
        start = main_rs.rfind("\n", 0, m.start()) + 1
        depth = 0
        j = m.start()
        while j < len(main_rs):
            if main_rs[j] == "(":
                depth += 1
            elif main_rs[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        end = main_rs.find("\n", j)
        out.append(("runner/src/main.rs", "\n".join(x[4:] if x.startswith("    ") else x for x in main_rs[start:end].split("\n"))))
    return out


def lua_multi(prelude, name):
    for l in prelude.split("\n"):
        m = re.match(r"^\s*([\w, ]+?)\s*=\s*(.+)$", l)
        if m and "," in m.group(1) and name in [x.strip() for x in m.group(1).split(",")]:
            return l.strip()
    return None


def lua_has(prelude, main_rs, name):
    if lua_multi(prelude, name):
        return True
    return bool(re.search(r'(^|\W)' + re.escape(name) + r'\s*=|function\s+' + re.escape(name) + r'\b', prelude, re.M)) \
        or f'"{name}"' in main_rs


def build_lua(entries, prelude, main_rs):
    out, missing = [], []
    for e in entries:
        name = e["name"].rstrip("()").lstrip("_")
        slug = e["slug"]
        is_fn = e["name"].endswith("()")
        ne = dict(slug=slug, name=e["name"].lstrip("_") if e["name"].startswith("_") else e["name"],
                  cat_tag=e.get("cat_tag", ""), description=plain(e.get("description", ""), "lua"),
                  related=e.get("related") or [])
        if slug.endswith("_class") or e.get("methods") or name in ("PFont", "PImage", "PGraphics", "PShape"):
            tname = name
            meths = []
            for mth in e.get("methods") or []:
                mname = re.match(r"(\w+)\s*\((.*)\)", mth.get("sig", ""))
                if not mname:
                    continue
                mn = mname.group(1)
                if re.search(r"(:|\.)" + re.escape(mn) + r"\b", prelude) or f'"{mn}"' in main_rs:
                    args = ", ".join(re.sub(r".*?(\w+)\s*$", r"\1", a.strip()) for a in mname.group(2).split(",") if a.strip())
                    meths.append({"sig": f":{mn}({args})", "desc": plain(mth.get("desc", ""), "lua")})
            if not meths and tname not in ("PFont", "PImage", "PGraphics", "PShape"):
                missing.append(e["name"])
                continue
            ne["syntax"] = {"PImage": 'local img = loadImage("file.png")', "PGraphics": "local pg = createGraphics(w, h)",
                            "PFont": 'local font = createFont("name", size)', "PVector": "local v = createVector(x, y)",
                            "PShape": 'local s = loadShape("file.svg")  -- or createShape()',
                            "Table": 'local t = loadTable("data.csv", "header")', "XML": 'local x = loadXML("data.xml")',
                            "TableRow": "for row in t:rows() do ... end"}.get(tname, f"local x = {tname}(...)")
            ne.update(params=[], returns=tname, methods=meths, uth=[])
            out.append(ne)
            continue
        if not is_fn:
            if not lua_has(prelude, main_rs, name) and name not in ("mousePressed", "keyPressed"):
                missing.append(e["name"])
                continue
            ne.update(syntax=name, params=[], returns=map_type(e.get("returns"), LTYPES, "lua") or "", uth=[
                [f, c] for f, c in lua_defs(prelude, main_rs, name)[:1]])
            out.append(ne)
            continue
        if name in ("setup", "draw", "settings", "mousePressed", "mouseReleased", "mouseClicked", "mouseMoved",
                    "mouseDragged", "mouseWheel", "keyPressed", "keyReleased", "keyTyped"):
            ne.update(syntax=f"function {name}()\n  ...\nend", params=[], returns="", uth=[])
            out.append(ne)
            continue
        defs = lua_defs(prelude, main_rs, name)
        if not defs and not lua_has(prelude, main_rs, name):
            missing.append(e["name"])
            continue
        calls = []
        for line in (e.get("syntax") or "").split("\n"):
            m = re.match(r"\s*[\w:<>,* .]*?\b" + re.escape(name) + r"\s*\((.*)\)\s*$", line)
            if m:
                args = [re.sub(r".*?(\w+)\s*$", r"\1", a.strip()) for a in m.group(1).split(",") if a.strip()]
                calls.append(f"{name}({', '.join(args)})")
        ne["syntax"] = "\n".join(dict.fromkeys(calls)) or f"{name}()"
        ne["params"] = [{"name": p.get("name"), "type": map_type(p.get("type"), LTYPES, "lua"),
                         "desc": plain(p.get("desc", ""), "lua")} for p in e.get("params") or []]
        ne["returns"] = "" if e.get("returns") in ("void", None) else map_type(e.get("returns"), LTYPES, "lua")
        ne["uth"] = [[f, c] for f, c in defs[:3]]
        out.append(ne)
    return out, missing


def sidebar_for(sidebar, keep):
    out = []
    for cat in sidebar:
        subs = []
        for sub in cat["subcats"]:
            slugs = [s for s in sub["slugs"] if s in keep]
            if slugs:
                subs.append({**sub, "slugs": slugs})
        if subs:
            out.append({**cat, "subcats": subs})
    return out


def main():
    data = yaml.safe_load(open(ROOT / "assets" / "reference.yml"))
    entries = data["entries"]
    files = rust_sources()
    ov_src = (RUST / "src" / "java" / "OverloadRewriter.java").read_text()
    overloads = {}
    for m in re.finditer(r'Map\.entry\("(\w+)",\s*Map\.of\(([^)]*)\)\)', ov_src):
        parts = [x.strip().strip('"') for x in m.group(2).split(",")]
        overloads[m.group(1)] = {int(parts[i]): parts[i + 1] for i in range(0, len(parts), 2)}
    prelude = (LUA / "runner" / "src" / "prelude.lua").read_text()
    main_rs = (LUA / "runner" / "src" / "main.rs").read_text()
    PIX = {
        "rust": dict(syntax="let mut px = load_pixels();   // every pixel of the canvas, 0xAARRGGBB\npx[y * width() as usize + x] = c.to_argb();\nupdate_pixels(&px);",
                     returns="Vec<u32>", note=" In Rust, load_pixels() hands you a copy as a Vec<u32> (each pixel packed 0xAARRGGBB, Processing's form); change it and give it back with update_pixels(&px). Color::from_u32(p) turns a pixel into a Color."),
        "lua": dict(syntax="loadPixels()\npixels[y * width + x] = color(255, 0, 0)\nupdatePixels()",
                    returns="table", note=" In Lua, pixels is counted from 0 like in Processing, so the same index math works."),
    }
    pix_src = next((e for e in entries if e["slug"] == "pixels_arr"), None)
    for key, (ents, missing) in {"rust": build_rust(entries, files, overloads, None),
                                 "lua": build_lua(entries, prelude, main_rs)}.items():
        if pix_src:
            pe = PIX[key]
            ents.append(dict(slug="pixels_arr", name="pixels[]", cat_tag=pix_src.get("cat_tag", ""),
                             description=plain(pix_src.get("description", ""), key) + pe["note"],
                             related=pix_src.get("related") or [], syntax=pe["syntax"], params=[], returns=pe["returns"], uth=[]))
            missing = [m for m in missing if m != "pixels[]"]
        if key == "lua":
            for e in entries:
                if e["slug"] == "mask_fn":
                    d = lua_defs(prelude, main_rs, "Image.mask")
                    ents.append(dict(slug="mask_fn", name="mask()", cat_tag=e.get("cat_tag", ""), description=plain(e.get("description", ""), "lua"),
                                     related=e.get("related") or [], syntax="img:mask(maskImg)", params=[{"name": "maskImg", "type": "PImage", "desc": "the image whose brightness becomes the alpha"}],
                                     returns="", uth=[["runner/src/prelude.lua", "function Image.mask(img, m) pixelsOf[img] = nil return imageMask(img, m) end"]]))
                    missing = [m for m in missing if m != "mask()"]
        keep = {e["slug"] for e in ents}
        for e in ents:
            e["related"] = [r for r in e["related"] if r in keep]
        out = {"sidebar": sidebar_for(data["sidebar"], keep), "entries": ents}
        dst = ROOT.parent / f"processing-{key}.github.io" / "content" / "reference.yml"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=1000))
        print(f"{key}: {len(ents)} entries; not in the mode ({len(missing)}): {', '.join(missing)}")


if __name__ == "__main__":
    main()
