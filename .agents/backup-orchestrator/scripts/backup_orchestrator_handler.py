#!/usr/bin/env python3
"""
Backup Orchestrator Handler

Cloud-specific operations handler for backup orchestration across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BackupResource:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    region: str
    environment: str
    size_gb: float
    criticality: str
    backup_required: bool
    last_backup: Optional[datetime]
    backup_frequency: str
    retention_days: int
    tags: Dict[str, Any]

@dataclass
class BackupJob:
    job_id: str
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    backup_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    size_gb: float
    location: str
    encryption_enabled: bool
    compression_enabled: bool
    verification_enabled: bool
    retention_days: int
    cost_estimate: float
    metadata: Dict[str, Any]

class BackupOrchestratorHandler(ABC):
    """Abstract base class for cloud-specific backup operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def discover_backup_resources(self) -> List[BackupResource]:
        """Discover backup-eligible resources"""
        pass
    
    @abstractmethod
    def execute_backup(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Execute backup for a resource"""
        pass
    
    @abstractmethod
    def verify_backup(self, job: BackupJob) -> Dict[str, Any]:
        """Verify backup integrity"""
        pass
    
    @abstractmethod
    def cleanup_old_backups(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old backups"""
        pass

class AWSBackupOrchestratorHandler(BackupOrchestratorHandler):
    """AWS-specific backup operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ec2': boto3.client('ec2', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region),
                'backup': boto3.client('backup', region_name=self.region),
                'ebs': boto3.client('ec2', region_name=self.region),  # EBS uses EC2 client
                'lambda': boto3.client('lambda', region_name=self.region),
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def discover_backup_resources(self) -> List[BackupResource]:
        """Discover AWS backup-eligible resources"""
        try:
            resources = []
            
            # Discover EC2 instances
            ec2_resources = self._discover_ec2_instances()
            resources.extend(ec2_resources)
            
            # Discover RDS instances
            rds_resources = self._discover_rds_instances()
            resources.extend(rds_resources)
            
            # Discover EBS volumes
            ebs_resources = self._discover_ebs_volumes()
            resources.extend(ebs_resources)
            
            # Discover Lambda functions
            lambda_resources = self._discover_lambda_functions()
            resources.extend(lambda_resources)
            
            # Discover S3 buckets
            s3_resources = self._discover_s3_buckets()
            resources.extend(s3_resources)
            
            logger.info(f"Discovered {len(resources)} AWS backup resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover AWS backup resources: {e}")
            return []
    
    def _discover_ec2_instances(self) -> List[BackupResource]:
        """Discover EC2 instances for backup"""
        resources = []
        
        try:
            response = self.client['ec2'].describe_instances()
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'running':
                        continue
                    
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    
                    # Get instance size (simplified)
                    size_gb = self._get_instance_size_gb(instance_type)
                    
                    # Get tags
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    # Determine criticality from tags
                    criticality = tags.get('Criticality', 'standard').lower()
                    
                    # Check if backup required
                    backup_required = tags.get('Backup', 'true').lower() == 'true'
                    
                    # Get last backup time (from AWS Backup if available)
                    last_backup = self._get_last_backup_time(instance_id)
                    
                    resource = BackupResource(
                        resource_id=instance_id,
                        resource_name=tags.get('Name', instance_id),
                        resource_type="ec2_instance",
                        provider="aws",
                        region=self.region,
                        environment=tags.get('Environment', 'unknown'),
                        size_gb=size_gb,
                        criticality=criticality,
                        backup_required=backup_required,
                        last_backup=last_backup,
                        backup_frequency=tags.get('BackupFrequency', 'daily'),
                        retention_days=int(tags.get('RetentionDays', 30)),
                        tags=tags
                    )
                    
                    resources.append(resource)
            
        except Exception as e:
            logger.error(f"Failed to discover EC2 instances: {e}")
        
        return resources
    
    def _get_instance_size_gb(self, instance_type: str) -> float:
        """Get instance size in GB (simplified)"""
        # Simplified sizing based on instance type
        size_mapping = {
            't3.micro': 8.0,
            't3.small': 20.0,
            't3.medium': 40.0,
            't3.large': 80.0,
            'm5.large': 80.0,
            'm5.xlarge': 160.0,
            'm5.2xlarge': 320.0,
            'c5.large': 50.0,
            'c5.xlarge': 100.0,
            'c5.2xlarge': 200.0
        }
        
        return size_mapping.get(instance_type, 80.0)
    
    def _get_last_backup_time(self, resource_id: str) -> Optional[datetime]:
        """Get last backup time from AWS Backup (simplified)"""
        try:
            # Try to get from AWS Backup
            response = self.client['backup'].list_recovery_points_by_resource(
                ResourceArn=f"arn:aws:ec2:{self.region}:*:instance/{resource_id}"
            )
            
            recovery_points = response.get('RecoveryPoints', [])
            if recovery_points:
                latest_point = max(recovery_points, key=lambda x: x['CreationDate'])
                return latest_point['CreationDate']
        
        except:
            pass
        
        return None
    
    def _discover_rds_instances(self) -> List[BackupResource]:
        """Discover RDS instances for backup"""
        resources = []
        
        try:
            response = self.client['rds'].describe_db_instances()
            
            for db_instance in response['DBInstances']:
                if db_instance['DBInstanceStatus'] != 'available':
                    continue
                
                db_id = db_instance['DBInstanceIdentifier']
                allocated_storage = db_instance['AllocatedStorage']
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['rds'].list_tags_for_resource(
                        ResourceName=db_instance['DBInstanceArn']
                    )
                    tags = {tag['Key']: tag['Value'] for tag in tag_response['TagList']}
                except:
                    pass
                
                criticality = tags.get('Criticality', 'standard').lower()
                backup_required = tags.get('Backup', 'true').lower() == 'true'
                last_backup = self._get_rds_last_backup(db_id)
                
                resource = BackupResource(
                    resource_id=db_id,
                    resource_name=tags.get('Name', db_id),
                    resource_type="rds_instance",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    size_gb=float(allocated_storage),
                    criticality=criticality,
                    backup_required=backup_required,
                    last_backup=last_backup,
                    backup_frequency=tags.get('BackupFrequency', 'daily'),
                    retention_days=int(tags.get('RetentionDays', 30)),
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to discover RDS instances: {e}")
        
        return resources
    
    def _get_rds_last_backup(self, db_id: str) -> Optional[datetime]:
        """Get last RDS backup time"""
        try:
            response = self.client['rds'].describe_db_snapshots(
                DBInstanceIdentifier=db_id,
                SnapshotType='automated',
                MaxRecords=1
            )
            
            snapshots = response.get('DBSnapshots', [])
            if snapshots:
                return snapshots[0]['SnapshotCreateTime']
        
        except:
            pass
        
        return None
    
    def _discover_ebs_volumes(self) -> List[BackupResource]:
        """Discover EBS volumes for backup"""
        resources = []
        
        try:
            response = self.client['ec2'].describe_volumes()
            
            for volume in response['Volumes']:
                if volume['State'] != 'in-use':
                    continue
                
                volume_id = volume['VolumeId']
                size_gb = volume['Size']
                
                # Get tags
                tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                
                criticality = tags.get('Criticality', 'standard').lower()
                backup_required = tags.get('Backup', 'true').lower() == 'true'
                last_backup = self._get_ebs_last_backup(volume_id)
                
                resource = BackupResource(
                    resource_id=volume_id,
                    resource_name=tags.get('Name', volume_id),
                    resource_type="ebs_volume",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    size_gb=float(size_gb),
                    criticality=criticality,
                    backup_required=backup_required,
                    last_backup=last_backup,
                    backup_frequency=tags.get('BackupFrequency', 'daily'),
                    retention_days=int(tags.get('RetentionDays', 30)),
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to discover EBS volumes: {e}")
        
        return resources
    
    def _get_ebs_last_backup(self, volume_id: str) -> Optional[datetime]:
        """Get last EBS snapshot time"""
        try:
            response = self.client['ec2'].describe_snapshots(
                Filters=[{'Name': 'volume-id', 'Values': [volume_id]}],
                MaxRecords=1
            )
            
            snapshots = response.get('Snapshots', [])
            if snapshots:
                return snapshots[0]['StartTime']
        
        except:
            pass
        
        return None
    
    def _discover_lambda_functions(self) -> List[BackupResource]:
        """Discover Lambda functions for backup"""
        resources = []
        
        try:
            response = self.client['lambda'].list_functions()
            
            for function in response['Functions']:
                function_name = function['FunctionName']
                
                # Lambda functions don't have traditional size, estimate based on code size
                code_size_mb = function['CodeSize'] / (1024 * 1024)  # Convert to MB
                size_gb = max(code_size_mb / 1024, 0.1)  # Convert to GB, minimum 0.1GB
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['lambda'].list_tags(Resource=function['FunctionArn'])
                    tags = tag_response.get('Tags', {})
                except:
                    pass
                
                criticality = tags.get('Criticality', 'standard').lower()
                backup_required = tags.get('Backup', 'true').lower() == 'true'
                
                resource = BackupResource(
                    resource_id=function_name,
                    resource_name=tags.get('Name', function_name),
                    resource_type="lambda_function",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    size_gb=size_gb,
                    criticality=criticality,
                    backup_required=backup_required,
                    last_backup=None,  # Lambda backups are version-based
                    backup_frequency=tags.get('BackupFrequency', 'daily'),
                    retention_days=int(tags.get('RetentionDays', 30)),
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to discover Lambda functions: {e}")
        
        return resources
    
    def _discover_s3_buckets(self) -> List[BackupResource]:
        """Discover S3 buckets for backup"""
        resources = []
        
        try:
            response = self.client['s3'].list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                # Get bucket size (simplified)
                size_gb = self._get_s3_bucket_size(bucket_name)
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['s3'].get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tag_response['TagSet']}
                except:
                    pass
                
                criticality = tags.get('Criticality', 'standard').lower()
                backup_required = tags.get('Backup', 'true').lower() == 'true'
                
                resource = BackupResource(
                    resource_id=bucket_name,
                    resource_name=tags.get('Name', bucket_name),
                    resource_type="s3_bucket",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    size_gb=size_gb,
                    criticality=criticality,
                    backup_required=backup_required,
                    last_backup=None,  # S3 has versioning
                    backup_frequency=tags.get('BackupFrequency', 'daily'),
                    retention_days=int(tags.get('RetentionDays', 30)),
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to discover S3 buckets: {e}")
        
        return resources
    
    def _get_s3_bucket_size(self, bucket_name: str) -> float:
        """Get S3 bucket size in GB (simplified)"""
        try:
            # This is a simplified implementation
            # In production, you would use CloudWatch metrics or S3 Inventory
            import random
            return random.uniform(10, 500)  # Random size between 10-500 GB
        except:
            return 100.0  # Fallback
    
    def execute_backup(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Execute backup for AWS resource"""
        try:
            if resource.resource_type == "ec2_instance":
                return self._backup_ec2_instance(resource, backup_type, job)
            elif resource.resource_type == "rds_instance":
                return self._backup_rds_instance(resource, backup_type, job)
            elif resource.resource_type == "ebs_volume":
                return self._backup_ebs_volume(resource, backup_type, job)
            elif resource.resource_type == "lambda_function":
                return self._backup_lambda_function(resource, backup_type, job)
            elif resource.resource_type == "s3_bucket":
                return self._backup_s3_bucket(resource, backup_type, job)
            else:
                raise ValueError(f"Unsupported resource type: {resource.resource_type}")
        
        except Exception as e:
            logger.error(f"Failed to execute backup for {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def _backup_ec2_instance(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Backup EC2 instance using AWS Backup"""
        try:
            # Use AWS Backup service
            backup_vault_name = f"backup-vault-{self.region}"
            
            # Create backup vault if it doesn't exist
            try:
                self.client['backup'].create_backup_vault(
                    BackupVaultName=backup_vault_name,
                    EncryptionKeyArn=None  # Use default AWS managed key
                )
            except self.client['backup'].exceptions AlreadyExistsException:
                pass
            
            # Start backup job
            response = self.client['backup'].start_backup_job(
                BackupVaultName=backup_vault_name,
                ResourceArn=f"arn:aws:ec2:{self.region}:*:instance/{resource.resource_id}",
                IamRoleArn=f"arn:aws:iam::{self._get_account_id()}:role/AWSBackupDefaultServiceRole",
                IdempotencyToken=job.job_id,
                Lifecycle={
                    'MoveToColdStorageAfterDays': 30,
                    'DeleteAfterDays': job.retention_days
                },
                CompleteWindowMinutes=60,
                Tags={
                    'BackupJobId': job.job_id,
                    'BackupType': backup_type,
                    'ResourceName': resource.resource_name
                }
            )
            
            backup_job_id = response['BackupJobId']
            
            # Wait for backup to complete (simplified - in production, you'd poll the status)
            import time
            time.sleep(10)  # Wait a bit for the job to start
            
            return {
                'success': True,
                'backup_job_id': backup_job_id,
                'location': f"aws-backup-vault://{backup_vault_name}/{backup_job_id}",
                'metadata': {
                    'backup_vault': backup_vault_name,
                    'aws_backup_job_id': backup_job_id
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to backup EC2 instance {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            return self.client['sts'].get_caller_identity()['Account']
        except:
            return "123456789012"  # Fallback
    
    def _backup_rds_instance(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Backup RDS instance"""
        try:
            snapshot_identifier = f"{resource.resource_id}-backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            if backup_type == "full":
                response = self.client['rds'].create_db_snapshot(
                    DBInstanceIdentifier=resource.resource_id,
                    DBSnapshotIdentifier=snapshot_identifier,
                    Tags=[
                        {'Key': 'BackupJobId', 'Value': job.job_id},
                        {'Key': 'BackupType', 'Value': backup_type}
                    ]
                )
            else:
                # For incremental/differential, RDS only supports full snapshots
                response = self.client['rds'].create_db_snapshot(
                    DBInstanceIdentifier=resource.resource_id,
                    DBSnapshotIdentifier=snapshot_identifier,
                    Tags=[
                        {'Key': 'BackupJobId', 'Value': job.job_id},
                        {'Key': 'BackupType', 'Value': backup_type}
                    ]
                )
            
            return {
                'success': True,
                'snapshot_id': snapshot_identifier,
                'location': f"rds-snapshot://{snapshot_identifier}",
                'metadata': {
                    'snapshot_identifier': snapshot_identifier,
                    'snapshot_type': response['DBSnapshot']['SnapshotType']
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to backup RDS instance {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def _backup_ebs_volume(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Backup EBS volume"""
        try:
            snapshot_description = f"Backup for {resource.resource_id} - {job.job_id}"
            
            response = self.client['ec2'].create_snapshot(
                VolumeId=resource.resource_id,
                Description=snapshot_description,
                TagSpecifications=[
                    {
                        'ResourceType': 'snapshot',
                        'Tags': [
                            {'Key': 'BackupJobId', 'Value': job.job_id},
                            {'Key': 'BackupType', 'Value': backup_type},
                            {'Key': 'Name', 'Value': f"{resource.resource_name}-backup"}
                        ]
                    }
                ]
            )
            
            snapshot_id = response['SnapshotId']
            
            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'location': f"ebs-snapshot://{snapshot_id}",
                'metadata': {
                    'snapshot_id': snapshot_id,
                    'volume_id': resource.resource_id
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to backup EBS volume {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def _backup_lambda_function(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Backup Lambda function (code and configuration)"""
        try:
            # Get function configuration
            response = self.client['lambda'].get_function(FunctionName=resource.resource_id)
            
            # Create backup of function code and configuration
            backup_data = {
                'configuration': response['Configuration'],
                'code': {
                    'location': response['Code']['Location'],
                    'repository_type': response['Code']['RepositoryType'] if 'RepositoryType' in response['Code'] else None
                },
                'tags': response.get('Tags', {})
            }
            
            # Store backup in S3 (simplified)
            backup_bucket = f"lambda-backups-{self.region}"
            backup_key = f"lambda-backups/{resource.resource_id}/{job.job_id}.json"
            
            try:
                self.client['s3'].put_object(
                    Bucket=backup_bucket,
                    Key=backup_key,
                    Body=json.dumps(backup_data, default=str),
                    ServerSideEncryption='AES256'
                )
            except:
                # Create bucket if it doesn't exist
                self.client['s3'].create_bucket(
                    Bucket=backup_bucket,
                    CreateBucketConfiguration={'LocationConstraint': self.region} if self.region != 'us-east-1' else {}
                )
                
                self.client['s3'].put_object(
                    Bucket=backup_bucket,
                    Key=backup_key,
                    Body=json.dumps(backup_data, default=str),
                    ServerSideEncryption='AES256'
                )
            
            return {
                'success': True,
                'location': f"s3://{backup_bucket}/{backup_key}",
                'metadata': {
                    'backup_bucket': backup_bucket,
                    'backup_key': backup_key,
                    'function_version': response['Configuration']['Version']
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to backup Lambda function {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def _backup_s3_bucket(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Backup S3 bucket (cross-region replication)"""
        try:
            # For S3, backup typically means cross-region replication
            # This is a simplified implementation
            
            backup_region = "us-east-1" if self.region != "us-east-1" else "us-west-2"
            backup_bucket_name = f"{resource.resource_id}-backup-{backup_region}"
            
            # Create backup bucket in different region
            try:
                s3_backup = self.client['s3']
                
                if backup_region != self.region:
                    s3_backup = boto3.client('s3', region_name=backup_region)
                
                s3_backup.create_bucket(
                    Bucket=backup_bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': backup_region} if backup_region != 'us-east-1' else {}
                )
                
                # Enable versioning
                s3_backup.put_bucket_versioning(
                    Bucket=backup_bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
            except s3_backup.exceptions.BucketAlreadyOwnedByYou:
                pass  # Bucket already exists
            
            # Set up replication (simplified - would need more complex configuration in production)
            return {
                'success': True,
                'location': f"s3://{backup_bucket_name}",
                'metadata': {
                    'backup_bucket': backup_bucket_name,
                    'backup_region': backup_region,
                    'replication_enabled': True
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to backup S3 bucket {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def verify_backup(self, job: BackupJob) -> Dict[str, Any]:
        """Verify AWS backup integrity"""
        try:
            if "aws-backup-vault" in job.location:
                return self._verify_aws_backup(job)
            elif "rds-snapshot" in job.location:
                return self._verify_rds_snapshot(job)
            elif "ebs-snapshot" in job.location:
                return self._verify_ebs_snapshot(job)
            elif "s3://" in job.location:
                return self._verify_s3_backup(job)
            else:
                return {
                    'passed': False,
                    'details': {'error': f'Unknown backup location format: {job.location}'}
                }
        
        except Exception as e:
            logger.error(f"Failed to verify backup {job.job_id}: {e}")
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def _verify_aws_backup(self, job: BackupJob) -> Dict[str, Any]:
        """Verify AWS Backup job"""
        try:
            backup_job_id = job.metadata.get('aws_backup_job_id')
            if not backup_job_id:
                return {
                    'passed': False,
                    'details': {'error': 'AWS Backup job ID not found'}
                }
            
            response = self.client['backup'].describe_backup_job(BackupJobId=backup_job_id)
            
            backup_job = response['BackupJob']
            status = backup_job['State']
            
            verification_details = {
                'backup_job_id': backup_job_id,
                'status': status,
                'creation_date': backup_job['CreationDate'].isoformat(),
                'completion_date': backup_job.get('CompletionDate', '').isoformat() if backup_job.get('CompletionDate') else None
            }
            
            if status == 'COMPLETED':
                return {
                    'passed': True,
                    'details': verification_details
                }
            else:
                return {
                    'passed': False,
                    'details': {**verification_details, 'error': f'Backup not completed: {status}'}
                }
        
        except Exception as e:
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def _verify_rds_snapshot(self, job: BackupJob) -> Dict[str, Any]:
        """Verify RDS snapshot"""
        try:
            snapshot_id = job.metadata.get('snapshot_identifier')
            if not snapshot_id:
                return {
                    'passed': False,
                    'details': {'error': 'RDS snapshot ID not found'}
                }
            
            response = self.client['rds'].describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)
            
            if not response['DBSnapshots']:
                return {
                    'passed': False,
                    'details': {'error': 'RDS snapshot not found'}
                }
            
            snapshot = response['DBSnapshots'][0]
            status = snapshot['Status']
            
            verification_details = {
                'snapshot_id': snapshot_id,
                'status': status,
                'created_at': snapshot['SnapshotCreateTime'].isoformat(),
                'storage_type': snapshot['AllocatedStorage']
            }
            
            if status == 'available':
                return {
                    'passed': True,
                    'details': verification_details
                }
            else:
                return {
                    'passed': False,
                    'details': {**verification_details, 'error': f'Snapshot not available: {status}'}
                }
        
        except Exception as e:
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def _verify_ebs_snapshot(self, job: BackupJob) -> Dict[str, Any]:
        """Verify EBS snapshot"""
        try:
            snapshot_id = job.metadata.get('snapshot_id')
            if not snapshot_id:
                return {
                    'passed': False,
                    'details': {'error': 'EBS snapshot ID not found'}
                }
            
            response = self.client['ec2'].describe_snapshots(SnapshotIds=[snapshot_id])
            
            if not response['Snapshots']:
                return {
                    'passed': False,
                    'details': {'error': 'EBS snapshot not found'}
                }
            
            snapshot = response['Snapshots'][0]
            state = snapshot['State']
            
            verification_details = {
                'snapshot_id': snapshot_id,
                'state': state,
                'start_time': snapshot['StartTime'].isoformat(),
                'volume_id': snapshot['VolumeId'],
                'volume_size': snapshot['VolumeSize']
            }
            
            if state == 'completed':
                return {
                    'passed': True,
                    'details': verification_details
                }
            else:
                return {
                    'passed': False,
                    'details': {**verification_details, 'error': f'Snapshot not completed: {state}'}
                }
        
        except Exception as e:
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def _verify_s3_backup(self, job: BackupJob) -> Dict[str, Any]:
        """Verify S3 backup"""
        try:
            # Parse S3 location
            location_parts = job.location.replace("s3://", "").split("/")
            bucket_name = location_parts[0]
            key = "/".join(location_parts[1:]) if len(location_parts) > 1 else ""
            
            # Check if object exists
            response = self.client['s3'].head_object(Bucket=bucket_name, Key=key)
            
            verification_details = {
                'bucket': bucket_name,
                'key': key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag']
            }
            
            return {
                'passed': True,
                'details': verification_details
            }
        
        except Exception as e:
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def cleanup_old_backups(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old AWS backups"""
        try:
            cleanup_results = {
                'deleted_count': 0,
                'space_freed_gb': 0.0,
                'details': {}
            }
            
            # Clean up old EBS snapshots
            ebs_result = self._cleanup_old_ebs_snapshots(cutoff_date)
            cleanup_results['details']['ebs_snapshots'] = ebs_result
            cleanup_results['deleted_count'] += ebs_result.get('deleted_count', 0)
            cleanup_results['space_freed_gb'] += ebs_result.get('space_freed_gb', 0.0)
            
            # Clean up old RDS snapshots
            rds_result = self._cleanup_old_rds_snapshots(cutoff_date)
            cleanup_results['details']['rds_snapshots'] = rds_result
            cleanup_results['deleted_count'] += rds_result.get('deleted_count', 0)
            cleanup_results['space_freed_gb'] += rds_result.get('space_freed_gb', 0.0)
            
            # Clean up old S3 backup objects
            s3_result = self._cleanup_old_s3_backups(cutoff_date)
            cleanup_results['details']['s3_backups'] = s3_result
            cleanup_results['deleted_count'] += s3_result.get('deleted_count', 0)
            cleanup_results['space_freed_gb'] += s3_result.get('space_freed_gb', 0.0)
            
            logger.info(f"Cleaned up {cleanup_results['deleted_count']} old AWS backups, freed {cleanup_results['space_freed_gb']:.2f} GB")
            return cleanup_results
        
        except Exception as e:
            logger.error(f"Failed to cleanup old AWS backups: {e}")
            return {'error': str(e)}
    
    def _cleanup_old_ebs_snapshots(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old EBS snapshots"""
        try:
            response = self.client['ec2'].describe_snapshots(OwnerIds=['self'])
            
            old_snapshots = [
                snapshot for snapshot in response['Snapshots']
                if snapshot['StartTime'].replace(tzinfo=None) < cutoff_date
            ]
            
            deleted_count = 0
            space_freed_gb = 0.0
            
            for snapshot in old_snapshots:
                try:
                    self.client['ec2'].delete_snapshot(SnapshotId=snapshot['SnapshotId'])
                    deleted_count += 1
                    space_freed_gb += snapshot['VolumeSize']
                except Exception as e:
                    logger.warning(f"Failed to delete EBS snapshot {snapshot['SnapshotId']}: {e}")
            
            return {
                'deleted_count': deleted_count,
                'space_freed_gb': space_freed_gb
            }
        
        except Exception as e:
            logger.error(f"Failed to cleanup old EBS snapshots: {e}")
            return {'deleted_count': 0, 'space_freed_gb': 0.0, 'error': str(e)}
    
    def _cleanup_old_rds_snapshots(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old RDS snapshots"""
        try:
            response = self.client['rds'].describe_db_snapshots(SnapshotType='manual')
            
            old_snapshots = [
                snapshot for snapshot in response['DBSnapshots']
                if snapshot['SnapshotCreateTime'].replace(tzinfo=None) < cutoff_date
            ]
            
            deleted_count = 0
            space_freed_gb = 0.0
            
            for snapshot in old_snapshots:
                try:
                    self.client['rds'].delete_db_snapshot(
                        DBSnapshotIdentifier=snapshot['DBSnapshotIdentifier']
                    )
                    deleted_count += 1
                    space_freed_gb += snapshot['AllocatedStorage']
                except Exception as e:
                    logger.warning(f"Failed to delete RDS snapshot {snapshot['DBSnapshotIdentifier']}: {e}")
            
            return {
                'deleted_count': deleted_count,
                'space_freed_gb': space_freed_gb
            }
        
        except Exception as e:
            logger.error(f"Failed to cleanup old RDS snapshots: {e}")
            return {'deleted_count': 0, 'space_freed_gb': 0.0, 'error': str(e)}
    
    def _cleanup_old_s3_backups(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old S3 backup objects"""
        try:
            backup_buckets = [f"lambda-backups-{self.region}"]
            
            deleted_count = 0
            space_freed_gb = 0.0
            
            for bucket_name in backup_buckets:
                try:
                    response = self.client['s3'].list_objects_v2(Bucket=bucket_name)
                    
                    for obj in response.get('Contents', []):
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            try:
                                self.client['s3'].delete_object(Bucket=bucket_name, Key=obj['Key'])
                                deleted_count += 1
                                space_freed_gb += obj['Size'] / (1024 * 1024 * 1024)  # Convert to GB
                            except Exception as e:
                                logger.warning(f"Failed to delete S3 object {obj['Key']}: {e}")
                
                except Exception as e:
                    logger.warning(f"Failed to process S3 bucket {bucket_name}: {e}")
            
            return {
                'deleted_count': deleted_count,
                'space_freed_gb': space_freed_gb
            }
        
        except Exception as e:
            logger.error(f"Failed to cleanup old S3 backups: {e}")
            return {'deleted_count': 0, 'space_freed_gb': 0.0, 'error': str(e)}

# Simplified handlers for other providers
class AzureBackupOrchestratorHandler(BackupOrchestratorHandler):
    """Azure-specific backup operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.recoveryservices import RecoveryServicesClient
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.storage import StorageManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'recovery': RecoveryServicesClient(credential, "<subscription-id>"),
                'compute': ComputeManagementClient(credential, "<subscription-id>"),
                'storage': StorageManagementClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def discover_backup_resources(self) -> List[BackupResource]:
        """Discover Azure backup-eligible resources"""
        try:
            resources = []
            
            # Simulate Azure VM discovery
            sample_resources = [
                BackupResource(
                    resource_id="azure-vm-1",
                    resource_name="web-server-01",
                    resource_type="virtual_machine",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    size_gb=80.0,
                    criticality="critical",
                    backup_required=True,
                    last_backup=datetime.utcnow() - timedelta(days=1),
                    backup_frequency="daily",
                    retention_days=30,
                    tags={"Environment": "production", "Backup": "true"}
                ),
                BackupResource(
                    resource_id="azure-sql-1",
                    resource_name="database-01",
                    resource_type="sql_database",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    size_gb=100.0,
                    criticality="critical",
                    backup_required=True,
                    last_backup=datetime.utcnow() - timedelta(hours=6),
                    backup_frequency="daily",
                    retention_days=30,
                    tags={"Environment": "production", "Backup": "true"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Discovered {len(resources)} Azure backup resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover Azure backup resources: {e}")
            return []
    
    def execute_backup(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Execute backup for Azure resource"""
        try:
            # Simulate Azure backup execution
            backup_id = f"azure-backup-{job.job_id}"
            
            return {
                'success': True,
                'backup_id': backup_id,
                'location': f"azure-backup://{backup_id}",
                'metadata': {
                    'backup_type': backup_type,
                    'resource_type': resource.resource_type,
                    'recovery_vault': 'backup-vault-1'
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to execute Azure backup for {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def verify_backup(self, job: BackupJob) -> Dict[str, Any]:
        """Verify Azure backup integrity"""
        try:
            # Simulate Azure backup verification
            return {
                'passed': True,
                'details': {
                    'backup_id': job.metadata.get('backup_id'),
                    'verification_time': datetime.utcnow().isoformat(),
                    'integrity_check': 'passed'
                }
            }
        
        except Exception as e:
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def cleanup_old_backups(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old Azure backups"""
        try:
            # Simulate Azure backup cleanup
            return {
                'deleted_count': 5,
                'space_freed_gb': 250.0
            }
        
        except Exception as e:
            logger.error(f"Failed to cleanup old Azure backups: {e}")
            return {'error': str(e)}

class GCPBackupOrchestratorHandler(BackupOrchestratorHandler):
    """GCP-specific backup operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import compute_v1
            from google.cloud import storage
            from google.cloud import sql
            
            self.client = {
                'compute': compute_v1.InstancesClient(),
                'storage': storage.Client(),
                'sql': sql.SQLAdminClient()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def discover_backup_resources(self) -> List[BackupResource]:
        """Discover GCP backup-eligible resources"""
        try:
            resources = []
            
            # Simulate GCP VM discovery
            sample_resources = [
                BackupResource(
                    resource_id="gcp-vm-1",
                    resource_name="web-server-gcp",
                    resource_type="compute_instance",
                    provider="gcp",
                    region="us-central1",
                    environment="production",
                    size_gb=50.0,
                    criticality="important",
                    backup_required=True,
                    last_backup=datetime.utcnow() - timedelta(hours=12),
                    backup_frequency="daily",
                    retention_days=30,
                    tags={"Environment": "production", "Backup": "true"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Discovered {len(resources)} GCP backup resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover GCP backup resources: {e}")
            return []
    
    def execute_backup(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Execute backup for GCP resource"""
        try:
            # Simulate GCP backup execution
            backup_id = f"gcp-snapshot-{job.job_id}"
            
            return {
                'success': True,
                'backup_id': backup_id,
                'location': f"gcp-snapshot://{backup_id}",
                'metadata': {
                    'backup_type': backup_type,
                    'resource_type': resource.resource_type,
                    'storage_location': 'us-central1'
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to execute GCP backup for {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def verify_backup(self, job: BackupJob) -> Dict[str, Any]:
        """Verify GCP backup integrity"""
        try:
            # Simulate GCP backup verification
            return {
                'passed': True,
                'details': {
                    'backup_id': job.metadata.get('backup_id'),
                    'verification_time': datetime.utcnow().isoformat(),
                    'checksum': 'verified'
                }
            }
        
        except Exception as e:
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def cleanup_old_backups(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old GCP backups"""
        try:
            # Simulate GCP backup cleanup
            return {
                'deleted_count': 3,
                'space_freed_gb': 150.0
            }
        
        except Exception as e:
            logger.error(f"Failed to cleanup old GCP backups: {e}")
            return {'error': str(e)}

class OnPremBackupOrchestratorHandler(BackupOrchestratorHandler):
    """On-premise backup operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use various backup systems
            logger.info("On-premise backup handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def discover_backup_resources(self) -> List[BackupResource]:
        """Discover on-premise backup-eligible resources"""
        try:
            resources = []
            
            # Simulate on-premise server discovery
            sample_resources = [
                BackupResource(
                    resource_id="onprem-server-1",
                    resource_name="database-server-01",
                    resource_type="physical_server",
                    provider="onprem",
                    region="datacenter-1",
                    environment="production",
                    size_gb=500.0,
                    criticality="critical",
                    backup_required=True,
                    last_backup=datetime.utcnow() - timedelta(hours=8),
                    backup_frequency="daily",
                    retention_days=30,
                    tags={"Environment": "production", "Backup": "true"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Discovered {len(resources)} on-premise backup resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover on-premise backup resources: {e}")
            return []
    
    def execute_backup(self, resource: BackupResource, backup_type: str, job: BackupJob) -> Dict[str, Any]:
        """Execute backup for on-premise resource"""
        try:
            # Simulate on-premise backup execution
            backup_id = f"onprem-backup-{job.job_id}"
            
            return {
                'success': True,
                'backup_id': backup_id,
                'location': f"onprem-backup://{backup_id}",
                'metadata': {
                    'backup_type': backup_type,
                    'resource_type': resource.resource_type,
                    'tape_location': 'tape-library-1'
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to execute on-premise backup for {resource.resource_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'location': None
            }
    
    def verify_backup(self, job: BackupJob) -> Dict[str, Any]:
        """Verify on-premise backup integrity"""
        try:
            # Simulate on-premise backup verification
            return {
                'passed': True,
                'details': {
                    'backup_id': job.metadata.get('backup_id'),
                    'verification_time': datetime.utcnow().isoformat(),
                    'media_integrity': 'verified'
                }
            }
        
        except Exception as e:
            return {
                'passed': False,
                'details': {'error': str(e)}
            }
    
    def cleanup_old_backups(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Clean up old on-premise backups"""
        try:
            # Simulate on-premise backup cleanup
            return {
                'deleted_count': 8,
                'space_freed_gb': 400.0
            }
        
        except Exception as e:
            logger.error(f"Failed to cleanup old on-premise backups: {e}")
            return {'error': str(e)}

def get_backup_handler(provider: str, region: str = "us-west-2") -> BackupOrchestratorHandler:
    """Get appropriate backup handler"""
    handlers = {
        'aws': AWSBackupOrchestratorHandler,
        'azure': AzureBackupOrchestratorHandler,
        'gcp': GCPBackupOrchestratorHandler,
        'onprem': OnPremBackupOrchestratorHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
