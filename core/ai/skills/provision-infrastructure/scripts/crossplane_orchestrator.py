#!/usr/bin/env python3
"""
Crossplane-based Multi-Cloud Infrastructure Orchestrator

Replaces Terraform-based provisioning with Kubernetes-native Crossplane resources
while maintaining backwards compatibility with existing orchestration interfaces.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import yaml
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

class ResourceType(Enum):
    NETWORK = "network"
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    LOAD_BALANCER = "load_balancer"

@dataclass
class CrossplaneResource:
    """Crossplane resource specification"""
    api_version: str
    kind: str
    metadata: Dict[str, Any]
    spec: Dict[str, Any]
    namespace: str = "default"

@dataclass
class ResourceRequest:
    """Resource creation request"""
    name: str
    resource_type: ResourceType
    provider: CloudProvider
    region: str
    config: Dict[str, Any]
    tags: Optional[Dict[str, str]] = None

@dataclass
class ResourceStatus:
    """Resource status information"""
    name: str
    resource_type: ResourceType
    provider: CloudProvider
    status: str
    message: str
    metadata: Dict[str, Any]
    timestamp: datetime

class CrossplaneOrchestrator:
    """Crossplane-based multi-cloud orchestrator"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        """Initialize Crossplane orchestrator"""
        try:
            config.load_kube_config(config_file=kubeconfig_path)
        except:
            config.load_incluster_config()
        
        self.api_client = client.ApiClient()
        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        self.dynamic_client = client.DynamicClient(self.api_client)
        
        # Crossplane API groups
        self.crossplane_groups = {
            'platform.example.com': 'v1alpha1',
            'apiextensions.crossplane.io': 'v1',
            'pkg.crossplane.io': 'v1'
        }
        
        logger.info("Crossplane orchestrator initialized")
    
    def create_network(self, request: ResourceRequest) -> ResourceStatus:
        """Create network resource using Crossplane"""
        try:
            # Create Network claim
            network_claim = {
                "apiVersion": "platform.example.com/v1alpha1",
                "kind": "Network",
                "metadata": {
                    "name": request.name,
                    "namespace": request.config.get('namespace', 'default'),
                    "labels": {
                        "app.kubernetes.io/managed-by": "crossplane-orchestrator",
                        "app.kubernetes.io/provider": request.provider.value
                    }
                },
                "spec": {
                    "provider": request.provider.value,
                    "region": request.region,
                    "cidrBlock": request.config.get('cidrBlock', '10.0.0.0/16'),
                    "subnetCount": request.config.get('subnetCount', 3),
                    "enableDnsHostnames": request.config.get('enableDnsHostnames', True),
                    "enableDnsSupport": request.config.get('enableDnsSupport', True),
                    "tags": request.tags or {}
                },
                "compositionSelector": {
                    "matchLabels": {
                        "provider": request.provider.value
                    }
                }
            }
            
            # Apply the claim
            result = self.custom_api.create_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=request.config.get('namespace', 'default'),
                plural="networks",
                body=network_claim
            )
            
            logger.info(f"Created network {request.name} on {request.provider.value}")
            
            return ResourceStatus(
                name=request.name,
                resource_type=ResourceType.NETWORK,
                provider=request.provider,
                status="created",
                message=f"Network {request.name} provisioned via Crossplane",
                metadata=result,
                timestamp=datetime.utcnow()
            )
            
        except ApiException as e:
            logger.error(f"Failed to create network {request.name}: {e}")
            return ResourceStatus(
                name=request.name,
                resource_type=ResourceType.NETWORK,
                provider=request.provider,
                status="error",
                message=str(e),
                metadata={"error": e.body},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Unexpected error creating network {request.name}: {e}")
            return ResourceStatus(
                name=request.name,
                resource_type=ResourceType.NETWORK,
                provider=request.provider,
                status="error",
                message=str(e),
                metadata={},
                timestamp=datetime.utcnow()
            )
    
    def create_compute(self, request: ResourceRequest) -> ResourceStatus:
        """Create compute resource using Crossplane"""
        try:
            compute_claim = {
                "apiVersion": "platform.example.com/v1alpha1",
                "kind": "Compute",
                "metadata": {
                    "name": request.name,
                    "namespace": request.config.get('namespace', 'default'),
                    "labels": {
                        "app.kubernetes.io/managed-by": "crossplane-orchestrator",
                        "app.kubernetes.io/provider": request.provider.value
                    }
                },
                "spec": {
                    "provider": request.provider.value,
                    "region": request.region,
                    "instanceType": request.config.get('instanceType', 't3.medium'),
                    "imageId": request.config.get('imageId'),
                    "keyName": request.config.get('keyName'),
                    "minCount": request.config.get('minCount', 1),
                    "maxCount": request.config.get('maxCount', 1),
                    "monitoring": request.config.get('monitoring', True),
                    "tags": request.tags or {}
                },
                "compositionSelector": {
                    "matchLabels": {
                        "provider": request.provider.value
                    }
                }
            }
            
            result = self.custom_api.create_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=request.config.get('namespace', 'default'),
                plural="computes",
                body=compute_claim
            )
            
            logger.info(f"Created compute {request.name} on {request.provider.value}")
            
            return ResourceStatus(
                name=request.name,
                resource_type=ResourceType.COMPUTE,
                provider=request.provider,
                status="created",
                message=f"Compute {request.name} provisioned via Crossplane",
                metadata=result,
                timestamp=datetime.utcnow()
            )
            
        except ApiException as e:
            logger.error(f"Failed to create compute {request.name}: {e}")
            return ResourceStatus(
                name=request.name,
                resource_type=ResourceType.COMPUTE,
                provider=request.provider,
                status="error",
                message=str(e),
                metadata={"error": e.body},
                timestamp=datetime.utcnow()
            )
    
    def create_storage(self, request: ResourceRequest) -> ResourceStatus:
        """Create storage resource using Crossplane"""
        try:
            storage_claim = {
                "apiVersion": "platform.example.com/v1alpha1",
                "kind": "Storage",
                "metadata": {
                    "name": request.name,
                    "namespace": request.config.get('namespace', 'default'),
                    "labels": {
                        "app.kubernetes.io/managed-by": "crossplane-orchestrator",
                        "app.kubernetes.io/provider": request.provider.value
                    }
                },
                "spec": {
                    "provider": request.provider.value,
                    "region": request.region,
                    "bucketName": request.config.get('bucketName', request.name),
                    "storageClass": request.config.get('storageClass', 'standard'),
                    "versioning": request.config.get('versioning', False),
                    "encryption": request.config.get('encryption', True),
                    "accessControl": request.config.get('accessControl', 'private'),
                    "tags": request.tags or {}
                },
                "compositionSelector": {
                    "matchLabels": {
                        "provider": request.provider.value
                    }
                }
            }
            
            result = self.custom_api.create_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=request.config.get('namespace', 'default'),
                plural="storages",
                body=storage_claim
            )
            
            logger.info(f"Created storage {request.name} on {request.provider.value}")
            
            return ResourceStatus(
                name=request.name,
                resource_type=ResourceType.STORAGE,
                provider=request.provider,
                status="created",
                message=f"Storage {request.name} provisioned via Crossplane",
                metadata=result,
                timestamp=datetime.utcnow()
            )
            
        except ApiException as e:
            logger.error(f"Failed to create storage {request.name}: {e}")
            return ResourceStatus(
                name=request.name,
                resource_type=ResourceType.STORAGE,
                provider=request.provider,
                status="error",
                message=str(e),
                metadata={"error": e.body},
                timestamp=datetime.utcnow()
            )
    
    def get_resource_status(self, resource_name: str, resource_type: ResourceType, 
                          namespace: str = "default") -> Optional[ResourceStatus]:
        """Get status of a Crossplane resource"""
        try:
            plural_map = {
                ResourceType.NETWORK: "networks",
                ResourceType.COMPUTE: "computes",
                ResourceType.STORAGE: "storages"
            }
            
            plural = plural_map.get(resource_type)
            if not plural:
                return None
            
            result = self.custom_api.get_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=namespace,
                plural=plural,
                name=resource_name
            )
            
            # Extract provider from labels
            provider = CloudProvider.AWS  # default
            labels = result.get('metadata', {}).get('labels', {})
            if 'app.kubernetes.io/provider' in labels:
                provider = CloudProvider(labels['app.kubernetes.io/provider'])
            
            # Determine status from conditions
            status = "unknown"
            message = "Resource found"
            conditions = result.get('status', {}).get('conditions', [])
            for condition in conditions:
                if condition.get('type') == 'Ready':
                    status = 'ready' if condition.get('status') == 'True' else 'not_ready'
                    message = condition.get('message', message)
                    break
            
            return ResourceStatus(
                name=resource_name,
                resource_type=resource_type,
                provider=provider,
                status=status,
                message=message,
                metadata=result,
                timestamp=datetime.utcnow()
            )
            
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"Failed to get status for {resource_name}: {e}")
            return None
    
    def delete_resource(self, resource_name: str, resource_type: ResourceType,
                     namespace: str = "default") -> bool:
        """Delete a Crossplane resource"""
        try:
            plural_map = {
                ResourceType.NETWORK: "networks",
                ResourceType.COMPUTE: "computes",
                ResourceType.STORAGE: "storages"
            }
            
            plural = plural_map.get(resource_type)
            if not plural:
                return False
            
            self.custom_api.delete_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=namespace,
                plural=plural,
                name=resource_name
            )
            
            logger.info(f"Deleted {resource_type.value} {resource_name}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to delete {resource_name}: {e}")
            return False
    
    def list_resources(self, resource_type: ResourceType, 
                    namespace: str = "default") -> List[ResourceStatus]:
        """List all resources of a specific type"""
        try:
            plural_map = {
                ResourceType.NETWORK: "networks",
                ResourceType.COMPUTE: "computes",
                ResourceType.STORAGE: "storages"
            }
            
            plural = plural_map.get(resource_type)
            if not plural:
                return []
            
            result = self.custom_api.list_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=namespace,
                plural=plural
            )
            
            resources = []
            for item in result.get('items', []):
                # Extract provider from labels
                provider = CloudProvider.AWS  # default
                labels = item.get('metadata', {}).get('labels', {})
                if 'app.kubernetes.io/provider' in labels:
                    provider = CloudProvider(labels['app.kubernetes.io/provider'])
                
                # Determine status
                status = "unknown"
                conditions = item.get('status', {}).get('conditions', [])
                for condition in conditions:
                    if condition.get('type') == 'Ready':
                        status = 'ready' if condition.get('status') == 'True' else 'not_ready'
                        break
                
                resources.append(ResourceStatus(
                    name=item['metadata']['name'],
                    resource_type=resource_type,
                    provider=provider,
                    status=status,
                    message="Resource listed",
                    metadata=item,
                    timestamp=datetime.utcnow()
                ))
            
            return resources
            
        except ApiException as e:
            logger.error(f"Failed to list {resource_type.value} resources: {e}")
            return []
    
    def get_crossplane_providers(self) -> Dict[str, Any]:
        """Get status of Crossplane providers"""
        try:
            result = self.custom_api.list_cluster_custom_object(
                group="pkg.crossplane.io",
                version="v1",
                plural="providers"
            )
            
            providers = {}
            for provider in result.get('items', []):
                name = provider['metadata']['name']
                providers[name] = {
                    'installed': provider.get('spec', {}).get('package', ''),
                    'healthy': provider.get('status', {}).get('healthy', False),
                    'package': provider.get('spec', {}).get('package', '')
                }
            
            return providers
            
        except ApiException as e:
            logger.error(f"Failed to get Crossplane providers: {e}")
            return {}
    
    def validate_crossplane_setup(self) -> Dict[str, Any]:
        """Validate Crossplane installation and configuration"""
        validation = {
            'crossplane_installed': False,
            'providers_installed': [],
            'xrds_available': [],
            'compositions_available': [],
            'errors': []
        }
        
        try:
            # Check if Crossplane is installed
            result = self.custom_api.list_cluster_custom_object(
                group="apiextensions.crossplane.io",
                version="v1",
                plural="compositeresourcedefinitions"
            )
            
            if result.get('items'):
                validation['crossplane_installed'] = True
                
                # List available XRDs
                for xrd in result.get('items', []):
                    validation['xrds_available'].append(xrd['metadata']['name'])
            
            # Check providers
            providers = self.get_crossplane_providers()
            validation['providers_installed'] = list(providers.keys())
            
            # Check compositions
            try:
                compositions = self.custom_api.list_cluster_custom_object(
                    group="apiextensions.crossplane.io",
                    version="v1",
                    plural="compositions"
                )
                
                for comp in compositions.get('items', []):
                    validation['compositions_available'].append(comp['metadata']['name'])
                    
            except ApiException as e:
                validation['errors'].append(f"Failed to list compositions: {e}")
            
        except ApiException as e:
            validation['errors'].append(f"Crossplane not accessible: {e}")
        
        return validation

# Backwards compatibility adapter
class TerraformCompatibilityAdapter:
    """Adapter to maintain compatibility with existing Terraform-based interfaces"""
    
    def __init__(self):
        self.orchestrator = CrossplaneOrchestrator()
    
    def apply_terraform_config(self, terraform_config: Dict[str, Any]) -> List[ResourceStatus]:
        """Convert Terraform config to Crossplane resources"""
        results = []
        
        # Convert Terraform resources to Crossplane claims
        for resource_name, resource_config in terraform_config.get('resource', {}).items():
            resource_type, resource_id = resource_name.split('.')
            
            # Map Terraform resource types to Crossplane
            if resource_type == 'aws_vpc':
                request = ResourceRequest(
                    name=resource_id,
                    resource_type=ResourceType.NETWORK,
                    provider=CloudProvider.AWS,
                    region=resource_config.get('region', 'us-west-2'),
                    config=resource_config,
                    tags=resource_config.get('tags', {})
                )
                results.append(self.orchestrator.create_network(request))
            
            elif resource_type == 'aws_instance':
                request = ResourceRequest(
                    name=resource_id,
                    resource_type=ResourceType.COMPUTE,
                    provider=CloudProvider.AWS,
                    region=resource_config.get('region', 'us-west-2'),
                    config=resource_config,
                    tags=resource_config.get('tags', {})
                )
                results.append(self.orchestrator.create_compute(request))
            
            elif resource_type == 'aws_s3_bucket':
                request = ResourceRequest(
                    name=resource_id,
                    resource_type=ResourceType.STORAGE,
                    provider=CloudProvider.AWS,
                    region=resource_config.get('region', 'us-west-2'),
                    config=resource_config,
                    tags=resource_config.get('tags', {})
                )
                results.append(self.orchestrator.create_storage(request))
        
        return results

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Crossplane Multi-Cloud Orchestrator")
    parser.add_argument("--action", choices=["create", "list", "status", "delete", "validate"], 
                       default="validate", help="Action to perform")
    parser.add_argument("--type", choices=["network", "compute", "storage"], 
                       help="Resource type")
    parser.add_argument("--name", help="Resource name")
    parser.add_argument("--provider", choices=["aws", "azure", "gcp"], 
                       default="aws", help="Cloud provider")
    parser.add_argument("--region", default="us-west-2", help="Cloud region")
    parser.add_argument("--config", help="JSON configuration")
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    orchestrator = CrossplaneOrchestrator()
    
    if args.action == "validate":
        validation = orchestrator.validate_crossplane_setup()
        print(json.dumps(validation, indent=2))
    
    elif args.action == "create" and args.type and args.name:
        resource_type = ResourceType(args.type)
        provider = CloudProvider(args.provider)
        
        config = {}
        if args.config:
            config = json.loads(args.config)
        
        request = ResourceRequest(
            name=args.name,
            resource_type=resource_type,
            provider=provider,
            region=args.region,
            config=config,
            namespace=args.namespace
        )
        
        if resource_type == ResourceType.NETWORK:
            result = orchestrator.create_network(request)
        elif resource_type == ResourceType.COMPUTE:
            result = orchestrator.create_compute(request)
        elif resource_type == ResourceType.STORAGE:
            result = orchestrator.create_storage(request)
        
        print(json.dumps({
            'name': result.name,
            'status': result.status,
            'message': result.message,
            'timestamp': result.timestamp.isoformat()
        }, indent=2))
    
    elif args.action == "list" and args.type:
        resource_type = ResourceType(args.type)
        resources = orchestrator.list_resources(resource_type, args.namespace)
        
        output = []
        for resource in resources:
            output.append({
                'name': resource.name,
                'provider': resource.provider.value,
                'status': resource.status,
                'message': resource.message,
                'timestamp': resource.timestamp.isoformat()
            })
        
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
