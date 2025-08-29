#!/bin/bash
# Fix API Client to use nginx proxy instead of direct backend

echo "🔧 Updating API Client to use nginx proxy..."

# Update API client to use /api/ prefix through nginx proxy
sed -i 's|http://portal-anwalts.ai:8000|https://portal-anwalts.ai/api|g' /var/www/portal-anwalts.ai/frontend/api-client.js
sed -i 's|http://127.0.0.1:8000|http://portal-anwalts.ai/api|g' /var/www/portal-anwalts.ai/frontend/api-client.js

echo "✅ API Client updated to use proxy"

echo "🧪 Checking updated configuration..."
grep -n "baseUrl.*api" /var/www/portal-anwalts.ai/frontend/api-client.js

echo ""
echo "🎯 API Client now configured for:"
echo "  🌐 Production: http://portal-anwalts.ai/api"
echo "  📡 Proxied to: http://127.0.0.1:8000"
echo ""
echo "🔄 This should work through port 80!"