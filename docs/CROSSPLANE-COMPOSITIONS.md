# Crossplane Compositions

Platform team guide for authoring, testing, and maintaining Crossplane Compositions and XRDs.

Spoke teams do not write Crossplane Compositions. They write cloud-agnostic XRD claims. The
Composition is the platform team's responsibility — it defines how a claim is translated to
provider-specific managed resources.

---

## Concepts

### XRD (CompositeResourceDefinition)

An XRD defines a new resource type — a cloud-agnostic API surface that spoke teams use. It has
no cloud-specific fields. It describes what the developer needs (a database, a network, a queue),
not how it is implemented.

### Composition

A Composition defines how an XRD is fulfilled. It maps fields from the claim to one or more
Crossplane managed resources (provider-aws, provider-azure, or provider-gcp). A single XRD can
have multiple Compositions — one per cloud provider — selected by a label on the claim.

### Managed Resource

A provider-specific resource (e.g. `rds.aws.crossplane.io/DBInstance`, `dbformysql.azure.jet.crossplane.io/FlexibleServer`). Spoke teams never write these directly. Compositions write them.

### Claim

What the spoke team writes: a reference to an XRD with their requirements. Small, cloud-agnostic,
readable by a developer without cloud expertise.

---

## File Layout

```
control-plane/crossplane/
  xrds/
    xdatabase.yaml             # XRD for databases
    xnetwork.yaml              # XRD for VPCs/VNets
    xqueue.yaml                # XRD for message queues
    xcluster.yaml              # XRD for Kubernetes clusters
  compositions/
    database-aws.yaml          # Composition: XDatabase → RDS
    database-azure.yaml        # Composition: XDatabase → Azure Database
    database-gcp.yaml          # Composition: XDatabase → Cloud SQL
    network-aws.yaml
    network-azure.yaml
    network-gcp.yaml
    cluster-eks.yaml
    cluster-aks.yaml
    cluster-gke.yaml
  providers/
    provider-aws.yaml
    provider-azure.yaml
    provider-gcp.yaml
    providerconfig-aws.yaml
    providerconfig-azure.yaml
    providerconfig-gcp.yaml

infrastructure/tenants/
  1-network/
    network-prod-aws.yaml      # XNetwork claim — developer-facing
  2-clusters/
    cluster-eks-prod.yaml      # XCluster claim
  3-workloads/
    database-orders.yaml       # XDatabase claim
```

---

## Authoring a Composition

### Step 1: Define the XRD

The XRD defines the schema for the claim. Keep it minimal. Do not expose cloud-specific fields.
The developer writing a claim should not need to know which cloud they are on.

```yaml
# control-plane/crossplane/xrds/xdatabase.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xdatabases.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XDatabase
    plural: xdatabases
  claimNames:
    kind: Database
    plural: databases
  versions:
    - name: v1alpha1
      served: true
      referenceable: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [engine, version, size]
              properties:
                engine:
                  type: string
                  enum: [postgres, mysql, redis]
                version:
                  type: string
                  description: "Engine version (e.g. '15', '8.0')"
                size:
                  type: string
                  enum: [small, medium, large]
                  description: "small=2vCPU/4GB, medium=4vCPU/16GB, large=8vCPU/32GB"
                region:
                  type: string
                  description: "Cloud region; provider-specific string"
                deletionPolicy:
                  type: string
                  enum: [Delete, Orphan]
                  default: Orphan
                  description: "Orphan retains cloud resource if claim is deleted"
            status:
              type: object
              properties:
                endpoint:
                  type: string
                port:
                  type: integer
                  format: int32
```

### Step 2: Write the Composition

One Composition per cloud provider per XRD. Use labels to select which Composition fulfills
a given claim.

```yaml
# control-plane/crossplane/compositions/database-aws.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xdatabase-aws
  labels:
    provider: aws
    platform.example.com/xrd: xdatabase
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: XDatabase
  resources:
    - name: rds-subnet-group
      base:
        apiVersion: rds.aws.crossplane.io/v1alpha1
        kind: DBSubnetGroup
        spec:
          forProvider:
            region: us-east-1         # patched below
            subnetIds:
              - subnet-placeholder    # patched from environment config
          providerConfigRef:
            name: aws-provider
      patches:
        - type: FromCompositeFieldPath
          fromFieldPath: spec.region
          toFieldPath: spec.forProvider.region

    - name: rds-instance
      base:
        apiVersion: rds.aws.crossplane.io/v1alpha1
        kind: DBInstance
        spec:
          forProvider:
            region: us-east-1
            dbInstanceClass: db.t3.medium    # patched by size
            engine: postgres
            engineVersion: "15"
            allocatedStorage: 20
            masterUsername: admin
            masterUserPasswordSecretRef:
              namespace: crossplane-system
              name: db-master-password
              key: password
            dbSubnetGroupNameRef:
              name: ""                       # patched to rds-subnet-group
            deletionPolicy: Orphan
          providerConfigRef:
            name: aws-provider
      patches:
        - type: FromCompositeFieldPath
          fromFieldPath: spec.region
          toFieldPath: spec.forProvider.region
        - type: FromCompositeFieldPath
          fromFieldPath: spec.engine
          toFieldPath: spec.forProvider.engine
        - type: FromCompositeFieldPath
          fromFieldPath: spec.version
          toFieldPath: spec.forProvider.engineVersion
        - type: FromCompositeFieldPath
          fromFieldPath: spec.deletionPolicy
          toFieldPath: spec.forProvider.deletionPolicy
        - type: FromCompositeFieldPath
          fromFieldPath: spec.size
          toFieldPath: spec.forProvider.dbInstanceClass
          transforms:
            - type: map
              map:
                small: db.t3.small
                medium: db.t3.medium
                large: db.r6g.large
        - type: ToCompositeFieldPath
          fromFieldPath: status.atProvider.endpoint.address
          toFieldPath: status.endpoint
        - type: ToCompositeFieldPath
          fromFieldPath: status.atProvider.endpoint.port
          toFieldPath: status.port
```

### Step 3: Write a claim (spoke team)

```yaml
# infrastructure/tenants/3-workloads/database-orders.yaml
apiVersion: platform.example.com/v1alpha1
kind: Database
metadata:
  name: orders-db
  namespace: orders-team
  annotations:
    # Required on all stateful resources — prevents accidental deletion
    platform.example.com/allow-deletion: "false"
spec:
  compositionSelector:
    matchLabels:
      provider: aws
  engine: postgres
  version: "15"
  size: medium
  region: us-east-1
  deletionPolicy: Orphan
  writeConnectionSecretToRef:
    name: orders-db-connection
    namespace: orders-team
```

---

## Deletion Guard Convention

All stateful XRDs (XDatabase, XVolume, XQueue, anything with persistent data) must have
`deletionPolicy: Orphan` in the Composition base and default to `Orphan` in the XRD schema.

If a claim is deleted without an explicit `deletionPolicy: Delete` override, the cloud resource
survives. The CI gate additionally blocks PRs that remove stateful claims without the
`platform.example.com/allow-deletion: "true"` annotation.

See [CI-POLICY-GATE.md](./CI-POLICY-GATE.md#deletion-guard) for the CI policy.

---

## Composition Selection

Compositions are selected by labels on the claim's `compositionSelector`. Convention:

| Label key | Values | Purpose |
|---|---|---|
| `provider` | `aws`, `azure`, `gcp` | Cloud provider |
| `tier` | `production`, `staging`, `dev` | Environment tier (size, backup config) |
| `region-group` | `us`, `eu`, `apac` | Regional variant |

Example: a staging database on Azure uses `provider: azure, tier: staging`.

```yaml
spec:
  compositionSelector:
    matchLabels:
      provider: azure
      tier: staging
```

---

## Testing a New Composition

Before merging a new Composition, validate it against a non-production environment:

```bash
# 1. Validate XRD schema
kubeconform -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  control-plane/crossplane/xrds/xdatabase.yaml

# 2. Apply XRD and Composition to a dev hub
kubectl apply -f control-plane/crossplane/xrds/xdatabase.yaml
kubectl apply -f control-plane/crossplane/compositions/database-aws.yaml

# 3. Apply a test claim
kubectl apply -f examples/crossplane-compositions/xdatabase-claim-dev.yaml

# 4. Monitor claim reconciliation
kubectl describe database test-db -n dev-team
# Look for: Synced=True, Ready=True in status conditions

# 5. Verify cloud resource was created
aws rds describe-db-instances --db-instance-identifier test-db

# 6. Test drift correction: modify the resource in the console, observe Crossplane revert it

# 7. Delete the test claim; verify Orphan policy retains the cloud resource
kubectl delete database test-db -n dev-team
aws rds describe-db-instances --db-instance-identifier test-db
# Cloud resource should still exist

# 8. Clean up manually
aws rds delete-db-instance --db-instance-identifier test-db --skip-final-snapshot
```

---

## Composition Authoring Checklist

Before submitting a new Composition PR:

- [ ] XRD has no cloud-specific fields in the claim schema
- [ ] `deletionPolicy` defaults to `Orphan` in the XRD schema for stateful resources
- [ ] Composition base resources use `providerConfigRef` by name, not inline credentials
- [ ] All required claim fields are patched to the correct managed resource fields
- [ ] Status fields (`endpoint`, `port`, etc.) are patched back to the composite status
- [ ] `writeConnectionSecretToRef` is documented in the XRD schema if connection details are needed
- [ ] Composition is labeled with `provider` and any applicable selectors
- [ ] Tested against a dev hub with a real claim — not just schema-validated
- [ ] Drift correction validated: manual console change was reverted by Crossplane

---

## Example Compositions

See `examples/crossplane-compositions/` for complete working examples:

- `xdatabase/` — XDatabase XRD + Compositions for AWS RDS, Azure Database, Cloud SQL
- `xnetwork/` — XNetwork XRD + Compositions for VPC (AWS), VNet (Azure), VPC (GCP)
- `xcluster/` — XCluster XRD + Compositions for EKS, AKS, GKE
