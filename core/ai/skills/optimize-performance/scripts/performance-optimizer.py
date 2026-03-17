#!/usr/bin/env python3
"""
Performance Optimizer Script

Multi-cloud automation for comprehensive performance optimization across AWS, Azure, GCP, and on-premise environments.
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
    SCALING = "scaling"
    RIGHT_SIZING = "right_sizing"
    CACHING = "caching"
    LOAD_BALANCING = "load_balancing"
    DATABASE_OPTIMIZATION = "database_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"
    APPLICATION_TUNING = "application_tuning"
    INFRASTRUCTURE_TUNING = "infrastructure_tuning"

class PerformanceMetric(Enum):
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    LATENCY = "latency"

class OptimizationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class PerformanceMetricData:
    metric_name: PerformanceMetric
    value: float
    unit: str
    timestamp: datetime
    resource_id: str
    resource_name: str
    provider: str
    environment: str
    metadata: Dict[str, Any]

@dataclass
class OptimizationRecommendation:
    recommendation_id: str
    title: str
    description: str
    optimization_type: OptimizationType
    priority: OptimizationPriority
    resource_id: str
    resource_name: str
    provider: str
    current_value: float
    target_value: float
    expected_improvement: float
    implementation_complexity: str
    estimated_cost_savings: Optional[float]
    estimated_performance_gain: float
    risk_level: str
    implementation_steps: List[str]
    rollback_plan: List[str]

@dataclass
class OptimizationResult:
    optimization_id: str
    provider: str
    environment: str
    optimized_at: datetime
    total_recommendations: int
    recommendations_by_priority: Dict[str, int]
    recommendations_by_type: Dict[str, int]
    total_cost_savings: float
    total_performance_gain: float
    implemented_recommendations: List[str]
    failed_recommendations: List[str]
    performance_baseline: Dict[str, float]
    performance_after: Dict[str, float]

class PerformanceOptimizer:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.metrics_history = []
        self.optimizations = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load performance optimizer configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'optimization_settings': {
                'enable_ml_optimization': True,
                'enable_cost_analysis': True,
                'enable_performance_prediction': True,
                'optimization_threshold': 0.2,
                'risk_tolerance': 'medium',
                'max_implementation_time_hours': 24,
                'require_approval_for_high_risk': True
            },
            'performance_thresholds': {
                'cpu_utilization_high': 80.0,
                'cpu_utilization_low': 20.0,
                'memory_utilization_high': 85.0,
                'memory_utilization_low': 30.0,
                'response_time_high': 1000.0,  # milliseconds
                'error_rate_high': 5.0,  # percentage
                'latency_high': 500.0,  # milliseconds
                'throughput_low': 100.0
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
    
    def collect_performance_metrics(self, providers: List[str], time_range_hours: int = 24) -> Dict[str, List[PerformanceMetricData]]:
        """Collect performance metrics from multiple providers"""
        logger.info(f"Collecting performance metrics from providers: {providers}")
        
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
                provider_metrics = handler.get_performance_metrics(time_range_hours)
                all_metrics[provider] = provider_metrics
                
                logger.info(f"Collected {len(provider_metrics)} metrics from {provider}")
                
            except Exception as e:
                logger.error(f"Failed to collect metrics from {provider}: {e}")
                all_metrics[provider] = []
        
        return all_metrics
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific performance handler"""
        from performance_optimizer_handler import get_performance_handler
        region = self.config['providers'][provider]['region']
        return get_performance_handler(provider, region)
    
    def analyze_performance(self, metrics: Dict[str, List[PerformanceMetricData]]) -> Dict[str, List[OptimizationRecommendation]]:
        """Analyze performance metrics and generate recommendations"""
        logger.info("Analyzing performance metrics")
        
        recommendations_by_provider = {}
        
        for provider, provider_metrics in metrics.items():
            try:
                # Analyze metrics for this provider
                provider_recommendations = self._analyze_provider_metrics(provider_metrics, provider)
                recommendations_by_provider[provider] = provider_recommendations
                
                logger.info(f"Generated {len(provider_recommendations)} recommendations for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to analyze metrics for {provider}: {e}")
                recommendations_by_provider[provider] = []
        
        return recommendations_by_provider
    
    def _analyze_provider_metrics(self, metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze metrics for a specific provider"""
        recommendations = []
        
        try:
            # Group metrics by resource
            metrics_by_resource = {}
            for metric in metrics:
                resource_id = metric.resource_id
                if resource_id not in metrics_by_resource:
                    metrics_by_resource[resource_id] = []
                metrics_by_resource[resource_id].append(metric)
            
            # Analyze each resource
            for resource_id, resource_metrics in metrics_by_resource.items():
                resource_recommendations = self._analyze_resource_performance(resource_metrics, provider)
                recommendations.extend(resource_recommendations)
            
            # Sort recommendations by priority and expected improvement
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(key=lambda x: (priority_order.get(x.priority.value, 4), -x.expected_performance_gain))
            
        except Exception as e:
            logger.error(f"Failed to analyze provider metrics: {e}")
        
        return recommendations
    
    def _analyze_resource_performance(self, metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze performance for a specific resource"""
        recommendations = []
        
        try:
            # Group metrics by type
            metrics_by_type = {}
            for metric in metrics:
                metric_type = metric.metric_name
                if metric_type not in metrics_by_type:
                    metrics_by_type[metric_type] = []
                metrics_by_type[metric_type].append(metric)
            
            # Analyze CPU utilization
            if PerformanceMetric.CPU_UTILIZATION in metrics_by_type:
                cpu_recommendations = self._analyze_cpu_utilization(metrics_by_type[PerformanceMetric.CPU_UTILIZATION], provider)
                recommendations.extend(cpu_recommendations)
            
            # Analyze memory utilization
            if PerformanceMetric.MEMORY_UTILIZATION in metrics_by_type:
                memory_recommendations = self._analyze_memory_utilization(metrics_by_type[PerformanceMetric.MEMORY_UTILIZATION], provider)
                recommendations.extend(memory_recommendations)
            
            # Analyze response time
            if PerformanceMetric.RESPONSE_TIME in metrics_by_type:
                response_time_recommendations = self._analyze_response_time(metrics_by_type[PerformanceMetric.RESPONSE_TIME], provider)
                recommendations.extend(response_time_recommendations)
            
            # Analyze error rate
            if PerformanceMetric.ERROR_RATE in metrics_by_type:
                error_rate_recommendations = self._analyze_error_rate(metrics_by_type[PerformanceMetric.ERROR_RATE], provider)
                recommendations.extend(error_rate_recommendations)
            
            # Analyze throughput
            if PerformanceMetric.THROUGHPUT in metrics_by_type:
                throughput_recommendations = self._analyze_throughput(metrics_by_type[PerformanceMetric.THROUGHPUT], provider)
                recommendations.extend(throughput_recommendations)
            
            # Analyze disk I/O
            if PerformanceMetric.DISK_IO in metrics_by_type:
                disk_io_recommendations = self._analyze_disk_io(metrics_by_type[PerformanceMetric.DISK_IO], provider)
                recommendations.extend(disk_io_recommendations)
            
            # Analyze network I/O
            if PerformanceMetric.NETWORK_IO in metrics_by_type:
                network_io_recommendations = self._analyze_network_io(metrics_by_type[PerformanceMetric.NETWORK_IO], provider)
                recommendations.extend(network_io_recommendations)
            
        except Exception as e:
            logger.error(f"Failed to analyze resource performance: {e}")
        
        return recommendations
    
    def _analyze_cpu_utilization(self, cpu_metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze CPU utilization metrics"""
        recommendations = []
        
        try:
            # Calculate average CPU utilization
            cpu_values = [metric.value for metric in cpu_metrics]
            avg_cpu = statistics.mean(cpu_values)
            max_cpu = max(cpu_values)
            
            thresholds = self.config['performance_thresholds']
            
            # High CPU utilization
            if avg_cpu > thresholds['cpu_utilization_high']:
                resource_id = cpu_metrics[0].resource_id
                resource_name = cpu_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"cpu-high-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="High CPU Utilization Detected",
                    description=f"Resource {resource_name} has average CPU utilization of {avg_cpu:.1f}%",
                    optimization_type=OptimizationType.SCALING,
                    priority=OptimizationPriority.HIGH if avg_cpu > 90 else OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_cpu,
                    target_value=thresholds['cpu_utilization_high'] - 10,
                    expected_improvement=15.0,
                    implementation_complexity="medium",
                    estimated_cost_savings=self._calculate_cpu_cost_savings(avg_cpu, provider),
                    estimated_performance_gain=20.0,
                    risk_level="low",
                    implementation_steps=[
                        "Scale up CPU resources (vertical scaling)",
                        "Add more instances (horizontal scaling)",
                        "Optimize application code for better CPU efficiency",
                        "Implement auto-scaling policies"
                    ],
                    rollback_plan=[
                        "Monitor performance after scaling",
                        "Scale back if performance degrades",
                        "Revert to original configuration if needed"
                    ]
                )
                recommendations.append(recommendation)
            
            # Low CPU utilization (potential for rightsizing)
            elif avg_cpu < thresholds['cpu_utilization_low']:
                resource_id = cpu_metrics[0].resource_id
                resource_name = cpu_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"cpu-low-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="Low CPU Utilization - Rightsizing Opportunity",
                    description=f"Resource {resource_name} has average CPU utilization of {avg_cpu:.1f}%",
                    optimization_type=OptimizationType.RIGHT_SIZING,
                    priority=OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_cpu,
                    target_value=thresholds['cpu_utilization_low'] + 10,
                    expected_improvement=25.0,
                    implementation_complexity="low",
                    estimated_cost_savings=self._calculate_cpu_cost_savings(avg_cpu, provider) * 0.3,
                    estimated_performance_gain=5.0,
                    risk_level="low",
                    implementation_steps=[
                        "Downsize CPU resources (vertical scaling)",
                        "Consolidate instances if possible",
                        "Implement auto-scaling with lower thresholds",
                        "Monitor performance after rightsizing"
                    ],
                    rollback_plan=[
                        "Scale up if performance issues occur",
                        "Monitor for increased response times",
                        "Revert to original configuration if needed"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Failed to analyze CPU utilization: {e}")
        
        return recommendations
    
    def _analyze_memory_utilization(self, memory_metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze memory utilization metrics"""
        recommendations = []
        
        try:
            memory_values = [metric.value for metric in memory_metrics]
            avg_memory = statistics.mean(memory_values)
            max_memory = max(memory_values)
            
            thresholds = self.config['performance_thresholds']
            
            # High memory utilization
            if avg_memory > thresholds['memory_utilization_high']:
                resource_id = memory_metrics[0].resource_id
                resource_name = memory_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"memory-high-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="High Memory Utilization Detected",
                    description=f"Resource {resource_name} has average memory utilization of {avg_memory:.1f}%",
                    optimization_type=OptimizationType.SCALING,
                    priority=OptimizationPriority.HIGH if avg_memory > 95 else OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_memory,
                    target_value=thresholds['memory_utilization_high'] - 10,
                    expected_improvement=18.0,
                    implementation_complexity="medium",
                    estimated_cost_savings=self._calculate_memory_cost_savings(avg_memory, provider),
                    estimated_performance_gain=25.0,
                    risk_level="low",
                    implementation_steps=[
                        "Scale up memory resources",
                        "Optimize application memory usage",
                        "Implement memory caching",
                        "Add more instances for load distribution"
                    ],
                    rollback_plan=[
                        "Monitor memory usage after scaling",
                        "Scale back if memory issues persist",
                        "Revert to original configuration"
                    ]
                )
                recommendations.append(recommendation)
            
            # Low memory utilization
            elif avg_memory < thresholds['memory_utilization_low']:
                resource_id = memory_metrics[0].resource_id
                resource_name = memory_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"memory-low-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="Low Memory Utilization - Rightsizing Opportunity",
                    description=f"Resource {resource_name} has average memory utilization of {avg_memory:.1f}%",
                    optimization_type=OptimizationType.RIGHT_SIZING,
                    priority=OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_memory,
                    target_value=thresholds['memory_utilization_low'] + 10,
                    expected_improvement=20.0,
                    implementation_complexity="low",
                    estimated_cost_savings=self._calculate_memory_cost_savings(avg_memory, provider) * 0.25,
                    estimated_performance_gain=5.0,
                    risk_level="low",
                    implementation_steps=[
                        "Downsize memory resources",
                        "Consolidate instances",
                        "Implement memory optimization",
                        "Monitor performance after rightsizing"
                    ],
                    rollback_plan=[
                        "Scale up if memory issues occur",
                        "Monitor for increased memory pressure",
                        "Revert to original configuration"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Failed to analyze memory utilization: {e}")
        
        return recommendations
    
    def _analyze_response_time(self, response_time_metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze response time metrics"""
        recommendations = []
        
        try:
            response_times = [metric.value for metric in response_time_metrics]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            thresholds = self.config['performance_thresholds']
            
            # High response time
            if avg_response_time > thresholds['response_time_high']:
                resource_id = response_time_metrics[0].resource_id
                resource_name = response_time_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"response-time-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="High Response Time Detected",
                    description=f"Resource {resource_name} has average response time of {avg_response_time:.1f}ms",
                    optimization_type=OptimizationType.APPLICATION_TUNING,
                    priority=OptimizationPriority.HIGH if avg_response_time > 2000 else OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_response_time,
                    target_value=thresholds['response_time_high'] * 0.7,
                    expected_improvement=30.0,
                    implementation_complexity="medium",
                    estimated_cost_savings=self._calculate_response_time_cost_savings(avg_response_time, provider),
                    estimated_performance_gain=35.0,
                    risk_level="medium",
                    implementation_steps=[
                        "Implement application caching",
                        "Optimize database queries",
                        "Add CDN or edge caching",
                        "Scale resources horizontally",
                        "Profile and optimize application code"
                    ],
                    rollback_plan=[
                        "Monitor response time after changes",
                        "Revert optimizations if performance degrades",
                        "Scale back resources if needed"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Failed to analyze response time: {e}")
        
        return recommendations
    
    def _analyze_error_rate(self, error_rate_metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze error rate metrics"""
        recommendations = []
        
        try:
            error_rates = [metric.value for metric in error_rate_metrics]
            avg_error_rate = statistics.mean(error_rates)
            
            thresholds = self.config['performance_thresholds']
            
            # High error rate
            if avg_error_rate > thresholds['error_rate_high']:
                resource_id = error_rate_metrics[0].resource_id
                resource_name = error_rate_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"error-rate-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="High Error Rate Detected",
                    description=f"Resource {resource_name} has average error rate of {avg_error_rate:.1f}%",
                    optimization_type=OptimizationType.APPLICATION_TUNING,
                    priority=OptimizationPriority.CRITICAL if avg_error_rate > 10 else OptimizationPriority.HIGH,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_error_rate,
                    target_value=thresholds['error_rate_high'] * 0.5,
                    expected_improvement=40.0,
                    implementation_complexity="high",
                    estimated_cost_savings=self._calculate_error_rate_cost_savings(avg_error_rate, provider),
                    estimated_performance_gain=50.0,
                    risk_level="high",
                    implementation_steps=[
                        "Investigate root cause of errors",
                        "Implement better error handling",
                        "Add circuit breakers",
                        "Improve monitoring and alerting",
                        "Scale resources if needed"
                    ],
                    rollback_plan=[
                        "Monitor error rate after fixes",
                        "Revert changes if errors increase",
                        "Implement emergency rollback procedures"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Failed to analyze error rate: {e}")
        
        return recommendations
    
    def _analyze_throughput(self, throughput_metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze throughput metrics"""
        recommendations = []
        
        try:
            throughput_values = [metric.value for metric in throughput_metrics]
            avg_throughput = statistics.mean(throughput_values)
            
            thresholds = self.config['performance_thresholds']
            
            # Low throughput
            if avg_throughput < thresholds['throughput_low']:
                resource_id = throughput_metrics[0].resource_id
                resource_name = throughput_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"throughput-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="Low Throughput Detected",
                    description=f"Resource {resource_name} has average throughput of {avg_throughput:.1f} requests/second",
                    optimization_type=OptimizationType.SCALING,
                    priority=OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_throughput,
                    target_value=thresholds['throughput_low'] * 2,
                    expected_improvement=25.0,
                    implementation_complexity="medium",
                    estimated_cost_savings=self._calculate_throughput_cost_savings(avg_throughput, provider),
                    estimated_performance_gain=30.0,
                    risk_level="medium",
                    implementation_steps=[
                        "Scale resources horizontally",
                        "Optimize application performance",
                        "Implement load balancing",
                        "Add caching layers",
                        "Optimize database performance"
                    ],
                    rollback_plan=[
                        "Monitor throughput after scaling",
                        "Scale back if issues occur",
                        "Revert to original configuration"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Failed to analyze throughput: {e}")
        
        return recommendations
    
    def _analyze_disk_io(self, disk_io_metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze disk I/O metrics"""
        recommendations = []
        
        try:
            # Simplified disk I/O analysis
            disk_io_values = [metric.value for metric in disk_io_metrics]
            avg_disk_io = statistics.mean(disk_io_values)
            
            # High disk I/O (simplified threshold)
            if avg_disk_io > 80:  # IOPS or similar metric
                resource_id = disk_io_metrics[0].resource_id
                resource_name = disk_io_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"disk-io-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="High Disk I/O Detected",
                    description=f"Resource {resource_name} has high disk I/O activity",
                    optimization_type=OptimizationType.INFRASTRUCTURE_TUNING,
                    priority=OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_disk_io,
                    target_value=60.0,
                    expected_improvement=20.0,
                    implementation_complexity="medium",
                    estimated_cost_savings=self._calculate_disk_io_cost_savings(avg_disk_io, provider),
                    estimated_performance_gain=25.0,
                    risk_level="medium",
                    implementation_steps=[
                        "Upgrade to faster storage (SSD)",
                        "Implement disk optimization",
                        "Add caching layers",
                        "Optimize database storage",
                        "Implement storage tiering"
                    ],
                    rollback_plan=[
                        "Monitor disk performance after changes",
                        "Revert storage upgrades if issues occur",
                        "Restore original configuration"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Failed to analyze disk I/O: {e}")
        
        return recommendations
    
    def _analyze_network_io(self, network_io_metrics: List[PerformanceMetricData], provider: str) -> List[OptimizationRecommendation]:
        """Analyze network I/O metrics"""
        recommendations = []
        
        try:
            # Simplified network I/O analysis
            network_io_values = [metric.value for metric in network_io_metrics]
            avg_network_io = statistics.mean(network_io_values)
            
            # High network I/O (simplified threshold)
            if avg_network_io > 85:  # Network utilization percentage
                resource_id = network_io_metrics[0].resource_id
                resource_name = network_io_metrics[0].resource_name
                
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"network-io-{provider}-{resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    title="High Network I/O Detected",
                    description=f"Resource {resource_name} has high network I/O utilization",
                    optimization_type=OptimizationType.NETWORK_OPTIMIZATION,
                    priority=OptimizationPriority.MEDIUM,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    provider=provider,
                    current_value=avg_network_io,
                    target_value=70.0,
                    expected_improvement=15.0,
                    implementation_complexity="medium",
                    estimated_cost_savings=self._calculate_network_io_cost_savings(avg_network_io, provider),
                    estimated_performance_gain=20.0,
                    risk_level="medium",
                    implementation_steps=[
                        "Upgrade network bandwidth",
                        "Implement network optimization",
                        "Add load balancing",
                        "Optimize network protocols",
                        "Implement compression"
                    ],
                    rollback_plan=[
                        "Monitor network performance after changes",
                        "Revert network upgrades if issues occur",
                        "Restore original configuration"
                    ]
                )
                recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Failed to analyze network I/O: {e}")
        
        return recommendations
    
    def _calculate_cpu_cost_savings(self, cpu_utilization: float, provider: str) -> float:
        """Calculate potential cost savings from CPU optimization"""
        # Simplified cost calculation
        base_cost = 100.0  # Base monthly cost
        if provider == 'aws':
            cost_per_cpu = 50.0
        elif provider == 'azure':
            cost_per_cpu = 45.0
        elif provider == 'gcp':
            cost_per_cpu = 48.0
        else:
            cost_per_cpu = 40.0
        
        # Calculate savings based on optimization potential
        if cpu_utilization > 80:
            # Scaling up costs more
            return -(cost_per_cpu * 0.5)
        elif cpu_utilization < 20:
            # Rightsizing saves money
            return cost_per_cpu * 0.3
        else:
            return cost_per_cpu * 0.1
    
    def _calculate_memory_cost_savings(self, memory_utilization: float, provider: str) -> float:
        """Calculate potential cost savings from memory optimization"""
        # Similar to CPU calculation
        base_cost = 80.0
        if provider == 'aws':
            cost_per_gb = 10.0
        elif provider == 'azure':
            cost_per_gb = 9.0
        elif provider == 'gcp':
            cost_per_gb = 9.5
        else:
            cost_per_gb = 8.0
        
        if memory_utilization > 85:
            return -(cost_per_gb * 0.4)
        elif memory_utilization < 30:
            return cost_per_gb * 0.25
        else:
            return cost_per_gb * 0.05
    
    def _calculate_response_time_cost_savings(self, response_time: float, provider: str) -> float:
        """Calculate cost savings from response time optimization"""
        # Response time optimization typically improves efficiency
        base_cost = 120.0
        improvement_factor = min(response_time / 1000.0, 2.0)  # Cap at 2x
        return base_cost * 0.1 * improvement_factor
    
    def _calculate_error_rate_cost_savings(self, error_rate: float, provider: str) -> float:
        """Calculate cost savings from error rate reduction"""
        # Error reduction has significant business value
        base_cost = 200.0
        business_impact = min(error_rate / 10.0, 5.0)  # Cap at 5x
        return base_cost * 0.2 * business_impact
    
    def _calculate_throughput_cost_savings(self, throughput: float, provider: str) -> float:
        """Calculate cost savings from throughput optimization"""
        # Higher throughput means better resource utilization
        base_cost = 100.0
        efficiency_gain = min(throughput / 1000.0, 1.5)  # Cap at 1.5x
        return base_cost * 0.15 * efficiency_gain
    
    def _calculate_disk_io_cost_savings(self, disk_io: float, provider: str) -> float:
        """Calculate cost savings from disk I/O optimization"""
        base_cost = 80.0
        if disk_io > 80:
            return -(base_cost * 0.3)  # Cost of upgrading storage
        else:
            return base_cost * 0.1
    
    def _calculate_network_io_cost_savings(self, network_io: float, provider: str) -> float:
        """Calculate cost savings from network I/O optimization"""
        base_cost = 60.0
        if network_io > 85:
            return -(base_cost * 0.25)  # Cost of upgrading network
        else:
            return base_cost * 0.08
    
    def implement_optimizations(self, recommendations: List[OptimizationRecommendation], 
                                dry_run: bool = False) -> OptimizationResult:
        """Implement performance optimizations"""
        logger.info(f"Implementing {len(recommendations)} optimizations")
        
        # Group recommendations by provider
        recommendations_by_provider = {}
        for rec in recommendations:
            if rec.provider not in recommendations_by_provider:
                recommendations_by_provider[rec.provider] = []
            recommendations_by_provider[rec.provider].append(rec)
        
        # Implement optimizations for each provider
        implemented = []
        failed = []
        total_cost_savings = 0.0
        total_performance_gain = 0.0
        
        performance_baseline = {}
        performance_after = {}
        
        for provider, provider_recommendations in recommendations_by_provider.items():
            try:
                handler = self._get_provider_handler(provider)
                if not handler.initialize_client():
                    raise RuntimeError(f"Failed to initialize {provider} handler")
                
                for rec in provider_recommendations:
                    try:
                        # Check if high-risk optimization requires approval
                        if rec.risk_level == 'high' and self.config['optimization_settings']['require_approval_for_high_risk']:
                            logger.warning(f"Skipping high-risk optimization {rec.recommendation_id} - requires approval")
                            continue
                        
                        if dry_run:
                            logger.info(f"DRY RUN: Would implement optimization {rec.recommendation_id}")
                            implemented.append(rec.recommendation_id)
                            total_cost_savings += rec.estimated_cost_savings or 0.0
                            total_performance_gain += rec.estimated_performance_gain
                        else:
                            # Implement optimization
                            success = self._implement_single_optimization(handler, rec)
                            if success:
                                implemented.append(rec.recommendation_id)
                                total_cost_savings += rec.estimated_cost_savings or 0.0
                                total_performance_gain += rec.estimated_performance_gain
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
            total_recommendations=len(recommendations),
            recommendations_by_priority=self._count_recommendations_by_priority(recommendations),
            recommendations_by_type=self._count_recommendations_by_type(recommendations),
            total_cost_savings=total_cost_savings,
            total_performance_gain=total_performance_gain,
            implemented_recommendations=implemented,
            failed_recommendations=failed,
            performance_baseline=performance_baseline,
            performance_after=performance_after
        )
        
        # Store optimization history
        self.optimizations.append({
            'optimization_id': result.optimization_id,
            'implemented_at': result.optimized_at,
            'total_recommendations': result.total_recommendations,
            'implemented_count': len(implemented),
            'failed_count': len(failed),
            'total_cost_savings': total_cost_savings,
            'total_performance_gain': total_performance_gain
        })
        
        return result
    
    def _implement_single_optimization(self, handler, recommendation: OptimizationRecommendation) -> bool:
        """Implement a single optimization"""
        try:
            # Implementation based on optimization type
            if recommendation.optimization_type == OptimizationType.SCALING:
                return handler.implement_scaling_optimization(recommendation)
            elif recommendation.optimization_type == OptimizationType.RIGHT_SIZING:
                return handler.implement_rightsizing_optimization(recommendation)
            elif recommendation.optimization_type == OptimizationType.CACHING:
                return handler.implement_caching_optimization(recommendation)
            elif recommendation.optimization_type == OptimizationType.LOAD_BALANCING:
                return handler.implement_load_balancing_optimization(recommendation)
            elif recommendation.optimization_type == OptimizationType.DATABASE_OPTIMIZATION:
                return handler.implement_database_optimization(recommendation)
            elif recommendation.optimization_type == OptimizationType.NETWORK_OPTIMIZATION:
                return handler.implement_network_optimization(recommendation)
            elif recommendation.optimization_type == OptimizationType.APPLICATION_TUNING:
                return handler.implement_application_tuning_optimization(recommendation)
            elif recommendation.optimization_type == OptimizationType.INFRASTRUCTURE_TUNING:
                return handler.implement_infrastructure_tuning_optimization(recommendation)
            else:
                logger.warning(f"Unsupported optimization type: {recommendation.optimization_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to implement optimization {recommendation.recommendation_id}: {e}")
            return False
    
    def _count_recommendations_by_priority(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, int]:
        """Count recommendations by priority"""
        counts = {}
        for rec in recommendations:
            priority = rec.priority.value
            counts[priority] = counts.get(priority, 0) + 1
        return counts
    
    def _count_recommendations_by_type(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, int]:
        """Count recommendations by type"""
        counts = {}
        for rec in recommendations:
            opt_type = rec.optimization_type.value
            counts[opt_type] = counts.get(opt_type, 0) + 1
        return counts
    
    def generate_optimization_report(self, analysis_results: Dict[str, List[OptimizationRecommendation]], 
                                     optimization_result: Optional[OptimizationResult] = None,
                                     output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        logger.info("Generating optimization report")
        
        # Calculate statistics
        total_recommendations = sum(len(recs) for recs in analysis_results.values())
        total_cost_savings = sum(rec.estimated_cost_savings or 0 for recs in [r for recs_list in analysis_results.values() for r in recs_list])
        total_performance_gain = sum(rec.estimated_performance_gain for recs in [r for recs_list in analysis_results.values() for r in recs_list])
        
        # Provider comparisons
        provider_comparison = {}
        for provider, recommendations in analysis_results.items():
            provider_comparison[provider] = {
                'recommendations_count': len(recommendations),
                'cost_savings': sum(rec.estimated_cost_savings or 0 for rec in recommendations),
                'performance_gain': sum(rec.estimated_performance_gain for rec in recommendations),
                'critical_count': len([r for r in recommendations if r.priority == OptimizationPriority.CRITICAL]),
                'high_count': len([r for r in recommendations if r.priority == OptimizationPriority.HIGH])
            }
        
        # Top recommendations
        all_recommendations = []
        for recommendations in analysis_results.values():
            all_recommendations.extend(recommendations)
        
        # Sort by expected performance gain and priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        top_recommendations = sorted(all_recommendations, 
                                   key=lambda x: (priority_order.get(x.priority.value, 4), -x.expected_performance_gain))[:20]
        
        # Recommendations by type
        type_distribution = {}
        for recommendations in analysis_results.values():
            for rec in recommendations:
                opt_type = rec.optimization_type.value
                type_distribution[opt_type] = type_distribution.get(opt_type, 0) + 1
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_providers_analyzed': len(analysis_results),
                'total_recommendations': total_recommendations,
                'total_potential_cost_savings': total_cost_savings,
                'total_potential_performance_gain': total_performance_gain,
                'critical_recommendations': len([r for r in all_recommendations if r.priority == OptimizationPriority.CRITICAL]),
                'high_recommendations': len([r for r in all_recommendations if r.priority == OptimizationPriority.HIGH])
            },
            'provider_comparison': provider_comparison,
            'type_distribution': type_distribution,
            'top_recommendations': [
                {
                    'recommendation_id': rec.recommendation_id,
                    'title': rec.title,
                    'priority': rec.priority.value,
                    'type': rec.optimization_type.value,
                    'resource_name': rec.resource_name,
                    'current_value': rec.current_value,
                    'target_value': rec.target_value,
                    'expected_improvement': rec.expected_improvement,
                    'cost_savings': rec.estimated_cost_savings,
                    'performance_gain': rec.estimated_performance_gain,
                    'risk_level': rec.risk_level
                }
                for rec in top_recommendations
            ],
            'implementation_results': {
                'optimization_id': optimization_result.optimization_id,
                'implemented_at': optimization_result.optimized_at.isoformat(),
                'total_implemented': len(optimization_result.implemented_recommendations),
                'total_failed': len(optimization_result.failed_recommendations),
                'actual_cost_savings': optimization_result.total_cost_savings,
                'actual_performance_gain': optimization_result.total_performance_gain
            } if optimization_result else None,
            'detailed_results': {
                provider: [
                    {
                        'recommendation_id': rec.recommendation_id,
                        'title': rec.title,
                        'priority': rec.priority.value,
                        'type': rec.optimization_type.value,
                        'resource_name': rec.resource_name,
                        'current_value': rec.current_value,
                        'target_value': rec.target_value,
                        'expected_improvement': rec.expected_improvement,
                        'cost_savings': rec.estimated_cost_savings,
                        'performance_gain': rec.estimated_performance_gain,
                        'risk_level': rec.risk_level,
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
            logger.info(f"Optimization report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Performance Optimizer")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--action", choices=['analyze', 'optimize', 'report'], 
                       default='analyze', help="Action to perform")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--time-range", type=int, default=24, help="Time range in hours for metrics")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode for optimization")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize performance optimizer
    optimizer = PerformanceOptimizer(args.config)
    
    try:
        if args.action == 'analyze':
            # Collect metrics
            metrics = optimizer.collect_performance_metrics(args.providers, args.time_range)
            
            # Analyze performance
            recommendations = optimizer.analyze_performance(metrics)
            
            print(f"\nPerformance Analysis Results:")
            for provider, provider_recommendations in recommendations.items():
                print(f"\n{provider.upper()}:")
                print(f"  Recommendations: {len(provider_recommendations)}")
                
                # Count by priority
                priority_counts = {}
                for rec in provider_recommendations:
                    priority = rec.priority.value
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                print(f"  By Priority: {priority_counts}")
                
                # Count by type
                type_counts = {}
                for rec in provider_recommendations:
                    opt_type = rec.optimization_type.value
                    type_counts[opt_type] = type_counts.get(opt_type, 0) + 1
                
                print(f"  By Type: {type_counts}")
                
                # Show top 3 recommendations
                top_recs = sorted(provider_recommendations, 
                                 key=lambda x: (x.priority.value, -x.expected_performance_gain))[:3]
                print(f"  Top Recommendations:")
                for i, rec in enumerate(top_recs, 1):
                    print(f"    {i}. {rec.title} (Priority: {rec.priority.value}, Gain: {rec.expected_performance_gain:.1f}%)")
        
        elif args.action == 'optimize':
            # First analyze to get recommendations
            metrics = optimizer.collect_performance_metrics(args.providers, args.time_range)
            recommendations = optimizer.analyze_performance(metrics)
            
            # Flatten all recommendations
            all_recommendations = []
            for provider_recommendations in recommendations.values():
                all_recommendations.extend(provider_recommendations)
            
            # Implement optimizations
            result = optimizer.implement_optimizations(all_recommendations, args.dry_run)
            
            print(f"\nOptimization Results:")
            print(f"Total Recommendations: {result.total_recommendations}")
            print(f"Implemented: {len(result.implemented_recommendations)}")
            print(f"Failed: {len(result.failed_recommendations)}")
            print(f"Total Cost Savings: ${result.total_cost_savings:.2f}")
            print(f"Total Performance Gain: {result.total_performance_gain:.1f}%")
            
            if args.dry_run:
                print("DRY RUN MODE - No actual optimizations performed")
        
        elif args.action == 'report':
            # Analyze first
            metrics = optimizer.collect_performance_metrics(args.providers, args.time_range)
            recommendations = optimizer.analyze_performance(metrics)
            
            # Generate report
            report = optimizer.generate_optimization_report(recommendations, output_file=args.output)
            
            summary = report['summary']
            print(f"\nPerformance Optimization Report:")
            print(f"Providers Analyzed: {summary['total_providers_analyzed']}")
            print(f"Total Recommendations: {summary['total_recommendations']}")
            print(f"Potential Cost Savings: ${summary['total_potential_cost_savings']:.2f}")
            print(f"Potential Performance Gain: {summary['total_potential_performance_gain']:.1f}%")
            print(f"Critical Recommendations: {summary['critical_recommendations']}")
            print(f"High Priority Recommendations: {summary['high_recommendations']}")
            
            print(f"\nProvider Comparison:")
            for provider, stats in report['provider_comparison'].items():
                print(f"  {provider}: {stats['recommendations_count']} recommendations, ${stats['cost_savings']:.2f} savings")
            
            print(f"\nRecommendation Types:")
            for opt_type, count in report['type_distribution'].items():
                print(f"  {opt_type}: {count}")
            
            print(f"\nTop Recommendations:")
            for rec in report['top_recommendations'][:5]:
                print(f"  - {rec['title']} (Priority: {rec['priority']}, Gain: {rec['performance_gain']:.1f}%)")
            
            if args.output:
                print(f"\nReport saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Performance optimization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
