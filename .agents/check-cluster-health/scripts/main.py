#!/usr/bin/env python3
"""
Cluster Health Check Agent - Main Entry Point

This is the main entry point for the cluster health check agent skill.
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
#   "prometheus-client>=0.15.0",
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
        HealthCheckRequest, HealthCheckResult,
        CloudProvider, OperationType, Environment,
        SkillMetadata, RiskLevel, AutonomyLevel
    )
    from multi_cloud_orchestrator import MultiCloudOrchestrator
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install with: pip install -e .")
    sys.exit(1)

app = typer.Typer(
    name="cluster-health-check",
    help="Multi-Cloud Cluster Health Check Agent",
    no_args_is_help=True
)


@app.command()
def check(
    cluster_name: str = typer.Argument(..., help="Cluster name to check"),
    provider: CloudProvider = typer.Option(CloudProvider.ALL, "--provider", "-p", help="Cloud provider"),
    check_types: Optional[str] = typer.Option("node,pod,network", "--checks", help="Health check types, comma-separated"),
    environment: Environment = typer.Option(Environment.PRODUCTION, "--env", "-e", help="Target environment"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file"),
    severity: str = typer.Option("warning", "--severity", help="Minimum severity to report"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Perform cluster health checks"""
    
    # Parse check types
    check_list = [c.strip() for c in check_types.split(',')] if check_types else ["node", "pod", "network"]
    
    # Create request
    try:
        request = HealthCheckRequest(
            operation=OperationType.HEALTH_CHECK,
            target_resource=cluster_name,
            cloud_provider=provider,
            environment=environment,
            dry_run=False,
            parameters={
                "cluster_name": cluster_name,
                "check_types": check_list,
                "severity_threshold": severity
            },
            check_types=check_list,
            cluster_name=cluster_name,
            severity_threshold=severity
        )
    except ValidationError as e:
        typer.echo(f"❌ Invalid request: {e}", err=True)
        raise typer.Exit(1)
    
    if verbose:
        typer.echo(f"🏥 Health check request:")
        typer.echo(f"   Cluster: {cluster_name}")
        typer.echo(f"   Provider: {provider.value}")
        typer.echo(f"   Check Types: {check_list}")
        typer.echo(f"   Environment: {environment.value}")
        typer.echo(f"   Severity Threshold: {severity}")
    
    # Create metadata
    metadata = SkillMetadata(
        skill_name="cluster-health-check",
        risk_level=RiskLevel.LOW,
        autonomy=AutonomyLevel.FULLY_AUTO,
        execution_id=f"health-{cluster_name}-{int(os.times()[4])}"
    )
    
    # Execute health check
    try:
        orchestrator = MultiCloudOrchestrator(config_file)
        result = execute_health_check(orchestrator, request, metadata, verbose)
        
        typer.echo(f"🏥 Health check completed: {result.status}")
        if result.health_score is not None:
            typer.echo(f"   Health Score: {result.health_score}/100")
        if result.issues:
            typer.echo(f"   Issues Found: {len(result.issues)}")
            for issue in result.issues[:5]:  # Show first 5 issues
                typer.echo(f"     - {issue.get('type', 'unknown')}: {issue.get('message', 'no message')}")
        if result.recommendations:
            typer.echo(f"   Recommendations: {len(result.recommendations)}")
            for rec in result.recommendations[:3]:  # Show first 3 recommendations
                typer.echo(f"     - {rec}")
        
    except Exception as e:
        typer.echo(f"❌ Health check failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def monitor(
    cluster_name: str = typer.Argument(..., help="Cluster name to monitor"),
    provider: CloudProvider = typer.Option(CloudProvider.ALL, "--provider", "-p", help="Cloud provider"),
    interval: int = typer.Option(300, "--interval", "-i", help="Monitoring interval in seconds"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Continuous cluster monitoring"""
    
    try:
        request = HealthCheckRequest(
            operation=OperationType.HEALTH_CHECK,
            target_resource=cluster_name,
            cloud_provider=provider,
            dry_run=False,
            parameters={
                "cluster_name": cluster_name,
                "monitoring": True,
                "interval": interval
            }
        )
    except ValidationError as e:
        typer.echo(f"❌ Invalid request: {e}", err=True)
        raise typer.Exit(1)
    
    metadata = SkillMetadata(
        skill_name="cluster-health-check",
        risk_level=RiskLevel.LOW,
        autonomy=AutonomyLevel.FULLY_AUTO,
        execution_id=f"monitor-{cluster_name}-{int(os.times()[4])}"
    )
    
    typer.echo(f"📊 Starting continuous monitoring for {cluster_name}")
    typer.echo(f"   Interval: {interval} seconds")
    typer.echo(f"   Press Ctrl+C to stop")
    
    try:
        orchestrator = MultiCloudOrchestrator(config_file)
        
        import time
        while True:
            result = execute_health_check(orchestrator, request, metadata, verbose)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_emoji = "✅" if result.health_score and result.health_score >= 80 else "⚠️" if result.health_score and result.health_score >= 60 else "❌"
            
            typer.echo(f"{timestamp} {status_emoji} Score: {result.health_score or 'N/A'}/100 | Issues: {len(result.issues)}")
            
            if verbose and result.issues:
                for issue in result.issues[:2]:
                    typer.echo(f"     - {issue.get('type', 'unknown')}: {issue.get('message', 'no message')}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        typer.echo(f"\n📊 Monitoring stopped for {cluster_name}")
    except Exception as e:
        typer.echo(f"❌ Monitoring failed: {e}", err=True)
        raise typer.Exit(1)


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load config file {config_file}: {e}")


def execute_health_check(
    orchestrator: MultiCloudOrchestrator,
    request: HealthCheckRequest,
    metadata: SkillMetadata,
    verbose: bool
) -> HealthCheckResult:
    """Execute cluster health check"""
    
    if verbose:
        typer.echo(f"🔍 Starting health check with execution ID: {metadata.execution_id}")
    
    # Create orchestration tasks for each check type
    agents = []
    for i, check_type in enumerate(request.check_types):
        agents.append({
            'name': f"{request.cluster_name}-{check_type}",
            'provider': request.cloud_provider.value,
            'cluster_name': request.cluster_name,
            'check_type': check_type,
            'severity_threshold': request.severity_threshold
        })
    
    tasks = orchestrator.create_deployment_plan(agents)
    
    if verbose:
        typer.echo(f"📋 Created {len(tasks)} health check tasks")
    
    # Execute tasks
    results = orchestrator.execute_tasks(tasks)
    
    # Aggregate results
    issues = []
    recommendations = []
    health_scores = []
    
    for result in results:
        if result.data:
            if 'issues' in result.data:
                issues.extend(result.data['issues'])
            if 'recommendations' in result.data:
                recommendations.extend(result.data['recommendations'])
            if 'health_score' in result.data:
                health_scores.append(result.data['health_score'])
    
    # Calculate overall health score
    overall_score = sum(health_scores) / len(health_scores) if health_scores else None
    
    # Create result
    success_count = sum(1 for r in results if r.status == 'success')
    result = HealthCheckResult(
        operation_id=metadata.execution_id,
        operation=request.operation,
        status='success' if success_count == len(tasks) else 'partial' if success_count > 0 else 'failed',
        message=f"Health check completed: {success_count}/{len(tasks)} checks successful",
        cloud_provider=request.cloud_provider,
        environment=request.environment,
        cluster_name=request.cluster_name,
        health_score=overall_score,
        issues=issues,
        recommendations=recommendations,
        data={
            'check_results': [
                {
                    'check_type': r.parameters.get('check_type', 'unknown'),
                    'status': r.status,
                    'message': r.message
                }
                for r in results
            ]
        }
    )
    
    return result


def datetime():
    """Get current datetime (imported here to avoid circular imports)"""
    from datetime import datetime
    return datetime.now()


if __name__ == "__main__":
    app()
