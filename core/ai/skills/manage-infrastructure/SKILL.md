---
name: manage-infrastructure
description: AI-powered infrastructure management skill with intelligent resource allocation, predictive scaling, and automated optimization. Use when managing cloud resources with advanced AI capabilities for proactive infrastructure management and cost optimization.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "2.0"
  category: enterprise
  risk_level: medium
  autonomy: conditional
  layer: temporal
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Infrastructure Manager — AI-Powered Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for infrastructure manager operations across AWS, Azure, GCP, and on-premise environments with advanced AI capabilities including intelligent resource allocation, predictive scaling, and automated optimization to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **AI-powered infrastructure management** across multi-cloud environments
- **Predictive scaling** and intelligent resource allocation
- **Automated infrastructure optimization** using ML and predictive analytics
- **Proactive infrastructure monitoring** with anomaly detection
- **Cost optimization** through AI-driven resource management
- **Infrastructure automation** with intelligent decision-making
- **Compliance and governance** for infrastructure manager activities

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **cloudProvider**: Cloud provider - `aws|azure|gcp|onprem|all` (optional, default: `all`)
- **parameters**: Operation-specific parameters including AI model configurations (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)
- **aiMode**: Enable AI-powered analysis and recommendations (optional, default: `true`)

## Process
1. **Cloud Provider Detection**: Identify target cloud providers and environments
2. **Input Validation**: Comprehensive parameter validation and security checks
3. **AI-Powered Analysis**: Apply ML algorithms for intelligent resource analysis
4. **Predictive Planning**: Generate optimized execution plan with AI insights
5. **Risk Assessment**: AI-enhanced risk analysis and impact evaluation
6. **Intelligent Execution**: Perform operations with AI monitoring and validation
7. **Results Analysis**: Process results and generate AI-enhanced reports
8. **Learning Integration**: Update AI models with operational outcomes

## Outputs
- **AI-Enhanced Operation Results**: Detailed execution results with AI insights
- **Predictive Analytics**: Infrastructure performance predictions and forecasts
- **Intelligent Recommendations**: AI-generated optimization suggestions
- **Anomaly Detection**: Infrastructure anomalies and potential issues
- **Cost Optimization**: AI-powered cost analysis and savings opportunities
- **Compliance Reports**: Validation and compliance status with AI insights
- **Audit Trail**: Complete operation history for compliance across all providers

## Environment
- **AWS**: EKS, EC2, Lambda, CloudWatch, IAM, S3, Auto Scaling
- **Azure**: AKS, VMs, Functions, Monitor, Azure AD, Autoscale
- **GCP**: GKE, Compute Engine, Cloud Functions, Cloud Monitoring, Cloud Run
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus, HPA
- **Multi-Cloud Tools**: Terraform, Ansible, Crossplane, Cluster API

## Dependencies
- **Python 3.8+**: Core execution environment
- **AI/ML Libraries**: scikit-learn, pandas, numpy, statsmodels, tensorflow/keras
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Time Series Libraries**: prophet, pmdarima for predictive analysis
- **Kubernetes**: kubernetes client for cluster operations
- **Multi-Cloud Libraries**: terraform-python, ansible-python

## Scripts
- `core/scripts/automation/infrastructure-manager.py`: AI-powered automation implementation
- `core/scripts/automation/infrastructure-manager_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
infrastructure, manager, ai, ml, predictive, scaling, optimization, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment operations require approval
- **High-impact operations**: Critical operations require review
- **Security changes**: Security modifications need validation
- **AI Model Updates**: Changes to AI models require approval
- **Infrastructure Scaling**: Major scaling operations need human oversight

## Enterprise Features
- **Multi-tenant Support**: Isolated operations per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify logic dynamically
- **Cross-Cloud Orchestration**: Coordinated operations across providers
- **AI-Powered Insights**: Advanced analytics and predictive capabilities
- **Automated Learning**: Continuous improvement from infrastructure patterns

## Best Practices
- **Idempotent Operations**: Safe retry mechanisms with AI validation
- **Circuit Breaker Patterns**: Resilience against failures with AI monitoring
- **Rate Limiting**: Respect API limits and implement backpressure
- **Graceful Degradation**: Fallback strategies when providers are unavailable
- **Comprehensive Testing**: Integration tests and compliance validation
- **Security First**: Zero-trust architecture and principle of least privilege
- **AI Model Validation**: Regular validation of ML models and prediction accuracy
- **Data Privacy**: Ensure infrastructure data handling complies with privacy regulations
