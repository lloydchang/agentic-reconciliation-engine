# Rust Agent Memory Service
FROM rust:1.75-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    musl-dev \
    sqlite-dev \
    pkgconfig \
    openssl-dev

WORKDIR /app

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./

# Create dummy main.rs to build dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release && rm -rf src

# Copy source code
COPY src ./src

# Build the application
RUN touch src/main.rs && cargo build --release

# Runtime image
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    sqlite \
    curl \
    ca-certificates

# Create app user
RUN addgroup -g 1000 -S appgroup && \
    adduser -S appuser -u 1000 -G appgroup

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/agent-memory-rust /usr/local/bin/agent-memory-rust

# Create data directory
RUN mkdir -p /data && chown -R appuser:appgroup /data

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run the application
CMD ["agent-memory-rust"]
