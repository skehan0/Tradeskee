FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies with security updates
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    --no-install-recommends \
    gcc \
    g++ \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (better cache)
COPY requirements.txt .

# Upgrade pip and install dependencies securely
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1001 appuser

# Copy application code and set ownership
COPY --chown=appuser:appgroup src/ ./src
COPY --chown=appuser:appgroup config.py .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start backend (FastAPI + Uvicorn)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
