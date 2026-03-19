#!/bin/bash

echo "🚀 Starting AI Infrastructure Services..."

# Start Dashboard API (port 5000)
echo "📊 Starting Dashboard API on port 5000..."
cd $TOPDIR/core/ai/eval
python3 api_server.py --port 5000 --host 0.0.0.0 --background &
sleep 2

# Start Memory Service (port 8081) 
echo "🧠 Starting Memory Service on port 8081..."
python3 api_server.py --port 8081 --host 0.0.0.0 --background &
sleep 2

# Start Comprehensive API (port 5001)
echo "📈 Starting Comprehensive API on port 5001..."
cd $TOPDIR/core/automation/scripts
python3 real-data-api.py --port 5001 --host 0.0.0.0 &
sleep 2

# Start Dashboard Flask app (port 5000 alternative)
echo "🖥️ Starting Dashboard Flask app..."
cd $TOPDIR/core/ai/eval/dashboard
python3 dashboard.py &
sleep 2

echo "✅ Services started!"
echo "📊 Dashboard API: http://localhost:5000"
echo "🧠 Memory Service: http://localhost:8081" 
echo "📈 Comprehensive API: http://localhost:5001"
echo "🖥️ Dashboard: http://localhost:5000/dashboard"

# Check service status
echo "🔍 Checking service status..."
sleep 3

for port in 5000 8081 5001; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ Service on port $port is running"
    else
        echo "❌ Service on port $port is not responding"
    fi
done
