#!/bin/bash

# Portal Launcher
# Starts the portal on port 9000 (common for admin consoles and enterprise tools)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=9000

echo "🚀 Starting Portal..."
echo "📍 Portal will be available at: http://localhost:${PORT}"
echo

# Check if port is already in use
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port ${PORT} is already in use!"
    echo "💡 You can:"
    echo "   1. Stop the service using port ${PORT}:"
    echo "      lsof -ti:${PORT} | xargs kill -9"
    echo "   2. Or run the portal on a different port:"
    echo "      python3 ${SCRIPT_DIR}/server.py"
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the portal
cd "$SCRIPT_DIR"
python3 server.py
