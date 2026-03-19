---
name: network-multi-cloud
description: Manages networking configurations across multi-cloud environments with VPC peering, load balancing, and security rules. Use when setting up cloud networks, managing connectivity, or implementing network security.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: enterprise
  risk-level: medium
  autonomy: conditional
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Multi Cloud Networking — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for multi cloud networking operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **multi cloud networking operations** across multi-cloud environments
- **Automation and optimization** of multi cloud networking workflows
- **Monitoring and management** of multi cloud networking resources
- **Compliance and governance** for multi cloud networking activities

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **cloudProvider**: Cloud provider - `aws|azure|gcp|onprem|all` (optional, default: `all`)
- **parameters**: Operation-specific parameters (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)

## Process
1. **Cloud Provider Detection**: Identify target cloud providers and environments
2. **Input Validation**: Comprehensive parameter validation and security checks
3. **Multi-Cloud Context Analysis**: Analyze current state across all providers
4. **Operation Planning**: Generate optimized execution plan
5. **Safety Assessment**: Risk analysis and impact evaluation across providers
6. **Execution**: Perform operations with monitoring and validation
7. **Results Analysis**: Process results and generate reports

## Outputs
- **Operation Results**: Detailed execution results and status per provider
- **Compliance Reports**: Validation and compliance status across environments
- **Performance Metrics**: Operation performance and efficiency metrics by provider
- **Recommendations**: Optimization suggestions and next steps
- **Audit Trail**: Complete operation history for compliance across all providers

## Environment
- **AWS**: EKS, EC2, Lambda, CloudWatch, IAM, S3
- **Azure**: AKS, VMs, Functions, Monitor, Azure AD
- **GCP**: GKE, Compute Engine, Cloud Functions, Cloud Monitoring
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus
- **Multi-Cloud Tools**: Terraform, Ansible, Crossplane, Cluster API

## Dependencies
- **Python 3.8+**: Core execution environment
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Kubernetes**: kubernetes client for cluster operations
- **Multi-Cloud Libraries**: terraform-python, ansible-python

## Scripts
- `core/core/automation/ci-cd/scripts/multi-cloud-networking.py`: Main automation implementation
- `core/core/automation/ci-cd/scripts/multi-cloud-networking_handler.py`: Cloud-specific operations
- `core/core/automation/ci-cd/scripts/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
multi, cloud, networking, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment operations require approval
- **High-impact operations**: Critical operations require review
- **Security changes**: Security modifications need validation

## Enterprise Features
- **Multi-tenant Support**: Isolated operations per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify logic dynamically
- **Cross-Cloud Orchestration**: Coordinated operations across providers

## Best Practices
- **Idempotent Operations**: Safe retry mechanisms
- **Circuit Breaker Patterns**: Resilience against failures
- **Rate Limiting**: Respect API limits and implement backpressure
- **Graceful Degradation**: Fallback strategies when providers are unavailable
- **Comprehensive Testing**: Integration tests and compliance validation
- **Security First**: Zero-trust architecture and principle of least privilege
