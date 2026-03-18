"""
Communication Layer for Open SWE Integration

This module provides unified agent interfaces across Slack, Linear, and GitHub platforms,
enabling infrastructure operations through natural development workflows.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported communication platforms"""
    SLACK = "slack"
    LINEAR = "linear"
    GITHUB = "github"
    INTERNAL = "internal"


@dataclass
class ConversationContext:
    """Conversation context across platforms"""
    id: str
    platform: Platform
    thread_id: Optional[str] = None
    channel: Optional[str] = None
    repository: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, text: str, response: str):
        """Add message to conversation context"""
        self.messages.append({
            "timestamp": asyncio.get_event_loop().time(),
            "text": text,
            "response": response
        })

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps({
            "id": self.id,
            "platform": self.platform.value,
            "thread_id": self.thread_id,
            "channel": self.channel,
            "repository": self.repository,
            "messages": self.messages,
            "metadata": self.metadata
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'ConversationContext':
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return cls(
            id=data["id"],
            platform=Platform(data["platform"]),
            thread_id=data.get("thread_id"),
            channel=data.get("channel"),
            repository=data.get("repository"),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class AgentRequest:
    """Unified agent request across platforms"""
    platform: Platform
    text: str
    user: str
    context: ConversationContext
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Platform-specific fields
    channel: Optional[str] = None
    thread_id: Optional[str] = None
    issue_id: Optional[str] = None
    pr_number: Optional[int] = None
    repository: Optional[str] = None


@dataclass
class AgentResponse:
    """Unified agent response across platforms"""
    text: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlatformAdapter(ABC):
    """Abstract base class for platform-specific adapters"""

    @abstractmethod
    async def normalize_request(self, platform_request: Any) -> AgentRequest:
        """Convert platform-specific request to unified AgentRequest"""
        pass

    @abstractmethod
    async def format_response(self, response: AgentResponse) -> Any:
        """Format unified response for platform-specific delivery"""
        pass

    @abstractmethod
    async def send_response(self, response: Any, context: Dict[str, Any]) -> None:
        """Send formatted response to platform"""
        pass


class ConversationManager:
    """Manages conversation context across platforms"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.local_storage: Dict[str, ConversationContext] = {}

    async def get_context(self, conversation_id: str) -> ConversationContext:
        """Get conversation context"""
        if self.redis:
            key = f"conversation:{conversation_id}"
            data = await self.redis.get(key)
            return ConversationContext.from_json(data) if data else ConversationContext(id=conversation_id, platform=Platform.INTERNAL)
        else:
            return self.local_storage.get(conversation_id, ConversationContext(id=conversation_id, platform=Platform.INTERNAL))

    async def save_context(self, context: ConversationContext):
        """Save conversation context"""
        if self.redis:
            key = f"conversation:{context.id}"
            await self.redis.setex(key, 86400, context.to_json())  # 24 hour expiry
        else:
            self.local_storage[context.id] = context


class RepositoryRouter:
    """Routes requests to appropriate repository contexts"""

    def __init__(self, repo_configs: Dict[str, Dict[str, Any]]):
        self.repo_configs = repo_configs

    def parse_repo_reference(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract repository reference from text"""
        import re
        match = re.search(r'repo:([^/\s]+)/([^/\s]+)', text)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def get_repo_config(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get configuration for repository"""
        return self.repo_configs.get(f"{owner}/{repo}", {})


class SkillRouter:
    """Routes requests to appropriate skills"""

    def __init__(self, skill_registry):
        self.skill_registry = skill_registry

    async def route_request(self, request: AgentRequest) -> AgentResponse:
        """Route request to appropriate skill"""

        # Simple routing logic - in real implementation would use NLP/ML
        text = request.text.lower()

        if "deploy" in text or "deployment" in text:
            skill_name = "deployment-manager"
        elif "validate" in text or "validation" in text:
            skill_name = "infrastructure-validator"
        elif "monitor" in text or "status" in text:
            skill_name = "system-monitor"
        else:
            skill_name = "general-assistant"

        # Get skill from registry
        skill = self.skill_registry.get(skill_name)
        if skill:
            return await skill.execute(request)
        else:
            return AgentResponse(
                text=f"Sorry, I don't have a skill for that operation: {skill_name}",
                actions=[]
            )


class UnifiedAgent:
    """Unified agent across all communication platforms"""

    def __init__(self, platform_adapters: Dict[Platform, PlatformAdapter],
                 conversation_manager: ConversationManager,
                 skill_router: SkillRouter,
                 repository_router: RepositoryRouter):
        self.adapters = platform_adapters
        self.conversations = conversation_manager
        self.skills = skill_router
        self.repositories = repository_router

    async def handle_request(self, platform_request: Any, platform: Platform) -> Any:
        """Handle requests from any platform uniformly"""

        try:
            # Get platform adapter
            adapter = self.adapters.get(platform)
            if not adapter:
                logger.error(f"No adapter for platform: {platform}")
                return await self._create_error_response(platform, "Platform not supported")

            # Normalize platform-specific request
            normalized_request = await adapter.normalize_request(platform_request)

            # Get conversation context
            context = await self.conversations.get_context(normalized_request.context.id)

            # Update request with context
            normalized_request.context = context

            # Route to repository if specified
            owner, repo = self.repositories.parse_repo_reference(normalized_request.text)
            if owner and repo:
                normalized_request.repository = f"{owner}/{repo}"
                normalized_request.metadata["repo_config"] = self.repositories.get_repo_config(owner, repo)

            # Route to appropriate skills
            skill_response = await self.skills.route_request(normalized_request)

            # Update conversation context
            context.add_message(normalized_request.text, skill_response.text)
            await self.conversations.save_context(context)

            # Format response for platform
            platform_response = await adapter.format_response(skill_response)

            return platform_response

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return await self._create_error_response(platform, str(e))

    async def _create_error_response(self, platform: Platform, error: str) -> Any:
        """Create error response for platform"""
        adapter = self.adapters.get(platform)
        if adapter:
            error_response = AgentResponse(
                text=f"Sorry, I encountered an error: {error}",
                actions=[]
            )
            return await adapter.format_response(error_response)
        else:
            return {"text": f"Error: {error}"}


class CommunicationLayer:
    """Main communication layer coordinating all platform integrations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.unified_agent = None
        self.platform_handlers = {}

    async def initialize(self):
        """Initialize communication layer"""

        # Initialize platform adapters
        platform_adapters = {}
        for platform_name, platform_config in self.config.get("platforms", {}).items():
            platform = Platform(platform_name)
            adapter = self._create_platform_adapter(platform, platform_config)
            if adapter:
                platform_adapters[platform] = adapter

        # Initialize components
        conversation_manager = ConversationManager()
        skill_router = SkillRouter(self.config.get("skill_registry", {}))
        repository_router = RepositoryRouter(self.config.get("repositories", {}))

        # Create unified agent
        self.unified_agent = UnifiedAgent(
            platform_adapters=platform_adapters,
            conversation_manager=conversation_manager,
            skill_router=skill_router,
            repository_router=repository_router
        )

        logger.info("Communication layer initialized")

    def _create_platform_adapter(self, platform: Platform, config: Dict[str, Any]) -> Optional[PlatformAdapter]:
        """Create platform-specific adapter"""

        if platform == Platform.SLACK:
            from .slack.adapter import SlackAdapter
            return SlackAdapter(config)
        elif platform == Platform.LINEAR:
            from .linear.adapter import LinearAdapter
            return LinearAdapter(config)
        elif platform == Platform.GITHUB:
            from .github.adapter import GitHubAdapter
            return GitHubAdapter(config)
        else:
            logger.warning(f"No adapter available for platform: {platform}")
            return None

    async def handle_platform_request(self, platform: Platform, request: Any) -> Any:
        """Handle request from specific platform"""
        if not self.unified_agent:
            await self.initialize()

        return await self.unified_agent.handle_request(request, platform)

    async def register_platform_handler(self, platform: Platform, handler):
        """Register platform-specific event handler"""
        self.platform_handlers[platform] = handler

    async def shutdown(self):
        """Shutdown communication layer"""
        logger.info("Communication layer shutdown")


# Placeholder adapters for initial implementation
class PlaceholderAdapter(PlatformAdapter):
    """Placeholder adapter for development"""

    def __init__(self, config):
        self.config = config

    async def normalize_request(self, platform_request):
        return AgentRequest(
            platform=Platform.INTERNAL,
            text=str(platform_request),
            user="system",
            context=ConversationContext(id="placeholder", platform=Platform.INTERNAL)
        )

    async def format_response(self, response):
        return {"text": response.text, "actions": response.actions}

    async def send_response(self, response, context):
        print(f"Sending response: {response}")


# Export key classes
__all__ = [
    'Platform',
    'ConversationContext',
    'AgentRequest',
    'AgentResponse',
    'PlatformAdapter',
    'ConversationManager',
    'RepositoryRouter',
    'SkillRouter',
    'UnifiedAgent',
    'CommunicationLayer'
]
