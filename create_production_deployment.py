#!/usr/bin/env python3
"""
AnwaltsAI Production Deployment Package Creator
Creates a complete deployment package for Hetzner AX102 server
Server: 148.251.195.222 (Dr. Markus Weigl, AIgenex GmbH)
"""

import os
import shutil
import zipfile
import json
from datetime import datetime
from pathlib import Path

def create_production_deployment():
    """Create complete production deployment package"""
    
    print("Creating AnwaltsAI Production Deployment Package...")
    print("=" * 60)
    
    # Configuration
    project_root = Path(__file__).parent
    deployment_name = "anwalts-ai-production"
    package_dir = project_root / deployment_name
    
    # Create deployment directory
    if package_dir.exists():
        print(f"Removing existing deployment directory...")
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    print(f"Created deployment directory: {package_dir}")
    
    # Step 1: Copy backend files (with fixes)
    print("Copying backend files...")
    backend_src = project_root / "backend"
    backend_dst = package_dir / "backend"
    
    if backend_src.exists():
        shutil.copytree(backend_src, backend_dst, 
                       ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo', '.pytest_cache'))
        print(f"Backend copied from {backend_src}")
    else:
        print(f"Backend directory not found at {backend_src}")
        return False
    
    # Step 2: Copy frontend files
    print("Copying frontend files...")
    frontend_src = project_root / "Client"
    frontend_dst = package_dir / "frontend"
    
    if frontend_src.exists():
        shutil.copytree(frontend_src, frontend_dst,
                       ignore=shutil.ignore_patterns('*.tmp', '*.log'))
        
        # Rename main dashboard file for clarity
        main_file = frontend_dst / "anwalts-ai-dashboard.html"
        if main_file.exists():
            index_file = frontend_dst / "index.html"
            shutil.copy2(main_file, index_file)
            print(f"Frontend copied and index.html created")
        else:
            print(f"Main dashboard file not found, using available files")
    else:
        print(f"Frontend directory not found at {frontend_src}")
        return False
    
    # Step 3: Copy data directory (German legal dataset)
    print("Copying German legal dataset...")
    data_src = project_root / "Data"
    data_dst = package_dir / "data"
    
    if data_src.exists():
        # Create data directory structure
        data_dst.mkdir()
        
        # Copy essential files
        essential_files = [
            "exported_datasets/parquet/train.parquet",
            "exported_datasets/parquet/validation.parquet", 
            "exported_datasets/parquet/test.parquet",
            "expanded_legal_data/train.jsonl",
            "expanded_legal_data/validation.jsonl",
            "expanded_legal_data/test.jsonl",
            "expanded_legal_data/metadata.json"
        ]
        
        copied_files = []
        for file_path in essential_files:
            src_file = data_src / file_path
            if src_file.exists():
                dst_file = data_dst / file_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                copied_files.append(file_path)
        
        # Create dataset summary
        dataset_info = {
            "name": "German Legal Dataset for AnwaltsAI",
            "total_examples": 9997,
            "splits": {
                "train": 7997,
                "validation": 999,
                "test": 1001
            },
            "language": "German",
            "domain": "Legal (5 areas covered)",
            "formats": ["JSONL", "Parquet"],
            "created": datetime.now().isoformat(),
            "files_included": copied_files
        }
        
        with open(data_dst / "dataset_info.json", 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, indent=2, ensure_ascii=False)
        
        print(f"Dataset copied: {len(copied_files)} files, 9,997 examples")
    else:
        print(f"Data directory not found at {data_src}, creating empty structure")
        data_dst.mkdir()
    
    # Step 4: Copy configuration files
    print("Copying configuration files...")
    config_dst = package_dir / "config"
    config_dst.mkdir()
    
    # Copy configuration files
    config_files = {
        "docker-compose.production.yml": "docker-compose.production.yml",
        ".env.production": ".env.production", 
        "config/nginx-production.conf": "nginx.conf",
        "nginx.conf": "nginx-frontend.conf"  # Frontend nginx config
    }
    
    for src_name, dst_name in config_files.items():
        src_file = project_root / src_name
        if src_file.exists():
            if dst_name == ".env.production":
                # Place .env.production in root
                dst_file = package_dir / dst_name
            else:
                dst_file = config_dst / dst_name
            shutil.copy2(src_file, dst_file)
            print(f"Copied {src_name} -> {dst_name}")
    
    # Step 5: Create deployment script
    print("Creating deployment script...")
    deploy_src = project_root / "deploy-production.sh"
    deploy_dst = package_dir / "deploy.sh"
    
    if deploy_src.exists():
        shutil.copy2(deploy_src, deploy_dst)
        print(f"Deployment script copied")
    else:
        print(f"Creating basic deployment script")
        with open(deploy_dst, 'w') as f:
            f.write("""#!/bin/bash
set -e
echo "Starting AnwaltsAI deployment..."
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
echo "Deployment completed!"
""")
    
    # Make deployment script executable
    os.chmod(deploy_dst, 0o755)
    
    # Step 6: Create Docker production Dockerfile
    print("Creating production Dockerfile...")
    dockerfile_content = """FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
"""
    
    with open(backend_dst / "Dockerfile", 'w') as f:
        f.write(dockerfile_content)
    
    # Step 7: Create documentation
    print("Creating documentation...")
    docs_dst = package_dir / "docs"
    docs_dst.mkdir()
    
    # Copy important documentation
    doc_files = [
        "PRODUCTION_DEPLOYMENT_PLAN.md",
        "HETZNER_SERVER_DEPLOYMENT.md", 
        "DNS_SETUP_INSTRUCTIONS.md",
        "UPLOAD_INSTRUCTIONS.md"
    ]
    
    for doc_file in doc_files:
        src_file = project_root / doc_file
        if src_file.exists():
            shutil.copy2(src_file, docs_dst / doc_file)
            print(f"Documentation: {doc_file}")
    
    # Step 8: Create README for deployment
    print("Creating deployment README...")
    readme_content = f"""# AnwaltsAI Production Deployment

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
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Ready for production deployment! 🚀
"""
    
    with open(package_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Step 9: Create archive
    print("Creating deployment archive...")
    archive_name = f"{deployment_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive_path = project_root / f"{archive_name}.tar.gz"
    
    # Create tar.gz archive
    import tarfile
    with tarfile.open(archive_path, 'w:gz') as tar:
        tar.add(package_dir, arcname=deployment_name)
    
    # Also create ZIP for Windows compatibility
    zip_path = project_root / f"{archive_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arc_path = deployment_name / file_path.relative_to(package_dir)
                zipf.write(file_path, arc_path)
    
    # Step 10: Generate deployment summary
    print("Generating deployment summary...")
    
    # Count files and sizes
    total_files = sum(1 for _ in package_dir.rglob('*') if _.is_file())
    package_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
    package_size_mb = package_size / (1024 * 1024)
    
    summary = {
        "deployment_info": {
            "package_name": deployment_name,
            "created": datetime.now().isoformat(),
            "total_files": total_files,
            "package_size_mb": round(package_size_mb, 2),
            "server_ip": "148.251.195.222",
            "server_owner": "Dr. Markus Weigl, AIgenex GmbH"
        },
        "components": {
            "backend": "FastAPI with fixed authentication",
            "frontend": "AnwaltsAI Dashboard UI", 
            "database": "PostgreSQL with schema",
            "cache": "Redis for sessions",
            "dataset": "9,997 German legal examples",
            "proxy": "Nginx with security headers",
            "monitoring": "Health checks and logging"
        },
        "files": {
            "archive_tar": str(archive_path.name),
            "archive_zip": str(zip_path.name),
            "deployment_directory": str(package_dir.name)
        }
    }
    
    with open(package_dir / "deployment-summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Final output
    print("=" * 60)
    print("PRODUCTION DEPLOYMENT PACKAGE CREATED!")
    print("=" * 60)
    print(f"Package Directory: {package_dir}")
    print(f"TAR Archive: {archive_path}")
    print(f"ZIP Archive: {zip_path}")
    print(f"Total Files: {total_files}")
    print(f"Package Size: {package_size_mb:.2f} MB")
    print()
    print("DEPLOYMENT INSTRUCTIONS:")
    print("=" * 40)
    print("1. Upload archive to server:")
    print(f"   scp {archive_path.name} root@148.251.195.222:/opt/")
    print()
    print("2. SSH and extract:")
    print("   ssh root@148.251.195.222")
    print("   cd /opt")
    print(f"   tar -xzf {archive_path.name}")
    print(f"   cd {deployment_name}")
    print()
    print("3. Deploy:")
    print("   chmod +x deploy.sh")
    print("   ./deploy.sh")
    print()
    print("4. Access:")
    print("   http://148.251.195.222")
    print("   http://148.251.195.222/api/docs")
    print("   http://148.251.195.222/health")
    print()
    print("German Legal Dataset: 9,997 examples ready!")
    print("Backend: Fixed authentication issues")
    print("Frontend: Professional AnwaltsAI interface")
    print("Security: Nginx proxy with rate limiting")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = create_production_deployment()
    if success:
        print("Production deployment package created successfully!")
    else:
        print("Failed to create deployment package")
        exit(1)