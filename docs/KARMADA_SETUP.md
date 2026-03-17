# 🌐 Karmada + Flux Multi-Cluster GitOps Setup

## 🎯 Overview

This guide explains how to set up Karmada with Flux for managing multi-cluster GitOps deployments across multiple Kubernetes clusters.

---

## 🏗 Architecture

### **Karmada Control Plane**

- **Central Management**: Single control plane managing multiple clusters
- **Resource Templates**: Flux CRDs as templates, not instances
- **Propagation Policies**: Control which resources go to which clusters
- **Override Policies**: Customize resources per cluster

### **Flux Integration**

- **Control Plane**: Flux CRDs only (no controllers)
- **Member Clusters**: Full Flux controllers for reconciliation
- **GitOps**: Central Git repository managing all clusters
- **Dependency Management**: Proper sequencing across clusters

---

## 🚀 Quick Start

### **Prerequisites**

```bash
# Install required tools
brew install kind kubectl flux

# Or download binaries
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
curl -LO "https://github.com/kubernetes-sigs/kind/releases/download/v0.20.0/kind-darwin-amd64"
curl -s https://fluxcd.io/install.sh | sudo bash
```

### **Setup Karmada + Flux**

```bash
# Run the setup script
./core/operators/karmada/setup-karmada.sh

# Or manual setup:
git clone https://github.com/karmada-io/karmada
cd karmada
./hack/local-up-karmada.sh

# Install Flux CRDs in control plane
kubectl apply -k github.com/fluxcd/flux2/manifests/crds?ref=main --kubeconfig ~/.kube/karmada.config

# Install Flux controllers in member clusters
flux install --kubeconfig ~/.kube/members.config --context member1
flux install --kubeconfig ~/.kube/members.config --context member2
flux install --kubeconfig ~/.kube/members.config --context member3
```

---

## 📊 Multi-Cluster Configuration

### **Helm Repository & Release**

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: gitops-infra
  namespace: gitops-multi-cluster
spec:
  interval: 5m
  url: https://stefanprodan.github.io/podinfo
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: gitops-infrastructure
  namespace: gitops-multi-cluster
spec:
  interval: 10m
  chart:
    spec:
      chart: podinfo
      version: 6.5.0
      sourceRef:
        kind: HelmRepository
        name: gitops-infra
```

### **Propagation Policy**

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: gitops-infra-policy
  namespace: gitops-multi-cluster
spec:
  resourceSelectors:
    - apiVersion: source.toolkit.fluxcd.io/v1
      kind: HelmRepository
      name: gitops-infra
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: gitops-infrastructure
  placement:
    clusterAffinity:
      clusterNames:
        - member1
        - member2
        - member3
```

### **Override Policy**

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: OverridePolicy
metadata:
  name: gitops-infra-production
  namespace: gitops-multi-cluster
spec:
  resourceSelectors:
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: gitops-infrastructure
  overrideRules:
    - targetCluster:
        clusterNames:
          - member1
      overriders:
        plaintext:
          - path: "/spec/values"
            operator: add
            value:
              replicaCount: 5
              resources:
                limits:
                  cpu: 1000m
                  memory: 1Gi
```

---

## 🎯 Cluster-Specific Configurations

### **Production Cluster (member1)**

- **Replicas**: 5 instances
- **Resources**: High CPU/memory allocation
- **Node Selector**: Production nodes only
- **Tolerations**: Production workload tolerations
- **Affinity**: Pod anti-affinity for high availability

### **Staging Cluster (member2)**

- **Replicas**: 3 instances
- **Resources**: Medium allocation
- **Node Selector**: Staging nodes
- **Autoscaling**: Enabled with moderate limits

### **Development Cluster (member3)**

- **Replicas**: 1 instance
- **Resources**: Low allocation
- **Node Selector**: Development nodes
- **Autoscaling**: Disabled for cost efficiency

---

## 📈 Multi-Cluster Monitoring

### **Prometheus + Grafana Setup**

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: multi-cluster-prometheus
  namespace: multi-cluster-monitoring
spec:
  values:
    prometheus:
      prometheusSpec:
        externalLabels:
          cluster: '{{ .Values.global.clusterName }}'
          region: '{{ .Values.global.region }}'
    global:
      clusterName: multi-cluster
      region: us-west-2
```

### **Monitoring Features**

- **Multi-Cluster Metrics**: Prometheus across all clusters
- **Centralized Grafana**: Single dashboard for all clusters
- **Cluster Labels**: Distinguish metrics by cluster
- **Alerting**: Cluster-specific alerting rules

---

## 🔧 Advanced Features

### **Spread Constraints**

```yaml
placement:
  clusterAffinity:
    clusterNames:
      - member1
      - member2
      - member3
  spreadConstraints:
    - spreadByField: cluster
      maxSkew: 1
      whenUnsatisfiable: DoNotSchedule
```

### **Dependency Management**

```yaml
spec:
  dependsOn:
    - name: gitops-infra-policy
    - name: monitoring-policy
```

### **Resource Templates**

- **Control Plane**: Flux CRDs as templates
- **Member Clusters**: Actual resource instances
- **Work Encapsulation**: Work objects for delivery
- **Reconciliation**: Member cluster controllers

---

## 🚀 Deployment Workflow

### **1. Setup Phase**

```bash
# 1. Start Karmada control plane
./hack/local-up-karmada.sh

# 2. Install Flux CRDs in control plane
kubectl apply -k github.com/fluxcd/flux2/manifests/crds?ref=main --kubeconfig ~/.kube/karmada.config

# 3. Install Flux controllers in member clusters
for cluster in member1 member2 member3; do
  flux install --kubeconfig ~/.kube/members.config --context $cluster
done
```

### **2. Configuration Phase**

```bash
# Apply multi-cluster GitOps configuration
kubectl apply -f core/operators/karmada/multi-cluster-gitops.yaml --kubeconfig ~/.kube/karmada.config

# Verify propagation
kubectl get propagationpolicies -A --kubeconfig ~/.kube/karmada.config
kubectl get overridepolicies -A --kubeconfig ~/.kube/karmada.config
```

### **3. Verification Phase**

```bash
# Check deployments in each cluster
for cluster in member1 member2 member3; do
  echo "=== $cluster ==="
  kubectl get pods -n gitops-multi-cluster --kubeconfig ~/.kube/members.config --context $cluster
  helm list -n gitops-multi-cluster --kubeconfig ~/.kube/members.config --context $cluster
done
```

---

## 📊 Monitoring & Observability

### **Cluster Status**

```bash
# Check Karmada cluster status
kubectl get clusters --kubeconfig ~/.kube/karmada.config

# Check propagation status
kubectl get propagationpolicies -A --kubeconfig ~/.kube/karmada.config

# Check resource status
kubectl get work -A --kubeconfig ~/.kube/karmada.config
```

### **Flux Status**

```bash
# Check Flux status in each member cluster
for cluster in member1 member2 member3; do
  echo "=== Flux Status in $cluster ==="
  flux get all --kubeconfig ~/.kube/members.config --context $cluster
done
```

### **Application Status**

```bash
# Check application deployments
for cluster in member1 member2 member3; do
  echo "=== Application Status in $cluster ==="
  kubectl get deployments -n gitops-multi-cluster --kubeconfig ~/.kube/members.config --context $cluster
  kubectl get services -n gitops-multi-cluster --kubeconfig ~/.kube/members.config --context $cluster
done
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### **Propagation Not Working**

```bash
# Check propagation policy status
kubectl describe propagationpolicy gitops-infra-policy -n gitops-multi-cluster --kubeconfig ~/.kube/karmada.config

# Check work status
kubectl get work -n gitops-multi-cluster --kubeconfig ~/.kube/karmada.config
kubectl describe work <work-name> -n gitops-multi-cluster --kubeconfig ~/.kube/karmada.config
```

#### **Flux Reconciliation Issues**

```bash
# Check Flux status in member cluster
flux get kustomizations --kubeconfig ~/.kube/members.config --context member1

# Check Flux events
kubectl get events -n flux-system --kubeconfig ~/.kube/members.config --context member1
```

#### **Override Policy Not Applied**

```bash
# Check override policy status
kubectl describe overridepolicy gitops-infra-production -n gitops-multi-cluster --kubeconfig ~/.kube/karmada.config

# Verify applied overrides
kubectl get helmrelease gitops-infrastructure -n gitops-multi-cluster -o yaml --kubeconfig ~/.kube/members.config --context member1
```

---

## 🎉 Benefits

### **Multi-Cluster Management**

- **Single Control Plane**: Manage multiple clusters from one place
- **Centralized GitOps**: Single Git repository for all clusters
- **Resource Templates**: Reuse configurations across clusters
- **Cluster Customization**: Override policies per cluster

### **Enterprise Features**

- **High Availability**: Spread across multiple clusters
- **Disaster Recovery**: Multi-cluster resilience
- **Load Distribution**: Intelligent workload placement
- **Cost Optimization**: Right-size resources per cluster

### **Operational Excellence**

- **Consistent Deployments**: Same application across clusters
- **Cluster-Specific Tuning**: Optimize per environment
- **Centralized Monitoring**: Single view of all clusters
- **Automated Rollouts**: GitOps-driven deployments

---

## 📚 Next Steps

1. **Scale Up**: Add more member clusters
2. **Advanced Policies**: Implement complex propagation rules
3. **GitOps Integration**: Connect with existing Git workflows
4. **Monitoring**: Set up comprehensive multi-cluster monitoring
5. **Security**: Implement RBAC and network policies

---

## 🔄 Integration with Control Plane

### **Kustomization Structure**

The Karmada configuration is now fully integrated into the GitOps infrastructure control plane:

```yaml
# Root level kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - core/operators/
labels:
  - pairs:
      managed-by: flux
      component: gitops-infra-control-plane
      platform: multi-cluster-gitops

# core/operators/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - flux/gotk-components.yaml
  - flux/gotk-sync.yaml
  - flux/image-update-automation.yaml
  - flux/image-policy.yaml
  - controllers/
  - karmada/          # ← Karmada multi-cluster setup
  - monitoring/
```

### **Deployment Commands**

```bash
# Deploy entire control plane including Karmada
kubectl apply -k .

# Deploy only Karmada components
kubectl apply -k core/operators/karmada/

# Verify Karmada integration
kubectl get propagationpolicies -A
kubectl get overridepolicies -A
kubectl get work -A
```

The Karmada + Flux integration provides enterprise-grade multi-cluster GitOps capabilities with centralized management and cluster-specific customization! 🚀
