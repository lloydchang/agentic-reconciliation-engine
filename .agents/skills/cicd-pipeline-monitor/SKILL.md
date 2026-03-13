---
name: cicd-pipeline-monitor
description: >
  Use this skill to monitor, trigger, diagnose, and remediate CI/CD pipelines
  across GitHub Actions, Azure DevOps, Jenkins, and ArgoCD. Triggers: any
  request to check pipeline status, investigate a build failure, re-trigger a
  deployment, analyse flaky tests, enforce pipeline standards, generate a
  deployment summary report, or show DORA metrics, deployment frequency,
  change failure rate, mean time to restore.
tools:
  - bash
  - computer
---

# CI/CD Pipeline Monitor Skill

Provide full observability and automated remediation for CI/CD pipelines.
Connect to pipeline APIs, parse run results, surface root-cause analysis,
and take corrective action within defined safe-action boundaries.

---

## Supported Platforms

| Platform       | Auth method              | API base                              |
|----------------|--------------------------|---------------------------------------|
| GitHub Actions | `GITHUB_TOKEN` env var   | `https://api.github.com`              |
| Azure DevOps   | `ADO_PAT` env var        | `https://dev.azure.com/{org}`         |
| Jenkins        | `JENKINS_USER/TOKEN`     | `http://{host}/api/json`              |
| ArgoCD         | `ARGOCD_TOKEN`           | `https://{host}/api/v1`               |

---

## Core Workflows

### Check Pipeline Status
```bash
# GitHub Actions
gh run list --repo $REPO --limit 10 --json status,conclusion,name,createdAt

# Azure DevOps
az pipelines runs list --org $ADO_ORG --project $PROJECT --top 10

# ArgoCD
argocd app list --output json
```

Parse and return:
- Run ID, pipeline name, trigger, status, duration
- Last success timestamp
- Consecutive failure count

### Investigate a Failed Run
1. Fetch the failed run's logs
2. Extract the failing step and error block (last 50 lines of failing job)
3. Classify error type:
   - **Flaky test** → flag for retry, log to flake tracker
   - **Infra timeout** → retry once, then escalate
   - **Config/code error** → open issue with full context
   - **Dependency failure** → check upstream pipeline / registry health
4. Return structured diagnosis

### Trigger / Re-trigger
```bash
# GitHub Actions
gh workflow run $WORKFLOW --repo $REPO --ref $BRANCH

# Azure DevOps
az pipelines run --id $PIPELINE_ID --branch $BRANCH

# ArgoCD sync
argocd app sync $APP_NAME --force
```
Only auto-trigger re-runs for classified flaky/infra failures.
Code/config failures require human review first.

### Deployment Summary Report
Aggregate across all pipelines for a time window:
```
Deployments:     total | successful | failed | rolled-back
Mean lead time:  X minutes
Change fail rate: X%
MTTR:            X minutes
Top failing pipelines: [list]
```

---

## Alerting Thresholds

| Metric                    | Warning | Critical |
|---------------------------|---------|----------|
| Consecutive failures      | 2       | 3        |
| Pipeline duration (P95)   | +50%    | +100%    |
| Change fail rate (7-day)  | >10%    | >25%     |
| Queue depth               | >20     | >50      |

On threshold breach: emit a structured alert → route to incident channel.

---

## Pipeline Standards Enforcement

When reviewing or generating pipelines, enforce:
- All secrets via vault/secret-store — never plaintext in YAML
- Branch protection: `main`/`prod` require passing checks before merge
- Docker images pinned to digest, not `latest`
- Scan steps: SAST (e.g., `semgrep`), container scan (`trivy`), IaC scan (`checkov`)
- Separate build / test / deploy stages with explicit approval gates for prod
- Artifacts retained for minimum 30 days

---

## Safe Action Boundaries

| Action                   | Auto | Requires Approval |
|--------------------------|------|-------------------|
| Re-run flaky test        | ✅   |                   |
| Re-run infra timeout     | ✅   |                   |
| Cancel stuck run (>2h)   | ✅   |                   |
| Trigger prod deployment  |      | ✅                |
| Modify pipeline YAML     |      | ✅                |
| Disable a pipeline       |      | ✅                |

---

## Examples

- "What failed in the last prod deployment?"
- "Show me all pipelines that failed more than twice this week"
- "Re-run the flaky integration tests on the payments service"
- "Generate a DORA metrics report for the last 30 days"
- "Check if the ArgoCD sync for tenant-42 completed successfully"

---

## Output Format

```json
{
  "pipeline_tool": "github-actions|azuredevops|jenkins|argocd",
  "pipeline": "string",
  "failure_reason": "string",
  "status": "success|failure|running|queued",
  "last_run": "ISO8601",
  "diagnosis": { "error_type": "string", "failing_step": "string", "message": "string" },
  "action_taken": "none|retried|escalated",
  "metrics": { "lead_time_min": 0, "fail_rate_pct": 0 },
  "dora": { "deployment_frequency": 0, "lead_time": 0, "mttr": 0, "change_fail_rate": 0 }
}
```
