# K8sGPT Integration with Qwen LLM - Comprehensive Guide

## Overview

This guide provides comprehensive documentation for integrating K8sGPT with Qwen LLM in the GitOps Infrastructure Control Plane. K8sGPT provides AI-powered Kubernetes cluster analysis and troubleshooting capabilities, while Qwen offers a powerful, open-source large language model for intelligent insights.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitOps Control Plane                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   K8sGPT    │  │   Qwen LLM  │  │  K8sGPT Analyzer    │ │
│  │   Skill     │  │  Backend    │  │     Agent           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Kubernetes Cluster                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    Pods     │  │ Services    │  │   Deployments       │ │
│  │   Resources │  │ Networking  │  │   ConfigMaps        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 🤖 AI-Powered Analysis
- **Intelligent Troubleshooting**: AI-driven problem detection and resolution
- **Contextual Insights**: Deep understanding of Kubernetes configurations
- **Automated Recommendations**: Actionable improvement suggestions
- **Multi-Cluster Support**: Analysis across multiple Kubernetes clusters

### 🔧 Qwen LLM Integration
- **Open Source**: Fully open-source LLM with no vendor lock-in
- **Local Deployment**: Run Qwen locally for privacy and security
- **Flexible Configuration**: Support for various Qwen model sizes
- **OpenAI Compatible**: Easy integration with existing tooling

### 📊 Comprehensive Monitoring
- **Real-time Analysis**: Continuous cluster health monitoring
- **Historical Insights**: Trend analysis and pattern recognition
- **Performance Metrics**: Resource usage and optimization recommendations
- **Security Scanning**: AI-powered vulnerability detection

## Quick Start

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Python 3.8+
- Access to Qwen LLM (local or cloud)

### Installation

#### 1. Install K8sGPT

```bash
# macOS/Linux
brew install k8sgpt

# Or download binary directly
curl -LO https://github.com/k8sgpt-ai/k8sgpt/releases/latest/download/k8sgpt_linux_amd64.tar.gz
tar xvf k8sgpt_linux_amd64.tar.gz
sudo mv k8sgpt /usr/local/bin/
```

#### 2. Setup Qwen LLM

**Option A: Local Qwen Server**

```bash
# Clone Qwen model and setup local server
git clone https://github.com/QwenLM/Qwen2.5.git
cd Qwen2.5

# Install dependencies
pip install torch transformers accelerate fastapi uvicorn

# Start local server (example)
python local_qwen_server.py --model qwen2.5-7b-instruct --port 8000
```

**Option B: Use Existing Qwen API**

```bash
# Configure environment variables
export QWEN_API_KEY="your-api-key"
export QWEN_BASE_URL="https://your-qwen-api.com"
```

#### 3. Configure K8sGPT for Qwen

```bash
# Add Qwen backend to K8sGPT
k8sgpt auth add \
  --backend localai \
  --model qwen2.5-7b-instruct \
  --baseurl http://localhost:8000/v1 \
  --password $QWEN_API_KEY

# Verify configuration
k8sgpt auth list
```

#### 4. Test Integration

```bash
# Run basic analysis
k8sgpt analyze --explain

# Analyze specific namespace
k8sgpt analyze --namespace default --explain

# Filter by resource
k8sgpt analyze --filter "pod/nginx-*" --explain
```

## Configuration

### K8sGPT Configuration

Create `~/.k8sgpt/config.yaml`:

```yaml
backend: localai
model: qwen2.5-7b-instruct
baseurl: http://localhost:8000/v1
api_key: ""  # Set via environment variable
max_tokens: 4096
temperature: 0.7
namespace: default
output_format: json
timeout: 300
retry_attempts: 3
```

### Qwen Model Options

| Model | Size | Use Case | Resources |
|-------|------|----------|-----------|
| qwen2.5-0.5b-instruct | 0.5B | Quick analysis | 2GB RAM |
| qwen2.5-1.5b-instruct | 1.5B | Basic troubleshooting | 4GB RAM |
| qwen2.5-7b-instruct | 7B | Advanced analysis | 16GB RAM |
| qwen2.5-14b-instruct | 14B | Enterprise features | 32GB RAM |
| qwen2.5-72b-instruct | 72B | Full capabilities | 128GB RAM |

### Environment Variables

```bash
# Qwen Configuration
export QWEN_API_KEY="your-api-key"
export QWEN_BASE_URL="http://localhost:8000"
export QWEN_MODEL="qwen2.5-7b-instruct"

# K8sGPT Configuration
export K8SGPT_BACKEND="localai"
export K8SGPT_OUTPUT_FORMAT="json"
export K8SGPT_TIMEOUT="300"
```

## Usage

### Basic Operations

#### Cluster Analysis

```bash
# Full cluster analysis
k8sgpt analyze --explain --backend localai

# Specific namespace
k8sgpt analyze --namespace kube-system --explain

# Resource-specific analysis
k8sgpt analyze --filter "deployment/*" --explain
```

#### Troubleshooting

```bash
# Diagnose problems
k8sgpt analyze --filter "problems" --explain

# Resource optimization
k8sgpt analyze --filter "resources" --explain

# Event analysis
k8sgpt analyze --filter "events" --explain
```

#### Output Formats

```bash
# JSON output (default)
k8sgpt analyze --output json

# YAML output
k8sgpt analyze --output yaml

# Table format
k8sgpt analyze --output table

# Summary only
k8sgpt analyze --output summary
```

### Advanced Usage

#### Custom Filters

```bash
# Multiple filters
k8sgpt analyze --filter "pod/app-*" --filter "service/frontend*" --explain

# Label-based filtering
k8sgpt analyze --filter "label=app=nginx" --explain

# Namespace and resource combination
k8sgpt analyze --namespace production --filter "deployment/*" --explain
```

#### Batch Analysis

```bash
# Analyze multiple namespaces
for ns in default production staging; do
  k8sgpt analyze --namespace $ns --explain --output json > "analysis-$ns.json"
done

# Scheduled analysis (cron)
0 */6 * * * /usr/local/bin/k8sgpt analyze --explain --output json >> /var/log/k8sgpt-analysis.log
```

#### Integration with Scripts

```python
#!/usr/bin/env python3
import subprocess
import json

def analyze_cluster(namespace=None):
    cmd = ['k8sgpt', 'analyze', '--explain', '--output', 'json']
    if namespace:
        cmd.extend(['--namespace', namespace])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# Usage
analysis = analyze_cluster('production')
print(f"Found {len(analysis.get('problems', []))} issues")
```

## Skill Integration

### K8sGPT Analyzer Skill

The repository includes a comprehensive K8sGPT analyzer skill that integrates with the existing agent framework:

```bash
# Execute skill directly
python3 core/ai/skills/k8sgpt-analyzer/scripts/k8sgpt_analyzer.py \
  '{"operation": "analyze", "targetResource": "cluster", "backend": "qwen"}'

# Via agent framework (if available)
agent execute --skill k8sgpt-analyzer --params '{"operation": "diagnose"}'
```

### Skill Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| operation | string | Yes | - | analyze, diagnose, optimize, monitor, report |
| targetResource | string | Yes | - | cluster, namespace, deployment, pod, service |
| scope | string | No | cluster | cluster, namespace, resource, all |
| backend | string | No | qwen | qwen, openai, localai, ollama |
| explain | boolean | No | true | Enable AI explanations |
| output | string | No | json | json, yaml, table, summary |

### Example Usage

```bash
# Analyze entire cluster
python3 scripts/k8sgpt_analyzer.py '{
  "operation": "analyze",
  "targetResource": "cluster",
  "scope": "cluster",
  "backend": "qwen",
  "explain": true
}'

# Diagnose specific namespace
python3 scripts/k8sgpt_analyzer.py '{
  "operation": "diagnose",
  "targetResource": "production",
  "scope": "namespace",
  "backend": "qwen"
}'

# Optimize resources
python3 scripts/k8sgpt_analyzer.py '{
  "operation": "optimize",
  "targetResource": "deployments",
  "scope": "cluster",
  "backend": "qwen"
}'
```

## Deployment

### Kubernetes Deployment

Deploy K8sGPT as a Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8sgpt-analyzer
  namespace: gitops-infra
spec:
  replicas: 2
  selector:
    matchLabels:
      app: k8sgpt-analyzer
  template:
    metadata:
      labels:
        app: k8sgpt-analyzer
    spec:
      containers:
      - name: k8sgpt
        image: k8sgpt/k8sgpt:latest
        command: ["/bin/sh"]
        args: ["-c", "while true; do sleep 3600; done"]
        env:
        - name: QWEN_API_KEY
          valueFrom:
            secretKeyRef:
              name: qwen-secret
              key: api-key
        - name: QWEN_BASE_URL
          value: "http://qwen-server:8000"
        volumeMounts:
        - name: k8sgpt-config
          mountPath: /root/.k8sgpt
      volumes:
      - name: k8sgpt-config
        configMap:
          name: k8sgpt-config
```

### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: k8sgpt-analyzer
  namespace: gitops-infra
spec:
  selector:
    app: k8sgpt-analyzer
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-config
  namespace: gitops-infra
data:
  config.yaml: |
    backend: localai
    model: qwen2.5-7b-instruct
    baseurl: http://qwen-server:8000/v1
    max_tokens: 4096
    temperature: 0.7
    output_format: json
    timeout: 300
```

## Monitoring and Observability

### Metrics Collection

K8sGPT analyzer provides built-in metrics:

```bash
# Enable metrics
export K8SGPT_METRICS_ENABLED=true
export K8SGPT_METRICS_PORT=8080

# Access metrics
curl http://localhost:8080/metrics
```

### Prometheus Integration

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: k8sgpt-analyzer
  namespace: gitops-infra
spec:
  selector:
    matchLabels:
      app: k8sgpt-analyzer
  endpoints:
  - port: metrics
    path: /metrics
```

### Grafana Dashboard

Import the provided Grafana dashboard for K8sGPT metrics:

- Cluster health overview
- Analysis execution times
- Error rates and patterns
- Resource utilization

## Security

### API Key Management

```bash
# Create secret for Qwen API key
kubectl create secret generic qwen-secret \
  --from-literal=api-key="your-qwen-api-key" \
  --namespace=gitops-infra

# Use in deployment
env:
- name: QWEN_API_KEY
  valueFrom:
    secretKeyRef:
      name: qwen-secret
      key: api-key
```

### RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: k8sgpt-analyzer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "deployments", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: k8sgpt-analyzer
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: k8sgpt-analyzer
subjects:
- kind: ServiceAccount
  name: k8sgpt-analyzer
  namespace: gitops-infra
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: k8sgpt-analyzer
  namespace: gitops-infra
spec:
  podSelector:
    matchLabels:
      app: k8sgpt-analyzer
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 443
  - to:
    - podSelector:
        matchLabels:
          app: qwen-server
    ports:
    - protocol: TCP
      port: 8000
```

## Troubleshooting

### Common Issues

#### K8sGPT Connection Failed

```bash
# Check K8sGPT installation
k8sgpt version

# Verify backend configuration
k8sgpt auth list

# Test Qwen connection
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-7b-instruct","messages":[{"role":"user","content":"test"}]}'
```

#### Permission Denied

```bash
# Check RBAC permissions
kubectl auth can-i get pods --as=system:serviceaccount:gitops-infra:k8sgpt-analyzer

# Test cluster access
kubectl get pods --as=system:serviceaccount:gitops-infra:k8sgpt-analyzer
```

#### Memory Issues

```bash
# Check resource usage
kubectl top pods -n gitops-infra

# Adjust resource limits
kubectl patch deployment k8sgpt-analyzer -p '{"spec":{"template":{"spec":{"containers":[{"name":"k8sgpt","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

### Debug Mode

```bash
# Enable debug logging
export K8SGPT_LOG_LEVEL=debug

# Run with verbose output
k8sgpt analyze --explain --verbose

# Check configuration
k8sgpt config show
```

## Performance Optimization

### Resource Tuning

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|-----------------|--------------|
| K8sGPT | 100m | 500m | 256Mi | 512Mi |
| Qwen 7B | 2 | 4 | 8Gi | 16Gi |
| Qwen 14B | 4 | 8 | 16Gi | 32Gi |

### Caching

```bash
# Enable result caching
export K8SGPT_CACHE_ENABLED=true
export K8SGPT_CACHE_TTL=300

# Configure cache backend
export K8SGPT_CACHE_BACKEND=redis
export K8SGPT_CACHE_REDIS_URL="redis://redis:6379"
```

### Batch Processing

```python
# Process multiple resources efficiently
def batch_analyze(resources, batch_size=10):
    results = []
    for i in range(0, len(resources), batch_size):
        batch = resources[i:i+batch_size]
        result = analyze_batch(batch)
        results.extend(result)
    return results
```

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Analyze Cluster with K8sGPT
  run: |
    k8sgpt analyze --explain --output json > analysis.json
    cat analysis.json
    
- name: Check for Critical Issues
  run: |
    python3 scripts/check_critical_issues.py analysis.json
```

### GitOps Integration

```yaml
# ArgoCD application for K8sGPT
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: k8sgpt-analyzer
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/agentic-reconciliation-engine
    path: overlays/k8sgpt
  destination:
    server: https://kubernetes.default.svc
    namespace: gitops-infra
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Monitoring Integration

```python
# Prometheus metrics for K8sGPT
from prometheus_client import Counter, Histogram, start_http_server

ANALYSIS_COUNTER = Counter('k8sgpt_analysis_total', 'Total K8sGPT analyses')
ANALYSIS_DURATION = Histogram('k8sgpt_analysis_duration_seconds', 'Analysis duration')

@ANALYSIS_DURATION.time()
def perform_analysis():
    ANALYSIS_COUNTER.inc()
    # K8sGPT analysis logic
    pass
```

## Best Practices

### Configuration Management

1. **Use ConfigMaps**: Store configuration in Kubernetes ConfigMaps
2. **Environment Variables**: Use environment variables for sensitive data
3. **Version Control**: Track configuration changes in Git
4. **Validation**: Validate configuration before deployment

### Security

1. **Principle of Least Privilege**: Grant minimal required permissions
2. **API Key Security**: Store API keys in Kubernetes secrets
3. **Network Isolation**: Use network policies to restrict traffic
4. **Audit Logging**: Enable audit logging for compliance

### Performance

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **Horizontal Scaling**: Deploy multiple replicas for high availability
3. **Caching**: Enable caching for frequently accessed data
4. **Batch Processing**: Process resources in batches for efficiency

### Monitoring

1. **Metrics Collection**: Enable comprehensive metrics collection
2. **Health Checks**: Implement proper health and readiness checks
3. **Alerting**: Set up alerts for critical issues
4. **Log Aggregation**: Centralize logs for analysis

## FAQ

### Q: What Kubernetes versions are supported?
A: K8sGPT supports Kubernetes v1.20 and later. For older versions, some features may not be available.

### Q: Can I use multiple LLM backends?
A: Yes, K8sGPT supports multiple backends. You can switch between them using the `--backend` flag.

### Q: How do I update Qwen models?
A: Update the model configuration in `~/.k8sgpt/config.yaml` and restart K8sGPT.

### Q: Is K8sGPT safe for production use?
A: Yes, K8sGPT is designed for production use with proper security configurations and RBAC.

### Q: How much resources does Qwen require?
A: Resource requirements vary by model size. Qwen2.5-7B requires approximately 16GB RAM, while larger models require more.

### Q: Can I run K8sGPT without internet access?
A: Yes, with local Qwen deployment, K8sGPT can operate entirely offline.

## Support and Contributing

### Getting Help

- **Documentation**: Check this guide and the official K8sGPT documentation
- **Issues**: Report bugs on GitHub issues
- **Community**: Join the K8sGPT Slack community
- **Support**: Contact the maintainers for enterprise support

### Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Development

```bash
# Setup development environment
git clone https://github.com/your-org/agentic-reconciliation-engine
cd agentic-reconciliation-engine

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Build documentation
mkdocs build
```

## License

This integration is licensed under the AGPLv3 license. See the LICENSE file for details.

---

**Note**: This guide is continuously updated. Check the repository for the latest version and updates.
