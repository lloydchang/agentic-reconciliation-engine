#!/usr/bin/env python3
"""
Resource Optimizer Agent - Main Entry Point

This is the main entry point for the resource optimizer agent skill.
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
#   "pandas>=1.5.0",
#   "numpy>=1.24.0",
#   "typer>=0.7.0"
# ]
# ///

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

# Add shared models to path
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

try:
    import typer
    from pydantic import ValidationError
    from models import (
        OptimizationRequest, OptimizationResult,
        CloudProvider, OperationType, Environment,
        SkillMetadata, RiskLevel, AutonomyLevel
    )
    from multi_cloud_orchestrator import MultiCloudOrchestrator
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install with: pip install -e .")
    sys.exit(1)

app = typer.Typer(
    name="resource-optimizer",
    help="Multi-Cloud Resource Optimization Agent",
    no_args_is_help=True
)


@app.command()
def analyze(
    resource_type: str = typer.Option("all", "--type", "-t", help="Resource type to analyze (all, compute, storage, network, database)"),
    provider: CloudProvider = typer.Option(CloudProvider.ALL, "--provider", "-p", help="Cloud provider"),
    environment: Environment = typer.Option(Environment.PRODUCTION, "--env", "-e", help="Target environment"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file"),
    optimization_type: str = typer.Option("cost", "--optimization", "-o", help="Optimization type (cost, performance, security)"),
    savings_target: Optional[float] = typer.Option(None, "--savings-target", help="Target savings percentage"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Analyze resource utilization and generate optimization recommendations"""
    
    # Create request
    try:
        request = OptimizationRequest(
            operation=OperationType.OPTIMIZE,
            target_resource=f"{resource_type}-analysis",
            cloud_provider=provider,
            environment=environment,
            dry_run=False,
            parameters={
                "resource_type": resource_type,
                "optimization_type": optimization_type,
                "savings_target": savings_target,
                "analysis_type": "utilization"
            },
            optimization_type=optimization_type,
            savings_target=savings_target
        )
    except ValidationError as e:
        typer.echo(f"❌ Invalid request: {e}", err=True)
        raise typer.Exit(1)
    
    if verbose:
        typer.echo(f"📊 Resource optimization analysis:")
        typer.echo(f"   Resource Type: {resource_type}")
        typer.echo(f"   Provider: {provider.value}")
        typer.echo(f"   Environment: {environment.value}")
        typer.echo(f"   Optimization Type: {optimization_type}")
        if savings_target:
            typer.echo(f"   Savings Target: {savings_target}%")
    
    # Create metadata
    metadata = SkillMetadata(
        skill_name="resource-optimizer",
        risk_level=RiskLevel.LOW,
        autonomy=AutonomyLevel.CONDITIONAL,
        execution_id=f"opt-{resource_type}-{int(os.times()[4])}"
    )
    
    # Execute analysis
    try:
        orchestrator = MultiCloudOrchestrator(config_file)
        result = execute_optimization_analysis(orchestrator, request, metadata, verbose)
        
        typer.echo(f"✅ Optimization analysis completed: {result.status}")
        if result.estimated_savings:
            typer.echo(f"   Estimated Savings: ${result.estimated_savings:.2f}/month")
        if result.recommendations:
            typer.echo(f"   Recommendations: {len(result.recommendations)}")
            for rec in result.recommendations[:3]:
                typer.echo(f"     - {rec.get('action', 'unknown')}: {rec.get('savings', 'N/A')} savings")
        
    except Exception as e:
        typer.echo(f"❌ Optimization analysis failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def optimize(
    resource_ids: List[str] = typer.Argument(..., help="Resource IDs to optimize"),
    provider: CloudProvider = typer.Option(CloudProvider.ALL, "--provider", "-p", help="Cloud provider"),
    optimization_type: str = typer.Option("cost", "--optimization", "-o", help="Optimization type (cost, performance, security)"),
    auto_apply: bool = typer.Option(False, "--apply", help="Automatically apply optimizations"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Dry run mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Apply resource optimizations to specific resources"""
    
    try:
        request = OptimizationRequest(
            operation=OperationType.OPTIMIZE,
            target_resource="specific-resources",
            cloud_provider=provider,
            dry_run=dry_run,
            parameters={
                "resource_ids": resource_ids,
                "optimization_type": optimization_type,
                "auto_apply": auto_apply
            },
            optimization_type=optimization_type
        )
    except ValidationError as e:
        typer.echo(f"❌ Invalid request: {e}", err=True)
        raise typer.Exit(1)
    
    if verbose:
        typer.echo(f"🚀 Resource optimization:")
        typer.echo(f"   Resources: {', '.join(resource_ids)}")
        typer.echo(f"   Provider: {provider.value}")
        typer.echo(f"   Optimization Type: {optimization_type}")
        typer.echo(f"   Auto Apply: {auto_apply}")
        typer.echo(f"   Dry Run: {dry_run}")
    
    metadata = SkillMetadata(
        skill_name="resource-optimizer",
        risk_level=RiskLevel.MEDIUM,
        autonomy=AutonomyLevel.CONDITIONAL,
        execution_id=f"opt-apply-{int(os.times()[4])}"
    )
    
    try:
        orchestrator = MultiCloudOrchestrator(config_file)
        result = execute_optimization(orchestrator, request, metadata, verbose)
        
        typer.echo(f"✅ Optimization completed: {result.status}")
        if result.actual_savings:
            typer.echo(f"   Actual Savings: ${result.actual_savings:.2f}/month")
        if result.recommendations:
            typer.echo(f"   Applied Optimizations: {len(result.recommendations)}")
        
    except Exception as e:
        typer.echo(f"❌ Optimization failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def report(
    provider: CloudProvider = typer.Option(CloudProvider.ALL, "--provider", "-p", help="Cloud provider"),
    environment: Environment = typer.Option(Environment.PRODUCTION, "--env", "-e", help="Target environment"),
    time_range: str = typer.Option("7d", "--range", "-r", help="Time range for report (1d, 7d, 30d)"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json, csv)"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Generate resource optimization report"""
    
    try:
        request = OptimizationRequest(
            operation=OperationType.OPTIMIZE,
            target_resource="optimization-report",
            cloud_provider=provider,
            environment=environment,
            dry_run=True,
            parameters={
                "report_type": "summary",
                "time_range": time_range,
                "output_format": output_format
            },
            optimization_type="cost"
        )
    except ValidationError as e:
        typer.echo(f"❌ Invalid request: {e}", err=True)
        raise typer.Exit(1)
    
    if verbose:
        typer.echo(f"📋 Generating optimization report:")
        typer.echo(f"   Provider: {provider.value}")
        typer.echo(f"   Environment: {environment.value}")
        typer.echo(f"   Time Range: {time_range}")
        typer.echo(f"   Format: {output_format}")
    
    metadata = SkillMetadata(
        skill_name="resource-optimizer",
        risk_level=RiskLevel.LOW,
        autonomy=AutonomyLevel.FULLY_AUTO,
        execution_id=f"report-{int(os.times()[4])}"
    )
    
    try:
        orchestrator = MultiCloudOrchestrator(config_file)
        result = generate_report(orchestrator, request, metadata, verbose)
        
        typer.echo(f"✅ Report generated: {result.status}")
        if result.data and 'summary' in result.data:
            summary = result.data['summary']
            typer.echo(f"   Total Resources: {summary.get('total_resources', 0)}")
            typer.echo(f"   Potential Savings: ${summary.get('potential_savings', 0):.2f}/month")
            typer.echo(f"   Optimization Opportunities: {summary.get('opportunities', 0)}")
        
    except Exception as e:
        typer.echo(f"❌ Report generation failed: {e}", err=True)
        raise typer.Exit(1)


def execute_optimization_analysis(
    orchestrator: MultiCloudOrchestrator,
    request: OptimizationRequest,
    metadata: SkillMetadata,
    verbose: bool
) -> OptimizationResult:
    """Execute resource optimization analysis"""
    
    if verbose:
        typer.echo(f"🔍 Starting optimization analysis with execution ID: {metadata.execution_id}")
    
    # Create analysis tasks
    resource_type = request.parameters.get('resource_type', 'all')
    
    if resource_type == 'all':
        analysis_types = ['compute', 'storage', 'network', 'database']
    else:
        analysis_types = [resource_type]
    
    agents = []
    for i, analysis_type in enumerate(analysis_types):
        agents.append({
            'name': f"{analysis_type}-analysis",
            'provider': request.cloud_provider.value,
            'analysis_type': analysis_type,
            'optimization_type': request.parameters.get('optimization_type', 'cost'),
            'savings_target': request.parameters.get('savings_target')
        })
    
    tasks = orchestrator.create_deployment_plan(agents)
    
    if verbose:
        typer.echo(f"📋 Created {len(tasks)} analysis tasks")
    
    # Execute analysis
    results = orchestrator.execute_tasks(tasks)
    
    # Aggregate results
    recommendations = []
    total_savings = 0.0
    
    for result in results:
        if result.data and 'recommendations' in result.data:
            recommendations.extend(result.data['recommendations'])
        if result.data and 'estimated_savings' in result.data:
            total_savings += result.data['estimated_savings']
    
    # Create result
    success_count = sum(1 for r in results if r.status == 'success')
    result = OptimizationResult(
        operation_id=metadata.execution_id,
        operation=request.operation,
        status='success' if success_count == len(tasks) else 'partial' if success_count > 0 else 'failed',
        message=f"Analysis completed: {success_count}/{len(tasks)} analyses successful",
        cloud_provider=request.cloud_provider,
        environment=request.environment,
        optimization_type=request.parameters.get('optimization_type', 'cost'),
        estimated_savings=total_savings,
        recommendations=recommendations,
        data={
            'analysis_results': [
                {
                    'analysis_type': r.parameters.get('analysis_type', 'unknown'),
                    'status': r.status,
                    'message': r.message
                }
                for r in results
            ]
        }
    )
    
    return result


def execute_optimization(
    orchestrator: MultiCloudOrchestrator,
    request: OptimizationRequest,
    metadata: SkillMetadata,
    verbose: bool
) -> OptimizationResult:
    """Execute resource optimizations"""
    
    if verbose:
        typer.echo(f"🚀 Starting optimization with execution ID: {metadata.execution_id}")
    
    # Create optimization tasks
    resource_ids = request.parameters.get('resource_ids', [])
    
    agents = []
    for i, resource_id in enumerate(resource_ids):
        agents.append({
            'name': f"optimize-{resource_id}",
            'provider': request.cloud_provider.value,
            'resource_id': resource_id,
            'optimization_type': request.parameters.get('optimization_type', 'cost'),
            'auto_apply': request.parameters.get('auto_apply', False)
        })
    
    tasks = orchestrator.create_deployment_plan(agents)
    
    if verbose:
        typer.echo(f"📋 Created {len(tasks)} optimization tasks")
    
    # Execute optimizations
    results = orchestrator.execute_tasks(tasks)
    
    # Aggregate results
    recommendations = []
    actual_savings = 0.0
    
    for result in results:
        if result.data and 'applied_optimizations' in result.data:
            recommendations.extend(result.data['applied_optimizations'])
        if result.data and 'actual_savings' in result.data:
            actual_savings += result.data['actual_savings']
    
    # Create result
    success_count = sum(1 for r in results if r.status == 'success')
    result = OptimizationResult(
        operation_id=metadata.execution_id,
        operation=request.operation,
        status='success' if success_count == len(tasks) else 'partial' if success_count > 0 else 'failed',
        message=f"Optimization completed: {success_count}/{len(tasks)} optimizations successful",
        cloud_provider=request.cloud_provider,
        environment=request.environment,
        optimization_type=request.parameters.get('optimization_type', 'cost'),
        actual_savings=actual_savings,
        recommendations=recommendations,
        data={
            'optimization_results': [
                {
                    'resource_id': r.parameters.get('resource_id', 'unknown'),
                    'status': r.status,
                    'message': r.message
                }
                for r in results
            ]
        }
    )
    
    return result


def generate_report(
    orchestrator: MultiCloudOrchestrator,
    request: OptimizationRequest,
    metadata: SkillMetadata,
    verbose: bool
) -> OptimizationResult:
    """Generate optimization report"""
    
    if verbose:
        typer.echo(f"📋 Generating report with execution ID: {metadata.execution_id}")
    
    # This would implement actual report generation logic
    # For now, return a mock result
    result = OptimizationResult(
        operation_id=metadata.execution_id,
        operation=request.operation,
        status='success',
        message=f"Report generated for {request.cloud_provider.value}",
        cloud_provider=request.cloud_provider,
        environment=request.environment,
        optimization_type=request.parameters.get('optimization_type', 'cost'),
        data={
            'summary': {
                'total_resources': 150,
                'potential_savings': 1250.50,
                'opportunities': 23,
                'time_range': request.parameters.get('time_range', '7d')
            },
            'recommendations': [
                {
                    'resource_type': 'compute',
                    'action': 'rightsize_instances',
                    'savings': 450.25,
                    'confidence': 0.85
                },
                {
                    'resource_type': 'storage',
                    'action': 'optimize_storage_classes',
                    'savings': 320.75,
                    'confidence': 0.92
                }
            ]
        }
    )
    
    return result


if __name__ == "__main__":
    app()
