# Terraform Infrastructure Inventory Matrix

## Overview

This document catalogs all infrastructure resources currently defined in Terraform configurations across AWS, GCP, and Azure. This inventory serves as the baseline for migrating to Crossplane.

**Source**: `core/infrastructure/terraform/{aws,gcp,azure}/main.tf`
**Date**: 2026-03-20

---

## AWS Resources

### File: `core/infrastructure/terraform/aws/main.tf`

| Resource Type | Terraform Resource | Count | Region | Purpose |
|---|---|---|---|---|
| **Networking** | | | | |
| VPC | `module.vpc` (terraform-aws-modules/vpc/aws) | 1 | var.region | Main VPC for EKS cluster |
| Subnets (Private) | `module.vpc.private_subnets` | 3 (per env) | var.region | Private subnets for worker nodes |
| Subnets (Public) | `module.vpc.public_subnets` | 3 (per env) | var.region | Public subnets for NAT/IGW |
| NAT Gateways | `module.vpc.nat_gateways` (from module) | 1 or 3 | var.region | Outbound internet access |
| Internet Gateway | `module.vpc.igw` (from module) | 1 | var.region | Public internet access |
| Route Tables | `module.vpc.private_route_tables` | 3 | var.region | Private subnet routing |
| Security Groups | `aws_security_group.*` | 5 | var.region | ALB, RDS, Redis, EKS nodes |
| **Compute** | | | | |
| EKS Cluster | `module.eks` (terraform-aws-modules/eks/aws) | 1 | var.region | Kubernetes cluster |
| EKS Node Groups | `module.eks.eks_managed_node_groups` | 2 (general, spot) | var.region | Worker nodes |
| Fargate Profiles | `module.eks.fargate_profiles` | 1 (ai_services) | var.region | Serverless workloads |
| **Database** | | | | |
| RDS PostgreSQL | `module.rds` (terraform-aws-modules/rds/aws) | 1 | var.region | Primary database |
| ElastiCache Redis | `module.redis` (terraform-aws-modules/elasticache/aws) | 1 | var.region | Caching layer |
| **Storage** | | | | |
| S3 Bucket | `aws_s3_bucket.backups` | 1 | var.region | Backup storage |
| **Load Balancing** | | | | |
| Application Load Balancer | `module.alb` (terraform-aws-modules/alb/aws) | 1 | var.region | Application ingress |
| CloudFront | `module.cloudfront` (terraform-aws-modules/cloudfront/aws) | 1 | Global | CDN/WAF |
| **Security** | | | | |
| ACM Certificate | `aws_acm_certificate.alb` | 1 | us-east-1* | SSL certificate |
| WAFv2 | `aws_wafv2_web_acl` | 1 (prod only) | Global | Web Application Firewall |
| Lambda@Edge | `aws_lambda_function.waf_integration` | 1 (prod only) | us-east-1* | WAF integration |
| **DNS** | | | | |
| Route 53 Records | `aws_route53_record.api` | 1 | Global | DNS record |
| **Monitoring** | | | | |
| CloudWatch Log Groups | Implicit (EKS, RDS, ALB) | Multiple | var.region | Logging |
| CloudWatch Metrics | Implicit | Multiple | var.region | Metrics |
| **IAM** | | | | |
| IAM Roles | `aws_iam_role.*` | Multiple | IAM global | Service roles |
| **Other** | | | | |
| KMS Key Ring | `google_kms_key_ring` (Note: This is GCP resource in AWS file? Check) | - | - | - |

*Note: CloudFront and associated resources require us-east-1 for certificate and Lambda@Edge*

---

## GCP Resources

### File: `core/infrastructure/terraform/gcp/main.tf`

| Resource Type | Terraform Resource | Count | Region | Purpose |
|---|---|---|---|---|
| **Networking** | | | | |
| VPC Network | `google_compute_network.vpc` | 1 | var.region | Main VPC |
| Subnetwork (Private) | `google_compute_subnetwork.private` | 1 | var.region | Private subnets with secondary ranges |
| Subnetwork (Public) | `google_compute_subnetwork.public` | 1 | var.region | Public subnets |
| Cloud Router | `google_compute_router.router` | 1 | var.region | NAT routing |
| Cloud NAT | `google_compute_router_nat.nat` | 1 | var.region | Outbound internet access |
| **Compute** | | | | |
| GKE Cluster (Autopilot) | `google_container_cluster.gke` | 1 | var.region | Kubernetes cluster |
| **Database** | | | | |
| Cloud SQL PostgreSQL | `google_sql_database_instance.postgres` | 1 | var.region | Primary database |
| Cloud SQL Database | `google_sql_database.ai_portal` | 1 | var.region | Database schema |
| Cloud SQL User | `google_sql_user.ai_portal` | 1 | var.region | Database user |
| Memorystore Redis | `google_redis_instance.redis` | 1 | var.region | Caching layer |
| **Storage** | | | | |
| Cloud Storage Bucket | `google_storage_bucket.backups` | 1 | var.region | Backup storage |
| BigQuery Dataset | `google_bigquery_dataset.gke_usage` | 1 | var.region | GKE usage metering |
| **Load Balancing** | | | | |
| Cloud Load Balancer | `google_compute_global_forwarding_rule.lb_forwarding_rule` + related | 1 | Global | Global HTTP(S) LB |
| Global Static IP | `google_compute_global_address.lb_ip` | 1 | Global | LB IP address |
| URL Map | `google_compute_url_map.lb_url_map` | 1 | Global | Routing rules |
| Backend Services | `google_compute_backend_service.*` | 2 (api, dashboard) | Global | Backend pools |
| Health Checks | `google_compute_health_check.*` | 2 (api, dashboard) | var.region | Health probes |
| Managed SSL Certificate | `google_compute_managed_ssl_certificate.lb_cert` | 1 | Global | SSL cert |
| **Security** | | | | |
| Cloud Armor | `google_compute_security_policy.cloud_armor` | 1 | Global | WAF equivalent |
| **DNS** | | | | |
| Cloud DNS Managed Zone | `google_dns_managed_zone.ai_portal` | 1 | Global | DNS zone |
| Cloud DNS Record Set | `google_dns_record_set.api` | 1 | Global | DNS A record |
| **Encryption** | | | | |
| Cloud KMS Key Ring | `google_kms_key_ring.key_ring` | 1 | global | KMS key ring |
| Cloud KMS Crypto Key | `google_kms_crypto_key.bucket_key` | 1 | global | Encryption key |
| **Service Enablement** | | | | |
| Required APIs | `google_project_service.*` | 10+ | N/A | Enable GCP APIs |

---

## Azure Resources

### File: `core/infrastructure/terraform/azure/main.tf`

| Resource Type | Terraform Resource | Count | Location | Purpose |
|---|---|---|---|---|
| **Networking** | | | | |
| Resource Group | `azurerm_resource_group.rg` | 1 | var.location | Resource container |
| Virtual Network | `azurerm_virtual_network.vnet` | 1 | var.location | Main VNet |
| Subnet (Private) | `azurerm_subnet.private` | 1 | var.location | Private subnets |
| Subnet (Public) | `azurerm_subnet.public` | 1 | var.location | Public subnets |
| **Compute** | | | | |
| AKS Cluster | `azurerm_kubernetes_cluster.aks` | 1 | var.location | Kubernetes cluster |
| **Database** | | | | |
| Azure PostgreSQL Flexible Server | `azurerm_postgresql_flexible_server.postgres` | 1 | var.location | Primary database |
| Azure PostgreSQL Database | `azurerm_postgresql_flexible_server_database.ai_portal` | 1 | var.location | Database schema |
| Azure Cache for Redis | `azurerm_redis_cache.redis` | 1 | var.location | Caching layer |
| **Storage** | | | | |
| Storage Account | `azurerm_storage_account.backups` | 1 | var.location | Backup storage |
| Storage Container | `azurerm_storage_container.backups` | 1 | var.location | Backup container |
| **Load Balancing** | | | | |
| Application Gateway | `azurerm_application_gateway.appgw` | 1 | var.location | Application load balancer |
| Public IP | `azurerm_public_ip.appgw` | 1 | var.location | AppGw public IP |
| **Monitoring** | | | | |
| Log Analytics Workspace | `azurerm_log_analytics_workspace.insights` | 1 | var.location | Azure Monitor |
| **Security** | | | | |
| Key Vault | `azurerm_key_vault.kv` | 1 | var.location | Secrets/certificates |
| Key Vault Certificate | `azurerm_key_vault_certificate.api_cert` | 1 | var.location | SSL certificate |
| **DNS** | | | | |
| Private DNS Zone | `azurerm_private_dns_zone.postgres` | 1 | var.location | PostgreSQL private DNS |
| Private DNS Zone Link | `azurerm_private_dns_zone_virtual_network_link.postgres` | 1 | var.location | VNet link |

---

## Summary Statistics

| Cloud Provider | Resource Types | Total Resources | Environments |
|---|---|---|---|
| AWS | 15+ | ~30-40 | dev/staging/prod |
| GCP | 15+ | ~30-40 | dev/staging/prod |
| Azure | 12+ | ~25-35 | dev/staging/prod |
| **Total** | | **~85-115** | Multi-environment |

---

## Resource Dependencies

### Network Dependencies
1. VPC/VNet → Subnets → (NAT/IGW) → Route Tables
2. Network → Security Groups/NSG/Firewall
3. Database/Cluster → Network (private subnet)

### Compute Dependencies
1. Network → Cluster (node subnet)
2. Cluster → Node Groups (requires VPC CNI configured)
3. Cluster → Fargate Profiles (requires OIDC/IAM)

### Data Dependencies
1. Network → Database (VPC, subnet, security group)
2. Network → Redis (VPC, subnet, security group)
3. Cluster → Database (K8s service connectivity)

### Load Balancer Dependencies
1. Network → LB (public subnet, security group)
2. LB → Target (Cluster services, health checks)
3. LB → WAF (optional integration)
4. LB → DNS (record pointing to LB IP/hostname)

---

## Next Steps

1. **Gap Analysis**: Compare inventory with existing Crossplane capabilities
2. **XRD Extension Planning**: Identify missing fields in XRDs
3. **Composition Mapping**: Map each Terraform resource to Crossplane managed resource
4. **Provider Capability Check**: Verify provider CRDs support needed resources
5. **Prioritization**: Determine migration order (Network → Cluster → Data → LB → Security → DNS)

---

**To be continued in**: `docs/migration/GAP-ANALYSIS.md`

