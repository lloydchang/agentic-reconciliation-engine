"""
Cross-Platform Policies and Configuration Management

This module provides unified policy management across all communication platforms
(Slack, Linear, GitHub) with intelligent configuration inheritance and validation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Union
from enum import Enum
import asyncio
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of policies"""
    SECURITY = "security"
    COMPLIANCE = "compliance"
    RESOURCE = "resource"
    COMMUNICATION = "communication"
    EXECUTION = "execution"
    AUDIT = "audit"


class PolicyScope(Enum):
    """Policy application scope"""
    GLOBAL = "global"
    PLATFORM = "platform"
    ORGANIZATION = "organization"
    REPOSITORY = "repository"
    USER = "user"
    AGENT = "agent"


class EnforcementLevel(Enum):
    """Policy enforcement levels"""
    PERMISSIVE = "permissive"  # Allow with warnings
    STRICT = "strict"          # Block violations
    AUDIT = "audit"           # Log only
    DISABLED = "disabled"     # No enforcement


@dataclass
class PolicyRule:
    """Individual policy rule"""
    id: str
    name: str
    description: str
    policy_type: PolicyType
    scope: PolicyScope
    enforcement: EnforcementLevel
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 1

    def matches_context(self, context: Dict[str, Any]) -> bool:
        """Check if policy applies to given context"""
        for key, expected_value in self.conditions.items():
            actual_value = context.get(key)
            if actual_value != expected_value:
                return False
        return True

    def should_enforce(self, context: Dict[str, Any]) -> bool:
        """Determine if policy should be enforced"""
        if not self.enabled:
            return False

        if self.enforcement == EnforcementLevel.DISABLED:
            return False

        return self.matches_context(context)


@dataclass
class PolicySet:
    """Collection of related policies"""
    id: str
    name: str
    description: str
    policies: List[PolicyRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def add_policy(self, policy: PolicyRule):
        """Add policy to set"""
        self.policies.append(policy)
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    def remove_policy(self, policy_id: str):
        """Remove policy from set"""
        self.policies = [p for p in self.policies if p.id != policy_id]

    def get_policies(self, policy_type: Optional[PolicyType] = None,
                    scope: Optional[PolicyScope] = None) -> List[PolicyRule]:
        """Get policies filtered by type and scope"""
        filtered = self.policies

        if policy_type:
            filtered = [p for p in filtered if p.policy_type == policy_type]

        if scope:
            filtered = [p for p in filtered if p.scope == scope]

        return filtered


@dataclass
class PlatformConfig:
    """Platform-specific configuration"""
    platform: str
    settings: Dict[str, Any] = field(default_factory=dict)
    policies: List[str] = field(default_factory=list)  # Policy set IDs
    rate_limits: Dict[str, Any] = field(default_factory=dict)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    integrations: Dict[str, Any] = field(default_factory=dict)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting with fallback"""
        return self.settings.get(key, default)

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled"""
        return self.feature_flags.get(feature, False)


@dataclass
class OrganizationConfig:
    """Organization-level configuration"""
    id: str
    name: str
    platforms: Dict[str, PlatformConfig] = field(default_factory=dict)
    policies: List[str] = field(default_factory=list)  # Policy set IDs
    repositories: Dict[str, 'RepositoryConfig'] = field(default_factory=dict)
    users: Dict[str, 'UserConfig'] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_platform_config(self, platform: str) -> Optional[PlatformConfig]:
        """Get configuration for specific platform"""
        return self.platforms.get(platform)

    def get_repository_config(self, repo_name: str) -> Optional['RepositoryConfig']:
        """Get configuration for specific repository"""
        return self.repositories.get(repo_name)


@dataclass
class RepositoryConfig:
    """Repository-specific configuration"""
    name: str
    platform: str
    policies: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, Any] = field(default_factory=dict)
    workflows: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for specific agent"""
        return self.agents.get(agent_name, {})


@dataclass
class UserConfig:
    """User-specific configuration"""
    id: str
    username: str
    permissions: Set[str] = field(default_factory=set)
    preferences: Dict[str, Any] = field(default_factory=dict)
    policies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        return self.preferences.get(key, default)


class PolicyEngine:
    """Policy evaluation and enforcement engine"""

    def __init__(self):
        self.policy_sets: Dict[str, PolicySet] = {}
        self.global_policies: List[PolicyRule] = []
        self.audit_log: List[Dict[str, Any]] = []

    def add_policy_set(self, policy_set: PolicySet):
        """Add policy set"""
        self.policy_sets[policy_set.id] = policy_set

    def remove_policy_set(self, policy_set_id: str):
        """Remove policy set"""
        if policy_set_id in self.policy_sets:
            del self.policy_sets[policy_set_id]

    def add_global_policy(self, policy: PolicyRule):
        """Add global policy"""
        self.global_policies.append(policy)
        self.global_policies.sort(key=lambda p: p.priority, reverse=True)

    def evaluate_policies(self, context: Dict[str, Any],
                         policy_set_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Evaluate policies against context"""
        violations = []
        evaluated_policies = []

        # Add global policies
        evaluated_policies.extend(self.global_policies)

        # Add specified policy sets
        if policy_set_ids:
            for set_id in policy_set_ids:
                policy_set = self.policy_sets.get(set_id)
                if policy_set:
                    evaluated_policies.extend(policy_set.policies)

        # Evaluate each policy
        for policy in evaluated_policies:
            if policy.should_enforce(context):
                result = self._evaluate_policy(policy, context)
                if result["violated"]:
                    violations.append(result)

                # Log evaluation
                self._log_evaluation(policy, context, result)

        return violations

    def _evaluate_policy(self, policy: PolicyRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate individual policy"""
        result = {
            "policy_id": policy.id,
            "policy_name": policy.name,
            "violated": False,
            "enforcement_level": policy.enforcement.value,
            "actions": []
        }

        # Simple condition evaluation (can be extended with more complex logic)
        if policy.matches_context(context):
            result["violated"] = True

            if policy.enforcement == EnforcementLevel.STRICT:
                result["actions"] = policy.actions
            elif policy.enforcement == EnforcementLevel.PERMISSIVE:
                result["actions"] = [{"type": "warning", "message": policy.description}]

        return result

    def _log_evaluation(self, policy: PolicyRule, context: Dict[str, Any], result: Dict[str, Any]):
        """Log policy evaluation"""
        log_entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "policy_id": policy.id,
            "context": context,
            "result": result
        }
        self.audit_log.append(log_entry)

        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]

    def get_audit_log(self, policy_id: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        log = self.audit_log

        if policy_id:
            log = [entry for entry in log if entry["policy_id"] == policy_id]

        return log[-limit:]


class ConfigurationManager:
    """Unified configuration management"""

    def __init__(self, config_directory: str = "core/ai/config"):
        self.config_directory = Path(config_directory)
        self.organizations: Dict[str, OrganizationConfig] = {}
        self.policy_engine = PolicyEngine()
        self.cache: Dict[str, Any] = {}

    async def load_configuration(self):
        """Load all configuration from filesystem"""
        logger.info("Loading configuration")

        # Load policy sets
        await self._load_policy_sets()

        # Load organization configurations
        await self._load_organizations()

        logger.info(f"Loaded configuration for {len(self.organizations)} organizations")

    async def _load_policy_sets(self):
        """Load policy sets from filesystem"""
        policy_dir = self.config_directory / "policies"
        if not policy_dir.exists():
            logger.warning(f"Policy directory not found: {policy_dir}")
            return

        policy_files = list(policy_dir.glob("*.json")) + list(policy_dir.glob("*.yaml"))

        for policy_file in policy_files:
            try:
                policy_set = await self._load_policy_set(policy_file)
                if policy_set:
                    self.policy_engine.add_policy_set(policy_set)
            except Exception as e:
                logger.error(f"Failed to load policy set {policy_file}: {e}")

    async def _load_policy_set(self, file_path: Path) -> Optional[PolicySet]:
        """Load individual policy set"""
        import yaml

        try:
            if file_path.suffix == '.json':
                data = json.loads(file_path.read_text())
            else:
                data = yaml.safe_load(file_path.read_text())

            policies = []
            for policy_data in data.get('policies', []):
                policy = PolicyRule(
                    id=policy_data['id'],
                    name=policy_data['name'],
                    description=policy_data['description'],
                    policy_type=PolicyType(policy_data['type']),
                    scope=PolicyScope(policy_data['scope']),
                    enforcement=EnforcementLevel(policy_data['enforcement']),
                    conditions=policy_data.get('conditions', {}),
                    actions=policy_data.get('actions', []),
                    metadata=policy_data.get('metadata', {}),
                    enabled=policy_data.get('enabled', True),
                    priority=policy_data.get('priority', 1)
                )
                policies.append(policy)

            return PolicySet(
                id=data['id'],
                name=data['name'],
                description=data['description'],
                policies=policies,
                metadata=data.get('metadata', {}),
                version=data.get('version', '1.0.0')
            )

        except Exception as e:
            logger.error(f"Failed to parse policy set {file_path}: {e}")
            return None

    async def _load_organizations(self):
        """Load organization configurations"""
        org_dir = self.config_directory / "organizations"
        if not org_dir.exists():
            logger.warning(f"Organization directory not found: {org_dir}")
            return

        org_files = list(org_dir.glob("*.json")) + list(org_dir.glob("*.yaml"))

        for org_file in org_files:
            try:
                org_config = await self._load_organization(org_file)
                if org_config:
                    self.organizations[org_config.id] = org_config
            except Exception as e:
                logger.error(f"Failed to load organization {org_file}: {e}")

    async def _load_organization(self, file_path: Path) -> Optional[OrganizationConfig]:
        """Load individual organization configuration"""
        import yaml

        try:
            if file_path.suffix == '.json':
                data = json.loads(file_path.read_text())
            else:
                data = yaml.safe_load(file_path.read_text())

            # Load platform configs
            platforms = {}
            for platform_name, platform_data in data.get('platforms', {}).items():
                platform_config = PlatformConfig(
                    platform=platform_name,
                    settings=platform_data.get('settings', {}),
                    policies=platform_data.get('policies', []),
                    rate_limits=platform_data.get('rate_limits', {}),
                    feature_flags=platform_data.get('feature_flags', {}),
                    integrations=platform_data.get('integrations', {})
                )
                platforms[platform_name] = platform_config

            # Load repository configs
            repositories = {}
            for repo_name, repo_data in data.get('repositories', {}).items():
                repo_config = RepositoryConfig(
                    name=repo_name,
                    platform=repo_data.get('platform', 'github'),
                    policies=repo_data.get('policies', []),
                    settings=repo_data.get('settings', {}),
                    agents=repo_data.get('agents', {}),
                    workflows=repo_data.get('workflows', {}),
                    metadata=repo_data.get('metadata', {})
                )
                repositories[repo_name] = repo_config

            # Load user configs
            users = {}
            for user_id, user_data in data.get('users', {}).items():
                user_config = UserConfig(
                    id=user_id,
                    username=user_data.get('username', user_id),
                    permissions=set(user_data.get('permissions', [])),
                    preferences=user_data.get('preferences', {}),
                    policies=user_data.get('policies', []),
                    metadata=user_data.get('metadata', {})
                )
                users[user_id] = user_config

            return OrganizationConfig(
                id=data['id'],
                name=data['name'],
                platforms=platforms,
                policies=data.get('policies', []),
                repositories=repositories,
                users=users,
                metadata=data.get('metadata', {})
            )

        except Exception as e:
            logger.error(f"Failed to parse organization {file_path}: {e}")
            return None

    def get_organization_config(self, org_id: str) -> Optional[OrganizationConfig]:
        """Get organization configuration"""
        return self.organizations.get(org_id)

    def get_repository_config(self, org_id: str, repo_name: str) -> Optional[RepositoryConfig]:
        """Get repository configuration"""
        org_config = self.get_organization_config(org_id)
        if org_config:
            return org_config.get_repository_config(repo_name)
        return None

    def get_user_config(self, org_id: str, user_id: str) -> Optional[UserConfig]:
        """Get user configuration"""
        org_config = self.get_organization_config(org_id)
        if org_config:
            return org_config.users.get(user_id)
        return None

    def get_platform_config(self, org_id: str, platform: str) -> Optional[PlatformConfig]:
        """Get platform configuration"""
        org_config = self.get_organization_config(org_id)
        if org_config:
            return org_config.get_platform_config(platform)
        return None

    async def evaluate_policies(self, org_id: str, context: Dict[str, Any],
                               additional_policy_sets: List[str] = None) -> List[Dict[str, Any]]:
        """Evaluate policies for organization"""
        org_config = self.get_organization_config(org_id)
        if not org_config:
            return []

        policy_set_ids = org_config.policies.copy()
        if additional_policy_sets:
            policy_set_ids.extend(additional_policy_sets)

        return self.policy_engine.evaluate_policies(context, policy_set_ids)

    def get_policy_violations(self, org_id: str, time_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Get policy violations for organization"""
        # This would filter audit log by organization
        # For now, return all violations (would need org_id tracking in audit log)
        return self.policy_engine.get_audit_log()

    async def update_configuration(self, org_id: str, updates: Dict[str, Any]):
        """Update organization configuration"""
        org_config = self.get_organization_config(org_id)
        if not org_config:
            raise ValueError(f"Organization {org_id} not found")

        # Apply updates (simplified - would need more sophisticated merging)
        for key, value in updates.items():
            if hasattr(org_config, key):
                setattr(org_config, key, value)

        # Invalidate cache
        self.cache.clear()

        logger.info(f"Updated configuration for organization {org_id}")

    async def validate_configuration(self, org_id: str) -> Dict[str, Any]:
        """Validate organization configuration"""
        org_config = self.get_organization_config(org_id)
        if not org_config:
            return {"valid": False, "errors": [f"Organization {org_id} not found"]}

        errors = []
        warnings = []

        # Validate platform configurations
        for platform_name, platform_config in org_config.platforms.items():
            if not platform_config.integrations:
                warnings.append(f"Platform {platform_name} has no integrations configured")

        # Validate policy references
        for policy_set_id in org_config.policies:
            if policy_set_id not in self.policy_engine.policy_sets:
                errors.append(f"Referenced policy set {policy_set_id} does not exist")

        # Validate repository configurations
        for repo_name, repo_config in org_config.repositories.items():
            if not repo_config.agents:
                warnings.append(f"Repository {repo_name} has no agents configured")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Export key classes
__all__ = [
    'PolicyType',
    'PolicyScope',
    'EnforcementLevel',
    'PolicyRule',
    'PolicySet',
    'PlatformConfig',
    'OrganizationConfig',
    'RepositoryConfig',
    'UserConfig',
    'PolicyEngine',
    'ConfigurationManager'
]
