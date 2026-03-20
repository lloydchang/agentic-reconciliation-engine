#!/usr/bin/env node

/**
 * AI Infrastructure Portal - Compliance Monitoring & Audit Engine
 * Automated compliance monitoring, audit logging, and regulatory reporting
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const axios = require('axios');
const promClient = require('prom-client');

class ComplianceMonitoringEngine {
  constructor(options = {}) {
    this.auditLogPath = options.auditLogPath || '/var/log/ai-portal/audit.log';
    this.complianceChecks = new Map();
    this.auditEvents = [];
    this.complianceFrameworks = ['SOC2', 'GDPR', 'ISO27001', 'HIPAA', 'PCI-DSS'];

    this.register = new promClient.Registry();

    // Compliance metrics
    this.complianceMetrics = {
      complianceScore: new promClient.Gauge({
        name: 'ai_portal_compliance_score',
        help: 'Overall compliance score (0-100)',
        labelNames: ['framework'],
        registers: [this.register]
      }),

      auditEventsTotal: new promClient.Counter({
        name: 'ai_portal_audit_events_total',
        help: 'Total number of audit events logged',
        labelNames: ['event_type', 'severity', 'user'],
        registers: [this.register]
      }),

      complianceViolations: new promClient.Counter({
        name: 'ai_portal_compliance_violations_total',
        help: 'Total number of compliance violations detected',
        labelNames: ['framework', 'severity', 'category'],
        registers: [this.register]
      }),

      dataRetentionCompliance: new promClient.Gauge({
        name: 'ai_portal_data_retention_compliance',
        help: 'Data retention compliance percentage',
        registers: [this.register]
      }),

      accessControlCompliance: new promClient.Gauge({
        name: 'ai_portal_access_control_compliance',
        help: 'Access control compliance percentage',
        registers: [this.register]
      }),

      encryptionCompliance: new promClient.Gauge({
        name: 'ai_portal_encryption_compliance',
        help: 'Data encryption compliance percentage',
        registers: [this.register]
      })
    };

    this.setupComplianceChecks();
    this.ensureAuditLogDirectory();
    this.startComplianceMonitoring();
  }

  setupComplianceChecks() {
    // SOC2 Compliance Checks
    this.complianceChecks.set('SOC2_Security', {
      framework: 'SOC2',
      category: 'Security',
      check: this.checkSecurityControls.bind(this),
      frequency: 'daily',
      severity: 'critical'
    });

    this.complianceChecks.set('SOC2_AccessControl', {
      framework: 'SOC2',
      category: 'Access Control',
      check: this.checkAccessControls.bind(this),
      frequency: 'hourly',
      severity: 'high'
    });

    // GDPR Compliance Checks
    this.complianceChecks.set('GDPR_DataProtection', {
      framework: 'GDPR',
      category: 'Data Protection',
      check: this.checkDataProtection.bind(this),
      frequency: 'daily',
      severity: 'critical'
    });

    this.complianceChecks.set('GDPR_DataRetention', {
      framework: 'GDPR',
      category: 'Data Retention',
      check: this.checkDataRetention.bind(this),
      frequency: 'weekly',
      severity: 'high'
    });

    // ISO27001 Compliance Checks
    this.complianceChecks.set('ISO27001_RiskManagement', {
      framework: 'ISO27001',
      category: 'Risk Management',
      check: this.checkRiskManagement.bind(this),
      frequency: 'monthly',
      severity: 'medium'
    });

    this.complianceChecks.set('ISO27001_IncidentResponse', {
      framework: 'ISO27001',
      category: 'Incident Response',
      check: this.checkIncidentResponse.bind(this),
      frequency: 'weekly',
      severity: 'high'
    });

    // HIPAA Compliance Checks
    this.complianceChecks.set('HIPAA_Privacy', {
      framework: 'HIPAA',
      category: 'Privacy',
      check: this.checkPrivacyControls.bind(this),
      frequency: 'daily',
      severity: 'critical'
    });

    // PCI-DSS Compliance Checks
    this.complianceChecks.set('PCI_DSS_CardholderData', {
      framework: 'PCI-DSS',
      category: 'Cardholder Data',
      check: this.checkCardholderDataProtection.bind(this),
      frequency: 'daily',
      severity: 'critical'
    });
  }

  ensureAuditLogDirectory() {
    const logDir = path.dirname(this.auditLogPath);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }

  async logAuditEvent(event) {
    const auditEntry = {
      timestamp: new Date().toISOString(),
      eventId: crypto.randomUUID(),
      eventType: event.type,
      severity: event.severity,
      user: event.user || 'system',
      resource: event.resource,
      action: event.action,
      result: event.result,
      details: event.details,
      sourceIP: event.sourceIP,
      userAgent: event.userAgent,
      complianceFrameworks: event.complianceFrameworks || []
    };

    // Add to in-memory array for quick access
    this.auditEvents.push(auditEntry);

    // Keep only last 10000 events in memory
    if (this.auditEvents.length > 10000) {
      this.auditEvents = this.auditEvents.slice(-5000);
    }

    // Write to audit log file
    const logLine = JSON.stringify(auditEntry) + '\n';
    fs.appendFileSync(this.auditLogPath, logLine);

    // Update Prometheus metrics
    this.complianceMetrics.auditEventsTotal.inc({
      event_type: event.type,
      severity: event.severity,
      user: event.user
    });

    console.log(`📋 Audit Event: ${event.type} - ${event.action} by ${event.user}`);
  }

  async checkSecurityControls() {
    const violations = [];

    try {
      // Check SSL/TLS configuration
      const sslCheck = await this.checkSSLConfiguration();
      if (!sslCheck.compliant) {
        violations.push({
          rule: 'SSL_TLS_Configuration',
          severity: 'high',
          description: 'SSL/TLS configuration does not meet security standards',
          remediation: 'Update SSL certificates and ensure TLS 1.3 is enabled'
        });
      }

      // Check firewall rules
      const firewallCheck = await this.checkFirewallRules();
      if (!firewallCheck.compliant) {
        violations.push({
          rule: 'Firewall_Configuration',
          severity: 'critical',
          description: 'Firewall rules allow unauthorized access',
          remediation: 'Review and tighten firewall rules'
        });
      }

      // Check encryption at rest
      const encryptionCheck = await this.checkEncryptionAtRest();
      if (!encryptionCheck.compliant) {
        violations.push({
          rule: 'Encryption_At_Rest',
          severity: 'high',
          description: 'Data encryption at rest is not properly configured',
          remediation: 'Enable encryption for all data storage'
        });
      }

    } catch (error) {
      console.error('Error checking security controls:', error);
    }

    return violations;
  }

  async checkAccessControls() {
    const violations = [];

    try {
      // Check RBAC configuration
      const rbacCheck = await this.checkRBACConfiguration();
      if (!rbacCheck.compliant) {
        violations.push({
          rule: 'RBAC_Configuration',
          severity: 'high',
          description: 'Role-based access control is not properly configured',
          remediation: 'Review and update RBAC policies'
        });
      }

      // Check MFA requirements
      const mfaCheck = await this.checkMFARequirements();
      if (!mfaCheck.compliant) {
        violations.push({
          rule: 'MFA_Requirements',
          severity: 'medium',
          description: 'Multi-factor authentication is not enforced for all users',
          remediation: 'Enable MFA for all privileged accounts'
        });
      }

      // Check session management
      const sessionCheck = await this.checkSessionManagement();
      if (!sessionCheck.compliant) {
        violations.push({
          rule: 'Session_Management',
          severity: 'medium',
          description: 'Session management does not meet security standards',
          remediation: 'Implement proper session timeouts and management'
        });
      }

    } catch (error) {
      console.error('Error checking access controls:', error);
    }

    return violations;
  }

  async checkDataProtection() {
    const violations = [];

    try {
      // Check data classification
      const classificationCheck = await this.checkDataClassification();
      if (!classificationCheck.compliant) {
        violations.push({
          rule: 'Data_Classification',
          severity: 'medium',
          description: 'Sensitive data is not properly classified',
          remediation: 'Implement data classification and labeling'
        });
      }

      // Check data minimization
      const minimizationCheck = await this.checkDataMinimization();
      if (!minimizationCheck.compliant) {
        violations.push({
          rule: 'Data_Minimization',
          severity: 'low',
          description: 'Data collection exceeds necessary requirements',
          remediation: 'Review and minimize data collection practices'
        });
      }

    } catch (error) {
      console.error('Error checking data protection:', error);
    }

    return violations;
  }

  async checkDataRetention() {
    const violations = [];

    try {
      // Check retention policies
      const retentionCheck = await this.checkRetentionPolicies();
      if (!retentionCheck.compliant) {
        violations.push({
          rule: 'Data_Retention_Policies',
          severity: 'high',
          description: 'Data retention policies do not comply with regulations',
          remediation: 'Update retention policies and implement automated deletion'
        });
      }

      // Update retention compliance metric
      this.complianceMetrics.dataRetentionCompliance.set(retentionCheck.compliancePercentage);

    } catch (error) {
      console.error('Error checking data retention:', error);
    }

    return violations;
  }

  async checkPrivacyControls() {
    const violations = [];

    try {
      // Check consent management
      const consentCheck = await this.checkConsentManagement();
      if (!consentCheck.compliant) {
        violations.push({
          rule: 'Consent_Management',
          severity: 'critical',
          description: 'User consent is not properly managed',
          remediation: 'Implement comprehensive consent management system'
        });
      }

      // Check data subject rights
      const rightsCheck = await this.checkDataSubjectRights();
      if (!rightsCheck.compliant) {
        violations.push({
          rule: 'Data_Subject_Rights',
          severity: 'high',
          description: 'Data subject rights are not properly implemented',
          remediation: 'Implement data subject rights request handling'
        });
      }

    } catch (error) {
      console.error('Error checking privacy controls:', error);
    }

    return violations;
  }

  async checkCardholderDataProtection() {
    const violations = [];

    try {
      // Check PCI DSS controls
      const pciCheck = await this.checkPCIDSSControls();
      if (!pciCheck.compliant) {
        violations.push({
          rule: 'PCI_DSS_Controls',
          severity: 'critical',
          description: 'PCI DSS controls are not properly implemented',
          remediation: 'Implement required PCI DSS security controls'
        });
      }

    } catch (error) {
      console.error('Error checking cardholder data protection:', error);
    }

    return violations;
  }

  // Mock compliance check implementations (would be replaced with actual checks)
  async checkSSLConfiguration() {
    return { compliant: true, details: 'SSL/TLS properly configured' };
  }

  async checkFirewallRules() {
    return { compliant: true, details: 'Firewall rules are secure' };
  }

  async checkEncryptionAtRest() {
    return { compliant: true, details: 'Encryption at rest enabled' };
  }

  async checkRBACConfiguration() {
    return { compliant: true, details: 'RBAC properly configured' };
  }

  async checkMFARequirements() {
    return { compliant: true, details: 'MFA enforced for privileged accounts' };
  }

  async checkSessionManagement() {
    return { compliant: true, details: 'Session management secure' };
  }

  async checkDataClassification() {
    return { compliant: true, details: 'Data properly classified' };
  }

  async checkDataMinimization() {
    return { compliant: true, details: 'Data collection minimized' };
  }

  async checkRetentionPolicies() {
    return { compliant: true, compliancePercentage: 95 };
  }

  async checkConsentManagement() {
    return { compliant: true, details: 'Consent management implemented' };
  }

  async checkDataSubjectRights() {
    return { compliant: true, details: 'Data subject rights implemented' };
  }

  async checkPCIDSSControls() {
    return { compliant: true, details: 'PCI DSS controls implemented' };
  }

  async checkRiskManagement() {
    return { compliant: true, details: 'Risk management processes in place' };
  }

  async checkIncidentResponse() {
    return { compliant: true, details: 'Incident response procedures documented' };
  }

  async runComplianceChecks() {
    console.log('🔍 Running compliance checks...');

    const results = {};

    for (const [checkId, checkConfig] of this.complianceChecks) {
      try {
        const violations = await checkConfig.check();

        results[checkId] = {
          framework: checkConfig.framework,
          category: checkConfig.category,
          violations: violations,
          timestamp: new Date().toISOString(),
          status: violations.length === 0 ? 'compliant' : 'violations_found'
        };

        // Log violations
        violations.forEach(violation => {
          this.complianceMetrics.complianceViolations.inc({
            framework: checkConfig.framework,
            severity: violation.severity,
            category: checkConfig.category
          });

          await this.logAuditEvent({
            type: 'compliance_violation',
            severity: violation.severity,
            user: 'system',
            resource: checkId,
            action: 'violation_detected',
            result: 'violation',
            details: violation,
            complianceFrameworks: [checkConfig.framework]
          });
        });

        // Update compliance score
        const complianceScore = violations.length === 0 ? 100 :
          Math.max(0, 100 - (violations.length * 10));
        this.complianceMetrics.complianceScore.set({
          framework: checkConfig.framework
        }, complianceScore);

      } catch (error) {
        console.error(`Error running compliance check ${checkId}:`, error);
        results[checkId] = {
          framework: checkConfig.framework,
          category: checkConfig.category,
          error: error.message,
          timestamp: new Date().toISOString(),
          status: 'error'
        };
      }
    }

    return results;
  }

  startComplianceMonitoring() {
    // Initial compliance check
    this.runComplianceChecks();

    // Set up periodic compliance checks
    setInterval(() => {
      this.runComplianceChecks();
    }, 3600000); // Check every hour

    console.log('⚖️ Compliance monitoring engine started - checking every hour');
  }

  getComplianceReport(framework = null) {
    const report = {
      timestamp: new Date().toISOString(),
      frameworks: {},
      summary: {
        totalChecks: 0,
        compliantChecks: 0,
        violations: 0
      }
    };

    for (const [checkId, checkConfig] of this.complianceChecks) {
      if (framework && checkConfig.framework !== framework) continue;

      if (!report.frameworks[checkConfig.framework]) {
        report.frameworks[checkConfig.framework] = {
          checks: 0,
          violations: 0,
          complianceScore: 0
        };
      }

      report.frameworks[checkConfig.framework].checks++;
      report.summary.totalChecks++;
    }

    return report;
  }

  getAuditEvents(limit = 100, filters = {}) {
    let events = [...this.auditEvents];

    // Apply filters
    if (filters.eventType) {
      events = events.filter(e => e.eventType === filters.eventType);
    }
    if (filters.severity) {
      events = events.filter(e => e.severity === filters.severity);
    }
    if (filters.user) {
      events = events.filter(e => e.user === filters.user);
    }
    if (filters.startDate) {
      const startDate = new Date(filters.startDate);
      events = events.filter(e => new Date(e.timestamp) >= startDate);
    }
    if (filters.endDate) {
      const endDate = new Date(filters.endDate);
      events = events.filter(e => new Date(e.timestamp) <= endDate);
    }

    return events.slice(-limit);
  }

  getMetrics() {
    return this.register.metrics();
  }

  async generateComplianceReport(framework) {
    const results = await this.runComplianceChecks();

    const report = {
      framework,
      timestamp: new Date().toISOString(),
      checks: Object.entries(results)
        .filter(([_, result]) => result.framework === framework)
        .map(([checkId, result]) => ({
          checkId,
          category: result.category,
          status: result.status,
          violations: result.violations || [],
          timestamp: result.timestamp
        })),
      summary: {
        totalChecks: Object.values(results).filter(r => r.framework === framework).length,
        compliantChecks: Object.values(results)
          .filter(r => r.framework === framework && r.status === 'compliant').length,
        violations: Object.values(results)
          .filter(r => r.framework === framework)
          .reduce((sum, r) => sum + (r.violations?.length || 0), 0)
      }
    };

    return report;
  }
}

// Express server for compliance monitoring API
const express = require('express');
const app = express();
app.use(express.json());

const complianceEngine = new ComplianceMonitoringEngine();

// Prometheus metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    const metrics = await complianceEngine.getMetrics();
    res.set('Content-Type', complianceEngine.register.contentType);
    res.end(metrics);
  } catch (error) {
    res.status(500).end(error.toString());
  }
});

// Compliance report endpoint
app.get('/compliance/:framework?', async (req, res) => {
  try {
    const framework = req.params.framework;
    const report = complianceEngine.getComplianceReport(framework);
    res.json(report);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Generate detailed compliance report
app.post('/compliance/:framework/report', async (req, res) => {
  try {
    const framework = req.params.framework;
    const report = await complianceEngine.generateComplianceReport(framework);
    res.json(report);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Audit events endpoint
app.get('/audit', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  const filters = {
    eventType: req.query.eventType,
    severity: req.query.severity,
    user: req.query.user,
    startDate: req.query.startDate,
    endDate: req.query.endDate
  };

  const events = complianceEngine.getAuditEvents(limit, filters);
  res.json({
    events,
    count: events.length,
    filters
  });
});

// Log audit event endpoint
app.post('/audit', async (req, res) => {
  try {
    await complianceEngine.logAuditEvent(req.body);
    res.json({ message: 'Audit event logged' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    auditEvents: complianceEngine.auditEvents.length,
    complianceChecks: complianceEngine.complianceChecks.size,
    timestamp: new Date().toISOString()
  });
});

const PORT = process.env.COMPLIANCE_PORT || 9094;
app.listen(PORT, () => {
  console.log(`⚖️ Compliance monitoring engine listening on port ${PORT}`);
  console.log(`📊 Metrics available at http://localhost:${PORT}/metrics`);
  console.log(`📋 Audit API at http://localhost:${PORT}/audit`);
  console.log(`⚖️ Compliance API at http://localhost:${PORT}/compliance`);
});

module.exports = ComplianceMonitoringEngine;
