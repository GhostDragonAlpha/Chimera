"""
MCP Test Cases Package — Organized test modules for MCP integration testing.

Each module contains tests for a specific tool category:
  - test_inspection.py: inspect tool tests (actor inspection, properties, components)
  - test_actor_control.py: control_actor tool tests (spawn, transform, components)
  - test_level_management.py: manage_level tool tests (level listing, streaming, metadata)

Usage:
    python mcp_integration_test_runner.py                    # Run all tests
    python mcp_integration_test_runner.py inspection         # Run only inspection tests
    python mcp_integration_test_runner.py actor_control      # Run only actor control tests
    python mcp_integration_test_runner.py level_management   # Run only level management tests
"""

from . import test_inspection, test_actor_control, test_level_management

__all__ = ["test_inspection", "test_actor_control", "test_level_management"]
