#!/usr/bin/env python3
"""
Langfuse Integration Test Script
Demonstrates real Langfuse integration capabilities
"""

import os
import sys
import logging
from pathlib import Path

# Add framework to path
sys.path.append(str(Path(__file__).parent))

from main import TracingEvaluationFramework
from integrations.langfuse_client import create_langfuse_client, TraceFilter
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_langfuse_integration():
    """Test Langfuse integration functionality"""
    print("🔗 Testing Langfuse Integration")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv('LANGFUSE_API_KEY')
    base_url = os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')
    
    if not api_key:
        print("⚠️  LANGFUSE_API_KEY not set")
        print("   Set environment variable to test real integration")
        print("   Example: export LANGFUSE_API_KEY=your-api-key")
        print("   Running with sample data instead...")
        test_sample_integration()
        return
    
    print(f"🔑 Using Langfuse at: {base_url}")
    
    try:
        # Test 1: Create Langfuse client
        print("\n1️⃣  Testing Langfuse client creation...")
        client = create_langfuse_client()
        print("✅ Langfuse client created successfully")
        
        # Test 2: Health check
        print("\n2️⃣  Testing Langfuse health check...")
        health = client.health_check()
        print(f"   Status: {health.get('status')}")
        if health.get('status') == 'healthy':
            print("✅ Langfuse connection healthy")
        else:
            print("⚠️  Langfuse connection issues detected")
        
        # Test 3: Fetch traces
        print("\n3️⃣  Testing trace fetching...")
        filters = TraceFilter(limit=10, from_date=datetime.utcnow() - timedelta(days=1))
        traces = client.fetch_traces(filters)
        print(f"✅ Fetched {len(traces)} traces")
        
        if traces:
            # Show sample trace
            sample = traces[0]
            print(f"   Sample trace ID: {sample.get('id')}")
            print(f"   Timestamp: {sample.get('timestamp')}")
            print(f"   Events: {len(sample.get('events', []))}")
        
        # Test 4: Framework integration
        print("\n4️⃣  Testing framework integration...")
        framework = TracingEvaluationFramework()
        framework_traces = framework.fetch_real_traces(5)
        print(f"✅ Framework fetched {len(framework_traces)} traces")
        
        # Test 5: Run evaluation
        if framework_traces:
            print("\n5️⃣  Running evaluation on real traces...")
            result = framework.evaluate_traces(framework_traces, ['skill_invocation', 'performance'])
            summary = result.get('summary', {})
            print(f"   Overall Score: {summary.get('overall_score', 0):.3f}")
            print(f"   Pass Rate: {summary.get('overall_pass_rate', 0):.1%}")
            print("✅ Evaluation completed successfully")
        
        print("\n🎉 Langfuse integration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Langfuse integration test failed: {e}")
        logger.exception("Langfuse integration test failed")
        print("   This might be expected if Langfuse is not accessible")
        print("   Check your API key and network connection")

def test_sample_integration():
    """Test integration with sample data when Langfuse is not available"""
    print("\n🧪 Testing with Sample Data")
    print("=" * 30)
    
    try:
        # Initialize framework
        framework = TracingEvaluationFramework()
        print("✅ Framework initialized without Langfuse")
        
        # Generate sample traces
        from example_usage import generate_sample_traces
        traces = generate_sample_traces(10)
        print(f"✅ Generated {len(traces)} sample traces")
        
        # Run evaluation
        result = framework.evaluate_traces(traces, ['skill_invocation', 'performance'])
        summary = result.get('summary', {})
        print(f"✅ Evaluation completed")
        print(f"   Overall Score: {summary.get('overall_score', 0):.3f}")
        print(f"   Pass Rate: {summary.get('overall_pass_rate', 0):.1%}")
        
        print("\n🎉 Sample integration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Sample integration test failed: {e}")
        logger.exception("Sample integration test failed")

def demonstrate_cli_usage():
    """Demonstrate CLI usage examples"""
    print("\n💻 CLI Usage Examples")
    print("=" * 30)
    
    examples = [
        {
            "description": "Fetch and evaluate real traces",
            "command": "python cli.py --langfuse --count 50 --evaluators skill_invocation,performance"
        },
        {
            "description": "Stream real-time evaluation",
            "command": "python cli.py --langfuse-stream --duration 30 --evaluators all"
        },
        {
            "description": "Filter by user ID",
            "command": "python cli.py --langfuse --user-id user-123 --evaluators security,compliance"
        },
        {
            "description": "Filter by tags",
            "command": "python cli.py --langfuse --tags production critical --evaluators all"
        },
        {
            "description": "Generate visualizations with real data",
            "command": "python cli.py --langfuse --count 100 --visualize --report-dir ./real-data-reports"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}:")
        print(f"   {example['command']}")

def show_configuration_guide():
    """Show configuration guide"""
    print("\n⚙️  Configuration Guide")
    print("=" * 30)
    
    config_info = [
        {
            "variable": "LANGFUSE_API_KEY",
            "description": "Your Langfuse API key",
            "example": "export LANGFUSE_API_KEY=sk-lf-..."
        },
        {
            "variable": "LANGFUSE_BASE_URL",
            "description": "Langfuse server URL",
            "example": "export LANGFUSE_BASE_URL=https://cloud.langfuse.com"
        },
        {
            "variable": "LANGFUSE_TIMEOUT",
            "description": "Request timeout in seconds",
            "example": "export LANGFUSE_TIMEOUT=30"
        },
        {
            "variable": "LANGFUSE_MAX_RETRIES",
            "description": "Maximum retry attempts",
            "example": "export LANGFUSE_MAX_RETRIES=3"
        },
        {
            "variable": "LANGFUSE_BATCH_SIZE",
            "description": "Batch size for trace fetching",
            "example": "export LANGFUSE_BATCH_SIZE=1000"
        },
        {
            "variable": "LANGFUSE_ENABLE_STREAMING",
            "description": "Enable real-time streaming",
            "example": "export LANGFUSE_ENABLE_STREAMING=true"
        }
    ]
    
    for config in config_info:
        print(f"\n{config['variable']}:")
        print(f"   Description: {config['description']}")
        print(f"   Example: {config['example']}")

def main():
    """Main test function"""
    print("🚀 Langfuse Integration Test Suite")
    print("=" * 50)
    
    # Run integration test
    test_langfuse_integration()
    
    # Show CLI examples
    demonstrate_cli_usage()
    
    # Show configuration guide
    show_configuration_guide()
    
    print("\n📚 Additional Resources:")
    print("   - Documentation: docs/AI-AGENT-EVALUATION-FRAMEWORK.md")
    print("   - Next Enhancements: docs/NEXT-ENHANCEMENTS.md")
    print("   - API Reference: Check CLI help with --help")

if __name__ == "__main__":
    main()
