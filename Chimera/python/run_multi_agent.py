"""
Run Multi-Agent — Entry point for the multi-agent coordination system.

Demonstrates coordinating agents for a complex task (e.g., building a race track
with vehicles). Parses command-line args for task description and agent count.
Outputs progress and final results.

Usage:
    python run_multi_agent.py                        # Default demo scenario
    python run_multi_agent.py --task "build a city"  # Custom task
    python run_multi_agent.py --agents 6             # More agents
    python run_multi_agent.py --async                # Async execution mode
"""

import argparse
import asyncio
import json
import sys
import time


try:
    from multi_agent_coordinator import (
        MultiAgentCoordinator,
        SubTask,
        AgentRole,
    )
    from agent_roles import LevelDesignerAgent, VehicleTunerAgent, AssetManagerAgent
except ImportError as e:
    print(f"[ERROR] Failed to import multi-agent modules: {e}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Task Templates
# ---------------------------------------------------------------------------


def build_race_track_tasks() -> list[SubTask]:
    """Create a coordinated task set for building a race track with vehicles.

    Tasks are structured so the LevelDesignerAgent builds terrain and structures,
    the AssetManagerAgent creates materials and textures, and the VehicleTunerAgent
    configures test vehicles.
    """
    return [
        SubTask(
            role=AgentRole.LEVEL_DESIGNER,
            description="Generate race track terrain with elevation changes",
            parameters={
                "task_type": "generate_terrain",
                "chunk_size": 2048,
                "resolution": 512,
                "seed": 42,
            },
        ),
        SubTask(
            role=AgentRole.LEVEL_DESIGNER,
            description="Place track barriers and grandstands",
            parameters={
                "task_type": "place_structures",
                "structure_type": "barrier",
                "count": 50,
                "placement": "track_outline",
            },
        ),
        SubTask(
            role=AgentRole.ASSET_MANAGER,
            description="Generate asphalt and grass materials for track",
            parameters={
                "task_type": "generate_material",
                "material_name": "TrackAsphaltMat",
                "material_type": "Standard",
                "properties": {"base_color": [0.15, 0.15, 0.15], "roughness": 0.8},
            },
        ),
        SubTask(
            role=AgentRole.ASSET_MANAGER,
            description="Create track boundary textures",
            parameters={
                "task_type": "generate_texture",
                "texture_name": "TrackBoundaryTex",
                "width": 2048,
                "height": 512,
                "format": "RGBA8",
            },
        ),
        SubTask(
            role=AgentRole.VEHICLE_TUNER,
            description="Tune vehicle for track racing (high thrust, low damping)",
            parameters={
                "task_type": "tune_vehicle",
                "actor_name": "RaceVehicleBP",
                "thrust_power": 2500.0,
                "damping": 0.95,
                "gravity_scale": 1.0,
            },
        ),
        SubTask(
            role=AgentRole.VEHICLE_TUNER,
            description="Spawn test vehicle on the track",
            parameters={
                "task_type": "spawn_test_vehicle",
                "blueprint_path": "/Game/Blueprints/RaceVehicleBP",
                "spawn_location": [0.0, 0.0, 150.0],
            },
        ),
    ]


def build_city_tasks() -> list[SubTask]:
    """Create tasks for building a city environment."""
    return [
        SubTask(
            role=AgentRole.LEVEL_DESIGNER,
            description="Generate city terrain with roads and blocks",
            parameters={"task_type": "generate_terrain", "chunk_size": 4096, "resolution": 1024},
        ),
        SubTask(
            role=AgentRole.LEVEL_DESIGNER,
            description="Place buildings and infrastructure",
            parameters={"task_type": "place_structures", "structure_type": "building", "count": 100, "placement": "grid"},
        ),
        SubTask(
            role=AgentRole.ASSET_MANAGER,
            description="Generate building facade materials",
            parameters={"task_type": "generate_material", "material_name": "BuildingFacadeMat", "material_type": "Standard"},
        ),
        SubTask(
            role=AgentRole.VEHICLE_TUNER,
            description="Spawn city traffic vehicles",
            parameters={"task_type": "spawn_test_vehicle", "blueprint_path": "/Game/Blueprints/CityVehicleBP", "spawn_location": [0.0, 0.0, 100.0]},
        ),
    ]



def build_custom_tasks(task_description: str) -> list[SubTask]:
    """Create a generic set of tasks based on a freeform description."""
    return [
        SubTask(
            role=AgentRole.LEVEL_DESIGNER,
            description=f"Level design for: {task_description}",
            parameters={"task_type": "build_environment", "environment_name": task_description.replace(" ", "_"), "style": "default"},
        ),
        SubTask(
            role=AgentRole.ASSET_MANAGER,
            description=f"Asset creation for: {task_description}",
            parameters={"task_type": "create_asset", "asset_name": f"{task_description}_Asset", "asset_class": "StaticMesh"},
        ),
        SubTask(
            role=AgentRole.VEHICLE_TUNER,
            description=f"Vehicle tuning for: {task_description}",
            parameters={"task_type": "inspect_vehicle", "actor_name": "TestPawn"},
        ),
    ]


def build_validation_tasks() -> list[SubTask]:
    """Create tasks for testing and validation."""
    return [
        SubTask(
            role=AgentRole.TEST_ENGINEER,
            description="Run automated tests for code and assets",
            parameters={
                "task_type": "run_tests",
                "test_suite": "default",
                "targets": ["level_designer", "asset_manager", "vehicle_tuner"],
            },
        ),
        SubTask(
            role=AgentRole.TEST_ENGINEER,
            description="Validate code quality and correctness",
            parameters={
                "task_type": "validate_code",
                "code_module": "multi_agent_coordinator",
                "rules": ["syntax", "style", "security"],
            },
        ),
        SubTask(
            role=AgentRole.TEST_ENGINEER,
            description="Verify asset integrity and compatibility",
            parameters={
                "task_type": "verify_assets",
                "assets": ["TrackAsphaltMat", "BuildingFacadeMat", "RaceVehicleBP"],
                "checks": ["integrity", "format", "compatibility"],
            },
        ),
        SubTask(
            role=AgentRole.TEST_ENGINEER,
            description="Perform comprehensive validation checks",
            parameters={
                "task_type": "test_validation",
                "environment": "default",
                "scope": "full",
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


async def run_demo(task_description: str = None, agent_count: int = 0,
                   async_mode: bool = False, parallel: bool = True,
                   validate_mode: bool = False, infinite_validate_mode: bool = False) -> dict:
    """Run the multi-agent coordination demo.

    Args:
        task_description: Optional custom task description (uses race track default if None)
        agent_count: Override number of agents (0 = auto from tasks)
        async_mode: Use fire-and-forget execution
        parallel: Run tasks in parallel with concurrency limiting
        validate_mode: Run test engineer validation tasks
        infinite_validate_mode: Run infinite validation loop without max retry cap

    Returns:
        Dict with final results summary
    """
    print("=" * 70)
    print("MULTI-AGENT COORDINATION SYSTEM")
    print("=" * 70)

    # Select task template
    if validate_mode:
        tasks = build_validation_tasks()
        print("\n[CONFIG] Validation mode: Running test engineer validation tasks")
    elif task_description:
        tasks = build_custom_tasks(task_description)
        print(f"\n[CONFIG] Custom task: '{task_description}' ({len(tasks)} subtasks)")
    else:
        tasks = build_race_track_tasks()
        print("\n[CONFIG] Default scenario: Build a race track with vehicles")

    # Create coordinator
    coordinator = MultiAgentCoordinator(
        lmstudio_base_url="http://localhost:1234",
        mcp_url="http://localhost:3000/mcp",
    )

    # Track progress
    all_progress = []

    def on_progress(event):
        msg = f"[{event.metadata.get('role', '?')}] {event.content}"
        if event.recipient_id:
            msg += f" -> {event.recipient_id}"
        print(f"  [PROGRESS] {msg}")
        all_progress.append(msg)

    coordinator.register_progress_callback(on_progress)

    # Spawn agents for each task
    agent_map = await coordinator.spawn_agents(tasks)
    print(f"\n[SPAWNED] {len(agent_map)} agents created")

    if agent_count > 0 and len(agent_map) != agent_count:
        print(f"[CONFIG] Requested {agent_count} agents, got {len(agent_map)} (auto from tasks)")

    # Execute tasks
    start = time.time()

    if validate_mode:
        print("\n[EXECUTE] Running with VALIDATION mode (sync + self-correction loop)...")
        validation_tasks_list = build_validation_tasks()
        max_retries = None if infinite_validate_mode else 3
        results_dict = await coordinator.execute_with_validation(
            tasks=[t.task_id for t in tasks],
            validation_tasks=validation_tasks_list,
            max_retries=max_retries,
        )
    elif async_mode:
        print("\n[EXECUTE] Running in ASYNC mode (fire-and-forget)...")
        task_handles = await coordinator.execute_async()
        # Await all tasks
        results_dict = {}
        for tid, task_h in task_handles.items():
            result = await task_h
            results_dict[tid] = result
    elif parallel:
        print("\n[EXECUTE] Running in PARALLEL mode (max concurrency=5)...")
        results_dict = await coordinator.execute_parallel(max_concurrent=5)
    else:
        print("\n[EXECUTE] Running in SYNC mode (sequential with dependency resolution)...")
        results_dict = await coordinator.execute_sync()

    elapsed = time.time() - start

    # Print results
    summary = coordinator.get_results_summary()
    print(f"\n{'=' * 70}")
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"  Total:      {summary['total']}")
    print(f"  Success:    {summary['success']}")
    print(f"  Failed:     {summary['failed']}")
    if summary.get('by_role'):
        for role, count in summary['by_role'].items():
            print(f"  By role '{role}': {count}")
    print(f"  Duration:   {elapsed:.2f}s")

    # Print individual results
    print("\n[DETAILS]")
    for tid, result in results_dict.items():
        status_icon = "[OK]" if result.status == "success" else "[FAIL]"
        error_detail = f" — {result.error}" if result.error else ""
        print(f"  {status_icon} {tid}: [{result.role}] {result.attempts} attempt(s){error_detail}")

    # Cleanup
    await coordinator.terminate_all()

    return {
        "summary": summary,
        "results": results_dict,
        "progress": all_progress,
        "elapsed_seconds": elapsed,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Coordination System — Run coordinated AI agent tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_multi_agent.py                          # Default race track scenario
  python run_multi_agent.py --task "build a city"    # Custom task description
  python run_multi_agent.py --agents 6               # Override agent count
  python run_multi_agent.py --async                  # Async fire-and-forget mode
  python run_multi_agent.py --sequential             # Sequential sync execution
  python run_multi_agent.py --validate               # Test engineer validation mode
  python run_multi_agent.py --infinite-validate      # Infinite validation loop
        """,
    )

    parser.add_argument(
        "--task", type=str, default=None,
        help="Custom task description (default: race track with vehicles)",
    )
    parser.add_argument(
        "--agents", type=int, default=0,
        help="Override number of agents (0 = auto from tasks)",
    )
    parser.add_argument(
        "--async", dest="async_mode", action="store_true", default=False,
        help="Use fire-and-forget async execution",
    )
    parser.add_argument(
        "--sequential", dest="no_parallel", action="store_true", default=False,
        help="Run tasks sequentially instead of in parallel",
    )
    parser.add_argument(
        "--validate", dest="validate_mode", action="store_true", default=False,
        help="Run test engineer validation tasks",
    )
    parser.add_argument(
        "--infinite-validate", dest="infinite_validate_mode", action="store_true", default=False,
        help="Run infinite validation loop without max retry cap",
    )

    args = parser.parse_args()

    try:
        result = asyncio.run(run_demo(
            task_description=args.task,
            agent_count=args.agents,
            async_mode=args.async_mode,
            parallel=not args.no_parallel,
            validate_mode=args.validate_mode,
            infinite_validate_mode=args.infinite_validate_mode,
        ))

        # Print JSON summary to stdout for programmatic consumption
        print("\n[JSON]")
        json.dump({
            "success": result["summary"]["success"] > 0 or result["summary"]["failed"] == 0,
            "total": result["summary"]["total"],
            "success_count": result["summary"]["success"],
            "failed_count": result["summary"]["failed"],
            "elapsed_seconds": round(result["elapsed_seconds"], 2),
        }, indent=2)

    except KeyboardInterrupt:
        print("\n[INTERRUPT] Coordinator stopped by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
