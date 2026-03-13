#!/bin/bash

# MCP Client Demo Script
# This script demonstrates how to interact with the MCP server

set -e

# Configuration
MCP_SERVER_URL="http://localhost:8082"
API_KEY="${MCP_API_KEY:-dev-api-key-12345}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if MCP server is running
check_server() {
    log_info "Checking MCP server availability..."
    
    if curl -s "${MCP_SERVER_URL}/health" > /dev/null 2>&1; then
        log_success "MCP server is running"
        return 0
    else
        log_error "MCP server is not accessible at ${MCP_SERVER_URL}"
        return 1
    fi
}

# Initialize MCP connection
initialize_mcp() {
    log_info "Initializing MCP connection..."
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d '{
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "clientInfo": {
                    "name": "demo-client",
                    "version": "1.0.0"
                }
            }
        }')
    
    if echo "$response" | grep -q '"result"'; then
        log_success "MCP connection initialized"
        echo "$response" | jq '.result.serverInfo' 2>/dev/null || echo "$response"
    else
        log_error "Failed to initialize MCP connection"
        echo "$response"
        return 1
    fi
}

# List available tools
list_tools() {
    log_info "Listing available MCP tools..."
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d '{
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }')
    
    if echo "$response" | grep -q '"tools"'; then
        log_success "Tools retrieved successfully"
        echo "$response" | jq '.result.tools' 2>/dev/null || echo "$response"
    else
        log_error "Failed to retrieve tools"
        echo "$response"
        return 1
    fi
}

# List available resources
list_resources() {
    log_info "Listing available MCP resources..."
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d '{
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list"
        }')
    
    if echo "$response" | grep -q '"resources"'; then
        log_success "Resources retrieved successfully"
        echo "$response" | jq '.result.resources' 2>/dev/null || echo "$response"
    else
        log_error "Failed to retrieve resources"
        echo "$response"
        return 1
    fi
}

# Start compliance workflow
start_compliance_workflow() {
    local target_resource="${1:-vm-web-server-001}"
    local compliance_type="${2:-SOC2}"
    
    log_info "Starting compliance workflow for ${target_resource} (${compliance_type})..."
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d "{
            \"jsonrpc\": \"2.0\",
            \"id\": 4,
            \"method\": \"tools/call\",
            \"params\": {
                \"name\": \"start_compliance_workflow\",
                \"arguments\": {
                    \"targetResource\": \"${target_resource}\",
                    \"complianceType\": \"${compliance_type}\",
                    \"priority\": \"normal\"
                }
            }
        }")
    
    if echo "$response" | grep -q '"content"'; then
        log_success "Compliance workflow started"
        echo "$response" | jq '.result.content[0].text' 2>/dev/null | sed 's/"//g' || echo "$response"
        
        # Extract workflow ID for status check
        WORKFLOW_ID=$(echo "$response" | jq -r '.result.content[0].text' | grep -o 'workflowId[^,]*' | cut -d':' -f2 | tr -d ' ' | tr -d '"' 2>/dev/null || echo "")
        if [ -n "$WORKFLOW_ID" ]; then
            echo "Workflow ID: $WORKFLOW_ID"
        fi
    else
        log_error "Failed to start compliance workflow"
        echo "$response"
        return 1
    fi
}

# Get workflow status
get_workflow_status() {
    local workflow_id="$1"
    
    if [ -z "$workflow_id" ]; then
        log_warning "No workflow ID provided. Using a sample ID..."
        workflow_id="mcp-compliance-vm-web-server-001-$(date +%s)"
    fi
    
    log_info "Getting status for workflow: ${workflow_id}"
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d "{
            \"jsonrpc\": \"2.0\",
            \"id\": 5,
            \"method\": \"tools/call\",
            \"params\": {
                \"name\": \"get_workflow_status\",
                \"arguments\": {
                    \"workflowId\": \"${workflow_id}\",
                    \"includeDetails\": true
                }
            }
        }")
    
    if echo "$response" | grep -q '"content"'; then
        log_success "Workflow status retrieved"
        echo "$response" | jq '.result.content[0].text' 2>/dev/null | sed 's/"//g' || echo "$response"
    else
        log_error "Failed to get workflow status"
        echo "$response"
        return 1
    fi
}

# Read workflow results resource
read_workflow_results() {
    log_info "Reading workflow results resource..."
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d '{
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/read",
            "params": {
                "uri": "workflow://results"
            }
        }')
    
    if echo "$response" | grep -q '"contents"'; then
        log_success "Workflow results retrieved"
        echo "$response" | jq '.result.contents[0].text' 2>/dev/null | sed 's/"//g' || echo "$response"
    else
        log_error "Failed to read workflow results"
        echo "$response"
        return 1
    fi
}

# Read compliance reports resource
read_compliance_reports() {
    log_info "Reading compliance reports resource..."
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d '{
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/read",
            "params": {
                "uri": "compliance://reports"
            }
        }')
    
    if echo "$response" | grep -q '"contents"'; then
        log_success "Compliance reports retrieved"
        echo "$response" | jq '.result.contents[0].text' 2>/dev/null | sed 's/"//g' || echo "$response"
    else
        log_error "Failed to read compliance reports"
        echo "$response"
        return 1
    fi
}

# Get infrastructure info
get_infrastructure_info() {
    local resource_type="${1:-all}"
    local environment="${2:-all}"
    
    log_info "Getting infrastructure info (type: ${resource_type}, env: ${environment})..."
    
    response=$(curl -s -X POST "${MCP_SERVER_URL}/mcp" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${API_KEY}" \
        -d "{
            \"jsonrpc\": \"2.0\",
            \"id\": 8,
            \"method\": \"tools/call\",
            \"params\": {
                \"name\": \"get_infrastructure_info\",
                \"arguments\": {
                    \"resourceType\": \"${resource_type}\",
                    \"environment\": \"${environment}\"
                }
            }
        }")
    
    if echo "$response" | grep -q '"content"'; then
        log_success "Infrastructure info retrieved"
        echo "$response" | jq '.result.content[0].text' 2>/dev/null | sed 's/"//g' || echo "$response"
    else
        log_error "Failed to get infrastructure info"
        echo "$response"
        return 1
    fi
}

# Demo workflow
demo_workflow() {
    log_info "Starting complete MCP demo workflow..."
    
    # 1. Initialize connection
    initialize_mcp
    
    # 2. List tools and resources
    list_tools
    echo
    list_resources
    echo
    
    # 3. Start a compliance workflow
    echo "=== Starting Compliance Workflow ==="
    start_compliance_workflow "vm-web-server-001" "SOC2"
    echo
    
    # 4. Get infrastructure info
    echo "=== Getting Infrastructure Info ==="
    get_infrastructure_info "vm" "prod"
    echo
    
    # 5. Read workflow results
    echo "=== Reading Workflow Results ==="
    read_workflow_results
    echo
    
    # 6. Read compliance reports
    echo "=== Reading Compliance Reports ==="
    read_compliance_reports
    echo
    
    log_success "Demo workflow completed!"
}

# Show usage
show_usage() {
    echo "MCP Client Demo Script"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  check                    Check if MCP server is running"
    echo "  init                     Initialize MCP connection"
    echo "  tools                    List available tools"
    echo "  resources                List available resources"
    echo "  compliance [RESOURCE] [TYPE]  Start compliance workflow"
    echo "  status [WORKFLOW_ID]     Get workflow status"
    echo "  results                  Read workflow results"
    echo "  reports                  Read compliance reports"
    echo "  infra [TYPE] [ENV]       Get infrastructure info"
    echo "  demo                     Run complete demo workflow"
    echo "  help                     Show this help"
    echo
    echo "Environment Variables:"
    echo "  MCP_SERVER_URL          MCP server URL (default: http://localhost:8082)"
    echo "  MCP_API_KEY              API key for authentication"
    echo
    echo "Examples:"
    echo "  $0 check                # Check server status"
    echo "  $0 compliance vm-001 SOC2  # Start SOC2 compliance check"
    echo "  $0 status wf-123        # Get workflow status"
    echo "  $0 infra vm prod        # Get production VM info"
}

# Main script logic
main() {
    # Check for required tools
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    # Check for jq (optional, for pretty output)
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed. Output will not be pretty-formatted"
    fi
    
    # Parse command
    case "${1:-help}" in
        "check")
            check_server
            ;;
        "init")
            initialize_mcp
            ;;
        "tools")
            list_tools
            ;;
        "resources")
            list_resources
            ;;
        "compliance")
            start_compliance_workflow "$2" "$3"
            ;;
        "status")
            get_workflow_status "$2"
            ;;
        "results")
            read_workflow_results
            ;;
        "reports")
            read_compliance_reports
            ;;
        "infra")
            get_infrastructure_info "$2" "$3"
            ;;
        "demo")
            demo_workflow
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"
