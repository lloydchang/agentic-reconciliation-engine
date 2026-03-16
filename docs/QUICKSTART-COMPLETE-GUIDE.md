# Quickstart Guide - GitOps Infrastructure with AI Agents

## Overview

The quickstart script provides a one-command deployment of the complete GitOps infrastructure control plane with AI agents ecosystem. This streamlined approach eliminates configuration complexity while providing a production-ready environment.

## Quickstart Script

### `scripts/quickstart.sh`

The main entry point for deploying the complete GitOps infrastructure with AI agents.

#### Usage
```bash
./scripts/quickstart.sh
```

#### Features
- **One-Command Deployment**: Complete infrastructure setup
- **Automated AI Agents**: Deploys full AI agents ecosystem
- **Production Ready**: Includes monitoring, dashboard, and orchestration
- **Self-Healing**: Automated dependency resolution and error recovery

#### Deployment Steps

1. **Prerequisites Check**
   - Validates system requirements
   - Checks for required tools (kubectl, helm, etc.)
   - Verifies cluster access

2. **GitOps Configuration**
   - Sets up Flux CD controllers
   - Configures Git repositories
   - Establishes reconciliation loops

3. **Bootstrap Cluster**
   - Creates recovery anchor cluster
   - Deploys essential infrastructure components
   - Establishes management plane

4. **Hub Cluster**
   - Deploys GitOps control plane
   - Configures Crossplane providers
   - Sets up monitoring stack

5. **Crossplane Installation**
   - Installs Kubernetes provider for local development
   - Configures provider credentials
   - Sets up managed resource reconciliation

6. **Spoke Clusters**
   - Creates workload clusters
   - Configures cluster networking
   - Establishes fleet management

7. **AI Agents Ecosystem**
   - Deploys Temporal orchestration
   - Installs AI agents with 72+ skills
   - Sets up monitoring and dashboard

#### Post-Deployment Access

After successful deployment, access the following services:

##### 1. AI Agents Dashboard
```bash
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80
open http://localhost:8080
```

##### 2. Temporal Workflow UI
```bash
kubectl port-forward -n ai-infrastructure svc/temporal-frontend 7233:7233
open http://localhost:7233
```

##### 3. Cluster Management
```bash
export KUBECONFIG=${SCRIPT_DIR}/../gitops-hub-local-kubeconfig
kubectl get nodes

export KUBECONFIG=${SCRIPT_DIR}/../gitops-spoke-local-kubeconfig
kubectl get nodes
```

## Crossplane Integration

### Enhanced `scripts/install-crossplane.sh`

Updated to support local development with Kubernetes provider.

#### Key Features

##### Kubernetes Provider for Local Development
- **Provider Package**: `crossplane-contrib/provider-kubernetes:v0.6.0`
- **Purpose**: Enables local cluster management
- **Configuration**: Automatic provider config setup

##### Provider Installation
```yaml
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-kubernetes
spec:
  package: "crossplane-contrib/provider-kubernetes:v0.6.0"
```

##### Provider Configuration
```yaml
apiVersion: kubernetes.crossplane.io/v1alpha1
kind: ProviderConfig
metadata:
  name: local-cluster
  namespace: "crossplane-system"
spec:
  credentials:
    source: InjectedIdentity
```

#### Usage Examples
```bash
# Install all cloud providers
./scripts/install-crossplane.sh

# Install specific providers
./scripts/install-crossplane.sh --providers azure,aws

# Install Kubernetes provider for local development
./scripts/install-crossplane.sh --providers local
```

## AI Agents Ecosystem Deployment

### `scripts/deploy-ai-agents-ecosystem.sh`

Deploys the complete AI agents monitoring and orchestration system.

#### Components Deployed

##### 1. Temporal Orchestration
- **Temporal Server**: Workflow orchestration engine
- **Temporal UI**: Web-based workflow management
- **Temporal Workers**: Go-based AI agents with skills

##### 2. AI Agents
- **Memory Agent**: Rust-based memory management
- **Orchestration Agent**: Go-based workflow coordination
- **Inference Gateway**: Python-based AI inference
- **72+ Skills**: Comprehensive automation capabilities

##### 3. Monitoring System
- **Go Metrics Server**: Real-time metrics collection
- **Dashboard API**: Flask API for frontend
- **React Dashboard**: Web-based monitoring interface

##### 4. Infrastructure Components
- **Kubernetes Deployments**: Container orchestration
- **Services**: Network exposure and load balancing
- **ConfigMaps**: Configuration management
- **Secrets**: Secure credential management

#### Service Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │    │  Flask API       │    │ Go Metrics      │
│   (Port 3001)   │◄──►│  (Port 5002)     │◄──►│ Server (8080)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Temporal UI     │    │ Temporal Server  │    │ AI Agents       │
│   (Port 7233)   │◄──►│   (Port 7233)    │◄──►│ (Go Workers)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Configuration Management

### Environment Variables
- `KUBECONFIG`: Path to cluster configuration
- `NAMESPACE`: Target namespace for deployments
- `DOMAIN`: Base domain for services (if applicable)

### Customization Options
- **Cluster Providers**: Choose between kind, k3s, or external clusters
- **Cloud Providers**: Configure AWS, Azure, GCP integration
- **Monitoring**: Enable/disable monitoring stack
- **Networking**: Configure CNI and load balancer options

## Troubleshooting

### Common Issues

#### 1. Port Conflicts
- **Symptom**: Services fail to start due to port conflicts
- **Solution**: Check for existing processes and kill if necessary
- **Command**: `lsof -i :8080` and `kill -9 <PID>`

#### 2. Cluster Access Issues
- **Symptom**: kubectl commands fail
- **Solution**: Verify kubeconfig path and cluster connectivity
- **Command**: `kubectl config current-context`

#### 3. AI Agents Not Starting
- **Symptom**: Dashboard shows no agent data
- **Solution**: Check pod logs and resource constraints
- **Command**: `kubectl logs -n ai-infrastructure -l app=ai-agents`

#### 4. Dashboard Connection Issues
- **Symptom**: Frontend cannot connect to API
- **Solution**: Verify port-forward and API health
- **Command**: `curl http://localhost:5002/health`

### Debug Commands

#### System Health Check
```bash
# Check all pods
kubectl get pods -A

# Check services
kubectl get svc -A

# Check AI agents specifically
kubectl get pods -n ai-infrastructure
```

#### Log Analysis
```bash
# AI agents logs
kubectl logs -n ai-infrastructure -l app=ai-agents --tail=100

# Temporal logs
kubectl logs -n ai-infrastructure -l app=temporal --tail=100

# Dashboard logs
kubectl logs -n ai-infrastructure -l app=dashboard-api --tail=100
```

#### Connectivity Testing
```bash
# Test API endpoints
curl http://localhost:5002/health
curl http://localhost:5002/api/config

# Test Go metrics server
curl http://localhost:8080/health

# Test Temporal
curl http://localhost:7233
```

## Performance Considerations

### Resource Requirements

#### Minimum Requirements
- **CPU**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 20GB available
- **Network**: Stable internet connection

#### Recommended Requirements
- **CPU**: 8 cores
- **Memory**: 16GB RAM
- **Storage**: 50GB available
- **Network**: High-speed connection

### Optimization Tips

#### 1. Resource Limits
- Configure appropriate CPU/memory limits for pods
- Use resource requests for guaranteed scheduling
- Monitor resource usage with built-in metrics

#### 2. Network Optimization
- Use local container registry for faster pulls
- Configure appropriate service types
- Optimize ingress for external access

#### 3. Storage Optimization
- Use appropriate storage classes
- Configure persistent volumes for data persistence
- Monitor storage usage and cleanup

## Security Considerations

### Network Security
- **Network Policies**: Isolate namespace traffic
- **Service Mesh**: Consider Istio for mTLS
- **Ingress**: Secure external access with TLS

### Authentication
- **RBAC**: Configure role-based access control
- **Service Accounts**: Use least-privilege accounts
- **External Auth**: Integrate with OIDC providers

### Secrets Management
- **Sealed Secrets**: Encrypt sensitive data
- **External Secret Store**: Use Vault or cloud KMS
- **Rotation**: Implement secret rotation policies

## Backup and Recovery

### Configuration Backup
```bash
# Backup GitOps configuration
kubectl get gitrepositories -A -o yaml > git-repos-backup.yaml
kubectl get kustomizations -A -o yaml > kustomizations-backup.yaml
```

### Data Backup
```bash
# Backup persistent data
kubectl get pvc -A -o yaml > pvc-backup.yaml
# Implement volume snapshots for critical data
```

### Recovery Procedures
1. **Cluster Recovery**: Restore from etcd snapshots
2. **Application Recovery**: Redeploy from Git repository
3. **Data Recovery**: Restore from volume snapshots

## Migration Guide

### From Existing Infrastructure
1. **Assessment**: Analyze current setup and dependencies
2. **Planning**: Create migration timeline and rollback plan
3. **Execution**: Follow step-by-step migration process
4. **Validation**: Verify all services and data integrity

### Version Upgrades
1. **Preparation**: Backup current configuration
2. **Testing**: Validate in staging environment
3. **Upgrade**: Apply updates following semantic versioning
4. **Verification**: Confirm all services are operational

## Best Practices

### Development Workflow
1. **Local Development**: Use kind clusters for testing
2. **CI/CD Integration**: Automate testing and deployment
3. **GitOps**: Store all configuration in Git
4. **Documentation**: Maintain up-to-date documentation

### Operational Excellence
1. **Monitoring**: Implement comprehensive monitoring
2. **Alerting**: Set up meaningful alerts
3. **Backup**: Regular backup and recovery testing
4. **Security**: Regular security audits and updates

### Team Collaboration
1. **Code Reviews**: Require peer review for changes
2. **Documentation**: Document all procedures and decisions
3. **Training**: Regular team training and knowledge sharing
4. **Communication**: Maintain clear communication channels

This quickstart guide provides a comprehensive foundation for deploying and managing the GitOps infrastructure with AI agents, ensuring production-ready deployments with proper monitoring, security, and operational excellence.
