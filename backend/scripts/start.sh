#!/bin/bash
# AnwaltsAI Backend Startup Script

set -e

echo "🚀 Starting AnwaltsAI Backend Server..."

# Load environment variables
if [ -f .env ]; then
    echo "📁 Loading environment variables from .env"
    export $(cat .env | xargs)
fi

# Default values
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
LOG_LEVEL=${LOG_LEVEL:-info}
ENVIRONMENT=${ENVIRONMENT:-development}

echo "🔧 Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Log Level: $LOG_LEVEL"

# Create necessary directories
mkdir -p logs uploads

# Run database migrations (if needed)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔄 Running database migrations..."
    python -m alembic upgrade head
fi

# Start the server based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🔨 Starting development server with auto-reload..."
    uvicorn main:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level $LOG_LEVEL
else
    echo "🏭 Starting production server with Gunicorn..."
    gunicorn main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers $WORKERS \
        --bind $HOST:$PORT \
        --log-level $LOG_LEVEL \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --pid logs/gunicorn.pid \
        --daemon
fi

echo "✅ AnwaltsAI Backend Server started successfully!"