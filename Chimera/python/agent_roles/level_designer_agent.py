"""
Level Designer Agent — Specialized for level/terrain generation and management.

Uses MCP tools: manage_level, build_environment, manage_geometry.
Can generate terrain chunks, place structures, and stream levels.
Reports progress through message bus with callbacks to coordinator.
"""

import asyncio
from typing import Any, Optional


from .base_agent import AgentRole, AgentSession, MessageEvent


class LevelDesignerAgent(AgentSession):
    """AI agent specialized in level design, terrain generation, and environment building."""

    def __init__(self, message_bus=None, lmstudio_base_url="http://localhost:1234",
                 mcp_url="http://localhost:3000/mcp"):
        super().__init__(
            role=AgentRole.LEVEL_DESIGNER,
            message_bus=message_bus,
            lmstudio_base_url=lmstudio_base_url,
            mcp_url=mcp_url,
        )

    async def _execute_task_impl(self, task_spec: dict) -> Any:
        """Execute level design tasks using MCP tools.

        Supported task types:
          - generate_terrain: Create terrain chunks with specified parameters
          - place_structures: Place buildings/structures in the environment
          - build_environment: Construct a full environment scene
          - manage_geometry: Add or modify geometry meshes
          - stream_level: Stream level data for large worlds
        """
        task_type = task_spec.get("task_type", "")
        parameters = task_spec.get("parameters", {})

        if task_type == "generate_terrain":
            return await self._generate_terrain(parameters)
        elif task_type == "place_structures":
            return await self._place_structures(parameters)
        elif task_type == "build_environment":
            return await self._build_environment(parameters)
        elif task_type == "manage_geometry":
            return await self._manage_geometry(parameters)
        elif task_type == "stream_level":
            return await self._stream_level(parameters)
        else:
            raise ValueError(f"Unknown level design task type: {task_type}")

    async def _generate_terrain(self, params: dict) -> Any:
        """Generate terrain chunks using MCP manage_level tool."""
        chunk_size = params.get("chunk_size", 1024)
        resolution = params.get("resolution", 256)
        seed = params.get("seed", None)

        self._emit_progress(f"Generating terrain: {chunk_size}x{chunk_size}, res={resolution}", {
            "chunk_size": chunk_size,
            "resolution": resolution,
        })

        # Call MCP tool for terrain generation
        response = await self.call_mcp_tool("manage_level", {
            "action": "generate_terrain",
            "parameters": {
                "chunk_size": chunk_size,
                "resolution": resolution,
                "seed": seed,
            }
        })

        if response:
            self._emit_progress(f"Terrain generation complete: {chunk_size}x{chunk_size}")
        else:
            raise RuntimeError("MCP manage_level returned no response for terrain generation")

        return {"task_type": "generate_terrain", "response": response, "params": params}

    async def _place_structures(self, params: dict) -> Any:
        """Place structures in the environment using build_environment."""
        structure_type = params.get("structure_type", "building")
        count = params.get("count", 1)
        placement = params.get("placement", "grid")

        self._emit_progress(f"Placing {count}x {structure_type} via {placement} layout")

        response = await self.call_mcp_tool("build_environment", {
            "action": "place_structures",
            "parameters": {
                "structure_type": structure_type,
                "count": count,
                "placement": placement,
            }
        })

        if response:
            self._emit_progress(f"Placed {count} structures")
        else:
            raise RuntimeError("MCP build_environment returned no response for structure placement")

        return {"task_type": "place_structures", "response": response, "params": params}

    async def _build_environment(self, params: dict) -> Any:
        """Build a complete environment scene."""
        env_name = params.get("environment_name", "default")
        style = params.get("style", "realistic")
        include_terrain = params.get("include_terrain", True)
        include_structures = params.get("include_structures", True)

        self._emit_progress(f"Building environment '{env_name}' (style={style})")

        operations = []
        if include_terrain:
            operations.append({"tool": "manage_level", "arguments": {"action": "create_terrain", "name": env_name}})
        if include_structures:
            operations.append({"tool": "build_environment", "arguments": {"action": "populate", "environment": env_name}})

        results = {}
        for op in operations:
            resp = await self.call_mcp_tool(op["tool"], op["arguments"])
            results[op["tool"]] = resp

        return {"task_type": "build_environment", "response": results, "params": params}

    async def _manage_geometry(self, params: dict) -> Any:
        """Add or modify geometry meshes."""
        action = params.get("action", "add_mesh")
        mesh_name = params.get("mesh_name", "default_mesh")

        self._emit_progress(f"Geometry operation: {action} '{mesh_name}'")

        response = await self.call_mcp_tool("manage_geometry", {
            "action": action,
            "parameters": {"mesh_name": mesh_name},
        })

        return {"task_type": "manage_geometry", "response": response, "params": params}

    async def _stream_level(self, params: dict) -> Any:
        """Stream level data for large worlds."""
        world_name = params.get("world_name", "default_world")
        streaming_threshold = params.get("streaming_threshold", 5000.0)

        self._emit_progress(f"Streaming level '{world_name}' (threshold={streaming_threshold})")

        response = await self.call_mcp_tool("manage_level", {
            "action": "configure_streaming",
            "parameters": {
                "world_name": world_name,
                "streaming_threshold": streaming_threshold,
            }
        })

        return {"task_type": "stream_level", "response": response, "params": params}
