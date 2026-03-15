# Operator Inputs Checklist

Update these values before applying to a real environment.

## CAPI Providers
- `control-plane/capi/infrastructure-providers.yaml`
  - `arn:aws:iam::ACCOUNT:role/capa-controller-role`
  - `azure.workload.identity/client-id: "<CAPZ_CLIENT_ID>"`
  - `capg-controller@PROJECT_ID.iam.gserviceaccount.com`

## CAPI ClusterClasses
- `control-plane/capi/clusterclass-aws.yaml`
  - `region`, `sshKeyName`
- `control-plane/capi/clusterclass-azure.yaml`
  - `subscriptionID`, `resourceGroup`
- `control-plane/capi/clusterclass-gcp.yaml`
  - `project`, `region`

## Crossplane Identity
- `control-plane/identity/irsa-setup.yaml`
  - `ACCOUNT_ID`, `REGION`, `CLUSTER_ID`
- `control-plane/identity/azure-workload-identity.yaml`
  - `SUBSCRIPTION_ID`, `RESOURCE_GROUP`
- `control-plane/identity/gcp-workload-identity.yaml`
  - `PROJECT_ID`

## ESO Workload Identity (Spokes)
- `infrastructure/tenants/3-workloads/eso-workload-identity/helmrelease.yaml`
  - uncomment and set the correct service account annotations
