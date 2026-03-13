#!/usr/bin/env python3
"""
Advanced Cost Analyzer for Cloud Infrastructure
Performs comprehensive cost analysis and optimization recommendations
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass, asdict
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Resource:
    id: str
    type: str
    name: str
    region: str
    current_cost: float
    usage_metrics: Dict[str, float]
    tags: Dict[str, str]

@dataclass
class OptimizationRecommendation:
    resource_id: str
    type: str
    description: str
    current_cost: float
    projected_cost: float
    monthly_savings: float
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high, critical
    roi_percentage: float
    time_to_implement: int  # days

class CostAnalyzer:
    def __init__(self, api_base: str = "http://localhost:8081", api_key: str = ""):
        self.api_base = api_base
        self.api_key = api_key
        self.resources: List[Resource] = []
        self.optimizations: List[OptimizationRecommendation] = []
        
    def load_resources(self, target_resource: str = "all-resources") -> None:
        """Load resource data from API or local files"""
        logger.info(f"Loading resources for: {target_resource}")
        
        try:
            # Try to load from API first
            if target_resource == "all-resources":
                resources_data = self._fetch_all_resources()
            else:
                resources_data = self._fetch_resource(target_resource)
            
            self.resources = [self._parse_resource(r) for r in resources_data]
            logger.info(f"Loaded {len(self.resources)} resources")
            
        except Exception as e:
            logger.warning(f"Failed to load from API: {e}")
            # Fallback to sample data for demonstration
            self._load_sample_data()
    
    def _fetch_all_resources(self) -> List[Dict]:
        """Fetch all resources from API"""
        import requests
        
        response = requests.get(
            f"{self.api_base}/api/v1/resources",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return response.json()
    
    def _fetch_resource(self, resource_id: str) -> List[Dict]:
        """Fetch specific resource from API"""
        import requests
        
        response = requests.get(
            f"{self.api_base}/api/v1/resources/{resource_id}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return [response.json()]
    
    def _parse_resource(self, resource_data: Dict) -> Resource:
        """Parse resource data from API response"""
        return Resource(
            id=resource_data.get('id', ''),
            type=resource_data.get('type', ''),
            name=resource_data.get('name', ''),
            region=resource_data.get('region', ''),
            current_cost=resource_data.get('cost', 0.0),
            usage_metrics=resource_data.get('usage_metrics', {}),
            tags=resource_data.get('tags', {})
        )
    
    def _load_sample_data(self) -> None:
        """Load sample data for demonstration"""
        logger.info("Loading sample data for demonstration")
        
        sample_resources = [
            Resource(
                id="vm-web-001",
                type="compute",
                name="Web Server 001",
                region="us-east-1",
                current_cost=150.0,
                usage_metrics={
                    "cpu_utilization": 0.25,
                    "memory_utilization": 0.40,
                    "disk_utilization": 0.60
                },
                tags={"environment": "production", "team": "web"}
            ),
            Resource(
                id="vm-db-001",
                type="compute",
                name="Database Server 001",
                region="us-east-1",
                current_cost=300.0,
                usage_metrics={
                    "cpu_utilization": 0.85,
                    "memory_utilization": 0.90,
                    "disk_utilization": 0.75
                },
                tags={"environment": "production", "team": "database"}
            ),
            Resource(
                id="storage-app-001",
                type="storage",
                name="Application Storage",
                region="us-east-1",
                current_cost=80.0,
                usage_metrics={
                    "storage_utilization": 0.35,
                    "iops_utilization": 0.20
                },
                tags={"environment": "production", "team": "application"}
            )
        ]
        
        self.resources = sample_resources
    
    def analyze_compute_optimization(self) -> List[OptimizationRecommendation]:
        """Analyze compute resources for optimization opportunities"""
        logger.info("Analyzing compute optimization opportunities")
        
        recommendations = []
        
        for resource in self.resources:
            if resource.type != "compute":
                continue
            
            cpu_util = resource.usage_metrics.get("cpu_utilization", 0)
            memory_util = resource.usage_metrics.get("memory_utilization", 0)
            
            # Check for underutilization
            if cpu_util < 0.3 and memory_util < 0.5:
                # Recommend downsizing
                savings = resource.current_cost * 0.4  # 40% savings estimate
                recommendations.append(OptimizationRecommendation(
                    resource_id=resource.id,
                    type="rightsize_down",
                    description=f"Downsize {resource.name} - Low utilization ({cpu_util:.1%} CPU, {memory_util:.1%} Memory)",
                    current_cost=resource.current_cost,
                    projected_cost=resource.current_cost * 0.6,
                    monthly_savings=savings,
                    implementation_effort="low",
                    risk_level="low",
                    roi_percentage=400.0,  # 400% ROI in first year
                    time_to_implement=3
                ))
            
            elif cpu_util > 0.9 or memory_util > 0.9:
                # Recommend upsizing for performance
                recommendations.append(OptimizationRecommendation(
                    resource_id=resource.id,
                    type="rightsize_up",
                    description=f"Upsize {resource.name} - High utilization ({cpu_util:.1%} CPU, {memory_util:.1%} Memory)",
                    current_cost=resource.current_cost,
                    projected_cost=resource.current_cost * 1.5,
                    monthly_savings=0.0,  # No direct savings, performance improvement
                    implementation_effort="medium",
                    risk_level="low",
                    roi_percentage=0.0,
                    time_to_implement=7
                ))
            
            # Check for scheduling opportunities
            if resource.tags.get("environment") == "development":
                # Recommend scheduling for dev environments
                savings = resource.current_cost * 0.65  # 65% savings (off 16 hours/day)
                recommendations.append(OptimizationRecommendation(
                    resource_id=resource.id,
                    type="schedule",
                    description=f"Schedule {resource.name} - Power off during non-business hours",
                    current_cost=resource.current_cost,
                    projected_cost=resource.current_cost * 0.35,
                    monthly_savings=savings,
                    implementation_effort="medium",
                    risk_level="low",
                    roi_percentage=650.0,
                    time_to_implement=5
                ))
        
        return recommendations
    
    def analyze_storage_optimization(self) -> List[OptimizationRecommendation]:
        """Analyze storage resources for optimization opportunities"""
        logger.info("Analyzing storage optimization opportunities")
        
        recommendations = []
        
        for resource in self.resources:
            if resource.type != "storage":
                continue
            
            storage_util = resource.usage_metrics.get("storage_utilization", 0)
            
            if storage_util < 0.5:
                # Recommend downsizing storage
                savings = resource.current_cost * 0.3
                recommendations.append(OptimizationRecommendation(
                    resource_id=resource.id,
                    type="storage_downsize",
                    description=f"Downsize {resource.name} - Low utilization ({storage_util:.1%})",
                    current_cost=resource.current_cost,
                    projected_cost=resource.current_cost * 0.7,
                    monthly_savings=savings,
                    implementation_effort="medium",
                    risk_level="medium",
                    roi_percentage=300.0,
                    time_to_implement=14
                ))
            
            # Recommend lifecycle policies
            recommendations.append(OptimizationRecommendation(
                resource_id=resource.id,
                type="lifecycle_policy",
                description=f"Implement lifecycle policy for {resource.name} - Archive old data",
                current_cost=resource.current_cost,
                projected_cost=resource.current_cost * 0.8,
                monthly_savings=resource.current_cost * 0.2,
                implementation_effort="low",
                risk_level="low",
                roi_percentage=200.0,
                time_to_implement=7
            ))
        
        return recommendations
    
    def analyze_network_optimization(self) -> List[OptimizationRecommendation]:
        """Analyze network resources for optimization opportunities"""
        logger.info("Analyzing network optimization opportunities")
        
        recommendations = []
        
        # Placeholder for network optimization logic
        # In real implementation, this would analyze CDN usage, data transfer patterns, etc.
        
        return recommendations
    
    def generate_optimization_report(self, timeframe_days: int = 30) -> Dict:
        """Generate comprehensive optimization report"""
        logger.info("Generating optimization report")
        
        # Collect all recommendations
        compute_recs = self.analyze_compute_optimization()
        storage_recs = self.analyze_storage_optimization()
        network_recs = self.analyze_network_optimization()
        
        all_recommendations = compute_recs + storage_recs + network_recs
        
        # Sort by monthly savings (descending)
        all_recommendations.sort(key=lambda x: x.monthly_savings, reverse=True)
        
        # Calculate totals
        total_current_cost = sum(r.current_cost for r in self.resources)
        total_monthly_savings = sum(r.monthly_savings for r in all_recommendations)
        total_implementation_cost = sum(r.current_cost * 0.1 for r in all_recommendations)  # Estimate 10% implementation cost
        
        # Generate report
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target_resource": "all-resources",
                "timeframe_days": timeframe_days,
                "total_resources": len(self.resources),
                "total_recommendations": len(all_recommendations)
            },
            "summary": {
                "current_monthly_cost": total_current_cost,
                "projected_monthly_savings": total_monthly_savings,
                "implementation_cost": total_implementation_cost,
                "net_12_month_savings": (total_monthly_savings * 12) - total_implementation_cost,
                "roi_percentage": ((total_monthly_savings * 12) / total_implementation_cost * 100) if total_implementation_cost > 0 else 0,
                "savings_percentage": (total_monthly_savings / total_current_cost * 100) if total_current_cost > 0 else 0
            },
            "recommendations": [asdict(rec) for rec in all_recommendations],
            "resource_breakdown": self._generate_resource_breakdown(),
            "implementation_roadmap": self._generate_implementation_roadmap(all_recommendations)
        }
        
        return report
    
    def _generate_resource_breakdown(self) -> Dict:
        """Generate breakdown by resource type"""
        breakdown = {}
        
        for resource in self.resources:
            if resource.type not in breakdown:
                breakdown[resource.type] = {
                    "count": 0,
                    "total_cost": 0.0,
                    "resources": []
                }
            
            breakdown[resource.type]["count"] += 1
            breakdown[resource.type]["total_cost"] += resource.current_cost
            breakdown[resource.type]["resources"].append({
                "id": resource.id,
                "name": resource.name,
                "cost": resource.current_cost,
                "utilization": resource.usage_metrics
            })
        
        return breakdown
    
    def _generate_implementation_roadmap(self, recommendations: List[OptimizationRecommendation]) -> Dict:
        """Generate implementation roadmap"""
        # Separate by implementation effort
        quick_wins = [r for r in recommendations if r.time_to_implement <= 7]
        medium_term = [r for r in recommendations if 7 < r.time_to_implement <= 30]
        long_term = [r for r in recommendations if r.time_to_implement > 30]
        
        return {
            "phase_1_quick_wins": {
                "duration_days": 30,
                "recommendations": [asdict(r) for r in quick_wins],
                "total_savings": sum(r.monthly_savings for r in quick_wins),
                "description": "Quick wins that can be implemented within 30 days"
            },
            "phase_2_medium_term": {
                "duration_days": 90,
                "recommendations": [asdict(r) for r in medium_term],
                "total_savings": sum(r.monthly_savings for r in medium_term),
                "description": "Medium-term optimizations requiring 30-90 days"
            },
            "phase_3_long_term": {
                "duration_days": 180,
                "recommendations": [asdict(r) for r in long_term],
                "total_savings": sum(r.monthly_savings for r in long_term),
                "description": "Strategic optimizations requiring 90+ days"
            }
        }
    
    def save_report(self, report: Dict, output_file: str) -> None:
        """Save report to file"""
        logger.info(f"Saving report to: {output_file}")
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    def print_summary(self, report: Dict) -> None:
        """Print executive summary"""
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("COST OPTIMIZATION REPORT SUMMARY")
        print("="*60)
        print(f"Current Monthly Cost: ${summary['current_monthly_cost']:,.2f}")
        print(f"Projected Monthly Savings: ${summary['projected_monthly_savings']:,.2f}")
        print(f"Savings Percentage: {summary['savings_percentage']:.1f}%")
        print(f"Implementation Cost: ${summary['implementation_cost']:,.2f}")
        print(f"Net 12-Month Savings: ${summary['net_12_month_savings']:,.2f}")
        print(f"ROI: {summary['roi_percentage']:.1f}%")
        print(f"Total Recommendations: {report['metadata']['total_recommendations']}")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Advanced Cost Analyzer")
    parser.add_argument("target", nargs="?", default="all-resources", 
                       help="Target resource to analyze (default: all-resources)")
    parser.add_argument("--analysis-type", choices=["usage", "optimization", "forecast", "full"],
                       default="full", help="Type of analysis to perform")
    parser.add_argument("--timeframe", type=int, default=30,
                       help="Analysis timeframe in days (default: 30)")
    parser.add_argument("--output", "-o", default="cost-analysis-report.json",
                       help="Output file for the report")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--api-base", default="http://localhost:8081",
                       help="API base URL")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = CostAnalyzer(api_base=args.api_base, api_key=args.api_key or "")
    
    # Load resources
    analyzer.load_resources(args.target)
    
    # Generate report
    report = analyzer.generate_optimization_report(args.timeframe)
    
    # Save report
    analyzer.save_report(report, args.output)
    
    # Print summary
    analyzer.print_summary(report)
    
    print(f"\nDetailed report saved to: {args.output}")

if __name__ == "__main__":
    main()
