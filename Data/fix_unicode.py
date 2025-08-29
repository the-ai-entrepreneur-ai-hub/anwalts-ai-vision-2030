#!/usr/bin/env python3
"""Fix Unicode issues in the training script"""

import re

# Read the file
with open('train_with_our_dataset.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all emojis and non-ASCII characters except German umlauts in strings
def fix_unicode(text):
    # Replace emojis with empty string
    emoji_pattern = re.compile("[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]|[\u2600-\u26FF]|[\u2700-\u27BF]")
    text = emoji_pattern.sub('', text)
    
    # Fix common emoji replacements
    replacements = {
        '📦': '',
        '✅': '',
        '⚠️': '',
        '📚': '',
        '📁': '',
        '📊': '',
        '📋': '',
        '🔄': '',
        '📝': '',
        '🏋️': '',
        '🔤': '',
        '🚀': '',
        '⏱️': '',
        '🎯': '',
        '💾': '',
        '❌': '',
        '🧪': '',
        '🔍': '',
        '🎉': '',
        '🤖': '',
        '🔢': '',
        '🎛️': '',
        '🏆': '',
    }
    
    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)
    
    return text

# Fix the content
fixed_content = fix_unicode(content)

# Write back
with open('train_with_our_dataset.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Unicode issues fixed!")