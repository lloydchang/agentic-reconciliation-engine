#!/usr/bin/env python3
"""
Infrastructure Provisioning Script

Multi-cloud automation for infrastructure provisioning across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class ProvisioningStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"

class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORKING = "networking"
    DATABASE = "database"
    SECURITY = "security"
    MONITORING = "monitoring"

@dataclass
class ProvisioningRequest:
    request_id: str
    resource_name: str
    resource_type: ResourceType
    provider: str
    region: str
    configuration: Dict[str, Any]
    tags: Dict[str, str]
    requested_by: str
    requested_at: datetime
    priority: str  # low, medium, high, critical

@dataclass
class ProvisioningResult:
    request_id: str
    resource_id: Optional[str]
    status: ProvisioningStatus
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    resource_details: Optional[Dict[str, Any]]
    cost_estimate: float

@dataclass
class ProvisioningTemplate:
    template_id: str
    template_name: str
    description: str
    provider: str
    resource_type: ResourceType
    configuration_schema: Dict[str, Any]
    default_configuration: Dict[str, Any]
    cost_estimate: float
    estimated_provisioning_time: timedelta

class InfrastructureProvisioner:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.templates = {}
        self.requests = {}
        self.results = {}
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load provisioning configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'provisioning_settings': {
                'auto_approve_safe_requests': True,
                'require_approval_for_expensive': True,
                'cost_approval_threshold': 1000.0,
                'enable_rollback': True,
                'validation_enabled': True,
                'dry_run_by_default': False
            },
            'limits': {
                'max_concurrent_provisioning': 5,
                'provisioning_timeout_minutes': 30,
                'retry_attempts': 3,
                'max_resources_per_request': 10
            }
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def load_templates(self, templates_file: Optional[str] = None) -> Dict[str, ProvisioningTemplate]:
        """Load provisioning templates"""
        logger.info("Loading provisioning templates")
        
        # Default templates
        default_templates = {
            'aws-ec2-small': ProvisioningTemplate(
                template_id='aws-ec2-small',
                template_name='AWS Small EC2 Instance',
                description='Small EC2 instance for development/testing',
                provider='aws',
                resource_type=ResourceType.COMPUTE,
                configuration_schema={
                    'instance_type': {'type': 'string', 'enum': ['t3.micro', 't3.small', 't3.medium']},
                    'ami_id': {'type': 'string'},
                    'key_name': {'type': 'string', 'required': False},
                    'security_groups': {'type': 'array', 'required': False},
                    'subnet_id': {'type': 'string', 'required': False},
                    'user_data': {'type': 'string', 'required': False}
                },
                default_configuration={
                    'instance_type': 't3.micro',
                    'ami_id': 'ami-12345678'
                },
                cost_estimate=15.32,  # Monthly cost
                estimated_provisioning_time=timedelta(minutes=5)
            ),
            'aws-ebs-standard': ProvisioningTemplate(
                template_id='aws-ebs-standard',
                template_name='AWS Standard EBS Volume',
                description='Standard EBS volume for general storage',
                provider='aws',
                resource_type=ResourceType.STORAGE,
                configuration_schema={
                    'size_gb': {'type': 'integer', 'min': 1, 'max': 16384},
                    'volume_type': {'type': 'string', 'enum': ['gp2', 'gp3', 'io1']},
                    'iops': {'type': 'integer', 'required': False},
                    'throughput': {'type': 'integer', 'required': False},
                    'availability_zone': {'type': 'string', 'required': False}
                },
                default_configuration={
                    'size_gb': 100,
                    'volume_type': 'gp3'
                },
                cost_estimate=8.0,  # Monthly cost for 100GB
                estimated_provisioning_time=timedelta(minutes=2)
            ),
            'azure-vm-small': ProvisioningTemplate(
                template_id='azure-vm-small',
                template_name='Azure Small VM',
                description='Small Azure VM for development/testing',
                provider='azure',
                resource_type=ResourceType.COMPUTE,
                configuration_schema={
                    'vm_size': {'type': 'string', 'enum': ['Standard_B1s', 'Standard_B2s']},
                    'image_reference': {'type': 'object'},
                    'admin_username': {'type': 'string'},
                    'admin_password': {'type': 'string', 'required': False},
                    'network_interface': {'type': 'object', 'required': False}
                },
                default_configuration={
                    'vm_size': 'Standard_B1s',
                    'admin_username': 'azureuser'
                },
                cost_estimate=14.40,  # Monthly cost
                estimated_provisioning_time=timedelta(minutes=7)
            ),
            'gcp-vm-small': ProvisioningTemplate(
                template_id='gcp-vm-small',
                template_name='GCP Small VM',
                description='Small GCP VM for development/testing',
                provider='gcp',
                resource_type=ResourceType.COMPUTE,
                configuration_schema={
                    'machine_type': {'type': 'string', 'enum': ['e2-micro', 'e2-small', 'e2-medium']},
                    'source_image': {'type': 'string'},
                    'zone': {'type': 'string', 'required': False},
                    'network_interfaces': {'type': 'array', 'required': False}
                },
                default_configuration={
                    'machine_type': 'e2-micro',
                    'source_image': 'ubuntu-2004-focal-v20220101'
                },
                cost_estimate=4.86,  # Monthly cost
                estimated_provisioning_time=timedelta(minutes=6)
            )
        }
        
        # Load custom templates from file if provided
        if templates_file:
            try:
                with open(templates_file, 'r') as f:
                    custom_templates = json.load(f)
                
                for template_id, template_data in custom_templates.items():
                    template = ProvisioningTemplate(
                        template_id=template_id,
                        template_name=template_data['template_name'],
                        description=template_data['description'],
                        provider=template_data['provider'],
                        resource_type=ResourceType(template_data['resource_type']),
                        configuration_schema=template_data['configuration_schema'],
                        default_configuration=template_data['default_configuration'],
                        cost_estimate=template_data['cost_estimate'],
                        estimated_provisioning_time=timedelta(minutes=template_data['estimated_provisioning_time_minutes'])
                    )
                    default_templates[template_id] = template
                    
            except Exception as e:
                logger.warning(f"Failed to load custom templates: {e}")
        
        self.templates = default_templates
        logger.info(f"Loaded {len(self.templates)} provisioning templates")
        
        return self.templates
    
    def create_provisioning_request(self, resource_name: str, resource_type: ResourceType,
                                   provider: str, configuration: Dict[str, Any],
                                   tags: Optional[Dict[str, str]] = None,
                                   requested_by: str = "system",
                                   priority: str = "medium",
                                   template_id: Optional[str] = None) -> ProvisioningRequest:
        """Create a provisioning request"""
        logger.info(f"Creating provisioning request for {resource_name}")
        
        request_id = f"req-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{resource_name.lower().replace(' ', '-')}"
        
        # Validate configuration
        if template_id:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Merge template defaults with provided configuration
            merged_config = template.default_configuration.copy()
            merged_config.update(configuration)
            configuration = merged_config
            
            # Validate against schema
            self._validate_configuration(configuration, template.configuration_schema)
            
            # Use template cost estimate if not provided
            cost_estimate = template.cost_estimate
        else:
            cost_estimate = self._estimate_cost(resource_type, provider, configuration)
        
        # Check if approval is required
        if self._requires_approval(cost_estimate, priority):
            logger.info(f"Request {request_id} requires approval due to cost or priority")
        
        request = ProvisioningRequest(
            request_id=request_id,
            resource_name=resource_name,
            resource_type=resource_type,
            provider=provider,
            region=self.config['providers'][provider]['region'],
            configuration=configuration,
            tags=tags or {},
            requested_by=requested_by,
            requested_at=datetime.utcnow(),
            priority=priority
        )
        
        self.requests[request_id] = request
        return request
    
    def provision_infrastructure(self, request: ProvisioningRequest, 
                                dry_run: bool = False) -> ProvisioningResult:
        """Provision infrastructure based on request"""
        logger.info(f"Provisioning infrastructure for request {request.request_id}")
        
        # Initialize provider handler
        handler = self._get_provider_handler(request.provider)
        if not handler.initialize_client():
            raise RuntimeError(f"Failed to initialize {request.provider} handler")
        
        # Create provisioning result
        result = ProvisioningResult(
            request_id=request.request_id,
            resource_id=None,
            status=ProvisioningStatus.PENDING,
            started_at=datetime.utcnow(),
            completed_at=None,
            error_message=None,
            resource_details=None,
            cost_estimate=self._estimate_cost(request.resource_type, request.provider, request.configuration)
        )
        
        try:
            if dry_run:
                logger.info(f"DRY RUN: Would provision {request.resource_name}")
                result.status = ProvisioningStatus.COMPLETED
                result.completed_at = datetime.utcnow()
                result.resource_id = f"dry-run-{request.request_id}"
                result.resource_details = {
                    'dry_run': True,
                    'configuration': request.configuration,
                    'estimated_cost': result.cost_estimate
                }
            else:
                # Validate request
                if self.config['provisioning_settings']['validation_enabled']:
                    self._validate_request(request)
                
                # Provision resource
                result.status = ProvisioningStatus.IN_PROGRESS
                
                provisioning_result = handler.provision_resource(
                    request.resource_type.value,
                    request.resource_name,
                    request.configuration,
                    request.tags
                )
                
                if provisioning_result.get('success', False):
                    result.status = ProvisioningStatus.COMPLETED
                    result.completed_at = datetime.utcnow()
                    result.resource_id = provisioning_result.get('resource_id')
                    result.resource_details = provisioning_result.get('resource_details', {})
                    
                    logger.info(f"Successfully provisioned {request.resource_name} with ID {result.resource_id}")
                else:
                    result.status = ProvisioningStatus.FAILED
                    result.completed_at = datetime.utcnow()
                    result.error_message = provisioning_result.get('error', 'Unknown error')
                    
                    logger.error(f"Failed to provision {request.resource_name}: {result.error_message}")
                    
                    # Rollback if enabled and failed
                    if self.config['provisioning_settings']['enable_rollback'] and result.resource_id:
                        self._rollback_provisioning(handler, request, result)
        
        except Exception as e:
            logger.error(f"Provisioning failed for {request.request_id}: {e}")
            result.status = ProvisioningStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.error_message = str(e)
        
        self.results[request.request_id] = result
        return result
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific provisioning handler"""
        from infrastructure_provisioning_handler import get_provisioning_handler
        region = self.config['providers'][provider]['region']
        return get_provisioning_handler(provider, region)
    
    def _validate_configuration(self, configuration: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Validate configuration against schema"""
        # Simplified validation
        for field_name, field_schema in schema.items():
            if field_schema.get('required', False) and field_name not in configuration:
                raise ValueError(f"Required field {field_name} is missing")
            
            if field_name in configuration:
                field_value = configuration[field_name]
                field_type = field_schema.get('type')
                
                if field_type == 'string' and not isinstance(field_value, str):
                    raise ValueError(f"Field {field_name} must be a string")
                elif field_type == 'integer' and not isinstance(field_value, int):
                    raise ValueError(f"Field {field_name} must be an integer")
                elif field_type == 'array' and not isinstance(field_value, list):
                    raise ValueError(f"Field {field_name} must be an array")
                
                # Check enum values
                if 'enum' in field_schema and field_value not in field_schema['enum']:
                    raise ValueError(f"Field {field_name} must be one of {field_schema['enum']}")
                
                # Check ranges
                if field_type == 'integer':
                    if 'min' in field_schema and field_value < field_schema['min']:
                        raise ValueError(f"Field {field_name} must be >= {field_schema['min']}")
                    if 'max' in field_schema and field_value > field_schema['max']:
                        raise ValueError(f"Field {field_name} must be <= {field_schema['max']}")
    
    def _estimate_cost(self, resource_type: ResourceType, provider: str, configuration: Dict[str, Any]) -> float:
        """Estimate monthly cost for resource"""
        # Simplified cost estimation
        if provider == 'aws':
            if resource_type == ResourceType.COMPUTE:
                instance_type = configuration.get('instance_type', 't3.micro')
                cost_mapping = {
                    't3.micro': 7.66, 't3.small': 15.32, 't3.medium': 30.64, 't3.large': 61.28,
                    'm5.large': 69.12, 'm5.xlarge': 138.24, 'm5.2xlarge': 276.48,
                    'c5.large': 68.46, 'c5.xlarge': 136.92, 'c5.2xlarge': 273.84
                }
                return cost_mapping.get(instance_type, 50.0)
            
            elif resource_type == ResourceType.STORAGE:
                size_gb = configuration.get('size_gb', 100)
                volume_type = configuration.get('volume_type', 'gp3')
                cost_per_gb = {
                    'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'st1': 0.045, 'sc1': 0.025
                }
                return size_gb * cost_per_gb.get(volume_type, 0.10)
            
            elif resource_type == ResourceType.DATABASE:
                db_class = configuration.get('db_instance_class', 'db.t3.micro')
                cost_mapping = {
                    'db.t3.micro': 11.62, 'db.t3.small': 23.24, 'db.t3.medium': 46.49,
                    'db.r5.large': 173.52, 'db.r5.xlarge': 347.04, 'db.r5.2xlarge': 694.08
                }
                return cost_mapping.get(db_class, 100.0)
        
        elif provider == 'azure':
            if resource_type == ResourceType.COMPUTE:
                vm_size = configuration.get('vm_size', 'Standard_B1s')
                cost_mapping = {
                    'Standard_B1s': 7.30, 'Standard_B2s': 29.20, 'Standard_B4ms': 58.40,
                    'Standard_D2s_v3': 70.08, 'Standard_D4s_v3': 140.16
                }
                return cost_mapping.get(vm_size, 50.0)
        
        elif provider == 'gcp':
            if resource_type == ResourceType.COMPUTE:
                machine_type = configuration.get('machine_type', 'e2-micro')
                cost_mapping = {
                    'e2-micro': 4.86, 'e2-small': 9.72, 'e2-medium': 19.44, 'e2-standard-2': 38.88,
                    'n1-standard-2': 53.06, 'n1-standard-4': 106.12
                }
                return cost_mapping.get(machine_type, 50.0)
        
        return 100.0  # Default cost estimate
    
    def _requires_approval(self, cost_estimate: float, priority: str) -> bool:
        """Check if request requires approval"""
        if not self.config['provisioning_settings']['require_approval_for_expensive']:
            return False
        
        threshold = self.config['provisioning_settings']['cost_approval_threshold']
        return cost_estimate > threshold or priority == 'critical'
    
    def _validate_request(self, request: ProvisioningRequest) -> None:
        """Validate provisioning request"""
        # Check provider availability
        if request.provider not in self.config['providers']:
            raise ValueError(f"Provider {request.provider} not configured")
        
        if not self.config['providers'][request.provider]['enabled']:
            raise ValueError(f"Provider {request.provider} is disabled")
        
        # Check resource limits
        if len(request.configuration) > self.config['limits']['max_resources_per_request']:
            raise ValueError(f"Too many resources in request (max: {self.config['limits']['max_resources_per_request']})")
        
        # Check for required fields based on resource type
        if request.resource_type == ResourceType.COMPUTE:
            required_fields = ['instance_type'] if request.provider == 'aws' else ['vm_size']
            for field in required_fields:
                if field not in request.configuration:
                    raise ValueError(f"Required field {field} missing for compute resource")
    
    def _rollback_provisioning(self, handler, request: ProvisioningRequest, result: ProvisioningResult) -> None:
        """Rollback failed provisioning"""
        logger.info(f"Rolling back provisioning for {request.request_id}")
        
        try:
            result.status = ProvisioningStatus.ROLLING_BACK
            
            rollback_result = handler.delete_resource(
                request.resource_type.value,
                result.resource_id
            )
            
            if rollback_result.get('success', False):
                logger.info(f"Successfully rolled back {result.resource_id}")
            else:
                logger.error(f"Rollback failed: {rollback_result.get('error')}")
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
    
    def batch_provision(self, requests: List[ProvisioningRequest], 
                        dry_run: bool = False) -> List[ProvisioningResult]:
        """Provision multiple resources in batch"""
        logger.info(f"Batch provisioning {len(requests)} requests")
        
        results = []
        
        # Sort requests by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_requests = sorted(requests, key=lambda x: priority_order.get(x.priority, 3))
        
        # Process requests with concurrency limit
        max_concurrent = self.config['limits']['max_concurrent_provisioning']
        current_requests = []
        completed_requests = set()
        
        for request in sorted_requests:
            # Wait for slot if at concurrency limit
            while len(current_requests) >= max_concurrent:
                # Check completed requests
                current_requests = [req for req in current_requests 
                                 if req.request_id not in completed_requests]
                if len(current_requests) < max_concurrent:
                    break
                # Small delay to avoid busy waiting
                import time
                time.sleep(1)
            
            # Start provisioning
            current_requests.append(request)
            
            try:
                result = self.provision_infrastructure(request, dry_run)
                results.append(result)
                completed_requests.add(request.request_id)
                
            except Exception as e:
                logger.error(f"Batch provisioning failed for {request.request_id}: {e}")
                error_result = ProvisioningResult(
                    request_id=request.request_id,
                    resource_id=None,
                    status=ProvisioningStatus.FAILED,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=str(e),
                    resource_details=None,
                    cost_estimate=0.0
                )
                results.append(error_result)
                completed_requests.add(request.request_id)
        
        return results
    
    def get_provisioning_status(self, request_ids: Optional[List[str]] = None) -> Dict[str, ProvisioningResult]:
        """Get provisioning status for requests"""
        if request_ids:
            return {req_id: self.results.get(req_id) for req_id in request_ids}
        else:
            return self.results.copy()
    
    def generate_provisioning_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive provisioning report"""
        logger.info("Generating provisioning report")
        
        # Calculate statistics
        total_requests = len(self.requests)
        completed_requests = len([r for r in self.results.values() if r.status == ProvisioningStatus.COMPLETED])
        failed_requests = len([r for r in self.results.values() if r.status == ProvisioningStatus.FAILED])
        in_progress_requests = len([r for r in self.results.values() if r.status == ProvisioningStatus.IN_PROGRESS])
        
        # Calculate cost statistics
        total_estimated_cost = sum(result.cost_estimate for result in self.results.values())
        successful_cost = sum(result.cost_estimate for result in self.results.values() 
                             if result.status == ProvisioningStatus.COMPLETED)
        
        # Group by provider
        provider_stats = {}
        for request in self.requests.values():
            provider = request.provider
            if provider not in provider_stats:
                provider_stats[provider] = {'requests': 0, 'completed': 0, 'failed': 0, 'total_cost': 0.0}
            
            provider_stats[provider]['requests'] += 1
            provider_stats[provider]['total_cost'] += self.results.get(request.request_id, ProvisioningResult(
                request_id=request.request_id, resource_id=None, status=ProvisioningStatus.PENDING,
                started_at=datetime.utcnow(), completed_at=None, error_message=None,
                resource_details=None, cost_estimate=0.0
            )).cost_estimate
            
            result = self.results.get(request.request_id)
            if result:
                if result.status == ProvisioningStatus.COMPLETED:
                    provider_stats[provider]['completed'] += 1
                elif result.status == ProvisioningStatus.FAILED:
                    provider_stats[provider]['failed'] += 1
        
        # Group by resource type
        resource_type_stats = {}
        for request in self.requests.values():
            resource_type = request.resource_type.value
            if resource_type not in resource_type_stats:
                resource_type_stats[resource_type] = {'requests': 0, 'completed': 0, 'failed': 0}
            
            resource_type_stats[resource_type]['requests'] += 1
            
            result = self.results.get(request.request_id)
            if result:
                if result.status == ProvisioningStatus.COMPLETED:
                    resource_type_stats[resource_type]['completed'] += 1
                elif result.status == ProvisioningStatus.FAILED:
                    resource_type_stats[resource_type]['failed'] += 1
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_requests': total_requests,
                'completed_requests': completed_requests,
                'failed_requests': failed_requests,
                'in_progress_requests': in_progress_requests,
                'success_rate': (completed_requests / total_requests * 100) if total_requests > 0 else 0,
                'total_estimated_cost': total_estimated_cost,
                'successful_cost': successful_cost
            },
            'provider_statistics': provider_stats,
            'resource_type_statistics': resource_type_stats,
            'templates_available': len(self.templates),
            'recent_requests': [
                {
                    'request_id': req.request_id,
                    'resource_name': req.resource_name,
                    'resource_type': req.resource_type.value,
                    'provider': req.provider,
                    'status': self.results.get(req.request_id, ProvisioningResult(
                        request_id=req.request_id, resource_id=None, status=ProvisioningStatus.PENDING,
                        started_at=datetime.utcnow(), completed_at=None, error_message=None,
                        resource_details=None, cost_estimate=0.0
                    )).status.value,
                    'requested_at': req.requested_at.isoformat(),
                    'priority': req.priority
                }
                for req in sorted(self.requests.values(), key=lambda x: x.requested_at, reverse=True)[:10]
            ]
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Provisioning report saved to: {output_file}")
        
        return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Infrastructure Provisioner")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--templates", help="Templates file")
    parser.add_argument("--action", choices=['provision', 'batch', 'status', 'report'], 
                       required=True, help="Action to perform")
    parser.add_argument("--resource-name", help="Resource name")
    parser.add_argument("--resource-type", choices=[t.value for t in ResourceType], 
                       help="Resource type")
    parser.add_argument("--provider", choices=['aws', 'azure', 'gcp', 'onprem'], 
                       help="Cloud provider")
    parser.add_argument("--configuration", help="Configuration JSON")
    parser.add_argument("--tags", help="Tags JSON")
    parser.add_argument("--template-id", help="Template ID")
    parser.add_argument("--requests-file", help="Batch requests JSON file")
    parser.add_argument("--request-ids", nargs="+", help="Request IDs for status")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize provisioner
    provisioner = InfrastructureProvisioner(args.config)
    
    # Load templates
    provisioner.load_templates(args.templates)
    
    try:
        if args.action == 'provision':
            if not args.resource_name or not args.resource_type or not args.provider:
                print("Error: --resource-name, --resource-type, and --provider required for provision action")
                sys.exit(1)
            
            # Parse configuration
            configuration = {}
            if args.configuration:
                configuration = json.loads(args.configuration)
            
            # Parse tags
            tags = {}
            if args.tags:
                tags = json.loads(args.tags)
            
            # Create request
            request = provisioner.create_provisioning_request(
                resource_name=args.resource_name,
                resource_type=ResourceType(args.resource_type),
                provider=args.provider,
                configuration=configuration,
                tags=tags,
                template_id=args.template_id
            )
            
            # Provision resource
            result = provisioner.provision_infrastructure(request, args.dry_run)
            
            print(f"\nProvisioning Result:")
            print(f"Request ID: {result.request_id}")
            print(f"Status: {result.status.value}")
            print(f"Resource ID: {result.resource_id}")
            print(f"Started: {result.started_at}")
            print(f"Completed: {result.completed_at}")
            print(f"Cost Estimate: ${result.cost_estimate:.2f}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            if args.dry_run:
                print("DRY RUN MODE - No actual resources were created")
        
        elif args.action == 'batch':
            if not args.requests_file:
                print("Error: --requests-file required for batch action")
                sys.exit(1)
            
            with open(args.requests_file, 'r') as f:
                requests_data = json.load(f)
            
            # Create requests
            requests = []
            for req_data in requests_data:
                request = provisioner.create_provisioning_request(
                    resource_name=req_data['resource_name'],
                    resource_type=ResourceType(req_data['resource_type']),
                    provider=req_data['provider'],
                    configuration=req_data.get('configuration', {}),
                    tags=req_data.get('tags', {}),
                    requested_by=req_data.get('requested_by', 'batch'),
                    priority=req_data.get('priority', 'medium'),
                    template_id=req_data.get('template_id')
                )
                requests.append(request)
            
            # Batch provision
            results = provisioner.batch_provision(requests, args.dry_run)
            
            print(f"\nBatch Provisioning Results:")
            success_count = len([r for r in results if r.status == ProvisioningStatus.COMPLETED])
            failed_count = len([r for r in results if r.status == ProvisioningStatus.FAILED])
            
            print(f"Total Requests: {len(results)}")
            print(f"Successful: {success_count}")
            print(f"Failed: {failed_count}")
            
            if args.output:
                results_data = [
                    {
                        'request_id': r.request_id,
                        'status': r.status.value,
                        'resource_id': r.resource_id,
                        'error': r.error_message
                    }
                    for r in results
                ]
                with open(args.output, 'w') as f:
                    json.dump(results_data, f, indent=2)
                print(f"Results saved to: {args.output}")
        
        elif args.action == 'status':
            request_ids = args.request_ids if args.request_ids else None
            status = provisioner.get_provisioning_status(request_ids)
            
            print(f"\nProvisioning Status:")
            for req_id, result in status.items():
                print(f"{req_id}: {result.status.value}")
                if result.resource_id:
                    print(f"  Resource ID: {result.resource_id}")
                if result.error_message:
                    print(f"  Error: {result.error_message}")
        
        elif args.action == 'report':
            report = provisioner.generate_provisioning_report(args.output)
            
            summary = report['summary']
            print(f"\nProvisioning Report:")
            print(f"Total Requests: {summary['total_requests']}")
            print(f"Completed: {summary['completed_requests']}")
            print(f"Failed: {summary['failed_requests']}")
            print(f"Success Rate: {summary['success_rate']:.1f}%")
            print(f"Total Estimated Cost: ${summary['total_estimated_cost']:.2f}")
            print(f"Templates Available: {report['templates_available']}")
            
            if args.output:
                print(f"Report saved to: {args.output}")
        
        else:
            print(f"Action {args.action} not implemented in CLI")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Provisioning failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
