"""
Updates the "Under the Hood" content in assets/reference.yml by pulling
the actual symbol definitions straight from the CppMode source, so the
reference docs stay in sync with the real implementation instead of
going stale.

Source files read (first match wins per file):
    /home/pep/sketchbook/modes/CppMode/src/Processing.h
    /home/pep/sketchbook/modes/CppMode/src/Processing.cpp

For every entry in reference.yml, this script derives a symbol name from
the entry's `name` field (stripping a trailing "()" if present -- nothing
else is stripped, since a leading "_" as in "_mousePressed" or
"_frameRate" is part of the real symbol name and must be kept), then
searches both source files for every actual DEFINITION of that symbol
(not call sites), grabs each one as a complete, self-contained block via
brace matching, and writes the result into two separate fields:

    under_the_hood_h    <- everything found in Processing.h
    under_the_hood_cpp  <- everything found in Processing.cpp

If a symbol has multiple overloads in a file, all of them are extracted
and concatenated (each separated by a blank line), in source order.
If a symbol is not found in a given file at all, that file's field is
set to null. The legacy single `impl` field is left alone (untouched)
so nothing already relying on it breaks; the two new fields are what
the reference page template should be updated to render going forward.

Usage:
    python3 regen_under_the_hood.py

This only rewrites assets/reference.yml. Run regen_reference.py
afterwards to regenerate the HTML pages from the updated data.
"""
import os
import re
import yaml

SRC_DIR = "/home/pep/sketchbook/modes/CppMode/src"
H_FILE = os.path.join(SRC_DIR, "Processing.h")
CPP_FILE = os.path.join(SRC_DIR, "Processing.cpp")

DATA_FILE = os.path.join(os.path.dirname(__file__), "assets", "reference.yml")


def symbol_name_for(entry):
    """
    Derive the source-level symbol name from an entry's display name.
    Only a trailing "()" is stripped (e.g. "abs()" -> "abs"). A leading
    "_" (e.g. "_mousePressed", "_frameRate") is part of the real symbol
    and is kept as-is. Names with no parens (e.g. "PVector", "mouseX",
    "color") are used verbatim.
    """
    name = entry.get("name", "")
    if name.endswith("()"):
        name = name[:-2]
    return name.strip()


def find_matching_brace(text, open_pos):
    """
    Given the index of an opening '{' in text, return the index of its
    matching closing '}', accounting for nested braces, string literals,
    char literals, and line/block comments so braces inside those don't
    throw off the count.
    """
    depth = 0
    i = open_pos
    n = len(text)
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_line_comment:
            if c == "\n":
                in_line_comment = False
        elif in_block_comment:
            if c == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if c == "\\":
                i += 1  # skip escaped char
            elif c == '"':
                in_string = False
        elif in_char:
            if c == "\\":
                i += 1
            elif c == "'":
                in_char = False
        else:
            if c == "/" and nxt == "/":
                in_line_comment = True
                i += 1
            elif c == "/" and nxt == "*":
                in_block_comment = True
                i += 1
            elif c == '"':
                in_string = True
            elif c == "'":
                in_char = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1  # unbalanced; caller should treat as not found


def find_statement_end(text, start_pos):
    """
    For a declaration with no body (ends in ';' rather than '{...}'),
    find the index of that terminating ';', skipping over strings/chars/
    comments the same way find_matching_brace does, and also skipping
    over any parenthesis nesting so a ';' inside default-argument
    expressions etc. doesn't end things early.
    """
    i = start_pos
    n = len(text)
    paren_depth = 0
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_line_comment:
            if c == "\n":
                in_line_comment = False
        elif in_block_comment:
            if c == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if c == "\\":
                i += 1
            elif c == '"':
                in_string = False
        elif in_char:
            if c == "\\":
                i += 1
            elif c == "'":
                in_char = False
        else:
            if c == "/" and nxt == "/":
                in_line_comment = True
                i += 1
            elif c == "/" and nxt == "*":
                in_block_comment = True
                i += 1
            elif c == '"':
                in_string = True
            elif c == "'":
                in_char = True
            elif c == "(":
                paren_depth += 1
            elif c == ")":
                paren_depth -= 1
            elif c == "{":
                # a body actually exists; not a bare declaration after all
                return None
            elif c == ";" and paren_depth <= 0:
                return i
        i += 1
    return -1


_word_chars = re.compile(r"[A-Za-z0-9_]")


def is_word_boundary(text, pos):
    """True if pos is not adjacent to an identifier character, i.e. a
    real word boundary rather than the middle of a longer identifier."""
    if pos < 0 or pos >= len(text):
        return True
    return not _word_chars.match(text[pos])


def find_definition_starts(text, symbol):
    """
    Find every index in `text` where `symbol` appears as a standalone
    identifier (real word boundaries on both sides), skipping occurrences
    inside string/char literals and comments, since those are not code.
    This intentionally does NOT try to distinguish "definition" from
    "call site" at this stage -- that filtering happens by the caller,
    which only keeps matches immediately followed by '(' + params + a
    body/declaration, or by a class/struct context, which call sites
    do not have.
    """
    positions = []
    pattern = re.compile(re.escape(symbol))
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    i = 0
    n = len(text)

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if c == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if in_char:
            if c == "\\":
                i += 2
                continue
            if c == "'":
                in_char = False
            i += 1
            continue

        if c == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if c == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if c == '"':
            in_string = True
            i += 1
            continue
        if c == "'":
            in_char = True
            i += 1
            continue

        m = pattern.match(text, i)
        if m and is_word_boundary(text, i - 1) and is_word_boundary(text, i + len(symbol)):
            positions.append(i)
            i += len(symbol)
            continue

        i += 1

    return positions


def extract_class_block(text, symbol, match_pos):
    """
    Given a match position for `symbol` that looks like a class/struct
    declaration ("class symbol ... { ... };" or "struct symbol ... {
    ... };"), capture the full block including the trailing ';'.
    Returns None if this match doesn't actually look like a class head.
    """
    # Look backwards (skipping whitespace) for "class" or "struct"
    before = text[:match_pos]
    m = re.search(r"\b(class|struct)\s*$", before)
    if not m:
        return None

    # Find the next '{' after the symbol (allows for ": public Base" etc.)
    brace_pos = text.find("{", match_pos)
    if brace_pos == -1:
        return None
    # Make sure there's no stray ';' before that '{' (would mean this is
    # a forward declaration, not the real definition)
    between = text[match_pos:brace_pos]
    if ";" in between:
        return None

    close_pos = find_matching_brace(text, brace_pos)
    if close_pos == -1:
        return None

    # Capture from "class"/"struct" keyword through the closing brace,
    # plus a trailing ';' if present. Also include an immediately
    # preceding "template<...>" line, if present, so generic class
    # definitions are captured complete.
    start = m.start()
    line_start = text.rfind("\n", 0, start) + 1
    prev_line_end = line_start - 1
    if prev_line_end > 0:
        prev_line_start = text.rfind("\n", 0, prev_line_end) + 1
        prev_line = text[prev_line_start:prev_line_end]
        if re.match(r"\s*template\s*<", prev_line):
            start = prev_line_start
    end = close_pos + 1
    if end < len(text) and text[end] == ";":
        end += 1
    return text[start:end].strip()


def _strip_comments(s):
    """Remove // line comments and /* */ block comments from a string,
    replacing them with nothing (safe here since we only use the result
    for a structural look-back check, not for re-emitting source)."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"//[^\n]*", "", s)
    return s


def looks_like_declaration_context(text, match_pos):
    """
    True if the text immediately before `match_pos` plausibly ends a
    return type / qualifier list for a function or variable declaration,
    rather than being in the middle of an expression (a call site or a
    read of a variable). This is a heuristic, not a real parser.

    The look-back window is the nearest previous statement/block
    boundary (';', '{', '}') -- or start of file -- to match_pos, with
    comments and preprocessor directive lines stripped out first so they
    can't be mistaken for expression syntax.
    """
    boundary = max(
        text.rfind(";", 0, match_pos),
        text.rfind("{", 0, match_pos),
        text.rfind("}", 0, match_pos),
    )
    raw_segment = text[boundary + 1:match_pos]
    segment = _strip_comments(raw_segment)
    # Drop preprocessor directive lines entirely (#include, #pragma, #define, ...)
    segment = "\n".join(
        line for line in segment.split("\n") if not line.strip().startswith("#")
    )

    # Reject if the segment contains characters that only show up in
    # expressions/calls, not in a return-type/qualifier list (assignment,
    # arithmetic operators, array indexing, member access).
    if re.search(r"[=+\-/%!\[\]]", segment):
        return False
    if re.search(r"\.\w", segment):
        return False
    # Reject if there's an unmatched '(' before us (we'd be inside a
    # call's argument list, e.g. "foo(abs(x))" when checking "abs").
    if segment.count("(") != segment.count(")"):
        return False
    return True


def extract_function_block(text, symbol, match_pos):
    """
    Given a match position for `symbol` that looks like a function name
    immediately followed by '(' (a call OR a definition/declaration),
    capture the complete definition if this is actually one -- i.e. the
    symbol sits in a declaration context (return type/qualifiers right
    before it, not mid-expression) AND the parameter list is followed by
    either a '{...}' body or a bare ';' declaration. Returns None for
    anything that looks like a call site instead.
    """
    n = len(text)
    i = match_pos + len(symbol)

    # skip whitespace before '('
    while i < n and text[i] in " \t":
        i += 1
    if i >= n or text[i] != "(":
        return None  # not a call/def at all (e.g. a variable usage)

    if not looks_like_declaration_context(text, match_pos):
        return None  # looks like a call site, e.g. "y = abs(-5.0f);"

    # Walk to the matching ')' of the parameter list, respecting nested
    # parens (default args can contain calls, e.g. "float m=1.0f*2").
    paren_depth = 0
    j = i
    while j < n:
        if text[j] == "(":
            paren_depth += 1
        elif text[j] == ")":
            paren_depth -= 1
            if paren_depth == 0:
                break
        j += 1
    else:
        return None
    close_paren = j

    # Find the line start so we can include qualifiers/return type that
    # precede the symbol on the same line (e.g. "inline float ").
    line_start = text.rfind("\n", 0, match_pos) + 1
    # If the line immediately above is a "template<...>" header, include
    # it too, so generic definitions are captured complete and would
    # actually compile if pasted standalone.
    prev_line_end = line_start - 1  # the '\n' just before this line, or -1
    if prev_line_end > 0:
        prev_line_start = text.rfind("\n", 0, prev_line_end) + 1
        prev_line = text[prev_line_start:prev_line_end]
        if re.match(r"\s*template\s*<", prev_line):
            line_start = prev_line_start

    # Skip whitespace/qualifiers after ')' (const, noexcept, override,
    # trailing return types with "->", initializer lists "X(): a(1)")
    k = close_paren + 1
    # Skip a trailing "const"/"noexcept" etc. and whitespace, plus an
    # optional constructor initializer list, up to the first '{' or ';'
    # at depth 0 relative to any further parens encountered.
    depth = 0
    while k < n:
        c = text[k]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif depth == 0 and c == "{":
            close = find_matching_brace(text, k)
            if close == -1:
                return None
            return text[line_start:close + 1].strip()
        elif depth == 0 and c == ";":
            return text[line_start:k + 1].strip()
        k += 1
    return None


def extract_variable_decl(text, symbol, match_pos):
    """
    Given a match position for `symbol` that is NOT followed by '(' and
    is NOT a class/struct head, check whether it looks like a simple
    variable declaration/definition on its own statement, e.g.:
        extern float mouseX, mouseY;
        float mouseX = 0, mouseY = 0;
        bool _mousePressed = false;
    and if so return that whole statement (start of statement through
    the terminating ';'). Returns None otherwise (e.g. mid-expression
    use of the variable, which is a "call site" equivalent for data).
    """
    n = len(text)

    if not looks_like_declaration_context(text, match_pos):
        return None

    # Must be immediately followed by whitespace, ',', ';', or '=' --
    # i.e. this is the declared name itself, not some other usage.
    i = match_pos + len(symbol)
    while i < n and text[i] in " \t":
        i += 1
    if i >= n or text[i] not in ",;=":
        return None

    boundary = max(
        text.rfind(";", 0, match_pos),
        text.rfind("{", 0, match_pos),
        text.rfind("}", 0, match_pos),
    )
    start = boundary + 1
    while start < match_pos and text[start] in " \t\n":
        start += 1

    end = find_statement_end(text, i)
    if end is None or end == -1:
        return None
    return text[start:end + 1].strip()


def extract_all_definitions(text, symbol):
    """
    Find every real definition of `symbol` in `text` (class blocks,
    function bodies/declarations, or plain variable declarations), in
    source order, skipping plain call sites and unrelated identifier
    matches. Returns a list of strings, each one a complete,
    self-contained definition block.

    Matches that fall inside an already-captured class block's text
    span are skipped, since a class's own constructors share its name
    and would otherwise be captured twice (once as part of the class
    body, once again as a standalone "function").
    """
    results = []
    seen_spans = set()
    consumed_ranges = []  # list of (start, end) absolute offsets already captured as a class block

    def inside_consumed(pos):
        return any(start <= pos < end for start, end in consumed_ranges)

    for pos in find_definition_starts(text, symbol):
        if inside_consumed(pos):
            continue

        block = extract_class_block(text, symbol, pos)
        if block is not None:
            idx = text.find(block, pos - 200 if pos > 200 else 0)
            if idx == -1:
                idx = text.find(block)
            if idx != -1:
                consumed_ranges.append((idx, idx + len(block)))
        else:
            block = extract_function_block(text, symbol, pos)
            if block is None:
                block = extract_variable_decl(text, symbol, pos)
        if block is None:
            continue
        span_key = (block[:60], len(block))  # cheap de-dupe key
        if span_key in seen_spans:
            continue
        seen_spans.add(span_key)
        results.append(block)

    return results


def extract_from_file(filepath, symbol):
    if not os.path.exists(filepath):
        return None, f"file not found: {filepath}"
    try:
        with open(filepath, "r", errors="replace") as f:
            text = f.read()
    except OSError as e:
        return None, f"could not read {filepath}: {e}"

    defs = extract_all_definitions(text, symbol)
    if not defs:
        return None, None
    return "\n\n".join(defs), None


def main():
    with open(DATA_FILE) as f:
        data = yaml.safe_load(f)

    entries = data["entries"]

    found_h = found_cpp = 0
    not_found = []

    for entry in entries:
        symbol = symbol_name_for(entry)
        if not symbol:
            entry["under_the_hood_h"] = None
            entry["under_the_hood_cpp"] = None
            continue

        h_result, h_err = extract_from_file(H_FILE, symbol)
        cpp_result, cpp_err = extract_from_file(CPP_FILE, symbol)

        entry["under_the_hood_h"] = h_result
        entry["under_the_hood_cpp"] = cpp_result

        if h_result:
            found_h += 1
        if cpp_result:
            found_cpp += 1
        if not h_result and not cpp_result:
            not_found.append((entry["slug"], symbol))

        if h_err and "file not found" in h_err:
            print(f"WARNING: {h_err}")
        if cpp_err and "file not found" in cpp_err:
            print(f"WARNING: {cpp_err}")

    with open(DATA_FILE, "w") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=100)

    print(f"Checked {len(entries)} entries.")
    print(f"Found in Processing.h:   {found_h}")
    print(f"Found in Processing.cpp: {found_cpp}")
    print(f"Not found in either file: {len(not_found)}")
    for slug, symbol in not_found:
        print(f"  - {slug} (symbol: {symbol!r})")


if __name__ == "__main__":
    main()
