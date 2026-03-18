"""
Middleware system for Open SWE Gateway
LangChain-compatible middleware with GitOps safety patterns
"""

from typing import Dict, Any, Callable, Awaitable
from datetime import datetime
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AgentState:
    """Represents the current state of an agent execution"""

    def __init__(self, messages: list = None, context: dict = None, task_id: str = None):
        self.messages = messages or []
        self.context = context or {}
        self.task_id = task_id
        self.metadata = {}
        self.gitops_validated = False
        self.risk_assessment = {}
        self.pr_created = False

class MiddlewareResult:
    """Result of middleware execution"""

    def __init__(self, success: bool = True, modified_state: AgentState = None,
                 error_message: str = None):
        self.success = success
        self.modified_state = modified_state
        self.error_message = error_message

class Middleware(ABC):
    """Abstract base class for middleware"""

    @abstractmethod
    async def execute(self, state: AgentState) -> MiddlewareResult:
        """Execute middleware logic"""
        pass

class GitOpsValidationMiddleware(Middleware):
    """Validate that planned actions comply with GitOps policies"""

    def __init__(self, gitops_client):
        self.gitops_client = gitops_client

    async def execute(self, state: AgentState) -> MiddlewareResult:
        """Validate planned actions against GitOps policies"""

        try:
            # Extract planned actions from state
            planned_actions = self._extract_planned_actions(state)

            # Validate against GitOps policies
            for action in planned_actions:
                if not await self._validate_gitops_compliance(action):
                    return MiddlewareResult(
                        success=False,
                        error_message=f"Action {action.get('type')} violates GitOps policy: {action.get('violation')}"
                    )

            # Add compliance metadata to state
            state.gitops_validated = True
            state.metadata["validation_timestamp"] = datetime.utcnow().isoformat()

            return MiddlewareResult(success=True, modified_state=state)

        except Exception as e:
            logger.error(f"GitOps validation failed: {str(e)}")
            return MiddlewareResult(success=False, error_message=str(e))

    def _extract_planned_actions(self, state: AgentState) -> list:
        """Extract planned actions from agent state"""
        # Implement action extraction logic
        return state.context.get("planned_actions", [])

    async def _validate_gitops_compliance(self, action: dict) -> bool:
        """Validate action against GitOps policies"""
        # Implement GitOps compliance validation
        # Check for PR requirements, risk levels, etc.
        return True  # Placeholder

class RiskAssessmentMiddleware(Middleware):
    """Dynamically assess risk level of planned actions"""

    def __init__(self, risk_engine):
        self.risk_engine = risk_engine

    async def execute(self, state: AgentState) -> MiddlewareResult:
        """Assess risk level of planned actions"""

        try:
            # Extract context and planned actions
            context = state.context
            actions = self._extract_planned_actions(state)

            # Calculate dynamic risk score
            risk_score = await self._calculate_risk_score(context, actions)

            # Determine required human gates
            human_gates = await self._determine_human_gates(risk_score, context)

            # Update state with risk assessment
            state.risk_assessment = {
                "score": risk_score,
                "level": self._map_score_to_level(risk_score),
                "human_gates": human_gates,
                "timestamp": datetime.utcnow().isoformat()
            }

            return MiddlewareResult(success=True, modified_state=state)

        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            return MiddlewareResult(success=False, error_message=str(e))

    def _extract_planned_actions(self, state: AgentState) -> list:
        """Extract planned actions from agent state"""
        return state.context.get("planned_actions", [])

    async def _calculate_risk_score(self, context: dict, actions: list) -> float:
        """Calculate dynamic risk score"""
        # Implement risk scoring logic
        base_score = 0.0

        for action in actions:
            if action.get("type") == "infrastructure_change":
                base_score += 0.7
            elif action.get("type") == "security_change":
                base_score += 0.9
            elif action.get("type") == "read_only":
                base_score += 0.1

        return min(base_score, 1.0)

    async def _determine_human_gates(self, risk_score: float, context: dict) -> list:
        """Determine required human gates based on risk score"""
        gates = []

        if risk_score > 0.8:
            gates.append("security_review")
            gates.append("pr_approval")
        elif risk_score > 0.5:
            gates.append("pr_approval")
        elif risk_score > 0.2:
            gates.append("conditional_approval")

        return gates

    def _map_score_to_level(self, score: float) -> str:
        """Map risk score to risk level"""
        if score > 0.8:
            return "high"
        elif score > 0.5:
            return "medium"
        elif score > 0.2:
            return "low"
        else:
            return "minimal"

class MessageQueueMiddleware(Middleware):
    """Inject pending user messages before model call"""

    def __init__(self, message_queue):
        self.message_queue = message_queue

    async def execute(self, state: AgentState) -> MiddlewareResult:
        """Inject pending messages into agent state"""

        try:
            if state.task_id:
                # Get pending messages for this task
                pending_messages = await self.message_queue.get_pending_messages(state.task_id)

                if pending_messages:
                    # Inject messages into agent state
                    for msg in pending_messages:
                        state.messages.append({
                            "role": "user",
                            "content": msg["content"],
                            "timestamp": msg["timestamp"]
                        })

                    state.metadata["messages_injected"] = len(pending_messages)

                    # Clear processed messages
                    await self.message_queue.clear_messages(state.task_id, pending_messages)

            return MiddlewareResult(success=True, modified_state=state)

        except Exception as e:
            logger.error(f"Message queue injection failed: {str(e)}")
            return MiddlewareResult(success=False, error_message=str(e))

class PRSafetyNetMiddleware(Middleware):
    """Ensure PR is created if agent didn't handle it"""

    def __init__(self, git_client, pr_creator):
        self.git_client = git_client
        self.pr_creator = pr_creator

    async def execute(self, state: AgentState) -> MiddlewareResult:
        """Ensure PR creation if agent didn't handle it"""

        try:
            # Check if agent already created PR
            if not state.pr_created:
                # Extract changes from state
                changes = self._extract_changes_from_state(state)

                if changes:
                    # Create PR using git-automation skill
                    pr_url = await self._create_pr_from_changes(changes, state)

                    if pr_url:
                        state.pr_created = True
                        state.metadata["pr_url"] = pr_url
                        state.metadata["pr_auto_created"] = True

            return MiddlewareResult(success=True, modified_state=state)

        except Exception as e:
            logger.error(f"PR safety net failed: {str(e)}")
            return MiddlewareResult(success=False, error_message=str(e))

    def _extract_changes_from_state(self, state: AgentState) -> list:
        """Extract file changes from agent state"""
        return state.context.get("file_changes", [])

    async def _create_pr_from_changes(self, changes: list, state: AgentState) -> str:
        """Create PR from changes using git automation"""
        # Implement PR creation logic
        return "https://github.com/example/pr/123"

class ToolErrorMiddleware(Middleware):
    """Catch and handle tool errors gracefully"""

    async def execute(self, state: AgentState) -> MiddlewareResult:
        """Handle tool errors in agent state"""

        try:
            # Check for tool errors in state
            tool_errors = state.context.get("tool_errors", [])

            for error in tool_errors:
                # Log error
                logger.warning(f"Tool error in task {state.task_id}: {error}")

                # Add error context to messages for agent
                error_message = {
                    "role": "system",
                    "content": f"Tool error occurred: {error.get('message', 'Unknown error')}. Please handle this appropriately.",
                    "timestamp": datetime.utcnow().isoformat()
                }
                state.messages.append(error_message)

            # Clear processed errors
            state.context["tool_errors"] = []

            return MiddlewareResult(success=True, modified_state=state)

        except Exception as e:
            logger.error(f"Tool error handling failed: {str(e)}")
            return MiddlewareResult(success=False, error_message=str(e))

class MiddlewarePipeline:
    """Pipeline for executing middleware in order"""

    def __init__(self):
        self.middleware = []

    def add_middleware(self, middleware: Middleware):
        """Add middleware to pipeline"""
        self.middleware.append(middleware)

    async def execute(self, state: AgentState) -> MiddlewareResult:
        """Execute all middleware in pipeline"""

        current_state = state

        for middleware in self.middleware:
            try:
                result = await middleware.execute(current_state)

                if not result.success:
                    logger.error(f"Middleware {middleware.__class__.__name__} failed: {result.error_message}")
                    return result

                if result.modified_state:
                    current_state = result.modified_state

            except Exception as e:
                logger.error(f"Middleware execution failed: {str(e)}")
                return MiddlewareResult(success=False, error_message=str(e))

        return MiddlewareResult(success=True, modified_state=current_state)

# Factory function to create default middleware pipeline
def create_default_middleware_pipeline(gitops_client=None, risk_engine=None,
                                    message_queue=None, git_client=None, pr_creator=None) -> MiddlewarePipeline:
    """Create default middleware pipeline with GitOps safety"""

    pipeline = MiddlewarePipeline()

    # Add middleware in order of execution
    pipeline.add_middleware(ToolErrorMiddleware())
    pipeline.add_middleware(GitOpsValidationMiddleware(gitops_client))
    pipeline.add_middleware(RiskAssessmentMiddleware(risk_engine))
    pipeline.add_middleware(MessageQueueMiddleware(message_queue))
    pipeline.add_middleware(PRSafetyNetMiddleware(git_client, pr_creator))

    return pipeline
