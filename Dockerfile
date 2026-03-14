FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /cloud-ai-worker ./ai-agents/cmd/worker/main.go
FROM gcr.io/distroless/static-debian12:latest
COPY --from=builder /cloud-ai-worker .
ENTRYPOINT ["./cloud-ai-worker"]
