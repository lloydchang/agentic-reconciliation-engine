# Build autonomous decision engine with learning capabilities
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Copy go mod files
COPY go.mod ./
COPY go.sum ./
COPY . .
RUN go mod vendor && echo "Dependencies resolved" && CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o autonomous-decision-engine .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /root/

# Copy the binary from builder stage
COPY --from=builder /app/autonomous-decision-engine .

# Create non-root user
RUN addgroup -g 1001 -S autonomous && \
    adduser -u 1001 -S autonomous -G autonomous

USER autonomous

# Expose port for health checks
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the application
CMD ["./autonomous-decision-engine"]
