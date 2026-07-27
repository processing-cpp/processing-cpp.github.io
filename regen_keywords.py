#!/usr/bin/env python3
"""
Generate assets/cppmode-keywords.js from sketchbook/modes/CppMode/keywords.txt
Run whenever keywords.txt changes.
"""
from pathlib import Path

KEYWORDS_TXT = Path.home() / "sketchbook/modes/CppMode/keywords.txt"
OUT = Path(__file__).parent / "assets/cppmode-keywords.js"

cats = {}

for line in KEYWORDS_TXT.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    parts = line.split()
    if len(parts) >= 2:
        word, cat = parts[0], parts[1]
        cats.setdefault(cat, []).append(word)

def js_set(words):
    quoted = ", ".join(f'"{w}"' for w in sorted(set(words)))
    return f"new Set([{quoted}])"

lines = ["// AUTO-GENERATED from keywords.txt -- do not edit manually",
         "// Run: python3 regen_keywords.py",
         "",
         "var CPPMODE_KEYWORDS = {"]

for cat, words in sorted(cats.items()):
    lines.append(f"  {cat}: {js_set(words)},")

lines += ["};", ""]

OUT.write_text("\n".join(lines))
total = sum(len(v) for v in cats.values())
print(f"Written {OUT} ({total} entries across {len(cats)} categories)")
for cat, words in sorted(cats.items()):
    print(f"  {cat}: {len(words)} words")
