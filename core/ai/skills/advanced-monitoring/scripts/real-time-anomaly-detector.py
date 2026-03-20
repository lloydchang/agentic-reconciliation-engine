#!/usr/bin/env python3
"""
Real-Time Anomaly Detection Engine

Advanced real-time anomaly detection with streaming analytics, 
machine learning models, and intelligent alerting.
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
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    from sklearn.cluster import DBSCAN
    import statsmodels.api as sm
    AI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"AI/ML libraries not available: {e}. Using fallback functionality.")
    AI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DetectionMethod(Enum):
    STATISTICAL = "statistical"
    ISOLATION_FOREST = "isolation_forest"
    DBSCAN = "dbscan"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"

@dataclass
class StreamingMetric:
    metric_id: str
    metric_name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    source: str
    resource_id: str

@dataclass
class AnomalyEvent:
    event_id: str
    metric_name: str
    resource_id: str
    anomaly_type: str
    severity: AnomalySeverity
    confidence_score: float
    detected_at: datetime
    value: float
    expected_range: Tuple[float, float]
    description: str
    detection_method: DetectionMethod
    context: Dict[str, Any]

class RealTimeAnomalyDetector:
    """Real-time anomaly detection engine with streaming analytics"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.metric_streams = defaultdict(lambda: deque(maxlen=1000))
        self.anomaly_models = {}
        self.scalers = {}
        self.detection_methods = []
        self.is_running = False
        self.anomaly_events = deque(maxlen=10000)
        
        # Initialize detection methods
        self._initialize_detection_methods()
        
        # Start background processing
        self._start_background_processing()
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load anomaly detection configuration"""
        default_config = {
            'detection': {
                'methods': ['statistical', 'isolation_forest', 'moving_average'],
                'sensitivity': 0.95,
                'min_samples': 50,
                'window_size': 100,
                'update_interval': 60,  # seconds
                'batch_size': 100
            },
            'thresholds': {
                'statistical_z_score': 3.0,
                'isolation_forest_contamination': 0.1,
                'dbscan_eps': 0.5,
                'moving_average_window': 20,
                'exponential_smoothing_alpha': 0.3
            },
            'alerting': {
                'cooldown_period': 300,  # seconds
                'max_alerts_per_minute': 10,
                'severity_thresholds': {
                    'critical': 0.9,
                    'high': 0.8,
                    'medium': 0.7,
                    'low': 0.6
                }
            },
            'streaming': {
                'buffer_size': 1000,
                'processing_interval': 5,  # seconds
                'max_processing_time': 30  # seconds
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
    
    def _initialize_detection_methods(self):
        """Initialize anomaly detection methods"""
        methods = self.config['detection']['methods']
        
        if 'statistical' in methods:
            self.detection_methods.append(self._statistical_detection)
        
        if 'isolation_forest' in methods and AI_AVAILABLE:
            self.detection_methods.append(self._isolation_forest_detection)
        
        if 'dbscan' in methods and AI_AVAILABLE:
            self.detection_methods.append(self._dbscan_detection)
        
        if 'moving_average' in methods:
            self.detection_methods.append(self._moving_average_detection)
        
        if 'exponential_smoothing' in methods:
            self.detection_methods.append(self._exponential_smoothing_detection)
        
        if 'seasonal_decomposition' in methods:
            self.detection_methods.append(self._seasonal_decomposition_detection)
        
        logger.info(f"Initialized {len(self.detection_methods)} detection methods")
    
    def _start_background_processing(self):
        """Start background processing thread"""
        def background_processor():
            while self.is_running:
                try:
                    self._process_metric_streams()
                    time.sleep(self.config['streaming']['processing_interval'])
                except Exception as e:
                    logger.error(f"Background processing error: {e}")
                    time.sleep(10)  # Wait before retrying
        
        self.is_running = True
        self.background_thread = threading.Thread(target=background_processor, daemon=True)
        self.background_thread.start()
        logger.info("Background anomaly detection processor started")
    
    def ingest_metric_stream(self, metrics: List[StreamingMetric]) -> int:
        """Ingest streaming metrics for real-time analysis"""
        ingested_count = 0
        
        for metric in metrics:
            try:
                # Add to stream buffer
                self.metric_streams[metric.metric_name].append(metric)
                ingested_count += 1
                
                # Trigger immediate processing for critical metrics
                if self._is_critical_metric(metric):
                    self._process_metric_immediately(metric)
                
            except Exception as e:
                logger.warning(f"Failed to ingest metric {metric.metric_id}: {e}")
                continue
        
        logger.debug(f"Ingested {ingested_count} metrics")
        return ingested_count
    
    def _is_critical_metric(self, metric: StreamingMetric) -> bool:
        """Check if metric requires immediate processing"""
        critical_metrics = ['cpu_utilization', 'memory_utilization', 'error_rate', 'availability']
        return metric.metric_name in critical_metrics
    
    def _process_metric_immediately(self, metric: StreamingMetric):
        """Process a single metric immediately"""
        try:
            # Get recent metrics for this metric name
            recent_metrics = list(self.metric_streams[metric.metric_name])
            
            if len(recent_metrics) >= self.config['detection']['min_samples']:
                # Run detection methods
                anomalies = self._detect_anomalies_for_metric(metric.metric_name, recent_metrics)
                
                # Store anomalies
                for anomaly in anomalies:
                    self.anomaly_events.append(anomaly)
                    
                    # Trigger immediate alert for critical anomalies
                    if anomaly.severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
                        self._trigger_immediate_alert(anomaly)
        
        except Exception as e:
            logger.warning(f"Failed immediate processing for metric {metric.metric_id}: {e}")
    
    def _process_metric_streams(self):
        """Process all metric streams in background"""
        try:
            for metric_name, metric_stream in self.metric_streams.items():
                if len(metric_stream) >= self.config['detection']['min_samples']:
                    # Get recent metrics
                    recent_metrics = list(metric_stream)
                    
                    # Detect anomalies
                    anomalies = self._detect_anomalies_for_metric(metric_name, recent_metrics)
                    
                    # Store anomalies
                    for anomaly in anomalies:
                        self.anomaly_events.append(anomaly)
        
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")
    
    def _detect_anomalies_for_metric(self, metric_name: str, metrics: List[StreamingMetric]) -> List[AnomalyEvent]:
        """Detect anomalies for a specific metric using all enabled methods"""
        all_anomalies = []
        
        for detection_method in self.detection_methods:
            try:
                anomalies = detection_method(metric_name, metrics)
                all_anomalies.extend(anomalies)
            except Exception as e:
                logger.warning(f"Detection method {detection_method.__name__} failed: {e}")
                continue
        
        # Remove duplicates and merge similar anomalies
        merged_anomalies = self._merge_similar_anomalies(all_anomalies)
        
        return merged_anomalies
    
    def _statistical_detection(self, metric_name: str, metrics: List[StreamingMetric]) -> List[AnomalyEvent]:
        """Statistical anomaly detection using z-score"""
        anomalies = []
        
        try:
            if len(metrics) < 30:
                return anomalies
            
            # Extract values
            values = np.array([m.value for m in metrics])
            
            # Calculate statistics
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val == 0:
                return anomalies
            
            # Calculate z-scores
            z_scores = np.abs((values - mean_val) / std_val)
            
            # Find anomalies
            threshold = self.config['thresholds']['statistical_z_score']
            anomaly_indices = np.where(z_scores > threshold)[0]
            
            for idx in anomaly_indices:
                metric = metrics[idx]
                severity = self._calculate_severity_from_z_score(z_scores[idx])
                
                anomaly = AnomalyEvent(
                    event_id=f"stat-{metric_name}-{metric.timestamp.strftime('%Y%m%d%H%M%S')}",
                    metric_name=metric_name,
                    resource_id=metric.resource_id,
                    anomaly_type="statistical_outlier",
                    severity=severity,
                    confidence_score=min(0.99, z_scores[idx] / threshold),
                    detected_at=metric.timestamp,
                    value=metric.value,
                    expected_range=(mean_val - 2*std_val, mean_val + 2*std_val),
                    description=f"Statistical anomaly: z-score {z_scores[idx]:.2f}",
                    detection_method=DetectionMethod.STATISTICAL,
                    context={
                        'z_score': z_scores[idx],
                        'mean': mean_val,
                        'std_dev': std_val,
                        'threshold': threshold
                    }
                )
                anomalies.append(anomaly)
        
        except Exception as e:
            logger.warning(f"Statistical detection failed for {metric_name}: {e}")
        
        return anomalies
    
    def _isolation_forest_detection(self, metric_name: str, metrics: List[StreamingMetric]) -> List[AnomalyEvent]:
        """Isolation Forest anomaly detection"""
        anomalies = []
        
        try:
            if len(metrics) < 50:
                return anomalies
            
            # Extract features
            features = []
            timestamps = []
            
            for metric in metrics:
                # Create feature vector with value and time-based features
                feature_vector = [
                    metric.value,
                    metric.timestamp.hour,
                    metric.timestamp.weekday(),
                    metric.timestamp.minute,
                    len(metric.labels)  # Number of labels
                ]
                features.append(feature_vector)
                timestamps.append(metric.timestamp)
            
            X = np.array(features)
            
            # Initialize or get model
            model_key = f"isolation_forest_{metric_name}"
            if model_key not in self.anomaly_models:
                self.anomaly_models[model_key] = IsolationForest(
                    contamination=self.config['thresholds']['isolation_forest_contamination'],
                    random_state=42
                )
                # Fit the model
                self.anomaly_models[model_key].fit(X)
            
            model = self.anomaly_models[model_key]
            
            # Predict anomalies
            predictions = model.predict(X)
            scores = model.decision_function(X)
            
            # Find anomalies (predictions == -1)
            anomaly_indices = np.where(predictions == -1)[0]
            
            for idx in anomaly_indices:
                metric = metrics[idx]
                score = scores[idx]
                severity = self._calculate_severity_from_isolation_score(score)
                
                anomaly = AnomalyEvent(
                    event_id=f"if-{metric_name}-{metric.timestamp.strftime('%Y%m%d%H%M%S')}",
                    metric_name=metric_name,
                    resource_id=metric.resource_id,
                    anomaly_type="isolation_forest_outlier",
                    severity=severity,
                    confidence_score=min(0.99, abs(score)),
                    detected_at=metric.timestamp,
                    value=metric.value,
                    expected_range=(0, 0),  # Not applicable for isolation forest
                    description=f"Isolation Forest anomaly: score {score:.3f}",
                    detection_method=DetectionMethod.ISOLATION_FOREST,
                    context={
                        'isolation_score': score,
                        'model_contamination': self.config['thresholds']['isolation_forest_contamination']
                    }
                )
                anomalies.append(anomaly)
        
        except Exception as e:
            logger.warning(f"Isolation Forest detection failed for {metric_name}: {e}")
        
        return anomalies
    
    def _dbscan_detection(self, metric_name: str, metrics: List[StreamingMetric]) -> List[AnomalyEvent]:
        """DBSCAN clustering anomaly detection"""
        anomalies = []
        
        try:
            if len(metrics) < 30:
                return anomalies
            
            # Extract features for clustering
            features = []
            timestamps = []
            
            for metric in metrics:
                feature_vector = [
                    metric.value,
                    metric.timestamp.hour,
                    metric.timestamp.weekday()
                ]
                features.append(feature_vector)
                timestamps.append(metric.timestamp)
            
            X = np.array(features)
            
            # Scale features
            scaler_key = f"dbscan_scaler_{metric_name}"
            if scaler_key not in self.scalers:
                self.scalers[scaler_key] = StandardScaler()
                X_scaled = self.scalers[scaler_key].fit_transform(X)
            else:
                X_scaled = self.scalers[scaler_key].transform(X)
            
            # Apply DBSCAN
            eps = self.config['thresholds']['dbscan_eps']
            min_samples = max(5, len(metrics) // 10)
            
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            cluster_labels = dbscan.fit_predict(X_scaled)
            
            # Find noise points (label == -1)
            noise_indices = np.where(cluster_labels == -1)[0]
            
            for idx in noise_indices:
                metric = metrics[idx]
                severity = AnomalySeverity.MEDIUM  # Default for DBSCAN
                
                anomaly = AnomalyEvent(
                    event_id=f"dbscan-{metric_name}-{metric.timestamp.strftime('%Y%m%d%H%M%S')}",
                    metric_name=metric_name,
                    resource_id=metric.resource_id,
                    anomaly_type="dbscan_outlier",
                    severity=severity,
                    confidence_score=0.7,
                    detected_at=metric.timestamp,
                    value=metric.value,
                    expected_range=(0, 0),  # Not applicable for DBSCAN
                    description=f"DBSCAN detected noise point",
                    detection_method=DetectionMethod.DBSCAN,
                    context={
                        'cluster_label': -1,
                        'eps': eps,
                        'min_samples': min_samples
                    }
                )
                anomalies.append(anomaly)
        
        except Exception as e:
            logger.warning(f"DBSCAN detection failed for {metric_name}: {e}")
        
        return anomalies
    
    def _moving_average_detection(self, metric_name: str, metrics: List[StreamingMetric]) -> List[AnomalyEvent]:
        """Moving average anomaly detection"""
        anomalies = []
        
        try:
            window_size = self.config['thresholds']['moving_average_window']
            
            if len(metrics) < window_size + 10:
                return anomalies
            
            # Extract values and timestamps
            values = [m.value for m in metrics]
            timestamps = [m.timestamp for m in metrics]
            
            # Calculate moving average
            moving_avg = pd.Series(values).rolling(window=window_size).mean()
            moving_std = pd.Series(values).rolling(window=window_size).std()
            
            # Detect anomalies
            threshold_multiplier = 2.5
            for i in range(window_size, len(values)):
                if pd.isna(moving_avg.iloc[i]) or pd.isna(moving_std.iloc[i]):
                    continue
                
                avg = moving_avg.iloc[i]
                std = moving_std.iloc[i]
                current_value = values[i]
                
                if std > 0:
                    z_score = abs(current_value - avg) / std
                    if z_score > threshold_multiplier:
                        metric = metrics[i]
                        severity = self._calculate_severity_from_z_score(z_score)
                        
                        anomaly = AnomalyEvent(
                            event_id=f"ma-{metric_name}-{metric.timestamp.strftime('%Y%m%d%H%M%S')}",
                            metric_name=metric_name,
                            resource_id=metric.resource_id,
                            anomaly_type="moving_average_anomaly",
                            severity=severity,
                            confidence_score=min(0.99, z_score / threshold_multiplier),
                            detected_at=metric.timestamp,
                            value=current_value,
                            expected_range=(avg - 2*std, avg + 2*std),
                            description=f"Moving average anomaly: {current_value:.2f} vs avg {avg:.2f}",
                            detection_method=DetectionMethod.MOVING_AVERAGE,
                            context={
                                'moving_average': avg,
                                'moving_std': std,
                                'z_score': z_score,
                                'window_size': window_size
                            }
                        )
                        anomalies.append(anomaly)
        
        except Exception as e:
            logger.warning(f"Moving average detection failed for {metric_name}: {e}")
        
        return anomalies
    
    def _exponential_smoothing_detection(self, metric_name: str, metrics: List[StreamingMetric]) -> List[AnomalyEvent]:
        """Exponential smoothing anomaly detection"""
        anomalies = []
        
        try:
            alpha = self.config['thresholds']['exponential_smoothing_alpha']
            
            if len(metrics) < 20:
                return anomalies
            
            # Extract values
            values = [m.value for m in metrics]
            timestamps = [m.timestamp for m in metrics]
            
            # Calculate exponential smoothing
            smoothed_values = [values[0]]
            for i in range(1, len(values)):
                smoothed_value = alpha * values[i] + (1 - alpha) * smoothed_values[-1]
                smoothed_values.append(smoothed_value)
            
            # Calculate residuals
            residuals = [abs(values[i] - smoothed_values[i]) for i in range(len(values))]
            
            # Calculate threshold based on residual standard deviation
            residual_std = np.std(residuals)
            threshold = 2.5 * residual_std
            
            # Detect anomalies
            for i in range(len(values)):
                if residuals[i] > threshold:
                    metric = metrics[i]
                    severity = AnomalySeverity.MEDIUM
                    
                    anomaly = AnomalyEvent(
                        event_id=f"es-{metric_name}-{metric.timestamp.strftime('%Y%m%d%H%M%S')}",
                        metric_name=metric_name,
                        resource_id=metric.resource_id,
                        anomaly_type="exponential_smoothing_anomaly",
                        severity=severity,
                        confidence_score=min(0.99, residuals[i] / threshold),
                        detected_at=metric.timestamp,
                        value=values[i],
                        expected_range=(smoothed_values[i] - threshold, smoothed_values[i] + threshold),
                        description=f"Exponential smoothing anomaly: residual {residuals[i]:.2f}",
                        detection_method=DetectionMethod.EXPONENTIAL_SMOOTHING,
                        context={
                            'smoothed_value': smoothed_values[i],
                            'residual': residuals[i],
                            'threshold': threshold,
                            'alpha': alpha
                        }
                    )
                    anomalies.append(anomaly)
        
        except Exception as e:
            logger.warning(f"Exponential smoothing detection failed for {metric_name}: {e}")
        
        return anomalies
    
    def _seasonal_decomposition_detection(self, metric_name: str, metrics: List[StreamingMetric]) -> List[AnomalyEvent]:
        """Seasonal decomposition anomaly detection"""
        anomalies = []
        
        try:
            if len(metrics) < 100:  # Need sufficient data for seasonal decomposition
                return anomalies
            
            # Create time series
            values = [m.value for m in metrics]
            timestamps = [m.timestamp for m in metrics]
            
            # Create pandas Series with datetime index
            ts = pd.Series(values, index=timestamps)
            
            # Resample to regular intervals if needed
            ts = ts.resample('5T').mean().fillna(method='ffill')
            
            # Perform seasonal decomposition
            decomposition = sm.tsa.seasonal_decompose(ts, model='additive', period=24)  # 24-hour seasonality
            
            # Get residuals
            residuals = decomposition.resid.dropna()
            
            # Calculate threshold
            residual_std = residuals.std()
            threshold = 2.5 * residual_std
            
            # Detect anomalies in residuals
            anomaly_times = residuals[abs(residuals) > threshold].index
            
            for timestamp in anomaly_times:
                # Find corresponding metric
                metric = None
                for m in metrics:
                    if abs((m.timestamp - timestamp).total_seconds()) < 300:  # Within 5 minutes
                        metric = m
                        break
                
                if metric:
                    residual_value = residuals[timestamp]
                    severity = AnomalySeverity.MEDIUM
                    
                    anomaly = AnomalyEvent(
                        event_id=f"sd-{metric_name}-{metric.timestamp.strftime('%Y%m%d%H%M%S')}",
                        metric_name=metric_name,
                        resource_id=metric.resource_id,
                        anomaly_type="seasonal_decomposition_anomaly",
                        severity=severity,
                        confidence_score=min(0.99, abs(residual_value) / threshold),
                        detected_at=metric.timestamp,
                        value=metric.value,
                        expected_range=(0, 0),  # Complex to calculate for seasonal decomposition
                        description=f"Seasonal decomposition anomaly: residual {residual_value:.2f}",
                        detection_method=DetectionMethod.SEASONAL_DECOMPOSITION,
                        context={
                            'residual': residual_value,
                            'threshold': threshold,
                            'seasonal_component': decomposition.seasonal[timestamp],
                            'trend_component': decomposition.trend[timestamp]
                        }
                    )
                    anomalies.append(anomaly)
        
        except Exception as e:
            logger.warning(f"Seasonal decomposition detection failed for {metric_name}: {e}")
        
        return anomalies
    
    def _calculate_severity_from_z_score(self, z_score: float) -> AnomalySeverity:
        """Calculate anomaly severity from z-score"""
        if z_score > 4:
            return AnomalySeverity.CRITICAL
        elif z_score > 3:
            return AnomalySeverity.HIGH
        elif z_score > 2:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_severity_from_isolation_score(self, score: float) -> AnomalySeverity:
        """Calculate anomaly severity from isolation forest score"""
        # Isolation forest scores are negative for anomalies
        abs_score = abs(score)
        
        if abs_score > 0.5:
            return AnomalySeverity.CRITICAL
        elif abs_score > 0.3:
            return AnomalySeverity.HIGH
        elif abs_score > 0.2:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _merge_similar_anomalies(self, anomalies: List[AnomalyEvent]) -> List[AnomalyEvent]:
        """Merge similar anomalies to reduce duplicates"""
        if not anomalies:
            return anomalies
        
        # Sort by timestamp
        anomalies.sort(key=lambda x: x.detected_at)
        
        merged = []
        current_anomaly = anomalies[0]
        
        for anomaly in anomalies[1:]:
            # Check if anomalies are similar (same metric, resource, and close in time)
            time_diff = abs((anomaly.detected_at - current_anomaly.detected_at).total_seconds())
            
            if (anomaly.metric_name == current_anomaly.metric_name and
                anomaly.resource_id == current_anomaly.resource_id and
                time_diff < 300):  # Within 5 minutes
                
                # Merge anomalies (keep the one with higher confidence)
                if anomaly.confidence_score > current_anomaly.confidence_score:
                    current_anomaly = anomaly
            else:
                merged.append(current_anomaly)
                current_anomaly = anomaly
        
        merged.append(current_anomaly)
        return merged
    
    def _trigger_immediate_alert(self, anomaly: AnomalyEvent):
        """Trigger immediate alert for critical anomaly"""
        try:
            alert_data = {
                'alert_id': f"immediate-{anomaly.event_id}",
                'title': f"Critical Anomaly: {anomaly.metric_name}",
                'severity': anomaly.severity.value,
                'description': anomaly.description,
                'resource_id': anomaly.resource_id,
                'detected_at': anomaly.detected_at.isoformat(),
                'confidence': anomaly.confidence_score,
                'context': anomaly.context
            }
            
            # In real implementation, this would send to alerting system
            logger.critical(f"IMMEDIATE ALERT: {json.dumps(alert_data)}")
            
        except Exception as e:
            logger.error(f"Failed to trigger immediate alert: {e}")
    
    def get_recent_anomalies(self, time_period: timedelta = timedelta(hours=1)) -> List[AnomalyEvent]:
        """Get recent anomalies within time period"""
        cutoff_time = datetime.utcnow() - time_period
        
        recent_anomalies = [
            anomaly for anomaly in self.anomaly_events
            if anomaly.detected_at >= cutoff_time
        ]
        
        return recent_anomalies
    
    def get_anomaly_summary(self, time_period: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """Get anomaly summary statistics"""
        cutoff_time = datetime.utcnow() - time_period
        
        recent_anomalies = [
            anomaly for anomaly in self.anomaly_events
            if anomaly.detected_at >= cutoff_time
        ]
        
        if not recent_anomalies:
            return {
                'period_hours': time_period.total_seconds() / 3600,
                'total_anomalies': 0,
                'by_severity': {},
                'by_method': {},
                'by_metric': {}
            }
        
        # Count by severity
        severity_counts = {}
        for anomaly in recent_anomalies:
            severity = anomaly.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by detection method
        method_counts = {}
        for anomaly in recent_anomalies:
            method = anomaly.detection_method.value
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Count by metric
        metric_counts = {}
        for anomaly in recent_anomalies:
            metric = anomaly.metric_name
            metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        return {
            'period_hours': time_period.total_seconds() / 3600,
            'total_anomalies': len(recent_anomalies),
            'by_severity': severity_counts,
            'by_method': method_counts,
            'by_metric': dict(sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'average_confidence': statistics.mean([a.confidence_score for a in recent_anomalies]),
            'most_recent': recent_anomalies[-1].detected_at.isoformat() if recent_anomalies else None
        }
    
    def shutdown(self):
        """Shutdown the anomaly detection engine"""
        self.is_running = False
        if hasattr(self, 'background_thread'):
            self.background_thread.join(timeout=10)
        logger.info("Anomaly detection engine shutdown")

def main():
    """Main function for real-time anomaly detection"""
    parser = argparse.ArgumentParser(description='Real-Time Anomaly Detection Engine')
    parser.add_argument('--operation', required=True, help='Operation type')
    parser.add_argument('--data-file', help='Input data file')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--config', help='Configuration file')
    parser.add_argument('--time-period', type=int, help='Time period in hours')
    parser.add_argument('--stream', action='store_true', help='Enable streaming mode')
    
    args = parser.parse_args()
    
    # Initialize anomaly detector
    detector = RealTimeAnomalyDetector(args.config)
    
    try:
        if args.operation == 'detect':
            # Load data
            if args.data_file:
                with open(args.data_file, 'r') as f:
                    data = json.load(f)
                
                # Convert to StreamingMetric objects
                metrics = []
                for item in data:
                    metric = StreamingMetric(
                        metric_id=item.get('metric_id', f"metric-{len(metrics)}"),
                        metric_name=item['metric_name'],
                        value=item['value'],
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        labels=item.get('labels', {}),
                        source=item.get('source', 'test'),
                        resource_id=item.get('resource_id', 'unknown')
                    )
                    metrics.append(metric)
                
                # Ingest metrics
                ingested = detector.ingest_metric_stream(metrics)
                logger.info(f"Ingested {ingested} metrics")
                
                # Wait for processing
                time.sleep(10)
                
                # Get results
                time_period = timedelta(hours=args.time_period) if args.time_period else timedelta(hours=1)
                recent_anomalies = detector.get_recent_anomalies(time_period)
                summary = detector.get_anomaly_summary(time_period)
                
                result = {
                    'ingested_metrics': ingested,
                    'recent_anomalies': [
                        {
                            'event_id': a.event_id,
                            'metric_name': a.metric_name,
                            'resource_id': a.resource_id,
                            'severity': a.severity.value,
                            'confidence': a.confidence_score,
                            'detected_at': a.detected_at.isoformat(),
                            'description': a.description,
                            'method': a.detection_method.value
                        }
                        for a in recent_anomalies
                    ],
                    'summary': summary
                }
                
                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(result, f, indent=2)
                
                print(json.dumps(result, indent=2))
            
            else:
                # Generate mock data
                metrics = []
                for i in range(100):
                    metric = StreamingMetric(
                        metric_id=f"metric-{i}",
                        metric_name=np.random.choice(['cpu_utilization', 'memory_utilization', 'response_time', 'error_rate']),
                        value=np.random.uniform(0, 100),
                        timestamp=datetime.utcnow() - timedelta(minutes=i),
                        labels={'env': 'production'},
                        source='test',
                        resource_id=f'resource-{i % 10}'
                    )
                    metrics.append(metric)
                
                # Ingest and process
                ingested = detector.ingest_metric_stream(metrics)
                time.sleep(5)
                
                # Get results
                recent_anomalies = detector.get_recent_anomalies(timedelta(hours=1))
                summary = detector.get_anomaly_summary(timedelta(hours=1))
                
                result = {
                    'ingested_metrics': ingested,
                    'recent_anomalies': len(recent_anomalies),
                    'summary': summary
                }
                
                print(json.dumps(result, indent=2))
        
        elif args.operation == 'summary':
            # Get anomaly summary
            time_period = timedelta(hours=args.time_period) if args.time_period else timedelta(hours=24)
            summary = detector.get_anomaly_summary(time_period)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(summary, f, indent=2)
            
            print(json.dumps(summary, indent=2))
        
        elif args.operation == 'stream' and args.stream:
            # Streaming mode
            logger.info("Starting streaming mode...")
            
            try:
                while True:
                    # Generate mock streaming data
                    metrics = []
                    for i in range(10):
                        metric = StreamingMetric(
                            metric_id=f"stream-{int(time.time())}-{i}",
                            metric_name=np.random.choice(['cpu_utilization', 'memory_utilization', 'response_time']),
                            value=np.random.uniform(0, 100),
                            timestamp=datetime.utcnow(),
                            labels={'env': 'production'},
                            source='stream',
                            resource_id=f'resource-{i}'
                        )
                        metrics.append(metric)
                    
                    # Ingest metrics
                    ingested = detector.ingest_metric_stream(metrics)
                    
                    # Get recent anomalies
                    recent = detector.get_recent_anomalies(timedelta(minutes=5))
                    
                    if recent:
                        logger.info(f"Detected {len(recent)} recent anomalies")
                        for anomaly in recent[-3:]:  # Show last 3
                            logger.info(f"  {anomaly.metric_name}: {anomaly.description}")
                    
                    time.sleep(30)  # Wait 30 seconds before next batch
                    
            except KeyboardInterrupt:
                logger.info("Streaming mode stopped by user")
        
        else:
            logger.error(f"Unknown operation: {args.operation}")
    
    finally:
        detector.shutdown()

if __name__ == "__main__":
    main()
