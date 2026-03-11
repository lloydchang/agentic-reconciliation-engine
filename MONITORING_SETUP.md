# 📊 GitOps Infrastructure Control Plane - Monitoring Setup Guide

## 🎯 Overview

This guide explains how to configure and use the comprehensive monitoring and alerting system implemented for the GitOps Infrastructure Control Plane.

---

## 🔔 **Alert Configuration**

### **Slack Integration**

#### **1. Create Slack Bot Token**
```bash
# Create Slack app and get bot token
# Visit: https://api.slack.com/apps
# Create new app → Bot → Add to Slack workspace
# Copy Bot User OAuth Token (starts with xoxb-)

# Create secret in Kubernetes
kubectl create secret generic slack-bot-token \
  --from-literal=token=xoxb-YOUR-SLACK-BOT-TOKEN \
  --namespace=flux-system
```

#### **2. Configure Slack Provider**
The Slack provider is already configured in `control-plane/monitoring/alerts/slack-provider.yaml`:
- **Channel**: `gitops-alerts` (change as needed)
- **Namespace**: `flux-system`
- **Auto-deployed**: Via monitoring kustomization

### **GitHub Integration**

#### **1. Create GitHub Token**
```bash
# Create personal access token with repo:write, repo:status scopes
# Visit: https://github.com/settings/tokens

# Create secret in Kubernetes
kubectl create secret generic github-token \
  --from-literal=token=ghp_YOUR-GITHUB-TOKEN \
  --namespace=flux-system
```

#### **2. Configure GitHub Provider**
The GitHub provider is already configured in `control-plane/monitoring/alerts/github-provider.yaml`:
- **Repository**: `lloydchang/gitops-infra-control-plane`
- **Namespace**: `flux-system`
- **Auto-deployed**: Via monitoring kustomization

---

## 📋 **Alert Types**

### **Error Alerts** (`gitops-pipeline-alerts`)
Triggered on:
- ❌ Kustomization build failures
- ❌ Resource apply errors
- ❌ Health check failures
- ❌ Git repository sync issues
- ❌ Cloud controller failures

### **Info Alerts** (`gitops-deployment-alerts`)
Triggered on:
- ✅ Successful resource creation
- ✅ Successful resource updates
- ✅ Successful resource deletions
- ✅ Health check passing
- ✅ Dependency chain execution

---

## 🔄 **GitHub Integration Benefits**

### **Commit Status Updates**
- 🟢 **Green checkmark**: Deployment succeeded
- 🔴 **Red cross**: Deployment failed
- 📊 **Click icon**: Detailed deployment information

### **Deployment Loop Closure**
- Traditional push-based CD: Manual verification
- Flux GitOps: Automatic status feedback
- **Benefit**: Immediate deployment visibility

---

## 🤖 **Automated Workflows**

### **Weekly Flux Upgrades**
```yaml
# .github/workflows/flux-upgrade.yml
- Schedule: Weekly (Sunday midnight)
- Action: Detect updates → Create PR
- Benefits: Security patches, bug fixes
```

### **OCI Manifest Publishing**
```yaml
# .github/workflows/push-manifests.yml
- Trigger: Push to main branch
- Action: Build → Push to GHCR
- Artifacts: 
  - ghcr.io/lloydchang/gitops-manifests:infrastructure
  - ghcr.io/lloydchang/gitops-manifests:workloads
- Tags: staging, production
```

### **E2E Testing**
```yaml
# .github/workflows/e2e-testing.yml
- Trigger: Push + PR
- Action: Kind cluster → Deploy → Test
- Validation: Full GitOps pipeline
- Output: Detailed test reports
```

---

## 📊 **Monitoring Dashboard Integration**

### **Grafana Setup**
```bash
# Grafana provider already configured
# Address: http://kube-prometheus-stack-grafana.monitoring/api/annotations
# Events: All Flux notifications
# Dashboard: Automatic event visualization
```

### **Prometheus Metrics**
- Flux controller metrics
- Kustomization reconciliation times
- Resource deployment counts
- Error rates and success rates

---

## 🚀 **Quick Start**

### **1. Configure Secrets**
```bash
# Slack token
kubectl create secret generic slack-bot-token \
  --from-literal=token=YOUR_SLACK_TOKEN \
  --namespace=flux-system

# GitHub token  
kubectl create secret generic github-token \
  --from-literal=token=YOUR_GITHUB_TOKEN \
  --namespace=flux-system
```

### **2. Deploy Monitoring**
```bash
# Monitoring is already included in main Flux deployment
# Apply the monitoring kustomization
kubectl apply -f control-plane/monitoring/kustomization.yaml

# Verify alerts are configured
flux get alerts
```

### **3. Test Alerts**
```bash
# Trigger a test alert
flux reconcile kustomization infrastructure-controllers

# Check Slack for notifications
# Check GitHub for commit status updates
```

---

## 🎯 **Alert Routing**

### **Team-Specific Channels**
```yaml
# Example: Different alerts to different channels
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: on-call-alerts
  namespace: flux-system
spec:
  providerRef:
    name: slack-bot
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      name: '*'
  # Custom routing to on-call channel
  summary: "On-call GitOps Alerts"
```

### **Environment-Specific Routing**
```yaml
# Example: Separate prod vs dev alerts
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: production-alerts
  namespace: flux-system
spec:
  eventMetadata:
    env: "production"
  providerRef:
    name: slack-bot
  eventSeverity: error
```

---

## 📈 **Best Practices**

### **Alert Configuration**
- ✅ Use descriptive alert names and summaries
- ✅ Include relevant metadata (env, cluster, region)
- ✅ Set appropriate severity levels (error vs info)
- ✅ Route to correct teams/channels

### **Secret Management**
- ✅ Use Kubernetes secrets, not hardcoded values
- ✅ Rotate tokens regularly
- ✅ Limit secret access to necessary namespaces
- ✅ Use least-privilege principle

### **Monitoring Coverage**
- ✅ Monitor all critical GitOps components
- ✅ Track dependency chain health
- ✅ Alert on reconciliation failures
- ✅ Provide deployment success feedback

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Slack Notifications Not Working**
```bash
# Check provider status
flux get providers

# Check secret exists
kubectl get secret slack-bot-token -n flux-system

# Check alert status
flux get alerts
```

#### **GitHub Status Not Updating**
```bash
# Check GitHub token permissions
# Ensure repo:write and repo:status scopes

# Check provider status
flux get providers

# Check recent events
kubectl get events -n flux-system --sort-by='.lastTimestamp'
```

#### **Alerts Not Triggering**
```bash
# Check kustomization status
flux get kustomizations

# Check for reconciliation events
kubectl get events -n flux-system --field-selector reason=ReconciliationFailed
```

---

## 🎉 **Production Readiness**

Your GitOps Infrastructure Control Plane now includes:

✅ **Real-time alerting** via Slack and GitHub
✅ **Automated workflows** for upgrades and testing  
✅ **Enterprise monitoring** with Grafana integration
✅ **Comprehensive visibility** into GitOps operations
✅ **Automated security updates** and dependency management

The monitoring system is production-ready and will provide immediate visibility into your multi-cloud infrastructure operations!
