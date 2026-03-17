#!/usr/bin/env python3
"""
Alert Router Handler

Cloud-specific operations handler for alert routing across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AlertData:
    alert_id: str
    title: str
    description: str
    severity: str
    category: str
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    created_at: datetime
    labels: Dict[str, str]
    annotations: Dict[str, str]
    metadata: Dict[str, Any]

class AlertRoutingHandler(ABC):
    """Abstract base class for cloud-specific alert routing operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_alerts_for_routing(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts that need routing"""
        pass
    
    @abstractmethod
    def send_notification(self, channel_type: str, recipients: List[str], alert: AlertData) -> bool:
        """Send notification through specified channel"""
        pass

class AWSAlertRoutingHandler(AlertRoutingHandler):
    """AWS-specific alert routing operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'sns': boto3.client('sns', region_name=self.region),
                'ses': boto3.client('ses', region_name=self.region),
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'events': boto3.client('events', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def get_alerts_for_routing(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from AWS that need routing"""
        try:
            alerts = []
            
            # Get CloudWatch alarms in ALARM state
            alarms_response = self.client['cloudwatch'].describe_alarms(
                StateValue='ALARM',
                AlarmTypes=['MetricAlarm', 'CompositeAlarm']
            )
            
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            for alarm in alarms_response['MetricAlarms']:
                if alarm['StateUpdatedTimestamp'] >= cutoff_time:
                    alert = AlertData(
                        alert_id=alarm['AlarmName'],
                        title=alarm['AlarmName'],
                        description=alarm.get('AlarmDescription', 'CloudWatch alarm triggered'),
                        severity=self._map_alarm_severity(alarm),
                        category=self._categorize_aws_alarm(alarm),
                        provider='aws',
                        resource_id=self._extract_resource_id(alarm),
                        resource_name=self._extract_resource_name(alarm),
                        environment=self._extract_environment(alarm),
                        created_at=alarm['AlarmConfigurationUpdatedTimestamp'],
                        labels=self._extract_alarm_labels(alarm),
                        annotations={
                            'namespace': alarm['Namespace'],
                            'metric_name': alarm['MetricName'],
                            'threshold': str(alarm.get('Threshold', 'N/A')),
                            'statistic': alarm.get('Statistic', 'Average')
                        },
                        metadata={
                            'alarm_arn': alarm['AlarmArn'],
                            'state_reason': alarm.get('StateReason', ''),
                            'evaluation_periods': alarm.get('EvaluationPeriods', 1)
                        }
                    )
                    alerts.append(alert)
            
            # Get AWS Health events
            health_alerts = self._get_aws_health_events(time_range_hours)
            alerts.extend(health_alerts)
            
            logger.info(f"Retrieved {len(alerts)} AWS alerts for routing")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get AWS alerts for routing: {e}")
            return []
    
    def send_notification(self, channel_type: str, recipients: List[str], alert: AlertData) -> bool:
        """Send notification through AWS services"""
        try:
            if channel_type == 'sns':
                return self._send_sns_notification(recipients, alert)
            elif channel_type == 'ses':
                return self._send_email_notification(recipients, alert)
            elif channel_type == 'events':
                return self._send_event_notification(recipients, alert)
            else:
                logger.warning(f"Unsupported channel type for AWS: {channel_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send AWS notification: {e}")
            return False
    
    def _get_aws_health_events(self, time_range_hours: int) -> List[AlertData]:
        """Get AWS Health events"""
        try:
            # Simplified AWS Health events collection
            # In real implementation, this would use AWS Health API
            health_events = [
                {
                    'title': 'EC2 Instance Performance Degraded',
                    'description': 'EC2 instance experiencing performance degradation',
                    'severity': 'high',
                    'category': 'infrastructure',
                    'service': 'EC2',
                    'event_type': 'issue'
                },
                {
                    'title': 'RDS Database Connection Issues',
                    'description': 'RDS database experiencing connection issues',
                    'severity': 'critical',
                    'category': 'infrastructure',
                    'service': 'RDS',
                    'event_type': 'issue'
                }
            ]
            
            alerts = []
            for event in health_events:
                alert = AlertData(
                    alert_id=f"health-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=event['title'],
                    description=event['description'],
                    severity=event['severity'],
                    category=event['category'],
                    provider='aws',
                    resource_id='aws-health-event',
                    resource_name='aws-health',
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(hours=1),
                    labels={'service': event['service'], 'event_type': event['event_type']},
                    annotations={'source': 'aws-health'},
                    metadata={'health_event_id': f"event-{len(alerts)}"}
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get AWS Health events: {e}")
            return []
    
    def _send_sns_notification(self, recipients: List[str], alert: AlertData) -> bool:
        """Send SNS notification"""
        try:
            # In real implementation, this would publish to SNS topics
            for recipient in recipients:
                topic_arn = f"arn:aws:sns:{self.region}:123456789012:{recipient}"
                
                message = {
                    'alert_id': alert.alert_id,
                    'title': alert.title,
                    'description': alert.description,
                    'severity': alert.severity,
                    'category': alert.category,
                    'resource': alert.resource_name,
                    'timestamp': alert.created_at.isoformat()
                }
                
                self.client['sns'].publish(
                    TopicArn=topic_arn,
                    Subject=f"[{alert.severity.upper()}] {alert.title}",
                    Message=json.dumps(message),
                    MessageStructure='json'
                )
            
            logger.info(f"Sent SNS notification to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SNS notification: {e}")
            return False
    
    def _send_email_notification(self, recipients: List[str], alert: AlertData) -> bool:
        """Send email notification via SES"""
        try:
            # In real implementation, this would send emails via SES
            subject = f"[{alert.severity.upper()}] {alert.title}"
            
            html_body = f"""
            <html>
            <body>
                <h2>Alert: {alert.title}</h2>
                <p><strong>Severity:</strong> {alert.severity}</p>
                <p><strong>Category:</strong> {alert.category}</p>
                <p><strong>Resource:</strong> {alert.resource_name}</p>
                <p><strong>Environment:</strong> {alert.environment}</p>
                <p><strong>Description:</strong> {alert.description}</p>
                <p><strong>Created:</strong> {alert.created_at}</p>
            </body>
            </html>
            """
            
            for recipient in recipients:
                self.client['ses'].send_email(
                    Source='alerts@company.com',
                    Destination={'ToAddresses': [recipient]},
                    Message={
                        'Subject': {'Data': subject},
                        'Body': {
                            'Html': {'Data': html_body},
                            'Text': {'Data': alert.description}
                        }
                    }
                )
            
            logger.info(f"Sent email notification to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_event_notification(self, recipients: List[str], alert: AlertData) -> bool:
        """Send EventBridge notification"""
        try:
            # In real implementation, this would send events to EventBridge
            for recipient in recipients:
                event_bus = f"arn:aws:events:{self.region}:123456789012:event-bus/{recipient}"
                
                event = {
                    'Source': 'com.company.alerts',
                    'DetailType': 'Alert Notification',
                    'Detail': json.dumps({
                        'alert_id': alert.alert_id,
                        'title': alert.title,
                        'severity': alert.severity,
                        'category': alert.category,
                        'resource': alert.resource_name,
                        'environment': alert.environment,
                        'description': alert.description,
                        'timestamp': alert.created_at.isoformat()
                    })
                }
                
                self.client['events'].put_events(
                    Entries=[{
                        'Source': event['Source'],
                        'DetailType': event['DetailType'],
                        'Detail': event['Detail'],
                        'EventBusName': event_bus
                    }]
                )
            
            logger.info(f"Sent EventBridge notification to {len(recipients)} event buses")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send EventBridge notification: {e}")
            return False
    
    def _map_alarm_severity(self, alarm: Dict[str, Any]) -> str:
        """Map CloudWatch alarm to severity"""
        # Check alarm name and description for severity indicators
        name = alarm['AlarmName'].lower()
        description = alarm.get('AlarmDescription', '').lower()
        
        if 'critical' in name or 'critical' in description:
            return 'critical'
        elif 'high' in name or 'high' in description:
            return 'high'
        elif 'warning' in name or 'warning' in description:
            return 'medium'
        else:
            return 'low'
    
    def _categorize_aws_alarm(self, alarm: Dict[str, Any]) -> str:
        """Categorize AWS alarm based on namespace and name"""
        namespace = alarm.get('Namespace', '')
        name = alarm['AlarmName'].lower()
        
        if 'EC2' in namespace or 'ec2' in name:
            return 'infrastructure'
        elif 'RDS' in namespace or 'rds' in name:
            return 'infrastructure'
        elif 'Lambda' in namespace or 'lambda' in name:
            return 'application'
        elif 'ELB' in namespace or 'elb' in name or 'alb' in name:
            return 'availability'
        elif 'Billing' in namespace or 'billing' in name:
            return 'cost'
        else:
            return 'application'
    
    def _extract_resource_id(self, alarm: Dict[str, Any]) -> str:
        """Extract resource ID from alarm dimensions"""
        dimensions = alarm.get('Dimensions', [])
        for dimension in dimensions:
            if dimension['Name'] in ['InstanceId', 'DBInstanceIdentifier', 'FunctionName']:
                return dimension['Value']
        return 'unknown'
    
    def _extract_resource_name(self, alarm: Dict[str, Any]) -> str:
        """Extract resource name from alarm"""
        return self._extract_resource_id(alarm)
    
    def _extract_environment(self, alarm: Dict[str, Any]) -> str:
        """Extract environment from alarm tags"""
        tags = alarm.get('Tags', [])
        for tag in tags:
            if tag['Key'].lower() == 'environment':
                return tag['Value']
        
        # Fallback to name analysis
        name = alarm['AlarmName'].lower()
        if 'prod' in name:
            return 'production'
        elif 'staging' in name:
            return 'staging'
        elif 'dev' in name:
            return 'development'
        
        return 'unknown'
    
    def _extract_alarm_labels(self, alarm: Dict[str, Any]) -> Dict[str, str]:
        """Extract labels from alarm"""
        labels = {}
        
        # Add dimensions as labels
        for dimension in alarm.get('Dimensions', []):
            labels[f"dimension_{dimension['Name']}"] = dimension['Value']
        
        # Add tags as labels
        for tag in alarm.get('Tags', []):
            labels[tag['Key']] = tag['Value']
        
        return labels

class AzureAlertRoutingHandler(AlertRoutingHandler):
    """Azure-specific alert routing operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.monitor import MonitorManagementClient
            from azure.mgmt.communication import CommunicationServiceClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'monitor': MonitorManagementClient(credential, "<subscription-id>"),
                'communication': CommunicationServiceClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def get_alerts_for_routing(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from Azure that need routing"""
        try:
            alerts = []
            
            # Get Azure Monitor alerts
            monitor_alerts = self._get_azure_monitor_alerts(time_range_hours)
            alerts.extend(monitor_alerts)
            
            # Get Log Analytics alerts
            log_analytics_alerts = self._get_log_analytics_alerts(time_range_hours)
            alerts.extend(log_analytics_alerts)
            
            logger.info(f"Retrieved {len(alerts)} Azure alerts for routing")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Azure alerts for routing: {e}")
            return []
    
    def send_notification(self, channel_type: str, recipients: List[str], alert: AlertData) -> bool:
        """Send notification through Azure services"""
        try:
            if channel_type == 'email':
                return self._send_azure_email(recipients, alert)
            elif channel_type == 'teams':
                return self._send_azure_teams(recipients, alert)
            else:
                logger.warning(f"Unsupported channel type for Azure: {channel_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Azure notification: {e}")
            return False
    
    def _get_azure_monitor_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Azure Monitor alerts"""
        try:
            # Simplified Azure Monitor alert collection
            azure_alerts = [
                {
                    'title': 'VM CPU High Utilization',
                    'description': 'Virtual machine CPU utilization is above threshold',
                    'severity': 'high',
                    'category': 'performance',
                    'resource_type': 'virtual_machine'
                },
                {
                    'title': 'App Service Response Time High',
                    'description': 'App service response time is exceeding SLA',
                    'severity': 'medium',
                    'category': 'performance',
                    'resource_type': 'app_service'
                }
            ]
            
            alerts = []
            for alert_data in azure_alerts:
                alert = AlertData(
                    alert_id=f"azure-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=alert_data['title'],
                    description=alert_data['description'],
                    severity=alert_data['severity'],
                    category=alert_data['category'],
                    provider='azure',
                    resource_id=f"azure-{alert_data['resource_type']}-{len(alerts)}",
                    resource_name=f"{alert_data['resource_type']}-{len(alerts)}",
                    region='eastus',
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(hours=1),
                    labels={'resource_type': alert_data['resource_type']},
                    annotations={'monitoring_service': 'azure-monitor'},
                    metadata={'cpu_utilization': 85.2, 'response_time': 450}
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Azure Monitor alerts: {e}")
            return []
    
    def _get_log_analytics_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Log Analytics alerts"""
        try:
            alert = AlertData(
                alert_id=f"azure-log-analytics-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                title='Application Error Spike Detected',
                description='Significant increase in application errors detected in logs',
                severity='medium',
                category='application',
                resource_id='azure-log-analytics-workspace',
                resource_name='log-analytics-workspace',
                region='eastus',
                environment='production',
                created_at=datetime.utcnow() - timedelta(minutes=45),
                labels={'workspace': 'production-workspace'},
                annotations={'query_type': 'log-analytics'},
                metadata={'error_rate': 12.3, 'time_window_minutes': 15}
            )
            return [alert]
            
        except Exception as e:
            logger.error(f"Failed to get Log Analytics alerts: {e}")
            return []
    
    def _send_azure_email(self, recipients: List[str], alert: AlertData) -> bool:
        """Send email via Azure Communication Services"""
        try:
            # In real implementation, this would use Azure Communication Services
            logger.info(f"Sending Azure email to {len(recipients)} recipients: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Azure email: {e}")
            return False
    
    def _send_azure_teams(self, recipients: List[str], alert: AlertData) -> bool:
        """Send Teams notification via Azure"""
        try:
            # In real implementation, this would use Azure Logic Apps or Teams API
            logger.info(f"Sending Azure Teams notification: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Azure Teams notification: {e}")
            return False

class GCPAlertRoutingHandler(AlertRoutingHandler):
    """GCP-specific alert routing operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import monitoring_v3
            from google.cloud import logging
            
            self.client = {
                'monitoring': monitoring_v3.MetricServiceClient(),
                'logging': logging.Client()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def get_alerts_for_routing(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from GCP that need routing"""
        try:
            alerts = []
            
            # Get Cloud Monitoring alerts
            monitoring_alerts = self._get_gcp_monitoring_alerts(time_range_hours)
            alerts.extend(monitoring_alerts)
            
            # Get Cloud Logging alerts
            logging_alerts = self._get_gcp_logging_alerts(time_range_hours)
            alerts.extend(logging_alerts)
            
            logger.info(f"Retrieved {len(alerts)} GCP alerts for routing")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get GCP alerts for routing: {e}")
            return []
    
    def send_notification(self, channel_type: str, recipients: List[str], alert: AlertData) -> bool:
        """Send notification through GCP services"""
        try:
            if channel_type == 'email':
                return self._send_gcp_email(recipients, alert)
            elif channel_type == 'webhook':
                return self._send_gcp_webhook(recipients, alert)
            else:
                logger.warning(f"Unsupported channel type for GCP: {channel_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send GCP notification: {e}")
            return False
    
    def _get_gcp_monitoring_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Cloud Monitoring alerts"""
        try:
            gcp_alerts = [
                {
                    'title': 'GCE Instance Memory Usage High',
                    'description': 'GCE instance memory usage is above threshold',
                    'severity': 'high',
                    'category': 'infrastructure',
                    'resource_type': 'compute_instance'
                },
                {
                    'title': 'Cloud SQL Database Connections High',
                    'description': 'Cloud SQL database connection count is high',
                    'severity': 'medium',
                    'category': 'infrastructure',
                    'resource_type': 'cloud_sql'
                }
            ]
            
            alerts = []
            for alert_data in gcp_alerts:
                alert = AlertData(
                    alert_id=f"gcp-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=alert_data['title'],
                    description=alert_data['description'],
                    severity=alert_data['severity'],
                    category=alert_data['category'],
                    provider='gcp',
                    resource_id=f"gcp-{alert_data['resource_type']}-{len(alerts)}",
                    resource_name=f"{alert_data['resource_type']}-{len(alerts)}",
                    region='us-central1',
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(minutes=20),
                    labels={'resource_type': alert_data['resource_type']},
                    annotations={'monitoring_service': 'cloud-monitoring'},
                    metadata={'memory_usage': 92.1, 'connection_count': 85}
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Cloud Monitoring alerts: {e}")
            return []
    
    def _get_gcp_logging_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Cloud Logging alerts"""
        try:
            alert = AlertData(
                alert_id=f"gcp-logging-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                title='Application Exception Detected',
                description='Application exceptions detected in Cloud Logging',
                severity='medium',
                category='application',
                resource_id='gcp-logging-project',
                resource_name='gcp-project',
                region='us-central1',
                environment='production',
                created_at=datetime.utcnow() - timedelta(minutes=10),
                labels={'log_name': 'application-errors'},
                annotations={'logging_service': 'cloud-logging'},
                metadata={'exception_count': 25, 'time_window_minutes': 10}
            )
            return [alert]
            
        except Exception as e:
            logger.error(f"Failed to get Cloud Logging alerts: {e}")
            return []
    
    def _send_gcp_email(self, recipients: List[str], alert: AlertData) -> bool:
        """Send email via GCP"""
        try:
            # In real implementation, this would use Google Workspace API or SendGrid
            logger.info(f"Sending GCP email to {len(recipients)} recipients: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send GCP email: {e}")
            return False
    
    def _send_gcp_webhook(self, recipients: List[str], alert: AlertData) -> bool:
        """Send webhook via GCP"""
        try:
            # In real implementation, this would use Cloud Functions or Pub/Sub
            logger.info(f"Sending GCP webhook: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send GCP webhook: {e}")
            return False

class OnPremAlertRoutingHandler(AlertRoutingHandler):
    """On-premise alert routing operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use Prometheus, Grafana, or custom systems
            logger.info("On-premise alert routing handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_alerts_for_routing(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from on-premise monitoring systems"""
        try:
            alerts = []
            
            # Simulate on-premise alerts
            onprem_alerts = [
                {
                    'title': 'Server Disk Space Low',
                    'description': 'Server disk space is below threshold',
                    'severity': 'high',
                    'category': 'infrastructure',
                    'source': 'prometheus'
                },
                {
                    'title': 'Database Connection Pool Exhausted',
                    'description': 'Database connection pool is exhausted',
                    'severity': 'critical',
                    'category': 'infrastructure',
                    'source': 'custom-monitoring'
                }
            ]
            
            for alert_data in onprem_alerts:
                alert = AlertData(
                    alert_id=f"onprem-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=alert_data['title'],
                    description=alert_data['description'],
                    severity=alert_data['severity'],
                    category=alert_data['category'],
                    provider='onprem',
                    resource_id=f"onprem-server-{len(alerts)}",
                    resource_name=f"server-{len(alerts)}",
                    region='onprem',
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(minutes=15),
                    labels={'datacenter': 'dc1', 'rack': 'rack1'},
                    annotations={'monitoring_system': alert_data['source']},
                    metadata={'disk_usage': 88.5, 'connection_pool_usage': 100.0}
                )
                alerts.append(alert)
            
            logger.info(f"Retrieved {len(alerts)} on-premise alerts for routing")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get on-premise alerts for routing: {e}")
            return []
    
    def send_notification(self, channel_type: str, recipients: List[str], alert: AlertData) -> bool:
        """Send notification through on-premise systems"""
        try:
            if channel_type == 'email':
                return self._send_onprem_email(recipients, alert)
            elif channel_type == 'slack':
                return self._send_onprem_slack(recipients, alert)
            elif channel_type == 'webhook':
                return self._send_onprem_webhook(recipients, alert)
            else:
                logger.warning(f"Unsupported channel type for on-premise: {channel_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send on-premise notification: {e}")
            return False
    
    def _send_onprem_email(self, recipients: List[str], alert: AlertData) -> bool:
        """Send email via on-premise SMTP"""
        try:
            logger.info(f"Sending on-premise email to {len(recipients)} recipients: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send on-premise email: {e}")
            return False
    
    def _send_onprem_slack(self, recipients: List[str], alert: AlertData) -> bool:
        """Send Slack via on-premise integration"""
        try:
            logger.info(f"Sending on-premise Slack: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send on-premise Slack: {e}")
            return False
    
    def _send_onprem_webhook(self, recipients: List[str], alert: AlertData) -> bool:
        """Send webhook via on-premise system"""
        try:
            logger.info(f"Sending on-premise webhook: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send on-preme webhook: {e}")
            return False

def get_alert_routing_handler(provider: str, region: str = "us-west-2") -> AlertRoutingHandler:
    """Get appropriate alert routing handler"""
    handlers = {
        'aws': AWSAlertRoutingHandler,
        'azure': AzureAlertRoutingHandler,
        'gcp': GCPAlertRoutingHandler,
        'onprem': OnPremAlertRoutingHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
