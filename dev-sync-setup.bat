@echo off
REM Development Sync Setup for AnwaltsAI
REM Creates real-time sync between local development and server

echo =====================================================
echo 🔄 AnwaltsAI Development Sync Setup
echo =====================================================
echo Server: 148.251.195.222 (Hetzner AX102)
echo Local: Windows Development Environment
echo =====================================================
echo.

REM Check if required tools are available
echo 🔧 Checking requirements...

REM Check for SSH
where ssh >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ SSH not found! Please install OpenSSH client
    echo Install from: Settings > Apps > Optional Features > OpenSSH Client
    pause
    exit /b 1
)
echo ✅ SSH found

REM Check for rsync (via WSL or Git Bash)
where rsync >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ rsync not found - will use alternative sync method
    set USE_RSYNC=false
) else (
    echo ✅ rsync found
    set USE_RSYNC=true
)

REM Check for Node.js (for file watching)
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js not found! Please install Node.js
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js found

echo.
echo 📋 Available Sync Options:
echo 1. Real-time File Sync (recommended for active development)
echo 2. On-demand Sync (manual push when ready)
echo 3. Git-based Sync (commit and deploy)
echo 4. Container Sync (Docker bind mounts for development)
echo.
set /p SYNC_CHOICE="Choose sync method (1-4): "

if "%SYNC_CHOICE%"=="1" goto :realtime_sync
if "%SYNC_CHOICE%"=="2" goto :ondemand_sync
if "%SYNC_CHOICE%"=="3" goto :git_sync
if "%SYNC_CHOICE%"=="4" goto :container_sync
echo Invalid choice!
pause
exit /b 1

:realtime_sync
echo.
echo 🔄 Setting up Real-time File Sync...
echo =====================================================

REM Create file watcher script
cat > file-watcher.js << 'EOF'
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Configuration
const SERVER = '148.251.195.222';
const USER = 'root';
const REMOTE_PATH = '/opt/anwalts-ai-production/';
const LOCAL_PATHS = [
    'backend/',
    'Client/',
    'config/'
];

// Debounce function to avoid rapid uploads
let uploadTimeout;
function debounceUpload(filePath, delay = 2000) {
    clearTimeout(uploadTimeout);
    uploadTimeout = setTimeout(() => {
        syncFile(filePath);
    }, delay);
}

// Sync single file to server
function syncFile(filePath) {
    const relativePath = path.relative(process.cwd(), filePath);
    const remoteFile = `${USER}@${SERVER}:${REMOTE_PATH}${relativePath}`;
    
    console.log(`📤 Syncing: ${relativePath}`);
    
    // Use SCP to copy file
    exec(`scp "${filePath}" "${remoteFile}"`, (error, stdout, stderr) => {
        if (error) {
            console.error(`❌ Sync error: ${error.message}`);
            return;
        }
        if (stderr && !stderr.includes('Warning')) {
            console.error(`⚠️ Sync warning: ${stderr}`);
        }
        console.log(`✅ Synced: ${relativePath}`);
    });
}

// Watch for file changes
console.log('🔍 Starting file watcher...');
console.log('Watching directories:', LOCAL_PATHS);

LOCAL_PATHS.forEach(localPath => {
    if (fs.existsSync(localPath)) {
        fs.watch(localPath, { recursive: true }, (eventType, filename) => {
            if (filename && eventType === 'change') {
                const fullPath = path.join(localPath, filename);
                
                // Skip certain files
                if (filename.includes('.git') || 
                    filename.includes('node_modules') ||
                    filename.includes('__pycache__') ||
                    filename.endsWith('.log')) {
                    return;
                }
                
                console.log(`📝 File changed: ${fullPath}`);
                debounceUpload(fullPath);
            }
        });
        console.log(`✅ Watching: ${localPath}`);
    } else {
        console.log(`⚠️ Path not found: ${localPath}`);
    }
});

console.log('🔄 File sync active! Press Ctrl+C to stop.');
EOF

REM Install chokidar for better file watching (optional)
echo Installing file watcher dependencies...
npm init -y >nul 2>nul
npm install chokidar --save-dev >nul 2>nul

echo.
echo ✅ Real-time sync configured!
echo.
echo 📋 Usage:
echo   Start sync: node file-watcher.js
echo   Stop sync:  Ctrl+C
echo.
echo 🔧 Configuration:
echo   - Server: %SERVER%
echo   - Remote path: /opt/anwalts-ai-production/
echo   - Local paths: backend/, Client/, config/
echo.

REM Create start script
echo @echo off > start-dev-sync.bat
echo echo 🔄 Starting AnwaltsAI Development Sync... >> start-dev-sync.bat
echo node file-watcher.js >> start-dev-sync.bat

echo 🚀 To start sync: run start-dev-sync.bat
goto :end

:ondemand_sync
echo.
echo 📤 Setting up On-demand Sync...
echo =====================================================

REM Create sync script
cat > sync-to-server.bat << 'EOF'
@echo off
echo 🔄 Syncing AnwaltsAI to server...
echo =====================================================

REM Create list of files to sync
echo 📋 Files to sync:
echo   - backend/ (Python files)
echo   - Client/ (Frontend files)
echo   - config/ (Configuration)
echo.

set /p CONFIRM="Continue with sync? (Y/N): "
if /i not "%CONFIRM%"=="Y" if /i not "%CONFIRM%"=="YES" (
    echo ❌ Sync cancelled
    pause
    exit /b 0
)

echo.
echo 📤 Uploading files...

REM Sync backend
echo Syncing backend...
scp -r backend root@148.251.195.222:/opt/anwalts-ai-production/

REM Sync frontend
echo Syncing frontend...
scp -r Client root@148.251.195.222:/opt/anwalts-ai-production/frontend/

REM Sync config
echo Syncing config...
scp -r config root@148.251.195.222:/opt/anwalts-ai-production/

echo.
echo ✅ Sync completed!
echo.
echo 🔄 Next steps on server:
echo   ssh root@148.251.195.222
echo   cd /opt/anwalts-ai-production
echo   docker-compose -f docker-compose.production.yml restart backend
echo.
pause
EOF

chmod +x sync-to-server.bat

echo ✅ On-demand sync configured!
echo.
echo 📋 Usage: run sync-to-server.bat when ready to deploy
goto :end

:git_sync
echo.
echo 🔧 Setting up Git-based Sync...
echo =====================================================

REM Create git hooks for automatic deployment
cat > git-deploy.sh << 'EOF'
#!/bin/bash
# Git-based deployment script

echo "🔄 Git-based deployment to server..."

# Commit changes
echo "📝 Committing changes..."
git add .
git commit -m "Development update: $(date)"

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf anwalts-ai-dev-$(date +%Y%m%d_%H%M%S).tar.gz \
    backend/ Client/ config/ \
    --exclude='*.log' --exclude='__pycache__' --exclude='node_modules'

# Upload to server
echo "📤 Uploading to server..."
scp anwalts-ai-dev-*.tar.gz root@148.251.195.222:/opt/

# SSH and deploy
echo "🚀 Deploying on server..."
ssh root@148.251.195.222 << 'DEPLOY'
cd /opt
tar -xzf anwalts-ai-dev-*.tar.gz -C anwalts-ai-production --strip-components=0
cd anwalts-ai-production
docker-compose -f docker-compose.production.yml restart
echo "✅ Deployment completed!"
DEPLOY

echo "✅ Git deployment finished!"
EOF

chmod +x git-deploy.sh

echo ✅ Git-based sync configured!
echo.
echo 📋 Usage: run git-deploy.sh when ready to commit and deploy
goto :end

:container_sync
echo.
echo 🐳 Setting up Container Development Sync...
echo =====================================================

REM Create development docker-compose with bind mounts
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  # Development PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: anwalts_postgres_dev
    environment:
      POSTGRES_DB: anwalts_ai_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    networks:
      - anwalts_dev_network

  # Development Redis
  redis:
    image: redis:7-alpine
    container_name: anwalts_redis_dev
    ports:
      - "6379:6379"
    networks:
      - anwalts_dev_network

  # Development Backend with live reload
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: anwalts_backend_dev
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=development
      - DEBUG=true
      - DATABASE_URL=postgresql://postgres:dev_password@postgres:5432/anwalts_ai_db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend:/app:cached  # Live reload
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - anwalts_dev_network

  # Development Frontend with live reload
  frontend:
    image: nginx:alpine
    container_name: anwalts_frontend_dev
    ports:
      - "3000:80"
    volumes:
      - ./Client:/usr/share/nginx/html:cached  # Live reload
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - anwalts_dev_network

volumes:
  postgres_dev_data:

networks:
  anwalts_dev_network:
    driver: bridge
EOF

REM Create development Dockerfile with hot reload
mkdir backend 2>nul
cat > backend/Dockerfile.dev << 'EOF'
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install development dependencies
RUN pip install watchdog

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Development command with auto-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

echo ✅ Container development sync configured!
echo.
echo 📋 Usage:
echo   Start dev environment: docker-compose -f docker-compose.dev.yml up -d
echo   Stop dev environment:  docker-compose -f docker-compose.dev.yml down
echo   View logs:             docker-compose -f docker-compose.dev.yml logs -f
echo.
echo 🔄 Features:
echo   - Live code reload for backend and frontend
echo   - Separate development database
echo   - Hot module replacement
echo   - Development logging
goto :end

:end
echo.
echo =====================================================
echo ✅ Development Sync Setup Complete!
echo =====================================================
echo.
echo 📋 Available sync methods configured:
if exist file-watcher.js echo   ✅ Real-time File Sync (file-watcher.js)
if exist sync-to-server.bat echo   ✅ On-demand Sync (sync-to-server.bat)  
if exist git-deploy.sh echo   ✅ Git-based Sync (git-deploy.sh)
if exist docker-compose.dev.yml echo   ✅ Container Development (docker-compose.dev.yml)
echo.
echo 🔧 Server Configuration:
echo   IP: 148.251.195.222
echo   Path: /opt/anwalts-ai-production/
echo   User: root
echo.
echo 📖 Documentation created in sync-methods.md
echo.

REM Create documentation
cat > sync-methods.md << 'EOF'
# AnwaltsAI Development Sync Methods

## 1. Real-time File Sync ⚡
**Best for**: Active development with immediate feedback
```bash
node file-watcher.js
```
- Watches file changes automatically
- Syncs modified files within 2 seconds
- Uses SCP for reliable transfer

## 2. On-demand Sync 📤
**Best for**: Controlled deployments
```bash
sync-to-server.bat
```
- Manual sync when ready
- Syncs all changes at once
- Prompts for confirmation

## 3. Git-based Sync 🔧
**Best for**: Version-controlled deployments  
```bash
git-deploy.sh
```
- Commits changes to git
- Creates versioned deployment package
- Deploys and restarts services

## 4. Container Development 🐳
**Best for**: Full development environment
```bash
docker-compose -f docker-compose.dev.yml up -d
```
- Live reload for all components
- Isolated development database
- Hot module replacement

## Server Commands
After syncing, restart services:
```bash
ssh root@148.251.195.222
cd /opt/anwalts-ai-production
docker-compose -f docker-compose.production.yml restart
```

## Troubleshooting
- **SSH issues**: Check OpenSSH client installation
- **Permission errors**: Verify server access
- **File sync delays**: Check network connection
- **Container issues**: Check Docker installation
EOF

echo 📖 Full documentation available in sync-methods.md
echo.
pause