# 🔄 Kubernetes Jobs Orchestration with Flux

## 🎯 Overview

This guide explains how to implement comprehensive job orchestration with Flux for pre-deployment and post-deployment tasks in your GitOps pipeline.

---

## 🏗 Architecture

### **Deployment Pipeline**

```
Pre-Deploy Jobs → Application Deployment → Post-Deploy Jobs → Monitoring
       ↓                    ↓                    ↓              ↓
  Database Backup    Application Update    Cache Refresh    Health Checks
  Database Migration    Rollout Status    Health Checks    Metrics Collection
  Environment Prep    Service Update    Index Rebuild    Alert Verification
```

### **Job Categories**

- **Pre-Deploy**: Database migrations, backups, environment preparation
- **Deploy**: Application deployment with dependency management
- **Post-Deploy**: Cache refresh, health checks, monitoring setup

---

## 📋 Job Types

### **🔄 Pre-Deployment Jobs**

#### **Database Migration Job**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration
spec:
  template:
    spec:
      containers:
      - name: migration
        image: ghcr.io/lloydchang/gitops-infra-control-plane:latest
        command: ["/scripts/migrate.sh"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
```

#### **Database Backup Job**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: database-backup
spec:
  template:
    spec:
      containers:
      - name: backup
        image: ghcr.io/lloydchang/gitops-infra-control-plane:latest
        command: ["sh", "-c", "create_backup.sh"]
        volumeMounts:
        - name: backup-storage
          mountPath: /backups
```

### **🚀 Application Deployment**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: application-deployment
spec:
  dependsOn:
    - name: pre-deploy-jobs
  path: "./infrastructure/tenants/3-workloads/sample-apps"
  wait: true
```

### **📊 Post-Deployment Jobs**

#### **Cache Refresh Job**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: cache-refresh
spec:
  template:
    spec:
      containers:
      - name: cache-refresh
        image: ghcr.io/lloydchang/gitops-infra-control-plane:latest
        command: ["/scripts/refresh_cache.sh"]
```

#### **Health Check Job**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: health-check
spec:
  template:
    spec:
      containers:
      - name: health-check
        image: ghcr.io/lloydchang/gitops-infra-control-plane:latest
        command: ["/scripts/health_check.sh"]
```

---

## 🔧 Flux Configuration

### **Dependency Management**

```yaml
# Pre-Deploy Jobs
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: pre-deploy-jobs
spec:
  dependsOn:
    - name: infrastructure-controllers
  path: "./infrastructure/tenants/3-workloads/job-orchestration/pre-deploy"
  force: true
  wait: true

# Application Deployment
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: application-deployment
spec:
  dependsOn:
    - name: pre-deploy-jobs
  path: "./infrastructure/tenants/3-workloads/sample-apps"
  wait: true

# Post-Deploy Jobs
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: post-deploy-jobs
spec:
  dependsOn:
    - name: application-deployment
  path: "./infrastructure/tenants/3-workloads/job-orchestration/post-deploy"
  force: true
  wait: true
```

### **Key Configuration Options**

- **force: true**: Recreate jobs when immutable fields change
- **wait: true**: Wait for jobs to complete before marking as ready
- **timeout: 15m**: Maximum time to wait for job completion
- **dependsOn**: Explicit dependency management

---

## 📁 Repository Structure

```
infrastructure/tenants/3-workloads/job-orchestration/
├── pre-deploy/
│   ├── database-migration.job.yaml
│   ├── backup.job.yaml
│   └── kustomization.yaml
├── post-deploy/
│   ├── cache-refresh.job.yaml
│   ├── health-check.job.yaml
│   └── kustomization.yaml
├── config/
│   ├── job-config.yaml
│   └── migration-scripts.yaml
├── flux-kustomizations.yaml
└── kustomization.yaml
```

---

## 🚀 Deployment Workflow

### **1. Pre-Deployment Phase**

```bash
# Flux starts pre-deploy jobs
flux reconcile kustomization pre-deploy-jobs

# Jobs run in sequence:
# 1. Database backup
# 2. Database migration
# 3. Environment preparation

# Monitor job status
kubectl get jobs -l phase=pre-deploy
kubectl logs job/database-migration
```

### **2. Application Deployment**

```bash
# Flux waits for pre-deploy jobs to complete
# Then starts application deployment
flux reconcile kustomization application-deployment

# Monitor deployment
kubectl get deployments
kubectl rollout status deployment/sample-app
```

### **3. Post-Deployment Phase**

```bash
# Flux starts post-deploy jobs after app deployment
flux reconcile kustomization post-deploy-jobs

# Jobs run in sequence:
# 1. Cache refresh
# 2. Health checks
# 3. Monitoring setup

# Monitor job status
kubectl get jobs -l phase=post-deploy
kubectl logs job/health-check
```

---

## 📊 Monitoring & Observability

### **Job Status Monitoring**

```bash
# Check all jobs
kubectl get jobs -l component=job-orchestration

# Check job details
kubectl describe job database-migration

# Check job logs
kubectl logs job/database-migration

# Check job history
kubectl get jobs -o wide --sort-by=.metadata.creationTimestamp
```

### **Flux Status Monitoring**

```bash
# Check kustomization status
flux get kustomizations

# Check reconciliation status
flux get kustomization pre-deploy-jobs
flux get kustomization application-deployment
flux get kustomization post-deploy-jobs
```

### **Alerting Setup**

```yaml
# Job failure alert
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: job-failure-alert
spec:
  providerRef:
    name: slack-bot
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      name: pre-deploy-jobs
    - kind: Kustomization
      name: post-deploy-jobs
```

---

## 🔧 Configuration Management

### **Job Configuration**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: job-config
data:
  APP_VERSION: "latest"
  ENVIRONMENT: "production"
  DATABASE_TYPE: "postgresql"
  CACHE_TYPE: "redis"
  HEALTH_CHECK_TIMEOUT: "300"
  JOB_TIMEOUT: "1800"
```

### **Migration Scripts**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: migration-scripts
data:
  migrate.sh: |
    #!/bin/bash
    echo "🔄 Starting database migration..."
    psql "$DATABASE_URL" -f /scripts/migrations/001_initial_schema.sql
    echo "✅ Migration completed!"
```

---

## 🎯 Best Practices

### **Job Design**

- **Idempotency**: Jobs should be safe to run multiple times
- **Error Handling**: Proper error handling and rollback capabilities
- **Timeouts**: Set appropriate timeouts for job completion
- **Resource Limits**: Define CPU and memory limits

### **Flux Configuration**

- **Dependencies**: Use explicit `dependsOn` for proper sequencing
- **Force**: Use `force: true` for job recreation on changes
- **Wait**: Use `wait: true` to ensure job completion
- **Timeout**: Set reasonable timeouts for job execution

### **Security**

- **Secrets**: Use Kubernetes secrets for sensitive data
- **RBAC**: Implement proper role-based access control
- **Network Policies**: Restrict network access for jobs
- **Pod Security**: Use restrictive pod security policies

---

## 🔍 Troubleshooting

### **Common Issues**

#### **Job Not Starting**

```bash
# Check kustomization status
flux get kustomization pre-deploy-jobs

# Check dependencies
flux tree kustomization pre-deploy-jobs

# Check events
kubectl get events --field-selector involvedObject.name=database-migration
```

#### **Job Failing**

```bash
# Check job status
kubectl describe job database-migration

# Check pod logs
kubectl logs job/database-migration

# Check job conditions
kubectl get job database-migration -o yaml
```

#### **Dependencies Not Working**

```bash
# Check dependency chain
flux get kustomizations

# Verify dependsOn configuration
kubectl get kustomization application-deployment -o yaml

# Check reconciliation status
flux reconcile kustomization application-deployment --with-source
```

---

## 🎉 Benefits

### **Deployment Safety**

- **Pre-Deploy Validation**: Database migrations before deployment
- **Rollback Protection**: Backup creation before changes
- **Health Verification**: Post-deployment health checks

### **Operational Excellence**

- **Automated Workflows**: Hands-off deployment pipeline
- **Dependency Management**: Proper sequencing of operations
- **Error Handling**: Automatic failure detection and rollback

### **Observability**

- **Job Tracking**: Complete visibility into job execution
- **Health Monitoring**: Continuous health verification
- **Alert Integration**: Real-time failure notifications

---

## 📚 Advanced Features

### **Rollback Jobs**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: rollback-job
spec:
  template:
    spec:
      containers:
      - name: rollback
        image: ghcr.io/lloydchang/gitops-infra-control-plane:latest
        command: ["/scripts/rollback.sh"]
```

### **Canary Deployments**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: canary-deployment
spec:
  dependsOn:
    - name: pre-deploy-jobs
  patchesStrategicMerge:
  - canary-patch.yaml
```

### **Blue-Green Deployments**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: blue-green-deployment
spec:
  dependsOn:
    - name: pre-deploy-jobs
  patchesStrategicMerge:
  - blue-green-patch.yaml
```

The Kubernetes Jobs orchestration with Flux provides enterprise-grade deployment automation with comprehensive pre and post-deployment job management! 🚀
