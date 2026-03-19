# Kind Configuration File Consolidation

## Issue Analysis

The repository contained multiple `kind-config.yaml` files in different locations, creating confusion about their purpose and usage.

### Files Found
- **Root `kind-config.yaml`**: Repository root with port mappings for Temporal (7233) and dashboards (3000/13000)
- **`core/resources/kind-config.yaml`**: Infrastructure directory with basic ingress ports (8080/8443) named "agent-orchestration-demo"

### Usage Analysis

#### What Uses `kind-config.yaml`?

**Deployment Scripts (Do NOT use root config):**
- `create-bootstrap-cluster.sh` → Creates `/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml`
- `create-spoke-clusters.sh` → Creates `/tmp/${spoke_name}-kind-config.yaml` for local provider
- `create-hub-cluster.sh` → References but doesn't use the root file

**Documentation & Scripts (DO use root config):**
- [docs/NETWORK-CONNECTIVITY-TROUBLESHOOTING.md](docs/NETWORK-CONNECTIVITY-TROUBLESHOOTING.md) - References root file for troubleshooting
- [docs/AI-AGENTS-DEVELOPMENT-SETUP-GUIDE.md](docs/AI-AGENTS-DEVELOPMENT-SETUP-GUIDE.md) - References root file for development setup
- `core/scripts/automation/recreate-clusters-with-fix.sh` - Uses root file for cluster recreation
- Multiple `test-e2e-local-agent-orchestration-demo.sh` files - Use root file for local demos

### Root Cause

The two `kind-config.yaml` files served different purposes:
- **Root file**: General local development with full stack ports (Temporal, dashboards, web)
- **Infrastructure file**: Agent orchestration demos with basic ingress ports

However, agent orchestration scripts actually reference the **root file**, making the infrastructure file unused.

### Solution Implemented

**Consolidated into single `kind-config.yaml` in repository root:**

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  # Use custom subnet to avoid conflicts with VPNs/local networks
  podSubnet: "10.254.0.0/16"
  serviceSubnet: "10.255.0.0/16"
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 8443
    protocol: TCP
  - containerPort: 7233
    hostPort: 7233
    protocol: TCP
  - containerPort: 3000
    hostPort: 3000
    protocol: TCP
  - containerPort: 13000
    hostPort: 13000
    protocol: TCP
```

### Ports Included

- **8080**: HTTP web services
- **8443**: HTTPS/SSL web services  
- **7233**: Temporal server
- **3000**: Dashboard services
- **13000**: Additional dashboard services

### Files Changed

- **Modified**: `kind-config.yaml` (consolidated ports and configuration)
- **Removed**: `core/resources/kind-config.yaml` (unused duplicate)

### Verification

- All 26+ references to `kind-config.yaml` remain intact (expect repo root location)
- No breaking changes to documentation or scripts
- Single config now supports all local development use cases

### Repository Pattern Compliance

This follows typical GitOps/Kubernetes repository patterns where:
- Primary/default configs are in repository root
- Specialized configs go in subdirectories
- `kind-config.yaml` is the conventional name for Kind cluster configurations

### Git History

```bash
commit: Consolidate kind-config.yaml files into single repository root config
- Merge core/resources/kind-config.yaml ports into root kind-config.yaml
- Remove unused core/resources/kind-config.yaml
- Add all necessary ports for local development and agent orchestration
```

## Conclusion

The consolidation eliminated confusion by providing a single, comprehensive Kind configuration that supports all local development use cases while maintaining backward compatibility with existing documentation and scripts.
