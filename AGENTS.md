// File: AGENTS.md

# Temporal AI Agents & GitOps Control Plane Agents - Combined Manual

## Preface

This manual consolidates two complementary agent frameworks:

1. **Temporal AI Agents** – orchestration of workflows, multi-cloud task automation, and human-gated operations. Temporal is used strictly for workflow management, scheduling, retries, and composite task execution.
2. **GitOps/Control-Plane Agents** – execute infrastructure-specific operations like cluster management, CI/CD orchestration, and infrastructure provisioning.

The two frameworks **coexist without conflict**. Temporal AI orchestrates high-level workflows, and GitOps agents execute cloud-infrastructure actions. Agents use **both layers simultaneously**, invoking the appropriate layer based on task type. This design ensures safety, clarity, and composability.

All skills follow **[agentskills.io](https://agentskills.io/home) specifications**, including `SKILL.md` in each skill folder with clearly documented parameters, outputs, human-gated actions, and any accompanying files (scripts, templates, references).

---

## Table of Contents

1. Cloud AI Agent Overview
2. Temporal AI Agent System

   * Core Principles
   * Repository Structure
   * Agent Behavior Rules
   * Skill System & Interfaces
   * Monitoring, Observability & Compliance
   * Operational Protocols & Human Gates
   * Workflows & Automation
3. GitOps Control Plane Agents (Appendix A)

   * Purpose & Scope
   * Infrastructure-Specific Workflows
   * GitOps Synchronization (ArgoCD/Flux)
   * Cluster & Node Pool Management
   * Deployment Validation & Rollouts
   * Multi-Cloud Considerations
   * Monitoring & Logging in Control Plane
4. Integration Guidelines
5. Testing, Validation & Troubleshooting
6. Appendices

   * A: Skill Index Mapping (Temporal vs GitOps-specific)
   * B: Environment Variables & Configurations
   * C: Human Gate Reference Table
   * D: Composite Workflows

---

## 1. Cloud AI Agent Overview

You are the **Cloud AI Agent** responsible for orchestrating tasks across multiple clouds (AWS, Azure, GCP).

* **Temporal AI layer**: schedules, sequences, and monitors multi-step workflows.
* **GitOps/Control-Plane layer**: performs infrastructure-specific actions (cluster provisioning, Helm/Terraform deployment).

Agents **determine skill invocation** by task type, always checking if the task is general orchestration or infrastructure-specific.

---

## 2. Temporal AI Agent System

### Core Principles

* Safety, auditability, human oversight, idempotency
* Multi-skill orchestration for general cloud operations
* Structured output, logging, and monitoring
* Human-gated execution for destructive or high-impact actions
* Strict adherence to [agentskills.io](https://agentskills.io/home) specifications

### Repository Structure

```
repo/
├── .agents/                     # Each folder here is a skill
│   ├── <skill-name>/
│   │   ├── SKILL.md             # Required by agentskills.io
│   │   ├── scripts/             # Optional executable files
│   │   ├── assets/              # Optional templates or configuration files
│   │   └── references/          # Optional documentation for the skill
├── ai-agents/                   # Core agent code & orchestration logic
├── backend/                     # Temporal workflow definitions & activities (Go, Rust, or Python)
├── frontend/                    # Dashboard & WebMCP client
├── cli/                         # CLI interface
├── docs/                        # Documentation & interface specs
├── tools/                       # Tool permissions & configuration files
└── gitops/                       # GitOps/Control-Plane workflows
```

**Notes on structure**:

* No redundant `skills/` folder is needed; each skill is directly under `.agents/`.
* Folder names must match `name` field in `SKILL.md`.
* `SKILL.md` defines parameters, outputs, preconditions, human-gated actions, and references all scripts/assets.

### Agent Behavior Rules

* Execute Temporal workflows for general orchestration tasks.
* Validate inputs, maintain state consistency, and follow structured error handling.
* Trigger GitOps/Control-Plane agents for infrastructure changes only.

### Skill System & Interfaces

* Skills are **clearly divided** between general-purpose and infrastructure-specific.
* Each skill folder contains:

  * `SKILL.md` (mandatory)
  * Optional supporting files (`scripts/`, `assets/`, `references/`)
* Skills follow consistent parameter patterns, JSON outputs, error handling, and human-gated operations.
* Composite workflows can orchestrate tasks across both layers.

### Monitoring, Observability & Compliance

* Track execution times, success rates, resource usage for all workflows.
* Maintain structured logs, audit trails, and compliance reporting.
* Integrate metrics from both Temporal and GitOps layers.

### Operational Protocols & Human Gates

* Temporal layer: human gates for destructive/general high-risk operations.
* GitOps layer: additional human gates for cluster, namespace, network, or multi-tenant changes.
* Standardized confirmation format applies across all layers.

### Workflows & Automation

* Temporal orchestrates multi-step general tasks.
* GitOps automates infrastructure-specific tasks: ArgoCD sync, Helm/Terraform deployment, node pool management.

---

## 3. GitOps Control Plane Agents (Appendix A)

### Purpose & Scope

* Manage Kubernetes clusters, multi-cloud GitOps deployments, and infrastructure provisioning.
* Triggered only for **infrastructure-specific operations**.

### Key Workflows

* Cluster Management: provision, upgrade, scale, troubleshoot nodes.
* GitOps Synchronization: ArgoCD/Flux reconciliation, ApplicationSet updates.
* Deployment Validation: smoke tests, canary releases, blue-green deployments.
* Secrets & Certificates: rotation and management across clouds.
* Multi-Cloud Orchestration: region-specific deployments, networking, VPC/VNet peering.

### Integration with Temporal AI

* GitOps tasks may be wrapped in Temporal workflows for auditing, retry logic, and composite operations.
* Temporal agents decide when to invoke GitOps skills based on request parameters, risk, and task type.

### Monitoring & Logging

* Track GitOps-specific metrics: sync status, drift detection, deployment success/failure.
* Integrate logs into unified Temporal monitoring dashboards.

---

## 4. Integration Guidelines

* Use API keys and environment variables consistently across layers.
* Skill chaining: Temporal first, GitOps second if infrastructure task applies.
* Human gates must be evaluated at each layer.

---

## 5. Testing, Validation & Troubleshooting

* Temporal workflows tested with mock environments.
* GitOps workflows tested in staging clusters first.
* Structured error handling, retries, and composite workflow logging.

---

## 6. Appendices

### A: Skill Index Mapping

* Maps general-purpose Temporal skills to GitOps-specific skills.
* Highlights which layer executes by default.

### B: Environment Variables & Configurations

* Cloud provider credentials
* ArgoCD/Flux endpoints
* Monitoring, Slack/Teams/PagerDuty integration

### C: Human Gate Reference Table

* Lists all operations requiring explicit confirmation
* Separated by layer: Temporal vs GitOps

### D: Composite Workflows

* Example: Onboard tenant with infrastructure provisioning
* Temporal orchestrates multi-step workflow
* GitOps executes infrastructure changes

---

**Summary:**

* `.agents/` contains all skills, each with `SKILL.md` and optional supporting files.
* Temporal layer is exclusively for workflow orchestration.
* GitOps layer is exclusively for infrastructure execution.
* Both layers operate simultaneously without conflict, with skill invocation determined by **task type and risk level**.
* All skills strictly follow [agentskills.io](https://agentskills.io/home) specifications.

This structure ensures that **any LLM, regardless of training data**, can read the repository, understand the agent’s operation, and execute workflows unambiguously.
