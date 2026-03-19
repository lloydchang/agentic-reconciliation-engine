# Agentic Reconciliation Engine (ARE)

<img width="180" height="180" alt="ARE Logo" src="https://github.com/user-attachments/assets/122d93a7-60d4-4ada-9b2e-e29bdd5e4202" />

**ARE** is a sandbox that provides agentic AI memory and reasoning for challenges beyond stateless reconciliation. Combines AGENTS.md, SKILL.md, SQLite, Qwen, Temporal with Crossplane, Flux, Kubernetes.

Combines [AGENTS.md](https://agents.md/), [SKILL.md](https://agentskills.io/), [SQLite](https://sqlite.org/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [Temporal](https://temporal.io/) with [Crossplane](https://www.crossplane.io/), [Flux](https://fluxcd.io/), [Kubernetes](https://kubernetes.io/).

---

### 🏗️ Separation of Concerns

* **Agentic AI Layer (A):** [AGENTS.md](https://agents.md/), [SKILL.md](https://agentskills.io/), [SQLite](https://sqlite.org/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [Temporal](https://temporal.io/): Complex actions that stateless controllers cannot reconcile.
* **Reconciliation Engine (RE):** [Crossplane](https://www.crossplane.io/), [Flux](https://fluxcd.io/), [Kubernetes](https://kubernetes.io/): Standard resource lifecycle, cross-provider orchestration, drift detection, and mechanical synchronization.

---

### ⚙️ Sample Escalation Loop

1.  **Observe:** Stateless controllers (Flux/Crossplane) flag a persistent or non-deterministic error.
2.  **Recall:** ARE queries **SQLite** for historical context and successful manual or agentic interventions.
3.  **Select:** Qwen summarizes the failure against **AGENTS.md** policies and selects a specialized **SKILL.md**.
4.  **Execute:** **Temporal** runs a durable, multi-step workflow to resolve the "out-of-bounds" issue.
5.  **Commit:** Result is logged to SQLite, informing both the Agent and future stateless telemetry.

---

### 📂 Quick Links

* [**Quickstart**](./docs/QUICKSTART.md) — Prerequisites and automation.
* [**Architecture**](./docs/OVERVIEW.md) — Deep dive into the escalation logic.
* [**Skills Guide**](./docs/AGENTIC-AI-SKILLS-GUIDE.md) — Catalog of 98 autonomous capabilities.
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
