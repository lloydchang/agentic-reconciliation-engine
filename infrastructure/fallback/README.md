# GitOps Infrastructure Control Plane - Fallback Resources Strategy

## Overview
For resources not directly supported by native cloud controllers (ACK/ASO/KCC), follow this hierarchical fallback strategy:

## 1. Official Kubernetes Operator
Use the official operator provided by the project or vendor when available.

Examples:
- cert-manager for TLS certificates
- ingress-nginx for ingress controllers
- external-dns for DNS management
- prometheus-operator for monitoring

## 2. Flux-Managed Kubernetes Job
For one-off or complex deployments, use Flux-managed Jobs to run kubectl or helm commands.

Example:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: deploy-custom-resource
spec:
  template:
    spec:
      containers:
      - name: deployer
        image: bitnami/kubectl:latest
        command: ["kubectl", "apply", "-f", "manifests/"]
        volumeMounts:
        - name: manifests
          mountPath: /manifests
      volumes:
      - name: manifests
        configMap:
          name: custom-manifests
      restartPolicy: OnFailure
```

## 3. Targeted Crossplane Provider (Last Resort)
Only use Crossplane providers when absolutely necessary and no other options exist.
This should be avoided to maintain the no-abstraction principle.

## Current Fallback Resources
None currently needed - all infrastructure managed by native controllers.

## Adding New Fallback Resources
1. Identify the resource requirement
2. Check if native controller support exists
3. If not, evaluate official operator availability
4. Document the decision in this file
5. Implement in infrastructure/fallback/ directory

## Sealed Secrets Architecture and Usage Guide

### Overview
Sealed Secrets is a Kubernetes controller and operator for managing encrypted secrets using asymmetric encryption. It allows you to store encrypted secrets in Git while maintaining the confidentiality of sensitive data.

### Architecture

#### Management Cluster
- **SealedSecrets Controller**: Runs in management cluster to provision workload clusters
- **Purpose**: Encrypt secrets that will be used across workload clusters
- **Location**: `control-plane/controllers/sealed-secrets/`

#### Workload Clusters
- **SealedSecrets Controller**: Must run in each workload cluster that needs to decrypt secrets
- **Purpose**: Decrypt SealedSecret resources into regular Kubernetes secrets at runtime
- **Location**: `infrastructure/tenants/3-workloads/sealed-secrets/` (per workload cluster)

### Sealing Process

#### 1. Install kubeseal CLI
```bash
# Download kubeseal
KUBESEAL_VERSION=$(curl -s https://api.github.com/repos/bitnami-labs/sealed-secrets/releases/latest | jq -r .tag_name)
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/${KUBESEAL_VERSION}/kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz
tar -xzf kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz
sudo install kubeseal /usr/local/bin/
```

#### 2. Get SealedSecrets Certificate (Public Key)
```bash
# Fetch the certificate from the cluster
kubeseal --fetch-cert \
  --controller-name=sealed-secrets \
  --controller-namespace=sealed-secrets-system \
  > pub-cert.pem
```

#### 3. Create and Seal Secrets
```bash
# Create a regular secret first (temporary)
kubectl create secret generic my-secret \
  --from-literal=username=admin \
  --from-literal=password=mypassword \
  --dry-run=client -o yaml > secret.yaml

# Seal the secret using kubeseal
kubeseal --cert=pub-cert.pem \
  --format=yaml \
  < secret.yaml \
  > sealed-secret.yaml

# Clean up temporary secret
rm secret.yaml
```

#### 4. Commit SealedSecret to Git
```bash
git add sealed-secret.yaml
git commit -m "Add encrypted database credentials"
git push
```

#### 5. Deploy to Cluster
The SealedSecrets controller will automatically decrypt the SealedSecret into a regular Kubernetes secret.

### Key Concepts

#### Asymmetric Encryption
- **Public Key**: Used by `kubeseal` to encrypt secrets (can be safely stored in Git)
- **Private Key**: Managed by SealedSecrets controller to decrypt secrets at runtime
- **No External Dependencies**: No external vault or password manager required

#### Scope
- **Cluster-Scoped**: Each Kubernetes cluster has its own SealedSecrets controller
- **Namespace-Scoped**: SealedSecrets can be scoped to specific namespaces
- **Multi-Cluster**: Different clusters can have different encryption keys

### Usage Examples

#### Database Credentials
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: mysql-credentials
  namespace: default
spec:
  encryptedData:
    MYSQL_ROOT_PASSWORD: <encrypted-password>
    MYSQL_DATABASE: <encrypted-database>
  template:
    metadata:
      name: mysql-credentials
    type: Opaque
```

#### Cloud Provider Credentials
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: aws-credentials
  namespace: kube-system
spec:
  encryptedData:
    AWS_ACCESS_KEY_ID: <encrypted-key>
    AWS_SECRET_ACCESS_KEY: <encrypted-secret>
  template:
    metadata:
      name: aws-credentials
    type: Opaque
```

### Security Considerations

#### Certificate Rotation
- Rotate the SealedSecrets certificate periodically
- Use `kubeseal --re-encrypt` to re-encrypt existing secrets with new certificates

#### Access Control
- Limit who can create SealedSecret resources
- Use RBAC to control secret access
- Consider namespace isolation

#### Backup and Recovery
- Backup the SealedSecrets private key securely (not in Git)
- Document certificate rotation procedures
- Plan for disaster recovery scenarios

### Troubleshooting

#### Common Issues
1. **SealedSecret not decrypting**: Check controller logs and certificate validity
2. **Permission denied**: Verify RBAC permissions for SealedSecrets resources
3. **Certificate expired**: Rotate certificates and re-encrypt secrets

#### Debug Commands
```bash
# Check controller status
kubectl get pods -n sealed-secrets-system

# View controller logs
kubectl logs -n sealed-secrets-system deployment/sealed-secrets-controller

# Check secret decryption
kubectl get sealedsecret
kubectl describe sealedsecret <name>
```

### Integration with GitOps

#### Flux Integration
- SealedSecrets work seamlessly with Flux GitOps workflows
- Encrypted secrets are stored in Git alongside other manifests
- Automatic decryption happens during deployment

#### CI/CD Integration
- Use `kubeseal` in CI pipelines to encrypt secrets
- Store encrypted secrets in Git repositories
- Automatic deployment through GitOps

### Alternative Approaches

#### External Secret Operator (ESO)
- For secrets stored in external systems (AWS Secrets Manager, HashiCorp Vault)
- Complements SealedSecrets for hybrid scenarios
- Location: `infrastructure/tenants/3-workloads/external-secrets/`

#### HashiCorp Vault
- Full-featured secret management system
- More complex setup than SealedSecrets
- Better for enterprise secret management

#### Password Managers with CLI/API Access

**Modern password managers** (1Password, LastPass, Bitwarden, etc.) now provide CLI tools and API access that can be used programmatically. These can serve as the **external source of truth** for initial secret creation:

```bash
# Example with 1Password CLI
op item get "database-credentials" --fields username,password

# Or with Bitwarden CLI
bw get item "database-credentials"

# Use in CI/CD pipelines
PASSWORD=$(op item get "db-password" --fields password)
USERNAME=$(op item get "db-username" --fields username)

# Create and seal secret
kubectl create secret generic temp-secret \
  --from-literal=username="$USERNAME" \
  --from-literal=password="$PASSWORD" \
  --dry-run=client -o yaml | \
kubeseal --cert=pub-cert.pem --format=yaml > sealed-secret.yaml
```

### Source of Truth for Initial Secrets

When using SealedSecrets, the **original plaintext secrets** need to be available during the sealing process. Here are recommended approaches:

#### 1. Password Managers (Recommended for Teams)
- **Benefits**: Centralized access, audit trails, secure sharing
- **CLI Support**: Most modern password managers have CLI tools
- **API Access**: REST APIs for CI/CD integration
- **Examples**: 1Password, Bitwarden, LastPass Enterprise

#### 2. Cloud Secret Managers
- **AWS Secrets Manager**, **Azure Key Vault**, **GCP Secret Manager**
- **Benefits**: Native cloud integration, fine-grained access control
- **Use ESO**: External Secrets Operator can pull from these during sealing

#### 3. HashiCorp Vault (Enterprise)
- **Benefits**: Advanced secret management, dynamic secrets, leasing
- **Integration**: Can be used with External Secrets Operator

#### 4. Local Development
- **Environment Variables** or **.env files** (not committed to Git)
- **Benefits**: Simple for development
- **Risk**: Manual process, potential for mistakes

### Recommended Workflow

1. **Store Secrets**: Use password manager as source of truth
2. **Generate Secrets**: Use password manager CLI/API in CI/CD
3. **Seal Secrets**: Use `kubeseal` to encrypt for Git storage
4. **Deploy**: Flux applies SealedSecrets, controller decrypts at runtime

This approach provides:
- ✅ **Secure storage** in password managers
- ✅ **GitOps compatibility** with encrypted secrets in Git
- ✅ **Audit trails** and access control
- ✅ **Programmatic access** for automation
- ✅ **No secrets in plain text** in repositories

### Conclusion

SealedSecrets provides a GitOps-friendly way to manage encrypted secrets without external dependencies. The controller runs in each cluster that needs secret decryption, while the sealing process uses `kubeseal` to encrypt secrets before committing to Git. This approach eliminates the need for external vaults while maintaining security through asymmetric encryption.
