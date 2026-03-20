---
name: advanced-monitoring
description: Enterprise-grade advanced monitoring with AI-powered analytics, real-time anomaly detection, predictive insights, and intelligent alerting. Use when implementing sophisticated monitoring with machine learning, time series analysis, and automated incident response.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "2.0"
  category: enterprise
  risk_level: medium
  autonomy: conditional
  layer: temporal
compatibility: Requires Python 3.8+, monitoring systems (Prometheus, Grafana), and access to infrastructure metrics
allowed-tools: Bash Read Write Grep
---

# Advanced Monitoring — AI-Powered Infrastructure Intelligence

## Purpose
Enterprise-grade advanced monitoring solution with AI-powered analytics, real-time anomaly detection, predictive insights, and intelligent alerting across multi-cloud environments.

## When to Use
- **Real-time Anomaly Detection** with machine learning
- **Predictive Analytics** for infrastructure forecasting
- **Intelligent Alerting** with AI-driven prioritization
- **Performance Optimization** with advanced analytics
- **Capacity Planning** with predictive modeling
- **Root Cause Analysis** with AI correlation

## Inputs
- **operation**: Monitoring operation type (required)
- **targetResources**: Resources to monitor (required)
- **timeRange**: Time range for analysis (optional)
- **alertThresholds**: Custom alert thresholds (optional)
- **aiMode**: Enable AI-powered analysis (optional)
- **outputFormat**: Output format (optional)

## Process
1. **Data Collection**: Gather metrics from all monitoring sources
2. **AI Analysis**: Apply machine learning for pattern detection
3. **Anomaly Detection**: Identify unusual behavior and trends
4. **Predictive Analytics**: Forecast future infrastructure needs
5. **Intelligent Alerting**: Generate prioritized alerts with AI insights
6. **Automated Response**: Trigger automated remediation when appropriate
7. **Continuous Learning**: Update models with new data patterns

## Outputs
- **AI-Enhanced Metrics**: Advanced analytics and insights
- **Anomaly Detection Results**: Unusual patterns and potential issues
- **Predictive Forecasts**: Future infrastructure needs and trends
- **Intelligent Alerts**: Prioritized notifications with AI context
- **Performance Reports**: Comprehensive monitoring analytics
- **Recommendations**: AI-driven optimization suggestions

## Environment
- **Monitoring Systems**: Prometheus, Grafana, ELK stack
- **AI/ML Frameworks**: scikit-learn, TensorFlow, PyTorch
- **Time Series Databases**: InfluxDB, TimescaleDB
- **Alerting Systems**: Alertmanager, PagerDuty integration
- **Visualization**: Grafana dashboards with AI insights

## Dependencies
- **Python 3.8+**: Core execution environment
- **Monitoring Libraries**: prometheus-client, grafana-api
- **AI/ML Libraries**: scikit-learn, pandas, numpy, statsmodels
- **Time Series**: prophet, pmdarima for forecasting
- **Visualization**: matplotlib, plotly, seaborn

## Scripts
- `core/scripts/automation/advanced-monitoring.py`: Main monitoring orchestrator
- `core/scripts/automation/anomaly-detector.py`: AI-powered anomaly detection
- `core/scripts/automation/predictive-analytics.py`: Forecasting and prediction

## Trigger Keywords
monitoring, analytics, anomaly detection, predictive, alerting, performance, capacity, insights

## Human Gate Requirements
- **Critical Alerts**: High-priority alerts may require human verification
- **Automated Response**: Automated remediation needs approval for critical systems
- **Model Updates**: AI model retraining requires validation
- **Security Alerts**: Security-related alerts need immediate human review

## Enterprise Features
- **Multi-Cloud Monitoring**: Unified monitoring across all providers
- **Real-Time Analytics**: Sub-second metric collection and analysis
- **Intelligent Alerting**: AI-driven alert prioritization and correlation
- **Predictive Insights**: Advanced forecasting and capacity planning
- **Automated Remediation**: Self-healing capabilities with AI guidance
- **Compliance Reporting**: Automated compliance and audit reporting

## Best Practices
- **Metric Quality**: Ensure high-quality, consistent metric collection
- **Alert Fatigue Prevention**: Use AI to minimize false positives
- **Performance Impact**: Minimize monitoring overhead on systems
- **Data Retention**: Balance storage costs with analytical needs
- **Security**: Secure monitoring data and alert channels
