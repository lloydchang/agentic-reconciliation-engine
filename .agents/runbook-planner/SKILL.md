# Runbook Planner Skill

## Name
runbook-planner

## Purpose
Convert operational alerts into structured runbook execution plans with safety validation and rollback procedures.

## When to Use
- When alerts require systematic response procedures
- When incidents need coordinated multi-step remediation
- When operational procedures require approval workflows
- When complex failures need structured troubleshooting plans
- When automated remediation requires human oversight

## Inputs
- Alert message and severity
- Current cluster state and resource status
- Incident summary and context
- Service configuration and dependencies
- Historical runbook data and success patterns
- Operational constraints and maintenance windows
- Available operator permissions

## Process
1. Analyze alert type and severity to determine response urgency
2. Map alert to existing runbook templates or create new procedures
3. Analyze current cluster state and affected resources
4. Generate step-by-step response plan with safety checks
5. Identify required approvals and escalation procedures
6. Prepare execution workflow with rollback procedures
7. Validate each step against cluster policies and constraints
8. Include success criteria and verification steps
9. Estimate execution time and resource requirements

## Outputs
- Step-by-step response plan with detailed procedures
- Executable commands and automation scripts
- Safety warnings and risk assessments
- Required approvals and escalation paths
- Rollback procedures and recovery steps
- Success criteria and validation checkpoints
- Estimated execution timeline and resource needs

## Environment
- Kubernetes cluster with monitoring and alerting
- Runbook template repository
- Incident management system integration
- Approval workflow systems
- Communication channels (Slack, Teams, etc.)

## Dependencies
- Alert management system (Prometheus, Grafana, etc.)
- Runbook template storage and versioning
- Cluster API access for state validation
- Incident tracking and documentation
- Approval workflow integration
- Communication platform APIs

## Scripts
- scripts/runbook_executor.py: Python script to execute and validate runbook steps

