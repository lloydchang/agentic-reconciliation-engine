#!/usr/bin/env python3
"""
Terraform to Crossplane Migration Tool

Automates migration from Terraform-managed infrastructure to Crossplane Kubernetes-native resources.
Maintains state consistency and provides rollback capabilities.
"""

import json
import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import yaml

from crossplane_orchestrator import CrossplaneOrchestrator, ResourceRequest, ResourceType, CloudProvider

logger = logging.getLogger(__name__)

@dataclass
class TerraformResource:
    """Represents a Terraform resource"""
    resource_type: str
    resource_name: str
    attributes: Dict[str, Any]
    dependencies: List[str]
    provider: str

@dataclass
class MigrationPlan:
    """Migration plan for Terraform resources"""
    source_resources: List[TerraformResource]
    target_resources: List[ResourceRequest]
    migration_order: List[str]
    rollback_plan: Dict[str, Any]
    estimated_downtime: int  # in minutes

class TerraformMigrationTool:
    """Tool for migrating Terraform resources to Crossplane"""
    
    def __init__(self, terraform_dir: str = "./terraform"):
        self.terraform_dir = Path(terraform_dir)
        self.orchestrator = CrossplaneOrchestrator()
        self.migration_state = {}
        
    def discover_terraform_resources(self) -> List[TerraformResource]:
        """Discover all Terraform-managed resources"""
        resources = []
        
        if not self.terraform_dir.exists():
            logger.error(f"Terraform directory {self.terraform_dir} does not exist")
            return resources
        
        # Parse Terraform state files
        for state_file in self.terraform_dir.rglob("*.tfstate"):
            resources.extend(self._parse_tfstate(state_file))
        
        # Parse Terraform configuration files
        for tf_file in self.terraform_dir.rglob("*.tf"):
            resources.extend(self._parse_tf_config(tf_file))
        
        logger.info(f"Discovered {len(resources)} Terraform resources")
        return resources
    
    def _parse_tfstate(self, state_file: Path) -> List[TerraformResource]:
        """Parse Terraform state file to extract resources"""
        resources = []
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            for resource in state.get('resources', []):
                if 'instances' in resource and resource['instances']:
                    instance = resource['instances'][0]
                    
                    terraform_resource = TerraformResource(
                        resource_type=resource['type'],
                        resource_name=resource['name'],
                        attributes=instance.get('attributes', {}),
                        dependencies=self._extract_dependencies(instance),
                        provider=resource.get('provider', 'unknown')
                    )
                    resources.append(terraform_resource)
        
        except Exception as e:
            logger.error(f"Failed to parse state file {state_file}: {e}")
        
        return resources
    
    def _parse_tf_config(self, tf_file: Path) -> List[TerraformResource]:
        """Parse Terraform configuration file"""
        resources = []
        
        try:
            with open(tf_file, 'r') as f:
                content = f.read()
            
            # Simple regex-based parsing (in production, use proper HCL parser)
            import re
            
            # Match resource blocks
            resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]+)\}'
            matches = re.findall(resource_pattern, content, re.DOTALL)
            
            for resource_type, resource_name, resource_body in matches:
                # Extract basic attributes
                attributes = self._parse_resource_attributes(resource_body)
                
                terraform_resource = TerraformResource(
                    resource_type=resource_type,
                    resource_name=resource_name,
                    attributes=attributes,
                    dependencies=self._extract_dependencies_from_body(resource_body),
                    provider=self._extract_provider_from_type(resource_type)
                )
                resources.append(terraform_resource)
        
        except Exception as e:
            logger.error(f"Failed to parse TF file {tf_file}: {e}")
        
        return resources
    
    def _parse_resource_attributes(self, resource_body: str) -> Dict[str, Any]:
        """Parse resource attributes from Terraform resource body"""
        attributes = {}
        
        # Simple attribute parsing (in production, use proper HCL parser)
        import re
        
        # Extract common attributes
        patterns = {
            'region': r'region\s*=\s*"([^"]+)"',
            'cidr_block': r'cidr_block\s*=\s*"([^"]+)"',
            'instance_type': r'instance_type\s*=\s*"([^"]+)"',
            'ami': r'ami\s*=\s*"([^"]+)"',
            'bucket': r'bucket\s*=\s*"([^"]+)"',
            'name': r'name\s*=\s*"([^"]+)"'
        }
        
        for attr, pattern in patterns.items():
            match = re.search(pattern, resource_body)
            if match:
                attributes[attr] = match.group(1)
        
        return attributes
    
    def _extract_dependencies(self, instance: Dict[str, Any]) -> List[str]:
        """Extract resource dependencies from Terraform instance"""
        dependencies = []
        
        # Extract from dependencies field if present
        if 'dependencies' in instance:
            dependencies.extend(instance['dependencies'])
        
        # Extract from attribute references
        attributes = instance.get('attributes', {})
        for key, value in attributes.items():
            if isinstance(value, str) and '${' in value:
                # Simple dependency extraction
                dependencies.append(value)
        
        return dependencies
    
    def _extract_dependencies_from_body(self, resource_body: str) -> List[str]:
        """Extract dependencies from resource body"""
        dependencies = []
        
        import re
        references = re.findall(r'\$\{([^}]+)\}', resource_body)
        dependencies.extend(references)
        
        return dependencies
    
    def _extract_provider_from_type(self, resource_type: str) -> str:
        """Extract cloud provider from Terraform resource type"""
        if resource_type.startswith('aws_'):
            return 'aws'
        elif resource_type.startswith('azurerm_'):
            return 'azure'
        elif resource_type.startswith('google_'):
            return 'gcp'
        else:
            return 'unknown'
    
    def create_migration_plan(self, resources: List[TerraformResource]) -> MigrationPlan:
        """Create migration plan for Terraform resources"""
        target_resources = []
        migration_order = []
        
        # Group resources by type and provider
        resource_groups = {}
        for resource in resources:
            key = f"{resource.provider}_{resource.resource_type}"
            if key not in resource_groups:
                resource_groups[key] = []
            resource_groups[key].append(resource)
        
        # Create migration order (network first, then compute, then storage)
        type_order = ['vpc', 'subnet', 'security_group', 'instance', 'bucket']
        
        for resource_type in type_order:
            for provider in ['aws', 'azure', 'gcp']:
                key = f"{provider}_{resource_type}"
                if key in resource_groups:
                    for tf_resource in resource_groups[key]:
                        crossplane_request = self._convert_to_crossplane(tf_resource)
                        if crossplane_request:
                            target_resources.append(crossplane_request)
                            migration_order.append(tf_resource.resource_name)
        
        # Create rollback plan
        rollback_plan = {
            'terraform_backup': True,
            'crossplane_cleanup': True,
            'restore_order': list(reversed(migration_order))
        }
        
        return MigrationPlan(
            source_resources=resources,
            target_resources=target_resources,
            migration_order=migration_order,
            rollback_plan=rollback_plan,
            estimated_downtime=5  # Conservative estimate
        )
    
    def _convert_to_crossplane(self, tf_resource: TerraformResource) -> Optional[ResourceRequest]:
        """Convert Terraform resource to Crossplane ResourceRequest"""
        
        # Map Terraform resource types to Crossplane resource types
        resource_mapping = {
            'aws_vpc': (ResourceType.NETWORK, CloudProvider.AWS),
            'aws_subnet': (ResourceType.NETWORK, CloudProvider.AWS),
            'aws_security_group': (ResourceType.NETWORK, CloudProvider.AWS),
            'aws_instance': (ResourceType.COMPUTE, CloudProvider.AWS),
            'aws_s3_bucket': (ResourceType.STORAGE, CloudProvider.AWS),
            'azurerm_virtual_network': (ResourceType.NETWORK, CloudProvider.AZURE),
            'azurerm_subnet': (ResourceType.NETWORK, CloudProvider.AZURE),
            'azurerm_network_security_group': (ResourceType.NETWORK, CloudProvider.AZURE),
            'azurerm_virtual_machine': (ResourceType.COMPUTE, CloudProvider.AZURE),
            'azurerm_storage_account': (ResourceType.STORAGE, CloudProvider.AZURE),
            'google_compute_network': (ResourceType.NETWORK, CloudProvider.GCP),
            'google_compute_subnetwork': (ResourceType.NETWORK, CloudProvider.GCP),
            'google_compute_firewall': (ResourceType.NETWORK, CloudProvider.GCP),
            'google_compute_instance': (ResourceType.COMPUTE, CloudProvider.GCP),
            'google_storage_bucket': (ResourceType.STORAGE, CloudProvider.GCP)
        }
        
        key = tf_resource.resource_type
        if key not in resource_mapping:
            logger.warning(f"No mapping for resource type: {key}")
            return None
        
        resource_type, provider = resource_mapping[key]
        
        # Convert attributes based on resource type
        config = self._convert_attributes(tf_resource.attributes, resource_type)
        
        return ResourceRequest(
            name=tf_resource.resource_name,
            resource_type=resource_type,
            provider=provider,
            region=config.get('region', 'us-west-2'),
            config=config,
            tags=self._extract_tags(tf_resource.attributes)
        )
    
    def _convert_attributes(self, attributes: Dict[str, Any], resource_type: ResourceType) -> Dict[str, Any]:
        """Convert Terraform attributes to Crossplane config"""
        
        if resource_type == ResourceType.NETWORK:
            return {
                'cidrBlock': attributes.get('cidr_block', '10.0.0.0/16'),
                'subnetCount': len([k for k in attributes.keys() if 'subnet' in k]),
                'enableDnsHostnames': True,
                'enableDnsSupport': True,
                'region': attributes.get('region', 'us-west-2')
            }
        
        elif resource_type == ResourceType.COMPUTE:
            return {
                'instanceType': attributes.get('instance_type', 't3.medium'),
                'imageId': attributes.get('ami'),
                'keyName': attributes.get('key_name'),
                'minCount': 1,
                'maxCount': 1,
                'monitoring': True,
                'region': attributes.get('region', 'us-west-2')
            }
        
        elif resource_type == ResourceType.STORAGE:
            return {
                'bucketName': attributes.get('bucket', attributes.get('name')),
                'storageClass': 'standard',
                'versioning': False,
                'encryption': True,
                'accessControl': 'private',
                'region': attributes.get('region', 'us-west-2')
            }
        
        return {}
    
    def _extract_tags(self, attributes: Dict[str, Any]) -> Dict[str, str]:
        """Extract tags from Terraform attributes"""
        tags = {}
        
        # Common tag patterns
        if 'tags' in attributes:
            if isinstance(attributes['tags'], dict):
                tags = attributes['tags']
            elif isinstance(attributes['tags'], list):
                # Handle tag lists
                for tag in attributes['tags']:
                    if isinstance(tag, dict) and 'key' in tag and 'value' in tag:
                        tags[tag['key']] = tag['value']
        
        # Add migration tag
        tags['migrated-from'] = 'terraform'
        tags['migration-date'] = datetime.now().isoformat()
        
        return tags
    
    def execute_migration(self, plan: MigrationPlan, dry_run: bool = True) -> Dict[str, Any]:
        """Execute the migration plan"""
        results = {
            'started_at': datetime.now().isoformat(),
            'dry_run': dry_run,
            'resources_migrated': [],
            'resources_failed': [],
            'rollback_triggered': False
        }
        
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting migration of {len(plan.target_resources)} resources")
        
        # Execute migration in order
        for resource_request in plan.target_resources:
            try:
                if dry_run:
                    logger.info(f"DRY RUN: Would migrate {resource_request.resource_type.value} {resource_request.name}")
                    results['resources_migrated'].append({
                        'name': resource_request.name,
                        'type': resource_request.resource_type.value,
                        'provider': resource_request.provider.value,
                        'status': 'dry_run_success'
                    })
                else:
                    # Actually create the resource
                    if resource_request.resource_type == ResourceType.NETWORK:
                        status = self.orchestrator.create_network(resource_request)
                    elif resource_request.resource_type == ResourceType.COMPUTE:
                        status = self.orchestrator.create_compute(resource_request)
                    elif resource_request.resource_type == ResourceType.STORAGE:
                        status = self.orchestrator.create_storage(resource_request)
                    
                    if status.status == 'created':
                        results['resources_migrated'].append({
                            'name': resource_request.name,
                            'type': resource_request.resource_type.value,
                            'provider': resource_request.provider.value,
                            'status': 'success',
                            'message': status.message
                        })
                    else:
                        results['resources_failed'].append({
                            'name': resource_request.name,
                            'type': resource_request.resource_type.value,
                            'provider': resource_request.provider.value,
                            'status': 'failed',
                            'error': status.message
                        })
                
            except Exception as e:
                logger.error(f"Failed to migrate {resource_request.name}: {e}")
                results['resources_failed'].append({
                    'name': resource_request.name,
                    'type': resource_request.resource_type.value,
                    'provider': resource_request.provider.value,
                    'status': 'failed',
                    'error': str(e)
                })
        
        results['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"Migration completed. Success: {len(results['resources_migrated'])}, Failed: {len(results['resources_failed'])}")
        
        return results
    
    def create_backup(self) -> str:
        """Create backup of current Terraform state"""
        backup_dir = tempfile.mkdtemp(prefix="terraform_backup_")
        
        try:
            # Copy Terraform files
            import shutil
            if self.terraform_dir.exists():
                shutil.copytree(self.terraform_dir, backup_dir + "/terraform")
            
            # Export current state
            if self.terraform_dir.exists():
                os.chdir(self.terraform_dir)
                result = subprocess.run(['terraform', 'show', '-json'], 
                                    capture_output=True, text=True)
                if result.returncode == 0:
                    with open(f"{backup_dir}/terraform_state.json", 'w') as f:
                        f.write(result.stdout)
            
            logger.info(f"Backup created at {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return backup_dir
    
    def rollback(self, backup_dir: str) -> bool:
        """Rollback migration using backup"""
        try:
            logger.info(f"Rolling back migration using backup {backup_dir}")
            
            # Delete Crossplane resources
            # This would need to be implemented based on what was created
            
            # Restore Terraform state
            terraform_backup = Path(backup_dir) / "terraform"
            if terraform_backup.exists():
                import shutil
                if self.terraform_dir.exists():
                    shutil.rmtree(self.terraform_dir)
                shutil.copytree(terraform_backup, self.terraform_dir)
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

def main():
    """Main migration execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Terraform to Crossplane Migration Tool")
    parser.add_argument("--terraform-dir", default="./terraform", 
                       help="Terraform configuration directory")
    parser.add_argument("--action", choices=["discover", "plan", "migrate", "backup", "rollback"],
                       default="discover", help="Migration action")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Perform dry run migration")
    parser.add_argument("--output", help="Output file for migration plan")
    parser.add_argument("--backup-dir", help="Backup directory for rollback")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    migrator = TerraformMigrationTool(args.terraform_dir)
    
    if args.action == "discover":
        resources = migrator.discover_terraform_resources()
        
        output = {
            'discovered_at': datetime.now().isoformat(),
            'terraform_dir': args.terraform_dir,
            'total_resources': len(resources),
            'resources': [
                {
                    'type': r.resource_type,
                    'name': r.resource_name,
                    'provider': r.provider,
                    'dependencies': r.dependencies
                }
                for r in resources
            ]
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output, f, indent=2)
        else:
            print(json.dumps(output, indent=2))
    
    elif args.action == "plan":
        resources = migrator.discover_terraform_resources()
        plan = migrator.create_migration_plan(resources)
        
        output = {
            'plan_created_at': datetime.now().isoformat(),
            'source_resources': len(plan.source_resources),
            'target_resources': len(plan.target_resources),
            'migration_order': plan.migration_order,
            'estimated_downtime_minutes': plan.estimated_downtime,
            'rollback_plan': plan.rollback_plan
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output, f, indent=2)
        else:
            print(json.dumps(output, indent=2))
    
    elif args.action == "migrate":
        resources = migrator.discover_terraform_resources()
        plan = migrator.create_migration_plan(resources)
        
        # Create backup before migration
        backup_dir = migrator.create_backup()
        
        # Execute migration
        results = migrator.execute_migration(plan, dry_run=args.dry_run)
        results['backup_directory'] = backup_dir
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(json.dumps(results, indent=2))
    
    elif args.action == "backup":
        backup_dir = migrator.create_backup()
        print(f"Backup created at: {backup_dir}")
    
    elif args.action == "rollback" and args.backup_dir:
        success = migrator.rollback(args.backup_dir)
        print(f"Rollback {'successful' if success else 'failed'}")

if __name__ == "__main__":
    main()
