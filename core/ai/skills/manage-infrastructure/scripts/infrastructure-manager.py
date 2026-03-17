#!/usr/bin/env python3
"""
Infrastructure Manager Script

Multi-cloud automation for comprehensive infrastructure management across AWS, Azure, GCP, and on-premise environments.
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

class InfrastructureOperation(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SCALE = "scale"
    MONITOR = "monitor"
    BACKUP = "backup"
    RESTORE = "restore"

class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORKING = "networking"
    DATABASE = "database"
    SECURITY = "security"
    MONITORING = "monitoring"

@dataclass
class InfrastructureResource:
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    region: str
    status: str
    configuration: Dict[str, Any]
    tags: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    cost: float
    dependencies: List[str]

@dataclass
class InfrastructureOperation:
    operation_id: str
    operation_type: InfrastructureOperation
    resource_id: str
    resource_type: ResourceType
    provider: str
    status: str
    progress: float
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    configuration: Dict[str, Any]

@dataclass
class InfrastructurePlan:
    plan_id: str
    name: str
    description: str
    provider: str
    operations: List[InfrastructureOperation]
    created_at: datetime
    estimated_cost: float
    estimated_duration: timedelta
    dependencies: List[str]

class InfrastructureManager:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.resources = {}
        self.operations = {}
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load infrastructure management configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'management_settings': {
                'auto_approve_safe_operations': True,
                'require_approval_for_destructive': True,
                'backup_before_modification': True,
                'monitoring_enabled': True,
                'cost_tracking_enabled': True
            },
            'resource_limits': {
                'max_concurrent_operations': 10,
                'operation_timeout_minutes': 60,
                'retry_attempts': 3
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
    
    def discover_infrastructure(self, providers: List[str], resource_types: List[ResourceType]) -> Dict[str, List[InfrastructureResource]]:
        """Discover existing infrastructure across providers"""
        logger.info(f"Discovering infrastructure for providers: {providers}")
        
        discovered_resources = {}
        
        for provider in providers:
            if provider not in self.config['providers']:
                logger.warning(f"Provider {provider} not in configuration")
                continue
            
            if not self.config['providers'][provider]['enabled']:
                logger.info(f"Provider {provider} is disabled")
                continue
            
            try:
                # Initialize provider handler
                handler = self._get_provider_handler(provider)
                if not handler.initialize_client():
                    raise RuntimeError(f"Failed to initialize {provider} handler")
                
                # Discover resources
                provider_resources = []
                for resource_type in resource_types:
                    resources = self._discover_resources(handler, resource_type)
                    provider_resources.extend(resources)
                
                discovered_resources[provider] = provider_resources
                logger.info(f"Discovered {len(provider_resources)} resources for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to discover infrastructure for {provider}: {e}")
                discovered_resources[provider] = []
        
        return discovered_resources
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific infrastructure handler"""
        from infrastructure_manager_handler import get_infrastructure_handler
        region = self.config['providers'][provider]['region']
        return get_infrastructure_handler(provider, region)
    
    def _discover_resources(self, handler, resource_type: ResourceType) -> List[InfrastructureResource]:
        """Discover resources of a specific type"""
        try:
            if resource_type == ResourceType.COMPUTE:
                return handler.get_compute_resources()
            elif resource_type == ResourceType.STORAGE:
                return handler.get_storage_resources()
            elif resource_type == ResourceType.NETWORKING:
                return handler.get_networking_resources()
            elif resource_type == ResourceType.DATABASE:
                return handler.get_database_resources()
            elif resource_type == ResourceType.SECURITY:
                return handler.get_security_resources()
            elif resource_type == ResourceType.MONITORING:
                return handler.get_monitoring_resources()
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
                
        except Exception as e:
            logger.error(f"Failed to discover {resource_type.value} resources: {e}")
            return []
    
    def create_infrastructure_plan(self, plan_name: str, description: str, provider: str,
                                  operations: List[Dict[str, Any]]) -> InfrastructurePlan:
        """Create an infrastructure management plan"""
        logger.info(f"Creating infrastructure plan: {plan_name}")
        
        # Validate provider
        if provider not in self.config['providers']:
            raise ValueError(f"Provider {provider} not configured")
        
        # Convert operation dictionaries to InfrastructureOperation objects
        infrastructure_operations = []
        for i, op_config in enumerate(operations):
            operation = InfrastructureOperation(
                operation_id=f"{plan_name}-op-{i+1}",
                operation_type=InfrastructureOperation(op_config['operation_type']),
                resource_id=op_config.get('resource_id', f"resource-{i+1}"),
                resource_type=ResourceType(op_config['resource_type']),
                provider=provider,
                status='pending',
                progress=0.0,
                started_at=datetime.utcnow(),
                completed_at=None,
                error_message=None,
                configuration=op_config.get('configuration', {})
            )
            infrastructure_operations.append(operation)
        
        # Calculate estimated cost and duration
        estimated_cost = self._calculate_plan_cost(infrastructure_operations)
        estimated_duration = self._calculate_plan_duration(infrastructure_operations)
        
        # Identify dependencies
        dependencies = self._identify_operation_dependencies(infrastructure_operations)
        
        # Create infrastructure plan
        plan = InfrastructurePlan(
            plan_id=f"plan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=plan_name,
            description=description,
            provider=provider,
            operations=infrastructure_operations,
            created_at=datetime.utcnow(),
            estimated_cost=estimated_cost,
            estimated_duration=estimated_duration,
            dependencies=dependencies
        )
        
        return plan
    
    def _calculate_plan_cost(self, operations: List[InfrastructureOperation]) -> float:
        """Calculate estimated cost for infrastructure plan"""
        total_cost = 0.0
        
        for operation in operations:
            if operation.operation_type == InfrastructureOperation.CREATE:
                # Cost based on resource configuration
                resource_config = operation.configuration
                if operation.resource_type == ResourceType.COMPUTE:
                    # Compute cost estimation
                    instance_type = resource_config.get('instance_type', 't3.medium')
                    total_cost += self._get_compute_cost(operation.provider, instance_type)
                elif operation.resource_type == ResourceType.STORAGE:
                    # Storage cost estimation
                    size_gb = resource_config.get('size_gb', 100)
                    storage_type = resource_config.get('storage_type', 'standard')
                    total_cost += self._get_storage_cost(operation.provider, size_gb, storage_type)
                elif operation.resource_type == ResourceType.DATABASE:
                    # Database cost estimation
                    db_class = resource_config.get('db_class', 'db.t3.medium')
                    total_cost += self._get_database_cost(operation.provider, db_class)
        
        return total_cost
    
    def _get_compute_cost(self, provider: str, instance_type: str) -> float:
        """Get compute instance cost per month"""
        # Simplified cost mapping
        cost_mapping = {
            'aws': {
                't3.micro': 7.66, 't3.small': 15.32, 't3.medium': 30.64, 't3.large': 61.28,
                'm5.large': 69.12, 'm5.xlarge': 138.24, 'm5.2xlarge': 276.48,
                'c5.large': 68.46, 'c5.xlarge': 136.92, 'c5.2xlarge': 273.84
            },
            'azure': {
                'Standard_B1s': 7.30, 'Standard_B2s': 29.20, 'Standard_B4ms': 58.40,
                'Standard_D2s_v3': 70.08, 'Standard_D4s_v3': 140.16, 'Standard_D8s_v3': 280.32
            },
            'gcp': {
                'e2-micro': 4.86, 'e2-small': 9.72, 'e2-medium': 19.44, 'e2-standard-2': 38.88,
                'n1-standard-2': 53.06, 'n1-standard-4': 106.12, 'n1-standard-8': 212.24
            }
        }
        
        return cost_mapping.get(provider, {}).get(instance_type, 50.0)
    
    def _get_storage_cost(self, provider: str, size_gb: int, storage_type: str) -> float:
        """Get storage cost per month"""
        # Simplified cost per GB per month
        cost_per_gb = {
            'aws': {'standard': 0.10, 'premium': 0.125, 'cold': 0.025},
            'azure': {'standard': 0.09, 'premium': 0.115, 'cold': 0.02},
            'gcp': {'standard': 0.08, 'premium': 0.10, 'cold': 0.018}
        }
        
        cost = cost_per_gb.get(provider, {}).get(storage_type, 0.10)
        return size_gb * cost
    
    def _get_database_cost(self, provider: str, db_class: str) -> float:
        """Get database cost per month"""
        # Simplified database cost mapping
        cost_mapping = {
            'aws': {
                'db.t3.micro': 11.62, 'db.t3.small': 23.24, 'db.t3.medium': 46.49,
                'db.r5.large': 173.52, 'db.r5.xlarge': 347.04, 'db.r5.2xlarge': 694.08
            },
            'azure': {
                'Basic': 5.00, 'Standard_S2': 25.00, 'Standard_S3': 50.00,
                'Premium_P1': 465.00, 'Premium_P2': 930.00, 'Premium_P6': 2790.00
            },
            'gcp': {
                'db-n1-standard-1': 52.03, 'db-n1-standard-2': 104.06, 'db-n1-standard-4': 208.12,
                'db-n1-standard-8': 416.24, 'db-n1-standard-16': 832.48
            }
        }
        
        return cost_mapping.get(provider, {}).get(db_class, 100.0)
    
    def _calculate_plan_duration(self, operations: List[InfrastructureOperation]) -> timedelta:
        """Calculate estimated duration for infrastructure plan"""
        # Simplified duration estimation based on operation types
        duration_minutes = 0
        
        for operation in operations:
            if operation.operation_type == InfrastructureOperation.CREATE:
                if operation.resource_type == ResourceType.COMPUTE:
                    duration_minutes += 5  # 5 minutes to create compute instance
                elif operation.resource_type == ResourceType.STORAGE:
                    duration_minutes += 2  # 2 minutes to create storage
                elif operation.resource_type == ResourceType.DATABASE:
                    duration_minutes += 10  # 10 minutes to create database
                else:
                    duration_minutes += 3  # Default 3 minutes
            elif operation.operation_type == InfrastructureOperation.UPDATE:
                duration_minutes += 3  # 3 minutes for updates
            elif operation.operation_type == InfrastructureOperation.DELETE:
                duration_minutes += 2  # 2 minutes for deletions
            elif operation.operation_type == InfrastructureOperation.SCALE:
                duration_minutes += 5  # 5 minutes for scaling
            else:
                duration_minutes += 1  # Default 1 minute
        
        return timedelta(minutes=duration_minutes)
    
    def _identify_operation_dependencies(self, operations: List[InfrastructureOperation]) -> List[str]:
        """Identify dependencies between operations"""
        dependencies = []
        
        # Simple dependency rules:
        # 1. Networking resources should be created before compute resources
        # 2. Storage resources should be created before database resources
        # 3. Security resources should be created before other resources
        
        networking_ops = [op for op in operations if op.resource_type == ResourceType.NETWORKING]
        compute_ops = [op for op in operations if op.resource_type == ResourceType.COMPUTE]
        storage_ops = [op for op in operations if op.resource_type == ResourceType.STORAGE]
        database_ops = [op for op in operations if op.resource_type == ResourceType.DATABASE]
        
        for net_op in networking_ops:
            for comp_op in compute_ops:
                dependencies.append(f"{comp_op.operation_id} depends on {net_op.operation_id}")
        
        for stor_op in storage_ops:
            for db_op in database_ops:
                dependencies.append(f"{db_op.operation_id} depends on {stor_op.operation_id}")
        
        return dependencies
    
    def execute_infrastructure_plan(self, plan: InfrastructurePlan) -> Dict[str, Any]:
        """Execute an infrastructure management plan"""
        logger.info(f"Executing infrastructure plan: {plan.name}")
        
        # Initialize provider handler
        handler = self._get_provider_handler(plan.provider)
        if not handler.initialize_client():
            raise RuntimeError(f"Failed to initialize {plan.provider} handler")
        
        # Check for approval requirements
        if self._requires_approval(plan):
            logger.warning(f"Plan {plan.name} requires approval before execution")
            return {
                'status': 'requires_approval',
                'plan_id': plan.plan_id,
                'message': 'Plan requires manual approval due to destructive operations'
            }
        
        # Execute operations in dependency order
        execution_results = []
        completed_operations = set()
        
        # Sort operations by dependencies
        sorted_operations = self._sort_operations_by_dependencies(plan.operations, plan.dependencies)
        
        for operation in sorted_operations:
            try:
                # Check if dependencies are satisfied
                if not self._dependencies_satisfied(operation, completed_operations, plan.dependencies):
                    logger.info(f"Skipping {operation.operation_id} - dependencies not satisfied")
                    continue
                
                # Execute operation
                result = self._execute_operation(handler, operation)
                execution_results.append(result)
                
                if result['status'] == 'success':
                    completed_operations.add(operation.operation_id)
                else:
                    logger.error(f"Operation {operation.operation_id} failed: {result.get('error')}")
                    # Continue with other operations for now
                
            except Exception as e:
                logger.error(f"Failed to execute operation {operation.operation_id}: {e}")
                execution_results.append({
                    'operation_id': operation.operation_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Calculate execution summary
        success_count = len([r for r in execution_results if r['status'] == 'success'])
        error_count = len([r for r in execution_results if r['status'] == 'error'])
        
        return {
            'status': 'completed',
            'plan_id': plan.plan_id,
            'total_operations': len(plan.operations),
            'successful_operations': success_count,
            'failed_operations': error_count,
            'execution_results': execution_results,
            'completed_at': datetime.utcnow().isoformat()
        }
    
    def _requires_approval(self, plan: InfrastructurePlan) -> bool:
        """Check if plan requires approval"""
        if not self.config['management_settings']['require_approval_for_destructive']:
            return False
        
        # Check for destructive operations
        destructive_operations = [InfrastructureOperation.DELETE, InfrastructureOperation.UPDATE]
        
        for operation in plan.operations:
            if operation.operation_type in destructive_operations:
                return True
        
        return False
    
    def _sort_operations_by_dependencies(self, operations: List[InfrastructureOperation], 
                                       dependencies: List[str]) -> List[InfrastructureOperation]:
        """Sort operations based on dependencies"""
        # Simplified topological sort
        operation_order = []
        remaining_ops = operations.copy()
        
        # Add operations without dependencies first
        ops_with_deps = set()
        for dep in dependencies:
            parts = dep.split(' depends on ')
            if len(parts) == 2:
                ops_with_deps.add(parts[0].strip())
        
        # Add operations without dependencies
        for op in remaining_ops[:]:
            if op.operation_id not in ops_with_deps:
                operation_order.append(op)
                remaining_ops.remove(op)
        
        # Add remaining operations
        operation_order.extend(remaining_ops)
        
        return operation_order
    
    def _dependencies_satisfied(self, operation: InfrastructureOperation, 
                              completed_operations: set, dependencies: List[str]) -> bool:
        """Check if operation dependencies are satisfied"""
        for dep in dependencies:
            parts = dep.split(' depends on ')
            if len(parts) == 2:
                dependent_op = parts[0].strip()
                required_op = parts[1].strip()
                
                if dependent_op == operation.operation_id and required_op not in completed_operations:
                    return False
        
        return True
    
    def _execute_operation(self, handler, operation: InfrastructureOperation) -> Dict[str, Any]:
        """Execute a single infrastructure operation"""
        logger.info(f"Executing operation: {operation.operation_id} ({operation.operation_type.value})")
        
        try:
            operation.status = 'running'
            operation.started_at = datetime.utcnow()
            
            result = {}
            
            if operation.operation_type == InfrastructureOperation.CREATE:
                result = handler.create_resource(
                    operation.resource_type,
                    operation.resource_id,
                    operation.configuration
                )
            elif operation.operation_type == InfrastructureOperation.UPDATE:
                result = handler.update_resource(
                    operation.resource_type,
                    operation.resource_id,
                    operation.configuration
                )
            elif operation.operation_type == InfrastructureOperation.DELETE:
                result = handler.delete_resource(
                    operation.resource_type,
                    operation.resource_id
                )
            elif operation.operation_type == InfrastructureOperation.SCALE:
                result = handler.scale_resource(
                    operation.resource_type,
                    operation.resource_id,
                    operation.configuration
                )
            elif operation.operation_type == InfrastructureOperation.MONITOR:
                result = handler.monitor_resource(
                    operation.resource_type,
                    operation.resource_id
                )
            elif operation.operation_type == InfrastructureOperation.BACKUP:
                result = handler.backup_resource(
                    operation.resource_type,
                    operation.resource_id
                )
            elif operation.operation_type == InfrastructureOperation.RESTORE:
                result = handler.restore_resource(
                    operation.resource_type,
                    operation.resource_id,
                    operation.configuration
                )
            else:
                raise ValueError(f"Unsupported operation type: {operation.operation_type}")
            
            operation.status = 'completed' if result.get('success', False) else 'failed'
            operation.completed_at = datetime.utcnow()
            operation.progress = 100.0 if result.get('success', False) else 0.0
            
            if not result.get('success', False):
                operation.error_message = result.get('error', 'Unknown error')
            
            return {
                'operation_id': operation.operation_id,
                'status': 'success' if result.get('success', False) else 'error',
                'result': result,
                'error': result.get('error') if not result.get('success', False) else None
            }
            
        except Exception as e:
            operation.status = 'failed'
            operation.completed_at = datetime.utcnow()
            operation.progress = 0.0
            operation.error_message = str(e)
            
            return {
                'operation_id': operation.operation_id,
                'status': 'error',
                'error': str(e)
            }
    
    def get_infrastructure_status(self, providers: List[str]) -> Dict[str, Any]:
        """Get comprehensive infrastructure status"""
        logger.info("Getting infrastructure status")
        
        status_report = {
            'generated_at': datetime.utcnow().isoformat(),
            'providers': {},
            'summary': {
                'total_resources': 0,
                'healthy_resources': 0,
                'unhealthy_resources': 0,
                'total_cost': 0.0
            }
        }
        
        for provider in providers:
            if provider not in self.config['providers']:
                continue
            
            try:
                handler = self._get_provider_handler(provider)
                if not handler.initialize_client():
                    continue
                
                # Get resource status
                resource_status = handler.get_resource_status()
                
                # Calculate provider summary
                provider_summary = {
                    'total_resources': len(resource_status),
                    'healthy_resources': len([r for r in resource_status if r.get('status') == 'healthy']),
                    'unhealthy_resources': len([r for r in resource_status if r.get('status') != 'healthy']),
                    'total_cost': sum(r.get('cost', 0) for r in resource_status)
                }
                
                status_report['providers'][provider] = {
                    'summary': provider_summary,
                    'resources': resource_status
                }
                
                # Update overall summary
                status_report['summary']['total_resources'] += provider_summary['total_resources']
                status_report['summary']['healthy_resources'] += provider_summary['healthy_resources']
                status_report['summary']['unhealthy_resources'] += provider_summary['unhealthy_resources']
                status_report['summary']['total_cost'] += provider_summary['total_cost']
                
            except Exception as e:
                logger.error(f"Failed to get status for {provider}: {e}")
                status_report['providers'][provider] = {
                    'error': str(e),
                    'summary': {'total_resources': 0, 'healthy_resources': 0, 'unhealthy_resources': 0, 'total_cost': 0.0}
                }
        
        return status_report
    
    def generate_infrastructure_report(self, status_report: Dict[str, Any], 
                                     output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive infrastructure report"""
        logger.info("Generating infrastructure report")
        
        summary = status_report['summary']
        
        # Generate recommendations
        recommendations = self._generate_infrastructure_recommendations(status_report)
        
        # Generate cost analysis
        cost_analysis = self._generate_cost_analysis(status_report)
        
        # Generate health analysis
        health_analysis = self._generate_health_analysis(status_report)
        
        report = {
            'generated_at': status_report['generated_at'],
            'summary': summary,
            'cost_analysis': cost_analysis,
            'health_analysis': health_analysis,
            'recommendations': recommendations,
            'provider_details': status_report['providers']
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Infrastructure report saved to: {output_file}")
        
        return report
    
    def _generate_infrastructure_recommendations(self, status_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate infrastructure recommendations"""
        recommendations = []
        
        for provider, provider_data in status_report['providers'].items():
            if 'error' in provider_data:
                continue
            
            resources = provider_data.get('resources', [])
            
            # Check for unhealthy resources
            unhealthy_resources = [r for r in resources if r.get('status') != 'healthy']
            if unhealthy_resources:
                recommendations.append({
                    'provider': provider,
                    'category': 'health',
                    'priority': 'high',
                    'description': f"Fix {len(unhealthy_resources)} unhealthy resources",
                    'affected_resources': len(unhealthy_resources)
                })
            
            # Check for high-cost resources
            high_cost_resources = [r for r in resources if r.get('cost', 0) > 500]
            if high_cost_resources:
                recommendations.append({
                    'provider': provider,
                    'category': 'cost',
                    'priority': 'medium',
                    'description': f"Review {len(high_cost_resources)} high-cost resources for optimization",
                    'affected_resources': len(high_cost_resources),
                    'potential_savings': sum(r.get('cost', 0) for r in high_cost_resources) * 0.2  # 20% potential savings
                })
            
            # Check for unused resources
            unused_resources = [r for r in resources if r.get('utilization', 0) < 10]
            if unused_resources:
                recommendations.append({
                    'provider': provider,
                    'category': 'optimization',
                    'priority': 'medium',
                    'description': f"Consider decommissioning {len(unused_resources)} unused resources",
                    'affected_resources': len(unused_resources),
                    'potential_savings': sum(r.get('cost', 0) for r in unused_resources)
                })
        
        return recommendations
    
    def _generate_cost_analysis(self, status_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cost analysis"""
        total_cost = status_report['summary']['total_cost']
        
        cost_by_provider = {}
        cost_by_resource_type = {}
        
        for provider, provider_data in status_report['providers'].items():
            if 'error' in provider_data:
                continue
            
            provider_cost = provider_data['summary']['total_cost']
            cost_by_provider[provider] = provider_cost
            
            # Group by resource type
            resources = provider_data.get('resources', [])
            for resource in resources:
                resource_type = resource.get('type', 'unknown')
                cost_by_resource_type[resource_type] = cost_by_resource_type.get(resource_type, 0) + resource.get('cost', 0)
        
        return {
            'total_cost': total_cost,
            'cost_by_provider': cost_by_provider,
            'cost_by_resource_type': cost_by_resource_type,
            'monthly_cost_trend': self._get_cost_trend()  # Placeholder for cost trend data
        }
    
    def _generate_health_analysis(self, status_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health analysis"""
        total_resources = status_report['summary']['total_resources']
        healthy_resources = status_report['summary']['healthy_resources']
        unhealthy_resources = status_report['summary']['unhealthy_resources']
        
        health_percentage = (healthy_resources / total_resources * 100) if total_resources > 0 else 0
        
        health_by_provider = {}
        for provider, provider_data in status_report['providers'].items():
            if 'error' in provider_data:
                continue
            
            provider_summary = provider_data['summary']
            provider_total = provider_summary['total_resources']
            provider_healthy = provider_summary['healthy_resources']
            
            health_by_provider[provider] = {
                'health_percentage': (provider_healthy / provider_total * 100) if provider_total > 0 else 0,
                'healthy_resources': provider_healthy,
                'unhealthy_resources': provider_summary['unhealthy_resources']
            }
        
        return {
            'overall_health_percentage': health_percentage,
            'health_by_provider': health_by_provider,
            'health_status': 'healthy' if health_percentage >= 90 else 'warning' if health_percentage >= 70 else 'critical'
        }
    
    def _get_cost_trend(self) -> List[Dict[str, Any]]:
        """Get cost trend data (placeholder)"""
        # Placeholder for historical cost data
        return [
            {'date': '2024-01-01', 'cost': 1000.0},
            {'date': '2024-02-01', 'cost': 1050.0},
            {'date': '2024-03-01', 'cost': 1020.0},
            {'date': '2024-04-01', 'cost': 1100.0}
        ]

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Infrastructure Manager")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--action", choices=['discover', 'create-plan', 'execute', 'status', 'report'], 
                       required=True, help="Action to perform")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--resource-types", nargs="+",
                       choices=[t.value for t in ResourceType],
                       default=['compute', 'storage', 'networking'], help="Resource types")
    parser.add_argument("--plan-name", help="Infrastructure plan name")
    parser.add_argument("--plan-description", help="Infrastructure plan description")
    parser.add_argument("--operations-file", help="JSON file containing operations")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize manager
    manager = InfrastructureManager(args.config)
    
    try:
        if args.action == 'discover':
            resource_types = [ResourceType(t) for t in args.resource_types]
            discovered = manager.discover_infrastructure(args.providers, resource_types)
            
            print(f"\nInfrastructure Discovery Results:")
            for provider, resources in discovered.items():
                print(f"{provider}: {len(resources)} resources")
                for resource in resources[:3]:  # Show first 3 resources
                    print(f"  - {resource.resource_name} ({resource.resource_type.value})")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump({p: [{'id': r.resource_id, 'name': r.resource_name, 'type': r.resource_type.value, 
                                   'status': r.status} for r in res] for p, res in discovered.items()}, f, indent=2)
                print(f"Discovery results saved to: {args.output}")
        
        elif args.action == 'create-plan':
            if not args.plan_name or not args.operations_file:
                print("Error: --plan-name and --operations-file required for create-plan action")
                sys.exit(1)
            
            with open(args.operations_file, 'r') as f:
                operations = json.load(f)
            
            plan = manager.create_infrastructure_plan(
                args.plan_name,
                args.plan_description or "",
                args.providers[0],  # Use first provider
                operations
            )
            
            print(f"\nInfrastructure Plan Created:")
            print(f"Plan ID: {plan.plan_id}")
            print(f"Operations: {len(plan.operations)}")
            print(f"Estimated Cost: ${plan.estimated_cost:.2f}")
            print(f"Estimated Duration: {plan.estimated_duration}")
            
            if args.output:
                plan_data = {
                    'plan_id': plan.plan_id,
                    'name': plan.name,
                    'description': plan.description,
                    'operations': [{'id': op.operation_id, 'type': op.operation_type.value, 
                                   'resource': op.resource_type.value} for op in plan.operations],
                    'estimated_cost': plan.estimated_cost,
                    'estimated_duration': str(plan.estimated_duration)
                }
                with open(args.output, 'w') as f:
                    json.dump(plan_data, f, indent=2)
                print(f"Plan saved to: {args.output}")
        
        elif args.action == 'status':
            status = manager.get_infrastructure_status(args.providers)
            
            summary = status['summary']
            print(f"\nInfrastructure Status:")
            print(f"Total Resources: {summary['total_resources']}")
            print(f"Healthy Resources: {summary['healthy_resources']}")
            print(f"Unhealthy Resources: {summary['unhealthy_resources']}")
            print(f"Total Cost: ${summary['total_cost']:.2f}")
            
            for provider, provider_data in status['providers'].items():
                if 'error' in provider_data:
                    print(f"{provider}: Error - {provider_data['error']}")
                else:
                    provider_summary = provider_data['summary']
                    print(f"{provider}: {provider_summary['total_resources']} resources, "
                          f"${provider_summary['total_cost']:.2f}")
        
        elif args.action == 'report':
            status = manager.get_infrastructure_status(args.providers)
            report = manager.generate_infrastructure_report(status, args.output)
            
            print(f"\nInfrastructure Report Generated:")
            print(f"Total Resources: {report['summary']['total_resources']}")
            print(f"Health Status: {report['health_analysis']['health_status']}")
            print(f"Total Cost: ${report['summary']['total_cost']:.2f}")
            print(f"Recommendations: {len(report['recommendations'])}")
            
            if args.output:
                print(f"Report saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Infrastructure management failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
