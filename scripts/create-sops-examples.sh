#!/bin/bash

# SOPS Examples Creation Script
# Creates comprehensive examples for different SOPS encryption methods

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."

    if ! command -v sops &> /dev/null; then
        print_error "sops not found. Install with: brew install sops"
        exit 1
    fi

    if ! command -v age-keygen &> /dev/null; then
        print_error "age-keygen not found. Install with: brew install age"
        exit 1
    fi

    print_success "Dependencies OK"
}

# Create examples directory
create_examples_dir() {
    print_status "Creating examples directory..."
    mkdir -p examples/sops
    print_success "Examples directory created"
}

# Age encryption example
create_age_example() {
    print_status "Creating age encryption example..."

    # Create sample secret
    cat > examples/sops/example-secret-age.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: example-age-secret
  namespace: default
  labels:
    app.kubernetes.io/name: example
    app.kubernetes.io/component: secret
    gitops-infra-control-plane.io/encryption: age
type: Opaque
stringData:
  username: admin
  password: my-secret-password
  api-key: sk-1234567890abcdef
  database-url: postgresql://user:pass@host:5432/db
EOF

    # Encrypt with age
    if [ -f "age.agekey" ]; then
        export SOPS_AGE_KEY_FILE=age.agekey
        sops --encrypt --in-place examples/sops/example-secret-age.yaml
        print_success "Age encryption example created"
    else
        print_warning "age.agekey not found - skipping encryption"
        mv examples/sops/example-secret-age.yaml examples/sops/example-secret-age.unencrypted.yaml
    fi
}

# GPG encryption example
create_gpg_example() {
    print_status "Creating GPG encryption example..."

    # Create sample secret
    cat > examples/sops/example-secret-gpg.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: example-gpg-secret
  namespace: default
  labels:
    app.kubernetes.io/name: example
    app.kubernetes.io/component: secret
    gitops-infra-control-plane.io/encryption: gpg
type: Opaque
stringData:
  username: admin
  password: my-secret-password
  api-key: sk-1234567890abcdef
  database-url: postgresql://user:pass@host:5432/db
EOF

    # Note: GPG encryption would require a GPG key setup
    # For now, just create the unencrypted template
    mv examples/sops/example-secret-gpg.yaml examples/sops/example-secret-gpg.unencrypted.yaml
    print_success "GPG encryption template created (requires GPG key setup)"
}

# Cloud KMS examples
create_kms_examples() {
    print_status "Creating cloud KMS encryption examples..."

    # AWS KMS example
    cat > examples/sops/example-secret-aws-kms.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: example-aws-kms-secret
  namespace: default
  labels:
    app.kubernetes.io/name: example
    app.kubernetes.io/component: secret
    gitops-infra-control-plane.io/encryption: aws-kms
type: Opaque
stringData:
  username: admin
  password: my-secret-password
  api-key: sk-1234567890abcdef
  database-url: postgresql://user:pass@host:5432/db
EOF

    # GCP KMS example
    cat > examples/sops/example-secret-gcp-kms.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: example-gcp-kms-secret
  namespace: default
  labels:
    app.kubernetes.io/name: example
    app.kubernetes.io/component: secret
    gitops-infra-control-plane.io/encryption: gcp-kms
type: Opaque
stringData:
  username: admin
  password: my-secret-password
  api-key: sk-1234567890abcdef
  database-url: postgresql://user:pass@host:5432/db
EOF

    # Azure Key Vault example
    cat > examples/sops/example-secret-azure-kv.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: example-azure-kv-secret
  namespace: default
  labels:
    app.kubernetes.io/name: example
    app.kubernetes.io/component: secret
    gitops-infra-control-plane.io/encryption: azure-kv
type: Opaque
stringData:
  username: admin
  password: my-secret-password
  api-key: sk-1234567890abcdef
  database-url: postgresql://user:pass@host:5432/db
EOF

    print_success "Cloud KMS encryption templates created"
}

# Create .sops.yaml configurations for different methods
create_sops_configs() {
    print_status "Creating .sops.yaml configuration examples..."

    # Age configuration
    cat > examples/sops/.sops.yaml.age << 'EOF'
creation_rules:
  - path_regex: .*\.yaml$
    age: age17plgtv2e2w0z8mqhh3fnxxtte2ktpnwuxav6qm27re9hapcqyg0q650q0l
EOF

    # GPG configuration template
    cat > examples/sops/.sops.yaml.gpg << 'EOF'
creation_rules:
  - path_regex: .*\.yaml$
    gpg: YOUR_GPG_FINGERPRINT_HERE
EOF

    # AWS KMS configuration template
    cat > examples/sops/.sops.yaml.aws-kms << 'EOF'
creation_rules:
  - path_regex: .*\.yaml$
    kms: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
EOF

    # GCP KMS configuration template
    cat > examples/sops/.sops.yaml.gcp-kms << 'EOF'
creation_rules:
  - path_regex: .*\.yaml$
    gcp_kms: projects/my-project/locations/us-east1/keyRings/my-keyring/cryptoKeys/my-key
EOF

    # Azure Key Vault configuration template
    cat > examples/sops/.sops.yaml.azure-kv << 'EOF'
creation_rules:
  - path_regex: .*\.yaml$
    azure_kv: https://my-keyvault.vault.azure.net/keys/my-key/
EOF

    print_success "SOPS configuration examples created"
}

# Create documentation
create_documentation() {
    print_status "Creating documentation..."

    cat > examples/sops/README.md << 'EOF'
# SOPS Encryption Examples

This directory contains comprehensive examples for encrypting Kubernetes secrets using SOPS (Secrets OPerationS) with different encryption methods.

## Available Examples

### Age Encryption (Recommended)
- `example-secret-age.yaml` - Encrypted with age (if age key was available)
- `example-secret-age.unencrypted.yaml` - Template for age encryption

### GPG Encryption
- `example-secret-gpg.unencrypted.yaml` - Template for GPG encryption

### Cloud KMS Encryption
- `example-secret-aws-kms.yaml` - Template for AWS KMS encryption
- `example-secret-gcp-kms.yaml` - Template for GCP KMS encryption
- `example-secret-azure-kv.yaml` - Template for Azure Key Vault encryption

## Configuration Files

- `.sops.yaml.age` - Age encryption configuration
- `.sops.yaml.gpg` - GPG encryption configuration template
- `.sops.yaml.aws-kms` - AWS KMS configuration template
- `.sops.yaml.gcp-kms` - GCP KMS configuration template
- `.sops.yaml.azure-kv` - Azure Key Vault configuration template

## Usage

### Encrypting Files

```bash
# Using age (recommended)
export SOPS_AGE_KEY_FILE=age.agekey
sops --encrypt --in-place secret.yaml

# Using GPG
sops --encrypt --in-place --pgp FINGERPRINT secret.yaml

# Using AWS KMS
sops --encrypt --in-place --kms arn:aws:kms:region:account:key/key-id secret.yaml
```

### Decrypting Files

```bash
# Files are automatically decrypted by Flux when using the sops-age secret
sops --decrypt secret.yaml
```

### Team Collaboration

For team collaboration with age encryption:
1. Share the public key from `.sops.pub.age`
2. Team members import it with: `age-keygen -i .sops.pub.age`
3. Everyone can encrypt files that can be decrypted by the cluster

## Security Notes

- Never commit private keys to git
- Use the appropriate encryption method for your environment
- Age encryption is recommended for its simplicity and security
- Cloud KMS methods provide enterprise-grade key management
- GPG is suitable for individual use or small teams

## Integration with GitOps Control Plane

These encrypted secrets are automatically decrypted by Flux when the Kustomization includes:

```yaml
decryption:
  provider: sops
  secretRef:
    name: sops-age
```
EOF

    print_success "Documentation created"
}

# Main execution
main() {
    print_status "Creating SOPS encryption examples..."

    check_dependencies
    create_examples_dir
    create_age_example
    create_gpg_example
    create_kms_examples
    create_sops_configs
    create_documentation

    print_success "All SOPS examples created successfully!"
    print_status "Examples are available in: examples/sops/"
}

main "$@"
EOF
