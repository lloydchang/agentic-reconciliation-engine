# Qwen Consolidation Plan

## Overview

This document outlines the plan to consolidate Qwen LLM usage across all components (K8sGPT, Flux, Argo, Flagger, etc.) to use the centralized Qwen instance in `agent-memory-rust` instead of maintaining separate containers.

## Current State

### Existing Qwen Deployments
- **agent-memory-rust**: Central Qwen instance using llama.cpp for inference
- **K8sGPT**: Separate Qwen container for Kubernetes analysis  
- **Flagger AI Integration**: Planned separate Qwen instance
- **Other Components**: Potential future Qwen deployments

### Current agent-memory-rust Architecture
- **Inference Engine**: llama.cpp for local Qwen model execution
- **Memory Management**: SQLite-based persistent memory storage
- **API Layer**: Internal Rust API for memory operations
- **Model Loading**: Qwen models loaded via llama.cpp bindings

### Issues with Current Approach
- Resource duplication and inefficiency
- Inconsistent model versions and configurations
- Multiple monitoring and maintenance points
- Increased infrastructure complexity

## Target Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   K8sGPT        │    │  agent-memory-   │    │    Flux         │
│                 │───▶│    rust (Qwen)   │◀───│                 │
│   Argo CD       │    │                  │    │   Flagger       │
│                 │    │  - llama.cpp     │    │                 │
│   Other Tools   │    │  - HTTP API      │    │   Future Tools  │
└─────────────────┘    │  - Shared Memory │    └─────────────────┘
                       └──────────────────┘
```

### Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    agent-memory-rust                        │
├─────────────────────────────────────────────────────────────┤
│  HTTP API Layer (axum)                                       │
│  ├── Authentication & Authorization                         │
│  ├── Request Validation & Rate Limiting                      │
│  └── OpenAPI Documentation                                   │
├─────────────────────────────────────────────────────────────┤
│  Inference Layer (llama.cpp)                                 │
│  ├── Model Loading & Management                              │
│  ├── Token Generation & Streaming                            │
│  └── Context Window Management                              │
├─────────────────────────────────────────────────────────────┤
│  Memory Layer (SQLite)                                       │
│  ├── Episodic Memory (conversations)                         │
│  ├── Semantic Memory (concepts)                              │
│  └── Working Memory (current session)                        │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Enhance agent-memory-rust

**Objective**: Add HTTP API endpoint for external Qwen inference

**Tasks**:
1. **Add HTTP Server Module**
   - Implement REST API endpoints using axum framework
   - Add OpenAPI/Swagger documentation
   - Implement authentication/authorization
   - Add request validation and rate limiting

2. **Qwen Inference Endpoint**
   - `POST /api/v1/inference/completions`
   - `POST /api/v1/inference/chat`
   - Support streaming responses via Server-Sent Events
   - Request/response validation
   - Integration with existing llama.cpp inference

3. **Configuration Management**
   - Expose model configuration via API
   - Support multiple model endpoints
   - Dynamic model switching
   - llama.cpp model parameters configuration

4. **Monitoring & Observability**
   - Prometheus metrics for inference requests
   - Request tracing and logging
   - Health check endpoints
   - llama.cpp performance metrics

5. **Memory Integration**
   - Leverage existing SQLite memory for context
   - Share conversation history across components
   - Persistent session management

**Files to Create/Modify**:
- `core/ai/runtime/backend/agent-memory-rust/src/http_api.rs`
- `core/ai/runtime/backend/agent-memory-rust/src/inference.rs`
- `core/ai/runtime/backend/agent-memory-rust/src/config.rs`
- `core/ai/runtime/backend/agent-memory-rust/src/llama_integration.rs`
- `core/ai/runtime/backend/agent-memory-rust/Cargo.toml`

### Dependencies to Add

```toml
[dependencies]
# Existing dependencies...
axum = "0.7"
tokio = { version = "1.0", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tower = "0.4"
tower-http = { version = "0.5", features = ["cors", "trace"] }
tracing = "0.1"
tracing-subscriber = "0.3"
prometheus = "0.13"
jsonwebtoken = "9.0"
uuid = { version = "1.0", features = ["v4"] }
```

### Phase 2: Update K8sGPT Integration

**Objective**: Configure K8sGPT to use centralized Qwen endpoint

**Tasks**:
1. **K8sGPT Configuration**
   - Update backend configuration to use agent-memory-rust
   - Configure authentication tokens
   - Update model parameters

2. **Service Discovery**
   - Add Kubernetes service for agent-memory-rust
   - Configure network policies
   - Set up internal DNS resolution

3. **Migration Script**
   - Backup existing K8sGPT configuration
   - Update K8sGPT deployment
   - Verify connectivity

**Files to Create/Modify**:
- `core/gitops/k8sgpt/configmap-centralized-qwen.yaml`
- `core/gitops/k8sgpt/deployment-updated.yaml`
- `scripts/migrate-k8sgpt-to-central-qwen.sh`

### Phase 3: Update Flagger AI Integration

**Objective**: Integrate Flagger with centralized Qwen endpoint

**Tasks**:
1. **Update Flagger Skill**
   - Modify `qwen_k8sgpt_integration.py` to use agent-memory-rust
   - Update API endpoints and authentication
   - Maintain backward compatibility

2. **Configuration Updates**
   - Update Qwen configuration in Flagger skill
   - Add service discovery configuration
   - Update environment variables

3. **Testing & Validation**
   - Update test scripts to use centralized endpoint
   - Validate AI analysis functionality
   - Performance testing

**Files to Create/Modify**:
- `core/ai/skills/flagger-automation/scripts/qwen_k8sgpt_integration.py`
- `core/ai/skills/flagger-automation/SKILL.md`
- `overlay/flagger/qwen-centralized-config.yaml`

### Phase 4: Update Other Components

**Objective**: Extend centralized Qwen to other tools

**Tasks**:
1. **Flux Integration**
   - Update any AI-powered Flux features
   - Configure service endpoints
   - Add monitoring

2. **Argo CD Integration**
   - Update Argo CD AI features if present
   - Configure authentication
   - Test integration

3. **Future Component Support**
   - Create integration templates
   - Document integration patterns
   - Add automated discovery

### Phase 5: Cleanup & Optimization

**Objective**: Remove redundant Qwen deployments and optimize

**Tasks**:
1. **Remove Standalone Qwen Containers**
   - Decommission separate Qwen deployments
   - Clean up unused resources
   - Update documentation

2. **Performance Optimization**
   - Optimize agent-memory-rust for concurrent requests
   - Implement request queuing and throttling
   - Add caching for common requests

3. **Monitoring & Alerting**
   - Set up comprehensive monitoring
   - Configure alerts for Qwen service health
   - Add dashboards for observability

## Technical Specifications

### API Endpoints

#### Chat Completions
```
POST /api/v1/inference/chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "model": "qwen2.5-7b-instruct",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "max_tokens": 4096,
  "temperature": 0.7,
  "stream": false
}
```

#### Model Information
```
GET /api/v1/models
Authorization: Bearer <token>

{
  "models": [
    {
      "id": "qwen2.5-7b-instruct",
      "name": "Qwen 2.5 7B Instruct",
      "description": "Qwen language model for instruction following"
    }
  ]
}
```

#### Health Check
```
GET /api/v1/health
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### Authentication

- **Bearer Token Authentication**: JWT tokens for service-to-service communication
- **Service Account Tokens**: Kubernetes service account tokens
- **API Keys**: Static API keys for legacy components

### Configuration

```yaml
# agent-memory-rust config
qwen_api:
  enabled: true
  bind_address: "0.0.0.0"
  port: 8080
  auth:
    enabled: true
    jwt_secret: "${JWT_SECRET}"
    api_keys: ["${K8SGPT_API_KEY}", "${FLAGGER_API_KEY}"]
  
  rate_limiting:
    enabled: true
    requests_per_minute: 100
    burst_size: 20
  
  models:
    default: "qwen2.5-7b-instruct"
    available:
      - id: "qwen2.5-7b-instruct"
        name: "Qwen 2.5 7B Instruct"
        max_tokens: 4096
```

## Migration Strategy

### Rollout Plan

1. **Phase 1**: Deploy enhanced agent-memory-rust with API (no traffic yet)
2. **Phase 2**: Configure K8sGPT to use centralized endpoint (parallel operation)
3. **Phase 3**: Update Flagger integration
4. **Phase 4**: Update other components
5. **Phase 5**: Decommission standalone Qwen deployments

### Rollback Strategy

- Maintain backup configurations for all components
- Quick rollback scripts for each component
- Monitoring to detect issues immediately
- Gradual traffic shifting with feature flags

### Testing Strategy

1. **Unit Tests**: Test API endpoints and authentication
2. **Integration Tests**: Test component interactions
3. **Load Tests**: Test concurrent request handling
4. **Failover Tests**: Test fallback mechanisms

## Benefits

### Resource Efficiency
- **Memory Reduction**: ~70% reduction in Qwen memory usage
- **CPU Optimization**: Shared inference across components
- **Storage**: Single model storage instead of multiple copies

### Operational Benefits
- **Single Point of Monitoring**: Unified observability
- **Simplified Updates**: Update model once, affects all components
- **Consistent Behavior**: Same model version across all tools

### Cost Savings
- **Infrastructure**: Reduced compute requirements
- **Maintenance**: Single service to maintain
- **Licensing**: Single model license if applicable

## Risks & Mitigations

### Risks
1. **Single Point of Failure**: If agent-memory-rust fails, all AI functionality stops
2. **Performance Bottleneck**: High concurrent load could impact performance
3. **Security**: Centralized endpoint increases attack surface

### Mitigations
1. **High Availability**: Deploy agent-memory-rust with multiple replicas
2. **Load Balancing**: Implement request queuing and throttling
3. **Security**: Strong authentication, network policies, monitoring

## Timeline

| Phase | Duration | Start Date | End Date |
|-------|----------|------------|----------|
| Phase 1: agent-memory-rust Enhancement | 2 weeks | Week 1 | Week 2 |
| Phase 2: K8sGPT Migration | 1 week | Week 3 | Week 3 |
| Phase 3: Flagger Integration | 1 week | Week 4 | Week 4 |
| Phase 4: Other Components | 1 week | Week 5 | Week 5 |
| Phase 5: Cleanup & Optimization | 1 week | Week 6 | Week 6 |

**Total Duration**: 6 weeks

## Success Criteria

1. **Functional**: All components successfully use centralized Qwen
2. **Performance**: No degradation in response times (>95% of current performance)
3. **Reliability**: 99.9% uptime for Qwen API service
4. **Resource**: 50%+ reduction in Qwen-related resource usage
5. **Cost**: Measurable reduction in infrastructure costs

## Next Steps

1. **Review and Approve**: Get stakeholder approval for the plan
2. **Resource Allocation**: Assign developers to each phase
3. **Environment Setup**: Prepare development and testing environments
4. **Begin Implementation**: Start with Phase 1

---

**Document Version**: 1.0  
**Last Updated**: 2025-03-17  
**Owner**: Agentic Reconciliation Engine Team  
**Reviewers**: AI Architecture Team, Platform Engineering
