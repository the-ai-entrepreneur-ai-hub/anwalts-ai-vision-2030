#!/bin/bash
# Fix nginx configuration properly

echo "🔧 Fixing nginx configuration..."

# Restore backup and fix properly
cp /etc/nginx/sites-available/portal-anwalts.ai.backup /etc/nginx/sites-available/portal-anwalts.ai

# Add workspace locations inside the server block
sed -i '/location \/ {/i\
    # Professional workspace paths\
    location /workspace {\
        alias /var/www/portal-anwalts.ai/frontend;\
        try_files /legal-workspace.html =404;\
    }\
    \
    location /legal-workspace {\
        alias /var/www/portal-anwalts.ai/frontend;\
        try_files /legal-workspace.html =404;\
    }\
' /etc/nginx/sites-available/portal-anwalts.ai

echo "✅ Nginx config fixed!"

# Test and reload nginx
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✅ Nginx reloaded successfully!"
else
    echo "❌ Nginx config test failed!"
    cp /etc/nginx/sites-available/portal-anwalts.ai.backup /etc/nginx/sites-available/portal-anwalts.ai
    systemctl reload nginx
fi

# Test the document generation endpoint
echo "🔍 Testing document generation endpoint..."
sleep 3
curl -X POST http://127.0.0.1:8000/api/ai/generate-document-simple \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test Document","document_type":"contract","prompt":"Create a test contract"}'