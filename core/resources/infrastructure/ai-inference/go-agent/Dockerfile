# Build stage
FROM golang:1.25-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY agent.go ./

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o memory-agent agent.go

# Runtime stage
FROM alpine:latest

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN adduser -D -s /bin/sh memoryagent

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/memory-agent .

# Create data directory
RUN mkdir -p /data && chown memoryagent:memoryagent /data

# Switch to non-root user
USER memoryagent

EXPOSE 8080

# Run the agent
CMD ["./memory-agent"]
