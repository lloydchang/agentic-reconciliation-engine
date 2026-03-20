#!/usr/bin/env python3
"""
Crossplane Orchestrator for Multi-Cloud Operations

Orchestrates Crossplane XRDs and Compositions for multi-cloud infrastructure management.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    NETWORK = "network"
    VM = "vm"
    STORAGE = "storage"
    DATABASE = "database"

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    AUTO = "auto"

@dataclass
class ResourceRequest:
    name: str
    resource_type: ResourceType
    provider: CloudProvider
    region: str
    spec: Dict[str, Any]
    namespace: str = "default"

@dataclass
class ResourceStatus:
    name: str
    resource_type: str
    provider: str
    status: str
    resource_id: str
    metadata: Dict[str, Any]
    timestamp: datetime

class CrossplaneOrchestrator:
    """Crossplane-based multi-cloud orchestrator"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        """Initialize Kubernetes client for Crossplane operations"""
        try:
            config.load_kube_config(config_file=kubeconfig_path)
            self.api_client = client.ApiClient()
            self.custom_api = client.CustomObjectsApi()
            self.core_api = client.CoreV1Api()
            logger.info("Successfully initialized Kubernetes client for Crossplane")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise
    
    def create_resource(self, request: ResourceRequest) -> ResourceStatus:
        """Create a Crossplane resource using XRDs"""
        try:
            # Determine the XRD based on resource type
            if request.resource_type == ResourceType.NETWORK:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xnetworks"
            elif request.resource_type == ResourceType.VM:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xvms"
            else:
                raise ValueError(f"Unsupported resource type: {request.resource_type}")
            
            # Create the composite resource
            resource = {
                "apiVersion": f"{group}/{version}",
                "kind": f"X{request.resource_type.value.title()}",
                "metadata": {
                    "name": request.name,
                    "namespace": request.namespace,
                    "labels": {
                        "managed-by": "crossplane-orchestrator",
                        "provider": request.provider.value
                    }
                },
                "spec": {
                    "provider": request.provider.value,
                    "region": request.region,
                    **request.spec
                }
            }
            
            logger.info(f"Creating {request.resource_type.value} {request.name} on {request.provider.value}")
            
            result = self.custom_api.create_namespaced_custom_object(
                namespace=request.namespace,
                group=group,
                version=version,
                plural=plural,
                body=resource
            )
            
            logger.info(f"Successfully created {request.resource_type.value} {request.name}")
            
            return ResourceStatus(
                name=request.name,
                resource_type=request.resource_type.value,
                provider=request.provider.value,
                status="created",
                resource_id=result.get("metadata", {}).get("uid", ""),
                metadata=result.get("metadata", {}),
                timestamp=datetime.utcnow()
            )
            
        except ApiException as e:
            logger.error(f"Failed to create resource {request.name}: {e}")
            return ResourceStatus(
                name=request.name,
                resource_type=request.resource_type.value,
                provider=request.provider.value,
                status="failed",
                resource_id="",
                metadata={"error": str(e)},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Unexpected error creating resource {request.name}: {e}")
            raise
    
    def get_resource_status(self, name: str, resource_type: ResourceType, namespace: str = "default") -> Optional[ResourceStatus]:
        """Get status of a Crossplane resource"""
        try:
            if resource_type == ResourceType.NETWORK:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xnetworks"
            elif resource_type == ResourceType.VM:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xvms"
            else:
                return None
            
            result = self.custom_api.get_namespaced_custom_object(
                name=name,
                namespace=namespace,
                group=group,
                version=version,
                plural=plural
            )
            
            metadata = result.get("metadata", {})
            status = result.get("status", {})
            
            return ResourceStatus(
                name=name,
                resource_type=resource_type.value,
                provider=status.get("provider", "unknown"),
                status=status.get("status", "unknown"),
                resource_id=metadata.get("uid", ""),
                metadata=result,
                timestamp=datetime.utcnow()
            )
            
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"Failed to get resource status for {name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting resource status for {name}: {e}")
            return None
    
    def delete_resource(self, name: str, resource_type: ResourceType, namespace: str = "default") -> bool:
        """Delete a Crossplane resource"""
        try:
            if resource_type == ResourceType.NETWORK:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xnetworks"
            elif resource_type == ResourceType.VM:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xvms"
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
            
            logger.info(f"Deleting {resource_type.value} {name}")
            
            self.custom_api.delete_namespaced_custom_object(
                name=name,
                namespace=namespace,
                group=group,
                version=version,
                plural=plural
            )
            
            logger.info(f"Successfully deleted {resource_type.value} {name}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to delete resource {name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting resource {name}: {e}")
            raise
    
    def list_resources(self, resource_type: ResourceType, namespace: str = "default", provider: Optional[CloudProvider] = None) -> List[ResourceStatus]:
        """List Crossplane resources with optional provider filter"""
        try:
            if resource_type == ResourceType.NETWORK:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xnetworks"
            elif resource_type == ResourceType.VM:
                group = "platform.example.com"
                version = "v1alpha1"
                plural = "xvms"
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
            
            result = self.custom_api.list_namespaced_custom_object(
                namespace=namespace,
                group=group,
                version=version,
                plural=plural
            )
            
            resources = []
            for item in result.get("items", []):
                metadata = item.get("metadata", {})
                status = item.get("status", {})
                spec = item.get("spec", {})
                
                # Filter by provider if specified
                if provider and spec.get("provider") != provider.value:
                    continue
                
                resources.append(ResourceStatus(
                    name=metadata.get("name", ""),
                    resource_type=resource_type.value,
                    provider=spec.get("provider", "unknown"),
                    status=status.get("status", "unknown"),
                    resource_id=metadata.get("uid", ""),
                    metadata=item,
                    timestamp=datetime.utcnow()
                ))
            
            return resources
            
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            return []
    
    def create_multi_cloud_network(self, name: str, regions: Dict[str, str]) -> ResourceStatus:
        """Create a multi-cloud network across different providers"""
        try:
            # Create cross-cloud failover composition
            resource = {
                "apiVersion": "platform.example.com/v1alpha1",
                "kind": "XNetwork",
                "metadata": {
                    "name": f"{name}-multi-cloud",
                    "namespace": "default",
                    "labels": {
                        "managed-by": "crossplane-orchestrator",
                        "type": "multi-cloud-failover"
                    }
                },
                "spec": {
                    "provider": "auto",
                    "region": "multi-cloud",
                    "cidrBlock": "10.0.0.0/8",
                    "subnetCount": 6
                }
            }
            
            logger.info(f"Creating multi-cloud network {name}")
            
            result = self.custom_api.create_namespaced_custom_object(
                namespace="default",
                group="platform.example.com",
                version="v1alpha1",
                plural="xnetworks",
                body=resource
            )
            
            logger.info(f"Successfully created multi-cloud network {name}")
            
            return ResourceStatus(
                name=f"{name}-multi-cloud",
                resource_type="network",
                provider="multi-cloud",
                status="created",
                resource_id=result.get("metadata", {}).get("uid", ""),
                metadata=result.get("metadata", {}),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to create multi-cloud network {name}: {e}")
            raise
    
    def wait_for_resource_ready(self, name: str, resource_type: ResourceType, namespace: str = "default", timeout: int = 300) -> bool:
        """Wait for a Crossplane resource to become ready"""
        import time
        
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            status = self.get_resource_status(name, resource_type, namespace)
            if status and status.status in ["healthy", "ready", "available"]:
                logger.info(f"Resource {name} is ready")
                return True
            elif status and status.status in ["failed", "error"]:
                logger.error(f"Resource {name} failed to become ready")
                return False
            
            time.sleep(10)
        
        logger.warning(f"Timeout waiting for resource {name} to become ready")
        return False

def main():
    """Example usage"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        orchestrator = CrossplaneOrchestrator()
        
        # Create AWS VM
        vm_request = ResourceRequest(
            name="test-vm-aws",
            resource_type=ResourceType.VM,
            provider=CloudProvider.AWS,
            region="us-west-2",
            spec={
                "instanceType": "t3.medium",
                "image": "ubuntu-latest"
            }
        )
        
        result = orchestrator.create_resource(vm_request)
        print(f"VM creation result: {result}")
        
        # Create multi-cloud network
        network_result = orchestrator.create_multi_cloud_network("test-network", {
            "aws": "us-west-2",
            "azure": "eastus",
            "gcp": "us-central1"
        })
        print(f"Multi-cloud network result: {network_result}")
        
        # List all VMs
        vms = orchestrator.list_resources(ResourceType.VM)
        print(f"VMs: {len(vms)} found")
        for vm in vms:
            print(f"  - {vm.name} ({vm.provider}): {vm.status}")
            
    except Exception as e:
        logger.error(f"Failed to run example: {e}")

if __name__ == "__main__":
    main()
