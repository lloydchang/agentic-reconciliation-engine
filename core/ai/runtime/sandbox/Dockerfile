# Sandbox Operator for Open SWE
# Provides safe execution environments for infrastructure code testing

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 sandbox

# Set working directory
WORKDIR /app

# Copy provider abstraction layer
COPY --chown=sandbox:sandbox providers/ ./providers/
COPY --chown=sandbox:sandbox audit-logger.go ./

# Switch to non-root user
USER sandbox

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Expose port
EXPOSE 8080

# Default command - operator mode
CMD ["python3", "-m", "providers", "--mode", "operator"]
