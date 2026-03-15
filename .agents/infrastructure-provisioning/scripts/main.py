#!/usr/bin/env python3
"""
Infrastructure Provisioning Agent - Main Entry Point

This is the main entry point for the infrastructure provisioning agent skill.
It demonstrates proper PEP 723 dependency management and Pydantic type safety.
"""

# /// script
# dependencies = [
#   "pydantic>=1.10.0",
#   "boto3>=1.26.0",
#   "azure-mgmt-compute>=29.0.0",
#   "google-cloud-compute>=1.8.0",
#   "kubernetes>=25.0.0",
#   "requests>=2.28.0",
#   "typer>=0.7.0"
# ]
# ///

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add shared models to path
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

try:
    import typer
    from pydantic import ValidationError
    from models import (
        InfrastructureRequest, InfrastructureResult, 
        CloudProvider, OperationType, Environment,
        SkillMetadata, RiskLevel, AutonomyLevel
    )
    from multi_cloud_orchestrator import MultiCloudOrchestrator
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install with: pip install -e .")
    sys.exit(1)

app = typer.Typer(
    name="infrastructure-provisioning",
    help="Multi-Cloud Infrastructure Provisioning Agent",
    no_args_is_help=True
)


@app.command()
def provision(
    resource_type: str = typer.Option(..., "--type", "-t", help="Resource type to provision"),
    resource_name: str = typer.Option(..., "--name", "-n", help="Resource name"),
    provider: CloudProvider = typer.Option(CloudProvider.AWS, "--provider", "-p", help="Cloud provider"),
    region: str = typer.Option("us-west-2", "--region", "-r", help="Target region"),
    environment: Environment = typer.Option(Environment.PRODUCTION, "--env", "-e", help="Target environment"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Dry run mode"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Tags as key=value pairs, comma-separated"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Provision infrastructure resources"""
    
    # Parse tags
    tag_dict = {}
    if tags:
        for tag in tags.split(','):
            if '=' in tag:
                key, value = tag.split('=', 1)
                tag_dict[key.strip()] = value.strip()
    
    # Create request
    try:
        request = InfrastructureRequest(
            operation=OperationType.PROVISION,
            target_resource=resource_name,
            cloud_provider=provider,
            environment=environment,
            dry_run=dry_run,
            parameters={
                "resource_type": resource_type,
                "region": region,
                "configuration": load_config(config_file) if config_file else {},
                "tags": tag_dict
            }
        )
    except ValidationError as e:
        typer.echo(f"❌ Invalid request: {e}", err=True)
        raise typer.Exit(1)
    
    if verbose:
        typer.echo(f"📋 Provisioning request:")
        typer.echo(f"   Resource: {resource_type} ({resource_name})")
        typer.echo(f"   Provider: {provider.value}")
        typer.echo(f"   Region: {region}")
        typer.echo(f"   Environment: {environment.value}")
        typer.echo(f"   Dry Run: {dry_run}")
        if tag_dict:
            typer.echo(f"   Tags: {tag_dict}")
    
    # Create metadata
    metadata = SkillMetadata(
        skill_name="infrastructure-provisioning",
        risk_level=RiskLevel.MEDIUM,
        autonomy=AutonomyLevel.CONDITIONAL,
        execution_id=f"prov-{resource_name}-{int(os.times()[4])}"
    )
    
    # Execute provisioning
    try:
        orchestrator = MultiCloudOrchestrator(config_file)
        result = execute_provisioning(orchestrator, request, metadata, verbose)
        
        typer.echo(f"✅ Provisioning completed: {result.status}")
        if result.resource_id:
            typer.echo(f"   Resource ID: {result.resource_id}")
        if result.cost_estimate:
            typer.echo(f"   Estimated Cost: ${result.cost_estimate:.2f}/month")
        
    except Exception as e:
        typer.echo(f"❌ Provisioning failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def status(
    resource_name: str = typer.Argument(..., help="Resource name to check"),
    provider: CloudProvider = typer.Option(CloudProvider.ALL, "--provider", "-p", help="Cloud provider"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Check resource status"""
    
    try:
        request = InfrastructureRequest(
            operation=OperationType.STATUS,
            target_resource=resource_name,
            cloud_provider=provider,
            dry_run=True
        )
    except ValidationError as e:
        typer.echo(f"❌ Invalid request: {e}", err=True)
        raise typer.Exit(1)
    
    metadata = SkillMetadata(
        skill_name="infrastructure-provisioning",
        risk_level=RiskLevel.LOW,
        autonomy=AutonomyLevel.FULLY_AUTO,
        execution_id=f"status-{resource_name}-{int(os.times()[4])}"
    )
    
    try:
        orchestrator = MultiCloudOrchestrator(config_file)
        result = execute_status_check(orchestrator, request, metadata, verbose)
        
        typer.echo(f"📊 Resource Status: {result.status}")
        if result.data:
            typer.echo(f"   Details: {json.dumps(result.data, indent=2)}")
        
    except Exception as e:
        typer.echo(f"❌ Status check failed: {e}", err=True)
        raise typer.Exit(1)


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load config file {config_file}: {e}")


def execute_provisioning(
    orchestrator: MultiCloudOrchestrator,
    request: InfrastructureRequest,
    metadata: SkillMetadata,
    verbose: bool
) -> InfrastructureResult:
    """Execute infrastructure provisioning"""
    
    if verbose:
        typer.echo(f"🚀 Starting provisioning with execution ID: {metadata.execution_id}")
    
    # Create orchestration tasks
    agents = [
        {
            'name': request.target_resource,
            'provider': request.cloud_provider.value,
            'resource_type': request.parameters['resource_type'],
            'region': request.parameters['region'],
            'configuration': request.parameters['configuration'],
            'tags': request.parameters['tags']
        }
    ]
    
    tasks = orchestrator.create_deployment_plan(agents)
    
    if verbose:
        typer.echo(f"📋 Created {len(tasks)} orchestration tasks")
    
    # Execute tasks
    results = orchestrator.execute_tasks(tasks)
    
    # Create result
    success_count = sum(1 for r in results if r.status == 'success')
    result = InfrastructureResult(
        operation_id=metadata.execution_id,
        operation=request.operation,
        status='success' if success_count == len(tasks) else 'partial' if success_count > 0 else 'failed',
        message=f"Provisioned {success_count}/{len(tasks)} resources successfully",
        cloud_provider=request.cloud_provider,
        environment=request.environment,
        resource_type=request.parameters['resource_type']
    )
    
    # Extract resource details from successful results
    for r in results:
        if r.status == 'success' and r.data:
            result.resource_id = r.data.get('resource_id')
            result.configuration = r.data.get('configuration')
            result.cost_estimate = r.data.get('cost_estimate')
            break
    
    return result


def execute_status_check(
    orchestrator: MultiCloudOrchestrator,
    request: InfrastructureRequest,
    metadata: SkillMetadata,
    verbose: bool
) -> InfrastructureResult:
    """Execute status check"""
    
    if verbose:
        typer.echo(f"🔍 Checking status with execution ID: {metadata.execution_id}")
    
    # This would implement actual status checking logic
    # For now, return a mock result
    result = InfrastructureResult(
        operation_id=metadata.execution_id,
        operation=request.operation,
        status='success',
        message=f"Status check completed for {request.target_resource}",
        cloud_provider=request.cloud_provider,
        environment=request.environment,
        resource_type='unknown',
        data={'status': 'running', 'health': 'healthy'}
    )
    
    return result


if __name__ == "__main__":
    app()
