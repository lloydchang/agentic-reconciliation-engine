# Crossplane Provider Configurations

This directory contains Crossplane ProviderConfig resources for AWS, Azure, and GCP.

## ProviderConfig Purpose

ProviderConfig tells Crossplane how to authenticate to cloud providers. It's a cluster-scoped resource, meaning it's available to all namespaces (subject to RBAC).

## Structure

```
providers/
├── aws-provider-config.yaml        # AWS ProviderConfig + Secret
├── azure-provider-config.yaml     # Azure ProviderConfig + Secret
├── gcp-provider-config.yaml       # GCP ProviderConfig + Secret
└── README.md                       # This file
```

## Security Model

- **Secrets**: Stored as Kubernetes Secrets in `crossplane-system` namespace
- **RBAC**: Only cluster admins can view/modify ProviderConfigs
- **Provider Pods**: Run with minimal permissions, access secrets via mounted volumes
- **Network Policies**: Egress restricted to cloud provider APIs only

## Setup Steps

1. **Create AWS credentials secret**:
   ```bash
   kubectl create secret generic aws-creds \
     --namespace crossplane-system \
     --from-file=key=./secrets/aws-credentials
   ```
   Where `aws-credentials` contains AWS credentials file format:
   ```
   [default]
   aws_access_key_id = AKIAIOSFODNN7EXAMPLE
   aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```

2. **Create Azure service principal secret**:
   ```bash
   kubectl create secret generic azure-creds \
     --namespace crossplane-system \
     --from-file=key=./secrets/azure-service-principal.json
   ```

3. **Create GCP service account key secret**:
   ```bash
   kubectl create secret generic gcp-creds \
     --namespace crossplane-system \
     --from-file=key=./secrets/gcp-service-account-key.json
   ```

4. **Apply ProviderConfigs**:
   ```bash
   kubectl apply -f providers/
   ```

5. **Verify**:
   ```bash
   kubectl get providerconfigs.aws.crossplane.io
   kubectl get providerconfigs.azure.crossplane.io
   kubectl get providerconfigs.gcp.crossplane.io
   ```

   All should show `READY: True`.

## RBAC Isolation

ProviderConfigs are cluster-scoped. To restrict which teams can use which providers, use ProviderConfigUsage resources:

```yaml
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfigUsage
metadata:
  name: aws-provider-usage
spec:
  providerConfigRef:
    name: aws-provider
```

Combine with Kubernetes RBAC to control who can create resources referencing this ProviderConfig.

## Troubleshooting

**ProviderConfig not ready**:
```bash
kubectl describe providerconfig aws-provider
# Check for authentication errors, missing secret, invalid credentials
```

**ManagedResource not connecting**:
```bash
kubectl get managed -o wide
# Check providerConfig reference is correct
```

**Secret not found**:
```bash
kubectl get secret aws-creds -n crossplane-system -o yaml
# Verify secret exists in crossplane-system namespace
```

## References

- [Crossplane ProviderConfig Documentation](https://docs.crossplane.io/latest/concepts/providers/)
- [AWS Provider](https://marketplace.upbound.io/providers/upbound/provider-aws)
- [Azure Provider](https://marketplace.upbound.io/providers/upbound/provider-azure)
- [GCP Provider](https://marketplace.upbound.io/providers/upbound/provider-gcp)
