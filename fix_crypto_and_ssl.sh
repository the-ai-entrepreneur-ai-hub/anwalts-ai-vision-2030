#!/bin/bash
# Fix crypto polyfill loading and add SSL certificate

echo "🔧 Fixing crypto polyfill and SSL..."

# 1. Fix crypto polyfill loading order - must be in HEAD before any other scripts
echo "1️⃣ Fixing crypto polyfill loading order..."

# Remove existing crypto-polyfill references
sed -i '/crypto-polyfill\.js/d' /var/www/portal-anwalts.ai/frontend/legal-workspace.html

# Add crypto polyfill at the very beginning of HEAD section, before any other scripts
sed -i '/<head>/a\    <script src="crypto-polyfill.js"></script>' /var/www/portal-anwalts.ai/frontend/legal-workspace.html

# 2. Install and configure SSL certificate
echo "2️⃣ Installing SSL certificate..."

# Install certbot
apt update
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d portal-anwalts.ai -d www.portal-anwalts.ai --non-interactive --agree-tos --email christopher.klaes@aigenex.de

# If certbot fails, create a self-signed certificate as fallback
if [ $? -ne 0 ]; then
    echo "📋 Creating self-signed certificate as fallback..."
    
    # Create SSL directory
    mkdir -p /etc/ssl/certs /etc/ssl/private
    
    # Generate self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/portal-anwalts.ai.key \
        -out /etc/ssl/certs/portal-anwalts.ai.crt \
        -subj "/C=DE/ST=State/L=City/O=AnwaltsAI/OU=IT/CN=portal-anwalts.ai"
    
    # Update nginx config for HTTPS
    cat > /etc/nginx/sites-available/portal-anwalts.ai << 'EOF'
server {
    listen 80;
    server_name portal-anwalts.ai www.portal-anwalts.ai;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name portal-anwalts.ai www.portal-anwalts.ai;
    
    ssl_certificate /etc/ssl/certs/portal-anwalts.ai.crt;
    ssl_certificate_key /etc/ssl/private/portal-anwalts.ai.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
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
fi

# Test and reload nginx
nginx -t && systemctl reload nginx

echo "3️⃣ Verifying fixes..."
echo "🔍 Crypto polyfill position:"
grep -n -A2 -B2 "crypto-polyfill" /var/www/portal-anwalts.ai/frontend/legal-workspace.html | head -5

echo ""
echo "✅ Fixes applied!"
echo "🌐 Site should now be secure: https://portal-anwalts.ai"
echo "🔧 Crypto polyfill loads first in HEAD section"