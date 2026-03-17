#!/usr/bin/env python3
"""
Capacity Planning Handler

Cloud-specific operations handler for capacity planning and resource forecasting across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
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

class CapacityPlanningHandler(ABC):
    """Abstract base class for cloud-specific capacity planning operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get compute resource capacity information"""
        pass
    
    @abstractmethod
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get storage resource capacity information"""
        pass
    
    @abstractmethod
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get networking resource capacity information"""
        pass
    
    @abstractmethod
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get database resource capacity information"""
        pass
    
    @abstractmethod
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get memory resource capacity information"""
        pass

class AWSCapacityPlanningHandler(CapacityPlanningHandler):
    """AWS-specific capacity planning operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'ec2': boto3.client('ec2', region_name=self.region),
                'autoscaling': boto3.client('autoscaling', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region),
                'elasticache': boto3.client('elasticache', region_name=self.region),
                'lambda': boto3.client('lambda', region_name=self.region),
                'pricing': boto3.client('pricing', region_name='us-east-1')  # Pricing API in us-east-1
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
        """Get AWS compute resource capacity information"""
        try:
            resources = []
            
            # Get EC2 instances
            instances = self._get_ec2_instances()
            resources.extend(instances)
            
            # Get Auto Scaling Groups
            asgs = self._get_auto_scaling_groups()
            resources.extend(asgs)
            
            # Get Lambda functions
            lambda_functions = self._get_lambda_functions()
            resources.extend(lambda_functions)
            
            logger.info(f"Collected {len(resources)} AWS compute resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS compute capacity: {e}")
            return []
    
    def _get_ec2_instances(self) -> List[ResourceCapacity]:
        """Get EC2 instance capacity information"""
        resources = []
        
        try:
            # Get all instances
            instances = self.client['ec2'].describe_instances()
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'running':
                        continue
                    
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    
                    # Get instance type info for capacity
                    instance_info = self._get_instance_type_info(instance_type)
                    
                    # Get CloudWatch metrics for utilization
                    cpu_utilization = self._get_cloudwatch_metric(
                        'AWS/EC2', 'CPUUtilization', 'InstanceId', instance_id
                    )
                    
                    # Get historical utilization data
                    utilization_trend = self._get_historical_utilization(
                        'AWS/EC2', 'CPUUtilization', 'InstanceId', instance_id
                    )
                    
                    # Calculate projected utilization
                    projected_utilization = self._calculate_projected_utilization(utilization_trend)
                    
                    # Get cost per instance
                    cost_per_hour = self._get_ec2_cost(instance_type)
                    
                    resource = ResourceCapacity(
                        resource_id=instance_id,
                        resource_name=instance.get('Tags', [{}])[0].get('Value', instance_id) if instance.get('Tags') else instance_id,
                        resource_type="compute",
                        provider="aws",
                        current_capacity=instance_info['vcpus'],
                        current_utilization=cpu_utilization,
                        projected_utilization=projected_utilization,
                        utilization_trend=utilization_trend,
                        capacity_unit="vcpus",
                        cost_per_unit=cost_per_hour / instance_info['vcpus'],  # Cost per vCPU per hour
                        region=self.region
                    )
                    
                    resources.append(resource)
            
        except Exception as e:
            logger.error(f"Failed to get EC2 instances: {e}")
        
        return resources
    
    def _get_instance_type_info(self, instance_type: str) -> Dict[str, Any]:
        """Get instance type information"""
        try:
            response = self.client['ec2'].describe_instance_types(InstanceTypes=[instance_type])
            instance_info = response['InstanceTypes'][0]
            
            return {
                'vcpus': instance_info['VCpuInfo']['DefaultVCpus'],
                'memory_gb': instance_info['MemoryInfo']['SizeInMiB'] / 1024,
                'instance_storage': instance_info.get('InstanceStorageInfo', {}).get('TotalSizeInGB', 0)
            }
        except:
            # Fallback to common instance types
            fallback_info = {
                't3.micro': {'vcpus': 2, 'memory_gb': 1, 'instance_storage': 0},
                't3.small': {'vcpus': 2, 'memory_gb': 2, 'instance_storage': 0},
                't3.medium': {'vcpus': 2, 'memory_gb': 4, 'instance_storage': 0},
                't3.large': {'vcpus': 2, 'memory_gb': 8, 'instance_storage': 0},
                'm5.large': {'vcpus': 2, 'memory_gb': 8, 'instance_storage': 0},
                'm5.xlarge': {'vcpus': 4, 'memory_gb': 16, 'instance_storage': 0},
                'm5.2xlarge': {'vcpus': 8, 'memory_gb': 32, 'instance_storage': 0},
                'c5.large': {'vcpus': 2, 'memory_gb': 4, 'instance_storage': 0},
                'c5.xlarge': {'vcpus': 4, 'memory_gb': 8, 'instance_storage': 0},
                'c5.2xlarge': {'vcpus': 8, 'memory_gb': 16, 'instance_storage': 0}
            }
            
            return fallback_info.get(instance_type, {'vcpus': 2, 'memory_gb': 4, 'instance_storage': 0})
    
    def _get_cloudwatch_metric(self, namespace: str, metric_name: str, 
                              dimension_name: str, dimension_value: str) -> float:
        """Get current CloudWatch metric value"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            response = self.client['cloudwatch'].get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=[{'Name': dimension_name, 'Value': dimension_value}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=['Average']
            )
            
            datapoints = response['Datapoints']
            if datapoints:
                return datapoints[-1]['Average']  # Return the latest average
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Failed to get CloudWatch metric {metric_name} for {dimension_value}: {e}")
            return 0.0
    
    def _get_historical_utilization(self, namespace: str, metric_name: str,
                                   dimension_name: str, dimension_value: str) -> List[float]:
        """Get historical utilization data"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)  # 30 days of data
            
            response = self.client['cloudwatch'].get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=[{'Name': dimension_name, 'Value': dimension_value}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600 * 24,  # Daily averages
                Statistics=['Average']
            )
            
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            return [dp['Average'] for dp in datapoints]
            
        except Exception as e:
            logger.warning(f"Failed to get historical utilization for {dimension_value}: {e}")
            return []
    
    def _calculate_projected_utilization(self, utilization_trend: List[float]) -> float:
        """Calculate projected utilization based on trend"""
        if len(utilization_trend) < 2:
            return utilization_trend[-1] if utilization_trend else 0.0
        
        # Simple linear projection
        n = len(utilization_trend)
        x = list(range(n))
        
        # Calculate slope
        sum_x = sum(x)
        sum_y = sum(utilization_trend)
        sum_xy = sum(x[i] * utilization_trend[i] for i in range(n))
        sum_x2 = sum(x[i]**2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        
        # Project 30 days forward
        projected = utilization_trend[-1] + (slope * 30)
        
        # Cap at 100%
        return min(projected, 100.0)
    
    def _get_ec2_cost(self, instance_type: str) -> float:
        """Get hourly cost for EC2 instance type"""
        try:
            # Simplified pricing lookup (would use pricing API in production)
            pricing_data = {
                't3.micro': 0.0104,
                't3.small': 0.0208,
                't3.medium': 0.0416,
                't3.large': 0.0832,
                'm5.large': 0.096,
                'm5.xlarge': 0.192,
                'm5.2xlarge': 0.384,
                'c5.large': 0.085,
                'c5.xlarge': 0.170,
                'c5.2xlarge': 0.340
            }
            
            base_price = pricing_data.get(instance_type, 0.1)
            
            # Adjust for region (simplified)
            region_multipliers = {
                'us-east-1': 1.0,
                'us-west-2': 1.0,
                'eu-west-1': 1.1,
                'ap-southeast-1': 1.05
            }
            
            multiplier = region_multipliers.get(self.region, 1.0)
            return base_price * multiplier
            
        except Exception:
            return 0.1  # Fallback pricing
    
    def _get_auto_scaling_groups(self) -> List[ResourceCapacity]:
        """Get Auto Scaling Group capacity information"""
        resources = []
        
        try:
            response = self.client['autoscaling'].describe_auto_scaling_groups()
            
            for asg in response['AutoScalingGroups']:
                asg_name = asg['AutoScalingGroupName']
                min_size = asg['MinSize']
                max_size = asg['MaxSize']
                desired_capacity = asg['DesiredCapacity']
                current_capacity = len(asg['Instances'])
                
                # Get average CPU utilization across instances
                total_cpu = 0.0
                instance_count = 0
                
                for instance in asg['Instances']:
                    if instance['LifecycleState'] == 'InService':
                        cpu_util = self._get_cloudwatch_metric(
                            'AWS/EC2', 'CPUUtilization', 'InstanceId', instance['InstanceId']
                        )
                        total_cpu += cpu_util
                        instance_count += 1
                
                avg_cpu_utilization = total_cpu / instance_count if instance_count > 0 else 0.0
                
                # Get historical utilization
                utilization_trend = self._get_asg_historical_utilization(asg_name)
                projected_utilization = self._calculate_projected_utilization(utilization_trend)
                
                # Calculate cost (simplified)
                instance_type = asg.get('Instances', [{}])[0].get('InstanceType', 't3.medium') if asg.get('Instances') else 't3.medium'
                cost_per_hour = self._get_ec2_cost(instance_type)
                
                resource = ResourceCapacity(
                    resource_id=asg_name,
                    resource_name=asg_name,
                    resource_type="compute",
                    provider="aws",
                    current_capacity=desired_capacity,
                    current_utilization=avg_cpu_utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="instances",
                    cost_per_unit=cost_per_hour,
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get Auto Scaling Groups: {e}")
        
        return resources
    
    def _get_asg_historical_utilization(self, asg_name: str) -> List[float]:
        """Get historical utilization for Auto Scaling Group"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/AutoScaling',
                MetricName='GroupInServiceInstances',
                Dimensions=[{'Name': 'AutoScalingGroupName', 'Value': asg_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600 * 24,  # Daily
                Statistics=['Average']
            )
            
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            return [dp['Average'] for dp in datapoints]
            
        except Exception as e:
            logger.warning(f"Failed to get ASG historical utilization for {asg_name}: {e}")
            return []
    
    def _get_lambda_functions(self) -> List[ResourceCapacity]:
        """Get Lambda function capacity information"""
        resources = []
        
        try:
            response = self.client['lambda'].list_functions()
            
            for function in response['Functions']:
                function_name = function['FunctionName']
                
                # Get memory configuration
                memory_size = function['MemorySize']
                
                # Get CloudWatch metrics
                duration_avg = self._get_cloudwatch_metric(
                    'AWS/Lambda', 'Duration', 'FunctionName', function_name
                )
                
                # Get invocation count for utilization
                invocations = self._get_cloudwatch_metric(
                    'AWS/Lambda', 'Invocations', 'FunctionName', function_name
                )
                
                # Calculate utilization based on invocations and duration
                max_concurrent = 1000  # Default Lambda concurrency limit
                utilization = min((invocations / 1000) * 100, 100.0)  # Simplified utilization
                
                # Get historical data
                utilization_trend = self._get_lambda_historical_utilization(function_name)
                projected_utilization = self._calculate_projected_utilization(utilization_trend)
                
                # Calculate cost
                cost_per_mb_sec = 0.0000166667  # $0.0000166667 per GB-second
                cost_per_unit = cost_per_mb_sec * duration_avg / 1000  # Cost per MB
                
                resource = ResourceCapacity(
                    resource_id=function_name,
                    resource_name=function_name,
                    resource_type="compute",
                    provider="aws",
                    current_capacity=memory_size,
                    current_utilization=utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="mb",
                    cost_per_unit=cost_per_unit,
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get Lambda functions: {e}")
        
        return resources
    
    def _get_lambda_historical_utilization(self, function_name: str) -> List[float]:
        """Get historical utilization for Lambda function"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600 * 24,  # Daily
                Statistics=['Sum']
            )
            
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            invocations = [dp['Sum'] for dp in datapoints]
            
            # Convert invocations to utilization percentage
            utilization = [min((inv / 1000) * 100, 100.0) for inv in invocations]
            return utilization
            
        except Exception as e:
            logger.warning(f"Failed to get Lambda historical utilization for {function_name}: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get AWS storage resource capacity information"""
        try:
            resources = []
            
            # Get S3 buckets
            s3_buckets = self._get_s3_buckets()
            resources.extend(s3_buckets)
            
            # Get EBS volumes
            ebs_volumes = self._get_ebs_volumes()
            resources.extend(ebs_volumes)
            
            # Get RDS storage
            rds_storage = self._get_rds_storage()
            resources.extend(rds_storage)
            
            logger.info(f"Collected {len(resources)} AWS storage resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS storage capacity: {e}")
            return []
    
    def _get_s3_buckets(self) -> List[ResourceCapacity]:
        """Get S3 bucket capacity information"""
        resources = []
        
        try:
            response = self.client['s3'].list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                # Get bucket size (simplified - would use CloudWatch in production)
                bucket_size_gb = self._get_s3_bucket_size(bucket_name)
                
                # Get storage utilization (simplified)
                utilization = min((bucket_size_gb / 1000) * 100, 100.0)  # Assume 1TB limit for calculation
                
                # Get historical data
                utilization_trend = self._get_s3_historical_utilization(bucket_name)
                projected_utilization = self._calculate_projected_utilization(utilization_trend)
                
                # Calculate cost
                storage_cost_per_gb = 0.023  # S3 Standard storage cost
                
                resource = ResourceCapacity(
                    resource_id=bucket_name,
                    resource_name=bucket_name,
                    resource_type="storage",
                    provider="aws",
                    current_capacity=bucket_size_gb,
                    current_utilization=utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="gb",
                    cost_per_unit=storage_cost_per_gb,
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get S3 buckets: {e}")
        
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
    
    def _get_s3_historical_utilization(self, bucket_name: str) -> List[float]:
        """Get historical utilization for S3 bucket"""
        try:
            # Simplified - would use CloudWatch BucketSizeBytes metric
            import random
            return [random.uniform(20, 80) for _ in range(30)]
        except:
            return []
    
    def _get_ebs_volumes(self) -> List[ResourceCapacity]:
        """Get EBS volume capacity information"""
        resources = []
        
        try:
            response = self.client['ec2'].describe_volumes()
            
            for volume in response['Volumes']:
                if volume['State'] != 'in-use':
                    continue
                
                volume_id = volume['VolumeId']
                size_gb = volume['Size']
                
                # Get volume utilization (simplified - would use CloudWatch)
                utilization = self._get_ebs_utilization(volume_id)
                
                # Get historical data
                utilization_trend = self._get_ebs_historical_utilization(volume_id)
                projected_utilization = self._calculate_projected_utilization(utilization_trend)
                
                # Calculate cost
                volume_type = volume.get('VolumeType', 'gp2')
                cost_per_gb = self._get_ebs_cost(volume_type)
                
                resource = ResourceCapacity(
                    resource_id=volume_id,
                    resource_name=volume_id,
                    resource_type="storage",
                    provider="aws",
                    current_capacity=size_gb,
                    current_utilization=utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="gb",
                    cost_per_unit=cost_per_gb,
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get EBS volumes: {e}")
        
        return resources
    
    def _get_ebs_utilization(self, volume_id: str) -> float:
        """Get EBS volume utilization (simplified)"""
        try:
            # Would use CloudWatch VolumeReadBytes/VolumeWriteBytes in production
            import random
            return random.uniform(10, 90)
        except:
            return 50.0
    
    def _get_ebs_historical_utilization(self, volume_id: str) -> List[float]:
        """Get historical utilization for EBS volume"""
        try:
            import random
            return [random.uniform(10, 90) for _ in range(30)]
        except:
            return []
    
    def _get_ebs_cost(self, volume_type: str) -> float:
        """Get EBS cost per GB"""
        pricing = {
            'gp2': 0.10,      # $0.10 per GB-month
            'gp3': 0.08,      # $0.08 per GB-month
            'io1': 0.125,     # $0.125 per GB-month
            'st1': 0.045,     # $0.045 per GB-month
            'sc1': 0.025      # $0.025 per GB-month
        }
        
        # Convert monthly to hourly
        monthly_cost = pricing.get(volume_type, 0.10)
        return monthly_cost / (30 * 24)
    
    def _get_rds_storage(self) -> List[ResourceCapacity]:
        """Get RDS storage capacity information"""
        resources = []
        
        try:
            response = self.client['rds'].describe_db_instances()
            
            for db_instance in response['DBInstances']:
                if db_instance['DBInstanceStatus'] != 'available':
                    continue
                
                db_id = db_instance['DBInstanceIdentifier']
                allocated_storage = db_instance['AllocatedStorage']
                
                # Get storage utilization
                utilization = self._get_rds_utilization(db_id)
                
                # Get historical data
                utilization_trend = self._get_rds_historical_utilization(db_id)
                projected_utilization = self._calculate_projected_utilization(utilization_trend)
                
                # Calculate cost
                storage_type = db_instance.get('StorageType', 'gp2')
                cost_per_gb = self._get_ebs_cost(storage_type)  # Use EBS pricing as reference
                
                resource = ResourceCapacity(
                    resource_id=db_id,
                    resource_name=db_id,
                    resource_type="storage",
                    provider="aws",
                    current_capacity=allocated_storage,
                    current_utilization=utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="gb",
                    cost_per_unit=cost_per_gb,
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get RDS storage: {e}")
        
        return resources
    
    def _get_rds_utilization(self, db_id: str) -> float:
        """Get RDS storage utilization"""
        try:
            return self._get_cloudwatch_metric('AWS/RDS', 'FreeStorageSpace', 'DBInstanceIdentifier', db_id)
        except:
            return 50.0
    
    def _get_rds_historical_utilization(self, db_id: str) -> List[float]:
        """Get historical utilization for RDS"""
        try:
            return self._get_historical_utilization('AWS/RDS', 'FreeStorageSpace', 'DBInstanceIdentifier', db_id)
        except:
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get AWS networking resource capacity information"""
        try:
            resources = []
            
            # Get VPCs and subnets
            vpc_resources = self._get_vpc_capacity()
            resources.extend(vpc_resources)
            
            # Get ELBs/ALBs
            elb_resources = self._get_elb_capacity()
            resources.extend(elb_resources)
            
            logger.info(f"Collected {len(resources)} AWS networking resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS networking capacity: {e}")
            return []
    
    def _get_vpc_capacity(self) -> List[ResourceCapacity]:
        """Get VPC networking capacity"""
        resources = []
        
        try:
            response = self.client['ec2'].describe_vpcs()
            
            for vpc in response['Vpcs']:
                vpc_id = vpc['VpcId']
                
                # Get subnets for this VPC
                subnets_response = self.client['ec2'].describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
                
                # Calculate capacity based on available IP addresses
                total_available_ips = sum(subnet['AvailableIpAddressCount'] for subnet in subnets_response['Subnets'])
                total_ips = sum(subnet['AvailableIpAddressCount'] + len(subnet.get('CidrBlockAssociationSet', [])) * 256 
                              for subnet in subnets_response['Subnets'])
                
                utilization = ((total_ips - total_available_ips) / total_ips * 100) if total_ips > 0 else 0.0
                
                # Get historical data (simplified)
                utilization_trend = [utilization] * 30  # Use current value for all historical points
                projected_utilization = utilization
                
                # Calculate cost (simplified)
                cost_per_ip = 0.005  # Simplified networking cost
                
                resource = ResourceCapacity(
                    resource_id=vpc_id,
                    resource_name=vpc.get('Tags', [{}])[0].get('Value', vpc_id) if vpc.get('Tags') else vpc_id,
                    resource_type="networking",
                    provider="aws",
                    current_capacity=total_ips,
                    current_utilization=utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="ips",
                    cost_per_unit=cost_per_ip,
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get VPC capacity: {e}")
        
        return resources
    
    def _get_elb_capacity(self) -> List[ResourceCapacity]:
        """Get ELB/ALB capacity information"""
        resources = []
        
        try:
            # Get Application Load Balancers
            try:
                response = self.client['elbv2'].describe_load_balancers()
                
                for lb in response['LoadBalancers']:
                    lb_arn = lb['LoadBalancerArn']
                    lb_name = lb['LoadBalancerName']
                    
                    # Get utilization metrics
                    request_count = self._get_cloudwatch_metric('AWS/ApplicationELB', 'RequestCount', 'LoadBalancer', lb_name)
                    active_connections = self._get_cloudwatch_metric('AWS/ApplicationELB', 'ActiveConnectionCount', 'LoadBalancer', lb_name)
                    
                    # Calculate utilization based on request count vs capacity
                    max_requests_per_second = 10000  # Simplified capacity
                    utilization = min((request_count / max_requests_per_second) * 100, 100.0)
                    
                    # Get historical data
                    utilization_trend = self._get_elb_historical_utilization(lb_name)
                    projected_utilization = self._calculate_projected_utilization(utilization_trend)
                    
                    # Calculate cost
                    cost_per_hour = 0.0225  # ALB cost per hour
                    
                    resource = ResourceCapacity(
                        resource_id=lb_arn,
                        resource_name=lb_name,
                        resource_type="networking",
                        provider="aws",
                        current_capacity=max_requests_per_second,
                        current_utilization=utilization,
                        projected_utilization=projected_utilization,
                        utilization_trend=utilization_trend,
                        capacity_unit="requests_per_second",
                        cost_per_unit=cost_per_hour / max_requests_per_second,
                        region=self.region
                    )
                    
                    resources.append(resource)
                    
            except:
                # ELB client might not be available
                pass
                
        except Exception as e:
            logger.error(f"Failed to get ELB capacity: {e}")
        
        return resources
    
    def _get_elb_historical_utilization(self, lb_name: str) -> List[float]:
        """Get historical utilization for ELB"""
        try:
            return self._get_historical_utilization('AWS/ApplicationELB', 'RequestCount', 'LoadBalancer', lb_name)
        except:
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get AWS database capacity information"""
        try:
            resources = []
            
            # Get RDS instances
            rds_instances = self._get_rds_instances()
            resources.extend(rds_instances)
            
            # Get ElastiCache clusters
            elasticache_clusters = self._get_elasticache_clusters()
            resources.extend(elasticache_clusters)
            
            logger.info(f"Collected {len(resources)} AWS database resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS database capacity: {e}")
            return []
    
    def _get_rds_instances(self) -> List[ResourceCapacity]:
        """Get RDS instance capacity information"""
        resources = []
        
        try:
            response = self.client['rds'].describe_db_instances()
            
            for db_instance in response['DBInstances']:
                if db_instance['DBInstanceStatus'] != 'available':
                    continue
                
                db_id = db_instance['DBInstanceIdentifier']
                instance_class = db_instance['DBInstanceClass']
                
                # Get instance capacity info
                instance_info = self._get_rds_instance_info(instance_class)
                
                # Get CPU utilization
                cpu_utilization = self._get_cloudwatch_metric('AWS/RDS', 'CPUUtilization', 'DBInstanceIdentifier', db_id)
                
                # Get historical utilization
                utilization_trend = self._get_historical_utilization('AWS/RDS', 'CPUUtilization', 'DBInstanceIdentifier', db_id)
                projected_utilization = self._calculate_projected_utilization(utilization_trend)
                
                # Calculate cost
                cost_per_hour = self._get_rds_cost(instance_class)
                
                resource = ResourceCapacity(
                    resource_id=db_id,
                    resource_name=db_id,
                    resource_type="database",
                    provider="aws",
                    current_capacity=instance_info['vcpus'],
                    current_utilization=cpu_utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="vcpus",
                    cost_per_unit=cost_per_hour / instance_info['vcpus'],
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get RDS instances: {e}")
        
        return resources
    
    def _get_rds_instance_info(self, instance_class: str) -> Dict[str, Any]:
        """Get RDS instance type information"""
        # Simplified RDS instance info
        rds_info = {
            'db.t3.micro': {'vcpus': 2, 'memory_gb': 1},
            'db.t3.small': {'vcpus': 2, 'memory_gb': 2},
            'db.t3.medium': {'vcpus': 2, 'memory_gb': 4},
            'db.t3.large': {'vcpus': 2, 'memory_gb': 8},
            'db.m5.large': {'vcpus': 2, 'memory_gb': 8},
            'db.m5.xlarge': {'vcpus': 4, 'memory_gb': 16},
            'db.m5.2xlarge': {'vcpus': 8, 'memory_gb': 32},
            'db.r5.large': {'vcpus': 2, 'memory_gb': 16},
            'db.r5.xlarge': {'vcpus': 4, 'memory_gb': 32},
            'db.r5.2xlarge': {'vcpus': 8, 'memory_gb': 64}
        }
        
        return rds_info.get(instance_class, {'vcpus': 2, 'memory_gb': 8})
    
    def _get_rds_cost(self, instance_class: str) -> float:
        """Get RDS instance cost per hour"""
        # Simplified RDS pricing
        pricing = {
            'db.t3.micro': 0.011,
            'db.t3.small': 0.022,
            'db.t3.medium': 0.044,
            'db.t3.large': 0.088,
            'db.m5.large': 0.192,
            'db.m5.xlarge': 0.384,
            'db.m5.2xlarge': 0.768,
            'db.r5.large': 0.213,
            'db.r5.xlarge': 0.426,
            'db.r5.2xlarge': 0.852
        }
        
        return pricing.get(instance_class, 0.1)
    
    def _get_elasticache_clusters(self) -> List[ResourceCapacity]:
        """Get ElastiCache cluster capacity information"""
        resources = []
        
        try:
            response = self.client['elasticache'].describe_cache_clusters()
            
            for cluster in response['CacheClusters']:
                cluster_id = cluster['CacheClusterId']
                node_type = cluster['CacheNodeType']
                num_nodes = cluster['NumNodes']
                
                # Get node capacity info
                node_info = self._get_elasticache_node_info(node_type)
                
                # Get CPU utilization
                cpu_utilization = self._get_cloudwatch_metric('AWS/ElastiCache', 'CPUUtilization', 'CacheClusterId', cluster_id)
                
                # Get historical utilization
                utilization_trend = self._get_historical_utilization('AWS/ElastiCache', 'CPUUtilization', 'CacheClusterId', cluster_id)
                projected_utilization = self._calculate_projected_utilization(utilization_trend)
                
                # Calculate cost
                cost_per_hour = self._get_elasticache_cost(node_type)
                
                resource = ResourceCapacity(
                    resource_id=cluster_id,
                    resource_name=cluster_id,
                    resource_type="database",
                    provider="aws",
                    current_capacity=node_info['vcpus'] * num_nodes,
                    current_utilization=cpu_utilization,
                    projected_utilization=projected_utilization,
                    utilization_trend=utilization_trend,
                    capacity_unit="vcpus",
                    cost_per_unit=cost_per_hour / node_info['vcpus'],
                    region=self.region
                )
                
                resources.append(resource)
                
        except Exception as e:
            logger.error(f"Failed to get ElastiCache clusters: {e}")
        
        return resources
    
    def _get_elasticache_node_info(self, node_type: str) -> Dict[str, Any]:
        """Get ElastiCache node type information"""
        # Simplified ElastiCache node info
        cache_info = {
            'cache.t3.micro': {'vcpus': 2, 'memory_gb': 0.5},
            'cache.t3.small': {'vcpus': 2, 'memory_gb': 1.3},
            'cache.t3.medium': {'vcpus': 2, 'memory_gb': 2.6},
            'cache.m5.large': {'vcpus': 2, 'memory_gb': 6.1},
            'cache.m5.xlarge': {'vcpus': 4, 'memory_gb': 13.4},
            'cache.m5.2xlarge': {'vcpus': 8, 'memory_gb': 27.6},
            'cache.r5.large': {'vcpus': 2, 'memory_gb': 13.6},
            'cache.r5.xlarge': {'vcpus': 4, 'memory_gb': 28.4},
            'cache.r5.2xlarge': {'vcpus': 8, 'memory_gb': 58.2}
        }
        
        return cache_info.get(node_type, {'vcpus': 2, 'memory_gb': 4})
    
    def _get_elasticache_cost(self, node_type: str) -> float:
        """Get ElastiCache node cost per hour"""
        # Simplified ElastiCache pricing
        pricing = {
            'cache.t3.micro': 0.007,
            'cache.t3.small': 0.014,
            'cache.t3.medium': 0.028,
            'cache.m5.large': 0.144,
            'cache.m5.xlarge': 0.288,
            'cache.m5.2xlarge': 0.576,
            'cache.r5.large': 0.189,
            'cache.r5.xlarge': 0.378,
            'cache.r5.2xlarge': 0.756
        }
        
        return pricing.get(node_type, 0.05)
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get AWS memory capacity information"""
        try:
            resources = []
            
            # Memory is already included in compute resources (EC2, Lambda, etc.)
            # This method could be used for specialized memory resources like MemoryDB
            
            logger.info(f"Collected {len(resources)} AWS memory resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS memory capacity: {e}")
            return []

# Simplified handlers for other providers
class AzureCapacityPlanningHandler(CapacityPlanningHandler):
    """Azure-specific capacity planning operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.storage import StorageManagementClient
            from azure.mgmt.sql import SqlManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
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
    
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get Azure compute resource capacity information"""
        try:
            resources = []
            
            # Simulate Azure VM capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="azure-vm-1",
                    resource_name="web-server-01",
                    resource_type="compute",
                    provider="azure",
                    current_capacity=4.0,
                    current_utilization=65.5,
                    projected_utilization=72.3,
                    utilization_trend=[60.0, 62.0, 65.0, 68.0, 65.5],
                    capacity_unit="vcpus",
                    cost_per_unit=0.048,
                    region="eastus"
                ),
                ResourceCapacity(
                    resource_id="azure-vm-2",
                    resource_name="app-server-01",
                    resource_type="compute",
                    provider="azure",
                    current_capacity=8.0,
                    current_utilization=45.2,
                    projected_utilization=48.7,
                    utilization_trend=[40.0, 42.0, 44.0, 46.0, 45.2],
                    capacity_unit="vcpus",
                    cost_per_unit=0.096,
                    region="eastus"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} Azure compute resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure compute capacity: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get Azure storage resource capacity information"""
        try:
            resources = []
            
            # Simulate Azure storage capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="azure-storage-1",
                    resource_name="data-storage-account",
                    resource_type="storage",
                    provider="azure",
                    current_capacity=500.0,
                    current_utilization=78.3,
                    projected_utilization=85.6,
                    utilization_trend=[70.0, 72.0, 74.0, 76.0, 78.3],
                    capacity_unit="gb",
                    cost_per_unit=0.018,
                    region="eastus"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} Azure storage resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure storage capacity: {e}")
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get Azure networking resource capacity information"""
        try:
            resources = []
            
            # Simulate Azure networking capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="azure-vnet-1",
                    resource_name="production-vnet",
                    resource_type="networking",
                    provider="azure",
                    current_capacity=1000.0,
                    current_utilization=35.7,
                    projected_utilization=42.1,
                    utilization_trend=[30.0, 32.0, 34.0, 36.0, 35.7],
                    capacity_unit="ips",
                    cost_per_unit=0.003,
                    region="eastus"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} Azure networking resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure networking capacity: {e}")
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get Azure database capacity information"""
        try:
            resources = []
            
            # Simulate Azure database capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="azure-sql-1",
                    resource_name="production-db",
                    resource_type="database",
                    provider="azure",
                    current_capacity=4.0,
                    current_utilization=82.4,
                    projected_utilization=88.9,
                    utilization_trend=[75.0, 78.0, 80.0, 82.0, 82.4],
                    capacity_unit="vcpus",
                    cost_per_unit=0.145,
                    region="eastus"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} Azure database resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure database capacity: {e}")
            return []
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get Azure memory capacity information"""
        try:
            resources = []
            
            # Memory is included in compute resources
            logger.info(f"Collected {len(resources)} Azure memory resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure memory capacity: {e}")
            return []

class GCPCapacityPlanningHandler(CapacityPlanningHandler):
    """GCP-specific capacity planning operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import compute_v1
            from google.cloud import storage
            from google.cloud import monitoring
            
            self.client = {
                'compute': compute_v1.InstancesClient(),
                'storage': storage.Client(),
                'monitoring': monitoring.MetricServiceClient()
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
        """Get GCP compute resource capacity information"""
        try:
            resources = []
            
            # Simulate GCP compute capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="gcp-instance-1",
                    resource_name="web-server-gcp",
                    resource_type="compute",
                    provider="gcp",
                    current_capacity=2.0,
                    current_utilization=58.9,
                    projected_utilization=64.2,
                    utilization_trend=[55.0, 56.0, 57.0, 58.0, 58.9],
                    capacity_unit="vcpus",
                    cost_per_unit=0.033,
                    region="us-central1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} GCP compute resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP compute capacity: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get GCP storage resource capacity information"""
        try:
            resources = []
            
            # Simulate GCP storage capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="gcp-bucket-1",
                    resource_name="data-bucket",
                    resource_type="storage",
                    provider="gcp",
                    current_capacity=250.0,
                    current_utilization=62.1,
                    projected_utilization=68.5,
                    utilization_trend=[58.0, 59.0, 60.0, 61.0, 62.1],
                    capacity_unit="gb",
                    cost_per_unit=0.020,
                    region="us-central1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} GCP storage resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP storage capacity: {e}")
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get GCP networking resource capacity information"""
        try:
            resources = []
            
            # Simulate GCP networking capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="gcp-network-1",
                    resource_name="production-network",
                    resource_type="networking",
                    provider="gcp",
                    current_capacity=2000.0,
                    current_utilization=28.4,
                    projected_utilization=35.7,
                    utilization_trend=[25.0, 26.0, 27.0, 28.0, 28.4],
                    capacity_unit="ips",
                    cost_per_unit=0.002,
                    region="us-central1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} GCP networking resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP networking capacity: {e}")
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get GCP database capacity information"""
        try:
            resources = []
            
            # Simulate GCP database capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="gcp-sql-1",
                    resource_name="production-sql",
                    resource_type="database",
                    provider="gcp",
                    current_capacity=2.0,
                    current_utilization=71.3,
                    projected_utilization=76.8,
                    utilization_trend=[65.0, 67.0, 69.0, 71.0, 71.3],
                    capacity_unit="vcpus",
                    cost_per_unit=0.125,
                    region="us-central1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} GCP database resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP database capacity: {e}")
            return []
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get GCP memory capacity information"""
        try:
            resources = []
            
            # Memory is included in compute resources
            logger.info(f"Collected {len(resources)} GCP memory resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP memory capacity: {e}")
            return []

class OnPremCapacityPlanningHandler(CapacityPlanningHandler):
    """On-premise capacity planning operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use various monitoring systems
            logger.info("On-premise capacity handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_compute_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise compute resource capacity information"""
        try:
            resources = []
            
            # Simulate on-premise compute capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="onprem-server-1",
                    resource_name="web-server-physical",
                    resource_type="compute",
                    provider="onprem",
                    current_capacity=8.0,
                    current_utilization=72.6,
                    projected_utilization=78.9,
                    utilization_trend=[68.0, 69.0, 70.0, 71.0, 72.6],
                    capacity_unit="vcpus",
                    cost_per_unit=0.025,
                    region="datacenter-1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} on-premise compute resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise compute capacity: {e}")
            return []
    
    def get_storage_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise storage resource capacity information"""
        try:
            resources = []
            
            # Simulate on-premise storage capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="onprem-storage-1",
                    resource_name="san-array-1",
                    resource_type="storage",
                    provider="onprem",
                    current_capacity=1000.0,
                    current_utilization=85.4,
                    projected_utilization=92.1,
                    utilization_trend=[80.0, 82.0, 84.0, 85.0, 85.4],
                    capacity_unit="gb",
                    cost_per_unit=0.015,
                    region="datacenter-1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} on-premise storage resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise storage capacity: {e}")
            return []
    
    def get_networking_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise networking resource capacity information"""
        try:
            resources = []
            
            # Simulate on-premise networking capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="onprem-switch-1",
                    resource_name="core-switch-01",
                    resource_type="networking",
                    provider="onprem",
                    current_capacity=500.0,
                    current_utilization=45.8,
                    projected_utilization=52.3,
                    utilization_trend=[42.0, 43.0, 44.0, 45.0, 45.8],
                    capacity_unit="ports",
                    cost_per_unit=0.010,
                    region="datacenter-1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} on-premise networking resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise networking capacity: {e}")
            return []
    
    def get_database_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise database capacity information"""
        try:
            resources = []
            
            # Simulate on-premise database capacity data
            sample_resources = [
                ResourceCapacity(
                    resource_id="onprem-db-1",
                    resource_name="mysql-server-01",
                    resource_type="database",
                    provider="onprem",
                    current_capacity=4.0,
                    current_utilization=68.7,
                    projected_utilization=74.2,
                    utilization_trend=[64.0, 65.0, 66.0, 67.0, 68.7],
                    capacity_unit="vcpus",
                    cost_per_unit=0.035,
                    region="datacenter-1"
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Collected {len(resources)} on-premise database resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise database capacity: {e}")
            return []
    
    def get_memory_capacity(self) -> List[ResourceCapacity]:
        """Get on-premise memory capacity information"""
        try:
            resources = []
            
            # Memory is included in compute resources
            logger.info(f"Collected {len(resources)} on-premise memory resources")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise memory capacity: {e}")
            return []

def get_capacity_handler(provider: str, region: str = "us-west-2") -> CapacityPlanningHandler:
    """Get appropriate capacity planning handler"""
    handlers = {
        'aws': AWSCapacityPlanningHandler,
        'azure': AzureCapacityPlanningHandler,
        'gcp': GCPCapacityPlanningHandler,
        'onprem': OnPremCapacityPlanningHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
