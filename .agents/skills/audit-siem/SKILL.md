---
name: audit-siem
description: >
  Use this skill to collect, forward, and query audit logs and security events
  from cloud infrastructure, Kubernetes, and application layers into a SIEM.
  Triggers: any request to set up audit logging, query who accessed secrets, vault access, audit who accessed, accessed secrets, configure log forwarding to
  Sentinel or Splunk, investigate a security event, search audit logs for
  suspicious activity, generate a SOC compliance evidence package, configure
  detection rules, or produce an audit trail for a specific user/resource/time.
tools:
  - bash
  - computer
---

# Audit & SIEM Skill

Centralise, search, and alert on audit logs from every platform layer:
Azure Activity Log, Kubernetes Audit, application events, and security
scanner findings — feeding into Microsoft Sentinel (or Splunk / Elastic).

---

## Log Sources & Collection

| Layer                    | Source                         | Forwarding method          |
|--------------------------|--------------------------------|----------------------------|
| Azure control plane      | Azure Activity Log             | Diagnostic settings → LAW  |
| Azure Resource changes   | Azure Resource Graph           | Policy + Event Hub         |
| Kubernetes API audit     | K8s audit log → OMS Agent      | Azure Monitor AKS add-on   |
| Container stdout/stderr  | Promtail / Fluent Bit          | Loki / Log Analytics       |
| OS / VM                  | Azure Monitor Agent (AMA)      | Log Analytics Workspace     |
| Network                  | NSG Flow Logs + Azure Firewall | Storage → Sentinel         |
| Identity                 | Azure AD Sign-in + Audit       | Entra diagnostic settings  |
| Application              | App Insights / OpenTelemetry   | Log Analytics              |
| Security scanner results | Defender for Cloud             | Sentinel connector         |

---

## Setup: Log Analytics Workspace + Diagnostic Settings

```bash
# Create Log Analytics Workspace (hub-level, shared)
az monitor log-analytics workspace create \
  --resource-group "$HUB_RG" \
  --workspace-name "law-platform-${REGION}" \
  --location "$REGION" \
  --retention-time 90 \
  --sku PerGB2018

# Enable AKS audit logging → LAW
az aks enable-addons \
  --resource-group "rg-${TENANT_ID}" \
  --name "aks-${CLUSTER_NAME}" \
  --addons monitoring \
  --workspace-resource-id "${LAW_ID}"

# Diagnostic settings for Azure SQL → LAW
az monitor diagnostic-settings create \
  --name "diag-sql-${TENANT_ID}" \
  --resource "${SQL_SERVER_ID}" \
  --workspace "${LAW_ID}" \
  --logs '[{"category":"SQLSecurityAuditEvents","enabled":true},
           {"category":"SQLInsights","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'

# Key Vault audit logging
az monitor diagnostic-settings create \
  --name "diag-kv-${TENANT_ID}" \
  --resource "${KEY_VAULT_ID}" \
  --workspace "${LAW_ID}" \
  --logs '[{"category":"AuditEvent","enabled":true}]'
```

---

## Microsoft Sentinel Configuration

```bash
# Enable Sentinel on the LAW
az sentinel workspace create \
  --resource-group "$HUB_RG" \
  --workspace-name "law-platform-${REGION}"

# Connect data connectors
for connector in \
  AzureActivityLog \
  AzureActiveDirectory \
  MicrosoftDefenderForCloud \
  KubernetesAudit \
  AzureFirewall; do
  az sentinel data-connector create \
    --resource-group "$HUB_RG" \
    --workspace-name "law-platform-${REGION}" \
    --data-connector-kind "$connector" \
    --name "$connector"
done
```

---

## KQL Audit Queries

### Kubernetes: Privileged Operations
```kql
AzureDiagnostics
| where Category == "kube-audit"
| where RequestURI_s has_any ("cluster-admin", "clusterrolebindings", "secrets")
| where Verb_s in ("create", "update", "delete", "patch")
| where User_s !startswith "system:"
| project TimeGenerated, User_s, Verb_s, RequestURI_s, SourceIps_s
| order by TimeGenerated desc
```

### Key Vault: Secret Access Pattern
```kql
AzureDiagnostics
| where ResourceType == "VAULTS" and OperationName == "SecretGet"
| summarize AccessCount = count() by CallerIPAddress, identity_claim_upn_s, bin(TimeGenerated, 1h)
| where AccessCount > 50
| order by AccessCount desc
```

### Failed Login Attempts (Entra ID)
```kql
SigninLogs
| where ResultType != "0"
| summarize FailureCount = count() by UserPrincipalName, IPAddress, bin(TimeGenerated, 1h)
| where FailureCount > 10
| order by FailureCount desc
```

### Azure RBAC Changes
```kql
AzureActivity
| where OperationNameValue contains "roleAssignment"
| where ActivityStatusValue == "Success"
| project TimeGenerated, Caller, OperationNameValue, ResourceGroup,
  Properties = parse_json(Properties)
| extend TargetRole = Properties.roleDefinitionName,
         TargetPrincipal = Properties.principalName
| order by TimeGenerated desc
```

### Terraform Destroy Operations
```kql
AzureActivity
| where OperationNameValue contains "delete" and ActivityStatusValue == "Start"
| where Caller !has "terraform-managed-identity"
| project TimeGenerated, Caller, OperationNameValue, ResourceGroup, Resource
| order by TimeGenerated desc
```

### Network: Traffic from Unexpected IPs
```kql
AzureNetworkAnalytics_CL
| where FlowType_s == "ExternalPublic"
| where SrcIP_s !in (split(APPROVED_IPS, ","))
| where DestPort_d in (22, 3389, 5432, 1433)
| summarize ConnectionCount = count() by SrcIP_s, DestIP_s, DestPort_d
| where ConnectionCount > 5
| order by ConnectionCount desc
```

---

## Sentinel Detection Rules (Analytics Rules)

```bash
# Create a scheduled analytics rule for brute force detection
az sentinel alert-rule create \
  --resource-group "$HUB_RG" \
  --workspace-name "law-platform-${REGION}" \
  --rule-name "BruteForceDetection" \
  --kind Scheduled \
  --display-name "Brute Force Login Attempt" \
  --severity High \
  --enabled true \
  --query-frequency PT1H \
  --query-period PT1H \
  --trigger-operator GreaterThan \
  --trigger-threshold 0 \
  --query "SigninLogs | where ResultType != '0' | summarize count() by UserPrincipalName | where count_ > 10"
```

### Automated Response Playbook (Logic App)
On high-severity incident:
1. Page on-call (PagerDuty)
2. Post alert to #security-incidents Slack
3. Enrich alert with threat intel
4. If confirmed account compromise → disable user in Entra ID (requires approval)

---

## Compliance Evidence Package

For audits (SOC2, ISO27001):

```bash
generate_audit_evidence() {
  local period_start=$1 period_end=$2 output_dir=$3

  mkdir -p "$output_dir"

  # 1. Admin actions log
  az monitor activity-log list \
    --start-time "$period_start" --end-time "$period_end" \
    --query "[?contains(authorization.action, 'write') || contains(authorization.action,'delete')]" \
    --output json > "$output_dir/admin-actions.json"

  # 2. Key Vault access log
  az monitor log-analytics query \
    --workspace "$LAW_ID" \
    --analytics-query "AzureDiagnostics | where ResourceType=='VAULTS' | where TimeGenerated between (datetime('${period_start}')..datetime('${period_end}'))" \
    --output json > "$output_dir/keyvault-access.json"

  # 3. Privileged K8s operations
  # (KQL query against LAW → output to CSV)

  # 4. Failed login summary
  # (KQL query → output to CSV)

  # 5. Policy compliance state
  az policy state summarize \
    --subscription "$SUBSCRIPTION_ID" \
    --output json > "$output_dir/policy-compliance.json"

  echo "Evidence package ready: $output_dir"
  ls -la "$output_dir"
}
```

---

## Examples

- "Show me all admin operations performed on the prod environment last week"
- "Who accessed the payments-api secrets in Key Vault in the past 30 days?"
- "Set up Sentinel with all connectors for the new production subscription"
- "Generate a SOC2 evidence package for the Q2 audit period"
- "Alert me when any cluster-admin bindings are created in any namespace"
- "Show failed login attempts for all service accounts in the last 24 hours"

---

## Output Format

```json
{
  "operation": "query|setup|alert-create|evidence-package",
  "query_period": { "start": "string", "end": "string" },
  "results_count": 0,
  "high_severity_events": 0,
  "evidence_files": [],
  "sentinel_workspace": "string",
  "status": "success|failure"
}
```
