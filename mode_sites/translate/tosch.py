"""Processing (Java) example -> SchemeMode sketch. First draft; each one is
then turned into Python with SchemeMode's own translator and run, and the few
that need it are fixed by hand in sch_hand/."""
import re, sys
from common import *

# Java names that mean something else in SchemeMode
RENAME = {
    "mousePressed": "mouse-is-pressed", "keyPressed": "key-is-pressed",
    "println": "println", "print": "print",
}
EVENTS = {"setup", "draw", "settings", "mousePressed", "mouseReleased", "mouseClicked", "mouseMoved",
          "mouseDragged", "mouseWheel", "keyPressed", "keyReleased", "keyTyped"}
# user names that would hide a Scheme or SchemeMode function
TAKEN = {"list", "length", "string", "vector", "char", "apply", "min", "max", "abs", "set", "get",
         "map", "filter", "sort", "reverse", "append", "assoc", "member", "error", "exp", "log",
         "round", "floor", "truncate", "iota", "values", "do", "case", "if", "else", "when", "let",
         "define", "begin", "lambda", "quote", "not", "and", "or", "cond", "loop", "point",
         "line", "box", "image", "color", "fill", "stroke", "text", "shape", "red", "green", "blue",
         "alpha", "hue", "noise", "random", "pixels", "time", "second", "minute", "hour", "day",
         "month", "year", "key", "width", "height", "scale", "rotate", "translate", "size",
         "mag", "dist", "lerp", "norm", "sq", "sqrt", "split", "join", "trim", "str", "int", "float",
         "boolean", "byte", "hex", "binary", "unhex", "copy", "mask", "blend", "add", "sub", "mult",
         "div", "dot", "heading", "limit", "normalize"}
LISTS = ("ArrayList", "LinkedList", "IntList", "FloatList", "StringList")
TAKEN_GLOBAL_ONLY = {"x", "y", "z", "angle", "radius", "time", "add", "sub", "x", "copy", "dot"}


def kebab(name):
    """mouseX -> mouse-x, TWO_PI -> TWO-PI, xSpeed -> x-speed, img2 -> img2."""
    if name.strip("_") and name != name.strip("_") and not name.isupper():
        name = name.strip("_")
    if name.isupper() or re.fullmatch(r"[A-Z0-9_]+", name):
        return name.replace("_", "-")
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"-\1", name)
    s = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"-\1", s)
    return s.replace("_", "-").lower()


class Comment:
    def __init__(self, text, trailing=False):
        self.text, self.trailing = text, trailing


BLANK = "\x00blank"


class Raw(str):
    """an atom printed as is"""


# ── printing ──────────────────────────────────────────────────────────────
BODY_AFTER = {"define": 1, "when": 1, "unless": 1, "lambda": 1, "let": 1, "let*": 1, "do": 2,
              "begin": 0, "cond": 0, "case": 1, "else": 0, "if": 1, "define-record-type": 2}


def flat(n):
    if isinstance(n, Comment) or n is BLANK:
        return None
    if isinstance(n, str):
        return n
    parts = []
    for c in n:
        f = flat(c)
        if f is None:
            return None
        parts.append(f)
    return "(" + " ".join(parts) + ")"


def pp(n, ind=0, width=88):
    """pretty-print one form starting at column ind (first line not indented)"""
    if isinstance(n, Comment):
        return n.text
    if isinstance(n, str):
        return n
    f = flat(n)
    if f is not None and n and isinstance(n[0], str) and n[0].endswith("-record"):
        return f
    if f is not None and ind + len(f) <= width and not (n and n[0] in ("define", "do") and len(n) > 3 and any(isinstance(c, list) for c in n[2:]) and ind + len(f) > 60):
        return f
    if not n:
        return "()"
    head = n[0]
    if isinstance(head, list) or isinstance(head, Comment):
        # a list of lists: clauses, bindings
        lines = [pp(head, ind + 1, width)]
        for c in n[1:]:
            lines.append(" " * (ind + 1) + pp(c, ind + 1, width))
        return "(" + join_lines(lines, n[1:], ind + 1) + ")"
    k = BODY_AFTER.get(head)
    if k is not None:
        first = [head] + n[1:1 + k]
        rest = n[1 + k:]
        h = "(" + " ".join(pp(c, ind + 1, width) for c in first)
        if head == "cond" or head == "else":
            rest = n[1:]
            h = "(" + head
        out = [h]
        for c in rest:
            out.append(" " * (ind + 2) + pp(c, ind + 2, width))
        return join_lines(out, rest, ind + 2) + ")"
    # a call: args under the first one when they fit, else indented by 2
    hs = pp(head, ind + 1, width)
    col = ind + 2 + len(hs)
    args = n[1:]
    if col < width - 30 and not any(isinstance(a, Comment) for a in args):
        lines = [f"({hs} " + pp(args[0], col, width)] if args else [f"({hs}"]
        for a in args[1:]:
            lines.append(" " * col + pp(a, col, width))
        return "\n".join(lines) + ")"
    lines = [f"({hs}"]
    for a in args:
        lines.append(" " * (ind + 2) + pp(a, ind + 2, width))
    return join_lines(lines, args, ind + 2) + ")"


def join_lines(lines, items, ind):
    """joins, putting trailing comments on the line before, and blanks as empty lines"""
    if len(items) >= 2 and isinstance(items[-1], Comment) and items[-1].trailing and not isinstance(items[-2], Comment):
        # a comment after the last form would leave the closing paren on its
        # own line: it goes above that form instead
        items = list(items[:-2]) + [Comment(items[-1].text), items[-2]]
        lines = list(lines[:-2]) + [" " * ind + items[-2].text, lines[-2]]
    out = [lines[0]]
    for l, it in zip(lines[1:], items):
        if it is BLANK:
            out.append("")
        elif isinstance(it, Comment) and it.trailing:
            out[-1] += "  " + it.text
        else:
            out.append(l)
    # a form can't end on a comment line: the closing paren would be commented out
    s = "\n".join(out)
    if items and isinstance(items[-1], Comment):
        s += "\n" + " " * ind
    return s


class Sch:
    def __init__(self, src):
        self.src = src
        self.tree, self.b, self.static = parse(src)
        self.scope = Scope()
        self.classes = {}
        self.funcs = {}
        self.overloads = {}
        self.cls = None
        self.notes = []
        self.helpers = set()
        self.need_return = False
        self.renamed = {}

    def t(self, n):
        return text(self.b, n)

    # ── collecting ────────────────────────────────────────────────────────
    def body_nodes(self):
        root = self.tree.root_node
        cls = [c for c in root.children if c.type == "class_declaration"][0]
        body = cls.child_by_field_name("body")
        kids = [c for c in body.children if c.is_named or is_comment(c)]
        if self.static:
            m = [c for c in kids if c.type == "method_declaration"][0]
            kids = [c for c in m.child_by_field_name("body").children if c.is_named or is_comment(c)]
        return kids

    def collect(self, kids):
        for k in kids:
            if k.type == "class_declaration":
                self.add_class(k)
            elif k.type == "method_declaration":
                nm = self.t(k.child_by_field_name("name"))
                self.funcs[nm] = self.decl_type(k)
                self.overloads.setdefault(nm, []).append(k)
            elif k.type in ("field_declaration", "local_variable_declaration"):
                for d in k.children_by_field_name("declarator"):
                    self.scope.add(self.t(d.child_by_field_name("name")), self.decl_type(k, d))

    def add_class(self, k):
        name = self.t(k.child_by_field_name("name"))
        ci = ClassInfo(name, k)
        ci.over = {}
        sup = k.child_by_field_name("superclass")
        if sup:
            ci.base = self.t(named(sup)[0])
        for m in k.child_by_field_name("body").children:
            if m.type == "field_declaration":
                for d in m.children_by_field_name("declarator"):
                    ci.fields[self.t(d.child_by_field_name("name"))] = self.decl_type(m, d)
            elif m.type == "method_declaration":
                mn = self.t(m.child_by_field_name("name"))
                ci.methods[mn] = self.decl_type(m)
                ci.over.setdefault(mn, []).append(m)
            elif m.type == "constructor_declaration":
                ci.ctors.append(m)
            elif m.type == "class_declaration":
                self.add_class(m)
        self.classes[name] = ci

    def decl_type(self, n, d=None):
        t = type_text(self.b, n) or ""
        if d is not None:
            dims = d.child_by_field_name("dimensions")
            if dims:
                t += self.t(dims).replace(" ", "")
        return t

    def field(self, name, ci=None):
        ci = ci or self.cls
        while ci:
            if name in ci.fields:
                return ci.fields[name]
            ci = self.classes.get(ci.base)
        return None

    def field_owner(self, name, ci):
        while ci:
            if name in ci.fields:
                return ci
            ci = self.classes.get(ci.base)
        return None

    def method_of(self, name, ci=None):
        ci = ci or self.cls
        while ci:
            if name in ci.methods:
                return ci
            ci = self.classes.get(ci.base)
        return None

    def all_fields(self, ci):
        chain = []
        while ci:
            chain.insert(0, ci)
            ci = self.classes.get(ci.base)
        out, seen = [], set()
        for c in chain:
            for m in c.node.child_by_field_name("body").children:
                if m.type == "field_declaration":
                    for d in m.children_by_field_name("declarator"):
                        nm = self.t(d.child_by_field_name("name"))
                        if nm not in seen:
                            seen.add(nm)
                            out.append((c, m, d))
        return out

    # ── names ─────────────────────────────────────────────────────────────
    def var(self, name, local=None):
        if name in self.renamed:
            return self.renamed[name]
        k = kebab(name)
        user = self.scope.get(name) is not None or name in self.funcs or (self.cls and self.field(name))
        if k in TAKEN and user:
            k = k + "-v" if len(k) > 1 else k + "1"
        return k

    def cname(self, ci):
        return kebab(ci.name if isinstance(ci, ClassInfo) else ci)

    # ── types (same rules as the Lua translator) ──────────────────────────
    def ty(self, n):
        k = n.type
        if k in ("decimal_integer_literal", "hex_integer_literal"):
            return "int"
        if k == "decimal_floating_point_literal":
            return "float"
        if k == "string_literal":
            return "String"
        if k == "character_literal":
            return "char"
        if k in ("true", "false"):
            return "boolean"
        if k == "parenthesized_expression":
            return self.ty(named(n)[0])
        if k == "identifier":
            name = self.t(n)
            if self.scope.local(name):
                return self.scope.get(name)
            if self.cls and self.field(name):
                return self.field(name)
            if self.scope.get(name):
                return self.scope.get(name)
            if name in INT_BUILTINS:
                return "int"
            if name == "key":
                return "char"
            return None
        if k == "binary_expression":
            op = self.t(n.child_by_field_name("operator"))
            a, c = self.ty(n.child_by_field_name("left")), self.ty(n.child_by_field_name("right"))
            if op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                return "boolean"
            if op == "+" and ("String" in (a, c)):
                return "String"
            if intlike(a) and intlike(c):
                return "int"
            if numeric(a) and numeric(c):
                return "float" if "float" in (a, c) or "double" in (a, c) else "int"
            return a or c
        if k == "unary_expression":
            op = self.t(n.child_by_field_name("operator"))
            return "boolean" if op == "!" else self.ty(named(n)[0])
        if k == "cast_expression":
            return self.t(n.child_by_field_name("type"))
        if k == "array_access":
            return elem_type(self.ty(n.child_by_field_name("array")))
        if k == "field_access":
            obj, f = n.child_by_field_name("object"), self.t(n.child_by_field_name("field"))
            if f == "length":
                return "int"
            ot = self.ty(obj) if obj.type != "this" else (self.cls.name if self.cls else None)
            if ot in self.classes:
                return self.field(f, self.classes[ot])
            if f in ("x", "y", "z"):
                return "float"
            if f in ("width", "height"):
                return "int"
            if f == "pixels":
                return "int[]"
            return None
        if k == "method_invocation":
            name = self.t(n.child_by_field_name("name"))
            obj = n.child_by_field_name("object")
            if obj is None:
                if self.cls and self.method_of(name):
                    return self.method_of(name).methods[name]
                if name in self.funcs:
                    return self.funcs[name]
                r = RET.get(name)
                if r is None and name in ("abs", "min", "max", "constrain"):
                    args = named(n.child_by_field_name("arguments"))
                    ts = [self.ty(a) for a in args]
                    return "int" if all(intlike(x) for x in ts) else "float"
                return r
            ot = self.ty(obj)
            if ot == "String":
                return {"length": "int", "charAt": "char", "indexOf": "int", "equals": "boolean"}.get(name, "String")
            if ot and base_type(ot) in ("ArrayList", "IntList", "FloatList", "StringList"):
                if name == "get":
                    return elem_type(ot)
                if name == "size":
                    return "int"
            if ot in self.classes:
                ci = self.method_of(name, self.classes[ot])
                return ci.methods[name] if ci else None
            if ot == "PVector" and name in ("mag", "dist", "heading", "dot", "magSq"):
                return "float"
            if ot == "PVector":
                return "PVector"
            if self.t(obj) == "PVector":
                return "float" if name in ("dist", "dot", "angleBetween") else "PVector"
            if name in ("get",) and ot in ("PImage", "PGraphics"):
                return "color" if len(named(n.child_by_field_name("arguments"))) == 2 else "PImage"
            if ot == "Table" and name == "getRowCount":
                return "int"
            if name in ("getFloat",):
                return "float"
            if name in ("getInt", "getChildCount", "getRowCount"):
                return "int"
            if name in ("getString",):
                return "String"
            return None
        if k == "object_creation_expression":
            return re.sub(r"\s+", "", self.t(n.child_by_field_name("type")))
        if k == "array_creation_expression":
            return self.t(n.child_by_field_name("type")) + "[]" * len(
                [c for c in n.children if c.type in ("dimensions_expr",)] or [1])
        if k == "ternary_expression":
            return self.ty(n.child_by_field_name("consequence"))
        if k == "assignment_expression":
            return self.ty(n.child_by_field_name("left"))
        return None

    # ── expressions ───────────────────────────────────────────────────────
    def args(self, n):
        out = []
        for a in named(n.child_by_field_name("arguments")):
            if is_comment(a):
                self.notes.append(self.t(a)[2:].strip() if a.type == "line_comment" else self.t(a)[2:-2].strip())
            else:
                out.append(self.ex(a))
        return out

    def num(self, s):
        return s

    def ex(self, n, want_int=False):
        k = n.type
        if k == "decimal_integer_literal":
            return self.t(n).rstrip("lL")
        if k == "hex_integer_literal":
            v = int(self.t(n).rstrip("lL"), 16)
            h = self.t(n)[2:].rstrip("lL")
            if len(h) == 8 and v >> 24:
                a, r, g, bb = (v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255
                return ["color", str(r), str(g), str(bb)] + ([] if a == 255 else [str(a)])
            return "#x" + h.upper()
        if k == "decimal_floating_point_literal":
            v = self.t(n).rstrip("fFdD")
            if v.startswith("."):
                v = "0" + v
            if v.endswith("."):
                v += "0"
            if "e" in v.lower() and "." not in v.lower().split("e")[0]:
                v = v.lower().replace("e", ".0e")
            return v
        if k == "string_literal":
            return Raw(self.t(n))
        if k == "character_literal":
            c = self.t(n)[1:-1]
            named_chars = {" ": "space", "\\n": "newline", "\\t": "tab", "\\\\": "\\", "\\'": "'"}
            return "#\\" + named_chars.get(c, c)
        if k == "true":
            return "#t"
        if k in ("false", "null_literal"):
            return "#f"
        if k == "this":
            return "self"
        if k == "identifier":
            name = self.t(n)
            if not self.scope.local(name) and self.cls and self.field(name):
                return [self.cname(self.field_owner(name, self.cls)) + "-" + kebab(name), "self"]
            if name in RENAME and not self.scope.get(name):
                return RENAME[name]
            return self.var(name)
        if k == "parenthesized_expression":
            return self.ex(named(n)[0], want_int)
        if k == "binary_expression":
            return self.binary(n, want_int)
        if k == "unary_expression":
            op = self.t(n.child_by_field_name("operator"))
            v = self.ex(n.child_by_field_name("operand"), want_int)
            if op == "!":
                return ["not", v]
            if op == "-":
                if isinstance(v, str) and re.fullmatch(r"[\d.]+", v):
                    return "-" + v
                return ["-", v]
            if op == "~":
                return ["bitwise-not", v]
            return v
        if k == "update_expression":
            return Raw(";TODO " + self.t(n))
        if k == "cast_expression":
            t = self.t(n.child_by_field_name("type"))
            v = self.ex(n.child_by_field_name("value"))
            if t in ("int", "long", "short"):
                return ["int", v]
            if t == "char":
                return ["char", v]
            if t == "byte":
                return ["byte", v]
            if t in ("float", "double"):
                return ["float", v] if intlike(self.ty(n.child_by_field_name("value"))) else v
            return v
        if k == "ternary_expression":
            c = self.cond(n.child_by_field_name("condition"))
            a = self.ex(n.child_by_field_name("consequence"), want_int)
            e = self.ex(n.child_by_field_name("alternative"), want_int)
            return ["if", c, a, e]
        if k == "assignment_expression":
            return Raw(";TODO " + self.t(n))
        if k == "array_access":
            arr = n.child_by_field_name("array")
            return ["vector-ref", self.ex(arr), self.ex(n.child_by_field_name("index"), True)]
        if k == "field_access":
            obj, f = n.child_by_field_name("object"), self.t(n.child_by_field_name("field"))
            ot = self.ty(obj) if obj.type != "this" else (self.cls.name if self.cls else None)
            o = self.ex(obj) if obj.type not in ("this", "super") else "self"
            if f == "length":
                return ["vector-length", o]
            if ot in self.classes:
                owner = self.field_owner(f, self.classes[ot]) or self.classes[ot]
                return [self.cname(owner) + "-" + kebab(f), o]
            if obj.type in ("this", "super") and self.cls:
                owner = self.field_owner(f, self.cls) or self.cls
                return [self.cname(owner) + "-" + kebab(f), "self"]
            if f in ("x", "y", "z") and (ot in ("PVector", None)):
                return ["vec-" + f, o]
            return [kebab(f), o]
        if k == "method_invocation":
            return self.call(n)
        if k == "object_creation_expression":
            t = re.sub(r"<.*>", "", self.t(n.child_by_field_name("type"))).strip()
            a = self.args(n)
            if t == "PVector":
                while len(a) < 2:
                    a.append("0")
                return ["PVector"] + a
            if t in ("ArrayList", "LinkedList", "IntList", "FloatList", "StringList", "JSONArray"):
                return ["list"]
            if t in ("JSONObject", "HashMap", "IntDict", "FloatDict", "StringDict"):
                return ["make-hash-table"]
            if t in self.classes:
                return [self.ctor_name(self.classes[t], len(a))] + a
            return [kebab(t)] + a
        if k == "array_creation_expression":
            init = n.child_by_field_name("value")
            if init:
                return self.ex(init)
            dims = [self.ex(named(d)[0], True) for d in n.children if d.type == "dimensions_expr"]
            t = self.t(n.child_by_field_name("type"))
            zero = "#f" if t == "boolean" else ("0" if numeric(t) else ("\"\"" if t == "String" else "#f"))
            if len(dims) == 1:
                return ["make-vector", dims[0], zero]
            self.helpers.add("matrix")
            return ["make-matrix"] + dims + [zero]
        if k == "array_initializer":
            return ["vector"] + [self.ex(c) for c in named(n)]
        if k == "lambda_expression":
            return Raw(";TODO lambda " + self.t(n))
        return Raw(f";TODO {k} " + self.t(n).replace("\n", " "))

    def cond(self, n):
        if n.type == "parenthesized_expression":
            n = named(n)[0]
        return self.ex(n)

    def is_str(self, n):
        return self.ty(n) == "String"

    def as_str(self, n):
        t = self.ty(n)
        v = self.ex(n)
        if t == "String":
            return v
        return ["str", v]

    def concat_parts(self, n):
        if n.type == "parenthesized_expression":
            return self.concat_parts(named(n)[0]) if self.ty(named(n)[0]) == "String" else [n]
        if n.type == "binary_expression" and self.t(n.child_by_field_name("operator")) == "+" and self.ty(n) == "String":
            return self.concat_parts(n.child_by_field_name("left")) + self.concat_parts(n.child_by_field_name("right"))
        return [n]

    def binary(self, n, want_int):
        op = self.t(n.child_by_field_name("operator"))
        L, R = n.child_by_field_name("left"), n.child_by_field_name("right")
        lt, rt = self.ty(L), self.ty(R)
        if op == "+" and "String" in (lt, rt):
            return ["string-append"] + [self.as_str(p) for p in self.concat_parts(n)]
        sub_int = want_int or op == "%"
        l, r = self.ex(L, sub_int), self.ex(R, sub_int)
        if op in ("+", "-", "*", "/", "%", "<", ">", "<=", ">="):
            if lt == "char":
                l = ["char->integer", l]
            if rt == "char":
                r = ["char->integer", r]
            if lt == "char" or rt == "char":
                lt = "int" if lt == "char" else lt
                rt = "int" if rt == "char" else rt
        if op == "/" and intlike(lt) and intlike(rt):
            return ["quotient", l, r] if want_int else ["/", l, r]
        if op == "%":
            return ["remainder" if intlike(lt) and intlike(rt) else "modulo", l, r]
        if op in ("==", "!="):
            if "String" in (lt, rt):
                f = ["equal?", l, r]
            elif numeric(lt) and numeric(rt) and not ("char" in (lt, rt)):
                f = ["=", l, r]
            elif r == "#f" or l == "#f":
                f = ["not", l if r == "#f" else r] if (r == "#f") != (l == "#f") else ["eq?", l, r]
                if op == "!=":
                    return f[1] if f[0] == "not" else ["not", f]
                return f
            else:
                f = ["eqv?", l, r]
            return f if op == "==" else ["not", f]
        if op in ("&&", "||"):
            name = "and" if op == "&&" else "or"
            parts = []
            for x, side in ((L, l), (R, r)):
                if isinstance(side, list) and side and side[0] == name:
                    parts += side[1:]
                else:
                    parts.append(side)
            return [name] + parts
        if op in ("+", "*"):
            parts = []
            for side in (l, r):
                if isinstance(side, list) and side and side[0] == op and len(side) > 2:
                    parts += side[1:]
                else:
                    parts.append(side)
            if op == "+" and l is parts[0] and isinstance(l, list) and l and l[0] == "+":
                pass
            return [op] + parts
        if op == "-" and isinstance(l, list) and l and l[0] == "-" and len(l) > 2:
            return l + [r]
        m = {"&": "bitwise-and", "|": "bitwise-or", "^": "bitwise-xor"}
        if op in m:
            return [m[op], l, r]
        if op == "<<":
            return ["arithmetic-shift", l, r]
        if op in (">>", ">>>"):
            return ["arithmetic-shift", l, ("-" + r) if isinstance(r, str) and r.isdigit() else ["-", r]]
        return [op, l, r]

    def ctor_name(self, ci, nargs):
        base = "make-" + self.cname(ci)
        if len(ci.ctors) > 1:
            arities = sorted({len([p for p in named(c.child_by_field_name("parameters")) if p.type == "formal_parameter"]) for c in ci.ctors})
            if nargs != arities[-1]:
                return f"{base}{nargs}"
        return base

    def fname(self, name, nargs=None):
        """a sketch-level function, with an arity suffix when Java overloads it"""
        f = self.var(name) if name not in EVENTS else kebab(name)
        ov = self.overloads.get(name, [])
        if len(ov) > 1 and nargs is not None:
            arities = sorted({self.arity(m) for m in ov})
            if nargs != arities[-1]:
                return f"{f}{nargs}"
        return f

    def arity(self, m):
        return len([p for p in named(m.child_by_field_name("parameters")) if p.type == "formal_parameter"])

    def mname(self, ci, name, nargs=None):
        f = self.cname(ci) + "-" + kebab(name)
        ov = ci.over.get(name, [])
        if len(ov) > 1 and nargs is not None:
            arities = sorted({self.arity(m) for m in ov})
            if nargs != arities[-1]:
                return f"{f}{nargs}"
        return f

    def call(self, n):
        name = self.t(n.child_by_field_name("name"))
        obj = n.child_by_field_name("object")
        a = self.args(n)
        if obj is None:
            if self.cls and self.method_of(name):
                return [self.mname(self.method_of(name), name, len(a)), "self"] + a
            if name in self.funcs:
                return [self.fname(name, len(a))] + a
            if name.startswith("__"):
                name = name[2:]
                return [name] + a
            if name in ("max", "min") and len(a) == 1:
                return ["apply", name, ["vector->list", a[0]] if (self.ty(named(n.child_by_field_name("arguments"))[0]) or "").endswith("[]") else a[0]]
            if name == "printArray":
                return ["println", a[0]]
            if name in ("split", "splitTokens", "join"):
                a = [Raw('"\\t"') if x == "TAB" else x for x in a]
                return [kebab(name)] + a
            if name == "random" and len(a) == 1:
                return ["random", a[0]]
            return [kebab(name)] + a
        if obj.type == "super":
            base = self.classes.get(self.cls.base) if self.cls else None
            ci = self.method_of(name, base) if base else None
            return [self.mname(ci, name, len(a)) if ci else kebab(name), "self"] + a
        o = self.ex(obj)
        ot = self.ty(obj)
        if obj.type == "identifier" and self.t(obj) == "PVector":
            if name in ("add", "sub", "mult", "div"):
                return [name, ["copy", a[0]], a[1]]
            if name == "fromAngle":
                return ["from-angle"] + a
            if name == "random2D":
                return ["random2-d"]
            return [kebab(name)] + a
        if obj.type == "identifier" and self.t(obj) == "Math":
            return [kebab(name)] + a
        if obj.type == "identifier" and self.t(obj) in ("Integer", "Float"):
            return {"parseInt": ["int"], "parseFloat": ["float"]}.get(name, [kebab(name)]) + a
        if obj.type == "field_access" and self.t(obj) == "System.out":
            return ["println"] + a
        if ot == "String" or (obj.type == "string_literal"):
            if name == "length":
                return ["string-length", o]
            if name == "charAt":
                return ["string-ref", o, a[0]]
            if name == "substring":
                return ["substring", o, a[0], a[1] if len(a) > 1 else ["string-length", o]]
            if name == "equals":
                return ["equal?", o, a[0]]
            if name == "toUpperCase":
                return ["string-upcase", o]
            if name == "toLowerCase":
                return ["string-downcase", o]
            if name == "indexOf":
                self.helpers.add("index-of")
                return ["string-index-of", o, a[0]]
        if name == "size" and not a:
            return ["length", o]
        bt = base_type(ot)
        if bt in LISTS:
            if name == "get":
                return ["list-ref", o, a[0]]
            if name == "size":
                return ["length", o]
            if name == "isEmpty":
                return ["null?", o]
            if name == "set":
                return ["vector-set!", o, a[0], a[1]]
        if ot in self.classes:
            ci = self.method_of(name, self.classes[ot])
            if ci:
                return [self.mname(ci, name, len(a)), o] + a
        if name == "heading2D":
            return ["heading", o]
        if name == "replaceAll" or (name == "replace" and ot == "String"):
            return ["join", ["split", o, a[0]], a[1]]
        if ot == "PVector" or (ot is None and name in ("mag", "normalize", "heading", "magSq", "setMag", "limit")):
            if name == "get" or name == "copy":
                return ["copy", o]
        return [kebab(name), o] + a

    # ── statements: each returns a list of forms ──────────────────────────
    def comment(self, n, trailing=False):
        c = self.t(n)
        if n.type == "line_comment":
            c = c.rstrip()
            return [Comment(";" + c[2:] if c[2:3] == " " or not c[2:] else "; " + c[2:], trailing)]
        body = c[2:-2]
        if body.startswith("*"):
            body = body[1:]
        lines = [re.sub(r"^\s*\* ?", "", l).rstrip() for l in body.split("\n")]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if trailing and len(lines) == 1:
            return [Comment("; " + lines[0].strip(), True)]
        return [Comment((";; " + l.strip()) if l.strip() else ";;") for l in lines] if lines else []

    def block(self, kids, tail=False):
        """statements -> forms. tail: the value of the last one is what the function returns"""
        out = []
        prev = None
        kids = list(kids)
        i = 0
        while i < len(kids):
            k = kids[i]
            last = all(is_comment(x) for x in kids[i + 1:])
            if prev is not None and k.start_point.row > prev.end_point.row + 1:
                out.append(BLANK)
            if is_comment(k):
                out += self.comment(k, prev is not None and k.start_point.row == prev.end_point.row)
            elif tail and k.type == "if_statement" and not last and self.ends_in_return(k.child_by_field_name("consequence")) \
                    and k.child_by_field_name("alternative") is None:
                # if (c) { ...; return a; } rest  ->  (if c (begin ... a) (begin rest))
                cons = self.branch(k.child_by_field_name("consequence"), True)
                rest = self.block(kids[i + 1:], True)
                out.append(self.if_form(self.cond(k.child_by_field_name("condition")), cons, rest))
                return out
            else:
                out += self.stmt(k, tail and last)
            prev = k
            i += 1
        return out

    def ends_in_return(self, n):
        if n.type == "return_statement":
            return True
        if n.type == "block":
            st = [c for c in n.children if c.is_named and not is_comment(c)]
            return bool(st) and self.ends_in_return(st[-1])
        if n.type == "if_statement":
            alt = n.child_by_field_name("alternative")
            return alt is not None and self.ends_in_return(n.child_by_field_name("consequence")) and self.ends_in_return(alt)
        return False

    def stmts_of(self, n):
        if n.type in ("block", "constructor_body"):
            return [c for c in n.children if c.is_named or is_comment(c)]
        return [n]

    def branch(self, n, tail=False):
        self.scope.push()
        f = self.block(self.stmts_of(n), tail)
        self.scope.pop()
        return f

    def if_form(self, c, cons, alt):
        def one(fs):
            real = [f for f in fs if not isinstance(f, Comment) and f is not BLANK]
            if len(real) == 1 and len(fs) == 1:
                return fs[0]
            return ["begin"] + fs
        if not alt:
            return ["when", c] + cons
        has_def = any(isinstance(f, list) and f and f[0] == "define" for f in cons + alt)
        a = alt[0] if len(alt) == 1 and isinstance(alt[0], list) and alt[0] else None
        chained = a is not None and (a[0] in ("cond", "when") or (a[0] == "if" and len(a) == 4))
        if len(cons) == 1 and len(alt) == 1 and not isinstance(cons[0], Comment) \
                and not isinstance(alt[0], Comment) and not has_def and not chained:
            return ["if", c, cons[0], alt[0]]
        clauses = [[c] + cons]
        if a is not None and a[0] == "cond":
            clauses += a[1:]
        elif a is not None and a[0] == "when":
            clauses.append(a[1:])
        elif a is not None and a[0] == "if" and len(a) == 4:
            clauses.append([a[1], a[2]])
            clauses.append(["else", a[3]])
        else:
            clauses.append(["else"] + alt)
        return ["cond"] + clauses

    def setter(self, L, v):
        """the form that stores v where the Java left-hand side L points"""
        if L.type == "parenthesized_expression":
            return self.setter(named(L)[0], v)
        if L.type == "identifier":
            name = self.t(L)
            if not self.scope.local(name) and self.cls and self.field(name):
                return ["set-" + self.cname(self.field_owner(name, self.cls)) + "-" + kebab(name) + "!", "self", v]
            return ["set!", self.var(name), v]
        if L.type == "array_access":
            return ["vector-set!", self.ex(L.child_by_field_name("array")), self.ex(L.child_by_field_name("index"), True), v]
        if L.type == "field_access":
            obj, f = L.child_by_field_name("object"), self.t(L.child_by_field_name("field"))
            ot = self.ty(obj) if obj.type != "this" else (self.cls.name if self.cls else None)
            o = self.ex(obj) if obj.type != "this" else "self"
            if ot in self.classes:
                owner = self.field_owner(f, self.classes[ot]) or self.classes[ot]
                return ["set-" + self.cname(owner) + "-" + kebab(f) + "!", o, v]
            if f in ("x", "y", "z"):
                return ["set-vec-" + f + "!", o, v]
            return [Raw(";TODO set"), self.t(L), v]
        return [Raw(";TODO set " + self.t(L)), v]

    def stmt(self, n, tail=False):
        k = n.type
        if k == "local_variable_declaration":
            out = []
            for d in n.children_by_field_name("declarator"):
                name = self.t(d.child_by_field_name("name"))
                t = self.decl_type(n, d)
                v = d.child_by_field_name("value")
                val = self.ex(v, intlike(t)) if v is not None else self.default(t)
                self.scope.add(name, t)
                out.append(["define", self.var(name), val])
            return out
        if k == "expression_statement":
            return self.expr_stmt(named(n)[0])
        if k == "if_statement":
            c = self.cond(n.child_by_field_name("condition"))
            cons = self.branch(n.child_by_field_name("consequence"), tail)
            alt = n.child_by_field_name("alternative")
            altf = self.branch(alt, tail) if alt is not None else []
            return [self.if_form(c, cons, altf)]
        if k == "for_statement":
            return self.for_stmt(n)
        if k == "enhanced_for_statement":
            name = self.t(n.child_by_field_name("name"))
            val = n.child_by_field_name("value")
            vt = self.ty(val) or ""
            self.scope.push()
            self.scope.add(name, self.t(n.child_by_field_name("type")))
            body = self.block(self.stmts_of(n.child_by_field_name("body")))
            self.scope.pop()
            seq = self.ex(val)
            if vt.endswith("[]"):
                return [["vector-for-each", ["lambda", [self.var(name)]] + body, seq]]
            return [["for-each", ["lambda", [self.var(name)]] + body, seq]]
        if k == "while_statement":
            c = self.cond(n.child_by_field_name("condition"))
            body = self.branch(n.child_by_field_name("body"))
            return [["do", [], [self.negate(c)]] + body]
        if k == "do_statement":
            body = self.branch(n.child_by_field_name("body"))
            c = self.cond(n.child_by_field_name("condition"))
            return [["let", "loop", []] + body + [["when", c, ["loop"]]]]
        if k == "return_statement":
            v = named(n)
            if not tail:
                self.need_return = True
                return [["return"] + ([self.ex(v[0])] if v else [])]
            return [self.ex(v[0])] if v else []
        if k == "break_statement":
            return [Raw(";TODO break")]
        if k == "continue_statement":
            return [Raw(";TODO continue")]
        if k == "block":
            return self.branch(n, tail)
        if k == "class_declaration":
            return self.class_decl(n)
        if k == "method_declaration":
            return self.func(n)
        if k == "field_declaration":
            return self.field_decl(n)
        if k == "switch_expression" or k == "switch_statement":
            return self.switch(n, tail)
        if k == "try_statement":
            body = n.child_by_field_name("body")
            return self.branch(body, tail)
        return [Raw(f";TODO {k} " + self.t(n).replace("\n", " "))]

    def switch(self, n, tail):
        cond = n.child_by_field_name("condition")
        v = self.cond(cond)
        body = n.child_by_field_name("body")
        clauses = []
        labels = []
        for grp in [c for c in body.children if c.type == "switch_block_statement_group"]:
            stmts = []
            for c in grp.children:
                if c.type == "switch_label":
                    vals = named(c)
                    if not vals:
                        labels.append("else")
                    else:
                        labels += [self.ex(x) for x in vals]
                elif c.is_named and c.type != "break_statement":
                    stmts.append(c)
            if not [s for s in stmts if not is_comment(s)]:
                continue
            self.scope.push()
            fs = self.block(stmts, tail)
            self.scope.pop()
            if "else" in labels:
                clauses.append(["else"] + fs)
            else:
                clauses.append([labels] + fs)
            labels = []
        return [["case", v] + clauses]

    def negate(self, c):
        flip = {"<": ">=", ">": "<=", "<=": ">", ">=": "<"}
        if isinstance(c, list) and len(c) == 3 and c[0] in flip:
            return [flip[c[0]], c[1], c[2]]
        if isinstance(c, list) and c and c[0] == "not":
            return c[1]
        return ["not", c]

    def expr_stmt(self, e):
        if e.type == "update_expression":
            txt = self.t(e)
            op = "+" if "++" in txt else "-"
            target = [c for c in e.children if c.is_named][0]
            return [self.setter(target, [op, self.ex(target), "1"])]
        if e.type == "assignment_expression":
            L, R = e.child_by_field_name("left"), e.child_by_field_name("right")
            op = self.t(e.child_by_field_name("operator"))
            lt = self.ty(L)
            if op == "=" and R.type == "assignment_expression":
                inner = R.child_by_field_name("left")
                first = self.expr_stmt(R)
                return first + [self.setter(L, self.ex(inner))]
            if op == "=":
                return [self.setter(L, self.ex(R, intlike(lt)))]
            o = op[:-1]
            rt = self.ty(R)
            l = self.ex(L)
            r = self.ex(R, intlike(lt))
            if o == "+" and lt == "String":
                return [self.setter(L, ["string-append", l, self.as_str(R)])]
            if o == "/" and intlike(lt):
                v = ["quotient", l, r] if intlike(rt) else ["int", ["/", l, r]]
            elif o == "%":
                v = ["remainder" if intlike(lt) and intlike(rt) else "modulo", l, r]
            else:
                v = {"&": ["bitwise-and", l, r], "|": ["bitwise-or", l, r], "^": ["bitwise-xor", l, r],
                     "<<": ["arithmetic-shift", l, r], ">>": ["arithmetic-shift", l, ["-", r]]}.get(o, [o, l, r])
                if intlike(lt) and o in ("*", "+", "-") and not intlike(rt) and rt is not None:
                    v = ["int", v]
            return [self.setter(L, v)]
        if e.type == "method_invocation" and not self.t(e.child_by_field_name("name")) == "":
            name = self.t(e.child_by_field_name("name"))
            obj = e.child_by_field_name("object")
            if obj is not None:
                bt = base_type(self.ty(obj))
                if bt in LISTS:
                    a = self.args(e)
                    o = self.ex(obj)
                    if name in ("add", "append") and len(a) == 1:
                        return [self.setter(obj, ["append", o, ["list", a[0]]])]
                    if name == "add" and len(a) == 2:
                        return [self.setter(obj, ["concat", ["subset", o, "0", a[0]], ["cons", a[1], ["subset", o, a[0]]]])]
                    if name == "remove":
                        self.helpers.add("remove-at")
                        return [self.setter(obj, ["remove-at", o, a[0]])]
                    if name == "clear":
                        return [self.setter(obj, ["list"])]
        return [self.ex(e)]

    def for_stmt(self, n):
        init = n.child_by_field_name("init")
        cond = n.child_by_field_name("condition")
        upds = n.children_by_field_name("update")
        body = n.child_by_field_name("body")
        self.scope.push()
        binds = []
        pre = []
        if init is not None:
            if init.type == "local_variable_declaration":
                for d in init.children_by_field_name("declarator"):
                    name = self.t(d.child_by_field_name("name"))
                    t = self.decl_type(init, d)
                    v = d.child_by_field_name("value")
                    val = self.ex(v, intlike(t)) if v is not None else self.default(t)
                    self.scope.add(name, t)
                    binds.append([self.var(name), val])
            else:
                pre = self.expr_stmt(init)
        steps = {}
        extra = []
        for u in upds:
            f = self.expr_stmt(u)
            if len(f) == 1 and isinstance(f[0], list) and f[0][0] == "set!" and any(b[0] == f[0][1] for b in binds):
                steps[f[0][1]] = f[0][2]
            else:
                extra += f
        stop = [self.negate(self.cond(cond))] if cond is not None else ["#f"]
        inner = self.block(self.stmts_of(body))
        self.scope.pop()
        dbinds = [b + ([steps[b[0]]] if b[0] in steps else []) for b in binds]
        return pre + [["do", dbinds, stop] + inner + extra]

    def params(self, n):
        ps = []
        for p in named(n.child_by_field_name("parameters")):
            if p.type == "formal_parameter":
                name = self.t(p.child_by_field_name("name"))
                self.scope.add(name, self.decl_type(p, p))
                ps.append(self.var(name))
        return ps

    def func(self, n):
        name = self.t(n.child_by_field_name("name"))
        if name == "settings":
            name = "settings"
        self.scope.push()
        ps = self.params(n)
        saved = self.need_return
        self.need_return = False
        rt = self.decl_type(n)
        body = self.block(self.stmts_of(n.child_by_field_name("body")), tail=rt != "void")
        if self.cls:
            head = [self.mname(self.cls, name, len(ps)), "self"] + ps
        else:
            head = [self.fname(name, len(ps))] + ps
        if self.need_return:
            body = [Raw(";TODO early return")] + body
        self.need_return = saved
        self.scope.pop()
        return [["define", head] + (body or ["(void)"])]

    def default(self, t):
        if t == "boolean":
            return "#f"
        if numeric(t):
            return "0" if intlike(t) or t == "color" else "0.0"
        if t == "String":
            return "\"\""
        return "#f"

    def field_decl(self, n):
        out = []
        for d in n.children_by_field_name("declarator"):
            name = self.t(d.child_by_field_name("name"))
            t = self.decl_type(n, d)
            v = d.child_by_field_name("value")
            out.append(["define", self.var(name), self.ex(v, intlike(t)) if v is not None else self.default(t)])
        return out

    # ── classes ───────────────────────────────────────────────────────────
    def class_decl(self, n):
        ci = self.classes[self.t(n.child_by_field_name("name"))]
        prev = self.cls
        self.cls = ci
        c = self.cname(ci)
        fields = self.all_fields(ci)
        rec = ["define-record-type", c, ["make-" + c + "-record"] + [kebab(self.t(d.child_by_field_name("name"))) for _, _, d in fields],
               c + "?"]
        for owner, _, d in fields:
            f = kebab(self.t(d.child_by_field_name("name")))
            rec.append([f, c + "-" + f, "set-" + c + "-" + f + "!"])
        out = [rec]
        body = n.child_by_field_name("body")
        members = [m for m in body.children if m.is_named or is_comment(m)]
        own_fields = [m for m in members if m.type == "field_declaration"]
        pending = []
        ctors_done = False
        for m in members:
            if m.type == "field_declaration":
                continue
            if is_comment(m):
                pending += self.comment(m)
                continue
            out.append(BLANK)
            out += pending
            pending = []
            if m.type == "constructor_declaration":
                out += self.ctor(m, fields)
                ctors_done = True
            elif m.type == "method_declaration":
                out += self.func(m)
            elif m.type == "class_declaration":
                self.cls = prev
                out += self.class_decl(m)
                self.cls = ci
        if not ci.ctors:
            out.append(BLANK)
            out += self.ctor(None, fields)
        out += pending
        self.cls = prev
        return out

    def ctor(self, m, fields):
        ci = self.cls
        c = self.cname(ci)
        self.scope.push()
        ps = self.params(m) if m is not None else []
        stmts = self.stmts_of(m.child_by_field_name("body")) if m is not None else []
        real = [s for s in stmts if not is_comment(s)]
        sup = None
        if real and real[0].type == "explicit_constructor_invocation":
            sup = real[0]
            stmts = [s for s in stmts if s != sup]
        zeros = [self.default(self.decl_type(f, d)) for _, f, d in fields]
        body = []
        if sup is not None:
            base = self.classes[ci.base]
            a = [self.ex(x) for x in named(sup.child_by_field_name("arguments"))]
            body.append(["define", "base", [self.ctor_name(base, len(a))] + a])
            for owner, f, d in fields:
                if owner is not ci:
                    fn = kebab(self.t(d.child_by_field_name("name")))
                    o = self.cname(owner)
                    body.append(["set-" + c + "-" + fn + "!", "self", [o + "-" + fn, "base"]])
        for owner, f, d in fields:
            if owner is not ci and sup is not None:
                continue
            v = d.child_by_field_name("value")
            if v is not None:
                fn = self.t(d.child_by_field_name("name"))
                body.append(["set-" + self.cname(owner) + "-" + kebab(fn) + "!", "self", self.ex(v, intlike(self.decl_type(f, d)))])
        saved = self.need_return
        self.need_return = False
        body += self.block(stmts)
        if self.need_return:
            body = [Raw(";TODO early return")] + body
        self.need_return = saved
        self.scope.pop()
        if sup is not None:
            # base's own fields were filled in by base's constructor
            pass
        name = self.ctor_name(ci, len(ps))
        return [["define", [name] + ps,
                 ["let", [["self", ["make-" + c + "-record"] + zeros]]] + body + ["self"]]]

    # ── program ───────────────────────────────────────────────────────────
    def run(self):
        kids = self.body_nodes()
        self.collect(kids)
        forms = [["import", ["processing"]]]
        if self.static:
            header = []
            while kids and is_comment(kids[0]):
                header += self.comment(kids.pop(0))
            body = self.block(kids)
            forms = header + [BLANK] + forms + [BLANK, ["define", ["setup"]] + body]
        else:
            header = []
            while kids and is_comment(kids[0]):
                header += self.comment(kids.pop(0))
            # the sketch's globals run top to bottom, so a class has to be
            # defined before a global made from it: classes go first
            cls, rest, i = [], [], 0
            while i < len(kids):
                j = i
                while j < len(kids) and is_comment(kids[j]):
                    j += 1
                if j < len(kids) and kids[j].type == "class_declaration":
                    cls += kids[i:j + 1]
                    i = j + 1
                else:
                    rest.append(kids[i])
                    i += 1
            body = (self.block(cls) + [BLANK] if cls else []) + self.block(rest)
            forms = header + [BLANK] + forms + [BLANK] + body
        out = self.render(forms)
        if self.helpers:
            out = self.add_helpers(out)
        out = re.sub(r"\n{3,}", "\n\n", out).strip("\n") + "\n"
        return out

    def render(self, forms):
        lines = []
        for f in forms:
            if f is BLANK:
                lines.append("")
            elif isinstance(f, Comment):
                if f.trailing and lines:
                    lines[-1] += "  " + f.text
                else:
                    lines.append(f.text)
            else:
                if isinstance(f, list) and f and f[0] == "define" and isinstance(f[1], list) and lines and lines[-1] != "" and not lines[-1].startswith(";"):
                    lines.append("")
                lines.append(pp(f, 0))
        return "\n".join(lines)

    def add_helpers(self, out):
        h = []
        if "matrix" in self.helpers:
            h.append("""; a vector of rows, each a vector of cols values (Java's new int[rows][cols])
(define (make-matrix rows cols v)
  (let ((m (make-vector rows #f)))
    (do ((i 0 (+ i 1))) ((= i rows) m)
      (vector-set! m i (make-vector cols v)))))""")
        if "remove-at" in self.helpers:
            h.append("""; the list without its i-th item
(define (remove-at xs i)
  (concat (subset xs 0 i) (subset xs (+ i 1))))""")
        if "index-of" in self.helpers:
            h.append("""; where t first appears in s, or -1
(define (string-index-of s t)
  (let loop ((i 0))
    (cond ((> (+ i (string-length t)) (string-length s)) -1)
          ((equal? (substring s i (+ i (string-length t))) t) i)
          (else (loop (+ i 1))))))""")
        i = out.index("(import (processing))") + len("(import (processing))")
        return out[:i] + "\n\n" + "\n\n".join(h) + out[i:]


if __name__ == "__main__":
    print(Sch(open(sys.argv[1]).read()).run(), end="")
