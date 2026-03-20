# AI Infrastructure Portal - API Reference

Complete API documentation for the AI Infrastructure Portal endpoints.

## Base URL
```
http://localhost:5001/api
```

## Authentication
Currently no authentication required for development. Add API keys for production use.

## Endpoints

### Health & Status

#### GET /api/health
Returns basic health status of the portal.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "uptime": "2h 30m"
}
```

#### GET /api/health/detailed
Returns detailed health status including all services.

**Response:**
```json
{
  "overall": "healthy",
  "services": {
    "temporal": { "status": "running", "responseTime": 45 },
    "prometheus": { "status": "running", "responseTime": 23 }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Core Data

#### GET /api/agents
Returns all agents with their current status and skills.

**Response:**
```json
{
  "agents": [
    {
      "id": "memory-agent-rust",
      "name": "Memory Agent (Rust)",
      "status": "idle",
      "skills": 8,
      "skillsList": ["analyze-logs", "optimize-costs"],
      "riskLevel": "low",
      "autonomy": "full",
      "memoryUsage": 150
    }
  ]
}
```

#### GET /api/skills
Returns all available skills from the repository.

**Response:**
```json
{
  "skills": [
    {
      "name": "optimize-costs",
      "description": "Multi-cloud cost optimization",
      "category": "enterprise",
      "risk_level": "medium",
      "autonomy": "conditional",
      "executions": 1250,
      "successRate": 96.5
    }
  ]
}
```

#### GET /api/services
Returns status of all monitored services.

**Response:**
```json
{
  "services": {
    "temporal": {
      "status": "running",
      "port": 7233,
      "uptime": "2d 4h"
    },
    "prometheus": {
      "status": "running",
      "port": 9090,
      "version": "2.40.0"
    }
  }
}
```

#### GET /api/metrics
Returns current system metrics.

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "system": {
    "cpu": 45.2,
    "memory": 68.1,
    "disk": 23.5
  },
  "services": {
    "temporal": { "workflows": 150, "activities": 1200 }
  }
}
```

### Enhanced Monitoring

#### GET /api/alerts
Returns active alerts and warnings.

**Response:**
```json
{
  "alerts": [
    {
      "id": "cpu-high",
      "severity": "warning",
      "message": "CPU usage above 80%",
      "timestamp": "2024-01-01T11:45:00Z",
      "resolved": false
    }
  ]
}
```

#### GET /api/metrics/history
Returns historical metrics data.

**Parameters:**
- `hours` (optional): Hours of history (default: 24)

**Response:**
```json
{
  "period": "24h",
  "data": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "cpu": 45.2,
      "memory": 68.1
    }
  ]
}
```

#### GET /api/metrics/prometheus
Returns metrics in Prometheus format.

**Response:**
```
# HELP ai_portal_cpu_usage CPU usage percentage
# TYPE ai_portal_cpu_usage gauge
ai_portal_cpu_usage 45.2

# HELP ai_portal_memory_usage Memory usage percentage
# TYPE ai_portal_memory_usage gauge
ai_portal_memory_usage 68.1
```

### Service Integrations

#### GET /api/argocd/applications
Returns ArgoCD application status.

**Response:**
```json
{
  "applications": [
    {
      "name": "ai-portal",
      "namespace": "default",
      "status": "Synced",
      "health": "Healthy",
      "repoUrl": "https://github.com/user/repo"
    }
  ]
}
```

#### GET /api/langfuse/metrics
Returns Langfuse usage metrics.

**Response:**
```json
{
  "totalTraces": 15000,
  "totalObservations": 45000,
  "usageByModel": {
    "gpt-4": 12000,
    "claude-3": 8000
  },
  "totalCost": 245.50
}
```

### Activity & Events

#### GET /api/activity
Returns recent system activity.

**Parameters:**
- `limit` (optional): Number of activities (default: 50)

**Response:**
```json
{
  "activities": [
    {
      "id": "wf-123",
      "type": "workflow_started",
      "message": "Cost optimization workflow started",
      "timestamp": "2024-01-01T11:30:00Z",
      "agent": "cost-optimizer"
    }
  ]
}
```

#### GET /api/activity/recent
Returns most recent activities (last 5 minutes).

**Response:**
```json
{
  "recent": [
    {
      "type": "agent_action",
      "agent": "memory-agent",
      "action": "processed_request",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### RAG Query

#### POST /api/rag/query
Process natural language queries about the system.

**Request:**
```json
{
  "query": "What services are currently running?"
}
```

**Response:**
```json
{
  "query": "What services are currently running?",
  "response": "Based on current monitoring data, the following services are running: Temporal (port 7233), Prometheus (port 9090), Redis (port 6379), and the AI Infrastructure Portal API itself.",
  "confidence": 0.95,
  "sources": ["services_endpoint", "health_checks"]
}
```

### Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable

Error response format:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Rate Limiting

- API requests are limited to 1000 per hour per IP
- Dashboard requests limited to 5000 per hour
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`: Maximum requests per hour
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

### WebSocket Support

Real-time updates available via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:5001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

Supported events:
- `agent_status_update`
- `service_health_change`
- `alert_triggered`
- `metrics_update`

---

For more details, see the [Deployment Guide](./DEPLOYMENT.md) or [Developer Setup](./DEVELOPER_SETUP.md).
