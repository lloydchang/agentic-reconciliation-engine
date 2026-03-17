#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<-USAGE
Usage: $0 <provider> <namespace> <repository> <branch>

Prints the URL that users can open in the browser to create a manual pull request
for providers that don't expose a PR CLI (AWS CodeCommit, GCP Secure Source Manager).
Supported providers: codecommit, gcp-ssm.
USAGE
}

if [[ $# -lt 4 ]]; then
  usage
  exit 1
fi

PROVIDER=$1
NAMESPACE=$2
REPO=$3
BRANCH=$4

case "$PROVIDER" in
  codecommit)
    echo "Open AWS CodeCommit PR console:"
    echo "https://console.aws.amazon.com/codesuite/codecommit/repositories/$REPO/pull-requests?region=${AWS_REGION:-us-east-1}"
    echo "Select 'Create pull request' and set source branch to $BRANCH and target main."
    ;;
  gcp-ssm)
    echo "Open Cloud Source Repositories console:"
    echo "https://console.cloud.google.com/source/repos/$REPO/compare?project=$NAMESPACE&legacyProject=false"
    echo "Click 'Create pull request' and confirm source branch $BRANCH targeting main."
    ;;
  *)
    echo "Provider '$PROVIDER' not supported by this helper." >&2
    usage
    exit 1
    ;;
esac
