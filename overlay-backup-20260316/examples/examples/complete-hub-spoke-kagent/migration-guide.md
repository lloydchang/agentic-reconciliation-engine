# Migration Guide: From Basic CronJobs to Kagent

This guide provides a step-by-step approach for migrating from the basic CronJob-based agent orchestration to enterprise-grade kagent orchestration.

## Migration Overview

### Current State (Basic Implementation)
- Custom CronJobs for scheduled tasks
- Manual Job definitions for validation
- Basic agent-to-gateway communication
- Limited workflow orchestration
- Simple error handling

### Target State (Kagent Implementation)
- TaskSpawner for advanced scheduling
- Agent chains for complex workflows
- MCP integration for tool coordination
- Event-driven automation
- Sophisticated error handling and retry logic

## Phase 1: Assessment and Planning

### 1.1 Inventory Current Workflows
```bash
# List current CronJobs
kubectl get cronjobs -n control-plane

# Describe each CronJob to understand functionality
kubectl describe cronjob ai-infra-drift-analysis -n control-plane
kubectl describe cronjob ai-manifest-validation -n control-plane

# Check current resource usage
kubectl top pods -n control-plane -l app=ai-cronjob
```

### 1.2 Document Dependencies
```bash
# Check Flux dependencies
kubectl get kustomizations -n control-plane
kubectl describe kustomization ai-validation-kustomization -n control-plane

# Document current agent interactions
kubectl logs -l app=ai-cronjob -n control-plane --tail=100
```

### 1.3 Performance Baseline
```bash
# Collect current performance metrics
kubectl get events -n control-plane --sort-by='.lastTimestamp' | grep ai-cronjob

# Document current execution times
kubectl get jobs -n control-plane -l app=ai-cronjob -o wide
```

## Phase 2: Parallel Deployment

### 2.1 Deploy Kagent Alongside Current Implementation
```bash
# Deploy kagent core components
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/kagent-core/

# Wait for kagent to be ready
kubectl wait --for=condition=available deployment/kagent-controller -n kagent-system --timeout=300s

# Deploy kagent monitoring
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/monitoring/

# Deploy MCP registries
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/mcp-registry/
```

### 2.2 Create Parallel TaskSpawners
```bash
# Deploy kagent TaskSpawners alongside existing CronJobs
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/taskspawners/

# Verify both systems are running
kubectl get cronjobs -n control-plane
kubectl get taskspawners -n control-plane
```

### 2.3 Configure Comparison Monitoring
```bash
# Set up comparison dashboards
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/monitoring/kagent-monitoring.yaml

# Access Grafana to compare performance
kubectl port-forward svc/grafana 3000:3000 -n monitoring
```

## Phase 3: Gradual Migration

### 3.1 Migrate Non-Critical Workloads First

#### Step 1: Migrate Infrastructure Drift Analysis
```bash
# Disable original CronJob
kubectl patch cronjob ai-infra-drift-analysis -n control-plane -p '{"spec":{"suspend":true}}'

# Verify kagent TaskSpawner is working
kubectl get taskspawner infra-drift-analyzer -n control-plane -o wide
kubectl describe taskspawner infra-drift-analyzer -n control-plane

# Monitor execution
kubectl logs -l kagent.io/taskspawner=infra-drift-analyzer -n control-plane -f
```

#### Step 2: Compare Results
```bash
# Compare outputs from both systems
kubectl exec -it deployment/claude-code-gateway -- cat /reports/drift-analysis-$(date +%Y-%m-%d).json

# Check kagent reports
kubectl get pods -l kagent.io/chain=infra-drift-chain -n control-plane
kubectl logs -l kagent.io/chain=infra-drift-chain -n control-plane
```

#### Step 3: Validate Migration Success
```bash
# Verify task completion
kubectl get agentchains -n control-plane
kubectl describe agentchain infra-drift-chain -n control-plane

# Check for any errors
kubectl get events -n control-plane --sort-by='.lastTimestamp' | grep kagent
```

### 3.2 Migrate Critical Workloads

#### Step 1: Migrate Security Compliance
```bash
# Disable original validation CronJob
kubectl patch cronjob ai-manifest-validation -n control-plane -p '{"spec":{"suspend":true}}'

# Enable kagent security workflows
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/agent-workflows/gitops-pipelines.yaml

# Monitor execution
kubectl get agentworkflows -n control-plane
kubectl describe agentworkflow security-compliance-checker -n control-plane
```

#### Step 2: Migrate GitOps Validation
```bash
# Update Flux kustomization to use kagent
kubectl patch kustomization ai-validation-kustomization -n control-plane --type='merge' -p='{"spec":{"dependsOn":["kagent-core"]}}'

# Verify GitOps triggers are working
kubectl get agentworkflows -n control-plane
kubectl describe agentworkflow gitops-validation-pipeline -n control-plane
```

## Phase 4: Complete Migration

### 4.1 Remove Legacy Components
```bash
# Remove original CronJobs
kubectl delete cronjob ai-infra-drift-analysis -n control-plane
kubectl delete cronjob ai-manifest-validation -n control-plane

# Remove original AI Gateway (if using kagent's MCP integration)
kubectl delete deployment claude-code-gateway -n control-plane
kubectl delete service claude-code-gateway -n control-plane

# Remove old PVCs
kubectl delete pvc ai-reports-pvc -n control-plane
kubectl delete pvc ai-validation-pvc -n control-plane
```

### 4.2 Update Kustomization
```bash
# Update main kustomization to use kagent
kubectl patch kustomization complete-hub-spoke-with-ai -n flux-system --type='merge' -p='{"resources":["../../overlay/examples/complete-hub-spoke-kagent/"]}'
```

### 4.3 Optimize Kagent Configuration
```bash
# Tune resource allocation
kubectl patch taskspawner infra-drift-analyzer -n control-plane --type='merge' -p='{"spec":{"resources":{"requests":{"memory":"1Gi","cpu":"1000m"}}}}'

# Optimize scheduling
kubectl patch taskspawner infra-drift-analyzer -n control-plane --type='merge' -p='{"spec":{"concurrency":3}}'

# Configure retry policies
kubectl patch taskspawner infra-drift-analyzer -n control-plane --type='merge' -p='{"spec":{"retryPolicy":{"maxRetries":5,"backoffDuration":"60s"}}}'
```

## Migration Validation Checklist

### Pre-Migration Checklist
- [ ] Document all current CronJobs and their schedules
- [ ] Record current performance metrics
- [ ] Identify all dependencies and integrations
- [ ] Create backup of current configuration
- [ ] Prepare rollback plan

### During Migration Checklist
- [ ] Kagent controller is running and healthy
- [ ] MCP registries are populated and accessible
- [ ] TaskSpawners are created and configured
- [ ] Agent workflows are defined and triggered
- [ ] Monitoring and alerting are configured
- [ ] Both systems are running in parallel

### Post-Migration Checklist
- [ ] All legacy CronJobs are removed
- [ ] Kagent workflows are executing successfully
- [ ] Performance meets or exceeds baseline
- [ ] Error rates are within acceptable limits
- [ ] Monitoring dashboards are updated
- [ ] Documentation is updated

## Troubleshooting Migration Issues

### Common Issues and Solutions

#### Issue 1: TaskSpawner Not Creating Tasks
```bash
# Check controller logs
kubectl logs deployment/kagent-controller -n kagent-system

# Verify CRD installation
kubectl get crd | grep kagent.io

# Check RBAC permissions
kubectl auth can-i create taskspawners --as=system:serviceaccount:kagent-system:kagent-controller
```

#### Issue 2: Agent Chain Failing
```bash
# Check agent chain status
kubectl get agentchains -n control-plane
kubectl describe agentchain infra-drift-chain -n control-plane

# Check individual agent logs
kubectl get pods -l kagent.io/chain=infra-drift-chain -n control-plane
kubectl logs -l kagent.io/chain=infra-drift-chain -n control-plane
```

#### Issue 3: MCP Server Connection Issues
```bash
# Verify MCP server status
kubectl get mcpservers -n control-plane
kubectl describe mcpserver gitops-tools -n control-plane

# Test MCP server connectivity
kubectl port-forward service/gitops-tools 8080:8080 -n control-plane
curl http://localhost:8080/healthz
```

#### Issue 4: Performance Degradation
```bash
# Check resource usage
kubectl top pods -n control-plane -l app=kagent

# Analyze metrics
kubectl port-forward svc/kagent-metrics 8080:8080 -n control-plane
curl http://localhost:8080/metrics

# Adjust resource limits
kubectl patch taskspawner infra-drift-analyzer -n control-plane --type='merge' -p='{"spec":{"resources":{"limits":{"memory":"4Gi","cpu":"4000m"}}}}'
```

## Rollback Plan

### Quick Rollback (Emergency)
```bash
# Restore original CronJobs
kubectl apply -f overlay/examples/complete-hub-spoke/ai-cronjobs/

# Disable kagent
kubectl patch deployment kagent-controller -n kagent-system -p '{"spec":{"replicas":0}}'

# Update kustomization
kubectl patch kustomization complete-hub-spoke-with-ai -n flux-system --type='json' -p='[{"op":"remove","path":"/resources/4"}]'
```

### Complete Rollback
```bash
# Remove all kagent components
kubectl delete -f overlay/examples/complete-hub-spoke-kagent/

# Restore original implementation
kubectl apply -f overlay/examples/complete-hub-spoke/

# Verify restoration
kubectl get cronjobs -n control-plane
kubectl get pods -n control-plane -l app=ai-cronjob
```

## Performance Comparison

### Expected Improvements
- **Execution Time**: 20-30% faster due to optimized agent chaining
- **Resource Efficiency**: 15-25% better resource utilization
- **Reliability**: 50% reduction in failure rates with retry logic
- **Scalability**: Horizontal scaling capabilities
- **Observability**: Enhanced monitoring and tracing

### Metrics to Track
- Task execution duration
- Agent chain completion rates
- Resource utilization patterns
- Error rates and types
- MCP server response times

## Post-Migration Optimization

### 1. Fine-Tune Agent Chains
```bash
# Optimize agent dependencies
kubectl patch agentchain infra-drift-chain -n control-plane --type='merge' -p='{"spec":{"agents":[{"name":"validation","dependsOn":["drift-detection"],"condition":"drift-detected"}]}}'

# Configure parallel execution
kubectl patch agentchain multi-cluster-deployment -n control-plane --type='merge' -p='{"spec":{"parallelism":2}}'
```

### 2. Optimize Resource Usage
```bash
# Implement auto-scaling
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: kagent-controller-hpa
  namespace: kagent-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: kagent-controller
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF
```

### 3. Enhance Monitoring
```bash
# Add custom metrics
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/monitoring/custom-metrics.yaml

# Configure alerting
kubectl apply -f overlay/examples/complete-hub-spoke-kagent/monitoring/alert-rules.yaml
```

## Training and Documentation

### Operator Training
1. **Kagent Concepts**: TaskSpawner, Agent Chains, MCP Integration
2. **Monitoring**: Dashboards, alerting, troubleshooting
3. **Operations**: Scaling, updates, maintenance
4. **Security**: RBAC, network policies, audit logging

### Documentation Updates
- Update runbooks for kagent operations
- Document new monitoring procedures
- Create troubleshooting guides
- Update architecture diagrams

## Support and Maintenance

### Solo.io Enterprise Support
- **24/7 Support**: Production assistance
- **Expert Services**: Architecture and optimization
- **Training Programs**: Operator and developer training
- **SLA Guarantees**: Uptime and performance commitments

### Community Support
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides and tutorials
- **Community Forums**: Peer support and knowledge sharing
- **Regular Releases**: Feature updates and security patches

This migration guide ensures a smooth transition from basic CronJob orchestration to enterprise-grade kagent orchestration while maintaining system reliability and performance.
