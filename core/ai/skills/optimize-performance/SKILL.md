---
name: optimize-performance
description: AI-powered performance optimization skill for multi-cloud environments with predictive analytics, ML-based recommendations, and automated optimization. Use when optimizing application and infrastructure performance across AWS, Azure, GCP, and on-premise.
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

# Performance Optimization — Multi-Cloud Enterprise Automation with AI

## Purpose
Enterprise-grade automation solution for performance optimization across AWS, Azure, GCP, and on-premise environments with advanced AI capabilities including predictive analytics, machine learning-based optimization recommendations, and automated performance tuning to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **performance optimization operations** across multi-cloud environments
- **AI-powered performance analysis** including predictive scaling and ML recommendations
- **Automated optimization** of application and infrastructure performance
- **Monitoring and management** of performance metrics and bottlenecks
- **Compliance and governance** for performance optimization activities
- **Predictive performance analytics** using historical data and ML models

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **cloudProvider**: Cloud provider - `aws|azure|gcp|onprem|all` (optional, default: `all`)
- **parameters**: Operation-specific parameters including AI model configurations (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)
- **historicalData**: Include historical performance data for predictive analysis (optional, default: `false`)
- **optimizationType**: Type of optimization - `scaling|right_sizing|caching|load_balancing|database|network|application|infrastructure` (optional)

## Process
1. **Cloud Provider Detection**: Identify target cloud providers and environments
2. **Input Validation**: Comprehensive parameter validation and security checks
3. **Multi-Cloud Context Analysis**: Analyze current performance state across all providers
4. **AI-Powered Performance Analysis**: Apply predictive analytics, ML-based bottleneck detection, and optimization modeling
5. **Optimization Planning**: Generate AI-enhanced optimization recommendations with risk assessment
6. **Safety Assessment**: Risk analysis and impact evaluation across providers
7. **Execution**: Perform optimizations with monitoring and validation
8. **Results Analysis**: Process results and generate AI-enhanced performance reports

## Outputs
- **Operation Results**: Detailed execution results and status per provider
- **AI-Enhanced Recommendations**: ML-generated optimization recommendations with predictive insights
- **Performance Analysis**: Comprehensive performance metrics and bottleneck identification
- **Predictive Forecasts**: Future performance predictions and capacity planning insights
- **Compliance Reports**: Validation and compliance status across environments
- **Performance Metrics**: Operation performance and efficiency metrics by provider
- **Optimization Results**: Before/after performance comparisons and cost-benefit analysis
- **Audit Trail**: Complete operation history for compliance across all providers

## Environment
- **AWS**: EC2, Lambda, ECS, EKS, CloudWatch, X-Ray, Performance Insights
- **Azure**: VMs, Functions, AKS, Monitor, Application Insights
- **GCP**: Compute Engine, Cloud Functions, GKE, Cloud Monitoring, Cloud Profiler
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus, Grafana

## Dependencies
- **Python 3.8+**: Core execution environment
- **AI/ML Libraries**: scikit-learn, pandas, numpy, statsmodels, tensorflow/keras
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Monitoring Tools**: prometheus-client, grafana-api, cloudwatch, azure-monitor
- **Optimization Libraries**: scipy, cvxopt for advanced optimization
- **Kubernetes**: kubernetes client for cluster operations
- **Multi-Cloud Libraries**: terraform-python, ansible-python

## Scripts
- `core/scripts/automation/performance-optimizer.py`: Main AI-powered optimization implementation
- `core/scripts/automation/performance_optimizer_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
performance, optimization, ai, ml, predictive, scaling, bottleneck, tuning, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment operations require approval
- **High-impact operations**: Critical performance optimizations require review
- **Security changes**: Security modifications need validation
- **AI Model Updates**: Changes to AI models require approval
- **Resource Scaling**: Major scaling operations need human oversight

## Enterprise Features
- **Multi-tenant Support**: Isolated operations per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify logic dynamically
- **Cross-Cloud Orchestration**: Coordinated optimizations across providers
- **AI-Powered Insights**: Advanced analytics and predictive capabilities
- **Automated Learning**: Continuous improvement from performance patterns

## Best Practices
- **Idempotent Operations**: Safe retry mechanisms
- **Circuit Breaker Patterns**: Resilience against failures
- **Rate Limiting**: Respect API limits and implement backpressure
- **Graceful Degradation**: Fallback strategies when providers are unavailable
- **Comprehensive Testing**: Integration tests and compliance validation
- **Security First**: Zero-trust architecture and principle of least privilege
- **AI Model Validation**: Regular validation of ML models and prediction accuracy
- **Data Privacy**: Ensure performance data handling complies with privacy regulations
