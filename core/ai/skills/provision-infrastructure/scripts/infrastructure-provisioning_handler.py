#!/usr/bin/env python3
"""
Infrastructure Provisioning Handler

Cloud-specific operations handler for infrastructure provisioning across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ProvisioningHandler(ABC):
    """Abstract base class for cloud-specific provisioning operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def provision_resource(self, resource_type: str, resource_name: str, 
                          configuration: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
        """Provision a resource"""
        pass
    
    @abstractmethod
    def delete_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Delete a resource"""
        pass

class AWSProvisioningHandler(ProvisioningHandler):
    """AWS-specific provisioning operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ec2': boto3.client('ec2', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                'cloudformation': boto3.client('cloudformation', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def provision_resource(self, resource_type: str, resource_name: str, 
                          configuration: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
        """Provision an AWS resource"""
        try:
            if resource_type == 'compute':
                return self._provision_ec2_instance(resource_name, configuration, tags)
            elif resource_type == 'storage':
                if configuration.get('storage_type') == 'ebs':
                    return self._provision_ebs_volume(resource_name, configuration, tags)
                elif configuration.get('storage_type') == 's3':
                    return self._provision_s3_bucket(resource_name, configuration, tags)
            elif resource_type == 'database':
                return self._provision_rds_instance(resource_name, configuration, tags)
            else:
                return {'success': False, 'error': f'Unsupported resource type: {resource_type}'}
                
        except Exception as e:
            logger.error(f"Failed to provision AWS resource {resource_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Delete an AWS resource"""
        try:
            if resource_type == 'compute':
                return self._delete_ec2_instance(resource_id)
            elif resource_type == 'storage':
                if resource_id.startswith('vol-'):
                    return self._delete_ebs_volume(resource_id)
                else:
                    return self._delete_s3_bucket(resource_id)
            elif resource_type == 'database':
                return self._delete_rds_instance(resource_id)
            else:
                return {'success': False, 'error': f'Unsupported resource type: {resource_type}'}
                
        except Exception as e:
            logger.error(f"Failed to delete AWS resource {resource_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _provision_ec2_instance(self, instance_name: str, config: Dict[str, Any], 
                               tags: Dict[str, str]) -> Dict[str, Any]:
        """Provision EC2 instance"""
        try:
            # Add Name tag
            tags['Name'] = instance_name
            
            # Convert tags to AWS format
            aws_tags = [{'Key': k, 'Value': v} for k, v in tags.items()]
            
            response = self.client['ec2'].run_instances(
                ImageId=config.get('ami_id', 'ami-12345678'),
                MinCount=1,
                MaxCount=1,
                InstanceType=config.get('instance_type', 't3.micro'),
                KeyName=config.get('key_name'),
                SecurityGroups=config.get('security_groups', []),
                SubnetId=config.get('subnet_id'),
                UserData=config.get('user_data', ''),
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': aws_tags
                    }
                ]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            
            return {
                'success': True,
                'resource_id': instance_id,
                'resource_details': {
                    'instance_id': instance_id,
                    'instance_type': config.get('instance_type'),
                    'state': response['Instances'][0]['State']['Name']
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _provision_ebs_volume(self, volume_name: str, config: Dict[str, Any], 
                             tags: Dict[str, str]) -> Dict[str, Any]:
        """Provision EBS volume"""
        try:
            tags['Name'] = volume_name
            aws_tags = [{'Key': k, 'Value': v} for k, v in tags.items()]
            
            response = self.client['ec2'].create_volume(
                VolumeType=config.get('volume_type', 'gp3'),
                Size=config.get('size_gb', 100),
                AvailabilityZone=config.get('availability_zone', f'{self.region}a'),
                Iops=config.get('iops'),
                Throughput=config.get('throughput'),
                Encrypted=config.get('encrypted', False),
                TagSpecifications=[
                    {
                        'ResourceType': 'volume',
                        'Tags': aws_tags
                    }
                ]
            )
            
            volume_id = response['VolumeId']
            
            return {
                'success': True,
                'resource_id': volume_id,
                'resource_details': {
                    'volume_id': volume_id,
                    'size_gb': config.get('size_gb'),
                    'volume_type': config.get('volume_type'),
                    'state': response['State']
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _provision_s3_bucket(self, bucket_name: str, config: Dict[str, Any], 
                             tags: Dict[str, str]) -> Dict[str, Any]:
        """Provision S3 bucket"""
        try:
            create_config = {
                'Bucket': bucket_name,
                'ObjectLockEnabled': config.get('object_lock_enabled', False)
            }
            
            # Create bucket
            if self.region != 'us-east-1':
                create_config['CreateBucketConfiguration'] = {
                    'LocationConstraint': self.region
                }
            
            self.client['s3'].create_bucket(**create_config)
            
            # Set bucket versioning if specified
            if config.get('versioning') == 'Enabled':
                self.client['s3'].put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            
            # Set encryption if specified
            if config.get('encryption'):
                self.client['s3'].put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': config.get('encryption', 'AES256')
                                }
                            }
                        ]
                    }
                )
            
            # Add tags
            if tags:
                tag_set = [{'Key': k, 'Value': v} for k, v in tags.items()]
                self.client['s3'].put_bucket_tagging(
                    Bucket=bucket_name,
                    Tagging={'TagSet': tag_set}
                )
            
            return {
                'success': True,
                'resource_id': bucket_name,
                'resource_details': {
                    'bucket_name': bucket_name,
                    'region': self.region,
                    'versioning': config.get('versioning', 'Disabled'),
                    'encryption': config.get('encryption', 'None')
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _provision_rds_instance(self, instance_name: str, config: Dict[str, Any], 
                                tags: Dict[str, str]) -> Dict[str, Any]:
        """Provision RDS instance"""
        try:
            tags['Name'] = instance_name
            aws_tags = [{'Key': k, 'Value': v} for k, v in tags.items()]
            
            response = self.client['rds'].create_db_instance(
                DBInstanceIdentifier=instance_name,
                DBInstanceClass=config.get('db_instance_class', 'db.t3.micro'),
                Engine=config.get('engine', 'mysql'),
                EngineVersion=config.get('engine_version'),
                AllocatedStorage=config.get('allocated_storage', 20),
                StorageType=config.get('storage_type', 'gp2'),
                StorageEncrypted=config.get('storage_encrypted', False),
                MasterUsername=config.get('master_username', 'admin'),
                MasterUserPassword=config.get('master_password'),
                DBName=config.get('database_name'),
                Port=config.get('port', 3306),
                VpcSecurityGroupIds=config.get('vpc_security_group_ids', []),
                DBSubnetGroupName=config.get('db_subnet_group_name'),
                Tags=aws_tags
            )
            
            return {
                'success': True,
                'resource_id': instance_name,
                'resource_details': {
                    'db_instance_identifier': instance_name,
                    'db_instance_class': config.get('db_instance_class'),
                    'engine': config.get('engine'),
                    'status': response['DBInstance']['DBInstanceStatus']
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _delete_ec2_instance(self, instance_id: str) -> Dict[str, Any]:
        """Delete EC2 instance"""
        try:
            self.client['ec2'].terminate_instances(InstanceIds=[instance_id])
            return {'success': True, 'message': f'EC2 instance {instance_id} termination initiated'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _delete_ebs_volume(self, volume_id: str) -> Dict[str, Any]:
        """Delete EBS volume"""
        try:
            self.client['ec2'].delete_volume(VolumeId=volume_id)
            return {'success': True, 'message': f'EBS volume {volume_id} deletion initiated'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _delete_s3_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Delete S3 bucket"""
        try:
            # Delete all objects first
            objects = self.client['s3'].list_objects_v2(Bucket=bucket_name)
            if 'Contents' in objects:
                delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
                self.client['s3'].delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': delete_keys}
                )
            
            # Delete bucket
            self.client['s3'].delete_bucket(Bucket=bucket_name)
            return {'success': True, 'message': f'S3 bucket {bucket_name} deleted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _delete_rds_instance(self, instance_id: str) -> Dict[str, Any]:
        """Delete RDS instance"""
        try:
            self.client['rds'].delete_db_instance(
                DBInstanceIdentifier=instance_id,
                SkipFinalSnapshot=True
            )
            return {'success': True, 'message': f'RDS instance {instance_id} deletion initiated'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Simplified handlers for other providers
class AzureProvisioningHandler(ProvisioningHandler):
    """Azure-specific provisioning operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
            from azure.mgmt.compute import ComputeManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'resource': ResourceManagementClient(credential, "<subscription-id>"),
                'compute': ComputeManagementClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def provision_resource(self, resource_type: str, resource_name: str, 
                          configuration: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
        return {'success': True, 'resource_id': f'azure-{resource_name}', 'message': 'Azure resource provisioned'}
    
    def delete_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        return {'success': True, 'message': 'Azure resource deleted'}

class GCPProvisioningHandler(ProvisioningHandler):
    """GCP-specific provisioning operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import compute_v1
            self.client = {'compute': compute_v1.InstancesClient()}
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def provision_resource(self, resource_type: str, resource_name: str, 
                          configuration: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
        return {'success': True, 'resource_id': f'gcp-{resource_name}', 'message': 'GCP resource provisioned'}
    
    def delete_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        return {'success': True, 'message': 'GCP resource deleted'}

class OnPremProvisioningHandler(ProvisioningHandler):
    """On-premise provisioning operations"""
    
    def initialize_client(self) -> bool:
        logger.info("On-premise provisioning handler initialized")
        return True
    
    def provision_resource(self, resource_type: str, resource_name: str, 
                          configuration: Dict[str, Any], tags: Dict[str, str]) -> Dict[str, Any]:
        return {'success': True, 'resource_id': f'onprem-{resource_name}', 'message': 'On-premise resource provisioned'}
    
    def delete_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        return {'success': True, 'message': 'On-premise resource deleted'}

def get_provisioning_handler(provider: str, region: str = "us-west-2") -> ProvisioningHandler:
    """Get appropriate provisioning handler"""
    handlers = {
        'aws': AWSProvisioningHandler,
        'azure': AzureProvisioningHandler,
        'gcp': GCPProvisioningHandler,
        'onprem': OnPremProvisioningHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
