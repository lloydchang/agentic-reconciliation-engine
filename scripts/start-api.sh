#!/bin/bash

echo "🚀 Starting Enhanced Dashboard API..."

# Kill any existing processes
pkill -f "enhanced-api" 2>/dev/null || true
pkill -f "python.*5002" 2>/dev/null || true

# Wait a moment
sleep 2

# Start the API in background
cd /Users/lloyd/github/antigravity/gitops-infra-control-plane
python3 enhanced-api-working.py > /dev/null 2>&1 &

# Wait for startup
sleep 3

# Check if it's running
if curl -s http://localhost:5002/health >/dev/null 2>&1; then
    echo "✅ Enhanced API is running!"
    echo "   Port: 5002"
    echo "   Dashboard: http://localhost:3001/"
    echo ""
    echo "🎯 Refresh your browser to see realistic agent data!"
else
    echo "❌ API failed to start. Check for errors:"
    ps aux | grep "enhanced-api"
fi
