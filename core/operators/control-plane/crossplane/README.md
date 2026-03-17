# Crossplane Control Plane

This directory contains XRDs, Compositions, and provider configs for the
GitOps Infra Control Plane. It assumes workload identity for providers.

Operator-supplied values to review before apply:
- ProviderConfig identities (AWS/Azure/GCP) are `InjectedIdentity`
- Network Compositions require `subnetCidrs` with at least 3 entries
- Azure resource group in `network-azure.yaml` and database composition
- GCP project/region values in database and network compositions
