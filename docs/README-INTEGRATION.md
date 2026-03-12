# Quick Integration Guide

This guide provides the fastest path to integrating with the Continuous Reconciliation Engine (CRE) for building proprietary infrastructure management platforms.

## Prerequisites

- Kubernetes cluster for hub deployment
- Access to AWS/Azure/GCP accounts
- Git repository for infrastructure manifests

## Step 1: Deploy CRE Foundation (15 minutes)

### Deploy Hub Cluster
```bash
# Use provided setup scripts
./scripts/hub-clusters/setup-aws-hub-eks.sh
# OR
./scripts/hub-clusters/setup-azure-hub-aks.sh
# OR
./scripts/hub-clusters/setup-gcp-hub-gke.sh
```

### Apply Core Infrastructure
```bash
kubectl apply -k control-plane/
kubectl apply -k infrastructure/
```

## Step 2: Expose APIs (10 minutes)

### Option A: Direct Kubernetes API
```bash
# Port-forward Flux controllers
kubectl port-forward svc/flux-controller -n flux-system 8080:80
```

### Option B: REST API Wrapper
Create a simple API service that communicates with CRE via kubectl/GitOps.

## Step 3: Build Your Proprietary Layer

### Basic Integration Pattern
```python
# Example: Python integration
import subprocess
import yaml

def deploy_infrastructure(manifest):
    # Write to Git repository
    with open('infra/manifest.yaml', 'w') as f:
        yaml.dump(manifest, f)

    # Git commit triggers CRE reconciliation
    subprocess.run(['git', 'add', 'infra/'])
    subprocess.run(['git', 'commit', '-m', 'Deploy infrastructure'])
    subprocess.run(['git', 'push'])

    return {"status": "deploying"}
```

### Webhook Integration
```javascript
// Example: Node.js webhook handler
app.post('/infrastructure/status', (req, res) => {
  const { status, resource } = req.body;
  // Update your proprietary database/UI
  updateInfrastructureStatus(resource, status);
  res.sendStatus(200);
});
```

## Step 4: Add Business Logic

### Authentication Layer
```python
def authenticated_deploy(user, manifest):
    if authorize(user, manifest):
        return deploy_infrastructure(manifest)
    else:
        raise PermissionError("Unauthorized")
```

### Multi-tenancy
```python
def tenant_isolated_deploy(tenant_id, manifest):
    # Prefix all resources with tenant
    manifest = add_tenant_prefix(manifest, tenant_id)
    return deploy_infrastructure(manifest)
```

## Step 5: Monitoring & Alerting

### Drift Detection Integration
```bash
# Monitor CRE status
kubectl get gitrepositories -n flux-system -w
```

### Custom Alerts
```yaml
# Add to your monitoring stack
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cre-alerts
spec:
  groups:
  - name: cre
    rules:
    - alert: InfrastructureDrift
      expr: flux_reconciliation_status != 1
      labels:
        severity: warning
```

## Directory Structure for Your Platform

```
your-platform/
├── api/                 # REST API layer
├── ui/                  # Web interface
├── business-logic/      # Proprietary features
├── integrations/        # CRE integration code
├── monitoring/          # Observability
└── deployment/          # Your platform deployment
```

## Next Steps

1. **Read [USAGE-GUIDE.md](./USAGE-GUIDE.md)** for architectural patterns
2. **Review [LICENSING-GUIDE.md](./LICENSING-GUIDE.md)** for compliance
3. **See [GREENFIELD-DEPLOYMENT.md](./GREENFIELD-DEPLOYMENT.md)** for detailed tutorial
4. **Explore [PROPRIETARY-EXTENSIONS.md](./PROPRIETARY-EXTENSIONS.md)** for examples

## Support

- Documentation: `/docs/` directory
- Scripts: `/scripts/` directory
- Examples: See implementation guides
