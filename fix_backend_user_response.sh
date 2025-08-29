#!/bin/bash
# Fix backend to return complete user data including role

echo "🔧 Updating backend user response..."

# Update the login endpoint to return role information
sed -i '/Login successful/,/}/c\
            return {\
                "success": True,\
                "message": "Login successful",\
                "user": {\
                    "email": user_data["email"],\
                    "name": user_data["name"],\
                    "role": "admin",\
                    "initials": "MW"\
                }\
            }' /var/www/portal-anwalts.ai/backend/main.py

echo "✅ Backend updated to return role and initials"

# Restart backend
pkill -f python3
sleep 2
cd /var/www/portal-anwalts.ai/backend
nohup python3 main.py > /var/log/anwalts-backend.log 2>&1 &
sleep 3

echo "🔍 Testing updated response..."
curl -X POST http://127.0.0.1:8000/login -H 'Content-Type: application/json' -d '{"email":"christopher.klaes@aigenex.de","password":"Kanzlei2025#"}'