#!/usr/bin/env python3
"""
Advanced Alerting System for AI Agent Evaluation Framework
Provides real-time alerting for evaluation anomalies, performance issues, and security concerns
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import jinja2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    timestamp: datetime
    source: str
    evaluation_id: Optional[str] = None
    trace_id: Optional[str] = None
    evaluator: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'evaluation_id': self.evaluation_id,
            'trace_id': self.trace_id,
            'evaluator': self.evaluator,
            'metrics': self.metrics,
            'tags': self.tags,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    enabled: bool = True
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    cooldown_minutes: int = 15
    tags: List[str] = field(default_factory=list)
    
    def evaluate(self, evaluation_results: Dict[str, Any]) -> bool:
        """Evaluate if alert should trigger"""
        if not self.enabled:
            return False
        
        for condition in self.conditions:
            if not self._evaluate_condition(condition, evaluation_results):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], results: Dict[str, Any]) -> bool:
        """Evaluate individual condition"""
        metric_path = condition.get('metric_path', '')
        operator = condition.get('operator', 'gt')
        threshold = condition.get('threshold', 0)
        
        # Extract metric value from results
        value = self._extract_metric_value(metric_path, results)
        if value is None:
            return False
        
        # Evaluate condition
        if operator == 'gt':
            return value > threshold
        elif operator == 'lt':
            return value < threshold
        elif operator == 'eq':
            return value == threshold
        elif operator == 'ne':
            return value != threshold
        elif operator == 'gte':
            return value >= threshold
        elif operator == 'lte':
            return value <= threshold
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    def _extract_metric_value(self, path: str, data: Dict[str, Any]) -> Any:
        """Extract metric value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current

class AlertAction:
    """Base class for alert actions"""
    
    async def execute(self, alert: Alert, rule: AlertRule) -> bool:
        """Execute alert action"""
        raise NotImplementedError

class EmailAlertAction(AlertAction):
    """Email alert action"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        self.template_env = jinja2.Environment(
            loader=jinja2.DictLoader({
                'alert_email': """
Subject: [{{ alert.severity.value.upper() }}] {{ alert.title }}

{{ alert.description }}

Alert Details:
- ID: {{ alert.id }}
- Severity: {{ alert.severity.value }}
- Status: {{ alert.status.value }}
- Timestamp: {{ alert.timestamp }}
- Source: {{ alert.source }}
{% if alert.evaluator %}- Evaluator: {{ alert.evaluator }}{% endif %}
{% if alert.trace_id %}- Trace ID: {{ alert.trace_id }}{% endif %}
{% if alert.evaluation_id %}- Evaluation ID: {{ alert.evaluation_id }}{% endif %}

Metrics:
{% for key, value in alert.metrics.items() %}
- {{ key }}: {{ value }}
{% endfor %}

{% if alert.tags %}
Tags: {{ alert.tags | join(', ') }}
{% endif %}

---
This alert was generated by the AI Agent Evaluation Framework
                """
            })
        )
    
    async def execute(self, alert: Alert, rule: AlertRule) -> bool:
        """Send email alert"""
        try:
            # Render email template
            template = self.template_env.get_template('alert_email')
            email_body = template.render(alert=alert)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.smtp_config['recipients'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Send email
            with smtplib.SMTP(
                self.smtp_config['smtp_host'],
                self.smtp_config['smtp_port']
            ) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                
                if self.smtp_config.get('username'):
                    server.login(
                        self.smtp_config['username'],
                        self.smtp_config['password']
                    )
                
                server.send_message(msg)
            
            logger.info(f"Email alert sent for {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

class SlackAlertAction(AlertAction):
    """Slack alert action"""
    
    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel
    
    async def execute(self, alert: Alert, rule: AlertRule) -> bool:
        """Send Slack alert"""
        try:
            # Determine color based on severity
            color_map = {
                AlertSeverity.CRITICAL: "#FF0000",
                AlertSeverity.HIGH: "#FF6600",
                AlertSeverity.MEDIUM: "#FFAA00",
                AlertSeverity.LOW: "#00AA00",
                AlertSeverity.INFO: "#0066CC"
            }
            
            # Create Slack payload
            payload = {
                "text": f"[{alert.severity.value.upper()}] {alert.title}",
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#CCCCCC"),
                        "fields": [
                            {
                                "title": "Description",
                                "value": alert.description,
                                "short": False
                            },
                            {
                                "title": "Severity",
                                "value": alert.severity.value,
                                "short": True
                            },
                            {
                                "title": "Status",
                                "value": alert.status.value,
                                "short": True
                            },
                            {
                                "title": "Source",
                                "value": alert.source,
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": True
                            }
                        ],
                        "footer": "AI Agent Evaluation Framework",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            if self.channel:
                payload["channel"] = self.channel
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert.id}")
                        return True
                    else:
                        logger.error(f"Slack alert failed: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

class WebhookAlertAction(AlertAction):
    """Generic webhook alert action"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def execute(self, alert: Alert, rule: AlertRule) -> bool:
        """Send webhook alert"""
        try:
            payload = {
                "alert": alert.to_dict(),
                "rule": {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json", **self.headers}
                ) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"Webhook alert sent for {alert.id}")
                        return True
                    else:
                        logger.error(f"Webhook alert failed: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False

class AlertManager:
    """Main alert management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.actions: Dict[str, AlertAction] = {}
        self.cooldowns: Dict[str, datetime] = {}
        
        # Initialize alert actions
        self._initialize_actions()
        
        # Load default rules
        self._load_default_rules()
    
    def _initialize_actions(self):
        """Initialize alert actions from configuration"""
        actions_config = self.config.get('actions', {})
        
        # Email action
        if 'email' in actions_config:
            self.actions['email'] = EmailAlertAction(actions_config['email'])
        
        # Slack action
        if 'slack' in actions_config:
            slack_config = actions_config['slack']
            self.actions['slack'] = SlackAlertAction(
                webhook_url=slack_config['webhook_url'],
                channel=slack_config.get('channel')
            )
        
        # Webhook action
        if 'webhook' in actions_config:
            webhook_config = actions_config['webhook']
            self.actions['webhook'] = WebhookAlertAction(
                webhook_url=webhook_config['webhook_url'],
                headers=webhook_config.get('headers')
            )
    
    def _load_default_rules(self):
        """Load default alert rules"""
        default_rules = [
            AlertRule(
                id="low-overall-score",
                name="Low Overall Evaluation Score",
                description="Triggered when overall evaluation score is below threshold",
                severity=AlertSeverity.HIGH,
                conditions=[
                    {
                        "metric_path": "summary.overall_score",
                        "operator": "lt",
                        "threshold": 0.5
                    }
                ],
                actions=["email", "slack"],
                cooldown_minutes=30
            ),
            AlertRule(
                id="critical-security-failure",
                name="Critical Security Evaluation Failure",
                description="Triggered when security evaluation fails critically",
                severity=AlertSeverity.CRITICAL,
                conditions=[
                    {
                        "metric_path": "evaluator_results.security.average_score",
                        "operator": "lt",
                        "threshold": 0.3
                    }
                ],
                actions=["email", "slack", "webhook"],
                cooldown_minutes=15
            ),
            AlertRule(
                id="performance-degradation",
                name="Performance Evaluation Degradation",
                description="Triggered when performance metrics show significant degradation",
                severity=AlertSeverity.MEDIUM,
                conditions=[
                    {
                        "metric_path": "evaluator_results.performance.average_score",
                        "operator": "lt",
                        "threshold": 0.6
                    }
                ],
                actions=["slack"],
                cooldown_minutes=60
            ),
            AlertRule(
                id="high-error-rate",
                name="High Evaluation Error Rate",
                description="Triggered when evaluation error rate exceeds threshold",
                severity=AlertSeverity.HIGH,
                conditions=[
                    {
                        "metric_path": "summary.evaluators_failed",
                        "operator": "gt",
                        "threshold": 2
                    }
                ],
                actions=["email", "slack"],
                cooldown_minutes=30
            ),
            AlertRule(
                id="compliance-violation",
                name="Compliance Evaluation Violation",
                description="Triggered when compliance evaluation fails",
                severity=AlertSeverity.HIGH,
                conditions=[
                    {
                        "metric_path": "evaluator_results.compliance.average_score",
                        "operator": "lt",
                        "threshold": 0.7
                    }
                ],
                actions=["email", "slack"],
                cooldown_minutes=45
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.id] = rule
    
    async def process_evaluation_results(self, evaluation_results: Dict[str, Any], 
                                       evaluation_id: Optional[str] = None):
        """Process evaluation results and trigger alerts if needed"""
        for rule_id, rule in self.rules.items():
            try:
                # Check cooldown
                if self._is_in_cooldown(rule_id):
                    continue
                
                # Evaluate rule
                if rule.evaluate(evaluation_results):
                    # Create alert
                    alert = self._create_alert(rule, evaluation_results, evaluation_id)
                    
                    # Add to active alerts
                    self.active_alerts[alert.id] = alert
                    self.alert_history.append(alert)
                    
                    # Execute actions
                    await self._execute_alert_actions(alert, rule)
                    
                    # Set cooldown
                    self.cooldowns[rule_id] = datetime.utcnow() + timedelta(minutes=rule.cooldown_minutes)
                    
                    logger.info(f"Alert triggered: {alert.id} - {alert.title}")
            
            except Exception as e:
                logger.error(f"Error processing rule {rule_id}: {e}")
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if rule is in cooldown period"""
        if rule_id not in self.cooldowns:
            return False
        
        return datetime.utcnow() < self.cooldowns[rule_id]
    
    def _create_alert(self, rule: AlertRule, evaluation_results: Dict[str, Any], 
                     evaluation_id: Optional[str] = None) -> Alert:
        """Create alert from rule and evaluation results"""
        alert_id = f"{rule.id}_{int(datetime.utcnow().timestamp())}"
        
        # Extract relevant metrics
        metrics = {}
        for condition in rule.conditions:
            metric_path = condition.get('metric_path', '')
            value = self._extract_metric_value(metric_path, evaluation_results)
            if value is not None:
                metrics[metric_path] = value
        
        return Alert(
            id=alert_id,
            title=rule.name,
            description=rule.description,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            source="ai-agent-evaluation",
            evaluation_id=evaluation_id,
            metrics=metrics,
            tags=rule.tags
        )
    
    def _extract_metric_value(self, path: str, data: Dict[str, Any]) -> Any:
        """Extract metric value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    async def _execute_alert_actions(self, alert: Alert, rule: AlertRule):
        """Execute alert actions"""
        for action_name in rule.actions:
            if action_name in self.actions:
                action = self.actions[action_name]
                try:
                    await action.execute(alert, rule)
                except Exception as e:
                    logger.error(f"Failed to execute action {action_name}: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved")
            return True
        
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
            return True
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get alert system metrics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        recent_alerts = [a for a in self.alert_history if a.timestamp > last_24h]
        
        return {
            "total_alerts": len(self.alert_history),
            "active_alerts": len(self.active_alerts),
            "alerts_last_24h": len(recent_alerts),
            "rules_configured": len(self.rules),
            "actions_configured": len(self.actions),
            "severity_breakdown": {
                severity.value: len([a for a in recent_alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "status_breakdown": {
                status.value: len([a for a in self.active_alerts if a.status == status])
                for status in AlertStatus
            }
        }

# Factory function
def create_alert_manager(config_path: Optional[str] = None) -> AlertManager:
    """Create alert manager with configuration"""
    if config_path:
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            "actions": {
                "email": {
                    "smtp_host": "localhost",
                    "smtp_port": 587,
                    "use_tls": True,
                    "from_email": "alerts@ai-agent-evaluation.local",
                    "recipients": ["admin@company.com"]
                }
            }
        }
    
    return AlertManager(config)
