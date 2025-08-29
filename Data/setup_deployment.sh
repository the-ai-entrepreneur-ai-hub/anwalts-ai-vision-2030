#!/bin/bash
# German Legal AI - AX102 Server Deployment Script
# Optimized for Ryzen 9 7950X3D with 128GB RAM

set -e  # Exit on any error

echo "🇩🇪 German Legal AI - AX102 Deployment Script"
echo "============================================="

# Color codes for output
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
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if script is run as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user."
   exit 1
fi

# System information
print_header "📊 System Information"
echo "CPU: $(lscpu | grep 'Model name' | cut -f 2 -d ':')"
echo "RAM: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "OS: $(lsb_release -d | cut -f 2)"
echo "Kernel: $(uname -r)"
echo

# Check system requirements
print_header "🔍 Checking System Requirements"

# Check CPU (should be Ryzen 9 7950X3D or similar)
CPU_MODEL=$(lscpu | grep 'Model name' | grep -i 'ryzen')
if [[ -n "$CPU_MODEL" ]]; then
    print_status "CPU check passed: AMD Ryzen detected"
else
    print_warning "Expected AMD Ryzen processor, but found: $(lscpu | grep 'Model name' | cut -f 2 -d ':')"
fi

# Check RAM (should be >= 64GB, preferably 128GB)
RAM_GB=$(free -g | grep '^Mem:' | awk '{print $2}')
if [[ $RAM_GB -ge 64 ]]; then
    print_status "RAM check passed: ${RAM_GB}GB available"
else
    print_error "Insufficient RAM: ${RAM_GB}GB (minimum 64GB required)"
    exit 1
fi

# Check disk space (need at least 100GB free)
DISK_FREE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
if [[ $DISK_FREE -ge 100 ]]; then
    print_status "Disk space check passed: ${DISK_FREE}GB free"
else
    print_error "Insufficient disk space: ${DISK_FREE}GB (minimum 100GB required)"
    exit 1
fi

# Update system
print_header "📦 Updating System Packages"
sudo apt update && sudo apt upgrade -y

# Install essential packages
print_header "🛠️ Installing Essential Packages"
sudo apt install -y \
    curl \
    wget \
    git \
    htop \
    nvtop \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    unzip \
    tree \
    jq \
    vim \
    tmux \
    ufw

# Install Docker
print_header "🐳 Installing Docker"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_status "Docker installed successfully"
else
    print_status "Docker already installed"
fi

# Install Docker Compose
print_header "🔧 Installing Docker Compose"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose already installed"
fi

# Create application directory
print_header "📁 Setting up Application Directory"
APP_DIR="/opt/german-legal-ai"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

cd $APP_DIR

# Copy deployment files
print_header "📋 Setting up Deployment Files"
if [[ -f "../Data/docker-compose.yml" ]]; then
    cp ../Data/* .
    print_status "Deployment files copied"
else
    print_warning "Deployment files not found in ../Data/, please copy them manually"
fi

# Create required directories
mkdir -p {models,logs,cache,dataset,ollama_models,vllm_logs,ssl}
mkdir -p {grafana/dashboards,grafana/datasources}

# Set up environment file
print_header "⚙️ Configuring Environment"
cat > .env << EOF
# Model Configuration
MODEL_PATH=/models/disco-german-legal-7b
QUANTIZED_MODEL_PATH=/models/disco-german-legal-7b-gptq
USE_QUANTIZED=true

# Performance Settings - Optimized for Ryzen 9 7950X3D
TORCH_NUM_THREADS=28
OMP_NUM_THREADS=28
MKL_NUM_THREADS=28
OPENBLAS_NUM_THREADS=28
VECLIB_MAXIMUM_THREADS=28
NUMEXPR_NUM_THREADS=28

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# API Configuration
MAX_CONTEXT_LENGTH=2048
BATCH_SIZE=4
TEMPERATURE=0.7
TOP_P=0.9

# Monitoring
PROMETHEUS_RETENTION=200h
GRAFANA_ADMIN_PASSWORD=admin123

# Security
NGINX_RATE_LIMIT=10r/s
EOF

print_status "Environment configuration created"

# System optimization for AI workloads
print_header "🚀 Optimizing System for AI Workloads"

# Configure huge pages
print_status "Configuring huge pages..."
echo 'vm.nr_hugepages=65536' | sudo tee -a /etc/sysctl.conf
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# CPU performance settings
print_status "Configuring CPU performance..."
# Set CPU governor to performance (if available)
if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
    echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
fi

# Disable swap (not recommended for 128GB RAM system, but can help with AI workloads)
# sudo swapoff -a
# print_status "Swap disabled"

# Apply sysctl changes
sudo sysctl -p

# Configure Redis
print_header "🔴 Configuring Redis"
cat > redis.conf << EOF
# Redis configuration for German Legal AI
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF

# Configure Prometheus
print_header "📊 Configuring Monitoring"
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'german-legal-ai'
    static_configs:
      - targets: ['german-legal-ai:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
EOF

# Set up firewall
print_header "🔐 Configuring Firewall"
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 3000/tcp # Grafana (optional, for monitoring)
sudo ufw allow 9090/tcp # Prometheus (optional, for monitoring)
sudo ufw --force enable

print_status "Firewall configured"

# Create systemd service for auto-start
print_header "🔄 Setting up Auto-start Service"
sudo tee /etc/systemd/system/german-legal-ai.service > /dev/null << EOF
[Unit]
Description=German Legal AI Services
Requires=docker.service
After=docker.service

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable german-legal-ai.service

print_status "Auto-start service configured"

# Create useful scripts
print_header "📜 Creating Management Scripts"

# Start script
cat > start.sh << 'EOF'
#!/bin/bash
echo "Starting German Legal AI services..."
docker-compose up -d
echo "Services started. Check status with: docker-compose ps"
EOF
chmod +x start.sh

# Stop script
cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stopping German Legal AI services..."
docker-compose down
echo "Services stopped."
EOF
chmod +x stop.sh

# Status script
cat > status.sh << 'EOF'
#!/bin/bash
echo "=== Service Status ==="
docker-compose ps

echo -e "\n=== Resource Usage ==="
docker stats --no-stream

echo -e "\n=== Health Check ==="
curl -s http://localhost/health | jq '.' 2>/dev/null || echo "Health endpoint not responding"

echo -e "\n=== System Resources ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"
EOF
chmod +x status.sh

# Update script
cat > update.sh << 'EOF'
#!/bin/bash
echo "Updating German Legal AI..."
docker-compose pull
docker-compose up -d
echo "Update complete. Services restarted."
EOF
chmod +x update.sh

# Logs script
cat > logs.sh << 'EOF'
#!/bin/bash
if [ "$1" = "" ]; then
    echo "Available services:"
    docker-compose ps --services
    echo "Usage: ./logs.sh <service-name>"
    echo "Example: ./logs.sh german-legal-ai"
else
    docker-compose logs -f "$1"
fi
EOF
chmod +x logs.sh

print_status "Management scripts created"

# Performance test script
cat > test_performance.py << 'EOF'
#!/usr/bin/env python3
"""
Performance test script for German Legal AI
"""
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import json

def test_single_request():
    url = "http://localhost/api/generate"
    payload = {
        "instruction": "Analysiere die rechtlichen Aspekte einer Kündigung während der Probezeit.",
        "input_text": "Ein Arbeitnehmer wurde nach 8 Monaten Probezeit gekündigt.",
        "max_length": 256,
        "temperature": 0.7
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            return end_time - start_time
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def run_performance_test(num_requests=10, concurrent=False):
    print(f"Running performance test with {num_requests} requests...")
    print(f"Concurrent: {concurrent}")
    
    if concurrent:
        with ThreadPoolExecutor(max_workers=5) as executor:
            times = list(filter(None, executor.map(lambda _: test_single_request(), range(num_requests))))
    else:
        times = []
        for i in range(num_requests):
            print(f"Request {i+1}/{num_requests}")
            time_taken = test_single_request()
            if time_taken:
                times.append(time_taken)
    
    if times:
        print(f"\nPerformance Results:")
        print(f"Total requests: {len(times)}")
        print(f"Average time: {statistics.mean(times):.2f}s")
        print(f"Median time: {statistics.median(times):.2f}s")
        print(f"Min time: {min(times):.2f}s")
        print(f"Max time: {max(times):.2f}s")
        print(f"Success rate: {len(times)/num_requests*100:.1f}%")
    else:
        print("No successful requests!")

if __name__ == "__main__":
    # Test health first
    try:
        health = requests.get("http://localhost/health", timeout=10)
        if health.status_code == 200:
            print("✅ Health check passed")
            run_performance_test(num_requests=5, concurrent=False)
        else:
            print("❌ Health check failed")
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
EOF
chmod +x test_performance.py

print_status "Performance test script created"

# Create model download instructions
cat > download_models.md << 'EOF'
# Model Download Instructions

## After Training in Google Colab

1. Download the model zip file from Colab
2. Transfer to your AX102 server:
   ```bash
   scp german-legal-model.zip user@your-server:/opt/german-legal-ai/
   ```

3. Extract the models:
   ```bash
   cd /opt/german-legal-ai
   unzip german-legal-model.zip
   mv disco-german-legal-7b models/
   mv disco-german-legal-7b-gptq models/
   ```

## Alternative: Use Pre-trained German Models

If you want to start with existing German models:

```bash
# Download DiscoLM German 7B (requires HuggingFace token)
cd models
git lfs clone https://huggingface.co/DiscoResearch/DiscoLM_German_7b_v1 disco-german-legal-7b

# Or use Ollama for easy setup
docker exec -it ollama-german-legal ollama pull disco-lm-german-7b
```

## Start the Services

Once models are in place:
```bash
./start.sh
```
EOF

print_status "Model download instructions created"

# Final summary
print_header "🎉 Deployment Setup Complete!"
echo
print_status "System optimized for German Legal AI workloads"
print_status "Docker and Docker Compose installed"
print_status "Application directory created: $APP_DIR"
print_status "Firewall configured"
print_status "Auto-start service enabled"
print_status "Management scripts ready"
echo

print_header "📋 Next Steps:"
echo "1. 📥 Download trained models from Google Colab"
echo "2. 📁 Extract models to: $APP_DIR/models/"
echo "3. 🚀 Start services: ./start.sh"
echo "4. ✅ Test deployment: ./test_performance.py"
echo "5. 📊 Monitor: ./status.sh"
echo

print_header "🔗 Useful Commands:"
echo "• Start services: ./start.sh"
echo "• Stop services: ./stop.sh"  
echo "• Check status: ./status.sh"
echo "• View logs: ./logs.sh german-legal-ai"
echo "• Test performance: python3 test_performance.py"
echo "• Health check: curl http://localhost/health"
echo

print_header "🌐 Web Interfaces (after starting):"
echo "• API: http://localhost/api/generate"
echo "• Health: http://localhost/health"
echo "• Grafana: http://localhost:3000 (admin/admin123)"
echo "• Prometheus: http://localhost:9090"
echo

print_warning "⚠️  IMPORTANT: You need to reboot or logout/login for Docker group changes to take effect!"
print_warning "⚠️  Remember to download and extract your trained models before starting services!"

echo
print_status "Deployment setup completed successfully! 🚀"
EOF