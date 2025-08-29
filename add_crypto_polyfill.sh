#!/bin/bash
# Add crypto polyfill to HTML files

echo "🔧 Adding crypto polyfill to HTML files..."

# Add polyfill script tag to HTML files
for file in /var/www/portal-anwalts.ai/frontend/*.html; do
    if [[ -f "$file" ]]; then
        echo "Processing: $(basename "$file")"
        
        # Check if polyfill already exists
        if grep -q "crypto-polyfill.js" "$file"; then
            echo "  ✅ Polyfill already exists in $(basename "$file")"
        else
            # Add polyfill before the closing </head> tag
            sed -i '/<\/head>/i\    <script src="crypto-polyfill.js"></script>' "$file"
            echo "  ✅ Added polyfill to $(basename "$file")"
        fi
    fi
done

echo ""
echo "✅ Crypto polyfill added to all HTML files!"
echo ""
echo "🔍 Verification:"
grep -n "crypto-polyfill.js" /var/www/portal-anwalts.ai/frontend/*.html || echo "No polyfill references found"