#!/usr/bin/env python3
"""
Resource Optimizer Handler

Cloud-specific operations handler for resource utilization analysis and optimization across multi-cloud environments.
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
class ResourceUtilization:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    region: str
    environment: str
    current_capacity: float
    current_utilization: float
    peak_utilization: float
    average_utilization: float
    utilization_trend: str  # increasing, decreasing, stable
    cost_per_hour: float
    monthly_cost: float
    tags: Dict[str, Any]

@dataclass
class OptimizationRecommendation:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    current_state: Dict[str, Any]
    recommended_action: str
    recommended_capacity: float
    estimated_savings: float
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    confidence: float
    rationale: str
    implementation_steps: List[str]

class ResourceOptimizerHandler(ABC):
    """Abstract base class for cloud-specific resource optimization operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def get_compute_utilization(self) -> List[ResourceUtilization]:
        """Get compute resource utilization data"""
        pass
    
    @abstractmethod
    def get_storage_utilization(self) -> List[ResourceUtilization]:
        """Get storage resource utilization data"""
        pass
    
    @abstractmethod
    def get_network_utilization(self) -> List[ResourceUtilization]:
        """Get network resource utilization data"""
        pass
    
    @abstractmethod
    def get_database_utilization(self) -> List[ResourceUtilization]:
        """Get database resource utilization data"""
        pass
    
    @abstractmethod
    def generate_optimization_recommendations(self, resources: List[ResourceUtilization]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations"""
        pass

class AWSResourceOptimizerHandler(ResourceOptimizerHandler):
    """AWS-specific resource optimization operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ec2': boto3.client('ec2', region_name=self.region),
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                'ebs': boto3.client('ec2', region_name=self.region),  # EBS uses EC2 client
                'lambda': boto3.client('lambda', region_name=self.region),
                'elb': boto3.client('elbv2', region_name=self.region),
                'pricing': boto3.client('pricing', region_name='us-east-1')
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def get_compute_utilization(self) -> List[ResourceUtilization]:
        """Get AWS compute resource utilization data"""
        try:
            resources = []
            
            # Get EC2 instances
            ec2_resources = self._get_ec2_utilization()
            resources.extend(ec2_resources)
            
            # Get Lambda functions
            lambda_resources = self._get_lambda_utilization()
            resources.extend(lambda_resources)
            
            logger.info(f"Retrieved {len(resources)} AWS compute utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS compute utilization: {e}")
            return []
    
    def _get_ec2_utilization(self) -> List[ResourceUtilization]:
        """Get EC2 instance utilization metrics"""
        resources = []
        
        try:
            # Get all instances
            response = self.client['ec2'].describe_instances()
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'running':
                        continue
                    
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    
                    # Get tags
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    # Get CloudWatch metrics
                    utilization_data = self._get_ec2_metrics(instance_id)
                    
                    # Get pricing information
                    cost_per_hour = self._get_ec2_pricing(instance_type)
                    
                    resource = ResourceUtilization(
                        resource_id=instance_id,
                        resource_name=tags.get('Name', instance_id),
                        resource_type="ec2_instance",
                        provider="aws",
                        region=self.region,
                        environment=tags.get('Environment', 'unknown'),
                        current_capacity=self._get_instance_capacity(instance_type),
                        current_utilization=utilization_data['current_utilization'],
                        peak_utilization=utilization_data['peak_utilization'],
                        average_utilization=utilization_data['average_utilization'],
                        utilization_trend=utilization_data['trend'],
                        cost_per_hour=cost_per_hour,
                        monthly_cost=cost_per_hour * 730,  # 730 hours per month
                        tags=tags
                    )
                    
                    resources.append(resource)
            
        except Exception as e:
            logger.error(f"Failed to get EC2 utilization: {e}")
        
        return resources
    
    def _get_ec2_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Get EC2 CloudWatch metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            # Get CPU utilization
            cpu_response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average', 'Maximum']
            )
            
            cpu_data = cpu_response.get('Datapoints', [])
            
            if not cpu_data:
                return {
                    'current_utilization': 0.0,
                    'peak_utilization': 0.0,
                    'average_utilization': 0.0,
                    'trend': 'stable'
                }
            
            # Calculate metrics
            current_utilization = cpu_data[-1]['Average'] if cpu_data else 0.0
            peak_utilization = max(dp['Maximum'] for dp in cpu_data) if cpu_data else 0.0
            average_utilization = statistics.mean(dp['Average'] for dp in cpu_data) if cpu_data else 0.0
            
            # Determine trend (simplified)
            if len(cpu_data) >= 2:
                recent_avg = statistics.mean(dp['Average'] for dp in cpu_data[-3:])
                older_avg = statistics.mean(dp['Average'] for dp in cpu_data[:-3])
                
                if recent_avg > older_avg * 1.1:
                    trend = 'increasing'
                elif recent_avg < older_avg * 0.9:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            return {
                'current_utilization': current_utilization,
                'peak_utilization': peak_utilization,
                'average_utilization': average_utilization,
                'trend': trend
            }
        
        except Exception as e:
            logger.error(f"Failed to get EC2 metrics for {instance_id}: {e}")
            return {
                'current_utilization': 0.0,
                'peak_utilization': 0.0,
                'average_utilization': 0.0,
                'trend': 'stable'
            }
    
    def _get_instance_capacity(self, instance_type: str) -> float:
        """Get instance capacity in vCPUs"""
        capacity_mapping = {
            't3.micro': 2.0,
            't3.small': 2.0,
            't3.medium': 2.0,
            't3.large': 2.0,
            'm5.large': 2.0,
            'm5.xlarge': 4.0,
            'm5.2xlarge': 8.0,
            'm5.4xlarge': 16.0,
            'c5.large': 2.0,
            'c5.xlarge': 4.0,
            'c5.2xlarge': 8.0,
            'c5.4xlarge': 16.0,
            'r5.large': 2.0,
            'r5.xlarge': 4.0,
            'r5.2xlarge': 8.0,
            'r5.4xlarge': 16.0
        }
        
        return capacity_mapping.get(instance_type, 4.0)
    
    def _get_ec2_pricing(self, instance_type: str) -> float:
        """Get EC2 instance pricing (simplified)"""
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
    
    def _get_lambda_utilization(self) -> List[ResourceUtilization]:
        """Get Lambda function utilization metrics"""
        resources = []
        
        try:
            response = self.client['lambda'].list_functions()
            
            for function in response['Functions']:
                function_name = function['FunctionName']
                
                # Get CloudWatch metrics
                utilization_data = self._get_lambda_metrics(function_name)
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['lambda'].list_tags(Resource=function['FunctionArn'])
                    tags = tag_response.get('Tags', {})
                except:
                    pass
                
                # Calculate cost based on invocations and duration
                cost_per_hour = self._calculate_lambda_cost(function, utilization_data)
                
                resource = ResourceUtilization(
                    resource_id=function_name,
                    resource_name=tags.get('Name', function_name),
                    resource_type="lambda_function",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    current_capacity=function['MemorySize'] / 1024,  # Convert MB to GB
                    current_utilization=utilization_data['current_utilization'],
                    peak_utilization=utilization_data['peak_utilization'],
                    average_utilization=utilization_data['average_utilization'],
                    utilization_trend=utilization_data['trend'],
                    cost_per_hour=cost_per_hour,
                    monthly_cost=cost_per_hour * 730,
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to get Lambda utilization: {e}")
        
        return resources
    
    def _get_lambda_metrics(self, function_name: str) -> Dict[str, Any]:
        """Get Lambda CloudWatch metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            # Get duration metrics
            duration_response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            duration_data = duration_response.get('Datapoints', [])
            
            if not duration_data:
                return {
                    'current_utilization': 0.0,
                    'peak_utilization': 0.0,
                    'average_utilization': 0.0,
                    'trend': 'stable'
                }
            
            # Calculate utilization based on memory usage (simplified)
            current_utilization = min(duration_data[-1]['Average'] / 1000 * 100, 100) if duration_data else 0.0  # Normalize to percentage
            peak_utilization = min(max(dp['Maximum'] for dp in duration_data) / 1000 * 100, 100) if duration_data else 0.0
            average_utilization = min(statistics.mean(dp['Average'] for dp in duration_data) / 1000 * 100, 100) if duration_data else 0.0
            
            # Determine trend
            if len(duration_data) >= 2:
                recent_avg = statistics.mean(dp['Average'] for dp in duration_data[-3:])
                older_avg = statistics.mean(dp['Average'] for dp in duration_data[:-3])
                
                if recent_avg > older_avg * 1.1:
                    trend = 'increasing'
                elif recent_avg < older_avg * 0.9:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            return {
                'current_utilization': current_utilization,
                'peak_utilization': peak_utilization,
                'average_utilization': average_utilization,
                'trend': trend
            }
        
        except Exception as e:
            logger.error(f"Failed to get Lambda metrics for {function_name}: {e}")
            return {
                'current_utilization': 0.0,
                'peak_utilization': 0.0,
                'average_utilization': 0.0,
                'trend': 'stable'
            }
    
    def _calculate_lambda_cost(self, function: Dict[str, Any], utilization_data: Dict[str, Any]) -> float:
        """Calculate Lambda cost per hour (simplified)"""
        try:
            # Lambda pricing: $0.20 per 1M requests + $0.0000166667 per GB-second
            # This is a simplified calculation
            memory_gb = function['MemorySize'] / 1024
            avg_duration_ms = utilization_data['average_utilization'] * 10  # Simplified
            
            # Estimate requests per hour based on utilization
            requests_per_hour = max(utilization_data['average_utilization'] * 100, 1)
            
            request_cost = (requests_per_hour / 1000000) * 0.20
            compute_cost = (requests_per_hour * avg_duration_ms / 1000 * memory_gb) * 0.0000166667
            
            return request_cost + compute_cost
        
        except:
            return 0.01  # Fallback cost
    
    def get_storage_utilization(self) -> List[ResourceUtilization]:
        """Get AWS storage resource utilization data"""
        try:
            resources = []
            
            # Get EBS volumes
            ebs_resources = self._get_ebs_utilization()
            resources.extend(ebs_resources)
            
            # Get S3 buckets
            s3_resources = self._get_s3_utilization()
            resources.extend(s3_resources)
            
            logger.info(f"Retrieved {len(resources)} AWS storage utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS storage utilization: {e}")
            return []
    
    def _get_ebs_utilization(self) -> List[ResourceUtilization]:
        """Get EBS volume utilization metrics"""
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
                
                # Get CloudWatch metrics
                utilization_data = self._get_ebs_metrics(volume_id)
                
                # Calculate cost
                cost_per_hour = self._get_ebs_pricing(volume['VolumeType'], size_gb)
                
                resource = ResourceUtilization(
                    resource_id=volume_id,
                    resource_name=tags.get('Name', volume_id),
                    resource_type="ebs_volume",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    current_capacity=size_gb,
                    current_utilization=utilization_data['current_utilization'],
                    peak_utilization=utilization_data['peak_utilization'],
                    average_utilization=utilization_data['average_utilization'],
                    utilization_trend=utilization_data['trend'],
                    cost_per_hour=cost_per_hour,
                    monthly_cost=cost_per_hour * 730,
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to get EBS utilization: {e}")
        
        return resources
    
    def _get_ebs_metrics(self, volume_id: str) -> Dict[str, Any]:
        """Get EBS CloudWatch metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
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
            
            # Calculate utilization based on IOPS (simplified)
            total_ops = 0
            for dp in read_response.get('Datapoints', []):
                total_ops += dp['Sum']
            for dp in write_response.get('Datapoints', []):
                total_ops += dp['Sum']
            
            # Normalize to percentage (very simplified)
            avg_ops_per_hour = total_ops / 168 if total_ops > 0 else 0  # 168 hours in 7 days
            current_utilization = min(avg_ops_per_hour / 1000 * 100, 100)  # Assume 1000 IOPS as baseline
            
            return {
                'current_utilization': current_utilization,
                'peak_utilization': current_utilization,  # Simplified
                'average_utilization': current_utilization,
                'trend': 'stable'
            }
        
        except Exception as e:
            logger.error(f"Failed to get EBS metrics for {volume_id}: {e}")
            return {
                'current_utilization': 0.0,
                'peak_utilization': 0.0,
                'average_utilization': 0.0,
                'trend': 'stable'
            }
    
    def _get_ebs_pricing(self, volume_type: str, size_gb: float) -> float:
        """Get EBS volume pricing"""
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
    
    def _get_s3_utilization(self) -> List[ResourceUtilization]:
        """Get S3 bucket utilization metrics"""
        resources = []
        
        try:
            response = self.client['s3'].list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['s3'].get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tag_response['TagSet']}
                except:
                    pass
                
                # Get bucket size (simplified - would use CloudWatch metrics in production)
                size_gb = self._get_s3_bucket_size(bucket_name)
                utilization_data = self._get_s3_metrics(bucket_name)
                
                # Calculate cost
                cost_per_hour = self._get_s3_pricing(size_gb)
                
                resource = ResourceUtilization(
                    resource_id=bucket_name,
                    resource_name=tags.get('Name', bucket_name),
                    resource_type="s3_bucket",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    current_capacity=size_gb,
                    current_utilization=utilization_data['current_utilization'],
                    peak_utilization=utilization_data['peak_utilization'],
                    average_utilization=utilization_data['average_utilization'],
                    utilization_trend=utilization_data['trend'],
                    cost_per_hour=cost_per_hour,
                    monthly_cost=cost_per_hour * 730,
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to get S3 utilization: {e}")
        
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
    
    def _get_s3_metrics(self, bucket_name: str) -> Dict[str, Any]:
        """Get S3 bucket metrics (simplified)"""
        try:
            # This is a simplified implementation
            # In production, you would use CloudWatch metrics
            return {
                'current_utilization': 50.0,  # Assume 50% utilization
                'peak_utilization': 75.0,
                'average_utilization': 45.0,
                'trend': 'stable'
            }
        except:
            return {
                'current_utilization': 0.0,
                'peak_utilization': 0.0,
                'average_utilization': 0.0,
                'trend': 'stable'
            }
    
    def _get_s3_pricing(self, size_gb: float) -> float:
        """Get S3 pricing"""
        # S3 Standard pricing: $0.023 per GB for first 50 TB
        price_per_gb_month = 0.023
        return price_per_gb_month * size_gb / 730  # Convert to per hour
    
    def get_network_utilization(self) -> List[ResourceUtilization]:
        """Get AWS network resource utilization data"""
        try:
            resources = []
            
            # Get ELB/ALB utilization
            elb_resources = self._get_elb_utilization()
            resources.extend(elb_resources)
            
            logger.info(f"Retrieved {len(resources)} AWS network utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS network utilization: {e}")
            return []
    
    def _get_elb_utilization(self) -> List[ResourceUtilization]:
        """Get ELB/ALB utilization metrics"""
        resources = []
        
        try:
            response = self.client['elb'].describe_load_balancers()
            
            for lb in response['LoadBalancers']:
                lb_arn = lb['LoadBalancerArn']
                lb_name = lb['LoadBalancerName']
                
                # Get tags
                tags = {}
                try:
                    tag_response = self.client['elb'].describe_tags(ResourceArns=[lb_arn])
                    for tag_desc in tag_response['TagDescriptions']:
                        for tag in tag_desc['Tags']:
                            tags[tag['Key']] = tag['Value']
                except:
                    pass
                
                # Get CloudWatch metrics
                utilization_data = self._get_elb_metrics(lb_arn)
                
                # Calculate cost
                cost_per_hour = self._get_elb_pricing(lb['Type'])
                
                resource = ResourceUtilization(
                    resource_id=lb_arn,
                    resource_name=tags.get('Name', lb_name),
                    resource_type="load_balancer",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    current_capacity=1000.0,  # Simplified capacity metric
                    current_utilization=utilization_data['current_utilization'],
                    peak_utilization=utilization_data['peak_utilization'],
                    average_utilization=utilization_data['average_utilization'],
                    utilization_trend=utilization_data['trend'],
                    cost_per_hour=cost_per_hour,
                    monthly_cost=cost_per_hour * 730,
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to get ELB utilization: {e}")
        
        return resources
    
    def _get_elb_metrics(self, lb_arn: str) -> Dict[str, Any]:
        """Get ELB CloudWatch metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
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
            
            if not datapoints:
                return {
                    'current_utilization': 0.0,
                    'peak_utilization': 0.0,
                    'average_utilization': 0.0,
                    'trend': 'stable'
                }
            
            # Calculate utilization based on request count (simplified)
            total_requests = sum(dp['Sum'] for dp in datapoints)
            avg_requests_per_hour = total_requests / 168 if total_requests > 0 else 0
            
            # Normalize to percentage (assume 1000 requests/hour as 100%)
            current_utilization = min(avg_requests_per_hour / 1000 * 100, 100)
            peak_utilization = current_utilization  # Simplified
            average_utilization = current_utilization
            
            return {
                'current_utilization': current_utilization,
                'peak_utilization': peak_utilization,
                'average_utilization': average_utilization,
                'trend': 'stable'
            }
        
        except Exception as e:
            logger.error(f"Failed to get ELB metrics for {lb_arn}: {e}")
            return {
                'current_utilization': 0.0,
                'peak_utilization': 0.0,
                'average_utilization': 0.0,
                'trend': 'stable'
            }
    
    def _get_elb_pricing(self, lb_type: str) -> float:
        """Get ELB pricing"""
        pricing = {
            'application': 0.0225,  # $0.0225 per hour
            'network': 0.0225,
            'gateway': 0.0225,
            'classic': 0.0225
        }
        
        return pricing.get(lb_type.lower(), 0.0225)
    
    def get_database_utilization(self) -> List[ResourceUtilization]:
        """Get AWS database resource utilization data"""
        try:
            resources = []
            
            # Get RDS instances
            rds_resources = self._get_rds_utilization()
            resources.extend(rds_resources)
            
            logger.info(f"Retrieved {len(resources)} AWS database utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get AWS database utilization: {e}")
            return []
    
    def _get_rds_utilization(self) -> List[ResourceUtilization]:
        """Get RDS instance utilization metrics"""
        resources = []
        
        try:
            response = self.client['rds'].describe_db_instances()
            
            for db_instance in response['DBInstances']:
                if db_instance['DBInstanceStatus'] != 'available':
                    continue
                
                db_id = db_instance['DBInstanceIdentifier']
                instance_class = db_instance['DBInstanceClass']
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
                
                # Get CloudWatch metrics
                utilization_data = self._get_rds_metrics(db_id)
                
                # Calculate cost
                cost_per_hour = self._get_rds_pricing(instance_class, allocated_storage)
                
                resource = ResourceUtilization(
                    resource_id=db_id,
                    resource_name=tags.get('Name', db_id),
                    resource_type="rds_instance",
                    provider="aws",
                    region=self.region,
                    environment=tags.get('Environment', 'unknown'),
                    current_capacity=self._get_rds_capacity(instance_class),
                    current_utilization=utilization_data['current_utilization'],
                    peak_utilization=utilization_data['peak_utilization'],
                    average_utilization=utilization_data['average_utilization'],
                    utilization_trend=utilization_data['trend'],
                    cost_per_hour=cost_per_hour,
                    monthly_cost=cost_per_hour * 730,
                    tags=tags
                )
                
                resources.append(resource)
        
        except Exception as e:
            logger.error(f"Failed to get RDS utilization: {e}")
        
        return resources
    
    def _get_rds_metrics(self, db_id: str) -> Dict[str, Any]:
        """Get RDS CloudWatch metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            # Get CPU utilization
            cpu_response = self.client['cloudwatch'].get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            cpu_data = cpu_response.get('Datapoints', [])
            
            if not cpu_data:
                return {
                    'current_utilization': 0.0,
                    'peak_utilization': 0.0,
                    'average_utilization': 0.0,
                    'trend': 'stable'
                }
            
            current_utilization = cpu_data[-1]['Average'] if cpu_data else 0.0
            peak_utilization = max(dp['Maximum'] for dp in cpu_data) if cpu_data else 0.0
            average_utilization = statistics.mean(dp['Average'] for dp in cpu_data) if cpu_data else 0.0
            
            # Determine trend
            if len(cpu_data) >= 2:
                recent_avg = statistics.mean(dp['Average'] for dp in cpu_data[-3:])
                older_avg = statistics.mean(dp['Average'] for dp in cpu_data[:-3])
                
                if recent_avg > older_avg * 1.1:
                    trend = 'increasing'
                elif recent_avg < older_avg * 0.9:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            return {
                'current_utilization': current_utilization,
                'peak_utilization': peak_utilization,
                'average_utilization': average_utilization,
                'trend': trend
            }
        
        except Exception as e:
            logger.error(f"Failed to get RDS metrics for {db_id}: {e}")
            return {
                'current_utilization': 0.0,
                'peak_utilization': 0.0,
                'average_utilization': 0.0,
                'trend': 'stable'
            }
    
    def _get_rds_capacity(self, instance_class: str) -> float:
        """Get RDS instance capacity"""
        capacity_mapping = {
            'db.t3.micro': 2.0,
            'db.t3.small': 2.0,
            'db.t3.medium': 4.0,
            'db.t3.large': 4.0,
            'db.m5.large': 2.0,
            'db.m5.xlarge': 4.0,
            'db.m5.2xlarge': 8.0,
            'db.m5.4xlarge': 16.0,
            'db.r5.large': 2.0,
            'db.r5.xlarge': 4.0,
            'db.r5.2xlarge': 8.0,
            'db.r5.4xlarge': 16.0
        }
        
        return capacity_mapping.get(instance_class, 4.0)
    
    def _get_rds_pricing(self, instance_class: str, storage_gb: float) -> float:
        """Get RDS pricing (simplified)"""
        # Simplified pricing - in production, use AWS Pricing API
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
    
    def generate_optimization_recommendations(self, resources: List[ResourceUtilization]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for AWS resources"""
        recommendations = []
        
        for resource in resources:
            recommendation = self._analyze_resource_for_optimization(resource)
            if recommendation:
                recommendations.append(recommendation)
        
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        return recommendations
    
    def _analyze_resource_for_optimization(self, resource: ResourceUtilization) -> Optional[OptimizationRecommendation]:
        """Analyze a single resource and generate optimization recommendation"""
        try:
            # Determine optimization action based on utilization
            if resource.average_utilization < 20:
                return self._generate_scale_down_recommendation(resource)
            elif resource.average_utilization > 85:
                return self._generate_scale_up_recommendation(resource)
            elif resource.average_utilization < 40 and resource.resource_type in ['ec2_instance', 'rds_instance']:
                return self._generate_rightsize_recommendation(resource)
            elif resource.average_utilization < 10:
                return self._generate_decommission_recommendation(resource)
            else:
                return None  # No optimization needed
        
        except Exception as e:
            logger.error(f"Failed to analyze resource {resource.resource_id}: {e}")
            return None
    
    def _generate_scale_down_recommendation(self, resource: ResourceUtilization) -> OptimizationRecommendation:
        """Generate scale down recommendation"""
        current_capacity = resource.current_capacity
        recommended_capacity = current_capacity * 0.5  # Scale down by 50%
        
        estimated_savings = resource.monthly_cost * 0.5  # 50% cost reduction
        
        return OptimizationRecommendation(
            resource_id=resource.resource_id,
            resource_name=resource.resource_name,
            resource_type=resource.resource_type,
            provider=resource.provider,
            current_state={
                'capacity': current_capacity,
                'utilization': resource.average_utilization,
                'monthly_cost': resource.monthly_cost
            },
            recommended_action="scale_down",
            recommended_capacity=recommended_capacity,
            estimated_savings=estimated_savings,
            implementation_effort="medium",
            risk_level="low",
            confidence=0.8,
            rationale=f"Resource is underutilized at {resource.average_utilization:.1f}% average utilization. Scaling down can reduce costs while maintaining performance.",
            implementation_steps=[
                f"Create backup of {resource.resource_name}",
                f"Scale down {resource.resource_type} from {current_capacity} to {recommended_capacity}",
                "Monitor performance for 24-48 hours",
                "Rollback if performance issues occur"
            ]
        )
    
    def _generate_scale_up_recommendation(self, resource: ResourceUtilization) -> OptimizationRecommendation:
        """Generate scale up recommendation"""
        current_capacity = resource.current_capacity
        recommended_capacity = current_capacity * 1.5  # Scale up by 50%
        
        estimated_savings = -resource.monthly_cost * 0.5  # Cost increase (negative savings)
        
        return OptimizationRecommendation(
            resource_id=resource.resource_id,
            resource_name=resource.resource_name,
            resource_type=resource.resource_type,
            provider=resource.provider,
            current_state={
                'capacity': current_capacity,
                'utilization': resource.average_utilization,
                'monthly_cost': resource.monthly_cost
            },
            recommended_action="scale_up",
            recommended_capacity=recommended_capacity,
            estimated_savings=estimated_savings,
            implementation_effort="medium",
            risk_level="medium",
            confidence=0.9,
            rationale=f"Resource is overutilized at {resource.average_utilization:.1f}% average utilization. Scaling up is required to maintain performance.",
            implementation_steps=[
                f"Scale up {resource.resource_type} from {current_capacity} to {recommended_capacity}",
                "Monitor performance improvements",
                "Validate application functionality",
                "Update monitoring thresholds"
            ]
        )
    
    def _generate_rightsize_recommendation(self, resource: ResourceUtilization) -> OptimizationRecommendation:
        """Generate rightsize recommendation"""
        current_capacity = resource.current_capacity
        recommended_capacity = current_capacity * 0.75  # Rightsize to 75%
        
        estimated_savings = resource.monthly_cost * 0.25  # 25% cost reduction
        
        return OptimizationRecommendation(
            resource_id=resource.resource_id,
            resource_name=resource.resource_name,
            resource_type=resource.resource_type,
            provider=resource.provider,
            current_state={
                'capacity': current_capacity,
                'utilization': resource.average_utilization,
                'monthly_cost': resource.monthly_cost
            },
            recommended_action="rightsize",
            recommended_capacity=recommended_capacity,
            estimated_savings=estimated_savings,
            implementation_effort="medium",
            risk_level="low",
            confidence=0.7,
            rationale=f"Resource has moderate utilization ({resource.average_utilization:.1f}%) but may be oversized. Rightsizing can optimize costs.",
            implementation_steps=[
                f"Analyze {resource.resource_name} usage patterns",
                f"Rightsize {resource.resource_type} from {current_capacity} to {recommended_capacity}",
                "Monitor for 48-72 hours",
                "Adjust if needed based on performance"
            ]
        )
    
    def _generate_decommission_recommendation(self, resource: ResourceUtilization) -> OptimizationRecommendation:
        """Generate decommission recommendation"""
        estimated_savings = resource.monthly_cost  # Full cost savings
        
        return OptimizationRecommendation(
            resource_id=resource.resource_id,
            resource_name=resource.resource_name,
            resource_type=resource.resource_type,
            provider=resource.provider,
            current_state={
                'capacity': resource.current_capacity,
                'utilization': resource.average_utilization,
                'monthly_cost': resource.monthly_cost
            },
            recommended_action="decommission",
            recommended_capacity=0.0,
            estimated_savings=estimated_savings,
            implementation_effort="low",
            risk_level="low",
            confidence=0.9,
            rationale=f"Resource is severely underutilized at {resource.average_utilization:.1f}% average utilization. Consider decommissioning if not needed.",
            implementation_steps=[
                f"Verify {resource.resource_name} is not in use",
                "Create final backup",
                f"Decommission {resource.resource_type}",
                "Update documentation and monitoring"
            ]
        )

# Simplified handlers for other providers
class AzureResourceOptimizerHandler(ResourceOptimizerHandler):
    """Azure-specific resource optimization operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.storage import StorageManagementClient
            from azure.mgmt.sql import SqlManagementClient
            from azure.monitor import MonitorManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'compute': ComputeManagementClient(credential, "<subscription-id>"),
                'storage': StorageManagementClient(credential, "<subscription-id>"),
                'sql': SqlManagementClient(credential, "<subscription-id>"),
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
    
    def get_compute_utilization(self) -> List[ResourceUtilization]:
        """Get Azure compute resource utilization data"""
        try:
            resources = []
            
            # Simulate Azure VM utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="azure-vm-1",
                    resource_name="web-server-01",
                    resource_type="virtual_machine",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    current_capacity=4.0,
                    current_utilization=35.0,
                    peak_utilization=65.0,
                    average_utilization=40.0,
                    utilization_trend="stable",
                    cost_per_hour=0.192,
                    monthly_cost=140.16,
                    tags={"Environment": "production", "Owner": "platform-team"}
                ),
                ResourceUtilization(
                    resource_id="azure-vm-2",
                    resource_name="app-server-01",
                    resource_type="virtual_machine",
                    provider="azure",
                    region="eastus",
                    environment="staging",
                    current_capacity=2.0,
                    current_utilization=15.0,
                    peak_utilization=25.0,
                    average_utilization=18.0,
                    utilization_trend="decreasing",
                    cost_per_hour=0.096,
                    monthly_cost=70.08,
                    tags={"Environment": "staging", "Owner": "dev-team"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} Azure compute utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure compute utilization: {e}")
            return []
    
    def get_storage_utilization(self) -> List[ResourceUtilization]:
        """Get Azure storage resource utilization data"""
        try:
            resources = []
            
            # Simulate Azure storage utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="azure-storage-1",
                    resource_name="data-storage-01",
                    resource_type="storage_account",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    current_capacity=500.0,
                    current_utilization=60.0,
                    peak_utilization=85.0,
                    average_utilization=65.0,
                    utilization_trend="increasing",
                    cost_per_hour=0.023,
                    monthly_cost=16.79,
                    tags={"Environment": "production", "DataClassification": "confidential"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} Azure storage utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure storage utilization: {e}")
            return []
    
    def get_network_utilization(self) -> List[ResourceUtilization]:
        """Get Azure network resource utilization data"""
        try:
            resources = []
            
            # Simulate Azure network utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="azure-lb-1",
                    resource_name="app-load-balancer",
                    resource_type="load_balancer",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    current_capacity=1000.0,
                    current_utilization=45.0,
                    peak_utilization=75.0,
                    average_utilization=50.0,
                    utilization_trend="stable",
                    cost_per_hour=0.0225,
                    monthly_cost=16.43,
                    tags={"Environment": "production", "Tier": "frontend"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} Azure network utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure network utilization: {e}")
            return []
    
    def get_database_utilization(self) -> List[ResourceUtilization]:
        """Get Azure database resource utilization data"""
        try:
            resources = []
            
            # Simulate Azure database utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="azure-sql-1",
                    resource_name="user-database-01",
                    resource_type="sql_database",
                    provider="azure",
                    region="eastus",
                    environment="production",
                    current_capacity=8.0,
                    current_utilization=55.0,
                    peak_utilization=90.0,
                    average_utilization=60.0,
                    utilization_trend="stable",
                    cost_per_hour=0.430,
                    monthly_cost=313.9,
                    tags={"Environment": "production", "DataClassification": "sensitive"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} Azure database utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Azure database utilization: {e}")
            return []
    
    def generate_optimization_recommendations(self, resources: List[ResourceUtilization]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for Azure resources"""
        recommendations = []
        
        for resource in resources:
            if resource.average_utilization < 20:
                recommendation = OptimizationRecommendation(
                    resource_id=resource.resource_id,
                    resource_name=resource.resource_name,
                    resource_type=resource.resource_type,
                    provider=resource.provider,
                    current_state={
                        'capacity': resource.current_capacity,
                        'utilization': resource.average_utilization,
                        'monthly_cost': resource.monthly_cost
                    },
                    recommended_action="scale_down",
                    recommended_capacity=resource.current_capacity * 0.5,
                    estimated_savings=resource.monthly_cost * 0.5,
                    implementation_effort="medium",
                    risk_level="low",
                    confidence=0.8,
                    rationale=f"Azure resource is underutilized at {resource.average_utilization:.1f}% average utilization.",
                    implementation_steps=["Scale down resource", "Monitor performance"]
                )
                recommendations.append(recommendation)
        
        return recommendations

class GCPResourceOptimizerHandler(ResourceOptimizerHandler):
    """GCP-specific resource optimization operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import compute_v1
            from google.cloud import storage
            from google.cloud import sql
            from google.cloud import monitoring
            
            self.client = {
                'compute': compute_v1.InstancesClient(),
                'storage': storage.Client(),
                'sql': sql.SQLAdminClient(),
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
    
    def get_compute_utilization(self) -> List[ResourceUtilization]:
        """Get GCP compute resource utilization data"""
        try:
            resources = []
            
            # Simulate GCP VM utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="gcp-vm-1",
                    resource_name="web-server-gcp",
                    resource_type="compute_instance",
                    provider="gcp",
                    region="us-central1",
                    environment="production",
                    current_capacity=4.0,
                    current_utilization=42.0,
                    peak_utilization=78.0,
                    average_utilization=45.0,
                    utilization_trend="stable",
                    cost_per_hour=0.190,
                    monthly_cost=138.7,
                    tags={"Environment": "production", "Team": "platform"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} GCP compute utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP compute utilization: {e}")
            return []
    
    def get_storage_utilization(self) -> List[ResourceUtilization]:
        """Get GCP storage resource utilization data"""
        try:
            resources = []
            
            # Simulate GCP storage utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="gcp-storage-1",
                    resource_name="data-bucket-01",
                    resource_type="storage_bucket",
                    provider="gcp",
                    region="us-central1",
                    environment="production",
                    current_capacity=250.0,
                    current_utilization=55.0,
                    peak_utilization=80.0,
                    average_utilization=60.0,
                    utilization_trend="increasing",
                    cost_per_hour=0.020,
                    monthly_cost=14.6,
                    tags={"Environment": "production", "Retention": "30-days"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} GCP storage utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP storage utilization: {e}")
            return []
    
    def get_network_utilization(self) -> List[ResourceUtilization]:
        """Get GCP network resource utilization data"""
        try:
            resources = []
            
            # Simulate GCP network utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="gcp-lb-1",
                    resource_name="app-lb-01",
                    resource_type="load_balancer",
                    provider="gcp",
                    region="us-central1",
                    environment="production",
                    current_capacity=1000.0,
                    current_utilization=38.0,
                    peak_utilization=70.0,
                    average_utilization=42.0,
                    utilization_trend="stable",
                    cost_per_hour=0.0225,
                    monthly_cost=16.43,
                    tags={"Environment": "production", "Protocol": "http"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} GCP network utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP network utilization: {e}")
            return []
    
    def get_database_utilization(self) -> List[ResourceUtilization]:
        """Get GCP database resource utilization data"""
        try:
            resources = []
            
            # Simulate GCP database utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="gcp-sql-1",
                    resource_name="user-db-01",
                    resource_type="cloud_sql",
                    provider="gcp",
                    region="us-central1",
                    environment="production",
                    current_capacity=4.0,
                    current_utilization=48.0,
                    peak_utilization=85.0,
                    average_utilization=52.0,
                    utilization_trend="stable",
                    cost_per_hour=0.215,
                    monthly_cost=156.95,
                    tags={"Environment": "production", "Backup": "enabled"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} GCP database utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get GCP database utilization: {e}")
            return []
    
    def generate_optimization_recommendations(self, resources: List[ResourceUtilization]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for GCP resources"""
        recommendations = []
        
        for resource in resources:
            if resource.average_utilization < 25:
                recommendation = OptimizationRecommendation(
                    resource_id=resource.resource_id,
                    resource_name=resource.resource_name,
                    resource_type=resource.resource_type,
                    provider=resource.provider,
                    current_state={
                        'capacity': resource.current_capacity,
                        'utilization': resource.average_utilization,
                        'monthly_cost': resource.monthly_cost
                    },
                    recommended_action="rightsize",
                    recommended_capacity=resource.current_capacity * 0.75,
                    estimated_savings=resource.monthly_cost * 0.25,
                    implementation_effort="medium",
                    risk_level="low",
                    confidence=0.7,
                    rationale=f"GCP resource has moderate utilization at {resource.average_utilization:.1f}% average.",
                    implementation_steps=["Rightsize resource", "Monitor performance"]
                )
                recommendations.append(recommendation)
        
        return recommendations

class OnPremResourceOptimizerHandler(ResourceOptimizerHandler):
    """On-premise resource optimization operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use various monitoring systems
            logger.info("On-premise resource optimizer handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_compute_utilization(self) -> List[ResourceUtilization]:
        """Get on-premise compute resource utilization data"""
        try:
            resources = []
            
            # Simulate on-premise server utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="onprem-server-1",
                    resource_name="database-server-01",
                    resource_type="physical_server",
                    provider="onprem",
                    region="datacenter-1",
                    environment="production",
                    current_capacity=16.0,
                    current_utilization=68.0,
                    peak_utilization=92.0,
                    average_utilization=70.0,
                    utilization_trend="stable",
                    cost_per_hour=0.050,
                    monthly_cost=36.5,
                    tags={"Environment": "production", "Location": "rack-a1"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} on-premise compute utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise compute utilization: {e}")
            return []
    
    def get_storage_utilization(self) -> List[ResourceUtilization]:
        """Get on-premise storage resource utilization data"""
        try:
            resources = []
            
            # Simulate on-premise storage utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="onprem-storage-1",
                    resource_name="nas-array-01",
                    resource_type="nas_storage",
                    provider="onprem",
                    region="datacenter-1",
                    environment="production",
                    current_capacity=2000.0,
                    current_utilization=72.0,
                    peak_utilization=88.0,
                    average_utilization=75.0,
                    utilization_trend="increasing",
                    cost_per_hour=0.015,
                    monthly_cost=10.95,
                    tags={"Environment": "production", "Tier": "gold"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} on-premise storage utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise storage utilization: {e}")
            return []
    
    def get_network_utilization(self) -> List[ResourceUtilization]:
        """Get on-premise network resource utilization data"""
        try:
            resources = []
            
            # Simulate on-premise network utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="onprem-switch-1",
                    resource_name="core-switch-01",
                    resource_type="network_switch",
                    provider="onprem",
                    region="datacenter-1",
                    environment="production",
                    current_capacity=10000.0,
                    current_utilization=52.0,
                    peak_utilization=78.0,
                    average_utilization=55.0,
                    utilization_trend="stable",
                    cost_per_hour=0.010,
                    monthly_cost=7.30,
                    tags={"Environment": "production", "VLAN": "production"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} on-premise network utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise network utilization: {e}")
            return []
    
    def get_database_utilization(self) -> List[ResourceUtilization]:
        """Get on-premise database resource utilization data"""
        try:
            resources = []
            
            # Simulate on-premise database utilization
            sample_resources = [
                ResourceUtilization(
                    resource_id="onprem-db-1",
                    resource_name="oracle-db-01",
                    resource_type="oracle_database",
                    provider="onprem",
                    region="datacenter-1",
                    environment="production",
                    current_capacity=32.0,
                    current_utilization=75.0,
                    peak_utilization=95.0,
                    average_utilization=78.0,
                    utilization_trend="stable",
                    cost_per_hour=0.100,
                    monthly_cost=73.0,
                    tags={"Environment": "production", "Version": "19c"}
                )
            ]
            
            resources.extend(sample_resources)
            
            logger.info(f"Retrieved {len(resources)} on-premise database utilization metrics")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get on-premise database utilization: {e}")
            return []
    
    def generate_optimization_recommendations(self, resources: List[ResourceUtilization]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for on-premise resources"""
        recommendations = []
        
        for resource in resources:
            if resource.average_utilization > 85:
                recommendation = OptimizationRecommendation(
                    resource_id=resource.resource_id,
                    resource_name=resource.resource_name,
                    resource_type=resource.resource_type,
                    provider=resource.provider,
                    current_state={
                        'capacity': resource.current_capacity,
                        'utilization': resource.average_utilization,
                        'monthly_cost': resource.monthly_cost
                    },
                    recommended_action="scale_up",
                    recommended_capacity=resource.current_capacity * 1.25,
                    estimated_savings=-resource.monthly_cost * 0.25,
                    implementation_effort="high",
                    risk_level="medium",
                    confidence=0.8,
                    rationale=f"On-premise resource is heavily utilized at {resource.average_utilization:.1f}% average.",
                    implementation_steps=["Upgrade hardware", "Migrate workload", "Monitor performance"]
                )
                recommendations.append(recommendation)
        
        return recommendations

def get_resource_optimizer_handler(provider: str, region: str = "us-west-2") -> ResourceOptimizerHandler:
    """Get appropriate resource optimizer handler"""
    handlers = {
        'aws': AWSResourceOptimizerHandler,
        'azure': AzureResourceOptimizerHandler,
        'gcp': GCPResourceOptimizerHandler,
        'onprem': OnPremResourceOptimizerHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
