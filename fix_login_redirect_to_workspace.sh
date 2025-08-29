#!/bin/bash
# Fix login redirect to use /workspace professional URL

echo "🔧 Updating login redirect to professional /workspace URL..."

# Update the redirect in anwalts-ai-app.html to use /workspace
echo "1️⃣ Changing redirect from legal-workspace.html to /workspace..."
sed -i "s|window.location.href = 'legal-workspace.html'|window.location.href = '/workspace'|g" /var/www/portal-anwalts.ai/frontend/anwalts-ai-app.html

# Verify the change
echo "2️⃣ Verification:"
grep -n -A2 -B2 "/workspace" /var/www/portal-anwalts.ai/frontend/anwalts-ai-app.html | grep "window.location"

echo ""
echo "✅ Login redirect updated!"
echo "🎯 Login now redirects to: https://portal-anwalts.ai/workspace"
echo "🏢 Professional clean URL instead of filename"