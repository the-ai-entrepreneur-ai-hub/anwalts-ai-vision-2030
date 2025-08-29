#!/bin/bash
# Fix API Client to use correct production URL

echo "🔧 Fixing API Client URL for portal-anwalts.ai..."

# Update the API client to use portal-anwalts.ai for production
sed -i 's|http://127.0.0.1:8000|http://portal-anwalts.ai:8000|g' /var/www/portal-anwalts.ai/frontend/api-client.js

echo "✅ API Client URL updated"

echo "🧪 Checking updated configuration..."
grep -n "baseUrl.*8000" /var/www/portal-anwalts.ai/frontend/api-client.js

echo ""
echo "🎯 API Client now configured for:"
echo "  🌐 Production: http://portal-anwalts.ai:8000"
echo ""
echo "🔄 Browser should now connect directly to backend!"
echo "Refresh browser (Ctrl+F5) and try login again."