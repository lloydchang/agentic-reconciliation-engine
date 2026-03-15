# Cluster API Control Plane

This directory contains CAPI provider installs and ClusterClass templates.

Operator-supplied values to review before apply:
- CAPA/CAPZ/CAPG workload identity annotations in `infrastructure-providers.yaml`
- AWS region, SSH key in `clusterclass-aws.yaml`
- Azure subscription ID and resource group in `clusterclass-azure.yaml`
- GCP project and region in `clusterclass-gcp.yaml`
- Network naming convention assumes `NETWORK_REF` and `${NETWORK_REF}-subnet`
