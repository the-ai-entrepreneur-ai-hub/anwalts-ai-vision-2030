# DNS Configuration for portal-anwalts.ai

## 🌐 **DNS Records Required**

Configure these DNS records with your domain provider:

### **A Records (IPv4)**
```
portal-anwalts.ai         A      148.251.195.222
www.portal-anwalts.ai     A      148.251.195.222
```

### **AAAA Records (IPv6)**
```
portal-anwalts.ai         AAAA   2a01:4f8:211:1956::2
www.portal-anwalts.ai     AAAA   2a01:4f8:211:1956::2
```

### **CNAME Records (Optional)**
```
api.portal-anwalts.ai     CNAME  portal-anwalts.ai
docs.portal-anwalts.ai    CNAME  portal-anwalts.ai
```

## 🔒 **SSL Certificate Setup (Let's Encrypt)**

### **Option 1: Automatic SSL with Certbot**
```bash
# During deployment, run:
docker-compose -f docker-compose-domain.yml run --rm certbot

# This will automatically obtain SSL certificates for:
# - portal-anwalts.ai
# - www.portal-anwalts.ai
```

### **Option 2: Manual SSL Setup**
```bash
# SSH into server after deployment
ssh root@portal-anwalts.ai

# Install certbot
apt install certbot

# Get certificates
certbot certonly --standalone -d portal-anwalts.ai -d www.portal-anwalts.ai

# Copy certificates to nginx
cp /etc/letsencrypt/live/portal-anwalts.ai/fullchain.pem /opt/anwalts-ai/config/ssl/portal-anwalts.ai.crt
cp /etc/letsencrypt/live/portal-anwalts.ai/privkey.pem /opt/anwalts-ai/config/ssl/portal-anwalts.ai.key

# Restart nginx
docker-compose restart nginx
```

## 📊 **Verification Commands**

### **Check DNS Propagation**
```bash
# Check A record
nslookup portal-anwalts.ai

# Check AAAA record  
nslookup -type=AAAA portal-anwalts.ai

# Online DNS checker
# https://dnschecker.org/
```

### **Test SSL Certificate**
```bash
# Check SSL
openssl s_client -connect portal-anwalts.ai:443 -servername portal-anwalts.ai

# Online SSL checker
# https://www.ssllabs.com/ssltest/
```

## 🚀 **Deployment Sequence**

1. **Configure DNS** (A and AAAA records)
2. **Wait for propagation** (15-60 minutes)
3. **Deploy application** to server
4. **Obtain SSL certificates**
5. **Update nginx configuration**
6. **Test application**

## 🎯 **Expected Results**

After DNS setup and deployment:

- **Main Application**: https://portal-anwalts.ai
- **API Documentation**: https://portal-anwalts.ai/docs
- **Health Check**: https://portal-anwalts.ai/health
- **API Endpoint**: https://portal-anwalts.ai/api/

## 📧 **Domain Configuration**

### **Common Domain Providers:**

**Cloudflare:**
1. Login to Cloudflare Dashboard
2. Select domain
3. Go to DNS section
4. Add A and AAAA records

**GoDaddy:**
1. Login to GoDaddy
2. Manage DNS
3. Add records

**Namecheap:**
1. Domain List → Manage
2. Advanced DNS
3. Add records

## 🔧 **Troubleshooting**

### **DNS Not Resolving**
```bash
# Clear DNS cache (Windows)
ipconfig /flushdns

# Check from different locations
# Use online tools like whatsmydns.net
```

### **SSL Issues**
```bash
# Check certificate validity
curl -I https://portal-anwalts.ai

# Renew certificates (auto-renewal)
certbot renew --dry-run
```

## 📈 **Performance Optimization**

### **CDN Setup (Optional)**
- **Cloudflare**: Free CDN and DDoS protection
- **AWS CloudFront**: Enterprise CDN
- **KeyCDN**: European CDN

### **Monitoring**
- **Uptime monitoring**: pingdom.com, uptimerobot.com
- **SSL monitoring**: sslmate.com
- **DNS monitoring**: dnsperf.com

---

**Your AnwaltsAI with 9,997 German legal examples will be available at https://portal-anwalts.ai once DNS is configured!** 🚀