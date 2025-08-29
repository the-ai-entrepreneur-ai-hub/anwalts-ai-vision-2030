#!/bin/bash
# Deploy navigation authentication fix

echo "🔧 Deploying navigation authentication fix..."

# Copy the fix script to the frontend
cp /tmp/fix_navigation_auth_issue.js /var/www/portal-anwalts.ai/frontend/

echo "1️⃣ Adding navigation auth fix to legal-workspace.html..."
# Add the fix script to the workspace HTML - load it early in head section
sed -i '/<script src="crypto-polyfill.js"><\/script>/a\    <script src="fix_navigation_auth_issue.js"></script>' /var/www/portal-anwalts.ai/frontend/legal-workspace.html

echo "2️⃣ Adding navigation auth fix to main app..."  
# Also add to main app for consistency
sed -i '/<script src="crypto-polyfill.js"><\/script>/a\    <script src="fix_navigation_auth_issue.js"></script>' /var/www/portal-anwalts.ai/frontend/anwalts-ai-app.html

echo "3️⃣ Verification..."
echo "Navigation fix script added to:"
grep -l "fix_navigation_auth_issue.js" /var/www/portal-anwalts.ai/frontend/*.html

echo ""
echo "✅ Navigation authentication fix deployed!"
echo "🔄 Browser back/forward navigation should now maintain session"
echo "🛡️ Only redirects to login when session is actually invalid"

# Set proper permissions
chmod 644 /var/www/portal-anwalts.ai/frontend/fix_navigation_auth_issue.js
chown www-data:www-data /var/www/portal-anwalts.ai/frontend/fix_navigation_auth_issue.js