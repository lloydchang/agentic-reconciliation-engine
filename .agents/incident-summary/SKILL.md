# incident-summary

## Purpose
Summarize alerts and incidents from monitoring systems into structured operational insights.

## When to Use
- When operational alerts are detected (e.g., high error rates, pod crashes, latency spikes)
- When incident triage requires quick summarization of events
- For generating incident reports or postmortem drafts

## Inputs
- Alert payload from monitoring systems (Prometheus, Grafana, etc.)
- Pod events and logs from Kubernetes
- Deployment history and recent changes
- Metrics summary (error rates, latency, resource usage)

## Process
1. Analyze operational signals from monitoring systems
2. Identify key events, timelines, and patterns
3. Correlate alerts with recent deployments or configuration changes
4. Generate concise summary focusing on impact, likely causes, and next steps

## Outputs
- Incident summary with service impact assessment
- Timeline of key events
- List of probable root causes
- Recommended immediate actions and investigation steps

## Environment
- Kubernetes cluster with monitoring stack
- Access to Prometheus/Grafana APIs
- kubectl access for pod event queries

## Safety Considerations
- Do not execute remediation actions without human approval
- Focus on analysis and recommendation, not direct intervention

## Optional Scripts
scripts/summarize_alerts.py

## Optional Manifests
manifests/example.yaml

