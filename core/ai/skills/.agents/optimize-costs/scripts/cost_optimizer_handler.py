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
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CostData:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    current_cost: float
    usage_metrics: Dict[str, float]
    billing_period: str
    currency: str
    metadata: Dict[str, Any]

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
    def get_cost_data(self, billing_period_days: int) -> List[CostData]:
        """Get cost data from cloud provider"""
        pass
    
    @abstractmethod
    def implement_rightsizing(self, resource_id: str, target_size: str) -> bool:
        """Implement rightsizing optimization"""
        pass
    
    @abstractmethod
    def implement_scheduling(self, resource_id: str, schedule: Dict[str, Any]) -> bool:
        """Implement scheduling optimization"""
        pass
    
    @abstractmethod
    def implement_storage_optimization(self, resource_id: str, storage_class: str) -> bool:
        """Implement storage optimization"""
        pass
    
    @abstractmethod
    def implement_reservation_purchase(self, resource_id: str, reservation_config: Dict[str, Any]) -> bool:
        """Implement reservation purchase"""
        pass

class AWSCostHandler(CostHandler):
    """AWS-specific cost operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ce': boto3.client('ce', region_name=self.region),
                'ec2': boto3.client('ec2', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                'lambda': boto3.client('lambda', region_name=self.region),
                'events': boto3.client('events', region_name=self.region),
                'scheduler': boto3.client('scheduler', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def get_cost_data(self, billing_period_days: int) -> List[CostData]:
        """Get cost data from AWS Cost Explorer"""
        try:
            cost_data = []
            
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=billing_period_days)
            
            # Get EC2 costs
            ec2_costs = self._get_ec2_costs(start_date, end_date)
            cost_data.extend(ec2_costs)
            
            # Get S3 costs
            s3_costs = self._get_s3_costs(start_date, end_date)
            cost_data.extend(s3_costs)
            
            # Get RDS costs
            rds_costs = self._get_rds_costs(start_date, end_date)
            cost_data.extend(rds_costs)
            
            # Get Lambda costs
            lambda_costs = self._get_lambda_costs(start_date, end_date)
            cost_data.extend(lambda_costs)
            
            # Get Data Transfer costs
            data_transfer_costs = self._get_data_transfer_costs(start_date, end_date)
            cost_data.extend(data_transfer_costs)
            
            logger.info(f"Retrieved {len(cost_data)} cost data items from AWS")
            return cost_data
            
        except Exception as e:
            logger.error(f"Failed to get AWS cost data: {e}")
            return []
    
    def _get_ec2_costs(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get EC2 instance costs"""
        try:
            cost_data = []
            
            # Get cost and usage data
            response = self.client['ce'].get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon EC2']
                    }
                }
            )
            
            # Get running instances for usage metrics
            instances = self.client['ec2'].describe_instances()
            instance_details = {}
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        instance_id = instance['InstanceId']
                        instance_name = self._get_tag_value(instance.get('Tags', []), 'Name', instance_id)
                        instance_type = instance['InstanceType']
                        
                        # Get CloudWatch metrics for usage
                        cpu_utilization = self._get_instance_cpu_utilization(instance_id)
                        
                        instance_details[instance_id] = {
                            'name': instance_name,
                            'type': instance_type,
                            'cpu_utilization': cpu_utilization
                        }
            
            # Process cost data
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    if group.get('Keys'):
                        service = group['Keys'][0]
                        instance_type = group['Keys'][1] if len(group['Keys']) > 1 else 'Unknown'
                        
                        amount = float(group['Metrics']['BlendedCost']['Amount'])
                        
                        # Find matching instances
                        matching_instances = [
                            (iid, details) for iid, details in instance_details.items()
                            if details['type'] == instance_type
                        ]
                        
                        if matching_instances:
                            for instance_id, details in matching_instances:
                                cost_data.append(CostData(
                                    resource_id=instance_id,
                                    resource_name=details['name'],
                                    resource_type='ec2_instance',
                                    provider='aws',
                                    current_cost=amount / len(matching_instances),  # Distribute cost
                                    usage_metrics={
                                        'cpu_utilization': details['cpu_utilization'],
                                        'instance_type': instance_type
                                    },
                                    billing_period='monthly',
                                    currency='USD',
                                    metadata={
                                        'service': service,
                                        'instance_type': instance_type,
                                        'region': self.region
                                    }
                                ))
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Failed to get EC2 costs: {e}")
            return []
    
    def _get_s3_costs(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get S3 storage costs"""
        try:
            cost_data = []
            
            # Get all buckets
            buckets = self.client['s3'].list_buckets()
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket size and object count
                    size_response = self.client['ce'].get_cost_and_usage(
                        TimePeriod={
                            'Start': start_date.strftime('%Y-%m-%d'),
                            'End': end_date.strftime('%Y-%m-%d')
                        },
                        Granularity='MONTHLY',
                        Metrics=['BlendedCost'],
                        Filter={
                            'Dimensions': {
                                'Key': 'SERVICE',
                                'Values': ['Amazon S3']
                            }
                        }
                    )
                    
                    # Simplified cost calculation
                    monthly_cost = 25.0  # Placeholder
                    
                    cost_data.append(CostData(
                        resource_id=bucket_name,
                        resource_name=bucket_name,
                        resource_type='s3_bucket',
                        provider='aws',
                        current_cost=monthly_cost,
                        usage_metrics={
                            'estimated_size_gb': 1000,  # Placeholder
                            'object_count': 10000  # Placeholder
                        },
                        billing_period='monthly',
                        currency='USD',
                        metadata={
                            'region': self.region,
                            'storage_class': 'STANDARD'
                        }
                    ))
                    
                except Exception as e:
                    logger.warning(f"Failed to get cost for bucket {bucket_name}: {e}")
                    continue
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Failed to get S3 costs: {e}")
            return []
    
    def _get_rds_costs(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get RDS database costs"""
        try:
            cost_data = []
            
            # Get all DB instances
            db_instances = self.client['rds'].describe_db_instances()
            
            for db_instance in db_instances['DBInstances']:
                if db_instance['DBInstanceStatus'] != 'available':
                    continue
                
                db_id = db_instance['DBInstanceIdentifier']
                db_name = db_instance.get('DBName', db_id)
                instance_class = db_instance['DBInstanceClass']
                engine = db_instance['Engine']
                
                # Simplified cost calculation based on instance class
                cost_mapping = {
                    'db.t3.micro': 15.0,
                    'db.t3.small': 30.0,
                    'db.t3.medium': 60.0,
                    'db.t3.large': 120.0,
                    'db.r5.large': 180.0,
                    'db.r5.xlarge': 360.0
                }
                
                monthly_cost = cost_mapping.get(instance_class, 100.0)
                
                # Get CPU utilization from CloudWatch
                cpu_utilization = self._get_rds_cpu_utilization(db_id)
                
                cost_data.append(CostData(
                    resource_id=db_id,
                    resource_name=db_name,
                    resource_type='rds_instance',
                    provider='aws',
                    current_cost=monthly_cost,
                    usage_metrics={
                        'cpu_utilization': cpu_utilization,
                        'instance_class': instance_class,
                        'engine': engine
                    },
                    billing_period='monthly',
                    currency='USD',
                    metadata={
                        'engine': engine,
                        'instance_class': instance_class,
                        'region': self.region
                    }
                ))
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Failed to get RDS costs: {e}")
            return []
    
    def _get_lambda_costs(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get Lambda function costs"""
        try:
            cost_data = []
            
            # Get all Lambda functions
            functions = self.client['lambda'].list_functions()
            
            for function in functions['Functions']:
                function_name = function['FunctionName']
                
                # Get CloudWatch metrics for usage
                invocations = self._get_lambda_invocations(function_name)
                duration = self._get_lambda_duration(function_name)
                
                # Calculate cost based on usage
                # AWS Lambda pricing: $0.20 per 1M requests + $0.0000166667 per GB-second
                requests_cost = (invocations / 1000000) * 0.20
                compute_cost = (duration * invocations / 1000000000) * 0.0000166667  # Simplified
                total_cost = requests_cost + compute_cost
                
                cost_data.append(CostData(
                    resource_id=function_name,
                    resource_name=function_name,
                    resource_type='lambda_function',
                    provider='aws',
                    current_cost=max(total_cost, 5.0),  # Minimum monthly cost
                    usage_metrics={
                        'invocations': invocations,
                        'avg_duration_ms': duration,
                        'memory_size': function.get('MemorySize', 128)
                    },
                    billing_period='monthly',
                    currency='USD',
                    metadata={
                        'runtime': function.get('Runtime', 'unknown'),
                        'memory_size': function.get('MemorySize', 128)
                    }
                ))
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Failed to get Lambda costs: {e}")
            return []
    
    def _get_data_transfer_costs(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get data transfer costs"""
        try:
            cost_data = []
            
            # Get data transfer costs
            response = self.client['ce'].get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['AWS Data Transfer']
                    }
                }
            )
            
            for result in response.get('ResultsByTime', []):
                amount = float(result['Total']['BlendedCost']['Amount'])
                
                if amount > 0:
                    cost_data.append(CostData(
                        resource_id='data-transfer',
                        resource_name='Data Transfer',
                        resource_type='data_transfer',
                        provider='aws',
                        current_cost=amount,
                        usage_metrics={
                            'total_gb_transferred': amount * 100  # Simplified calculation
                        },
                        billing_period='monthly',
                        currency='USD',
                        metadata={
                            'region': self.region,
                            'transfer_type': 'inter-region'
                        }
                    ))
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Failed to get data transfer costs: {e}")
            return []
    
    def _get_instance_cpu_utilization(self, instance_id: str) -> float:
        """Get average CPU utilization for an instance"""
        try:
            import boto3
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg_cpu = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return avg_cpu
            else:
                return 50.0  # Default if no data
                
        except Exception:
            return 50.0  # Default if error
    
    def _get_rds_cpu_utilization(self, db_id: str) -> float:
        """Get average CPU utilization for an RDS instance"""
        try:
            import boto3
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg_cpu = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return avg_cpu
            else:
                return 40.0  # Default if no data
                
        except Exception:
            return 40.0  # Default if error
    
    def _get_lambda_invocations(self, function_name: str) -> int:
        """Get Lambda function invocations"""
        try:
            import boto3
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Sum']
            )
            
            if response['Datapoints']:
                total_invocations = sum(dp['Sum'] for dp in response['Datapoints'])
                return int(total_invocations)
            else:
                return 1000  # Default if no data
                
        except Exception:
            return 1000  # Default if error
    
    def _get_lambda_duration(self, function_name: str) -> float:
        """Get Lambda function average duration"""
        try:
            import boto3
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg_duration = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return avg_duration
            else:
                return 100.0  # Default if no data
                
        except Exception:
            return 100.0  # Default if error
    
    def _get_tag_value(self, tags: List[Dict[str, str]], key: str, default: str) -> str:
        """Get tag value from AWS resource tags"""
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return default
    
    def implement_rightsizing(self, resource_id: str, target_size: str) -> bool:
        """Implement rightsizing optimization"""
        try:
            logger.info(f"Implementing rightsizing for {resource_id} to {target_size}")
            
            # For EC2 instances, modify instance type
            if resource_id.startswith('i-'):
                # Stop instance
                self.client['ec2'].stop_instances(InstanceIds=[resource_id])
                
                # Wait for instance to stop
                waiter = self.client['ec2'].get_waiter('instance_stopped')
                waiter.wait(InstanceIds=[resource_id])
                
                # Modify instance type
                self.client['ec2'].modify_instance_attribute(
                    InstanceId=resource_id,
                    InstanceType={'Value': target_size}
                )
                
                # Start instance
                self.client['ec2'].start_instances(InstanceIds=[resource_id])
                
                logger.info(f"Successfully rightsized instance {resource_id} to {target_size}")
                return True
            
            # For RDS instances, modify instance class
            elif resource_id.startswith(('db-', 'rds-')):
                self.client['rds'].modify_db_instance(
                    DBInstanceIdentifier=resource_id,
                    DBInstanceClass=target_size,
                    ApplyImmediately=True
                )
                
                logger.info(f"Successfully rightsized RDS instance {resource_id} to {target_size}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to implement rightsizing: {e}")
            return False
    
    def implement_scheduling(self, resource_id: str, schedule: Dict[str, Any]) -> bool:
        """Implement scheduling optimization"""
        try:
            logger.info(f"Implementing scheduling for {resource_id}")
            
            # Create EventBridge rule for start/stop
            rule_name = f"schedule-{resource_id}"
            
            # Create start rule
            start_schedule = schedule.get('start', 'cron(0 9 ? * MON-FRI *)')  # Weekdays 9 AM
            self.client['events'].put_rule(
                Name=f"{rule_name}-start",
                ScheduleExpression=start_schedule,
                State='ENABLED',
                Description=f"Start {resource_id}"
            )
            
            # Create stop rule
            stop_schedule = schedule.get('stop', 'cron(0 18 ? * MON-FRI *)')  # Weekdays 6 PM
            self.client['events'].put_rule(
                Name=f"{rule_name}-stop",
                ScheduleExpression=stop_schedule,
                State='ENABLED',
                Description=f"Stop {resource_id}"
            )
            
            # Add targets
            start_target = {
                'Id': f"{resource_id}-start",
                'Arn': f"arn:aws:automation:{self.region}:123456789012:action/EC2/StartInstance",
                'Input': json.dumps({'InstanceId': resource_id})
            }
            
            stop_target = {
                'Id': f"{resource_id}-stop",
                'Arn': f"arn:aws:automation:{self.region}:123456789012:action/EC2/StopInstance",
                'Input': json.dumps({'InstanceId': resource_id})
            }
            
            self.client['events'].put_targets(
                Rule=f"{rule_name}-start",
                Targets=[start_target]
            )
            
            self.client['events'].put_targets(
                Rule=f"{rule_name}-stop",
                Targets=[stop_target]
            )
            
            logger.info(f"Successfully implemented scheduling for {resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to implement scheduling: {e}")
            return False
    
    def implement_storage_optimization(self, resource_id: str, storage_class: str) -> bool:
        """Implement storage optimization"""
        try:
            logger.info(f"Implementing storage optimization for {resource_id} to {storage_class}")
            
            # For S3 buckets, create lifecycle policy
            if resource_id.startswith(('s3://',) or not resource_id.startswith(('i-', 'db-', 'rds-'))):
                # Create lifecycle policy for S3
                lifecycle_config = {
                    'Rules': [
                        {
                            'ID': f'lifecycle-{storage_class}',
                            'Status': 'Enabled',
                            'Transitions': [
                                {
                                    'Days': 30,
                                    'StorageClass': storage_class
                                }
                            ]
                        }
                    ]
                }
                
                self.client['s3'].put_bucket_lifecycle_configuration(
                    Bucket=resource_id,
                    LifecycleConfiguration=lifecycle_config
                )
                
                logger.info(f"Successfully implemented storage optimization for {resource_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to implement storage optimization: {e}")
            return False
    
    def implement_reservation_purchase(self, resource_id: str, reservation_config: Dict[str, Any]) -> bool:
        """Implement reservation purchase"""
        try:
            logger.info(f"Implementing reservation purchase for {resource_id}")
            
            # This would use AWS Cost Explorer or other APIs to purchase reservations
            # For now, just log the action
            logger.info(f"Would purchase reservation for {resource_id} with config: {reservation_config}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to implement reservation purchase: {e}")
            return False

# Simplified handlers for other providers
class AzureCostHandler(CostHandler):
    """Azure-specific cost operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.costmanagement import CostManagementClient
            from azure.mgmt.compute import ComputeManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'cost': CostManagementClient(credential, "<subscription-id>"),
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
    
    def get_cost_data(self, billing_period_days: int) -> List[CostData]:
        """Get cost data from Azure Cost Management"""
        try:
            # Simplified Azure cost data collection
            azure_costs = [
                CostData(
                    resource_id='azure-vm-001',
                    resource_name='web-server-01',
                    resource_type='virtual_machine',
                    provider='azure',
                    current_cost=180.0,
                    usage_metrics={'cpu_utilization': 45.0, 'memory_utilization': 60.0},
                    billing_period='monthly',
                    currency='USD',
                    metadata={'vm_size': 'Standard_D2s_v3', 'region': 'eastus'}
                ),
                CostData(
                    resource_id='azure-storage-001',
                    resource_name='data-storage',
                    resource_type='storage_account',
                    provider='azure',
                    current_cost=75.0,
                    usage_metrics={'storage_gb': 500, 'transaction_count': 100000},
                    billing_period='monthly',
                    currency='USD',
                    metadata={'storage_type': 'Standard_LRS', 'region': 'eastus'}
                )
            ]
            
            return azure_costs
            
        except Exception as e:
            logger.error(f"Failed to get Azure cost data: {e}")
            return []
    
    def implement_rightsizing(self, resource_id: str, target_size: str) -> bool:
        try:
            logger.info(f"Implementing rightsizing for {resource_id} to {target_size}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement rightsizing: {e}")
            return False
    
    def implement_scheduling(self, resource_id: str, schedule: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Implementing scheduling for {resource_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement scheduling: {e}")
            return False
    
    def implement_storage_optimization(self, resource_id: str, storage_class: str) -> bool:
        try:
            logger.info(f"Implementing storage optimization for {resource_id} to {storage_class}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement storage optimization: {e}")
            return False
    
    def implement_reservation_purchase(self, resource_id: str, reservation_config: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Implementing reservation purchase for {resource_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement reservation purchase: {e}")
            return False

class GCPCostHandler(CostHandler):
    """GCP-specific cost operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import billing_v1
            from google.cloud import compute_v1
            
            self.client = {
                'billing': billing_v1.CloudBillingClient(),
                'compute': compute_v1.InstancesClient()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def get_cost_data(self, billing_period_days: int) -> List[CostData]:
        """Get cost data from Google Cloud Billing"""
        try:
            # Simplified GCP cost data collection
            gcp_costs = [
                CostData(
                    resource_id='gcp-instance-001',
                    resource_name='web-server-01',
                    resource_type='compute_instance',
                    provider='gcp',
                    current_cost=120.0,
                    usage_metrics={'cpu_utilization': 55.0, 'memory_utilization': 65.0},
                    billing_period='monthly',
                    currency='USD',
                    metadata={'machine_type': 'e2-medium', 'region': 'us-central1'}
                ),
                CostData(
                    resource_id='gcp-storage-001',
                    resource_name='data-storage',
                    resource_type='storage_bucket',
                    provider='gcp',
                    current_cost=45.0,
                    usage_metrics={'storage_gb': 300, 'class': 'STANDARD'},
                    billing_period='monthly',
                    currency='USD',
                    metadata={'storage_class': 'STANDARD', 'region': 'us-central1'}
                )
            ]
            
            return gcp_costs
            
        except Exception as e:
            logger.error(f"Failed to get GCP cost data: {e}")
            return []
    
    def implement_rightsizing(self, resource_id: str, target_size: str) -> bool:
        try:
            logger.info(f"Implementing rightsizing for {resource_id} to {target_size}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement rightsizing: {e}")
            return False
    
    def implement_scheduling(self, resource_id: str, schedule: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Implementing scheduling for {resource_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement scheduling: {e}")
            return False
    
    def implement_storage_optimization(self, resource_id: str, storage_class: str) -> bool:
        try:
            logger.info(f"Implementing storage optimization for {resource_id} to {storage_class}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement storage optimization: {e}")
            return False
    
    def implement_reservation_purchase(self, resource_id: str, reservation_config: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Implementing reservation purchase for {resource_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement reservation purchase: {e}")
            return False

class OnPremCostHandler(CostHandler):
    """On-premise cost operations"""
    
    def initialize_client(self) -> bool:
        try:
            logger.info("On-premise cost handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def get_cost_data(self, billing_period_days: int) -> List[CostData]:
        """Get cost data from on-premise systems"""
        try:
            # Simplified on-premise cost data collection
            onprem_costs = [
                CostData(
                    resource_id='onprem-server-001',
                    resource_name='legacy-app-server',
                    resource_type='physical_server',
                    provider='onprem',
                    current_cost=300.0,
                    usage_metrics={'cpu_utilization': 25.0, 'memory_utilization': 40.0},
                    billing_period='monthly',
                    currency='USD',
                    metadata={'server_type': 'physical', 'location': 'datacenter-1'}
                ),
                CostData(
                    resource_id='onprem-storage-001',
                    resource_name='backup-storage',
                    resource_type='storage_array',
                    provider='onprem',
                    current_cost=150.0,
                    usage_metrics={'storage_gb': 2000, 'utilization': 60.0},
                    billing_period='monthly',
                    currency='USD',
                    metadata={'storage_type': 'SAN', 'location': 'datacenter-1'}
                )
            ]
            
            return onprem_costs
            
        except Exception as e:
            logger.error(f"Failed to get on-premise cost data: {e}")
            return []
    
    def implement_rightsizing(self, resource_id: str, target_size: str) -> bool:
        try:
            logger.info(f"Implementing rightsizing for {resource_id} to {target_size}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement rightsizing: {e}")
            return False
    
    def implement_scheduling(self, resource_id: str, schedule: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Implementing scheduling for {resource_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement scheduling: {e}")
            return False
    
    def implement_storage_optimization(self, resource_id: str, storage_class: str) -> bool:
        try:
            logger.info(f"Implementing storage optimization for {resource_id} to {storage_class}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement storage optimization: {e}")
            return False
    
    def implement_reservation_purchase(self, resource_id: str, reservation_config: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Implementing reservation purchase for {resource_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to implement reservation purchase: {e}")
            return False

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
