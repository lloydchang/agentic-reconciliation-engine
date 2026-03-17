#!/usr/bin/env python3
"""
CLI Tool for AI Agent Tracing Evaluation

Command-line interface for running evaluations on Pi-Mono agent traces.
"""

import argparse
import sys
import os
from pathlib import Path

# Add framework to path
sys.path.append(str(Path(__file__).parent))

from main import TracingEvaluationFramework
from visualization import EvaluationVisualizer


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Evaluate AI agent traces from Langfuse",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate traces from file
  python cli.py --file traces.json

  # Run specific evaluators
  python cli.py --file traces.json --evaluators skill_invocation performance

  # Generate full report with visualizations
  python cli.py --file traces.json --visualize --report-dir reports/

  # Run tests
  python cli.py --test

  # Show available evaluators
  python cli.py --list-evaluators
        """
    )

    parser.add_argument(
        "--file", "-f",
        help="JSON file containing trace data"
    )

    parser.add_argument(
        "--evaluators", "-e",
        nargs="+",
        choices=["skill_invocation", "performance", "cost", "all"],
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
        "--visualize", "-v",
        action="store_true",
        help="Generate visualizations"
    )

    parser.add_argument(
        "--report-dir", "-r",
        default="reports/",
        help="Directory for reports and visualizations (default: reports/)"
    )

    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run test suite"
    )

    parser.add_argument(
        "--list-evaluators", "-l",
        action="store_true",
        help="List available evaluators"
    )

    parser.add_argument(
        "--generate-sample", "-s",
        type=int,
        help="Generate sample traces (specify number)"
    )

    args = parser.parse_args()

    # Handle special commands
    if args.test:
        run_tests()
        return

    if args.list_evaluators:
        list_evaluators()
        return

    if args.generate_sample:
        generate_sample_data(args.generate_sample)
        return

    # Main evaluation workflow
    if not args.file:
        print("Error: --file required for evaluation")
        parser.print_help()
        sys.exit(1)

    run_evaluation(args)


def run_evaluation(args):
    """Run the evaluation workflow"""
    print("🚀 AI Agent Tracing Evaluation")
    print("=" * 50)

    # Initialize framework
    framework = TracingEvaluationFramework()

    # Load traces
    print(f"📂 Loading traces from {args.file}")
    traces = framework.load_traces_from_file(args.file)
    if not traces:
        print("❌ No traces found to evaluate")
        sys.exit(1)

    print(f"✅ Loaded {len(traces)} traces")

    # Determine evaluators
    evaluators = args.evaluators
    if "all" in evaluators:
        evaluators = None  # Run all

    # Run evaluation
    print(f"🔍 Running evaluation with evaluators: {', '.join(evaluators or list(framework.evaluators.keys()))}")
    result = framework.evaluate_traces(traces, evaluators)

    # Generate report
    print("📊 Generating report...")
    report = framework.generate_report(result, args.format)

    # Output handling
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"✅ Report saved to {args.output}")
    else:
        print("\n" + "=" * 50)
        print(report)

    # Visualization
    if args.visualize:
        generate_visualizations(framework, result, args.report_dir)


def generate_visualizations(framework, result, report_dir):
    """Generate visualizations"""
    print(f"🎨 Generating visualizations in {report_dir}...")

    # Create directory
    Path(report_dir).mkdir(parents=True, exist_ok=True)

    try:
        visualizer = EvaluationVisualizer()

        # Generate various visualizations
        visualizer.create_performance_dashboard(
            result,
            f"{report_dir}/performance_dashboard.png"
        )

        visualizer.create_trend_analysis(
            result,
            f"{report_dir}/trend_analysis.png"
        )

        visualizer.create_model_comparison(
            result,
            f"{report_dir}/model_comparison.png"
        )

        visualizer.generate_html_report(
            result,
            f"{report_dir}/evaluation_report.html"
        )

        print("✅ Visualizations generated successfully")

    except ImportError as e:
        print(f"⚠️  Visualization skipped: {e}")
        print("   Install visualization dependencies: pip install matplotlib seaborn plotly")


def run_tests():
    """Run the test suite"""
    print("🧪 Running test suite...")

    try:
        from tests.test_evaluators import run_tests as run_test_suite
        test_results = run_test_suite()

        print("\n" + "=" * 30 + " TEST RESULTS " + "=" * 30)
        print(f"Tests Run: {test_results['tests_run']}")
        print(f"Failures: {test_results['failures']}")
        print(f"Errors: {test_results['errors']}")

        if test_results['success']:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            sys.exit(1)

    except ImportError:
        print("❌ Test suite not found. Run from evaluation framework directory.")
        sys.exit(1)


def list_evaluators():
    """List available evaluators"""
    print("📋 Available Evaluators")
    print("=" * 30)

    evaluators = {
        "skill_invocation": "Evaluates proper skill invocation for GitOps operations",
        "performance": "Analyzes latency, throughput, and resource utilization",
        "cost": "Evaluates cost efficiency and spending patterns"
    }

    for name, description in evaluators.items():
        print(f"• {name}")
        print(f"  {description}")
        print()


def generate_sample_data(num_traces):
    """Generate sample trace data"""
    print(f"🎯 Generating {num_traces} sample traces...")

    try:
        from example_usage import generate_sample_traces

        traces = generate_sample_traces(num_traces)

        # Save to file
        filename = f"sample_traces_{num_traces}.json"
        with open(filename, 'w') as f:
            import json
            json.dump({"traces": traces}, f, indent=2)

        print(f"✅ Sample data saved to {filename}")

        # Show summary
        operations = {}
        models = {}
        for trace in traces:
            op = trace.get("attributes", {}).get("operation_type", "unknown")
            model = trace.get("attributes", {}).get("model", "unknown")
            operations[op] = operations.get(op, 0) + 1
            models[model] = models.get(model, 0) + 1

        print("📊 Data Summary:")
        print(f"  Operations: {operations}")
        print(f"  Models: {models}")

    except ImportError:
        print("❌ Example usage module not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
