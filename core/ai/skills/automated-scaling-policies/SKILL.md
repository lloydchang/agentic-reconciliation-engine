---
name: automated-scaling-policies
description: AI-powered automated scaling policies skill with intelligent resource optimization, predictive scaling decisions, and adaptive policy management. Use when implementing automated scaling with advanced AI capabilities for proactive resource management and cost optimization.
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

# Automated Scaling Policies — AI-Powered Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for automated scaling policies across AWS, Azure, GCP, and on-premise environments with advanced AI capabilities including intelligent resource optimization, predictive scaling decisions, and adaptive policy management to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **AI-powered automated scaling** across multi-cloud environments
- **Predictive scaling decisions** and intelligent resource optimization
- **Adaptive policy management** using ML and predictive analytics
- **Proactive scaling monitoring** with anomaly detection
- **Resource optimization** through AI-driven scaling policies
- **Scaling automation** with intelligent decision-making
- **Compliance and governance** for automated scaling activities

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
3. **AI-Powered Analysis**: Apply ML algorithms for intelligent scaling analysis
4. **Predictive Planning**: Generate optimized scaling plan with AI insights
5. **Risk Assessment**: AI-enhanced risk analysis and impact evaluation
6. **Intelligent Execution**: Perform scaling operations with AI monitoring and validation
7. **Results Analysis**: Process results and generate AI-enhanced reports
8. **Learning Integration**: Update AI models with operational outcomes

## Outputs
- **AI-Enhanced Scaling Results**: Detailed execution results with AI insights
- **Predictive Analytics**: Scaling performance predictions and forecasts
- **Intelligent Recommendations**: AI-generated optimization suggestions
- **Anomaly Detection**: Scaling anomalies and potential issues
- **Resource Optimization**: AI-powered scaling analysis and optimization opportunities
- **Compliance Reports**: Validation and compliance status with AI insights
- **Audit Trail**: Complete scaling history for compliance across all providers

## Environment
- **AWS**: EKS, EC2, Lambda, CloudWatch, IAM, S3, Auto Scaling, CloudWatch Container Insights
- **Azure**: AKS, VMs, Functions, Monitor, Azure AD, Autoscale, Azure Monitor for containers
- **GCP**: GKE, Compute Engine, Cloud Functions, Cloud Monitoring, Cloud Run, Cloud Operations
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus, HPA, custom metrics
- **Multi-Cloud Tools**: Terraform, Ansible, Crossplane, Cluster API, Helm, Kustomize

## Dependencies
- **Python 3.8+**: Core execution environment
- **AI/ML Libraries**: scikit-learn, pandas, numpy, statsmodels, tensorflow/keras
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Time Series Libraries**: prophet, pmdarima for predictive analysis
- **Kubernetes**: kubernetes client for cluster operations
- **Multi-Cloud Libraries**: terraform-python, ansible-python

## Scripts
- `core/scripts/automation/automated-scaling-policies.py`: AI-powered automation implementation
- `core/scripts/automation/scaling-policy-handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_scaler.py`: Cross-provider coordination

## Trigger Keywords
scaling, policies, automation, ai, ml, predictive, optimization, resource, enterprise, multi-cloud, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment operations require approval
- **High-impact operations**: Critical scaling operations require review
- **Security changes**: Security modifications need validation
- **AI Model Updates**: Changes to AI models require approval
- **Major Scaling**: Large-scale scaling operations need human oversight

## Enterprise Features
- **Multi-tenant Support**: Isolated scaling operations per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify logic dynamically
- **Cross-Cloud Orchestration**: Coordinated scaling operations across providers
- **AI-Powered Insights**: Advanced analytics and predictive capabilities
- **Automated Learning**: Continuous improvement from scaling patterns

## Best Practices
- **Idempotent Operations**: Safe retry mechanisms with AI validation
- **Circuit Breaker Patterns**: Resilience against failures with AI monitoring
- **Rate Limiting**: Respect API limits and implement backpressure
- **Graceful Degradation**: Fallback strategies when providers are unavailable
- **Comprehensive Testing**: Integration tests and compliance validation
- **Security First**: Zero-trust architecture and principle of least privilege
- **AI Model Validation**: Regular validation of ML models and prediction accuracy
- **Data Privacy**: Ensure scaling data handling complies with privacy regulations
