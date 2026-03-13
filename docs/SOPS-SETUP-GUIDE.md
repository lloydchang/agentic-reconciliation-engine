# SOPS Setup Guide for GitOps Infra Control Plane

This guide provides comprehensive instructions for setting up and managing encrypted secrets using SOPS (Secrets OPerationS) with Flux in the GitOps Infra Control Plane.

## Overview

SOPS allows you to securely store encrypted secrets in Git repositories while maintaining the GitOps workflow. This setup uses age encryption (recommended over GPG) for simplicity and security.

## Prerequisites

- Kubernetes cluster with Flux installed
- `kubectl` configured to access your cluster
- `age` and `sops` CLI tools installed
- Access to the GitOps Infra Control Plane repository

### Install Required Tools

```bash
# macOS
brew install age sops

# Linux
# For age
curl -L https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz | tar xz
sudo mv age/age /usr/local/bin/
sudo mv age/age-keygen /usr/local/bin/

# For SOPS
curl -L https://github.com/getsops/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64 -o sops
chmod +x sops
sudo mv sops /usr/local/bin/
```

## Quick Start

### 1. Initial Setup (Repository Maintainer)

Run the setup script to generate age keys and create the Kubernetes secret:

```bash
# Make the script executable
chmod +x scripts/setup-sops-keys.sh

# Run the setup
./scripts/setup-sops-keys.sh
```

This will:
- Generate a new age key pair
- Create the `sops-age` Kubernetes secret in the `flux-system` namespace
- Update your `.sops.yaml` with the public key

### 2. Update SOPS Configuration

After running the setup script, update your `.sops.yaml` file with the actual public key generated:

```yaml
creation_rules:
  - path_regex: .*.yaml$
    age: age1your-actual-public-key-here
    encrypted_regex: '^(data|stringData)$'
```

### 3. Encrypt Example Secrets

Encrypt the provided example secrets:

```bash
# Make the script executable
chmod +x scripts/encrypt-secrets.sh

# Set your age key (from setup script output)
export AGE_KEY="age1your-actual-public-key-here"

# Encrypt all secrets
./scripts/encrypt-secrets.sh
```

### 4. Deploy to Cluster

Commit the changes and let Flux handle the rest:

```bash
git add .
git commit -m "Add SOPS encrypted secrets and configuration"
git push
```

Flux will automatically decrypt the secrets and apply them to your cluster.

## Team Member Setup

### New Team Member Onboarding

New team members can set up their local environment using the team setup script:

```bash
# Make the script executable
chmod +x scripts/setup-team-member.sh

# Run the setup
./scripts/setup-team-member.sh
```

This will:
- Import the shared public key from `.sops.pub.age`
- Configure local SOPS settings
- Test the encryption/decryption workflow

### Creating New Secrets

1. **Create a secret manifest:**

```bash
kubectl create secret generic my-app-secret \
  --from-literal=database-url="postgresql://user:pass@host:5432/db" \
  --from-literal=api-key="your-api-key-here" \
  --namespace=default \
  --dry-run=client -o yaml > my-app-secret.yaml
```

2. **Encrypt the secret:**

```bash
sops --encrypt --in-place my-app-secret.yaml
```

3. **Add to Git:**

```bash
git add my-app-secret.yaml
git commit -m "Add encrypted secret for my-app"
git push
```

### Editing Existing Secrets

To edit an encrypted secret:

```bash
# This will decrypt, open in $EDITOR, and re-encrypt on save
sops my-app-secret.yaml
```

Or to decrypt to a temporary file:

```bash
sops --decrypt my-app-secret.yaml > my-app-secret-decrypted.yaml
# Edit the file...
# Re-encrypt when done:
sops --encrypt --in-place my-app-secret.yaml
```

## Advanced Configuration

### Multiple Environments

For different environments (dev/staging/prod), you can use separate SOPS configurations:

```yaml
# .sops.yaml
creation_rules:
  # Development secrets
  - path_regex: dev/.*\.yaml$
    age: age1dev-key-here
    encrypted_regex: '^(data|stringData)$'
  
  # Production secrets
  - path_regex: prod/.*\.yaml$
    age: age1prod-key-here
    encrypted_regex: '^(data|stringData)$'
```

### Key Rotation

To rotate encryption keys:

1. **Generate new age key:**
```bash
age-keygen -o age-new.agekey
```

2. **Update .sops.yaml** with the new key
3. **Re-encrypt all secrets:**
```bash
find . -name "*.secret.yaml" -exec sops --encrypt --in-place {} \;
```

4. **Update cluster secret:**
```bash
cat age-new.agekey | kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey=/dev/stdin \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Backup and Recovery

**Important:** Always backup your age private key securely:

```bash
# Store in password manager or secure location
cp .sops-keys/age.agekey ~/.password-manager/age-key-backup.agekey

# Or create an encrypted backup
gpg --symmetric --cipher-algo AES256 .sops-keys/age.agekey
```

## Flux Integration

### Kustomization Configuration

The Flux Kustomizations are configured with SOPS decryption:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: tenant-secrets
  namespace: flux-system
spec:
  # ... other fields ...
  decryption:
    provider: sops
    secretRef:
      name: sops-age-key
```

### Verification

Check that Flux can decrypt secrets:

```bash
# Check Flux reconciliation status
flux get kustomizations --namespace=flux-system

# Check if secrets are applied
kubectl get secrets --namespace=default

# Check specific secret
kubectl get secret database-credentials --namespace=default -o yaml
```

## Troubleshooting

### Common Issues

1. **Decryption fails in cluster:**
   - Verify the `sops-age` secret exists and contains the correct private key
   - Check that the age key in `.sops.yaml` matches the public key used for encryption

2. **SOPS encryption fails locally:**
   - Ensure you have the correct age key
   - Verify the file matches one of the `path_regex` patterns in `.sops.yaml`

3. **Team member can't encrypt:**
   - Ensure they've imported the public key from `.sops.pub.age`
   - Check their local `.sops.yaml` configuration

### Debug Commands

```bash
# Test SOPS configuration
sops --config .sops.yaml --encrypt --dry-run my-secret.yaml

# Verify age key
age-keygen -y .sops-keys/age.agekey

# Check Flux logs
kubectl logs -n flux-system deployment/kustomize-controller
```

## Security Best Practices

1. **Never commit private keys** to Git repositories
2. **Use separate keys** for different environments
3. **Regularly rotate keys** and re-encrypt secrets
4. **Limit access** to the `sops-age` Kubernetes secret
5. **Monitor access** to encrypted secrets in Git
6. **Use RBAC** to control who can apply secrets to clusters

## File Structure

```
gitops-infra-control-plane/
├── .sops.yaml                    # SOPS configuration
├── .sops.pub.age                 # Public key for team sharing
├── scripts/
│   ├── setup-sops-keys.sh        # Initial setup script
│   ├── encrypt-secrets.sh        # Bulk encryption script
│   └── setup-team-member.sh      # Team member onboarding
├── infrastructure/
│   └── tenants/
│       ├── *.secret.yaml         # Encrypted secrets
│       └── kustomization.yaml    # Kustomization with secrets
└── docs/
    └── SOPS-SETUP-GUIDE.md       # This guide
```

## Support

For issues and questions:

1. Check the [Flux SOPS documentation](https://fluxcd.io/flux/guides/sops/)
2. Review the [SOPS documentation](https://github.com/getsops/sops)
3. Check the troubleshooting section above
4. Open an issue in the repository

---

**Remember:** The security of your secrets depends on properly managing the age private keys. Always follow security best practices and never expose private keys in version control.
