# Crossplane Gap Analysis

## Executive Summary

This gap analysis compares the current Crossplane implementation (`core/operators/control-plane/crossplane/`) with the Terraform infrastructure inventory to identify missing capabilities and required XRD extensions.

**Current Crossplane State**: Existing XRDs and Compositions for XNetwork, XCluster, XDatabase, XQueue with basic implementations.
**Terraform Capabilities**: Comprehensive infrastructure with advanced networking, detailed cluster configuration, managed services (RDS, Redis, load balancers, WAF, DNS).
**Gap**: Crossplane needs XRD extensions and new XRD definitions to achieve parity with Terraform.

---

## 1. XNetwork Gap Analysis

### Current XNetwork (`xrds/xnetwork.yaml`)

**Schema**:
```yaml
spec:
  required: [cidr, region]
  properties:
    cidr: string
    region: string
    subnetCidrs: string[]
```

**Terraform Capabilities Not Covered**:

| Feature | Terraform Resource | Crossplane Gap | Priority |
|---|---|---|---|
| **NAT Gateway** | `module.vpc.nat_gateways` (AWS) / `google_compute_router_nat` (GCP) / `azurerm_nat_gateway` (Azure) | No NAT resource in composition | HIGH |
| **Internet Gateway** | `module.vpc.igw` | IGW creation in AWS composition incomplete | HIGH |
| **Route Tables** | `module.vpc.private_route_tables` / `public_route_tables` | No route table resources | HIGH |
| **Security Groups** | `aws_security_group.*` | SG only mentioned in database/cluster compositions, not in XNetwork | HIGH |
| **VPC Peering** | `aws_vpc_peering_connection` / equivalent | Not supported in XRD | MEDIUM |
| **DNS Resolution** | `enable_dns_hostnames`, `enable_dns_support` | Fields exist but may need validation | MEDIUM |
| **Flow Logs** | VPC Flow Logs, NSG Flow Logs | Not in XRD | LOW |
| **Private DNS Zones** | `google_dns_managed_zone`, `azurerm_private_dns_zone` | Should be separate XRD (XDNS) | MEDIUM |
| **VPN / Transit Gateway** | `azurerm_virtual_network_gateway`, `aws_ec2_transit_gateway` | Out of scope for XNetwork? | LOW |

### Current Compositions

- `network-aws.yaml`: Creates VPC + 3 subnets only. Missing NAT, IGW, route tables, SGs.
- `network-gcp.yaml`: Creates VPC + subnets. Missing Cloud Router, Cloud NAT, firewall rules.
- `network-azure.yaml`: Creates VNet + subnets. Missing NAT gateway, VPN gateway, NSG.

### Required XRD Extensions

Add to `xnetwork.yaml`:

```yaml
spec:
  properties:
    # Existing fields...
    enableDnsHostnames: boolean
    enableDnsSupport: boolean

    # NAT Gateway
    enableNat: boolean
    natGatewayType: string  # enum: ["managed", "self-managed"]

    # Internet Gateway
    enableInternetGateway: boolean

    # Route Tables
    routeTables:
      type: array
      items:
        type: object
        properties:
          name: string
          routes:
            type: array
            items:
              type: object
              properties:
                destinationCidr: string
                nextHopType: string  # "internet-gateway", "nat-gateway", "instance", "vpcconnection"
                nextHopId: string

    # Security Groups (as part of network, or separate XRD?)
    securityGroups:
      type: array
      items:
        type: object
        properties:
          name: string
          description: string
          ingressRules:
            type: array
            items:
              type: object
              properties:
                protocol: string
                fromPort: integer
                toPort: integer
                cidrBlocks: string[]
          egressRules: [...]
```

---

## 2. XCluster Gap Analysis

### Current XCluster (`xrds/xcluster.yaml`)

**Schema**:
```yaml
spec:
  required: [nodeCount, nodeSize, kubernetesVersion, region]
  properties:
    nodeCount: integer
    nodeSize: enum[small, medium, large]
    kubernetesVersion: string
    region: string
    networkRef: object
    deletionPolicy: string
```

**Terraform Capabilities Not Covered**:

| Feature | Terraform Configuration | Crossplane Gap | Priority |
|---|---|---|---|
| **Multiple Node Pools** | `eks_managed_node_groups` with general + spot | Single node pool only | HIGH |
| **Autoscaling** | `min_size`, `max_size`, `desired_size` per pool | Only `nodeCount` | HIGH |
| **Instance Types** | `instance_types` list | Single `nodeSize` enum too limited | HIGH |
| **Disk Configuration** | Not in Terraform? (defaults) | Disk size, type missing | MEDIUM |
| **Labels & Taints** | `tags` in node group | Not in XRD | MEDIUM |
| **GPU Support** | Could add GPU instance types | Not in XRD | LOW |
| **Fargate Profiles** | `fargate_profiles` | Not in XRD | MEDIUM |
| **Cluster Add-ons** | EKS managed add-ons (vpc-cni, coredns, kube-proxy) | Not in XRD | HIGH |
| **Endpoint Access** | `private_cluster_config` | Private vs public access missing | HIGH |
| **OIDC/IAM** | `workload_identity_config` (GKE), IAM roles (EKS) | Not in XRD | HIGH |
| **Logging** | `resource_usage_export_config`, CloudWatch | Not in XRD | MEDIUM |
| **Monitoring** | CloudWatch, Azure Monitor integration | Not in XRD | MEDIUM |
| **Binary Authorization** | (GKE) | Not in XRD | LOW |
| **Shielded Nodes** | (EKS, GKE) | Not in XRD | LOW |
| **Maintenance Window** | `maintenance_policy` | Not in XRD | MEDIUM |

### Required XRD Extensions

Add to `xcluster.yaml`:

```yaml
spec:
  properties:
    # Existing...
    kubernetesVersion: string

    # Replace simple nodeCount with detailed nodePools
    nodePools:
      type: array
      items:
        type: object
        required: [name, instanceType]
        properties:
          name: string
          instanceType: string  # e.g., "t3.large", "e2-standard-2"
          minSize: integer
          maxSize: integer
          desiredSize: integer  # For non-autoscaling, just use min=max=desired
          diskSizeGb: integer
          diskType: string  # "gp3", "standard", etc.
          labels:
            type: object
          taints:
            type: array
            items:
              type: object
              properties:
                key: string
                value: string
                effect: string
          capacityType: string  # enum: ["ON_DEMAND", "SPOT", "RESERVED"]
          tags:
            type: object

    # Single-node pool legacy support (deprecated)
    nodeCount: integer  # Keep for backward compatibility?
    nodeSize: string

    # Cluster configuration
    endpointAccess:
      type: object
      properties:
        private: boolean
        public: boolean  # if both false, use private only with VPC endpoint

    addons:
      type: array
      items:
        type: object
        properties:
          name: string  # "vpc-cni", "coredns", "kube-proxy", "ebs-csi", "efs-csi"
          version: string
          configuration: object

    logging:
      type: object
      properties:
        enableClusterLogging: boolean
        logTypes:
          type: array
          items:
            type: string  # "api", "audit", "app", "controllerManager"

    monitoring:
      type: object
      properties:
        enableManagedPrometheus: boolean
        enableCloudWatch (Azure/GCP equivalent)

    identity:
      type: object
      properties:
        oidc:
          type: object
          properties:
            issuerUrl: string
            clientId: string
        iam:
          type: object
          properties:
            roleArn: string  # AWS IAM role for EKS

    maintenance:
      type: object
      properties:
        window:
          type: string  # CRON expression or "Sun:03:00-Sun:04:00"
        day: string
        hour: integer
```

---

## 3. XDatabase Gap Analysis

### Current XDatabase (`xrds/xdatabase.yaml`)

**Schema**:
```yaml
spec:
  required: [engine, version, size]
  properties:
    engine: enum[postgres, mysql]
    version: string
    size: enum[small, medium, large]
    region: string
    deletionPolicy: string
```

**Terraform Capabilities Not Covered**:

| Feature | Terraform Configuration | Crossplane Gap | Priority |
|---|---|---|---|
| **Backup Configuration** | `backup_configuration { enabled, start_time }` | Not in XRD | HIGH |
| **Multi-AZ / HA** | `multi_az = var.environment == "prod"` | Not in XRD | HIGH |
| **Maintenance Window** | `maintenance_window { day, hour }` | Not in XRD | MEDIUM |
| **Encryption** | `disk_encryption` (RDS), KMS keys | Not in XRD | HIGH |
| **Parameter Groups** | `database_flags { name, value }` | Not in XRD | MEDIUM |
| **Option Groups** | (RDS option groups for MySQL) | Not in XRD | LOW |
| **Performance Insights** | `insights_config { query_insights_enabled }` | Not in XRD | MEDIUM |
| **Enhanced Monitoring** | `monitoring_interval`, `monitoring_role_name` | Not in XRD | MEDIUM |
| **Read Replicas** | Separate Terraform resources | Not in XRD | MEDIUM |
| **Connectivity** | `ip_configuration`, `vpc_security_group_ids`, `private_network` | Networking fields missing | HIGH |
| **Storage Configuration** | `allocated_storage`, `storage_type`, `iops` | Only `size` enum insufficient | HIGH |
| **Public Access** | `publicly_accessible` | Not in XRD | MEDIUM |
| **Deletion Protection** | `deletion_protection` | Not in XRD | MEDIUM |

### Current Compositions

- `database-aws.yaml`: Basic RDS with DBSubnetGroup, minimal config. Missing backups, monitoring, HA, encryption, parameter groups.
- `database-gcp.yaml`: Basic CloudSQL, mostly placeholder.
- `database-azure.yaml`: Basic PostgreSQL Flexible Server, missing HA, backups, maintenance.

### Required XRD Extensions

Add to `xdatabase.yaml`:

```yaml
spec:
  properties:
    # Existing...
    engine: enum[postgres, mysql, mariadb, sqlserver]
    version: string
    size: enum[small, medium, large, xlarge, 2xlarge]  # Expand!

    # Storage
    storage:
      type: object
      properties:
        type: string  # "gp2", "gp3", "io1", "standard"
        sizeGb: integer
        iops: integer
        throughput: integer  # For gp3

    # High Availability
    highAvailability:
      type: object
      properties:
        enabled: boolean
        mode: string  # "multi-az", "zone-redundant", "ha"
        standbyCount: integer

    # Backups
    backup:
      type: object
      properties:
        enabled: boolean
        retentionDays: integer
        window: string  # "03:00-04:00"
        type: string  # "automated", "manual"
        pointInTimeRecovery:
          type: boolean

    # Maintenance
    maintenance:
      type: object
      properties:
        window: string  # "Sun:03:00-Sun:04:00"
        day: string
        hour: integer
        preferred: boolean

    # Security
    encryption:
      type: object
      properties:
        enabled: boolean
        type: string  # "aws:kms", "azure-keyvault", "gcp-kms"
        keyId: string  # KMS key ARN/ID

    deletionProtection:
      type: boolean

    # Networking
    network:
      type: object
      properties:
        vpcId: string  # Or networkRef name?
        subnetIds: string[]
        securityGroupIds: string[]
        privateAccessOnly: boolean
        assignPublicIp: boolean

    # Database Flags/Parameters
    parameterGroup:
      type: object
      properties:
        name: string
        family: string
        parameters:
          type: array
          items:
            type: object
            properties:
              name: string
              value: string

    # Option Group (RDS-specific)
    optionGroup:
      type: object
      properties:
        name: string

    # Performance & Monitoring
    performance:
      type: object
      properties:
        insightsEnabled: boolean
        insightsRetentionDays: integer
        monitoringInterval: integer  # seconds
        monitoringRoleArn: string

    # Replication
    readReplicas:
      type: array
      items:
        type: object
        properties:
          count: integer
          size: string

```

---

## 4. XRedis Gap Analysis

### Current State

**No XRedis XRD exists**. Redis resources are scattered:
- AWS: `aws_elasticache_cluster` in Terraform
- GCP: `google_redis_instance` in Terraform
- Azure: `azurerm_redis_cache` in Terraform
- Compositions: None (only database compositions for RDS/CloudSQL/AzureDB)

### Recommendation

**Option A**: Extend XDatabase XRD with `engine: redis` (simpler, but Redis has different semantics)
**Option B**: Create separate XRedis XRD (cleaner separation)

**Preferred**: Create separate XRedis XRD because Redis configuration differs significantly from relational databases (cluster mode, replication, persistence, eviction policies).

### Required XRD: XRedis

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xredises.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XRedis
    plural: xredises
  claimNames:
    kind: Redis
    plural: redises
  connectionSecretKeys:
    - host
    - port
    - password
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: [size, region]
            properties:
              size:
                type: string
                enum: [small, medium, large]  # Map to cache.t3.micro, etc.
              region: string
              version:
                type: string
                default: "6.x"  # Redis version
              # HA / Replication
              ha:
                type: object
                properties:
                  enabled: boolean
                  replicationGroup: boolean  # For cluster mode
                  replicaCount: integer
                  automaticFailover: boolean
              # Networking
              network:
                type: object
                properties:
                  vpcId: string
                  subnetIds: string[]
                  securityGroupIds: string[]
                  privateAccess: boolean
              # Security
              auth:
                type: object
                properties:
                  type: string  # "password", "acl", "both"
                  passwordSecretRef:
                    namespace: string
                    name: string
                    key: string
              # Persistence
              persistence:
                type: object
                properties:
                  rdb:
                    type: object
                    properties:
                      enabled: boolean
                      snapshotRetention: integer
                      snapshotWindow: string
                  aof:
                    type: object
                    properties:
                      enabled: boolean
              # Eviction Policy
              evictionPolicy:
                type: string
                enum: ["noeviction", "allkeys-lru", "volatile-lru", "allkeys-random", "volatile-random", "volatile-ttl"]
              # Encryption
              encryption:
                type: object
                properties:
                  inTransit:
                    type: boolean
                  atRest:
                    type: boolean
                  kmsKeyId: string
              deletionPolicy:
                type: string
                enum: [Delete, Orphan]
                default: Orphan
          status:
            type: object
            properties:
              host: string
              port: integer
              endpoint: string
              sslEnabled: boolean
```

---

## 5. XStorageBucket Gap Analysis

### Current State

**No XStorageBucket XRD exists**. Storage handled separately in Terraform, not in Crossplane (except maybe generic bucket resources).

### Recommendation

Create XStorageBucket XRD for object storage across clouds.

### Required XRD: XStorageBucket

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xstoragebuckets.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XStorageBucket
    plural: xstoragebuckets
  claimNames:
    kind: StorageBucket
    plural: storagebuckets
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: [region]
            properties:
              region: string
              # Versioning
              versioning:
                type: object
                properties:
                  enabled: boolean
                  suspended: boolean
              # Encryption
              encryption:
                type: object
                properties:
                  type: string  # "SSE-S3", "SSE-KMS", "SSE-C"
                  kmsKeyId: string
                  customerManagedKey: boolean
              # Lifecycle
              lifecycle:
                type: object
                properties:
                  rules:
                    type: array
                    items:
                      type: object
                      properties:
                        id: string
                        status: boolean
                        expiration:
                          type: object
                          properties:
                            days: integer
                            expiredObjectDeleteMarker: boolean
                        transition:
                          type: array
                          items:
                            type: object
                            properties:
                              days: integer
                              storageClass: string  # "STANDARD_IA", "GLACIER", etc.
              # Access Control
              publicAccessBlock:
                type: object
                properties:
                  blockPublicAcls: boolean
                  blockPublicPolicy: boolean
                  ignorePublicAcls: boolean
                  restrictPublicBuckets: boolean
              # CORS
              cors:
                type: array
                items:
                  type: object
                  properties:
                    allowedOrigins: string[]
                    allowedMethods: string[]
                    allowedHeaders: string[]
                    maxAgeSeconds: integer
              # Logging
              logging:
                type: object
                properties:
                  targetBucket: string
                  targetPrefix: string
              # Bucket Policy / ACL
              acl: string  # "private", "public-read", etc.
              bucketPolicy:
                type: object
                properties:
                  statement:
                    type: array
                    items:
                      type: object
                      properties:
                        sid: string
                        effect: string
                        principals: object
                        actions: string[]
                        resources: string[]
              deletionPolicy:
                type: string
                enum: [Delete, Orphan]
                default: Orphan
          status:
            type: object
            properties:
              bucketName: string
              bucketArn: string
              endpoint: string
              region: string
```

---

## 6. XLoadBalancer Gap Analysis

### Current State

**No XLB XRD exists**. Load balancers not in Crossplane yet.

### Required XRD: XLoadBalancer

Cloud-specific LBs:
- AWS: Application Load Balancer (ALB) + Network Load Balancer (NLB)
- GCP: Cloud Load Balancing (HTTP(S), TCP, UDP)
- Azure: Application Gateway (Layer 7) + Load Balancer (Layer 4)

Create XRD for HTTP(S) load balancers primarily.

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xloadbalancers.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XLoadBalancer
    plural: xloadbalancers
  claimNames:
    kind: LoadBalancer
    plural: loadbalancers
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: [listeners]
            properties:
              # Provider selection
              provider: string  # aws, gcp, azure (or use compositionSelector)
              # LB Type
              type: string  # "application", "network", "gateway"
              # Listeners
              listeners:
                type: array
                items:
                  type: object
                  required: [port, protocol]
                  properties:
                    port: integer
                    protocol: string  # "HTTP", "HTTPS", "TCP", "TLS"
                    targetPort: integer
                    targetProtocol: string  # defaults to protocol
                    sslPolicy: string  # AWS: ELBSecurityPolicy-...
                    certificateArn: string  # For HTTPS
                    caCertificateArn: string  # For mutual TLS
              # Default backend / target groups
              defaultBackend:
                type: object
                properties:
                  service:
                    type: object
                    properties:
                      name: string
                      namespace: string
                      port: integer
                  healthCheck:
                    type: object
                    properties:
                      path: string
                      port: integer
                      protocol: string
                      intervalSeconds: integer
                      timeoutSeconds: integer
                      healthyThresholdCount: integer
                      unhealthyThresholdCount: integer
              # Advanced routing
              hostRules:
                type: array
                items:
                  type: object
                  properties:
                    host: string
                    pathRules:
                      type: array
                      items:
                        type: object
                        properties:
                          path: string
                          serviceName: string
                          servicePort: integer
              # WAF integration
              wafEnabled: boolean
              wafAclId: string
              # Session affinity
              sessionAffinity: string  # "none", "source_ip"
              # Cross-zone load balancing
              crossZoneLoadBalancing:
                type: object
                properties:
                  enabled: boolean
              deletionPolicy:
                type: string
                enum: [Delete, Orphan]
                default: Orphan
          status:
            type: object
            properties:
              dnsName: string
              zoneId: string
              hostname: string
              ipAddresses: string[]
              canonicalHostedZoneId: string  # For CloudFront/CloudFront-like

```

---

## 7. XWAF Gap Analysis

### Current State

**No XWAF XRD exists**. WAF managed directly in Terraform (AWS WAFv2, Cloud Armor).

### Required XRD: XWAF

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xwafs.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XWAF
    plural: xwafs
  claimNames:
    kind: WAF
    plural: wafs
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: [provider, scope]
            properties:
              provider: string  # "aws", "gcp", "azure"
              scope: string  # "CLOUDFRONT", "REGIONAL", "GLOBAL"
              defaultAction:
                type: object
                properties:
                  allow: boolean  # true = allow, false = block implicitly
              # Rules
              rules:
                type: array
                items:
                  type: object
                  required: [priority, action]
                  properties:
                    priority: integer
                    name: string
                    statement:
                      type: object
                      properties:
                        # Could be managed rule group or custom
                        managedRuleGroup:
                          type: object
                          properties:
                            vendorName: string
                            name: string
                            version: string
                            excludedRules: string[]
                        # OR custom rule
                        byteMatchStatement: object
                        sqliMatchStatement: object
                        xssMatchStatement: object
                        rateBasedStatement: object
                        ipSetReferenceStatement: object
                        sizeConstraintStatement: object
                        geoMatchStatement: object
                        labelMatchStatement: object
                    action:
                      type: object
                      properties:
                        allow: boolean
                        block: boolean
                        count: boolean
                    visibilityConfig:
                      type: object
                      properties:
                        sampledRequestsEnabled: boolean
                        cloudWatchMetricsEnabled: boolean
                        metricName: string
                # Rule group association
              ruleGroups:
                type: array
                items:
                  type: object
                  properties:
                    name: string
                    priority: integer
                    statement:
                      type: object
                      properties:
                        managedRuleGroup:
                          vendorName: string
                          name: string
                          version: string
              # Viewing capacity for request sampling
              visibilityConfig:
                type: object
                properties:
                  sampledRequestsEnabled: boolean
                  cloudWatchMetricsEnabled: boolean
              deletionPolicy:
                type: string
                enum: [Delete, Orphan]
                default: Orphan
          status:
            type: object
            properties:
              wafId: string
              arn: string
              webAclId: string  # AWS-specific

```

---

## 8. XDNS Gap Analysis

### Current State

**No XDNS XRD exists**. DNS managed in Terraform (Route53, Cloud DNS, Azure DNS).

### Required XRD: XDNS

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xdnses.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XDNS
    plural: xdnses
  claimNames:
    kind: DNS
    plural: dnses
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: [zone, recordSets]
            properties:
              provider: string  # "aws", "gcp", "azure"
              # Hosted Zone
              zone:
                type: object
                required: [name]
                properties:
                  name: string  # "example.com."
                  description: string
                  # private zone configuration
                  private:
                    type: boolean
                    vpcs:
                      type: array
                      items:
                        type: object
                        properties:
                          vpcId: string
                          region: string
              # Record Sets
              recordSets:
                type: array
                items:
                  type: object
                  required: [name, type, ttl, records]
                  properties:
                    name: string  # "www.example.com" or "@" for apex
                    type: string  # "A", "AAAA", "CNAME", "MX", "TXT", "SRV", etc.
                    ttl: integer
                    records:
                      type: array
                      items:
                        type: string
                    # Weighted/Geolocation routing
                    routingPolicy:
                      type: object
                      properties:
                        weight: integer
                        geolocation:
                          type: object
                          properties:
                            continent: string
                            country: string
                            subdivision: string
                    # Health checks for failover
                    healthCheckId: string
                    failover: string  # "PRIMARY", "SECONDARY"
                    alias:
                      type: object
                      properties:
                        dnsName: string
                        hostedZoneId: string
                        evaluateTargetHealth: boolean
              deletionPolicy:
                type: string
                enum: [Delete, Orphan]
                default: Orphan
          status:
            type: object
            properties:
              zoneId: string
              nameServerIds: string[]
              recordSetIds: string[]

```

---

## 9. Provider Capability Assessment

### AWS Provider (`provider-aws`)

**Installed Version**: v0.50.0 (from existing `provider-aws.yaml`)

**Required Managed Resources**:

| Resource | Needed? | Crossplane CRD | Status |
|---|---|---|
| EC2 Instance | Maybe | `instances.ec2.aws.crossplane.io/v1beta1` | Available |
| EKS Cluster | ✅ | `clusters.eks.aws.crossplane.io/v1beta1` | Available |
| RDS (Postgres/MySQL) | ✅ | `databases.rds.aws.crossplane.io/v1alpha1` | Available |
| ElastiCache Redis | ✅ | `elasticacheclusters.cache.aws.crossplane.io/v1beta1` | Available |
| S3 Bucket | ✅ | `buckets.s3.aws.crossplane.io/v1beta1` | Available |
| VPC | ✅ | `networks.ec2.aws.crossplane.io/v1beta1` | Available |
| Subnets | ✅ | `subnets.ec2.aws.crossplane.io/v1beta1` | Available |
| NAT Gateway | ✅ | `natgateways.ec2.aws.crossplane.io/v1beta1` | Check availability |
| Internet Gateway | ✅ | `internetgateways.ec2.aws.crossplane.io/v1beta1` | Check availability |
| Route Tables | ✅ | `routetables.ec2.aws.crossplane.io/v1beta1` | Check availability |
| Security Groups | ✅ | `securitygroups.ec2.aws.crossplane.io/v1beta1` | Check availability |
| ALB / ELBv2 | ✅ | `loadbalancers.elbv2.aws.crossplane.io/v1beta1` | Available |
| ACM Certificate | Optional | `certificates.acm.aws.crossplane.io/v1beta1` | Check availability |
| WAFv2 | ✅ | `webacls.wafv2.aws.crossplane.io/v1beta1` | Available |
| CloudFront | Optional | `distributions.cloudfront.aws.crossplane.io/v1beta1` | Check availability |
| Route53 | ✅ | `recordsets.route53.aws.crossplane.io/v1beta1` | Available |
| KMS Keys | Optional | `keys.kms.aws.crossplane.io/v1beta1` | Available |

**Gap**: Verify NAT Gateway, Internet Gateway, Route Tables, Security Groups CRDs exist in provider-aws v0.50.0.

### GCP Provider (`provider-gcp`)

**Installed Version**: Need to check existing `provider-gcp.yaml`

**Required Managed Resources**:

| Resource | Needed? | Crossplane CRD | Status |
|---|---|---|
| GKE Cluster | ✅ | `clusters.container.gcp.crossplane.io/v1beta1` | Available |
| Cloud SQL | ✅ | `databases.sqladmin.gcp.crossplane.io/v1beta1` | Available |
| Memorystore Redis | ✅ | `instances.redis.googleapis.com/v1beta1` (GCP native API group) | Check |
| GCS Bucket | ✅ | `buckets.storage.googleapis.com/v1beta1` | Available |
| VPC Network | ✅ | `networks.compute.gcp.crossplane.io/v1beta1` | Available |
| Subnets | ✅ | `subnetworks.compute.gcp.crossplane.io/v1beta1` | Available |
| Cloud Router | ✅ | `routers.compute.gcp.crossplane.io/v1beta1` | Available |
| Cloud NAT | ✅ | `natrouters.networkservices.cloud.google.com/v1beta1`? | Check |
| Firewall Rules | ✅ | `firewalls.compute.gcp.crossplane.io/v1beta1` | Available |
| Cloud Load Balancer | ✅ | `forwardingrules.compute.gcp.crossplane.io/v1beta1` | Available |
| Cloud Armor | ✅ | `securitypolicies.compute.gcp.crossplane.io/v1beta1` | Available |
| Cloud DNS | ✅ | `recordsets.dns.googleapis.com/v1beta1` | Available |
| Cloud KMS | Optional | `cryptoKeys.cloudkms.googleapis.com/v1beta1` | Check |

### Azure Provider (`provider-azure`)

**Required Managed Resources**:

| Resource | Needed? | Crossplane CRD | Status |
|---|---|---|
| AKS Cluster | ✅ | `managedclusters.azure.crossplane.io/v1beta1` | Available |
| PostgreSQL Flexible Server | ✅ | `flexibleservers.database.azure.crossplane.io/v1beta1` | Available |
| Azure Cache for Redis | ✅ | `redis.azure.crossplane.io/v1beta1` | Check availability |
| Storage Account | ✅ | `storageaccounts.storage.azure.crossplane.io/v1beta1` | Available |
| Virtual Network | ✅ | `virtualnetworks.network.azure.crossplane.io/v1beta1` | Available |
| Subnets | ✅ | `subnets.network.azure.crossplane.io/v1beta1` | Available |
| NAT Gateway | ✅ | `natgateways.network.azure.crossplane.io/v1beta1` | Check availability |
| Network Security Groups | ✅ | `networksecuritygroups.network.azure.crossplane.io/v1beta1` | Available |
| Application Gateway | ✅ | `applicationgateways.network.azure.crossplane.io/v1beta1` | Available |
| Load Balancer | ✅ | `loadbalancers.network.azure.crossplane.io/v1beta1` | Available (standard SKU) |
| Private DNS Zones | ✅ | `privatednszones.network.azure.crossplane.io/v1beta1` | Available |
| Key Vault | Optional | `vaults.azure.crossplane.io/v1beta1` | Check availability |

---

## 10. Missing Managed Resource Summary

### HIGH Priority (Blocking Migration)

1. **XNetwork extensions**: NAT, IGW, route tables, security groups
2. **XCluster extensions**: Node pools, autoscaling, add-ons, endpoint access
3. **XDatabase extensions**: Backups, HA, maintenance, encryption, networking
4. **XRedis XRD**: Separate Redis resource definition
5. **XStorageBucket XRD**: Object storage across clouds

### MEDIUM Priority (After HIGH)

6. **XLoadBalancer XRD**: ALB/NLB/App Gateway
7. **XWAF XRD**: WAF across clouds
8. **XDNS XRD**: DNS zones and records
9. **Provider resources verification**: Confirm NAT, route tables, SGs available in provider CRDs

### LOW Priority (Nice to have)

10. XCertificate XRD (for SSL certs across clouds)
11. XSecret XRD (for secret management abstraction)
12. XMonitoring XRD (for metrics, logs, alerts)

---

## 11. Composition Gaps

### Network Compositions Need:

- [ ] AWS: Add NAT Gateway, IGW, route tables (public/private), security groups
- [ ] GCP: Add Cloud Router, Cloud NAT, firewall rules
- [ ] Azure: Add NAT gateway, NSG, route tables

### Cluster Compositions Need:

- [ ] AWS: Expand node groups, add-ons, OIDC, logging, endpoint access
- [ ] GCP: Expand node pools, add-ons, logging, binary authorization
- [ ] Azure: Expand node pools, auto-scaling, Azure Monitor, AAD integration

### Database Compositions Need:

- [ ] AWS: Add subnet group (already there but needs expansion), backup config, monitoring, HA, encryption
- [ ] GCP: Add backup config, private network, maintenance window, flags
- [ ] Azure: Add HA (ZoneRedundant), backup retention, maintenance window, high availability config

### New Compositions to Create:

- [ ] `redis-aws.yaml`, `redis-azure.yaml`, `redis-gcp.yaml`
- [ ] `storagebucket-aws.yaml`, `storagebucket-azure.yaml`, `storagebucket-gcp.yaml`
- [ ] `lb-aws.yaml`, `lb-azure.yaml`, `lb-gcp.yaml`
- [ ] `waf-aws.yaml`, `waf-azure.yaml`, `waf-gcp.yaml`
- [ ] `dns-aws.yaml`, `dns-azure.yaml`, `dns-gcp.yaml`

---

## 12. Implementation Order & Priorities

### Phase 1: XRD Extensions (Week 2-3)
1. Extend XNetwork with NAT, IGW, routes, SGs
2. Extend XCluster with node pools, autoscaling, add-ons
3. Extend XDatabase with backups, HA, encryption, networking

### Phase 2: New XRD Definitions (Week 4)
4. Create XRedis XRD + compositions
5. Create XStorageBucket XRD + compositions

### Phase 3: Advanced Services (Week 5-6)
6. Create XLB XRD + compositions
7. Create XWAF XRD + compositions
8. Create XDNS XRD + compositions

### Phase 4: Provider Verification & Testing (Ongoing)
- Validate all CRDs exist in installed provider versions
- Test each composition in dev environment
- Update provider versions if needed

---

**Next Steps**:
1. Review gap analysis with team
2. Prioritize XRD extensions based on migration phases
3. Begin implementing XNetwork extension first (migration Phase 2 starts with networks)
4. Verify provider CRD availability before writing compositions

**To be continued in**: Implementation of XRD extensions

---

**Document Owners**: Platform Engineering Team
**Last Updated**: 2026-03-20
**Status**: Draft
