#!/bin/bash
echo "Starting AnwaltsAI Locally (No Docker)..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo ""
echo "================================================"
echo "Setting up Backend..."
echo "================================================"

# Navigate to backend directory
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set environment variables for local development
export DATABASE_URL="sqlite:///./anwalts_ai.db"
export REDIS_URL="redis://localhost:6379/0"
export TOGETHER_API_KEY="5b5174dc42932c781810d4be36a11435fe07cdf2d95b8cac17c29c7f87e10720"
export JWT_SECRET_KEY="local-development-jwt-secret-key"
export ENVIRONMENT="development"
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:5500"

echo ""
echo "Starting FastAPI backend server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Go back to root and start frontend
cd ..

echo ""
echo "================================================"
echo "Setting up Frontend..."
echo "================================================"

# Start a simple HTTP server for frontend
cd Client
echo "Starting frontend HTTP server..."
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo ""
echo "================================================"
echo "AnwaltsAI Started Successfully!"
echo "================================================"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To stop: Press Ctrl+C"
echo "================================================"

# Open in browser (if available)
if command -v xdg-open > /dev/null; then
    sleep 2
    xdg-open http://localhost:3000
elif command -v open > /dev/null; then
    sleep 2
    open http://localhost:3000
fi

# Wait for user interrupt
wait