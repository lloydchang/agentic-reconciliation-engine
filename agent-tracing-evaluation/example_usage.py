#!/usr/bin/env python3
"""
Example Usage Script for AI Agent Tracing Evaluation Framework

Demonstrates how to use the evaluation framework with sample data.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add framework to path
sys.path.append(str(Path(__file__).parent))

from main import TracingEvaluationFramework
# from visualization import EvaluationVisualizer  # Commented out due to dependency issues


def generate_sample_traces(num_traces: int = 50) -> list:
    """Generate realistic sample trace data for demonstration"""
    
    models = [
        "anthropic:claude-3-5-sonnet-20241022",
        "anthropic:claude-3-haiku-20240307",
        "openai:gpt-4",
        "openai:gpt-3.5-turbo"
    ]
    
    operations = [
        "cost-optimization", "security-scan", "deployment-strategy",
        "infrastructure-provisioning", "database-maintenance",
        "cluster-scaling", "network-configuration", "secret-rotation",
        "simple-query", "health-check", "log-analysis"
    ]
    
    traces = []
    base_timestamp = datetime.now().timestamp() * 1000  # Convert to milliseconds
    
    for i in range(num_traces):
        # Random model and operation
        model = random.choice(models)
        operation = random.choice(operations)
        
        # Generate realistic metrics based on model
        if "claude-3-5-sonnet" in model:
            input_tokens = random.randint(800, 2000)
            output_tokens = random.randint(200, 800)
            duration_ms = random.randint(500, 2000)
            memory_mb = random.randint(400, 1200)
            cpu_percent = random.randint(30, 70)
        elif "claude-3-haiku" in model:
            input_tokens = random.randint(400, 1200)
            output_tokens = random.randint(100, 400)
            duration_ms = random.randint(200, 800)
            memory_mb = random.randint(200, 600)
            cpu_percent = random.randint(20, 50)
        elif "gpt-4" in model:
            input_tokens = random.randint(1000, 2500)
            output_tokens = random.randint(300, 1000)
            duration_ms = random.randint(800, 3000)
            memory_mb = random.randint(600, 1500)
            cpu_percent = random.randint(40, 80)
        else:  # gpt-3.5-turbo
            input_tokens = random.randint(200, 800)
            output_tokens = random.randint(50, 300)
            duration_ms = random.randint(100, 500)
            memory_mb = random.randint(100, 400)
            cpu_percent = random.randint(10, 40)
        
        # Determine if skill should be invoked
        should_use_skill = operation in [
            "cost-optimization", "security-scan", "deployment-strategy",
            "infrastructure-provisioning", "database-maintenance",
            "cluster-scaling", "network-configuration", "secret-rotation"
        ]
        
        # Simulate skill invocation with some errors
        skill_invoked = should_use_skill and random.random() > 0.2  # 80% success rate
        
        # Generate events
        events = []
        if skill_invoked:
            events.append({
                "name": "skill_loaded",
                "level": "info",
                "timestamp": base_timestamp + i * 60000 + 1000  # 1 minute after start
            })
        
        events.append({
            "name": "workflow_started",
            "level": "info",
            "timestamp": base_timestamp + i * 60000 + 2000  # 2 minutes after start
        })
        
        # Add some error events
        if random.random() < 0.1:  # 10% error rate
            events.append({
                "name": "error",
                "level": "error",
                "timestamp": base_timestamp + i * 60000 + 3000
            })
        
        events.append({
            "name": "response",
            "level": "info",
            "timestamp": base_timestamp + i * 60000 + duration_ms
        })
        
        trace = {
            "id": f"trace-{i+1:03d}",
            "timestamp": int(base_timestamp + i * 60000),
            "duration": {"duration_ms": duration_ms},
            "attributes": {
                "operation_type": operation,
                "skill_invoked": skill_invoked,
                "model": model,
                "memory_usage_mb": memory_mb,
                "cpu_usage_percent": cpu_percent
            },
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "events": events
        }
        
        traces.append(trace)
    
    return traces


def demonstrate_basic_evaluation():
    """Demonstrate basic evaluation functionality"""
    print("🔍 Basic Evaluation Demonstration")
    print("=" * 50)
    
    # Generate sample data
    traces = generate_sample_traces(10)
    
    # Save to file
    sample_file = "sample_traces.json"
    with open(sample_file, 'w') as f:
        json.dump({"traces": traces}, f, indent=2)
    
    print(f"Generated {len(traces)} sample traces in {sample_file}")
    
    # Initialize framework
    framework = TracingEvaluationFramework()
    
    # Run evaluation
    result = framework.evaluate_traces(traces, ["skill_invocation", "performance", "cost"])
    
    # Generate summary report
    report = framework.generate_report(result, "summary")
    print("\n📊 Evaluation Results:")
    print(report)


def demonstrate_visualization():
    """Demonstrate visualization functionality"""
    print("\n🎨 Visualization Demonstration")
    print("=" * 50)
    print("⚠️  Visualization skipped due to missing dependencies")
    print("   Install with: pip install matplotlib seaborn plotly")
    print("   Then uncomment visualization imports and calls")
    return


def demonstrate_batch_analysis():
    """Demonstrate batch analysis capabilities"""
    print("\n📊 Batch Analysis Demonstration")
    print("=" * 50)
    
    # Generate larger sample dataset
    traces = generate_sample_traces(100)
    
    # Save to file
    sample_file = "batch_traces.json"
    with open(sample_file, 'w') as f:
        json.dumps({"traces": traces}, f, indent=2)
    
    print(f"Generated {len(traces)} sample traces for batch analysis")
    
    # Initialize framework
    framework = TracingEvaluationFramework()
    
    # Run evaluation with all evaluators
    result = framework.evaluate_traces(traces)
    
    # Generate detailed report
    report = framework.generate_report(result, "detailed")
    print("\n📋 Detailed Batch Analysis Results:")
    print(report)
    
    # Extract key insights
    summary = result["summary"]
    print(f"\n💡 Key Insights:")
    print(f"  • Overall Score: {summary['overall_score']:.3f}")
    print(f"  • Pass Rate: {summary['overall_pass_rate']:.1%}")
    print(f"  • Total Evaluations: {summary['total_evaluations']}")
    
    # Check individual evaluator performance
    evaluator_summaries = summary.get("evaluator_summaries", {})
    for evaluator, eval_summary in evaluator_summaries.items():
        avg_score = eval_summary.get("average_score", 0)
        pass_rate = eval_summary.get("pass_rate", 0)
        print(f"  • {evaluator.title()}:")
        print(f"    - Average Score: {avg_score:.3f}")
        print(f"    - Pass Rate: {pass_rate:.1%}")


def demonstrate_trend_analysis():
    """Demonstrate trend analysis over time"""
    print("\n📈 Trend Analysis Demonstration")
    print("=" * 50)
    print("⚠️  Trend analysis skipped due to missing dependencies")
    print("   Install with: pip install matplotlib seaborn plotly")
    return


def demonstrate_cost_optimization():
    """Demonstrate cost optimization analysis"""
    print("\n💰 Cost Optimization Demonstration")
    print("=" * 50)
    
    # Generate traces with different cost patterns
    traces = []
    
    # High-cost traces (inefficient)
    for i in range(20):
        traces.append({
            "id": f"expensive-trace-{i+1:03d}",
            "timestamp": int((datetime.now().timestamp() - 6*24*60*60) * 1000) + i * 60000,
            "duration": {"duration_ms": 3000},
            "attributes": {
                "operation_type": "cost-optimization",
                "skill_invoked": True,
                "model": "openai:gpt-4"  # Expensive model
            },
            "usage": {
                "input_tokens": 3000,  # High token usage
                "output_tokens": 1500,
                "total_tokens": 4500
            },
            "events": [
                {"name": "skill_loaded", "level": "info", "timestamp": 1000},
                {"name": "workflow_started", "level": "info", "timestamp": 2000},
                {"name": "response", "level": "info", "timestamp": 5000}
            ]
        })
    
    # Low-cost traces (efficient)
    for i in range(20):
        traces.append({
            "id": f"efficient-trace-{i+1:03d}",
            "timestamp": int((datetime.now().timestamp() - 3*24*60*60) * 1000) + i * 60000,
            "duration": {"duration_ms": 800},
            "attributes": {
                "operation_type": "cost-optimization",
                "skill_invoked": True,
                "model": "anthropic:claude-3-haiku-20240307"  # Cheaper model
            },
            "usage": {
                "input_tokens": 500,   # Lower token usage
                "output_tokens": 250,
                "total_tokens": 750
            },
            "events": [
                {"name": "skill_loaded", "level": "info", "timestamp": 1000},
                {"name": "workflow_started", "level": "info", "timestamp": 1500},
                {"name": "response", "level": "info", "timestamp": 1800}
            ]
        })
        
    # Save to file
    sample_file = "visualization_traces.json"
    with open(sample_file, 'w') as f:
        json.dump({"traces": traces}, f, indent=2)
        
    print(f"Generated {len(traces)} traces for cost comparison")
        
    # Initialize framework
    framework = TracingEvaluationFramework()
        
    # Run cost-focused evaluation
    result = framework.evaluate_traces(traces, ["cost"])
    
    # Generate cost report
    cost_evaluator = framework.evaluators["cost"]
    cost_report = cost_evaluator.generate_cost_report(result["evaluator_results"]["cost"])
    
    print("\n💰 Cost Analysis Results:")
    print(cost_report)
    
    # Show cost optimization recommendations
    aggregate_metrics = result["evaluator_results"]["cost"]["aggregate_metrics"]
    print(f"\n💡 Cost Optimization Insights:")
    print(f"  • Total Cost: ${aggregate_metrics['total_cost']:.2f}")
    print(f"  • Average Cost per Request: ${aggregate_metrics['average_cost_per_request']:.4f}")
    print(f"  • Overall Efficiency: {aggregate_metrics['overall_efficiency_tokens_per_dollar']:.0f} tokens/$")
    
    if aggregate_metrics['total_cost'] > 100:
        print("  ⚠️  High total cost detected - consider model optimization")
    
    if aggregate_metrics['overall_efficiency_tokens_per_dollar'] < 50000:
        print("  ⚠️  Low efficiency detected - consider prompt optimization")


def main():
    """Main demonstration function"""
    print("🚀 AI Agent Tracing Evaluation Framework - Usage Demonstration")
    print("=" * 60)
    
    try:
        # Run all demonstrations
        demonstrate_basic_evaluation()
        demonstrate_visualization()
        demonstrate_batch_analysis()
        demonstrate_trend_analysis()
        demonstrate_cost_optimization()
        
        print("\n" + "=" * 60)
        print("✅ All demonstrations completed successfully!")
        print("\n📚 Next Steps:")
        print("  1. Review generated files and visualizations")
        print("  2. Replace sample data with real Langfuse traces")
        print("  3. Customize evaluators for your specific needs")
        print("  4. Integrate into your CI/CD pipeline")
        print("  5. Set up monitoring and alerting")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
