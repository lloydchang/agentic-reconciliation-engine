#!/usr/bin/env python3
"""
Compliance Reporter Script

Multi-cloud automation for compliance reporting and audit management across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class ComplianceFramework(Enum):
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    NIST = "nist"
    CIS = "cis"
    CUSTOM = "custom"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL_COMPLIANCE = "partial_compliance"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class ComplianceRequirement:
    requirement_id: str
    framework: ComplianceFramework
    control_id: str
    control_name: str
    description: str
    category: str
    provider: str
    resource_type: str
    test_method: str
    expected_result: str
    severity: SeverityLevel
    automated: bool
    frequency_days: int

@dataclass
class ComplianceCheck:
    check_id: str
    requirement_id: str
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    region: str
    environment: str
    status: ComplianceStatus
    severity: SeverityLevel
    score: float
    details: str
    evidence: List[str]
    recommendations: List[str]
    checked_at: datetime
    checked_by: str
    metadata: Dict[str, Any]

@dataclass
class ComplianceReport:
    report_id: str
    report_name: str
    framework: ComplianceFramework
    provider: str
    environment: str
    period_start: datetime
    period_end: datetime
    overall_status: ComplianceStatus
    overall_score: float
    total_checks: int
    compliant_checks: int
    non_compliant_checks: int
    partial_compliance_checks: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    checks_by_category: Dict[str, int]
    checks_by_severity: Dict[str, int]
    recommendations: List[str]
    generated_at: datetime
    generated_by: str
    metadata: Dict[str, Any]

class ComplianceReporter:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.requirements = {}
        self.reports = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load compliance reporter configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'frameworks': {
                'soc2': {'enabled': True, 'controls': ['security', 'availability', 'processing', 'confidentiality', 'privacy']},
                'iso27001': {'enabled': True, 'controls': ['access_control', 'cryptography', 'physical_security', 'operations_security']},
                'pci_dss': {'enabled': True, 'controls': ['network_security', 'data_protection', 'access_management', 'monitoring']},
                'hipaa': {'enabled': True, 'controls': ['administrative_safeguards', 'physical_safeguards', 'technical_safeguards']},
                'gdpr': {'enabled': True, 'controls': ['data_protection', 'privacy_rights', 'consent_management', 'breach_notification']},
                'nist': {'enabled': True, 'controls': ['access_control', 'audit', 'identification', 'risk_assessment']},
                'cis': {'enabled': True, 'controls': ['iam', 'networking', 'logging', 'monitoring']}
            },
            'reporting_settings': {
                'default_period_days': 30,
                'include_recommendations': True,
                'include_evidence': True,
                'export_formats': ['json', 'pdf', 'csv'],
                'auto_schedule': False,
                'notification_enabled': True
            },
            'scoring_settings': {
                'compliant_weight': 1.0,
                'partial_compliance_weight': 0.5,
                'non_compliant_weight': 0.0,
                'not_applicable_weight': 1.0,
                'severity_weights': {
                    'critical': 0.1,
                    'high': 0.3,
                    'medium': 0.5,
                    'low': 0.8,
                    'info': 1.0
                }
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
    
    def load_compliance_requirements(self, frameworks: List[str], providers: List[str]) -> Dict[str, List[ComplianceRequirement]]:
        """Load compliance requirements for specified frameworks and providers"""
        logger.info(f"Loading compliance requirements for frameworks: {frameworks}, providers: {providers}")
        
        requirements_by_framework = {}
        
        for framework in frameworks:
            if framework not in self.config['frameworks']:
                logger.warning(f"Framework {framework} not in configuration")
                continue
            
            if not self.config['frameworks'][framework]['enabled']:
                logger.info(f"Framework {framework} is disabled")
                continue
            
            try:
                # Initialize provider handler
                handler = self._get_provider_handler('aws')  # Use AWS as default for requirements
                if not handler.initialize_client():
                    raise RuntimeError("Failed to initialize requirements handler")
                
                # Load framework requirements
                framework_requirements = handler.get_framework_requirements(framework, providers)
                requirements_by_framework[framework] = framework_requirements
                
                logger.info(f"Loaded {len(framework_requirements)} requirements for {framework}")
                
            except Exception as e:
                logger.error(f"Failed to load requirements for {framework}: {e}")
                requirements_by_framework[framework] = []
        
        return requirements_by_framework
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific compliance handler"""
        from compliance_reporter_handler import get_compliance_handler
        region = self.config['providers'][provider]['region']
        return get_compliance_handler(provider, region)
    
    def execute_compliance_checks(self, requirements: Dict[str, List[ComplianceRequirement]], 
                                providers: List[str]) -> Dict[str, List[ComplianceCheck]]:
        """Execute compliance checks across providers"""
        logger.info("Executing compliance checks")
        
        checks_by_framework = {}
        
        for framework, framework_requirements in requirements.items():
            framework_checks = []
            
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
                    
                    # Execute checks for this provider
                    provider_checks = handler.execute_compliance_checks(framework_requirements)
                    framework_checks.extend(provider_checks)
                    
                    logger.info(f"Executed {len(provider_checks)} compliance checks for {provider}")
                    
                except Exception as e:
                    logger.error(f"Failed to execute checks for {provider}: {e}")
            
            checks_by_framework[framework] = framework_checks
            logger.info(f"Total checks for {framework}: {len(framework_checks)}")
        
        return checks_by_framework
    
    def analyze_compliance_results(self, checks: Dict[str, List[ComplianceCheck]]) -> Dict[str, Any]:
        """Analyze compliance results and generate insights"""
        logger.info("Analyzing compliance results")
        
        analysis = {
            'summary': {},
            'framework_analysis': {},
            'provider_analysis': {},
            'severity_analysis': {},
            'trend_analysis': {},
            'recommendations': []
        }
        
        # Overall summary
        total_checks = sum(len(framework_checks) for framework_checks in checks.values())
        total_compliant = sum(
            sum(1 for check in framework_checks if check.status == ComplianceStatus.COMPLIANT)
            for framework_checks in checks.values()
        )
        total_non_compliant = sum(
            sum(1 for check in framework_checks if check.status == ComplianceStatus.NON_COMPLIANT)
            for framework_checks in checks.values()
        )
        total_partial = sum(
            sum(1 for check in framework_checks if check.status == ComplianceStatus.PARTIAL_COMPLIANCE)
            for framework_checks in checks.values()
        )
        
        overall_score = (total_compliant + total_partial * 0.5) / total_checks if total_checks > 0 else 0.0
        
        analysis['summary'] = {
            'total_checks': total_checks,
            'compliant_checks': total_compliant,
            'non_compliant_checks': total_non_compliant,
            'partial_compliance_checks': total_partial,
            'overall_score': overall_score,
            'overall_status': self._determine_overall_status(overall_score)
        }
        
        # Framework analysis
        for framework, framework_checks in checks.items():
            framework_compliant = sum(1 for check in framework_checks if check.status == ComplianceStatus.COMPLIANT)
            framework_non_compliant = sum(1 for check in framework_checks if check.status == ComplianceStatus.NON_COMPLIANT)
            framework_partial = sum(1 for check in framework_checks if check.status == ComplianceStatus.PARTIAL_COMPLIANCE)
            framework_score = (framework_compliant + framework_partial * 0.5) / len(framework_checks) if framework_checks else 0.0
            
            analysis['framework_analysis'][framework] = {
                'total_checks': len(framework_checks),
                'compliant_checks': framework_compliant,
                'non_compliant_checks': framework_non_compliant,
                'partial_compliance_checks': framework_partial,
                'score': framework_score,
                'status': self._determine_overall_status(framework_score)
            }
        
        # Provider analysis
        provider_checks = {}
        for framework_checks in checks.values():
            for check in framework_checks:
                provider = check.provider
                if provider not in provider_checks:
                    provider_checks[provider] = []
                provider_checks[provider].append(check)
        
        for provider, provider_check_list in provider_checks.items():
            provider_compliant = sum(1 for check in provider_check_list if check.status == ComplianceStatus.COMPLIANT)
            provider_non_compliant = sum(1 for check in provider_check_list if check.status == ComplianceStatus.NON_COMPLIANT)
            provider_partial = sum(1 for check in provider_check_list if check.status == ComplianceStatus.PARTIAL_COMPLIANCE)
            provider_score = (provider_compliant + provider_partial * 0.5) / len(provider_check_list) if provider_check_list else 0.0
            
            analysis['provider_analysis'][provider] = {
                'total_checks': len(provider_check_list),
                'compliant_checks': provider_compliant,
                'non_compliant_checks': provider_non_compliant,
                'partial_compliance_checks': provider_partial,
                'score': provider_score,
                'status': self._determine_overall_status(provider_score)
            }
        
        # Severity analysis
        severity_counts = {severity.value: 0 for severity in SeverityLevel}
        for framework_checks in checks.values():
            for check in framework_checks:
                if check.status == ComplianceStatus.NON_COMPLIANT:
                    severity_counts[check.severity.value] += 1
        
        analysis['severity_analysis'] = severity_counts
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_compliance_recommendations(checks)
        
        return analysis
    
    def _determine_overall_status(self, score: float) -> ComplianceStatus:
        """Determine overall compliance status based on score"""
        if score >= 0.95:
            return ComplianceStatus.COMPLIANT
        elif score >= 0.80:
            return ComplianceStatus.PARTIAL_COMPLIANCE
        else:
            return ComplianceStatus.NON_COMPLIANT
    
    def _generate_compliance_recommendations(self, checks: Dict[str, List[ComplianceCheck]]) -> List[str]:
        """Generate compliance recommendations based on check results"""
        recommendations = []
        
        try:
            # Analyze common non-compliance patterns
            non_compliant_checks = []
            for framework_checks in checks.values():
                non_compliant_checks.extend([check for check in framework_checks if check.status == ComplianceStatus.NON_COMPLIANT])
            
            # Group by control category
            category_issues = {}
            for check in non_compliant_checks:
                category = check.metadata.get('category', 'unknown')
                if category not in category_issues:
                    category_issues[category] = []
                category_issues[category].append(check)
            
            # Generate recommendations for each category
            for category, category_checks in category_issues.items():
                if len(category_checks) >= 3:
                    recommendations.append(f"Address {len(category_checks)} non-compliant controls in {category} category")
                
                # Get most common recommendations
                all_recommendations = []
                for check in category_checks:
                    all_recommendations.extend(check.recommendations)
                
                if all_recommendations:
                    # Count recommendation frequency
                    rec_counts = {}
                    for rec in all_recommendations:
                        rec_counts[rec] = rec_counts.get(rec, 0) + 1
                    
                    # Get top recommendations
                    top_recs = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                    for rec, count in top_recs:
                        recommendations.append(f"{rec} (affects {count} controls)")
            
            # Critical findings recommendations
            critical_checks = [check for check in non_compliant_checks if check.severity == SeverityLevel.CRITICAL]
            if critical_checks:
                recommendations.append(f"URGENT: Address {len(critical_checks)} critical compliance findings immediately")
            
            # High severity recommendations
            high_checks = [check for check in non_compliant_checks if check.severity == SeverityLevel.HIGH]
            if high_checks:
                recommendations.append(f"HIGH PRIORITY: Address {len(high_checks)} high-severity compliance findings within 30 days")
            
            # General recommendations
            recommendations.extend([
                "Implement automated compliance monitoring to detect issues early",
                "Establish regular compliance review cycles",
                "Create remediation plans for non-compliant controls",
                "Document evidence for compliant controls",
                "Consider implementing compliance-as-code solutions"
            ])
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            recommendations.append("Review compliance findings and implement remediation plans")
        
        return recommendations
    
    def generate_compliance_report(self, framework: str, provider: str, environment: str,
                                 checks: List[ComplianceCheck], 
                                 period_start: datetime, period_end: datetime,
                                 output_file: Optional[str] = None) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        logger.info(f"Generating compliance report for {framework} - {provider}")
        
        try:
            # Calculate statistics
            compliant_checks = [check for check in checks if check.status == ComplianceStatus.COMPLIANT]
            non_compliant_checks = [check for check in checks if check.status == ComplianceStatus.NON_COMPLIANT]
            partial_compliance_checks = [check for check in checks if check.status == ComplianceStatus.PARTIAL_COMPLIANCE]
            
            # Calculate overall score
            scoring = self.config['scoring_settings']
            total_score = 0.0
            total_weight = 0.0
            
            for check in checks:
                weight = scoring['severity_weights'].get(check.severity.value, 1.0)
                
                if check.status == ComplianceStatus.COMPLIANT:
                    score = scoring['compliant_weight']
                elif check.status == ComplianceStatus.PARTIAL_COMPLIANCE:
                    score = scoring['partial_compliance_weight']
                elif check.status == ComplianceStatus.NON_COMPLIANT:
                    score = scoring['non_compliant_weight']
                else:  # NOT_APPLICABLE
                    score = scoring['not_applicable_weight']
                
                total_score += score * weight
                total_weight += weight
            
            overall_score = total_score / total_weight if total_weight > 0 else 0.0
            
            # Count findings by severity
            critical_findings = len([check for check in non_compliant_checks if check.severity == SeverityLevel.CRITICAL])
            high_findings = len([check for check in non_compliant_checks if check.severity == SeverityLevel.HIGH])
            medium_findings = len([check for check in non_compliant_checks if check.severity == SeverityLevel.MEDIUM])
            low_findings = len([check for check in non_compliant_checks if check.severity == SeverityLevel.LOW])
            
            # Group checks by category
            checks_by_category = {}
            for check in checks:
                category = check.metadata.get('category', 'unknown')
                checks_by_category[category] = checks_by_category.get(category, 0) + 1
            
            # Group checks by severity
            checks_by_severity = {}
            for check in checks:
                severity = check.severity.value
                checks_by_severity[severity] = checks_by_severity.get(severity, 0) + 1
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations({framework: checks})
            
            # Determine overall status
            overall_status = self._determine_overall_status(overall_score)
            
            # Create report
            report = ComplianceReport(
                report_id=f"compliance-report-{framework}-{provider}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                report_name=f"{framework.upper()} Compliance Report - {provider.upper()}",
                framework=ComplianceFramework(framework),
                provider=provider,
                environment=environment,
                period_start=period_start,
                period_end=period_end,
                overall_status=overall_status,
                overall_score=overall_score,
                total_checks=len(checks),
                compliant_checks=len(compliant_checks),
                non_compliant_checks=len(non_compliant_checks),
                partial_compliance_checks=len(partial_compliance_checks),
                critical_findings=critical_findings,
                high_findings=high_findings,
                medium_findings=medium_findings,
                low_findings=low_findings,
                checks_by_category=checks_by_category,
                checks_by_severity=checks_by_severity,
                recommendations=recommendations,
                generated_at=datetime.utcnow(),
                generated_by="compliance-reporter",
                metadata={
                    'framework_version': '1.0',
                    'scoring_methodology': 'weighted_average',
                    'include_evidence': self.config['reporting_settings']['include_evidence']
                }
            )
            
            # Save to file if specified
            if output_file:
                report_data = {
                    'report_id': report.report_id,
                    'report_name': report.report_name,
                    'framework': report.framework.value,
                    'provider': report.provider,
                    'environment': report.environment,
                    'period_start': report.period_start.isoformat(),
                    'period_end': report.period_end.isoformat(),
                    'overall_status': report.overall_status.value,
                    'overall_score': report.overall_score,
                    'total_checks': report.total_checks,
                    'compliant_checks': report.compliant_checks,
                    'non_compliant_checks': report.non_compliant_checks,
                    'partial_compliance_checks': report.partial_compliance_checks,
                    'critical_findings': report.critical_findings,
                    'high_findings': report.high_findings,
                    'medium_findings': report.medium_findings,
                    'low_findings': report.low_findings,
                    'checks_by_category': report.checks_by_category,
                    'checks_by_severity': report.checks_by_severity,
                    'recommendations': report.recommendations,
                    'generated_at': report.generated_at.isoformat(),
                    'generated_by': report.generated_by,
                    'metadata': report.metadata,
                    'detailed_checks': [
                        {
                            'check_id': check.check_id,
                            'requirement_id': check.requirement_id,
                            'resource_name': check.resource_name,
                            'resource_type': check.resource_type,
                            'status': check.status.value,
                            'severity': check.severity.value,
                            'score': check.score,
                            'details': check.details,
                            'evidence': check.evidence[:3],  # Limit evidence for readability
                            'recommendations': check.recommendations[:3],  # Limit recommendations
                            'checked_at': check.checked_at.isoformat()
                        }
                        for check in checks[:50]  # Limit detailed checks for readability
                    ]
                }
                
                with open(output_file, 'w') as f:
                    json.dump(report_data, f, indent=2)
                logger.info(f"Compliance report saved to: {output_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            raise
    
    def schedule_compliance_reports(self, frameworks: List[str], providers: List[str], 
                                 frequency_days: int, notification_enabled: bool = True) -> Dict[str, Any]:
        """Schedule automated compliance reports"""
        logger.info(f"Scheduling compliance reports with frequency: {frequency_days} days")
        
        schedule = {
            'schedule_id': f"compliance-schedule-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'frameworks': frameworks,
            'providers': providers,
            'frequency_days': frequency_days,
            'next_run': datetime.utcnow() + timedelta(days=frequency_days),
            'notification_enabled': notification_enabled,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        
        # In a real implementation, this would integrate with a scheduling system
        # For now, we'll just log the schedule
        logger.info(f"Compliance report schedule created: {schedule['schedule_id']}")
        logger.info(f"Next run scheduled for: {schedule['next_run']}")
        
        return schedule
    
    def export_compliance_data(self, checks: Dict[str, List[ComplianceCheck]], 
                             format: str = "json", output_file: Optional[str] = None) -> Dict[str, Any]:
        """Export compliance data in specified format"""
        logger.info(f"Exporting compliance data in {format} format")
        
        try:
            if format.lower() == "json":
                return self._export_json(checks, output_file)
            elif format.lower() == "csv":
                return self._export_csv(checks, output_file)
            elif format.lower() == "pdf":
                return self._export_pdf(checks, output_file)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export compliance data: {e}")
            raise
    
    def _export_json(self, checks: Dict[str, List[ComplianceCheck]], output_file: Optional[str]) -> Dict[str, Any]:
        """Export compliance data as JSON"""
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'total_frameworks': len(checks),
            'total_checks': sum(len(framework_checks) for framework_checks in checks.values()),
            'frameworks': {}
        }
        
        for framework, framework_checks in checks.items():
            framework_data = {
                'total_checks': len(framework_checks),
                'checks': []
            }
            
            for check in framework_checks:
                check_data = {
                    'check_id': check.check_id,
                    'requirement_id': check.requirement_id,
                    'resource_id': check.resource_id,
                    'resource_name': check.resource_name,
                    'resource_type': check.resource_type,
                    'provider': check.provider,
                    'region': check.region,
                    'environment': check.environment,
                    'status': check.status.value,
                    'severity': check.severity.value,
                    'score': check.score,
                    'details': check.details,
                    'evidence': check.evidence,
                    'recommendations': check.recommendations,
                    'checked_at': check.checked_at.isoformat(),
                    'checked_by': check.checked_by,
                    'metadata': check.metadata
                }
                framework_data['checks'].append(check_data)
            
            export_data['frameworks'][framework] = framework_data
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"JSON export saved to: {output_file}")
        
        return export_data
    
    def _export_csv(self, checks: Dict[str, List[ComplianceCheck]], output_file: Optional[str]) -> Dict[str, Any]:
        """Export compliance data as CSV"""
        import csv
        
        csv_data = []
        headers = [
            'framework', 'check_id', 'requirement_id', 'resource_id', 'resource_name',
            'resource_type', 'provider', 'region', 'environment', 'status', 'severity',
            'score', 'details', 'checked_at', 'checked_by'
        ]
        
        for framework, framework_checks in checks.items():
            for check in framework_checks:
                row = [
                    framework,
                    check.check_id,
                    check.requirement_id,
                    check.resource_id,
                    check.resource_name,
                    check.resource_type,
                    check.provider,
                    check.region,
                    check.environment,
                    check.status.value,
                    check.severity.value,
                    check.score,
                    check.details,
                    check.checked_at.isoformat(),
                    check.checked_by
                ]
                csv_data.append(row)
        
        if output_file:
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(csv_data)
            logger.info(f"CSV export saved to: {output_file}")
        
        return {
            'format': 'csv',
            'headers': headers,
            'rows': len(csv_data),
            'data': csv_data
        }
    
    def _export_pdf(self, checks: Dict[str, List[ComplianceCheck]], output_file: Optional[str]) -> Dict[str, Any]:
        """Export compliance data as PDF"""
        # Simplified PDF export - in reality would use a PDF library like ReportLab
        export_data = {
            'format': 'pdf',
            'title': 'Compliance Report',
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_frameworks': len(checks),
                'total_checks': sum(len(framework_checks) for framework_checks in checks.values())
            },
            'note': 'PDF export would require additional PDF library implementation'
        }
        
        if output_file:
            # In a real implementation, this would generate an actual PDF
            with open(output_file, 'w') as f:
                f.write("PDF export not implemented - would require PDF library")
            logger.info(f"PDF export placeholder saved to: {output_file}")
        
        return export_data

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Compliance Reporter")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--action", choices=['check', 'report', 'schedule', 'export'], 
                       default='check', help="Action to perform")
    parser.add_argument("--frameworks", nargs="+", 
                       choices=['soc2', 'iso27001', 'pci_dss', 'hipaa', 'gdpr', 'nist', 'cis'],
                       default=['soc2'], help="Compliance frameworks")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--environment", default="production", help="Environment")
    parser.add_argument("--period-days", type=int, default=30, help="Reporting period in days")
    parser.add_argument("--format", choices=['json', 'csv', 'pdf'], 
                       default='json', help="Export format")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize compliance reporter
    reporter = ComplianceReporter(args.config)
    
    try:
        if args.action == 'check':
            # Load requirements
            requirements = reporter.load_compliance_requirements(args.frameworks, args.providers)
            
            # Execute checks
            checks = reporter.execute_compliance_checks(requirements, args.providers)
            
            # Analyze results
            analysis = reporter.analyze_compliance_results(checks)
            
            print(f"\nCompliance Check Results:")
            summary = analysis['summary']
            print(f"Total Checks: {summary['total_checks']}")
            print(f"Compliant: {summary['compliant_checks']}")
            print(f"Non-Compliant: {summary['non_compliant_checks']}")
            print(f"Partial Compliance: {summary['partial_compliance_checks']}")
            print(f"Overall Score: {summary['overall_score']:.1%}")
            print(f"Overall Status: {summary['overall_status'].value}")
            
            print(f"\nFramework Analysis:")
            for framework, framework_analysis in analysis['framework_analysis'].items():
                print(f"  {framework}: {framework_analysis['score']:.1%} ({framework_analysis['status'].value})")
            
            print(f"\nProvider Analysis:")
            for provider, provider_analysis in analysis['provider_analysis'].items():
                print(f"  {provider}: {provider_analysis['score']:.1%} ({provider_analysis['status'].value})")
            
            print(f"\nSeverity Analysis:")
            for severity, count in analysis['severity_analysis'].items():
                if count > 0:
                    print(f"  {severity}: {count}")
            
            print(f"\nTop Recommendations:")
            for rec in analysis['recommendations'][:5]:
                print(f"  - {rec}")
        
        elif args.action == 'report':
            # Load requirements and execute checks
            requirements = reporter.load_compliance_requirements(args.frameworks, args.providers)
            checks = reporter.execute_compliance_checks(requirements, args.providers)
            
            # Generate reports for each framework
            period_start = datetime.utcnow() - timedelta(days=args.period_days)
            period_end = datetime.utcnow()
            
            for framework in args.frameworks:
                if framework in checks:
                    framework_checks = checks[framework]
                    
                    # Generate report
                    report = reporter.generate_compliance_report(
                        framework, 'multi', args.environment, 
                        framework_checks, period_start, period_end,
                        f"{framework}_compliance_report.json" if args.output else None
                    )
                    
                    print(f"\n{framework.upper()} Compliance Report:")
                    print(f"Report ID: {report.report_id}")
                    print(f"Overall Status: {report.overall_status.value}")
                    print(f"Overall Score: {report.overall_score:.1%}")
                    print(f"Total Checks: {report.total_checks}")
                    print(f"Compliant: {report.compliant_checks}")
                    print(f"Non-Compliant: {report.non_compliant_checks}")
                    print(f"Critical Findings: {report.critical_findings}")
                    print(f"High Findings: {report.high_findings}")
                    print(f"Medium Findings: {report.medium_findings}")
                    print(f"Low Findings: {report.low_findings}")
                    
                    print(f"\nChecks by Category:")
                    for category, count in report.checks_by_category.items():
                        print(f"  {category}: {count}")
                    
                    print(f"\nTop Recommendations:")
                    for rec in report.recommendations[:3]:
                        print(f"  - {rec}")
        
        elif args.action == 'schedule':
            # Schedule automated reports
            schedule = reporter.schedule_compliance_reports(
                args.frameworks, args.providers, args.period_days
            )
            
            print(f"\nCompliance Report Schedule:")
            print(f"Schedule ID: {schedule['schedule_id']}")
            print(f"Frameworks: {', '.join(schedule['frameworks'])}")
            print(f"Providers: {', '.join(schedule['providers'])}")
            print(f"Frequency: {schedule['frequency_days']} days")
            print(f"Next Run: {schedule['next_run']}")
            print(f"Status: {schedule['status']}")
        
        elif args.action == 'export':
            # Load requirements and execute checks
            requirements = reporter.load_compliance_requirements(args.frameworks, args.providers)
            checks = reporter.execute_compliance_checks(requirements, args.providers)
            
            # Export data
            export_result = reporter.export_compliance_data(checks, args.format, args.output)
            
            print(f"\nCompliance Data Export:")
            print(f"Format: {export_result.get('format', 'json')}")
            if 'total_frameworks' in export_result:
                print(f"Total Frameworks: {export_result['total_frameworks']}")
                print(f"Total Checks: {export_result['total_checks']}")
            if 'rows' in export_result:
                print(f"Total Rows: {export_result['rows']}")
            
            if args.output:
                print(f"Export saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Compliance reporting failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
