"""
Agent Roles Package — Specialized AI agent definitions for multi-agent coordination.

Each agent module provides a role-specific subclass of AgentSession that knows
which MCP tools to use, what task formats it accepts, and how to report results.
"""

from .base_agent import AgentSession, AgentRole, AgentStatus, MessageEvent
from .level_designer_agent import LevelDesignerAgent
from .vehicle_tuner_agent import VehicleTunerAgent
from .asset_manager_agent import AssetManagerAgent
from .test_engineer_agent import TestEngineerAgent

__all__ = [
    "AgentSession",
    "AgentRole",
    "AgentStatus",
    "MessageEvent",
    "LevelDesignerAgent",
    "VehicleTunerAgent",
    "AssetManagerAgent",
    "TestEngineerAgent",
]
