#!/usr/bin/env python3
"""
Cost Optimizer Handler

Cloud-specific operations handler for cost optimization across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CostHandler(ABC):
    """Abstract base class for cloud-specific cost operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_cost_data(self, time_range_days: int) -> List[Dict[str, Any]]:
        """Get cost and usage data"""
        pass
    
    @abstractmethod
    def get_resource_utilization(self, resource_ids: List[str]) -> Dict[str, Any]:
        """Get resource utilization metrics"""
        pass
    
    @abstractmethod
    def analyze_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze rightsizing opportunities"""
        pass

class AWSCostHandler(CostHandler):
    """AWS-specific cost operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ce': boto3.client('ce', region_name='us-east-1'),  # Cost Explorer in us-east-1
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'ec2': boto3.client('ec2', region_name=self.region),
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
    
    def get_cost_data(self, time_range_days: int) -> List[Dict[str, Any]]:
        """Get AWS cost and usage data"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_range_days)
            
            # Get cost and usage data
            response = self.client['ce'].get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}
                ]
            )
            
            cost_data = []
            for result in response.get('ResultsByTime', []):
                time_period = result['TimePeriod']
                groups = result.get('Groups', [])
                
                for group in groups:
                    keys = group.get('Keys', [])
                    metrics = group.get('Metrics', {})
                    
                    cost_data.append({
                        'date': time_period.get('Start'),
                        'service': keys[0] if keys else 'Unknown',
                        'instance_type': keys[1] if len(keys) > 1 else 'Unknown',
                        'blended_cost': float(metrics.get('BlendedCost', {}).get('Amount', 0)),
                        'usage_quantity': float(metrics.get('UsageQuantity', {}).get('Amount', 0))
                    })
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Failed to get AWS cost data: {e}")
            return []
    
    def get_resource_utilization(self, resource_ids: List[str]) -> Dict[str, Any]:
        """Get AWS resource utilization metrics"""
        try:
            utilization_data = {}
            
            for resource_id in resource_ids:
                if resource_id.startswith('i-'):  # EC2 instance
                    utilization = self._get_ec2_utilization(resource_id)
                    utilization_data[resource_id] = utilization
                elif resource_id.startswith('vol-'):  # EBS volume
                    utilization = self._get_ebs_utilization(resource_id)
                    utilization_data[resource_id] = utilization
            
            return utilization_data
            
        except Exception as e:
            logger.error(f"Failed to get AWS resource utilization: {e}")
            return {}
    
    def _get_ec2_utilization(self, instance_id: str) -> Dict[str, Any]:
        """Get EC2 instance utilization"""
        try:
            # Get CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            cpu_metrics = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            cpu_data_points = cpu_metrics.get('Datapoints', [])
            avg_cpu = sum(dp['Average'] for dp in cpu_data_points) / len(cpu_data_points) if cpu_data_points else 0
            
            # Get instance details
            instance_details = self.client['ec2'].describe_instances(InstanceIds=[instance_id])
            instance = instance_details['Reservations'][0]['Instances'][0]
            
            return {
                'instance_type': instance['InstanceType'],
                'state': instance['State']['Name'],
                'platform': instance.get('Platform', 'linux'),
                'cpu_utilization': {
                    'average': avg_cpu,
                    'max': max(dp['Maximum'] for dp in cpu_data_points) if cpu_data_points else 0,
                    'min': min(dp['Minimum'] for dp in cpu_data_points) if cpu_data_points else 0
                },
                'launch_time': instance['LaunchTime'].isoformat(),
                'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
            }
            
        except Exception as e:
            logger.error(f"Failed to get EC2 utilization for {instance_id}: {e}")
            return {}
    
    def _get_ebs_utilization(self, volume_id: str) -> Dict[str, Any]:
        """Get EBS volume utilization"""
        try:
            volume_details = self.client['ec2'].describe_volumes(VolumeIds=[volume_id])
            volume = volume_details['Volumes'][0]
            
            # Get CloudWatch metrics for volume
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            # Get volume read/write operations
            read_ops = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeReadOps',
                Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            write_ops = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EBS',
                MetricName='VolumeWriteOps',
                Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            total_reads = sum(dp['Sum'] for dp in read_ops.get('Datapoints', []))
            total_writes = sum(dp['Sum'] for dp in write_ops.get('Datapoints', []))
            
            return {
                'volume_type': volume['VolumeType'],
                'size_gb': volume['Size'],
                'state': volume['State'],
                'iops': volume.get('Iops', 0),
                'throughput': volume.get('Throughput', 0),
                'total_reads_7d': total_reads,
                'total_writes_7d': total_writes,
                'attached': len(volume.get('Attachments', [])) > 0,
                'tags': {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
            }
            
        except Exception as e:
            logger.error(f"Failed to get EBS utilization for {volume_id}: {e}")
            return {}
    
    def analyze_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze AWS rightsizing opportunities"""
        try:
            opportunities = []
            
            # Get all EC2 instances
            instances_response = self.client['ec2'].describe_instances()
            
            for reservation in instances_response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        # Get utilization data
                        utilization = self._get_ec2_utilization(instance['InstanceId'])
                        
                        # Analyze if instance can be rightsized
                        if utilization:
                            opportunity = self._analyze_ec2_rightsizing(instance, utilization)
                            if opportunity:
                                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to analyze AWS rightsizing opportunities: {e}")
            return []
    
    def _analyze_ec2_rightsizing(self, instance: Dict[str, Any], utilization: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze if EC2 instance can be rightsized"""
        try:
            cpu_avg = utilization.get('cpu_utilization', {}).get('average', 0)
            instance_type = instance['InstanceType']
            
            # Rightsizing logic
            if cpu_avg < 20:  # Underutilized
                # Suggest smaller instance type
                smaller_instances = self._get_smaller_instance_types(instance_type)
                if smaller_instances:
                    return {
                        'resource_id': instance['InstanceId'],
                        'resource_name': instance.get('Tags', [{}])[0].get('Value', instance['InstanceId']),
                        'current_instance_type': instance_type,
                        'recommended_instance_type': smaller_instances[0],
                        'current_cpu_utilization': cpu_avg,
                        'estimated_savings': self._calculate_savings(instance_type, smaller_instances[0]),
                        'confidence': 0.85 if cpu_avg < 10 else 0.75,
                        'reason': f'Instance is underutilized with {cpu_avg:.1f}% average CPU'
                    }
            
            elif cpu_avg > 80:  # Overutilized
                # Suggest larger instance type
                larger_instances = self._get_larger_instance_types(instance_type)
                if larger_instances:
                    return {
                        'resource_id': instance['InstanceId'],
                        'resource_name': instance.get('Tags', [{}])[0].get('Value', instance['InstanceId']),
                        'current_instance_type': instance_type,
                        'recommended_instance_type': larger_instances[0],
                        'current_cpu_utilization': cpu_avg,
                        'estimated_cost_increase': self._calculate_savings(larger_instances[0], instance_type),
                        'confidence': 0.80,
                        'reason': f'Instance is overutilized with {cpu_avg:.1f}% average CPU'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to analyze EC2 rightsizing: {e}")
            return None
    
    def _get_smaller_instance_types(self, current_type: str) -> List[str]:
        """Get smaller instance types for rightsizing"""
        # Simplified instance family mapping
        instance_mapping = {
            't3.large': ['t3.medium', 't3.small'],
            't3.medium': ['t3.small', 't3.micro'],
            't3.small': ['t3.micro'],
            'm5.large': ['m5.medium', 't3.large'],
            'm5.medium': ['m5.small', 't3.medium'],
            'c5.large': ['c5.medium', 't3.large'],
            'c5.medium': ['c5.small', 't3.medium'],
        }
        return instance_mapping.get(current_type, [])
    
    def _get_larger_instance_types(self, current_type: str) -> List[str]:
        """Get larger instance types for rightsizing"""
        instance_mapping = {
            't3.micro': ['t3.small', 't3.medium'],
            't3.small': ['t3.medium', 't3.large'],
            't3.medium': ['t3.large', 'm5.medium'],
            't3.large': ['m5.medium', 'm5.large'],
            'm5.small': ['m5.medium', 't3.large'],
            'm5.medium': ['m5.large', 'c5.large'],
            'c5.small': ['c5.medium', 't3.large'],
            'c5.medium': ['c5.large', 'm5.large'],
        }
        return instance_mapping.get(current_type, [])
    
    def _calculate_savings(self, current_type: str, new_type: str) -> float:
        """Calculate cost difference between instance types"""
        # Simplified cost mapping (hourly rates in USD)
        cost_mapping = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            'm5.small': 0.0464,
            'm5.medium': 0.096,
            'm5.large': 0.192,
            'c5.small': 0.0416,
            'c5.medium': 0.0832,
            'c5.large': 0.170,
        }
        
        current_cost = cost_mapping.get(current_type, 0)
        new_cost = cost_mapping.get(new_type, 0)
        
        return (current_cost - new_cost) * 24 * 30  # Monthly savings

class AzureCostHandler(CostHandler):
    """Azure-specific cost operations"""
    
    def initialize_client(self) -> bool:
        """Initialize Azure clients"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.costmanagement import CostManagementClient
            from azure.mgmt.monitor import MonitorManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'cost': CostManagementClient(credential, "<subscription-id>"),
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
    
    def get_cost_data(self, time_range_days: int) -> List[Dict[str, Any]]:
        """Get Azure cost data"""
        try:
            # Placeholder for Azure Cost Management API
            return [
                {
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'service': 'Virtual Machines',
                    'resource_type': 'Standard_B2s',
                    'cost': 52.8,
                    'usage_quantity': 744
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get Azure cost data: {e}")
            return []
    
    def get_resource_utilization(self, resource_ids: List[str]) -> Dict[str, Any]:
        """Get Azure resource utilization"""
        try:
            # Placeholder for Azure Monitor metrics
            return {
                'vm-1': {
                    'cpu_utilization': 25.5,
                    'memory_utilization': 60.2,
                    'disk_utilization': 45.8
                }
            }
        except Exception as e:
            logger.error(f"Failed to get Azure resource utilization: {e}")
            return {}
    
    def analyze_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze Azure rightsizing opportunities"""
        try:
            # Placeholder for Azure rightsizing analysis
            return [
                {
                    'resource_id': '/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1',
                    'resource_name': 'web-server-1',
                    'current_size': 'Standard_B2s',
                    'recommended_size': 'Standard_B1s',
                    'current_cpu_utilization': 15.2,
                    'estimated_savings': 26.4,
                    'confidence': 0.80,
                    'reason': 'VM is underutilized with 15.2% average CPU'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to analyze Azure rightsizing opportunities: {e}")
            return []

class GCPCostHandler(CostHandler):
    """GCP-specific cost operations"""
    
    def initialize_client(self) -> bool:
        """Initialize GCP clients"""
        try:
            from google.cloud import billing_v1
            from google.cloud import monitoring_v3
            
            self.client = {
                'billing': billing_v1.CloudBillingClient(),
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
    
    def get_cost_data(self, time_range_days: int) -> List[Dict[str, Any]]:
        """Get GCP cost data"""
        try:
            # Placeholder for GCP Billing API
            return [
                {
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'service': 'Compute Engine',
                    'resource_type': 'e2-medium',
                    'cost': 48.6,
                    'usage_quantity': 744
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get GCP cost data: {e}")
            return []
    
    def get_resource_utilization(self, resource_ids: List[str]) -> Dict[str, Any]:
        """Get GCP resource utilization"""
        try:
            # Placeholder for Cloud Monitoring metrics
            return {
                'instance-1': {
                    'cpu_utilization': 35.8,
                    'memory_utilization': 55.1,
                    'disk_utilization': 40.2
                }
            }
        except Exception as e:
            logger.error(f"Failed to get GCP resource utilization: {e}")
            return {}
    
    def analyze_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze GCP rightsizing opportunities"""
        try:
            # Placeholder for GCP rightsizing analysis
            return [
                {
                    'resource_id': 'projects/project-123/zones/us-central1-a/instances/instance-1',
                    'resource_name': 'app-server-1',
                    'current_machine_type': 'e2-medium',
                    'recommended_machine_type': 'e2-small',
                    'current_cpu_utilization': 22.5,
                    'estimated_savings': 16.8,
                    'confidence': 0.75,
                    'reason': 'Instance is underutilized with 22.5% average CPU'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to analyze GCP rightsizing opportunities: {e}")
            return []

class OnPremCostHandler(CostHandler):
    """On-premise cost operations"""
    
    def initialize_client(self) -> bool:
        """Initialize on-premise clients"""
        try:
            # On-premise cost tracking might use custom monitoring systems
            logger.info("On-premise cost handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_cost_data(self, time_range_days: int) -> List[Dict[str, Any]]:
        """Get on-premise cost data"""
        try:
            # Placeholder for on-premise cost tracking
            return [
                {
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'service': 'Physical Servers',
                    'resource_type': 'Dell R740',
                    'cost': 450.0,
                    'usage_quantity': 744
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get on-premise cost data: {e}")
            return []
    
    def get_resource_utilization(self, resource_ids: List[str]) -> Dict[str, Any]:
        """Get on-premise resource utilization"""
        try:
            # Placeholder for on-premise monitoring systems
            return {
                'server-01': {
                    'cpu_utilization': 18.5,
                    'memory_utilization': 42.3,
                    'disk_utilization': 65.8,
                    'power_consumption': 350.0
                }
            }
        except Exception as e:
            logger.error(f"Failed to get on-premise resource utilization: {e}")
            return {}
    
    def analyze_rightsizing_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze on-premise rightsizing opportunities"""
        try:
            # Placeholder for on-premise rightsizing analysis
            return [
                {
                    'resource_id': 'server-01',
                    'resource_name': 'legacy-app-server',
                    'current_spec': 'Dell R740 (24 cores, 256GB RAM)',
                    'recommended_action': 'Migrate to cloud VM',
                    'current_cpu_utilization': 12.5,
                    'estimated_savings': 280.0,
                    'confidence': 0.70,
                    'reason': 'Physical server is underutilized and can be migrated to cloud'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to analyze on-premise rightsizing opportunities: {e}")
            return []

def get_cost_handler(provider: str, region: str = "us-west-2") -> CostHandler:
    """Get appropriate cost handler"""
    handlers = {
        'aws': AWSCostHandler,
        'azure': AzureCostHandler,
        'gcp': GCPCostHandler,
        'onprem': OnPremCostHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
