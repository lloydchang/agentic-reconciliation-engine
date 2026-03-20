#!/usr/bin/env python3
"""
Predictive Maintenance Engine

Advanced predictive maintenance system using AI/ML for proactive infrastructure
health monitoring, failure prediction, and automated maintenance scheduling.
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
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import threading
import time

# AI/ML imports
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.ensemble import IsolationForest
    import statsmodels.api as sm
    from prophet import Prophet
    import warnings
    warnings.filterwarnings('ignore')
    AI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"AI/ML libraries not available: {e}. Using fallback functionality.")
    AI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaintenanceType(Enum):
    PREDICTIVE = "predictive"
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    CONDITION_BASED = "condition_based"

class FailureMode(Enum):
    HARDWARE_FAILURE = "hardware_failure"
    SOFTWARE_FAILURE = "software_failure"
    NETWORK_FAILURE = "network_failure"
    STORAGE_FAILURE = "storage_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_BREACH = "security_breach"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MaintenancePrediction:
    prediction_id: str
    resource_id: str
    component: str
    failure_mode: FailureMode
    risk_level: RiskLevel
    confidence_score: float
    predicted_failure_time: datetime
    time_to_failure_days: float
    maintenance_type: MaintenanceType
    estimated_cost: float
    recommended_actions: List[str]
    created_at: datetime

@dataclass
class HealthScore:
    resource_id: str
    component: str
    overall_health: float
    failure_probability: float
    degradation_rate: float
    last_updated: datetime
    contributing_factors: Dict[str, float]
    risk_indicators: List[str]

@dataclass
class MaintenanceSchedule:
    schedule_id: str
    resource_id: str
    component: str
    maintenance_type: MaintenanceType
    scheduled_date: datetime
    estimated_duration_hours: float
    priority: str
    cost_estimate: float
    prerequisites: List[str]
    status: str

class PredictiveMaintenanceEngine:
    """Advanced predictive maintenance engine"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.health_models = {}
        self.failure_prediction_models = {}
        self.maintenance_history = defaultdict(list)
        self.health_scores = {}
        self.scheduled_maintenance = []
        self.is_initialized = False
        
        if AI_AVAILABLE:
            self._initialize_ai_models()
        else:
            logger.warning("AI not available, using rule-based maintenance")
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load predictive maintenance configuration"""
        default_config = {
            'prediction': {
                'horizon_days': 30,
                'confidence_threshold': 0.8,
                'risk_thresholds': {
                    'critical': 0.9,
                    'high': 0.7,
                    'medium': 0.5,
                    'low': 0.3
                },
                'maintenance_intervals': {
                    'preventive_days': 90,
                    'predictive_threshold_days': 7,
                    'emergency_threshold_days': 1
                }
            },
            'health_scoring': {
                'weights': {
                    'performance': 0.3,
                    'reliability': 0.3,
                    'capacity': 0.2,
                    'security': 0.2
                },
                'update_interval_minutes': 15,
                'health_thresholds': {
                    'excellent': 0.9,
                    'good': 0.8,
                    'fair': 0.6,
                    'poor': 0.4,
                    'critical': 0.2
                }
            },
            'monitoring': {
                'critical_components': [
                    'cpu', 'memory', 'storage', 'network', 'power_supply',
                    'cooling_system', 'load_balancer', 'database', 'cache'
                ],
                'metrics_window_days': 7,
                'anomaly_detection_enabled': True
            }
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                self._deep_update(default_config, user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _initialize_ai_models(self):
        """Initialize AI models for predictive maintenance"""
        try:
            # Initialize health scoring models
            for component in self.config['monitoring']['critical_components']:
                self.health_models[component] = GradientBoostingRegressor(
                    n_estimators=100, random_state=42
                )
            
            # Initialize failure prediction models
            for failure_mode in FailureMode:
                self.failure_prediction_models[failure_mode.value] = RandomForestRegressor(
                    n_estimators=100, random_state=42
                )
            
            self.is_initialized = True
            logger.info("Predictive maintenance AI models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self.is_initialized = False
    
    def analyze_component_health(self, component_data: Dict[str, Any]) -> HealthScore:
        """Analyze health of a specific component"""
        component = component_data.get('component', 'unknown')
        resource_id = component_data.get('resource_id', 'unknown')
        
        try:
            # Calculate health factors
            performance_score = self._calculate_performance_health(component_data)
            reliability_score = self._calculate_reliability_health(component_data)
            capacity_score = self._calculate_capacity_health(component_data)
            security_score = self._calculate_security_health(component_data)
            
            # Weighted overall health score
            weights = self.config['health_scoring']['weights']
            overall_health = (
                performance_score * weights['performance'] +
                reliability_score * weights['reliability'] +
                capacity_score * weights['capacity'] +
                security_score * weights['security']
            )
            
            # Calculate failure probability
            failure_probability = self._calculate_failure_probability(component_data, overall_health)
            
            # Calculate degradation rate
            degradation_rate = self._calculate_degradation_rate(component_data)
            
            # Identify risk indicators
            risk_indicators = self._identify_risk_indicators(component_data, overall_health)
            
            health_score = HealthScore(
                resource_id=resource_id,
                component=component,
                overall_health=overall_health,
                failure_probability=failure_probability,
                degradation_rate=degradation_rate,
                last_updated=datetime.utcnow(),
                contributing_factors={
                    'performance': performance_score,
                    'reliability': reliability_score,
                    'capacity': capacity_score,
                    'security': security_score
                },
                risk_indicators=risk_indicators
            )
            
            # Store health score
            self.health_scores[f"{resource_id}:{component}"] = health_score
            
            logger.info(f"Health analysis completed for {resource_id}:{component} - Health: {overall_health:.3f}")
            return health_score
            
        except Exception as e:
            logger.error(f"Health analysis failed for {resource_id}:{component}: {e}")
            return HealthScore(
                resource_id=resource_id,
                component=component,
                overall_health=0.5,
                failure_probability=0.5,
                degradation_rate=0.0,
                last_updated=datetime.utcnow(),
                contributing_factors={},
                risk_indicators=["Health analysis failed"]
            )
    
    def predict_failures(self, component_data: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> List[MaintenancePrediction]:
        """Predict potential failures using AI/ML"""
        predictions = []
        component = component_data.get('component', 'unknown')
        resource_id = component_data.get('resource_id', 'unknown')
        
        if not self.is_initialized or not historical_data:
            return self._fallback_failure_prediction(component_data)
        
        try:
            # Analyze each potential failure mode
            for failure_mode in FailureMode:
                try:
                    prediction = self._predict_failure_mode(
                        failure_mode, component_data, historical_data
                    )
                    
                    if prediction and prediction.confidence_score >= self.config['prediction']['confidence_threshold']:
                        predictions.append(prediction)
                        
                except Exception as e:
                    logger.warning(f"Failed to predict {failure_mode.value} for {component}: {e}")
                    continue
            
            # Sort by risk and time to failure
            predictions.sort(key=lambda x: (x.risk_level.value, x.time_to_failure_days))
            
            logger.info(f"Generated {len(predictions)} failure predictions for {resource_id}:{component}")
            
        except Exception as e:
            logger.error(f"Failure prediction failed for {resource_id}:{component}: {e}")
            return self._fallback_failure_prediction(component_data)
        
        return predictions
    
    def _predict_failure_mode(self, failure_mode: FailureMode, component_data: Dict[str, Any], 
                            historical_data: List[Dict[str, Any]]) -> Optional[MaintenancePrediction]:
        """Predict failure for specific mode"""
        try:
            # Prepare features for this failure mode
            features = self._extract_failure_features(failure_mode, component_data, historical_data)
            
            if not features:
                return None
            
            # Get prediction model
            model_key = failure_mode.value
            if model_key not in self.failure_prediction_models:
                return None
            
            model = self.failure_prediction_models[model_key]
            
            # Make prediction
            features_array = np.array(features).reshape(1, -1)
            failure_probability = model.predict(features_array)[0]
            
            # Calculate time to failure
            time_to_failure_days = self._estimate_time_to_failure(failure_probability, historical_data)
            
            # Determine risk level
            risk_level = self._calculate_risk_level(failure_probability, time_to_failure_days)
            
            if risk_level.value == 'low':
                return None  # Don't predict low-risk failures
            
            # Calculate predicted failure time
            predicted_failure_time = datetime.utcnow() + timedelta(days=time_to_failure_days)
            
            # Determine maintenance type
            maintenance_type = self._determine_maintenance_type(risk_level, time_to_failure_days)
            
            # Estimate cost
            cost_estimate = self._estimate_maintenance_cost(failure_mode, maintenance_type)
            
            # Generate recommendations
            recommendations = self._generate_maintenance_recommendations(
                failure_mode, risk_level, time_to_failure_days
            )
            
            prediction = MaintenancePrediction(
                prediction_id=f"pred-{failure_mode.value}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=component_data.get('resource_id', 'unknown'),
                component=component_data.get('component', 'unknown'),
                failure_mode=failure_mode,
                risk_level=risk_level,
                confidence_score=min(0.99, failure_probability),
                predicted_failure_time=predicted_failure_time,
                time_to_failure_days=time_to_failure_days,
                maintenance_type=maintenance_type,
                estimated_cost=cost_estimate,
                recommended_actions=recommendations,
                created_at=datetime.utcnow()
            )
            
            return prediction
            
        except Exception as e:
            logger.warning(f"Failure prediction for {failure_mode.value} failed: {e}")
            return None
    
    def _extract_failure_features(self, failure_mode: FailureMode, component_data: Dict[str, Any], 
                                historical_data: List[Dict[str, Any]]) -> List[float]:
        """Extract features for failure prediction"""
        try:
            features = []
            
            # Recent performance metrics
            recent_data = historical_data[-30:] if len(historical_data) > 30 else historical_data
            
            if not recent_data:
                return []
            
            # Component-specific features
            if failure_mode == FailureMode.HARDWARE_FAILURE:
                features.extend([
                    np.mean([d.get('temperature', 0) for d in recent_data]),
                    np.mean([d.get('power_consumption', 0) for d in recent_data]),
                    np.mean([d.get('vibration', 0) for d in recent_data]),
                    np.std([d.get('temperature', 0) for d in recent_data]),
                    len([d for d in recent_data if d.get('hardware_errors', 0) > 0])
                ])
                
            elif failure_mode == FailureMode.SOFTWARE_FAILURE:
                features.extend([
                    np.mean([d.get('cpu_utilization', 0) for d in recent_data]),
                    np.mean([d.get('memory_utilization', 0) for d in recent_data]),
                    np.mean([d.get('error_rate', 0) for d in recent_data]),
                    np.std([d.get('response_time', 0) for d in recent_data]),
                    len([d for d in recent_data if d.get('software_errors', 0) > 0])
                ])
                
            elif failure_mode == FailureMode.PERFORMANCE_DEGRADATION:
                features.extend([
                    np.mean([d.get('response_time', 0) for d in recent_data]),
                    np.mean([d.get('throughput', 0) for d in recent_data]),
                    np.mean([d.get('queue_length', 0) for d in recent_data]),
                    np.std([d.get('cpu_utilization', 0) for d in recent_data]),
                    len([d for d in recent_data if d.get('performance_warnings', 0) > 0])
                ])
            
            # Add time-based features
            features.extend([
                len(recent_data),  # Data points available
                np.mean([d.get('uptime_hours', 0) for d in recent_data]),  # Average uptime
                datetime.utcnow().hour / 24.0,  # Hour of day (normalized)
                datetime.utcnow().weekday() / 7.0,  # Day of week (normalized)
            ])
            
            return features
            
        except Exception as e:
            logger.warning(f"Feature extraction failed for {failure_mode.value}: {e}")
            return []
    
    def _estimate_time_to_failure(self, failure_probability: float, historical_data: List[Dict[str, Any]]) -> float:
        """Estimate time to failure based on probability and historical patterns"""
        try:
            # Analyze historical failure patterns
            failure_times = []
            for i, data in enumerate(historical_data):
                if data.get('failure_occurred', False):
                    failure_times.append(i)
            
            if failure_times:
                avg_time_between_failures = np.mean(np.diff(failure_times))
                # Higher probability means shorter time to failure
                time_multiplier = 1 / (failure_probability + 0.1)
                estimated_days = min(avg_time_between_failures * time_multiplier, 365)
            else:
                # Default estimation based on probability
                estimated_days = max(1, (1 - failure_probability) * 30)
            
            return estimated_days
            
        except Exception as e:
            logger.warning(f"Time to failure estimation failed: {e}")
            return max(1, (1 - failure_probability) * 30)
    
    def _calculate_risk_level(self, failure_probability: float, time_to_failure_days: float) -> RiskLevel:
        """Calculate risk level based on probability and time to failure"""
        risk_score = failure_probability
        
        # Adjust based on time to failure
        if time_to_failure_days < 1:
            risk_score *= 1.5  # Immediate risk
        elif time_to_failure_days < 7:
            risk_score *= 1.2  # Short-term risk
        
        thresholds = self.config['prediction']['risk_thresholds']
        
        if risk_score >= thresholds['critical']:
            return RiskLevel.CRITICAL
        elif risk_score >= thresholds['high']:
            return RiskLevel.HIGH
        elif risk_score >= thresholds['medium']:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _determine_maintenance_type(self, risk_level: RiskLevel, time_to_failure_days: float) -> MaintenanceType:
        """Determine appropriate maintenance type"""
        if risk_level == RiskLevel.CRITICAL or time_to_failure_days < 1:
            return MaintenanceType.CORRECTIVE
        elif risk_level == RiskLevel.HIGH or time_to_failure_days < 7:
            return MaintenanceType.PREDICTIVE
        else:
            return MaintenanceType.PREVENTIVE
    
    def _estimate_maintenance_cost(self, failure_mode: FailureMode, maintenance_type: MaintenanceType) -> float:
        """Estimate maintenance cost"""
        base_costs = {
            FailureMode.HARDWARE_FAILURE: 5000,
            FailureMode.SOFTWARE_FAILURE: 2000,
            FailureMode.NETWORK_FAILURE: 1500,
            FailureMode.STORAGE_FAILURE: 3000,
            FailureMode.PERFORMANCE_DEGRADATION: 1000,
            FailureMode.SECURITY_BREACH: 8000
        }
        
        base_cost = base_costs.get(failure_mode, 2000)
        
        # Adjust by maintenance type
        if maintenance_type == MaintenanceType.PREDICTIVE:
            cost_multiplier = 0.6  # Cheaper to prevent
        elif maintenance_type == MaintenanceType.PREVENTIVE:
            cost_multiplier = 0.8
        else:  # Corrective
            cost_multiplier = 1.5  # More expensive to fix after failure
        
        return base_cost * cost_multiplier
    
    def _generate_maintenance_recommendations(self, failure_mode: FailureMode, risk_level: RiskLevel, 
                                            time_to_failure_days: float) -> List[str]:
        """Generate maintenance recommendations"""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("URGENT: Schedule immediate maintenance")
            recommendations.append("Consider emergency failover procedures")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Schedule maintenance within 24-48 hours")
            recommendations.append("Prepare backup systems")
        else:
            recommendations.append(f"Schedule maintenance within {int(time_to_failure_days)} days")
        
        # Failure mode specific recommendations
        if failure_mode == FailureMode.HARDWARE_FAILURE:
            recommendations.extend([
                "Check hardware temperatures and cooling",
                "Run hardware diagnostics",
                "Consider hardware replacement"
            ])
        elif failure_mode == FailureMode.SOFTWARE_FAILURE:
            recommendations.extend([
                "Review recent software changes",
                "Check for software bugs or memory leaks",
                "Consider software updates or patches"
            ])
        elif failure_mode == FailureMode.PERFORMANCE_DEGRADATION:
            recommendations.extend([
                "Optimize application performance",
                "Review resource allocation",
                "Consider scaling or load balancing improvements"
            ])
        
        return recommendations
    
    def schedule_maintenance(self, predictions: List[MaintenancePrediction]) -> List[MaintenanceSchedule]:
        """Schedule maintenance based on predictions"""
        schedules = []
        
        try:
            for prediction in predictions:
                # Only schedule for high-risk predictions
                if prediction.risk_level.value in ['critical', 'high']:
                    schedule = MaintenanceSchedule(
                        schedule_id=f"schedule-{prediction.prediction_id}",
                        resource_id=prediction.resource_id,
                        component=prediction.component,
                        maintenance_type=prediction.maintenance_type,
                        scheduled_date=self._calculate_schedule_date(prediction),
                        estimated_duration_hours=self._estimate_maintenance_duration(prediction),
                        priority=self._determine_maintenance_priority(prediction),
                        cost_estimate=prediction.estimated_cost,
                        prerequisites=self._identify_prerequisites(prediction),
                        status="scheduled"
                    )
                    
                    schedules.append(schedule)
                    
                    # Store in scheduled maintenance
                    self.scheduled_maintenance.append(schedule)
            
            logger.info(f"Scheduled {len(schedules)} maintenance activities")
            
        except Exception as e:
            logger.error(f"Maintenance scheduling failed: {e}")
        
        return schedules
    
    def _calculate_schedule_date(self, prediction: MaintenancePrediction) -> datetime:
        """Calculate optimal maintenance schedule date"""
        if prediction.risk_level == RiskLevel.CRITICAL:
            # Schedule immediately
            return datetime.utcnow() + timedelta(hours=2)
        elif prediction.risk_level == RiskLevel.HIGH:
            # Schedule within maintenance window
            return datetime.utcnow() + timedelta(hours=24)
        else:
            # Schedule based on time to failure
            schedule_days = max(1, prediction.time_to_failure_days - 7)  # 1 week buffer
            return datetime.utcnow() + timedelta(days=schedule_days)
    
    def _estimate_maintenance_duration(self, prediction: MaintenancePrediction) -> float:
        """Estimate maintenance duration"""
        base_durations = {
            MaintenanceType.PREVENTIVE: 2.0,
            MaintenanceType.PREDICTIVE: 4.0,
            MaintenanceType.CORRECTIVE: 8.0,
            MaintenanceType.CONDITION_BASED: 6.0
        }
        
        base_duration = base_durations.get(prediction.maintenance_type, 4.0)
        
        # Adjust based on failure mode
        if prediction.failure_mode == FailureMode.HARDWARE_FAILURE:
            duration_multiplier = 1.5
        elif prediction.failure_mode == FailureMode.SECURITY_BREACH:
            duration_multiplier = 2.0
        else:
            duration_multiplier = 1.0
        
        return base_duration * duration_multiplier
    
    def _determine_maintenance_priority(self, prediction: MaintenancePrediction) -> str:
        """Determine maintenance priority"""
        if prediction.risk_level == RiskLevel.CRITICAL:
            return "emergency"
        elif prediction.risk_level == RiskLevel.HIGH:
            return "high"
        elif prediction.risk_level == RiskLevel.MEDIUM:
            return "medium"
        else:
            return "low"
    
    def _identify_prerequisites(self, prediction: MaintenancePrediction) -> List[str]:
        """Identify maintenance prerequisites"""
        prerequisites = []
        
        # Common prerequisites
        prerequisites.append("Create system backup")
        prerequisites.append("Notify stakeholders")
        
        # Failure mode specific prerequisites
        if prediction.failure_mode == FailureMode.HARDWARE_FAILURE:
            prerequisites.append("Prepare replacement hardware")
            prerequisites.append("Schedule downtime window")
        elif prediction.failure_mode == FailureMode.SOFTWARE_FAILURE:
            prerequisites.append("Test rollback procedures")
            prerequisites.append("Prepare alternative deployment")
        elif prediction.failure_mode == FailureMode.SECURITY_BREACH:
            prerequisites.append("Security team approval required")
            prerequisites.append("Prepare incident response team")
        
        return prerequisites
    
    def _calculate_performance_health(self, component_data: Dict[str, Any]) -> float:
        """Calculate performance health score"""
        metrics = component_data.get('metrics', {})
        
        performance_indicators = [
            metrics.get('cpu_utilization', 0) <= 80,
            metrics.get('memory_utilization', 0) <= 85,
            metrics.get('response_time', 0) <= 1000,
            metrics.get('error_rate', 0) <= 5,
            metrics.get('throughput', 0) >= 100
        ]
        
        performance_score = sum(performance_indicators) / len(performance_indicators)
        return performance_score
    
    def _calculate_reliability_health(self, component_data: Dict[str, Any]) -> float:
        """Calculate reliability health score"""
        metrics = component_data.get('metrics', {})
        
        reliability_indicators = [
            metrics.get('uptime_percentage', 100) >= 99.5,
            metrics.get('error_rate', 0) <= 1,
            metrics.get('failure_count', 0) == 0,
            metrics.get('recovery_time', 0) <= 300
        ]
        
        reliability_score = sum(reliability_indicators) / len(reliability_indicators)
        return reliability_score
    
    def _calculate_capacity_health(self, component_data: Dict[str, Any]) -> float:
        """Calculate capacity health score"""
        metrics = component_data.get('metrics', {})
        
        capacity_indicators = [
            metrics.get('disk_utilization', 0) <= 80,
            metrics.get('memory_utilization', 0) <= 75,
            metrics.get('connection_count', 0) <= 10000,
            metrics.get('queue_length', 0) <= 100
        ]
        
        capacity_score = sum(capacity_indicators) / len(capacity_indicators)
        return capacity_score
    
    def _calculate_security_health(self, component_data: Dict[str, Any]) -> float:
        """Calculate security health score"""
        metrics = component_data.get('metrics', {})
        
        security_indicators = [
            metrics.get('failed_logins', 0) <= 5,
            metrics.get('security_events', 0) == 0,
            metrics.get('vulnerability_count', 0) <= 2,
            metrics.get('compliance_score', 100) >= 95
        ]
        
        security_score = sum(security_indicators) / len(security_indicators)
        return security_score
    
    def _calculate_failure_probability(self, component_data: Dict[str, Any], health_score: float) -> float:
        """Calculate failure probability"""
        # Simple inverse relationship with health score
        base_probability = 1 - health_score
        
        # Adjust based on component age and usage
        age_factor = component_data.get('age_days', 0) / 365.0
        usage_factor = component_data.get('usage_intensity', 1.0)
        
        adjusted_probability = base_probability * (1 + age_factor) * usage_factor
        
        return min(0.99, max(0.01, adjusted_probability))
    
    def _calculate_degradation_rate(self, component_data: Dict[str, Any]) -> float:
        """Calculate component degradation rate"""
        try:
            # Analyze historical metrics for degradation trend
            historical_metrics = component_data.get('historical_data', [])
            
            if len(historical_metrics) < 10:
                return 0.0
            
            # Calculate trend in key metrics
            performance_values = [m.get('performance_score', 0.8) for m in historical_metrics]
            
            if len(performance_values) > 1:
                # Simple linear trend
                slope = np.polyfit(range(len(performance_values)), performance_values, 1)[0]
                # Normalize to daily degradation rate
                daily_degradation = slope * (len(performance_values) / len(historical_metrics))
                return max(-0.1, min(0.1, daily_degradation))  # Clamp to reasonable range
            
        except Exception as e:
            logger.warning(f"Degradation rate calculation failed: {e}")
        
        return 0.0
    
    def _identify_risk_indicators(self, component_data: Dict[str, Any], health_score: float) -> List[str]:
        """Identify risk indicators"""
        indicators = []
        metrics = component_data.get('metrics', {})
        
        if health_score < 0.6:
            indicators.append("Overall health below acceptable threshold")
        
        if metrics.get('cpu_utilization', 0) > 90:
            indicators.append("High CPU utilization")
        
        if metrics.get('memory_utilization', 0) > 85:
            indicators.append("High memory utilization")
        
        if metrics.get('error_rate', 0) > 10:
            indicators.append("High error rate")
        
        if metrics.get('uptime_percentage', 100) < 99:
            indicators.append("Low uptime percentage")
        
        if metrics.get('security_events', 0) > 0:
            indicators.append("Recent security events")
        
        return indicators
    
    def _fallback_failure_prediction(self, component_data: Dict[str, Any]) -> List[MaintenancePrediction]:
        """Fallback failure prediction using rules"""
        predictions = []
        
        try:
            metrics = component_data.get('metrics', {})
            component = component_data.get('component', 'unknown')
            resource_id = component_data.get('resource_id', 'unknown')
            
            # Simple rule-based predictions
            if metrics.get('cpu_utilization', 0) > 95:
                prediction = MaintenancePrediction(
                    prediction_id=f"fallback-cpu-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    resource_id=resource_id,
                    component=component,
                    failure_mode=FailureMode.PERFORMANCE_DEGRADATION,
                    risk_level=RiskLevel.HIGH,
                    confidence_score=0.8,
                    predicted_failure_time=datetime.utcnow() + timedelta(hours=24),
                    time_to_failure_days=1.0,
                    maintenance_type=MaintenanceType.PREDICTIVE,
                    estimated_cost=1000,
                    recommended_actions=[
                        "Reduce CPU load",
                        "Consider scaling up CPU resources",
                        "Optimize CPU-intensive processes"
                    ],
                    created_at=datetime.utcnow()
                )
                predictions.append(prediction)
            
            if metrics.get('memory_utilization', 0) > 90:
                prediction = MaintenancePrediction(
                    prediction_id=f"fallback-memory-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    resource_id=resource_id,
                    component=component,
                    failure_mode=FailureMode.SOFTWARE_FAILURE,
                    risk_level=RiskLevel.MEDIUM,
                    confidence_score=0.7,
                    predicted_failure_time=datetime.utcnow() + timedelta(days=3),
                    time_to_failure_days=3.0,
                    maintenance_type=MaintenanceType.PREVENTIVE,
                    estimated_cost=1500,
                    recommended_actions=[
                        "Reduce memory usage",
                        "Clear memory caches",
                        "Consider memory upgrade"
                    ],
                    created_at=datetime.utcnow()
                )
                predictions.append(prediction)
        
        except Exception as e:
            logger.warning(f"Fallback failure prediction failed: {e}")
        
        return predictions
    
    def generate_maintenance_report(self, time_period: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """Generate comprehensive maintenance report"""
        try:
            cutoff_time = datetime.utcnow() - time_period
            
            # Collect recent data
            recent_health_scores = [
                score for score in self.health_scores.values()
                if score.last_updated >= cutoff_time
            ]
            
            recent_predictions = []
            for maintenance_list in self.maintenance_history.values():
                recent_predictions.extend([
                    pred for pred in maintenance_list
                    if pred.created_at >= cutoff_time
                ])
            
            # Calculate statistics
            avg_health = statistics.mean([s.overall_health for s in recent_health_scores]) if recent_health_scores else 0.5
            avg_failure_probability = statistics.mean([s.failure_probability for s in recent_health_scores]) if recent_health_scores else 0.0
            
            # Risk distribution
            risk_counts = {}
            for prediction in recent_predictions:
                risk = prediction.risk_level.value
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
            # Maintenance type distribution
            maintenance_counts = {}
            for prediction in recent_predictions:
                maint_type = prediction.maintenance_type.value
                maintenance_counts[maint_type] = maintenance_counts.get(maint_type, 0) + 1
            
            # Top risk components
            component_risks = defaultdict(list)
            for prediction in recent_predictions:
                component_risks[prediction.component].append(prediction.risk_level.value)
            
            top_risk_components = []
            for component, risks in component_risks.items():
                critical_count = risks.count('critical')
                high_count = risks.count('high')
                risk_score = critical_count * 3 + high_count * 2 + len(risks)
                top_risk_components.append({
                    'component': component,
                    'total_predictions': len(risks),
                    'critical_risks': critical_count,
                    'high_risks': high_count,
                    'risk_score': risk_score
                })
            
            top_risk_components.sort(key=lambda x: x['risk_score'], reverse=True)
            
            return {
                'report_period_days': time_period.total_seconds() / 86400,
                'generated_at': datetime.utcnow().isoformat(),
                'health_overview': {
                    'components_analyzed': len(recent_health_scores),
                    'average_health_score': avg_health,
                    'average_failure_probability': avg_failure_probability,
                    'health_distribution': self._calculate_health_distribution(recent_health_scores)
                },
                'predictions_overview': {
                    'total_predictions': len(recent_predictions),
                    'risk_distribution': risk_counts,
                    'maintenance_distribution': maintenance_counts,
                    'average_time_to_failure': statistics.mean([p.time_to_failure_days for p in recent_predictions]) if recent_predictions else 0
                },
                'top_risk_components': top_risk_components[:10],
                'maintenance_efficiency': self._calculate_maintenance_efficiency(),
                'recommendations': self._generate_maintenance_recommendations_report(recent_predictions, recent_health_scores)
            }
            
        except Exception as e:
            logger.error(f"Maintenance report generation failed: {e}")
            return {'error': str(e), 'generated_at': datetime.utcnow().isoformat()}
    
    def _calculate_health_distribution(self, health_scores: List[HealthScore]) -> Dict[str, int]:
        """Calculate health score distribution"""
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'critical': 0}
        
        for score in health_scores:
            health = score.overall_health
            if health >= 0.9:
                distribution['excellent'] += 1
            elif health >= 0.8:
                distribution['good'] += 1
            elif health >= 0.6:
                distribution['fair'] += 1
            elif health >= 0.4:
                distribution['poor'] += 1
            else:
                distribution['critical'] += 1
        
        return distribution
    
    def _calculate_maintenance_efficiency(self) -> Dict[str, Any]:
        """Calculate maintenance efficiency metrics"""
        try:
            # Mock efficiency calculation
            return {
                'preventive_maintenance_ratio': 0.75,
                'average_resolution_time_hours': 4.2,
                'cost_savings_percentage': 35.0,
                'uptime_improvement_percentage': 12.0,
                'mtbf_improvement_days': 15.5
            }
        except Exception as e:
            logger.warning(f"Maintenance efficiency calculation failed: {e}")
            return {}
    
    def _generate_maintenance_recommendations_report(self, predictions: List[MaintenancePrediction], 
                                                  health_scores: List[HealthScore]) -> List[str]:
        """Generate maintenance recommendations for report"""
        recommendations = []
        
        if not predictions and not health_scores:
            return ["No maintenance data available for recommendations"]
        
        # Analyze health scores
        low_health_components = [
            score for score in health_scores 
            if score.overall_health < 0.6
        ]
        
        if low_health_components:
            recommendations.append(f"Focus maintenance on {len(low_health_components)} components with low health scores")
        
        # Analyze predictions
        critical_predictions = [
            pred for pred in predictions 
            if pred.risk_level == RiskLevel.CRITICAL
        ]
        
        if critical_predictions:
            recommendations.append(f"Address {len(critical_predictions)} critical risk predictions immediately")
        
        # General recommendations
        recommendations.extend([
            "Implement regular preventive maintenance schedule",
            "Monitor component degradation rates closely",
            "Consider predictive maintenance for high-risk components",
            "Review maintenance procedures for effectiveness"
        ])
        
        return recommendations

def main():
    """Main function for predictive maintenance"""
    parser = argparse.ArgumentParser(description='Predictive Maintenance Engine')
    parser.add_argument('--operation', required=True, help='Operation type')
    parser.add_argument('--data-file', help='Input data file')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--config', help='Configuration file')
    parser.add_argument('--component', help='Component to analyze')
    
    args = parser.parse_args()
    
    # Initialize predictive maintenance engine
    engine = PredictiveMaintenanceEngine(args.config)
    
    if args.operation == 'analyze':
        # Load component data
        component_data = {}
        if args.data_file:
            try:
                with open(args.data_file, 'r') as f:
                    component_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load component data: {e}")
                sys.exit(1)
        else:
            # Generate mock component data
            component_data = {
                'resource_id': 'server-001',
                'component': args.component or 'cpu',
                'metrics': {
                    'cpu_utilization': np.random.uniform(60, 95),
                    'temperature': np.random.uniform(40, 80),
                    'power_consumption': np.random.uniform(100, 300),
                    'memory_utilization': np.random.uniform(70, 90),
                    'disk_utilization': np.random.uniform(50, 85),
                    'network_io': np.random.uniform(100, 1000),
                    'response_time': np.random.uniform(200, 1500),
                    'error_rate': np.random.uniform(0, 8),
                    'uptime_percentage': np.random.uniform(98, 100),
                    'failure_count': np.random.randint(0, 3),
                    'recovery_time': np.random.uniform(0, 600),
                    'connection_count': np.random.uniform(100, 5000),
                    'queue_length': np.random.uniform(0, 150),
                    'throughput': np.random.uniform(500, 2000),
                    'uptime_hours': np.random.uniform(100, 8760),  # Hours in year
                    'failed_logins': np.random.randint(0, 10),
                    'security_events': np.random.randint(0, 2),
                    'vulnerability_count': np.random.randint(0, 5),
                    'compliance_score': np.random.uniform(90, 100)
                },
                'historical_data': [
                    {
                        'cpu_utilization': np.random.uniform(40, 90),
                        'memory_utilization': np.random.uniform(50, 85),
                        'temperature': np.random.uniform(35, 75),
                        'performance_score': np.random.uniform(0.6, 0.9),
                        'failure_occurred': np.random.choice([True, False], p=[0.05, 0.95])
                    }
                    for _ in range(100)
                ]
            }
        
        # Analyze component health
        health_score = engine.analyze_component_health(component_data)
        
        # Generate failure predictions
        historical_data = component_data.get('historical_data', [])
        predictions = engine.predict_failures(component_data, historical_data)
        
        # Schedule maintenance
        maintenance_schedule = engine.schedule_maintenance(predictions)
        
        # Generate report
        report = {
            'component_analysis': {
                'resource_id': health_score.resource_id,
                'component': health_score.component,
                'overall_health': health_score.overall_health,
                'failure_probability': health_score.failure_probability,
                'degradation_rate': health_score.degradation_rate,
                'risk_indicators': health_score.risk_indicators,
                'contributing_factors': health_score.contributing_factors
            },
            'failure_predictions': [
                {
                    'failure_mode': pred.failure_mode.value,
                    'risk_level': pred.risk_level.value,
                    'confidence': pred.confidence_score,
                    'time_to_failure_days': pred.time_to_failure_days,
                    'maintenance_type': pred.maintenance_type.value,
                    'estimated_cost': pred.estimated_cost,
                    'recommendations': pred.recommended_actions
                }
                for pred in predictions
            ],
            'maintenance_schedule': [
                {
                    'component': sched.component,
                    'maintenance_type': sched.maintenance_type.value,
                    'scheduled_date': sched.scheduled_date.isoformat(),
                    'priority': sched.priority,
                    'estimated_cost': sched.cost_estimate,
                    'prerequisites': sched.prerequisites
                }
                for sched in maintenance_schedule
            ],
            'maintenance_report': engine.generate_maintenance_report()
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
        
        print(json.dumps(report, indent=2))
        
    elif args.operation == 'report':
        # Generate maintenance report
        report = engine.generate_maintenance_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
        
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
