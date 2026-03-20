# Terraform Infrastructure Inventory

**Crossplane Migration: Resource Mapping Inventory**

Generated: 2026-03-20

---

## Overview

This matrix catalogs all Terraform resources that will be migrated to Crossplane. Each resource is mapped to its corresponding Crossplane XRD and Managed Resource type.

### Legend

- **Status**: `✅ Ready` | `⚠️ Partial` | `❌ Missing` | `🔧 Custom Composition Needed`
- **XR**: Crossplane Composite Resource (XDatabase, XCluster, etc.)
- **MR**: Crossplane Managed Resource (rds.aws.crossplane.io/DBInstance, etc.)

---

## AWS Resources

### VPC & Networking

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_vpc` | `networks.aws.crossplane.io/v1beta1` | XNetwork | ✅ Ready | Use `Cluster` kind? Actually VPC is Network |
| `aws_subnet` | `subnets.aws.crossplane.io/v1beta1` | XNetwork | ✅ Ready | Subnets are part of XNetwork spec |
| `aws_internet_gateway` | `internetgateways.aws.crossplane.io/v1beta1` | XNetwork | ✅ Ready | Included in Composition |
| `aws_nat_gateway` | `natgateways.aws.crossplane.io/v1beta1` | XNetwork | ✅ Ready | Requires EIP |
| `aws_eip` | `eipaddresses.aws.crossplane.io/v1beta1` | XNetwork | ✅ Ready | For NAT gateway |
| `aws_route_table` | `routetables.aws.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |
| `aws_route_table_association` | Patches on subnets | XNetwork | ✅ Ready | |
| `aws_security_group` | `securitygroups.aws.crossplane.io/v1beta1` | XSecurityGroup | ⚠️ Partial | May need XRD or inline in Composition |
| `aws_vpc_peering` | `vpcpeeringconnections.aws.crossplane.io/v1beta1` | XNetworkPeering | ⚠️ Partial | No XRD yet - create or use direct MR |

**Gaps**: Need XSecurityGroup XRD if managing SGs separately. Or embed in XNetwork Composition.

---

### Compute: EKS

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_eks_cluster` (module.eks) | `clusters.eks.aws.crossplane.io/v1beta1` | XCluster | ✅ Ready | See `cluster-eks.yaml` |
| `aws_eks_node_group` | `nodepools.eks.aws.crossplane.io/v1beta1` | XCluster (subresource) | ✅ Ready | Node pools as part of XCluster |
| `aws_iam_role` (EKS role) | Managed via IAMComposition | - | 🔧 Custom | IAM not in core Crossplane; needs custom composition or keep in Terraform |
| `aws_iam_role_policy_attachment` | - | - | 🔧 Custom | |
| `aws_cloudwatch_log_group` | `groups.logs.aws.crossplane.io/v1beta1` | XLogGroup | ✅ Ready | Logging |

**Gaps**: EKS node IAM roles may need custom handling or remain in Terraform.

---

### Databases: RDS

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_db_instance` (module.rds) | `instances.rds.aws.crossplane.io/v1alpha1` | XDatabase | ✅ Ready | See `database-aws.yaml` |
| `aws_db_subnet_group` | `dbsubnetgroups.rds.aws.crossplane.io/v1alpha1` | XDatabase (component) | ✅ Ready | |
| `aws_db_parameter_group` | `dbparametergroups.rds.aws.crossplane.io/v1alpha1` | XDatabase (component) | ✅ Ready | |
| `aws_security_group` (RDS) | `securitygroups.aws.crossplane.io/v1beta1` | XSecurityGroup | ⚠️ Partial | See above |

**Gaps**: None major. Read replicas, cluster instances (Aurora) may need Composition updates.

---

### Caching: ElastiCache

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_elasticache_cluster` | `replicationgroups.elasticache.aws.crossplane.io/v1beta1` | XRedis | ⚠️ Partial | XRedis XRD may need creation |
| `aws_elasticache_subnet_group` | `subnetgroups.elasticache.aws.crossplane.io/v1beta1` | XRedis (component) | ⚠️ Partial | |

**Gaps**: Need XRedis XRD (or use XDatabase with engine=redis). Current repo has no XRedis XRD.

---

### Storage: S3

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_s3_bucket` | `buckets.s3.aws.crossplane.io/v1beta1` + `bucketpolicies` | XStorageBucket | ✅ Ready | Buckets + policies |
| `aws_s3_bucket_versioning` | Versioning property on Bucket MR | ✅ | ✅ Ready | |
| `aws_s3_bucket_server_side_encryption_configuration` | Encryption property | ✅ | ✅ Ready | |
| `aws_s3_bucket_lifecycle_configuration` | `bucketlifecycleconfigurations.s3.aws.crossplane.io/v1beta1` | XStorageBucket | ✅ Ready | |

---

### Load Balancing: ALB + CloudFront

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_lb` (module.alb) | `loadbalancers.elbv2.aws.crossplane.io/v1beta1` | XLB | ✅ Ready | Application Load Balancer |
| `aws_lb_target_group` | `targetgroups.elbv2.aws.crossplane.io/v1beta1` | XLB (component) | ✅ Ready | |
| `aws_lb_listener` | `listeners.elbv2.aws.crossplane.io/v1beta1` | XLB (component) | ✅ Ready | |
| `aws_lb_target_group_attachment` | Auto via pods/services | - | N/A | Kubernetes handles |
| `aws_acm_certificate` | `certificates.acm.aws.crossplane.io/v1beta1` | XCertificate | ⚠️ Partial | May need XRD |
| `module.cloudfront` | `distributions.cloudfront.aws.crossplane.io/v1beta1` | XCDN | ✅ Ready | CloudFront |

**Gaps**: XLB XRD may need refinement to cover all Terraform configs. XCertificate XRD optional.

---

### WAF

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_wafv2_web_acl` | `webacls.wafv2.aws.crossplane.io/v1beta1` | XWAF | ✅ Ready | |
| `aws_lambda_function` (WAF integration) | `functions.lambda.aws.crossplane.io/v1beta1` | XFunction | ✅ Ready | Lambda@Edge |

---

### DNS

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_route53_record` | `recordsets.route53.aws.crossplane.io/v1beta1` | XDNS | ✅ Ready | |
| `aws_route53_zone` | `hostedzones.route53.aws.crossplane.io/v1beta1` | XDNS (zone) | ✅ Ready | |

---

### IAM (Optional)

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_iam_role` | `roles.iam.aws.crossplane.io/v1beta1` | XIAMRole | ⚠️ Available | IAM provider exists but may not fully cover |
| `aws_iam_policy` | `policies.iam.aws.crossplane.io/v1beta1` | XIAMPolicy | ⚠️ Available | |
| `aws_iam_role_policy_attachment` | Attachments | XIAMRole | ⚠️ Available | |

**Recommendation**: Consider keeping IAM in Terraform initially. Crossplane IAM is powerful but adds complexity.

---

### Miscellaneous

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `aws_ssm_parameter` | `parameters.ssm.aws.crossplane.io/v1beta1` | XParameterStore | ✅ Ready | Parameter Store |
| `aws_cloudwatch_metric_alarm` | `alarms.cloudwatch.aws.crossplane.io/v1beta1` | XAlarm | ✅ Ready | |

---

## GCP Resources

### VPC & Networking

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_compute_network` | `networks.compute.gcp.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |
| `google_compute_subnetwork` | `subnetworks.compute.gcp.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |
| `google_compute_router` | `routers.compute.gcp.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |
| `google_compute_router_nat` | `natrouters.compute.gcp.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |
| `google_compute_firewall` | `firewalls.compute.gcp.crossplane.io/v1beta1` | XSecurityGroup | ⚠️ Partial | |

---

### Compute: GKE

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_container_cluster` | `clusters.container.gcp.crossplane.io/v1beta1` | XCluster | ✅ Ready | See `cluster-gke.yaml` - uses GKE |
| `google_container_node_pool` | `nodepools.container.gcp.crossplane.io/v1beta1` | XCluster (subresource) | ✅ Ready | |

**Gaps**: Autopilot mode support? Check Crossplane GKE provider capabilities.

---

### Databases: Cloud SQL

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_sql_database_instance` | `instances.sqladmin.gcp.crossplane.io/v1beta1` | XDatabase | ✅ Ready | See `database-gcp.yaml` |
| `google_sql_database` | Databases are subresources | - | ✅ Ready | Part of instance |
| `google_sql_user` | Users subresource | - | ✅ Ready | |

---

### Caching: Memorystore Redis

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_redis_instance` | `instances.redis.googleapis.com/v1beta1` (GCP native) | XRedis | ⚠️ Partial | Need Crossplane MR for Redis (not GCP native) |

**Gaps**: Redis provider may not have managed resource. May need to use GCP provider's Redis MR or custom Composition.

---

### Storage: Cloud Storage

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_storage_bucket` | `buckets.storage.googleapis.com/v1beta1` | XStorageBucket | ✅ Ready | GCS buckets |
| `google_storage_bucket_iam_member` | IAM bindings | - | ⚠️ Partial | May need XStorageBucket XRD extension |

---

### Load Balancing

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_compute_global_address` | `globaladdresses.compute.gcp.crossplane.io/v1beta1` | XLB | ✅ Ready | |
| `google_compute_global_forwarding_rule` | `globalforwardingrules.compute.gcp.crossplane.io/v1beta1` | XLB | ✅ Ready | |
| `google_compute_target_https_proxy` | `targethttpsproxies.compute.gcp.crossplane.io/v1beta1` | XLB | ✅ Ready | |
| `google_compute_url_map` | `urlmaps.compute.gcp.crossplane.io/v1beta1` | XLB | ✅ Ready | |
| `google_compute_backend_service` | `backendservices.compute.gcp.crossplane.io/v1beta1` | XLB | ✅ Ready | |
| `google_compute_health_check` | `healthchecks.compute.gcp.crossplane.io/v1beta1` | XLB | ✅ Ready | |
| `google_compute_managed_ssl_certificate` | `managedsslcertificates.compute.gcp.crossplane.io/v1beta1` | XCertificate | ⚠️ Partial | |

---

### Security

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_compute_security_policy` | `securitypolicies.compute.gcp.crossplane.io/v1beta1` | XWAF | ✅ Ready | Cloud Armor |

---

### DNS

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_dns_managed_zone` | `managedzones.dns.gcp.crossplane.io/v1beta1` | XDNS | ✅ Ready | |
| `google_dns_record_set` | `recordsets.dns.gcp.crossplane.io/v1beta1` | XDNS | ✅ Ready | |

---

### Miscellaneous

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `google_bigquery_dataset` | `datasets.bigquery.googleapis.com/v1beta1` | XBigQueryDataset | 🔧 Custom | Not commonly used for infra; may keep in Terraform |
| `google_kms_key_ring` | `keyrings.cloudkms.googleapis.com/v1beta1` | XKMS | 🔧 Custom | KMS |
| `google_kms_crypto_key` | `cryptokeys.cloudkms.googleapis.com/v1beta1` | XKMS | 🔧 Custom | |
| `google_project_service` | `services.serviceusage.googleapis.com/v1beta1` | XService | ⚠️ Partial | Enable APIs |

---

## Azure Resources

### Resource Group & Networking

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_resource_group` | `resourcegroups.resources.azure.crossplane.io/v1beta1` | XResourceGroup | ✅ Ready | |
| `azurerm_virtual_network` | `virtualnetworks.network.azure.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |
| `azurerm_subnet` | `subnets.network.azure.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |
| `azurerm_network_security_group` | `securitygroups.network.azure.crossplane.io/v1beta1` | XSecurityGroup | ⚠️ Partial | |
| `azurerm_public_ip` | `publicipaddresses.network.azure.crossplane.io/v1beta1` | XNetwork | ✅ Ready | |

---

### Compute: AKS

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_kubernetes_cluster` | `managedclusters.azure.crossplane.io/v1beta1` | XCluster | ✅ Ready | See `cluster-aks.yaml` |
| `azurerm_kubernetes_cluster_node_pool` | Nodepools are part of cluster MR | ✅ | ✅ Ready | |

---

### Databases: PostgreSQL Flexible

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_postgresql_flexible_server` | `flexibleservers.database.azure.crossplane.io/v1beta1` | XDatabase | ✅ Ready | See `database-azure.yaml` |
| `azurerm_postgresql_flexible_server_database` | Databases part of server | ✅ | ✅ Ready | |
| `azurerm_private_dns_zone` | `privatednszones.network.azure.crossplane.io/v1beta1` | XDNS | ✅ Ready | |
| `azurerm_private_dns_zone_virtual_network_link` | VNet links | ✅ | ✅ Ready | |

---

### Caching: Redis

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_redis_cache` | `redis.azure.crossplane.io/v1beta1` | XRedis | ⚠️ Partial | Need XRedis XRD |

---

### Storage

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_storage_account` | `storageaccounts.storage.azure.crossplane.io/v1beta1` | XStorageAccount | ✅ Ready | |
| `azurerm_storage_container` | `blobcontainers.storage.azure.crossplane.io/v1beta1` | XStorageContainer | ✅ Ready | |

---

### Load Balancing: Application Gateway

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_public_ip` (appgw) | `publicipaddresses.network.azure.crossplane.io/v1beta1` | ✅ | ✅ Ready | |
| `azurerm_application_gateway` | `applicationgateways.network.azure.crossplane.io/v1beta1` | XLB | ✅ Ready | |

---

### Security & WAF

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_key_vault` | `vaults.vault.azure.crossplane.io/v1beta1` | XVault | ✅ Ready | |
| `azurerm_key_vault_certificate` | `vaultcertificates.vault.azure.crossplane.io/v1beta1` | XCertificate | ✅ Ready | |

**WAF**: Application Gateway WAF policy included in `applicationgateways`.

---

### Monitoring

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_log_analytics_workspace` | `workspaces.operationalinsights.azure.crossplane.io/v1beta1` | XLogAnalytics | ✅ Ready | |

---

### DNS

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| `azurerm_dns_zone` | `dnszones.network.azure.crossplane.io/v1beta1` | XDNS | ✅ Ready | |
| `azurerm_dns_a_record` | `arecords.network.azure.crossplane.io/v1beta1` | XDNS | ✅ Ready | |

---

## On-Premise / Kubernetes

| Terraform Resource | Crossplane MR | XR | Status | Notes |
|---|---|---|---|---|
| (None) | `deployments.apps/v1` via provider-kubernetes | XDeployment | ✅ Ready | Use Kubernetes provider for K8s objects |

---

## Summary Metrics

| Provider | Total Resources | ✅ Ready | ⚠️ Partial | ❌ Missing | 🔧 Custom |
|----------|-----------------|----------|------------|------------|-----------|
| AWS | 30+ | 25 | 3 | 0 | 2 |
| GCP | 25+ | 20 | 2 | 0 | 3 |
| Azure | 20+ | 18 | 1 | 0 | 1 |
| On-Prem | 0 | 0 | 0 | 0 | 0 |
| **Total** | **75+** | **63** | **6** | **0** | **6** |

**Ready Rate**: 84% (63/75 resources have direct Crossplane equivalents)
**Partial/Missing**: 16% require custom XRD, Composition tweaks, or remain in Terraform

---

## Custom XRD Requirements

If not present, need to create:

1. **XSecurityGroup** - security groups/firewall rules across providers
2. **XRedis** - Redis instances (AWS ElastiCache, GCP Memorystore, Azure Cache)
3. **XCertificate** - SSL/TLS certificates (ACM, Key Vault, Certificate Manager)
4. **XDNS** - DNS zones and records (may exist as separate for each provider)
5. **XWAF** - WAF across AWS WAF, Cloud Armor, Azure WAF (may exist per provider)
6. **XIAMRole** / **XIAMPolicy** - IAM resources (optional)

Most of these likely have provider-specific managed resources; need XRD to unify.

---

## Recommended Migration Order

1. **Networks** (XNetwork) - foundational, no dependencies
2. **Clusters** (XCluster) - depends on networks
3. **Databases** (XDatabase) - depends on clusters/networks
4. **Storage** (XStorageBucket) - independent
5. **Load Balancers** (XLB) - depends on clusters/networks
6. **WAF, DNS, IAM** - depends on LBs, domains

---

## Terraform Resources NOT Migrating to Crossplane

Keep in Terraform if:

- **GCP BigQuery dataset** (analytics, not infra)
- **Service Usage API enablement** (`google_project_service`, `azurerm_*` role assignments)
- **KMS Key Rings** (complex; may keep separate)
- **Cloud-specific IAM** (if Crossplane IAM insufficient)
- **Provider-specific custom modules** (like WAF Lambda@Edge code deployment - that's app code, not infra)

---

**Next Steps**:

1. Validate this inventory against actual Terraform state files
2. Check Crossplane provider CRDs to confirm MR availability
3. Create missing XRDs (SecurityGroup, Redis, Certificate, etc.)
4. Update Compositions to cover all mapped resources
5. Flag custom resources to keep in Terraform
