"""
Vehicle Tuner Agent — Specialized for vehicle configuration and physics tuning.

Uses MCP tools: control_actor, inspect, manage_blueprint.
Can adjust vehicle parameters, spawn test vehicles, and run physics tests.
Integrates with existing flight_test_suite.py for validation.
"""

import asyncio
import os
from typing import Any, Optional


try:
    from .base_agent import AgentRole, AgentSession, MessageEvent
except ImportError:
    AgentRole = None
    AgentSession = object
    MessageEvent = None


class VehicleTunerAgent(AgentSession):
    """AI agent specialized in vehicle configuration, tuning, and physics testing."""

    def __init__(self, message_bus=None, lmstudio_base_url="http://localhost:1234",
                 mcp_url="http://localhost:3000/mcp"):
        super().__init__(
            role=AgentRole.VEHICLE_TUNER,
            message_bus=message_bus,
            lmstudio_base_url=lmstudio_base_url,
            mcp_url=mcp_url,
        )

    async def _execute_task_impl(self, task_spec: dict) -> Any:
        """Execute vehicle tuning tasks using MCP tools.

        Supported task types:
          - tune_vehicle: Adjust vehicle parameters (thrust, damping, etc.)
          - spawn_test_vehicle: Spawn a test vehicle in the world
          - run_physics_test: Execute physics validation tests
          - inspect_vehicle: Inspect current vehicle configuration
          - modify_blueprint: Modify vehicle Blueprint properties
        """
        task_type = task_spec.get("task_type", "")
        parameters = task_spec.get("parameters", {})

        if task_type == "tune_vehicle":
            return await self._tune_vehicle(parameters)
        elif task_type == "spawn_test_vehicle":
            return await self._spawn_test_vehicle(parameters)
        elif task_type == "run_physics_test":
            return await self._run_physics_test(parameters)
        elif task_type == "inspect_vehicle":
            return await self._inspect_vehicle(parameters)
        elif task_type == "modify_blueprint":
            return await self._modify_blueprint(parameters)
        else:
            raise ValueError(f"Unknown vehicle tuning task type: {task_type}")

    async def _tune_vehicle(self, params: dict) -> Any:
        """Adjust vehicle parameters via control_actor."""
        actor_name = params.get("actor_name", "ChimeraPawn")
        thrust_power = params.get("thrust_power", 1500.0)
        damping = params.get("damping", 0.98)
        gravity_scale = params.get("gravity_scale", 1.0)

        self._emit_progress(f"Tuning vehicle '{actor_name}': thrust={thrust_power}, damping={damping}")

        response = await self.call_mcp_tool("control_actor", {
            "action": "set_properties",
            "parameters": {
                "actor_name": actor_name,
                "properties": {
                    "ThrustPower": thrust_power,
                    "LinDamping": damping,
                    "GravityScale": gravity_scale,
                }
            }
        })

        return {"task_type": "tune_vehicle", "response": response, "params": params}

    async def _spawn_test_vehicle(self, params: dict) -> Any:
        """Spawn a test vehicle in the world."""
        blueprint_path = params.get("blueprint_path", "/Game/Blueprints/VehicleBP")
        spawn_location = params.get("spawn_location", [0.0, 0.0, 100.0])

        self._emit_progress(f"Spawning test vehicle from {blueprint_path} at {spawn_location}")

        response = await self.call_mcp_tool("control_actor", {
            "action": "spawn_actor",
            "parameters": {
                "blueprint_path": blueprint_path,
                "location": spawn_location,
            }
        })

        return {"task_type": "spawn_test_vehicle", "response": response, "params": params}

    async def _run_physics_test(self, params: dict) -> Any:
        """Run physics validation tests using flight_test_suite integration."""
        test_types = params.get("test_types", ["thrust", "rotation", "damping"])

        self._emit_progress(f"Running physics tests: {', '.join(test_types)}")

        # Try to import and run the local flight_test_suite for validation
        try:
            from flight_test_suite import FlightTestSuite
            suite = FlightTestSuite()

            results = []
            if "thrust" in test_types:
                suite.test_thrust()
                results.append("thrust")
            if "rotation" in test_types:
                suite.test_rotation()
                results.append("rotation")
            if "damping" in test_types:
                suite.test_damping()
                results.append("damping")

            self._emit_progress(f"Physics tests complete: {len(results)}/{len(test_types)} passed")

            return {"task_type": "run_physics_test", "results": results, "params": params}

        except ImportError:
            # Fallback: run via MCP tools if flight_test_suite is unavailable
            test_ops = []
            for tt in test_types:
                test_ops.append({
                    "tool": "control_actor",
                    "arguments": {"action": f"run_{tt}_test"},
                })

            responses = {}
            for op in test_ops:
                resp = await self.call_mcp_tool(op["tool"], op["arguments"])
                responses[op["tool"]] = resp

            return {"task_type": "run_physics_test", "responses": responses, "params": params}

    async def _inspect_vehicle(self, params: dict) -> Any:
        """Inspect current vehicle configuration."""
        actor_name = params.get("actor_name", "ChimeraPawn")

        self._emit_progress(f"Inspecting vehicle '{actor_name}'")

        response = await self.call_mcp_tool("inspect", {
            "action": "get_actor_info",
            "parameters": {"actor_name": actor_name},
        })

        return {"task_type": "inspect_vehicle", "response": response, "params": params}

    async def _modify_blueprint(self, params: dict) -> Any:
        """Modify vehicle Blueprint properties."""
        blueprint_path = params.get("blueprint_path", "/Game/Blueprints/VehicleBP")
        property_changes = params.get("property_changes", {})

        self._emit_progress(f"Modifying blueprint '{blueprint_path}': {list(property_changes.keys())}")

        response = await self.call_mcp_tool("manage_blueprint", {
            "action": "set_properties",
            "parameters": {
                "blueprint_path": blueprint_path,
                "properties": property_changes,
            }
        })

        return {"task_type": "modify_blueprint", "response": response, "params": params}
