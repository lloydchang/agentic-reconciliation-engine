FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY cmd/worker/main.go .
COPY internal/workflow/ ./internal/workflow/
COPY internal/activities/ ./internal/activities/
COPY go.mod go.sum ./

# Build the worker
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o worker ./cmd/worker/main.go

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/worker .

EXPOSE 8080

CMD ["./worker"]
