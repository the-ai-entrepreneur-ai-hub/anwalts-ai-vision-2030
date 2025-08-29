#!/bin/bash
# Fix Nginx to Proxy API Requests

echo "🔧 Fixing Nginx API Proxy..."

# Update nginx config to proxy API requests
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
    
    # API proxy to backend
    location /api/ {
        # Remove /api prefix when forwarding to backend
        rewrite ^/api/(.*)$ /$1 break;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept" always;
        add_header Access-Control-Allow-Credentials "true" always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # Direct backend proxy (for /login, /register, etc.)
    location ~ ^/(login|register|health|docs)$ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept" always;
        add_header Access-Control-Allow-Credentials "true" always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF

# Test nginx config
echo "🧪 Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config is valid"
    
    # Restart nginx
    echo "🔄 Restarting nginx..."
    systemctl reload nginx
    
    echo "✅ Nginx restarted successfully"
    
    # Test the API proxy
    echo "🧪 Testing API proxy..."
    
    # Test health endpoint through nginx
    echo "Testing health endpoint:"
    curl -s http://localhost/health || echo "Health endpoint failed"
    
    # Test login endpoint through nginx  
    echo ""
    echo "Testing login endpoint:"
    curl -s -X POST http://localhost/login \
        -H "Content-Type: application/json" \
        -d '{"email": "admin@portal-anwalts.ai", "password": "password"}' || echo "Login endpoint failed"
        
else
    echo "❌ Nginx config has errors"
    nginx -t
fi

echo ""
echo "🎉 Nginx proxy setup complete!"
echo ""
echo "✅ API endpoints now available through nginx:"
echo "  🔗 http://portal-anwalts.ai/login"
echo "  🔗 http://portal-anwalts.ai/health"
echo "  🔗 http://portal-anwalts.ai/register"
echo ""
echo "🔄 Please refresh browser and try login again!"