#!/bin/bash
echo "Starting AnwaltsAI Local Development Environment..."

# Check if Docker is running
if ! docker version >/dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Start the application
echo "Starting services with docker-compose..."
docker-compose up -d

echo ""
echo "================================================"
echo "AnwaltsAI Local Development Started!"
echo "================================================"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Database: localhost:5432"
echo "Redis: localhost:6379"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo "================================================"

# Wait a moment for services to start
sleep 5

# Open the application in browser (Linux/Mac)
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
fi