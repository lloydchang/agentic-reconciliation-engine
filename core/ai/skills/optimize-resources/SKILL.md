---
name: optimize-resources
description: AI-powered resource optimization skill with intelligent resource allocation, ML-based scaling recommendations, and predictive resource management. Use when optimizing cloud resource utilization with advanced AI capabilities for cost reduction and performance improvement.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "2.0"
  category: enterprise
  risk_level: low
  autonomy: conditional
  layer: temporal
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Resource Optimizer — Multi-Cloud AI-Powered Resource Management

## Purpose
Enterprise-grade automation solution for resource optimization operations across AWS, Azure, GCP, and on-premise environments with advanced AI capabilities including intelligent resource allocation, ML-based scaling recommendations, and predictive resource management to maximize cost efficiency while maintaining performance and reliability standards.

## When to Use
- **resource optimization operations** across multi-cloud environments
- **AI-powered resource allocation** and intelligent scaling recommendations
- **Predictive resource management** using ML and time series forecasting
- **Cost reduction and efficiency** improvement workflows with AI insights
- **Resource right-sizing and scaling** recommendations
- **Performance optimization** and capacity planning with predictive analytics

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **cloudProvider**: Cloud provider - `aws|azure|gcp|onprem|all` (optional, default: `all`)
- **parameters**: Operation-specific parameters including AI model configurations (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)
- **historicalData**: Include historical resource usage data for predictive analysis (optional, default: `false`)

## Process
1. **Resource Discovery**: Identify and catalog all resources across providers
2. **AI-Powered Utilization Analysis**: Apply ML algorithms to analyze current usage patterns and performance metrics
3. **Predictive Resource Forecasting**: Use time series analysis to predict future resource needs
4. **Intelligent Allocation**: Apply ML-based resource allocation and scaling recommendations
5. **Cost Analysis**: Evaluate spending patterns and identify optimization opportunities with AI insights
6. **Recommendation Engine**: Generate intelligent optimization suggestions with confidence scores
7. **Risk Assessment**: Evaluate impact and risks of proposed changes using AI models
8. **Execution**: Apply optimizations with monitoring and rollback capabilities
9. **Validation**: Verify improvements and measure cost savings with AI validation

## Outputs
- **AI-Enhanced Recommendations**: ML-generated resource optimization suggestions with predictive insights
- **Utilization Reports**: Current and historical resource usage analysis with trend predictions
- **Cost Analysis**: Spending patterns and optimization impact metrics with forecasting
- **Performance Metrics**: Resource performance before and after optimization with AI validation
- **Predictive Forecasts**: Future resource needs and capacity planning insights
- **Audit Trail**: Complete optimization history for compliance

## Environment
- **AWS**: Cost Explorer, CloudWatch, EC2, RDS, Lambda, S3, Auto Scaling
- **Azure**: Cost Management, Monitor, VMs, SQL Database, Functions, Autoscale
- **GCP**: Cloud Billing, Cloud Monitoring, Compute Engine, Cloud SQL, Cloud Run
- **On-Premise**: Prometheus, Grafana, VMware, OpenStack monitoring, Kubernetes HPA

## Dependencies
- **Python 3.8+**: Core execution environment
- **AI/ML Libraries**: scikit-learn, pandas, numpy, statsmodels, tensorflow/keras
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Time Series Libraries**: prophet, pmdarima for predictive analysis
- **Optimization Libraries**: scipy, cvxopt for resource allocation
- **Data Analysis**: pandas, numpy, matplotlib for AI model training
- **Kubernetes**: kubernetes client for cluster operations

## Scripts
- `core/scripts/automation/resource-optimizer.py`: Main AI-powered optimization implementation
- `core/scripts/automation/resource_optimizer_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
resource, optimization, ai, ml, predictive, allocation, scaling, intelligent, cost, efficiency, performance, multi-cloud, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment optimizations require approval
- **High-impact operations**: Critical resource modifications need review
- **Security changes**: Security modifications need validation
- **AI Model Updates**: Changes to AI models require approval
- **Resource Scaling**: Major scaling operations need human oversight

## Enterprise Features
- **Multi-tenant Support**: Isolated optimization per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete optimization trail for compliance
- **Performance Monitoring**: SLA tracking and cost metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify optimization logic
- **Cross-Cloud Orchestration**: Coordinated optimizations across providers
- **AI-Powered Insights**: Advanced analytics and predictive capabilities
- **Automated Learning**: Continuous improvement from resource usage patterns

## Best Practices
- **Gradual Optimization**: Implement changes in phases to minimize risk
- **Performance Validation**: Ensure optimizations don't impact performance with AI monitoring
- **Cost Monitoring**: Track actual savings vs. projected savings with ML validation
- **Rollback Planning**: Maintain ability to revert changes
- **Comprehensive Testing**: Validate recommendations before implementation
- **Security First**: Ensure optimizations don't compromise security posture
- **AI Model Validation**: Regular validation of ML models and prediction accuracy
- **Data Privacy**: Ensure resource usage data handling complies with privacy regulations
