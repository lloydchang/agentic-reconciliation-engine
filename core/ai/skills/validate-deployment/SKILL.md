---
name: validate-deployment
description: Use when you need to validate deployments before or after release with automated testing, health checks, and smoke tests. Ensures application quality by running integration tests, monitoring metrics, and checking service health across environments.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: enterprise
  risk_level: medium
  autonomy: conditional
  layer: temporal
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Deployment Validation — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for deployment validation operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Pre-Deployment Validation**: Before deploying to production to catch issues early
- **Post-Deployment Verification**: After deployment to ensure everything is working correctly
- **Environment Promotion**: When promoting deployments through dev → staging → production pipeline
- **Critical Updates**: For database changes, API updates, or security patches
- **Performance Validation**: When need to verify performance benchmarks are met
- **Integration Testing**: When need to validate external service integrations are working
- **Compliance Checks**: When need to ensure deployments meet security and compliance standards

## Gotchas

### Common Pitfalls
- **Test Data Pollution**: Validation tests should use isolated test data, not production data
- **Health Check False Positives**: Health checks may pass while application has subtle issues
- **Timeout Settings**: Validation tests may timeout for applications with slow startup times
- **Environment Differences**: Test results may not reflect production behavior due to environment differences

### Edge Cases
- **Third-Party Service Downtime**: Validation may fail due to external service issues, not deployment problems
- **Network Latency**: Cross-region deployments may have different latency patterns affecting validation
- **Resource Constraints**: Test environments may have different resource limits than production
- **Time-Dependent Features**: Features with time-based logic may behave differently during validation

### Performance Issues
- **Load Testing Impact**: Heavy validation tests can impact application performance
- **Concurrent Validations**: Running multiple validations simultaneously can cause resource contention
- **Monitoring Delays**: Metrics and logs may have delays before reflecting deployment changes
- **Database Connection Limits**: Validation tests may exhaust database connection pools

### Security Considerations
- **Test Credentials**: Validation should use test credentials, not production secrets
- **Data Privacy**: Ensure validation doesn't expose sensitive data in logs or reports
- **Access Rights**: Validation service needs appropriate but limited access to services
- **Audit Trail**: Maintain validation results for compliance and troubleshooting

### Troubleshooting
- **Flaky Tests**: Identify and fix tests that have inconsistent results
- **Environment Issues**: Ensure test environments are properly configured and stable
- **Network Connectivity**: Verify validation service can reach all required endpoints
- **Service Dependencies**: Check that all required external services are available during validation

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
- `core/scripts/automation/deployment-validation.py`: Main automation implementation
- `core/scripts/automation/deployment-validation_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
deployment, validation, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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

## References

Load these files when needed:
- `scripts/validation-engine.py` - Core validation logic and test execution
- `scripts/health-checker.py` - Health check implementation and monitoring
- `references/test-templates.md` - Standard validation test templates
- `assets/validation-criteria.yaml` - Validation rules and pass/fail criteria
- `examples/validation-reports/` - Sample validation reports and formats
