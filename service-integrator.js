#!/usr/bin/env node

/**
 * Service Integration Framework
 * Unified framework for connecting to external services and APIs
 */

const axios = require('axios');
const https = require('https');

class ServiceIntegrator {
  constructor() {
    this.services = {};
    this.healthCache = new Map();
    this.CACHE_TTL = 30000; // 30 seconds
  }

  /**
   * Register a service with its configuration
   */
  registerService(name, config) {
    this.services[name] = {
      ...config,
      lastHealthCheck: null,
      healthStatus: 'unknown',
      metrics: {}
    };
  }

  /**
   * Get cached health status or perform fresh check
   */
  async getHealthStatus(serviceName) {
    const service = this.services[serviceName];
    if (!service) return { status: 'unknown', error: 'Service not registered' };

    const now = Date.now();
    const cached = this.healthCache.get(serviceName);

    if (cached && (now - cached.timestamp) < this.CACHE_TTL) {
      return cached.status;
    }

    try {
      const status = await this.performHealthCheck(service);
      this.healthCache.set(serviceName, { status, timestamp: now });
      service.lastHealthCheck = new Date().toISOString();
      service.healthStatus = status.status;
      return status;
    } catch (error) {
      const status = { status: 'error', error: error.message };
      this.healthCache.set(serviceName, { status, timestamp: now });
      service.lastHealthCheck = new Date().toISOString();
      service.healthStatus = 'error';
      return status;
    }
  }

  /**
   * Perform health check for a service
   */
  async performHealthCheck(service) {
    const axiosConfig = {
      timeout: service.timeout || 5000,
      headers: service.headers || {},
      httpsAgent: new https.Agent({
        rejectUnauthorized: service.rejectUnauthorized !== false
      })
    };

    // Basic HTTP health check
    if (service.healthEndpoint) {
      try {
        const response = await axios.get(`${service.baseUrl}${service.healthEndpoint}`, axiosConfig);
        return {
          status: 'running',
          responseTime: response.data.responseTime || 'unknown',
          version: response.data.version || 'unknown',
          uptime: response.data.uptime || 'unknown'
        };
      } catch (error) {
        // If health endpoint fails, try basic connectivity
        try {
          await axios.get(service.baseUrl, axiosConfig);
          return { status: 'degraded', error: 'Health endpoint unavailable' };
        } catch (connectError) {
          return { status: 'error', error: connectError.message };
        }
      }
    }

    // Basic connectivity check
    try {
      await axios.get(service.baseUrl, axiosConfig);
      return { status: 'running' };
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  }

  /**
   * Get metrics from a service
   */
  async getMetrics(serviceName) {
    const service = this.services[serviceName];
    if (!service || !service.metricsEndpoint) return null;

    try {
      const response = await axios.get(`${service.baseUrl}${service.metricsEndpoint}`, {
        timeout: service.timeout || 5000,
        headers: service.headers || {}
      });
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  }

  /**
   * Get all registered services status
   */
  async getAllServicesStatus() {
    const results = {};
    for (const serviceName of Object.keys(this.services)) {
      results[serviceName] = await this.getHealthStatus(serviceName);
    }
    return results;
  }
}

// ArgoCD Integration
class ArgoCDIntegration {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async getApplications() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/applications`, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        },
        timeout: 10000
      });

      return response.data.items.map(app => ({
        name: app.metadata.name,
        namespace: app.metadata.namespace,
        status: app.status.sync.status,
        health: app.status.health.status,
        operation: app.status.operationState?.phase || 'Unknown',
        lastSync: app.status.operationState?.finishedAt || 'Never',
        images: app.status.summary?.images || [],
        repoUrl: app.spec.source.repoURL
      }));
    } catch (error) {
      return { error: error.message };
    }
  }

  async getClusters() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/clusters`, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        },
        timeout: 10000
      });

      return response.data.items.map(cluster => ({
        name: cluster.name,
        server: cluster.server,
        status: cluster.connectionState.status,
        version: cluster.serverVersion || 'Unknown'
      }));
    } catch (error) {
      return { error: error.message };
    }
  }

  async getProjects() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/projects`, {
        headers: {
          'Authorization': `Bearer ${this.token}`
        },
        timeout: 10000
      });

      return response.data.items.map(project => ({
        name: project.metadata.name,
        description: project.spec.description,
        destinations: project.spec.destinations.length,
        sources: project.spec.sourceRepos.length
      }));
    } catch (error) {
      return { error: error.message };
    }
  }
}

// Langfuse Integration
class LangfuseIntegration {
  constructor(baseUrl, secretKey, publicKey) {
    this.baseUrl = baseUrl;
    this.secretKey = secretKey;
    this.publicKey = publicKey;
  }

  async getUsage() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/public/usage`, {
        headers: {
          'Authorization': `Bearer ${this.publicKey}`,
          'X-Langfuse-Secret-Key': this.secretKey
        },
        timeout: 10000
      });

      return {
        totalTraces: response.data.totalTraces,
        totalObservations: response.data.totalObservations,
        totalUsers: response.data.totalUsers,
        usageByModel: response.data.usageByModel || [],
        totalCost: response.data.totalCost || 0
      };
    } catch (error) {
      return { error: error.message };
    }
  }

  async getTraces(limit = 50) {
    try {
      const response = await axios.get(`${this.baseUrl}/api/public/traces`, {
        params: { limit },
        headers: {
          'Authorization': `Bearer ${this.publicKey}`,
          'X-Langfuse-Secret-Key': this.secretKey
        },
        timeout: 10000
      });

      return response.data.data.map(trace => ({
        id: trace.id,
        name: trace.name,
        timestamp: trace.timestamp,
        duration: trace.duration,
        tokens: trace.totalTokens,
        cost: trace.totalCost,
        userId: trace.userId,
        tags: trace.tags
      }));
    } catch (error) {
      return { error: error.message };
    }
  }

  async getDatasets() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/public/datasets`, {
        headers: {
          'Authorization': `Bearer ${this.publicKey}`,
          'X-Langfuse-Secret-Key': this.secretKey
        },
        timeout: 10000
      });

      return response.data.data.map(dataset => ({
        name: dataset.name,
        description: dataset.description,
        items: dataset.items?.length || 0,
        runs: dataset.runs?.length || 0
      }));
    } catch (error) {
      return { error: error.message };
    }
  }
}

// Prometheus Integration
class PrometheusIntegration {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async query(query, time) {
    try {
      const params = { query };
      if (time) params.time = time;

      const response = await axios.get(`${this.baseUrl}/api/v1/query`, {
        params,
        timeout: 10000
      });

      return response.data.data.result;
    } catch (error) {
      return { error: error.message };
    }
  }

  async queryRange(query, start, end, step = '15s') {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/query_range`, {
        params: { query, start, end, step },
        timeout: 10000
      });

      return response.data.data.result;
    } catch (error) {
      return { error: error.message };
    }
  }

  async getTargets() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/v1/targets`, {
        timeout: 10000
      });

      return response.data.data.activeTargets.map(target => ({
        labels: target.labels,
        health: target.health,
        lastScrape: target.lastScrape,
        scrapeUrl: target.scrapeUrl
      }));
    } catch (error) {
      return { error: error.message };
    }
  }
}

// Elasticsearch Integration
class ElasticsearchIntegration {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async getClusterHealth() {
    try {
      const response = await axios.get(`${this.baseUrl}/_cluster/health`, {
        headers: {
          'Authorization': `ApiKey ${this.apiKey}`
        },
        timeout: 10000
      });

      return {
        status: response.data.status,
        clusterName: response.data.cluster_name,
        nodes: response.data.number_of_nodes,
        dataNodes: response.data.number_of_data_nodes,
        activeShards: response.data.active_shards,
        relocatingShards: response.data.relocating_shards,
        initializingShards: response.data.initializing_shards,
        unassignedShards: response.data.unassigned_shards
      };
    } catch (error) {
      return { error: error.message };
    }
  }

  async searchLogs(index, query = {}, size = 50) {
    try {
      const response = await axios.post(`${this.baseUrl}/${index}/_search`, {
        size,
        sort: [{ '@timestamp': { order: 'desc' } }],
        query: query.bool || { match_all: {} }
      }, {
        headers: {
          'Authorization': `ApiKey ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });

      return response.data.hits.hits.map(hit => ({
        timestamp: hit._source['@timestamp'],
        level: hit._source.level || hit._source.log?.level,
        message: hit._source.message || hit._source.log?.message,
        service: hit._source.service?.name || hit._source.kubernetes?.pod_name,
        index: hit._index
      }));
    } catch (error) {
      return { error: error.message };
    }
  }
}

module.exports = {
  ServiceIntegrator,
  ArgoCDIntegration,
  LangfuseIntegration,
  PrometheusIntegration,
  ElasticsearchIntegration
};
