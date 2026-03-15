# Kubectl Assistant Skill

## Name
kubectl-assistant

## Purpose
Generate and explain kubectl commands for Kubernetes cluster operations with safety checks and context awareness.

## When to Use
- When operators need help with kubectl command syntax
- When troubleshooting cluster issues and need diagnostic commands
- When performing routine operations but unsure of exact flags
- When learning Kubernetes operations and need guidance
- When generating automation scripts for cluster management

## Inputs
- Natural language request describing the operation
- Cluster context (namespace, environment)
- Resource type and target resources
- Operation intent (create, update, delete, query)
- Safety constraints and permissions

## Process
1. Parse user request to identify operational intent
2. Map intent to appropriate kubectl command pattern
3. Generate safe executable commands with proper flags
4. Add appropriate selectors and labels for targeting
5. Include safety warnings for destructive operations
6. Provide command explanation and expected behavior
7. Suggest alternative commands when applicable

## Outputs
- Executable kubectl command with proper syntax
- Detailed command explanation and behavior
- Safety warnings for destructive operations
- Alternative commands for different scenarios
- Expected output description and interpretation
- Prerequisites and permissions requirements

## Environment
- Kubernetes cluster with kubectl access
- RBAC permissions for target operations
- Proper cluster context configuration
- Access to cluster resources and namespaces

## Dependencies
- kubectl binary access
- Cluster API server connectivity
- Authentication and authorization setup
- Resource definitions and schemas
- Cluster context and namespace access

## Scripts
- scripts/gen_kubectl_cmds.py: Python script to generate and validate commands

