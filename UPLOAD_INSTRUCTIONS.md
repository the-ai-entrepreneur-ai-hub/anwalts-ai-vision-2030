# Hetzner Server Upload Instructions - AnwaltsAI Deployment

## 🖥️ Your Server Details
- **IP Address**: 148.251.195.222
- **Username**: root
- **Password**: BrfiDiUwxFEAvu
- **Server**: Hetzner AX102 #2743403

## 📦 Files Ready for Upload
- **ZIP Package**: `anwalts-ai-deployment-Law Firm Vision 2030.zip`
- **Directory**: `deployment_package/` (29 files)
- **Dataset**: 9,997 German legal examples included

## 🚀 Upload Methods (Choose One)

### **Method 1: Upload ZIP File (Recommended)**

#### Step 1: Upload ZIP to Server
```bash
# From your local machine (Windows Command Prompt or PowerShell)
cd "C:\Users\Administrator\Documents\serveless-apps\Law Firm Vision 2030"

# Upload ZIP file using SCP
scp "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/
```

#### Step 2: SSH into Server and Extract
```bash
# Connect to server
ssh root@148.251.195.222
# Password: BrfiDiUwxFEAvu

# Navigate and extract
cd /opt
unzip "anwalts-ai-deployment-Law Firm Vision 2030.zip"
cd deployment_package/

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### **Method 2: Upload Directory Directly**

#### Upload entire deployment package
```bash
# From your local machine
cd "C:\Users\Administrator\Documents\serveless-apps\Law Firm Vision 2030"

# Upload entire directory
scp -r deployment_package root@148.251.195.222:/opt/anwalts-ai/
```

#### SSH and Deploy
```bash
# Connect to server
ssh root@148.251.195.222

# Navigate and deploy
cd /opt/anwalts-ai
chmod +x deploy.sh
./deploy.sh
```

### **Method 3: Using Windows GUI Tools**

#### Option A: WinSCP (Recommended for Windows)
1. Download WinSCP: https://winscp.net/
2. Create new connection:
   - **Protocol**: SFTP
   - **Host**: 148.251.195.222
   - **Username**: root
   - **Password**: BrfiDiUwxFEAvu
3. Upload ZIP file to `/opt/` directory
4. Use WinSCP's terminal to extract and deploy

#### Option B: FileZilla
1. Download FileZilla: https://filezilla-project.org/
2. Connect with SFTP:
   - **Host**: sftp://148.251.195.222
   - **Username**: root
   - **Password**: BrfiDiUwxFEAvu
3. Upload files to `/opt/` directory

## 🔧 What Happens During Deployment

The `deploy.sh` script will automatically:

1. **System Setup**
   ```bash
   apt update && apt upgrade -y
   ```

2. **Install Docker & Docker Compose**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

3. **Build and Start Services**
   ```bash
   docker-compose -f docker-compose.production.yml build
   docker-compose -f docker-compose.production.yml up -d
   ```

4. **Health Checks**
   - Backend API: http://148.251.195.222:8000/health
   - Frontend UI: http://148.251.195.222:3000
   - Nginx Proxy: http://148.251.195.222

## 📊 Dataset Integration

Your expanded German legal dataset will be available at:
- **Location**: `/opt/anwalts-ai/data/`
- **Examples**: 9,997 total
- **Formats**: JSONL and Parquet
- **API Access**: http://148.251.195.222/api/dataset

## 🔍 Verification Steps

After deployment, verify everything works:

```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Test endpoints
curl http://148.251.195.222/health
curl http://148.251.195.222

# View logs if needed
docker-compose -f docker-compose.production.yml logs -f
```

## 🚨 Troubleshooting

### If SCP fails:
```bash
# Try with verbose output
scp -v "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/

# Or use different SSH options
scp -o StrictHostKeyChecking=no "anwalts-ai-deployment-Law Firm Vision 2030.zip" root@148.251.195.222:/opt/
```

### If SSH connection fails:
```bash
# Test connection first
ssh -v root@148.251.195.222

# Or try with specific options
ssh -o StrictHostKeyChecking=no root@148.251.195.222
```

### If deployment fails:
```bash
# Check Docker logs
docker-compose -f docker-compose.production.yml logs

# Restart services
docker-compose -f docker-compose.production.yml restart

# Check disk space
df -h
```

## 🎯 Expected Results

After successful deployment:

✅ **AnwaltsAI Application**: http://148.251.195.222  
✅ **API Documentation**: http://148.251.195.222/api/docs  
✅ **Health Check**: http://148.251.195.222/health  
✅ **German Legal Dataset**: 9,997 examples ready for AI training  
✅ **Production Environment**: Docker containers running with Nginx  

## 📞 Support

**Server Issues**: Hetzner Support +49 [0] 9831 505-0  
**Project Owner**: Dr. Markus Weigl (017621137333)  

## 🔐 Security Notes

- Change default passwords after deployment
- Consider setting up SSL/TLS certificates
- Configure firewall rules as needed
- Monitor server resources and logs

---

**Ready to deploy your AnwaltsAI with 9,997 German legal examples! 🚀**