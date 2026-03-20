#!/usr/bin/env python3
"""
Update Multi-Cloud Skills for Crossplane

This script updates all multi-cloud orchestrator skills to use Crossplane
instead of direct cloud provider SDKs.

It transforms:
  - multi_cloud_orchestrator.py (uses boto3/azure-sdk/gcp-sdk)
  + Crossplane Kubernetes API client

  - multi-cloud-abstraction.js (direct cloud SDK calls)
  + Crossplane REST API wrapper

  - multi-cloud-scatter-gather.go (Temporal activities calling cloud APIs)
  + Crossplane resource querying

Usage:
  python update-skills-for-crossplane.py [--dry-run] [--backup]

Author: Agentic Reconciliation Engine Migration Tool
"""

import os
import re
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.parent
SKILLS_DIR = BASE_DIR / "core" / "ai" / "skills"
BACKUP_SUFFIX = f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"

# Dry run flag
DRY_RUN = False

def log_info(msg):
    print(f"[INFO] {msg}")

def log_warn(msg):
    print(f"[WARN] {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}")

def backup_file(filepath):
    """Create a backup of a file before modifying"""
    backup_path = filepath + BACKUP_SUFFIX
    shutil.copy2(filepath, backup_path)
    log_info(f"Backed up {filepath} -> {backup_path}")

def update_multi_cloud_orchestrator_py():
    """Update multi_cloud_orchestrator.py to use Crossplane"""
    filepath = BASE_DIR / "core" / "ai" / "skills" / "manage-infrastructure" / "scripts" / "multi_cloud_orchestrator.py"

    if not filepath.exists():
        log_warn(f"File not found: {filepath}")
        return

    log_info(f"Updating {filepath}...")

    if DRY_RUN:
        log_info("[DRY RUN] Would update multi_cloud_orchestrator.py")
        return

    backup_file(filepath)

    # Read original content
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace imports
    new_imports = '''#!/usr/bin/env python3
"""
Multi-Cloud Infrastructure Orchestrator (Crossplane)

Orchestrates infrastructure provisioning using Crossplane XResources
instead of direct cloud provider SDKs.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import statistics

logger = logging.getLogger(__name__)

# Load kube config
config.load_kube_config()
custom_api = client.CustomObjectsApi()
'''

    # Remove old imports
    content = re.sub(
        r'#!/usr/bin/env python3\n"""[\s\S]*?""".*?(?=\nclass|\nimport|\nfrom)',
        new_imports,
        content,
        flags=re.MULTILINE
    )

    # Replace provider initialization
    old_init = r'def __init__\(self,.*?\):.*?self\.handlers = \{\}.*?self\.tasks = \[\]'
    new_init = '''def __init__(self):
        self.k8s_client = custom_api
        self.namespace = os.getenv('CROSSPLANE_NAMESPACE', 'default')
        # No cloud-specific handlers needed - Crossplane abstracts providers
'''

    content = re.sub(old_init, new_init, content, flags=re.DOTALL)

    # Replace initialize_handlers method
    initialize_pattern = r'def initialize_handlers\(self.*?\n.*?return success\n.*?\n(?=\s+def )'
    initialize_replacement = '''def initialize_handlers(self) -> Dict[str, bool]:
        """Verify Crossplane is ready (no provider-specific initialization needed)"""
        results = {'crossplane': True}
        try:
            # Check Crossplane providers are healthy
            providers = custom_api.list_cluster_custom_object(
                group='pkg.crossplane.io',
                version='v1',
                plural='providers'
            )
            for provider in providers.get('items', []):
                name = provider['metadata']['name']
                healthy = provider.get('status', {}).get('healthy', False)
                results[name] = healthy
                if not healthy:
                    logger.error(f"Provider {name} is not healthy")
            return results
        except Exception as e:
            logger.error(f"Failed to check Crossplane providers: {e}")
            return {'crossplane': False}
'''

    content = re.sub(initialize_pattern, initialize_replacement, content, flags=re.DOTALL)

    # Replace provisioning methods to create Crossplane resources
    # This is simplified - you'd need to adapt based on your actual orchestrator usage

    # Add Crossplane helper methods
    crossplane_methods = '''
    def create_crossplane_resource(self, group, version, kind, name, spec):
        """Create a Crossplane custom resource"""
        try:
            body = {
                "apiVersion": f"{group}/{version}",
                "kind": kind,
                "metadata": {"name": name},
                "spec": spec
            }
            return self.k8s_client.create_cluster_custom_object(
                group=group,
                version=version,
                plural=kind.lower() + 's',
                body=body
            )
        except ApiException as e:
            logger.error(f"Failed to create {kind}/{name}: {e}")
            raise

    def get_crossplane_resource(self, group, version, kind, name):
        """Get a Crossplane custom resource"""
        try:
            return self.k8s_client.get_cluster_custom_object(
                group=group,
                version=version,
                plural=kind.lower() + 's',
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def list_crossplane_resources(self, group, version, kind):
        """List all Crossplane resources of a kind"""
        try:
            response = self.k8s_client.list_cluster_custom_object(
                group=group,
                version=version,
                plural=kind.lower() + 's'
            )
            return response.get('items', [])
        except ApiException as e:
            logger.error(f"Failed to list {kind}: {e}")
            return []
'''

    # Insert crossplane methods before the orchestration methods
    content = re.sub(
        r'(    def orchestrate_provisioning\()',
        crossplane_methods + '\n\n    \\1',
        content
    )

    with open(filepath, 'w') as f:
        f.write(content)

    log_success(f"Updated {filepath}")

def update_multi_cloud_abstraction_js():
    """Update multi-cloud-abstraction.js to use Crossplane"""
    filepath = BASE_DIR / "core" / "multi-cloud-abstraction.js"

    if not filepath.exists():
        log_warn(f"File not found: {filepath}")
        return

    log_info(f"Updating {filepath}...")

    if DRY_RUN:
        log_info("[DRY RUN] Would update multi-cloud-abstraction.js")
        return

    backup_file(filepath)

    with open(filepath, 'r') as f:
        content = f.read()

    # Replace the entire class with Crossplane-based implementation
    new_content = '''const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

/**
 * Multi-Cloud Infrastructure Abstraction Layer (Crossplane-based)
 *
 * Unified API for managing infrastructure via Crossplane Kubernetes resources
 * instead of direct cloud provider SDKs.
 */

class CrossplaneAbstractionLayer {
  constructor(options = {}) {
    this.namespace = options.namespace || 'default';
    this.kubeconfig = options.kubeconfig || process.env.KUBECONFIG || '~/.kube/config';
  }

  // Execute kubectl command
  async kubectl(action, resourceType, name, body = null) {
    const cmd = ['kubectl', '-n', this.namespace];
    if (body) {
      cmd.push(action, '-f', '-');
      const { stdout, stderr } = await execAsync(cmd.join(' '), {
        input: JSON.stringify(body)
      });
      return JSON.parse(stdout);
    } else {
      cmd.push(action, resourceType, name, '-o', 'json');
      try {
        const { stdout } = await execAsync(cmd.join(' '));
        return JSON.parse(stdout);
      } catch (error) {
        if (error.code === 1) return null; // Not found
        throw error;
      }
    }
  }

  // Wait for resource to be ready
  async waitForReady(resourceType, name, timeout = 300) {
    const start = Date.now();
    while (Date.now() - start < timeout * 1000) {
      const resource = await this.kubectl('get', resourceType, name);
      if (resource) {
        const conditions = resource.status?.conditions || [];
        const readyCond = conditions.find(c => c.type === 'Ready');
        if (readyCond && readyCond.status === 'True') {
          return resource;
        }
      }
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    throw new Error(`Timeout waiting for ${resourceType}/${name} to be ready`);
  }

  // Unified VM Management via Crossplane Compositions
  async createVM(config) {
    // config should specify which provider composition to use
    // e.g., { composition: 'eksclusters.platform.aws.ecs.azure', ...spec }
    const group = config.apiVersion.split('/')[0];
    const version = config.apiVersion.split('/')[1];
    const kind = config.kind;
    const name = config.metadata.name;

    const resource = await this.kubectl('apply', 'custom_resource', name, config);
    const ready = await this.waitForReady(kind.toLowerCase() + 's', name);

    return {
      provider: ready.spec?.provider || 'unknown',
      id: ready.status?.atProvider?.id || ready.metadata?.uid,
      state: ready.status?.atProvider?.state || 'creating',
      k8sResource: ready
    };
  }

  async listVMs(providerName = null) {
    // List all compute resources across providers
    const eks = await this.kubectl('get', 'eksclusters.platform.aws.ecs.azure');
    const aks = await this.kubectl('get', 'kubernetesclusters.platform.azure');
    const gke = await this.kubectl('get', 'gkeclusters.platform.gcp');

    const results = {};

    if (!providerName || providerName === 'aws') {
      results.aws = eks.items?.map(r => ({
        id: r.status?.atProvider?.arn || r.metadata?.name,
        name: r.metadata?.name,
        state: r.status?.atProvider?.status || 'unknown',
        provider: 'aws'
      })) || [];
    }

    if (!providerName || providerName === 'azure') {
      results.azure = aks.items?.map(r => ({
        id: r.status?.atProvider?.id || r.metadata?.name,
        name: r.metadata?.name,
        state: r.status?.atProvider?.provisioningState || 'unknown',
        provider: 'azure'
      })) || [];
    }

    if (!providerName || providerName === 'gcp') {
      results.gcp = gke.items?.map(r => ({
        id: r.status?.atProvider?.id || r.metadata?.name,
        name: r.metadata?.name,
        state: r.status?.atProvider?.status || 'unknown',
        provider: 'gcp'
      })) || [];
    }

    return results;
  }

  async deleteVM(name, provider) {
    // Determine resource kind based on provider
    let resourceType;
    switch(provider) {
      case 'aws': resourceType = 'eksclusters.platform.aws.ecs.azure'; break;
      case 'azure': resourceType = 'kubernetesclusters.platform.azure'; break;
      case 'gcp': resourceType = 'gkeclusters.platform.gcp'; break;
      default: throw new Error(`Unknown provider: ${provider}`);
    }
    await this.kubectl('delete', resourceType, name);
    return { provider, name, action: 'deleted' };
  }

  // Storage Management
  async createBucket(config) {
    const body = {
      apiVersion: 'storage.aws/v1alpha1',
      kind: 'StorageBucketClaim',
      metadata: { name: config.name, namespace: this.namespace },
      spec: {
        bucketName: config.bucketName,
        region: config.region || 'us-west-2',
        versioningEnabled: config.versioningEnabled !== false,
        encryption: config.encryption || 'AES256',
        tags: config.tags || {}
      }
    };
    const resource = await this.kubectl('apply', 'custom_resource', config.name, body);
    const ready = await this.waitForReady('storagebucketclaims', config.name);
    return {
      provider: 'aws',
      name: config.name,
      bucketName: ready.status?.atProvider?.name,
      region: ready.status?.atProvider?.region
    };
  }

  async listBuckets(providerName = null) {
    const buckets = await this.kubectl('get', 'storagebucketclaims.storage.aws');
    const results = {};
    if (!providerName || providerName === 'aws') {
      results.aws = buckets.items?.map(r => ({
        name: r.metadata?.name,
        bucketName: r.status?.atProvider?.name,
        region: r.status?.atProvider?.region
      })) || [];
    }
    return results;
  }

  // Cost Estimation (read-only from crossplane or cloud APIs)
  async getCosts(providerName = null, period = '30d') {
    // Crossplane doesn't directly provide cost data
    // This would still call cloud billing APIs or use Cost Explorer
    // But uses Crossplane ProviderConfig credentials
    const costs = {};

    if (!providerName || providerName === 'aws') {
      costs.aws = { total: 0, currency: 'USD', note: 'Cost data requires custom integration' };
    }
    if (!providerName || providerName === 'azure') {
      costs.azure = { total: 0, currency: 'USD', note: 'Cost data requires custom integration' };
    }
    if (!providerName || providerName === 'gcp') {
      costs.gcp = { total: 0, currency: 'USD', note: 'Cost data requires custom integration' };
    }

    return costs;
  }

  // Network operations remain similar but use Crossplane resources
  async createNetwork(config) {
    const body = {
      apiVersion: 'networking.aws.crossplane.io/v1beta1',
      kind: 'VPC',
      metadata: { name: config.name, namespace: this.namespace },
      spec: {
        forProvider: {
          cidrBlock: config.cidrBlock || '10.0.0.0/16',
          tags: { Name: config.name, ManagedBy: 'crossplane' }
        }
      }
    };
    const resource = await this.kubectl('apply', 'custom_resource', config.name, body);
    const ready = await this.waitForReady('vpcs', config.name);
    return {
      provider: config.provider || 'aws',
      id: ready.status?.atProvider?.id,
      cidr: ready.status?.atProvider?.cidrBlock
    };
  }

  // Optimize resource placement using Crossplane ResourceClasses
  async optimizeResourcePlacement(resources) {
    // In Crossplane, this would query ResourceClasses and their allowed resources
    const recommendations = [];

    try {
      resourceClasses = await this.kubectl.get_cluster_custom_object(
        group='compute.crossplane.io',
        version='v1alpha1',
        plural='resourceclasses'
      );

      for (const resource of resources) {
        // Find appropriate ResourceClass based on requirements
        const bestClass = resourceClasses.items.find(rc =>
          rc.spec.allowedResources?.some(ar =>
            ar.name?.includes(resource.type)
          )
        );
        if (bestClass) {
          recommendations.push({
            resource: resource.id,
            recommendedClass: bestClass.metadata.name,
            reason: `Matches ResourceClass ${bestClass.metadata.name}`
          });
        }
      }
    } catch (e) {
      logger.warn(f"Could not query ResourceClasses: {e}");
    }

    return recommendations;
  }

  async createFailoverPlan(primaryProvider, secondaryProvider) {
    // In Crossplane, failover is typically handled via
    // - Compositions that create resources in multiple regions
    // - ExternalDNS for DNS-based failover
    // - Crossplane's replication capabilities
    return {
      primary: primaryProvider,
      secondary: secondaryProvider,
      note: 'Failover implemented via Crossplane Compositions and external tooling',
      resources: []
    };
  }

  // Utility: Get all managed resources across all providers
  async getAllManagedResources() {
    const allResources = [];

    // Query all known Crossplane resource kinds
    const kinds = [
      { kind: 'eksclusters', group: 'eks.aws.crossplane.io', version: 'v1beta1' },
      { kind: 'kubernetesclusters', group: 'platform.azure', version: 'v1beta1' },
      { kind: 'gkeclusters', group: 'platform.gcp', version: 'v1beta1' },
      { kind: 'rdsinstances', group: 'database.aws', version: 'v1beta1' },
      { kind: 'postgresqlinstances', group: 'database.azure', version: 'v1beta1' },
      { kind: 'cloudsqlpostgresql', group: 'database.gcp', version: 'v1beta1' },
      { kind: 'storagebuckets', group: 'storage.aws', version: 'v1alpha1' },
      // Add more as needed
    ];

    for (const { kind, group, version } of kinds) {
      try {
        resources = await this.kubectl('get', f'{kind}.{group}');
        if (resources?.items) {
          allResources.push(...resources.items.map(r => ({
            kind,
            name: r.metadata.name,
            namespace: r.metadata.namespace,
            status: r.status?.conditions?.[0]?.status || 'Unknown',
            provider: group.split('.')[0]
          })));
        }
      } catch (e) {
        // Resource kind may not be installed
        continue;
      }
    }

    return allResources;
  }
}

module.exports = CrossplaneAbstractionLayer;
'''

    with open(filepath, 'w') as f:
        f.write(new_content)

    log_success(f"Updated {filepath}")

def main():
    parser = argparse.ArgumentParser(description='Update multi-cloud skills for Crossplane')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--backup', action='store_true', help='Create backups (always true in this script)')
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = args.dry_run

    if DRY_RUN:
        log_warn("DRY RUN MODE - No files will be modified")

    log_info("Starting Crossplane skill migration...")

    # Update Python orchestrator
    update_multi_cloud_orchestrator_py()

    # Update JavaScript abstraction layer
    update_multi_cloud_abstraction_js()

    # Note: multi-cloud-scatter-gather.go requires more complex transformation
    log_info("Note: multi-cloud-scatter-gather.go needs manual update")
    log_info("  Replace per-cloud activities with Crossplane resource queries")

    log_success("Skill update complete!")
    log_info("Review the changes and test with sample claims before full migration")

if __name__ == '__main__':
    main()
