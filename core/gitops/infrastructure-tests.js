#!/usr/bin/env node

/**
 * Infrastructure Testing Suite
 * Automated testing for infrastructure as code
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const yaml = require('js-yaml');
const axios = require('axios');

class InfrastructureTestSuite {
  constructor(options = {}) {
    this.testResults = [];
    this.environment = options.environment || 'test';
    this.namespace = options.namespace || 'ai-infrastructure-test';
    this.kubeconfig = options.kubeconfig || process.env.KUBECONFIG;
  }

  async runAllTests(directory) {
    console.log(`🧪 Running infrastructure tests for ${this.environment}`);

    const tests = [
      this.testKubernetesManifests.bind(this, directory),
      this.testHelmCharts.bind(this, directory),
      this.testTerraformModules.bind(this, directory),
      this.testSecurityCompliance.bind(this, directory),
      this.testResourceLimits.bind(this, directory),
      this.testNetworkingPolicies.bind(this, directory),
      this.testMonitoringSetup.bind(this, directory),
      this.testDisasterRecovery.bind(this, directory)
    ];

    for (const test of tests) {
      try {
        const result = await test();
        this.testResults.push(result);
      } catch (error) {
        this.testResults.push({
          test: test.name,
          status: 'failed',
          error: error.message,
          duration: 0
        });
      }
    }

    return this.generateTestReport();
  }

  async testKubernetesManifests(directory) {
    const startTime = Date.now();
    console.log('Testing Kubernetes manifests...');

    const k8sFiles = this.findFiles(directory, ['.yaml', '.yml'], ['templates/', 'charts/']);
    let passed = 0, failed = 0;

    for (const file of k8sFiles) {
      try {
        // Validate YAML syntax
        yaml.load(fs.readFileSync(file, 'utf8'));

        // Test with kubectl dry-run
        execSync(`kubectl apply -f ${file} --dry-run=client --namespace=${this.namespace}`, {
          stdio: 'pipe'
        });

        passed++;
      } catch (error) {
        failed++;
        console.error(`❌ Failed to validate ${file}: ${error.message}`);
      }
    }

    return {
      test: 'kubernetes-manifests',
      status: failed === 0 ? 'passed' : 'failed',
      duration: Date.now() - startTime,
      details: { total: k8sFiles.length, passed, failed }
    };
  }

  async testHelmCharts(directory) {
    const startTime = Date.now();
    console.log('Testing Helm charts...');

    if (!this.hasHelmChart(directory)) {
      return {
        test: 'helm-charts',
        status: 'skipped',
        duration: Date.now() - startTime,
        details: { reason: 'No Helm charts found' }
      };
    }

    try {
      // Lint chart
      execSync('helm lint .', { cwd: directory, stdio: 'pipe' });

      // Template chart
      execSync('helm template test . --dry-run', { cwd: directory, stdio: 'pipe' });

      return {
        test: 'helm-charts',
        status: 'passed',
        duration: Date.now() - startTime,
        details: { actions: ['lint', 'template'] }
      };
    } catch (error) {
      return {
        test: 'helm-charts',
        status: 'failed',
        duration: Date.now() - startTime,
        error: error.message
      };
    }
  }

  async testTerraformModules(directory) {
    const startTime = Date.now();
    console.log('Testing Terraform modules...');

    if (!this.hasTerraformFiles(directory)) {
      return {
        test: 'terraform-modules',
        status: 'skipped',
        duration: Date.now() - startTime,
        details: { reason: 'No Terraform files found' }
      };
    }

    try {
      // Initialize Terraform
      execSync('terraform init -backend=false', { cwd: directory, stdio: 'pipe' });

      // Validate configuration
      execSync('terraform validate', { cwd: directory, stdio: 'pipe' });

      // Plan (without applying)
      execSync('terraform plan -out=tfplan', { cwd: directory, stdio: 'pipe' });

      // Clean up plan file
      if (fs.existsSync(path.join(directory, 'tfplan'))) {
        fs.unlinkSync(path.join(directory, 'tfplan'));
      }

      return {
        test: 'terraform-modules',
        status: 'passed',
        duration: Date.now() - startTime,
        details: { actions: ['init', 'validate', 'plan'] }
      };
    } catch (error) {
      return {
        test: 'terraform-modules',
        status: 'failed',
        duration: Date.now() - startTime,
        error: error.message
      };
    }
  }

  async testSecurityCompliance(directory) {
    const startTime = Date.now();
    console.log('Testing security compliance...');

    const violations = [];

    try {
      // Run Trivy security scan
      execSync('trivy config --exit-code 1 .', { cwd: directory, stdio: 'pipe' });
    } catch (error) {
      violations.push({
        tool: 'trivy',
        severity: 'high',
        message: error.message
      });
    }

    try {
      // Run kube-score
      execSync('kube-score score --output-format ci .', { cwd: directory, stdio: 'pipe' });
    } catch (error) {
      violations.push({
        tool: 'kube-score',
        severity: 'medium',
        message: error.message
      });
    }

    return {
      test: 'security-compliance',
      status: violations.length === 0 ? 'passed' : 'failed',
      duration: Date.now() - startTime,
      details: { violations }
    };
  }

  async testResourceLimits(directory) {
    const startTime = Date.now();
    console.log('Testing resource limits...');

    const k8sFiles = this.findFiles(directory, ['.yaml', '.yml']);
    let violations = 0;

    for (const file of k8sFiles) {
      try {
        const content = yaml.load(fs.readFileSync(file, 'utf8'));

        if (content.spec?.template?.spec?.containers) {
          content.spec.template.spec.containers.forEach(container => {
            if (!container.resources?.limits || !container.resources?.requests) {
              violations++;
            }
          });
        }
      } catch (error) {
        violations++;
      }
    }

    return {
      test: 'resource-limits',
      status: violations === 0 ? 'passed' : 'failed',
      duration: Date.now() - startTime,
      details: { violations, totalChecked: k8sFiles.length }
    };
  }

  async testNetworkingPolicies(directory) {
    const startTime = Date.now();
    console.log('Testing networking policies...');

    const networkPolicies = this.findFiles(directory, ['.yaml', '.yml'])
      .filter(file => {
        try {
          const content = yaml.load(fs.readFileSync(file, 'utf8'));
          return content.kind === 'NetworkPolicy';
        } catch {
          return false;
        }
      });

    const hasDefaultDeny = networkPolicies.some(file => {
      try {
        const content = yaml.load(fs.readFileSync(file, 'utf8'));
        return content.spec?.policyTypes?.includes('Ingress') &&
               content.spec?.podSelector?.matchLabels?.app;
      } catch {
        return false;
      }
    });

    return {
      test: 'networking-policies',
      status: hasDefaultDeny ? 'passed' : 'failed',
      duration: Date.now() - startTime,
      details: {
        networkPoliciesFound: networkPolicies.length,
        hasDefaultDeny
      }
    };
  }

  async testMonitoringSetup(directory) {
    const startTime = Date.now();
    console.log('Testing monitoring setup...');

    const k8sFiles = this.findFiles(directory, ['.yaml', '.yml']);
    let hasServiceMonitor = false;
    let hasPrometheusRules = false;
    let hasGrafanaDashboard = false;

    for (const file of k8sFiles) {
      try {
        const content = yaml.load(fs.readFileSync(file, 'utf8'));
        const kind = content.kind;

        if (kind === 'ServiceMonitor') hasServiceMonitor = true;
        if (kind === 'PrometheusRule') hasPrometheusRules = true;
        if (kind === 'ConfigMap' && content.metadata?.labels?.['grafana_dashboard']) {
          hasGrafanaDashboard = true;
        }
      } catch (error) {
        // Ignore parsing errors
      }
    }

    const monitoringComplete = hasServiceMonitor && hasPrometheusRules && hasGrafanaDashboard;

    return {
      test: 'monitoring-setup',
      status: monitoringComplete ? 'passed' : 'warning',
      duration: Date.now() - startTime,
      details: {
        hasServiceMonitor,
        hasPrometheusRules,
        hasGrafanaDashboard
      }
    };
  }

  async testDisasterRecovery(directory) {
    const startTime = Date.now();
    console.log('Testing disaster recovery setup...');

    const k8sFiles = this.findFiles(directory, ['.yaml', '.yml']);
    let hasBackupJob = false;
    let hasPDB = false;
    let hasMultiRegion = false;

    for (const file of k8sFiles) {
      try {
        const content = yaml.load(fs.readFileSync(file, 'utf8'));
        const kind = content.kind;

        if (kind === 'CronJob' && content.metadata?.name?.includes('backup')) {
          hasBackupJob = true;
        }
        if (kind === 'PodDisruptionBudget') {
          hasPDB = true;
        }
        if (kind === 'Ingress' && content.spec?.ingressClassName?.includes('global')) {
          hasMultiRegion = true;
        }
      } catch (error) {
        // Ignore parsing errors
      }
    }

    const drComplete = hasBackupJob && hasPDB;

    return {
      test: 'disaster-recovery',
      status: drComplete ? 'passed' : 'warning',
      duration: Date.now() - startTime,
      details: {
        hasBackupJob,
        hasPDB,
        hasMultiRegion
      }
    };
  }

  async runIntegrationTests(baseUrl) {
    console.log(`🔗 Running integration tests against ${baseUrl}`);

    const tests = [
      this.testApiHealth.bind(this, baseUrl),
      this.testServiceConnectivity.bind(this, baseUrl),
      this.testWebSocketConnection.bind(this, baseUrl),
      this.testDatabaseConnection.bind(this, baseUrl),
      this.testLoadBalancing.bind(this, baseUrl)
    ];

    const results = [];

    for (const test of tests) {
      try {
        const result = await test();
        results.push(result);
      } catch (error) {
        results.push({
          test: test.name,
          status: 'failed',
          error: error.message,
          duration: 0
        });
      }
    }

    return results;
  }

  async testApiHealth(baseUrl) {
    const startTime = Date.now();

    try {
      const response = await axios.get(`${baseUrl}/api/health`, { timeout: 10000 });
      const isHealthy = response.status === 200 && response.data.status === 'healthy';

      return {
        test: 'api-health',
        status: isHealthy ? 'passed' : 'failed',
        duration: Date.now() - startTime,
        details: { statusCode: response.status, response: response.data }
      };
    } catch (error) {
      return {
        test: 'api-health',
        status: 'failed',
        duration: Date.now() - startTime,
        error: error.message
      };
    }
  }

  async testServiceConnectivity(baseUrl) {
    const startTime = Date.now();
    const services = ['/api/services', '/api/metrics', '/api/agents'];

    const results = [];

    for (const service of services) {
      try {
        const response = await axios.get(`${baseUrl}${service}`, { timeout: 5000 });
        results.push({ service, status: response.status });
      } catch (error) {
        results.push({ service, status: 'failed', error: error.message });
      }
    }

    const allPassed = results.every(r => r.status === 200);

    return {
      test: 'service-connectivity',
      status: allPassed ? 'passed' : 'failed',
      duration: Date.now() - startTime,
      details: { services: results }
    };
  }

  async testWebSocketConnection(baseUrl) {
    const startTime = Date.now();

    return new Promise((resolve) => {
      const WebSocket = require('ws');
      const wsUrl = baseUrl.replace(/^http/, 'ws') + '/ws';

      const ws = new WebSocket(wsUrl);

      const timeout = setTimeout(() => {
        ws.close();
        resolve({
          test: 'websocket-connection',
          status: 'failed',
          duration: Date.now() - startTime,
          error: 'Connection timeout'
        });
      }, 5000);

      ws.on('open', () => {
        clearTimeout(timeout);
        ws.close();
        resolve({
          test: 'websocket-connection',
          status: 'passed',
          duration: Date.now() - startTime
        });
      });

      ws.on('error', (error) => {
        clearTimeout(timeout);
        resolve({
          test: 'websocket-connection',
          status: 'failed',
          duration: Date.now() - startTime,
          error: error.message
        });
      });
    });
  }

  async testDatabaseConnection(baseUrl) {
    const startTime = Date.now();

    try {
      const response = await axios.get(`${baseUrl}/api/health/database`, { timeout: 5000 });

      return {
        test: 'database-connection',
        status: response.data.database === 'connected' ? 'passed' : 'failed',
        duration: Date.now() - startTime,
        details: response.data
      };
    } catch (error) {
      return {
        test: 'database-connection',
        status: 'failed',
        duration: Date.now() - startTime,
        error: error.message
      };
    }
  }

  async testLoadBalancing(baseUrl) {
    const startTime = Date.now();
    const requests = 10;
    const results = [];

    for (let i = 0; i < requests; i++) {
      try {
        const response = await axios.get(`${baseUrl}/api/health`, { timeout: 2000 });
        results.push({
          request: i + 1,
          status: response.status,
          server: response.headers['x-server'] || 'unknown'
        });
      } catch (error) {
        results.push({
          request: i + 1,
          status: 'failed',
          error: error.message
        });
      }
    }

    const successful = results.filter(r => r.status === 200).length;
    const uniqueServers = [...new Set(results.filter(r => r.server).map(r => r.server))];

    return {
      test: 'load-balancing',
      status: successful >= requests * 0.8 ? 'passed' : 'failed',
      duration: Date.now() - startTime,
      details: {
        totalRequests: requests,
        successfulRequests: successful,
        uniqueServers: uniqueServers.length,
        results
      }
    };
  }

  generateTestReport() {
    const report = {
      timestamp: new Date().toISOString(),
      environment: this.environment,
      summary: {
        total: this.testResults.length,
        passed: this.testResults.filter(t => t.status === 'passed').length,
        failed: this.testResults.filter(t => t.status === 'failed').length,
        warning: this.testResults.filter(t => t.status === 'warning').length,
        skipped: this.testResults.filter(t => t.status === 'skipped').length
      },
      results: this.testResults,
      overall: this.testResults.every(t => t.status === 'passed') ? 'PASSED' : 'FAILED'
    };

    return report;
  }

  // Utility methods
  findFiles(directory, extensions, includePaths = []) {
    const files = [];

    function scan(dir) {
      const items = fs.readdirSync(dir);

      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory() && (includePaths.length === 0 || includePaths.some(p => fullPath.includes(p)))) {
          scan(fullPath);
        } else if (stat.isFile() && extensions.some(ext => item.endsWith(ext))) {
          files.push(fullPath);
        }
      }
    }

    try {
      scan(directory);
    } catch (error) {
      console.error(`Error scanning directory ${directory}:`, error);
    }

    return files;
  }

  hasHelmChart(directory) {
    return fs.existsSync(path.join(directory, 'Chart.yaml'));
  }

  hasTerraformFiles(directory) {
    return fs.existsSync(path.join(directory, 'main.tf')) ||
           fs.existsSync(path.join(directory, 'main.tf.json'));
  }
}

// CLI interface
if (require.main === module) {
  const suite = new InfrastructureTestSuite({
    environment: process.argv[3] || 'test',
    namespace: process.argv[4] || 'ai-infrastructure-test'
  });

  const command = process.argv[2];
  const directory = process.argv[5] || '.';

  switch (command) {
    case 'unit':
      suite.runAllTests(directory)
        .then(report => {
          console.log(JSON.stringify(report, null, 2));
          process.exit(report.overall === 'PASSED' ? 0 : 1);
        })
        .catch(error => {
          console.error('Unit tests failed:', error.message);
          process.exit(1);
        });
      break;

    case 'integration':
      const baseUrl = process.argv[3];
      if (!baseUrl) {
        console.error('Usage: node infrastructure-tests.js integration <baseUrl>');
        process.exit(1);
      }
      suite.runIntegrationTests(baseUrl)
        .then(results => {
          console.log(JSON.stringify(results, null, 2));
          const passed = results.filter(r => r.status === 'passed').length;
          const total = results.length;
          console.log(`Integration tests: ${passed}/${total} passed`);
          process.exit(passed === total ? 0 : 1);
        })
        .catch(error => {
          console.error('Integration tests failed:', error.message);
          process.exit(1);
        });
      break;

    default:
      console.log('Usage:');
      console.log('  unit [environment] [namespace] [directory] - Run unit tests');
      console.log('  integration <baseUrl>                      - Run integration tests');
      process.exit(1);
  }
}

module.exports = InfrastructureTestSuite;
