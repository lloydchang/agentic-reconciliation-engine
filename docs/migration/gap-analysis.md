# Crossplane Migration Gap Analysis

**Assessment: Missing XRDs and Custom Compositions Needed**

---

## Missing CompositeResourceDefinitions (XRDs)

Based on the Terraform inventory, the following cloud-agnostic resource types are **not yet defined** in `core/operators/control-plane/crossplane/xrds/`:

### 1. XSecurityGroup

**Purpose**: Unified security group / firewall rule abstraction across AWS (Security Groups), Azure (NSG), GCP (Firewall Rules).

**Why needed**: Terraform defines numerous `aws_security_group`, `azurerm_network_security_group`, `google_compute_firewall`.

**Proposed XRD**:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xsecuritygroups.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XSecurityGroup
    plural: xsecuritygroups
  claimNames:
    kind: SecurityGroup
    plural: securitygroups
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
            required: [name, rules]
            properties:
              name:
                type: string
              description:
                type: string
              rules:
                type: array
                items:
                  type: object
                  required: [port, protocol, direction]
                  properties:
                    port:
                      type: integer
                    protocol:
                      type: string
                      enum: [tcp, udp, icmp, all]
                    direction:
                      type: string
                      enum: [ingress, egress]
                    cidrBlocks:
                      type: array
                      items:
                        type: string
                    sourceSecurityGroupIds:
                      type: array
                      items:
                        type: string
              networkRef:
                type: object
                properties:
                  name:
                    type: string
                  namespace:
                    type: string
          status:
            type: object
            properties:
              securityGroupId:
                type: string
              provider:
                type: string
```

**Compositions needed**:
- `securitygroup-aws.yaml` → `securitygroups.ec2.aws.crossplane.io/v1beta1`
- `securitygroup-azure.yaml` → `securityrules.network.azure.crossplane.io/v1beta1` + `securitygroups`
- `securitygroup-gcp.yaml` → `firewalls.compute.gcp.crossplane.io/v1beta1`

---

### 2. XRedis

**Purpose**: Unified Redis instance abstraction across AWS ElastiCache, GCP Memorystore, Azure Cache for Redis.

**Why needed**: Terraform has `aws_elasticache_cluster`, `google_redis_instance`, `azurerm_redis_cache`.

**Proposed XRD**:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xredises.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XRedis
    plural: xredises
  claimNames:
    kind: Redis
    plural: redises
  connectionSecretKeys:
    - endpoint
    - port
    - password
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
            required: [size, engineVersion]
            properties:
              engine:
                type: string
                enum: [redis]
                default: redis
              size:
                type: string
                enum: [small, medium, large]
                description: "small=1 node, medium=2 nodes, large=3+ nodes"
              engineVersion:
                type: string
                default: "7.0"
              region:
                type: string
                default: us-east-1
              deletionPolicy:
                type: string
                enum: [Delete, Orphan]
                default: Orphan
          status:
            type: object
            properties:
              endpoint:
                type: string
              port:
                type: integer
```

**Compositions needed**:
- `redis-aws.yaml` → `replicationgroups.elasticache.aws.crossplane.io/v1beta1`
- `redis-gcp.yaml` → `instances.redis.googleapis.com/v1beta1` (GCP native, need Crossplane wrapper)
- `redis-azure.yaml` → `redis.azure.crossplane.io/v1beta1`

**Complexity**: High - Redis providers vary significantly.

---

### 3. XCertificate

**Purpose**: Unified SSL/TLS certificate management across AWS ACM, Azure Key Vault, GCP Certificate Manager.

**Why needed**: Terraform manages `aws_acm_certificate`, `azurerm_key_vault_certificate`, potentially GCP managed certs.

**Proposed XRD**:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xcertificates.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XCertificate
    plural: xcertificates
  claimNames:
    kind: Certificate
    plural: certificates
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
            required: [domains, validationMethod]
            properties:
              domains:
                type: array
                items:
                  type: string
              validationMethod:
                type: string
                enum: [DNS, EMAIL]
                default: DNS
              certificateAuthority:
                type: string
                enum: [amazon, azure, google, self-signed]
              region:
                type: string
                default: us-east-1
          status:
            type: object
            properties:
              arn:
                type: string
              provider:
                type: string
```

**Compositions needed**:
- `certificate-aws.yaml` → `certificates.acm.aws.crossplane.io/v1beta1`
- `certificate-azure.yaml` → `vaultcertificates.vault.azure.crossplane.io/v1beta1`
- `certificate-gcp.yaml` → `managedsslcertificates.compute.gcp.crossplane.io/v1beta1`

**Note**: For now, may keep ACM certs in Terraform (used by CloudFront/ALB) and manage separately.

---

### 4. XWAF (Web Application Firewall)

**Purpose**: Unified WAF across AWS WAF, GCP Cloud Armor, Azure WAF.

**Why needed**: Terraform defines `aws_wafv2_web_acl`, `google_compute_security_policy`, `azurerm_web_application_firewall_policy`.

**Proposed XRD**:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xwafs.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XWAF
    plural: xwafs
  claimNames:
    kind: WAF
    plural: wafs
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
            required: [name, rules]
            properties:
              name:
                type: string
              description:
                type: string
              mode:
                type: string
                enum: [DETECTION, PREVENTION]
                default: DETECTION
              rules:
                type: array
                items:
                  type: object
                  required: [priority, action]
                  properties:
                    priority:
                      type: integer
                    action:
                      type: string
                      enum: [allow, block, count]
                    condition:
                      type: object
              lbRef:
                type: object
                properties:
                  name:
                    type: string
                  namespace:
                    type: string
          status:
            type: object
            properties:
              wafId:
                type: string
              provider:
                type: string
```

**Compositions needed**:
- `waf-aws.yaml` → `webacls.wafv2.aws.crossplane.io/v1beta1` + `rules`
- `waf-gcp.yaml` → `securitypolicies.compute.gcp.crossplane.io/v1beta1`
- `waf-azure.yaml` → `applicationgatewaywafpolicies.network.azure.crossplane.io/v1beta1`

---

### 5. XIAMRole / XIAMPolicy

**Purpose**: Unified IAM roles and policies across AWS IAM, Azure RBAC, GCP IAM.

**Why needed**: Terraform has extensive IAM resources: `aws_iam_role`, `aws_iam_policy`, `aws_iam_role_policy_attachment`, etc.

**Complexity**: Very high. IAM is provider-specific and complex. Crossplane has IAM providers but integration depth varies.

**Recommendation**: **Keep IAM in Terraform** for Phase 1 migration. Evaluate Crossplane IAM maturity later. Document as "Out of Scope for Initial Migration".

---

### 6. XDNS (Maybe Already Covered?)

The current repo **already has** separate provider-specific DNS resources:

- AWS: `recordsets.route53.aws.crossplane.io/v1beta1` (via provider-aws)
- GCP: `recordsets.dns.gcp.crossplane.io/v1beta1`
- Azure: `arecords.dns.azure.crossplane.io/v1beta1` + others

But the XRD list (xrds/) shows:
- `xqueue.yaml`
- `xdatabase.yaml`
- `xnetwork.yaml`

**No `xcluster.yaml`?** Wait, we saw `cluster-eks.yaml` Composition. Check if XRD exists.

**Action**: Verify if `xcluster.yaml` exists in `xrds/`. If not, that's a gap. If it exists but not listed in README, update docs.

---

## Custom Composition Updates Needed

Even when MRs exist, Compositions might need updates to match Terraform configurations.

### AWS Compositions

| Composition | Terraform Feature | Update Needed? |
|---|---|---|
| `network-aws.yaml` | NAT Gateway, multiple subnets, route tables | ✅ Verify all SG rules, NAT, IGW included |
| `cluster-eks.yaml` | Fargate profiles, managed node groups, addons | ⚠️ Check if Fargate profiles, managed node groups covered |
| `database-aws.yaml` | Parameter groups, option groups, subnet groups, multi-AZ | ✅ Mostly covered; verify parameter groups |
| (No LB yet) | ALB with HTTPS, WAF integration, CloudFront | 🔧 Create `lb-aws.yaml` Composition |

### GCP Compositions

| Composition | Terraform Feature | Update Needed? |
|---|---|---|
| `network-gcp.yaml` | Cloud Router, NAT, secondary IP ranges for pods/services | ✅ Verify Cloud Router NAT configured |
| `cluster-gke.yaml` | Autopilot vs Standard, network policy, binary auth, shielded nodes | ✅ Check if Autopilot supported (via node pools = 0) |
| `database-gcp.yaml` | Private IP, maintenance window, backup config, insights | ✅ Verify private network configuration |
| `queue-gcp.yaml` | Cloud Pub/Sub topics + subscriptions | ✅ Check if both topics and subscriptions covered |
| (No LB yet) | GCP Cloud Load Balancer with HTTPS, Cloud Armor | 🔧 Create `lb-gcp.yaml` |

### Azure Compositions

| Composition | Terraform Feature | Update Needed? |
|---|---|---|
| `network-azure.yaml` | VNet, subnets, NSG, possibly VPN gateway/private endpoints | ✅ Check NSG rules, private DNS zones |
| `cluster-aks.yaml` | AKS with Azure AD integration, network policy, monitoring | ⚠️ Verify Azure AD integration (kubelet identity, etc.) |
| `database-azure.yaml` | PostgreSQL Flexible Server, private DNS zone, high availability | ✅ Verify private DNS zone linking, HA config |
| `queue-azure.yaml` | Service Bus queues/topics, Event Hubs | ✅ Check both Service Bus and Event Hubs if used |
| (No LB yet) | Application Gateway with WAF, SSL certs | 🔧 Create `lb-azure.yaml` |

---

## Missing Compositions

From Terraform resources, need new Composition files:

1. **Load Balancers**
   - `lb-aws.yaml` (ALB + CloudFront integration)
   - `lb-gcp.yaml` (Global HTTP(S) LB)
   - `lb-azure.yaml` (Application Gateway)

2. **Redis**
   - `redis-aws.yaml`
   - `redis-gcp.yaml`
   - `redis-azure.yaml`

3. **SecurityGroups** (if separate XRD)
   - `securitygroup-aws.yaml`
   - `securitygroup-azure.yaml`
   - `securitygroup-gcp.yaml`

4. **Certificates**
   - `certificate-aws.yaml` (ACM)
   - `certificate-azure.yaml` (Key Vault)
   - `certificate-gcp.yaml` (Certificate Manager)

5. **WAF**
   - `waf-aws.yaml`
   - `waf-gcp.yaml`
   - `waf-azure.yaml`

6. **DNS** (if using XRD)
   - `dns-aws.yaml` (Route53)
   - `dns-gcp.yaml` (Cloud DNS)
   - `dns-azure.yaml` (Azure DNS)

---

## Resources to Keep in Terraform

Based on complexity and low strategic value:

- **IAM**: `aws_iam_*`, Azure role assignments, GCP IAM bindings
- **Service Account Keys**: `google_service_account_key`, etc.
- **Provider-specific monitoring alerts** (CloudWatch alarms, etc. — could migrate later)
- **BigQuery datasets** (analytics, not core infra)
- **KMS key rings** (complex secret management; keep Terraform separate or use external secrets operator)

---

## Implementation Plan

1. **Create Missing XRDs** (Week 2)
   - XSecurityGroup
   - XRedis
   - XCertificate
   - XWAF
   - XLB (if not covered by existing XCluster/XDatabase)
   - Review XDNS need

2. **Update Existing Compositions** (Week 2-3)
   - Verify network, cluster, database Compositions match Terraform configs
   - Add missing fields (security groups, IAM roles, logs, monitoring)
   - Add patches for status fields (endpoint, connection secrets)

3. **Create New Compositions** (Week 3)
   - LB Compositions (ALB, GLB, AppGateway)
   - Redis Compositions
   - SecurityGroup Compositions
   - Certificate Compositions
   - WAF Compositions
   - DNS Compositions (if XRD created)

4. **Validate Provider CRDs** (Week 1)
   - `kubectl get crd | grep crossplane` on hub cluster
   - Verify all required managed resource types exist
   - If missing, file issue with provider or implement custom compositions using provider-specific resources

---

## Provider Capability Assessment

Need to check installed providers for CRD coverage:

```bash
# Get list of provider CRDs
kubectl get crd -l 'api.crossplane.io/provider=provider-aws' -o name
kubectl get crd -l 'api.crossplane.io/provider=provider-azure' -o name
kubectl get crd -l 'api.crossplane.io/provider=provider-gcp' -o name
```

Cross-reference with [Crossplane Provider Catalog](https://marketplace.upbound.io/providers).

---

## Risk Assessment

| Gap | Risk | Mitigation |
|-----|------|------------|
| Missing XRedis XRD | Can't migrate ElastiCache/Memorystore | Create XRD, or keep Redis in Terraform |
| Missing XSecurityGroup XRD | SGs remain in Terraform | Moderate risk; embed in XNetwork Composition instead |
| IAM complexity | IAM stays in Terraform (acceptable) | Document as separate domain; keep IAM in Terraform |
| LB Compositions missing | Load balancers stay in Terraform initially | Higher priority: LBs are critical production infra |
| Provider MR gaps | Some Terraform resources have no Crossplane equivalent | File provider issue, or keep those specific resources in Terraform |

---

## Acceptance Criteria

✅ All XRDs created for resource types in inventory (except IAM)
✅ All Compositions updated/created to cover Terraform configs
✅ Provider CRDs confirmed available in hub cluster
✅ Test claims for each XRD successfully provision resources in dev cloud
✅ Crossplane resources match Terraform configurations 1:1

---

**Status**: Draft
**Last Updated**: 2026-03-20
**Owner**: Platform Engineering
