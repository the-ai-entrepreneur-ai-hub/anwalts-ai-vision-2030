#!/usr/bin/env python3
"""
Remote Python file syntax fixer
Fixes unterminated string literals in Python scraper files
"""

import sys

def fix_bgh_file():
    """Fix fetch_bgh_juris.py"""
    try:
        with open("/root/legal-corpus/scripts/fetch_bgh_juris.py", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Find and fix the problematic line
        for i, line in enumerate(lines):
            if 'f.write(json.dumps(rec, ensure_ascii=False) + "' in line and line.rstrip().endswith('"'):
                # Fix the unterminated string
                lines[i] = '                f.write(json.dumps(rec, ensure_ascii=False) + "\\n")\\n'
                print(f"Fixed BGH line {i+1}")
                break
        
        with open("/root/legal-corpus/scripts/fetch_bgh_juris.py", "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("BGH file fixed successfully")
        return True
    except Exception as e:
        print(f"Error fixing BGH file: {e}")
        return False

def fix_bverfg_file():
    """Fix fetch_bverfg_index.py"""
    try:
        with open("/root/legal-corpus/scripts/fetch_bverfg_index.py", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        fixed_count = 0
        for i, line in enumerate(lines):
            # Fix txt = " line
            if line.strip() == 'txt = "':
                lines[i] = '    txt = "\\n"\\n'
                print(f"Fixed BVerfG line {i+1}: txt assignment")
                fixed_count += 1
            # Fix f.write line
            elif 'f.write(json.dumps(rec, ensure_ascii=False) + "' in line and line.rstrip().endswith('"'):
                lines[i] = '            f.write(json.dumps(rec, ensure_ascii=False) + "\\n")\\n'
                print(f"Fixed BVerfG line {i+1}: f.write statement")
                fixed_count += 1
        
        with open("/root/legal-corpus/scripts/fetch_bverfg_index.py", "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"BVerfG file fixed successfully ({fixed_count} fixes)")
        return True
    except Exception as e:
        print(f"Error fixing BVerfG file: {e}")
        return False

if __name__ == "__main__":
    print("Starting Python syntax fixes...")
    
    bgh_ok = fix_bgh_file()
    bverfg_ok = fix_bverfg_file()
    
    if bgh_ok and bverfg_ok:
        print("All files fixed successfully!")
        sys.exit(0)
    else:
        print("Some files failed to fix")
        sys.exit(1)