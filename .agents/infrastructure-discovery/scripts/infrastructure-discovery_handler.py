#!/usr/bin/env python3
"""
Infrastructure Discovery Handler

Cloud-specific operations handler for infrastructure discovery across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class InfrastructureResource:
    id: str
    name: str
    type: str
    provider: str
    region: str
    status: str
    metadata: Dict[str, Any]

class InfrastructureHandler(ABC):
    """Abstract base class for cloud-specific infrastructure operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def discover_resources(self, resource_types: List[str]) -> List[InfrastructureResource]:
        """Discover infrastructure resources"""
        pass
    
    @abstractmethod
    def get_resource_details(self, resource_id: str) -> Dict[str, Any]:
        """Get detailed resource information"""
        pass
    
    @abstractmethod
    def analyze_dependencies(self) -> List[Dict[str, Any]]:
        """Analyze resource dependencies"""
        pass

class AWSInfrastructureHandler(InfrastructureHandler):
    """AWS-specific infrastructure discovery"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ec2': boto3.client('ec2', region_name=self.region),
                'ecs': boto3.client('ecs', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                'elb': boto3.client('elbv2', region_name=self.region),
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
    
    def discover_resources(self, resource_types: List[str]) -> List[InfrastructureResource]:
        """Discover AWS resources"""
        resources = []
        
        try:
            if 'ec2' in resource_types:
                instances = self._discover_ec2_instances()
                resources.extend(instances)
            
            if 'ecs' in resource_types:
                services = self._discover_ecs_services()
                resources.extend(services)
            
            if 'rds' in resource_types:
                databases = self._discover_rds_instances()
                resources.extend(databases)
            
            if 'elb' in resource_types:
                load_balancers = self._discover_load_balancers()
                resources.extend(load_balancers)
                
        except Exception as e:
            logger.error(f"Failed to discover AWS resources: {e}")
        
        return resources
    
    def _discover_ec2_instances(self) -> List[InfrastructureResource]:
        """Discover EC2 instances"""
        try:
            response = self.client['ec2'].describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    resource = InfrastructureResource(
                        id=instance['InstanceId'],
                        name=instance.get('Tags', [{}])[0].get('Value', instance['InstanceId']),
                        type='ec2_instance',
                        provider='aws',
                        region=self.region,
                        status=instance['State']['Name'],
                        metadata={
                            'instance_type': instance['InstanceType'],
                            'public_ip': instance.get('PublicIpAddress'),
                            'private_ip': instance.get('PrivateIpAddress'),
                            'launch_time': instance['LaunchTime'].isoformat()
                        }
                    )
                    instances.append(resource)
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to discover EC2 instances: {e}")
            return []
    
    def _discover_ecs_services(self) -> List[InfrastructureResource]:
        """Discover ECS services"""
        try:
            clusters = self.client['ecs'].list_clusters()
            services = []
            
            for cluster_arn in clusters['clusterArns']:
                cluster_name = cluster_arn.split('/')[-1]
                service_list = self.client['ecs'].list_services(cluster=cluster_name)
                
                for service_arn in service_list['serviceArns']:
                    service_name = service_arn.split('/')[-1]
                    service_desc = self.client['ecs'].describe_services(
                        cluster=cluster_name, services=[service_name]
                    )
                    
                    if service_desc['services']:
                        service = service_desc['services'][0]
                        resource = InfrastructureResource(
                            id=service_arn,
                            name=service_name,
                            type='ecs_service',
                            provider='aws',
                            region=self.region,
                            status=service['status'],
                            metadata={
                                'cluster': cluster_name,
                                'desired_count': service['desiredCount'],
                                'running_count': service['runningCount'],
                                'task_definition': service['taskDefinition']
                            }
                        )
                        services.append(resource)
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to discover ECS services: {e}")
            return []
    
    def _discover_rds_instances(self) -> List[InfrastructureResource]:
        """Discover RDS instances"""
        try:
            response = self.client['rds'].describe_db_instances()
            databases = []
            
            for db_instance in response['DBInstances']:
                resource = InfrastructureResource(
                    id=db_instance['DBInstanceIdentifier'],
                    name=db_instance['DBInstanceIdentifier'],
                    type='rds_instance',
                    provider='aws',
                    region=self.region,
                    status=db_instance['DBInstanceStatus'],
                    metadata={
                        'engine': db_instance['Engine'],
                        'engine_version': db_instance['EngineVersion'],
                        'instance_class': db_instance['DBInstanceClass'],
                        'allocated_storage': db_instance['AllocatedStorage'],
                        'multi_az': db_instance['MultiAZ']
                    }
                )
                databases.append(resource)
            
            return databases
            
        except Exception as e:
            logger.error(f"Failed to discover RDS instances: {e}")
            return []
    
    def _discover_load_balancers(self) -> List[InfrastructureResource]:
        """Discover Load Balancers"""
        try:
            response = self.client['elb'].describe_load_balancers()
            load_balancers = []
            
            for lb in response['LoadBalancers']:
                resource = InfrastructureResource(
                    id=lb['LoadBalancerArn'],
                    name=lb['LoadBalancerName'],
                    type='load_balancer',
                    provider='aws',
                    region=self.region,
                    status=lb['State']['Code'],
                    metadata={
                        'type': lb['Type'],
                        'scheme': lb['Scheme'],
                        'vpc_id': lb['VpcId'],
                        'availability_zones': [az['ZoneName'] for az in lb['AvailabilityZones']]
                    }
                )
                load_balancers.append(resource)
            
            return load_balancers
            
        except Exception as e:
            logger.error(f"Failed to discover Load Balancers: {e}")
            return []
    
    def get_resource_details(self, resource_id: str) -> Dict[str, Any]:
        """Get detailed AWS resource information"""
        try:
            # Determine resource type and get details
            if resource_id.startswith('i-'):
                # EC2 instance
                response = self.client['ec2'].describe_instances(InstanceIds=[resource_id])
                return response['Reservations'][0]['Instances'][0]
            elif '/' in resource_id:
                # ECS service or other ARN
                resource_type = resource_id.split(':')[2]
                if resource_type == 'ecs':
                    parts = resource_id.split('/')
                    cluster_name = parts[1]
                    service_name = parts[2]
                    response = self.client['ecs'].describe_services(
                        cluster=cluster_name, services=[service_name]
                    )
                    return response['services'][0] if response['services'] else {}
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get AWS resource details: {e}")
            return {}
    
    def analyze_dependencies(self) -> List[Dict[str, Any]]:
        """Analyze AWS resource dependencies"""
        try:
            dependencies = []
            
            # Analyze CloudFormation stacks for dependencies
            stacks = self.client['cloudformation'].list_stacks()
            
            for stack_summary in stacks['StackSummaries']:
                if stack_summary['StackStatus'] != 'DELETE_COMPLETE':
                    try:
                        resources = self.client['cloudformation'].describe_stack_resources(
                            StackName=stack_summary['StackName']
                        )
                        
                        for resource in resources['StackResources']:
                            dependencies.append({
                                'source_id': stack_summary['StackName'],
                                'target_id': resource['PhysicalResourceId'],
                                'relationship_type': 'contains',
                                'resource_type': resource['ResourceType']
                            })
                    except Exception:
                        continue
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Failed to analyze AWS dependencies: {e}")
            return []

class AzureInfrastructureHandler(InfrastructureHandler):
    """Azure-specific infrastructure discovery"""
    
    def initialize_client(self) -> bool:
        """Initialize Azure clients"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
            from azure.mgmt.compute import ComputeManagementClient
            from azure.mgmt.sql import SqlManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'resource': ResourceManagementClient(credential, "<subscription-id>"),
                'compute': ComputeManagementClient(credential, "<subscription-id>"),
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
    
    def discover_resources(self, resource_types: List[str]) -> List[InfrastructureResource]:
        """Discover Azure resources"""
        resources = []
        
        try:
            if 'vm' in resource_types:
                vms = self._discover_virtual_machines()
                resources.extend(vms)
            
            if 'sql' in resource_types:
                databases = self._discover_sql_databases()
                resources.extend(databases)
                
        except Exception as e:
            logger.error(f"Failed to discover Azure resources: {e}")
        
        return resources
    
    def _discover_virtual_machines(self) -> List[InfrastructureResource]:
        """Discover Azure VMs"""
        try:
            vms = []
            for vm in self.client['compute'].virtual_machines.list_all():
                resource = InfrastructureResource(
                    id=vm.id,
                    name=vm.name,
                    type='virtual_machine',
                    provider='azure',
                    region=vm.location,
                    status='running' if vm.instance_view else 'unknown',
                    metadata={
                        'vm_size': vm.hardware_profile.vm_size if vm.hardware_profile else None,
                        'os_type': vm.storage_profile.os_disk.os_type.value if vm.storage_profile and vm.storage_profile.os_disk else None
                    }
                )
                vms.append(resource)
            return vms
        except Exception as e:
            logger.error(f"Failed to discover Azure VMs: {e}")
            return []
    
    def _discover_sql_databases(self) -> List[InfrastructureResource]:
        """Discover Azure SQL databases"""
        try:
            databases = []
            for db in self.client['sql'].databases.list_by_server("<resource-group>", "<server>"):
                resource = InfrastructureResource(
                    id=db.id,
                    name=db.name,
                    type='sql_database',
                    provider='azure',
                    region=db.location,
                    status='available',
                    metadata={
                        'collation': db.collation,
                        'create_mode': db.create_mode,
                        'max_size_bytes': db.max_size_bytes
                    }
                )
                databases.append(resource)
            return databases
        except Exception as e:
            logger.error(f"Failed to discover Azure SQL databases: {e}")
            return []
    
    def get_resource_details(self, resource_id: str) -> Dict[str, Any]:
        """Get detailed Azure resource information"""
        try:
            # Placeholder for Azure resource details
            return {
                'resource_id': resource_id,
                'details': 'Azure resource details placeholder'
            }
        except Exception as e:
            logger.error(f"Failed to get Azure resource details: {e}")
            return {}
    
    def analyze_dependencies(self) -> List[Dict[str, Any]]:
        """Analyze Azure resource dependencies"""
        try:
            # Placeholder for Azure dependency analysis
            return [
                {
                    'source_id': 'azure-resource-group',
                    'target_id': 'azure-resource',
                    'relationship_type': 'contains',
                    'resource_type': 'Resource'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to analyze Azure dependencies: {e}")
            return []

class GCPInfrastructureHandler(InfrastructureHandler):
    """GCP-specific infrastructure discovery"""
    
    def initialize_client(self) -> bool:
        """Initialize GCP clients"""
        try:
            from google.cloud import compute_v1
            from google.cloud import resourcemanager_v3
            
            self.client = {
                'compute': compute_v1.InstancesClient(),
                'resource_manager': resourcemanager_v3.ProjectsClient()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def discover_resources(self, resource_types: List[str]) -> List[InfrastructureResource]:
        """Discover GCP resources"""
        resources = []
        
        try:
            if 'compute' in resource_types:
                instances = self._discover_compute_instances()
                resources.extend(instances)
                
        except Exception as e:
            logger.error(f"Failed to discover GCP resources: {e}")
        
        return resources
    
    def _discover_compute_instances(self) -> List[InfrastructureResource]:
        """Discover GCP Compute instances"""
        try:
            instances = []
            request = compute_v1.ListInstancesRequest(
                project="<project-id>",
                zone=self.region
            )
            
            for instance in self.client['compute'].list(request=request):
                resource = InfrastructureResource(
                    id=str(instance.id),
                    name=instance.name,
                    type='compute_instance',
                    provider='gcp',
                    region=self.region,
                    status=instance.status,
                    metadata={
                        'machine_type': instance.machine_type.split('/')[-1],
                        'creation_timestamp': instance.creation_timestamp
                    }
                )
                instances.append(resource)
            
            return instances
        except Exception as e:
            logger.error(f"Failed to discover GCP Compute instances: {e}")
            return []
    
    def get_resource_details(self, resource_id: str) -> Dict[str, Any]:
        """Get detailed GCP resource information"""
        try:
            # Placeholder for GCP resource details
            return {
                'resource_id': resource_id,
                'details': 'GCP resource details placeholder'
            }
        except Exception as e:
            logger.error(f"Failed to get GCP resource details: {e}")
            return {}
    
    def analyze_dependencies(self) -> List[Dict[str, Any]]:
        """Analyze GCP resource dependencies"""
        try:
            # Placeholder for GCP dependency analysis
            return [
                {
                    'source_id': 'gcp-project',
                    'target_id': 'gcp-resource',
                    'relationship_type': 'contains',
                    'resource_type': 'Resource'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to analyze GCP dependencies: {e}")
            return []

class OnPremInfrastructureHandler(InfrastructureHandler):
    """On-premise infrastructure discovery"""
    
    def initialize_client(self) -> bool:
        """Initialize on-premise clients"""
        try:
            import kubernetes
            kubernetes.config.load_kube_config()
            self.client = kubernetes.client.CoreV1Api()
            logger.info("Kubernetes client initialized for on-premise")
            return True
        except ImportError:
            logger.error("Kubernetes client not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def discover_resources(self, resource_types: List[str]) -> List[InfrastructureResource]:
        """Discover on-premise resources"""
        resources = []
        
        try:
            if 'kubernetes' in resource_types:
                pods = self._discover_kubernetes_pods()
                resources.extend(pods)
                
        except Exception as e:
            logger.error(f"Failed to discover on-premise resources: {e}")
        
        return resources
    
    def _discover_kubernetes_pods(self) -> List[InfrastructureResource]:
        """Discover Kubernetes pods"""
        try:
            pods = []
            pod_list = self.client.list_pod_for_all_namespaces()
            
            for pod in pod_list.items:
                resource = InfrastructureResource(
                    id=pod.metadata.uid,
                    name=pod.metadata.name,
                    type='kubernetes_pod',
                    provider='onprem',
                    region=pod.metadata.namespace,
                    status=pod.status.phase,
                    metadata={
                        'namespace': pod.metadata.namespace,
                        'node_name': pod.spec.node_name,
                        'pod_ip': pod.status.pod_ip,
                        'creation_timestamp': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                    }
                )
                pods.append(resource)
            
            return pods
        except Exception as e:
            logger.error(f"Failed to discover Kubernetes pods: {e}")
            return []
    
    def get_resource_details(self, resource_id: str) -> Dict[str, Any]:
        """Get detailed on-premise resource information"""
        try:
            # Placeholder for on-premise resource details
            return {
                'resource_id': resource_id,
                'details': 'On-premise resource details placeholder'
            }
        except Exception as e:
            logger.error(f"Failed to get on-premise resource details: {e}")
            return {}
    
    def analyze_dependencies(self) -> List[Dict[str, Any]]:
        """Analyze on-premise resource dependencies"""
        try:
            # Placeholder for on-premise dependency analysis
            return [
                {
                    'source_id': 'kubernetes-namespace',
                    'target_id': 'kubernetes-pod',
                    'relationship_type': 'contains',
                    'resource_type': 'Kubernetes'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to analyze on-premise dependencies: {e}")
            return []

def get_infrastructure_handler(provider: str, region: str = "us-west-2") -> InfrastructureHandler:
    """Get appropriate infrastructure handler"""
    handlers = {
        'aws': AWSInfrastructureHandler,
        'azure': AzureInfrastructureHandler,
        'gcp': GCPInfrastructureHandler,
        'onprem': OnPremInfrastructureHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
