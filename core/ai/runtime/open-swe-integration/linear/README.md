# Linear Integration Implementation

## Overview

Linear integration has been added to the Open SWE + GitOps Control Plane, enabling issue-based automation and natural language command processing from Linear issues.

## Components Added

### 1. Linear Webhook Handler
- **Endpoint**: `/webhooks/linear`
- **Function**: Processes Linear webhook events for issue creation, updates, and comments
- **Location**: `linear/handler.go`

### 2. Linear Configuration
- **ConfigMap**: `linear-integration-config`
- **Features**: Issue triage, priority mapping, GitOps integration, command patterns
- **Location**: `kubernetes/linear-configmap.yaml`

### 3. Linear Secrets
- **Secret**: `linear-secrets`
- **Contents**: Webhook secret and API token (base64 encoded)
- **Location**: `kubernetes/linear-secrets.yaml`

### 4. Ingress Updates
- **Route**: Added `/webhooks/linear` path to existing ingress
- **Backend**: Routes to same service as Slack integration
- **Location**: Updated `kubernetes/ingress.yaml`

## Linear Integration Features

### Issue Processing
- **Auto-triage**: Automatically assigns issues to infrastructure team
- **Priority Mapping**: Maps Linear priorities to GitOps risk levels
- **Issue Types**: Supports Bug, Feature, Task, Improvement, Security

### GitOps Integration
- **PR Creation**: Automatically creates pull requests for issues
- **Commit Linking**: Links commits to related issues
- **Status Sync**: Syncs issue status with deployment status

### Command Patterns
The integration recognizes natural language patterns in Linear issues:

- **Deploy**: "deploy to production" → `deployment-strategy` skill
- **Optimize**: "optimize costs" → `optimize-costs` skill
- **Secure**: "security scan" → `analyze-security` skill
- **Scale**: "scale frontend service" → `scale-resources` skill
- **Monitor**: "check cluster health" → `check-cluster-health` skill
- **Troubleshoot**: "troubleshoot network issue" → `diagnose-network` skill
- **Certificate**: "renew api.example.com certificate" → `manage-certificates` skill
- **Database**: "database maintenance" → `maintain-databases` skill
- **Cluster**: "cluster upgrade" → `manage-kubernetes-cluster` skill
- **Compliance**: "compliance report" → `generate-compliance-report` skill
- **Audit**: "security audit" → `audit-security-events` skill
- **Secrets**: "rotate api secrets" → `rotate-secrets` skill

## Deployment Status

✅ **Linear integration deployed successfully**

### Resources Created
- ConfigMap: `linear-integration-config`
- Secret: `linear-secrets`
- Ingress: Updated with Linear webhook route
- Application: Updated with Linear webhook handler

### Next Steps

1. **Configure Linear Webhook**:
   - Go to Linear workspace settings
   - Create webhook pointing to: `https://slack-integration.gitops.example.com/webhooks/linear`
   - Set webhook secret in `linear-secrets`

2. **Update API Token**:
   - Generate Linear API token
   - Update `linear-secrets` with base64 encoded token

3. **Test Integration**:
   - Create test issue in Linear
   - Verify webhook processing
   - Check command recognition

## Configuration

### Webhook Setup
```bash
# Update Linear webhook secret
echo -n "your-linear-webhook-secret" | base64
kubectl edit secret linear-secrets -n ai-infrastructure

# Update Linear API token
echo -n "your-linear-api-token" | base64
kubectl edit secret linear-secrets -n ai-infrastructure
```

### Feature Flags
Enable Linear integration in main config:
```yaml
feature_flags:
  enable_linear_integration: true
```

## Testing

### Webhook Test
```bash
# Test Linear webhook endpoint
kubectl port-forward -n ai-infrastructure svc/slack-integration-service 8080:80 &
curl -X POST http://localhost:8080/webhooks/linear \
  -H "Content-Type: application/json" \
  -d '{"action":"issue_created","data":{"title":"Test issue"}}'
```

### Issue Processing Test
1. Create issue in Linear with title: "Deploy to staging environment"
2. Verify webhook receives the event
3. Check that command is recognized and routed to `deployment-strategy` skill

## Security

- ✅ Webhook signature validation (when configured)
- ✅ HTTPS encryption via ingress
- ✅ RBAC permissions for required resources
- ✅ Secret management for API tokens
- ✅ Rate limiting on ingress

## Monitoring

Linear integration metrics are included in existing monitoring:
- Webhook request count and success rate
- Issue processing latency
- Command recognition accuracy
- GitOps workflow triggers

## Architecture

```
Linear → Webhook → Integration Service → Command Router → Temporal → GitOps
```

The Linear integration follows the same security and safety patterns as the Slack integration, ensuring all operations flow through the GitOps control plane with proper validation and human oversight.
