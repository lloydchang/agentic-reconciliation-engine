---
name: runbook-documentation-gen
description: >
  Use this skill to automatically generate, update, and maintain operational
  runbooks, architecture decision records (ADRs), platform documentation, and
  wiki pages. Triggers: any request to write or update a runbook, document an
  incident pattern, create an ADR, generate API or infrastructure documentation
  from code/config, produce an onboarding guide, or keep documentation in sync
  with current platform state.
tools:
  - bash
  - computer
---

# Runbook & Documentation Generator Skill

Auto-generate and maintain high-quality operational documentation from live
system state, incident history, code, and configuration. Keep docs in sync
with reality — not written once and forgotten.

## Runbook Generation

### From Operational Logs
Analyze operational logs to identify recurring tasks and generate standardized procedures.

### Workflow for Runbook Generation
1. Analyze operational logs.
2. Identify recurring operational tasks.
3. Generate standardized runbooks.

Each runbook includes:
- incident description
- diagnostic steps
- remediation steps
- escalation criteria

### Enhanced Runbook Template
```markdown
---
name: {alert-name-kebab}
trigger_pattern: "{prometheus_alert_name}"
severity: P2
owner: live system owner
last_updated: {date}
---

# Runbook: {Human Readable Title}

## Overview
Brief description of the problem this runbook addresses.

## Symptoms
- Alert: `{alert_name}` fires in Prometheus/PagerDuty
- Users may see: {user-visible symptoms}

## Impact
- Affected components: {list}
- Blast radius: {description}

## Diagnosis Steps
### 1. {Step Name}
**Command:**
```bash
{command}
```
**Expected output:** {description}
**If unexpected:** {what to do}

## Resolution Steps
### 1. {Step Name}
**Command:**
```bash
{command}
```
**Rollback:**
```bash
{rollback_command}
```

## Escalation
If unresolved after 30 min → escalate to {team} via PagerDuty escalation policy.

## Post-Resolution
- [ ] Verify service health
- [ ] Update incident ticket with RCA
- [ ] Check if runbook needs updating
- [ ] Open ticket for permanent fix if applicable

## Related Runbooks
- {link}

## Change Log
| Date | Author | Change |
|------|--------|--------|
| {date} | {author} | Initial creation |
```

---

## Document Types

| Type               | Trigger                               | Output format       |
|--------------------|---------------------------------------|---------------------|
| Runbook            | New incident pattern or manual request| Markdown + YAML     |
| ADR                | Architecture decision made            | Markdown (MADR)     |
| Postmortem         | Incident resolved                     | Markdown / Notion   |
| API reference      | OpenAPI spec or code change           | Markdown / HTML     |
| Infrastructure doc | Terraform state or diagram request    | Markdown + diagrams |
| Onboarding guide   | New team member or service            | Markdown            |
| Changelog          | Release completed                     | Markdown            |
| Wiki sync          | Scheduled or on-change                | Confluence / Notion |

---

## Runbook Generation

### From Incident History
Analyse past incidents to extract a repeatable runbook:

```python
# Pseudo-code for pattern extraction
incidents = query_incident_db(alert_name=alert, limit=20)
steps = extract_resolution_steps(incidents)  # LLM-assisted
runbook = format_runbook(alert, steps)
```

### Runbook Template
```markdown
---
name: {alert-name-kebab}
trigger_pattern: "{prometheus_alert_name}"
severity: P2
owner: incidents owner
last_updated: {date}
---

# Runbook: {Human Readable Title}

## Overview
Brief description of the problem this runbook addresses.

## Symptoms
- Alert: `{alert_name}` fires in Prometheus/PagerDuty
- Users may see: {user-visible symptoms}

## Impact
- Affected components: {list}
- Blast radius: {description}

## Diagnosis Steps
### 1. {Step Name}
**Command:**
\```bash
{command}
\```
**Expected output:** {description}
**If unexpected:** {what to do}

## Resolution Steps
### 1. {Step Name}
**Command:**
\```bash
{command}
\```
**Rollback:**
\```bash
{rollback_command}
\```

## Escalation
If unresolved after 30 min → escalate to {team} via PagerDuty escalation policy.

## Post-Resolution
- [ ] Verify service health
- [ ] Update incident ticket with RCA
- [ ] Check if runbook needs updating
- [ ] Open ticket for permanent fix if applicable

## Related Runbooks
- {link}

## Change Log
| Date | Author | Change |
|------|--------|--------|
| {date} | {author} | Initial creation |
```

---

## Architecture Decision Records (ADRs)

Use the MADR format:

```markdown
# ADR-{NNN}: {Title}

**Date:** {YYYY-MM-DD}
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-{NNN}
**Deciders:** {list of people involved}
**Tags:** multi-cloud, kubernetes, security

## Context and Problem Statement
{Describe the architectural problem and context.}

## Decision Drivers
- {driver 1}
- {driver 2}

## Considered Options
1. {Option A}
2. {Option B}
3. {Option C}

## Decision Outcome
**Chosen: {Option X}** because {justification}.

### Positive Consequences
- {consequence}

### Negative Consequences
- {consequence}

## Pros and Cons of the Options

### Option A
**Pro:** {pro}
**Con:** {con}

### Option B
...

## Links
- {Link to relevant tickets, RFCs, or external references}
```

---

## Infrastructure Documentation from Terraform State

```bash
# Generate module README via terraform-docs
terraform-docs markdown table --output-file README.md ./modules/${MODULE}

# Generate architecture diagram via Inframap
inframap generate --tfstate terraform.tfstate | dot -Tsvg > architecture.svg

# Generate resource inventory
terraform state list | while read resource; do
  echo "## $resource"
  terraform state show "$resource"
done > infrastructure-inventory.md
```

---

## API Documentation from OpenAPI Spec

```bash
# Generate rich Markdown from OpenAPI spec
npx @redocly/cli build-docs openapi.yaml --output docs/api.html

# Validate spec completeness
npx @redocly/cli lint openapi.yaml
```

Enforce documentation standards:
- Every endpoint has a description and example
- All response codes documented
- Authentication requirements stated
- Changelog entry on breaking changes

---

## Documentation Sync to Wiki

### Confluence
```bash
confluence_upload() {
  local file=$1
  local page_id=$2
  local content=$(python3 -m markdown "$file")
  curl -X PUT "$CONFLUENCE_URL/rest/api/content/$page_id" \
    -H "Authorization: Basic $CONFLUENCE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"version\":{\"number\":$((CURRENT_VERSION+1))},
         \"title\":\"$TITLE\",\"type\":\"page\",
         \"body\":{\"storage\":{\"value\":\"$content\",\"representation\":\"storage\"}}}"
}
```

### Notion
```bash
# Via Notion API
curl -X PATCH "https://api.notion.com/v1/pages/$PAGE_ID" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -d "$NOTION_PAYLOAD"
```

---

## Documentation Quality Gates

Before merging or publishing:
- [ ] All commands tested in a non-prod environment
- [ ] Links validated (no 404s)
- [ ] Spelling / grammar check (`vale` linter)
- [ ] Reviewed by at least one team member
- [ ] Runbooks: trigger_pattern tested against real alert
- [ ] Diagrams up to date with current architecture

---

## Examples

- "Generate a runbook for the 'PodCrashLoopBackOff' alert based on our last 10 incidents"
- "Write an ADR for choosing Argo Rollouts over Flagger for canary deployments"
- "Generate API documentation for the tenant management service from its OpenAPI spec"
- "Create an onboarding guide for a new person joining the team"
- "Sync all runbooks in ./runbooks/ to our Confluence space"

---

## Output Format

```json
{
  "doc_type": "runbook|adr|postmortem|api_ref|infra_doc|onboarding",
  "title": "string",
  "file_path": "string",
  "word_count": 0,
  "quality_gates_passed": true,
  "wiki_synced": false,
  "wiki_url": null
}
```
