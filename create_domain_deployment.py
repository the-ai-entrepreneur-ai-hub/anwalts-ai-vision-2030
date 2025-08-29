#!/usr/bin/env python3
"""
Create Domain-Ready Deployment Package for portal-anwalts.ai
Complete production deployment with SSL, domain configuration, and 9,997 legal examples
"""

import os
import shutil
import json
from pathlib import Path
import zipfile
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DomainDeploymentPackager:
    """Create production deployment package for portal-anwalts.ai"""
    
    def __init__(self, source_dir="deployment_package", output_dir="portal-anwalts-ai-deployment"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def copy_base_files(self):
        """Copy all files from existing deployment package"""
        logger.info("Copying base deployment files...")
        
        if self.source_dir.exists():
            # Copy entire deployment package
            for item in self.source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.output_dir)
                elif item.is_dir():
                    dest_dir = self.output_dir / item.name
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    shutil.copytree(item, dest_dir)
            
            logger.info("Base files copied successfully")
        else:
            logger.error(f"Source directory not found: {self.source_dir}")
    
    def create_domain_specific_files(self):
        """Create domain-specific configuration files"""
        
        # Create SSL directory
        ssl_dir = self.output_dir / 'config' / 'ssl'
        ssl_dir.mkdir(parents=True, exist_ok=True)
        
        # Create SSL placeholder files
        with open(ssl_dir / 'README.md', 'w') as f:
            f.write("""# SSL Certificates Directory

This directory will contain SSL certificates for portal-anwalts.ai

After deployment:
1. DNS must be configured (A record: portal-anwalts.ai -> server IP)
2. SSL certificates will be automatically generated using Let's Encrypt
3. Files will be:
   - portal-anwalts.ai.crt (certificate)
   - portal-anwalts.ai.key (private key)

The deploy-domain.sh script handles SSL setup automatically.
""")
        
        # Create certbot webroot directory
        webroot_dir = self.output_dir / 'config' / 'certbot-webroot'
        webroot_dir.mkdir(parents=True, exist_ok=True)
        
        with open(webroot_dir / '.gitkeep', 'w') as f:
            f.write('')
    
    def create_deployment_readme(self):
        """Create comprehensive deployment README"""
        
        readme_content = """# AnwaltsAI Production Deployment for portal-anwalts.ai

## 🎯 **Overview**
Complete German legal AI system with 9,997 training examples, ready for production deployment at **portal-anwalts.ai**.

## 📊 **What's Included**
- **9,997 German legal examples** (train: 7,997, validation: 999, test: 1,001)
- **5 legal domains**: Civil, Criminal, Constitutional, Administrative, Labor Law
- **Production-ready configuration** for portal-anwalts.ai
- **SSL/HTTPS setup** with Let's Encrypt
- **Docker containerization** with health checks
- **Nginx reverse proxy** with security headers

## 🚀 **Quick Deployment**

### **Step 1: Configure DNS**
Set up DNS records with your domain provider:
```
portal-anwalts.ai         A      [SERVER_IP]
www.portal-anwalts.ai     A      [SERVER_IP]
```

### **Step 2: Upload to Server**
```bash
scp -r . root@[SERVER_IP]:/opt/anwalts-ai/
```

### **Step 3: Deploy**
```bash
ssh root@[SERVER_IP]
cd /opt/anwalts-ai
chmod +x deploy-domain.sh
./deploy-domain.sh
```

## 🌐 **Expected Results**
- **Application**: https://portal-anwalts.ai
- **API Documentation**: https://portal-anwalts.ai/docs  
- **Health Check**: https://portal-anwalts.ai/health

## 📁 **Package Contents**
```
portal-anwalts-ai-deployment/
├── backend/                    # FastAPI backend service
├── frontend/                   # Client application
├── data/                       # 9,997 German legal examples
├── config/                     # Production configuration
│   ├── .env.production        # Environment variables
│   ├── nginx.conf             # HTTP configuration
│   ├── nginx-ssl.conf         # HTTPS configuration
│   └── ssl/                   # SSL certificates directory
├── deploy-domain.sh           # Main deployment script
├── docker-compose-domain.yml  # Domain-specific Docker config
└── DNS_SETUP_INSTRUCTIONS.md # DNS configuration guide
```

## 🔧 **Configuration Features**
- **Domain**: portal-anwalts.ai (www subdomain supported)
- **SSL**: Automatic Let's Encrypt certificates
- **Security**: HTTPS redirect, security headers, CORS
- **Performance**: Nginx caching, compression
- **Monitoring**: Health checks, logging
- **Auto-renewal**: SSL certificates auto-renew

## 📞 **Support Information**
- **Server**: Hetzner AX102 #2743403
- **Owner**: Dr. Markus Weigl, AIgenex GmbH
- **Mobile**: 017621137333

## 🎯 **Next Steps**
1. Configure DNS records
2. Upload deployment package to server
3. Run deployment script
4. Verify HTTPS access
5. Your German legal AI is ready!

**Ready for production with 9,997 German legal examples! 🚀**
"""
        
        with open(self.output_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def create_quick_deploy_script(self):
        """Create Windows script for quick deployment"""
        
        script_content = """@echo off
echo ==========================================
echo  AnwaltsAI Domain Deployment
echo ==========================================
echo.
echo Domain: portal-anwalts.ai
echo Dataset: 9,997 German legal examples
echo SSL: Automatic HTTPS setup
echo.

REM Check if deployment package exists
if not exist "portal-anwalts-ai-deployment" (
    echo Deployment package not found!
    echo Run: python create_domain_deployment.py
    pause
    exit /b 1
)

echo Step 1: Configure DNS records
echo ================================
echo Add these DNS records:
echo   portal-anwalts.ai     A    [SERVER_IP]
echo   www.portal-anwalts.ai A    [SERVER_IP]
echo.
echo Step 2: Upload to server
echo ========================
echo Command: scp -r portal-anwalts-ai-deployment root@[SERVER_IP]:/opt/anwalts-ai/
echo.
echo Step 3: Deploy
echo ==============
echo SSH: ssh root@[SERVER_IP]
echo Run: cd /opt/anwalts-ai && chmod +x deploy-domain.sh && ./deploy-domain.sh
echo.
echo Expected result: https://portal-anwalts.ai
echo.
pause
"""
        
        with open(Path('deploy_portal_anwalts.bat'), 'w') as f:
            f.write(script_content)
    
    def create_zip_package(self):
        """Create ZIP package for easy distribution"""
        zip_path = Path(f"portal-anwalts-ai-production-deployment.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.output_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created ZIP package: {zip_path}")
        return zip_path
    
    def package_for_domain(self):
        """Create complete domain deployment package"""
        logger.info("Creating portal-anwalts.ai deployment package...")
        
        # Copy base files
        self.copy_base_files()
        
        # Create domain-specific files
        self.create_domain_specific_files()
        
        # Create documentation
        self.create_deployment_readme()
        
        # Create deployment scripts
        self.create_quick_deploy_script()
        
        # Create ZIP package
        zip_path = self.create_zip_package()
        
        return zip_path

def main():
    """Create domain deployment package"""
    packager = DomainDeploymentPackager()
    zip_path = packager.package_for_domain()
    
    print(f"\n🎉 Portal-AnwaltsAI deployment package created!")
    print(f"📁 Directory: {packager.output_dir}")
    print(f"📦 ZIP package: {zip_path}")
    print(f"🌐 Domain: portal-anwalts.ai")
    print(f"📊 Dataset: 9,997 German legal examples")
    print(f"🔒 SSL: Automatic HTTPS setup")
    print(f"🚀 Ready for production deployment!")

if __name__ == "__main__":
    main()