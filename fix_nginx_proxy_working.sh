#!/bin/bash
# Fix Nginx Proxy for API - Working Version

echo "🔧 Setting up working nginx proxy..."

# First, let's check if backend is running
echo "🔍 Checking backend status..."
systemctl status anwalts-api --no-pager || echo "Backend may not be running"

# Test backend directly
echo "Testing backend directly:"
curl -s http://127.0.0.1:8000/health && echo " ✅ Backend responding" || echo " ❌ Backend not responding"

# Create working nginx config
cat > /etc/nginx/sites-available/portal-anwalts.ai << 'EOF'
server {
    listen 80;
    server_name portal-anwalts.ai www.portal-anwalts.ai;
    
    root /var/www/portal-anwalts.ai/frontend;
    index anwalts-ai-app.html;
    
    # Frontend static files
    location / {
        try_files $uri $uri/ /anwalts-ai-app.html;
    }
    
    # Proxy ALL /api/* requests to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Add CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }
}
EOF

# Test and reload nginx
echo "🧪 Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config valid, reloading..."
    systemctl reload nginx
    
    # Test the proxy
    echo "🧪 Testing API proxy through nginx..."
    curl -H "Host: portal-anwalts.ai" http://localhost/api/health && echo " ✅ Proxy working" || echo " ❌ Proxy failed"
    
else
    echo "❌ Nginx config error:"
    nginx -t
fi

echo ""
echo "✅ Setup complete!"
echo "🔗 API should now be available at: http://portal-anwalts.ai/api/*"