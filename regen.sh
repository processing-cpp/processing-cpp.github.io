#!/bin/bash
cd ~/Projects/processing-cpp.github.io
python3 regen.py && git add . && git commit -m "Regenerate examples" && git push origin main
