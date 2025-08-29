#!/usr/bin/env python3
import re

# Read the file
with open("/root/legal-corpus/scripts/fetch_bgh_juris.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the unterminated string literal at line 122
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'f.write(json.dumps(rec, ensure_ascii=False) + "' in line and line.endswith('"'):
        lines[i] = line[:-1] + '\\n")'
        print(f"Fixed line {i+1}: {lines[i]}")

# Write back the file
with open("/root/legal-corpus/scripts/fetch_bgh_juris.py", "w", encoding="utf-8") as f:
    f.write('\n'.join(lines))

print("BGH file fixed successfully")