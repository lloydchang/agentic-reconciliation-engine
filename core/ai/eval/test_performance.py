#!/usr/bin/env python3
"""
Performance Optimization Test Suite
Tests and validates performance improvements
"""

import asyncio
import time
import sys
from pathlib import Path

# Add framework to path
sys.path.append(str(Path(__file__).parent))

from main import TracingEvaluationFramework
from performance.optimization import create_optimized_framework, EvaluationCache, BatchProcessor

def generate_test_traces(count: int = 1000) -> list:
    """Generate test traces for performance testing"""
    traces = []
    
    for i in range(count):
        trace = {
            "id": f"perf-test-{i}",
            "timestamp": "2026-03-17T14:00:00Z",
            "events": [
                {
                    "name": "skill_invocation",
                    "timestamp": "2026-03-17T14:00:01Z",
                    "level": "INFO" if i % 10 != 0 else "ERROR",
                    "type": "SKILL_EXECUTION",
                    "input": {"operation": "deploy", "trace_id": i},
                    "output": {"success": i % 10 != 0, "duration": 100 + (i % 500)}
                }
            ],
            "attributes": {
                "operation_type": "deploy",
                "model": "gpt-4",
                "total_duration": 100 + (i % 500),
                "event_count": 1,
                "error_count": 1 if i % 10 == 0 else 0,
                "success_rate": 0.9 if i % 10 != 0 else 0.1
            }
        }
        traces.append(trace)
    
    return traces

def test_cache_performance():
    """Test evaluation cache performance"""
    print("🚀 Testing Cache Performance")
    print("=" * 40)
    
    # Create framework with cache
    framework = TracingEvaluationFramework()
    optimized_framework = create_optimized_framework(framework, cache_size=100)
    
    # Generate test traces
    test_traces = generate_test_traces(100)
    evaluators = ['skill_invocation', 'performance', 'security']
    
    print(f"📊 Generated {len(test_traces)} test traces")
    
    # First run (cache miss)
    print("\n🔍 First evaluation (cache miss)...")
    start_time = time.time()
    result1 = await optimized_framework.evaluate_traces_optimized(
        test_traces, evaluators, use_cache=True
    )
    first_duration = time.time() - start_time
    print(f"   Duration: {first_duration:.3f}s")
    
    # Second run (cache hit)
    print("\n💾 Second evaluation (cache hit)...")
    start_time = time.time()
    result2 = await optimized_framework.evaluate_traces_optimized(
        test_traces, evaluators, use_cache=True
    )
    second_duration = time.time() - start_time
    print(f"   Duration: {second_duration:.3f}s")
    
    # Calculate cache benefit
    speedup = first_duration / second_duration if second_duration > 0 else 0
    print(f"\n📈 Cache Performance:")
    print(f"   Speedup: {speedup:.2f}x")
    print(f"   Time saved: {(first_duration - second_duration):.3f}s ({((first_duration - second_duration) / first_duration * 100):.1f}%)")
    
    # Get cache stats
    cache_stats = optimized_framework.get_performance_stats()['cache_stats']
    print(f"   Cache entries: {cache_stats['total_entries']}")
    print(f"   Cache usage: {cache_stats['usage_percent']:.1f}%")

async def test_parallel_processing():
    """Test parallel vs sequential processing"""
    print("\n🚀 Testing Parallel Processing")
    print("=" * 40)
    
    framework = TracingEvaluationFramework()
    optimized_framework = create_optimized_framework(framework, max_workers=4)
    
    # Generate larger test set
    test_traces = generate_test_traces(500)
    evaluators = ['skill_invocation', 'performance', 'security', 'compliance']
    
    print(f"📊 Generated {len(test_traces)} test traces")
    
    # Sequential processing
    print("\n🔄 Sequential processing...")
    start_time = time.time()
    result_seq = await optimized_framework.evaluate_traces_optimized(
        test_traces, evaluators, use_cache=False, use_parallel=False
    )
    sequential_duration = time.time() - start_time
    print(f"   Duration: {sequential_duration:.3f}s")
    
    # Parallel processing
    print("\n⚡ Parallel processing...")
    start_time = time.time()
    result_par = await optimized_framework.evaluate_traces_optimized(
        test_traces, evaluators, use_cache=False, use_parallel=True
    )
    parallel_duration = time.time() - start_time
    print(f"   Duration: {parallel_duration:.3f}s")
    
    # Calculate parallel benefit
    speedup = sequential_duration / parallel_duration if parallel_duration > 0 else 0
    print(f"\n📈 Parallel Performance:")
    print(f"   Speedup: {speedup:.2f}x")
    print(f"   Time saved: {(sequential_duration - parallel_duration):.3f}s ({((sequential_duration - parallel_duration) / sequential_duration * 100):.1f}%)")
    
    # Compare results consistency
    summary_seq = result_seq['summary']
    summary_par = result_par['summary']
    
    print(f"\n🔍 Results Consistency:")
    print(f"   Sequential score: {summary_seq['overall_score']:.3f}")
    print(f"   Parallel score: {summary_par['overall_score']:.3f}")
    print(f"   Difference: {abs(summary_seq['overall_score'] - summary_par['overall_score']):.6f}")

async def test_memory_efficiency():
    """Test memory-efficient batch processing"""
    print("\n🚀 Testing Memory Efficiency")
    print("=" * 40)
    
    # Test with different batch sizes
    batch_sizes = [50, 100, 200, 500]
    trace_counts = [100, 500, 1000, 2000]
    
    for batch_size in batch_sizes:
        print(f"\n📦 Batch size: {batch_size}")
        
        for trace_count in trace_counts:
            test_traces = generate_test_traces(trace_count)
            
            # Measure memory usage (simplified)
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss
            
            # Process with batch optimization
            from performance.optimization import memory_efficient_batch_processor
            
            @memory_efficient_batch_processor(batch_size=batch_size)
            def process_batch(traces):
                # Simulate processing work
                results = []
                for trace in traces:
                    result = {
                        'score': 0.8 if trace['attributes']['success_rate'] > 0.5 else 0.3,
                        'passed': trace['attributes']['success_rate'] > 0.5
                    }
                    results.append(result)
                return results
            
            start_time = time.time()
            results = process_batch(test_traces)
            duration = time.time() - start_time
            
            memory_after = process.memory_info().rss
            memory_used = (memory_after - memory_before) / 1024 / 1024  # MB
            
            print(f"   {trace_count:4d} traces: {duration:6.3f}s, {memory_used:6.1f}MB")

def test_scalability():
    """Test framework scalability with increasing trace counts"""
    print("\n🚀 Testing Scalability")
    print("=" * 40)
    
    framework = TracingEvaluationFramework()
    optimized_framework = create_optimized_framework(framework, max_workers=8)
    
    # Test with increasing trace counts
    trace_counts = [100, 500, 1000, 2000, 5000]
    evaluators = ['skill_invocation', 'performance', 'security']
    
    results = []
    
    for trace_count in trace_counts:
        print(f"\n📊 Testing {trace_count} traces...")
        test_traces = generate_test_traces(trace_count)
        
        # Measure performance
        start_time = time.time()
        result = await optimized_framework.evaluate_traces_optimized(
            test_traces, evaluators, use_cache=True, use_parallel=True
        )
        duration = time.time() - start_time
        
        traces_per_second = trace_count / duration
        results.append({
            'trace_count': trace_count,
            'duration': duration,
            'traces_per_second': traces_per_second,
            'overall_score': result['summary']['overall_score']
        })
        
        print(f"   Duration: {duration:6.3f}s")
        print(f"   Throughput: {traces_per_second:.1f} traces/s")
        print(f"   Score: {result['summary']['overall_score']:.3f}")
    
    # Analyze scalability
    print(f"\n📈 Scalability Analysis:")
    print(f"   Linear scaling expected: ~{results[0]['traces_per_second']:.1f} traces/s")
    
    for i, result in enumerate(results[1:], 1):
        expected_duration = result['trace_count'] / results[0]['traces_per_second']
        efficiency = expected_duration / result['duration']
        print(f"   {result['trace_count']:5d} traces: {efficiency:.2f}x efficiency")

async def test_performance_monitoring():
    """Test performance monitoring capabilities"""
    print("\n🚀 Testing Performance Monitoring")
    print("=" * 40)
    
    framework = TracingEvaluationFramework()
    optimized_framework = create_optimized_framework(framework)
    
    # Run multiple evaluations to collect performance data
    evaluators = ['skill_invocation', 'performance', 'security']
    
    print("Running multiple evaluations to collect performance data...")
    for i in range(5):
        test_traces = generate_test_traces(100 + i * 50)  # Varying sizes
        
        await optimized_framework.evaluate_traces_optimized(
            test_traces, evaluators, use_cache=True, use_parallel=True
        )
        
        print(f"   Evaluation {i+1} completed")
        await asyncio.sleep(0.1)  # Small delay
    
    # Get performance statistics
    perf_stats = optimized_framework.get_performance_stats()
    
    print(f"\n📊 Performance Statistics:")
    print(f"   Cache Stats:")
    cache_stats = perf_stats['cache_stats']
    print(f"     Entries: {cache_stats['total_entries']}")
    print(f"     Usage: {cache_stats['usage_percent']:.1f}%")
    print(f"     Hit rate: {cache_stats.get('hit_rate', 0):.1f}%")
    
    print(f"   Evaluator Performance:")
    for evaluator, stats in perf_stats['evaluator_performance'].items():
        print(f"     {evaluator}:")
        print(f"       Count: {stats['count']}")
        print(f"       Avg time: {stats['avg_time']:.3f}s")
        print(f"       Min/Max: {stats['min_time']:.3f}s / {stats['max_time']:.3f}s")
        print(f"       Recent avg: {stats['recent_avg']:.3f}s")
    
    slow_evaluators = perf_stats['slow_evaluators']
    if slow_evaluators:
        print(f"   Slow evaluators (>5s): {', '.join(slow_evaluators)}")
    else:
        print(f"   No slow evaluators detected")

async def main():
    """Main performance test function"""
    print("🚀 Performance Optimization Test Suite")
    print("=" * 50)
    
    try:
        # Run all performance tests
        await test_cache_performance()
        await test_parallel_processing()
        await test_memory_efficiency()
        await test_scalability()
        await test_performance_monitoring()
        
        print("\n✅ Performance optimization tests completed successfully!")
        
        print("\n📚 Performance Recommendations:")
        print("   - Enable caching for repeated evaluations")
        print("   - Use parallel processing for large trace sets")
        print("   - Monitor evaluator performance regularly")
        print("   - Optimize batch sizes for memory efficiency")
        print("   - Consider scaling workers based on workload")
        
    except Exception as e:
        print(f"\n❌ Performance test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
