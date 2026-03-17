#!/usr/bin/env python3
"""
AI Agent Tracing Evaluation Framework

Main entry point for evaluating Pi-Mono agent traces from Langfuse.
Coordinates multiple evaluators to provide comprehensive analysis.
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Add evaluators to path
sys.path.append(str(Path(__file__).parent / "evaluators"))

from skill_invocation_evaluator import GitOpsSkillEvaluator
from performance_evaluator import PerformanceEvaluator
from cost_evaluator import CostEvaluator
from monitoring_evaluator import AgentMonitoringEvaluator
from health_check_evaluator import HealthCheckEvaluator
from security_evaluator import SecurityEvaluator
from compliance_evaluator import ComplianceEvaluator
from auto_fix_evaluator import AutoFixManager
from integrations.langfuse_client import create_langfuse_client, LangfuseTraceGenerator
from alerts.alert_manager import create_alert_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TracingEvaluationFramework:
    """Main framework for evaluating agent traces"""

    def __init__(self, enable_alerts: bool = True):
        self.skill_evaluator = GitOpsSkillEvaluator()
        self.performance_evaluator = PerformanceEvaluator()
        self.monitoring_evaluator = AgentMonitoringEvaluator()
        self.auto_fix_manager = AutoFixManager()
        self.health_check_evaluator = HealthCheckEvaluator()
        self.evaluators = {
            "skill_invocation": self.skill_evaluator,
            "performance": self.performance_evaluator,
            "cost": CostEvaluator(),
            "monitoring": self.monitoring_evaluator,
            "health_check": self.health_check_evaluator,
            "security": SecurityEvaluator(),
            "compliance": ComplianceEvaluator()
        }
        
        # Initialize Langfuse integration
        self.use_langfuse = False
        self.langfuse_client = None
        self.langfuse_generator = None
        
        # Try to initialize Langfuse if environment variables are set
        try:
            self.langfuse_client = create_langfuse_client()
            self.langfuse_generator = LangfuseTraceGenerator(self.langfuse_client)
            self.use_langfuse = True
            logger.info("Langfuse integration initialized")
        except Exception as e:
            logger.info(f"Langfuse integration not available: {e}")
            self.use_langfuse = False
        
        # Initialize alert manager
        self.alert_manager = None
        if enable_alerts:
            try:
                self.alert_manager = create_alert_manager()
                logger.info("Alert manager initialized")
            except Exception as e:
                logger.warning(f"Alert manager initialization failed: {e}")
                self.alert_manager = None

    def fetch_real_traces(self, count: int = 100, filters: dict = None) -> List[Dict[str, Any]]:
        """
        Fetch real traces from Langfuse
        
        Args:
            count: Number of traces to fetch
            filters: Optional filter criteria
            
        Returns:
            List of real traces from Langfuse
        """
        if not self.use_langfuse or not self.langfuse_generator:
            logger.warning("Langfuse integration not available, using sample traces")
            from example_usage import generate_sample_traces
            return generate_sample_traces(count)
        
        try:
            # Convert filters to Langfuse format
            langfuse_filters = None
            if filters:
                from integrations.langfuse_client import TraceFilter
                langfuse_filters = TraceFilter(
                    user_id=filters.get('user_id'),
                    session_id=filters.get('session_id'),
                    tags=filters.get('tags'),
                    limit=count
                )
            
            traces = self.langfuse_generator.generate_evaluation_traces(count, langfuse_filters)
            logger.info(f"Fetched {len(traces)} real traces from Langfuse")
            return traces
            
        except Exception as e:
            logger.error(f"Failed to fetch real traces from Langfuse: {e}")
            # Fallback to sample traces
            from example_usage import generate_sample_traces
            return generate_sample_traces(count)
    
    def stream_real_traces(self, duration_minutes: int = 60, filters: dict = None):
        """
        Stream real traces from Langfuse
        
        Args:
            duration_minutes: Duration to stream traces
            filters: Optional filter criteria
            
        Yields:
            Real-time traces from Langfuse
        """
        if not self.use_langfuse or not self.langfuse_generator:
            logger.warning("Langfuse integration not available")
            return
        
        try:
            # Convert filters to Langfuse format
            langfuse_filters = None
            if filters:
                from integrations.langfuse_client import TraceFilter
                langfuse_filters = TraceFilter(
                    user_id=filters.get('user_id'),
                    session_id=filters.get('session_id'),
                    tags=filters.get('tags')
                )
            
            for trace in self.langfuse_generator.generate_real_time_traces(duration_minutes, langfuse_filters):
                yield trace
                
        except Exception as e:
            logger.error(f"Failed to stream real traces from Langfuse: {e}")
    
    def get_langfuse_health(self) -> Dict[str, Any]:
        """
        Check Langfuse service health
        
        Returns:
            Health status information
        """
        if not self.use_langfuse or not self.langfuse_client:
            return {
                'status': 'disabled',
                'message': 'Langfuse integration not enabled'
            }
        
        try:
            return self.langfuse_client.health_check()
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def evaluate_traces(self, traces: List[Dict[str, Any]], 
                      evaluator_types: List[str] = None) -> Dict[str, Any]:
        """
        Evaluate traces using specified evaluators

        Args:
            traces: List of Langfuse trace data
            evaluator_types: List of evaluator types to run (None for all)

        Returns:
            Comprehensive evaluation results
        """
        if evaluator_types is None:
            evaluator_types = list(self.evaluators.keys())
        
        results = {}
        
        for evaluator_type in evaluator_types:
            if evaluator_type in self.evaluators:
                evaluator = self.evaluators[evaluator_type]
                try:
                    # Use evaluate_batch method for consistency
                    result = evaluator.evaluate_batch(traces)
                    results[evaluator_type] = result
                except Exception as e:
                    logger.error(f"Evaluation failed for {evaluator_type}: {e}")
                    results[evaluator_type] = {
                        'error': str(e),
                        'average_score': 0.0,
                        'pass_rate': 0.0
                    }
            else:
                logger.warning(f"Unknown evaluator: {evaluator_type}")
        
        # Generate summary
        summary = self._generate_summary(results)
        
        # Create evaluation results
        evaluation_results = {
            'summary': summary,
            'evaluator_results': results,
            'aggregate_metrics': {
                'total_evaluations': len(traces),
                'evaluators_run': evaluator_types,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Process alerts if enabled
        if self.alert_manager:
            try:
                import asyncio
                evaluation_id = f"eval_{int(datetime.now().timestamp())}"
                asyncio.create_task(
                    self.alert_manager.process_evaluation_results(evaluation_results, evaluation_id)
                )
                logger.info("Alert processing initiated")
            except Exception as e:
                logger.error(f"Alert processing failed: {e}")
        
        return evaluation_results

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary from evaluator results"""
        summary = {
            "overall_score": 0,
            "overall_pass_rate": 0,
            "total_evaluations": 0,
            "evaluator_count": len(results),
            "evaluators_passed": 0,
            "evaluators_failed": 0
        }
        
        total_score = 0
        total_pass_rate = 0
        evaluator_count = 0
        
        for evaluator_name, result in results.items():
            if 'error' in result:
                summary["evaluators_failed"] += 1
                continue
                
            evaluator_count += 1
            score = result.get('average_score', 0)
            pass_rate = result.get('pass_rate', 0)
            
            total_score += score
            total_pass_rate += pass_rate
            
            # Count passes/failures
            if score >= 0.7:  # Assuming 0.7 is passing threshold
                summary["evaluators_passed"] += 1
            else:
                summary["evaluators_failed"] += 1
        
        if evaluator_count > 0:
            summary["overall_score"] = total_score / evaluator_count
            summary["overall_pass_rate"] = total_pass_rate / evaluator_count
        
        return summary

    def load_traces_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load traces from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'traces' in data:
                return data['traces']
            else:
                print(f"Error: Unexpected data format in {file_path}")
                return []
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {e}")
            return []

    def generate_report(self, evaluation_result: Dict[str, Any], 
                      output_format: str = "json") -> str:
        """Generate formatted evaluation report"""
        if output_format.lower() == "json":
            return json.dumps(evaluation_result, indent=2)
        elif output_format.lower() == "summary":
            return self._generate_summary_report(evaluation_result)
        elif output_format.lower() == "detailed":
            return self._generate_detailed_report(evaluation_result)
        else:
            return json.dumps(evaluation_result, indent=2)

    def _generate_summary_report(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary report"""
        summary = result["summary"]
        lines = []
        
        lines.append("AI Agent Evaluation Summary")
        lines.append("=" * 40)
        lines.append(f"Overall Score: {summary['overall_score']:.3f}")
        lines.append(f"Overall Pass Rate: {summary['overall_pass_rate']:.1%}")
        lines.append(f"Evaluators Passed: {summary['evaluators_passed']}")
        lines.append(f"Evaluators Failed: {summary['evaluators_failed']}")
        lines.append("")
        
        # Add evaluator-specific summaries
        for evaluator_name, evaluator_result in result["evaluator_results"].items():
            if 'error' in evaluator_result:
                lines.append(f"{evaluator_name}: ERROR - {evaluator_result['error']}")
            else:
                score = evaluator_result.get('average_score', 0)
                pass_rate = evaluator_result.get('pass_rate', 0)
                lines.append(f"{evaluator_name}: {score:.3f} ({pass_rate:.1%} pass rate)")
        
        return "\n".join(lines)

    def _generate_detailed_report(self, result: Dict[str, Any]) -> str:
        """Generate detailed report with all results"""
        lines = [self._generate_summary_report(result)]
        lines.append("\nDETAILED RESULTS:")
        lines.append("=" * 50)
        
        for evaluator_name, evaluator_result in result["evaluator_results"].items():
            lines.append(f"\n{evaluator_name.upper()}:")
            lines.append("-" * 30)
            
            if 'error' in evaluator_result:
                lines.append(f"ERROR: {evaluator_result['error']}")
            else:
                for key, value in evaluator_result.items():
                    if key != 'error':
                        lines.append(f"{key}: {value}")
        
        return "\n".join(lines)

    def get_alerts(self, alert_type: str = 'active', limit: int = 100) -> List[Dict[str, Any]]:
        """Get alerts from alert manager"""
        if not self.alert_manager:
            return []
        
        if alert_type == 'active':
            alerts = self.alert_manager.get_active_alerts()
        elif alert_type == 'history':
            alerts = self.alert_manager.get_alert_history(limit)
        else:
            return []
        
        return [alert.to_dict() for alert in alerts]
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if not self.alert_manager:
            return False
        
        return self.alert_manager.acknowledge_alert(alert_id, acknowledged_by)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if not self.alert_manager:
            return False
        
        return self.alert_manager.resolve_alert(alert_id)
    
    def get_alert_metrics(self) -> Dict[str, Any]:
        """Get alert system metrics"""
        if not self.alert_manager:
            return {'status': 'Alert manager not initialized'}
        
        return self.alert_manager.get_metrics()
