# Comprehensive Autonomous Development Studio: MCP Testing, Continuous Validation Loops, and Git-Based File Restoration

## Overview

This plan implements a comprehensive autonomous development studio workflow that combines:
1. **MCP-Based Automated Testing Workflow** - Native automated testing using McpAutomationBridge plugin on port 3000 with LM Studio AI analysis
2. **TEST_ENGINEER Agent with Self-Correction Validation Loops** - Explicit validation phase where failed validations trigger re-execution of failing subtasks
3. **Continuous Subagent Deployment Indefinitely** - Infinite validation loop supporting `max_retries=None` for continuous deployment until manually interrupted
4. **Git-Based Deleted Files Restoration** - Mechanism to restore deleted files using git history

## Goals

1. **Implement MCP-native automated testing workflow** that runs after PIE starts, capturing screenshots and sending them to LM Studio for AI analysis
2. **Add TEST_ENGINEER agent role** that validates results from other agents after task execution with self-correction loops
3. **Implement infinite validation loop** via `execute_with_validation()` supporting `max_retries=None` for continuous deployment indefinitely
4. **Enable git-based deleted files restoration** to recover accidentally deleted or modified files using git history

## Design Decisions (Resolved)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP workflow trigger | Automatic on editor startup with retry/backoff + standalone runner | Current approach runs before PIE exists; need post-PIE hook that retries until ready |
| Init mode priority | MCP first, legacy fallback | New workflow is preferred; old scripts preserved as fallback |
| Flight vehicle MCP tools | Use existing control_editor + system_control via console commands | Custom C++ tool definitions require plugin recompilation; console commands sufficient for now |
| Authentication | No auth initially (loopback-only binding) | Local dev security adequate; enable capability token later if LAN access needed |
| Screenshot capture | full_editor_window mode with polling fallback | game_viewport is async and unreliable; full_editor_window returns base64 synchronously |
| LM Studio health check | Check /v1/models before sending screenshots, retry once | Prevents wasted requests when LM Studio restarts or model fails to load |
| Validation loop retries | Support max_retries=None for infinite loops | Enables continuous deployment until manually interrupted (KeyboardInterrupt/SIGTERM) |
| Default validation retries | max_retries=3 for finite loops | Maintains backward compatibility with existing execute_sync(), execute_async(), execute_parallel() |
| Git restoration method | git checkout / git restore | Standard git commands to recover deleted or modified files from history |

## Completed Implementation - MCP Automated Testing Workflow

### Phase 1: MCP Automation Workflow

**Task 1: Create mcp_automation_client.py** — Chimera/Python/mcp_automation_client.py (new, ~350 lines)
- MCPTestClient class manages MCP session lifecycle with initialize_session(), call_tool(), _request() methods
- Exponential backoff retry logic (max 10 retries, starting at 100ms, doubling each attempt)
- run_automated_test() orchestrates full workflow: PIE start -> ground screenshots (x2) -> flight mode toggle -> thrust -> flight screenshots (x3) -> AI analysis -> PIE stop
- _analyze_screenshots() and _analyze_single_screenshot() handle LM Studio integration with health checks

**Task 2: Modify init_unreal.py** — Chimera/Python/init_unreal.py (modified, 65 lines)
- Dual-mode startup: tries MCP workflow first, falls back to legacy scripts on failure
- Mode 1: MCP-native automated testing via mcp_automation_client.run_mcp_automated_test()
- Mode 2: Legacy synchronous startup with procedural_game_generator, play_test, runtime_screenshot_playtest

**Task 3: Create run_mcp_test.py** — Chimera/Python/run_mcp_test.py (new, ~60 lines)
- Standalone test runner for manual triggering from UE Python Console or terminal
- Provides run_standalone_test() function that calls mcp_automation_client.run_mcp_automated_test()

**Task 4: Update .mcp.json** — Chimera/.mcp.json (modified, 9 lines)
- Added instructions field describing MCP tools for automated testing (control_editor, system_control, manage_level, inspect)

### Phase 2: Dual-Mode Init and Validation Testing

**Task 1: Update init_unreal.py — Dual-Mode Startup** — COMPLETED
- Replaced MCP-only approach with dual-mode initialization that tries MCP first, falls back to legacy scripts on failure

**Task 2: Create Validation Test Suite** — Chimera/Python/validation_test_suite.py (new, 130 lines)
- Comprehensive validation script that imports and tests all 6 modules independently
- Tests mcp_automation_client, procedural_game_generator, play_test, runtime_screenshot_playtest, screenshot_lmstudio_workflow, unreal_api_operations
- Each test attempts import, verifies expected classes/functions exist, reports PASS/FAIL with error message

## Implementation Details - TEST_ENGINEER Agent and Validation Loops

### 1. New File: `Chimera/Python/agent_roles/test_engineer_agent.py`

```python
"""
Test Engineer Agent — Specialized for validating agent results and triggering
self-correction loops when validation fails. Supports infinite retry loops
when max_retries=None is specified.

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

        # Support infinite loop when max_retries is None
        is_infinite_loop = max_retries is None
        
        if not is_infinite_loop and retry_count >= max_retries:
            self._emit_progress(
                f"Max retries ({max_retries}) reached for agent {original_agent_id} - stopping re-execution"
            )
            return {
                "task_type": "trigger_reexecution",
                "original_agent_id": original_agent_id,
                "retry_count": retry_count,
                "should_retry": False,
                "max_retries_exhausted": True,
            }

        self._emit_progress(
            f"Triggering re-execution for agent {original_agent_id} "
            f"(attempt {retry_count + 1}{' (infinite loop)' if is_infinite_loop else '/' + str(max_retries)})"
        )

        return {
            "task_type": "trigger_reexecution",
            "original_agent_id": original_agent_id,
            "retry_count": retry_count + 1,
            "should_retry": True if is_infinite_loop or retry_count < max_retries else False,
            "is_infinite_loop": is_infinite_loop,
        }
```

### 2. Modify: `Chimera/Python/multi_agent_coordinator.py`

#### a) Import `TestEngineerAgent` in imports section:

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

```python
        agents = {
            AgentRole.LEVEL_DESIGNER: LevelDesignerAgent,  # type: ignore
            AgentRole.VEHICLE_TUNER: VehicleTunerAgent,  # type: ignore
            AgentRole.ASSET_MANAGER: AssetManagerAgent,  # type: ignore
            AgentRole.TEST_ENGINEER: TestEngineerAgent,  # type: ignore — NEW
        }
```

#### c) Add `execute_with_validation()` method with infinite loop support:

```python
    async def execute_with_validation(
        self,
        tasks: Optional[list[str]] = None,
        max_retries: int | None = 3,
        validation_criteria: Optional[dict] = None,
    ) -> dict[str, TaskResult]:
        """Execute tasks synchronously with an explicit validation phase.

        After initial task execution, failed or pending tasks are routed to
        TEST_ENGINEER agents for validation. Failed validations trigger
        re-execution of the specific failing subtask with the original agent,
        up to max_retries total attempts per task. If max_retries is None,
        the loop runs indefinitely until manually interrupted (KeyboardInterrupt/SIGTERM).

        Args:
            tasks: List of task IDs to execute. If None, executes all assigned subtasks.
            max_retries: Maximum total attempts per task before marking as permanently failed 
                         (default 3). Set to None for infinite validation loop.
            validation_criteria: Optional dict of criteria passed to TEST_ENGINEER for validation.

        Returns:
            Dict mapping task_id -> TaskResult with final status after validation loop.
        """
        self._running = True
        self._start_time = time.time()

        if not tasks:
            tasks = list(self.subtasks.keys())

        # Phase 1: Initial synchronous execution
        infinite_loop = max_retries is None
        retry_label = "indefinite" if infinite_loop else str(max_retries)
        self._emit_coordinator_progress(
            f"Phase 1 — Initial sync execution of {len(tasks)} tasks",
            {"task_ids": tasks},
        )

        results = await self.execute_sync(tasks)

        # Phase 2: Validation loop
        failed_tasks = [tid for tid, r in results.items() if r.status != "success"]

        validation_round = 0
        while failed_tasks:
            validation_round += 1
            
            if not infinite_loop and validation_round > max_retries:
                self._emit_coordinator_progress(
                    f"Max retries ({max_retries}) exhausted for {len(failed_tasks)} tasks — stopping validation loop",
                    {"failed_task_ids": failed_tasks, "round": validation_round},
                )
                break

            retry_label = "indefinite" if infinite_loop else str(max_retries)
            self._emit_coordinator_progress(
                f"Phase {validation_round + 1} — Validation round {validation_round} for {len(failed_tasks)} failed tasks (max_retries={retry_label})",
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
                should_retry = True
                max_retries_exhausted = False
                
                if validator_result and isinstance(validator_result, dict):
                    is_valid = validator_result.get("is_valid", False)
                    should_retry = validator_result.get("should_retry", True)
                    max_retries_exhausted = validator_result.get("max_retries_exhausted", False)

                if not is_valid:
                    if not should_retry and not infinite_loop:
                        self._emit_coordinator_progress(
                            f"Validation FAILED for task {task_id} — re-execution stopped after max retries exhausted",
                            {"task_id": task_id, "round": validation_round},
                        )
                        continue

                    # Validation failed or infinite loop — trigger re-execution of original agent
                    self._emit_coordinator_progress(
                        f"Validation FAILED for task {task_id} — triggering re-execution (attempt {validation_round + 1}{' (infinite loop)' if infinite_loop else ''})",
                        {"task_id": task_id, "round": validation_round},
                    )

                    # Re-execute the original agent with the same task spec
                    if not validation_task_spec["parameters"].get("original_agent_id"):
                        new_failed.append(task_id)
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
            
            # If no new failures, exit the loop
            if not failed_tasks and validation_round > 0:
                break

        self._running = False

        success_count = sum(1 for r in results.values() if r.status == "success")
        failed_count = sum(1 for r in results.values() if r.status != "success")

        retry_label = "indefinite" if infinite_loop else str(max_retries or 0)
        self._emit_coordinator_progress(
            f"Validation loop complete: {success_count} success, {failed_count} failed after {validation_round or 0} round(s) (max_retries={retry_label})",
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

Add `--validate` and `--infinite-validate` CLI flags:

In the `run_demo()` function signature, add `validate_mode: bool = False, infinite_validate: bool = False`:

```python
async def run_demo(task_description: str = None, agent_count: int = 0,
                   async_mode: bool = False, parallel: bool = True,
                   validate_mode: bool = False, infinite_validate: bool = False) -> dict:
```

In the execution section:

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
    elif infinite_validate:
        print("\n[EXECUTE] Running with INFINITE VALIDATION mode (sync + continuous validation loop)...")
        results_dict = await coordinator.execute_with_validation(max_retries=None)
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

In the `main()` function, add CLI arguments:

```python
    parser.add_argument(
        "--validate", dest="validate_mode", action="store_true", default=False,
        help="Enable validation mode with self-correction loops (sync + TEST_ENGINEER validation, max_retries=3)",
    )
    parser.add_argument(
        "--infinite-validate", dest="infinite_validate", action="store_true", default=False,
        help="Enable infinite validation loop (sync + continuous validation until KeyboardInterrupt/SIGTERM)",
    )
```

And pass them to `run_demo`:

```python
        result = asyncio.run(run_demo(
            task_description=args.task,
            agent_count=args.agents,
            async_mode=args.async_mode,
            parallel=not args.no_parallel,
            validate_mode=args.validate_mode,
            infinite_validate=args.infinite_validate,
        ))
```

## Implementation Details - Git-Based Deleted Files Restoration

### Git Restoration Utility: `Chimera/Python/git_restoration.py`

```python
"""
Git-Based Deleted Files Restoration Utility

Provides functionality to restore deleted or modified files using git history.
Supports both file restoration and directory restoration from previous commits.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional


def get_git_root() -> Optional[Path]:
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def restore_deleted_file(file_path: str, commit_ref: str = "HEAD") -> bool:
    """Restore a deleted or modified file from git history.
    
    Args:
        file_path: Relative path to the file from the git root
        commit_ref: Git reference (commit hash, branch name, or 'HEAD')
        
    Returns:
        True if restoration was successful, False otherwise
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    full_path = git_root / file_path
    
    # Check if file exists in the specified commit
    try:
        subprocess.run(
            ["git", "show", f"{commit_ref}:{file_path}"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        raise ValueError(f"File {file_path} not found in git history at {commit_ref}")

    # Restore the file from git history
    try:
        subprocess.run(
            ["git", "checkout", commit_ref, "--", file_path],
            capture_output=True,
            check=True
        )
        print(f"Successfully restored {file_path} from {commit_ref}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to restore {file_path}: {e}")
        return False


def restore_files_by_pattern(pattern: str, commit_ref: str = "HEAD") -> list[str]:
    """Restore all files matching a pattern from git history.
    
    Args:
        pattern: File pattern (e.g., '*.py', 'Chimera/Python/*.py')
        commit_ref: Git reference
        
    Returns:
        List of successfully restored file paths
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    # Find files matching the pattern in git history
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit_ref, "--", pattern],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        raise ValueError(f"No files found matching pattern {pattern} at {commit_ref}")

    restored_files = []
    for file_path in files:
        if restore_deleted_file(file_path, commit_ref):
            restored_files.append(file_path)

    return restored_files


def get_deleted_files_since_commit(commit_ref: str = "HEAD") -> list[str]:
    """Get a list of files that have been deleted since the specified commit.
    
    Args:
        commit_ref: Git reference
        
    Returns:
        List of deleted file paths
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    try:
        # Get list of deleted files between previous commit and HEAD
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{commit_ref}^", commit_ref, "--diff-filter=D"],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        return []


def unstage_and_restore_all() -> bool:
    """Unstage all changes and restore all files to the state of HEAD.
    
    Returns:
        True if successful, False otherwise
    """
    git_root = get_git_root()
    if not git_root:
        raise RuntimeError("Not a git repository or unable to determine git root")

    try:
        # Unstage all changes
        subprocess.run(
            ["git", "reset"],
            capture_output=True,
            check=True
        )
        # Restore all files
        subprocess.run(
            ["git", "restore", "."],
            capture_output=True,
            check=True
        )
        print("Successfully unstaged and restored all files")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to unstage and restore files: {e}")
        return False
```

### Git Restoration Usage Examples

```bash
# Restore a specific deleted file from HEAD
python Chimera/Python/git_restoration.py --restore-file Chimera/Python/mcp_automation_client.py

# Restore all Python files matching a pattern from a specific commit
python Chimera/Python/git_restoration.py --restore-pattern "Chimera/Python/*.py" --commit-ref v1.2.0

# Get list of deleted files since a specific commit
python Chimera/Python/git_restoration.py --list-deleted-since HEAD~5

# Unstage and restore all changes to HEAD state
python Chimera/Python/git_restoration.py --restore-all
```

## Data Flow

### MCP Automated Testing Workflow

UE Editor Startup (PythonScriptPlugin)
    -> init_unreal.py loads
        -> Tries MCP workflow: mcp_automation_client.run_mcp_automated_test()
            -> MCPTestClient.initialize_session() -> HTTP POST /mcp (JSON-RPC)
                -> control_editor action=play -> PIE starts
                    -> Wait 5s for world load
                        -> control_editor action=screenshot (full_editor_window, returnBase64=True) x2
                            -> system_control console_command=bFlightModeEnabled=True
                                -> system_control console_command=thrust input
                                    -> Wait 3s for physics simulation
                                        -> control_editor action=screenshot x3
                                            -> HTTP POST to LM Studio /v1/chat/completions (base64 images)
                                                -> control_editor action=stop -> PIE stops

### Continuous Validation Loop Flow

Coordinator.execute_with_validation()
    -> Phase 1: Initial execute_sync() of all tasks
        -> Failed tasks identified
    -> Phase 2: Validation loop
        -> For each failed task:
            -> Spawn TEST_ENGINEER agent
            -> Validate results using MCP inspect tool + LM Studio analysis
            -> If validation passes: mark as success
            -> If validation fails: trigger re-execution of original agent
                -> If max_retries=None (infinite loop): continue until manual interrupt
                -> If max_retries exhausted: mark task as permanently failed

### Git Restoration Flow

User requests file restoration
    -> git_restoration.py invoked with file pattern or specific file
        -> get_git_root() determines repository root
            -> Verify file exists in git history using `git show <commit>:<file>`
                -> Restore file using `git checkout <commit> -- <file>` or `git restore .`

## Validation Steps

### Step 1 - Module Import Suite (UE Editor)

Open UE Python Console and run:
from validation_test_suite import run_validation; run_validation()

Expected output: All 6 modules report PASS, summary shows Total: 6/6 modules validated successfully

### Step 2 - Dual-Mode Startup (Open Chimera.uproject)

Check Output Log for startup message:

If MCP server is running on port 3000:
[INIT] Attempting MCP-based automated test...
[MCP] Workflow completed successfully.

If MCP server is NOT running (fallback):
[WARN] MCP workflow unavailable (...)
[INFO] Falling back to legacy startup scripts...
[LEGACY] Running complete startup workflow...
CHIMERA INITIALIZATION COMPLETE - Legacy workflow finished

### Step 3 - Validation Mode Execution (Terminal)

```bash
# Standard validation mode (max_retries=3)
python Chimera/Python/run_multi_agent.py --task "build a race track" --validate

# Infinite validation mode (max_retries=None)
python Chimera/Python/run_multi_agent.py --task "build a race track" --infinite-validate
```

### Step 4 - Git Restoration Verification (Terminal)

```bash
# List deleted files since last commit
git diff --name-only HEAD~1 HEAD --diff-filter=D

# Restore specific file
git checkout HEAD~1 -- Chimera/Python/example.py

# Or use git restoration utility
python Chimera/Python/git_restoration.py --restore-file Chimera/Python/example.py
```

## Failure Modes & Retry Logic

| Scenario | Behavior | Recovery |
|----------|----------|----------|
| MCP server not ready on startup | Retry 10 times with exponential backoff (30s max) | Log error, exit gracefully; user can run standalone runner manually |
| LM Studio not available | Skip AI analysis, still capture screenshots to disk | Screenshots saved locally for later analysis |
| PIE fails to start | control_editor returns error, workflow stops | Log error, no crash; existing scripts unaffected |
| Task fails on first attempt | TEST_ENGINEER validates → if validation fails, re-execute original agent (attempt 2) | Self-correction loop continues |
| Re-execution also fails | TEST_ENGINEER validates again → if still failing, re-execute (attempt 3) | Continues up to max_retries |
| All 3 attempts exhausted (finite loop) | Mark task as permanently failed; report in results summary with attempts=3 | Task marked as failed |
| Infinite validation loop active | Loop continues indefinitely until KeyboardInterrupt/SIGTERM | User must manually interrupt |
| Git restoration file not found | ValueError raised indicating file not in git history | Verify commit reference and file path |

## Rollout / Migration Path

1. **Current state** - MCP workflow replaces old synchronous startup; legacy scripts preserved as fallback via dual-mode init_unreal.py
2. **TEST_ENGINEER integration** - Add test_engineer_agent.py, modify multi_agent_coordinator.py with execute_with_validation() method
3. **Infinite validation support** - Add max_retries=None support to execute_with_validation() and CLI flags (--validate, --infinite-validate)
4. **Git restoration utility** - Add git_restoration.py for recovering deleted or modified files using git history
5. **Production use** - All features handle both scenarios automatically; graceful degradation ensures no crashes

## Open Questions (Out of Scope)

- Custom MCP tool definitions for flight vehicle actions - can be added later if console commands prove insufficient
- Capability token authentication - enable when LAN access is needed beyond loopback
- SSE progress notifications for long-running tools - implement when workflow timing becomes critical
- Automated git commit after restoration - future enhancement to auto-commit restored files
