#!/usr/bin/env python3
"""
Performance Optimization Module for AI Agent Evaluation Framework
Provides caching, batch processing, and performance improvements
"""

import asyncio
import hashlib
import json
import pickle
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import lru_cache, wraps
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    data: Any
    timestamp: datetime
    ttl_seconds: int = 3600  # 1 hour default
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.timestamp + timedelta(seconds=self.ttl_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'ttl_seconds': self.ttl_seconds
        }

class EvaluationCache:
    """Thread-safe evaluation results cache"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.access_times: Dict[str, datetime] = {}
        self.lock = threading.RLock()
    
    def _generate_key(self, traces: List[Dict], evaluators: List[str]) -> str:
        """Generate cache key from traces and evaluators"""
        # Create a hash of the input data
        traces_str = json.dumps(traces, sort_keys=True)
        evaluators_str = json.dumps(sorted(evaluators))
        combined = f"{traces_str}:{evaluators_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, traces: List[Dict], evaluators: List[str]) -> Optional[Dict[str, Any]]:
        """Get cached evaluation results"""
        key = self._generate_key(traces, evaluators)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    # Update access time for LRU
                    self.access_times[key] = datetime.utcnow()
                    logger.debug(f"Cache hit for key: {key[:8]}...")
                    return entry.data
                else:
                    # Remove expired entry
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
        
        return None
    
    def put(self, traces: List[Dict], evaluators: List[str], results: Dict[str, Any], ttl_seconds: int = 3600):
        """Cache evaluation results"""
        key = self._generate_key(traces, evaluators)
        entry = CacheEntry(
            data=results,
            timestamp=datetime.utcnow(),
            ttl_seconds=ttl_seconds
        )
        
        with self.lock:
            # Check cache size and evict if necessary
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            self.cache[key] = entry
            self.access_times[key] = datetime.utcnow()
            logger.debug(f"Cached results for key: {key[:8]}...")
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove from cache
        del self.cache[lru_key]
        del self.access_times[lru_key]
        logger.debug(f"Evicted LRU cache entry: {lru_key[:8]}...")
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_entries = len(self.cache)
            expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
            
            return {
                'total_entries': total_entries,
                'max_size': self.max_size,
                'usage_percent': (total_entries / self.max_size) * 100,
                'expired_entries': expired_entries,
                'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1) * 100
            }

class BatchProcessor:
    """Optimized batch processing for evaluations"""
    
    def __init__(self, max_workers: int = 4, use_processes: bool = False):
        self.max_workers = max_workers
        self.use_processes = use_processes
        
        if use_processes:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_evaluators_parallel(self, traces: List[Dict], evaluators: List[str], 
                                   evaluator_map: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple evaluators in parallel"""
        logger.info(f"Processing {len(evaluators)} evaluators with {self.max_workers} workers")
        
        # Create tasks for each evaluator
        futures = {}
        for evaluator_name in evaluators:
            if evaluator_name in evaluator_map:
                evaluator = evaluator_map[evaluator_name]
                future = self.executor.submit(self._run_evaluator_safe, evaluator, traces)
                futures[future] = evaluator_name
        
        # Collect results
        results = {}
        for future in as_completed(futures):
            evaluator_name = futures[future]
            try:
                result = future.result(timeout=300)  # 5 minute timeout
                results[evaluator_name] = result
                logger.debug(f"Evaluator {evaluator_name} completed successfully")
            except Exception as e:
                logger.error(f"Evaluator {evaluator_name} failed: {e}")
                results[evaluator_name] = {
                    'error': str(e),
                    'average_score': 0.0,
                    'pass_rate': 0.0
                }
        
        return results
    
    def _run_evaluator_safe(self, evaluator: Any, traces: List[Dict]) -> Dict[str, Any]:
        """Safely run evaluator with error handling"""
        try:
            # Check if evaluator has batch method
            if hasattr(evaluator, 'evaluate_batch'):
                return evaluator.evaluate_batch(traces)
            else:
                # Fallback to individual evaluations
                individual_results = []
                for trace in traces:
                    result = evaluator.evaluate(trace)
                    individual_results.append(result)
                
                # Aggregate individual results
                return self._aggregate_individual_results(individual_results)
        except Exception as e:
            logger.error(f"Evaluator execution failed: {e}")
            raise
    
    def _aggregate_individual_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Aggregate individual evaluation results"""
        if not results:
            return {
                'total_evaluations': 0,
                'average_score': 0.0,
                'pass_rate': 0.0
            }
        
        total_score = sum(r.get('score', 0) for r in results)
        passed_count = sum(1 for r in results if r.get('passed', False))
        
        return {
            'total_evaluations': len(results),
            'average_score': total_score / len(results),
            'pass_rate': (passed_count / len(results)) * 100,
            'individual_results': results
        }
    
    def shutdown(self):
        """Shutdown the executor"""
        self.executor.shutdown(wait=True)

class PerformanceMonitor:
    """Monitor and optimize evaluation performance"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
    
    def record_evaluation_time(self, evaluator_name: str, duration: float, trace_count: int):
        """Record evaluation performance metrics"""
        with self.lock:
            if evaluator_name not in self.metrics:
                self.metrics[evaluator_name] = []
            
            self.metrics[evaluator_name].append(duration)
            
            # Keep only last 100 measurements
            if len(self.metrics[evaluator_name]) > 100:
                self.metrics[evaluator_name] = self.metrics[evaluator_name][-100:]
        
        traces_per_second = trace_count / duration if duration > 0 else 0
        logger.info(f"Evaluation {evaluator_name}: {duration:.2f}s for {trace_count} traces ({traces_per_second:.1f} traces/s)")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            stats = {}
            for evaluator_name, times in self.metrics.items():
                if not times:
                    continue
                
                stats[evaluator_name] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'recent_avg': sum(times[-10:]) / min(len(times), 10)
                }
            
            return stats
    
    def get_slow_evaluators(self, threshold_seconds: float = 5.0) -> List[str]:
        """Get evaluators slower than threshold"""
        with self.lock:
            slow_evaluators = []
            for evaluator_name, times in self.metrics.items():
                if times and sum(times) / len(times) > threshold_seconds:
                    slow_evaluators.append(evaluator_name)
            
            return slow_evaluators

def timed_cache(ttl_seconds: int = 3600):
    """Decorator for caching function results with TTL"""
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = str(args) + str(sorted(kwargs.items()))
            
            # Check cache
            if key in cache:
                entry = cache[key]
                if not entry['expired']:
                    return entry['data']
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache[key] = {
                'data': result,
                'timestamp': datetime.utcnow(),
                'expired': False,
                'ttl_seconds': ttl_seconds
            }
            
            return result
        
        # Cleanup expired entries periodically
        def cleanup():
            current_time = datetime.utcnow()
            expired_keys = [
                k for k, v in cache.items()
                if current_time > v['timestamp'] + timedelta(seconds=v['ttl_seconds'])
            ]
            for k in expired_keys:
                del cache[k]
        
        # Schedule cleanup (simplified - in production use proper scheduler)
        if len(cache) > 100:  # Simple cleanup trigger
            cleanup()
        
        return wrapper
    return decorator

def memory_efficient_batch_processor(batch_size: int = 100):
    """Decorator for memory-efficient batch processing"""
    def decorator(func):
        @wraps(func)
        def wrapper(traces: List[Dict], *args, **kwargs):
            if len(traces) <= batch_size:
                return func(traces, *args, **kwargs)
            
            # Process in batches
            results = []
            for i in range(0, len(traces), batch_size):
                batch = traces[i:i + batch_size]
                batch_result = func(batch, *args, **kwargs)
                results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
                
                # Force garbage collection for memory efficiency
                import gc
                gc.collect()
            
            return results
        return wrapper
    return decorator

class OptimizedEvaluationFramework:
    """Performance-optimized evaluation framework"""
    
    def __init__(self, base_framework, cache_size: int = 1000, max_workers: int = 4):
        self.base_framework = base_framework
        self.cache = EvaluationCache(max_size=cache_size)
        self.batch_processor = BatchProcessor(max_workers=max_workers)
        self.performance_monitor = PerformanceMonitor()
        
        # Override evaluators with optimized versions
        self._setup_optimized_evaluators()
    
    def _setup_optimized_evaluators(self):
        """Setup optimized evaluator versions"""
        # Wrap evaluators with performance monitoring
        for name, evaluator in self.base_framework.evaluators.items():
            self.base_framework.evaluators[name] = self._wrap_evaluator(evaluator, name)
    
    def _wrap_evaluator(self, evaluator: Any, name: str):
        """Wrap evaluator with performance monitoring"""
        class OptimizedEvaluator:
            def __init__(self, original_evaluator, evaluator_name, perf_monitor):
                self.original = original_evaluator
                self.name = evaluator_name
                self.perf_monitor = perf_monitor
            
            def evaluate_batch(self, traces):
                start_time = time.time()
                
                try:
                    result = self.original.evaluate_batch(traces)
                    duration = time.time() - start_time
                    self.perf_monitor.record_evaluation_time(self.name, duration, len(traces))
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.perf_monitor.record_evaluation_time(self.name, duration, len(traces))
                    raise
            
            def evaluate(self, trace):
                # Fallback for individual evaluation
                start_time = time.time()
                try:
                    result = self.original.evaluate(trace)
                    duration = time.time() - start_time
                    self.perf_monitor.record_evaluation_time(self.name, duration, 1)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.perf_monitor.record_evaluation_time(self.name, duration, 1)
                    raise
        
        return OptimizedEvaluator(evaluator, name, self.performance_monitor)
    
    async def evaluate_traces_optimized(self, traces: List[Dict], evaluator_types: List[str] = None,
                                     use_cache: bool = True, use_parallel: bool = True) -> Dict[str, Any]:
        """Optimized trace evaluation with caching and parallel processing"""
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_result = self.cache.get(traces, evaluator_types or list(self.base_framework.evaluators.keys()))
            if cached_result:
                logger.info("Using cached evaluation results")
                return cached_result
        
        # Filter available evaluators
        if evaluator_types is None:
            evaluator_types = list(self.base_framework.evaluators.keys())
        
        available_evaluators = {}
        for evaluator_type in evaluator_types:
            if evaluator_type in self.base_framework.evaluators:
                available_evaluators[evaluator_type] = self.base_framework.evaluators[evaluator_type]
        
        # Process evaluations
        if use_parallel and len(available_evaluators) > 1:
            results = self.batch_processor.process_evaluators_parallel(
                traces, list(available_evaluators.keys()), available_evaluators
            )
        else:
            # Sequential processing
            results = {}
            for evaluator_name, evaluator in available_evaluators.items():
                try:
                    if hasattr(evaluator, 'evaluate_batch'):
                        result = evaluator.evaluate_batch(traces)
                    else:
                        # Fallback to individual evaluations
                        individual_results = []
                        for trace in traces:
                            result = evaluator.evaluate(trace)
                            individual_results.append(result)
                        result = self.batch_processor._aggregate_individual_results(individual_results)
                    results[evaluator_name] = result
                except Exception as e:
                    logger.error(f"Evaluation failed for {evaluator_name}: {e}")
                    results[evaluator_name] = {
                        'error': str(e),
                        'average_score': 0.0,
                        'pass_rate': 0.0
                    }
        
        # Generate summary
        summary = self.base_framework._generate_summary(results)
        
        evaluation_results = {
            'summary': summary,
            'evaluator_results': results,
            'aggregate_metrics': {
                'total_evaluations': len(traces),
                'evaluators_run': evaluator_types,
                'timestamp': datetime.now().isoformat(),
                'processing_time': time.time() - start_time,
                'cache_used': use_cache,
                'parallel_processing': use_parallel
            }
        }
        
        # Cache results
        if use_cache:
            self.cache.put(traces, evaluator_types or list(self.base_framework.evaluators.keys()), evaluation_results)
        
        return evaluation_results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'cache_stats': self.cache.get_stats(),
            'evaluator_performance': self.performance_monitor.get_performance_stats(),
            'slow_evaluators': self.performance_monitor.get_slow_evaluators()
        }
    
    def clear_cache(self):
        """Clear evaluation cache"""
        self.cache.clear()
    
    def shutdown(self):
        """Shutdown optimized framework"""
        self.batch_processor.shutdown()

# Factory function
def create_optimized_framework(base_framework, cache_size: int = 1000, max_workers: int = 4) -> OptimizedEvaluationFramework:
    """Create optimized evaluation framework"""
    return OptimizedEvaluationFramework(base_framework, cache_size, max_workers)
