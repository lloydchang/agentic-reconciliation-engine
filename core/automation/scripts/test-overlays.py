#!/usr/bin/env python3
"""
Overlay Testing Framework
Comprehensive testing for overlays including structure, composition, and functionality
"""

import os
import sys
import yaml
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OverlayTester:
    def __init__(self, overlays_dir: str):
        self.overlays_dir = Path(overlays_dir)
        self.test_results = []
        self.failed_tests = []

    def run_all_tests(self) -> bool:
        """Run all overlay tests"""
        logger.info(f"Running overlay tests in: {self.overlays_dir}")
        
        if not self.overlays_dir.exists():
            logger.error(f"Overlays directory not found: {self.overlays_dir}")
            return False

        success = True
        
        # Test each overlay
        for overlay_dir in self._find_overlay_directories():
            if not self.test_overlay(overlay_dir):
                success = False
        
        # Test composed overlays
        for composed_dir in self._find_composed_directories():
            if not self.test_composed_overlay(composed_dir):
                success = False
        
        # Test overlay composition
        if not self.test_overlay_composition():
            success = False
        
        # Print summary
        self._print_test_summary()
        return success

    def test_overlay(self, overlay_dir: Path) -> bool:
        """Test a single overlay"""
        logger.info(f"Testing overlay: {overlay_dir}")
        overlay_success = True
        
        # Test structure
        if not self._test_overlay_structure(overlay_dir):
            overlay_success = False
        
        # Test kustomization
        if not self._test_kustomization_build(overlay_dir):
            overlay_success = False
        
        # Test metadata
        if not self._test_overlay_metadata(overlay_dir):
            overlay_success = False
        
        # Test composition
        if not self._test_overlay_composition_single(overlay_dir):
            overlay_success = False
        
        return overlay_success

    def test_composed_overlay(self, composed_dir: Path) -> bool:
        """Test a composed overlay"""
        logger.info(f"Testing composed overlay: {composed_dir}")
        composed_success = True
        
        # Test composed structure
        if not self._test_composed_structure(composed_dir):
            composed_success = False
        
        # Test composed build
        if not self._test_composed_build(composed_dir):
            composed_success = False
        
        # Test dependency resolution
        if not self._test_dependency_resolution(composed_dir):
            composed_success = False
        
        return composed_success

    def test_overlay_composition(self) -> bool:
        """Test overlay composition scenarios"""
        logger.info("Testing overlay composition scenarios")
        composition_success = True
        
        # Test multiple overlay composition
        if not self._test_multiple_composition():
            composition_success = False
        
        # Test overlay conflicts
        if not self._test_overlay_conflicts():
            composition_success = False
        
        # Test overlay dependencies
        if not self._test_overlay_dependencies():
            composition_success = False
        
        return composition_success

    def _find_overlay_directories(self) -> List[Path]:
        """Find all overlay directories"""
        overlay_dirs = []
        
        for root, dirs, files in os.walk(self.overlays_dir):
            if 'kustomization.yaml' in files and 'examples' not in str(root):
                overlay_dirs.append(Path(root))
        
        return overlay_dirs

    def _find_composed_directories(self) -> List[Path]:
        """Find all composed overlay directories"""
        composed_dirs = []
        
        composed_path = self.overlays_dir / 'examples'
        if composed_path.exists():
            for root, dirs, files in os.walk(composed_path):
                if 'kustomization.yaml' in files:
                    composed_dirs.append(Path(root))
        
        return composed_dirs

    def _test_overlay_structure(self, overlay_dir: Path) -> bool:
        """Test overlay directory structure"""
        test_name = f"structure_{overlay_dir.name}"
        
        try:
            # Check required files
            required_files = ['kustomization.yaml']
            for file in required_files:
                file_path = overlay_dir / file
                if not file_path.exists():
                    self._add_test_failure(test_name, f"Missing required file: {file}")
                    return False
            
            # Check YAML syntax
            for file in overlay_dir.rglob('*.yaml'):
                if file.is_file():
                    try:
                        with open(file, 'r') as f:
                            yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self._add_test_failure(test_name, f"Invalid YAML in {file}: {e}")
                        return False
            
            self._add_test_success(test_name, "Overlay structure is valid")
            return True
            
        except Exception as e:
            self._add_test_failure(test_name, f"Structure test error: {e}")
            return False

    def _test_kustomization_build(self, overlay_dir: Path) -> bool:
        """Test kustomization build"""
        test_name = f"kustomization_build_{overlay_dir.name}"
        
        try:
            # Run kustomize build
            result = subprocess.run(
                ['kustomize', 'build', str(overlay_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self._add_test_failure(test_name, f"Kustomize build failed: {result.stderr}")
                return False
            
            # Validate output is valid YAML
            try:
                yaml.safe_load(result.stdout)
            except yaml.YAMLError as e:
                self._add_test_failure(test_name, f"Invalid kustomize output: {e}")
                return False
            
            self._add_test_success(test_name, "Kustomize build successful")
            return True
            
        except subprocess.TimeoutExpired:
            self._add_test_failure(test_name, "Kustomize build timed out")
            return False
        except Exception as e:
            self._add_test_failure(test_name, f"Kustomize build error: {e}")
            return False

    def _test_overlay_metadata(self, overlay_dir: Path) -> bool:
        """Test overlay metadata"""
        test_name = f"metadata_{overlay_dir.name}"
        
        try:
            metadata_path = overlay_dir / 'overlay-metadata.yaml'
            
            if not metadata_path.exists():
                self._add_test_success(test_name, "No metadata file (optional)")
                return True
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
            
            # Check required fields
            required_fields = ['name', 'version', 'description', 'category', 'license']
            for field in required_fields:
                if not metadata.get(field):
                    self._add_test_failure(test_name, f"Missing required metadata field: {field}")
                    return False
            
            # Validate version format
            version = metadata.get('version', '')
            if not self._validate_version_format(version):
                self._add_test_failure(test_name, f"Invalid version format: {version}")
                return False
            
            # Validate category
            category = metadata.get('category', '')
            valid_categories = ['skills', 'dashboard', 'infrastructure', 'composed']
            if category not in valid_categories:
                self._add_test_failure(test_name, f"Invalid category: {category}")
                return False
            
            self._add_test_success(test_name, "Overlay metadata is valid")
            return True
            
        except Exception as e:
            self._add_test_failure(test_name, f"Metadata test error: {e}")
            return False

    def _test_overlay_composition_single(self, overlay_dir: Path) -> bool:
        """Test single overlay composition"""
        test_name = f"composition_single_{overlay_dir.name}"
        
        try:
            # Test with dry-run
            result = subprocess.run(
                ['kubectl', 'apply', '--dry-run=client', '-f', '-'],
                input=subprocess.run(['kustomize', 'build', str(overlay_dir)], 
                                  capture_output=True, text=True).stdout,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self._add_test_failure(test_name, f"Dry-run failed: {result.stderr}")
                return False
            
            self._add_test_success(test_name, "Single overlay composition successful")
            return True
            
        except subprocess.TimeoutExpired:
            self._add_test_failure(test_name, "Composition test timed out")
            return False
        except Exception as e:
            self._add_test_failure(test_name, f"Composition test error: {e}")
            return False

    def _test_composed_structure(self, composed_dir: Path) -> bool:
        """Test composed overlay structure"""
        test_name = f"composed_structure_{composed_dir.name}"
        
        try:
            # Check for resource references
            kustomization_path = composed_dir / 'kustomization.yaml'
            with open(kustomization_path, 'r') as f:
                kustomization = yaml.safe_load(f)
            
            resources = kustomization.get('resources', [])
            if not resources:
                self._add_test_failure(test_name, "No resources found in composed overlay")
                return False
            
            # Check if resources exist
            for resource in resources:
                if isinstance(resource, str):
                    resource_path = composed_dir.parent / resource
                    if not resource_path.exists():
                        self._add_test_failure(test_name, f"Resource not found: {resource}")
                        return False
            
            self._add_test_success(test_name, "Composed overlay structure is valid")
            return True
            
        except Exception as e:
            self._add_test_failure(test_name, f"Composed structure test error: {e}")
            return False

    def _test_composed_build(self, composed_dir: Path) -> bool:
        """Test composed overlay build"""
        test_name = f"composed_build_{composed_dir.name}"
        
        try:
            result = subprocess.run(
                ['kustomize', 'build', str(composed_dir)],
                capture_output=True,
                text=True,
                timeout=60  # Longer timeout for composed overlays
            )
            
            if result.returncode != 0:
                self._add_test_failure(test_name, f"Composed build failed: {result.stderr}")
                return False
            
            # Validate output size (composed overlays should be larger)
            output_lines = len(result.stdout.split('\n'))
            if output_lines < 50:
                self._add_test_failure(test_name, f"Composed output too small: {output_lines} lines")
                return False
            
            self._add_test_success(test_name, f"Composed build successful ({output_lines} lines)")
            return True
            
        except subprocess.TimeoutExpired:
            self._add_test_failure(test_name, "Composed build timed out")
            return False
        except Exception as e:
            self._add_test_failure(test_name, f"Composed build error: {e}")
            return False

    def _test_dependency_resolution(self, composed_dir: Path) -> bool:
        """Test dependency resolution for composed overlays"""
        test_name = f"dependency_resolution_{composed_dir.name}"
        
        try:
            # Check for circular dependencies
            kustomization_path = composed_dir / 'kustomization.yaml'
            with open(kustomization_path, 'r') as f:
                kustomization = yaml.safe_load(f)
            
            resources = kustomization.get('resources', [])
            
            # Simple circular dependency check
            for resource in resources:
                if isinstance(resource, str) and 'composed' in resource:
                    resource_parts = resource.split('/')
                    if len(resource_parts) > 2 and resource_parts[1] == composed_dir.name:
                        self._add_test_failure(test_name, f"Circular dependency detected: {resource}")
                        return False
            
            self._add_test_success(test_name, "Dependency resolution successful")
            return True
            
        except Exception as e:
            self._add_test_failure(test_name, f"Dependency resolution error: {e}")
            return False

    def _test_multiple_composition(self) -> bool:
        """Test multiple overlay composition"""
        test_name = "multiple_composition"
        
        try:
            # Find multiple overlays to compose
            overlay_dirs = self._find_overlay_directories()[:3]  # Test first 3
            
            if len(overlay_dirs) < 2:
                self._add_test_success(test_name, "Not enough overlays for multiple composition test")
                return True
            
            # Create temporary composition
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                kustomization_path = temp_path / 'kustomization.yaml'
                
                # Create composition kustomization
                composition = {
                    'apiVersion': 'kustomize.config.k8s.io/v1beta1',
                    'kind': 'Kustomization',
                    'metadata': {'name': 'test-composition'},
                    'resources': [str(overlay_dir.relative_to(self.overlays_dir)) for overlay_dir in overlay_dirs]
                }
                
                with open(kustomization_path, 'w') as f:
                    yaml.dump(composition, f)
                
                # Test build
                result = subprocess.run(
                    ['kustomize', 'build', str(temp_path)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.overlays_dir
                )
                
                if result.returncode != 0:
                    self._add_test_failure(test_name, f"Multiple composition failed: {result.stderr}")
                    return False
            
            self._add_test_success(test_name, "Multiple composition successful")
            return True
            
        except Exception as e:
            self._add_test_failure(test_name, f"Multiple composition error: {e}")
            return False

    def _test_overlay_conflicts(self) -> bool:
        """Test overlay conflict detection"""
        test_name = "overlay_conflicts"
        
        try:
            # This is a simplified conflict test
            # In a real implementation, you'd check for resource name conflicts, etc.
            
            overlay_dirs = self._find_overlay_directories()
            resource_names = set()
            
            for overlay_dir in overlay_dirs:
                kustomization_path = overlay_dir / 'kustomization.yaml'
                with open(kustomization_path, 'r') as f:
                    kustomization = yaml.safe_load(f)
                
                # Check for name conflicts
                name = kustomization.get('metadata', {}).get('name', '')
                if name in resource_names:
                    self._add_test_failure(test_name, f"Name conflict detected: {name}")
                    return False
                resource_names.add(name)
            
            self._add_test_success(test_name, "No overlay conflicts detected")
            return True
            
        except Exception as e:
            self._add_test_failure(test_name, f"Conflict detection error: {e}")
            return False

    def _test_overlay_dependencies(self) -> bool:
        """Test overlay dependencies"""
        test_name = "overlay_dependencies"
        
        try:
            overlay_dirs = self._find_overlay_directories()
            
            for overlay_dir in overlay_dirs:
                metadata_path = overlay_dir / 'overlay-metadata.yaml'
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = yaml.safe_load(f)
                    
                    dependencies = metadata.get('dependencies', [])
                    for dep in dependencies:
                        dep_name = dep.get('name', '')
                        if dep_name:
                            # Check if dependency exists
                            dep_found = False
                            for other_dir in overlay_dirs:
                                other_metadata = other_dir / 'overlay-metadata.yaml'
                                if other_metadata.exists():
                                    with open(other_metadata, 'r') as f:
                                        other_meta = yaml.safe_load(f)
                                    if other_meta.get('name') == dep_name:
                                        dep_found = True
                                        break
                            
                            if not dep_found:
                                self._add_test_failure(test_name, f"Dependency not found: {dep_name}")
                                return False
            
            self._add_test_success(test_name, "All dependencies resolved")
            return True
            
        except Exception as e:
            self._add_test_failure(test_name, f"Dependency test error: {e}")
            return False

    def _validate_version_format(self, version: str) -> bool:
        """Validate semantic version format"""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))

    def _add_test_success(self, test_name: str, message: str):
        """Add successful test result"""
        self.test_results.append({
            'name': test_name,
            'status': 'PASS',
            'message': message,
            'timestamp': time.time()
        })

    def _add_test_failure(self, test_name: str, message: str):
        """Add failed test result"""
        self.test_results.append({
            'name': test_name,
            'status': 'FAIL',
            'message': message,
            'timestamp': time.time()
        })
        self.failed_tests.append(test_name)

    def _print_test_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("OVERLAY TESTING SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = total_tests - len(self.failed_tests)
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_core/automation/testing/total_tests*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results:
                if test['status'] == 'FAIL':
                    print(f"  - {test['name']}: {test['message']}")
        
        print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description='Test overlays structure and composition')
    parser.add_argument('overlays_dir', help='Overlays directory path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = OverlayTester(args.overlays_dir)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
