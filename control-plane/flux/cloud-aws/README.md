# AWS Cloud Overlay

# AWS Cloud Overlay

This overlay groups the AWS-specific network, cluster, and workload manifests that Flux deploys when `./cloud-aws` is listed in `control-plane/flux/kustomization.yaml`.

## Structure
- `kustomization.yaml` pulls the tenant-level directories and applies `patches/` for per-environment overrides.
- `patches/vpc-overrides.yaml` updates the VPC CIDR and tags (e.g., apply your account tag strategy).
- `patches/eks-overrides.yaml` overrides cluster metadata such as the role ARN, networking, and node pool sizing.

## Customizing
1. Update the patch files to match your AWS account IDs, CIDRs, and IAM roles.
2. Build the overlay locally (`kustomize build control-plane/flux/cloud-aws`) to verify the generated resources.
3. Run `scripts/enable-cloud.sh aws` and `flux reconcile kustomization control-plane --with-source` to apply it.
