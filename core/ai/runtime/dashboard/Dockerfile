# Backend Dockerfile (Multi-Arch Optimized)
FROM golang:1.24-alpine AS backend-builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the backend
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main ./cmd/server

# Frontend Dockerfile
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
RUN npm install --only=production

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Final image
FROM alpine:latest

RUN apk --no-cache add ca-certificates

# Copy backend binary
COPY --from=backend-builder /app/main /app/main

# Copy frontend build
COPY --from=frontend-builder /app/frontend/build /app/static

WORKDIR /app

EXPOSE 8081

CMD ["./main"]
