#!/usr/bin/env python3
import glob, os

REPO = os.path.dirname(os.path.abspath(__file__))

NEW_FOOTER = '<footer>\n  <p>C++ Mode for Processing</p>\n  <p class="footer-contact">\n    <a href="mailto:pep84c@gmail.com">pep84c@gmail.com</a>\n    <span class="footer-sep">&middot;</span>\n    <a href="https://discord.gg/vShSrPegJT">Discord</a>\n  </p>\n</footer>'

FOOTER_CSS = '\n    .footer-contact { margin-top: 0.4rem; font-size: 12px; }\n    .footer-contact a { color: #aaa; border-bottom: 1px solid transparent; }\n    .footer-contact a:hover { color: #111; border-bottom-color: #111; }\n    .footer-sep { color: #ccc; margin: 0 0.5rem; }'

files = glob.glob(os.path.join(REPO, '**/*.html'), recursive=True)
files = [f for f in files if '/examples/' not in f and '.git' not in f]

changed = 0
for f in sorted(files):
    raw = open(f, 'rb').read()
    text = raw.decode('utf-8', errors='replace')

    if 'discord.gg' in text:
        continue

    original = text

    # Find and replace the footer - try every variant
    for old in [
        '<footer><p>C++ Mode for Processing</p></footer>',
        '<footer><p>Processing for C++</p></footer>',
    ]:
        if old in text:
            text = text.replace(old, NEW_FOOTER)
            break

    # Add CSS if footer was replaced but CSS missing
    if text != original and 'footer-contact' not in text and '</style>' in text:
        text = text.replace('</style>', FOOTER_CSS + '\n  </style>', 1)

    if text != original:
        open(f, 'w', encoding='utf-8').write(text)
        changed += 1
        print(f'  {os.path.relpath(f, REPO)}')

print(f'\nUpdated {changed} files.')
