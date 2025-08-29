#!/bin/bash
# Change password for christopher.klaes@aigenex.de to Kanzlei2025#

echo "🔑 Changing admin password..."

# Generate new password hash
NEW_HASH=$(python3 -c "import hashlib; print(hashlib.sha256('Kanzlei2025#'.encode()).hexdigest())")
echo "New password hash: $NEW_HASH"

# Backup current main.py
cp /var/www/portal-anwalts.ai/backend/main.py /var/www/portal-anwalts.ai/backend/main.py.backup2

# Replace the password hash for christopher.klaes@aigenex.de
sed -i "/christopher\.klaes@aigenex\.de/,/}/s/\"password_hash\": \"[^\"]*\"/\"password_hash\": \"$NEW_HASH\"/" /var/www/portal-anwalts.ai/backend/main.py

echo "✅ Password hash updated in main.py"

# Verify the change
echo "🔍 Verification:"
grep -A 4 "christopher.klaes@aigenex.de" /var/www/portal-anwalts.ai/backend/main.py

echo ""
echo "🔄 Restarting backend..."
pkill -f 'python.*main.py'
sleep 2
cd /var/www/portal-anwalts.ai/backend
nohup python3 main.py > /var/log/anwalts-backend.log 2>&1 &
sleep 3

echo "✅ Password changed successfully!"
echo "📧 Email: christopher.klaes@aigenex.de"
echo "🔑 New Password: Kanzlei2025#"