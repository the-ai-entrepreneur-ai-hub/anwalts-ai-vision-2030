#!/bin/bash

# Emergency HTTPS Fix for AnwaltsAI Production Server
# This script should be run directly on the server console

echo "=========================================="
echo "Emergency HTTPS Fix for AnwaltsAI"
echo "=========================================="

# Check if we're running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Go to production directory
cd /opt/anwalts-ai-production/

echo "1. Current system status:"
echo "========================="
systemctl is-active nginx
systemctl is-active docker
docker-compose ps 2>/dev/null || echo "Docker compose not running"

echo ""
echo "2. Current nginx ports:"
echo "======================"
netstat -tlnp | grep nginx || netstat -tlnp | grep :80

echo ""
echo "3. Checking SSL directory:"
echo "========================="
ls -la ssl/ 2>/dev/null || mkdir -p ssl

echo ""
echo "4. Creating self-signed SSL certificate:"
echo "======================================="
if [ ! -f "ssl/anwalts-ai.crt" ] || [ ! -f "ssl/anwalts-ai.key" ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/anwalts-ai.key \
        -out ssl/anwalts-ai.crt \
        -subj "/C=DE/ST=NRW/L=Dusseldorf/O=AnwaltsAI/CN=148.251.195.222"
    
    chmod 600 ssl/anwalts-ai.key
    chmod 644 ssl/anwalts-ai.crt
    echo "SSL certificates created successfully"
else
    echo "SSL certificates already exist"
fi

echo ""
echo "5. Updating nginx configuration:"
echo "==============================="

# Backup current config
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null

# Create new nginx configuration
cat > /etc/nginx/sites-available/anwalts-ai << 'EOF'
# HTTP Server - Redirect to HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name _;
    
    # SSL Configuration
    ssl_certificate /opt/anwalts-ai-production/ssl/anwalts-ai.crt;
    ssl_certificate_key /opt/anwalts-ai-production/ssl/anwalts-ai.key;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Document Root
    root /opt/anwalts-ai-production/Client;
    index anwalts-ai-dashboard.html index.html;
    
    # API Proxy to Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
        proxy_connect_timeout 86400;
        proxy_send_timeout 86400;
    }
    
    # Static Files
    location / {
        try_files $uri $uri/ /anwalts-ai-dashboard.html;
        expires 1h;
        add_header Cache-Control "public";
    }
    
    # Handle JS/CSS/Images
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Security - Block hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Enable the site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/anwalts-ai /etc/nginx/sites-enabled/

echo ""
echo "6. Testing nginx configuration:"
echo "=============================="
nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration is valid!"
    
    echo ""
    echo "7. Restarting nginx:"
    echo "==================="
    systemctl reload nginx
    systemctl status nginx --no-pager -l
    
    echo ""
    echo "8. Opening firewall ports:"
    echo "========================="
    # Try different firewall commands
    if command -v ufw &> /dev/null; then
        ufw allow 443/tcp
        ufw allow 80/tcp
        ufw allow 22/tcp
        ufw --force enable
        echo "UFW firewall updated"
    elif command -v iptables &> /dev/null; then
        iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        iptables -A INPUT -p tcp --dport 22 -j ACCEPT
        iptables-save > /etc/iptables/rules.v4 2>/dev/null
        echo "iptables rules updated"
    fi
    
    echo ""
    echo "9. Testing endpoints:"
    echo "===================="
    sleep 2
    echo "Testing HTTP (should redirect):"
    curl -I http://localhost 2>/dev/null | head -5
    
    echo ""
    echo "Testing HTTPS:"
    curl -I -k https://localhost 2>/dev/null | head -5
    
    echo ""
    echo "10. Final status:"
    echo "================="
    ss -tlnp | grep -E ':80|:443' || netstat -tlnp | grep -E ':80|:443'
    
    echo ""
    echo "✅ HTTPS configuration completed!"
    echo "🌐 Test your site at: https://148.251.195.222"
    
else
    echo "❌ Nginx configuration has errors!"
    nginx -t
    echo "Please fix the configuration errors above."
fi

echo ""
echo "11. Additional troubleshooting info:"
echo "==================================="
echo "Log files to check if issues persist:"
echo "- nginx error log: tail -f /var/log/nginx/error.log"
echo "- nginx access log: tail -f /var/log/nginx/access.log"
echo "- Docker logs: docker-compose logs -f"
echo ""
echo "If HTTPS still doesn't work, check:"
echo "1. Firewall settings (ufw status or iptables -L)"
echo "2. SSL certificate permissions (ls -la /opt/anwalts-ai-production/ssl/)"
echo "3. nginx error logs for specific SSL errors"