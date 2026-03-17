# API Reference - Comprehensive Dashboard

## Overview

The Comprehensive Dashboard API provides RESTful endpoints for accessing real-time AI agents metrics, skill information, time-series data, and failure analysis. This document provides complete API reference documentation.

## Base URL

```
Production: http://localhost:5001
Development: http://localhost:5000
Documentation: http://localhost:5001/docs
```

## Authentication

Currently, the API does not require authentication. Future versions may implement API keys or OAuth.

## Response Format

All responses use JSON format with the following structure:

```json
{
  "data": {...},
  "timestamp": "2025-03-17T10:30:00.000Z",
  "status": "success"
}
```

Error responses follow HTTP status codes with detailed error messages:

```json
{
  "detail": "Error description",
  "status_code": 500,
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

## Endpoints

### Health Check

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

---

### Agents

#### GET /api/v2/agents

Get comprehensive agent metrics from all sources.

**Query Parameters:**
None

**Response:**
```json
{
  "agents": [
    {
      "timestamp": "2025-03-17T10:30:00.000Z",
      "agent_name": "agent-dashboard-545b645768-gflgt",
      "agent_type": "kubernetes_pod",
      "status": "running",
      "pod_name": "agent-dashboard-545b645768-gflgt",
      "cpu_usage": 25.5,
      "memory_usage": 128.0,
      "success_rate": 100.0,
      "error_count": 0
    },
    {
      "timestamp": "2025-03-17T10:30:00.000Z",
      "agent_name": "cost-optimization-workflow",
      "agent_type": "temporal_workflow",
      "status": "running",
      "workflow_id": "workflow-12345",
      "success_rate": 98.5,
      "error_count": 2
    },
    {
      "timestamp": "2025-03-17T10:30:00.000Z",
      "agent_name": "agent-memory-rust",
      "agent_type": "memory_agent",
      "status": "running",
      "memory_agent_id": "rust-memory-001",
      "success_rate": 99.8,
      "error_count": 1
    }
  ],
  "total_count": 3,
  "by_type": {
    "kubernetes_pods": 1,
    "temporal_workflows": 1,
    "memory_agents": 1
  },
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

**Agent Types:**
- `kubernetes_pod`: Container-based agents running in Kubernetes
- `temporal_workflow`: Orchestration-based agents managed by Temporal
- `memory_agent`: Local inference agents with persistent memory
- `pi_mono_rpc`: Interactive AI assistance agents via RPC

**Status Values:**
- `running`: Agent is operational
- `failed`: Agent has encountered errors
- `unknown`: Agent status cannot be determined

---

### Skills

#### GET /api/v2/skills

Get detailed skill information with descriptions.

**Query Parameters:**
None

**Response:**
```json
{
  "skills": [
    {
      "timestamp": "2025-03-17T10:30:00.000Z",
      "skill_name": "optimize-costs",
      "skill_description": "Multi-cloud automation skill for cost optimizer operations. Use when managing cost optimizer across cloud providers.",
      "risk_level": "medium",
      "autonomy_level": "conditional",
      "execution_count": 150,
      "success_count": 147,
      "failure_count": 3,
      "avg_execution_time": 45.2
    },
    {
      "timestamp": "2025-03-17T10:30:00.000Z",
      "skill_name": "security-scanner",
      "skill_description": "Automated security scanning and vulnerability assessment for cloud infrastructure.",
      "risk_level": "high",
      "autonomy_level": "conditional",
      "execution_count": 89,
      "success_count": 88,
      "failure_count": 1,
      "avg_execution_time": 120.5
    }
  ],
  "total_count": 2,
  "by_risk_level": {
    "low": 0,
    "medium": 1,
    "high": 1
  },
  "by_autonomy_level": {
    "conditional": 2,
    "fully_auto": 0
  },
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

**Risk Levels:**
- `low`: Minimal risk, safe to execute
- `medium`: Moderate risk, requires monitoring
- `high`: High risk, requires approval

**Autonomy Levels:**
- `conditional`: Requires human oversight
- `fully_auto`: Can run without intervention

---

### Time-Series Metrics

#### GET /api/v2/metrics/timeseries

Get time-series metrics data for visualization.

**Query Parameters:**
- `metric_type` (string, required): Type of metrics to retrieve
  - `agents`: Agent performance metrics
  - `skills`: Skill execution metrics
- `time_range_hours` (integer, optional): Time range in hours (default: 24)
- `interval_minutes` (integer, optional): Data interval in minutes (default: 60)

**Example Request:**
```
GET /api/v2/metrics/timeseries?metric_type=agents&time_range_hours=24&interval_minutes=60
```

**Response for Agents:**
```json
{
  "metric_type": "agents",
  "time_range_hours": 24,
  "data": [
    [
      "2025-03-16T10:30:00.000Z",
      "kubernetes_pod",
      "running",
      2,
      100.0
    ],
    [
      "2025-03-16T11:30:00.000Z",
      "temporal_workflow",
      "running",
      3,
      98.5
    ]
  ],
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

**Data Format:**
- `[timestamp, agent_type, status, count, avg_success_rate]` for agents
- `[timestamp, risk_level, total_executions, avg_time]` for skills

---

### Failure Analysis

#### GET /api/v2/failures/analysis

Get comprehensive failure analysis with root cause.

**Query Parameters:**
- `time_range_hours` (integer, optional): Time range for analysis (default: 24)

**Example Request:**
```
GET /api/v2/failures/analysis?time_range_hours=24
```

**Response:**
```json
{
  "success_rate": 98.75,
  "total_operations": 240,
  "total_errors": 3,
  "failure_analysis": {
    "total_failures": 3,
    "error_types": {
      "timeout": 2,
      "permission_denied": 1
    },
    "agents_with_failures": {
      "cost-optimizer-agent": 2,
      "security-scanner-agent": 1
    },
    "recent_failures": [
      [
        1,
        "2025-03-17T09:15:00.000Z",
        "cost-optimizer-agent",
        "optimize-costs",
        "timeout",
        "Operation timed out after 30 seconds",
        "Resource exhaustion",
        "Increased memory limits",
        "medium",
        "resolved"
      ],
      [
        2,
        "2025-03-17T08:45:00.000Z",
        "security-scanner-agent",
        "security-scanner",
        "permission_denied",
        "Access denied to cloud resources",
        "Missing IAM permissions",
        "Updated service account permissions",
        "high",
        "resolved"
      ]
    ]
  },
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

**Failure Data Format:**
`[id, timestamp, agent_name, skill_name, error_type, error_message, root_cause, resolution, severity, status]`

**Severity Levels:**
- `low`: Minor issues with minimal impact
- `medium`: Moderate issues requiring attention
- `high`: Critical issues requiring immediate action

**Status Values:**
- `open`: Failure is being investigated
- `resolved`: Failure has been resolved
- `closed`: Failure investigation is complete

---

### Report Failure

#### POST /api/v2/failures/report

Report a new failure for analysis.

**Request Body:**
```json
{
  "agent_name": "test-agent",
  "error_type": "timeout",
  "error_message": "Operation timed out",
  "severity": "medium",
  "skill_name": "optimize-costs"
}
```

**Parameters:**
- `agent_name` (string, required): Name of the agent experiencing failure
- `error_type` (string, required): Type of error that occurred
- `error_message` (string, required): Detailed error message
- `severity` (string, optional): Severity level (default: "medium")
- `skill_name` (string, optional): Name of the skill being executed

**Response:**
```json
{
  "status": "recorded",
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

---

## Data Models

### AgentMetrics

```typescript
interface AgentMetrics {
  timestamp: string;
  agent_name: string;
  agent_type: "kubernetes_pod" | "temporal_workflow" | "memory_agent" | "pi_mono_rpc";
  status: "running" | "failed" | "unknown";
  pod_name?: string;
  workflow_id?: string;
  memory_agent_id?: string;
  cpu_usage?: number;
  memory_usage?: number;
  success_rate?: number;
  error_count?: number;
}
```

### SkillMetrics

```typescript
interface SkillMetrics {
  timestamp: string;
  skill_name: string;
  skill_description?: string;
  risk_level?: "low" | "medium" | "high";
  autonomy_level?: "conditional" | "fully_auto";
  execution_count?: number;
  success_count?: number;
  failure_count?: number;
  avg_execution_time?: number;
}
```

### FailureReport

```typescript
interface FailureReport {
  agent_name: string;
  error_type: string;
  error_message: string;
  severity?: "low" | "medium" | "high";
  skill_name?: string;
}
```

## HTTP Status Codes

| Code | Description |
|---|---|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Rate Limiting

Currently, no rate limiting is implemented. Future versions may implement rate limiting to prevent abuse.

## Error Handling

### Common Error Scenarios

#### 1. Database Connection Error
```json
{
  "detail": "Database connection failed",
  "status_code": 500,
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

#### 2. Kubernetes API Error
```json
{
  "detail": "Failed to connect to Kubernetes API",
  "status_code": 503,
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

#### 3. Skill Parsing Error
```json
{
  "detail": "Failed to parse skill file: optimize-costs/SKILL.md",
  "status_code": 500,
  "timestamp": "2025-03-17T10:30:00.000Z"
}
```

## SDK Examples

### Python

```python
import requests

class DashboardAPI:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
    
    def get_agents(self):
        """Get all agent metrics"""
        response = requests.get(f"{self.base_url}/api/v2/agents")
        response.raise_for_status()
        return response.json()
    
    def get_skills(self):
        """Get all skill information"""
        response = requests.get(f"{self.base_url}/api/v2/skills")
        response.raise_for_status()
        return response.json()
    
    def get_failure_analysis(self, hours=24):
        """Get failure analysis"""
        response = requests.get(f"{self.base_url}/api/v2/failures/analysis", 
                               params={"time_range_hours": hours})
        response.raise_for_status()
        return response.json()
    
    def report_failure(self, agent_name, error_type, error_message, severity="medium"):
        """Report a new failure"""
        data = {
            "agent_name": agent_name,
            "error_type": error_type,
            "error_message": error_message,
            "severity": severity
        }
        response = requests.post(f"{self.base_url}/api/v2/failures/report", json=data)
        response.raise_for_status()
        return response.json()

# Usage
api = DashboardAPI()
agents = api.get_agents()
skills = api.get_skills()
failures = api.get_failure_analysis()
```

### JavaScript

```javascript
class DashboardAPI {
    constructor(baseUrl = 'http://localhost:5001') {
        this.baseUrl = baseUrl;
    }
    
    async getAgents() {
        const response = await fetch(`${this.baseUrl}/api/v2/agents`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
    
    async getSkills() {
        const response = await fetch(`${this.baseUrl}/api/v2/skills`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
    
    async getFailureAnalysis(hours = 24) {
        const response = await fetch(`${this.baseUrl}/api/v2/failures/analysis?time_range_hours=${hours}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
    
    async reportFailure(agentName, errorType, errorMessage, severity = 'medium') {
        const response = await fetch(`${this.baseUrl}/api/v2/failures/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                agent_name: agentName,
                error_type: errorType,
                error_message: errorMessage,
                severity: severity
            })
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    }
}

// Usage
const api = new DashboardAPI();
api.getAgents().then(agents => console.log(agents));
api.getSkills().then(skills => console.log(skills));
```

### cURL

```bash
# Get agents
curl -X GET "http://localhost:5001/api/v2/agents"

# Get skills
curl -X GET "http://localhost:5001/api/v2/skills"

# Get failure analysis
curl -X GET "http://localhost:5001/api/v2/failures/analysis?time_range_hours=24"

# Report failure
curl -X POST "http://localhost:5001/api/v2/failures/report" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test-agent",
    "error_type": "timeout",
    "error_message": "Operation timed out",
    "severity": "medium"
  }'
```

## Testing

### Unit Testing

The API includes built-in health checks that can be used for testing:

```bash
# Health check
curl http://localhost:5001/health

# Test data collection
curl http://localhost:5001/api/v2/agents
curl http://localhost:5001/api/v2/skills
```

### Integration Testing

For integration testing, use the test endpoints:

```bash
# Test with sample data
curl -X POST "http://localhost:5001/api/v2/failures/report" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test-agent",
    "error_type": "test_error",
    "error_message": "Test error message",
    "severity": "low"
  }'
```

## Monitoring

### API Metrics

The API exposes metrics for monitoring:

- Request count by endpoint
- Response times
- Error rates
- Database connection status

### Logging

API logs include:
- Request timestamps
- Endpoint accessed
- Response status codes
- Error details
- Performance metrics

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 2.0.0 | 2025-03-17 | Initial comprehensive dashboard API |
| 2.0.1 | TBD | Bug fixes and improvements |

---

**API Version**: 2.0.0  
**Base URL**: http://localhost:5001  
**Documentation**: http://localhost:5001/docs  
**Last Updated**: 2025-03-17
