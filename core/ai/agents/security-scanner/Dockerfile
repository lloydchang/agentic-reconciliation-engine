# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o security-scanner-agent .

# Runtime stage
FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/security-scanner-agent /usr/local/bin/security-scanner-agent
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1
CMD ["security-scanner-agent"]
