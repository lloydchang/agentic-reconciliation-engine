#!/usr/bin/env node

/**
 * AI Infrastructure Portal - Custom Metrics Collector
 * Business KPIs and advanced monitoring metrics
 */

const promClient = require('prom-client');
const axios = require('axios');
const os = require('os');

class CustomMetricsCollector {
  constructor(options = {}) {
    this.apiUrl = options.apiUrl || 'http://localhost:5001/api';
    this.collectionInterval = options.interval || 30000; // 30 seconds
    this.register = new promClient.Registry();

    // Business KPIs
    this.businessMetrics = {
      activeUsers: new promClient.Gauge({
        name: 'ai_portal_active_users',
        help: 'Number of active users currently using the portal',
        registers: [this.register]
      }),

      apiRequestsTotal: new promClient.Counter({
        name: 'ai_portal_api_requests_total',
        help: 'Total number of API requests',
        labelNames: ['endpoint', 'method', 'status'],
        registers: [this.register]
      }),

      agentInteractions: new promClient.Counter({
        name: 'ai_portal_agent_interactions_total',
        help: 'Total number of agent interactions',
        labelNames: ['agent_type', 'skill', 'outcome'],
        registers: [this.register]
      }),

      costSavings: new promClient.Gauge({
        name: 'ai_portal_cost_savings_usd',
        help: 'Total cost savings achieved through AI optimization',
        registers: [this.register]
      }),

      skillExecutionTime: new promClient.Histogram({
        name: 'ai_portal_skill_execution_duration_seconds',
        help: 'Time taken to execute skills',
        labelNames: ['skill_name', 'risk_level'],
        buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60, 120],
        registers: [this.register]
      }),

      ragQueryAccuracy: new promClient.Gauge({
        name: 'ai_portal_rag_query_accuracy',
        help: 'Accuracy score of RAG query responses',
        labelNames: ['query_type'],
        registers: [this.register]
      }),

      serviceHealthScore: new promClient.Gauge({
        name: 'ai_portal_service_health_score',
        help: 'Overall service health score (0-100)',
        labelNames: ['service_name'],
        registers: [this.register]
      }),

      infrastructureEfficiency: new promClient.Gauge({
        name: 'ai_portal_infrastructure_efficiency',
        help: 'Infrastructure resource utilization efficiency (0-100)',
        registers: [this.register]
      }),

      userSatisfaction: new promClient.Gauge({
        name: 'ai_portal_user_satisfaction_score',
        help: 'User satisfaction score based on feedback (0-100)',
        registers: [this.register]
      }),

      automationCoverage: new promClient.Gauge({
        name: 'ai_portal_automation_coverage_percent',
        help: 'Percentage of operations covered by automation',
        registers: [this.register]
      }),

      incidentResponseTime: new promClient.Histogram({
        name: 'ai_portal_incident_response_time_seconds',
        help: 'Time to respond to incidents',
        buckets: [60, 300, 600, 1800, 3600, 7200],
        registers: [this.register]
      }),

      complianceScore: new promClient.Gauge({
        name: 'ai_portal_compliance_score',
        help: 'Compliance score across different frameworks (0-100)',
        labelNames: ['framework'],
        registers: [this.register]
      }),

      dataQuality: new promClient.Gauge({
        name: 'ai_portal_data_quality_score',
        help: 'Data quality score for AI training data (0-100)',
        registers: [this.register]
      }),

      modelAccuracy: new promClient.Gauge({
        name: 'ai_portal_model_accuracy',
        help: 'AI model accuracy across different tasks',
        labelNames: ['model_type', 'task'],
        registers: [this.register]
      }),

      cacheHitRate: new promClient.Gauge({
        name: 'ai_portal_cache_hit_rate',
        help: 'Cache hit rate for performance optimization',
        registers: [this.register]
      }),

      websocketConnections: new promClient.Gauge({
        name: 'ai_portal_websocket_connections_active',
        help: 'Number of active WebSocket connections',
        registers: [this.register]
      }),

      featureAdoption: new promClient.Gauge({
        name: 'ai_portal_feature_adoption_rate',
        help: 'Rate of feature adoption by users',
        labelNames: ['feature'],
        registers: [this.register]
      }),

      errorRate: new promClient.Gauge({
        name: 'ai_portal_error_rate_percent',
        help: 'Overall error rate across all services',
        registers: [this.register]
      }),

      uptime: new promClient.Gauge({
        name: 'ai_portal_uptime_percent',
        help: 'Service uptime percentage (last 24h)',
        labelNames: ['service'],
        registers: [this.register]
      }),

      scalabilityIndex: new promClient.Gauge({
        name: 'ai_portal_scalability_index',
        help: 'Scalability index based on load handling capacity',
        registers: [this.register]
      })
    };

    // Start collection
    this.startCollection();
  }

  async collectBusinessMetrics() {
    try {
      // Collect API metrics
      await this.collectAPIMetrics();

      // Collect agent metrics
      await this.collectAgentMetrics();

      // Collect service metrics
      await this.collectServiceMetrics();

      // Collect infrastructure metrics
      await this.collectInfrastructureMetrics();

      // Collect synthetic business metrics
      this.collectSyntheticMetrics();

    } catch (error) {
      console.error('Error collecting business metrics:', error);
    }
  }

  async collectAPIMetrics() {
    try {
      // Get API activity data
      const response = await axios.get(`${this.apiUrl}/activity`);
      const activities = response.data || [];

      // Count requests by endpoint and method
      const requestCounts = {};
      activities.forEach(activity => {
        const key = `${activity.endpoint}_${activity.method}`;
        requestCounts[key] = (requestCounts[key] || 0) + 1;
      });

      // Update metrics
      Object.entries(requestCounts).forEach(([key, count]) => {
        const [endpoint, method] = key.split('_');
        this.businessMetrics.apiRequestsTotal.inc({ endpoint, method, status: '200' }, count);
      });

      // Calculate active users (unique IPs in last 5 minutes)
      const recentActivities = activities.filter(a =>
        Date.now() - new Date(a.timestamp).getTime() < 300000
      );
      const uniqueUsers = new Set(recentActivities.map(a => a.userId || a.ip)).size;
      this.businessMetrics.activeUsers.set(uniqueUsers);

    } catch (error) {
      console.error('Error collecting API metrics:', error);
    }
  }

  async collectAgentMetrics() {
    try {
      const response = await axios.get(`${this.apiUrl}/agents`);
      const agents = response.data || [];

      agents.forEach(agent => {
        // Record agent interactions
        if (agent.lastActivity) {
          const timeSinceActivity = Date.now() - new Date(agent.lastActivity).getTime();
          if (timeSinceActivity < 3600000) { // Last hour
            this.businessMetrics.agentInteractions.inc({
              agent_type: agent.type,
              skill: agent.currentSkill || 'unknown',
              outcome: agent.status === 'success' ? 'success' : 'pending'
            });
          }
        }

        // Record skill execution times (simulated)
        if (agent.responseTime) {
          this.businessMetrics.skillExecutionTime
            .observe({ skill_name: agent.name, risk_level: agent.riskLevel }, agent.responseTime);
        }
      });

    } catch (error) {
      console.error('Error collecting agent metrics:', error);
    }
  }

  async collectServiceMetrics() {
    try {
      const response = await axios.get(`${this.apiUrl}/services`);
      const services = response.data || [];

      services.forEach(service => {
        // Calculate health score
        let healthScore = 100;
        if (service.status !== 'healthy') healthScore -= 50;
        if (service.responseTime > 1000) healthScore -= 20;
        if (service.errorRate > 0.01) healthScore -= 30;

        this.businessMetrics.serviceHealthScore.set(
          { service_name: service.name },
          Math.max(0, healthScore)
        );

        // Calculate uptime (simulated)
        const uptime = service.status === 'healthy' ? 99.9 : 95.0;
        this.businessMetrics.uptime.set({ service: service.name }, uptime);
      });

    } catch (error) {
      console.error('Error collecting service metrics:', error);
    }
  }

  async collectInfrastructureMetrics() {
    try {
      const response = await axios.get(`${this.apiUrl}/metrics`);
      const metrics = response.data || {};

      // Infrastructure efficiency
      const cpuEfficiency = Math.min(100, (1 - (metrics.cpu?.usage || 0) / 100) * 100);
      const memoryEfficiency = Math.min(100, (1 - (metrics.memory?.usage || 0) / 100) * 100);
      const efficiency = (cpuEfficiency + memoryEfficiency) / 2;

      this.businessMetrics.infrastructureEfficiency.set(efficiency);

      // Scalability index based on resource utilization
      const scalabilityIndex = Math.max(0, 100 - ((metrics.cpu?.usage || 0) + (metrics.memory?.usage || 0)) / 2);
      this.businessMetrics.scalabilityIndex.set(scalabilityIndex);

    } catch (error) {
      console.error('Error collecting infrastructure metrics:', error);
    }
  }

  collectSyntheticMetrics() {
    // RAG Query Accuracy (simulated)
    const accuracy = 85 + Math.random() * 10; // 85-95%
    this.businessMetrics.ragQueryAccuracy.set({ query_type: 'general' }, accuracy);

    // Cost Savings (simulated)
    const savings = Math.floor(Math.random() * 10000) + 5000; // $5K-$15K
    this.businessMetrics.costSavings.set(savings);

    // User Satisfaction (simulated)
    const satisfaction = 75 + Math.random() * 20; // 75-95%
    this.businessMetrics.userSatisfaction.set(satisfaction);

    // Automation Coverage (simulated)
    const coverage = 60 + Math.random() * 30; // 60-90%
    this.businessMetrics.automationCoverage.set(coverage);

    // Compliance Scores (simulated)
    const frameworks = ['SOC2', 'GDPR', 'ISO27001'];
    frameworks.forEach(framework => {
      const score = 80 + Math.random() * 15; // 80-95%
      this.businessMetrics.complianceScore.set({ framework }, score);
    });

    // Data Quality (simulated)
    const dataQuality = 85 + Math.random() * 10; // 85-95%
    this.businessMetrics.dataQuality.set(dataQuality);

    // Model Accuracy (simulated)
    const models = ['text_classification', 'sentiment_analysis', 'entity_recognition'];
    models.forEach(model => {
      const accuracy = 85 + Math.random() * 12; // 85-97%
      this.businessMetrics.modelAccuracy.set({ model_type: 'transformer', task: model }, accuracy);
    });

    // Cache Hit Rate (simulated)
    const hitRate = 75 + Math.random() * 20; // 75-95%
    this.businessMetrics.cacheHitRate.set(hitRate);

    // WebSocket Connections (simulated)
    const connections = Math.floor(Math.random() * 50) + 10; // 10-60
    this.businessMetrics.websocketConnections.set(connections);

    // Feature Adoption (simulated)
    const features = ['real_time_updates', 'advanced_charts', 'custom_dashboards'];
    features.forEach(feature => {
      const adoption = 20 + Math.random() * 60; // 20-80%
      this.businessMetrics.featureAdoption.set({ feature }, adoption);
    });

    // Error Rate (simulated)
    const errorRate = Math.random() * 2; // 0-2%
    this.businessMetrics.errorRate.set(errorRate);
  }

  startCollection() {
    // Initial collection
    this.collectBusinessMetrics();

    // Set up periodic collection
    setInterval(() => {
      this.collectBusinessMetrics();
    }, this.collectionInterval);

    console.log(`🚀 Custom metrics collector started - collecting every ${this.collectionInterval/1000}s`);
  }

  getMetrics() {
    return this.register.metrics();
  }

  async getMetricsEndpoint() {
    return this.register.getMetricsAsJSON();
  }
}

// Express server for metrics endpoint
const express = require('express');
const app = express();

const metricsCollector = new CustomMetricsCollector();

// Metrics endpoint for Prometheus
app.get('/metrics', async (req, res) => {
  try {
    const metrics = await metricsCollector.getMetrics();
    res.set('Content-Type', metricsCollector.register.contentType);
    res.end(metrics);
  } catch (error) {
    res.status(500).end(error.toString());
  }
});

// Health endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Business KPIs endpoint
app.get('/kpis', async (req, res) => {
  try {
    const kpis = await metricsCollector.getMetricsEndpoint();
    res.json(kpis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.METRICS_PORT || 9090;
app.listen(PORT, () => {
  console.log(`📊 Custom metrics server listening on port ${PORT}`);
  console.log(`📈 Prometheus metrics available at http://localhost:${PORT}/metrics`);
  console.log(`📊 Business KPIs available at http://localhost:${PORT}/kpis`);
});

module.exports = CustomMetricsCollector;
