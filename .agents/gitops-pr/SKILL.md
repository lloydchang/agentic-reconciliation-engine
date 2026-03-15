Name: gitops-pr
Purpose: Create infrastructure changes via GitOps pull requests for automated deployments.
Inputs: Patch request, Manifest update, Resource configuration change, Cluster state
Process: Generate configuration changes for Flux/ArgoCD, validate syntax, create commit with appropriate changes, open pull request in infrastructure repository with deployment notes and rollback instructions.
Outputs: Git commit patch, Pull request description, Deployment notes, Rollback instructions, Impact assessment
Optional scripts: scripts/create_pr.py
Optional manifests: manifests/example.yaml

