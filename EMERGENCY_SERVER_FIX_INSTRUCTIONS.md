# 🚨 EMERGENCY SERVER FIX INSTRUCTIONS
**Server: 148.251.195.222 (root/8sKHWH5cVu5fb3)**

## 🔍 DIAGNOSIS SUMMARY

✅ **WORKING:**
- HTTP (port 80) - nginx serving AnwaltsAI dashboard
- Web application is accessible at `http://148.251.195.222`
- Docker containers appear to be running
- Backend API likely running on port 8000

❌ **NOT WORKING:**
- HTTPS (port 443) - SSL configuration missing/broken
- SSH (port 22) - Connection blocked/disabled

## 🎯 IMMEDIATE FIX REQUIRED

### Method 1: Server Console Access (RECOMMENDED)

1. **Access server via hosting provider console/VNC**
2. **Login as root with password: `8sKHWH5cVu5fb3`**
3. **Run the emergency fix script:**

```bash
# Download and run the fix script
wget -O emergency_fix.sh https://raw.githubusercontent.com/[your-repo]/emergency_https_fix.sh
chmod +x emergency_fix.sh
./emergency_fix.sh
```

**OR manually execute these commands:**

```bash
# Go to production directory
cd /opt/anwalts-ai-production/

# Create SSL certificates
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/anwalts-ai.key \
    -out ssl/anwalts-ai.crt \
    -subj "/C=DE/ST=NRW/L=Dusseldorf/O=AnwaltsAI/CN=148.251.195.222"

chmod 600 ssl/anwalts-ai.key
chmod 644 ssl/anwalts-ai.crt

# Update nginx config for HTTPS
cat > /etc/nginx/sites-available/anwalts-ai << 'EOF'
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;
    
    ssl_certificate /opt/anwalts-ai-production/ssl/anwalts-ai.crt;
    ssl_certificate_key /opt/anwalts-ai-production/ssl/anwalts-ai.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    root /opt/anwalts-ai-production/Client;
    index anwalts-ai-dashboard.html;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        try_files $uri $uri/ /anwalts-ai-dashboard.html;
    }
}
EOF

# Enable site and restart nginx
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/anwalts-ai /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Open firewall ports
ufw allow 443/tcp
ufw allow 22/tcp

# Test HTTPS
curl -I -k https://localhost
```

### Method 2: Remote Upload via Web Interface (if available)

If the server has a file manager or upload interface accessible via HTTP:

1. **Upload the `emergency_https_fix.sh` script**
2. **Execute via web terminal or cron job**

### Method 3: Recovery via Hosting Provider

Contact hosting provider to:
1. **Enable SSH access (port 22)**
2. **Configure HTTPS on port 443**
3. **Run the emergency fix script**

## 🧪 TESTING AFTER FIX

```bash
# Test HTTP redirect
curl -I http://148.251.195.222

# Test HTTPS
curl -I -k https://148.251.195.222

# Test API
curl -I -k https://148.251.195.222/api/health

# Check ports
netstat -tlnp | grep -E ':80|:443|:22'
```

## 📊 EXPECTED RESULTS

After successful fix:
- ✅ HTTP redirects to HTTPS (301 redirect)
- ✅ HTTPS serves AnwaltsAI dashboard (200 OK)
- ✅ API accessible at `/api/` endpoint
- ✅ SSH accessible on port 22

## 🔧 TROUBLESHOOTING

If HTTPS still doesn't work:

1. **Check nginx logs:**
```bash
tail -f /var/log/nginx/error.log
```

2. **Verify SSL certificates:**
```bash
ls -la /opt/anwalts-ai-production/ssl/
openssl x509 -in ssl/anwalts-ai.crt -text -noout
```

3. **Check firewall:**
```bash
ufw status
iptables -L -n
```

4. **Restart all services:**
```bash
systemctl restart nginx
docker-compose restart
```

## 🚀 PRIORITY ORDER

1. **CRITICAL:** Fix HTTPS (port 443) - Business impact
2. **HIGH:** Enable SSH (port 22) - For future management
3. **MEDIUM:** Verify all containers healthy
4. **LOW:** Update security configurations

## 📞 SUPPORT

If issues persist after running the fix:
1. Check nginx error logs
2. Verify SSL certificate validity
3. Test individual components (nginx, docker, firewall)
4. Contact system administrator with logs

---
**Generated:** $(date)
**Server:** 148.251.195.222
**Status:** HTTP ✅ | HTTPS ❌ | SSH ❌