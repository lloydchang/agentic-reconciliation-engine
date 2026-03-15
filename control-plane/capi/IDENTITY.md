# CAPI Provider Identity

Do not store static credentials in this repo. Use workload identity mechanisms:

- AWS (CAPA): IRSA on the CAPA controller service account
- Azure (CAPZ): Azure Managed Identity / Workload Identity
- GCP (CAPG): Workload Identity Federation

Inject identities via HelmRelease values or post-install patches to the
`capi-system` service accounts for each provider.
