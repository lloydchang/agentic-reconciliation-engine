#!/usr/bin/env python3
"""
Alert Router Script

Multi-cloud automation for intelligent alert routing and distribution across AWS, Azure, GCP, and on-premise environments.
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

class RoutingStrategy(Enum):
    SEVERITY_BASED = "severity_based"
    CATEGORY_BASED = "category_based"
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    EXPERT_BASED = "expert_based"
    TIME_BASED = "time_based"

class NotificationChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"
    TEAMS = "teams"

@dataclass
class Alert:
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    category: str
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    created_at: datetime
    labels: Dict[str, str]
    annotations: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class RoutingRule:
    rule_id: str
    rule_name: str
    description: str
    conditions: Dict[str, Any]
    strategy: RoutingStrategy
    target_channels: List[NotificationChannel]
    target_teams: List[str]
    target_individuals: List[str]
    escalation_policy: Optional[Dict[str, Any]]
    suppression_window: Optional[Dict[str, Any]]
    enabled: bool
    priority: int

@dataclass
class RoutingResult:
    alert_id: str
    routing_strategy: RoutingStrategy
    applied_rules: List[str]
    target_channels: List[str]
    target_recipients: List[str]
    escalation_triggered: bool
    suppression_active: bool
    routing_confidence: float
    delivery_status: Dict[str, str]
    error_message: Optional[str]

@dataclass
class NotificationChannel:
    channel_id: str
    channel_type: NotificationChannel
    name: str
    configuration: Dict[str, Any]
    enabled: bool
    rate_limit: Optional[Dict[str, Any]]
    retry_policy: Optional[Dict[str, Any]]

class AlertRouter:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.rules = {}
        self.channels = {}
        self.routing_history = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load alert router configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'routing_settings': {
                'default_strategy': 'severity_based',
                'enable_ml_routing': True,
                'max_recipients_per_alert': 10,
                'enable_deduplication': True,
                'deduplication_window_minutes': 15,
                'enable_load_balancing': True,
                'fallback_strategy': 'round_robin'
            },
            'notification_settings': {
                'enable_retry': True,
                'max_retry_attempts': 3,
                'retry_delay_seconds': 60,
                'enable_rate_limiting': True,
                'rate_limit_per_minute': 100,
                'batch_notifications': True,
                'batch_size': 10
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
    
    def load_routing_rules(self, rules_file: Optional[str] = None) -> Dict[str, RoutingRule]:
        """Load alert routing rules"""
        logger.info("Loading alert routing rules")
        
        # Default routing rules
        default_rules = {
            'critical-production': RoutingRule(
                rule_id='critical-production',
                rule_name='Critical Production Alerts',
                description='Route critical production alerts to on-call team',
                conditions={
                    'severity': ['critical'],
                    'environment': ['production'],
                    'categories': ['infrastructure', 'security', 'availability']
                },
                strategy=RoutingStrategy.SEVERITY_BASED,
                target_channels=[NotificationChannel.PAGERDUTY, NotificationChannel.SLACK],
                target_teams=['on-call', 'sre'],
                target_individuals=[],
                escalation_policy={
                    'escalation_after_minutes': 15,
                    'escalation_to': ['manager', 'director'],
                    'max_escalations': 3
                },
                suppression_window=None,
                enabled=True,
                priority=1
            ),
            'security-alerts': RoutingRule(
                rule_id='security-alerts',
                rule_name='Security Alerts Routing',
                description='Route all security alerts to security team',
                conditions={
                    'category': ['security'],
                    'severity': ['critical', 'high', 'medium']
                },
                strategy=RoutingStrategy.EXPERT_BASED,
                target_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                target_teams=['security-team'],
                target_individuals=['security-lead'],
                escalation_policy={
                    'escalation_after_minutes': 30,
                    'escalation_to': ['ciso'],
                    'max_escalations': 2
                },
                suppression_window=None,
                enabled=True,
                priority=2
            ),
            'cost-alerts': RoutingRule(
                rule_id='cost-alerts',
                rule_name='Cost Alerts Routing',
                description='Route cost alerts to finance team',
                conditions={
                    'category': ['cost'],
                    'severity': ['high', 'critical']
                },
                strategy=RoutingStrategy.CATEGORY_BASED,
                target_channels=[NotificationChannel.EMAIL],
                target_teams=['finance', 'devops'],
                target_individuals=[],
                escalation_policy={
                    'escalation_after_minutes': 60,
                    'escalation_to': ['vp-finance'],
                    'max_escalations': 2
                },
                suppression_window=None,
                enabled=True,
                priority=3
            ),
            'business-hours': RoutingRule(
                rule_id='business-hours',
                rule_name='Business Hours Routing',
                description='Route non-critical alerts during business hours',
                conditions={
                    'severity': ['low', 'medium'],
                    'time_window': 'business_hours',
                    'exclude_critical': True
                },
                strategy=RoutingStrategy.TIME_BASED,
                target_channels=[NotificationChannel.EMAIL],
                target_teams=['dev-team'],
                target_individuals=[],
                escalation_policy=None,
                suppression_window={
                    'start_hour': 18,
                    'end_hour': 8,
                    'weekdays_only': True
                },
                enabled=True,
                priority=4
            ),
            'load-balanced-routing': RoutingRule(
                rule_id='load-balanced-routing',
                rule_name='Load Balanced Routing',
                description='Balance alert load across team members',
                conditions={
                    'category': ['application', 'performance'],
                    'severity': ['medium', 'low']
                },
                strategy=RoutingStrategy.LOAD_BALANCED,
                target_channels=[NotificationChannel.SLACK],
                target_teams=['dev-team'],
                target_individuals=[],
                escalation_policy=None,
                suppression_window=None,
                enabled=True,
                priority=5
            )
        }
        
        # Load custom rules from file if provided
        if rules_file:
            try:
                with open(rules_file, 'r') as f:
                    custom_rules = json.load(f)
                
                for rule_id, rule_data in custom_rules.items():
                    rule = RoutingRule(
                        rule_id=rule_id,
                        rule_name=rule_data['rule_name'],
                        description=rule_data['description'],
                        conditions=rule_data['conditions'],
                        strategy=RoutingStrategy(rule_data['strategy']),
                        target_channels=[NotificationChannel(ch) for ch in rule_data['target_channels']],
                        target_teams=rule_data['target_teams'],
                        target_individuals=rule_data['target_individuals'],
                        escalation_policy=rule_data.get('escalation_policy'),
                        suppression_window=rule_data.get('suppression_window'),
                        enabled=rule_data.get('enabled', True),
                        priority=rule_data.get('priority', 10)
                    )
                    default_rules[rule_id] = rule
                    
            except Exception as e:
                logger.warning(f"Failed to load custom rules: {e}")
        
        self.rules = default_rules
        logger.info(f"Loaded {len(self.rules)} routing rules")
        
        return self.rules
    
    def load_notification_channels(self, channels_file: Optional[str] = None) -> Dict[str, NotificationChannel]:
        """Load notification channel configurations"""
        logger.info("Loading notification channels")
        
        # Default channels
        default_channels = {
            'pagerduty-primary': NotificationChannel(
                channel_id='pagerduty-primary',
                channel_type=NotificationChannel.PAGERDUTY,
                name='Primary PagerDuty',
                configuration={
                    'service_key': 'pagerduty-service-key',
                    'severity_mapping': {
                        'critical': 'critical',
                        'high': 'high',
                        'medium': 'warning',
                        'low': 'info'
                    }
                },
                enabled=True,
                rate_limit={
                    'max_per_minute': 10,
                    'burst_size': 5
                },
                retry_policy={
                    'max_attempts': 3,
                    'backoff_seconds': [30, 60, 120]
                }
            ),
            'slack-alerts': NotificationChannel(
                channel_id='slack-alerts',
                channel_type=NotificationChannel.SLACK,
                name='Alerts Slack Channel',
                configuration={
                    'webhook_url': 'https://hooks.slack.com/services/...',
                    'channel': '#alerts',
                    'username': 'AlertBot',
                    'icon_emoji': ':warning:'
                },
                enabled=True,
                rate_limit={
                    'max_per_minute': 50,
                    'burst_size': 20
                },
                retry_policy={
                    'max_attempts': 2,
                    'backoff_seconds': [15, 30]
                }
            ),
            'email-notifications': NotificationChannel(
                channel_id='email-notifications',
                channel_type=NotificationChannel.EMAIL,
                name='Email Notifications',
                configuration={
                    'smtp_server': 'smtp.company.com',
                    'smtp_port': 587,
                    'from_address': 'alerts@company.com',
                    'use_tls': True
                },
                enabled=True,
                rate_limit={
                    'max_per_minute': 100,
                    'burst_size': 50
                },
                retry_policy={
                    'max_attempts': 3,
                    'backoff_seconds': [60, 120, 300]
                }
            ),
            'teams-alerts': NotificationChannel(
                channel_id='teams-alerts',
                channel_type=NotificationChannel.TEAMS,
                name='Teams Alerts Channel',
                configuration={
                    'webhook_url': 'https://outlook.office.com/webhook/...',
                    'title_template': 'Alert: {title}',
                    'summary_template': '{severity} alert in {environment}'
                },
                enabled=True,
                rate_limit={
                    'max_per_minute': 30,
                    'burst_size': 15
                },
                retry_policy={
                    'max_attempts': 2,
                    'backoff_seconds': [20, 40]
                }
            ),
            'webhook-custom': NotificationChannel(
                channel_id='webhook-custom',
                channel_type=NotificationChannel.WEBHOOK,
                name='Custom Webhook',
                configuration={
                    'url': 'https://api.company.com/alerts',
                    'headers': {
                        'Authorization': 'Bearer token',
                        'Content-Type': 'application/json'
                    }
                },
                enabled=True,
                rate_limit={
                    'max_per_minute': 20,
                    'burst_size': 10
                },
                retry_policy={
                    'max_attempts': 3,
                    'backoff_seconds': [10, 30, 60]
                }
            )
        }
        
        # Load custom channels from file if provided
        if channels_file:
            try:
                with open(channels_file, 'r') as f:
                    custom_channels = json.load(f)
                
                for channel_id, channel_data in custom_channels.items():
                    channel = NotificationChannel(
                        channel_id=channel_id,
                        channel_type=NotificationChannel(channel_data['channel_type']),
                        name=channel_data['name'],
                        configuration=channel_data['configuration'],
                        enabled=channel_data.get('enabled', True),
                        rate_limit=channel_data.get('rate_limit'),
                        retry_policy=channel_data.get('retry_policy')
                    )
                    default_channels[channel_id] = channel
                    
            except Exception as e:
                logger.warning(f"Failed to load custom channels: {e}")
        
        self.channels = default_channels
        logger.info(f"Loaded {len(self.channels)} notification channels")
        
        return self.channels
    
    def route_alert(self, alert: Alert) -> RoutingResult:
        """Route alert to appropriate channels and recipients"""
        logger.info(f"Routing alert {alert.alert_id}")
        
        try:
            # Check for deduplication
            if self.config['routing_settings']['enable_deduplication']:
                if self._is_duplicate_alert(alert):
                    logger.info(f"Alert {alert.alert_id} is duplicate, skipping routing")
                    return RoutingResult(
                        alert_id=alert.alert_id,
                        routing_strategy=RoutingStrategy.SEVERITY_BASED,
                        applied_rules=['deduplication'],
                        target_channels=[],
                        target_recipients=[],
                        escalation_triggered=False,
                        suppression_active=True,
                        routing_confidence=1.0,
                        delivery_status={},
                        error_message="Duplicate alert suppressed"
                    )
            
            # Find matching routing rules
            matching_rules = self._find_matching_rules(alert)
            
            if not matching_rules:
                # Use fallback strategy
                logger.warning(f"No matching rules for alert {alert.alert_id}, using fallback strategy")
                return self._apply_fallback_routing(alert)
            
            # Apply highest priority rule
            selected_rule = min(matching_rules, key=lambda r: r.priority)
            
            # Execute routing strategy
            routing_result = self._execute_routing_strategy(alert, selected_rule)
            
            # Record routing history
            self.routing_history.append({
                'alert_id': alert.alert_id,
                'rule_id': selected_rule.rule_id,
                'strategy': selected_rule.strategy.value,
                'timestamp': datetime.utcnow(),
                'success': routing_result.error_message is None
            })
            
            return routing_result
            
        except Exception as e:
            logger.error(f"Failed to route alert {alert.alert_id}: {e}")
            return RoutingResult(
                alert_id=alert.alert_id,
                routing_strategy=RoutingStrategy.SEVERITY_BASED,
                applied_rules=[],
                target_channels=[],
                target_recipients=[],
                escalation_triggered=False,
                suppression_active=False,
                routing_confidence=0.0,
                delivery_status={},
                error_message=str(e)
            )
    
    def _is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if alert is a duplicate"""
        deduplication_window = self.config['routing_settings']['deduplication_window_minutes']
        cutoff_time = datetime.utcnow() - timedelta(minutes=deduplication_window)
        
        # Check recent routing history for similar alerts
        for history_item in self.routing_history:
            if (history_item['timestamp'] >= cutoff_time and 
                history_item['alert_id'] != alert.alert_id):
                # In real implementation, this would check alert content similarity
                # For now, we'll use a simple check
                pass
        
        return False
    
    def _find_matching_rules(self, alert: Alert) -> List[RoutingRule]:
        """Find routing rules that match the alert"""
        matching_rules = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if self._rule_matches(alert, rule):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _rule_matches(self, alert: Alert, rule: RoutingRule) -> bool:
        """Check if alert matches routing rule conditions"""
        conditions = rule.conditions
        
        # Check severity condition
        if 'severity' in conditions:
            if alert.severity.value not in conditions['severity']:
                return False
        
        # Check environment condition
        if 'environment' in conditions:
            if alert.environment not in conditions['environment']:
                return False
        
        # Check category condition
        if 'categories' in conditions:
            if alert.category not in conditions['categories']:
                return False
        
        # Check category condition (single)
        if 'category' in conditions:
            if alert.category != conditions['category']:
                return False
        
        # Check time window condition
        if 'time_window' in conditions:
            if not self._is_in_time_window(conditions['time_window']):
                return False
        
        # Check exclude critical condition
        if 'exclude_critical' in conditions and conditions['exclude_critical']:
            if alert.severity == AlertSeverity.CRITICAL:
                return False
        
        return True
    
    def _is_in_time_window(self, time_window: str) -> bool:
        """Check if current time is in specified time window"""
        now = datetime.utcnow()
        
        if time_window == 'business_hours':
            # Business hours: 9 AM - 6 PM, Monday-Friday
            if now.weekday() >= 5:  # Saturday or Sunday
                return False
            return 9 <= now.hour < 18
        elif time_window == 'after_hours':
            # After hours: 6 PM - 9 AM
            return now.hour >= 18 or now.hour < 9
        elif time_window == 'weekends':
            return now.weekday() >= 5
        
        return True
    
    def _execute_routing_strategy(self, alert: Alert, rule: RoutingRule) -> RoutingResult:
        """Execute the routing strategy"""
        try:
            # Check suppression window
            suppression_active = False
            if rule.suppression_window:
                suppression_active = self._is_in_suppression_window(rule.suppression_window)
            
            if suppression_active:
                return RoutingResult(
                    alert_id=alert.alert_id,
                    routing_strategy=rule.strategy,
                    applied_rules=[rule.rule_id],
                    target_channels=[],
                    target_recipients=[],
                    escalation_triggered=False,
                    suppression_active=True,
                    routing_confidence=1.0,
                    delivery_status={},
                    error_message="Alert suppressed due to suppression window"
                )
            
            # Get target recipients
            target_recipients = self._get_target_recipients(alert, rule)
            
            # Get target channels
            target_channels = [ch.channel_id for ch in rule.target_channels if ch.enabled]
            
            # Apply strategy-specific logic
            if rule.strategy == RoutingStrategy.LOAD_BALANCED:
                target_recipients = self._apply_load_balancing(target_recipients)
            elif rule.strategy == RoutingStrategy.ROUND_ROBIN:
                target_recipients = self._apply_round_robin(target_recipients)
            elif rule.strategy == RoutingStrategy.EXPERT_BASED:
                target_recipients = self._apply_expert_routing(alert, target_recipients)
            
            # Send notifications
            delivery_status = self._send_notifications(alert, target_channels, target_recipients)
            
            # Check for escalation
            escalation_triggered = False
            if rule.escalation_policy:
                escalation_triggered = self._check_escalation_needed(alert, rule.escalation_policy)
            
            # Calculate routing confidence
            routing_confidence = self._calculate_routing_confidence(alert, rule)
            
            return RoutingResult(
                alert_id=alert.alert_id,
                routing_strategy=rule.strategy,
                applied_rules=[rule.rule_id],
                target_channels=target_channels,
                target_recipients=target_recipients,
                escalation_triggered=escalation_triggered,
                suppression_active=False,
                routing_confidence=routing_confidence,
                delivery_status=delivery_status,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Failed to execute routing strategy: {e}")
            return RoutingResult(
                alert_id=alert.alert_id,
                routing_strategy=rule.strategy,
                applied_rules=[rule.rule_id],
                target_channels=[],
                target_recipients=[],
                escalation_triggered=False,
                suppression_active=False,
                routing_confidence=0.0,
                delivery_status={},
                error_message=str(e)
            )
    
    def _apply_fallback_routing(self, alert: Alert) -> RoutingResult:
        """Apply fallback routing strategy"""
        fallback_strategy = RoutingStrategy(self.config['routing_settings']['fallback_strategy'])
        
        # Simple fallback: route to default channels
        default_channels = ['slack-alerts', 'email-notifications']
        default_recipients = ['dev-team']
        
        delivery_status = self._send_notifications(alert, default_channels, default_recipients)
        
        return RoutingResult(
            alert_id=alert.alert_id,
            routing_strategy=fallback_strategy,
            applied_rules=['fallback'],
            target_channels=default_channels,
            target_recipients=default_recipients,
            escalation_triggered=False,
            suppression_active=False,
            routing_confidence=0.5,
            delivery_status=delivery_status,
            error_message=None
        )
    
    def _get_target_recipients(self, alert: Alert, rule: RoutingRule) -> List[str]:
        """Get target recipients for alert"""
        recipients = []
        
        # Add teams
        recipients.extend(rule.target_teams)
        
        # Add individuals
        recipients.extend(rule.target_individuals)
        
        # Add severity-based recipients
        if alert.severity == AlertSeverity.CRITICAL:
            recipients.extend(['on-call', 'manager'])
        elif alert.severity == AlertSeverity.HIGH:
            recipients.extend(['on-call'])
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        # Limit recipients
        max_recipients = self.config['routing_settings']['max_recipients_per_alert']
        if len(recipients) > max_recipients:
            recipients = recipients[:max_recipients]
        
        return recipients
    
    def _apply_load_balancing(self, recipients: List[str]) -> List[str]:
        """Apply load balancing to recipients"""
        # Simplified load balancing - rotate recipients
        # In real implementation, this would track current load per recipient
        return recipients
    
    def _apply_round_robin(self, recipients: List[str]) -> List[str]:
        """Apply round-robin to recipients"""
        # Simplified round-robin
        # In real implementation, this would track last assigned recipient
        return recipients
    
    def _apply_expert_routing(self, alert: Alert, recipients: List[str]) -> List[str]:
        """Apply expert-based routing"""
        # Simplified expert routing based on alert category
        expert_mapping = {
            'infrastructure': ['sre-team', 'infrastructure-team'],
            'security': ['security-team'],
            'application': ['dev-team', 'app-team'],
            'performance': ['performance-team'],
            'cost': ['finance-team', 'devops-team']
        }
        
        experts = expert_mapping.get(alert.category, [])
        return list(set(recipients + experts))
    
    def _send_notifications(self, alert: Alert, channels: List[str], recipients: List[str]) -> Dict[str, str]:
        """Send notifications through specified channels"""
        delivery_status = {}
        
        for channel_id in channels:
            if channel_id not in self.channels:
                delivery_status[channel_id] = 'failed'
                continue
            
            channel = self.channels[channel_id]
            
            if not channel.enabled:
                delivery_status[channel_id] = 'disabled'
                continue
            
            try:
                # Check rate limiting
                if not self._check_rate_limit(channel):
                    delivery_status[channel_id] = 'rate_limited'
                    continue
                
                # Send notification
                success = self._send_to_channel(channel, alert, recipients)
                delivery_status[channel_id] = 'sent' if success else 'failed'
                
            except Exception as e:
                logger.error(f"Failed to send to channel {channel_id}: {e}")
                delivery_status[channel_id] = 'error'
        
        return delivery_status
    
    def _check_rate_limit(self, channel: NotificationChannel) -> bool:
        """Check if channel is rate limited"""
        # Simplified rate limiting check
        # In real implementation, this would track actual send rates
        return True
    
    def _send_to_channel(self, channel: NotificationChannel, alert: Alert, recipients: List[str]) -> bool:
        """Send alert to specific channel"""
        try:
            if channel.channel_type == NotificationChannel.EMAIL:
                return self._send_email(channel, alert, recipients)
            elif channel.channel_type == NotificationChannel.SLACK:
                return self._send_slack(channel, alert, recipients)
            elif channel.channel_type == NotificationChannel.PAGERDUTY:
                return self._send_pagerduty(channel, alert, recipients)
            elif channel.channel_type == NotificationChannel.WEBHOOK:
                return self._send_webhook(channel, alert, recipients)
            elif channel.channel_type == NotificationChannel.TEAMS:
                return self._send_teams(channel, alert, recipients)
            else:
                logger.warning(f"Unsupported channel type: {channel.channel_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send to {channel.channel_type}: {e}")
            return False
    
    def _send_email(self, channel: NotificationChannel, alert: Alert, recipients: List[str]) -> bool:
        """Send email notification"""
        # Simplified email sending
        logger.info(f"Sending email to {recipients}: {alert.title}")
        return True
    
    def _send_slack(self, channel: NotificationChannel, alert: Alert, recipients: List[str]) -> bool:
        """Send Slack notification"""
        # Simplified Slack sending
        logger.info(f"Sending Slack to {channel.configuration.get('channel', '#alerts')}: {alert.title}")
        return True
    
    def _send_pagerduty(self, channel: NotificationChannel, alert: Alert, recipients: List[str]) -> bool:
        """Send PagerDuty notification"""
        # Simplified PagerDuty sending
        logger.info(f"Sending PagerDuty alert: {alert.title}")
        return True
    
    def _send_webhook(self, channel: NotificationChannel, alert: Alert, recipients: List[str]) -> bool:
        """Send webhook notification"""
        # Simplified webhook sending
        logger.info(f"Sending webhook to {channel.configuration.get('url')}: {alert.title}")
        return True
    
    def _send_teams(self, channel: NotificationChannel, alert: Alert, recipients: List[str]) -> bool:
        """Send Teams notification"""
        # Simplified Teams sending
        logger.info(f"Sending Teams notification: {alert.title}")
        return True
    
    def _is_in_suppression_window(self, suppression_window: Dict[str, Any]) -> bool:
        """Check if current time is in suppression window"""
        now = datetime.utcnow()
        start_hour = suppression_window.get('start_hour', 18)
        end_hour = suppression_window.get('end_hour', 8)
        weekdays_only = suppression_window.get('weekdays_only', True)
        
        # Check weekdays
        if weekdays_only and now.weekday() >= 5:
            return False
        
        # Check time window
        if start_hour <= end_hour:
            # Same day window (e.g., 22:00 - 06:00)
            return start_hour <= now.hour < end_hour
        else:
            # Overnight window (e.g., 18:00 - 08:00)
            return now.hour >= start_hour or now.hour < end_hour
    
    def _check_escalation_needed(self, alert: Alert, escalation_policy: Dict[str, Any]) -> bool:
        """Check if escalation is needed"""
        # Simplified escalation check
        # In real implementation, this would check alert age and response time
        return alert.severity == AlertSeverity.CRITICAL
    
    def _calculate_routing_confidence(self, alert: Alert, rule: RoutingRule) -> float:
        """Calculate routing confidence score"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on rule specificity
        conditions_count = len(rule.conditions)
        confidence += min(0.3, conditions_count * 0.1)
        
        # Increase confidence for high severity alerts
        if alert.severity == AlertSeverity.CRITICAL:
            confidence += 0.2
        elif alert.severity == AlertSeverity.HIGH:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def batch_route_alerts(self, alerts: List[Alert]) -> List[RoutingResult]:
        """Route multiple alerts in batch"""
        logger.info(f"Batch routing {len(alerts)} alerts")
        
        results = []
        
        if self.config['notification_settings']['batch_notifications']:
            # Group alerts by routing rules
            alert_groups = self._group_alerts_by_rules(alerts)
            
            for rule_id, grouped_alerts in alert_groups.items():
                # Route alerts in the group
                for alert in grouped_alerts:
                    result = self.route_alert(alert)
                    results.append(result)
        else:
            # Route alerts individually
            for alert in alerts:
                result = self.route_alert(alert)
                results.append(result)
        
        return results
    
    def _group_alerts_by_rules(self, alerts: List[Alert]) -> Dict[str, List[Alert]]:
        """Group alerts by matching routing rules"""
        groups = {}
        
        for alert in alerts:
            matching_rules = self._find_matching_rules(alert)
            if matching_rules:
                selected_rule = min(matching_rules, key=lambda r: r.priority)
                if selected_rule.rule_id not in groups:
                    groups[selected_rule.rule_id] = []
                groups[selected_rule.rule_id].append(alert)
            else:
                # Group under fallback
                if 'fallback' not in groups:
                    groups['fallback'] = []
                groups['fallback'].append(alert)
        
        return groups
    
    def generate_routing_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive routing report"""
        logger.info("Generating routing report")
        
        # Calculate statistics
        total_routed = len(self.routing_history)
        successful_routes = len([h for h in self.routing_history if h['success']])
        failed_routes = total_routed - successful_routes
        success_rate = (successful_routes / total_routed * 100) if total_routed > 0 else 0
        
        # Strategy usage statistics
        strategy_usage = {}
        for history_item in self.routing_history:
            strategy = history_item['strategy']
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        # Rule usage statistics
        rule_usage = {}
        for history_item in self.routing_history:
            rule_id = history_item.get('rule_id', 'unknown')
            rule_usage[rule_id] = rule_usage.get(rule_id, 0) + 1
        
        # Channel usage statistics
        channel_usage = {}
        for history_item in self.routing_history:
            # In real implementation, this would track actual channel usage
            pass
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_alerts_routed': total_routed,
                'successful_routes': successful_routes,
                'failed_routes': failed_routes,
                'success_rate': success_rate,
                'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
                'enabled_channels': len([c for c in self.channels.values() if c.enabled])
            },
            'strategy_usage': strategy_usage,
            'rule_usage': rule_usage,
            'channel_usage': channel_usage,
            'recent_routing': self.routing_history[-20:],  # Last 20 routing events
            'top_rules': sorted(rule_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Routing report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Alert Router")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--rules", help="Routing rules file")
    parser.add_argument("--channels", help="Notification channels file")
    parser.add_argument("--action", choices=['route', 'batch', 'report'], 
                       default='route', help="Action to perform")
    parser.add_argument("--alert-file", help="Alert JSON file for routing")
    parser.add_argument("--batch-file", help="Batch alerts JSON file")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize alert router
    router = AlertRouter(args.config)
    
    # Load rules and channels
    router.load_routing_rules(args.rules)
    router.load_notification_channels(args.channels)
    
    try:
        if args.action == 'route':
            if not args.alert_file:
                print("Error: --alert-file required for route action")
                sys.exit(1)
            
            with open(args.alert_file, 'r') as f:
                alert_data = json.load(f)
            
            # Create alert object
            alert = Alert(
                alert_id=alert_data['alert_id'],
                title=alert_data['title'],
                description=alert_data['description'],
                severity=AlertSeverity(alert_data['severity']),
                category=alert_data['category'],
                provider=alert_data['provider'],
                resource_id=alert_data['resource_id'],
                resource_name=alert_data['resource_name'],
                environment=alert_data['environment'],
                created_at=datetime.fromisoformat(alert_data['created_at']),
                labels=alert_data.get('labels', {}),
                annotations=alert_data.get('annotations', {}),
                metadata=alert_data.get('metadata', {})
            )
            
            # Route alert
            result = router.route_alert(alert)
            
            print(f"\nRouting Result:")
            print(f"Alert ID: {result.alert_id}")
            print(f"Strategy: {result.routing_strategy.value}")
            print(f"Applied Rules: {result.applied_rules}")
            print(f"Target Channels: {result.target_channels}")
            print(f"Target Recipients: {result.target_recipients}")
            print(f"Escalation Triggered: {result.escalation_triggered}")
            print(f"Suppression Active: {result.suppression_active}")
            print(f"Routing Confidence: {result.routing_confidence:.2f}")
            print(f"Delivery Status: {result.delivery_status}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
        
        elif args.action == 'batch':
            if not args.batch_file:
                print("Error: --batch-file required for batch action")
                sys.exit(1)
            
            with open(args.batch_file, 'r') as f:
                alerts_data = json.load(f)
            
            # Create alert objects
            alerts = []
            for alert_data in alerts_data:
                alert = Alert(
                    alert_id=alert_data['alert_id'],
                    title=alert_data['title'],
                    description=alert_data['description'],
                    severity=AlertSeverity(alert_data['severity']),
                    category=alert_data['category'],
                    provider=alert_data['provider'],
                    resource_id=alert_data['resource_id'],
                    resource_name=alert_data['resource_name'],
                    environment=alert_data['environment'],
                    created_at=datetime.fromisoformat(alert_data['created_at']),
                    labels=alert_data.get('labels', {}),
                    annotations=alert_data.get('annotations', {}),
                    metadata=alert_data.get('metadata', {})
                )
                alerts.append(alert)
            
            # Batch route alerts
            results = router.batch_route_alerts(alerts)
            
            print(f"\nBatch Routing Results:")
            success_count = len([r for r in results if r.error_message is None])
            failed_count = len(results) - success_count
            
            print(f"Total Alerts: {len(results)}")
            print(f"Successful: {success_count}")
            print(f"Failed: {failed_count}")
            
            if args.output:
                results_data = [
                    {
                        'alert_id': r.alert_id,
                        'strategy': r.routing_strategy.value,
                        'success': r.error_message is None,
                        'channels': r.target_channels,
                        'recipients': r.target_recipients
                    }
                    for r in results
                ]
                with open(args.output, 'w') as f:
                    json.dump(results_data, f, indent=2)
                print(f"Results saved to: {args.output}")
        
        elif args.action == 'report':
            report = router.generate_routing_report(args.output)
            
            summary = report['summary']
            print(f"\nRouting Report:")
            print(f"Total Alerts Routed: {summary['total_alerts_routed']}")
            print(f"Successful Routes: {summary['successful_routes']}")
            print(f"Failed Routes: {summary['failed_routes']}")
            print(f"Success Rate: {summary['success_rate']:.1f}%")
            print(f"Enabled Rules: {summary['enabled_rules']}")
            print(f"Enabled Channels: {summary['enabled_channels']}")
            
            if args.output:
                print(f"Report saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Alert routing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
