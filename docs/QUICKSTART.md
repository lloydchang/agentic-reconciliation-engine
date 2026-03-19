# Quickstart - MVP GitOps Infrastructure

Get a working GitOps control plane running locally in minutes.

## Prerequisites

- `kubectl`, `helm`, `kind` (for local clusters)
- POSIX shell (bash, WSL, Git Bash)

## MVP Setup (One Command)

```bash
# One-command MVP setup with AI agents and dashboard
./core/scripts/automation/quickstart.sh
```

**What it deploys:**
1. Bootstrap Cluster (recovery anchor)
2. Hub Cluster with Flux + Crossplane + Kubernetes Provider
3. Spoke Cluster (local workloads)
4. AI Agents Ecosystem with Temporal orchestration
5. Interactive Dashboard for monitoring and control

Or run steps manually:

```bash
# 1. Validate your environment
./core/scripts/automation/prerequisites.sh

# 2. Setup GitOps configuration
./core/scripts/automation/setup-gitops-config.sh

# 3. Create bootstrap cluster (recovery anchor)
./core/scripts/infrastructure/create-bootstrap-cluster.sh

# 4. Create hub cluster (GitOps control plane)
./core/scripts/automation/create-hub-cluster.sh --provider kind --bootstrap-kubeconfig bootstrap-kubeconfig

# 5. Install Crossplane with Kubernetes provider for local development
./core/scripts/automation/install-crossplane.sh --providers local

# 6. Create spoke cluster (MVP - local emulation)
./core/scripts/automation/create-spoke-clusters.sh

# 7. Deploy AI agents ecosystem with dashboard
./core/scripts/automation/deploy-ai-agents-ecosystem.sh
```

## MVP Options

```bash
# Full MVP setup (recommended)
./core/scripts/automation/quickstart.sh

# Show help
./core/scripts/automation/quickstart.sh --help
```

## What You Get

✅ **Bootstrap Cluster** - Recovery anchor for hub cluster  
✅ **Hub Cluster** - Runs Flux, Crossplane with Kubernetes Provider, Cluster API  
✅ **Spoke Cluster** - Local kind cluster for workloads  
✅ **GitOps Workflow** - Full continuous reconciliation  
✅ **AI Agents Ecosystem** - 90+ operational skills with Temporal orchestration  
✅ **Interactive Dashboard** - Real-time monitoring and control with FastAPI backend  
✅ **Auto API Documentation** - Interactive docs at `/docs` endpoint  
✅ **Zero Cloud Costs** - Everything runs locally with full functionality  

## Verify Your MVP

```bash
# Check all clusters
kubectl get clusters -n gitops-system

# Check Flux status
kubectl get pods -n flux-system

# Check Crossplane with Kubernetes provider
kubectl get providers -n crossplane-system
kubectl get providerconfig -n crossplane-system

# Check AI agents
kubectl get pods -n ai-infrastructure

# Access AI Dashboard
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80
open http://localhost:8080

# Access API Documentation (FastAPI)
kubectl port-forward -n ai-infrastructure svc/dashboard-api-service 5000:5000
open http://localhost:5000/docs
```

## Next Steps

- **Learn Crossplane Local Development**: See [docs/CROSSPLANE-LOCAL-DEVELOPMENT.md](docs/CROSSPLANE-LOCAL-DEVELOPMENT.md)
- **Add Real Cloud**: `./core/scripts/automation/create-spoke-clusters.sh --providers azure`
- **Multi-Cloud**: `./core/scripts/automation/create-spoke-clusters.sh --providers azure,aws,gcp`
- **Production**: Use real cloud providers for hub cluster
- **AI Agents Guide**: See [docs/AI-AGENTS-DEPLOYMENT-GUIDE.md](docs/AI-AGENTS-DEPLOYMENT-GUIDE.md)

## Architecture

```
Bootstrap Cluster (local) → Hub Cluster (local) → Spoke Cluster (local)
        ↓                           ↓                      ↓
   Recovery Config         Flux + Crossplane +      Workloads + Apps
                              Kubernetes Provider
                              ↓
                        AI Agents + Temporal
                              ↓
                         Interactive Dashboard
```

---

**MVP Benefits**: No cloud costs, no credentials, full GitOps validation, complete Crossplane functionality.  

**For production deployment**, see [docs/OVERVIEW.md](docs/OVERVIEW.md).

**For Crossplane local development details**, see [docs/CROSSPLANE-LOCAL-DEVELOPMENT.md](docs/CROSSPLANE-LOCAL-DEVELOPMENT.md).
