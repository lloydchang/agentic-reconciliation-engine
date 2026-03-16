#!/usr/bin/env bash
# =============================================================================
# Cloud AI Agent — migrate an Argo CD application to a new cluster context
# =============================================================================
set -euo pipefail
cd $(dirname $0)

usage() {
  cat <<USAGE
Usage: $0 <app-name> <target-context> [namespace]

Updates the Argo CD application destination to point at the cluster referenced
by <target-context>, syncs the application, and waits for healthy reconciliation.
NS defaults to the application's existing destination namespace if not provided.
USAGE
}

if [[ $# -lt 2 ]]; then
  usage
  exit 1
fi

APP_NAME=$1
TARGET_CONTEXT=$2
DEST_NAMESPACE=${3:-}

command -v argocd >/dev/null 2>&1 || { echo "argocd CLI required" >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl CLI required" >&2; exit 1; }

# Determine the API server from the kubeconfig context
CLUSTER_NAME=$(kubectl config view -o jsonpath="{.contexts[?(@.name==\"$TARGET_CONTEXT\")].context.cluster}")
if [[ -z "$CLUSTER_NAME" ]]; then
  echo "Context '$TARGET_CONTEXT' not found in kubeconfig" >&2
  exit 1
fi

DEST_SERVER=$(kubectl config view -o jsonpath="{.clusters[?(@.name==\"$CLUSTER_NAME\")].cluster.server}")
if [[ -z "$DEST_SERVER" ]]; then
  echo "Unable to resolve API server for context $TARGET_CONTEXT" >&2
  exit 1
fi

if [[ -z "$DEST_NAMESPACE" ]]; then
  DEST_NAMESPACE=$(argocd app get "$APP_NAME" -o jsonpath='{.spec.destination.namespace}' 2>/dev/null)
  DEST_NAMESPACE=${DEST_NAMESPACE:-default}
fi

echo "Migrating Argo CD application '$APP_NAME' to context '$TARGET_CONTEXT' (server: $DEST_SERVER, namespace: $DEST_NAMESPACE)"

argocd app set "$APP_NAME" \
  --dest-server "$DEST_SERVER" \
  --dest-namespace "$DEST_NAMESPACE"

argocd app sync "$APP_NAME"
argocd app wait "$APP_NAME" --health --timeout 180

echo "Migration complete for $APP_NAME."
