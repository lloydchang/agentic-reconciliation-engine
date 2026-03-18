#!/bin/bash

# Open SWE GitHub App Setup Script
# This script creates and configures a GitHub App for Open SWE integration

set -e

# Configuration
APP_NAME="GitOps Infra Control Plane Agent"
APP_DESCRIPTION="AI-powered infrastructure automation and software engineering assistance"
WEBHOOK_URL="https://open-swe-webhooks.your-domain.com/api/webhooks/github"
APP_URL="https://open-swe.your-domain.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed. Please install it first:"
        log_error "  brew install gh  # macOS"
        log_error "  # or visit: https://cli.github.com/"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it first:"
        log_error "  brew install jq  # macOS"
        exit 1
    fi

    if ! gh auth status &> /dev/null; then
        log_error "You are not authenticated with GitHub CLI. Please run:"
        log_error "  gh auth login"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create GitHub App manifest
create_app_manifest() {
    log_info "Creating GitHub App manifest..."

    cat > /tmp/github-app-manifest.json << EOF
{
    "name": "${APP_NAME}",
    "description": "${APP_DESCRIPTION}",
    "url": "${APP_URL}",
    "hook_attributes": {
        "url": "${WEBHOOK_URL}",
        "active": true
    },
    "redirect_url": "${APP_URL}/github/oauth/callback",
    "public": false,
    "default_permissions": {
        "contents": "read",
        "issues": "write",
        "pull_requests": "write",
        "repository_hooks": "write",
        "statuses": "write",
        "deployments": "write",
        "checks": "write",
        "metadata": "read"
    },
    "default_events": [
        "issues",
        "issue_comment",
        "pull_request",
        "pull_request_review",
        "pull_request_review_comment",
        "push",
        "check_suite",
        "check_run",
        "deployment",
        "deployment_status"
    ]
}
EOF

    log_success "GitHub App manifest created at /tmp/github-app-manifest.json"
}

# Create GitHub App
create_github_app() {
    log_info "Creating GitHub App..."

    # Create the app using GitHub CLI
    APP_CONFIG=$(gh api \
        --method POST \
        -H "Accept: application/vnd.github.v3+json" \
        /app-manifests \
        -f code="$(cat /tmp/github-app-manifest.json | jq -r tostring)")

    # Extract app details
    APP_ID=$(echo "$APP_CONFIG" | jq -r '.id')
    APP_SLUG=$(echo "$APP_CONFIG" | jq -r '.slug')
    PRIVATE_KEY=$(echo "$APP_CONFIG" | jq -r '.pem')
    WEBHOOK_SECRET=$(echo "$APP_CONFIG" | jq -r '.webhook_secret')

    log_success "GitHub App created successfully!"
    log_info "App ID: $APP_ID"
    log_info "App Slug: $APP_SLUG"

    # Save private key
    echo "$PRIVATE_KEY" > /tmp/github-app-private-key.pem
    log_success "Private key saved to /tmp/github-app-private-key.pem"

    # Save webhook secret
    echo "$WEBHOOK_SECRET" > /tmp/github-app-webhook-secret.txt
    log_success "Webhook secret saved to /tmp/github-app-webhook-secret.txt"
}

# Generate Kubernetes secrets
generate_k8s_secrets() {
    log_info "Generating Kubernetes secrets..."

    # Create namespace if it doesn't exist
    kubectl create namespace open-swe --dry-run=client -o yaml | kubectl apply -f -

    # Create private key secret
    kubectl create secret generic open-swe-github-app-key \
        --namespace open-swe \
        --from-file=github-app-private-key.pem=/tmp/github-app-private-key.pem \
        --dry-run=client -o yaml > /tmp/github-app-secrets.yaml

    # Add webhook secret to the secrets file
    cat >> /tmp/github-app-secrets.yaml << EOF
---
apiVersion: v1
kind: Secret
metadata:
  name: open-swe-webhook-secrets
  namespace: open-swe
type: Opaque
stringData:
  webhook-secret: "$(cat /tmp/github-app-webhook-secret.txt)"
  github-app-id: "$APP_ID"
EOF

    log_success "Kubernetes secrets generated at /tmp/github-app-secrets.yaml"
}

# Install app to repository
install_app_to_repo() {
    log_info "Installing GitHub App to repository..."

    # Get current repository
    REPO=$(gh repo view --json owner,name -q ".owner.login + \"/\" + .name")

    log_info "Installing app to repository: $REPO"

    # Install the app (this would typically be done through the GitHub web interface)
    # For now, we'll provide instructions
    log_warning "Please manually install the GitHub App to your repository:"
    log_warning "1. Go to: https://github.com/apps/$APP_SLUG/installations/new"
    log_warning "2. Select repository: $REPO"
    log_warning "3. Grant permissions and install"

    # Generate repository installation token (requires app installation first)
    log_info "After installation, you can generate an installation token:"
    log_info "gh api /app/installations -q '.[] | select(.app_slug==\"$APP_SLUG\") | .id'"
}

# Generate configuration documentation
generate_config_docs() {
    log_info "Generating configuration documentation..."

    cat > /tmp/github-app-setup-instructions.md << EOF
# GitHub App Setup Instructions

## App Details
- **App ID**: $APP_ID
- **App Slug**: $APP_SLUG
- **Webhook URL**: $WEBHOOK_URL

## Required Environment Variables

Add these to your Open SWE deployment:

\`\`\`yaml
env:
- name: GITHUB_APP_ID
  value: "$APP_ID"
- name: GITHUB_WEBHOOK_SECRET
  value: "$(cat /tmp/github-app-webhook-secret.txt)"
- name: GITHUB_PRIVATE_KEY
  valueFrom:
    secretKeyRef:
      name: open-swe-github-app-key
      key: github-app-private-key.pem
\`\`\`

## Installation Steps

1. **Install the App to Repository**:
   - Go to: https://github.com/apps/$APP_SLUG/installations/new
   - Select your repository: $REPO
   - Grant the requested permissions

2. **Apply Kubernetes Secrets**:
   \`\`\`bash
   kubectl apply -f /tmp/github-app-secrets.yaml
   \`\`\`

3. **Deploy Open SWE Components**:
   \`\`\`bash
   kubectl apply -f core/ai/runtime/openswe-integration/langgraph/langgraph-deployment.yaml
   kubectl apply -f core/ai/runtime/openswe-integration/webhooks/webhook-deployment.yaml
   \`\`\`

4. **Verify Installation**:
   - Check GitHub App installation: https://github.com/apps/$APP_SLUG
   - Verify webhook delivery: https://github.com/$REPO/settings/hooks
   - Test with a sample issue/PR

## Troubleshooting

- **Webhook not firing**: Check webhook URL and secret
- **Authentication errors**: Verify private key format and app ID
- **Permission denied**: Ensure app has proper repository permissions
EOF

    log_success "Configuration documentation generated at /tmp/github-app-setup-instructions.md"
}

# Main execution
main() {
    echo "🚀 Open SWE GitHub App Setup"
    echo "============================"

    check_prerequisites
    create_app_manifest
    create_github_app
    generate_k8s_secrets
    install_app_to_repo
    generate_config_docs

    log_success "GitHub App setup completed!"
    log_info "Review the setup instructions at: /tmp/github-app-setup-instructions.md"
    log_info "Apply the Kubernetes secrets with: kubectl apply -f /tmp/github-app-secrets.yaml"
}

# Run main function
main "$@"
