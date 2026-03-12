// Infrastructure Discovery Skill for GitOps Control Plane
// This skill enables AI agents to discover and catalog infrastructure resources
// across multiple cloud providers with durable execution through Temporal

// Define tool schema inline to avoid zod dependency issues
const infrastructureDiscoverySkill = {
  description: 'Discover and catalog infrastructure resources across multiple cloud providers',
  input: {
    cloudProviders: {
      type: 'array',
      items: { type: 'string' },
      description: 'Cloud providers to query (aws, azure, gcp)',
      required: true,
    },
    resourceTypes: {
      type: 'array',
      items: { type: 'string' },
      description: 'Types of resources to discover',
      required: true,
    },
    regions: {
      type: 'array',
      items: { type: 'string' },
      description: 'Specific regions to search',
      required: false,
    },
    tags: {
      type: 'object',
      description: 'Filter resources by tags',
      required: false,
    },
    includeCosts: {
      type: 'boolean',
      description: 'Include cost information',
      required: false,
      default: true,
    },
    deepDiscovery: {
      type: 'boolean',
      description: 'Perform deep discovery including nested resources',
      required: false,
      default: false,
    },
  },
};

export async function discoverInfrastructure(input: any) {
  console.log(`[INFRA-DISCOVERY] Starting infrastructure discovery across ${input.cloudProviders.join(', ')}`);
  
  const discoveryId = `discovery-${Date.now()}`;
  const results: DiscoveryResult[] = [];
  
  // Scatter: Query all cloud providers in parallel
  const discoveryPromises = input.cloudProviders.map(async (provider: string) => {
    try {
      console.log(`[INFRA-DISCOVERY] Querying ${provider} for resources`);
      
      const providerResult = await queryCloudProvider(provider, {
        resourceTypes: input.resourceTypes,
        regions: input.regions,
        tags: input.tags,
        includeCosts: input.includeCosts,
        deepDiscovery: input.deepDiscovery,
      });
      
      return {
        provider,
        status: 'success',
        data: providerResult,
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      console.error(`[INFRA-DISCOVERY] Failed to query ${provider}:`, error);
      return {
        provider,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      };
    }
  });
  
  const discoveryResults = await Promise.allSettled(discoveryPromises);
  
  // Gather: Aggregate results from all providers
  for (const result of discoveryResults) {
    if (result.status === 'fulfilled') {
      results.push(result.value);
    } else {
      console.error(`[INFRA-DISCOVERY] Discovery failed:`, result.reason);
    }
  }
  
  // Process and analyze discovered resources
  const analysis = analyzeDiscoveredResources(results);
  
  const output: DiscoveryOutput = {
    discoveryId,
    timestamp: new Date().toISOString(),
    providers: input.cloudProviders,
    resourceTypes: input.resourceTypes,
    results,
    analysis,
    summary: generateDiscoverySummary(results, analysis),
  };
  
  console.log(`[INFRA-DISCOVERY] Discovery completed. Found ${analysis.totalResources} resources across ${results.length} providers`);
  
  return output;
}

// Helper functions for cloud provider queries
async function queryCloudProvider(provider: string, params: any): Promise<ProviderResult> {
  switch (provider) {
    case 'aws':
      return queryAWSResources(params);
    case 'azure':
      return queryAzureResources(params);
    case 'gcp':
      return queryGCPResources(params);
    default:
      throw new Error(`Unsupported provider: ${provider}`);
  }
}

async function queryAWSResources(params: any): Promise<ProviderResult> {
  // Simulated AWS resource discovery
  console.log(`[INFRA-DISCOVERY] Querying AWS resources`);
  
  // In real implementation, this would use AWS SDK
  const resources = [
    {
      id: 'i-1234567890abcdef0',
      name: 'web-server-1',
      type: 'ec2-instance',
      region: 'us-east-1',
      status: 'running',
      cost: 45.67,
      tags: { Environment: 'production', Team: 'platform' },
      specifications: {
        instanceType: 't3.large',
        vcpu: 2,
        memory: 8,
        storage: 100,
      },
    },
    {
      id: 'vol-1234567890abcdef0',
      name: 'web-data-1',
      type: 'ebs-volume',
      region: 'us-east-1',
      status: 'in-use',
      cost: 12.34,
      tags: { Environment: 'production', Team: 'platform' },
      specifications: {
        size: 100,
        type: 'gp3',
        iops: 3000,
        throughput: 125,
      },
    },
  ];
  
  return {
    provider: 'aws',
    resources,
    metadata: {
      region: 'us-east-1',
      account: '123456789012',
      queriedAt: new Date().toISOString(),
      apiCalls: 3,
    },
  };
}

async function queryAzureResources(params: any): Promise<ProviderResult> {
  // Simulated Azure resource discovery
  console.log(`[INFRA-DISCOVERY] Querying Azure resources`);
  
  const resources = [
    {
      id: '/subscriptions/123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-1',
      name: 'app-server-1',
      type: 'virtual-machine',
      region: 'eastus',
      status: 'running',
      cost: 38.45,
      tags: { Environment: 'production', Department: 'engineering' },
      specifications: {
        vmSize: 'Standard_D2s_v3',
        vcpu: 2,
        memory: 8,
        osDisk: 128,
      },
    },
  ];
  
  return {
    provider: 'azure',
    resources,
    metadata: {
      region: 'eastus',
      subscription: '12345678-1234-1234-1234-123456789012',
      queriedAt: new Date().toISOString(),
      apiCalls: 2,
    },
  };
}

async function queryGCPResources(params: any): Promise<ProviderResult> {
  // Simulated GCP resource discovery
  console.log(`[INFRA-DISCOVERY] Querying GCP resources`);
  
  const resources = [
    {
      id: 'projects/my-project/zones/us-central1-a/instances/instance-1',
      name: 'database-1',
      type: 'compute-instance',
      region: 'us-central1',
      status: 'running',
      cost: 52.23,
      tags: { Environment: 'production', Project: 'platform' },
      specifications: {
        machineType: 'e2-medium',
        vcpu: 2,
        memory: 4,
        diskSize: 50,
      },
    },
  ];
  
  return {
    provider: 'gcp',
    resources,
    metadata: {
      region: 'us-central1',
      project: 'my-project',
      queriedAt: new Date().toISOString(),
      apiCalls: 2,
    },
  };
}

// Analysis functions
function analyzeDiscoveredResources(results: DiscoveryResult[]): DiscoveryAnalysis {
  const successfulResults = results.filter((r: any) => r.status === 'success');
  const totalResources = successfulResults.reduce((sum: number, r: any) => sum + r.data.resources.length, 0);
  const totalCost = successfulResults.reduce((sum: number, r: any) => sum + r.data.resources.reduce((costSum: number, resource: any) => costSum + (resource.cost || 0), 0), 0);
  
  // Resource type breakdown
  const resourceTypes = new Map<string, number>();
  const regions = new Map<string, number>();
  const statuses = new Map<string, number>();
  
  successfulResults.forEach((result: any) => {
    result.data.resources.forEach((resource: any) => {
      // Count by type
      const typeCount = resourceTypes.get(resource.type) || 0;
      resourceTypes.set(resource.type, typeCount + 1);
      
      // Count by region
      const regionCount = regions.get(resource.region) || 0;
      regions.set(resource.region, regionCount + 1);
      
      // Count by status
      const statusCount = statuses.get(resource.status) || 0;
      statuses.set(resource.status, statusCount + 1);
    });
  });
  
  // Identify issues
  const issues = identifyResourceIssues(successfulResults);
  
  // Find optimization opportunities
  const opportunities = findOptimizationOpportunities(successfulResults);
  
  return {
    totalResources,
    totalCost,
    totalProviders: successfulResults.length,
    resourceTypes: Object.fromEntries(resourceTypes),
    regions: Object.fromEntries(regions),
    statuses: Object.fromEntries(statuses),
    issues,
    opportunities,
  };
}

function identifyResourceIssues(results: any[]): ResourceIssue[] {
  const issues: ResourceIssue[] = [];
  
  results.forEach((result: any) => {
    result.data.resources.forEach((resource: any) => {
      // Check for common issues
      if (!resource.tags || Object.keys(resource.tags).length === 0) {
        issues.push({
          id: `missing-tags-${resource.id}`,
          resourceId: resource.id,
          provider: result.provider,
          type: 'missing-tags',
          severity: 'medium',
          description: `Resource ${resource.name} is missing required tags`,
          recommendation: 'Add Environment, Team, and Owner tags',
        });
      }
      
      if (resource.status === 'stopped' && resource.cost > 50) {
        issues.push({
          id: `expensive-stopped-${resource.id}`,
          resourceId: resource.id,
          provider: result.provider,
          type: 'expensive-stopped',
          severity: 'high',
          description: `Stopped resource ${resource.name} costs $${resource.cost}/month`,
          recommendation: 'Start or terminate the resource',
        });
      }
      
      if (resource.specifications) {
        const specs = resource.specifications as any;
        if (specs.memory && specs.memory > 32) {
          issues.push({
            id: `oversized-memory-${resource.id}`,
            resourceId: resource.id,
            provider: result.provider,
            type: 'oversized',
            severity: 'medium',
            description: `Resource ${resource.name} has oversized memory (${specs.memory}GB)`,
            recommendation: 'Consider right-sizing to reduce costs',
          });
        }
      }
    });
  });
  
  return issues;
}

function findOptimizationOpportunities(results: any[]): OptimizationOpportunity[] {
  const opportunities: OptimizationOpportunity[] = [];
  
  // Group similar resources for optimization
  const instanceGroups = new Map<string, any[]>();
  
  results.forEach((result: any) => {
    result.data.resources.forEach((resource: any) => {
      if (resource.type === 'ec2-instance' || resource.type === 'virtual-machine' || resource.type === 'compute-instance') {
        const key = `${resource.type}-${resource.specifications?.instanceType || resource.specifications?.vmSize || 'unknown'}`;
        const group = instanceGroups.get(key) || [];
        group.push({ ...resource, provider: result.provider });
        instanceGroups.set(key, group);
      }
    });
  });
  
  // Find consolidation opportunities
  instanceGroups.forEach((instances: any[], key: string) => {
    if (instances.length > 3) {
      const totalCost = instances.reduce((sum: number, instance: any) => sum + (instance.cost || 0), 0);
      
      opportunities.push({
        id: `consolidation-${key}`,
        type: 'consolidation',
        description: `Consolidate ${instances.length} ${key} instances`,
        potentialSavings: totalCost * 0.2, // 20% savings through consolidation
        affectedResources: instances.map((i: any) => i.id),
        recommendation: 'Use reserved instances or instance scheduling',
        effort: 'medium',
      });
    }
  });
  
  return opportunities;
}

function generateDiscoverySummary(results: DiscoveryResult[], analysis: DiscoveryAnalysis): string {
  const successfulProviders = results.filter((r: any) => r.status === 'success').length;
  const failedProviders = results.filter((r: any) => r.status === 'error').length;
  
  let summary = `Discovery completed across ${results.length} providers. `;
  summary += `Found ${analysis.totalResources} resources with total cost of $${analysis.totalCost.toFixed(2)}. `;
  
  if (analysis.issues.length > 0) {
    summary += `Identified ${analysis.issues.length} issues requiring attention. `;
  }
  
  if (analysis.opportunities.length > 0) {
    summary += `Found ${analysis.opportunities.length} optimization opportunities with potential savings of $${analysis.opportunities.reduce((sum: number, opp: any) => sum + opp.potentialSavings, 0).toFixed(2)}. `;
  }
  
  if (failedProviders > 0) {
    summary += `${failedProviders} providers failed to respond.`;
  }
  
  return summary;
}

// Type definitions
interface DiscoveryResult {
  provider: string;
  status: 'success' | 'error';
  data?: ProviderResult;
  error?: string;
  timestamp: string;
}

interface ProviderResult {
  provider: string;
  resources: DiscoveredResource[];
  metadata: {
    region?: string;
    account?: string;
    subscription?: string;
    project?: string;
    queriedAt: string;
    apiCalls: number;
  };
}

interface DiscoveredResource {
  id: string;
  name: string;
  type: string;
  region: string;
  status: string;
  cost?: number;
  tags?: Record<string, string>;
  specifications?: Record<string, any>;
}

interface DiscoveryOutput {
  discoveryId: string;
  timestamp: string;
  providers: string[];
  resourceTypes: string[];
  results: DiscoveryResult[];
  analysis: DiscoveryAnalysis;
  summary: string;
}

interface DiscoveryAnalysis {
  totalResources: number;
  totalCost: number;
  totalProviders: number;
  resourceTypes: Record<string, number>;
  regions: Record<string, number>;
  statuses: Record<string, number>;
  issues: ResourceIssue[];
  opportunities: OptimizationOpportunity[];
}

interface ResourceIssue {
  id: string;
  resourceId: string;
  provider: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  recommendation: string;
}

interface OptimizationOpportunity {
  id: string;
  type: string;
  description: string;
  potentialSavings: number;
  affectedResources: string[];
  recommendation: string;
  effort: 'low' | 'medium' | 'high';
}

export { infrastructureDiscoverySkill };
