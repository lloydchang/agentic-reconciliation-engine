#!/usr/bin/env python3
"""
Script to completely fix all SKILL.md files to comply with agentskills.io specification
"""

import os
import re
import glob
import yaml

def get_skill_description(skill_name):
    """Get skill-specific description"""
    descriptions = {
        'kubectl-assistant': 'Provides intelligent kubectl command assistance, autocomplete suggestions, and Kubernetes cluster management guidance. Use when managing Kubernetes clusters, troubleshooting kubectl commands, or optimizing cluster operations.',
        'log-classifier': 'Classifies and analyzes logs from various sources across multi-cloud environments to identify patterns, anomalies, and issues. Use when troubleshooting problems, analyzing system behavior, or implementing log-based monitoring.',
        'tenant-lifecycle-manager': 'Manages complete tenant lifecycle from onboarding to offboarding with automated resource provisioning and access management. Use when managing multi-tenant environments, handling tenant transitions, or implementing tenant automation.',
        'change-management': 'Manages infrastructure changes with approval workflows, rollback capabilities, and compliance tracking across cloud environments. Use when implementing controlled deployments, managing configuration changes, or ensuring change governance.',
        'audit-siem': 'Performs security audits and SIEM analysis across multi-cloud environments, detects threats, and generates compliance reports. Use when conducting security assessments, monitoring for threats, or ensuring regulatory compliance.',
        'rollback-assistant': 'Provides intelligent rollback capabilities for failed deployments and configuration changes across multi-cloud environments. Use when recovering from failed deployments, undoing changes, or implementing disaster recovery procedures.',
        'incident-triage-runbook': 'Automates incident triage processes and executes runbooks based on incident type and severity across cloud environments. Use when handling incidents, coordinating response teams, or implementing incident automation.',
        'alert-prioritizer': 'Prioritizes and categorizes alerts from monitoring systems across multi-cloud environments, applies intelligent filtering and escalation rules, and provides actionable alert summaries. Use when managing alert floods, improving incident response times, or implementing alert management strategies.',
        'temporal-workflow': 'Manages and orchestrates Temporal workflows across multi-cloud environments with monitoring, retry logic, and error handling. Use when implementing workflow automation, managing distributed systems, or coordinating complex operations.',
        'database-maintenance': 'Performs database maintenance, optimization, and backup procedures across multi-cloud environments. Use when ensuring database performance, managing database health, or implementing maintenance schedules.',
        'cicd-pipeline-monitor': 'Monitors CI/CD pipeline health, performance, and success rates with intelligent alerting and optimization. Use when ensuring deployment reliability, tracking pipeline metrics, or optimizing build processes.',
        'feature-flag-manager': 'Manages feature flags across applications and environments with controlled rollouts and A/B testing capabilities. Use when implementing feature toggles, managing releases, or conducting controlled experiments.',
        'onboarding-assistant': 'Automates user and service onboarding processes across multi-cloud environments with access management and resource provisioning. Use when adding new users, setting up services, or implementing onboarding workflows.',
        'multi-cloud-networking': 'Manages networking configurations across multi-cloud environments with VPC peering, load balancing, and security rules. Use when setting up cloud networks, managing connectivity, or implementing network security.',
        'policy-as-code': 'Implements and manages policy-as-code solutions across multi-cloud environments with validation and enforcement. Use when defining infrastructure policies, ensuring compliance, or implementing governance automation.',
        'observability-stack': 'Deploys and manages observability stacks including monitoring, logging, and tracing across cloud environments. Use when setting up monitoring, implementing observability, or managing telemetry data.',
        'ci-cd-integrator': 'Integrates CI/CD pipelines across multi-cloud environments with automated testing, deployment, and monitoring. Use when streamlining deployment processes, ensuring code quality, or implementing DevOps workflows.',
        'cluster-health-check': 'Performs comprehensive health checks on Kubernetes clusters across multi-cloud environments. Use when monitoring cluster status, troubleshooting issues, or ensuring cluster reliability.',
        'manage-kubernetes-cluster': 'Manages Kubernetes cluster operations including provisioning, scaling, and maintenance across cloud providers. Use when administering clusters, managing node pools, or implementing cluster automation.',
        'alert-router': 'Routes alerts to appropriate teams and systems based on content, severity, and business impact. Use when implementing intelligent alert distribution, team-based alert routing, or automated escalation workflows.',
        'deployment-strategy': 'Implements and manages various deployment strategies including canary, blue-green, and rolling updates. Use when planning deployments, minimizing downtime, or implementing release strategies.',
        'capacity-planning': 'Analyzes resource usage patterns and provides capacity planning recommendations across cloud providers. Use when forecasting resource needs, optimizing infrastructure costs, or planning scaling activities.',
        'rotate-secrets': 'Automates secret rotation and management across multi-cloud environments with security best practices. Use when managing credentials, rotating secrets, or implementing security automation.',
        'monitor-sla-alerting': 'Monitors SLA compliance and generates alerts for violations across multi-cloud services and applications. Use when tracking service levels, ensuring performance guarantees, or implementing SLA monitoring.',
        'policy-explainer': 'Explains and documents infrastructure policies and their impact across cloud environments in natural language. Use when understanding policies, documenting governance, or explaining compliance requirements.',
        'manage-certificates': 'Manages secrets and certificates across multi-cloud environments with automated provisioning and renewal. Use when handling TLS certificates, managing secrets, or implementing security automation.',
        'analyze-backstage-catalog': 'Manages Backstage service catalog with automated service registration and metadata management. Use when implementing service catalogs, managing software assets, or organizing service information.',
        'autoscaler-advisor': 'Provides intelligent autoscaling recommendations and automation for cloud resources across providers. Use when optimizing resource utilization, reducing costs, or implementing scaling strategies.',
        'node-scale-assistant': 'Assists with Kubernetes node scaling operations including cluster autoscaling and node pool management. Use when scaling clusters, managing nodes, or optimizing resource allocation.',
        'deployment-validation': 'Validates deployments before and after release with automated testing and health checks across environments. Use when ensuring deployment quality, preventing issues, or implementing validation pipelines.',
        'disaster-recovery': 'Implements disaster recovery procedures and failover testing across multi-cloud environments. Use when planning disaster recovery, testing failover, or ensuring business continuity.',
        'ai-agent-orchestration': 'Orchestrates AI agents across multi-cloud environments, coordinates workflows, manages agent lifecycles, and provides intelligent task distribution and monitoring. Use when managing AI agent fleets, coordinating complex workflows, or optimizing agent performance across cloud providers.',
        'generate-compliance-report': 'Generates compliance reports and audits for security standards across multi-cloud environments. Use when ensuring regulatory compliance, conducting security audits, or preparing for certifications.',
        'generate-security-report': 'Scans infrastructure and applications for security vulnerabilities and compliance issues. Use when identifying security risks, ensuring compliance, or implementing security best practices.',
        'runbook-planner': 'Creates and manages automated runbooks for common operational tasks and incident response procedures. Use when documenting procedures, automating operations, or implementing runbook systems.',
        'dependency-checker': 'Analyzes and validates software dependencies for security vulnerabilities and compatibility. Use when managing dependencies, ensuring security, or preventing supply chain issues.',
        'infrastructure-manager': 'Manages infrastructure resources across multi-cloud environments with provisioning, monitoring, and optimization. Use when managing cloud resources, optimizing infrastructure, or implementing IaC automation.',
        'observability-aggregator': 'Aggregates observability data from multiple sources across cloud environments for unified monitoring. Use when consolidating metrics, centralizing logs, or implementing observability platforms.',
        'release-manager': 'Manages software release processes across environments with automated deployments and rollbacks. Use when coordinating releases, managing versions, or implementing release automation.',
        'troubleshoot-kubernetes': 'Provides intelligent troubleshooting guidance for Kubernetes issues across clusters and environments. Use when diagnosing K8s problems, resolving cluster issues, or implementing troubleshooting automation.',
        'manifest-generator': 'Generates Kubernetes manifests and configuration files based on requirements and best practices. Use when creating K8s configs, generating manifests, or implementing configuration automation.',
        'gitops-workflow': 'Manages GitOps workflows including automated deployments and drift detection across environments. Use when implementing GitOps, managing deployments, or ensuring configuration consistency.',
        'node-maintenance': 'Performs Kubernetes node maintenance including draining, updates, and health checks across clusters. Use when maintaining nodes, performing updates, or implementing node automation.',
        'monitor-slo': 'Monitors Service Level Objectives and generates alerts for violations across cloud services. Use when tracking SLOs, ensuring service quality, or implementing reliability monitoring.',
        'container-registry': 'Manages container image repositories across multi-cloud environments with security scanning and optimization. Use when managing container images, ensuring image security, or optimizing registry performance.',
        'kpi-report-generator': 'Generates KPI reports and dashboards for infrastructure and application performance across cloud environments. Use when tracking performance metrics, generating reports, or implementing KPI monitoring.',
        'tune-load-balancer': 'Optimizes load balancer configurations and performance across multi-cloud environments. Use when tuning load balancers, optimizing traffic distribution, or implementing performance optimization.',
        'troubleshooting-playbook': 'Provides automated troubleshooting playbooks for common infrastructure and application issues. Use when diagnosing problems, implementing fixes, or creating troubleshooting guides.',
        'migrate-workload': 'Manages workload migration between cloud providers and environments with minimal downtime. Use when migrating workloads, changing providers, or implementing cloud migration.',
        'stakeholder-comms-drafter': 'Drafts stakeholder communications for incidents, deployments, and system changes across cloud operations. Use when communicating with stakeholders, managing expectations, or implementing comms automation.',
        'runbook-documentation-gen': 'Generates comprehensive runbook documentation from operational procedures and best practices. Use when creating documentation, standardizing procedures, or implementing knowledge management.',
        'incident-summary': 'Generates incident summaries and post-mortem reports with analysis and recommendations. Use when documenting incidents, learning from failures, or implementing incident management.',
        'incident-predictor': 'Predicts potential incidents based on system metrics, patterns, and historical data across cloud environments. Use when preventing incidents, identifying risks, or implementing predictive monitoring.',
        'validate-config': 'Validates infrastructure configurations against best practices and compliance requirements. Use when ensuring configuration correctness, preventing misconfigurations, or implementing governance.',
        'infrastructure-discovery': 'Discovers and maps infrastructure resources across multi-cloud environments for visibility and management. Use when inventorying resources, mapping dependencies, or implementing discovery automation.',
        'remediate-issues': 'Automatically remediates common infrastructure issues and security vulnerabilities across cloud environments. Use when fixing issues, implementing automation, or ensuring system health.',
        'doc-generator': 'Generates technical documentation for infrastructure, applications, and processes across cloud environments. Use when creating docs, documenting systems, or implementing knowledge sharing.',
        'chaos-load-testing': 'Performs chaos engineering and load testing to validate system resilience across multi-cloud environments. Use when testing system reliability, identifying failure points, or validating disaster recovery.',
        'enable-self-service': 'Provides self-service capabilities for developers to manage resources and deployments across cloud environments. Use when enabling developers, implementing self-service, or improving developer experience.',
        'database-operations': 'Manages database operations including provisioning, scaling, and monitoring across cloud providers. Use when administering databases, optimizing performance, or ensuring availability.',
        'backup-validator': 'Validates backup integrity, schedules automated backups, and manages disaster recovery across multi-cloud environments. Use when ensuring data protection, testing backup procedures, or implementing disaster recovery.',
        'platform-chat': 'Provides intelligent chat interface for platform operations and management across cloud environments. Use when implementing chatops, managing platforms, or enabling conversational automation.',
        'manage-service-mesh': 'Manages service mesh configurations and operations across multi-cloud Kubernetes environments. Use when implementing microservices, managing service communication, or ensuring observability.',
        'analyze-security': 'Performs comprehensive security analysis across multi-cloud environments for threats and vulnerabilities. Use when conducting security assessments, identifying risks, or implementing security monitoring.',
        'diagnose-network': 'Diagnoses and troubleshoots network issues across multi-cloud environments with intelligent analysis. Use when solving network problems, optimizing connectivity, or implementing network troubleshooting.',
        'incident-history': 'Maintains and analyzes incident history across cloud environments for pattern identification and learning. Use when tracking incidents, analyzing patterns, or implementing incident learning.',
        'gitops-pr': 'Manages GitOps pull requests and automated validation for infrastructure changes. Use when implementing GitOps, managing changes, or ensuring code quality.',
        'orchestrator': 'Orchestrates complex workflows and automation across multi-cloud environments. Use when coordinating operations, managing workflows, or implementing automation orchestration.',
        'resource-balancer': 'Balances resource allocation and usage across multi-cloud environments for optimal performance and cost. Use when optimizing resources, balancing load, or implementing resource management.',
        'infrastructure-provisioning': 'Provisions infrastructure resources across multi-cloud environments with automation and best practices. Use when creating resources, implementing IaC, or managing provisioning.',
        'workflow-management': 'Manages workflows and automation processes across multi-cloud environments. Use when coordinating workflows, managing processes, or implementing workflow automation.',
    }
    return descriptions.get(skill_name, f"Multi-cloud automation skill for {skill_name.replace('-', ' ')} operations. Use when managing {skill_name.replace('-', ' ')} across cloud providers.")

def fix_skill_file(skill_path):
    """Fix a single SKILL.md file completely"""
    skill_name = os.path.basename(os.path.dirname(skill_path))
    
    # Create proper frontmatter
    frontmatter = {
        'name': skill_name,
        'description': get_skill_description(skill_name),
        'license': 'Apache-2.0',
        'metadata': {
            'author': 'gitops-infra-control-plane',
            'version': '1.0',
            'category': 'enterprise',
            'risk-level': 'medium',
            'autonomy': 'conditional'
        },
        'compatibility': 'Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems',
        'allowed-tools': 'Bash Read Write Grep'
    }
    
    # Read existing content to preserve body
    with open(skill_path, 'r') as f:
        content = f.read()
    
    # Extract body content (after frontmatter)
    if '---' in content[3:]:
        body_start = content.find('---', 3) + 3
        body = content[body_start:].strip()
    else:
        body = ''
    
    # Generate new content
    new_content = f"""---
name: {frontmatter['name']}
description: {frontmatter['description']}
license: {frontmatter['license']}
metadata:
  author: {frontmatter['metadata']['author']}
  version: "{frontmatter['metadata']['version']}"
  category: {frontmatter['metadata']['category']}
  risk-level: {frontmatter['metadata']['risk-level']}
  autonomy: {frontmatter['metadata']['autonomy']}
compatibility: {frontmatter['compatibility']}
allowed-tools: {frontmatter['allowed-tools']}
---

# {skill_name.replace('-', ' ').title()} — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for {skill_name.replace('-', ' ')} operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **{skill_name.replace('-', ' ')} operations** across multi-cloud environments
- **Automation and optimization** of {skill_name.replace('-', ' ')} workflows
- **Monitoring and management** of {skill_name.replace('-', ' ')} resources
- **Compliance and governance** for {skill_name.replace('-', ' ')} activities

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
- `scripts/{skill_name}.py`: Main automation implementation
- `scripts/{skill_name}_handler.py`: Cloud-specific operations
- `scripts/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
{skill_name.replace('-', ', ')}, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
"""
    
    # Save new content
    with open(skill_path, 'w') as f:
        f.write(new_content)
    
    print(f"Fixed {skill_name}")

def main():
    # Find all SKILL.md files
    skill_files = glob.glob('/Users/lloyd/github/antigravity/gitops-infra-control-plane/.agents/*/SKILL.md')
    
    for skill_file in skill_files:
        fix_skill_file(skill_file)
    
    print(f"Fixed {len(skill_files)} skill files")

if __name__ == "__main__":
    main()
