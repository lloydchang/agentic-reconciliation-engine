#!/usr/bin/env python3
"""
Runbook Executor Script
Converts alerts into structured runbook execution plans with safety validation.
"""

import json
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum


class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ExecutionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    APPROVAL_REQUIRED = "approval_required"


class RunbookStepType(Enum):
    VALIDATION = "validation"
    DIAGNOSTIC = "diagnostic"
    REMEDIATION = "remediation"
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    ESCALATION = "escalation"


class RunbookExecutor:
    def __init__(self, cluster_context: str = "default"):
        self.cluster_context = cluster_context
        self.execution_history = []
        self.approval_required_operations = [
            'delete', 'scale', 'restart', 'patch', 'apply'
        ]
        
    def analyze_alert(self, alert: Dict) -> Dict:
        """Analyze alert and determine appropriate runbook"""
        alert_type = alert.get('type', 'unknown')
        severity = AlertSeverity(alert.get('severity', 'medium'))
        service = alert.get('service', 'unknown')
        message = alert.get('message', '')
        
        # Determine runbook type
        runbook_type = self._determine_runbook_type(alert_type, service, message)
        
        # Get runbook template
        template = self._get_runbook_template(runbook_type, severity)
        
        # Customize template based on alert context
        customized_plan = self._customize_runbook(template, alert)
        
        return {
            'alert': alert,
            'runbook_type': runbook_type,
            'severity': severity.value,
            'plan': customized_plan,
            'estimated_duration': self._estimate_duration(customized_plan),
            'required_approvals': self._identify_required_approvals(customized_plan),
            'rollback_procedures': self._generate_rollback_plan(customized_plan)
        }
    
    def _determine_runbook_type(self, alert_type: str, service: str, message: str) -> str:
        """Determine the appropriate runbook type based on alert"""
        alert_patterns = {
            'pod_crash_loop_backoff': 'pod_failure',
            'image_pull_backoff': 'image_issue',
            'high_error_rate': 'application_error',
            'high_latency': 'performance_issue',
            'memory_pressure': 'resource_exhaustion',
            'cpu_pressure': 'resource_exhaustion',
            'disk_pressure': 'storage_issue',
            'node_not_ready': 'node_failure',
            'service_unavailable': 'network_issue',
            'deployment_failure': 'deployment_issue',
            'hpa_scaling': 'autoscaling_event'
        }
        
        # Check for specific patterns
        for pattern, runbook in alert_patterns.items():
            if pattern in alert_type.lower() or pattern in message.lower():
                return runbook
        
        # Service-specific patterns
        if 'database' in service.lower():
            if 'connection' in message.lower():
                return 'database_connectivity'
            elif 'slow' in message.lower():
                return 'database_performance'
        
        # Default patterns
        if 'critical' in alert_type.lower():
            return 'critical_incident'
        elif 'warning' in alert_type.lower():
            return 'warning_event'
        else:
            return 'general_troubleshooting'
    
    def _get_runbook_template(self, runbook_type: str, severity: AlertSeverity) -> Dict:
        """Get runbook template for the specified type"""
        templates = {
            'pod_failure': {
                'name': 'Pod Failure Troubleshooting',
                'steps': [
                    {'type': 'validation', 'name': 'Verify pod status', 'command': 'kubectl get pods'},
                    {'type': 'diagnostic', 'name': 'Check pod events', 'command': 'kubectl describe pod'},
                    {'type': 'diagnostic', 'name': 'Review pod logs', 'command': 'kubectl logs'},
                    {'type': 'remediation', 'name': 'Restart pod if needed', 'command': 'kubectl delete pod', 'approval': True},
                    {'type': 'verification', 'name': 'Verify pod recovery', 'command': 'kubectl get pods'}
                ]
            },
            'application_error': {
                'name': 'Application Error Response',
                'steps': [
                    {'type': 'validation', 'name': 'Check error rate', 'command': 'kubectl get pods'},
                    {'type': 'diagnostic', 'name': 'Review application logs', 'command': 'kubectl logs'},
                    {'type': 'diagnostic', 'name': 'Check recent deployments', 'command': 'kubectl rollout history'},
                    {'type': 'remediation', 'name': 'Rollback if needed', 'command': 'kubectl rollout undo', 'approval': True},
                    {'type': 'verification', 'name': 'Monitor error rate', 'command': 'kubectl top pods'}
                ]
            },
            'resource_exhaustion': {
                'name': 'Resource Exhaustion Response',
                'steps': [
                    {'type': 'validation', 'name': 'Check resource usage', 'command': 'kubectl top nodes'},
                    {'type': 'diagnostic', 'name': 'Check pod resource limits', 'command': 'kubectl describe pod'},
                    {'type': 'remediation', 'name': 'Scale resources if needed', 'command': 'kubectl scale deployment', 'approval': True},
                    {'type': 'verification', 'name': 'Monitor resource usage', 'command': 'kubectl top pods'}
                ]
            },
            'deployment_issue': {
                'name': 'Deployment Issue Resolution',
                'steps': [
                    {'type': 'validation', 'name': 'Check deployment status', 'command': 'kubectl get deployments'},
                    {'type': 'diagnostic', 'name': 'Review deployment events', 'command': 'kubectl describe deployment'},
                    {'type': 'diagnostic', 'name': 'Check deployment logs', 'command': 'kubectl logs deployment'},
                    {'type': 'remediation', 'name': 'Fix configuration', 'command': 'kubectl apply -f', 'approval': True},
                    {'type': 'verification', 'name': 'Verify deployment health', 'command': 'kubectl rollout status'}
                ]
            },
            'critical_incident': {
                'name': 'Critical Incident Response',
                'steps': [
                    {'type': 'validation', 'name': 'Assess incident scope', 'command': 'kubectl get all'},
                    {'type': 'notification', 'name': 'Notify on-call team', 'command': 'send_alert'},
                    {'type': 'diagnostic', 'name': 'Gather diagnostic data', 'command': 'collect_logs'},
                    {'type': 'escalation', 'name': 'Escalate if needed', 'command': 'escalate_incident'},
                    {'type': 'remediation', 'name': 'Execute recovery plan', 'command': 'execute_recovery', 'approval': True},
                    {'type': 'verification', 'name': 'Verify service recovery', 'command': 'health_check'}
                ]
            }
        }
        
        return templates.get(runbook_type, templates['pod_failure'])
    
    def _customize_runbook(self, template: Dict, alert: Dict) -> Dict:
        """Customize runbook template based on specific alert context"""
        customized = template.copy()
        service = alert.get('service', '')
        namespace = alert.get('namespace', 'default')
        
        # Customize commands with specific context
        for step in customized['steps']:
            if 'command' in step:
                # Add namespace context
                if 'kubectl' in step['command'] and '-n' not in step['command']:
                    step['command'] += f' -n {namespace}'
                
                # Add service context if applicable
                if service and '{service}' in step['command']:
                    step['command'] = step['command'].format(service=service)
        
        # Add alert-specific context
        customized['alert_context'] = {
            'service': service,
            'namespace': namespace,
            'alert_id': alert.get('id', 'unknown'),
            'severity': alert.get('severity', 'medium'),
            'timestamp': alert.get('timestamp', datetime.now().isoformat())
        }
        
        return customized
    
    def _estimate_duration(self, plan: Dict) -> Dict:
        """Estimate execution duration for the runbook"""
        step_durations = {
            RunbookStepType.VALIDATION: 30,  # seconds
            RunbookStepType.DIAGNOSTIC: 120,
            RunbookStepType.REMEDIATION: 180,
            RunbookStepType.VERIFICATION: 60,
            RunbookStepType.NOTIFICATION: 30,
            RunbookStepType.ESCALATION: 60
        }
        
        total_duration = 0
        for step in plan.get('steps', []):
            step_type = RunbookStepType(step.get('type', 'diagnostic'))
            total_duration += step_durations.get(step_type, 60)
        
        return {
            'estimated_seconds': total_duration,
            'estimated_minutes': round(total_duration / 60, 1),
            'confidence': 'medium'  # Could be calculated based on historical data
        }
    
    def _identify_required_approvals(self, plan: Dict) -> List[str]:
        """Identify steps that require approval"""
        approval_steps = []
        
        for i, step in enumerate(plan.get('steps', [])):
            if step.get('approval', False):
                approval_steps.append({
                    'step_number': i + 1,
                    'step_name': step.get('name', 'Unknown'),
                    'command': step.get('command', ''),
                    'reason': 'Destructive operation requires approval'
                })
        
        return approval_steps
    
    def _generate_rollback_plan(self, plan: Dict) -> Dict:
        """Generate rollback procedures for the runbook"""
        rollback_steps = []
        
        # Generate rollback for each remediation step
        for step in plan.get('steps', []):
            if step.get('type') == 'remediation':
                command = step.get('command', '')
                
                # Generate specific rollback commands
                if 'delete pod' in command:
                    rollback_steps.append({
                        'step': f'Restore deleted pods from {step.get("name", "remediation")}',
                        'command': 'kubectl get pods -o yaml > backup.yaml',
                        'notes': 'Restore from backup if needed'
                    })
                elif 'scale' in command:
                    rollback_steps.append({
                        'step': f'Rescale from {step.get("name", "remediation")}',
                        'command': 'kubectl scale deployment --replicas=original',
                        'notes': 'Scale back to original replica count'
                    })
                elif 'rollout undo' in command:
                    rollback_steps.append({
                        'step': f'Re-apply deployment from {step.get("name", "remediation")}',
                        'command': 'kubectl rollout undo deployment --to-revision=previous',
                        'notes': 'Rollback to previous deployment'
                    })
        
        return {
            'steps': rollback_steps,
            'procedure': 'Execute rollback steps in reverse order if remediation causes issues',
            'verification': 'Run health checks after rollback'
        }
    
    def execute_step(self, step: Dict, context: Dict) -> Dict:
        """Execute a single runbook step"""
        step_type = step.get('type', 'diagnostic')
        step_name = step.get('name', 'Unknown step')
        command = step.get('command', '')
        
        start_time = datetime.now()
        
        try:
            if step_type == 'notification':
                result = self._execute_notification(step, context)
            elif step_type == 'escalation':
                result = self._execute_escalation(step, context)
            else:
                result = self._execute_command(command, context)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'step_name': step_name,
                'status': 'completed' if result.get('success', False) else 'failed',
                'duration_seconds': duration,
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'step_name': step_name,
                'status': 'failed',
                'duration_seconds': duration,
                'output': '',
                'error': str(e),
                'timestamp': end_time.isoformat()
            }
    
    def _execute_command(self, command: str, context: Dict) -> Dict:
        """Execute a shell command"""
        try:
            # Safety check for dangerous commands
            if any(dangerous in command for dangerous in ['rm -rf', 'kubectl delete', 'docker rm']):
                if not context.get('approved', False):
                    return {
                        'success': False,
                        'error': 'Command requires approval but not approved'
                    }
            
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command execution timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_notification(self, step: Dict, context: Dict) -> Dict:
        """Execute notification step"""
        # Mock notification - in real implementation would send to Slack/Teams/etc.
        message = step.get('message', f"Alert: {context.get('alert', {}).get('message', 'Unknown')}")
        
        return {
            'success': True,
            'output': f"Notification sent: {message}"
        }
    
    def _execute_escalation(self, step: Dict, context: Dict) -> Dict:
        """Execute escalation step"""
        # Mock escalation - in real implementation would escalate to incident management
        alert = context.get('alert', {})
        severity = alert.get('severity', 'medium')
        
        return {
            'success': True,
            'output': f"Incident escalated with severity: {severity}"
        }
    
    def execute_runbook(self, alert: Dict, auto_approve: bool = False) -> Dict:
        """Execute complete runbook for an alert"""
        # Analyze alert and create plan
        analysis = self.analyze_alert(alert)
        plan = analysis['plan']
        
        execution_id = f"runbook-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        execution_log = {
            'execution_id': execution_id,
            'alert': alert,
            'plan': plan,
            'start_time': datetime.now().isoformat(),
            'steps_executed': [],
            'status': ExecutionStatus.IN_PROGRESS.value
        }
        
        try:
            # Execute each step
            for i, step in enumerate(plan.get('steps', [])):
                # Check for approval requirement
                if step.get('approval', False) and not auto_approve:
                    execution_log['steps_executed'].append({
                        'step_number': i + 1,
                        'step_name': step.get('name', 'Unknown'),
                        'status': ExecutionStatus.APPROVAL_REQUIRED.value,
                        'message': 'Step requires approval before execution'
                    })
                    execution_log['status'] = ExecutionStatus.APPROVAL_REQUIRED.value
                    break
                
                # Execute step
                context = {
                    'alert': alert,
                    'plan': plan,
                    'step_number': i + 1,
                    'approved': auto_approve
                }
                
                step_result = self.execute_step(step, context)
                step_result['step_number'] = i + 1
                execution_log['steps_executed'].append(step_result)
                
                # Stop execution if step failed
                if step_result['status'] == 'failed':
                    execution_log['status'] = ExecutionStatus.FAILED.value
                    break
            
            # Mark as completed if all steps succeeded
            if execution_log['status'] == ExecutionStatus.IN_PROGRESS.value:
                execution_log['status'] = ExecutionStatus.COMPLETED.value
            
        except Exception as e:
            execution_log['status'] = ExecutionStatus.FAILED.value
            execution_log['error'] = str(e)
        
        finally:
            execution_log['end_time'] = datetime.now().isoformat()
            
            # Calculate total duration
            start = datetime.fromisoformat(execution_log['start_time'])
            end = datetime.fromisoformat(execution_log['end_time'])
            execution_log['total_duration_seconds'] = (end - start).total_seconds()
        
        # Store in execution history
        self.execution_history.append(execution_log)
        
        return {
            'execution_id': execution_id,
            'status': execution_log['status'],
            'analysis': analysis,
            'execution_log': execution_log,
            'next_steps': self._get_next_steps(execution_log)
        }
    
    def _get_next_steps(self, execution_log: Dict) -> List[str]:
        """Determine next steps based on execution results"""
        status = execution_log.get('status', '')
        steps = []
        
        if status == ExecutionStatus.COMPLETED.value:
            steps.append('Runbook execution completed successfully')
            steps.append('Monitor service health for 15 minutes')
            steps.append('Document incident resolution')
        elif status == ExecutionStatus.FAILED.value:
            steps.append('Review failed step and error message')
            steps.append('Consider manual intervention')
            steps.append('Escalate to senior engineer if needed')
        elif status == ExecutionStatus.APPROVAL_REQUIRED.value:
            steps.append('Review pending approval steps')
            steps.append('Approve or reject pending operations')
            steps.append('Consider alternative approaches')
        
        return steps


def main():
    """Example usage"""
    if len(sys.argv) < 2:
        print("Usage: python runbook_executor.py <alert_json>")
        print("Example: python runbook_executor.py '{\"type\": \"pod_crash_loop_backoff\", \"service\": \"api\", \"severity\": \"high\"}'")
        sys.exit(1)
    
    try:
        alert = json.loads(sys.argv[1])
        executor = RunbookExecutor()
        
        # Execute runbook
        result = executor.execute_runbook(alert, auto_approve=False)
        
        print(json.dumps(result, indent=2))
        
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
