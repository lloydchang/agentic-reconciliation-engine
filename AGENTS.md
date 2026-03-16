# GitOps Infra Control Plane Agents

## Preface

This document defines an **agent architecture** that integrates LLM-driven orchestration with GitOps-controlled infrastructure operations. It ensures clarity, precision, and unambiguous instructions following open standard specifications at https://agentskills.io/specification web page.

Two complementary layers coexist:

1. **Temporal Agents**: General-purpose workflow orchestration, multi-cloud, multi-tenant operations. Determines *what* actions are required.
2. **GitOps/Control-Plane Agents**: Deterministic executor of LLM-generated structured plans. Ensures safe infrastructure changes via GitOps pipelines and Kubernetes reconciliation loops.

**Key Principle:** LLM decides *what*, system decides *how*. This is called **tool-constrained or structured tool agents**.

---

## Table of Contents

1. Cloud Agent Overview
2. Temporal Agent System
3. GitOps Control Plane Agents (Appendix A)
4. Autonomy, PR Gating, and Risk Levels
5. Integration Guidelines
6. Testing, Validation & Troubleshooting
7. Appendices
   * A: Skill Index Mapping (Temporal vs GitOps-specific)
   * B: Environment Variables & Configurations
   * C: Human Gate Reference Table
   * D: Composite Workflows & Autonomy Rules
## Repository Structure
```
repo/
├── .agents/                    # Agent skill definitions (agentskills.io compliant)
│   └── [skill_name]/
│       ├── SKILL.md          # Skill definition with YAML frontmatter
│       ├── scripts/          # Optional executable code
│       ├── references/       # Optional documentation
│       └── assets/           # Optional templates/resources
├── AGENTS.md                  # This file - agent operating rules
├── agents/                    # Agent runtime implementation
│   ├── backend/              # Go Temporal workflows and activities
│   ├── dashboard/            # React dashboard and WebMCP client
│   ├── cli/                  # Command-line interface
│   └── tools/                # Tool permissions and configurations
├── docs/                     # Documentation and interface specs
├── scripts/                  # Utility scripts for validation and fixes
└── gitops/                   # GitOps/Control-Plane workflows
```

### Skills Directory
The `.agents/` directory contains individual skill definitions that follow the [agentskills.io specification](https://agentskills.io/specification):

- Each skill has a `SKILL.md` file with YAML frontmatter containing `name`, `description`, and optional fields
- Skills define specific capabilities like `cost-optimizer`, `alert-prioritizer`, `cluster-health-check`
- Agents discover and load skills based on task requirements and skill descriptions
- All 72 skills have been validated to comply with the specification

---

## 1. Agent Overview

Agents automate cloud workflows while preserving safety:

* Temporal layer decides *what* actions are needed and composes workflows.
* GitOps/Control-Plane layer executes changes deterministically.
* Risk-based gating controls which actions are fully autonomous vs PR-gated.
* Skills define structured outputs, parameters, and error handling.

---

## 2. Temporal Agent System

### Core Principles

* Multi-skill orchestration for general cloud operations
* Safety, auditability, human oversight, idempotency
* Structured output, logging, and monitoring
* Risk-level assessment and human gating

### Agent Behavior Rules

* Temporal orchestrates multi-step workflows and decides action sequences.
* GitOps layer executes structured plans deterministically.
* Skills define autonomy level, risk, and human gate requirements.

### Example Workflow: Cost Optimization
1. **Temporal** receives request: "Optimize costs for production environment"
2. **Skill Discovery**: Agent identifies `cost-optimizer` skill based on description
3. **Plan Generation**: Agent creates structured plan using skill's input schema
4. **Risk Assessment**: Plan marked as `medium` risk, `conditional` autonomy
5. **GitOps Execution**: Plan executed via Flux or Argo CD with human approval gate
6. **Results**: Cost savings report generated and monitored

### Skill System & Interfaces

* `.agents/[skill]/SKILL.md` defines the skill:

  * **action_name**: unique identifier
  * **risk_level**: low / medium / high
  * **autonomy**: fully_auto / conditional / requires_PR
  * **input_schema** and **output_schema**: JSON schemas
  * **human_gate**: optional explanation of required approvals
* Skills may include additional files in the skill directory (scripts, templates).
* Composite workflows combine multiple skills, potentially across both layers.

### Monitoring, Observability & Compliance

* Track execution times, success rates, resource usage.
* Unified logs from Temporal and GitOps layers.
* Risk and human gate auditing.

### Operational Protocols & Human Gates

* Low-risk actions may run fully automated.
* Medium/high-risk actions are PR-gated, requiring explicit human approval.
* Standardized confirmation and audit trail for all human-gated operations.

### Workflows & Automation

* Temporal workflows orchestrate general cloud operations.
* GitOps workflows execute infrastructure changes via validated pipelines (Flux, Argo CD).
* LLM output is never executed directly on clusters; only through structured plans.

---

## 3. GitOps Control Plane Agents (Appendix A)

### Purpose & Scope

* Manage clusters, multi-cloud deployments, infrastructure provisioning.
* Execute **structured plans** generated by Temporal.
* Reconciliation ensures system-level safety even if automation misfires.

### Key Workflows

* Cluster Management: provision, upgrade, scale, troubleshoot nodes
* GitOps Synchronization: PR validation, Flux and Argo CD reconciliation
* Deployment Validation: smoke tests, canary, blue-green
* Secrets & Certificates: rotation and management
* Multi-Cloud Orchestration: region-specific deployments, networking

### Monitoring & Logging

* GitOps-specific metrics (sync status, drift detection, deployment success/failure)
* Integration into unified Temporal monitoring dashboards

---

## 4. Autonomy, PR Gating, and Risk Levels

| Risk Level | Autonomy Options | Description                                                                    |
| ---------- | ---------------- | ------------------------------------------------------------------------------ |
| Low        | fully_auto       | LLM generates plan, GitOps executes without PR. Safe for dev or test clusters. |
| Medium     | conditional      | LLM generates plan, PR created; human may approve or skip if policy allows.    |
| High       | requires_PR      | LLM generates plan; all actions require human approval before execution.       |

**Structured Action Example:**

```
action: get_pod_logs
namespace: payments
pod: api-123
risk_level: low
autonomy: fully_auto
```

**High-Risk Example:**

```
action: rotate_tls_certificates
namespace: production
risk_level: high
autonomy: requires_PR
```

* Even fully_auto tasks go through GitOps pipeline for validation and reconciliation.
* Kubernetes reconciliation loops automatically revert invalid changes.

---

## 5. Integration Guidelines

* LLM outputs **structured JSON plans**, never shell commands.
* GitOps pipelines validate and apply changes deterministically.
* Skills define risk and gating clearly in `.agents/[skill]/SKILL.md`.
* Human gates enforced at both Temporal orchestration and GitOps layers where specified.

---

## 6. Testing, Validation & Troubleshooting

* Temporal workflows: unit tests, mock cloud environments.
* GitOps workflows: staging clusters, PR validation, rollback scenarios.
* Continuous monitoring for errors, retries, and workflow consistency.

---

## 7. Appendices

### A: Skill Index Mapping

| Skill Category | Example Skills | Default Layer | Autonomy |
| -------------- | -------------- | ------------- | -------- |
| **Cost Management** | cost-optimizer, capacity-planning | Temporal | conditional |
| **Monitoring** | alert-prioritizer, cluster-health-check | Temporal | conditional |
| **Security** | compliance-scanner, security-analysis | GitOps | requires_PR |
| **Deployment** | deployment-strategy, gitops-workflow | GitOps | conditional |
| **Database** | database-maintenance, database-operations | GitOps | conditional |

### B: Environment Variables & Configurations

```bash
# Cloud Provider Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AZURE_CLIENT_ID=your_client_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# GitOps Endpoints
ARGO_CD_SERVER=https://argocd.example.com
FLUX_GIT_REPO=git@example.com:example/gitops-infra-control-plane.git

# GitOps Configuration
GITOPS_TOOL=flux # or argo_cd
GITOPS_NAMESPACE=gitops-system

# Monitoring Integration
PROMETHEUS_URL=https://prometheus.example.com
GRAFANA_API_KEY=your_grafana_key
```

### C: Human Gate Reference Table

| Operation Type | Risk Level | Human Gate Required | Approval Method |
| -------------- | ---------- | ------------------ | -------------- |
| **Read Operations** | Low | No | N/A |
| **Dev/Test Changes** | Low | No | N/A |
| **Production Scaling** | Medium | Yes | PR approval |
| **Security Changes** | High | Yes | PR + security review |
| **Database Changes** | High | Yes | PR + DBA review |
| **Network Changes** | High | Yes | PR + network review |
| **Cost Optimization** | Medium | Conditional | Auto-approve < $100/day |

### D: Composite Workflows & Autonomy Rules

#### Example: Tenant Onboarding Workflow
```yaml
workflow: tenant-onboarding
steps:
  1. create-infrastructure:
     skill: infrastructure-provisioning
     risk: medium
     autonomy: conditional
  2. setup-monitoring:
     skill: observability-stack
     risk: low
     autonomy: fully_auto
  3. configure-security:
     skill: security-analysis
     risk: high
     autonomy: requires_PR
  4. deploy-applications:
     skill: deployment-strategy
     risk: medium
     autonomy: conditional
```

#### Autonomy Rules Matrix
| Layer | Low Risk | Medium Risk | High Risk |
| ----- | -------- | ----------- | --------- |
| **Temporal** | fully_auto | conditional | requires_PR |
| **GitOps** | fully_auto | conditional | requires_PR |
| **Combined** | fully_auto | conditional | requires_PR |

---

**Summary:**

* Architecture is **tool-constrained / structured tool agent** pattern.
* LLM decides *what*, deterministic system decides *how*.
* Autonomy is explicitly defined per skill and risk level.
* GitOps and Kubernetes reconciliation provide safety net for fully automated actions.
* Document and skills follow open standard specifications at https://agentskills.io/specification web page.
