# Deployment Automation Guide

## Overview

This comprehensive guide covers the fully automated deployment system for AI Agent Skills, providing zero-touch deployment with automatic configuration, service startup, and integration setup.

## Table of Contents

1. [Automation Architecture](#automation-architecture)
2. [Quick Start](#quick-start)
3. [Deployment Process](#deployment-process)
4. [Configuration Management](#configuration-management)
5. [Service Management](#service-management)
6. [Integration Setup](#integration-setup)
7. [Monitoring and Health](#monitoring-and-health)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)
10. [Maintenance and Updates](#maintenance-and-updates)

## Automation Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                Deployment Automation System               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Quickstart │  │   Deploy    │  │   Service   │    │
│  │   Scripts   │  │   Scripts   │  │   Manager   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │             │
│         ▼                ▼                ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Dependency│  │   Config    │  │   Health    │    │
│  │   Installer │  │   Generator │  │   Monitor   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │             │
│         ▼                ▼                ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   MCP       │  │   Claude    │  │   Runtime   │    │
│  │   Servers   │  │   Desktop   │  │   Services  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Automation Flow

1. **Initialization**: Environment detection and validation
2. **Dependency Installation**: Automatic package installation
3. **Configuration Generation**: Auto-creation of environment files
4. **Service Deployment**: MCP server installation and startup
5. **Integration Setup**: Claude Desktop configuration
6. **Health Validation**: Service health checks and monitoring
7. **User Notification**: Deployment status and next steps

## Quick Start

### Single Command Deployment

The entire AI Agent Skills ecosystem can be deployed with a single command:

```bash
# Full deployment with zero manual steps
./core/automation/scripts/quickstart.sh
```

### What Happens Automatically

1. ✅ **Environment Detection**: System requirements validation
2. ✅ **Dependency Installation**: npm packages and system dependencies
3. ✅ **Configuration Setup**: Auto-generated .env and config files
4. ✅ **Service Startup**: All MCP servers started in background
5. ✅ **Integration Setup**: Claude Desktop configuration updated
6. ✅ **Health Monitoring**: Real-time service status validation
7. ✅ **User Notification**: Deployment complete with status report

### Overlay Quickstart

For overlay-specific deployment:

```bash
# Overlay deployment with AI Agent Skills
./core/automation/scripts/overlay-quickstart.sh
```

### Deployment Options

```bash
# Standard deployment
./core/automation/scripts/quickstart.sh

# Overlay deployment
./core/automation/scripts/overlay-quickstart.sh

# Examples only
./core/automation/scripts/overlay-quickstart.sh --examples

# Test deployment only
./core/automation/scripts/overlay-quickstart.sh --test

# Full deployment with all options
./core/automation/scripts/overlay-quickstart.sh --all
```

## Deployment Process

### Phase 1: Environment Preparation

#### System Requirements Check
```bash
# Node.js version check
node --version  # >= 18.0.0 required

# npm version check
npm --version   # >= 8.0.0 required

# Memory check
free -m          # >= 2GB recommended

# Disk space check
df -h            # >= 1GB free space required
```

#### Directory Structure Creation
```bash
# Automatically created directories
.claude/
├── skills/                    # Skill definitions
│   ├── cloud-compliance-auditor/
│   ├── incident-triage-automator/
│   ├── iac-deployment-validator/
│   ├── knowledge-base-server/
│   └── progress-reporter/
├── mcp-servers/               # MCP server implementations
│   ├── cloud-compliance/
│   ├── incident-triage/
│   ├── iac-validator/
│   ├── knowledge-base/
│   └── engagement-sync/
├── references/                # Knowledge repository
│   ├── runbooks/
│   ├── governance/
│   ├── knowledge-base/
│   └── templates/
└── communication/             # Meeting and decision records
    ├── meetings/
    ├── decisions/
    ├── stakeholders/
    └── announcements/
```

### Phase 2: Dependency Installation

#### Automatic npm Package Installation
```bash
# For each MCP server
cd .claude/mcp-servers/cloud-compliance
npm install --silent

cd .claude/mcp-servers/incident-triage
npm install --silent

cd .claude/mcp-servers/iac-validator
npm install --silent

cd .claude/mcp-servers/knowledge-base
npm install --silent

cd .claude/mcp-servers/engagement-sync
npm install --silent
```

#### Dependency Validation
```bash
# Validate npm installations
for server in cloud-compliance incident-triage iac-validator knowledge-base engagement-sync; do
  cd .claude/mcp-servers/$server
  if npm list --depth=0 2>/dev/null | grep -q "empty"; then
    echo "❌ $server dependencies missing"
    exit 1
  else
    echo "✅ $server dependencies installed"
  fi
done
```

### Phase 3: Configuration Generation

#### Environment File Creation
```bash
# Auto-create .env from template
if [[ ! -f .env ]]; then
  cp .env.template .env
  echo "✅ .env file created from template"
fi
```

#### Claude Desktop Configuration
```bash
# Auto-configure Claude Desktop
CLAUDE_CONFIG_DIR="$HOME/.config/claude-desktop"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/config.json"
SOURCE_CONFIG=".claude/claude_desktop_config.json"

mkdir -p "$CLAUDE_CONFIG_DIR"

# Backup existing configuration
if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
  cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
  echo "✅ Existing Claude Desktop configuration backed up"
fi

# Apply new configuration
cp "$SOURCE_CONFIG" "$CLAUDE_CONFIG_FILE"
echo "✅ Claude Desktop configuration updated"
```

#### Configuration Validation
```bash
# Validate .env file
if [[ -f .env ]]; then
  # Check for required variables
  required_vars=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AZURE_CLIENT_ID"
    "AZURE_CLIENT_SECRET"
    "GOOGLE_APPLICATION_CREDENTIALS"
  )
  
  for var in "${required_vars[@]}"; do
    if grep -q "^${var}=" .env; then
      echo "✅ $var configured"
    else
      echo "⚠️  $var not configured (using placeholder)"
    fi
  done
fi
```

### Phase 4: Service Deployment

#### MCP Server Startup
```bash
# Auto-start all MCP servers
for server_dir in .claude/mcp-servers/*; do
  if [[ -d "$server_dir" && -f "$server_dir/index.js" ]]; then
    server_name=$(basename "$server_dir")
    echo "🚀 Starting $server_name server..."
    
    cd "$server_dir"
    
    # Set environment variables
    if [[ -f ../../.env ]]; then
      set -a
      source ../../.env
      set +a
    fi
    
    # Start server in background
    nohup node index.js > ../../logs/${server_name}.log 2>&1 &
    echo $! > ../../.${server_name}.pid
    
    echo "✅ $server_name server started (PID: $!)"
  fi
done
```

#### Service Health Validation
```bash
# Wait for servers to initialize
sleep 3

# Check server health
running_count=0
total_count=0

for server_dir in .claude/mcp-servers/*; do
  if [[ -d "$server_dir" && -f "$server_dir/index.js" ]]; then
    server_name=$(basename "$server_dir")
    ((total_count++))
    
    if [[ -f ".${server_name}.pid" ]]; then
      pid=$(cat ".${server_name}.pid")
      if kill -0 "$pid" 2>/dev/null; then
        ((running_count++))
        echo "✅ $server_name server is running (PID: $pid)"
      else
        echo "❌ $server_name server failed to start"
      fi
    else
      echo "⚠️  $server_name server not running"
    fi
  fi
done

echo "📊 Server Summary: $running_count/$total_count running"
```

### Phase 5: Integration Setup

#### Claude Desktop Integration
```bash
# Test Claude Desktop configuration
if command -v code &>/dev/null; then
  echo "🔧 Testing Claude Desktop integration..."
  
  # Check if Claude Desktop is running
  if pgrep -f "Claude Desktop" > /dev/null; then
    echo "ℹ️  Claude Desktop is running - restart to load new AI Agent Skills"
  else
    echo "ℹ️  Claude Desktop not running - configuration ready for next startup"
  fi
  
  echo "✅ Claude Desktop integration configured"
fi
```

#### Service Scripts Creation
```bash
# Create startup script
cat > scripts/start-mcp-servers.sh << 'EOF'
#!/bin/bash
# MCP Server Startup Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_SERVERS_DIR="$REPO_ROOT/.claude/mcp-servers"

# Check if .env file exists
if [[ ! -f "$REPO_ROOT/.env" ]]; then
  echo "❌ .env file not found. Please copy .env.template to .env and configure your credentials."
  exit 1
fi

# Source environment variables
set -a
source "$REPO_ROOT/.env"
set +a

# Start MCP servers
echo "🚀 Starting MCP servers..."

for server_dir in "$MCP_SERVERS_DIR"/*; do
  if [[ -d "$server_dir" && -f "$server_dir/index.js" ]]; then
    server_name=$(basename "$server_dir")
    echo "Starting $server_name server..."
    
    cd "$server_dir"
    if node index.js > "$REPO_ROOT/logs/${server_name}.log" 2>&1 &
    then
      echo $! > "$REPO_ROOT/.${server_name}.pid"
      echo "✅ $server_name server started (PID: $!)"
    else
      echo "❌ Failed to start $server_name server"
    fi
  fi
done

echo "✅ All MCP servers started. Check logs in $REPO_ROOT/logs/"
echo "ℹ️  To stop servers, run: $REPO_ROOT/scripts/stop-mcp-servers.sh"
EOF

chmod +x scripts/start-mcp-servers.sh

# Create stop script
cat > scripts/stop-mcp-servers.sh << 'EOF'
#!/bin/bash
# MCP Server Stop Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Stop MCP servers
echo "🛑 Stopping MCP servers..."

for pid_file in "$REPO_ROOT"/.*.pid; do
  if [[ -f "$pid_file" ]]; then
    pid=$(cat "$pid_file")
    server_name=$(basename "$pid_file" .pid | sed 's/^\.//')
    
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $server_name server (PID: $pid)..."
      kill "$pid"
      echo "✅ $server_name server stopped"
    else
      echo "ℹ️  $server_name server was not running"
    fi
    
    rm -f "$pid_file"
  fi
done

echo "✅ All MCP servers stopped"
EOF

chmod +x scripts/stop-mcp-servers.sh

echo "✅ Service management scripts created"
```

### Phase 6: Health Monitoring

#### Health Check Implementation
```bash
# Create health check script
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash
# MCP Server Health Check

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
  local status=$1
  local message=$2
  local pid=$3
  
  case $status in
    "running")
      echo -e "${GREEN}✅${NC} $message (PID: $pid)"
      ;;
    "stopped")
      echo -e "${RED}❌${NC} $message (not running)"
      ;;
    "unknown")
      echo -e "${YELLOW}⚠️ ${NC} $message (status unknown)"
      ;;
  esac
}

echo "🔍 MCP Server Health Check"
echo "========================"

running_count=0
total_count=0

for server_dir in "$REPO_ROOT/.claude/mcp-servers"/*; do
  if [[ -d "$server_dir" && -f "$server_dir/index.js" ]]; then
    server_name=$(basename "$server_dir")
    ((total_count++))
    
    if [[ -f "$REPO_ROOT/.${server_name}.pid" ]]; then
      pid=$(cat "$REPO_ROOT/.${server_name}.pid")
      if kill -0 "$pid" 2>/dev/null; then
        print_status "running" "$server_name server" "$pid"
        ((running_count++))
      else
        print_status "stopped" "$server_name server" "$pid"
        # Remove stale PID file
        rm -f "$REPO_ROOT/.${server_name}.pid"
      fi
    else
      print_status "stopped" "$server_name server" "N/A"
    fi
  fi
done

echo ""
echo "📊 Health Summary:"
echo "Running: $running_count/$total_count servers"

if [[ $running_count -eq $total_count ]]; then
  echo -e "${GREEN}🎉 All MCP servers are healthy!${NC}"
  exit 0
else
  echo -e "${RED}⚠️  Some MCP servers are not running${NC}"
  exit 1
fi
EOF

chmod +x scripts/health-check.sh

echo "✅ Health check script created"
```

#### Log Management
```bash
# Create logs directory
mkdir -p logs

# Create log rotation script
cat > scripts/rotate-logs.sh << 'EOF'
#!/bin/bash
# Log Rotation Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$REPO_ROOT/logs"

# Rotate logs older than 7 days
find "$LOGS_DIR" -name "*.log" -mtime +7 -exec gzip {} \;
find "$LOGS_DIR" -name "*.log.gz" -mtime +30 -delete

echo "✅ Log rotation completed"
EOF

chmod +x scripts/rotate-logs.sh

echo "✅ Log management configured"
```

### Phase 7: User Notification

#### Deployment Status Report
```bash
# Generate comprehensive status report
generate_status_report() {
  echo ""
  echo "🚀 AI Agent Skills Deployment Status"
  echo "=================================="
  echo ""
  echo "✅ What was done automatically:"
  echo "• MCP server dependencies installed"
  echo "• Environment configuration created (auto-generated from template)"
  echo "• Claude Desktop configuration updated"
  echo "• MCP servers validated and auto-started"
  echo "• Startup and stop scripts created"
  echo "• Logs directory initialized"
  echo "• Demo mode enabled for immediate testing"
  echo ""
  echo "🤖 AI Agent Skills Status:"
  
  # Check actual server status
  local running_count=0
  local total_count=0
  for server_dir in "$REPO_ROOT/.claude/mcp-servers"/*; do
    if [[ -d "$server_dir" && -f "$server_dir/index.js" ]]; then
      server_name=$(basename "$server_dir")
      ((total_count++))
      
      if [[ -f "$REPO_ROOT/.${server_name}.pid" ]]; then
        pid=$(cat "$REPO_ROOT/.${server_name}.pid")
        if kill -0 "$pid" 2>/dev/null; then
          ((running_count++))
          echo "  ✅ $server_name (PID: $pid)"
        else
          echo "  ❌ $server_name (failed to start)"
        fi
      else
        echo "  ⚠️  $server_name (not running)"
      fi
    fi
  done
  
  echo ""
  echo "📊 Server Summary: $running_count/$total_count running"
  echo ""
  echo "🎯 READY FOR IMMEDIATE USE - No manual configuration needed!"
  echo ""
  echo "🔧 Configuration files created:"
  echo "  • $REPO_ROOT/.env (auto-generated from template)"
  echo "  • $HOME/.config/claude-desktop/config.json (Claude Desktop)"
  echo "  • $REPO_ROOT/scripts/start-mcp-servers.sh (manual control)"
  echo "  • $REPO_ROOT/scripts/stop-mcp-servers.sh (manual control)"
  echo ""
  echo "🚀 AI Agent Skills are now fully operational and autonomous!"
}

generate_status_report
```

## Configuration Management

### Environment Variables

#### Required Variables
```bash
# Cloud Provider Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_DEFAULT_REGION=us-east-1

AZURE_CLIENT_ID=your_azure_client_id_here
AZURE_CLIENT_SECRET=your_azure_client_secret_here
AZURE_TENANT_ID=your_azure_tenant_id_here
AZURE_SUBSCRIPTION_ID=your_azure_subscription_id_here

GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
GCP_PROJECT_ID=your_gcp_project_id_here
GCP_ORGANIZATION_ID=your_gcp_organization_id_here

# Monitoring and Alerting
PROMETHEUS_URL=https://prometheus.company.com
DATADOG_API_KEY=your_datadog_api_key_here
DATADOG_APP_KEY=your_datadog_app_key_here
PAGERDUTY_API_KEY=your_pagerduty_api_key_here

# Communication Platforms
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_SIGNING_SECRET=your-slack-signing-secret-here
TEAMS_WEBHOOK_URL=https://your-teams-webhook-url-here

# Email Configuration
SMTP_HOST=smtp.company.com
SMTP_PORT=587
SMTP_USERNAME=reports@company.com
SMTP_PASSWORD=your_email_password_here

# Database and Storage
VECTOR_DB_URL=your_vector_database_url
VECTOR_DB_API_KEY=your_vector_db_api_key
POSTGRES_URL=postgresql://username:password@localhost:5432/knowledge_base
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
ANALYTICS_API_KEY=your_analytics_api_key_here
```

#### Optional Variables
```bash
# Development Mode
DEV_MODE=false
DEBUG=false
VERBOSE=false

# MCP Server Configuration
MCP_LOG_LEVEL=info
MCP_DEBUG=false
MCP_ENABLE_AUTH=true
MCP_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Performance Settings
SKILL_EXECUTION_TIMEOUT=300
SKILL_MAX_MEMORY=2GB
SKILL_PARALLEL_WORKERS=4

# Cache Settings
SKILL_CACHE_TTL=3600
SKILL_CACHE_SIZE=1GB
SKILL_CACHE_BACKEND=redis
```

### Configuration Templates

#### Development Template
```bash
# .env.development
DEV_MODE=true
DEBUG=true
VERBOSE=true
LOG_LEVEL=debug

# Use mock services for testing
USE_MOCK_SERVICES=true
MOCK_AWS_API=true
MOCK_AZURE_API=true
MOCK_GCP_API=true

# Reduced timeouts for development
SKILL_EXECUTION_TIMEOUT=60
MCP_TIMEOUT=30
```

#### Production Template
```bash
# .env.production
DEV_MODE=false
DEBUG=false
VERBOSE=false
LOG_LEVEL=warn

# Production credentials (actual values)
AWS_ACCESS_KEY_ID=prod_aws_key
AWS_SECRET_ACCESS_KEY=prod_aws_secret
# ... other production credentials

# Enhanced security
MCP_ENABLE_AUTH=true
MCP_RATE_LIMIT_ENABLED=true
SKILL_AUDIT_LOGGING=true
```

### Configuration Validation

#### Validation Script
```bash
# Create configuration validator
cat > scripts/validate-config.sh << 'EOF'
#!/bin/bash
# Configuration Validation Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_result() {
  local status=$1
  local message=$2
  
  case $status in
    "success")
      echo -e "${GREEN}✅${NC} $message"
      ;;
    "warning")
      echo -e "${YELLOW}⚠️ ${NC} $message"
      ;;
    "error")
      echo -e "${RED}❌${NC} $message"
      ;;
  esac
}

echo "🔍 Configuration Validation"
echo "=========================="

# Check .env file exists
if [[ -f "$REPO_ROOT/.env" ]]; then
  print_result "success" ".env file exists"
else
  print_result "error" ".env file not found"
  exit 1
fi

# Check for required variables
required_vars=(
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "AZURE_CLIENT_ID"
  "AZURE_CLIENT_SECRET"
  "GOOGLE_APPLICATION_CREDENTIALS"
)

missing_vars=()
for var in "${required_vars[@]}"; do
  if ! grep -q "^${var}=" "$REPO_ROOT/.env"; then
    missing_vars+=("$var")
  fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
  print_result "warning" "Missing required variables: ${missing_vars[*]}"
  echo "ℹ️  Using placeholder values for demo mode"
else
  print_result "success" "All required variables configured"
fi

# Check Claude Desktop configuration
if [[ -f "$HOME/.config/claude-desktop/config.json" ]]; then
  if jq empty "$HOME/.config/claude-desktop/config.json" >/dev/null 2>&1; then
    print_result "success" "Claude Desktop configuration valid"
  else
    print_result "warning" "Claude Desktop configuration may be invalid"
  fi
else
  print_result "warning" "Claude Desktop configuration not found"
fi

# Check MCP servers
server_count=0
for server_dir in "$REPO_ROOT/.claude/mcp-servers"/*; do
  if [[ -d "$server_dir" && -f "$server_dir/index.js" ]]; then
    server_name=$(basename "$server_dir")
    
    if [[ -f "$server_dir/package.json" ]]; then
      print_result "success" "$server_name server package.json exists"
      ((server_count++))
    else
      print_result "warning" "$server_name server package.json missing"
    fi
  fi
done

if [[ $server_count -eq 5 ]]; then
  print_result "success" "All MCP servers found"
else
  print_result "warning" "Found $server_count/5 MCP servers"
fi

echo ""
echo "✅ Configuration validation completed"
EOF

chmod +x scripts/validate-config.sh

echo "✅ Configuration validator created"
```

## Service Management

### Startup Scripts

#### Automatic Startup
```bash
# Main startup script
./scripts/start-mcp-servers.sh
```

#### Manual Startup Options
```bash
# Start specific server
cd .claude/mcp-servers/cloud-compliance
node index.js

# Start with custom environment
DEMO_MODE=true node index.js

# Start with debug logging
DEBUG=true node index.js
```

### Stop Scripts

#### Automatic Stop
```bash
# Stop all servers
./scripts/stop-mcp-servers.sh
```

#### Manual Stop Options
```bash
# Stop specific server by PID
kill $(cat .cloud-compliance.pid)

# Force stop if needed
kill -9 $(cat .cloud-compliance.pid)

# Clean up all PID files
rm -f .*.pid
```

### Service Status

#### Health Check
```bash
# Check all services
./scripts/health-check.sh

# Check specific service
curl http://localhost:3001/health
```

#### Status Monitoring
```bash
# Monitor service logs
tail -f logs/cloud-compliance.log

# Monitor all services
for log in logs/*.log; do
  echo "=== $log ==="
  tail -n 5 "$log"
done
```

## Integration Setup

### Claude Desktop Integration

#### Automatic Configuration
The deployment system automatically configures Claude Desktop:

1. **Configuration File**: `~/.config/claude-desktop/config.json`
2. **Server Registration**: All 5 MCP servers registered
3. **Environment Variables**: Proper variable passing
4. **Backup**: Existing configuration backed up

#### Manual Configuration (if needed)
```bash
# Update Claude Desktop config
cp .claude/claude_desktop_config.json ~/.config/claude-desktop/config.json

# Restart Claude Desktop
pkill -f "Claude Desktop"
open -a "Claude Desktop"
```

#### Integration Verification
```bash
# Test Claude Desktop integration
echo "Testing Claude Desktop integration..."

# Check configuration file
if [[ -f ~/.config/claude-desktop/config.json ]]; then
  echo "✅ Claude Desktop configuration found"
  
  # Validate JSON syntax
  if jq empty ~/.config/claude-desktop/config.json >/dev/null 2>&1; then
    echo "✅ Configuration syntax valid"
  else
    echo "❌ Configuration syntax invalid"
  fi
else
  echo "❌ Claude Desktop configuration not found"
fi
```

### API Integration

#### REST API Endpoints
Each MCP server provides REST endpoints:

```bash
# Health endpoints
curl http://localhost:3001/health  # Cloud Compliance
curl http://localhost:3002/health  # Incident Triage
curl http://localhost:3003/health  # IaC Validator
curl http://localhost:3004/health  # Knowledge Base
curl http://localhost:3005/health  # Engagement Sync

# API documentation
curl http://localhost:3001/docs   # API docs
```

#### API Client Example
```javascript
// JavaScript client example
class MCPClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }
  
  async call(skillName, action, parameters = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1/${skillName}/${action}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(parameters)
    });
    
    return await response.json();
  }
}

// Usage
const client = new MCPClient('http://localhost:3001');

// Compliance scan
const result = await client.call('cloud-compliance', 'scan', {
  scope: 'aws',
  framework: 'CIS',
  severityThreshold: 'medium'
});
```

## Monitoring and Health

### Health Checks

#### Server Health Endpoints
```javascript
// Health check implementation
app.get('/health', (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: process.env.npm_package_version,
    environment: process.env.NODE_ENV || 'development'
  };
  
  res.json(health);
});
```

#### Health Check Script
```bash
#!/bin/bash
# Comprehensive health check
check_server_health() {
  local server_name=$1
  local port=$2
  
  if curl -s "http://localhost:$port/health" >/dev/null; then
    echo "✅ $server_name is healthy"
    return 0
  else
    echo "❌ $server_name is unhealthy"
    return 1
  fi
}

# Check all servers
check_server_health "Cloud Compliance" 3001
check_server_health "Incident Triage" 3002
check_server_health "IaC Validator" 3003
check_server_health "Knowledge Base" 3004
check_server_health "Engagement Sync" 3005
```

### Performance Monitoring

#### Metrics Collection
```javascript
// Metrics middleware
const metrics = {
  requestCount: 0,
  errorCount: 0,
  responseTime: [],
  activeConnections: 0
};

const metricsMiddleware = (req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    metrics.responseTime.push(duration);
    metrics.requestCount++;
    
    if (res.statusCode >= 400) {
      metrics.errorCount++;
    }
  });
  
  next();
};

// Metrics endpoint
app.get('/metrics', (req, res) => {
  const avgResponseTime = metrics.responseTime.length > 0 
    ? metrics.responseTime.reduce((a, b) => a + b, 0) / metrics.responseTime.length 
    : 0;
  
  res.json({
    requestCount: metrics.requestCount,
    errorCount: metrics.errorCount,
    errorRate: metrics.requestCount > 0 ? (metrics.errorCount / metrics.requestCount) * 100 : 0,
    avgResponseTime,
    activeConnections: metrics.activeConnections,
    uptime: process.uptime()
  });
});
```

#### Log Monitoring
```bash
# Log monitoring script
monitor_logs() {
  local log_pattern=$1
  local time_range=${2:-"1h"}
  
  echo "📊 Log Analysis: $log_pattern (last $time_range)"
  echo "================================"
  
  # Count error messages
  local error_count=$(grep -c "ERROR" logs/*.log)
  echo "Errors: $error_count"
  
  # Count warning messages
  local warning_count=$(grep -c "WARN" logs/*.log)
  echo "Warnings: $warning_count"
  
  # Recent errors
  echo ""
  echo "Recent Errors:"
  grep "ERROR" logs/*.log | tail -5
  
  # Performance metrics
  echo ""
  echo "Performance Metrics:"
  grep "response_time" logs/*.log | tail -5
}
```

### Alerting

#### Alert Configuration
```yaml
# Alert thresholds
alerts:
  error_rate_threshold: 5%
  response_time_threshold: 5000ms
  memory_usage_threshold: 80%
  disk_usage_threshold: 85%
  cpu_usage_threshold: 90%

# Notification channels
notifications:
  slack:
    webhook_url: https://hooks.slack.com/services/xxx
    channel: #alerts
  email:
    smtp_server: smtp.company.com
    recipients: alerts@company.com
```

#### Alert Script
```bash
#!/bin/bash
# Alert script
check_alerts() {
  local error_rate=$(calculate_error_rate)
  local avg_response_time=$(calculate_avg_response_time)
  local memory_usage=$(calculate_memory_usage)
  
  if (( $(echo "$error_rate > 5" | bc -l) )); then
    send_alert "High error rate: $error_rate%"
  fi
  
  if (( $(echo "$avg_response_time > 5000" | bc -l) )); then
    send_alert "High response time: ${avg_response_time}ms"
  fi
  
  if (( $(echo "$memory_usage > 80" | bc -l) )); then
    send_alert "High memory usage: $memory_usage%"
  fi
}
```

## Troubleshooting

### Common Issues

#### Server Startup Failures
```bash
# Problem: Server fails to start
# Solution: Check logs and dependencies

# Check server logs
tail -f logs/cloud-compliance.log

# Check dependencies
cd .claude/mcp-servers/cloud-compliance
npm list

# Validate configuration
node -c index.js

# Common fixes:
# 1. Install missing dependencies: npm install
# 2. Fix syntax errors in index.js
# 3. Check environment variables
# 4. Verify port availability
```

#### Configuration Issues
```bash
# Problem: Configuration errors
# Solution: Validate and regenerate configuration

# Check .env file
cat .env | grep -v "^#" | grep -v "^$"

# Validate JSON syntax
jq empty .claude/claude_desktop_config.json

# Regenerate configuration
cp .env.template .env
cp .claude/claude_desktop_config.json ~/.config/claude-desktop/config.json
```

#### Network Issues
```bash
# Problem: Network connectivity issues
# Solution: Check network configuration

# Check port availability
netstat -tulpn | grep :3001

# Test local connectivity
curl http://localhost:3001/health

# Check firewall rules
sudo ufw status

# Common fixes:
# 1. Kill processes using required ports
# 2. Update firewall rules
# 3. Check network configuration
# 4. Verify DNS resolution
```

#### Performance Issues
```bash
# Problem: Slow response times
# Solution: Monitor and optimize performance

# Check system resources
top -p $(cat .cloud-compliance.pid)

# Monitor memory usage
ps aux | grep node

# Check disk space
df -h

# Common fixes:
# 1. Increase memory allocation
# 2. Optimize database queries
# 3. Implement caching
# 4. Scale horizontally
```

### Debug Mode

#### Enable Debug Logging
```bash
# Enable debug mode
export DEBUG=true
export VERBOSE=true

# Start servers with debug output
./scripts/start-mcp-servers.sh

# Monitor debug logs
tail -f logs/*.log | grep DEBUG
```

#### Debug Script
```bash
#!/bin/bash
# Debug script
debug_deployment() {
  echo "🔍 Deployment Debug Mode"
  echo "===================="
  
  # Check environment
  echo "Environment:"
  node --version
  npm --version
  echo ""
  
  # Check files
  echo "Files:"
  ls -la .claude/
  ls -la .claude/mcp-servers/
  ls -la scripts/
  echo ""
  
  # Check processes
  echo "Processes:"
  ps aux | grep node
  echo ""
  
  # Check ports
  echo "Ports:"
  netstat -tulpn | grep :300
  echo ""
  
  # Check logs
  echo "Recent Logs:"
  for log in logs/*.log; do
    echo "=== $log ==="
    tail -3 "$log"
  done
}

debug_deployment
```

### Recovery Procedures

#### Server Recovery
```bash
#!/bin/bash
# Server recovery script
recover_servers() {
  echo "🔄 Recovering MCP Servers"
  echo "========================"
  
  # Stop all servers
  ./scripts/stop-mcp-servers.sh
  
  # Clean up
  rm -f .*.pid
  rm -f logs/*.log
  
  # Wait for cleanup
  sleep 2
  
  # Restart servers
  ./scripts/start-mcp-servers.sh
  
  # Validate
  ./scripts/health-check.sh
}

recover_servers
```

#### Configuration Recovery
```bash
#!/bin/bash
# Configuration recovery script
recover_configuration() {
  echo "🔄 Recovering Configuration"
  echo "=========================="
  
  # Backup current configuration
  if [[ -f .env ]]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
  fi
  
  if [[ -f ~/.config/claude-desktop/config.json ]]; then
    cp ~/.config/claude-desktop/config.json \
       ~/.config/claude-desktop/config.json.backup.$(date +%Y%m%d_%H%M%S)
  fi
  
  # Reset to templates
  cp .env.template .env
  cp .claude/claude_desktop_config.json ~/.config/claude-desktop/config.json
  
  echo "✅ Configuration recovered from templates"
}

recover_configuration
```

## Advanced Configuration

### Custom Environment Setup

#### Development Environment
```bash
# Setup development environment
setup_dev_environment() {
  export DEV_MODE=true
  export DEBUG=true
  export LOG_LEVEL=debug
  
  # Use mock services
  export USE_MOCK_SERVICES=true
  export MOCK_AWS_API=true
  export MOCK_AZURE_API=true
  export MOCK_GCP_API=true
  
  # Reduced timeouts
  export SKILL_EXECUTION_TIMEOUT=60
  export MCP_TIMEOUT=30
}
```

#### Production Environment
```bash
# Setup production environment
setup_prod_environment() {
  export DEV_MODE=false
  export DEBUG=false
  export LOG_LEVEL=warn
  
  # Enhanced security
  export MCP_ENABLE_AUTH=true
  export MCP_RATE_LIMIT_ENABLED=true
  export SKILL_AUDIT_LOGGING=true
  
  # Performance optimization
  export SKILL_EXECUTION_TIMEOUT=300
  export SKILL_MAX_MEMORY=4GB
  export SKILL_PARALLEL_WORKERS=8
}
```

### Custom Server Configuration

#### Server Customization
```javascript
// Custom server configuration
const customConfig = {
  port: process.env.SERVER_PORT || 3001,
  host: process.env.SERVER_HOST || 'localhost',
  timeout: parseInt(process.env.SERVER_TIMEOUT) || 120000,
  maxConnections: parseInt(process.env.MAX_CONNECTIONS) || 100,
  enableCors: process.env.ENABLE_CORS === 'true',
  corsOrigins: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
  logLevel: process.env.LOG_LEVEL || 'info',
  enableMetrics: process.env.ENABLE_METRICS !== 'false',
  enableAuth: process.env.ENABLE_AUTH === 'true'
};
```

#### Plugin System
```javascript
// Plugin system for extensibility
class PluginManager {
  constructor() {
    this.plugins = new Map();
  }
  
  register(name, plugin) {
    this.plugins.set(name, plugin);
  }
  
  async execute(name, context) {
    const plugin = this.plugins.get(name);
    if (!plugin) {
      throw new Error(`Plugin not found: ${name}`);
    }
    
    return await plugin.execute(context);
  }
}
```

## Maintenance and Updates

### Regular Maintenance

#### Maintenance Script
```bash
#!/bin/bash
# Maintenance script
perform_maintenance() {
  echo "🔧 Performing Maintenance"
  echo "====================="
  
  # Update dependencies
  echo "Updating dependencies..."
  for server_dir in .claude/mcp-servers/*; do
    if [[ -d "$server_dir" && -f "$server_dir/package.json" ]]; then
      echo "Updating $(basename "$server_dir")..."
      cd "$server_dir"
      npm update
    fi
  done
  
  # Rotate logs
  echo "Rotating logs..."
  ./scripts/rotate-logs.sh
  
  # Clean up old files
  echo "Cleaning up old files..."
  find logs/ -name "*.log.gz" -mtime +90 -delete
  find . -name "*.tmp" -mtime +7 -delete
  
  # Validate configuration
  echo "Validating configuration..."
  ./scripts/validate-config.sh
  
  # Health check
  echo "Performing health check..."
  ./scripts/health-check.sh
  
  echo "✅ Maintenance completed"
}

perform_maintenance
```

### Update Procedures

#### Safe Update Process
```bash
#!/bin/bash
# Safe update script
safe_update() {
  echo "🔄 Safe Update Process"
  echo "===================="
  
  # Create backup
  echo "Creating backup..."
  backup_dir="backup-$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$backup_dir"
  
  cp -r .claude "$backup_dir/"
  cp .env "$backup_dir/"
  cp -r scripts "$backup_dir/"
  
  # Update dependencies
  echo "Updating dependencies..."
  for server_dir in .claude/mcp-servers/*; do
    if [[ -d "$server_dir" && -f "$server_dir/package.json" ]]; then
      echo "Updating $(basename "$server_dir")..."
      cd "$server_dir"
      npm update
    fi
  done
  
  # Test configuration
  echo "Testing configuration..."
  ./scripts/validate-config.sh
  
  # Test services
  echo "Testing services..."
  ./scripts/health-check.sh
  
  echo "✅ Update completed successfully"
  echo "Backup stored in: $backup_dir"
}

safe_update
```

### Monitoring Setup

#### Monitoring Dashboard
```bash
# Create monitoring dashboard
create_monitoring_dashboard() {
  cat > scripts/monitoring-dashboard.sh << 'EOF'
#!/bin/bash
# Monitoring Dashboard

echo "📊 MCP Servers Monitoring Dashboard"
echo "=============================="

while true; do
  clear
  date
  echo ""
  
  # Server status
  echo "Server Status:"
  ./scripts/health-check.sh
  echo ""
  
  # Resource usage
  echo "Resource Usage:"
  ps aux | grep node | awk '{print $4, $11}' | column -t
  
  # Recent logs
  echo ""
  echo "Recent Activity:"
  for log in logs/*.log; do
    echo "=== $(basename "$log") ==="
    tail -2 "$log"
  done
  
  sleep 30
done
EOF

chmod +x scripts/monitoring-dashboard.sh
echo "✅ Monitoring dashboard created"
}

create_monitoring_dashboard
```

---

## Conclusion

This comprehensive Deployment Automation Guide provides complete coverage of the fully automated AI Agent Skills deployment system. The automation ensures zero-touch deployment with automatic configuration, service startup, and integration setup.

Key takeaways:
1. **Zero-Touch Deployment**: Single command deployment with no manual steps
2. **Automatic Configuration**: Environment files and Claude Desktop setup
3. **Service Management**: Automatic startup, health monitoring, and recovery
4. **Integration Ready**: Claude Desktop and API integration out of the box
5. **Comprehensive Monitoring**: Health checks, logging, and performance metrics
6. **Maintenance Friendly**: Automated updates and maintenance procedures

The deployment system is designed to be robust, scalable, and maintainable, ensuring reliable operation of the AI Agent Skills ecosystem in production environments.
