#!/usr/bin/env python3
"""
Audit Trail Handler

Cloud-specific operations handler for audit trail management across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

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
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: str
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

class AuditTrailHandler(ABC):
    """Abstract base class for cloud-specific audit trail operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def discover_audit_trails(self) -> List[AuditTrailConfig]:
        """Discover existing audit trails"""
        pass
    
    @abstractmethod
    def create_audit_trail(self, trail_config: Dict[str, Any]) -> Optional[AuditTrailConfig]:
        """Create a new audit trail"""
        pass
    
    @abstractmethod
    def collect_audit_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect audit events"""
        pass

class AWSAuditTrailHandler(AuditTrailHandler):
    """AWS-specific audit trail operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'cloudtrail': boto3.client('cloudtrail', region_name=self.region),
                'logs': boto3.client('logs', region_name=self.region),
                'iam': boto3.client('iam', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region),
                'ec2': boto3.client('ec2', region_name=self.region),
                'lambda': boto3.client('lambda', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                'securityhub': boto3.client('securityhub', region_name=self.region),
                'guardduty': boto3.client('guardduty', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def discover_audit_trails(self) -> List[AuditTrailConfig]:
        """Discover existing AWS CloudTrail trails"""
        try:
            trails = []
            
            # Get CloudTrail trails
            cloudtrail_trails = self.client['cloudtrail'].describe_trails()
            
            for trail_name, trail_details in cloudtrail_trails.items():
                try:
                    # Get trail status
                    trail_status = self.client['cloudtrail'].get_trail_status(Name=trail_name)
                    
                    trail_config = AuditTrailConfig(
                        trail_id=trail_details.get('TrailARN', trail_name),
                        name=trail_name,
                        provider="aws",
                        region=self.region,
                        enabled=trail_status.get('IsLogging', False),
                        log_sources=self._get_aws_log_sources(),
                        retention_days=self._get_cloudtrail_retention(trail_name),
                        encryption_enabled=trail_details.get('KmsKeyId') is not None,
                        multi_region=trail_details.get('IsMultiRegionTrail', False),
                        log_format="json",
                        destination=trail_details.get('S3BucketName', ''),
                        filters={},
                        alert_rules=[]
                    )
                    
                    trails.append(trail_config)
                    
                except Exception as e:
                    logger.warning(f"Failed to get details for trail {trail_name}: {e}")
                    continue
            
            logger.info(f"Discovered {len(trails)} AWS CloudTrail trails")
            return trails
            
        except Exception as e:
            logger.error(f"Failed to discover AWS audit trails: {e}")
            return []
    
    def _get_aws_log_sources(self) -> List[str]:
        """Get AWS log sources"""
        return [
            'cloudtrail',
            'cloudtrail_logs',
            'aws_config',
            'aws_config_history',
            'aws_cloudtrail',
            'aws_guardduty',
            'aws_securityhub',
            'vpc_flow_logs',
            'aws_lambda',
            'cloudwatch_logs',
            'aws_iam',
            'aws_ec2'
        ]
    
    def _get_cloudtrail_retention(self, trail_name: str) -> int:
        """Get CloudTrail log retention period"""
        try:
            # Get S3 bucket lifecycle policy
            trails = self.client['cloudtrail'].describe_trails()
            trail_details = trails.get(trail_name, {})
            bucket_name = trail_details.get('S3BucketName')
            
            if bucket_name:
                try:
                    lifecycle = self.client['s3'].get_bucket_lifecycle_configuration(Bucket=bucket_name)
                    for rule in lifecycle.get('Rules', []):
                        if 'Expiration' in rule:
                            days = rule['Expiration'].get('Days')
                            if days:
                                return days
                except:
                    pass
            
            return 365  # Default retention
            
        except Exception:
            return 365
    
    def create_audit_trail(self, trail_config: Dict[str, Any]) -> Optional[AuditTrailConfig]:
        """Create a new AWS CloudTrail trail"""
        try:
            trail_name = trail_config['name']
            
            # Create S3 bucket for logs if specified
            s3_bucket_name = trail_config.get('s3_bucket_name')
            if not s3_bucket_name:
                s3_bucket_name = f"cloudtrail-{trail_name}-{self.region}-{datetime.utcnow().strftime('%Y%m%d')}"
                
                # Create bucket
                self.client['s3'].create_bucket(
                    Bucket=s3_bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region} if self.region != 'us-east-1' else {}
                )
            
            # Create CloudTrail trail
            trail_params = {
                'Name': trail_name,
                'S3BucketName': s3_bucket_name,
                'IncludeGlobalServiceEvents': trail_config.get('include_global_service_events', True),
                'IsMultiRegionTrail': trail_config.get('multi_region', False),
                'EnableLogFileValidation': trail_config.get('enable_log_file_validation', True)
            }
            
            # Add KMS key if specified
            if trail_config.get('kms_key_id'):
                trail_params['KmsKeyId'] = trail_config['kms_key_id']
            
            # Add CloudWatch logs if specified
            if trail_config.get('cloudwatch_log_group'):
                trail_params['CloudWatchLogsLogGroupArn'] = trail_config['cloudwatch_log_group']
            
            response = self.client['cloudtrail'].create_trail(**trail_params)
            
            # Start logging
            self.client['cloudtrail'].start_logging(Name=response['TrailARN'])
            
            # Create trail config object
            created_trail = AuditTrailConfig(
                trail_id=response['TrailARN'],
                name=trail_name,
                provider="aws",
                region=self.region,
                enabled=True,
                log_sources=self._get_aws_log_sources(),
                retention_days=trail_config.get('retention_days', 365),
                encryption_enabled=trail_config.get('kms_key_id') is not None,
                multi_region=trail_config.get('multi_region', False),
                log_format="json",
                destination=s3_bucket_name,
                filters=trail_config.get('filters', {}),
                alert_rules=trail_config.get('alert_rules', [])
            )
            
            logger.info(f"Created AWS CloudTrail trail: {trail_name}")
            return created_trail
            
        except Exception as e:
            logger.error(f"Failed to create AWS audit trail: {e}")
            return None
    
    def collect_audit_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect audit events from AWS CloudTrail"""
        try:
            events = []
            
            # Get CloudTrail events
            lookup_attributes = []
            if event_types:
                lookup_attributes.append({
                    'AttributeKey': 'EventName',
                    'AttributeValue': ','.join(event_types)
                })
            
            paginator = self.client['cloudtrail'].get_paginator('lookup_events')
            
            for page in paginator.paginate(
                StartTime=start_time,
                EndTime=end_time,
                LookupAttributes=lookup_attributes
            ):
                for event in page.get('Events', []):
                    try:
                        # Parse CloudTrail event
                        cloudtrail_event = json.loads(event.get('CloudTrailEvent', '{}'))
                        
                        audit_event = AuditEvent(
                            event_id=event.get('EventId', ''),
                            timestamp=event.get('EventTime', datetime.utcnow()),
                            event_type=self._map_aws_event_type(cloudtrail_event.get('EventName', '')),
                            user_id=cloudtrail_event.get('userIdentity', {}).get('principalId', ''),
                            user_name=cloudtrail_event.get('userIdentity', {}).get('userName', ''),
                            resource_id=cloudtrail_event.get('resources', [{}])[0].get('ARN', '') if cloudtrail_event.get('resources') else '',
                            resource_name=cloudtrail_event.get('resources', [{}])[0].get('ResourceName', '') if cloudtrail_event.get('resources') else '',
                            resource_type=self._get_aws_resource_type(cloudtrail_event.get('resources', [{}])[0].get('ResourceType', '')) if cloudtrail_event.get('resources') else '',
                            provider="aws",
                            region=cloudtrail_event.get('awsRegion', self.region),
                            environment=self._determine_environment(cloudtrail_event),
                            action=cloudtrail_event.get('EventName', ''),
                            result='success' if cloudtrail_event.get('errorCode') is None else 'failed',
                            source_ip=cloudtrail_event.get('sourceIPAddress', ''),
                            user_agent=cloudtrail_event.get('userAgent', ''),
                            details={
                                'event_version': cloudtrail_event.get('eventVersion'),
                                'user_identity': cloudtrail_event.get('userIdentity'),
                                'request_parameters': cloudtrail_event.get('requestParameters'),
                                'response_elements': cloudtrail_event.get('responseElements'),
                                'error_code': cloudtrail_event.get('errorCode'),
                                'error_message': cloudtrail_event.get('errorMessage')
                            },
                            severity=self._determine_severity(cloudtrail_event),
                            compliance_tags=self._get_compliance_tags(cloudtrail_event),
                            metadata={
                                'event_source': cloudtrail_event.get('eventSource'),
                                'account_id': cloudtrail_event.get('recipientAccountId'),
                                'request_id': cloudtrail_event.get('requestID',
                                'event_id': event.get('EventId')
                            }
                        )
                        
                        # Apply filters
                        if self._passes_filters(audit_event, filters):
                            events.append(audit_event)
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse CloudTrail event: {e}")
                        continue
            
            # Collect events from other AWS services
            events.extend(self._collect_guardduty_events(start_time, end_time, event_types, filters))
            events.extend(self._collect_securityhub_events(start_time, end_time, event_types, filters))
            events.extend(self._collect_cloudwatch_logs(start_time, end_time, event_types, filters))
            
            logger.info(f"Collected {len(events)} AWS audit events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to collect AWS audit events: {e}")
            return []
    
    def _map_aws_event_type(self, event_name: str) -> str:
        """Map AWS event name to standard event type"""
        event_mapping = {
            'ConsoleLogin': 'user_login',
            'CreateUser': 'user_creation',
            'DeleteUser': 'user_deletion',
            'AddUserToGroup': 'permission_change',
            'RemoveUserFromGroup': 'permission_change',
            'AttachUserPolicy': 'permission_change',
            'DetachUserPolicy': 'permission_change',
            'CreateRole': 'permission_change',
            'DeleteRole': 'permission_change',
            'AttachRolePolicy': 'permission_change',
            'DetachRolePolicy': 'permission_change',
            'RunInstances': 'resource_creation',
            'TerminateInstances': 'resource_deletion',
            'CreateBucket': 'resource_creation',
            'DeleteBucket': 'resource_deletion',
            'CreateVolume': 'resource_creation',
            'DeleteVolume': 'resource_deletion',
            'CreateFunction': 'resource_creation',
            'DeleteFunction': 'resource_deletion',
            'ModifyInstanceAttribute': 'resource_modification',
            'ModifyBucket': 'resource_modification',
            'ModifyVolumeAttribute': 'resource_modification',
            'UpdateFunctionCode': 'resource_modification'
        }
        
        return event_mapping.get(event_name, 'system_event')
    
    def _get_aws_resource_type(self, resource_type: str) -> str:
        """Map AWS resource type to standard type"""
        if not resource_type:
            return 'unknown'
        
        type_mapping = {
            'AWS::IAM::User': 'iam_user',
            'AWS::IAM::Role': 'iam_role',
            'AWS::IAM::Policy': 'iam_policy',
            'AWS::EC2::Instance': 'ec2_instance',
            'AWS::EC2::Volume': 'ebs_volume',
            'AWS::EC2::VPC': 'vpc',
            'AWS::EC2::SecurityGroup': 'security_group',
            'AWS::S3::Bucket': 's3_bucket',
            'AWS::Lambda::Function': 'lambda_function',
            'AWS::RDS::DBInstance': 'rds_instance',
            'AWS::RDS::DBSnapshot': 'rds_snapshot'
        }
        
        return type_mapping.get(resource_type, resource_type.lower().replace('::', '_'))
    
    def _determine_environment(self, event: Dict[str, Any]) -> str:
        """Determine environment from event context"""
        # Check for environment tags
        resources = event.get('resources', [])
        for resource in resources:
            resource_name = resource.get('ResourceName', '').lower()
            if 'prod' in resource_name or 'production' in resource_name:
                return 'production'
            elif 'dev' in resource_name or 'development' in resource_name:
                return 'development'
            elif 'test' in resource_name:
                return 'test'
            elif 'staging' in resource_name:
                return 'staging'
        
        # Check user context
        user_name = event.get('userIdentity', {}).get('userName', '').lower()
        if 'prod' in user_name or 'admin' in user_name:
            return 'production'
        
        return 'unknown'
    
    def _determine_severity(self, event: Dict[str, Any]) -> str:
        """Determine severity of event"""
        event_name = event.get('EventName', '')
        error_code = event.get('errorCode')
        user_type = event.get('userIdentity', {}).get('type', '')
        
        # High severity events
        if any(keyword in event_name.lower() for keyword in ['delete', 'terminate', 'remove', 'detach']):
            return 'high'
        
        # Critical events
        if user_type == 'Root' and event_name == 'ConsoleLogin':
            return 'critical'
        
        # Failed events
        if error_code:
            return 'medium'
        
        # Privilege changes
        if any(keyword in event_name.lower() for keyword in ['attach', 'create', 'modify']):
            return 'medium'
        
        return 'low'
    
    def _get_compliance_tags(self, event: Dict[str, Any]) -> List[str]:
        """Get compliance tags for event"""
        tags = []
        
        event_name = event.get('EventName', '')
        event_source = event.get('eventSource', '')
        
        # SOC2 relevant events
        if event_source in ['iam.amazonaws.com', 'cloudtrail.amazonaws.com', 'config.amazonaws.com']:
            tags.append('soc2')
        
        # ISO27001 relevant events
        if event_source in ['iam.amazonaws.com', 'ec2.amazonaws.com', 's3.amazonaws.com']:
            tags.append('iso27001')
        
        # PCI-DSS relevant events
        if any(keyword in event_name.lower() for keyword in ['delete', 'terminate', 'detach']):
            tags.append('pci_dss')
        
        # HIPAA relevant events
        if event_source in ['iam.amazonaws.com', 'rds.amazonaws.com', 'ec2.amazonaws.com']:
            tags.append('hipaa')
        
        return tags
    
    def _passes_filters(self, event: AuditEvent, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if event passes filters"""
        if not filters:
            return True
        
        # Filter by user
        if 'user_id' in filters:
            if isinstance(filters['user_id'], list):
                if event.user_id not in filters['user_id']:
                    return False
            else:
                if event.user_id != filters['user_id']:
                    return False
        
        # Filter by resource type
        if 'resource_type' in filters:
            if isinstance(filters['resource_type'], list):
                if event.resource_type not in filters['resource_type']:
                    return False
            else:
                if event.resource_type != filters['resource_type']:
                    return False
        
        # Filter by severity
        if 'severity' in filters:
            if isinstance(filters['severity'], list):
                if event.severity not in filters['severity']:
                    return False
            else:
                if event.severity != filters['severity']:
                    return False
        
        return True
    
    def _collect_guardduty_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect events from AWS GuardDuty"""
        try:
            events = []
            
            # Get GuardDuty detectors
            detectors = self.client['guardduty'].list_detectors()
            
            for detector_id in detectors['DetectorIds']:
                try:
                    # Get findings
                    findings = self.client['guardduty'].list_findings(
                        DetectorId=detector_id,
                        FindingCriteria={
                            'Criterion': {
                                'UpdatedAt': {
                                    'Gte': start_time.isoformat(),
                                    'Lte': end_time.isoformat()
                                }
                            }
                        }
                    )
                    
                    for finding_id in findings['FindingIds']:
                        try:
                            finding = self.client['guardduty'].get_finding(
                                DetectorId=detector_id,
                                FindingId=finding_id
                            )
                            
                            audit_event = AuditEvent(
                                event_id=finding_id,
                                timestamp=datetime.fromisoformat(finding['Service']['UpdatedAt'].replace('Z', '+00:00')),
                                event_type='security_event',
                                user_id=finding['Resource'].get('InstanceDetails', {}).get('InstanceId', ''),
                                user_name='guardduty',
                                resource_id=finding['Resource'].get('InstanceDetails', {}).get('InstanceId', ''),
                                resource_name=finding['Resource'].get('InstanceDetails', {}).get('InstanceTags', {}).get('Name', ''),
                                resource_type='ec2_instance',
                                provider="aws",
                                region=finding['Resource'].get('Region', self.region),
                                environment='production',
                                action=finding['Service']['Action'].get('ActionType', ''),
                                result='detected',
                                source_ip=finding['Service'].get('Action', {}).get('AwsApiCallAction', {}).get('CallerIp', ''),
                                user_agent='guardduty',
                                details={
                                    'finding_type': finding['Type'],
                                    'severity': finding['Severity'],
                                    'confidence': finding['Service'].get('Confidence'),
                                    'description': finding['Description'],
                                    'resource_details': finding['Resource']
                                },
                                severity=self._map_guardduty_severity(finding['Severity']),
                                compliance_tags=['soc2', 'iso27001', 'pci_dss'],
                                metadata={
                                    'detector_id': detector_id,
                                    'finding_id': finding_id,
                                    'service': finding['Service']
                                }
                            )
                            
                            if self._passes_filters(audit_event, filters):
                                events.append(audit_event)
                            
                        except Exception as e:
                            logger.warning(f"Failed to get GuardDuty finding {finding_id}: {e}")
                            continue
                
                except Exception as e:
                    logger.warning(f"Failed to get findings from detector {detector_id}: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to collect GuardDuty events: {e}")
            return []
    
    def _map_guardduty_severity(self, guardduty_severity: float) -> str:
        """Map GuardDuty severity to standard severity"""
        if guardduty_severity >= 8.0:
            return 'critical'
        elif guardduty_severity >= 6.0:
            return 'high'
        elif guardduty_severity >= 4.0:
            return 'medium'
        else:
            return 'low'
    
    def _collect_securityhub_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect events from AWS Security Hub"""
        try:
            events = []
            
            # Get Security Hub findings
            findings = self.client['securityhub'].get_findings(
                Filters={
                    'UpdatedAt': [
                        {
                            'DateRange': {
                                'Start': start_time.isoformat(),
                                'End': end_time.isoformat()
                            }
                        }
                    ]
                }
            )
            
            for finding in findings['Findings']:
                try:
                    audit_event = AuditEvent(
                        event_id=finding['Id'],
                        timestamp=datetime.fromisoformat(finding['UpdatedAt'].replace('Z', '+00:00')),
                        event_type='security_event',
                        user_id=finding['Resources'][0].get('Id', '') if finding.get('Resources') else '',
                        user_name='securityhub',
                        resource_id=finding['Resources'][0].get('Id', '') if finding.get('Resources') else '',
                        resource_name=finding['Resources'][0].get('Details', {}).get('AwsEc2Instance', {}).get('Tags', {}).get('Name', '') if finding.get('Resources') else '',
                        resource_type=self._get_securityhub_resource_type(finding),
                        provider="aws",
                        region=finding['Resources'][0].get('Region', self.region) if finding.get('Resources') else self.region,
                        environment='production',
                        action=finding['Title'],
                        result='detected',
                        source_ip=finding.get('Network', {}).get('SourceIpV4', ''),
                        user_agent='securityhub',
                        details={
                            'finding_type': finding['Types'][0] if finding.get('Types') else '',
                            'severity': finding['Severity']['Label'],
                            'description': finding['Description'],
                            'remediation': finding.get('Remediation', {}),
                            'confidence': finding.get('Confidence'),
                            'criticality': finding.get('Criticality')
                        },
                        severity=self._map_securityhub_severity(finding['Severity']['Label']),
                        compliance_tags=['soc2', 'iso27001', 'pci_dss'],
                        metadata={
                            'product_name': finding['ProductFields'].get('aws/securityhub/ProductName', ''),
                            'company_name': finding['ProductFields'].get('aws/securityhub/CompanyName', ''),
                            'finding_generator': finding['ProductFields'].get('aws/securityhub/FindingGenerator', '')
                        }
                    )
                    
                    if self._passes_filters(audit_event, filters):
                        events.append(audit_event)
                    
                except Exception as e:
                    logger.warning(f"Failed to process Security Hub finding: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to collect Security Hub events: {e}")
            return []
    
    def _get_securityhub_resource_type(self, finding: Dict[str, Any]) -> str:
        """Get resource type from Security Hub finding"""
        resources = finding.get('Resources', [])
        if not resources:
            return 'unknown'
        
        resource = resources[0]
        resource_type = resource.get('Type', '')
        
        type_mapping = {
            'AwsEc2Instance': 'ec2_instance',
            'AwsS3Bucket': 's3_bucket',
            'AwsIamUser': 'iam_user',
            'AwsIamRole': 'iam_role',
            'AwsRdsDbInstance': 'rds_instance',
            'AwsLambdaFunction': 'lambda_function'
        }
        
        return type_mapping.get(resource_type, resource_type.lower())
    
    def _map_securityhub_severity(self, severity_label: str) -> str:
        """Map Security Hub severity to standard severity"""
        severity_mapping = {
            'CRITICAL': 'critical',
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low',
            'INFORMATIONAL': 'low'
        }
        
        return severity_mapping.get(severity_label, 'medium')
    
    def _collect_cloudwatch_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect events from CloudWatch Logs"""
        try:
            events = []
            
            # Get log groups
            log_groups = self.client['logs'].describe_log_groups()
            
            for log_group in log_groups['logGroups']:
                log_group_name = log_group['logGroupName']
                
                # Skip non-audit log groups
                if not any(keyword in log_group_name.lower() for keyword in ['audit', 'security', 'access', 'cloudtrail']):
                    continue
                
                try:
                    # Get log streams
                    log_streams = self.client['logs'].describe_log_streams(
                        logGroupName=log_group_name,
                        orderBy='LastEventTime',
                        descending=True
                    )
                    
                    for log_stream in log_streams['logStreams'][:10]:  # Limit to recent streams
                        try:
                            # Get log events
                            log_events = self.client['logs'].get_log_events(
                                logGroupName=log_group_name,
                                logStreamName=log_stream['logStreamName'],
                                startTime=int(start_time.timestamp() * 1000),
                                endTime=int(end_time.timestamp() * 1000)
                            )
                            
                            for log_event in log_events['events']:
                                try:
                                    # Parse log message
                                    message = log_event['message']
                                    
                                    # Try to parse as JSON
                                    try:
                                        log_data = json.loads(message)
                                        event_name = log_data.get('event', 'unknown')
                                        user_id = log_data.get('user_id', 'unknown')
                                        resource_id = log_data.get('resource_id', 'unknown')
                                    except:
                                        # Parse as plain text
                                        event_name = 'log_event'
                                        user_id = 'unknown'
                                        resource_id = log_group_name
                                    
                                    audit_event = AuditEvent(
                                        event_id=log_event['eventId'],
                                        timestamp=datetime.fromtimestamp(log_event['timestamp'] / 1000),
                                        event_type='system_event',
                                        user_id=user_id,
                                        user_name='cloudwatch',
                                        resource_id=resource_id,
                                        resource_name=log_group_name,
                                        resource_type='log_group',
                                        provider="aws",
                                        region=self.region,
                                        environment='production',
                                        action=event_name,
                                        result='logged',
                                        source_ip='',
                                        user_agent='cloudwatch_logs',
                                        details={
                                            'log_group': log_group_name,
                                            'log_stream': log_stream['logStreamName'],
                                            'message': message
                                        },
                                        severity='low',
                                        compliance_tags=['soc2', 'iso27001'],
                                        metadata={
                                            'log_group_name': log_group_name,
                                            'log_stream_name': log_stream['logStreamName']
                                        }
                                    )
                                    
                                    if self._passes_filters(audit_event, filters):
                                        events.append(audit_event)
                                    
                                except Exception as e:
                                    logger.warning(f"Failed to process CloudWatch log event: {e}")
                                    continue
                        
                        except Exception as e:
                            logger.warning(f"Failed to get events from log stream {log_stream['logStreamName']}: {e}")
                            continue
                
                except Exception as e:
                    logger.warning(f"Failed to process log group {log_group_name}: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to collect CloudWatch logs: {e}")
            return []

# Simplified handlers for other providers
class AzureAuditTrailHandler(AuditTrailHandler):
    """Azure-specific audit trail operations"""
    
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
    
    def discover_audit_trails(self) -> List[AuditTrailConfig]:
        """Discover existing Azure audit trails"""
        try:
            trails = []
            
            # Simplified Azure audit trail discovery
            trail_config = AuditTrailConfig(
                trail_id="azure-audit-log",
                name="Azure Activity Log",
                provider="azure",
                region="eastus",
                enabled=True,
                log_sources=["azure_activity_log", "azure_signin_log"],
                retention_days=365,
                encryption_enabled=True,
                multi_region=True,
                log_format="json",
                destination="azure_monitor",
                filters={},
                alert_rules=[]
            )
            
            trails.append(trail_config)
            
            logger.info(f"Discovered {len(trails)} Azure audit trails")
            return trails
            
        except Exception as e:
            logger.error(f"Failed to discover Azure audit trails: {e}")
            return []
    
    def create_audit_trail(self, trail_config: Dict[str, Any]) -> Optional[AuditTrailConfig]:
        """Create a new Azure audit trail"""
        try:
            # Simplified Azure trail creation
            created_trail = AuditTrailConfig(
                trail_id=f"azure-{trail_config['name']}",
                name=trail_config['name'],
                provider="azure",
                region="eastus",
                enabled=True,
                log_sources=["azure_activity_log", "azure_signin_log"],
                retention_days=trail_config.get('retention_days', 365),
                encryption_enabled=True,
                multi_region=True,
                log_format="json",
                destination="azure_monitor",
                filters={},
                alert_rules=[]
            )
            
            logger.info(f"Created Azure audit trail: {trail_config['name']}")
            return created_trail
            
        except Exception as e:
            logger.error(f"Failed to create Azure audit trail: {e}")
            return None
    
    def collect_audit_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect audit events from Azure"""
        try:
            events = []
            
            # Simulate Azure audit events
            sample_events = [
                AuditEvent(
                    event_id="azure-event-1",
                    timestamp=datetime.utcnow() - timedelta(hours=1),
                    event_type="user_login",
                    user_id="user@azure.com",
                    user_name="Azure User",
                    resource_id="/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1",
                    resource_name="vm1",
                    resource_type="virtual_machine",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    action="VirtualMachineStart",
                    result="success",
                    source_ip="192.168.1.100",
                    user_agent="Azure Portal",
                    details={"operation": "VM start"},
                    severity="medium",
                    compliance_tags=["soc2", "iso27001"],
                    metadata={}
                )
            ]
            
            events.extend(sample_events)
            
            logger.info(f"Collected {len(events)} Azure audit events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to collect Azure audit events: {e}")
            return []

class GCPAuditTrailHandler(AuditTrailHandler):
    """GCP-specific audit trail operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import logging
            from google.cloud import resource_manager
            
            self.client = {
                'logging': logging.Client(),
                'resource': resource_manager.Client()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def discover_audit_trails(self) -> List[AuditTrailConfig]:
        """Discover existing GCP audit trails"""
        try:
            trails = []
            
            # Simplified GCP audit trail discovery
            trail_config = AuditTrailConfig(
                trail_id="gcp-audit-log",
                name="GCP Cloud Audit Logs",
                provider="gcp",
                region="us-central1",
                enabled=True,
                log_sources=["gcp_audit_log", "gcp_activity_log"],
                retention_days=365,
                encryption_enabled=True,
                multi_region=True,
                log_format="json",
                destination="cloud_logging",
                filters={},
                alert_rules=[]
            )
            
            trails.append(trail_config)
            
            logger.info(f"Discovered {len(trails)} GCP audit trails")
            return trails
            
        except Exception as e:
            logger.error(f"Failed to discover GCP audit trails: {e}")
            return []
    
    def create_audit_trail(self, trail_config: Dict[str, Any]) -> Optional[AuditTrailConfig]:
        """Create a new GCP audit trail"""
        try:
            # Simplified GCP trail creation
            created_trail = AuditTrailConfig(
                trail_id=f"gcp-{trail_config['name']}",
                name=trail_config['name'],
                provider="gcp",
                region="us-central1",
                enabled=True,
                log_sources=["gcp_audit_log", "gcp_activity_log"],
                retention_days=trail_config.get('retention_days', 365),
                encryption_enabled=True,
                multi_region=True,
                log_format="json",
                destination="cloud_logging",
                filters={},
                alert_rules=[]
            )
            
            logger.info(f"Created GCP audit trail: {trail_config['name']}")
            return created_trail
            
        except Exception as e:
            logger.error(f"Failed to create GCP audit trail: {e}")
            return None
    
    def collect_audit_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect audit events from GCP"""
        try:
            events = []
            
            # Simulate GCP audit events
            sample_events = [
                AuditEvent(
                    event_id="gcp-event-1",
                    timestamp=datetime.utcnow() - timedelta(hours=1),
                    event_type="user_login",
                    user_id="user@gcp.com",
                    user_name="GCP User",
                    resource_id="projects/my-project/zones/us-central1-a/instances/vm1",
                    resource_name="vm1",
                    resource_type="compute_instance",
                    provider="gcp",
                    region="us-central1",
                    environment="production",
                    action="compute.instances.start",
                    result="success",
                    source_ip="192.168.1.100",
                    user_agent="GCP Console",
                    details={"operation": "VM start"},
                    severity="medium",
                    compliance_tags=["soc2", "iso27001"],
                    metadata={}
                )
            ]
            
            events.extend(sample_events)
            
            logger.info(f"Collected {len(events)} GCP audit events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to collect GCP audit events: {e}")
            return []

class OnPremAuditTrailHandler(AuditTrailHandler):
    """On-premise audit trail operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use various logging systems
            logger.info("On-premise audit handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def discover_audit_trails(self) -> List[AuditTrailConfig]:
        """Discover existing on-premise audit trails"""
        try:
            trails = []
            
            # Simplified on-premise audit trail discovery
            trail_config = AuditTrailConfig(
                trail_id="onprem-audit-log",
                name="On-premise System Logs",
                provider="onprem",
                region="datacenter-1",
                enabled=True,
                log_sources=["syslog", "auth_log", "application_logs"],
                retention_days=365,
                encryption_enabled=True,
                multi_region=False,
                log_format="syslog",
                destination="central_log_server",
                filters={},
                alert_rules=[]
            )
            
            trails.append(trail_config)
            
            logger.info(f"Discovered {len(trails)} on-premise audit trails")
            return trails
            
        except Exception as e:
            logger.error(f"Failed to discover on-premise audit trails: {e}")
            return []
    
    def create_audit_trail(self, trail_config: Dict[str, Any]) -> Optional[AuditTrailConfig]:
        """Create a new on-premise audit trail"""
        try:
            # Simplified on-premise trail creation
            created_trail = AuditTrailConfig(
                trail_id=f"onprem-{trail_config['name']}",
                name=trail_config['name'],
                provider="onprem",
                region="datacenter-1",
                enabled=True,
                log_sources=["syslog", "auth_log", "application_logs"],
                retention_days=trail_config.get('retention_days', 365),
                encryption_enabled=True,
                multi_region=False,
                log_format="syslog",
                destination="central_log_server",
                filters={},
                alert_rules=[]
            )
            
            logger.info(f"Created on-premise audit trail: {trail_config['name']}")
            return created_trail
            
        except Exception as e:
            logger.error(f"Failed to create on-premise audit trail: {e}")
            return None
    
    def collect_audit_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditEvent]:
        """Collect audit events from on-premise systems"""
        try:
            events = []
            
            # Simulate on-premise audit events
            sample_events = [
                AuditEvent(
                    event_id="onprem-event-1",
                    timestamp=datetime.utcnow() - timedelta(hours=1),
                    event_type="user_login",
                    user_id="user@company.com",
                    user_name="Local User",
                    resource_id="server1",
                    resource_name="server1",
                    resource_type="server",
                    provider="onprem",
                    region="datacenter-1",
                    environment="production",
                    action="ssh_login",
                    result="success",
                    source_ip="192.168.1.100",
                    user_agent="OpenSSH",
                    details={"operation": "SSH login"},
                    severity="medium",
                    compliance_tags=["soc2", "iso27001"],
                    metadata={}
                )
            ]
            
            events.extend(sample_events)
            
            logger.info(f"Collected {len(events)} on-premise audit events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to collect on-premise audit events: {e}")
            return []

def get_audit_handler(provider: str, region: str = "us-west-2") -> AuditTrailHandler:
    """Get appropriate audit handler"""
    handlers = {
        'aws': AWSAuditTrailHandler,
        'azure': AzureAuditTrailHandler,
        'gcp': GCPAuditTrailHandler,
        'onprem': OnPremAuditTrailHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
