#!/usr/bin/env node

/**
 * AI Infrastructure Portal - Performance Profiling & Bottleneck Analysis
 * Advanced performance monitoring and optimization tools
 */

const v8 = require('v8');
const { performance, PerformanceObserver } = require('perf_hooks');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const promClient = require('prom-client');
const os = require('os');

class PerformanceProfiler {
  constructor(options = {}) {
    this.apiUrl = options.apiUrl || 'http://localhost:5001/api';
    this.dashboardUrl = options.dashboardUrl || 'http://localhost:8081';
    this.collectionInterval = options.interval || 30000; // 30 seconds
    this.profiles = [];
    this.benchmarks = new Map();
    this.bottlenecks = [];

    this.register = new promClient.Registry();

    // Performance metrics
    this.performanceMetrics = {
      responseTime: new promClient.Histogram({
        name: 'ai_portal_response_time_seconds',
        help: 'Response time for API endpoints',
        labelNames: ['endpoint', 'method'],
        buckets: [0.1, 0.5, 1, 2, 5, 10],
        registers: [this.register]
      }),

      throughput: new promClient.Gauge({
        name: 'ai_portal_throughput_requests_per_second',
        help: 'Current request throughput',
        registers: [this.register]
      }),

      memoryUsage: new promClient.Gauge({
        name: 'ai_portal_memory_usage_bytes',
        help: 'Memory usage by component',
        labelNames: ['component'],
        registers: [this.register]
      }),

      cpuUsage: new promClient.Gauge({
        name: 'ai_portal_cpu_usage_percent',
        help: 'CPU usage by component',
        labelNames: ['component'],
        registers: [this.register]
      }),

      bottleneckScore: new promClient.Gauge({
        name: 'ai_portal_bottleneck_score',
        help: 'Bottleneck severity score (0-100)',
        labelNames: ['component', 'type'],
        registers: [this.register]
      }),

      performanceScore: new promClient.Gauge({
        name: 'ai_portal_performance_score',
        help: 'Overall performance score (0-100)',
        registers: [this.register]
      })
    };

    this.startProfiling();
    this.setupPerformanceObserver();
  }

  setupPerformanceObserver() {
    // Observe performance marks and measures
    const obs = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name.startsWith('ai-portal-')) {
          this.recordPerformanceEntry(entry);
        }
      }
    });

    obs.observe({ entryTypes: ['measure', 'mark'] });
  }

  recordPerformanceEntry(entry) {
    const profile = {
      name: entry.name,
      type: entry.entryType,
      startTime: entry.startTime,
      duration: entry.duration || 0,
      timestamp: Date.now()
    };

    this.profiles.push(profile);

    // Keep only last 1000 profiles
    if (this.profiles.length > 1000) {
      this.profiles = this.profiles.slice(-500);
    }

    // Record in Prometheus if it's a measure
    if (entry.entryType === 'measure' && entry.duration) {
      const endpoint = entry.name.replace('ai-portal-', '');
      this.performanceMetrics.responseTime
        .observe({ endpoint, method: 'GET' }, entry.duration / 1000);
    }
  }

  async profileAPIEndpoints() {
    const endpoints = [
      '/health',
      '/services',
      '/metrics',
      '/agents',
      '/skills',
      '/activity'
    ];

    console.log('🔬 Profiling API endpoints...');

    for (const endpoint of endpoints) {
      try {
        performance.mark(`ai-portal-start-${endpoint}`);

        const startTime = Date.now();
        const response = await axios.get(`${this.apiUrl}${endpoint}`, {
          timeout: 10000
        });
        const endTime = Date.now();

        performance.mark(`ai-portal-end-${endpoint}`);
        performance.measure(`ai-portal-${endpoint}`, `ai-portal-start-${endpoint}`, `ai-portal-end-${endpoint}`);

        const profile = {
          endpoint,
          responseTime: endTime - startTime,
          statusCode: response.status,
          dataSize: JSON.stringify(response.data).length,
          timestamp: new Date().toISOString()
        };

        // Analyze for bottlenecks
        if (profile.responseTime > 2000) {
          this.bottlenecks.push({
            type: 'slow_api_response',
            component: 'api',
            endpoint,
            severity: profile.responseTime > 5000 ? 'high' : 'medium',
            value: profile.responseTime,
            recommendation: `Consider caching or optimizing ${endpoint}`
          });
        }

        // Update throughput metric
        this.updateThroughput();

      } catch (error) {
        console.error(`Error profiling ${endpoint}:`, error.message);
        this.bottlenecks.push({
          type: 'api_error',
          component: 'api',
          endpoint,
          severity: 'high',
          error: error.message,
          recommendation: `Fix API endpoint ${endpoint}`
        });
      }
    }
  }

  async profileSystemResources() {
    try {
      // CPU usage
      const cpuUsage = process.cpuUsage();
      const cpuPercent = (cpuUsage.user + cpuUsage.system) / 1000000; // Convert to seconds

      this.performanceMetrics.cpuUsage.set({ component: 'api' }, cpuPercent);

      // Memory usage
      const memUsage = process.memoryUsage();
      this.performanceMetrics.memoryUsage.set({ component: 'api' }, memUsage.heapUsed);

      // V8 heap statistics
      const heapStats = v8.getHeapStatistics();
      this.performanceMetrics.memoryUsage.set({ component: 'v8_heap' }, heapStats.used_heap_size);

      // System memory
      const totalMem = os.totalmem();
      const freeMem = os.freemem();
      const memUsagePercent = ((totalMem - freeMem) / totalMem) * 100;

      this.performanceMetrics.memoryUsage.set({ component: 'system' }, memUsagePercent);

      // Check for memory bottlenecks
      if (memUsagePercent > 90) {
        this.bottlenecks.push({
          type: 'high_memory_usage',
          component: 'system',
          severity: 'critical',
          value: memUsagePercent,
          recommendation: 'Consider increasing memory limits or optimizing memory usage'
        });
      }

      // Check for heap size issues
      if (heapStats.used_heap_size / heapStats.heap_size_limit > 0.8) {
        this.bottlenecks.push({
          type: 'high_heap_usage',
          component: 'nodejs',
          severity: 'high',
          value: (heapStats.used_heap_size / heapStats.heap_size_limit) * 100,
          recommendation: 'Memory leak detected - review application code'
        });
      }

    } catch (error) {
      console.error('Error profiling system resources:', error);
    }
  }

  async profileDatabaseQueries() {
    // Simulate database query profiling
    // In a real implementation, this would integrate with actual DB drivers
    try {
      const queryTimes = [50, 120, 80, 200, 90, 150]; // Simulated query times in ms

      queryTimes.forEach((time, index) => {
        if (time > 100) {
          this.bottlenecks.push({
            type: 'slow_db_query',
            component: 'database',
            queryId: `query_${index}`,
            severity: time > 200 ? 'high' : 'medium',
            value: time,
            recommendation: 'Add index or optimize query'
          });
        }
      });

      // Record average query time
      const avgQueryTime = queryTimes.reduce((a, b) => a + b) / queryTimes.length;
      this.performanceMetrics.responseTime
        .observe({ endpoint: 'database_query', method: 'SELECT' }, avgQueryTime / 1000);

    } catch (error) {
      console.error('Error profiling database queries:', error);
    }
  }

  async profileNetworkRequests() {
    try {
      // Profile external API calls
      const externalAPIs = [
        { name: 'ArgoCD', url: process.env.ARGOCD_URL || 'http://localhost:8080/api/v1/applications' },
        { name: 'Prometheus', url: process.env.PROMETHEUS_URL || 'http://localhost:9090/api/v1/query?query=up' }
      ];

      for (const api of externalAPIs) {
        try {
          const startTime = Date.now();
          const response = await axios.get(api.url, { timeout: 5000 });
          const endTime = Date.now();

          const responseTime = endTime - startTime;

          if (responseTime > 1000) {
            this.bottlenecks.push({
              type: 'slow_external_api',
              component: 'network',
              api: api.name,
              severity: 'medium',
              value: responseTime,
              recommendation: `Optimize calls to ${api.name} or implement caching`
            });
          }

          // Record network performance
          this.performanceMetrics.responseTime
            .observe({ endpoint: `external_${api.name}`, method: 'GET' }, responseTime / 1000);

        } catch (error) {
          this.bottlenecks.push({
            type: 'external_api_error',
            component: 'network',
            api: api.name,
            severity: 'high',
            error: error.message,
            recommendation: `Check connectivity to ${api.name}`
          });
        }
      }

    } catch (error) {
      console.error('Error profiling network requests:', error);
    }
  }

  updateThroughput() {
    // Calculate throughput based on recent requests
    const recentProfiles = this.profiles.filter(p =>
      Date.now() - p.timestamp < 60000 // Last minute
    );

    const throughput = recentProfiles.length / 60; // requests per second
    this.performanceMetrics.throughput.set(throughput);
  }

  async analyzeBottlenecks() {
    // Calculate bottleneck scores
    const bottleneckTypes = ['slow_api_response', 'high_memory_usage', 'slow_db_query', 'slow_external_api'];

    bottleneckTypes.forEach(type => {
      const typeBottlenecks = this.bottlenecks.filter(b => b.type === type);
      if (typeBottlenecks.length > 0) {
        const avgSeverity = typeBottlenecks.reduce((sum, b) => {
          const severityScore = b.severity === 'critical' ? 100 : b.severity === 'high' ? 75 : 50;
          return sum + severityScore;
        }, 0) / typeBottlenecks.length;

        this.performanceMetrics.bottleneckScore.set({
          component: typeBottlenecks[0].component,
          type
        }, avgSeverity);
      }
    });

    // Calculate overall performance score
    const totalBottlenecks = this.bottlenecks.length;
    const criticalBottlenecks = this.bottlenecks.filter(b => b.severity === 'critical').length;

    let performanceScore = 100;
    performanceScore -= totalBottlenecks * 2; // -2 points per bottleneck
    performanceScore -= criticalBottlenecks * 5; // -5 points per critical bottleneck
    performanceScore = Math.max(0, Math.min(100, performanceScore));

    this.performanceMetrics.performanceScore.set(performanceScore);

    console.log(`📊 Performance Score: ${performanceScore}/100 (${totalBottlenecks} bottlenecks detected)`);
  }

  async runBenchmark(name, fn, iterations = 100) {
    console.log(`🏃 Running benchmark: ${name}`);

    const times = [];

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      await fn();
      const end = performance.now();
      times.push(end - start);
    }

    const avgTime = times.reduce((a, b) => a + b) / times.length;
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    const p95Time = times.sort((a, b) => a - b)[Math.floor(times.length * 0.95)];

    const benchmark = {
      name,
      iterations,
      avgTime,
      minTime,
      maxTime,
      p95Time,
      timestamp: new Date().toISOString()
    };

    this.benchmarks.set(name, benchmark);

    console.log(`✅ Benchmark ${name}: ${avgTime.toFixed(2)}ms avg, ${p95Time.toFixed(2)}ms p95`);

    return benchmark;
  }

  async benchmarkAPI() {
    await this.runBenchmark('API Health Check', async () => {
      await axios.get(`${this.apiUrl}/health`);
    });

    await this.runBenchmark('API Services List', async () => {
      await axios.get(`${this.apiUrl}/services`);
    });

    await this.runBenchmark('API Metrics Fetch', async () => {
      await axios.get(`${this.apiUrl}/metrics`);
    });
  }

  startProfiling() {
    // Initial profiling run
    this.runProfilingCycle();

    // Set up periodic profiling
    setInterval(() => {
      this.runProfilingCycle();
    }, this.collectionInterval);

    console.log(`🚀 Performance profiler started - profiling every ${this.collectionInterval/1000}s`);
  }

  async runProfilingCycle() {
    try {
      await Promise.all([
        this.profileAPIEndpoints(),
        this.profileSystemResources(),
        this.profileDatabaseQueries(),
        this.profileNetworkRequests()
      ]);

      await this.analyzeBottlenecks();

      // Clean up old bottlenecks (keep last 24 hours)
      const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
      this.bottlenecks = this.bottlenecks.filter(b => new Date(b.timestamp).getTime() > oneDayAgo);

    } catch (error) {
      console.error('Error in profiling cycle:', error);
    }
  }

  getProfiles(limit = 100) {
    return this.profiles.slice(-limit);
  }

  getBottlenecks(limit = 50) {
    return this.bottlenecks.slice(-limit);
  }

  getBenchmarks() {
    return Array.from(this.benchmarks.values());
  }

  getMetrics() {
    return this.register.metrics();
  }

  async saveProfileReport(filename = 'performance-report.json') {
    const report = {
      timestamp: new Date().toISOString(),
      profiles: this.getProfiles(),
      bottlenecks: this.getBottlenecks(),
      benchmarks: this.getBenchmarks(),
      summary: {
        totalProfiles: this.profiles.length,
        totalBottlenecks: this.bottlenecks.length,
        activeBenchmarks: this.benchmarks.size,
        performanceScore: await this.getPerformanceScore()
      }
    };

    await fs.promises.writeFile(filename, JSON.stringify(report, null, 2));
    console.log(`📄 Performance report saved to ${filename}`);
  }

  async getPerformanceScore() {
    try {
      const metrics = await this.register.getMetricsAsJSON();
      const performanceMetric = metrics.find(m => m.name === 'ai_portal_performance_score');
      return performanceMetric ? performanceMetric.values[0].value : 0;
    } catch (error) {
      return 0;
    }
  }
}

// Express server for performance profiling API
const express = require('express');
const app = express();
app.use(express.json());

const profiler = new PerformanceProfiler();

// Prometheus metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    const metrics = await profiler.getMetrics();
    res.set('Content-Type', profiler.register.contentType);
    res.end(metrics);
  } catch (error) {
    res.status(500).end(error.toString());
  }
});

// Performance profiles API
app.get('/profiles', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  res.json({
    profiles: profiler.getProfiles(limit),
    total: profiler.profiles.length
  });
});

// Bottlenecks API
app.get('/bottlenecks', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  res.json({
    bottlenecks: profiler.getBottlenecks(limit),
    total: profiler.bottlenecks.length
  });
});

// Benchmarks API
app.get('/benchmarks', (req, res) => {
  res.json({
    benchmarks: profiler.getBenchmarks(),
    count: profiler.benchmarks.size
  });
});

// Run benchmark endpoint
app.post('/benchmark/:name', async (req, res) => {
  const { name } = req.params;
  const { iterations = 100 } = req.body;

  try {
    const benchmark = await profiler.runBenchmark(name, async () => {
      // Default benchmark function - can be customized
      await new Promise(resolve => setTimeout(resolve, Math.random() * 100));
    }, iterations);

    res.json(benchmark);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Generate report endpoint
app.post('/report', async (req, res) => {
  try {
    const filename = req.body.filename || `performance-report-${Date.now()}.json`;
    await profiler.saveProfileReport(filename);
    res.json({ message: `Report saved to ${filename}` });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health endpoint
app.get('/health', async (req, res) => {
  const performanceScore = await profiler.getPerformanceScore();
  res.json({
    status: 'healthy',
    performanceScore,
    profiles: profiler.profiles.length,
    bottlenecks: profiler.bottlenecks.length,
    benchmarks: profiler.benchmarks.size,
    timestamp: new Date().toISOString()
  });
});

const PORT = process.env.PROFILER_PORT || 9092;
app.listen(PORT, () => {
  console.log(`📈 Performance profiler listening on port ${PORT}`);
  console.log(`📊 Metrics available at http://localhost:${PORT}/metrics`);
  console.log(`🔍 Profiles API at http://localhost:${PORT}/profiles`);
  console.log(`🚧 Bottlenecks API at http://localhost:${PORT}/bottlenecks`);
});

module.exports = PerformanceProfiler;
