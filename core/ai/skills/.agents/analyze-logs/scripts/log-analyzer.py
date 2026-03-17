#!/usr/bin/env python3
"""
Log Analyzer Script

Multi-cloud automation for comprehensive log analysis and pattern detection across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
import re
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

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogPattern(Enum):
    ERROR_PATTERN = "error_pattern"
    SECURITY_BREACH = "security_breach"
    PERFORMANCE_ISSUE = "performance_issue"
    AUTHENTICATION_FAILURE = "authentication_failure"
    DATABASE_ISSUE = "database_issue"
    NETWORK_ISSUE = "network_issue"
    APPLICATION_CRASH = "application_crash"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    provider: str
    resource_id: str
    resource_name: str
    environment: str
    metadata: Dict[str, Any]

@dataclass
class LogPattern:
    pattern_id: str
    pattern_name: str
    description: str
    pattern_type: LogPattern
    regex_pattern: str
    severity: str
    category: str
    enabled: bool
    false_positive_threshold: float

@dataclass
class LogAnalysisResult:
    analysis_id: str
    provider: str
    environment: str
    analyzed_at: datetime
    total_logs: int
    logs_by_level: Dict[str, int]
    patterns_found: List[Dict[str, Any]]
    anomalies_detected: List[Dict[str, Any]]
    security_events: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    recommendations: List[str]
    trend_analysis: Dict[str, Any]

class LogAnalyzer:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.patterns = {}
        self.analysis_history = []
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load log analyzer configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'analysis_settings': {
                'enable_ml_analysis': True,
                'enable_anomaly_detection': True,
                'enable_pattern_matching': True,
                'enable_correlation_analysis': True,
                'time_window_hours': 24,
                'max_logs_per_analysis': 100000,
                'false_positive_threshold': 0.1
            },
            'pattern_matching': {
                'enable_regex_patterns': True,
                'enable_ml_patterns': True,
                'enable_custom_patterns': True,
                'pattern_confidence_threshold': 0.7,
                'max_pattern_matches': 1000
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
    
    def load_patterns(self, patterns_file: Optional[str] = None) -> Dict[str, LogPattern]:
        """Load log analysis patterns"""
        logger.info("Loading log analysis patterns")
        
        # Default patterns
        default_patterns = {
            'error-exception': LogPattern(
                pattern_id='error-exception',
                pattern_name='Error/Exception Pattern',
                description='Detects error messages and exceptions in logs',
                pattern_type=LogPattern.ERROR_PATTERN,
                regex_pattern=r'(?i)(error|exception|failed|failure|fatal)',
                severity='high',
                category='application',
                enabled=True,
                false_positive_threshold=0.1
            ),
            'security-breach': LogPattern(
                pattern_id='security-breach',
                pattern_name='Security Breach Pattern',
                description='Detects potential security breaches',
                pattern_type=LogPattern.SECURITY_BREACH,
                regex_pattern=r'(?i)(unauthorized|forbidden|access denied|security breach|intrusion|attack|malicious)',
                severity='critical',
                category='security',
                enabled=True,
                false_positive_threshold=0.05
            ),
            'auth-failure': LogPattern(
                pattern_id='auth-failure',
                pattern_name='Authentication Failure Pattern',
                description='Detects authentication failures',
                pattern_type=LogPattern.AUTHENTICATION_FAILURE,
                regex_pattern=r'(?i)(authentication failed|login failed|invalid credentials|access denied|unauthorized)',
                severity='medium',
                category='security',
                enabled=True,
                false_positive_threshold=0.2
            ),
            'performance-issue': LogPattern(
                pattern_id='performance-issue',
                pattern_name='Performance Issue Pattern',
                description='Detects performance-related issues',
                pattern_type=LogPattern.PERFORMANCE_ISSUE,
                regex_pattern=r'(?i)(slow|timeout|performance|latency|bottleneck|degraded)',
                severity='medium',
                category='performance',
                enabled=True,
                false_positive_threshold=0.15
            ),
            'database-issue': LogPattern(
                pattern_id='database-issue',
                pattern_name='Database Issue Pattern',
                description='Detects database-related issues',
                pattern_type=LogPattern.DATABASE_ISSUE,
                regex_pattern=r'(?i)(database|connection|query|deadlock|lock|timeout|sql)',
                severity='medium',
                category='database',
                enabled=True,
                false_positive_threshold=0.1
            ),
            'network-issue': LogPattern(
                pattern_id='network-issue',
                pattern_name='Network Issue Pattern',
                description='Detects network-related issues',
                pattern_type=LogPattern.NETWORK_ISSUE,
                regex_pattern=r'(?i)(network|connection|socket|timeout|unreachable|refused)',
                severity='medium',
                category='network',
                enabled=True,
                false_positive_threshold=0.1
            ),
            'application-crash': LogPattern(
                pattern_id='application-crash',
                pattern_name='Application Crash Pattern',
                description='Detects application crashes',
                pattern_type=LogPattern.APPLICATION_CRASH,
                regex_pattern=r'(?i)(crash|segfault|abort|terminated|killed|panic)',
                severity='critical',
                category='application',
                enabled=True,
                false_positive_threshold=0.05
            ),
            'resource-exhaustion': LogPattern(
                pattern_id='resource-exhaustion',
                pattern_name='Resource Exhaustion Pattern',
                description='Detects resource exhaustion issues',
                pattern_type=LogPattern.RESOURCE_EXHAUSTION,
                regex_pattern=r'(?i)(memory|disk|cpu|space|exhausted|out of|quota|limit)',
                severity='high',
                category='infrastructure',
                enabled=True,
                false_positive_threshold=0.1
            )
        }
        
        # Load custom patterns from file if provided
        if patterns_file:
            try:
                with open(patterns_file, 'r') as f:
                    custom_patterns = json.load(f)
                
                for pattern_id, pattern_data in custom_patterns.items():
                    pattern = LogPattern(
                        pattern_id=pattern_id,
                        pattern_name=pattern_data['pattern_name'],
                        description=pattern_data['description'],
                        pattern_type=LogPattern(pattern_data['pattern_type']),
                        regex_pattern=pattern_data['regex_pattern'],
                        severity=pattern_data['severity'],
                        category=pattern_data['category'],
                        enabled=pattern_data.get('enabled', True),
                        false_positive_threshold=pattern_data.get('false_positive_threshold', 0.1)
                    )
                    default_patterns[pattern_id] = pattern
                    
            except Exception as e:
                logger.warning(f"Failed to load custom patterns: {e}")
        
        self.patterns = default_patterns
        logger.info(f"Loaded {len(self.patterns)} log analysis patterns")
        
        return self.patterns
    
    def analyze_logs(self, providers: List[str], environment: str = 'production') -> Dict[str, LogAnalysisResult]:
        """Perform comprehensive log analysis"""
        logger.info(f"Starting log analysis for providers: {providers}")
        
        analysis_results = {}
        
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
                
                # Collect logs
                logs = self._collect_logs(handler, provider, environment)
                
                # Analyze logs
                result = self._analyze_provider_logs(logs, provider, environment)
                analysis_results[provider] = result
                
                logger.info(f"Log analysis completed for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to analyze logs for {provider}: {e}")
                # Create a failed result
                result = LogAnalysisResult(
                    analysis_id=f"failed-{provider}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    provider=provider,
                    environment=environment,
                    analyzed_at=datetime.utcnow(),
                    total_logs=0,
                    logs_by_level={},
                    patterns_found=[],
                    anomalies_detected=[],
                    security_events=[],
                    performance_issues=[],
                    recommendations=[f"Log analysis failed: {str(e)}"],
                    trend_analysis={}
                )
                analysis_results[provider] = result
        
        return analysis_results
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific log handler"""
        from log_analyzer_handler import get_log_handler
        region = self.config['providers'][provider]['region']
        return get_log_handler(provider, region)
    
    def _collect_logs(self, handler, provider: str, environment: str) -> List[LogEntry]:
        """Collect logs from provider"""
        logger.info(f"Collecting logs from {provider}")
        
        try:
            time_window_hours = self.config['analysis_settings']['time_window_hours']
            logs = handler.get_logs(time_window_hours, environment)
            
            # Limit logs if necessary
            max_logs = self.config['analysis_settings']['max_logs_per_analysis']
            if len(logs) > max_logs:
                logs = logs[:max_logs]
                logger.info(f"Limited logs to {max_logs} for analysis")
            
            logger.info(f"Collected {len(logs)} logs from {provider}")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to collect logs from {provider}: {e}")
            return []
    
    def _analyze_provider_logs(self, logs: List[LogEntry], provider: str, environment: str) -> LogAnalysisResult:
        """Analyze logs for a specific provider"""
        logger.info(f"Analyzing {len(logs)} logs for {provider}")
        
        # Calculate basic statistics
        total_logs = len(logs)
        logs_by_level = self._group_logs_by_level(logs)
        
        # Pattern matching
        patterns_found = []
        if self.config['analysis_settings']['enable_pattern_matching']:
            patterns_found = self._match_patterns(logs)
        
        # Anomaly detection
        anomalies_detected = []
        if self.config['analysis_settings']['enable_anomaly_detection']:
            anomalies_detected = self._detect_anomalies(logs)
        
        # Security event detection
        security_events = []
        security_events = self._detect_security_events(logs)
        
        # Performance issue detection
        performance_issues = []
        performance_issues = self._detect_performance_issues(logs)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(logs, patterns_found, security_events, performance_issues)
        
        # Generate trend analysis
        trend_analysis = self._generate_trend_analysis(logs)
        
        # Create analysis result
        result = LogAnalysisResult(
            analysis_id=f"analysis-{provider}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            provider=provider,
            environment=environment,
            analyzed_at=datetime.utcnow(),
            total_logs=total_logs,
            logs_by_level=logs_by_level,
            patterns_found=patterns_found,
            anomalies_detected=anomalies_detected,
            security_events=security_events,
            performance_issues=performance_issues,
            recommendations=recommendations,
            trend_analysis=trend_analysis
        )
        
        # Store analysis history
        self.analysis_history.append({
            'provider': provider,
            'environment': environment,
            'analysis_id': result.analysis_id,
            'analyzed_at': result.analyzed_at,
            'total_logs': total_logs,
            'patterns_found': len(patterns_found),
            'security_events': len(security_events),
            'performance_issues': len(performance_issues)
        })
        
        return result
    
    def _group_logs_by_level(self, logs: List[LogEntry]) -> Dict[str, int]:
        """Group logs by level"""
        level_counts = {}
        
        for log in logs:
            level = log.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return level_counts
    
    def _match_patterns(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Match patterns against logs"""
        logger.info("Matching patterns against logs")
        
        pattern_matches = []
        
        for pattern in self.patterns.values():
            if not pattern.enabled:
                continue
            
            try:
                regex = re.compile(pattern.regex_pattern, re.IGNORECASE)
                matches = []
                
                for log in logs:
                    if regex.search(log.message):
                        matches.append({
                            'timestamp': log.timestamp.isoformat(),
                            'level': log.level.value,
                            'message': log.message,
                            'source': log.source,
                            'resource_id': log.resource_id,
                            'resource_name': log.resource_name
                        })
                
                if matches:
                    # Filter false positives
                    filtered_matches = self._filter_false_positives(matches, pattern)
                    
                    if filtered_matches:
                        pattern_matches.append({
                            'pattern_id': pattern.pattern_id,
                            'pattern_name': pattern.pattern_name,
                            'pattern_type': pattern.pattern_type.value,
                            'severity': pattern.severity,
                            'category': pattern.category,
                            'match_count': len(filtered_matches),
                            'matches': filtered_matches[:10],  # Limit to top 10 matches
                            'confidence': self._calculate_pattern_confidence(filtered_matches, pattern)
                        })
                
            except Exception as e:
                logger.error(f"Failed to match pattern {pattern.pattern_id}: {e}")
        
        # Sort by confidence and severity
        pattern_matches.sort(key=lambda x: (x['confidence'], x['severity']), reverse=True)
        
        return pattern_matches
    
    def _filter_false_positives(self, matches: List[Dict[str, Any]], pattern: LogPattern) -> List[Dict[str, Any]]:
        """Filter false positives from pattern matches"""
        try:
            # Simple false positive filtering based on message content
            filtered_matches = []
            
            for match in matches:
                message = match['message'].lower()
                
                # Common false positive indicators
                false_positive_indicators = [
                    'test', 'debug', 'demo', 'example', 'sample',
                    'expected', 'simulated', 'mock', 'placeholder'
                ]
                
                is_false_positive = any(indicator in message for indicator in false_positive_indicators)
                
                if not is_false_positive:
                    filtered_matches.append(match)
            
            # Apply threshold
            threshold = pattern.false_positive_threshold
            if len(filtered_matches) > len(matches) * (1 - threshold):
                # Too many false positives, return empty list
                return []
            
            return filtered_matches
            
        except Exception as e:
            logger.error(f"Failed to filter false positives: {e}")
            return matches
    
    def _calculate_pattern_confidence(self, matches: List[Dict[str, Any]], pattern: LogPattern) -> float:
        """Calculate confidence score for pattern matches"""
        try:
            # Base confidence based on match count
            base_confidence = min(len(matches) / 10.0, 1.0)  # Normalize to 0-1
            
            # Adjust based on pattern severity
            severity_weights = {
                'critical': 1.0,
                'high': 0.9,
                'medium': 0.8,
                'low': 0.7,
                'info': 0.6
            }
            
            severity_weight = severity_weights.get(pattern.severity, 0.8)
            
            # Calculate final confidence
            confidence = base_confidence * severity_weight
            
            return confidence
            
        except Exception as e:
            logger.error(f"Failed to calculate pattern confidence: {e}")
            return 0.5
    
    def _detect_anomalies(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect anomalies in log patterns"""
        logger.info("Detecting anomalies in log patterns")
        
        anomalies = []
        
        try:
            # Time-based anomaly detection
            time_anomalies = self._detect_time_anomalies(logs)
            anomalies.extend(time_anomalies)
            
            # Frequency-based anomaly detection
            frequency_anomalies = self._detect_frequency_anomalies(logs)
            anomalies.extend(frequency_anomalies)
            
            # Content-based anomaly detection
            content_anomalies = self._detect_content_anomalies(logs)
            anomalies.extend(content_anomalies)
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
        
        return anomalies
    
    def _detect_time_anomalies(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect time-based anomalies"""
        anomalies = []
        
        try:
            # Group logs by hour
            hourly_counts = {}
            for log in logs:
                hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            
            if len(hourly_counts) < 2:
                return anomalies
            
            # Calculate average and standard deviation
            counts = list(hourly_counts.values())
            avg_count = statistics.mean(counts)
            std_dev = statistics.stdev(counts) if len(counts) > 1 else 0
            
            # Detect anomalies (more than 2 standard deviations from mean)
            threshold = 2 * std_dev
            for hour, count in hourly_counts.items():
                if abs(count - avg_count) > threshold:
                    anomaly_type = 'spike' if count > avg_count else 'drop'
                    anomalies.append({
                        'anomaly_type': 'time_pattern',
                        'anomaly_subtype': anomaly_type,
                        'timestamp': hour.isoformat(),
                        'description=f'Log {anomaly_type} detected at {hour}',
                        'severity': 'medium' if anomaly_type == 'spike' else 'low',
                        'metrics': {
                            'count': count,
                            'average': avg_count,
                            'deviation': abs(count - avg_count)
                        }
                    })
            
        except Exception as e:
            logger.error(f"Failed to detect time anomalies: {e}")
        
        return anomalies
    
    def _detect_frequency_anomalies(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect frequency-based anomalies"""
        anomalies = []
        
        try:
            # Analyze error frequency
            error_logs = [log for log in logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
            error_rate = len(error_logs) / len(logs) if logs else 0
            
            # High error rate anomaly
            if error_rate > 0.1:  # More than 10% errors
                anomalies.append({
                    'anomaly_type': 'frequency',
                    'anomaly_subtype': 'high_error_rate',
                    'description=f'High error rate detected: {error_rate:.2%}',
                    'severity': 'high',
                    'metrics': {
                        'error_rate': error_rate,
                        'error_count': len(error_logs),
                        'total_logs': len(logs)
                    }
                })
            
            # Analyze critical error frequency
            critical_logs = [log for log in logs if log.level == LogLevel.CRITICAL]
            critical_rate = len(critical_logs) / len(logs) if logs else 0
            
            if critical_rate > 0.01:  # More than 1% critical
                anomalies.append({
                    'anomaly_type': 'frequency',
                    'anomaly_subtype': 'high_critical_rate',
                    'description=f'High critical error rate detected: {critical_rate:.2%}',
                    'severity': 'critical',
                    'metrics': {
                        'critical_rate': critical_rate,
                        'critical_count': len(critical_logs),
                        'total_logs': len(logs)
                    }
                })
            
        except Exception as e:
            logger.error(f"Failed to detect frequency anomalies: {e}")
        
        return anomalies
    
    def _detect_content_anomalies(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect content-based anomalies"""
        anomalies = []
        
        try:
            # Analyze message length anomalies
            message_lengths = [len(log.message) for log in logs]
            if message_lengths:
                avg_length = statistics.mean(message_lengths)
                std_dev = statistics.stdev(message_lengths) if len(message_lengths) > 1 else 0
                
                # Find unusually long or short messages
                for log in logs:
                    if abs(len(log.message) - avg_length) > 3 * std_dev:
                        anomalies.append({
                            'anomaly_type': 'content',
                            'anomaly_subtype': 'unusual_message_length',
                            'timestamp': log.timestamp.isoformat(),
                            'description=f'Unusual message length detected: {len(log.message)} characters',
                            'severity': 'low',
                            'metrics': {
                                'message_length': len(log.message),
                                'average_length': avg_length,
                                'deviation': abs(len(log.message) - avg_length)
                            },
                            'sample_message': log.message[:100] + '...' if len(log.message) > 100 else log.message
                        })
            
        except Exception as e:
            logger.error(f"Failed to detect content anomalies: {e}")
        
        return anomalies
    
    def _detect_security_events(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect security events in logs"""
        logger.info("Detecting security events in logs")
        
        security_events = []
        
        try:
            # Use security-related patterns
            security_patterns = [p for p in self.patterns.values() 
                              if p.category == 'security' and p.enabled]
            
            for pattern in security_patterns:
                try:
                    regex = re.compile(pattern.regex_pattern, re.IGNORECASE)
                    matches = []
                    
                    for log in logs:
                        if regex.search(log.message):
                            matches.append({
                                'timestamp': log.timestamp.isoformat(),
                                'level': log.level.value,
                                'message': log.message,
                                'source': log.source,
                                'resource_id': log.resource_id,
                                'resource_name': log.resource_name
                            })
                    
                    if matches:
                        security_events.append({
                            'event_type': pattern.pattern_type.value,
                            'event_name': pattern.pattern_name,
                            'severity': pattern.severity,
                            'match_count': len(matches),
                            'matches': matches[:5],  # Limit to top 5 matches
                            'first_occurrence': min(matches, key=lambda x: x['timestamp'])['timestamp'],
                            'last_occurrence': max(matches, key=lambda x: x['timestamp'])['timestamp']
                        })
                
                except Exception as e:
                    logger.error(f"Failed to detect security events with pattern {pattern.pattern_id}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to detect security events: {e}")
        
        return security_events
    
    def _detect_performance_issues(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect performance issues in logs"""
        logger.info("Detecting performance issues in logs")
        
        performance_issues = []
        
        try:
            # Use performance-related patterns
            performance_patterns = [p for p in self.patterns.values() 
                                 if p.category == 'performance' and p.enabled]
            
            for pattern in performance_patterns:
                try:
                    regex = re.compile(pattern.regex_pattern, re.IGNORECASE)
                    matches = []
                    
                    for log in logs:
                        if regex.search(log.message):
                            matches.append({
                                'timestamp': log.timestamp.isoformat(),
                                'level': log.level.value,
                                'message': log.message,
                                'source': log.source,
                                'resource_id': log.resource_id,
                                'resource_name': log.resource_name
                            })
                    
                    if matches:
                        performance_issues.append({
                            'issue_type': pattern.pattern_type.value,
                            'issue_name': pattern.pattern_name,
                            'severity': pattern.severity,
                            'match_count': len(matches),
                            'matches': matches[:5],  # Limit to top 5 matches
                            'first_occurrence': min(matches, key=lambda x: x['timestamp'])['timestamp'],
                            'last_occurrence': max(matches, key=lambda x: x['timestamp'])['timestamp']
                        })
                
                except Exception as e:
                    logger.error(f"Failed to detect performance issues with pattern {pattern.pattern_id}: {e}")
            
            # Detect response time patterns
            response_time_matches = []
            for log in logs:
                # Look for response time patterns in messages
                response_time_pattern = r'(?i)(response time|latency|took|elapsed|duration)[:\s]*(\d+(?:\.\d+)?)\s*(ms|seconds?|s)'
                match = re.search(response_time_pattern, log.message)
                if match:
                    try:
                        value = float(match.group(2))
                        unit = match.group(3).lower()
                        
                        # Convert to milliseconds
                        if unit in ['seconds', 's']:
                            value *= 1000
                        
                        if value > 1000:  # More than 1 second
                            response_time_matches.append({
                                'timestamp': log.timestamp.isoformat(),
                                'response_time_ms': value,
                                'message': log.message,
                                'source': log.source,
                                'resource_id': log.resource_id,
                                'resource_name': log.resource_name
                            })
                    except ValueError:
                        continue
            
            if response_time_matches:
                # Calculate statistics
                response_times = [m['response_time_ms'] for m in response_time_matches]
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                
                performance_issues.append({
                    'issue_type': 'response_time',
                    'issue_name': 'High Response Time',
                    'severity': 'medium' if avg_response_time < 5000 else 'high',
                    'match_count': len(response_time_matches),
                    'matches': response_time_matches[:5],
                    'statistics': {
                        'average_response_time_ms': avg_response_time,
                        'max_response_time_ms': max_response_time,
                        'min_response_time_ms': min(response_times)
                    }
                })
            
        except Exception as e:
            logger.error(f"Failed to detect performance issues: {e}")
        
        return performance_issues
    
    def _generate_recommendations(self, logs: List[LogEntry], patterns_found: List[Dict[str, Any]], 
                                 security_events: List[Dict[str, Any]], performance_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        try:
            # Recommendations based on log levels
            total_logs = len(logs)
            if total_logs > 0:
                error_rate = len([log for log in logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]) / total_logs
                
                if error_rate > 0.1:
                    recommendations.append("High error rate detected. Review application code and infrastructure health.")
                elif error_rate > 0.05:
                    recommendations.append("Elevated error rate detected. Monitor closely and investigate root causes.")
                
                critical_rate = len([log for log in logs if log.level == LogLevel.CRITICAL]) / total_logs
                if critical_rate > 0.01:
                    recommendations.append("Critical errors detected. Immediate investigation required.")
            
            # Recommendations based on patterns
            high_severity_patterns = [p for p in patterns_found if p['severity'] in ['critical', 'high']]
            if high_severity_patterns:
                recommendations.append("High-severity patterns detected. Implement automated monitoring and alerting.")
            
            # Recommendations based on security events
            if security_events:
                recommendations.append("Security events detected. Review security policies and access controls.")
                
                critical_security = [e for e in security_events if e['severity'] == 'critical']
                if critical_security:
                    recommendations.append("Critical security events detected. Immediate security team notification required.")
            
            # Recommendations based on performance issues
            if performance_issues:
                recommendations.append("Performance issues detected. Review application performance and resource utilization.")
                
                high_performance = [i for i in performance_issues if i['severity'] in ['critical', 'high']]
                if high_performance:
                    recommendations.append("High-severity performance issues detected. Consider scaling or optimization.")
            
            # General recommendations
            if not recommendations:
                recommendations.append("Log analysis completed with no major issues detected. Continue monitoring.")
            
            # Add operational recommendations
            recommendations.extend([
                "Implement structured logging for better analysis capabilities",
                "Set up automated log aggregation and monitoring",
                "Configure alerts for critical log patterns",
                "Regularly review and update log analysis patterns"
            ])
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            recommendations.append("Failed to generate recommendations. Please review logs manually.")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_trend_analysis(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """Generate trend analysis"""
        try:
            if not logs:
                return {}
            
            # Time-based trends
            hourly_trends = {}
            for log in logs:
                hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_trends:
                    hourly_trends[hour] = {'total': 0, 'error': 0, 'critical': 0}
                
                hourly_trends[hour]['total'] += 1
                if log.level == LogLevel.ERROR:
                    hourly_trends[hour]['error'] += 1
                elif log.level == LogLevel.CRITICAL:
                    hourly_trends[hour]['critical'] += 1
            
            # Calculate trends
            trend_analysis = {
                'hourly_volume': {hour.isoformat(): counts for hour, counts in hourly_trends.items()},
                'peak_hour': max(hourly_trends.items(), key=lambda x: x[1]['total'])[0].isoformat() if hourly_trends else None,
                'error_trend': 'increasing' if len([h for h in hourly_trends.values() if h['error'] > 0]) > len(hourly_trends) / 2 else 'stable',
                'critical_trend': 'increasing' if len([h for h in hourly_trends.values() if h['critical'] > 0]) > len(hourly_trends) / 4 else 'stable'
            }
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to generate trend analysis: {e}")
            return {}
    
    def generate_log_report(self, analysis_results: Dict[str, LogAnalysisResult], 
                           output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive log analysis report"""
        logger.info("Generating log analysis report")
        
        # Calculate overall statistics
        total_logs = sum(result.total_logs for result in analysis_results.values())
        total_patterns = sum(len(result.patterns_found) for result in analysis_results.values())
        total_security_events = sum(len(result.security_events) for result in analysis_results.values())
        total_performance_issues = sum(len(result.performance_issues) for result in analysis_results.values())
        
        # Provider comparisons
        provider_comparison = {}
        for provider, result in analysis_results.items():
            provider_comparison[provider] = {
                'total_logs': result.total_logs,
                'patterns_found': len(result.patterns_found),
                'security_events': len(result.security_events),
                'performance_issues': len(result.performance_issues),
                'recommendations': len(result.recommendations)
            }
        
        # Top patterns across all providers
        all_patterns = []
        for result in analysis_results.values():
            all_patterns.extend(result.patterns_found)
        
        top_patterns = sorted(all_patterns, key=lambda x: x['confidence'], reverse=True)[:10]
        
        # Security events summary
        security_summary = {}
        for result in analysis_results.values():
            for event in result.security_events:
                event_type = event['event_type']
                security_summary[event_type] = security_summary.get(event_type, 0) + 1
        
        # Performance issues summary
        performance_summary = {}
        for result in analysis_results.values():
            for issue in result.performance_issues:
                issue_type = issue['issue_type']
                performance_summary[issue_type] = performance_summary.get(issue_type, 0) + 1
        
        # All recommendations
        all_recommendations = []
        for result in analysis_results.values():
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates and get top recommendations
        unique_recommendations = list(set(all_recommendations))
        top_recommendations = sorted(unique_recommendations, key=lambda x: len(x), reverse=True)[:10]
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_providers_analyzed': len(analysis_results),
                'total_logs_analyzed': total_logs,
                'total_patterns_found': total_patterns,
                'total_security_events': total_security_events,
                'total_performance_issues': total_performance_issues,
                'enabled_patterns': len([p for p in self.patterns.values() if p.enabled])
            },
            'provider_comparison': provider_comparison,
            'top_patterns': top_patterns,
            'security_summary': security_summary,
            'performance_summary': performance_summary,
            'top_recommendations': top_recommendations,
            'detailed_results': {
                provider: {
                    'analysis_id': result.analysis_id,
                    'total_logs': result.total_logs,
                    'logs_by_level': result.logs_by_level,
                    'patterns_found': result.patterns_found[:5],
                    'security_events': result.security_events[:5],
                    'performance_issues': result.performance_issues[:5],
                    'recommendations': result.recommendations[:5],
                    'trend_analysis': result.trend_analysis
                }
                for provider, result in analysis_results.items()
            }
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Log analysis report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Log Analyzer")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--patterns", help="Log patterns file")
    parser.add_argument("--action", choices=['analyze', 'report'], 
                       default='analyze', help="Action to perform")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--environment", default='production', help="Environment to analyze")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize log analyzer
    analyzer = LogAnalyzer(args.config)
    
    # Load patterns
    analyzer.load_patterns(args.patterns)
    
    try:
        if args.action == 'analyze':
            # Perform log analysis
            results = analyzer.analyze_logs(args.providers, args.environment)
            
            print(f"\nLog Analysis Results:")
            for provider, result in results.items():
                print(f"\n{provider.upper()}:")
                print(f"  Total Logs: {result.total_logs}")
                print(f"  Patterns Found: {len(result.patterns_found)}")
                print(f"  Security Events: {len(result.security_events)}")
                print(f"  Performance Issues: {len(result.performance_issues)}")
                print(f"  Recommendations: {len(result.recommendations)}")
                
                if result.logs_by_level:
                    print(f"  Log Levels: {result.logs_by_level}")
                
                if result.patterns_found:
                    print(f"  Top Patterns:")
                    for pattern in result.patterns_found[:3]:
                        print(f"    - {pattern['pattern_name']}: {pattern['match_count']} matches")
        
        elif args.action == 'report':
            # Perform analysis first
            results = analyzer.analyze_logs(args.providers, args.environment)
            
            # Generate report
            report = analyzer.generate_log_report(results, args.output)
            
            summary = report['summary']
            print(f"\nLog Analysis Report:")
            print(f"Providers Analyzed: {summary['total_providers_analyzed']}")
            print(f"Total Logs Analyzed: {summary['total_logs_analyzed']}")
            print(f"Total Patterns Found: {summary['total_patterns_found']}")
            print(f"Total Security Events: {summary['total_security_events']}")
            print(f"Total Performance Issues: {summary['total_performance_issues']}")
            print(f"Enabled Patterns: {summary['enabled_patterns']}")
            
            print(f"\nProvider Comparison:")
            for provider, stats in report['provider_comparison'].items():
                print(f"  {provider}: {stats['total_logs']} logs, {stats['patterns_found']} patterns")
            
            if report['security_summary']:
                print(f"\nSecurity Events Summary:")
                for event_type, count in report['security_summary'].items():
                    print(f"  {event_type}: {count}")
            
            if report['performance_summary']:
                print(f"\nPerformance Issues Summary:")
                for issue_type, count in report['performance_summary'].items():
                    print(f"  {issue_type}: {count}")
            
            print(f"\nTop Recommendations:")
            for rec in report['top_recommendations'][:5]:
                print(f"  - {rec}")
            
            if args.output:
                print(f"\nReport saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Log analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
