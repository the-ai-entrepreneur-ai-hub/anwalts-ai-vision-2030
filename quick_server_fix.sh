#!/bin/bash
# Quick fix for portal-anwalts.ai server issues

echo "🔧 Quick Fix for Portal-Anwalts.AI Server"
echo "=========================================="

# Step 1: Create missing directories
echo "📁 Creating missing directories..."
mkdir -p /var/www/portal-anwalts.ai/frontend
mkdir -p /var/www/portal-anwalts.ai/backend
mkdir -p /var/log/nginx

# Step 2: Copy files from deployment
echo "📋 Copying files from deployment..."
cd /tmp/portal-anwalts-ai-deployment
cp -r frontend/* /var/www/portal-anwalts.ai/frontend/
cp -r backend/* /var/www/portal-anwalts.ai/backend/

# Step 3: Set correct permissions
echo "🔐 Setting permissions..."
chown -R www-data:www-data /var/www/portal-anwalts.ai
chmod -R 755 /var/www/portal-anwalts.ai

# Step 4: Create basic nginx config if missing
echo "🌐 Fixing nginx configuration..."
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

# Step 5: Enable site and test nginx
echo "⚙️ Enabling site..."
ln -sf /etc/nginx/sites-available/portal-anwalts.ai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Step 6: Test nginx config
echo "🧪 Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config is valid"
    systemctl restart nginx
    systemctl enable nginx
    echo "🚀 Nginx restarted successfully"
else
    echo "❌ Nginx config has errors"
    nginx -t
fi

# Step 7: Check if files exist
echo "📋 Checking deployed files..."
ls -la /var/www/portal-anwalts.ai/frontend/

# Step 8: Test the site
echo "🔍 Testing site..."
curl -I http://localhost

echo ""
echo "✅ Quick fix complete!"
echo "🔗 Test your site: http://portal-anwalts.ai"
echo "📱 Main app should be at: http://portal-anwalts.ai/"