# Langfuse Configuration Guide

## Overview

Langfuse is an open-source LLM engineering platform for tracing, evaluation, and prompt management. This guide covers the configuration and deployment of Langfuse in the GitOps infrastructure.

## Secret Configuration

### Kubernetes Secret: `langfuse-secrets`

The `langfuse-secrets` secret contains the authentication credentials needed for Langfuse integration.

#### Secret Fields

| Field | Description | Example Value |
|-------|-------------|---------------|
| `public-key` | Langfuse project public key | `lf-xxxxxxxxxxxx` |
| `secret-key` | Langfuse project secret key | `sk-xxxxxxxxxxxx` |
| `otlp-headers` | OTLP authentication headers | `Authorization=Bearer sk-xxxxxxxxxxxx` |

### Base64 Encoding Requirements

Kubernetes Secrets require all data values to be base64-encoded. Use the following commands to encode your credentials:

```bash
# Encode your public key
echo -n 'lf-your-public-key-here' | base64

# Encode your secret key  
echo -n 'sk-your-secret-key-here' | base64

# Encode OTLP headers (replace YOUR_SECRET_KEY with actual secret)
echo -n 'Authorization=Bearer sk-your-secret-key-here' | base64
```

### Deployment Options

#### Option 1: Using the YAML Template (Development)

1. Update `core/config/langfuse-secret.yaml` with your encoded values
2. Apply with kubectl:
   ```bash
   kubectl apply -f core/config/langfuse-secret.yaml -n ai-infrastructure
   ```

#### Option 2: Using kubectl Create Secret (Recommended)

Create the secret directly from environment variables:

```bash
# Set your credentials
export LANGFUSE_PUBLIC_KEY="lf-your-public-key-here"
export LANGFUSE_SECRET_KEY="sk-your-secret-key-here"

# Create the secret
kubectl create secret generic langfuse-secrets \
  --from-literal=public-key="$LANGFUSE_PUBLIC_KEY" \
  --from-literal=secret-key="$LANGFUSE_SECRET_KEY" \
  --from-literal=otlp-headers="Authorization=Bearer $LANGFUSE_SECRET_KEY" \
  -n ai-infrastructure \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### Option 3: Using Sealed Secrets (Production)

For production environments, use sealed secrets to encrypt sensitive data:

```bash
# Install kubeseal if not already installed
brew install kubeseal

# Create and seal the secret
kubectl create secret generic langfuse-secrets \
  --from-literal=public-key="$LANGFUSE_PUBLIC_KEY" \
  --from-literal=secret-key="$LANGFUSE_SECRET_KEY" \
  --from-literal=otlp-headers="Authorization=Bearer $LANGFUSE_SECRET_KEY" \
  -n ai-infrastructure \
  --dry-run=client -o yaml | kubeseal > sealed-langfuse-secret.yaml

# Apply the sealed secret
kubectl apply -f sealed-langfuse-secret.yaml
```

## Security Considerations

### Placeholder Values

The default configuration contains placeholder values that are safe to commit:

- `public-key`: `placeholder-public-key` (base64: `cGxhY2Vob2xkZXItcHVibGljLWtleQ==`)
- `secret-key`: `placeholder-secret-key` (base64: `cGxhY2Vob2xkZXItc2VjcmV0LWtleQ==`)
- `otlp-headers`: `Authorization=Bearer placeholder-secret-key` (base64: `QXV0aG9yaXphdGlvbj1CZWFyZXIgcGxhY2Vob2xkZXItc2VjcmV0LWtleQ==`)

**Important**: Never commit actual credentials to version control.

### Best Practices

1. **Environment Separation**: Use different Langfuse projects for dev/staging/production
2. **Secret Rotation**: Regularly rotate your Langfuse API keys
3. **Access Control**: Limit access to the Langfuse secrets using RBAC
4. **Audit Logging**: Monitor access to the Langfuse configuration
5. **Backup**: Keep secure backups of your Langfuse credentials

## Integration Points

### AI Agents Integration

The AI agents use the Langfuse secret for:

- **Tracing**: Sending execution traces to Langfuse
- **Metrics**: Publishing performance metrics
- **Evaluation**: Recording evaluation results

### Monitoring Integration

Langfuse integrates with the monitoring stack:

- **Prometheus**: Export metrics for scraping
- **Grafana**: Dashboards for Langfuse analytics
- **Alertmanager**: Alerts based on Langfuse metrics

## Troubleshooting

### Common Issues

#### 1. Base64 Encoding Error
```
Error: Secret in version "v1" cannot be handled as a Secret: illegal base64 data at input byte 0
```

**Solution**: Ensure all secret values are properly base64-encoded:
```bash
# Test your encoding
echo -n 'your-value' | base64
```

#### 2. Authentication Failed
```
Error: Authentication failed when connecting to Langfuse
```

**Solution**: Verify your Langfuse credentials are correct and match the project.

#### 3. Namespace Issues
```
Error: namespace "ai-infrastructure" not found
```

**Solution**: Ensure the namespace exists:
```bash
kubectl create namespace ai-infrastructure
```

### Verification Commands

```bash
# Check secret exists
kubectl get secret langfuse-secrets -n ai-infrastructure

# View secret (decoded)
kubectl get secret langfuse-secrets -n ai-infrastructure -o jsonpath='{.data.public-key}' | base64 --decode

# Test Langfuse connectivity
kubectl run langfuse-test --image=langfuse/langfuse-server:latest --rm -it --restart=Never \
  --env="LANGFUSE_PUBLIC_KEY=$(kubectl get secret langfuse-secrets -n ai-infrastructure -o jsonpath='{.data.public-key}' | base64 --decode)" \
  --env="LANGFUSE_SECRET_KEY=$(kubectl get secret langfuse-secrets -n ai-infrastructure -o jsonpath='{.data.secret-key}' | base64 --decode)"
```

## References

- [Langfuse Documentation](https://langfuse.com/docs)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Sealed Secrets Controller](https://github.com/bitnami-labs/sealed-secrets)

## Support

For issues related to Langfuse configuration:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [Langfuse documentation](https://langfuse.com/docs)
3. Contact the infrastructure team for production deployments

---

**Last Updated**: 2026-03-18
**Version**: 1.0
