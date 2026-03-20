#!/usr/bin/env python3
"""
Crossplane Migration Utilities

Utilities for migrating from Terraform to Crossplane with backwards compatibility.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class CrossplaneMigrationUtils:
    """Utilities for Crossplane migration"""
    
    def __init__(self, terraform_dir: str = "core/infrastructure/terraform"):
        self.terraform_dir = Path(terraform_dir)
        self.backup_dir = Path("core/infrastructure/terraform-backup")
        
    def backup_terraform_configurations(self) -> bool:
        """Backup existing Terraform configurations"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            shutil.copytree(self.terraform_dir, self.backup_dir)
            logger.info(f"Backed up Terraform configurations to {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup Terraform configurations: {e}")
            return False
    
    def parse_terraform_state(self, state_file: str) -> Dict[str, Any]:
        """Parse Terraform state file"""
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            resources = {}
            for resource in state.get("resources", []):
                resource_type = resource.get("type", "")
                resource_name = resource.get("name", "")
                
                if resource_type and resource_name:
                    key = f"{resource_type}.{resource_name}"
                    resources[key] = resource
            
            return resources
            
        except Exception as e:
            logger.error(f"Failed to parse Terraform state: {e}")
            return {}
    
    def generate_crossplane_manifests(self, terraform_resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Crossplane manifests from Terraform resources"""
        manifests = []
        
        for resource_key, resource_data in terraform_resources.items():
            resource_type = resource_data.get("type", "")
            
            if resource_type.startswith("aws_"):
                manifest = self._generate_aws_manifest(resource_data)
            elif resource_type.startswith("azurerm_"):
                manifest = self._generate_azure_manifest(resource_data)
            elif resource_type.startswith("google_"):
                manifest = self._generate_gcp_manifest(resource_data)
            else:
                continue
            
            if manifest:
                manifests.append(manifest)
        
        return manifests
    
    def _generate_aws_manifest(self, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AWS Crossplane manifest"""
        resource_type = resource_data.get("type", "")
        instances = resource_data.get("instances", [])
        
        if not instances:
            return None
        
        instance = instances[0]  # Use first instance
        attributes = instance.get("attributes", {})
        
        if resource_type == "aws_instance":
            return {
                "apiVersion": "multicloud.example.com/v1alpha1",
                "kind": "XCompute",
                "metadata": {
                    "name": f"migrated-{attributes.get('tags', {}).get('Name', 'instance')}"
                },
                "spec": {
                    "provider": "aws",
                    "region": attributes.get("region", "us-west-2"),
                    "instanceType": attributes.get("instance_type", "t3.medium"),
                    "image": attributes.get("ami", "ubuntu-20.04"),
                    "subnetId": attributes.get("subnet_id", "")
                }
            }
        
        elif resource_type == "aws_vpc":
            return {
                "apiVersion": "multicloud.example.com/v1alpha1",
                "kind": "XNetwork",
                "metadata": {
                    "name": f"migrated-{attributes.get('tags', {}).get('Name', 'vpc')}"
                },
                "spec": {
                    "provider": "aws",
                    "region": attributes.get("region", "us-west-2"),
                    "cidrBlock": attributes.get("cidr_block", "10.0.0.0/16"),
                    "subnetCount": 3
                }
            }
        
        elif resource_type == "aws_s3_bucket":
            return {
                "apiVersion": "multicloud.example.com/v1alpha1",
                "kind": "XStorage",
                "metadata": {
                    "name": f"migrated-{attributes.get('bucket', 'bucket')}"
                },
                "spec": {
                    "provider": "aws",
                    "region": attributes.get("region", "us-west-2"),
                    "storageClass": "standard",
                    "size": "100Gi",
                    "versioning": attributes.get("versioning", True)
                }
            }
        
        return None
    
    def _generate_azure_manifest(self, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate Azure Crossplane manifest"""
        resource_type = resource_data.get("type", "")
        instances = resource_data.get("instances", [])
        
        if not instances:
            return None
        
        instance = instances[0]
        attributes = instance.get("attributes", {})
        
        if resource_type == "azurerm_linux_virtual_machine":
            return {
                "apiVersion": "multicloud.example.com/v1alpha1",
                "kind": "XCompute",
                "metadata": {
                    "name": f"migrated-{attributes.get('name', 'vm')}"
                },
                "spec": {
                    "provider": "azure",
                    "region": attributes.get("location", "East US"),
                    "instanceType": attributes.get("vm_size", "Standard_B2s"),
                    "image": "ubuntu-20.04"
                }
            }
        
        elif resource_type == "azurerm_virtual_network":
            return {
                "apiVersion": "multicloud.example.com/v1alpha1",
                "kind": "XNetwork",
                "metadata": {
                    "name": f"migrated-{attributes.get('name', 'vnet')}"
                },
                "spec": {
                    "provider": "azure",
                    "region": attributes.get("location", "East US"),
                    "cidrBlock": attributes.get("address_space", ["10.0.0.0/16"])[0],
                    "subnetCount": 3
                }
            }
        
        return None
    
    def _generate_gcp_manifest(self, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate GCP Crossplane manifest"""
        resource_type = resource_data.get("type", "")
        instances = resource_data.get("instances", [])
        
        if not instances:
            return None
        
        instance = instances[0]
        attributes = instance.get("attributes", {})
        
        if resource_type == "google_compute_instance":
            return {
                "apiVersion": "multicloud.example.com/v1alpha1",
                "kind": "XCompute",
                "metadata": {
                    "name": f"migrated-{attributes.get('name', 'instance')}"
                },
                "spec": {
                    "provider": "gcp",
                    "region": attributes.get("zone", "us-central1-a").rsplit('-', 1)[0],
                    "instanceType": attributes.get("machine_type", "e2-medium"),
                    "image": "ubuntu-20.04"
                }
            }
        
        elif resource_type == "google_compute_network":
            return {
                "apiVersion": "multicloud.example.com/v1alpha1",
                "kind": "XNetwork",
                "metadata": {
                    "name": f"migrated-{attributes.get('name', 'network')}"
                },
                "spec": {
                    "provider": "gcp",
                    "region": attributes.get("region", "us-central1"),
                    "cidrBlock": attributes.get("ipv4_range", "10.0.0.0/16"),
                    "subnetCount": 3
                }
            }
        
        return None
    
    def run_terraform_command(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run Terraform command and return result"""
        try:
            work_dir = cwd or str(self.terraform_dir)
            
            result = subprocess.run(
                ["terraform"] + command,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_migration_plan(self, state_file: str) -> Dict[str, Any]:
        """Create migration plan from Terraform state"""
        resources = self.parse_terraform_state(state_file)
        manifests = self.generate_crossplane_manifests(resources)
        
        plan = {
            "timestamp": str(Path(state_file).stat().st_mtime),
            "terraform_resources": len(resources),
            "crossplane_manifests": len(manifests),
            "resources": [],
            "estimated_time": len(manifests) * 5  # 5 minutes per resource
        }
        
        for manifest in manifests:
            resource_type = manifest.get("kind", "")
            resource_name = manifest.get("metadata", {}).get("name", "")
            provider = manifest.get("spec", {}).get("provider", "")
            
            plan["resources"].append({
                "name": resource_name,
                "type": resource_type,
                "provider": provider,
                "status": "pending"
            })
        
        return plan
    
    def execute_migration(self, state_file: str, namespace: str = "default") -> Dict[str, Any]:
        """Execute migration from Terraform to Crossplane"""
        try:
            # Backup Terraform configurations
            if not self.backup_terraform_configurations():
                return {"success": False, "error": "Failed to backup Terraform configurations"}
            
            # Parse Terraform state
            resources = self.parse_terraform_state(state_file)
            if not resources:
                return {"success": False, "error": "No resources found in Terraform state"}
            
            # Generate Crossplane manifests
            manifests = self.generate_crossplane_manifests(resources)
            
            # Apply manifests to Kubernetes
            from crossplane_multi_cloud_orchestrator import CrossplaneMultiCloudOrchestrator
            orchestrator = CrossplaneMultiCloudOrchestrator()
            
            results = []
            for manifest in manifests:
                resource_name = manifest.get("metadata", {}).get("name", "")
                resource_type = manifest.get("kind", "")
                
                # Create resource
                result = orchestrator.create_composite_resource(
                    type(resource_type.replace("X", ""))(  # Convert XCompute -> Compute, etc.
                        api_version=manifest.get("apiVersion"),
                        kind=resource_type,
                        name=resource_name,
                        namespace=namespace,
                        spec=manifest.get("spec", {})
                    )
                )
                
                results.append({
                    "name": resource_name,
                    "type": resource_type,
                    "result": result
                })
            
            return {
                "success": True,
                "migrated": len(results),
                "total": len(manifests),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_migration(self, namespace: str = "default") -> Dict[str, Any]:
        """Validate migration by comparing Terraform and Crossplane resources"""
        try:
            from crossplane_multi_cloud_orchestrator import CrossplaneMultiCloudOrchestrator
            orchestrator = CrossplaneMultiCloudOrchestrator()
            
            # Get Crossplane resources
            crossplane_resources = orchestrator.get_multi_cloud_inventory()
            
            # Get Terraform resources (if state exists)
            terraform_state_file = self.terraform_dir / "terraform.tfstate"
            terraform_resources = {}
            
            if terraform_state_file.exists():
                terraform_resources = self.parse_terraform_state(str(terraform_state_file))
            
            # Compare resources
            validation = {
                "timestamp": str(Path().cwd()),
                "terraform_resources": len(terraform_resources),
                "crossplane_resources": 0,
                "matched_resources": 0,
                "missing_resources": [],
                "extra_resources": []
            }
            
            # Count Crossplane resources
            for resource_type, resources in crossplane_resources.get("resources", {}).items():
                validation["crossplane_resources"] += len(resources)
            
            # Simple validation by count (can be enhanced with detailed comparison)
            validation["matched_resources"] = min(
                validation["terraform_resources"],
                validation["crossplane_resources"]
            )
            
            if validation["crossplane_resources"] < validation["terraform_resources"]:
                validation["missing_resources"] = [f"resource_{i}" for i in range(
                    validation["terraform_resources"] - validation["crossplane_resources"]
                )]
            
            return validation
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"success": False, "error": str(e)}

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Crossplane Migration Utilities")
    parser.add_argument("--action", choices=["backup", "plan", "migrate", "validate"], 
                       default="plan", help="Action to perform")
    parser.add_argument("--state-file", help="Terraform state file path")
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace")
    
    args = parser.parse_args()
    
    migration_utils = CrossplaneMigrationUtils()
    
    if args.action == "backup":
        success = migration_utils.backup_terraform_configurations()
        print(f"Backup {'successful' if success else 'failed'}")
    
    elif args.action == "plan" and args.state_file:
        plan = migration_utils.create_migration_plan(args.state_file)
        print("Migration Plan:")
        print(json.dumps(plan, indent=2))
    
    elif args.action == "migrate" and args.state_file:
        result = migration_utils.execute_migration(args.state_file, args.namespace)
        print("Migration Result:")
        print(json.dumps(result, indent=2))
    
    elif args.action == "validate":
        validation = migration_utils.validate_migration(args.namespace)
        print("Migration Validation:")
        print(json.dumps(validation, indent=2))

if __name__ == "__main__":
    main()
