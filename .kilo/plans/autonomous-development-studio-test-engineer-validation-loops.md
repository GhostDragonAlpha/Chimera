# Autonomous Development Studio: TEST_ENGINEER Agent with Self-Correction Validation Loops

## Overview

This plan adds a `TEST_ENGINEER` agent role to the Chimera multi-agent coordination system, enabling self-correction validation loops where agents can iterate on failures rather than failing out permanently. The feature transforms the existing coordinator from a simple task executor into an autonomous development studio workflow with built-in quality gates and retry logic.

## Goals

1. **Add `TEST_ENGINEER` agent role** that validates results from other agents after task execution
2. **Implement explicit validation phase** via new `execute_with_validation()` method on `MultiAgentCoordinator`
3. **Enable self-correction loops** where failed validations trigger re-execution of specific failing subtasks with the original agent (up to 3 total attempts)
4. **Maintain backward compatibility** — no breaking changes to existing `execute_sync()`, `execute_async()`, `execute_parallel()` methods

## Affected Boundaries

| File | Change Type | Description |
|------|-------------|-------------|
| `Chimera/Python/agent_roles/test_engineer_agent.py` | **New** | Implement `TestEngineerAgent` class inheriting from `AgentSession` |
| `Chimera/Python/agent_roles/__init__.py` | **Modify** | Export `TestEngineerAgent` |
| `Chimera/Python/multi_agent_coordinator.py` | **Modify** | Add `execute_with_validation()` method; register `TestEngineerAgent` in `AgentFactory` |
| `Chimera/Python/run_multi_agent.py` | **Modify** | Add `--validate` CLI flag to enable validation mode |

## Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  MultiAgent      │     │  AgentFactory    │     │  AgentSession    │
│  Coordinator     │────▶│  (registry)      │────▶│  (base class)    │
└────────┬─────────┘     └──────────────────┘     └────────┬─────────┘
         │                                                 │
         ▼                                                ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  execute_sync()  │     │  LevelDesigner   │     │  VehicleTuner    │
│  / execute_      │     │  Agent           │     │  Agent           │
│  with_validation │────▶│                  │────▶│                  │
└────────┬─────────┘     └──────────────────┘     └──────────────────┘
         │                                                 │
         ▼                                                ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  execute_        │◀────│  TestEngineer    │     │  AssetManager    │
│  with_validation │     │  Agent (NEW)     │◀────│  Agent           │
└────────┬─────────┘     └──────────────────┘     └──────────────────┘
         │                                                 │
         ▼                                                ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Validation      │     │  MCP tools:      │     │  MCP tools:      │
│  phase           │────▶│  inspect,        │     │  manage_asset,   │
│                  │     │  control_actor   │     │  manage_material │
└────────┬─────────┘     └──────────────────┘     └──────────────────┘
         │
         ▼ (if validation fails)
┌─────────────────┐
│  Re-execute      │
│  original agent  │
│  with same task  │
│  spec            │
└─────────────────┘
```

## Implementation Details

### 1. New File: `Chimera/Python/agent_roles/test_engineer_agent.py`

```python
"""
Test Engineer Agent — Specialized for validating agent results and triggering
self-correction loops when validation fails.

Uses MCP tools: inspect, control_actor, system_control.
Integrates with LM Studio for AI-based result analysis.
Reports progress through message bus to coordinator.
"""

import asyncio
from typing import Any, Optional

from .base_agent import AgentRole, AgentSession, MessageEvent


class TestEngineerAgent(AgentSession):
    """AI agent specialized in validating task results and triggering re-execution."""

    def __init__(self, message_bus=None, lmstudio_base_url="http://localhost:1234",
                 mcp_url="http://localhost:3000/mcp"):
        super().__init__(
            role=AgentRole.TEST_ENGINEER,
            message_bus=message_bus,
            lmstudio_base_url=lmstudio_base_url,
            mcp_url=mcp_url,
        )

    async def _execute_task_impl(self, task_spec: dict) -> Any:
        """Execute validation tasks using MCP tools and LM Studio analysis.

        Supported task types:
          - validate_task_results: Review results from other agents, verify MCP tool outputs
          - verify_mcp_tool_output: Validate specific MCP tool responses for correctness
          - trigger_reexecution: Call back to the original agent with the same task spec
        """
        task_type = task_spec.get("task_type", "")
        parameters = task_spec.get("parameters", {})

        if task_type == "validate_task_results":
            return await self._validate_task_results(parameters)
        elif task_type == "verify_mcp_tool_output":
            return await self._verify_mcp_tool_output(parameters)
        elif task_type == "trigger_reexecution":
            return await self._trigger_reexecution(parameters)
        else:
            raise ValueError(f"Unknown test engineer task type: {task_type}")

    async def _validate_task_results(self, params: dict) -> Any:
        """Validate results from another agent's task execution.

        Args:
            params: Dict with keys: 'original_agent_id', 'original_task_spec', 'validation_criteria'

        Returns:
            Validation result dict with status and findings
        """
        original_agent_id = params.get("original_agent_id", "")
        original_task_spec = params.get("original_task_spec", {})
        validation_criteria = params.get("validation_criteria", {})

        self._emit_progress(f"Validating results from agent {original_agent_id}")

        # Inspect the world state to verify task completion
        response = await self.call_mcp_tool("inspect", {
            "action": "get_world_state",
            "parameters": {"agent_id": original_agent_id}
        })

        # Analyze results with LM Studio for AI-based validation
        lmstudio_prompt = (
            f"Validate the following task result from agent {original_agent_id}. "
            f"Original task: {original_task_spec.get('description', 'unknown')}. "
            f"Result: {response}. "
            f"Validation criteria: {validation_criteria}."
        )

        lmstudio_result = await self.query_lmstudio(lmstudio_prompt, temperature=0.1)

        is_valid = False
        if lmstudio_result and 'error' not in lmstudio_result:
            # Parse LM Studio response to determine validity
            content = lmstudio_result.get("content", "")
            is_valid = "valid" in content.lower() or "pass" in content.lower()

        return {
            "task_type": "validate_task_results",
            "is_valid": is_valid,
            "original_agent_id": original_agent_id,
            "lmstudio_analysis": lmstudio_result,
            "mcp_response": response,
        }

    async def _verify_mcp_tool_output(self, params: dict) -> Any:
        """Verify a specific MCP tool output for correctness."""
        tool_name = params.get("tool_name", "")
        expected_output = params.get("expected_output", {})

        self._emit_progress(f"Verifying MCP tool '{tool_name}' output")

        response = await self.call_mcp_tool(tool_name, {
            "action": "verify_output",
            "parameters": {"expected": expected_output}
        })

        return {
            "task_type": "verify_mcp_tool_output",
            "is_valid": response is not None and response.get("status") == "success",
            "response": response,
        }

    async def _trigger_reexecution(self, params: dict) -> Any:
        """Trigger re-execution of a failed task by the original agent."""
        original_agent_id = params.get("original_agent_id", "")
        retry_count = params.get("retry_count", 0)
        max_retries = params.get("max_retries", 3)

        self._emit_progress(
            f"Triggering re-execution for agent {original_agent_id} "
            f"(attempt {retry_count + 1}/{max_retries})"
        )

        return {
            "task_type": "trigger_reexecution",
            "original_agent_id": original_agent_id,
            "retry_count": retry_count + 1,
            "should_retry": retry_count < max_retries,
        }
```

### 2. Modify: `Chimera/Python/multi_agent_coordinator.py`

Add the following changes to `multi_agent_coordinator.py`:

#### a) Import `TestEngineerAgent` in imports section (lines ~17-36):

```python
try:
    from .base_agent import (
        AgentSession,
        AgentRole,
        AgentStatus,
        MessageEvent,
        AgentMessageBus,
    )
    from .level_designer_agent import LevelDesignerAgent
    from .vehicle_tuner_agent import VehicleTunerAgent
    from .asset_manager_agent import AssetManagerAgent
    from .test_engineer_agent import TestEngineerAgent  # NEW
except ImportError:
    AgentSession = object
    AgentRole = None
    AgentStatus = None
    MessageEvent = None
    AgentMessageBus = None
    LevelDesignerAgent = None
    VehicleTunerAgent = None
    AssetManagerAgent = None
    TestEngineerAgent = None  # NEW
```

#### b) Register `TestEngineerAgent` in `AgentFactory.create_agent`:

Change the agents dict from:
```python
        agents = {
            AgentRole.LEVEL_DESIGNER: LevelDesignerAgent,  # type: ignore
            AgentRole.VEHICLE_TUNER: VehicleTunerAgent,  # type: ignore
            AgentRole.ASSET_MANAGER: AssetManagerAgent,  # type: ignore
            AgentRole.TEST_ENGINEER: None,  # Generic base agent for test engineering
        }
```

To:
```python
        agents = {
            AgentRole.LEVEL_DESIGNER: LevelDesignerAgent,  # type: ignore
            AgentRole.VEHICLE_TUNER: VehicleTunerAgent,  # type: ignore
            AgentRole.ASSET_MANAGER: AssetManagerAgent,  # type: ignore
            AgentRole.TEST_ENGINEER: TestEngineerAgent,  # type: ignore — NEW
        }
```

#### c) Add `execute_with_validation()` method after existing execution methods (after line ~546):

```python
    async def execute_with_validation(
        self,
        tasks: Optional[list[str]] = None,
        max_retries: int = 3,
        validation_criteria: Optional[dict] = None,
    ) -> dict[str, TaskResult]:
        """Execute tasks synchronously with an explicit validation phase.

        After initial task execution, failed or pending tasks are routed to
        TEST_ENGINEER agents for validation. Failed validations trigger
        re-execution of the specific failing subtask with the original agent,
        up to max_retries total attempts per task.

        Args:
            tasks: List of task IDs to execute. If None, executes all assigned subtasks.
            max_retries: Maximum total attempts per task before marking as permanently failed (default 3).
            validation_criteria: Optional dict of criteria passed to TEST_ENGINEER for validation.

        Returns:
            Dict mapping task_id -> TaskResult with final status after validation loop.
        """
        self._running = True
        self._start_time = time.time()

        if not tasks:
            tasks = list(self.subtasks.keys())

        # Phase 1: Initial synchronous execution
        self._emit_coordinator_progress(
            f"Phase 1 — Initial sync execution of {len(tasks)} tasks",
            {"task_ids": tasks},
        )

        results = await self.execute_sync(tasks)

        # Phase 2: Validation loop
        failed_tasks = [tid for tid, r in results.items() if r.status != "success"]

        validation_round = 0
        while failed_tasks and validation_round < max_retries:
            validation_round += 1
            self._emit_coordinator_progress(
                f"Phase {validation_round + 1} — Validation round {validation_round} for {len(failed_tasks)} failed tasks",
                {"failed_task_ids": failed_tasks, "round": validation_round},
            )

            new_failed = []
            for task_id in failed_tasks:
                subtask = self.subtasks.get(task_id)
                if not subtask or subtask.role is None:  # type: ignore
                    continue

                # Spawn TEST_ENGINEER agent to validate this specific task
                validator_agent_id = await self.spawn_agent(AgentRole.TEST_ENGINEER)

                # Build validation task spec
                validation_task_spec = {
                    "task_type": "validate_task_results",
                    "description": f"Validate results for task {task_id}",
                    "parameters": {
                        "original_agent_id": None,  # Will be resolved below
                        "original_task_spec": {
                            "task_id": task_id,
                            "description": subtask.description,
                            "parameters": subtask.parameters,
                        },
                        "validation_criteria": validation_criteria or {},
                    },
                }

                # Find the original agent that failed this task
                for aid, agent in self.agents.items():
                    if agent.role == subtask.role and agent.status != AgentStatus.TERMINATED:  # type: ignore
                        validation_task_spec["parameters"]["original_agent_id"] = aid
                        break

                # Execute validation
                validator_result = await self.agents[validator_agent_id].execute_task(validation_task_spec)

                # Check if validation passed
                is_valid = False
                if validator_result and isinstance(validator_result, dict):
                    is_valid = validator_result.get("is_valid", False)

                if not is_valid:
                    # Validation failed — trigger re-execution of original agent
                    self._emit_coordinator_progress(
                        f"Validation FAILED for task {task_id} — triggering re-execution (attempt {validation_round + 1})",
                        {"task_id": task_id, "round": validation_round},
                    )

                    # Re-execute the original agent with the same task spec
                    if not validation_task_spec["parameters"].get("original_agent_id"):
                        continue  # Skip if we can't find the original agent

                    result = await self.agents[validation_task_spec["parameters"]["original_agent_id"]].execute_task(
                        {
                            "task_id": task_id,
                            "description": subtask.description,
                            "parameters": subtask.parameters,
                            "task_type": subtask.parameters.get("task_type", ""),
                        }
                    )

                    # Update the result in our tracking
                    task_result = TaskResult(
                        agent_id=result.get("agent_id"),
                        role=subtask.role.value if subtask.role else "",  # type: ignore
                        task_id=task_id,
                        status=result.get("status", "failed"),
                        result=result.get("result"),
                        error=result.get("error"),
                        attempts=validation_round + 1,
                    )
                    task_result.started_at = self._start_time
                    task_result.completed_at = time.time()

                    results[task_id] = task_result
                    self.results[task_id] = task_result

                    # If still failed after re-execution, add back to failed list
                    if result.get("status") != "success":
                        new_failed.append(task_id)
                else:
                    # Validation passed — mark as success
                    results[task_id].status = "success"
                    self.results[task_id] = results[task_id]

            failed_tasks = new_failed

        self._running = False

        success_count = sum(1 for r in results.values() if r.status == "success")
        failed_count = sum(1 for r in results.values() if r.status != "success")

        self._emit_coordinator_progress(
            f"Validation loop complete: {success_count} success, {failed_count} failed after {validation_round or 0} round(s)",
            {"total": len(results), "success": success_count, "failed": failed_count},
        )

        return results
```

### 3. Modify: `Chimera/Python/agent_roles/__init__.py`

Add `TestEngineerAgent` to the exports:

```python
from .base_agent import AgentSession, AgentRole, AgentStatus, MessageEvent, AgentMessageBus
from .level_designer_agent import LevelDesignerAgent
from .vehicle_tuner_agent import VehicleTunerAgent
from .asset_manager_agent import AssetManagerAgent
from .test_engineer_agent import TestEngineerAgent  # NEW

__all__ = [
    "AgentSession",
    "AgentRole",
    "AgentStatus",
    "MessageEvent",
    "AgentMessageBus",
    "LevelDesignerAgent",
    "VehicleTunerAgent",
    "AssetManagerAgent",
    "TestEngineerAgent",  # NEW
]
```

### 4. Modify: `Chimera/Python/run_multi_agent.py`

Add `--validate` CLI flag to enable validation mode in the demo:

In the `run_demo()` function signature, add `validate_mode: bool = False`:

```python
async def run_demo(task_description: str = None, agent_count: int = 0,
                   async_mode: bool = False, parallel: bool = True,
                   validate_mode: bool = False) -> dict:
```

In the execution section (around line ~214-230), add validation mode handling:

```python
    # Execute tasks
    start = time.time()

    if async_mode:
        print("\n[EXECUTE] Running in ASYNC mode (fire-and-forget)...")
        task_handles = await coordinator.execute_async()
        results_dict = {}
        for tid, task_h in task_handles.items():
            result = await task_h
            results_dict[tid] = result
    elif validate_mode:
        print("\n[EXECUTE] Running with VALIDATION mode (sync + self-correction loop)...")
        results_dict = await coordinator.execute_with_validation(max_retries=3)
    elif parallel:
        print("\n[EXECUTE] Running in PARALLEL mode (max concurrency=5)...")
        results_dict = await coordinator.execute_parallel(max_concurrent=5)
    else:
        print("\n[EXECUTE] Running in SYNC mode (sequential with dependency resolution)...")
        results_dict = await coordinator.execute_sync()
```

In the `main()` function, add CLI argument:

```python
    parser.add_argument(
        "--validate", dest="validate_mode", action="store_true", default=False,
        help="Enable validation mode with self-correction loops (sync + TEST_ENGINEER validation)",
    )
```

And pass it to `run_demo`:

```python
        result = asyncio.run(run_demo(
            task_description=args.task,
            agent_count=args.agents,
            async_mode=args.async_mode,
            parallel=not args.no_parallel,
            validate_mode=args.validate_mode,  # NEW
        ))
```

## Failure Modes & Retry Logic

| Scenario | Behavior |
|----------|----------|
| Task fails on first attempt | TEST_ENGINEER validates → if validation fails, re-execute original agent (attempt 2) |
| Re-execution also fails | TEST_ENGINEER validates again → if still failing, re-execute (attempt 3) |
| All 3 attempts exhausted | Mark task as permanently failed; report in results summary with `attempts=3` |
| Validation passes on retry | Mark task as success; continue to next failed task |

## Rollout Path

1. **Step 1**: Create new file `Chimera/Python/agent_roles/test_engineer_agent.py`
2. **Step 2**: Modify `Chimera/Python/multi_agent_coordinator.py`:
   - Add import for `TestEngineerAgent`
   - Register in `AgentFactory.create_agent` agents dict
   - Add `execute_with_validation()` method
3. **Step 3**: Modify `Chimera/Python/agent_roles/__init__.py` to export `TestEngineerAgent`
4. **Step 4** (optional): Modify `Chimera/Python/run_multi_agent.py` to add `--validate` CLI flag

No breaking changes to existing methods — all existing code paths remain functional.

## Validation Plan

1. **Unit test**: Verify `execute_with_validation()` correctly routes failed tasks to TEST_ENGINEER agents
2. **Integration test**: Run `run_multi_agent.py --task "build a race track" --validate` and verify validation loop triggers on failures
3. **Regression test**: Ensure existing `execute_sync()`, `execute_async()`, `execute_parallel()` methods continue to work unchanged

## Usage Example

```bash
# Default demo with validation enabled (self-correction loops)
python Chimera/Python/run_multi_agent.py --task "build a race track" --validate

# Custom task with validation and max retries
python Chimera/Python/run_multi_agent.py --task "build a city" --validate --agents 6
```

## Summary of Changes

| File | Lines Added/Modified | Change Type |
|------|---------------------|-------------|
| `agent_roles/test_engineer_agent.py` | ~157 lines (new) | New file |
| `multi_agent_coordinator.py` | ~80 lines added | Method + import + factory registration |
| `agent_roles/__init__.py` | 2 lines modified | Export addition |
| `run_multi_agent.py` | ~15 lines modified | CLI flag + execution mode |
