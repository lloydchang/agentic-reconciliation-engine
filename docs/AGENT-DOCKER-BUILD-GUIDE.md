# Agent Docker Build Configuration Guide

## Overview

This guide documents the Docker build configurations for all independent AI agents, including build optimizations, multi-stage builds, and cross-platform compatibility considerations.

## Table of Contents

1. [Agent Build Configurations](#agent-build-configurations)
2. [Build Optimization Strategies](#build-optimization-strategies)
3. [Multi-Stage Build Patterns](#multi-stage-build-patterns)
4. [Cross-Platform Considerations](#cross-platform-considerations)
5. [Build Troubleshooting](#build-troubleshooting)
6. [Best Practices](#best-practices)

## Agent Build Configurations

### Cost Optimizer Agent (Rust)

#### Dockerfile Structure
```dockerfile
# Build stage
FROM rust:1.83-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    pkgconfig \
    openssl-dev \
    musl-dev \
    openssl-libs-static

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Build the application
RUN cargo build --release

# Runtime stage
FROM alpine:latest

# Install runtime dependencies
RUN apk --no-cache add ca-certificates

# Copy the binary from builder stage
COPY --from=builder /app/target/release/cost-optimizer /usr/local/bin/cost-optimizer

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["cost-optimizer"]
```

#### Key Features
- **Multi-stage build**: Reduces final image size by excluding build dependencies
- **Alpine Linux**: Minimal runtime footprint
- **Static linking**: OpenSSL libraries statically linked for reliability
- **Health check**: Built-in container health monitoring

#### Build Command
```bash
docker build -t cost-optimizer-agent:latest .
```

### Security Scanner Agent (Go)

#### Dockerfile Structure
```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

WORKDIR /app

# Download dependencies
COPY go.mod ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o security-scanner-agent .

# Runtime stage
FROM alpine:latest

# Install runtime dependencies
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Copy the binary from builder stage
COPY --from=builder /app/security-scanner-agent /usr/local/bin/security-scanner-agent

# Set permissions
RUN chown appuser:appgroup /usr/local/bin/security-scanner-agent

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["security-scanner-agent"]
```

#### Key Features
- **Multi-stage build**: Minimal runtime image
- **Non-root user**: Enhanced security posture
- **Static binary**: No runtime dependencies
- **Alpine Linux**: Small attack surface

#### Build Command
```bash
docker build -t security-scanner-agent:latest .
```

### Swarm Coordinator Agent (Go)

#### Dockerfile Structure
```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

WORKDIR /app

# Download dependencies
COPY go.mod ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o agent-swarm-coordinator .

# Runtime stage
FROM alpine:latest

# Install runtime dependencies
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Copy the binary from builder stage
COPY --from=builder /app/agent-swarm-coordinator /usr/local/bin/agent-swarm-coordinator

# Set permissions
RUN chown appuser:appgroup /usr/local/bin/agent-swarm-coordinator

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["agent-swarm-coordinator"]
```

#### Key Features
- **Multi-stage build**: Optimized for production
- **Security-focused**: Non-root execution
- **Lightweight**: Minimal runtime dependencies
- **Health monitoring**: Built-in health checks

#### Build Command
```bash
docker build -t agent-swarm-coordinator:latest .
```

## Build Optimization Strategies

### 1. Layer Caching Optimization

#### Rust Agent
```dockerfile
# Optimize layer caching for Rust dependencies
FROM rust:1.83-alpine AS builder

# Install build dependencies (cached layer)
RUN apk add --no-cache \
    pkgconfig \
    openssl-dev \
    musl-dev \
    openssl-libs-static

WORKDIR /app

# Copy dependency files first (cached if unchanged)
COPY Cargo.toml Cargo.lock ./

# Create dummy main.rs to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release && rm -rf src

# Copy actual source code
COPY src ./src

# Build application (uses cached dependencies)
RUN cargo build --release
```

#### Go Agent
```dockerfile
# Optimize layer caching for Go modules
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go.mod first (cached if unchanged)
COPY go.mod ./
RUN go mod download

# Copy source code
COPY . .

# Build application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o app .
```

### 2. Image Size Optimization

#### Multi-Stage Benefits
- **Build stage**: Includes all build tools and dependencies
- **Runtime stage**: Only contains necessary runtime components
- **Size reduction**: Typically 70-90% smaller than single-stage builds

#### Example Size Comparison
```bash
# Single-stage build size
docker images | grep agent
# agent-single-stage    850MB

# Multi-stage build size  
docker images | grep agent
# agent-multi-stage     125MB
```

### 3. Security Hardening

#### Non-Root User Pattern
```dockerfile
# Create non-root user with specific UID/GID
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Set proper ownership
COPY --from=builder /app/binary /usr/local/bin/binary
RUN chown appuser:appgroup /usr/local/bin/binary

# Switch to non-root user
USER appuser
```

#### Minimal Attack Surface
```dockerfile
# Use minimal base image
FROM alpine:latest

# Only install necessary runtime dependencies
RUN apk --no-cache add ca-certificates

# Remove package cache to reduce image size
RUN rm -rf /var/cache/apk/*
```

## Multi-Stage Build Patterns

### Pattern 1: Standard Multi-Stage
```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o app .

# Runtime stage
FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/app /usr/local/bin/app
CMD ["app"]
```

### Pattern 2: Dependency Caching
```dockerfile
# Dependency stage
FROM golang:1.21-alpine AS deps
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY --from=deps /app/go.mod /app/go.sum
COPY --from=deps /app/go.sum /app/go.sum
COPY . .
RUN go build -o app .

# Runtime stage
FROM alpine:latest
COPY --from=builder /app/app /usr/local/bin/app
CMD ["app"]
```

### Pattern 3: Development vs Production
```dockerfile
# Development stage
FROM golang:1.21-alpine AS development
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o app .
CMD ["go", "run", "main.go"]

# Production stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o app .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/app /usr/local/bin/app
CMD ["app"]
```

## Cross-Platform Considerations

### 1. Base Image Selection

#### Alpine Linux
```dockerfile
# Benefits:
# - Small size (~5MB base)
# - Security-focused
# - Good for production

# Considerations:
# - Uses musl libc (may need compatibility fixes)
# - Some packages unavailable
FROM alpine:latest
```

#### Distroless Images
```dockerfile
# Benefits:
# - Minimal attack surface
# - No package manager
# - Only application and runtime dependencies

# Considerations:
# - No shell for debugging
# - More complex build process
FROM gcr.io/distroless/static:latest
```

### 2. Architecture Support

#### Multi-Architecture Builds
```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t agent:latest .

# Push to registry with multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t registry/agent:latest --push .
```

#### Architecture-Specific Optimizations
```dockerfile
# Rust agent with architecture-specific optimizations
FROM rust:1.83-alpine AS builder

ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        apk add --no-cache gcc-aarch64-none-elf; \
    else \
        apk add --no-cache gcc; \
    fi

RUN cargo build --target=$TARGETARCH-unknown-linux-musl --release
```

### 3. Dependency Management

#### Go Modules
```go
// go.mod
module github.com/organization/agent

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/sirupsen/logrus v1.9.3
)
```

#### Rust Dependencies
```toml
# Cargo.toml
[package]
name = "cost-optimizer"
version = "1.0.0"
edition = "2021"

[dependencies]
tokio = { version = "1.0", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
warp = "0.3"
```

## Build Troubleshooting

### Common Issues and Solutions

#### 1. Rust Build Failures
```bash
# Issue: OpenSSL linking errors
# Solution: Add static linking libraries
RUN apk add --no-cache openssl-libs-static

# Issue: Missing musl-dev
# Solution: Install development tools
RUN apk add --no-cache musl-dev

# Issue: Cargo lock file conflicts
# Solution: Update dependencies or use --locked flag
RUN cargo build --release --locked
```

#### 2. Go Build Failures
```bash
# Issue: Module download failures
# Solution: Use GOPROXY environment variable
ENV GOPROXY=https://proxy.golang.org,direct

# Issue: CGO errors in alpine
# Solution: Disable CGO for static binaries
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo

# Issue: Missing go.sum
# Solution: Generate go.sum before build
COPY go.mod go.sum ./
RUN go mod download
```

#### 3. Docker Build Issues
```bash
# Issue: Layer cache not working
# Solution: Order COPY commands by change frequency
COPY go.mod go.sum ./          # Changes rarely
COPY . .                       # Changes frequently

# Issue: Build context too large
# Solution: Use .dockerignore
echo "target/" >> .dockerignore
echo ".git/" >> .dockerignore
echo "*.log" >> .dockerignore

# Issue: Permission denied
# Solution: Set proper file permissions
RUN chown -R appuser:appgroup /app
USER appuser
```

### Debug Build Issues

#### Build with Debug Information
```dockerfile
# Debug build for troubleshooting
FROM rust:1.83-alpine AS debug-builder
RUN cargo build

# Production build
FROM rust:1.83-alpine AS builder
RUN cargo build --release
```

#### Verbose Build Output
```bash
# Verbose Docker build
docker build --progress=plain -t agent:latest .

# Verbose Go build
RUN go build -v -x -o app .

# Verbose Rust build
RUST_LOG=debug cargo build --verbose
```

## Best Practices

### 1. Build Performance

#### Parallel Builds
```dockerfile
# Use build cache effectively
COPY --from=deps /app/go.mod /app/go.sum
COPY --from=deps /app/go.sum /app/go.sum

# Parallel compilation
RUN cargo build -j $(nproc) --release
```

#### Build Arguments
```dockerfile
# Use build arguments for flexibility
ARG VERSION=1.0.0
ARG BUILD_DATE

ENV APP_VERSION=$VERSION
ENV BUILD_DATE=$BUILD_DATE
```

### 2. Security

#### Vulnerability Scanning
```bash
# Scan images for vulnerabilities
docker scan agent:latest

# Use Trivy for comprehensive scanning
trivy image agent:latest
```

#### Minimal Privileges
```dockerfile
# Drop all capabilities
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

USER appuser

# Read-only filesystem
VOLUME ["/tmp"]
```

### 3. Monitoring and Observability

#### Build Metrics
```bash
# Track build time
time docker build -t agent:latest .

# Track image size
docker images | grep agent | awk '{print $1, $7}'
```

#### Health Checks
```dockerfile
# Comprehensive health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

### 4. CI/CD Integration

#### Automated Builds
```yaml
# GitHub Actions example
- name: Build Docker images
  run: |
    docker build -t agent:${{ github.sha }} .
    docker build -t agent:latest .
```

#### Multi-Environment Support
```dockerfile
# Environment-specific builds
ARG ENV=production
RUN if [ "$ENV" = "development" ]; then \
        echo "Development build"; \
    else \
        echo "Production build"; \
    fi
```

## Conclusion

This guide provides comprehensive documentation for building Docker images for independent AI agents with focus on:

1. **Optimized multi-stage builds** for minimal image sizes
2. **Security hardening** with non-root users and minimal attack surfaces
3. **Cross-platform compatibility** for different architectures
4. **Build performance optimization** through effective caching strategies
5. **Troubleshooting guidance** for common build issues

By following these patterns and best practices, you can create reliable, secure, and efficient Docker images for your AI agent deployments.

## References

- [Docker Multi-Stage Build Documentation](https://docs.docker.com/build/building/multi-stage/)
- [Rust Docker Best Practices](https://doc.rust-lang.org/cargo/guide/building-docker.html)
- [Go Docker Best Practices](https://github.com/golang/go/wiki/Docker)
- [Alpine Linux Package Repository](https://pkgs.alpinelinux.org/packages)
