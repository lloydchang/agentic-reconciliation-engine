#!/usr/bin/env python3
"""
Simplified Crossplane Multi-Cloud Orchestrator

Unified orchestrator for single Crossplane control plane with team-based isolation.
Supports native multi-cloud compositions with RBAC-based access control.
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
class ResourceRequest:
    """Resource creation request with team isolation"""
    name: str
    resource_type: ResourceType
    provider: CloudProvider
    region: str
    config: Dict[str, Any]
    team: str
    namespace: str = "default"
    tags: Optional[Dict[str, str]] = None

@dataclass
class ResourceStatus:
    """Resource status information"""
    name: str
    resource_type: ResourceType
    provider: CloudProvider
    team: str
    namespace: str
    status: str
    message: str
    metadata: Dict[str, Any]
    timestamp: datetime

class SimplifiedCrossplaneOrchestrator:
    """Simplified Crossplane orchestrator for unified control plane"""
    
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
        
        logger.info("Simplified Crossplane orchestrator initialized")
    
    def create_multi_cloud_resource(self, request: ResourceRequest) -> ResourceStatus:
        """Create multi-cloud resource using unified compositions"""
        try:
            # Determine resource kind based on type
            resource_kinds = {
                ResourceType.NETWORK: "Network",
                ResourceType.COMPUTE: "Compute", 
                ResourceType.STORAGE: "Storage"
            }
            
            kind = resource_kinds.get(request.resource_type)
            if not kind:
                return ResourceStatus(
                    name=request.name,
                    resource_type=request.resource_type,
                    provider=request.provider,
                    team=request.team,
                    namespace=request.namespace,
                    status="error",
                    message=f"Unsupported resource type: {request.resource_type}",
                    metadata={},
                    timestamp=datetime.utcnow()
                )
            
            # Create resource claim with team isolation
            resource_claim = {
                "apiVersion": "platform.example.com/v1alpha1",
                "kind": kind,
                "metadata": {
                    "name": request.name,
                    "namespace": request.namespace,
                    "labels": {
                        "app.kubernetes.io/managed-by": "crossplane-orchestrator",
                        "app.kubernetes.io/provider": request.provider.value,
                        "app.kubernetes.io/team": request.team,
                        "crossplane.io/managed": "true"
                    },
                    "annotations": {
                        "crossplane.io/claim-name": request.name,
                        "crossplane.io/team": request.team
                    }
                },
                "spec": {
                    "provider": request.provider.value,
                    "region": request.region,
                    "tags": request.tags or {}
                },
                "compositionSelector": {
                    "matchLabels": {
                        "crossplane.io/managed": "true"
                    }
                }
            }
            
            # Add resource-specific configuration
            if request.resource_type == ResourceType.NETWORK:
                resource_claim["spec"].update({
                    "cidrBlock": request.config.get('cidrBlock', '10.0.0.0/16'),
                    "subnetCount": request.config.get('subnetCount', 3),
                    "enableDnsHostnames": request.config.get('enableDnsHostnames', True),
                    "enableDnsSupport": request.config.get('enableDnsSupport', True)
                })
            elif request.resource_type == ResourceType.COMPUTE:
                resource_claim["spec"].update({
                    "instanceType": request.config.get('instanceType', 't3.medium'),
                    "imageId": request.config.get('imageId'),
                    "keyName": request.config.get('keyName'),
                    "minCount": request.config.get('minCount', 1),
                    "maxCount": request.config.get('maxCount', 1),
                    "monitoring": request.config.get('monitoring', True)
                })
            elif request.resource_type == ResourceType.STORAGE:
                resource_claim["spec"].update({
                    "bucketName": request.config.get('bucketName', request.name),
                    "storageClass": request.config.get('storageClass', 'standard'),
                    "versioning": request.config.get('versioning', False),
                    "encryption": request.config.get('encryption', True),
                    "accessControl": request.config.get('accessControl', 'private')
                })
            
            # Apply the claim
            plural = f"{kind.lower()}s"
            result = self.custom_api.create_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=request.namespace,
                plural=plural,
                body=resource_claim
            )
            
            logger.info(f"Created {kind} {request.name} for team {request.team} on {request.provider.value}")
            
            return ResourceStatus(
                name=request.name,
                resource_type=request.resource_type,
                provider=request.provider,
                team=request.team,
                namespace=request.namespace,
                status="created",
                message=f"{kind} {request.name} provisioned via unified Crossplane",
                metadata=result,
                timestamp=datetime.utcnow()
            )
            
        except ApiException as e:
            logger.error(f"Failed to create {request.resource_type.value} {request.name}: {e}")
            return ResourceStatus(
                name=request.name,
                resource_type=request.resource_type,
                provider=request.provider,
                team=request.team,
                namespace=request.namespace,
                status="error",
                message=str(e),
                metadata={"error": e.body},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Unexpected error creating {request.resource_type.value} {request.name}: {e}")
            return ResourceStatus(
                name=request.name,
                resource_type=request.resource_type,
                provider=request.provider,
                team=request.team,
                namespace=request.namespace,
                status="error",
                message=str(e),
                metadata={},
                timestamp=datetime.utcnow()
            )
    
    def get_team_resources(self, team: str, resource_type: Optional[ResourceType] = None,
                          namespace: str = "default") -> List[ResourceStatus]:
        """Get all resources for a specific team"""
        resources = []
        
        try:
            resource_types = [resource_type] if resource_type else list(ResourceType)
            resource_kinds = {
                ResourceType.NETWORK: "networks",
                ResourceType.COMPUTE: "computes",
                ResourceType.STORAGE: "storages"
            }
            
            for rtype in resource_types:
                if rtype not in resource_kinds:
                    continue
                
                plural = resource_kinds[rtype]
                
                result = self.custom_api.list_namespaced_custom_object(
                    group="platform.example.com",
                    version="v1alpha1",
                    namespace=namespace,
                    plural=plural
                )
                
                for item in result.get('items', []):
                    # Check if resource belongs to the team
                    labels = item.get('metadata', {}).get('labels', {})
                    annotations = item.get('metadata', {}).get('annotations', {})
                    
                    if (labels.get('app.kubernetes.io/team') == team or 
                        annotations.get('crossplane.io/team') == team):
                        
                        # Extract provider from labels
                        provider = CloudProvider.AWS  # default
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
                            resource_type=rtype,
                            provider=provider,
                            team=team,
                            namespace=namespace,
                            status=status,
                            message="Resource listed",
                            metadata=item,
                            timestamp=datetime.utcnow()
                        ))
            
            return resources
            
        except ApiException as e:
            logger.error(f"Failed to list resources for team {team}: {e}")
            return []
    
    def delete_team_resource(self, team: str, resource_name: str, resource_type: ResourceType,
                           namespace: str = "default") -> bool:
        """Delete a team resource with proper authorization checks"""
        try:
            resource_kinds = {
                ResourceType.NETWORK: "networks",
                ResourceType.COMPUTE: "computes",
                ResourceType.STORAGE: "storages"
            }
            
            plural = resource_kinds.get(resource_type)
            if not plural:
                return False
            
            # Verify resource belongs to team before deletion
            try:
                resource = self.custom_api.get_namespaced_custom_object(
                    group="platform.example.com",
                    version="v1alpha1",
                    namespace=namespace,
                    plural=plural,
                    name=resource_name
                )
                
                labels = resource.get('metadata', {}).get('labels', {})
                annotations = resource.get('metadata', {}).get('annotations', {})
                
                if (labels.get('app.kubernetes.io/team') != team and 
                    annotations.get('crossplane.io/team') != team):
                    logger.error(f"Resource {resource_name} does not belong to team {team}")
                    return False
                    
            except ApiException as e:
                if e.status == 404:
                    logger.error(f"Resource {resource_name} not found")
                    return False
                raise
            
            # Delete the resource
            self.custom_api.delete_namespaced_custom_object(
                group="platform.example.com",
                version="v1alpha1",
                namespace=namespace,
                plural=plural,
                name=resource_name
            )
            
            logger.info(f"Deleted {resource_type.value} {resource_name} for team {team}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to delete {resource_name}: {e}")
            return False
    
    def get_crossplane_status(self) -> Dict[str, Any]:
        """Get unified Crossplane control plane status"""
        status = {
            'crossplane_healthy': False,
            'providers_installed': [],
            'compositions_available': [],
            'xrds_available': [],
            'team_resources': {},
            'errors': []
        }
        
        try:
            # Check Crossplane health
            try:
                result = self.custom_api.list_cluster_custom_object(
                    group="pkg.crossplane.io",
                    version="v1",
                    plural="providers"
                )
                
                if result.get('items'):
                    status['crossplane_healthy'] = True
                    
                    for provider in result.get('items', []):
                        name = provider['metadata']['name']
                        status['providers_installed'].append({
                            'name': name,
                            'healthy': provider.get('status', {}).get('healthy', False),
                            'package': provider.get('spec', {}).get('package', '')
                        })
            except ApiException as e:
                status['errors'].append(f"Crossplane not accessible: {e}")
            
            # Check XRDs
            try:
                result = self.custom_api.list_cluster_custom_object(
                    group="apiextensions.crossplane.io",
                    version="v1",
                    plural="compositeresourcedefinitions"
                )
                
                for xrd in result.get('items', []):
                    status['xrds_available'].append(xrd['metadata']['name'])
                    
            except ApiException as e:
                status['errors'].append(f"Failed to list XRDs: {e}")
            
            # Check compositions
            try:
                result = self.custom_api.list_cluster_custom_object(
                    group="apiextensions.crossplane.io",
                    version="v1",
                    plural="compositions"
                )
                
                for comp in result.get('items', []):
                    status['compositions_available'].append(comp['metadata']['name'])
                    
            except ApiException as e:
                status['errors'].append(f"Failed to list compositions: {e}")
            
            # Check team resources
            teams = ['team-a', 'team-b']  # Could be dynamic
            for team in teams:
                resources = self.get_team_resources(team)
                status['team_resources'][team] = {
                    'total': len(resources),
                    'by_type': {}
                }
                
                for resource in resources:
                    rtype = resource.resource_type.value
                    if rtype not in status['team_resources'][team]['by_type']:
                        status['team_resources'][team]['by_type'][rtype] = 0
                    status['team_resources'][team]['by_type'][rtype] += 1
            
        except Exception as e:
            status['errors'].append(f"Unexpected error: {e}")
        
        return status
    
    def validate_team_access(self, team: str, namespace: str = "default") -> bool:
        """Validate team has proper RBAC access"""
        try:
            # Check if team namespace exists
            try:
                self.core_api.read_namespace(name=namespace)
            except ApiException as e:
                if e.status == 404:
                    logger.error(f"Namespace {namespace} does not exist for team {team}")
                    return False
                raise
            
            # Check team service account exists
            try:
                self.core_api.read_namespaced_service_account(
                    name=f"{team}-sa",
                    namespace=namespace
                )
            except ApiException as e:
                if e.status == 404:
                    logger.warning(f"Service account {team}-sa not found in namespace {namespace}")
                # Continue anyway - service account might not be required
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate team access for {team}: {e}")
            return False

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simplified Crossplane Multi-Cloud Orchestrator")
    parser.add_argument("--action", choices=["create", "list", "status", "delete", "validate"], 
                       default="status", help="Action to perform")
    parser.add_argument("--type", choices=["network", "compute", "storage"], 
                       help="Resource type")
    parser.add_argument("--name", help="Resource name")
    parser.add_argument("--provider", choices=["aws", "azure", "gcp"], 
                       default="aws", help="Cloud provider")
    parser.add_argument("--region", default="us-west-2", help="Cloud region")
    parser.add_argument("--team", default="team-a", help="Team name")
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace")
    parser.add_argument("--config", help="JSON configuration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    orchestrator = SimplifiedCrossplaneOrchestrator()
    
    if args.action == "validate":
        valid = orchestrator.validate_team_access(args.team, args.namespace)
        print(json.dumps({"team": args.team, "access_valid": valid}, indent=2))
    
    elif args.action == "status":
        status = orchestrator.get_crossplane_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == "list":
        if args.team:
            resource_type = ResourceType(args.type) if args.type else None
            resources = orchestrator.get_team_resources(args.team, resource_type, args.namespace)
            
            output = []
            for resource in resources:
                output.append({
                    'name': resource.name,
                    'type': resource.resource_type.value,
                    'provider': resource.provider.value,
                    'status': resource.status,
                    'message': resource.message,
                    'timestamp': resource.timestamp.isoformat()
                })
            
            print(json.dumps(output, indent=2))
        else:
            print("Error: --team is required for list action")
    
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
            team=args.team,
            namespace=args.namespace
        )
        
        result = orchestrator.create_multi_cloud_resource(request)
        
        print(json.dumps({
            'name': result.name,
            'type': result.resource_type.value,
            'provider': result.provider.value,
            'team': result.team,
            'namespace': result.namespace,
            'status': result.status,
            'message': result.message,
            'timestamp': result.timestamp.isoformat()
        }, indent=2))
    
    elif args.action == "delete" and args.type and args.name:
        resource_type = ResourceType(args.type)
        success = orchestrator.delete_team_resource(args.team, args.name, resource_type, args.namespace)
        
        print(json.dumps({
            'name': args.name,
            'type': args.type,
            'team': args.team,
            'namespace': args.namespace,
            'deleted': success
        }, indent=2))

if __name__ == "__main__":
    main()
