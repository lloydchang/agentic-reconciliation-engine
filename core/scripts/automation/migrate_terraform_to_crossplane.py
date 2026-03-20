#!/usr/bin/env python3
"""
Terraform to Crossplane Migration Script

Automates the migration of Terraform configurations to Crossplane composite resources.
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import subprocess
import yaml

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

@dataclass
class TerraformResource:
    """Represents a Terraform resource"""
    resource_type: str
    name: str
    provider: str
    config: Dict[str, Any]
    dependencies: List[str]

@dataclass
class CrossplaneResource:
    """Represents a Crossplane composite resource"""
    kind: str
    name: str
    spec: Dict[str, Any]
    provider: str

class TerraformToCrossplaneMigrator:
    """Migrates Terraform configurations to Crossplane"""
    
    def __init__(self, terraform_dir: str, output_dir: str):
        self.terraform_dir = Path(terraform_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Kubernetes client
        config.load_kube_config()
        self.k8s_client = client.CustomObjectsApi()
        
        self.migration_mappings = {
            'aws': {
                'aws_instance': {'crossplane_type': 'XCompute', 'provider': 'aws'},
                'aws_vpc': {'crossplane_type': 'XNetwork', 'provider': 'aws'},
                'aws_s3_bucket': {'crossplane_type': 'XStorage', 'provider': 'aws'},
                'aws_db_instance': {'crossplane_type': 'XDatabase', 'provider': 'aws'},
            },
            'azure': {
                'azurerm_linux_virtual_machine': {'crossplane_type': 'XCompute', 'provider': 'azure'},
                'azurerm_virtual_network': {'crossplane_type': 'XNetwork', 'provider': 'azure'},
                'azurerm_storage_account': {'crossplane_type': 'XStorage', 'provider': 'azure'},
                'azurerm_postgresql_server': {'crossplane_type': 'XDatabase', 'provider': 'azure'},
            },
            'gcp': {
                'google_compute_instance': {'crossplane_type': 'XCompute', 'provider': 'gcp'},
                'google_compute_network': {'crossplane_type': 'XNetwork', 'provider': 'gcp'},
                'google_storage_bucket': {'crossplane_type': 'XStorage', 'provider': 'gcp'},
                'google_sql_database_instance': {'crossplane_type': 'XDatabase', 'provider': 'gcp'},
            }
        }
    
    def analyze_terraform_state(self) -> List[TerraformResource]:
        """Analyze Terraform state to extract resources"""
        logger.info("Analyzing Terraform state...")
        
        # Try to get state from terraform show
        try:
            result = subprocess.run(
                ['terraform', 'show', '-json'],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                check=True
            )
            terraform_data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get Terraform state: {e}")
            return []
        
        resources = []
        values = terraform_data.get('values', {})
        
        # Parse resources from Terraform state
        for resource_type, resource_data in values.get('root_module', {}).get('resources', {}).items():
            for resource_name, resource_config in resource_data.items():
                provider = self._extract_provider_from_resource_type(resource_type)
                
                terraform_resource = TerraformResource(
                    resource_type=resource_type,
                    name=resource_name,
                    provider=provider,
                    config=resource_config,
                    dependencies=self._extract_dependencies(resource_config)
                )
                resources.append(terraform_resource)
        
        logger.info(f"Found {len(resources)} Terraform resources")
        return resources
    
    def _extract_provider_from_resource_type(self, resource_type: str) -> str:
        """Extract provider from Terraform resource type"""
        if resource_type.startswith('aws_'):
            return 'aws'
        elif resource_type.startswith('azurerm_'):
            return 'azure'
        elif resource_type.startswith('google_'):
            return 'gcp'
        else:
            return 'unknown'
    
    def _extract_dependencies(self, resource_config: Dict[str, Any]) -> List[str]:
        """Extract resource dependencies"""
        dependencies = []
        
        # Look for references to other resources
        def find_references(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'id' or key == 'arn':
                        if isinstance(value, str) and '.' in value:
                            # This looks like a reference to another resource
                            parts = value.split('.')
                            if len(parts) >= 2:
                                dependencies.append(parts[1])
                    else:
                        find_references(value)
            elif isinstance(obj, list):
                for item in obj:
                    find_references(item)
        
        find_references(resource_config)
        return list(set(dependencies))
    
    def convert_to_crossplane_resources(self, terraform_resources: List[TerraformResource]) -> List[CrossplaneResource]:
        """Convert Terraform resources to Crossplane resources"""
        logger.info("Converting Terraform resources to Crossplane...")
        
        crossplane_resources = []
        
        for tf_resource in terraform_resources:
            provider_config = self.migration_mappings.get(tf_resource.provider, {})
            resource_mapping = provider_config.get(tf_resource.resource_type, {})
            
            if not resource_mapping:
                logger.warning(f"No mapping for {tf_resource.provider}.{tf_resource.resource_type}")
                continue
            
            crossplane_spec = self._convert_resource_spec(
                tf_resource.config,
                tf_resource.provider,
                resource_mapping['crossplane_type']
            )
            
            crossplane_resource = CrossplaneResource(
                kind=resource_mapping['crossplane_type'],
                name=tf_resource.name,
                spec=crossplane_spec,
                provider=resource_mapping['provider']
            )
            crossplane_resources.append(crossplane_resource)
        
        logger.info(f"Converted {len(crossplane_resources)} resources to Crossplane")
        return crossplane_resources
    
    def _convert_resource_spec(self, tf_config: Dict[str, Any], provider: str, crossplane_type: str) -> Dict[str, Any]:
        """Convert Terraform resource spec to Crossplane spec"""
        if crossplane_type == 'XCompute':
            return self._convert_compute_spec(tf_config, provider)
        elif crossplane_type == 'XNetwork':
            return self._convert_network_spec(tf_config, provider)
        elif crossplane_type == 'XStorage':
            return self._convert_storage_spec(tf_config, provider)
        elif crossplane_type == 'XDatabase':
            return self._convert_database_spec(tf_config, provider)
        else:
            return {}
    
    def _convert_compute_spec(self, tf_config: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Convert Terraform compute spec to Crossplane XCompute spec"""
        spec = {
            'provider': provider,
            'environment': 'production'  # Default, can be overridden
        }
        
        # Common mappings
        if 'instance_type' in tf_config:
            spec['instanceType'] = tf_config['instance_type']
        if 'ami' in tf_config:
            spec['image'] = tf_config['ami']
        
        # Provider-specific mappings
        if provider == 'aws':
            if 'subnet_id' in tf_config:
                spec['subnetId'] = tf_config['subnet_id']
            if 'key_name' in tf_config:
                spec['sshKey'] = tf_config['key_name']
            if 'vpc_security_group_ids' in tf_config:
                spec['securityGroupIds'] = tf_config['vpc_security_group_ids']
        
        elif provider == 'azure':
            if 'location' in tf_config:
                spec['region'] = tf_config['location']
            if 'size' in tf_config:
                spec['instanceType'] = tf_config['size']
            if 'network_interface' in tf_config:
                # Extract network info from network_interface
                pass
        
        elif provider == 'gcp':
            if 'machine_type' in tf_config:
                spec['instanceType'] = tf_config['machine_type']
            if 'zone' in tf_config:
                spec['region'] = tf_config['zone'].rsplit('-', 1)[0]
            if 'network_interface' in tf_config:
                # Extract network info
                pass
        
        return spec
    
    def _convert_network_spec(self, tf_config: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Convert Terraform network spec to Crossplane XNetwork spec"""
        spec = {
            'provider': provider,
            'environment': 'production'
        }
        
        if provider == 'aws':
            if 'cidr_block' in tf_config:
                spec['cidrBlock'] = tf_config['cidr_block']
            if 'tags' in tf_config:
                spec.update(tf_config['tags'])
        
        elif provider == 'azure':
            if 'address_space' in tf_config:
                spec['cidrBlock'] = tf_config['address_space'][0] if tf_config['address_space'] else '10.0.0.0/16'
            if 'location' in tf_config:
                spec['region'] = tf_config['location']
        
        elif provider == 'gcp':
            if 'auto_create_subnetworks' in tf_config:
                pass  # Handled by Crossplane composition
            if 'routing_mode' in tf_config:
                pass  # Handled by Crossplane composition
        
        return spec
    
    def _convert_storage_spec(self, tf_config: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Convert Terraform storage spec to Crossplane XStorage spec"""
        spec = {
            'provider': provider,
            'environment': 'production'
        }
        
        if provider == 'aws':
            if 'bucket' in tf_config:
                spec['name'] = tf_config['bucket']
            if 'region' in tf_config:
                spec['region'] = tf_config['region']
            if 'versioning' in tf_config:
                spec['versioning'] = tf_config['versioning'].get('enabled', False)
            if 'server_side_encryption_configuration' in tf_config:
                spec['encryption'] = True
        
        elif provider == 'azure':
            if 'name' in tf_config:
                spec['name'] = tf_config['name']
            if 'location' in tf_config:
                spec['region'] = tf_config['location']
            if 'account_tier' in tf_config:
                spec['storageClass'] = tf_config['account_tier']
        
        elif provider == 'gcp':
            if 'name' in tf_config:
                spec['name'] = tf_config['name']
            if 'location' in tf_config:
                spec['region'] = tf_config['location']
            if 'versioning' in tf_config:
                spec['versioning'] = tf_config['versioning'].get('enabled', False)
        
        return spec
    
    def _convert_database_spec(self, tf_config: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Convert Terraform database spec to Crossplane XDatabase spec"""
        spec = {
            'provider': provider,
            'environment': 'production'
        }
        
        if provider == 'aws':
            if 'instance_class' in tf_config:
                spec['instanceClass'] = tf_config['instance_class']
            if 'engine' in tf_config:
                spec['engine'] = tf_config['engine']
            if 'allocated_storage' in tf_config:
                spec['storageSize'] = tf_config['allocated_storage']
            if 'backup_retention_period' in tf_config:
                spec['backupRetention'] = tf_config['backup_retention_period']
            if 'storage_encrypted' in tf_config:
                spec['encryption'] = tf_config['storage_encrypted']
            if 'multi_az' in tf_config:
                spec['highAvailability'] = tf_config['multi_az']
        
        elif provider == 'azure':
            if 'location' in tf_config:
                spec['region'] = tf_config['location']
            if 'version' in tf_config:
                spec['version'] = tf_config['version']
            if 'administrator_login_password' in tf_config:
                pass  # Handled by Crossplane secrets
            if 'sku_name' in tf_config:
                spec['instanceClass'] = tf_config['sku_name']
        
        elif provider == 'gcp':
            if 'database_version' in tf_config:
                spec['version'] = tf_config['database_version']
            if 'region' in tf_config:
                spec['region'] = tf_config['region']
            if 'tier' in tf_config:
                spec['instanceClass'] = tf_config['tier']
        
        return spec
    
    def generate_crossplane_manifests(self, crossplane_resources: List[CrossplaneResource]) -> List[str]:
        """Generate Crossplane Kubernetes manifests"""
        logger.info("Generating Crossplane manifests...")
        
        manifests = []
        
        # Group resources by type for better organization
        resources_by_type = {}
        for resource in crossplane_resources:
            if resource.kind not in resources_by_type:
                resources_by_type[resource.kind] = []
            resources_by_type[resource.kind].append(resource)
        
        # Generate manifests for each resource type
        for resource_type, resources in resources_by_type.items():
            for resource in resources:
                manifest = {
                    'apiVersion': 'platform.example.com/v1alpha1',
                    'kind': resource.kind,
                    'metadata': {
                        'name': resource.name,
                        'labels': {
                            'managed-by': 'terraform-migration',
                            'provider': resource.provider,
                            'migrated-from': 'terraform'
                        }
                    },
                    'spec': resource.spec
                }
                
                manifest_yaml = yaml.dump(manifest, default_flow_style=False)
                manifests.append(manifest_yaml)
        
        logger.info(f"Generated {len(manifests)} Crossplane manifests")
        return manifests
    
    def write_crossplane_files(self, manifests: List[str]):
        """Write Crossplane manifests to files"""
        logger.info("Writing Crossplane manifests...")
        
        # Create directory structure
        (self.output_dir / 'crossplane').mkdir(exist_ok=True)
        
        # Write individual resource files
        for i, manifest in enumerate(manifests):
            filename = f"resource_{i+1:03d}.yaml"
            filepath = self.output_dir / 'crossplane' / filename
            
            with open(filepath, 'w') as f:
                f.write(manifest)
            
            logger.info(f"Written: {filepath}")
        
        # Write consolidated manifest
        consolidated_file = self.output_dir / 'crossplane' / 'all-resources.yaml'
        with open(consolidated_file, 'w') as f:
            f.write("---\n".join(manifests))
        
        logger.info(f"Written consolidated manifest: {consolidated_file}")
        
        # Write migration report
        self._write_migration_report(len(manifests))
    
    def _write_migration_report(self, resource_count: int):
        """Write migration report"""
        report = {
            'migration_summary': {
                'terraform_directory': str(self.terraform_dir),
                'output_directory': str(self.output_dir),
                'resources_migrated': resource_count,
                'migration_date': self._get_current_timestamp()
            },
            'next_steps': [
                '1. Review generated Crossplane manifests',
                '2. Apply Crossplane providers and compositions',
                '3. Test Crossplane resources in staging',
                '4. Apply resources to production',
                '5. Update CI/CD pipelines',
                '6. Decommission Terraform resources'
            ],
            'validation_checks': [
                'Verify Crossplane provider health: kubectl get providers',
                'Check resource status: kubectl get xnetworks,xcomputes,xstorages,xdatabases',
                'Validate resource connectivity',
                'Test failover procedures'
            ]
        }
        
        report_file = self.output_dir / 'migration-report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Migration report written: {report_file}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def backup_terraform_state(self):
        """Backup Terraform state before migration"""
        logger.info("Backing up Terraform state...")
        
        try:
            # Export Terraform state
            result = subprocess.run(
                ['terraform', 'state', 'pull'],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Save backup
            backup_file = self.output_dir / 'terraform-state-backup.json'
            with open(backup_file, 'w') as f:
                f.write(result.stdout)
            
            logger.info(f"Terraform state backup: {backup_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to backup Terraform state: {e}")
            return False
    
    def migrate(self):
        """Execute the complete migration process"""
        logger.info("Starting Terraform to Crossplane migration...")
        
        # Step 1: Backup Terraform state
        if not self.backup_terraform_state():
            logger.error("Failed to backup Terraform state, aborting migration")
            return False
        
        # Step 2: Analyze Terraform configuration
        terraform_resources = self.analyze_terraform_state()
        if not terraform_resources:
            logger.warning("No Terraform resources found to migrate")
            return True
        
        # Step 3: Convert to Crossplane resources
        crossplane_resources = self.convert_to_crossplane_resources(terraform_resources)
        if not crossplane_resources:
            logger.error("Failed to convert resources to Crossplane")
            return False
        
        # Step 4: Generate Crossplane manifests
        manifests = self.generate_crossplane_manifests(crossplane_resources)
        
        # Step 5: Write Crossplane files
        self.write_crossplane_files(manifests)
        
        logger.info("✅ Terraform to Crossplane migration completed successfully!")
        return True

def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description="Migrate Terraform to Crossplane")
    parser.add_argument("terraform_dir", help="Path to Terraform configuration directory")
    parser.add_argument("output_dir", help="Output directory for Crossplane manifests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Validate input directory
    terraform_dir = Path(args.terraform_dir)
    if not terraform_dir.exists():
        logger.error(f"Terraform directory does not exist: {terraform_dir}")
        return 1
    
    # Create migrator and run migration
    migrator = TerraformToCrossplaneMigrator(args.terraform_dir, args.output_dir)
    
    try:
        success = migrator.migrate()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
