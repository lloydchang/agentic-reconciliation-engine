#!/usr/bin/env python3
"""
Security Analysis Script

Multi-cloud automation for comprehensive security analysis across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class SecurityRiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SecurityCategory(Enum):
    NETWORK = "network"
    IDENTITY = "identity"
    DATA = "data"
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    COMPLIANCE = "compliance"

class ThreatType(Enum):
    MALWARE = "malware"
    PHISHING = "phishing"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    DENIAL_OF_SERVICE = "denial_of_service"
    INSIDER_THREAT = "insider_threat"
    VULNERABILITY = "vulnerability"
    MISCONFIGURATION = "misconfiguration"

@dataclass
class SecurityFinding:
    finding_id: str
    title: str
    description: str
    risk_level: SecurityRiskLevel
    category: SecurityCategory
    threat_type: Optional[ThreatType]
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    discovered_at: datetime
    severity_score: float
    impact_score: float
    likelihood_score: float
    affected_assets: List[str]
    remediation_steps: List[str]
    compliance_references: List[str]
    cve_ids: List[str]

@dataclass
class SecurityPolicy:
    policy_id: str
    policy_name: str
    description: str
    category: SecurityCategory
    provider: str
    rules: List[Dict[str, Any]]
    enabled: bool
    last_updated: datetime
    violation_count: int

@dataclass
class SecurityAnalysisResult:
    analysis_id: str
    provider: str
    environment: str
    analyzed_at: datetime
    total_findings: int
    findings_by_risk: Dict[str, int]
    findings_by_category: Dict[str, int]
    overall_risk_score: float
    compliance_score: float
    recommendations: List[str]
    policy_violations: List[str]
    trend_analysis: Dict[str, Any]

class SecurityAnalyzer:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.policies = {}
        self.findings = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load security analysis configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'analysis_settings': {
                'enable_ml_analysis': True,
                'risk_threshold': 0.7,
                'compliance_threshold': 0.8,
                'include_historical_trends': True,
                'generate_recommendations': True,
                'threat_intelligence_enabled': True
            },
            'scanning_parameters': {
                'depth_level': 'comprehensive',
                'include_sensitive_data': True,
                'scan_network_configurations': True,
                'scan_identity_management': True,
                'scan_data_protection': True,
                'scan_applications': True
            }
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def load_security_policies(self, policies_file: Optional[str] = None) -> Dict[str, SecurityPolicy]:
        """Load security policies"""
        logger.info("Loading security policies")
        
        # Default security policies
        default_policies = {
            'aws-cis-benchmark': SecurityPolicy(
                policy_id='aws-cis-benchmark',
                policy_name='AWS CIS Foundations Benchmark',
                description='CIS AWS Foundations Benchmark security controls',
                category=SecurityCategory.COMPLIANCE,
                provider='aws',
                rules=[
                    {
                        'rule_id': 'IAM-1',
                        'description': 'Ensure IAM password policy requires password length of at least 14 characters',
                        'check_command': 'aws iam get-account-password-policy',
                        'expected_result': 'MinimumPasswordLength >= 14'
                    },
                    {
                        'rule_id': 'IAM-2',
                        'description': 'Ensure IAM password policy prevents password reuse',
                        'check_command': 'aws iam get-account-password-policy',
                        'expected_result': 'PasswordReusePrevention is enabled'
                    },
                    {
                        'rule_id': 'S3-1',
                        'description': 'Ensure S3 bucket access logging is enabled on the CloudTrail S3 bucket',
                        'check_command': 'aws s3api get-bucket-logging --bucket <BUCKET_NAME>',
                        'expected_result': 'Logging is enabled'
                    },
                    {
                        'rule_id': 'EC2-1',
                        'description': 'Ensure EC2 instances have appropriate IAM roles attached',
                        'check_command': 'aws ec2 describe-instances',
                        'expected_result': 'IAM instance profile is attached'
                    }
                ],
                enabled=True,
                last_updated=datetime.utcnow() - timedelta(days=7),
                violation_count=0
            ),
            'azure-security-baseline': SecurityPolicy(
                policy_id='azure-security-baseline',
                policy_name='Azure Security Baseline',
                description='Microsoft Azure security baseline policies',
                category=SecurityCategory.COMPLIANCE,
                provider='azure',
                rules=[
                    {
                        'rule_id': 'AAD-1',
                        'description': 'Ensure Multi-Factor Authentication is enabled for all users',
                        'check_command': 'az ad user list',
                        'expected_result': 'MFA is enabled'
                    },
                    {
                        'rule_id': 'Network-1',
                        'description': 'Ensure Network Security Groups are properly configured',
                        'check_command': 'az network nsg list',
                        'expected_result': 'NSG rules are restrictive'
                    },
                    {
                        'rule_id': 'Storage-1',
                        'description': 'Ensure storage accounts use encryption',
                        'check_command': 'az storage account show',
                        'expected_result': 'Encryption is enabled'
                    }
                ],
                enabled=True,
                last_updated=datetime.utcnow() - timedelta(days=5),
                violation_count=0
            ),
            'gcp-security-foundations': SecurityPolicy(
                policy_id='gcp-security-foundations',
                policy_name='GCP Security Foundations',
                description='Google Cloud Platform security foundations',
                category=SecurityCategory.COMPLIANCE,
                provider='gcp',
                rules=[
                    {
                        'rule_id': 'IAM-1',
                        'description': 'Ensure IAM service accounts have minimal permissions',
                        'check_command': 'gcloud iam service-accounts list',
                        'expected_result': 'Least privilege principle applied'
                    },
                    {
                        'rule_id': 'Network-1',
                        'description': 'Ensure VPC flow logs are enabled',
                        'check_command': 'gcloud compute routers describe',
                        'expected_result': 'Flow logs are enabled'
                    },
                    {
                        'rule_id': 'Storage-1',
                        'description': 'Ensure Cloud Storage buckets have uniform bucket-level access',
                        'check_command': 'gsutil iam get <BUCKET_NAME>',
                        'expected_result': 'Uniform access is enabled'
                    }
                ],
                enabled=True,
                last_updated=datetime.utcnow() - timedelta(days=3),
                violation_count=0
            )
        }
        
        # Load custom policies from file if provided
        if policies_file:
            try:
                with open(policies_file, 'r') as f:
                    custom_policies = json.load(f)
                
                for policy_id, policy_data in custom_policies.items():
                    policy = SecurityPolicy(
                        policy_id=policy_id,
                        policy_name=policy_data['policy_name'],
                        description=policy_data['description'],
                        category=SecurityCategory(policy_data['category']),
                        provider=policy_data['provider'],
                        rules=policy_data['rules'],
                        enabled=policy_data.get('enabled', True),
                        last_updated=datetime.fromisoformat(policy_data['last_updated']),
                        violation_count=0
                    )
                    default_policies[policy_id] = policy
                    
            except Exception as e:
                logger.warning(f"Failed to load custom policies: {e}")
        
        self.policies = default_policies
        logger.info(f"Loaded {len(self.policies)} security policies")
        
        return self.policies
    
    def analyze_security(self, providers: List[str], environment: str = 'production') -> Dict[str, SecurityAnalysisResult]:
        """Perform comprehensive security analysis"""
        logger.info(f"Starting security analysis for providers: {providers}")
        
        analysis_results = {}
        
        for provider in providers:
            if provider not in self.config['providers']:
                logger.warning(f"Provider {provider} not in configuration")
                continue
            
            if not self.config['providers'][provider]['enabled']:
                logger.info(f"Provider {provider} is disabled")
                continue
            
            try:
                # Initialize provider handler
                handler = self._get_provider_handler(provider)
                if not handler.initialize_client():
                    raise RuntimeError(f"Failed to initialize {provider} handler")
                
                # Perform security analysis
                result = self._analyze_provider_security(handler, provider, environment)
                analysis_results[provider] = result
                
                logger.info(f"Security analysis completed for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to analyze security for {provider}: {e}")
                # Create a failed result
                result = SecurityAnalysisResult(
                    analysis_id=f"failed-{provider}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    environment=environment,
                    analyzed_at=datetime.utcnow(),
                    total_findings=0,
                    findings_by_risk={},
                    findings_by_category={},
                    overall_risk_score=0.0,
                    compliance_score=0.0,
                    recommendations=[f"Security analysis failed: {str(e)}"],
                    policy_violations=[],
                    trend_analysis={}
                )
                analysis_results[provider] = result
        
        return analysis_results
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific security handler"""
        from security_analysis_handler import get_security_handler
        region = self.config['providers'][provider]['region']
        return get_security_handler(provider, region)
    
    def _analyze_provider_security(self, handler, provider: str, environment: str) -> SecurityAnalysisResult:
        """Analyze security for a specific provider"""
        logger.info(f"Analyzing security for {provider}")
        
        # Collect security findings
        findings = []
        
        # Network security analysis
        network_findings = self._analyze_network_security(handler, provider)
        findings.extend(network_findings)
        
        # Identity and access management analysis
        identity_findings = self._analyze_identity_security(handler, provider)
        findings.extend(identity_findings)
        
        # Data protection analysis
        data_findings = self._analyze_data_security(handler, provider)
        findings.extend(data_findings)
        
        # Infrastructure security analysis
        infrastructure_findings = self._analyze_infrastructure_security(handler, provider)
        findings.extend(infrastructure_findings)
        
        # Application security analysis
        application_findings = self._analyze_application_security(handler, provider)
        findings.extend(application_findings)
        
        # Compliance analysis
        compliance_findings = self._analyze_compliance(handler, provider)
        findings.extend(compliance_findings)
        
        # Calculate metrics
        total_findings = len(findings)
        findings_by_risk = self._group_findings_by_risk(findings)
        findings_by_category = self._group_findings_by_category(findings)
        overall_risk_score = self._calculate_overall_risk_score(findings)
        compliance_score = self._calculate_compliance_score(findings, provider)
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(findings, provider)
        
        # Check policy violations
        policy_violations = self._check_policy_violations(findings, provider)
        
        # Generate trend analysis
        trend_analysis = self._generate_trend_analysis(findings, provider)
        
        # Create analysis result
        result = SecurityAnalysisResult(
            analysis_id=f"analysis-{provider}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            provider=provider,
            environment=environment,
            analyzed_at=datetime.utcnow(),
            total_findings=total_findings,
            findings_by_risk=findings_by_risk,
            findings_by_category=findings_by_category,
            overall_risk_score=overall_risk_score,
            compliance_score=compliance_score,
            recommendations=recommendations,
            policy_violations=policy_violations,
            trend_analysis=trend_analysis
        )
        
        # Store findings
        self.findings.extend(findings)
        
        return result
    
    def _analyze_network_security(self, handler, provider: str) -> List[SecurityFinding]:
        """Analyze network security"""
        findings = []
        
        try:
            # Check network configurations
            network_issues = handler.check_network_security()
            
            for issue in network_issues:
                finding = SecurityFinding(
                    finding_id=f"network-{provider}-{len(findings)}",
                    title=issue['title'],
                    description=issue['description'],
                    risk_level=SecurityRiskLevel(issue['risk_level']),
                    category=SecurityCategory.NETWORK,
                    threat_type=ThreatType(issue.get('threat_type', 'MISCONFIGURATION')),
                    provider=provider,
                    resource_id=issue['resource_id'],
                    resource_name=issue['resource_name'],
                    environment='production',
                    discovered_at=datetime.utcnow(),
                    severity_score=issue['severity_score'],
                    impact_score=issue['impact_score'],
                    likelihood_score=issue['likelihood_score'],
                    affected_assets=issue['affected_assets'],
                    remediation_steps=issue['remediation_steps'],
                    compliance_references=issue.get('compliance_references', []),
                    cve_ids=issue.get('cve_ids', [])
                )
                findings.append(finding)
            
        except Exception as e:
            logger.error(f"Failed to analyze network security: {e}")
        
        return findings
    
    def _analyze_identity_security(self, handler, provider: str) -> List[SecurityFinding]:
        """Analyze identity and access management security"""
        findings = []
        
        try:
            # Check IAM configurations
            identity_issues = handler.check_identity_security()
            
            for issue in identity_issues:
                finding = SecurityFinding(
                    finding_id=f"identity-{provider}-{len(findings)}",
                    title=issue['title'],
                    description=issue['description'],
                    risk_level=SecurityRiskLevel(issue['risk_level']),
                    category=SecurityCategory.IDENTITY,
                    threat_type=ThreatType(issue.get('threat_type', 'UNAUTHORIZED_ACCESS')),
                    provider=provider,
                    resource_id=issue['resource_id'],
                    resource_name=issue['resource_name'],
                    environment='production',
                    discovered_at=datetime.utcnow(),
                    severity_score=issue['severity_score'],
                    impact_score=issue['impact_score'],
                    likelihood_score=issue['likelihood_score'],
                    affected_assets=issue['affected_assets'],
                    remediation_steps=issue['remediation_steps'],
                    compliance_references=issue.get('compliance_references', []),
                    cve_ids=issue.get('cve_ids', [])
                )
                findings.append(finding)
            
        except Exception as e:
            logger.error(f"Failed to analyze identity security: {e}")
        
        return findings
    
    def _analyze_data_security(self, handler, provider: str) -> List[SecurityFinding]:
        """Analyze data protection security"""
        findings = []
        
        try:
            # Check data protection configurations
            data_issues = handler.check_data_security()
            
            for issue in data_issues:
                finding = SecurityFinding(
                    finding_id=f"data-{provider}-{len(findings)}",
                    title=issue['title'],
                    description=issue['description'],
                    risk_level=SecurityRiskLevel(issue['risk_level']),
                    category=SecurityCategory.DATA,
                    threat_type=ThreatType(issue.get('threat_type', 'DATA_BREACH')),
                    provider=provider,
                    resource_id=issue['resource_id'],
                    resource_name=issue['resource_name'],
                    environment='production',
                    discovered_at=datetime.utcnow(),
                    severity_score=issue['severity_score'],
                    impact_score=issue['impact_score'],
                    likelihood_score=issue['likelihood_score'],
                    affected_assets=issue['affected_assets'],
                    remediation_steps=issue['remediation_steps'],
                    compliance_references=issue.get('compliance_references', []),
                    cve_ids=issue.get('cve_ids', [])
                )
                findings.append(finding)
            
        except Exception as e:
            logger.error(f"Failed to analyze data security: {e}")
        
        return findings
    
    def _analyze_infrastructure_security(self, handler, provider: str) -> List[SecurityFinding]:
        """Analyze infrastructure security"""
        findings = []
        
        try:
            # Check infrastructure configurations
            infrastructure_issues = handler.check_infrastructure_security()
            
            for issue in infrastructure_issues:
                finding = SecurityFinding(
                    finding_id=f"infrastructure-{provider}-{len(findings)}",
                    title=issue['title'],
                    description=issue['description'],
                    risk_level=SecurityRiskLevel(issue['risk_level']),
                    category=SecurityCategory.INFRASTRUCTURE,
                    threat_type=ThreatType(issue.get('threat_type', 'VULNERABILITY')),
                    provider=provider,
                    resource_id=issue['resource_id'],
                    resource_name=issue['resource_name'],
                    environment='production',
                    discovered_at=datetime.utcnow(),
                    severity_score=issue['severity_score'],
                    impact_score=issue['impact_score'],
                    likelihood_score=issue['likelihood_score'],
                    affected_assets=issue['affected_assets'],
                    remediation_steps=issue['remediation_steps'],
                    compliance_references=issue.get('compliance_references', []),
                    cve_ids=issue.get('cve_ids', [])
                )
                findings.append(finding)
            
        except Exception as e:
            logger.error(f"Failed to analyze infrastructure security: {e}")
        
        return findings
    
    def _analyze_application_security(self, handler, provider: str) -> List[SecurityFinding]:
        """Analyze application security"""
        findings = []
        
        try:
            # Check application security configurations
            application_issues = handler.check_application_security()
            
            for issue in application_issues:
                finding = SecurityFinding(
                    finding_id=f"application-{provider}-{len(findings)}",
                    title=issue['title'],
                    description=issue['description'],
                    risk_level=SecurityRiskLevel(issue['risk_level']),
                    category=SecurityCategory.APPLICATION,
                    threat_type=ThreatType(issue.get('threat_type', 'MALWARE')),
                    provider=provider,
                    resource_id=issue['resource_id'],
                    resource_name=issue['resource_name'],
                    environment='production',
                    discovered_at=datetime.utcnow(),
                    severity_score=issue['severity_score'],
                    impact_score=issue['impact_score'],
                    likelihood_score=issue['likelihood_score'],
                    affected_assets=issue['affected_assets'],
                    remediation_steps=issue['remediation_steps'],
                    compliance_references=issue.get('compliance_references', []),
                    cve_ids=issue.get('cve_ids', [])
                )
                findings.append(finding)
            
        except Exception as e:
            logger.error(f"Failed to analyze application security: {e}")
        
        return findings
    
    def _analyze_compliance(self, handler, provider: str) -> List[SecurityFinding]:
        """Analyze compliance"""
        findings = []
        
        try:
            # Check compliance against policies
            compliance_issues = handler.check_compliance()
            
            for issue in compliance_issues:
                finding = SecurityFinding(
                    finding_id=f"compliance-{provider}-{len(findings)}",
                    title=issue['title'],
                    description=issue['description'],
                    risk_level=SecurityRiskLevel(issue['risk_level']),
                    category=SecurityCategory.COMPLIANCE,
                    threat_type=None,
                    provider=provider,
                    resource_id=issue['resource_id'],
                    resource_name=issue['resource_name'],
                    environment='production',
                    discovered_at=datetime.utcnow(),
                    severity_score=issue['severity_score'],
                    impact_score=issue['impact_score'],
                    likelihood_score=issue['likelihood_score'],
                    affected_assets=issue['affected_assets'],
                    remediation_steps=issue['remediation_steps'],
                    compliance_references=issue.get('compliance_references', []),
                    cve_ids=[]
                )
                findings.append(finding)
            
        except Exception as e:
            logger.error(f"Failed to analyze compliance: {e}")
        
        return findings
    
    def _group_findings_by_risk(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Group findings by risk level"""
        risk_counts = {}
        
        for finding in findings:
            risk_level = finding.risk_level.value
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        return risk_counts
    
    def _group_findings_by_category(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Group findings by category"""
        category_counts = {}
        
        for finding in findings:
            category = finding.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return category_counts
    
    def _calculate_overall_risk_score(self, findings: List[SecurityFinding]) -> float:
        """Calculate overall risk score"""
        if not findings:
            return 0.0
        
        # Weighted risk calculation
        risk_weights = {
            SecurityRiskLevel.CRITICAL: 1.0,
            SecurityRiskLevel.HIGH: 0.8,
            SecurityRiskLevel.MEDIUM: 0.6,
            SecurityRiskLevel.LOW: 0.4,
            SecurityRiskLevel.INFO: 0.2
        }
        
        total_risk = 0.0
        for finding in findings:
            weight = risk_weights.get(finding.risk_level, 0.5)
            risk_score = finding.severity_score * finding.impact_score * finding.likelihood_score
            total_risk += weight * risk_score
        
        # Normalize to 0-1 scale
        max_possible_risk = len(findings) * 1.0  # Maximum risk score per finding
        normalized_risk = min(total_risk / max_possible_risk, 1.0) if max_possible_risk > 0 else 0.0
        
        return normalized_risk
    
    def _calculate_compliance_score(self, findings: List[SecurityFinding], provider: str) -> float:
        """Calculate compliance score"""
        try:
            # Get applicable policies for provider
            applicable_policies = [p for p in self.policies.values() if p.provider == provider and p.enabled]
            
            if not applicable_policies:
                return 0.0
            
            total_rules = sum(len(policy.rules) for policy in applicable_policies)
            
            # Count violations
            violations = 0
            for finding in findings:
                if finding.category == SecurityCategory.COMPLIANCE:
                    violations += 1
            
            # Calculate compliance score
            compliance_score = (total_rules - violations) / total_rules if total_rules > 0 else 0.0
            
            return compliance_score
            
        except Exception as e:
            logger.error(f"Failed to calculate compliance score: {e}")
            return 0.0
    
    def _generate_security_recommendations(self, findings: List[SecurityFinding], provider: str) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Group findings by category
        findings_by_category = {}
        for finding in findings:
            category = finding.category.value
            if category not in findings_by_category:
                findings_by_category[category] = []
            findings_by_category[category].append(finding)
        
        # Generate recommendations for each category
        for category, category_findings in findings_by_category.items():
            if category == 'network':
                recommendations.extend([
                    "Review and update network security groups/firewall rules",
                    "Implement network segmentation for critical assets",
                    "Enable network traffic logging and monitoring",
                    "Configure DDoS protection and rate limiting"
                ])
            elif category == 'identity':
                recommendations.extend([
                    "Implement multi-factor authentication for all users",
                    "Review and minimize privileged access permissions",
                    "Enable regular access reviews and certifications",
                    "Implement just-in-time access for privileged operations"
                ])
            elif category == 'data':
                recommendations.extend([
                    "Enable encryption for data at rest and in transit",
                    "Implement data classification and tagging",
                    "Configure data loss prevention policies",
                    "Regular backup and disaster recovery testing"
                ])
            elif category == 'infrastructure':
                recommendations.extend([
                    "Enable security monitoring and alerting",
                    "Regular patch management and vulnerability scanning",
                    "Implement infrastructure as code security scanning",
                    "Configure secure boot and trusted boot"
                ])
            elif category == 'application':
                recommendations.extend([
                    "Implement secure software development lifecycle",
                    "Regular application security testing",
                    "Container security scanning and runtime protection",
                    "API security and rate limiting"
                ])
            elif category == 'compliance':
                recommendations.extend([
                    "Implement automated compliance monitoring",
                    "Regular security policy reviews and updates",
                    "Maintain comprehensive audit trails",
                    "Implement security awareness training programs"
                ])
        
        # Add provider-specific recommendations
        if provider == 'aws':
            recommendations.extend([
                "Enable AWS Security Hub for centralized security monitoring",
                "Implement AWS Config rules for continuous compliance checking",
                "Use AWS GuardDuty for threat detection",
                "Enable AWS Macie for data discovery and classification"
            ])
        elif provider == 'azure':
            recommendations.extend([
                "Enable Microsoft Defender for Cloud",
                "Implement Azure Security Center recommendations",
                "Use Azure Sentinel for SIEM and threat intelligence",
                "Enable Azure Information Protection for data classification"
            ])
        elif provider == 'gcp':
            recommendations.extend([
                    "Enable Google Cloud Security Command Center",
                    "Implement Cloud Asset Inventory for resource tracking",
                    "Use Security Health Analytics for risk assessment",
                    "Enable Context-Aware Access for fine-grained permissions"
                ])
        
        # Remove duplicates and limit to top recommendations
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:15]
    
    def _check_policy_violations(self, findings: List[SecurityFinding], provider: str) -> List[str]:
        """Check policy violations"""
        violations = []
        
        try:
            # Get applicable policies
            applicable_policies = [p for p in self.policies.values() if p.provider == provider and p.enabled]
            
            for policy in applicable_policies:
                for rule in policy.rules:
                    # Check if any finding violates this rule
                    for finding in findings:
                        if self._is_policy_violation(finding, rule):
                            violations.append(f"{policy.policy_name}: {rule['description']}")
                            break
            
        except Exception as e:
            logger.error(f"Failed to check policy violations: {e}")
        
        return violations
    
    def _is_policy_violation(self, finding: SecurityFinding, rule: Dict[str, Any]) -> bool:
        """Check if finding violates a specific rule"""
        # Simplified violation check
        # In real implementation, this would be more sophisticated
        return finding.category.value.lower() in rule['description'].lower()
    
    def _generate_trend_analysis(self, findings: List[SecurityFinding], provider: str) -> Dict[str, Any]:
        """Generate trend analysis"""
        try:
            # Get historical findings for trend analysis
            historical_findings = [f for f in self.findings if f.provider == provider]
            
            # Calculate trends
            trend_analysis = {
                'new_findings_this_week': len([f for f in findings if (datetime.utcnow() - f.discovered_at).days <= 7]),
                'critical_findings_trend': self._calculate_critical_trend(historical_findings),
                'most_common_categories': self._get_most_common_categories(historical_findings),
                'average_resolution_time': self._calculate_avg_resolution_time(historical_findings),
                'recurring_issues': self._identify_recurring_issues(historical_findings)
            }
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to generate trend analysis: {e}")
            return {}
    
    def _calculate_critical_trend(self, findings: List[SecurityFinding]) -> str:
        """Calculate critical findings trend"""
        try:
            # Get critical findings from last 30 days
            recent_critical = [f for f in findings 
                             if f.risk_level == SecurityRiskLevel.CRITICAL 
                             and (datetime.utcnow() - f.discovered_at).days <= 30]
            
            # Get critical findings from previous 30 days
            previous_critical = [f for f in findings 
                                if f.risk_level == SecurityRiskLevel.CRITICAL 
                                and 30 < (datetime.utcnow() - f.discovered_at).days <= 60]
            
            if len(previous_critical) == 0:
                return "increasing" if len(recent_critical) > 0 else "stable"
            
            if len(recent_critical) > len(previous_critical):
                return "increasing"
            elif len(recent_critical) < len(previous_critical):
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Failed to calculate critical trend: {e}")
            return "unknown"
    
    def _get_most_common_categories(self, findings: List[SecurityFinding]) -> List[str]:
        """Get most common security categories"""
        try:
            category_counts = {}
            for finding in findings:
                category = finding.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            return [category for category, count in sorted_categories[:5]]
            
        except Exception as e:
            logger.error(f"Failed to get most common categories: {e}")
            return []
    
    def _calculate_avg_resolution_time(self, findings: List[SecurityFinding]) -> float:
        """Calculate average resolution time"""
        try:
            # Simplified calculation - in real implementation would track actual resolution times
            return 72.0  # hours
            
        except Exception as e:
            logger.error(f"Failed to calculate average resolution time: {e}")
            return 0.0
    
    def _identify_recurring_issues(self, findings: List[SecurityFinding]) -> List[str]:
        """Identify recurring security issues"""
        try:
            # Simplified recurring issue identification
            recurring = []
            
            # Group by title similarity
            title_groups = {}
            for finding in findings:
                title_key = finding.title.lower().replace(' ', '_').replace('-', '_')
                if title_key not in title_groups:
                    title_groups[title_key] = []
                title_groups[title_key].append(finding)
            
            # Find groups with multiple occurrences
            for title_key, group_findings in title_groups.items():
                if len(group_findings) >= 3:
                    recurring.append(group_findings[0].title)
            
            return recurring[:5]
            
        except Exception as e:
            logger.error(f"Failed to identify recurring issues: {e}")
            return []
    
    def generate_security_report(self, analysis_results: Dict[str, SecurityAnalysisResult], 
                                output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        logger.info("Generating security report")
        
        # Calculate overall statistics
        total_findings = sum(result.total_findings for result in analysis_results.values())
        total_critical = sum(len([f for f in self.findings if f.risk_level == SecurityRiskLevel.CRITICAL and f.provider in analysis_results]) for result in analysis_results.values())
        total_high = sum(len([f for f in self.findings if f.risk_level == SecurityRiskLevel.HIGH and f.provider in analysis_results]) for result in analysis_results.values())
        
        # Calculate average scores
        avg_risk_score = sum(result.overall_risk_score for result in analysis_results.values()) / len(analysis_results) if analysis_results else 0
        avg_compliance_score = sum(result.compliance_score for result in analysis_results.values()) / len(analysis_results) if analysis_results else 0
        
        # Provider comparisons
        provider_comparison = {}
        for provider, result in analysis_results.items():
            provider_comparison[provider] = {
                'total_findings': result.total_findings,
                'risk_score': result.overall_risk_score,
                'compliance_score': result.compliance_score,
                'critical_findings': result.findings_by_risk.get('critical', 0),
                'policy_violations': len(result.policy_violations)
            }
        
        # Top recommendations
        all_recommendations = []
        for result in analysis_results.values():
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates and get top recommendations
        unique_recommendations = list(set(all_recommendations))
        top_recommendations = sorted(unique_recommendations, key=lambda x: len(x), reverse=True)[:10]
        
        # Risk distribution
        risk_distribution = {}
        category_distribution = {}
        for result in analysis_results.values():
            for risk_level, count in result.findings_by_risk.items():
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + count
            for category, count in result.findings_by_category.items():
                category_distribution[category] = category_distribution.get(category, 0) + count
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_providers_analyzed': len(analysis_results),
                'total_findings': total_findings,
                'critical_findings': total_critical,
                'high_findings': total_high,
                'average_risk_score': avg_risk_score,
                'average_compliance_score': avg_compliance_score,
                'enabled_policies': len([p for p in self.policies.values() if p.enabled])
            },
            'provider_comparison': provider_comparison,
            'risk_distribution': risk_distribution,
            'category_distribution': category_distribution,
            'top_recommendations': top_recommendations,
            'detailed_results': {
                provider: {
                    'analysis_id': result.analysis_id,
                    'total_findings': result.total_findings,
                    'findings_by_risk': result.findings_by_risk,
                    'findings_by_category': result.findings_by_category,
                    'risk_score': result.overall_risk_score,
                    'compliance_score': result.compliance_score,
                    'recommendations': result.recommendations[:5],
                    'policy_violations': result.policy_violations[:5],
                    'trend_analysis': result.trend_analysis
                }
                for provider, result in analysis_results.items()
            }
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Security report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Security Analyzer")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--policies", help="Security policies file")
    parser.add_argument("--action", choices=['analyze', 'report'], 
                       default='analyze', help="Action to perform")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--environment", default='production', help="Environment to analyze")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize security analyzer
    analyzer = SecurityAnalyzer(args.config)
    
    # Load policies
    analyzer.load_security_policies(args.policies)
    
    try:
        if args.action == 'analyze':
            # Perform security analysis
            results = analyzer.analyze_security(args.providers, args.environment)
            
            print(f"\nSecurity Analysis Results:")
            for provider, result in results.items():
                print(f"\n{provider.upper()}:")
                print(f"  Total Findings: {result.total_findings}")
                print(f"  Risk Score: {result.overall_risk_score:.2f}")
                print(f"  Compliance Score: {result.compliance_score:.2f}")
                print(f"  Critical Findings: {result.findings_by_risk.get('critical', 0)}")
                print(f"  High Findings: {result.findings_by_risk.get('high', 0)}")
                print(f"  Policy Violations: {len(result.policy_violations)}")
                
                if result.recommendations:
                    print(f"  Top Recommendations:")
                    for rec in result.recommendations[:3]:
                        print(f"    - {rec}")
        
        elif args.action == 'report':
            # Perform analysis first
            results = analyzer.analyze_security(args.providers, args.environment)
            
            # Generate report
            report = analyzer.generate_security_report(results, args.output)
            
            summary = report['summary']
            print(f"\nSecurity Analysis Report:")
            print(f"Providers Analyzed: {summary['total_providers_analyzed']}")
            print(f"Total Findings: {summary['total_findings']}")
            print(f"Critical Findings: {summary['critical_findings']}")
            print(f"High Findings: {summary['high_findings']}")
            print(f"Average Risk Score: {summary['average_risk_score']:.2f}")
            print(f"Average Compliance Score: {summary['average_compliance_score']:.2f}")
            print(f"Enabled Policies: {summary['enabled_policies']}")
            
            print(f"\nRisk Distribution:")
            for risk, count in report['risk_distribution'].items():
                print(f"  {risk}: {count}")
            
            print(f"\nCategory Distribution:")
            for category, count in report['category_distribution'].items():
                print(f"  {category}: {count}")
            
            print(f"\nTop Recommendations:")
            for rec in report['top_recommendations'][:5]:
                print(f"  - {rec}")
            
            if args.output:
                print(f"\nReport saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Security analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
