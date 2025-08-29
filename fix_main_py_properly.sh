#!/bin/bash
# Fix main.py properly by adding admin user correctly

echo "🔧 Fixing main.py properly..."

# Replace the USERS_DB section completely
cat > /tmp/users_db_section.py << 'EOF'
# Simple user storage (in production, use proper database)
USERS_DB = {
    "admin@portal-anwalts.ai": {
        "password_hash": "REDACTED",  # "password"
        "email": "admin@portal-anwalts.ai",
        "name": "Admin User"
    },
    "christopher.klaes@aigenex.de": {
        "password_hash": "REDACTED",  # "admin123"
        "email": "christopher.klaes@aigenex.de",
        "name": "Dr. Markus Weigl"
    },
    "test@example.com": {
        "password_hash": "REDACTED",  # "secret123"
        "email": "test@example.com", 
        "name": "Test User"
    }
}
EOF

# Replace the USERS_DB section in main.py
sed -i '/# Simple user storage/,/^}/c\
# Simple user storage (in production, use proper database)\
USERS_DB = {\
    "admin@portal-anwalts.ai": {\
        "password_hash": "REDACTED",  # "password"\
        "email": "admin@portal-anwalts.ai",\
        "name": "Admin User"\
    },\
    "christopher.klaes@aigenex.de": {\
        "password_hash": "REDACTED",  # "admin123"\
        "email": "christopher.klaes@aigenex.de",\
        "name": "Dr. Markus Weigl"\
    },\
    "test@example.com": {\
        "password_hash": "REDACTED",  # "secret123"\
        "email": "test@example.com", \
        "name": "Test User"\
    }\
}' /var/www/portal-anwalts.ai/backend/main.py

echo "✅ main.py fixed!"

# Test syntax
echo "🔍 Testing Python syntax..."
cd /var/www/portal-anwalts.ai/backend
python3 -m py_compile main.py
if [ $? -eq 0 ]; then
    echo "✅ Python syntax is valid!"
else
    echo "❌ Python syntax error!"
    exit 1
fi

echo "🔄 Restarting backend..."
pkill -f 'python.*main.py'
sleep 2
nohup python3 main.py > /var/log/anwalts-backend.log 2>&1 &
sleep 3

echo "✅ Backend restarted with admin user!"