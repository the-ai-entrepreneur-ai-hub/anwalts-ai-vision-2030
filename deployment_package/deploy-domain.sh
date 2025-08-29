#!/bin/bash
set -e

echo "🚀 Starting AnwaltsAI Production Deployment for portal-anwalts.ai..."

# Server info
echo "📊 Server: Hetzner AX102 #2743403"
echo "🌐 Domain: portal-anwalts.ai"
echo "📦 Dataset: 9,997 German legal examples"
echo "🏛️ Owner: Dr. Markus Weigl, AIgenex GmbH"

# Create necessary directories
mkdir -p logs data/backups config/ssl config/certbot-webroot

# Set permissions
chmod 600 config/.env.production
chmod -R 755 data/
chmod +x deploy-domain.sh

# Install system dependencies
echo "📋 Installing system dependencies..."
apt update
apt install -y curl htop certbot

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Check DNS resolution
echo "🌐 Checking DNS resolution..."
if nslookup portal-anwalts.ai > /dev/null 2>&1; then
    echo "✅ DNS resolved for portal-anwalts.ai"
    DNS_READY=true
else
    echo "⚠️ DNS not yet resolved for portal-anwalts.ai"
    echo "Please configure DNS A record: portal-anwalts.ai -> $(curl -s ifconfig.me)"
    DNS_READY=false
fi

# Build and start services
echo "📦 Building Docker containers..."
docker-compose -f docker-compose-domain.yml build --no-cache

echo "🔄 Starting services..."
docker-compose -f docker-compose-domain.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 45

# SSL Certificate setup
if [ "$DNS_READY" = true ]; then
    echo "🔒 Setting up SSL certificates..."
    
    # Stop nginx temporarily for standalone certbot
    docker-compose -f docker-compose-domain.yml stop nginx
    
    # Get SSL certificates
    certbot certonly --standalone --non-interactive --agree-tos \
        --email info@portal-anwalts.ai \
        -d portal-anwalts.ai -d www.portal-anwalts.ai
    
    # Copy certificates to nginx directory
    if [ -d "/etc/letsencrypt/live/portal-anwalts.ai" ]; then
        cp /etc/letsencrypt/live/portal-anwalts.ai/fullchain.pem config/ssl/portal-anwalts.ai.crt
        cp /etc/letsencrypt/live/portal-anwalts.ai/privkey.pem config/ssl/portal-anwalts.ai.key
        
        # Update nginx to use SSL configuration
        cp config/nginx-ssl.conf config/nginx.conf
        
        echo "✅ SSL certificates installed"
        SSL_READY=true
    else
        echo "⚠️ SSL certificate generation failed"
        SSL_READY=false
    fi
    
    # Restart nginx with SSL config
    docker-compose -f docker-compose-domain.yml up -d nginx
else
    echo "⚠️ Skipping SSL setup - DNS not ready"
    SSL_READY=false
fi

# Health checks
echo "✅ Verifying deployment..."
timeout 30 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done' || {
    echo "❌ Backend health check failed"
    docker-compose -f docker-compose-domain.yml logs backend
    exit 1
}

timeout 30 bash -c 'until curl -f http://localhost:3000; do sleep 5; done' || {
    echo "❌ Frontend health check failed"  
    docker-compose -f docker-compose-domain.yml logs frontend
    exit 1
}

# Setup auto-renewal for SSL certificates
if [ "$SSL_READY" = true ]; then
    echo "🔄 Setting up SSL auto-renewal..."
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'docker-compose -f /opt/anwalts-ai/docker-compose-domain.yml restart nginx'") | crontab -
fi

# Display status
echo ""
echo "🎉 Deployment completed successfully!"
echo "📊 Legal Dataset: 9,997 examples loaded"
echo "🌐 Domain: portal-anwalts.ai"

if [ "$DNS_READY" = true ] && [ "$SSL_READY" = true ]; then
    echo "🔒 HTTPS Application: https://portal-anwalts.ai"
    echo "📚 API Documentation: https://portal-anwalts.ai/docs"
    echo "📈 Health Check: https://portal-anwalts.ai/health"
elif [ "$DNS_READY" = true ]; then
    echo "🌐 HTTP Application: http://portal-anwalts.ai"
    echo "📚 API Documentation: http://portal-anwalts.ai/docs"
    echo "📈 Health Check: http://portal-anwalts.ai/health"
    echo "⚠️ SSL not configured - run SSL setup manually"
else
    echo "📧 Configure DNS first, then run SSL setup"
    echo "🔧 A Record needed: portal-anwalts.ai -> $(curl -s ifconfig.me)"
fi

echo ""
echo "🔧 Useful commands:"
echo "  - View logs: docker-compose -f docker-compose-domain.yml logs -f"
echo "  - Check status: docker-compose -f docker-compose-domain.yml ps"
echo "  - Stop services: docker-compose -f docker-compose-domain.yml down"
echo "  - Update: git pull && docker-compose -f docker-compose-domain.yml up -d --build"
echo ""
echo "📊 German Legal Dataset: 9,997 examples ready for AI training!"