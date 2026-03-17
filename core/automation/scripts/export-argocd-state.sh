#!/usr/bin/env bash
# =============================================================================
# Cloud AI Agent — export Argo CD state for migration
# =============================================================================
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [output-directory] [provider]

Dumps Argo CD Applications, ApplicationSets, and cluster registrations into
a timestamped directory (defaults to /tmp/argocd-export-<timestamp>) so the
state can be safely versioned before migrating workloads.

The provider argument is ignored - this script exports Argo CD state 
regardless of the cloud provider.
USAGE
}

OUTPUT_DIR=${1:-/tmp/argocd-export-$(date +%Y%m%d-%H%M%S)}
# Ignore provider argument for compatibility
PROVIDER=${2:-""}

mkdir -p "$OUTPUT_DIR"

command -v argocd >/dev/null 2>&1 || { echo "argocd CLI required" >&2; exit 1; }

echo "Exporting Argo CD applications and clusters to $OUTPUT_DIR"

# Try to list all apps, fallback to apps in default namespace if that fails
if argocd app list -o yaml > "$OUTPUT_DIR/applications.yaml" 2>/dev/null; then
    echo "Successfully exported all applications"
else
    echo "Failed to export all apps, trying default namespace..."
    if argocd app list -N default -o yaml > "$OUTPUT_DIR/applications.yaml" 2>/dev/null; then
        echo "Successfully exported applications from default namespace"
    else
        echo "Argo CD server not reachable or no applications found"
        echo "# No Argo CD applications found - server not reachable or no apps" > "$OUTPUT_DIR/applications.yaml"
    fi
fi

# Export clusters (may fail if Argo CD server is not running)
if argocd cluster list --output yaml > "$OUTPUT_DIR/clusters.yaml" 2>/dev/null; then
    echo "Successfully exported clusters"
else
    echo "Argo CD server not reachable or no clusters found"
    echo "# No Argo CD clusters found - server not reachable or no clusters" > "$OUTPUT_DIR/clusters.yaml"
fi

# Export ApplicationSets (may fail if Argo CD is not installed)
if kubectl get applicationsets.argoproj.io -A -o yaml > "$OUTPUT_DIR/applicationsets.yaml" 2>/dev/null; then
    echo "Successfully exported ApplicationSets"
else
    echo "Argo CD ApplicationSets not found or not installed"
    echo "# No Argo CD ApplicationSets found - not installed or no resources" > "$OUTPUT_DIR/applicationsets.yaml"
fi

echo "Finished exporting:"
echo "  - Applications -> $OUTPUT_DIR/applications.yaml"
echo "  - Clusters     -> $OUTPUT_DIR/clusters.yaml"
echo "  - ApplicationSets -> $OUTPUT_DIR/applicationsets.yaml"

echo ""
echo "You can reference these files when editing the migration playbooks."
