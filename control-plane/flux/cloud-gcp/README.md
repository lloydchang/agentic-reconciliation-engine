# GCP Cloud Overlay

Enables GCP-specific control-plane manifests when Flux reconciles `./cloud-gcp`.

## Contents
- `kustomization.yaml` – aggregates GCP network, clusters, workloads, Vertex/AI configs, and auth helpers.
- Drop additional patches or parameter files here for project IDs, regions, or node pools.

## Usage
1. Tweak the referenced manifests (`gcp-*`) in `control-plane/flux/` so they align with your project, network, and service accounts.
2. Flux provisions the stack as soon as `control-plane/flux/kustomization.yaml` lists `./cloud-gcp`.
3. Remove the resource entry to tear down the GCP overlay cleanly.
