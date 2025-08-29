#!/usr/bin/env python3
import re

# Read the file
with open("/root/legal-corpus/scripts/fetch_bverfg_index.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the unterminated string literals
lines = content.split('\n')
for i, line in enumerate(lines):
    if line.strip() == 'txt = "':
        lines[i] = '    txt = "\\n"'
        print(f"Fixed line {i+1}: {lines[i]}")
    elif 'f.write(json.dumps(rec, ensure_ascii=False) + "' in line and line.endswith('"'):
        lines[i] = line[:-1] + '\\n")'
        print(f"Fixed line {i+1}: {lines[i]}")

# Write back the file
with open("/root/legal-corpus/scripts/fetch_bverfg_index.py", "w", encoding="utf-8") as f:
    f.write('\n'.join(lines))

print("BVerfG file fixed successfully")