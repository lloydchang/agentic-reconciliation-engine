# AI System Debugging and Monitoring Guide

## Overview

This document provides comprehensive documentation for the AI agents system debugging and monitoring capabilities implemented across the GitOps infrastructure. The system includes automated debugging skills, real-time metrics collection, distributed system monitoring, and comprehensive deployment automation.

## Architecture Components

### 1. AI System Debugger Skill

**Location**: [core/ai/skills/debug/SKILL.md](core/ai/skills/debug/SKILL.md)
**Purpose**: Comprehensive debugging skill for AI agents, Temporal workflows, and Kubernetes infrastructure

#### Key Capabilities

- **Component Debugging**:
  - AI Agents: Execution logs, performance metrics, failure patterns
  - Temporal Workflows: Execution history, timeouts, activity failures
  - Kubernetes Infrastructure: Pod health, resource utilization, network connectivity
  - Integration Points: Cross-service communication validation

- **Issue Types Supported**:
  - Performance: Slow execution, high latency, resource bottlenecks
  - Errors: Agent failures, workflow crashes, API errors
  - Timeouts: Workflow timeouts, agent inference delays
  - Connectivity: Network issues, service discovery problems
  - Resource: Memory/CPU exhaustion, storage issues
  - Behavior: Unexpected responses, hallucination detection

#### Usage Examples

```bash
# Basic agent debugging
python main.py debug \
  --target-component agents \
  --issue-type errors \
  --time-range 1h \
  --verbose

# Infrastructure health check
python main.py debug \
  --target-component infrastructure \
  --issue-type resource \
  --time-range 30m \
  --auto-fix

# Full system analysis
python main.py debug \
  --target-component all \
  --issue-type performance \
  --time-range 2h \
  --namespace temporal \
  --verbose \
  --auto-fix
```

#### Auto-Fix Capabilities

When enabled, the skill can automatically:
- Restart failing pods
- Clear stuck workflows
- Adjust resource limits
- Restart unhealthy agents
- Clear temporary cache issues

#### Structured Output Schema

The skill produces structured debugging reports with:
- **Findings**: Detailed analysis of discovered issues
- **Evidence**: Log snippets, metrics, supporting data
- **Recommendations**: Actionable remediation steps
- **Metrics**: Summary statistics and health scores
- **Next Steps**: Follow-up actions and monitoring

### 2. Go Metrics Collection System

**Location**: `ai-core/ai/runtime/backend/monitoring/metrics.go`
**Purpose**: Comprehensive metrics collection and aggregation for AI agents and workflows

#### Core Components

##### MetricsCollector Struct
```go
type MetricsCollector struct {
    metrics     map[string]*Metric
    alerts      []*Alert
    mu          sync.RWMutex
    alertChan   chan *Alert
    stopChan    chan struct{}
    collectors  []MetricCollector
}
```

##### Supported Metric Types
- **Counter**: Monotonically increasing values (e.g., requests served)
- **Gauge**: Point-in-time values (e.g., current memory usage)
- **Histogram**: Distribution of values (e.g., request latency)
- **Summary**: Similar to histogram with quantiles

##### Alert System
- **Severity Levels**: Critical, Warning, Info
- **Auto-acknowledgment**: Tracks alert acknowledgment and timing
- **Threshold-based**: Configurable thresholds for automatic alerts

#### Specialized Collectors

##### WorkflowMetricsCollector
Tracks Temporal workflow execution metrics:
- Active workflows count
- Status distribution (running, completed, failed)
- Execution duration statistics
- Error rates and retry counts

##### AgentMetricsCollector
Monitors agent performance:
- Total executions per agent
- Success/failure rates
- Average response times
- Resource utilization
- Error rate tracking

##### SystemMetricsCollector
System-level metrics:
- Application uptime
- Memory usage statistics
- Goroutine counts
- System health indicators

#### Key Methods

```go
// Record workflow execution
func (mc *MetricsCollector) RecordWorkflowExecution(execution *WorkflowExecution)

// Record agent performance
func (mc *MetricsCollector) RecordAgentExecution(agentName string, success bool, score float64, duration time.Duration)

// Retrieve metrics
func (mc *MetricsCollector) GetMetrics() map[string]*Metric
func (mc *MetricsCollector) GetAlerts() []*Alert
```

#### Temporal Integration Activities

The system includes Temporal workflow activities for metrics integration:

```go
// Record workflow metrics
func RecordWorkflowMetricsActivity(ctx context.Context, workflowID, workflowType, status string, startTime time.Time, agentResults []types.AgentResult) error

// Record agent execution metrics
func RecordAgentMetricsActivity(ctx context.Context, agentName string, success bool, score float64, duration time.Duration) error

// Retrieve current metrics
func GetMetricsActivity(ctx context.Context) (map[string]interface{}, error)
```

### 3. AI Agents Ecosystem Deployment

**Location**: `core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh`
**Purpose**: Complete deployment automation for the AI agents infrastructure

#### Deployment Components

##### Infrastructure Setup
- **Namespace Creation**: `ai-infrastructure` namespace
- **AI Inference Backend**: Integration with Llama.cpp agents
- **Kubernetes Configuration**: Context validation and setup

##### Agent Deployment
- **Memory Agent (Rust)**: Persistent storage, database initialization
- **Resource Configuration**: CPU/memory limits and requests
- **Health Checks**: Readiness and liveness probes

##### Gateway and Orchestration
- **AI Inference Gateway**: Unified API for skill inference calls
- **Temporal Workflows**: Distributed orchestration engine
- **Operational Skills**: 64+ automated operational capabilities

##### Dashboard and Monitoring
- **Agent Dashboard**: Real-time monitoring interface
- **Dashboard API**: RESTful metrics and status endpoints
- **Ingress Configuration**: External access routing

##### Networking and Access
- **Service Mesh**: Internal service communication
- **Ingress Controllers**: NGINX-based external access
- **Load Balancing**: Traffic distribution and health checking

#### Key Deployment Features

- **Multi-language Support**: Go, Rust, Python agents
- **Scalable Architecture**: Horizontal pod autoscaling
- **Persistent Storage**: Database and model persistence
- **Security**: RBAC, network policies, secrets management

#### Access URLs (Post-Deployment)

```
🌐 Agent Dashboard: http://dashboard.local
🔄 Temporal Workflows: http://temporal.local
📊 Metrics API: http://dashboard.local/api/cluster-status
🤖 Agent API: http://dashboard.local/api/core/ai/runtime/status
```

### 4. Debugging Methodology and Knowledge Base

#### Systematic Debugging Approach

##### 1. Information Gathering
- **Metrics Collection**: Real-time performance data
- **Log Analysis**: Structured logging across components
- **Temporal History**: Workflow execution traces
- **Resource Monitoring**: CPU, memory, network utilization

##### 2. Pattern Recognition
- **Failure Patterns**: Common error signatures
- **Anomaly Detection**: Statistical outliers in behavior
- **Correlation Analysis**: Cross-component issue linking
- **Trend Analysis**: Time-series pattern identification

##### 3. Root Cause Analysis
- **Call Chain Tracing**: End-to-end request flow analysis
- **Dependency Mapping**: Service interaction graphs
- **Configuration Validation**: Environment and settings verification
- **Resource Bottleneck Identification**: Capacity and performance limits

##### 4. Remediation and Prevention
- **Automated Fixes**: Self-healing capabilities
- **Manual Procedures**: Step-by-step resolution guides
- **Prevention Strategies**: Proactive monitoring and alerts
- **Documentation Updates**: Knowledge base enhancement

#### Quick Debug Commands

```bash
# Fast agent debugging
./quick_debug.sh agents errors true

# Full system analysis
python main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Infrastructure health check
kubectl get pods -n temporal -l app=temporal-worker
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep ERROR
```

#### Monitoring Endpoints

- **Metrics API**: `http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/metrics`
- **Alerts API**: `http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/alerts`
- **Health Checks**: `http://temporal-worker.temporal.svc.cluster.local:8080/health`
- **Audit Logs**: `http://temporal-worker.temporal.svc.cluster.local:8080/audit/events`

#### Common Issue Patterns

- **Agent Failures**: Pod restarts, skill execution errors, resource exhaustion
- **Workflow Timeouts**: Long-running activities, stuck workflows, queue issues
- **Infrastructure Issues**: Node failures, storage issues, network problems
- **Performance Bottlenecks**: High CPU/memory usage, slow inference, bottlenecks

## Integration and Data Flow

### Architecture Overview

```
[AI Agents] → [Metrics Endpoints] → [Aggregation Service] → [Dashboard API] → [Frontend UI]
      ↑              ↑                        ↑                      ↑
[Prometheus]  [Temporal Monitor]    [K8s Monitor]        [Real-time Updates]
```

### Component Integration Points

#### Temporal Workflows
- **Workflow History**: Execution tracking and failure analysis
- **Activity Logs**: Individual step monitoring and debugging
- **Task Queues**: Load balancing and processing rate monitoring
- **Worker Health**: Distributed agent status and capacity

#### Kubernetes Integration
- **Pod Status**: Container health and lifecycle monitoring
- **Resource Metrics**: CPU, memory, storage utilization
- **Service Discovery**: Dynamic endpoint registration
- **Network Policies**: Communication security and isolation

#### External Systems
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Advanced visualization and dashboards
- **Logging Systems**: Centralized log aggregation
- **Alert Managers**: Notification and escalation systems

## Security and Access Control

### Authentication and Authorization
- **API Security**: Token-based authentication for metrics endpoints
- **RBAC Integration**: Role-based access to monitoring data
- **Service Accounts**: Automated system-to-system authentication

### Network Security
- **Internal Communication**: Encrypted service mesh traffic
- **External Access**: TLS termination and certificate management
- **Network Policies**: Kubernetes network segmentation

### Data Protection
- **Metrics Encryption**: Sensitive data protection in transit
- **Access Logging**: Comprehensive audit trails
- **Data Retention**: Configurable metrics and log retention policies

## Performance and Scalability

### Monitoring Overhead
- **Resource Impact**: Minimal performance overhead (<1% CPU)
- **Memory Usage**: Efficient in-memory aggregation
- **Network Traffic**: Optimized metric transmission

### Scalability Features
- **Horizontal Scaling**: Distributed metrics collection
- **Data Partitioning**: Namespace and component isolation
- **Caching Strategy**: Frequently accessed data caching
- **Async Processing**: Non-blocking metrics collection

### Performance Requirements
- **Update Frequency**: 10-30 second intervals
- **Response Time**: <200ms for API calls
- **Data Retention**: 24 hours detailed, 30 days aggregated
- **Concurrent Users**: Support for multiple dashboard users

## Troubleshooting and Maintenance

### Common Issues and Solutions

#### Metrics Collection Problems
```
Symptom: Missing agent metrics
Solution: Check Prometheus configuration and service discovery
```

#### Dashboard Data Issues
```
Symptom: Stale or incorrect data
Solution: Verify aggregation service connectivity and cache invalidation
```

#### Performance Degradation
```
Symptom: Slow dashboard response
Solution: Check database performance and optimize queries
```

### Maintenance Procedures

#### Regular Tasks
- **Log Rotation**: Automated log file management
- **Metrics Cleanup**: Historical data archiving
- **Certificate Renewal**: SSL certificate maintenance
- **Dependency Updates**: Keep monitoring stack current

#### Backup and Recovery
- **Configuration Backup**: Monitoring configuration snapshots
- **Metrics Archival**: Long-term data preservation
- **Disaster Recovery**: Failover procedures and testing

## Future Enhancements

### Planned Features
- **Machine Learning Integration**: Anomaly detection using ML models
- **Predictive Analytics**: Failure prediction and prevention
- **Advanced Visualization**: 3D system topology views
- **Automated Remediation**: AI-driven problem resolution

### Research Areas
- **Distributed Tracing**: End-to-end request tracing
- **Performance Profiling**: Detailed bottleneck analysis
- **Cost Optimization**: Resource usage optimization recommendations
- **Security Monitoring**: Advanced threat detection

---

## Quick Reference

### Key Files and Locations
- **Skill Definition**: [core/ai/skills/debug/SKILL.md](core/ai/skills/debug/SKILL.md)
- **Metrics System**: `ai-core/ai/runtime/backend/monitoring/metrics.go`
- **Deployment Script**: `core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh`
- **Monitoring Plan**: [docs/REAL_MONITORING_IMPLEMENTATION.md](docs/REAL_MONITORING_IMPLEMENTATION.md)

### Important Endpoints
- **Dashboard**: `http://dashboard.local`
- **Temporal UI**: `http://temporal.local`
- **Metrics API**: `/api/cluster-status`
- **Agent API**: `/api/core/ai/runtime/status`

### Emergency Contacts
- **System Alerts**: Check dashboard for active alerts
- **Log Analysis**: Use debugging skill for comprehensive analysis
- **Manual Intervention**: Follow documented troubleshooting procedures

---

*This documentation covers the complete AI system debugging and monitoring ecosystem. For specific implementation details, refer to the individual component documentation and source code.*
