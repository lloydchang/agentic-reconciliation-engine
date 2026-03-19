# Agentic Reconciliation Engine (ARE)

<img width="180" height="180" alt="ARE Logo" src="https://github.com/user-attachments/assets/122d93a7-60d4-4ada-9b2e-e29bdd5e4202" />

**ARE** is an event-driven automation framework that bridges stateless GitOps controllers with agentic AI reasoning for persistent infrastructure challenges. It extends traditional reconciliation with memory, learning, and complex problem-solving capabilities.

**Core Integration:** [AGENTS.md](./AGENTS.md) policies + [SKILL.md](https://agentskills.io/) capabilities + [SQLite](https://sqlite.org/) memory + [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765) reasoning + [Temporal](https://temporal.io/) orchestration, triggered by [Crossplane](https://www.crossplane.io/)/[Flux](https://fluxcd.io/) events via [Argo Events](https://argoproj.github.io/argo-events/) and [Prometheus](https://prometheus.io/) monitoring.

---

### 🏗️ Architecture Overview

**Event-Driven Bridge:**
- **Monitoring Layer:** Prometheus + Alertmanager watches controller health and generates alerts
- **Event Bus:** Argo Events captures alerts, webhooks, and scheduled triggers  
- **AI Reasoning Layer:** Memory agents (SQLite) + Qwen LLM provide context and decision-making
- **Orchestration Layer:** Temporal workflows execute complex multi-step remediations
- **Control Layer:** GitOps (Flux/ArgoCD) applies changes safely with PR validation

**Component Responsibilities:**
* **Agentic AI Layer:** Memory persistence, pattern recognition, policy evaluation, skill selection, workflow orchestration
* **GitOps Control Layer:** Resource reconciliation, drift detection, safe change application, audit trails

---

### ⚙️ Escalation Flow

**1. Detection & Triage**
- **Observe:** Prometheus monitors Flux/Crossplane controller logs, reconciliation status, and resource health
- **Alert:** Alertmanager fires alerts for persistent failures (e.g., 5+ consecutive reconcile failures)
- **Classify:** Alert routing rules determine severity and escalation requirements

**2. Event Bridging**  
- **Capture:** Argo Events sensors consume Prometheus alerts and webhook events
- **Enrich:** Event payloads include failure context, resource metadata, and historical patterns
- **Trigger:** Sensors invoke memory agent API with structured event data

**3. Contextual Analysis**
- **Recall:** Memory agent queries SQLite for similar historical incidents and successful interventions
- **Pattern Match:** Qwen LLM analyzes current failure against stored patterns and AGENTS.md policies
- **Skill Selection:** System selects appropriate SKILL.md based on failure type and context

**4. Orchestration & Execution**
- **Plan:** Temporal workflow generates structured remediation plan with safety gates
- **Validate:** Plan undergoes risk assessment and human approval if required
- **Execute:** Multi-step workflow runs via GitOps (PR creation → validation → apply)

**5. Learning & Persistence**
- **Log:** Results, effectiveness, and new patterns stored in SQLite memory
- **Update:** Success/failure rates refine future decision-making
- **Inform:** Enhanced context available for subsequent incidents

---

### 🔍 Critical Integration Points

**Event Flow Requirements:**
- **Prometheus Configuration:** Alert rules must target controller-specific metrics (reconcile failures, resource drift)
- **Argo Events Setup:** Sensors need proper RBAC and network access to memory agent endpoints
- **Memory Agent API:** REST endpoints for event ingestion, context queries, and result storage
- **Temporal Integration:** Workflow templates for common remediation patterns

**Data Flow Gaps to Address:**
- **Alert Enrichment:** Prometheus alerts need controller context and resource metadata
- **Event Correlation:** Multiple related alerts should trigger single consolidated workflow
- **State Synchronization:** Memory agent must maintain real-time view of controller status
- **Rollback Handling:** Failed remediations need automatic rollback and incident logging

### 📂 Quick Links

* [**Quickstart**](./docs/QUICKSTART.md) — Prerequisites and automation.
* [**Architecture**](./docs/AGENT-ARCHITECTURE-OVERVIEW.md) — Deep dive into the escalation logic.
* [**Skills Guide**](./docs/AGENTIC-AI-SKILLS-GUIDE.md) — Catalog of 91 autonomous capabilities.
* [**Safety Rules**](./docs/CRITICAL-SAFETY-RULES-BEST-PRACTICES.md) — Operational best practices.

---

### 🛠️ Getting Started

**Initialize:** Run `core/scripts/automation/quickstart.sh`

*This single command validates prerequisites and sets up the entire environment.*

**Optional:** Validate prerequisites only:
```bash
core/scripts/automation/quickstart.sh --validate-only
```

---

### ⚖️ License

**AGPL-3.0-or-later** — [Full License](LICENSE)
