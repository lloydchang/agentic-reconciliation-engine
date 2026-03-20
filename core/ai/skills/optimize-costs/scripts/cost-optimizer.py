#!/usr/bin/env python3
"""
Advanced AI Cost Optimizer Script

Multi-cloud automation for AI-powered cost optimization across AWS, Azure, GCP, and on-premise environments
with ML-based recommendations, predictive spending analysis, and automated cost-saving measures.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

# AI/ML imports
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error
    import statsmodels.api as sm
    from prophet import Prophet
    import warnings
    warnings.filterwarnings('ignore')
except ImportError as e:
    logging.warning(f"AI/ML libraries not available: {e}. Falling back to basic functionality.")

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
    ai_enhanced: bool = False
    predicted_cost_trend: Optional[str] = None

@dataclass
class CostAnalysis:
    provider: str
    total_current_cost: float
    total_projected_savings: float
    recommendations_count: int
    risk_assessment: str
    predictive_insights: List[str]

class AICostOptimizer:
    """Advanced AI-powered cost optimizer with ML and predictive analytics"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.recommendations = []
        self.config = self._load_config(config_file)
        
        # Initialize AI models if available
        self.ml_model = None
        self.anomaly_detector = None
        self.scaler = None
        self.time_series_models = {}
        self._initialize_ai_models()
        
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
            'analysis_period_days': 90,  # Extended for AI analysis
            'currency': 'USD',
            'ai_config': {
                'enable_ml_optimization': True,
                'enable_predictive_analysis': True,
                'enable_anomaly_detection': True,
                'prediction_horizon_days': 30,
                'confidence_threshold': 0.7,
                'historical_data_months': 6
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
    
    def _initialize_ai_models(self):
        """Initialize AI/ML models if libraries are available"""
        try:
            # ML model for cost optimization predictions
            self.ml_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            # Anomaly detection for unusual cost patterns
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=50
            )
            
            # Feature scaler
            self.scaler = StandardScaler()
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize AI models: {e}")
    
    def analyze_costs_with_ai(self, providers: List[str], optimization_types: List[OptimizationType], 
                             include_historical: bool = True) -> Tuple[List[CostRecommendation], List[CostAnalysis]]:
        """Analyze costs across providers using AI/ML techniques"""
        logger.info(f"Performing AI-enhanced cost analysis for providers: {providers}")
        
        all_recommendations = []
        analyses = []
        
        for provider in providers:
            if provider not in self.config['providers']:
                logger.warning(f"Provider {provider} not in configuration")
                continue
            
            if not self.config['providers'][provider]['enabled']:
                logger.info(f"Provider {provider} is disabled")
                continue
            
            try:
                # AI-powered analysis for this provider
                provider_recommendations, provider_analysis = self._analyze_provider_costs_with_ai(
                    provider, optimization_types, include_historical
                )
                all_recommendations.extend(provider_recommendations)
                analyses.append(provider_analysis)
                
                logger.info(f"Generated {len(provider_recommendations)} AI-enhanced recommendations for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to analyze costs for provider {provider}: {e}")
                # Fallback to basic analysis
                basic_recommendations = self._analyze_provider_costs_basic(provider, optimization_types)
                all_recommendations.extend(basic_recommendations)
        
        # Apply AI-based filtering and prioritization
        filtered_recommendations = self._ai_filter_recommendations(all_recommendations)
        
        return filtered_recommendations, analyses
    
    def _analyze_provider_costs_with_ai(self, provider: str, optimization_types: List[OptimizationType], 
                                       include_historical: bool) -> Tuple[List[CostRecommendation], CostAnalysis]:
        """AI-powered cost analysis for a specific provider"""
        recommendations = []
        
        # Get cost data
        cost_data = self._collect_cost_data(provider, include_historical)
        
        if not cost_data:
            logger.warning(f"No cost data available for {provider}")
            return [], CostAnalysis(provider, 0, 0, 0, "No data", [])
        
        # AI analysis for each optimization type
        for opt_type in optimization_types:
            if opt_type == OptimizationType.RIGHTSIZING:
                recommendations.extend(self._ai_rightsizing_analysis(cost_data, provider))
            elif opt_type == OptimizationType.SCHEDULING:
                recommendations.extend(self._ai_scheduling_analysis(cost_data, provider))
            elif opt_type == OptimizationType.STORAGE:
                recommendations.extend(self._ai_storage_analysis(cost_data, provider))
            elif opt_type == OptimizationType.NETWORKING:
                recommendations.extend(self._ai_networking_analysis(cost_data, provider))
            elif opt_type == OptimizationType.RESERVATIONS:
                recommendations.extend(self._ai_reservations_analysis(cost_data, provider))
        
        # Anomaly detection
        anomaly_insights = self._detect_cost_anomalies(cost_data)
        
        # Predictive analysis
        predictive_insights = self._predictive_cost_analysis(cost_data)
        
        # Overall analysis
        total_current_cost = sum(item.get('cost', 0) for item in cost_data)
        total_projected_savings = sum(rec.projected_savings for rec in recommendations)
        risk_assessment = self._assess_cost_risk(cost_data, recommendations)
        
        analysis = CostAnalysis(
            provider=provider,
            total_current_cost=total_current_cost,
            total_projected_savings=total_projected_savings,
            recommendations_count=len(recommendations),
            risk_assessment=risk_assessment,
            predictive_insights=predictive_insights + anomaly_insights
        )
        
        return recommendations, analysis
    
    def _collect_cost_data(self, provider: str, include_historical: bool) -> List[Dict[str, Any]]:
        """Collect cost data from provider APIs"""
        # This would integrate with actual cloud provider APIs
        # For now, return mock data structure
        return [
            {
                'resource_id': f'{provider}-instance-001',
                'resource_name': f'{provider.capitalize()} Instance 001',
                'resource_type': 'compute',
                'cost': 150.0,
                'usage_hours': 720,
                'cpu_utilization': 0.65,
                'memory_utilization': 0.8,
                'storage_gb': 100,
                'network_gb': 50,
                'tags': {'environment': 'production', 'team': 'backend'},
                'historical_costs': [140, 155, 148, 162, 150] if include_historical else []
            },
            # Add more mock data...
        ]
    
    def _ai_rightsizing_analysis(self, cost_data: List[Dict[str, Any]], provider: str) -> List[CostRecommendation]:
        """AI-powered rightsizing analysis"""
        recommendations = []
        
        try:
            for resource in cost_data:
                if resource.get('resource_type') != 'compute':
                    continue
                
                # ML-based utilization prediction
                features = [
                    resource.get('cpu_utilization', 0),
                    resource.get('memory_utilization', 0),
                    resource.get('usage_hours', 0) / 720,  # Normalize to monthly hours
                    len(resource.get('historical_costs', []))
                ]
                
                # Predict optimal instance size using ML
                optimal_size = self._predict_optimal_instance_size(features, provider)
                current_cost = resource.get('cost', 0)
                predicted_savings = self._calculate_rightsizing_savings(current_cost, optimal_size, provider)
                
                if predicted_savings > self.config['optimization_threshold']:
                    recommendation = CostRecommendation(
                        resource_id=resource['resource_id'],
                        resource_name=resource['resource_name'],
                        resource_type=resource['resource_type'],
                        provider=provider,
                        current_cost=current_cost,
                        projected_savings=predicted_savings,
                        optimization_type=OptimizationType.RIGHTSIZING,
                        confidence=0.85,  # AI confidence score
                        effort="medium",
                        description=f"AI analysis suggests rightsizing to {optimal_size} instance type",
                        implementation_steps=[
                            "Analyze current utilization patterns",
                            "Select optimal instance size based on AI recommendations",
                            "Schedule maintenance window for migration",
                            "Test performance after rightsizing",
                            "Monitor costs and performance post-migration"
                        ],
                        ai_enhanced=True,
                        predicted_cost_trend="decreasing"
                    )
                    recommendations.append(recommendation)
                    
        except Exception as e:
            logger.warning(f"AI rightsizing analysis failed: {e}")
            # Fallback to basic analysis
            recommendations.extend(self._basic_rightsizing_analysis(cost_data, provider))
        
        return recommendations
    
    def _predict_optimal_instance_size(self, features: List[float], provider: str) -> str:
        """Predict optimal instance size using ML"""
        if not self.ml_model:
            # Fallback logic
            cpu_util = features[0]
            mem_util = features[1]
            
            if cpu_util < 0.3 and mem_util < 0.4:
                return "small"
            elif cpu_util < 0.6 and mem_util < 0.7:
                return "medium"
            else:
                return "large"
        
        # ML prediction would go here
        return "medium"  # Placeholder
    
    def _calculate_rightsizing_savings(self, current_cost: float, optimal_size: str, provider: str) -> float:
        """Calculate potential savings from rightsizing"""
        # Simplified calculation - in reality would use actual pricing APIs
        size_multipliers = {
            "small": 0.6,
            "medium": 0.8,
            "large": 1.0,
            "xlarge": 1.5
        }
        
        optimal_multiplier = size_multipliers.get(optimal_size, 1.0)
        optimal_cost = current_cost * optimal_multiplier
        
        return max(0, current_cost - optimal_cost)
    
    def _ai_scheduling_analysis(self, cost_data: List[Dict[str, Any]], provider: str) -> List[CostRecommendation]:
        """AI-powered scheduling analysis for workload optimization"""
        recommendations = []
        
        try:
            # Analyze usage patterns to identify scheduling opportunities
            for resource in cost_data:
                if resource.get('resource_type') != 'compute':
                    continue
                
                usage_pattern = self._analyze_usage_pattern(resource)
                
                if usage_pattern.get('scheduleable_hours', 0) > 100:  # More than ~14 hours/day
                    schedule_savings = usage_pattern['scheduleable_hours'] * (resource.get('cost', 0) / 720)
                    
                    if schedule_savings > self.config['optimization_threshold']:
                        recommendation = CostRecommendation(
                            resource_id=resource['resource_id'],
                            resource_name=resource['resource_name'],
                            resource_type=resource['resource_type'],
                            provider=provider,
                            current_cost=resource.get('cost', 0),
                            projected_savings=schedule_savings,
                            optimization_type=OptimizationType.SCHEDULING,
                            confidence=0.8,
                            effort="low",
                            description=f"AI detected {usage_pattern['scheduleable_hours']} hours/day available for scheduling optimization",
                            implementation_steps=[
                                "Analyze usage patterns with AI",
                                "Define optimal operating hours",
                                "Implement auto-scheduling policies",
                                "Set up monitoring and alerts",
                                "Review and adjust schedule based on business needs"
                            ],
                            ai_enhanced=True,
                            predicted_cost_trend="decreasing"
                        )
                        recommendations.append(recommendation)
                        
        except Exception as e:
            logger.warning(f"AI scheduling analysis failed: {e}")
        
        return recommendations
    
    def _analyze_usage_pattern(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource usage patterns for scheduling opportunities"""
        # Simplified pattern analysis
        cpu_util = resource.get('cpu_utilization', 0)
        usage_hours = resource.get('usage_hours', 720)
        
        # Assume typical business hours usage
        business_hours = 8 * 30  # 8 hours/day * 30 days
        total_hours = 24 * 30
        
        # Estimate scheduleable hours (non-business hours)
        scheduleable_hours = max(0, usage_hours - business_hours)
        
        return {
            'business_hours_usage': business_hours,
            'total_usage': usage_hours,
            'scheduleable_hours': scheduleable_hours,
            'utilization_pattern': 'business_hours' if scheduleable_hours > 50 else 'continuous'
        }
    
    def _detect_cost_anomalies(self, cost_data: List[Dict[str, Any]]) -> List[str]:
        """Detect cost anomalies using ML"""
        insights = []
        
        try:
            if not self.anomaly_detector or not cost_data:
                return insights
            
            # Prepare data for anomaly detection
            costs = [item.get('cost', 0) for item in cost_data]
            if len(costs) < 10:
                return insights
            
            # Reshape for sklearn
            costs_array = np.array(costs).reshape(-1, 1)
            
            # Detect anomalies
            anomaly_scores = self.anomaly_detector.fit_predict(costs_array)
            anomaly_indices = np.where(anomaly_scores == -1)[0]
            
            if len(anomaly_indices) > 0:
                insights.append(f"Detected {len(anomaly_indices)} cost anomalies requiring investigation")
            
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
        
        return insights
    
    def _predictive_cost_analysis(self, cost_data: List[Dict[str, Any]]) -> List[str]:
        """Predictive cost analysis using time series forecasting"""
        insights = []
        
        try:
            if not cost_data or len(cost_data) < 5:
                return insights
            
            # Extract historical costs
            all_historical = []
            for item in cost_data:
                historical = item.get('historical_costs', [])
                if historical:
                    all_historical.extend(historical)
            
            if len(all_historical) < 10:
                return insights
            
            # Simple trend analysis
            recent_avg = statistics.mean(all_historical[-5:])
            older_avg = statistics.mean(all_historical[:5])
            
            if recent_avg > older_avg * 1.1:
                insights.append(f"Cost trend increasing by {((recent_avg/older_avg)-1)*100:.1f}% - investigate drivers")
            elif recent_avg < older_avg * 0.9:
                insights.append(f"Cost trend decreasing by {((older_avg/recent_avg)-1)*100:.1f}% - validate optimization effectiveness")
            
        except Exception as e:
            logger.warning(f"Predictive analysis failed: {e}")
        
        return insights
    
    def _assess_cost_risk(self, cost_data: List[Dict[str, Any]], recommendations: List[CostRecommendation]) -> str:
        """Assess overall cost optimization risk"""
        total_current = sum(item.get('cost', 0) for item in cost_data)
        total_savings = sum(rec.projected_savings for rec in recommendations)
        savings_percentage = (total_savings / total_current) * 100 if total_current > 0 else 0
        
        if savings_percentage > 30:
            return "High risk - Large cost reduction may impact performance"
        elif savings_percentage > 15:
            return "Medium risk - Moderate cost reduction with potential performance impact"
        else:
            return "Low risk - Conservative optimization approach"
    
    def _ai_filter_recommendations(self, recommendations: List[CostRecommendation]) -> List[CostRecommendation]:
        """AI-based filtering and prioritization of recommendations"""
        # Filter by threshold
        filtered = [
            r for r in recommendations 
            if r.projected_savings >= self.config['optimization_threshold']
        ]
        
        # Sort by AI-enhanced confidence and savings
        filtered.sort(key=lambda x: (x.confidence if x.ai_enhanced else 0.5, -x.projected_savings), reverse=True)
        
        return filtered[:50]  # Limit to top 50 recommendations
    
    # Fallback methods for when AI is not available
    def _analyze_provider_costs_basic(self, provider: str, optimization_types: List[OptimizationType]) -> List[CostRecommendation]:
        """Basic cost analysis without AI"""
        recommendations = []
        
        for opt_type in optimization_types:
            if opt_type == OptimizationType.RIGHTSIZING:
                recommendations.extend(self._basic_rightsizing_analysis([], provider))
        
        return recommendations
    
    def _basic_rightsizing_analysis(self, cost_data: List[Dict[str, Any]], provider: str) -> List[CostRecommendation]:
        """Basic rightsizing analysis"""
        # Simplified basic analysis
        return []
    
    def generate_cost_report(self, recommendations: List[CostRecommendation], 
                           analyses: List[CostAnalysis], output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive cost optimization report"""
        logger.info("Generating AI-enhanced cost optimization report")
        
        total_current_cost = sum(analysis.total_current_cost for analysis in analyses)
        total_projected_savings = sum(analysis.total_projected_savings for analysis in analyses)
        total_recommendations = sum(analysis.recommendations_count for analysis in analyses)
        
        # AI insights summary
        ai_recommendations = [r for r in recommendations if r.ai_enhanced]
        predictive_insights = []
        for analysis in analyses:
            predictive_insights.extend(analysis.predictive_insights)
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_providers_analyzed': len(analyses),
                'total_current_cost': total_current_cost,
                'total_projected_savings': total_projected_savings,
                'savings_percentage': (total_projected_savings / total_current_cost * 100) if total_current_cost > 0 else 0,
                'total_recommendations': total_recommendations,
                'ai_enhanced_recommendations': len(ai_recommendations),
                'predictive_insights_count': len(predictive_insights)
            },
            'provider_breakdown': [
                {
                    'provider': analysis.provider,
                    'current_cost': analysis.total_current_cost,
                    'projected_savings': analysis.total_projected_savings,
                    'recommendations_count': analysis.recommendations_count,
                    'risk_assessment': analysis.risk_assessment,
                    'predictive_insights': analysis.predictive_insights
                }
                for analysis in analyses
            ],
            'top_recommendations': [
                {
                    'resource_name': rec.resource_name,
                    'provider': rec.provider,
                    'optimization_type': rec.optimization_type.value,
                    'current_cost': rec.current_cost,
                    'projected_savings': rec.projected_savings,
                    'confidence': rec.confidence,
                    'ai_enhanced': rec.ai_enhanced,
                    'description': rec.description
                }
                for rec in recommendations[:20]
            ],
            'predictive_insights': predictive_insights[:10],
            'recommendations_by_type': self._count_recommendations_by_type(recommendations)
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Cost optimization report saved to: {output_file}")
        
        return report
    
    def _count_recommendations_by_type(self, recommendations: List[CostRecommendation]) -> Dict[str, int]:
        """Count recommendations by optimization type"""
        counts = {}
        for rec in recommendations:
            opt_type = rec.optimization_type.value
            counts[opt_type] = counts.get(opt_type, 0) + 1
        return counts
    
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
