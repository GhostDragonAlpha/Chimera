"""
Multi-Agent Coordinator — Core orchestrator for managing multiple AI agent sessions.

Manages agent lifecycle (spawn, manage, terminate), task distribution based on roles,
inter-agent communication via shared message bus, and both synchronous and asynchronous
task execution modes. Resilient to individual agent failures with retry/skip logic.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


try:
    from agent_roles.base_agent import (
        AgentSession,
        AgentRole,
        AgentStatus,
        MessageEvent,
        AgentMessageBus,
    )
    from agent_roles.level_designer_agent import LevelDesignerAgent
    from agent_roles.vehicle_tuner_agent import VehicleTunerAgent
    from agent_roles.asset_manager_agent import AssetManagerAgent
    from agent_roles.test_engineer_agent import TestEngineerAgent
except ImportError:
    AgentSession = object
    AgentRole = None
    AgentStatus = None
    MessageEvent = None
    AgentMessageBus = None
    LevelDesignerAgent = None
    VehicleTunerAgent = None
    AssetManagerAgent = None
    TestEngineerAgent = None


# ---------------------------------------------------------------------------
# Task & Result Data Classes
# ---------------------------------------------------------------------------


@dataclass
class SubTask:
    """A subtask assigned to a specialized agent."""
    task_id: str = field(default_factory=lambda: f"subtask-{uuid.uuid4().hex[:8]}")
    role: AgentRole = None  # type: ignore[assignment]
    description: str = ""
    parameters: dict = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)  # task IDs this depends on


@dataclass
class TaskResult:
    """Result from a completed subtask."""
    agent_id: str = ""
    role: str = ""
    task_id: str = ""
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0

    @property
    def duration(self) -> float:
        if self.completed_at > 0:
            return self.completed_at - self.started_at
        return time.time() - self.started_at


# ---------------------------------------------------------------------------
# Agent Registry & Factory
# ---------------------------------------------------------------------------


class AgentFactory:
    """Factory for creating specialized agent instances."""

    @staticmethod
    def create_agent(role: AgentRole, message_bus=None, **kwargs) -> AgentSession:  # type: ignore
        """Create an agent instance for the given role.

        Args:
            role: The AgentRole to create
            message_bus: Shared message bus for inter-agent communication
            **kwargs: Additional arguments passed to the agent constructor

        Returns:
            An initialized AgentSession subclass
        """
        lmstudio_base_url = kwargs.pop("lmstudio_base_url", "http://localhost:1234")
        mcp_url = kwargs.pop("mcp_url", "http://localhost:3000/mcp")

        agents = {
            AgentRole.LEVEL_DESIGNER: LevelDesignerAgent,  # type: ignore
            AgentRole.VEHICLE_TUNER: VehicleTunerAgent,  # type: ignore
            AgentRole.ASSET_MANAGER: AssetManagerAgent,  # type: ignore
            AgentRole.TEST_ENGINEER: TestEngineerAgent,  # type: ignore
        }

        agent_class = agents.get(role)
        if agent_class is None:
            return AgentSession(role=role, message_bus=message_bus, **kwargs)  # type: ignore

        return agent_class(
            message_bus=message_bus,
            lmstudio_base_url=lmstudio_base_url,
            mcp_url=mcp_url,
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Multi-Agent Coordinator
# ---------------------------------------------------------------------------


class MultiAgentCoordinator:
    """Core coordinator that manages multiple AI agent sessions.

    Features:
      - Spawn, manage, and terminate agent sessions by role
      - Task distribution to specialized agents based on their roles
      - Inter-agent communication via shared AgentMessageBus
      - Synchronous (wait-for-all) and asynchronous (fire-and-forget) execution
      - Resilient to individual agent failures with retry/skip logic

    Example:
        coordinator = MultiAgentCoordinator()
        await coordinator.spawn_agents([
            SubTask(role=AgentRole.LEVEL_DESIGNER, description="Build terrain"),
            SubTask(role=AgentRole.VEHICLE_TUNER, description="Tune vehicle physics"),
        ])
        results = await coordinator.execute_sync()
    """

    def __init__(self, lmstudio_base_url: str = "http://localhost:1234",
                 mcp_url: str = "http://localhost:3000/mcp"):
        self.lmstudio_base_url = lmstudio_base_url
        self.mcp_url = mcp_url

        # Shared message bus for inter-agent communication
        self.message_bus = AgentMessageBus()

        # Agent registry: agent_id -> AgentSession
        self.agents: dict[str, AgentSession] = {}

        # Task tracking: task_id -> SubTask
        self.subtasks: dict[str, SubTask] = {}

        # Results: task_id -> TaskResult
        self.results: dict[str, TaskResult] = {}

        # Progress callbacks registered by the caller
        self._progress_callbacks: list[Callable] = []

        # Coordinator status
        self._running = False
        self._start_time: float = 0.0

    def register_progress_callback(self, callback: Callable) -> None:
        """Register a callback for progress reports from the coordinator."""
        self._progress_callbacks.append(callback)

    def _emit_coordinator_progress(self, message: str, metadata: Optional[dict] = None) -> None:
        """Emit a progress update to all registered callbacks."""
        event = MessageEvent(
            sender_id="coordinator",
            content=message,
            metadata=metadata or {},
        )

        for cb in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(event))
                else:
                    cb(event)
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Agent Lifecycle
    # -----------------------------------------------------------------------

    async def spawn_agent(self, role: AgentRole, task_spec: Optional[dict] = None,
                          **kwargs) -> str:
        """Spawn a new agent session for the given role.

        Args:
            role: The AgentRole to create
            task_spec: Optional initial task specification
            **kwargs: Additional constructor arguments

        Returns:
            The agent_id of the newly created agent
        """
        agent = AgentFactory.create_agent(
            role=role,
            message_bus=self.message_bus,
            lmstudio_base_url=self.lmstudio_base_url,
            mcp_url=self.mcp_url,
            **kwargs,
        )

        # Subscribe this agent's topic on the message bus for coordinator messages
        topic = f"agent:{agent.agent_id}"
        self.message_bus.subscribe(topic, lambda e: None)  # No-op subscriber for routing

        self.agents[agent.agent_id] = agent

        # Register progress callback from agent to coordinator
        async def on_progress(event: MessageEvent):
            self._emit_coordinator_progress(
                f"[{event.metadata.get('role', '?')}] {event.content}",
                event.metadata,
            )

        agent.register_progress_callback(on_progress)

        # Initialize MCP if task_spec provided
        if task_spec:
            await agent.initialize_mcp()

        self._emit_coordinator_progress(f"Spawned {role.value} agent ({agent.agent_id})")

        return agent.agent_id

    async def spawn_agents(self, tasks: list[SubTask], **kwargs) -> dict[str, str]:
        """Spawn agents for a list of subtasks.

        Args:
            tasks: List of SubTask definitions with roles
            **kwargs: Additional constructor arguments passed to each agent

        Returns:
            Dict mapping task_id -> agent_id
        """
        mapping = {}
        for task in tasks:
            agent_id = await self.spawn_agent(task.role, **kwargs)
            mapping[task.task_id] = agent_id
            self.subtasks[task.task_id] = task

        self._emit_coordinator_progress(
            f"Spawned {len(tasks)} agents",
            {"roles": [t.role.value for t in tasks]},
        )

        return mapping

    async def terminate_agent(self, agent_id: str) -> None:
        """Terminate a specific agent session."""
        agent = self.agents.get(agent_id)
        if agent and agent.status != AgentStatus.TERMINATED:  # type: ignore
            await agent.terminate()
            del self.agents[agent_id]
            self._emit_coordinator_progress(f"Terminated agent {agent_id}")

    async def terminate_all(self) -> None:
        """Terminate all managed agents."""
        for agent_id in list(self.agents.keys()):
            try:
                await self.terminate_agent(agent_id)
            except Exception:
                pass
        self.agents.clear()

    # -----------------------------------------------------------------------
    # Task Distribution & Execution
    # -----------------------------------------------------------------------

    async def assign_task(self, task_id: str, agent_id: str, description: str,
                          parameters: Optional[dict] = None) -> None:
        """Assign a task to a specific agent.

        Args:
            task_id: Unique identifier for this subtask
            agent_id: The agent that will execute the task
            description: Human-readable task description
            parameters: Task-specific parameters dict
        """
        self.subtasks[task_id] = SubTask(
            task_id=task_id,
            role=self.agents[agent_id].role if agent_id in self.agents else None,  # type: ignore
            description=description,
            parameters=parameters or {},
        )

    async def execute_sync(self, tasks: Optional[list[str]] = None) -> dict[str, TaskResult]:
        """Execute assigned tasks synchronously — waits for all to complete.

        If tasks is None, executes all assigned subtasks. Tasks with dependencies
        are resolved topologically before execution.

        Returns:
            Dict mapping task_id -> TaskResult
        """
        self._running = True
        self._start_time = time.time()

        if not tasks:
            tasks = list(self.subtasks.keys())

        # Resolve dependency order
        ordered_tasks = self._resolve_dependencies(tasks)

        self._emit_coordinator_progress(
            f"Starting synchronous execution of {len(ordered_tasks)} tasks",
            {"task_ids": ordered_tasks},
        )

        results = {}
        for task_id in ordered_tasks:
            subtask = self.subtasks.get(task_id)
            if not subtask or subtask.role is None:  # type: ignore
                continue

            agent_id = None
            for aid, agent in self.agents.items():
                if agent.role == subtask.role and agent.status != AgentStatus.TERMINATED:  # type: ignore
                    agent_id = aid
                    break

            if not agent_id:
                # Spawn a new agent if none available
                agent_id = await self.spawn_agent(subtask.role)

            task_spec = {
                "task_id": task_id,
                "description": subtask.description,
                "parameters": subtask.parameters,
                "task_type": subtask.parameters.get("task_type", ""),
            }

            result = await self.agents[agent_id].execute_task(task_spec)

            task_result = TaskResult(
                agent_id=result.get("agent_id", agent_id),
                role=result.get("role", subtask.role.value if subtask.role else ""),  # type: ignore
                task_id=task_id,
                status=result.get("status", "failed"),
                result=result.get("result"),
                error=result.get("error"),
                attempts=result.get("attempts", 0),
            )
            task_result.started_at = self._start_time
            task_result.completed_at = time.time()

            results[task_id] = task_result
            self.results[task_id] = task_result

        self._running = False

        success_count = sum(1 for r in results.values() if r.status == "success")
        failed_count = sum(1 for r in results.values() if r.status != "success")

        self._emit_coordinator_progress(
            f"Sync execution complete: {success_count} success, {failed_count} failed",
            {"total": len(results), "success": success_count, "failed": failed_count},
        )

        return results

    async def execute_async(self, tasks: Optional[list[str]] = None) -> dict[str, asyncio.Task]:
        """Execute assigned tasks asynchronously — fire and forget.

        Returns tasks immediately; callers should await them separately.
        Failed agents are retried or skipped automatically.

        Args:
            tasks: List of task IDs to execute. If None, executes all.

        Returns:
            Dict mapping task_id -> asyncio.Task (await these for results)
        """
        self._running = True
        self._start_time = time.time()

        if not tasks:
            tasks = list(self.subtasks.keys())

        self._emit_coordinator_progress(
            f"Starting async execution of {len(tasks)} tasks",
            {"task_ids": tasks},
        )

        async def run_task(task_id: str) -> TaskResult:
            subtask = self.subtasks.get(task_id)
            if not subtask or subtask.role is None:  # type: ignore
                return TaskResult(task_id=task_id, status="skipped", error="No role assigned")

            agent_id = None
            for aid, agent in self.agents.items():
                if agent.role == subtask.role and agent.status != AgentStatus.TERMINATED:  # type: ignore
                    agent_id = aid
                    break

            if not agent_id:
                agent_id = await self.spawn_agent(subtask.role)

            task_spec = {
                "task_id": task_id,
                "description": subtask.description,
                "parameters": subtask.parameters,
                "task_type": subtask.parameters.get("task_type", ""),
            }

            try:
                result = await self.agents[agent_id].execute_task(task_spec)
                return TaskResult(
                    agent_id=result.get("agent_id", agent_id),
                    role=result.get("role", subtask.role.value if subtask.role else ""),  # type: ignore
                    task_id=task_id,
                    status=result.get("status", "failed"),
                    result=result.get("result"),
                    error=result.get("error"),
                    attempts=result.get("attempts", 0),
                )
            except Exception as e:
                return TaskResult(task_id=task_id, status="error", error=str(e))

        task_map = {}
        for task_id in tasks:
            t = asyncio.create_task(run_task(task_id))
            task_map[task_id] = t

        self._running = False
        return task_map

    async def execute_parallel(self, max_concurrent: int = 5) -> dict[str, TaskResult]:
        """Execute all tasks in parallel with concurrency limiting.

        Args:
            max_concurrent: Maximum number of concurrent agent executions

        Returns:
            Dict mapping task_id -> TaskResult
        """
        self._running = True
        self._start_time = time.time()

        semaphore = asyncio.Semaphore(max_concurrent)
        all_tasks = list(self.subtasks.keys())

        async def run_with_semaphore(task_id: str) -> TaskResult:
            subtask = self.subtasks.get(task_id)
            if not subtask or subtask.role is None:  # type: ignore
                return TaskResult(task_id=task_id, status="skipped")

            agent_id = None
            for aid, agent in self.agents.items():
                if agent.role == subtask.role and agent.status != AgentStatus.TERMINATED:  # type: ignore
                    agent_id = aid
                    break

            if not agent_id:
                agent_id = await self.spawn_agent(subtask.role)

            async with semaphore:
                task_spec = {
                    "task_id": task_id,
                    "description": subtask.description,
                    "parameters": subtask.parameters,
                    "task_type": subtask.parameters.get("task_type", ""),
                }
                try:
                    result = await self.agents[agent_id].execute_task(task_spec)
                    return TaskResult(
                        agent_id=result.get("agent_id", agent_id),
                        role=result.get("role", subtask.role.value if subtask.role else ""),  # type: ignore
                        task_id=task_id,
                        status=result.get("status", "failed"),
                        result=result.get("result"),
                        error=result.get("error"),
                        attempts=result.get("attempts", 0),
                    )
                except Exception as e:
                    return TaskResult(task_id=task_id, status="error", error=str(e))

        tasks = [run_with_semaphore(tid) for tid in all_tasks]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for i, task_result in enumerate(raw_results):
            task_id = all_tasks[i]
            if isinstance(task_result, Exception):
                results[task_id] = TaskResult(task_id=task_id, status="error", error=str(task_result))
            else:
                results[task_id] = task_result

        self._running = False
        return results

    # -----------------------------------------------------------------------
    # Dependency Resolution
    # -----------------------------------------------------------------------

    def _resolve_dependencies(self, tasks: list[str]) -> list[str]:
        """Resolve topological order for tasks with dependencies.

        Returns a list of task IDs in execution order (dependencies first).
        Cycles are broken by removing the earliest dependency.
        """
        graph: dict[str, list[str]] = {}
        for tid in tasks:
            subtask = self.subtasks.get(tid)
            if subtask:
                deps = [d for d in subtask.depends_on if d in tasks]
                graph[tid] = deps

        # Kahn's algorithm for topological sort
        in_degree: dict[str, int] = {tid: 0 for tid in graph}
        for tid, deps in graph.items():
            for dep in deps:
                in_degree[tid] += 1  # This is wrong direction; fix below

        # Correct: reverse the edges — if A depends on B, then B -> A
        adj: dict[str, list[str]] = {tid: [] for tid in graph}
        for tid, deps in graph.items():
            for dep in deps:
                adj[dep].append(tid)

        in_degree = {tid: 0 for tid in graph}
        for tid, deps in graph.items():
            in_degree[tid] = len(deps)

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        ordered = []

        while queue:
            node = queue.pop(0)
            ordered.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Handle any remaining tasks (cycles)
        remaining = [tid for tid in graph if tid not in ordered]
        ordered.extend(remaining)

        return ordered

    async def execute_with_validation(self, tasks: Optional[list[str]] = None, validation_tasks: Optional[list[SubTask]] = None, max_retries: Optional[int] = 3) -> dict[str, TaskResult]:
        """Execute assigned tasks synchronously and run validation tests with retry loop.

        Args:
            tasks: List of task IDs to execute. If None, executes all subtasks.
            validation_tasks: Optional list of SubTask definitions for validation.
            max_retries: Maximum number of validation rounds. None for infinite loop.

        Returns:
            Dict mapping task_id -> TaskResult including validation results
        """
        execution_results = {}
        failed_tasks: dict[str, TaskResult] = {}
        validation_round = 0

        while True:
            # Execute primary tasks or re-execute failed ones
            if not failed_tasks:
                execution_results = await self.execute_sync(tasks)
            else:
                # Re-execute failed tasks with TEST_ENGINEER validation loop
                reexecute_task_ids = list(failed_tasks.keys())
                
                # Filter out tasks where original agent is TERMINATED
                valid_reexecute_tasks = []
                for task_id in reexecute_task_ids:
                    subtask = self.subtasks.get(task_id)
                    if not subtask or subtask.role is None:
                        continue
                    
                    # Find the original agent for this task
                    original_agent_id = None
                    for aid, agent in self.agents.items():
                        if agent.role == subtask.role and agent.status != AgentStatus.TERMINATED:
                            original_agent_id = aid
                            break
                    
                    # Skip re-execution if no valid agent available (all TERMINATED)
                    if not original_agent_id:
                        continue
                        
                    valid_reexecute_tasks.append(task_id)

                if valid_reexecute_tasks:
                    self._emit_coordinator_progress(
                        f"Re-executing {len(valid_reexecute_tasks)} failed tasks (round {validation_round + 1})",
                        {"task_ids": valid_reexecute_tasks, "round": validation_round + 1},
                    )
                    
                    reexecute_results = await self.execute_sync(valid_reexecute_tasks)
                    execution_results.update(reexecute_results)

            # Collect failed tasks after this round
            current_failed: dict[str, TaskResult] = {}
            for task_id, result in execution_results.items():
                subtask = self.subtasks.get(task_id)
                if subtask and subtask.role != AgentRole.TEST_ENGINEER:
                    if result.status != "success":
                        current_failed[task_id] = result

            failed_tasks = current_failed

            # Check validation loop termination condition
            if not failed_tasks:
                self._emit_coordinator_progress("All tasks completed successfully")
                break
                
            validation_round += 1
            
            if max_retries is not None and validation_round >= max_retries:
                self._emit_coordinator_progress(
                    f"Validation loop terminated after {max_retries} rounds with {len(failed_tasks)} failed tasks",
                    {"failed_count": len(failed_tasks)},
                )
                break

            # Run TEST_ENGINEER validation for failed tasks
            if validation_tasks and AgentRole.TEST_ENGINEER in [t.role for t in validation_tasks]:
                self._emit_coordinator_progress(
                    f"Running TEST_ENGINEER validation round {validation_round} on {len(failed_tasks)} failed tasks",
                    {"failed_count": len(failed_tasks), "round": validation_round},
                )
                
                # Spawn test engineer agents for validation
                await self.spawn_agents(validation_tasks)

                # Execute validation tasks
                validation_task_ids = [t.task_id for t in validation_tasks]
                validation_execution_results = await self.execute_sync(validation_task_ids)

                # Merge results
                execution_results.update(validation_execution_results)
                self.results.update(validation_execution_results)
            else:
                # If no validation_tasks provided, skip re-execution and just report failures
                self._emit_coordinator_progress(
                    f"Validation round {validation_round} complete with {len(failed_tasks)} failures. No validation tasks provided.",
                    {"failed_count": len(failed_tasks), "round": validation_round},
                )

        # Final results merge
        for task_id, result in execution_results.items():
            self.results[task_id] = result

        return execution_results

    # -----------------------------------------------------------------------
    # Status & Reporting
    # -----------------------------------------------------------------------

    def get_status(self) -> dict:
        """Return the coordinator's current status and agent states."""
        agent_statuses = {}
        for aid, agent in self.agents.items():
            agent_statuses[aid] = agent.get_status()

        return {
            "running": self._running,
            "agents": len(self.agents),
            "subtasks": len(self.subtasks),
            "results": len(self.results),
            "agent_details": agent_statuses,
        }

    def get_results_summary(self) -> dict:
        """Return a summary of all task results."""
        if not self.results:
            return {"total": 0}

        total = len(self.results)
        success = sum(1 for r in self.results.values() if r.status == "success")
        failed = sum(1 for r in self.results.values() if r.status != "success")

        by_role: dict[str, int] = {}
        for r in self.results.values():
            role_key = r.role or "unknown"
            by_role[role_key] = by_role.get(role_key, 0) + 1

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "by_role": by_role,
            "duration": time.time() - self._start_time if self._start_time > 0 else 0,
        }
