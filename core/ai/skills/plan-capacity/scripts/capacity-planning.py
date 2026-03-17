#!/usr/bin/env python3
"""
Capacity Planning Script

Multi-cloud automation for capacity planning and resource forecasting across AWS, Azure, GCP, and on-premise environments.
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

class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORKING = "networking"
    DATABASE = "database"
    MEMORY = "memory"

class PlanningHorizon(Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

@dataclass
class ResourceCapacity:
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    current_capacity: float
    current_utilization: float
    projected_utilization: float
    utilization_trend: List[float]  # Historical utilization data
    capacity_unit: str
    cost_per_unit: float
    region: str

@dataclass
class CapacityRecommendation:
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    action: str  # scale_up, scale_down, maintain
    current_capacity: float
    recommended_capacity: float
    confidence: float
    urgency: str  # low, medium, high, critical
    timeframe: str  # immediate, 1_week, 1_month, 1_quarter
    cost_impact: float
    rationale: str
    implementation_steps: List[str]

@dataclass
class CapacityPlan:
    plan_id: str
    provider: str
    horizon: PlanningHorizon
    created_at: datetime
    recommendations: List[CapacityRecommendation]
    summary: Dict[str, Any]
    total_cost_impact: float

class CapacityPlanner:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load capacity planning configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'planning_thresholds': {
                'high_utilization': 80.0,
                'low_utilization': 30.0,
                'critical_utilization': 90.0,
                'growth_rate_threshold': 10.0  # % growth per month
            },
            'forecast_horizon_days': 90,
            'historical_data_days': 30,
            'confidence_threshold': 0.7
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def analyze_capacity(self, providers: List[str], resource_types: List[ResourceType], 
                        horizon: PlanningHorizon) -> List[CapacityPlan]:
        """Analyze capacity across providers and resource types"""
        logger.info(f"Analyzing capacity for providers: {providers}, horizon: {horizon.value}")
        
        plans = []
        
        for provider in providers:
            if provider not in self.config['providers']:
                logger.warning(f"Provider {provider} not in configuration")
                continue
            
            if not self.config['providers'][provider]['enabled']:
                logger.info(f"Provider {provider} is disabled")
                continue
            
            try:
                plan = self._analyze_provider_capacity(provider, resource_types, horizon)
                plans.append(plan)
                logger.info(f"Generated capacity plan for {provider} with {len(plan.recommendations)} recommendations")
                
            except Exception as e:
                logger.error(f"Failed to analyze capacity for provider {provider}: {e}")
        
        return plans
    
    def _analyze_provider_capacity(self, provider: str, resource_types: List[ResourceType], 
                                   horizon: PlanningHorizon) -> CapacityPlan:
        """Analyze capacity for a specific provider"""
        # Initialize provider handler
        handler = self._get_provider_handler(provider)
        if not handler.initialize_client():
            raise RuntimeError(f"Failed to initialize {provider} handler")
        
        # Collect capacity data
        all_resources = []
        for resource_type in resource_types:
            resources = self._collect_resource_capacity(handler, resource_type)
            all_resources.extend(resources)
        
        # Generate recommendations
        recommendations = self._generate_capacity_recommendations(all_resources, horizon)
        
        # Calculate summary
        summary = self._generate_capacity_summary(recommendations)
        
        # Calculate total cost impact
        total_cost_impact = sum(r.cost_impact for r in recommendations)
        
        # Create capacity plan
        plan = CapacityPlan(
            plan_id=f"capacity-plan-{provider}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            provider=provider,
            horizon=horizon,
            created_at=datetime.utcnow(),
            recommendations=recommendations,
            summary=summary,
            total_cost_impact=total_cost_impact
        )
        
        return plan
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific capacity handler"""
        from capacity_planning_handler import get_capacity_handler
        region = self.config['providers'][provider]['region']
        return get_capacity_handler(provider, region)
    
    def _collect_resource_capacity(self, handler, resource_type: ResourceType) -> List[ResourceCapacity]:
        """Collect capacity data for a specific resource type"""
        try:
            if resource_type == ResourceType.COMPUTE:
                return handler.get_compute_capacity()
            elif resource_type == ResourceType.STORAGE:
                return handler.get_storage_capacity()
            elif resource_type == ResourceType.NETWORKING:
                return handler.get_networking_capacity()
            elif resource_type == ResourceType.DATABASE:
                return handler.get_database_capacity()
            elif resource_type == ResourceType.MEMORY:
                return handler.get_memory_capacity()
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
                
        except Exception as e:
            logger.error(f"Failed to collect {resource_type.value} capacity: {e}")
            return []
    
    def _generate_capacity_recommendations(self, resources: List[ResourceCapacity], 
                                         horizon: PlanningHorizon) -> List[CapacityRecommendation]:
        """Generate capacity recommendations based on resource analysis"""
        recommendations = []
        thresholds = self.config['planning_thresholds']
        
        for resource in resources:
            # Analyze utilization trend
            trend_analysis = self._analyze_utilization_trend(resource.utilization_trend)
            
            # Determine action based on current and projected utilization
            action, urgency, timeframe = self._determine_capacity_action(
                resource.current_utilization,
                resource.projected_utilization,
                trend_analysis,
                thresholds
            )
            
            # Skip if no action needed
            if action == "maintain":
                continue
            
            # Calculate recommended capacity
            recommended_capacity = self._calculate_recommended_capacity(
                resource,
                action,
                resource.projected_utilization,
                trend_analysis
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(resource, trend_analysis)
            
            # Skip if confidence is too low
            if confidence < self.config['confidence_threshold']:
                continue
            
            # Calculate cost impact
            cost_impact = self._calculate_cost_impact(resource, recommended_capacity)
            
            # Generate rationale
            rationale = self._generate_rationale(resource, action, trend_analysis)
            
            # Generate implementation steps
            implementation_steps = self._generate_implementation_steps(resource, action)
            
            recommendation = CapacityRecommendation(
                resource_id=resource.resource_id,
                resource_name=resource.resource_name,
                resource_type=resource.resource_type,
                provider=resource.provider,
                action=action,
                current_capacity=resource.current_capacity,
                recommended_capacity=recommended_capacity,
                confidence=confidence,
                urgency=urgency,
                timeframe=timeframe,
                cost_impact=cost_impact,
                rationale=rationale,
                implementation_steps=implementation_steps
            )
            
            recommendations.append(recommendation)
        
        # Sort by urgency and cost impact
        recommendations.sort(key=lambda x: (x.urgency, -abs(x.cost_impact)))
        
        return recommendations
    
    def _analyze_utilization_trend(self, utilization_data: List[float]) -> Dict[str, Any]:
        """Analyze utilization trend from historical data"""
        if len(utilization_data) < 2:
            return {
                'trend': 'stable',
                'growth_rate': 0.0,
                'volatility': 0.0,
                'confidence': 0.5
            }
        
        # Calculate trend (simple linear regression)
        n = len(utilization_data)
        x = list(range(n))
        
        # Calculate slope (growth rate)
        sum_x = sum(x)
        sum_y = sum(utilization_data)
        sum_xy = sum(x[i] * utilization_data[i] for i in range(n))
        sum_x2 = sum(x[i]**2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        
        # Calculate volatility (standard deviation)
        mean = sum_y / n
        variance = sum((y - mean)**2 for y in utilization_data) / n
        volatility = variance ** 0.5
        
        # Determine trend direction
        if slope > 1.0:
            trend = 'increasing'
        elif slope < -1.0:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Calculate confidence based on data consistency
        confidence = max(0.3, 1.0 - (volatility / 50.0))  # Normalize volatility to confidence
        
        return {
            'trend': trend,
            'growth_rate': slope,
            'volatility': volatility,
            'confidence': confidence
        }
    
    def _determine_capacity_action(self, current_util: float, projected_util: float,
                                 trend_analysis: Dict[str, Any], thresholds: Dict[str, float]) -> Tuple[str, str, str]:
        """Determine what action to take based on utilization"""
        growth_rate = trend_analysis['growth_rate']
        trend = trend_analysis['trend']
        
        # Critical utilization - immediate action needed
        if current_util >= thresholds['critical_utilization'] or projected_util >= thresholds['critical_utilization']:
            if trend == 'increasing' and growth_rate > 5.0:
                return "scale_up", "critical", "immediate"
            else:
                return "scale_up", "high", "1_week"
        
        # High utilization - scale up
        elif current_util >= thresholds['high_utilization'] or projected_util >= thresholds['high_utilization']:
            if trend == 'increasing':
                return "scale_up", "high", "1_week"
            else:
                return "scale_up", "medium", "1_month"
        
        # Low utilization - scale down
        elif current_util <= thresholds['low_utilization'] and projected_util <= thresholds['low_utilization']:
            if trend == 'decreasing':
                return "scale_down", "medium", "1_month"
            else:
                return "scale_down", "low", "1_quarter"
        
        # Stable utilization - maintain
        else:
            return "maintain", "low", "1_quarter"
    
    def _calculate_recommended_capacity(self, resource: ResourceCapacity, action: str,
                                       projected_util: float, trend_analysis: Dict[str, Any]) -> float:
        """Calculate recommended capacity based on action"""
        current_capacity = resource.current_capacity
        growth_rate = trend_analysis['growth_rate']
        
        if action == "scale_up":
            # Scale up to handle projected utilization with buffer
            target_util = 70.0  # Target 70% utilization
            buffer_factor = 1.2  # 20% buffer for growth
            
            if growth_rate > 5.0:
                buffer_factor = 1.5  # Higher buffer for fast growth
            
            recommended_capacity = (projected_util / target_util) * current_capacity * buffer_factor
            
        elif action == "scale_down":
            # Scale down to optimize cost while maintaining headroom
            target_util = 60.0  # Target 60% utilization (conservative)
            recommended_capacity = (projected_util / target_util) * current_capacity
            
            # Don't scale down too aggressively
            min_capacity = current_capacity * 0.5
            recommended_capacity = max(recommended_capacity, min_capacity)
            
        else:
            recommended_capacity = current_capacity
        
        # Round to reasonable precision
        if resource.resource_type == ResourceType.COMPUTE:
            # Round to nearest whole number for compute resources
            recommended_capacity = round(recommended_capacity)
        elif resource.resource_type == ResourceType.STORAGE:
            # Round to nearest GB for storage
            recommended_capacity = round(recommended_capacity / 1024) * 1024
        else:
            # Round to 2 decimal places for others
            recommended_capacity = round(recommended_capacity, 2)
        
        return recommended_capacity
    
    def _calculate_confidence(self, resource: ResourceCapacity, trend_analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the recommendation"""
        base_confidence = trend_analysis['confidence']
        
        # Adjust confidence based on data quality
        if len(resource.utilization_trend) >= 30:
            data_quality_factor = 1.0
        elif len(resource.utilization_trend) >= 14:
            data_quality_factor = 0.8
        elif len(resource.utilization_trend) >= 7:
            data_quality_factor = 0.6
        else:
            data_quality_factor = 0.4
        
        # Adjust confidence based on volatility
        volatility = trend_analysis['volatility']
        if volatility < 10:
            volatility_factor = 1.0
        elif volatility < 20:
            volatility_factor = 0.8
        elif volatility < 30:
            volatility_factor = 0.6
        else:
            volatility_factor = 0.4
        
        return base_confidence * data_quality_factor * volatility_factor
    
    def _calculate_cost_impact(self, resource: ResourceCapacity, recommended_capacity: float) -> float:
        """Calculate cost impact of the capacity change"""
        current_cost = resource.current_capacity * resource.cost_per_unit
        recommended_cost = recommended_capacity * resource.cost_per_unit
        
        return recommended_cost - current_cost
    
    def _generate_rationale(self, resource: ResourceCapacity, action: str, trend_analysis: Dict[str, Any]) -> str:
        """Generate rationale for the recommendation"""
        current_util = resource.current_utilization
        projected_util = resource.projected_utilization
        trend = trend_analysis['trend']
        growth_rate = trend_analysis['growth_rate']
        
        if action == "scale_up":
            if current_util >= 90:
                return f"Resource is critically utilized at {current_util:.1f}% and projected to reach {projected_util:.1f}%"
            elif trend == 'increasing':
                return f"Resource utilization is {trend} at {growth_rate:.1f}%/period, projected to reach {projected_util:.1f}%"
            else:
                return f"Resource is under-provisioned for current {current_util:.1f}% utilization"
                
        elif action == "scale_down":
            if trend == 'decreasing':
                return f"Resource utilization is {trend} and consistently low at {current_util:.1f}%, opportunity to optimize costs"
            else:
                return f"Resource is over-provisioned with only {current_util:.1f}% utilization"
        else:
            return f"Resource utilization is stable at {current_util:.1f}%, no action needed"
    
    def _generate_implementation_steps(self, resource: ResourceCapacity, action: str) -> List[str]:
        """Generate implementation steps for the recommendation"""
        if action == "scale_up":
            if resource.resource_type == ResourceType.COMPUTE:
                return [
                    "Review current workload requirements",
                    "Select appropriate instance size/type",
                    "Schedule maintenance window for scaling",
                    "Monitor performance after scaling",
                    "Update documentation and capacity plans"
                ]
            elif resource.resource_type == ResourceType.STORAGE:
                return [
                    "Analyze storage usage patterns",
                    "Select appropriate storage tier",
                    "Plan data migration if needed",
                    "Execute storage expansion",
                    "Monitor storage performance"
                ]
            else:
                return [
                    "Analyze current resource usage",
                    "Plan capacity increase",
                    "Execute scaling operation",
                    "Monitor post-scaling performance"
                ]
                
        elif action == "scale_down":
            if resource.resource_type == ResourceType.COMPUTE:
                return [
                    "Verify workload can handle reduced capacity",
                    "Select appropriate smaller instance size",
                    "Schedule maintenance window",
                    "Execute scale-down operation",
                    "Monitor performance and adjust if needed"
                ]
            elif resource.resource_type == ResourceType.STORAGE:
                return [
                    "Identify unused or stale data",
                    "Implement data cleanup policies",
                    "Migrate data to smaller storage tier",
                    "Monitor storage utilization"
                ]
            else:
                return [
                    "Verify reduced capacity meets requirements",
                    "Execute scale-down operation",
                    "Monitor performance metrics"
                ]
        else:
            return [
                "Continue monitoring resource utilization",
                "Review capacity planning quarterly",
                "Update capacity forecasts as needed"
            ]
    
    def _generate_capacity_summary(self, recommendations: List[CapacityRecommendation]) -> Dict[str, Any]:
        """Generate summary of capacity recommendations"""
        if not recommendations:
            return {
                'total_recommendations': 0,
                'scale_up_count': 0,
                'scale_down_count': 0,
                'high_urgency_count': 0,
                'total_cost_impact': 0.0,
                'resource_types': {}
            }
        
        # Count recommendations by type
        scale_up_count = len([r for r in recommendations if r.action == 'scale_up'])
        scale_down_count = len([r for r in recommendations if r.action == 'scale_down'])
        high_urgency_count = len([r for r in recommendations if r.urgency in ['high', 'critical']])
        
        # Group by resource type
        resource_types = {}
        for rec in recommendations:
            resource_type = rec.resource_type.value
            if resource_type not in resource_types:
                resource_types[resource_type] = {'count': 0, 'cost_impact': 0.0}
            resource_types[resource_type]['count'] += 1
            resource_types[resource_type]['cost_impact'] += rec.cost_impact
        
        return {
            'total_recommendations': len(recommendations),
            'scale_up_count': scale_up_count,
            'scale_down_count': scale_down_count,
            'high_urgency_count': high_urgency_count,
            'total_cost_impact': sum(r.cost_impact for r in recommendations),
            'resource_types': resource_types
        }
    
    def generate_capacity_report(self, plans: List[CapacityPlan], output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive capacity planning report"""
        if not plans:
            return {"error": "No capacity plans available"}
        
        # Calculate overall summary
        total_recommendations = sum(len(p.recommendations) for p in plans)
        total_cost_impact = sum(p.total_cost_impact for p in plans)
        
        # Group recommendations by provider
        provider_summary = {}
        for plan in plans:
            provider = plan.provider
            if provider not in provider_summary:
                provider_summary[provider] = {
                    'plan_count': 0,
                    'recommendations': 0,
                    'cost_impact': 0.0,
                    'horizons': set()
                }
            
            provider_summary[provider]['plan_count'] += 1
            provider_summary[provider]['recommendations'] += len(plan.recommendations)
            provider_summary[provider]['cost_impact'] += plan.total_cost_impact
            provider_summary[provider]['horizons'].add(plan.horizon.value)
        
        # Convert sets to lists for JSON serialization
        for provider_data in provider_summary.values():
            provider_data['horizons'] = list(provider_data['horizons'])
        
        # Generate recommendations
        all_recommendations = []
        for plan in plans:
            for rec in plan.recommendations:
                all_recommendations.append({
                    'provider': plan.provider,
                    'resource_name': rec.resource_name,
                    'resource_type': rec.resource_type.value,
                    'action': rec.action,
                    'urgency': rec.urgency,
                    'timeframe': rec.timeframe,
                    'confidence': rec.confidence,
                    'cost_impact': rec.cost_impact,
                    'rationale': rec.rationale
                })
        
        # Sort by urgency and cost impact
        all_recommendations.sort(key=lambda x: (
            {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[x['urgency']],
            -abs(x['cost_impact'])
        ))
        
        report_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_plans": len(plans),
                "total_recommendations": total_recommendations,
                "total_cost_impact": total_cost_impact,
                "providers_analyzed": list(provider_summary.keys())
            },
            "provider_summary": provider_summary,
            "top_recommendations": all_recommendations[:20],  # Top 20 recommendations
            "implementation_roadmap": self._generate_implementation_roadmap(all_recommendations),
            "cost_optimization_potential": self._calculate_optimization_potential(all_recommendations)
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Capacity planning report saved to: {output_file}")
        
        return report_data
    
    def _generate_implementation_roadmap(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate implementation roadmap based on urgency and timeframe"""
        roadmap = {
            'immediate': [],  # Critical urgency
            'week_1': [],     # High urgency, 1 week timeframe
            'month_1': [],   # Medium urgency, 1 month timeframe
            'quarter_1': []  # Low urgency, 1 quarter timeframe
        }
        
        for rec in recommendations:
            if rec['urgency'] == 'critical' and rec['timeframe'] == 'immediate':
                roadmap['immediate'].append(rec)
            elif rec['urgency'] in ['high', 'critical'] and rec['timeframe'] in ['1_week', 'immediate']:
                roadmap['week_1'].append(rec)
            elif rec['urgency'] in ['medium', 'high'] and rec['timeframe'] in ['1_month', '1_week']:
                roadmap['month_1'].append(rec)
            else:
                roadmap['quarter_1'].append(rec)
        
        return roadmap
    
    def _calculate_optimization_potential(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate optimization potential from recommendations"""
        scale_up_cost = sum(r['cost_impact'] for r in recommendations if r['action'] == 'scale_up')
        scale_down_savings = sum(-r['cost_impact'] for r in recommendations if r['action'] == 'scale_down')
        
        return {
            'scale_up_investment': scale_up_cost,
            'scale_down_savings': scale_down_savings,
            'net_cost_impact': scale_up_cost - scale_down_savings,
            'roi_percentage': (scale_down_savings / scale_up_cost * 100) if scale_up_cost > 0 else 0,
            'payback_period_months': (scale_up_cost / scale_down_savings * 12) if scale_down_savings > 0 else None
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Capacity Planner")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--resource-types", nargs="+",
                       choices=[t.value for t in ResourceType],
                       default=['compute', 'storage', 'memory'], help="Resource types")
    parser.add_argument("--horizon", choices=[h.value for h in PlanningHorizon],
                       default=PlanningHorizon.MONTHLY.value, help="Planning horizon")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize planner
    planner = CapacityPlanner(args.config)
    
    # Convert resource types and horizon
    resource_types = [ResourceType(t) for t in args.resource_types]
    horizon = PlanningHorizon(args.horizon)
    
    # Analyze capacity
    plans = planner.analyze_capacity(args.providers, resource_types, horizon)
    print(f"Generated {len(plans)} capacity plans")
    
    # Generate report
    report = planner.generate_capacity_report(plans, args.output)
    
    # Print summary
    summary = report.get('summary', {})
    print(f"\nCapacity Planning Summary:")
    print(f"Total Plans: {summary.get('total_plans', 0)}")
    print(f"Total Recommendations: {summary.get('total_recommendations', 0)}")
    print(f"Total Cost Impact: ${summary.get('total_cost_impact', 0):.2f}")
    
    if args.output:
        print(f"Report saved to: {args.output}")

if __name__ == "__main__":
    main()
