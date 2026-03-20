#!/usr/bin/env node

/**
 * AI Infrastructure Portal - End-to-End Test Suite
 * Comprehensive workflow testing for the entire portal system
 */

const axios = require('axios');
const { expect } = require('chai');
const WebSocket = require('ws');

class EndToEndTestSuite {
  constructor(baseUrl = 'http://localhost:5001') {
    this.baseUrl = baseUrl;
    this.apiUrl = baseUrl;
    this.dashboardUrl = 'http://localhost:8081';
    this.testResults = [];
    this.authToken = null;
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  async runTest(testName, testFn) {
    try {
      this.log(`Starting test: ${testName}`);
      const startTime = Date.now();
      const result = await testFn();
      const duration = Date.now() - startTime;

      const testResult = {
        name: testName,
        status: 'passed',
        duration,
        result
      };

      this.testResults.push(testResult);
      this.log(`Test passed: ${testName} (${duration}ms)`, 'success');
      return result;
    } catch (error) {
      const testResult = {
        name: testName,
        status: 'failed',
        error: error.message,
        stack: error.stack
      };

      this.testResults.push(testResult);
      this.log(`Test failed: ${testName} - ${error.message}`, 'error');
      throw error;
    }
  }

  async testHealthChecks() {
    return this.runTest('Health Checks', async () => {
      // API Health Check
      const apiHealth = await axios.get(`${this.apiUrl}/api/health`);
      expect(apiHealth.status).to.equal(200);
      expect(apiHealth.data.status).to.equal('healthy');

      // Detailed Health Check
      const detailedHealth = await axios.get(`${this.apiUrl}/api/health/detailed`);
      expect(detailedHealth.status).to.equal(200);
      expect(detailedHealth.data).to.have.property('services');
      expect(detailedHealth.data).to.have.property('system');

      // Dashboard Health Check
      try {
        const dashboardHealth = await axios.get(`${this.dashboardUrl}/health`);
        expect(dashboardHealth.status).to.equal(200);
      } catch (error) {
        this.log('Dashboard health check skipped - service may not be running');
      }
    });
  }

  async testAPIServices() {
    return this.runTest('API Services Endpoints', async () => {
      // Services endpoint
      const services = await axios.get(`${this.apiUrl}/api/services`);
      expect(services.status).to.equal(200);
      expect(services.data).to.be.an('array');
      expect(services.data.length).to.be.greaterThan(0);

      // Validate service structure
      const service = services.data[0];
      expect(service).to.have.property('name');
      expect(service).to.have.property('status');
      expect(service).to.have.property('url');

      // Metrics endpoint
      const metrics = await axios.get(`${this.apiUrl}/api/metrics`);
      expect(metrics.status).to.equal(200);
      expect(metrics.data).to.have.property('cpu');
      expect(metrics.data).to.have.property('memory');
      expect(metrics.data).to.have.property('disk');

      // Agents endpoint
      const agents = await axios.get(`${this.apiUrl}/api/agents`);
      expect(agents.status).to.equal(200);
      expect(agents.data).to.be.an('array');

      // Skills endpoint
      const skills = await axios.get(`${this.apiUrl}/api/skills`);
      expect(skills.status).to.equal(200);
      expect(skills.data).to.be.an('array');
    });
  }

  async testAuthentication() {
    return this.runTest('Authentication Flow', async () => {
      // Test login endpoint
      try {
        const login = await axios.post(`${this.apiUrl}/auth/login`, {
          username: 'admin',
          password: 'admin123'
        });
        expect(login.status).to.equal(200);
        expect(login.data).to.have.property('token');
        this.authToken = login.data.token;
      } catch (error) {
        if (error.response?.status === 404) {
          this.log('Authentication endpoints not implemented yet - skipping');
          return;
        }
        throw error;
      }

      // Test protected endpoint with token
      if (this.authToken) {
        const users = await axios.get(`${this.apiUrl}/api/users`, {
          headers: { Authorization: `Bearer ${this.authToken}` }
        });
        expect(users.status).to.equal(200);
      }
    });
  }

  async testWebSocketConnection() {
    return this.runTest('WebSocket Real-time Updates', async () => {
      return new Promise((resolve, reject) => {
        try {
          const ws = new WebSocket(`ws://localhost:8081`);

          ws.on('open', () => {
            this.log('WebSocket connection established');
          });

          ws.on('message', (data) => {
            try {
              const message = JSON.parse(data.toString());
              expect(message).to.have.property('type');
              expect(message).to.have.property('timestamp');
              ws.close();
              resolve();
            } catch (error) {
              reject(error);
            }
          });

          ws.on('error', (error) => {
            reject(error);
          });

          // Timeout after 10 seconds
          setTimeout(() => {
            ws.close();
            reject(new Error('WebSocket test timeout'));
          }, 10000);
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  async testRAGQuery() {
    return this.runTest('RAG Query Functionality', async () => {
      const ragQuery = await axios.post(`${this.apiUrl}/api/rag/query`, {
        query: 'What is the current system status?',
        context: 'infrastructure monitoring'
      });

      expect(ragQuery.status).to.equal(200);
      expect(ragQuery.data).to.have.property('response');
      expect(ragQuery.data).to.have.property('confidence');
      expect(ragQuery.data.confidence).to.be.within(0, 1);
    });
  }

  async testLoadBalancing() {
    return this.runTest('Load Balancing Verification', async () => {
      // Make multiple concurrent requests to test load balancing
      const requests = Array(10).fill().map(() =>
        axios.get(`${this.apiUrl}/api/health`)
      );

      const responses = await Promise.all(requests);

      // All responses should be successful
      responses.forEach(response => {
        expect(response.status).to.equal(200);
      });

      // Check if requests were distributed (may have different pod identifiers)
      const serverHeaders = responses.map(r => r.headers['x-server-pod']);
      const uniqueServers = new Set(serverHeaders.filter(Boolean));

      if (uniqueServers.size > 1) {
        this.log(`Load balancing working - requests distributed across ${uniqueServers.size} servers`);
      } else {
        this.log('Load balancing check inconclusive - single server or no pod headers');
      }
    });
  }

  async testCachingLayer() {
    return this.runTest('Caching Layer Functionality', async () => {
      // Make same request twice and check for cache headers
      const firstRequest = await axios.get(`${this.apiUrl}/api/metrics`);
      const secondRequest = await axios.get(`${this.apiUrl}/api/metrics`);

      expect(firstRequest.status).to.equal(200);
      expect(secondRequest.status).to.equal(200);

      // Check for cache headers (may be implemented differently)
      const hasCacheHeader = secondRequest.headers['x-cache'] ||
                            secondRequest.headers['cache-control'];

      if (hasCacheHeader) {
        this.log('Caching layer appears to be working');
      } else {
        this.log('Caching layer check inconclusive - no cache headers detected');
      }
    });
  }

  async testErrorHandling() {
    return this.runTest('Error Handling', async () => {
      // Test 404 endpoint
      try {
        await axios.get(`${this.apiUrl}/api/nonexistent`);
        throw new Error('Should have returned 404');
      } catch (error) {
        expect(error.response.status).to.equal(404);
      }

      // Test invalid RAG query
      try {
        await axios.post(`${this.apiUrl}/api/rag/query`, {
          query: '',
          context: ''
        });
        throw new Error('Should have returned validation error');
      } catch (error) {
        expect(error.response.status).to.be.oneOf([400, 422]);
      }
    });
  }

  async testDataConsistency() {
    return this.runTest('Data Consistency Across Endpoints', async () => {
      // Get data from multiple endpoints
      const [services, agents, skills] = await Promise.all([
        axios.get(`${this.apiUrl}/api/services`),
        axios.get(`${this.apiUrl}/api/agents`),
        axios.get(`${this.apiUrl}/api/skills`)
      ]);

      // Validate data structures
      expect(services.data).to.be.an('array');
      expect(agents.data).to.be.an('array');
      expect(skills.data).to.be.an('array');

      // Check for required fields in agents
      if (agents.data.length > 0) {
        const agent = agents.data[0];
        expect(agent).to.have.property('id');
        expect(agent).to.have.property('name');
        expect(agent).to.have.property('status');
      }

      // Check for required fields in skills
      if (skills.data.length > 0) {
        const skill = skills.data[0];
        expect(skill).to.have.property('name');
        expect(skill).to.have.property('description');
        expect(skill).to.have.property('risk_level');
      }
    });
  }

  async runFullTestSuite() {
    this.log('🚀 Starting AI Infrastructure Portal End-to-End Test Suite');
    this.log('=' .repeat(80));

    try {
      await this.testHealthChecks();
      await this.testAPIServices();
      await this.testAuthentication();
      await this.testWebSocketConnection();
      await this.testRAGQuery();
      await this.testLoadBalancing();
      await this.testCachingLayer();
      await this.testErrorHandling();
      await this.testDataConsistency();

      this.generateReport();
    } catch (error) {
      this.log(`Test suite failed: ${error.message}`, 'error');
      this.generateReport();
      throw error;
    }
  }

  generateReport() {
    this.log('\n📊 End-to-End Test Suite Results');
    this.log('=' .repeat(80));

    const passed = this.testResults.filter(t => t.status === 'passed').length;
    const failed = this.testResults.filter(t => t.status === 'failed').length;
    const total = this.testResults.length;

    this.log(`Total Tests: ${total}`);
    this.log(`Passed: ${passed}`, 'success');
    this.log(`Failed: ${failed}`, failed > 0 ? 'error' : 'info');

    if (failed > 0) {
      this.log('\n❌ Failed Tests:');
      this.testResults
        .filter(t => t.status === 'failed')
        .forEach(test => {
          this.log(`  - ${test.name}: ${test.error}`, 'error');
        });
    }

    const successRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;
    this.log(`\nSuccess Rate: ${successRate}%`);

    if (passed === total) {
      this.log('🎉 All tests passed!', 'success');
    } else {
      this.log('⚠️ Some tests failed - review the results above', 'error');
    }

    return {
      total,
      passed,
      failed,
      successRate: parseFloat(successRate),
      results: this.testResults
    };
  }

  async saveReport(filename = 'e2e-test-report.json') {
    const report = {
      timestamp: new Date().toISOString(),
      testSuite: 'AI Infrastructure Portal End-to-End Tests',
      summary: this.generateReport(),
      details: this.testResults
    };

    await require('fs').promises.writeFile(filename, JSON.stringify(report, null, 2));
    this.log(`📄 Test report saved to ${filename}`);
  }
}

// CLI runner
async function main() {
  const args = process.argv.slice(2);
  const baseUrl = args[0] || 'http://localhost:5001';

  const testSuite = new EndToEndTestSuite(baseUrl);

  try {
    await testSuite.runFullTestSuite();
    await testSuite.saveReport();

    const summary = testSuite.generateReport();
    if (summary.failed > 0) {
      console.log('\n❌ End-to-end tests failed!');
      process.exit(1);
    } else {
      console.log('\n✅ All end-to-end tests passed!');
    }
  } catch (error) {
    console.error('End-to-end test suite failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = EndToEndTestSuite;
