#!/usr/bin/env python3
"""
Multi-Cloud Backup Orchestrator

Orchestrates backup operations across multiple cloud providers
to ensure consistent backup management and disaster recovery.
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

from backup_orchestrator_handler import (
    BackupOrchestratorHandler, BackupResource, BackupJob,
    get_backup_handler
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
class BackupOrchestrationSummary:
    orchestration_id: str
    total_tasks: int
    completed_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_resources: int
    total_backed_up_gb: float
    total_cost: float
    success_rate: float
    providers: List[str]
    resource_types: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "in_progress"

class MultiCloudBackupOrchestrator:
    """Orchestrates backup operations across multiple cloud providers"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.handlers: Dict[str, BackupOrchestratorHandler] = {}
        self.tasks: List[OrchestrationTask] = []
        self.results: List[OrchestrationResult] = []
        self.orchestrations: Dict[str, BackupOrchestrationSummary] = {}
        
    def initialize_handlers(self, providers: List[str], regions: Dict[str, str]) -> bool:
        """Initialize backup handlers for all providers"""
        try:
            success = True
            
            for provider in providers:
                region = regions.get(provider, "us-west-2")
                handler = get_backup_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    logger.info(f"Initialized {provider} backup handler")
                else:
                    logger.error(f"Failed to initialize {provider} backup handler")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            return False
    
    def orchestrate_backup_discovery(
        self,
        providers: List[str],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> BackupOrchestrationSummary:
        """Orchestrate backup resource discovery across providers"""
        
        if not orchestration_id:
            orchestration_id = f"discovery-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting backup discovery orchestration {orchestration_id} for providers: {providers}")
        
        # Create orchestration summary
        summary = BackupOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_resources=0,
            total_backed_up_gb=0.0,
            total_cost=0.0,
            success_rate=0.0,
            providers=providers,
            resource_types=[],
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
            
            logger.info(f"Completed backup discovery orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute backup discovery orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def orchestrate_backup_execution(
        self,
        providers: List[str],
        resource_types: Optional[List[str]] = None,
        backup_type: str = "full",
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> BackupOrchestrationSummary:
        """Orchestrate backup execution across providers"""
        
        if not orchestration_id:
            orchestration_id = f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting backup execution orchestration {orchestration_id} for providers: {providers}")
        
        # Create orchestration summary
        summary = BackupOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_resources=0,
            total_backed_up_gb=0.0,
            total_cost=0.0,
            success_rate=0.0,
            providers=providers,
            resource_types=resource_types or [],
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # First discover resources
            discovery_tasks = self._generate_discovery_tasks(providers)
            discovery_results = self._execute_tasks_parallel(discovery_tasks)
            
            # Collect all discovered resources
            all_resources = []
            for result in discovery_results:
                if result.success and result.result:
                    resources = result.result.get('resources', [])
                    all_resources.extend(resources)
            
            # Filter by resource types if specified
            if resource_types:
                all_resources = [r for r in all_resources if r.resource_type in resource_types]
            
            # Generate backup tasks
            backup_tasks = self._generate_backup_tasks(all_resources, backup_type)
            summary.total_tasks = len(backup_tasks)
            summary.total_resources = len(all_resources)
            
            # Execute backup tasks based on strategy
            if strategy == OrchestrationStrategy.SEQUENTIAL:
                results = self._execute_tasks_sequential(backup_tasks)
            elif strategy == OrchestrationStrategy.PARALLEL:
                results = self._execute_tasks_parallel(backup_tasks)
            elif strategy == OrchestrationStrategy.PRIORITY_BASED:
                results = self._execute_tasks_priority(backup_tasks)
            else:
                raise ValueError(f"Unknown orchestration strategy: {strategy}")
            
            # Process results
            self._process_backup_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed backup execution orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute backup execution orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def orchestrate_backup_verification(
        self,
        backup_jobs: List[Dict[str, Any]],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> BackupOrchestrationSummary:
        """Orchestrate backup verification across providers"""
        
        if not orchestration_id:
            orchestration_id = f"verification-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting backup verification orchestration {orchestration_id}")
        
        # Create orchestration summary
        summary = BackupOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_resources=0,
            total_backed_up_gb=0.0,
            total_cost=0.0,
            success_rate=0.0,
            providers=[],
            resource_types=[],
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # Generate verification tasks
            tasks = self._generate_verification_tasks(backup_jobs)
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
            self._process_verification_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed backup verification orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute backup verification orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def _generate_discovery_tasks(self, providers: List[str]) -> List[OrchestrationTask]:
        """Generate backup resource discovery tasks"""
        tasks = []
        
        for provider in providers:
            task = OrchestrationTask(
                task_id=f"task-{provider}-discovery-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                provider=provider,
                action="discover_resources",
                parameters={},
                priority="high",
                status="pending",
                created_at=datetime.utcnow()
            )
            tasks.append(task)
        
        return tasks
    
    def _generate_backup_tasks(self, resources: List[BackupResource], backup_type: str) -> List[OrchestrationTask]:
        """Generate backup tasks for resources"""
        tasks = []
        
        for resource in resources:
            if not resource.backup_required:
                continue
            
            task = OrchestrationTask(
                task_id=f"task-{resource.resource_id}-backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                provider=resource.provider,
                action="execute_backup",
                parameters={
                    'resource': resource,
                    'backup_type': backup_type
                },
                priority="high" if resource.criticality == "critical" else "medium",
                status="pending",
                created_at=datetime.utcnow()
            )
            tasks.append(task)
        
        return tasks
    
    def _generate_verification_tasks(self, backup_jobs: List[Dict[str, Any]]) -> List[OrchestrationTask]:
        """Generate backup verification tasks"""
        tasks = []
        
        for job_info in backup_jobs:
            provider = job_info.get('provider', 'unknown')
            
            task = OrchestrationTask(
                task_id=f"task-{job_info.get('job_id', 'unknown')}-verification-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                provider=provider,
                action="verify_backup",
                parameters={
                    'job_info': job_info
                },
                priority="medium",
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
        """Execute a single backup task"""
        start_time = datetime.utcnow()
        
        try:
            handler = self.handlers.get(task.provider)
            if not handler:
                raise ValueError(f"No handler available for provider: {task.provider}")
            
            if task.action == "discover_resources":
                resources = handler.discover_backup_resources()
                result_data = {
                    'resources': [asdict(resource) for resource in resources],
                    'count': len(resources),
                    'total_size_gb': sum(r.size_gb for r in resources)
                }
            elif task.action == "execute_backup":
                resource = task.parameters['resource']
                backup_type = task.parameters['backup_type']
                
                # Create a mock job for the backup
                job = BackupJob(
                    job_id=f"job-{task.task_id}",
                    resource_id=resource.resource_id,
                    resource_name=resource.resource_name,
                    resource_type=resource.resource_type,
                    provider=resource.provider,
                    backup_type=backup_type,
                    status="pending",
                    created_at=datetime.utcnow(),
                    started_at=None,
                    completed_at=None,
                    size_gb=resource.size_gb,
                    location="",
                    encryption_enabled=True,
                    compression_enabled=True,
                    verification_enabled=True,
                    retention_days=30,
                    cost_estimate=0.0,
                    metadata={}
                )
                
                backup_result = handler.execute_backup(resource, backup_type, job)
                result_data = {
                    'backup_result': backup_result,
                    'resource_id': resource.resource_id,
                    'backup_type': backup_type,
                    'size_gb': resource.size_gb
                }
            elif task.action == "verify_backup":
                job_info = task.parameters['job_info']
                
                # Create a mock job for verification
                job = BackupJob(
                    job_id=job_info.get('job_id', ''),
                    resource_id=job_info.get('resource_id', ''),
                    resource_name=job_info.get('resource_name', ''),
                    resource_type=job_info.get('resource_type', ''),
                    provider=task.provider,
                    backup_type=job_info.get('backup_type', 'full'),
                    status="completed",
                    created_at=datetime.utcnow(),
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    size_gb=job_info.get('size_gb', 0.0),
                    location=job_info.get('location', ''),
                    encryption_enabled=job_info.get('encryption_enabled', True),
                    compression_enabled=job_info.get('compression_enabled', True),
                    verification_enabled=job_info.get('verification_enabled', True),
                    retention_days=job_info.get('retention_days', 30),
                    cost_estimate=job_info.get('cost_estimate', 0.0),
                    metadata=job_info.get('metadata', {})
                )
                
                verification_result = handler.verify_backup(job)
                result_data = {
                    'verification_result': verification_result,
                    'job_id': job.job_id,
                    'passed': verification_result.get('passed', False)
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
    
    def _process_discovery_results(self, results: List[OrchestrationResult], summary: BackupOrchestrationSummary):
        """Process discovery results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate resource information
        total_resources = 0
        total_size_gb = 0.0
        all_resource_types = set()
        
        for result in results:
            if result.success and result.result:
                total_resources += result.result.get('count', 0)
                total_size_gb += result.result.get('total_size_gb', 0.0)
        
        summary.total_resources = total_resources
        summary.total_backed_up_gb = total_size_gb
        summary.resource_types = list(all_resource_types)
    
    def _process_backup_results(self, results: List[OrchestrationResult], summary: BackupOrchestrationSummary):
        """Process backup results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate backup information
        total_backed_up_gb = 0.0
        total_cost = 0.0
        
        for result in results:
            if result.success and result.result:
                total_backed_up_gb += result.result.get('size_gb', 0.0)
                # Simplified cost calculation
                backup_cost = result.result.get('size_gb', 0.0) * 0.023  # $0.023 per GB
                total_cost += backup_cost
        
        summary.total_backed_up_gb = total_backed_up_gb
        summary.total_cost = total_cost
        summary.success_rate = (summary.successful_tasks / summary.total_tasks * 100) if summary.total_tasks > 0 else 0.0
    
    def _process_verification_results(self, results: List[OrchestrationResult], summary: BackupOrchestrationSummary):
        """Process verification results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Calculate verification success rate
        passed_verifications = 0
        for result in results:
            if result.success and result.result:
                if result.result.get('passed', False):
                    passed_verifications += 1
        
        summary.success_rate = (passed_verifications / summary.total_tasks * 100) if summary.total_tasks > 0 else 0.0
    
    def orchestrate_backup_cleanup(
        self,
        providers: List[str],
        retention_days: int = 30,
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> BackupOrchestrationSummary:
        """Orchestrate backup cleanup across providers"""
        
        if not orchestration_id:
            orchestration_id = f"cleanup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting backup cleanup orchestration {orchestration_id}")
        
        # Create orchestration summary
        summary = BackupOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_resources=0,
            total_backed_up_gb=0.0,
            total_cost=0.0,
            success_rate=0.0,
            providers=providers,
            resource_types=[],
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # Generate cleanup tasks
            tasks = self._generate_cleanup_tasks(providers, retention_days)
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
            self._process_cleanup_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed backup cleanup orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute backup cleanup orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def _generate_cleanup_tasks(self, providers: List[str], retention_days: int) -> List[OrchestrationTask]:
        """Generate backup cleanup tasks"""
        tasks = []
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        for provider in providers:
            task = OrchestrationTask(
                task_id=f"task-{provider}-cleanup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                provider=provider,
                action="cleanup_backups",
                parameters={
                    'cutoff_date': cutoff_date
                },
                priority="medium",
                status="pending",
                created_at=datetime.utcnow()
            )
            tasks.append(task)
        
        return tasks
    
    def _process_cleanup_results(self, results: List[OrchestrationResult], summary: BackupOrchestrationSummary):
        """Process cleanup results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate cleanup information
        total_deleted = 0
        space_freed_gb = 0.0
        
        for result in results:
            if result.success and result.result:
                total_deleted += result.result.get('deleted_count', 0)
                space_freed_gb += result.result.get('space_freed_gb', 0.0)
        
        summary.total_resources = total_deleted
        summary.total_backed_up_gb = space_freed_gb
    
    def orchestrate_continuous_monitoring(
        self,
        providers: List[str],
        interval_hours: int = 24
    ) -> Dict[str, Any]:
        """Orchestrate continuous backup monitoring"""
        
        logger.info(f"Starting continuous backup monitoring with {interval_hours}h interval")
        
        monitoring_config = {
            'monitoring_id': f"monitoring-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'providers': providers,
            'interval_hours': interval_hours,
            'last_run': None,
            'next_run': datetime.utcnow() + timedelta(hours=interval_hours),
            'status': 'active'
        }
        
        # In a real implementation, this would set up a scheduler
        # For now, just run one discovery and return config
        
        discovery_summary = self.orchestrate_backup_discovery(providers)
        
        monitoring_config['last_run'] = discovery_summary.start_time.isoformat()
        monitoring_config['last_discovery'] = asdict(discovery_summary)
        
        return monitoring_config
    
    def generate_backup_report(self, orchestrations: List[str], output_format: str = "json") -> Dict[str, Any]:
        """Generate comprehensive backup report"""
        try:
            # Collect all orchestration summaries
            summaries = []
            for orch_id in orchestrations:
                summary = self.get_orchestration_status(orch_id)
                if summary:
                    summaries.append(asdict(summary))
            
            # Generate report
            report = {
                'report_metadata': {
                    'report_id': f"backup-report-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    'generated_at': datetime.utcnow().isoformat(),
                    'orchestrations_analyzed': len(summaries),
                    'format': output_format
                },
                'executive_summary': {
                    'total_orchestrations': len(summaries),
                    'total_tasks': sum(s['total_tasks'] for s in summaries),
                    'successful_tasks': sum(s['successful_tasks'] for s in summaries),
                    'failed_tasks': sum(s['failed_tasks'] for s in summaries),
                    'overall_success_rate': 0.0,
                    'total_resources_backed_up': sum(s['total_resources'] for s in summaries),
                    'total_data_backed_up_gb': sum(s['total_backed_up_gb'] for s in summaries),
                    'total_cost': sum(s['total_cost'] for s in summaries)
                },
                'provider_analysis': {},
                'orchestration_types': {},
                'recommendations': []
            }
            
            # Calculate overall success rate
            total_tasks = report['executive_summary']['total_tasks']
            successful_tasks = report['executive_summary']['successful_tasks']
            report['executive_summary']['overall_success_rate'] = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            
            # Analyze by provider
            provider_data = {}
            for summary in summaries:
                for provider in summary['providers']:
                    if provider not in provider_data:
                        provider_data[provider] = {
                            'orchestrations': 0,
                            'tasks': 0,
                            'successful_tasks': 0,
                            'failed_tasks': 0,
                            'resources': 0,
                            'data_gb': 0.0,
                            'cost': 0.0
                        }
                    
                    provider_data[provider]['orchestrations'] += 1
                    provider_data[provider]['tasks'] += summary['total_tasks']
                    provider_data[provider]['successful_tasks'] += summary['successful_tasks']
                    provider_data[provider]['failed_tasks'] += summary['failed_tasks']
                    provider_data[provider]['resources'] += summary['total_resources']
                    provider_data[provider]['data_gb'] += summary['total_backed_up_gb']
                    provider_data[provider]['cost'] += summary['total_cost']
            
            report['provider_analysis'] = provider_data
            
            # Generate recommendations
            recommendations = self._generate_backup_recommendations(report)
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate backup report: {e}")
            raise
    
    def _generate_backup_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate backup recommendations based on report data"""
        recommendations = []
        
        success_rate = report['executive_summary']['overall_success_rate']
        
        if success_rate < 95:
            recommendations.append(f"Overall backup success rate ({success_rate:.1f}%) is below 95%. Review failed operations.")
        
        # Cost recommendations
        total_cost = report['executive_summary']['total_cost']
        if total_cost > 1000:
            recommendations.append("Consider implementing backup compression or tiered storage to reduce costs.")
        
        # Provider-specific recommendations
        for provider, data in report['provider_analysis'].items():
            provider_success_rate = (data['successful_tasks'] / data['tasks'] * 100) if data['tasks'] > 0 else 0.0
            if provider_success_rate < 95:
                recommendations.append(f"{provider.upper()} backup success rate ({provider_success_rate:.1f}%) needs improvement.")
        
        if not recommendations:
            recommendations.append("Backup operations are performing well. Continue monitoring and maintenance.")
        
        return recommendations
    
    def get_orchestration_status(self, orchestration_id: str) -> Optional[BackupOrchestrationSummary]:
        """Get status of a specific orchestration"""
        return self.orchestrations.get(orchestration_id)
    
    def get_all_orchestrations(self) -> Dict[str, BackupOrchestrationSummary]:
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

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Cloud Backup Orchestrator")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--strategy", choices=[s.value for s in OrchestrationStrategy],
                       default=OrchestrationStrategy.PARALLEL.value, help="Orchestration strategy")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--action", choices=['discover', 'backup', 'verify', 'cleanup', 'report'],
                       default='discover', help="Action to perform")
    parser.add_argument("--backup-type", default='full',
                       choices=['full', 'incremental', 'differential', 'snapshot'], help="Backup type")
    parser.add_argument("--retention-days", type=int, default=30, help="Retention days for cleanup")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = MultiCloudBackupOrchestrator()
    
    # Initialize handlers
    regions = {
        'aws': 'us-west-2',
        'azure': 'eastus', 
        'gcp': 'us-central1',
        'onprem': 'datacenter-1'
    }
    
    init_success = orchestrator.initialize_handlers(args.providers, regions)
    if not init_success:
        print("Failed to initialize handlers")
        return
    
    # Execute action
    strategy = OrchestrationStrategy(args.strategy)
    
    if args.action == 'discover':
        summary = orchestrator.orchestrate_backup_discovery(args.providers, strategy)
        
        print(f"Backup Discovery Summary:")
        print(f"Orchestration ID: {summary.orchestration_id}")
        print(f"Total Tasks: {summary.total_tasks}")
        print(f"Completed Tasks: {summary.completed_tasks}")
        print(f"Successful Tasks: {summary.successful_tasks}")
        print(f"Failed Tasks: {summary.failed_tasks}")
        print(f"Total Resources: {summary.total_resources}")
        print(f"Total Size: {summary.total_backed_up_gb:.2f} GB")
        print(f"Providers: {', '.join(summary.providers)}")
        print(f"Status: {summary.status}")
        
    elif args.action == 'backup':
        summary = orchestrator.orchestrate_backup_execution(
            args.providers, backup_type=args.backup_type, strategy=strategy
        )
        
        print(f"Backup Execution Summary:")
        print(f"Orchestration ID: {summary.orchestration_id}")
        print(f"Total Tasks: {summary.total_tasks}")
        print(f"Successful Tasks: {summary.successful_tasks}")
        print(f"Failed Tasks: {summary.failed_tasks}")
        print(f"Success Rate: {summary.success_rate:.1f}%")
        print(f"Total Data Backed Up: {summary.total_backed_up_gb:.2f} GB")
        print(f"Total Cost: ${summary.total_cost:.2f}")
        print(f"Status: {summary.status}")
        
    elif args.action == 'verify':
        # Mock backup jobs for verification
        mock_jobs = [
            {'job_id': 'backup-1', 'provider': 'aws', 'resource_id': 'resource-1'},
            {'job_id': 'backup-2', 'provider': 'azure', 'resource_id': 'resource-2'}
        ]
        
        summary = orchestrator.orchestrate_backup_verification(mock_jobs, strategy)
        
        print(f"Backup Verification Summary:")
        print(f"Orchestration ID: {summary.orchestration_id}")
        print(f"Total Tasks: {summary.total_tasks}")
        print(f"Successful Tasks: {summary.successful_tasks}")
        print(f"Failed Tasks: {summary.failed_tasks}")
        print(f"Success Rate: {summary.success_rate:.1f}%")
        print(f"Status: {summary.status}")
        
    elif args.action == 'cleanup':
        summary = orchestrator.orchestrate_backup_cleanup(
            args.providers, retention_days=args.retention_days, strategy=strategy
        )
        
        print(f"Backup Cleanup Summary:")
        print(f"Orchestration ID: {summary.orchestration_id}")
        print(f"Total Tasks: {summary.total_tasks}")
        print(f"Successful Tasks: {summary.successful_tasks}")
        print(f"Failed Tasks: {summary.failed_tasks}")
        print(f"Total Deleted: {summary.total_resources}")
        print(f"Space Freed: {summary.total_backed_up_gb:.2f} GB")
        print(f"Status: {summary.status}")
        
    elif args.action == 'report':
        # Run some operations first to generate data
        discovery_summary = orchestrator.orchestrate_backup_discovery(args.providers, strategy)
        backup_summary = orchestrator.orchestrate_backup_execution(args.providers, strategy=strategy)
        
        report = orchestrator.generate_backup_report([discovery_summary.orchestration_id, backup_summary.orchestration_id])
        
        print(f"Backup Report:")
        print(f"Generated: {report['report_metadata']['generated_at']}")
        print(f"Orchestrations: {report['executive_summary']['total_orchestrations']}")
        print(f"Overall Success Rate: {report['executive_summary']['overall_success_rate']:.1f}%")
        print(f"Total Data Backed Up: {report['executive_summary']['total_data_backed_up_gb']:.2f} GB")
        print(f"Total Cost: ${report['executive_summary']['total_cost']:.2f}")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

if __name__ == "__main__":
    main()
