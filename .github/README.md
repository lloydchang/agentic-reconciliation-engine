# GitHub Actions - Agent Skills GitOps Integration

This directory contains GitHub Actions workflows that implement GitOps control plane integration for the multi-cloud agent skills ecosystem.

## 🏗️ Architecture Overview

The GitOps integration follows the **structured tool agent pattern** with proper risk assessment, human gates, and compliance validation:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agent Skills   │───▶│  GitHub Actions  │───▶│  Cloud Providers│
│   (Python)       │    │   (Orchestrators)│    │   (Execution)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Risk Assessment│    │   Human Gates    │    │   Monitoring    │
│   & Validation  │    │   (Approvals)    │    │   & Alerts      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Available Workflows

### **Individual Agent Skills**

#### **Infrastructure Provisioning** (`agent-skills-infrastructure-provisioning.yml`)
- **Actions**: provision, status, rollback
- **Risk Levels**: Low (dev), Medium (staging), High (production)
- **Human Gates**: Required for production changes
- **Features**: Multi-cloud support, dry-run mode, auto-approval options

#### **Cluster Health Check** (`agent-skills-cluster-health-check.yml`)
- **Actions**: check, monitor, report
- **Risk Levels**: Low (all environments)
- **Human Gates**: Optional for production monitoring
- **Features**: Scheduled health checks, continuous monitoring, critical alerts

#### **Resource Optimizer** (`agent-skills-resource-optimizer.yml`)
- **Actions**: analyze, optimize, report
- **Risk Levels**: Low (analysis), Medium (optimization), High (auto-apply)
- **Human Gates**: Required for optimizations, finance team approval
- **Features**: Cost analysis, performance optimization, savings tracking

### **Coordinated Workflows**

#### **Agent Skills Coordination** (`agent-skills-coordination.yml`)
- **Workflow Types**: 
  - `provision-and-monitor`: Deploy and monitor new resources
  - `optimize-and-health-check`: Optimize with health validation
  - `full-lifecycle`: Complete resource lifecycle management
  - `disaster-recovery`: Emergency recovery procedures
  - `cost-optimization-cycle`: Regular cost optimization
- **Risk Assessment**: Dynamic based on workflow type and environment
- **Human Gates**: Multi-team approval for complex workflows

### **Quality Gates**

#### **CI Policy Gate** (`ci-policy-gate.yml`)
- **Validations**: Agent Skills specification, code quality, dependencies
- **Security**: Vulnerability scanning, secret detection
- **Compliance**: Risk level validation, human gate requirements
- **Testing**: Unit tests, integration tests, CLI validation

## 🚀 Usage Examples

### **Manual Execution**

```bash
# Trigger infrastructure provisioning
gh workflow run agent-skills-infrastructure-provisioning.yml \
  --field action=provision \
  --field resource_type=ec2 \
  --field resource_name=web-server \
  --field provider=aws \
  --field environment=staging \
  --field dry_run=true

# Trigger resource optimization analysis
gh workflow run agent-skills-resource-optimizer.yml \
  --field action=analyze \
  --field resource_type=compute \
  --field provider=all \
  --field optimization_type=cost \
  --field savings_target=20

# Trigger coordinated workflow
gh workflow run agent-skills-coordination.yml \
  --field workflow_type=optimize-and-health-check \
  --field environment=production \
  --field provider=all \
  --field auto_approve=false
```

### **Scheduled Execution**

- **Health Checks**: Every hour
- **Cost Analysis**: Daily at 3 AM UTC
- **Comprehensive Optimization**: Weekly on Sunday at 2 AM UTC
- **Monthly Reports**: 1st of each month at 1 AM UTC

## 🔧 Configuration

### **Required Secrets**

Configure these secrets in your GitHub repository:

```yaml
# Cloud Provider Credentials
AWS_ACCESS_KEY_ID: xxx
AWS_SECRET_ACCESS_KEY: xxx
AWS_ROLE_ARN: arn:aws:iam::account:role/GitHubActions

AZURE_CREDENTIALS: '{"subscriptionId": "...", "tenantId": "...", "clientId": "...", "clientSecret": "..."}'

GCP_CREDENTIALS: '{"type": "service_account", "project_id": "...", "private_key": "..."}'

# Communication
SLACK_WEBHOOK_URL: https://hooks.slack.com/services/xxx/xxx/xxx

# Team Configuration
INFRASTRUCTURE_TEAM: team/infrastructure
FINANCE_TEAM: team/finance
SRE_TEAM: team/sre
```

### **Environment Variables**

Workflows use these environment variables:

```yaml
PYTHON_VERSION: '3.11'
DEFAULT_REGION: us-west-2
DEFAULT_ENVIRONMENT: production
RISK_THRESHOLD: medium
APPROVAL_TIMEOUT: 60  # minutes
```

## 🛡️ Risk Management

### **Risk Levels**

| Risk Level | Description | Autonomy | Human Gates |
|------------|-------------|-----------|-------------|
| **Low** | Read operations, dev/test changes | `fully_auto` | None |
| **Medium** | Production changes, optimizations | `conditional` | Team approval |
| **High** | Critical infrastructure, auto-apply | `requires_PR` | Multi-team approval |
| **Critical** | Disaster recovery, emergency changes | `requires_PR` | Executive approval |

### **Human Gate Process**

1. **Risk Assessment**: Automatic evaluation based on inputs
2. **Approval Request**: GitHub Issue with detailed information
3. **Team Review**: Required approvers review and comment
4. **Approval/Rejection**: Decision recorded in workflow
5. **Execution**: Proceed with or skip the operation

### **Compliance Validation**

- **SOC2**: Audit logging, access controls
- **GDPR**: Data protection, privacy controls
- **HIPAA**: Healthcare data compliance
- **Internal**: Company-specific policies

## 📊 Monitoring and Observability

### **Metrics Collection**

- **Execution Metrics**: Success rates, duration, resource usage
- **Cost Metrics**: Savings tracking, optimization impact
- **Health Metrics**: Cluster scores, issue detection
- **Security Metrics**: Vulnerability counts, compliance status

### **Alerting**

- **Critical Issues**: Immediate Slack notification and GitHub Issue
- **Cost Thresholds**: Finance team alerts for high savings opportunities
- **Health Degradation**: SRE team alerts for cluster issues
- **Security Findings**: Security team alerts for vulnerabilities

### **Dashboards**

- **GitOps Dashboard**: Workflow status, approval queue
- **Cost Dashboard**: Savings tracking, optimization trends
- **Health Dashboard**: Cluster status, issue trends
- **Security Dashboard**: Compliance status, vulnerability trends

## 🔄 Workflow Examples

### **Example 1: Provision and Monitor**

```yaml
# Input
action: provision
resource_type: ec2
environment: staging
dry_run: false

# Workflow Steps
1. Risk Assessment: Medium (staging + provision)
2. Human Gate: Infrastructure team approval
3. Provision EC2 instance
4. Health Check: Validate deployment
5. Start Monitoring: Continuous health monitoring
6. Results: Instance details, health status
```

### **Example 2: Cost Optimization Cycle**

```yaml
# Input
workflow_type: cost-optimization-cycle
environment: production
auto_approve: false

# Workflow Steps
1. Risk Assessment: Low (analysis only)
2. Resource Analysis: All resource types
3. Optimization Recommendations: Cost savings opportunities
4. Human Gate: Finance team approval for optimizations
5. Apply Optimizations: Safe changes with rollback
6. Health Validation: Post-optimization health checks
7. Report Generation: Monthly cost optimization report
```

### **Example 3: Disaster Recovery**

```yaml
# Input
workflow_type: disaster-recovery
environment: production
auto_approve: false

# Workflow Steps
1. Risk Assessment: Critical (disaster recovery)
2. Human Gate: Executive approval required
3. Health Check: Identify critical issues
4. Rollback: Revert problematic changes
5. Re-provision: Deploy stable configurations
6. Health Validation: Confirm recovery
7. Post-mortem: Document incident and improvements
```

## 🧪 Testing and Validation

### **Local Testing**

```bash
# Test agent skills locally
cd .agents/infrastructure-provisioning/scripts
python main.py provision --type ec2 --name test-instance --dry-run

# Test workflows locally
act -j agent-skills-infrastructure-provisioning
```

### **Integration Testing**

```bash
# Test GitHub Actions workflow
gh workflow run agent-skills-infrastructure-provisioning.yml \
  --field action=status \
  --field provider=aws \
  --field dry_run=true

# Validate policy compliance
gh workflow run ci-policy-gate
```

### **End-to-End Testing**

```bash
# Full workflow test
gh workflow run agent-skills-coordination.yml \
  --field workflow_type=provision-and-monitor \
  --field environment=development \
  --field dry_run=true
```

## 📚 Best Practices

### **Workflow Design**

- **Idempotent**: Safe to run multiple times
- **Atomic**: Either complete fully or rollback
- **Observable**: Comprehensive logging and metrics
- **Secure**: Principle of least privilege
- **Compliant**: Follow organizational policies

### **Risk Management**

- **Conservative Defaults**: Dry-run enabled by default
- **Progressive Deployment**: Dev → Staging → Production
- **Rollback Capability**: Always able to revert changes
- **Human Oversight**: Critical changes require approval
- **Audit Trail**: Complete execution history

### **Performance Optimization**

- **Parallel Execution**: Independent tasks run concurrently
- **Caching**: Reuse expensive operations
- **Rate Limiting**: Respect API limits
- **Timeouts**: Prevent hanging workflows
- **Resource Efficiency**: Optimize runner usage

## 🔍 Troubleshooting

### **Common Issues**

1. **Workflow Not Triggering**
   - Check file paths in workflow triggers
   - Verify branch protection rules
   - Check GitHub Actions permissions

2. **Approval Not Working**
   - Verify approvers are team members
   - Check GitHub token permissions
   - Validate manual approval action configuration

3. **Cloud Provider Errors**
   - Verify credentials in secrets
   - Check IAM permissions
   - Validate resource quotas

4. **Test Failures**
   - Check dependency versions
   - Verify test environment setup
   - Review test configuration

### **Debugging Commands**

```bash
# Check workflow logs
gh run list --workflow=agent-skills-infrastructure-provisioning.yml
gh run view <run-id> --log

# Debug specific job
gh run view <run-id> --job=<job-id> --log

# Test workflow locally
act -j <job-name> --dry-run

# Validate workflow syntax
yamllint .github/workflows/*.yml
```

## 📞 Support

For issues and questions:

1. **Check Documentation**: Review agent skills documentation
2. **Review Logs**: Check workflow execution logs
3. **Search Issues**: Look for similar problems in GitHub Issues
4. **Create Issue**: Provide detailed information and logs
5. **Contact Team**: Reach out to infrastructure team for urgent issues

---

**This GitOps integration provides a secure, compliant, and automated way to manage multi-cloud infrastructure using agent skills with proper human oversight and risk management.**
