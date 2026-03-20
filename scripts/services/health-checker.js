#!/usr/bin/env node

/**
 * Deployment Health Check Script
 * Validates deployment status and service health
 */

const axios = require('axios');
const { spawn } = require('child_process');

class DeploymentHealthChecker {
  constructor(baseUrl = 'http://localhost:5001') {
    this.baseUrl = baseUrl;
    this.checks = [];
  }

  async checkEndpoint(endpoint, expectedStatus = 200, description = '') {
    try {
      const startTime = Date.now();
      const response = await axios.get(`${this.baseUrl}${endpoint}`, {
        timeout: 10000,
        validateStatus: () => true
      });
      const duration = Date.now() - startTime;

      const result = {
        endpoint,
        description: description || endpoint,
        status: response.status,
        expected: expectedStatus,
        responseTime: duration,
        success: response.status === expectedStatus
      };

      this.checks.push(result);

      if (result.success) {
        console.log(`✅ ${endpoint} - ${description} (${duration}ms)`);
      } else {
        console.log(`❌ ${endpoint} - Expected ${expectedStatus}, got ${response.status}`);
      }

      return result;
    } catch (error) {
      const result = {
        endpoint,
        description: description || endpoint,
        status: 'ERROR',
        expected: expectedStatus,
        error: error.message,
        success: false
      };

      this.checks.push(result);
      console.log(`❌ ${endpoint} - ${error.message}`);
      return result;
    }
  }

  async checkServiceConnectivity() {
    console.log('🔗 Checking external service connectivity');

    const services = [
      { name: 'ArgoCD', url: process.env.ARGOCD_URL || 'http://localhost:8080/api/v1/applications' },
      { name: 'Langfuse', url: process.env.LANGFUSE_URL || 'http://localhost:3000/api/public/usage' },
      { name: 'Prometheus', url: process.env.PROMETHEUS_URL || 'http://localhost:9090/api/v1/query?query=up' },
      { name: 'Elasticsearch', url: process.env.ELASTICSEARCH_URL || 'http://localhost:9200/_cluster/health' }
    ];

    for (const service of services) {
      try {
        const response = await axios.get(service.url, {
          timeout: 5000,
          validateStatus: () => true
        });

        const result = {
          service: service.name,
          url: service.url,
          status: response.status,
          success: response.status < 400,
          responseTime: response.data?.responseTime || 'unknown'
        };

        this.checks.push(result);

        if (result.success) {
          console.log(`✅ ${service.name} connectivity OK (${response.status})`);
        } else {
          console.log(`⚠️ ${service.name} returned ${response.status} - may be using mock data`);
        }
      } catch (error) {
        const result = {
          service: service.name,
          url: service.url,
          status: 'ERROR',
          error: error.message,
          success: false
        };

        this.checks.push(result);
        console.log(`⚠️ ${service.name} not reachable - using mock data: ${error.message}`);
      }
    }
  }

  async checkKubernetesResources() {
    console.log('☸️ Checking Kubernetes resources');

    return new Promise((resolve) => {
      const kubectl = spawn('kubectl', ['get', 'pods', '-o', 'json'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      kubectl.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      kubectl.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      kubectl.on('close', (code) => {
        if (code === 0) {
          try {
            const data = JSON.parse(stdout);
            const pods = data.items || [];

            const portalPods = pods.filter(pod =>
              pod.metadata?.labels?.app === 'ai-infrastructure-portal'
            );

            const result = {
              resource: 'kubernetes-pods',
              portalPods: portalPods.length,
              totalPods: pods.length,
              success: portalPods.length > 0
            };

            this.checks.push(result);

            if (result.success) {
              console.log(`✅ Found ${portalPods.length} AI Infrastructure Portal pods`);
            } else {
              console.log('❌ No AI Infrastructure Portal pods found');
            }
          } catch (error) {
            const result = {
              resource: 'kubernetes-pods',
              error: error.message,
              success: false
            };
            this.checks.push(result);
            console.log(`❌ Failed to parse kubectl output: ${error.message}`);
          }
        } else {
          const result = {
            resource: 'kubernetes-pods',
            error: stderr,
            success: false
          };
          this.checks.push(result);
          console.log(`❌ kubectl command failed: ${stderr}`);
        }
        resolve();
      });
    });
  }

  async checkDockerContainers() {
    console.log('🐳 Checking Docker containers');

    return new Promise((resolve) => {
      const docker = spawn('docker', ['ps', '--format', 'json'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      docker.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      docker.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      docker.on('close', (code) => {
        if (code === 0) {
          const lines = stdout.trim().split('\n').filter(line => line.trim());
          const containers = lines.map(line => {
            try {
              return JSON.parse(line);
            } catch {
              return null;
            }
          }).filter(Boolean);

          const portalContainers = containers.filter(container =>
            container.Names?.some(name => name.includes('ai-infrastructure-portal'))
          );

          const result = {
            resource: 'docker-containers',
            portalContainers: portalContainers.length,
            totalContainers: containers.length,
            success: portalContainers.length > 0
          };

          this.checks.push(result);

          if (result.success) {
            console.log(`✅ Found ${portalContainers.length} AI Infrastructure Portal containers`);
          } else {
            console.log('⚠️ No AI Infrastructure Portal containers found - may be using direct Node.js');
          }
        } else {
          const result = {
            resource: 'docker-containers',
            error: stderr,
            success: false
          };
          this.checks.push(result);
          console.log(`❌ docker command failed: ${stderr}`);
        }
        resolve();
      });
    });
  }

  async runFullHealthCheck() {
    console.log('🏥 Starting comprehensive deployment health check');
    console.log('=' .repeat(60));

    // API endpoint checks
    await this.checkEndpoint('/api/health', 200, 'Basic health check');
    await this.checkEndpoint('/api/health/detailed', 200, 'Detailed health assessment');
    await this.checkEndpoint('/api/services', 200, 'Service status');
    await this.checkEndpoint('/api/agents', 200, 'Agent data');
    await this.checkEndpoint('/api/skills', 200, 'Skills repository');
    await this.checkEndpoint('/api/metrics', 200, 'System metrics');

    // Authentication endpoints (may require auth)
    await this.checkEndpoint('/auth/login', 200, 'Authentication endpoint');
    await this.checkEndpoint('/api/users', 401, 'User management (should require auth)');

    // External service connectivity
    await this.checkServiceConnectivity();

    // Infrastructure checks
    await this.checkKubernetesResources();
    await this.checkDockerContainers();

    // Generate summary
    const summary = this.generateSummary();
    console.log('\n' + '='.repeat(60));
    console.log('🏥 Health Check Summary:');
    console.log(`Total Checks: ${summary.total}`);
    console.log(`Passed: ${summary.passed}`);
    console.log(`Failed: ${summary.failed}`);
    console.log(`Warnings: ${summary.warnings}`);

    if (summary.failed > 0) {
      console.log('\n❌ Failed checks:');
      summary.failedChecks.forEach(check => {
        console.log(`  - ${check.endpoint || check.service || check.resource}: ${check.error || 'Failed'}`);
      });
    }

    return summary;
  }

  generateSummary() {
    const total = this.checks.length;
    const passed = this.checks.filter(c => c.success).length;
    const failed = total - passed;
    const warnings = this.checks.filter(c => !c.success && !c.error).length;

    const failedChecks = this.checks.filter(c => !c.success);

    return {
      total,
      passed,
      failed,
      warnings,
      failedChecks,
      success: failed === 0
    };
  }

  async saveReport(filename = 'health-check-report.json') {
    const report = {
      timestamp: new Date().toISOString(),
      target: this.baseUrl,
      summary: this.generateSummary(),
      checks: this.checks
    };

    await require('fs').promises.writeFile(filename, JSON.stringify(report, null, 2));
    console.log(`📄 Health check report saved to ${filename}`);
  }
}

// CLI runner
async function main() {
  const args = process.argv.slice(2);
  const baseUrl = args[0] || 'http://localhost:5001';

  const checker = new DeploymentHealthChecker(baseUrl);

  try {
    const summary = await checker.runFullHealthCheck();
    await checker.saveReport();

    if (!summary.success) {
      console.log('\n❌ Deployment health check failed!');
      process.exit(1);
    } else {
      console.log('\n✅ Deployment health check passed!');
    }
  } catch (error) {
    console.error('Health check failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = DeploymentHealthChecker;
