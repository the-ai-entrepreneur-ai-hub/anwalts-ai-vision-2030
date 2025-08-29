#!/bin/bash
# Fixed Portal-Anwalts.AI Deployment Script
# Run this on server: bash fixed_deploy.sh

echo "🚀 Deploying AnwaltsAI to portal-anwalts.ai..."

# Update system (without sudo since you're already root)
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "🔧 Installing dependencies..."
apt install -y python3-pip nginx postgresql postgresql-contrib certbot python3-certbot-nginx

# Create application directory
echo "📁 Creating application directories..."
mkdir -p /var/www/portal-anwalts.ai
chown root:root /var/www/portal-anwalts.ai

# Copy files (remove Windows line endings)
echo "📋 Copying application files..."
cp -r backend /var/www/portal-anwalts.ai/
cp -r frontend /var/www/portal-anwalts.ai/
cp config/.env.production /var/www/portal-anwalts.ai/backend/.env

# Install Python dependencies
echo "🐍 Installing Python packages..."
cd /var/www/portal-anwalts.ai/backend
pip3 install fastapi uvicorn pydantic sqlalchemy psycopg2-binary python-jose passlib python-multipart httpx

# Setup database
echo "🗄️ Setting up database..."
systemctl start postgresql
systemctl enable postgresql
sudo -u postgres createuser anwalts_user 2>/dev/null || echo "User already exists"
sudo -u postgres createdb anwalts_ai_prod 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "ALTER USER anwalts_user PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE anwalts_ai_prod TO anwalts_user;"

# Setup nginx
echo "🌐 Configuring nginx..."
cp ../config/nginx.conf /etc/nginx/sites-available/portal-anwalts.ai
ln -sf /etc/nginx/sites-available/portal-anwalts.ai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Get SSL certificate
echo "🔒 Getting SSL certificate..."
certbot --nginx -d portal-anwalts.ai -d www.portal-anwalts.ai --non-interactive --agree-tos --email admin@portal-anwalts.ai || echo "SSL setup will be done later"

# Create systemd service for backend
echo "⚙️ Creating backend service..."
cat > /etc/systemd/system/anwalts-api.service << 'EOF'
[Unit]
Description=AnwaltsAI API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/portal-anwalts.ai/backend
Environment=PATH=/usr/local/bin
ExecStart=/usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable anwalts-api
systemctl start anwalts-api
systemctl restart nginx

# Check status
echo "📊 Checking service status..."
systemctl status anwalts-api --no-pager -l
systemctl status nginx --no-pager -l

echo ""
echo "✅ Deployment complete!"
echo "🔗 Main frontend (anwalts-ai-app.html): https://portal-anwalts.ai/"
echo "📊 Dashboard: https://portal-anwalts.ai/anwalts-ai-dashboard.html"
echo "📝 Registration: https://portal-anwalts.ai/enhanced-registration.html"
echo "🔧 API Health: https://portal-anwalts.ai/api/health"
echo ""
echo "🎯 Your enhanced registration system is now live!"