# Incident Summary Skill

## Name
incident-summary

## Purpose
Summarize alerts and incidents from monitoring systems to provide structured operational insights.

## When to Use
- When an alert is triggered from Prometheus, Grafana, or other monitoring tools
- When analyzing operational signals from cluster events
- When generating incident reports or postmortems
- When converting raw logs or metrics into actionable summaries

## Inputs
- Alert payload (JSON or structured data)
- Pod events and logs
- Deployment history
- Metrics summary from Prometheus/Grafana
- Cluster state information

## Process
1. Analyze operational signals from monitoring systems
2. Identify key events, timestamps, and affected components
3. Correlate related events to determine likely causes
4. Generate a concise timeline of events
5. Produce probable root causes and impact assessment
6. Suggest immediate next actions

## Outputs
- Structured incident summary with title and description
- Timeline of key events
- List of likely root causes with confidence levels
- Recommended immediate actions and remediation steps
- Severity rating and escalation recommendations

## Environment
- Kubernetes cluster with monitoring stack
- Access to Prometheus, Grafana, and kubectl
- Optional: Integration with incident management tools

## Dependencies
- Monitoring data access
- Cluster event logs
- Historical incident data (optional)

## Scripts
- scripts/summarize_alerts.py: Python script to parse alerts and generate summaries
