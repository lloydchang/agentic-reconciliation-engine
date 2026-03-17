# Operator Inputs Checklist

Update these values before applying to a real environment.

## CAPI Providers

- `core/operators/capi/infrastructure-providers.yaml`
  - `arn:aws:iam::ACCOUNT:role/capa-controller-role`
  - `azure.workload.identity/client-id: "<CAPZ_CLIENT_ID>"`
  - `capg-controller@PROJECT_ID.iam.gserviceaccount.com`

## CAPI ClusterClasses

- `core/operators/capi/clusterclass-aws.yaml`
  - `region`, `sshKeyName`
- `core/operators/capi/clusterclass-azure.yaml`
  - `subscriptionID`, `resourceGroup`
- `core/operators/capi/clusterclass-gcp.yaml`
  - `project`, `region`

## Crossplane Identity

- `core/operators/identity/irsa-setup.yaml`
  - `ACCOUNT_ID`, `REGION`, `CLUSTER_ID`
- `core/operators/identity/azure-workload-identity.yaml`
  - `SUBSCRIPTION_ID`, `RESOURCE_GROUP`
- `core/operators/identity/gcp-workload-identity.yaml`
  - `PROJECT_ID`

## ESO Workload Identity (Spokes)

- `core/resources/tenants/3-workloads/eso-workload-identity/helmrelease.yaml`
  - uncomment and set the correct service account annotations
