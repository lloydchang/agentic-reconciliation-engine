#!/usr/bin/env python3
"""
Compliance Evaluator for AI Agent Systems

Evaluates compliance aspects including:
- Regulatory compliance (GDPR, HIPAA, SOX)
- Industry standards (ISO 27001, NIST)
- Internal policies and procedures
- Data governance requirements
- Audit trail completeness
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ComplianceStandard(Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    ISO_27001 = "iso_27001"
    NIST = "nist"
    CCPA = "ccpa"
    PCI_DSS = "pci_dss"

class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"

class ComplianceIssueType(Enum):
    DATA_RETENTION = "data_retention"
    PRIVACY_POLICY = "privacy_policy"
    CONSENT_MANAGEMENT = "consent_management"
    AUDIT_TRAIL = "audit_trail"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION_STANDARDS = "encryption_standards"
    DOCUMENTATION = "documentation"
    TRAINING_COMPLIANCE = "training_compliance"

@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement"""
    standard: ComplianceStandard
    requirement_id: str
    description: str
    mandatory: bool
    evidence_required: List[str]
    control_measures: List[str]

@dataclass
class ComplianceIssue:
    """Represents a compliance issue"""
    id: str
    standard: ComplianceStandard
    issue_type: ComplianceIssueType
    level: ComplianceLevel
    description: str
    component: str
    evidence_missing: List[str]
    timestamp: datetime
    remediation: str

class ComplianceEvaluator:
    """Evaluates compliance aspects of AI agent operations"""

    def __init__(self):
        self.issues: List[ComplianceIssue] = []
        self.requirements = self._load_compliance_requirements()
        self.audit_requirements = self._load_audit_requirements()

    def _load_compliance_requirements(self) -> Dict[ComplianceStandard, List[ComplianceRequirement]]:
        """Load compliance requirements by standard"""
        return {
            ComplianceStandard.GDPR: [
                ComplianceRequirement(
                    standard=ComplianceStandard.GDPR,
                    requirement_id="GDPR_ART_5",
                    description="Data minimization and purpose limitation",
                    mandatory=True,
                    evidence_required=["data_purpose", "minimal_data", "consent_record"],
                    control_measures=["data_classification", "purpose_tracking", "consent_management"]
                ),
                ComplianceRequirement(
                    standard=ComplianceStandard.GDPR,
                    requirement_id="GDPR_ART_32",
                    description="Security of processing",
                    mandatory=True,
                    evidence_required=["encryption_evidence", "access_logs", "security_measures"],
                    control_measures=["encryption", "access_control", "security_monitoring"]
                ),
            ],
            ComplianceStandard.HIPAA: [
                ComplianceRequirement(
                    standard=ComplianceStandard.HIPAA,
                    requirement_id="HIPAA_164.312",
                    description="Technical safeguards",
                    mandatory=True,
                    evidence_required=["access_control", "audit_controls", "integrity_controls"],
                    control_measures=["access_management", "audit_logging", "data_integrity"]
                ),
            ],
            ComplianceStandard.NIST: [
                ComplianceRequirement(
                    standard=ComplianceStandard.NIST,
                    requirement_id="NIST_AC_1",
                    description="Access control policy and procedures",
                    mandatory=True,
                    evidence_required=["access_policy", "review_procedures", "access_logs"],
                    control_measures=["policy_documentation", "regular_reviews", "access_monitoring"]
                ),
            ],
        }

    def _load_audit_requirements(self) -> Dict[str, Any]:
        """Load audit trail requirements"""
        return {
            "required_fields": [
                "timestamp", "user_id", "action", "resource", "outcome", "ip_address"
            ],
            "retention_period_days": 365,
            "immutable": True,
            "tamper_evident": True,
            "searchable": True,
            "exportable": True
        }

    def evaluate(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main evaluation method for framework compatibility
        
        Args:
            trace: Single trace data to evaluate
            
        Returns:
            Dict containing evaluation results with score and status
        """
        try:
            # Reset issues for this evaluation
            self.issues = []
            
            # Run compliance checks
            self._check_gdpr_compliance(trace)
            self._check_hipaa_compliance(trace)
            self._check_nist_compliance(trace)
            self._check_audit_trail_compliance(trace)
            self._check_data_retention_compliance(trace)
            self._check_access_control_compliance(trace)
            
            # Calculate compliance score
            score = self._calculate_compliance_score()
            
            # Determine pass/fail status
            non_compliant_count = sum(1 for issue in self.issues if issue.level == ComplianceLevel.NON_COMPLIANT)
            
            passed = score >= 0.7 and non_compliant_count == 0
            
            return {
                "score": score,
                "passed": passed,
                "details": {
                    "compliance_issues": len(self.issues),
                    "non_compliant": non_compliant_count,
                    "partially_compliant": sum(1 for issue in self.issues if issue.level == ComplianceLevel.PARTIALLY_COMPLIANT),
                    "compliant_standards": self._get_compliant_standards(),
                    "audit_trail_score": self._calculate_audit_trail_score(trace),
                    "recommendations": self._generate_compliance_recommendations()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in compliance evaluation: {e}")
            return {
                "score": 0.0,
                "passed": False,
                "details": {
                    "error": str(e),
                    "evaluation_failed": True
                }
            }

    def evaluate_batch(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch evaluation method for multiple traces
        
        Args:
            traces: List of trace data to evaluate
            
        Returns:
            Dict containing batch evaluation results
        """
        try:
            results = []
            total_score = 0.0
            passed_count = 0
            all_issues = []
            
            for trace in traces:
                result = self.evaluate(trace)
                results.append(result)
                total_score += result["score"]
                if result["passed"]:
                    passed_count += 1
                
                # Collect all issues
                all_issues.extend(self.issues)
            
            # Analyze compliance trends
            compliance_trends = self._analyze_compliance_trends(all_issues)
            
            return {
                "total_traces": len(traces),
                "average_score": total_score / len(traces) if traces else 0.0,
                "pass_rate": passed_count / len(traces) if traces else 0.0,
                "passed_count": passed_count,
                "failed_count": len(traces) - passed_count,
                "individual_results": results,
                "aggregate_metrics": {
                    "total_compliance_issues": len(all_issues),
                    "non_compliant_issues": sum(1 for issue in all_issues if issue.level == ComplianceLevel.NON_COMPLIANT),
                    "partially_compliant_issues": sum(1 for issue in all_issues if issue.level == ComplianceLevel.PARTIALLY_COMPLIANT),
                    "compliance_trends": compliance_trends,
                    "standards_coverage": self._calculate_standards_coverage(all_issues),
                    "audit_trail_completeness": self._calculate_audit_completeness(traces),
                    "compliance_recommendations": self._generate_batch_compliance_recommendations(all_issues)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in batch compliance evaluation: {e}")
            return {
                "total_traces": len(traces),
                "average_score": 0.0,
                "pass_rate": 0.0,
                "error": str(e)
            }

    def _check_gdpr_compliance(self, trace: Dict[str, Any]):
        """Check GDPR compliance"""
        gdpr_requirements = self.requirements.get(ComplianceStandard.GDPR, [])
        
        for req in gdpr_requirements:
            missing_evidence = []
            
            # Check for required evidence
            for evidence in req.evidence_required:
                if evidence not in json.dumps(trace, default=str).lower():
                    missing_evidence.append(evidence)
            
            if missing_evidence:
                level = ComplianceLevel.NON_COMPLIANT if req.mandatory else ComplianceLevel.PARTIALLY_COMPLIANT
                
                issue = ComplianceIssue(
                    id=f"gdpr_{len(self.issues) + 1}",
                    standard=ComplianceStandard.GDPR,
                    issue_type=ComplianceIssueType.PRIVACY_POLICY,
                    level=level,
                    description=f"GDPR requirement {req.requirement_id} not fully met",
                    component="privacy_compliance",
                    evidence_missing=missing_evidence,
                    timestamp=datetime.utcnow(),
                    remediation=f"Implement {', '.join(req.control_measures)} for {req.requirement_id}"
                )
                self.issues.append(issue)

    def _check_hipaa_compliance(self, trace: Dict[str, Any]):
        """Check HIPAA compliance"""
        hipaa_requirements = self.requirements.get(ComplianceStandard.HIPAA, [])
        
        for req in hipaa_requirements:
            missing_evidence = []
            
            # Check for PHI (Protected Health Information) indicators
            text_data = json.dumps(trace, default=str).lower()
            has_phi = any(keyword in text_data for keyword in ["patient", "medical", "health", "diagnosis", "treatment"])
            
            if has_phi:
                for evidence in req.evidence_required:
                    if evidence not in text_data:
                        missing_evidence.append(evidence)
                
                if missing_evidence:
                    issue = ComplianceIssue(
                        id=f"hipaa_{len(self.issues) + 1}",
                        standard=ComplianceStandard.HIPAA,
                        issue_type=ComplianceIssueType.AUDIT_TRAIL,
                        level=ComplianceLevel.NON_COMPLIANT,
                        description=f"HIPAA requirement {req.requirement_id} not met",
                        component="healthcare_compliance",
                        evidence_missing=missing_evidence,
                        timestamp=datetime.utcnow(),
                        remediation=f"Implement {', '.join(req.control_measures)} for HIPAA compliance"
                    )
                    self.issues.append(issue)

    def _check_nist_compliance(self, trace: Dict[str, Any]):
        """Check NIST compliance"""
        nist_requirements = self.requirements.get(ComplianceStandard.NIST, [])
        
        for req in nist_requirements:
            missing_evidence = []
            
            # Check for NIST control evidence
            text_data = json.dumps(trace, default=str).lower()
            
            for evidence in req.evidence_required:
                if evidence not in text_data:
                    missing_evidence.append(evidence)
            
            if len(missing_evidence) > 1:  # Allow some flexibility
                issue = ComplianceIssue(
                    id=f"nist_{len(self.issues) + 1}",
                    standard=ComplianceStandard.NIST,
                    issue_type=ComplianceIssueType.ACCESS_CONTROL,
                    level=ComplianceLevel.PARTIALLY_COMPLIANT,
                    description=f"NIST requirement {req.requirement_id} partially met",
                    component="security_compliance",
                    evidence_missing=missing_evidence,
                    timestamp=datetime.utcnow(),
                    remediation=f"Enhance {', '.join(req.control_measures)} for NIST compliance"
                )
                self.issues.append(issue)

    def _check_audit_trail_compliance(self, trace: Dict[str, Any]):
        """Check audit trail compliance"""
        required_fields = self.audit_requirements["required_fields"]
        trace_data = json.dumps(trace, default=str).lower()
        
        missing_fields = []
        for field in required_fields:
            if field not in trace_data:
                missing_fields.append(field)
        
        if missing_fields:
            issue = ComplianceIssue(
                id=f"audit_{len(self.issues) + 1}",
                standard=ComplianceStandard.NIST,  # Default to NIST for audit requirements
                issue_type=ComplianceIssueType.AUDIT_TRAIL,
                level=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="Audit trail completeness issues",
                component="audit_logging",
                evidence_missing=missing_fields,
                timestamp=datetime.utcnow(),
                remediation=f"Add missing audit fields: {', '.join(missing_fields)}"
            )
            self.issues.append(issue)

    def _check_data_retention_compliance(self, trace: Dict[str, Any]):
        """Check data retention compliance"""
        # Check for data retention metadata
        trace_data = json.dumps(trace, default=str).lower()
        
        retention_indicators = ["retention", "expiry", "deletion", "cleanup", "archival"]
        has_retention_policy = any(indicator in trace_data for indicator in retention_indicators)
        
        if not has_retention_policy:
            issue = ComplianceIssue(
                id=f"retention_{len(self.issues) + 1}",
                standard=ComplianceStandard.GDPR,
                issue_type=ComplianceIssueType.DATA_RETENTION,
                level=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="Data retention policy not evident",
                component="data_governance",
                evidence_missing=["retention_policy", "deletion_schedule"],
                timestamp=datetime.utcnow(),
                remediation="Implement and document data retention policies"
            )
            self.issues.append(issue)

    def _check_access_control_compliance(self, trace: Dict[str, Any]):
        """Check access control compliance"""
        # Check for access control evidence
        attributes = trace.get("attributes", {})
        events = trace.get("events", [])
        
        access_indicators = ["access", "permission", "role", "authorization"]
        has_access_control = any(
            indicator in json.dumps(trace, default=str).lower() 
            for indicator in access_indicators
        )
        
        if not has_access_control:
            issue = ComplianceIssue(
                id=f"access_{len(self.issues) + 1}",
                standard=ComplianceStandard.NIST,
                issue_type=ComplianceIssueType.ACCESS_CONTROL,
                level=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="Access control evidence missing",
                component="access_management",
                evidence_missing=["access_logs", "permission_checks", "role_assignments"],
                timestamp=datetime.utcnow(),
                remediation="Implement comprehensive access control logging"
            )
            self.issues.append(issue)

    def _calculate_compliance_score(self) -> float:
        """Calculate overall compliance score"""
        if not self.issues:
            return 1.0
        
        base_score = 1.0
        
        # Deduct points based on compliance level
        for issue in self.issues:
            if issue.level == ComplianceLevel.NON_COMPLIANT:
                base_score -= 0.3
            elif issue.level == ComplianceLevel.PARTIALLY_COMPLIANT:
                base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))

    def _get_compliant_standards(self) -> List[str]:
        """Get list of standards that are compliant"""
        standards_with_issues = set(issue.standard.value for issue in self.issues)
        all_standards = set(standard.value for standard in ComplianceStandard)
        return list(all_standards - standards_with_issues)

    def _calculate_audit_trail_score(self, trace: Dict[str, Any]) -> float:
        """Calculate audit trail completeness score"""
        required_fields = self.audit_requirements["required_fields"]
        trace_data = json.dumps(trace, default=str).lower()
        
        present_fields = sum(1 for field in required_fields if field in trace_data)
        return present_fields / len(required_fields)

    def _generate_compliance_recommendations(self) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        standards_with_issues = set(issue.standard for issue in self.issues)
        
        for standard in standards_with_issues:
            if standard == ComplianceStandard.GDPR:
                recommendations.append("Review GDPR compliance measures, especially data minimization and consent management")
            elif standard == ComplianceStandard.HIPAA:
                recommendations.append("Enhance HIPAA safeguards for protected health information")
            elif standard == ComplianceStandard.NIST:
                recommendations.append("Strengthen NIST security controls and access management")
        
        issue_types = set(issue.issue_type for issue in self.issues)
        
        if ComplianceIssueType.AUDIT_TRAIL in issue_types:
            recommendations.append("Improve audit trail completeness and integrity")
        
        if ComplianceIssueType.ACCESS_CONTROL in issue_types:
            recommendations.append("Enhance access control mechanisms and logging")
        
        if not recommendations:
            recommendations.append("Compliance posture is good - continue monitoring")
        
        return recommendations

    def _analyze_compliance_trends(self, issues: List[ComplianceIssue]) -> Dict[str, Any]:
        """Analyze compliance trends"""
        if not issues:
            return {"trend": "compliant", "insights": ["No compliance issues detected"]}
        
        # Group issues by standard
        standard_counts = {}
        for issue in issues:
            standard = issue.standard.value
            if standard not in standard_counts:
                standard_counts[standard] = 0
            standard_counts[standard] += 1
        
        # Determine trend
        non_compliant = sum(1 for issue in issues if issue.level == ComplianceLevel.NON_COMPLIANT)
        
        if non_compliant > 0:
            trend = "non_compliant"
        elif len(issues) > 10:
            trend = "partially_compliant"
        else:
            trend = "mostly_compliant"
        
        return {
            "trend": trend,
            "standard_distribution": standard_counts,
            "total_issues": len(issues),
            "non_compliant_issues": non_compliant,
            "insights": [
                f"Most affected standard: {max(standard_counts, key=standard_counts.get) if standard_counts else 'None'}",
                f"Non-compliant issues requiring attention: {non_compliant}"
            ]
        }

    def _calculate_standards_coverage(self, issues: List[ComplianceIssue]) -> Dict[str, float]:
        """Calculate compliance coverage by standard"""
        coverage = {}
        
        for standard in ComplianceStandard:
            standard_issues = [issue for issue in issues if issue.standard == standard]
            total_requirements = len(self.requirements.get(standard, []))
            
            if total_requirements == 0:
                coverage[standard.value] = 1.0  # Not applicable
            else:
                compliant_count = total_requirements - len(standard_issues)
                coverage[standard.value] = compliant_count / total_requirements
        
        return coverage

    def _calculate_audit_completeness(self, traces: List[Dict[str, Any]]) -> float:
        """Calculate overall audit trail completeness"""
        if not traces:
            return 0.0
        
        total_score = 0.0
        for trace in traces:
            total_score += self._calculate_audit_trail_score(trace)
        
        return total_score / len(traces)

    def _generate_batch_compliance_recommendations(self, issues: List[ComplianceIssue]) -> List[str]:
        """Generate recommendations for batch evaluation"""
        if not issues:
            return ["Excellent compliance posture - maintain current standards"]
        
        recommendations = set()
        
        # Analyze issue patterns
        standards_with_issues = set(issue.standard for issue in issues)
        non_compliant_standards = set(
            issue.standard for issue in issues 
            if issue.level == ComplianceLevel.NON_COMPLIANT
        )
        
        if non_compliant_standards:
            recommendations.add("URGENT: Address all non-compliant issues immediately")
        
        if ComplianceStandard.GDPR in standards_with_issues:
            recommendations.add("Focus on GDPR compliance measures, especially data protection")
        
        if ComplianceStandard.HIPAA in standards_with_issues:
            recommendations.add("Strengthen healthcare data protection and HIPAA safeguards")
        
        if len(issues) > 15:
            recommendations.add("Consider a comprehensive compliance audit")
        
        return list(recommendations)

    def generate_compliance_report(self, batch_results: Dict[str, Any]) -> str:
        """Generate comprehensive compliance report"""
        report = []
        report.append("=" * 60)
        report.append("COMPLIANCE EVALUATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append(f"Total Traces: {batch_results['total_traces']}")
        report.append(f"Average Score: {batch_results['average_score']:.3f}")
        report.append(f"Pass Rate: {batch_results['pass_rate']:.1%}")
        report.append("")
        
        # Compliance metrics
        metrics = batch_results['aggregate_metrics']
        report.append("COMPLIANCE METRICS:")
        report.append(f"  Total Issues: {metrics['total_compliance_issues']}")
        report.append(f"  Non-Compliant: {metrics['non_compliant_issues']}")
        report.append(f"  Partially Compliant: {metrics['partially_compliant_issues']}")
        report.append(f"  Audit Trail Completeness: {metrics['audit_trail_completeness']:.1%}")
        report.append("")
        
        # Standards coverage
        coverage = metrics['standards_coverage']
        report.append("STANDARDS COVERAGE:")
        for standard, score in coverage.items():
            report.append(f"  {standard.upper()}: {score:.1%}")
        report.append("")
        
        # Trends
        trends = metrics['compliance_trends']
        report.append("COMPLIANCE TRENDS:")
        report.append(f"  Trend: {trends['trend']}")
        report.append(f"  Insights: {', '.join(trends['insights'])}")
        report.append("")
        
        # Recommendations
        report.append("COMPLIANCE RECOMMENDATIONS:")
        for i, rec in enumerate(metrics['compliance_recommendations'], 1):
            report.append(f"  {i}. {rec}")
        report.append("")
        
        return "\n".join(report)
