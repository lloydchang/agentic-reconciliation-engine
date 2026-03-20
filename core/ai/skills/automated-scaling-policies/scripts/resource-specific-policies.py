#!/usr/bin/env python3
"""
Resource-Specific Scaling Policies Configuration

Advanced scaling policy configuration system for defining specific scaling rules
and thresholds for particular resources, resource types, and environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScalingStrategy(Enum):
    CPU_BASED = "cpu_based"
    MEMORY_BASED = "memory_based"
    REQUEST_BASED = "request_based"
    CUSTOM_METRIC = "custom_metric"
    PREDICTIVE = "predictive"
    SCHEDULED = "scheduled"
    COST_OPTIMIZED = "cost_optimized"
    HYBRID = "hybrid"

class ScalingAction(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_TO = "scale_to"
    NO_ACTION = "no_action"

class ResourceCategory(Enum):
    WEB_SERVERS = "web_servers"
    API_SERVERS = "api_servers"
    DATABASES = "databases"
    CACHE_SERVERS = "cache_servers"
    BACKGROUND_WORKERS = "background_workers"
    LOAD_BALANCERS = "load_balancers"
    STORAGE_SYSTEMS = "storage_systems"
    CUSTOM = "custom"

@dataclass
class ScalingThreshold:
    metric_name: str
    scale_up_threshold: float
    scale_down_threshold: float
    critical_threshold: Optional[float] = None
    evaluation_period_minutes: int = 5
    cooldown_period_minutes: int = 10
    weight: float = 1.0

@dataclass
class TimeBasedRule:
    start_time: time
    end_time: time
    days_of_week: List[int]  # 0=Monday, 6=Sunday
    min_replicas: int
    max_replicas: int
    priority: int = 1

@dataclass
class LoadBasedRule:
    metric_name: str
    operator: str  # "gt", "lt", "between"
    threshold: Union[float, List[float]]
    action: ScalingAction
    target_replicas: Optional[int] = None
    scale_factor: Optional[float] = None
    priority: int = 1

@dataclass
class PredictiveRule:
    forecast_horizon_hours: int
    confidence_threshold: float
    scale_up_buffer: float = 0.1  # Scale up when predicted load exceeds current capacity by this factor
    scale_down_buffer: float = 0.2  # Scale down when predicted load drops below this factor
    priority: int = 1

@dataclass
class CostOptimizationRule:
    max_cost_per_hour: float
    preferred_instance_types: List[str]
    spot_instance_allowed: bool = False
    reserved_instance_priority: bool = True
    scaling_efficiency_threshold: float = 0.8
    priority: int = 1

@dataclass
class ResourceConstraint:
    max_replicas: int
    min_replicas: int
    max_scale_up_percent: float = 100.0  # Maximum percentage increase in one scaling operation
    max_scale_down_percent: float = 50.0  # Maximum percentage decrease in one scaling operation
    dependency_resources: List[str] = None  # Resources that must be scaled together
    zone_distribution: Dict[str, int] = None  # Minimum replicas per zone
    region_distribution: Dict[str, int] = None  # Minimum replicas per region

@dataclass
class ResourceSpecificPolicy:
    resource_id: str
    resource_name: str
    resource_category: ResourceCategory
    provider: str
    region: str
    namespace: str

    # Basic scaling configuration
    enabled: bool = True
    strategy: ScalingStrategy = ScalingStrategy.CPU_BASED
    default_min_replicas: int = 1
    default_max_replicas: int = 10

    # Scaling thresholds
    thresholds: List[ScalingThreshold] = None

    # Advanced rules
    time_based_rules: List[TimeBasedRule] = None
    load_based_rules: List[LoadBasedRule] = None
    predictive_rules: List[PredictiveRule] = None
    cost_optimization_rules: List[CostOptimizationRule] = None

    # Constraints
    constraints: ResourceConstraint = None

    # Custom configuration
    custom_metrics: Dict[str, Any] = None
    environment_overrides: Dict[str, Any] = None
    emergency_scaling: Dict[str, Any] = None

    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = "system"
    version: str = "1.0"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class ScalingPolicyConfigurationManager:
    """Manager for resource-specific scaling policy configurations"""

    def __init__(self, config_file: Optional[str] = None):
        self.policies: Dict[str, ResourceSpecificPolicy] = {}
        self.category_templates: Dict[ResourceCategory, Dict[str, Any]] = {}
        self.global_defaults: Dict[str, Any] = {}
        self.config_file = config_file

        self._initialize_defaults()
        self._load_configuration()

    def _initialize_defaults(self):
        """Initialize default configurations for different resource categories"""
        self.global_defaults = {
            'scaling_cooldown_minutes': 10,
            'evaluation_period_minutes': 5,
            'max_scaling_operations_per_hour': 6,
            'emergency_scaling_enabled': True,
            'predictive_scaling_enabled': True,
            'cost_optimization_enabled': False
        }

        # Define category-specific templates
        self.category_templates = {
            ResourceCategory.WEB_SERVERS: {
                'strategy': ScalingStrategy.REQUEST_BASED,
                'default_min_replicas': 2,
                'default_max_replicas': 20,
                'thresholds': [
                    ScalingThreshold(
                        metric_name='cpu_utilization',
                        scale_up_threshold=70.0,
                        scale_down_threshold=30.0,
                        critical_threshold=85.0,
                        weight=0.6
                    ),
                    ScalingThreshold(
                        metric_name='request_rate',
                        scale_up_threshold=1000,
                        scale_down_threshold=200,
                        weight=0.4
                    )
                ],
                'time_based_rules': [
                    TimeBasedRule(
                        start_time=time(9, 0),  # 9 AM
                        end_time=time(18, 0),   # 6 PM
                        days_of_week=[0, 1, 2, 3, 4],  # Weekdays
                        min_replicas=3,
                        max_replicas=15
                    ),
                    TimeBasedRule(
                        start_time=time(18, 0),  # 6 PM
                        end_time=time(9, 0),     # 9 AM
                        days_of_week=[0, 1, 2, 3, 4, 5, 6],  # All days
                        min_replicas=2,
                        max_replicas=10
                    )
                ]
            },

            ResourceCategory.API_SERVERS: {
                'strategy': ScalingStrategy.HYBRID,
                'default_min_replicas': 3,
                'default_max_replicas': 25,
                'thresholds': [
                    ScalingThreshold(
                        metric_name='cpu_utilization',
                        scale_up_threshold=65.0,
                        scale_down_threshold=25.0,
                        critical_threshold=80.0,
                        weight=0.5
                    ),
                    ScalingThreshold(
                        metric_name='memory_utilization',
                        scale_up_threshold=75.0,
                        scale_down_threshold=40.0,
                        critical_threshold=85.0,
                        weight=0.3
                    ),
                    ScalingThreshold(
                        metric_name='response_time',
                        scale_up_threshold=500.0,  # milliseconds
                        scale_down_threshold=200.0,
                        weight=0.2
                    )
                ]
            },

            ResourceCategory.DATABASES: {
                'strategy': ScalingStrategy.CUSTOM_METRIC,
                'default_min_replicas': 1,
                'default_max_replicas': 5,  # Limited scaling for databases
                'thresholds': [
                    ScalingThreshold(
                        metric_name='connection_count',
                        scale_up_threshold=80,  # percentage of max connections
                        scale_down_threshold=30,
                        evaluation_period_minutes=10,
                        cooldown_period_minutes=30,  # Longer cooldown for databases
                        weight=0.7
                    ),
                    ScalingThreshold(
                        metric_name='query_latency',
                        scale_up_threshold=100.0,  # milliseconds
                        scale_down_threshold=50.0,
                        weight=0.3
                    )
                ],
                'constraints': ResourceConstraint(
                    max_replicas=5,
                    min_replicas=1,
                    max_scale_up_percent=50.0,  # Conservative scaling
                    max_scale_down_percent=25.0
                )
            },

            ResourceCategory.CACHE_SERVERS: {
                'strategy': ScalingStrategy.MEMORY_BASED,
                'default_min_replicas': 1,
                'default_max_replicas': 8,
                'thresholds': [
                    ScalingThreshold(
                        metric_name='memory_utilization',
                        scale_up_threshold=80.0,
                        scale_down_threshold=40.0,
                        critical_threshold=90.0,
                        weight=0.8
                    ),
                    ScalingThreshold(
                        metric_name='cache_hit_rate',
                        scale_up_threshold=85.0,  # Minimum acceptable hit rate
                        scale_down_threshold=95.0,  # Scale down if very efficient
                        weight=0.2
                    )
                ]
            },

            ResourceCategory.BACKGROUND_WORKERS: {
                'strategy': ScalingStrategy.REQUEST_BASED,
                'default_min_replicas': 1,
                'default_max_replicas': 15,
                'thresholds': [
                    ScalingThreshold(
                        metric_name='queue_length',
                        scale_up_threshold=100,  # Queue items
                        scale_down_threshold=10,
                        critical_threshold=500,
                        weight=0.9
                    ),
                    ScalingThreshold(
                        metric_name='processing_rate',
                        scale_up_threshold=50,  # items per minute
                        scale_down_threshold=200,
                        weight=0.1
                    )
                ]
            }
        }

    def _load_configuration(self):
        """Load configuration from file"""
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

                # Load policies
                if 'policies' in config:
                    for policy_data in config['policies']:
                        policy = ResourceSpecificPolicy(**policy_data)
                        self.policies[policy.resource_id] = policy

                # Load category templates
                if 'category_templates' in config:
                    for category_name, template_data in config['category_templates'].items():
                        category = ResourceCategory(category_name)
                        self.category_templates[category] = template_data

                logger.info(f"Loaded configuration with {len(self.policies)} policies")

            except Exception as e:
                logger.warning(f"Failed to load configuration: {e}")

    def create_policy_for_resource(self, resource_id: str, resource_name: str,
                                 resource_category: ResourceCategory, provider: str,
                                 region: str, namespace: str,
                                 custom_config: Optional[Dict[str, Any]] = None) -> ResourceSpecificPolicy:
        """Create a specific scaling policy for a resource"""

        # Start with category template
        template = self.category_templates.get(resource_category, {})

        # Apply custom configuration
        if custom_config:
            template.update(custom_config)

        # Create policy
        policy = ResourceSpecificPolicy(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_category=resource_category,
            provider=provider,
            region=region,
            namespace=namespace,
            **template
        )

        self.policies[resource_id] = policy
        logger.info(f"Created scaling policy for resource {resource_id}")

        return policy

    def update_policy(self, resource_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing scaling policy"""
        if resource_id not in self.policies:
            logger.error(f"Policy for resource {resource_id} not found")
            return False

        policy = self.policies[resource_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        policy.updated_at = datetime.utcnow()

        logger.info(f"Updated scaling policy for resource {resource_id}")
        return True

    def get_policy_for_resource(self, resource_id: str) -> Optional[ResourceSpecificPolicy]:
        """Get scaling policy for a specific resource"""
        return self.policies.get(resource_id)

    def get_policies_by_category(self, category: ResourceCategory) -> List[ResourceSpecificPolicy]:
        """Get all policies for a specific resource category"""
        return [policy for policy in self.policies.values() if policy.resource_category == category]

    def get_policies_by_provider(self, provider: str) -> List[ResourceSpecificPolicy]:
        """Get all policies for a specific provider"""
        return [policy for policy in self.policies.values() if policy.provider == provider]

    def validate_policy(self, policy: ResourceSpecificPolicy) -> List[str]:
        """Validate a scaling policy for correctness"""
        errors = []

        # Basic validation
        if policy.default_min_replicas < 1:
            errors.append("Minimum replicas must be at least 1")

        if policy.default_max_replicas < policy.default_min_replicas:
            errors.append("Maximum replicas must be greater than or equal to minimum replicas")

        # Constraint validation
        if policy.constraints:
            constraints = policy.constraints
            if constraints.max_replicas < constraints.min_replicas:
                errors.append("Constraint max_replicas must be >= min_replicas")

            if constraints.max_scale_up_percent <= 0 or constraints.max_scale_up_percent > 500:
                errors.append("max_scale_up_percent must be between 0 and 500")

            if constraints.max_scale_down_percent <= 0 or constraints.max_scale_down_percent > 100:
                errors.append("max_scale_down_percent must be between 0 and 100")

        # Threshold validation
        if policy.thresholds:
            for threshold in policy.thresholds:
                if threshold.scale_up_threshold <= threshold.scale_down_threshold:
                    errors.append(f"Scale up threshold must be > scale down threshold for {threshold.metric_name}")

                if threshold.critical_threshold and threshold.critical_threshold <= threshold.scale_up_threshold:
                    errors.append(f"Critical threshold must be > scale up threshold for {threshold.metric_name}")

        return errors

    def apply_policy_to_resource(self, resource_id: str, current_metrics: Dict[str, Any],
                               historical_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Apply scaling policy to determine scaling actions for a resource"""
        policy = self.get_policy_for_resource(resource_id)

        if not policy or not policy.enabled:
            return {'action': ScalingAction.NO_ACTION.value, 'reason': 'Policy not found or disabled'}

        try:
            # Evaluate time-based rules first
            time_action = self._evaluate_time_based_rules(policy, datetime.utcnow())
            if time_action:
                return time_action

            # Evaluate load-based rules
            load_action = self._evaluate_load_based_rules(policy, current_metrics)
            if load_action:
                return load_action

            # Evaluate thresholds
            threshold_action = self._evaluate_thresholds(policy, current_metrics)
            if threshold_action:
                return threshold_action

            # Evaluate predictive rules
            if historical_data and policy.predictive_rules:
                predictive_action = self._evaluate_predictive_rules(policy, historical_data)
                if predictive_action:
                    return predictive_action

            # Default to no action
            return {
                'action': ScalingAction.NO_ACTION.value,
                'reason': 'No scaling conditions met',
                'current_metrics': current_metrics
            }

        except Exception as e:
            logger.error(f"Failed to apply policy for resource {resource_id}: {e}")
            return {'action': ScalingAction.NO_ACTION.value, 'error': str(e)}

    def _evaluate_time_based_rules(self, policy: ResourceSpecificPolicy, current_time: datetime) -> Optional[Dict[str, Any]]:
        """Evaluate time-based scaling rules"""
        if not policy.time_based_rules:
            return None

        current_time_only = current_time.time()
        current_weekday = current_time.weekday()

        for rule in policy.time_based_rules:
            # Check if current time falls within rule window
            if current_weekday in rule.days_of_week:
                if rule.start_time <= rule.end_time:
                    # Same day rule
                    if rule.start_time <= current_time_only <= rule.end_time:
                        return {
                            'action': ScalingAction.SCALE_TO.value,
                            'target_replicas': rule.min_replicas,  # Use min as baseline
                            'reason': f'Time-based rule: {rule.start_time}-{rule.end_time}',
                            'rule_type': 'time_based'
                        }
                else:
                    # Overnight rule
                    if current_time_only >= rule.start_time or current_time_only <= rule.end_time:
                        return {
                            'action': ScalingAction.SCALE_TO.value,
                            'target_replicas': rule.min_replicas,
                            'reason': f'Overnight time-based rule: {rule.start_time}-{rule.end_time}',
                            'rule_type': 'time_based'
                        }

        return None

    def _evaluate_load_based_rules(self, policy: ResourceSpecificPolicy, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate load-based scaling rules"""
        if not policy.load_based_rules:
            return None

        for rule in policy.load_based_rules:
            metric_value = metrics.get(rule.metric_name)
            if metric_value is None:
                continue

            triggered = False

            if rule.operator == 'gt' and isinstance(rule.threshold, (int, float)):
                triggered = metric_value > rule.threshold
            elif rule.operator == 'lt' and isinstance(rule.threshold, (int, float)):
                triggered = metric_value < rule.threshold
            elif rule.operator == 'between' and isinstance(rule.threshold, list) and len(rule.threshold) == 2:
                triggered = rule.threshold[0] <= metric_value <= rule.threshold[1]

            if triggered:
                result = {
                    'action': rule.action.value,
                    'reason': f'Load-based rule: {rule.metric_name} {rule.operator} {rule.threshold}',
                    'rule_type': 'load_based',
                    'metric_value': metric_value,
                    'threshold': rule.threshold
                }

                if rule.target_replicas:
                    result['target_replicas'] = rule.target_replicas
                elif rule.scale_factor:
                    result['scale_factor'] = rule.scale_factor

                return result

        return None

    def _evaluate_thresholds(self, policy: ResourceSpecificPolicy, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate scaling thresholds"""
        if not policy.thresholds:
            return None

        scale_up_score = 0.0
        scale_down_score = 0.0
        total_weight = 0.0

        for threshold in policy.thresholds:
            metric_value = metrics.get(threshold.metric_name)
            if metric_value is None:
                continue

            weight = threshold.weight
            total_weight += weight

            # Calculate scaling scores
            if metric_value >= threshold.scale_up_threshold:
                scale_up_score += weight
            elif metric_value <= threshold.scale_down_threshold:
                scale_down_score += weight

        if total_weight == 0:
            return None

        scale_up_ratio = scale_up_score / total_weight
        scale_down_ratio = scale_down_score / total_weight

        # Determine action based on scores
        if scale_up_ratio >= 0.6:  # 60% of metrics indicate scale up
            return {
                'action': ScalingAction.SCALE_UP.value,
                'reason': f'Threshold-based: {scale_up_ratio:.2f} scale-up indicators',
                'rule_type': 'threshold',
                'scale_up_ratio': scale_up_ratio
            }
        elif scale_down_ratio >= 0.6:  # 60% of metrics indicate scale down
            return {
                'action': ScalingAction.SCALE_DOWN.value,
                'reason': f'Threshold-based: {scale_down_ratio:.2f} scale-down indicators',
                'rule_type': 'threshold',
                'scale_down_ratio': scale_down_ratio
            }

        return None

    def _evaluate_predictive_rules(self, policy: ResourceSpecificPolicy, historical_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Evaluate predictive scaling rules"""
        if not policy.predictive_rules:
            return None

        # Simple predictive logic based on trend analysis
        for rule in policy.predictive_rules:
            try:
                recent_data = historical_data[-rule.forecast_horizon_hours:] if len(historical_data) > rule.forecast_horizon_hours else historical_data

                if len(recent_data) < 3:
                    continue

                # Calculate trend for key metrics
                cpu_values = [d.get('cpu_utilization', 0) for d in recent_data]
                memory_values = [d.get('memory_utilization', 0) for d in recent_data]

                cpu_trend = np.polyfit(range(len(cpu_values)), cpu_values, 1)[0] if len(cpu_values) > 1 else 0
                memory_trend = np.polyfit(range(len(memory_values)), memory_values, 1)[0] if len(memory_values) > 1 else 0

                # Predict future load
                predicted_cpu = cpu_values[-1] + cpu_trend * rule.forecast_horizon_hours
                predicted_memory = memory_values[-1] + memory_trend * rule.forecast_horizon_hours

                # Check if prediction exceeds buffers
                current_avg = (cpu_values[-1] + memory_values[-1]) / 2
                predicted_avg = (predicted_cpu + predicted_memory) / 2

                if predicted_avg > current_avg * (1 + rule.scale_up_buffer):
                    return {
                        'action': ScalingAction.SCALE_UP.value,
                        'reason': f'Predictive: Expected load increase to {predicted_avg:.1f}',
                        'rule_type': 'predictive',
                        'predicted_load': predicted_avg,
                        'confidence': rule.confidence_threshold
                    }
                elif predicted_avg < current_avg * (1 - rule.scale_down_buffer):
                    return {
                        'action': ScalingAction.SCALE_DOWN.value,
                        'reason': f'Predictive: Expected load decrease to {predicted_avg:.1f}',
                        'rule_type': 'predictive',
                        'predicted_load': predicted_avg,
                        'confidence': rule.confidence_threshold
                    }

            except Exception as e:
                logger.warning(f"Failed to evaluate predictive rule: {e}")
                continue

        return None

    def export_configuration(self, output_file: str):
        """Export current configuration to file"""
        config = {
            'global_defaults': self.global_defaults,
            'category_templates': {
                category.value: template for category, template in self.category_templates.items()
            },
            'policies': [asdict(policy) for policy in self.policies.values()]
        }

        # Convert datetime objects to ISO strings
        for policy_dict in config['policies']:
            if 'created_at' in policy_dict and isinstance(policy_dict['created_at'], datetime):
                policy_dict['created_at'] = policy_dict['created_at'].isoformat()
            if 'updated_at' in policy_dict and isinstance(policy_dict['updated_at'], datetime):
                policy_dict['updated_at'] = policy_dict['updated_at'].isoformat()

        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Configuration exported to {output_file}")

    def generate_resource_policy_report(self, resource_id: str) -> Dict[str, Any]:
        """Generate detailed report for a specific resource's scaling policy"""
        policy = self.get_policy_for_resource(resource_id)

        if not policy:
            return {'error': f'Policy for resource {resource_id} not found'}

        report = {
            'resource_id': resource_id,
            'resource_name': policy.resource_name,
            'category': policy.resource_category.value,
            'strategy': policy.strategy.value,
            'enabled': policy.enabled,
            'scaling_limits': {
                'min_replicas': policy.default_min_replicas,
                'max_replicas': policy.default_max_replicas
            },
            'active_rules': {
                'thresholds': len(policy.thresholds) if policy.thresholds else 0,
                'time_based': len(policy.time_based_rules) if policy.time_based_rules else 0,
                'load_based': len(policy.load_based_rules) if policy.load_based_rules else 0,
                'predictive': len(policy.predictive_rules) if policy.predictive_rules else 0,
                'cost_optimization': len(policy.cost_optimization_rules) if policy.cost_optimization_rules else 0
            }
        }

        # Add validation results
        validation_errors = self.validate_policy(policy)
        report['validation'] = {
            'is_valid': len(validation_errors) == 0,
            'errors': validation_errors
        }

        # Add constraint information
        if policy.constraints:
            report['constraints'] = {
                'max_replicas': policy.constraints.max_replicas,
                'min_replicas': policy.constraints.min_replicas,
                'max_scale_up_percent': policy.constraints.max_scale_up_percent,
                'max_scale_down_percent': policy.constraints.max_scale_down_percent,
                'has_dependencies': bool(policy.constraints.dependency_resources),
                'dependency_count': len(policy.constraints.dependency_resources) if policy.constraints.dependency_resources else 0
            }

        return report

def main():
    """Main function for resource-specific scaling policy configuration"""
    parser = argparse.ArgumentParser(description='Resource-Specific Scaling Policies Configuration')
    parser.add_argument('--operation', required=True, help='Operation type')
    parser.add_argument('--resource-id', help='Resource ID')
    parser.add_argument('--resource-name', help='Resource name')
    parser.add_argument('--category', help='Resource category')
    parser.add_argument('--provider', help='Cloud provider')
    parser.add_argument('--region', help='Region')
    parser.add_argument('--namespace', help='Namespace')
    parser.add_argument('--config-file', help='Configuration file')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--metrics', help='Current metrics (JSON string)')

    args = parser.parse_args()

    # Initialize policy manager
    manager = ScalingPolicyConfigurationManager(args.config_file)

    if args.operation == 'create':
        # Create policy for resource
        if not all([args.resource_id, args.resource_name, args.category, args.provider]):
            logger.error("Resource ID, name, category, and provider are required")
            sys.exit(1)

        category = ResourceCategory(args.category)
        region = args.region or 'us-west-2'
        namespace = args.namespace or 'default'

        policy = manager.create_policy_for_resource(
            args.resource_id, args.resource_name, category,
            args.provider, region, namespace
        )

        result = {
            'policy_created': True,
            'resource_id': args.resource_id,
            'category': category.value,
            'strategy': policy.strategy.value
        }

        print(json.dumps(result, indent=2))

    elif args.operation == 'apply':
        # Apply policy to resource
        if not args.resource_id or not args.metrics:
            logger.error("Resource ID and metrics are required")
            sys.exit(1)

        try:
            metrics = json.loads(args.metrics)
        except json.JSONDecodeError:
            logger.error("Invalid metrics JSON")
            sys.exit(1)

        result = manager.apply_policy_to_resource(args.resource_id, metrics)
        print(json.dumps(result, indent=2))

    elif args.operation == 'report':
        # Generate policy report
        if not args.resource_id:
            logger.error("Resource ID is required")
            sys.exit(1)

        report = manager.generate_resource_policy_report(args.resource_id)
        print(json.dumps(report, indent=2))

    elif args.operation == 'export':
        # Export configuration
        if not args.output:
            logger.error("Output file is required")
            sys.exit(1)

        manager.export_configuration(args.output)
        print(f"Configuration exported to {args.output}")

    elif args.operation == 'list':
        # List all policies
        policies = list(manager.policies.keys())
        result = {
            'total_policies': len(policies),
            'policies': policies
        }
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
