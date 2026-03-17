#!/usr/bin/env python3
"""
Backup Orchestrator Script

Multi-cloud automation for backup orchestration, scheduling, and management across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"

class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RetentionPolicy(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

@dataclass
class BackupResource:
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    region: str
    environment: str
    size_gb: float
    criticality: str  # critical, important, standard
    backup_required: bool
    last_backup: Optional[datetime]
    backup_frequency: str
    retention_days: int
    tags: Dict[str, Any]

@dataclass
class BackupJob:
    job_id: str
    resource_id: str
    resource_name: str
    resource_type: str
    provider: str
    backup_type: BackupType
    status: BackupStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    size_gb: float
    location: str
    encryption_enabled: bool
    compression_enabled: bool
    verification_enabled: bool
    retention_days: int
    cost_estimate: float
    metadata: Dict[str, Any]

@dataclass
class BackupPolicy:
    policy_id: str
    name: str
    description: str
    resource_types: List[str]
    backup_type: BackupType
    schedule: str  # cron expression
    retention_policy: RetentionPolicy
    retention_days: int
    encryption_required: bool
    compression_enabled: bool
    verification_enabled: bool
    cross_region: bool
    cross_cloud: bool
    priority: str
    tags: Dict[str, Any]

@dataclass
class BackupReport:
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    total_size_gb: float
    total_cost: float
    success_rate: float
    provider_summary: Dict[str, Any]
    resource_type_summary: Dict[str, Any]
    recommendations: List[str]

class BackupOrchestrator:
    """Main backup orchestration class"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = self._load_config()
        self.handlers = {}
        self.resources = {}
        self.policies = {}
        self.jobs = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'datacenter-1', 'enabled': True}
            },
            'backup_settings': {
                'default_retention_days': 30,
                'max_concurrent_jobs': 5,
                'encryption_required': True,
                'compression_enabled': True,
                'verification_enabled': True,
                'cross_region_backup': False,
                'cross_cloud_backup': False
            },
            'cost_settings': {
                'storage_cost_per_gb': 0.023,  # S3 Standard
                'transfer_cost_per_gb': 0.02,
                'compute_cost_per_hour': 0.05
            },
            'alert_settings': {
                'failure_threshold': 3,
                'success_rate_threshold': 95.0,
                'notification_channels': ['email', 'slack']
            }
        }
        
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        return default_config
    
    def initialize_handlers(self, providers: List[str]) -> bool:
        """Initialize backup handlers for specified providers"""
        try:
            success = True
            
            for provider in providers:
                if provider not in self.config['providers']:
                    logger.warning(f"Provider {provider} not in configuration")
                    continue
                
                if not self.config['providers'][provider]['enabled']:
                    logger.info(f"Provider {provider} is disabled")
                    continue
                
                from backup_orchestrator_handler import get_backup_handler
                region = self.config['providers'][provider]['region']
                handler = get_backup_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    logger.info(f"Initialized {provider} backup handler")
                else:
                    logger.error(f"Failed to initialize {provider} backup handler")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            return False
    
    def discover_backup_resources(self, providers: List[str]) -> Dict[str, List[BackupResource]]:
        """Discover backup-eligible resources across providers"""
        discovered_resources = {}
        
        for provider in providers:
            try:
                handler = self.handlers.get(provider)
                if not handler:
                    logger.warning(f"No handler available for {provider}")
                    continue
                
                resources = handler.discover_backup_resources()
                discovered_resources[provider] = resources
                
                # Store in resources dict
                for resource in resources:
                    self.resources[resource.resource_id] = resource
                
                logger.info(f"Discovered {len(resources)} backup resources for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to discover backup resources for {provider}: {e}")
                discovered_resources[provider] = []
        
        return discovered_resources
    
    def create_backup_policy(self, policy_config: Dict[str, Any]) -> BackupPolicy:
        """Create a new backup policy"""
        try:
            policy = BackupPolicy(
                policy_id=f"policy-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                name=policy_config['name'],
                description=policy_config.get('description', ''),
                resource_types=policy_config.get('resource_types', []),
                backup_type=BackupType(policy_config.get('backup_type', 'full')),
                schedule=policy_config.get('schedule', '0 2 * * *'),  # Daily at 2 AM
                retention_policy=RetentionPolicy(policy_config.get('retention_policy', 'daily')),
                retention_days=policy_config.get('retention_days', self.config['backup_settings']['default_retention_days']),
                encryption_required=policy_config.get('encryption_required', self.config['backup_settings']['encryption_required']),
                compression_enabled=policy_config.get('compression_enabled', self.config['backup_settings']['compression_enabled']),
                verification_enabled=policy_config.get('verification_enabled', self.config['backup_settings']['verification_enabled']),
                cross_region=policy_config.get('cross_region', self.config['backup_settings']['cross_region_backup']),
                cross_cloud=policy_config.get('cross_cloud', self.config['backup_settings']['cross_cloud_backup']),
                priority=policy_config.get('priority', 'medium'),
                tags=policy_config.get('tags', {})
            )
            
            self.policies[policy.policy_id] = policy
            logger.info(f"Created backup policy: {policy.name}")
            
            return policy
            
        except Exception as e:
            logger.error(f"Failed to create backup policy: {e}")
            raise
    
    def execute_backup_job(self, resource: BackupResource, backup_type: BackupType, policy: Optional[BackupPolicy] = None) -> BackupJob:
        """Execute a backup job for a specific resource"""
        try:
            job_id = f"backup-{resource.resource_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create backup job
            job = BackupJob(
                job_id=job_id,
                resource_id=resource.resource_id,
                resource_name=resource.resource_name,
                resource_type=resource.resource_type,
                provider=resource.provider,
                backup_type=backup_type,
                status=BackupStatus.PENDING,
                created_at=datetime.utcnow(),
                started_at=None,
                completed_at=None,
                size_gb=resource.size_gb,
                location="",  # Will be set by handler
                encryption_enabled=policy.encryption_required if policy else self.config['backup_settings']['encryption_required'],
                compression_enabled=policy.compression_enabled if policy else self.config['backup_settings']['compression_enabled'],
                verification_enabled=policy.verification_enabled if policy else self.config['backup_settings']['verification_enabled'],
                retention_days=policy.retention_days if policy else self.config['backup_settings']['default_retention_days'],
                cost_estimate=self._estimate_backup_cost(resource, backup_type),
                metadata={}
            )
            
            self.jobs[job_id] = job
            
            # Execute backup
            handler = self.handlers.get(resource.provider)
            if not handler:
                raise ValueError(f"No handler available for provider {resource.provider}")
            
            # Update job status to running
            job.status = BackupStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            # Execute backup through handler
            backup_result = handler.execute_backup(resource, backup_type, job)
            
            # Update job with results
            if backup_result['success']:
                job.status = BackupStatus.COMPLETED
                job.location = backup_result['location']
                job.metadata = backup_result.get('metadata', {})
                logger.info(f"Backup job {job_id} completed successfully")
            else:
                job.status = BackupStatus.FAILED
                job.metadata['error'] = backup_result.get('error', 'Unknown error')
                logger.error(f"Backup job {job_id} failed: {backup_result.get('error')}")
            
            job.completed_at = datetime.utcnow()
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to execute backup job: {e}")
            if job_id in self.jobs:
                self.jobs[job_id].status = BackupStatus.FAILED
                self.jobs[job_id].completed_at = datetime.utcnow()
                self.jobs[job_id].metadata['error'] = str(e)
            raise
    
    def orchestrate_backup_execution(self, providers: List[str], resource_types: Optional[List[str]] = None, 
                                   backup_type: BackupType = BackupType.FULL) -> Dict[str, List[BackupJob]]:
        """Orchestrate backup execution across providers"""
        logger.info(f"Starting backup orchestration for providers: {providers}")
        
        execution_results = {}
        
        for provider in providers:
            try:
                handler = self.handlers.get(provider)
                if not handler:
                    logger.warning(f"No handler available for {provider}")
                    continue
                
                # Get resources for this provider
                provider_resources = [r for r in self.resources.values() if r.provider == provider]
                
                # Filter by resource types if specified
                if resource_types:
                    provider_resources = [r for r in provider_resources if r.resource_type in resource_types]
                
                # Filter resources that require backup
                backup_resources = [r for r in provider_resources if r.backup_required]
                
                provider_jobs = []
                
                # Execute backups with concurrency limit
                max_concurrent = self.config['backup_settings']['max_concurrent_jobs']
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def execute_with_semaphore(resource):
                    async with semaphore:
                        return self.execute_backup_job(resource, backup_type)
                
                # Run backups concurrently
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    tasks = [execute_with_semaphore(resource) for resource in backup_resources]
                    provider_jobs = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                    
                    # Filter out exceptions
                    provider_jobs = [job for job in provider_jobs if isinstance(job, BackupJob)]
                    
                finally:
                    loop.close()
                
                execution_results[provider] = provider_jobs
                logger.info(f"Executed {len(provider_jobs)} backup jobs for {provider}")
                
            except Exception as e:
                logger.error(f"Failed to orchestrate backup execution for {provider}: {e}")
                execution_results[provider] = []
        
        return execution_results
    
    def schedule_backup_jobs(self, policy: BackupPolicy) -> List[str]:
        """Schedule backup jobs based on policy"""
        try:
            scheduled_jobs = []
            
            # Find resources matching policy
            matching_resources = [
                r for r in self.resources.values()
                if r.resource_type in policy.resource_types and r.backup_required
            ]
            
            for resource in matching_resources:
                # Create scheduled job (in real implementation, this would integrate with a scheduler)
                job_id = f"scheduled-{resource.resource_id}-{policy.policy_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                
                # Store scheduled job info
                scheduled_jobs.append({
                    'job_id': job_id,
                    'resource_id': resource.resource_id,
                    'policy_id': policy.policy_id,
                    'schedule': policy.schedule,
                    'backup_type': policy.backup_type.value,
                    'next_run': self._calculate_next_run(policy.schedule)
                })
            
            logger.info(f"Scheduled {len(scheduled_jobs)} backup jobs for policy {policy.name}")
            return scheduled_jobs
            
        except Exception as e:
            logger.error(f"Failed to schedule backup jobs: {e}")
            return []
    
    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time from cron schedule (simplified)"""
        # This is a simplified implementation
        # In production, you would use a proper cron parser
        if schedule == "0 2 * * *":  # Daily at 2 AM
            tomorrow = datetime.utcnow() + timedelta(days=1)
            return tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)
        elif schedule == "0 2 * * 0":  # Weekly on Sunday at 2 AM
            days_ahead = 6 - datetime.utcnow().weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_sunday = datetime.utcnow() + timedelta(days=days_ahead)
            return next_sunday.replace(hour=2, minute=0, second=0, microsecond=0)
        else:
            # Default to next day
            return datetime.utcnow() + timedelta(days=1)
    
    def verify_backup_integrity(self, job: BackupJob) -> Dict[str, Any]:
        """Verify backup integrity"""
        try:
            handler = self.handlers.get(job.provider)
            if not handler:
                raise ValueError(f"No handler available for provider {job.provider}")
            
            verification_result = handler.verify_backup(job)
            
            return {
                'job_id': job.job_id,
                'verification_passed': verification_result.get('passed', False),
                'verification_details': verification_result.get('details', {}),
                'verified_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to verify backup integrity for job {job.job_id}: {e}")
            return {
                'job_id': job.job_id,
                'verification_passed': False,
                'verification_details': {'error': str(e)},
                'verified_at': datetime.utcnow().isoformat()
            }
    
    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """Clean up old backups based on retention policy"""
        try:
            if not retention_days:
                retention_days = self.config['backup_settings']['default_retention_days']
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            cleanup_results = {
                'total_backups_checked': 0,
                'backups_deleted': 0,
                'space_freed_gb': 0.0,
                'provider_results': {}
            }
            
            for provider, handler in self.handlers.items():
                try:
                    provider_result = handler.cleanup_old_backups(cutoff_date)
                    cleanup_results['provider_results'][provider] = provider_result
                    cleanup_results['backups_deleted'] += provider_result.get('deleted_count', 0)
                    cleanup_results['space_freed_gb'] += provider_result.get('space_freed_gb', 0.0)
                    
                except Exception as e:
                    logger.error(f"Failed to cleanup old backups for {provider}: {e}")
                    cleanup_results['provider_results'][provider] = {'error': str(e)}
            
            logger.info(f"Cleaned up {cleanup_results['backups_deleted']} old backups, freed {cleanup_results['space_freed_gb']:.2f} GB")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return {'error': str(e)}
    
    def generate_backup_report(self, period_days: int = 7) -> BackupReport:
        """Generate comprehensive backup report"""
        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=period_days)
            
            # Filter jobs within period
            period_jobs = [
                job for job in self.jobs.values()
                if job.created_at >= period_start and job.created_at <= period_end
            ]
            
            # Calculate statistics
            total_jobs = len(period_jobs)
            successful_jobs = len([j for j in period_jobs if j.status == BackupStatus.COMPLETED])
            failed_jobs = len([j for j in period_jobs if j.status == BackupStatus.FAILED])
            total_size_gb = sum(j.size_gb for j in period_jobs)
            total_cost = sum(j.cost_estimate for j in period_jobs)
            success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0
            
            # Provider summary
            provider_summary = {}
            for provider in set(j.provider for j in period_jobs):
                provider_jobs = [j for j in period_jobs if j.provider == provider]
                provider_summary[provider] = {
                    'total_jobs': len(provider_jobs),
                    'successful_jobs': len([j for j in provider_jobs if j.status == BackupStatus.COMPLETED]),
                    'failed_jobs': len([j for j in provider_jobs if j.status == BackupStatus.FAILED]),
                    'total_size_gb': sum(j.size_gb for j in provider_jobs),
                    'success_rate': (len([j for j in provider_jobs if j.status == BackupStatus.COMPLETED]) / len(provider_jobs) * 100) if provider_jobs else 0.0
                }
            
            # Resource type summary
            resource_type_summary = {}
            for resource_type in set(j.resource_type for j in period_jobs):
                type_jobs = [j for j in period_jobs if j.resource_type == resource_type]
                resource_type_summary[resource_type] = {
                    'total_jobs': len(type_jobs),
                    'successful_jobs': len([j for j in type_jobs if j.status == BackupStatus.COMPLETED]),
                    'failed_jobs': len([j for j in type_jobs if j.status == BackupStatus.FAILED]),
                    'total_size_gb': sum(j.size_gb for j in type_jobs),
                    'success_rate': (len([j for j in type_jobs if j.status == BackupStatus.COMPLETED]) / len(type_jobs) * 100) if type_jobs else 0.0
                }
            
            # Generate recommendations
            recommendations = self._generate_backup_recommendations(period_jobs, success_rate)
            
            report = BackupReport(
                report_id=f"report-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                generated_at=datetime.utcnow(),
                period_start=period_start,
                period_end=period_end,
                total_jobs=total_jobs,
                successful_jobs=successful_jobs,
                failed_jobs=failed_jobs,
                total_size_gb=total_size_gb,
                total_cost=total_cost,
                success_rate=success_rate,
                provider_summary=provider_summary,
                resource_type_summary=resource_type_summary,
                recommendations=recommendations
            )
            
            logger.info(f"Generated backup report with {total_jobs} jobs, {success_rate:.1f}% success rate")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate backup report: {e}")
            raise
    
    def _generate_backup_recommendations(self, jobs: List[BackupJob], success_rate: float) -> List[str]:
        """Generate backup recommendations based on analysis"""
        recommendations = []
        
        # Success rate recommendations
        if success_rate < self.config['alert_settings']['success_rate_threshold']:
            recommendations.append(f"Success rate ({success_rate:.1f}%) is below threshold ({self.config['alert_settings']['success_rate_threshold']}%). Review failed jobs.")
        
        # Failed jobs analysis
        failed_jobs = [j for j in jobs if j.status == BackupStatus.FAILED]
        if len(failed_jobs) > self.config['alert_settings']['failure_threshold']:
            recommendations.append(f"High number of failed jobs ({len(failed_jobs)}). Investigate common failure patterns.")
        
        # Cost optimization
        total_cost = sum(j.cost_estimate for j in jobs)
        if total_cost > 1000:  # Arbitrary threshold
            recommendations.append("Consider implementing backup compression or tiered storage to reduce costs.")
        
        # Resource coverage
        backed_up_resources = set(j.resource_id for j in jobs if j.status == BackupStatus.COMPLETED)
        all_resources = set(r.resource_id for r in self.resources.values() if r.backup_required)
        
        if len(backed_up_resources) < len(all_resources):
            missing_resources = len(all_resources) - len(backed_up_resources)
            recommendations.append(f"{missing_resources} resources not backed up. Review backup policies and resource coverage.")
        
        # Retention policy
        old_jobs = [j for j in jobs if j.created_at < datetime.utcnow() - timedelta(days=60)]
        if len(old_jobs) > 0:
            recommendations.append("Consider implementing automated cleanup for old backups to optimize storage costs.")
        
        if not recommendations:
            recommendations.append("Backup operations are performing well. Continue monitoring and maintenance.")
        
        return recommendations
    
    def _estimate_backup_cost(self, resource: BackupResource, backup_type: BackupType) -> float:
        """Estimate backup cost"""
        try:
            storage_cost_per_gb = self.config['cost_settings']['storage_cost_per_gb']
            transfer_cost_per_gb = self.config['cost_settings']['transfer_cost_per_gb']
            
            # Base storage cost
            storage_cost = resource.size_gb * storage_cost_per_gb
            
            # Transfer cost (for cross-region/cloud)
            transfer_cost = 0.0
            if self.config['backup_settings']['cross_region_backup']:
                transfer_cost = resource.size_gb * transfer_cost_per_gb
            
            # Compression reduces storage cost
            if self.config['backup_settings']['compression_enabled']:
                storage_cost *= 0.7  # Assume 30% compression
            
            # Backup type multiplier
            type_multipliers = {
                BackupType.FULL: 1.0,
                BackupType.INCREMENTAL: 0.2,
                BackupType.DIFFERENTIAL: 0.5,
                BackupType.SNAPSHOT: 0.1
            }
            
            multiplier = type_multipliers.get(backup_type, 1.0)
            
            total_cost = (storage_cost + transfer_cost) * multiplier
            
            return round(total_cost, 4)
            
        except Exception as e:
            logger.error(f"Failed to estimate backup cost: {e}")
            return 0.0
    
    def get_backup_status(self, job_id: str) -> Optional[BackupJob]:
        """Get status of a specific backup job"""
        return self.jobs.get(job_id)
    
    def get_all_backup_jobs(self, status: Optional[BackupStatus] = None) -> List[BackupJob]:
        """Get all backup jobs, optionally filtered by status"""
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs
    
    def get_backup_policies(self) -> List[BackupPolicy]:
        """Get all backup policies"""
        return list(self.policies.values())
    
    def export_backup_data(self, format: str = "json", output_file: Optional[str] = None) -> str:
        """Export backup data to specified format"""
        try:
            if format.lower() == "json":
                data = {
                    'resources': [asdict(resource) for resource in self.resources.values()],
                    'policies': [asdict(policy) for policy in self.policies.values()],
                    'jobs': [asdict(job) for job in self.jobs.values()]
                }
                
                # Convert datetime objects to strings
                for item in data['resources']:
                    item['last_backup'] = item['last_backup'].isoformat() if item['last_backup'] else None
                
                for item in data['policies']:
                    pass  # No datetime fields in policies
                
                for item in data['jobs']:
                    item['created_at'] = item['created_at'].isoformat()
                    item['started_at'] = item['started_at'].isoformat() if item['started_at'] else None
                    item['completed_at'] = item['completed_at'].isoformat() if item['completed_at'] else None
                
                output = json.dumps(data, indent=2, default=str)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            # Save to file if specified
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(output)
                logger.info(f"Backup data exported to {output_file}")
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to export backup data: {e}")
            raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Multi-Cloud Backup Orchestrator')
    parser.add_argument('--config', type=str, help='Configuration file')
    parser.add_argument('--providers', type=str, nargs='+', default=['aws'], help='Cloud providers')
    parser.add_argument('--action', type=str, required=True, choices=[
        'discover', 'backup', 'schedule', 'report', 'cleanup', 'verify', 'export'
    ], help='Action to perform')
    parser.add_argument('--resource-types', type=str, nargs='+', help='Resource types to backup')
    parser.add_argument('--backup-type', type=str, default='full', 
                       choices=['full', 'incremental', 'differential', 'snapshot'], help='Backup type')
    parser.add_argument('--retention-days', type=int, help='Retention days for cleanup')
    parser.add_argument('--period-days', type=int, default=7, help='Period for report (days)')
    parser.add_argument('--output', type=str, help='Output file')
    parser.add_argument('--format', type=str, default='json', choices=['json'], help='Output format')
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = BackupOrchestrator(args.config)
        
        # Initialize handlers
        if not orchestrator.initialize_handlers(args.providers):
            logger.error("Failed to initialize handlers")
            sys.exit(1)
        
        # Execute action
        if args.action == 'discover':
            resources = orchestrator.discover_backup_resources(args.providers)
            print(json.dumps({p: [asdict(r) for r in resource_list] for p, resource_list in resources.items()}, indent=2, default=str))
        
        elif args.action == 'backup':
            # First discover resources
            orchestrator.discover_backup_resources(args.providers)
            
            # Execute backups
            backup_type = BackupType(args.backup_type)
            results = orchestrator.orchestrate_backup_execution(args.providers, args.resource_types, backup_type)
            
            # Print results
            for provider, jobs in results.items():
                print(f"\n{provider.upper()} Results:")
                for job in jobs:
                    print(f"  {job.resource_name}: {job.status.value} ({job.size_gb} GB)")
        
        elif args.action == 'schedule':
            # Create a sample policy
            policy_config = {
                'name': 'Daily Backup Policy',
                'description': 'Daily full backups for all resources',
                'resource_types': args.resource_types or ['all'],
                'backup_type': args.backup_type,
                'schedule': '0 2 * * *',  # Daily at 2 AM
                'retention_policy': 'daily',
                'retention_days': args.retention_days or 30
            }
            
            policy = orchestrator.create_backup_policy(policy_config)
            scheduled_jobs = orchestrator.schedule_backup_jobs(policy)
            
            print(f"Created policy: {policy.name}")
            print(f"Scheduled {len(scheduled_jobs)} backup jobs")
            for job in scheduled_jobs[:5]:  # Show first 5
                print(f"  {job['resource_id']}: Next run {job['next_run']}")
        
        elif args.action == 'report':
            # First discover resources to get context
            orchestrator.discover_backup_resources(args.providers)
            
            report = orchestrator.generate_backup_report(args.period_days)
            
            report_data = asdict(report)
            report_data['generated_at'] = report.generated_at.isoformat()
            report_data['period_start'] = report.period_start.isoformat()
            report_data['period_end'] = report.period_end.isoformat()
            
            print(json.dumps(report_data, indent=2, default=str))
        
        elif args.action == 'cleanup':
            results = orchestrator.cleanup_old_backups(args.retention_days)
            print(json.dumps(results, indent=2, default=str))
        
        elif args.action == 'verify':
            # Get recent completed jobs
            recent_jobs = [j for j in orchestrator.get_all_backup_jobs(BackupStatus.COMPLETED) 
                          if j.completed_at and j.completed_at > datetime.utcnow() - timedelta(days=1)]
            
            verification_results = []
            for job in recent_jobs[:5]:  # Verify up to 5 recent jobs
                result = orchestrator.verify_backup_integrity(job)
                verification_results.append(result)
            
            print(json.dumps(verification_results, indent=2, default=str))
        
        elif args.action == 'export':
            # First discover resources
            orchestrator.discover_backup_resources(args.providers)
            
            output = orchestrator.export_backup_data(args.format, args.output)
            if not args.output:
                print(output)
        
        logger.info(f"Completed {args.action} action successfully")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
