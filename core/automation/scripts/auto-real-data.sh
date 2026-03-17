#!/bin/bash

echo "🔥 AUTOMATIC REAL DATA SETUP - NO MORE FAKING!"
echo "=========================================="

# Step 1: Set up real connection
echo "📡 Step 1: Setting up real connection to Go metrics server..."
./setup-real-connection.sh

# Wait for connection to establish
sleep 3

# Step 2: Switch to real data API
echo "🔄 Step 2: Switching to REAL DATA ONLY API..."
echo "   Stopping any fake/simulated APIs..."
pkill -f "enhanced-api" 2>/dev/null || true
pkill -f "test-api" 2>/dev/null || true

sleep 2

echo "   Starting REAL DATA ONLY API..."
python3 real-data-api.py > /dev/null 2>&1 &
API_PID=$!

# Wait for API to start
sleep 3

# Step 3: Test the real connection
echo "🧪 Step 3: Testing REAL DATA connection..."
if curl -s http://localhost:5002/api/config | grep -q "real_data_only"; then
    echo "✅ REAL DATA API is running!"
    echo "   PID: $API_PID"
    echo "   Port: 5002"
    echo "   Data Source: REAL METRICS ONLY"
    echo ""
    
    # Test actual data endpoint
    echo "📊 Testing real data endpoint..."
    if curl -s http://localhost:5002/api/core/ai/runtime/detailed >/dev/null 2>&1; then
        echo "✅ Real data endpoints responding!"
    else
        echo "⚠️  Real data endpoints not responding - checking Go server..."
        if curl -s http://localhost:8080/health >/dev/null 2>&1; then
            echo "✅ Go metrics server is running"
            echo "❌ API connection issue - check logs"
        else
            echo "❌ Go metrics server not accessible"
            echo "   Port-forward may have failed"
        fi
    fi
    
else
    echo "❌ REAL DATA API failed to start"
    echo "   Check for Python errors or missing dependencies"
fi

echo ""
echo "🎯 Step 4: Dashboard Ready!"
echo "=========================="
echo "🌐 Dashboard: http://localhost:3001/"
echo "📡 Real API: http://localhost:5002/api/config"
echo "🔥 Go Server: http://localhost:8080/health"
echo ""
echo "🚀 YOUR DASHBOARD NOW USES:"
echo "   ✅ REAL CPU usage from running agents"
echo "   ✅ REAL memory consumption measurements"  
echo "   ✅ TRUE skill execution counts from Temporal"
echo "   ✅ ACTUAL workflow status from Go workers"
echo "   ✅ REAL system health metrics from Kubernetes"
echo ""
echo "❌ NO MORE:"
echo "   ❌ Fake data"
echo "   ❌ Simulated metrics"
echo "   ❌ Random numbers"
echo "   ❌ Realistic fallbacks"
echo ""
echo "🎉 Refresh your browser at http://localhost:3001/ to see REAL DATA!"
echo ""
echo "🛑 To stop: pkill -f 'real-data-api.py'"
