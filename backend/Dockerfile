# Multi-stage Dockerfile for AnwaltsAI Backend
# Production-optimized with security and performance best practices

# ============ Base Stage ============
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create directories
RUN mkdir -p /app /app/logs /app/uploads && \
    chown -R appuser:appuser /app

WORKDIR /app

# ============ Development Stage ============
FROM base as development

# Copy requirements first for better caching
COPY requirements.txt ./
COPY requirements-dev.txt ./

# Install dependencies
RUN pip install -r requirements.txt -r requirements-dev.txt

# Copy source code
COPY --chown=appuser:appuser . .

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Development command with auto-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# ============ Production Stage ============
FROM base as production

# Copy requirements
COPY requirements.txt ./

# Install production dependencies only
RUN pip install --no-deps -r requirements.txt && \
    pip install gunicorn[gthread]==21.2.0

# Copy source code
COPY --chown=appuser:appuser *.py ./
COPY --chown=appuser:appuser migration/ ./migration/
COPY --chown=appuser:appuser database/ ./database/

# Create necessary directories
RUN mkdir -p logs uploads && \
    chown -R appuser:appuser logs uploads

# Switch to app user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command with Gunicorn
CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--preload", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "120", \
     "--keep-alive", "5"]