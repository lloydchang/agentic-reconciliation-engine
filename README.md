# Agentic Reconciliation Engine (ARE)

<img width="312" height="180" alt="logo.png" src="https://github.com/user-attachments/assets/36fb6c86-e84a-49c1-bf12-5e25e6fa10ab" />

**ARE** is a sandbox that provides agentic AI memory and reasoning for challenges beyond stateless reconciliation. Combines AGENTS.md, SKILL.md, SQLite, Qwen, llama.cpp, Temporal with Crossplane, Flux, Kubernetes.

Combines [SKILL.md](https://agentskills.io/), [AGENTS.md](https://agents.md/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [llama.cpp](https://github.com/ggml-org/llama.cpp), [SQLite](https://sqlite.org/), [Temporal](https://temporal.io/) with [Argo](https://argoproj.github.io/), [Flux](https://fluxcd.io/), [Crossplane](https://www.crossplane.io/), [Kubernetes](https://kubernetes.io/).

---

### Separation of Concerns

* **Agentic AI Layer (A):** [SKILL.md](https://agentskills.io/), [AGENTS.md](https://agents.md/), [Qwen](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765), [llama.cpp](https://github.com/ggml-org/llama.cpp), [SQLite](https://sqlite.org/), [Temporal](https://temporal.io/): Complex actions that stateless controllers cannot reconcile.
* **Reconciliation Engine (RE):** [Argo](https://argoproj.github.io/), [Flux](https://fluxcd.io/), [Crossplane](https://www.crossplane.io/), [Kubernetes](https://kubernetes.io/): Standard resource lifecycle, drift detection, cross-provider orchestration, and mechanical synchronization.

---

### Getting Started

Choose the appropriate quickstart script for your environment:

#### Local Development
- **Kind**: `./core/scripts/automation/quickstart-local-kind.sh`
- **Docker Desktop**: `./core/scripts/automation/quickstart-local-docker-desktop.sh`
- **Minikube**: `./core/scripts/automation/quickstart-local-minikube.sh`

#### Cloud Service Emulators
- **LocalStack AWS**: `./core/scripts/automation/quickstart-local-localstack-aws.sh`
- **Azurite + LocalStack Azure**: `./core/scripts/automation/quickstart-local-azurite-and-localstack-azure.sh`
- **Google Cloud Emulator**: `./core/scripts/automation/quickstart-local-gcloud-emulator.sh`

#### Production Deployments
- **AWS EKS**: `./core/scripts/automation/quickstart-remote-aws.sh`
- **Azure AKS**: `./core/scripts/automation/quickstart-remote-azure.sh`
- **Google Cloud GKE**: `./core/scripts/automation/quickstart-remote-gcp.sh`
- **On-Premises**: `./core/scripts/automation/quickstart-remote-on-prem.sh`

#### Overlay Extensions
Each environment has an overlay version (e.g., `overlay-quickstart-local-kind.sh`) that adds enhanced features without modifying the base scripts.

**Example**: `./core/scripts/automation/quickstart-local-kind.sh`

---

### Quick Links

* [**Quickstart**](./docs/QUICKSTART.md) — Prerequisites and automation.
* [**Architecture**](./docs/OVERVIEW.md) — Deep dive into the escalation logic.
* [**Skills Guide**](./docs/AGENTIC-AI-SKILLS-GUIDE.md) — Catalog of 98 autonomous capabilities.
* [**Safety Rules**](./docs/CRITICAL-SAFETY-RULES-BEST-PRACTICES.md) — Operational best practices.

---

### Abstraction Layers

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

### Example

#### Request Path
1. **Skill (10):** Defines `provision_ha_database` via Resource schemas and Scripts.
2. **Agent (9):** Receives _Traffic Spike_ alert; invokes the Skill (10) based on Instruction set.
3. **Logic & Runtime (8-7):** Qwen (8) reasons; llama.cpp (7) inferences.
4. **Memory (6):** SQLite (6) persists the intent: Agent (9) initiated HA database upgrade.
5. **Durable Execution (5):** Temporal (5) manages the long-running commit and retry logic.
6. **Dependency & Delivery (4-3):** Argo (4) clears event dependencies; Flux (3) syncs YAML to cluster.
7. **Control Planes (2):** Crossplane (2) reconciles the CompositeDatabase against external APIs.
8. **Orchestration (1):** Kubernetes (1) hosts the controllers and maintains connection secrets.

#### Self-Healing Loop
* **Detection:** Crossplane (2) identifies drift if the database is manually deleted.
* **Authority:** Flux (3) provides the desired state from Git.
* **Action:** Crossplane (2) re-provisions the resource to match the Agent’s (9) original intent.

#### Telemetry Feedback Loop
* **Observation:** Crossplane (2) emits an event once the resource reaches a _Ready_ state.
* **Capture:** Argo (4) captures the event and signals the completion of the delivery.
* **Storage:** SQLite (6) updates the entry to _Success_, providing the Agent (9) with verified history for future reasoning.


---

### License

[AGPL-3.0-or-later](LICENSE)
