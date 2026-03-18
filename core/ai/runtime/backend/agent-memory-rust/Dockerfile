# Simple build for agent-memory-rust
FROM rust:1.65 as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . .

# Build the application with timeout
RUN timeout 300 cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 agent

# Set up directories
RUN mkdir -p /data && chown agent:agent /data

# Copy binary
COPY --from=builder /app/target/release/agent-memory /usr/local/bin/agent-memory

# Set permissions
RUN chmod +x /usr/local/bin/agent-memory

# Switch to non-root user
USER agent

# Expose port
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Set environment variables
ENV DATABASE_PATH=/data/memory.db
ENV INBOX_PATH=/data/inbox
ENV BIND_ADDRESS=0.0.0.0
ENV PORT=8080
ENV METRICS_ENABLED=true
ENV METRICS_PORT=9090

# Volume for persistent data
VOLUME ["/data"]

# Run application
CMD ["agent-memory"]
