# SOPS Tenant Secrets (Fallback)

This kustomization was used to decrypt tenant secrets with SOPS.
The primary path is ESO + workload identity; SOPS should only be used
for on‑prem or legacy cases.
