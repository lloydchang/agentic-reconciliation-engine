#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.28.0",
#   "kubernetes>=25.0.0",
#   "pydantic>=1.10.0",
#   "click>=8.0.0",
#   "rich>=12.0.0",
#   "temporalio>=1.0.0"
# ]
# ///

import json
import time
import uuid
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import click
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class DebugSession(BaseModel):
    session_id: str
    start_time: datetime
    target_component: str
    issue_type: str
    time_range: str
    namespace: str
    verbose: bool
    auto_fix: bool

class DebugFinding(BaseModel):
    component: str
    severity: str
    issue: str
    root_cause: str
    evidence: List[str]
    recommendations: List[str]

class DebugResult(BaseModel):
    debug_session_id: str
    findings: List[DebugFinding]
    metrics_summary: Dict[str, int]
    execution_time: float
    next_steps: List[str]

class AISystemDebugger:
    def __init__(self, namespace: str = "temporal", verbose: bool = False):
        self.namespace = namespace
        self.verbose = verbose
        self.console = Console()
        self.session = None
        self.findings = []
        
    def log(self, message: str, level: str = "info"):
        """Enhanced logging with rich formatting"""
        if self.verbose or level in ["error", "warning", "critical"]:
            if level == "error":
                self.console.print(f"[red]ERROR: {message}[/red]")
            elif level == "warning":
                self.console.print(f"[yellow]WARNING: {message}[/yellow]")
            elif level == "critical":
                self.console.print(f"[bold red]CRITICAL: {message}[/bold red]")
            else:
                self.console.print(f"[blue]INFO: {message}[/blue]")
    
    def run_kubectl(self, command: str) -> str:
        """Execute kubectl command and return output"""
        try:
            full_command = f"kubectl {command} -n {self.namespace}"
            if self.verbose:
                self.log(f"Running: {full_command}")
            result = subprocess.run(full_command.split(), capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.log(f"kubectl command failed: {result.stderr}", "error")
                return ""
            return result.stdout
        except subprocess.TimeoutExpired:
            self.log(f"kubectl command timed out: {command}", "error")
            return ""
        except Exception as e:
            self.log(f"kubectl command error: {e}", "error")
            return ""
    
    def check_api_endpoint(self, endpoint: str) -> Optional[Dict]:
        """Check API endpoint availability and return data"""
        try:
            # Try to reach the monitoring endpoint
            url = f"http://temporal-worker.{self.namespace}.svc.cluster.local:8080{endpoint}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"API endpoint {endpoint} returned {response.status_code}", "warning")
                return None
        except requests.exceptions.RequestException as e:
            self.log(f"Failed to reach API endpoint {endpoint}: {e}", "warning")
            return None
    
    def debug_agents(self, issue_type: str, time_range: str) -> List[DebugFinding]:
        """Debug AI agents"""
        findings = []
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console) as progress:
            task = progress.add_task("Analyzing AI agents...", total=None)
            
            # Check agent pod status
            pods_output = self.run_kubectl("get pods -l app=temporal-worker -o json")
            if pods_output:
                try:
                    pods_data = json.loads(pods_output)
                    for pod in pods_data.get("items", []):
                        pod_name = pod["metadata"]["name"]
                        pod_status = pod["status"]["phase"]
                        
                        if pod_status != "Running":
                            findings.append(DebugFinding(
                                component="agents",
                                severity="critical",
                                issue=f"Agent pod {pod_name} is {pod_status}",
                                root_cause="Pod lifecycle issue",
                                evidence=[f"Pod status: {pod_status}"],
                                recommendations=[f"Check pod logs: kubectl logs {pod_name}", "Restart pod if necessary"]
                            ))
                        
                        # Check for restarts
                        restart_count = sum(container.get("restartCount", 0) 
                                        for container in pod.get("status", {}).get("containerStatuses", []))
                        if restart_count > 3:
                            findings.append(DebugFinding(
                                component="agents",
                                severity="warning",
                                issue=f"Agent pod {pod_name} has restarted {restart_count} times",
                                root_cause="Container instability or resource issues",
                                evidence=[f"Restart count: {restart_count}"],
                                recommendations=["Check memory/CPU limits", "Review application logs for crashes"]
                            ))
                except json.JSONDecodeError as e:
                    self.log(f"Failed to parse pod JSON: {e}", "error")
            
            # Check agent metrics
            metrics_data = self.check_api_endpoint("/monitoring/metrics")
            if metrics_data:
                for metric_name, metric in metrics_data.get("metrics", {}).items():
                    if "agent" in metric_name.lower():
                        if "error_rate" in metric_name.lower() and metric.get("value", 0) > 0.1:
                            findings.append(DebugFinding(
                                component="agents",
                                severity="critical",
                                issue=f"High agent error rate: {metric['value']:.2%}",
                                root_cause="Agent execution failures",
                                evidence=[f"Metric {metric_name}: {metric['value']}"],
                                recommendations["Check agent execution logs", "Review skill configurations"]
                            ))
            
            # Check recent agent logs for errors
            logs_output = self.run_kubectl("logs deployment/temporal-worker --since=1h --tail=50")
            if logs_output and "ERROR" in logs_output:
                error_lines = [line for line in logs_output.split('\n') if "ERROR" in line]
                findings.append(DebugFinding(
                    component="agents",
                    severity="warning",
                    issue=f"Found {len(error_lines)} error messages in agent logs",
                    root_cause="Agent execution errors",
                    evidence=error_lines[:3],  # First 3 errors
                    recommendations=["Review full agent logs", "Check skill configurations", "Monitor error patterns"]
                ))
            
            progress.update(task, description="Agent analysis complete")
        
        return findings
    
    def debug_workflows(self, issue_type: str, time_range: str) -> List[DebugFinding]:
        """Debug Temporal workflows"""
        findings = []
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console) as progress:
            task = progress.add_task("Analyzing workflows...", total=None)
            
            # Check Temporal server status
            server_pods = self.run_kubectl("get pods -l app=temporal-server -o json")
            if server_pods:
                try:
                    pods_data = json.loads(server_pods)
                    if not pods_data.get("items"):
                        findings.append(DebugFinding(
                            component="workflows",
                            severity="critical",
                            issue="Temporal server pods not found",
                            root_cause="Temporal server deployment issue",
                            evidence=["No pods with label app=temporal-server"],
                            recommendations["Check temporal-server deployment", "Verify namespace configuration"]
                        ))
                except json.JSONDecodeError:
                    pass
            
            # Check workflow metrics
            metrics_data = self.check_api_endpoint("/monitoring/metrics")
            if metrics_data:
                for metric_name, metric in metrics_data.get("metrics", {}).items():
                    if "workflow" in metric_name.lower():
                        if "duration" in metric_name.lower() and metric.get("value", 0) > 3600:  # 1 hour
                            findings.append(DebugFinding(
                                component="workflows",
                                severity="warning",
                                issue=f"Long workflow duration: {metric['value']:.0f} seconds",
                                root_cause="Workflow performance issue",
                                evidence=[f"Metric {metric_name}: {metric['value']}"],
                                recommendations["Optimize workflow logic", "Check for infinite loops", "Review activity timeouts"]
                            ))
            
            progress.update(task, description="Workflow analysis complete")
        
        return findings
    
    def debug_infrastructure(self, issue_type: str, time_range: str) -> List[DebugFinding]:
        """Debug Kubernetes infrastructure"""
        findings = []
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console) as progress:
            task = progress.add_task("Analyzing infrastructure...", total=None)
            
            # Check node status
            nodes_output = self.run_kubectl("get nodes --no-headers")
            if nodes_output:
                node_lines = nodes_output.strip().split('\n')
                for line in node_lines:
                    if "NotReady" in line:
                        node_name = line.split()[0]
                        findings.append(DebugFinding(
                            component="infrastructure",
                            severity="critical",
                            issue=f"Node {node_name} is not ready",
                            root_cause="Node health issue",
                            evidence=[f"Node status: {line}"],
                            recommendations["Check node status", "Verify kubelet service", "Review resource utilization"]
                        ))
            
            # Check resource utilization
            top_output = self.run_kubectl("top pods --no-headers")
            if top_output:
                lines = top_output.strip().split('\n')
                for line in lines:
                    if len(line.split()) >= 3:
                        pod_name = line.split()[0]
                        cpu = line.split()[1]
                        memory = line.split()[2]
                        
                        # Check for high CPU usage
                        if "m" in cpu and int(cpu.replace("m", "")) > 1000:  # > 1 CPU core
                            findings.append(DebugFinding(
                                component="infrastructure",
                                severity="warning",
                                issue=f"High CPU usage for pod {pod_name}: {cpu}",
                                root_cause="Resource intensive process",
                                evidence=[f"CPU usage: {cpu}"],
                                recommendations["Optimize application", "Scale horizontally", "Review resource limits"]
                            ))
            
            # Check storage
            pv_output = self.run_kubectl("get pv --no-headers")
            if pv_output:
                lines = pv_output.strip().split('\n')
                for line in lines:
                    if "Failed" in line:
                        findings.append(DebugFinding(
                            component="infrastructure",
                            severity="critical",
                            issue="PersistentVolume failure detected",
                            root_cause="Storage system issue",
                            evidence=[f"PV status: {line}"],
                            recommendations["Check storage class", "Verify storage backend", "Review PV configuration"]
                        ))
            
            progress.update(task, description="Infrastructure analysis complete")
        
        return findings
    
    def apply_auto_fixes(self, findings: List[DebugFinding]) -> int:
        """Apply automatic fixes for common issues"""
        fixes_applied = 0
        
        if not self.session.auto_fix:
            return fixes_applied
        
        for finding in findings:
            if finding.severity == "critical" and "pod" in finding.component.lower():
                if "restart" in finding.recommendations[0].lower():
                    pod_name = finding.evidence[0].split()[-1] if finding.evidence else ""
                    if pod_name:
                        self.log(f"Attempting to restart pod: {pod_name}")
                        result = self.run_kubectl(f"delete pod {pod_name}")
                        if result:
                            fixes_applied += 1
                            self.log(f"Successfully initiated restart for pod: {pod_name}")
        
        return fixes_applied
    
    def debug(self, target_component: str, issue_type: str, time_range: str, 
              namespace: str, verbose: bool, auto_fix: bool) -> DebugResult:
        """Main debugging function"""
        start_time = time.time()
        
        # Initialize session
        self.session = DebugSession(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            target_component=target_component,
            issue_type=issue_type,
            time_range=time_range,
            namespace=namespace,
            verbose=verbose,
            auto_fix=auto_fix
        )
        
        self.namespace = namespace
        self.verbose = verbose
        
        self.console.print(Panel.fit(
            f"[bold blue]AI System Debugger[/bold blue]\n"
            f"Session: {self.session.session_id}\n"
            f"Target: {target_component} | Issue: {issue_type} | Range: {time_range}",
            title="Debug Session Started"
        ))
        
        # Collect findings based on target component
        if target_component in ["agents", "all"]:
            self.findings.extend(self.debug_agents(issue_type, time_range))
        
        if target_component in ["workflows", "all"]:
            self.findings.extend(self.debug_workflows(issue_type, time_range))
        
        if target_component in ["infrastructure", "all"]:
            self.findings.extend(self.debug_infrastructure(issue_type, time_range))
        
        # Apply auto-fixes if enabled
        fixes_applied = self.apply_auto_fixes(self.findings)
        
        # Generate metrics summary
        critical_issues = len([f for f in self.findings if f.severity == "critical"])
        warnings = len([f for f in self.findings if f.severity == "warning"])
        
        metrics_summary = {
            "total_issues": len(self.findings),
            "critical_issues": critical_issues,
            "warnings": warnings,
            "auto_fixes_applied": fixes_applied
        }
        
        # Generate next steps
        next_steps = []
        if critical_issues > 0:
            next_steps.append("Address critical issues immediately")
        if warnings > 0:
            next_steps.append("Review warnings during maintenance window")
        if auto_fix and fixes_applied > 0:
            next_steps.append("Monitor applied fixes for effectiveness")
        if not self.findings:
            next_steps.append("Continue monitoring system health")
        
        execution_time = time.time() - start_time
        
        # Create result
        result = DebugResult(
            debug_session_id=self.session.session_id,
            findings=self.findings,
            metrics_summary=metrics_summary,
            execution_time=execution_time,
            next_steps=next_steps
        )
        
        # Display results
        self.display_results(result)
        
        return result
    
    def display_results(self, result: DebugResult):
        """Display debugging results in a formatted way"""
        self.console.print("\n")
        
        # Summary table
        summary_table = Table(title="Debug Session Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        
        for key, value in result.metrics_summary.items():
            summary_table.add_row(key.replace("_", " ").title(), str(value))
        
        summary_table.add_row("Execution Time", f"{result.execution_time:.2f}s")
        self.console.print(summary_table)
        
        # Findings
        if result.findings:
            self.console.print("\n[bold red]Issues Found:[/bold red]")
            for i, finding in enumerate(result.findings, 1):
                severity_color = {
                    "critical": "red",
                    "warning": "yellow", 
                    "info": "blue"
                }.get(finding.severity, "white")
                
                panel_content = f"[bold]{finding.issue}[/bold]\n\n"
                panel_content += f"[dim]Component:[/dim] {finding.component}\n"
                panel_content += f"[dim]Root Cause:[/dim] {finding.root_cause}\n\n"
                
                if finding.evidence:
                    panel_content += "[dim]Evidence:[/dim]\n"
                    for evidence in finding.evidence[:2]:  # Show first 2
                        panel_content += f"  • {evidence}\n"
                
                if finding.recommendations:
                    panel_content += "\n[dim]Recommendations:[/dim]\n"
                    for rec in finding.recommendations[:2]:  # Show first 2
                        panel_content += f"  • {rec}\n"
                
                self.console.print(Panel(
                    panel_content,
                    title=f"[{severity_color}]{finding.severity.upper()}[/{severity_color}] #{i}",
                    border_style=severity_color
                ))
        else:
            self.console.print("[green]No issues found! System appears healthy.[/green]")
        
        # Next steps
        if result.next_steps:
            self.console.print("\n[bold blue]Next Steps:[/bold blue]")
            for step in result.next_steps:
                self.console.print(f"• {step}")
        
        # Session info
        self.console.print(f"\n[dim]Session ID: {result.debug_session_id}[/dim]")

@click.command()
@click.option('--target-component', '-t', 
              type=click.Choice(['agents', 'workflows', 'infrastructure', 'all']),
              required=True, help='Component to debug')
@click.option('--issue-type', '-i',
              type=click.Choice(['performance', 'errors', 'timeouts', 'connectivity', 'resource', 'behavior']),
              required=True, help='Type of issue to investigate')
@click.option('--time-range', '-r', default='1h', 
              help='Time range for analysis (e.g., 30m, 2h, 1d)')
@click.option('--namespace', '-n', default='temporal',
              help='Kubernetes namespace to investigate')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--auto-fix', '-a', is_flag=True, help='Attempt automatic fixes')
@click.option('--output', '-o', type=click.Path(), help='Save results to file')
def main(target_component, issue_type, time_range, namespace, verbose, auto_fix, output):
    """AI System Debugger - Comprehensive debugging for distributed AI agent systems"""
    
    debugger = AISystemDebugger(namespace=namespace, verbose=verbose)
    
    try:
        result = debugger.debug(
            target_component=target_component,
            issue_type=issue_type,
            time_range=time_range,
            namespace=namespace,
            verbose=verbose,
            auto_fix=auto_fix
        )
        
        # Save results if requested
        if output:
            with open(output, 'w') as f:
                json.dump(result.dict(), f, indent=2, default=str)
            debugger.console.print(f"\n[green]Results saved to: {output}[/green]")
        
        # Exit with error code if critical issues found
        if result.metrics_summary.get('critical_issues', 0) > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        debugger.console.print("\n[yellow]Debug session interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        debugger.console.print(f"\n[red]Debug session failed: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
