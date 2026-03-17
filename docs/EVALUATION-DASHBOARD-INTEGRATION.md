# Evaluation Dashboard Integration Guide

## Overview

This guide documents the complete integration of the Agent Tracing Evaluation Framework with the GitOps Infra Control Plane dashboard. The integration provides real-time monitoring, health checks, and auto-fix capabilities for AI agents running in the distributed system.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Evaluation     │    │   Dashboard     │    │   Frontend      │
│  Framework      │───▶│   Backend       │───▶│   Interface     │
│  (Python)       │    │   (Go)          │    │   (React)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   RAG Service   │    │   WebSocket     │
│   Server        │    │   Integration   │    │   Hub           │
│   (Port 8082)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. Evaluation Framework (Python)

**Location**: `/agent-tracing-evaluation/`

**Key Files**:
- `api_server.py` - FastAPI server exposing evaluation endpoints
- `server_manager.py` - Background process management
- `main.py` - Core evaluation framework with evaluators
- `evaluators/` - Individual evaluator modules

**Evaluators**:
- **Monitoring Evaluator**: Infrastructure, Temporal, and agent health monitoring
- **Auto-Fix Manager**: Automated issue resolution with backoff mechanisms
- **Health Check Evaluator**: Worker health and conversation tracking

### 2. Dashboard Backend (Go)

**Location**: `/core/ai/runtime/dashboard/`

**Integration Points**:
- `internal/rag/evaluation_source.go` - RAG data source for evaluation queries
- `internal/services/evaluation_service.go` - HTTP client for evaluation API
- `internal/models/evaluation.go` - Data models for evaluation results
- `internal/api/handler.go` - API endpoints for evaluation data

### 3. API Endpoints

#### Evaluation Framework API (Port 8082)

```bash
# Health check
GET /health

# Agent health evaluation
GET /api/v1/evaluation/health

# Monitoring evaluation
GET /api/v1/evaluation/monitoring

# Detected issues
GET /api/v1/evaluation/issues

# Auto-fix status
GET /api/v1/evaluation/auto-fix

# Comprehensive summary
GET /api/v1/evaluation/summary

# Run custom evaluation
POST /api/v1/evaluation/evaluate
```

#### Dashboard API (Port 8080)

```bash
# Proxy evaluation endpoints
GET /api/v1/evaluation/health
GET /api/v1/evaluation/monitoring
GET /api/v1/evaluation/issues
GET /api/v1/evaluation/auto-fix
GET /api/v1/evaluation/summary
```

## Setup and Deployment

### 1. Prerequisites

```bash
# Python dependencies
pip install fastapi uvicorn

# Go dependencies (handled via go.mod)
cd core/ai/runtime/dashboard
go mod tidy
```

### 2. Start Evaluation Server

```bash
# Using server manager (recommended)
cd agent-tracing-evaluation
python server_manager.py start --port 8082

# Or directly (foreground mode)
python api_server.py --port 8082 --no-reload
```

### 3. Start Dashboard

```bash
cd core/ai/runtime/dashboard
go run cmd/server/main.go
```

### 4. Environment Configuration

```bash
# Evaluation API URL
export EVALUATION_API_URL="http://localhost:8082"

# RAG Integration
export RAG_ENABLED="true"
export QWEN_LLAMACPP_URL="http://localhost:8080"
export QWEN_MODEL="qwen2.5:0.5b"
```

## Data Flow

### 1. Evaluation Collection

1. **Trace Data**: Collected from Temporal workflows, Kubernetes events, and agent interactions
2. **Evaluation Processing**: Evaluators analyze traces for issues, performance, and health metrics
3. **Result Storage**: Results cached in memory and available via FastAPI endpoints

### 2. Dashboard Integration

1. **RAG Integration**: Evaluation data integrated into RAG search results
2. **API Proxy**: Dashboard backend proxies evaluation requests to evaluation server
3. **Frontend Display**: React components visualize evaluation metrics and issues

### 3. Real-time Updates

1. **WebSocket Hub**: Real-time updates pushed to connected clients
2. **Auto-refresh**: Frontend periodically fetches latest evaluation data
3. **Alert Integration**: Critical issues trigger dashboard alerts

## Monitoring and Observability

### 1. Health Metrics

- **Agent Health**: Worker status, conversation completion rates
- **Infrastructure Health**: Pod restarts, resource usage, network connectivity
- **Temporal Health**: Workflow success rates, activity performance, queue health

### 2. Issue Detection

- **Critical Issues**: Service failures, security violations, data corruption
- **High Priority**: Performance degradation, resource exhaustion
- **Medium Priority**: Configuration drift, minor errors
- **Low Priority**: Optimization opportunities, best practice violations

### 3. Auto-Fix Capabilities

- **Pod Management**: Automatic restart of failing pods
- **Workflow Recovery**: Clear stuck workflows and timeouts
- **Resource Adjustment**: Dynamic scaling based on load
- **Configuration Repair**: Apply known-good configurations

## Security Considerations

### 1. Network Security

- **Internal Communication**: Evaluation API should be accessible only from dashboard backend
- **Firewall Rules**: Restrict evaluation server port (8082) to internal network
- **Authentication**: Dashboard should authenticate requests to evaluation API

### 2. Data Privacy

- **Sensitive Data**: Evaluation results may contain sensitive system information
- **Access Control**: Restrict evaluation data access to authorized users
- **Data Retention**: Implement appropriate data retention policies

## Troubleshooting

### 1. Common Issues

#### Server Not Starting
```bash
# Check if port is in use
lsof -i :8082

# Stop existing server
python server_manager.py stop

# Check logs
tail -f api_server.log
```

#### API Connection Issues
```bash
# Test evaluation API directly
curl http://localhost:8082/health

# Test dashboard proxy
curl http://localhost:8080/api/v1/evaluation/health

# Check environment variables
env | grep EVALUATION
```

#### Data Not Appearing
```bash
# Check evaluation framework status
python server_manager.py status

# Run manual evaluation
curl -X POST http://localhost:8082/api/v1/evaluation/evaluate \
  -H "Content-Type: application/json" \
  -d '{"traces": [], "evaluator_types": ["monitoring"]}'
```

### 2. Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL="debug"

# Run evaluation server in foreground
python api_server.py --port 8082 --no-reload

# Run dashboard with debug logs
cd core/ai/runtime/dashboard
LOG_LEVEL=debug go run cmd/server/main.go
```

## Performance Optimization

### 1. Caching Strategy

- **Evaluation Results**: Cache results for 5 minutes to reduce API calls
- **RAG Integration**: Cache evaluation documents in RAG index
- **Frontend State**: Implement client-side caching for UI components

### 2. Resource Management

- **Background Processing**: Run evaluations in background processes
- **Connection Pooling**: Reuse HTTP connections for API calls
- **Memory Management**: Limit evaluation history to prevent memory leaks

### 3. Scaling Considerations

- **Horizontal Scaling**: Deploy multiple evaluation server instances
- **Load Balancing**: Use load balancer for evaluation API requests
- **Database Integration**: Persist evaluation results for long-term analysis

## Development

### 1. Adding New Evaluators

1. **Create Evaluator Module**:
```python
# agent-tracing-evaluation/evaluators/new_evaluator.py
class NewEvaluator(BaseEvaluator):
    def evaluate(self, traces):
        # Implementation
        return results
```

2. **Register Evaluator**:
```python
# agent-tracing-evaluation/main.py
from evaluators.new_evaluator import NewEvaluator

framework = TracingEvaluationFramework()
framework.register_evaluator("new_evaluator", NewEvaluator())
```

3. **Add API Endpoint**:
```python
# agent-tracing-evaluation/api_server.py
@app.get("/api/v1/evaluation/new-metrics")
async def get_new_metrics():
    # Implementation
    return results
```

### 2. Frontend Integration

1. **API Service**:
```typescript
// src/services/evaluationService.ts
export const getEvaluationHealth = async () => {
  const response = await fetch('/api/v1/evaluation/health');
  return response.json();
};
```

2. **React Component**:
```tsx
// src/components/EvaluationHealth.tsx
import { getEvaluationHealth } from '../services/evaluationService';

export const EvaluationHealth = () => {
  const [health, setHealth] = useState(null);
  
  useEffect(() => {
    getEvaluationHealth().then(setHealth);
  }, []);
  
  return <div>{/* Render health data */}</div>;
};
```

## Maintenance

### 1. Regular Tasks

- **Log Rotation**: Rotate evaluation server logs weekly
- **Cache Cleanup**: Clear old evaluation cache entries
- **Health Checks**: Monitor evaluation server health and restart if needed

### 2. Updates and Upgrades

- **Dependency Updates**: Regularly update FastAPI, uvicorn, and Go dependencies
- **Security Patches**: Apply security patches promptly
- **Feature Enhancements**: Add new evaluators and monitoring capabilities

### 3. Backup and Recovery

- **Configuration Backup**: Backup evaluation framework configuration
- **Data Export**: Export evaluation history for analysis
- **Disaster Recovery**: Plan for evaluation server failure scenarios

## Integration Testing

### 1. End-to-End Tests

```bash
# Start all services
python server_manager.py start --port 8082
cd core/ai/runtime/dashboard && go run cmd/server/main.go

# Run integration tests
go test ./tests/integration/evaluation_test.go

# Cleanup
python server_manager.py stop
```

### 2. Load Testing

```bash
# Generate load on evaluation API
hey -n 1000 -c 10 http://localhost:8082/api/v1/evaluation/summary

# Monitor dashboard performance
curl -s http://localhost:8080/api/v1/system/metrics | jq '.response_time'
```

## Best Practices

### 1. Code Organization

- **Separation of Concerns**: Keep evaluation logic separate from API logic
- **Modular Design**: Design evaluators as independent modules
- **Interface Consistency**: Use consistent API patterns across endpoints

### 2. Error Handling

- **Graceful Degradation**: Handle evaluation server failures gracefully
- **User Feedback**: Provide clear error messages in dashboard
- **Retry Logic**: Implement exponential backoff for API calls

### 3. Documentation

- **API Documentation**: Keep OpenAPI/Swagger documentation updated
- **Code Comments**: Document complex evaluation logic
- **User Guides**: Maintain user-facing documentation

## Future Enhancements

### 1. Advanced Analytics

- **Trend Analysis**: Track evaluation metrics over time
- **Predictive Analytics**: Predict potential issues before they occur
- **Anomaly Detection**: Identify unusual patterns in evaluation data

### 2. Integration Expansion

- **External Monitoring**: Integrate with Prometheus, Grafana
- **Alert Management**: Connect to alerting systems like PagerDuty
- **ChatOps**: Enable evaluation queries via chat platforms

### 3. Machine Learning

- **Intelligent Auto-Fix**: Use ML to improve auto-fix effectiveness
- **Pattern Recognition**: Identify recurring issue patterns
- **Optimization Recommendations**: Suggest system improvements

---

## Appendix

### A. Configuration Reference

#### Evaluation Server Configuration
```python
# api_server.py configuration
DEFAULT_PORT = 8081
DEFAULT_HOST = "0.0.0.0"
LOG_LEVEL = "info"
CACHE_TTL = 300  # 5 minutes
```

#### Dashboard Configuration
```go
// main.go configuration
DefaultPort = 8080
EvaluationAPIURL = "http://localhost:8082"
RAGEnabled = true
```

### B. API Schema Examples

#### Health Evaluation Response
```json
{
  "status": "success",
  "data": {
    "worker_health": {
      "active_workers": 5,
      "failed_workers": 0,
      "response_time_ms": 150
    },
    "conversation_health": {
      "total_conversations": 100,
      "completion_rate": 0.95,
      "average_duration_ms": 2000
    },
    "overall_health_status": "healthy",
    "recommendations": []
  },
  "timestamp": "2026-03-17T10:44:55.543901"
}
```

#### Monitoring Evaluation Response
```json
{
  "status": "success",
  "data": {
    "infrastructure_health": {
      "pod_status": {"running": 10, "failed": 0},
      "resource_usage": {"cpu_percent": 45, "memory_percent": 60},
      "issues": []
    },
    "temporal_health": {
      "workflow_status": {"completed": 50, "failed": 2},
      "activity_performance": {"average_duration_ms": 1200},
      "timeout_issues": [],
      "issues": []
    },
    "agent_health": {
      "conversation_tracking": {"active": 5, "stuck": 0},
      "tool_execution": {"success_rate": 0.98},
      "issues": []
    },
    "total_issues": 0,
    "correlation_id": "eval_1773769495_9839"
  },
  "timestamp": "2026-03-17T10:44:55.543901"
}
```

### C. Troubleshooting Checklist

- [ ] Evaluation server running on correct port
- [ ] Dashboard can reach evaluation API
- [ ] Environment variables set correctly
- [ ] Logs show successful startup
- [ ] API endpoints responding with data
- [ ] Frontend displaying evaluation results
- [ ] WebSocket connections established
- [ ] Auto-fix mechanisms working
- [ ] Error handling functioning properly
- [ ] Performance within acceptable limits
