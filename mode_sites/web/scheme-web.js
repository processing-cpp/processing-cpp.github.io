// scheme-web.js: runs a Scheme Mode sketch in the browser. The sketch is
// compiled to JavaScript right here (no server, nothing to wait for), with
// Scheme Mode's rules: Processing's names in kebab-case (no-stroke, mouse-x),
// methods with the object first ((add v w), (get img x y)), lists that work
// like Scheme Mode's (vectors underneath, so list-ref is quick), and errors
// that point at the sketch's own line. The drawing is pweb.js.
(function (global) {
  "use strict";

  // ── reading ─────────────────────────────────────────────────────────────
  class Sym { constructor(n, line) { this.n = n; this.line = line; } }
  class Char { constructor(c) { this.c = c; } toString() { return this.c; } }
  class Pair { constructor(a, d) { this.car = a; this.cdr = d; } }   // only for dotted pairs
  const LIST = Symbol("list");
  function mk(items, line) { items[LIST] = true; items.line = line; return items; }
  const isList = (x) => Array.isArray(x) && x[LIST];
  const isSym = (x, n) => x instanceof Sym && (n === undefined || x.n === n);

  function read(src) {
    let i = 0, line = 1;
    const out = [];
    const err = (m) => { const e = new Error(m); e.schemeLine = line; throw e; };
    function skip() {
      for (;;) {
        const c = src[i];
        if (c === "\n") { line++; i++; }
        else if (c === " " || c === "\t" || c === "\r" || c === "\f") i++;
        else if (c === ";") { while (i < src.length && src[i] !== "\n") i++; }
        else if (c === "#" && src[i + 1] === "|") {
          let depth = 1; i += 2;
          while (i < src.length && depth) {
            if (src[i] === "\n") line++;
            if (src[i] === "|" && src[i + 1] === "#") { depth--; i += 2; }
            else if (src[i] === "#" && src[i + 1] === "|") { depth++; i += 2; }
            else i++;
          }
        } else if (c === "#" && src[i + 1] === ";") { i += 2; datum(); }
        else return;
      }
    }
    const DELIM = /[\s()\[\]";']/;
    function datum() {
      skip();
      if (i >= src.length) err("the code ends in the middle of a form (a missing close paren?)");
      const c = src[i], ln = line;
      if (c === "(" || c === "[") {
        const close = c === "(" ? ")" : "]";
        i++;
        const items = [];
        for (;;) {
          skip();
          if (i >= src.length) { line = ln; err("this ( is never closed"); }
          if (src[i] === close) { i++; return mk(items, ln); }
          if (src[i] === ")" || src[i] === "]") err("a " + src[i] + " that doesn't match");
          if (src[i] === "." && DELIM.test(src[i + 1] || " ")) {
            i++; const tail = datum(); skip();
            if (src[i] !== close) err("expected " + close + " after a dotted pair");
            i++;
            return items.reduceRight((d, a) => new Pair(a, d), tail);
          }
          items.push(datum());
        }
      }
      if (c === ")" || c === "]") err("a " + c + " with no ( before it");
      if (c === "'") { i++; return mk([new Sym("quote", ln), datum()], ln); }
      if (c === "`") { i++; return mk([new Sym("quasiquote", ln), datum()], ln); }
      if (c === ",") {
        i++;
        if (src[i] === "@") { i++; return mk([new Sym("unquote-splicing", ln), datum()], ln); }
        return mk([new Sym("unquote", ln), datum()], ln);
      }
      if (c === '"') {
        i++; let s = "";
        while (i < src.length && src[i] !== '"') {
          if (src[i] === "\\") {
            i++; const e = src[i];
            s += e === "n" ? "\n" : e === "t" ? "\t" : e === "r" ? "\r" : e === "a" ? "\x07" : e === "0" ? "\0" : e;
          } else { if (src[i] === "\n") line++; s += src[i]; }
          i++;
        }
        if (i >= src.length) { line = ln; err("this string is never closed"); }
        i++;
        return { str: s };
      }
      if (c === "#" && src[i + 1] === "(") {
        i++; const v = datum(); return { vec: v };
      }
      if (c === "#" && src[i + 1] === "\\") {
        i += 2; let s = src[i++];
        while (i < src.length && !DELIM.test(src[i])) s += src[i++];
        const named = { space: " ", newline: "\n", tab: "\t", nul: "\0", null: "\0", return: "\r", linefeed: "\n", alarm: "\x07", backspace: "\b", delete: "\x7f", escape: "\x1b" };
        if (s.length > 1 && named[s.toLowerCase()] !== undefined) return new Char(named[s.toLowerCase()]);
        if (s.length > 1 && /^x[0-9a-f]+$/i.test(s)) return new Char(String.fromCodePoint(parseInt(s.slice(1), 16)));
        return new Char(s);
      }
      let s = "";
      while (i < src.length && !DELIM.test(src[i])) s += src[i++];
      if (s === "#t" || s === "#true") return true;
      if (s === "#f" || s === "#false") return false;
      if (/^#x[0-9a-f]+$/i.test(s)) return parseInt(s.slice(2), 16);
      if (/^#b[01]+$/i.test(s)) return parseInt(s.slice(2), 2);
      if (/^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(s)) return parseFloat(s);
      if (/^[+-]?\d+\/\d+$/.test(s)) { const [a, b] = s.split("/"); return +a / +b; }
      return new Sym(s, ln);
    }
    for (;;) { skip(); if (i >= src.length) break; out.push(datum()); }
    return out;
  }

  // ── names ───────────────────────────────────────────────────────────────
  // a Scheme name as a JavaScript identifier
  function jsName(n) {
    return "$" + n.replace(/[^A-Za-z0-9_]/g, (c) => "_" + c.charCodeAt(0).toString(36) + "_");
  }
  const kebab = (n) => n.replace(/([a-z0-9])([A-Z])/g, "$1-$2").replace(/_/g, "-").toLowerCase();

  // ── compiling ───────────────────────────────────────────────────────────
  // Every body is compiled to statements; an expression that needs
  // statements (a loop inside an argument, say) becomes a small function.
  function Compiler(builtins, dynamic, globals) {
    let tmp = 0;
    const fresh = (p) => "$t" + p + (tmp++);
    const line = (f) => (f && f.line) || (f instanceof Sym ? f.line : 0);

    function ref(sym, scope) {
      const n = sym.n;
      if (scope.has(n)) return jsName(n);
      if (globals.has(n)) return "G." + jsName(n);
      if (dynamic.has(n)) return "$D." + jsName(n);
      if (/^[A-Z][A-Z0-9_-]*$/.test(n) && builtins.has(n.replace(/-/g, "_"))) return "R." + n.replace(/-/g, "_");
      if (builtins.has(n)) return "R[" + JSON.stringify(n) + "]";
      // a top-level name of the sketch (defined later in the file, maybe)
      return "G." + jsName(n);
    }

    function quote(x) {
      if (isList(x)) return "[" + x.map(quote).join(",") + "]";
      if (x instanceof Sym) return "R.sym(" + JSON.stringify(x.n) + ")";
      if (x instanceof Char) return "R.ch(" + JSON.stringify(x.c) + ")";
      if (x instanceof Pair) return "R.cons(" + quote(x.car) + "," + quote(x.cdr) + ")";
      if (x && x.str !== undefined) return JSON.stringify(x.str);
      if (x && x.vec) return "[" + x.vec.map(quote).join(",") + "]";
      return JSON.stringify(x);
    }
    function quasi(x, scope, depth) {
      if (!isList(x)) return quote(x);
      if (isSym(x[0], "unquote")) return expr(x[1], scope);
      const parts = [];
      for (const el of x) {
        if (isList(el) && isSym(el[0], "unquote-splicing")) parts.push("..." + expr(el[1], scope));
        else parts.push(quasi(el, scope, depth));
      }
      return "[" + parts.join(",") + "]";
    }

    const truthy = (js) => "((" + js + ")!==false)";

    // expression -> JS expression
    function expr(f, scope) {
      if (typeof f === "number") return Number.isFinite(f) ? (f < 0 ? "(" + f + ")" : String(f)) : f > 0 ? "Infinity" : f < 0 ? "-Infinity" : "NaN";
      if (typeof f === "boolean") return String(f);
      if (f instanceof Char) return "R.ch(" + JSON.stringify(f.c) + ")";
      if (f && f.str !== undefined) return JSON.stringify(f.str);
      if (f && f.vec) return "[" + f.vec.map((e) => quote(e)).join(",") + "]";
      if (f instanceof Sym) return ref(f, scope);
      if (!isList(f)) return "undefined";
      if (f.length === 0) return "[]";
      const h = f[0];
      if (h instanceof Sym && !scope.has(h.n)) {
        switch (h.n) {
          case "quote": return quote(f[1]);
          case "quasiquote": return quasi(f[1], scope, 1);
          case "if": return "(" + truthy(expr(f[1], scope)) + "?" + expr(f[2], scope) + ":" + (f.length > 3 ? expr(f[3], scope) : "undefined") + ")";
          case "and": return f.length === 1 ? "true" : "R.and_(" + f.slice(1).map((x) => "()=>" + expr(x, scope)).join(",") + ")";
          case "or": return f.length === 1 ? "false" : "R.or_(" + f.slice(1).map((x) => "()=>" + expr(x, scope)).join(",") + ")";
          case "not": return "(" + expr(f[1], scope) + "===false)";
          case "lambda": return lambda(f[1], f.slice(2), scope, null);
          case "set!": return "(" + assign(f[1], expr(f[2], scope), scope) + ",undefined)";
          case "begin": if (f.length === 2) return expr(f[1], scope); break;
          case "+": if (f.length === 3) return "(" + expr(f[1], scope) + "+" + expr(f[2], scope) + ")"; break;
          case "-": if (f.length === 3) return "(" + expr(f[1], scope) + "-" + expr(f[2], scope) + ")";
                    if (f.length === 2) return "(-" + expr(f[1], scope) + ")"; break;
          case "*": if (f.length === 3) return "(" + expr(f[1], scope) + "*" + expr(f[2], scope) + ")"; break;
          case "<": case ">": case "<=": case ">=":
            if (f.length === 3) return "(" + expr(f[1], scope) + h.n + expr(f[2], scope) + ")"; break;
          case "=": if (f.length === 3) return "(" + expr(f[1], scope) + "==" + expr(f[2], scope) + ")"; break;
          case "vector-ref": if (f.length === 3) return "R.vref(" + expr(f[1], scope) + "," + expr(f[2], scope) + ")"; break;
          case "vector-set!": if (f.length === 4) return "R.vset(" + expr(f[1], scope) + "," + expr(f[2], scope) + "," + expr(f[3], scope) + ")"; break;
        }
        if (STMT_FORMS.has(h.n)) return "(()=>{" + body([f], scope, true) + "})()";
      }
      // (width img): a value that is also a procedure is called as the procedure
      const fn = h instanceof Sym && !scope.has(h.n) && !globals.has(h.n) && dynamic.has(h.n) && builtins.has(h.n)
        ? "R[" + JSON.stringify(h.n) + "]" : expr(h, scope);
      return fn + "(" + f.slice(1).map((a) => expr(a, scope)).join(",") + ")";
    }
    const STMT_FORMS = new Set(["define", "begin", "let", "let*", "letrec", "letrec*", "do", "cond", "case", "when", "unless",
      "define-record-type", "let-values", "let*-values", "define-values", "guard", "with-matrix", "call-with-current-continuation", "call/cc"]);

    function assign(target, val, scope) {
      if (!(target instanceof Sym)) throw at(target, "set! needs a variable name");
      return ref(target, scope) + "=" + val;
    }
    function at(f, msg) { const e = new Error(msg); e.schemeLine = line(f); return e; }

    function params(ps, scope) {
      const names = [];
      let rest = null;
      if (ps instanceof Sym) rest = ps.n;
      else if (ps instanceof Pair) {
        let p = ps;
        while (p instanceof Pair) { names.push(p.car.n); p = p.cdr; }
        rest = p.n;
      } else if (isList(ps)) for (const p of ps) names.push(p.n);
      const inner = new Set(scope);
      names.forEach((n) => inner.add(n));
      if (rest) inner.add(rest);
      return { js: names.map(jsName).concat(rest ? ["..." + jsName(rest)] : []).join(","), inner, names, rest };
    }
    function lambda(ps, forms, scope, selfName) {
      const p = params(ps, scope);
      return "((" + p.js + ")=>{" + body(forms, p.inner, true, selfName ? { name: selfName, params: p.names, rest: p.rest } : null) + "})";
    }

    // body: a list of forms -> statements; tail: the last value is returned
    function body(forms, scope, tail, self) {
      if (forms.length === 0) return tail ? "return undefined;" : "";
      // defines anywhere in a body belong to the whole body (as in Scheme Mode)
      const local = new Set(scope);
      const decl = [];
      for (const f of forms) collectDefines(f, local, decl);
      let out = decl.length ? "var " + [...new Set(decl)].map(jsName).join(",") + ";" : "";
      forms.forEach((f, k) => { out += stmt(f, local, tail && k === forms.length - 1, self); });
      return out;
    }
    function collectDefines(f, scope, decl) {
      if (!isList(f) || !(f[0] instanceof Sym)) return;
      const n = f[0].n;
      if (n === "define") {
        const t = f[1];
        const name = isList(t) ? t[0].n : t instanceof Pair ? t.car.n : t.n;
        scope.add(name); decl.push(name);
      } else if (n === "define-values") {
        for (const s of (isList(f[1]) ? f[1] : [])) { scope.add(s.n); decl.push(s.n); }
      } else if (n === "define-record-type") {
        const tn = f[1] instanceof Sym ? f[1].n : f[1][0].n;
        const names = [];
        if (isList(f[2])) names.push(f[2][0].n); else if (f[2] instanceof Sym) names.push(f[2].n);
        names.push(f[3].n);
        for (const fd of f.slice(4)) { if (isList(fd)) fd.slice(1).forEach((s) => names.push(s.n)); }
        names.push(tn);
        names.forEach((x) => { scope.add(x); decl.push(x); });
      } else if (n === "begin") f.slice(1).forEach((x) => collectDefines(x, scope, decl));
      // defines inside when/do/cond bodies are local to the enclosing function in Scheme Mode
      else if (["when", "unless", "do", "cond", "case", "if"].includes(n)) {
        const walk = (g) => { if (isList(g)) { if (isSym(g[0], "define")) collectDefines(g, scope, decl); else if (!isSym(g[0], "lambda") && !isSym(g[0], "let") && !isSym(g[0], "define-record-type")) g.forEach(walk); } };
        f.slice(1).forEach(walk);
      }
    }

    function stmt(f, scope, tail, self) {
      const ln = line(f);
      const mark = ln ? "$L=" + ln + ";" : "";
      const ret = (js) => (tail ? "return " + js + ";" : js + ";");
      if (!isList(f) || f.length === 0 || !(f[0] instanceof Sym) || scope.has(f[0].n) && !["define"].includes(f[0].n)) {
        // a self tail call in a loop function: jump instead of recursing
        if (tail && self && isList(f) && isSym(f[0], self.name) && !self.rest && f.length - 1 === self.params.length) {
          const tmps = self.params.map(() => fresh("a"));
          return mark + "{const " + tmps.map((t, k) => t + "=" + expr(f[k + 1], scope)).join(",") + ";" +
            self.params.map((p, k) => jsName(p) + "=" + tmps[k] + ";").join("") + "continue $self;}";
        }
        return mark + ret(expr(f, scope));
      }
      const h = f[0].n;
      switch (h) {
        case "define": {
          const t = f[1];
          if (isList(t) || t instanceof Pair) {
            const name = isList(t) ? t[0] : t.car;
            const ps = isList(t) ? mk(t.slice(1), t.line) : t.cdr;
            return mark + jsName(name.n) + "=" + fnWithLoop(name.n, ps, f.slice(2), scope) + ";" + (tail ? "return undefined;" : "");
          }
          return mark + jsName(t.n) + "=" + (f.length > 2 ? expr(f[2], scope) : "undefined") + ";" + (tail ? "return undefined;" : "");
        }
        case "begin": return f.length === 1 ? (tail ? "return undefined;" : "") : f.slice(1).map((g, k) => stmt(g, scope, tail && k === f.length - 2, self)).join("");
        case "if": {
          let s = mark + "if" + truthy(expr(f[1], scope)) + "{" + stmt(f[2], scope, tail, self) + "}";
          if (f.length > 3) s += "else{" + stmt(f[3], scope, tail, self) + "}";
          else if (tail) s += "else return undefined;";
          return s;
        }
        case "when": case "unless": {
          const c = expr(f[1], scope);
          return mark + "if(" + (h === "when" ? truthy(c) : "(" + c + ")===false") + "){" + seq(f.slice(2), scope, tail, self) + "}" + (tail ? "else return undefined;" : "");
        }
        case "cond": {
          let s = mark, first = true;
          for (const cl of f.slice(1)) {
            if (isSym(cl[0], "else")) { s += (first ? "{" : "else{") + seq(cl.slice(1), scope, tail, self) + "}"; first = false; continue; }
            if (cl.length >= 3 && isSym(cl[1], "=>")) {
              const tv = fresh("c");
              s += (first ? "" : "else ") + "{const " + tv + "=" + expr(cl[0], scope) + ";if(" + tv + "!==false){" + ret(expr(cl[2], scope) + "(" + tv + ")") + "}" ;
              s += "}"; first = false; continue;
            }
            if (cl.length === 1) {
              const tv = fresh("c");
              s += (first ? "" : "else ") + "if((" + tv + "=" + expr(cl[0], scope) + ")!==false){" + ret(tv) + "}";
              s = "var " + tv + ";" + s;
            } else s += (first ? "" : "else ") + "if" + truthy(expr(cl[0], scope)) + "{" + seq(cl.slice(1), scope, tail, self) + "}";
            first = false;
          }
          if (tail && !f.slice(1).some((cl) => isSym(cl[0], "else"))) s += (f.length > 1 ? "else " : "") + "return undefined;";
          return s;
        }
        case "case": {
          const k = fresh("k");
          let s = mark + "{const " + k + "=" + expr(f[1], scope) + ";";
          let first = true, hasElse = false;
          for (const cl of f.slice(2)) {
            if (isSym(cl[0], "else")) { s += (first ? "{" : "else{") + seq(cl.slice(1), scope, tail, self) + "}"; hasElse = true; first = false; continue; }
            const tests = (isList(cl[0]) ? cl[0] : [cl[0]]).map((d) => "R.eqv(" + k + "," + quote(d) + ")").join("||");
            s += (first ? "" : "else ") + "if(" + (tests || "false") + "){" + seq(cl.slice(1), scope, tail, self) + "}";
            first = false;
          }
          if (tail && !hasElse) s += (first ? "" : "else ") + "return undefined;";
          return s + "}";
        }
        case "let": {
          if (f[1] instanceof Sym) return mark + namedLet(f, scope, tail);
          const inner = new Set(scope);
          let s = "{";
          const binds = isList(f[1]) ? f[1] : [];
          const vals = binds.map((b) => expr(b[1], scope));
          binds.forEach((b, k) => { inner.add(b[0].n); s += "let " + jsName(b[0].n) + "=" + vals[k] + ";"; });
          return mark + s + seqBody(f.slice(2), inner, tail, self) + "}";
        }
        case "let*": case "letrec": case "letrec*": {
          const inner = new Set(scope);
          let s = "{";
          const binds = isList(f[1]) ? f[1] : [];
          if (h !== "let*") binds.forEach((b) => inner.add(b[0].n));
          for (const b of binds) {
            if (h === "let*") { const v = expr(b[1], inner); inner.add(b[0].n); s += "let " + jsName(b[0].n) + "=" + v + ";"; }
            else s += "var " + jsName(b[0].n) + ";";
          }
          if (h !== "let*") for (const b of binds) s += jsName(b[0].n) + "=" + expr(b[1], inner) + ";";
          return mark + s + seqBody(f.slice(2), inner, tail, self) + "}";
        }
        case "do": {
          // (do ((var init step) ...) (test result...) body...)
          const inner = new Set(scope);
          const specs = isList(f[1]) ? f[1] : [];
          let s = "{";
          const inits = specs.map((sp) => expr(sp[1], scope));
          specs.forEach((sp, k) => { inner.add(sp[0].n); s += "let " + jsName(sp[0].n) + "=" + inits[k] + ";"; });
          const test = f[2];
          s += "for(;;){if" + truthy(expr(test[0], inner)) + "{" + (test.length > 1 ? seq(test.slice(1), inner, tail, null) : tail ? "return undefined;" : "") + "break;}";
          s += body(f.slice(3), inner, false, null);
          const steps = specs.filter((sp) => sp.length > 2);
          if (steps.length === 1) s += jsName(steps[0][0].n) + "=" + expr(steps[0][2], inner) + ";";
          else if (steps.length > 1) {
            const tmps = steps.map(() => fresh("s"));
            s += "{const " + steps.map((sp, k) => tmps[k] + "=" + expr(sp[2], inner)).join(",") + ";" + steps.map((sp, k) => jsName(sp[0].n) + "=" + tmps[k] + ";").join("") + "}";
          }
          return mark + s + "}}";
        }
        case "define-record-type": return mark + record(f, scope) + (tail ? "return undefined;" : "");
        case "define-values": {
          const tv = fresh("v");
          return mark + "{const " + tv + "=R.vals(" + expr(f[2], scope) + ");" + f[1].map((s2, k) => jsName(s2.n) + "=" + tv + "[" + k + "];").join("") + "}" + (tail ? "return undefined;" : "");
        }
        case "let-values": case "let*-values": {
          const inner = new Set(scope);
          let s = "{";
          for (const b of f[1]) {
            const tv = fresh("v");
            s += "const " + tv + "=R.vals(" + expr(b[1], inner) + ");";
            b[0].forEach((s2, k) => { inner.add(s2.n); s += "let " + jsName(s2.n) + "=" + tv + "[" + k + "];"; });
          }
          return mark + s + seqBody(f.slice(2), inner, tail, self) + "}";
        }
        case "guard": {
          // (guard (e clause...) body...)
          const v = f[1][0].n, inner = new Set(scope); inner.add(v);
          const r = fresh("g");
          return mark + "{let " + r + ";try{" + r + "=(()=>{" + body(f.slice(2), scope, true) + "})();}catch(" + jsName(v) + "){if(" + jsName(v) + " instanceof R.Escape)throw " + jsName(v) + ";" + jsName(v) + "=R.condition(" + jsName(v) + ");" + r + "=(()=>{" +
            stmt(mk([new Sym("cond", f.line)].concat(f[1].slice(1)).concat(f[1].slice(1).some((c) => isSym(c[0], "else")) ? [] : [mk([new Sym("else"), mk([new Sym("raise"), new Sym(v)])])]), f.line), inner, true, null) + "})();}" + ret(r) + "}";
        }
        case "with-matrix": return mark + "R.push_matrix();try{" + seq(f.slice(1), scope, tail, self) + "}finally{R.pop_matrix();}";
        case "call-with-current-continuation": case "call/cc": {
          const k = fresh("k");
          return mark + "{const " + k + "=new R.Escape();try{" + ret(expr(f[1], scope) + "(" + k + ".fn)") + "}catch(e){if(e!==" + k + ")throw e;" + ret(k + ".value") + "}}";
        }
      }
      return mark + ret(expr(f, scope));
    }
    function seq(forms, scope, tail, self) {
      if (forms.length === 0) return tail ? "return undefined;" : "";
      return forms.map((g, k) => stmt(g, scope, tail && k === forms.length - 1, self)).join("");
    }
    function seqBody(forms, scope, tail, self) {
      const local = new Set(scope), decl = [];
      for (const f of forms) collectDefines(f, local, decl);
      return (decl.length ? "var " + [...new Set(decl)].map(jsName).join(",") + ";" : "") + seq(forms, local, tail, self);
    }
    // a function whose tail calls to itself become a loop
    function fnWithLoop(name, ps, forms, scope) {
      const p = params(ps, scope);
      const inner = new Set(p.inner);
      const self = { name, params: p.names, rest: p.rest };
      const code = body(forms, inner, true, inner.has(name) ? null : self);
      if (!code.includes("continue $self")) return "((" + p.js + ")=>{" + code + "})";
      return "((" + p.js + ")=>{$self:for(;;){" + code + "}})";
    }
    function namedLet(f, scope, tail) {
      const name = f[1].n, binds = isList(f[2]) ? f[2] : [];
      const inner = new Set(scope); inner.add(name);
      const ps = mk(binds.map((b) => b[0]), f.line);
      const fn = fnWithLoop(name, ps, f.slice(3), inner);
      const call = jsName(name) + "(" + binds.map((b) => expr(b[1], scope)).join(",") + ")";
      return "{let " + jsName(name) + "=" + fn + ";" + (tail ? "return " + call + ";" : call + ";") + "}";
    }
    function record(f, scope) {
      const tn = f[1] instanceof Sym ? f[1].n : f[1][0].n;
      const fields = f.slice(4).map((fd) => (isList(fd) ? fd[0].n : fd.n));
      const cls = jsName(tn);
      let s = cls + "=R.recordType(" + JSON.stringify(tn) + "," + JSON.stringify(fields) + ");";
      if (isList(f[2])) {
        const ctorFields = f[2].slice(1).map((x) => x.n);
        s += jsName(f[2][0].n) + "=(...a)=>{const o=new " + cls + "();" + ctorFields.map((fn, k) => "o[" + JSON.stringify(fn) + "]=a[" + k + "];").join("") + "return o;};";
      } else if (f[2] instanceof Sym) {
        s += jsName(f[2].n) + "=(...a)=>{const o=new " + cls + "();" + fields.map((fn, k) => "o[" + JSON.stringify(fn) + "]=a[" + k + "];").join("") + "return o;};";
      }
      s += jsName(f[3].n) + "=(x)=>x instanceof " + cls + ";";
      for (const fd of f.slice(4)) {
        if (!isList(fd)) continue;
        const fname = JSON.stringify(fd[0].n);
        if (fd[1]) s += jsName(fd[1].n) + "=(o)=>R.field(o," + cls + "," + fname + "," + JSON.stringify(fd[1].n) + ");";
        if (fd[2]) s += jsName(fd[2].n) + "=(o,v)=>{R.field(o," + cls + "," + fname + "," + JSON.stringify(fd[2].n) + ");o[" + fname + "]=v;};";
      }
      return s;
    }

    // the whole sketch: top-level names live on G, so they can be read
    // before their define runs (as in Scheme Mode, where they are globals)
    this.program = function (forms) {
      const scope = new Set();
      let out = "";
      for (const f of forms) {
        if (isList(f) && isSym(f[0], "import")) continue;
        const ln = line(f);
        out += (ln ? "$L=" + ln + ";" : "") + topStmt(f, scope);
      }
      return out;
    };
    function topStmt(f, scope) {
      if (isList(f) && isSym(f[0], "define")) {
        const t = f[1];
        if (isList(t) || t instanceof Pair) {
          const name = isList(t) ? t[0] : t.car;
          const ps = isList(t) ? mk(t.slice(1), t.line) : t.cdr;
          return "G." + jsName(name.n) + "=" + fnWithLoop(name.n, ps, f.slice(2), scope) + ";";
        }
        return "G." + jsName(t.n) + "=" + (f.length > 2 ? expr(f[2], scope) : "undefined") + ";";
      }
      if (isList(f) && isSym(f[0], "define-record-type")) {
        const local = new Set(), decl = [];
        collectDefines(f, local, decl);
        return "{var " + decl.map(jsName).join(",") + ";" + record(f, scope) + decl.map((d) => "G." + jsName(d) + "=" + jsName(d) + ";").join("") + "}";
      }
      if (isList(f) && isSym(f[0], "define-values")) {
        const tv = fresh("v");
        return "{const " + tv + "=R.vals(" + expr(f[2], scope) + ");" + f[1].map((s2, k) => "G." + jsName(s2.n) + "=" + tv + "[" + k + "];").join("") + "}";
      }
      if (isList(f) && isSym(f[0], "begin")) return f.slice(1).map((g) => topStmt(g, scope)).join("");
      return "(()=>{" + body([f], scope, false) + "})();";
    }
  }

  // ── the runtime: Scheme's procedures and Processing's, kebab-case ───────
  function Runtime(W) {
    const A = W.api, K = global.PWeb.K;
    const R = Object.create(null);
    class Escape { constructor() { this.value = undefined; this.fn = (v) => { this.value = v; throw this; }; } }
    class SchemeError extends Error { constructor(msg, irritants) { super(msg); this.irritants = irritants || []; } }
    R.Escape = Escape;
    const syms = new Map();
    R.sym = (n) => { let s = syms.get(n); if (!s) { s = new Sym(n); syms.set(n, s); } return s; };
    R.ch = (c) => new Char(c);
    R.and_ = (...fs) => { let v = true; for (const f of fs) { v = f(); if (v === false) return false; } return v; };
    R.or_ = (...fs) => { for (const f of fs) { const v = f(); if (v !== false) return v; } return false; };
    R.vals = (v) => (v && v.__values ? v.list : [v]);
    R.condition = (e) => (e instanceof SchemeError ? e : e && e.payload !== undefined ? e.payload : e);
    const err = (m) => { throw new SchemeError(m); };
    const str = (x) => (x instanceof Char ? x.c : x);
    const num = (x, who) => { if (typeof x !== "number") err(who + ": expected a number, got " + show(x)); return x; };
    R.vref = (v, i) => {
      if (!Array.isArray(v) && !ArrayBuffer.isView(v)) err("vector-ref: not a vector: " + show(v));
      if (!(i >= 0 && i < v.length)) err("vector-ref: index " + i + " out of range for a vector of length " + v.length);
      return v[i | 0];
    };
    R.vset = (v, i, x) => {
      if (!Array.isArray(v) && !ArrayBuffer.isView(v)) err("vector-set!: not a vector: " + show(v));
      if (!(i >= 0 && i < v.length)) err("vector-set!: index " + i + " out of range for a vector of length " + v.length);
      v[i | 0] = x;
    };
    R.recordType = (name, fields) => {
      const C = function () {};
      Object.defineProperty(C, "name", { value: name });
      C.prototype.toString = function () { return "#<" + name + ">"; };
      C.fields = fields;
      return C;
    };
    // a record of another type that has the same field (a "subclass") works too, as in Scheme Mode
    R.field = (o, C, f, who) => { if (!(o instanceof C) && !(o && typeof o === "object" && f in o)) err(who + ": expected a " + C.name + ", got " + show(o)); return o[f]; };

    // printing, as Scheme Mode's println does
    function show(x, write) {
      if (x === true) return "#t";
      if (x === false) return "#f";
      if (x === undefined || x === null) return "";
      if (typeof x === "number") return Number.isInteger(x) ? String(x) : String(x);
      if (typeof x === "string") return write ? JSON.stringify(x) : x;
      if (x instanceof Char) return write ? "#\\" + (x.c === " " ? "space" : x.c === "\n" ? "newline" : x.c) : x.c;
      if (x instanceof Sym) return x.n;
      if (Array.isArray(x)) return "(" + x.map((y) => show(y, true)).join(" ") + ")";
      if (x instanceof Pair) return "(" + show(x.car, true) + " . " + show(x.cdr, true) + ")";
      if (x instanceof Map) return "#<hash-table>";
      if (typeof x === "function") return "#<procedure>";
      if (x instanceof Vec) return "[ " + x.x + ", " + x.y + ", " + x.z + " ]";
      return String(x);
    }
    R.show = show;

    // ── Scheme ──
    const def = (names, fn) => names.split(" ").forEach((n) => { R[n] = fn; });
    def("+", (...a) => a.reduce((s, x) => s + num(x, "+"), 0));
    def("-", (a, ...b) => (b.length ? b.reduce((s, x) => s - num(x, "-"), num(a, "-")) : -num(a, "-")));
    def("*", (...a) => a.reduce((s, x) => s * num(x, "*"), 1));
    def("/", (a, ...b) => (b.length ? b.reduce((s, x) => s / num(x, "/"), num(a, "/")) : 1 / num(a, "/")));
    const chain = (op) => (...a) => { for (let i = 0; i + 1 < a.length; i++) if (!op(a[i], a[i + 1])) return false; return true; };
    def("=", chain((a, b) => a == b)); def("<", chain((a, b) => a < b)); def(">", chain((a, b) => a > b));
    def("<=", chain((a, b) => a <= b)); def(">=", chain((a, b) => a >= b));
    R.quotient = (a, b) => Math.trunc(a / b);
    R.remainder = (a, b) => a % b;
    R.modulo = (a, b) => { const m = a % b; return m !== 0 && (m < 0) !== (b < 0) ? m + b : m; };
    def("floor-quotient", (a, b) => Math.floor(a / b));
    def("floor-remainder", R.modulo); def("truncate-quotient", R.quotient); def("truncate-remainder", R.remainder);
    R.floor = Math.floor; R.ceiling = Math.ceil; R.truncate = Math.trunc;
    R.round = (x) => { const r = Math.round(x); return Math.abs(x % 1) === 0.5 ? (r % 2 === 0 ? r : r - 1) : r; };
    R.expt = (a, b) => Math.pow(a, b); R.exp = Math.exp;
    R.log = (x, b) => (b === undefined ? Math.log(x) : Math.log(x) / Math.log(b));
    R.sqrt = Math.sqrt; R["exact-integer-sqrt"] = (x) => Math.floor(Math.sqrt(x)); R.square = (x) => x * x;
    R.sin = Math.sin; R.cos = Math.cos; R.tan = Math.tan; R.asin = Math.asin; R.acos = Math.acos;
    R.atan = (y, x) => (x === undefined ? Math.atan(y) : Math.atan2(y, x));
    R.atan2 = Math.atan2;
    R.exact = (x) => Math.round(x); R.inexact = (x) => +x; R["exact->inexact"] = R.inexact; R["inexact->exact"] = R.exact;
    R.gcd = (...a) => a.reduce((x, y) => { x = Math.abs(x); y = Math.abs(y); while (y) [x, y] = [y, x % y]; return x; }, 0);
    R.lcm = (...a) => a.reduce((x, y) => (x * y === 0 ? 0 : Math.abs(x * y) / R.gcd(x, y)), 1);
    def("number? real? rational? complex?", (x) => typeof x === "number");
    def("integer? exact-integer?", (x) => typeof x === "number" && Number.isInteger(x));
    def("exact? ", (x) => Number.isInteger(x)); R["inexact?"] = (x) => !Number.isInteger(x);
    def("zero?", (x) => x === 0); def("positive?", (x) => x > 0); def("negative?", (x) => x < 0);
    def("odd?", (x) => Math.abs(x % 2) === 1); def("even?", (x) => x % 2 === 0);
    def("nan?", (x) => Number.isNaN(x));
    R["number->string"] = (x, radix) => (radix ? x.toString(radix) : show(x));
    R["string->number"] = (s, radix) => { const v = radix ? parseInt(s, radix) : Number(s); return Number.isNaN(v) || String(s).trim() === "" ? false : v; };
    R.not = (x) => x === false;
    const eqv = (a, b) => {
      if (a === b) return true;
      if (a instanceof Char || b instanceof Char) return str(a) === str(b);
      if (typeof a === "number" && typeof b === "number") return a === b;
      return false;
    };
    R.eqv = eqv;
    const equal = (a, b) => {
      if (eqv(a, b)) return true;
      if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((x, i) => equal(x, b[i]));
      if (a instanceof Pair && b instanceof Pair) return equal(a.car, b.car) && equal(a.cdr, b.cdr);
      if (typeof a === "string" && typeof b === "string") return a === b;
      return false;
    };
    def("eq? eqv?", eqv); R["equal?"] = equal;
    def("boolean?", (x) => typeof x === "boolean"); def("procedure?", (x) => typeof x === "function");
    def("symbol?", (x) => x instanceof Sym); def("string?", (x) => typeof x === "string"); def("char?", (x) => x instanceof Char);
    def("vector?", (x) => Array.isArray(x)); def("list?", (x) => Array.isArray(x));
    def("pair?", (x) => (Array.isArray(x) && x.length > 0) || x instanceof Pair);
    def("null?", (x) => Array.isArray(x) && x.length === 0);
    R["symbol->string"] = (s) => s.n; R["string->symbol"] = (s) => R.sym(s);
    R.boolean = (x) => (typeof x === "string" ? x.toLowerCase() === "true" : typeof x === "number" ? x !== 0 : x !== false);

    // lists (vectors underneath, as in Scheme Mode)
    R.cons = (a, d) => (Array.isArray(d) ? [a].concat(d) : new Pair(a, d));
    R.car = (x) => { if (x instanceof Pair) return x.car; if (!Array.isArray(x) || !x.length) err("car: expected a non-empty list, got " + show(x)); return x[0]; };
    R.cdr = (x) => { if (x instanceof Pair) return x.cdr; if (!Array.isArray(x) || !x.length) err("cdr: expected a non-empty list, got " + show(x)); return x.slice(1); };
    R.first = R.car; R.rest = R.cdr;
    R.cadr = (x) => R.car(R.cdr(x)); R.cddr = (x) => R.cdr(R.cdr(x)); R.caddr = (x) => R.car(R.cddr(x)); R.cdddr = (x) => R.cdr(R.cddr(x));
    R.caar = (x) => R.car(R.car(x)); R.cdar = (x) => R.cdr(R.car(x)); R.cadddr = (x) => R.car(R.cdddr(x));
    R.third = R.caddr; R.fourth = R.cadddr;
    R.list = (...a) => a;
    R["make-list"] = (n, x) => new Array(n | 0).fill(x === undefined ? 0 : x);
    R.length = (x) => (Array.isArray(x) || typeof x === "string" ? x.length : x instanceof Map ? x.size : err("length: not a list: " + show(x)));
    R["list-ref"] = (l, k) => { if (!(k >= 0 && k < l.length)) err("list-ref: index " + k + " out of range for a list of length " + l.length); return l[k]; };
    R["list-tail"] = (l, k) => l.slice(k);
    R["list-head"] = (l, k) => l.slice(0, k);
    R["list-copy"] = (l) => l.slice();
    R["last-pair"] = (l) => l.slice(-1);
    R.reverse = (l) => l.slice().reverse();
    R.iota = (n, start, step) => Array.from({ length: n | 0 }, (_, i) => (start || 0) + i * (step === undefined ? 1 : step));
    R.memq = R.memv = (x, l) => { const i = l.findIndex((y) => eqv(x, y)); return i < 0 ? false : l.slice(i); };
    R.member = (x, l, eq) => { const i = l.findIndex((y) => (eq ? eq(x, y) !== false : equal(x, y))); return i < 0 ? false : l.slice(i); };
    R.assq = R.assv = (x, al) => al.find((p) => eqv(R.car(p), x)) || false;
    R.assoc = (x, al, eq) => al.find((p) => (eq ? eq(x, R.car(p)) !== false : equal(x, R.car(p)))) || false;
    R.apply = (f, ...a) => f(...a.slice(0, -1).concat(a.length ? Array.from(a[a.length - 1]) : []));
    R["for-each"] = (f, ...ls) => { const n = Math.min(...ls.map((l) => l.length)); for (let i = 0; i < n; i++) f(...ls.map((l) => l[i])); };
    R["vector-for-each"] = R["for-each"];
    R["string-for-each"] = (f, s) => { for (const c of s) f(new Char(c)); };
    R.filter = (f, l) => l.filter((x) => f(x) !== false);
    // (remove pred list), or Processing's list.remove(index): takes the item out and returns it
    R.remove = (f, l) => {
      if (typeof f === "function") return l.filter((x) => f(x) === false);
      if (Array.isArray(f) && typeof l === "number") { if (!(l >= 0 && l < f.length)) err("remove: index " + l + " out of range"); return f.splice(l, 1)[0]; }
      if (f instanceof Map) { const v = f.get(l); f.delete(l); return v; }
      err("remove: expected a procedure and a list");
    };
    R.save = (name) => A.saveFrame(name);
    R.partition = (f, l) => ({ __values: true, list: [R.filter(f, l), R.remove(f, l)] });
    R.reduce = (f, init, l) => (l.length ? l.slice(1).reduce((acc, x) => f(x, acc), l[0]) : init);
    R["fold-left"] = (f, init, ...ls) => { let acc = init; const n = Math.min(...ls.map((l) => l.length)); for (let i = 0; i < n; i++) acc = f(acc, ...ls.map((l) => l[i])); return acc; };
    R.fold = (f, init, l) => l.reduce((acc, x) => f(x, acc), init);
    R["fold-right"] = (f, init, l) => l.reduceRight((acc, x) => f(x, acc), init);
    R["list-index"] = (f, l) => { const i = l.findIndex((x) => f(x) !== false); return i < 0 ? false : i; };
    R.find = (f, l) => { const v = l.find((x) => f(x) !== false); return v === undefined ? false : v; };
    R.any = (f, l) => { for (const x of l) { const v = f(x); if (v !== false) return v; } return false; };
    R.every = (f, l) => { let v = true; for (const x of l) { v = f(x); if (v === false) return false; } return v; };
    R.delete = (x, l) => l.filter((y) => !equal(x, y));
    R.values = (...a) => (a.length === 1 ? a[0] : { __values: true, list: a });
    R["call-with-values"] = (p, c) => c(...R.vals(p()));
    R.error = (msg, ...irr) => { throw new SchemeError(show(msg) + (irr.length ? " " + irr.map((x) => show(x, true)).join(" ") : ""), irr); };
    R.raise = (x) => { const e = new Error(show(x)); e.payload = x; throw e; };
    R["error-object?"] = (e) => e instanceof Error;
    R["error-object-message"] = (e) => (e instanceof SchemeError ? e.message.split(" ")[0] && e.message : String(e && e.message));
    R["error-object-irritants"] = (e) => (e && e.irritants) || [];
    R["call-with-current-continuation"] = R["call/cc"] = (f) => { const k = new Escape(); try { return f(k.fn); } catch (e) { if (e === k) return k.value; throw e; } };
    R["dynamic-wind"] = (a, b, c) => { a(); try { return b(); } finally { c(); } };
    R.void = () => undefined;
    R.exit = () => A.exit();

    // vectors
    R.vector = (...a) => a;
    R["make-vector"] = (n, x) => new Array(Math.max(0, n | 0)).fill(x === undefined ? 0 : x);
    R["vector-length"] = (v) => v.length;
    R["vector-ref"] = R.vref; R["vector-set!"] = R.vset;
    R["vector-fill!"] = (v, x, s, e) => { v.fill(x, s || 0, e === undefined ? v.length : e); };
    R["vector->list"] = (v, s, e) => v.slice(s || 0, e === undefined ? v.length : e);
    R["list->vector"] = (l) => l.slice();
    R["vector-copy"] = (v, s, e) => v.slice(s || 0, e === undefined ? v.length : e);
    R["vector-copy!"] = (to, at, from, s, e) => { const part = from.slice(s || 0, e === undefined ? from.length : e); for (let i = 0; i < part.length; i++) to[at + i] = part[i]; };
    R["vector-map"] = (f, ...vs) => { const n = Math.min(...vs.map((v) => v.length)); const out = []; for (let i = 0; i < n; i++) out.push(f(...vs.map((v) => v[i]))); return out; };
    R["vector-append"] = (...vs) => [].concat(...vs);
    R["vector-grow"] = (v, n) => v.concat(new Array(Math.max(0, n - v.length)).fill(0));
    R["vector-binary-search"] = (v, x, cmp) => { let lo = 0, hi = v.length - 1; while (lo <= hi) { const m = (lo + hi) >> 1, c = cmp(v[m], x); if (c === 0) return m; if (c < 0) lo = m + 1; else hi = m - 1; } return false; };
    R.map = (f, ...a) => {
      if (typeof f === "number") return A_map(f, ...a);   // Processing's map(value, start1, stop1, start2, stop2)
      const n = Math.min(...a.map((l) => l.length)); const out = new Array(n);
      for (let i = 0; i < n; i++) out[i] = f(...a.map((l) => l[i]));
      return out;
    };
    const A_map = (v, a1, b1, a2, b2) => a2 + (v - a1) / (b1 - a1) * (b2 - a2);
    R.sort = (l, less) => {
      if (typeof l === "function") [l, less] = [less, l];
      const c = l.slice();
      if (typeof less === "number") return c.slice(0, less).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0)).concat(c.slice(less));
      return less ? c.sort((a, b) => (less(a, b) !== false ? -1 : less(b, a) !== false ? 1 : 0)) : c.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
    };
    R["list-sort"] = (less, l) => R.sort(l, less);
    R["sort!"] = (l, less) => { const s = R.sort(l, less); for (let i = 0; i < s.length; i++) l[i] = s[i]; return l; };

    // strings and chars
    R["string-length"] = (s) => s.length;
    R["string-ref"] = (s, k) => { if (!(k >= 0 && k < s.length)) err("string-ref: index " + k + " out of range for a string of length " + s.length); return new Char(s[k]); };
    R.substring = (s, a, b) => s.substring(a, b === undefined ? s.length : b);
    R["string-append"] = (...a) => a.map((x) => (x instanceof Char ? x.c : typeof x === "string" ? x : show(x))).join("");
    R.string = (...a) => a.map(str).join("");
    R["make-string"] = (n, c) => (c ? str(c) : " ").repeat(n | 0);
    R["string-copy"] = (s, a, b) => s.slice(a || 0, b === undefined ? s.length : b);
    R["string->list"] = (s) => [...s].map((c) => new Char(c));
    R["list->string"] = (l) => l.map(str).join("");
    R["string-upcase"] = (s) => s.toUpperCase(); R["string-downcase"] = (s) => s.toLowerCase();
    R["string-index"] = (s, c) => { const i = s.indexOf(str(c)); return i < 0 ? false : i; };
    R["string-contains"] = (s, t) => { const i = s.indexOf(t); return i < 0 ? false : i; };
    R["string-split"] = (s, d) => s.split(str(d));
    R["string-join"] = (l, d) => l.join(d === undefined ? " " : str(d));
    R["string-null?"] = (s) => s.length === 0;
    for (const [n, op] of [["=?", (a, b) => a === b], ["<?", (a, b) => a < b], [">?", (a, b) => a > b], ["<=?", (a, b) => a <= b], [">=?", (a, b) => a >= b]]) {
      R["string" + n] = chain(op); R["string-ci" + n] = chain((a, b) => op(a.toLowerCase(), b.toLowerCase()));
      R["char" + n] = chain((a, b) => op(str(a), str(b)));
    }
    R["char->integer"] = (c) => str(c).codePointAt(0);
    R["integer->char"] = (n) => new Char(String.fromCodePoint(n));
    R["char-upcase"] = (c) => new Char(str(c).toUpperCase()); R["char-downcase"] = (c) => new Char(str(c).toLowerCase());
    R["char-alphabetic?"] = (c) => /\p{L}/u.test(str(c)); R["char-numeric?"] = (c) => /\d/.test(str(c));
    R["char-whitespace?"] = (c) => /\s/.test(str(c));
    R["char-upper-case?"] = (c) => /\p{Lu}/u.test(str(c)); R["char-lower-case?"] = (c) => /\p{Ll}/u.test(str(c));
    R["digit-value"] = (c) => (/\d/.test(str(c)) ? +str(c) : false);
    R["string-map"] = (f, s) => [...s].map((c) => str(f(new Char(c)))).join("");
    R["string-search-forward"] = (t, s, start) => { const i = s.indexOf(t, start || 0); return i < 0 ? false : i; };

    // hash tables
    const hk = (k) => (k instanceof Char ? "c:" + k.c : k instanceof Sym ? "s:" + k.n : k);
    R["make-hash-table"] = R["make-equal-hash-table"] = R["make-strong-eqv-hash-table"] = R["make-string-hash-table"] = () => new Map();
    R["hash-table-set!"] = (h, k, v) => { h.set(hk(k), v); };
    R["hash-table-ref"] = (h, k, dflt) => { const key = hk(k); if (h.has(key)) return h.get(key); if (dflt) return dflt(); err("hash-table-ref: no such key " + show(k, true)); };
    R["hash-table-ref/default"] = (h, k, d) => { const key = hk(k); return h.has(key) ? h.get(key) : d; };
    R["hash-table/get"] = R["hash-table-ref/default"]; R["hash-table/put!"] = R["hash-table-set!"];
    R["hash-table-delete!"] = (h, k) => { h.delete(hk(k)); };
    R["hash-table-contains?"] = R["hash-table-exists?"] = (h, k) => h.has(hk(k));
    R["hash-table-count"] = R["hash-table-size"] = (h) => h.size;
    R["hash-table-keys"] = (h) => [...h.keys()]; R["hash-table-values"] = (h) => [...h.values()];
    R["hash-table->alist"] = (h) => [...h.entries()].map(([k, v]) => [k, v]);
    R["hash-table-walk"] = (h, f) => { for (const [k, v] of h) f(k, v); };
    R["hash-table-update!"] = (h, k, f, d) => { const key = hk(k); h.set(key, f(h.has(key) ? h.get(key) : d ? d() : err("hash-table-update!: no such key"))); };
    R["hash-table-update!/default"] = (h, k, f, d) => { const key = hk(k); h.set(key, f(h.has(key) ? h.get(key) : d)); };
    R["hash-table?"] = (h) => h instanceof Map;

    // ── Processing, Scheme Mode's way ───────────────────────────────────
    const print = W.print;
    R.println = (...a) => { print(a.map((x) => show(x)).join(" ")); };
    R.print = (...a) => { print(a.map((x) => show(x)).join(" ")); };
    R.display = (x) => print(show(x)); R.write = (x) => print(show(x, true)); R.newline = () => print("");
    R["print-array"] = (l) => { l.forEach((x, i) => print("[" + i + "] " + show(x, true))); };
    R.int = (x) => (typeof x === "string" ? (/^\s*-?\d/.test(x) ? parseInt(x, 10) : 0) : x instanceof Char ? x.c.codePointAt(0) : typeof x === "boolean" ? +x : Math.trunc(x));
    R.float = (x) => (typeof x === "string" ? (Number.isNaN(parseFloat(x)) ? 0 : parseFloat(x)) : x instanceof Char ? x.c.codePointAt(0) : +x);
    R.str = (x) => (Array.isArray(x) ? x.map(R.str) : typeof x === "boolean" ? String(x) : show(x));
    R.byte = (x) => { const b = Math.trunc(x) & 255; return b > 127 ? b - 256 : b; };
    R.char = (x) => new Char(typeof x === "number" ? String.fromCodePoint(x) : str(x)[0]);
    const pad = (n, left) => { const neg = n < 0; let s = String(Math.abs(Math.trunc(n))); while (s.length < left) s = "0" + s; return (neg ? "-" : "") + s; };
    R.nf = (n, left, right) => {
      if (Array.isArray(n)) return n.map((x) => R.nf(x, left, right));
      if (right === undefined) return pad(n, left || 0);
      const neg = n < 0; const [i, f] = Math.abs(n).toFixed(right).split(".");
      let s = i; while (s.length < (left || 0)) s = "0" + s;
      return (neg ? "-" : "") + s + (right > 0 ? "." + f : "");
    };
    R.nfc = (n, right) => { const [i, f] = (right === undefined ? String(Math.trunc(n)) : n.toFixed(right)).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
    R.nfp = (n, l, r) => (n >= 0 ? "+" : "") + R.nf(n, l, r);
    R.nfs = (n, l, r) => (n >= 0 ? " " : "") + R.nf(n, l, r);
    R.hex = (n, d) => { let s = ((n | 0) >>> 0).toString(16).toUpperCase(); if (d !== undefined) s = s.padStart(8, "0").slice(-d); return s; };
    R.unhex = (s) => parseInt(s, 16) | 0;
    R.binary = (n, d) => { let s = ((n | 0) >>> 0).toString(2); if (d !== undefined) s = s.padStart(32, "0").slice(-d); return s; };
    R.unbinary = (s) => parseInt(s, 2);
    R.split = (s, d) => String(s).split(str(d));
    R["split-tokens"] = (s, d) => String(s).split(d === undefined ? /\s+/ : new RegExp("[" + d.replace(/[\]\\^-]/g, "\\$&") + "]+")).filter((x) => x.length);
    R.join = (l, d) => l.join(str(d));
    R.trim = (s) => (Array.isArray(s) ? s.map(R.trim) : String(s).trim());
    R.match = (s, re) => { const m = new RegExp(re).exec(s); return m ? Array.from(m, (x) => x || "") : false; };
    R["match-all"] = (s, re) => { const a = [...String(s).matchAll(new RegExp(re, "g"))].map((m) => Array.from(m, (x) => x || "")); return a.length ? a : false; };
    R.append = (...ls) => [].concat(...ls.map((l) => (Array.isArray(l) ? l : [l])));
    R.concat = (...ls) => [].concat(...ls);
    R.expand = (l, n) => { const pad0 = l.length && typeof l[0] === "string" ? "" : 0; return l.concat(new Array(Math.max(0, (n === undefined ? Math.max(1, l.length * 2) : n) - l.length)).fill(pad0)); };
    R.shorten = (l) => l.slice(0, -1);
    R.subset = (l, s, n) => l.slice(s, n === undefined ? undefined : s + n);
    R.splice = (l, v, i) => l.slice(0, i).concat(Array.isArray(v) ? v : [v], l.slice(i));
    R["array-copy"] = (src, a, b, c, d) => { if (b === undefined) { for (let i = 0; i < a.length && i < src.length; i++) a[i] = src[i]; return; } for (let i = 0; i < d; i++) b[c + i] = src[a + i]; };
    R.shuffle = (l) => { for (let i = l.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [l[i], l[j]] = [l[j], l[i]]; } return l; };
    R.sq = (x) => x * x; R.abs = Math.abs;
    R.min = (...a) => (a.length === 1 && Array.isArray(a[0]) ? Math.min(...a[0]) : Math.min(...a));
    R.max = (...a) => (a.length === 1 && Array.isArray(a[0]) ? Math.max(...a[0]) : Math.max(...a));
    R.constrain = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
    R.dist = (...a) => (a.length === 4 ? Math.hypot(a[2] - a[0], a[3] - a[1]) : a.length === 6 ? Math.hypot(a[3] - a[0], a[4] - a[1], a[5] - a[2]) : vecDist(a[0], a[1]));
    R.lerp = (a, b, t) => (typeof a === "number" ? a + (b - a) * t : a.lerp(b, t));
    R.norm = (v, a, b) => (v - a) / (b - a);
    R.mag = (...a) => (a.length === 1 ? a[0].mag() : Math.hypot(...a));
    R.radians = (d) => d * Math.PI / 180; R.degrees = (r) => r * 180 / Math.PI;
    R.pow = Math.pow; R.ceil = Math.ceil;
    R.year = () => new Date().getFullYear(); R.month = () => new Date().getMonth() + 1; R.day = () => new Date().getDate();
    R.hour = () => new Date().getHours(); R.minute = () => new Date().getMinutes();
    R.second = (l) => (l === undefined ? new Date().getSeconds() : R.cadr(l));

    // PVector, Processing's (methods change the vector, as in Java)
    class Vec {
      constructor(x, y, z) { this.x = x || 0; this.y = y || 0; this.z = z || 0; }
      copy() { return new Vec(this.x, this.y, this.z); }
      set(x, y, z) { if (x instanceof Vec) { this.x = x.x; this.y = x.y; this.z = x.z; } else { this.x = x; this.y = y; this.z = z || 0; } return this; }
      mag() { return Math.hypot(this.x, this.y, this.z); }
      magSq() { return this.x * this.x + this.y * this.y + this.z * this.z; }
      add(a, b, c) { if (a instanceof Vec) { this.x += a.x; this.y += a.y; this.z += a.z; } else { this.x += a; this.y += b; this.z += c || 0; } return this; }
      sub(a, b, c) { if (a instanceof Vec) { this.x -= a.x; this.y -= a.y; this.z -= a.z; } else { this.x -= a; this.y -= b; this.z -= c || 0; } return this; }
      mult(n) { if (n instanceof Vec) { this.x *= n.x; this.y *= n.y; this.z *= n.z; } else { this.x *= n; this.y *= n; this.z *= n; } return this; }
      div(n) { if (n instanceof Vec) { this.x /= n.x; this.y /= n.y; this.z /= n.z; } else { this.x /= n; this.y /= n; this.z /= n; } return this; }
      dot(v, y, z) { return v instanceof Vec ? this.x * v.x + this.y * v.y + this.z * v.z : this.x * v + this.y * y + this.z * (z || 0); }
      cross(v) { return new Vec(this.y * v.z - this.z * v.y, this.z * v.x - this.x * v.z, this.x * v.y - this.y * v.x); }
      dist(v) { return Math.hypot(this.x - v.x, this.y - v.y, this.z - v.z); }
      normalize() { const m = this.mag(); if (m > 0) this.div(m); return this; }
      limit(max) { if (this.magSq() > max * max) { this.normalize(); this.mult(max); } return this; }
      setMag(m) { this.normalize(); return this.mult(m); }
      heading() { return Math.atan2(this.y, this.x); }
      setHeading(a) { const m = this.mag(); this.x = m * Math.cos(a); this.y = m * Math.sin(a); return this; }
      rotate(a) { const x = this.x, c = Math.cos(a), s = Math.sin(a); this.x = x * c - this.y * s; this.y = x * s + this.y * c; return this; }
      lerp(v, t) { this.x += (v.x - this.x) * t; this.y += (v.y - this.y) * t; this.z += (v.z - this.z) * t; return this; }
      array() { return [this.x, this.y, this.z]; }
      toString() { return "[ " + this.x + ", " + this.y + ", " + this.z + " ]"; }
    }
    const vecDist = (a, b) => a.dist(b);
    R.Vec = Vec;
    R.PVector = (x, y, z) => new Vec(x, y, z);
    R["create-vector"] = R.PVector;
    R["vec-x"] = (v) => v.x; R["vec-y"] = (v) => v.y; R["vec-z"] = (v) => v.z;
    R["set-vec-x!"] = (v, a) => { v.x = a; }; R["set-vec-y!"] = (v, a) => { v.y = a; }; R["set-vec-z!"] = (v, a) => { v.z = a; };
    R["from-angle"] = (a) => new Vec(Math.cos(a), Math.sin(a));
    R["random2-d"] = () => R["from-angle"](Math.random() * Math.PI * 2);
    R["random3-d"] = () => { const a = Math.random() * Math.PI * 2, z = Math.random() * 2 - 1, r = Math.sqrt(1 - z * z); return new Vec(r * Math.cos(a), r * Math.sin(a), z); };
    R["angle-between"] = (a, b) => Math.acos(Math.max(-1, Math.min(1, a.dot(b) / (a.mag() * b.mag()))));

    // images, layers, fonts and shapes are objects here, not numbers
    class Img { constructor(id) { this.id = id; } get width() { return A.imageWidth(this.id); } get height() { return A.imageHeight(this.id); } toString() { return "#<image " + this.width + "x" + this.height + ">"; } }
    class Gfx extends Img { toString() { return "#<graphics " + this.width + "x" + this.height + ">"; } }
    class Font { constructor(id) { this.id = id; } toString() { return "#<font>"; } }
    class Shape { constructor(id, w, h) { this.id = id; this.w = w; this.h = h; } toString() { return "#<shape>"; } }
    const imgOf = (x) => (x instanceof Img ? x.id : x);
    R["load-image"] = (n) => new Img(A.loadImage(n));
    R["request-image"] = R["load-image"];
    R["create-image"] = (w, h) => new Img(A.createImage(w, h));
    R["create-graphics"] = (w, h, r) => new Gfx(A.createGraphics(w, h, r));
    R["create-font"] = (n, s) => new Font(A.createFont(n, s));
    R["load-font"] = (n) => new Font(A.loadFont(n));
    R["text-font"] = (f, s) => A.textFont(f instanceof Font ? f.id : 0, s);
    R["load-shape"] = (n) => { const [id, w, h] = A.loadShape(n); return id ? new Shape(id, w, h) : false; };
    R.image = (img, ...a) => A.image(imgOf(img), ...a);
    R.texture = (img) => A.texture(imgOf(img));
    R.shape = (s, ...a) => { if (s instanceof Shape) A.shape(s.id, ...a); };

    // pixels: the canvas as a vector of colors, after (load-pixels)
    const D = {};
    R.$D = D;
    // width and height follow size() and layers right away
    Object.defineProperty(D, jsName("width"), { get: () => A.targetSize()[0], enumerable: true });
    Object.defineProperty(D, jsName("height"), { get: () => A.targetSize()[1], enumerable: true });
    Object.defineProperty(D, "width", { get: () => A.targetSize()[0] });
    Object.defineProperty(D, "height", { get: () => A.targetSize()[1] });
    // methods: (name obj args...) calls obj's version when obj is one of these
    const methods = {
      Img: {
        get: (o, x, y, w, h) => (x === undefined ? new Img(A.imageCopy(o.id)) : w !== undefined ? new Img(A.imageGet(o.id, x, y, w, h)) : A.imageGet(o.id, x, y)),
        set: (o, x, y, c) => { if (c instanceof Img) { A.beginGraphics; } A.imageSet(o.id, x, y, c); },
        "load-pixels": (o) => { o.px = A.imgLoadPixels(o.id); },
        "update-pixels": (o) => { if (o.px) A.imgUpdatePixels(o.id, o.px); },
        pixels: (o) => { if (!o.px) o.px = A.imgLoadPixels(o.id); return o.px; },
        width: (o) => o.width, height: (o) => o.height,
        resize: (o, w, h) => { A.imageResize(o.id, w, h || 0); o.px = null; },
        mask: (o, m) => { A.imageMask(o.id, imgOf(m)); o.px = null; },
        filter: (o, k, p) => { A.imgFilter(o.id, k, p); o.px = null; },
        copy: (o, ...a) => { if (!a.length) return new Img(A.imageCopy(o.id)); if (a.length >= 9) A.imgBlend(o.id, imgOf(a[0]), a.slice(1), K.REPLACE); else A.imgBlend(o.id, o.id, a, K.REPLACE); o.px = null; },
        blend: (o, ...a) => { const mode = a.pop(); if (a.length >= 9) A.imgBlend(o.id, imgOf(a[0]), a.slice(1), mode); else A.imgBlend(o.id, o.id, a, mode); o.px = null; },
        save: (o, path) => A.imgSave(o.id, path),
      },
      Gfx: {
        "begin-draw": (o) => { A.beginGraphics(o.id); },
        "end-draw": (o) => { A.endGraphics(); },
      },
      Shape: {
        width: (o) => o.w, height: (o) => o.h,
        "get-child": (o, k) => { const [id, w, h] = A.shapeChild(o.id, k); return id ? new Shape(id, w, h) : false; },
        "get-child-count": (o) => A.shapeChildCount(o.id),
        "disable-style": (o) => A.shapeStyle(o.id, false),
        "enable-style": (o) => A.shapeStyle(o.id, true),
        "get-vertex-count": (o) => A.shapePoints(o.id).length,
        "get-vertex": (o, i) => { const p = A.shapePoints(o.id)[i]; return p ? new Vec(p.x, p.y) : new Vec(); },
      },
      Vec: {},
    };
    for (const [n, m] of [["add", "add"], ["sub", "sub"], ["mult", "mult"], ["div", "div"], ["mag", "mag"], ["mag-sq", "magSq"],
      ["normalize", "normalize"], ["limit", "limit"], ["set-mag", "setMag"], ["heading", "heading"], ["heading2-d", "heading"],
      ["dot", "dot"], ["cross", "cross"], ["dist", "dist"], ["copy", "copy"], ["get", "copy"], ["rotate", "rotate"], ["lerp", "lerp"],
      ["set", "set"], ["array", "array"], ["set-heading", "setHeading"]]) methods.Vec[n] = (o, ...a) => o[m](...a);

    // ── the drawing functions, under their kebab-case names ──────────────
    // A layer as the first argument draws on that layer, like pg.ellipse(...).
    const own = new Set(Object.keys(R));
    for (const name of Object.keys(A)) {
      const k = kebab(name);
      if (own.has(k) || R[k] !== undefined) continue;
      const fn = A[name];
      R[k] = function (...a) {
        if (a[0] instanceof Gfx) {
          A.beginGraphics(a[0].id);
          try { return fn(...a.slice(1).map(imgOf)); } finally { A.endGraphics(); }
        }
        return fn(...a.map((x) => (x instanceof Img || x instanceof Font ? x.id : x)));
      };
    }
    R.size = (w, h, r) => { A.size(w, h, r); };
    R["load-pixels"] = (o) => { if (o !== undefined) return methods.Img["load-pixels"](o); D.pixels = D[jsName("pixels")] = A.loadPixels(); };
    R["update-pixels"] = (o) => { if (o !== undefined) return methods.Img["update-pixels"](o); A.updatePixels(D.pixels); };
    R.get = (...a) => { if (a[0] instanceof Img) return methods.Img.get(...a); if (a[0] instanceof Vec) return a[0].copy(); const v = A.get(...a); return a.length === 0 || a.length === 4 ? new Img(v) : v; };
    R.set = (...a) => { if (a[0] instanceof Img && a.length === 4) return methods.Img.set(...a); if (a[0] instanceof Vec) return a[0].set(...a.slice(1)); A.set(a[0], a[1], a[2] instanceof Img ? a[2].id : a[2]); };
    R.filter = (...a) => (typeof a[0] === "function" ? R.filter_list(...a) : a[0] instanceof Img ? methods.Img.filter(...a) : A.filter(...a));
    R.filter_list = (f, l) => l.filter((x) => f(x) !== false);
    R.copy = (...a) => (a[0] instanceof Vec ? a[0].copy() : a[0] instanceof Img ? methods.Img.copy(...a) : Array.isArray(a[0]) ? a[0].slice() : A.copy(...a.map(imgOf)));
    R.random = (a, b) => (b === undefined ? (a === undefined ? Math.random() : Math.random() * a) : a + Math.random() * (b - a));
    R["frame-rate"] = (fps) => (fps === undefined ? D.frame_rate : A.setFrameRate(fps));
    R.width = (o) => (o === undefined ? D.width : o.width !== undefined ? o.width : o.w);
    R.height = (o) => (o === undefined ? D.height : o.height !== undefined ? o.height : o.h);
    R.pixels = (o) => methods.Img.pixels(o);
    R["key-pressed"] = undefined; R["mouse-pressed"] = undefined;
    // constants, in both spellings (TWO-PI and TWO_PI)
    for (const k in K) { R[k] = K[k]; R[k.replace(/_/g, "-")] = K[k]; }
    // method dispatch: the first argument picks
    const dispatch = (name, base) => function (...a) {
      const o = a[0];
      const kind = o instanceof Gfx ? "Gfx" : o instanceof Img ? "Img" : o instanceof Shape ? "Shape" : o instanceof Vec ? "Vec" : null;
      if (kind) {
        const m = (kind === "Gfx" && methods.Gfx[name]) || (methods[kind] && methods[kind][name]) || (kind === "Gfx" && methods.Img[name]);
        if (m) return m(...a);
      }
      if (base) return base(...a);
      err(name + ": not something that has " + name + ": " + show(o, true));
    };
    for (const kind of Object.keys(methods)) for (const name of Object.keys(methods[kind])) R[name] = dispatch(name, R[name]);
    // data files: Table, JSON, XML (fetched before the sketch started)
    dataLib(R, W, show, err);
    return R;
  }

  // loadTable / loadJSONObject / loadStrings / loadXML, the parts sketches use
  function dataLib(R, W, show, err) {
    const files = W.files;
    const text = (n) => { const v = files[n] !== undefined ? files[n] : files[String(n).replace(/^data\//, "")]; if (v === undefined) err("file not found: " + n + " (put it in the data folder of the sketch)"); return v; };
    R["load-strings"] = (n) => text(n).split(/\r?\n/).filter((l, i, a) => !(i === a.length - 1 && l === ""));
    R["save-strings"] = (n, l) => { files[n] = l.join("\n") + "\n"; };
    class Table { constructor(cols, rows) { this.columns = cols; this.rows = rows; } toString() { return "#<table " + this.rows.length + " rows>"; } }
    class Row { constructor(t, i) { this.t = t; this.i = i; } }
    R["load-table"] = (n, opts) => {
      const delim = /tsv/.test(opts || "") || /\.tsv$/.test(n) ? "\t" : ",";
      const lines = text(n).split(/\r?\n/).filter((l) => l.length);
      const parse = (l) => { if (delim === "\t") return l.split("\t"); const out = []; let cur = "", q = false; for (const c of l) { if (c === '"') q = !q; else if (c === "," && !q) { out.push(cur); cur = ""; } else cur += c; } out.push(cur); return out; };
      const header = /header/.test(opts || "");
      const rows = lines.map(parse);
      const cols = header ? rows.shift() : (rows[0] || []).map((_, i) => String(i));
      return new Table(cols, rows);
    };
    const col = (t, c) => (typeof c === "number" ? c : t.columns.indexOf(c));
    R["get-row-count"] = (t) => t.rows.length;
    R["get-column-count"] = (t) => t.columns.length;
    R["get-row"] = (t, i) => new Row(t, i);
    R.rows = (t) => t.rows.map((_, i) => new Row(t, i));
    R["add-row"] = (t) => { t.rows.push(t.columns.map(() => "")); return new Row(t, t.rows.length - 1); };
    R["remove-row"] = (t, i) => { t.rows.splice(i, 1); };
    R["save-table"] = (t, n) => { files[n] = [t.columns.join(",")].concat(t.rows.map((r) => r.join(","))).join("\n"); };
    const getter = (conv) => (o, k) => {
      if (o instanceof Row) return conv(o.t.rows[o.i][col(o.t, k)]);
      if (o instanceof Map) return o.get(k);
      if (Array.isArray(o)) return o[k];
      err("not a table row: " + show(o, true));
    };
    const setter = (conv) => (o, k, v) => {
      if (o instanceof Row) { o.t.rows[o.i][col(o.t, k)] = String(v); return; }
      if (o instanceof Map) { o.set(k, conv(v)); return; }
      if (Array.isArray(o)) o[k] = conv(v);
    };
    R["get-float"] = getter((v) => parseFloat(v)); R["get-int"] = getter((v) => parseInt(v, 10) | 0); R["get-string"] = getter((v) => (v === undefined ? "" : v));
    R["get-boolean"] = getter((v) => v === true || v === "true");
    R["set-float"] = setter((v) => +v); R["set-int"] = setter((v) => v | 0); R["set-string"] = setter((v) => String(v));
    R["get-json-object"] = (o, k) => o.get ? o.get(k) : o[k]; R["get-json-array"] = R["get-json-object"];
    R["set-json-object"] = (o, k, v) => (o instanceof Map ? o.set(k, v) : (o[k] = v));
    R["set-json-array"] = R["set-json-object"];
    const fromJSON = (v) => (Array.isArray(v) ? v.map(fromJSON) : v && typeof v === "object" ? new Map(Object.entries(v).map(([k, x]) => [k, fromJSON(x)])) : v);
    const toJSON = (v) => (v instanceof Map ? Object.fromEntries([...v].map(([k, x]) => [k, toJSON(x)])) : Array.isArray(v) ? v.map(toJSON) : v);
    R["load-json-object"] = (n) => fromJSON(JSON.parse(text(n))); R["load-json-array"] = R["load-json-object"];
    R["parse-json-object"] = (s) => fromJSON(JSON.parse(s)); R["parse-json-array"] = R["parse-json-object"];
    R["save-json-object"] = (a, b) => { const [n, v] = typeof a === "string" ? [a, b] : [b, a]; files[n] = JSON.stringify(toJSON(v), null, 2); };
    R["save-json-array"] = R["save-json-object"];
    R.size = ((base) => (...a) => (a.length === 1 && (a[0] instanceof Map || Array.isArray(a[0])) ? (a[0].size !== undefined ? a[0].size : a[0].length) : base(...a)))(R.size);
    R["has-key"] = (m, k) => m.has(k);
    class Xml { constructor(el) { this.el = el; } toString() { return "#<xml " + this.el.tagName + ">"; } }
    R["load-xml"] = (n) => new Xml(new DOMParser().parseFromString(text(n), "application/xml").documentElement);
    R["parse-xml"] = (s) => new Xml(new DOMParser().parseFromString(s, "application/xml").documentElement);
    R["get-children"] = (x, name) => [...x.el.children].filter((c) => !name || c.tagName === name).map((c) => new Xml(c));
    const child = R["get-child"];
    R["get-child"] = (x, k) => { if (!(x instanceof Xml)) return child(x, k); const c = typeof k === "number" ? x.el.children[k] : x.el.querySelector(":scope > " + k); return c ? new Xml(c) : false; };
    const childCount = R["get-child-count"];
    R["get-child-count"] = (x) => (x instanceof Xml ? x.el.children.length : childCount(x));
    R["get-content"] = (x) => x.el.textContent;
    R["get-name"] = (x) => x.el.tagName;
    const xg = (conv, base) => (o, k, d) => (o instanceof Xml ? (o.el.hasAttribute(k) ? conv(o.el.getAttribute(k)) : d === undefined ? conv("") : d) : base(o, k));
    R["get-string"] = xg((v) => v, R["get-string"]); R["get-int"] = xg((v) => parseInt(v, 10) || 0, R["get-int"]);
    R["get-float"] = xg((v) => parseFloat(v) || 0, R["get-float"]);
  }

  // ── running ──────────────────────────────────────────────────────────────
  const DYNAMIC = ["mouse-x", "mouse-y", "pmouse-x", "pmouse-y", "mouse-is-pressed", "key-is-pressed", "mouse-button", "key",
    "key-code", "width", "height", "frame-count", "focused", "pixels", "pixel-width", "pixel-height", "moved-x", "moved-y", "mouse-wheel"];
  const IMG = /\.(png|jpe?g|gif|bmp)$/i, FONT = /\.(ttf|otf)$/i, TEXT = /\.(txt|csv|tsv|json|xml|svg|obj)$/i;

  function compile(code) {
    const forms = read(code);
    const builtins = new Set(Object.keys(BUILTIN_NAMES));
    const globals = topNames(forms);
    const c = new Compiler(builtins, new Set(DYNAMIC.filter((n) => !globals.has(n))), globals);
    return c.program(forms);
  }
  // the names the sketch defines at the top level: they win over built-in ones
  function topNames(forms) {
    const out = new Set();
    const walk = (f) => {
      if (!isList(f) || !(f[0] instanceof Sym)) return;
      const h = f[0].n;
      if (h === "begin") return f.slice(1).forEach(walk);
      if (h === "define") { const t = f[1]; out.add(isList(t) ? t[0].n : t instanceof Pair ? t.car.n : t.n); }
      if (h === "define-values" && isList(f[1])) f[1].forEach((x) => out.add(x.n));
      if (h === "define-record-type") {
        out.add(f[1] instanceof Sym ? f[1].n : f[1][0].n);
        if (isList(f[2])) out.add(f[2][0].n); else if (f[2] instanceof Sym) out.add(f[2].n);
        out.add(f[3].n);
        f.slice(4).forEach((fd) => { if (isList(fd)) fd.slice(1).forEach((x) => out.add(x.n)); });
      }
    };
    forms.forEach(walk);
    return out;
  }
  let BUILTIN_NAMES = {};

  function run(opts) {
    const code = opts.code;
    const print = opts.print || console.log;
    const files = {};
    const strings = [];
    code.replace(/"((?:\\.|[^"\\])*)"/g, (_, s) => { strings.push(s); return ""; });
    const base = opts.dataBase || "";
    return Promise.all(strings.filter((n) => TEXT.test(n)).map((n) =>
      fetch(/^https?:/.test(n) ? n : base + n.replace(/^data\//, "")).then((r) => (r.ok ? r.text() : null)).then((t) => { if (t !== null) files[n] = t; }).catch(() => {})
    )).then(() => start(opts, code, print, files, strings));
  }

  function start(opts, code, print, files, strings) {
    let stopped = false;
    let lineNow = 0;
    const W = new global.PWeb({ dataBase: opts.dataBase, print, files, error: (e) => report(e), exit: opts.exit });
    W.print = print; W.files = files;
    function report(e) {
      if (stopped) return; stopped = true;
      try { W.p5() && W.p5().noLoop(); } catch (_) {}
      const ln = (e && e.schemeLine) || lineNow;
      let msg = (e && e.message) || String(e);
      msg = msg.replace(/\$([A-Za-z0-9_]+)/g, (m, s) => s.replace(/_([0-9a-z]+)_/g, (x, c) => String.fromCharCode(parseInt(c, 36))));
      if (/is not a function/.test(msg)) msg = msg.replace(/^(?:G\.)?(.*) is not a function$/, "$1 is not a procedure (or isn't defined yet)");
      if (/is not defined|Cannot read properties of undefined/.test(msg)) msg = msg.replace(/^G\./, "");
      (opts.error || console.error)((ln ? "line " + ln + ": " : "") + msg);
    }
    let R, G = {}, js;
    const host = {
      setup() {
        try {
          R = Runtime(W);
          BUILTIN_NAMES = R;
          js = opts.js || compile(code);   // wscheme compiles on the server
          const D = R.$D;
          const f = new Function("R", "G", "$D", "$rt", "var $L=0;Object.defineProperty($rt,'line',{get(){return $L;}});" + js);
          sync();
          f(R, G, D, rt);
          call("setup");
        } catch (e) { report(e); }
        if (opts.ready) opts.ready();
      },
      draw() { if (stopped) return; try { sync(); call("draw"); } catch (e) { report(e); } },
      event(name, a) { if (stopped) return; try { sync(); call(kebab(name), a); } catch (e) { report(e); } },
    };
    const rt = {};
    function call(name, a) {
      const fn = G[jsName(name)];
      if (typeof fn !== "function") return;
      try { a === undefined ? fn() : fn.length ? fn(a) : fn(); } catch (e) { if (!e.schemeLine) e.schemeLine = rt.line; throw e; }
    }
    function sync() {
      const s = W.state(), D = R.$D;
      D[jsName("mouse-x")] = s.mouseX; D[jsName("mouse-y")] = s.mouseY;
      D[jsName("pmouse-x")] = s.pmouseX; D[jsName("pmouse-y")] = s.pmouseY;
      D[jsName("mouse-is-pressed")] = s.mousePressed; D[jsName("key-is-pressed")] = s.keyPressed;
      D[jsName("mouse-button")] = s.mouseButton;
      D[jsName("key")] = typeof s.key === "string" ? (s.key.length === 1 ? new Char(s.key) : s.key) : s.key;
      D[jsName("key-code")] = s.keyCode;
      D[jsName("frame-count")] = s.frameCount; D.frame_rate = s.frameRate; D[jsName("focused")] = s.focused;
      D[jsName("pixel-width")] = s.width; D[jsName("pixel-height")] = s.height;
      D[jsName("pixels")] = D.pixels;
    }
    W.run(opts.parent, host, { images: strings.filter((n) => IMG.test(n)), fonts: strings.filter((n) => FONT.test(n)) });
    return { stop() { stopped = true; try { W.p5().remove(); } catch (_) {} } };
  }
  const jsNameOf = (n) => jsName(n).slice(1) === n ? n : jsName(n).slice(1);

  global.SchemeWeb = { run, read, compile: (code, builtins) => { BUILTIN_NAMES = builtins || BUILTIN_NAMES; return compile(code); },
                       __runtime: (W) => Runtime(W) };
})(typeof window !== "undefined" ? window : globalThis);
