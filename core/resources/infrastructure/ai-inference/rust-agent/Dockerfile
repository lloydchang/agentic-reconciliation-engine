# Build stage
FROM rust:1.75-slim AS builder

WORKDIR /usr/src/app

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./

# Copy source
COPY src ./src

# Build release
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies for llama.cpp
RUN apt-get update && apt-get install -y \
    libgomp1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -r -s /bin/false memoryagent

WORKDIR /app

# Copy binary from builder
COPY --from=builder /usr/src/app/target/release/memory_agent /app/memory_agent

# Create data directory
RUN mkdir -p /data && chown memoryagent:memoryagent /data

# Switch to non-root user
USER memoryagent

EXPOSE 8080

# Run the agent
CMD ["/app/memory_agent", "/data/memory.db", "/data/inbox"]
