"""
Asset Manager Agent — Specialized for asset operations and dependency management.

Uses MCP tools: manage_asset, manage_material_authoring, manage_texture.
Can create/import/duplicate assets, generate materials and textures.
Handles dependency analysis and cleanup.
"""

import asyncio
from typing import Any, Optional


try:
    from .base_agent import AgentRole, AgentSession, MessageEvent
except ImportError:
    AgentRole = None
    AgentSession = object
    MessageEvent = None


class AssetManagerAgent(AgentSession):
    """AI agent specialized in asset management, material creation, and texture operations."""

    def __init__(self, message_bus=None, lmstudio_base_url="http://localhost:1234",
                 mcp_url="http://localhost:3000/mcp"):
        super().__init__(
            role=AgentRole.ASSET_MANAGER,
            message_bus=message_bus,
            lmstudio_base_url=lmstudio_base_url,
            mcp_url=mcp_url,
        )

    async def _execute_task_impl(self, task_spec: dict) -> Any:
        """Execute asset management tasks using MCP tools.

        Supported task types:
          - create_asset: Create a new asset in the project
          - import_asset: Import an external file as a project asset
          - duplicate_asset: Duplicate an existing asset
          - generate_material: Generate a material with specified properties
          - generate_texture: Generate or modify textures
          - analyze_dependencies: Analyze asset dependencies and references
          - cleanup_assets: Remove unused assets and clean up references
        """
        task_type = task_spec.get("task_type", "")
        parameters = task_spec.get("parameters", {})

        if task_type == "create_asset":
            return await self._create_asset(parameters)
        elif task_type == "import_asset":
            return await self._import_asset(parameters)
        elif task_type == "duplicate_asset":
            return await self._duplicate_asset(parameters)
        elif task_type == "generate_material":
            return await self._generate_material(parameters)
        elif task_type == "generate_texture":
            return await self._generate_texture(parameters)
        elif task_type == "analyze_dependencies":
            return await self._analyze_dependencies(parameters)
        elif task_type == "cleanup_assets":
            return await self._cleanup_assets(parameters)
        else:
            raise ValueError(f"Unknown asset management task type: {task_type}")

    async def _create_asset(self, params: dict) -> Any:
        """Create a new asset in the project."""
        asset_name = params.get("asset_name", "NewAsset")
        asset_class = params.get("asset_class", "StaticMesh")
        package_path = params.get("package_path", "/Game/Assets")

        self._emit_progress(f"Creating {asset_class} '{asset_name}' at {package_path}")

        response = await self.call_mcp_tool("manage_asset", {
            "action": "create",
            "parameters": {
                "name": asset_name,
                "class": asset_class,
                "path": package_path,
            }
        })

        return {"task_type": "create_asset", "response": response, "params": params}

    async def _import_asset(self, params: dict) -> Any:
        """Import an external file as a project asset."""
        source_path = params.get("source_path", "")
        destination_path = params.get("destination_path", "/Game/Assets")
        import_flags = params.get("flags", {})

        self._emit_progress(f"Importing from '{source_path}' to {destination_path}")

        response = await self.call_mcp_tool("manage_asset", {
            "action": "import",
            "parameters": {
                "source_path": source_path,
                "destination_path": destination_path,
                "flags": import_flags,
            }
        })

        return {"task_type": "import_asset", "response": response, "params": params}

    async def _duplicate_asset(self, params: dict) -> Any:
        """Duplicate an existing asset."""
        source_path = params.get("source_path", "")
        new_name = params.get("new_name", f"{source_path}_Copy")

        self._emit_progress(f"Duplicating '{source_path}' as '{new_name}'")

        response = await self.call_mcp_tool("manage_asset", {
            "action": "duplicate",
            "parameters": {
                "source_path": source_path,
                "new_name": new_name,
            }
        })

        return {"task_type": "duplicate_asset", "response": response, "params": params}

    async def _generate_material(self, params: dict) -> Any:
        """Generate a material with specified properties."""
        material_name = params.get("material_name", "NewMaterial")
        material_type = params.get("material_type", "Standard")
        properties = params.get("properties", {})

        self._emit_progress(f"Generating material '{material_name}' (type={material_type})")

        response = await self.call_mcp_tool("manage_material_authoring", {
            "action": "create",
            "parameters": {
                "name": material_name,
                "type": material_type,
                "properties": properties,
            }
        })

        return {"task_type": "generate_material", "response": response, "params": params}

    async def _generate_texture(self, params: dict) -> Any:
        """Generate or modify textures."""
        texture_name = params.get("texture_name", "NewTexture")
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        format_type = params.get("format", "RGBA8")

        self._emit_progress(f"Generating texture '{texture_name}' ({width}x{height}, {format_type})")

        response = await self.call_mcp_tool("manage_texture", {
            "action": "create",
            "parameters": {
                "name": texture_name,
                "dimensions": {"width": width, "height": height},
                "format": format_type,
            }
        })

        return {"task_type": "generate_texture", "response": response, "params": params}

    async def _analyze_dependencies(self, params: dict) -> Any:
        """Analyze asset dependencies and references."""
        asset_path = params.get("asset_path", "")

        self._emit_progress(f"Analyzing dependencies for '{asset_path}'")

        response = await self.call_mcp_tool("manage_asset", {
            "action": "analyze_dependencies",
            "parameters": {"asset_path": asset_path},
        })

        return {"task_type": "analyze_dependencies", "response": response, "params": params}

    async def _cleanup_assets(self, params: dict) -> Any:
        """Remove unused assets and clean up references."""
        target_folder = params.get("target_folder", "/Game")
        dry_run = params.get("dry_run", True)

        self._emit_progress(f"Cleaning up '{target_folder}' (dry_run={dry_run})")

        response = await self.call_mcp_tool("manage_asset", {
            "action": "cleanup",
            "parameters": {
                "folder": target_folder,
                "dry_run": dry_run,
            }
        })

        return {"task_type": "cleanup_assets", "response": response, "params": params}
