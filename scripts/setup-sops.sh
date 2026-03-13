#!/bin/bash

# SOPS Setup Script for GitOps Infrastructure Control Plane
# This script sets up SOPS encryption for Kubernetes secrets using age (recommended)
# or GPG as alternatives.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CLUSTER_NAME="${CLUSTER_NAME:-cluster0.yourdomain.com}"
NAMESPACE="${NAMESPACE:-flux-system}"
ENCRYPTION_METHOD="${ENCRYPTION_METHOD:-age}" # age, gpg, or cloud
CLOUD_PROVIDER="${CLOUD_PROVIDER:-aws}" # aws, azure, gcp

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    if ! command -v sops &> /dev/null; then
        print_error "SOPS is not installed. Please install it first:"
        echo "  brew install sops"
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install it first."
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        print_error "Unable to connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Setup age encryption (recommended method)
setup_age() {
    print_status "Setting up age encryption..."

    # Generate age key pair
    if [ ! -f "age.agekey" ]; then
        print_status "Generating age key pair..."
        age-keygen -o age.agekey
        print_success "Age key pair generated"
    else
        print_warning "Age key file already exists, skipping generation"
    fi

    # Extract public key
    AGE_PUBLIC_KEY=$(grep "public key:" age.agekey | cut -d' ' -f4)
    print_status "Age public key: $AGE_PUBLIC_KEY"

    # Create Kubernetes secret
    print_status "Creating Kubernetes secret for age key..."
    kubectl create secret generic sops-age \
        --namespace=$NAMESPACE \
        --from-file=age.agekey=age.agekey \
        --dry-run=client -o yaml | kubectl apply -f -

    print_success "Age encryption setup completed"
}

# Setup GPG encryption (alternative method)
setup_gpg() {
    print_status "Setting up GPG encryption..."

    if ! command -v gpg &> /dev/null; then
        print_error "GPG is not installed. Please install gnupg first:"
        echo "  brew install gnupg"
        exit 1
    fi

    # Generate GPG key
    export KEY_NAME="$CLUSTER_NAME"
    export KEY_COMMENT="flux secrets"

    if ! gpg --list-secret-keys "$KEY_NAME" &> /dev/null; then
        print_status "Generating GPG key pair..."
        gpg --batch --full-generate-key <<EOF
%no-protection
Key-Type: 1
Key-Length: 4096
Subkey-Type: 1
Subkey-Length: 4096
Expire-Date: 0
Name-Comment: ${KEY_COMMENT}
Name-Real: ${KEY_NAME}
EOF
        print_success "GPG key pair generated"
    else
        print_warning "GPG key already exists for $KEY_NAME"
    fi

    # Get key fingerprint
    export KEY_FP=$(gpg --list-secret-keys "$KEY_NAME" | grep -E "^\s+" | head -1 | tr -d ' ')
    print_status "GPG key fingerprint: $KEY_FP"

    # Export secret key to Kubernetes
    print_status "Creating Kubernetes secret for GPG key..."
    gpg --export-secret-keys --armor "$KEY_FP" | \
        kubectl create secret generic sops-gpg \
        --namespace=$NAMESPACE \
        --from-file=sops.asc=/dev/stdin \
        --dry-run=client -o yaml | kubectl apply -f -

    print_success "GPG encryption setup completed"
}

# Setup cloud KMS (AWS KMS, Azure Key Vault, GCP KMS)
setup_cloud_kms() {
    print_status "Setting up $CLOUD_PROVIDER KMS encryption..."

    case $CLOUD_PROVIDER in
        aws)
            print_status "AWS KMS setup requires IAM role binding to kustomize-controller service account"
            print_warning "Please ensure the kustomize-controller has access to your KMS key"
            ;;
        azure)
            print_status "Azure Key Vault setup requires managed identity or service principal"
            print_warning "Please ensure the kustomize-controller has access to your Key Vault"
            ;;
        gcp)
            print_status "GCP KMS setup requires Workload Identity or service account key"
            print_warning "Please ensure the kustomize-controller has access to your KMS key"
            ;;
        *)
            print_error "Unsupported cloud provider: $CLOUD_PROVIDER"
            exit 1
            ;;
    esac

    print_success "Cloud KMS setup completed (manual IAM/role configuration required)"
}

# Create SOPS configuration
create_sops_config() {
    print_status "Creating SOPS configuration..."

    case $ENCRYPTION_METHOD in
        age)
            if [ -z "$AGE_PUBLIC_KEY" ]; then
                AGE_PUBLIC_KEY=$(grep "public key:" age.agekey | cut -d' ' -f4)
            fi
            cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: .*.yaml
    encrypted_regex: ^(data|stringData)$
    age: ${AGE_PUBLIC_KEY}
EOF
            ;;
        gpg)
            cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: .*.yaml
    encrypted_regex: ^(data|stringData)$
    pgp: ${KEY_FP}
EOF
            ;;
        cloud)
            case $CLOUD_PROVIDER in
                aws)
                    cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: .*.yaml
    encrypted_regex: ^(data|stringData)$
    kms: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
EOF
                    ;;
                azure)
                    cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: .*.yaml
    encrypted_regex: ^(data|stringData)$
    azure_keyvault: https://mykeyvault.vault.azure.net/keys/mykey
EOF
                    ;;
                gcp)
                    cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: .*.yaml
    encrypted_regex: ^(data|stringData)$
    gcp_kms: projects/my-project/locations/us-east1/keyRings/my-key-ring/cryptoKeys/my-key
EOF
                    ;;
            esac
            ;;
    esac

    print_success "SOPS configuration created"
}

# Update Flux Kustomization with SOPS decryption
update_flux_kustomization() {
    print_status "Updating Flux Kustomization with SOPS decryption..."

    local kustomization_file="$1"
    local secret_name="$2"

    if [ ! -f "$kustomization_file" ]; then
        print_error "Kustomization file not found: $kustomization_file"
        return 1
    fi

    # Add decryption configuration to existing Kustomization
    if ! grep -q "decryption:" "$kustomization_file"; then
        # Insert decryption config before spec.healthChecks or at end of spec
        if grep -q "healthChecks:" "$kustomization_file"; then
            sed -i.bak "/healthChecks:/i\\
  decryption:\\
    provider: sops\\
    secretRef:\\
      name: $secret_name\\
" "$kustomization_file"
        else
            sed -i.bak "/spec:/a\\
  decryption:\\
    provider: sops\\
    secretRef:\\
      name: $secret_name\\
" "$kustomization_file"
        fi
        print_success "Updated $kustomization_file with SOPS decryption"
    else
        print_warning "Decryption already configured in $kustomization_file"
    fi
}

# Main execution
main() {
    echo "SOPS Setup Script for GitOps Infrastructure Control Plane"
    echo "======================================================"
    echo "Cluster: $CLUSTER_NAME"
    echo "Namespace: $NAMESPACE"
    echo "Encryption Method: $ENCRYPTION_METHOD"
    if [ "$ENCRYPTION_METHOD" = "cloud" ]; then
        echo "Cloud Provider: $CLOUD_PROVIDER"
    fi
    echo ""

    check_prerequisites

    case $ENCRYPTION_METHOD in
        age)
            setup_age
            SECRET_NAME="sops-age"
            ;;
        gpg)
            setup_gpg
            SECRET_NAME="sops-gpg"
            ;;
        cloud)
            setup_cloud_kms
            SECRET_NAME="" # No secret needed for cloud KMS
            ;;
        *)
            print_error "Invalid encryption method: $ENCRYPTION_METHOD"
            echo "Valid options: age, gpg, cloud"
            exit 1
            ;;
    esac

    create_sops_config

    # Update relevant Kustomizations
    if [ -n "$SECRET_NAME" ]; then
        # Update control-plane kustomization
        update_flux_kustomization "control-plane/kustomization.yaml" "$SECRET_NAME"

        # Update infrastructure kustomizations
        for tenant_dir in infrastructure/tenants/*/; do
            if [ -f "${tenant_dir}kustomization.yaml" ]; then
                update_flux_kustomization "${tenant_dir}kustomization.yaml" "$SECRET_NAME"
            fi
        done
    fi

    print_success "SOPS setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Commit the .sops.yaml file to your repository"
    echo "2. Use 'sops --encrypt --in-place secret.yaml' to encrypt secrets"
    echo "3. Test the decryption by applying manifests to your cluster"
    echo ""
    if [ "$ENCRYPTION_METHOD" = "cloud" ]; then
        echo "Cloud KMS Note: Ensure proper IAM roles/service accounts are configured"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cluster-name)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --encryption-method)
            ENCRYPTION_METHOD="$2"
            shift 2
            ;;
        --cloud-provider)
            CLOUD_PROVIDER="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --cluster-name NAME      Cluster name (default: cluster0.yourdomain.com)"
            echo "  --namespace NS           Kubernetes namespace (default: flux-system)"
            echo "  --encryption-method METHOD  Encryption method: age, gpg, or cloud (default: age)"
            echo "  --cloud-provider PROVIDER  Cloud provider for KMS: aws, azure, gcp (default: aws)"
            echo "  --help                   Show this help"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

main
