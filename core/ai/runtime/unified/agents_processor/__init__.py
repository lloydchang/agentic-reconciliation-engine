"""
Enhanced AGENTS.md Processing for Open SWE Integration

This module provides advanced processing of AGENTS.md files with intelligent
skill mapping, metadata extraction, and dynamic capability discovery.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Set
import asyncio
import logging
import re
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Enhanced agent metadata"""
    name: str
    description: str
    risk_level: str = "medium"
    autonomy: str = "conditional"
    layer: str = "temporal"
    human_gate: str = ""
    execution_mode: str = "local"
    sandbox_config: Dict[str, Any] = field(default_factory=dict)
    communication_preferences: Dict[str, Any] = field(default_factory=dict)
    capabilities: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    version: str = "1.0.0"
    last_updated: Optional[float] = None

    @property
    def skill_hash(self) -> str:
        """Generate hash for skill identification"""
        content = f"{self.name}:{self.description}:{self.capabilities}"
        return hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class SkillMapping:
    """Mapping between skills and capabilities"""
    skill_name: str
    agent_name: str
    capability_match: float  # 0.0 to 1.0
    confidence_score: float  # 0.0 to 1.0
    context_requirements: Dict[str, Any] = field(default_factory=dict)
    execution_hints: Dict[str, Any] = field(default_factory=dict)


class AGENTSProcessor:
    """Advanced AGENTS.md processor"""

    def __init__(self, agents_directory: str = "core/ai/skills"):
        self.agents_directory = Path(agents_directory)
        self.agent_cache: Dict[str, AgentMetadata] = {}
        self.skill_mappings: Dict[str, List[SkillMapping]] = {}
        self.capability_index: Dict[str, Set[str]] = {}  # capability -> agent names

        # Natural language patterns for capability extraction
        self.capability_patterns = {
            "deployment": re.compile(r'\b(deploy|deployment|rollout|release)\b', re.IGNORECASE),
            "monitoring": re.compile(r'\b(monitor|alert|metrics|observability)\b', re.IGNORECASE),
            "security": re.compile(r'\b(security|audit|compliance|policy)\b', re.IGNORECASE),
            "infrastructure": re.compile(r'\b(infra|kubernetes|cloud|aws|azure|gcp)\b', re.IGNORECASE),
            "database": re.compile(r'\b(database|db|sql|nosql|postgres|mysql)\b', re.IGNORECASE),
            "networking": re.compile(r'\b(network|dns|load.?balanc|firewall|vpn)\b', re.IGNORECASE),
            "storage": re.compile(r'\b(storage|volume|bucket|s3|blob)\b', re.IGNORECASE),
            "cost": re.compile(r'\b(cost|billing|budget|optimization|spend)\b', re.IGNORECASE),
            "ci_cd": re.compile(r'\b(ci|cd|pipeline|build|test|jenkins|github.?actions)\b', re.IGNORECASE),
            "logging": re.compile(r'\b(log|trace|debug|audit)\b', re.IGNORECASE)
        }

    async def process_agents_directory(self) -> Dict[str, AgentMetadata]:
        """Process all agents in directory"""
        logger.info(f"Processing agents directory: {self.agents_directory}")

        if not self.agents_directory.exists():
            logger.warning(f"Agents directory not found: {self.agents_directory}")
            return {}

        agent_files = list(self.agents_directory.glob("**/SKILL.md"))
        logger.info(f"Found {len(agent_files)} skill files")

        for skill_file in agent_files:
            try:
                metadata = await self.process_skill_file(skill_file)
                if metadata:
                    self.agent_cache[metadata.name] = metadata
                    await self._index_capabilities(metadata)

            except Exception as e:
                logger.error(f"Failed to process {skill_file}: {e}")

        # Generate skill mappings
        await self._generate_skill_mappings()

        logger.info(f"Processed {len(self.agent_cache)} agents successfully")
        return self.agent_cache

    async def process_skill_file(self, file_path: Path) -> Optional[AgentMetadata]:
        """Process individual skill file"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract frontmatter
            frontmatter = self._extract_frontmatter(content)
            if not frontmatter:
                return None

            # Extract basic metadata
            name = frontmatter.get('name', file_path.parent.name)
            description = frontmatter.get('description', '')

            # Extract enhanced metadata
            metadata_section = frontmatter.get('metadata', {})

            agent_metadata = AgentMetadata(
                name=name,
                description=description,
                risk_level=metadata_section.get('risk_level', 'medium'),
                autonomy=metadata_section.get('autonomy', 'conditional'),
                layer=metadata_section.get('layer', 'temporal'),
                human_gate=metadata_section.get('human_gate', ''),
                execution_mode=metadata_section.get('execution_mode', 'local'),
                sandbox_config=metadata_section.get('sandbox_config', {}),
                communication_preferences=metadata_section.get('communication_preferences', {}),
                version=frontmatter.get('version', '1.0.0'),
                last_updated=asyncio.get_event_loop().time()
            )

            # Extract capabilities from description and content
            agent_metadata.capabilities = await self._extract_capabilities(content)
            agent_metadata.dependencies = self._extract_dependencies(content)
            agent_metadata.tags = self._extract_tags(content)

            return agent_metadata

        except Exception as e:
            logger.error(f"Error processing skill file {file_path}: {e}")
            return None

    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract YAML frontmatter from markdown"""
        import yaml

        if not content.startswith('---'):
            return None

        try:
            end_pos = content.find('---', 3)
            if end_pos == -1:
                return None

            frontmatter_text = content[3:end_pos]
            return yaml.safe_load(frontmatter_text)

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse frontmatter: {e}")
            return None

    async def _extract_capabilities(self, content: str) -> Set[str]:
        """Extract capabilities from content using NLP patterns"""
        capabilities = set()

        # Apply pattern matching
        for capability, pattern in self.capability_patterns.items():
            if pattern.search(content):
                capabilities.add(capability)

        # Extract explicit capability declarations
        explicit_caps = re.findall(r'@capability:(\w+)', content, re.IGNORECASE)
        capabilities.update(explicit_caps)

        # Extract tool usage patterns
        tool_patterns = {
            "terraform": re.compile(r'\bterraform\b', re.IGNORECASE),
            "kubernetes": re.compile(r'\bkubectl|kubernetes|k8s\b', re.IGNORECASE),
            "docker": re.compile(r'\bdocker\b', re.IGNORECASE),
            "helm": re.compile(r'\bhelm\b', re.IGNORECASE),
            "ansible": re.compile(r'\bansible\b', re.IGNORECASE),
            "aws": re.compile(r'\baws|ec2|s3|lambda\b', re.IGNORECASE),
            "azure": re.compile(r'\bazure|aks\b', re.IGNORECASE),
            "gcp": re.compile(r'\bgcp|gke\b', re.IGNORECASE)
        }

        for tool, pattern in tool_patterns.items():
            if pattern.search(content):
                capabilities.add(f"tool_{tool}")

        return capabilities

    def _extract_dependencies(self, content: str) -> Set[str]:
        """Extract skill dependencies"""
        dependencies = set()

        # Extract @depends declarations
        deps = re.findall(r'@depends:(\w+)', content, re.IGNORECASE)
        dependencies.update(deps)

        # Extract @requires declarations
        reqs = re.findall(r'@requires:(\w+)', content, re.IGNORECASE)
        dependencies.update(reqs)

        return dependencies

    def _extract_tags(self, content: str) -> Set[str]:
        """Extract tags from content"""
        tags = set()

        # Extract @tag declarations
        tag_matches = re.findall(r'@tag:(\w+)', content, re.IGNORECASE)
        tags.update(tag_matches)

        # Extract category hints
        if 'infrastructure' in content.lower():
            tags.add('infrastructure')
        if 'security' in content.lower():
            tags.add('security')
        if 'monitoring' in content.lower():
            tags.add('monitoring')
        if 'deployment' in content.lower():
            tags.add('deployment')

        return tags

    async def _index_capabilities(self, metadata: AgentMetadata):
        """Index agent capabilities for fast lookup"""
        for capability in metadata.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = set()
            self.capability_index[capability].add(metadata.name)

    async def _generate_skill_mappings(self):
        """Generate intelligent skill mappings"""
        # For each agent, find related agents based on capabilities
        for agent_name, metadata in self.agent_cache.items():
            mappings = []

            for capability in metadata.capabilities:
                related_agents = self.capability_index.get(capability, set()) - {agent_name}

                for related_agent in related_agents:
                    related_metadata = self.agent_cache[related_agent]

                    # Calculate capability match score
                    common_caps = len(metadata.capabilities & related_metadata.capabilities)
                    total_caps = len(metadata.capabilities | related_metadata.capabilities)
                    match_score = common_caps / total_caps if total_caps > 0 else 0

                    # Calculate confidence score based on risk levels and autonomy
                    risk_compatibility = self._calculate_risk_compatibility(
                        metadata.risk_level, related_metadata.risk_level
                    )
                    autonomy_compatibility = self._calculate_autonomy_compatibility(
                        metadata.autonomy, related_metadata.autonomy
                    )

                    confidence_score = (match_score + risk_compatibility + autonomy_compatibility) / 3

                    if confidence_score > 0.3:  # Minimum threshold
                        mapping = SkillMapping(
                            skill_name=related_metadata.name,
                            agent_name=agent_name,
                            capability_match=match_score,
                            confidence_score=confidence_score,
                            context_requirements=self._generate_context_requirements(metadata, related_metadata)
                        )
                        mappings.append(mapping)

            self.skill_mappings[agent_name] = mappings

    def _calculate_risk_compatibility(self, risk1: str, risk2: str) -> float:
        """Calculate risk compatibility score"""
        risk_levels = {'low': 1, 'medium': 2, 'high': 3}
        level1 = risk_levels.get(risk1, 2)
        level2 = risk_levels.get(risk2, 2)

        # Higher compatibility for similar risk levels
        return 1.0 - abs(level1 - level2) / 2.0

    def _calculate_autonomy_compatibility(self, autonomy1: str, autonomy2: str) -> float:
        """Calculate autonomy compatibility score"""
        autonomy_levels = {'supervised': 1, 'conditional': 2, 'full_auto': 3}
        level1 = autonomy_levels.get(autonomy1, 2)
        level2 = autonomy_levels.get(autonomy2, 2)

        # Higher compatibility for similar autonomy levels
        return 1.0 - abs(level1 - level2) / 2.0

    def _generate_context_requirements(self, agent1: AgentMetadata, agent2: AgentMetadata) -> Dict[str, Any]:
        """Generate context requirements for skill mapping"""
        requirements = {}

        # Platform compatibility
        if agent1.communication_preferences or agent2.communication_preferences:
            requirements['platform_compatibility'] = {
                'agent1_platforms': list(agent1.communication_preferences.keys()),
                'agent2_platforms': list(agent2.communication_preferences.keys())
            }

        # Execution mode compatibility
        if agent1.execution_mode != agent2.execution_mode:
            requirements['execution_mode_bridge'] = {
                'agent1_mode': agent1.execution_mode,
                'agent2_mode': agent2.execution_mode
            }

        # Dependency alignment
        if agent1.dependencies & agent2.capabilities:
            requirements['dependency_satisfaction'] = list(agent1.dependencies & agent2.capabilities)

        return requirements

    async def find_best_agent(self, request_description: str,
                             context: Dict[str, Any] = None) -> Optional[Tuple[AgentMetadata, float]]:
        """Find best agent for request"""
        context = context or {}

        # Extract capabilities from request
        request_capabilities = await self._extract_capabilities(request_description)
        request_tags = self._extract_tags(request_description)

        best_agent = None
        best_score = 0.0

        for agent_name, metadata in self.agent_cache.items():
            score = self._calculate_agent_score(
                metadata, request_capabilities, request_tags, context
            )

            if score > best_score:
                best_score = score
                best_agent = metadata

        return (best_agent, best_score) if best_agent else None

    def _calculate_agent_score(self, metadata: AgentMetadata,
                              request_capabilities: Set[str],
                              request_tags: Set[str],
                              context: Dict[str, Any]) -> float:
        """Calculate how well agent matches request"""
        score = 0.0

        # Capability matching (40% weight)
        capability_matches = len(request_capabilities & metadata.capabilities)
        capability_score = capability_matches / len(request_capabilities) if request_capabilities else 0
        score += capability_score * 0.4

        # Tag matching (20% weight)
        tag_matches = len(request_tags & metadata.tags)
        tag_score = tag_matches / len(request_tags) if request_tags else 0
        score += tag_score * 0.2

        # Description similarity (20% weight)
        # Simple keyword matching for now
        desc_words = set(metadata.description.lower().split())
        request_words = set(request_description.lower().split())
        desc_score = len(desc_words & request_words) / len(request_words) if request_words else 0
        score += desc_score * 0.2

        # Context compatibility (20% weight)
        context_score = self._calculate_context_compatibility(metadata, context)
        score += context_score * 0.2

        return score

    def _calculate_context_compatibility(self, metadata: AgentMetadata, context: Dict[str, Any]) -> float:
        """Calculate context compatibility score"""
        score = 0.0
        factors = 0

        # Platform compatibility
        platform = context.get('platform')
        if platform and metadata.communication_preferences:
            if platform in metadata.communication_preferences:
                score += 1.0
            factors += 1

        # Risk level compatibility
        risk_preference = context.get('risk_tolerance', 'medium')
        if risk_preference == metadata.risk_level:
            score += 1.0
        elif abs(['low', 'medium', 'high'].index(risk_preference) -
                 ['low', 'medium', 'high'].index(metadata.risk_level)) == 1:
            score += 0.5
        factors += 1

        # Execution mode preference
        execution_preference = context.get('execution_mode')
        if execution_preference and execution_preference == metadata.execution_mode:
            score += 1.0
            factors += 1

        return score / factors if factors > 0 else 0.5

    def get_agent_recommendations(self, agent_name: str, limit: int = 5) -> List[SkillMapping]:
        """Get recommended related agents"""
        mappings = self.skill_mappings.get(agent_name, [])
        return sorted(mappings, key=lambda m: m.confidence_score, reverse=True)[:limit]

    def get_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Get all agents with specific capability"""
        agent_names = self.capability_index.get(capability, set())
        return [self.agent_cache[name] for name in agent_names if name in self.agent_cache]

    def get_agents_by_tag(self, tag: str) -> List[AgentMetadata]:
        """Get all agents with specific tag"""
        return [metadata for metadata in self.agent_cache.values() if tag in metadata.tags]

    def validate_agent_dependencies(self, agent_name: str) -> Dict[str, bool]:
        """Validate that agent dependencies are satisfied"""
        if agent_name not in self.agent_cache:
            return {}

        metadata = self.agent_cache[agent_name]
        validation = {}

        for dependency in metadata.dependencies:
            # Check if dependency is a capability provided by another agent
            satisfied = dependency in self.capability_index and len(self.capability_index[dependency]) > 0
            validation[dependency] = satisfied

        return validation

    async def refresh_cache(self):
        """Refresh agent cache from filesystem"""
        self.agent_cache.clear()
        self.skill_mappings.clear()
        self.capability_index.clear()
        await self.process_agents_directory()


# Export key classes
__all__ = [
    'AgentMetadata',
    'SkillMapping',
    'AGENTSProcessor'
]
