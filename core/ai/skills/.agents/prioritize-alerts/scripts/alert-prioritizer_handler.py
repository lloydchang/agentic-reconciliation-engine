#!/usr/bin/env python3
"""
Alert Prioritizer Handler

Cloud-specific operations handler for alert prioritization across multi-cloud environments.
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
    resource_id: str
    resource_name: str
    region: str
    environment: str
    created_at: datetime
    updated_at: datetime
    status: str
    source: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    metrics: Dict[str, Any]

class AlertHandler(ABC):
    """Abstract base class for cloud-specific alert operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from cloud provider"""
        pass

class AWSAlertHandler(AlertHandler):
    """AWS-specific alert operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'ses': boto3.client('ses', region_name=self.region),
                'sns': boto3.client('sns', region_name=self.region),
                'logs': boto3.client('logs', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def get_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from AWS CloudWatch"""
        try:
            alerts = []
            
            # Get CloudWatch alarms
            alarms = self._get_cloudwatch_alarms(time_range_hours)
            alerts.extend(alarms)
            
            # Get CloudWatch Logs insights alerts
            logs_alerts = self._get_logs_insights_alerts(time_range_hours)
            alerts.extend(logs_alerts)
            
            # Get AWS Health events
            health_alerts = self._get_health_events(time_range_hours)
            alerts.extend(health_alerts)
            
            logger.info(f"Retrieved {len(alerts)} alerts from AWS")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get AWS alerts: {e}")
            return []
    
    def _get_cloudwatch_alarms(self, time_range_hours: int) -> List[AlertData]:
        """Get CloudWatch alarms"""
        try:
            response = self.client['cloudwatch'].describe_alarms()
            
            alerts = []
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            for alarm in response['MetricAlarms']:
                if alarm['StateValue'] in ['ALARM', 'INSUFFICIENT_DATA']:
                    # Check if alarm was updated within time range
                    if alarm['StateUpdatedTimestamp'] >= cutoff_time:
                        alert = AlertData(
                            alert_id=alarm['AlarmName'],
                            title=alarm['AlarmName'],
                            description=alarm['AlarmDescription'] or f"Alarm for {alarm['MetricName']}",
                            severity=self._map_alarm_severity(alarm['StateValue']),
                            category=self._categorize_metric(alarm['Namespace']),
                            resource_id=alarm.get('Dimensions', [{}])[0].get('Value', 'unknown'),
                            resource_name=alarm.get('Dimensions', [{}])[0].get('Value', 'unknown'),
                            region=self.region,
                            environment=self._extract_environment(alarm),
                            created_at=alarm['AlarmConfigurationUpdatedTimestamp'],
                            updated_at=alarm['StateUpdatedTimestamp'],
                            status='open' if alarm['StateValue'] == 'ALARM' else 'acknowledged',
                            source='aws-cloudwatch',
                            labels=self._extract_alarm_labels(alarm),
                            annotations={'metric_name': alarm['MetricName'], 'namespace': alarm['Namespace']},
                            metrics={
                                'threshold': alarm.get('Threshold'),
                                'period': alarm.get('Period'),
                                'evaluation_periods': alarm.get('EvaluationPeriods'),
                                'statistic': alarm.get('Statistic')
                            }
                        )
                        alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get CloudWatch alarms: {e}")
            return []
    
    def _get_logs_insights_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get CloudWatch Logs insights alerts"""
        try:
            # Simplified logs insights alert collection
            # In real implementation, this would query CloudWatch Logs Insights
            
            alerts = []
            
            # Example error pattern alerts
            error_patterns = [
                {'pattern': 'ERROR', 'severity': 'high'},
                {'pattern': 'CRITICAL', 'severity': 'critical'},
                {'pattern': 'TIMEOUT', 'severity': 'medium'}
            ]
            
            for pattern in error_patterns:
                # Simulate finding error logs
                alert = AlertData(
                    alert_id=f"logs-{pattern['pattern'].lower()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title=f"High {pattern['pattern']} Rate Detected",
                    description=f"Increased {pattern['pattern']} messages detected in application logs",
                    severity=pattern['severity'],
                    category='application',
                    resource_id='log-group/application-logs',
                    resource_name='application-logs',
                    region=self.region,
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(minutes=30),
                    updated_at=datetime.utcnow(),
                    status='open',
                    source='aws-cloudwatch-logs',
                    labels={'pattern': pattern['pattern'], 'log_group': 'application-logs'},
                    annotations={'detection_method': 'pattern-matching'},
                    metrics={'error_rate': 15.5, 'time_window_minutes': 30}
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get logs insights alerts: {e}")
            return []
    
    def _get_health_events(self, time_range_hours: int) -> List[AlertData]:
        """Get AWS Health events"""
        try:
            # Simplified AWS Health events
            # In real implementation, this would use AWS Health API
            
            alerts = []
            
            # Example health events
            health_events = [
                {
                    'title': 'EC2 Instance Degraded Performance',
                    'description': 'EC2 instance is experiencing degraded performance',
                    'severity': 'high',
                    'category': 'infrastructure'
                },
                {
                    'title': 'RDS Database Connection Issues',
                    'description': 'RDS database experiencing connection issues',
                    'severity': 'critical',
                    'category': 'infrastructure'
                }
            ]
            
            for event in health_events:
                alert = AlertData(
                    alert_id=f"health-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=event['title'],
                    description=event['description'],
                    severity=event['severity'],
                    category=event['category'],
                    resource_id='aws-health-event',
                    resource_name='aws-health',
                    region=self.region,
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(hours=2),
                    updated_at=datetime.utcnow(),
                    status='open',
                    source='aws-health',
                    labels={'event_type': 'issue', 'service': 'aws'},
                    annotations={'health_event_id': f"event-{len(alerts)}"},
                    metrics={'affected_resources': 1, 'impact_score': 0.8}
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get health events: {e}")
            return []
    
    def _map_alarm_severity(self, state_value: str) -> str:
        """Map CloudWatch alarm state to severity"""
        if state_value == 'ALARM':
            return 'high'
        elif state_value == 'INSUFFICIENT_DATA':
            return 'medium'
        else:
            return 'low'
    
    def _categorize_metric(self, namespace: str) -> str:
        """Categorize CloudWatch metric namespace"""
        category_mapping = {
            'AWS/EC2': 'infrastructure',
            'AWS/RDS': 'infrastructure',
            'AWS/ECS': 'infrastructure',
            'AWS/Lambda': 'application',
            'AWS/ApplicationELB': 'availability',
            'AWS/NetworkELB': 'networking',
            'AWS/S3': 'storage',
            'AWS/Billing': 'cost'
        }
        return category_mapping.get(namespace, 'application')
    
    def _extract_environment(self, alarm: Dict[str, Any]) -> str:
        """Extract environment from alarm configuration"""
        # Check tags for environment
        tags = alarm.get('Tags', [])
        for tag in tags:
            if tag['Key'].lower() == 'environment':
                return tag['Value']
        
        # Check alarm name for environment indicators
        name = alarm['AlarmName'].lower()
        if 'prod' in name or 'production' in name:
            return 'production'
        elif 'staging' in name:
            return 'staging'
        elif 'dev' in name or 'development' in name:
            return 'development'
        else:
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

class AzureAlertHandler(AlertHandler):
    """Azure-specific alert operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.monitor import MonitorManagementClient
            from azure.mgmt.resource import ResourceManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'monitor': MonitorManagementClient(credential, "<subscription-id>"),
                'resource': ResourceManagementClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def get_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from Azure Monitor"""
        try:
            alerts = []
            
            # Get Azure Monitor alerts
            monitor_alerts = self._get_monitor_alerts(time_range_hours)
            alerts.extend(monitor_alerts)
            
            # Get Log Analytics alerts
            log_analytics_alerts = self._get_log_analytics_alerts(time_range_hours)
            alerts.extend(log_analytics_alerts)
            
            logger.info(f"Retrieved {len(alerts)} alerts from Azure")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Azure alerts: {e}")
            return []
    
    def _get_monitor_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Azure Monitor alerts"""
        try:
            # Simplified Azure Monitor alert collection
            alerts = []
            
            # Example Azure alerts
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
            
            for alert_data in azure_alerts:
                alert = AlertData(
                    alert_id=f"azure-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=alert_data['title'],
                    description=alert_data['description'],
                    severity=alert_data['severity'],
                    category=alert_data['category'],
                    resource_id=f"azure-{alert_data['resource_type']}-{len(alerts)}",
                    resource_name=f"{alert_data['resource_type']}-{len(alerts)}",
                    region='eastus',
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(hours=1),
                    updated_at=datetime.utcnow(),
                    status='open',
                    source='azure-monitor',
                    labels={'resource_type': alert_data['resource_type']},
                    annotations={'monitoring_service': 'azure-monitor'},
                    metrics={'cpu_utilization': 85.2, 'response_time': 450}
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Azure Monitor alerts: {e}")
            return []
    
    def _get_log_analytics_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Log Analytics alerts"""
        try:
            # Simplified Log Analytics alert collection
            alerts = []
            
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
                updated_at=datetime.utcnow(),
                status='open',
                source='azure-log-analytics',
                labels={'workspace': 'production-workspace'},
                annotations={'query_type': 'log-analytics'},
                metrics={'error_rate': 12.3, 'time_window_minutes': 15}
            )
            alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Log Analytics alerts: {e}")
            return []

class GCPAlertHandler(AlertHandler):
    """GCP-specific alert operations"""
    
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
    
    def get_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from GCP"""
        try:
            alerts = []
            
            # Get Cloud Monitoring alerts
            monitoring_alerts = self._get_monitoring_alerts(time_range_hours)
            alerts.extend(monitoring_alerts)
            
            # Get Cloud Logging alerts
            logging_alerts = self._get_logging_alerts(time_range_hours)
            alerts.extend(logging_alerts)
            
            logger.info(f"Retrieved {len(alerts)} alerts from GCP")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get GCP alerts: {e}")
            return []
    
    def _get_monitoring_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Cloud Monitoring alerts"""
        try:
            # Simplified Cloud Monitoring alert collection
            alerts = []
            
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
            
            for alert_data in gcp_alerts:
                alert = AlertData(
                    alert_id=f"gcp-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=alert_data['title'],
                    description=alert_data['description'],
                    severity=alert_data['severity'],
                    category=alert_data['category'],
                    resource_id=f"gcp-{alert_data['resource_type']}-{len(alerts)}",
                    resource_name=f"{alert_data['resource_type']}-{len(alerts)}",
                    region='us-central1',
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(minutes=20),
                    updated_at=datetime.utcnow(),
                    status='open',
                    source='gcp-monitoring',
                    labels={'resource_type': alert_data['resource_type']},
                    annotations={'monitoring_service': 'cloud-monitoring'},
                    metrics={'memory_usage': 92.1, 'connection_count': 85}
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Cloud Monitoring alerts: {e}")
            return []
    
    def _get_logging_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get Cloud Logging alerts"""
        try:
            # Simplified Cloud Logging alert collection
            alerts = []
            
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
                updated_at=datetime.utcnow(),
                status='open',
                source='gcp-logging',
                labels={'log_name': 'application-errors'},
                annotations={'logging_service': 'cloud-logging'},
                metrics={'exception_count': 25, 'time_window_minutes': 10}
            )
            alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get Cloud Logging alerts: {e}")
            return []

class OnPremAlertHandler(AlertHandler):
    """On-premise alert operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use Prometheus, Grafana, or custom monitoring systems
            logger.info("On-premise alert handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_alerts(self, time_range_hours: int) -> List[AlertData]:
        """Get alerts from on-premise monitoring systems"""
        try:
            alerts = []
            
            # Simulate on-premise alerts from various systems
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
                },
                {
                    'title': 'Network Latency High',
                    'description='Network latency between services is high',
                    'severity': 'medium',
                    'category': 'performance',
                    'source': 'grafana'
                }
            ]
            
            for alert_data in onprem_alerts:
                alert = AlertData(
                    alert_id=f"onprem-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(alerts)}",
                    title=alert_data['title'],
                    description=alert_data['description'],
                    severity=alert_data['severity'],
                    category=alert_data['category'],
                    resource_id=f"onprem-server-{len(alerts)}",
                    resource_name=f"server-{len(alerts)}",
                    region='onprem',
                    environment='production',
                    created_at=datetime.utcnow() - timedelta(minutes=15),
                    updated_at=datetime.utcnow(),
                    status='open',
                    source=alert_data['source'],
                    labels={'datacenter': 'dc1', 'rack': 'rack1'},
                    annotations={'monitoring_system': alert_data['source']},
                    metrics={'disk_usage': 88.5, 'connection_pool_usage': 100.0, 'network_latency': 250.0}
                )
                alerts.append(alert)
            
            logger.info(f"Retrieved {len(alerts)} alerts from on-premise systems")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get on-premise alerts: {e}")
            return []

def get_alert_handler(provider: str, region: str = "us-west-2") -> AlertHandler:
    """Get appropriate alert handler"""
    handlers = {
        'aws': AWSAlertHandler,
        'azure': AzureAlertHandler,
        'gcp': GCPAlertHandler,
        'onprem': OnPremAlertHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
