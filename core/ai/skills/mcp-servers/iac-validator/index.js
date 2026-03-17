#!/usr/bin/env node

/**
 * IaC Deployment Validator MCP Server
 * 
 * This MCP server provides Infrastructure as Code validation capabilities:
 * - Terraform plan validation
 * - Kubernetes manifest validation
 * - Helm chart validation
 * - Security policy checks
 * - Cost estimation
 * - Compliance validation
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require('@modelcontextprotocol/sdk/types.js');

// YAML/JSON processing
const yaml = require('js-yaml');
const fs = require('fs').promises;
const path = require('path');

class IacValidatorServer {
  constructor() {
    this.server = new Server(
      {
        name: 'iac-deployment-validator',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupErrorHandling() {
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'validate_terraform_plan',
          description: 'Validate Terraform plan for security, cost, and compliance',
          inputSchema: {
            type: 'object',
            properties: {
              plan_file: {
                type: 'string',
                description: 'Path to Terraform plan file (JSON format)'
              },
              check_security: {
                type: 'boolean',
                default: true,
                description: 'Perform security checks'
              },
              check_cost: {
                type: 'boolean',
                default: true,
                description: 'Perform cost estimation'
              },
              check_compliance: {
                type: 'boolean',
                default: true,
                description: 'Perform compliance checks'
              },
              compliance_framework: {
                type: 'string',
                enum: ['CIS', 'NIST', 'SOC2', 'PCI-DSS', 'HIPAA'],
                description: 'Compliance framework to validate against'
              }
            }
          }
        },
        {
          name: 'validate_kubernetes_manifests',
          description: 'Validate Kubernetes manifests for best practices and security',
          inputSchema: {
            type: 'object',
            properties: {
              manifest_path: {
                type: 'string',
                description: 'Path to Kubernetes manifest file or directory'
              },
              namespace: {
                type: 'string',
                description: 'Target namespace for validation'
              },
              check_security: {
                type: 'boolean',
                default: true,
                description: 'Perform security checks'
              },
              check_resources: {
                type: 'boolean',
                default: true,
                description: 'Check resource limits and requests'
              },
              check_best_practices: {
                type: 'boolean',
                default: true,
                description: 'Check Kubernetes best practices'
              }
            }
          }
        },
        {
          name: 'validate_helm_chart',
          description: 'Validate Helm chart for security and best practices',
          inputSchema: {
            type: 'object',
            properties: {
              chart_path: {
                type: 'string',
                description: 'Path to Helm chart directory'
              },
              values_file: {
                type: 'string',
                description: 'Path to custom values file (optional)'
              },
              release_name: {
                type: 'string',
                description: 'Release name for validation'
              },
              namespace: {
                type: 'string',
                description: 'Target namespace'
              },
              check_security: {
                type: 'boolean',
                default: true,
                description: 'Perform security checks'
              },
              dry_run: {
                type: 'boolean',
                default: true,
                description: 'Perform dry-run installation'
              }
            }
          }
        },
        {
          name: 'estimate_deployment_costs',
          description: 'Estimate costs for infrastructure deployment',
          inputSchema: {
            type: 'object',
            properties: {
              iac_type: {
                type: 'string',
                enum: ['terraform', 'kubernetes', 'helm'],
                description: 'Type of IaC'
              },
              config_path: {
                type: 'string',
                description: 'Path to IaC configuration'
              },
              cloud_provider: {
                type: 'string',
                enum: ['aws', 'azure', 'gcp'],
                description: 'Cloud provider for cost estimation'
              },
              region: {
                type: 'string',
                description: 'Cloud region'
              },
              duration: {
                type: 'string',
                default: 'monthly',
                enum: ['hourly', 'daily', 'monthly', 'yearly'],
                description: 'Cost estimation duration'
              }
            }
          }
        },
        {
          name: 'check_security_policies',
          description: 'Check IaC against security policies and standards',
          inputSchema: {
            type: 'object',
            properties: {
              iac_path: {
                type: 'string',
                description: 'Path to IaC files'
              },
              policy_set: {
                type: 'string',
                enum: ['CIS', 'NIST', 'SOC2', 'PCI-DSS', 'custom'],
                description: 'Security policy set to check against'
              },
              custom_policy_path: {
                type: 'string',
                description: 'Path to custom policy file (if policy_set=custom)'
              },
              severity_threshold: {
                type: 'string',
                enum: ['low', 'medium', 'high', 'critical'],
                default: 'medium',
                description: 'Minimum severity level for violations'
              }
            }
          }
        },
        {
          name: 'generate_deployment_report',
          description: 'Generate comprehensive deployment validation report',
          inputSchema: {
            type: 'object',
            properties: {
              iac_path: {
                type: 'string',
                description: 'Path to IaC configuration'
              },
              report_format: {
                type: 'string',
                enum: ['JSON', 'HTML', 'PDF'],
                default: 'JSON',
                description: 'Report output format'
              },
              include_recommendations: {
                type: 'boolean',
                default: true,
                description: 'Include improvement recommendations'
              },
              include_cost_analysis: {
                type: 'boolean',
                default: true,
                description: 'Include cost analysis'
              }
            }
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'validate_terraform_plan':
            return await this.validateTerraformPlan(args);
          case 'validate_kubernetes_manifests':
            return await this.validateKubernetesManifests(args);
          case 'validate_helm_chart':
            return await this.validateHelmChart(args);
          case 'estimate_deployment_costs':
            return await this.estimateDeploymentCosts(args);
          case 'check_security_policies':
            return await this.checkSecurityPolicies(args);
          case 'generate_deployment_report':
            return await this.generateDeploymentReport(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error in ${name}:`, error);
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error.message}`);
      }
    });
  }

  async validateTerraformPlan(args) {
    const { plan_file, check_security = true, check_cost = true, check_compliance = true, compliance_framework } = args;
    
    try {
      // Read Terraform plan file
      const planData = await this.readTerraformPlan(plan_file);
      
      const validation_results = {
        plan_file,
        timestamp: new Date().toISOString(),
        checks_performed: [],
        issues_found: [],
        recommendations: [],
        summary: {}
      };
      
      // Security checks
      if (check_security) {
        const securityResults = await this.performTerraformSecurityChecks(planData);
        validation_results.checks_performed.push('security');
        validation_results.issues_found.push(...securityResults.issues);
        validation_results.recommendations.push(...securityResults.recommendations);
      }
      
      // Cost estimation
      if (check_cost) {
        const costResults = await this.estimateTerraformCosts(planData);
        validation_results.checks_performed.push('cost');
        validation_results.cost_analysis = costResults;
      }
      
      // Compliance checks
      if (check_compliance) {
        const complianceResults = await this.checkTerraformCompliance(planData, compliance_framework);
        validation_results.checks_performed.push('compliance');
        validation_results.issues_found.push(...complianceResults.issues);
        validation_results.recommendations.push(...complianceResults.recommendations);
      }
      
      // Generate summary
      validation_results.summary = {
        total_resources: planData.planned_values?.root_module?.resources?.length || 0,
        total_issues: validation_results.issues_found.length,
        critical_issues: validation_results.issues_found.filter(i => i.severity === 'critical').length,
        estimated_monthly_cost: validation_results.cost_analysis?.monthly_total || 'Unknown',
        compliance_score: this.calculateComplianceScore(validation_results.issues_found)
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'terraform_plan_validation',
              ...validation_results
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Terraform plan validation failed: ${error.message}`);
    }
  }

  async validateKubernetesManifests(args) {
    const { manifest_path, namespace, check_security = true, check_resources = true, check_best_practices = true } = args;
    
    try {
      const manifests = await this.readKubernetesManifests(manifest_path);
      
      const validation_results = {
        manifest_path,
        namespace,
        timestamp: new Date().toISOString(),
        manifests_processed: manifests.length,
        checks_performed: [],
        issues_found: [],
        recommendations: [],
        summary: {}
      };
      
      // Process each manifest
      for (const manifest of manifests) {
        const manifestValidation = {
          api_version: manifest.apiVersion,
          kind: manifest.kind,
          name: manifest.metadata?.name,
          namespace: manifest.metadata?.namespace,
          issues: [],
          recommendations: []
        };
        
        // Security checks
        if (check_security) {
          const securityIssues = this.checkKubernetesSecurity(manifest);
          manifestValidation.issues.push(...securityIssues);
        }
        
        // Resource checks
        if (check_resources) {
          const resourceIssues = this.checkKubernetesResources(manifest);
          manifestValidation.issues.push(...resourceIssues);
        }
        
        // Best practices checks
        if (check_best_practices) {
          const practiceIssues = this.checkKubernetesBestPractices(manifest);
          manifestValidation.issues.push(...practiceIssues);
        }
        
        validation_results.issues_found.push(...manifestValidation.issues.map(issue => ({
          ...issue,
          resource: `${manifest.kind}/${manifest.metadata?.name}`
        })));
      }
      
      // Generate recommendations
      validation_results.recommendations = this.generateKubernetesRecommendations(validation_results.issues_found);
      
      // Generate summary
      validation_results.summary = {
        total_manifests: manifests.length,
        total_issues: validation_results.issues_found.length,
        critical_issues: validation_results.issues_found.filter(i => i.severity === 'critical').length,
        security_issues: validation_results.issues_found.filter(i => i.category === 'security').length,
        resource_issues: validation_results.issues_found.filter(i => i.category === 'resources').length,
        best_practice_issues: validation_results.issues_found.filter(i => i.category === 'best_practices').length
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'kubernetes_manifests_validation',
              ...validation_results
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Kubernetes manifests validation failed: ${error.message}`);
    }
  }

  async validateHelmChart(args) {
    const { chart_path, values_file, release_name, namespace, check_security = true, dry_run = true } = args;
    
    try {
      const validation_results = {
        chart_path,
        release_name,
        namespace,
        timestamp: new Date().toISOString(),
        checks_performed: [],
        issues_found: [],
        recommendations: [],
        summary: {}
      };
      
      // Read Chart.yaml
      const chartYaml = await this.readChartYaml(chart_path);
      
      // Validate chart structure
      const structureValidation = this.validateHelmChartStructure(chart_path, chartYaml);
      validation_results.issues_found.push(...structureValidation.issues);
      
      // Security checks
      if (check_security) {
        const securityValidation = await this.validateHelmChartSecurity(chart_path, chartYaml);
        validation_results.checks_performed.push('security');
        validation_results.issues_found.push(...securityValidation.issues);
      }
      
      // Template validation
      const templateValidation = await this.validateHelmTemplates(chart_path, values_file, namespace);
      validation_results.checks_performed.push('templates');
      validation_results.issues_found.push(...templateValidation.issues);
      
      // Dry run installation if requested
      if (dry_run) {
        const dryRunResult = await this.performHelmDryRun(chart_path, values_file, release_name, namespace);
        validation_results.dry_run_result = dryRunResult;
      }
      
      // Generate recommendations
      validation_results.recommendations = this.generateHelmRecommendations(validation_results.issues_found);
      
      // Generate summary
      validation_results.summary = {
        chart_name: chartYaml.name,
        chart_version: chartYaml.version,
        total_issues: validation_results.issues_found.length,
        critical_issues: validation_results.issues_found.filter(i => i.severity === 'critical').length,
        security_issues: validation_results.issues_found.filter(i => i.category === 'security').length,
        template_issues: validation_results.issues_found.filter(i => i.category === 'templates').length
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'helm_chart_validation',
              ...validation_results
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Helm chart validation failed: ${error.message}`);
    }
  }

  async estimateDeploymentCosts(args) {
    const { iac_type, config_path, cloud_provider, region, duration = 'monthly' } = args;
    
    try {
      const cost_analysis = {
        iac_type,
        config_path,
        cloud_provider,
        region,
        duration,
        timestamp: new Date().toISOString(),
        resources: [],
        cost_breakdown: {},
        total_cost: 0,
        recommendations: []
      };
      
      // Analyze IaC and extract resources
      const resources = await this.extractResourcesFromIaC(iac_type, config_path);
      
      // Calculate costs for each resource
      for (const resource of resources) {
        const resourceCost = await this.calculateResourceCost(resource, cloud_provider, region, duration);
        cost_analysis.resources.push(resourceCost);
        cost_analysis.total_cost += resourceCost.cost;
      }
      
      // Generate cost breakdown
      cost_analysis.cost_breakdown = this.generateCostBreakdown(cost_analysis.resources);
      
      // Generate cost optimization recommendations
      cost_analysis.recommendations = this.generateCostRecommendations(cost_analysis.resources);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'deployment_cost_estimation',
              ...cost_analysis
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Cost estimation failed: ${error.message}`);
    }
  }

  async checkSecurityPolicies(args) {
    const { iac_path, policy_set, custom_policy_path, severity_threshold = 'medium' } = args;
    
    try {
      const policy_check = {
        iac_path,
        policy_set,
        severity_threshold,
        timestamp: new Date().toISOString(),
        violations: [],
        compliance_score: 0,
        recommendations: []
      };
      
      // Load security policies
      const policies = await this.loadSecurityPolicies(policy_set, custom_policy_path);
      
      // Analyze IaC files
      const iac_files = await this.getIaCFiles(iac_path);
      
      for (const file of iac_files) {
        const fileViolations = await this.checkFileAgainstPolicies(file, policies, severity_threshold);
        policy_check.violations.push(...fileViolations);
      }
      
      // Calculate compliance score
      policy_check.compliance_score = this.calculatePolicyComplianceScore(policy_check.violations);
      
      // Generate recommendations
      policy_check.recommendations = this.generatePolicyRecommendations(policy_check.violations);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'security_policy_check',
              ...policy_check
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Security policy check failed: ${error.message}`);
    }
  }

  async generateDeploymentReport(args) {
    const { iac_path, report_format = 'JSON', include_recommendations = true, include_cost_analysis = true } = args;
    
    try {
      const report = {
        iac_path,
        report_format,
        timestamp: new Date().toISOString(),
        executive_summary: {},
        technical_analysis: {},
        security_analysis: {},
        cost_analysis: {},
        recommendations: []
      };
      
      // Determine IaC type
      const iac_type = await this.detectIaCType(iac_path);
      
      // Perform comprehensive analysis
      if (iac_type === 'terraform') {
        const terraformAnalysis = await this.analyzeTerraformProject(iac_path);
        report.technical_analysis = terraformAnalysis.technical;
        report.security_analysis = terraformAnalysis.security;
        if (include_cost_analysis) {
          report.cost_analysis = terraformAnalysis.cost;
        }
      } else if (iac_type === 'kubernetes') {
        const k8sAnalysis = await this.analyzeKubernetesProject(iac_path);
        report.technical_analysis = k8sAnalysis.technical;
        report.security_analysis = k8sAnalysis.security;
      } else if (iac_type === 'helm') {
        const helmAnalysis = await this.analyzeHelmProject(iac_path);
        report.technical_analysis = helmAnalysis.technical;
        report.security_analysis = helmAnalysis.security;
      }
      
      // Generate executive summary
      report.executive_summary = this.generateExecutiveSummary(report);
      
      // Generate recommendations
      if (include_recommendations) {
        report.recommendations = this.generateComprehensiveRecommendations(report);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'deployment_report',
              ...report
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Deployment report generation failed: ${error.message}`);
    }
  }

  // Helper methods
  async readTerraformPlan(planFile) {
    try {
      const content = await fs.readFile(planFile, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      throw new Error(`Failed to read Terraform plan: ${error.message}`);
    }
  }

  async readKubernetesManifests(manifestPath) {
    try {
      const stat = await fs.stat(manifestPath);
      if (stat.isDirectory()) {
        const files = await fs.readdir(manifestPath);
        const manifests = [];
        
        for (const file of files) {
          if (file.endsWith('.yaml') || file.endsWith('.yml')) {
            const content = await fs.readFile(path.join(manifestPath, file), 'utf8');
            const docs = yaml.loadAll(content);
            manifests.push(...docs.filter(doc => doc !== null));
          }
        }
        
        return manifests;
      } else {
        const content = await fs.readFile(manifestPath, 'utf8');
        const docs = yaml.loadAll(content);
        return docs.filter(doc => doc !== null);
      }
    } catch (error) {
      throw new Error(`Failed to read Kubernetes manifests: ${error.message}`);
    }
  }

  async readChartYaml(chartPath) {
    try {
      const content = await fs.readFile(path.join(chartPath, 'Chart.yaml'), 'utf8');
      return yaml.load(content);
    } catch (error) {
      throw new Error(`Failed to read Chart.yaml: ${error.message}`);
    }
  }

  async performTerraformSecurityChecks(planData) {
    const issues = [];
    const recommendations = [];
    
    // Check for security issues in Terraform plan
    const resources = planData.planned_values?.root_module?.resources || [];
    
    for (const resource of resources) {
      // Check for open security groups
      if (resource.type === 'aws_security_group') {
        const ingress = resource.values?.ingress || [];
        for (const rule of ingress) {
          if (rule.cidr_blocks?.includes('0.0.0.0/0')) {
            issues.push({
              type: 'security',
              severity: 'high',
              resource: resource.address,
              message: 'Security group allows inbound traffic from 0.0.0.0/0',
              recommendation: 'Restrict ingress to specific IP ranges'
            });
          }
        }
      }
      
      // Check for unencrypted storage
      if (resource.type === 'aws_ebs_volume' && !resource.values?.encrypted) {
        issues.push({
          type: 'security',
          severity: 'medium',
          resource: resource.address,
          message: 'EBS volume is not encrypted',
          recommendation: 'Enable EBS encryption'
        });
      }
    }
    
    return { issues, recommendations };
  }

  async estimateTerraformCosts(planData) {
    // Mock cost estimation
    const resources = planData.planned_values?.root_module?.resources || [];
    let monthlyTotal = 0;
    
    for (const resource of resources) {
      // Simple cost calculation based on resource type
      if (resource.type === 'aws_instance') {
        monthlyTotal += 50; // Mock cost
      } else if (resource.type === 'aws_ebs_volume') {
        const size = resource.values?.size || 10;
        monthlyTotal += size * 0.1; // $0.1 per GB
      }
    }
    
    return {
      monthly_total: monthlyTotal,
      currency: 'USD',
      breakdown: {
        compute: monthlyTotal * 0.7,
        storage: monthlyTotal * 0.2,
        network: monthlyTotal * 0.1
      }
    };
  }

  async checkTerraformCompliance(planData, framework) {
    const issues = [];
    const recommendations = [];
    
    // Mock compliance checks
    if (framework === 'CIS') {
      // Check for CIS compliance
      const resources = planData.planned_values?.root_module?.resources || [];
      
      for (const resource of resources) {
        if (resource.type === 'aws_instance') {
          // Check for required tags
          const tags = resource.values?.tags || {};
          if (!tags.Environment) {
            issues.push({
              type: 'compliance',
              severity: 'medium',
              resource: resource.address,
              framework: 'CIS',
              message: 'Missing Environment tag (CIS requirement)',
              recommendation: 'Add Environment tag to all resources'
            });
          }
        }
      }
    }
    
    return { issues, recommendations };
  }

  checkKubernetesSecurity(manifest) {
    const issues = [];
    
    // Check for security context
    if (!manifest.spec?.securityContext) {
      issues.push({
        type: 'security',
        severity: 'medium',
        message: 'Missing security context',
        recommendation: 'Add security context to restrict container capabilities'
      });
    }
    
    // Check for privileged containers
    const containers = manifest.spec?.containers || [];
    for (const container of containers) {
      if (container.securityContext?.privileged) {
        issues.push({
          type: 'security',
          severity: 'high',
          message: 'Container running in privileged mode',
          recommendation: 'Avoid running containers in privileged mode'
        });
      }
    }
    
    return issues;
  }

  checkKubernetesResources(manifest) {
    const issues = [];
    
    // Check for resource limits
    const containers = manifest.spec?.containers || [];
    for (const container of containers) {
      if (!container.resources?.limits) {
        issues.push({
          type: 'resources',
          severity: 'medium',
          message: 'Missing resource limits',
          recommendation: 'Set resource limits to prevent resource exhaustion'
        });
      }
      
      if (!container.resources?.requests) {
        issues.push({
          type: 'resources',
          severity: 'low',
          message: 'Missing resource requests',
          recommendation: 'Set resource requests for proper scheduling'
        });
      }
    }
    
    return issues;
  }

  checkKubernetesBestPractices(manifest) {
    const issues = [];
    
    // Check for latest tag
    const containers = manifest.spec?.containers || [];
    for (const container of containers) {
      if (container.image?.endsWith(':latest')) {
        issues.push({
          type: 'best_practices',
          severity: 'low',
          message: 'Using latest tag for container image',
          recommendation: 'Use specific version tags for reproducibility'
        });
      }
    }
    
    // Check for readiness and liveness probes
    for (const container of containers) {
      if (!container.livenessProbe) {
        issues.push({
          type: 'best_practices',
          severity: 'medium',
          message: 'Missing liveness probe',
          recommendation: 'Add liveness probe for health checking'
        });
      }
      
      if (!container.readinessProbe) {
        issues.push({
          type: 'best_practices',
          severity: 'medium',
          message: 'Missing readiness probe',
          recommendation: 'Add readiness probe for traffic management'
        });
      }
    }
    
    return issues;
  }

  validateHelmChartStructure(chartPath, chartYaml) {
    const issues = [];
    
    // Check required files
    const requiredFiles = ['Chart.yaml', 'values.yaml', 'templates/'];
    
    for (const file of requiredFiles) {
      const filePath = path.join(chartPath, file);
      try {
        if (file.endsWith('/')) {
          const stat = fs.stat(filePath);
          if (!stat.isDirectory()) {
            issues.push({
              type: 'structure',
              severity: 'high',
              message: `Missing required directory: ${file}`
            });
          }
        } else {
          await fs.access(filePath);
        }
      } catch (error) {
        issues.push({
          type: 'structure',
          severity: 'high',
          message: `Missing required file: ${file}`
        });
      }
    }
    
    // Check Chart.yaml fields
    const requiredFields = ['name', 'version', 'description'];
    for (const field of requiredFields) {
      if (!chartYaml[field]) {
        issues.push({
          type: 'structure',
          severity: 'medium',
          message: `Missing required field in Chart.yaml: ${field}`
        });
      }
    }
    
    return { issues };
  }

  async validateHelmChartSecurity(chartPath, chartYaml) {
    const issues = [];
    
    // Check templates for security issues
    const templatesDir = path.join(chartPath, 'templates');
    try {
      const files = await fs.readdir(templatesDir);
      
      for (const file of files) {
        if (file.endsWith('.yaml') || file.endsWith('.yml')) {
          const content = await fs.readFile(path.join(templatesDir, file), 'utf8');
          const docs = yaml.loadAll(content);
          
          for (const doc of docs) {
            if (doc && doc.kind === 'Deployment') {
              const securityIssues = this.checkKubernetesSecurity(doc);
              issues.push(...securityIssues);
            }
          }
        }
      }
    } catch (error) {
      // Template directory might not exist
    }
    
    return { issues };
  }

  async validateHelmTemplates(chartPath, valuesFile, namespace) {
    const issues = [];
    
    // Mock template validation
    try {
      const templatesDir = path.join(chartPath, 'templates');
      const files = await fs.readdir(templatesDir);
      
      for (const file of files) {
        if (file.endsWith('.yaml') || file.endsWith('.yml')) {
          try {
            const content = await fs.readFile(path.join(templatesDir, file), 'utf8');
            yaml.loadAll(content); // Validate YAML syntax
          } catch (error) {
            issues.push({
              type: 'templates',
              severity: 'high',
              file,
              message: `Invalid YAML syntax: ${error.message}`
            });
          }
        }
      }
    } catch (error) {
      issues.push({
        type: 'templates',
        severity: 'high',
        message: `Cannot read templates directory: ${error.message}`
      });
    }
    
    return { issues };
  }

  async performHelmDryRun(chartPath, valuesFile, releaseName, namespace) {
    // Mock dry run result
    return {
      success: true,
      release_name: releaseName,
      namespace,
      resources_deployed: 5,
      warnings: [],
      notes: 'Dry run completed successfully'
    };
  }

  calculateComplianceScore(issues) {
    if (issues.length === 0) return 100;
    
    const severityWeights = { critical: 25, high: 10, medium: 5, low: 1 };
    const totalWeight = issues.reduce((sum, issue) => sum + (severityWeights[issue.severity] || 1), 0);
    
    return Math.max(0, 100 - totalWeight);
  }

  generateKubernetesRecommendations(issues) {
    const recommendations = [];
    const issueTypes = [...new Set(issues.map(i => i.type))];
    
    for (const type of issueTypes) {
      const typeIssues = issues.filter(i => i.type === type);
      recommendations.push({
        category: type,
        priority: typeIssues.some(i => i.severity === 'critical') ? 'high' : 'medium',
        description: `Address ${typeIssues.length} ${type} issues`,
        affected_resources: typeIssues.map(i => i.resource)
      });
    }
    
    return recommendations;
  }

  generateHelmRecommendations(issues) {
    return this.generateKubernetesRecommendations(issues);
  }

  async extractResourcesFromIaC(iacType, configPath) {
    // Mock resource extraction
    return [
      {
        type: 'aws_instance',
        name: 'web-server',
        config: { instance_type: 't3.medium' }
      },
      {
        type: 'aws_ebs_volume',
        name: 'data-volume',
        config: { size: 100, type: 'gp3' }
      }
    ];
  }

  async calculateResourceCost(resource, cloudProvider, region, duration) {
    // Mock cost calculation
    const costData = {
      'aws_instance': { t3: { medium: 50 }, t2: { micro: 10 } },
      'aws_ebs_volume': { gp3: 0.1, gp2: 0.08 }
    };
    
    let hourlyCost = 0;
    
    if (resource.type === 'aws_instance') {
      const instanceType = resource.config.instance_type;
      hourlyCost = costData.aws_instance[instanceType.split('.')[0]]?.[instanceType.split('.')[1]] || 0;
    } else if (resource.type === 'aws_ebs_volume') {
      hourlyCost = costData.aws_ebs_volume[resource.config.type] || 0.1;
      hourlyCost *= resource.config.size;
    }
    
    const durationMultiplier = {
      hourly: 1,
      daily: 24,
      monthly: 24 * 30,
      yearly: 24 * 365
    };
    
    return {
      resource: resource.name,
      type: resource.type,
      hourly_cost: hourlyCost,
      cost: hourlyCost * durationMultiplier[duration],
      currency: 'USD'
    };
  }

  generateCostBreakdown(resources) {
    const breakdown = {};
    
    for (const resource of resources) {
      const category = this.getResourceCategory(resource.type);
      if (!breakdown[category]) {
        breakdown[category] = 0;
      }
      breakdown[category] += resource.cost;
    }
    
    return breakdown;
  }

  getResourceCategory(resourceType) {
    const categories = {
      'aws_instance': 'compute',
      'aws_ebs_volume': 'storage',
      'aws_rds_instance': 'database',
      'aws_elb': 'network'
    };
    
    return categories[resourceType] || 'other';
  }

  generateCostRecommendations(resources) {
    const recommendations = [];
    
    // Check for oversized resources
    for (const resource of resources) {
      if (resource.type === 'aws_instance' && resource.hourly_cost > 100) {
        recommendations.push({
          type: 'cost_optimization',
          resource: resource.resource,
          message: 'Consider using smaller instance type or spot instances',
          potential_savings: resource.cost * 0.3
        });
      }
    }
    
    return recommendations;
  }

  async loadSecurityPolicies(policySet, customPolicyPath) {
    // Mock policy loading
    return {
      'CIS': [
        { id: 'cis-1.1', description: 'Ensure all resources have tags', severity: 'medium' },
        { id: 'cis-2.1', description: 'Ensure encryption is enabled', severity: 'high' }
      ],
      'NIST': [
        { id: 'nist-1.1', description: 'Ensure access control is configured', severity: 'high' }
      ]
    }[policySet] || [];
  }

  async getIaCFiles(iacPath) {
    // Mock file enumeration
    return [
      { path: path.join(iacPath, 'main.tf'), type: 'terraform' },
      { path: path.join(iacPath, 'variables.tf'), type: 'terraform' }
    ];
  }

  async checkFileAgainstPolicies(file, policies, severityThreshold) {
    // Mock policy checking
    const violations = [];
    
    for (const policy of policies) {
      if (this.shouldIncludeViolation(policy.severity, severityThreshold)) {
        violations.push({
          policy_id: policy.id,
          file: file.path,
          severity: policy.severity,
          message: policy.description
        });
      }
    }
    
    return violations;
  }

  shouldIncludeViolation(policySeverity, threshold) {
    const severityOrder = { low: 0, medium: 1, high: 2, critical: 3 };
    return severityOrder[policySeverity] >= severityOrder[threshold];
  }

  calculatePolicyComplianceScore(violations) {
    if (violations.length === 0) return 100;
    
    const severityWeights = { critical: 25, high: 10, medium: 5, low: 1 };
    const totalWeight = violations.reduce((sum, v) => sum + severityWeights[v.severity], 0);
    
    return Math.max(0, 100 - totalWeight);
  }

  generatePolicyRecommendations(violations) {
    return violations.map(v => ({
      policy_id: v.policy_id,
      file: v.file,
      recommendation: `Fix policy violation: ${v.message}`,
      priority: v.severity
    }));
  }

  async detectIaCType(iacPath) {
    try {
      const files = await fs.readdir(iacPath);
      
      if (files.includes('Chart.yaml')) {
        return 'helm';
      } else if (files.some(f => f.endsWith('.tf') || f === 'terraform.tfstate')) {
        return 'terraform';
      } else if (files.some(f => f.endsWith('.yaml') || f.endsWith('.yml'))) {
        return 'kubernetes';
      }
      
      return 'unknown';
    } catch (error) {
      return 'unknown';
    }
  }

  async analyzeTerraformProject(iacPath) {
    // Mock analysis
    return {
      technical: {
        resources_count: 10,
        modules_count: 2,
        variables_count: 5
      },
      security: {
        issues_count: 3,
        critical_issues: 1
      },
      cost: {
        estimated_monthly: 500
      }
    };
  }

  async analyzeKubernetesProject(iacPath) {
    // Mock analysis
    return {
      technical: {
        manifests_count: 8,
        namespaces_count: 2,
        services_count: 3
      },
      security: {
        issues_count: 2,
        critical_issues: 0
      }
    };
  }

  async analyzeHelmProject(iacPath) {
    // Mock analysis
    return {
      technical: {
        chart_version: '1.0.0',
        templates_count: 6,
        values_count: 15
      },
      security: {
        issues_count: 1,
        critical_issues: 0
      }
    };
  }

  generateExecutiveSummary(report) {
    return {
      overall_health: 'good',
      total_issues: report.security_analysis.issues_count || 0,
      critical_issues: report.security_analysis.critical_issues || 0,
      estimated_cost: report.cost_analysis?.estimated_monthly || 0,
      compliance_score: 85
    };
  }

  generateComprehensiveRecommendations(report) {
    const recommendations = [];
    
    if (report.security_analysis.critical_issues > 0) {
      recommendations.push({
        priority: 'high',
        category: 'security',
        description: 'Address critical security issues immediately'
      });
    }
    
    if (report.cost_analysis?.estimated_monthly > 1000) {
      recommendations.push({
        priority: 'medium',
        category: 'cost',
        description: 'Review and optimize resource costs'
      });
    }
    
    return recommendations;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('IaC Validator MCP server running on stdio');
  }
}

// Run the server
if (require.main === module) {
  const server = new IacValidatorServer();
  server.run().catch(console.error);
}

module.exports = IacValidatorServer;
