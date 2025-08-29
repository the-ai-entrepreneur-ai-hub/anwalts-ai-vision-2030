# AnwaltsAI Production Deployment

## 🖥️ Server Information
- **Server**: Hetzner AX102 #2743403
- **IP**: 148.251.195.222
- **Owner**: Dr. Markus Weigl, AIgenex GmbH

## 📊 Legal Dataset
- **Total Examples**: 9,997 German legal training examples
- **Training**: 7,997 examples
- **Validation**: 999 examples  
- **Test**: 1,001 examples
- **Domains**: Civil, Criminal, Constitutional, Administrative, Labor Law

## 🚀 Quick Deployment

1. **Upload files to server:**
   ```bash
   scp -r . root@148.251.195.222:/opt/anwalts-ai/
   ```

2. **SSH into server:**
   ```bash
   ssh root@148.251.195.222
   cd /opt/anwalts-ai
   ```

3. **Deploy:**
   ```bash
   ./deploy.sh
   ```

4. **Access application:**
   - Application: http://148.251.195.222
   - API Docs: http://148.251.195.222/api/docs
   - Health: http://148.251.195.222/health

## 📁 Package Contents
- `backend/` - FastAPI backend service
- `frontend/` - Client application
- `data/` - German legal dataset (9,997 examples)
- `config/` - Production configuration
- `docker-compose.production.yml` - Service orchestration
- `deploy.sh` - Automated deployment script

## 🔧 Management Commands
```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check service status  
docker-compose -f docker-compose.production.yml ps

# Stop services
docker-compose -f docker-compose.production.yml down

# Update deployment
git pull && docker-compose -f docker-compose.production.yml up -d --build
```

## 📞 Support
- **Hetzner Support**: +49 [0] 9831 505-0
- **Project Owner**: Dr. Markus Weigl (017621137333)

**Ready for production with 9,997 German legal examples! 🚀**
