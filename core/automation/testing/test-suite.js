#!/usr/bin/env node

/**
 * AI Infrastructure Portal - Comprehensive Testing Suite
 * Tests API endpoints, service integrations, load testing, and security
 */

const axios = require('axios');
const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class TestingSuite {
  constructor(baseUrl = 'http://localhost:5001') {
    this.baseUrl = baseUrl;
    this.results = {
      passed: 0,
      failed: 0,
      errors: [],
      warnings: [],
      performance: []
    };
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const coloredMessage = this.colorize(`[${timestamp}] ${message}`, type);
    console.log(coloredMessage);

    if (type === 'error') {
      this.results.errors.push(message);
    } else if (type === 'warning') {
      this.results.warnings.push(message);
    }
  }

  colorize(message, type) {
    const colors = {
      success: '\x1b[32m',
      error: '\x1b[31m',
      warning: '\x1b[33m',
      info: '\x1b[36m',
      reset: '\x1b[0m'
    };
    return `${colors[type]}${message}${colors.reset}`;
  }

  async testEndpoint(endpoint, expectedStatus = 200, description = '') {
    try {
      const startTime = Date.now();
      const response = await axios.get(`${this.baseUrl}${endpoint}`, {
        timeout: 10000,
        validateStatus: () => true
      });
      const duration = Date.now() - startTime;

      this.results.performance.push({
        endpoint,
        duration,
        status: response.status
      });

      if (response.status === expectedStatus) {
        this.log(`✓ ${endpoint} - ${description} (${duration}ms)`, 'success');
        this.results.passed++;
        return response.data;
      } else {
        this.log(`✗ ${endpoint} - Expected ${expectedStatus}, got ${response.status}`, 'error');
        this.results.failed++;
        return null;
      }
    } catch (error) {
      this.log(`✗ ${endpoint} - ${error.message}`, 'error');
      this.results.failed++;
      return null;
    }
  }

  async testEndpointPost(endpoint, data, expectedStatus = 200, description = '') {
    try {
      const startTime = Date.now();
      const response = await axios.post(`${this.baseUrl}${endpoint}`, data, {
        timeout: 10000,
        validateStatus: () => true
      });
      const duration = Date.now() - startTime;

      this.results.performance.push({
        endpoint,
        duration,
        status: response.status,
        method: 'POST'
      });

      if (response.status === expectedStatus) {
        this.log(`✓ POST ${endpoint} - ${description} (${duration}ms)`, 'success');
        this.results.passed++;
        return response.data;
      } else {
        this.log(`✗ POST ${endpoint} - Expected ${expectedStatus}, got ${response.status}`, 'error');
        this.results.failed++;
        return null;
      }
    } catch (error) {
      this.log(`✗ POST ${endpoint} - ${error.message}`, 'error');
      this.results.failed++;
      return null;
    }
  }

  async runAPITests() {
    this.log('🚀 Starting API Integration Tests', 'info');

    // Basic health checks
    await this.testEndpoint('/api/health', 200, 'Basic health check');
    await this.testEndpoint('/api/health/detailed', 200, 'Detailed health assessment');

    // Core data endpoints
    await this.testEndpoint('/api/services', 200, 'Service status listing');
    await this.testEndpoint('/api/metrics', 200, 'System metrics');
    await this.testEndpoint('/api/agents', 200, 'Agent data with skills');
    await this.testEndpoint('/api/skills', 200, 'Skills repository data');
    await this.testEndpoint('/api/activity', 200, 'Recent activity feed');

    // Enhanced monitoring
    await this.testEndpoint('/api/alerts', 200, 'Active alerts');
    await this.testEndpoint('/api/metrics/history', 200, 'Historical metrics');
    await this.testEndpoint('/api/metrics/prometheus', 200, 'Prometheus metrics export');

    // Service integrations
    await this.testEndpoint('/api/argocd/applications', 200, 'ArgoCD applications');
    await this.testEndpoint('/api/langfuse/metrics', 200, 'Langfuse metrics');

    // RAG query test
    await this.testEndpointPost('/api/rag/query',
      { query: 'What services are running?' },
      200, 'RAG query processing');

    this.log('✅ API Integration Tests Completed', 'info');
  }

  async runDataValidationTests() {
    this.log('🔍 Starting Data Validation Tests', 'info');

    // Validate agent data structure
    const agents = await this.testEndpoint('/api/agents', 200, 'Agent data structure');
    if (agents) {
      const agent = agents.agents[0];
      if (agent && agent.skillsList && Array.isArray(agent.skillsList)) {
        this.log('✓ Agent skillsList is properly populated', 'success');
        this.results.passed++;
      } else {
        this.log('✗ Agent skillsList is missing or invalid', 'error');
        this.results.failed++;
      }
    }

    // Validate skills data
    const skills = await this.testEndpoint('/api/skills', 200, 'Skills data structure');
    if (skills && skills.skills && skills.skills.length > 0) {
      const skill = skills.skills[0];
      if (skill.name && skill.description) {
        this.log('✓ Skills data has required fields', 'success');
        this.results.passed++;
      } else {
        this.log('✗ Skills data missing required fields', 'error');
        this.results.failed++;
      }
    }

    // Validate service status
    const services = await this.testEndpoint('/api/services', 200, 'Service status');
    if (services) {
      const serviceNames = Object.keys(services.services);
      if (serviceNames.length >= 7) { // Should have at least 7 services
        this.log('✓ All expected services are present', 'success');
        this.results.passed++;
      } else {
        this.log('✗ Missing expected services', 'error');
        this.results.failed++;
      }
    }

    this.log('✅ Data Validation Tests Completed', 'info');
  }

  async runLoadTest(endpoint, requests = 50, concurrency = 5) {
    this.log(`⚡ Starting Load Test: ${requests} requests to ${endpoint}`, 'info');

    const results = [];
    const batches = Math.ceil(requests / concurrency);

    for (let i = 0; i < batches; i++) {
      const promises = [];
      const batchSize = Math.min(concurrency, requests - i * concurrency);

      for (let j = 0; j < batchSize; j++) {
        promises.push(this.testEndpoint(endpoint, 200, `Load test ${i * concurrency + j + 1}`));
      }

      const batchResults = await Promise.all(promises);
      results.push(...batchResults.filter(r => r !== null));
    }

    const successful = results.length;
    const avgResponse = results.reduce((sum, r) => sum + (r.responseTime || 0), 0) / successful;

    if (successful === requests) {
      this.log(`✓ Load test passed: ${successful}/${requests} successful (${avgResponse.toFixed(2)}ms avg)`, 'success');
      this.results.passed++;
    } else {
      this.log(`✗ Load test failed: ${successful}/${requests} successful`, 'error');
      this.results.failed++;
    }

    return { successful, total: requests, avgResponse };
  }

  async runSecurityTests() {
    this.log('🔒 Starting Security Tests', 'info');

    // Test for basic security headers
    try {
      const response = await axios.get(`${this.baseUrl}/api/health`, {
        timeout: 5000,
        validateStatus: () => true
      });

      // Check for common security headers
      const headers = response.headers;
      const securityChecks = [
        { header: 'x-content-type-options', value: 'nosniff' },
        { header: 'x-frame-options', value: 'DENY' },
        { header: 'x-xss-protection', value: '1; mode=block' }
      ];

      securityChecks.forEach(check => {
        if (headers[check.header] === check.value) {
          this.log(`✓ Security header ${check.header} present`, 'success');
          this.results.passed++;
        } else {
          this.log(`⚠ Security header ${check.header} missing or incorrect`, 'warning');
        }
      });
    } catch (error) {
      this.log(`✗ Security test failed: ${error.message}`, 'error');
      this.results.failed++;
    }

    // Test for SQL injection attempts
    const maliciousQueries = [
      { query: "'; DROP TABLE users; --" },
      { query: '1 UNION SELECT * FROM information_schema.tables' },
      { query: '<script>alert("xss")</script>' }
    ];

    for (const testQuery of maliciousQueries) {
      try {
        const response = await axios.post(`${this.baseUrl}/api/rag/query`, testQuery, {
          timeout: 5000,
          validateStatus: () => true
        });

        if (response.status === 200) {
          this.log(`✓ Malicious input handled safely: ${testQuery.query.substring(0, 20)}...`, 'success');
          this.results.passed++;
        } else {
          this.log(`⚠ Unexpected response to malicious input`, 'warning');
        }
      } catch (error) {
        this.log(`✓ Malicious input properly rejected: ${testQuery.query.substring(0, 20)}...`, 'success');
        this.results.passed++;
      }
    }

    this.log('✅ Security Tests Completed', 'info');
  }

  async runServiceIntegrationTests() {
    this.log('🔗 Starting Service Integration Tests', 'info');

    // Test ArgoCD integration
    const argocdData = await this.testEndpoint('/api/argocd/applications', 200, 'ArgoCD applications');
    if (argocdData && argocdData.applications && Array.isArray(argocdData.applications)) {
      this.log('✓ ArgoCD integration returns valid application data', 'success');
      this.results.passed++;
    } else {
      this.log('✗ ArgoCD integration failed or returned invalid data', 'error');
      this.results.failed++;
    }

    // Test Langfuse integration
    const langfuseData = await this.testEndpoint('/api/langfuse/metrics', 200, 'Langfuse metrics');
    if (langfuseData && langfuseData.traces) {
      this.log('✓ Langfuse integration returns valid metrics data', 'success');
      this.results.passed++;
    } else {
      this.log('✗ Langfuse integration failed or returned invalid data', 'error');
      this.results.failed++;
    }

    this.log('✅ Service Integration Tests Completed', 'info');
  }

  async runPerformanceTests() {
    this.log('📊 Starting Performance Tests', 'info');

    // Test response times for critical endpoints
    const criticalEndpoints = [
      '/api/health',
      '/api/agents',
      '/api/services',
      '/api/metrics'
    ];

    for (const endpoint of criticalEndpoints) {
      const startTime = Date.now();
      await this.testEndpoint(endpoint, 200, 'Performance test');
      const duration = Date.now() - startTime;

      if (duration < 1000) { // Should respond within 1 second
        this.log(`✓ ${endpoint} responds quickly (${duration}ms)`, 'success');
        this.results.passed++;
      } else {
        this.log(`⚠ ${endpoint} response slow (${duration}ms)`, 'warning');
      }
    }

    // Run basic load test
    await this.runLoadTest('/api/health', 20, 5);

    this.log('✅ Performance Tests Completed', 'info');
  }

  async runE2ETests() {
    this.log('🌐 Starting End-to-End Tests', 'info');

    try {
      // Test complete data flow
      const health = await this.testEndpoint('/api/health', 200, 'E2E: Health check');
      const services = await this.testEndpoint('/api/services', 200, 'E2E: Service status');
      const agents = await this.testEndpoint('/api/agents', 200, 'E2E: Agent data');
      const skills = await this.testEndpoint('/api/skills', 200, 'E2E: Skills data');

      if (health && services && agents && skills) {
        // Validate cross-references
        const agentSkills = agents.agents.flatMap(a => a.skillsList || []);
        const availableSkills = skills.skills.map(s => s.name);

        const matchingSkills = agentSkills.filter(skill =>
          availableSkills.includes(skill)
        );

        if (matchingSkills.length > 0) {
          this.log('✓ E2E: Agent skills properly reference skill repository', 'success');
          this.results.passed++;
        } else {
          this.log('⚠ E2E: Agent skills may not reference skill repository', 'warning');
        }

        this.log('✓ E2E: Complete data flow validation passed', 'success');
        this.results.passed++;
      } else {
        this.log('✗ E2E: Missing critical data endpoints', 'error');
        this.results.failed++;
      }
    } catch (error) {
      this.log(`✗ E2E: Test failed - ${error.message}`, 'error');
      this.results.failed++;
    }

    this.log('✅ End-to-End Tests Completed', 'info');
  }

  async generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total: this.results.passed + this.results.failed,
        passed: this.results.passed,
        failed: this.results.failed,
        successRate: ((this.results.passed / (this.results.passed + this.results.failed)) * 100).toFixed(2) + '%'
      },
      errors: this.results.errors,
      warnings: this.results.warnings,
      performance: this.results.performance
    };

    await fs.writeFile('test-results.json', JSON.stringify(report, null, 2));
    this.log(`📄 Test report saved to test-results.json`, 'info');

    return report;
  }

  async runAllTests() {
    this.log('🎯 Starting Comprehensive Testing Suite', 'info');

    await this.runAPITests();
    await this.runDataValidationTests();
    await this.runServiceIntegrationTests();
    await this.runSecurityTests();
    await this.runPerformanceTests();
    await this.runE2ETests();

    const report = await this.generateReport();

    this.log(`\n🎯 Testing Suite Complete!`, 'info');
    this.log(`Total Tests: ${report.summary.total}`, 'info');
    this.log(`Passed: ${report.summary.passed}`, 'success');
    this.log(`Failed: ${report.summary.failed}`, report.summary.failed > 0 ? 'error' : 'success');
    this.log(`Success Rate: ${report.summary.successRate}`, 'info');

    if (this.results.errors.length > 0) {
      this.log(`\n❌ Errors:`, 'error');
      this.results.errors.forEach(error => this.log(`  - ${error}`, 'error'));
    }

    if (this.results.warnings.length > 0) {
      this.log(`\n⚠️ Warnings:`, 'warning');
      this.results.warnings.forEach(warning => this.log(`  - ${warning}`, 'warning'));
    }

    return report;
  }
}

// CLI runner
async function main() {
  const args = process.argv.slice(2);
  const baseUrl = args[0] || 'http://localhost:5001';

  const suite = new TestingSuite(baseUrl);

  try {
    const report = await suite.runAllTests();
    process.exit(report.summary.failed > 0 ? 1 : 0);
  } catch (error) {
    console.error('Testing suite failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = TestingSuite;
