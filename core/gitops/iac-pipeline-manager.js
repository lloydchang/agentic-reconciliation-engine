#!/usr/bin/env node

/**
 * Infrastructure as Code Pipeline Manager
 * Automated IaC validation, testing, and deployment
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const yaml = require('js-yaml');

class IaCPipelineManager {
  constructor(options = {}) {
    this.repoPath = options.repoPath || process.cwd();
    this.kubeconfig = options.kubeconfig || process.env.KUBECONFIG;
    this.environments = ['dev', 'staging', 'prod'];
    this.validationRules = this.loadValidationRules();
  }

  loadValidationRules() {
    return {
      kubernetes: {
        requiredLabels: ['app', 'version', 'environment'],
        securityChecks: ['noPrivilegedContainers', 'noHostMounts', 'validResourceLimits'],
        bestPractices: ['hasHealthChecks', 'hasResourceRequests', 'usesSecretsForCredentials']
      },
      helm: {
        chartStructure: ['Chart.yaml', 'values.yaml', 'templates/'],
        linting: true,
        security: ['noLatestTag', 'validImageRegistry']
      },
      terraform: {
        providers: ['aws', 'gcp', 'azure'],
        modules: ['vpc', 'eks', 'rds'],
        validation: ['tflint', 'terraform-validate']
      }
    };
  }

  async validateInfrastructure(directory) {
    console.log(`🔍 Validating infrastructure in ${directory}`);

    const results = {
      kubernetes: await this.validateKubernetes(directory),
      helm: await this.validateHelm(directory),
      terraform: await this.validateTerraform(directory),
      security: await this.runSecurityScans(directory)
    };

    return this.generateValidationReport(results);
  }

  async validateKubernetes(directory) {
    const k8sFiles = this.findFiles(directory, ['.yaml', '.yml'], ['templates/', 'charts/']);
    const violations = [];

    for (const file of k8sFiles) {
      try {
        const content = yaml.load(fs.readFileSync(file, 'utf8'));
        const fileViolations = this.checkKubernetesBestPractices(content, file);
        violations.push(...fileViolations);
      } catch (error) {
        violations.push({
          file,
          severity: 'error',
          rule: 'yaml-parsing',
          message: `Failed to parse YAML: ${error.message}`
        });
      }
    }

    return violations;
  }

  checkKubernetesBestPractices(content, file) {
    const violations = [];

    // Check required labels
    if (content.metadata?.labels) {
      const requiredLabels = this.validationRules.kubernetes.requiredLabels;
      for (const label of requiredLabels) {
        if (!content.metadata.labels[label]) {
          violations.push({
            file,
            severity: 'warning',
            rule: 'missing-required-label',
            message: `Missing required label: ${label}`
          });
        }
      }
    }

    // Security checks
    if (content.spec?.template?.spec?.containers) {
      content.spec.template.spec.containers.forEach((container, index) => {
        if (container.securityContext?.privileged) {
          violations.push({
            file,
            severity: 'critical',
            rule: 'privileged-container',
            message: `Container ${index} runs in privileged mode`
          });
        }
      });
    }

    return violations;
  }

  async validateHelm(directory) {
    const violations = [];

    if (this.hasHelmChart(directory)) {
      try {
        execSync('helm lint .', { cwd: directory, stdio: 'pipe' });
      } catch (error) {
        violations.push({
          file: 'Chart.yaml',
          severity: 'error',
          rule: 'helm-lint',
          message: `Helm lint failed: ${error.message}`
        });
      }
    }

    return violations;
  }

  async validateTerraform(directory) {
    const violations = [];

    if (this.hasTerraformFiles(directory)) {
      try {
        execSync('terraform validate', { cwd: directory, stdio: 'pipe' });
      } catch (error) {
        violations.push({
          file: 'main.tf',
          severity: 'error',
          rule: 'terraform-validate',
          message: `Terraform validation failed: ${error.message}`
        });
      }
    }

    return violations;
  }

  async runSecurityScans(directory) {
    const violations = [];

    // Run Trivy for container security
    try {
      execSync('trivy config .', { cwd: directory, stdio: 'pipe' });
    } catch (error) {
      violations.push({
        file: 'Dockerfile',
        severity: 'high',
        rule: 'security-scan',
        message: `Security scan failed: ${error.message}`
      });
    }

    return violations;
  }

  generateValidationReport(results) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalViolations: 0,
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        passed: true
      },
      details: results
    };

    // Count violations by severity
    Object.values(results).forEach(category => {
      category.forEach(violation => {
        report.summary.totalViolations++;
        report.summary[violation.severity] = (report.summary[violation.severity] || 0) + 1;

        if (violation.severity === 'critical') {
          report.summary.passed = false;
        }
      });
    });

    return report;
  }

  async deployInfrastructure(environment, directory) {
    console.log(`🚀 Deploying to ${environment} from ${directory}`);

    // Validate before deployment
    const validationReport = await this.validateInfrastructure(directory);
    if (!validationReport.summary.passed) {
      throw new Error(`Validation failed: ${validationReport.summary.totalViolations} violations found`);
    }

    // Deploy based on infrastructure type
    if (this.hasKubernetesFiles(directory)) {
      return await this.deployKubernetes(environment, directory);
    } else if (this.hasHelmChart(directory)) {
      return await this.deployHelm(environment, directory);
    } else if (this.hasTerraformFiles(directory)) {
      return await this.deployTerraform(environment, directory);
    }

    throw new Error('No supported infrastructure files found');
  }

  async deployKubernetes(environment, directory) {
    const k8sFiles = this.findFiles(directory, ['.yaml', '.yml']);

    for (const file of k8sFiles) {
      execSync(`kubectl apply -f ${file} --namespace=${this.getNamespace(environment)}`, {
        stdio: 'inherit',
        env: { ...process.env, KUBECONFIG: this.kubeconfig }
      });
    }

    return { status: 'success', files: k8sFiles.length };
  }

  async deployHelm(environment, directory) {
    const releaseName = `ai-portal-${environment}`;
    const namespace = this.getNamespace(environment);

    execSync(`helm upgrade --install ${releaseName} . --namespace ${namespace} --create-namespace`, {
      cwd: directory,
      stdio: 'inherit',
      env: { ...process.env, KUBECONFIG: this.kubeconfig }
    });

    return { status: 'success', release: releaseName };
  }

  async deployTerraform(environment, directory) {
    execSync('terraform init', { cwd: directory, stdio: 'inherit' });
    execSync(`terraform apply -auto-approve -var environment=${environment}`, {
      cwd: directory,
      stdio: 'inherit'
    });

    return { status: 'success', environment };
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

    scan(directory);
    return files;
  }

  hasKubernetesFiles(directory) {
    return this.findFiles(directory, ['.yaml', '.yml']).length > 0;
  }

  hasHelmChart(directory) {
    return fs.existsSync(path.join(directory, 'Chart.yaml'));
  }

  hasTerraformFiles(directory) {
    return fs.existsSync(path.join(directory, 'main.tf')) || fs.existsSync(path.join(directory, 'main.tf.json'));
  }

  getNamespace(environment) {
    return `ai-infrastructure-${environment}`;
  }
}

// CLI interface
if (require.main === module) {
  const manager = new IaCPipelineManager();

  const command = process.argv[2];
  const directory = process.argv[3] || '.';
  const environment = process.argv[4];

  switch (command) {
    case 'validate':
      manager.validateInfrastructure(directory)
        .then(report => {
          console.log(JSON.stringify(report, null, 2));
          process.exit(report.summary.passed ? 0 : 1);
        })
        .catch(error => {
          console.error('Validation failed:', error.message);
          process.exit(1);
        });
      break;

    case 'deploy':
      if (!environment) {
        console.error('Usage: node iac-pipeline.js deploy <directory> <environment>');
        process.exit(1);
      }
      manager.deployInfrastructure(environment, directory)
        .then(result => {
          console.log('Deployment successful:', result);
          process.exit(0);
        })
        .catch(error => {
          console.error('Deployment failed:', error.message);
          process.exit(1);
        });
      break;

    default:
      console.log('Usage:');
      console.log('  validate <directory>    - Validate infrastructure');
      console.log('  deploy <directory> <env> - Deploy infrastructure');
      process.exit(1);
  }
}

module.exports = IaCPipelineManager;
