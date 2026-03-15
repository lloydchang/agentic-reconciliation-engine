Name: runbook-planner
Purpose: Convert operational alerts into structured runbook execution plans.
Inputs: Alert message, Cluster state, Incident summary, Service configuration, Historical runbook data
Process: Map alerts to existing runbook templates, analyze current cluster state, generate step-by-step response plan with safety checks, identify required approvals, and prepare execution workflow with rollback procedures.
Outputs: Step-by-step response plan, Executable commands, Safety warnings, Required approvals, Rollback procedures, Success criteria
Optional scripts: scripts/runbook_executor.py
Optional manifests: manifests/example.yaml

