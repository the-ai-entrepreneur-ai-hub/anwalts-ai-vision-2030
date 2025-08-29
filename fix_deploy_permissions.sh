#!/bin/bash
# Fix deployment script permissions

echo "🔧 Fixing deploy.sh permissions..."

# Make the script executable
chmod +x /tmp/portal-anwalts-ai-deployment/scripts/deploy.sh

# Verify permissions
ls -la /tmp/portal-anwalts-ai-deployment/scripts/deploy.sh

echo "✅ Permissions fixed! Now you can run: ./deploy.sh"