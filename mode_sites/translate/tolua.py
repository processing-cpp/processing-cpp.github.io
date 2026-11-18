"""Processing (Java) example -> LuaMode sketch. First draft; checked by
running it, then fixed by hand where needed."""
import re, sys
from common import *

STRING_METHODS = {"toUpperCase": "upper", "toLowerCase": "lower"}
STATIC_PVEC = {"add": "+", "sub": "-", "mult": "*", "div": "/"}


LUA_KW = {"end", "repeat", "until", "local", "function", "nil", "not", "and", "or", "then",
          "elseif", "in", "goto", "do"}


def safe(name):
    return name + "_" if name in LUA_KW else name


class Lua:
    def __init__(self, src):
        self.src = src
        self.tree, self.b, self.static = parse(src)
        self.scope = Scope()
        self.classes = {}
        self.funcs = {}
        self.cls = None          # ClassInfo while inside a class
        self.loopvars = []       # numeric for vars shifted to 1-based
        self.need_array = False
        self.label = 0
        self.out = []
        self.notes = []
        self.post = []

    # ── helpers ───────────────────────────────────────────────────────────
    def t(self, n):
        return text(self.b, n)

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
                self.funcs[self.t(k.child_by_field_name("name"))] = self.decl_type(k)
            elif k.type in ("field_declaration", "local_variable_declaration"):
                for d in k.children_by_field_name("declarator"):
                    self.scope.add(self.t(d.child_by_field_name("name")), self.decl_type(k, d))

    def add_class(self, k):
        name = self.t(k.child_by_field_name("name"))
        ci = ClassInfo(name, k)
        sup = k.child_by_field_name("superclass")
        if sup:
            ci.base = self.t(named(sup)[0])
        for m in k.child_by_field_name("body").children:
            if m.type == "field_declaration":
                for d in m.children_by_field_name("declarator"):
                    ci.fields[self.t(d.child_by_field_name("name"))] = self.decl_type(m, d)
            elif m.type == "method_declaration":
                ci.methods[self.t(m.child_by_field_name("name"))] = self.decl_type(m)
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

    def method_of(self, name, ci=None):
        ci = ci or self.cls
        while ci:
            if name in ci.methods:
                return ci
            ci = self.classes.get(ci.base)
        return None

    # ── types ─────────────────────────────────────────────────────────────
    def ty(self, n):
        k = n.type
        if k == "decimal_integer_literal" or k == "hex_integer_literal":
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
            return self.ty(named(n)[0])
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
            if f in ("x", "y", "z") or f in ("width", "height"):
                return "float" if ot == "PVector" else "int"
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
                return {"length": "int", "charAt": "char", "indexOf": "int"}.get(name, "String")
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

    def ex(self, n, want_int=False):
        k = n.type
        if k == "decimal_integer_literal":
            return self.t(n).rstrip("lL")
        if k == "hex_integer_literal":
            return self.t(n).rstrip("lL")
        if k == "decimal_floating_point_literal":
            v = self.t(n).rstrip("fFdD")
            if v.startswith("."):
                v = "0" + v
            if v.endswith("."):
                v += "0"
            return v
        if k == "string_literal":
            return self.t(n)
        if k == "character_literal":
            c = self.t(n)[1:-1]
            return '"' + c.replace('"', '\\"') + '"'
        if k in ("true", "false"):
            return k
        if k == "null_literal":
            return "nil"
        if k == "this":
            return "self"
        if k == "identifier":
            name = self.t(n)
            if not self.scope.local(name) and self.cls and self.field(name):
                return "self." + safe(name)
            return safe(name)
        if k == "parenthesized_expression":
            return "(" + self.ex(named(n)[0], want_int) + ")"
        if k == "binary_expression":
            return self.binary(n, want_int)
        if k == "unary_expression":
            op = self.t(n.child_by_field_name("operator"))
            v = self.ex(n.child_by_field_name("operand"))
            return {"!": "not ", "-": "-", "+": "", "~": "~"}[op] + v
        if k == "update_expression":
            return "--[[TODO update in expression]] " + self.t(n)
        if k == "cast_expression":
            t = self.t(n.child_by_field_name("type"))
            v = self.ex(n.child_by_field_name("value"))
            if t in ("int", "long"):
                return f"int({v})"
            if t == "char":
                return f"char({v})"
            return v
        if k == "ternary_expression":
            c = self.ex(n.child_by_field_name("condition"))
            a = self.ex(n.child_by_field_name("consequence"))
            e = self.ex(n.child_by_field_name("alternative"))
            return f"({c} and {a} or {e})"
        if k == "assignment_expression":
            return "--[[TODO assignment in expression]] " + self.t(n)
        if k == "array_access":
            return self.index(n)
        if k == "field_access":
            obj, f = n.child_by_field_name("object"), self.t(n.child_by_field_name("field"))
            if f == "length" and obj.type != "this":
                return "#" + self.ex(obj)
            if obj.type == "super":
                return "self." + f
            return self.ex(obj) + "." + safe(f)
        if k == "method_invocation":
            return self.call(n)
        if k == "object_creation_expression":
            t = re.sub(r"<.*>", "", self.t(n.child_by_field_name("type"))).strip()
            a = self.args(n)
            if t == "PVector":
                return f"createVector({', '.join(a)})"
            if t in ("ArrayList", "HashMap", "LinkedList"):
                return "{}"
            if t in self.classes:
                return f"{t}.new({', '.join(a)})"
            return f"{t}({', '.join(a)})"
        if k == "array_creation_expression":
            init = n.child_by_field_name("value")
            if init:
                return self.ex(init)
            dims = [self.ex(named(d)[0], True) for d in n.children if d.type == "dimensions_expr"]
            t = self.t(n.child_by_field_name("type"))
            zero = "false" if t == "boolean" else ("0" if numeric(t) else "nil")
            self.need_array = True
            return f"newArray({', '.join(dims)}, {zero})"
        if k == "array_initializer":
            return "{" + ", ".join(self.ex(c) for c in named(n)) + "}"
        if k == "lambda_expression":
            return "--[[TODO lambda]] " + self.t(n)
        return f"--[[TODO {k}]] " + self.t(n)

    def binary(self, n, want_int):
        op = self.t(n.child_by_field_name("operator"))
        L, R = n.child_by_field_name("left"), n.child_by_field_name("right")
        lt, rt = self.ty(L), self.ty(R)
        if op == "+" and "String" in (lt, rt):
            return f"{self.ex(L)} .. {self.ex(R)}"
        sub_int = want_int or op in ("%",)
        l, r = self.ex(L, sub_int), self.ex(R, sub_int)
        if op == "/" and intlike(lt) and intlike(rt) and want_int:
            return f"{l} // {r}"
        lua = {"&&": "and", "||": "or", "!=": "~=", "^": "~", ">>>": ">>"}.get(op, op)
        return f"{l} {lua} {r}"

    def index(self, n):
        arr = n.child_by_field_name("array")
        idx = n.child_by_field_name("index")
        a = self.ex(arr)
        if idx.type == "update_expression" and self.t(idx).endswith(("++", "--")):
            v = self.ex(named(idx)[0])
            self.post.append(f"{v} = {v} {'+' if self.t(idx).endswith('++') else '-'} 1")
            return f"{a}[{v} + 1]"
        if a == "pixels" or a.endswith(".pixels"):
            return f"{a}[{self.ex(idx, True)}]"
        if idx.type == "identifier" and self.t(idx) in self.loopvars:
            return f"{a}[{self.t(idx)}]"
        i = self.ex(idx, True)
        m = re.fullmatch(r"(.*) - 1", i)
        if m and idx.type == "binary_expression":
            return f"{a}[{m.group(1)}]"
        if re.fullmatch(r"\d+", i):
            return f"{a}[{int(i) + 1}]"
        return f"{a}[{i} + 1]"

    def call(self, n):
        name = self.t(n.child_by_field_name("name"))
        obj = n.child_by_field_name("object")
        a = self.args(n)
        A = ", ".join(a)
        if obj is None:
            if self.cls and self.method_of(name):
                return f"self:{safe(name)}({A})"
            if name.startswith("__"):
                name = {"__boolean": "toboolean"}.get(name, name[2:])
            if name == "println":
                name = "print"
            if name in ("max", "min") and len(a) == 1:
                return f"math.{name}(table.unpack({a[0]}))"
            return f"{name}({A})"
        if obj.type == "super":
            base = self.cls.base if self.cls else "?"
            return f"{base}.{name}(self{', ' if a else ''}{A})"
        o = self.ex(obj)
        ot = self.ty(obj)
        if obj.type == "identifier" and o == "PVector":
            if name in STATIC_PVEC:
                return f"({a[0]} {STATIC_PVEC[name]} {a[1]})"
            if name in ("dist", "dot", "cross", "angleBetween") and name != "angleBetween":
                return f"{a[0]}:{name}({a[1]})"
            return f"PVector.{name}({A})"
        if obj.type == "identifier" and o[0].isupper() and ot is None and o not in self.classes:
            if o == "Math":
                return f"math.{name}({A})"
            return f"{o}.{name}({A})"
        if obj.type == "identifier" and o in ("Math",):
            return f"math.{name}({A})"
        if ot == "String":
            if name == "length":
                return f"#{o}"
            if name == "charAt":
                i = a[0]
                return f"{o}:sub({i} + 1, {i} + 1)" if not re.fullmatch(r"\d+", i) else f"{o}:sub({int(i)+1}, {int(i)+1})"
            if name == "substring":
                if len(a) == 1:
                    return f"{o}:sub({a[0]} + 1)"
                return f"{o}:sub({a[0]} + 1, {a[1]})"
            if name == "replaceAll" or name == "replace":
                return f"{o}:gsub({a[0]}, {a[1]})"
            if name == "equals":
                return f"{o} == {a[0]}"
            if name in STRING_METHODS:
                return f"{o}:{STRING_METHODS[name]}()"
            if name == "indexOf":
                return f"(({o}:find({a[0]}, 1, true) or 0) - 1)"
        bt = base_type(ot)
        if bt in ("ArrayList", "LinkedList"):
            if name == "add":
                return f"table.insert({o}, {A})" if len(a) == 1 else f"table.insert({o}, {a[0]} + 1, {a[1]})"
            if name == "get":
                return f"{o}[{self.index_text(n, 0)}]"
            if name == "size":
                return f"#{o}"
            if name == "remove":
                return f"table.remove({o}, {self.index_text(n, 0)})"
            if name == "set":
                return f"--[[set]] {o}[{self.index_text(n, 0)}] = {a[1]}"
            if name == "clear":
                return f"for i = #{o}, 1, -1 do {o}[i] = nil end"
            if name == "isEmpty":
                return f"#{o} == 0"
        if bt.endswith("[]") or (ot or "").endswith("[]"):
            pass
        return f"{o}:{safe(name)}({A})"

    def index_text(self, call, i):
        arg = named(call.child_by_field_name("arguments"))[i]
        if arg.type == "identifier" and self.t(arg) in self.loopvars:
            return self.t(arg)
        v = self.ex(arg, True)
        if re.fullmatch(r"\d+", v):
            return str(int(v) + 1)
        m = re.fullmatch(r"(.*) - 1", v)
        if m and arg.type == "binary_expression":
            return m.group(1)
        return f"{v} + 1"

    # ── statements ────────────────────────────────────────────────────────
    def emit(self, line, ind):
        if self.notes and line:
            line += "  -- " + ", ".join(self.notes)
            self.notes = []
        self.out.append("  " * ind + line if line else "")
        if self.post and line:
            post, self.post = self.post, []
            for p in post:
                self.out.append("  " * ind + p)

    def comment(self, n, ind):
        c = self.t(n)
        if n.type == "line_comment":
            return "--" + c[2:]
        body = c[2:-2]
        if body.startswith("*"):
            body = body[1:]
        lines = [re.sub(r"^\s*\* ?", "", l) for l in body.split("\n")]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if len(lines) == 1:
            return "-- " + lines[0].strip()
        pad = "  " * ind
        return "--[[\n" + "\n".join((pad + "  " + l) if l.strip() else "" for l in lines) + "\n" + pad + "]]"

    def block(self, kids, ind):
        prev = None
        for k in kids:
            if prev is not None and k.start_point.row > prev.end_point.row + 1:
                self.emit("", ind)
            if is_comment(k) and prev is not None and k.start_point.row == prev.end_point.row and self.out:
                self.out[-1] += "  " + self.comment(k, ind)
            elif is_comment(k):
                for l in self.comment(k, ind).split("\n"):
                    self.out.append(("  " * ind + l) if l and not l.startswith("  " * ind) else l)
            else:
                self.stmt(k, ind)
            prev = k

    def stmts_of(self, n):
        if n.type in ("block", "constructor_body"):
            return [c for c in n.children if c.is_named or is_comment(c)]
        return [n]

    def stmt(self, n, ind):
        k = n.type
        if k == "local_variable_declaration":
            for d in n.children_by_field_name("declarator"):
                name = safe(self.t(d.child_by_field_name("name")))
                t = self.decl_type(n, d)
                self.scope.add(name, t)
                v = d.child_by_field_name("value")
                if v is not None:
                    self.emit(f"local {name} = {self.ex(v, intlike(t))}", ind)
                else:
                    self.emit(f"local {name}", ind)
        elif k == "expression_statement":
            e = named(n)[0]
            self.expr_stmt(e, ind)
        elif k == "if_statement":
            self.if_stmt(n, ind, "if")
            self.emit("end", ind)
        elif k == "for_statement":
            self.for_stmt(n, ind)
        elif k == "enhanced_for_statement":
            name = self.t(n.child_by_field_name("name"))
            val = n.child_by_field_name("value")
            self.scope.push()
            self.scope.add(name, self.t(n.child_by_field_name("type")))
            if val.type == "method_invocation" and self.t(val.child_by_field_name("name")) == "rows":
                self.emit(f"for {name} in {self.ex(val)} do", ind)
            else:
                self.emit(f"for _, {name} in ipairs({self.ex(val)}) do", ind)
            self.block(self.stmts_of(n.child_by_field_name("body")), ind + 1)
            self.scope.pop()
            self.emit("end", ind)
        elif k == "while_statement":
            c = self.ex(named(n.child_by_field_name("condition"))[0])
            self.emit(f"while {c} do", ind)
            self.scope.push()
            self.block(self.stmts_of(n.child_by_field_name("body")), ind + 1)
            self.scope.pop()
            self.emit("end", ind)
        elif k == "do_statement":
            self.emit("repeat", ind)
            self.block(self.stmts_of(n.child_by_field_name("body")), ind + 1)
            c = self.ex(named(n.child_by_field_name("condition"))[0])
            self.emit(f"until not ({c})", ind)
        elif k == "return_statement":
            v = named(n)
            self.emit("return" + (" " + self.ex(v[0]) if v else ""), ind)
        elif k == "break_statement":
            self.emit("break", ind)
        elif k == "continue_statement":
            self.emit("goto continue", ind)
        elif k == "block":
            self.emit("do", ind)
            self.scope.push()
            self.block(self.stmts_of(n), ind + 1)
            self.scope.pop()
            self.emit("end", ind)
        elif k == "class_declaration":
            self.class_decl(n, ind)
        elif k == "method_declaration":
            self.func(n, ind)
        elif k == "field_declaration":
            self.field_decl(n, ind)
        else:
            self.emit(f"--[[TODO {k}]] " + self.t(n).replace("\n", " "), ind)

    def expr_stmt(self, e, ind):
        if e.type == "update_expression":
            txt = self.t(e)
            op = "+" if "++" in txt else "-"
            target = [c for c in e.children if c.is_named][0]
            v = self.ex(target)
            self.emit(f"{v} = {v} {op} 1", ind)
        elif e.type == "assignment_expression":
            L, R = e.child_by_field_name("left"), e.child_by_field_name("right")
            op = self.t(e.child_by_field_name("operator"))
            lt = self.ty(L)
            l = self.ex(L)
            if op == "=" and R.type == "assignment_expression":
                # a = b = v
                inner = R.child_by_field_name("left")
                v = self.ex(R.child_by_field_name("right"))
                self.emit(f"{self.ex(inner)} = {v}", ind)
                self.emit(f"{l} = {self.ex(inner)}", ind)
            elif op == "=":
                self.emit(f"{l} = {self.ex(R, intlike(lt))}", ind)
            else:
                o = op[:-1]
                rt = self.ty(R)
                r = self.ex(R, intlike(lt))
                if R.type in ("binary_expression", "ternary_expression"):
                    r = f"({r})"
                if o == "+" and lt == "String":
                    o = ".."
                elif o == "/" and intlike(lt) and intlike(rt):
                    o = "//"
                o = {"^": "~", ">>>": ">>"}.get(o, o)
                self.emit(f"{l} = {l} {o} {r}", ind)
        else:
            self.emit(self.ex(e), ind)

    def if_stmt(self, n, ind, kw):
        c = self.ex(named(n.child_by_field_name("condition"))[0])
        self.emit(f"{kw} {c} then", ind)
        self.scope.push()
        self.block(self.stmts_of(n.child_by_field_name("consequence")), ind + 1)
        self.scope.pop()
        alt = n.child_by_field_name("alternative")
        if alt is not None:
            if alt.type == "if_statement":
                self.if_stmt(alt, ind, "elseif")
            else:
                self.emit("else", ind)
                self.scope.push()
                self.block(self.stmts_of(alt), ind + 1)
                self.scope.pop()

    def uses_only_as_index(self, body, var):
        ok = True
        st = [body]
        while st:
            x = st.pop()
            if x.type == "identifier" and self.t(x) == var:
                p = x.parent
                if not (p.type == "array_access" and p.child_by_field_name("index") == x):
                    if not (p.type == "argument_list" and p.parent.type == "method_invocation"
                            and self.t(p.parent.child_by_field_name("name")) in ("get",)
                            and p.parent.child_by_field_name("object") is not None
                            and base_type(self.ty(p.parent.child_by_field_name("object"))) == "ArrayList"):
                        ok = False
                else:
                    arr = self.t(p.child_by_field_name("array"))
                    if arr == "pixels" or arr.endswith(".pixels"):
                        ok = False
            if x.type in ("assignment_expression", "update_expression"):
                tgt = x.child_by_field_name("left") if x.type == "assignment_expression" else named(x)[0]
                if tgt is not None and self.t(tgt) == var:
                    return False
            st.extend(x.children)
        return ok

    def has_continue(self, body):
        st = [body]
        while st:
            x = st.pop()
            if x.type == "continue_statement":
                return True
            if x.type in ("for_statement", "while_statement", "enhanced_for_statement", "do_statement"):
                continue
            st.extend(x.children)
        return False

    def for_stmt(self, n, ind):
        init = n.child_by_field_name("init")
        cond = n.child_by_field_name("condition")
        upd = n.child_by_field_name("update")
        body = n.child_by_field_name("body")
        self.scope.push()
        simple = None
        if init is not None and init.type == "local_variable_declaration" and cond is not None and upd is not None:
            decls = init.children_by_field_name("declarator")
            if len(decls) == 1:
                var = self.t(decls[0].child_by_field_name("name"))
                start = decls[0].child_by_field_name("value")
                self.scope.add(var, self.decl_type(init, decls[0]))
                if cond.type == "binary_expression" and self.t(cond.child_by_field_name("left")) == var:
                    op = self.t(cond.child_by_field_name("operator"))
                    lim = cond.child_by_field_name("right")
                    ut = self.t(upd).replace(" ", "")
                    step = None
                    if ut in (var + "++", "++" + var):
                        step = "1"
                    elif ut in (var + "--", "--" + var):
                        step = "-1"
                    else:
                        m = re.fullmatch(re.escape(var) + r"(\+|-)=(.+)", ut)
                        if m:
                            step = ("-" if m.group(1) == "-" else "") + self.ex(upd.child_by_field_name("right"))
                    mutated = not self.uses_only_as_index(body, var) and self.mutates(body, var)
                    if step and not mutated:
                        simple = (var, start, op, lim, step)
        if simple:
            var, start, op, lim, step = simple
            s = self.ex(start, True)
            l = self.ex(lim, True)
            if op == "<" and step == "1":
                e = self.minus1(l)
            elif op == "<=" or op == ">=":
                e = l
            elif op == ">" and step == "-1":
                e = self.plus1(l)
            elif op == "<":
                e = f"{l} - 1"
            elif op == ">":
                e = f"{l} + 1"
            else:
                e = None
            if e is not None:
                shift = s == "0" and step == "1" and op == "<" and self.uses_only_as_index(body, var)
                if shift:
                    self.loopvars.append(var)
                    s, e = "1", l
                st = "" if step == "1" else f", {step}"
                self.emit(f"for {var} = {s}, {e}{st} do", ind)
                self.loop_body(body, ind)
                if shift:
                    self.loopvars.pop()
                self.emit("end", ind)
                self.scope.pop()
                return
        # general form
        self.emit("do", ind)
        if init is not None:
            self.stmt(init, ind + 1) if init.type == "local_variable_declaration" else self.expr_stmt(init, ind + 1)
        c = self.ex(cond) if cond is not None else "true"
        self.emit(f"while {c} do", ind + 1)
        self.loop_body(body, ind + 1, tail=upd)
        self.emit("end", ind + 1)
        self.emit("end", ind)
        self.scope.pop()

    def mutates(self, body, var):
        st = [body]
        while st:
            x = st.pop()
            if x.type in ("assignment_expression", "update_expression"):
                tgt = x.child_by_field_name("left") if x.type == "assignment_expression" else named(x)[0]
                if tgt is not None and self.t(tgt) == var:
                    return True
            st.extend(x.children)
        return False

    def minus1(self, l):
        m = re.fullmatch(r"(.*) \+ 1", l)
        if m:
            return m.group(1)
        if re.fullmatch(r"\d+", l):
            return str(int(l) - 1)
        if l.startswith("#") or re.fullmatch(r"[\w.]+", l):
            return f"{l} - 1"
        return f"{l} - 1"

    def plus1(self, l):
        m = re.fullmatch(r"(.*) - 1", l)
        if m:
            return m.group(1)
        if re.fullmatch(r"-?\d+", l):
            return str(int(l) + 1)
        return f"{l} + 1"

    def loop_body(self, body, ind, tail=None):
        cont = self.has_continue(body)
        self.scope.push()
        self.block(self.stmts_of(body), ind + 1)
        self.scope.pop()
        if cont:
            self.emit("::continue::", ind + 1)
        if tail is not None:
            self.expr_stmt(tail, ind + 1)

    def params(self, n):
        ps = []
        for p in named(n.child_by_field_name("parameters")):
            if p.type == "formal_parameter":
                name = self.t(p.child_by_field_name("name"))
                self.scope.add(name, self.decl_type(p, p))
                ps.append(safe(name))
        return ps

    def func(self, n, ind):
        name = self.t(n.child_by_field_name("name"))
        self.scope.push()
        ps = self.params(n)
        if self.cls:
            self.emit(f"function {self.cls.name}:{safe(name)}({', '.join(ps)})", ind)
        else:
            self.emit(f"function {name}({', '.join(ps)})", ind)
        body = n.child_by_field_name("body")
        self.block(self.stmts_of(body), ind + 1)
        self.scope.pop()
        self.emit("end", ind)

    def default(self, t):
        if t == "boolean":
            return "false"
        if numeric(t):
            return "0"
        if t == "String":
            return "nil"
        return None

    def field_decl(self, n, ind, deferred=()):
        names, vals = [], []
        for d in n.children_by_field_name("declarator"):
            name = safe(self.t(d.child_by_field_name("name")))
            t = self.decl_type(n, d)
            self.scope.add(name, t)
            v = d.child_by_field_name("value")
            names.append(name)
            if v is not None:
                vals.append(self.ex(v, intlike(t)))
            else:
                vals.append(self.default(t))
        if len(names) > 1 and len(set(vals)) == 1 and vals[0] is not None:
            self.emit(f"local {', '.join(names)} = {', '.join(vals)}", ind)
            return
        for name, v in zip(names, vals):
            self.emit(f"local {name}" + (f" = {v}" if v is not None else ""), ind)

    # ── classes ───────────────────────────────────────────────────────────
    def class_decl(self, n, ind):
        ci = self.classes[self.t(n.child_by_field_name("name"))]
        prev = self.cls
        self.cls = ci
        name = ci.name
        if ci.base:
            self.emit(f"{name} = setmetatable({{}}, {{ __index = {ci.base} }})", ind)
        else:
            self.emit(f"{name} = {{}}", ind)
        self.emit(f"{name}.__index = {name}", ind)
        body = n.child_by_field_name("body")
        members = [c for c in body.children if c.is_named or is_comment(c)]
        inits = [m for m in members if m.type == "field_declaration"]
        pending = []
        for m in members:
            if m.type == "field_declaration":
                continue
            if is_comment(m):
                pending.append(m)
                continue
            self.emit("", ind)
            for c in pending:
                for l in self.comment(c, ind).split("\n"):
                    self.emit(l, ind)
            pending = []
            if m.type == "constructor_declaration":
                self.ctor(m, inits, ind)
            elif m.type == "method_declaration":
                self.func(m, ind)
            elif m.type == "class_declaration":
                self.cls = prev
                self.class_decl(m, ind)
                self.cls = ci
        if not ci.ctors:
            self.emit("", ind)
            self.ctor(None, inits, ind)
        self.cls = prev

    def ctor(self, m, inits, ind):
        ci = self.cls
        self.scope.push()
        ps = self.params(m) if m is not None else []
        self.emit(f"function {ci.name}.new({', '.join(ps)})", ind)
        stmts = self.stmts_of(m.child_by_field_name("body")) if m is not None else []
        first = [s for s in stmts if not is_comment(s)]
        sup = None
        if first and first[0].type == "explicit_constructor_invocation":
            sup = first[0]
            stmts = [s for s in stmts if s != sup]
        if sup is not None:
            a = [self.ex(x) for x in named(sup.child_by_field_name("arguments"))]
            self.emit(f"local self = setmetatable({ci.base}.new({', '.join(a)}), {ci.name})", ind + 1)
        elif ci.base:
            self.emit(f"local self = setmetatable({ci.base}.new(), {ci.name})", ind + 1)
        else:
            self.emit(f"local self = setmetatable({{}}, {ci.name})", ind + 1)
        for f in inits:
            for d in f.children_by_field_name("declarator"):
                v = d.child_by_field_name("value")
                fname = safe(self.t(d.child_by_field_name("name")))
                t = self.decl_type(f, d)
                val = self.ex(v, intlike(t)) if v is not None else self.default(t)
                if val is not None and not (m is not None and self.assigns(m, fname) and v is None):
                    self.emit(f"self.{safe(fname)} = {val}", ind + 1)
        self.block(stmts, ind + 1)
        self.emit("return self", ind + 1)
        self.emit("end", ind)
        self.scope.pop()

    def assigns(self, m, fname):
        return re.search(r"\b(this\.)?" + re.escape(fname) + r"\s*=[^=]", self.t(m)) is not None

    # ── program ───────────────────────────────────────────────────────────
    def run(self):
        kids = self.body_nodes()
        self.collect(kids)
        if self.static:
            # static sketch: everything runs once, which is setup()
            header = []
            while kids and is_comment(kids[0]):
                header.append(kids.pop(0))
            self.block(header, 0)
            self.emit("", 0)
            self.emit("function setup()", 0)
            self.scope.push()
            self.block(kids, 1)
            self.scope.pop()
            self.emit("end", 0)
        else:
            classes = [k for k in kids if k.type == "class_declaration"]
            needs_first = any(re.search(r"\bnew\s+" + re.escape(c) + r"\b", self.t(f))
                              for f in kids if f.type == "field_declaration" for c in self.classes)
            order = kids
            if needs_first:
                # Lua runs top to bottom: a class has to exist before a
                # field is made from it, so classes go right after the fields
                # that don't need them... simplest: classes first, after the header
                header = []
                rest = list(kids)
                while rest and is_comment(rest[0]):
                    header.append(rest.pop(0))
                # comments right above a class belong to it
                cls_with = []
                others = []
                i = 0
                while i < len(rest):
                    j = i
                    while j < len(rest) and is_comment(rest[j]):
                        j += 1
                    if j < len(rest) and rest[j].type == "class_declaration":
                        cls_with.extend(rest[i:j + 1])
                        i = j + 1
                    else:
                        others.append(rest[i])
                        i += 1
                fields = [k for k in others if k.type == "field_declaration"]
                used = set()
                for c in classes:
                    for f in fields:
                        for d in f.children_by_field_name("declarator"):
                            nm = self.t(d.child_by_field_name("name"))
                            if re.search(r"\b" + re.escape(nm) + r"\b", self.t(c)) and not self.field(nm, self.classes[self.t(c.child_by_field_name("name"))]):
                                used.add(nm)
                self.block(header, 0)
                if used:
                    self.emit("", 0)
                    self.emit("local " + ", ".join(sorted(used)) + "  --FWD", 0)
                    self.forward = used
                self.out.append("")
                self.block(cls_with, 0)
                self.out.append("")
                order = others
            self.block(order, 0)
        out = "\n".join(self.out)
        if getattr(self, "forward", None):
            for nm in self.forward:
                out = re.sub(r"^local " + re.escape(nm) + r"\n", "", out, flags=re.M)
                out = re.sub(r"^local " + re.escape(nm) + r"( =|$)", nm + r"\1", out, flags=re.M)
            out = out.replace("  --FWD", "")
        if self.need_array:
            helper = ("-- a table of n values, counted from 1 (rows of tables for more sizes)\n"
                      "local function newArray(n, ...)\n"
                      "  local t = {}\n"
                      "  for i = 1, n do\n"
                      "    if select(\"#\", ...) > 1 then t[i] = newArray(...) else t[i] = (...) end\n"
                      "  end\n"
                      "  return t\n"
                      "end\n")
            lines = out.split("\n")
            i = 0
            if lines and lines[0].startswith("--"):
                if lines[0].startswith("--[["):
                    while i < len(lines) and lines[i].strip() != "]]":
                        i += 1
                    i += 1
                else:
                    while i < len(lines) and lines[i].startswith("--"):
                        i += 1
            out = "\n".join(lines[:i] + ["", helper.rstrip()] + lines[i:])
        out = re.sub(r"\n{3,}", "\n\n", out).strip("\n") + "\n"
        return out


def fix_newarray_dims(src):
    return src


if __name__ == "__main__":
    print(Lua(open(sys.argv[1]).read()).run(), end="")
