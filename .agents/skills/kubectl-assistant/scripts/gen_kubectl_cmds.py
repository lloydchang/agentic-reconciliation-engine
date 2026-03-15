#!/usr/bin/env python3
"""
Kubectl Command Generator Script
Generates and validates kubectl commands for Kubernetes operations.
"""

import json
import subprocess
import sys
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class OperationType(Enum):
    GET = "get"
    DESCRIBE = "describe"
    LOGS = "logs"
    CREATE = "create"
    DELETE = "delete"
    APPLY = "apply"
    EDIT = "edit"
    EXEC = "exec"
    PORT_FORWARD = "port-forward"
    SCALE = "scale"
    ROLLOUT = "rollout"
    TOP = "top"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KubectlCommandGenerator:
    def __init__(self):
        self.risk_levels = {
            OperationType.DELETE: RiskLevel.HIGH,
            OperationType.CREATE: RiskLevel.MEDIUM,
            OperationType.APPLY: RiskLevel.MEDIUM,
            OperationType.EDIT: RiskLevel.MEDIUM,
            OperationType.EXEC: RiskLevel.MEDIUM,
            OperationType.SCALE: RiskLevel.MEDIUM,
            OperationType.ROLLOUT: RiskLevel.MEDIUM,
            OperationType.PORT_FORWARD: RiskLevel.LOW,
            OperationType.GET: RiskLevel.LOW,
            OperationType.DESCRIBE: RiskLevel.LOW,
            OperationType.LOGS: RiskLevel.LOW,
            OperationType.TOP: RiskLevel.LOW,
        }
        
        self.resource_shortcuts = {
            'po': 'pods',
            'svc': 'services',
            'deploy': 'deployments',
            'rs': 'replicasets',
            'sts': 'statefulsets',
            'ds': 'daemonsets',
            'ing': 'ingresses',
            'cm': 'configmaps',
            'sec': 'secrets',
            'sa': 'serviceaccounts',
            'ns': 'namespaces',
            'pv': 'persistentvolumes',
            'pvc': 'persistentvolumeclaims',
            'no': 'nodes',
            'ev': 'events'
        }
    
    def parse_request(self, request: str) -> Dict:
        """Parse natural language request into structured command"""
        request_lower = request.lower()
        
        # Identify operation type
        operation = self._identify_operation(request_lower)
        
        # Identify resource type
        resource_type = self._identify_resource_type(request_lower)
        
        # Extract resource name
        resource_name = self._extract_resource_name(request_lower, resource_type)
        
        # Extract namespace
        namespace = self._extract_namespace(request_lower)
        
        # Extract additional flags and options
        flags = self._extract_flags(request_lower, operation)
        
        # Extract selectors
        selectors = self._extract_selectors(request_lower)
        
        return {
            'operation': operation,
            'resource_type': resource_type,
            'resource_name': resource_name,
            'namespace': namespace,
            'flags': flags,
            'selectors': selectors,
            'risk_level': self.risk_levels.get(operation, RiskLevel.MEDIUM)
        }
    
    def _identify_operation(self, request: str) -> OperationType:
        """Identify the kubectl operation from request"""
        operation_patterns = {
            OperationType.GET: ['get', 'show', 'list', 'display', 'view'],
            OperationType.DESCRIBE: ['describe', 'details', 'info', 'explain'],
            OperationType.LOGS: ['logs', 'log', 'output'],
            OperationType.CREATE: ['create', 'new', 'add', 'deploy'],
            OperationType.DELETE: ['delete', 'remove', 'del', 'rm'],
            OperationType.APPLY: ['apply', 'update', 'modify'],
            OperationType.EDIT: ['edit', 'modify', 'change'],
            OperationType.EXEC: ['exec', 'execute', 'run', 'shell'],
            OperationType.PORT_FORWARD: ['port-forward', 'forward', 'pf'],
            OperationType.SCALE: ['scale', 'resize'],
            OperationType.ROLLOUT: ['rollout', 'restart', 'undo', 'status'],
            OperationType.TOP: ['top', 'metrics', 'usage']
        }
        
        for op, patterns in operation_patterns.items():
            if any(pattern in request for pattern in patterns):
                return op
        
        return OperationType.GET  # Default
    
    def _identify_resource_type(self, request: str) -> str:
        """Identify Kubernetes resource type"""
        for shortcut, full_name in self.resource_shortcuts.items():
            if shortcut in request or full_name in request:
                return full_name
        
        # Check for full resource names
        resource_types = [
            'pods', 'services', 'deployments', 'replicasets', 'statefulsets',
            'daemonsets', 'ingresses', 'configmaps', 'secrets', 'serviceaccounts',
            'namespaces', 'persistentvolumes', 'persistentvolumeclaims',
            'nodes', 'events', 'jobs', 'cronjobs'
        ]
        
        for resource in resource_types:
            if resource in request:
                return resource
        
        return 'pods'  # Default
    
    def _extract_resource_name(self, request: str, resource_type: str) -> Optional[str]:
        """Extract specific resource name from request"""
        # Look for patterns like "pod my-pod" or "deployment nginx"
        patterns = [
            rf'{resource_type}\s+(\S+)',
            rf'{resource_type[:-1]}\s+(\S+)',  # singular form
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_namespace(self, request: str) -> Optional[str]:
        """Extract namespace from request"""
        namespace_patterns = [
            r'namespace\s+(\S+)',
            r'ns\s+(\S+)',
            r'in\s+(\S+)\s+namespace',
            r'(-n|--namespace)\s+(\S+)'
        ]
        
        for pattern in namespace_patterns:
            match = re.search(pattern, request)
            if match:
                # Handle patterns with and without flags
                return match.group(1) if len(match.groups()) == 1 else match.group(2)
        
        return None
    
    def _extract_flags(self, request: str, operation: OperationType) -> Dict[str, str]:
        """Extract command flags based on operation type"""
        flags = {}
        
        # Common flags
        if 'watch' in request or 'w' in request:
            flags['watch'] = 'true'
        
        if 'wide' in request:
            flags['wide'] = 'true'
        
        if 'all' in request or 'a' in request:
            flags['all'] = 'true'
        
        # Operation-specific flags
        if operation == OperationType.LOGS:
            if 'follow' in request or 'f' in request:
                flags['follow'] = 'true'
            if 'tail' in request:
                tail_match = re.search(r'tail\s+(\d+)', request)
                if tail_match:
                    flags['tail'] = tail_match.group(1)
            if 'previous' in request or 'p' in request:
                flags['previous'] = 'true'
        
        if operation == OperationType.DELETE:
            if 'force' in request:
                flags['force'] = 'true'
            if 'grace' in request:
                grace_match = re.search(r'grace.*?(\d+)', request)
                if grace_match:
                    flags['grace-period'] = grace_match.group(1)
        
        return flags
    
    def _extract_selectors(self, request: str) -> Dict[str, str]:
        """Extract label selectors from request"""
        selectors = {}
        
        # Look for label patterns
        label_patterns = [
            r'label\s+(\S+)=(\S+)',
            r'(\S+)=(\S+)',
            r'with\s+(\S+)\s+(\S+)'
        ]
        
        for pattern in label_patterns:
            matches = re.findall(pattern, request)
            for match in matches:
                if len(match) == 2:
                    key, value = match
                    # Skip common words that aren't labels
                    if key not in ['namespace', 'in', 'with', 'the', 'and', 'or']:
                        selectors[key] = value
        
        return selectors
    
    def generate_command(self, parsed_request: Dict) -> str:
        """Generate kubectl command from parsed request"""
        parts = ['kubectl']
        
        # Add operation
        parts.append(parsed_request['operation'].value)
        
        # Add resource type and name
        if parsed_request['resource_name']:
            parts.append(f"{parsed_request['resource_type']}/{parsed_request['resource_name']}")
        else:
            parts.append(parsed_request['resource_type'])
        
        # Add namespace
        if parsed_request['namespace']:
            parts.extend(['-n', parsed_request['namespace']])
        
        # Add selectors
        for key, value in parsed_request['selectors'].items():
            parts.extend(['-l', f'{key}={value}'])
        
        # Add flags
        for flag, value in parsed_request['flags'].items():
            if len(flag) == 1:
                parts.append(f'-{flag}')
            else:
                if value == 'true':
                    parts.append(f'--{flag}')
                else:
                    parts.extend([f'--{flag}', value])
        
        return ' '.join(parts)
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate kubectl command syntax"""
        try:
            # Use kubectl --dry-run=client for validation
            result = subprocess.run(
                command.split() + ['--dry-run=client'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Command syntax is valid"
            else:
                return False, f"Validation failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Command validation timed out"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_safety_warnings(self, parsed_request: Dict) -> List[str]:
        """Generate safety warnings based on operation and context"""
        warnings = []
        risk = parsed_request['risk_level']
        
        if risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            warnings.append("⚠️  HIGH RISK OPERATION")
            
        if parsed_request['operation'] == OperationType.DELETE:
            warnings.append("This will permanently delete resources")
            if not parsed_request['resource_name']:
                warnings.append("No specific resource named - this may delete multiple resources")
        
        if parsed_request['operation'] == OperationType.APPLY:
            warnings.append("This will modify cluster state")
            warnings.append("Review changes with --dry-run first")
        
        if parsed_request['namespace'] == 'default' and risk != RiskLevel.LOW:
            warnings.append("Operating in default namespace - verify this is intended")
        
        if parsed_request['operation'] == OperationType.EXEC:
            warnings.append("Executing commands in containers")
            warnings.append("Ensure commands are safe for production")
        
        return warnings
    
    def get_alternatives(self, parsed_request: Dict) -> List[str]:
        """Suggest alternative commands"""
        alternatives = []
        operation = parsed_request['operation']
        
        if operation == OperationType.DELETE:
            alternatives.append("Consider 'kubectl scale deployment <name> --replicas=0' instead")
        
        if operation == OperationType.GET and not parsed_request['flags'].get('watch'):
            alternatives.append("Add '--watch' for real-time monitoring")
        
        if operation == OperationType.LOGS and not parsed_request['flags'].get('follow'):
            alternatives.append("Add '-f' to follow logs in real-time")
        
        if parsed_request['resource_type'] == 'pods' and operation == OperationType.GET:
            alternatives.append("Consider 'kubectl get pods -o wide' for more information")
        
        return alternatives
    
    def explain_command(self, parsed_request: Dict, command: str) -> str:
        """Generate detailed explanation of the command"""
        operation = parsed_request['operation']
        resource_type = parsed_request['resource_type']
        
        explanations = {
            OperationType.GET: f"This command will list {resource_type}",
            OperationType.DESCRIBE: f"This command will show detailed information about {resource_type}",
            OperationType.LOGS: f"This command will show logs from {resource_type}",
            OperationType.CREATE: f"This command will create a new {resource_type[:-1] if resource_type.endswith('s') else resource_type}",
            OperationType.DELETE: f"This command will delete {resource_type}",
            OperationType.APPLY: f"This command will apply configuration changes to {resource_type}",
            OperationType.EDIT: f"This command will open an editor to modify {resource_type}",
            OperationType.EXEC: f"This command will execute commands in {resource_type}",
            OperationType.SCALE: f"This command will scale {resource_type}",
            OperationType.ROLLOUT: f"This command will manage rollout status for {resource_type}",
            OperationType.TOP: f"This command will show resource usage for {resource_type}",
        }
        
        explanation = explanations.get(operation, f"This command will perform {operation.value} on {resource_type}")
        
        # Add context-specific details
        if parsed_request['namespace']:
            explanation += f" in the '{parsed_request['namespace']}' namespace"
        
        if parsed_request['resource_name']:
            explanation += f" named '{parsed_request['resource_name']}'"
        
        if parsed_request['selectors']:
            selector_str = ', '.join([f"{k}={v}" for k, v in parsed_request['selectors'].items()])
            explanation += f" with selectors {selector_str}"
        
        return explanation


def main():
    """Example usage"""
    if len(sys.argv) < 2:
        print("Usage: python gen_kubectl_cmds.py <natural_language_request>")
        print("Example: python gen_kubectl_cmds.py 'get all pods in production namespace'")
        sys.exit(1)
    
    try:
        request = ' '.join(sys.argv[1:])
        generator = KubectlCommandGenerator()
        
        # Parse request
        parsed = generator.parse_request(request)
        
        # Generate command
        command = generator.generate_command(parsed)
        
        # Validate command
        is_valid, validation_msg = generator.validate_command(command)
        
        # Get safety warnings
        warnings = generator.get_safety_warnings(parsed)
        
        # Get alternatives
        alternatives = generator.get_alternatives(parsed)
        
        # Explain command
        explanation = generator.explain_command(parsed, command)
        
        result = {
            'request': request,
            'command': command,
            'valid': is_valid,
            'validation_message': validation_msg,
            'explanation': explanation,
            'risk_level': parsed['risk_level'].value,
            'warnings': warnings,
            'alternatives': alternatives,
            'parsed_request': parsed
        }
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
