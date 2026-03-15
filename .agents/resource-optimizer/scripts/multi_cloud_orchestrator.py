#!/usr/bin/env python3
"""
Multi-Cloud Resource Optimizer Orchestrator

Orchestrates resource optimization operations across multiple cloud providers
to ensure consistent resource utilization analysis and optimization.
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

from resource_optimizer_handler import (
    ResourceOptimizerHandler, ResourceUtilization, OptimizationRecommendation,
    get_resource_optimizer_handler
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
class ResourceOptimizationSummary:
    orchestration_id: str
    total_tasks: int
    completed_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_resources: int
    total_optimizations: int
    estimated_savings: float
    success_rate: float
    providers: List[str]
    resource_types: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "in_progress"

class MultiCloudResourceOptimizerOrchestrator:
    """Orchestrates resource optimization operations across multiple cloud providers"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.handlers: Dict[str, ResourceOptimizerHandler] = {}
        self.tasks: List[OrchestrationTask] = []
        self.results: List[OrchestrationResult] = []
        self.orchestrations: Dict[str, ResourceOptimizationSummary] = {}
        
    def initialize_handlers(self, providers: List[str], regions: Dict[str, str]) -> bool:
        """Initialize resource optimizer handlers for all providers"""
        try:
            success = True
            
            for provider in providers:
                region = regions.get(provider, "us-west-2")
                handler = get_resource_optimizer_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    logger.info(f"Initialized {provider} resource optimizer handler")
                else:
                    logger.error(f"Failed to initialize {provider} resource optimizer handler")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            return False
    
    def orchestrate_resource_analysis(
        self,
        providers: List[str],
        resource_types: Optional[List[str]] = None,
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> ResourceOptimizationSummary:
        """Orchestrate resource utilization analysis across providers"""
        
        if not orchestration_id:
            orchestration_id = f"analysis-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting resource analysis orchestration {orchestration_id} for providers: {providers}")
        
        # Create orchestration summary
        summary = ResourceOptimizationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_resources=0,
            total_optimizations=0,
            estimated_savings=0.0,
            success_rate=0.0,
            providers=providers,
            resource_types=resource_types or [],
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # Generate analysis tasks
            tasks = self._generate_analysis_tasks(providers, resource_types)
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
            self._process_analysis_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed resource analysis orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute resource analysis orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def orchestrate_optimization_recommendations(
        self,
        providers: List[str],
        resource_types: Optional[List[str]] = None,
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> ResourceOptimizationSummary:
        """Orchestrate optimization recommendations across providers"""
        
        if not orchestration_id:
            orchestration_id = f"optimization-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting optimization recommendations orchestration {orchestration_id} for providers: {providers}")
        
        # Create orchestration summary
        summary = ResourceOptimizationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_resources=0,
            total_optimizations=0,
            estimated_savings=0.0,
            success_rate=0.0,
            providers=providers,
            resource_types=resource_types or [],
            start_time=datetime.utcnow()
        )
        
        self.orchestrations[orchestration_id] = summary
        
        try:
            # First collect resource utilization data
            analysis_tasks = self._generate_analysis_tasks(providers, resource_types)
            analysis_results = self._execute_tasks_parallel(analysis_tasks)
            
            # Collect all resources from analysis results
            all_resources = []
            for result in analysis_results:
                if result.success and result.result:
                    resources = result.result.get('resources', [])
                    all_resources.extend(resources)
            
            # Generate optimization tasks
            optimization_tasks = self._generate_optimization_tasks(all_resources)
            summary.total_tasks = len(optimization_tasks)
            summary.total_resources = len(all_resources)
            
            # Execute optimization tasks based on strategy
            if strategy == OrchestrationStrategy.SEQUENTIAL:
                results = self._execute_tasks_sequential(optimization_tasks)
            elif strategy == OrchestrationStrategy.PARALLEL:
                results = self._execute_tasks_parallel(optimization_tasks)
            elif strategy == OrchestrationStrategy.PRIORITY_BASED:
                results = self._execute_tasks_priority(optimization_tasks)
            else:
                raise ValueError(f"Unknown orchestration strategy: {strategy}")
            
            # Process results
            self._process_optimization_results(results, summary)
            
            # Update summary
            summary.end_time = datetime.utcnow()
            summary.status = "completed" if summary.failed_tasks == 0 else "completed_with_errors"
            
            logger.info(f"Completed optimization recommendations orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute optimization recommendations orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def orchestrate_continuous_optimization(
        self,
        providers: List[str],
        resource_types: Optional[List[str]] = None,
        interval_hours: int = 24
    ) -> Dict[str, Any]:
        """Orchestrate continuous resource optimization monitoring"""
        
        logger.info(f"Starting continuous resource optimization with {interval_hours}h interval")
        
        monitoring_config = {
            'monitoring_id': f"monitoring-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'providers': providers,
            'resource_types': resource_types or [],
            'interval_hours': interval_hours,
            'last_run': None,
            'next_run': datetime.utcnow() + timedelta(hours=interval_hours),
            'status': 'active'
        }
        
        # In a real implementation, this would set up a scheduler
        # For now, just run one analysis and return config
        
        analysis_summary = self.orchestrate_resource_analysis(providers, resource_types)
        
        monitoring_config['last_run'] = analysis_summary.start_time.isoformat()
        monitoring_config['last_analysis'] = asdict(analysis_summary)
        
        return monitoring_config
    
    def _generate_analysis_tasks(self, providers: List[str], resource_types: Optional[List[str]] = None) -> List[OrchestrationTask]:
        """Generate resource utilization analysis tasks"""
        tasks = []
        
        for provider in providers:
            if not resource_types or 'compute' in resource_types:
                task = OrchestrationTask(
                    task_id=f"task-{provider}-compute-analysis-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    action="get_compute_utilization",
                    parameters={},
                    priority="high",
                    status="pending",
                    created_at=datetime.utcnow()
                )
                tasks.append(task)
            
            if not resource_types or 'storage' in resource_types:
                task = OrchestrationTask(
                    task_id=f"task-{provider}-storage-analysis-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    action="get_storage_utilization",
                    parameters={},
                    priority="high",
                    status="pending",
                    created_at=datetime.utcnow()
                )
                tasks.append(task)
            
            if not resource_types or 'network' in resource_types:
                task = OrchestrationTask(
                    task_id=f"task-{provider}-network-analysis-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    action="get_network_utilization",
                    parameters={},
                    priority="medium",
                    status="pending",
                    created_at=datetime.utcnow()
                )
                tasks.append(task)
            
            if not resource_types or 'database' in resource_types:
                task = OrchestrationTask(
                    task_id=f"task-{provider}-database-analysis-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    action="get_database_utilization",
                    parameters={},
                    priority="high",
                    status="pending",
                    created_at=datetime.utcnow()
                )
                tasks.append(task)
        
        return tasks
    
    def _generate_optimization_tasks(self, resources: List[ResourceUtilization]) -> List[OrchestrationTask]:
        """Generate optimization recommendation tasks"""
        tasks = []
        
        # Group resources by provider
        resources_by_provider = {}
        for resource in resources:
            if resource.provider not in resources_by_provider:
                resources_by_provider[resource.provider] = []
            resources_by_provider[resource.provider].append(resource)
        
        for provider, provider_resources in resources_by_provider.items():
            task = OrchestrationTask(
                task_id=f"task-{provider}-optimization-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                provider=provider,
                action="generate_optimization_recommendations",
                parameters={'resources': provider_resources},
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
        """Execute a single resource optimization task"""
        start_time = datetime.utcnow()
        
        try:
            handler = self.handlers.get(task.provider)
            if not handler:
                raise ValueError(f"No handler available for provider: {task.provider}")
            
            if task.action == "get_compute_utilization":
                resources = handler.get_compute_utilization()
                result_data = {
                    'resources': [asdict(resource) for resource in resources],
                    'count': len(resources),
                    'total_cost': sum(r.monthly_cost for r in resources)
                }
            elif task.action == "get_storage_utilization":
                resources = handler.get_storage_utilization()
                result_data = {
                    'resources': [asdict(resource) for resource in resources],
                    'count': len(resources),
                    'total_cost': sum(r.monthly_cost for r in resources)
                }
            elif task.action == "get_network_utilization":
                resources = handler.get_network_utilization()
                result_data = {
                    'resources': [asdict(resource) for resource in resources],
                    'count': len(resources),
                    'total_cost': sum(r.monthly_cost for r in resources)
                }
            elif task.action == "get_database_utilization":
                resources = handler.get_database_utilization()
                result_data = {
                    'resources': [asdict(resource) for resource in resources],
                    'count': len(resources),
                    'total_cost': sum(r.monthly_cost for r in resources)
                }
            elif task.action == "generate_optimization_recommendations":
                resources = task.parameters['resources']
                recommendations = handler.generate_optimization_recommendations(resources)
                result_data = {
                    'recommendations': [asdict(rec) for rec in recommendations],
                    'count': len(recommendations),
                    'total_savings': sum(rec.estimated_savings for rec in recommendations)
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
    
    def _process_analysis_results(self, results: List[OrchestrationResult], summary: ResourceOptimizationSummary):
        """Process resource analysis results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate resource information
        total_resources = 0
        total_cost = 0.0
        all_resource_types = set()
        
        for result in results:
            if result.success and result.result:
                total_resources += result.result.get('count', 0)
                total_cost += result.result.get('total_cost', 0.0)
        
        summary.total_resources = total_resources
        summary.resource_types = list(all_resource_types)
    
    def _process_optimization_results(self, results: List[OrchestrationResult], summary: ResourceOptimizationSummary):
        """Process optimization results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate optimization information
        total_optimizations = 0
        total_savings = 0.0
        
        for result in results:
            if result.success and result.result:
                total_optimizations += result.result.get('count', 0)
                total_savings += result.result.get('total_savings', 0.0)
        
        summary.total_optimizations = total_optimizations
        summary.estimated_savings = total_savings
        summary.success_rate = (summary.successful_tasks / summary.total_tasks * 100) if summary.total_tasks > 0 else 0.0
    
    def generate_optimization_report(self, orchestrations: List[str], output_format: str = "json") -> Dict[str, Any]:
        """Generate comprehensive resource optimization report"""
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
                    'report_id': f"resource-optimization-report-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
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
                    'total_resources': sum(s['total_resources'] for s in summaries),
                    'total_optimizations': sum(s['total_optimizations'] for s in summaries),
                    'total_estimated_savings': sum(s['estimated_savings'] for s in summaries)
                },
                'provider_analysis': {},
                'resource_type_analysis': {},
                'optimization_opportunities': {},
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
                            'optimizations': 0,
                            'savings': 0.0
                        }
                    
                    provider_data[provider]['orchestrations'] += 1
                    provider_data[provider]['tasks'] += summary['total_tasks']
                    provider_data[provider]['successful_tasks'] += summary['successful_tasks']
                    provider_data[provider]['failed_tasks'] += summary['failed_tasks']
                    provider_data[provider]['resources'] += summary['total_resources']
                    provider_data[provider]['optimizations'] += summary['total_optimizations']
                    provider_data[provider]['savings'] += summary['estimated_savings']
            
            report['provider_analysis'] = provider_data
            
            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(report)
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate resource optimization report: {e}")
            raise
    
    def _generate_optimization_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on report data"""
        recommendations = []
        
        success_rate = report['executive_summary']['overall_success_rate']
        total_savings = report['executive_summary']['total_estimated_savings']
        
        if success_rate < 95:
            recommendations.append(f"Overall optimization success rate ({success_rate:.1f}%) is below 95%. Review failed operations.")
        
        if total_savings > 1000:
            recommendations.append(f"Significant cost savings opportunity detected (${total_savings:.2f}). Prioritize implementation of high-impact recommendations.")
        elif total_savings > 100:
            recommendations.append(f"Moderate cost savings opportunity detected (${total_savings:.2f}). Implement recommendations to optimize costs.")
        else:
            recommendations.append("Limited cost savings opportunities detected. Current resource utilization appears optimized.")
        
        # Provider-specific recommendations
        for provider, data in report['provider_analysis'].items():
            provider_success_rate = (data['successful_tasks'] / data['tasks'] * 100) if data['tasks'] > 0 else 0.0
            if provider_success_rate < 95:
                recommendations.append(f"{provider.upper()} optimization success rate ({provider_success_rate:.1f}%) needs improvement.")
            
            if data['savings'] > 500:
                recommendations.append(f"{provider.upper()} shows significant optimization potential (${data['savings']:.2f}). Focus implementation efforts here.")
        
        if not recommendations:
            recommendations.append("Resource optimization operations are performing well. Continue monitoring and periodic analysis.")
        
        return recommendations
    
    def get_orchestration_status(self, orchestration_id: str) -> Optional[ResourceOptimizationSummary]:
        """Get status of a specific orchestration"""
        return self.orchestrations.get(orchestration_id)
    
    def get_all_orchestrations(self) -> Dict[str, ResourceOptimizationSummary]:
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
    
    parser = argparse.ArgumentParser(description="Multi-Cloud Resource Optimizer Orchestrator")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--strategy", choices=[s.value for s in OrchestrationStrategy],
                       default=OrchestrationStrategy.PARALLEL.value, help="Orchestration strategy")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--resource-types", nargs="+",
                       choices=['compute', 'storage', 'network', 'database'],
                       default=['compute', 'storage'], help="Resource types")
    parser.add_argument("--action", choices=['analyze', 'optimize', 'report'],
                       default='analyze', help="Action to perform")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = MultiCloudResourceOptimizerOrchestrator()
    
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
    
    if args.action == 'analyze':
        summary = orchestrator.orchestrate_resource_analysis(args.providers, args.resource_types, strategy)
        
        print(f"Resource Analysis Summary:")
        print(f"Orchestration ID: {summary.orchestration_id}")
        print(f"Total Tasks: {summary.total_tasks}")
        print(f"Completed Tasks: {summary.completed_tasks}")
        print(f"Successful Tasks: {summary.successful_tasks}")
        print(f"Failed Tasks: {summary.failed_tasks}")
        print(f"Total Resources: {summary.total_resources}")
        print(f"Providers: {', '.join(summary.providers)}")
        print(f"Status: {summary.status}")
        
    elif args.action == 'optimize':
        summary = orchestrator.orchestrate_optimization_recommendations(args.providers, args.resource_types, strategy)
        
        print(f"Optimization Recommendations Summary:")
        print(f"Orchestration ID: {summary.orchestration_id}")
        print(f"Total Tasks: {summary.total_tasks}")
        print(f"Successful Tasks: {summary.successful_tasks}")
        print(f"Failed Tasks: {summary.failed_tasks}")
        print(f"Total Resources: {summary.total_resources}")
        print(f"Total Optimizations: {summary.total_optimizations}")
        print(f"Estimated Savings: ${summary.estimated_savings:.2f}")
        print(f"Success Rate: {summary.success_rate:.1f}%")
        print(f"Status: {summary.status}")
        
    elif args.action == 'report':
        # Run some operations first to generate data
        analysis_summary = orchestrator.orchestrate_resource_analysis(args.providers, args.resource_types, strategy)
        optimization_summary = orchestrator.orchestrate_optimization_recommendations(args.providers, args.resource_types, strategy)
        
        report = orchestrator.generate_optimization_report([analysis_summary.orchestration_id, optimization_summary.orchestration_id])
        
        print(f"Resource Optimization Report:")
        print(f"Generated: {report['report_metadata']['generated_at']}")
        print(f"Orchestrations: {report['executive_summary']['total_orchestrations']}")
        print(f"Overall Success Rate: {report['executive_summary']['overall_success_rate']:.1f}%")
        print(f"Total Resources: {report['executive_summary']['total_resources']}")
        print(f"Total Optimizations: {report['executive_summary']['total_optimizations']}")
        print(f"Total Estimated Savings: ${report['executive_summary']['total_estimated_savings']:.2f}")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

if __name__ == "__main__":
    main()
