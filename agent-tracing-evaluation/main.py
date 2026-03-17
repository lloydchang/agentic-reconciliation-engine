#!/usr/bin/env python3
"""
AI Agent Tracing Evaluation Framework

Main entry point for evaluating Pi-Mono agent traces from Langfuse.
Coordinates multiple evaluators to provide comprehensive analysis.
"""

import argparse
import json
import sys
from typing import Dict, Any, List
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

class TracingEvaluationFramework:
    """Main framework for evaluating agent traces"""

    def __init__(self):
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
        
        # Run each evaluator
        for evaluator_type in evaluator_types:
            if evaluator_type not in self.evaluators:
                print(f"Warning: Unknown evaluator type '{evaluator_type}'")
                continue

            evaluator = self.evaluators[evaluator_type]
            
            # Run evaluation
            if hasattr(evaluator, 'evaluate_batch'):
                result = evaluator.evaluate_batch(traces)
            else:
                # Fallback to individual evaluations
                individual_results = []
                for trace in traces:
                    individual_result = evaluator.evaluate(trace)
                    individual_results.append(individual_result)
                
                result = {
                    "total_evaluations": len(individual_results),
                    "results": individual_results,
                    "evaluator": evaluator_type,
                    "timestamp": datetime.now().isoformat()
                }
            
            results[evaluator_type] = result

        # Generate summary
        summary = self._generate_summary(results)

        return {
            "summary": summary,
            "evaluator_results": results,
            "trace_count": len(traces),
            "evaluators_run": evaluator_types,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary from evaluator results"""
        summary = {
            "overall_score": 0,
            "total_evaluations": 0,
            "passed_evaluations": 0,
            "evaluator_summaries": {}
        }

        total_score = 0
        evaluator_count = 0

        for evaluator_type, result in results.items():
            evaluator_summary = {}
            
            # Extract key metrics
            if "average_score" in result:
                evaluator_summary["average_score"] = result["average_score"]
                total_score += result["average_score"]
                evaluator_count += 1
            
            if "pass_rate" in result:
                evaluator_summary["pass_rate"] = result["pass_rate"]
                summary["passed_evaluations"] += result.get("passed_count", 0)
            
            if "total_evaluations" in result:
                evaluator_summary["total_evaluations"] = result["total_evaluations"]
                summary["total_evaluations"] += result["total_evaluations"]

            summary["evaluator_summaries"][evaluator_type] = evaluator_summary

        # Calculate overall score
        if evaluator_count > 0:
            summary["overall_score"] = total_score / evaluator_count

        # Calculate overall pass rate
        if summary["total_evaluations"] > 0:
            summary["overall_pass_rate"] = summary["passed_evaluations"] / summary["total_evaluations"]
        else:
            summary["overall_pass_rate"] = 0

        return summary

    def load_traces_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load traces from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Handle different file formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "traces" in data:
                return data["traces"]
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            else:
                print(f"Error: Unexpected file format in {file_path}")
                return []
                
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {e}")
            return []

    def load_traces_from_langfuse(self, langfuse_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load traces directly from Langfuse API"""
        try:
            # This would require langfuse client library
            # For now, return placeholder
            print("Langfuse API integration not yet implemented")
            return []
        except Exception as e:
            print(f"Error loading from Langfuse: {e}")
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
        
        lines.append("=" * 60)
        lines.append("AI AGENT TRACING EVALUATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {result['timestamp']}")
        lines.append(f"Total Traces: {result['trace_count']}")
        lines.append(f"Evaluators Run: {', '.join(result['evaluators_run'])}")
        lines.append("")
        
        # Overall metrics
        lines.append("OVERALL PERFORMANCE:")
        lines.append(f"  Overall Score: {summary['overall_score']:.2f}")
        lines.append(f"  Pass Rate: {summary['overall_pass_rate']:.1%}")
        lines.append(f"  Total Evaluations: {summary['total_evaluations']}")
        lines.append("")
        
        # Evaluator-specific summaries
        lines.append("EVALUATOR DETAILS:")
        for evaluator_type, evaluator_summary in summary["evaluator_summaries"].items():
            lines.append(f"  {evaluator_type.upper()}:")
            if "average_score" in evaluator_summary:
                lines.append(f"    Average Score: {evaluator_summary['average_score']:.2f}")
            if "pass_rate" in evaluator_summary:
                lines.append(f"    Pass Rate: {evaluator_summary['pass_rate']:.1%}")
            if "total_evaluations" in evaluator_summary:
                lines.append(f"    Total Evaluations: {evaluator_summary['total_evaluations']}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_detailed_report(self, result: Dict[str, Any]) -> str:
        """Generate detailed report with all results"""
        lines = [self._generate_summary_report(result)]
        lines.append("\nDETAILED RESULTS:")
        lines.append("=" * 40)
        
        # Add detailed results from each evaluator
        for evaluator_type, evaluator_result in result["evaluator_results"].items():
            lines.append(f"\n{evaluator_type.upper()} EVALUATOR:")
            lines.append("-" * 30)
            
            if "results" in evaluator_result:
                for i, individual_result in enumerate(evaluator_result["results"][:5]):  # Limit to first 5
                    lines.append(f"  Result {i+1}:")
                    lines.append(f"    Score: {individual_result.get('score', 'N/A')}")
                    lines.append(f"    Passed: {individual_result.get('passed', 'N/A')}")
                    
                    if "details" in individual_result:
                        details = individual_result["details"]
                        lines.append("    Details:")
                        for key, value in details.items():
                            lines.append(f"      {key}: {value}")
                    lines.append("")
                
                if len(evaluator_result["results"]) > 5:
                    lines.append(f"  ... and {len(evaluator_result['results']) - 5} more results")
        
        return "\n".join(lines)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Evaluate AI agent traces from Langfuse",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate traces from file
  python main.py --file traces.json
  
  # Run specific evaluators
  python main.py --file traces.json --evaluators skill_invocation performance
  
  # Generate summary report
  python main.py --file traces.json --format summary
  
  # Load from Langfuse API
  python main.py --langfuse --config langfuse-config.json
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        help="JSON file containing trace data"
    )
    
    parser.add_argument(
        "--evaluators", "-e",
        nargs="+",
        choices=["skill_invocation", "performance", "all"],
        default=["all"],
        help="Evaluators to run (default: all)"
    )
    
    parser.add_argument(
        "--format", "-o",
        choices=["json", "summary", "detailed"],
        default="summary",
        help="Output format (default: summary)"
    )
    
    parser.add_argument(
        "--output", "-w",
        help="Write report to file"
    )
    
    parser.add_argument(
        "--langfuse", "-l",
        action="store_true",
        help="Load traces from Langfuse API"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Configuration file for Langfuse API"
    )
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = TracingEvaluationFramework()
    
    # Load traces
    traces = []
    if args.langfuse:
        if not args.config:
            print("Error: --config required when using --langfuse")
            sys.exit(1)
        
        with open(args.config, 'r') as f:
            langfuse_config = json.load(f)
        traces = framework.load_traces_from_langfuse(langfuse_config)
    elif args.file:
        traces = framework.load_traces_from_file(args.file)
    else:
        print("Error: Either --file or --langfuse must be specified")
        parser.print_help()
        sys.exit(1)
    
    if not traces:
        print("Error: No traces found to evaluate")
        sys.exit(1)
    
    # Determine evaluators to run
    evaluators = args.evaluators
    if "all" in evaluators:
        evaluators = None  # Run all evaluators
    
    # Run evaluation
    print(f"Evaluating {len(traces)} traces...")
    evaluation_result = framework.evaluate_traces(traces, evaluators)
    
    # Generate report
    report = framework.generate_report(evaluation_result, args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
