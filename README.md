# Agentic Reconciliation Engine (ARE)

<img width="180" height="180" alt="ARE Logo" src="https://github.com/user-attachments/assets/122d93a7-60d4-4ada-9b2e-e29bdd5e4202" />

**ARE** is a sandbox that provides agentic AI memory and reasoning for challenges beyond stateless reconciliation. Combines AGENTS.md, SKILL.md, SQLite, Qwen, llama.cpp, Temporal with Crossplane, Flux, Kubernetes.

Combines [SKILL.md](https://agentskills.io/), [AGENTS.md](https://agents.md/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [llama.cpp](https://github.com/ggml-org/llama.cpp), [SQLite](https://sqlite.org/), [Temporal](https://temporal.io/) with [Argo](https://argoproj.github.io/), [Flux](https://fluxcd.io/), [Crossplane](https://www.crossplane.io/), [Kubernetes](https://kubernetes.io/).

---

### 🏗️ Separation of Concerns

* **Agentic AI Layer (A):** [SKILL.md](https://agentskills.io/), [AGENTS.md](https://agents.md/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [llama.cpp](https://github.com/ggml-org/llama.cpp), [SQLite](https://sqlite.org/), [Temporal](https://temporal.io/): Complex actions that stateless controllers cannot reconcile.
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

### ARE Abstraction Layers

| Layer | Component | Role |
| :--- | :--- | :--- |
| 10 | [SKILL.md](https://agentskills.io/) | Instructions, Scripts, and Resources |
| 9 | [AGENTS.md](https://agents.md/) | Context and Instructions |
| 8 | [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765) | Reasoning Logic |
| 7 | [llama.cpp](https://github.com/ggml-org/llama.cpp) | Inference Runtime |
| 6 | [SQLite](https://sqlite.org/) | Agentic Memory |
| 5 | [Temporal](https://temporal.io/) | Durable Execution |
| 4 | [Argo](https://argoproj.github.io/) | Event-based Dependency Management |
| 3 | [Flux](https://fluxcd.io/) | Continuous and Progressive Delivery |
| 2 | [Crossplane](https://www.crossplane.io/) | Control Planes |
| 1 | [Kubernetes](https://kubernetes.io/) | Container Orchestration |

---

### The Reconciliation Loop

#### The Request Path
1. **Skill (10):** Defines provision_ha_database via Resource schemas and Scripts.
2. **Agent (9):** Receives Traffic spike alert; invokes the Skill based on Instruction set.
3. **Logic & Runtime (8-7):** Qwen (8) plans specs; llama.cpp (7) executes the inference.
4. **Memory (6):** SQLite persists the intent: Agent initiated HA database upgrade.
5. **Durable Execution (5):** Temporal manages the long-running commit and retry logic.
6. **Dependency & Delivery (4-3):** Argo (4) clears event dependencies; Flux (3) syncs YAML to cluster.
7. **Control Planes (2):** Crossplane reconciles the CompositeDatabase against external APIs.
8. **Orchestration (1):** Kubernetes hosts the controllers and maintains connection secrets.

#### Self-Healing Loop
* **Detection:** Layer 2 (Crossplane) identifies drift if the database is manually deleted.
* **Authority:** Layer 3 (Flux) provides the desired state from Git.
* **Action:** Layer 2 re-provisions the resource to match the Agent’s (9) original intent.

#### Telemetry Feedback Loop
* **Observation:** Layer 2 (Crossplane) emits an event once the resource reaches a Ready state.
* **Capture:** Layer 4 (Argo) captures the event and signals the completion of the delivery.
* **Storage:** Layer 6 (SQLite) updates the entry to Success, providing the Agent (9) with verified history for future reasoning.


---

### ⚖️ License

**AGPL-3.0-or-later** — [Full License](LICENSE)
