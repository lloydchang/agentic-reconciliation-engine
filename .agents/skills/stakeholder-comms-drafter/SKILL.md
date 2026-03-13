---
name: stakeholder-comms-drafter
description: >
  Use this skill to draft, structure, and send stakeholder
  communications for teams. Triggers: any request to write an
  incident notification, executive status update, platform change announcement,
  risk escalation, SLA breach notification, quarterly business review summary
  email, or cross-team alignment memo. Also triggers when asking for help
  communicating progress, risks, or outages to leadership or customers.
tools:
  - bash
  - computer
---

# Stakeholder Communications Drafter Skill

Generate clear, appropriately pitched communications for every stakeholder
audience — from real-time incident Slack updates to executive QBR summaries.
Drafts are produced instantly; a human always reviews and sends.

---

## Audience Profiles

| Audience           | Tone              | Detail level | Primary concern              |
|--------------------|-------------------|--------------|------------------------------|
| Executive / C-suite| Concise, decisive | Low          | Business impact, risk, cost  |
| Engineering leads  | Technical, direct | High         | Root cause, fix, timeline    |
| Product teams      | Collaborative     | Medium       | Impact on features/customers |
| Customers / tenants| Empathetic, clear | Low-medium   | Impact, ETA, workarounds     |
| Security / audit   | Formal, precise   | High         | Compliance, evidence         |
| Operations team    | Tactical, fast    | High         | Actions, who does what       |

---

## Communication Templates

### 1. Incident Status Update (Slack / Teams)

```
🔴 [P{SEVERITY} INCIDENT] {TITLE}
────────────────────────────────
Time detected:  {HH:MM UTC}
Affected:       {tenants / services / regions}
Impact:         {user-visible description}
Current status: {Investigating | Identified | Mitigating | Resolved}

What we know:   {1-2 sentence summary}
Next update:    {HH:MM UTC} or when status changes

Incident lead:  @{name}
Bridge:         {link}
```

Update cadence:
- P1: every 15 minutes until resolved
- P2: every 30 minutes
- P3/P4: on status change only

### 2. Incident Resolution Summary

```
✅ [RESOLVED] {TITLE} — INC-{ID}
────────────────────────────────
Duration:       {X hours Y minutes}
Root cause:     {1-2 sentences}
Impact:         {tenants/users affected, data loss Y/N}
Resolution:     {what fixed it}
SLA status:     {Within SLA | Breach — {minutes over}}

Immediate actions taken:
  • {action 1}
  • {action 2}

Next steps (permanent fix):
  • {action} — Owner: {name} — Due: {date}

Post-mortem:    {link} (draft within 24 hr)
```

### 3. Executive Weekly Status Email

Subject: `Cloud AI — Weekly Status [Date]`

```
Summary: {GREEN | AMBER | RED} — {one-line headline}

Platform Health
  Uptime:               {X.XX%} (target {X.XX%}) {✅|⚠️|🔴}
  Deployments:          {N} ({N} success, {N} failed)
  Incidents:            {N} total — MTTR avg {N} min
  Error budget:         {N}% remaining

Key Achievements This Week
  • {achievement 1}
  • {achievement 2}

Risks & Issues
  • {risk 1} — Mitigation: {description}

Next Week Priorities
  1. {priority}
  2. {priority}

[Full dashboard] {link}
```

### 4. Platform Change Announcement

Subject: `[Action Required / FYI] {Change Title} — {Date}`

```
Hi {team/audience},

We are {deploying | migrating | retiring} {component} on {date} at {time} UTC.

What's changing:
  {description}

Impact on your team:
  {specific impact — "no action needed" or "you need to..."}

Timeline:
  {date time} — Maintenance window begins
  {date time} — Expected completion
  {date time} — Rollback decision point (if issues arise)

What to do:
  {clear action items, if any}

Questions? Reach us at #{slack-channel} or reply to this email.

{Name}, Team
```

### 5. SLA Breach Notification (Customer-facing)

```
Subject: Service Disruption Report — {Tenant/Product} — {Date}

Dear {Customer Name},

We are writing to inform you of a service disruption that affected your
environment on {date}.

Duration:    {HH:MM UTC} – {HH:MM UTC} ({X minutes})
Impact:      {description of what was unavailable or degraded}
Root cause:  {brief, non-technical explanation}

This incident resulted in {X minutes} of downtime against your {SLA tier}
SLA of {X}% monthly uptime.

Actions we have taken:
  • {action 1}
  • {action 2}

Preventive measures:
  • {measure 1} — Expected completion: {date}

Your SLA credit, if applicable, will be applied to your next invoice
per the terms of your service agreement.

We sincerely apologise for the disruption and are committed to the
reliability standards your business depends on.

{Name}
{Organization}
```

### 6. Risk Escalation to Leadership

```
Subject: [Risk Escalation] {Risk Title} — Decision Required by {Date}

Context:
  {2-3 sentence background}

Risk:
  {Clear description of the risk and what could happen if unaddressed}

Probability:  {Low | Medium | High}
Impact:       {Low | Medium | High | Critical}
Time horizon: {when the risk materialises}

Options:
  Option A: {description} — Cost: ${X} — Timeline: {X weeks}
  Option B: {description} — Cost: ${X} — Timeline: {X weeks}
  Option C: Accept risk — Rationale: {description}

Recommendation:
  {Option X} because {justification}

Decision needed by: {date}
Owner if approved: {name}
```

---

## Communication Workflow

1. **Generate draft** using the appropriate template above
2. **Populate** from incident/deployment/report data automatically
3. **Tone-match** to audience profile
4. **Flag for review** — never auto-send
5. **Log** the communication in the incident or project record

---

## Writing Rules

- Lead with impact, not process
- Use plain numbers: "12 minutes of downtime" not "an extended disruption event"
- One ask per communication
- No jargon for customer-facing content
- Always include a next-update time for ongoing incidents
- Link to dashboards/tickets — don't embed everything in the email
- 3 bullet max for exec summaries; full detail available on request

---

## Examples

- "Draft a P2 incident update for Slack — the AKS cluster in East US is degraded"
- "Write the resolution email for last night's database outage to send to affected tenants"
- "Generate the weekly executive status email from this week's KPI data"
- "Draft the change announcement for the Kubernetes 1.29 upgrade next Tuesday"
- "Write a risk escalation memo about our single-region deployment for the CTO"

---

## Output Format

```json
{
  "comm_type": "incident_update|resolution|executive_status|change_announcement|sla_breach|risk_escalation",
  "audience": "string",
  "subject": "string",
  "body": "string",
  "channel": "email|slack|teams",
  "review_required": true,
  "sent": false
}
```
