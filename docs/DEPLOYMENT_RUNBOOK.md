# AI Infrastructure Portal - Deployment Runbook

## Overview
This runbook provides comprehensive procedures for deploying the AI Infrastructure Portal across different environments (development, staging, production) using Kubernetes and related infrastructure components.

## Prerequisites

### Infrastructure Requirements
- Kubernetes cluster (v1.24+) with kubectl access
- Helm 3.x installed
- Docker registry access (GitHub Container Registry recommended)
- External load balancer or ingress controller
- Persistent storage for database and logs

### Access Requirements
- Cluster-admin permissions for initial setup
- Docker registry credentials
- Database credentials (if using external DB)
- SSL/TLS certificates for production

### Network Requirements
- DNS records configured for portal domains
- Firewall rules allowing traffic on required ports
- VPN or secure access for administrative operations

## Environment Setup

### 1. Cluster Preparation

#### Create Namespace
```bash
kubectl create namespace ai-infrastructure
```

#### Configure RBAC
```bash
# Apply service account and RBAC policies
kubectl apply -f dashboard/overlay/rbac.yaml

# Verify service account creation
kubectl get serviceaccounts -n ai-infrastructure
```

#### Set up Secrets
```bash
# Create Docker registry secret
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  --namespace=ai-infrastructure

# Create database secrets (if using external DB)
kubectl create secret generic db-secret \
  --from-literal=username=<db-user> \
  --from-literal=password=<db-password> \
  --namespace=ai-infrastructure

# Create TLS certificates
kubectl create secret tls ai-portal-tls \
  --cert=<path-to-cert> \
  --key=<path-to-key> \
  --namespace=ai-infrastructure
```

### 2. Ingress Controller Setup

#### Install NGINX Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ai-infrastructure \
  --set controller.replicas=2 \
  --set controller.metrics.enabled=true
```

#### Configure Ingress
```bash
# Apply ingress configuration
kubectl apply -f dashboard/overlay/services-and-ingress.yaml

# Verify ingress creation
kubectl get ingress -n ai-infrastructure
```

## Deployment Procedures

### Development Environment Deployment

#### Quick Start (Docker Compose)
```bash
# Clone repository
git clone <repository-url>
cd agentic-reconciliation-engine

# Start services
./scripts/services/start-real-services.sh

# Verify deployment
curl http://localhost:5001/api/health
curl http://localhost:8081/health
```

#### Kubernetes Deployment (Dev)
```bash
# Deploy to development namespace
kubectl apply -f dashboard/overlay/dashboard-backend-code.yaml

# Wait for rollout
kubectl rollout status deployment/ai-infrastructure-portal -n ai-infrastructure

# Check pod status
kubectl get pods -n ai-infrastructure
```

### Staging Environment Deployment

#### Automated Deployment (CI/CD)
Staging deployments are automatically triggered by GitHub Actions on merge to `main` branch.

#### Manual Deployment (if needed)
```bash
# Update image tags for staging
export TAG=$(git rev-parse HEAD)
sed -i "s|ai-infrastructure-portal:.*|ai-infrastructure-portal:$TAG|g" dashboard/overlay/dashboard-backend-k8s-real.yaml

# Deploy to staging
kubectl apply -f dashboard/overlay/dashboard-backend-k8s-real.yaml

# Verify deployment
kubectl get pods -l environment=staging -n ai-infrastructure
```

### Production Environment Deployment

#### Blue-Green Deployment Strategy

##### Phase 1: Prepare Green Environment
```bash
# Create green deployment (new version)
kubectl apply -f dashboard/overlay/dashboard-backend-k8s-real.yaml

# Tag green deployment
kubectl label deployment ai-infrastructure-portal-green version=$NEW_VERSION -n ai-infrastructure

# Update green deployment with new images
kubectl set image deployment/ai-infrastructure-portal-green \
  ai-infrastructure-portal=ghcr.io/<org>/ai-infrastructure-portal:$NEW_VERSION \
  -n ai-infrastructure
```

##### Phase 2: Health Checks
```bash
# Wait for green deployment to be ready
kubectl rollout status deployment/ai-infrastructure-portal-green -n ai-infrastructure

# Run health checks
node health-checker.js https://api.ai-infrastructure-portal.com

# Run performance tests
npm test -- --grep "performance"
```

##### Phase 3: Traffic Switching
```bash
# Switch ingress to green deployment
kubectl patch ingress ai-infrastructure-portal-ingress \
  -p '{"spec":{"rules":[{"host":"api.ai-infrastructure-portal.com","http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"ai-infrastructure-portal-green","port":{"number":5001}}}}]}}]}}' \
  -n ai-infrastructure

# Wait for traffic to stabilize (5 minutes)
sleep 300

# Monitor error rates and latency
kubectl logs -l app=ai-infrastructure-portal-green -n ai-infrastructure --tail=100
```

##### Phase 4: Verification and Cleanup
```bash
# Verify production health
curl https://api.ai-infrastructure-portal.com/api/health

# If successful, scale down blue deployment
kubectl scale deployment ai-infrastructure-portal --replicas=0 -n ai-infrastructure

# Update production tags
kubectl label deployment ai-infrastructure-portal-green version=production -n ai-infrastructure
kubectl label deployment ai-infrastructure-portal-green version=production -n ai-infrastructure

# Rename green to blue for next deployment
kubectl get deployment ai-infrastructure-portal-green -o yaml | \
  sed 's/name: ai-infrastructure-portal-green/name: ai-infrastructure-portal/' | \
  kubectl apply -f -
```

## Scaling Configuration

### Horizontal Pod Autoscaling (HPA)

#### Configure HPA for API Service
```bash
kubectl apply -f dashboard/overlay/hpa.yaml

# Verify HPA configuration
kubectl get hpa -n ai-infrastructure

# Monitor scaling events
kubectl describe hpa ai-portal-api-hpa -n ai-infrastructure
```

#### Configure HPA for Dashboard Service
```bash
kubectl apply -f dashboard/overlay/hpa.yaml

# Check dashboard HPA status
kubectl get hpa ai-portal-dashboard-hpa -n ai-infrastructure
```

### Vertical Pod Autoscaling (VPA)

#### Install VPA Controller
```bash
# Add VPA Helm repository
helm repo add fairwinds-stable https://charts.fairwinds.com/stable
helm repo update

# Install VPA
helm install vpa fairwinds-stable/vpa \
  --namespace ai-infrastructure \
  --version 1.7.5
```

#### Apply VPA Policies
```bash
kubectl apply -f dashboard/overlay/vpa.yaml

# Check VPA recommendations
kubectl get vpa -n ai-infrastructure
kubectl describe vpa ai-portal-api-vpa -n ai-infrastructure
```

### Cluster Autoscaling

#### Enable Cluster Autoscaler
```bash
# For AWS EKS
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=<cluster-name> \
  --set awsRegion=<region>
```

## Monitoring Setup

### Install Prometheus and Grafana

#### Prometheus Stack
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

#### Service Monitors
```bash
kubectl apply -f dashboard/overlay/service-monitors.yaml

# Verify service monitors
kubectl get servicemonitors -n ai-infrastructure
```

### Configure Alerting

#### Prometheus Rules
```bash
kubectl apply -f dashboard/overlay/prometheus-rules.yaml

# Check alerting rules
kubectl get prometheusrules -n ai-infrastructure
```

#### AlertManager Configuration
```bash
# Configure notification channels
kubectl create secret generic alertmanager-config \
  --from-file=alertmanager.yaml \
  --namespace monitoring
```

## Backup and Recovery

### Automated Backups

#### Configure Backup CronJobs
```bash
kubectl apply -f dashboard/overlay/backup-restore.yaml

# Verify backup jobs
kubectl get cronjobs -n ai-infrastructure
```

#### Manual Backup
```bash
# Trigger immediate backup
kubectl create job manual-backup --from=cronjob/automated-backup -n ai-infrastructure

# Check backup status
kubectl logs job/manual-backup -n ai-infrastructure
```

### Disaster Recovery

#### Failover Procedures
```bash
# Switch to secondary region (if configured)
kubectl apply -f dashboard/overlay/disaster-recovery.yaml

# Update DNS to point to secondary region
# This would typically be automated with a DNS service
```

## Troubleshooting

### Common Deployment Issues

#### Pods Not Starting
```bash
# Check pod status
kubectl get pods -n ai-infrastructure

# Check pod logs
kubectl logs <pod-name> -n ai-infrastructure

# Check events
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp'
```

#### Image Pull Errors
```bash
# Check image pull secrets
kubectl get secrets -n ai-infrastructure

# Verify registry access
kubectl describe pod <pod-name> -n ai-infrastructure
```

#### Service Mesh Issues
```bash
# Check Istio sidecar injection
kubectl get pods -o jsonpath='{.items[*].spec.containers[*].name}' -n ai-infrastructure

# Verify Istio configuration
kubectl get virtualservices -n ai-infrastructure
```

### Rollback Procedures

#### Quick Rollback
```bash
# Rollback to previous deployment
kubectl rollout undo deployment/ai-infrastructure-portal -n ai-infrastructure

# Rollback to specific revision
kubectl rollout undo deployment/ai-infrastructure-portal --to-revision=2 -n ai-infrastructure
```

#### Emergency Rollback
```bash
# Scale down problematic deployment
kubectl scale deployment ai-infrastructure-portal --replicas=0 -n ai-infrastructure

# Scale up previous version
kubectl scale deployment ai-infrastructure-portal-previous --replicas=3 -n ai-infrastructure
```

## Post-Deployment Validation

### Health Checks
```bash
# Run comprehensive health check
node health-checker.js https://api.ai-infrastructure-portal.com

# Check Kubernetes resources
kubectl get all -n ai-infrastructure
```

### Performance Validation
```bash
# Run load tests
npm run test:performance

# Check resource utilization
kubectl top pods -n ai-infrastructure
```

### Security Validation
```bash
# Run security scans
npm run test:security

# Check network policies
kubectl get networkpolicies -n ai-infrastructure
```

## Maintenance Procedures

### Certificate Rotation
```bash
# Update TLS certificates
kubectl create secret tls ai-portal-tls-new \
  --cert=<new-cert> \
  --key=<new-key> \
  --namespace=ai-infrastructure

# Update ingress to use new secret
kubectl patch ingress ai-infrastructure-portal-ingress \
  -p '{"spec":{"tls":[{"secretName":"ai-portal-tls-new"}]}}' \
  -n ai-infrastructure
```

### Log Rotation
```bash
# Configure log rotation (handled automatically by Kubernetes)
kubectl get configmaps -n ai-infrastructure

# Manual log cleanup
kubectl exec -n ai-infrastructure <pod-name> -- find /var/log -name "*.log" -mtime +30 -delete
```

### Dependency Updates
```bash
# Update Helm charts
helm repo update
helm upgrade <release-name> <chart> -n ai-infrastructure

# Update Docker images
kubectl set image deployment/ai-infrastructure-portal ai-infrastructure-portal=ghcr.io/<org>/ai-infrastructure-portal:latest -n ai-infrastructure
```

## Contact Information

### Support Teams
- **DevOps Team**: devops@company.com
- **Security Team**: security@company.com
- **Application Team**: app-support@company.com

### Escalation Matrix
- **Level 1**: On-call engineer (response: 15 minutes)
- **Level 2**: Team lead (response: 1 hour)
- **Level 3**: Engineering manager (response: 4 hours)
- **Level 4**: Executive team (response: 24 hours)

### Emergency Contacts
- **24/7 On-call**: +1-800-DEPLOY
- **Security Incidents**: +1-800-SECURITY
- **Infrastructure Issues**: +1-800-INFRA

---

## Checklist

### Pre-Deployment
- [ ] Infrastructure prerequisites met
- [ ] Access credentials configured
- [ ] Network connectivity verified
- [ ] Backup procedures documented
- [ ] Rollback plan prepared

### Deployment Execution
- [ ] Namespace created and configured
- [ ] Secrets and configmaps applied
- [ ] Ingress controller installed
- [ ] Services deployed in correct order
- [ ] Health checks passing
- [ ] Monitoring configured

### Post-Deployment
- [ ] End-to-end testing completed
- [ ] Performance benchmarks met
- [ ] Security scans passed
- [ ] Documentation updated
- [ ] Team notification sent

### Ongoing Maintenance
- [ ] Monitoring alerts configured
- [ ] Backup schedules verified
- [ ] Certificate expiration monitored
- [ ] Log rotation automated
- [ ] Performance metrics tracked
