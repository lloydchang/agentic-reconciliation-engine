#!/usr/bin/env bash
# =============================================================================
# Cloud AI Agent — export Argo CD state for migration
# =============================================================================
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [output-directory]

Dumps Argo CD Applications, ApplicationSets, and cluster registrations into
a timestamped directory (defaults to /tmp/argocd-export-<timestamp>) so the
state can be safely versioned before migrating workloads.
USAGE
}

OUTPUT_DIR=${1:-/tmp/argocd-export-$(date +%Y%m%d-%H%M%S)}

mkdir -p "$OUTPUT_DIR"

command -v argocd >/dev/null 2>&1 || { echo "argocd CLI required" >&2; exit 1; }

echo "Exporting Argo CD applications and clusters to $OUTPUT_DIR"

argocd app list --all-namespaces --output yaml > "$OUTPUT_DIR/applications.yaml"
argocd cluster list --output yaml > "$OUTPUT_DIR/clusters.yaml"
kubectl get applicationsets.argoproj.io -A -o yaml > "$OUTPUT_DIR/applicationsets.yaml"

echo "Finished exporting:"
echo "  - Applications -> $OUTPUT_DIR/applications.yaml"
echo "  - Clusters     -> $OUTPUT_DIR/clusters.yaml"
echo "  - ApplicationSets -> $OUTPUT_DIR/applicationsets.yaml"

echo ""
echo "You can reference these files when editing the migration playbooks."
