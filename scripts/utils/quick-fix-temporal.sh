#!/bin/bash

# Quick Temporal Fix using Docker Compose
echo "🔧 Fixing Temporal 500 error with Docker Compose..."

# Navigate to the temporal directory
cd /Users/lloyd/github/antigravity/agentic-reconciliation-engine/core/ai/runtime/standalone/backend

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || echo "No existing containers to stop"

# Kill any processes on ports 7233 and 8080
echo "Freeing up ports..."
lsof -ti:7233 | xargs kill -9 2>/dev/null || echo "Port 7233 is free"
lsof -ti:8080 | xargs kill -9 2>/dev/null || echo "Port 8080 is free"

# Wait for ports to be released
sleep 2

# Start Temporal services
echo "🚀 Starting Temporal services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Test the services
echo "🧪 Testing services..."
echo "Testing Temporal API..."
if curl -s http://localhost:7233/health > /dev/null; then
    echo "✅ Temporal API is working at http://localhost:7233"
else
    echo "❌ Temporal API is not responding"
fi

echo "Testing Temporal UI..."
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Temporal UI is working at http://localhost:8080"
else
    echo "❌ Temporal UI is not responding"
fi

echo ""
echo "🎉 Temporal should now be working!"
echo "📊 UI: http://localhost:8080"
echo "🔌 API: http://localhost:7233"
echo ""
echo "If you still see errors, check logs with:"
echo "docker-compose logs temporal"
echo "docker-compose logs temporal-ui"
echo ""
echo "To stop: docker-compose down"
