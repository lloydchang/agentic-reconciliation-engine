---
name: optimize-resources
description: Optimizes cloud resource utilization and costs across multi-cloud environments with intelligent analysis and automated recommendations. Use when reducing costs, improving efficiency, or right-sizing resources.
license: AGPLv3
metadata:
  author: gitops-infra-control-plane
  version: "1.0"
  category: enterprise
  risk-level: low
  autonomy: conditional
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Resource Optimizer — Multi-Cloud Cost and Performance Optimization

## Purpose
Enterprise-grade automation solution for resource optimization operations across AWS, Azure, GCP, and on-premise environments to maximize cost efficiency while maintaining performance and reliability standards.

## When to Use
- **resource optimization operations** across multi-cloud environments
- **Cost reduction and efficiency** improvement workflows
- **Resource right-sizing and scaling** recommendations
- **Performance optimization** and capacity planning
- **Compliance and governance** for resource utilization

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **cloudProvider**: Cloud provider - `aws|azure|gcp|onprem|all` (optional, default: `all`)
- **parameters**: Operation-specific parameters (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)

## Process
1. **Resource Discovery**: Identify and catalog all resources across providers
2. **Utilization Analysis**: Analyze current usage patterns and performance metrics
3. **Cost Analysis**: Evaluate spending patterns and identify optimization opportunities
4. **Recommendation Engine**: Generate intelligent optimization suggestions
5. **Risk Assessment**: Evaluate impact and risks of proposed changes
6. **Execution**: Apply optimizations with monitoring and rollback capabilities
7. **Validation**: Verify improvements and measure cost savings

## Outputs
- **Optimization Recommendations**: Detailed suggestions with cost savings estimates
- **Utilization Reports**: Current and historical resource usage analysis
- **Cost Analysis**: Spending patterns and optimization impact metrics
- **Performance Metrics**: Resource performance before and after optimization
- **Audit Trail**: Complete optimization history for compliance

## Environment
- **AWS**: Cost Explorer, CloudWatch, EC2, RDS, Lambda, S3
- **Azure**: Cost Management, Monitor, VMs, SQL Database, Functions
- **GCP**: Cloud Billing, Cloud Monitoring, Compute Engine, Cloud SQL
- **On-Premise**: Prometheus, Grafana, VMware, OpenStack monitoring
- **Multi-Cloud Tools**: Terraform, Ansible, Crossplane, Cluster API

## Dependencies
- **Python 3.8+**: Core execution environment
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Data Analysis**: pandas, numpy, matplotlib
- **Cost Analysis**: cloud-cost-attic, infracost
- **Kubernetes**: kubernetes client for cluster operations

## Scripts
- `core/core/automation/ci-cd/scripts/resource_optimizer.py`: Main optimization implementation
- `core/core/automation/ci-cd/scripts/resource_optimizer_handler.py`: Cloud-specific operations
- `core/core/automation/ci-cd/scripts/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
resource, optimization, cost, efficiency, savings, right-size, performance, multi-cloud, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment optimizations require approval
- **High-impact operations**: Critical resource modifications need review
- **Cost-sensitive changes**: Significant cost reductions need validation

## Enterprise Features
- **Multi-tenant Support**: Isolated optimization per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete optimization trail for compliance
- **Performance Monitoring**: SLA tracking and cost metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify optimization logic
- **Cross-Cloud Orchestration**: Coordinated optimizations across providers

## Best Practices
- **Gradual Optimization**: Implement changes in phases to minimize risk
- **Performance Validation**: Ensure optimizations don't impact performance
- **Cost Monitoring**: Track actual savings vs. projected savings
- **Rollback Planning**: Maintain ability to revert changes
- **Comprehensive Testing**: Validate recommendations before implementation
- **Security First**: Ensure optimizations don't compromise security posture
