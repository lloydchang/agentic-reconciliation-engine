---
name: iac-deployment-validator
description: >
  Infrastructure as Code validation and security checking for Terraform, Kubernetes,
  and Helm deployments. Performs comprehensive security analysis, cost estimation,
  compliance validation, and best practices enforcement.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: Manual approval required for production deployments
---

# IaC Deployment Validator Skill

## Overview

The IaC Deployment Validator skill provides comprehensive validation and security analysis for Infrastructure as Code deployments. It supports Terraform, Kubernetes manifests, and Helm charts, ensuring deployments meet security standards, compliance requirements, and best practices.

## Capabilities

### Core Functions

- **Terraform Plan Validation**: Analyzes Terraform plans for security, cost, and compliance
- **Kubernetes Manifest Validation**: Validates K8s manifests for security and best practices
- **Helm Chart Validation**: Checks Helm charts for security and configuration issues
- **Cost Estimation**: Provides detailed cost analysis for infrastructure deployments
- **Security Policy Checks**: Validates IaC against security policies and standards
- **Comprehensive Reporting**: Generates detailed deployment validation reports

### Supported IaC Types

- **Terraform**: Plans, configurations, modules, and state analysis
- **Kubernetes**: YAML manifests, resources, and cluster configurations
- **Helm**: Charts, templates, values, and deployment analysis

### Validation Categories

1. **Security Analysis**
   - Resource security configurations
   - Network security rules
   - Access control policies
   - Encryption settings

2. **Compliance Validation**
   - CIS benchmarks
   - NIST frameworks
   - SOC2 requirements
   - Industry-specific standards

3. **Cost Analysis**
   - Resource cost estimation
   - Cost optimization recommendations
   - Budget impact analysis
   - ROI calculations

4. **Best Practices**
   - Resource naming conventions
   - Configuration standards
   - Performance optimization
   - Maintainability checks

## Usage

### Terraform Validation

```bash
# Validate Terraform plan
skill invoke iac-deployment-validator validate-terraform --plan-file terraform.plan --framework CIS

# Validate with cost analysis
skill invoke iac-deployment-validator validate-terraform --plan-file terraform.plan --check-cost --provider aws

# Comprehensive validation
skill invoke iac-deployment-validator validate-terraform --plan-file terraform.plan \
  --check-security --check-cost --check-compliance --framework NIST
```

### Kubernetes Validation

```bash
# Validate Kubernetes manifests
skill invoke iac-deployment-validator validate-k8s --manifest-path k8s/ --namespace production

# Security-focused validation
skill invoke iac-deployment-validator validate-k8s --manifest-path deployment.yaml \
  --check-security --check-resources --check-best-practices

# Validate specific manifest
skill invoke iac-deployment-validator validate-k8s --manifest-path pod.yaml \
  --security-only
```

### Helm Chart Validation

```bash
# Validate Helm chart
skill invoke iac-deployment-validator validate-helm --chart-path ./chart --release-name myapp

# Dry-run validation
skill invoke iac-deployment-validator validate-helm --chart-path ./chart \
  --values-file values-prod.yaml --dry-run --namespace production

# Security validation
skill invoke iac-deployment-validator validate-helm --chart-path ./chart \
  --check-security --values-file values.yaml
```

### Cost Estimation

```bash
# Estimate deployment costs
skill invoke iac-deployment-validator estimate-cost --iac-type terraform \
  --config-path ./ --provider aws --region us-east-1

# Multi-cloud cost comparison
skill invoke iac-deployment-validator estimate-cost --iac-type terraform \
  --config-path ./ --compare-providers aws,azure,gcp

# Cost optimization analysis
skill invoke iac-deployment-validator estimate-cost --iac-type terraform \
  --config-path ./ --optimization-recommendations
```

### Security Policy Checks

```bash
# Check against security policies
skill invoke iac-deployment-validator check-security --iac-path ./ \
  --policy-set CIS --severity-threshold medium

# Custom policy validation
skill invoke iac-deployment-validator check-security --iac-path ./ \
  --policy-set custom --custom-policy-path ./policies/

# Compliance validation
skill invoke iac-deployment-validator check-security --iac-path ./ \
  --policy-set NIST --generate-report
```

### Comprehensive Reporting

```bash
# Generate deployment report
skill invoke iac-deployment-validator report --iac-path ./ \
  --format PDF --include-recommendations --include-cost-analysis

# Executive summary report
skill invoke iac-deployment-validator report --iac-path ./ \
  --format HTML --executive-summary --compliance-framework CIS

# Technical analysis report
skill invoke iac-deployment-validator report --iac-path ./ \
  --format JSON --technical-analysis --security-analysis
```

## Configuration

### Required Environment Variables

```bash
# Cloud Provider Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
AZURE_SUBSCRIPTION_ID=your_subscription_id

GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your_project_id

# Cost Estimation API
INFRACOST_API_KEY=your_infracost_api_key
PRICING_API_KEY=your_pricing_api_key
```

### Skill Configuration

```yaml
# .claude/skills/iac-deployment-validator/config.yaml
validation_rules:
  terraform:
    security:
      - check_unencrypted_storage
      - check_open_security_groups
      - check_iam_privileges
      - check_logging_configuration
    compliance:
      - CIS_AWS_Controls
      - NIST_800_53
      - SOC2_Controls
    cost:
      - resource_sizing
      - instance_types
      - storage_optimization
      - data_transfer_costs

  kubernetes:
    security:
      - check_security_contexts
      - check_privileged_containers
      - check_secrets_management
      - check_network_policies
    best_practices:
      - check_resource_limits
      - check_health_checks
      - check_image_tags
      - check_namespace_usage

  helm:
    security:
      - check_template_security
      - check_values_security
      - check_chart_integrity
    structure:
      - check_required_files
      - check_chart_metadata
      - check_template_syntax

cost_estimation:
  providers:
    aws:
      pricing_api: https://pricing.us-east-1.amazonaws.com
      regions: [us-east-1, us-west-2, eu-west-1]
    azure:
      pricing_api: https://prices.azure.com
      regions: [eastus, westus2, westeurope]
    gcp:
      pricing_api: https://cloudbilling.googleapis.com
      regions: [us-central1, us-east1, europe-west1]

reporting:
  formats:
    - JSON
    - HTML
    - PDF
  sections:
    - executive_summary
    - technical_analysis
    - security_analysis
    - cost_analysis
    - recommendations
  templates:
    executive: templates/executive-report.html
    technical: templates/technical-report.html
    security: templates/security-report.html

notification:
  slack:
    webhook_url: https://hooks.slack.com/services/...
    channel: #iac-validation
    username: IaC Validator
  email:
    smtp_server: smtp.company.com
    smtp_port: 587
    from_address: iac-validator@company.com
    recipients:
      - devops@company.com
      - security@company.com
```

## MCP Server Integration

This skill integrates with the `iac-validator` MCP server for enhanced capabilities:

### Available MCP Tools

- `validate_terraform_plan`: Validate Terraform plans for security, cost, and compliance
- `validate_kubernetes_manifests`: Validate K8s manifests for best practices and security
- `validate_helm_chart`: Validate Helm charts for security and best practices
- `estimate_deployment_costs`: Estimate costs for infrastructure deployment
- `check_security_policies`: Check IaC against security policies and standards
- `generate_deployment_report`: Generate comprehensive deployment validation report

### MCP Usage Example

```javascript
// Using the MCP server directly
const terraformValidation = await mcp.call('validate_terraform_plan', {
  plan_file: 'terraform.plan',
  check_security: true,
  check_cost: true,
  check_compliance: true,
  compliance_framework: 'CIS'
});

const k8sValidation = await mcp.call('validate_kubernetes_manifests', {
  manifest_path: 'k8s/',
  namespace: 'production',
  check_security: true,
  check_resources: true,
  check_best_practices: true
});
```

## Implementation Details

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ IaC Parsers     │    │ Validation Engine│    │ Reporting       │
│                 │    │                  │    │                 │
│ • Terraform     │───▶│ • Security Rules │───▶│ • PDF Generator │
│ • Kubernetes    │    │ • Compliance     │    │ • HTML Generator │
│ • Helm          │    │ • Cost Analysis  │    │ • JSON Export   │
│ • YAML/JSON     │    │ • Best Practices │    │ • Email Sender  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Cost Estimator  │    │ Policy Engine    │    │ Notification    │
│                 │    │                  │    │                 │
│ • Cloud APIs    │    │ • Rule Evaluation│    │ • Slack Webhook │
│ • Pricing Data  │    │ • Policy Matching│    │ • Email SMTP    │
│ • Optimization  │    │ • Scoring        │    │ • Teams Channel │
│ • Budget Track  │    │ • Exceptions     │    │ • PagerDuty     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Validation Rules

#### Terraform Security Rules

1. **Storage Encryption**
   ```hcl
   # ❌ Bad - Unencrypted EBS volume
   resource "aws_ebs_volume" "example" {
     size = 100
     # encrypted = false  # Missing encryption
   }
   
   # ✅ Good - Encrypted EBS volume
   resource "aws_ebs_volume" "example" {
     size = 100
     encrypted = true
   }
   ```

2. **Security Group Configuration**
   ```hcl
   # ❌ Bad - Open to world
   resource "aws_security_group" "example" {
     ingress {
       from_port   = 22
       to_port     = 22
       protocol    = "tcp"
       cidr_blocks = ["0.0.0.0/0"]  # Too open
     }
   }
   
   # ✅ Good - Restricted access
   resource "aws_security_group" "example" {
     ingress {
       from_port   = 22
       to_port     = 22
       protocol    = "tcp"
       cidr_blocks = ["10.0.0.0/8"]  # Restricted
     }
   }
   ```

#### Kubernetes Security Rules

1. **Security Context**
   ```yaml
   # ❌ Bad - No security context
   apiVersion: v1
   kind: Pod
   spec:
     containers:
     - name: app
       image: nginx
   # Missing security context
   
   # ✅ Good - With security context
   apiVersion: v1
   kind: Pod
   spec:
     securityContext:
       runAsNonRoot: true
       runAsUser: 1000
       fsGroup: 2000
     containers:
     - name: app
       image: nginx
       securityContext:
         allowPrivilegeEscalation: false
         readOnlyRootFilesystem: true
   ```

2. **Resource Limits**
   ```yaml
   # ❌ Bad - No resource limits
   apiVersion: v1
   kind: Pod
   spec:
     containers:
     - name: app
       image: nginx
       # Missing resources section
   
   # ✅ Good - With resource limits
   apiVersion: v1
   kind: Pod
   spec:
     containers:
     - name: app
       image: nginx
       resources:
         requests:
           memory: "64Mi"
           cpu: "250m"
         limits:
           memory: "128Mi"
           cpu: "500m"
   ```

### Cost Estimation Algorithm

The cost estimation uses a multi-factor approach:

1. **Resource Pricing**: Real-time cloud provider pricing data
2. **Usage Patterns**: Historical usage data and projections
3. **Regional Variations**: Price differences across regions
4. **Volume Discounts**: Enterprise pricing and volume discounts
5. **Optimization Opportunities**: Rightsizing and alternative options

### Compliance Validation

The skill validates against multiple compliance frameworks:

#### CIS Controls
- Access control
- Audit logging
- Data encryption
- Network security
- Vulnerability management

#### NIST 800-53
- Security and privacy controls
- Risk management
- System and communications protection
- System and information integrity

#### SOC2
- Security
- Availability
- Processing integrity
- Confidentiality
- Privacy

## Best Practices

### 1. IaC Development
- Use consistent naming conventions
- Implement modular design
- Include comprehensive documentation
- Use version control effectively

### 2. Security Integration
- Implement security checks early in development
- Use automated security scanning
- Regularly update security rules
- Monitor for new vulnerabilities

### 3. Cost Management
- Regularly review resource utilization
- Implement cost monitoring
- Use reserved instances where appropriate
- Optimize storage and data transfer

### 4. Compliance Management
- Map compliance requirements to technical controls
- Maintain compliance evidence
- Regular compliance assessments
- Continuous compliance monitoring

## Troubleshooting

### Common Issues

**Terraform Plan Parsing Errors**
```bash
# Check Terraform version compatibility
skill invoke iac-deployment-validator check-terraform-version

# Validate plan file format
skill invoke iac-deployment-validator validate-plan-format --plan-file terraform.plan

# Debug parsing issues
export IAC_VALIDATOR_DEBUG=true
skill invoke iac-deployment-validator validate-terraform --plan-file terraform.plan --debug
```

**Kubernetes Manifest Validation Failures**
```bash
# Check YAML syntax
skill invoke iac-deployment-validator validate-yaml --manifest-path deployment.yaml

# Verify K8s API version compatibility
skill invoke iac-deployment-validator check-api-version --manifest-path deployment.yaml

# Test resource validation
skill invoke iac-deployment-validator test-resource --manifest-path deployment.yaml
```

**Cost Estimation Issues**
```bash
# Check pricing API connectivity
skill invoke iac-deployment-validator test-pricing-api --provider aws

# Verify cost calculation
skill invoke iac-deployment-validator debug-cost --config-path ./ --verbose

# Update pricing data
skill invoke iac-deployment-validator update-pricing --provider aws
```

### Debug Mode

```bash
# Enable comprehensive debugging
export IAC_VALIDATOR_DEBUG=true
export IAC_VALIDATOR_TRACE=true
skill invoke iac-deployment-validator validate-terraform --plan-file terraform.plan \
  --debug --trace --verbose
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/iac-validation.yml
name: IaC Validation
on: [push, pull_request]

jobs:
  validate-terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v1
      - name: Terraform Plan
        run: terraform plan -out=tf.plan
      - name: Validate IaC
        run: |
          skill invoke iac-deployment-validator validate-terraform \
            --plan-file tf.plan \
            --check-security --check-cost --check-compliance \
            --framework CIS
      - name: Upload Validation Report
        uses: actions/upload-artifact@v2
        with:
          name: iac-validation-report
          path: validation-report.pdf

  validate-kubernetes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Kubernetes Manifests
        run: |
          skill invoke iac-deployment-validator validate-k8s \
            --manifest-path k8s/ \
            --check-security --check-resources --check-best-practices
```

### Git Hooks Integration

```bash
#!/bin/sh
# .git/hooks/pre-commit
echo "Running IaC validation..."

# Validate Terraform files
if find . -name "*.tf" -print -quit | grep -q .; then
  terraform plan -out=tf.plan
  skill invoke iac-deployment-validator validate-terraform \
    --plan-file tf.plan \
    --severity-threshold high
  rm tf.plan
fi

# Validate Kubernetes manifests
if find . -name "*.yaml" -o -name "*.yml" -print -quit | grep -q .; then
  skill invoke iac-deployment-validator validate-k8s \
    --manifest-path . \
    --severity-threshold medium
fi

echo "IaC validation passed!"
```

### IDE Integration

```json
// .vscode/settings.json
{
  "iac-validator.autoValidate": true,
  "iac-validator.severityThreshold": "medium",
  "iac-validator.frameworks": ["CIS", "NIST"],
  "iac-validator.costEstimation": true,
  "iac-validator.notificationChannels": ["slack"]
}
```

## Performance Considerations

### Optimization Tips

1. **Parallel Processing**: Validate multiple files in parallel
2. **Caching**: Cache validation results and pricing data
3. **Incremental Validation**: Only validate changed files
4. **Batch Processing**: Process multiple resources together

### Resource Usage

- **Memory**: ~2GB for large-scale IaC validation
- **CPU**: High usage during security analysis and cost estimation
- **Network**: High usage during cloud API calls for pricing
- **Storage**: ~1GB for validation cache and reports

## Security Considerations

### Data Protection

- All cloud credentials are encrypted at rest
- IaC configurations are processed in memory only
- Validation reports are stored securely
- Sensitive data is redacted in reports

### Access Control

- Role-based access for validation operations
- Audit logging for all validation activities
- Secure API key management
- Network segmentation for validation workloads

## Version History

### v1.0.0
- Initial Terraform validation support
- Basic security checks and cost estimation
- JSON and HTML reporting

### v1.1.0
- Added Kubernetes manifest validation
- Enhanced security rules
- PDF reporting support

### v1.2.0
- Helm chart validation
- Multi-cloud cost estimation
- Compliance framework support

### v1.3.0
- Advanced security analysis
- Real-time pricing integration
- Comprehensive reporting suite

## Support and Contributing

### Getting Help

- Documentation: `/docs/iac-deployment-validator.md`
- Examples: `/examples/iac-validation/`
- Community: `#iac-validation` Slack channel

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new validation rules
4. Submit a pull request

### License

This skill is licensed under the MIT License. See LICENSE file for details.
