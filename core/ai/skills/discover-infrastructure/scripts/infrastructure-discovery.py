#!/usr/bin/env python3
"""
Infrastructure Discovery Scanner
Multi-cloud infrastructure discovery and visualization generator
"""

import json
import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import subprocess
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Resource:
    id: str
    name: str
    type: str
    environment: str
    region: str
    status: str
    cost_per_month: float
    utilization: Dict[str, float]
    dependencies: List[str]
    metadata: Dict[str, str]

@dataclass
class Relationship:
    source_id: str
    target_id: str
    type: str
    strength: float
    bidirectional: bool

class InfrastructureScanner:
    def __init__(self, output_dir: str = "/tmp/infrastructure-discovery"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.resources: List[Resource] = []
        self.relationships: List[Relationship] = []
        
    def scan_infrastructure(self, resource_type: str = "all", environment: str = "all") -> None:
        """Scan infrastructure resources"""
        logger.info(f"Scanning infrastructure: type={resource_type}, environment={environment}")
        
        # Discover resources from different sources
        self.resources = self._discover_resources(resource_type, environment)
        
        # Build relationships
        self.relationships = self._build_relationships()
        
        # Enrich with metrics
        self._enrich_with_metrics()
        
        logger.info(f"Discovered {len(self.resources)} resources and {len(self.relationships)} relationships")
    
    def _discover_resources(self, resource_type: str, environment: str) -> List[Resource]:
        """Discover resources from various sources"""
        resources = []
        
        # Sample data for demonstration
        # In real implementation, this would connect to cloud APIs
        sample_resources = [
            Resource(
                id="vm-web-prod-001",
                name="Web Server Production 001",
                type="compute",
                environment="production",
                region="us-east-1",
                status="running",
                cost_per_month=150.0,
                utilization={"cpu": 0.25, "memory": 0.40, "disk": 0.60},
                dependencies=["lb-web-prod", "db-web-prod"],
                metadata={"instance_type": "t3.medium", "os": "ubuntu", "team": "web"}
            ),
            Resource(
                id="vm-web-prod-002",
                name="Web Server Production 002",
                type="compute",
                environment="production",
                region="us-east-1",
                status="running",
                cost_per_month=150.0,
                utilization={"cpu": 0.30, "memory": 0.45, "disk": 0.55},
                dependencies=["lb-web-prod", "db-web-prod"],
                metadata={"instance_type": "t3.medium", "os": "ubuntu", "team": "web"}
            ),
            Resource(
                id="lb-web-prod",
                name="Web Load Balancer",
                type="network",
                environment="production",
                region="us-east-1",
                status="active",
                cost_per_month=25.0,
                utilization={"connections": 0.60, "bandwidth": 0.40},
                dependencies=["vm-web-prod-001", "vm-web-prod-002"],
                metadata={"type": "application", "ssl": True, "team": "web"}
            ),
            Resource(
                id="db-web-prod",
                name="Web Database",
                type="database",
                environment="production",
                region="us-east-1",
                status="available",
                cost_per_month=300.0,
                utilization={"cpu": 0.85, "memory": 0.90, "storage": 0.75},
                dependencies=["storage-backup-prod"],
                metadata={"engine": "postgresql", "version": "13", "team": "database"}
            ),
            Resource(
                id="storage-backup-prod",
                name="Backup Storage",
                type="storage",
                environment="production",
                region="us-east-1",
                status="available",
                cost_per_month=80.0,
                utilization={"storage": 0.35, "iops": 0.20},
                dependencies=[],
                metadata={"type": "s3", "size_gb": 1000, "team": "backup"}
            ),
            Resource(
                id="vm-dev-001",
                name="Development Server 001",
                type="compute",
                environment="development",
                region="us-west-2",
                status="stopped",
                cost_per_month=75.0,
                utilization={"cpu": 0.0, "memory": 0.0, "disk": 0.10},
                dependencies=[],
                metadata={"instance_type": "t3.small", "os": "ubuntu", "team": "dev"}
            )
        ]
        
        # Filter by resource type and environment
        if resource_type != "all":
            sample_resources = [r for r in sample_resources if r.type == resource_type]
        
        if environment != "all":
            sample_resources = [r for r in sample_resources if r.environment == environment]
        
        return sample_resources
    
    def _build_relationships(self) -> List[Relationship]:
        """Build resource relationships"""
        relationships = []
        
        resource_map = {r.id: r for r in self.resources}
        
        for resource in self.resources:
            for dep_id in resource.dependencies:
                if dep_id in resource_map:
                    relationships.append(Relationship(
                        source_id=resource.id,
                        target_id=dep_id,
                        type="dependency",
                        strength=0.8,
                        bidirectional=False
                    ))
        
        return relationships
    
    def _enrich_with_metrics(self) -> None:
        """Add additional metrics to resources"""
        for resource in self.resources:
            # Calculate health score based on utilization
            cpu_util = resource.utilization.get("cpu", 0)
            memory_util = resource.utilization.get("memory", 0)
            
            if resource.status == "running":
                if 0.3 <= cpu_util <= 0.8 and 0.3 <= memory_util <= 0.8:
                    resource.metadata["health_score"] = "good"
                elif cpu_util > 0.9 or memory_util > 0.9:
                    resource.metadata["health_score"] = "warning"
                elif cpu_util < 0.1 and memory_util < 0.1:
                    resource.metadata["health_score"] = "underutilized"
                else:
                    resource.metadata["health_score"] = "fair"
            else:
                resource.metadata["health_score"] = resource.status
            
            # Add cost efficiency score
            if resource.type == "compute" and resource.status == "running":
                avg_util = (cpu_util + memory_util) / 2
                if avg_util < 0.3:
                    resource.metadata["cost_efficiency"] = "poor"
                elif avg_util < 0.7:
                    resource.metadata["cost_efficiency"] = "fair"
                else:
                    resource.metadata["cost_efficiency"] = "good"
    
    def generate_visualization(self, output_format: str = "html") -> str:
        """Generate visualization output"""
        logger.info(f"Generating {output_format} visualization")
        
        if output_format == "html":
            return self._generate_html_visualization()
        elif output_format == "json":
            return self._generate_json_export()
        elif output_format == "csv":
            return self._generate_csv_export()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_html_visualization(self) -> str:
        """Generate interactive HTML visualization"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"infrastructure-dashboard-{timestamp}.html"
        
        # Calculate summary statistics
        total_cost = sum(r.cost_per_month for r in self.resources)
        cost_by_type = {}
        status_distribution = {}
        environment_distribution = {}
        
        for resource in self.resources:
            cost_by_type[resource.type] = cost_by_type.get(resource.type, 0) + resource.cost_per_month
            status_distribution[resource.status] = status_distribution.get(resource.status, 0) + 1
            environment_distribution[resource.environment] = environment_distribution.get(resource.environment, 0) + 1
        
        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Infrastructure Discovery Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #333; }}
        .container {{ display: flex; height: 100vh; }}
        .sidebar {{ width: 320px; background: #2c3e50; color: white; padding: 20px; overflow-y: auto; }}
        .main {{ flex: 1; padding: 20px; overflow-y: auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
        .stat-label {{ color: #7f8c8d; font-size: 14px; margin-top: 5px; }}
        .section {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ font-size: 18px; margin-bottom: 15px; color: #2c3e50; }}
        .resource-list {{ list-style: none; }}
        .resource-item {{ padding: 15px; border-left: 4px solid #3498db; margin-bottom: 10px; background: #f8f9fa; border-radius: 4px; }}
        .resource-item.compute {{ border-left-color: #3498db; }}
        .resource-item.database {{ border-left-color: #e74c3c; }}
        .resource-item.storage {{ border-left-color: #f39c12; }}
        .resource-item.network {{ border-left-color: #27ae60; }}
        .resource-header {{ display: flex; justify-content: between; align-items: center; margin-bottom: 8px; }}
        .resource-name {{ font-weight: bold; font-size: 16px; }}
        .resource-status {{ padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .status-running {{ background: #d4edda; color: #155724; }}
        .status-stopped {{ background: #f8d7da; color: #721c24; }}
        .status-available {{ background: #d1ecf1; color: #0c5460; }}
        .resource-details {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 14px; }}
        .detail-item {{ display: flex; justify-content: space-between; }}
        .detail-label {{ color: #7f8c8d; }}
        .detail-value {{ font-weight: 500; }}
        .health-good {{ color: #27ae60; }}
        .health-warning {{ color: #f39c12; }}
        .health-underutilized {{ color: #e67e22; }}
        .health-fair {{ color: #3498db; }}
        .sidebar h3 {{ font-size: 16px; margin-bottom: 15px; color: #ecf0f1; }}
        .sidebar-item {{ margin-bottom: 15px; }}
        .sidebar-label {{ font-size: 12px; color: #bdc3c7; margin-bottom: 5px; }}
        .sidebar-value {{ font-size: 18px; font-weight: bold; }}
        .cost-breakdown {{ margin-top: 20px; }}
        .cost-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #34495e; }}
        .cost-type {{ color: #ecf0f1; }}
        .cost-amount {{ font-weight: bold; }}
        .utilization-bar {{ height: 8px; background: #ecf0f1; border-radius: 4px; margin-top: 5px; overflow: hidden; }}
        .utilization-fill {{ height: 100%; background: linear-gradient(90deg, #27ae60, #f39c12, #e74c3c); transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h3>📊 Infrastructure Overview</h3>
            
            <div class="sidebar-item">
                <div class="sidebar-label">Total Resources</div>
                <div class="sidebar-value">{len(self.resources)}</div>
            </div>
            
            <div class="sidebar-item">
                <div class="sidebar-label">Monthly Cost</div>
                <div class="sidebar-value">${total_cost:,.2f}</div>
            </div>
            
            <div class="sidebar-item">
                <div class="sidebar-label">Relationships</div>
                <div class="sidebar-value">{len(self.relationships)}</div>
            </div>
            
            <div class="sidebar-item">
                <div class="sidebar-label">Last Updated</div>
                <div class="sidebar-value" style="font-size: 14px;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            </div>
            
            <h3>💰 Cost Breakdown</h3>
            <div class="cost-breakdown">"""
        
        for resource_type, cost in sorted(cost_by_type.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            html_content += f"""
                <div class="cost-item">
                    <span class="cost-type">{resource_type.title()}</span>
                    <span class="cost-amount">${cost:,.2f} ({percentage:.1f}%)</span>
                </div>"""
        
        html_content += f"""
            </div>
            
            <h3>🌍 Environment Distribution</h3>
            <div class="sidebar-item">"""
        
        for env, count in environment_distribution.items():
            html_content += f"""
                <div class="sidebar-item">
                    <div class="sidebar-label">{env.title()}</div>
                    <div class="sidebar-value">{count} resources</div>
                </div>"""
        
        html_content += f"""
            </div>
        </div>
        
        <div class="main">
            <div class="header">
                <h1>🚀 Infrastructure Discovery Dashboard</h1>
                <p>Comprehensive view of your infrastructure resources and their relationships</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(self.resources)}</div>
                    <div class="stat-label">Total Resources</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${total_cost:,.2f}</div>
                    <div class="stat-label">Monthly Cost</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len([r for r in self.resources if r.status == 'running'])}</div>
                    <div class="stat-label">Running Resources</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(self.relationships)}</div>
                    <div class="stat-label">Dependencies</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📦 Resources</h2>
                <ul class="resource-list">"""
        
        for resource in self.resources:
            health_class = f"health-{resource.metadata.get('health_score', 'unknown')}"
            status_class = f"status-{resource.status}"
            
            # Calculate utilization percentage
            cpu_util = resource.utilization.get('cpu', 0) * 100
            memory_util = resource.utilization.get('memory', 0) * 100
            
            html_content += f"""
                <li class="resource-item {resource.type}">
                    <div class="resource-header">
                        <span class="resource-name">{resource.name}</span>
                        <span class="resource-status {status_class}">{resource.status.upper()}</span>
                    </div>
                    <div class="resource-details">
                        <div class="detail-item">
                            <span class="detail-label">Type:</span>
                            <span class="detail-value">{resource.type.title()}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Environment:</span>
                            <span class="detail-value">{resource.environment.title()}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Cost/Month:</span>
                            <span class="detail-value">${resource.cost_per_month:.2f}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Health:</span>
                            <span class="detail-value {health_class}">{resource.metadata.get('health_score', 'unknown').title()}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">CPU:</span>
                            <span class="detail-value">{cpu_util:.1f}%</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Memory:</span>
                            <span class="detail-value">{memory_util:.1f}%</span>
                        </div>
                    </div>
                    <div class="utilization-bar">
                        <div class="utilization-fill" style="width: {cpu_util}%"></div>
                    </div>
                </li>"""
        
        html_content += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>🔗 Dependencies</h2>
                <ul class="resource-list">"""
        
        for relationship in self.relationships:
            source_name = next((r.name for r in self.resources if r.id == relationship.source_id), relationship.source_id)
            target_name = next((r.name for r in self.resources if r.id == relationship.target_id), relationship.target_id)
            
            html_content += f"""
                <li class="resource-item">
                    <div class="resource-header">
                        <span class="resource-name">{source_name} → {target_name}</span>
                        <span class="resource-status status-available">{relationship.type.title()}</span>
                    </div>
                    <div class="resource-details">
                        <div class="detail-item">
                            <span class="detail-label">Strength:</span>
                            <span class="detail-value">{relationship.strength:.1f}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Direction:</span>
                            <span class="detail-value">{'Bidirectional' if relationship.bidirectional else 'Unidirectional'}</span>
                        </div>
                    </div>
                </li>"""
        
        html_content += f"""
                </ul>
            </div>
        </div>
    </div>
    
    <script>
        // Add interactivity
        document.addEventListener('DOMContentLoaded', function() {{
            // Auto-refresh every 30 seconds
            setTimeout(function() {{
                location.reload();
            }}, 30000);
            
            // Add click handlers for resource items
            const resourceItems = document.querySelectorAll('.resource-item');
            resourceItems.forEach(item => {{
                item.addEventListener('click', function() {{
                    this.style.backgroundColor = this.style.backgroundColor === 'rgb(236, 240, 241)' ? '' : '#ecf0f1';
                }});
            }});
        }});
    </script>
</body>
</html>"""
        
        # Write HTML file
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML visualization saved to: {output_file}")
        
        # Open in browser
        try:
            webbrowser.open(f'file://{output_file.absolute()}')
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        return str(output_file)
    
    def _generate_json_export(self) -> str:
        """Generate JSON export"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"infrastructure-export-{timestamp}.json"
        
        export_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_resources": len(self.resources),
                "total_relationships": len(self.relationships),
                "total_monthly_cost": sum(r.cost_per_month for r in self.resources)
            },
            "resources": [asdict(resource) for resource in self.resources],
            "relationships": [asdict(relationship) for relationship in self.relationships]
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"JSON export saved to: {output_file}")
        return str(output_file)
    
    def _generate_csv_export(self) -> str:
        """Generate CSV export"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"infrastructure-export-{timestamp}.csv"
        
        import csv
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'ID', 'Name', 'Type', 'Environment', 'Region', 'Status',
                'Cost_Per_Month', 'CPU_Utilization', 'Memory_Utilization',
                'Disk_Utilization', 'Health_Score', 'Cost_Efficiency'
            ])
            
            # Write resource data
            for resource in self.resources:
                writer.writerow([
                    resource.id,
                    resource.name,
                    resource.type,
                    resource.environment,
                    resource.region,
                    resource.status,
                    resource.cost_per_month,
                    resource.utilization.get('cpu', 0),
                    resource.utilization.get('memory', 0),
                    resource.utilization.get('disk', 0),
                    resource.metadata.get('health_score', ''),
                    resource.metadata.get('cost_efficiency', '')
                ])
        
        logger.info(f"CSV export saved to: {output_file}")
        return str(output_file)

def main():
    parser = argparse.ArgumentParser(description="Infrastructure Discovery Scanner")
    parser.add_argument("resource_type", nargs="?", default="all",
                       help="Resource type to scan (default: all)")
    parser.add_argument("environment", nargs="?", default="all",
                       help="Environment to scan (default: all)")
    parser.add_argument("--format", choices=["html", "json", "csv"],
                       default="html", help="Output format (default: html)")
    parser.add_argument("--output", "-o",
                       help="Output directory (default: /tmp/infrastructure-discovery)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize scanner
    scanner = InfrastructureScanner(output_dir=args.output or "/tmp/infrastructure-discovery")
    
    # Scan infrastructure
    scanner.scan_infrastructure(args.resource_type, args.environment)
    
    # Generate visualization
    output_file = scanner.generate_visualization(args.format)
    
    print(f"\nInfrastructure discovery completed!")
    print(f"Resources discovered: {len(scanner.resources)}")
    print(f"Relationships found: {len(scanner.relationships)}")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()
