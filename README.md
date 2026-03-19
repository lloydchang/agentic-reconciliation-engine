# Agentic Reconciliation Engine (ARE)

<img width="180" height="180" alt="ARE Logo" src="https://github.com/user-attachments/assets/122d93a7-60d4-4ada-9b2e-e29bdd5e4202" />

**ARE** is a sandbox that provides agentic AI memory and reasoning for challenges beyond stateless reconciliation. Combines AGENTS.md, SKILL.md, SQLite, Qwen, llama.cpp, Temporal with Crossplane, Flux, Kubernetes.

Combines [AGENTS.md](https://agents.md/), [SKILL.md](https://agentskills.io/), [SQLite](https://sqlite.org/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [llama.cpp](https://github.com/ggml-org/llama.cpp), [Temporal](https://temporal.io/) with [Argo](https://argoproj.github.io/), [Flux](https://fluxcd.io/), [Crossplane](https://www.crossplane.io/), [Kubernetes](https://kubernetes.io/).

---

### 🏗️ Separation of Concerns

* **Agentic AI Layer (A):** [AGENTS.md](https://agents.md/), [SKILL.md](https://agentskills.io/), [SQLite](https://sqlite.org/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [llama.cpp](https://github.com/ggml-org/llama.cpp), [Temporal](https://temporal.io/): Complex actions that stateless controllers cannot reconcile.
* **Reconciliation Engine (RE):** [Argo](https://argoproj.github.io/), [Flux](https://fluxcd.io/), [Crossplane](https://www.crossplane.io/), [Kubernetes](https://kubernetes.io/): Standard resource lifecycle, cross-provider orchestration, drift detection, and mechanical synchronization.

---

### 🛠️ Getting Started

**Initialize:** Run `core/scripts/automation/quickstart.sh`

*This single command validates prerequisites and sets up the entire environment.*

**Optional:** Validate prerequisites only:
```bash
core/scripts/automation/quickstart.sh --validate-only
```

---

### 📂 Quick Links

* [**Quickstart**](./docs/QUICKSTART.md) — Prerequisites and automation.
* [**Architecture**](./docs/OVERVIEW.md) — Deep dive into the escalation logic.
* [**Skills Guide**](./docs/AGENTIC-AI-SKILLS-GUIDE.md) — Catalog of 98 autonomous capabilities.
* [**Safety Rules**](./docs/CRITICAL-SAFETY-RULES-BEST-PRACTICES.md) — Operational best practices.

---

### ⚙️ Sample Escalation Loop

1.  **Observe:** Stateless controllers (Flux/Crossplane) flag a persistent or non-deterministic error.
2.  **Recall:** ARE queries **SQLite** for historical context and successful manual or agentic interventions.
3.  **Select:** Qwen summarizes the failure against **AGENTS.md** policies and selects a specialized **SKILL.md**.
4.  **Execute:** **Temporal** runs a durable, multi-step workflow to resolve the "out-of-bounds" issue.
5.  **Commit:** Result is logged to SQLite, informing both the Agent and future stateless telemetry.

---

### Sample's Integration Points & Implementation Details

**Event Flow Requirements:**
- **Prometheus Configuration:** Alert rules must target controller-specific metrics (reconcile failures, resource drift)
- **Argo Events Setup:** Sensors need proper RBAC and network access to memory agent endpoints
- **Memory Agent API:** REST endpoints for event ingestion, context queries, and result storage
- **Temporal Integration:** Workflow templates for common remediation patterns

**Data Flow Gaps & Solutions:**
- **Alert Enrichment:** Prometheus rules are configured with custom labels extracting controller context from Kubernetes annotations and resource specs. Alert payloads include resource namespace, kind, name, and failure reason via kube-state-metrics.
- **Event Correlation:** Argo Events uses sensor grouping and deduplication rules based on resource identifiers (namespace/name) and failure types. Related alerts within a 5-minute window trigger a single correlated event.
- **State Synchronization:** Memory agents subscribe to controller status via Kubernetes API watch streams, maintaining real-time views through continuous updates from Flux/Crossplane status conditions.
- **Rollback Handling:** Failed workflows automatically revert changes using GitOps rollback mechanisms (Flux/ArgoCD sync to previous commit). Failed remediations log incidents to SQLite with rollback actions taken.

**Skill Invocation Mechanism:**
Skills are invoked via Temporal activities that load SKILL.md instructions at runtime. Qwen LLM parses the skill body, generates execution parameters, and Temporal orchestrates the multi-step plan with GitOps validation gates.

**SQLite Memory Population:**
Initial data comes from historical logs and manual incident records imported via bulk CSV/JSON scripts. Continuous updates occur through workflow completion hooks that store outcomes, patterns, and effectiveness metrics in structured tables.

**Argo Events Communication Protocol:**
Sensors send HTTP POST requests to memory agent `/api/events` endpoint with JSON payloads containing alert metadata, resource context, and correlation IDs. Responses include workflow initiation confirmations and status updates.

---

### ⚖️ License

**AGPL-3.0-or-later** — [Full License](LICENSE)
