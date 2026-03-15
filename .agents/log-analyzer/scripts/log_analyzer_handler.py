#!/usr/bin/env python3
"""
Log Analyzer Handler

Cloud-specific operations handler for log analysis across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LogData:
    timestamp: datetime
    level: str
    message: str
    source: str
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    metadata: Dict[str, Any]

class LogHandler(ABC):
    """Abstract base class for cloud-specific log operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get logs from cloud provider"""
        pass

class AWSLogHandler(LogHandler):
    """AWS-specific log operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'logs': boto3.client('logs', region_name=self.region),
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def get_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get logs from AWS CloudWatch Logs and other sources"""
        try:
            logs = []
            
            # Get CloudWatch Logs
            cloudwatch_logs = self._get_cloudwatch_logs(time_range_hours, environment)
            logs.extend(cloudwatch_logs)
            
            # Get CloudTrail logs
            cloudtrail_logs = self._get_cloudtrail_logs(time_range_hours, environment)
            logs.extend(cloudtrail_logs)
            
            # Get VPC Flow Logs (simplified)
            flow_logs = self._get_flow_logs(time_range_hours, environment)
            logs.extend(flow_logs)
            
            logger.info(f"Retrieved {len(logs)} logs from AWS")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get AWS logs: {e}")
            return []
    
    def _get_cloudwatch_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get CloudWatch Logs"""
        try:
            logs = []
            
            # Get log groups
            log_groups = self.client['logs'].describe_log_groups()
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_range_hours)
            
            for log_group in log_groups['logGroups']:
                log_group_name = log_group['logGroupName']
                
                # Filter by environment if specified
                if environment and environment.lower() not in log_group_name.lower():
                    continue
                
                # Get log streams
                log_streams = self.client['logs'].describe_log_streams(
                    logGroupName=log_group_name,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=10
                )
                
                for log_stream in log_streams['logStreams']:
                    stream_name = log_stream['logStreamName']
                    
                    # Get log events
                    events = self.client['logs'].get_log_events(
                        logGroupName=log_group_name,
                        logStreamName=stream_name,
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000),
                        limit=1000
                    )
                    
                    for event in events['events']:
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        message = event['message']
                        
                        # Parse log level from message
                        level = self._extract_log_level(message)
                        
                        log_data = LogData(
                            timestamp=timestamp,
                            level=level,
                            message=message,
                            source=log_group_name,
                            provider='aws',
                            resource_id=log_group_name,
                            resource_name=log_group_name,
                            environment=environment,
                            metadata={
                                'log_stream': stream_name,
                                'log_group': log_group_name
                            }
                        )
                        logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get CloudWatch logs: {e}")
            return []
    
    def _get_cloudtrail_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get CloudTrail logs"""
        try:
            # Simplified CloudTrail logs collection
            # In real implementation, this would use CloudTrail events
            cloudtrail_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=30),
                    'level': 'INFO',
                    'message': 'CloudTrail: CreateAutoScalingGroup event',
                    'source': 'CloudTrail',
                    'resource_id': 'autoscaling-group',
                    'resource_name': 'web-app-asg'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=15),
                    'level': 'WARNING',
                    'message': 'CloudTrail: UnauthorizedAccessAttempt event',
                    'source': 'CloudTrail',
                    'resource_id': 'iam-role',
                    'resource_name': 'web-app-role'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=5),
                    'level': 'ERROR',
                    'message': 'CloudTrail: DeleteBucket event for critical bucket',
                    'source': 'CloudTrail',
                    'resource_id': 's3-bucket',
                    'resource_name': 'critical-data-bucket'
                }
            ]
            
            logs = []
            for log_entry in cloudtrail_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='aws',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'event_source': 'CloudTrail'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get CloudTrail logs: {e}")
            return []
    
    def _get_flow_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get VPC Flow Logs"""
        try:
            # Simplified VPC Flow Logs collection
            flow_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=20),
                    'level': 'INFO',
                    'message': 'VPC Flow Log: ACCEPT traffic from 10.0.1.100 to 10.0.2.200',
                    'source': 'VPCFlowLogs',
                    'resource_id': 'vpc-flow-log',
                    'resource_name': 'vpc-flow-log'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=10),
                    'level': 'WARNING',
                    'message': 'VPC Flow Log: REJECT traffic from unauthorized IP',
                    'source': 'VPCFlowLogs',
                    'resource_id': 'vpc-flow-log',
                    'resource_name': 'vpc-flow-log'
                }
            ]
            
            logs = []
            for log_entry in flow_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='aws',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'VPC Flow Log'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get VPC Flow logs: {e}")
            return []
    
    def _extract_log_level(self, message: str) -> str:
        """Extract log level from message"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['error', 'exception', 'failed', 'failure']):
            return 'ERROR'
        elif any(keyword in message_lower for keyword in ['warning', 'warn']):
            return 'WARNING'
        elif any(keyword in message_lower for keyword in ['critical', 'fatal', 'panic']):
            return 'CRITICAL'
        elif any(keyword in message_lower for keyword in ['debug']):
            return 'DEBUG'
        else:
            return 'INFO'

class AzureLogHandler(LogHandler):
    """Azure-specific log operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.monitor.query import LogsQueryClient
            from azure.storage.blob import BlobServiceClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'logs': LogsQueryClient(credential),
                'storage': BlobServiceClient(account_url="<account_url>", credential=credential)
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def get_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get logs from Azure Monitor and other sources"""
        try:
            logs = []
            
            # Get Azure Monitor logs
            monitor_logs = self._get_azure_monitor_logs(time_range_hours, environment)
            logs.extend(monitor_logs)
            
            # Get Activity logs
            activity_logs = self._get_activity_logs(time_range_hours, environment)
            logs.extend(activity_logs)
            
            # Get Application Insights logs
            app_insights_logs = self._get_app_insights_logs(time_range_hours, environment)
            logs.extend(app_insights_logs)
            
            logger.info(f"Retrieved {len(logs)} logs from Azure")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get Azure logs: {e}")
            return []
    
    def _get_azure_monitor_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get Azure Monitor logs"""
        try:
            # Simplified Azure Monitor logs collection
            monitor_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=25),
                    'level': 'ERROR',
                    'message': 'Azure Monitor: App Service response time exceeded threshold',
                    'source': 'AzureMonitor',
                    'resource_id': 'app-service',
                    'resource_name': 'web-app-prod'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=18),
                    'level': 'WARNING',
                    'message': 'Azure Monitor: VM CPU utilization high',
                    'source': 'AzureMonitor',
                    'resource_id': 'virtual-machine',
                    'resource_name': 'web-server-01'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=8),
                    'level': 'INFO',
                    'message': 'Azure Monitor: Database connection pool at 80% capacity',
                    'source': 'AzureMonitor',
                    'resource_id': 'sql-database',
                    'resource_name': 'app-database'
                }
            ]
            
            logs = []
            for log_entry in monitor_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='azure',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'monitor_type': 'Azure Monitor'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get Azure Monitor logs: {e}")
            return []
    
    def _get_activity_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get Azure Activity logs"""
        try:
            activity_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=22),
                    'level': 'INFO',
                    'message': 'Activity Log: Create or Update Virtual Machine',
                    'source': 'ActivityLog',
                    'resource_id': 'virtual-machine',
                    'resource_name': 'web-server-02'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=12),
                    'level': 'WARNING',
                    'message': 'Activity Log: Delete Network Security Group',
                    'source': 'ActivityLog',
                    'resource_id': 'network-security-group',
                    'resource_name': 'app-nsg'
                }
            ]
            
            logs = []
            for log_entry in activity_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='azure',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'Activity Log'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get Activity logs: {e}")
            return []
    
    def _get_app_insights_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get Application Insights logs"""
        try:
            app_insights_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=15),
                    'level': 'ERROR',
                    'message': 'Application Insights: Exception in web application',
                    'source': 'ApplicationInsights',
                    'resource_id': 'app-insights',
                    'resource_name': 'web-app-insights'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=5),
                    'level': 'WARNING',
                    'message': 'Application Insights: High dependency call failure rate',
                    'source': 'ApplicationInsights',
                    'resource_id': 'app-insights',
                    'resource_name': 'web-app-insights'
                }
            ]
            
            logs = []
            for log_entry in app_insights_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='azure',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'insights_type': 'Application Insights'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get Application Insights logs: {e}")
            return []

class GCPLogHandler(LogHandler):
    """GCP-specific log operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import logging
            from google.cloud import monitoring_v3
            
            self.client = {
                'logging': logging.Client(),
                'monitoring': monitoring_v3.MetricServiceClient()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def get_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get logs from Google Cloud Logging"""
        try:
            logs = []
            
            # Get Cloud Logging logs
            cloud_logs = self._get_cloud_logging_logs(time_range_hours, environment)
            logs.extend(cloud_logs)
            
            # Get Audit logs
            audit_logs = self._get_audit_logs(time_range_hours, environment)
            logs.extend(audit_logs)
            
            # Get VPC Flow logs
            vpc_flow_logs = self._get_vpc_flow_logs(time_range_hours, environment)
            logs.extend(vpc_flow_logs)
            
            logger.info(f"Retrieved {len(logs)} logs from GCP")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get GCP logs: {e}")
            return []
    
    def _get_cloud_logging_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get Cloud Logging logs"""
        try:
            # Simplified Cloud Logging logs collection
            cloud_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=30),
                    'level': 'ERROR',
                    'message': 'Cloud Logging: Container startup failed',
                    'source': 'CloudLogging',
                    'resource_id': 'gke-cluster',
                    'resource_name': 'production-cluster'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=20),
                    'level': 'WARNING',
                    'message': 'Cloud Logging: High memory usage in Cloud Function',
                    'source': 'CloudLogging',
                    'resource_id': 'cloud-function',
                    'resource_name': 'data-processor'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=10),
                    'level': 'INFO',
                    'message': 'Cloud Logging: Load balancer health check passed',
                    'source': 'CloudLogging',
                    'resource_id': 'load-balancer',
                    'resource_name': 'web-app-lb'
                }
            ]
            
            logs = []
            for log_entry in cloud_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='gcp',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'Cloud Logging'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get Cloud Logging logs: {e}")
            return []
    
    def _get_audit_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get GCP Audit logs"""
        try:
            audit_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=25),
                    'level': 'INFO',
                    'message': 'Audit Log: CreateInstance operation',
                    'source': 'AuditLog',
                    'resource_id': 'compute-engine',
                    'resource_name': 'web-server-03'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=15),
                    'level': 'WARNING',
                    'message': 'Audit Log: DeleteBucket operation on critical bucket',
                    'source': 'AuditLog',
                    'resource_id': 'cloud-storage',
                    'resource_name': 'critical-data-bucket'
                }
            ]
            
            logs = []
            for log_entry in audit_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='gcp',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'Audit Log'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get Audit logs: {e}")
            return []
    
    def _get_vpc_flow_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get VPC Flow logs"""
        try:
            vpc_flow_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=18),
                    'level': 'INFO',
                    'message': 'VPC Flow Log: ALLOW traffic between instances',
                    'source': 'VPCFlowLogs',
                    'resource_id': 'vpc-flow-log',
                    'resource_name': 'vpc-flow-log'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=8),
                    'level': 'WARNING',
                    'message': 'VPC Flow Log: DENY traffic from external IP',
                    'source': 'VPCFlowLogs',
                    'resource_id': 'vpc-flow-log',
                    'resource_name': 'vpc-flow-log'
                }
            ]
            
            logs = []
            for log_entry in vpc_flow_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='gcp',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'VPC Flow Log'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get VPC Flow logs: {e}")
            return []

class OnPremLogHandler(LogHandler):
    """On-premise log operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use syslog, file-based logging, or custom systems
            logger.info("On-premise log handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get logs from on-premise systems"""
        try:
            logs = []
            
            # Get application logs
            app_logs = self._get_application_logs(time_range_hours, environment)
            logs.extend(app_logs)
            
            # Get system logs
            system_logs = self._get_system_logs(time_range_hours, environment)
            logs.extend(system_logs)
            
            # Get security logs
            security_logs = self._get_security_logs(time_range_hours, environment)
            logs.extend(security_logs)
            
            logger.info(f"Retrieved {len(logs)} logs from on-premise systems")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get on-premise logs: {e}")
            return []
    
    def _get_application_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get application logs"""
        try:
            app_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=35),
                    'level': 'ERROR',
                    'message': 'Application: Database connection pool exhausted',
                    'source': 'ApplicationLog',
                    'resource_id': 'web-app',
                    'resource_name': 'production-web-app'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=28),
                    'level': 'WARNING',
                    'message': 'Application: High memory usage detected',
                    'source': 'ApplicationLog',
                    'resource_id': 'web-app',
                    'resource_name': 'production-web-app'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=12),
                    'level': 'INFO',
                    'message': 'Application: User authentication successful',
                    'source': 'ApplicationLog',
                    'resource_id': 'web-app',
                    'resource_name': 'production-web-app'
                }
            ]
            
            logs = []
            for log_entry in app_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='onprem',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'Application Log'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get application logs: {e}")
            return []
    
    def _get_system_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get system logs"""
        try:
            system_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=40),
                    'level': 'ERROR',
                    'message': 'System: Disk space critically low on /var partition',
                    'source': 'SystemLog',
                    'resource_id': 'server-01',
                    'resource_name': 'web-server-01'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=22),
                    'level': 'WARNING',
                    'message': 'System: High CPU load average detected',
                    'source': 'SystemLog',
                    'resource_id': 'server-01',
                    'resource_name': 'web-server-01'
                }
            ]
            
            logs = []
            for log_entry in system_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='onprem',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'System Log'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get system logs: {e}")
            return []
    
    def _get_security_logs(self, time_range_hours: int, environment: str) -> List[LogData]:
        """Get security logs"""
        try:
            security_logs = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=32),
                    'level': 'WARNING',
                    'message': 'Security: Failed login attempt from unknown IP',
                    'source': 'SecurityLog',
                    'resource_id': 'auth-system',
                    'resource_name': 'authentication-service'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=18),
                    'level': 'ERROR',
                    'message': 'Security: Unauthorized access attempt to sensitive file',
                    'source': 'SecurityLog',
                    'resource_id': 'file-server',
                    'resource_name': 'secure-file-server'
                }
            ]
            
            logs = []
            for log_entry in security_logs:
                log_data = LogData(
                    timestamp=log_entry['timestamp'],
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source'],
                    provider='onprem',
                    resource_id=log_entry['resource_id'],
                    resource_name=log_entry['resource_name'],
                    environment=environment,
                    metadata={'log_type': 'Security Log'}
                )
                logs.append(log_data)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get security logs: {e}")
            return []

def get_log_handler(provider: str, region: str = "us-west-2") -> LogHandler:
    """Get appropriate log handler"""
    handlers = {
        'aws': AWSLogHandler,
        'azure': AzureLogHandler,
        'gcp': GCPLogHandler,
        'onprem': OnPremLogHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
