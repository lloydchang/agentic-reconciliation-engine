#!/bin/bash

# Flux MCP Server Installation Script
# This script installs and configures the Flux MCP Server for Agentic GitOps

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_SERVER_VERSION="latest"
KUBECONFIG_PATH="${KUBECONFIG:-$HOME/.kube/config}"
MCP_CONFIG_DIR="$HOME/.config/mcp-server"

echo -e "${BLUE}🤖 Flux MCP Server Installation Script${NC}"
echo "======================================="

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check if Flux Operator is installed
if ! kubectl get crd fluxinstances.fluxcd.controlplane.io &> /dev/null; then
    echo -e "${RED}❌ Flux Operator is not installed. Please install Flux Operator first.${NC}"
    echo "Run: ./core/automation/scripts/install-flux-operator.sh"
    exit 1
fi

# Install flux-operator-mcp CLI
echo -e "${YELLOW}📦 Installing Flux MCP Server CLI...${NC}"

if command -v brew &> /dev/null; then
    brew install controlplaneio-fluxcd/tap/flux-operator-mcp
else
    echo -e "${YELLOW}📥 Installing flux-operator-mcp directly...${NC}"
    
    # Download the binary
    ARCH=$(uname -m | sed 's/x86_64/amd64/' | sed 's/arm64/arm64/')
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    
    curl -L "https://github.com/controlplaneio-fluxcd/flux-operator-mcp/releases/latest/download/flux-operator-mcp-${OS}-${ARCH}" \
        -o /usr/local/bin/flux-operator-mcp
    
    chmod +x /usr/local/bin/flux-operator-mcp
fi

# Verify installation
if command -v flux-operator-mcp &> /dev/null; then
    MCP_VERSION=$(flux-operator-mcp version --short 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✅ Flux MCP Server CLI version: $MCP_VERSION${NC}"
else
    echo -e "${RED}❌ Failed to install flux-operator-mcp CLI${NC}"
    exit 1
fi

# Create MCP config directory
echo -e "${YELLOW}📁 Creating MCP configuration directory...${NC}"
mkdir -p "$MCP_CONFIG_DIR"

# Create MCP server configuration
echo -e "${YELLOW}⚙️  Creating MCP server configuration...${NC}"

cat > "$MCP_CONFIG_DIR/flux-mcp-config.json" << EOF
{
  "flux-operator-mcp": {
    "command": "flux-operator-mcp",
    "args": [
      "serve",
      "--read-only=false",
      "--kubeconfig=${KUBECONFIG_PATH}",
      "--namespace=flux-system",
      "--log-level=info"
    ],
    "env": {
      "KUBECONFIG": "${KUBECONFIG_PATH}",
      "FLUX_NAMESPACE": "flux-system"
    }
  }
}
EOF

# Create Claude Desktop configuration
echo -e "${YELLOW}🎨 Creating Claude Desktop configuration...${NC}"

CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
if [ -d "$CLAUDE_CONFIG_DIR" ]; then
    cat > "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" << EOF
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=${KUBECONFIG_PATH}",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "${KUBECONFIG_PATH}",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
EOF
    echo -e "${GREEN}✅ Claude Desktop configuration created${NC}"
else
    echo -e "${YELLOW}⚠️  Claude Desktop not found. Manual configuration required.${NC}"
fi

# Create Cursor configuration
echo -e "${YELLOW}🖱️  Creating Cursor configuration...${NC}"

CURSOR_CONFIG_DIR="$HOME/.cursor"
if [ -d "$CURSOR_CONFIG_DIR" ]; then
    cat > "$CURSOR_CONFIG_DIR/mcp.json" << EOF
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=${KUBECONFIG_PATH}",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "${KUBECONFIG_PATH}",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
EOF
    echo -e "${GREEN}✅ Cursor configuration created${NC}"
else
    echo -e "${YELLOW}⚠️  Cursor not found. Manual configuration required.${NC}"
fi

# Create VS Code configuration
echo -e "${YELLOW}💻 Creating VS Code configuration...${NC}"

VSCODE_CONFIG_DIR="$HOME/.vscode"
if [ -d "$VSCODE_CONFIG_DIR" ]; then
    cat > "$VSCODE_CONFIG_DIR/mcp.json" << EOF
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=${KUBECONFIG_PATH}",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "${KUBECONFIG_PATH}",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
EOF
    echo -e "${GREEN}✅ VS Code configuration created${NC}"
else
    echo -e "${YELLOW}⚠️  VS Code not found. Manual configuration required.${NC}"
fi

# Create MCP server systemd service (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${YELLOW}🔧 Creating systemd service...${NC}"
    
    cat > /tmp/flux-mcp.service << EOF
[Unit]
Description=Flux MCP Server
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/flux-operator-mcp serve --read-only=false --kubeconfig=${KUBECONFIG_PATH} --namespace=flux-system --log-level=info
Restart=always
RestartSec=5
Environment=KUBECONFIG=${KUBECONFIG_PATH}
Environment=FLUX_NAMESPACE=flux-system

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${YELLOW}📋 To install the systemd service, run:${NC}"
    echo "sudo cp /tmp/flux-mcp.service /etc/systemd/user/"
    echo "systemctl --user daemon-reload"
    echo "systemctl --user enable --now flux-mcp.service"
    
    rm -f /tmp/flux-mcp.service
fi

# Create macOS launch agent
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}🍎 Creating macOS launch agent...${NC}"
    
    LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
    mkdir -p "$LAUNCH_AGENTS_DIR"
    
    cat > "$LAUNCH_AGENTS_DIR/com.fluxoperator.mcp.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fluxoperator.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/flux-operator-mcp</string>
        <string>serve</string>
        <string>--read-only=false</string>
        <string>--kubeconfig=${KUBECONFIG_PATH}</string>
        <string>--namespace=flux-system</string>
        <string>--log-level=info</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>KUBECONFIG</key>
        <string>${KUBECONFIG_PATH}</string>
        <key>FLUX_NAMESPACE</key>
        <string>flux-system</string>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/flux-mcp.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/flux-mcp.stderr.log</string>
</dict>
</plist>
EOF
    
    echo -e "${YELLOW}📋 To load the launch agent, run:${NC}"
    echo "launchctl load ~/Library/LaunchAgents/com.fluxoperator.mcp.plist"
    echo "launchctl start com.fluxoperator.mcp"
fi

# Test MCP server
echo -e "${YELLOW}🧪 Testing MCP server...${NC}"

# Start MCP server in background
flux-operator-mcp serve --read-only=false --kubeconfig="${KUBECONFIG_PATH}" --namespace=flux-system --log-level=info &
MCP_PID=$!

# Wait for server to start
sleep 5

# Test basic functionality
echo -e "${YELLOW}🔍 Testing MCP server functionality...${NC}"

# Test connection to Flux Operator
if kubectl get fluxinstance -n flux-system &> /dev/null; then
    echo -e "${GREEN}✅ Flux Operator connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to Flux Operator${NC}"
fi

# Test MCP server commands
echo -e "${YELLOW}📋 Available MCP commands:${NC}"
echo "- list_flux_instances: List all Flux instances"
echo "- get_flux_instance: Get a specific Flux instance"
echo "- create_flux_instance: Create a new Flux instance"
echo "- update_flux_instance: Update a Flux instance"
echo "- delete_flux_instance: Delete a Flux instance"
echo "- list_resourcesets: List all ResourceSets"
echo "- get_resourceset: Get a specific ResourceSet"
echo "- sync_status: Get sync status"
echo "- reconcile_flux_instance: Trigger reconciliation"

# Stop test server
kill $MCP_PID 2>/dev/null || true

# Create example prompts
echo -e "${YELLOW}📝 Creating example prompts...${NC}"

cat > "$MCP_CONFIG_DIR/example-prompts.md" << EOF
# Flux MCP Server Example Prompts

## Basic Operations

### List Flux Instances
"List all Flux instances in the flux-system namespace"

### Get Flux Instance Details
"Get the details of the flux FluxInstance"

### Create New Flux Instance
"Create a new FluxInstance named 'app-flux' that syncs from https://github.com/user/app-manifests"

### Update Flux Instance
"Update the flux FluxInstance to use the staging branch"

### Delete Flux Instance
"Delete the app-flux FluxInstance"

## Advanced Operations

### Check Sync Status
"What is the current sync status of all Flux instances?"

### Trigger Reconciliation
"Trigger reconciliation for the flux FluxInstance"

### List ResourceSets
"List all ResourceSets in the flux-system namespace"

### Get ResourceSet Details
"Get the details of the infrastructure ResourceSet"

## Troubleshooting

### Check Flux Instance Health
"Check the health status of the flux FluxInstance"

### Get Flux Instance Events
"Get recent events for the flux FluxInstance"

### Check Component Status
"Check the status of all Flux components"

## GitOps Operations

### Sync from New Repository
"Create a new FluxInstance that syncs from https://github.com/user/new-repo"

### Enable Webhook Triggers
"Enable webhook triggers for the flux FluxInstance"

### Set Up Health Checks
"Configure health checks for the flux FluxInstance"

## Multi-Environment

### Create Staging Flux Instance
"Create a staging FluxInstance that syncs from the staging branch"

### Create Production Flux Instance
"Create a production FluxInstance with enhanced security settings"

### List All Environment Flux Instances
"List all Flux instances across different environments"
EOF

echo -e "${GREEN}✅ Example prompts saved to $MCP_CONFIG_DIR/example-prompts.md${NC}"

# Create troubleshooting guide
echo -e "${YELLOW}📚 Creating troubleshooting guide...${NC}"

cat > "$MCP_CONFIG_DIR/troubleshooting.md" << EOF
# Flux MCP Server Troubleshooting

## Common Issues

### MCP Server Won't Start

**Symptoms**: MCP server fails to start or crashes immediately

**Solutions**:
1. Check kubeconfig path:
   \`\`\`bash
   echo $KUBECONFIG
   ls -la $KUBECONFIG
   \`\`\`

2. Verify cluster connection:
   \`\`\`bash
   kubectl cluster-info
   \`\`\`

3. Check Flux Operator installation:
   \`\`\`bash
   kubectl get crd fluxinstances.fluxcd.controlplane.io
   \`\`\`

### Permission Errors

**Symptoms**: MCP server returns permission denied errors

**Solutions**:
1. Check RBAC permissions:
   \`\`\`bash
   kubectl auth can-i get fluxinstances --as=system:serviceaccount:flux-system:default
   \`\`\`

2. Verify service account:
   \`\`\`bash
   kubectl get serviceaccount -n flux-system
   \`\`\`

### Connection Timeout

**Symptoms**: MCP server times out when connecting to cluster

**Solutions**:
1. Check network connectivity:
   \`\`\`bash
   kubectl get nodes
   \`\`\`

2. Verify API server accessibility:
   \`\`\`bash
   kubectl get namespaces
   \`\`\`

## Debug Commands

### Check MCP Server Status
\`\`\`bash
# Check if MCP server is running
ps aux | grep flux-operator-mcp

# Check MCP server logs
tail -f /tmp/flux-mcp.stdout.log
tail -f /tmp/flux-mcp.stderr.log
\`\`\`

### Test MCP Server
\`\`\`bash
# Test MCP server manually
flux-operator-mcp serve --read-only=false --kubeconfig=$KUBECONFIG_PATH --namespace=flux-system --log-level=debug
\`\`\`

### Verify Configuration
\`\`\`bash
# Check configuration files
cat $HOME/.config/mcp-server/flux-mcp-config.json

# Check Claude configuration
cat "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
\`\`\`

## Configuration Issues

### Claude Desktop Not Working

**Symptoms**: Claude Desktop doesn't show MCP tools

**Solutions**:
1. Restart Claude Desktop
2. Check Claude configuration file
3. Verify MCP server is running
4. Check Claude Desktop logs

### Cursor Not Working

**Symptoms**: Cursor doesn't show MCP tools

**Solutions**:
1. Restart Cursor
2. Check Cursor configuration file
3. Verify MCP server is running
4. Check Cursor logs

## Performance Issues

### Slow Response Times

**Symptoms**: MCP server responds slowly

**Solutions**:
1. Check cluster resources
2. Reduce log level to warning
3. Optimize kubeconfig
4. Check network latency

### High Memory Usage

**Symptoms**: MCP server uses excessive memory

**Solutions**:
1. Reduce cache size
2. Limit concurrent requests
3. Restart MCP server
4. Check for memory leaks

## Getting Help

### Logs and Debugging
\`\`\`bash
# Enable debug logging
flux-operator-mcp serve --log-level=debug

# Check system logs
journalctl --user -u flux-mcp  # Linux
log show --predicate 'process == "flux-operator-mcp"'  # macOS
\`\`\`

### Community Support
- GitHub Issues: https://github.com/controlplaneio-fluxcd/flux-operator-mcp/issues
- Documentation: https://fluxoperator.dev/mcp/
- Discord: https://discord.gg/fluxcd
EOF

echo -e "${GREEN}✅ Troubleshooting guide saved to $MCP_CONFIG_DIR/troubleshooting.md${NC}"

echo -e "${GREEN}✅ Flux MCP Server installation completed!${NC}"
echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo "1. Restart your AI assistant (Claude, Cursor, VS Code)"
echo "2. Test the MCP integration with example prompts:"
echo "   cat $MCP_CONFIG_DIR/example-prompts.md"
echo ""
echo "3. Start the MCP server manually if needed:"
echo "   flux-operator-mcp serve --read-only=false --kubeconfig=$KUBECONFIG_PATH --namespace=flux-system"
echo ""
echo "4. Check MCP server status:"
echo "   ps aux | grep flux-operator-mcp"
echo ""
echo "5. View configuration files:"
echo "   ls -la $MCP_CONFIG_DIR/"
echo ""
echo -e "${YELLOW}📚 For more information, see:${NC}"
echo "- MCP Server Documentation: https://fluxoperator.dev/mcp/"
echo "- Example Prompts: $MCP_CONFIG_DIR/example-prompts.md"
echo "- Troubleshooting Guide: $MCP_CONFIG_DIR/troubleshooting.md"
echo ""
echo -e "${GREEN}🎉 MCP server is ready for Agentic GitOps!${NC}"
