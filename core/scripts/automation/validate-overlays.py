#!/usr/bin/env python3
"""
Overlay Validation Script
Validates overlay structure, metadata, and compliance with agentskills.io specification
"""

import os
import sys
import yaml
import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OverlayValidator:
    def __init__(self, overlays_dir: str, schema_file: str = None):
        self.overlays_dir = Path(overlays_dir)
        self.schema_file = schema_file or (self.overlays_dir / "registry" / "schema.yaml")
        self.schema = self._load_schema()
        self.errors = []
        self.warnings = []

    def _load_schema(self) -> Dict:
        """Load overlay metadata schema"""
        try:
            with open(self.schema_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self.schema_file}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error loading schema: {e}")
            return {}

    def validate_all_overlays(self) -> bool:
        """Validate all overlays in the overlays directory"""
        logger.info(f"Validating overlays in: {self.overlays_dir}")
        
        if not self.overlays_dir.exists():
            logger.error(f"Overlays directory not found: {self.overlays_dir}")
            return False

        success = True
        
        # Validate each overlay directory
        for overlay_dir in self._find_overlay_directories():
            if not self.validate_overlay(overlay_dir):
                success = False
        
        # Print summary
        self._print_summary()
        return success

    def validate_overlay(self, overlay_dir: Path) -> bool:
        """Validate a single overlay"""
        logger.info(f"Validating overlay: {overlay_dir}")
        overlay_success = True
        
        # Check required files
        if not self._validate_required_files(overlay_dir):
            overlay_success = False
        
        # Validate kustomization.yaml
        if not self._validate_kustomization(overlay_dir):
            overlay_success = False
        
        # Validate metadata
        if not self._validate_metadata(overlay_dir):
            overlay_success = False
        
        # Validate structure
        if not self._validate_structure(overlay_dir):
            overlay_success = False
        
        # Validate agentskills.io compliance for skill overlays
        if self._is_skill_overlay(overlay_dir):
            if not self._validate_agentskills_compliance(overlay_dir):
                overlay_success = False
        
        return overlay_success

    def _find_overlay_directories(self) -> List[Path]:
        """Find all overlay directories"""
        overlay_dirs = []
        
        # Look for directories containing kustomization.yaml
        for root, dirs, files in os.walk(self.overlays_dir):
            if 'kustomization.yaml' in files:
                overlay_dirs.append(Path(root))
        
        return overlay_dirs

    def _validate_required_files(self, overlay_dir: Path) -> bool:
        """Validate required overlay files"""
        required_files = ['kustomization.yaml']
        optional_files = ['overlay-metadata.yaml', 'README.md']
        
        success = True
        
        for file in required_files:
            file_path = overlay_dir / file
            if not file_path.exists():
                self.errors.append(f"Missing required file: {file_path}")
                success = False
        
        # Check for optional files and warn
        for file in optional_files:
            file_path = overlay_dir / file
            if not file_path.exists():
                self.warnings.append(f"Missing optional file: {file_path}")
        
        return success

    def _validate_kustomization(self, overlay_dir: Path) -> bool:
        """Validate kustomization.yaml"""
        kustomization_path = overlay_dir / 'kustomization.yaml'
        
        try:
            with open(kustomization_path, 'r') as f:
                kustomization = yaml.safe_load(f)
            
            # Check required fields
            if not kustomization.get('apiVersion'):
                self.errors.append(f"Missing apiVersion in {kustomization_path}")
                return False
            
            if not kustomization.get('kind'):
                self.errors.append(f"Missing kind in {kustomization_path}")
                return False
            
            if kustomization['kind'] != 'Kustomization':
                self.errors.append(f"Invalid kind in {kustomization_path}: expected 'Kustomization'")
                return False
            
            # Check resources reference base components
            resources = kustomization.get('resources', [])
            if not resources:
                self.warnings.append(f"No resources found in {kustomization_path}")
            
            # Validate resource paths
            for resource in resources:
                if isinstance(resource, str):
                    resource_path = overlay_dir.parent / resource
                    if not resource_path.exists():
                        self.errors.append(f"Resource not found: {resource_path}")
                        return False
            
            return True
            
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in {kustomization_path}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error validating {kustomization_path}: {e}")
            return False

    def _validate_metadata(self, overlay_dir: Path) -> bool:
        """Validate overlay metadata"""
        metadata_path = overlay_dir / 'overlay-metadata.yaml'
        
        if not metadata_path.exists():
            self.warnings.append(f"No metadata file found: {metadata_path}")
            return True  # Optional file
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
            
            # Validate against schema if available
            if self.schema:
                try:
                    jsonschema.validate(metadata, self.schema.get('schema', {}))
                except jsonschema.ValidationError as e:
                    self.errors.append(f"Schema validation failed for {metadata_path}: {e.message}")
                    return False
            
            # Check required metadata fields
            required_fields = ['name', 'version', 'description', 'category', 'license']
            for field in required_fields:
                if not metadata.get(field):
                    self.errors.append(f"Missing required metadata field: {field} in {metadata_path}")
                    return False
            
            # Validate version format
            version = metadata.get('version', '')
            if not self._validate_version_format(version):
                self.errors.append(f"Invalid version format: {version} in {metadata_path}")
                return False
            
            # Validate category
            category = metadata.get('category', '')
            valid_categories = ['skills', 'dashboard', 'infrastructure', 'composed']
            if category not in valid_categories:
                self.errors.append(f"Invalid category: {category} in {metadata_path}")
                return False
            
            return True
            
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in {metadata_path}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error validating {metadata_path}: {e}")
            return False

    def _validate_structure(self, overlay_dir: Path) -> bool:
        """Validate overlay directory structure"""
        success = True
        
        # Check for placeholder values in files
        for file_path in overlay_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.yaml', '.yml', '.json']:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Check for placeholder patterns
                    placeholders = ['{{overlay-name}}', '{{base-skill}}', '{{base-component}}']
                    for placeholder in placeholders:
                        if placeholder in content:
                            self.warnings.append(f"Placeholder found in {file_path}: {placeholder}")
                
                except Exception as e:
                    self.warnings.append(f"Could not read {file_path}: {e}")
        
        return success

    def _is_skill_overlay(self, overlay_dir: Path) -> bool:
        """Check if overlay is a skill overlay"""
        return 'ai/skills' in str(overlay_dir)

    def _validate_agentskills_compliance(self, overlay_dir: Path) -> bool:
        """Validate agentskills.io compliance for skill overlays"""
        metadata_path = overlay_dir / 'overlay-metadata.yaml'
        
        if not metadata_path.exists():
            self.warnings.append(f"No metadata to validate agentskills.io compliance: {metadata_path}")
            return True
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
            
            success = True
            
            # Check for agentskills.io compatibility
            compatibility = metadata.get('compatibility', {})
            if not compatibility.get('agentskills.io'):
                self.warnings.append(f"No agentskills.io version specified in {metadata_path}")
            
            # Validate input/output schemas for skills
            if not metadata.get('inputs'):
                self.warnings.append(f"No input schema defined in {metadata_path}")
            
            if not metadata.get('outputs'):
                self.warnings.append(f"No output schema defined in {metadata_path}")
            
            # Check for proper skill naming convention
            name = metadata.get('name', '')
            if not self._validate_skill_name(name):
                self.errors.append(f"Invalid skill name format: {name} in {metadata_path}")
                success = False
            
            return success
            
        except Exception as e:
            self.errors.append(f"Error validating agentskills.io compliance: {e}")
            return False

    def _validate_version_format(self, version: str) -> bool:
        """Validate semantic version format"""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))

    def _validate_skill_name(self, name: str) -> bool:
        """Validate skill name format (lowercase, numbers, hyphens only)"""
        import re
        pattern = r'^[a-z0-9-]+$'
        return bool(re.match(pattern, name))

    def _print_summary(self):
        """Print validation summary"""
        print("\n" + "="*50)
        print("OVERLAY VALIDATION SUMMARY")
        print("="*50)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All overlays validated successfully!")
        elif not self.errors:
            print("\n✅ All overlays validated with warnings")
        else:
            print(f"\n❌ Validation failed with {len(self.errors)} error(s)")
        
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Validate overlays structure and metadata')
    parser.add_argument('overlays_dir', help='Overlays directory path')
    parser.add_argument('--schema', help='Schema file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = OverlayValidator(args.overlays_dir, args.schema)
    success = validator.validate_all_overlays()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
