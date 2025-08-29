#!/bin/bash
# Add admin user to USERS_DB in main.py

echo "🔧 Adding admin user to USERS_DB..."

# Backup original file
cp /var/www/portal-anwalts.ai/backend/main.py /var/www/portal-anwalts.ai/backend/main.py.backup

# Add the new admin user to USERS_DB
sed -i '/USERS_DB = {/,/}/ {
    /}/i \    "christopher.klaes@aigenex.de": {\
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # "admin123"\
        "email": "christopher.klaes@aigenex.de",\
        "name": "Dr. Markus Weigl"\
    },
}' /var/www/portal-anwalts.ai/backend/main.py

echo "✅ Admin user added to USERS_DB"
echo ""
echo "🔍 Verification:"
grep -A 4 "christopher.klaes@aigenex.de" /var/www/portal-anwalts.ai/backend/main.py

echo ""
echo "🔄 Restarting backend service..."
systemctl restart anwalts-ai-backend || echo "Manual restart may be needed"

echo "✅ Admin user setup complete!"
echo "📧 Email: christopher.klaes@aigenex.de"
echo "🔑 Password: admin123"