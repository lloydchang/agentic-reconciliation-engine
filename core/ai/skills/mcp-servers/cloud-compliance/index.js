#!/usr/bin/env node

/**
 * Cloud Compliance Auditor MCP Server
 * 
 * This MCP server provides cloud compliance auditing capabilities:
 * - AWS Security Hub analysis
 * - Azure Policy compliance checks
 * - GCP Security Center assessment
 * - Multi-cloud compliance reporting
 * - Automated remediation suggestions
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require('@modelcontextprotocol/sdk/types.js');

// AWS SDK v3
const { SecurityHubClient, GetFindingsCommand, DescribeFindingsCommand } = require('@aws-sdk/client-securityhub');
const { ResourceGroupsTaggingAPIClient, GetResourcesCommand } = require('@aws-sdk/client-resource-groups-tagging-api');
const { OrganizationsClient, ListAccountsCommand } = require('@aws-sdk/client-organizations');
// Azure SDK
const { ResourceManagementClient } = require('@azure/arm-resources');
const { PolicyInsightsClient } = require('@azure/arm-policyinsights');
// GCP SDK
const { SecurityCenterClient } = require('@google-cloud/security-center');

class CloudComplianceServer {
  constructor() {
    this.server = new Server(
      {
        name: 'cloud-compliance-auditor',
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
          name: 'aws_security_hub_analysis',
          description: 'Analyze AWS Security Hub findings and generate compliance report',
          inputSchema: {
            type: 'object',
            properties: {
              region: {
                type: 'string',
                description: 'AWS region to analyze',
                default: 'us-east-1'
              },
              severity: {
                type: 'string',
                enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
                description: 'Minimum severity level to include'
              },
              compliance_standard: {
                type: 'string',
                enum: ['CIS', 'NIST', 'PCI-DSS', 'HIPAA', 'SOC2'],
                description: 'Compliance standard to check against'
              }
            }
          }
        },
        {
          name: 'azure_policy_compliance',
          description: 'Check Azure Policy compliance status and generate recommendations',
          inputSchema: {
            type: 'object',
            properties: {
              subscription_id: {
                type: 'string',
                description: 'Azure subscription ID'
              },
              resource_group: {
                type: 'string',
                description: 'Resource group to analyze (optional)'
              },
              policy_definition: {
                type: 'string',
                description: 'Specific policy definition to check'
              }
            }
          }
        },
        {
          name: 'gcp_security_assessment',
          description: 'Assess GCP Security Center findings and security posture',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: {
                type: 'string',
                description: 'GCP project ID'
              },
              organization_id: {
                type: 'string',
                description: 'GCP organization ID'
              },
              category: {
                type: 'string',
                enum: ['ALL', 'OPEN_FIREWALL', 'MISCONFIGURED_IAM', 'PUBLIC_STORAGE'],
                description: 'Security finding category to filter'
              }
            }
          }
        },
        {
          name: 'multi_cloud_compliance_report',
          description: 'Generate comprehensive multi-cloud compliance report',
          inputSchema: {
            type: 'object',
            properties: {
              include_aws: {
                type: 'boolean',
                default: true,
                description: 'Include AWS findings'
              },
              include_azure: {
                type: 'boolean',
                default: true,
                description: 'Include Azure findings'
              },
              include_gcp: {
                type: 'boolean',
                default: true,
                description: 'Include GCP findings'
              },
              compliance_framework: {
                type: 'string',
                enum: ['CIS', 'NIST', 'PCI-DSS', 'HIPAA', 'SOC2', 'ALL'],
                default: 'ALL',
                description: 'Compliance framework to map findings against'
              },
              output_format: {
                type: 'string',
                enum: ['JSON', 'PDF', 'HTML'],
                default: 'JSON',
                description: 'Report output format'
              }
            }
          }
        },
        {
          name: 'automated_remediation_suggestions',
          description: 'Generate automated remediation suggestions for compliance violations',
          inputSchema: {
            type: 'object',
            properties: {
              finding_id: {
                type: 'string',
                description: 'Specific finding ID to remediate'
              },
              auto_apply: {
                type: 'boolean',
                default: false,
                description: 'Whether to auto-apply remediation (requires permissions)'
              },
              dry_run: {
                type: 'boolean',
                default: true,
                description: 'Generate suggestions without applying changes'
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
          case 'aws_security_hub_analysis':
            return await this.awsSecurityHubAnalysis(args);
          case 'azure_policy_compliance':
            return await this.azurePolicyCompliance(args);
          case 'gcp_security_assessment':
            return await this.gcpSecurityAssessment(args);
          case 'multi_cloud_compliance_report':
            return await this.multiCloudComplianceReport(args);
          case 'automated_remediation_suggestions':
            return await this.automatedRemediationSuggestions(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error in ${name}:`, error);
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error.message}`);
      }
    });
  }

  async awsSecurityHubAnalysis(args) {
    const { region = 'us-east-1', severity, compliance_standard } = args;
    
    // Initialize AWS Security Hub client v3
    const securityHub = new SecurityHubClient({ region });
    
    try {
      // Build filters for findings
      const filters = {};
      
      if (severity) {
        filters.SeverityLabel = [{ Comparison: 'EQUALS', Value: severity }];
      }
      
      if (compliance_standard) {
        filters.ComplianceStandards = [{ Comparison: 'EQUALS', Value: compliance_standard }];
      }
      
      // Get findings
      const findingsCommand = new GetFindingsCommand({
        Filters: filters,
        MaxResults: 100
      });
      
      const findings = await securityHub.send(findingsCommand);
      
      // Process findings
      const processedFindings = findings.Findings.map(finding => ({
        id: finding.Id,
        title: finding.Title,
        severity: finding.Severity?.Label,
        description: finding.Description,
        resource: finding.Resources?.[0]?.Id,
        compliance: finding.Compliance?.Status,
        remediation: finding.Remediation?.Recommendation?.Text,
        firstObserved: finding.FirstObservedAt?.toISOString(),
        lastObserved: finding.LastObservedAt?.toISOString()
      }));
      
      // Generate compliance summary
      const summary = {
        total_findings: findings.Findings.length,
        severity_breakdown: this.groupBySeverity(processedFindings),
        compliance_status: this.groupByCompliance(processedFindings),
        recommendations: this.generateRecommendations(processedFindings)
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'aws_security_hub_analysis',
              region,
              timestamp: new Date().toISOString(),
              summary,
              findings: processedFindings
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`AWS Security Hub analysis failed: ${error.message}`);
    }
  }

  async azurePolicyCompliance(args) {
    const { subscription_id, resource_group, policy_definition } = args;
    
    try {
      // Initialize Azure clients
      const policyClient = new PolicyInsightsClient(subscription_id);
      
      // Get policy states
      const policyStates = await policyClient.policyStates.listQueryResultsForSubscription(
        'latest',
        subscription_id,
        {
          filter: resource_group ? `ResourceId eq '*${resource_group}*'` : undefined,
          filter: policy_definition ? `PolicyDefinitionId eq '*${policy_definition}*'` : undefined
        }
      );
      
      // Process compliance data
      const complianceData = [];
      
      for await (const state of policyStates) {
        complianceData.push({
          policyDefinitionId: state.policyDefinitionId,
          resourceId: state.resourceId,
          complianceState: state.complianceState,
          timestamp: state.timestamp,
          policyDefinitionName: state.policyDefinitionName,
          policyDefinitionCategory: state.policyDefinitionCategory
        });
      }
      
      // Generate compliance summary
      const summary = {
        total_resources: complianceData.length,
        compliant_resources: complianceData.filter(d => d.complianceState === 'Compliant').length,
        non_compliant_resources: complianceData.filter(d => d.complianceState === 'NonCompliant').length,
        policy_categories: this.groupByPolicyCategory(complianceData)
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'azure_policy_compliance',
              subscription_id,
              resource_group,
              timestamp: new Date().toISOString(),
              summary,
              compliance_data: complianceData
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Azure Policy compliance check failed: ${error.message}`);
    }
  }

  async gcpSecurityAssessment(args) {
    const { project_id, organization_id, category = 'ALL' } = args;
    
    try {
      // Initialize GCP Security Center client
      const client = new SecurityCenterClient();
      
      // Get security findings
      const parent = organization_id ? `organizations/${organization_id}` : `projects/${project_id}`;
      
      const [findings] = await client.listFindings({
        parent,
        filter: category !== 'ALL' ? `category="${category}"` : undefined
      });
      
      // Process findings
      const processedFindings = findings.map(finding => ({
        name: finding.name,
        category: finding.category,
        severity: finding.severity,
        state: finding.state,
        resourceName: finding.resourceName,
        findingClass: finding.findingClass,
        eventTime: finding.eventTime,
        externalUri: finding.externalUri
      }));
      
      // Generate security summary
      const summary = {
        total_findings: processedFindings.length,
        category_breakdown: this.groupByCategory(processedFindings),
        severity_breakdown: this.groupBySeverity(processedFindings),
        state_breakdown: this.groupByState(processedFindings)
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'gcp_security_assessment',
              project_id,
              organization_id,
              category,
              timestamp: new Date().toISOString(),
              summary,
              findings: processedFindings
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`GCP Security Center assessment failed: ${error.message}`);
    }
  }

  async multiCloudComplianceReport(args) {
    const { include_aws = true, include_azure = true, include_gcp = true, compliance_framework = 'ALL', output_format = 'JSON' } = args;
    
    try {
      const report_data = {
        report_metadata: {
          generated_at: new Date().toISOString(),
          compliance_framework,
          output_format,
          included_clouds: {
            aws: include_aws,
            azure: include_azure,
            gcp: include_gcp
          }
        },
        findings: {},
        summary: {}
      };
      
      // Collect data from each cloud provider
      if (include_aws) {
        report_data.findings.aws = await this.collectAwsFindings();
      }
      
      if (include_azure) {
        report_data.findings.azure = await this.collectAzureFindings();
      }
      
      if (include_gcp) {
        report_data.findings.gcp = await this.collectGcpFindings();
      }
      
      // Generate comprehensive summary
      report_data.summary = this.generateMultiCloudSummary(report_data.findings, compliance_framework);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(report_data, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Multi-cloud compliance report generation failed: ${error.message}`);
    }
  }

  async automatedRemediationSuggestions(args) {
    const { finding_id, auto_apply = false, dry_run = true } = args;
    
    try {
      // Get finding details (this would be implemented based on the specific cloud provider)
      const finding = await this.getFindingDetails(finding_id);
      
      if (!finding) {
        throw new Error(`Finding not found: ${finding_id}`);
      }
      
      // Generate remediation suggestions
      const suggestions = this.generateRemediationForFinding(finding);
      
      const remediation_plan = {
        finding_id,
        finding_type: finding.type,
        cloud_provider: finding.cloud_provider,
        remediation_steps: suggestions.steps,
        estimated_time: suggestions.estimated_time,
        risk_level: suggestions.risk_level,
        prerequisites: suggestions.prerequisites,
        rollback_plan: suggestions.rollback_plan
      };
      
      // Apply remediation if requested and not dry run
      if (auto_apply && !dry_run) {
        const result = await this.applyRemediation(remediation_plan);
        remediation_plan.applied = true;
        remediation_plan.application_result = result;
      } else {
        remediation_plan.applied = false;
        remediation_plan.dry_run = true;
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'automated_remediation_suggestions',
              timestamp: new Date().toISOString(),
              remediation_plan
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Remediation suggestions failed: ${error.message}`);
    }
  }

  // Helper methods
  groupBySeverity(findings) {
    return findings.reduce((acc, finding) => {
      acc[finding.severity] = (acc[finding.severity] || 0) + 1;
      return acc;
    }, {});
  }

  groupByCompliance(findings) {
    return findings.reduce((acc, finding) => {
      const status = finding.compliance || 'Unknown';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});
  }

  groupByCategory(findings) {
    return findings.reduce((acc, finding) => {
      acc[finding.category] = (acc[finding.category] || 0) + 1;
      return acc;
    }, {});
  }

  groupByState(findings) {
    return findings.reduce((acc, finding) => {
      acc[finding.state] = (acc[finding.state] || 0) + 1;
      return acc;
    }, {});
  }

  groupByPolicyCategory(complianceData) {
    return complianceData.reduce((acc, data) => {
      const category = data.policyDefinitionCategory || 'Uncategorized';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});
  }

  generateRecommendations(findings) {
    const recommendations = [];
    
    findings.forEach(finding => {
      if (finding.remediation) {
        recommendations.push({
          finding_id: finding.id,
          recommendation: finding.remediation,
          priority: this.mapSeverityToPriority(finding.severity)
        });
      }
    });
    
    return recommendations.sort((a, b) => this.priorityOrder(a.priority) - this.priorityOrder(b.priority));
  }

  mapSeverityToPriority(severity) {
    const mapping = {
      'CRITICAL': 'P0',
      'HIGH': 'P1',
      'MEDIUM': 'P2',
      'LOW': 'P3'
    };
    return mapping[severity] || 'P3';
  }

  priorityOrder(priority) {
    const order = { 'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3 };
    return order[priority] || 999;
  }

  async collectAwsFindings() {
    // Implementation for collecting AWS findings
    return { provider: 'aws', findings: [], summary: {} };
  }

  async collectAzureFindings() {
    // Implementation for collecting Azure findings
    return { provider: 'azure', findings: [], summary: {} };
  }

  async collectGcpFindings() {
    // Implementation for collecting GCP findings
    return { provider: 'gcp', findings: [], summary: {} };
  }

  generateMultiCloudSummary(findings, framework) {
    // Implementation for generating multi-cloud summary
    return {
      total_findings: 0,
      compliance_score: 0,
      recommendations: []
    };
  }

  async getFindingDetails(findingId) {
    // Implementation for retrieving finding details
    return null;
  }

  generateRemediationForFinding(finding) {
    // Implementation for generating remediation suggestions
    return {
      steps: [],
      estimated_time: '0 minutes',
      risk_level: 'LOW',
      prerequisites: [],
      rollback_plan: []
    };
  }

  async applyRemediation(plan) {
    // Implementation for applying remediation
    return { success: false, message: 'Not implemented' };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Cloud Compliance MCP server running on stdio');
  }
}

// Run the server
if (require.main === module) {
  const server = new CloudComplianceServer();
  server.run().catch(console.error);
}

module.exports = CloudComplianceServer;
