#!/usr/bin/env python3
"""
Overlay Registry Implementation
Manages overlay metadata, discovery, and distribution
"""

import os
import sys
import yaml
import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import argparse
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OverlayRegistry:
    def __init__(self, registry_dir: str = "core/deployment/overlays/registry"):
        self.registry_dir = Path(registry_dir)
        self.schema_file = self.registry_dir / "schema.yaml"
        self.catalog_file = self.registry_dir / "catalog.yaml"
        self.index_file = self.registry_dir / "index.json"
        
    def initialize_registry(self) -> bool:
        """Initialize a new registry"""
        try:
            # Create registry directory
            self.registry_dir.mkdir(parents=True, exist_ok=True)
            
            # Create schema if it doesn't exist
            if not self.schema_file.exists():
                schema = self._create_schema()
                with open(self.schema_file, 'w') as f:
                    yaml.dump(schema, f, default_flow_style=False)
            
            # Create catalog if it doesn't exist
            if not self.catalog_file.exists():
                catalog = {
                    'version': "1.0.0",
                    'description': "GitOps Infrastructure Control Plane Overlay Registry",
                    'overlays': [],
                    'statistics': {
                        'total_overlays': 0,
                        'overlays_by_category': {},
                        'overlays_by_risk_level': {},
                        'overlays_by_autonomy': {}
                    }
                }
                with open(self.catalog_file, 'w') as f:
                    yaml.dump(catalog, f, default_flow_style=False)
            
            logger.info(f"Registry initialized at: {self.registry_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing registry: {e}")
            return False
    
    def register_overlay(self, overlay_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Register an overlay in the catalog"""
        try:
            overlay_dir = Path(overlay_path)
            
            # Load metadata from file if not provided
            if not metadata:
                metadata_file = overlay_dir / "overlay-metadata.yaml"
                if not metadata_file.exists():
                    logger.error(f"Metadata file not found: {metadata_file}")
                    return False
                
                with open(metadata_file, 'r') as f:
                    metadata = yaml.safe_load(f)
            
            # Validate metadata
            if not self._validate_metadata(metadata):
                logger.error("Invalid metadata")
                return False
            
            # Calculate overlay checksum
            checksum = self._calculate_checksum(overlay_dir)
            metadata['checksum'] = checksum
            metadata['registered_at'] = datetime.now().isoformat()
            
            # Load existing catalog
            catalog = self._load_catalog()
            
            # Check if overlay already exists
            existing_overlays = [o for o in catalog['overlays'] if o['name'] == metadata['name']]
            if existing_overlays:
                # Update existing overlay
                for i, overlay in enumerate(catalog['overlays']):
                    if overlay['name'] == metadata['name']:
                        catalog['overlays'][i] = metadata
                        break
                logger.info(f"Updated overlay: {metadata['name']}")
            else:
                # Add new overlay
                catalog['overlays'].append(metadata)
                logger.info(f"Registered overlay: {metadata['name']}")
            
            # Update statistics
            catalog['statistics'] = self._calculate_statistics(catalog['overlays'])
            
            # Save catalog
            with open(self.catalog_file, 'w') as f:
                yaml.dump(catalog, f, default_flow_style=False)
            
            # Update index
            self._update_index(catalog)
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering overlay: {e}")
            return False
    
    def unregister_overlay(self, overlay_name: str) -> bool:
        """Unregister an overlay from the catalog"""
        try:
            catalog = self._load_catalog()
            
            # Remove overlay
            original_count = len(catalog['overlays'])
            catalog['overlays'] = [o for o in catalog['overlays'] if o['name'] != overlay_name]
            
            if len(catalog['overlays']) == original_count:
                logger.warning(f"Overlay not found: {overlay_name}")
                return False
            
            # Update statistics
            catalog['statistics'] = self._calculate_statistics(catalog['overlays'])
            
            # Save catalog
            with open(self.catalog_file, 'w') as f:
                yaml.dump(catalog, f, default_flow_style=False)
            
            # Update index
            self._update_index(catalog)
            
            logger.info(f"Unregistered overlay: {overlay_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering overlay: {e}")
            return False
    
    def search_overlays(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search overlays in the catalog"""
        try:
            catalog = self._load_catalog()
            overlays = catalog['overlays']
            results = []
            
            for overlay in overlays:
                # Text search
                if query.lower() in overlay.get('name', '').lower() or \
                   query.lower() in overlay.get('description', '').lower():
                    results.append(overlay)
                    continue
                
                # Tag search
                tags = overlay.get('tags', [])
                if any(query.lower() in tag.lower() for tag in tags):
                    results.append(overlay)
                    continue
            
            # Apply filters
            if filters:
                filtered_results = []
                for overlay in results:
                    match = True
                    for key, value in filters.items():
                        if key in overlay and overlay[key] != value:
                            match = False
                            break
                    if match:
                        filtered_results.append(overlay)
                results = filtered_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching overlays: {e}")
            return []
    
    def get_overlay(self, overlay_name: str) -> Optional[Dict[str, Any]]:
        """Get overlay metadata by name"""
        try:
            catalog = self._load_catalog()
            
            for overlay in catalog['overlays']:
                if overlay['name'] == overlay_name:
                    return overlay
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting overlay: {e}")
            return None
    
    def list_overlays(self, category: Optional[str] = None, sort_by: str = "name") -> List[Dict[str, Any]]:
        """List all overlays"""
        try:
            catalog = self._load_catalog()
            overlays = catalog['overlays']
            
            # Filter by category
            if category:
                overlays = [o for o in overlays if o.get('category') == category]
            
            # Sort
            if sort_by in ['name', 'version', 'category', 'risk_level', 'autonomy']:
                overlays.sort(key=lambda x: x.get(sort_by, ''))
            
            return overlays
            
        except Exception as e:
            logger.error(f"Error listing overlays: {e}")
            return []
    
    def validate_registry(self) -> Tuple[bool, List[str]]:
        """Validate registry integrity"""
        try:
            errors = []
            
            # Check schema file
            if not self.schema_file.exists():
                errors.append("Schema file not found")
            
            # Check catalog file
            if not self.catalog_file.exists():
                errors.append("Catalog file not found")
            
            # Validate catalog structure
            catalog = self._load_catalog()
            required_fields = ['version', 'description', 'overlays', 'statistics']
            for field in required_fields:
                if field not in catalog:
                    errors.append(f"Missing required field in catalog: {field}")
            
            # Validate each overlay
            for overlay in catalog.get('overlays', []):
                if not self._validate_metadata(overlay):
                    errors.append(f"Invalid metadata for overlay: {overlay.get('name', 'unknown')}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating registry: {e}")
            return False, [str(e)]
    
    def export_registry(self, output_file: str, format_type: str = "yaml") -> bool:
        """Export registry to file"""
        try:
            catalog = self._load_catalog()
            
            output_path = Path(output_file)
            with open(output_path, 'w') as f:
                if format_type == "yaml":
                    yaml.dump(catalog, f, default_flow_style=False)
                elif format_type == "json":
                    json.dump(catalog, f, indent=2)
                else:
                    logger.error(f"Unsupported format: {format_type}")
                    return False
            
            logger.info(f"Registry exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting registry: {e}")
            return False
    
    def import_registry(self, input_file: str, merge: bool = True) -> bool:
        """Import registry from file"""
        try:
            input_path = Path(input_file)
            
            # Load import data
            with open(input_path, 'r') as f:
                if input_path.suffix.lower() == '.json':
                    import_data = json.load(f)
                else:
                    import_data = yaml.safe_load(f)
            
            # Validate import data
            if 'overlays' not in import_data:
                logger.error("Invalid import data: missing overlays")
                return False
            
            if merge:
                # Merge with existing catalog
                catalog = self._load_catalog()
                existing_names = {o['name'] for o in catalog['overlays']}
                
                for overlay in import_data['overlays']:
                    if overlay['name'] not in existing_names:
                        catalog['overlays'].append(overlay)
            else:
                # Replace entire catalog
                catalog = import_data
            
            # Update statistics
            catalog['statistics'] = self._calculate_statistics(catalog['overlays'])
            
            # Save catalog
            with open(self.catalog_file, 'w') as f:
                yaml.dump(catalog, f, default_flow_style=False)
            
            # Update index
            self._update_index(catalog)
            
            logger.info(f"Registry imported from: {input_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing registry: {e}")
            return False
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load catalog from file"""
        with open(self.catalog_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate overlay metadata"""
        required_fields = ['name', 'version', 'description', 'category', 'license']
        
        for field in required_fields:
            if field not in metadata:
                return False
        
        # Validate category
        valid_categories = ['skills', 'dashboard', 'infrastructure', 'composed']
        if metadata.get('category') not in valid_categories:
            return False
        
        # Validate version format
        version = metadata.get('version', '')
        if not self._validate_version_format(version):
            return False
        
        return True
    
    def _validate_version_format(self, version: str) -> bool:
        """Validate semantic version format"""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def _calculate_checksum(self, overlay_dir: Path) -> str:
        """Calculate checksum for overlay directory"""
        hash_md5 = hashlib.md5()
        
        for file_path in sorted(overlay_dir.rglob("*")):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
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
    
    def _update_index(self, catalog: Dict[str, Any]) -> None:
        """Update search index"""
        index = {
            'version': "1.0.0",
            'updated_at': datetime.now().isoformat(),
            'overlays': []
        }
        
        for overlay in catalog['overlays']:
            index_entry = {
                'name': overlay['name'],
                'category': overlay['category'],
                'description': overlay['description'],
                'tags': overlay.get('tags', []),
                'version': overlay['version']
            }
            index['overlays'].append(index_entry)
        
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def _create_schema(self) -> Dict[str, Any]:
        """Create overlay metadata schema"""
        return {
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'title': 'Overlay Metadata Schema',
            'type': 'object',
            'required': [
                'name', 'version', 'description', 'category', 
                'base_path', 'license', 'risk_level', 'autonomy'
            ],
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': '^[a-z0-9-]+$',
                    'description': 'Overlay name (lowercase, hyphens allowed)'
                },
                'version': {
                    'type': 'string',
                    'pattern': '^\\d+\\.\\d+\\.\\d+$',
                    'description': 'Semantic version'
                },
                'description': {
                    'type': 'string',
                    'minLength': 10,
                    'description': 'Detailed description of the overlay'
                },
                'category': {
                    'type': 'string',
                    'enum': ['skills', 'dashboard', 'infrastructure', 'composed'],
                    'description': 'Overlay category'
                },
                'base_path': {
                    'type': 'string',
                    'description': 'Base path for the overlay'
                },
                'license': {
                    'type': 'string',
                    'description': 'License type'
                },
                'risk_level': {
                    'type': 'string',
                    'enum': ['low', 'medium', 'high'],
                    'description': 'Risk level of the overlay'
                },
                'autonomy': {
                    'type': 'string',
                    'enum': ['fully_auto', 'conditional', 'requires_pr'],
                    'description': 'Autonomy level of the overlay'
                },
                'maintainer': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'email': {'type': 'string', 'format': 'email'},
                        'organization': {'type': 'string'},
                        'url': {'type': 'string', 'format': 'uri'}
                    }
                },
                'tags': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Tags for categorization'
                },
                'compatibility': {
                    'type': 'object',
                    'properties': {
                        'min_base': {'type': 'string'},
                        'max_base': {'type': 'string'},
                        'agentskills.io': {'type': 'string'},
                        'python': {'type': 'string'},
                        'kubernetes': {'type': 'string'}
                    }
                }
            }
        }

def main():
    parser = argparse.ArgumentParser(description='Overlay Registry Tool')
    parser.add_argument('--registry-dir', default='core/deployment/overlays/registry', help='Registry directory path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize registry')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register an overlay')
    register_parser.add_argument('overlay_path', help='Overlay directory path')
    
    # Unregister command
    unregister_parser = subparsers.add_parser('unregister', help='Unregister an overlay')
    unregister_parser.add_argument('overlay_name', help='Overlay name')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search overlays')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--category', help='Filter by category')
    search_parser.add_argument('--risk-level', help='Filter by risk level')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List overlays')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--sort', choices=['name', 'version', 'category'], default='name', help='Sort by')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get overlay details')
    get_parser.add_argument('overlay_name', help='Overlay name')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate registry')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export registry')
    export_parser.add_argument('output_file', help='Output file path')
    export_parser.add_argument('--format', choices=['yaml', 'json'], default='yaml', help='Output format')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import registry')
    import_parser.add_argument('input_file', help='Input file path')
    import_parser.add_argument('--replace', action='store_true', help='Replace existing registry')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return
    
    registry = OverlayRegistry(args.registry_dir)
    
    if args.command == 'init':
        success = registry.initialize_registry()
    elif args.command == 'register':
        success = registry.register_overlay(args.overlay_path)
    elif args.command == 'unregister':
        success = registry.unregister_overlay(args.overlay_name)
    elif args.command == 'search':
        filters = {}
        if args.category:
            filters['category'] = args.category
        if args.risk_level:
            filters['risk_level'] = args.risk_level
        results = registry.search_overlays(args.query, filters)
        for overlay in results:
            print(f"{overlay['name']} - {overlay['description']}")
        success = True
    elif args.command == 'list':
        overlays = registry.list_overlays(args.category, args.sort)
        for overlay in overlays:
            print(f"{overlay['name']} ({overlay['category']}) - {overlay['description']}")
        success = True
    elif args.command == 'get':
        overlay = registry.get_overlay(args.overlay_name)
        if overlay:
            print(yaml.dump(overlay, default_flow_style=False))
            success = True
        else:
            print(f"Overlay not found: {args.overlay_name}")
            success = False
    elif args.command == 'validate':
        success, errors = registry.validate_registry()
        if success:
            print("Registry is valid")
        else:
            print("Registry validation failed:")
            for error in errors:
                print(f"  - {error}")
    elif args.command == 'export':
        success = registry.export_registry(args.output_file, args.format)
    elif args.command == 'import':
        success = registry.import_registry(args.input_file, not args.replace)
    else:
        parser.print_help()
        return
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
