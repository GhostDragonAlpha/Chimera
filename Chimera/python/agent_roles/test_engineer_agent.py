"""
Test Engineer Agent — Specialized for testing, validation, and quality assurance.

Uses MCP tools: control_actor, inspect, system_control.
Can run tests, validate code/assets, verify functionality, and report results.
Reports progress through message bus with callbacks to coordinator.
"""

import asyncio
from typing import Any, Optional


from .base_agent import AgentRole, AgentSession, MessageEvent


class TestEngineerAgent(AgentSession):
    """AI agent specialized in testing, validation, and quality assurance."""

    def __init__(self, message_bus=None, lmstudio_base_url="http://localhost:1234",
                 mcp_url="http://localhost:3000/mcp"):
        super().__init__(
            role=AgentRole.TEST_ENGINEER,
            message_bus=message_bus,
            lmstudio_base_url=lmstudio_base_url,
            mcp_url=mcp_url,
        )

    async def _execute_task_impl(self, task_spec: dict) -> Any:
        """Execute test and validation tasks using MCP tools.

        Supported task types:
          - run_tests: Execute automated tests for code or assets
          - validate_code: Validate code quality and correctness
          - verify_assets: Verify asset integrity and compatibility
          - test_validation: Perform comprehensive validation checks
        """
        task_type = task_spec.get("task_type", "")
        parameters = task_spec.get("parameters", {})

        if task_type == "run_tests":
            return await self._run_tests(parameters)
        elif task_type == "validate_code":
            return await self._validate_code(parameters)
        elif task_type == "verify_assets":
            return await self._verify_assets(parameters)
        elif task_type == "test_validation":
            return await self._test_validation(parameters)
        else:
            raise ValueError(f"Unknown test engineer task type: {task_type}")

    async def _run_tests(self, params: dict) -> Any:
        """Run automated tests using MCP control_actor and inspect tools."""
        test_suite = params.get("test_suite", "default")
        test_targets = params.get("targets", [])

        self._emit_progress(f"Running tests for suite: {test_suite}, targets: {len(test_targets)}")

        results = {}
        for target in test_targets:
            response = await self.call_mcp_tool("inspect", {
                "action": "run_test",
                "parameters": {"target": target, "suite": test_suite}
            })
            results[target] = response or {"status": "unknown"}

        success_count = sum(1 for r in results.values() if r.get("status") == "passed")
        self._emit_progress(f"Test run complete: {success_count}/{len(test_targets)} passed")

        return {"task_type": "run_tests", "results": results, "params": params}

    async def _validate_code(self, params: dict) -> Any:
        """Validate code quality and correctness."""
        code_module = params.get("code_module", "")
        validation_rules = params.get("rules", ["syntax", "style", "security"])

        self._emit_progress(f"Validating code module: {code_module} with rules: {validation_rules}")

        response = await self.call_mcp_tool("inspect", {
            "action": "validate_code",
            "parameters": {
                "module": code_module,
                "rules": validation_rules,
            }
        })

        if response:
            self._emit_progress(f"Code validation complete for {code_module}")
        else:
            raise RuntimeError("MCP inspect returned no response for code validation")

        return {"task_type": "validate_code", "response": response, "params": params}

    async def _verify_assets(self, params: dict) -> Any:
        """Verify asset integrity and compatibility."""
        asset_names = params.get("assets", [])
        verification_checks = params.get("checks", ["integrity", "format", "compatibility"])

        self._emit_progress(f"Verifying {len(asset_names)} assets with checks: {verification_checks}")

        results = {}
        for asset in asset_names:
            response = await self.call_mcp_tool("inspect", {
                "action": "verify_asset",
                "parameters": {
                    "asset_name": asset,
                    "checks": verification_checks,
                }
            })
            results[asset] = response or {"status": "unknown"}

        valid_count = sum(1 for r in results.values() if r.get("status") == "valid")
        self._emit_progress(f"Asset verification complete: {valid_count}/{len(asset_names)} valid")

        return {"task_type": "verify_assets", "results": results, "params": params}

    async def _test_validation(self, params: dict) -> Any:
        """Perform comprehensive validation checks."""
        target_environment = params.get("environment", "default")
        validation_scope = params.get("scope", "full")

        self._emit_progress(f"Running comprehensive validation for environment '{target_environment}' (scope={validation_scope})")

        # Perform system control check
        system_response = await self.call_mcp_tool("system_control", {
            "action": "health_check",
            "parameters": {"environment": target_environment}
        })

        # Perform actor inspection
        inspect_response = await self.call_mcp_tool("control_actor", {
            "action": "validate_state",
            "parameters": {"scope": validation_scope}
        })

        return {
            "task_type": "test_validation",
            "system_check": system_response,
            "inspection_result": inspect_response,
            "params": params,
        }
