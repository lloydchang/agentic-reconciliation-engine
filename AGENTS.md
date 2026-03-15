// File: AGENTS.md

# AGENTS.md - World-Class AI Agent Specification (Temporal + GitOps)

## Preface

This document defines a **world-class AI agent framework** for multi-cloud, multi-tenant environments. It is designed to be unambiguous, fully machine-readable, and conform to [https://agentskills.io/home](https://agentskills.io/home) specifications. The framework **combines two distinct layers**: Temporal-based workflow orchestration and GitOps/Control-Plane execution.

### Purpose of Dual Layers

1. **Temporal AI Layer (Workflow Orchestration)**

   * Temporal is a **workflow orchestration engine**. It sequences, retries, and persists tasks but does not directly modify infrastructure.
   * AI agents execute **skills** within Temporal workflows. Temporal handles **state management, execution order, retries, and logging**.
   * Suitable for general cloud operations, multi-step workflows, and human-gated orchestration.

2. **GitOps/Control-Plane Layer (Infrastructure Execution)**

   * GitOps agents are **specialized execution layers** for Kubernetes clusters, CI/CD, Terraform/Helm, secrets, certificates, and multi-cloud provisioning.
   * Invoked **only when infrastructure changes are required**, either automatically via Temporal workflows or manually by human-gated decisions.
   * Provides **auditability, idempotency, and compliance** in infrastructure actions.

**Rationale:** Temporal handles orchestration and workflow logic, while GitOps handles real-world, state-changing infrastructure operations. Separating these ensures **clear responsibilities, safer execution, and auditable processes**.

---

## Table of Contents

1. AI Agent Overview
2. Temporal Workflow Layer

   * Core Principles
   * Repository Structure
   * Agent Behavior Rules
   * Skill System & Interfaces
   * Monitoring, Observability & Compliance
   * Operational Protocols & Human Gates
   * Example Temporal Workflows
3. GitOps/Control-Plane Layer

   * Purpose & Scope
   * Infrastructure-Specific Workflows
   * Integration with Temporal
   * Monitoring & Logging
   * Example GitOps Workflows
4. SKILL.md Specification and Examples

   * Required Fields
   * JSON/YAML Format
   * Accompanying Files
   * Example Skills
5. Integration Guidelines
6. Testing, Validation & Troubleshooting
7. Appendices

   * A: Skill Index Mapping
   * B: Environment Variables & Configurations
   * C: Human Gate Reference Table
   * D: Composite Workflows

---

## 1. AI Agent Overview

* The **AI Agent** is a software entity that executes skills in response to Temporal workflows.
* Skills can be **general-purpose (Temporal)** or **infrastructure-specific (GitOps)**.
* Agents **first evaluate the request** to determine which layer(s) apply:

  * Temporal layer for workflow orchestration and general tasks.
  * GitOps layer for state-changing, infrastructure-specific tasks.
* Human gates are enforced at both layers for destructive, high-impact, or compliance-critical operations.

---

## 2. Temporal Workflow Layer

### Core Principles

* **Temporal = workflow orchestration only**. No direct infrastructure changes.
* Safety, idempotency, auditability, human oversight.
* Multi-skill orchestration for general cloud operations.
* Structured logging, metrics, and monitoring.
* Human-gated execution for high-risk operations.

### Repository Structure

```
repo/
├── .agents/
├── ai-agents/
├── backend/          # Temporal workflows and activities (Go, Rust, or Python)
├── frontend/         # Dashboard & WebMCP client
├── cli/              # CLI interface
├── docs/             # Documentation & interface specs
├── SKILL.md          # Skill definitions (follows agentskills.io specs)
├── AGENTS.md         # This agent specification file
├── tools/            # Tool permissions & configurations
└── gitops/           # GitOps/Control-Plane workflows
```

### Agent Behavior Rules

* Temporal layer executes **general-purpose workflows**.
* Validate inputs, maintain state, follow structured error handling.
* Invoke GitOps/Control-Plane layer **only when infrastructure changes are required**.
* Enforce **human gates** consistently.

### Skill System & Interfaces

* Skills must conform to [https://agentskills.io/home](https://agentskills.io/home) specifications.
* Each skill must include:

  * Name, description, version
  * Input parameters with types
  * Output schema
  * Side effects
  * Human-gate flag (if required)
* Skills may have **accompanying files**, each documented with purpose, format, and usage.

### Monitoring, Observability & Compliance

* Temporal logs must include execution time, success/failure, workflow ID.
* Metrics collected for retries, failures, resource usage.
* All actions auditable; integrates with compliance dashboards.

### Operational Protocols & Human Gates

* **Human gates**: explicit confirmation required for destructive or high-impact actions.
* Gate applies across both layers.
* Standardized confirmation format (JSON/YAML) ensures machine readability.

### Example Temporal Workflow

* Workflow: Tenant Onboarding

  1. Validate request input
  2. Execute pre-checks (general cloud validations)
  3. Trigger GitOps workflow if infrastructure provisioning is needed
  4. Log all actions, human confirmations, and output results

---

## 3. GitOps/Control-Plane Layer

### Purpose & Scope

* Executes **real infrastructure changes**.
* Supports Kubernetes, Terraform, Helm, secrets management, and multi-cloud orchestration.
* Invoked by Temporal workflows **or manually via human gates**.

### Example GitOps Workflows

* Cluster provisioning, upgrades, scaling
* ArgoCD/Flux sync, ApplicationSet reconciliation
* Terraform apply/destroy
* Secrets & certificate rotation
* Canary releases, blue-green deployments

### Integration with Temporal

* GitOps actions are **wrapped in Temporal workflows** for auditability and retries.
* Temporal AI decides when to invoke GitOps layer based on task type, risk, and human-gate status.

### Monitoring & Logging

* GitOps metrics include sync status, drift detection, deployment success/failure.
* Logs integrated into Temporal dashboards for unified monitoring.

---

## 4. SKILL.md Specification and Examples

* Must follow [https://agentskills.io/home](https://agentskills.io/home) standards.
* Example structure (YAML/JSON):

```
name: provision-k8s-cluster
version: 1.0.0
description: Creates a new Kubernetes cluster in specified cloud provider
inputs:
  region: string
  cluster_size: integer
outputs:
  cluster_id: string
  endpoint: string
side_effects:
  - Creates cloud resources
human_gate: true
accompanying_files:
  - terraform/main.tf
  - terraform/variables.tf
  - README.md  # Explains Terraform variables, usage, and required credentials
```

* **Accompanying files** must clearly document purpose, dependencies, and usage.
* All skills **explicitly declare side effects** and human-gate requirements.
* LLMs and AI agents can interpret skills and workflows **without ambiguity**.

---

## 5. Integration Guidelines

* Always use **API keys and environment variables** consistently.
* Skill chaining: Temporal workflow first, GitOps layer second if infrastructure action is required.
* Human gates evaluated **at every layer**.

## 6. Testing, Validation & Troubleshooting

* Test Temporal workflows with **mock environments**.
* Test GitOps workflows in **staging clusters** first.
* Structured error handling, retries, and composite workflow logging.

## 7. Appendices

### A: Skill Index Mapping

* Maps Temporal skills to GitOps-specific skills.
* Explicitly defines **default execution layer**.

### B: Environment Variables & Configurations

* Cloud credentials, ArgoCD/Flux endpoints, monitoring integrations.

### C: Human Gate Reference Table

* Lists all operations requiring explicit confirmation.
* Separated by Temporal and GitOps layers.

### D: Composite Workflows

* Example: Tenant onboarding with infrastructure provisioning.
* Temporal orchestrates multi-step workflow; GitOps executes infra changes.

---

**Summary:** This agent framework uses **precise terminology** and **dual-layer separation**:

* Temporal: workflow orchestration and general-purpose cloud tasks.
* GitOps: infrastructure execution.
* Skills (SKILL.md) fully follow [https://agentskills.io/home](https://agentskills.io/home) specifications, including input/output, side effects, human gates, and accompanying files.
* No ambiguity exists; all AI agents can interpret workflows and skills consistently.
