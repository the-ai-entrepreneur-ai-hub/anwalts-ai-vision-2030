#!/bin/bash
# Fix main.py properly by adding admin user correctly

echo "🔧 Fixing main.py properly..."

# Replace the USERS_DB section completely
cat > /tmp/users_db_section.py << 'EOF'
# Simple user storage (in production, use proper database)
USERS_DB = {
    "admin@portal-anwalts.ai": {
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
        "email": "admin@portal-anwalts.ai",
        "name": "Admin User"
    },
    "christopher.klaes@aigenex.de": {
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # "admin123"
        "email": "christopher.klaes@aigenex.de",
        "name": "Dr. Markus Weigl"
    },
    "test@example.com": {
        "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # "secret123"
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
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"\
        "email": "admin@portal-anwalts.ai",\
        "name": "Admin User"\
    },\
    "christopher.klaes@aigenex.de": {\
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # "admin123"\
        "email": "christopher.klaes@aigenex.de",\
        "name": "Dr. Markus Weigl"\
    },\
    "test@example.com": {\
        "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # "secret123"\
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