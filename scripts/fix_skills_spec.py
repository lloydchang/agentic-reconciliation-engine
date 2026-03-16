#!/usr/bin/env python3
"""
Script to fix all SKILL.md files to comply with agentskills.io specification
"""

import os
import re
import glob

def fix_skill_file(skill_path):
    """Fix a single SKILL.md file to comply with specification"""
    with open(skill_path, 'r') as f:
        content = f.read()
    
    # Extract directory name for skill name
    skill_dir = os.path.basename(os.path.dirname(skill_path))
    
    # Fix allowed-tools format
    content = re.sub(
        r'allowed-tools:\s*\n\s*-\s*(.*?)\n\s*-\s*(.*?)\n\s*-\s*(.*?)\n\s*-\s*(.*?)',
        r'allowed-tools: \1 \2 \3 \4',
        content,
        flags=re.MULTILINE
    )
    
    # Fix generic description based on skill name
    skill_descriptions = {
        'ai-agent-orchestration': 'Orchestrates AI agents across multi-cloud environments, coordinates workflows, manages agent lifecycles, and provides intelligent task distribution and monitoring. Use when managing AI agent fleets, coordinating complex workflows, or optimizing agent performance across cloud providers.',
        'alert-prioritizer': 'Prioritizes and categorizes alerts from monitoring systems across multi-cloud environments, applies intelligent filtering and escalation rules, and provides actionable alert summaries. Use when managing alert floods, improving incident response times, or implementing alert management strategies.',
        'alert-router': 'Routes alerts to appropriate teams and systems based on content, severity, and business impact. Use when implementing intelligent alert distribution, team-based alert routing, or automated escalation workflows.',
        'audit-siem': 'Performs security audits and SIEM analysis across multi-cloud environments, detects threats, and generates compliance reports. Use when conducting security assessments, monitoring for threats, or ensuring regulatory compliance.',
        'autoscaler-advisor': 'Provides intelligent autoscaling recommendations and automation for cloud resources across providers. Use when optimizing resource utilization, reducing costs, or implementing scaling strategies.',
        'backup-validator': 'Validates backup integrity, schedules automated backups, and manages disaster recovery across multi-cloud environments. Use when ensuring data protection, testing backup procedures, or implementing disaster recovery.',
        'capacity-planning': 'Analyzes resource usage patterns and provides capacity planning recommendations across cloud providers. Use when forecasting resource needs, optimizing infrastructure costs, or planning scaling activities.',
        'change-management': 'Manages infrastructure changes with approval workflows, rollback capabilities, and compliance tracking. Use when implementing controlled deployments, managing configuration changes, or ensuring change governance.',
        'chaos-load-testing': 'Performs chaos engineering and load testing to validate system resilience across multi-cloud environments. Use when testing system reliability, identifying failure points, or validating disaster recovery.',
        'ci-cd-integrator': 'Integrates CI/CD pipelines across multi-cloud environments with automated testing, deployment, and monitoring. Use when streamlining deployment processes, ensuring code quality, or implementing DevOps workflows.',
        'cicd-pipeline-monitor': 'Monitors CI/CD pipeline health, performance, and success rates with intelligent alerting and optimization. Use when ensuring deployment reliability, tracking pipeline metrics, or optimizing build processes.',
        'cluster-health-check': 'Performs comprehensive health checks on Kubernetes clusters across multi-cloud environments. Use when monitoring cluster status, troubleshooting issues, or ensuring cluster reliability.',
        'compliance-reporter': 'Generates compliance reports and audits for security standards across multi-cloud environments. Use when ensuring regulatory compliance, conducting security audits, or preparing for certifications.',
        'compliance-security-scanner': 'Scans infrastructure and applications for security vulnerabilities and compliance issues. Use when identifying security risks, ensuring compliance, or implementing security best practices.',
        'config-validator': 'Validates infrastructure configurations against best practices and compliance requirements. Use when ensuring configuration correctness, preventing misconfigurations, or implementing governance.',
        'container-registry': 'Manages container image repositories across multi-cloud environments with security scanning and optimization. Use when managing container images, ensuring image security, or optimizing registry performance.',
        'cost-optimizer': 'Analyzes and optimizes cloud costs across providers with intelligent recommendations and automation. Use when reducing expenses, optimizing resource usage, or implementing cost governance.',
        'database-maintenance': 'Performs database maintenance, optimization, and backup procedures across multi-cloud environments. Use when ensuring database performance, managing database health, or implementing maintenance schedules.',
        'database-operations': 'Manages database operations including provisioning, scaling, and monitoring across cloud providers. Use when administering databases, optimizing performance, or ensuring availability.',
        'dependency-checker': 'Analyzes and validates software dependencies for security vulnerabilities and compatibility. Use when managing dependencies, ensuring security, or preventing supply chain issues.',
        'deployment-strategy': 'Implements and manages various deployment strategies including canary, blue-green, and rolling updates. Use when planning deployments, minimizing downtime, or implementing release strategies.',
        'dns-manager': 'Manages DNS configurations across multi-cloud environments with automated failover and monitoring. Use when managing domain records, ensuring DNS reliability, or implementing disaster recovery.',
        'incident-response': 'Coordinates incident response activities across multi-cloud environments with automated workflows and communication. Use when handling incidents, coordinating response teams, or implementing incident management.',
        'infrastructure-health': 'Monitors infrastructure health and performance across multi-cloud environments with predictive analytics. Use when ensuring system reliability, monitoring performance, or preventing outages.',
        'log-analyzer': 'Analyzes logs across multi-cloud environments to detect issues, trends, and security events. Use when troubleshooting problems, monitoring system behavior, or investigating security incidents.',
        'metrics-collector': 'Collects and processes metrics from various sources across multi-cloud environments. Use when monitoring performance, tracking KPIs, or implementing observability.',
        'network-monitor': 'Monitors network performance and security across multi-cloud environments with intelligent alerting. Use when ensuring network reliability, detecting issues, or implementing network security.',
        'performance-tuner': 'Optimizes application and infrastructure performance across multi-cloud environments. Use when improving system performance, reducing latency, or optimizing resource usage.',
        'policy-enforcer': 'Enforces governance and compliance policies across multi-cloud infrastructure automatically. Use when implementing governance, ensuring compliance, or automating policy checks.',
        'resource-allocator': 'Intelligently allocates and manages resources across multi-cloud environments based on demand and cost. Use when optimizing resource distribution, managing capacity, or implementing resource governance.',
        'security-scanner': 'Performs comprehensive security scans across multi-cloud environments for vulnerabilities and misconfigurations. Use when ensuring security, identifying risks, or implementing security monitoring.',
        'service-mesh': 'Manages service mesh configurations and operations across multi-cloud Kubernetes environments. Use when implementing microservices, managing service communication, or ensuring observability.',
        'slack-integration': 'Integrates with Slack for notifications, commands, and workflow automation across cloud operations. Use when enabling team communication, automating notifications, or implementing chatops.',
        'storage-manager': 'Manages storage resources across multi-cloud environments with optimization and lifecycle management. Use when managing data storage, optimizing costs, or implementing data governance.',
        'tenant-onboarding': 'Automates tenant onboarding processes across multi-cloud environments with resource provisioning and access management. Use when adding new tenants, managing multi-tenancy, or implementing onboarding workflows.',
        'user-access': 'Manages user access and permissions across multi-cloud environments with role-based access control. Use when managing user accounts, implementing access control, or ensuring security.',
        'workload-optimizer': 'Optimizes workload placement and performance across multi-cloud environments intelligently. Use when distributing workloads, optimizing performance, or implementing workload management.',
    }
    
    # Update description if generic
    generic_desc = "World-class multi-cloud enterprise automation skill that provides intelligent operations across AWS, Azure, GCP, and on-premise environments with comprehensive validation and compliance workflows."
    if generic_desc in content:
        desc = skill_descriptions.get(skill_dir, f"Multi-cloud automation skill for {skill_dir.replace('-', ' ')} operations. Use when managing {skill_dir.replace('-', ' ')} across cloud providers.")
        content = content.replace(generic_desc, desc)
    
    # Save updated content
    with open(skill_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {skill_path}")

def main():
    # Find all SKILL.md files
    skill_files = glob.glob('/Users/lloyd/github/antigravity/gitops-infra-control-plane/.agents/*/SKILL.md')
    
    for skill_file in skill_files:
        fix_skill_file(skill_file)
    
    print(f"Fixed {len(skill_files)} skill files")

if __name__ == "__main__":
    main()
