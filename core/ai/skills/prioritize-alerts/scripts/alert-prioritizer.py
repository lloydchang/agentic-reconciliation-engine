#!/usr/bin/env python3
"""
Alert Prioritizer Script

Multi-cloud automation for alert prioritization and management across AWS, Azure, GCP, and on-premise environments.
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

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertStatus(Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class AlertCategory(Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    COST = "cost"

@dataclass
class Alert:
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    category: AlertCategory
    provider: str
    resource_id: str
    resource_name: str
    region: str
    environment: str
    created_at: datetime
    updated_at: datetime
    status: AlertStatus
    source: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    metrics: Dict[str, Any]
    impact_score: float
    urgency_score: float

@dataclass
class PrioritizationRule:
    rule_id: str
    rule_name: str
    description: str
    conditions: Dict[str, Any]
    priority_score: float
    severity_override: Optional[AlertSeverity]
    category_override: Optional[AlertCategory]
    auto_suppress: bool
    auto_escalate: bool
    enabled: bool

@dataclass
class AlertPrioritizationResult:
    alert_id: str
    original_severity: AlertSeverity
    prioritized_severity: AlertSeverity
    priority_score: float
    impact_score: float
    urgency_score: float
    applied_rules: List[str]
    recommended_actions: List[str]
    escalation_required: bool
    suppression_reason: Optional[str]

class AlertPrioritizer:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.rules = {}
        self.alerts = {}
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load alert prioritizer configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'prioritization_settings': {
                'enable_ml_scoring': True,
                'impact_weight': 0.6,
                'urgency_weight': 0.4,
                'auto_suppression_enabled': True,
                'escalation_threshold': 0.8,
                'batch_processing_size': 100
            },
            'scoring_weights': {
                'severity_weights': {
                    'critical': 1.0,
                    'high': 0.8,
                    'medium': 0.6,
                    'low': 0.4,
                    'info': 0.2
                },
                'category_weights': {
                    'infrastructure': 0.8,
                    'security': 0.9,
                    'availability': 0.9,
                    'performance': 0.7,
                    'application': 0.6,
                    'cost': 0.5
                },
                'environment_weights': {
                    'production': 1.0,
                    'staging': 0.7,
                    'development': 0.4,
                    'testing': 0.5
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
    
    def load_prioritization_rules(self, rules_file: Optional[str] = None) -> Dict[str, PrioritizationRule]:
        """Load alert prioritization rules"""
        logger.info("Loading alert prioritization rules")
        
        # Default rules
        default_rules = {
            'production-critical': PrioritizationRule(
                rule_id='production-critical',
                rule_name='Production Critical Alerts',
                description='Elevate priority for critical alerts in production',
                conditions={
                    'environment': 'production',
                    'severity': ['critical', 'high'],
                    'categories': ['infrastructure', 'security', 'availability']
                },
                priority_score=0.9,
                severity_override=None,
                category_override=None,
                auto_suppress=False,
                auto_escalate=True,
                enabled=True
            ),
            'security-high': PrioritizationRule(
                rule_id='security-high',
                rule_name='Security High Priority',
                description='Elevate all security alerts',
                conditions={
                    'category': 'security',
                    'severity': ['medium', 'high', 'critical']
                },
                priority_score=0.85,
                severity_override=None,
                category_override=None,
                auto_suppress=False,
                auto_escalate=True,
                enabled=True
            ),
            'cost-optimization': PrioritizationRule(
                rule_id='cost-optimization',
                rule_name='Cost Alert Prioritization',
                description='Prioritize cost alerts with high impact',
                conditions={
                    'category': 'cost',
                    'impact_threshold': 1000.0
                },
                priority_score=0.7,
                severity_override=None,
                category_override=None,
                auto_suppress=False,
                auto_escalate=False,
                enabled=True
            ),
            'duplicate-suppression': PrioritizationRule(
                rule_id='duplicate-suppression',
                rule_name='Duplicate Alert Suppression',
                description='Suppress duplicate alerts from same resource',
                conditions={
                    'time_window_minutes': 15,
                    'same_resource': True,
                    'same_category': True
                },
                priority_score=0.0,
                severity_override=AlertSeverity.LOW,
                category_override=None,
                auto_suppress=True,
                auto_escalate=False,
                enabled=True
            ),
            'maintenance-suppression': PrioritizationRule(
                rule_id='maintenance-suppression',
                rule_name='Maintenance Window Suppression',
                description='Suppress alerts during maintenance windows',
                conditions={
                    'maintenance_window': True,
                    'non_critical_severity': True
                },
                priority_score=0.0,
                severity_override=AlertSeverity.INFO,
                category_override=None,
                auto_suppress=True,
                auto_escalate=False,
                enabled=True
            )
        }
        
        # Load custom rules from file if provided
        if rules_file:
            try:
                with open(rules_file, 'r') as f:
                    custom_rules = json.load(f)
                
                for rule_id, rule_data in custom_rules.items():
                    rule = PrioritizationRule(
                        rule_id=rule_id,
                        rule_name=rule_data['rule_name'],
                        description=rule_data['description'],
                        conditions=rule_data['conditions'],
                        priority_score=rule_data['priority_score'],
                        severity_override=AlertSeverity(rule_data['severity_override']) if rule_data.get('severity_override') else None,
                        category_override=AlertCategory(rule_data['category_override']) if rule_data.get('category_override') else None,
                        auto_suppress=rule_data.get('auto_suppress', False),
                        auto_escalate=rule_data.get('auto_escalate', False),
                        enabled=rule_data.get('enabled', True)
                    )
                    default_rules[rule_id] = rule
                    
            except Exception as e:
                logger.warning(f"Failed to load custom rules: {e}")
        
        self.rules = default_rules
        logger.info(f"Loaded {len(self.rules)} prioritization rules")
        
        return self.rules
    
    def collect_alerts(self, providers: List[str], time_range_hours: int = 24) -> Dict[str, List[Alert]]:
        """Collect alerts from multiple providers"""
        logger.info(f"Collecting alerts from providers: {providers}")
        
        all_alerts = {}
        
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
                
                # Collect alerts
                provider_alerts = handler.get_alerts(time_range_hours)
                all_alerts[provider] = provider_alerts
                
                logger.info(f"Collected {len(provider_alerts)} alerts from {provider}")
                
            except Exception as e:
                logger.error(f"Failed to collect alerts from {provider}: {e}")
                all_alerts[provider] = []
        
        return all_alerts
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific alert handler"""
        from alert_prioritizer_handler import get_alert_handler
        region = self.config['providers'][provider]['region']
        return get_alert_handler(provider, region)
    
    def prioritize_alerts(self, alerts: List[Alert]) -> List[AlertPrioritizationResult]:
        """Prioritize alerts using rules and ML scoring"""
        logger.info(f"Prioritizing {len(alerts)} alerts")
        
        prioritized_results = []
        
        for alert in alerts:
            try:
                # Calculate initial scores
                impact_score = self._calculate_impact_score(alert)
                urgency_score = self._calculate_urgency_score(alert)
                
                # Apply prioritization rules
                applied_rules, priority_score, severity_override, category_override, suppress, escalate = self._apply_rules(alert)
                
                # Calculate final priority score
                final_priority_score = self._calculate_final_priority_score(
                    priority_score, impact_score, urgency_score
                )
                
                # Determine final severity
                final_severity = severity_override if severity_override else alert.severity
                
                # Generate recommended actions
                recommended_actions = self._generate_recommended_actions(alert, final_severity, escalate)
                
                # Check for suppression
                suppression_reason = None
                if suppress:
                    suppression_reason = self._get_suppression_reason(alert, applied_rules)
                
                # Create prioritization result
                result = AlertPrioritizationResult(
                    alert_id=alert.alert_id,
                    original_severity=alert.severity,
                    prioritized_severity=final_severity,
                    priority_score=final_priority_score,
                    impact_score=impact_score,
                    urgency_score=urgency_score,
                    applied_rules=applied_rules,
                    recommended_actions=recommended_actions,
                    escalation_required=escalate,
                    suppression_reason=suppression_reason
                )
                
                prioritized_results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to prioritize alert {alert.alert_id}: {e}")
                # Create a basic result for failed alerts
                result = AlertPrioritizationResult(
                    alert_id=alert.alert_id,
                    original_severity=alert.severity,
                    prioritized_severity=alert.severity,
                    priority_score=0.5,
                    impact_score=0.5,
                    urgency_score=0.5,
                    applied_rules=[],
                    recommended_actions=['Review alert manually'],
                    escalation_required=False,
                    suppression_reason=None
                )
                prioritized_results.append(result)
        
        # Sort by priority score (descending)
        prioritized_results.sort(key=lambda x: x.priority_score, reverse=True)
        
        return prioritized_results
    
    def _calculate_impact_score(self, alert: Alert) -> float:
        """Calculate impact score based on alert characteristics"""
        weights = self.config['scoring_weights']
        
        # Base impact from severity
        severity_weight = weights['severity_weights'].get(alert.severity.value, 0.5)
        
        # Category impact
        category_weight = weights['category_weights'].get(alert.category.value, 0.5)
        
        # Environment impact
        environment_weight = weights['environment_weights'].get(alert.environment, 0.5)
        
        # Resource criticality (simplified)
        resource_criticality = self._get_resource_criticality(alert.resource_id)
        
        # Business impact (simplified)
        business_impact = self._get_business_impact(alert.labels)
        
        # Calculate weighted impact score
        impact_score = (
            severity_weight * 0.3 +
            category_weight * 0.2 +
            environment_weight * 0.2 +
            resource_criticality * 0.15 +
            business_impact * 0.15
        )
        
        return min(impact_score, 1.0)
    
    def _calculate_urgency_score(self, alert: Alert) -> float:
        """Calculate urgency score based on time and trends"""
        # Time-based urgency
        time_since_creation = datetime.utcnow() - alert.created_at
        hours_old = time_since_creation.total_seconds() / 3600
        
        # Newer alerts are more urgent
        time_urgency = max(0, 1.0 - (hours_old / 24))  # Decay over 24 hours
        
        # Trend-based urgency (simplified)
        trend_urgency = self._get_alert_trend_urgency(alert)
        
        # Volume-based urgency (simplified)
        volume_urgency = self._get_volume_urgency(alert)
        
        # Calculate weighted urgency score
        urgency_score = (
            time_urgency * 0.4 +
            trend_urgency * 0.3 +
            volume_urgency * 0.3
        )
        
        return min(urgency_score, 1.0)
    
    def _apply_rules(self, alert: Alert) -> Tuple[List[str], float, Optional[AlertSeverity], Optional[AlertCategory], bool, bool]:
        """Apply prioritization rules to alert"""
        applied_rules = []
        priority_score = 0.5  # Base score
        severity_override = None
        category_override = None
        suppress = False
        escalate = False
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            if self._rule_matches(alert, rule):
                applied_rules.append(rule_id)
                
                # Apply rule effects
                priority_score = max(priority_score, rule.priority_score)
                
                if rule.severity_override:
                    severity_override = rule.severity_override
                
                if rule.category_override:
                    category_override = rule.category_override
                
                if rule.auto_suppress:
                    suppress = True
                
                if rule.auto_escalate:
                    escalate = True
        
        return applied_rules, priority_score, severity_override, category_override, suppress, escalate
    
    def _rule_matches(self, alert: Alert, rule: PrioritizationRule) -> bool:
        """Check if alert matches rule conditions"""
        conditions = rule.conditions
        
        # Check environment condition
        if 'environment' in conditions:
            if alert.environment != conditions['environment']:
                return False
        
        # Check severity condition
        if 'severity' in conditions:
            if alert.severity.value not in conditions['severity']:
                return False
        
        # Check category condition
        if 'categories' in conditions:
            if alert.category.value not in conditions['categories']:
                return False
        
        # Check category condition (single)
        if 'category' in conditions:
            if alert.category.value != conditions['category']:
                return False
        
        # Check impact threshold
        if 'impact_threshold' in conditions:
            if alert.impact_score < conditions['impact_threshold']:
                return False
        
        # Check maintenance window
        if 'maintenance_window' in conditions:
            if not self._is_in_maintenance_window(alert):
                return False
        
        # Check non-critical severity
        if 'non_critical_severity' in conditions:
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                return False
        
        # Check duplicate condition
        if 'same_resource' in conditions and 'time_window_minutes' in conditions:
            if not self._is_duplicate_alert(alert, conditions['time_window_minutes']):
                return False
        
        return True
    
    def _calculate_final_priority_score(self, rule_priority: float, impact_score: float, urgency_score: float) -> float:
        """Calculate final priority score"""
        settings = self.config['prioritization_settings']
        
        if settings['enable_ml_scoring']:
            # Weighted combination
            final_score = (
                rule_priority * 0.4 +
                impact_score * settings['impact_weight'] +
                urgency_score * settings['urgency_weight']
            )
        else:
            # Simple average
            final_score = (rule_priority + impact_score + urgency_score) / 3
        
        return min(final_score, 1.0)
    
    def _generate_recommended_actions(self, alert: Alert, severity: AlertSeverity, escalate: bool) -> List[str]:
        """Generate recommended actions based on alert and severity"""
        actions = []
        
        # Basic actions based on severity
        if severity == AlertSeverity.CRITICAL:
            actions.extend([
                "Immediate investigation required",
                "Notify on-call engineer",
                "Check system status dashboard",
                "Prepare rollback plan"
            ])
        elif severity == AlertSeverity.HIGH:
            actions.extend([
                "Investigate within 30 minutes",
                "Review recent changes",
                "Check related systems"
            ])
        elif severity == AlertSeverity.MEDIUM:
            actions.extend([
                "Investigate within 2 hours",
                "Review performance metrics",
                "Monitor for escalation"
            ])
        else:
            actions.extend([
                "Review during business hours",
                "Document for trend analysis"
            ])
        
        # Category-specific actions
        if alert.category == AlertCategory.SECURITY:
            actions.extend([
                "Review security logs",
                "Check for unauthorized access",
                "Notify security team"
            ])
        elif alert.category == AlertCategory.AVAILABILITY:
            actions.extend([
                "Check service dependencies",
                "Verify SLA compliance",
                "Notify stakeholders"
            ])
        elif alert.category == AlertCategory.PERFORMANCE:
            actions.extend([
                "Analyze performance metrics",
                "Check resource utilization",
                "Review recent deployments"
            ])
        
        # Escalation actions
        if escalate:
            actions.extend([
                "Escalate to senior team",
                "Notify management",
                "Create incident ticket"
            ])
        
        return actions
    
    def _get_suppression_reason(self, alert: Alert, applied_rules: List[str]) -> Optional[str]:
        """Get suppression reason for alert"""
        if 'duplicate-suppression' in applied_rules:
            return "Duplicate alert suppressed"
        elif 'maintenance-suppression' in applied_rules:
            return "Suppressed during maintenance window"
        return None
    
    def _get_resource_criticality(self, resource_id: str) -> float:
        """Get resource criticality score"""
        # Simplified criticality mapping
        if 'prod' in resource_id.lower() or 'production' in resource_id.lower():
            return 0.9
        elif 'critical' in resource_id.lower():
            return 0.8
        elif 'staging' in resource_id.lower():
            return 0.6
        elif 'dev' in resource_id.lower() or 'test' in resource_id.lower():
            return 0.4
        else:
            return 0.5
    
    def _get_business_impact(self, labels: Dict[str, str]) -> float:
        """Get business impact score from labels"""
        # Check for business impact indicators
        if labels.get('business_critical', '').lower() == 'true':
            return 0.9
        elif labels.get('customer_facing', '').lower() == 'true':
            return 0.8
        elif labels.get('revenue_impact', '').lower() == 'true':
            return 0.85
        else:
            return 0.5
    
    def _get_alert_trend_urgency(self, alert: Alert) -> float:
        """Get urgency based on alert trends"""
        # Simplified trend analysis
        # In real implementation, this would analyze historical alert patterns
        return 0.5
    
    def _get_volume_urgency(self, alert: Alert) -> float:
        """Get urgency based on alert volume"""
        # Simplified volume analysis
        # In real implementation, this would check alert frequency
        return 0.5
    
    def _is_in_maintenance_window(self, alert: Alert) -> bool:
        """Check if alert is within maintenance window"""
        # Simplified maintenance window check
        # In real implementation, this would check maintenance schedules
        return False
    
    def _is_duplicate_alert(self, alert: Alert, time_window_minutes: int) -> bool:
        """Check if alert is a duplicate within time window"""
        # Simplified duplicate check
        # In real implementation, this would check recent similar alerts
        return False
    
    def generate_prioritization_report(self, prioritized_results: List[AlertPrioritizationResult], 
                                       output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive prioritization report"""
        logger.info("Generating prioritization report")
        
        # Calculate statistics
        total_alerts = len(prioritized_results)
        critical_alerts = len([r for r in prioritized_results if r.prioritized_severity == AlertSeverity.CRITICAL])
        high_alerts = len([r for r in prioritized_results if r.prioritized_severity == AlertSeverity.HIGH])
        medium_alerts = len([r for r in prioritized_results if r.prioritized_severity == AlertSeverity.MEDIUM])
        low_alerts = len([r for r in prioritized_results if r.prioritized_severity == AlertSeverity.LOW])
        suppressed_alerts = len([r for r in prioritized_results if r.suppression_reason])
        escalation_required = len([r for r in prioritized_results if r.escalation_required])
        
        # Calculate average scores
        avg_priority_score = sum(r.priority_score for r in prioritized_results) / total_alerts if total_alerts > 0 else 0
        avg_impact_score = sum(r.impact_score for r in prioritized_results) / total_alerts if total_alerts > 0 else 0
        avg_urgency_score = sum(r.urgency_score for r in prioritized_results) / total_alerts if total_alerts > 0 else 0
        
        # Group by severity
        severity_distribution = {
            'critical': critical_alerts,
            'high': high_alerts,
            'medium': medium_alerts,
            'low': low_alerts,
            'suppressed': suppressed_alerts
        }
        
        # Top priority alerts
        top_priority_alerts = prioritized_results[:10]
        
        # Applied rules statistics
        rule_usage = {}
        for result in prioritized_results:
            for rule_id in result.applied_rules:
                rule_usage[rule_id] = rule_usage.get(rule_id, 0) + 1
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'high_alerts': high_alerts,
                'medium_alerts': medium_alerts,
                'low_alerts': low_alerts,
                'suppressed_alerts': suppressed_alerts,
                'escalation_required': escalation_required,
                'suppression_rate': (suppressed_alerts / total_alerts * 100) if total_alerts > 0 else 0,
                'escalation_rate': (escalation_required / total_alerts * 100) if total_alerts > 0 else 0
            },
            'scoring_summary': {
                'average_priority_score': avg_priority_score,
                'average_impact_score': avg_impact_score,
                'average_urgency_score': avg_urgency_score
            },
            'severity_distribution': severity_distribution,
            'rule_usage': rule_usage,
            'top_priority_alerts': [
                {
                    'alert_id': r.alert_id,
                    'original_severity': r.original_severity.value,
                    'prioritized_severity': r.prioritized_severity.value,
                    'priority_score': r.priority_score,
                    'applied_rules': r.applied_rules,
                    'escalation_required': r.escalation_required,
                    'suppression_reason': r.suppression_reason
                }
                for r in top_priority_alerts
            ],
            'recommended_actions_summary': self._generate_actions_summary(prioritized_results)
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Prioritization report saved to: {output_file}")
        
        return report
    
    def _generate_actions_summary(self, prioritized_results: List[AlertPrioritizationResult]) -> Dict[str, Any]:
        """Generate summary of recommended actions"""
        action_counts = {}
        critical_actions = []
        
        for result in prioritized_results:
            if result.prioritized_severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                critical_actions.extend(result.recommended_actions)
            
            for action in result.recommended_actions:
                action_counts[action] = action_counts.get(action, 0) + 1
        
        # Sort actions by frequency
        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'most_common_actions': sorted_actions[:10],
            'critical_actions_count': len(critical_actions),
            'unique_actions': len(action_counts)
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Alert Prioritizer")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--rules", help="Prioritization rules file")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--time-range", type=int, default=24, help="Time range in hours")
    parser.add_argument("--action", choices=['collect', 'prioritize', 'report'], 
                       default='prioritize', help="Action to perform")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize alert prioritizer
    prioritizer = AlertPrioritizer(args.config)
    
    # Load rules
    prioritizer.load_prioritization_rules(args.rules)
    
    try:
        if args.action == 'collect':
            alerts = prioritizer.collect_alerts(args.providers, args.time_range)
            
            print(f"\nAlert Collection Results:")
            total_alerts = sum(len(alerts_list) for alerts_list in alerts.values())
            print(f"Total Alerts: {total_alerts}")
            
            for provider, provider_alerts in alerts.items():
                print(f"{provider}: {len(provider_alerts)} alerts")
        
        elif args.action == 'prioritize':
            # Collect alerts
            all_alerts = prioritizer.collect_alerts(args.providers, args.time_range)
            
            # Flatten alerts from all providers
            flat_alerts = []
            for provider_alerts in all_alerts.values():
                flat_alerts.extend(provider_alerts)
            
            # Prioritize alerts
            prioritized_results = prioritizer.prioritize_alerts(flat_alerts)
            
            print(f"\nPrioritization Results:")
            print(f"Total Alerts Processed: {len(prioritized_results)}")
            
            # Show top alerts
            for i, result in enumerate(prioritized_results[:10]):
                print(f"{i+1}. {result.alert_id}: {result.prioritized_severity.value} (Score: {result.priority_score:.2f})")
                if result.escalation_required:
                    print(f"   ESCALATION REQUIRED")
                if result.suppression_reason:
                    print(f"   SUPPRESSED: {result.suppression_reason}")
        
        elif args.action == 'report':
            # Collect and prioritize alerts
            all_alerts = prioritizer.collect_alerts(args.providers, args.time_range)
            flat_alerts = []
            for provider_alerts in all_alerts.values():
                flat_alerts.extend(provider_alerts)
            
            prioritized_results = prioritizer.prioritize_alerts(flat_alerts)
            
            # Generate report
            report = prioritizer.generate_prioritization_report(prioritized_results, args.output)
            
            summary = report['summary']
            print(f"\nAlert Prioritization Report:")
            print(f"Total Alerts: {summary['total_alerts']}")
            print(f"Critical: {summary['critical_alerts']}")
            print(f"High: {summary['high_alerts']}")
            print(f"Medium: {summary['medium_alerts']}")
            print(f"Low: {summary['low_alerts']}")
            print(f"Suppressed: {summary['suppressed_alerts']}")
            print(f"Escalation Required: {summary['escalation_required']}")
            print(f"Average Priority Score: {report['scoring_summary']['average_priority_score']:.2f}")
            
            if args.output:
                print(f"Report saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Alert prioritization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
