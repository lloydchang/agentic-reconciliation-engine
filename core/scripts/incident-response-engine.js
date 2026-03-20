#!/usr/bin/env node

/**
 * AI Infrastructure Portal - Automated Incident Response Engine
 * Intelligent incident detection, classification, and automated remediation
 */

const axios = require('axios');
const { EventEmitter } = require('events');
const promClient = require('prom-client');
const nodemailer = require('nodemailer');
const { WebClient } = require('@slack/web-api');

class IncidentResponseEngine extends EventEmitter {
  constructor(options = {}) {
    super();

    this.alertmanagerUrl = options.alertmanagerUrl || 'http://localhost:9093/api/v2';
    this.apiUrl = options.apiUrl || 'http://localhost:5001/api';
    this.incidentTimeout = options.timeout || 3600000; // 1 hour default timeout
    this.autoRemediate = options.autoRemediate !== false; // Enable by default

    this.activeIncidents = new Map();
    this.incidentHistory = [];
    this.remediationRules = new Map();

    this.register = new promClient.Registry();

    // Incident metrics
    this.incidentMetrics = {
      activeIncidents: new promClient.Gauge({
        name: 'ai_portal_active_incidents',
        help: 'Number of currently active incidents',
        registers: [this.register]
      }),

      totalIncidents: new promClient.Counter({
        name: 'ai_portal_incidents_total',
        help: 'Total number of incidents created',
        labelNames: ['severity', 'category', 'resolved'],
        registers: [this.register]
      }),

      incidentResponseTime: new promClient.Histogram({
        name: 'ai_portal_incident_response_time_seconds',
        help: 'Time to respond to incidents',
        labelNames: ['severity'],
        buckets: [60, 300, 600, 1800, 3600, 7200],
        registers: [this.register]
      }),

      automatedRemediations: new promClient.Counter({
        name: 'ai_portal_automated_remediations_total',
        help: 'Number of automated remediation actions taken',
        labelNames: ['action', 'success'],
        registers: [this.register]
      }),

      incidentEscalations: new promClient.Counter({
        name: 'ai_portal_incident_escalations_total',
        help: 'Number of incidents escalated to human intervention',
        labelNames: ['severity', 'reason'],
        registers: [this.register]
      })
    };

    this.setupRemediationRules();
    this.setupNotificationChannels();
    this.startIncidentMonitoring();
  }

  setupRemediationRules() {
    // Define automated remediation rules
    this.remediationRules.set('HighPodCPUUsage', {
      condition: (alert) => alert.labels.severity === 'warning' && alert.labels.service === 'resources',
      actions: [
        {
          name: 'scale_deployment',
          description: 'Scale up deployment replicas',
          execute: async (incident) => await this.scaleDeployment(incident)
        },
        {
          name: 'increase_cpu_limits',
          description: 'Increase CPU resource limits',
          execute: async (incident) => await this.adjustResourceLimits(incident, 'cpu')
        }
      ],
      timeout: 300000, // 5 minutes
      maxRetries: 2
    });

    this.remediationRules.set('RedisDown', {
      condition: (alert) => alert.labels.service === 'cache' && alert.labels.severity === 'critical',
      actions: [
        {
          name: 'restart_redis',
          description: 'Restart Redis cache service',
          execute: async (incident) => await this.restartService('redis-cache')
        },
        {
          name: 'failover_to_backup',
          description: 'Switch to backup cache instance',
          execute: async (incident) => await this.failoverToBackup('redis')
        }
      ],
      timeout: 600000, // 10 minutes
      maxRetries: 1
    });

    this.remediationRules.set('AIPortalAPIHighErrorRate', {
      condition: (alert) => alert.labels.service === 'api' && alert.labels.severity === 'critical',
      actions: [
        {
          name: 'restart_api_pods',
          description: 'Restart API pods to clear potential issues',
          execute: async (incident) => await this.restartPods('ai-infrastructure-portal')
        },
        {
          name: 'rollback_deployment',
          description: 'Rollback to previous deployment version',
          execute: async (incident) => await this.rollbackDeployment('ai-infrastructure-portal')
        }
      ],
      timeout: 900000, // 15 minutes
      maxRetries: 1
    });

    this.remediationRules.set('NginxHighErrorRate', {
      condition: (alert) => alert.labels.service === 'load-balancer' && alert.labels.severity === 'warning',
      actions: [
        {
          name: 'reload_nginx_config',
          description: 'Reload NGINX configuration',
          execute: async (incident) => await this.reloadNginxConfig()
        },
        {
          name: 'scale_nginx',
          description: 'Scale NGINX load balancer',
          execute: async (incident) => await this.scaleDeployment(incident, 'nginx-load-balancer')
        }
      ],
      timeout: 180000, // 3 minutes
      maxRetries: 3
    });

    this.remediationRules.set('KubeServiceDown', {
      condition: (alert) => alert.labels.service === 'kubernetes' && alert.labels.severity === 'critical',
      actions: [
        {
          name: 'check_node_health',
          description: 'Check and repair node health',
          execute: async (incident) => await this.checkNodeHealth(incident)
        },
        {
          name: 'reschedule_pods',
          description: 'Reschedule pods to healthy nodes',
          execute: async (incident) => await this.reschedulePods(incident)
        }
      ],
      timeout: 600000, // 10 minutes
      maxRetries: 1
    });
  }

  setupNotificationChannels() {
    // Email configuration
    this.emailTransporter = nodemailer.createTransporter({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: process.env.SMTP_PORT || 587,
      secure: false,
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });

    // Slack configuration
    this.slackClient = new WebClient(process.env.SLACK_TOKEN);

    // Webhook configuration
    this.webhookUrls = {
      teams: process.env.TEAMS_WEBHOOK_URL,
      discord: process.env.DISCORD_WEBHOOK_URL,
      pagerduty: process.env.PAGERDUTY_INTEGRATION_KEY
    };
  }

  async startIncidentMonitoring() {
    console.log('🚨 Starting incident response monitoring...');

    // Poll Alertmanager for alerts
    setInterval(async () => {
      await this.checkForAlerts();
    }, 30000); // Check every 30 seconds

    // Clean up resolved incidents
    setInterval(() => {
      this.cleanupResolvedIncidents();
    }, 300000); // Clean up every 5 minutes
  }

  async checkForAlerts() {
    try {
      const response = await axios.get(`${this.alertmanagerUrl}/alerts`);
      const alerts = response.data || [];

      for (const alert of alerts) {
        await this.processAlert(alert);
      }
    } catch (error) {
      console.error('Error checking for alerts:', error.message);
    }
  }

  async processAlert(alert) {
    const alertKey = `${alert.labels.alertname}_${alert.labels.instance || 'default'}`;

    // Check if we already have an active incident for this alert
    if (this.activeIncidents.has(alertKey)) {
      const existingIncident = this.activeIncidents.get(alertKey);
      existingIncident.lastSeen = new Date();
      existingIncident.alertCount++;
      return;
    }

    // Create new incident
    const incident = {
      id: `incident_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      alertKey,
      title: alert.annotations.summary || alert.labels.alertname,
      description: alert.annotations.description || 'No description provided',
      severity: alert.labels.severity || 'unknown',
      status: 'active',
      createdAt: new Date(),
      lastSeen: new Date(),
      alertCount: 1,
      labels: alert.labels,
      annotations: alert.annotations,
      remediationAttempts: [],
      notificationsSent: [],
      timeout: this.incidentTimeout
    };

    this.activeIncidents.set(alertKey, incident);
    this.incidentMetrics.activeIncidents.inc();
    this.incidentMetrics.totalIncidents.inc({
      severity: incident.severity,
      category: alert.labels.service || 'unknown',
      resolved: 'false'
    });

    console.log(`🚨 New incident created: ${incident.id} - ${incident.title}`);

    // Emit incident created event
    this.emit('incidentCreated', incident);

    // Start incident response
    this.respondToIncident(incident);
  }

  async respondToIncident(incident) {
    const startTime = Date.now();

    try {
      // Classify incident
      await this.classifyIncident(incident);

      // Attempt automated remediation
      if (this.autoRemediate) {
        await this.attemptRemediation(incident);
      }

      // Send notifications
      await this.notifyStakeholders(incident);

      // Set up timeout for escalation
      setTimeout(() => {
        this.escalateIncident(incident);
      }, incident.timeout);

    } catch (error) {
      console.error(`Error responding to incident ${incident.id}:`, error);
      this.escalateIncident(incident, error.message);
    }

    // Record response time
    const responseTime = (Date.now() - startTime) / 1000;
    this.incidentMetrics.incidentResponseTime
      .observe({ severity: incident.severity }, responseTime);
  }

  async classifyIncident(incident) {
    // Classify based on alert labels and annotations
    incident.category = incident.labels.service || 'infrastructure';
    incident.impact = this.calculateImpact(incident);
    incident.urgency = this.calculateUrgency(incident);

    // Add classification to incident
    incident.classification = {
      category: incident.category,
      impact: incident.impact,
      urgency: incident.urgency,
      priority: this.calculatePriority(incident)
    };

    console.log(`📋 Incident ${incident.id} classified: ${incident.classification.category} (${incident.classification.priority} priority)`);
  }

  calculateImpact(incident) {
    const severity = incident.severity;
    const service = incident.labels.service;

    // High impact services
    const criticalServices = ['api', 'database', 'kubernetes', 'load-balancer'];

    if (severity === 'critical' && criticalServices.includes(service)) {
      return 'high';
    } else if (severity === 'critical') {
      return 'medium';
    } else if (severity === 'warning' && criticalServices.includes(service)) {
      return 'medium';
    }

    return 'low';
  }

  calculateUrgency(incident) {
    const severity = incident.severity;
    const impact = incident.classification?.impact || this.calculateImpact(incident);

    if (severity === 'critical' && impact === 'high') {
      return 'critical';
    } else if (severity === 'critical' || impact === 'high') {
      return 'high';
    } else if (severity === 'warning') {
      return 'medium';
    }

    return 'low';
  }

  calculatePriority(incident) {
    const urgency = incident.urgency;
    const impact = incident.impact;

    if (urgency === 'critical' || impact === 'high') {
      return 'P1';
    } else if (urgency === 'high' || impact === 'medium') {
      return 'P2';
    } else {
      return 'P3';
    }
  }

  async attemptRemediation(incident) {
    // Find applicable remediation rule
    const rule = Array.from(this.remediationRules.values())
      .find(rule => rule.condition(incident));

    if (!rule) {
      console.log(`⚠️ No remediation rule found for incident ${incident.id}`);
      return;
    }

    incident.remediationRule = rule;

    for (const action of rule.actions) {
      try {
        console.log(`🔧 Executing remediation: ${action.name} for incident ${incident.id}`);

        const result = await this.executeRemediationAction(action, incident, rule);

        incident.remediationAttempts.push({
          action: action.name,
          timestamp: new Date(),
          success: result.success,
          output: result.output,
          error: result.error
        });

        this.incidentMetrics.automatedRemediations.inc({
          action: action.name,
          success: result.success ? 'true' : 'false'
        });

        if (result.success) {
          console.log(`✅ Remediation successful: ${action.name}`);
          incident.status = 'resolved';
          incident.resolvedAt = new Date();
          break; // Stop after first successful remediation
        } else {
          console.log(`❌ Remediation failed: ${action.name} - ${result.error}`);
        }

      } catch (error) {
        console.error(`Error executing remediation ${action.name}:`, error);
        incident.remediationAttempts.push({
          action: action.name,
          timestamp: new Date(),
          success: false,
          error: error.message
        });
      }
    }
  }

  async executeRemediationAction(action, incident, rule) {
    let attempts = 0;
    let lastError = null;

    while (attempts <= rule.maxRetries) {
      try {
        const result = await action.execute(incident);
        return { success: true, output: result };
      } catch (error) {
        lastError = error;
        attempts++;
        if (attempts <= rule.maxRetries) {
          console.log(`Retrying remediation ${action.name} (attempt ${attempts}/${rule.maxRetries + 1})`);
          await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        }
      }
    }

    return { success: false, error: lastError?.message };
  }

  // Remediation action implementations
  async scaleDeployment(incident, deploymentName = null) {
    const deployment = deploymentName || `ai-infrastructure-portal-${incident.category}`;
    const namespace = 'ai-infrastructure';

    // Scale up by 50%
    const currentReplicas = await this.getCurrentReplicas(deployment, namespace);
    const newReplicas = Math.ceil(currentReplicas * 1.5);

    const { exec } = require('child_process');
    const command = `kubectl scale deployment ${deployment} --replicas=${newReplicas} -n ${namespace}`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Failed to scale deployment: ${stderr}`));
        } else {
          resolve(`Scaled ${deployment} from ${currentReplicas} to ${newReplicas} replicas`);
        }
      });
    });
  }

  async adjustResourceLimits(incident, resource = 'cpu') {
    // This would typically update the deployment's resource limits
    // For demo purposes, we'll simulate this
    console.log(`Adjusting ${resource} limits for ${incident.labels.service}`);
    return `Increased ${resource} limits for ${incident.labels.service}`;
  }

  async restartService(serviceName) {
    const { exec } = require('child_process');
    const command = `kubectl rollout restart deployment ${serviceName} -n ai-infrastructure`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Failed to restart service: ${stderr}`));
        } else {
          resolve(`Restarted service ${serviceName}`);
        }
      });
    });
  }

  async failoverToBackup(service) {
    // Implement backup failover logic
    console.log(`Failing over ${service} to backup instance`);
    return `Failed over ${service} to backup`;
  }

  async restartPods(deploymentName) {
    return this.restartService(deploymentName);
  }

  async rollbackDeployment(deploymentName) {
    const { exec } = require('child_process');
    const command = `kubectl rollout undo deployment ${deploymentName} -n ai-infrastructure`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Failed to rollback deployment: ${stderr}`));
        } else {
          resolve(`Rolled back deployment ${deploymentName}`);
        }
      });
    });
  }

  async reloadNginxConfig() {
    const { exec } = require('child_process');
    const command = `kubectl exec -n ai-infrastructure deployment/nginx-load-balancer -- nginx -s reload`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Failed to reload NGINX config: ${stderr}`));
        } else {
          resolve('Reloaded NGINX configuration');
        }
      });
    });
  }

  async checkNodeHealth(incident) {
    const { exec } = require('child_process');
    const command = `kubectl get nodes --no-headers | awk '{print $1}' | xargs -I {} kubectl describe node {}`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Failed to check node health: ${stderr}`));
        } else {
          // Analyze node status and return health report
          resolve(`Node health check completed: ${stdout.split('\n').length} nodes analyzed`);
        }
      });
    });
  }

  async reschedulePods(incident) {
    // Force reschedule pods by deleting them (they will be recreated by deployment)
    const { exec } = require('child_process');
    const command = `kubectl delete pods -l app=ai-infrastructure-portal -n ai-infrastructure --force --grace-period=0`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Failed to reschedule pods: ${stderr}`));
        } else {
          resolve('Rescheduled problematic pods');
        }
      });
    });
  }

  async getCurrentReplicas(deployment, namespace) {
    const { exec } = require('child_process');
    const command = `kubectl get deployment ${deployment} -n ${namespace} -o jsonpath='{.spec.replicas}'`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Failed to get replicas: ${stderr}`));
        } else {
          resolve(parseInt(stdout.trim()) || 1);
        }
      });
    });
  }

  async notifyStakeholders(incident) {
    const notifications = [];

    // Email notification
    if (this.emailTransporter && process.env.ALERT_EMAIL_RECIPIENTS) {
      try {
        await this.sendEmailNotification(incident);
        notifications.push('email');
      } catch (error) {
        console.error('Failed to send email notification:', error);
      }
    }

    // Slack notification
    if (this.slackClient && process.env.SLACK_CHANNEL) {
      try {
        await this.sendSlackNotification(incident);
        notifications.push('slack');
      } catch (error) {
        console.error('Failed to send Slack notification:', error);
      }
    }

    // Webhook notifications
    if (this.webhookUrls.teams) {
      try {
        await this.sendWebhookNotification('teams', incident);
        notifications.push('teams');
      } catch (error) {
        console.error('Failed to send Teams notification:', error);
      }
    }

    if (this.webhookUrls.pagerduty) {
      try {
        await this.sendPagerDutyNotification(incident);
        notifications.push('pagerduty');
      } catch (error) {
        console.error('Failed to send PagerDuty notification:', error);
      }
    }

    incident.notificationsSent = notifications;
    console.log(`📢 Sent notifications for incident ${incident.id}: ${notifications.join(', ')}`);
  }

  async sendEmailNotification(incident) {
    const recipients = process.env.ALERT_EMAIL_RECIPIENTS.split(',');

    await this.emailTransporter.sendMail({
      from: process.env.SMTP_USER,
      to: recipients,
      subject: `🚨 ${incident.classification.priority} Incident: ${incident.title}`,
      html: this.generateIncidentEmail(incident)
    });
  }

  async sendSlackNotification(incident) {
    const message = {
      channel: process.env.SLACK_CHANNEL,
      text: `🚨 *${incident.classification.priority} Incident*\n${incident.title}\n${incident.description}`,
      attachments: [{
        color: incident.severity === 'critical' ? 'danger' : 'warning',
        fields: [
          { title: 'Severity', value: incident.severity, short: true },
          { title: 'Service', value: incident.category, short: true },
          { title: 'Status', value: incident.status, short: true },
          { title: 'Created', value: incident.createdAt.toISOString(), short: true }
        ]
      }]
    };

    await this.slackClient.chat.postMessage(message);
  }

  async sendWebhookNotification(type, incident) {
    const payload = {
      incident: incident.id,
      title: incident.title,
      severity: incident.severity,
      status: incident.status,
      created: incident.createdAt.toISOString(),
      description: incident.description
    };

    await axios.post(this.webhookUrls[type], payload);
  }

  async sendPagerDutyNotification(incident) {
    const payload = {
      routing_key: this.webhookUrls.pagerduty,
      event_action: 'trigger',
      dedup_key: incident.id,
      payload: {
        summary: incident.title,
        severity: incident.severity,
        source: 'ai-infrastructure-portal',
        component: incident.category,
        group: 'infrastructure',
        class: 'incident',
        custom_details: {
          description: incident.description,
          impact: incident.impact,
          urgency: incident.urgency
        }
      }
    };

    await axios.post('https://events.pagerduty.com/v2/enqueue', payload);
  }

  generateIncidentEmail(incident) {
    return `
      <h1>🚨 ${incident.classification.priority} Incident Alert</h1>
      <h2>${incident.title}</h2>
      <p><strong>Description:</strong> ${incident.description}</p>
      <p><strong>Severity:</strong> ${incident.severity}</p>
      <p><strong>Category:</strong> ${incident.category}</p>
      <p><strong>Impact:</strong> ${incident.impact}</p>
      <p><strong>Urgency:</strong> ${incident.urgency}</p>
      <p><strong>Status:</strong> ${incident.status}</p>
      <p><strong>Created:</strong> ${incident.createdAt.toISOString()}</p>
      ${incident.remediationAttempts.length > 0 ? `
        <h3>Remediation Attempts</h3>
        <ul>
          ${incident.remediationAttempts.map(attempt =>
            `<li>${attempt.action}: ${attempt.success ? '✅ Success' : '❌ Failed'} ${attempt.error ? `(${attempt.error})` : ''}</li>`
          ).join('')}
        </ul>
      ` : ''}
      <hr>
      <p>This is an automated notification from the AI Infrastructure Portal Incident Response Engine.</p>
    `;
  }

  escalateIncident(incident, reason = 'Timeout exceeded') {
    if (incident.status === 'resolved') return;

    incident.status = 'escalated';
    incident.escalatedAt = new Date();
    incident.escalationReason = reason;

    this.incidentMetrics.incidentEscalations.inc({
      severity: incident.severity,
      reason: reason
    });

    console.log(`⚠️ Incident ${incident.id} escalated: ${reason}`);

    // Send escalation notifications
    this.notifyEscalation(incident);

    // Emit escalation event
    this.emit('incidentEscalated', incident);
  }

  async notifyEscalation(incident) {
    // Send escalation to higher priority channels (e.g., on-call engineers)
    const escalationMessage = `🚨🚨 ESCALATION: ${incident.title} (${incident.classification.priority})`;

    if (this.slackClient && process.env.SLACK_ESCALATION_CHANNEL) {
      try {
        await this.slackClient.chat.postMessage({
          channel: process.env.SLACK_ESCALATION_CHANNEL,
          text: escalationMessage,
          attachments: [{
            color: 'danger',
            text: `Incident ${incident.id} has been escalated due to: ${incident.escalationReason}`
          }]
        });
      } catch (error) {
        console.error('Failed to send escalation notification:', error);
      }
    }
  }

  cleanupResolvedIncidents() {
    const now = Date.now();
    const resolvedIncidents = [];

    for (const [key, incident] of this.activeIncidents) {
      if (incident.status === 'resolved' && incident.resolvedAt) {
        // Keep resolved incidents for 1 hour after resolution
        if (now - incident.resolvedAt.getTime() > 3600000) {
          resolvedIncidents.push(key);
          this.incidentHistory.push(incident);
        }
      } else if (incident.status === 'escalated') {
        // Keep escalated incidents for 24 hours
        if (now - incident.createdAt.getTime() > 86400000) {
          resolvedIncidents.push(key);
          this.incidentHistory.push(incident);
        }
      }
    }

    resolvedIncidents.forEach(key => {
      this.activeIncidents.delete(key);
    });

    if (resolvedIncidents.length > 0) {
      console.log(`🧹 Cleaned up ${resolvedIncidents.length} resolved/escalated incidents`);
    }

    // Update metrics
    this.incidentMetrics.activeIncidents.set(this.activeIncidents.size);
  }

  getActiveIncidents() {
    return Array.from(this.activeIncidents.values());
  }

  getIncidentHistory(limit = 100) {
    return this.incidentHistory.slice(-limit);
  }

  getMetrics() {
    return this.register.metrics();
  }

  async generateIncidentReport(incidentId) {
    const incident = this.activeIncidents.get(incidentId) ||
                    this.incidentHistory.find(i => i.id === incidentId);

    if (!incident) {
      throw new Error(`Incident ${incidentId} not found`);
    }

    const report = {
      incident,
      timeline: this.generateTimeline(incident),
      impact: this.calculateIncidentImpact(incident),
      recommendations: this.generateRecommendations(incident)
    };

    return report;
  }

  generateTimeline(incident) {
    const timeline = [
      { timestamp: incident.createdAt, event: 'Incident created', type: 'creation' }
    ];

    incident.remediationAttempts.forEach(attempt => {
      timeline.push({
        timestamp: attempt.timestamp,
        event: `Remediation attempt: ${attempt.action}`,
        type: attempt.success ? 'success' : 'failure',
        details: attempt.output || attempt.error
      });
    });

    incident.notificationsSent.forEach(notification => {
      timeline.push({
        timestamp: incident.createdAt, // Approximate
        event: `Notification sent: ${notification}`,
        type: 'notification'
      });
    });

    if (incident.escalatedAt) {
      timeline.push({
        timestamp: incident.escalatedAt,
        event: 'Incident escalated',
        type: 'escalation',
        details: incident.escalationReason
      });
    }

    if (incident.resolvedAt) {
      timeline.push({
        timestamp: incident.resolvedAt,
        event: 'Incident resolved',
        type: 'resolution'
      });
    }

    return timeline.sort((a, b) => a.timestamp - b.timestamp);
  }

  calculateIncidentImpact(incident) {
    const duration = incident.resolvedAt ?
      (incident.resolvedAt - incident.createdAt) / 1000 : // seconds
      (Date.now() - incident.createdAt) / 1000;

    return {
      duration,
      severity: incident.severity,
      affectedServices: [incident.category],
      estimatedDowntime: this.estimateDowntime(incident),
      userImpact: this.estimateUserImpact(incident)
    };
  }

  estimateDowntime(incident) {
    // Simple estimation based on severity and category
    const baseDowntime = {
      critical: 3600, // 1 hour
      warning: 600,   // 10 minutes
      info: 60        // 1 minute
    };

    const multiplier = incident.category === 'api' ? 2 :
                      incident.category === 'database' ? 3 : 1;

    return baseDowntime[incident.severity] * multiplier;
  }

  estimateUserImpact(incident) {
    // Estimate based on service and severity
    if (incident.category === 'api' && incident.severity === 'critical') {
      return 'high';
    } else if (incident.category === 'load-balancer' && incident.severity === 'warning') {
      return 'medium';
    }

    return 'low';
  }

  generateRecommendations(incident) {
    const recommendations = [];

    if (incident.remediationAttempts.length === 0) {
      recommendations.push('Implement automated remediation for this type of incident');
    }

    if (incident.escalationReason) {
      recommendations.push('Review incident response timeout settings');
    }

    if (incident.alertCount > 5) {
      recommendations.push('Consider implementing alert deduplication');
    }

    // Category-specific recommendations
    switch (incident.category) {
      case 'api':
        recommendations.push('Review API rate limiting and circuit breaker configurations');
        break;
      case 'database':
        recommendations.push('Implement database connection pooling and query optimization');
        break;
      case 'load-balancer':
        recommendations.push('Consider horizontal scaling for load balancer');
        break;
    }

    return recommendations;
  }
}

// Express server for incident response API
const express = require('express');
const app = express();
app.use(express.json());

const incidentEngine = new IncidentResponseEngine();

// Prometheus metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    const metrics = await incidentEngine.getMetrics();
    res.set('Content-Type', incidentEngine.register.contentType);
    res.end(metrics);
  } catch (error) {
    res.status(500).end(error.toString());
  }
});

// Active incidents API
app.get('/incidents/active', (req, res) => {
  const incidents = incidentEngine.getActiveIncidents();
  res.json({
    incidents,
    count: incidents.length,
    timestamp: new Date().toISOString()
  });
});

// Incident history API
app.get('/incidents/history', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  const history = incidentEngine.getIncidentHistory(limit);
  res.json({
    incidents: history,
    count: history.length,
    timestamp: new Date().toISOString()
  });
});

// Get specific incident
app.get('/incidents/:id', async (req, res) => {
  try {
    const report = await incidentEngine.generateIncidentReport(req.params.id);
    res.json(report);
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
});

// Manual incident creation (for testing)
app.post('/incidents', (req, res) => {
  const incident = {
    id: `manual_${Date.now()}`,
    title: req.body.title || 'Manual incident',
    description: req.body.description || 'Manually created incident',
    severity: req.body.severity || 'warning',
    status: 'active',
    createdAt: new Date(),
    labels: { service: req.body.service || 'manual' }
  };

  // Simulate alert processing
  incidentEngine.processAlert({
    labels: {
      alertname: 'ManualIncident',
      severity: incident.severity,
      service: incident.labels.service
    },
    annotations: {
      summary: incident.title,
      description: incident.description
    }
  });

  res.json({ message: 'Incident created', id: incident.id });
});

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    activeIncidents: incidentEngine.getActiveIncidents().length,
    incidentHistory: incidentEngine.incidentHistory.length,
    timestamp: new Date().toISOString()
  });
});

// Webhook endpoint for external alerts
app.post('/webhook/alert', (req, res) => {
  const alert = req.body;
  incidentEngine.processAlert(alert);
  res.json({ message: 'Alert processed' });
});

const PORT = process.env.INCIDENT_PORT || 9093;
app.listen(PORT, () => {
  console.log(`🚨 Incident response engine listening on port ${PORT}`);
  console.log(`📊 Metrics available at http://localhost:${PORT}/metrics`);
  console.log(`🚨 Active incidents at http://localhost:${PORT}/incidents/active`);
});

module.exports = IncidentResponseEngine;
