# GitOps Infra Agents

## Preface

This document defines the **agent architecture** for this repository. It integrates LLM-driven
orchestration with GitOps-controlled infrastructure operations, ensuring clarity, precision, and
unambiguous operating rules.

Skills in this repo follow the open [agentskills.io specification](https://agentskills.io/specification).
Project-specific metadata (risk level, autonomy, layer) is stored under the standard `metadata:`
key in each `SKILL.md` frontmatter — it is not part of the agentskills.io standard itself.

**Key Principle:** LLM decides *what*, the deterministic system decides *how*. This is the
**tool-constrained / structured tool agent** pattern.

---

## Table of Contents

1. Agent Overview
2. Architecture Layers
3. Memory Agent Layer
4. Temporal Orchestration Layer
5. GitOps Control Layer
6. Skill System
7. Autonomy, PR Gating, and Risk Levels
8. Integration Guidelines
9. Testing, Validation & Troubleshooting
10. Appendices
    * A: Skill Index Mapping
    * B: Environment Variables & Configurations
    * C: Human Gate Reference Table
    * D: Composite Workflows & Autonomy Rules

---

## Repository Structure

```
gitops-infra-control-plane/
├── core/ai/
│   ├── AGENTS.md                          # This file
│   ├── skills/                            # agentskills.io-compliant skill definitions
│   │   └── [skill_name]/
│   │       ├── SKILL.md                   # Required: name, description + metadata
│   │       ├── scripts/                   # Optional: executable code
│   │       ├── references/               # Optional: documentation
│   │       └── assets/                    # Optional: templates/resources
│   └── runtime/                           # Agent runtime implementation
│       ├── backend/                       # Go Temporal workflows and activities
│       ├── dashboard/                     # React dashboard and backend API
│       ├── cli/                           # Command-line interface
│       └── tools/                         # Tool permissions and configurations
├── core/automation/ci-cd/scripts/         # Utility scripts for validation and fixes
├── docs/                                  # Architecture documentation
└── gitops/                                # GitOps/Control-Plane manifests (Flux/ArgoCD)
```

### Skills Directory

The `core/ai/skills/` directory contains skill definitions following the
[agentskills.io specification](https://agentskills.io/specification):

- Each skill directory contains a `SKILL.md` with required `name` and `description` frontmatter
- `name` must be lowercase, hyphen-separated, max 64 characters, matching the directory name
- Project-specific fields (`risk_level`, `autonomy`, `layer`, `human_gate`) live under `metadata:`
- Skills are validated with `skills-ref validate ./core/ai/skills/` in CI
- 64+ skills are currently available

**Example SKILL.md frontmatter (agentskills.io compliant):**
```yaml
---
name: cost-optimizer
description: >
  Analyses cloud spend and recommends cost reductions. Use when asked to reduce
  costs, right-size resources, or analyse billing across AWS, Azure, or GCP.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for changes > $100/day savings
---
```

---

## 1. Agent Overview

Four layers work together to automate infrastructure operations safely:

| Layer | Purpose | Decides |
|---|---|---|
| **Memory Agents** | Persistent AI state, conversation history, local inference | What context exists |
| **Temporal Orchestration** | Multi-skill workflow coordination | What actions are needed |
| **GitOps Control** | Deterministic execution of structured plans | How changes are applied |
| **Monitoring & Observability** | Metrics, logging, alerting | Whether the system is healthy |

No LLM output is ever executed directly on a cluster. All changes flow through structured
plans → GitOps pipelines → Kubernetes reconciliation.

---

## 2. Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│                  User / Operator Request                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│              Temporal Orchestration Layer                    │
│  Decides what actions are needed. Composes multi-skill       │
│  workflows. Assesses risk. Routes to GitOps or Memory Agent. │
└───────────┬──────────────────────────┬───────────────────────┘
            │                          │
            ▼                          ▼
┌───────────────────────┐  ┌───────────────────────────────────┐
│  Memory Agent Layer   │  │       GitOps Control Layer        │
│                       │  │                                   │
│  Rust / Go / Python   │  │  Executes structured JSON plans   │
│  Local inference      │  │  via Flux or ArgoCD. Never runs   │
│  (llama.cpp / Ollama) │  │  LLM output directly on cluster.  │
│  SQLite persistence   │  │                                   │
└───────────────────────┘  └───────────────────────────────────┘
            │                          │
            └──────────────┬───────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│           Monitoring & Observability Layer                   │
│     Prometheus · Grafana · ELK · Alertmanager · Dashboard    │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Memory Agent Layer

Memory Agents provide persistent AI state across sessions. They are the foundation of the
system's ability to learn from past operations and provide context-aware responses.

### Implementation

Three language implementations serve different purposes:

| Implementation | Use Case | Inference |
|---|---|---|
| **Rust** (`agent-memory-rust`) | Performance-critical, high-throughput | llama.cpp (embedded) |
| **Go** (`agent-memory-go`) | Orchestration integration, Temporal activities | llama.cpp or Ollama |
| **Python** (`agent-memory-python`) | ML/AI prototyping, model experimentation | transformers/torch |

Selection is controlled by `LANGUAGE_PRIORITY` environment variable (default: `rust,go,python`).

### Inference Backend

All inference is local by design — **no external API calls for inference**. This is a core
privacy and security principle: infrastructure data never leaves the cluster.

```
Priority: llama.cpp → Ollama (fallback)

Controlled by: BACKEND_PRIORITY=llama-cpp,ollama
```

### Persistence

Each memory agent uses SQLite with a 10Gi PVC:

| Memory Type | Description |
|---|---|
| Episodic | Conversation history across sessions |
| Semantic | Learned concepts and entity relationships |
| Procedural | Skill execution patterns and outcomes |
| Working | Current session context |

### Failure Handling

- If the primary language agent is unavailable, the system falls back through `LANGUAGE_PRIORITY`
- If llama.cpp fails, Ollama is used as the inference fallback
- Health endpoint: `GET /api/health` on each agent
- Kubernetes liveness and readiness probes are required on all memory agent deployments

---

## 4. Temporal Orchestration Layer

Temporal provides durable, auditable workflow execution across all infrastructure operations.

### Core Principles

- Multi-skill orchestration for general infrastructure operations
- Safety, auditability, human oversight, idempotency
- Structured output, logging, and monitoring
- Risk-level assessment and human gating before execution

### Agent Behavior Rules

- Temporal orchestrates multi-step workflows and decides action sequences
- All LLM outputs are **structured JSON plans**, never shell commands
- GitOps layer executes structured plans deterministically
- Skills define autonomy level, risk, and human gate requirements

### Example Workflow: Cost Optimization

1. **Request**: "Optimize costs for production environment"
2. **Skill Discovery**: Agent loads `cost-optimizer` skill based on description match
3. **Context Retrieval**: Memory agent provides historical cost patterns
4. **Plan Generation**: Structured JSON plan created from skill instructions
5. **Risk Assessment**: Plan marked `medium` risk, `conditional` autonomy
6. **Human Gate**: PR created; awaits approval
7. **GitOps Execution**: On approval, Flux/ArgoCD applies the plan
8. **Results**: Cost savings recorded; memory agent updated with outcome

### Temporal State Store

Temporal uses **Cassandra** for distributed workflow state persistence.

### Monitoring

- Execution times, success/failure rates, resource usage
- Unified logs from Temporal and GitOps layers
- Risk and human gate audit trail

---

## 5. GitOps Control Layer

### Purpose & Scope

- Executes **structured JSON plans** generated by the Temporal layer
- Never accepts free-form LLM text or shell commands as input
- All changes are PR-tracked, version-controlled, and reconciled by Flux or ArgoCD
- Kubernetes reconciliation loops automatically revert invalid changes

### Key Workflows

- Cluster Management: provision, upgrade, scale, troubleshoot nodes
- GitOps Synchronization: PR validation, Flux and ArgoCD reconciliation
- Deployment Validation: smoke tests, canary, blue-green
- Secrets & Certificates: rotation and management
- Multi-Cloud Orchestration: region-specific deployments, networking

### Safety Net

Even `fully_auto` tasks flow through the GitOps pipeline for validation.
Kubernetes reconciliation provides a final safety layer for all automated actions.

---

## 6. Skill System

Skills follow the [agentskills.io specification](https://agentskills.io/specification) using
**progressive disclosure**:

1. **Discovery**: At startup, only `name` and `description` are loaded for all skills
2. **Activation**: When a task matches a skill's description, the full `SKILL.md` body loads
3. **Execution**: Agent follows instructions; optionally loads files from `scripts/`, `references/`, `assets/`

### Standard SKILL.md Frontmatter Fields (agentskills.io)

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Lowercase, hyphens only, max 64 chars, matches directory name |
| `description` | Yes | What the skill does and when to use it. Max 1024 chars. |
| `license` | No | License name or reference |
| `compatibility` | No | Environment requirements. Max 500 chars. |
| `metadata` | No | Key-value map. Use for project-specific fields. |
| `allowed-tools` | No | Space-delimited pre-approved tools (experimental) |

### Project-Specific Metadata Keys

These are stored under `metadata:` in frontmatter — they are not agentskills.io standard fields:

| Key | Values | Description |
|---|---|---|
| `risk_level` | `low`, `medium`, `high` | Determines autonomy and PR gating |
| `autonomy` | `fully_auto`, `conditional`, `requires_PR` | Execution mode |
| `layer` | `temporal`, `gitops` | Which layer executes this skill |
| `human_gate` | string | Description of required approval |

### Skill Size Guidelines

- Keep `SKILL.md` body under 500 lines / 5000 tokens
- Move detailed reference material to `references/`
- Tell the agent *when* to load each reference file — do not load all at startup

### Validation

All skills must pass `skills-ref validate` before merge. This is enforced as a CI gate:

```bash
skills-ref validate ./core/ai/skills/
```

---

## 7. Autonomy, PR Gating, and Risk Levels

| Risk Level | Autonomy | Description |
|---|---|---|
| Low | `fully_auto` | Plan generated and executed via GitOps without PR. Safe for dev/test. |
| Medium | `conditional` | PR created; human may approve or policy may auto-approve. |
| High | `requires_PR` | All actions require explicit human approval before execution. |

**Example — low risk (read operation):**
```yaml
action: get_pod_logs
namespace: payments
pod: api-123
risk_level: low
autonomy: fully_auto
```

**Example — high risk (certificate rotation):**
```yaml
action: rotate_tls_certificates
namespace: production
risk_level: high
autonomy: requires_PR
```

---

## 8. Integration Guidelines

- LLM outputs **structured JSON plans only** — never shell commands or raw text
- GitOps pipelines validate and apply changes deterministically
- All deployments go through GitOps manifests — never `kubectl apply` in CI directly
- Skills define risk and gating in `metadata:` under their `SKILL.md` frontmatter
- Human gates are enforced at both the Temporal and GitOps layers where specified
- Service addresses are always environment variables — never hardcoded URLs

---

## 9. Testing, Validation & Troubleshooting

- Skills: `skills-ref validate ./core/ai/skills/` (required CI gate)
- Temporal workflows: unit tests with mock cloud environments
- GitOps workflows: staging clusters, PR validation, rollback scenarios
- Memory agents: integration tests via `/api/health` and `/api/chat` endpoints
- Inference backends: smoke test llama.cpp availability before Ollama fallback
- Continuous monitoring for errors, retries, and workflow consistency

---

## 10. Appendices

### A: Skill Index Mapping

| Skill Category | Example Skills | Layer | Default Autonomy |
|---|---|---|---|
| **Cost Management** | cost-optimizer, capacity-planning | Temporal | conditional |
| **Monitoring** | alert-prioritizer, cluster-health-check | Temporal | conditional |
| **Security** | compliance-scanner, analyze-security | GitOps | requires_PR |
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
FLUX_GIT_REPO=git@example.com:lloydchang/gitops-infra-control-plane.git

# GitOps Configuration
GITOPS_TOOL=flux                   # or argo_cd
GITOPS_NAMESPACE=gitops-system

# Memory Agent Configuration
MEMORY_AGENT_URL=http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080
BACKEND_PRIORITY=llama-cpp,ollama  # local inference first — no external API calls
LANGUAGE_PRIORITY=rust,go,python

# Temporal
TEMPORAL_ADDRESS=temporal-frontend.ai-infrastructure.svc.cluster.local:7233

# Monitoring
PROMETHEUS_URL=https://prometheus.example.com
GRAFANA_API_KEY=your_grafana_key
```

### C: Human Gate Reference Table

| Operation Type | Risk Level | Human Gate Required | Approval Method |
|---|---|---|---|
| **Read Operations** | Low | No | N/A |
| **Dev/Test Changes** | Low | No | N/A |
| **Production Scaling** | Medium | Yes | PR approval |
| **Cost Optimization** | Medium | Conditional | Auto-approve < $100/day |
| **Security Changes** | High | Yes | PR + security review |
| **Database Changes** | High | Yes | PR + DBA review |
| **Network Changes** | High | Yes | PR + network review |
| **Certificate Rotation** | High | Yes | PR + security review |

### D: Composite Workflows & Autonomy Rules

#### Example: Tenant Onboarding Workflow

```yaml
workflow: tenant-onboarding
steps:
  - id: create-infrastructure
    skill: infrastructure-provisioning
    risk: medium
    autonomy: conditional
  - id: setup-monitoring
    skill: observability-stack
    risk: low
    autonomy: fully_auto
  - id: configure-security
    skill: analyze-security
    risk: high
    autonomy: requires_PR
  - id: deploy-applications
    skill: deployment-strategy
    risk: medium
    autonomy: conditional
```

#### Autonomy Rules Matrix

| Layer | Low Risk | Medium Risk | High Risk |
|---|---|---|---|
| **Temporal** | fully_auto | conditional | requires_PR |
| **GitOps** | fully_auto | conditional | requires_PR |
| **Combined** | fully_auto | conditional | requires_PR |

---

## Summary

- Architecture follows the **tool-constrained / structured tool agent** pattern
- LLM decides *what*; deterministic system decides *how*
- Four layers: Memory Agents → Temporal Orchestration → GitOps Control → Monitoring
- All inference is local (llama.cpp / Ollama) — infrastructure data stays on-prem
- Skills follow [agentskills.io specification](https://agentskills.io/specification); project fields live under `metadata:`
- Autonomy is explicitly defined per skill via `metadata:` in `SKILL.md`
- All deployments go through GitOps — no direct `kubectl apply` in CI
- GitOps and Kubernetes reconciliation provide the safety net for all automated actions
