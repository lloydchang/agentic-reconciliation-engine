#!/usr/bin/env python3
"""
Multi-Cloud Compliance Orchestrator

Orchestrates compliance operations across multiple cloud providers
to ensure consistent compliance reporting and audit management.
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

from compliance_reporter_handler import (
    ComplianceHandler, ComplianceRequirement, ComplianceCheck,
    get_compliance_handler
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
    framework: str
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
    framework: str
    action: str
    status: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ComplianceOrchestrationSummary:
    orchestration_id: str
    total_tasks: int
    completed_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_checks: int
    compliant_checks: int
    non_compliant_checks: int
    partial_compliance_checks: int
    overall_compliance_score: float
    frameworks: List[str]
    providers: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "in_progress"

class MultiCloudComplianceOrchestrator:
    """Orchestrates compliance operations across multiple cloud providers"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.handlers: Dict[str, ComplianceHandler] = {}
        self.tasks: List[OrchestrationTask] = []
        self.results: List[OrchestrationResult] = []
        self.orchestrations: Dict[str, ComplianceOrchestrationSummary] = {}
        
    def initialize_handlers(self, providers: List[str], regions: Dict[str, str]) -> bool:
        """Initialize compliance handlers for all providers"""
        try:
            success = True
            
            for provider in providers:
                region = regions.get(provider, "us-west-2")
                handler = get_compliance_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    logger.info(f"Initialized {provider} compliance handler")
                else:
                    logger.error(f"Failed to initialize {provider} compliance handler")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            return False
    
    def orchestrate_compliance_assessment(
        self,
        frameworks: List[str],
        providers: List[str],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> ComplianceOrchestrationSummary:
        """Orchestrate compliance assessment across frameworks and providers"""
        
        if not orchestration_id:
            orchestration_id = f"compliance-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting compliance orchestration {orchestration_id} for frameworks: {frameworks}, providers: {providers}")
        
        # Create orchestration summary
        summary = ComplianceOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_checks=0,
            compliant_checks=0,
            non_compliant_checks=0,
            partial_compliance_checks=0,
            overall_compliance_score=0.0,
            frameworks=frameworks,
            providers=providers,
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # Generate tasks
            tasks = self._generate_compliance_tasks(frameworks, providers)
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
            self._process_orchestration_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed compliance orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute compliance orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def _generate_compliance_tasks(self, frameworks: List[str], providers: List[str]) -> List[OrchestrationTask]:
        """Generate compliance assessment tasks"""
        tasks = []
        
        for provider in providers:
            for framework in frameworks:
                # Create task for getting requirements
                task = OrchestrationTask(
                    task_id=f"task-{provider}-{framework}-requirements-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    framework=framework,
                    action="get_requirements",
                    parameters={},
                    priority="high",
                    status="pending",
                    created_at=datetime.utcnow()
                )
                tasks.append(task)
                
                # Create task for executing checks
                task = OrchestrationTask(
                    task_id=f"task-{provider}-{framework}-checks-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    framework=framework,
                    action="execute_checks",
                    parameters={},
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
                    framework=task.framework,
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
                        framework=task.framework,
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
        """Execute a single compliance task"""
        start_time = datetime.utcnow()
        
        try:
            handler = self.handlers.get(task.provider)
            if not handler:
                raise ValueError(f"No handler available for provider: {task.provider}")
            
            if task.action == "get_requirements":
                requirements = handler.get_framework_requirements(task.framework, [task.provider])
                result_data = {
                    'requirements': [asdict(req) for req in requirements],
                    'count': len(requirements)
                }
            elif task.action == "execute_checks":
                # First get requirements
                requirements = handler.get_framework_requirements(task.framework, [task.provider])
                # Then execute checks
                checks = handler.execute_compliance_checks(requirements)
                result_data = {
                    'checks': [asdict(check) for check in checks],
                    'count': len(checks),
                    'compliant': len([c for c in checks if c.status == 'compliant']),
                    'non_compliant': len([c for c in checks if c.status == 'non_compliant']),
                    'partial_compliance': len([c for c in checks if c.status == 'partial_compliance'])
                }
            else:
                raise ValueError(f"Unknown task action: {task.action}")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return OrchestrationResult(
                task_id=task.task_id,
                provider=task.provider,
                framework=task.framework,
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
                framework=task.framework,
                action=task.action,
                status="failed",
                success=False,
                error=str(e),
                execution_time=execution_time,
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
    
    def _process_orchestration_results(self, results: List[OrchestrationResult], summary: ComplianceOrchestrationSummary):
        """Process orchestration results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate compliance check results
        total_checks = 0
        compliant_checks = 0
        non_compliant_checks = 0
        partial_compliance_checks = 0
        all_scores = []
        
        for result in results:
            if result.success and result.action == "execute_checks" and result.result:
                total_checks += result.result.get('count', 0)
                compliant_checks += result.result.get('compliant', 0)
                non_compliant_checks += result.result.get('non_compliant', 0)
                partial_compliance_checks += result.result.get('partial_compliance', 0)
                
                # Calculate compliance score
                if result.result.get('count', 0) > 0:
                    score = result.result.get('compliant', 0) / result.result.get('count', 1)
                    all_scores.append(score)
        
        summary.total_checks = total_checks
        summary.compliant_checks = compliant_checks
        summary.non_compliant_checks = non_compliant_checks
        summary.partial_compliance_checks = partial_compliance_checks
        
        # Calculate overall compliance score
        if all_scores:
            summary.overall_compliance_score = statistics.mean(all_scores)
        elif total_checks > 0:
            summary.overall_compliance_score = compliant_checks / total_checks
        else:
            summary.overall_compliance_score = 0.0
    
    def orchestrate_compliance_reporting(
        self,
        frameworks: List[str],
        providers: List[str],
        output_format: str = "json",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orchestrate comprehensive compliance reporting"""
        
        logger.info(f"Starting compliance reporting for frameworks: {frameworks}, providers: {providers}")
        
        try:
            # Execute compliance assessment
            assessment_summary = self.orchestrate_compliance_assessment(frameworks, providers)
            
            # Generate comprehensive report
            report = self._generate_compliance_report(assessment_summary, output_format)
            
            # Save report if requested
            if output_file:
                self._save_report(report, output_file, output_format)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            raise
    
    def _generate_compliance_report(self, summary: ComplianceOrchestrationSummary, output_format: str) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        # Collect all results for this orchestration
        orchestration_results = [r for r in self.results if r.provider in summary.providers and r.framework in summary.frameworks]
        
        report = {
            'report_metadata': {
                'report_id': f"report-{summary.orchestration_id}",
                'generated_at': datetime.utcnow().isoformat(),
                'frameworks': summary.frameworks,
                'providers': summary.providers,
                'format': output_format
            },
            'executive_summary': {
                'overall_compliance_score': summary.overall_compliance_score,
                'total_checks': summary.total_checks,
                'compliant_checks': summary.compliant_checks,
                'non_compliant_checks': summary.non_compliant_checks,
                'partial_compliance_checks': summary.partial_compliance_checks,
                'compliance_percentage': (summary.compliant_checks / summary.total_checks * 100) if summary.total_checks > 0 else 0,
                'status': 'compliant' if summary.overall_compliance_score >= 0.9 else 'non_compliant' if summary.overall_compliance_score < 0.7 else 'partial_compliance'
            },
            'framework_analysis': {},
            'provider_analysis': {},
            'risk_assessment': {
                'high_risk_items': [],
                'medium_risk_items': [],
                'low_risk_items': []
            },
            'recommendations': [],
            'detailed_findings': []
        }
        
        # Analyze by framework
        for framework in summary.frameworks:
            framework_results = [r for r in orchestration_results if r.framework == framework and r.action == "execute_checks"]
            framework_checks = sum(r.result.get('count', 0) for r in framework_results if r.success and r.result)
            framework_compliant = sum(r.result.get('compliant', 0) for r in framework_results if r.success and r.result)
            framework_score = framework_compliant / framework_checks if framework_checks > 0 else 0.0
            
            report['framework_analysis'][framework] = {
                'total_checks': framework_checks,
                'compliant_checks': framework_compliant,
                'compliance_score': framework_score,
                'status': 'compliant' if framework_score >= 0.9 else 'non_compliant' if framework_score < 0.7 else 'partial_compliance'
            }
        
        # Analyze by provider
        for provider in summary.providers:
            provider_results = [r for r in orchestration_results if r.provider == provider and r.action == "execute_checks"]
            provider_checks = sum(r.result.get('count', 0) for r in provider_results if r.success and r.result)
            provider_compliant = sum(r.result.get('compliant', 0) for r in provider_results if r.success and r.result)
            provider_score = provider_compliant / provider_checks if provider_checks > 0 else 0.0
            
            report['provider_analysis'][provider] = {
                'total_checks': provider_checks,
                'compliant_checks': provider_compliant,
                'compliance_score': provider_score,
                'status': 'compliant' if provider_score >= 0.9 else 'non_compliant' if provider_score < 0.7 else 'partial_compliance'
            }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(summary, report)
        report['recommendations'] = recommendations
        
        return report
    
    def _generate_recommendations(self, summary: ComplianceOrchestrationSummary, report: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Overall recommendations
        if summary.overall_compliance_score < 0.7:
            recommendations.append("CRITICAL: Overall compliance is below 70%. Immediate action required.")
        elif summary.overall_compliance_score < 0.9:
            recommendations.append("WARNING: Overall compliance is below 90%. Review and address compliance gaps.")
        
        # Framework-specific recommendations
        for framework, analysis in report['framework_analysis'].items():
            if analysis['compliance_score'] < 0.7:
                recommendations.append(f"CRITICAL: {framework.upper()} compliance is below 70%. Prioritize remediation.")
            elif analysis['compliance_score'] < 0.9:
                recommendations.append(f"REVIEW: {framework.upper()} compliance is below 90%. Address specific gaps.")
        
        # Provider-specific recommendations
        for provider, analysis in report['provider_analysis'].items():
            if analysis['compliance_score'] < 0.7:
                recommendations.append(f"CRITICAL: {provider.upper()} compliance is below 70%. Review provider-specific controls.")
            elif analysis['compliance_score'] < 0.9:
                recommendations.append(f"REVIEW: {provider.upper()} compliance is below 90%. Optimize provider configuration.")
        
        # General recommendations
        if summary.non_compliant_checks > 0:
            recommendations.append(f"Address {summary.non_compliant_checks} non-compliant controls immediately.")
        
        if summary.partial_compliance_checks > 0:
            recommendations.append(f"Review {summary.partial_compliance_checks} partially compliant controls for improvement.")
        
        if not recommendations:
            recommendations.append("Excellent compliance posture! Continue monitoring and maintaining controls.")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any], output_file: str, output_format: str):
        """Save compliance report to file"""
        try:
            if output_format.lower() == "json":
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif output_format.lower() == "csv":
                # Simplified CSV export
                import csv
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Framework', 'Provider', 'Total Checks', 'Compliant', 'Score', 'Status'])
                    
                    for framework, framework_data in report['framework_analysis'].items():
                        for provider, provider_data in report['provider_analysis'].items():
                            writer.writerow([
                                framework,
                                provider,
                                provider_data['total_checks'],
                                provider_data['compliant_checks'],
                                f"{provider_data['compliance_score']:.2%}",
                                provider_data['status']
                            ])
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            logger.info(f"Compliance report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise
    
    def orchestrate_continuous_monitoring(
        self,
        frameworks: List[str],
        providers: List[str],
        interval_hours: int = 24
    ) -> Dict[str, Any]:
        """Orchestrate continuous compliance monitoring"""
        
        logger.info(f"Starting continuous compliance monitoring with {interval_hours}h interval")
        
        monitoring_config = {
            'monitoring_id': f"monitoring-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'frameworks': frameworks,
            'providers': providers,
            'interval_hours': interval_hours,
            'last_run': None,
            'next_run': datetime.utcnow() + timedelta(hours=interval_hours),
            'status': 'active'
        }
        
        # In a real implementation, this would set up a scheduler
        # For now, just run one assessment and return config
        
        assessment_summary = self.orchestrate_compliance_assessment(frameworks, providers)
        monitoring_config['last_run'] = assessment_summary.start_time.isoformat()
        monitoring_config['last_assessment'] = asdict(assessment_summary)
        
        return monitoring_config
    
    def get_orchestration_status(self, orchestration_id: str) -> Optional[ComplianceOrchestrationSummary]:
        """Get status of a specific orchestration"""
        return self.orchestrations.get(orchestration_id)
    
    def get_all_orchestrations(self) -> Dict[str, ComplianceOrchestrationSummary]:
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
