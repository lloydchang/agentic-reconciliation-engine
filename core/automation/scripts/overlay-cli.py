#!/usr/bin/env python3
"""
Overlay CLI Tool
Command-line interface for managing overlays in the GitOps Infrastructure Control Plane
"""

import os
import sys
import yaml
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OverlayCLI:
    def __init__(self, overlays_dir: str = "overlay"):
        self.overlays_dir = Path(overlays_dir)
        self.registry_dir = self.overlays_dir / "registry"
        self.templates_dir = self.overlays_dir / "templates"
        
    def list_overlays(self, category: Optional[str] = None, format_type: str = "table") -> bool:
        """List available overlays"""
        try:
            catalog_path = self.registry_dir / "catalog.yaml"
            if not catalog_path.exists():
                logger.error(f"Catalog not found: {catalog_path}")
                return False
            
            with open(catalog_path, 'r') as f:
                catalog = yaml.safe_load(f)
            
            overlays = catalog.get('overlays', [])
            
            if category:
                overlays = [o for o in overlays if o.get('category') == category]
            
            if format_type == "table":
                self._print_table(overlays)
            elif format_type == "json":
                print(json.dumps(overlays, indent=2))
            elif format_type == "yaml":
                yaml.dump(overlays, sys.stdout)
            
            return True
            
        except Exception as e:
            logger.error(f"Error listing overlays: {e}")
            return False
    
    def create_overlay(self, name: str, category: str, base_path: str, template: Optional[str] = None) -> bool:
        """Create a new overlay"""
        try:
            # Determine target directory based on new overlay structure
            if category == "skills":
                target_dir = self.overlays_dir / "ai" / "skills" / name
            elif category == "dashboard":
                target_dir = self.overlays_dir / "ai" / "runtime" / "dashboard" / name
            elif category == "infrastructure":
                target_dir = self.overlays_dir / "operators" / "control-plane" / name
            elif category == "config":
                target_dir = self.overlays_dir / "config" / name
            elif category == "deployment":
                target_dir = self.overlays_dir / "deployment" / name
            elif category == "composed":
                target_dir = self.overlays_dir / "examples" / name
            else:
                logger.error(f"Unknown category: {category}")
                return False
            
            # Check if overlay already exists
            if target_dir.exists():
                logger.error(f"Overlay already exists: {target_dir}")
                return False
            
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Use template if specified
            if template:
                # Handle both singular and plural forms
                template_name = template
                if category == "skills" and template == "skills-overlay":
                    template_name = "skill-overlay"
                elif category == "skills" and template == "skill-overlay":
                    template_name = "skill-overlay"
                elif category == "dashboard" and template == "dashboard-overlays":
                    template_name = "dashboard-overlay"
                elif category == "dashboard" and template == "dashboard-overlay":
                    template_name = "dashboard-overlay"
                elif category == "infrastructure" and template == "infra-overlays":
                    template_name = "infra-overlay"
                elif category == "infrastructure" and template == "infra-overlay":
                    template_name = "infra-overlay"
                
                template_dir = self.templates_dir / template_name
                if not template_dir.exists():
                    logger.error(f"Template not found: {template_dir}")
                    return False
                
                # Copy template files
                for item in template_dir.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(template_dir)
                        target_file = target_dir / rel_path
                        
                        # Create parent directories if needed
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy and replace placeholders
                        content = item.read_text()
                        content = content.replace("{{overlay-name}}", name)
                        content = content.replace("{{base-skill}}" if category == "skills" else "{{base-component}}", base_path)
                        target_file.write_text(content)
            
            # Create basic kustomization.yaml if no template
            if not template:
                kustomization = {
                    'apiVersion': 'kustomize.config.k8s.io/v1beta1',
                    'kind': 'Kustomization',
                    'metadata': {
                        'name': name,
                        'namespace': 'flux-system'
                    },
                    'resources': []
                }
                
                kustomization_path = target_dir / "kustomization.yaml"
                with open(kustomization_path, 'w') as f:
                    yaml.dump(kustomization, f)
            
            # Create metadata
            metadata = {
                'name': name,
                'version': "1.0.0",
                'description': f"Generated {category} overlay: {name}",
                'category': category,
                'base_path': base_path,
                'license': "AGPLv3",
                'risk_level': "low",
                'autonomy': "fully_auto",
                'maintainer': {
                    'name': "Generated",
                    'email': "generated@example.com"
                },
                'tags': [category, name],
                'compatibility': {
                    'min_base': "main",
                    'kubernetes': ">=1.20"
                }
            }
            
            metadata_path = target_dir / "overlay-metadata.yaml"
            with open(metadata_path, 'w') as f:
                yaml.dump(metadata, f)
            
            logger.info(f"Created overlay: {target_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating overlay: {e}")
            return False
    
    def validate_overlay(self, overlay_path: str) -> bool:
        """Validate an overlay"""
        try:
            overlay_dir = Path(overlay_path)
            if not overlay_dir.is_absolute():
                overlay_dir = self.overlays_dir / overlay_dir
            
            # Run validation script
            result = subprocess.run([
                'python', 
                str(Path(__file__).parent / 'validate-overlays.py'),
                str(overlay_dir)
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error validating overlay: {e}")
            return False
    
    def test_overlay(self, overlay_path: str) -> bool:
        """Test an overlay"""
        try:
            overlay_dir = Path(overlay_path)
            if not overlay_dir.is_absolute():
                overlay_dir = self.overlays_dir / overlay_dir
            
            # Run testing script
            result = subprocess.run([
                'python',
                str(Path(__file__).parent / 'test-overlays.py'),
                str(overlay_dir)
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error testing overlay: {e}")
            return False
    
    def build_overlay(self, overlay_path: str, output: Optional[str] = None) -> bool:
        """Build an overlay with kustomize"""
        try:
            overlay_dir = Path(overlay_path)
            if not overlay_dir.is_absolute():
                overlay_dir = self.overlays_dir / overlay_dir
            
            # Run kustomize build
            result = subprocess.run([
                'kustomize', 'build', str(overlay_dir)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Kustomize build failed: {result.stderr}")
                return False
            
            if output:
                with open(output, 'w') as f:
                    f.write(result.stdout)
                logger.info(f"Built overlay saved to: {output}")
            else:
                print(result.stdout)
            
            return True
            
        except Exception as e:
            logger.error(f"Error building overlay: {e}")
            return False
    
    def apply_overlay(self, overlay_path: str, dry_run: bool = False) -> bool:
        """Apply an overlay to the cluster"""
        try:
            overlay_dir = Path(overlay_path)
            if not overlay_dir.is_absolute():
                overlay_dir = self.overlays_dir / overlay_dir
            
            # Build overlay
            build_result = subprocess.run([
                'kustomize', 'build', str(overlay_dir)
            ], capture_output=True, text=True)
            
            if build_result.returncode != 0:
                logger.error(f"Kustomize build failed: {build_result.stderr}")
                return False
            
            # Apply with kubectl
            cmd = ['kubectl', 'apply']
            if dry_run:
                cmd.extend(['--dry-run=client'])
            cmd.extend(['-f', '-'])
            
            apply_result = subprocess.run(
                cmd,
                input=build_result.stdout,
                capture_output=True,
                text=True
            )
            
            if apply_result.returncode != 0:
                logger.error(f"Kubectl apply failed: {apply_result.stderr}")
                return False
            
            print(apply_result.stdout)
            if dry_run:
                logger.info("Dry run completed successfully")
            else:
                logger.info("Overlay applied successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying overlay: {e}")
            return False
    
    def search_overlays(self, query: str, tags: Optional[List[str]] = None) -> bool:
        """Search overlays by name, description, or tags"""
        try:
            catalog_path = self.registry_dir / "catalog.yaml"
            if not catalog_path.exists():
                logger.error(f"Catalog not found: {catalog_path}")
                return False
            
            with open(catalog_path, 'r') as f:
                catalog = yaml.safe_load(f)
            
            overlays = catalog.get('overlays', [])
            results = []
            
            for overlay in overlays:
                # Search by name and description
                if query.lower() in overlay.get('name', '').lower() or \
                   query.lower() in overlay.get('description', '').lower():
                    results.append(overlay)
                    continue
                
                # Search by tags
                overlay_tags = overlay.get('tags', [])
                if tags:
                    if any(tag.lower() in [t.lower() for t in overlay_tags] for tag in tags):
                        results.append(overlay)
                elif query.lower() in [t.lower() for t in overlay_tags]:
                    results.append(overlay)
            
            if results:
                self._print_table(results)
            else:
                print(f"No overlays found for query: {query}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error searching overlays: {e}")
            return False
    
    def update_catalog(self) -> bool:
        """Update the overlay catalog by scanning the overlays directory"""
        try:
            overlays = []
            
            # Scan overlays directory
            for root, dirs, files in os.walk(self.overlays_dir):
                if 'overlay-metadata.yaml' in files:
                    metadata_path = Path(root) / 'overlay-metadata.yaml'
                    with open(metadata_path, 'r') as f:
                        metadata = yaml.safe_load(f)
                    overlays.append(metadata)
            
            # Update catalog
            catalog = {
                'version': "1.0.0",
                'description': "GitOps Infrastructure Control Plane Overlay Registry",
                'overlays': overlays,
                'statistics': self._calculate_statistics(overlays)
            }
            
            catalog_path = self.registry_dir / "catalog.yaml"
            with open(catalog_path, 'w') as f:
                yaml.dump(catalog, f, default_flow_style=False)
            
            logger.info(f"Updated catalog with {len(overlays)} overlays")
            return True
            
        except Exception as e:
            logger.error(f"Error updating catalog: {e}")
            return False
    
    def _print_table(self, overlays: List[Dict[str, Any]]):
        """Print overlays in table format"""
        if not overlays:
            print("No overlays found")
            return
        
        # Table headers
        headers = ["Name", "Category", "Version", "Risk", "Autonomy", "Description"]
        col_widths = [20, 12, 10, 8, 12, 50]
        
        # Print header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        print(header_row)
        print("-" * len(header_row))
        
        # Print rows
        for overlay in overlays:
            row = [
                overlay.get('name', 'N/A')[:19],
                overlay.get('category', 'N/A')[:11],
                overlay.get('version', 'N/A')[:9],
                overlay.get('risk_level', 'N/A')[:7],
                overlay.get('autonomy', 'N/A')[:11],
                overlay.get('description', 'N/A')[:49]
            ]
            row_str = " | ".join(r.ljust(w) for r, w in zip(row, col_widths))
            print(row_str)
    
    def _calculate_statistics(self, overlays: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overlay statistics"""
        stats = {
            'total_overlays': len(overlays),
            'overlays_by_category': {},
            'overlays_by_risk_level': {},
            'overlays_by_autonomy': {}
        }
        
        for overlay in overlays:
            # Category stats
            category = overlay.get('category', 'unknown')
            stats['overlays_by_category'][category] = \
                stats['overlays_by_category'].get(category, 0) + 1
            
            # Risk level stats
            risk = overlay.get('risk_level', 'unknown')
            stats['overlays_by_risk_level'][risk] = \
                stats['overlays_by_risk_level'].get(risk, 0) + 1
            
            # Autonomy stats
            autonomy = overlay.get('autonomy', 'unknown')
            stats['overlays_by_autonomy'][autonomy] = \
                stats['overlays_by_autonomy'].get(autonomy, 0) + 1
        
        return stats

def main():
    import os
    default_overlays_dir = os.environ.get('OVERLAY_DIR', 'overlay')
    
    parser = argparse.ArgumentParser(description='Overlay CLI Tool')
    parser.add_argument('--overlays-dir', default=default_overlays_dir, help='Overlays directory path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available overlays')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--format', choices=['table', 'json', 'yaml'], default='table', help='Output format')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new overlay')
    create_parser.add_argument('name', help='Overlay name')
    create_parser.add_argument('category', choices=['skills', 'dashboard', 'infrastructure', 'composed'], help='Overlay category')
    create_parser.add_argument('base_path', help='Base path for the overlay')
    create_parser.add_argument('--template', help='Template to use')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate an overlay')
    validate_parser.add_argument('overlay_path', help='Overlay path')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test an overlay')
    test_parser.add_argument('overlay_path', help='Overlay path')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build an overlay')
    build_parser.add_argument('overlay_path', help='Overlay path')
    build_parser.add_argument('--output', '-o', help='Output file')
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help='Apply an overlay')
    apply_parser.add_argument('overlay_path', help='Overlay path')
    apply_parser.add_argument('--dry-run', action='store_true', help='Dry run only')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search overlays')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    
    # Update catalog command
    update_parser = subparsers.add_parser('update-catalog', help='Update overlay catalog')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return
    
    cli = OverlayCLI(args.overlays_dir)
    
    if args.command == 'list':
        success = cli.list_overlays(args.category, args.format)
    elif args.command == 'create':
        success = cli.create_overlay(args.name, args.category, args.base_path, args.template)
    elif args.command == 'validate':
        success = cli.validate_overlay(args.overlay_path)
    elif args.command == 'test':
        success = cli.test_overlay(args.overlay_path)
    elif args.command == 'build':
        success = cli.build_overlay(args.overlay_path, args.output)
    elif args.command == 'apply':
        success = cli.apply_overlay(args.overlay_path, args.dry_run)
    elif args.command == 'search':
        success = cli.search_overlays(args.query, args.tags)
    elif args.command == 'update-catalog':
        success = cli.update_catalog()
    else:
        parser.print_help()
        return
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
