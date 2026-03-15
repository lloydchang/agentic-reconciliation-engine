# Azure Local Emulator Overlay

This optional overlay deploys the Azure emulator services under `infrastructure/tenants/azure/localstack`. Enable it by uncommenting the `local-emulator` entry in `control-plane/flux/cloud-azure/kustomization.yaml`.

## Purpose
Use this when you are developing locally and do not want to hit a real Azure subscription. The overlay brings up Azurite, Azure SQL emulator, Cosmos emulator, Event Hubs emulator, Service Bus emulator, and related local-stack helpers defined in `infrastructure/tenants/azure/localstack`.

## Enablement
1. Ensure your local environment satisfies the emulator prerequisites (e.g., run Azurite, configure storage endpoints, etc.).
2. Uncomment the `- local-emulator` entry in `control-plane/flux/cloud-azure/kustomization.yaml` so Flux reconciles this overlay.
3. Flux will now apply `local-emulator/kustomization.yaml`, which points at `infrastructure/tenants/azure/localstack`.
4. When you no longer need the emulator, comment out the entry and `flux reconcile kustomization control-plane --with-source` to let Flux prune the emulator resources.
