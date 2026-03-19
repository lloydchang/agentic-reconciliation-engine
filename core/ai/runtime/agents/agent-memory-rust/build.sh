#!/bin/bash

# Build script for Agent Memory Service
set -e

echo "Building Agent Memory Service..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust/Cargo is not installed"
    exit 1
fi

# Build the Rust application
echo "Building Rust binary..."
cargo build --release

# Create Docker image
echo "Building Docker image..."
docker build -t agent-memory-rust:latest .

echo "Build completed successfully!"
echo ""
echo "To run the service:"
echo "  docker run -p 8080:8080 -p 9090:9090 -v \$(pwd)/data:/data agent-memory-rust:latest"
echo ""
echo "Or with custom configuration:"
echo "  docker run -p 8080:8080 -p 9090:9090 -v \$(pwd)/data:/data -v \$(pwd)/.env:/app/.env agent-memory-rust:latest"
