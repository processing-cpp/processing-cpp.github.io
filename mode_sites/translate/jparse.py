import re, tree_sitter as ts, tree_sitter_java as tj
P = ts.Parser(ts.Language(tj.language()))
TOK = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)
def prep_code(s):
    s = re.sub(r'#([0-9A-Fa-f]{6})\b', lambda m: '0xFF' + m.group(1).upper(), s)
    s = re.sub(r'(?<![\w.])(int|float|boolean|char|byte|str)\s*\(', r'__\1(', s)
    return s
def prep(src):
    # only code changes; comments and strings stay as written
    out, i = [], 0
    for m in TOK.finditer(src):
        out.append(prep_code(src[i:m.start()]))
        out.append(m.group(0))
        i = m.end()
    out.append(prep_code(src[i:]))
    return "".join(out)
def is_static(src):
    return not re.search(r'^\s*(void|public\s+void)\s+(setup|draw|settings)\s*\(', src, re.M)
def parse(src):
    s = prep(src)
    static = is_static(src)
    if static:
        b = ("class __S { void __static() {\n" + s + "\n}}\n").encode()
    else:
        b = ("class __S {\n" + s + "\n}\n").encode()
    return P.parse(b), b, static
