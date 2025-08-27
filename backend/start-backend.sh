#!/bin/bash
echo "Starting AnwaltsAI Backend..."

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install fastapi uvicorn sqlalchemy databases[sqlite] python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv httpx aiosqlite

# Set environment variables
export DATABASE_URL="sqlite:///./anwalts_ai.db"
export TOGETHER_API_KEY="REDACTED"
export JWT_SECRET_KEY="local-dev-secret"
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:5500"

echo "Starting FastAPI server on http://localhost:8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload