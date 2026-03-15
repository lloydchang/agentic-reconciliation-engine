# Using gitops-infra-control-plane as a Building Block

This repository contains the **Continuous Reconciliation Engine for Multi-Cloud Infra** (AGPL-3.0 licensed) that serves as a foundational "engine" for infrastructure management platforms. This guide explains how to use this engine as a building block for building proprietary layers above it.

## Architectural Concept

The Continuous Reconciliation Engine (CRE) is the core infrastructure management engine. It provides:

- **24/7 continuous reconciliation** across AWS, Azure, GCP
- **Configuration drift prevention** and auto-healing
- **GitOps-driven infrastructure** via Flux controllers
- **Hub-and-spoke topology** for multi-cloud management

**Above this engine**, you can build proprietary layers such as:

- SaaS platforms
- Compliance frameworks
- DevOps portals
- Enterprise management consoles
- Multi-tenant infrastructure services

## Integration Approaches

### 1. Core Replacement Pattern

Use CRE as the primary reconciliation engine for infrastructure management, supplementing or gradually migrating from traditional IaC tools (Terraform/CDK/CloudFormation), then build proprietary orchestration layers on top.

**Brownfield approach**: Keep existing IaC for initial setup, add CRE for continuous reconciliation and drift prevention.
**Greenfield approach**: Start fresh with CRE as the foundation, build proprietary layers above it.

### 2. Platform Foundation Pattern

Use CRE as the infrastructure foundation, add proprietary APIs, UIs, and business logic layers.

### 3. Augmentation Pattern

Keep existing IaC tools but add CRE for continuous monitoring and drift detection.

### 4. Multi-Platform Pattern

Build a unified control plane that manages multiple CRE instances across different environments.

### 5. SaaS Pattern

Wrap CRE in a SaaS offering with proprietary features (multi-tenancy, billing, etc.).

## Licensing Considerations

The core engine is AGPL-3.0, which allows building proprietary software on top as long as:

- Communication happens via APIs/network (not code linking)
- CRE core remains unmodified
- Clear architectural boundaries exist

## Quick Start Integration

1. **Deploy the CRE** using the provided scripts and manifests
2. **Expose APIs** for infrastructure operations
3. **Build your platform layer** that communicates via GitOps, webhooks, or REST APIs
4. **Maintain separation** - your proprietary code never links to AGPL code directly

See detailed guides:

- [Greenfield Deployment](./GREENFIELD-DEPLOYMENT.md)
- [Brownfield Migration](./BROWNFIELD-MIGRATION.md)
- [API Integration](./API-INTEGRATION.md)
- [Proprietary Extensions](./PROPRIETARY-EXTENSIONS.md)
