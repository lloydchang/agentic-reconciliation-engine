#!/usr/bin/env python3
"""
Incident Triage Runbook Script

Multi-cloud automation for incident triage and runbook execution across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class IncidentSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IncidentCategory(Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    NETWORKING = "networking"
    DATABASE = "database"

class TriageStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

class RunbookStepType(Enum):
    DIAGNOSTIC = "diagnostic"
    REMEDIATION = "remediation"
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    ESCALATION = "escalation"

@dataclass
class Incident:
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    category: IncidentCategory
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    created_at: datetime
    impact_score: float
    affected_services: List[str]
    symptoms: List[str]
    metrics: Dict[str, Any]

@dataclass
class RunbookStep:
    step_id: str
    step_name: str
    step_type: RunbookStepType
    description: str
    commands: List[Dict[str, Any]]
    expected_result: str
    timeout_minutes: int
    retry_attempts: int
    automated: bool
    dependencies: List[str]
    success_criteria: Dict[str, Any]

@dataclass
class Runbook:
    runbook_id: str
    runbook_name: str
    description: str
    incident_category: IncidentCategory
    incident_severity: List[IncidentSeverity]
    provider: str
    steps: List[RunbookStep]
    estimated_duration_minutes: int
    success_rate: float
    last_updated: datetime
    enabled: bool

@dataclass
class TriageResult:
    incident_id: str
    runbook_id: str
    triage_status: TriageStatus
    started_at: datetime
    completed_at: Optional[datetime]
    steps_executed: List[str]
    steps_failed: List[str]
    current_step: Optional[str]
    progress_percentage: float
    automated_steps: int
    manual_steps: int
    escalation_triggered: bool
    resolution_summary: Optional[str]
    error_message: Optional[str]

class IncidentTriageRunbook:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.runbooks = {}
        self.triage_history = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load triage runbook configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'triage_settings': {
                'auto_triage_enabled': True,
                'max_parallel_triage': 3,
                'step_timeout_minutes': 30,
                'retry_attempts': 3,
                'escalation_enabled': True,
                'verification_enabled': True,
                'notification_enabled': True
            },
            'automation_settings': {
                'automate_safe_steps': True,
                'require_approval_for_destructive': True,
                'dry_run_by_default': False,
                'rollback_enabled': True,
                'logging_level': 'info'
            }
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def load_runbooks(self, runbooks_file: Optional[str] = None) -> Dict[str, Runbook]:
        """Load incident triage runbooks"""
        logger.info("Loading incident triage runbooks")
        
        # Default runbooks
        default_runbooks = {
            'aws-infrastructure-critical': Runbook(
                runbook_id='aws-infrastructure-critical',
                runbook_name='AWS Critical Infrastructure Triage',
                description='Triage runbook for critical AWS infrastructure incidents',
                incident_category=IncidentCategory.INFRASTRUCTURE,
                incident_severity=[IncidentSeverity.CRITICAL, IncidentSeverity.HIGH],
                provider='aws',
                steps=[
                    RunbookStep(
                        step_id='step-1',
                        step_name='Assess Incident Impact',
                        step_type=RunbookStepType.DIAGNOSTIC,
                        description='Assess the impact and scope of the infrastructure incident',
                        commands=[
                            {'type': 'aws-cli', 'command': 'aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,State.Name]"'},
                            {'type': 'aws-cli', 'command': 'aws cloudwatch describe-alarms --state-value ALARM'},
                            {'type': 'check', 'command': 'check_service_health'}
                        ],
                        expected_result='Incident impact assessment completed',
                        timeout_minutes=5,
                        retry_attempts=2,
                        automated=True,
                        dependencies=[],
                        success_criteria={'services_affected': 'identified', 'impact_scope': 'determined'}
                    ),
                    RunbookStep(
                        step_id='step-2',
                        step_name='Isolate Affected Resources',
                        step_type=RunbookStepType.REMEDIATION,
                        description='Isolate affected resources to prevent further impact',
                        commands=[
                            {'type': 'aws-cli', 'command': 'aws autoscaling suspend-processes --auto-scaling-group-name <ASG_NAME>'},
                            {'type': 'aws-cli', 'command': 'aws elbv2 modify-load-balancer --load-balancer-name <LB_NAME> --scheme internal'},
                            {'type': 'network', 'command': 'isolate_network_segment'}
                        ],
                        expected_result='Affected resources isolated',
                        timeout_minutes=10,
                        retry_attempts=3,
                        automated=True,
                        dependencies=['step-1'],
                        success_criteria={'isolation_complete': True, 'no_new_impact': True}
                    ),
                    RunbookStep(
                        step_id='step-3',
                        step_name='Implement Temporary Fix',
                        step_type=RunbookStepType.REMEDIATION,
                        description='Implement temporary fix to restore service',
                        commands=[
                            {'type': 'aws-cli', 'command': 'aws ec2 start-instances --instance-ids <INSTANCE_ID>'},
                            {'type': 'aws-cli', 'command': 'aws rds reboot-db-instance --db-instance-identifier <DB_ID>'},
                            {'type': 'service', 'command': 'restart_service'}
                        ],
                        expected_result='Temporary fix implemented',
                        timeout_minutes=15,
                        retry_attempts=2,
                        automated=True,
                        dependencies=['step-2'],
                        success_criteria={'service_restored': True, 'basic_functionality': True}
                    ),
                    RunbookStep(
                        step_id='step-4',
                        step_name='Verify Service Recovery',
                        step_type=RunbookStepType.VERIFICATION,
                        description='Verify that services have recovered',
                        commands=[
                            {'type': 'health-check', 'command': 'check_service_health'},
                            {'type': 'aws-cli', 'command': 'aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime'},
                            {'type': 'user-check', 'command': 'verify_user_access'}
                        ],
                        expected_result='Service recovery verified',
                        timeout_minutes=10,
                        retry_attempts=3,
                        automated=True,
                        dependencies=['step-3'],
                        success_criteria={'health_checks_pass': True, 'response_time_normal': True}
                    ),
                    RunbookStep(
                        step_id='step-5',
                        step_name='Notify Stakeholders',
                        step_type=RunbookStepType.NOTIFICATION,
                        description='Notify stakeholders about incident resolution',
                        commands=[
                            {'type': 'notification', 'command': 'send_slack_notification'},
                            {'type': 'email', 'command': 'send_status_update'},
                            {'type': 'incident-update', 'command': 'update_incident_ticket'}
                        ],
                        expected_result='Stakeholders notified',
                        timeout_minutes=5,
                        retry_attempts=2,
                        automated=True,
                        dependencies=['step-4'],
                        success_criteria={'notifications_sent': True, 'status_updated': True}
                    )
                ],
                estimated_duration_minutes=45,
                success_rate=0.92,
                last_updated=datetime.utcnow() - timedelta(days=7),
                enabled=True
            ),
            'azure-application-high': Runbook(
                runbook_id='azure-application-high',
                runbook_name='Azure High Severity Application Triage',
                description='Triage runbook for high severity Azure application incidents',
                incident_category=IncidentCategory.APPLICATION,
                incident_severity=[IncidentSeverity.HIGH, IncidentSeverity.MEDIUM],
                provider='azure',
                steps=[
                    RunbookStep(
                        step_id='step-1',
                        step_name='Analyze Application Metrics',
                        step_type=RunbookStepType.DIAGNOSTIC,
                        description='Analyze application performance and error metrics',
                        commands=[
                            {'type': 'azure-cli', 'command': 'az monitor metrics list --resource <RESOURCE_ID>'},
                            {'type': 'azure-cli', 'command': 'az webapp log tail --name <APP_NAME> --resource-group <RG_NAME>'},
                            {'type': 'app-insights', 'command': 'get_application_insights'}
                        ],
                        expected_result='Application metrics analyzed',
                        timeout_minutes=8,
                        retry_attempts=2,
                        automated=True,
                        dependencies=[],
                        success_criteria={'metrics_collected': True, 'errors_identified': True}
                    ),
                    RunbookStep(
                        step_id='step-2',
                        step_name='Scale Application Resources',
                        step_type=RunbookStepType.REMEDIATION,
                        description='Scale application resources to handle load',
                        commands=[
                            {'type': 'azure-cli', 'command': 'az webapp scale up --name <APP_NAME> --resource-group <RG_NAME>'},
                            {'type': 'azure-cli', 'command': 'az appservice plan update --name <PLAN_NAME> --scale <SCALE_SETTINGS>'},
                            {'type': 'k8s', 'command': 'kubectl scale deployment <DEPLOYMENT> --replicas <REPLICAS>'}
                        ],
                        expected_result='Application resources scaled',
                        timeout_minutes=12,
                        retry_attempts=2,
                        automated=True,
                        dependencies=['step-1'],
                        success_criteria={'scaling_complete': True, 'resources_available': True}
                    ),
                    RunbookStep(
                        step_id='step-3',
                        step_name='Restart Application Services',
                        step_type=RunbookStepType.REMEDIATION,
                        description='Restart affected application services',
                        commands=[
                            {'type': 'azure-cli', 'command': 'az webapp restart --name <APP_NAME> --resource-group <RG_NAME>'},
                            {'type': 'service', 'command': 'restart_application_service'},
                            {'type': 'container', 'command': 'restart_container'}
                        ],
                        expected_result='Application services restarted',
                        timeout_minutes=10,
                        retry_attempts=2,
                        automated=True,
                        dependencies=['step-2'],
                        success_criteria={'services_restarted': True, 'application_responding': True}
                    ),
                    RunbookStep(
                        step_id='step-4',
                        step_name='Verify Application Functionality',
                        step_type=RunbookStepType.VERIFICATION,
                        description='Verify application functionality and performance',
                        commands=[
                            {'type': 'health-check', 'command': 'check_application_health'},
                            {'type': 'load-test', 'command': 'run_smoke_test'},
                            {'type': 'user-check', 'command': 'verify_user_workflows'}
                        ],
                        expected_result='Application functionality verified',
                        timeout_minutes=8,
                        retry_attempts=3,
                        automated=True,
                        dependencies=['step-3'],
                        success_criteria={'health_checks_pass': True, 'performance_acceptable': True}
                    ),
                    RunbookStep(
                        step_id='step-5',
                        step_name='Update Monitoring Alerts',
                        step_type=RunbookStepType.NOTIFICATION,
                        description='Update monitoring alerts and thresholds',
                        commands=[
                            {'type': 'azure-cli', 'command': 'az monitor metrics alert update --name <ALERT_NAME>'},
                            {'type': 'monitoring', 'command': 'adjust_alert_thresholds'},
                            {'type': 'documentation', 'command': 'update_runbook_procedures'}
                        ],
                        expected_result='Monitoring alerts updated',
                        timeout_minutes=6,
                        retry_attempts=1,
                        automated=True,
                        dependencies=['step-4'],
                        success_criteria={'alerts_updated': True, 'thresholds_adjusted': True}
                    )
                ],
                estimated_duration_minutes=44,
                success_rate=0.88,
                last_updated=datetime.utcnow() - timedelta(days=5),
                enabled=True
            ),
            'gcp-security-critical': Runbook(
                runbook_id='gcp-security-critical',
                runbook_name='GCP Critical Security Triage',
                description='Triage runbook for critical security incidents in GCP',
                incident_category=IncidentCategory.SECURITY,
                incident_severity=[IncidentSeverity.CRITICAL],
                provider='gcp',
                steps=[
                    RunbookStep(
                        step_id='step-1',
                        step_name='Security Incident Assessment',
                        step_type=RunbookStepType.DIAGNOSTIC,
                        description='Assess security incident scope and impact',
                        commands=[
                            {'type': 'gcloud-cli', 'command': 'gcloud logging read "severity=ERROR" --limit 50'},
                            {'type': 'gcloud-cli', 'command': 'gcloud compute instances list --filter="status=RUNNING"'},
                            {'type': 'security-scan', 'command': 'run_security_scan'}
                        ],
                        expected_result='Security incident assessment completed',
                        timeout_minutes=10,
                        retry_attempts=2,
                        automated=True,
                        dependencies=[],
                        success_criteria={'scope_identified': True, 'impact_assessed': True}
                    ),
                    RunbookStep(
                        step_id='step-2',
                        step_name='Isolate Compromised Resources',
                        step_type=RunbookStepType.REMEDIATION,
                        description='Isolate compromised resources to prevent further damage',
                        commands=[
                            {'type': 'gcloud-cli', 'command': 'gcloud compute instances stop <INSTANCE_ID>'},
                            {'type': 'gcloud-cli', 'command': 'gcloud projects update <PROJECT_ID> --set-iam-policy <SECURE_POLICY>'},
                            {'type': 'firewall', 'command': 'block_malicious_ips'}
                        ],
                        expected_result='Compromised resources isolated',
                        timeout_minutes=15,
                        retry_attempts=3,
                        automated=True,
                        dependencies=['step-1'],
                        success_criteria={'isolation_complete': True, 'access_revoked': True}
                    ),
                    RunbookStep(
                        step_id='step-3',
                        step_name='Security Remediation',
                        step_type=RunbookStepType.REMEDIATION,
                        description='Perform security remediation actions',
                        commands=[
                            {'type': 'gcloud-cli', 'command': 'gcloud kms decrypt --ciphertext-file <ENCRYPTED_FILE>'},
                            {'type': 'security', 'command': 'patch_security_vulnerabilities'},
                            {'type': 'identity', 'command': 'rotate_compromised_credentials'}
                        ],
                        expected_result='Security remediation completed',
                        timeout_minutes=20,
                        retry_attempts=2,
                        automated=True,
                        dependencies=['step-2'],
                        success_criteria={'vulnerabilities_patched': True, 'credentials_rotated': True}
                    ),
                    RunbookStep(
                        step_id='step-4',
                        step_name='Security Verification',
                        step_type=RunbookStepType.VERIFICATION,
                        description='Verify security posture and incident resolution',
                        commands=[
                            {'type': 'security-scan', 'command': 'run_vulnerability_scan'},
                            {'type': 'compliance', 'command': 'check_compliance_status'},
                            {'type': 'audit', 'command': 'security_audit_check'}
                        ],
                        expected_result='Security verification completed',
                        timeout_minutes=12,
                        retry_attempts=2,
                        automated=True,
                        dependencies=['step-3'],
                        success_criteria={'scan_clean': True, 'compliance_met': True}
                    ),
                    RunbookStep(
                        step_id='step-5',
                        step_name='Security Incident Escalation',
                        step_type=RunbookStepType.ESCALATION,
                        description='Escalate security incident to security team',
                        commands=[
                            {'type': 'notification', 'command': 'notify_security_team'},
                            {'type': 'incident', 'command': 'create_security_incident_ticket'},
                            {'type': 'compliance', 'command': 'report_to_compliance_team'}
                        ],
                        expected_result='Security incident escalated',
                        timeout_minutes=5,
                        retry_attempts=2,
                        automated=True,
                        dependencies=['step-4'],
                        success_criteria={'escalation_complete': True, 'documentation_updated': True}
                    )
                ],
                estimated_duration_minutes=62,
                success_rate=0.95,
                last_updated=datetime.utcnow() - timedelta(days=3),
                enabled=True
            )
        }
        
        # Load custom runbooks from file if provided
        if runbooks_file:
            try:
                with open(runbooks_file, 'r') as f:
                    custom_runbooks = json.load(f)
                
                for runbook_id, runbook_data in custom_runbooks.items():
                    steps = []
                    for step_data in runbook_data['steps']:
                        step = RunbookStep(
                            step_id=step_data['step_id'],
                            step_name=step_data['step_name'],
                            step_type=RunbookStepType(step_data['step_type']),
                            description=step_data['description'],
                            commands=step_data['commands'],
                            expected_result=step_data['expected_result'],
                            timeout_minutes=step_data['timeout_minutes'],
                            retry_attempts=step_data['retry_attempts'],
                            automated=step_data['automated'],
                            dependencies=step_data['dependencies'],
                            success_criteria=step_data['success_criteria']
                        )
                        steps.append(step)
                    
                    runbook = Runbook(
                        runbook_id=runbook_id,
                        runbook_name=runbook_data['runbook_name'],
                        description=runbook_data['description'],
                        incident_category=IncidentCategory(runbook_data['incident_category']),
                        incident_severity=[IncidentSeverity(s) for s in runbook_data['incident_severity']],
                        provider=runbook_data['provider'],
                        steps=steps,
                        estimated_duration_minutes=runbook_data['estimated_duration_minutes'],
                        success_rate=runbook_data['success_rate'],
                        last_updated=datetime.fromisoformat(runbook_data['last_updated']),
                        enabled=runbook_data.get('enabled', True)
                    )
                    default_runbooks[runbook_id] = runbook
                    
            except Exception as e:
                logger.warning(f"Failed to load custom runbooks: {e}")
        
        self.runbooks = default_runbooks
        logger.info(f"Loaded {len(self.runbooks)} triage runbooks")
        
        return self.runbooks
    
    def select_runbook(self, incident: Incident) -> Optional[Runbook]:
        """Select appropriate runbook for incident"""
        logger.info(f"Selecting runbook for incident {incident.incident_id}")
        
        # Find matching runbooks
        matching_runbooks = []
        
        for runbook in self.runbooks.values():
            if not runbook.enabled:
                continue
            
            # Check category match
            if runbook.incident_category != incident.category:
                continue
            
            # Check severity match
            if incident.severity not in runbook.incident_severity:
                continue
            
            # Check provider match (or generic runbook)
            if runbook.provider != incident.provider and runbook.provider != 'all':
                continue
            
            matching_runbooks.append(runbook)
        
        if not matching_runbooks:
            logger.warning(f"No matching runbook found for incident {incident.incident_id}")
            return None
        
        # Select best match (prefer provider-specific runbook)
        best_runbook = None
        for runbook in matching_runbooks:
            if runbook.provider == incident.provider:
                best_runbook = runbook
                break
        
        if not best_runbook:
            best_runbook = matching_runbooks[0]
        
        logger.info(f"Selected runbook: {best_runbook.runbook_id}")
        return best_runbook
    
    def execute_triage(self, incident: Incident, runbook: Runbook, dry_run: bool = False) -> TriageResult:
        """Execute triage runbook for incident"""
        logger.info(f"Executing triage for incident {incident.incident_id} with runbook {runbook.runbook_id}")
        
        # Initialize provider handler
        handler = self._get_provider_handler(incident.provider)
        if not handler.initialize_client():
            raise RuntimeError(f"Failed to initialize {incident.provider} handler")
        
        # Create triage result
        result = TriageResult(
            incident_id=incident.incident_id,
            runbook_id=runbook.runbook_id,
            triage_status=TriageStatus.PENDING,
            started_at=datetime.utcnow(),
            completed_at=None,
            steps_executed=[],
            steps_failed=[],
            current_step=None,
            progress_percentage=0.0,
            automated_steps=0,
            manual_steps=0,
            escalation_triggered=False,
            resolution_summary=None,
            error_message=None
        )
        
        try:
            result.triage_status = TriageStatus.IN_PROGRESS
            
            # Execute runbook steps
            total_steps = len(runbook.steps)
            completed_steps = 0
            
            for step in runbook.steps:
                result.current_step = step.step_id
                
                # Check dependencies
                if not self._check_step_dependencies(step, result.steps_executed):
                    logger.warning(f"Skipping step {step.step_id} due to unmet dependencies")
                    continue
                
                # Execute step
                step_success = self._execute_step(handler, incident, step, dry_run)
                
                if step_success:
                    result.steps_executed.append(step.step_id)
                    completed_steps += 1
                    
                    if step.automated:
                        result.automated_steps += 1
                    else:
                        result.manual_steps += 1
                else:
                    result.steps_failed.append(step.step_id)
                    
                    # Check if this is a critical step failure
                    if step.step_type in [RunbookStepType.REMEDIATION, RunbookStepType.DIAGNOSTIC]:
                        logger.error(f"Critical step {step.step_id} failed, stopping triage")
                        break
                
                # Update progress
                result.progress_percentage = (completed_steps / total_steps) * 100
                
                # Check for escalation conditions
                if not self._check_escalation_conditions(incident, result):
                    result.escalation_triggered = True
                    self._trigger_escalation(incident, result)
                    break
            
            # Determine final status
            if len(result.steps_failed) == 0:
                result.triage_status = TriageStatus.COMPLETED
                result.resolution_summary = "Triage completed successfully with all steps executed"
            elif len(result.steps_failed) < len(runbook.steps) / 2:
                result.triage_status = TriageStatus.COMPLETED
                result.resolution_summary = f"Triage completed with {len(result.steps_failed)} failed steps"
            else:
                result.triage_status = TriageStatus.FAILED
                result.resolution_summary = f"Triage failed with {len(result.steps_failed)} failed steps"
            
            result.completed_at = datetime.utcnow()
            result.current_step = None
            
        except Exception as e:
            logger.error(f"Triage execution failed for incident {incident.incident_id}: {e}")
            result.triage_status = TriageStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.error_message = str(e)
        
        # Record triage history
        self.triage_history.append({
            'incident_id': incident.incident_id,
            'runbook_id': runbook.runbook_id,
            'status': result.triage_status.value,
            'started_at': result.started_at,
            'completed_at': result.completed_at,
            'success': result.triage_status == TriageStatus.COMPLETED
        })
        
        return result
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific triage handler"""
        from incident_triage_runbook_handler import get_triage_handler
        region = self.config['providers'][provider]['region']
        return get_triage_handler(provider, region)
    
    def _check_step_dependencies(self, step: RunbookStep, executed_steps: List[str]) -> bool:
        """Check if step dependencies are satisfied"""
        for dependency in step.dependencies:
            if dependency not in executed_steps:
                return False
        return True
    
    def _execute_step(self, handler, incident: Incident, step: RunbookStep, dry_run: bool) -> bool:
        """Execute a single triage step"""
        logger.info(f"Executing step {step.step_id}: {step.step_name}")
        
        try:
            if dry_run:
                logger.info(f"DRY RUN: Would execute step {step.step_id}")
                return True
            
            # Execute commands
            for command in step.commands:
                command_success = self._execute_command(handler, incident, command, step)
                
                if not command_success:
                    logger.error(f"Command failed in step {step.step_id}: {command}")
                    return False
            
            # Verify success criteria
            if not self._verify_success_criteria(handler, incident, step.success_criteria):
                logger.error(f"Success criteria not met for step {step.step_id}")
                return False
            
            logger.info(f"Step {step.step_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute step {step.step_id}: {e}")
            return False
    
    def _execute_command(self, handler, incident: Incident, command: Dict[str, Any], step: RunbookStep) -> bool:
        """Execute a single command"""
        try:
            command_type = command.get('type')
            command_str = command.get('command', '')
            
            # Substitute variables in command
            command_str = self._substitute_variables(command_str, incident, step)
            
            if command_type == 'aws-cli':
                return handler.execute_aws_cli(command_str)
            elif command_type == 'azure-cli':
                return handler.execute_azure_cli(command_str)
            elif command_type == 'gcloud-cli':
                return handler.execute_gcloud_cli(command_str)
            elif command_type == 'k8s':
                return handler.execute_kubernetes(command_str)
            elif command_type == 'health-check':
                return handler.execute_health_check(command_str)
            elif command_type == 'notification':
                return handler.execute_notification(command_str)
            elif command_type == 'email':
                return handler.execute_email(command_str)
            elif command_type == 'security-scan':
                return handler.execute_security_scan(command_str)
            elif command_type == 'service':
                return handler.execute_service_command(command_str)
            elif command_type == 'network':
                return handler.execute_network_command(command_str)
            elif command_type == 'container':
                return handler.execute_container_command(command_str)
            elif command_type == 'app-insights':
                return handler.execute_app_insights(command_str)
            elif command_type == 'firewall':
                return handler.execute_firewall_command(command_str)
            elif command_type == 'identity':
                return handler.execute_identity_command(command_str)
            elif command_type == 'compliance':
                return handler.execute_compliance_command(command_str)
            elif command_type == 'audit':
                return handler.execute_audit_command(command_str)
            elif command_type == 'monitoring':
                return handler.execute_monitoring_command(command_str)
            elif command_type == 'documentation':
                return handler.execute_documentation_command(command_str)
            elif command_type == 'incident':
                return handler.execute_incident_command(command_str)
            else:
                logger.warning(f"Unsupported command type: {command_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False
    
    def _substitute_variables(self, command_str: str, incident: Incident, step: RunbookStep) -> str:
        """Substitute variables in command string"""
        substitutions = {
            '<INCIDENT_ID>': incident.incident_id,
            '<RESOURCE_ID>': incident.resource_id,
            '<RESOURCE_NAME>': incident.resource_name,
            '<ENVIRONMENT>': incident.environment,
            '<SEVERITY>': incident.severity.value,
            '<CATEGORY>': incident.category.value,
            '<STEP_ID>': step.step_id
        }
        
        for placeholder, value in substitutions.items():
            command_str = command_str.replace(placeholder, value)
        
        return command_str
    
    def _verify_success_criteria(self, handler, incident: Incident, criteria: Dict[str, Any]) -> bool:
        """Verify step success criteria"""
        try:
            for criterion, expected_value in criteria.items():
                if criterion == 'services_affected':
                    # Verify services affected are identified
                    actual_value = handler.get_affected_services(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'impact_scope':
                    # Verify impact scope is determined
                    actual_value = handler.get_impact_scope(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'isolation_complete':
                    # Verify isolation is complete
                    actual_value = handler.check_isolation_status(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'no_new_impact':
                    # Verify no new impact
                    actual_value = handler.check_new_impact(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'service_restored':
                    # Verify service is restored
                    actual_value = handler.check_service_status(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'basic_functionality':
                    # Verify basic functionality
                    actual_value = handler.check_basic_functionality(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'health_checks_pass':
                    # Verify health checks pass
                    actual_value = handler.run_health_checks(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'response_time_normal':
                    # Verify response time is normal
                    actual_value = handler.check_response_time(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'notifications_sent':
                    # Verify notifications were sent
                    actual_value = handler.check_notifications_sent(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'status_updated':
                    # Verify status was updated
                    actual_value = handler.check_status_updated(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'metrics_collected':
                    # Verify metrics were collected
                    actual_value = handler.check_metrics_collected(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'errors_identified':
                    # Verify errors were identified
                    actual_value = handler.check_errors_identified(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'scaling_complete':
                    # Verify scaling is complete
                    actual_value = handler.check_scaling_complete(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'resources_available':
                    # Verify resources are available
                    actual_value = handler.check_resources_available(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'services_restarted':
                    # Verify services were restarted
                    actual_value = handler.check_services_restarted(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'application_responding':
                    # Verify application is responding
                    actual_value = handler.check_application_responding(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'performance_acceptable':
                    # Verify performance is acceptable
                    actual_value = handler.check_performance_acceptable(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'alerts_updated':
                    # Verify alerts were updated
                    actual_value = handler.check_alerts_updated(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'thresholds_adjusted':
                    # Verify thresholds were adjusted
                    actual_value = handler.check_thresholds_adjusted(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'scope_identified':
                    # Verify scope was identified
                    actual_value = handler.get_incident_scope(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'impact_assessed':
                    # Verify impact was assessed
                    actual_value = handler.get_incident_impact(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'isolation_complete':
                    # Verify isolation is complete
                    actual_value = handler.check_isolation_complete(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'access_revoked':
                    # Verify access was revoked
                    actual_value = handler.check_access_revoked(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'vulnerabilities_patched':
                    # Verify vulnerabilities were patched
                    actual_value = handler.check_vulnerabilities_patched(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'credentials_rotated':
                    # Verify credentials were rotated
                    actual_value = handler.check_credentials_rotated(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'scan_clean':
                    # Verify security scan is clean
                    actual_value = handler.run_security_scan(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'compliance_met':
                    # Verify compliance is met
                    actual_value = handler.check_compliance_status(incident)
                    if not actual_value:
                        return False
                
                elif criterion == 'escalation_complete':
                    # Verify escalation is complete
                    actual_value = handler.check_escalation_complete(incident)
                    if actual_value != expected_value:
                        return False
                
                elif criterion == 'documentation_updated':
                    # Verify documentation was updated
                    actual_value = handler.check_documentation_updated(incident)
                    if actual_value != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify success criteria: {e}")
            return False
    
    def _check_escalation_conditions(self, incident: Incident, result: TriageResult) -> bool:
        """Check if escalation conditions are met"""
        # Escalate if critical incident and steps are failing
        if incident.severity == IncidentSeverity.CRITICAL and len(result.steps_failed) > 0:
            return False  # Need escalation
        
        # Escalate if triage is taking too long
        if (datetime.utcnow() - result.started_at).total_seconds() > (runbook.estimated_duration_minutes * 60 * 2):
            return False  # Need escalation
        
        return True  # No escalation needed
    
    def _trigger_escalation(self, incident: Incident, result: TriageResult) -> None:
        """Trigger escalation for incident"""
        logger.info(f"Triggering escalation for incident {incident.incident_id}")
        
        # In real implementation, this would:
        # 1. Notify escalation contacts
        # 2. Create escalation ticket
        # 3. Update incident status
        # 4. Document escalation reason
        
        result.escalation_triggered = True
    
    def batch_triage(self, incidents: List[Incident], dry_run: bool = False) -> List[TriageResult]:
        """Perform batch triage for multiple incidents"""
        logger.info(f"Batch triaging {len(incidents)} incidents")
        
        results = []
        
        # Sort incidents by severity
        severity_order = {
            IncidentSeverity.CRITICAL: 0,
            IncidentSeverity.HIGH: 1,
            IncidentSeverity.MEDIUM: 2,
            IncidentSeverity.LOW: 3
        }
        
        sorted_incidents = sorted(incidents, key=lambda x: severity_order[x.severity])
        
        # Process incidents with concurrency limit
        max_parallel = self.config['triage_settings']['max_parallel_triage']
        current_triage = []
        completed_triage = set()
        
        for incident in sorted_incidents:
            # Wait for slot if at concurrency limit
            while len(current_triage) >= max_parallel:
                # Check completed triage
                current_triage = [inc for inc in current_triage 
                               if inc.incident_id not in completed_triage]
                if len(current_triage) < max_parallel:
                    break
                # Small delay to avoid busy waiting
                import time
                time.sleep(1)
            
            # Start triage
            current_triage.append(incident)
            
            try:
                # Select runbook
                runbook = self.select_runbook(incident)
                if not runbook:
                    logger.warning(f"No runbook found for incident {incident.incident_id}")
                    # Create a failed result
                    result = TriageResult(
                        incident_id=incident.incident_id,
                        runbook_id='none',
                        triage_status=TriageStatus.FAILED,
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                        steps_executed=[],
                        steps_failed=[],
                        current_step=None,
                        progress_percentage=0.0,
                        automated_steps=0,
                        manual_steps=0,
                        escalation_triggered=False,
                        resolution_summary="No suitable runbook found",
                        error_message="No runbook available for this incident type"
                    )
                    results.append(result)
                    completed_triage.add(incident.incident_id)
                    continue
                
                # Execute triage
                result = self.execute_triage(incident, runbook, dry_run)
                results.append(result)
                completed_triage.add(incident.incident_id)
                
            except Exception as e:
                logger.error(f"Failed to triage incident {incident.incident_id}: {e}")
                # Create a failed result
                result = TriageResult(
                    incident_id=incident.incident_id,
                    runbook_id='error',
                    triage_status=TriageStatus.FAILED,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    steps_executed=[],
                    steps_failed=[],
                    current_step=None,
                    progress_percentage=0.0,
                    automated_steps=0,
                    manual_steps=0,
                    escalation_triggered=False,
                    resolution_summary=None,
                    error_message=str(e)
                )
                results.append(result)
                completed_triage.add(incident.incident_id)
        
        return results
    
    def generate_triage_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive triage report"""
        logger.info("Generating triage report")
        
        # Calculate statistics
        total_triage = len(self.triage_history)
        successful_triage = len([t for t in self.triage_history if t['success']])
        failed_triage = total_triage - successful_triage
        success_rate = (successful_triage / total_triage * 100) if total_triage > 0 else 0
        
        # Runbook usage statistics
        runbook_usage = {}
        for triage in self.triage_history:
            runbook_id = triage.get('runbook_id', 'unknown')
            runbook_usage[runbook_id] = runbook_usage.get(runbook_id, 0) + 1
        
        # Average triage duration
        durations = []
        for triage in self.triage_history:
            if triage['started_at'] and triage['completed_at']:
                start = datetime.fromisoformat(triage['started_at'])
                end = datetime.fromisoformat(triage['completed_at'])
                duration = (end - start).total_seconds() / 60  # minutes
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_triage_operations': total_triage,
                'successful_triage': successful_triage,
                'failed_triage': failed_triage,
                'success_rate': success_rate,
                'average_duration_minutes': avg_duration,
                'enabled_runbooks': len([r for r in self.runbooks.values() if r.enabled])
            },
            'runbook_usage': runbook_usage,
            'runbook_performance': {
                runbook_id: {
                    'success_rate': runbook.success_rate,
                    'estimated_duration_minutes': runbook.estimated_duration_minutes,
                    'total_steps': len(runbook.steps),
                    'automated_steps': len([s for s in runbook.steps if s.automated]),
                    'enabled': runbook.enabled
                }
                for runbook_id, runbook in self.runbooks.items()
            },
            'recent_triage': self.triage_history[-20:]  # Last 20 triage operations
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Triage report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Incident Triage Runbook")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--runbooks", help="Runbooks file")
    parser.add_argument("--action", choices=['triage', 'batch', 'report'], 
                       default='triage', help="Action to perform")
    parser.add_argument("--incident-file", help="Incident JSON file for triage")
    parser.add_argument("--batch-file", help="Batch incidents JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize incident triage runbook
    triage = IncidentTriageRunbook(args.config)
    
    # Load runbooks
    triage.load_runbooks(args.runbooks)
    
    try:
        if args.action == 'triage':
            if not args.incident_file:
                print("Error: --incident-file required for triage action")
                sys.exit(1)
            
            with open(args.incident_file, 'r') as f:
                incident_data = json.load(f)
            
            # Create incident object
            incident = Incident(
                incident_id=incident_data['incident_id'],
                title=incident_data['title'],
                description=incident_data['description'],
                severity=IncidentSeverity(incident_data['severity']),
                category=IncidentCategory(incident_data['category']),
                provider=incident_data['provider'],
                resource_id=incident_data['resource_id'],
                resource_name=incident_data['resource_name'],
                environment=incident_data['environment'],
                created_at=datetime.fromisoformat(incident_data['created_at']),
                impact_score=incident_data.get('impact_score', 0.5),
                affected_services=incident_data.get('affected_services', []),
                symptoms=incident_data.get('symptoms', []),
                metrics=incident_data.get('metrics', {})
            )
            
            # Select and execute runbook
            runbook = triage.select_runbook(incident)
            if not runbook:
                print(f"No suitable runbook found for incident {incident.incident_id}")
                sys.exit(1)
            
            result = triage.execute_triage(incident, runbook, args.dry_run)
            
            print(f"\nTriage Result:")
            print(f"Incident ID: {result.incident_id}")
            print(f"Runbook ID: {result.runbook_id}")
            print(f"Status: {result.triage_status.value}")
            print(f"Progress: {result.progress_percentage:.1f}%")
            print(f"Steps Executed: {len(result.steps_executed)}")
            print(f"Steps Failed: {len(result.steps_failed)}")
            print(f"Automated Steps: {result.automated_steps}")
            print(f"Manual Steps: {result.manual_steps}")
            print(f"Escalation Triggered: {result.escalation_triggered}")
            
            if result.resolution_summary:
                print(f"Resolution Summary: {result.resolution_summary}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            if args.dry_run:
                print("DRY RUN MODE - No actual triage actions performed")
        
        elif args.action == 'batch':
            if not args.batch_file:
                print("Error: --batch-file required for batch action")
                sys.exit(1)
            
            with open(args.batch_file, 'r') as f:
                incidents_data = json.load(f)
            
            # Create incident objects
            incidents = []
            for incident_data in incidents_data:
                incident = Incident(
                    incident_id=incident_data['incident_id'],
                    title=incident_data['title'],
                    description=incident_data['description'],
                    severity=IncidentSeverity(incident_data['severity']),
                    category=IncidentCategory(incident_data['category']),
                    provider=incident_data['provider'],
                    resource_id=incident_data['resource_id'],
                    resource_name=incident_data['resource_name'],
                    environment=incident_data['environment'],
                    created_at=datetime.fromisoformat(incident_data['created_at']),
                    impact_score=incident_data.get('impact_score', 0.5),
                    affected_services=incident_data.get('affected_services', []),
                    symptoms=incident_data.get('symptoms', []),
                    metrics=incident_data.get('metrics', {})
                )
                incidents.append(incident)
            
            # Batch triage
            results = triage.batch_triage(incidents, args.dry_run)
            
            print(f"\nBatch Triage Results:")
            success_count = len([r for r in results if r.triage_status == TriageStatus.COMPLETED])
            failed_count = len(results) - success_count
            
            print(f"Total Incidents: {len(results)}")
            print(f"Successful: {success_count}")
            print(f"Failed: {failed_count}")
            print(f"Average Progress: {sum(r.progress_percentage for r in results) / len(results):.1f}%")
            
            if args.output:
                results_data = [
                    {
                        'incident_id': r.incident_id,
                        'runbook_id': r.runbook_id,
                        'status': r.triage_status.value,
                        'progress': r.progress_percentage,
                        'steps_executed': len(r.steps_executed),
                        'steps_failed': len(r.steps_failed),
                        'escalation_triggered': r.escalation_triggered
                    }
                    for r in results
                ]
                with open(args.output, 'w') as f:
                    json.dump(results_data, f, indent=2)
                print(f"Results saved to: {args.output}")
        
        elif args.action == 'report':
            report = triage.generate_triage_report(args.output)
            
            summary = report['summary']
            print(f"\nTriage Report:")
            print(f"Total Triage Operations: {summary['total_triage_operations']}")
            print(f"Successful: {summary['successful_triage']}")
            print(f"Failed: {summary['failed_triage']}")
            print(f"Success Rate: {summary['success_rate']:.1f}%")
            print(f"Average Duration: {summary['average_duration_minutes']:.1f} minutes")
            print(f"Enabled Runbooks: {summary['enabled_runbooks']}")
            
            if args.output:
                print(f"Report saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Triage failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
