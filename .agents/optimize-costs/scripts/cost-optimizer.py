#!/usr/bin/env python3
"""
Cost Optimizer Script

Multi-cloud automation for cost optimization across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
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

class OptimizationType(Enum):
    RIGHTSIZING = "rightsizing"
    SCHEDULING = "scheduling"
    STORAGE = "storage"
    NETWORKING = "networking"
    LICENSES = "licenses"
    RESERVATIONS = "reservations"

@dataclass
class CostRecommendation:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    current_cost: float
    projected_savings: float
    optimization_type: OptimizationType
    confidence: float
    effort: str
    description: str
    implementation_steps: List[str]

class CostOptimizer:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.recommendations = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load cost optimization configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'optimization_threshold': 10.0,  # Minimum savings percentage
            'analysis_period_days': 30,
            'currency': 'USD'
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def analyze_costs(self, providers: List[str], optimization_types: List[OptimizationType]) -> List[CostRecommendation]:
        """Analyze costs across providers and optimization types"""
        logger.info(f"Analyzing costs for providers: {providers}")
        
        all_recommendations = []
        
        for provider in providers:
            if provider not in self.config['providers']:
                logger.warning(f"Provider {provider} not in configuration")
                continue
            
            if not self.config['providers'][provider]['enabled']:
                logger.info(f"Provider {provider} is disabled")
                continue
            
            try:
                provider_recommendations = self._analyze_provider_costs(provider, optimization_types)
                all_recommendations.extend(provider_recommendations)
                logger.info(f"Generated {len(provider_recommendations)} recommendations for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to analyze costs for provider {provider}: {e}")
        
        # Filter recommendations by threshold
        filtered_recommendations = [
            r for r in all_recommendations 
            if r.projected_savings >= self.config['optimization_threshold']
        ]
        
        # Sort by potential savings
        filtered_recommendations.sort(key=lambda x: x.projected_savings, reverse=True)
        
        self.recommendations = filtered_recommendations
        return filtered_recommendations
    
    def _analyze_provider_costs(self, provider: str, optimization_types: List[OptimizationType]) -> List[CostRecommendation]:
        """Analyze costs for a specific provider"""
        recommendations = []
        
        for opt_type in optimization_types:
            if opt_type == OptimizationType.RIGHTSIZING:
                recommendations.extend(self._analyze_rightsizing(provider))
            elif opt_type == OptimizationType.SCHEDULING:
                recommendations.extend(self._analyze_scheduling(provider))
            elif opt_type == OptimizationType.STORAGE:
                recommendations.extend(self._analyze_storage(provider))
            elif opt_type == OptimizationType.NETWORKING:
                recommendations.extend(self._analyze_networking(provider))
            elif opt_type == OptimizationType.LICENSES:
                recommendations.extend(self._analyze_licenses(provider))
            elif opt_type == OptimizationType.RESERVATIONS:
                recommendations.extend(self._analyze_reservations(provider))
        
        return recommendations
    
    def _analyze_rightsizing(self, provider: str) -> List[CostRecommendation]:
        """Analyze rightsizing opportunities"""
        recommendations = []
        
        if provider == 'aws':
            recommendations.extend(self._aws_rightsizing())
        elif provider == 'azure':
            recommendations.extend(self._azure_rightsizing())
        elif provider == 'gcp':
            recommendations.extend(self._gcp_rightsizing())
        elif provider == 'onprem':
            recommendations.extend(self._onprem_rightsizing())
        
        return recommendations
    
    def _aws_rightsizing(self) -> List[CostRecommendation]:
        """AWS rightsizing analysis"""
        # Placeholder for AWS EC2 rightsizing
        return [
            CostRecommendation(
                resource_id="i-1234567890abcdef0",
                resource_name="web-server-1",
                resource_type="ec2_instance",
                provider="aws",
                current_cost=150.0,
                projected_savings=45.0,
                optimization_type=OptimizationType.RIGHTSIZING,
                confidence=0.85,
                effort="low",
                description="EC2 instance is consistently underutilized (15% CPU average)",
                implementation_steps=[
                    "Analyze CloudWatch metrics for the past 30 days",
                    "Verify application can run on smaller instance type",
                    "Schedule downtime during instance resize",
                    "Test application performance on new instance type"
                ]
            ),
            CostRecommendation(
                resource_id="i-0987654321fedcba0",
                resource_name="batch-worker-3",
                resource_type="ec2_instance",
                provider="aws",
                current_cost=200.0,
                projected_savings=80.0,
                optimization_type=OptimizationType.RIGHTSIZING,
                confidence=0.90,
                effort="medium",
                description="Batch worker instances can use spot instances for 60% cost reduction",
                implementation_steps=[
                    "Identify batch workloads suitable for spot instances",
                    "Implement spot instance interruption handling",
                    "Update Auto Scaling Group to use mixed instances",
                    "Monitor spot instance termination notices"
                ]
            )
        ]
    
    def _azure_rightsizing(self) -> List[CostRecommendation]:
        """Azure rightsizing analysis"""
        return [
            CostRecommendation(
                resource_id="/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                resource_name="app-server-1",
                resource_type="virtual_machine",
                provider="azure",
                current_cost=180.0,
                projected_savings=72.0,
                optimization_type=OptimizationType.RIGHTSIZING,
                confidence=0.80,
                effort="low",
                description="Azure VM is overprovisioned for current workload",
                implementation_steps=[
                    "Review Azure Monitor metrics",
                    "Resize VM to appropriate size",
                    "Validate application performance",
                    "Update cost allocation tags"
                ]
            )
        ]
    
    def _gcp_rightsizing(self) -> List[CostRecommendation]:
        """GCP rightsizing analysis"""
        return [
            CostRecommendation(
                resource_id="projects/project-123/zones/us-central1-a/instances/instance-1",
                resource_name="data-processor-1",
                resource_type="compute_instance",
                provider="gcp",
                current_cost=120.0,
                projected_savings=48.0,
                optimization_type=OptimizationType.RIGHTSIZING,
                confidence=0.75,
                effort="low",
                description="GCP instance can be downsized based on usage patterns",
                implementation_steps=[
                    "Analyze Cloud Monitoring metrics",
                    "Select appropriate machine type",
                    "Schedule instance migration",
                    "Verify performance after migration"
                ]
            )
        ]
    
    def _onprem_rightsizing(self) -> List[CostRecommendation]:
        """On-premise rightsizing analysis"""
        return [
            CostRecommendation(
                resource_id="onprem-server-01",
                resource_name="legacy-app-server",
                resource_type="physical_server",
                provider="onprem",
                current_cost=300.0,
                projected_savings=150.0,
                optimization_type=OptimizationType.RIGHTSIZING,
                confidence=0.70,
                effort="high",
                description="Physical server is underutilized and can be migrated to cloud",
                implementation_steps=[
                    "Assess application cloud compatibility",
                    "Plan migration strategy",
                    "Set up cloud infrastructure",
                    "Execute migration and decommission"
                ]
            )
        ]
    
    def _analyze_scheduling(self, provider: str) -> List[CostRecommendation]:
        """Analyze scheduling opportunities"""
        recommendations = []
        
        if provider == 'aws':
            recommendations.extend([
                CostRecommendation(
                    resource_id="i-dev-server-01",
                    resource_name="development-server",
                    resource_type="ec2_instance",
                    provider="aws",
                    current_cost=100.0,
                    projected_savings=70.0,
                    optimization_type=OptimizationType.SCHEDULING,
                    confidence=0.95,
                    effort="low",
                    description="Development server runs 24/7 but only used during business hours",
                    implementation_steps=[
                        "Create start/stop schedules using AWS Instance Scheduler",
                        "Configure schedules for business hours (9am-6pm, weekdays)",
                        "Test automatic start/stop functionality",
                        "Notify team of new schedule"
                    ]
                )
            ])
        
        return recommendations
    
    def _analyze_storage(self, provider: str) -> List[CostRecommendation]:
        """Analyze storage optimization opportunities"""
        recommendations = []
        
        if provider == 'aws':
            recommendations.extend([
                CostRecommendation(
                    resource_id="s3-bucket-archive",
                    resource_name="archive-storage-bucket",
                    resource_type="s3_bucket",
                    provider="aws",
                    current_cost=50.0,
                    projected_savings=35.0,
                    optimization_type=OptimizationType.STORAGE,
                    confidence=0.90,
                    effort="medium",
                    description="Archive data in S3 Standard can be moved to Glacier for cost savings",
                    implementation_steps=[
                        "Identify objects older than 90 days",
                        "Set up S3 lifecycle policy",
                        "Configure Glacier retrieval options",
                        "Monitor cost savings"
                    ]
                )
            ])
        
        return recommendations
    
    def _analyze_networking(self, provider: str) -> List[CostRecommendation]:
        """Analyze network optimization opportunities"""
        return []
    
    def _analyze_licenses(self, provider: str) -> List[CostRecommendation]:
        """Analyze license optimization opportunities"""
        return []
    
    def _analyze_reservations(self, provider: str) -> List[CostRecommendation]:
        """Analyze reservation opportunities"""
        recommendations = []
        
        if provider == 'aws':
            recommendations.extend([
                CostRecommendation(
                    resource_id="ri-analysis",
                    resource_name="production-instances",
                    resource_type="reservation",
                    provider="aws",
                    current_cost=500.0,
                    projected_savings=150.0,
                    optimization_type=OptimizationType.RESERVATIONS,
                    confidence=0.85,
                    effort="medium",
                    description="Production instances have steady usage and can benefit from Reserved Instances",
                    implementation_steps=[
                        "Analyze instance usage patterns",
                        "Calculate optimal RI term and payment option",
                        "Purchase Reserved Instances",
                        "Update cost allocation"
                    ]
                )
            ])
        
        return recommendations
    
    def generate_cost_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive cost optimization report"""
        if not self.recommendations:
            return {"error": "No recommendations available. Run analyze_costs first."}
        
        # Calculate summary metrics
        total_current_cost = sum(r.current_cost for r in self.recommendations)
        total_potential_savings = sum(r.projected_savings for r in self.recommendations)
        avg_savings_percentage = (total_potential_savings / total_current_cost * 100) if total_current_cost > 0 else 0
        
        # Group recommendations by type
        recommendations_by_type = {}
        for rec in self.recommendations:
            opt_type = rec.optimization_type.value
            if opt_type not in recommendations_by_type:
                recommendations_by_type[opt_type] = []
            recommendations_by_type[opt_type].append(rec)
        
        # Group recommendations by provider
        recommendations_by_provider = {}
        for rec in self.recommendations:
            provider = rec.provider
            if provider not in recommendations_by_provider:
                recommendations_by_provider[provider] = []
            recommendations_by_provider[provider].append(rec)
        
        # Generate implementation plan
        implementation_plan = self._generate_implementation_plan()
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_period": f"{self.config['analysis_period_days']} days",
            "currency": self.config['currency'],
            "summary": {
                "total_recommendations": len(self.recommendations),
                "total_current_cost": total_current_cost,
                "total_potential_savings": total_potential_savings,
                "average_savings_percentage": round(avg_savings_percentage, 2),
                "high_confidence_recommendations": len([r for r in self.recommendations if r.confidence >= 0.8]),
                "low_effort_recommendations": len([r for r in self.recommendations if r.effort == 'low'])
            },
            "recommendations_by_type": {
                opt_type: {
                    "count": len(recs),
                    "total_savings": sum(r.projected_savings for r in recs),
                    "recommendations": [self._serialize_recommendation(r) for r in recs[:5]]  # Top 5 per type
                }
                for opt_type, recs in recommendations_by_type.items()
            },
            "recommendations_by_provider": {
                provider: {
                    "count": len(recs),
                    "total_savings": sum(r.projected_savings for r in recs),
                    "recommendations": [self._serialize_recommendation(r) for r in recs[:5]]  # Top 5 per provider
                }
                for provider, recs in recommendations_by_provider.items()
            },
            "implementation_plan": implementation_plan,
            "all_recommendations": [self._serialize_recommendation(r) for r in self.recommendations]
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Cost optimization report saved to: {output_file}")
        
        return report
    
    def _serialize_recommendation(self, rec: CostRecommendation) -> Dict[str, Any]:
        """Serialize recommendation to dictionary"""
        return {
            "resource_id": rec.resource_id,
            "resource_name": rec.resource_name,
            "resource_type": rec.resource_type,
            "provider": rec.provider,
            "current_cost": rec.current_cost,
            "projected_savings": rec.projected_savings,
            "optimization_type": rec.optimization_type.value,
            "confidence": rec.confidence,
            "effort": rec.effort,
            "description": rec.description,
            "implementation_steps": rec.implementation_steps
        }
    
    def _generate_implementation_plan(self) -> Dict[str, Any]:
        """Generate prioritized implementation plan"""
        # Quick wins (high confidence, low effort)
        quick_wins = [r for r in self.recommendations if r.confidence >= 0.8 and r.effort == 'low']
        
        # Medium effort items
        medium_effort = [r for r in self.recommendations if r.effort == 'medium' and r.confidence >= 0.7]
        
        # High effort items
        high_effort = [r for r in self.recommendations if r.effort == 'high']
        
        return {
            "phase_1_quick_wins": {
                "description": "High confidence, low effort optimizations",
                "items": [self._serialize_recommendation(r) for r in quick_wins[:10]],
                "estimated_savings": sum(r.projected_savings for r in quick_wins[:10]),
                "timeline": "1-2 weeks"
            },
            "phase_2_medium_effort": {
                "description": "Medium effort optimizations with good ROI",
                "items": [self._serialize_recommendation(r) for r in medium_effort[:10]],
                "estimated_savings": sum(r.projected_savings for r in medium_effort[:10]),
                "timeline": "1-2 months"
            },
            "phase_3_high_effort": {
                "description": "High effort strategic optimizations",
                "items": [self._serialize_recommendation(r) for r in high_effort[:5]],
                "estimated_savings": sum(r.projected_savings for r in high_effort[:5]),
                "timeline": "3-6 months"
            }
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Cost Optimizer")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--optimization-types", nargs="+",
                       choices=[t.value for t in OptimizationType],
                       default=['rightsizing', 'scheduling', 'storage'], help="Optimization types")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize optimizer
    optimizer = CostOptimizer(args.config)
    
    # Convert optimization types
    opt_types = [OptimizationType(t) for t in args.optimization_types]
    
    # Analyze costs
    recommendations = optimizer.analyze_costs(args.providers, opt_types)
    print(f"Generated {len(recommendations)} cost optimization recommendations")
    
    # Generate report
    report = optimizer.generate_cost_report(args.output)
    
    # Print summary
    summary = report.get('summary', {})
    print(f"\nCost Optimization Summary:")
    print(f"Total Recommendations: {summary.get('total_recommendations', 0)}")
    print(f"Potential Savings: ${summary.get('total_potential_savings', 0):.2f}")
    print(f"Average Savings: {summary.get('average_savings_percentage', 0):.1f}%")
    
    if args.output:
        print(f"Report saved to: {args.output}")

if __name__ == "__main__":
    main()
