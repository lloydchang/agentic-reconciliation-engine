#!/bin/bash
# MCP Server Startup Script
# This script starts all MCP servers for Claude Desktop integration

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_SERVERS_DIR="$REPO_ROOT/.claude/mcp-servers"

# Check if .env file exists
if [[ ! -f "$REPO_ROOT/.env" ]]; then
    print_error ".env file not found. Please copy .env.template to .env and configure your credentials."
    exit 1
fi

# Source environment variables
set -a
source "$REPO_ROOT/.env"
set +a

# Start MCP servers
print_info "Starting MCP servers..."

for server_dir in "$MCP_SERVERS_DIR"/*; do
    if [[ -d "$server_dir" && -f "$server_dir/index.js" ]]; then
        server_name=$(basename "$server_dir")
        print_info "Starting $server_name server..."
        
        cd "$server_dir"
        if node index.js > "$REPO_ROOT/logs/${server_name}.log" 2>&1 &
        then
            echo $! > "$REPO_ROOT/.${server_name}.pid"
            print_success "$server_name server started (PID: $!)"
        else
            print_error "Failed to start $server_name server"
        fi
    fi
done

print_info "All MCP servers started. Check logs in $REPO_ROOT/logs/"
print_info "To stop servers, run: $REPO_ROOT/scripts/stop-mcp-servers.sh"
