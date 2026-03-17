#!/usr/bin/env node

/**
 * Incident Triage Automator MCP Server
 * 
 * This MCP server provides automated incident triage capabilities:
 * - Alert aggregation and correlation
 * - Severity assessment and prioritization
 * - Automated incident creation
 * - Stakeholder notification
 * - Runbook recommendation
 * - Incident status tracking
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require('@modelcontextprotocol/sdk/types.js');

// External integrations
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

class IncidentTriageServer {
  constructor() {
    this.server = new Server(
      {
        name: 'incident-triage-automator',
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
          name: 'aggregate_alerts',
          description: 'Aggregate and correlate alerts from multiple monitoring systems',
          inputSchema: {
            type: 'object',
            properties: {
              time_window: {
                type: 'string',
                description: 'Time window for alert aggregation (e.g., "5m", "1h", "24h")',
                default: '1h'
              },
              alert_sources: {
                type: 'array',
                items: { type: 'string' },
                description: 'Alert sources to include (prometheus, datadog, pagerduty, etc.)',
                default: ['prometheus', 'datadog', 'pagerduty']
              },
              correlation_threshold: {
                type: 'number',
                description: 'Correlation threshold (0.0-1.0)',
                default: 0.7
              },
              severity_filter: {
                type: 'string',
                enum: ['critical', 'warning', 'info', 'all'],
                description: 'Filter alerts by severity',
                default: 'all'
              }
            }
          }
        },
        {
          name: 'assess_incident_severity',
          description: 'Assess incident severity based on impact and urgency',
          inputSchema: {
            type: 'object',
            properties: {
              incident_data: {
                type: 'object',
                description: 'Incident data including affected services, user impact, etc.',
                properties: {
                  title: { type: 'string' },
                  description: { type: 'string' },
                  affected_services: { type: 'array', items: { type: 'string' } },
                  user_impact: { type: 'string', enum: ['none', 'minor', 'major', 'critical'] },
                  business_impact: { type: 'string', enum: ['none', 'minor', 'major', 'critical'] },
                  affected_users: { type: 'number' },
                  duration: { type: 'string' }
                }
              },
              auto_create_incident: {
                type: 'boolean',
                default: false,
                description: 'Automatically create incident in incident management system'
              }
            }
          }
        },
        {
          name: 'create_incident',
          description: 'Create incident in incident management system',
          inputSchema: {
            type: 'object',
            properties: {
              title: {
                type: 'string',
                description: 'Incident title'
              },
              description: {
                type: 'string',
                description: 'Detailed incident description'
              },
              severity: {
                type: 'string',
                enum: ['P0', 'P1', 'P2', 'P3', 'P4'],
                description: 'Incident severity'
              },
              incident_type: {
                type: 'string',
                enum: ['outage', 'degradation', 'security', 'maintenance', 'other'],
                description: 'Type of incident'
              },
              affected_services: {
                type: 'array',
                items: { type: 'string' },
                description: 'List of affected services'
              },
              assignee: {
                type: 'string',
                description: 'Incident assignee (optional)'
              },
              tags: {
                type: 'array',
                items: { type: 'string' },
                description: 'Incident tags'
              }
            }
          }
        },
        {
          name: 'notify_stakeholders',
          description: 'Notify relevant stakeholders about incident',
          inputSchema: {
            type: 'object',
            properties: {
              incident_id: {
                type: 'string',
                description: 'Incident ID'
              },
              notification_channels: {
                type: 'array',
                items: { type: 'string' },
                enum: ['slack', 'email', 'teams', 'pagerduty'],
                description: 'Notification channels to use',
                default: ['slack', 'email']
              },
              escalation_level: {
                type: 'string',
                enum: ['team', 'manager', 'director', 'executive'],
                description: 'Escalation level',
                default: 'team'
              },
              message_template: {
                type: 'string',
                description: 'Custom message template (optional)'
              }
            }
          }
        },
        {
          name: 'recommend_runbook',
          description: 'Recommend relevant runbooks for incident resolution',
          inputSchema: {
            type: 'object',
            properties: {
              incident_type: {
                type: 'string',
                description: 'Type of incident'
              },
              affected_services: {
                type: 'array',
                items: { type: 'string' },
                description: 'Affected services'
              },
              symptoms: {
                type: 'array',
                items: { type: 'string' },
                description: 'Observed symptoms'
              },
              error_patterns: {
                type: 'array',
                items: { type: 'string' },
                description: 'Error patterns from logs/metrics'
              }
            }
          }
        },
        {
          name: 'track_incident_status',
          description: 'Track and update incident status and resolution progress',
          inputSchema: {
            type: 'object',
            properties: {
              incident_id: {
                type: 'string',
                description: 'Incident ID'
              },
              status_update: {
                type: 'string',
                enum: ['investigating', 'identified', 'monitoring', 'resolved', 'closed'],
                description: 'New incident status'
              },
              resolution_notes: {
                type: 'string',
                description: 'Resolution notes and post-mortem details'
              },
              root_cause: {
                type: 'string',
                description: 'Identified root cause'
              },
              follow_up_actions: {
                type: 'array',
                items: { type: 'string' },
                description: 'Follow-up actions to prevent recurrence'
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
          case 'aggregate_alerts':
            return await this.aggregateAlerts(args);
          case 'assess_incident_severity':
            return await this.assessIncidentSeverity(args);
          case 'create_incident':
            return await this.createIncident(args);
          case 'notify_stakeholders':
            return await this.notifyStakeholders(args);
          case 'recommend_runbook':
            return await this.recommendRunbook(args);
          case 'track_incident_status':
            return await this.trackIncidentStatus(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error in ${name}:`, error);
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error.message}`);
      }
    });
  }

  async aggregateAlerts(args) {
    const { time_window = '1h', alert_sources = ['prometheus', 'datadog', 'pagerduty'], correlation_threshold = 0.7, severity_filter = 'all' } = args;
    
    try {
      // Fetch alerts from different sources
      const alerts = await this.fetchAlertsFromSources(alert_sources, time_window, severity_filter);
      
      // Correlate alerts
      const correlatedGroups = this.correlateAlerts(alerts, correlation_threshold);
      
      // Generate aggregation summary
      const summary = {
        total_alerts: alerts.length,
        correlated_groups: correlatedGroups.length,
        time_window,
        sources: alert_sources,
        severity_distribution: this.calculateSeverityDistribution(alerts),
        top_services: this.getTopAffectedServices(alerts)
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'alert_aggregation',
              timestamp: new Date().toISOString(),
              summary,
              correlated_groups,
              raw_alerts: alerts
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Alert aggregation failed: ${error.message}`);
    }
  }

  async assessIncidentSeverity(args) {
    const { incident_data, auto_create_incident = false } = args;
    
    try {
      // Calculate severity score
      const severityScore = this.calculateSeverityScore(incident_data);
      
      // Determine severity level
      const severity = this.mapScoreToSeverity(severityScore);
      
      // Generate severity assessment
      const assessment = {
        incident_data,
        severity_score: severityScore,
        severity_level: severity,
        assessment_factors: this.getAssessmentFactors(incident_data),
        recommended_actions: this.getRecommendedActions(severity),
        estimated_resolution_time: this.estimateResolutionTime(severity)
      };
      
      // Auto-create incident if requested
      let incident_id = null;
      if (auto_create_incident) {
        const incident = await this.createIncident({
          title: incident_data.title,
          description: incident_data.description,
          severity,
          incident_type: this.inferIncidentType(incident_data),
          affected_services: incident_data.affected_services
        });
        incident_id = incident.incident_id;
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'severity_assessment',
              timestamp: new Date().toISOString(),
              assessment,
              auto_created_incident: incident_id
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Severity assessment failed: ${error.message}`);
    }
  }

  async createIncident(args) {
    const { title, description, severity, incident_type, affected_services, assignee, tags = [] } = args;
    
    try {
      const incident_id = uuidv4();
      
      const incident = {
        id: incident_id,
        title,
        description,
        severity,
        incident_type,
        affected_services: affected_services || [],
        assignee,
        tags,
        status: 'investigating',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        timeline: [
          {
            timestamp: new Date().toISOString(),
            action: 'incident_created',
            details: `Incident ${incident_id} created with severity ${severity}`
          }
        ]
      };
      
      // Store incident (in a real implementation, this would save to a database)
      await this.storeIncident(incident);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'incident_created',
              timestamp: new Date().toISOString(),
              incident
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Incident creation failed: ${error.message}`);
    }
  }

  async notifyStakeholders(args) {
    const { incident_id, notification_channels = ['slack', 'email'], escalation_level = 'team', message_template } = args;
    
    try {
      // Get incident details
      const incident = await this.getIncident(incident_id);
      
      if (!incident) {
        throw new Error(`Incident not found: ${incident_id}`);
      }
      
      // Get stakeholders based on escalation level
      const stakeholders = await this.getStakeholders(incident, escalation_level);
      
      // Generate notification message
      const message = message_template || this.generateNotificationMessage(incident, escalation_level);
      
      // Send notifications through specified channels
      const notification_results = [];
      
      for (const channel of notification_channels) {
        try {
          const result = await this.sendNotification(channel, stakeholders, message, incident);
          notification_results.push({
            channel,
            success: true,
            result
          });
        } catch (error) {
          notification_results.push({
            channel,
            success: false,
            error: error.message
          });
        }
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'stakeholder_notification',
              timestamp: new Date().toISOString(),
              incident_id,
              escalation_level,
              stakeholders_notified: stakeholders.length,
              channels: notification_channels,
              results: notification_results
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Stakeholder notification failed: ${error.message}`);
    }
  }

  async recommendRunbook(args) {
    const { incident_type, affected_services, symptoms, error_patterns } = args;
    
    try {
      // Search for relevant runbooks
      const runbooks = await this.searchRunbooks({
        incident_type,
        affected_services,
        symptoms,
        error_patterns
      });
      
      // Rank runbooks by relevance
      const ranked_runbooks = this.rankRunbooks(runbooks, {
        incident_type,
        affected_services,
        symptoms,
        error_patterns
      });
      
      // Generate recommendations
      const recommendations = ranked_runbooks.map((runbook, index) => ({
        rank: index + 1,
        title: runbook.title,
        description: runbook.description,
        relevance_score: runbook.relevance_score,
        steps: runbook.steps,
        estimated_time: runbook.estimated_time,
        required_tools: runbook.required_tools,
        success_rate: runbook.success_rate
      }));
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'runbook_recommendations',
              timestamp: new Date().toISOString(),
              query: {
                incident_type,
                affected_services,
                symptoms,
                error_patterns
              },
              recommendations
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Runbook recommendation failed: ${error.message}`);
    }
  }

  async trackIncidentStatus(args) {
    const { incident_id, status_update, resolution_notes, root_cause, follow_up_actions } = args;
    
    try {
      // Get existing incident
      const incident = await this.getIncident(incident_id);
      
      if (!incident) {
        throw new Error(`Incident not found: ${incident_id}`);
      }
      
      // Update incident status
      const previous_status = incident.status;
      incident.status = status_update;
      incident.updated_at = new Date().toISOString();
      
      // Add timeline entry
      incident.timeline.push({
        timestamp: new Date().toISOString(),
        action: 'status_updated',
        details: `Status changed from ${previous_status} to ${status_update}`
      });
      
      // Add resolution details if provided
      if (resolution_notes) {
        incident.resolution_notes = resolution_notes;
        incident.timeline.push({
          timestamp: new Date().toISOString(),
          action: 'resolution_added',
          details: 'Resolution notes added'
        });
      }
      
      if (root_cause) {
        incident.root_cause = root_cause;
        incident.timeline.push({
          timestamp: new Date().toISOString(),
          action: 'root_cause_identified',
          details: 'Root cause identified'
        });
      }
      
      if (follow_up_actions) {
        incident.follow_up_actions = follow_up_actions;
        incident.timeline.push({
          timestamp: new Date().toISOString(),
          action: 'follow_up_actions_added',
          details: `${follow_up_actions.length} follow-up actions added`
        });
      }
      
      // Store updated incident
      await this.storeIncident(incident);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'incident_status_updated',
              timestamp: new Date().toISOString(),
              incident_id,
              previous_status,
              current_status: status_update,
              incident
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Incident status tracking failed: ${error.message}`);
    }
  }

  // Helper methods
  async fetchAlertsFromSources(sources, timeWindow, severityFilter) {
    const alerts = [];
    
    for (const source of sources) {
      try {
        const sourceAlerts = await this.fetchFromSource(source, timeWindow, severityFilter);
        alerts.push(...sourceAlerts);
      } catch (error) {
        console.error(`Failed to fetch alerts from ${source}:`, error);
      }
    }
    
    return alerts;
  }

  async fetchFromSource(source, timeWindow, severityFilter) {
    // Mock implementation - in reality, this would integrate with actual monitoring systems
    switch (source) {
      case 'prometheus':
        return this.fetchPrometheusAlerts(timeWindow, severityFilter);
      case 'datadog':
        return this.fetchDatadogAlerts(timeWindow, severityFilter);
      case 'pagerduty':
        return this.fetchPagerDutyAlerts(timeWindow, severityFilter);
      default:
        return [];
    }
  }

  fetchPrometheusAlerts(timeWindow, severityFilter) {
    // Mock implementation
    return [
      {
        id: 'prom-001',
        source: 'prometheus',
        title: 'High CPU Usage',
        severity: 'warning',
        service: 'web-api',
        timestamp: new Date().toISOString(),
        description: 'CPU usage exceeded 80%'
      }
    ];
  }

  fetchDatadogAlerts(timeWindow, severityFilter) {
    // Mock implementation
    return [
      {
        id: 'dd-001',
        source: 'datadog',
        title: 'Memory Pressure',
        severity: 'critical',
        service: 'database',
        timestamp: new Date().toISOString(),
        description: 'Memory usage at 95%'
      }
    ];
  }

  fetchPagerDutyAlerts(timeWindow, severityFilter) {
    // Mock implementation
    return [
      {
        id: 'pd-001',
        source: 'pagerduty',
        title: 'Service Down',
        severity: 'critical',
        service: 'auth-service',
        timestamp: new Date().toISOString(),
        description: 'Authentication service is not responding'
      }
    ];
  }

  correlateAlerts(alerts, threshold) {
    // Simple correlation based on service and time proximity
    const groups = [];
    const serviceGroups = {};
    
    // Group by service
    alerts.forEach(alert => {
      const service = alert.service || 'unknown';
      if (!serviceGroups[service]) {
        serviceGroups[service] = [];
      }
      serviceGroups[service].push(alert);
    });
    
    // Create correlation groups
    Object.keys(serviceGroups).forEach(service => {
      if (serviceGroups[service].length > 1) {
        groups.push({
          id: `group-${service}`,
          correlation_score: 0.8,
          service,
          alerts: serviceGroups[service],
          correlation_reason: 'Same service affected'
        });
      }
    });
    
    return groups;
  }

  calculateSeverityDistribution(alerts) {
    const distribution = alerts.reduce((acc, alert) => {
      acc[alert.severity] = (acc[alert.severity] || 0) + 1;
      return acc;
    }, {});
    
    return distribution;
  }

  getTopAffectedServices(alerts) {
    const serviceCounts = alerts.reduce((acc, alert) => {
      const service = alert.service || 'unknown';
      acc[service] = (acc[service] || 0) + 1;
      return acc;
    }, {});
    
    return Object.entries(serviceCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([service, count]) => ({ service, count }));
  }

  calculateSeverityScore(incidentData) {
    let score = 0;
    
    // User impact scoring
    const userImpactScores = { none: 0, minor: 25, major: 50, critical: 100 };
    score += userImpactScores[incidentData.user_impact] || 0;
    
    // Business impact scoring
    const businessImpactScores = { none: 0, minor: 25, major: 50, critical: 100 };
    score += businessImpactScores[incidentData.business_impact] || 0;
    
    // Affected users scoring
    if (incidentData.affected_users) {
      if (incidentData.affected_users > 10000) score += 50;
      else if (incidentData.affected_users > 1000) score += 30;
      else if (incidentData.affected_users > 100) score += 15;
      else if (incidentData.affected_users > 10) score += 5;
    }
    
    // Affected services scoring
    if (incidentData.affected_services) {
      score += incidentData.affected_services.length * 10;
    }
    
    return Math.min(score, 100);
  }

  mapScoreToSeverity(score) {
    if (score >= 80) return 'P0';
    if (score >= 60) return 'P1';
    if (score >= 40) return 'P2';
    if (score >= 20) return 'P3';
    return 'P4';
  }

  getAssessmentFactors(incidentData) {
    const factors = [];
    
    if (incidentData.user_impact !== 'none') {
      factors.push(`User impact: ${incidentData.user_impact}`);
    }
    
    if (incidentData.business_impact !== 'none') {
      factors.push(`Business impact: ${incidentData.business_impact}`);
    }
    
    if (incidentData.affected_users) {
      factors.push(`${incidentData.affected_users} users affected`);
    }
    
    if (incidentData.affected_services && incidentData.affected_services.length > 0) {
      factors.push(`${incidentData.affected_services.length} services affected`);
    }
    
    return factors;
  }

  getRecommendedActions(severity) {
    const actions = {
      'P0': ['Immediate escalation to executives', 'War room activation', 'Customer communication'],
      'P1': ['Manager notification', 'Team lead assignment', 'Status page updates'],
      'P2': ['Team notification', 'Documentation update', 'Monitoring enhancement'],
      'P3': ['Team awareness', 'Post-mortem scheduling'],
      'P4': ['Documentation', 'Trend monitoring']
    };
    
    return actions[severity] || [];
  }

  estimateResolutionTime(severity) {
    const estimates = {
      'P0': '1-4 hours',
      'P1': '4-8 hours',
      'P2': '8-24 hours',
      'P3': '1-3 days',
      'P4': '3-7 days'
    };
    
    return estimates[severity] || 'Unknown';
  }

  inferIncidentType(incidentData) {
    if (incidentData.title && incidentData.title.toLowerCase().includes('security')) {
      return 'security';
    }
    if (incidentData.user_impact === 'critical' || incidentData.business_impact === 'critical') {
      return 'outage';
    }
    return 'degradation';
  }

  async storeIncident(incident) {
    // Mock implementation - in reality, this would save to a database
    console.log('Storing incident:', incident.id);
  }

  async getIncident(incidentId) {
    // Mock implementation - in reality, this would fetch from a database
    return {
      id: incidentId,
      title: 'Sample Incident',
      description: 'This is a sample incident',
      severity: 'P1',
      status: 'investigating'
    };
  }

  async getStakeholders(incident, escalationLevel) {
    // Mock implementation - in reality, this would query an on-call system
    const stakeholders = {
      team: ['team-lead@example.com', 'engineer1@example.com'],
      manager: ['manager@example.com'],
      director: ['director@example.com'],
      executive: ['cto@example.com', 'ceo@example.com']
    };
    
    return stakeholders[escalationLevel] || [];
  }

  generateNotificationMessage(incident, escalationLevel) {
    return `
🚨 Incident Alert - ${incident.severity.toUpperCase()} 🚨

Title: ${incident.title}
Description: ${incident.description}
Status: ${incident.status}
Affected Services: ${incident.affected_services.join(', ')}

Escalation Level: ${escalationLevel}

Please investigate and take appropriate action.
    `.trim();
  }

  async sendNotification(channel, stakeholders, message, incident) {
    // Mock implementation - in reality, this would integrate with actual notification systems
    console.log(`Sending ${channel} notification to ${stakeholders.length} stakeholders`);
    return { sent: true, recipients: stakeholders.length };
  }

  async searchRunbooks(query) {
    // Mock implementation - in reality, this would search a knowledge base
    return [
      {
        title: 'Database Performance Issues',
        description: 'Runbook for troubleshooting database performance problems',
        relevance_score: 0.9,
        steps: ['Check database connections', 'Analyze slow queries', 'Review resource usage'],
        estimated_time: '30 minutes',
        required_tools: ['database-admin', 'monitoring-dashboard'],
        success_rate: 0.85
      },
      {
        title: 'Service Outage Recovery',
        description: 'Steps to recover from service outage',
        relevance_score: 0.8,
        steps: ['Check service health', 'Restart services', 'Verify connectivity'],
        estimated_time: '15 minutes',
        required_tools: ['service-dashboard', 'log-analyzer'],
        success_rate: 0.95
      }
    ];
  }

  rankRunbooks(runbooks, query) {
    // Simple ranking based on relevance score
    return runbooks.sort((a, b) => b.relevance_score - a.relevance_score);
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Incident Triage MCP server running on stdio');
  }
}

// Run the server
if (require.main === module) {
  const server = new IncidentTriageServer();
  server.run().catch(console.error);
}

module.exports = IncidentTriageServer;
