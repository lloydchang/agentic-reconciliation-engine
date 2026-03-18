# K8sGPT Consolidation Deployment and Validation Guide

## 🚀 Next Steps: Deploy and Validate

This guide provides step-by-step instructions for deploying the consolidated K8sGPT to test clusters and validating component integration.

## 📋 Prerequisites Checklist

### Cluster Readiness
- [ ] Kubernetes cluster accessible (kubectl configured)
- [ ] Agent-memory service deployed and running
- [ ] Required namespaces exist or can be created
- [ ] Sufficient cluster resources (4Gi memory, 2000m CPU available)
- [ ] Network policies allow inter-namespace communication

### Tool Requirements
- [ ] kubectl installed and configured
- [ ] Access to repository with consolidated files
- [ ] Migration script executable: `chmod +x scripts/migrate-to-consolidated-k8sgpt.sh`

## 🎯 Phase 1: Deploy to Test Clusters

### Step 1.1: Prepare Secrets
```bash
# Copy and customize secrets template
cp core/gitops/consolidated/k8sgpt-secrets-template.yaml core/gitops/consolidated/k8sgpt-secrets.yaml

# Edit with your actual values
vim core/gitops/consolidated/k8sgpt-secrets.yaml
```

**Critical secrets to configure:**
- `agent-memory-jwt-secret`: JWT secret for agent-memory service
- `webhook-secret`: Webhook authentication token
- `prometheus-token`: Metrics access token
- Component-specific tokens for integrations

### Step 1.2: Create Namespace
```bash
# Create k8sgpt-system namespace
kubectl create namespace k8sgpt-system \
  --label=app.kubernetes.io/name=k8sgpt \
  --label=app.kubernetes.io/component=namespace \
  --label=app.kubernetes.io/part-of=gitops-infra-control-plane \
  --label=name=k8sgpt-system
```

### Step 1.3: Deploy Consolidated K8sGPT
```bash
# Apply unified configuration
kubectl apply -f core/gitops/consolidated/k8sgpt-unified-config.yaml

# Apply secrets (customize first!)
kubectl apply -f core/gitops/consolidated/k8sgpt-secrets.yaml

# Apply main deployment
kubectl apply -f core/gitops/consolidated/k8sgpt-unified-deployment.yaml

# Apply GitOps applications (optional)
kubectl apply -f core/gitops/consolidated/k8sgpt-gitops-apps.yaml
```

### Step 1.4: Verify Deployment
```bash
# Check deployment status
kubectl get deployment k8sgpt -n k8sgpt-system

# Wait for rollout
kubectl rollout status deployment/k8sgpt -n k8sgpt-system

# Check pod status
kubectl get pods -n k8sgpt-system -l app.kubernetes.io/name=k8sgpt

# Check service
kubectl get service k8sgpt -n k8sgpt-system
```

### Step 1.5: Test Service Health
```bash
# Port-forward to local testing
kubectl port-forward service/k8sgpt 8080:8080 -n k8sgpt-system &
PF_PID=$!

# Wait for deployment to be ready
sleep 30

# Test health endpoint
curl -f http://localhost:8080/healthz || echo "❌ Health check failed"

# Test metrics endpoint
curl -f http://localhost:8080/metrics || echo "❌ Metrics check failed"

# Test analysis endpoint
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","resources":["deployments"]}' || echo "❌ Analysis check failed"

# Clean up port-forward
kill $PF_PID 2>/dev/null
```

## 🔧 Phase 2: Component Integration Validation

### Step 2.1: Argo Workflows Integration
```bash
# Test from Argo Workflows namespace
kubectl run test-k8sgpt-argo --image=curlimages/curl --rm -i --restart=Never \
  -- curl -f http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz \
  -n argo-workflows

# Update Argo Workflows configuration
kubectl patch configmap argo-workflows-config -n argo-workflows \
  --patch '{"data":{"K8SGPT_ENDPOINT":"http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"}}'
```

### Step 2.2: Argo Rollouts Integration
```bash
# Test from Argo Rollouts namespace
kubectl run test-k8sgpt-rollouts --image=curlimages/curl --rm -i --restart=Never \
  -- curl -f http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz \
  -n argo-rollouts

# Update Rollouts analysis templates
kubectl patch configmap argo-rollouts-config -n argo-rollouts \
  --patch '{"data":{"K8SGPT_SERVICE_URL":"http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"}}'
```

### Step 2.3: Flux CD Integration
```bash
# Test from Flux namespace
kubectl run test-k8sgpt-flux --image=curlimages/curl --rm -i --restart=Never \
  -- curl -f http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz \
  -n flux-system

# Update Flux Kustomizations
kubectl patch kustomization apps -n flux-system \
  --patch '{"spec":{"postBuild":{"substitute":{"K8SGPT_ENDPOINT":"http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"}}}'
```

### Step 2.4: Argo Events Integration
```bash
# Test from Argo Events namespace
kubectl run test-k8sgpt-events --image=curlimages/curl --rm -i --restart=Never \
  -- curl -f http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz \
  -n argo-events

# Update Event sensors
kubectl patch sensor k8sgpt-sensor -n argo-events \
  --patch '{"spec":{"triggers":[{"template":{"name":"k8sgpt-trigger","http":{"url":"http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"}}}]}'
```

## 🔍 Phase 3: End-to-End Validation

### Step 3.1: Cross-Namespace Communication Test
```bash
# Test service discovery from each namespace
for ns in argo-workflows argo-rollouts flux-system argo-events argocd pipecd; do
  echo "Testing from $ns namespace..."
  kubectl run test-cross-ns --image=curlimages/curl --rm -i --restart=Never \
    -- curl -f http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz \
    -n $ns || echo "❌ Failed from $ns"
done
```

### Step 3.2: Resource Analysis Validation
```bash
# Trigger analysis and verify results
curl -X POST http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "default",
    "resources": ["deployments", "services"],
    "filters": ["Ingress", "Service", "Deployment"],
    "backend": "agent-memory"
  }' | jq '.' > analysis-results.json

# Check analysis results
echo "Analysis Results:"
cat analysis-results.json | jq '.issues[] | {severity, category, description}'
```

### Step 3.3: Performance Monitoring
```bash
# Monitor resource usage
kubectl top pod -n k8sgpt-system -l app.kubernetes.io/name=k8sgpt

# Check metrics endpoint
kubectl port-forward service/k8sgpt 9090:9090 -n k8sgpt-system &
METRICS_PID=$!

sleep 5
curl -s http://localhost:9090/metrics | grep -E "(k8sgpt_analysis_duration|k8sgpt_issues_found|k8sgpt_backend_requests)"

kill $METRICS_PID 2>/dev/null
```

### Step 3.4: Integration Health Check
```bash
# Comprehensive health check script
cat << 'EOF' > validate-integration.sh
#!/bin/bash

echo "🔍 K8sGPT Integration Validation"
echo "================================="

# Check K8sGPT deployment
echo "1. Checking K8sGPT deployment..."
if kubectl get deployment k8sgpt -n k8sgpt-system &>/dev/null; then
  echo "✅ K8sGPT deployment found"
else
  echo "❌ K8sGPT deployment not found"
  exit 1
fi

# Check service endpoints
echo "2. Checking service endpoints..."
if kubectl get service k8sgpt -n k8sgpt-system &>/dev/null; then
  echo "✅ K8sGPT service found"
else
  echo "❌ K8sGPT service not found"
  exit 1
fi

# Test service connectivity
echo "3. Testing service connectivity..."
SERVICE_URL="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
if curl -f --connect-timeout 10 "$SERVICE_URL/healthz" &>/dev/null; then
  echo "✅ Service is healthy"
else
  echo "❌ Service health check failed"
  exit 1
fi

# Check component namespaces
echo "4. Checking component namespaces..."
COMPONENTS=("argo-workflows" "argo-rollouts" "flux-system" "argo-events" "argocd" "pipecd")
for ns in "${COMPONENTS[@]}"; do
  if kubectl get namespace "$ns" &>/dev/null; then
    echo "✅ Namespace $ns exists"
  else
    echo "⚠️  Namespace $ns not found (may not be deployed)"
  fi
done

# Test cross-namespace connectivity
echo "5. Testing cross-namespace connectivity..."
for ns in "${COMPONENTS[@]}"; do
  if kubectl run test-$ns --image=curlimages/curl --rm -i --restart=Never \
    -- curl -f --connect-timeout 5 "$SERVICE_URL/healthz" -n "$ns" &>/dev/null; then
    echo "✅ Connectivity from $ns namespace"
  else
    echo "❌ Connectivity failed from $ns namespace"
  fi
done

echo "6. Integration validation complete!"
EOF

chmod +x validate-integration.sh
./validate-integration.sh
```

## 🚨 Phase 4: Migration from Existing Deployments

### Step 4.1: Backup Current State
```bash
# Create backup before migration
./core/scripts/migrate-to-consolidated-k8sgpt.sh --backup

# Verify backup created
BACKUP_DIR="/tmp/k8sgpt-migration-backup-$(date +%Y%m%d-%H%M%S)"
if [ -d "$BACKUP_DIR" ]; then
  echo "✅ Backup created: $BACKUP_DIR"
  ls -la "$BACKUP_DIR"
else
  echo "❌ Backup creation failed"
  exit 1
fi
```

### Step 4.2: Run Migration Script
```bash
# Execute full migration
./core/scripts/migrate-to-consolidated-k8sgpt.sh

# Verify migration success
if kubectl get deployment k8sgpt -n k8sgpt-system &>/dev/null; then
  echo "✅ Migration completed successfully"
else
  echo "❌ Migration failed"
  exit 1
fi
```

### Step 4.3: Cleanup Old Deployments
```bash
# Remove old K8sGPT instances (manual verification)
echo "Checking for old K8sGPT deployments to clean up..."

OLD_DEPLOYMENTS=$(kubectl get deployments -A -l app.kubernetes.io/name=k8sgpt --no-headers | awk '{print $1":"$2}')

for deployment in $OLD_DEPLOYMENTS; do
  IFS=':' read -r namespace name <<< "$deployment"
  if [ "$namespace" != "k8sgpt-system" ]; then
    echo "Removing old deployment: $name in $namespace"
    kubectl delete deployment $name -n $namespace --ignore-not-found=true
    kubectl delete service $name -n $namespace --ignore-not-found=true
    kubectl delete configmap -l app.kubernetes.io/name=k8sgpt -n $namespace --ignore-not-found=true
    echo "✅ Cleaned up old deployment from $namespace"
  fi
done
```

## 📊 Phase 5: Production Readiness Validation

### Step 5.1: Load Testing
```bash
# Test K8sGPT under load
cat << 'EOF' > load-test.sh
#!/bin/bash

echo "🚀 Load Testing K8sGPT Service"
echo "==============================="

SERVICE_URL="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
CONCURRENT_REQUESTS=10
TEST_DURATION=60

echo "Running $CONCURRENT_REQUESTS concurrent requests for $TEST_DURATION seconds..."

# Start background load test
for i in $(seq 1 $CONCURRENT_REQUESTS); do
  (
    echo "Load test $i started"
    start_time=$(date +%s)
    end_time=$((start_time + TEST_DURATION))
    
    while [ $(date +%s) -lt $end_time ]; do
      curl -s -o /dev/null "$SERVICE_URL/healthz" || true
      sleep 1
    done
    
    echo "Load test $i completed"
  ) &
done

# Wait for all tests to complete
wait

echo "Load testing completed. Checking service health..."
if curl -f "$SERVICE_URL/healthz"; then
  echo "✅ Service healthy after load test"
else
  echo "❌ Service unhealthy after load test"
fi
EOF

chmod +x load-test.sh
./load-test.sh
```

### Step 5.2: Failover Testing
```bash
# Test backend failover
echo "Testing backend failover capabilities..."

# Temporarily disable agent-memory (if possible)
kubectl patch deployment k8sgpt -n k8sgpt-system \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"k8sgpt","env":[{"name":"K8SGPT_BACKEND","value":"localai"}]}}]}}'

echo "Testing LocalAI fallback..."
sleep 30

# Test service with fallback backend
if curl -f http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz; then
  echo "✅ Fallback to LocalAI working"
else
  echo "❌ Fallback to LocalAI failed"
fi

# Restore primary backend
kubectl patch deployment k8sgpt -n k8sgpt-system \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"k8sgpt","env":[{"name":"K8SGPT_BACKEND","value":"agent-memory"}]}}]}}'

echo "✅ Failover testing completed"
```

### Step 5.3: Security Validation
```bash
# Test RBAC permissions
echo "Testing RBAC permissions..."

# Test pod access
kubectl auth can-i get pods --as=system:serviceaccount:k8sgpt:k8sgpt -n k8sgpt-system

# Test service access
kubectl auth can-i get services --as=system:serviceaccount:k8sgpt:k8sgpt -n k8sgpt-system

# Test deployment access
kubectl auth can-i get deployments --as=system:serviceaccount:k8sgpt:k8sgpt -n k8sgpt-system

# Test custom resource access
kubectl auth can-i get workflows --as=system:serviceaccount:k8sgpt:k8sgpt -n k8sgpt-system
kubectl auth can-i get rollouts --as=system:serviceaccount:k8sgpt:k8sgpt -n k8sgpt-system

echo "✅ RBAC validation completed"
```

## 📈 Phase 6: Monitoring and Observability

### Step 6.1: Setup Monitoring
```bash
# Create ServiceMonitor for Prometheus
cat << 'EOF' > k8sgpt-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: k8sgpt-metrics
  namespace: k8sgpt-system
  labels:
    app.kubernetes.io/name: k8sgpt
    app.kubernetes.io/component: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: k8sgpt
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF

kubectl apply -f k8sgpt-servicemonitor.yaml
```

### Step 6.2: Setup Alerting
```bash
# Create PrometheusRules for alerting
cat << 'EOF' > k8sgpt-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: k8sgpt-alerts
  namespace: k8sgpt-system
  labels:
    app.kubernetes.io/name: k8sgpt
    app.kubernetes.io/component: monitoring
spec:
  groups:
  - name: k8sgpt.rules
    rules:
    - alert: K8sGPTDown
      expr: up{job="k8sgpt"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "K8sGPT service is down"
        description: "K8sGPT has been down for more than 5 minutes"
    
    - alert: K8sGPTHighErrorRate
      expr: rate(k8sgpt_analysis_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "K8sGPT error rate is high"
        description: "K8sGPT error rate is {{ $value }} errors per second"
    
    - alert: K8sGPTHighLatency
      expr: histogram_quantile(0.95, rate(k8sgpt_request_duration_seconds_bucket[5m])) > 5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "K8sGPT latency is high"
        description: "95th percentile latency is {{ $value }} seconds"
EOF

kubectl apply -f k8sgpt-alerts.yaml
```

## ✅ Phase 7: Validation Checklist

### Final Validation Checklist
```bash
echo "🎯 Final Validation Checklist"
echo "=========================="

# Deployment validation
DEPLOYMENT_HEALTHY=$(kubectl get deployment k8sgpt -n k8sgpt-system -o jsonpath='{.status.readyReplicas}')
if [ "$DEPLOYMENT_HEALTHY" = "1" ]; then
  echo "✅ K8sGPT deployment is healthy"
else
  echo "❌ K8sGPT deployment is not healthy"
fi

# Service validation
SERVICE_EXISTS=$(kubectl get service k8sgpt -n k8sgpt-system --no-headers | wc -l)
if [ "$SERVICE_EXISTS" = "1" ]; then
  echo "✅ K8sGPT service exists"
else
  echo "❌ K8sGPT service missing"
fi

# Integration validation
INTEGRATION_WORKING=true
for ns in argo-workflows argo-rollouts flux-system; do
  if kubectl run test-integration-$ns --image=curlimages/curl --rm -i --restart=Never \
    -- curl -f --connect-timeout 10 "http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz" -n $ns &>/dev/null; then
    echo "✅ Integration working for $ns"
  else
    echo "❌ Integration failed for $ns"
    INTEGRATION_WORKING=false
  fi
done

# Resource usage validation
MEMORY_USAGE=$(kubectl top pod -n k8sgpt-system -l app.kubernetes.io/name=k8sgpt --no-headers | awk '{print $3}' | sed 'sMi//')
if [ "${MEMORY_USAGE%Mi}" -le 4096 ]; then
  echo "✅ Memory usage within limits (${MEMORY_USAGE})"
else
  echo "⚠️  Memory usage high (${MEMORY_USAGE})"
fi

# Overall validation
if [ "$DEPLOYMENT_HEALTHY" = "1" ] && [ "$SERVICE_EXISTS" = "1" ] && [ "$INTEGRATION_WORKING" = "true" ]; then
  echo ""
  echo "🎉 ALL VALIDATIONS PASSED - K8sGPT consolidation is ready for production!"
else
  echo ""
  echo "❌ Some validations failed - please review and fix issues"
fi
```

## 📝 Documentation and Reporting

### Step 8.1: Generate Deployment Report
```bash
# Create deployment report
cat << 'EOF' > deployment-report.md
# K8sGPT Consolidation Deployment Report

## Deployment Summary
- **Date**: $(date)
- **Cluster**: $(kubectl config current-context)
- **K8sGPT Version**: v0.3.40
- **Backend**: Agent-memory (primary), LocalAI (fallback)
- **Namespace**: k8sgpt-system

## Resource Allocation
- **CPU Request**: 500m
- **CPU Limit**: 2000m
- **Memory Request**: 1Gi
- **Memory Limit**: 4Gi
- **Storage**: 10Gi PVC

## Service Endpoints
- **HTTP**: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080
- **Metrics**: http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics
- **Health**: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz

## Component Integration Status
$(for ns in argo-workflows argo-rollouts flux-system argo-events; do
  echo "- $ns: $(kubectl run test-$ns --image=curlimages/curl --rm -i --restart=Never -- curl -f --connect-timeout 5 "http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz" -n $ns &>/dev/null && echo "✅ Connected" || echo "❌ Failed")"
done)

## Validation Results
$(./validate-integration.sh)

## Next Steps
1. Monitor performance for 24 hours
2. Validate all component integrations in production workflows
3. Scale resources based on actual usage patterns
4. Set up automated monitoring and alerting
5. Document any custom configurations for future deployments

## Troubleshooting
- Check logs: \`kubectl logs -n k8sgpt-system deployment/k8sgpt\`
- Check events: \`kubectl get events -n k8sgpt-system --sort-by='.lastTimestamp'\`
- Service connectivity: \`kubectl port-forward service/k8sgpt 8080:8080 -n k8sgpt-system\`
EOF

echo "📄 Deployment report generated: deployment-report.md"
```

## 🚀 Production Rollout Plan

### Pre-Production Checklist
- [ ] All validations pass in test environment
- [ ] Performance metrics meet requirements
- [ ] Security scan completed
- [ ] Backup and recovery procedures tested
- [ ] Documentation updated with actual values
- [ ] Team training completed

### Production Deployment Steps
1. **Deploy to Staging**: Follow same process in staging environment
2. **Load Testing**: Conduct comprehensive load testing
3. **Security Review**: Final security validation
4. **Production Deployment**: Deploy to production clusters
5. **Monitoring Setup**: Configure production monitoring
6. **Rollback Plan**: Have rollback procedure ready

---

## 📞 Support and Troubleshooting

### Common Issues and Solutions
1. **Service Not Accessible**: Check network policies and DNS resolution
2. **Backend Connection Failed**: Verify agent-memory service status
3. **High Memory Usage**: Adjust resource limits or scale vertically
4. **Analysis Timeouts**: Increase timeout values or check backend performance
5. **Permission Errors**: Verify RBAC configuration

### Debug Commands
```bash
# Check K8sGPT logs
kubectl logs -n k8sgpt-system deployment/k8sgpt --since=10m

# Check pod events
kubectl describe pod -n k8sgpt-system -l app.kubernetes.io/name=k8sgpt

# Check service endpoints
kubectl get endpoints -n k8sgpt-system k8sgpt

# Test service connectivity
kubectl port-forward service/k8sgpt 8080:8080 -n k8sgpt-system
```

### Getting Help
- **Documentation**: Refer to integration guide and consolidation summary
- **Migration Script**: Use `./scripts/migrate-to-consolidated-k8sgpt.sh --help`
- **Community**: Open GitHub issues for specific problems
- **Logs**: Collect K8sGPT and component logs for analysis

---

**🎯 Success Criteria**: K8sGPT consolidation is successful when:
- Single healthy deployment in k8sgpt-system namespace
- All GitOps components can communicate with the service
- Resource usage is within expected limits
- Monitoring and alerting are configured
- Migration from old deployments is complete

This guide provides a comprehensive path from deployment through production validation of the consolidated K8sGPT architecture.
