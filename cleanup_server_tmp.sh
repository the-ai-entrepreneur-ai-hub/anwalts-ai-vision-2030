#!/bin/bash
# Server Cleanup Script for /tmp directory

echo "🧹 Cleaning up /tmp directory on server..."

# Safe cleanup - only remove specific files, keep system files
cd /tmp

# Remove deployment files
echo "Removing old deployment files..."
rm -rf backend config frontend docs
rm -f deploy-domain.sh deploy.sh docker-compose.production.yml
rm -f DEPLOYMENT_GUIDE.md README.md
rm -f portal-anwalts-ai-production-deployment.zip
rm -f *.tmp
rm -rf data

# Keep systemd and system files (they start with systemd-private)
echo "Keeping system files (systemd-private-*)"

# Show what remains
echo "📋 Remaining files in /tmp:"
ls -la /tmp/

echo "✅ Cleanup complete!"