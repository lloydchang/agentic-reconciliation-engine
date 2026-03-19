# Overlay Quick Start Guide

Complete quick start guide for the Agentic Reconciliation Engine Overlay System.

## Table of Contents

1. [What Are Overlays?](#what-are-overlays)
2. [Installation](#installation)
3. [Quick Start Examples](#quick-start-examples)
4. [Common Use Cases](#common-use-cases)
5. [Advanced Examples](#advanced-examples)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

## What Are Overlays?

Overlays are modular extensions that customize and enhance the base Agentic Reconciliation Engine without modifying core components. They provide:

- **Customization**: Add new features and capabilities
- **Isolation**: Separate concerns from base system
- **Reusability**: Share overlays across environments
- **Upstream Compatibility**: Easy to merge updates

### Overlay Types

| Type | Purpose | Examples |
|-------|---------|----------|
| **Skills** | Extend AI agent capabilities | Enhanced debugging, ML analysis |
| **Dashboard** | Customize UI/UX | Dark themes, custom widgets |
| **Infrastructure** | Enhance infrastructure | Multi-cloud, security policies |
| **Composed** | Combine multiple overlays | Enterprise suite, community bundle |

## Installation

### Prerequisites

```bash
# Required tools
kubectl --version  # >= 1.20
kustomize version  # >= 4.0
python3 --version  # >= 3.8
git --version  # For version control

# Clone repository
git clone https://github.com/gitops-infra-core/operators/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Make tools executable
chmod +x core/scripts/automation/*.py
export PATH="$PWD/scripts:$PATH"
```

### Quick Setup

```bash
# Verify installation
python core/automation/scripts/overlay-cli.py list

# Test with example overlay
python core/automation/scripts/validate-overlays.py overlay/ai/skills/debug/enhanced
```

## Quick Start Examples

### 1. Hello World Overlay

Create your first overlay in 5 minutes:

```bash
# Create overlay from template
python core/automation/scripts/overlay-cli.py create hello-world skills debug --template skill-overlay

# Navigate to overlay directory
cd overlay/ai/skills/hello-world

# Edit overlay metadata
cat > overlay-metadata.yaml << EOF
---
name: hello-world
version: "1.0.0"
description: "Simple hello world overlay"
category: skills
base_path: "core/ai/skills/debug"
license: "AGPLv3"
risk_level: low
autonomy: fully_auto

maintainer:
  name: "Your Name"
  email: "your.email@example.com"

tags:
  - skills
  - example
  - hello-world

compatibility:
  min_base: "1.0.0"
  kubernetes: ">=1.20"

examples:
  - name: "Hello World"
    description: "Run hello world example"
    command: "echo 'Hello, World!'"
    expected_output: "Hello, World!"
EOF

# Test overlay
python core/scripts/automation/validate-overlays.py .
python core/scripts/automation/test-overlays.py .

# Apply overlay
python core/scripts/automation/overlay-cli.py apply . --dry-run
```

### 2. Configuration Override Overlay

Add custom configuration to existing skills:

```bash
# Create configuration overlay
python core/scripts/automation/overlay-cli.py create custom-config skills debug --template skill-overlay

# Add configuration patches
cat > patches/custom-config.yaml << EOF
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-config
data:
  LOG_LEVEL: "debug"
  TIMEOUT: "300"
  FEATURE_X: "enabled"
  CUSTOM_SETTING: "production"
EOF

# Update kustomization.yaml
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: custom-config
  namespace: flux-system
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/custom-config.yaml
configMapGenerator:
  - name: custom-config-overlay
    literals:
      - OVERLAY_ENABLED=true
      - CUSTOM_FEATURES=true
EOF

# Test and apply
python core/scripts/automation/overlay-cli.py validate .
python core/scripts/automation/overlay-cli.py apply . --dry-run
```

### 3. Dashboard Theme Overlay

Create a custom dashboard theme:

```bash
# Create theme overlay
python core/scripts/automation/overlay-cli.py create my-theme dashboard themes --template dashboard-overlay

# Add theme files
mkdir -p theme/css
cat > theme/css/custom-theme.css << EOF
:root {
  --primary-color: #2563eb;
  --secondary-color: #6c757d;
  --background-color: #f8f9fa;
  --text-color: #212529;
  --border-color: #dee2e6;
}

.dashboard-container {
  background: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
}

.button-primary {
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.button-primary:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}
EOF

# Update kustomization.yaml
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: my-theme
  namespace: flux-system
resources:
  - ../../../../../core/ai/runtime/dashboard
patchesStrategicMerge:
  - patches/theme-patches.yaml
configMapGenerator:
  - name: my-theme-config
    files:
      - theme/css/custom-theme.css
    literals:
      - THEME_NAME="custom-theme"
      - THEME_VERSION="1.0.0"
      - CUSTOM_CSS=true
EOF

# Test theme
python core/scripts/automation/overlay-cli.py validate .
python core/scripts/automation/overlay-cli.py build . --output my-theme.yaml
```

### 4. Infrastructure Enhancement Overlay

Add monitoring and security to infrastructure:

```bash
# Create infrastructure overlay
python core/scripts/automation/overlay-cli.py create enhanced-infra infrastructure flux --template infra-overlay

# Add monitoring configuration
cat > config/monitoring.yaml << EOF
global:
  scrape_interval: 30s
  evaluation_interval: 30s

rule_files:
  - "/etc/prometheus/rules/*.yaml"

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: (.+)
        target_label: application
        replacement: \$1
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: (.+)
        target_label: application
        replacement: \$1
EOF

# Add security policies
cat > security/network-policies.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: enhanced-security
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: flux-system
    - namespaceSelector:
        matchLabels:
          name: monitoring
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
EOF

# Update kustomization.yaml
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: enhanced-infra
  namespace: flux-system
resources:
  - ../../../../control-plane
  - monitoring/
  - security/
configMapGenerator:
  - name: enhanced-infra-config
    files:
      - config/monitoring.yaml
    literals:
      - MONITORING_ENABLED=true
      - SECURITY_ENHANCED=true
      - ALERTING_ENABLED=true
EOF

# Test infrastructure overlay
python core/scripts/automation/overlay-cli.py validate .
python core/scripts/automation/test-overlays.py .
```

## Common Use Cases

### 1. Development Environment

Set up a lightweight development environment:

```bash
# Create development overlay
python core/scripts/automation/overlay-cli.py create dev-env composed ""

# Add base components
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: dev-env
  namespace: development
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Development tools
  - ../core/ai/skills/debug/enhanced
  - ../core/ai/runtime/dashboard/themes/dark-pro

# Development configuration
configMapGenerator:
  - name: dev-env-config
    literals:
      - ENVIRONMENT=development
      - DEBUG_MODE=true
      - LOG_LEVEL=debug
      - HOT_RELOAD=true
      - RESOURCE_LIMITS=minimal

# Development resource requirements
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
EOF

# Deploy development environment
python core/scripts/automation/overlay-cli.py validate .
python core/scripts/automation/overlay-cli.py apply .
```

### 2. Production Environment

Set up a production-ready environment:

```bash
# Create production overlay
python core/scripts/automation/overlay-cli.py create prod-env composed ""

# Add production components
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: prod-env
  namespace: production
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Production enhancements
  - ../core/ai/skills/debug/enhanced
  - ../core/ai/runtime/dashboard/themes/dark-pro
  - ../core/operators/monitoring/enhanced
  - ../core/operators/security/policies

# Production configuration
configMapGenerator:
  - name: prod-env-config
    literals:
      - ENVIRONMENT=production
      - SECURITY_LEVEL=high
      - MONITORING_LEVEL=comprehensive
      - BACKUP_ENABLED=true
      - AUDIT_LOGGING=true
      - MULTI_REGION=true

# Production resource requirements
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
EOF

# Deploy production environment
python core/scripts/automation/overlay-cli.py validate .
python core/scripts/automation/overlay-cli.py apply .
```

### 3. Multi-Environment Setup

Manage multiple environments:

```bash
# Create environment-specific overlays
for env in development staging production; do
  python core/scripts/automation/overlay-cli.py create $env-env composed ""
  
  cat > core/deployment/overlays/composed/$env-env/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: $env-env
  namespace: $env
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Common components
  - ../core/ai/skills/debug/enhanced
  - ../core/ai/runtime/dashboard/themes/dark-pro

configMapGenerator:
  - name: $env-env-config
    literals:
      - ENVIRONMENT=$env
      - LOG_LEVEL=\$( [[ "$env" == "production" ]] && echo "info" || echo "debug" \)
      - DEBUG_MODE=\$( [[ "$env" == "development" ]] && echo "true" || echo "false" \)
EOF

  # Environment-specific resource limits
  if [[ "$env" == "development" ]]; then
    cat >> core/deployment/overlays/composed/$env-env/kustomization.yaml << 'EOF'
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
EOF
  elif [[ "$env" == "production" ]]; then
    cat >> core/deployment/overlays/composed/$env-env/kustomization.yaml << 'EOF'
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
EOF
  fi
  
  # Validate environment overlay
  python core/scripts/automation/overlay-cli.py validate core/deployment/overlays/composed/$env-env
done

# Deploy specific environment
python core/scripts/automation/overlay-cli.py apply core/deployment/overlays/composed/production-env
```

## Advanced Examples

### 1. ML-Enhanced Debugging Overlay

Add machine learning capabilities to debugging:

```bash
# Create ML debugging overlay
python core/scripts/automation/overlay-cli.py create ml-debug skills debug --template skill-overlay

# Add ML configuration
cat > config/ml-config.yaml << EOF
model_config:
  algorithms:
    - isolation_forest
    - random_forest
    - gradient_boosting
  features:
    - pod_metrics
    - log_patterns
    - network_latency
    - error_rates
  thresholds:
    anomaly_score: 0.8
    confidence_level: 0.9
    correlation_threshold: 0.7

training:
  batch_size: 1000
  epochs: 100
  validation_split: 0.2
  early_stopping:
    patience: 10
    min_delta: 0.001
EOF

# Add ML deployment patches
cat > patches/ml-deployment.yaml << EOF
---
# Enhanced Deployment with ML capabilities
apiVersion: apps/v1
kind: Deployment
metadata:
  name: debug
  labels:
    overlay: ml-debug
spec:
  template:
    spec:
      containers:
      - name: debug
        # Add ML sidecar
        - name: ml-processor
          image: python:3.11-slim
          command:
            - python
            - -c
            - |
              import pandas as pd
              import numpy as np
              from sklearn.ensemble import IsolationForest
              import requests
              import time
              
              while True:
                  try:
                      # Collect metrics from main container
                      response = requests.get('http://localhost:8080/metrics', timeout=5)
                      if response.status_code == 200:
                          metrics = response.json()
                          # Process with ML model
                          anomaly_score = detect_anomaly(metrics)
                          if anomaly_score > 0.8:
                              print(f"Anomaly detected: {anomaly_score}")
                  except Exception as e:
                      print(f"ML processing error: {e}")
                  time.sleep(30)
          resources:
            requests:
              cpu: "200m"
              memory: "512Mi"
            limits:
              cpu: "500m"
              memory: "1Gi"
          volumeMounts:
          - name: ml-models
            mountPath: /models
      volumes:
      - name: ml-models
        persistentVolumeClaim:
          claimName: ml-debug-models
EOF

# Add ML model storage
cat > patches/ml-storage.yaml << EOF
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ml-debug-models
  labels:
    overlay: ml-debug
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
EOF

# Update kustomization.yaml
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: ml-debug
  namespace: flux-system
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/ml-deployment.yaml
  - patches/ml-storage.yaml
configMapGenerator:
  - name: ml-debug-config
    files:
      - config/ml-config.yaml
    literals:
      - ML_ENABLED=true
      - ANOMALY_DETECTION=true
      - PREDICTIVE_ANALYSIS=true
      - MODEL_TRAINING=true
EOF

# Test ML overlay
python core/scripts/automation/overlay-cli.py validate .
python core/scripts/automation/test-overlays.py .
python core/scripts/automation/overlay-cli.py build . --output ml-debug.yaml
```

### 2. Multi-Cloud Infrastructure Overlay

Deploy across multiple cloud providers:

```bash
# Create multi-cloud overlay
python core/scripts/automation/overlay-cli.py create multi-cloud infrastructure flux --template infra-overlay

# Add cloud-specific configurations
mkdir -p configs/{aws,azure,gcp}

# AWS configuration
cat > configs/aws/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-cloud-aws
configMapGenerator:
  - name: cloud-config
    literals:
      - CLOUD_PROVIDER=aws
      - REGION=us-east-1
      - AVAILABILITY_ZONE=us-east-1a
      - CLUSTER_TYPE=eks
      - STORAGE_CLASS=gp2
patchesStrategicMerge:
  - patches/aws-specific.yaml
EOF

# Azure configuration
cat > configs/azure/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-cloud-azure
configMapGenerator:
  - name: cloud-config
    literals:
      - CLOUD_PROVIDER=azure
      - REGION=eastus
      - AVAILABILITY_ZONE=1
      - CLUSTER_TYPE=aks
      - STORAGE_CLASS=managed-premium
patchesStrategicMerge:
  - patches/azure-specific.yaml
EOF

# GCP configuration
cat > configs/gcp/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-cloud-gcp
configMapGenerator:
  - name: cloud-config
    literals:
      - CLOUD_PROVIDER=gcp
      - REGION=us-central1
      - AVAILABILITY_ZONE=us-central1-a
      - CLUSTER_TYPE=gke
      - STORAGE_CLASS=standard
patchesStrategicMerge:
  - patches/gcp-specific.yaml
EOF

# Cloud-specific patches
cat > patches/aws-specific.yaml << EOF
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-cloud-config
data:
  eks_cluster.yaml: |
    apiVersion: eksctl.io/v1alpha5
    kind: ClusterConfig
    metadata:
      name: my-cluster
      region: us-east-1
      version: "1.28"
    nodeGroups:
      - name: ng-1
        instanceType: m5.large
        desiredCapacity: 2
        volumeSize: 80
        ssh:
          allow: true
        iam:
          withAddonPolicies:
            - AmazonEKSWorkerNodePolicy
            - AmazonEC2ContainerRegistryReadOnly
EOF

cat > patches/azure-specific.yaml << EOF
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: azure-cloud-config
data:
  aks_cluster.yaml: |
    apiVersion: containerservice.azure.com/v1beta3
    kind: ManagedCluster
    metadata:
      name: my-cluster
      location: eastus
    spec:
      kubernetesVersion: 1.28.3
      dnsPrefix: mycluster
      agentPoolProfiles:
        - name: default
          count: 2
          vmSize: Standard_D2s_v3
          osType: Linux
          mode: System
EOF

cat > patches/gcp-specific.yaml << EOF
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: gcp-cloud-config
data:
  gke_cluster.yaml: |
    apiVersion: container.cnrm.cloud.google.com/v1beta1
    kind: ContainerCluster
    metadata:
      name: my-cluster
      location: us-central1
    spec:
      initialNodeCount: 2
      nodeConfig:
        machineType: e2-standard-2
        oauthScopes:
          - "https://www.googleapis.com/auth/cloud-platform"
      nodeLocations:
        - us-central1-a
        - us-central1-b
EOF

# Main kustomization.yaml
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-cloud
  namespace: flux-system
resources:
  - ../../../../control-plane
configurations:
  - configs/\${CLOUD_PROVIDER:-aws}/
configMapGenerator:
  - name: multi-cloud-config
    literals:
      - MULTI_CLOUD_ENABLED=true
      - CLOUD_FAILOVER=true
      - CROSS_CLOUD_NETWORKING=true
EOF

# Test multi-cloud overlays
for cloud in aws azure gcp; do
  echo "Testing $cloud configuration..."
  CLOUD_PROVIDER=$cloud python core/scripts/automation/overlay-cli.py validate .
  CLOUD_PROVIDER=$cloud python core/scripts/automation/overlay-cli.py build . --output multi-cloud-$cloud.yaml
done
```

### 3. Security Hardening Overlay

Add comprehensive security policies:

```bash
# Create security overlay
python core/scripts/automation/overlay-cli.py create security-hardened infrastructure flux --template infra-overlay

# Add security policies
mkdir -p security/{policies,rbac,network}

# Pod Security Policy
cat > security/core/governance/pod-security.yaml << EOF
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
  namespace: flux-system
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
EOF

# Network Policy
cat > security/network/network-policy.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
EOF

cat > security/network/allow-dns.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to: []
    ports:
    - protocol: UDP
      port: 53
EOF

# RBAC Policy
cat > security/rbac/rbac.yaml << EOF
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flux-system
  namespace: flux-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: flux-system-role
  namespace: flux-system
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: flux-system-binding
  namespace: flux-system
subjects:
- kind: ServiceAccount
  name: flux-system
  namespace: flux-system
roleRef:
  kind: Role
  name: flux-system-role
  apiGroup: rbac.authorization.k8s.io
EOF

# Security configuration
cat > security/security-config.yaml << EOF
security_policies:
  pod_security:
    - restricted
    - baseline
  network_policies:
    - deny_all_ingress
    - allow_dns_only
    - allow_same_namespace
  rbac:
    - least_privilege
    - separation_of_duties
  
compliance:
  frameworks:
    - cis_benchmark_1.6
    - nist_800_53
    - pci_dss_4.0
  
monitoring:
  security_events:
    enabled: true
    log_level: info
    alert_threshold: medium
  
audit:
  enabled: true
  log_all_api_calls: true
  retention_period: "90d"
EOF

# Main kustomization.yaml
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: security-hardened
  namespace: flux-system
resources:
  - ../../../../control-plane
  - security/core/governance/
  - security/network/
  - security/rbac/
configMapGenerator:
  - name: security-hardened-config
    files:
      - security/security-config.yaml
    literals:
      - SECURITY_LEVEL=high
      - COMPLIANCE_MODE=strict
      - AUDIT_LOGGING=true
      - NETWORK_POLICY_ENABLED=true
      - POD_SECURITY_ENABLED=true
      - RBAC_ENHANCED=true
EOF

# Test security overlay
python core/scripts/automation/overlay-cli.py validate .
python core/scripts/automation/test-overlays.py .
python core/scripts/automation/overlay-cli.py build . --output security-hardened.yaml
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Validation Failures

```bash
# Issue: Missing required files
❌ ERRORS (1):
  - Missing required file: overlay-metadata.yaml

# Solution: Create missing file
cat > overlay-metadata.yaml << EOF
---
name: my-overlay
version: "1.0.0"
description: "My overlay description"
category: skills
base_path: "core/ai/skills/debug"
license: "AGPLv3"
risk_level: low
autonomy: fully_auto
EOF

# Issue: Invalid YAML syntax
❌ ERRORS (1):
  - Invalid YAML in kustomization.yaml: mapping values are not allowed here

# Solution: Fix YAML syntax
yamllint kustomization.yaml
# Use 2 spaces for indentation
# Quote strings with special characters
```

#### 2. Build Failures

```bash
# Issue: Resource path not found
Error: accumulating resources: couldn't make target for path

# Solution: Check and fix paths
find . -name "*.yaml" | head -10
# Update kustomization.yaml with correct relative paths
kustomize build . --enable-alpha-plugins

# Issue: Kustomize build timeout
Error: build timed out after 30 seconds

# Solution: Optimize overlay
# Reduce complexity
# Use kustomize --enable-alpha-plugins for advanced features
# Check for circular dependencies
```

#### 3. Deployment Issues

```bash
# Issue: Resource conflicts
Error: the server could not find the requested resource

# Solution: Check resource names and namespaces
kubectl get all -n flux-system
kubectl describe deployment my-overlay -n flux-system

# Issue: Permission denied
Error: forbidden: User "system:serviceaccount:default" cannot create resource

# Solution: Check RBAC permissions
kubectl auth can-i create deployment --namespace=flux-system
kubectl auth can-i create configmap --namespace=flux-system
```

#### 4. Performance Issues

```bash
# Issue: Slow overlay application
# Solution: Optimize overlay structure
# Use ConfigMapGenerator instead of large patches
# Minimize resource count
# Use patchesJson6902 for targeted changes

# Issue: Memory/CPU usage high
# Solution: Set appropriate resource limits
# Add resource requests and limits
# Use horizontal pod autoscaling
# Monitor resource usage
```

### Debug Commands

```bash
# Comprehensive overlay validation
python core/scripts/automation/validate-overlays.py core/deployment/overlays/ --verbose --report validation-report.json

# Test overlay functionality
python core/scripts/automation/test-overlays.py core/deployment/overlays/ --verbose --coverage

# Build with debugging
kustomize build core/deployment/overlays/core/ai/skills/debug/enhanced --enable-alpha-plugins --v 6

# Check overlay composition
python core/scripts/automation/test-overlays.py core/deployment/overlays/composed/enterprise-suite --test-composition

# Verify overlay registry
python core/scripts/automation/overlay-registry.py validate --verbose
```

## Next Steps

### 1. Explore Existing Overlays

```bash
# List all available overlays
python core/scripts/automation/overlay-cli.py list

# Search by category
python core/scripts/automation/overlay-cli.py list --category skills
python core/scripts/automation/overlay-cli.py list --category dashboard
python core/scripts/automation/overlay-cli.py list --category infrastructure
python core/scripts/automation/overlay-cli.py list --category composed

# Search by keyword
python core/scripts/automation/overlay-cli.py search "debugging"
python core/scripts/automation/overlay-cli.py search "monitoring"
python core/scripts/automation/overlay-cli.py search "security"
```

### 2. Create Custom Overlays

```bash
# Use templates for quick start
python core/scripts/automation/overlay-cli.py create my-overlay skills debug --template skill-overlay
python core/scripts/automation/overlay-cli.py create my-theme dashboard themes --template dashboard-overlay
python core/scripts/automation/overlay-cli.py create my-infra infrastructure flux --template infra-overlay
python core/scripts/automation/overlay-cli.py create my-bundle composed ""

# Customize overlay templates
cd core/deployment/overlays/core/ai/skills/my-overlay
# Edit files as needed
# Test and validate
python core/scripts/automation/validate-overlays.py .
python core/scripts/automation/test-overlays.py .
```

### 3. Deploy to Production

```bash
# Validate production overlays
python core/scripts/automation/validate-overlays.py core/deployment/overlays/composed/production-suite

# Test in staging first
python core/scripts/automation/overlay-cli.py apply core/deployment/overlays/composed/production-suite --dry-run -n staging

# Deploy to production
python core/scripts/automation/overlay-cli.py apply core/deployment/overlays/composed/production-suite -n production

# Monitor deployment
kubectl get pods -n production
kubectl logs -n production -l overlay=production-suite
```

### 4. Join the Community

```bash
# Register your overlay in the catalog
python core/scripts/automation/overlay-registry.py register core/deployment/overlays/core/ai/skills/my-overlay

# Contribute to community
git checkout -b feature/my-overlay
git add .
git commit -m "Add my-overlay: Custom capability for specific use case"
git push origin feature/my-overlay
# Create pull request on GitHub
```

## Quick Reference

### Essential Commands

```bash
# List overlays
python core/scripts/automation/overlay-cli.py list

# Create overlay
python core/scripts/automation/overlay-cli.py create name category base --template template

# Validate overlay
python core/scripts/automation/overlay-cli.py validate overlay-path

# Test overlay
python core/scripts/automation/overlay-cli.py test overlay-path

# Build overlay
python core/scripts/automation/overlay-cli.py build overlay-path --output manifest.yaml

# Apply overlay
python core/scripts/automation/overlay-cli.py apply overlay-path --dry-run

# Search overlays
python core/scripts/automation/overlay-cli.py search keyword

# Update catalog
python core/scripts/automation/overlay-cli.py update-catalog
```

### Directory Structure

```
overlay/
├── ai/skills/                # Skill overlays
│   ├── debug/              # Enhanced debugging skill
│   ├── infrastructure-provisioning/
│   └── ...
├── core/ai/runtime/                 # Dashboard overlays
│   ├── themes/
│   └── widgets/
├── core/operators/          # Infrastructure overlays
│   ├── monitoring/
│   ├── security/
│   └── backup/
├── composed/               # Composed overlays
│   ├── enterprise-suite/
│   ├── community-bundle/
│   └── development-env/
├── templates/              # Overlay templates
└── registry/              # Overlay catalog
```

### File Templates

#### overlay-metadata.yaml
```yaml
---
name: overlay-name
version: "1.0.0"
description: "Brief description"
category: skills|dashboard|infrastructure|composed
base_path: "path/to/base"
license: "AGPLv3"
risk_level: low|medium|high
autonomy: fully_auto|conditional|requires_pr

maintainer:
  name: "Your Name"
  email: "your.email@example.com"
  organization: "Your Organization"

tags:
  - relevant-tag
  - another-tag

compatibility:
  min_base: "1.0.0"
  kubernetes: ">=1.20"

dependencies:
  - name: "dependency-name"
    version: ">=1.0.0"
    optional: false

examples:
  - name: "Example usage"
    description: "Description of example"
    command: "command to run"
    expected_output: "Expected result"
```

#### kustomization.yaml
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: overlay-name
  namespace: flux-system
  annotations:
    overlay.name: "overlay-name"
    overlay.version: "1.0.0"
    overlay.category: "skills"
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/enhanced-features.yaml
configMapGenerator:
  - name: overlay-config
    literals:
      - OVERLAY_ENABLED=true
      - OVERLAY_VERSION="1.0.0"
commonLabels:
  overlay: "overlay-name"
  overlay-type: "skill"
  managed-by: "kustomize"
```

---

## 🎉 **You're Ready!**

With this quick start guide, you can:

1. ✅ **Understand** the overlay system architecture
2. ✅ **Install** and configure the overlay tools
3. ✅ **Create** your first overlay in minutes
4. ✅ **Deploy** overlays to development and production
5. ✅ **Troubleshoot** common issues
6. ✅ **Extend** the system with custom overlays

**Start building your overlays today!** 🚀

For more detailed information, refer to:
- **[User Guide](OVERLAY-USER-GUIDE.md)**: Comprehensive documentation
- **[Developer Guide](OVERLAY-DEVELOPER-GUIDE.md)**: Development guidelines
- **[Examples](OVERLAY-EXAMPLES.md)**: Real-world use cases
- **[Community Guide](OVERLAY-COMMUNITY-GUIDE.md)**: Community resources

---

*Last updated: March 2026*
