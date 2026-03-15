# GitOps Pull Request Skill

## # GitOps PR Skill

## Name
gitops-pr

## Purpose
Create infrastructure changes via GitOps pull requests for automated deployments using Flux or Argo CD.

## When to Use
- When automated remediation requires infrastructure changes
- When configuration drift is detected and needs correction
- When scaling operations require resource modifications
- When security patches need to be applied via GitOps
- When deploying new services or updating existing ones

## Inputs
- Patch request (resource modification details)
- Manifest update (YAML changes)
- Resource configuration change (limits, replicas, etc.)
- Cluster state information
- Deployment context and requirements
- Deployment context (namespace, environment)

## Process
1. Analyze the required infrastructure change
2. Generate appropriate YAML manifest modifications
3. Validate syntax and Kubernetes resource definitions
4. Create git commit with structured commit message
5. Open pull request in infrastructure repository
6. Include deployment notes and rollback instructions
7. Validate against policy compliance if required

## Outputs
- Git commit patch with changes
- Pull request description with context
- Deployment notes and impact assessment
- Rollback instructions and procedures
- Policy compliance validation results
- Expected deployment timeline

## Environment
- Git repository with GitOps configuration
- Flux or Argo CD controller
- Kubernetes cluster with GitOps deployment
- RBAC permissions for infrastructure changes

## Dependencies
- Git repository access
- GitOps controller (Flux/Argo CD)
- Kubernetes API access
- Policy validation tools (optional)
- CI/CD pipeline integration

## Scripts
- scripts/create_pr.py: Python script to generate PRs and validate changes

