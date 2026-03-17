#!/usr/bin/env python3
"""
Visualization Module for AI Agent Tracing Evaluation

Generates charts and visual reports from evaluation results.
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import argparse
from pathlib import Path

class EvaluationVisualizer:
    """Creates visualizations from evaluation results"""

    def __init__(self):
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def create_performance_dashboard(self, evaluation_result: Dict[str, Any], 
                              output_path: str = "performance_dashboard.png"):
        """Create comprehensive performance dashboard"""
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('AI Agent Performance Dashboard', fontsize=16, fontweight='bold')
        
        evaluator_results = evaluation_result.get("evaluator_results", {})
        
        # Performance scores over time
        if "performance" in evaluator_results:
            self._plot_performance_scores(evaluator_results["performance"], axes[0, 0])
        
        # Skill invocation success rates
        if "skill_invocation" in evaluator_results:
            self._plot_skill_invocation_rates(evaluator_results["skill_invocation"], axes[0, 1])
        
        # Cost analysis
        if "cost" in evaluator_results:
            self._plot_cost_analysis(evaluator_results["cost"], axes[1, 0])
        
        # Overall metrics summary
        self._plot_metrics_summary(evaluation_result, axes[1, 1])
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Performance dashboard saved to {output_path}")

    def _plot_performance_scores(self, perf_result: Dict[str, Any], ax):
        """Plot performance scores over time"""
        if "results" not in perf_result:
            ax.text(0.5, 0.5, 'No performance data', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        results = perf_result["results"]
        if not results:
            ax.text(0.5, 0.5, 'No performance data', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # Extract scores and timestamps
        scores = [r.get("score", 0) for r in results]
        timestamps = [r.get("timestamp", "") for r in results]
        
        # Create simple index if timestamps are not parseable
        x = range(len(scores))
        
        ax.plot(x, scores, marker='o', linewidth=2, markersize=6)
        ax.set_title('Performance Scores Over Time')
        ax.set_xlabel('Request Index')
        ax.set_ylabel('Performance Score')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        
        # Add performance tier reference lines
        ax.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='Excellent')
        ax.axhline(y=0.7, color='blue', linestyle='--', alpha=0.5, label='Good')
        ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Acceptable')
        ax.legend(loc='upper right')

    def _plot_skill_invocation_rates(self, skill_result: Dict[str, Any], ax):
        """Plot skill invocation success rates"""
        if "results" not in skill_result:
            ax.text(0.5, 0.5, 'No skill invocation data', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        results = skill_result["results"]
        if not results:
            ax.text(0.5, 0.5, 'No skill invocation data', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # Count passed/failed
        passed = sum(1 for r in results if r.get("passed", False))
        failed = len(results) - passed
        
        # Create pie chart
        sizes = [passed, failed] if (passed + failed) > 0 else [1]
        labels = ['Passed', 'Failed'] if (passed + failed) > 0 else ['No Data']
        colors = ['#2ecc71', '#e74c3c'] if (passed + failed) > 0 else ['#95a5a6']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                          startangle=90)
        ax.set_title('Skill Invocation Success Rate')

    def _plot_cost_analysis(self, cost_result: Dict[str, Any], ax):
        """Plot cost analysis"""
        if "aggregate_metrics" not in cost_result:
            ax.text(0.5, 0.5, 'No cost data', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        metrics = cost_result["aggregate_metrics"]
        
        # Create bar chart for key metrics
        metric_names = ['Total Cost ($)', 'Avg Cost/Request ($)', 'Tokens/$']
        metric_values = [
            metrics.get("total_cost", 0),
            metrics.get("average_cost_per_request", 0),
            metrics.get("overall_efficiency_tokens_per_dollar", 0)
        ]
        
        bars = ax.bar(metric_names, metric_values, color=['#3498db', '#2ecc71', '#f39c12'])
        ax.set_title('Cost Analysis')
        ax.set_ylabel('Value')
        
        # Rotate x labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}', ha='center', va='bottom')

    def _plot_metrics_summary(self, evaluation_result: Dict[str, Any], ax):
        """Plot overall metrics summary"""
        summary = evaluation_result.get("summary", {})
        
        # Create summary metrics
        metrics = {
            'Overall Score': summary.get("overall_score", 0),
            'Pass Rate': summary.get("overall_pass_rate", 0),
            'Total Traces': summary.get("total_evaluations", 0)
        }
        
        # Create horizontal bar chart
        y_pos = range(len(metrics))
        bars = ax.barh(y_pos, list(metrics.values()), color=['#3498db', '#2ecc71', '#f39c12'])
        
        ax.set_yticks(y_pos, list(metrics.keys()))
        ax.set_xlabel('Value')
        ax.set_title('Overall Summary')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, metrics.values())):
            width = bar.get_width()
            ax.text(width + 0.01, bar.get_y() + bar.get_height()/2.,
                    f'{value:.3f}', ha='left', va='center')

    def create_trend_analysis(self, evaluation_result: Dict[str, Any], 
                          output_path: str = "trend_analysis.png"):
        """Create trend analysis visualization"""
        
        evaluator_results = evaluation_result.get("evaluator_results", {})
        
        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Trend Analysis', fontsize=16, fontweight='bold')
        
        # Performance trends
        if "performance" in evaluator_results:
            perf_data = evaluator_results["performance"]
            if "trends" in perf_data:
                self._plot_trend_line(perf_data["trends"], axes[0], "Performance")
        
        # Cost trends
        if "cost" in evaluator_results:
            cost_data = evaluator_results["cost"]
            if "trends" in cost_data:
                self._plot_trend_line(cost_data["trends"], axes[1], "Cost")
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Trend analysis saved to {output_path}")

    def _plot_trend_line(self, trend_data: Dict[str, Any], ax, metric_type: str):
        """Plot individual trend"""
        if "time_series" not in trend_data:
            ax.text(0.5, 0.5, f'No {metric_type.lower()} trend data', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        time_series = trend_data["time_series"]
        if not time_series:
            ax.text(0.5, 0.5, f'No {metric_type.lower()} trend data', 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # Extract data points
        timestamps = [point.get("timestamp", 0) for point in time_series]
        
        if metric_type == "Performance":
            values = [point.get("latency_ms", 0) for point in time_series]
            ylabel = "Latency (ms)"
            title = "Performance Trend"
        elif metric_type == "Cost":
            values = [point.get("request_cost", 0) for point in time_series]
            ylabel = "Cost ($)"
            title = "Cost Trend"
        else:
            values = [0 for point in time_series]
            ylabel = "Value"
            title = f"{metric_type} Trend"
        
        # Create simple index for x-axis
        x = range(len(values))
        
        ax.plot(x, values, marker='o', linewidth=2, markersize=6)
        ax.set_title(title)
        ax.set_xlabel('Time Index')
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    def create_model_comparison(self, evaluation_result: Dict[str, Any], 
                           output_path: str = "model_comparison.png"):
        """Create model performance comparison"""
        
        evaluator_results = evaluation_result.get("evaluator_results", {})
        
        if "cost" not in evaluator_results:
            print("No cost data available for model comparison")
            return
        
        cost_data = evaluator_results["cost"]
        if "model_usage" not in cost_data:
            print("No model usage data available")
            return
        
        model_usage = cost_data["model_usage"]
        
        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Model Performance Comparison', fontsize=16, fontweight='bold')
        
        # Model usage by count
        models = list(model_usage.keys())
        counts = [model_usage[model]["count"] for model in models]
        costs = [model_usage[model]["cost"] for model in models]
        efficiencies = []
        
        for model in models:
            usage = model_usage[model]
            if usage["cost"] > 0:
                efficiencies.append(usage["tokens"] / usage["cost"])
            else:
                efficiencies.append(0)
        
        # Plot usage count
        axes[0].bar(models, counts, color='#3498db')
        axes[0].set_title('Model Usage Count')
        axes[0].set_ylabel('Number of Requests')
        plt.setp(axes[0].get_xticklabels(), rotation=45, ha='right')
        
        # Plot efficiency
        axes[1].bar(models, efficiencies, color='#2ecc71')
        axes[1].set_title('Model Efficiency (tokens/$)')
        axes[1].set_ylabel('Tokens per Dollar')
        plt.setp(axes[1].get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Model comparison saved to {output_path}")

    def generate_html_report(self, evaluation_result: Dict[str, Any], 
                         output_path: str = "evaluation_report.html"):
        """Generate comprehensive HTML report"""
        
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Agent Evaluation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
        .score {{ font-size: 24px; font-weight: bold; color: #2ecc71; }}
        .pass {{ color: #2ecc71; }}
        .fail {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .chart {{ text-align: center; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Agent Evaluation Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
    
    <div class="section">
        <h2>Overall Summary</h2>
        <div class="metric">
            <div>Overall Score</div>
            <div class="score">{overall_score:.3f}</div>
        </div>
        <div class="metric">
            <div>Pass Rate</div>
            <div class="score">{overall_pass_rate:.1%}</div>
        </div>
        <div class="metric">
            <div>Total Evaluations</div>
            <div class="score">{total_evaluations}</div>
        </div>
    </div>
    
    {evaluator_sections}
    
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            {recommendations}
        </ul>
    </div>
</body>
</html>
        """
        
        # Build evaluator sections
        evaluator_sections = ""
        evaluator_results = evaluation_result.get("evaluator_results", {})
        
        for evaluator_name, result in evaluator_results.items():
            section = f"""
    <div class="section">
        <h2>{evaluator_name.title()} Evaluation</h2>
        <p>Average Score: {result.get('average_score', 0):.3f}</p>
        <p>Pass Rate: {result.get('pass_rate', 0):.1%}</p>
        <p>Total Evaluations: {result.get('total_evaluations', 0)}</p>
    </div>
            """
            evaluator_sections += section
        
        # Generate recommendations
        recommendations = self._generate_recommendations(evaluation_result)
        recommendations_html = "".join(f"<li>{rec}</li>" for rec in recommendations)
        
        # Fill template
        html_content = html_template.format(
            timestamp=evaluation_result.get("timestamp", datetime.now().isoformat()),
            overall_score=evaluation_result.get("summary", {}).get("overall_score", 0),
            overall_pass_rate=evaluation_result.get("summary", {}).get("overall_pass_rate", 0),
            total_evaluations=evaluation_result.get("summary", {}).get("total_evaluations", 0),
            evaluator_sections=evaluator_sections,
            recommendations=recommendations_html
        )
        
        # Write HTML file
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report saved to {output_path}")

    def _generate_recommendations(self, evaluation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evaluation results"""
        recommendations = []
        
        summary = evaluation_result.get("summary", {})
        overall_score = summary.get("overall_score", 0)
        pass_rate = summary.get("overall_pass_rate", 0)
        
        if overall_score < 0.7:
            recommendations.append("Overall performance is below target. Consider reviewing agent configuration and model selection.")
        
        if pass_rate < 0.8:
            recommendations.append("Pass rate is low. Investigate failing evaluations and address common issues.")
        
        # Check specific evaluator results
        evaluator_results = evaluation_result.get("evaluator_results", {})
        
        # Performance recommendations
        if "performance" in evaluator_results:
            perf_result = evaluator_results["performance"]
            if perf_result.get("average_score", 0) < 0.7:
                recommendations.append("Performance issues detected. Consider optimizing prompts, using faster models, or increasing resources.")
        
        # Cost recommendations
        if "cost" in evaluator_results:
            cost_result = evaluator_results["cost"]
            aggregate = cost_result.get("aggregate_metrics", {})
            if aggregate.get("total_cost", 0) > 50:  # $50 threshold
                recommendations.append("High costs detected. Consider using more efficient models or implementing caching.")
        
        # Skill invocation recommendations
        if "skill_invocation" in evaluator_results:
            skill_result = evaluator_results["skill_invocation"]
            if skill_result.get("pass_rate", 0) < 0.8:
                recommendations.append("Skill invocation issues detected. Review skill definitions and timing.")
        
        if not recommendations:
            recommendations.append("All metrics are within acceptable ranges. Continue monitoring for trends.")
        
        return recommendations


def main():
    """Main entry point for visualization"""
    parser = argparse.ArgumentParser(description="Generate visualizations from evaluation results")
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="JSON file containing evaluation results"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Output directory for visualizations (default: current directory)"
    )
    
    parser.add_argument(
        "--dashboard", "-d",
        action="store_true",
        help="Generate performance dashboard"
    )
    
    parser.add_argument(
        "--trends", "-t",
        action="store_true",
        help="Generate trend analysis"
    )
    
    parser.add_argument(
        "--models", "-m",
        action="store_true",
        help="Generate model comparison"
    )
    
    parser.add_argument(
        "--html", "-H",
        action="store_true",
        help="Generate HTML report"
    )
    
    args = parser.parse_args()
    
    # Load evaluation results
    try:
        with open(args.input, 'r') as f:
            evaluation_result = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {args.input} not found")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input}: {e}")
        return
    
    # Initialize visualizer
    visualizer = EvaluationVisualizer()
    
    # Generate requested visualizations
    if args.dashboard:
        visualizer.create_performance_dashboard(
            evaluation_result, 
            f"{args.output_dir}/performance_dashboard.png"
        )
    
    if args.trends:
        visualizer.create_trend_analysis(
            evaluation_result,
            f"{args.output_dir}/trend_analysis.png"
        )
    
    if args.models:
        visualizer.create_model_comparison(
            evaluation_result,
            f"{args.output_dir}/model_comparison.png"
        )
    
    if args.html:
        visualizer.generate_html_report(
            evaluation_result,
            f"{args.output_dir}/evaluation_report.html"
        )
    
    # Generate all if no specific option
    if not any([args.dashboard, args.trends, args.models, args.html]):
        visualizer.create_performance_dashboard(
            evaluation_result,
            f"{args.output_dir}/performance_dashboard.png"
        )
        visualizer.create_trend_analysis(
            evaluation_result,
            f"{args.output_dir}/trend_analysis.png"
        )
        visualizer.create_model_comparison(
            evaluation_result,
            f"{args.output_dir}/model_comparison.png"
        )
        visualizer.generate_html_report(
            evaluation_result,
            f"{args.output_dir}/evaluation_report.html"
        )


if __name__ == "__main__":
    main()
