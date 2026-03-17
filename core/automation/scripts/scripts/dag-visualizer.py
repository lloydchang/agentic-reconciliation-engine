#!/usr/bin/env python3
"""
Strategic Architecture: Flux + Temporal + Consensus Hybrid Approach

This tool visualizes dependency management within the Flux declarative layer of our hybrid architecture.

North Star Vision: Establish the definitive reference implementation for autonomous infrastructure management

Current Status: Core Flux dependency visualization and DAG analysis

Strategic Plan: See docs/STRATEGIC-ARCHITECTURE.md for roadmap

GitOps DAG Visualization Tool
Generates interactive dependency graphs for GitOps Infra Control Plane
"""

import json
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import argparse
from pathlib import Path

@dataclass
class Component:
    """Represents a component in the DAG"""
    name: str
    type: str  # kustomization, gitrepository, etc.
    path: Optional[str] = None
    dependencies: List[str] = None
    namespace: str = "flux-system"
    variant: str = "base"  # open-source, enterprise, language-specific
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class DAGVisualizer:
    """Generates DAG visualizations from GitOps manifests"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.components = {}
        self.edges = []
        
    def parse_kustomization(self, yaml_content: str) -> Dict:
        """Parse YAML content safely"""
        try:
            import yaml
            return yaml.safe_load(yaml_content)
        except ImportError:
            print("Error: PyYAML required. Install with: pip install pyyaml")
            sys.exit(1)
    
    def extract_dependencies(self, kustomization: Dict) -> List[str]:
        """Extract dependencies from a Kustomization"""
        deps = kustomization.get('spec', {}).get('dependsOn', [])
        if isinstance(deps, list):
            return [dep.get('name') for dep in deps if dep.get('name')]
        elif isinstance(deps, dict):
            return [deps.get('name')] if deps.get('name') else []
        return []
    
    def scan_repository(self):
        """Scan repository for GitOps components"""
        yaml_files = list(self.repo_path.rglob("*.yaml")) + list(self.repo_path.rglob("*.yml"))
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    content = f.read()
                    docs = content.split('---')
                    
                    for doc in docs:
                        if not doc.strip():
                            continue
                            
                        parsed = self.parse_kustomization(doc)
                        if not parsed:
                            continue
                            
                        if parsed.get('kind') == 'Kustomization':
                            metadata = parsed.get('metadata', {})
                            name = metadata.get('name')
                            if not name:
                                continue
                                
                            spec = parsed.get('spec', {})
                            dependencies = self.extract_dependencies(parsed)
                            
                            component = Component(
                                name=name,
                                type='kustomization',
                                path=spec.get('path'),
                                dependencies=dependencies,
                                namespace=metadata.get('namespace', 'flux-system')
                            )
                            
                            self.components[name] = component
                            
                            # Create edges
                            for dep in dependencies:
                                self.edges.append((dep, name))
                                
            except Exception as e:
                print(f"Warning: Could not parse {yaml_file}: {e}")
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return True
                
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            
            for dep in [e[1] for e in self.edges if e[0] == node]:
                if dfs(dep, path + [node]):
                    return True
                    
            rec_stack.remove(node)
            return False
        
        for component in self.components:
            if component not in visited:
                dfs(component, [])
                
        return cycles
    
    def generate_mermaid(self) -> str:
        """Generate Mermaid diagram for DAG visualization"""
        mermaid = ["graph TD"]
        
        # Add nodes
        for name, component in self.components.items():
            label = f"{name}\\n({component.type})"
            if component.path:
                label += f"\\n{component.path}"
            mermaid.append(f'    {name.replace("-", "")}["{label}"]')
        
        # Add edges
        for dep, dependent in self.edges:
            mermaid.append(f'    {dep.replace("-", "")} --> {dependent.replace("-")}')
        
        # Add styling for different types
        mermaid.extend([
            "    classDef kustomization fill:#e1f5fe",
            "    classDef gitrepository fill:#f3e5f5",
            "    classDef helmrelease fill:#e8f5e8",
            "    class kustomization kustomization"
        ])
        
        return "\n".join(mermaid)
    
    def generate_dot(self) -> str:
        """Generate GraphViz DOT format"""
        dot = ["digraph gitops_dag {"]
        dot.append("    rankdir=TB;")
        dot.append("    node [shape=box, style=filled];")
        
        # Add nodes
        for name, component in self.components.items():
            color = "#e1f5fe" if component.type == "kustomization" else "#f3e5f5"
            label = f"{name}\\n({component.type})"
            if component.path:
                label += f"\\n{component.path}"
            dot.append(f'    "{name}" [label="{label}", fillcolor="{color}"];')
        
        # Add edges
        for dep, dependent in self.edges:
            dot.append(f'    "{dep}" -> "{dependent}";')
        
        dot.append("}")
        return "\n".join(dot)
    
    def generate_plantuml(self) -> str:
        """Generate PlantUML diagram"""
        puml = ["@startuml", "!theme plain"]
        
        # Add components
        for name, component in self.components.items():
            stereotype = component.type.upper()
            puml.append(f'component "{name}" as {name.replace("-", "")} <<{stereotype}>>')
        
        # Add dependencies
        for dep, dependent in self.edges:
            puml.append(f'{dep.replace("-", "")} --> {dependent.replace("-")}')
        
        puml.append("@enduml")
        return "\n".join(puml)
    
    def analyze_variants(self) -> Dict[str, List[str]]:
        """Analyze different deployment variants"""
        variants = {
            "open-source": [],
            "enterprise": [],
            "ai-enhanced": [],
            "consensus-based": [],
            "language-specific": {}
        }
        
        for name, component in self.components.items():
            # Categorize by path and naming patterns
            path = component.path or ""
            
            if "enhanced" in path or "grafana" in path or "honeycomb" in path:
                variants["enterprise"].append(name)
            elif "ai" in path or "claude" in path or "openai" in path:
                variants["ai-enhanced"].append(name)
            elif "consensus" in path or "agent" in path:
                variants["consensus-based"].append(name)
            elif "python" in path or "go" in path or "rust" in path or "typescript" in path:
                lang = next((l for l in ["python", "go", "rust", "typescript"] if l in path), "other")
                if lang not in variants["language-specific"]:
                    variants["language-specific"][lang] = []
                variants["language-specific"][lang].append(name)
            else:
                variants["open-source"].append(name)
        
        return variants
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        cycles = self.detect_cycles()
        variants = self.analyze_variants()
        
        # Calculate statistics
        total_components = len(self.components)
        total_dependencies = len(self.edges)
        dependency_density = total_dependencies / max(total_components, 1)
        
        # Find critical path (longest dependency chain)
        def longest_path(node: str, visited: set) -> int:
            if node in visited:
                return 0
            visited.add(node)
            
            deps = [e[1] for e in self.edges if e[0] == node]
            if not deps:
                return 1
            return 1 + max(longest_path(dep, visited.copy()) for dep in deps)
        
        critical_path_length = max(
            (longest_path(comp, set()) for comp in self.components),
            default=0
        )
        
        return {
            "summary": {
                "total_components": total_components,
                "total_dependencies": total_dependencies,
                "dependency_density": dependency_density,
                "critical_path_length": critical_path_length,
                "has_cycles": len(cycles) > 0
            },
            "cycles": cycles,
            "variants": variants,
            "components": {name: {
                "type": comp.type,
                "path": comp.path,
                "dependencies": comp.dependencies,
                "namespace": comp.namespace
            } for name, comp in self.components.items()},
            "edges": self.edges
        }

def main():
    parser = argparse.ArgumentParser(description="GitOps DAG Visualization Tool")
    parser.add_argument("repo_path", help="Path to GitOps repository")
    parser.add_argument("--format", choices=["mermaid", "dot", "plantuml", "report"], 
                       default="mermaid", help="Output format")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    visualizer = DAGVisualizer(args.repo_path)
    visualizer.scan_repository()
    
    if args.format == "mermaid":
        output = visualizer.generate_mermaid()
    elif args.format == "dot":
        output = visualizer.generate_dot()
    elif args.format == "plantuml":
        output = visualizer.generate_plantuml()
    elif args.format == "report":
        report = visualizer.generate_report()
        output = json.dumps(report, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Output written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
