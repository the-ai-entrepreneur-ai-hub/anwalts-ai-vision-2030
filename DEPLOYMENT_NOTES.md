# AnwaltsAI Document Upload Integration - Developer Notes

This document summarizes the document upload architecture and how to run it in dev and production.

## Overview

- Frontend (nginx serving `Client/`)
- Backend (FastAPI, port 8000)
- Secure Sanitizer Service (Flask, port 5001)
- PostgreSQL + Redis

The frontend uploads files to the backend `/api/documents/upload`. The backend proxies the file to the sanitizer at `SANITIZER_URL/process-document` and returns the sanitizer JSON response. Legacy `/process-document` endpoint is preserved as an alias.

## Key Changes

- `Client/api-client.js`: `processDocument(file)` now targets `/api/documents/upload` (fallback to `/process-document`).
- `Client/anwalts-ai-dashboard.html`: Real upload handler replaces the simulated one.
- `backend/main.py`:
  - `POST /api/documents/upload` and `POST /process-document` (legacy) endpoints added.
  - Both require JWT and proxy to sanitizer (`SANITIZER_URL`).
- `backend/.env.template`: added `SANITIZER_URL`.
- `docker-compose.yml` and `docker-compose.production.yml`: added `sanitizer` service and wired `SANITIZER_URL` in backend.
- `start-all-services.sh`: orchestrates dev/prod startup.

## Environment

- Backend uses `SANITIZER_URL` (default: `http://127.0.0.1:5001` locally; in Docker: `http://sanitizer:5001`).
- Provide `TOGETHER_API_KEY` in a local `.env` for sanitizer when running via Docker (not committed).

## Run (Development)

```bash
./start-all-services.sh
# Frontend: http://localhost:3000
# Backend health: http://localhost:8000/health
# Sanitizer (internal): http://localhost:5001
```

Direct test:

```bash
curl -sS -X POST -F 'file=@test.pdf' http://127.0.0.1:8000/api/documents/upload | jq .
```

## Run (Production)

```bash
./start-all-services.sh prod
```

- Public access goes through `nginx` defined in `docker-compose.production.yml`.
- Backend and Sanitizer are not exposed publicly; only nginx exposes 80/443.

## Security Notes

- Do not expose sanitizer directly to the internet; use backend proxy.
- Keep `TOGETHER_API_KEY` and JWT secrets out of Git.
- Size limits enforced at sanitizer (50MB) — validate client-side where possible.

## Future Work

- Persist processed document metadata/content in DB.
- Add `/api/documents/list` and retrieval endpoints.
- Add health checks for sanitizer in backend before proxying.

