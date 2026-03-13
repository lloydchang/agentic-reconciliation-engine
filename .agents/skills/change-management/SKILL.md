---
name: change-management
description: >
  Use this skill to automate the change management lifecycle:
  risk scoring, change advisory board (CAB) coordination,
  change freeze window enforcement, rollback planning, and audit trail
  generation. Triggers: any request to raise a change request, score a change
  for risk, check if a deployment is blocked by a change freeze, coordinate
  an emergency change, generate the weekly change calendar, or produce a
  change success rate report.
tools:
  - bash
  - computer
---

# Change Management Skill

Automate change governance: from risk scoring a PR through CAB review,
change freeze enforcement, to post-change audit. Reduce overhead while
maintaining control.

---

## Change Types

| Type       | Definition                         | Approval required   | Lead time |
|------------|------------------------------------|---------------------|-----------|
| Standard   | Pre-approved, low-risk, routine    | None (auto)         | 0         |
| Normal     | Assessed, medium-risk              | CAB or peer review  | 24 hr     |
| Emergency  | High urgency, any risk level       | Emergency CAB (2 approvers) | ASAP |
| Major      | High-risk, broad impact            | Full CAB + leadership | 72 hr  |

---

## Risk Scoring

```python
def score_change_risk(change: dict) -> dict:
    score = 0
    reasons = []

    # Impact scope
    if change["environments"] == ["prod"]:
        score += 30; reasons.append("Production-only change (+30)")
    elif "prod" in change["environments"]:
        score += 20; reasons.append("Includes production (+20)")

    # Tenant blast radius
    tenant_count = change.get("affected_tenants", 0)
    if tenant_count > 50:
        score += 25; reasons.append(f"Affects {tenant_count} tenants (+25)")
    elif tenant_count > 10:
        score += 15; reasons.append(f"Affects {tenant_count} tenants (+15)")

    # Change category
    category_scores = {
        "database_schema": 25, "network": 20, "security": 20,
        "iam": 20, "kubernetes": 15, "application": 10,
        "config": 5, "documentation": 0
    }
    cat = change.get("category", "application")
    cat_score = category_scores.get(cat, 10)
    score += cat_score
    reasons.append(f"Category: {cat} (+{cat_score})")

    # Rollback complexity
    rollback = change.get("rollback_plan", "none")
    if rollback == "none":
        score += 20; reasons.append("No rollback plan (+20)")
    elif rollback == "complex":
        score += 10; reasons.append("Complex rollback (+10)")

    # Change window
    if not change.get("maintenance_window"):
        score += 10; reasons.append("No maintenance window (+10)")

    # Previous failures
    prev_failures = change.get("previous_failure_count", 0)
    if prev_failures > 0:
        score += 15; reasons.append(f"{prev_failures} previous failures (+15)")

    # Determine type
    if score < 20:
        change_type = "standard"
    elif score < 50:
        change_type = "normal"
    elif score < 75:
        change_type = "major"
    else:
        change_type = "high-risk-major"

    return {
        "risk_score": score,
        "change_type": change_type,
        "reasons": reasons,
        "approval_required": change_type != "standard"
    }
```

---

## Change Request Template

```markdown
## Change Request: ${CR_ID}

**Title:** ${title}
**Requestor:** ${requestor}
**Target date/time:** ${datetime} UTC
**Change type:** ${type}  **Risk score:** ${score}/100

### Description
${description}

### Scope
- Environments: ${environments}
- Tenants affected: ${affected_tenants}
- Services affected: ${services}
- Estimated duration: ${duration}

### Technical Implementation Steps
1. ${step_1}
2. ${step_2}
...

### Rollback Plan
${rollback_plan}
**Rollback trigger:** ${rollback_trigger}
**Rollback time estimate:** ${rollback_time}

### Testing / Validation
${validation_steps}

### Communication Plan
${comms_plan}

### Approvals Required
- [ ] ${approver_1}
- [ ] ${approver_2} (if risk > 50)
```

---

## Change Freeze Windows

```python
FREEZE_WINDOWS = [
    # Format: (start_iso, end_iso, description, exceptions_allowed)
    ("2025-12-20T00:00:00Z", "2026-01-03T00:00:00Z",
     "Year-end freeze", False),
    ("2025-11-27T18:00:00Z", "2025-11-30T18:00:00Z",
     "US Thanksgiving", True),
    ("2025-06-30T12:00:00Z", "2025-07-01T12:00:00Z",
     "Quarter-end freeze", True),
]

def check_change_freeze(proposed_datetime: str) -> dict:
    dt = datetime.fromisoformat(proposed_datetime.replace("Z", "+00:00"))
    for start, end, description, exceptions_ok in FREEZE_WINDOWS:
        if datetime.fromisoformat(start) <= dt <= datetime.fromisoformat(end):
            return {
                "frozen": True,
                "freeze_name": description,
                "exceptions_allowed": exceptions_ok,
                "unfreeze_at": end
            }
    return {"frozen": False}
```

### Enforcement Hook (CI/CD)
```bash
check_deployment_allowed() {
  local env=$1
  [[ "$env" != "prod" ]] && return 0  # Only enforce on prod

  FREEZE=$(curl -sf "${PLATFORM_API}/change-freeze/check" \
    -d "{\"datetime\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" | jq -r '.frozen')

  [[ "$FREEZE" == "true" ]] && {
    echo "BLOCKED: Change freeze is active. See #change-freeze for emergency exceptions."
    exit 1
  }
}
```

---

## CAB Automation

```bash
# Create change request in ServiceNow
create_change_request() {
  curl -X POST "${SERVICENOW_URL}/api/now/table/change_request" \
    -H "Authorization: Basic ${SN_CREDENTIALS}" \
    -H "Content-Type: application/json" \
    -d "{
      \"short_description\": \"${TITLE}\",
      \"description\": \"${DESCRIPTION}\",
      \"risk\": \"${RISK_LEVEL}\",
      \"type\": \"${CHANGE_TYPE}\",
      \"start_date\": \"${START_DATE}\",
      \"end_date\": \"${END_DATE}\",
      \"assignment_group\": \"cab-team\",
      \"cmdb_ci\": \"${AFFECTED_CI}\"
    }" | jq -r '.result.number'
}

# Notify approvers via Slack with approve/reject buttons
post_cab_request() {
  curl -X POST "$SLACK_WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "{
      \"text\": \"CAB Approval Required: ${CR_ID}\",
      \"blocks\": [
        {\"type\": \"section\", \"text\": {\"type\": \"mrkdwn\",
          \"text\": \"*${TITLE}*\\nRisk: ${RISK_SCORE}/100 | Type: ${CHANGE_TYPE}\"}},
        {\"type\": \"actions\", \"elements\": [
          {\"type\": \"button\", \"text\": {\"type\": \"plain_text\", \"text\": \"Approve\"},
           \"style\": \"primary\", \"action_id\": \"approve_cr\", \"value\": \"${CR_ID}\"},
          {\"type\": \"button\", \"text\": {\"type\": \"plain_text\", \"text\": \"Reject\"},
           \"style\": \"danger\", \"action_id\": \"reject_cr\", \"value\": \"${CR_ID}\"}
        ]}
      ]
    }"
}
```

---

## Emergency Change Process

```
Emergency identified
     ↓
Raise emergency CR (all fields required: reason, impact, rollback)
     ↓
Auto-page: On-call lead + Engineering Manager (2 approvers needed)
     ↓
Verbal approval captured in CR record within 15 min
     ↓
Implement change
     ↓
Post-implementation review within 24 hr
     ↓
Full retrospective within 72 hr
```

---

## Change Calendar & Weekly Report

```
Change Calendar — Week of [DATE]
─────────────────────────────────
Monday
  14:00 UTC — [Normal] K8s 1.30 upgrade — aks-staging (CR-2025-0441)

Wednesday
  22:00 UTC — [Standard] Deploy payments-api v2.3.1 (auto-approved)

Thursday
  20:00 UTC — [Major] Database schema migration — tenant-42 (PENDING APPROVAL)
  Approvers needed: @alice, @bob

Change Success Rate (last 30 days)
  Total changes:    127
  Successful:       122 (96.1%)  ✅ target 95%
  Failed/rolled back: 5 (3.9%)
  Emergency changes:  2
  Change freeze violations: 0 ✅
```

---

## Examples

- "Score the risk of deploying a new database schema to prod for 45 tenants"
- "Create a change request for the K8s 1.30 upgrade on the prod cluster"
- "Is there a change freeze for next week? Can I deploy on Dec 22nd?"
- "Generate this week's change calendar and email it to the ops team"
- "Show me all changes that failed or were rolled back in the last quarter"
- "I need an emergency change to fix a P1 — walk me through the process"

---

## Output Format

```json
{
  "cr_id": "CR-2025-0001",
  "change_type": "standard|normal|major|emergency",
  "risk_score": 0,
  "risk_reasons": [],
  "frozen": false,
  "approval_status": "auto-approved|pending|approved|rejected",
  "approvers": [],
  "scheduled_datetime": "ISO8601",
  "status": "draft|submitted|approved|implemented|closed|rolled-back"
}
```
