# SOPS Example Deployment

This example demonstrates how to use SOPS-encrypted secrets in the GitOps Infra Control Plane with a complete WordPress deployment.

## Overview

This example shows:
- **Encrypted secrets management** using SOPS with age encryption
- **Database deployment** with encrypted credentials
- **Application deployment** consuming encrypted secrets
- **Flux integration** with automatic decryption
- **Dependency management** using Flux `dependsOn`

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WordPress     │    │   MySQL DB      │    │  SOPS Secrets  │
│   (Frontend)    │───▶│   (Database)    │◀───│   (Encrypted)   │
│                 │    │                 │    │                 │
│ - Web Server    │    │ - MySQL 8.0     │    │ - DB Credentials│
│ - PHP Runtime   │    │ - Persistent    │    │ - API Keys      │
│ - HTTP Service  │    │   Storage       │    │ - TLS Certs     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### Secrets (Encrypted)
- **`database-credentials.secret.yaml`** - Database connection credentials
- **`registry-credentials.secret.yaml`** - Container registry credentials  
- **`tls-certificate.secret.yaml`** - TLS certificates
- **`external-api-keys.secret.yaml`** - External service API keys

### Database
- **MySQL 8.0** deployment with persistent storage
- **Service** for database connectivity
- **ConfigMap** for MySQL configuration
- **PVC** for data persistence
- **Init job** for database initialization

### Application
- **WordPress 6.4** deployment with Apache
- **Service** for web access
- **PVC** for content storage
- **ConfigMap** for WordPress configuration

## Deployment Flow

1. **Secret Decryption** - Flux decrypts SOPS-encrypted secrets using age key
2. **Database Deployment** - MySQL starts with encrypted credentials
3. **Application Deployment** - WordPress connects using decrypted secrets
4. **Service Exposure** - Services become available for connectivity

## Prerequisites

- Kubernetes cluster with Flux installed
- SOPS and age CLI tools installed locally
- `sops-age` secret created in `flux-system` namespace
- Valid SOPS configuration (`.sops.yaml`)

## Quick Start

### 1. Set up SOPS (if not already done)

```bash
# Generate age keys and create Kubernetes secret
./scripts/setup-sops-keys.sh

# Update .sops.yaml with the generated public key
# (Script will output the key to use)
```

### 2. Encrypt the secrets

```bash
# Encrypt all example secrets
export AGE_KEY="age1your-public-key-here"
./scripts/encrypt-secrets.sh

# Or encrypt manually
sops --encrypt --in-place database-credentials.secret.yaml
```

### 3. Deploy the example

```bash
# Add to your GitOps repository
git add examples/complete-hub-spoke/sops-example/
git commit -m "Add SOPS example deployment"
git push

# Flux will automatically deploy and decrypt the secrets
```

### 4. Verify deployment

```bash
# Check that secrets are applied
kubectl get secrets -n default

# Check pod status
kubectl get pods -n default

# Check WordPress is running
kubectl get deployment wordpress -n default

# Access WordPress (if you have an ingress)
kubectl port-forward service/wordpress-service 8080:80
# Then visit http://localhost:8080
```

## Secret Management

### Creating New Secrets

```bash
# Create a secret manifest
kubectl create secret generic my-secret \
  --from-literal=key=value \
  --namespace=default \
  --dry-run=client -o yaml > my-secret.yaml

# Encrypt with SOPS
sops --encrypt --in-place my-secret.yaml

# Add to GitOps
git add my-secret.yaml
git commit -m "Add encrypted secret"
```

### Editing Existing Secrets

```bash
# Edit (decrypts, opens editor, re-encrypts on save)
sops database-credentials.secret.yaml

# Or decrypt to temp file, edit, then re-encrypt
sops --decrypt database-credentials.secret.yaml > temp.yaml
# Edit temp.yaml
sops --encrypt --in-place temp.yaml
mv temp.yaml database-credentials.secret.yaml
```

### Rotating Secrets

```bash
# Update the secret values
kubectl create secret generic database-credentials \
  --from-literal=username=new-user \
  --from-literal=password=new-password \
  --namespace=default \
  --dry-run=client -o yaml > database-credentials.secret.yaml

# Re-encrypt
sops --encrypt --in-place database-credentials.secret.yaml

# Deploy
git add database-credentials.secret.yaml
git commit -m "Rotate database credentials"
git push
```

## Configuration

### SOPS Configuration (.sops.yaml)

```yaml
creation_rules:
  - path_regex: infrastructure/.*\.secret\.yaml$
    age: age1your-public-key-here
    encrypted_regex: '^(data|stringData)$'
```

### Flux Kustomization

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: sops-example
spec:
  # ... other fields ...
  decryption:
    provider: sops
    secretRef:
      name: sops-age
```

## Security Best Practices

1. **Never commit private keys** to Git repositories
2. **Use separate keys** for different environments
3. **Regularly rotate keys** and re-encrypt secrets
4. **Limit access** to the `sops-age` Kubernetes secret
5. **Monitor secret access** and decryption failures
6. **Use RBAC** to control who can apply secrets

## Troubleshooting

### Common Issues

1. **Decryption fails in cluster:**
   ```bash
   # Check if sops-age secret exists
   kubectl get secret sops-age -n flux-system
   
   # Check Flux logs
   kubectl logs -n flux-system deployment/kustomize-controller
   ```

2. **SOPS encryption fails locally:**
   ```bash
   # Validate SOPS configuration
   ./scripts/validate-sops-config.sh
   
   # Check age key
   age-keygen -y .sops-keys/age.agekey
   ```

3. **Secrets not applied:**
   ```bash
   # Check Flux reconciliation
   flux get kustomizations --namespace=flux-system
   
   # Check secret decryption
   kubectl get secrets -n default
   ```

### Debug Commands

```bash
# Test SOPS workflow
./scripts/test-sops-workflow.sh

# Health check
./scripts/sops-health-check.sh

# Validate configuration
./scripts/validate-sops-config.sh
```

## Monitoring

The example includes monitoring configuration for:

- **SOPS decryption failures** - Alert when Flux can't decrypt secrets
- **Missing SOPS keys** - Alert when age key is unavailable
- **Secret age** - Alert for old secrets that need rotation
- **Decryption error rate** - Alert for high decryption failure rates

Access the monitoring dashboard:
```bash
# Check Prometheus rules
kubectl get prometheusrules -n flux-system

# View Grafana dashboard
kubectl port-forward service/grafana 3000:3000
```

## Next Steps

1. **Customize the example** for your specific application
2. **Add more secrets** for your application needs
3. **Set up monitoring** for SOPS operations
4. **Implement secret rotation** policies
5. **Add Git hooks** for SOPS validation

## References

- [SOPS Documentation](https://github.com/getsops/sops)
- [Flux SOPS Guide](https://fluxcd.io/flux/guides/sops/)
- [Age Encryption](https://github.com/FiloSottile/age)
- [GitOps Infra Control Plane](../../README.md)

---

**Security Note:** This example uses encrypted secrets, but ensure you follow proper security practices for your production environment including key rotation, access control, and audit logging.
