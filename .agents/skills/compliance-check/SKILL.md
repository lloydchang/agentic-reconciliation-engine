---
name: compliance-check
description: >
  Legacy compliance scanning skill consolidated into `compliance-security-scanner`; use the canonical skill for full coverage.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Compliance Check — Redirect to Compliance & Security Scanner

This skill is deprecated in favor of `compliance-security-scanner`, which already covers full compliance, security, risk scoring, and dispatcher integration. Use the canonical skill instead for any compliance, policy validation, or audit requirements.

## When to invoke
- Refer to `.agents/skills/compliance-security-scanner/SKILL.md` for invocation patterns, workflows, telemetry, and human gate guidance.
- All compliance-related requests should now use `compliance-security-scanner` to avoid duplication and ensure consistent outputs.

## Related skills
- `/compliance-security-scanner`: canonical compliance/security scanning skill.
