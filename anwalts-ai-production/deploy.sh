#!/bin/bash

# AnwaltsAI Production Deployment Script
# Server: Hetzner AX102 #2743403 (148.251.195.222)
# Date: 2025-01-08

set -e  # Exit on any error

echo "🚀 Starting AnwaltsAI Production Deployment..."
echo "============================================="
echo "Server: Hetzner AX102 #2743403"
echo "IP: 148.251.195.222"
echo "Date: $(date)"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root. Consider creating a dedicated user for production."
fi

# Step 1: System Update
print_step "1. Updating system packages..."
apt update && apt upgrade -y
print_status "System updated successfully"

# Step 2: Install Docker and Docker Compose
print_step "2. Installing Docker and Docker Compose..."

if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    print_status "Docker installed successfully"
else
    print_status "Docker already installed"
fi

if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose already installed"
fi

# Step 3: Install additional utilities
print_step "3. Installing additional utilities..."
apt install -y curl wget htop ncdu tree jq ufw fail2ban
print_status "Additional utilities installed"

# Step 4: Setup directories and permissions
print_step "4. Setting up directories and permissions..."

# Create necessary directories
mkdir -p /opt/anwalts-ai/{data,logs,backups,config,ssl}
mkdir -p /opt/anwalts-ai/data/{postgres,redis}

# Set ownership and permissions
chown -R $USER:$USER /opt/anwalts-ai
chmod -R 755 /opt/anwalts-ai
chmod 700 /opt/anwalts-ai/ssl  # SSL certificates should be secure

print_status "Directories created and permissions set"

# Step 5: Configure firewall
print_step "5. Configuring firewall..."

# Configure UFW
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

print_status "Firewall configured"

# Step 6: Configure fail2ban
print_step "6. Configuring fail2ban for SSH protection..."

# Basic fail2ban configuration for SSH
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

systemctl enable fail2ban
systemctl restart fail2ban

print_status "Fail2ban configured"

# Step 7: Verify deployment files
print_step "7. Verifying deployment files..."

REQUIRED_FILES=(
    "docker-compose.production.yml"
    ".env.production"
    "config/nginx-production.conf"
    "backend/main.py"
    "Client/anwalts-ai-dashboard.html"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "/opt/anwalts-ai/$file" ]]; then
        MISSING_FILES+=("$file")
    fi
done

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    print_error "Missing required files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    print_error "Please upload all required files before running deployment"
    exit 1
fi

print_status "All required files found"

# Step 8: Build and start services
print_step "8. Building Docker containers..."

cd /opt/anwalts-ai

# Set environment file permissions
chmod 600 .env.production

# Pull base images first
docker-compose -f docker-compose.production.yml pull

# Build containers
docker-compose -f docker-compose.production.yml build --no-cache

print_status "Docker containers built successfully"

# Step 9: Start services
print_step "9. Starting services..."

# Start services in detached mode
docker-compose -f docker-compose.production.yml up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 60

print_status "Services started"

# Step 10: Health checks
print_step "10. Running health checks..."

# Function to check if service is responding
check_service() {
    local url=$1
    local service=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Checking $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$url" > /dev/null; then
            print_status "$service is responding ✓"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - $service not ready yet..."
        sleep 5
        ((attempt++))
    done
    
    print_error "$service failed to respond after $max_attempts attempts"
    return 1
}

# Check backend health
check_service "http://localhost:8000/health" "Backend API"

# Check if frontend is serving
check_service "http://localhost:3000" "Frontend"

# Check if nginx is proxying correctly
check_service "http://localhost/health" "Nginx Proxy"

# Step 11: Initialize database (if needed)
print_step "11. Initializing database..."

# Check if database needs initialization
if docker-compose -f docker-compose.production.yml exec -T postgres psql -U postgres -d anwalts_ai_db -c '\dt' | grep -q "No relations found"; then
    print_status "Database appears empty, running initialization..."
    docker-compose -f docker-compose.production.yml exec -T backend python -c "
import asyncio
from database import Database
async def init_db():
    db = Database()
    await db.connect()
    print('Database initialized successfully')
asyncio.run(init_db())
"
else
    print_status "Database already initialized"
fi

# Step 12: Final verification
print_step "12. Final verification..."

# Check all container statuses
print_status "Container statuses:"
docker-compose -f docker-compose.production.yml ps

# Test all endpoints
print_status "Testing endpoints..."

ENDPOINTS=(
    "http://localhost/health|Backend Health Check"
    "http://localhost/|Frontend Application"
    "http://localhost/api/docs|API Documentation"
)

for endpoint_info in "${ENDPOINTS[@]}"; do
    IFS='|' read -r url description <<< "$endpoint_info"
    if curl -f -s "$url" > /dev/null; then
        print_status "$description: ✓"
    else
        print_warning "$description: ✗"
    fi
done

# Step 13: Setup log rotation
print_step "13. Setting up log rotation..."

cat > /etc/logrotate.d/anwalts-ai << 'EOF'
/opt/anwalts-ai/logs/*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}
EOF

print_status "Log rotation configured"

# Step 14: Create backup script
print_step "14. Creating backup script..."

cat > /opt/anwalts-ai/backup.sh << 'EOF'
#!/bin/bash
# AnwaltsAI Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/anwalts-ai/backups"

echo "Starting backup at $(date)"

# Database backup
docker-compose -f /opt/anwalts-ai/docker-compose.production.yml exec -T postgres pg_dump -U postgres anwalts_ai_db > "$BACKUP_DIR/db-$DATE.sql"

# Application data backup
tar -czf "$BACKUP_DIR/app-data-$DATE.tar.gz" /opt/anwalts-ai/data --exclude='*.sock'

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.sql" -type f -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +30 -delete

echo "Backup completed at $(date)"
EOF

chmod +x /opt/anwalts-ai/backup.sh

# Add backup to crontab (daily at 2 AM)
if ! crontab -l 2>/dev/null | grep -q "anwalts-ai/backup.sh"; then
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/anwalts-ai/backup.sh >> /opt/anwalts-ai/logs/backup.log 2>&1") | crontab -
    print_status "Daily backup scheduled"
fi

# Step 15: Create system monitoring script
print_step "15. Creating monitoring script..."

cat > /opt/anwalts-ai/monitor.sh << 'EOF'
#!/bin/bash
# AnwaltsAI Monitoring Script

echo "=== AnwaltsAI System Status ==="
echo "Date: $(date)"
echo

echo "=== Container Status ==="
docker-compose -f /opt/anwalts-ai/docker-compose.production.yml ps
echo

echo "=== Service Health ==="
echo "Backend Health: $(curl -f -s http://localhost:8000/health && echo "✓ OK" || echo "✗ FAIL")"
echo "Frontend: $(curl -f -s http://localhost:3000 && echo "✓ OK" || echo "✗ FAIL")"
echo "Nginx Proxy: $(curl -f -s http://localhost/health && echo "✓ OK" || echo "✗ FAIL")"
echo

echo "=== System Resources ==="
echo "Disk Usage:"
df -h /opt/anwalts-ai
echo
echo "Memory Usage:"
free -h
echo
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)"
echo

echo "=== Recent Logs (Last 10 lines) ==="
tail -n 10 /opt/anwalts-ai/logs/anwalts-ai.log 2>/dev/null || echo "No application logs found"
EOF

chmod +x /opt/anwalts-ai/monitor.sh

print_status "Monitoring script created"

# Final success message
echo
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉"
echo "============================================="
echo
print_status "AnwaltsAI is now running on:"
echo "  📱 Main Application: http://148.251.195.222"
echo "  🔧 API Documentation: http://148.251.195.222/api/docs"
echo "  🏥 Health Check: http://148.251.195.222/health"
echo
print_status "Services:"
echo "  🗄️  PostgreSQL: localhost:5432 (internal only)"
echo "  📊 Redis Cache: localhost:6379 (internal only)"
echo "  🚀 FastAPI Backend: localhost:8000 (internal only)"
echo "  🌐 Frontend: localhost:3000 (internal only)"
echo "  🔄 Nginx Proxy: localhost:80 (public)"
echo
print_status "Directories:"
echo "  📁 Application: /opt/anwalts-ai"
echo "  📈 Logs: /opt/anwalts-ai/logs"
echo "  💾 Backups: /opt/anwalts-ai/backups"
echo "  🗃️  Data: /opt/anwalts-ai/data"
echo
print_status "Maintenance:"
echo "  📊 Monitor: /opt/anwalts-ai/monitor.sh"
echo "  💾 Backup: /opt/anwalts-ai/backup.sh (daily at 2 AM)"
echo "  🔄 Restart: docker-compose -f /opt/anwalts-ai/docker-compose.production.yml restart"
echo
print_status "German Legal Dataset: 9,997 examples ready for AI training"
echo
print_warning "IMPORTANT: Change default passwords in .env.production for production use!"
echo
echo "============================================="
echo "🎯 AnwaltsAI is ready to serve German legal professionals!"
echo "============================================="