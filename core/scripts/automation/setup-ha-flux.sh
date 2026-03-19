#!/bin/bash
# setup-ha-flux.sh
# Script to deploy active-passive Flux instances for high availability

set -e

# Configuration
PRIMARY_CLUSTER="hub-primary"
SECONDARY_CLUSTER="hub-secondary"
GIT_REPO="https://github.com/lloydchang/agentic-reconciliation-engine"
BRANCH="main"

# Function to deploy Flux to a cluster
deploy_flux() {
  local cluster=$1
  local mode=$2  # primary or secondary

  echo "Deploying Flux in $mode mode to cluster $cluster"

  # Use kubectl context for the cluster
  kubectl config use-context $cluster

  # Deploy Flux with Helm (assuming Helm is used)
  helm upgrade --install flux fluxcd/flux \
    --namespace flux-system \
    --create-namespace \
    --set git.url=$GIT_REPO \
    --set git.branch=$BRANCH \
    --set mode=$mode \
    --wait

  echo "Flux deployed to $cluster"
}

# Deploy primary
deploy_flux $PRIMARY_CLUSTER "primary"

# Deploy secondary (passive)
deploy_flux $SECONDARY_CLUSTER "secondary"

# Setup monitoring and failover
echo "Setting up monitoring and failover logic"

# Assume Prometheus is already deployed, add alert rules
kubectl apply -f core/resources/monitoring/flux-ha-alerts.yaml

# DNS switching script (placeholder)
cat > /tmp/failover.sh <<EOF
#!/bin/bash
# Check primary Flux health
if ! kubectl --context $PRIMARY_CLUSTER get pods -n flux-system | grep -q Running; then
  echo "Primary Flux down, switching to secondary"
  # Update DNS or config to point to secondary
  # This is a placeholder - implement actual DNS update
fi
EOF

chmod +x /tmp/failover.sh

echo "HA setup complete. Run /tmp/failover.sh periodically for monitoring."
