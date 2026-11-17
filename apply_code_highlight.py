#!/usr/bin/env python3
"""
Run from repo root:
    python3 apply_code_highlight.py

Adds CodeMirror read-only syntax highlighting to all static <pre><code>
blocks across the entire site including reference/, error/, and examples/.
"""

import os, glob

REPO = os.path.dirname(os.path.abspath(__file__))

STATIC_CM_CSS = '''
    .cm-static-wrap .CodeMirror {
      height: auto;
      border-radius: 8px;
      font-size: 13px;
      line-height: 1.6;
      padding: 0.25rem 0;
      margin-bottom: 1.25rem;
      font-family: "SF Mono", "Fira Code", "Source Code Pro", monospace;
    }
    .cm-static-wrap .CodeMirror-scroll {
      overflow: hidden !important;
      max-height: none;
    }
    .cm-static-wrap .CodeMirror-scrollbar-filler { display: none; }'''

def get_prefix(rel):
    depth = len([p for p in rel.split('/')[:-1] if p])
    return '../' * depth if depth > 0 else ''

def scripts(prefix):
    return f'''<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="{prefix}assets/cppmode-keywords.js"></script>
<script src="{prefix}assets/cm-cppmode.js"></script>
<script src="{prefix}assets/code-highlight.js"></script>'''

all_files = glob.glob(os.path.join(REPO, '**/*.html'), recursive=True)
all_files = [f for f in all_files if '.git' not in f and '__pycache__' not in f]

changed = 0
skipped = 0
for f in sorted(all_files):
    text = open(f).read()

    if '<pre>' not in text and '<pre ' not in text:
        continue

    if 'code-highlight.js' in text:
        skipped += 1
        continue

    rel = os.path.relpath(f, REPO)
    prefix = get_prefix(rel)

    if 'cm-static-wrap' not in text and '</style>' in text:
        text = text.replace('</style>', STATIC_CM_CSS + '\n  </style>', 1)

    text = text.replace('</body>', scripts(prefix) + '\n</body>', 1)

    open(f, 'w').write(text)
    changed += 1
    print(f'  patched: {rel}')

print(f'\nDone. Patched {changed} files, skipped {skipped} already done.')
