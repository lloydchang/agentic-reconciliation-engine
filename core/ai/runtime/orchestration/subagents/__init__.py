"""
Subagent Coordination System for Open SWE Integration

This module provides advanced orchestration capabilities by enabling subagent spawning,
coordination, and result consolidation. It integrates Deep Agents subagent patterns
with the existing GitOps Temporal workflow system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


class SubagentStatus(Enum):
    """Status of subagent execution"""
    CREATED = "created"
    SPAWNING = "spawning"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CoordinationStrategy(Enum):
    """Strategies for coordinating multiple subagents"""
    PARALLEL = "parallel"      # All subagents run simultaneously
    SEQUENTIAL = "sequential"  # Subagents run one after another
    DEPENDENT = "dependent"    # Subagents run based on dependencies
    COMPETITIVE = "competitive" # Subagents compete for best result


@dataclass
class SubagentSpec:
    """Specification for a subagent"""
    name: str
    skill_name: str
    config: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    priority: int = 1   # 1-10, higher is more important


@dataclass
class SubagentInstance:
    """Runtime instance of a subagent"""
    id: str
    spec: SubagentSpec
    status: SubagentStatus = SubagentStatus.CREATED
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Get execution duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def mark_started(self):
        """Mark subagent as started"""
        self.start_time = asyncio.get_event_loop().time()
        self.status = SubagentStatus.ACTIVE

    def mark_completed(self, result: Any = None):
        """Mark subagent as completed"""
        self.end_time = asyncio.get_event_loop().time()
        self.result = result
        self.status = SubagentStatus.COMPLETED

    def mark_failed(self, error: str):
        """Mark subagent as failed"""
        self.end_time = asyncio.get_event_loop().time()
        self.error = error
        self.status = SubagentStatus.FAILED


@dataclass
class CoordinationContext:
    """Context for coordinating multiple subagents"""
    request_id: str
    strategy: CoordinationStrategy
    subagents: Dict[str, SubagentInstance] = field(default_factory=dict)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def add_subagent(self, spec: SubagentSpec) -> SubagentInstance:
        """Add a subagent to coordination"""
        instance = SubagentInstance(
            id=f"{self.request_id}-{spec.name}",
            spec=spec
        )
        self.subagents[spec.name] = instance
        return instance

    def get_ready_subagents(self) -> List[SubagentInstance]:
        """Get subagents ready to execute (dependencies satisfied)"""
        ready = []
        for instance in self.subagents.values():
            if instance.status == SubagentStatus.CREATED:
                # Check if all dependencies are completed
                deps_satisfied = all(
                    dep in self.results or
                    self.subagents.get(dep, SubagentInstance("", SubagentSpec(""))).status == SubagentStatus.COMPLETED
                    for dep in instance.spec.dependencies
                )
                if deps_satisfied:
                    ready.append(instance)
        return ready

    def mark_started(self):
        """Mark coordination as started"""
        self.start_time = asyncio.get_event_loop().time()

    def mark_completed(self):
        """Mark coordination as completed"""
        self.end_time = asyncio.get_event_loop().time()


class SubagentSpawner(ABC):
    """Abstract base class for spawning subagents"""

    @abstractmethod
    async def spawn_subagent(self, spec: SubagentSpec, context: CoordinationContext) -> SubagentInstance:
        """Spawn a new subagent instance"""
        pass

    @abstractmethod
    async def monitor_subagent(self, instance: SubagentInstance) -> None:
        """Monitor subagent execution"""
        pass

    @abstractmethod
    async def cancel_subagent(self, instance: SubagentInstance) -> None:
        """Cancel subagent execution"""
        pass


class TemporalSubagentSpawner(SubagentSpawner):
    """Temporal-based subagent spawner"""

    def __init__(self, temporal_client):
        self.temporal_client = temporal_client

    async def spawn_subagent(self, spec: SubagentSpec, context: CoordinationContext) -> SubagentInstance:
        """Spawn subagent via Temporal workflow"""
        try:
            # Create Temporal workflow execution for subagent
            workflow_id = f"subagent-{spec.name}-{uuid.uuid4()}"

            # Start Temporal workflow with subagent specification
            execution = await self.temporal_client.start_workflow(
                workflow="SubagentExecutionWorkflow",
                args=[spec, context.shared_context],
                id=workflow_id,
                task_queue="infrastructure-agents"
            )

            instance = SubagentInstance(
                id=workflow_id,
                spec=spec,
                status=SubagentStatus.SPAWNING,
                metadata={"temporal_execution": execution}
            )

            return instance

        except Exception as e:
            logger.error(f"Failed to spawn subagent {spec.name}: {e}")
            raise

    async def monitor_subagent(self, instance: SubagentInstance) -> None:
        """Monitor Temporal workflow execution"""
        try:
            execution = instance.metadata.get("temporal_execution")
            if execution:
                # Check workflow status
                status = await self.temporal_client.describe_workflow_execution(
                    workflow_id=instance.id
                )

                # Update instance status based on workflow status
                if status.status.name == "COMPLETED":
                    instance.status = SubagentStatus.COMPLETED
                    # Get result from workflow
                    result = await self.temporal_client.get_workflow_result(instance.id)
                    instance.result = result
                elif status.status.name == "FAILED":
                    instance.status = SubagentStatus.FAILED
                    instance.error = "Workflow execution failed"
                elif status.status.name == "RUNNING":
                    instance.status = SubagentStatus.ACTIVE

        except Exception as e:
            logger.error(f"Failed to monitor subagent {instance.id}: {e}")

    async def cancel_subagent(self, instance: SubagentInstance) -> None:
        """Cancel Temporal workflow"""
        try:
            await self.temporal_client.cancel_workflow(instance.id)
            instance.status = SubagentStatus.CANCELLED
        except Exception as e:
            logger.error(f"Failed to cancel subagent {instance.id}: {e}"


class ResultConsolidator:
    """Consolidates results from multiple subagents"""

    def __init__(self):
        self.consolidation_strategies: Dict[str, Callable] = {
            "first_completed": self._first_completed,
            "majority_vote": self._majority_vote,
            "weighted_average": self._weighted_average,
            "merge_results": self._merge_results,
            "best_result": self._best_result
        }

    async def consolidate(self, context: CoordinationContext, strategy: str = "merge_results") -> Any:
        """Consolidate results from all completed subagents"""
        if strategy not in self.consolidation_strategies:
            raise ValueError(f"Unknown consolidation strategy: {strategy}")

        consolidator = self.consolidation_strategies[strategy]
        return await consolidator(context)

    async def _first_completed(self, context: CoordinationContext) -> Any:
        """Return result from first completed subagent"""
        for instance in context.subagents.values():
            if instance.status == SubagentStatus.COMPLETED and instance.result:
                return instance.result
        return None

    async def _majority_vote(self, context: CoordinationContext) -> Any:
        """Return result with majority agreement"""
        results = {}
        for instance in context.subagents.values():
            if instance.status == SubagentStatus.COMPLETED and instance.result:
                result_key = str(instance.result)
                results[result_key] = results.get(result_key, 0) + 1

        if not results:
            return None

        # Return result with most votes
        return max(results.items(), key=lambda x: x[1])[0]

    async def _weighted_average(self, context: CoordinationContext) -> Any:
        """Return weighted average of numeric results"""
        total_weight = 0
        weighted_sum = 0

        for instance in context.subagents.values():
            if instance.status == SubagentStatus.COMPLETED and instance.result:
                try:
                    value = float(instance.result)
                    weight = instance.spec.priority
                    weighted_sum += value * weight
                    total_weight += weight
                except (ValueError, TypeError):
                    continue

        return weighted_sum / total_weight if total_weight > 0 else None

    async def _merge_results(self, context: CoordinationContext) -> Dict[str, Any]:
        """Merge all results into a dictionary"""
        merged = {}
        for name, instance in context.subagents.items():
            if instance.status == SubagentStatus.COMPLETED:
                merged[name] = {
                    "result": instance.result,
                    "duration": instance.duration,
                    "priority": instance.spec.priority
                }
        return merged

    async def _best_result(self, context: CoordinationContext) -> Any:
        """Return result from highest priority subagent"""
        best_instance = None
        best_priority = -1

        for instance in context.subagents.values():
            if (instance.status == SubagentStatus.COMPLETED and
                instance.spec.priority > best_priority):
                best_instance = instance
                best_priority = instance.spec.priority

        return best_instance.result if best_instance else None


class SubagentCoordinator:
    """Main coordinator for subagent orchestration"""

    def __init__(self, spawner: SubagentSpawner, consolidator: ResultConsolidator):
        self.spawner = spawner
        self.consolidator = consolidator
        self.active_coordinations: Dict[str, CoordinationContext] = {}

    async def coordinate_subagents(
        self,
        request_id: str,
        subagent_specs: List[SubagentSpec],
        strategy: CoordinationStrategy = CoordinationStrategy.PARALLEL,
        consolidation_strategy: str = "merge_results",
        timeout: int = 600
    ) -> Dict[str, Any]:
        """Coordinate execution of multiple subagents"""

        context = CoordinationContext(
            request_id=request_id,
            strategy=strategy
        )

        # Add all subagents to context
        for spec in subagent_specs:
            context.add_subagent(spec)

        self.active_coordinations[request_id] = context
        context.mark_started()

        try:
            # Execute coordination based on strategy
            if strategy == CoordinationStrategy.PARALLEL:
                await self._execute_parallel(context, timeout)
            elif strategy == CoordinationStrategy.SEQUENTIAL:
                await self._execute_sequential(context, timeout)
            elif strategy == CoordinationStrategy.DEPENDENT:
                await self._execute_dependent(context, timeout)
            elif strategy == CoordinationStrategy.COMPETITIVE:
                await self._execute_competitive(context, timeout)

            # Consolidate results
            final_result = await self.consolidator.consolidate(context, consolidation_strategy)

            context.mark_completed()
            return {
                "success": True,
                "result": final_result,
                "coordination_context": context,
                "subagent_results": context.results
            }

        except Exception as e:
            logger.error(f"Coordination failed for {request_id}: {e}")
            context.mark_completed()
            return {
                "success": False,
                "error": str(e),
                "coordination_context": context
            }

        finally:
            # Clean up
            del self.active_coordinations[request_id]

    async def _execute_parallel(self, context: CoordinationContext, timeout: int):
        """Execute all subagents in parallel"""
        tasks = []

        for instance in context.subagents.values():
            task = asyncio.create_task(self._execute_single_subagent(instance, context))
            tasks.append(task)

        # Wait for all tasks with timeout
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)

    async def _execute_sequential(self, context: CoordinationContext, timeout: int):
        """Execute subagents sequentially"""
        start_time = asyncio.get_event_loop().time()

        for instance in context.subagents.values():
            if asyncio.get_event_loop().time() - start_time > timeout:
                break

            await self._execute_single_subagent(instance, context)

    async def _execute_dependent(self, context: CoordinationContext, timeout: int):
        """Execute subagents based on dependencies"""
        start_time = asyncio.get_event_loop().time()

        while context.get_ready_subagents():
            if asyncio.get_event_loop().time() - start_time > timeout:
                break

            ready_instances = context.get_ready_subagents()
            if not ready_instances:
                break

            # Execute ready instances in parallel
            tasks = [
                self._execute_single_subagent(instance, context)
                for instance in ready_instances
            ]
            await asyncio.gather(*tasks)

    async def _execute_competitive(self, context: CoordinationContext, timeout: int):
        """Execute subagents competitively (first to complete wins)"""
        tasks = []
        completion_event = asyncio.Event()

        async def execute_with_completion(instance):
            await self._execute_single_subagent(instance, context)
            if instance.status == SubagentStatus.COMPLETED:
                completion_event.set()

        for instance in context.subagents.values():
            task = asyncio.create_task(execute_with_completion(instance))
            tasks.append(task)

        # Wait for first completion or timeout
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()

    async def _execute_single_subagent(self, instance: SubagentInstance, context: CoordinationContext):
        """Execute a single subagent"""
        try:
            instance.mark_started()

            # Spawn subagent
            spawned_instance = await self.spawner.spawn_subagent(instance.spec, context)

            # Monitor until completion
            while spawned_instance.status in [SubagentStatus.SPAWNING, SubagentStatus.ACTIVE]:
                await asyncio.sleep(1)
                await self.spawner.monitor_subagent(spawned_instance)

            # Update instance with results
            instance.status = spawned_instance.status
            instance.result = spawned_instance.result
            instance.error = spawned_instance.error
            instance.end_time = spawned_instance.end_time

            # Store result in context
            if instance.status == SubagentStatus.COMPLETED:
                context.results[instance.spec.name] = instance.result

        except Exception as e:
            logger.error(f"Failed to execute subagent {instance.spec.name}: {e}")
            instance.mark_failed(str(e))

    async def cancel_coordination(self, request_id: str):
        """Cancel ongoing coordination"""
        context = self.active_coordinations.get(request_id)
        if context:
            for instance in context.subagents.values():
                if instance.status in [SubagentStatus.SPAWNING, SubagentStatus.ACTIVE]:
                    await self.spawner.cancel_subagent(instance)
            del self.active_coordinations[request_id]


# Export key classes
__all__ = [
    'SubagentStatus',
    'CoordinationStrategy',
    'SubagentSpec',
    'SubagentInstance',
    'CoordinationContext',
    'SubagentSpawner',
    'TemporalSubagentSpawner',
    'ResultConsolidator',
    'SubagentCoordinator'
]
