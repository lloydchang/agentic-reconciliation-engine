#!/usr/bin/env python3
"""
Resource Optimizer Script

Multi-cloud automation for resource utilization analysis and rightsizing across AWS, Azure, GCP, and on-premise environments.
"""

# /// script
# dependencies = [
#   "boto3>=1.26.0",
#   "azure-mgmt-compute>=29.0.0",
#   "google-cloud-compute>=1.8.0",
#   "kubernetes>=25.0.0",
#   "pydantic>=1.10.0",
#   "requests>=2.28.0",
#   "pandas>=1.5.0",
#   "numpy>=1.24.0"
# ]
# ///

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

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
    NETWORK = "network"
    DATABASE = "database"
    CONTAINER = "container"
    SERVERLESS = "serverless"

class OptimizationAction(Enum):
    RIGHTSIZE = "rightsize"
    SCALE_DOWN = "scale_down"
    SCALE_UP = "scale_up"
    CONSOLIDATE = "consolidate"
    DECOMMISSION = "decommission"
    MIGRATE = "migrate"

class UtilizationLevel(Enum):
    UNDERUTILIZED = "underutilized"
    OPTIMAL = "optimal"
    OVERUTILIZED = "overutilized"
    CRITICAL = "critical"

@dataclass
class ResourceMetrics:
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    region: str
    environment: str
    cpu_utilization: float
    memory_utilization: float
    disk_utilization: float
    network_utilization: float
    current_capacity: Dict[str, Any]
    recommended_capacity: Dict[str, Any]
    utilization_score: float
    efficiency_score: float
    cost_per_hour: float
    last_updated: datetime
    metadata: Dict[str, Any]

@dataclass
class ResourceRecommendation:
    recommendation_id: str
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    current_state: UtilizationLevel
    recommended_action: OptimizationAction
    priority: str
    confidence: float
    expected_savings: float
    performance_impact: str
    implementation_complexity: str
    description: str
    current_config: Dict[str, Any]
    recommended_config: Dict[str, Any]
    implementation_steps: List[str]
    rollback_steps: List[str]
    risk_assessment: Dict[str, Any]

@dataclass
class OptimizationResult:
    optimization_id: str
    provider: str
    environment: str
    optimized_at: datetime
    total_resources_analyzed: int
    recommendations_generated: int
    recommendations_by_action: Dict[str, int]
    recommendations_by_priority: Dict[str, int]
    total_potential_savings: float
    implemented_recommendations: List[str]
    failed_recommendations: List[str]
    performance_baseline: Dict[str, float]
    performance_after: Dict[str, float]

#!/usr/bin/env python3
"""
Advanced AI Resource Optimizer Script

Multi-cloud automation for AI-powered resource utilization analysis, intelligent allocation,
and predictive scaling across AWS, Azure, GCP, and on-premise environments.
"""

# /// script
# dependencies = [
#   "boto3>=1.26.0",
#   "azure-mgmt-compute>=29.0.0",
#   "google-cloud-compute>=1.8.0",
#   "kubernetes>=25.0.0",
#   "pydantic>=1.10.0",
#   "requests>=2.28.0",
#   "pandas>=1.5.0",
#   "numpy>=1.24.0",
#   "scikit-learn>=1.2.0",
#   "statsmodels>=0.13.0",
#   "prophet>=1.1.0"
# ]
# ///

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
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
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

class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CONTAINER = "container"
    SERVERLESS = "serverless"

class OptimizationAction(Enum):
    RIGHTSIZE = "rightsize"
    SCALE_DOWN = "scale_down"
    SCALE_UP = "scale_up"
    CONSOLIDATE = "consolidate"
    DECOMMISSION = "decommission"
    MIGRATE = "migrate"

class UtilizationLevel(Enum):
    UNDERUTILIZED = "underutilized"
    OPTIMAL = "optimal"
    OVERUTILIZED = "overutilized"
    CRITICAL = "critical"

@dataclass
class ResourceMetrics:
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    region: str
    environment: str
    cpu_utilization: float
    memory_utilization: float
    disk_utilization: float
    network_utilization: float
    current_capacity: Dict[str, Any]
    recommended_capacity: Dict[str, Any]
    utilization_score: float
    efficiency_score: float
    cost_per_hour: float
    last_updated: datetime
    metadata: Dict[str, Any]
    ai_enhanced: bool = False
    predicted_utilization: Optional[Dict[str, float]] = None

@dataclass
class ResourceRecommendation:
    recommendation_id: str
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    current_state: UtilizationLevel
    recommended_action: OptimizationAction
    priority: str
    confidence: float
    expected_savings: float
    performance_impact: str
    implementation_complexity: str
    description: str
    current_config: Dict[str, Any]
    recommended_config: Dict[str, Any]
    implementation_steps: List[str]
    rollback_steps: List[str]
    risk_assessment: Dict[str, Any]
    ai_enhanced: bool = False
    predictive_insights: List[str] = None

@dataclass
class OptimizationResult:
    optimization_id: str
    provider: str
    environment: str
    optimized_at: datetime
    total_resources_analyzed: int
    recommendations_generated: int
    recommendations_by_action: Dict[str, int]
    recommendations_by_priority: Dict[str, int]
    total_potential_savings: float
    implemented_recommendations: List[str]
    failed_recommendations: List[str]
    performance_baseline: Dict[str, float]
    performance_after: Dict[str, float]
    ai_insights: List[str] = None

class IntelligentResourceAllocator:
    """AI-powered resource allocation and scaling engine"""
    
    def __init__(self):
        self.allocation_model = None
        self.scaling_model = None
        self.feature_scaler = StandardScaler()
        self.encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
        self.is_trained = False
        
    def train_allocation_model(self, historical_data: List[Dict[str, Any]]):
        """Train ML model for intelligent resource allocation"""
        try:
            if not historical_data:
                logger.warning("No historical data available for training")
                return
            
            # Prepare features
            features = []
            targets = []
            
            for data_point in historical_data:
                feature_vector = self._extract_allocation_features(data_point)
                features.append(feature_vector)
                
                # Target: optimal resource allocation score
                targets.append(data_point.get('optimal_allocation_score', 0.8))
            
            if len(features) < 10:
                logger.warning("Insufficient data for training allocation model")
                return
            
            X = np.array(features)
            y = np.array(targets)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.allocation_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            self.allocation_model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.allocation_model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"Allocation model trained - MAE: {mae:.3f}, R²: {r2:.3f}")
            self.is_trained = True
            
        except Exception as e:
            logger.warning(f"Failed to train allocation model: {e}")
    
    def train_scaling_model(self, scaling_data: List[Dict[str, Any]]):
        """Train ML model for predictive scaling"""
        try:
            if not scaling_data:
                logger.warning("No scaling data available for training")
                return
            
            # Prepare time series features
            features = []
            targets = []
            
            for data_point in scaling_data:
                feature_vector = self._extract_scaling_features(data_point)
                features.append(feature_vector)
                
                # Target: scaling decision (scale up/down/no change)
                targets.append(data_point.get('scaling_decision', 0))  # -1, 0, 1
            
            if len(features) < 10:
                logger.warning("Insufficient data for training scaling model")
                return
            
            X = np.array(features)
            y = np.array(targets)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.scaling_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                random_state=42,
                n_jobs=-1
            )
            
            self.scaling_model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.scaling_model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            
            logger.info(f"Scaling model trained - MAE: {mae:.3f}")
            
        except Exception as e:
            logger.warning(f"Failed to train scaling model: {e}")
    
    def predict_optimal_allocation(self, resource_metrics: ResourceMetrics) -> Dict[str, Any]:
        """Predict optimal resource allocation using ML"""
        if not self.is_trained or not self.allocation_model:
            return self._fallback_allocation(resource_metrics)
        
        try:
            features = self._extract_allocation_features_from_metrics(resource_metrics)
            features_scaled = self.feature_scaler.transform([features])
            
            prediction = self.allocation_model.predict(features_scaled)[0]
            
            # Convert prediction to allocation recommendations
            return {
                'cpu_cores': max(1, int(prediction * 4)),  # Scale to reasonable CPU cores
                'memory_gb': max(1, int(prediction * 8)),  # Scale to reasonable memory
                'confidence': min(0.95, max(0.1, prediction)),
                'ai_predicted': True
            }
            
        except Exception as e:
            logger.warning(f"Allocation prediction failed: {e}")
            return self._fallback_allocation(resource_metrics)
    
    def predict_scaling_action(self, resource_metrics: ResourceMetrics, 
                             historical_usage: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict scaling actions using ML"""
        if not self.scaling_model:
            return self._fallback_scaling(resource_metrics)
        
        try:
            features = self._extract_scaling_features_from_history(resource_metrics, historical_usage)
            features_scaled = self.feature_scaler.transform([features])
            
            prediction = self.scaling_model.predict(features_scaled)[0]
            
            # Interpret prediction
            if prediction > 0.3:
                action = "scale_up"
                confidence = min(0.9, prediction)
            elif prediction < -0.3:
                action = "scale_down"
                confidence = min(0.9, abs(prediction))
            else:
                action = "no_change"
                confidence = 0.8
            
            return {
                'action': action,
                'confidence': confidence,
                'prediction_score': prediction,
                'ai_predicted': True
            }
            
        except Exception as e:
            logger.warning(f"Scaling prediction failed: {e}")
            return self._fallback_scaling(resource_metrics)
    
    def _extract_allocation_features(self, data_point: Dict[str, Any]) -> List[float]:
        """Extract features for allocation model training"""
        return [
            data_point.get('cpu_utilization', 0),
            data_point.get('memory_utilization', 0),
            data_point.get('disk_utilization', 0),
            data_point.get('network_utilization', 0),
            data_point.get('workload_type_encoded', 0),  # 0=web, 1=batch, 2=ml, etc.
            data_point.get('time_of_day', 12),  # hour of day
            data_point.get('day_of_week', 1),  # 0-6
            data_point.get('concurrent_users', 10),
            data_point.get('request_rate', 100),
        ]
    
    def _extract_allocation_features_from_metrics(self, metrics: ResourceMetrics) -> List[float]:
        """Extract features from resource metrics for prediction"""
        return [
            metrics.cpu_utilization,
            metrics.memory_utilization,
            metrics.disk_utilization,
            metrics.network_utilization,
            0,  # workload_type_encoded (default)
            datetime.now().hour,
            datetime.now().weekday(),
            metrics.metadata.get('concurrent_users', 10),
            metrics.metadata.get('request_rate', 100),
        ]
    
    def _extract_scaling_features(self, data_point: Dict[str, Any]) -> List[float]:
        """Extract features for scaling model training"""
        return [
            data_point.get('current_cpu', 0),
            data_point.get('current_memory', 0),
            data_point.get('cpu_trend', 0),  # rate of change
            data_point.get('memory_trend', 0),
            data_point.get('time_to_peak', 24),  # hours to peak usage
            data_point.get('seasonal_pattern', 0),
            data_point.get('queue_length', 0),
            data_point.get('error_rate', 0),
        ]
    
    def _extract_scaling_features_from_history(self, metrics: ResourceMetrics, 
                                             historical: List[Dict[str, Any]]) -> List[float]:
        """Extract scaling features from current metrics and history"""
        # Calculate trends
        if historical:
            recent_cpu = [h.get('cpu_utilization', 0) for h in historical[-10:]]
            cpu_trend = np.polyfit(range(len(recent_cpu)), recent_cpu, 1)[0] if len(recent_cpu) > 1 else 0
            
            recent_memory = [h.get('memory_utilization', 0) for h in historical[-10:]]
            memory_trend = np.polyfit(range(len(recent_memory)), recent_memory, 1)[0] if len(recent_memory) > 1 else 0
        else:
            cpu_trend = memory_trend = 0
        
        return [
            metrics.cpu_utilization,
            metrics.memory_utilization,
            cpu_trend,
            memory_trend,
            24,  # time_to_peak (default)
            0,   # seasonal_pattern (default)
            metrics.metadata.get('queue_length', 0),
            metrics.metadata.get('error_rate', 0),
        ]
    
    def _fallback_allocation(self, metrics: ResourceMetrics) -> Dict[str, Any]:
        """Fallback allocation when AI is not available"""
        # Simple rule-based allocation
        cpu_cores = max(1, int(metrics.cpu_utilization * 4 / 100) + 1)
        memory_gb = max(1, int(metrics.memory_utilization * 8 / 100) + 1)
        
        return {
            'cpu_cores': cpu_cores,
            'memory_gb': memory_gb,
            'confidence': 0.5,
            'ai_predicted': False
        }
    
    def _fallback_scaling(self, metrics: ResourceMetrics) -> Dict[str, Any]:
        """Fallback scaling when AI is not available"""
        # Simple threshold-based scaling
        avg_utilization = (metrics.cpu_utilization + metrics.memory_utilization) / 2
        
        if avg_utilization > 85:
            action = "scale_up"
            confidence = 0.7
        elif avg_utilization < 25:
            action = "scale_down"
            confidence = 0.6
        else:
            action = "no_change"
            confidence = 0.8
        
        return {
            'action': action,
            'confidence': confidence,
            'ai_predicted': False
        }

class PredictiveResourceManager:
    """Predictive resource management using time series forecasting"""
    
    def __init__(self):
        self.forecasting_models = {}
        
    def forecast_resource_usage(self, resource_id: str, historical_data: List[Dict[str, Any]], 
                               forecast_hours: int = 24) -> Dict[str, Any]:
        """Forecast future resource usage using time series analysis"""
        try:
            if len(historical_data) < 24:  # Need minimum data for forecasting
                return self._simple_forecast(historical_data, forecast_hours)
            
            # Prepare data for Prophet
            df = pd.DataFrame(historical_data)
            if 'timestamp' not in df.columns:
                # Create timestamps if not present
                df['timestamp'] = pd.date_range(
                    end=datetime.now(), 
                    periods=len(df), 
                    freq='H'
                )
            
            df = df.rename(columns={'timestamp': 'ds'})
            
            forecasts = {}
            
            # Forecast CPU usage
            if 'cpu_utilization' in df.columns:
                cpu_model = Prophet(
                    yearly_seasonality=False,
                    weekly_seasonality=True,
                    daily_seasonality=True,
                    seasonality_mode='multiplicative'
                )
                
                cpu_df = df[['ds', 'cpu_utilization']].rename(columns={'cpu_utilization': 'y'})
                cpu_model.fit(cpu_df)
                
                future = cpu_model.make_future_dataframe(periods=forecast_hours, freq='H')
                cpu_forecast = cpu_model.predict(future)
                
                forecasts['cpu_utilization'] = {
                    'values': cpu_forecast['yhat'].tail(forecast_hours).tolist(),
                    'lower_bound': cpu_forecast['yhat_lower'].tail(forecast_hours).tolist(),
                    'upper_bound': cpu_forecast['yhat_upper'].tail(forecast_hours).tolist()
                }
            
            # Forecast memory usage
            if 'memory_utilization' in df.columns:
                memory_model = Prophet(
                    yearly_seasonality=False,
                    weekly_seasonality=True,
                    daily_seasonality=True,
                    seasonality_mode='multiplicative'
                )
                
                memory_df = df[['ds', 'memory_utilization']].rename(columns={'memory_utilization': 'y'})
                memory_model.fit(memory_df)
                
                future = memory_model.make_future_dataframe(periods=forecast_hours, freq='H')
                memory_forecast = memory_model.predict(future)
                
                forecasts['memory_utilization'] = {
                    'values': memory_forecast['yhat'].tail(forecast_hours).tolist(),
                    'lower_bound': memory_forecast['yhat_lower'].tail(forecast_hours).tolist(),
                    'upper_bound': memory_forecast['yhat_upper'].tail(forecast_hours).tolist()
                }
            
            # Store model for future use
            self.forecasting_models[resource_id] = {
                'cpu_model': cpu_model if 'cpu_utilization' in forecasts else None,
                'memory_model': memory_model if 'memory_utilization' in forecasts else None,
                'last_updated': datetime.now()
            }
            
            return {
                'forecasts': forecasts,
                'forecast_period_hours': forecast_hours,
                'confidence_intervals': True,
                'ai_generated': True
            }
            
        except Exception as e:
            logger.warning(f"Time series forecasting failed: {e}")
            return self._simple_forecast(historical_data, forecast_hours)
    
    def _simple_forecast(self, historical_data: List[Dict[str, Any]], forecast_hours: int) -> Dict[str, Any]:
        """Simple trend-based forecasting fallback"""
        if not historical_data:
            return {'forecasts': {}, 'ai_generated': False}
        
        # Calculate simple moving averages
        cpu_values = [d.get('cpu_utilization', 0) for d in historical_data[-24:]]
        memory_values = [d.get('memory_utilization', 0) for d in historical_data[-24:]]
        
        forecasts = {}
        
        if cpu_values:
            avg_cpu = statistics.mean(cpu_values)
            forecasts['cpu_utilization'] = {
                'values': [avg_cpu] * forecast_hours,
                'lower_bound': [max(0, avg_cpu * 0.8)] * forecast_hours,
                'upper_bound': [min(100, avg_cpu * 1.2)] * forecast_hours
            }
        
        if memory_values:
            avg_memory = statistics.mean(memory_values)
            forecasts['memory_utilization'] = {
                'values': [avg_memory] * forecast_hours,
                'lower_bound': [max(0, avg_memory * 0.8)] * forecast_hours,
                'upper_bound': [min(100, avg_memory * 1.2)] * forecast_hours
            }
        
        return {
            'forecasts': forecasts,
            'forecast_period_hours': forecast_hours,
            'confidence_intervals': False,
            'ai_generated': False
        }
    
    def detect_anomalies(self, resource_id: str, current_metrics: Dict[str, float], 
                        historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect anomalous resource usage patterns"""
        try:
            if len(historical_data) < 10:
                return {'anomalies_detected': [], 'ai_generated': False}
            
            anomalies = []
            
            # Simple statistical anomaly detection
            cpu_values = [d.get('cpu_utilization', 0) for d in historical_data]
            memory_values = [d.get('memory_utilization', 0) for d in historical_data]
            
            if cpu_values:
                cpu_mean = statistics.mean(cpu_values)
                cpu_stdev = statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
                
                current_cpu = current_metrics.get('cpu_utilization', 0)
                if abs(current_cpu - cpu_mean) > 3 * cpu_stdev and cpu_stdev > 0:
                    anomalies.append({
                        'metric': 'cpu_utilization',
                        'current_value': current_cpu,
                        'expected_range': [cpu_mean - cpu_stdev, cpu_mean + cpu_stdev],
                        'severity': 'high' if abs(current_cpu - cpu_mean) > 5 * cpu_stdev else 'medium'
                    })
            
            if memory_values:
                memory_mean = statistics.mean(memory_values)
                memory_stdev = statistics.stdev(memory_values) if len(memory_values) > 1 else 0
                
                current_memory = current_metrics.get('memory_utilization', 0)
                if abs(current_memory - memory_mean) > 3 * memory_stdev and memory_stdev > 0:
                    anomalies.append({
                        'metric': 'memory_utilization',
                        'current_value': current_memory,
                        'expected_range': [memory_mean - memory_stdev, memory_mean + memory_stdev],
                        'severity': 'high' if abs(current_memory - memory_mean) > 5 * memory_stdev else 'medium'
                    })
            
            return {
                'anomalies_detected': anomalies,
                'total_anomalies': len(anomalies),
                'ai_generated': True
            }
            
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            return {'anomalies_detected': [], 'ai_generated': False}

class AIResourceOptimizer:
    """Advanced AI-powered resource optimizer with ML and predictive analytics"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.metrics_history = []
        self.optimizations = []
        self.config = self._load_config(config_file)
        
        # Initialize AI components
        self.intelligent_allocator = IntelligentResourceAllocator()
        self.predictive_manager = PredictiveResourceManager()
        
        # Train AI models if data is available
        self._initialize_ai_models()
        
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load resource optimizer configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'optimization_thresholds': {
                'cpu_underutilized': 20.0,
                'cpu_overutilized': 80.0,
                'memory_underutilized': 30.0,
                'memory_overutilized': 85.0,
                'disk_underutilized': 25.0,
                'disk_overutilized': 90.0,
                'network_underutilized': 10.0,
                'network_overutilized': 80.0
            },
            'analysis_settings': {
                'analysis_period_days': 30,
                'min_utilization_samples': 10,
                'confidence_threshold': 0.7,
                'forecast_horizon_hours': 24,
                'ai_enabled': True
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
        """Initialize and train AI models"""
        try:
            # Load historical training data (mock data for demonstration)
            training_data = self._load_training_data()
            
            if training_data and self.config['analysis_settings']['ai_enabled']:
                logger.info("Training AI models for resource optimization...")
                
                # Train allocation model
                self.intelligent_allocator.train_allocation_model(training_data.get('allocation', []))
                
                # Train scaling model
                self.intelligent_allocator.train_scaling_model(training_data.get('scaling', []))
                
                logger.info("AI models trained successfully")
            else:
                logger.info("AI training data not available, using fallback methods")
                
        except Exception as e:
            logger.warning(f"Failed to initialize AI models: {e}")
    
    def _load_training_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load historical training data for AI models"""
        # In a real implementation, this would load from a database or file
        # For now, return empty data
        return {
            'allocation': [],
            'scaling': []
        }
    
    def analyze_resources_with_ai(self, providers: List[str], include_historical: bool = True) -> Tuple[List[ResourceRecommendation], Dict[str, Any]]:
        """Analyze resources across providers using AI/ML techniques"""
        logger.info(f"Performing AI-enhanced resource analysis for providers: {providers}")
        
        all_recommendations = []
        analysis_results = {}
        
        for provider in providers:
            if provider not in self.config['providers']:
                logger.warning(f"Provider {provider} not in configuration")
                continue
            
            if not self.config['providers'][provider]['enabled']:
                logger.info(f"Provider {provider} is disabled")
                continue
            
            try:
                # AI-powered analysis for this provider
                provider_recommendations, provider_analysis = self._analyze_provider_resources_with_ai(
                    provider, include_historical
                )
                all_recommendations.extend(provider_recommendations)
                analysis_results[provider] = provider_analysis
                
                logger.info(f"Generated {len(provider_recommendations)} AI-enhanced recommendations for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to analyze resources for provider {provider}: {e}")
                # Fallback to basic analysis
                basic_recommendations = self._analyze_provider_resources_basic(provider)
                all_recommendations.extend(basic_recommendations)
        
        # Apply AI-based filtering and prioritization
        filtered_recommendations = self._ai_filter_recommendations(all_recommendations)
        
        return filtered_recommendations, analysis_results
    
    def _analyze_provider_resources_with_ai(self, provider: str, include_historical: bool) -> Tuple[List[ResourceRecommendation], Dict[str, Any]]:
        """AI-powered resource analysis for a specific provider"""
        recommendations = []
        
        # Get resource data
        resource_data = self._collect_resource_data(provider, include_historical)
        
        if not resource_data:
            logger.warning(f"No resource data available for {provider}")
            return [], {'total_resources': 0, 'recommendations': 0, 'ai_insights': []}
        
        ai_insights = []
        
        for resource in resource_data:
            try:
                # AI-enhanced resource analysis
                resource_recommendations, resource_insights = self._analyze_resource_with_ai(
                    resource, provider, include_historical
                )
                recommendations.extend(resource_recommendations)
                ai_insights.extend(resource_insights)
                
            except Exception as e:
                logger.warning(f"AI analysis failed for resource {resource['resource_id']}: {e}")
                # Fallback to basic analysis
                basic_recommendations = self._analyze_resource_basic(resource, provider)
                recommendations.extend(basic_recommendations)
        
        analysis_result = {
            'total_resources': len(resource_data),
            'recommendations': len(recommendations),
            'ai_insights': ai_insights,
            'ai_enabled': True
        }
        
        return recommendations, analysis_result
    
    def _analyze_resource_with_ai(self, resource: Dict[str, Any], provider: str, 
                                include_historical: bool) -> Tuple[List[ResourceRecommendation], List[str]]:
        """AI-powered analysis for a single resource"""
        recommendations = []
        insights = []
        
        # Create ResourceMetrics object
        metrics = ResourceMetrics(
            resource_id=resource['resource_id'],
            resource_name=resource['resource_name'],
            resource_type=ResourceType(resource.get('resource_type', 'compute')),
            provider=provider,
            region=resource.get('region', 'unknown'),
            environment=resource.get('environment', 'production'),
            cpu_utilization=resource.get('cpu_utilization', 0),
            memory_utilization=resource.get('memory_utilization', 0),
            disk_utilization=resource.get('disk_utilization', 0),
            network_utilization=resource.get('network_utilization', 0),
            current_capacity=resource.get('current_capacity', {}),
            recommended_capacity=resource.get('recommended_capacity', {}),
            utilization_score=resource.get('utilization_score', 0.5),
            efficiency_score=resource.get('efficiency_score', 0.5),
            cost_per_hour=resource.get('cost_per_hour', 0),
            last_updated=datetime.now(),
            metadata=resource.get('metadata', {}),
            ai_enhanced=True
        )
        
        # Get historical data for predictive analysis
        historical_data = resource.get('historical_data', []) if include_historical else []
        
        # AI-based allocation prediction
        optimal_allocation = self.intelligent_allocator.predict_optimal_allocation(metrics)
        
        # Predictive scaling analysis
        scaling_prediction = self.intelligent_allocator.predict_scaling_action(metrics, historical_data)
        
        # Resource usage forecasting
        if historical_data:
            forecast = self.predictive_manager.forecast_resource_usage(
                resource['resource_id'], historical_data
            )
            metrics.predicted_utilization = {
                'cpu_forecast': forecast.get('forecasts', {}).get('cpu_utilization', {}).get('values', [])[:24],
                'memory_forecast': forecast.get('forecasts', {}).get('memory_utilization', {}).get('values', [])[:24]
            }
            
            # Generate predictive insights
            if forecast.get('ai_generated'):
                insights.append(f"Resource {resource['resource_name']} shows predictable usage patterns")
        
        # Anomaly detection
        current_metrics = {
            'cpu_utilization': metrics.cpu_utilization,
            'memory_utilization': metrics.memory_utilization
        }
        anomalies = self.predictive_manager.detect_anomalies(
            resource['resource_id'], current_metrics, historical_data
        )
        
        if anomalies.get('anomalies_detected'):
            for anomaly in anomalies['anomalies_detected']:
                insights.append(f"Anomaly detected in {anomaly['metric']}: {anomaly['current_value']:.1f}% (expected: {anomaly['expected_range'][0]:.1f}-{anomaly['expected_range'][1]:.1f}%)")
        
        # Generate AI-enhanced recommendations
        resource_recommendations = self._generate_ai_recommendations(
            metrics, optimal_allocation, scaling_prediction, anomalies
        )
        recommendations.extend(resource_recommendations)
        
        return recommendations, insights
    
    def _generate_ai_recommendations(self, metrics: ResourceMetrics, optimal_allocation: Dict[str, Any],
                                   scaling_prediction: Dict[str, Any], anomalies: Dict[str, Any]) -> List[ResourceRecommendation]:
        """Generate AI-enhanced recommendations"""
        recommendations = []
        
        # Rightsizing recommendation based on AI allocation prediction
        if optimal_allocation.get('ai_predicted'):
            current_cpu = metrics.current_capacity.get('cpu_cores', 1)
            current_memory = metrics.current_capacity.get('memory_gb', 1)
            predicted_cpu = optimal_allocation.get('cpu_cores', current_cpu)
            predicted_memory = optimal_allocation.get('memory_gb', current_memory)
            
            if abs(predicted_cpu - current_cpu) > 0 or abs(predicted_memory - current_memory) > 0:
                recommendation = ResourceRecommendation(
                    recommendation_id=f"ai-rightsizing-{metrics.provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    resource_id=metrics.resource_id,
                    resource_name=metrics.resource_name,
                    resource_type=metrics.resource_type,
                    provider=metrics.provider,
                    current_state=self._determine_utilization_level(metrics),
                    recommended_action=OptimizationAction.RIGHTSIZE,
                    priority="medium",
                    confidence=optimal_allocation.get('confidence', 0.5),
                    expected_savings=self._calculate_rightsizing_savings(metrics, predicted_cpu, predicted_memory),
                    performance_impact="low",
                    implementation_complexity="medium",
                    description=f"AI recommends rightsizing from {current_cpu} CPU cores, {current_memory}GB RAM to {predicted_cpu} CPU cores, {predicted_memory}GB RAM",
                    current_config=metrics.current_capacity,
                    recommended_config={
                        'cpu_cores': predicted_cpu,
                        'memory_gb': predicted_memory,
                        'ai_predicted': True
                    },
                    implementation_steps=[
                        "Analyze current resource utilization with AI models",
                        "Validate AI recommendations against business requirements",
                        "Schedule maintenance window for resource changes",
                        "Apply new resource allocation",
                        "Monitor performance and adjust if needed"
                    ],
                    rollback_steps=[
                        "Revert to previous resource allocation",
                        "Monitor for performance issues",
                        "Validate system stability after rollback"
                    ],
                    risk_assessment={
                        'performance_risk': 'low',
                        'cost_risk': 'medium',
                        'downtime_required': True
                    },
                    ai_enhanced=True,
                    predictive_insights=[
                        f"AI predicts optimal allocation with {optimal_allocation.get('confidence', 0.5)*100:.1f}% confidence"
                    ]
                )
                recommendations.append(recommendation)
        
        # Scaling recommendation based on AI prediction
        if scaling_prediction.get('ai_predicted'):
            action = scaling_prediction.get('action')
            if action != 'no_change':
                scaling_action = OptimizationAction.SCALE_UP if action == 'scale_up' else OptimizationAction.SCALE_DOWN
                
                recommendation = ResourceRecommendation(
                    recommendation_id=f"ai-scaling-{metrics.provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    resource_id=metrics.resource_id,
                    resource_name=metrics.resource_name,
                    resource_type=metrics.resource_type,
                    provider=metrics.provider,
                    current_state=self._determine_utilization_level(metrics),
                    recommended_action=scaling_action,
                    priority="high" if scaling_prediction.get('confidence', 0) > 0.8 else "medium",
                    confidence=scaling_prediction.get('confidence', 0.5),
                    expected_savings=self._calculate_scaling_savings(metrics, scaling_action),
                    performance_impact="medium",
                    implementation_complexity="low",
                    description=f"AI predicts need to {action.replace('_', ' ')} based on usage patterns and forecasts",
                    current_config=metrics.current_capacity,
                    recommended_config=metrics.current_capacity.copy(),  # Scaling keeps same config per instance
                    implementation_steps=[
                        "Review AI scaling recommendations",
                        "Configure auto-scaling policies",
                        "Set appropriate scaling thresholds",
                        "Enable scaling monitoring",
                        "Test scaling behavior"
                    ],
                    rollback_steps=[
                        "Disable auto-scaling policies",
                        "Manually adjust resource count if needed",
                        "Monitor system stability"
                    ],
                    risk_assessment={
                        'performance_risk': 'low',
                        'cost_risk': 'low',
                        'downtime_required': False
                    },
                    ai_enhanced=True,
                    predictive_insights=[
                        f"AI scaling prediction confidence: {scaling_prediction.get('confidence', 0.5)*100:.1f}%"
                    ]
                )
                recommendations.append(recommendation)
        
        # Anomaly-based recommendations
        if anomalies.get('anomalies_detected'):
            for anomaly in anomalies['anomalies_detected']:
                if anomaly['severity'] == 'high':
                    recommendation = ResourceRecommendation(
                        recommendation_id=f"ai-anomaly-{metrics.provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        resource_id=metrics.resource_id,
                        resource_name=metrics.resource_name,
                        resource_type=metrics.resource_type,
                        provider=metrics.provider,
                        current_state=UtilizationLevel.CRITICAL,
                        recommended_action=OptimizationAction.SCALE_UP,
                        priority="critical",
                        confidence=0.9,
                        expected_savings=0,  # Anomalies may require immediate action
                        performance_impact="high",
                        implementation_complexity="low",
                        description=f"AI detected critical anomaly in {anomaly['metric']}: current {anomaly['current_value']:.1f}%, expected {anomaly['expected_range'][0]:.1f}-{anomaly['expected_range'][1]:.1f}%",
                        current_config=metrics.current_capacity,
                        recommended_config=metrics.current_capacity.copy(),
                        implementation_steps=[
                            "Investigate root cause of anomaly",
                            "Implement immediate scaling if needed",
                            "Review monitoring alerts",
                            "Update anomaly detection thresholds if necessary"
                        ],
                        rollback_steps=[
                            "Scale back resources if anomaly was false positive",
                            "Review anomaly detection accuracy"
                        ],
                        risk_assessment={
                            'performance_risk': 'high',
                            'cost_risk': 'medium',
                            'downtime_required': False
                        },
                        ai_enhanced=True,
                        predictive_insights=[
                            f"Anomaly detected: {anomaly['metric']} outside normal range"
                        ]
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _determine_utilization_level(self, metrics: ResourceMetrics) -> UtilizationLevel:
        """Determine utilization level based on metrics"""
        avg_utilization = (metrics.cpu_utilization + metrics.memory_utilization) / 2
        
        if avg_utilization >= 90:
            return UtilizationLevel.CRITICAL
        elif avg_utilization >= 80:
            return UtilizationLevel.OVERUTILIZED
        elif avg_utilization <= 25:
            return UtilizationLevel.UNDERUTILIZED
        else:
            return UtilizationLevel.OPTIMAL
    
    def _calculate_rightsizing_savings(self, metrics: ResourceMetrics, new_cpu: int, new_memory: int) -> float:
        """Calculate potential savings from rightsizing"""
        current_cpu = metrics.current_capacity.get('cpu_cores', 1)
        current_memory = metrics.current_capacity.get('memory_gb', 1)
        
        # Simplified cost calculation - in reality would use actual pricing
        cpu_cost_per_core = 10.0  # $/month per CPU core
        memory_cost_per_gb = 2.0  # $/month per GB RAM
        
        current_cost = (current_cpu * cpu_cost_per_core) + (current_memory * memory_cost_per_gb)
        new_cost = (new_cpu * cpu_cost_per_core) + (new_memory * memory_cost_per_gb)
        
        return max(0, current_cost - new_cost)
    
    def _calculate_scaling_savings(self, metrics: ResourceMetrics, action: OptimizationAction) -> float:
        """Calculate potential savings from scaling actions"""
        # Simplified calculation
        if action == OptimizationAction.SCALE_DOWN:
            return metrics.cost_per_hour * 24 * 30 * 0.2  # 20% savings from scaling down
        elif action == OptimizationAction.SCALE_UP:
            return -(metrics.cost_per_hour * 24 * 30 * 0.3)  # Cost increase for scaling up
        return 0
    
    def _collect_resource_data(self, provider: str, include_historical: bool) -> List[Dict[str, Any]]:
        """Collect resource data from provider APIs"""
        # This would integrate with actual cloud provider APIs
        # For now, return mock data structure
        return [
            {
                'resource_id': f'{provider}-instance-001',
                'resource_name': f'{provider.capitalize()} Instance 001',
                'resource_type': 'compute',
                'region': self.config['providers'][provider]['region'],
                'environment': 'production',
                'cpu_utilization': 65.0,
                'memory_utilization': 75.0,
                'disk_utilization': 45.0,
                'network_utilization': 30.0,
                'current_capacity': {'cpu_cores': 2, 'memory_gb': 4},
                'recommended_capacity': {'cpu_cores': 2, 'memory_gb': 6},
                'utilization_score': 0.7,
                'efficiency_score': 0.8,
                'cost_per_hour': 0.15,
                'metadata': {'concurrent_users': 50, 'request_rate': 200},
                'historical_data': [
                    {'cpu_utilization': 60, 'memory_utilization': 70, 'timestamp': datetime.now() - timedelta(hours=i)}
                    for i in range(24)
                ] if include_historical else []
            },
            # Add more mock data...
        ]
    
    def _ai_filter_recommendations(self, recommendations: List[ResourceRecommendation]) -> List[ResourceRecommendation]:
        """AI-based filtering and prioritization of recommendations"""
        # Filter by confidence threshold
        filtered = [
            r for r in recommendations 
            if r.confidence >= self.config['analysis_settings']['confidence_threshold']
        ]
        
        # Sort by AI-enhanced confidence and expected savings
        filtered.sort(key=lambda x: (x.confidence, -x.expected_savings), reverse=True)
        
        return filtered[:50]  # Limit to top 50 recommendations
    
    # Fallback methods for when AI is not available
    def _analyze_provider_resources_basic(self, provider: str) -> List[ResourceRecommendation]:
        """Basic resource analysis without AI"""
        recommendations = []
        resource_data = self._collect_resource_data(provider, False)
        
        for resource in resource_data:
            basic_recommendations = self._analyze_resource_basic(resource, provider)
            recommendations.extend(basic_recommendations)
        
        return recommendations
    
    def _analyze_resource_basic(self, resource: Dict[str, Any], provider: str) -> List[ResourceRecommendation]:
        """Basic resource analysis without AI"""
        recommendations = []
        
        # Simple threshold-based analysis
        cpu_util = resource.get('cpu_utilization', 0)
        memory_util = resource.get('memory_utilization', 0)
        
        thresholds = self.config['optimization_thresholds']
        
        if cpu_util > thresholds['cpu_overutilized'] or memory_util > thresholds['memory_overutilized']:
            # Scale up recommendation
            recommendation = ResourceRecommendation(
                recommendation_id=f"basic-scale-up-{provider}-{resource['resource_id']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=resource['resource_id'],
                resource_name=resource['resource_name'],
                resource_type=ResourceType(resource.get('resource_type', 'compute')),
                provider=provider,
                current_state=UtilizationLevel.OVERUTILIZED,
                recommended_action=OptimizationAction.SCALE_UP,
                priority="high",
                confidence=0.7,
                expected_savings=0,  # Scaling up costs more
                performance_impact="low",
                implementation_complexity="low",
                description=f"High utilization detected: CPU {cpu_util:.1f}%, Memory {memory_util:.1f}%",
                current_config=resource.get('current_capacity', {}),
                recommended_config=resource.get('current_capacity', {}),
                implementation_steps=[
                    "Scale up resources to handle load",
                    "Monitor performance after scaling",
                    "Adjust scaling policies as needed"
                ],
                rollback_steps=[
                    "Scale back if performance improves",
                    "Monitor for cost increases"
                ],
                risk_assessment={
                    'performance_risk': 'low',
                    'cost_risk': 'medium',
                    'downtime_required': False
                },
                ai_enhanced=False
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def generate_resource_report(self, recommendations: List[ResourceRecommendation], 
                               analysis_results: Dict[str, Any], output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive resource optimization report"""
        logger.info("Generating AI-enhanced resource optimization report")
        
        total_recommendations = len(recommendations)
        total_potential_savings = sum(rec.expected_savings for rec in recommendations)
        ai_recommendations = [r for r in recommendations if r.ai_enhanced]
        
        # Collect AI insights
        all_insights = []
        for provider_results in analysis_results.values():
            all_insights.extend(provider_results.get('ai_insights', []))
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_recommendations': total_recommendations,
                'ai_enhanced_recommendations': len(ai_recommendations),
                'total_potential_savings': total_potential_savings,
                'providers_analyzed': len(analysis_results),
                'ai_insights_count': len(all_insights)
            },
            'provider_breakdown': analysis_results,
            'top_recommendations': [
                {
                    'resource_name': rec.resource_name,
                    'provider': rec.provider,
                    'action': rec.recommended_action.value,
                    'priority': rec.priority,
                    'confidence': rec.confidence,
                    'expected_savings': rec.expected_savings,
                    'ai_enhanced': rec.ai_enhanced,
                    'description': rec.description
                }
                for rec in recommendations[:20]
            ],
            'ai_insights': all_insights[:10],
            'recommendations_by_type': self._count_recommendations_by_type(recommendations)
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Resource optimization report saved to: {output_file}")
        
        return report
    
    def _count_recommendations_by_type(self, recommendations: List[ResourceRecommendation]) -> Dict[str, int]:
        """Count recommendations by optimization type"""
        counts = {}
        for rec in recommendations:
            opt_type = rec.recommended_action.value
            counts[opt_type] = counts.get(opt_type, 0) + 1
        return counts
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load resource optimizer configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'optimization_thresholds': {
                'cpu_underutilized': 20.0,
                'cpu_overutilized': 80.0,
                'memory_underutilized': 30.0,
                'memory_overutilized': 85.0,
                'disk_underutilized': 25.0,
                'disk_overutilized': 90.0,
                'network_underutilized': 10.0,
                'network_overutilized': 80.0
            },
            'analysis_settings': {
                'analysis_period_days': 30,
                'min_utilization_samples': 10,
                'confidence_threshold': 0.7,
                'risk_tolerance': 'medium',
                'automation_enabled': True
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
    
    def collect_resource_metrics(self, providers: List[str], time_range_days: int = 30) -> Dict[str, List[ResourceMetrics]]:
        """Collect resource metrics from multiple providers"""
        logger.info(f"Collecting resource metrics from providers: {providers}")
        
        all_metrics = {}
        
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
                
                # Collect metrics
                provider_metrics = handler.get_resource_metrics(time_range_days)
                all_metrics[provider] = provider_metrics
                
                logger.info(f"Collected {len(provider_metrics)} resource metrics from {provider}")
                
            except Exception as e:
                logger.error(f"Failed to collect metrics from {provider}: {e}")
                all_metrics[provider] = []
        
        return all_metrics
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific resource handler"""
        from resource_optimizer_handler import get_resource_handler
        region = self.config['providers'][provider]['region']
        return get_resource_handler(provider, region)
    
    def analyze_resources(self, metrics: Dict[str, List[ResourceMetrics]]) -> Dict[str, List[ResourceRecommendation]]:
        """Analyze resource metrics and generate recommendations"""
        logger.info("Analyzing resource metrics")
        
        recommendations_by_provider = {}
        
        for provider, provider_metrics in metrics.items():
            try:
                # Analyze metrics for this provider
                provider_recommendations = self._analyze_provider_resources(provider_metrics, provider)
                recommendations_by_provider[provider] = provider_recommendations
                
                logger.info(f"Generated {len(provider_recommendations)} recommendations for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to analyze resources for {provider}: {e}")
                recommendations_by_provider[provider] = []
        
        return recommendations_by_provider
    
    def _analyze_provider_resources(self, metrics: List[ResourceMetrics], provider: str) -> List[ResourceRecommendation]:
        """Analyze resources for a specific provider"""
        recommendations = []
        
        try:
            # Group metrics by resource type
            metrics_by_type = {}
            for metric in metrics:
                resource_type = metric.resource_type
                if resource_type not in metrics_by_type:
                    metrics_by_type[resource_type] = []
                metrics_by_type[resource_type].append(metric)
            
            # Analyze each resource type
            for resource_type, type_metrics in metrics_by_type.items():
                type_recommendations = self._analyze_resource_type(type_metrics, provider)
                recommendations.extend(type_recommendations)
            
            # Sort recommendations by priority and expected savings
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(key=lambda x: (priority_order.get(x.priority, 4), -x.expected_savings))
            
        except Exception as e:
            logger.error(f"Failed to analyze provider resources: {e}")
        
        return recommendations
    
    def _analyze_resource_type(self, metrics: List[ResourceMetrics], provider: str) -> List[ResourceRecommendation]:
        """Analyze resources of a specific type"""
        recommendations = []
        
        try:
            for resource_metrics in metrics:
                resource_recommendations = self._analyze_single_resource(resource_metrics, provider)
                recommendations.extend(resource_recommendations)
            
        except Exception as e:
            logger.error(f"Failed to analyze resource type: {e}")
        
        return recommendations
    
    def _analyze_single_resource(self, metrics: ResourceMetrics, provider: str) -> List[ResourceRecommendation]:
        """Analyze a single resource"""
        recommendations = []
        
        try:
            # Determine utilization levels
            cpu_level = self._determine_utilization_level(metrics.cpu_utilization, 'cpu')
            memory_level = self._determine_utilization_level(metrics.memory_utilization, 'memory')
            disk_level = self._determine_utilization_level(metrics.disk_utilization, 'disk')
            network_level = self._determine_utilization_level(metrics.network_utilization, 'network')
            
            # Calculate overall utilization score
            utilization_score = self._calculate_utilization_score(metrics)
            
            # Determine current state
            current_state = self._determine_current_state(cpu_level, memory_level, disk_level, network_level)
            
            # Generate recommendations based on current state
            if current_state == UtilizationLevel.UNDERUTILIZED:
                recommendations.extend(self._generate_underutilized_recommendations(metrics, provider))
            elif current_state == UtilizationLevel.OVERUTILIZED:
                recommendations.extend(self._generate_overutilized_recommendations(metrics, provider))
            elif current_state == UtilizationLevel.CRITICAL:
                recommendations.extend(self._generate_critical_recommendations(metrics, provider))
            elif current_state == UtilizationLevel.OPTIMAL:
                # Still check for optimization opportunities
                recommendations.extend(self._generate_optimal_recommendations(metrics, provider))
            
        except Exception as e:
            logger.error(f"Failed to analyze single resource: {e}")
        
        return recommendations
    
    def _determine_utilization_level(self, utilization: float, metric_type: str) -> UtilizationLevel:
        """Determine utilization level for a metric"""
        thresholds = self.config['optimization_thresholds']
        
        underutilized_key = f'{metric_type}_underutilized'
        overutilized_key = f'{metric_type}_overutilized'
        
        if utilization < thresholds[underutilized_key]:
            return UtilizationLevel.UNDERUTILIZED
        elif utilization > thresholds[overutilized_key]:
            return UtilizationLevel.OVERUTILIZED
        else:
            return UtilizationLevel.OPTIMAL
    
    def _calculate_utilization_score(self, metrics: ResourceMetrics) -> float:
        """Calculate overall utilization score"""
        # Weight different metrics
        weights = {
            'cpu': 0.3,
            'memory': 0.3,
            'disk': 0.2,
            'network': 0.2
        }
        
        cpu_score = min(metrics.cpu_utilization / 100, 1.0)
        memory_score = min(metrics.memory_utilization / 100, 1.0)
        disk_score = min(metrics.disk_utilization / 100, 1.0)
        network_score = min(metrics.network_utilization / 100, 1.0)
        
        overall_score = (
            cpu_score * weights['cpu'] +
            memory_score * weights['memory'] +
            disk_score * weights['disk'] +
            network_score * weights['network']
        )
        
        return overall_score
    
    def _determine_current_state(self, cpu_level: UtilizationLevel, memory_level: UtilizationLevel,
                               disk_level: UtilizationLevel, network_level: UtilizationLevel) -> UtilizationLevel:
        """Determine current utilization state"""
        levels = [cpu_level, memory_level, disk_level, network_level]
        
        # If any metric is critical, overall state is critical
        if UtilizationLevel.CRITICAL in levels:
            return UtilizationLevel.CRITICAL
        
        # If any metric is overutilized, overall state is overutilized
        if UtilizationLevel.OVERUTILIZED in levels:
            return UtilizationLevel.OVERUTILIZED
        
        # If most metrics are underutilized, overall state is underutilized
        underutilized_count = sum(1 for level in levels if level == UtilizationLevel.UNDERUTILIZED)
        if underutilized_count >= 2:
            return UtilizationLevel.UNDERUTILIZED
        
        # Otherwise, state is optimal
        return UtilizationLevel.OPTIMAL
    
    def _generate_underutilized_recommendations(self, metrics: ResourceMetrics, provider: str) -> List[ResourceRecommendation]:
        """Generate recommendations for underutilized resources"""
        recommendations = []
        
        try:
            # Rightsizing recommendation
            rightsizing_rec = self._create_rightsizing_recommendation(metrics, provider)
            if rightsizing_rec:
                recommendations.append(rightsizing_rec)
            
            # Consolidation recommendation
            consolidation_rec = self._create_consolidation_recommendation(metrics, provider)
            if consolidation_rec:
                recommendations.append(consolidation_rec)
            
            # Decommission recommendation (for severely underutilized)
            if metrics.utilization_score < 0.2:
                decommission_rec = self._create_decommission_recommendation(metrics, provider)
                if decommission_rec:
                    recommendations.append(decommission_rec)
            
        except Exception as e:
            logger.error(f"Failed to generate underutilized recommendations: {e}")
        
        return recommendations
    
    def _generate_overutilized_recommendations(self, metrics: ResourceMetrics, provider: str) -> List[ResourceRecommendation]:
        """Generate recommendations for overutilized resources"""
        recommendations = []
        
        try:
            # Scale up recommendation
            scale_up_rec = self._create_scale_up_recommendation(metrics, provider)
            if scale_up_rec:
                recommendations.append(scale_up_rec)
            
            # Load balancing recommendation
            load_balance_rec = self._create_load_balance_recommendation(metrics, provider)
            if load_balance_rec:
                recommendations.append(load_balance_rec)
            
        except Exception as e:
            logger.error(f"Failed to generate overutilized recommendations: {e}")
        
        return recommendations
    
    def _generate_critical_recommendations(self, metrics: ResourceMetrics, provider: str) -> List[ResourceRecommendation]:
        """Generate recommendations for critical resources"""
        recommendations = []
        
        try:
            # Immediate scale up
            immediate_scale_rec = self._create_immediate_scale_recommendation(metrics, provider)
            if immediate_scale_rec:
                recommendations.append(immediate_scale_rec)
            
            # Migration to larger instance
            migration_rec = self._create_migration_recommendation(metrics, provider)
            if migration_rec:
                recommendations.append(migration_rec)
            
        except Exception as e:
            logger.error(f"Failed to generate critical recommendations: {e}")
        
        return recommendations
    
    def _generate_optimal_recommendations(self, metrics: ResourceMetrics, provider: str) -> List[ResourceRecommendation]:
        """Generate recommendations for optimal resources"""
        recommendations = []
        
        try:
            # Check for cost optimization opportunities even in optimal state
            if metrics.efficiency_score < 0.8:
                optimization_rec = self._create_efficiency_recommendation(metrics, provider)
                if optimization_rec:
                    recommendations.append(optimization_rec)
            
        except Exception as e:
            logger.error(f"Failed to generate optimal recommendations: {e}")
        
        return recommendations
    
    def _create_rightsizing_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create rightsizing recommendation"""
        try:
            # Calculate recommended capacity based on current utilization
            target_utilization = 70.0  # Target 70% utilization
            
            cpu_target_size = (metrics.cpu_utilization / target_utilization) * 100
            memory_target_size = (metrics.memory_utilization / target_utilization) * 100
            
            # Use the higher of the two for conservative sizing
            recommended_size = max(cpu_target_size, memory_target_size)
            
            # Map to actual instance types (simplified)
            if provider == 'aws':
                current_type = metrics.current_capacity.get('instance_type', 't3.medium')
                recommended_type = self._map_aws_instance_type(recommended_size)
            elif provider == 'azure':
                current_type = metrics.current_capacity.get('vm_size', 'Standard_B2s')
                recommended_type = self._map_azure_vm_size(recommended_size)
            elif provider == 'gcp':
                current_type = metrics.current_capacity.get('machine_type', 'e2-medium')
                recommended_type = self._map_gcp_machine_type(recommended_size)
            else:
                return None
            
            if recommended_type == current_type:
                return None  # No change needed
            
            # Calculate expected savings
            current_cost = metrics.cost_per_hour * 24 * 30  # Monthly cost
            recommended_cost = self._calculate_instance_cost(recommended_type, provider) * 24 * 30
            expected_savings = max(0, current_cost - recommended_cost)
            
            recommendation = ResourceRecommendation(
                recommendation_id=f"rightsize-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.UNDERUTILIZED,
                recommended_action=OptimizationAction.RIGHTSIZE,
                priority='high' if expected_savings > 50 else 'medium',
                confidence=0.8,
                expected_savings=expected_savings,
                performance_impact='minimal',
                implementation_complexity='low',
                description=f"Resource is underutilized ({metrics.utilization_score:.1%} overall). Rightsizing to {recommended_type} can save ${expected_savings:.2f}/month.",
                current_config={'instance_type': current_type, 'utilization': metrics.utilization_score},
                recommended_config={'instance_type': recommended_type, 'target_utilization': target_utilization},
                implementation_steps=[
                    f"Schedule maintenance window for {metrics.resource_name}",
                    f"Resize {metrics.resource_type} from {current_type} to {recommended_type}",
                    "Monitor performance after resize",
                    "Update documentation and monitoring"
                ],
                rollback_steps=[
                    f"Resize back to {current_type} if performance issues occur",
                    "Monitor for 24 hours after rollback",
                    "Investigate root cause of performance issues"
                ],
                risk_assessment={
                    'risk_level': 'low',
                    'potential_downtime': '5-10 minutes',
                    'data_loss_risk': 'none',
                    'performance_impact': 'minimal'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create rightsizing recommendation: {e}")
            return None
    
    def _create_consolidation_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create consolidation recommendation"""
        try:
            # Check if consolidation is feasible
            if metrics.resource_type != ResourceType.COMPUTE:
                return None
            
            # Find potential consolidation targets (simplified)
            consolidation_ratio = self._calculate_consolidation_ratio(metrics)
            
            if consolidation_ratio <= 1:
                return None  # No consolidation benefit
            
            current_cost = metrics.cost_per_hour * 24 * 30
            consolidated_cost = current_cost / consolidation_ratio
            expected_savings = current_cost - consolidated_cost
            
            recommendation = ResourceRecommendation(
                recommendation_id=f"consolidate-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.UNDERUTILIZED,
                recommended_action=OptimizationAction.CONSOLIDATE,
                priority='medium',
                confidence=0.7,
                expected_savings=expected_savings,
                performance_impact='minimal',
                implementation_complexity='medium',
                description=f"Resource can be consolidated with {consolidation_ratio-1:.0f} other resources, saving ${expected_savings:.2f}/month.",
                current_config={'standalone': True, 'utilization': metrics.utilization_score},
                recommended_config={'consolidated': True, 'consolidation_ratio': consolidation_ratio},
                implementation_steps=[
                    "Identify consolidation candidates",
                    "Plan migration strategy",
                    "Execute consolidation during maintenance window",
                    "Monitor performance after consolidation"
                ],
                rollback_steps=[
                    "Deconsolidate if performance issues occur",
                    "Restore original configuration",
                    "Monitor for 24 hours after rollback"
                ],
                risk_assessment={
                    'risk_level': 'medium',
                    'potential_downtime': '30-60 minutes',
                    'data_loss_risk': 'none',
                    'performance_impact': 'minimal'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create consolidation recommendation: {e}")
            return None
    
    def _create_decommission_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create decommission recommendation"""
        try:
            # Only recommend decommissioning if utilization is very low
            if metrics.utilization_score > 0.15:
                return None
            
            current_cost = metrics.cost_per_hour * 24 * 30
            expected_savings = current_cost * 0.9  # Assume 90% savings after decommission
            
            recommendation = ResourceRecommendation(
                recommendation_id=f"decommission-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.UNDERUTILIZED,
                recommended_action=OptimizationAction.DECOMMISSION,
                priority='high',
                confidence=0.9,
                expected_savings=expected_savings,
                performance_impact='none',
                implementation_complexity='medium',
                description=f"Resource is severely underutilized ({metrics.utilization_score:.1%}). Decommissioning can save ${expected_savings:.2f}/month.",
                current_config={'active': True, 'utilization': metrics.utilization_score},
                recommended_config={'decommissioned': True},
                implementation_steps=[
                    "Verify resource is not in use",
                    "Backup any important data",
                    "Update documentation and configurations",
                    "Decommission resource",
                    "Monitor for any service impact"
                ],
                rollback_steps=[
                    "Recreate resource if needed",
                    "Restore from backup",
                    "Update configurations"
                ],
                risk_assessment={
                    'risk_level': 'high',
                    'potential_downtime': 'none',
                    'data_loss_risk': 'medium',
                    'performance_impact': 'none'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create decommission recommendation: {e}")
            return None
    
    def _create_scale_up_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create scale up recommendation"""
        try:
            # Calculate required scale up based on utilization
            scale_factor = max(
                metrics.cpu_utilization / 80.0,
                metrics.memory_utilization / 85.0,
                metrics.disk_utilization / 90.0
            )
            
            if scale_factor <= 1.0:
                return None
            
            # Map to larger instance types
            if provider == 'aws':
                current_type = metrics.current_capacity.get('instance_type', 't3.medium')
                recommended_type = self._map_aws_instance_type(scale_factor * 100)
            elif provider == 'azure':
                current_type = metrics.current_capacity.get('vm_size', 'Standard_B2s')
                recommended_type = self._map_azure_vm_size(scale_factor * 100)
            elif provider == 'gcp':
                current_type = metrics.current_capacity.get('machine_type', 'e2-medium')
                recommended_type = self._map_gcp_machine_type(scale_factor * 100)
            else:
                return None
            
            current_cost = metrics.cost_per_hour * 24 * 30
            recommended_cost = self._calculate_instance_cost(recommended_type, provider) * 24 * 30
            additional_cost = recommended_cost - current_cost
            
            recommendation = ResourceRecommendation(
                recommendation_id=f"scaleup-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.OVERUTILIZED,
                recommended_action=OptimizationAction.SCALE_UP,
                priority='critical',
                confidence=0.9,
                expected_savings=-additional_cost,  # Negative because it's a cost increase
                performance_impact='significant',
                implementation_complexity='low',
                description=f"Resource is overutilized ({metrics.utilization_score:.1%} overall). Scaling up to {recommended_type} will cost an additional ${additional_cost:.2f}/month.",
                current_config={'instance_type': current_type, 'utilization': metrics.utilization_score},
                recommended_config={'instance_type': recommended_type, 'target_utilization': 70.0},
                implementation_steps=[
                    f"Scale up {metrics.resource_type} from {current_type} to {recommended_type}",
                    "Monitor performance after scaling",
                    "Update cost allocation and documentation"
                ],
                rollback_steps=[
                    f"Scale down to {current_type} if overprovisioned",
                    "Monitor for performance degradation",
                    "Investigate root cause of high utilization"
                ],
                risk_assessment={
                    'risk_level': 'low',
                    'potential_downtime': '5-10 minutes',
                    'data_loss_risk': 'none',
                    'performance_impact': 'positive'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create scale up recommendation: {e}")
            return None
    
    def _create_load_balance_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create load balancing recommendation"""
        try:
            # Simplified load balancing recommendation
            recommendation = ResourceRecommendation(
                recommendation_id=f"loadbalance-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.OVERUTILIZED,
                recommended_action=OptimizationAction.MIGRATE,
                priority='high',
                confidence=0.7,
                expected_savings=0.0,  # Cost neutral
                performance_impact='significant',
                implementation_complexity='medium',
                description=f"Resource is overutilized. Implement load balancing to distribute load and improve performance.",
                current_config={'single_instance': True, 'utilization': metrics.utilization_score},
                recommended_config={'load_balanced': True, 'instance_count': 2},
                implementation_steps=[
                    "Set up load balancer",
                    "Deploy additional instances",
                    "Configure health checks",
                    "Update DNS and routing"
                ],
                rollback_steps=[
                    "Remove load balancer",
                    "Consolidate back to single instance",
                    "Update routing"
                ],
                risk_assessment={
                    'risk_level': 'medium',
                    'potential_downtime': '10-20 minutes',
                    'data_loss_risk': 'none',
                    'performance_impact': 'positive'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create load balance recommendation: {e}")
            return None
    
    def _create_immediate_scale_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create immediate scale recommendation for critical resources"""
        try:
            recommendation = ResourceRecommendation(
                recommendation_id=f"immediate-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.CRITICAL,
                recommended_action=OptimizationAction.SCALE_UP,
                priority='critical',
                confidence=0.95,
                expected_savings=0.0,
                performance_impact='critical',
                implementation_complexity='low',
                description=f"Resource is in critical state ({metrics.utilization_score:.1%} utilization). Immediate scaling required.",
                current_config={'current_state': 'critical', 'utilization': metrics.utilization_score},
                recommended_config={'scaled_up': True, 'target_utilization': 50.0},
                implementation_steps=[
                    "IMMEDIATE ACTION REQUIRED",
                    "Scale up resource immediately",
                    "Monitor for service recovery",
                    "Investigate root cause of critical utilization"
                ],
                rollback_steps=[
                    "Scale down if overprovisioned after recovery",
                    "Monitor for stability",
                    "Document incident and resolution"
                ],
                risk_assessment={
                    'risk_level': 'high',
                    'potential_downtime': 'imminent without action',
                    'data_loss_risk': 'possible',
                    'performance_impact': 'critical'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create immediate scale recommendation: {e}")
            return None
    
    def _create_migration_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create migration recommendation"""
        try:
            recommendation = ResourceRecommendation(
                recommendation_id=f"migrate-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.CRITICAL,
                recommended_action=OptimizationAction.MIGRATE,
                priority='critical',
                confidence=0.8,
                expected_savings=0.0,
                performance_impact='significant',
                implementation_complexity='high',
                description=f"Resource requires migration to higher performance tier due to critical utilization.",
                current_config={'current_tier': 'insufficient', 'utilization': metrics.utilization_score},
                recommended_config={'migrated': True, 'target_tier': 'high_performance'},
                implementation_steps=[
                    "Plan migration strategy",
                    "Set up target infrastructure",
                    "Execute migration with minimal downtime",
                    "Validate performance after migration"
                ],
                rollback_steps=[
                    "Rollback to original configuration",
                    "Investigate migration issues",
                    "Document lessons learned"
                ],
                risk_assessment={
                    'risk_level': 'high',
                    'potential_downtime': '30-60 minutes',
                    'data_loss_risk': 'low',
                    'performance_impact': 'positive'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create migration recommendation: {e}")
            return None
    
    def _create_efficiency_recommendation(self, metrics: ResourceMetrics, provider: str) -> Optional[ResourceRecommendation]:
        """Create efficiency improvement recommendation"""
        try:
            recommendation = ResourceRecommendation(
                recommendation_id=f"efficiency-{provider}-{metrics.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                resource_id=metrics.resource_id,
                resource_name=metrics.resource_name,
                resource_type=metrics.resource_type,
                provider=provider,
                current_state=UtilizationLevel.OPTIMAL,
                recommended_action=OptimizationAction.RIGHTSIZE,
                priority='low',
                confidence=0.6,
                expected_savings=10.0,  # Small optimization
                performance_impact='minimal',
                implementation_complexity='low',
                description=f"Resource efficiency can be improved from {metrics.efficiency_score:.1%} to ~85%.",
                current_config={'efficiency': metrics.efficiency_score},
                recommended_config={'efficiency': 0.85},
                implementation_steps=[
                    "Analyze resource usage patterns",
                    "Optimize configuration settings",
                    "Monitor efficiency improvements"
                ],
                rollback_steps=[
                    "Revert configuration changes",
                    "Monitor for performance impact"
                ],
                risk_assessment={
                    'risk_level': 'low',
                    'potential_downtime': 'none',
                    'data_loss_risk': 'none',
                    'performance_impact': 'minimal'
                }
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create efficiency recommendation: {e}")
            return None
    
    def _map_aws_instance_type(self, target_size: float) -> str:
        """Map target size to AWS instance type"""
        if target_size <= 20:
            return 't3.nano'
        elif target_size <= 40:
            return 't3.micro'
        elif target_size <= 60:
            return 't3.small'
        elif target_size <= 80:
            return 't3.medium'
        elif target_size <= 120:
            return 't3.large'
        elif target_size <= 160:
            return 't3.xlarge'
        elif target_size <= 200:
            return 't3.2xlarge'
        else:
            return 'm5.large'
    
    def _map_azure_vm_size(self, target_size: float) -> str:
        """Map target size to Azure VM size"""
        if target_size <= 20:
            return 'Standard_B1s'
        elif target_size <= 40:
            return 'Standard_B2s'
        elif target_size <= 60:
            return 'Standard_B2ms'
        elif target_size <= 80:
            return 'Standard_D2s_v3'
        elif target_size <= 120:
            return 'Standard_D4s_v3'
        elif target_size <= 160:
            return 'Standard_D8s_v3'
        else:
            return 'Standard_D16s_v3'
    
    def _map_gcp_machine_type(self, target_size: float) -> str:
        """Map target size to GCP machine type"""
        if target_size <= 20:
            return 'e2-micro'
        elif target_size <= 40:
            return 'e2-small'
        elif target_size <= 60:
            return 'e2-medium'
        elif target_size <= 80:
            return 'e2-standard-2'
        elif target_size <= 120:
            return 'e2-standard-4'
        elif target_size <= 160:
            return 'e2-standard-8'
        else:
            return 'e2-standard-16'
    
    def _calculate_instance_cost(self, instance_type: str, provider: str) -> float:
        """Calculate hourly cost for instance type"""
        # Simplified cost calculation
        if provider == 'aws':
            cost_mapping = {
                't3.nano': 0.0052,
                't3.micro': 0.0104,
                't3.small': 0.0208,
                't3.medium': 0.0416,
                't3.large': 0.0832,
                't3.xlarge': 0.1664,
                't3.2xlarge': 0.3328,
                'm5.large': 0.096
            }
        elif provider == 'azure':
            cost_mapping = {
                'Standard_B1s': 0.0104,
                'Standard_B2s': 0.0416,
                'Standard_B2ms': 0.0552,
                'Standard_D2s_v3': 0.0768,
                'Standard_D4s_v3': 0.1536,
                'Standard_D8s_v3': 0.3072,
                'Standard_D16s_v3': 0.6144
            }
        elif provider == 'gcp':
            cost_mapping = {
                'e2-micro': 0.0049,
                'e2-small': 0.0195,
                'e2-medium': 0.0291,
                'e2-standard-2': 0.0582,
                'e2-standard-4': 0.1164,
                'e2-standard-8': 0.2328,
                'e2-standard-16': 0.4656
            }
        else:
            return 0.05  # Default
        
        return cost_mapping.get(instance_type, 0.05)
    
    def _calculate_consolidation_ratio(self, metrics: ResourceMetrics) -> float:
        """Calculate consolidation ratio for resource"""
        # Simplified calculation based on utilization
        if metrics.utilization_score < 0.3:
            return 3.0  # Can consolidate 3:1
        elif metrics.utilization_score < 0.5:
            return 2.0  # Can consolidate 2:1
        else:
            return 1.0  # No consolidation benefit
    
    def implement_optimizations(self, recommendations: List[ResourceRecommendation], 
                                dry_run: bool = False) -> OptimizationResult:
        """Implement resource optimizations"""
        logger.info(f"Implementing {len(recommendations)} resource optimizations")
        
        # Group recommendations by provider
        recommendations_by_provider = {}
        for rec in recommendations:
            if rec.provider not in recommendations_by_provider:
                recommendations_by_provider[rec.provider] = []
            recommendations_by_provider[rec.provider].append(rec)
        
        # Implement optimizations for each provider
        implemented = []
        failed = []
        total_savings = 0.0
        
        performance_baseline = {}
        performance_after = {}
        
        for provider, provider_recommendations in recommendations_by_provider.items():
            try:
                handler = self._get_provider_handler(provider)
                if not handler.initialize_client():
                    raise RuntimeError(f"Failed to initialize {provider} handler")
                
                for rec in provider_recommendations:
                    try:
                        # Check if critical recommendation requires immediate action
                        if rec.priority == 'critical':
                            logger.info(f"CRITICAL: Implementing {rec.recommendation_id}")
                        
                        if dry_run:
                            logger.info(f"DRY RUN: Would implement optimization {rec.recommendation_id}")
                            implemented.append(rec.recommendation_id)
                            total_savings += rec.expected_savings
                        else:
                            # Implement optimization
                            success = self._implement_single_optimization(handler, rec)
                            if success:
                                implemented.append(rec.recommendation_id)
                                total_savings += rec.expected_savings
                            else:
                                failed.append(rec.recommendation_id)
                    
                    except Exception as e:
                        logger.error(f"Failed to implement optimization {rec.recommendation_id}: {e}")
                        failed.append(rec.recommendation_id)
                
            except Exception as e:
                logger.error(f"Failed to implement optimizations for {provider}: {e}")
                failed.extend([rec.recommendation_id for rec in provider_recommendations])
        
        # Create optimization result
        result = OptimizationResult(
            optimization_id=f"opt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            provider="multi",
            environment="production",
            optimized_at=datetime.utcnow(),
            total_resources_analyzed=sum(len(recs) for recs in recommendations_by_provider.values()),
            recommendations_generated=len(recommendations),
            recommendations_by_action=self._count_recommendations_by_action(recommendations),
            recommendations_by_priority=self._count_recommendations_by_priority(recommendations),
            total_potential_savings=total_savings,
            implemented_recommendations=implemented,
            failed_recommendations=failed,
            performance_baseline=performance_baseline,
            performance_after=performance_after
        )
        
        # Store optimization history
        self.optimizations.append({
            'optimization_id': result.optimization_id,
            'implemented_at': result.optimized_at,
            'total_recommendations': result.recommendations_generated,
            'implemented_count': len(implemented),
            'failed_count': len(failed),
            'total_savings': total_savings
        })
        
        return result
    
    def _implement_single_optimization(self, handler, recommendation: ResourceRecommendation) -> bool:
        """Implement a single optimization"""
        try:
            # Implementation based on optimization action
            if recommendation.recommended_action == OptimizationAction.RIGHTSIZE:
                return handler.implement_rightsizing(recommendation.resource_id, recommendation.recommended_config)
            elif recommendation.recommended_action == OptimizationAction.SCALE_UP:
                return handler.implement_scale_up(recommendation.resource_id, recommendation.recommended_config)
            elif recommendation.recommended_action == OptimizationAction.SCALE_DOWN:
                return handler.implement_scale_down(recommendation.resource_id, recommendation.recommended_config)
            elif recommendation.recommended_action == OptimizationAction.CONSOLIDATE:
                return handler.implement_consolidation(recommendation.resource_id, recommendation.recommended_config)
            elif recommendation.recommended_action == OptimizationAction.DECOMMISSION:
                return handler.implement_decommission(recommendation.resource_id, recommendation.recommended_config)
            elif recommendation.recommended_action == OptimizationAction.MIGRATE:
                return handler.implement_migration(recommendation.resource_id, recommendation.recommended_config)
            else:
                logger.warning(f"Unsupported optimization action: {recommendation.recommended_action}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to implement optimization {recommendation.recommendation_id}: {e}")
            return False
    
    def _count_recommendations_by_action(self, recommendations: List[ResourceRecommendation]) -> Dict[str, int]:
        """Count recommendations by action"""
        counts = {}
        for rec in recommendations:
            action = rec.recommended_action.value
            counts[action] = counts.get(action, 0) + 1
        return counts
    
    def _count_recommendations_by_priority(self, recommendations: List[ResourceRecommendation]) -> Dict[str, int]:
        """Count recommendations by priority"""
        counts = {}
        for rec in recommendations:
            priority = rec.priority
            counts[priority] = counts.get(priority, 0) + 1
        return counts
    
    def generate_optimization_report(self, analysis_results: Dict[str, List[ResourceRecommendation]], 
                                     optimization_result: Optional[OptimizationResult] = None,
                                     output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive resource optimization report"""
        logger.info("Generating resource optimization report")
        
        # Calculate statistics
        total_recommendations = sum(len(recs) for recs in analysis_results.values())
        total_savings = sum(rec.expected_savings for recs in [r for recs_list in analysis_results.values() for r in recs_list])
        
        # Provider comparisons
        provider_comparison = {}
        for provider, recommendations in analysis_results.items():
            provider_comparison[provider] = {
                'recommendations_count': len(recommendations),
                'potential_savings': sum(rec.expected_savings for rec in recommendations),
                'critical_count': len([r for r in recommendations if r.priority == 'critical']),
                'high_count': len([r for r in recommendations if r.priority == 'high'])
            }
        
        # Top recommendations
        all_recommendations = []
        for recommendations in analysis_results.values():
            all_recommendations.extend(recommendations)
        
        # Sort by expected savings and priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        top_recommendations = sorted(all_recommendations, 
                                   key=lambda x: (priority_order.get(x.priority, 4), -x.expected_savings))[:20]
        
        # Recommendations by action
        action_distribution = {}
        for recommendations in analysis_results.values():
            for rec in recommendations:
                action = rec.recommended_action.value
                action_distribution[action] = action_distribution.get(action, 0) + 1
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_providers_analyzed': len(analysis_results),
                'total_recommendations': total_recommendations,
                'total_potential_savings': total_savings,
                'critical_recommendations': len([r for r in all_recommendations if r.priority == 'critical']),
                'high_recommendations': len([r for r in all_recommendations if r.priority == 'high'])
            },
            'provider_comparison': provider_comparison,
            'action_distribution': action_distribution,
            'top_recommendations': [
                {
                    'recommendation_id': rec.recommendation_id,
                    'resource_name': rec.resource_name,
                    'resource_type': rec.resource_type.value,
                    'priority': rec.priority,
                    'action': rec.recommended_action.value,
                    'current_state': rec.current_state.value,
                    'expected_savings': rec.expected_savings,
                    'performance_impact': rec.performance_impact,
                    'confidence': rec.confidence,
                    'risk_level': rec.risk_assessment.get('risk_level', 'unknown')
                }
                for rec in top_recommendations
            ],
            'implementation_results': {
                'optimization_id': optimization_result.optimization_id,
                'implemented_at': optimization_result.optimized_at.isoformat(),
                'total_implemented': len(optimization_result.implemented_recommendations),
                'total_failed': len(optimization_result.failed_recommendations),
                'actual_savings': optimization_result.total_potential_savings
            } if optimization_result else None,
            'detailed_results': {
                provider: [
                    {
                        'recommendation_id': rec.recommendation_id,
                        'resource_name': rec.resource_name,
                        'resource_type': rec.resource_type.value,
                        'priority': rec.priority,
                        'action': rec.recommended_action.value,
                        'current_state': rec.current_state.value,
                        'expected_savings': rec.expected_savings,
                        'performance_impact': rec.performance_impact,
                        'confidence': rec.confidence,
                        'implementation_complexity': rec.implementation_complexity,
                        'risk_assessment': rec.risk_assessment,
                        'implementation_steps': rec.implementation_steps[:3]
                    }
                    for rec in recommendations[:10]
                ]
                for provider, recommendations in analysis_results.items()
            }
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Resource optimization report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Resource Optimizer")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--action", choices=['analyze', 'optimize', 'report'], 
                       default='analyze', help="Action to perform")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--time-range", type=int, default=30, help="Time range in days for metrics")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode for optimization")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize resource optimizer
    optimizer = ResourceOptimizer(args.config)
    
    try:
        if args.action == 'analyze':
            # Collect metrics
            metrics = optimizer.collect_resource_metrics(args.providers, args.time_range)
            
            # Analyze resources
            recommendations = optimizer.analyze_resources(metrics)
            
            print(f"\nResource Analysis Results:")
            for provider, provider_recommendations in recommendations.items():
                print(f"\n{provider.upper()}:")
                print(f"  Recommendations: {len(provider_recommendations)}")
                
                # Count by priority
                priority_counts = {}
                for rec in provider_recommendations:
                    priority = rec.priority
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                print(f"  By Priority: {priority_counts}")
                
                # Count by action
                action_counts = {}
                for rec in provider_recommendations:
                    action = rec.recommended_action.value
                    action_counts[action] = action_counts.get(action, 0) + 1
                
                print(f"  By Action: {action_counts}")
                
                # Show top 3 recommendations
                top_recs = sorted(provider_recommendations, 
                                 key=lambda x: (x.priority, -x.expected_savings))[:3]
                print(f"  Top Recommendations:")
                for i, rec in enumerate(top_recs, 1):
                    print(f"    {i}. {rec.resource_name} - {rec.recommended_action.value} (Savings: ${rec.expected_savings:.2f})")
        
        elif args.action == 'optimize':
            # First analyze to get recommendations
            metrics = optimizer.collect_resource_metrics(args.providers, args.time_range)
            recommendations = optimizer.analyze_resources(metrics)
            
            # Flatten all recommendations
            all_recommendations = []
            for provider_recommendations in recommendations.values():
                all_recommendations.extend(provider_recommendations)
            
            # Implement optimizations
            result = optimizer.implement_optimizations(all_recommendations, args.dry_run)
            
            print(f"\nOptimization Results:")
            print(f"Total Recommendations: {result.recommendations_generated}")
            print(f"Implemented: {len(result.implemented_recommendations)}")
            print(f"Failed: {len(result.failed_recommendations)}")
            print(f"Total Savings: ${result.total_potential_savings:.2f}")
            
            if args.dry_run:
                print("DRY RUN MODE - No actual optimizations performed")
        
        elif args.action == 'report':
            # Analyze first
            metrics = optimizer.collect_resource_metrics(args.providers, args.time_range)
            recommendations = optimizer.analyze_resources(metrics)
            
            # Generate report
            report = optimizer.generate_optimization_report(recommendations, output_file=args.output)
            
            summary = report['summary']
            print(f"\nResource Optimization Report:")
            print(f"Providers Analyzed: {summary['total_providers_analyzed']}")
            print(f"Total Recommendations: {summary['total_recommendations']}")
            print(f"Potential Savings: ${summary['total_potential_savings']:.2f}")
            print(f"Critical Recommendations: {summary['critical_recommendations']}")
            print(f"High Priority Recommendations: {summary['high_recommendations']}")
            
            print(f"\nProvider Comparison:")
            for provider, stats in report['provider_comparison'].items():
                print(f"  {provider}: {stats['recommendations_count']} recommendations, ${stats['potential_savings']:.2f} savings")
            
            if report['action_distribution']:
                print(f"\nRecommendation Actions:")
                for action, count in report['action_distribution'].items():
                    print(f"  {action}: {count}")
            
            print(f"\nTop Recommendations:")
            for rec in report['top_recommendations'][:5]:
                print(f"  - {rec['resource_name']} - {rec['action']} (Priority: {rec['priority']}, Savings: ${rec['expected_savings']:.2f})")
            
            if args.output:
                print(f"\nReport saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Resource optimization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
