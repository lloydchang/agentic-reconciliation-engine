# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go module files
COPY go.mod go.sum ./

# Download dependencies (we'll create go.mod in next step, but for now assume)
RUN go mod download

# Copy source code
COPY main.go ./

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -installsuffix cgo -o memory-selector main.go

# Runtime stage
FROM alpine:latest

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN adduser -D -s /bin/sh selector

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/memory-selector .

# Switch to non-root user
USER selector

EXPOSE 8080

# Run the selector service
CMD ["./memory-selector"]
