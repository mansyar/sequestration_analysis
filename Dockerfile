# Multi-stage build for smaller, secure image
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Install dependencies in builder stage
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim-bookworm

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code with proper ownership
COPY --chown=appuser:appgroup . .

# Security: Set proper permissions
RUN chmod -R 755 /app && \
    chown -R appuser:appgroup /app

# Security: Switch to non-root user
USER appuser

# Ensure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Security: Don't store Python bytecode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port (non-privileged)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Security labels
LABEL org.opencontainers.image.source="https://github.com/ansyar/sequestration-calculator"
LABEL org.opencontainers.image.description="Indonesia Carbon Sequestration Calculator"
LABEL org.opencontainers.image.licenses="MIT"

# Run with uvicorn (non-root, with proxy headers for HTTPS)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
