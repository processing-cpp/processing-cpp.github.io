"""Processing (Java) example -> RustMode sketch. First draft; type-checked
with rustc against the engine, then fixed by hand where needed."""
import json, os, re, sys
from common import *

HERE = os.path.dirname(os.path.abspath(__file__))
SIG = json.load(open(os.path.join(HERE, "rsig.json")))
OVER = {k: {int(a): b for a, b in v.items()} for k, v in json.load(open(os.path.join(HERE, "rover.json"))).items()}

RTY = {"float": "f32", "double": "f32", "int": "i32", "long": "i64", "boolean": "bool",
       "char": "char", "byte": "i8", "short": "i32", "String": "String", "color": "Color",
       "PVector": "PVector", "PImage": "u64", "PGraphics": "u64", "PFont": "u64",
       "PShape": "u64", "Table": "Table", "TableRow": "TableRow", "JSONObject": "Json",
       "JSONArray": "Json", "XML": "Xml", "IntList": "IntList", "FloatList": "FloatList",
       "StringList": "StringList", "IntDict": "IntDict", "FloatDict": "FloatDict",
       "StringDict": "StringDict", "PShader": "PShader", "PMatrix3D": "PMatrix3D"}
GLOBAL_TY = {"width": "f32", "height": "f32", "mouseX": "f32", "mouseY": "f32", "pmouseX": "f32",
             "pmouseY": "f32", "frameCount": "u64", "key": "char", "keyCode": "u32",
             "mousePressed": "bool", "keyPressed": "bool", "displayWidth": "f32",
             "displayHeight": "f32", "mouseButton": "u32", "focused": "bool"}
INTS = ("i32", "i64", "u32", "u64", "usize", "u8", "i8")
MATH_METHOD = {"sin", "cos", "tan", "asin", "acos", "atan", "exp", "ln"}
CONSTS = {"PI", "TWO_PI", "HALF_PI", "QUARTER_PI", "TAU"}
RUST_KW = {"type", "move", "match", "loop", "ref", "mod", "fn", "impl", "use", "self", "Self",
           "struct", "trait", "where", "crate", "box", "dyn", "in", "as", "mut", "pub", "super",
           "unsafe", "extern", "yield", "async", "await", "macro", "priv", "final", "override",
           "typeof", "become", "abstract", "do", "virtual", "unsized", "try", "gen"}


def snake(n):
    n = {"heading2D": "heading", "random2D": "random_2d", "random3D": "random_3d"}.get(n, n)
    n = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", n)
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", n).lower()


def safe(n):
    return n + "_" if n in RUST_KW else n


def isint(t):
    return t in INTS


def isnum(t):
    return t in INTS or t == "f32"


class Rs:
    def __init__(self, src):
        self.tree, self.b, self.static = parse(src)
        self.scope = Scope()
        self.classes = {}
        self.funcs = {}
        self.cls = None
        self.fn_ret = None
        self.out = []
        self.notes = []
        self.mutated = set()      # sketch names assigned somewhere
        self.sketch = {}          # sketch var -> rust type
        self.needs = {}           # helper fn / class -> sketch vars it uses
        self.in_helper = False
        self.extra = {}           # helper name -> [(var, mut)]
        self.loop_usize = []
        self.cur_fn = None
        self.slice_params = set()
        self.made_shapes = b"createShape" in self.b
        self.java_types = {}
        st = [self.tree.root_node]
        while st:
            x = st.pop()
            if x.type in ("field_declaration", "local_variable_declaration"):
                jt = re.sub(r"\s+", "", self.t(x.child_by_field_name("type")))
                for d in x.children_by_field_name("declarator"):
                    self.java_types[self.t(d.child_by_field_name("name"))] = jt
            st.extend(x.children)

    def t(self, n):
        return text(self.b, n)

    # ── types ─────────────────────────────────────────────────────────────
    def rt(self, jt):
        """Java type text -> Rust type"""
        jt = re.sub(r"\s+", "", jt or "")
        if jt.endswith("[]"):
            return f"Vec<{self.rt(jt[:-2])}>"
        m = re.match(r"(ArrayList|List|LinkedList)<(.+)>$", jt)
        if m:
            return f"Vec<{self.rt(m.group(2))}>"
        if jt in ("ArrayList", "List", "LinkedList"):
            ts = set(re.findall(r"ArrayList<\s*(\w+)\s*>", self.b.decode()))
            return f"Vec<{self.rt(ts.pop())}>" if len(ts) == 1 else "Vec<_>"
        m = re.match(r"HashMap<(.+),(.+)>$", jt)
        if m:
            return f"std::collections::HashMap<{self.rt(m.group(1))}, {self.rt(m.group(2))}>"
        if jt == "PShape" and getattr(self, "made_shapes", False):
            return "PShape"
        if jt == "Integer":
            return "i32"
        if jt == "Float":
            return "f32"
        return RTY.get(jt, jt)

    def zero(self, t):
        if t == "f32":
            return "0.0"
        if isint(t):
            return "0"
        if t == "bool":
            return "false"
        if t == "char":
            return "' '"
        if t == "String":
            return "String::new()"
        if t.startswith("Vec<"):
            return "Vec::new()"
        if t == "Color":
            return "color(0)"
        if t == "PVector":
            return "PVector::new(0.0, 0.0)"
        if t in self.classes:
            return f"{t}::default()"
        if t.startswith("std::collections::HashMap"):
            return "std::collections::HashMap::new()"
        return "Default::default()"

    def decl_type(self, n, d=None):
        t = type_text(self.b, n) or ""
        if d is not None:
            dims = d.child_by_field_name("dimensions")
            if dims:
                t += self.t(dims).replace(" ", "")
        return self.rt(t)

    def field(self, name, ci=None):
        ci = ci or self.cls
        while ci:
            if name in ci.fields:
                return ci.fields[name]
            ci = self.classes.get(ci.base)
        return None

    def path_to(self, name, ci, kind="field"):
        """'spin.' when a field (or method) comes from the base class, '' when it's the class's own"""
        p = ""
        while ci:
            if (name in ci.fields) if kind == "field" else (name in ci.methods):
                return p
            if not ci.base:
                return p
            p += snake(ci.base) + "."
            ci = self.classes.get(ci.base)
        return p

    def method_of(self, name, ci=None):
        ci = ci or self.cls
        while ci:
            if name in ci.methods:
                return ci
            ci = self.classes.get(ci.base)
        return None

    def var_ty(self, name):
        if self.scope.local(name):
            return self.scope.get(name)
        if self.cls and self.field(name):
            return self.field(name)
        if name in self.sketch:
            return self.sketch[name]
        if name in GLOBAL_TY:
            return GLOBAL_TY[name]
        if name in CONSTS:
            return "f32"
        if name == "pixels" or name.endswith("_pixels"):
            return "Vec<u32>"
        if name.isupper():
            return "u32"
        return None

    def ty(self, n):
        k = n.type
        if k in ("decimal_integer_literal",):
            return "lit"
        if k == "hex_integer_literal":
            return "u32"
        if k == "decimal_floating_point_literal":
            return "f32"
        if k == "string_literal":
            return "str"
        if k == "character_literal":
            return "char"
        if k in ("true", "false"):
            return "bool"
        if k == "parenthesized_expression":
            return self.ty(named(n)[0])
        if k == "identifier":
            return self.var_ty(self.t(n))
        if k == "binary_expression":
            op = self.t(n.child_by_field_name("operator"))
            a, c = self.ty(n.child_by_field_name("left")), self.ty(n.child_by_field_name("right"))
            if op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                return "bool"
            if op == "+" and ("String" in (a, c) or "str" in (a, c)):
                return "String"
            return self.unify(a, c)
        if k == "unary_expression":
            op = self.t(n.child_by_field_name("operator"))
            return "bool" if op == "!" else self.ty(n.child_by_field_name("operand"))
        if k == "cast_expression":
            return self.rt(self.t(n.child_by_field_name("type")))
        if k == "array_access":
            at = self.ty(n.child_by_field_name("array"))
            if at and at.startswith("Vec<"):
                return at[4:-1]
            if self.t(n.child_by_field_name("array")) == "pixels":
                return "u32"
            return None
        if k == "field_access":
            obj, f = n.child_by_field_name("object"), self.t(n.child_by_field_name("field"))
            if f == "length":
                return "usize"
            if obj.type == "this":
                return self.field(f)
            ot = self.ty(obj)
            if ot in self.classes:
                return self.field(f, self.classes[ot])
            if ot == "PVector":
                return "f32"
            if ot == "u64" and f in ("width", "height"):
                return "f32"
            if f == "pixels":
                return "Vec<u32>"
            if f in ("width", "height"):
                return "f32"
            return None
        if k == "method_invocation":
            return self.call_ty(n)
        if k == "object_creation_expression":
            return self.rt(re.sub(r"<>", "", self.t(n.child_by_field_name("type"))))
        if k == "array_creation_expression":
            dims = len([c for c in n.children if c.type == "dimensions_expr"])
            d2 = n.child_by_field_name("dimensions")
            dims += self.t(d2).count("[") if d2 else 0
            t = self.rt(self.t(n.child_by_field_name("type")))
            for _ in range(max(dims, 1)):
                t = f"Vec<{t}>"
            return t
        if k == "ternary_expression":
            return self.ty(n.child_by_field_name("consequence"))
        return None

    def unify(self, a, c):
        if "char" in (a, c) and (a in ("lit", "char", "i32") and c in ("lit", "char", "i32")) and a != c:
            return "i32"
        if a == c:
            return a
        if "f32" in (a, c):
            return "f32"
        if a == "lit":
            return c
        if c == "lit":
            return a
        if isint(a) and isint(c):
            return "i32"
        return a or c

    def call_ty(self, n):
        name = self.t(n.child_by_field_name("name"))
        obj = n.child_by_field_name("object")
        if obj is None:
            if self.cls and self.method_of(name):
                return self.method_of(name).methods[name]
            if name in self.funcs:
                return self.funcs[name]
            if name in ("__int",):
                return "i32"
            if name in ("__float",):
                return "f32"
            if name in ("__str", "str", "nf", "nfc", "nfs", "nfp", "hex", "binary", "trim", "join"):
                return "String"
            if name == "__char":
                return "char"
            if name in ("round", "floor", "ceil"):
                return "i32"
            if name in ("abs", "min", "max", "constrain"):
                ts = [self.ty(a) for a in self.argnodes(n)]
                if all(x in ("lit", "i32") for x in ts):
                    return "i32"
                return "f32"
            if name in MATH_METHOD or name in ("atan2", "sqrt", "pow", "sq", "random", "noise",
                                               "map", "lerp", "dist", "mag", "norm", "radians",
                                               "degrees", "log", "randomGaussian", "exp"):
                return "f32"
            if name in ("millis",):
                return "u64"
            if name in ("second", "minute", "hour", "day", "month", "year"):
                return "i32"
            if name in ("loadImage", "createImage", "createGraphics", "createFont", "loadFont", "requestImage"):
                return "u64"
            if name in ("color", "lerpColor", "get"):
                return "Color"
            if name in ("red", "green", "blue", "alpha", "hue", "saturation", "brightness", "textWidth"):
                return "f32"
            if name in ("loadStrings", "split", "splitTokens"):
                return "Vec<String>"
            sn = self.engine_name(name, len(self.argnodes(n)))
            if sn in SIG:
                r = SIG[sn][1]
                return r or None
            return None
        ot = self.ty(obj)
        if ot in ("String", "str"):
            return {"length": "usize", "charAt": "char", "indexOf": "i32", "equals": "bool"}.get(name, "String")
        if ot in ("IntList", "FloatList", "StringList"):
            if name == "size":
                return "usize"
            if name in ("get", "remove"):
                return {"IntList": "i32", "FloatList": "f32", "StringList": "String"}[ot]
        if ot and ot.startswith("Vec<"):
            if name == "get":
                return ot[4:-1]
            if name == "size":
                return "usize"
            if name == "remove":
                return ot[4:-1]
        if ot in self.classes:
            ci = self.method_of(name, self.classes[ot])
            return ci.methods[name] if ci else None
        if ot == "PVector":
            if name in ("mag", "dist", "heading", "dot", "magSq"):
                return "f32"
            return "PVector"
        if self.t(obj) == "PVector":
            if name in ("dist", "dot", "angleBetween"):
                return "f32"
            return "PVector"
        if ot == "u64" and name in ("get",):
            return "Color"
        if ot == "u64" and name in ("getChildCount", "getVertexCount"):
            return "usize"
        if ot == "u64" and name == "getChild":
            return "u64"
        if ot == "u64" and name == "getVertex":
            return "PVector"
        if self.t(obj) == "PFont" and name == "list":
            return "Vec<String>"
        return None

    def argnodes(self, n):
        return [a for a in named(n.child_by_field_name("arguments")) if not is_comment(a)]

    # ── casting ───────────────────────────────────────────────────────────
    def cast(self, code, have, want, node=None):
        """code of type `have` used where `want` is needed"""
        if want is None or have == want:
            return code
        if have == "lit":
            if want == "f32":
                return code + ".0" if re.fullmatch(r"-?\d+", code) else code
            return code
        if have == "char" and isint(want):
            return f"({code} as {want})"
        if have == "char" and want == "f32":
            return f"({code} as u32 as f32)"
        if want == "f32" and isint(have):
            return f"{self.paren(code)} as f32"
        if isint(want) and (isint(have) or have == "f32"):
            return f"{self.paren(code)} as {want}"
        if want == "String" and have == "str":
            return f"{code}.to_string()"
        if want == "&str" and have == "String":
            return f"&{code}"
        if want == "Color" and have == "u32":
            return f"Color::from_u32({code})"
        if want == "u32" and have == "Color":
            return f"{self.paren(code)}.to_argb()"
        return code

    def paren(self, c):
        if re.fullmatch(r"[\w.()\[\]]+", c) and c.count("(") == c.count(")"):
            return c
        return f"({c})"

    def arg(self, n, want):
        """an argument for a sketch's own function or method"""
        if want and want.startswith("own "):
            return self.ex(n)
        if want and want.startswith("mut "):
            code = self.ex(n)
            if self.in_helper and self.t(n) in self.mut_params:
                return code
            return f"&mut {code}"
        if want and (want.startswith("Vec<") or want in self.classes or want in LIB_REF):
            code = self.ex(n)
            if want == "String" and n.type == "string_literal":
                return code
            if self.in_helper and (self.t(n) in self.mut_params or self.t(n) in getattr(self, "ro_params", set())):
                return code
            if n.type == "identifier" and self.scope.local(self.t(n)) and self.scope.get(self.t(n)) == want and self.is_param(self.t(n)):
                return code
            return f"&{code}"
        return self.exw(n, want)

    def is_param(self, name):
        return name in getattr(self, "cur_params", set())

    def exw(self, n, want):
        """expression converted to type `want`"""
        if want and want.startswith("Vec<") and n.type == "identifier" and self.t(n) in self.slice_params and self.scope.local(self.t(n)):
            return f"{safe(self.t(n))}.to_vec()"
        if want == "String" and n.type == "identifier" and self.t(n) in self.slice_params and self.scope.local(self.t(n)):
            return f"{safe(self.t(n))}.to_string()"
        if want and want.startswith("Vec<") and n.type == "identifier" and not self.scope.local(self.t(n)) and self.t(n) in self.sketch and self.cur_fn is None:
            return f"{safe(self.t(n))}.clone()"
        if want == "f32" and n.type == "decimal_integer_literal":
            return self.t(n).rstrip("lL") + ".0"
        if want == "f32" and n.type == "unary_expression" and self.t(n.child_by_field_name("operator")) == "-" \
                and n.child_by_field_name("operand").type == "decimal_integer_literal":
            return "-" + self.t(n.child_by_field_name("operand")) + ".0"
        code = self.ex(n, want)
        return self.cast(code, self.ty(n), want, n)

    # ── expressions ───────────────────────────────────────────────────────
    def ex(self, n, want=None):
        k = n.type
        if k == "decimal_integer_literal":
            v = self.t(n).rstrip("lL")
            return v + ".0" if want == "f32" else v
        if k == "hex_integer_literal":
            return self.t(n).rstrip("lL")
        if k == "decimal_floating_point_literal":
            v = self.t(n).rstrip("fFdD")
            if v.startswith("."):
                v = "0" + v
            if v.endswith("."):
                v += "0"
            if "." not in v and "e" not in v.lower():
                v += ".0"
            return v
        if k == "string_literal":
            return self.t(n)
        if k == "character_literal":
            return self.t(n)
        if k in ("true", "false"):
            return k
        if k == "null_literal":
            return "None"
        if k == "this":
            return "self"
        if k == "identifier":
            name = self.t(n)
            if not self.scope.local(name) and self.cls and self.field(name):
                return "self." + self.path_to(name, self.cls) + safe(name)
            if name in GLOBAL_TY and not self.scope.local(name):
                return {"mousePressed": "mouse_pressed_global()", "keyPressed": "key_pressed_global()"}.get(name, snake(name) + "()")
            if name in self.consts and not self.scope.local(name):
                return self.consts[name]
            if self.in_helper and name in self.sketch and not self.scope.local(name) and name in self.mut_params:
                return f"*{name}" if self.sketch[name] in ("f32", "i32", "bool", "char", "u64", "u32", "Color", "PVector") else name
            return safe(name)
        if k == "parenthesized_expression":
            return "(" + self.ex(named(n)[0], want) + ")"
        if k == "binary_expression":
            return self.binary(n, want)
        if k == "unary_expression":
            op = self.t(n.child_by_field_name("operator"))
            o = n.child_by_field_name("operand")
            v = self.ex(o, want)
            return {"!": "!", "-": "-", "+": "", "~": "!"}[op] + v
        if k == "update_expression":
            return "/* TODO update in expression */ " + self.t(n)
        if k == "cast_expression":
            t = self.rt(self.t(n.child_by_field_name("type")))
            v = n.child_by_field_name("value")
            return f"{self.paren(self.ex(v))} as {t}" if isnum(t) else self.ex(v)
        if k == "ternary_expression":
            c = self.ex(n.child_by_field_name("condition"))
            tt = want or self.unify(self.ty(n.child_by_field_name("consequence")), self.ty(n.child_by_field_name("alternative")))
            a = self.exw(n.child_by_field_name("consequence"), tt)
            e = self.exw(n.child_by_field_name("alternative"), tt)
            return f"if {c} {{ {a} }} else {{ {e} }}"
        if k == "array_access":
            return self.index(n)
        if k == "field_access":
            obj, f = n.child_by_field_name("object"), self.t(n.child_by_field_name("field"))
            if f == "length":
                return self.ex(obj) + ".len()"
            ot = self.ty(obj)
            if ot == "u64" and f in ("width", "height") and self.java_types.get(self.t(obj)) == "PShape":
                return f"shape_{f}({self.ex(obj)})"
            if ot == "u64" and f in ("width", "height"):
                return f"{self.ex(obj)}.{f}()"
            if f == "pixels":
                return f"{self.ex(obj)}_pixels"
            oc = self.classes.get(self.cls.name if obj.type == "this" and self.cls else ot)
            if oc is not None:
                return self.ex(obj) + "." + self.path_to(f, oc) + safe(f)
            return self.ex(obj) + "." + safe(f)
        if k == "method_invocation":
            return self.call(n, want)
        if k == "object_creation_expression":
            t = re.sub(r"<.*>", "", self.t(n.child_by_field_name("type"))).strip()
            an = self.argnodes(n)
            if t == "PVector":
                a = [self.exw(x, "f32") for x in an]
                return f"PVector::new{'3' if len(a) == 3 else ''}({', '.join(a)})" if a else "PVector::new(0.0, 0.0)"
            if t in ("ArrayList", "LinkedList"):
                return "Vec::new()"
            if t == "HashMap":
                return "std::collections::HashMap::new()"
            if t == "JSONObject":
                return "Json::object()"
            if t == "JSONArray":
                return "Json::array()"
            if t in self.classes:
                ps = self.classes[t].ctor_types(len(an)) if hasattr(self.classes[t], "ctor_types") else None
                a = [self.arg(x, ps[i] if ps and i < len(ps) else None) for i, x in enumerate(an)]
                a += self.extra_args(t)
                return f"{t}::new({', '.join(a)})"
            a = [self.ex(x) for x in an]
            return f"{self.rt(t)}::new({', '.join(a)})"
        if k == "array_creation_expression":
            init = n.child_by_field_name("value")
            t = self.rt(self.t(n.child_by_field_name("type")))
            if init:
                return self.arr_init(init, t)
            dims = [self.exw(named(d)[0], "usize") for d in n.children if d.type == "dimensions_expr"]
            v = self.zero(t)
            for d in reversed(dims):
                v = f"vec![{v}; {d}]"
            return v
        if k == "array_initializer":
            return self.arr_init(n, want[4:-1] if want and want.startswith("Vec<") else None)
        return f"/* TODO {k} */ " + self.t(n)

    def arr_init(self, n, et):
        items = []
        for c in named(n):
            if c.type == "array_initializer":
                items.append(self.arr_init(c, et[4:-1] if et and et.startswith("Vec<") else None))
            else:
                v = self.exw(c, et) if et else self.ex(c)
                if c.type == "identifier" and et and et.startswith("Vec<") and not v.endswith(".clone()"):
                    v += ".clone()"
                items.append(v)
        return "vec![" + ", ".join(items) + "]"

    def binary(self, n, want):
        op = self.t(n.child_by_field_name("operator"))
        L, R = n.child_by_field_name("left"), n.child_by_field_name("right")
        lt, rt = self.ty(L), self.ty(R)
        if op == "+" and ("String" in (lt, rt) or "str" in (lt, rt)):
            parts = self.concat_parts(n)
            fmt = "".join("{}" if not p[1] else p[0][1:-1].replace("{", "{{").replace("}", "}}") for p in parts)
            args = [p[0] for p in parts if not p[1]]
            return f'format!("{fmt}"' + "".join(", " + a for a in args) + ")"
        if op in ("&&", "||"):
            return f"{self.ex(L)} {op} {self.ex(R)}"
        if op in ("==", "!=", "<", ">", "<=", ">="):
            u = self.unify(lt, rt)
            if u == "lit":
                u = "i32"
            if lt == "usize" and rt in ("lit", "usize"):
                u = "usize"
            if rt == "usize" and lt in ("lit", "usize"):
                u = "usize"
            if R.type == "null_literal" and lt == "u64":
                return f"{self.ex(L)} {op} 0"
            if lt in ("char", "str", "String", "bool", "Color") or rt in ("char", "str", "String", "bool", "Color"):
                return f"{self.ex(L)} {op} {self.ex(R)}"
            a, c = self.exw(L, u), self.exw(R, u)
            if re.search(r" as \w+$", a):
                a = f"({a})"
            return f"{a} {op} {c}"
        u = self.unify(lt, rt)
        if op in ("+", "-", "*", "/", "%") and "char" in (lt, rt):
            u = "i32"
        if "PVector" in (lt, rt) and op in ("*", "/"):
            pv, other = (L, R) if lt == "PVector" else (R, L)
            return f"{self.ex(L) if L is pv else self.exw(L, 'f32')} {op} {self.ex(R) if R is pv else self.exw(R, 'f32')}"
        if want == "f32" and u in ("lit",):
            u = "f32"
        if u == "lit":
            u = want if want in ("f32", "i32", "usize", "u32") else None
        if op in ("&", "|", "^", ">>", "<<", ">>>"):
            if op == ">>>":
                op = ">>"
            return f"{self.exw(L, u)} {op} {self.exw(R, u if op not in ('>>', '<<') else None)}"
        if op == "%" and u == "f32":
            pass
        if u is None or u == "lit":
            return f"{self.ex(L, want)} {op} {self.ex(R, want)}"
        return f"{self.exw(L, u)} {op} {self.exw(R, u)}"

    def concat_parts(self, n):
        if n.type == "binary_expression" and self.t(n.child_by_field_name("operator")) == "+" and \
                ("String" in (self.ty(n.child_by_field_name("left")), self.ty(n.child_by_field_name("right"))) or
                 "str" in (self.ty(n.child_by_field_name("left")), self.ty(n.child_by_field_name("right")))):
            return self.concat_parts(n.child_by_field_name("left")) + self.concat_parts(n.child_by_field_name("right"))
        if n.type == "string_literal":
            return [(self.t(n), True)]
        if n.type == "parenthesized_expression" and self.ty(n) == "String":
            return self.concat_parts(named(n)[0])
        return [(self.ex(n), False)]

    def index(self, n):
        arr = n.child_by_field_name("array")
        idx = n.child_by_field_name("index")
        a = self.ex(arr)
        it = self.ty(idx)
        if idx.type == "update_expression":
            v = self.ex(named(idx)[0])
            self.post.append(f"{v} += 1;" if "++" in self.t(idx) else f"{v} -= 1;")
            return f"{a}[{self.cast(v, self.ty(named(idx)[0]), 'usize')}]"
        if it == "usize":
            return f"{a}[{self.ex(idx)}]"
        return f"{a}[{self.exw(idx, 'usize')}]"

    def engine_name(self, name, argc):
        cands = [snake(name), name]
        for c in cands:
            if c in OVER and argc in OVER[c]:
                return OVER[c][argc]
        for c in cands:
            if c in SIG:
                return c
        return snake(name)

    def call(self, n, want=None):
        name = self.t(n.child_by_field_name("name"))
        obj = n.child_by_field_name("object")
        an = self.argnodes(n)
        for a in named(n.child_by_field_name("arguments")):
            if is_comment(a):
                self.notes.append(self.t(a)[2:].strip() if a.type == "line_comment" else self.t(a)[2:-2].strip())
        if obj is None:
            if self.cls and self.method_of(name):
                ci = self.method_of(name)
                ps = ci.param_types.get(name, [])
                a = [self.arg(x, ps[i] if i < len(ps) else None) for i, x in enumerate(an)]
                a += self.extra_args(f"{ci.name}.{name}")
                if name in getattr(ci, "mut_methods", ()):
                    # the method changes self, so it can't also borrow parts of self
                    a = [f"&{x[1:]}.clone()" if x.startswith("&self.") else x for x in a]
                return f"self.{self.path_to(name, self.cls, 'method')}{safe(snake(name))}({', '.join(a)})"
            if name in self.funcs:
                ps = self.func_params.get(name, [])
                a = [self.arg(x, ps[i] if i < len(ps) else None) for i, x in enumerate(an)]
                a += self.extra_args(name)
                return f"{snake(name)}({', '.join(a)})"
            return self.builtin(name, an, want)
        if obj.type == "super" and self.cls and self.cls.base:
            base = self.classes[self.cls.base]
            ps = base.param_types.get(name, [])
            a = [self.arg(x, ps[i] if i < len(ps) else None) for i, x in enumerate(an)]
            return f"self.{snake(self.cls.base)}.{self.path_to(name, base, 'method')}{safe(snake(name))}({', '.join(a)})"
        o = self.ex(obj)
        ot = self.ty(obj)
        if self.t(obj) == "PVector":
            a = [self.ex(x) for x in an]
            if name in ("add", "sub", "mult", "div") and len(a) == 2:
                op = {"add": "+", "sub": "-", "mult": "*", "div": "/"}[name]
                if name in ("mult", "div"):
                    a[1] = self.exw(an[1], "f32")
                return f"({a[0]} {op} {a[1]})"
            if name in ("dist", "dot"):
                return f"{a[0]}.{name}(&{a[1]})"
            if name == "angleBetween":
                return f"PVector::angle_between(&{a[0]}, &{a[1]})"
            if name == "random2D":
                return "PVector::random_2d()"
            if name == "fromAngle":
                return f"PVector::from_angle({self.exw(an[0], 'f32')})"
            return f"PVector::{snake(name)}({', '.join(a)})"
        if self.t(obj) == "Math":
            return self.builtin(name, an, want)
        if obj.type == "identifier" and self.t(obj)[0].isupper() and ot is None and self.t(obj) not in self.classes:
            return f"{self.t(obj)}::{snake(name)}({', '.join(self.ex(x) for x in an)})"
        if ot in ("String", "str"):
            a = [self.ex(x) for x in an]
            if name == "length":
                return f"{o}.len()"
            if name == "charAt":
                return f"{o}.chars().nth({self.exw(an[0], 'usize')}).unwrap()"
            if name == "substring":
                if len(a) == 1:
                    return f"{o}[{self.exw(an[0], 'usize')}..].to_string()"
                return f"{o}[{self.exw(an[0], 'usize')}..{self.exw(an[1], 'usize')}].to_string()"
            if name == "equals":
                return f"{o} == {a[0]}"
            if name == "toUpperCase":
                return f"{o}.to_uppercase()"
            if name == "toLowerCase":
                return f"{o}.to_lowercase()"
            if name == "indexOf":
                return f"{o}.find({a[0]}).map_or(-1, |i| i as i32)"
            if name in ("replaceAll", "replace"):
                return f"{o}.replace({a[0]}, &{a[1]})"
        if ot and ot.startswith("Vec<"):
            et = ot[4:-1]
            if name == "add":
                if len(an) == 1:
                    return f"{o}.push({self.exw(an[0], et)})"
                return f"{o}.insert({self.exw(an[0], 'usize')}, {self.exw(an[1], et)})"
            if name == "get":
                return f"{o}[{self.exw(an[0], 'usize')}]"
            if name == "size":
                return f"{o}.len()"
            if name == "remove":
                return f"{o}.remove({self.exw(an[0], 'usize')})"
            if name == "set":
                return f"{o}[{self.exw(an[0], 'usize')}] = {self.exw(an[1], et)}"
            if name == "clear":
                return f"{o}.clear()"
            if name == "isEmpty":
                return f"{o}.is_empty()"
        if ot in ("IntList", "FloatList", "StringList"):
            if name in ("get", "remove") and an:
                return f"{o}.{name}({self.exw(an[0], 'usize')})"
            if name == "set" and len(an) == 2:
                return f"{o}.set({self.exw(an[0], 'usize')}, {self.ex(an[1])})"
        if ot in self.classes:
            ci = self.method_of(name, self.classes[ot])
            ps = ci.param_types.get(name, []) if ci else []
            a = [self.arg(x, ps[i] if i < len(ps) else None) for i, x in enumerate(an)]
            if ci:
                a += self.extra_args(f"{ci.name}.{name}")
            return f"{o}.{self.path_to(name, self.classes[ot], 'method')}{safe(snake(name))}({', '.join(a)})"
        if ot == "PVector":
            a = []
            for x in an:
                xt = self.ty(x)
                a.append(("&" + self.ex(x)) if xt == "PVector" else self.exw(x, "f32"))
            if name == "copy" or name == "get":
                return f"{o}.copy()"
            if name in ("add", "sub", "mult", "div", "normalize", "limit", "setMag", "rotate", "lerp", "set"):
                # these change the vector and hand it back; as a value it's a copy
                return "\x00" + f"{o.lstrip(chr(0))}.{snake(name)}({', '.join(a)})"
            return f"{o.lstrip(chr(0))}.{snake(name)}({', '.join(a)})"
        if self.java_types.get(self.t(obj)) == "PGraphics":
            if name == "beginDraw":
                return f"begin_graphics({o})"
            if name == "endDraw":
                return "end_graphics()"
            return self.builtin(name, an, want)
        if ot == "Table" and name == "addRow" and not an:
            return f"{o}.add_row_handle()"
        if ot == "Json" and name == "remove" and an and self.ty(an[0]) in ("lit", "i32", "usize"):
            return f"{o}.remove_at({self.exw(an[0], 'usize')})"
        if ot == "u64" and name == "filter" and len(an) == 1:
            return f"{o}.filter({self.ex(an[0])}, 0.0)"
        if ot == "u64" and name in ("disableStyle", "enableStyle"):
            return f"shape_{snake(name)}({o})"
        if name == "loadPixels" and not an:
            if f"{o}_pixels" in self.sketch or self.scope.get(f"{o}_px_made"):
                return f"{o}_pixels = {o}.load_pixels()"
            return f"let mut {o}_pixels = {o}.load_pixels()"
        if name == "updatePixels" and not an:
            return f"{o}.update_pixels(&{o}_pixels)"
        a = [self.ex(x) for x in an]
        return f"{o}.{snake(name)}({', '.join(a)})"

    def builtin(self, name, an, want):
        if name == "subset" and len(an) == 3:
            st, ct = self.exw(an[1], "usize"), self.exw(an[2], "usize")
            return f"{self.ex(an[0])}[{st}..{st} + {ct}].to_vec()" if st != "0" else f"{self.ex(an[0])}[..{ct}].to_vec()"
        if name == "loadPixels" and not an:
            return "pixels = load_pixels()" if "pixels" in self.sketch else "let mut pixels = load_pixels()"
        if name == "updatePixels" and not an:
            return "update_pixels(&pixels)"
        if name == "println" or name == "print":
            mac = "println" if name == "println" else "print"
            if not an:
                return f"{mac}!()"
            x = an[0]
            if self.ty(x) == "String" and x.type == "binary_expression":
                f = self.ex(x)
                return f"{mac}!" + f[len("format!"):]
            if x.type == "string_literal":
                return f'{mac}!({self.t(x)})'
            return f'{mac}!("{{}}", {self.ex(x)})'
        if name in ("__int", "__float") and self.ty(an[0]) in ("String", "str"):
            t = "i32" if name == "__int" else "f32"
            return f"{self.ex(an[0])}.trim().parse::<{t}>().unwrap_or(0{'.0' if t == 'f32' else ''})"
        if an and name in ("__int", "__float", "__byte") and self.ty(an[0]) == "char":
            t = {"__int": "i32", "__float": "f32", "__byte": "i8"}[name]
            return f"{self.paren(self.ex(an[0]))} as u32 as {t}"
        if name == "__byte":
            return f"{self.paren(self.ex(an[0]))} as i8"
        if name == "__int":
            return f"{self.paren(self.ex(an[0]))} as i32"
        if name == "__float":
            return f"{self.paren(self.ex(an[0]))} as f32"
        if name in ("__str", "str"):
            return f"{self.ex(an[0])}.to_string()"
        if name == "__char":
            return f"char::from({self.paren(self.ex(an[0]))} as u8)"
        if name in MATH_METHOD:
            return f"{self.paren(self.exw(an[0], 'f32'))}.{name}()"
        if name == "atan2":
            return f"{self.paren(self.exw(an[0], 'f32'))}.atan2({self.exw(an[1], 'f32')})"
        if name == "log":
            return f"{self.paren(self.exw(an[0], 'f32'))}.ln()"
        if name in ("round", "floor", "ceil"):
            return f"{self.paren(self.exw(an[0], 'f32'))}.{name}() as i32"
        if name in ("abs", "min", "max") and all(self.ty(x) in ("lit", "i32") for x in an):
            a = [self.ex(x) for x in an]
            if name == "abs":
                return f"{self.paren(a[0])}.abs()"
            return f"{self.paren(a[0])}.{name}({a[1]})"
        if name == "sq":
            v = self.paren(self.exw(an[0], "f32"))
            return f"{v} * {v}" if re.fullmatch(r"[\w.]+", v) else f"{v}.powi(2)"
        if name in ("max", "min") and len(an) == 1 and self.ty(an[0]) in ("Vec<i32>",):
            return f"*{self.ex(an[0])}.iter().{name}().unwrap()"
        if name in ("max", "min") and len(an) == 1:
            return f"{self.ex(an[0])}.iter().cloned().fold({'f32::MIN' if name == 'max' else 'f32::MAX'}, f32::{name})"
        sn = self.engine_name(name, len(an))
        ps, _ = SIG.get(sn, ([], ""))
        a = []
        for i, x in enumerate(an):
            p = ps[i] if i < len(ps) else None
            want = {"f32": "f32", "u32": "u32", "i32": "i32", "usize": "usize", "&str": "&str", "Color": "Color",
                    "u64": "u64", "impl Num": None}.get(p, None)
            if p == "&str":
                xt = self.ty(x)
                c = self.ex(x)
                if x.type == "character_literal":
                    a.append('"' + self.t(x)[1:-1].replace('"', '\\"') + '"')
                elif xt == "String":
                    a.append(f"&{c}")
                elif xt in ("str",):
                    a.append(c)
                elif xt is None and c.startswith("format!"):
                    a.append(f"&{c}")
                else:
                    a.append(f"&{self.paren(c)}.to_string()")
            elif p and p.startswith("&[") and self.ty(x) and self.ty(x).startswith("Vec"):
                a.append("&" + self.ex(x))
            elif p and p.startswith("&") and not p.startswith("&str") and x.type == "identifier":
                a.append("&" + self.ex(x))
            elif want:
                a.append(self.exw(x, want))
            else:
                a.append(self.ex(x))
        shown = snake(name) if (snake(name) in SIG or snake(name) in OVER) else name
        if shown == "loop":
            shown = "r#loop"
        return f"{shown}({', '.join(a)})"

    def extra_args(self, key):
        out = []
        for var, mut in self.extra.get(key, []):
            ref = self.ex_var(var)
            if mut:
                out.append(ref if ref.startswith("&mut") or (self.in_helper and var in self.mut_params) else f"&mut {ref}")
            else:
                t = self.sketch.get(var, "")
                copy = t in ("f32", "i32", "bool", "char", "u64", "u32", "Color", "PVector", "usize")
                if copy or (self.in_helper and (var in getattr(self, "ro_params", set()) or var in self.mut_params)):
                    out.append(ref)
                else:
                    out.append(f"&{ref}")
        return out

    def ex_var(self, var):
        if self.in_helper and var in self.mut_params:
            return var
        if self.in_helper and var in getattr(self, "ro_params", set()):
            return var
        return var

    # ── statements ────────────────────────────────────────────────────────
    def emit(self, line, ind):
        line = re.sub("\x00+", "*", line).replace(".to_string().to_string()", ".to_string()")
        if self.notes and line:
            line += "  // " + ", ".join(self.notes)
            self.notes = []
        self.out.append("    " * ind + line if line else "")
        if self.post and line:
            p, self.post = self.post, []
            for x in p:
                self.out.append("    " * ind + x)

    def comment(self, n):
        return self.t(n)

    def block(self, kids, ind):
        prev = None
        for k in kids:
            if prev is not None and k.start_point.row > prev.end_point.row + 1:
                self.emit("", ind)
            if is_comment(k) and prev is not None and k.start_point.row == prev.end_point.row and self.out:
                self.out[-1] += "  " + self.comment(k).split("\n")[0]
            elif is_comment(k):
                c = self.comment(k)
                lines = c.split("\n")
                base = len(lines[-1]) - len(lines[-1].lstrip()) if len(lines) > 1 else 0
                for i, l in enumerate(lines):
                    if i == 0:
                        self.out.append("    " * ind + l.strip())
                    else:
                        s = l[min(base, len(l) - len(l.lstrip())):] if l.strip() else ""
                        self.out.append(("    " * ind + " " + s.lstrip(" ") if s.lstrip().startswith("*") else "    " * ind + s) if s else "")
            else:
                self.stmt(k, ind)
            prev = k

    def stmts_of(self, n):
        if n.type in ("block", "constructor_body"):
            return [c for c in n.children if c.is_named or is_comment(c)]
        return [n]

    def assigned_in(self, node, name):
        st = [node]
        while st:
            x = st.pop()
            if x.type in ("assignment_expression", "update_expression"):
                tgt = x.child_by_field_name("left") if x.type == "assignment_expression" else named(x)[0]
                if tgt is not None:
                    base = tgt
                    while base.type in ("array_access", "field_access"):
                        base = base.child_by_field_name("array") or base.child_by_field_name("object")
                    if base is not None and self.t(base) == name:
                        return True
            if x.type == "method_invocation":
                o = x.child_by_field_name("object")
                m = self.t(x.child_by_field_name("name"))
                if o is not None and self.t(o) == name and (m in MUTATORS or any(m in getattr(c, "mut_methods", ()) for c in self.classes.values())):
                    return True
            st.extend(x.children)
        return False

    def all_args(self, body):
        st = [body]
        while st:
            x = st.pop()
            if x.type == "argument_list":
                for a in named(x):
                    yield a
            st.extend(x.children)

    def changes_obj(self, body, name, cls):
        """does body assign a field of `name` or call a method that changes it"""
        ci = self.classes.get(cls)
        st = [body]
        while st:
            x = st.pop()
            if x.type == "method_invocation":
                o = x.child_by_field_name("object")
                if o is not None and self.t(o) == name:
                    m = self.t(x.child_by_field_name("name"))
                    owner = self.method_of(m, ci) if ci else None
                    if owner is None or m in owner.mut_methods:
                        return True
            if x.type in ("assignment_expression", "update_expression"):
                tgt = x.child_by_field_name("left") if x.type == "assignment_expression" else named(x)[0]
                if tgt is not None and tgt.type == "field_access" and self.t(tgt.child_by_field_name("object")) == name:
                    return True
            st.extend(x.children)
        return False

    def local_decl(self, n, ind):
        scope_node = n.parent
        for d in n.children_by_field_name("declarator"):
            name = self.t(d.child_by_field_name("name"))
            t = self.decl_type(n, d)
            v = d.child_by_field_name("value")
            mut = self.assigned_in(scope_node, name) or v is None
            val = None
            if v is not None:
                val = self.arr_init(v, t[4:-1]) if v.type == "array_initializer" else self.exw(v, t)
                if t in self.classes and v.type in ("array_access", "method_invocation") and self.ty(v) == t:
                    # an object out of a list: work on it in place
                    self.scope.add(name, t)
                    self.emit(f"let {safe(name)} = &mut {val};", ind)
                    continue
                if t == "String" and self.ty(v) == "str":
                    val = f"{val}.to_string()"
            self.scope.add(name, t)
            if self.java_types.get(name) in ("PImage", "PGraphics") and re.search(r"\b" + re.escape(name) + r"\.pixels\b", self.b.decode()) \
                    and (name + "_pixels") not in self.sketch:
                self.pending_px = name
            kw = "let mut" if mut else "let"
            ann = f": {t}" if (t not in self.classes and not t.startswith("Vec<") and t not in ("Json", "Xml", "TableRow")) or v is None else ""
            if val is None:
                self.emit(f"{kw} {safe(name)}: {t};", ind)
            else:
                self.emit(f"{kw} {safe(name)}{ann} = {val};", ind)
            if getattr(self, "pending_px", None) == name:
                self.pending_px = None
                self.emit(f"let mut {name}_pixels = {name}.load_pixels();", ind)

    def stmt(self, n, ind):
        k = n.type
        if k == "local_variable_declaration":
            self.local_decl(n, ind)
        elif k == "expression_statement":
            self.expr_stmt(named(n)[0], ind)
        elif k == "if_statement":
            self.if_stmt(n, ind, "if")
        elif k == "for_statement":
            self.for_stmt(n, ind)
        elif k == "enhanced_for_statement":
            name = self.t(n.child_by_field_name("name"))
            val = n.child_by_field_name("value")
            vt = self.ty(val)
            et = self.rt(self.t(n.child_by_field_name("type")))
            self.scope.push()
            self.scope.add(name, et)
            v = self.ex(val)
            if val.type == "method_invocation" and self.t(val.child_by_field_name("name")) in ("rows", "findRows", "matchRows"):
                self.emit(f"for {safe(name)} in {v} {{", ind)
            elif et in self.classes:
                body = n.child_by_field_name("body")
                changes = self.assigned_in(body, name) and self.changes_obj(body, name, et)
                coll = self.t(val)
                passes = changes and any(self.t(a) == coll for a in self.all_args(body))
                if passes:
                    # each one sees all the others: they look at a copy taken before the loop
                    self.emit(f"let others = {v}.clone();", ind)
                self.emit(f"for {safe(name)} in {v}.{'iter_mut' if changes else 'iter'}() {{", ind)
                if passes:
                    start = len(self.out)
                    self.block(self.stmts_of(n.child_by_field_name("body")), ind + 1)
                    for i in range(start, len(self.out)):
                        self.out[i] = self.out[i].replace(f"&{v}", "&others").replace(f"&mut {v}", "&mut others")
                    self.scope.pop()
                    self.emit("}", ind)
                    return
            elif isnum(et) or et in ("char", "bool", "PVector", "Color"):
                self.emit(f"for &{safe(name)} in {v}.iter() {{", ind)
            else:
                self.emit(f"for {safe(name)} in {v}.iter() {{", ind)
            self.block(self.stmts_of(n.child_by_field_name("body")), ind + 1)
            self.scope.pop()
            self.emit("}", ind)
        elif k == "while_statement":
            c = self.ex(named(n.child_by_field_name("condition"))[0])
            self.emit(f"while {c} {{", ind)
            self.scope.push()
            self.block(self.stmts_of(n.child_by_field_name("body")), ind + 1)
            self.scope.pop()
            self.emit("}", ind)
        elif k == "do_statement":
            self.emit("loop {", ind)
            self.block(self.stmts_of(n.child_by_field_name("body")), ind + 1)
            c = self.ex(named(n.child_by_field_name("condition"))[0])
            self.emit(f"if !({c}) {{ break; }}", ind + 1)
            self.emit("}", ind)
        elif k == "return_statement":
            v = named(n)
            self.emit("return" + (" " + self.exw(v[0], self.fn_ret) if v else "") + ";", ind)
        elif k == "break_statement":
            self.emit("break;", ind)
        elif k == "continue_statement":
            self.emit("continue;", ind)
        elif k == "block":
            self.emit("{", ind)
            self.scope.push()
            self.block(self.stmts_of(n), ind + 1)
            self.scope.pop()
            self.emit("}", ind)
        elif k == "class_declaration":
            self.class_decl(n, ind)
        elif k == "method_declaration":
            self.func(n, ind)
        elif k == "field_declaration":
            self.field_decl(n, ind)
        else:
            self.emit(f"/* TODO {k} */ " + self.t(n).replace("\n", " "), ind)

    def expr_stmt(self, e, ind):
        if e.type == "update_expression":
            target = named(e)[0]
            v = self.ex(target)
            one = "1.0" if self.ty(target) == "f32" else "1"
            self.emit(f"{v} {'+' if '++' in self.t(e) else '-'}= {one};", ind)
        elif e.type == "assignment_expression":
            L, R = e.child_by_field_name("left"), e.child_by_field_name("right")
            op = self.t(e.child_by_field_name("operator"))
            lt = self.ty(L)
            l = self.ex(L)
            if op == "=" and R.type == "assignment_expression":
                inner = R.child_by_field_name("left")
                self.expr_stmt(R, ind)
                self.emit(f"{l} = {self.ex(inner)};", ind)
                return
            if L.type == "array_access" and re.search(r"\b" + re.escape(self.t(L.child_by_field_name("array"))) + r"\b", self.t(L.child_by_field_name("index"))):
                idx = self.exw(L.child_by_field_name("index"), "usize")
                self.emit(f"let last = {idx};", ind)
                l = f"{self.ex(L.child_by_field_name('array'))}[last]"
            if L.type == "identifier" and self.in_helper and self.t(L) in self.mut_params and not l.startswith("*"):
                l = "*" + l
            if op == "=":
                r = self.arr_init(R, lt[4:-1]) if R.type == "array_initializer" else self.exw(R, lt)
                if lt == "String" and self.ty(R) == "str":
                    r += ".to_string()"
                elif R.type in ("identifier", "field_access", "array_access") and lt and (lt == "String" or lt.startswith("Vec<") or lt in self.classes) \
                        and not r.endswith((".clone()", ".to_vec()", ".to_string()")) and not (R.type == "identifier" and self.scope.local(self.t(R)) and self.t(R) not in self.slice_params):
                    r += ".clone()"
                self.emit(f"{l} = {r};", ind)
            else:
                o = op[:-1]
                if o == "+" and lt == "String":
                    self.emit(f"{l} += {'&' if self.ty(R) == 'String' else ''}{self.ex(R)};", ind)
                    return
                if o == ">>>":
                    o = ">>"
                self.emit(f"{l} {o}= {self.exw(R, lt)};", ind)
        elif e.type == "method_invocation":
            self.emit(self.ex(e).replace("\x00", "") + ";", ind)
        else:
            self.emit(self.ex(e) + ";", ind)

    def if_stmt(self, n, ind, kw, cont=False):
        c = self.ex(named(n.child_by_field_name("condition"))[0])
        if c.startswith("(") and c.endswith(")") and c.count("(") == 1:
            c = c[1:-1]
        line = f"{kw} {c} {{"
        if cont:
            self.out[-1] = self.out[-1] + " " + line
        else:
            self.emit(line, ind)
        self.scope.push()
        self.block(self.stmts_of(n.child_by_field_name("consequence")), ind + 1)
        self.scope.pop()
        alt = n.child_by_field_name("alternative")
        self.emit("}", ind)
        if alt is not None:
            if alt.type == "if_statement":
                self.if_stmt(alt, ind, "else if", cont=True)
            else:
                self.out[-1] += " else {"
                self.scope.push()
                self.block(self.stmts_of(alt), ind + 1)
                self.scope.pop()
                self.emit("}", ind)

    def for_stmt(self, n, ind):
        init = n.child_by_field_name("init")
        cond = n.child_by_field_name("condition")
        upd = n.child_by_field_name("update")
        body = n.child_by_field_name("body")
        self.scope.push()
        if init is not None and init.type == "local_variable_declaration" and cond is not None and upd is not None:
            decls = init.children_by_field_name("declarator")
            jt = self.decl_type(init, decls[0])
            if len(decls) == 1 and isint(jt):
                var = self.t(decls[0].child_by_field_name("name"))
                start = decls[0].child_by_field_name("value")
                if cond.type == "binary_expression" and self.t(cond.child_by_field_name("left")) == var \
                        and not self.assigned_in(body, var):
                    op = self.t(cond.child_by_field_name("operator"))
                    lim = cond.child_by_field_name("right")
                    ut = self.t(upd).replace(" ", "")
                    step = None
                    if ut in (var + "++", "++" + var):
                        step = 1
                    elif ut in (var + "--", "--" + var):
                        step = -1
                    else:
                        m = re.fullmatch(re.escape(var) + r"(\+|-)=(\d+)", ut)
                        if m:
                            step = int(m.group(2)) * (-1 if m.group(1) == "-" else 1)
                    if step == -1 and op == ">=" and start.type == "binary_expression" \
                            and self.t(start.child_by_field_name("operator")) == "-" and self.t(start.child_by_field_name("right")) == "1" \
                            and self.ty(start.child_by_field_name("left")) == "usize":
                        # from the last item down to `lim`: (lim..len).rev() never goes below 0
                        self.scope.add(var, "usize")
                        top = self.ex(start.child_by_field_name("left"))
                        self.emit(f"for {safe(var)} in ({self.exw(lim, 'usize')}..{top}).rev() {{", ind)
                        self.block(self.stmts_of(body), ind + 1)
                        self.emit("}", ind)
                        self.scope.pop()
                        return
                    if step:
                        lt = self.ty(lim)
                        vt = "usize" if lt == "usize" else "i32"
                        self.scope.add(var, vt)
                        s = self.exw(start, vt)
                        l = self.exw(lim, vt)
                        if step > 0 and op in ("<", "<="):
                            rng = f"{s}..{l}" if op == "<" else f"{s}..={l}"
                            if step != 1:
                                rng = f"({rng}).step_by({step})"
                        elif step < 0 and op in (">", ">="):
                            rng = f"({l}..={s})" if op == ">=" else f"({l} + 1..={s})"
                            rng += ".rev()" if step == -1 else f".rev().step_by({-step})"
                        else:
                            rng = None
                        if rng:
                            self.emit(f"for {safe(var)} in {rng} {{", ind)
                            self.block(self.stmts_of(body), ind + 1)
                            self.emit("}", ind)
                            self.scope.pop()
                            return
        # general form
        self.emit("{", ind)
        if init is not None:
            if init.type == "local_variable_declaration":
                self.local_decl(init, ind + 1)
                for d in init.children_by_field_name("declarator"):
                    i = len(self.out) - 1
                    nm = safe(self.t(d.child_by_field_name("name")))
                    self.out[i] = self.out[i].replace(f"let {nm}", f"let mut {nm}")
            else:
                self.expr_stmt(init, ind + 1)
        c = self.ex(cond) if cond is not None else "true"
        self.emit(f"while {c} {{", ind + 1)
        self.scope.push()
        self.block(self.stmts_of(body), ind + 2)
        self.scope.pop()
        if upd is not None:
            self.expr_stmt(upd, ind + 2)
        self.emit("}", ind + 1)
        self.emit("}", ind)
        self.scope.pop()

    def params(self, n):
        ps = []
        body = n.child_by_field_name("body")
        for p in named(n.child_by_field_name("parameters")):
            if p.type == "formal_parameter":
                name = self.t(p.child_by_field_name("name"))
                t = self.decl_type(p, p)
                changed = body is not None and self.assigned_in(body, name)
                self.scope.add(name, t)
                stored = body is not None and self.stored(body, name)
                if t in self.classes and stored:
                    ps.append((safe(name), t))
                elif t in self.classes:
                    t = f"&mut {t}" if changed else f"&{t}"
                    ps.append((safe(name), t))
                elif t in LIB_REF:
                    ps.append((safe(name), f"&mut {t}" if changed else ("&str" if t == "String" else f"&{t}")))
                    if t == "String" and not changed:
                        self.slice_params.add(name)
                elif t.startswith("Vec<"):
                    ps.append((safe(name), f"&mut {t}" if changed else f"&[{t[4:-1]}]"))
                    if not changed:
                        self.slice_params.add(name)
                else:
                    ps.append(((f"mut {safe(name)}" if changed else safe(name)), t))
        return ps

    def stored(self, body, name):
        """is the parameter kept: pushed into a list or assigned to something"""
        st = [body]
        while st:
            x = st.pop()
            if x.type == "assignment_expression" and self.t(x.child_by_field_name("right")) == name:
                return True
            if x.type == "method_invocation" and self.t(x.child_by_field_name("name")) in ("add", "push", "append"):
                if any(self.t(a) == name for a in named(x.child_by_field_name("arguments"))):
                    return True
            st.extend(x.children)
        return False

    def ptypes(self, n):
        out = []
        body = n.child_by_field_name("body")
        for p in named(n.child_by_field_name("parameters")):
            if p.type == "formal_parameter":
                t = self.decl_type(p, p)
                nm = self.t(p.child_by_field_name("name"))
                if body is not None and t in self.classes and self.stored(body, nm):
                    t = "own " + t
                elif body is not None and self.assigned_in(body, nm) and (t.startswith("Vec<") or t in self.classes):
                    t = "mut " + t
                out.append(t)
        return out

    def func(self, n, ind):
        name = self.t(n.child_by_field_name("name"))
        self.scope.push()
        ps = self.params(n)
        self.cur_fn = name
        self.cur_params = {p[0].replace("mut ", "") for p in ps}
        ret = self.decl_type(n)
        self.fn_ret = ret
        key = f"{self.cls.name}.{name}" if self.cls else name
        extra = self.extra.get(key, [])
        prev = (self.in_helper, getattr(self, "mut_params", set()))
        lifecycle = not self.cls and snake(name) in LIFECYCLE
        if extra:
            self.in_helper = True
            self.mut_params = {v for v, m in extra if m}
            self.ro_params = {v for v, m in extra if not m}
            for v, m in extra:
                t = self.sketch[v]
                ps.append((v, f"&mut {t}" if m else (t if t in ("f32", "i32", "bool", "char", "u64", "u32", "Color", "PVector", "usize") else f"&{t}")))
                self.scope.stack[-1].pop(v, None)
        sig = ", ".join(f"{a}: {b}" for a, b in ps)
        r = "" if ret in ("void", "") else f" -> {ret}"
        fname = snake(name) if not lifecycle else snake(name)
        if self.cls:
            me = "&mut self" if name in self.cls.mut_methods else "&self"
            self.emit(f"fn {safe(fname)}({me}{', ' if sig else ''}{sig}){r} {{", ind)
        else:
            self.emit(f"fn {fname}({sig}){r} {{", ind)
        body = n.child_by_field_name("body")
        for p in named(n.child_by_field_name("parameters")):
            if p.type == "formal_parameter" and self.t(p.child_by_field_name("type")).strip() == "PImage":
                pn = self.t(p.child_by_field_name("name"))
                if re.search(r"\b" + re.escape(pn) + r"\.pixels\b", self.t(body)):
                    self.emit(f"let {pn}_pixels = {pn}.load_pixels();", ind + 1)
        self.block(self.stmts_of(body), ind + 1)
        self.scope.pop()
        self.emit("}", ind)
        self.in_helper, self.mut_params = prev
        self.fn_ret = None
        self.cur_fn = None

    def field_decl(self, n, ind):
        for d in n.children_by_field_name("declarator"):
            name = self.t(d.child_by_field_name("name"))
            t = self.decl_type(n, d)
            v = d.child_by_field_name("value")
            if name in self.consts:
                cv = self.exw(v, t)
                self.emit(f"const {self.consts[name]}: {t} = {cv};", ind)
                continue
            val = self.zero(t) if v is None else (self.arr_init(v, t[4:-1]) if v.type == "array_initializer" else self.exw(v, t))
            if t == "String" and v is not None and self.ty(v) == "str":
                val += ".to_string()"
            copy = t in ("f32", "i32", "bool", "char", "u64", "u32", "Color", "usize", "i8", "String")
            mut = "mut " if name in self.mutated or v is None or not copy else ""
            self.emit(f"let {mut}{safe(name)}: {t} = {val};", ind)

    # ── classes ───────────────────────────────────────────────────────────
    def class_decl(self, n, ind):
        ci = self.classes[self.t(n.child_by_field_name("name"))]
        prev = self.cls
        self.cls = ci
        body = n.child_by_field_name("body")
        members = [c for c in body.children if c.is_named or is_comment(c)]
        fields = [m for m in members if m.type == "field_declaration"]
        self.emit("#[derive(Clone, Default)]", ind)
        self.emit(f"struct {ci.name} {{", ind)
        if ci.base:
            self.emit(f"{snake(ci.base)}: {ci.base},  // what {ci.name} builds on (Java: extends {ci.base})", ind + 1)
        for f in fields:
            for d in f.children_by_field_name("declarator"):
                nm = self.t(d.child_by_field_name("name"))
                self.emit(f"{safe(nm)}: {self.decl_type(f, d)},", ind + 1)
        self.emit("}", ind)
        self.emit("", ind)
        self.emit(f"impl {ci.name} {{", ind)
        pending = []
        first = True
        for m in members:
            if m.type == "field_declaration":
                continue
            if is_comment(m):
                pending.append(m)
                continue
            if not first:
                self.emit("", ind + 1)
            first = False
            for c in pending:
                for l in self.t(c).split("\n"):
                    self.emit(l.strip() if not l.strip().startswith("*") else " " + l.strip(), ind + 1)
            pending = []
            if m.type == "constructor_declaration":
                self.ctor(m, fields, ind + 1)
            elif m.type == "method_declaration":
                self.func(m, ind + 1)
        if not ci.ctors:
            if not first:
                self.emit("", ind + 1)
            self.ctor(None, fields, ind + 1)
        self.emit("}", ind)
        self.cls = prev

    def ctor(self, m, fields, ind):
        ci = self.cls
        self.scope.push()
        ps = self.params(m) if m is not None else []
        extra = self.extra.get(ci.name, [])
        prev = (self.in_helper, getattr(self, "mut_params", set()))
        if extra:
            self.in_helper = True
            self.mut_params = {v for v, mm in extra if mm}
            self.ro_params = {v for v, mm in extra if not mm}
            for v, mm in extra:
                t = self.sketch[v]
                ps.append((v, f"&mut {t}" if mm else (t if t in ("f32", "i32", "bool", "char", "u64", "u32", "Color", "PVector", "usize") else f"&{t}")))
        sig = ", ".join(f"{a}: {b}" for a, b in ps)
        self.emit(f"fn new({sig}) -> {ci.name} {{", ind)
        stmts = self.stmts_of(m.child_by_field_name("body")) if m is not None else []
        # field values: initializers first, then plain `field = value;` at the top of the body
        vals = {}
        order = []
        for f in fields:
            for d in f.children_by_field_name("declarator"):
                nm = self.t(d.child_by_field_name("name"))
                t = self.decl_type(f, d)
                v = d.child_by_field_name("value")
                vals[nm] = (self.zero(t) if v is None else (self.arr_init(v, t[4:-1]) if v.type == "array_initializer" else self.exw(v, t)))
                order.append(nm)
        if ci.base:
            order.insert(0, snake(ci.base))
            vals[snake(ci.base)] = f"{ci.base}::default()"
            for i, st_ in enumerate(stmts):
                if st_.type == "explicit_constructor_invocation":
                    base = self.classes[ci.base]
                    an_ = [a for a in named(st_.child_by_field_name("arguments")) if not is_comment(a)]
                    ps_ = base.ctor_types(len(an_)) or []
                    self.cls = None
                    args_ = [self.arg(x, ps_[j] if j < len(ps_) else None) for j, x in enumerate(an_)]
                    self.cls = ci
                    vals[snake(ci.base)] = f"{ci.base}::new({', '.join(args_)})"
                    stmts = stmts[:i] + stmts[i + 1:]
                    break
        rest = list(stmts)
        simple = True
        taken = {}
        self.cls = None  # inside new(), field names are plain locals/params
        while rest:
            s = rest[0]
            if is_comment(s):
                break
            e = named(s)[0] if s.type == "expression_statement" else None
            if e is not None and e.type == "assignment_expression" and self.t(e.child_by_field_name("operator")) == "=":
                L = e.child_by_field_name("left")
                nm = None
                if L.type == "identifier" and self.t(L) in vals and not self.scope.local(self.t(L)):
                    nm = self.t(L)
                elif L.type == "field_access" and L.child_by_field_name("object").type == "this":
                    nm = self.t(L.child_by_field_name("field"))
                if nm and nm in vals and not any(re.search(r"\b" + re.escape(o) + r"\b", self.t(e.child_by_field_name("right"))) for o in order if o in taken or o not in [p[0] for p in ps]):
                    rv = self.exw(e.child_by_field_name("right"), ci.fields.get(nm))
                    ft = ci.fields.get(nm) or ""
                    if e.child_by_field_name("right").type == "array_access" and (ft == "String" or ft.startswith("Vec<")):
                        rv += ".clone()"
                    taken[nm] = rv
                    rest.pop(0)
                    continue
            break
        self.cls = ci
        for nm, v in taken.items():
            vals[nm] = v
        if not rest:
            self.emit(f"{ci.name} {{", ind + 1)
            for nm in order:
                v = vals[nm]
                self.emit(f"{safe(nm)}," if v == safe(nm) else f"{safe(nm)}: {v},", ind + 2)
            self.emit("}", ind + 1)
        else:
            self.emit(f"let mut this = {ci.name} {{", ind + 1)
            for nm in order:
                v = vals[nm]
                self.emit(f"{safe(nm)}," if v == safe(nm) else f"{safe(nm)}: {v},", ind + 2)
            self.emit("};", ind + 1)
            start = len(self.out)
            self.block(rest, ind + 1)
            for i in range(start, len(self.out)):
                self.out[i] = re.sub(r"\bself\.", "this.", self.out[i])
            self.emit("this", ind + 1)
        self.emit("}", ind)
        self.in_helper, self.mut_params = prev
        self.scope.pop()

    # ── program ───────────────────────────────────────────────────────────
    def body_nodes(self):
        root = self.tree.root_node
        cls = [c for c in root.children if c.type == "class_declaration"][0]
        kids = [c for c in cls.child_by_field_name("body").children if c.is_named or is_comment(c)]
        if self.static:
            m = [c for c in kids if c.type == "method_declaration"][0]
            kids = [c for c in m.child_by_field_name("body").children if c.is_named or is_comment(c)]
        return kids

    def collect(self, kids):
        cl = [k for k in kids if k.type == "class_declaration"]
        names = {self.t(k.child_by_field_name("name")) for k in cl}
        done = set()
        while cl:
            for k in list(cl):
                sup = k.child_by_field_name("superclass")
                b = self.t(named(sup)[0]) if sup else None
                if b is None or b not in names or b in done:
                    self.add_class(k)
                    done.add(self.t(k.child_by_field_name("name")))
                    cl.remove(k)
        for k in kids:
            if k.type == "method_declaration":
                nm = self.t(k.child_by_field_name("name"))
                self.funcs[nm] = self.decl_type(k)
                self.func_params[nm] = self.ptypes(k)
            elif k.type == "field_declaration":
                for d in k.children_by_field_name("declarator"):
                    self.sketch[self.t(d.child_by_field_name("name"))] = self.decl_type(k, d)
        # Processing's pixels[] (and img.pixels[]) become sketch variables
        # filled by load_pixels(), when more than one function can see them
        self.pixel_vars = []
        if not self.static:
            src = self.b.decode()
            if re.search(r"(?<![\w.])pixels\s*\[", src):
                self.pixel_vars.append("pixels")
            for m in sorted(set(re.findall(r"\b(\w+)\.pixels\b", src))):
                if m in self.sketch:
                    self.pixel_vars.append(m + "_pixels")
            for v in self.pixel_vars:
                self.sketch[v] = "Vec<u32>"
                self.mutated.add(v)

    def add_class(self, k):
        name = self.t(k.child_by_field_name("name"))
        ci = ClassInfo(name, k)
        ci.param_types = {}
        sup = k.child_by_field_name("superclass")
        if sup:
            ci.base = self.t(named(sup)[0])
        self.classes[name] = ci
        for m in k.child_by_field_name("body").children:
            if m.type == "field_declaration":
                for d in m.children_by_field_name("declarator"):
                    ci.fields[self.t(d.child_by_field_name("name"))] = self.decl_type(m, d)
            elif m.type == "method_declaration":
                nm = self.t(m.child_by_field_name("name"))
                ci.methods[nm] = self.decl_type(m)
                ci.param_types[nm] = self.ptypes(m)
            elif m.type == "constructor_declaration":
                ci.ctors.append(m)
        # which methods change the object (they take &mut self; the rest &self)
        bodies = {}
        for m in k.child_by_field_name("body").children:
            if m.type == "method_declaration":
                bodies[self.t(m.child_by_field_name("name"))] = m.child_by_field_name("body")
        mut = set()
        allf = set(ci.fields)
        bc = self.classes.get(ci.base)
        while bc:
            allf |= set(bc.fields)
            bc = self.classes.get(bc.base)
        for nm, b in bodies.items():
            if b is not None and any(self.assigned_in(b, f) for f in allf):
                mut.add(nm)
            elif b is not None:
                # looping over a field of objects and calling them: assume it changes them
                st = [b]
                while st:
                    x = st.pop()
                    if x.type == "enhanced_for_statement" and self.t(x.child_by_field_name("value")) in ci.fields \
                            and "(" in self.t(x.child_by_field_name("body")):
                        mut.add(nm)
                        break
                    st.extend(x.children)
        changed = True
        while changed:
            changed = False
            for nm, b in bodies.items():
                if nm in mut or b is None:
                    continue
                st = [b]
                while st:
                    x = st.pop()
                    if x.type == "method_invocation" and x.child_by_field_name("object") in (None,) and self.t(x.child_by_field_name("name")) in mut:
                        mut.add(nm); changed = True; break
                    if x.type == "method_invocation" and x.child_by_field_name("object") is not None and x.child_by_field_name("object").type == "this" and self.t(x.child_by_field_name("name")) in mut:
                        mut.add(nm); changed = True; break
                    st.extend(x.children)
        ci.mut_methods = mut
        ctor_ps = [self.ptypes(c) for c in ci.ctors]
        ci.ctor_types = lambda n, cp=ctor_ps: next((p for p in cp if len(p) == n), None)

    def uses(self, node, names):
        """sketch names read in node, and the ones written"""
        r, w = set(), set()
        local = set()
        st = [node]
        while st:
            x = st.pop()
            if x.type in ("local_variable_declaration", "formal_parameter"):
                for d in (x.children_by_field_name("declarator") or [x]):
                    nn = d.child_by_field_name("name")
                    if nn is not None:
                        local.add(self.t(nn))
            if x.type == "identifier" and self.t(x) in names:
                p = x.parent
                f = p.child_by_field_name("field") if p.type == "field_access" else None
                nm = p.child_by_field_name("name") if p.type in ("method_invocation", "method_declaration", "constructor_declaration", "class_declaration") else None
                if f is not None and f.start_byte == x.start_byte:
                    pass
                elif nm is not None and nm.start_byte == x.start_byte:
                    pass
                else:
                    r.add(self.t(x))
            st.extend(x.children)
        r -= local
        for v in list(r):
            if self.assigned_in(node, v):
                w.add(v)
        return r, w

    def plan(self, kids):
        """Which helpers and classes need which sketch variables."""
        names = set(self.sketch)
        # sketch vars that are assigned anywhere (top-level code included)
        for k in kids:
            for v in names:
                if k.type != "field_declaration" and self.assigned_in(k, v):
                    self.mutated.add(v)
        # constants: never changed, simple number values
        self.consts = {}
        for k in kids:
            if k.type == "field_declaration":
                for d in k.children_by_field_name("declarator"):
                    nm = self.t(d.child_by_field_name("name"))
                    v = d.child_by_field_name("value")
                    t = self.sketch[nm]
                    if v is not None and nm not in self.mutated and isnum(t) and re.fullmatch(r"[-\d.fFeE+ *]+", self.t(v)):
                        self.consts[nm] = nm.upper()
        cand = dict(self.consts)
        names -= set(cand)
        helpers = {}
        for k in kids:
            if k.type == "method_declaration":
                nm = self.t(k.child_by_field_name("name"))
                if snake(nm) not in LIFECYCLE:
                    helpers[nm] = k
            elif k.type == "class_declaration":
                cname = self.t(k.child_by_field_name("name"))
                ci = self.classes[cname]
                for m in k.child_by_field_name("body").children:
                    if m.type == "method_declaration":
                        helpers[f"{cname}.{self.t(m.child_by_field_name('name'))}"] = m
                    elif m.type == "constructor_declaration":
                        helpers[cname] = m
                if not ci.ctors:
                    # field initializers run in new()
                    helpers[cname] = None
                    ci.init_node = k
        need = {}
        for h, node in helpers.items():
            if node is None:
                fields = [m for m in self.classes[h].node.child_by_field_name("body").children if m.type == "field_declaration"]
                r, w = set(), set()
                for f in fields:
                    a, b = self.uses(f, names)
                    r |= a
                    w |= b
            else:
                r, w = self.uses(node, names)
            if "." in h or h in self.classes:
                cname = h.split(".")[0]
                r = {v for v in r if not self.field(v, self.classes[cname])}
                w = {v for v in w if not self.field(v, self.classes[cname])}
            need[h] = (r, w)
        # a helper that calls another helper needs what that one needs
        calls = {}
        for h, node in helpers.items():
            cs = set()
            st = [node] if node is not None else []
            while st:
                x = st.pop()
                if x.type == "method_invocation":
                    nm = self.t(x.child_by_field_name("name"))
                    for h2 in helpers:
                        if h2 == nm or h2.endswith("." + nm):
                            cs.add(h2)
                if x.type == "object_creation_expression":
                    tn = re.sub(r"<.*>", "", self.t(x.child_by_field_name("type"))).strip()
                    if tn in helpers:
                        cs.add(tn)
                st.extend(x.children)
            calls[h] = cs - {h}
        changed = True
        while changed:
            changed = False
            for h in helpers:
                r, w = need[h]
                for h2 in calls[h]:
                    r2, w2 = need[h2]
                    if not r2 <= r or not w2 <= w:
                        r, w = r | r2, w | w2
                        changed = True
                need[h] = (r, w)
        self.extra = {h: [(v, v in w) for v in sorted(r)] for h, (r, w) in need.items() if r}
        # a never-changed number only becomes a const when a helper or class needs it
        used = set()
        for h, node in helpers.items():
            nodes = [node] if node is not None else [m for m in self.classes[h].node.child_by_field_name("body").children if m.type == "field_declaration"]
            for nd in nodes:
                a, _ = self.uses(nd, set(cand))
                used |= a
        self.consts = {k: v for k, v in cand.items() if k in used}
        for h, lst in self.extra.items():
            for v, m in lst:
                if m:
                    self.mutated.add(v)

    def run(self):
        self.func_params = {}
        self.post = []
        kids = self.body_nodes()
        self.collect(kids)
        if self.static:
            header = []
            while kids and is_comment(kids[0]):
                header.append(kids.pop(0))
            self.consts = {}
            self.block(header, 0)
            self.emit("", 0)
            self.emit("fn setup() {", 0)
            self.scope.push()
            self.block(kids, 1)
            self.scope.pop()
            self.emit("}", 0)
        else:
            self.plan(kids)
            hdr = 0
            while hdr < len(kids) and is_comment(kids[hdr]):
                hdr += 1
            self.block(kids[:hdr], 0)
            if self.pixel_vars:
                self.emit("", 0)
                for v in self.pixel_vars:
                    self.emit(f"let mut {v}: Vec<u32> = Vec::new();  // filled by load_pixels()", 0)
            self.block(kids[hdr:], 0)
        out = "\n".join(self.out)
        out = re.sub(r"[ \t]+\n", "\n", out)
        out = re.sub(r"\n{3,}", "\n\n", out).strip("\n") + "\n"
        return out


MUTATORS = {"add", "sub", "mult", "div", "normalize", "limit", "set", "setMag", "rotate", "lerp",
            "push", "remove", "clear", "append", "insert", "sort", "sortReverse", "shuffle", "reverse",
            "increment", "addRow", "removeRow", "setInt", "setFloat", "setString", "setJSONObject",
            "setJSONArray", "resize", "mask", "filter", "updatePixels", "loadPixels", "beginDraw", "endDraw",
            "translate", "rotateX", "rotateY", "rotateZ", "scale", "setFill", "setStroke", "setVertex",
            "addChild", "removeChild", "update", "move", "run", "display", "step", "render", "grow"}
LIB_REF = {"IntList", "FloatList", "StringList", "Table", "Json", "Xml", "String", "IntDict",
           "FloatDict", "StringDict", "PShape"}

LIFECYCLE = {"setup", "draw", "settings", "mouse_pressed", "mouse_released", "mouse_moved", "mouse_dragged",
             "mouse_clicked", "mouse_wheel", "key_pressed", "key_released", "key_typed", "mouse_entered",
             "mouse_exited", "focus_gained", "focus_lost", "window_moved", "window_resized"}

if __name__ == "__main__":
    print(Rs(open(sys.argv[1]).read()).run(), end="")
