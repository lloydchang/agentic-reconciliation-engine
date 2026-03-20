#!/usr/bin/env node

/**
 * Infrastructure Drift Detection and Remediation Engine
 * Automated detection and correction of configuration drift
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync, spawn } = require('child_process');
const yaml = require('js-yaml');
const axios = require('axios');

class DriftDetectionEngine {
  constructor(options = {}) {
    this.clusterUrl = options.clusterUrl || 'https://kubernetes.default.svc';
    this.namespace = options.namespace || 'ai-infrastructure';
    this.kubeconfig = options.kubeconfig || process.env.KUBECONFIG;
    this.driftThreshold = options.driftThreshold || 0.05; // 5% change threshold
    this.scanInterval = options.scanInterval || 300000; // 5 minutes
    this.baselineDir = options.baselineDir || '/tmp/drift-baselines';
    this.remediationEnabled = options.remediationEnabled !== false;

    this.driftHistory = [];
    this.baselines = new Map();

    // Ensure baseline directory exists
    if (!fs.existsSync(this.baselineDir)) {
      fs.mkdirSync(this.baselineDir, { recursive: true });
    }
  }

  async startMonitoring() {
    console.log('🔍 Starting infrastructure drift detection monitoring...');

    // Initial baseline capture
    await this.captureBaseline();

    // Start periodic drift detection
    setInterval(async () => {
      try {
        await this.detectDrift();
      } catch (error) {
        console.error('Error during drift detection:', error);
      }
    }, this.scanInterval);

    console.log(`📊 Drift detection active - scanning every ${this.scanInterval / 1000} seconds`);
  }

  async captureBaseline() {
    console.log('📸 Capturing infrastructure baseline...');

    const resources = await this.getClusterResources();
    const baseline = {
      timestamp: new Date().toISOString(),
      resources: {},
      checksums: {}
    };

    for (const [resourceType, items] of Object.entries(resources)) {
      baseline.resources[resourceType] = items;
      baseline.checksums[resourceType] = this.calculateResourceChecksum(items);
    }

    // Save baseline
    const baselineFile = path.join(this.baselineDir, `baseline-${Date.now()}.json`);
    fs.writeFileSync(baselineFile, JSON.stringify(baseline, null, 2));

    // Update in-memory baseline
    this.baselines.set('current', baseline);

    console.log(`✅ Baseline captured with ${Object.keys(resources).length} resource types`);
    return baseline;
  }

  async detectDrift() {
    console.log('🔍 Scanning for infrastructure drift...');

    const currentResources = await this.getClusterResources();
    const baseline = this.baselines.get('current');

    if (!baseline) {
      console.warn('No baseline available for drift detection');
      return;
    }

    const driftReport = {
      timestamp: new Date().toISOString(),
      baselineTimestamp: baseline.timestamp,
      driftDetected: false,
      changes: [],
      summary: {
        added: 0,
        removed: 0,
        modified: 0,
        unchanged: 0
      }
    };

    // Compare each resource type
    for (const [resourceType, currentItems] of Object.entries(currentResources)) {
      const baselineItems = baseline.resources[resourceType] || [];
      const currentChecksums = this.calculateResourceChecksum(currentItems);
      const baselineChecksum = baseline.checksums[resourceType];

      if (currentChecksums !== baselineChecksum) {
        const changes = this.compareResourceSets(baselineItems, currentItems, resourceType);
        driftReport.changes.push(...changes);
        driftReport.driftDetected = true;
      } else {
        driftReport.summary.unchanged++;
      }
    }

    // Update summary counts
    driftReport.summary.added = driftReport.changes.filter(c => c.type === 'added').length;
    driftReport.summary.removed = driftReport.changes.filter(c => c.type === 'removed').length;
    driftReport.summary.modified = driftReport.changes.filter(c => c.type === 'modified').length;

    // Log drift report
    this.driftHistory.push(driftReport);

    if (driftReport.driftDetected) {
      console.log(`⚠️  Drift detected: ${driftReport.summary.added} added, ${driftReport.summary.removed} removed, ${driftReport.summary.modified} modified`);

      // Trigger remediation if enabled
      if (this.remediationEnabled) {
        await this.remediateDrift(driftReport);
      }
    } else {
      console.log('✅ No drift detected - infrastructure matches baseline');
    }

    return driftReport;
  }

  async getClusterResources() {
    const resources = {};

    // Define resource types to monitor
    const resourceTypes = [
      'deployments.apps',
      'statefulsets.apps',
      'services',
      'configmaps',
      'secrets',
      'ingresses.networking.k8s.io',
      'networkpolicies.networking.k8s.io',
      'serviceaccounts',
      'roles.rbac.authorization.k8s.io',
      'rolebindings.rbac.authorization.k8s.io',
      'clusterroles.rbac.authorization.k8s.io',
      'clusterrolebindings.rbac.authorization.k8s.io',
      'poddisruptionbudgets.policy',
      'horizontalpodautoscalers.autoscaling',
      'verticalpodautoscalers.autoscaling.k8s.io'
    ];

    for (const resourceType of resourceTypes) {
      try {
        const output = execSync(
          `kubectl get ${resourceType} -n ${this.namespace} -o json --ignore-not-found`,
          { encoding: 'utf8', env: { ...process.env, KUBECONFIG: this.kubeconfig } }
        );

        const data = JSON.parse(output);
        resources[resourceType] = data.items || [];
      } catch (error) {
        console.warn(`Failed to get ${resourceType}:`, error.message);
        resources[resourceType] = [];
      }
    }

    return resources;
  }

  calculateResourceChecksum(resources) {
    const normalized = resources.map(resource => ({
      apiVersion: resource.apiVersion,
      kind: resource.kind,
      metadata: {
        name: resource.metadata.name,
        namespace: resource.metadata.namespace,
        labels: resource.metadata.labels,
        annotations: this.filterAnnotations(resource.metadata.annotations)
      },
      spec: this.normalizeSpec(resource.spec)
    }));

    const jsonString = JSON.stringify(normalized, Object.keys(normalized).sort());
    return crypto.createHash('sha256').update(jsonString).digest('hex');
  }

  filterAnnotations(annotations) {
    if (!annotations) return {};

    // Filter out dynamic annotations that change frequently
    const filtered = { ...annotations };
    delete filtered['kubectl.kubernetes.io/restartedAt'];
    delete filtered['deployment.kubernetes.io/revision'];
    delete filtered['last-applied-configuration'];

    return filtered;
  }

  normalizeSpec(spec) {
    if (!spec) return spec;

    const normalized = { ...spec };

    // Remove fields that change frequently or are not relevant for drift detection
    delete normalized.status;
    delete normalized.metadata;
    delete normalized.generation;

    // Normalize timestamps and other dynamic fields
    if (normalized.template && normalized.template.metadata) {
      delete normalized.template.metadata.creationTimestamp;
      delete normalized.template.metadata.managedFields;
    }

    return normalized;
  }

  compareResourceSets(baselineItems, currentItems, resourceType) {
    const changes = [];
    const baselineMap = new Map(baselineItems.map(item => [item.metadata.name, item]));
    const currentMap = new Map(currentItems.map(item => [item.metadata.name, item]));

    // Find added resources
    for (const [name, item] of currentMap) {
      if (!baselineMap.has(name)) {
        changes.push({
          type: 'added',
          resourceType,
          name,
          details: this.summarizeResource(item)
        });
      }
    }

    // Find removed resources
    for (const [name, item] of baselineMap) {
      if (!currentMap.has(name)) {
        changes.push({
          type: 'removed',
          resourceType,
          name,
          details: this.summarizeResource(item)
        });
      }
    }

    // Find modified resources
    for (const [name, currentItem] of currentMap) {
      const baselineItem = baselineMap.get(name);
      if (baselineItem) {
        const diff = this.calculateResourceDiff(baselineItem, currentItem);
        if (diff.hasChanges) {
          changes.push({
            type: 'modified',
            resourceType,
            name,
            details: this.summarizeResource(currentItem),
            changes: diff.changes
          });
        }
      }
    }

    return changes;
  }

  summarizeResource(resource) {
    return {
      kind: resource.kind,
      apiVersion: resource.apiVersion,
      namespace: resource.metadata.namespace,
      labels: resource.metadata.labels,
      annotations: this.filterAnnotations(resource.metadata.annotations)
    };
  }

  calculateResourceDiff(baseline, current) {
    const changes = [];
    let hasChanges = false;

    // Compare labels
    const baselineLabels = baseline.metadata.labels || {};
    const currentLabels = current.metadata.labels || {};

    for (const [key, value] of Object.entries(currentLabels)) {
      if (baselineLabels[key] !== value) {
        changes.push(`Label ${key} changed from '${baselineLabels[key]}' to '${value}'`);
        hasChanges = true;
      }
    }

    for (const key of Object.keys(baselineLabels)) {
      if (!(key in currentLabels)) {
        changes.push(`Label ${key} removed`);
        hasChanges = true;
      }
    }

    // Compare annotations (filtered)
    const baselineAnnotations = this.filterAnnotations(baseline.metadata.annotations || {});
    const currentAnnotations = this.filterAnnotations(current.metadata.annotations || {});

    for (const [key, value] of Object.entries(currentAnnotations)) {
      if (baselineAnnotations[key] !== value) {
        changes.push(`Annotation ${key} changed`);
        hasChanges = true;
      }
    }

    // Compare specs
    const specDiff = this.deepDiff(baseline.spec, current.spec);
    if (specDiff.length > 0) {
      changes.push(...specDiff.map(diff => `Spec: ${diff}`));
      hasChanges = true;
    }

    return { hasChanges, changes };
  }

  deepDiff(obj1, obj2, path = '') {
    const differences = [];

    function compare(a, b, currentPath) {
      if (a === b) return;

      if (a === null || a === undefined || b === null || b === undefined) {
        if (a !== b) {
          differences.push(`${currentPath}: ${JSON.stringify(a)} -> ${JSON.stringify(b)}`);
        }
        return;
      }

      if (typeof a !== typeof b) {
        differences.push(`${currentPath}: type changed from ${typeof a} to ${typeof b}`);
        return;
      }

      if (typeof a === 'object') {
        const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
        for (const key of keys) {
          const newPath = currentPath ? `${currentPath}.${key}` : key;
          compare(a[key], b[key], newPath);
        }
      } else if (a !== b) {
        differences.push(`${currentPath}: ${a} -> ${b}`);
      }
    }

    compare(obj1, obj2, path);
    return differences;
  }

  async remediateDrift(driftReport) {
    console.log('🔧 Starting drift remediation...');

    const remediationActions = [];

    for (const change of driftReport.changes) {
      switch (change.type) {
        case 'added':
          // Evaluate if added resource should be allowed
          if (this.shouldRemediateAddition(change)) {
            remediationActions.push({
              action: 'review',
              type: 'addition',
              resource: change,
              reason: 'Unexpected resource addition detected'
            });
          }
          break;

        case 'removed':
          // Check if critical resource was removed
          if (this.shouldRemediateRemoval(change)) {
            remediationActions.push({
              action: 'restore',
              type: 'removal',
              resource: change,
              reason: 'Critical resource removal detected'
            });
          }
          break;

        case 'modified':
          // Check if modification violates policies
          if (this.shouldRemediateModification(change)) {
            remediationActions.push({
              action: 'rollback',
              type: 'modification',
              resource: change,
              reason: 'Policy violation detected in resource modification'
            });
          }
          break;
      }
    }

    // Execute remediation actions
    for (const action of remediationActions) {
      await this.executeRemediationAction(action);
    }

    if (remediationActions.length > 0) {
      console.log(`✅ Executed ${remediationActions.length} remediation actions`);
    } else {
      console.log('✅ No remediation actions required');
    }
  }

  shouldRemediateAddition(change) {
    // Define rules for when to remediate additions
    const criticalResources = [
      'networkpolicies.networking.k8s.io',
      'poddisruptionbudgets.policy',
      'roles.rbac.authorization.k8s.io',
      'clusterroles.rbac.authorization.k8s.io'
    ];

    return criticalResources.includes(change.resourceType);
  }

  shouldRemediateRemoval(change) {
    // Define rules for when to remediate removals
    const criticalResources = [
      'deployments.apps',
      'services',
      'ingresses.networking.k8s.io',
      'networkpolicies.networking.k8s.io'
    ];

    return criticalResources.includes(change.resourceType);
  }

  shouldRemediateModification(change) {
    // Check for policy violations in modifications
    const policyViolations = change.changes.filter(changeDesc =>
      changeDesc.includes('securityContext') ||
      changeDesc.includes('image:') ||
      changeDesc.includes('privileged') ||
      changeDesc.includes('hostPath')
    );

    return policyViolations.length > 0;
  }

  async executeRemediationAction(action) {
    console.log(`🔧 Executing remediation: ${action.action} for ${action.type} of ${action.resource.name}`);

    switch (action.action) {
      case 'restore':
        await this.restoreResource(action.resource);
        break;

      case 'rollback':
        await this.rollbackResource(action.resource);
        break;

      case 'review':
        await this.createReviewRequest(action);
        break;

      default:
        console.warn(`Unknown remediation action: ${action.action}`);
    }
  }

  async restoreResource(resource) {
    try {
      // This would typically restore from GitOps repository
      console.log(`Restoring ${resource.resourceType}/${resource.name} from GitOps repository`);

      // Placeholder for actual restoration logic
      // In a real implementation, this would:
      // 1. Get the resource definition from Git
      // 2. Apply it to the cluster
      // 3. Verify restoration

    } catch (error) {
      console.error(`Failed to restore ${resource.name}:`, error);
    }
  }

  async rollbackResource(resource) {
    try {
      console.log(`Rolling back ${resource.resourceType}/${resource.name} to baseline state`);

      // Placeholder for rollback logic
      // In a real implementation, this would:
      // 1. Get the baseline version of the resource
      // 2. Apply it to the cluster
      // 3. Verify rollback

    } catch (error) {
      console.error(`Failed to rollback ${resource.name}:`, error);
    }
  }

  async createReviewRequest(action) {
    console.log(`📋 Creating review request for ${action.resource.name}`);

    // Create notification for human review
    const reviewRequest = {
      timestamp: new Date().toISOString(),
      resource: action.resource,
      reason: action.reason,
      actionRequired: 'human_review',
      severity: this.determineSeverity(action)
    };

    // In a real implementation, this would:
    // 1. Create a ticket in the incident management system
    // 2. Send notifications to the responsible team
    // 3. Log the review request for audit purposes

    console.log('Review request created:', JSON.stringify(reviewRequest, null, 2));
  }

  determineSeverity(action) {
    if (action.type === 'removal' && this.isCriticalResource(action.resource)) {
      return 'high';
    }
    if (action.type === 'modification' && action.resource.changes.some(c =>
      c.includes('security') || c.includes('privileged'))) {
      return 'high';
    }
    return 'medium';
  }

  isCriticalResource(resource) {
    const criticalTypes = [
      'deployments.apps',
      'statefulsets.apps',
      'services',
      'ingresses.networking.k8s.io'
    ];

    return criticalTypes.includes(resource.resourceType);
  }

  getDriftHistory(limit = 10) {
    return this.driftHistory.slice(-limit);
  }

  getDriftStatistics() {
    const stats = {
      totalScans: this.driftHistory.length,
      driftIncidents: this.driftHistory.filter(h => h.driftDetected).length,
      totalChanges: this.driftHistory.reduce((sum, h) => sum + h.changes.length, 0),
      mostCommonChanges: {}
    };

    // Calculate most common change types
    const changeTypes = {};
    this.driftHistory.forEach(history => {
      history.changes.forEach(change => {
        changeTypes[change.type] = (changeTypes[change.type] || 0) + 1;
      });
    });

    stats.mostCommonChanges = changeTypes;

    return stats;
  }

  async generateDriftReport() {
    const history = this.getDriftHistory(50);
    const stats = this.getDriftStatistics();

    return {
      generatedAt: new Date().toISOString(),
      monitoringPeriod: history.length > 0 ?
        `${history[0].timestamp} to ${history[history.length - 1].timestamp}` : 'N/A',
      statistics: stats,
      recentDrifts: history.filter(h => h.driftDetected).slice(-10),
      recommendations: this.generateRecommendations(stats)
    };
  }

  generateRecommendations(stats) {
    const recommendations = [];

    if (stats.driftIncidents / stats.totalScans > 0.1) {
      recommendations.push({
        priority: 'high',
        recommendation: 'High drift frequency detected. Consider implementing stricter policy controls.',
        action: 'Review and strengthen Kyverno policies'
      });
    }

    if (stats.mostCommonChanges.removed > stats.mostCommonChanges.added) {
      recommendations.push({
        priority: 'medium',
        recommendation: 'More resources are being removed than added. Check for unauthorized deletions.',
        action: 'Implement resource deletion alerts and approval workflows'
      });
    }

    if (stats.mostCommonChanges.modified > stats.totalChanges * 0.5) {
      recommendations.push({
        priority: 'medium',
        recommendation: 'High frequency of resource modifications detected.',
        action: 'Review change management processes'
      });
    }

    return recommendations;
  }
}

// CLI interface
if (require.main === module) {
  const engine = new DriftDetectionEngine({
    namespace: process.argv[3] || 'ai-infrastructure',
    remediationEnabled: process.argv[4] !== 'no-remediation'
  });

  const command = process.argv[2];

  switch (command) {
    case 'baseline':
      engine.captureBaseline()
        .then(() => console.log('Baseline captured successfully'))
        .catch(error => {
          console.error('Failed to capture baseline:', error);
          process.exit(1);
        });
      break;

    case 'detect':
      engine.detectDrift()
        .then(report => {
          console.log(JSON.stringify(report, null, 2));
          process.exit(report.driftDetected ? 1 : 0);
        })
        .catch(error => {
          console.error('Drift detection failed:', error);
          process.exit(1);
        });
      break;

    case 'monitor':
      engine.startMonitoring();
      // Keep process alive
      process.on('SIGINT', () => {
        console.log('Stopping drift detection monitoring...');
        process.exit(0);
      });
      break;

    case 'report':
      engine.generateDriftReport()
        .then(report => {
          console.log(JSON.stringify(report, null, 2));
        })
        .catch(error => {
          console.error('Failed to generate report:', error);
          process.exit(1);
        });
      break;

    default:
      console.log('Usage:');
      console.log('  baseline [namespace]     - Capture infrastructure baseline');
      console.log('  detect [namespace]       - Run drift detection scan');
      console.log('  monitor [namespace]      - Start continuous monitoring');
      console.log('  report                   - Generate drift analysis report');
      process.exit(1);
  }
}

module.exports = DriftDetectionEngine;
