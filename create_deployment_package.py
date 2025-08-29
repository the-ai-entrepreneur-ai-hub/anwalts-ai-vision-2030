#!/usr/bin/env python3
"""
Create Deployment Package for Hetzner Server
Packages essential files for AnwaltsAI production deployment
"""

import os
import shutil
import json
from pathlib import Path
import zipfile
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentPackager:
    """Create production deployment package"""
    
    def __init__(self, source_dir=".", output_dir="deployment_package"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Essential files mapping
        self.file_mappings = {
            # Backend files
            'backend/main.py': 'backend/main.py',
            'backend/ai_service.py': 'backend/ai_service.py', 
            'backend/auth_service.py': 'backend/auth_service.py',
            'backend/cache_service.py': 'backend/cache_service.py',
            'backend/database.py': 'backend/database.py',
            'backend/models.py': 'backend/models.py',
            'backend/requirements.txt': 'backend/requirements.txt',
            'backend/Dockerfile': 'backend/Dockerfile',
            'backend/database/schema.sql': 'backend/database/schema.sql',
            
            # Frontend files
            'Client/anwalts_ai_enhanced.html': 'frontend/anwalts_ai_enhanced.html',
            'Client/api-client.js': 'frontend/api-client.js',
            'Client/favicon.ico': 'frontend/favicon.ico',
            'Client/favicon.svg': 'frontend/favicon.svg',
            'Client/start_frontend.py': 'frontend/start_frontend.py',
            
            # Configuration
            'docker-compose.yml': 'docker-compose.production.yml',
            'nginx.conf': 'config/nginx.conf',
            
            # Documentation
            'README.md': 'README.md',
            'ANWALTS_AI_SYSTEM_ARCHITECTURE.md': 'docs/SYSTEM_ARCHITECTURE.md',
            'CLIENT_SUCCESS_STATUS.md': 'docs/CLIENT_SUCCESS_STATUS.md',
            'HETZNER_SERVER_DEPLOYMENT.md': 'DEPLOYMENT_GUIDE.md'
        }
        
        # Dataset files (massive_legal_data - our 9,997 examples)
        self.dataset_files = [
            'Data/massive_legal_data/train.jsonl',
            'Data/massive_legal_data/validation.jsonl', 
            'Data/massive_legal_data/test.jsonl',
            'Data/massive_legal_data/metadata.json',
            'Data/exported_datasets/dataset_info.json',
            'Data/DATA_EXPANSION_SUMMARY_REPORT.md'
        ]
        
        # Export formats (select most useful)
        self.export_formats = [
            'Data/exported_datasets/parquet/train.parquet',
            'Data/exported_datasets/parquet/validation.parquet',
            'Data/exported_datasets/parquet/test.parquet',
            'Data/exported_datasets/huggingface/train/',
            'Data/exported_datasets/huggingface/validation/',
            'Data/exported_datasets/huggingface/test/'
        ]
    
    def copy_file_safe(self, src_path, dst_path):
        """Safely copy file with error handling"""
        try:
            src_full = self.source_dir / src_path
            dst_full = self.output_dir / dst_path
            
            # Create destination directory
            dst_full.parent.mkdir(parents=True, exist_ok=True)
            
            if src_full.exists():
                if src_full.is_file():
                    shutil.copy2(src_full, dst_full)
                    logger.info(f"Copied: {src_path} -> {dst_path}")
                    return True
                elif src_full.is_dir():
                    if dst_full.exists():
                        shutil.rmtree(dst_full)
                    shutil.copytree(src_full, dst_full)
                    logger.info(f"Copied directory: {src_path} -> {dst_path}")
                    return True
            else:
                logger.warning(f"Source not found: {src_path}")
                return False
        except Exception as e:
            logger.error(f"Error copying {src_path}: {e}")
            return False
    
    def create_production_config(self):
        """Create production configuration files"""
        
        # Production environment file
        env_content = """# AnwaltsAI Production Environment
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
DATASET_SIZE=9997

# Security
SECRET_KEY=change-this-in-production
JWT_SECRET=change-this-jwt-secret
CORS_ORIGINS=http://148.251.195.222,https://148.251.195.222

# Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Legal Dataset
DATASET_PATH=/opt/anwalts-ai/data/massive_legal_data
DATASET_FORMAT=jsonl
TOTAL_EXAMPLES=9997
TRAIN_EXAMPLES=7997
VALIDATION_EXAMPLES=999
TEST_EXAMPLES=1001
"""
        
        config_dir = self.output_dir / 'config'
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / '.env.production', 'w') as f:
            f.write(env_content)
        
        # Production Docker Compose
        docker_compose_content = """version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=sqlite:///app/data/anwalts_ai.db
      - AI_MODEL_PATH=/app/data/massive_legal_data
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  data:
  ssl:
"""
        
        with open(self.output_dir / 'docker-compose.production.yml', 'w') as f:
            f.write(docker_compose_content)
        
        # Nginx configuration
        nginx_content = """events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    server {
        listen 80;
        server_name 148.251.195.222;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Backend API
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            proxy_pass http://backend/health;
        }
    }
}
"""
        
        with open(config_dir / 'nginx.conf', 'w') as f:
            f.write(nginx_content)
    
    def create_deployment_script(self):
        """Create deployment script"""
        
        deploy_script = """#!/bin/bash
set -e

echo "🚀 Starting AnwaltsAI Production Deployment on Hetzner Server..."

# Server info
echo "📊 Server: AX102 #2743403 (148.251.195.222)"
echo "📦 Dataset: 9,997 German legal examples"

# Create necessary directories
mkdir -p logs data/backups config/ssl

# Set permissions
chmod 600 config/.env.production
chmod -R 755 data/
chmod +x deploy.sh

# Install system dependencies
echo "📋 Installing system dependencies..."
apt update
apt install -y curl htop

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Build and start services
echo "📦 Building Docker containers..."
docker-compose -f docker-compose.production.yml build --no-cache

echo "🔄 Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 45

# Health checks
echo "✅ Verifying deployment..."
timeout 30 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done' || {
    echo "❌ Backend health check failed"
    docker-compose -f docker-compose.production.yml logs backend
    exit 1
}

timeout 30 bash -c 'until curl -f http://localhost:3000; do sleep 5; done' || {
    echo "❌ Frontend health check failed"  
    docker-compose -f docker-compose.production.yml logs frontend
    exit 1
}

# Display status
echo ""
echo "🎉 Deployment completed successfully!"
echo "📊 Legal Dataset: 9,997 examples loaded"
echo "🌐 Application URL: http://148.251.195.222"
echo "📚 API Documentation: http://148.251.195.222/api/docs"
echo "📈 Health Check: http://148.251.195.222/health"
echo ""
echo "🔧 Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "  - Check status: docker-compose -f docker-compose.production.yml ps"
echo "  - Stop services: docker-compose -f docker-compose.production.yml down"
echo "  - Update: git pull && docker-compose -f docker-compose.production.yml up -d --build"
"""
        
        deploy_path = self.output_dir / 'deploy.sh'
        with open(deploy_path, 'w', encoding='utf-8') as f:
            f.write(deploy_script)
        
        # Make executable
        os.chmod(deploy_path, 0o755)
    
    def create_readme(self):
        """Create deployment README"""
        
        readme_content = """# AnwaltsAI Production Deployment

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
"""
        
        with open(self.output_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def package_files(self):
        """Package all essential files"""
        logger.info("Creating deployment package for Hetzner server...")
        
        # Copy essential application files
        copied_files = 0
        for src, dst in self.file_mappings.items():
            if self.copy_file_safe(src, dst):
                copied_files += 1
        
        # Copy dataset files (the valuable 9,997 examples!)
        dataset_dir = self.output_dir / 'data'
        dataset_dir.mkdir(exist_ok=True)
        
        for dataset_file in self.dataset_files:
            if self.copy_file_safe(dataset_file, f"data/{Path(dataset_file).name}"):
                copied_files += 1
        
        # Copy parquet exports (efficient format)
        parquet_dir = dataset_dir / 'exported_datasets' / 'parquet'
        parquet_dir.mkdir(parents=True, exist_ok=True)
        
        for export_file in self.export_formats[:3]:  # Just parquet files
            if self.copy_file_safe(export_file, f"data/exported_datasets/parquet/{Path(export_file).name}"):
                copied_files += 1
        
        # Create production configuration
        self.create_production_config()
        
        # Create deployment script
        self.create_deployment_script()
        
        # Create README
        self.create_readme()
        
        logger.info(f"Deployment package created with {copied_files} files")
        return copied_files
    
    def create_zip_package(self):
        """Create ZIP package for easy upload"""
        zip_path = Path(f"anwalts-ai-deployment-{Path.cwd().name}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.output_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created ZIP package: {zip_path}")
        return zip_path

def main():
    """Create deployment package"""
    packager = DeploymentPackager()
    
    # Package files
    file_count = packager.package_files()
    
    # Create ZIP for easy upload
    zip_path = packager.create_zip_package()
    
    # Summary
    print(f"\n🎉 Deployment package created successfully!")
    print(f"📁 Location: {packager.output_dir}")
    print(f"📦 ZIP package: {zip_path}")
    print(f"📊 Files packaged: {file_count}")
    print(f"🖥️ Target server: 148.251.195.222 (Hetzner)")
    print(f"📚 Legal dataset: 9,997 German examples included")
    print(f"\n🚀 Ready for deployment!")

if __name__ == "__main__":
    main()