---
name: secret-rotation
description: |
  Rotate secrets, certificates, and keys across clouds and Kubernetes using AI to project expiration and automate approvals.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Secret Rotation — World-class Key Hygiene Playbook

Keeps secrets fresh, certificates valid, and keys secure with risk-aware automations, telemetry, and human gates.

## When to invoke
- Certificates/keys nearing expiration.
- Secrets marked leaked or compromised.
- Key rotations triggered by compliance (PCI, SOC2).

## Capabilities
- **Expiration forecasting**, **automated rotation**, **shared context**, **alerting**.
## When to invoke
- Certificates/keys nearing expiration.
- Secrets marked leaked or compromised.
- Key rotations triggered by compliance (PCI, SOC2).

## Capabilities
- **Expiration forecasting** tracks TTL and metrics.
- **Automated rotation** scripts for key vaults, Kubernetes secrets, containers.
- **Shared context** `shared-context://memory-store/secret-rotation/{operationId}`.

## Invocation
```bash
/secret-rotation rotate --secret=azure-key --vault=prod-kv
/secret-rotation forecast --secret=payment-tls --window=30d
/secret-rotation revoke --key=pk-123 --reason=compromise
```
