---
name: secrets-certificate-manager
description: >
  Use this skill to manage secrets, API keys, connection strings, and TLS
  certificates across cloud secret stores and Kubernetes clusters. Triggers:
  any request to rotate a secret, renew a certificate, audit secret access,
  detect expiring certs, inject secrets into workloads, set up cert-manager,
  migrate secrets between environments, or detect hardcoded credentials in
  infrastructure or application code.
tools:
  - bash
  - computer
---

# Secrets & Certificate Manager Skill

Automate the full secrets and certificate lifecycle: centralised storage,
automatic rotation, expiry monitoring, workload injection, and audit trail —
across Azure Key Vault, AWS Secrets Manager, HashiCorp Vault, and Kubernetes
Secrets with cert-manager.

---

## Secret Store Backends

| Backend                 | Auth                          | CLI / SDK               |
|-------------------------|-------------------------------|-------------------------|
| Azure Key Vault         | Managed Identity / SP         | `az keyvault`           |
| AWS Secrets Manager     | IAM Role / IRSA               | `aws secretsmanager`    |
| HashiCorp Vault         | AppRole / K8s Auth            | `vault`                 |
| Kubernetes Secrets      | RBAC / Service Account        | `kubectl`               |
| GCP Secret Manager      | Workload Identity             | `gcloud secrets`        |

---

## Secret Lifecycle

### Create / Update a Secret
```bash
# Azure Key Vault
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "$SECRET_NAME" \
  --value "$SECRET_VALUE" \
  --expires "$(date -d '+90 days' +%Y-%m-%dT%H:%M:%SZ)" \
  --tags "owner=$OWNER" "service=$SERVICE" "rotation=auto"

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name "$SECRET_NAME" \
  --secret-string "$SECRET_VALUE" \
  --tags Key=owner,Value="$OWNER" Key=service,Value="$SERVICE"

# Kubernetes Secret (sealed with kubeseal)
echo -n "$SECRET_VALUE" | \
  kubectl create secret generic "$SECRET_NAME" \
  --from-literal=value=/dev/stdin \
  --dry-run=client -o yaml | \
  kubeseal --controller-namespace sealed-secrets > sealed-secret.yaml
```

### Read a Secret (for diagnosis only — never log values)
```bash
# Check existence without exposing value
az keyvault secret show --vault-name "$VAULT_NAME" --name "$SECRET_NAME" \
  --query "{name:name, expires:attributes.expires, enabled:attributes.enabled}" \
  --output json
```

---

## Secret Rotation

### Automatic Rotation Workflow
```bash
rotate_secret() {
  local secret_name=$1
  local generator=$2

  # 1. Generate new value
  NEW_VALUE=$(eval "$generator")

  # 2. Validate new value works (service-specific health check)
  validate_secret "$secret_name" "$NEW_VALUE" || {
    echo "Validation failed — aborting rotation"
    return 1
  }

  # 3. Store new version (keep old version active for 1hr overlap)
  az keyvault secret set \
    --vault-name "$VAULT_NAME" \
    --name "$secret_name" \
    --value "$NEW_VALUE"

  # 4. Trigger rolling restart to pick up new secret
  kubectl rollout restart deployment \
    -l "secret=$secret_name" -n "$NAMESPACE"

  # 5. Confirm pods are healthy with new secret
  kubectl rollout status deployment \
    -l "secret=$secret_name" -n "$NAMESPACE" --timeout=5m

  # 6. Disable old secret version
  az keyvault secret set-attributes \
    --vault-name "$VAULT_NAME" \
    --name "$secret_name" \
    --version "$OLD_VERSION" \
    --enabled false

  echo "Rotation complete for $secret_name"
}
```

### Rotation Schedule
| Secret type                   | Rotation interval | Auto-rotatable |
|-------------------------------|-------------------|----------------|
| Database passwords            | 90 days           | ✅             |
| API keys (internal services)  | 90 days           | ✅             |
| Service principal credentials | 180 days          | ✅             |
| Customer-facing API keys      | On-demand         | ⚠️ Notify first |
| SSH keys                      | 365 days          | ✅             |
| JWT signing keys              | 180 days          | ✅             |
| Encryption keys (KEK)         | 365 days          | ⚠️ Needs approval |

---

## Certificate Management (cert-manager)

### Install cert-manager
```bash
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true \
  --set prometheus.enabled=true
```

### Create a ClusterIssuer (Let's Encrypt + Azure DNS)
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@company.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - dns01:
        azureDNS:
          subscriptionID: $SUBSCRIPTION_ID
          resourceGroupName: $DNS_RG
          hostedZoneName: $ZONE
          managedIdentity:
            clientID: $IDENTITY_CLIENT_ID
```

### Create a Certificate
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ${TENANT_ID}-tls
  namespace: $NAMESPACE
spec:
  secretName: ${TENANT_ID}-tls-secret
  dnsNames:
    - ${TENANT_ID}.app.company.com
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  duration: 2160h  # 90 days
  renewBefore: 360h  # Renew 15 days before expiry
```

### Expiry Monitoring
```bash
# List all certs and days until expiry
kubectl get certificates -A -o json | \
  jq -r '.items[] | {
    namespace: .metadata.namespace,
    name: .metadata.name,
    expiry: .status.notAfter,
    ready: .status.conditions[]? | select(.type=="Ready") | .status
  }'

# Alert if any cert expires within 30 days
kubectl get certificates -A -o json | \
  jq -r '.items[] | select(
    (.status.notAfter | fromdateiso8601) < (now + 30*86400)
  ) | "\(.metadata.namespace)/\(.metadata.name) expires \(.status.notAfter)"'
```

---

## Hardcoded Secret Detection

```bash
# Scan entire repo for secrets
gitleaks detect --source . \
  --report-format json \
  --report-path reports/secrets.json

# Scan Kubernetes secrets for base64-encoded sensitive patterns
kubectl get secrets -A -o json | \
  jq -r '.items[] | .data // {} | to_entries[] |
    "\(.key): \(.value | @base64d)"' | \
  grep -iE "password|key|token|secret|credential" | \
  grep -v "^#"
```

On detection:
1. Block PR / commit
2. Classify: API key, DB password, cert private key, etc.
3. Auto-rotate if integration exists
4. Notify committer + security team
5. Log to audit trail

---

## Kubernetes Secrets Best Practices

Enforce these standards via OPA/Gatekeeper:
- All Secrets stored in Key Vault / Secrets Manager, not plaintext YAML
- Secrets synced to pods via External Secrets Operator (ESO) or CSI driver
- No `env` injection of secrets (use mounted volumes or ESO refs)
- `imagePullSecrets` rotated every 180 days
- Secret access audited via K8s audit log → SIEM

```yaml
# External Secrets Operator — sync from Azure Key Vault
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: ${SERVICE}-secrets
  namespace: $NAMESPACE
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: azure-keyvault
    kind: ClusterSecretStore
  target:
    name: ${SERVICE}-secrets
  data:
    - secretKey: db-password
      remoteRef:
        key: ${SERVICE}-db-password
```

---

## Audit & Compliance

```bash
# Azure — who accessed Key Vault secrets (last 7 days)
az monitor activity-log list \
  --start-time "$(date -d '-7 days' +%Y-%m-%dT%H:%M:%SZ)" \
  --namespace Microsoft.KeyVault \
  --query "[?operationName.value=='Microsoft.KeyVault/vaults/secrets/read'].
    {time:eventTimestamp, caller:caller, secret:resourceId}" \
  --output table
```

---

## Examples

- "Rotate all database passwords that haven't been rotated in 90+ days"
- "Show me all TLS certificates expiring in the next 30 days"
- "Set up cert-manager for tenant-42's namespace with Let's Encrypt"
- "Audit who accessed production secrets in Key Vault last week"
- "Scan the platform codebase for any hardcoded credentials"
- "Migrate secrets from the old Key Vault to the new one after the subscription move"

---

## Output Format

```json
{
  "operation": "rotate|create|audit|scan|expiry_check",
  "secrets_affected": [],
  "certificates_expiring_soon": [],
  "hardcoded_secrets_found": 0,
  "rotation_status": "success|partial|failure",
  "audit_events": [],
  "next_rotation_due": "ISO8601"
}
```
