#!/usr/bin/env python3
"""
Incident Predictor Script

Multi-cloud automation for predictive incident analysis across AWS, Azure, GCP, and on-premise environments.
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
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class PredictionModel(Enum):
    LINEAR_REGRESSION = "linear_regression"
    TIME_SERIES = "time_series"
    ANOMALY_DETECTION = "anomaly_detection"
    ML_CLASSIFIER = "ml_classifier"
    ENSEMBLE = "ensemble"

class IncidentSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IncidentCategory(Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    NETWORKING = "networking"
    DATABASE = "database"

@dataclass
class Incident:
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    category: IncidentCategory
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    created_at: datetime
    resolved_at: Optional[datetime]
    duration_minutes: int
    impact_score: float
    affected_services: List[str]
    root_cause: Optional[str]
    resolution: Optional[str]
    metrics: Dict[str, Any]

@dataclass
class PredictionInput:
    timestamp: datetime
    metrics: Dict[str, float]
    alerts: List[Dict[str, Any]]
    system_state: Dict[str, Any]
    environmental_factors: Dict[str, Any]

@dataclass
class PredictionResult:
    prediction_id: str
    timestamp: datetime
    predicted_incidents: List[Dict[str, Any]]
    confidence_score: float
    risk_level: str
    time_horizon_hours: int
    recommended_actions: List[str]
    model_used: PredictionModel
    features_importance: Dict[str, float]
    false_positive_risk: float

@dataclass
class PredictionModel:
    model_id: str
    model_name: str
    model_type: PredictionModel
    description: str
    features: List[str]
    accuracy: float
    precision: float
    recall: float
    training_data_points: int
    last_trained: datetime
    enabled: bool

class IncidentPredictor:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.models = {}
        self.historical_data = []
        self.predictions = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load incident predictor configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'prediction_settings': {
                'default_model': 'ensemble',
                'confidence_threshold': 0.7,
                'prediction_horizon_hours': 24,
                'min_training_data': 100,
                'model_retrain_interval_days': 30,
                'enable_feature_importance': True,
                'enable_false_positive_detection': True
            },
            'feature_weights': {
                'alert_volume': 0.25,
                'error_rate': 0.20,
                'response_time': 0.15,
                'resource_utilization': 0.15,
                'system_health': 0.10,
                'environmental_factors': 0.05,
                'historical_patterns': 0.10
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
    
    def load_prediction_models(self, models_file: Optional[str] = None) -> Dict[str, PredictionModel]:
        """Load prediction models"""
        logger.info("Loading prediction models")
        
        # Default models
        default_models = {
            'time-series-forecaster': PredictionModel(
                model_id='time-series-forecaster',
                model_name='Time Series Incident Forecaster',
                model_type=PredictionModel.TIME_SERIES,
                description='Predicts incidents based on historical time series patterns',
                features=['alert_volume', 'error_rate', 'response_time', 'system_health'],
                accuracy=0.85,
                precision=0.82,
                recall=0.88,
                training_data_points=1000,
                last_trained=datetime.utcnow() - timedelta(days=15),
                enabled=True
            ),
            'anomaly-detector': PredictionModel(
                model_id='anomaly-detector',
                model_name='Anomaly Detection Model',
                model_type=PredictionModel.ANOMALY_DETECTION,
                description='Detects anomalies in system metrics to predict incidents',
                features=['cpu_usage', 'memory_usage', 'network_latency', 'error_rate'],
                accuracy=0.82,
                precision=0.79,
                recall=0.85,
                training_data_points=800,
                last_trained=datetime.utcnow() - timedelta(days=10),
                enabled=True
            ),
            'ml-classifier': PredictionModel(
                model_id='ml-classifier',
                model_name='Machine Learning Incident Classifier',
                model_type=PredictionModel.ML_CLASSIFIER,
                description='Classifies incident probability using ML algorithms',
                features=['alert_volume', 'error_rate', 'response_time', 'resource_utilization', 'system_health'],
                accuracy=0.88,
                precision=0.86,
                recall=0.90,
                training_data_points=1200,
                last_trained=datetime.utcnow() - timedelta(days=5),
                enabled=True
            ),
            'ensemble-model': PredictionModel(
                model_id='ensemble-model',
                model_name='Ensemble Prediction Model',
                model_type=PredictionModel.ENSEMBLE,
                description='Combines multiple models for improved accuracy',
                features=['alert_volume', 'error_rate', 'response_time', 'resource_utilization', 'system_health', 'historical_patterns'],
                accuracy=0.91,
                precision=0.89,
                recall=0.93,
                training_data_points=1500,
                last_trained=datetime.utcnow() - timedelta(days=3),
                enabled=True
            )
        }
        
        # Load custom models from file if provided
        if models_file:
            try:
                with open(models_file, 'r') as f:
                    custom_models = json.load(f)
                
                for model_id, model_data in custom_models.items():
                    model = PredictionModel(
                        model_id=model_id,
                        model_name=model_data['model_name'],
                        model_type=PredictionModel(model_data['model_type']),
                        description=model_data['description'],
                        features=model_data['features'],
                        accuracy=model_data['accuracy'],
                        precision=model_data['precision'],
                        recall=model_data['recall'],
                        training_data_points=model_data['training_data_points'],
                        last_trained=datetime.fromisoformat(model_data['last_trained']),
                        enabled=model_data.get('enabled', True)
                    )
                    default_models[model_id] = model
                    
            except Exception as e:
                logger.warning(f"Failed to load custom models: {e}")
        
        self.models = default_models
        logger.info(f"Loaded {len(self.models)} prediction models")
        
        return self.models
    
    def collect_historical_data(self, providers: List[str], days_back: int = 90) -> List[Incident]:
        """Collect historical incident data"""
        logger.info(f"Collecting historical data from providers: {providers}")
        
        all_incidents = []
        
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
                
                # Collect incidents
                provider_incidents = handler.get_historical_incidents(days_back)
                all_incidents.extend(provider_incidents)
                
                logger.info(f"Collected {len(provider_incidents)} incidents from {provider}")
                
            except Exception as e:
                logger.error(f"Failed to collect historical data from {provider}: {e}")
        
        self.historical_data = all_incidents
        logger.info(f"Total historical incidents collected: {len(all_incidents)}")
        
        return all_incidents
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific incident handler"""
        from incident_predictor_handler import get_incident_handler
        region = self.config['providers'][provider]['region']
        return get_incident_handler(provider, region)
    
    def predict_incidents(self, prediction_input: PredictionInput, model_id: Optional[str] = None) -> PredictionResult:
        """Predict incidents using specified model"""
        logger.info(f"Predicting incidents for {prediction_input.timestamp}")
        
        try:
            # Select model
            if model_id:
                if model_id not in self.models:
                    raise ValueError(f"Model {model_id} not found")
                model = self.models[model_id]
            else:
                # Use default model
                default_model_id = self.config['prediction_settings']['default_model']
                model = self.models.get(default_model_id)
                if not model:
                    raise ValueError(f"Default model {default_model_id} not found")
            
            if not model.enabled:
                raise ValueError(f"Model {model.model_id} is disabled")
            
            # Extract features
            features = self._extract_features(prediction_input, model.features)
            
            # Make prediction
            prediction = self._make_prediction(model, features, prediction_input)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(model, features, prediction)
            
            # Generate recommended actions
            recommended_actions = self._generate_recommended_actions(prediction)
            
            # Calculate feature importance
            feature_importance = self._calculate_feature_importance(model, features) if self.config['prediction_settings']['enable_feature_importance'] else {}
            
            # Calculate false positive risk
            false_positive_risk = self._calculate_false_positive_risk(prediction, model) if self.config['prediction_settings']['enable_false_positive_detection'] else 0.1
            
            # Create prediction result
            result = PredictionResult(
                prediction_id=f"pred-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.utcnow(),
                predicted_incidents=prediction['incidents'],
                confidence_score=confidence_score,
                risk_level=self._calculate_risk_level(prediction['incidents']),
                time_horizon_hours=self.config['prediction_settings']['prediction_horizon_hours'],
                recommended_actions=recommended_actions,
                model_used=model.model_type,
                features_importance=feature_importance,
                false_positive_risk=false_positive_risk
            )
            
            # Store prediction
            self.predictions.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to predict incidents: {e}")
            raise
    
    def _extract_features(self, prediction_input: PredictionInput, required_features: List[str]) -> Dict[str, float]:
        """Extract features from prediction input"""
        features = {}
        
        # Extract metrics
        for feature in required_features:
            if feature in prediction_input.metrics:
                features[feature] = prediction_input.metrics[feature]
            elif feature == 'alert_volume':
                features[feature] = len(prediction_input.alerts)
            elif feature == 'error_rate':
                features[feature] = prediction_input.metrics.get('error_rate', 0.0)
            elif feature == 'response_time':
                features[feature] = prediction_input.metrics.get('response_time', 100.0)
            elif feature == 'system_health':
                features[feature] = prediction_input.system_state.get('health_score', 1.0)
            elif feature == 'resource_utilization':
                features[feature] = prediction_input.system_state.get('cpu_utilization', 50.0)
            elif feature == 'historical_patterns':
                features[feature] = self._calculate_historical_patterns(prediction_input)
            else:
                features[feature] = 0.0  # Default value
        
        return features
    
    def _calculate_historical_patterns(self, prediction_input: PredictionInput) -> float:
        """Calculate historical pattern score"""
        # Simplified historical pattern calculation
        # In real implementation, this would analyze historical data patterns
        return random.uniform(0.3, 0.8)
    
    def _make_prediction(self, model: PredictionModel, features: Dict[str, float], prediction_input: PredictionInput) -> Dict[str, Any]:
        """Make prediction using specified model"""
        try:
            if model.model_type == PredictionModel.TIME_SERIES:
                return self._time_series_prediction(model, features, prediction_input)
            elif model.model_type == PredictionModel.ANOMALY_DETECTION:
                return self._anomaly_detection_prediction(model, features, prediction_input)
            elif model.model_type == PredictionModel.ML_CLASSIFIER:
                return self._ml_classifier_prediction(model, features, prediction_input)
            elif model.model_type == PredictionModel.ENSEMBLE:
                return self._ensemble_prediction(model, features, prediction_input)
            else:
                raise ValueError(f"Unsupported model type: {model.model_type}")
                
        except Exception as e:
            logger.error(f"Failed to make prediction with model {model.model_id}: {e}")
            return {'incidents': [], 'error': str(e)}
    
    def _time_series_prediction(self, model: PredictionModel, features: Dict[str, float], prediction_input: PredictionInput) -> Dict[str, Any]:
        """Time series prediction"""
        # Simplified time series prediction
        incident_probability = self._calculate_incident_probability(features)
        
        if incident_probability > 0.7:
            incidents = [
                {
                    'probability': incident_probability,
                    'severity': 'high',
                    'category': 'infrastructure',
                    'estimated_time_hours': random.randint(2, 8),
                    'confidence': 0.8
                }
            ]
        elif incident_probability > 0.5:
            incidents = [
                {
                    'probability': incident_probability,
                    'severity': 'medium',
                    'category': 'application',
                    'estimated_time_hours': random.randint(4, 12),
                    'confidence': 0.7
                }
            ]
        else:
            incidents = []
        
        return {'incidents': incidents}
    
    def _anomaly_detection_prediction(self, model: PredictionModel, features: Dict[str, float], prediction_input: PredictionInput) -> Dict[str, Any]:
        """Anomaly detection prediction"""
        # Simplified anomaly detection
        anomaly_score = self._calculate_anomaly_score(features)
        
        if anomaly_score > 0.8:
            incidents = [
                {
                    'probability': anomaly_score,
                    'severity': 'critical',
                    'category': 'infrastructure',
                    'estimated_time_hours': random.randint(1, 4),
                    'confidence': 0.85
                }
            ]
        elif anomaly_score > 0.6:
            incidents = [
                {
                    'probability': anomaly_score,
                    'severity': 'high',
                    'category': 'performance',
                    'estimated_time_hours': random.randint(3, 6),
                    'confidence': 0.75
                }
            ]
        else:
            incidents = []
        
        return {'incidents': incidents}
    
    def _ml_classifier_prediction(self, model: PredictionModel, features: Dict[str, float], prediction_input: PredictionInput) -> Dict[str, Any]:
        """Machine learning classifier prediction"""
        # Simplified ML classifier
        incident_probability = self._calculate_incident_probability(features)
        
        # Determine category based on features
        if features.get('error_rate', 0) > 10:
            category = 'application'
        elif features.get('cpu_utilization', 0) > 90:
            category = 'infrastructure'
        elif features.get('response_time', 0) > 500:
            category = 'performance'
        else:
            category = 'application'
        
        # Determine severity
        if incident_probability > 0.8:
            severity = 'critical'
        elif incident_probability > 0.6:
            severity = 'high'
        elif incident_probability > 0.4:
            severity = 'medium'
        else:
            severity = 'low'
        
        if incident_probability > 0.5:
            incidents = [
                {
                    'probability': incident_probability,
                    'severity': severity,
                    'category': category,
                    'estimated_time_hours': random.randint(2, 10),
                    'confidence': 0.82
                }
            ]
        else:
            incidents = []
        
        return {'incidents': incidents}
    
    def _ensemble_prediction(self, model: PredictionModel, features: Dict[str, float], prediction_input: PredictionInput) -> Dict[str, Any]:
        """Ensemble prediction combining multiple models"""
        # Get predictions from individual models
        time_series_result = self._time_series_prediction(model, features, prediction_input)
        anomaly_result = self._anomaly_detection_prediction(model, features, prediction_input)
        ml_result = self._ml_classifier_prediction(model, features, prediction_input)
        
        # Combine predictions
        all_incidents = []
        all_incidents.extend(time_series_result.get('incidents', []))
        all_incidents.extend(anomaly_result.get('incidents', []))
        all_incidents.extend(ml_result.get('incidents', []))
        
        # Weight and deduplicate incidents
        weighted_incidents = self._weight_and_deduplicate_incidents(all_incidents)
        
        return {'incidents': weighted_incidents}
    
    def _calculate_incident_probability(self, features: Dict[str, float]) -> float:
        """Calculate incident probability from features"""
        weights = self.config['feature_weights']
        
        probability = 0.0
        total_weight = 0.0
        
        for feature, value in features.items():
            if feature in weights:
                weight = weights[feature]
                probability += value * weight
                total_weight += weight
        
        if total_weight > 0:
            probability = probability / total_weight
        
        # Normalize to 0-1 range
        return min(max(probability / 100.0, 0.0), 1.0)
    
    def _calculate_anomaly_score(self, features: Dict[str, float]) -> float:
        """Calculate anomaly score from features"""
        # Simplified anomaly detection
        anomalies = 0
        total_features = 0
        
        for feature, value in features.items():
            total_features += 1
            
            # Check for anomalous values
            if feature == 'cpu_usage' and value > 95:
                anomalies += 1
            elif feature == 'memory_usage' and value > 90:
                anomalies += 1
            elif feature == 'error_rate' and value > 5:
                anomalies += 1
            elif feature == 'response_time' and value > 1000:
                anomalies += 1
        
        return anomalies / total_features if total_features > 0 else 0.0
    
    def _weight_and_deduplicate_incidents(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Weight and deduplicate incidents"""
        # Group incidents by category and severity
        incident_groups = {}
        
        for incident in incidents:
            key = f"{incident['category']}-{incident['severity']}"
            if key not in incident_groups:
                incident_groups[key] = []
            incident_groups[key].append(incident)
        
        # Combine incidents in each group
        combined_incidents = []
        for group_key, group_incidents in incident_groups.items():
            # Average probabilities
            avg_probability = sum(inc['probability'] for inc in group_incidents) / len(group_incidents)
            
            # Use highest confidence
            max_confidence = max(inc['confidence'] for inc in group_incidents)
            
            # Average estimated time
            avg_time = sum(inc['estimated_time_hours'] for inc in group_incidents) / len(group_incidents)
            
            combined_incident = {
                'probability': avg_probability,
                'severity': group_incidents[0]['severity'],
                'category': group_incidents[0]['category'],
                'estimated_time_hours': int(avg_time),
                'confidence': max_confidence
            }
            combined_incidents.append(combined_incident)
        
        return combined_incidents
    
    def _calculate_confidence_score(self, model: PredictionModel, features: Dict[str, float], prediction: Dict[str, Any]) -> float:
        """Calculate confidence score for prediction"""
        # Base confidence from model accuracy
        base_confidence = model.accuracy
        
        # Adjust based on feature completeness
        feature_completeness = len([f for f in model.features if f in features]) / len(model.features)
        
        # Adjust based on prediction consistency
        prediction_consistency = 1.0 if prediction.get('incidents') else 0.0
        
        # Calculate final confidence
        confidence = base_confidence * feature_completeness * prediction_consistency
        
        return min(confidence, 1.0)
    
    def _calculate_risk_level(self, incidents: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level"""
        if not incidents:
            return 'low'
        
        # Calculate weighted risk score
        total_risk = 0.0
        
        for incident in incidents:
            severity_weight = {'critical': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.4}
            weight = severity_weight.get(incident['severity'], 0.5)
            total_risk += incident['probability'] * weight
        
        avg_risk = total_risk / len(incidents)
        
        if avg_risk > 0.8:
            return 'critical'
        elif avg_risk > 0.6:
            return 'high'
        elif avg_risk > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommended_actions(self, prediction: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on prediction"""
        actions = []
        
        incidents = prediction.get('incidents', [])
        
        if not incidents:
            actions.append("Continue monitoring system health")
            return actions
        
        # Generate actions based on incident severity and category
        for incident in incidents:
            if incident['severity'] == 'critical':
                actions.extend([
                    "Immediate investigation required",
                    "Notify on-call team",
                    "Prepare emergency response plan",
                    "Check system dependencies"
                ])
            elif incident['severity'] == 'high':
                actions.extend([
                    "Investigate within 30 minutes",
                    "Review recent changes",
                    "Check system metrics"
                ])
            elif incident['severity'] == 'medium':
                actions.extend([
                    "Investigate within 2 hours",
                    "Monitor for escalation",
                    "Review performance trends"
                ])
            
            # Category-specific actions
            if incident['category'] == 'infrastructure':
                actions.append("Check resource utilization and capacity")
            elif incident['category'] == 'application':
                actions.append("Review application logs and metrics")
            elif incident['category'] == 'security':
                actions.append("Review security logs and access patterns")
            elif incident['category'] == 'performance':
                actions.append("Analyze performance bottlenecks")
        
        # Remove duplicates
        actions = list(set(actions))
        
        return actions[:10]  # Limit to top 10 actions
    
    def _calculate_feature_importance(self, model: PredictionModel, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate feature importance"""
        # Simplified feature importance calculation
        importance = {}
        
        for feature in model.features:
            if feature in features:
                # Use normalized feature value as importance
                importance[feature] = min(features[feature] / 100.0, 1.0)
            else:
                importance[feature] = 0.0
        
        # Normalize importance scores
        total_importance = sum(importance.values())
        if total_importance > 0:
            for feature in importance:
                importance[feature] = importance[feature] / total_importance
        
        return importance
    
    def _calculate_false_positive_risk(self, prediction: Dict[str, Any], model: PredictionModel) -> float:
        """Calculate false positive risk"""
        # Use model precision as base false positive risk
        base_risk = 1.0 - model.precision
        
        # Adjust based on prediction confidence
        incidents = prediction.get('incidents', [])
        if incidents:
            avg_confidence = sum(inc['confidence'] for inc in incidents) / len(incidents)
            adjusted_risk = base_risk * (1.0 - avg_confidence)
        else:
            adjusted_risk = 0.0
        
        return max(adjusted_risk, 0.0)
    
    def batch_predict(self, prediction_inputs: List[PredictionInput], model_id: Optional[str] = None) -> List[PredictionResult]:
        """Predict incidents for multiple inputs"""
        logger.info(f"Batch predicting for {len(prediction_inputs)} inputs")
        
        results = []
        
        for prediction_input in prediction_inputs:
            try:
                result = self.predict_incidents(prediction_input, model_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to predict for input {prediction_input.timestamp}: {e}")
                # Create a failed result
                result = PredictionResult(
                    prediction_id=f"failed-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    timestamp=datetime.utcnow(),
                    predicted_incidents=[],
                    confidence_score=0.0,
                    risk_level='unknown',
                    time_horizon_hours=self.config['prediction_settings']['prediction_horizon_hours'],
                    recommended_actions=['Manual review required'],
                    model_used=PredictionModel.ENSEMBLE,
                    features_importance={},
                    false_positive_risk=1.0
                )
                results.append(result)
        
        return results
    
    def generate_prediction_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive prediction report"""
        logger.info("Generating prediction report")
        
        # Calculate statistics
        total_predictions = len(self.predictions)
        high_risk_predictions = len([p for p in self.predictions if p.risk_level in ['critical', 'high']])
        avg_confidence = sum(p.confidence_score for p in self.predictions) / total_predictions if total_predictions > 0 else 0
        avg_false_positive_risk = sum(p.false_positive_risk for p in self.predictions) / total_predictions if total_predictions > 0 else 0
        
        # Model usage statistics
        model_usage = {}
        for prediction in self.predictions:
            model_type = prediction.model_used.value
            model_usage[model_type] = model_usage.get(model_type, 0) + 1
        
        # Risk level distribution
        risk_distribution = {}
        for prediction in self.predictions:
            risk_level = prediction.risk_level
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Recent predictions
        recent_predictions = self.predictions[-20:]
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_predictions': total_predictions,
                'high_risk_predictions': high_risk_predictions,
                'average_confidence': avg_confidence,
                'average_false_positive_risk': avg_false_positive_risk,
                'enabled_models': len([m for m in self.models.values() if m.enabled]),
                'historical_incidents': len(self.historical_data)
            },
            'model_usage': model_usage,
            'risk_distribution': risk_distribution,
            'recent_predictions': [
                {
                    'prediction_id': p.prediction_id,
                    'timestamp': p.timestamp.isoformat(),
                    'risk_level': p.risk_level,
                    'confidence_score': p.confidence_score,
                    'predicted_incidents': len(p.predicted_incidents),
                    'model_used': p.model_used.value,
                    'false_positive_risk': p.false_positive_risk
                }
                for p in recent_predictions
            ],
            'model_performance': {
                model_id: {
                    'accuracy': model.accuracy,
                    'precision': model.precision,
                    'recall': model.recall,
                    'training_data_points': model.training_data_points,
                    'last_trained': model.last_trained.isoformat(),
                    'enabled': model.enabled
                }
                for model_id, model in self.models.items()
            }
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Prediction report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Incident Predictor")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--models", help="Prediction models file")
    parser.add_argument("--action", choices=['collect', 'predict', 'batch', 'report'], 
                       default='predict', help="Action to perform")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--days-back", type=int, default=90, help="Days of historical data to collect")
    parser.add_argument("--model-id", help="Prediction model ID")
    parser.add_argument("--input-file", help="Input file for prediction")
    parser.add_argument("--batch-file", help="Batch input file")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize incident predictor
    predictor = IncidentPredictor(args.config)
    
    # Load models
    predictor.load_prediction_models(args.models)
    
    try:
        if args.action == 'collect':
            # Collect historical data
            incidents = predictor.collect_historical_data(args.providers, args.days_back)
            
            print(f"\nHistorical Data Collection Results:")
            print(f"Total Incidents: {len(incidents)}")
            
            # Group by provider
            provider_counts = {}
            for incident in incidents:
                provider = incident.provider
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
            
            for provider, count in provider_counts.items():
                print(f"{provider}: {count} incidents")
        
        elif args.action == 'predict':
            if not args.input_file:
                print("Error: --input-file required for predict action")
                sys.exit(1)
            
            with open(args.input_file, 'r') as f:
                input_data = json.load(f)
            
            # Create prediction input
            prediction_input = PredictionInput(
                timestamp=datetime.fromisoformat(input_data['timestamp']),
                metrics=input_data.get('metrics', {}),
                alerts=input_data.get('alerts', []),
                system_state=input_data.get('system_state', {}),
                environmental_factors=input_data.get('environmental_factors', {})
            )
            
            # Make prediction
            result = predictor.predict_incidents(prediction_input, args.model_id)
            
            print(f"\nPrediction Result:")
            print(f"Prediction ID: {result.prediction_id}")
            print(f"Model Used: {result.model_used.value}")
            print(f"Risk Level: {result.risk_level}")
            print(f"Confidence Score: {result.confidence_score:.2f}")
            print(f"Predicted Incidents: {len(result.predicted_incidents)}")
            print(f"False Positive Risk: {result.false_positive_risk:.2f}")
            
            if result.predicted_incidents:
                print("\nPredicted Incidents:")
                for i, incident in enumerate(result.predicted_incidents):
                    print(f"  {i+1}. {incident['category']} - {incident['severity']} (Probability: {incident['probability']:.2f})")
            
            if result.recommended_actions:
                print("\nRecommended Actions:")
                for action in result.recommended_actions[:5]:
                    print(f"  - {action}")
        
        elif args.action == 'batch':
            if not args.batch_file:
                print("Error: --batch-file required for batch action")
                sys.exit(1)
            
            with open(args.batch_file, 'r') as f:
                batch_data = json.load(f)
            
            # Create prediction inputs
            prediction_inputs = []
            for input_data in batch_data:
                prediction_input = PredictionInput(
                    timestamp=datetime.fromisoformat(input_data['timestamp']),
                    metrics=input_data.get('metrics', {}),
                    alerts=input_data.get('alerts', []),
                    system_state=input_data.get('system_state', {}),
                    environmental_factors=input_data.get('environmental_factors', {})
                )
                prediction_inputs.append(prediction_input)
            
            # Batch predict
            results = predictor.batch_predict(prediction_inputs, args.model_id)
            
            print(f"\nBatch Prediction Results:")
            success_count = len([r for r in results if r.confidence_score > 0])
            failed_count = len(results) - success_count
            
            print(f"Total Predictions: {len(results)}")
            print(f"Successful: {success_count}")
            print(f"Failed: {failed_count}")
            print(f"Average Confidence: {sum(r.confidence_score for r in results) / len(results):.2f}")
            
            if args.output:
                results_data = [
                    {
                        'prediction_id': r.prediction_id,
                        'risk_level': r.risk_level,
                        'confidence_score': r.confidence_score,
                        'predicted_incidents': len(r.predicted_incidents),
                        'model_used': r.model_used.value
                    }
                    for r in results
                ]
                with open(args.output, 'w') as f:
                    json.dump(results_data, f, indent=2)
                print(f"Results saved to: {args.output}")
        
        elif args.action == 'report':
            report = predictor.generate_prediction_report(args.output)
            
            summary = report['summary']
            print(f"\nPrediction Report:")
            print(f"Total Predictions: {summary['total_predictions']}")
            print(f"High Risk Predictions: {summary['high_risk_predictions']}")
            print(f"Average Confidence: {summary['average_confidence']:.2f}")
            print(f"Average False Positive Risk: {summary['average_false_positive_risk']:.2f}")
            print(f"Enabled Models: {summary['enabled_models']}")
            print(f"Historical Incidents: {summary['historical_incidents']}")
            
            if args.output:
                print(f"Report saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
