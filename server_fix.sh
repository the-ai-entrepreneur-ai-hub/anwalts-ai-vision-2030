#!/bin/bash
# Direct server commands to fix the backend

echo "Uploading navigation fix..."
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null fix_navigation_auth_issue.js root@148.251.195.222:/var/www/portal-anwalts.ai/frontend/

echo "Connecting to server to restart backend..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@148.251.195.222 << 'EOF'
echo "Killing existing backend processes..."
pkill -f uvicorn

echo "Starting backend with Together API key..."
cd /var/www/portal-anwalts.ai/backend
export TOGETHER_API_KEY=5b5174dc42932c781810d4be36a11435fe07cdf2d95b8cac17c29c7f87e10720
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &

sleep 5
echo "Backend started. Checking processes..."
ps aux | grep uvicorn | grep -v grep

echo "Testing health endpoint..."
curl -X GET http://localhost:8000/health
EOF

echo "Server fixes complete!"