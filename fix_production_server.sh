#!/bin/bash

# AnwaltsAI Production Server Fix Script
# Server: 148.251.195.222
# Purpose: Fix HTTPS configuration and service issues

echo "=========================================="
echo "AnwaltsAI Production Server Fix Script"
echo "=========================================="

# Check current status
echo "1. Checking system status..."
uptime
free -h
df -h

echo ""
echo "2. Checking Docker containers..."
docker ps -a

echo ""
echo "3. Checking nginx status..."
systemctl status nginx --no-pager

echo ""
echo "4. Checking SSL certificate files..."
ls -la /etc/nginx/ssl/ 2>/dev/null || echo "SSL directory not found at /etc/nginx/ssl/"
ls -la /etc/ssl/certs/anwalts* 2>/dev/null || echo "SSL certificates not found in standard location"
ls -la /opt/anwalts-ai-production/ssl/ 2>/dev/null || echo "SSL directory not found in project"

echo ""
echo "5. Checking nginx configuration..."
nginx -t

echo ""
echo "6. Checking current nginx config files..."
ls -la /etc/nginx/sites-available/
ls -la /etc/nginx/sites-enabled/
cat /etc/nginx/sites-available/anwalts-ai 2>/dev/null || echo "anwalts-ai config not found"

echo ""
echo "7. Checking port bindings..."
netstat -tlnp | grep -E ':80|:443|:22'

echo ""
echo "8. Checking firewall status..."
ufw status verbose 2>/dev/null || iptables -L -n

echo ""
echo "9. Checking docker-compose status..."
cd /opt/anwalts-ai-production/
docker-compose ps
docker-compose logs --tail=50 backend
docker-compose logs --tail=50 nginx

echo ""
echo "10. Fixing HTTPS configuration..."

# Create SSL directory if it doesn't exist
mkdir -p /opt/anwalts-ai-production/ssl

# Check if SSL certificates exist
if [ ! -f "/opt/anwalts-ai-production/ssl/anwalts-ai.crt" ] || [ ! -f "/opt/anwalts-ai-production/ssl/anwalts-ai.key" ]; then
    echo "SSL certificates missing. Creating self-signed certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /opt/anwalts-ai-production/ssl/anwalts-ai.key \
        -out /opt/anwalts-ai-production/ssl/anwalts-ai.crt \
        -subj "/C=DE/ST=NRW/L=Dusseldorf/O=AnwaltsAI/CN=anwalts-ai.com"
    chmod 600 /opt/anwalts-ai-production/ssl/anwalts-ai.key
    chmod 644 /opt/anwalts-ai-production/ssl/anwalts-ai.crt
fi

# Create proper nginx configuration
cat > /etc/nginx/sites-available/anwalts-ai << 'EOF'
server {
    listen 80;
    server_name anwalts-ai.com www.anwalts-ai.com 148.251.195.222;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name anwalts-ai.com www.anwalts-ai.com 148.251.195.222;
    
    # SSL Configuration
    ssl_certificate /opt/anwalts-ai-production/ssl/anwalts-ai.crt;
    ssl_certificate_key /opt/anwalts-ai-production/ssl/anwalts-ai.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Document root
    root /opt/anwalts-ai-production/Client;
    index anwalts-ai-dashboard.html;
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Static files
    location / {
        try_files $uri $uri/ /anwalts-ai-dashboard.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Handle specific file types
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/anwalts-ai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo ""
echo "11. Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid. Restarting services..."
    
    # Restart services
    systemctl restart nginx
    cd /opt/anwalts-ai-production/
    docker-compose restart
    
    echo ""
    echo "12. Verifying services after restart..."
    sleep 5
    systemctl status nginx --no-pager
    docker-compose ps
    
    echo ""
    echo "13. Testing endpoints..."
    curl -I http://localhost
    curl -I -k https://localhost
    
else
    echo "Nginx configuration has errors. Please check the configuration manually."
fi

echo ""
echo "14. Opening necessary firewall ports..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw reload 2>/dev/null || echo "UFW not available, checking iptables..."

echo ""
echo "Fix script completed!"
echo "Please test:"
echo "- HTTP: http://148.251.195.222"
echo "- HTTPS: https://148.251.195.222"