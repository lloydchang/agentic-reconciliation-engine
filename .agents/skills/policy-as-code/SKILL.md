---
name: policy-as-code
description: >
  Use this skill to define, enforce, and audit governance policies across
  cloud infrastructure and Kubernetes using Open Policy Agent (OPA), Azure
  Policy, AWS Service Control Policies, and Kubernetes Gatekeeper. Triggers:
  any request to create or update a governance policy, enforce tagging
  standards, restrict resource types or regions, audit policy compliance,
  generate a policy violation report, set up guardrails for developer
  self-service, or implement a platform governance framework.
tools:
  - bash
  - computer
---

# Policy-as-Code Governance Skill

Codify, deploy, and audit governance policies across the cloud stack.
Shift governance left — enforce standards at PR time, admission time, and
continuously in production — using OPA/Gatekeeper, Azure Policy, and SCPs.

## Enhanced Governance Enforcement

### Enforce Governance Policies Across Infrastructure Environments
Enforce governance policies across infrastructure environments with automated remediation.

**Policies Enforced:**
- Resource naming conventions
- Mandatory tagging standards
- Cost limits and budget controls
- Security baseline requirements
- Compliance framework adherence

**Workflow:**
1. Scan environment for policy violations
2. Detect non-compliant resources and configurations
3. Apply automated remediation where safe
4. Generate governance compliance report
5. Escalate critical violations for manual review

**Output:** Governance compliance report with violation details, remediation actions taken, and compliance score.

---

## Policy Layers

| Layer               | Tool                        | Enforcement point         |
|---------------------|-----------------------------|---------------------------|
| IaC (pre-plan)      | `conftest` + OPA Rego        | CI/CD pipeline gate       |
| K8s admission       | Gatekeeper (OPA)            | kubectl apply             |
| Azure platform      | Azure Policy + Initiatives  | ARM deployment            |
| AWS platform        | Service Control Policies    | IAM evaluation            |
| Runtime             | Falco                       | Continuous                |
| Git (pre-commit)    | Custom OPA + conftest       | Developer workstation     |

---

## Core Policy Set

### 1. Resource Tagging (IaC + Azure Policy)

**Required tags:** `tenant`, `env`, `owner`, `cost_center`, `managed_by`

```rego
# conftest/terraform/tagging.rego
package terraform.tagging

required_tags := {"tenant", "env", "owner", "cost_center", "managed_by"}

deny[msg] {
  resource := input.resource_changes[_]
  resource.change.actions[_] == "create"
  missing := required_tags - {tag | resource.change.after.tags[tag]}
  count(missing) > 0
  msg := sprintf(
    "Resource %v is missing required tags: %v",
    [resource.address, missing]
  )
}
```

```bash
# Run at PR time
conftest test terraform/plan.json -p conftest/terraform/
```

### 2. Approved Regions Only (Azure Policy)
```json
{
  "if": {
    "not": {
      "field": "location",
      "in": ["eastus", "westeurope", "southeastasia", "global"]
    }
  },
  "then": { "effect": "Deny" }
}
```

### 3. Approved VM SKUs
```json
{
  "if": {
    "allOf": [
      { "field": "type", "equals": "Microsoft.Compute/virtualMachines" },
      { "field": "Microsoft.Compute/virtualMachines/sku.name",
        "notIn": ["Standard_D2s_v3","Standard_D4s_v3","Standard_D8s_v3",
                  "Standard_E2s_v3","Standard_E4s_v3"] }
    ]
  },
  "then": { "effect": "Deny" }
}
```

### 4. No Public IPs on Production VMs
```rego
# conftest/terraform/network.rego
package terraform.network

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "azurerm_network_interface"
  resource.change.after.ip_configuration[_].public_ip_address_id != null
  contains(resource.change.after.tags.env, "prod")
  msg := sprintf(
    "Production NIC %v must not have a public IP",
    [resource.address]
  )
}
```

---

## Kubernetes Gatekeeper Policies

### Install Gatekeeper
```bash
helm upgrade --install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace \
  --set replicas=3
```

### Policy: Require Resource Limits
```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: requireresourcelimits
spec:
  crd:
    spec:
      names:
        kind: RequireResourceLimits
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package requireresourcelimits
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.cpu
          msg := sprintf(
            "Container %v must have CPU limits set",
            [container.name]
          )
        }
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.memory
          msg := sprintf(
            "Container %v must have memory limits set",
            [container.name]
          )
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: RequireResourceLimits
metadata:
  name: require-resource-limits
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces: ["kube-system", "monitoring"]
```

### Policy: No Root Containers
```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: noroot
spec:
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package noroot
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          container.securityContext.runAsUser == 0
          msg := sprintf("Container %v must not run as root (UID 0)", [container.name])
        }
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot
          msg := sprintf("Container %v must set runAsNonRoot: true", [container.name])
        }
```

### Policy: Approved Image Registries
```rego
package approvedregistries

approved := {"myregistry.azurecr.io", "mcr.microsoft.com"}

violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  registry := split(container.image, "/")[0]
  not approved[registry]
  msg := sprintf(
    "Container image %v must be from an approved registry. Approved: %v",
    [container.image, approved]
  )
}
```

---

## AWS Service Control Policies

### Restrict to Approved Regions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyOutsideApprovedRegions",
      "Effect": "Deny",
      "NotAction": [
        "iam:*", "sts:*", "cloudfront:*",
        "route53:*", "support:*", "budgets:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1", "eu-west-1", "ap-southeast-1"]
        }
      }
    }
  ]
}
```

### Prevent Disabling Security Services
```json
{
  "Sid": "ProtectSecurityServices",
  "Effect": "Deny",
  "Action": [
    "guardduty:DeleteDetector",
    "guardduty:DisassociateFromMasterAccount",
    "cloudtrail:DeleteTrail",
    "cloudtrail:StopLogging",
    "config:DeleteConfigRule",
    "config:DeleteConfigurationRecorder"
  ],
  "Resource": "*"
}
```

---

## Policy Audit & Compliance Reporting

```bash
# Audit all Gatekeeper constraint violations
kubectl get constraints -A -o json | \
  jq -r '.items[] | {
    constraint: .metadata.name,
    violations: .status.totalViolations,
    details: [.status.violations[]? | {resource: .resource, message: .message}]
  }'

# Azure Policy compliance state
az policy state summarize \
  --subscription "$SUBSCRIPTION_ID" \
  --query "{compliant: results.compliantResources,
            nonCompliant: results.nonCompliantResources}" \
  --output json

# Generate full violation report
kubectl get constraints -A -o json > policy-violations.json
python3 scripts/generate_policy_report.py \
  --input policy-violations.json \
  --output reports/policy-compliance.html
```

---

## Policy Governance Workflow

```
Developer writes IaC/manifests
         ↓
  Pre-commit: conftest (local)
         ↓
  PR created → CI runs conftest + tfsec
         ↓
  PR blocked if policies fail
         ↓
  Merge → Terraform plan + conftest in pipeline
         ↓
  Apply → Azure Policy / GK admission controller
         ↓
  Runtime → Falco + Gatekeeper audit mode
         ↓
  Weekly compliance report generated
```

---

## Examples

- "Add a policy that requires all new AKS workloads to have CPU and memory limits"
- "Deny deployment to any non-approved region across all subscriptions"
- "Run a compliance audit and show me all current policy violations"
- "Write an OPA policy that prevents images from Docker Hub in production"
- "Show me all Kubernetes pods currently violating our security policies"
- "Create a tagging policy that auto-remediates missing tags where possible"

---

## Output Format

```json
{
  "policy_name": "string",
  "layer": "iac|k8s|azure|aws|runtime",
  "action": "create|update|audit|enforce",
  "violations": [],
  "compliant_resources": 0,
  "non_compliant_resources": 0,
  "compliance_pct": 0.0,
  "auto_remediated": 0,
  "status": "success|failure"
}
```
