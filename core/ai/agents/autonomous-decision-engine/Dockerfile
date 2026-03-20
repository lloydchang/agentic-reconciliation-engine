# Build autonomous decision engine with learning capabilities
FROM golang:1.24-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Copy go mod files
COPY go.mod ./
RUN go mod download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the autonomous decision engine
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o autonomous-decision-engine .

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
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["/autonomous-decision-engine", "health"]

# Run the autonomous decision engine
CMD ["./autonomous-decision-engine"]
