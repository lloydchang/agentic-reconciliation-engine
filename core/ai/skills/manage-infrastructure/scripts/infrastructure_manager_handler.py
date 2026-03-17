#!/usr/bin/env python3
"""
Infrastructure Manager Handler

Cloud-specific operations handler for comprehensive infrastructure management across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class InfrastructureResource:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    region: str
    environment: str
    status: str
    created_at: datetime
    updated_at: datetime
    configuration: Dict[str, Any]
    tags: Dict[str, Any]
    dependencies: List[str]
    cost_per_hour: float
    utilization: Dict[str, float]

@dataclass
class InfrastructureOperation:
    operation_id: str
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    operation_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    configuration: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    cost_impact: float

class InfrastructureManagerHandler(ABC):
    """Abstract base class for cloud-specific infrastructure management operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def discover_resources(self, resource_types: Optional[List[str]] = None) -> List[InfrastructureResource]:
        """Discover infrastructure resources"""
        pass
    
    @abstractmethod
    def create_resource(self, resource_type: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Create a new infrastructure resource"""
        pass
    
    @abstractmethod
    def update_resource(self, resource_id: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Update an existing infrastructure resource"""
        pass
    
    @abstractmethod
    def delete_resource(self, resource_id: str) -> InfrastructureOperation:
        """Delete an infrastructure resource"""
        pass
    
    @abstractmethod
    def scale_resource(self, resource_id: str, target_capacity: int) -> InfrastructureOperation:
        """Scale an infrastructure resource"""
        pass
    
    @abstractmethod
    def monitor_resource(self, resource_id: str) -> Dict[str, Any]:
        """Monitor an infrastructure resource"""
        pass

class AWSInfrastructureManagerHandler(InfrastructureManagerHandler):
    """AWS-specific infrastructure management operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ec2': boto3.client('ec2', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region),
                'elb': boto3.client('elbv2', region_name=self.region),
                'cloudformation': boto3.client('cloudformation', region_name=self.region),
                'autoscaling': boto3.client('autoscaling', region_name=self.region),
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
    
    def discover_resources(self, resource_types: Optional[List[str]] = None) -> List[InfrastructureResource]:
        """Discover AWS infrastructure resources"""
        try:
            resources = []
            
            if not resource_types or 'compute' in resource_types:
                compute_resources = self._discover_compute_resources()
                resources.extend(compute_resources)
            
            if not resource_types or 'storage' in resource_types:
                storage_resources = self._discover_storage_resources()
                resources.extend(storage_resources)
            
            if not resource_types or 'networking' in resource_types:
                networking_resources = self._discover_networking_resources()
                resources.extend(networking_resources)
            
            if not resource_types or 'database' in resource_types:
                database_resources = self._discover_database_resources()
                resources.extend(database_resources)
            
            logger.info(f"Discovered {len(resources)} AWS infrastructure resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover AWS infrastructure resources: {e}")
            return []
    
    def _discover_compute_resources(self) -> List[InfrastructureResource]:
        """Discover AWS compute resources"""
        resources = []
        
        try:
            # Get EC2 instances
            response = self.client['ec2'].describe_instances()
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    state = instance['State']['Name']
                    
                    # Get tags
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    # Get utilization metrics
                    utilization = self._get_ec2_utilization(instance_id)
                    
                    resource = InfrastructureResource(
                        resource_id=instance_id,
                        resource_name=tags.get('Name', instance_id),
                        resource_type="ec2_instance",
                        provider="aws",
                        region=self.region,
                        environment=tags.get('Environment', 'unknown'),
                        status=state,
                        created_at=instance['LaunchTime'],
                        updated_at=datetime.utcnow(),
                        configuration={
                            'instance_type': instance_type,
                            'ami_id': instance['ImageId'],
                            'subnet_id': instance.get('SubnetId', ''),
                            'vpc_id': instance.get('VpcId', ''),
                            'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])]
                        },
                        tags=tags,
                        dependencies=self._get_instance_dependencies(instance),
                        cost_per_hour=self._get_ec2_cost(instance_type),
                        utilization=utilization
                    )
                    
                    resources.append(resource)
            
        except Exception as e:
            logger.error(f"Failed to discover EC2 instances: {e}")
        
        return resources
    
    def _discover_storage_resources(self) -> List[InfrastructureResource]:
        """Discover AWS storage resources"""
        resources = []
        
        try:
            # Get EBS volumes
            response = self.client['ec2'].describe_volumes()
            
            for volume in response['Volumes']:
                volume_id = volume['VolumeId']
                volume_type = volume['VolumeType']
                size_gb = volume['Size']
                state = volume['State']
                
                # Get tags
                tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                
                # Get utilization metrics
                utilization = self._get_ebs_utilization(volume_id)
                
                resource = InfrastructureResource(
                    resource_id=volume_id,
                    resource_name=tags.get('Name', volume_id),
                    resource_type="ebs_volume",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    status=state,
                    created_at=volume['CreateTime'],
                    updated_at=datetime.utcnow(),
                    configuration={
                        'volume_type': volume_type,
                        'size_gb': size_gb,
                        'iops': volume.get('Iops', 0),
                        'throughput': volume.get('Throughput', 0),
                        'encrypted': volume.get('Encrypted', False),
                        'availability_zone': volume.get('AvailabilityZone', '')
                    },
                    tags=tags,
                    dependencies=[],
                    cost_per_hour=self._get_ebs_cost(volume_type, size_gb),
                    utilization=utilization
                )
                
                resources.append(resource)
            
            # Get S3 buckets
            s3_response = self.client['s3'].list_buckets()
            
            for bucket in s3_response['Buckets']:
                bucket_name = bucket['Name']
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['s3'].get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tag_response['TagSet']}
                except:
                    pass
                
                # Get utilization metrics
                utilization = self._get_s3_utilization(bucket_name)
                
                resource = InfrastructureResource(
                    resource_id=bucket_name,
                    resource_name=tags.get('Name', bucket_name),
                    resource_type="s3_bucket",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    status="active",
                    created_at=bucket['CreationDate'],
                    updated_at=datetime.utcnow(),
                    configuration={
                        'bucket_name': bucket_name,
                        'versioning': self._get_s3_versioning(bucket_name),
                        'encryption': self._get_s3_encryption(bucket_name),
                        'lifecycle_rules': self._get_s3_lifecycle(bucket_name)
                    },
                    tags=tags,
                    dependencies=[],
                    cost_per_hour=self._get_s3_cost(bucket_name),
                    utilization=utilization
                )
                
                resources.append(resource)
            
        except Exception as e:
            logger.error(f"Failed to discover AWS storage resources: {e}")
        
        return resources
    
    def _discover_networking_resources(self) -> List[InfrastructureResource]:
        """Discover AWS networking resources"""
        resources = []
        
        try:
            # Get VPCs
            response = self.client['ec2'].describe_vpcs()
            
            for vpc in response['Vpcs']:
                vpc_id = vpc['VpcId']
                cidr_block = vpc['CidrBlock']
                state = vpc['State']
                
                # Get tags
                tags = {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
                
                resource = InfrastructureResource(
                    resource_id=vpc_id,
                    resource_name=tags.get('Name', vpc_id),
                    resource_type="vpc",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    status=state,
                    created_at=vpc.get('CreateTime', datetime.utcnow()),
                    updated_at=datetime.utcnow(),
                    configuration={
                        'cidr_block': cidr_block,
                        'is_default': vpc.get('IsDefault', False),
                        'dns_hostnames': vpc.get('DnsHostnames', False),
                        'dns_resolution': vpc.get('DnsResolution', True)
                    },
                    tags=tags,
                    dependencies=[],
                    cost_per_hour=0.0,  # VPCs don't have direct cost
                    utilization={}
                )
                
                resources.append(resource)
            
            # Get Load Balancers
            elb_response = self.client['elb'].describe_load_balancers()
            
            for lb in elb_response['LoadBalancers']:
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                lb_type = lb['Type']
                state = lb['State']['Code']
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['elb'].describe_tags(ResourceArns=[lb_arn])
                    for tag_desc in tag_response['TagDescriptions']:
                        for tag in tag_desc['Tags']:
                            tags[tag['Key']] = tag['Value']
                except:
                    pass
                
                resource = InfrastructureResource(
                    resource_id=lb_arn,
                    resource_name=tags.get('Name', lb_name),
                    resource_type="load_balancer",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    status=state,
                    created_at=lb['CreatedTime'],
                    updated_at=datetime.utcnow(),
                    configuration={
                        'lb_type': lb_type,
                        'scheme': lb['Scheme'],
                        'vpc_id': lb['VpcId'],
                        'subnet_mappings': lb['AvailabilityZones'],
                        'security_groups': lb['SecurityGroups']
                    },
                    tags=tags,
                    dependencies=[],
                    cost_per_hour=self._get_elb_cost(lb_type),
                    utilization=self._get_elb_utilization(lb_arn)
                )
                
                resources.append(resource)
            
        except Exception as e:
            logger.error(f"Failed to discover AWS networking resources: {e}")
        
        return resources
    
    def _discover_database_resources(self) -> List[InfrastructureResource]:
        """Discover AWS database resources"""
        resources = []
        
        try:
            # Get RDS instances
            response = self.client['rds'].describe_db_instances()
            
            for db_instance in response['DBInstances']:
                db_id = db_instance['DBInstanceIdentifier']
                db_engine = db_instance['Engine']
                db_class = db_instance['DBInstanceClass']
                allocated_storage = db_instance['AllocatedStorage']
                status = db_instance['DBInstanceStatus']
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['rds'].list_tags_for_resource(
                        ResourceName=db_instance['DBInstanceArn']
                    )
                    tags = {tag['Key']: tag['Value'] for tag in tag_response['TagList']}
                except:
                    pass
                
                resource = InfrastructureResource(
                    resource_id=db_id,
                    resource_name=tags.get('Name', db_id),
                    resource_type="rds_instance",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    status=status,
                    created_at=db_instance['InstanceCreateTime'],
                    updated_at=datetime.utcnow(),
                    configuration={
                        'engine': db_engine,
                        'engine_version': db_instance['EngineVersion'],
                        'instance_class': db_class,
                        'allocated_storage': allocated_storage,
                        'storage_type': db_instance.get('StorageType', 'gp2'),
                        'multi_az': db_instance.get('MultiAZ', False),
                        'vpc_security_groups': db_instance.get('VpcSecurityGroups', [])
                    },
                    tags=tags,
                    dependencies=[],
                    cost_per_hour=self._get_rds_cost(db_class, allocated_storage),
                    utilization=self._get_rds_utilization(db_id)
                )
                
                resources.append(resource)
            
        except Exception as e:
            logger.error(f"Failed to discover AWS database resources: {e}")
        
        return resources
    
    def _get_ec2_utilization(self, instance_id: str) -> Dict[str, float]:
        """Get EC2 instance utilization metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            datapoints = response.get('Datapoints', [])
            
            if datapoints:
                avg_cpu = statistics.mean(dp['Average'] for dp in datapoints)
                max_cpu = max(dp['Maximum'] for dp in datapoints)
                
                return {
                    'cpu_average': avg_cpu,
                    'cpu_maximum': max_cpu,
                    'cpu_utilization': avg_cpu
                }
            else:
                return {'cpu_average': 0.0, 'cpu_maximum': 0.0, 'cpu_utilization': 0.0}
        
        except Exception as e:
            logger.error(f"Failed to get EC2 utilization for {instance_id}: {e}")
            return {'cpu_average': 0.0, 'cpu_maximum': 0.0, 'cpu_utilization': 0.0}
    
    def _get_ebs_utilization(self, volume_id: str) -> Dict[str, float]:
        """Get EBS volume utilization metrics"""
        try:
            # EBS utilization is based on IOPS and throughput
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            # Get volume read/write operations
            read_response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeReadOps',
                Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            write_response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeWriteOps',
                Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            read_ops = sum(dp['Sum'] for dp in read_response.get('Datapoints', []))
            write_ops = sum(dp['Sum'] for dp in write_response.get('Datapoints', []))
            
            total_ops = read_ops + write_ops
            avg_ops_per_hour = total_ops / 24 if total_ops > 0 else 0
            
            return {
                'read_ops': read_ops,
                'write_ops': write_ops,
                'total_ops': total_ops,
                'ops_per_hour': avg_ops_per_hour,
                'utilization': min(avg_ops_per_hour / 1000 * 100, 100) if avg_ops_per_hour > 0 else 0.0
            }
        
        except Exception as e:
            logger.error(f"Failed to get EBS utilization for {volume_id}: {e}")
            return {'read_ops': 0.0, 'write_ops': 0.0, 'total_ops': 0.0, 'ops_per_hour': 0.0, 'utilization': 0.0}
    
    def _get_s3_utilization(self, bucket_name: str) -> Dict[str, float]:
        """Get S3 bucket utilization metrics"""
        try:
            # This is a simplified implementation
            # In production, you would use CloudWatch metrics or S3 Inventory
            import random
            
            size_gb = random.uniform(10, 500)
            object_count = random.uniform(1000, 100000)
            
            return {
                'size_gb': size_gb,
                'object_count': object_count,
                'average_object_size': size_gb * 1024 / object_count if object_count > 0 else 0.0,
                'utilization': min(size_gb / 1000 * 100, 100)  # Assume 1TB as baseline
            }
        
        except Exception as e:
            logger.error(f"Failed to get S3 utilization for {bucket_name}: {e}")
            return {'size_gb': 0.0, 'object_count': 0.0, 'average_object_size': 0.0, 'utilization': 0.0}
    
    def _get_elb_utilization(self, lb_arn: str) -> Dict[str, float]:
        """Get ELB utilization metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            # Get request count
            response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='RequestCount',
                Dimensions=[{'Name': 'LoadBalancer', 'Value': lb_arn.split('/')[-1]}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            total_requests = sum(dp['Sum'] for dp in datapoints)
            avg_requests_per_hour = total_requests / 24 if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'requests_per_hour': avg_requests_per_hour,
                'utilization': min(avg_requests_per_hour / 10000 * 100, 100)  # Assume 10k req/hr as baseline
            }
        
        except Exception as e:
            logger.error(f"Failed to get ELB utilization for {lb_arn}: {e}")
            return {'total_requests': 0.0, 'requests_per_hour': 0.0, 'utilization': 0.0}
    
    def _get_rds_utilization(self, db_id: str) -> Dict[str, float]:
        """Get RDS instance utilization metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            datapoints = response.get('Datapoints', [])
            
            if datapoints:
                avg_cpu = statistics.mean(dp['Average'] for dp in datapoints)
                max_cpu = max(dp['Maximum'] for dp in datapoints)
                
                return {
                    'cpu_average': avg_cpu,
                    'cpu_maximum': max_cpu,
                    'cpu_utilization': avg_cpu
                }
            else:
                return {'cpu_average': 0.0, 'cpu_maximum': 0.0, 'cpu_utilization': 0.0}
        
        except Exception as e:
            logger.error(f"Failed to get RDS utilization for {db_id}: {e}")
            return {'cpu_average': 0.0, 'cpu_maximum': 0.0, 'cpu_utilization': 0.0}
    
    def _get_instance_dependencies(self, instance: Dict[str, Any]) -> List[str]:
        """Get instance dependencies"""
        dependencies = []
        
        # Security groups
        for sg in instance.get('SecurityGroups', []):
            dependencies.append(f"sg-{sg['GroupId']}")
        
        # Subnet
        if 'SubnetId' in instance:
            dependencies.append(f"subnet-{instance['SubnetId']}")
        
        # VPC
        if 'VpcId' in instance:
            dependencies.append(f"vpc-{instance['VpcId']}")
        
        return dependencies
    
    def _get_ec2_cost(self, instance_type: str) -> float:
        """Get EC2 instance cost per hour"""
        # Simplified pricing - in production, use AWS Pricing API
        pricing = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'm5.4xlarge': 0.768,
            'c5.large': 0.085,
            'c5.xlarge': 0.170,
            'c5.2xlarge': 0.340,
            'c5.4xlarge': 0.680,
            'r5.large': 0.126,
            'r5.xlarge': 0.252,
            'r5.2xlarge': 0.504,
            'r5.4xlarge': 1.008
        }
        
        return pricing.get(instance_type, 0.192)
    
    def _get_ebs_cost(self, volume_type: str, size_gb: float) -> float:
        """Get EBS volume cost per hour"""
        pricing = {
            'gp2': 0.10,  # $0.10 per GB-month
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.025
        }
        
        price_per_gb_month = pricing.get(volume_type, 0.10)
        return price_per_gb_month * size_gb / 730  # Convert to per hour
    
    def _get_s3_cost(self, bucket_name: str) -> float:
        """Get S3 bucket cost per hour"""
        # This is a simplified implementation
        # In production, you would calculate based on actual usage
        return 0.023 / 730  # $0.023 per GB-month, convert to per hour
    
    def _get_elb_cost(self, lb_type: str) -> float:
        """Get ELB cost per hour"""
        pricing = {
            'application': 0.0225,
            'network': 0.0225,
            'gateway': 0.0225,
            'classic': 0.0225
        }
        
        return pricing.get(lb_type.lower(), 0.0225)
    
    def _get_rds_cost(self, instance_class: str, storage_gb: float) -> float:
        """Get RDS instance cost per hour"""
        # Simplified pricing
        instance_pricing = {
            'db.t3.micro': 0.0116,
            'db.t3.small': 0.023,
            'db.t3.medium': 0.046,
            'db.t3.large': 0.092,
            'db.m5.large': 0.193,
            'db.m5.xlarge': 0.386,
            'db.m5.2xlarge': 0.772,
            'db.m5.4xlarge': 1.544,
            'db.r5.large': 0.215,
            'db.r5.xlarge': 0.430,
            'db.r5.2xlarge': 0.860,
            'db.r5.4xlarge': 1.720
        }
        
        storage_pricing = 0.115  # $0.115 per GB-month for General Purpose SSD
        
        instance_cost = instance_pricing.get(instance_class, 0.193)
        storage_cost = storage_pricing * storage_gb / 730  # Convert to per hour
        
        return instance_cost + storage_cost
    
    def _get_s3_versioning(self, bucket_name: str) -> str:
        """Get S3 bucket versioning status"""
        try:
            response = self.client['s3'].get_bucket_versioning(Bucket=bucket_name)
            return response.get('Status', 'Disabled')
        except:
            return 'Disabled'
    
    def _get_s3_encryption(self, bucket_name: str) -> str:
        """Get S3 bucket encryption status"""
        try:
            response = self.client['s3'].get_bucket_encryption(Bucket=bucket_name)
            return response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [{}])[0].get('ApplyServerSideEncryptionByDefault', {}).get('SSEAlgorithm', 'None')
        except:
            return 'None'
    
    def _get_s3_lifecycle(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Get S3 bucket lifecycle rules"""
        try:
            response = self.client['s3'].get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return response.get('Rules', [])
        except:
            return []
    
    def create_resource(self, resource_type: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Create a new AWS infrastructure resource"""
        operation_id = f"create-{resource_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            if resource_type == "ec2_instance":
                result = self._create_ec2_instance(configuration)
            elif resource_type == "s3_bucket":
                result = self._create_s3_bucket(configuration)
            elif resource_type == "rds_instance":
                result = self._create_rds_instance(configuration)
            elif resource_type == "load_balancer":
                result = self._create_load_balancer(configuration)
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
            
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=result.get('resource_id', ''),
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="aws",
                operation_type="create",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=result,
                error=None,
                cost_impact=result.get('cost_per_hour', 0.0)
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id='',
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="aws",
                operation_type="create",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def _create_ec2_instance(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Create EC2 instance"""
        try:
            response = self.client['ec2'].run_instances(
                ImageId=configuration['image_id'],
                MinCount=1,
                MaxCount=1,
                InstanceType=configuration['instance_type'],
                KeyName=configuration.get('key_name'),
                SecurityGroupIds=configuration.get('security_group_ids', []),
                SubnetId=configuration.get('subnet_id'),
                UserData=configuration.get('user_data', ''),
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': configuration['name']},
                            {'Key': 'Environment', 'Value': configuration.get('environment', 'unknown')}
                        ]
                    }
                ]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            
            return {
                'resource_id': instance_id,
                'instance_id': instance_id,
                'cost_per_hour': self._get_ec2_cost(configuration['instance_type'])
            }
            
        except Exception as e:
            logger.error(f"Failed to create EC2 instance: {e}")
            raise
    
    def _create_s3_bucket(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Create S3 bucket"""
        try:
            bucket_name = configuration['name']
            
            # Create bucket
            if self.region != 'us-east-1':
                self.client['s3'].create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            else:
                self.client['s3'].create_bucket(Bucket=bucket_name)
            
            # Set versioning if specified
            if configuration.get('versioning', False):
                self.client['s3'].put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            
            # Set encryption if specified
            if configuration.get('encryption', 's3'):
                self.client['s3'].put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': configuration['encryption']
                                }
                            }
                        ]
                    }
                )
            
            # Add tags
            if 'tags' in configuration:
                self.client['s3'].put_bucket_tagging(
                    Bucket=bucket_name,
                    Tagging={
                        'TagSet': [
                            {'Key': key, 'Value': value}
                            for key, value in configuration['tags'].items()
                        ]
                    }
                )
            
            return {
                'resource_id': bucket_name,
                'bucket_name': bucket_name,
                'cost_per_hour': self._get_s3_cost(bucket_name)
            }
            
        except Exception as e:
            logger.error(f"Failed to create S3 bucket: {e}")
            raise
    
    def _create_rds_instance(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Create RDS instance"""
        try:
            response = self.client['rds'].create_db_instance(
                DBInstanceIdentifier=configuration['name'],
                DBInstanceClass=configuration['instance_class'],
                Engine=configuration['engine'],
                EngineVersion=configuration.get('engine_version'),
                MasterUsername=configuration['master_username'],
                MasterUserPassword=configuration['master_password'],
                AllocatedStorage=configuration['allocated_storage'],
                StorageType=configuration.get('storage_type', 'gp2'),
                VpcSecurityGroupIds=configuration.get('security_group_ids', []),
                DBSubnetGroupName=configuration.get('subnet_group_name'),
                Tags=[
                    {'Key': 'Name', 'Value': configuration['name']},
                    {'Key': 'Environment', 'Value': configuration.get('environment', 'unknown')}
                ]
            )
            
            return {
                'resource_id': configuration['name'],
                'db_instance_identifier': configuration['name'],
                'cost_per_hour': self._get_rds_cost(configuration['instance_class'], configuration['allocated_storage'])
            }
            
        except Exception as e:
            logger.error(f"Failed to create RDS instance: {e}")
            raise
    
    def _create_load_balancer(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Create Load Balancer"""
        try:
            response = self.client['elb'].create_load_balancer(
                Name=configuration['name'],
                Subnets=configuration['subnets'],
                SecurityGroups=configuration.get('security_groups', []),
                Scheme=configuration.get('scheme', 'internet-facing'),
                Type=configuration.get('type', 'application'),
                Tags=[
                    {'Key': 'Name', 'Value': configuration['name']},
                    {'Key': 'Environment', 'Value': configuration.get('environment', 'unknown')}
                ]
            )
            
            lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
            
            return {
                'resource_id': lb_arn,
                'load_balancer_arn': lb_arn,
                'cost_per_hour': self._get_elb_cost(configuration.get('type', 'application'))
            }
            
        except Exception as e:
            logger.error(f"Failed to create Load Balancer: {e}")
            raise
    
    def update_resource(self, resource_id: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Update an existing AWS infrastructure resource"""
        operation_id = f"update-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # This is a simplified implementation
            # In production, you would determine resource type from resource_id and update accordingly
            
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="aws",
                operation_type="update",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result={'message': 'Resource updated successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="aws",
                operation_type="update",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def delete_resource(self, resource_id: str) -> InfrastructureOperation:
        """Delete an AWS infrastructure resource"""
        operation_id = f"delete-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # This is a simplified implementation
            # In production, you would determine resource type from resource_id and delete accordingly
            
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="aws",
                operation_type="delete",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result={'message': 'Resource deleted successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="aws",
                operation_type="delete",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def scale_resource(self, resource_id: str, target_capacity: int) -> InfrastructureOperation:
        """Scale an AWS infrastructure resource"""
        operation_id = f"scale-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # This is a simplified implementation
            # In production, you would determine resource type and scale accordingly
            
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="aws",
                operation_type="scale",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result={'message': 'Resource scaled successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="aws",
                operation_type="scale",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def monitor_resource(self, resource_id: str) -> Dict[str, Any]:
        """Monitor an AWS infrastructure resource"""
        try:
            # This is a simplified implementation
            # In production, you would get detailed monitoring data
            
            return {
                'resource_id': resource_id,
                'status': 'healthy',
                'metrics': {
                    'cpu_utilization': 45.0,
                    'memory_utilization': 60.0,
                    'network_utilization': 25.0
                },
                'alerts': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor resource {resource_id}: {e}")
            return {
                'resource_id': resource_id,
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }

# Simplified handlers for other providers
class AzureInfrastructureManagerHandler(InfrastructureManagerHandler):
    """Azure-specific infrastructure management operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.storage import StorageManagementClient
            from azure.mgmt.sql import SqlManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'resource': ResourceManagementClient(credential, "<subscription-id>"),
                'compute': ComputeManagementClient(credential, "<subscription-id>"),
                'storage': StorageManagementClient(credential, "<subscription-id>"),
                'sql': SqlManagementClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def discover_resources(self, resource_types: Optional[List[str]] = None) -> List[InfrastructureResource]:
        """Discover Azure infrastructure resources"""
        try:
            resources = []
            
            # Simulate Azure resource discovery
            sample_resources = [
                InfrastructureResource(
                    resource_id="azure-vm-1",
                    resource_name="web-server-01",
                    resource_type="virtual_machine",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    status="running",
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow(),
                    configuration={'vm_size': 'Standard_D2s_v3', 'os_type': 'Linux'},
                    tags={'Environment': 'production', 'Team': 'platform'},
                    dependencies=[],
                    cost_per_hour=0.192,
                    utilization={'cpu': 35.0, 'memory': 45.0}
                ),
                InfrastructureResource(
                    resource_id="azure-storage-1",
                    resource_name="data-storage-01",
                    resource_type="storage_account",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    status="active",
                    created_at=datetime.utcnow() - timedelta(days=60),
                    updated_at=datetime.utcnow(),
                    configuration={'account_type': 'Standard_LRS', 'tier': 'Hot'},
                    tags={'Environment': 'production', 'DataClassification': 'confidential'},
                    dependencies=[],
                    cost_per_hour=0.023,
                    utilization={'size_gb': 250.0, 'utilization': 60.0}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Discovered {len(resources)} Azure infrastructure resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover Azure infrastructure resources: {e}")
            return []
    
    def create_resource(self, resource_type: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Create a new Azure infrastructure resource"""
        operation_id = f"create-{resource_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # Simulate Azure resource creation
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=f"azure-{resource_type}-{operation_id}",
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="azure",
                operation_type="create",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result={'message': 'Azure resource created successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id='',
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="azure",
                operation_type="create",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def update_resource(self, resource_id: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Update an existing Azure infrastructure resource"""
        operation_id = f"update-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="azure",
                operation_type="update",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result={'message': 'Azure resource updated successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="azure",
                operation_type="update",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def delete_resource(self, resource_id: str) -> InfrastructureOperation:
        """Delete an Azure infrastructure resource"""
        operation_id = f"delete-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="azure",
                operation_type="delete",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result={'message': 'Azure resource deleted successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="azure",
                operation_type="delete",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def scale_resource(self, resource_id: str, target_capacity: int) -> InfrastructureOperation:
        """Scale an Azure infrastructure resource"""
        operation_id = f"scale-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="azure",
                operation_type="scale",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result={'message': 'Azure resource scaled successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="azure",
                operation_type="scale",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def monitor_resource(self, resource_id: str) -> Dict[str, Any]:
        """Monitor an Azure infrastructure resource"""
        try:
            return {
                'resource_id': resource_id,
                'status': 'healthy',
                'metrics': {
                    'cpu_utilization': 40.0,
                    'memory_utilization': 55.0,
                    'network_utilization': 30.0
                },
                'alerts': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor Azure resource {resource_id}: {e}")
            return {
                'resource_id': resource_id,
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }

class GCPInfrastructureManagerHandler(InfrastructureManagerHandler):
    """GCP-specific infrastructure management operations"""
    
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
    
    def discover_resources(self, resource_types: Optional[List[str]] = None) -> List[InfrastructureResource]:
        """Discover GCP infrastructure resources"""
        try:
            resources = []
            
            # Simulate GCP resource discovery
            sample_resources = [
                InfrastructureResource(
                    resource_id="gcp-vm-1",
                    resource_name="web-server-gcp",
                    resource_type="compute_instance",
                    provider="gcp",
                    region="us-central1",
                    environment="production",
                    status="running",
                    created_at=datetime.utcnow() - timedelta(days=45),
                    updated_at=datetime.utcnow(),
                    configuration={'machine_type': 'n1-standard-2', 'zone': 'us-central1-a'},
                    tags={'Environment': 'production', 'Project': 'platform'},
                    dependencies=[],
                    cost_per_hour=0.190,
                    utilization={'cpu': 42.0, 'memory': 48.0}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Discovered {len(resources)} GCP infrastructure resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover GCP infrastructure resources: {e}")
            return []
    
    def create_resource(self, resource_type: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Create a new GCP infrastructure resource"""
        operation_id = f"create-{resource_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=f"gcp-{resource_type}-{operation_id}",
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="gcp",
                operation_type="create",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result={'message': 'GCP resource created successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id='',
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="gcp",
                operation_type="create",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def update_resource(self, resource_id: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Update an existing GCP infrastructure resource"""
        operation_id = f"update-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="gcp",
                operation_type="update",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result={'message': 'GCP resource updated successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="gcp",
                operation_type="update",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def delete_resource(self, resource_id: str) -> InfrastructureOperation:
        """Delete a GCP infrastructure resource"""
        operation_id = f"delete-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="gcp",
                operation_type="delete",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result={'message': 'GCP resource deleted successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="gcp",
                operation_type="delete",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def scale_resource(self, resource_id: str, target_capacity: int) -> InfrastructureOperation:
        """Scale a GCP infrastructure resource"""
        operation_id = f"scale-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="gcp",
                operation_type="scale",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result={'message': 'GCP resource scaled successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="gcp",
                operation_type="scale",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def monitor_resource(self, resource_id: str) -> Dict[str, Any]:
        """Monitor a GCP infrastructure resource"""
        try:
            return {
                'resource_id': resource_id,
                'status': 'healthy',
                'metrics': {
                    'cpu_utilization': 38.0,
                    'memory_utilization': 52.0,
                    'network_utilization': 28.0
                },
                'alerts': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor GCP resource {resource_id}: {e}")
            return {
                'resource_id': resource_id,
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }

class OnPremInfrastructureManagerHandler(InfrastructureManagerHandler):
    """On-premise infrastructure management operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use various management systems
            logger.info("On-premise infrastructure manager handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def discover_resources(self, resource_types: Optional[List[str]] = None) -> List[InfrastructureResource]:
        """Discover on-premise infrastructure resources"""
        try:
            resources = []
            
            # Simulate on-premise resource discovery
            sample_resources = [
                InfrastructureResource(
                    resource_id="onprem-server-1",
                    resource_name="database-server-01",
                    resource_type="physical_server",
                    provider="onprem",
                    region="datacenter-1",
                    environment="production",
                    status="running",
                    created_at=datetime.utcnow() - timedelta(days=365),
                    updated_at=datetime.utcnow(),
                    configuration={'cpu_cores': 16, 'memory_gb': 64, 'storage_gb': 2000},
                    tags={'Environment': 'production', 'Location': 'rack-a1'},
                    dependencies=[],
                    cost_per_hour=0.050,
                    utilization={'cpu': 68.0, 'memory': 75.0, 'storage': 72.0}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Discovered {len(resources)} on-premise infrastructure resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to discover on-premise infrastructure resources: {e}")
            return []
    
    def create_resource(self, resource_type: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Create a new on-premise infrastructure resource"""
        operation_id = f"create-{resource_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=f"onprem-{resource_type}-{operation_id}",
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="onprem",
                operation_type="create",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result={'message': 'On-premise resource created successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id='',
                resource_name=configuration.get('name', ''),
                resource_type=resource_type,
                provider="onprem",
                operation_type="create",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def update_resource(self, resource_id: str, configuration: Dict[str, Any]) -> InfrastructureOperation:
        """Update an existing on-premise infrastructure resource"""
        operation_id = f"update-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="onprem",
                operation_type="update",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result={'message': 'On-premise resource updated successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="onprem",
                operation_type="update",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration=configuration,
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def delete_resource(self, resource_id: str) -> InfrastructureOperation:
        """Delete an on-premise infrastructure resource"""
        operation_id = f"delete-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="onprem",
                operation_type="delete",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result={'message': 'On-premise resource deleted successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="onprem",
                operation_type="delete",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def scale_resource(self, resource_id: str, target_capacity: int) -> InfrastructureOperation:
        """Scale an on-premise infrastructure resource"""
        operation_id = f"scale-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="onprem",
                operation_type="scale",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result={'message': 'On-premise resource scaled successfully'},
                error=None,
                cost_impact=0.0
            )
            
        except Exception as e:
            return InfrastructureOperation(
                operation_id=operation_id,
                resource_id=resource_id,
                resource_name='',
                resource_type='',
                provider="onprem",
                operation_type="scale",
                status="failed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                configuration={'target_capacity': target_capacity},
                result=None,
                error=str(e),
                cost_impact=0.0
            )
    
    def monitor_resource(self, resource_id: str) -> Dict[str, Any]:
        """Monitor an on-premise infrastructure resource"""
        try:
            return {
                'resource_id': resource_id,
                'status': 'healthy',
                'metrics': {
                    'cpu_utilization': 55.0,
                    'memory_utilization': 70.0,
                    'storage_utilization': 65.0
                },
                'alerts': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor on-premise resource {resource_id}: {e}")
            return {
                'resource_id': resource_id,
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }

def get_infrastructure_manager_handler(provider: str, region: str = "us-west-2") -> InfrastructureManagerHandler:
    """Get appropriate infrastructure manager handler"""
    handlers = {
        'aws': AWSInfrastructureManagerHandler,
        'azure': AzureInfrastructureManagerHandler,
        'gcp': GCPInfrastructureManagerHandler,
        'onprem': OnPremInfrastructureManagerHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
