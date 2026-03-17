#!/usr/bin/env python3
"""
Incident Predictor Handler

Cloud-specific operations handler for incident prediction across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IncidentData:
    incident_id: str
    title: str
    description: str
    severity: str
    category: str
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    created_at: datetime
    resolved_at: Optional[datetime]
    duration_minutes: int
    impact_score: float
    affected_services: List[str]
    root_cause: Optional[str]
    resolution: Optional[str]
    metrics: Dict[str, Any]

class IncidentHandler(ABC):
    """Abstract base class for cloud-specific incident operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_historical_incidents(self, days_back: int) -> List[IncidentData]:
        """Get historical incidents"""
        pass
    
    @abstractmethod
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        pass
    
    @abstractmethod
    def get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts"""
        pass

class AWSIncidentHandler(IncidentHandler):
    """AWS-specific incident operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'logs': boto3.client('logs', region_name=self.region),
                'support': boto3.client('support', region_name=self.region),
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
    
    def get_historical_incidents(self, days_back: int) -> List[IncidentData]:
        """Get historical incidents from AWS"""
        try:
            incidents = []
            
            # Get AWS Health events
            health_events = self._get_aws_health_events(days_back)
            incidents.extend(health_events)
            
            # Get CloudWatch alarm incidents
            alarm_incidents = self._get_cloudwatch_alarm_incidents(days_back)
            incidents.extend(alarm_incidents)
            
            # Get support cases
            support_cases = self._get_support_cases(days_back)
            incidents.extend(support_cases)
            
            logger.info(f"Retrieved {len(incidents)} AWS incidents")
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get AWS historical incidents: {e}")
            return []
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current AWS system metrics"""
        try:
            metrics = {}
            
            # Get CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=15)
            
            # CPU utilization
            cpu_response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if cpu_response['Datapoints']:
                metrics['cpu_utilization'] = cpu_response['Datapoints'][-1]['Average']
            else:
                metrics['cpu_utilization'] = 45.0
            
            # Memory utilization (simplified)
            metrics['memory_utilization'] = 60.0
            
            # Error rate (simplified)
            metrics['error_rate'] = 2.5
            
            # Response time (simplified)
            metrics['response_time'] = 120.0
            
            # Network traffic (simplified)
            metrics['network_in'] = 1000000.0
            metrics['network_out'] = 800000.0
            
            # Disk utilization (simplified)
            metrics['disk_utilization'] = 35.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get AWS metrics: {e}")
            return {}
    
    def get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current AWS alerts"""
        try:
            alerts = []
            
            # Get CloudWatch alarms in ALARM state
            alarms_response = self.client['cloudwatch'].describe_alarms(StateValue='ALARM')
            
            for alarm in alarms_response['MetricAlarms']:
                alert = {
                    'alert_id': alarm['AlarmName'],
                    'title': alarm['AlarmName'],
                    'description': alarm.get('AlarmDescription', ''),
                    'severity': self._map_alarm_severity(alarm),
                    'category': self._categorize_alarm(alarm),
                    'resource_id': self._extract_resource_id(alarm),
                    'resource_name': self._extract_resource_name(alarm),
                    'created_at': alarm['AlarmConfigurationUpdatedTimestamp'].isoformat(),
                    'metrics': {
                        'threshold': alarm.get('Threshold'),
                        'statistic': alarm.get('Statistic'),
                        'period': alarm.get('Period'),
                        'evaluation_periods': alarm.get('EvaluationPeriods')
                    }
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get AWS alerts: {e}")
            return []
    
    def _get_aws_health_events(self, days_back: int) -> List[IncidentData]:
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
                    'event_type': 'issue',
                    'duration_hours': 4
                },
                {
                    'title': 'RDS Database Connection Issues',
                    'description': 'RDS database experiencing connection issues',
                    'severity': 'critical',
                    'category': 'database',
                    'service': 'RDS',
                    'event_type': 'issue',
                    'duration_hours': 2
                },
                {
                    'title': 'S3 Service Degradation',
                    'description': 'S3 service experiencing elevated error rates',
                    'severity': 'medium',
                    'category': 'infrastructure',
                    'service': 'S3',
                    'event_type': 'issue',
                    'duration_hours': 1
                }
            ]
            
            incidents = []
            for event in health_events:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(hours=event['duration_hours'])
                
                incident = IncidentData(
                    incident_id=f"health-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=event['title'],
                    description=event['description'],
                    severity=event['severity'],
                    category=event['category'],
                    provider='aws',
                    resource_id='aws-health-event',
                    resource_name='aws-health',
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=event['duration_hours'] * 60,
                    impact_score=self._calculate_impact_score(event['severity']),
                    affected_services=[event['service']],
                    root_cause='AWS service issue',
                    resolution='AWS resolved the underlying issue',
                    metrics={
                        'affected_resources': random.randint(1, 10),
                        'impact_score': self._calculate_impact_score(event['severity'])
                    }
                )
                incidents.append(incident)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get AWS Health events: {e}")
            return []
    
    def _get_cloudwatch_alarm_incidents(self, days_back: int) -> List[IncidentData]:
        """Get CloudWatch alarm incidents"""
        try:
            # Simplified CloudWatch alarm incidents
            alarm_incidents = [
                {
                    'title': 'High CPU Utilization',
                    'description': 'EC2 instance CPU utilization exceeded threshold',
                    'severity': 'medium',
                    'category': 'performance',
                    'resource_type': 'EC2',
                    'duration_minutes': 30
                },
                {
                    'title': 'Low Memory Available',
                    'description': 'System memory usage is critically high',
                    'severity': 'high',
                    'category': 'infrastructure',
                    'resource_type': 'EC2',
                    'duration_minutes': 45
                }
            ]
            
            incidents = []
            for alarm in alarm_incidents:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(minutes=alarm['duration_minutes'])
                
                incident = IncidentData(
                    incident_id=f"alarm-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=alarm['title'],
                    description=alarm['description'],
                    severity=alarm['severity'],
                    category=alarm['category'],
                    provider='aws',
                    resource_id=f"{alarm['resource_type']}-instance",
                    resource_name=f"{alarm['resource_type']}-instance",
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=alarm['duration_minutes'],
                    impact_score=self._calculate_impact_score(alarm['severity']),
                    affected_services=[alarm['resource_type']],
                    root_cause='Resource utilization exceeded threshold',
                    resolution='Resource scaled or optimized',
                    metrics={
                        'threshold_exceeded': True,
                        'peak_utilization': random.uniform(80, 95)
                    }
                )
                incidents.append(incident)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get CloudWatch alarm incidents: {e}")
            return []
    
    def _get_support_cases(self, days_back: int) -> List[IncidentData]:
        """Get AWS support cases"""
        try:
            # Simplified AWS support cases
            support_cases = [
                {
                    'title': 'VPC Connectivity Issues',
                    'description': 'Inter-VPC connectivity problems',
                    'severity': 'high',
                    'category': 'networking',
                    'duration_hours': 6
                },
                {
                    'title': 'IAM Policy Conflicts',
                    'description': 'IAM policies causing access issues',
                    'severity': 'medium',
                    'category': 'security',
                    'duration_hours': 3
                }
            ]
            
            incidents = []
            for case in support_cases:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(hours=case['duration_hours'])
                
                incident = IncidentData(
                    incident_id=f"support-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=case['title'],
                    description=case['description'],
                    severity=case['severity'],
                    category=case['category'],
                    provider='aws',
                    resource_id='aws-support-case',
                    resource_name='aws-support',
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=case['duration_hours'] * 60,
                    impact_score=self._calculate_impact_score(case['severity']),
                    affected_services=['Support'],
                    root_cause='Configuration issue',
                    resolution='AWS Support provided solution',
                    metrics={
                        'case_id': f"case-{random.randint(100000, 999999)}",
                        'response_time_hours': random.uniform(1, 4)
                    }
                )
                incidents.append(incident)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get AWS support cases: {e}")
            return []
    
    def _map_alarm_severity(self, alarm: Dict[str, Any]) -> str:
        """Map CloudWatch alarm to severity"""
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
    
    def _categorize_alarm(self, alarm: Dict[str, Any]) -> str:
        """Categorize alarm based on namespace"""
        namespace = alarm.get('Namespace', '')
        
        if 'EC2' in namespace:
            return 'infrastructure'
        elif 'RDS' in namespace:
            return 'database'
        elif 'Lambda' in namespace:
            return 'application'
        elif 'ELB' in namespace:
            return 'networking'
        elif 'Billing' in namespace:
            return 'cost'
        else:
            return 'application'
    
    def _extract_resource_id(self, alarm: Dict[str, Any]) -> str:
        """Extract resource ID from alarm"""
        dimensions = alarm.get('Dimensions', [])
        for dimension in dimensions:
            if dimension['Name'] in ['InstanceId', 'DBInstanceIdentifier', 'FunctionName']:
                return dimension['Value']
        return 'unknown'
    
    def _extract_resource_name(self, alarm: Dict[str, Any]) -> str:
        """Extract resource name from alarm"""
        return self._extract_resource_id(alarm)
    
    def _calculate_impact_score(self, severity: str) -> float:
        """Calculate impact score based on severity"""
        impact_mapping = {
            'critical': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        }
        return impact_mapping.get(severity, 0.5)

class AzureIncidentHandler(IncidentHandler):
    """Azure-specific incident operations"""
    
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
    
    def get_historical_incidents(self, days_back: int) -> List[IncidentData]:
        """Get historical incidents from Azure"""
        try:
            incidents = []
            
            # Get Azure Service Health incidents
            service_health = self._get_azure_service_health(days_back)
            incidents.extend(service_health)
            
            # Get Azure Monitor alerts
            monitor_alerts = self._get_azure_monitor_incidents(days_back)
            incidents.extend(monitor_alerts)
            
            logger.info(f"Retrieved {len(incidents)} Azure incidents")
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get Azure historical incidents: {e}")
            return []
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current Azure system metrics"""
        try:
            # Simplified Azure metrics
            return {
                'cpu_utilization': 55.0,
                'memory_utilization': 65.0,
                'error_rate': 3.2,
                'response_time': 150.0,
                'network_in': 1200000.0,
                'network_out': 900000.0,
                'disk_utilization': 40.0
            }
        except Exception as e:
            logger.error(f"Failed to get Azure metrics: {e}")
            return {}
    
    def get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current Azure alerts"""
        try:
            # Simplified Azure alerts
            return [
                {
                    'alert_id': 'azure-vm-cpu-high',
                    'title': 'VM CPU High Utilization',
                    'description': 'Virtual machine CPU utilization is above threshold',
                    'severity': 'high',
                    'category': 'performance',
                    'resource_id': 'azure-vm-001',
                    'resource_name': 'web-server-01',
                    'created_at': datetime.utcnow().isoformat(),
                    'metrics': {'cpu_utilization': 85.0}
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get Azure alerts: {e}")
            return []
    
    def _get_azure_service_health(self, days_back: int) -> List[IncidentData]:
        """Get Azure Service Health incidents"""
        try:
            # Simplified Azure Service Health incidents
            service_health = [
                {
                    'title': 'Azure VM Scale Set Performance Issues',
                    'description': 'VM scale set experiencing performance degradation',
                    'severity': 'high',
                    'category': 'infrastructure',
                    'service': 'Virtual Machines',
                    'duration_hours': 3
                },
                {
                    'title': 'Azure SQL Database Connectivity',
                    'description': 'SQL database experiencing connection issues',
                    'severity': 'medium',
                    'category': 'database',
                    'service': 'SQL Database',
                    'duration_hours': 2
                }
            ]
            
            incidents = []
            for event in service_health:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(hours=event['duration_hours'])
                
                incident = IncidentData(
                    incident_id=f"azure-health-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=event['title'],
                    description=event['description'],
                    severity=event['severity'],
                    category=event['category'],
                    provider='azure',
                    resource_id='azure-service-health',
                    resource_name='azure-service-health',
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=event['duration_hours'] * 60,
                    impact_score=self._calculate_impact_score(event['severity']),
                    affected_services=[event['service']],
                    root_cause='Azure service issue',
                    resolution='Azure resolved the service issue',
                    metrics={'affected_resources': random.randint(1, 5)}
                )
                incidents.append(incident)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get Azure Service Health: {e}")
            return []
    
    def _get_azure_monitor_incidents(self, days_back: int) -> List[IncidentData]:
        """Get Azure Monitor incidents"""
        try:
            # Simplified Azure Monitor incidents
            monitor_incidents = [
                {
                    'title': 'App Service Response Time High',
                    'description': 'App service response time exceeding SLA',
                    'severity': 'medium',
                    'category': 'performance',
                    'resource_type': 'App Service',
                    'duration_minutes': 25
                }
            ]
            
            incidents = []
            for incident in monitor_incidents:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(minutes=incident['duration_minutes'])
                
                incident_data = IncidentData(
                    incident_id=f"azure-monitor-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=incident['title'],
                    description=incident['description'],
                    severity=incident['severity'],
                    category=incident['category'],
                    provider='azure',
                    resource_id='azure-app-service',
                    resource_name='web-app-01',
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=incident['duration_minutes'],
                    impact_score=self._calculate_impact_score(incident['severity']),
                    affected_services=[incident['resource_type']],
                    root_cause='Performance bottleneck',
                    resolution='Application optimized',
                    metrics={'response_time_ms': 450}
                )
                incidents.append(incident_data)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get Azure Monitor incidents: {e}")
            return []
    
    def _calculate_impact_score(self, severity: str) -> float:
        """Calculate impact score based on severity"""
        impact_mapping = {
            'critical': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        }
        return impact_mapping.get(severity, 0.5)

class GCPIncidentHandler(IncidentHandler):
    """GCP-specific incident operations"""
    
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
    
    def get_historical_incidents(self, days_back: int) -> List[IncidentData]:
        """Get historical incidents from GCP"""
        try:
            incidents = []
            
            # Get Cloud Monitoring incidents
            monitoring_incidents = self._get_gcp_monitoring_incidents(days_back)
            incidents.extend(monitoring_incidents)
            
            # Get Cloud Logging incidents
            logging_incidents = self._get_gcp_logging_incidents(days_back)
            incidents.extend(logging_incidents)
            
            logger.info(f"Retrieved {len(incidents)} GCP incidents")
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get GCP historical incidents: {e}")
            return []
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current GCP system metrics"""
        try:
            # Simplified GCP metrics
            return {
                'cpu_utilization': 48.0,
                'memory_utilization': 58.0,
                'error_rate': 2.8,
                'response_time': 110.0,
                'network_in': 900000.0,
                'network_out': 700000.0,
                'disk_utilization': 32.0
            }
        except Exception as e:
            logger.error(f"Failed to get GCP metrics: {e}")
            return {}
    
    def get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current GCP alerts"""
        try:
            # Simplified GCP alerts
            return [
                {
                    'alert_id': 'gcp-gce-memory-high',
                    'title': 'GCE Instance Memory High',
                    'description': 'GCE instance memory usage is above threshold',
                    'severity': 'medium',
                    'category': 'infrastructure',
                    'resource_id': 'gce-instance-001',
                    'resource_name': 'app-server-01',
                    'created_at': datetime.utcnow().isoformat(),
                    'metrics': {'memory_usage': 88.0}
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get GCP alerts: {e}")
            return []
    
    def _get_gcp_monitoring_incidents(self, days_back: int) -> List[IncidentData]:
        """Get GCP Cloud Monitoring incidents"""
        try:
            # Simplified GCP Cloud Monitoring incidents
            monitoring_incidents = [
                {
                    'title': 'GCE Instance Memory Usage High',
                    'description': 'GCE instance memory usage exceeded threshold',
                    'severity': 'medium',
                    'category': 'infrastructure',
                    'service': 'Compute Engine',
                    'duration_minutes': 35
                },
                {
                    'title': 'Cloud SQL Database Slow Queries',
                    'description': 'Cloud SQL database experiencing slow query performance',
                    'severity': 'high',
                    'category': 'database',
                    'service': 'Cloud SQL',
                    'duration_minutes': 50
                }
            ]
            
            incidents = []
            for incident in monitoring_incidents:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(minutes=incident['duration_minutes'])
                
                incident_data = IncidentData(
                    incident_id=f"gcp-monitoring-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=incident['title'],
                    description=incident['description'],
                    severity=incident['severity'],
                    category=incident['category'],
                    provider='gcp',
                    resource_id='gcp-monitoring',
                    resource_name='gcp-monitoring',
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=incident['duration_minutes'],
                    impact_score=self._calculate_impact_score(incident['severity']),
                    affected_services=[incident['service']],
                    root_cause='Resource utilization issue',
                    resolution='Resource optimized or scaled',
                    metrics={'peak_memory_usage': 92.0}
                )
                incidents.append(incident_data)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get GCP Cloud Monitoring incidents: {e}")
            return []
    
    def _get_gcp_logging_incidents(self, days_back: int) -> List[IncidentData]:
        """Get GCP Cloud Logging incidents"""
        try:
            # Simplified GCP Cloud Logging incidents
            logging_incidents = [
                {
                    'title': 'Application Error Spike',
                    'description': 'Significant increase in application errors detected',
                    'severity': 'high',
                    'category': 'application',
                    'service': 'Cloud Logging',
                    'duration_minutes': 20
                }
            ]
            
            incidents = []
            for incident in logging_incidents:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(minutes=incident['duration_minutes'])
                
                incident_data = IncidentData(
                    incident_id=f"gcp-logging-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=incident['title'],
                    description=incident['description'],
                    severity=incident['severity'],
                    category=incident['category'],
                    provider='gcp',
                    resource_id='gcp-logging',
                    resource_name='gcp-logging',
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=incident['duration_minutes'],
                    impact_score=self._calculate_impact_score(incident['severity']),
                    affected_services=[incident['service']],
                    root_cause='Application bug or configuration issue',
                    resolution='Application fix deployed',
                    metrics={'error_count': 150}
                )
                incidents.append(incident_data)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get GCP Cloud Logging incidents: {e}")
            return []
    
    def _calculate_impact_score(self, severity: str) -> float:
        """Calculate impact score based on severity"""
        impact_mapping = {
            'critical': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        }
        return impact_mapping.get(severity, 0.5)

class OnPremIncidentHandler(IncidentHandler):
    """On-premise incident operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use custom monitoring systems
            logger.info("On-premise incident handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_historical_incidents(self, days_back: int) -> List[IncidentData]:
        """Get historical incidents from on-premise systems"""
        try:
            # Simplified on-premise incidents
            onprem_incidents = [
                {
                    'title': 'Server Disk Space Low',
                    'description': 'Server disk space is critically low',
                    'severity': 'high',
                    'category': 'infrastructure',
                    'source': 'Prometheus',
                    'duration_minutes': 40
                },
                {
                    'title': 'Database Connection Pool Exhausted',
                    'description': 'Database connection pool is exhausted',
                    'severity': 'critical',
                    'category': 'database',
                    'source': 'Custom Monitoring',
                    'duration_minutes': 60
                },
                {
                    'title': 'Network Switch Failure',
                    'description': 'Network switch experiencing hardware failure',
                    'severity': 'critical',
                    'category': 'networking',
                    'source': 'SNMP Monitoring',
                    'duration_minutes': 120
                }
            ]
            
            incidents = []
            for incident in onprem_incidents:
                created_at = datetime.utcnow() - timedelta(days=random.randint(1, days_back))
                resolved_at = created_at + timedelta(minutes=incident['duration_minutes'])
                
                incident_data = IncidentData(
                    incident_id=f"onprem-{created_at.strftime('%Y%m%d%H%M%S')}",
                    title=incident['title'],
                    description=incident['description'],
                    severity=incident['severity'],
                    category=incident['category'],
                    provider='onprem',
                    resource_id='onprem-server',
                    resource_name='onprem-server',
                    environment='production',
                    created_at=created_at,
                    resolved_at=resolved_at,
                    duration_minutes=incident['duration_minutes'],
                    impact_score=self._calculate_impact_score(incident['severity']),
                    affected_services=[incident['source']],
                    root_cause='Hardware or configuration issue',
                    resolution='Hardware replaced or configuration updated',
                    metrics={'affected_users': random.randint(10, 100)}
                )
                incidents.append(incident_data)
            
            logger.info(f"Retrieved {len(incidents)} on-premise incidents")
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get on-premise historical incidents: {e}")
            return []
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current on-premise system metrics"""
        try:
            # Simplified on-premise metrics
            return {
                'cpu_utilization': 52.0,
                'memory_utilization': 62.0,
                'error_rate': 4.1,
                'response_time': 180.0,
                'network_in': 800000.0,
                'network_out': 600000.0,
                'disk_utilization': 75.0
            }
        except Exception as e:
            logger.error(f"Failed to get on-premise metrics: {e}")
            return {}
    
    def get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current on-premise alerts"""
        try:
            # Simplified on-premise alerts
            return [
                {
                    'alert_id': 'onprem-disk-low',
                    'title': 'Disk Space Low',
                    'description': 'Server disk space is below threshold',
                    'severity': 'medium',
                    'category': 'infrastructure',
                    'resource_id': 'server-01',
                    'resource_name=': 'server-01',
                    'created_at': datetime.utcnow().isoformat(),
                    'metrics': {'disk_usage': 88.5}
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get on-premise alerts: {e}")
            return []
    
    def _calculate_impact_score(self, severity: str) -> float:
        """Calculate impact score based on severity"""
        impact_mapping = {
            'critical': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        }
        return impact_mapping.get(severity, 0.5)

def get_incident_handler(provider: str, region: str = "us-west-2") -> IncidentHandler:
    """Get appropriate incident handler"""
    handlers = {
        'aws': AWSIncidentHandler,
        'azure': AzureIncidentHandler,
        'gcp': GCPIncidentHandler,
        'onprem': OnPremIncidentHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)

# Import random for simulation
import random
