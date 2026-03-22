# Build autonomous decision engine with learning capabilities
FROM golang:1.24.2 AS builder

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git ca-certificates tzdata

# Copy go mod files
COPY go.mod ./
COPY go.sum ./
COPY . .
RUN go mod vendor && echo "Dependencies resolved" && CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o autonomous-decision-engine .

# Final stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y ca-certificates tzdata && rm -rf /var/lib/apt/lists/*

# Create non-root user BEFORE copying files so we can chown properly
RUN addgroup --gid 1001 autonomous && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" autonomous

WORKDIR /app

# Copy the binary from builder stage and ensure the non-root user can read it
# The Temporal SDK's getBinaryChecksum() reads the running binary — it must be readable by the process user
COPY --from=builder --chown=autonomous:autonomous /app/autonomous-decision-engine .

USER autonomous

# Expose port for health checks
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the application
CMD ["/app/autonomous-decision-engine"]
