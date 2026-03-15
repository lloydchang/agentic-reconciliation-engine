#!/usr/bin/env python3
"""
Multi-Cloud Audit Trail Orchestrator

Orchestrates audit trail operations across multiple cloud providers
to ensure consistent audit management and compliance monitoring.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import concurrent.futures
import statistics

from audit_trail_handler import (
    AuditTrailHandler, AuditTrailConfig, AuditEvent,
    get_audit_handler
)

logger = logging.getLogger(__name__)

class OrchestrationStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PRIORITY_BASED = "priority_based"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class OrchestrationTask:
    task_id: str
    provider: str
    action: str
    parameters: Dict[str, Any]
    priority: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class OrchestrationResult:
    task_id: str
    provider: str
    action: str
    status: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class AuditOrchestrationSummary:
    orchestration_id: str
    total_tasks: int
    completed_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_events: int
    total_trails: int
    enabled_trails: int
    disabled_trails: int
    providers: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "in_progress"

class MultiCloudAuditOrchestrator:
    """Orchestrates audit trail operations across multiple cloud providers"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.handlers: Dict[str, AuditTrailHandler] = {}
        self.tasks: List[OrchestrationTask] = []
        self.results: List[OrchestrationResult] = []
        self.orchestrations: Dict[str, AuditOrchestrationSummary] = {}
        
    def initialize_handlers(self, providers: List[str], regions: Dict[str, str]) -> bool:
        """Initialize audit handlers for all providers"""
        try:
            success = True
            
            for provider in providers:
                region = regions.get(provider, "us-west-2")
                handler = get_audit_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    logger.info(f"Initialized {provider} audit handler")
                else:
                    logger.error(f"Failed to initialize {provider} audit handler")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            return False
    
    def orchestrate_audit_discovery(
        self,
        providers: List[str],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> AuditOrchestrationSummary:
        """Orchestrate audit trail discovery across providers"""
        
        if not orchestration_id:
            orchestration_id = f"discovery-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting audit discovery orchestration {orchestration_id} for providers: {providers}")
        
        # Create orchestration summary
        summary = AuditOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_events=0,
            total_trails=0,
            enabled_trails=0,
            disabled_trails=0,
            providers=providers,
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # Generate discovery tasks
            tasks = self._generate_discovery_tasks(providers)
            summary.total_tasks = len(tasks)
            
            # Execute tasks based on strategy
            if strategy == OrchestrationStrategy.SEQUENTIAL:
                results = self._execute_tasks_sequential(tasks)
            elif strategy == OrchestrationStrategy.PARALLEL:
                results = self._execute_tasks_parallel(tasks)
            elif strategy == OrchestrationStrategy.PRIORITY_BASED:
                results = self._execute_tasks_priority(tasks)
            else:
                raise ValueError(f"Unknown orchestration strategy: {strategy}")
            
            # Process results
            self._process_discovery_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed audit discovery orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute audit discovery orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def orchestrate_audit_collection(
        self,
        providers: List[str],
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> AuditOrchestrationSummary:
        """Orchestrate audit event collection across providers"""
        
        if not orchestration_id:
            orchestration_id = f"collection-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting audit collection orchestration {orchestration_id} for providers: {providers}")
        
        # Create orchestration summary
        summary = AuditOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_events=0,
            total_trails=0,
            enabled_trails=0,
            disabled_trails=0,
            providers=providers,
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # Generate collection tasks
            tasks = self._generate_collection_tasks(providers, start_time, end_time, event_types, filters)
            summary.total_tasks = len(tasks)
            
            # Execute tasks based on strategy
            if strategy == OrchestrationStrategy.SEQUENTIAL:
                results = self._execute_tasks_sequential(tasks)
            elif strategy == OrchestrationStrategy.PARALLEL:
                results = self._execute_tasks_parallel(tasks)
            elif strategy == OrchestrationStrategy.PRIORITY_BASED:
                results = self._execute_tasks_priority(tasks)
            else:
                raise ValueError(f"Unknown orchestration strategy: {strategy}")
            
            # Process results
            self._process_collection_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed audit collection orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute audit collection orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def _generate_discovery_tasks(self, providers: List[str]) -> List[OrchestrationTask]:
        """Generate audit trail discovery tasks"""
        tasks = []
        
        for provider in providers:
            task = OrchestrationTask(
                task_id=f"task-{provider}-discovery-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                provider=provider,
                action="discover_trails",
                parameters={},
                priority="high",
                status="pending",
                created_at=datetime.utcnow()
            )
            tasks.append(task)
        
        return tasks
    
    def _generate_collection_tasks(
        self,
        providers: List[str],
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]],
        filters: Optional[Dict[str, Any]]
    ) -> List[OrchestrationTask]:
        """Generate audit event collection tasks"""
        tasks = []
        
        for provider in providers:
            task = OrchestrationTask(
                task_id=f"task-{provider}-collection-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                provider=provider,
                action="collect_events",
                parameters={
                    'start_time': start_time,
                    'end_time': end_time,
                    'event_types': event_types,
                    'filters': filters
                },
                priority="high",
                status="pending",
                created_at=datetime.utcnow()
            )
            tasks.append(task)
        
        return tasks
    
    def _execute_tasks_sequential(self, tasks: List[OrchestrationTask]) -> List[OrchestrationResult]:
        """Execute tasks sequentially"""
        results = []
        
        for task in tasks:
            try:
                result = self._execute_single_task(task)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to execute task {task.task_id}: {e}")
                results.append(OrchestrationResult(
                    task_id=task.task_id,
                    provider=task.provider,
                    action=task.action,
                    status="failed",
                    success=False,
                    error=str(e),
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                ))
        
        return results
    
    def _execute_tasks_parallel(self, tasks: List[OrchestrationTask]) -> List[OrchestrationResult]:
        """Execute tasks in parallel"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._execute_single_task, task): task
                for task in tasks
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to execute task {task.task_id}: {e}")
                    results.append(OrchestrationResult(
                        task_id=task.task_id,
                        provider=task.provider,
                        action=task.action,
                        status="failed",
                        success=False,
                        error=str(e),
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    ))
        
        return results
    
    def _execute_tasks_priority(self, tasks: List[OrchestrationTask]) -> List[OrchestrationResult]:
        """Execute tasks based on priority"""
        # Sort tasks by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 3))
        
        # Execute high priority tasks in parallel, then medium, then low
        results = []
        current_priority = None
        current_batch = []
        
        for task in tasks:
            if current_priority is None:
                current_priority = task.priority
                current_batch.append(task)
            elif task.priority == current_priority:
                current_batch.append(task)
            else:
                # Execute current batch
                batch_results = self._execute_tasks_parallel(current_batch)
                results.extend(batch_results)
                
                # Start new batch
                current_priority = task.priority
                current_batch = [task]
        
        # Execute last batch
        if current_batch:
            batch_results = self._execute_tasks_parallel(current_batch)
            results.extend(batch_results)
        
        return results
    
    def _execute_single_task(self, task: OrchestrationTask) -> OrchestrationResult:
        """Execute a single audit task"""
        start_time = datetime.utcnow()
        
        try:
            handler = self.handlers.get(task.provider)
            if not handler:
                raise ValueError(f"No handler available for provider: {task.provider}")
            
            if task.action == "discover_trails":
                trails = handler.discover_audit_trails()
                result_data = {
                    'trails': [asdict(trail) for trail in trails],
                    'count': len(trails),
                    'enabled': len([t for t in trails if t.enabled]),
                    'disabled': len([t for t in trails if not t.enabled])
                }
            elif task.action == "collect_events":
                start_time_param = task.parameters['start_time']
                end_time_param = task.parameters['end_time']
                event_types = task.parameters.get('event_types')
                filters = task.parameters.get('filters')
                
                events = handler.collect_audit_events(start_time_param, end_time_param, event_types, filters)
                result_data = {
                    'events': [asdict(event) for event in events],
                    'count': len(events),
                    'event_types': list(set(e.event_type for e in events)),
                    'users': list(set(e.user_id for e in events)),
                    'resources': list(set(e.resource_id for e in events))
                }
            else:
                raise ValueError(f"Unknown task action: {task.action}")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return OrchestrationResult(
                task_id=task.task_id,
                provider=task.provider,
                action=task.action,
                status="completed",
                success=True,
                result=result_data,
                execution_time=execution_time,
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return OrchestrationResult(
                task_id=task.task_id,
                provider=task.provider,
                action=task.action,
                status="failed",
                success=False,
                error=str(e),
                execution_time=execution_time,
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def _process_discovery_results(self, results: List[OrchestrationResult], summary: AuditOrchestrationSummary):
        """Process discovery results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate trail information
        total_trails = 0
        enabled_trails = 0
        disabled_trails = 0
        
        for result in results:
            if result.success and result.result:
                total_trails += result.result.get('count', 0)
                enabled_trails += result.result.get('enabled', 0)
                disabled_trails += result.result.get('disabled', 0)
        
        summary.total_trails = total_trails
        summary.enabled_trails = enabled_trails
        summary.disabled_trails = disabled_trails
    
    def _process_collection_results(self, results: List[OrchestrationResult], summary: AuditOrchestrationSummary):
        """Process collection results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate event information
        total_events = 0
        
        for result in results:
            if result.success and result.result:
                total_events += result.result.get('count', 0)
        
        summary.total_events = total_events
    
    def orchestrate_audit_reporting(
        self,
        providers: List[str],
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        output_format: str = "json",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orchestrate comprehensive audit reporting"""
        
        logger.info(f"Starting audit reporting for providers: {providers}")
        
        try:
            # Execute audit collection
            collection_summary = self.orchestrate_audit_collection(
                providers, start_time, end_time, event_types, filters
            )
            
            # Generate comprehensive report
            report = self._generate_audit_report(collection_summary, output_format)
            
            # Save report if requested
            if output_file:
                self._save_report(report, output_file, output_format)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            raise
    
    def _generate_audit_report(self, summary: AuditOrchestrationSummary, output_format: str) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        
        # Collect all results for this orchestration
        orchestration_results = [r for r in self.results if r.provider in summary.providers]
        
        report = {
            'report_metadata': {
                'report_id': f"report-{summary.orchestration_id}",
                'generated_at': datetime.utcnow().isoformat(),
                'providers': summary.providers,
                'format': output_format
            },
            'executive_summary': {
                'total_events': summary.total_events,
                'total_trails': summary.total_trails,
                'enabled_trails': summary.enabled_trails,
                'disabled_trails': summary.disabled_trails,
                'collection_success_rate': (summary.successful_tasks / summary.total_tasks * 100) if summary.total_tasks > 0 else 0,
                'status': 'healthy' if summary.failed_tasks == 0 else 'warning' if summary.failed_tasks < summary.total_tasks else 'critical'
            },
            'provider_analysis': {},
            'event_analysis': {
                'event_types': {},
                'user_activity': {},
                'resource_activity': {},
                'severity_distribution': {},
                'compliance_coverage': {}
            },
            'security_findings': {
                'high_risk_events': [],
                'failed_login_attempts': [],
                'privilege_escalation': [],
                'unusual_patterns': []
            },
            'compliance_analysis': {
                'framework_coverage': {},
                'violations': [],
                'gaps': []
            },
            'recommendations': []
        }
        
        # Analyze by provider
        for provider in summary.providers:
            provider_results = [r for r in orchestration_results if r.provider == provider and r.action == "collect_events"]
            provider_events = sum(r.result.get('count', 0) for r in provider_results if r.success and r.result)
            provider_success = len([r for r in provider_results if r.success])
            provider_total = len(provider_results)
            
            report['provider_analysis'][provider] = {
                'total_events': provider_events,
                'success_rate': (provider_success / provider_total * 100) if provider_total > 0 else 0,
                'status': 'healthy' if provider_success == provider_total else 'warning' if provider_success > 0 else 'critical'
            }
        
        # Aggregate event analysis from results
        all_events = []
        for result in orchestration_results:
            if result.success and result.action == "collect_events" and result.result:
                # Convert event dicts back to objects for analysis
                for event_dict in result.result.get('events', []):
                    # Simplified event representation for analysis
                    all_events.append({
                        'event_type': event_dict.get('event_type'),
                        'user_id': event_dict.get('user_id'),
                        'resource_id': event_dict.get('resource_id'),
                        'severity': event_dict.get('severity'),
                        'compliance_tags': event_dict.get('compliance_tags', []),
                        'timestamp': event_dict.get('timestamp')
                    })
        
        # Event type distribution
        event_types = {}
        for event in all_events:
            event_type = event.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        report['event_analysis']['event_types'] = event_types
        
        # User activity
        user_activity = {}
        for event in all_events:
            user_id = event.get('user_id', 'unknown')
            user_activity[user_id] = user_activity.get(user_id, 0) + 1
        report['event_analysis']['user_activity'] = dict(sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Resource activity
        resource_activity = {}
        for event in all_events:
            resource_id = event.get('resource_id', 'unknown')
            resource_activity[resource_id] = resource_activity.get(resource_id, 0) + 1
        report['event_analysis']['resource_activity'] = dict(sorted(resource_activity.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Severity distribution
        severity_distribution = {}
        for event in all_events:
            severity = event.get('severity', 'unknown')
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        report['event_analysis']['severity_distribution'] = severity_distribution
        
        # Compliance coverage
        compliance_coverage = {}
        for event in all_events:
            for tag in event.get('compliance_tags', []):
                compliance_coverage[tag] = compliance_coverage.get(tag, 0) + 1
        report['event_analysis']['compliance_coverage'] = compliance_coverage
        
        # Generate recommendations
        recommendations = self._generate_audit_recommendations(report)
        report['recommendations'] = recommendations
        
        return report
    
    def _generate_audit_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate audit recommendations"""
        recommendations = []
        
        # Collection health recommendations
        success_rate = report['executive_summary']['collection_success_rate']
        if success_rate < 100:
            recommendations.append(f"Address collection failures - only {success_rate:.1f}% of tasks succeeded")
        
        # Trail coverage recommendations
        if report['executive_summary']['disabled_trails'] > 0:
            recommendations.append(f"Enable {report['executive_summary']['disabled_trails']} disabled audit trails")
        
        # Event volume recommendations
        total_events = report['executive_summary']['total_events']
        if total_events == 0:
            recommendations.append("CRITICAL: No audit events collected - check trail configuration")
        elif total_events < 100:
            recommendations.append("Low event volume detected - verify audit trail coverage")
        
        # Security recommendations
        critical_events = report['event_analysis']['severity_distribution'].get('critical', 0)
        high_events = report['event_analysis']['severity_distribution'].get('high', 0)
        
        if critical_events > 0:
            recommendations.append(f"URGENT: Investigate {critical_events} critical security events")
        
        if high_events > 10:
            recommendations.append(f"Review {high_events} high-severity events for security risks")
        
        # Compliance recommendations
        compliance_coverage = report['event_analysis']['compliance_coverage']
        if not compliance_coverage:
            recommendations.append("Add compliance tags to audit events for better coverage tracking")
        
        # Provider-specific recommendations
        for provider, analysis in report['provider_analysis'].items():
            if analysis['success_rate'] < 100:
                recommendations.append(f"Fix {provider.upper()} audit collection issues - {analysis['success_rate']:.1f}% success rate")
        
        if not recommendations:
            recommendations.append("Audit trail system appears healthy. Continue monitoring.")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any], output_file: str, output_format: str):
        """Save audit report to file"""
        try:
            if output_format.lower() == "json":
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif output_format.lower() == "csv":
                # Simplified CSV export
                import csv
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write executive summary
                    writer.writerow(['Metric', 'Value'])
                    for key, value in report['executive_summary'].items():
                        writer.writerow([key, value])
                    
                    # Write provider analysis
                    writer.writerow([])
                    writer.writerow(['Provider', 'Events', 'Success Rate', 'Status'])
                    for provider, data in report['provider_analysis'].items():
                        writer.writerow([provider, data['total_events'], f"{data['success_rate']:.1f}%", data['status']])
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            logger.info(f"Audit report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise
    
    def orchestrate_continuous_monitoring(
        self,
        providers: List[str],
        interval_hours: int = 1
    ) -> Dict[str, Any]:
        """Orchestrate continuous audit monitoring"""
        
        logger.info(f"Starting continuous audit monitoring with {interval_hours}h interval")
        
        monitoring_config = {
            'monitoring_id': f"monitoring-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'providers': providers,
            'interval_hours': interval_hours,
            'last_run': None,
            'next_run': datetime.utcnow() + timedelta(hours=interval_hours),
            'status': 'active'
        }
        
        # In a real implementation, this would set up a scheduler
        # For now, just run one collection and return config
        
        collection_summary = self.orchestrate_audit_collection(
            providers,
            datetime.utcnow() - timedelta(hours=interval_hours),
            datetime.utcnow()
        )
        
        monitoring_config['last_run'] = collection_summary.start_time.isoformat()
        monitoring_config['last_collection'] = asdict(collection_summary)
        
        return monitoring_config
    
    def orchestrate_audit_trail_management(
        self,
        providers: List[str],
        action: str,
        trail_configs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Orchestrate audit trail management operations"""
        
        logger.info(f"Starting audit trail management: {action}")
        
        results = {}
        
        for provider in providers:
            try:
                handler = self.handlers.get(provider)
                if not handler:
                    logger.warning(f"No handler available for {provider}")
                    continue
                
                if action == "discover":
                    trails = handler.discover_audit_trails()
                    results[provider] = {
                        'action': action,
                        'success': True,
                        'trails': [asdict(trail) for trail in trails],
                        'count': len(trails)
                    }
                elif action == "create" and trail_configs:
                    created_trails = []
                    for config in trail_configs:
                        trail = handler.create_audit_trail(config)
                        if trail:
                            created_trails.append(asdict(trail))
                    
                    results[provider] = {
                        'action': action,
                        'success': True,
                        'created_trails': created_trails,
                        'count': len(created_trails)
                    }
                else:
                    results[provider] = {
                        'action': action,
                        'success': False,
                        'error': f"Unsupported action or missing configuration: {action}"
                    }
                
            except Exception as e:
                logger.error(f"Failed to execute {action} for {provider}: {e}")
                results[provider] = {
                    'action': action,
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def get_orchestration_status(self, orchestration_id: str) -> Optional[AuditOrchestrationSummary]:
        """Get status of a specific orchestration"""
        return self.orchestrations.get(orchestration_id)
    
    def get_all_orchestrations(self) -> Dict[str, AuditOrchestrationSummary]:
        """Get all orchestrations"""
        return self.orchestrations
    
    def cleanup_completed_orchestrations(self, older_than_days: int = 7):
        """Clean up old completed orchestrations"""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        to_remove = []
        for orch_id, summary in self.orchestrations.items():
            if summary.end_time and summary.end_time < cutoff_date:
                to_remove.append(orch_id)
        
        for orch_id in to_remove:
            del self.orchestrations[orch_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old orchestrations")
