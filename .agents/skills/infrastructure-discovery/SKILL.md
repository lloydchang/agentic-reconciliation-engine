---
name: infrastructure-discovery
description: Discover and visualize infrastructure resources with interactive HTML output. Use when exploring new environments, understanding resource relationships, or creating infrastructure documentation.
argument-hint: "[resourceType] [environment] [outputFormat]"
allowed-tools: 
  - "Bash(python *)"
---

# Infrastructure Discovery Skill

Advanced infrastructure discovery with interactive visual output. Creates comprehensive HTML visualizations of your infrastructure with collapsible trees, resource metrics, and relationship mapping.

## Usage
```bash
/infrastructure-discovery all all html
/infrastructure-discovery vm production interactive
/infrastructure-discovery database all detailed
```

## Visual Output Features

### Interactive HTML Dashboard
- **Collapsible Tree View**: Expand/collapse infrastructure hierarchies
- **Resource Metrics**: Real-time performance and utilization data
- **Cost Analysis**: Monthly cost breakdown by resource type
- **Relationship Mapping**: Visual connections between resources
- **Status Indicators**: Color-coded health and availability status

### Resource Classification
- **Compute**: VMs, containers, serverless functions
- **Storage**: Block storage, object storage, databases
- **Network**: Load balancers, VPCs, CDN, DNS
- **Services**: Monitoring, security, analytics
- **Applications**: Web apps, APIs, microservices

## Discovery Process

### 1. Resource Enumeration
```python
# Multi-cloud resource discovery
def discover_resources(resource_type="all", environment="all"):
    resources = []
    
    # AWS resources
    if has_aws_credentials():
        resources.extend(discover_aws_resources(resource_type, environment))
    
    # Azure resources
    if has_azure_credentials():
        resources.extend(discover_azure_resources(resource_type, environment))
    
    # GCP resources
    if has_gcp_credentials():
        resources.extend(discover_gcp_resources(resource_type, environment))
    
    # Local infrastructure
    resources.extend(discover_local_resources(resource_type, environment))
    
    return enrich_with_metadata(resources)
```

### 2. Relationship Mapping
```python
# Build resource dependency graph
def build_relationship_graph(resources):
    graph = {}
    
    for resource in resources:
        dependencies = find_dependencies(resource)
        dependents = find_dependents(resource)
        
        graph[resource.id] = {
            'resource': resource,
            'dependencies': dependencies,
            'dependents': dependents,
            'relationships': calculate_relationship_strength(dependencies, dependents)
        }
    
    return graph
```

### 3. Metrics Collection
```python
# Real-time metrics gathering
def collect_resource_metrics(resources):
    metrics = {}
    
    for resource in resources:
        metrics[resource.id] = {
            'cpu_utilization': get_cpu_metric(resource),
            'memory_utilization': get_memory_metric(resource),
            'disk_utilization': get_disk_metric(resource),
            'network_throughput': get_network_metric(resource),
            'cost_per_month': get_cost_metric(resource),
            'health_status': get_health_status(resource),
            'last_updated': datetime.now()
        }
    
    return metrics
```

## Visualization Components

### 1. Infrastructure Tree View
```javascript
// Interactive tree component
function renderInfrastructureTree(data, container) {
    const tree = new TreeView(container, {
        data: data,
        expandable: true,
        searchable: true,
        filterable: true,
        nodeRenderer: function(node) {
            return `
                <div class="tree-node">
                    <span class="node-icon">${getNodeIcon(node.type)}</span>
                    <span class="node-name">${node.name}</span>
                    <span class="node-status status-${node.status}">${node.status}</span>
                    <span class="node-cost">$${node.cost}/mo</span>
                </div>
            `;
        }
    });
}
```

### 2. Resource Metrics Dashboard
```javascript
// Metrics visualization
function renderMetricsDashboard(metrics, container) {
    const dashboard = new Dashboard(container);
    
    // CPU utilization chart
    dashboard.addChart('cpu', {
        type: 'gauge',
        title: 'CPU Utilization',
        value: metrics.avg_cpu_utilization,
        max: 100,
        unit: '%'
    });
    
    // Cost breakdown chart
    dashboard.addChart('costs', {
        type: 'pie',
        title: 'Monthly Cost Breakdown',
        data: metrics.cost_by_type
    });
    
    // Health status overview
    dashboard.addChart('health', {
        type: 'status',
        title: 'Resource Health',
        data: metrics.health_distribution
    });
}
```

### 3. Relationship Graph
```javascript
// Network graph visualization
function renderRelationshipGraph(graph, container) {
    const networkGraph = new NetworkGraph(container, {
        nodes: graph.nodes,
        edges: graph.edges,
        layout: 'force-directed',
        nodeRenderer: function(node) {
            return {
                label: node.name,
                color: getNodeColor(node.type),
                size: getNodeSize(node.importance),
                shape: getNodeShape(node.category)
            };
        },
        edgeRenderer: function(edge) {
            return {
                width: edge.strength,
                color: getEdgeColor(edge.type),
                style: getEdgeStyle(edge.type)
            };
        }
    });
}
```

## Output Formats

### Interactive HTML (Default)
- Full-featured interactive dashboard
- Real-time updates via WebSocket
- Exportable to PDF/PNG
- Responsive design for all devices

### Static HTML
- Lightweight visualization
- No external dependencies
- Fast loading for large infrastructures
- Printable format

### JSON Export
- Machine-readable format
- API integration ready
- Data analysis compatible
- Import into other tools

### CSV Export
- Spreadsheet compatible
- Financial analysis ready
- Simple data structure
- Easy data manipulation

## Advanced Features

### 1. Real-time Monitoring
```python
# Live monitoring integration
class InfrastructureMonitor:
    def __init__(self):
        self.websocket_server = WebSocketServer()
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
    
    def start_monitoring(self, resources):
        for resource in resources:
            self.metrics_collector.monitor(resource, self.on_metric_update)
        
        self.websocket_server.start()
    
    def on_metric_update(self, resource_id, metrics):
        # Broadcast to connected clients
        self.websocket_server.broadcast({
            'type': 'metric_update',
            'resource_id': resource_id,
            'metrics': metrics
        })
```

### 2. Automated Discovery
```python
# Scheduled discovery automation
class DiscoveryScheduler:
    def __init__(self):
        self.schedule = {}
        self.discovery_engine = DiscoveryEngine()
    
    def schedule_discovery(self, frequency, resource_type, environment):
        job_id = f"{resource_type}_{environment}_{frequency}"
        
        self.schedule[job_id] = {
            'frequency': frequency,
            'resource_type': resource_type,
            'environment': environment,
            'last_run': None,
            'next_run': datetime.now()
        }
    
    def run_scheduled_discoveries(self):
        for job_id, job in self.schedule.items():
            if datetime.now() >= job['next_run']:
                results = self.discovery_engine.discover(
                    job['resource_type'], 
                    job['environment']
                )
                
                self.save_discovery_results(job_id, results)
                job['last_run'] = datetime.now()
                job['next_run'] = self.calculate_next_run(job['frequency'])
```

### 3. Cost Analysis Integration
```python
# Cost analysis integration
def analyze_infrastructure_costs(resources):
    cost_analysis = {
        'total_monthly_cost': 0,
        'cost_by_type': {},
        'cost_by_environment': {},
        'cost_trends': {},
        'optimization_opportunities': []
    }
    
    for resource in resources:
        cost = get_monthly_cost(resource)
        cost_analysis['total_monthly_cost'] += cost
        
        # Categorize costs
        resource_type = resource.type
        environment = resource.environment
        
        cost_analysis['cost_by_type'][resource_type] = \
            cost_analysis['cost_by_type'].get(resource_type, 0) + cost
        
        cost_analysis['cost_by_environment'][environment] = \
            cost_analysis['cost_by_environment'].get(environment, 0) + cost
        
        # Identify optimization opportunities
        if is_underutilized(resource):
            cost_analysis['optimization_opportunities'].append({
                'resource_id': resource.id,
                'type': 'rightsize',
                'potential_savings': cost * 0.4,
                'confidence': 0.8
            })
    
    return cost_analysis
```

## Integration with Temporal AI Agents

### API Endpoints
- `discover_resources`: Start infrastructure discovery workflow
- `get_resource_topology`: Get resource relationship graph
- `get_resource_metrics`: Get real-time metrics
- `export_visualization`: Export visualization in various formats

### Workflow Integration
```python
# Discovery workflow orchestration
class DiscoveryWorkflow:
    def execute(self, parameters):
        # 1. Resource discovery
        resources = self.discover_resources(
            parameters.get('resource_type', 'all'),
            parameters.get('environment', 'all')
        )
        
        # 2. Relationship mapping
        relationships = self.build_relationship_graph(resources)
        
        # 3. Metrics collection
        metrics = self.collect_resource_metrics(resources)
        
        # 4. Visualization generation
        visualization = self.generate_visualization(
            resources, relationships, metrics,
            parameters.get('output_format', 'html')
        )
        
        # 5. Cost analysis
        cost_analysis = self.analyze_infrastructure_costs(resources)
        
        return {
            'resources': resources,
            'relationships': relationships,
            'metrics': metrics,
            'visualization': visualization,
            'cost_analysis': cost_analysis
        }
```

## Security & Privacy

### Data Protection
- Encrypt sensitive configuration data
- Anonymize resource names in exports
- Secure WebSocket connections
- Role-based access control

### Compliance Support
- GDPR compliance for data discovery
- SOC2 audit trail maintenance
- HIPAA data classification support
- Industry-specific compliance checks

## Performance Optimization

### Large Infrastructure Support
- Lazy loading for resource trees
- Virtual scrolling for large lists
- Pagination for resource grids
- Progressive image loading

### Caching Strategy
- Redis-based metrics caching
- Browser-side visualization caching
- CDN for static assets
- Incremental updates only

## Supporting Files

- [scripts/infrastructure-scanner.py](scripts/infrastructure-scanner.py): Multi-cloud discovery engine
- [templates/infrastructure-dashboard.html](templates/infrastructure-dashboard.html): Interactive dashboard template
- [assets/resource-icons.json](assets/resource-icons.json): Resource type icon mappings
- [scripts/visualization-generator.py](scripts/visualization-generator.py): HTML visualization generator

## Examples

### Full Infrastructure Discovery
```bash
/infrastructure-discovery all all html
```

### Production Environment Only
```bash
/infrastructure-discovery all production interactive
```

### Database Resources Analysis
```bash
/infrastructure-discovery database all detailed
```

## Related Skills

- `/compliance-check`: Validate discovered resources against compliance standards
- `/security-analysis`: Analyze security posture of discovered infrastructure
- `/cost-optimization`: Optimize costs of discovered resources
- `/workflow-management`: Orchestrate discovery workflows

## Best Practices

1. **Credential Management**: Use secure credential storage for multi-cloud discovery
2. **Permission Scoping**: Limit discovery to necessary resources only
3. **Regular Updates**: Schedule periodic discovery to keep data current
4. **Performance Monitoring**: Monitor discovery performance for large infrastructures
5. **Data Retention**: Implement appropriate data retention policies
6. **Access Control**: Implement proper access controls for sensitive infrastructure data
7. **Documentation**: Maintain detailed documentation of discovered resources
8. **Change Detection**: Implement change detection and alerting for infrastructure changes
