# Complete Hub-Spoke AI Integration with Kagent

This example demonstrates enterprise-grade agent orchestration using **kagent** - a cloud-native framework for orchestrating autonomous AI agents in Kubernetes. This represents an evolution from the basic CronJob-based approach to sophisticated agent-driven infrastructure automation.

## Architecture Overview

### Kagent-Enhanced Architecture

```
[Git Repository] ── Flux ──> [Infrastructure Changes]
       │                        │
       │                        ▼
       │              [Kagent TaskSpawner Cluster]
       │                        │
       ▼                        ▼
[Agent Chains] ◄────────────► [MCP Servers] ◄────────────► [AI Agents]
       │                        │                        │
       │                        ▼                        ▼
[Reports Storage] ◄────────────► [Tool Registry] ◄────────────► [Audit Logs]
```

### Key Components

- **TaskSpawner**: Advanced scheduling and task management
- **Agent Chains**: Complex multi-agent workflows with dependencies
- **MCP Integration**: Model Context Protocol for tool coordination
- **Kubernetes-Native**: Designed specifically for K8s environments

## Evolution from Basic Implementation

### Before (Basic CronJobs)
```yaml
# Simple scheduled tasks
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ai-infra-drift-analysis
spec:
  schedule: "0 */4 * * *"
  # Basic job template...
```

### After (Kagent TaskSpawner)
```yaml
# Sophisticated agent orchestration
apiVersion: kagent.io/v1alpha1
kind: TaskSpawner
metadata:
  name: infra-drift-analyzer
spec:
  schedule: "0 */4 * * *"
  agentChain:
  - name: drift-analysis
    target: claude-code
  - name: validation
    target: kubeconform
    dependsOn: ["drift-analysis"]
  - name: remediation
    target: kubectl-apply
    dependsOn: ["validation"]
    condition: "policy-violation-detected"
```

## Kagent Capabilities

### 1. TaskSpawner
- **Advanced Scheduling**: Beyond simple CronJob patterns
- **Dynamic Task Management**: Runtime task creation and modification
- **Resource Optimization**: Intelligent resource allocation
- **Error Handling**: Built-in retry logic and failure recovery

### 2. Agent Chaining
- **Complex Workflows**: Multi-step agent pipelines
- **Conditional Execution**: Branch based on previous results
- **Dependency Management**: Explicit agent dependencies
- **Result Passing**: Seamless data flow between agents

### 3. MCP Integration
- **Standardized Protocol**: Model Context Protocol for tool communication
- **Tool Registry**: Centralized tool management
- **Dynamic Tool Loading**: Runtime tool discovery
- **Version Management**: Tool versioning and compatibility

### 4. Kubernetes-Native Design
- **Resource Management**: Proper K8s resource handling
- **Scaling Support**: Horizontal scaling capabilities
- **Monitoring Integration**: Prometheus metrics and health checks
- **Security**: RBAC and network policy integration

## Deployment Options

### Option 1: Kagent Only (Recommended)
```bash
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/
```
- Full kagent orchestration
- Advanced agent workflows
- MCP integration enabled

### Option 2: Hybrid Migration
```bash
# Deploy alongside existing implementation
kubectl apply -f overlay/examples/complete-hub-spoke/          # Basic
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/   # Enhanced
```
- Gradual migration path
- Parallel operation
- Feature comparison

### Option 3: Complete Replacement
```bash
# Migrate from basic to kagent
kubectl delete -f overlay/examples/complete-hub-spoke/
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/
```
- Full replacement
- Enterprise features
- Simplified architecture

## Agent Workflow Examples

### Infrastructure Drift Analysis Chain
```yaml
apiVersion: kagent.io/v1alpha1
kind: TaskSpawner
metadata:
  name: infra-drift-chain
spec:
  schedule: "0 */4 * * *"
  agentChain:
  - name: drift-detection
    target: claude-code
    config:
      task: "detect-infrastructure-drift"
      scope: "all-clusters"
  - name: impact-analysis
    target: claude-code
    dependsOn: ["drift-detection"]
    config:
      task: "analyze-drift-impact"
      input: "${drift-detection.results}"
  - name: validation
    target: kubeconform
    dependsOn: ["impact-analysis"]
    config:
      manifests: "${impact-analysis.affected-manifests}"
  - name: remediation
    target: kubectl-apply
    dependsOn: ["validation"]
    condition: "validation.has-fixable-issues"
    config:
      manifests: "${validation.fixable-manifests}"
```

### GitOps Validation Pipeline
```yaml
apiVersion: kagent.io/v1alpha1
kind: AgentWorkflow
metadata:
  name: gitops-validation-pipeline
spec:
  triggers:
  - type: git-commit
    repository: infrastructure-repo
    paths: ["core/resources/**"]
  - type: schedule
    cron: "0 */6 * * *"
  agents:
  - name: change-detector
    task: analyze-git-changes
    config:
      focus: "kubernetes-manifests"
  - name: security-validator
    task: validate-security-policies
    dependsOn: ["change-detector"]
    config:
      policies: ["rbac", "network-policies", "secrets"]
  - name: compliance-checker
    task: check-compliance
    dependsOn: ["security-validator"]
    config:
      standards: ["cis-benchmark", "company-policies"]
  - name: auto-remediation
    task: apply-fixes
    dependsOn: ["compliance-checker"]
    condition: "compliance-checker.has-fixable-issues"
    config:
      approval: "automatic-for-low-risk"
```

### Multi-Cloud Health Monitoring
```yaml
apiVersion: kagent.io/v1alpha1
kind: TaskSpawner
metadata:
  name: multi-cloud-health-monitor
spec:
  schedule: "*/15 * * * *"  # Every 15 minutes
  agentChain:
  - name: aws-health-check
    target: aws-health-checker
    config:
      services: ["eks", "rds", "ec2"]
  - name: azure-health-check
    target: azure-health-checker
    config:
      services: ["aks", "sql-database", "vm"]
  - name: gcp-health-check
    target: gcp-health-checker
    config:
      services: ["gke", "cloud-sql", "compute"]
  - name: health-aggregator
    target: health-aggregator
    dependsOn: ["aws-health-check", "azure-health-check", "gcp-health-check"]
    config:
      alert-threshold: "critical"
      notification: ["slack", "pagerduty"]
```

## MCP Server Integration

### Tool Registry Configuration
```yaml
apiVersion: kagent.io/v1alpha1
kind: MCPRegistry
metadata:
  name: infrastructure-tools
spec:
  tools:
  - name: kubectl
    version: "v1.28.0"
    capabilities: ["apply", "get", "describe", "logs"]
    security: "rbac-restricted"
  - name: helm
    version: "v3.14.0"
    capabilities: ["install", "upgrade", "rollback", "test"]
    security: "namespace-scoped"
  - name: terraform
    version: "v1.6.0"
    capabilities: ["plan", "apply", "destroy", "validate"]
    security: "read-only-by-default"
  - name: flux-cli
    version: "v2.2.0"
    capabilities: ["reconcile", "suspend", "resume", "status"]
    security: "cluster-admin"
```

### Custom MCP Server
```yaml
apiVersion: kagent.io/v1alpha1
kind: MCPServer
metadata:
  name: gitops-tools
spec:
  image: "gitops-tools-mcp:latest"
  tools:
  - name: manifest-validator
    description: "Validate Kubernetes manifests"
    endpoint: "/validate"
  - name: drift-analyzer
    description: "Analyze infrastructure drift"
    endpoint: "/analyze-drift"
  - name: compliance-checker
    description: "Check compliance against policies"
    endpoint: "/check-compliance"
  resources:
    requests:
      memory: "256Mi"
      cpu: "200m"
    limits:
      memory: "512Mi"
      cpu: "500m"
```

## Migration Guide

### Phase 1: Assessment and Planning
1. **Evaluate Current Workflows**
   - Identify existing CronJobs
   - Map agent dependencies
   - Document current limitations

2. **Design Kagent Architecture**
   - Define agent chains
   - Plan MCP integration
   - Design migration strategy

### Phase 2: Parallel Deployment
1. **Deploy Kagent Alongside**
   ```bash
   # Keep existing implementation
   kubectl apply -f overlay/examples/complete-hub-spoke/
   
   # Add kagent for comparison
   kubectl apply -f overlay/examples/complete-hub-spoke-kagent/
   ```

2. **Compare Performance**
   - Monitor execution times
   - Compare resource usage
   - Evaluate feature completeness

### Phase 3: Gradual Migration
1. **Migrate Simple Workflows**
   - Start with non-critical tasks
   - Validate agent chains
   - Test error handling

2. **Migrate Critical Workflows**
   - Move production workloads
   - Implement monitoring
   - Train operations team

### Phase 4: Complete Migration
1. **Decommission Legacy**
   ```bash
   # Remove basic implementation
   kubectl delete -f overlay/examples/complete-hub-spoke/
   ```

2. **Optimize Kagent**
   - Fine-tune agent chains
   - Optimize resource usage
   - Scale horizontally

## Monitoring and Observability

### Kagent Metrics
```yaml
# Prometheus monitoring
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kagent-metrics
spec:
  selector:
    matchLabels:
      app: kagent
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Key Metrics
- **TaskSpawner**: Task execution count, success/failure rates, execution times
- **Agent Chains**: Chain completion rates, bottleneck identification, dependency delays
- **MCP Servers**: Tool usage statistics, response times, error rates
- **Resource Usage**: CPU/memory consumption, scaling events

### Logging Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kagent-logging
data:
  log-level: "info"
  log-format: "json"
  audit-enabled: "true"
  trace-enabled: "true"
```

## Security Considerations

### RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kagent-operator
rules:
- apiGroups: ["kagent.io"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kagent-netpol
spec:
  podSelector:
    matchLabels:
      app: kagent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: control-plane
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS to external APIs
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

## Troubleshooting

### Common Issues

1. **TaskSpawner Not Creating Tasks**
   ```bash
   kubectl get taskspawners
   kubectl describe taskspawner infra-drift-analyzer
   kubectl logs deployment/kagent-controller
   ```

2. **Agent Chain Failing**
   ```bash
   kubectl get agentchains
   kubectl describe agentchain infra-drift-chain
   kubectl get pods -l kagent.io/chain=infra-drift-chain
   ```

3. **MCP Server Connection Issues**
   ```bash
   kubectl get mcpservers
   kubectl describe mcpserver gitops-tools
   kubectl port-forward service/gitops-tools 8080:8080
   ```

### Debug Commands
```bash
# Check kagent controller status
kubectl get deployment kagent-controller -n kagent-system
kubectl logs deployment/kagent-controller -n kagent-system

# List all kagent resources
kubectl api-resources --api-group=kagent.io
kubectl get taskspawners,agentchains,mcpservers

# Check specific workflow
kubectl get agentchain gitops-validation-pipeline -o yaml
kubectl describe agentchain gitops-validation-pipeline
```

## Performance Optimization

### Resource Tuning
```yaml
apiVersion: kagent.io/v1alpha1
kind: TaskSpawner
metadata:
  name: optimized-taskspawner
spec:
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "2000m"
  concurrency: 5
  timeout: "30m"
  retryPolicy:
    maxRetries: 3
    backoffDuration: "30s"
```

### Scaling Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kagent-controller
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: controller
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "4000m"
```

## Enterprise Support

### Solo.io Production Support
- **Enterprise Features**: Advanced monitoring, scaling, security
- **Expert Assistance**: Professional services for implementation
- **SLA Guarantees**: Production uptime and performance
- **Training**: Operator and developer training programs

### Support Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kagent-support
data:
  support-enabled: "true"
  metrics-endpoint: "https://metrics.solo.io"
  alert-endpoint: "https://alerts.solo.io"
  support-key: "${SUPPORT_API_KEY}"
```

This kagent-enhanced example provides enterprise-grade agent orchestration capabilities while maintaining the GitOps principles and Kubernetes-native design patterns of the control plane.
