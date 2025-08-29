# Hetzner Server Deployment Guide - AnwaltsAI

## 🖥️ Server Information
- **Server**: AX102 #2743403
- **IPv4**: 148.251.195.222
- **IPv6**: 2a01:4f8:211:1956::2
- **Provider**: Hetzner Online GmbH
- **Owner**: Dr. Markus Weigl, AIgenex GmbH

## 📦 Deployment Package Contents

### Essential Files for Server Upload
```
anwalts-ai-production/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── ai_service.py          # AI service integration
│   ├── auth_service.py        # Authentication system
│   ├── cache_service.py       # Caching layer
│   ├── database.py            # Database connections
│   ├── models.py              # Data models
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Backend container
│   └── database/
│       └── schema.sql        # Database schema
│
├── frontend/
│   ├── anwalts_ai_enhanced.html  # Main UI
│   ├── api-client.js            # API client
│   ├── favicon.ico              # Brand assets
│   └── start_frontend.py        # Frontend server
│
├── data/
│   ├── massive_legal_data/      # 9,997 German legal examples
│   │   ├── train.jsonl         # 7,997 training examples  
│   │   ├── validation.jsonl    # 999 validation examples
│   │   ├── test.jsonl          # 1,001 test examples
│   │   └── metadata.json       # Dataset information
│   │
│   └── exported_datasets/       # Multi-format exports
│       ├── parquet/            # For ML frameworks
│       ├── huggingface/        # For transformers
│       └── dataset_info.json   # Usage guide
│
├── config/
│   ├── nginx.conf              # Reverse proxy
│   ├── .env.production         # Environment variables
│   └── ssl/                    # SSL certificates (if needed)
│
├── docker-compose.production.yml  # Production orchestration
├── deploy.sh                      # Deployment script
├── README.md                      # Deployment instructions
└── LEGAL_DATASET_INFO.md         # Dataset documentation
```

## 🚀 Quick Deployment Steps

### 1. Server Initial Setup
```bash
# SSH into server
ssh root@148.251.195.222
# Password: BrfiDiUwxFEAvu

# Update system
apt update && apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. Upload Project Files
```bash
# Create project directory
mkdir -p /opt/anwalts-ai
cd /opt/anwalts-ai

# Upload files (using SCP or similar)
# Files will be uploaded here...
```

### 3. Deploy Application
```bash
# Set permissions
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## 🔧 Production Configuration

### Environment Variables (.env.production)
```env
# Application
NODE_ENV=production
DEBUG=false
PORT=8000
FRONTEND_PORT=3000

# Database
DATABASE_URL=sqlite:///opt/anwalts-ai/data/anwalts_ai.db
DATABASE_POOL_SIZE=20

# AI Service
AI_MODEL_PATH=/opt/anwalts-ai/data/massive_legal_data
AI_MODEL_TYPE=german_legal
MAX_TOKENS=2048

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
CORS_ORIGINS=http://148.251.195.222,https://148.251.195.222

# Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Legal Dataset
DATASET_PATH=/opt/anwalts-ai/data/massive_legal_data
DATASET_FORMAT=jsonl
DATASET_SIZE=9997
```

### Docker Compose Production
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./config/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

## 🔒 Security Configuration

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name 148.251.195.222;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Firewall Setup
```bash
# Install UFW
apt install ufw -y

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 📊 Legal Dataset Integration

### Dataset Information
- **Total Examples**: 9,997
- **Training Data**: 7,997 examples
- **Validation Data**: 999 examples  
- **Test Data**: 1,001 examples
- **Language**: German
- **Domain**: Legal (5 areas covered)
- **Format**: Instruction tuning ready

### Usage in Production
```python
# Load dataset in application
from datasets import load_from_disk
import pandas as pd

# Load training data
train_data = pd.read_parquet('/opt/anwalts-ai/data/exported_datasets/parquet/train.parquet')

# Load with HuggingFace
dataset = load_from_disk('/opt/anwalts-ai/data/exported_datasets/huggingface/train')
```

## 🚀 Deployment Script (deploy.sh)
```bash
#!/bin/bash
set -e

echo "🚀 Starting AnwaltsAI Production Deployment..."

# Create necessary directories
mkdir -p logs data/backups

# Set file permissions
chmod 600 config/.env.production
chmod -R 755 data/
chmod +x backend/start.sh

# Build and start services
echo "📦 Building Docker containers..."
docker-compose -f docker-compose.production.yml build

echo "🔄 Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to start
sleep 30

# Initialize database
echo "🗄️  Initializing database..."
docker-compose -f docker-compose.production.yml exec backend python database.py

# Verify deployment
echo "✅ Verifying deployment..."
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000 || exit 1

echo "🎉 Deployment completed successfully!"
echo "📊 Legal Dataset: 9,997 examples loaded"
echo "🌐 Application available at: http://148.251.195.222"
echo "📚 API Documentation: http://148.251.195.222/docs"
```

## 📈 Monitoring & Maintenance

### Health Checks
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Monitor resources
htop
df -h
```

### Backup Strategy
```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /opt/backups/anwalts-ai-$DATE.tar.gz /opt/anwalts-ai/data
```

## 🎯 Next Steps After Deployment

1. **Test Application**: Verify all endpoints work correctly
2. **Configure SSL**: Add HTTPS support (Let's Encrypt)
3. **Monitor Performance**: Set up logging and monitoring
4. **Scale Resources**: Adjust based on usage patterns
5. **Legal Model Training**: Use the 9,997 examples for model fine-tuning

## 📞 Support Information

**Server Support**: Hetzner Online GmbH
- **Phone**: +49 [0] 9831 505-0 (Mon-Fri, 8:00-18:00)
- **Data Center**: +49 [0] 911 234226-100 (24/7)
- **Status**: https://status.hetzner.com

**Project Owner**: Dr. Markus Weigl, AIgenex GmbH
- **Mobile**: 017621137333
- **Email**: [Contact via AIgenex]

---

**Ready for deployment with 9,997 German legal examples! 🚀**