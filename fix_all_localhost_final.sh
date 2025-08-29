#!/bin/bash
# Fix ALL localhost references in frontend files

echo "🚨 FIXING ALL LOCALHOST REFERENCES - FINAL FIX"

# Fix config.js
echo "1️⃣ Fixing config.js..."
sed -i "s|local: 'http://127.0.0.1:8000'|local: window.location.origin + '/api'|g" /var/www/portal-anwalts.ai/frontend/config.js

# Fix HTML hardcoded API client
echo "2️⃣ Fixing HTML hardcoded API client..."
sed -i "s|new AnwaltsAIApiClient('http://127.0.0.1:8000')|new AnwaltsAIApiClient()|g" /var/www/portal-anwalts.ai/frontend/anwalts-ai-app.html

# Fix dashboard direct fetch
echo "3️⃣ Fixing dashboard direct fetch..."
sed -i "s|'http://127.0.0.1:8000/api/ai/|window.location.origin + '/api/ai/|g" /var/www/portal-anwalts.ai/frontend/anwalts-ai-dashboard.html

echo "✅ All localhost references fixed!"
echo ""
echo "🔍 Verification:"
echo "Config.js:"
grep -n "local:" /var/www/portal-anwalts.ai/frontend/config.js
echo ""
echo "HTML hardcoded clients:"
grep -n "new AnwaltsAIApiClient" /var/www/portal-anwalts.ai/frontend/*.html
echo ""
echo "Direct fetches:"
grep -n "127.0.0.1" /var/www/portal-anwalts.ai/frontend/*.html || echo "No more 127.0.0.1 references!"

echo ""
echo "🎯 REFRESH BROWSER WITH CTRL+SHIFT+R TO CLEAR CACHE!"