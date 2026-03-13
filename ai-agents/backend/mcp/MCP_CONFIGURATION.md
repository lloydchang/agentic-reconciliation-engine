# MCP Configuration Guide

This guide explains how to configure and deploy the MCP (Model Context Protocol) server for the Temporal AI Agents system.

## Environment Variables

The MCP server can be configured using the following environment variables:

### Core MCP Configuration

```bash
# Enable/disable MCP server
ENABLE_MCP=true

# Server identification
MCP_SERVER_NAME="Temporal AI Agents"
MCP_SERVER_VERSION="1.0.0"

# Transport configuration
MCP_TRANSPORT="stdio"          # Options: stdio, websocket, http
MCP_PORT="8082"                # Port for websocket/http transports
```

### Authentication Configuration

```bash
# Enable authentication
MCP_ENABLE_AUTH=false          # Set to true to enable auth

# API key authentication
MCP_API_KEY="your-api-key-here"

# Development mode (adds example API keys)
MCP_DEV_MODE=true              # Adds dev keys for testing
```

### Access Control

```bash
# Limit available tools (comma-separated)
MCP_ALLOWED_TOOLS="start_compliance_workflow,get_workflow_status"

# Limit available resources (comma-separated)
MCP_ALLOWED_RESOURCES="workflow://results,compliance://reports"

# Empty lists allow all tools/resources
MCP_ALLOWED_TOOLS=""
MCP_ALLOWED_RESOURCES=""
```

## Configuration Examples

### Development Setup

```bash
# Enable MCP with stdio transport (default)
export ENABLE_MCP=true
export MCP_TRANSPORT=stdio
export MCP_ENABLE_AUTH=false
export MCP_DEV_MODE=true
```

### Production Setup with Authentication

```bash
# Production configuration
export ENABLE_MCP=true
export MCP_SERVER_NAME="Production Temporal AI Agents"
export MCP_TRANSPORT=http
export MCP_PORT=8082
export MCP_ENABLE_AUTH=true
export MCP_API_KEY="prod-secure-api-key-12345"
export MCP_ALLOWED_TOOLS="start_compliance_workflow,start_security_scan,get_workflow_status"
export MCP_ALLOWED_RESOURCES="workflow://results,compliance://reports"
```

### WebSocket Setup for Real-time Clients

```bash
# WebSocket configuration
export ENABLE_MCP=true
export MCP_TRANSPORT=websocket
export MCP_PORT=8082
export MCP_ENABLE_AUTH=true
export MCP_API_KEY="ws-api-key-67890"
```

## Transport Options

### 1. StdIO Transport (Default)

- **Use Case**: Command-line tools and direct process communication
- **Configuration**: `MCP_TRANSPORT=stdio`
- **Port**: Not used
- **Authentication**: Optional API key

**Example Usage**:
```bash
# Start the main application
./main_v2_enhanced

# In another terminal, use MCP client
mcp-client --transport stdio --api-key "your-key"
```

### 2. HTTP Transport

- **Use Case**: Web applications and REST API integration
- **Configuration**: `MCP_TRANSPORT=http`
- **Port**: `MCP_PORT` (default: 8082)
- **Authentication**: API key in Authorization header

**Example Usage**:
```bash
# Start server
export MCP_TRANSPORT=http
export MCP_PORT=8082
./main_v2_enhanced

# HTTP client examples
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Tool call
curl -X POST http://localhost:8082/mcp/tools/start_compliance_workflow \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"targetResource":"vm-web-server-001","complianceType":"SOC2"}'
```

### 3. WebSocket Transport

- **Use Case**: Real-time web applications and streaming
- **Configuration**: `MCP_TRANSPORT=websocket`
- **Port**: `MCP_PORT` (default: 8082)
- **Authentication**: API key in connection headers

**Example Usage**:
```javascript
// WebSocket client
const ws = new WebSocket('ws://localhost:8082/mcp');
ws.onopen = () => {
  // Send initialization
  ws.send(JSON.stringify({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "web-client", version: "1.0.0" }
    }
  }));
};
```

## Authentication Setup

### API Key Authentication

1. **Set API Key**:
```bash
export MCP_ENABLE_AUTH=true
export MCP_API_KEY="your-secure-api-key"
```

2. **Client Usage**:
```bash
# StdIO with API key
mcp-client --transport stdio --api-key "your-secure-api-key"

# HTTP with API key
curl -H "Authorization: Bearer your-secure-api-key" http://localhost:8082/mcp

# WebSocket with API key
const ws = new WebSocket('ws://localhost:8082/mcp', [], {
  headers: { 'Authorization': 'Bearer your-secure-api-key' }
});
```

### Development API Keys

When `MCP_DEV_MODE=true`, these example keys are available:

- `dev-api-key-12345`: Full access (tools:*, resources:*)
- `limited-api-key-67890`: Limited access (tools:start_compliance_workflow, resources:read)

## Docker Deployment

### Dockerfile Configuration

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go mod tidy && go build -o main ./main_v2_enhanced.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
COPY --from=builder /app/mcp ./mcp
EXPOSE 8081 8082
CMD ["./main"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  temporal-ai-agents:
    build: .
    ports:
      - "8081:8081"  # HTTP API
      - "8082:8082"  # MCP Server
    environment:
      - ENABLE_MCP=true
      - MCP_TRANSPORT=http
      - MCP_PORT=8082
      - MCP_ENABLE_AUTH=true
      - MCP_API_KEY=${MCP_API_KEY}
      - TEMPORAL_HOST=temporal:7233
    depends_on:
      - temporal
      - postgres

  mcp-client-example:
    image: your-mcp-client:latest
    environment:
      - MCP_SERVER_URL=http://temporal-ai-agents:8082
      - MCP_API_KEY=${MCP_API_KEY}
    depends_on:
      - temporal-ai-agents
```

## Kubernetes Deployment

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-config
data:
  ENABLE_MCP: "true"
  MCP_TRANSPORT: "http"
  MCP_PORT: "8082"
  MCP_ENABLE_AUTH: "true"
  MCP_SERVER_NAME: "Kubernetes Temporal AI Agents"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-secrets
type: Opaque
data:
  MCP_API_KEY: <base64-encoded-api-key>
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-ai-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: temporal-ai-agents
  template:
    metadata:
      labels:
        app: temporal-ai-agents
    spec:
      containers:
      - name: app
        image: temporal-ai-agents:latest
        ports:
        - containerPort: 8081
        - containerPort: 8082
        envFrom:
        - configMapRef:
            name: mcp-config
        - secretRef:
            name: mcp-secrets
```

## Client Integration Examples

### Python Client

```python
import requests
import json

class MCPClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def start_compliance_workflow(self, target_resource, compliance_type):
        response = requests.post(
            f"{self.base_url}/mcp/tools/start_compliance_workflow",
            headers=self.headers,
            json={
                "targetResource": target_resource,
                "complianceType": compliance_type,
                "priority": "normal"
            }
        )
        return response.json()

# Usage
client = MCPClient("http://localhost:8082", api_key="your-key")
result = client.start_compliance_workflow("vm-web-server-001", "SOC2")
print(result)
```

### JavaScript Client

```javascript
class MCPClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json',
        };
        if (apiKey) {
            this.headers['Authorization'] = `Bearer ${apiKey}`;
        }
    }

    async startComplianceWorkflow(targetResource, complianceType) {
        const response = await fetch(`${this.baseUrl}/mcp/tools/start_compliance_workflow`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                targetResource,
                complianceType,
                priority: 'normal'
            })
        });
        return await response.json();
    }
}

// Usage
const client = new MCPClient('http://localhost:8082', 'your-key');
client.startComplianceWorkflow('vm-web-server-001', 'SOC2')
    .then(result => console.log(result));
```

## Security Best Practices

1. **Use HTTPS in production** for HTTP transport
2. **Rotate API keys regularly**
3. **Implement rate limiting** on MCP endpoints
4. **Audit MCP usage** through logs
5. **Network segmentation** - restrict MCP access to authorized networks
6. **Use environment variables** for sensitive configuration
7. **Enable authentication** in production environments

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure MCP_PORT doesn't conflict with other services
2. **Authentication failures**: Verify API key is correctly set
3. **Transport errors**: Check firewall rules for WebSocket/HTTP access
4. **Permission denied**: Verify MCP_ALLOWED_TOOLS and MCP_ALLOWED_RESOURCES

### Debug Logging

Enable debug logging:
```bash
export LOG_LEVEL=debug
export MCP_DEV_MODE=true  # Adds more verbose logging
```

### Health Check

Monitor MCP server health:
```bash
curl http://localhost:8081/health  # Main application health
curl http://localhost:8082/mcp     # MCP endpoint health (if http transport)
```

## Migration from REST API

If you're currently using the REST API, you can gradually migrate to MCP:

1. **Phase 1**: Enable MCP alongside REST API
2. **Phase 2**: Update clients to use MCP for new features
3. **Phase 3**: Migrate existing clients to MCP
4. **Phase 4**: Deprecate REST API endpoints

The MCP server provides the same functionality as the REST API with standardized protocol support.
