# GitOps Infra Control Plane - Fallback Resources Strategy

## Overview
For resources not directly supported by native cloud controllers (ACK/ASO/KCC), follow this hierarchical fallback strategy:

## 1. Official Kubernetes Operator
Use the official operator provided by the project or vendor when available.

Examples:
- cert-manager for TLS certificates
- ingress-nginx for ingress controllers
- external-dns for DNS management
- prometheus-operator for monitoring

## 2. Flux-Managed Kubernetes Job
For one-off or complex deployments, use Flux-managed Jobs to run kubectl or helm commands.

Example:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: deploy-custom-resource
spec:
  template:
    spec:
      containers:
      - name: deployer
        image: bitnami/kubectl:latest
        command: ["kubectl", "apply", "-f", "manifests/"]
        volumeMounts:
        - name: manifests
          mountPath: /manifests
      volumes:
        - name: manifests
          configMap:
            name: custom-manifests
      restartPolicy: OnFailure
```

## 3. Targeted Crossplane Provider (Last Resort)
Only use Crossplane providers when absolutely necessary and no other options exist.
This should be avoided to maintain the no-abstraction principle.

## Current Fallback Resources
None currently needed - all infrastructure managed by native controllers.

## Adding New Fallback Resources
1. Identify the resource requirement
2. Check if native controller support exists
3. If not, evaluate official operator availability
4. Document the decision in this file
5. Implement in core/resources/fallback/ directory

## See Also
- **SealedSecrets Documentation**: See [docs/SEALED-SECRETS.md](docs/SEALED-SECRETS.md) for comprehensive secret management guide
- **Secret Management**: See [docs/SECRET-MANAGEMENT.md](docs/SECRET-MANAGEMENT.md) for security practices and incident response
