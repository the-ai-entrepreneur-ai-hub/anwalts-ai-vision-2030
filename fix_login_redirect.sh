#!/bin/bash
# Fix login redirect to use new professional workspace URL

echo "🔧 Fixing login redirect URLs..."

# Fix redirect in main app
echo "1️⃣ Updating anwalts-ai-app.html redirect..."
sed -i "s|window.location.href = 'anwalts-ai-dashboard.html'|window.location.href = 'legal-workspace.html'|g" /var/www/portal-anwalts.ai/frontend/anwalts-ai-app.html

# Also check for any other dashboard references and fix them
sed -i "s|anwalts-ai-dashboard.html|legal-workspace.html|g" /var/www/portal-anwalts.ai/frontend/anwalts-ai-app.html

# Create redirect for old URL to new URL (nginx redirect)
echo "2️⃣ Creating nginx redirect for old dashboard URL..."

# Add redirect to nginx config
sed -i '/location \/workspace/i\
    # Redirect old dashboard URL to new workspace\
    location /anwalts-ai-dashboard.html {\
        return 301 https://$server_name/legal-workspace.html;\
    }\
' /etc/nginx/sites-available/portal-anwalts.ai

# Test and reload nginx
nginx -t && systemctl reload nginx

echo "3️⃣ Verification:"
echo "Checking redirect URLs in app:"
grep -n "legal-workspace.html" /var/www/portal-anwalts.ai/frontend/anwalts-ai-app.html

echo ""
echo "✅ Login redirect fixed!"
echo "🔄 Login now redirects to: legal-workspace.html"
echo "🌐 Old dashboard URL redirects to new workspace"