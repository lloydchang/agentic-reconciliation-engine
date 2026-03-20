#!/usr/bin/env python3
"""
Terraform to Crossplane Migration Script

Migrates Terraform resources to Crossplane compositions with backwards compatibility.
"""

import json
import logging
import os
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TerraformResource:
    """Represents a Terraform resource to be migrated"""
    resource_type: str
    resource_id: str
    provider: str
    config: Dict[str, Any]
    state: Dict[str, Any]

@dataclass
class MigrationResult:
    """Result of migration operation"""
    resource_type: str
    resource_id: str
    provider: str
    status: str
    crossplane_name: str
    error: Optional[str] = None
    timestamp: datetime = None

class TerraformToCrossplaneMigrator:
    """Migrates Terraform resources to Crossplane"""
    
    def __init__(self, terraform_dir: str, crossplane_dir: str):
        self.terraform_dir = Path(terraform_dir)
        self.crossplane_dir = Path(crossplane_dir)
        self.migration_results = []
        
    def analyze_terraform_resources(self) -> List[TerraformResource]:
        """Analyze existing Terraform resources"""
        resources = []
        
        # Parse Terraform state files
        for provider_dir in self.terraform_dir.iterdir():
            if not provider_dir.is_dir():
                continue
                
            provider = provider_dir.name
            state_file = provider_dir / "terraform.tfstate"
            
            if not state_file.exists():
                logger.warning(f"No state file found for provider {provider}")
                continue
            
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Extract resources from Terraform state
                for resource in state.get('resources', []):
                    for instance in resource.get('instances', []):
                        resources.append(TerraformResource(
                            resource_type=resource.get('type'),
                            resource_id=instance.get('attributes', {}).get('id', ''),
                            provider=provider,
                            config=instance.get('attributes', {}),
                            state=instance.get('attributes', {})
                        ))
                        
            except Exception as e:
                logger.error(f"Failed to parse Terraform state for {provider}: {e}")
        
        logger.info(f"Found {len(resources)} Terraform resources to migrate")
        return resources
    
    def create_crossplane_composition(self, resource: TerraformResource) -> str:
        """Create Crossplane composition from Terraform resource"""
        
        # Map Terraform resource types to Crossplane compositions
        composition_map = {
            'aws_instance': 'aws-vm.platform.example.com',
            'aws_vpc': 'aws-network.platform.example.com',
            'azure_virtual_machine': 'azure-vm.platform.example.com',
            'azure_virtual_network': 'azure-network.platform.example.com',
            'google_compute_instance': 'gcp-vm.platform.example.com',
            'google_compute_network': 'gcp-network.platform.example.com'
        }
        
        composition_name = composition_map.get(resource.resource_type)
        if not composition_name:
            logger.warning(f"No Crossplane composition mapping for {resource.resource_type}")
            return ""
        
        # Generate Crossplane resource spec from Terraform config
        crossplane_spec = self._terraform_to_crossplane_spec(resource)
        
        # Create Crossplane composition manifest
        composition = {
            'apiVersion': 'platform.example.com/v1alpha1',
            'kind': f"X{resource.resource_type.split('_')[1].title()}",
            'metadata': {
                'name': f"{resource.resource_id}-crossplane",
                'namespace': 'default',
                'labels': {
                    'migrated-from': 'terraform',
                    'terraform-provider': resource.provider,
                    'terraform-type': resource.resource_type
                }
            },
            'spec': crossplane_spec
        }
        
        return json.dumps(composition, indent=2)
    
    def _terraform_to_crossplane_spec(self, resource: TerraformResource) -> Dict[str, Any]:
        """Convert Terraform resource config to Crossplane spec"""
        
        if resource.resource_type in ['aws_instance', 'azure_virtual_machine', 'google_compute_instance']:
            return {
                'provider': resource.provider,
                'region': resource.config.get('region', 'us-west-2'),
                'instanceType': resource.config.get('instance_type', 'medium'),
                'image': resource.config.get('image', 'ubuntu-latest'),
                'subnetId': resource.config.get('subnet_id', '')
            }
        elif resource.resource_type in ['aws_vpc', 'azure_virtual_network', 'google_compute_network']:
            return {
                'provider': resource.provider,
                'region': resource.config.get('region', 'us-west-2'),
                'cidrBlock': resource.config.get('cidr_block', '10.0.0.0/16'),
                'subnetCount': resource.config.get('subnet_count', 3)
            }
        else:
            logger.warning(f"Unknown resource type for Crossplane conversion: {resource.resource_type}")
            return {}
    
    def migrate_resource(self, resource: TerraformResource) -> MigrationResult:
        """Migrate a single Terraform resource to Crossplane"""
        try:
            logger.info(f"Migrating {resource.resource_type} {resource.resource_id} from {resource.provider}")
            
            # Create Crossplane composition
            composition_content = self.create_crossplane_composition(resource)
            if not composition_content:
                return MigrationResult(
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    provider=resource.provider,
                    status="failed",
                    crossplane_name="",
                    error="No Crossplane composition mapping"
                )
            
            # Write Crossplane composition to file
            crossplane_name = f"{resource.resource_id}-crossplane.yaml"
            crossplane_file = self.crossplane_dir / "compositions" / resource.provider / crossplane_name
            
            crossplane_file.parent.mkdir(parents=True, exist_ok=True)
            with open(crossplane_file, 'w') as f:
                f.write(composition_content)
            
            # Apply Crossplane composition
            result = subprocess.run(
                ['kubectl', 'apply', '-f', str(crossplane_file)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                status = "migrated"
                error = None
                logger.info(f"Successfully migrated {resource.resource_type} {resource.resource_id}")
            else:
                status = "failed"
                error = result.stderr
                logger.error(f"Failed to apply Crossplane composition for {resource.resource_id}: {error}")
            
            return MigrationResult(
                resource_type=resource.resource_type,
                resource_id=resource.resource_id,
                provider=resource.provider,
                status=status,
                crossplane_name=crossplane_name,
                error=error,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to migrate resource {resource.resource_id}: {e}")
            return MigrationResult(
                resource_type=resource.resource_type,
                resource_id=resource.resource_id,
                provider=resource.provider,
                status="failed",
                crossplane_name="",
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    def migrate_all_resources(self) -> List[MigrationResult]:
        """Migrate all Terraform resources to Crossplane"""
        resources = self.analyze_terraform_resources()
        
        if not resources:
            logger.warning("No Terraform resources found to migrate")
            return []
        
        results = []
        for resource in resources:
            result = self.migrate_resource(resource)
            results.append(result)
            self.migration_results.append(result)
        
        return results
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate migration report"""
        if not self.migration_results:
            return {"status": "no_resources", "message": "No resources to migrate"}
        
        total = len(self.migration_results)
        successful = len([r for r in self.migration_results if r.status == "migrated"])
        failed = len([r for r in self.migration_results if r.status == "failed"])
        
        return {
            "migration_summary": {
                "total_resources": total,
                "successful_migrations": successful,
                "failed_migrations": failed,
                "success_rate": successful / total if total > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            },
            "migrated_resources": [
                {
                    "terraform_type": r.resource_type,
                    "terraform_id": r.resource_id,
                    "provider": r.provider,
                    "crossplane_name": r.crossplane_name,
                    "status": r.status,
                    "error": r.error
                }
                for r in self.migration_results
            ],
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate post-migration recommendations"""
        recommendations = []
        
        failed_migrations = [r for r in self.migration_results if r.status == "failed"]
        if failed_migrations:
            recommendations.append("Review and fix failed migrations before decommissioning Terraform")
        
        successful_migrations = [r for r in self.migration_results if r.status == "migrated"]
        if successful_migrations:
            recommendations.append("Validate Crossplane resources match Terraform functionality")
            recommendations.append("Update CI/CD pipelines to use Crossplane instead of Terraform")
            recommendations.append("Train teams on Crossplane operations and troubleshooting")
        
        return recommendations

def main():
    """Main migration execution"""
    logging.basicConfig(level=logging.INFO)
    
    terraform_dir = "/Users/lloyd/github/antigravity/agentic-reconciliation-engine/core/infrastructure/terraform"
    crossplane_dir = "/Users/lloyd/github/antigravity/agentic-reconciliation-engine/core/infrastructure/crossplane"
    
    migrator = TerraformToCrossplaneMigrator(terraform_dir, crossplane_dir)
    
    logger.info("Starting Terraform to Crossplane migration")
    
    # Migrate all resources
    results = migrator.migrate_all_resources()
    
    # Generate and save migration report
    report = migrator.generate_migration_report()
    
    report_file = crossplane_dir / "migration-report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Migration completed. Report saved to {report_file}")
    print(f"Migration Summary:")
    print(f"  Total Resources: {report['migration_summary']['total_resources']}")
    print(f"  Successful: {report['migration_summary']['successful_migrations']}")
    print(f"  Failed: {report['migration_summary']['failed_migrations']}")
    print(f"  Success Rate: {report['migration_summary']['success_rate']:.2%}")

if __name__ == "__main__":
    main()
