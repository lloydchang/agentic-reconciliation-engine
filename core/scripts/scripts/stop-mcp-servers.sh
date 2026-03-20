#!/bin/bash
# MCP Server Stop Script
# This script stops all running MCP servers

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
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Stop MCP servers
print_info "Stopping MCP servers..."

for pid_file in "$REPO_ROOT"/.*.pid; do
    if [[ -f "$pid_file" ]]; then
        pid=$(cat "$pid_file")
        server_name=$(basename "$pid_file" .pid | sed 's/^\.//')
        
        if kill -0 "$pid" 2>/dev/null; then
            print_info "Stopping $server_name server (PID: $pid)..."
            kill "$pid"
            print_success "$server_name server stopped"
        else
            print_info "$server_name server was not running"
        fi
        
        rm -f "$pid_file"
    fi
done

print_success "All MCP servers stopped"
