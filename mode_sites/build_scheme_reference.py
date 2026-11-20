#!/usr/bin/env python3
"""Makes content/reference.yml for the Scheme site from the C++ one.

Same entries, categories and descriptions (Processing's API), written the
Scheme Mode way: kebab-case names, calls in parentheses, methods with the
object first. An entry is kept only when Scheme Mode has it: its name is in
SchemeMode's keywords.txt, or the Python runtime SchemeMode puts in front of
every sketch defines it. "Under the Hood" shows that Python when there is
some (functions the engine has natively have none).

    python3 mode_sites/build_scheme_reference.py [SCHEMEMODE_DIR]

Run from the root of processing-cpp.github.io; needs Java (it runs Scheme
Mode's own converter once to get the runtime). Writes
../processing-scheme.github.io/content/reference.yml.
"""
import re, subprocess, sys, tempfile
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCM = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "sketchbook/modes/SchemeMode")


def kebab(n):
    if re.fullmatch(r"[A-Z0-9_]+", n):
        return n.replace("_", "-")
    n = {"heading2D": "heading", "random2D": "random2-d", "random3D": "random3-d"}.get(n, n)
    n = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", n)
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"-\1", n).lower()


def snake(k):
    if re.fullmatch(r"[A-Z][A-Z0-9_-]*", k):
        return k.replace("-", "_")
    s = k.replace("->", "_to_").replace("-", "_").replace("!", "")
    return s[:-1] + "_p" if s.endswith("?") else s


def runtime():
    """The Python SchemeMode puts in front of a sketch."""
    jar = SCM / "mode" / "SchemeMode.jar"
    with tempfile.TemporaryDirectory() as d:
        src, out = Path(d) / "t.scm", Path(d) / "t.py"
        src.write_text("(define (setup) (size 100 100))\n")
        r = subprocess.run(["java", "-cp", str(jar), "processing.mode.scheme.SchemeCli", str(src), str(out)],
                           capture_output=True, text=True)
        if not out.exists():
            sys.exit("couldn't run SchemeCli (build the jar first: gradle jar)\n" + r.stdout + r.stderr)
        text = out.read_text()
    return text.split("\n_scm_wrap(globals())")[0]


def py_def(py, name):
    """def name(...) and its body, or name = ... (one line)"""
    lines = py.split("\n")
    found = None
    for i, l in enumerate(lines):
        if re.match(r"(\s*)def " + re.escape(name) + r"\(", l):
            found = i  # the last one wins, as in Python
    if found is not None:
        ind = len(lines[found]) - len(lines[found].lstrip())
        j = found + 1
        while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > ind):
            j += 1
        body = [l[ind:] for l in lines[found:j]]
        while body and not body[-1].strip():
            body.pop()
        return "\n".join(body[:30])
    for l in reversed(lines):
        if re.match(r"^" + re.escape(name) + r"\s*=\s*\S", l) and "globals()" not in l:
            return l.strip()
    return None


def plain(text):
    reps = [(r"std::vector<std::string>", "a list of strings"), (r"std::vector<[^>]*>", "a list"),
            (r"\bthe vector\b", "the list"), (r"std::vector", "list"), (r"std::string", "string"), (r"std::map<[^>]*>", "a hash table"),
            (r"std::function<[^>]*>", "a function"), (r"\bnullptr\b", "#f"), (r"\bpointer\b", "value"),
            (r"\bstd::(\w+)", r"\1"), (r"\bC\+\+ Mode\b", "Scheme Mode"), (r"\bC\+\+", "Scheme"), (r"->", "."),
            (r"\btrue\b", "#t"), (r"\bfalse\b", "#f")]
    for a, b in reps:
        text = re.sub(a, b, text)
    # names in the text the way a sketch writes them
    return re.sub(r"\b([a-z]+[A-Z]\w*)\(\)", lambda m: kebab(m.group(1)), text)


TYPES = {"float": "number", "int": "integer", "double": "number", "long": "integer", "byte": "integer",
         "boolean": "boolean", "bool": "boolean", "char": "char", "color": "color", "String": "string",
         "std::string": "string", "PImage": "image", "PGraphics": "graphics", "PFont": "font",
         "PShape": "shape", "PVector": "vector", "Table": "table", "TableRow": "table row", "XML": "xml",
         "any": "any", "T": "any", "void": ""}


def ty(t):
    if not t:
        return ""
    t = t.replace("const ", "").replace("&", "").replace("*", "").strip()
    if t in TYPES:
        return TYPES[t]
    if t.startswith("std::vector") or t.endswith("[]"):
        return "list"
    if t.startswith("std::function"):
        return "procedure"
    if t.startswith("std::map") or t.startswith("HashMap"):
        return "hash table"
    return t


EVENTS = {"setup", "draw", "settings", "mousePressed", "mouseReleased", "mouseClicked", "mouseMoved",
          "mouseDragged", "mouseWheel", "keyPressed", "keyReleased", "keyTyped", "windowMoved", "windowResized"}
VARS = {"mousePressed": "mouse-is-pressed", "keyPressed": "key-is-pressed", "mouseDX": "moved-x", "mouseDY": "moved-y"}
# the values the converter reads straight from the engine (Transpiler's DYNATTR)
DYNATTR = {"mouse-x", "mouse-y", "pmouse-x", "pmouse-y", "mouse-is-pressed", "mouse-button", "mouse-wheel",
           "moved-x", "moved-y", "key", "key-code", "key-is-pressed", "width", "height", "focused",
           "pixel-width", "pixel-height", "frame-count", "delta-time", "display-width", "display-height"}
CLASS_SYNTAX = {
    "PVector": '(define v (PVector x y))', "PImage": '(define img (load-image "file.png"))',
    "PGraphics": "(define pg (create-graphics w h))", "PFont": '(define f (create-font "name" size))',
    "PShape": '(define s (load-shape "file.svg"))', "Table": '(define t (load-table "data.csv" "header"))',
    "TableRow": '(define row (get-row t 0))', "XML": '(define x (load-xml "data.xml"))',
    "HashMap": "(define m (make-hash-table))\n(hash-table-set! m \"key\" 1)\n(hash-table-ref m \"key\")",
    "PrintWriter": '(define out (create-writer "file.txt"))', "BufferedReader": '(define in (create-reader "file.txt"))',
}
LABEL = "src/java/processing/mode/scheme/Transpiler.java, the Python every sketch runs with"


def main():
    data = yaml.safe_load(open(ROOT / "assets" / "reference.yml"))
    py = runtime()
    kw = {}
    for l in (SCM / "keywords.txt").read_text().splitlines():
        p = l.split("\t")
        if len(p) == 2:
            kw[p[0]] = p[1]

    def has(k):
        s = snake(k)
        return k in DYNATTR or k in kw or py_def(py, s) is not None or re.search(r"['\s(]" + re.escape(s) + r"['\s,)]", py) is not None

    out, missing = [], []
    for e in data["entries"]:
        raw = e["name"].lstrip("_")
        name = raw[:-2] if raw.endswith("()") else raw
        is_fn = raw.endswith("()")
        ne = dict(slug=e["slug"], name="", cat_tag=e.get("cat_tag", ""), description=plain(e.get("description", "")),
                  related=e.get("related") or [], params=[], returns="", uth=[])

        if e["slug"].endswith("_class") or e.get("methods") or name in CLASS_SYNTAX:
            meths = []
            for m in e.get("methods") or []:
                mm = re.match(r"(\w+)\s*\((.*)\)", m.get("sig", ""))
                if not mm:
                    continue
                k = kebab(mm.group(1))
                if not has(k):
                    continue
                args = [kebab(re.sub(r".*?(\w+)\s*$", r"\1", a.strip())) for a in mm.group(2).split(",") if a.strip()]
                obj = re.search(r"\(define (\S+)", CLASS_SYNTAX.get(name, ""))
                args = [x + "2" if obj and x == obj.group(1) else x for x in args]
                meths.append({"sig": "(" + " ".join([k, obj.group(1) if obj else "x"] + args) + ")",
                              "desc": plain(m.get("desc", ""))})
            if name not in CLASS_SYNTAX:
                missing.append(e["name"])
                continue
            ne.update(name=name, syntax=CLASS_SYNTAX[name], returns=ty(name), methods=meths)
            ne["description"] += " Methods take the object first: v.add(w) is (add v w)."
            out.append(ne)
            continue

        if not is_fn:
            if re.fullmatch(r"[A-Z0-9_]+", name):
                k = kebab(name)
                if not has(k) and not has(name):
                    missing.append(e["name"]); continue
                ne.update(name=k, syntax=k, returns="number")
            else:
                k = VARS.get(name, kebab(name))
                if not has(k):
                    missing.append(e["name"]); continue
                ne.update(name=k, syntax=k, returns=ty(e.get("returns")))
            out.append(ne)
            continue

        k = kebab(name)
        if e["slug"] == "pixels_arr" or name == "pixels[]":
            continue
        if name in EVENTS:
            ne.update(name=f"({k})", syntax=f"(define ({k})\n  ...)")
            if name in ("mousePressed", "keyPressed"):
                ne["description"] += f" To ask whether it's held right now, read {VARS[name]}."
            out.append(ne)
            continue
        if not has(k):
            missing.append(e["name"]); continue
        calls = []
        for line in (e.get("syntax") or "").split("\n"):
            m = re.match(r"\s*[\w:<>,*& .]*?\b" + re.escape(name) + r"\s*\((.*)\)\s*;?\s*$", line)
            if m:
                args = [kebab(re.sub(r".*?(\w+)\s*$", r"\1", a.strip())) for a in m.group(1).split(",") if a.strip()]
                calls.append("(" + " ".join([k] + args) + ")")
        ne["name"] = f"({k})"
        ne["syntax"] = "\n".join(dict.fromkeys(calls)) or f"({k})"
        ne["params"] = [{"name": kebab(p.get("name", "")), "type": ty(p.get("type")), "desc": plain(p.get("desc", ""))}
                        for p in e.get("params") or []]
        ne["returns"] = ty(e.get("returns"))
        d = py_def(py, snake(k))
        if d and d.startswith("def "):
            ne["uth"] = [[LABEL, d]]
        out.append(ne)

    # pixels: a vector the sketch fills in
    src = next((e for e in data["entries"] if e["slug"] == "pixels_arr"), None)
    if src:
        out.append(dict(slug="pixels_arr", name="pixels", cat_tag=src.get("cat_tag", ""),
                        description=plain(src.get("description", "")) + " In Scheme Mode it's a vector, counted from 0 like in Processing.",
                        related=src.get("related") or [], params=[], returns="vector", uth=[],
                        syntax="(load-pixels)\n(vector-set! pixels (+ x (* y width)) (color 255 0 0))\n(update-pixels)"))
    keep = {e["slug"] for e in out}
    for e in out:
        e["related"] = [r for r in e["related"] if r in keep]
    sidebar = []
    for cat in data["sidebar"]:
        subs = [{**s, "slugs": [x for x in s["slugs"] if x in keep]} for s in cat["subcats"]]
        subs = [s for s in subs if s["slugs"]]
        if subs:
            sidebar.append({**cat, "subcats": subs})
    dst = ROOT.parent / "processing-scheme.github.io" / "content" / "reference.yml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(yaml.safe_dump({"sidebar": sidebar, "entries": out}, sort_keys=False, allow_unicode=True, width=1000))
    missing = [m for m in missing if m != "pixels[]"]
    print(f"scheme: {len(out)} entries; not in the mode ({len(missing)}): {', '.join(missing)}")


if __name__ == "__main__":
    main()
