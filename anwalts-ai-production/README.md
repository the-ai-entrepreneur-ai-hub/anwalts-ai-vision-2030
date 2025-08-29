# AnwaltsAI Production Deployment

## 🖥️ Server Information
- **Server**: Hetzner AX102 #2743403
- **IP**: 148.251.195.222
- **SSH**: root@148.251.195.222
- **Owner**: Dr. Markus Weigl, AIgenex GmbH

## 🚀 Quick Deployment

### 1. Upload this package to server:
```bash
scp anwalts-ai-production.tar.gz root@148.251.195.222:/opt/
```

### 2. SSH into server and extract:
```bash
ssh root@148.251.195.222
cd /opt
tar -xzf anwalts-ai-production.tar.gz
cd anwalts-ai-production
```

### 3. Run deployment:
```bash
chmod +x deploy.sh
./deploy.sh
```

## 📊 What's Included

### Backend (Fixed)
- ✅ Fixed authentication error (get_current_user_id)
- ✅ FastAPI with Together AI integration
- ✅ PostgreSQL database connection
- ✅ Redis caching
- ✅ JWT authentication system

### Frontend
- ✅ AnwaltsAI Dashboard UI
- ✅ API client integration
- ✅ Professional German legal interface

### German Legal Dataset
- ✅ 9,997 German legal examples
- ✅ Training data: 7,997 examples
- ✅ Validation data: 999 examples  
- ✅ Test data: 1,001 examples
- ✅ JSONL and Parquet formats

### Production Configuration
- ✅ Docker Compose with health checks
- ✅ Nginx reverse proxy
- ✅ Security headers and rate limiting
- ✅ Automated backups
- ✅ Log rotation
- ✅ Monitoring scripts

## 🔧 After Deployment

### Access Points
- **Main App**: http://148.251.195.222
- **API Docs**: http://148.251.195.222/api/docs  
- **Health**: http://148.251.195.222/health

### Monitoring
```bash
# Check status
docker-compose -f docker-compose.production.yml ps

# View logs  
docker-compose -f docker-compose.production.yml logs -f

# Monitor system
./monitor.sh
```

### Maintenance
```bash
# Backup
./backup.sh

# Restart services
docker-compose -f docker-compose.production.yml restart
```

## 📞 Support
- **Hetzner Support**: +49 [0] 9831 505-0
- **Project Owner**: Dr. Markus Weigl (017621137333)

---
Generated: 2025-08-07 19:00:42
Ready for production deployment! 🚀
