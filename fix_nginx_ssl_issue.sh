#!/bin/bash
# Fix nginx SSL certificate issue

echo "🔧 Fixing nginx SSL certificate issue..."

# Remove any existing nginx configs that reference SSL
echo "📝 Cleaning up nginx configs..."
rm -f /etc/nginx/sites-enabled/*

# Create HTTP-only config (no SSL)
echo "🌐 Creating HTTP-only nginx config..."
cat > /etc/nginx/sites-available/portal-anwalts.ai << 'EOF'
server {
    listen 80;
    server_name portal-anwalts.ai www.portal-anwalts.ai;
    
    root /var/www/portal-anwalts.ai/frontend;
    index anwalts-ai-app.html;
    
    location / {
        try_files $uri $uri/ /anwalts-ai-app.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
echo "⚙️ Enabling site..."
ln -sf /etc/nginx/sites-available/portal-anwalts.ai /etc/nginx/sites-enabled/

# Test nginx config
echo "🧪 Testing nginx configuration..."
nginx -t

echo "✅ Nginx config should be working now!"