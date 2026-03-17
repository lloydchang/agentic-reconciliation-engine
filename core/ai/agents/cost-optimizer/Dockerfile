FROM rust:1.83-alpine AS builder

RUN apk add --no-cache \
    pkgconfig \
    openssl-dev \
    musl-dev \
    openssl-libs-static

WORKDIR /app

# Copy Cargo.toml
COPY Cargo.toml ./

# Copy source code
COPY src ./src/

# Build the application
RUN cargo update && cargo build --release

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy the binary from builder stage
COPY --from=builder /app/target/release/cost-optimizer .

# Expose port
EXPOSE 8080

# Health check endpoints
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the application
CMD ["./cost-optimizer"]
