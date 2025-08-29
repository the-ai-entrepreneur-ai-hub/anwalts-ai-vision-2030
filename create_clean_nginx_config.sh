#!/bin/bash
# Create clean nginx config from scratch

echo "🔧 Creating clean nginx configuration..."

# Create clean nginx config
cat > /etc/nginx/sites-available/portal-anwalts.ai << 'EOF'
server {
    listen 80;
    server_name portal-anwalts.ai www.portal-anwalts.ai;
    
    root /var/www/portal-anwalts.ai/frontend;
    index index.html anwalts-ai-app.html;

    # Serve static files
    location / {
        try_files $uri $uri/ /anwalts-ai-app.html;
    }

    # Professional workspace paths
    location /workspace {
        try_files /legal-workspace.html =404;
    }
    
    location /legal-workspace {
        try_files /legal-workspace.html =404;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # Static file optimization
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/portal-anwalts.ai /etc/nginx/sites-enabled/

# Test and start nginx
nginx -t
if [ $? -eq 0 ]; then
    systemctl start nginx
    echo "✅ Nginx started successfully!"
else
    echo "❌ Nginx config test failed!"
fi

echo "✅ Clean nginx configuration created!"