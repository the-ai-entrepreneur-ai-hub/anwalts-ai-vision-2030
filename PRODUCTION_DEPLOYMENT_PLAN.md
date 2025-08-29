# 🚀 AnwaltsAI Production Deployment Plan - Hetzner AX102

## 📋 **Server Information**
- **Server**: Hetzner AX102 #2743403  
- **IPv4**: 148.251.195.222  
- **IPv6**: 2a01:4f8:211:1956::2  
- **SSH**: root@148.251.195.222 (Password: BrfiDiUwxFEAvu)  
- **Owner**: Dr. Markus Weigl, AIgenex GmbH

## 🎯 **Deployment Strategy**

### **Current State Analysis**
✅ **Backend Fixed**: NoneType authentication error resolved  
✅ **Frontend Working**: anwalts-ai-dashboard.html functional  
✅ **Database Ready**: PostgreSQL with schema  
✅ **AI Integration**: DeepSeek-V3 with Together API  
✅ **Legal Dataset**: 9,997 German legal examples prepared  

### **Production Architecture**
```
┌─────────────────────┐
│   Nginx (Port 80)   │ ←─ Public Access
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  Frontend (Port 3000) │ ←─ anwalts-ai-dashboard.html
└─────────────────────┘
          │
┌─────────▼───────────┐
│  Backend (Port 8000) │ ←─ FastAPI + Auth + AI
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ PostgreSQL (5432)   │ ←─ User data + documents
└─────────────────────┘
          │
┌─────────▼───────────┐
│   Redis (6379)      │ ←─ Sessions + cache
└─────────────────────┘
          │
┌─────────▼───────────┐
│ Model Server (8080) │ ←─ German legal model
└─────────────────────┘
```

## 📁 **Server Directory Structure**

```
/opt/anwalts-ai/                    # Main application directory
├── frontend/                       # Static files
│   ├── anwalts-ai-dashboard.html  # Main UI
│   ├── api-client.js              # API integration
│   ├── favicon.ico                # Branding
│   └── assets/                    # CSS, JS, images
│
├── backend/                        # Python FastAPI
│   ├── main.py                    # Fixed main application
│   ├── auth_service.py            # Fixed authentication
│   ├── ai_service.py              # Together AI integration
│   ├── database.py                # PostgreSQL connection
│   ├── requirements.txt           # Dependencies
│   └── Dockerfile                 # Container config
│
├── data/                          # Legal dataset
│   ├── train.jsonl               # 7,997 training examples
│   ├── validation.jsonl          # 999 validation examples
│   ├── test.jsonl                # 1,001 test examples
│   └── metadata.json             # Dataset info
│
├── config/                        # Configuration files
│   ├── nginx.conf                # Production nginx
│   ├── docker-compose.yml        # Container orchestration
│   ├── .env.production           # Environment variables
│   └── ssl/                      # SSL certificates (future)
│
├── logs/                          # Application logs
├── backups/                       # Database backups
└── deploy.sh                     # Deployment script
```

## 🔧 **Production Configuration Files**

### **1. Production Environment (.env.production)**
```env
# Application
NODE_ENV=production
DEBUG=false
PORT=8000
FRONTEND_PORT=3000

# Database
DATABASE_URL=postgresql://postgres:REDACTED@localhost:5432/anwalts_ai_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# AI Service (Your existing Together API)
TOGETHER_API_KEY=REDACTED
DEFAULT_AI_MODEL=deepseek-ai/DeepSeek-V3
AI_MAX_TOKENS=2048
AI_TEMPERATURE=0.3

# Security (PRODUCTION SECRETS - Change These!)
JWT_SECRET_KEY=REDACTED
SECRET_KEY=AnwaltsAI-Production-Secret-Key-For-Sessions-And-Encryption-Very-Secure
CORS_ORIGINS=http://148.251.195.222,https://148.251.195.222

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Legal Dataset
DATASET_PATH=/opt/anwalts-ai/data
DATASET_SIZE=9997
LEGAL_MODEL_PATH=/opt/anwalts-ai/models

# Monitoring
LOG_LEVEL=INFO
LOG_FILE=/opt/anwalts-ai/logs/anwalts-ai.log
```

### **2. Production Docker Compose (docker-compose.production.yml)**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: anwalts_postgres_prod
    environment:
      POSTGRES_DB: anwalts_ai_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: REDACTED
    ports:
      - "127.0.0.1:5432:5432"  # Only local access
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    networks:
      - anwalts_network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: anwalts_redis_prod
    ports:
      - "127.0.0.1:6379:6379"  # Only local access
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    networks:
      - anwalts_network

  # FastAPI Backend (Your Fixed Backend)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: anwalts_backend_prod
    ports:
      - "127.0.0.1:8000:8000"  # Only local access
    env_file:
      - .env.production
    environment:
      - DATABASE_URL=postgresql://postgres:REDACTED@postgres:5432/anwalts_ai_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./data:/app/data:ro        # Legal dataset (read-only)
      - ./logs:/app/logs           # Application logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - anwalts_network

  # Frontend (Static Files)
  frontend:
    image: nginx:alpine
    container_name: anwalts_frontend_prod
    ports:
      - "127.0.0.1:3000:80"  # Only local access
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
      - ./config/nginx-frontend.conf:/etc/nginx/nginx.conf:ro
    restart: unless-stopped
    networks:
      - anwalts_network

  # Nginx Reverse Proxy (Public Access)
  nginx:
    image: nginx:alpine
    container_name: anwalts_nginx_prod
    ports:
      - "80:80"              # Public HTTP
      - "443:443"            # Public HTTPS (future)
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/ssl:/etc/nginx/ssl:ro  # SSL certificates
      - ./logs:/var/log/nginx           # Nginx logs
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - anwalts_network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  anwalts_network:
    driver: bridge
```

### **3. Production Nginx Configuration**
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # Upstream backends
    upstream backend {
        server frontend:80;
        keepalive 32;
    }

    upstream api {
        server backend:8000;
        keepalive 32;
    }

    server {
        listen 80;
        server_name 148.251.195.222;
        
        # Security
        server_tokens off;
        
        # Logs
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
        
        # Main application
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # API specific headers
            proxy_set_header Content-Type application/json;
            proxy_buffering off;
        }
        
        # Authentication endpoints (stricter rate limiting)
        location /auth/ {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://api/auth/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            proxy_pass http://api/health;
            access_log off;
        }
        
        # Static assets caching
        location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg)$ {
            proxy_pass http://backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 🚀 **Deployment Steps**

### **Step 1: Prepare Deployment Package**
```bash
# On your Windows machine
cd "C:\Users\Administrator\Documents\serveless-apps\Law Firm Vision 2030"

# Create production deployment package
mkdir production-deployment
cp -r backend production-deployment/
cp -r Client production-deployment/frontend
cp -r Data production-deployment/data

# Copy configuration files
mkdir production-deployment/config
# Copy nginx.conf, docker-compose.production.yml, .env.production
```

### **Step 2: Upload to Server**
```bash
# Create deployment archive
tar -czf anwalts-ai-production.tar.gz production-deployment/

# Upload to server
scp anwalts-ai-production.tar.gz root@148.251.195.222:/opt/

# SSH into server
ssh root@148.251.195.222
```

### **Step 3: Server Setup**
```bash
# Extract deployment
cd /opt
tar -xzf anwalts-ai-production.tar.gz
mv production-deployment anwalts-ai
cd anwalts-ai

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Set permissions
chmod 600 .env.production
chmod +x deploy.sh
chmod -R 755 data/
```

### **Step 4: Deploy Application**
```bash
# Run deployment
./deploy.sh

# Or manual deployment:
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# Wait for services to start
sleep 60

# Initialize database (if needed)
docker-compose -f docker-compose.production.yml exec backend python database.py
```

### **Step 5: Verify Deployment**
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Test endpoints
curl http://localhost/health
curl http://148.251.195.222/health

# Check logs
docker-compose -f docker-compose.production.yml logs -f backend
```

## 🛡️ **Security Configuration**

### **Firewall Setup**
```bash
# Install and configure UFW
apt update && apt install ufw -y

# Configure firewall rules
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Verify status
ufw status verbose
```

### **System Security**
```bash
# Update system
apt update && apt upgrade -y

# Install fail2ban for SSH protection
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban

# Disable root SSH (after creating admin user)
# sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
# systemctl restart ssh
```

## 📊 **Model Integration**

The server will host both the AnwaltsAI application AND the German legal model:

### **Model Server Configuration**
```bash
# Model will be served alongside the application
# Directory: /opt/anwalts-ai/models/
# Port: 8080 (internal)
# Access: Via backend API at /api/ai/
```

### **Dataset Integration**
- **Location**: `/opt/anwalts-ai/data/`
- **Size**: 9,997 German legal examples
- **Format**: JSONL + Parquet
- **Usage**: Training data for model fine-tuning
- **API Access**: `/api/dataset/` endpoints

## 📈 **Monitoring & Maintenance**

### **Health Monitoring**
```bash
# Application health
curl http://148.251.195.222/health

# Service monitoring
watch docker-compose -f docker-compose.production.yml ps

# Resource monitoring
htop
df -h
free -h
```

### **Backup Strategy**
```bash
# Database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U postgres anwalts_ai_db > /opt/backups/db-$DATE.sql

# Full application backup
tar -czf /opt/backups/anwalts-ai-full-$DATE.tar.gz /opt/anwalts-ai
```

## 🎯 **Expected Results**

After successful deployment:

✅ **Main Application**: http://148.251.195.222  
✅ **API Documentation**: http://148.251.195.222/api/docs  
✅ **Health Check**: http://148.251.195.222/health  
✅ **German Legal AI**: Integrated with 9,997 examples  
✅ **Authentication**: Fixed and working  
✅ **Document Generation**: DeepSeek-V3 integration  

## 📞 **Support & Escalation**

**Server Support**: Hetzner Online GmbH  
- Phone: +49 [0] 9831 505-0  
- Emergency: +49 [0] 911 234226-100  

**Project Owner**: Dr. Markus Weigl, AIgenex GmbH  
- Mobile: 017621137333  

## 🔄 **Next Steps After Deployment**

1. **Test Application**: Verify all endpoints work
2. **SSL Setup**: Configure HTTPS with Let's Encrypt
3. **Domain Configuration**: Set up portal-anwalts.ai DNS
4. **Model Training**: Utilize the 9,997 legal examples
5. **Performance Optimization**: Monitor and scale resources
6. **Backup Automation**: Set up automated backups
7. **Monitoring Setup**: Implement logging and alerts

---

**Ready to deploy AnwaltsAI with your 9,997 German legal examples on Hetzner AX102! 🚀**