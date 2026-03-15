#!/usr/bin/env python3
"""
GitOps Pull Request Generator Script
Creates infrastructure changes via GitOps pull requests for Flux/Argo CD deployments.
"""

import json
import subprocess
import sys
import os
import tempfile
from typing import Dict, List, Optional
from datetime import datetime


class GitOpsPRGenerator:
    def __init__(self, repo_path: str, git_user: str = "ai-agent", git_email: str = "ai-agent@company.com"):
        self.repo_path = repo_path
        self.git_user = git_user
        self.git_email = git_email
        
    def validate_yaml_syntax(self, yaml_content: str) -> bool:
        """Validate YAML syntax using kubectl"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(yaml_content)
                f.flush()
                
                result = subprocess.run(
                    ['kubectl', 'apply', '--dry-run=client', '-f', f.name],
                    capture_output=True, text=True, timeout=30
                )
                os.unlink(f.name)
                return result.returncode == 0
        except Exception as e:
            print(f"YAML validation error: {e}")
            return False
    
    def create_feature_branch(self, branch_name: str) -> bool:
        """Create and checkout a new feature branch"""
        try:
            subprocess.run(['git', 'checkout', '-b', branch_name], 
                         cwd=self.repo_path, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to create branch: {e}")
            return False
    
    def commit_changes(self, commit_message: str, files: List[str]) -> bool:
        """Stage and commit changes"""
        try:
            # Configure git user
            subprocess.run(['git', 'config', 'user.name', self.git_user], 
                         cwd=self.repo_path, check=True)
            subprocess.run(['git', 'config', 'user.email', self.git_email], 
                         cwd=self.repo_path, check=True)
            
            # Stage files
            for file in files:
                subprocess.run(['git', 'add', file], cwd=self.repo_path, check=True)
            
            # Commit
            subprocess.run(['git', 'commit', '-m', commit_message], 
                         cwd=self.repo_path, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to commit changes: {e}")
            return False
    
    def create_pull_request(self, branch_name: str, pr_title: str, pr_body: str, 
                          base_branch: str = "main") -> bool:
        """Create pull request (requires gh CLI or git provider API)"""
        try:
            # Push branch
            subprocess.run(['git', 'push', 'origin', branch_name], 
                         cwd=self.repo_path, check=True)
            
            # Create PR using GitHub CLI if available
            result = subprocess.run([
                'gh', 'pr', 'create', 
                '--title', pr_title,
                '--body', pr_body,
                '--base', base_branch,
                '--head', branch_name
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"PR created successfully: {result.stdout.strip()}")
                return True
            else:
                print(f"Failed to create PR: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Failed to create PR: {e}")
            return False
    
    def generate_manifest_patch(self, patch_request: Dict) -> Dict:
        """Generate YAML manifest patches based on request"""
        patches = []
        
        for change in patch_request.get('changes', []):
            resource_type = change.get('resource_type')
            resource_name = change.get('resource_name')
            namespace = change.get('namespace', 'default')
            modifications = change.get('modifications', {})
            
            patch = {
                'resource_type': resource_type,
                'resource_name': resource_name,
                'namespace': namespace,
                'modifications': modifications,
                'yaml_patch': self._generate_yaml_patch(change)
            }
            patches.append(patch)
        
        return {'patches': patches}
    
    def _generate_yaml_patch(self, change: Dict) -> str:
        """Generate YAML patch content"""
        resource_type = change.get('resource_type', '')
        resource_name = change.get('resource_name', '')
        namespace = change.get('namespace', 'default')
        modifications = change.get('modifications', {})
        
        # Basic YAML structure generation
        yaml_lines = [
            f"apiVersion: v1",
            f"kind: {resource_type}",
            f"metadata:",
            f"  name: {resource_name}",
            f"  namespace: {namespace}",
            f"spec:"
        ]
        
        # Add modifications
        for key, value in modifications.items():
            if isinstance(value, dict):
                yaml_lines.append(f"  {key}:")
                for sub_key, sub_value in value.items():
                    yaml_lines.append(f"    {sub_key}: {sub_value}")
            else:
                yaml_lines.append(f"  {key}: {value}")
        
        return '\n'.join(yaml_lines)
    
    def create_infrastructure_pr(self, patch_request: Dict) -> Dict:
        """Main function to create infrastructure PR"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"ai-infrastructure-{timestamp}"
        
        # Generate patches
        patches = self.generate_manifest_patch(patch_request)
        
        # Validate patches
        for patch in patches['patches']:
            if not self.validate_yaml_syntax(patch['yaml_patch']):
                return {
                    'success': False,
                    'error': f"YAML validation failed for {patch['resource_name']}"
                }
        
        # Create branch
        if not self.create_feature_branch(branch_name):
            return {'success': False, 'error': 'Failed to create branch'}
        
        # Write patch files
        files_created = []
        for i, patch in enumerate(patches['patches']):
            filename = f"{patch['resource_type']}-{patch['resource_name']}.yaml"
            filepath = os.path.join(self.repo_path, filename)
            
            with open(filepath, 'w') as f:
                f.write(patch['yaml_patch'])
            files_created.append(filepath)
        
        # Commit changes
        commit_message = f"AI: Infrastructure update for {patch_request.get('purpose', 'automated remediation')}"
        if not self.commit_changes(commit_message, files_created):
            return {'success': False, 'error': 'Failed to commit changes'}
        
        # Create PR
        pr_title = f"AI: Infrastructure Update - {patch_request.get('purpose', 'Automated Change')}"
        pr_body = self._generate_pr_description(patch_request, patches)
        
        pr_created = self.create_pull_request(branch_name, pr_title, pr_body)
        
        return {
            'success': pr_created,
            'branch': branch_name,
            'files': files_created,
            'pr_title': pr_title,
            'patches': patches
        }
    
    def _generate_pr_description(self, patch_request: Dict, patches: Dict) -> str:
        """Generate detailed PR description"""
        description = [
            f"## Infrastructure Update",
            f"",
            f"**Purpose**: {patch_request.get('purpose', 'Automated infrastructure change')}",
            f"**Trigger**: {patch_request.get('trigger', 'AI agent automation')}",
            f"**Impact**: {patch_request.get('impact', 'Resource configuration modification')}",
            f"",
            f"### Changes",
            f""
        ]
        
        for patch in patches['patches']:
            description.extend([
                f"#### {patch['resource_type']}/{patch['resource_name']}",
                f"- Namespace: {patch['namespace']}",
                f"- Modifications: {len(patch['modifications'])} items",
                f""
            ])
        
        description.extend([
            f"### Rollback Instructions",
            f"1. If issues occur, revert this PR",
            f"2. Check cluster state: `kubectl get all -n <namespace>`",
            f"3. Monitor application health for 5 minutes",
            f"",
            f"### Validation Steps",
            f"1. Resources should apply without errors",
            f"2. Applications should remain healthy",
            f"3. Monitor metrics for 5 minutes post-deployment",
            f"",
            f"---",
            f"*This PR was generated by AI agent for automated infrastructure management*"
        ])
        
        return '\n'.join(description)


def main():
    """Example usage"""
    if len(sys.argv) < 2:
        print("Usage: python create_pr.py <patch_request_json>")
        sys.exit(1)
    
    try:
        patch_request = json.loads(sys.argv[1])
        repo_path = os.getcwd()
        
        generator = GitOpsPRGenerator(repo_path)
        result = generator.create_infrastructure_pr(patch_request)
        
        print(json.dumps(result, indent=2))
        
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
