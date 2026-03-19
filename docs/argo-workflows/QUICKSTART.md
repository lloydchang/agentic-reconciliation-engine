# Argo Workflows Quickstart Guide

## Getting Started with Argo Workflows and Qwen LLM

This guide will help you get Argo Workflows with Qwen LLM integration up and running in minutes.

## Prerequisites

Before you begin, ensure you have:

- **Kubernetes cluster** (v1.20+) - local (kind, minikube, k3s) or cloud (EKS, GKE, AKS)
- **kubectl** configured to access your cluster
- **kustomize** installed (`brew install kustomize` on macOS)
- **Optional**: helm for monitoring stack

## Quick Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine

# Make the quickstart script executable
chmod +x scripts/quickstart-argo-workflows.sh
```

### 2. Run Quickstart

```bash
# Basic installation with all features
./scripts/quickstart-argo-workflows.sh

# Or with custom options
./scripts/quickstart-argo-workflows.sh \
  --namespace my-workflows \
  --cluster kind \
  --auto-approve
```

### 3. Access Services

Once installation completes, you'll see output like:

```
=== Access Information ===
Argo Workflows UI: http://localhost:2746
Qwen K8sGPT API: http://localhost:8080
MinIO Console: http://localhost:9001
Username: admin
Password: admin123
```

## Installation Options

### Custom Namespace

```bash
./scripts/quickstart-argo-workflows.sh --namespace production-workflows
```

### Skip Components

```bash
# Skip monitoring (Prometheus/Grafana)
./scripts/quickstart-argo-workflows.sh --no-monitoring

# Skip MinIO storage
./scripts/quickstart-argo-workflows.sh --no-minio

# Skip Qwen LLM integration
./scripts/quickstart-argo-workflows.sh --no-qwen
```

### Cluster-Specific Installation

```bash
# For kind cluster
./scripts/quickstart-argo-workflows.sh --cluster kind

# For EKS cluster
./scripts/quickstart-argo-workflows.sh --cluster eks

# For GKE cluster
./scripts/quickstart-argo-workflows.sh --cluster gke

# Auto-detect cluster type
./scripts/quickstart-argo-workflows.sh --cluster auto
```

### Dry Run (Preview)

```bash
# See what would be installed without actually installing
./scripts/quickstart-argo-workflows.sh --dry-run
```

## First Steps

### 1. Explore Argo Workflows UI

Open http://localhost:2746 in your browser:

- **Dashboard**: View running and completed workflows
- **Submit**: Submit new workflows
- **Templates**: Browse workflow templates
- **Cron**: View scheduled workflows

### 2. Try a Basic Workflow

```bash
# Submit a simple hello world workflow
kubectl apply -f - << EOF
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: hello-world
  namespace: argo-workflows
spec:
  entrypoint: main
  templates:
  - name: main
    container:
      image: alpine:latest
      command: [echo]
      args: ["Hello from Argo Workflows!"]
EOF

# Watch the workflow
kubectl get workflows -n argo-workflows -w

# View logs
kubectl logs -n argo-workflows -l workflow=hello-world -c main
```

### 3. Test Qwen LLM Integration

```bash
# Test Qwen API directly
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test",
    "namespace": "argo-workflows",
    "component": "hello-world",
    "severity": "info",
    "description": "Testing Qwen LLM integration"
  }'
```

### 4. Run AI-Powered Workflow

```bash
# Submit a workflow that uses Qwen for analysis
kubectl apply -f overlay/argo-workflows/examples/qwen-analysis-workflows.yaml

# Monitor the workflow
kubectl get workflows -n argo-workflows -l app.kubernetes.io/llm=qwen -w

# View analysis results
kubectl logs -n argo-workflows -l workflow=qwen-workflow-analysis -c analyze-with-qwen
```

## Workflow Examples

### Basic Examples

Try these basic workflow examples from the repository:

```bash
# Apply all basic examples
kubectl apply -f overlay/argo-workflows/examples/basic-workflows.yaml

# List workflows
kubectl get workflows -n argo-workflows

# View specific workflow
kubectl describe workflow basic-hello-world -n argo-workflows
```

### CI/CD Examples

```bash
# Apply CI/CD pipeline examples
kubectl apply -f overlay/argo-workflows/examples/ci-cd-workflows.yaml

# Monitor CI/CD workflows
kubectl get workflows -n argo-workflows -l app.kubernetes.io/component=ci-cd
```

## Monitoring

### Grafana Dashboard

Access Grafana at http://localhost:3000 (if monitoring was installed):

- **Username**: admin
- **Password**: admin123

Available dashboards:
- **Argo Workflows Overview**: Workflow metrics and status
- **Qwen LLM Analytics**: AI analysis performance
- **Resource Usage**: System resource utilization

### Prometheus Metrics

Access Prometheus at http://localhost:9090:

Key metrics to monitor:
- `argo_workflows_workflow_status_total`: Workflow status counts
- `qwen_analysis_requests_total`: Qwen analysis requests
- `container_cpu_usage_seconds_total`: CPU usage
- `container_memory_usage_bytes`: Memory usage

### CLI Monitoring

```bash
# Component status
kubectl get all -n argo-workflows

# Workflow events
kubectl get events -n argo-workflows --sort-by='.lastTimestamp'

# Resource usage
kubectl top pods -n argo-workflows
```

## Troubleshooting

### Common Issues

#### 1. Port Forwarding Not Working

```bash
# Stop existing port forwards
pkill -f "kubectl port-forward"

# Restart port forwarding
./scripts/quickstart-argo-workflows.sh
```

#### 2. Workflows Stuck in Pending

```bash
# Check controller logs
kubectl logs -n argo-workflows deployment/argo-workflows-controller

# Check RBAC permissions
kubectl auth can-i create workflows -n argo-workflows

# Check workflow events
kubectl describe workflow <workflow-name> -n argo-workflows
```

#### 3. Qwen Service Not Responding

```bash
# Check Qwen deployment
kubectl get deployment qwen-k8sgpt -n argo-workflows

# Check Qwen logs
kubectl logs -n argo-workflows deployment/qwen-k8sgpt

# Test health endpoint
kubectl exec -n argo-workflows deployment/qwen-k8sgpt -- curl http://localhost:8080/health
```

#### 4. MinIO Connection Issues

```bash
# Check MinIO deployment
kubectl get deployment minio -n argo-workflows

# Test MinIO connectivity
kubectl run minio-test --rm -i --restart=Never --image=minio/mc:latest \
  --namespace=argo-workflows -- \
  mc alias set minio http://minio:9000 admin admin123 && mc ls minio
```

### Debug Commands

```bash
# Full system status
kubectl get all -n argo-workflows

# Workflow details
kubectl get workflows -n argo-workflows -o wide

# Component logs
kubectl logs -n argo-workflows deployment/argo-workflows-controller --tail=50
kubectl logs -n argo-workflows deployment/argo-workflows-server --tail=50
kubectl logs -n argo-workflows deployment/qwen-k8sgpt --tail=50

# Events
kubectl get events -n argo-workflows --sort-by='.lastTimestamp' --tail=20
```

## Configuration

### Environment Variables

Create a `.env` file for custom configuration:

```bash
# .env
NAMESPACE=argo-workflows
ARGO_WORKFLOWS_VERSION=v3.5.0
QWEN_MODEL_NAME=qwen
QWEN_MAX_TOKENS=4096
QWEN_TEMPERATURE=0.7
ENABLE_MONITORING=true
ENABLE_MINIO=true
```

### Custom Configuration Files

1. **Edit workflow controller config**:
   ```bash
   vim overlay/argo-workflows/configurations/workflow-controller-config.yaml
   ```

2. **Edit Qwen configuration**:
   ```bash
   vim overlay/argo-workflows/qwen/qwen-configmap.yaml
   ```

3. **Apply changes**:
   ```bash
   kustomize build overlay/argo-workflows | kubectl apply -f -
   ```

### Resource Scaling

For production workloads, increase resource limits:

```bash
# Edit production patches
vim overlay/argo-workflows/patches/prod/controller-resources.yaml
vim overlay/argo-workflows/patches/prod/qwen-resources.yaml

# Apply production configuration
kustomize build overlay/argo-workflows/overlays/prod | kubectl apply -f -
```

## Testing

### Run Automated Tests

```bash
# Run all tests
./tests/argo-workflows/test-suite.sh

# Run specific test suite
./tests/argo-workflows/test-suite.sh --test-suite basic

# Run with verbose output
./tests/argo-workflows/test-suite.sh --verbose

# Run without cleanup (keep test resources)
./tests/argo-workflows/test-suite.sh --no-cleanup
```

### Test Suites

1. **Basic Tests**: Core Argo Workflows functionality
2. **Qwen Tests**: LLM integration validation
3. **Integration Tests**: End-to-end workflow testing
4. **Performance Tests**: Load and performance validation
5. **Security Tests**: RBAC and network policy testing

### Manual Testing

```bash
# Test basic workflow
kubectl apply -f overlay/argo-workflows/examples/basic-workflows.yaml
kubectl get workflows -n argo-workflows

# Test Qwen integration
kubectl apply -f overlay/argo-workflows/examples/qwen-analysis-workflows.yaml
kubectl logs -n argo-workflows -l workflow=qwen-workflow-analysis -c analyze-with-qwen
```

## Next Steps

### 1. Create Custom Workflows

Learn to create your own workflows:

```bash
# Create a custom workflow template
kubectl apply -f - << EOF
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: my-custom-workflow
  namespace: argo-workflows
spec:
  entrypoint: main
  templates:
  - name: main
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: ["print('Hello from my custom workflow!')"]
EOF
```

### 2. Integrate with Your Applications

Use Argo Workflows for:

- **CI/CD Pipelines**: Automated build, test, and deployment
- **Data Processing**: Batch jobs and ETL workflows
- **Machine Learning**: Model training and inference pipelines
- **Backup and Recovery**: Automated backup workflows

### 3. Set Up Monitoring

Configure comprehensive monitoring:

```bash
# Install monitoring stack (if not already installed)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

# Import Grafana dashboards
kubectl apply -f overlay/argo-workflows/monitoring/grafana-dashboard.yaml
```

### 4. Configure SSO

Set up single sign-on for Argo Workflows:

```bash
# Configure OIDC
kubectl patch configmap workflow-controller-configmap -n argo-workflows --patch-file sso-config.yaml
```

## Cleanup

### Remove Argo Workflows

```bash
# Delete the namespace (removes all resources)
kubectl delete namespace argo-workflows

# Or use the uninstall script (if available)
./scripts/uninstall-argo-workflows.sh --namespace argo-workflows
```

### Stop Port Forwarding

```bash
# Kill port forwarding processes
kill $(cat /tmp/argo-port-forward.pid)

# Or find and kill manually
pkill -f "kubectl port-forward"
```

## Support

### Documentation Resources

- [Full Documentation](../README.md)
- [Argo Workflows Official Docs](https://argoproj.github.io/argo-workflows/)
- [Qwen Model Documentation](https://github.com/QwenLM/Qwen)

### Getting Help

1. **Check logs**: Use the debug commands above
2. **Run tests**: Execute the test suite to validate installation
3. **Check events**: Look at Kubernetes events for errors
4. **Review configuration**: Verify your custom configurations

### Community

- [Argo Workflows Slack](https://argoproj.github.io/community/join-slack/)
- [GitHub Issues](https://github.com/your-org/agentic-reconciliation-engine/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/argo-workflows)

---

**Congratulations!** You now have Argo Workflows with Qwen LLM integration running. Explore the examples, create your own workflows, and leverage the AI-powered analysis capabilities.
