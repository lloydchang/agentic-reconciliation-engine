#!/bin/bash

# Portal - Services Stopper
# Stops all real services

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Portal - Services Stopper${NC}"
echo

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="/tmp/${service_name// /_}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping $service_name (PID: $pid)...${NC}"
            kill "$pid"
            rm "$pid_file"
            echo -e "${GREEN}✅ $service_name stopped${NC}"
        else
            echo -e "${RED}⚠️  $service_name PID $pid not running, removing PID file${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
    fi
}

# Stop all services
stop_service "Real Data API"
stop_service "Real Dashboard"
stop_service "Comprehensive API"
stop_service "Memory Service"

# Also kill any remaining node processes on our ports
echo
echo -e "${BLUE}🧹 Cleaning up any remaining processes...${NC}"

for port in 5000 5001 8081 8082; do
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Killing process on port $port (PID: $pid)${NC}"
        kill -9 "$pid" 2>/dev/null || true
    fi
done

echo
echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
