#!/bin/bash
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
