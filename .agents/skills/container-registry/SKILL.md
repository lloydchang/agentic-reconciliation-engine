---
name: container-registry
description: >
  Use this skill to manage container registries, image lifecycle, vulnerability
  scanning, and image promotion pipelines. Triggers: any request to set up or
  manage Azure Container Registry (ACR), push or pull images, scan for CVEs,
  promote images from dev to prod registries, enforce image signing, clean up
  old images, configure replication, manage access controls, or audit what
  images are running in production.
tools:
  - bash
  - computer
---

# Container Registry Skill

Manage the full container image lifecycle: build → scan → sign → promote →
run → retire. Enforce supply chain security across all environments.

---

## Registry Architecture

```
dev-registry.azurecr.io       (dev builds, unverified)
       ↓ scan + sign
staging-registry.azurecr.io   (verified, pre-prod)
       ↓ approved promotion only
prod-registry.azurecr.io      (signed, scanned, approved images only)
       ↑
  Geo-replicated to DR region
```

---

## ACR Provisioning

```bash
az acr create \
  --resource-group "$REGISTRY_RG" \
  --name "$REGISTRY_NAME" \
  --sku Premium \
  --location "$REGION" \
  --admin-enabled false \
  --public-network-enabled false \
  --tags "managed_by=container-registry" "env=$ENV"

# Private endpoint for registry
az network private-endpoint create \
  --resource-group "$REGISTRY_RG" \
  --name "pe-acr-${REGISTRY_NAME}" \
  --vnet-name "vnet-hub-${REGION}" \
  --subnet "snet-shared" \
  --private-connection-resource-id "${ACR_ID}" \
  --group-id registry

# Geo-replication (Premium tier)
az acr replication create \
  --registry "$REGISTRY_NAME" \
  --location "$DR_REGION"
```

---

## Image Scanning

### Pre-Push CVE Scan (CI gate)
```bash
scan_image() {
  local image=$1
  local fail_on=$2  # CRITICAL,HIGH

  trivy image \
    --format json \
    --severity "${fail_on}" \
    --exit-code 1 \
    --ignore-unfixed \
    "${image}" > "scan-${image//\//-}.json"

  CRIT=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' \
    "scan-${image//\//-}.json")
  HIGH=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity=="HIGH")] | length' \
    "scan-${image//\//-}.json")

  echo "Scan complete: CRITICAL=$CRIT HIGH=$HIGH"
  [[ "$fail_on" =~ "CRITICAL" && $CRIT -gt 0 ]] && return 1
  [[ "$fail_on" =~ "HIGH" && $HIGH -gt 0 ]] && return 1
  return 0
}
```

### Continuous Scan (ACR Tasks)
```bash
# Enable continuous vulnerability scanning in ACR
az acr task create \
  --registry "$REGISTRY_NAME" \
  --name continuous-scan \
  --image "registry.hub.docker.com/aquasec/trivy:latest" \
  --schedule "0 2 * * *" \
  --cmd "trivy image --exit-code 0 --format json \
    ${REGISTRY_NAME}.azurecr.io/\$IMAGE:\$TAG" \
  --timeout 3600
```

---

## Image Signing (Notation / Cosign)

```bash
# Sign image with Notation + Azure Key Vault key
notation sign "${REGISTRY_NAME}.azurecr.io/${IMAGE}:${TAG}" \
  --plugin azure-kv \
  --id "${KEY_VAULT_KEY_ID}" \
  --signature-format cose

# Verify signature
notation verify "${REGISTRY_NAME}.azurecr.io/${IMAGE}:${TAG}" \
  --policy policy.json

# Enforce signed images via OPA Gatekeeper
# (ImageSignatureRequired constraint — see policy-as-code skill)
```

---

## Image Promotion Pipeline

```bash
promote_image() {
  local image=$1
  local tag=$2
  local source_reg=$3  # staging
  local dest_reg=$4    # prod

  # Step 1: Verify scan is clean
  scan_image "${source_reg}.azurecr.io/${image}:${tag}" "CRITICAL" || {
    echo "BLOCKED: Critical CVEs found — cannot promote to ${dest_reg}"
    return 1
  }

  # Step 2: Verify signature
  notation verify "${source_reg}.azurecr.io/${image}:${tag}" || {
    echo "BLOCKED: Image not signed — cannot promote to ${dest_reg}"
    return 1
  }

  # Step 3: Copy to destination registry
  az acr import \
    --name "$dest_reg" \
    --source "${source_reg}.azurecr.io/${image}:${tag}" \
    --image "${image}:${tag}" \
    --force

  # Step 4: Re-sign in destination registry
  notation sign "${dest_reg}.azurecr.io/${image}:${tag}" \
    --plugin azure-kv --id "${PROD_KEY_ID}" \
    --signature-format cose

  # Step 5: Quarantine source tag (prevent re-use)
  az acr repository update \
    --name "$source_reg" \
    --image "${image}:${tag}" \
    --write-enabled false

  echo "Promoted: ${image}:${tag} → ${dest_reg}"
}
```

---

## Image Lifecycle Management

### Retention Policy (Auto-purge old images)
```bash
# Purge untagged manifests older than 7 days
az acr run \
  --registry "$REGISTRY_NAME" \
  --cmd "acr purge \
    --filter '${IMAGE_NAME}:.*' \
    --untagged \
    --ago 7d" \
  /dev/null

# Purge tagged images older than 90 days (non-prod only)
az acr run \
  --registry "$DEV_REGISTRY" \
  --cmd "acr purge \
    --filter '.*:.*' \
    --ago 90d \
    --keep 5" \
  /dev/null
```

### Registry Storage Report
```bash
az acr show-usage --name "$REGISTRY_NAME" \
  --query "[].{Name:name, Used:currentValue, Limit:limit, Unit:unit}" \
  --output table

# Top repositories by size
az acr repository list --name "$REGISTRY_NAME" --output tsv | \
  while read repo; do
    size=$(az acr repository show-manifests --name "$REGISTRY_NAME" \
      --repository "$repo" --query "[].imageSize" --output tsv | \
      awk '{sum += $1} END {print sum}')
    echo "${size} ${repo}"
  done | sort -rn | head -20
```

---

## Access Control

```bash
# Assign AcrPull to AKS cluster identity (per-cluster)
az role assignment create \
  --assignee "$AKS_IDENTITY_ID" \
  --role AcrPull \
  --scope "/subscriptions/${SUB}/resourceGroups/${REGISTRY_RG}/providers/Microsoft.ContainerRegistry/registries/${REGISTRY_NAME}"

# Grant CI pipeline push access
az role assignment create \
  --assignee "$CI_SP_ID" \
  --role AcrPush \
  --scope "${ACR_ID}"

# Audit all role assignments on registry
az role assignment list \
  --scope "${ACR_ID}" \
  --output json | \
  jq -r '.[] | "\(.principalName): \(.roleDefinitionName)"'
```

---

## Production Image Audit

```bash
# What images are running in production right now?
kubectl get pods -A -o json | \
  jq -r '.items[] | .spec.containers[].image' | \
  sort -u | \
  while read image; do
    # Check if it's from approved registry
    [[ "$image" =~ "prod-registry.azurecr.io" ]] || \
      echo "WARN: Non-prod image in cluster: $image"
    # Check if signed
    notation verify "$image" 2>/dev/null || \
      echo "WARN: Unsigned image: $image"
  done
```

---

## Examples

- "Scan the payments-api:v2.3.1 image and block promotion if there are critical CVEs"
- "Promote tenant-app:v1.5.0 from staging to prod registry after all gates pass"
- "Clean up all untagged images in the dev registry older than 7 days"
- "What images are currently running in production and are they all signed?"
- "Set up ACR with geo-replication to West Europe and private endpoint access"

---

## Output Format

```json
{
  "operation": "scan|sign|promote|purge|audit|provision",
  "image": "string",
  "tag": "string",
  "registry": "string",
  "scan_result": { "critical": 0, "high": 0, "medium": 0 },
  "signed": true,
  "promotion_status": "approved|blocked|pending",
  "block_reason": null,
  "status": "success|failure"
}
```
