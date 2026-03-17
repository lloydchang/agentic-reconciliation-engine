#!/usr/bin/env python3
"""
Security Evaluator for AI Agent Systems

Evaluates security aspects of agent operations including:
- Data privacy and PII handling
- Authentication and authorization
- Input validation and sanitization
- Security policy compliance
- Vulnerability assessment
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SecurityIssueType(Enum):
    PII_EXPOSURE = "pii_exposure"
    INJECTION_VULNERABILITY = "injection_vulnerability"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_LEAKAGE = "data_leakage"
    POLICY_VIOLATION = "policy_violation"
    WEAK_CRYPTOGRAPHY = "weak_cryptography"

@dataclass
class SecurityIssue:
    """Represents a security issue detected"""
    id: str
    type: SecurityIssueType
    level: SecurityLevel
    description: str
    component: str
    evidence: str
    timestamp: datetime
    remediation: str

class SecurityEvaluator:
    """Evaluates security aspects of AI agent operations"""

    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.security_policies = self._load_security_policies()
        self.pii_patterns = self._load_pii_patterns()
        self.injection_patterns = self._load_injection_patterns()

    def _load_security_policies(self) -> Dict[str, Any]:
        """Load security policies and compliance requirements"""
        return {
            "data_encryption": {
                "required": True,
                "algorithms": ["AES-256", "RSA-4096"],
                "min_key_length": 256
            },
            "authentication": {
                "required": True,
                "min_password_length": 12,
                "require_mfa": True
            },
            "authorization": {
                "required": True,
                "principle_of_least_privilege": True
            },
            "audit_logging": {
                "required": True,
                "retention_days": 90,
                "log_sensitive_operations": True
            },
            "input_validation": {
                "required": True,
                "sanitize_user_input": True,
                "validate_file_uploads": True
            }
        }

    def _load_pii_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns for detecting PII and sensitive data"""
        return [
            {"pattern": r'\b\d{3}-\d{2}-\d{4}\b', "type": "SSN", "severity": SecurityLevel.CRITICAL},
            {"pattern": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "type": "Credit Card", "severity": SecurityLevel.CRITICAL},
            {"pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "type": "Email", "severity": SecurityLevel.MEDIUM},
            {"pattern": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "type": "Phone", "severity": SecurityLevel.MEDIUM},
            {"pattern": r'\b(?:\d{1,3}\.){3}\d{1,3}\b', "type": "IP Address", "severity": SecurityLevel.LOW},
            {"pattern": r'\b(?:[A-Z][a-z]+ ){1,2}(?:Avenue|Street|Road|Lane|Drive|Boulevard)\b', "type": "Address", "severity": SecurityLevel.MEDIUM},
        ]

    def _load_injection_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns for detecting injection vulnerabilities"""
        return [
            {"pattern": r'(union|select|insert|update|delete|drop)\s+', "type": "SQL Injection", "severity": SecurityLevel.CRITICAL},
            {"pattern": r'<script[^>]*>.*?</script>', "type": "XSS", "severity": SecurityLevel.HIGH},
            {"pattern": r'\${.*}', "type": "Template Injection", "severity": SecurityLevel.HIGH},
            {"pattern": r'\|\s*(cat|ls|pwd|whoami)', "type": "Command Injection", "severity": SecurityLevel.CRITICAL},
            {"pattern": r'(?<!\\)(?:\\{2}|%2e|%2E)', "type": "Path Traversal", "severity": SecurityLevel.HIGH},
        ]

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
            
            # Run security checks
            self._check_pii_exposure(trace)
            self._check_injection_vulnerabilities(trace)
            self._check_authentication(trace)
            self._check_authorization(trace)
            self._check_data_encryption(trace)
            self._check_audit_logging(trace)
            self._check_input_validation(trace)
            
            # Calculate security score
            score = self._calculate_security_score()
            
            # Determine pass/fail status
            critical_issues = sum(1 for issue in self.issues if issue.level == SecurityLevel.CRITICAL)
            high_issues = sum(1 for issue in self.issues if issue.level == SecurityLevel.HIGH)
            
            passed = score >= 0.7 and critical_issues == 0
            
            return {
                "score": score,
                "passed": passed,
                "details": {
                    "security_issues": len(self.issues),
                    "critical_issues": critical_issues,
                    "high_issues": high_issues,
                    "medium_issues": sum(1 for issue in self.issues if issue.level == SecurityLevel.MEDIUM),
                    "low_issues": sum(1 for issue in self.issues if issue.level == SecurityLevel.LOW),
                    "security_policies_compliant": self._check_policy_compliance(),
                    "recommendations": self._generate_security_recommendations()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in security evaluation: {e}")
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
            
            # Analyze security trends
            security_trends = self._analyze_security_trends(all_issues)
            
            return {
                "total_traces": len(traces),
                "average_score": total_score / len(traces) if traces else 0.0,
                "pass_rate": passed_count / len(traces) if traces else 0.0,
                "passed_count": passed_count,
                "failed_count": len(traces) - passed_count,
                "individual_results": results,
                "aggregate_metrics": {
                    "total_security_issues": len(all_issues),
                    "critical_issues": sum(1 for issue in all_issues if issue.level == SecurityLevel.CRITICAL),
                    "high_issues": sum(1 for issue in all_issues if issue.level == SecurityLevel.HIGH),
                    "medium_issues": sum(1 for issue in all_issues if issue.level == SecurityLevel.MEDIUM),
                    "low_issues": sum(1 for issue in all_issues if issue.level == SecurityLevel.LOW),
                    "security_trends": security_trends,
                    "compliance_score": self._calculate_compliance_score(all_issues),
                    "security_recommendations": self._generate_batch_recommendations(all_issues)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in batch security evaluation: {e}")
            return {
                "total_traces": len(traces),
                "average_score": 0.0,
                "pass_rate": 0.0,
                "error": str(e)
            }

    def _check_pii_exposure(self, trace: Dict[str, Any]):
        """Check for PII exposure in trace data"""
        text_data = json.dumps(trace, default=str)
        
        for pattern_info in self.pii_patterns:
            pattern = pattern_info["pattern"]
            pii_type = pattern_info["type"]
            severity = pattern_info["severity"]
            
            matches = re.findall(pattern, text_data, re.IGNORECASE)
            if matches:
                issue = SecurityIssue(
                    id=f"pii_{len(self.issues) + 1}",
                    type=SecurityIssueType.PII_EXPOSURE,
                    level=severity,
                    description=f"PII data detected: {pii_type}",
                    component="trace_data",
                    evidence=f"Found {len(matches)} instances of {pii_type}",
                    timestamp=datetime.utcnow(),
                    remediation=f"Remove or encrypt {pii_type} data from traces"
                )
                self.issues.append(issue)

    def _check_injection_vulnerabilities(self, trace: Dict[str, Any]):
        """Check for injection vulnerabilities"""
        text_data = json.dumps(trace, default=str)
        
        for pattern_info in self.injection_patterns:
            pattern = pattern_info["pattern"]
            vuln_type = pattern_info["type"]
            severity = pattern_info["severity"]
            
            matches = re.findall(pattern, text_data, re.IGNORECASE)
            if matches:
                issue = SecurityIssue(
                    id=f"injection_{len(self.issues) + 1}",
                    type=SecurityIssueType.INJECTION_VULNERABILITY,
                    level=severity,
                    description=f"Potential {vuln_type} vulnerability",
                    component="trace_data",
                    evidence=f"Found {len(matches)} suspicious patterns",
                    timestamp=datetime.utcnow(),
                    remediation=f"Implement input validation and sanitization for {vuln_type}"
                )
                self.issues.append(issue)

    def _check_authentication(self, trace: Dict[str, Any]):
        """Check authentication mechanisms"""
        events = trace.get("events", [])
        
        # Look for authentication events
        auth_events = [event for event in events if "auth" in event.get("name", "").lower()]
        
        if not auth_events:
            issue = SecurityIssue(
                id=f"auth_{len(self.issues) + 1}",
                type=SecurityIssueType.AUTHENTICATION_BYPASS,
                level=SecurityLevel.HIGH,
                description="No authentication events detected",
                component="authentication",
                evidence="Trace lacks authentication events",
                timestamp=datetime.utcnow(),
                remediation="Implement proper authentication for all agent operations"
            )
            self.issues.append(issue)

    def _check_authorization(self, trace: Dict[str, Any]):
        """Check authorization controls"""
        attributes = trace.get("attributes", {})
        
        # Check for authorization context
        if not any(key in attributes for key in ["user_id", "role", "permissions", "auth_context"]):
            issue = SecurityIssue(
                id=f"authz_{len(self.issues) + 1}",
                type=SecurityIssueType.PRIVILEGE_ESCALATION,
                level=SecurityLevel.MEDIUM,
                description="Missing authorization context",
                component="authorization",
                evidence="No user/role information in trace",
                timestamp=datetime.utcnow(),
                remediation="Add authorization context to all agent operations"
            )
            self.issues.append(issue)

    def _check_data_encryption(self, trace: Dict[str, Any]):
        """Check data encryption compliance"""
        # This is a simplified check - in practice, you'd check actual encryption metadata
        sensitive_data_found = False
        
        # Look for sensitive fields
        sensitive_fields = ["password", "token", "key", "secret", "credential"]
        text_data = json.dumps(trace, default=str).lower()
        
        for field in sensitive_fields:
            if field in text_data:
                sensitive_data_found = True
                break
        
        if sensitive_data_found:
            # Check if encryption is indicated
            if "encrypted" not in text_data and "cipher" not in text_data:
                issue = SecurityIssue(
                    id=f"crypto_{len(self.issues) + 1}",
                    type=SecurityIssueType.WEAK_CRYPTOGRAPHY,
                    level=SecurityLevel.HIGH,
                    description="Sensitive data without encryption indication",
                    component="data_protection",
                    evidence="Sensitive fields found without encryption metadata",
                    timestamp=datetime.utcnow(),
                    remediation="Implement encryption for all sensitive data"
                )
                self.issues.append(issue)

    def _check_audit_logging(self, trace: Dict[str, Any]):
        """Check audit logging compliance"""
        # Check if trace has proper audit metadata
        if not trace.get("timestamp"):
            issue = SecurityIssue(
                id=f"audit_{len(self.issues) + 1}",
                type=SecurityIssueType.POLICY_VIOLATION,
                level=SecurityLevel.MEDIUM,
                description="Missing audit timestamp",
                component="audit_logging",
                evidence="Trace lacks timestamp for audit trail",
                timestamp=datetime.utcnow(),
                remediation="Add timestamps to all traces for audit compliance"
            )
            self.issues.append(issue)

    def _check_input_validation(self, trace: Dict[str, Any]):
        """Check input validation evidence"""
        # Look for validation events
        events = trace.get("events", [])
        validation_events = [event for event in events if "valid" in event.get("name", "").lower()]
        
        # Check for user input indicators
        has_user_input = any(key in json.dumps(trace, default=str).lower() for key in ["input", "query", "prompt", "user_data"])
        
        if has_user_input and not validation_events:
            issue = SecurityIssue(
                id=f"validation_{len(self.issues) + 1}",
                type=SecurityIssueType.POLICY_VIOLATION,
                level=SecurityLevel.MEDIUM,
                description="User input without validation evidence",
                component="input_validation",
                evidence="User input detected but no validation events",
                timestamp=datetime.utcnow(),
                remediation="Implement input validation for all user-provided data"
            )
            self.issues.append(issue)

    def _calculate_security_score(self) -> float:
        """Calculate overall security score based on detected issues"""
        base_score = 1.0
        
        # Deduct points based on issue severity
        for issue in self.issues:
            if issue.level == SecurityLevel.CRITICAL:
                base_score -= 0.3
            elif issue.level == SecurityLevel.HIGH:
                base_score -= 0.2
            elif issue.level == SecurityLevel.MEDIUM:
                base_score -= 0.1
            elif issue.level == SecurityLevel.LOW:
                base_score -= 0.05
        
        return max(0.0, min(1.0, base_score))

    def _check_policy_compliance(self) -> bool:
        """Check if security policies are compliant"""
        # Simplified compliance check
        critical_issues = sum(1 for issue in self.issues if issue.level == SecurityLevel.CRITICAL)
        return critical_issues == 0

    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on detected issues"""
        recommendations = []
        
        issue_types = set(issue.type for issue in self.issues)
        
        if SecurityIssueType.PII_EXPOSURE in issue_types:
            recommendations.append("Implement PII detection and redaction in trace data")
        
        if SecurityIssueType.INJECTION_VULNERABILITY in issue_types:
            recommendations.append("Add input validation and sanitization for all user inputs")
        
        if SecurityIssueType.AUTHENTICATION_BYPASS in issue_types:
            recommendations.append("Implement proper authentication for all agent operations")
        
        if SecurityIssueType.PRIVILEGE_ESCALATION in issue_types:
            recommendations.append("Add authorization context and enforce principle of least privilege")
        
        if SecurityIssueType.WEAK_CRYPTOGRAPHY in issue_types:
            recommendations.append("Implement encryption for all sensitive data")
        
        if not recommendations:
            recommendations.append("No critical security issues detected - continue monitoring")
        
        return recommendations

    def _analyze_security_trends(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """Analyze security trends across all issues"""
        if not issues:
            return {"trend": "stable", "insights": ["No security issues detected"]}
        
        # Group issues by type
        issue_counts = {}
        for issue in issues:
            issue_type = issue.type.value
            if issue_type not in issue_counts:
                issue_counts[issue_type] = 0
            issue_counts[issue_type] += 1
        
        # Determine trend
        total_issues = len(issues)
        critical_count = sum(1 for issue in issues if issue.level == SecurityLevel.CRITICAL)
        
        if critical_count > 0:
            trend = "critical"
        elif total_issues > 10:
            trend = "degrading"
        elif total_issues > 5:
            trend = "concerning"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "issue_distribution": issue_counts,
            "total_issues": total_issues,
            "critical_issues": critical_count,
            "insights": [
                f"Most common issue type: {max(issue_counts, key=issue_counts.get) if issue_counts else 'None'}",
                f"Critical issues require immediate attention: {critical_count}"
            ]
        }

    def _calculate_compliance_score(self, issues: List[SecurityIssue]) -> float:
        """Calculate compliance score based on security issues"""
        if not issues:
            return 1.0
        
        # Weight issues by severity
        critical_weight = 0.4
        high_weight = 0.3
        medium_weight = 0.2
        low_weight = 0.1
        
        total_weight = 0.0
        penalty_weight = 0.0
        
        for issue in issues:
            if issue.level == SecurityLevel.CRITICAL:
                penalty_weight += critical_weight
            elif issue.level == SecurityLevel.HIGH:
                penalty_weight += high_weight
            elif issue.level == SecurityLevel.MEDIUM:
                penalty_weight += medium_weight
            elif issue.level == SecurityLevel.LOW:
                penalty_weight += low_weight
            total_weight += 1.0
        
        if total_weight == 0:
            return 1.0
        
        compliance_score = 1.0 - (penalty_weight / total_weight)
        return max(0.0, compliance_score)

    def _generate_batch_recommendations(self, issues: List[SecurityIssue]) -> List[str]:
        """Generate recommendations for batch evaluation"""
        if not issues:
            return ["Security posture is excellent - continue monitoring"]
        
        recommendations = set()
        
        # Analyze issue patterns
        critical_types = set(issue.type for issue in issues if issue.level == SecurityLevel.CRITICAL)
        high_types = set(issue.type for issue in issues if issue.level == SecurityLevel.HIGH)
        
        if critical_types:
            recommendations.add("URGENT: Address all critical security issues immediately")
        
        if SecurityIssueType.PII_EXPOSURE in critical_types or SecurityIssueType.PII_EXPOSURE in high_types:
            recommendations.add("Implement comprehensive PII protection and redaction")
        
        if SecurityIssueType.INJECTION_VULNERABILITY in critical_types or SecurityIssueType.INJECTION_VULNERABILITY in high_types:
            recommendations.add("Implement robust input validation and injection prevention")
        
        if len(issues) > 20:
            recommendations.add("Consider implementing a comprehensive security review process")
        
        if len(set(issue.type for issue in issues)) > 5:
            recommendations.add("Focus on security fundamentals before adding new features")
        
        return list(recommendations)

    def generate_security_report(self, batch_results: Dict[str, Any]) -> str:
        """Generate comprehensive security report"""
        report = []
        report.append("=" * 60)
        report.append("SECURITY EVALUATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append(f"Total Traces: {batch_results['total_traces']}")
        report.append(f"Average Score: {batch_results['average_score']:.3f}")
        report.append(f"Pass Rate: {batch_results['pass_rate']:.1%}")
        report.append("")
        
        # Security metrics
        metrics = batch_results['aggregate_metrics']
        report.append("SECURITY METRICS:")
        report.append(f"  Total Issues: {metrics['total_security_issues']}")
        report.append(f"  Critical: {metrics['critical_issues']}")
        report.append(f"  High: {metrics['high_issues']}")
        report.append(f"  Medium: {metrics['medium_issues']}")
        report.append(f"  Low: {metrics['low_issues']}")
        report.append(f"  Compliance Score: {metrics['compliance_score']:.3f}")
        report.append("")
        
        # Trends
        trends = metrics['security_trends']
        report.append("SECURITY TRENDS:")
        report.append(f"  Trend: {trends['trend']}")
        report.append(f"  Insights: {', '.join(trends['insights'])}")
        report.append("")
        
        # Recommendations
        report.append("SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(metrics['security_recommendations'], 1):
            report.append(f"  {i}. {rec}")
        report.append("")
        
        return "\n".join(report)
