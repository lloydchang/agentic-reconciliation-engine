#!/usr/bin/env python3
"""
Capacity Planning Handler

Cloud-specific operations handler for capacity planning across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ResourceCapacity:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    current_capacity: float
    current_utilization: float
    projected_utilization: float
    utilization_trend: List[float]
    capacity_unit: str
    cost_per_unit: float
    region: str

class CapacityHandler(ABC):
    """Abstract base class for cloud-specific capacity operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get compute capacity information"""
        pass
    
    @abstractmethod
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get storage capacity information"""
        pass
    
    @abstractmethod
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get networking capacity information"""
        pass
    
    @abstractmethod
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get database capacity information"""
        pass
    
    @abstractmethod
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get memory capacity information"""
        pass

class AWSCapacityHandler(CapacityHandler):
    """AWS-specific capacity operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ec2': boto3.client('ec2', region_name=self.region),
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                'elasticache': boto3.client('elasticache', region_name=self.region),
                'autoscaling': boto3.client('autoscaling', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get AWS compute capacity information"""
        try:
            capacities = []
            
            # Get EC2 instances
            instances_response = self.client['ec2'].describe_instances()
            
            for reservation in instances_response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        # Get utilization metrics
                        utilization = self._get_ec2_utilization(instance['InstanceId'])
                        
                        capacity = ResourceCapacity(
                            resource_id=instance['InstanceId'],
                            resource_name=self._get_resource_name(instance.get('Tags', []), instance['InstanceId']),
                            resource_type='compute',
                            provider='aws',
                            current_capacity=self._get_instance_vcpus(instance['InstanceType']),
                            current_utilization=utilization['current'],
                            projected_utilization=utilization['projected'],
                            utilization_trend=utilization['trend'],
                            capacity_unit='vCPUs',
                            cost_per_unit=self._get_instance_cost_per_vcpu(instance['InstanceType']),
                            region=self.region
                        )
                        capacities.append(capacity)
            
            return capacities
            
        except Exception as e:
            logger.error(f"Failed to get AWS compute capacity: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get AWS storage capacity information"""
        try:
            capacities = []
            
            # Get EBS volumes
            volumes_response = self.client['ec2'].describe_volumes()
            
            for volume in volumes_response['Volumes']:
                if volume['State'] == 'in-use':
                    # Get utilization metrics
                    utilization = self._get_ebs_utilization(volume['VolumeId'])
                    
                    capacity = ResourceCapacity(
                        resource_id=volume['VolumeId'],
                        resource_name=self._get_resource_name(volume.get('Tags', []), volume['VolumeId']),
                        resource_type='storage',
                        provider='aws',
                        current_capacity=volume['Size'],
                        current_utilization=utilization['current'],
                        projected_utilization=utilization['projected'],
                        utilization_trend=utilization['trend'],
                        capacity_unit='GB',
                        cost_per_unit=self._get_ebs_cost_per_gb(volume['VolumeType']),
                        region=self.region
                    )
                    capacities.append(capacity)
            
            return capacities
            
        except Exception as e:
            logger.error(f"Failed to get AWS storage capacity: {e}")
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get AWS networking capacity information"""
        try:
            capacities = []
            
            # Get VPCs and their network usage
            vpcs_response = self.client['ec2'].describe_vpcs()
            
            for vpc in vpcs_response['Vpcs']:
                # Get network utilization (simplified)
                utilization = self._get_vpc_network_utilization(vpc['VpcId'])
                
                capacity = ResourceCapacity(
                    resource_id=vpc['VpcId'],
                    resource_name=self._get_resource_name(vpc.get('Tags', []), vpc['VpcId']),
                    resource_type='networking',
                    provider='aws',
                    current_capacity=10000.0,  # Simplified bandwidth capacity
                    current_utilization=utilization['current'],
                    projected_utilization=utilization['projected'],
                    utilization_trend=utilization['trend'],
                    capacity_unit='Mbps',
                    cost_per_unit=0.01,  # Simplified cost per Mbps
                    region=self.region
                )
                capacities.append(capacity)
            
            return capacities
            
        except Exception as e:
            logger.error(f"Failed to get AWS networking capacity: {e}")
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get AWS database capacity information"""
        try:
            capacities = []
            
            # Get RDS instances
            rds_response = self.client['rds'].describe_db_instances()
            
            for db_instance in rds_response['DBInstances']:
                if db_instance['DBInstanceStatus'] == 'available':
                    # Get utilization metrics
                    utilization = self._get_rds_utilization(db_instance['DBInstanceIdentifier'])
                    
                    capacity = ResourceCapacity(
                        resource_id=db_instance['DBInstanceIdentifier'],
                        resource_name=db_instance['DBInstanceIdentifier'],
                        resource_type='database',
                        provider='aws',
                        current_capacity=self._get_rds_capacity_units(db_instance['DBInstanceClass']),
                        current_utilization=utilization['current'],
                        projected_utilization=utilization['projected'],
                        utilization_trend=utilization['trend'],
                        capacity_unit='DB Units',
                        cost_per_unit=self._get_rds_cost_per_unit(db_instance['DBInstanceClass']),
                        region=self.region
                    )
                    capacities.append(capacity)
            
            return capacities
            
        except Exception as e:
            logger.error(f"Failed to get AWS database capacity: {e}")
            return []
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get AWS memory capacity information"""
        try:
            capacities = []
            
            # Get ElastiCache clusters
            cache_response = self.client['elasticache'].describe_cache_clusters()
            
            for cache_cluster in cache_response['CacheClusters']:
                if cache_cluster['CacheClusterStatus'] == 'available':
                    # Get utilization metrics
                    utilization = self._get_elasticache_utilization(cache_cluster['CacheClusterId'])
                    
                    capacity = ResourceCapacity(
                        resource_id=cache_cluster['CacheClusterId'],
                        resource_name=cache_cluster['CacheClusterId'],
                        resource_type='memory',
                        provider='aws',
                        current_capacity=self._get_elasticache_memory_gb(cache_cluster['Engine'], cache_cluster['CacheNodeType']),
                        current_utilization=utilization['current'],
                        projected_utilization=utilization['projected'],
                        utilization_trend=utilization['trend'],
                        capacity_unit='GB',
                        cost_per_unit=self._get_elasticache_cost_per_gb(cache_cluster['Engine'], cache_cluster['CacheNodeType']),
                        region=self.region
                    )
                    capacities.append(capacity)
            
            return capacities
            
        except Exception as e:
            logger.error(f"Failed to get AWS memory capacity: {e}")
            return []
    
    def _get_resource_name(self, tags: List[Dict], default_name: str) -> str:
        """Extract resource name from tags"""
        for tag in tags:
            if tag['Key'] == 'Name':
                return tag['Value']
        return default_name
    
    def _get_instance_vcpus(self, instance_type: str) -> float:
        """Get vCPU count for instance type"""
        vcpu_mapping = {
            't3.micro': 2, 't3.small': 2, 't3.medium': 2, 't3.large': 2, 't3.xlarge': 4,
            't3a.micro': 2, 't3a.small': 2, 't3a.medium': 2, 't3a.large': 2,
            'm5.large': 2, 'm5.xlarge': 4, 'm5.2xlarge': 8, 'm5.4xlarge': 16,
            'c5.large': 2, 'c5.xlarge': 4, 'c5.2xlarge': 8, 'c5.4xlarge': 16,
            'r5.large': 2, 'r5.xlarge': 4, 'r5.2xlarge': 8, 'r5.4xlarge': 16
        }
        return vcpu_mapping.get(instance_type, 2)
    
    def _get_instance_cost_per_vcpu(self, instance_type: str) -> float:
        """Get cost per vCPU for instance type"""
        # Simplified hourly cost per vCPU
        cost_mapping = {
            't3.micro': 0.0052, 't3.small': 0.0104, 't3.medium': 0.0208, 't3.large': 0.0416,
            't3a.micro': 0.0047, 't3a.small': 0.0094, 't3a.medium': 0.0188, 't3a.large': 0.0376,
            'm5.large': 0.048, 'm5.xlarge': 0.096, 'm5.2xlarge': 0.192, 'm5.4xlarge': 0.384,
            'c5.large': 0.0416, 'c5.xlarge': 0.0832, 'c5.2xlarge': 0.1664, 'c5.4xlarge': 0.3328,
            'r5.large': 0.054, 'r5.xlarge': 0.108, 'r5.2xlarge': 0.216, 'r5.4xlarge': 0.432
        }
        return cost_mapping.get(instance_type, 0.05)
    
    def _get_ec2_utilization(self, instance_id: str) -> Dict[str, Any]:
        """Get EC2 instance utilization metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            # Get CPU utilization
            cpu_response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600 * 24,  # Daily
                Statistics=['Average']
            )
            
            cpu_data = [dp['Average'] for dp in cpu_response['Datapoints']]
            
            # Calculate trend and projection
            if len(cpu_data) >= 7:
                recent_avg = sum(cpu_data[-7:]) / 7
                older_avg = sum(cpu_data[:-7]) / len(cpu_data[:-7]) if len(cpu_data) > 7 else recent_avg
                growth_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
                projected = recent_avg * (1 + growth_rate / 100 * 3)  # 3-month projection
            else:
                recent_avg = sum(cpu_data) / len(cpu_data) if cpu_data else 50
                growth_rate = 0
                projected = recent_avg
            
            return {
                'current': recent_avg,
                'projected': min(projected, 100),  # Cap at 100%
                'trend': cpu_data[-10:] if len(cpu_data) >= 10 else cpu_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get EC2 utilization for {instance_id}: {e}")
            return {'current': 50, 'projected': 50, 'trend': [50]}
    
    def _get_ebs_utilization(self, volume_id: str) -> Dict[str, Any]:
        """Get EBS volume utilization metrics"""
        try:
            # Simplified EBS utilization (would need CloudWatch metrics in real implementation)
            return {
                'current': 65.0,
                'projected': 72.5,
                'trend': [60, 62, 65, 68, 65, 70, 65]
            }
        except Exception as e:
            logger.error(f"Failed to get EBS utilization for {volume_id}: {e}")
            return {'current': 50, 'projected': 50, 'trend': [50]}
    
    def _get_vpc_network_utilization(self, vpc_id: str) -> Dict[str, Any]:
        """Get VPC network utilization metrics"""
        try:
            # Simplified network utilization
            return {
                'current': 45.0,
                'projected': 52.0,
                'trend': [40, 42, 45, 48, 45, 50, 45]
            }
        except Exception as e:
            logger.error(f"Failed to get VPC utilization for {vpc_id}: {e}")
            return {'current': 30, 'projected': 30, 'trend': [30]}
    
    def _get_rds_utilization(self, db_identifier: str) -> Dict[str, Any]:
        """Get RDS instance utilization metrics"""
        try:
            # Simplified RDS utilization
            return {
                'current': 55.0,
                'projected': 61.0,
                'trend': [50, 52, 55, 58, 55, 60, 55]
            }
        except Exception as e:
            logger.error(f"Failed to get RDS utilization for {db_identifier}: {e}")
            return {'current': 40, 'projected': 40, 'trend': [40]}
    
    def _get_elasticache_utilization(self, cache_id: str) -> Dict[str, Any]:
        """Get ElastiCache utilization metrics"""
        try:
            # Simplified ElastiCache utilization
            return {
                'current': 70.0,
                'projected': 78.0,
                'trend': [65, 67, 70, 73, 70, 75, 70]
            }
        except Exception as e:
            logger.error(f"Failed to get ElastiCache utilization for {cache_id}: {e}")
            return {'current': 50, 'projected': 50, 'trend': [50]}
    
    def _get_ebs_cost_per_gb(self, volume_type: str) -> float:
        """Get EBS cost per GB"""
        cost_mapping = {
            'gp2': 0.10,  # General Purpose SSD
            'gp3': 0.08,  # General Purpose SSD v3
            'io1': 0.125, # Provisioned IOPS SSD
            'st1': 0.045, # Throughput Optimized HDD
            'sc1': 0.025  # Cold HDD
        }
        return cost_mapping.get(volume_type, 0.10)
    
    def _get_rds_capacity_units(self, db_class: str) -> float:
        """Get RDS capacity units"""
        # Simplified capacity units based on instance class
        if 'db.t' in db_class:
            return 1.0
        elif 'db.r5' in db_class:
            return 2.0
        elif 'db.r6' in db_class:
            return 2.5
        else:
            return 1.5
    
    def _get_rds_cost_per_unit(self, db_class: str) -> float:
        """Get RDS cost per capacity unit"""
        # Simplified cost mapping
        if 'db.t' in db_class:
            return 0.015
        elif 'db.r5' in db_class:
            return 0.025
        elif 'db.r6' in db_class:
            return 0.030
        else:
            return 0.020
    
    def _get_elasticache_memory_gb(self, engine: str, node_type: str) -> float:
        """Get ElastiCache memory in GB"""
        # Simplified memory mapping
        if 'cache.t3' in node_type:
            return 1.5
        elif 'cache.r5' in node_type:
            return 13.0
        elif 'cache.r6' in node_type:
            return 16.0
        else:
            return 2.5
    
    def _get_elasticache_cost_per_gb(self, engine: str, node_type: str) -> float:
        """Get ElastiCache cost per GB"""
        # Simplified cost mapping
        if 'cache.t3' in node_type:
            return 0.018
        elif 'cache.r5' in node_type:
            return 0.025
        elif 'cache.r6' in node_type:
            return 0.030
        else:
            return 0.020

class AzureCapacityHandler(CapacityHandler):
    """Azure-specific capacity operations"""
    
    def initialize_client(self) -> bool:
        """Initialize Azure clients"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.monitor import MonitorManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'compute': ComputeManagementClient(credential, "<subscription-id>"),
                'monitor': MonitorManagementClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get Azure compute capacity information"""
        try:
            # Placeholder for Azure VM capacity
            return [
                ResourceCapacity(
                    resource_id="vm-azure-001",
                    resource_name="web-server-01",
                    resource_type="compute",
                    provider="azure",
                    current_capacity=2.0,
                    current_utilization=45.0,
                    projected_utilization=52.0,
                    utilization_trend=[40, 42, 45, 48, 45, 50, 45],
                    capacity_unit="vCPUs",
                    cost_per_unit=0.048,
                    region="eastus"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get Azure compute capacity: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get Azure storage capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="disk-azure-001",
                    resource_name="data-disk-01",
                    resource_type="storage",
                    provider="azure",
                    current_capacity=128.0,
                    current_utilization=65.0,
                    projected_utilization=72.0,
                    utilization_trend=[60, 62, 65, 68, 65, 70, 65],
                    capacity_unit="GB",
                    cost_per_unit=0.08,
                    region="eastus"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get Azure storage capacity: {e}")
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get Azure networking capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="vnet-azure-001",
                    resource_name="main-vnet",
                    resource_type="networking",
                    provider="azure",
                    current_capacity=10000.0,
                    current_utilization=35.0,
                    projected_utilization=42.0,
                    utilization_trend=[30, 32, 35, 38, 35, 40, 35],
                    capacity_unit="Mbps",
                    cost_per_unit=0.01,
                    region="eastus"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get Azure networking capacity: {e}")
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get Azure database capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="sql-azure-001",
                    resource_name="app-sql-01",
                    resource_type="database",
                    provider="azure",
                    current_capacity=2.0,
                    current_utilization=55.0,
                    projected_utilization=61.0,
                    utilization_trend=[50, 52, 55, 58, 55, 60, 55],
                    capacity_unit="DTUs",
                    cost_per_unit=0.025,
                    region="eastus"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get Azure database capacity: {e}")
            return []
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get Azure memory capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="cache-azure-001",
                    resource_name="redis-cache-01",
                    resource_type="memory",
                    provider="azure",
                    current_capacity=6.0,
                    current_utilization=70.0,
                    projected_utilization=78.0,
                    utilization_trend=[65, 67, 70, 73, 70, 75, 70],
                    capacity_unit="GB",
                    cost_per_unit=0.018,
                    region="eastus"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get Azure memory capacity: {e}")
            return []

class GCPCapacityHandler(CapacityHandler):
    """GCP-specific capacity operations"""
    
    def initialize_client(self) -> bool:
        """Initialize GCP clients"""
        try:
            from google.cloud import compute_v1
            from google.cloud import monitoring_v3
            
            self.client = {
                'compute': compute_v1.InstancesClient(),
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
    
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get GCP compute capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="instance-gcp-001",
                    resource_name="app-server-01",
                    resource_type="compute",
                    provider="gcp",
                    current_capacity=2.0,
                    current_utilization=42.0,
                    projected_utilization=48.0,
                    utilization_trend=[38, 40, 42, 45, 42, 47, 42],
                    capacity_unit="vCPUs",
                    cost_per_unit=0.0416,
                    region="us-central1"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get GCP compute capacity: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get GCP storage capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="disk-gcp-001",
                    resource_name="data-disk-01",
                    resource_type="storage",
                    provider="gcp",
                    current_capacity=100.0,
                    current_utilization=60.0,
                    projected_utilization=67.0,
                    utilization_trend=[55, 57, 60, 63, 60, 65, 60],
                    capacity_unit="GB",
                    cost_per_unit=0.08,
                    region="us-central1"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get GCP storage capacity: {e}")
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get GCP networking capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="network-gcp-001",
                    resource_name="default-network",
                    resource_type="networking",
                    provider="gcp",
                    current_capacity=10000.0,
                    current_utilization=30.0,
                    projected_utilization=37.0,
                    utilization_trend=[25, 27, 30, 33, 30, 35, 30],
                    capacity_unit="Mbps",
                    cost_per_unit=0.01,
                    region="us-central1"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get GCP networking capacity: {e}")
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get GCP database capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="sql-gcp-001",
                    resource_name="app-sql-01",
                    resource_type="database",
                    provider="gcp",
                    current_capacity=2.0,
                    current_utilization=50.0,
                    projected_utilization=56.0,
                    utilization_trend=[45, 47, 50, 53, 50, 55, 50],
                    capacity_unit="vCPUs",
                    cost_per_unit=0.020,
                    region="us-central1"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get GCP database capacity: {e}")
            return []
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get GCP memory capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="memstore-gcp-001",
                    resource_name="cache-01",
                    resource_type="memory",
                    provider="gcp",
                    current_capacity=4.0,
                    current_utilization=65.0,
                    projected_utilization=72.0,
                    utilization_trend=[60, 62, 65, 68, 65, 70, 65],
                    capacity_unit="GB",
                    cost_per_unit=0.018,
                    region="us-central1"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get GCP memory capacity: {e}")
            return []

class OnPremCapacityHandler(CapacityHandler):
    """On-premise capacity operations"""
    
    def initialize_client(self) -> bool:
        """Initialize on-premise clients"""
        try:
            # On-premise might use custom monitoring systems
            logger.info("On-premise capacity handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise compute capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="server-onprem-001",
                    resource_name="legacy-server-01",
                    resource_type="compute",
                    provider="onprem",
                    current_capacity=8.0,
                    current_utilization=35.0,
                    projected_utilization=40.0,
                    utilization_trend=[30, 32, 35, 38, 35, 39, 35],
                    capacity_unit="CPU Cores",
                    cost_per_unit=0.015,
                    region="onprem"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get on-premise compute capacity: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise storage capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="storage-onprem-001",
                    resource_name="san-array-01",
                    resource_type="storage",
                    provider="onprem",
                    current_capacity=2000.0,
                    current_utilization=55.0,
                    projected_utilization=62.0,
                    utilization_trend=[50, 52, 55, 58, 55, 60, 55],
                    capacity_unit="GB",
                    cost_per_unit=0.005,
                    region="onprem"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get on-premise storage capacity: {e}")
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise networking capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="network-onprem-001",
                    resource_name="core-switch-01",
                    resource_type="networking",
                    provider="onprem",
                    current_capacity=10000.0,
                    current_utilization=40.0,
                    projected_utilization=47.0,
                    utilization_trend=[35, 37, 40, 43, 40, 45, 40],
                    capacity_unit="Mbps",
                    cost_per_unit=0.008,
                    region="onprem"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get on-premise networking capacity: {e}")
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise database capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="db-onprem-001",
                    resource_name="oracle-db-01",
                    resource_type="database",
                    provider="onprem",
                    current_capacity=4.0,
                    current_utilization=60.0,
                    projected_utilization=68.0,
                    utilization_trend=[55, 57, 60, 63, 60, 65, 60],
                    capacity_unit="CPU Cores",
                    cost_per_unit=0.012,
                    region="onprem"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get on-premise database capacity: {e}")
            return []
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise memory capacity information"""
        try:
            return [
                ResourceCapacity(
                    resource_id="memory-onprem-001",
                    resource_name="cache-server-01",
                    resource_type="memory",
                    provider="onprem",
                    current_capacity=32.0,
                    current_utilization=75.0,
                    projected_utilization=83.0,
                    utilization_trend=[70, 72, 75, 78, 75, 80, 75],
                    capacity_unit="GB",
                    cost_per_unit=0.008,
                    region="onprem"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to get on-premise memory capacity: {e}")
            return []

def get_capacity_handler(provider: str, region: str = "us-west-2") -> CapacityHandler:
    """Get appropriate capacity handler"""
    handlers = {
        'aws': AWSCapacityHandler,
        'azure': AzureCapacityHandler,
        'gcp': GCPCapacityHandler,
        'onprem': OnPremCapacityHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
