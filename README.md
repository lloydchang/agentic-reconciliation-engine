# Agentic Reconciliation Engine (ARE)

<img width="180" height="180" alt="ARE Logo" src="https://github.com/user-attachments/assets/122d93a7-60d4-4ada-9b2e-e29bdd5e4202" />

**ARE** is an experimental sandbox that provides a reasoning and execution layer for infrastructure challenges that exceed the scope of stateless reconciliation.

Combines [Kubernetes](https://kubernetes.io/), [Crossplane](https://www.crossplane.io/), [Flux](https://fluxcd.io/) with [Temporal](https://temporal.io/), [SQLite](https://sqlite.org/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [AGENTS.md](https://agents.md/), [SKILL.md](https://agentskills.io/).

---

### 🏗️ Separation of Concerns

* **Agentic Layer (A):** [Temporal](https://temporal.io/), [SQLite](https://sqlite.org/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [AGENTS.md](https://agents.md/), [SKILL.md](https://agentskills.io/): Complex actions that stateless controllers cannot own.
* **Reconciliation Engine (RE):** [Kubernetes](https://kubernetes.io/), [Crossplane](https://www.crossplane.io/), [Flux](https://fluxcd.io/): Standard resource lifecycle, cross-provider orchestration, drift detection, and mechanical synchronization.

---

### ⚙️ The Escalation Loop

1.  **Observe:** Stateless controllers (Flux/Crossplane) flag a persistent or non-deterministic error.
2.  **Recall:** ARE queries **SQLite** for historical context and successful manual or agentic interventions.
3.  **Select:** Agent evaluates the failure against **AGENTS.md** policies and selects a specialized **SKILL.md**.
4.  **Execute:** **Temporal** runs a durable, multi-step workflow to resolve the "out-of-bounds" issue.
5.  **Commit:** Result is logged to SQLite, informing both the Agent and future stateless telemetry.

---

### 📂 Quick Links

* [**Quickstart**](./docs/QUICKSTART.md) — Prerequisites and automation.
* [**Architecture**](./docs/OVERVIEW.md) — Deep dive into the escalation logic.
* [**Skills Guide**](./docs/AGENTIC-AI-SKILLS-GUIDE.md) — Catalog of 70+ autonomous capabilities.
* [**Safety Rules**](./docs/CRITICAL-SAFETY-RULES-BEST-PRACTICES.md) — Operational best practices.

---

### 🛠️ Getting Started

1.  **Prerequisites:** Run `core/scripts/automation/prerequisites.sh`.
2.  **Initialize:** Run `core/scripts/automation/run-local-automation.sh`.

---

### ⚖️ License

**AGPL-3.0-or-later** — [Full License](LICENSE)
