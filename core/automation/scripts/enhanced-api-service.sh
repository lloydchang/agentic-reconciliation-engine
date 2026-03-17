#!/bin/bash

# Enhanced Dashboard API Launcher
# Production-ready background service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.enhanced-api.pid"
LOG_FILE="$SCRIPT_DIR/enhanced-api.log"

start_api() {
    echo "🚀 Starting Enhanced Dashboard API..."
    
    # Check if already running
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
        echo "⚠️  Enhanced API is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    # Start in background with production settings
    cd "$SCRIPT_DIR"
    nohup python3 -c "
import os
import sys
sys.path.insert(0, '$SCRIPT_DIR')
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'false'
exec(open('$SCRIPT_DIR/enhanced-api-working.py').read())
" > "$LOG_FILE" 2>&1 &
    
    local PID=$!
    echo "$PID" > "$PID_FILE"
    
    echo "✅ Enhanced API started successfully!"
    echo "   PID: $PID"
    echo "   Port: 5002"
    echo "   Logs: $LOG_FILE"
    echo "   Dashboard: http://localhost:3001/"
}

stop_api() {
    echo "🛑 Stopping Enhanced Dashboard API..."
    
    if [ -f "$PID_FILE" ]; then
        local PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm -f "$PID_FILE"
            echo "✅ Enhanced API stopped (PID: $PID)"
        else
            echo "⚠️  API process not found, cleaning up PID file"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️  No PID file found, trying to find process..."
        pkill -f "enhanced-api-working.py"
    fi
}

status_api() {
    echo "📊 Enhanced Dashboard API Status:"
    
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null; then
        local PID=$(cat "$PID_FILE")
        echo "✅ Status: RUNNING"
        echo "   PID: $PID"
        echo "   Port: 5002"
        echo "   Dashboard: http://localhost:3001/"
        
        # Check if responding
        if curl -s http://localhost:5002/health >/dev/null 2>&1; then
            echo "   Health: ✅ Responding"
        else
            echo "   Health: ❌ Not responding"
        fi
    else
        echo "❌ Status: STOPPED"
        echo "   Port: 5002"
        echo "   Dashboard: http://localhost:3001/"
    fi
}

restart_api() {
    echo "🔄 Restarting Enhanced Dashboard API..."
    stop_api
    sleep 2
    start_api
}

case "$1" in
    start)
        start_api
        ;;
    stop)
        stop_api
        ;;
    restart)
        restart_api
        ;;
    status)
        status_api
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Enhanced API in background"
        echo "  stop    - Stop Enhanced API"
        echo "  restart - Restart Enhanced API"
        echo "  status  - Show API status"
        echo ""
        echo "Dashboard: http://localhost:3001/"
        echo "API: http://localhost:5002/health"
        exit 1
        ;;
esac
