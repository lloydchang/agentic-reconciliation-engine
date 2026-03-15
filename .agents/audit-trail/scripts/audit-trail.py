#!/usr/bin/env python3
"""
Audit Trail Script

Multi-cloud automation for audit trail management, log collection, and compliance monitoring across AWS, Azure, GCP, and on-premise environments.
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
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditEventType(Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHANGE = "permission_change"
    RESOURCE_CREATION = "resource_creation"
    RESOURCE_MODIFICATION = "resource_modification"
    RESOURCE_DELETION = "resource_deletion"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_VIOLATION = "compliance_violation"
    DATA_ACCESS = "data_access"
    SYSTEM_EVENT = "system_event"

@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    user_name: str
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    region: str
    environment: str
    action: str
    result: str
    source_ip: str
    user_agent: str
    details: Dict[str, Any]
    severity: str
    compliance_tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class AuditTrailConfig:
    trail_id: str
    name: str
    provider: str
    region: str
    enabled: bool
    log_sources: List[str]
    retention_days: int
    encryption_enabled: bool
    multi_region: bool
    log_format: str
    destination: str
    filters: Dict[str, Any]
    alert_rules: List[Dict[str, Any]]

@dataclass
class AuditQuery:
    query_id: str
    name: str
    description: str
    event_types: List[AuditEventType]
    time_range: Tuple[datetime, datetime]
    filters: Dict[str, Any]
    group_by: List[str]
    aggregations: List[str]
    order_by: List[str]

@dataclass
class AuditReport:
    report_id: str
    name: str
    description: str
    query: AuditQuery
    generated_at: datetime
    total_events: int
    event_summary: Dict[str, int]
    user_activity: Dict[str, int]
    resource_activity: Dict[str, int]
    compliance_summary: Dict[str, Any]
    findings: List[Dict[str, Any]]
    recommendations: List[str]

@dataclass
class AuditAlert:
    alert_id: str
    rule_id: str
    rule_name: str
    severity: str
    triggered_at: datetime
    event_count: int
    events: List[AuditEvent]
    description: str
    action_taken: str
    status: str

class AuditTrailManager:
    """Main audit trail management class"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = self._load_config()
        self.handlers = {}
        self.trails = {}
        self.queries = {}
        self.reports = {}
        self.alerts = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'providers': ['aws', 'azure', 'gcp', 'onprem'],
            'regions': {
                'aws': 'us-west-2',
                'azure': 'eastus',
                'gcp': 'us-central1',
                'onprem': 'datacenter-1'
            },
            'retention_days': 365,
            'encryption_enabled': True,
            'alert_thresholds': {
                'failed_login_attempts': 5,
                'privilege_escalation': 1,
                'data_access_anomaly': 10
            },
            'compliance_frameworks': ['soc2', 'iso27001', 'pci_dss', 'hipaa'],
            'output_directory': './audit_reports',
            'log_level': 'INFO'
        }
        
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        return default_config
    
    def initialize_handlers(self, providers: List[str]) -> bool:
        """Initialize audit handlers for specified providers"""
        try:
            from audit_trail_handler import get_audit_handler
            
            for provider in providers:
                region = self.config['regions'].get(provider, 'us-west-2')
                handler = get_audit_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    logger.info(f"Initialized {provider} audit handler")
                else:
                    logger.error(f"Failed to initialize {provider} audit handler")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            return False
    
    def discover_audit_trails(self, providers: List[str]) -> Dict[str, List[AuditTrailConfig]]:
        """Discover existing audit trails across providers"""
        discovered_trails = {}
        
        for provider in providers:
            try:
                handler = self.handlers.get(provider)
                if not handler:
                    logger.warning(f"No handler available for {provider}")
                    continue
                
                trails = handler.discover_audit_trails()
                discovered_trails[provider] = trails
                
                # Store in trails dict
                for trail in trails:
                    self.trails[trail.trail_id] = trail
                
                logger.info(f"Discovered {len(trails)} audit trails for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to discover audit trails for {provider}: {e}")
                discovered_trails[provider] = []
        
        return discovered_trails
    
    def create_audit_trail(self, provider: str, trail_config: Dict[str, Any]) -> Optional[AuditTrailConfig]:
        """Create a new audit trail"""
        try:
            handler = self.handlers.get(provider)
            if not handler:
                logger.error(f"No handler available for {provider}")
                return None
            
            trail = handler.create_audit_trail(trail_config)
            if trail:
                self.trails[trail.trail_id] = trail
                logger.info(f"Created audit trail {trail.trail_id} for {provider}")
            
            return trail
            
        except Exception as e:
            logger.error(f"Failed to create audit trail for {provider}: {e}")
            return None
    
    def collect_audit_events(
        self,
        providers: List[str],
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[AuditEventType]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[AuditEvent]]:
        """Collect audit events from all providers"""
        collected_events = {}
        
        for provider in providers:
            try:
                handler = self.handlers.get(provider)
                if not handler:
                    logger.warning(f"No handler available for {provider}")
                    continue
                
                events = handler.collect_audit_events(start_time, end_time, event_types, filters)
                collected_events[provider] = events
                
                logger.info(f"Collected {len(events)} audit events from {provider}")
                
            except Exception as e:
                logger.error(f"Failed to collect audit events from {provider}: {e}")
                collected_events[provider] = []
        
        return collected_events
    
    def analyze_audit_events(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Analyze audit events for patterns and anomalies"""
        try:
            analysis = {
                'summary': {
                    'total_events': len(events),
                    'unique_users': len(set(e.user_id for e in events)),
                    'unique_resources': len(set(e.resource_id for e in events)),
                    'event_types': {},
                    'severity_distribution': {},
                    'time_distribution': {},
                    'compliance_events': 0
                },
                'patterns': {
                    'failed_login_attempts': [],
                    'privilege_escalation': [],
                    'unusual_access_patterns': [],
                    'off_hours_activity': [],
                    'geographic_anomalies': []
                },
                'compliance_analysis': {
                    'framework_coverage': {},
                    'violations': [],
                    'gaps': []
                },
                'recommendations': []
            }
            
            # Event type distribution
            for event in events:
                event_type = event.event_type.value
                analysis['summary']['event_types'][event_type] = analysis['summary']['event_types'].get(event_type, 0) + 1
                
                # Severity distribution
                severity = event.severity
                analysis['summary']['severity_distribution'][severity] = analysis['summary']['severity_distribution'].get(severity, 0) + 1
                
                # Time distribution (hourly)
                hour = event.timestamp.hour
                time_key = f"{hour:02d}:00"
                analysis['summary']['time_distribution'][time_key] = analysis['summary']['time_distribution'].get(time_key, 0) + 1
                
                # Compliance events
                if 'compliance' in event.compliance_tags:
                    analysis['summary']['compliance_events'] += 1
            
            # Analyze patterns
            analysis['patterns'] = self._analyze_patterns(events)
            
            # Compliance analysis
            analysis['compliance_analysis'] = self._analyze_compliance(events)
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze audit events: {e}")
            return {}
    
    def _analyze_patterns(self, events: List[AuditEvent]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze patterns in audit events"""
        patterns = {
            'failed_login_attempts': [],
            'privilege_escalation': [],
            'unusual_access_patterns': [],
            'off_hours_activity': [],
            'geographic_anomalies': []
        }
        
        # Group events by user
        user_events = {}
        for event in events:
            if event.user_id not in user_events:
                user_events[event.user_id] = []
            user_events[event.user_id].append(event)
        
        # Analyze failed login attempts
        for user_id, user_event_list in user_events.items():
            failed_logins = [e for e in user_event_list if e.event_type == AuditEventType.USER_LOGIN and e.result == 'failed']
            
            if len(failed_logins) >= self.config['alert_thresholds']['failed_login_attempts']:
                patterns['failed_login_attempts'].append({
                    'user_id': user_id,
                    'failed_attempts': len(failed_logins),
                    'time_range': (min(e.timestamp for e in failed_logins), max(e.timestamp for e in failed_logins)),
                    'source_ips': list(set(e.source_ip for e in failed_logins))
                })
        
        # Analyze privilege escalation
        for event in events:
            if event.event_type == AuditEventType.PERMISSION_CHANGE and 'admin' in event.action.lower():
                patterns['privilege_escalation'].append({
                    'user_id': event.user_id,
                    'timestamp': event.timestamp,
                    'resource_id': event.resource_id,
                    'action': event.action,
                    'details': event.details
                })
        
        # Analyze off-hours activity (22:00-06:00)
        for event in events:
            hour = event.timestamp.hour
            if hour >= 22 or hour <= 6:
                patterns['off_hours_activity'].append({
                    'user_id': event.user_id,
                    'timestamp': event.timestamp,
                    'event_type': event.event_type.value,
                    'resource_id': event.resource_id
                })
        
        return patterns
    
    def _analyze_compliance(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Analyze compliance aspects of audit events"""
        compliance_analysis = {
            'framework_coverage': {},
            'violations': [],
            'gaps': []
        }
        
        # Framework coverage
        for framework in self.config['compliance_frameworks']:
            framework_events = [e for e in events if framework in e.compliance_tags]
            compliance_analysis['framework_coverage'][framework] = {
                'total_events': len(framework_events),
                'event_types': list(set(e.event_type.value for e in framework_events)),
                'users': list(set(e.user_id for e in framework_events))
            }
        
        # Identify potential violations
        for event in events:
            if event.severity in ['high', 'critical']:
                compliance_analysis['violations'].append({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp,
                    'severity': event.severity,
                    'event_type': event.event_type.value,
                    'user_id': event.user_id,
                    'resource_id': event.resource_id,
                    'description': event.details.get('description', ''),
                    'compliance_tags': event.compliance_tags
                })
        
        # Identify gaps
        all_event_types = set(e.event_type.value for e in events)
        required_event_types = ['user_login', 'permission_change', 'resource_creation', 'resource_modification', 'resource_deletion']
        
        missing_event_types = required_event_types - all_event_types
        if missing_event_types:
            compliance_analysis['gaps'].append({
                'type': 'missing_event_types',
                'missing_types': list(missing_event_types),
                'impact': 'Incomplete audit trail for compliance'
            })
        
        return compliance_analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Failed login recommendations
        if analysis['patterns']['failed_login_attempts']:
            recommendations.append("Implement account lockout policy after multiple failed login attempts")
            recommendations.append("Review and investigate users with high failed login counts")
        
        # Privilege escalation recommendations
        if analysis['patterns']['privilege_escalation']:
            recommendations.append("Implement approval workflow for privilege escalation")
            recommendations.append("Monitor and alert on all privilege changes")
        
        # Off-hours activity recommendations
        if analysis['patterns']['off_hours_activity']:
            recommendations.append("Review off-hours activity policies and exceptions")
            recommendations.append("Implement just-in-time access for off-hours operations")
        
        # Compliance recommendations
        if analysis['compliance_analysis']['violations']:
            recommendations.append("Investigate and remediate high-severity compliance violations")
            recommendations.append("Enhance monitoring for compliance-critical events")
        
        if analysis['compliance_analysis']['gaps']:
            recommendations.append("Address audit trail gaps to ensure complete compliance coverage")
        
        # General recommendations
        if analysis['summary']['severity_distribution'].get('critical', 0) > 0:
            recommendations.append("URGENT: Address critical security events immediately")
        
        if analysis['summary']['severity_distribution'].get('high', 0) > 10:
            recommendations.append("Review and reduce high-severity events through improved controls")
        
        if not recommendations:
            recommendations.append("Audit trail appears healthy. Continue monitoring and maintenance.")
        
        return recommendations
    
    def create_audit_query(self, query_config: Dict[str, Any]) -> AuditQuery:
        """Create a new audit query"""
        try:
            query = AuditQuery(
                query_id=f"query-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                name=query_config['name'],
                description=query_config.get('description', ''),
                event_types=[AuditEventType(t) for t in query_config.get('event_types', [])],
                time_range=(
                    datetime.fromisoformat(query_config['start_time']),
                    datetime.fromisoformat(query_config['end_time'])
                ),
                filters=query_config.get('filters', {}),
                group_by=query_config.get('group_by', []),
                aggregations=query_config.get('aggregations', []),
                order_by=query_config.get('order_by', [])
            )
            
            self.queries[query.query_id] = query
            logger.info(f"Created audit query {query.query_id}")
            
            return query
            
        except Exception as e:
            logger.error(f"Failed to create audit query: {e}")
            raise
    
    def execute_audit_query(self, query: AuditQuery, providers: List[str]) -> Dict[str, List[AuditEvent]]:
        """Execute an audit query across providers"""
        try:
            # Collect events matching query criteria
            all_events = []
            
            for provider in providers:
                events = self.collect_audit_events(
                    providers=[provider],
                    start_time=query.time_range[0],
                    end_time=query.time_range[1],
                    event_types=query.event_types,
                    filters=query.filters
                )
                all_events.extend(events.get(provider, []))
            
            # Apply filters and aggregations
            filtered_events = self._apply_query_filters(all_events, query)
            grouped_events = self._apply_grouping(filtered_events, query)
            
            # Group by provider for return
            provider_events = {}
            for event in grouped_events:
                provider = event.provider
                if provider not in provider_events:
                    provider_events[provider] = []
                provider_events[provider].append(event)
            
            return provider_events
            
        except Exception as e:
            logger.error(f"Failed to execute audit query {query.query_id}: {e}")
            return {}
    
    def _apply_query_filters(self, events: List[AuditEvent], query: AuditQuery) -> List[AuditEvent]:
        """Apply filters to audit events"""
        filtered_events = events
        
        # Apply event type filter
        if query.event_types:
            filtered_events = [e for e in filtered_events if e.event_type in query.event_types]
        
        # Apply custom filters
        for filter_key, filter_value in query.filters.items():
            if filter_key == 'user_id':
                if isinstance(filter_value, list):
                    filtered_events = [e for e in filtered_events if e.user_id in filter_value]
                else:
                    filtered_events = [e for e in filtered_events if e.user_id == filter_value]
            elif filter_key == 'resource_type':
                if isinstance(filter_value, list):
                    filtered_events = [e for e in filtered_events if e.resource_type in filter_value]
                else:
                    filtered_events = [e for e in filtered_events if e.resource_type == filter_value]
            elif filter_key == 'severity':
                if isinstance(filter_value, list):
                    filtered_events = [e for e in filtered_events if e.severity in filter_value]
                else:
                    filtered_events = [e for e in filtered_events if e.severity == filter_value]
            elif filter_key == 'result':
                if isinstance(filter_value, list):
                    filtered_events = [e for e in filtered_events if e.result in filter_value]
                else:
                    filtered_events = [e for e in filtered_events if e.result == filter_value]
        
        return filtered_events
    
    def _apply_grouping(self, events: List[AuditEvent], query: AuditQuery) -> List[AuditEvent]:
        """Apply grouping to audit events"""
        # For now, return events as-is
        # In a full implementation, this would group events and apply aggregations
        return events
    
    def generate_audit_report(self, query: AuditQuery, providers: List[str]) -> AuditReport:
        """Generate a comprehensive audit report"""
        try:
            # Execute query
            query_results = self.execute_audit_query(query, providers)
            all_events = []
            for provider_events in query_results.values():
                all_events.extend(provider_events)
            
            # Analyze events
            analysis = self.analyze_audit_events(all_events)
            
            # Create report
            report = AuditReport(
                report_id=f"report-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                name=f"Audit Report - {query.name}",
                description=query.description,
                query=query,
                generated_at=datetime.utcnow(),
                total_events=len(all_events),
                event_summary=analysis['summary']['event_types'],
                user_activity=self._calculate_user_activity(all_events),
                resource_activity=self._calculate_resource_activity(all_events),
                compliance_summary=analysis['compliance_analysis'],
                findings=self._extract_findings(analysis),
                recommendations=analysis['recommendations']
            )
            
            self.reports[report.report_id] = report
            logger.info(f"Generated audit report {report.report_id}")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            raise
    
    def _calculate_user_activity(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Calculate user activity statistics"""
        user_activity = {}
        for event in events:
            user_id = event.user_id
            user_activity[user_id] = user_activity.get(user_id, 0) + 1
        
        return dict(sorted(user_activity.items(), key=lambda x: x[1], reverse=True))
    
    def _calculate_resource_activity(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Calculate resource activity statistics"""
        resource_activity = {}
        for event in events:
            resource_id = event.resource_id
            resource_activity[resource_id] = resource_activity.get(resource_id, 0) + 1
        
        return dict(sorted(resource_activity.items(), key=lambda x: x[1], reverse=True))
    
    def _extract_findings(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key findings from analysis"""
        findings = []
        
        # Failed login findings
        for failed_login in analysis['patterns']['failed_login_attempts']:
            findings.append({
                'type': 'security_risk',
                'severity': 'high',
                'title': 'Multiple Failed Login Attempts',
                'description': f"User {failed_login['user_id']} had {failed_login['failed_attempts']} failed login attempts",
                'details': failed_login
            })
        
        # Privilege escalation findings
        for escalation in analysis['patterns']['privilege_escalation']:
            findings.append({
                'type': 'privilege_escalation',
                'severity': 'critical',
                'title': 'Privilege Escalation Detected',
                'description': f"User {escalation['user_id']} performed privilege escalation on {escalation['resource_id']}",
                'details': escalation
            })
        
        # Compliance violations
        for violation in analysis['compliance_analysis']['violations']:
            findings.append({
                'type': 'compliance_violation',
                'severity': violation['severity'],
                'title': 'Compliance Violation',
                'description': f"Compliance violation in event {violation['event_id']}",
                'details': violation
            })
        
        return findings
    
    def setup_audit_alerts(self, alert_rules: List[Dict[str, Any]]) -> List[str]:
        """Setup audit alerts based on rules"""
        try:
            created_alerts = []
            
            for rule in alert_rules:
                alert_id = f"alert-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                
                # Store alert rule
                self.alerts[alert_id] = {
                    'alert_id': alert_id,
                    'rule': rule,
                    'created_at': datetime.utcnow(),
                    'last_triggered': None,
                    'trigger_count': 0
                }
                
                created_alerts.append(alert_id)
                logger.info(f"Created audit alert {alert_id}")
            
            return created_alerts
            
        except Exception as e:
            logger.error(f"Failed to setup audit alerts: {e}")
            return []
    
    def evaluate_audit_alerts(self, events: List[AuditEvent]) -> List[AuditAlert]:
        """Evaluate audit events against alert rules"""
        triggered_alerts = []
        
        for alert_id, alert_config in self.alerts.items():
            rule = alert_config['rule']
            
            try:
                # Evaluate rule against events
                matching_events = self._evaluate_alert_rule(rule, events)
                
                if matching_events:
                    alert = AuditAlert(
                        alert_id=f"triggered-{alert_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        rule_id=alert_id,
                        rule_name=rule['name'],
                        severity=rule['severity'],
                        triggered_at=datetime.utcnow(),
                        event_count=len(matching_events),
                        events=matching_events,
                        description=rule['description'],
                        action_taken=rule.get('action', 'none'),
                        status='triggered'
                    )
                    
                    triggered_alerts.append(alert)
                    
                    # Update alert config
                    alert_config['last_triggered'] = datetime.utcnow()
                    alert_config['trigger_count'] += 1
                    
                    logger.warning(f"Alert triggered: {rule['name']} - {len(matching_events)} events")
                
            except Exception as e:
                logger.error(f"Failed to evaluate alert {alert_id}: {e}")
        
        return triggered_alerts
    
    def _evaluate_alert_rule(self, rule: Dict[str, Any], events: List[AuditEvent]) -> List[AuditEvent]:
        """Evaluate a single alert rule against events"""
        matching_events = []
        
        for event in events:
            # Check event type
            if 'event_types' in rule:
                if event.event_type.value not in rule['event_types']:
                    continue
            
            # Check severity
            if 'severity' in rule:
                if event.severity != rule['severity']:
                    continue
            
            # Check user
            if 'users' in rule:
                if event.user_id not in rule['users']:
                    continue
            
            # Check time window
            if 'time_window' in rule:
                window_minutes = rule['time_window']
                cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
                if event.timestamp < cutoff_time:
                    continue
            
            # Check custom conditions
            if 'conditions' in rule:
                conditions_met = True
                for condition in rule['conditions']:
                    field = condition['field']
                    operator = condition['operator']
                    value = condition['value']
                    
                    event_value = getattr(event, field, None)
                    if event_value is None:
                        conditions_met = False
                        break
                    
                    if operator == 'equals':
                        if event_value != value:
                            conditions_met = False
                            break
                    elif operator == 'contains':
                        if value not in str(event_value):
                            conditions_met = False
                            break
                    elif operator == 'greater_than':
                        if event_value <= value:
                            conditions_met = False
                            break
                
                if not conditions_met:
                    continue
            
            matching_events.append(event)
        
        # Check threshold
        if 'threshold' in rule:
            if len(matching_events) < rule['threshold']:
                return []
        
        return matching_events
    
    def export_audit_data(
        self,
        events: List[AuditEvent],
        format: str = "json",
        output_file: Optional[str] = None
    ) -> str:
        """Export audit data to specified format"""
        try:
            if format.lower() == "json":
                data = [asdict(event) for event in events]
                # Convert datetime objects to strings
                for event_data in data:
                    event_data['timestamp'] = event_data['timestamp'].isoformat()
                    event_data['event_type'] = event_data['event_type']
                
                output = json.dumps(data, indent=2, default=str)
            
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                header = ['event_id', 'timestamp', 'event_type', 'user_id', 'user_name', 'resource_id', 'resource_name', 'resource_type', 'provider', 'region', 'environment', 'action', 'result', 'source_ip', 'user_agent', 'severity']
                writer.writerow(header)
                
                # Write events
                for event in events:
                    row = [
                        event.event_id,
                        event.timestamp.isoformat(),
                        event.event_type.value,
                        event.user_id,
                        event.user_name,
                        event.resource_id,
                        event.resource_name,
                        event.resource_type,
                        event.provider,
                        event.region,
                        event.environment,
                        event.action,
                        event.result,
                        event.source_ip,
                        event.user_agent,
                        event.severity
                    ]
                    writer.writerow(row)
                
                output = output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            # Save to file if specified
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(output)
                logger.info(f"Exported {len(events)} audit events to {output_file}")
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to export audit data: {e}")
            raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Multi-Cloud Audit Trail Manager')
    parser.add_argument('--config', type=str, help='Configuration file')
    parser.add_argument('--providers', type=str, nargs='+', default=['aws'], help='Cloud providers')
    parser.add_argument('--action', type=str, required=True, choices=[
        'discover', 'collect', 'analyze', 'report', 'alerts', 'export'
    ], help='Action to perform')
    parser.add_argument('--start-time', type=str, help='Start time (ISO format)')
    parser.add_argument('--end-time', type=str, help='End time (ISO format)')
    parser.add_argument('--output', type=str, help='Output file')
    parser.add_argument('--format', type=str, default='json', choices=['json', 'csv'], help='Output format')
    
    args = parser.parse_args()
    
    try:
        # Initialize manager
        manager = AuditTrailManager(args.config)
        
        # Initialize handlers
        if not manager.initialize_handlers(args.providers):
            logger.error("Failed to initialize handlers")
            sys.exit(1)
        
        # Execute action
        if args.action == 'discover':
            trails = manager.discover_audit_trails(args.providers)
            print(json.dumps({p: [asdict(t) for t in trail_list] for p, trail_list in trails.items()}, indent=2, default=str))
        
        elif args.action == 'collect':
            start_time = datetime.fromisoformat(args.start_time) if args.start_time else datetime.utcnow() - timedelta(hours=24)
            end_time = datetime.fromisoformat(args.end_time) if args.end_time else datetime.utcnow()
            
            events = manager.collect_audit_events(args.providers, start_time, end_time)
            all_events = []
            for provider_events in events.values():
                all_events.extend(provider_events)
            
            output = manager.export_audit_data(all_events, args.format, args.output)
            if not args.output:
                print(output)
        
        elif args.action == 'analyze':
            start_time = datetime.fromisoformat(args.start_time) if args.start_time else datetime.utcnow() - timedelta(hours=24)
            end_time = datetime.fromisoformat(args.end_time) if args.end_time else datetime.utcnow()
            
            events = manager.collect_audit_events(args.providers, start_time, end_time)
            all_events = []
            for provider_events in events.values():
                all_events.extend(provider_events)
            
            analysis = manager.analyze_audit_events(all_events)
            print(json.dumps(analysis, indent=2, default=str))
        
        elif args.action == 'report':
            # Create a sample query
            query_config = {
                'name': 'Security Events Report',
                'description': 'Report of security-related audit events',
                'event_types': ['user_login', 'permission_change', 'security_event'],
                'start_time': args.start_time or (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                'end_time': args.end_time or datetime.utcnow().isoformat(),
                'filters': {}
            }
            
            query = manager.create_audit_query(query_config)
            report = manager.generate_audit_report(query, args.providers)
            
            output_data = asdict(report)
            output_data['query'] = asdict(report.query)
            output_data['generated_at'] = report.generated_at.isoformat()
            
            print(json.dumps(output_data, indent=2, default=str))
        
        elif args.action == 'alerts':
            # Setup sample alerts
            alert_rules = [
                {
                    'name': 'Failed Login Alert',
                    'description': 'Alert on multiple failed login attempts',
                    'severity': 'high',
                    'event_types': ['user_login'],
                    'conditions': [
                        {'field': 'result', 'operator': 'equals', 'value': 'failed'}
                    ],
                    'threshold': 5,
                    'time_window': 60,
                    'action': 'notify'
                },
                {
                    'name': 'Privilege Escalation Alert',
                    'description': 'Alert on privilege escalation events',
                    'severity': 'critical',
                    'event_types': ['permission_change'],
                    'conditions': [
                        {'field': 'action', 'operator': 'contains', 'value': 'admin'}
                    ],
                    'threshold': 1,
                    'action': 'immediate_notify'
                }
            ]
            
            alert_ids = manager.setup_audit_alerts(alert_rules)
            print(f"Created {len(alert_ids)} alert rules: {alert_ids}")
        
        elif args.action == 'export':
            start_time = datetime.fromisoformat(args.start_time) if args.start_time else datetime.utcnow() - timedelta(hours=24)
            end_time = datetime.fromisoformat(args.end_time) if args.end_time else datetime.utcnow()
            
            events = manager.collect_audit_events(args.providers, start_time, end_time)
            all_events = []
            for provider_events in events.values():
                all_events.extend(provider_events)
            
            output = manager.export_audit_data(all_events, args.format, args.output)
            if not args.output:
                print(output)
        
        logger.info(f"Completed {args.action} action successfully")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
