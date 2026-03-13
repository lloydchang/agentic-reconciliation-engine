# ESO Workload Identity

Per-spoke secret delivery using External Secrets Operator and native cloud workload identity.
The hub is not in the secrets path. Each spoke authenticates directly to its cloud vault.

---

## Architecture

```
Spoke ESO agent
  -> cloud workload identity (IRSA / Managed Identity / Workload Identity Federation)
  -> cloud vault (AWS SM / AKV / GCP SM)
  -> Kubernetes Secret in spoke namespace
```

The hub does not hold vault credentials. Hub outage does not affect secret delivery. Secret
access is scoped by cloud IAM per spoke — a compromise of one spoke's identity does not expose
other spokes' secrets.

---

## Installing ESO on a Spoke

ESO is bootstrapped onto each spoke by Flux after CAPI provisions the cluster.

```yaml
# control-plane/flux/spoke-bootstrap/eso-helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: external-secrets
  namespace: external-secrets
spec:
  interval: 1h
  chart:
    spec:
      chart: external-secrets
      version: ">=0.9.0 <1.0.0"
      sourceRef:
        kind: HelmRepository
        name: external-secrets
        namespace: flux-system
  values:
    serviceAccount:
      annotations: {}   # patched per spoke with workload identity annotation
    webhook:
      create: true
    certController:
      create: true
```

---

## EKS -- IRSA (IAM Roles for Service Accounts)

### 1. Create the IAM role

```bash
CLUSTER_NAME=spoke-eks-prod
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_PROVIDER=$(aws eks describe-cluster --name $CLUSTER_NAME \
  --query "cluster.identity.oidc.issuer" --output text | sed 's|https://||')

cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_PROVIDER}"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "${OIDC_PROVIDER}:sub": "system:serviceaccount:external-secrets:external-secrets"
      }
    }
  }]
}
EOF

aws iam create-role \
  --role-name spoke-eks-prod-eso-role \
  --assume-role-policy-document file:///tmp/trust-policy.json

aws iam attach-role-policy \
  --role-name spoke-eks-prod-eso-role \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

### 2. Annotate the ESO service account

```yaml
# Patch in the spoke's ESO HelmRelease
values:
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/spoke-eks-prod-eso-role
```

### 3. ClusterSecretStore

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
```

### 4. ExternalSecret (spoke team)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: orders-db-credentials
  namespace: orders-team
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: orders-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: prod/orders-db
        property: username
    - secretKey: password
      remoteRef:
        key: prod/orders-db
        property: password
```

---

## AKS -- Azure Managed Identity

### 1. Create the managed identity and Key Vault role assignment

```bash
SPOKE_RG=spoke-aks-prod-rg
KEYVAULT_NAME=spoke-prod-kv

az identity create \
  --name spoke-aks-prod-eso-identity \
  --resource-group $SPOKE_RG

IDENTITY_CLIENT_ID=$(az identity show \
  --name spoke-aks-prod-eso-identity \
  --resource-group $SPOKE_RG \
  --query clientId -o tsv)

KEYVAULT_ID=$(az keyvault show --name $KEYVAULT_NAME --query id -o tsv)

az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee $IDENTITY_CLIENT_ID \
  --scope $KEYVAULT_ID

# Federate the identity to the AKS service account
AKS_OIDC_ISSUER=$(az aks show --resource-group $SPOKE_RG \
  --name spoke-aks-prod --query oidcIssuerProfile.issuerUrl -o tsv)

az identity federated-credential create \
  --name eso-federated-credential \
  --identity-name spoke-aks-prod-eso-identity \
  --resource-group $SPOKE_RG \
  --issuer $AKS_OIDC_ISSUER \
  --subject "system:serviceaccount:external-secrets:external-secrets" \
  --audience api://AzureADTokenExchange
```

### 2. Annotate the ESO service account

```yaml
values:
  serviceAccount:
    annotations:
      azure.workload.identity/client-id: "<IDENTITY_CLIENT_ID>"
  podLabels:
    azure.workload.identity/use: "true"
```

### 3. ClusterSecretStore

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: azure-key-vault
spec:
  provider:
    azurekv:
      vaultUrl: "https://spoke-prod-kv.vault.azure.net"
      authType: WorkloadIdentity
```

### 4. ExternalSecret (spoke team)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: orders-db-credentials
  namespace: orders-team
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: azure-key-vault
    kind: ClusterSecretStore
  target:
    name: orders-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: prod-orders-db-username
    - secretKey: password
      remoteRef:
        key: prod-orders-db-password
```

---

## GKE -- Workload Identity Federation

### 1. Create the Google Service Account and IAM binding

```bash
PROJECT_ID=my-gcp-project
SPOKE_NAME=spoke-gke-prod

gcloud iam service-accounts create spoke-gke-prod-eso \
  --project=$PROJECT_ID

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:spoke-gke-prod-eso@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Bind the GSA to the Kubernetes service account
gcloud iam service-accounts add-iam-policy-binding \
  spoke-gke-prod-eso@${PROJECT_ID}.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${PROJECT_ID}.svc.id.goog[external-secrets/external-secrets]"
```

### 2. Annotate the ESO service account

```yaml
values:
  serviceAccount:
    annotations:
      iam.gke.io/gcp-service-account: spoke-gke-prod-eso@PROJECT_ID.iam.gserviceaccount.com
```

### 3. ClusterSecretStore

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: gcp-secret-manager
spec:
  provider:
    gcpsm:
      projectID: my-gcp-project
      auth:
        workloadIdentity:
          clusterLocation: us-central1
          clusterName: spoke-gke-prod
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
```

### 4. ExternalSecret (spoke team)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: orders-db-credentials
  namespace: orders-team
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcp-secret-manager
    kind: ClusterSecretStore
  target:
    name: orders-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: prod-orders-db-username
        version: latest
    - secretKey: password
      remoteRef:
        key: prod-orders-db-password
        version: latest
```

---

## Kubeadm / On-Prem -- HashiCorp Vault

### 1. Configure Vault Kubernetes auth

```bash
# On the Vault server
vault auth enable -path=spoke-onprem kubernetes

# Get the spoke service account JWT and CA
kubectl get secret -n external-secrets \
  $(kubectl get sa external-secrets -n external-secrets \
    -o jsonpath='{.secrets[0].name}') \
  -o jsonpath='{.data.token}' | base64 -d > /tmp/sa-token

kubectl get cm -n kube-system kube-root-ca.crt \
  -o jsonpath='{.data.ca\.crt}' > /tmp/k8s-ca.crt

KUBE_HOST=$(kubectl config view --raw --minify \
  -o jsonpath='{.clusters[0].cluster.server}')

vault write auth/spoke-onprem/config \
  kubernetes_host=$KUBE_HOST \
  kubernetes_ca_cert=@/tmp/k8s-ca.crt

# Create Vault policy
vault policy write spoke-onprem-eso - << EOF
path "secret/data/spoke-onprem/*" {
  capabilities = ["read"]
}
EOF

# Create role binding the ESO service account to the policy
vault write auth/spoke-onprem/role/eso \
  bound_service_account_names=external-secrets \
  bound_service_account_namespaces=external-secrets \
  policies=spoke-onprem-eso \
  ttl=1h
```

### 2. ClusterSecretStore

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "spoke-onprem"
          role: "eso"
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
```

### 3. ExternalSecret (spoke team)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: orders-db-credentials
  namespace: orders-team
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault
    kind: ClusterSecretStore
  target:
    name: orders-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: secret/data/spoke-onprem/orders-db
        property: username
    - secretKey: password
      remoteRef:
        key: secret/data/spoke-onprem/orders-db
        property: password
```

---

## SOPS / age Fallback

Retained for on-prem spokes where HashiCorp Vault is not available and for cross-cloud secrets
with no natural cloud vault home. Not the primary path.

```bash
# Generate an age key pair
age-keygen -o age-key.txt

# Back up the private key to a cloud key vault before committing anything encrypted with it
aws secretsmanager create-secret \
  --name gitops/sops-age-private-key \
  --secret-string "$(cat age-key.txt)"

# Export for Flux SOPS decryption
kubectl create secret generic sops-age \
  --from-file=age.agekey=age-key.txt \
  -n flux-system

# .sops.yaml in repository root
creation_rules:
  - path_regex: infrastructure/tenants/.*\.yaml
    age: age1xxxx...  # public key only in repo
```

Flux decrypts at apply time on the hub. Spokes receive plain Kubernetes Secret objects. Only the
hub needs access to the age private key.

---

## Validation

After configuring ESO on a spoke, verify end-to-end secret delivery:

```bash
# Check ESO controller is running
kubectl get pods -n external-secrets

# Check ClusterSecretStore status
kubectl get clustersecretstore
# Expected: Ready=True

# Check ExternalSecret sync status
kubectl get externalsecrets -A
# Expected: SecretSynced, Ready=True

# Verify the Secret was created
kubectl get secret orders-db-credentials -n orders-team

# Simulate hub outage: scale hub API server unreachable, verify ESO still syncs
# (ESO uses cloud vault credentials, not hub credentials)
```

---

## Troubleshooting

**ExternalSecret status: SecretSyncedError**

```bash
kubectl describe externalsecret orders-db-credentials -n orders-team
# Check Events section for vault access errors
```

Common causes: workload identity annotation missing from service account; IAM role trust policy
incorrect OIDC issuer; secret path does not exist in vault; secret version is not "latest".

**ClusterSecretStore status: not Ready**

```bash
kubectl describe clustersecretstore aws-secrets-manager
# Check status.conditions for the error
```

Common causes: ESO service account lacks the workload identity annotation; provider config
references incorrect region or vault URL.

See [CONTROLLER-RUNBOOKS.md](./CONTROLLER-RUNBOOKS.md#eso) for full ESO failure playbook.

