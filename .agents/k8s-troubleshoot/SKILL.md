# Kubernetes Troubleshoot Skill

## Name
k8s-troubleshoot

## Purpose
Diagnose and troubleshoot Kubernetes workload failures and cluster issues.

## When to Use
- When pods are failing (CrashLoopBackOff, ImagePullBackOff, etc.)
- When services are not accessible or routing issues occur
- For investigating resource limits, probe failures, or network problems
- During cluster health checks or post-deployment validation

## Inputs
- kubectl describe pod output
- kubectl logs from containers
- kubectl get events from namespaces
- Resource usage data (CPU, memory, disk)
- Cluster state information
- Error messages from applications

## Process
1. Identify common Kubernetes failure patterns and states
2. Query cluster state using kubectl commands
3. Analyze container logs and system events
4. Correlate issues with resource metrics and configuration
5. Suggest diagnostic steps or remediation fixes

## Outputs
- Explanation of the failure reason
- Suggested debugging commands to run next
- Potential remediation steps or configuration patches
- Resource recommendations if applicable

## Environment
- Kubernetes cluster with kubectl access
- RBAC permissions to query pod states and logs
- Access to monitoring/metrics if available

## Dependencies
- kubectl binary access
- Cluster API access
- Monitoring stack integration (optional)

## Scripts
- scripts/analyze_pod.py: Python script to analyze pod failures

