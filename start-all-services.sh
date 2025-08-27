#!/usr/bin/env bash
set -euo pipefail

# Start sanitizer + backend + frontend + deps
# Usage: ./start-all-services.sh [prod]

mode=${1:-dev}

if [[ "$mode" == "prod" ]]; then
  echo "Starting services in PRODUCTION mode (docker-compose.production.yml)"
  docker compose -f docker-compose.production.yml up -d --build
else
  echo "Starting services in DEV mode (docker-compose.yml)"
  docker compose up -d --build
fi

echo "Waiting for backend health..."
# Basic wait loop for backend health
for i in {1..30}; do
  if curl -sf http://127.0.0.1:8000/health >/dev/null; then
    echo "Backend healthy."
    exit 0
  fi
  echo "...still waiting ($i)"; sleep 2
done

echo "Backend health check failed. Check docker logs."
exit 1
