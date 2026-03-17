#!/usr/bin/env python3
"""
Multi-Cloud Capacity Planning Orchestrator

Orchestrates capacity planning operations across multiple cloud providers
to ensure consistent resource forecasting and optimization.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
import statistics

from capacity_planning_handler import get_capacity_handler, ResourceCapacity

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
class CapacityOrchestrationSummary:
    orchestration_id: str
    total_tasks: int
    completed_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_resources: int
    total_capacity: float
    average_utilization: float
    providers: List[str]
    resource_types: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "in_progress"

class MultiCloudCapacityOrchestrator:
    """Orchestrates capacity planning operations across multiple cloud providers"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.handlers: Dict[str, Any] = {}
        self.tasks: List[OrchestrationTask] = []
        self.results: List[OrchestrationResult] = []
        self.orchestrations: Dict[str, CapacityOrchestrationSummary] = {}
        
    def initialize_handlers(self, providers: List[str], regions: Dict[str, str]) -> bool:
        """Initialize capacity handlers for all providers"""
        try:
            success = True
            
            for provider in providers:
                region = regions.get(provider, "us-west-2")
                handler = get_capacity_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    logger.info(f"Initialized {provider} capacity handler")
                else:
                    logger.error(f"Failed to initialize {provider} capacity handler")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            return False
    
    def orchestrate_capacity_analysis(
        self,
        providers: List[str],
        resource_types: List[str],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> CapacityOrchestrationSummary:
        """Orchestrate capacity analysis across providers"""
        
        if not orchestration_id:
            orchestration_id = f"capacity-analysis-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting capacity analysis orchestration {orchestration_id} for providers: {providers}")
        
        # Create orchestration summary
        summary = CapacityOrchestrationSummary(
            orchestration_id=orchestration_id,
            total_tasks=0,
            completed_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            total_resources=0,
            total_capacity=0.0,
            average_utilization=0.0,
            providers=providers,
            resource_types=resource_types,
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
            
            logger.info(f"Completed capacity analysis orchestration {orchestration_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute capacity analysis orchestration {orchestration_id}: {e}")
            summary.status = "failed"
            summary.end_time = datetime.utcnow()
        
        return summary
    
    def _generate_analysis_tasks(self, providers: List[str], resource_types: List[str]) -> List[OrchestrationTask]:
        """Generate capacity analysis tasks"""
        tasks = []
        
        for provider in providers:
            for resource_type in resource_types:
                task = OrchestrationTask(
                    task_id=f"task-{provider}-{resource_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    action=f"get_{resource_type}_capacity",
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
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._execute_single_task, task): task
                for task in tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
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
        """Execute a single capacity task"""
        start_time = datetime.utcnow()
        
        try:
            handler = self.handlers.get(task.provider)
            if not handler:
                raise ValueError(f"No handler available for provider: {task.provider}")
            
            if task.action == "get_compute_capacity":
                resources = handler.get_compute_capacity()
            elif task.action == "get_storage_capacity":
                resources = handler.get_storage_capacity()
            elif task.action == "get_networking_capacity":
                resources = handler.get_networking_capacity()
            elif task.action == "get_database_capacity":
                resources = handler.get_database_capacity()
            elif task.action == "get_memory_capacity":
                resources = handler.get_memory_capacity()
            else:
                raise ValueError(f"Unknown task action: {task.action}")
            
            result_data = {
                'resources': [asdict(resource) for resource in resources],
                'count': len(resources),
                'total_capacity': sum(r.current_capacity for r in resources),
                'average_utilization': sum(r.current_utilization for r in resources) / len(resources) if resources else 0.0
            }
            
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
    
    def _process_analysis_results(self, results: List[OrchestrationResult], summary: CapacityOrchestrationSummary):
        """Process analysis results and update summary"""
        summary.completed_tasks = len(results)
        summary.successful_tasks = len([r for r in results if r.success])
        summary.failed_tasks = len([r for r in results if not r.success])
        
        # Aggregate resource information
        total_resources = 0
        total_capacity = 0.0
        all_utilizations = []
        
        for result in results:
            if result.success and result.result:
                total_resources += result.result.get('count', 0)
                total_capacity += result.result.get('total_capacity', 0.0)
                avg_util = result.result.get('average_utilization', 0.0)
                if avg_util > 0:
                    all_utilizations.append(avg_util)
        
        summary.total_resources = total_resources
        summary.total_capacity = total_capacity
        
        if all_utilizations:
            summary.average_utilization = statistics.mean(all_utilizations)
    
    def orchestrate_capacity_optimization(
        self,
        providers: List[str],
        optimization_goals: List[str],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PARALLEL,
        orchestration_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orchestrate capacity optimization across providers"""
        
        logger.info(f"Starting capacity optimization for providers: {providers}")
        
        try:
            # First run capacity analysis
            analysis_summary = self.orchestrate_capacity_analysis(
                providers, ['compute', 'storage', 'networking', 'database'], strategy, orchestration_id
            )
            
            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(analysis_summary)
            
            # Create optimization plan
            optimization_plan = {
                'analysis_summary': asdict(analysis_summary),
                'recommendations': recommendations,
                'implementation_roadmap': self._create_implementation_roadmap(recommendations),
                'cost_optimization': self._calculate_cost_optimization(recommendations),
                'risk_assessment': self._assess_optimization_risks(recommendations)
            }
            
            return optimization_plan
            
        except Exception as e:
            logger.error(f"Failed to orchestrate capacity optimization: {e}")
            raise
    
    def _generate_optimization_recommendations(self, summary: CapacityOrchestrationSummary) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []
        
        # Analyze utilization patterns
        if summary.average_utilization > 85:
            recommendations.append({
                'type': 'scale_up',
                'priority': 'high',
                'description': 'High utilization detected - consider scaling up resources',
                'impact': 'performance',
                'estimated_cost_change': '+15-25%'
            })
        elif summary.average_utilization < 30:
            recommendations.append({
                'type': 'scale_down',
                'priority': 'medium',
                'description': 'Low utilization detected - opportunity to scale down and optimize costs',
                'impact': 'cost',
                'estimated_cost_change': '-20-40%'
            })
        
        # Add provider-specific recommendations
        for provider in summary.providers:
            recommendations.append({
                'type': 'provider_optimization',
                'priority': 'medium',
                'description': f'Optimize {provider.upper()} resource allocation for better efficiency',
                'impact': 'cost_performance',
                'provider': provider,
                'estimated_cost_change': '-5-15%'
            })
        
        return recommendations
    
    def _create_implementation_roadmap(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create implementation roadmap for recommendations"""
        roadmap = {
            'immediate': [],
            'week_1': [],
            'month_1': [],
            'quarter_1': []
        }
        
        for rec in recommendations:
            if rec.get('priority') == 'high':
                roadmap['immediate'].append(rec)
            elif rec.get('priority') == 'medium':
                roadmap['week_1'].append(rec)
            else:
                roadmap['month_1'].append(rec)
        
        return roadmap
    
    def _calculate_cost_optimization(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost optimization potential"""
        total_savings = 0.0
        total_investment = 0.0
        
        for rec in recommendations:
            cost_change = rec.get('estimated_cost_change', '0%')
            if cost_change.startswith('-'):
                # Savings
                savings_pct = float(cost_change.replace('%', '').replace('-', ''))
                total_savings += savings_pct
            else:
                # Investment
                investment_pct = float(cost_change.replace('%', '').replace('+', ''))
                total_investment += investment_pct
        
        return {
            'potential_savings': total_savings,
            'required_investment': total_investment,
            'net_impact': total_savings - total_investment,
            'roi_months': (total_investment / total_savings * 12) if total_savings > 0 else None
        }
    
    def _assess_optimization_risks(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risks associated with optimization recommendations"""
        risks = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'mitigation_strategies': []
        }
        
        for rec in recommendations:
            if rec.get('priority') == 'high':
                risks['high_risk'].append(rec)
            elif rec.get('priority') == 'medium':
                risks['medium_risk'].append(rec)
            else:
                risks['low_risk'].append(rec)
        
        # Add mitigation strategies
        if risks['high_risk']:
            risks['mitigation_strategies'].append('Implement high-priority changes during maintenance windows')
        if risks['medium_risk']:
            risks['mitigation_strategies'].append('Monitor performance closely after medium-priority changes')
        
        return risks
    
    def orchestrate_continuous_monitoring(
        self,
        providers: List[str],
        interval_hours: int = 24
    ) -> Dict[str, Any]:
        """Orchestrate continuous capacity monitoring"""
        
        logger.info(f"Starting continuous capacity monitoring with {interval_hours}h interval")
        
        monitoring_config = {
            'monitoring_id': f"monitoring-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'providers': providers,
            'interval_hours': interval_hours,
            'last_run': None,
            'next_run': datetime.utcnow() + timedelta(hours=interval_hours),
            'status': 'active'
        }
        
        # In a real implementation, this would set up a scheduler
        # For now, just run one analysis and return config
        
        analysis_summary = self.orchestrate_capacity_analysis(providers, ['compute', 'storage'])
        
        monitoring_config['last_run'] = analysis_summary.start_time.isoformat()
        monitoring_config['last_analysis'] = asdict(analysis_summary)
        
        return monitoring_config
    
    def get_orchestration_status(self, orchestration_id: str) -> Optional[CapacityOrchestrationSummary]:
        """Get status of a specific orchestration"""
        return self.orchestrations.get(orchestration_id)
    
    def get_all_orchestrations(self) -> Dict[str, CapacityOrchestrationSummary]:
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
    
    parser = argparse.ArgumentParser(description="Multi-Cloud Capacity Planning Orchestrator")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--strategy", choices=[s.value for s in OrchestrationStrategy],
                       default=OrchestrationStrategy.PARALLEL.value, help="Orchestration strategy")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--resource-types", nargs="+",
                       choices=['compute', 'storage', 'networking', 'database', 'memory'],
                       default=['compute', 'storage'], help="Resource types")
    parser.add_argument("--action", choices=['analyze', 'optimize', 'monitor'],
                       default='analyze', help="Action to perform")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = MultiCloudCapacityOrchestrator()
    
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
    if args.action == 'analyze':
        strategy = OrchestrationStrategy(args.strategy)
        summary = orchestrator.orchestrate_capacity_analysis(
            args.providers, args.resource_types, strategy
        )
        
        print(f"Capacity Analysis Summary:")
        print(f"Orchestration ID: {summary.orchestration_id}")
        print(f"Total Tasks: {summary.total_tasks}")
        print(f"Completed Tasks: {summary.completed_tasks}")
        print(f"Successful Tasks: {summary.successful_tasks}")
        print(f"Failed Tasks: {summary.failed_tasks}")
        print(f"Total Resources: {summary.total_resources}")
        print(f"Total Capacity: {summary.total_capacity}")
        print(f"Average Utilization: {summary.average_utilization:.2f}%")
        print(f"Providers: {', '.join(summary.providers)}")
        print(f"Resource Types: {', '.join(summary.resource_types)}")
        print(f"Status: {summary.status}")
        
    elif args.action == 'optimize':
        optimization_plan = orchestrator.orchestrate_capacity_optimization(
            args.providers, ['cost', 'performance']
        )
        
        print(f"Capacity Optimization Plan:")
        print(f"Recommendations: {len(optimization_plan['recommendations'])}")
        for rec in optimization_plan['recommendations']:
            print(f"  - {rec['type']}: {rec['description']}")
        
        print(f"Cost Optimization:")
        cost_opt = optimization_plan['cost_optimization']
        print(f"  Potential Savings: {cost_opt['potential_savings']:.1f}%")
        print(f"  Required Investment: {cost_opt['required_investment']:.1f}%")
        print(f"  Net Impact: {cost_opt['net_impact']:.1f}%")
        
    elif args.action == 'monitor':
        monitoring = orchestrator.orchestrate_continuous_monitoring(
            args.providers, interval_hours=24
        )
        
        print(f"Continuous Monitoring Setup:")
        print(f"Monitoring ID: {monitoring['monitoring_id']}")
        print(f"Providers: {', '.join(monitoring['providers'])}")
        print(f"Interval: {monitoring['interval_hours']} hours")
        print(f"Status: {monitoring['status']}")

if __name__ == "__main__":
    main()
