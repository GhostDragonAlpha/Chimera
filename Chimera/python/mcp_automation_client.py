"""
MCP Automation Client — Core module for automated testing workflow.

Manages MCP session lifecycle, screenshot capture, flight vehicle control,
and LM Studio AI analysis for UE Editor automated testing.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
Integrates thread-safe MetricsCollector for telemetry tracking and generates
combined session report JSON linking screenshots to telemetry snapshots.
"""

import asyncio
import base64
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from config import LM_STUDIO_MODEL

from lmstudio_client import send_to_lmstudio, display_response
from utils import MetricsCollector, export_metrics_to_json


# ---------------------------------------------------------------------------
# Telemetry Collector
# ---------------------------------------------------------------------------

telemetry_collector = MetricsCollector()


# ---------------------------------------------------------------------------
# MCP Test Client
# ---------------------------------------------------------------------------

class MCPTestClient:
    """Manages MCP session lifecycle and tool execution with telemetry tracking."""

    def __init__(self, mcp_url="http://localhost:3000/mcp"):
        self.mcp_url = mcp_url
        self.session_id = None
        self.cdn_key = None

    def initialize_session(self):
        """Send JSON-RPC initialize request and extract server info.

        Returns True on success, False on failure (with retry/backoff).
        """
        import time as time_module
        
        max_retries = 10
        base_delay_ms = 100
        
        telemetry_collector.record_call("mcp_initialize_session")
        start_time = time_module.perf_counter()

        for attempt in range(max_retries):
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-07",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "Chimera MCP Client",
                            "version": "1.0.0"
                        }
                    }
                }

                response = self._request(payload, method="mcp_initialize")
                if response and "session" in response:
                    session_info = response["session"]
                    self.session_id = session_info.get("sessionId")
                    self.cdn_key = session_info.get("cdnKey")
                    server_info = response.get("serverInfo", {})
                    print(f"[MCP] Session initialized — Server: {server_info.get('name', 'unknown')} v{server_info.get('version', '?')}")
                    
                    elapsed_time = time_module.perf_counter() - start_time
                    telemetry_collector.record_response_time("mcp_initialize_session", elapsed_time)
                    return True

                delay = base_delay_ms * (2 ** attempt)
                time_module.sleep(delay / 1000.0)

            except Exception as e:
                delay = base_delay_ms * (2 ** attempt)
                print(f"[MCP] Initialize attempt {attempt + 1}/{max_retries} failed — {e}")
                telemetry_collector.record_error("mcp_initialize_session")
                if attempt < max_retries - 1:
                    time_module.sleep(delay / 1000.0)

        elapsed_time = time_module.perf_counter() - start_time
        telemetry_collector.record_response_time("mcp_initialize_session", elapsed_time)
        print(f"[MCP] Failed to initialize session after {max_retries} attempts")
        return False

    def call_tool(self, tool_name, arguments):
        """Send tools/call request with session ID header.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Dict of tool parameters

        Returns:
            Response dict or None on failure
        """
        import time as time_module
        
        telemetry_collector.record_call(f"mcp_tool_{tool_name}")
        start_time = time_module.perf_counter()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "tool": tool_name,
                "arguments": arguments
            }
        }

        if self.session_id and self.cdn_key:
            payload["session"] = {
                "sessionId": self.session_id,
                "cdnKey": self.cdn_key
            }

        try:
            response = self._request(payload, method=f"mcp_tool_{tool_name}")
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(f"mcp_tool_{tool_name}", elapsed_time)
            return response
        except Exception:
            telemetry_collector.record_error(f"mcp_tool_{tool_name}")
            raise

    async def call_tool_async(self, tool_name, arguments):
        """Async version of call_tool for parallel operations.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Dict of tool parameters

        Returns:
            Response dict or None on failure
        """
        import time as time_module
        
        telemetry_collector.record_call(f"mcp_tool_async_{tool_name}")
        start_time = time_module.perf_counter()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "tool": tool_name,
                "arguments": arguments
            }
        }

        if self.session_id and self.cdn_key:
            payload["session"] = {
                "sessionId": self.session_id,
                "cdnKey": self.cdn_key
            }

        try:
            response = await asyncio.to_thread(self._request_sync, payload)
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(f"mcp_tool_async_{tool_name}", elapsed_time)
            return response
        except Exception:
            telemetry_collector.record_error(f"mcp_tool_async_{tool_name}")
            raise

    def _request_sync(self, payload):
        """Synchronous HTTP request helper for async compatibility."""
        import time as time_module
        
        start_time = time_module.perf_counter()
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.mcp_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time("mcp_request_sync", elapsed_time)
            
            if "error" in result:
                print(f"[MCP] Tool call error: {result['error']}")
                telemetry_collector.record_error("mcp_request_sync")
                return None

            return result

        except urllib.error.URLError as e:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time("mcp_request_sync", elapsed_time)
            telemetry_collector.record_error("mcp_request_sync")
            print(f"[MCP] Request failed: {e.reason}")
            return None
        except TimeoutError:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time("mcp_request_sync", elapsed_time)
            telemetry_collector.record_error("mcp_request_sync")
            print("[MCP] Request timed out after 30s")
            return None
        except Exception as e:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time("mcp_request_sync", elapsed_time)
            telemetry_collector.record_error("mcp_request_sync")
            print(f"[MCP] Unexpected error: {e}")
            return None

    def _request(self, payload, method="mcp_request"):
        """Handle HTTP POST to /mcp endpoint with timeout.

        Args:
            payload: JSON-RPC request dict
            method: Telemetry method name for tracking

        Returns:
            Response dict or None on failure/timeout
        """
        import time as time_module
        
        start_time = time_module.perf_counter()
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.mcp_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(method, elapsed_time)
            
            if "error" in result:
                print(f"[MCP] Tool call error: {result['error']}")
                telemetry_collector.record_error(method)
                return None

            return result

        except urllib.error.URLError as e:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(method, elapsed_time)
            telemetry_collector.record_error(method)
            print(f"[MCP] Request failed: {e.reason}")
            return None
        except TimeoutError:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(method, elapsed_time)
            telemetry_collector.record_error(method)
            print("[MCP] Request timed out after 30s")
            return None
        except Exception as e:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(method, elapsed_time)
            telemetry_collector.record_error(method)
            print(f"[MCP] Unexpected error: {e}")
            return None

    def get_available_tools(self):
        """List all registered MCP tools and their descriptions.

        Sends a 'tools/list' request to the MCP server and returns
        the available tools with their names, descriptions, and schemas.

        Returns:
            List of tool dicts with keys: name, description, schema, raw_response
            or empty list on failure.
        """
        import time as time_module
        
        telemetry_collector.record_call("mcp_get_available_tools")
        start_time = time_module.perf_counter()

        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 99,
                "method": "tools/list"
            }

            if self.session_id and self.cdn_key:
                payload["session"] = {
                    "sessionId": self.session_id,
                    "cdnKey": self.cdn_key
                }

            response = self._request(payload, method="mcp_tools_list")

            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time("mcp_get_available_tools", elapsed_time)

            if response is None or "result" not in response:
                print("[MCP] tools/list returned no result")
                return []

            tools_data = response.get("result", {})
            tools_list = tools_data.get("tools", [])

            available_tools = []
            for tool in tools_list:
                available_tools.append({
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "schema": tool.get("inputSchema", {}),
                    "raw_response": tool
                })

            print(f"[MCP] Discovered {len(available_tools)} available tools")
            return available_tools

        except Exception as e:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time("mcp_get_available_tools", elapsed_time)
            telemetry_collector.record_error("mcp_get_available_tools")
            print(f"[MCP] Failed to list available tools: {e}")
            return []

    def run_batch_operations(self, operations, retry_count=3, backoff_base=2.0):
        """Chain multiple MCP tool calls together with conditional logic and retry logic.

        Each operation is a dict with keys:
          - 'tool': str — name of the MCP tool to call
          - 'arguments': dict — arguments for the tool
          - 'condition': callable or None — if provided, only executes when condition(response) returns True
          - 'on_success': callable or None — callback executed on successful response
          - 'on_failure': callable or None — callback executed on failure/None response
          - 'label': str (optional) — human-readable label for telemetry

        Conditional logic example:
            operations = [
                {
                    "tool": "find_actor",
                    "arguments": {"name": "MyActor"},
                    "condition": lambda resp: resp is not None and resp.get("exists"),
                    "on_success": lambda resp: print(f"Found actor: {resp}"),
                    "label": "check_actor_exists"
                },
                {
                    "tool": "create_actor",
                    "arguments": {"name": "MyActor", "class": "Pawn"},
                    "condition": lambda resp: True,  # always runs (runs only if previous condition was False)
                    "label": "create_actor_if_missing"
                }
            ]

        Args:
            operations: List of operation dicts defining the chain
            retry_count: Number of retries per operation on failure
            backoff_base: Base delay in seconds for exponential backoff

        Returns:
            Dict mapping operation labels to their results
        """
        import time as time_module
        
        results = {}
        
        print(f"\n[BATCH] Starting batch operations ({len(operations)} steps)")
        print("=" * 60)
        
        for i, op in enumerate(operations):
            tool_name = op.get("tool", "unknown")
            arguments = op.get("arguments", {})
            condition = op.get("condition", None)
            on_success = op.get("on_success", None)
            on_failure = op.get("on_failure", None)
            label = op.get("label", f"op_{i}_{tool_name}")
            
            print(f"\n[BATCH] Step {i + 1}/{len(operations)}: '{label}' (tool={tool_name})")
            
            attempt = 0
            last_response = None
            
            while attempt < retry_count:
                try:
                    response = self.call_tool(tool_name, arguments)
                    last_response = response
                    
                    if condition is not None:
                        cond_result = condition(response)
                        print(f"[BATCH]   Condition check for '{label}': {cond_result}")
                        
                        if cond_result:
                            # Condition passed — execute this step
                            print(f"[BATCH]   Executing '{label}'...")
                            
                            if on_success and response is not None:
                                try:
                                    on_success(response)
                                except Exception as e:
                                    print(f"[BATCH]   Warning: on_success callback error: {e}")
                            
                            results[label] = {"status": "success", "response": response, "attempts": attempt + 1}
                            break
                        
                        else:
                            # Condition failed — skip this step
                            print(f"[BATCH]   Skipping '{label}' (condition not met)")
                            results[label] = {"status": "skipped", "reason": "condition_not_met", "response": None, "attempts": attempt + 1}
                            break
                    
                    else:
                        # No condition — always execute
                        print(f"[BATCH]   Executing '{label}'...")
                        
                        if on_success and response is not None:
                            try:
                                on_success(response)
                            except Exception as e:
                                print(f"[BATCH]   Warning: on_success callback error: {e}")
                        
                        results[label] = {"status": "success", "response": response, "attempts": attempt + 1}
                        break
                
                except Exception as e:
                    attempt += 1
                    delay = backoff_base * (2 ** (attempt - 1))
                    print(f"[BATCH]   Error on '{label}' (attempt {attempt}/{retry_count}): {e}")
                    
                    if attempt < retry_count:
                        print(f"[BATCH]   Retrying in {delay:.2f}s...")
                        time_module.sleep(delay)
            
            else:
                # Exhausted all retries — record failure and optionally run on_failure callback
                results[label] = {"status": "failed", "reason": "max_retries_exceeded", "response": last_response, "attempts": retry_count}
                
                if on_failure:
                    try:
                        on_failure(last_response)
                    except Exception as e:
                        print(f"[BATCH]   Warning: on_failure callback error: {e}")

        print("\n" + "=" * 60)
        
        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        skipped_count = sum(1 for r in results.values() if r.get("status") == "skipped")
        failed_count = sum(1 for r in results.values() if r.get("status") == "failed")
        
        print(f"[BATCH] Complete — {success_count} success, {skipped_count} skipped, {failed_count} failed")
        
        return results

    async def run_batch_operations_async(self, operations, max_concurrent=5, retry_count=3, backoff_base=2.0):
        """Async version of run_batch_operations with parallel execution support.

        Operations can be grouped by 'group' key — operations in the same group
        execute sequentially, but groups run in parallel (up to max_concurrent).

        Args:
            operations: List of operation dicts
            max_concurrent: Maximum number of concurrent async operations
            retry_count: Number of retries per operation
            backoff_base: Base delay for exponential backoff

        Returns:
            Dict mapping operation labels to their results
        """
        import time as time_module
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        print(f"\n[BATCH-ASYNC] Starting batch operations ({len(operations)} steps, max {max_concurrent} concurrent)")
        print("=" * 60)
        
        async def execute_op(op):
            tool_name = op.get("tool", "unknown")
            arguments = op.get("arguments", {})
            condition = op.get("condition", None)
            on_success = op.get("on_success", None)
            on_failure = op.get("on_failure", None)
            label = op.get("label", f"op_{tool_name}")
            
            async with semaphore:
                attempt = 0
                
                while attempt < retry_count:
                    try:
                        response = await self.call_tool_async(tool_name, arguments)
                        
                        if condition is not None:
                            cond_result = condition(response)
                            
                            if cond_result:
                                if on_success and response is not None:
                                    try:
                                        await asyncio.to_thread(on_success, response)
                                    except Exception as e:
                                        print(f"[BATCH-ASYNC]   Warning: on_success callback error: {e}")
                                
                                return {"status": "success", "response": response, "attempts": attempt + 1}
                            else:
                                return {"status": "skipped", "reason": "condition_not_met", "response": None, "attempts": attempt + 1}
                        
                        if on_success and response is not None:
                            try:
                                await asyncio.to_thread(on_success, response)
                            except Exception as e:
                                print(f"[BATCH-ASYNC]   Warning: on_success callback error: {e}")
                        
                        return {"status": "success", "response": response, "attempts": attempt + 1}
                    
                    except Exception as e:
                        attempt += 1
                        delay = backoff_base * (2 ** (attempt - 1))
                        print(f"[BATCH-ASYNC]   Error on '{label}' (attempt {attempt}/{retry_count}): {e}")
                        
                        if attempt < retry_count:
                            await asyncio.sleep(delay)
                
                return {"status": "failed", "reason": "max_retries_exceeded", "response": None, "attempts": retry_count}

        tasks = [execute_op(op) for op in operations]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        for i, task_result in enumerate(raw_results):
            label = operations[i].get("label", f"op_{i}")
            
            if isinstance(task_result, Exception):
                results[label] = {"status": "error", "reason": str(task_result), "response": None}
            else:
                results[label] = task_result

        print("\n" + "=" * 60)
        
        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        skipped_count = sum(1 for r in results.values() if r.get("status") == "skipped")
        failed_count = sum(1 for r in results.values() if r.get("status") == "failed")
        
        print(f"[BATCH-ASYNC] Complete — {success_count} success, {skipped_count} skipped, {failed_count} failed")
        
        return results

    def create_agent_session(self, role: str = "general", task: dict | None = None) -> dict:
        """Create a new MCP session for an AI agent role.

        Initializes a dedicated MCP session configured for the specified agent role.
        The session is optimized for the role's tool access patterns and can execute
        tasks delegated by the multi-agent coordinator.

        Args:
            role: Agent role identifier (e.g., "level_designer", "vehicle_tuner", 
                  "asset_manager", "test_engineer"). Defaults to "general".
            task: Optional task dict with keys: 'task_id', 'description', 'parameters'.
                  If provided, the session is pre-configured for this task.

        Returns:
            Dict with session info including sessionId, cdnKey, role config, and status.
            Returns empty dict on failure.
        """
        import time as time_module
        
        telemetry_collector.record_call(f"mcp_create_agent_session_{role}")
        start_time = time_module.perf_counter()

        try:
            # Initialize a new session for this agent role
            if not self.session_id or not self.cdn_key:
                if not self.initialize_session():
                    print(f"[MCP] Failed to initialize agent session for role '{role}'")
                    return {}

            # Build role-specific configuration payload
            role_config = {
                "role": role,
                "session_id": self.session_id,
                "capabilities": {},
            }

            # Configure tool access based on role
            if role in ("level_designer", "terrain"):
                role_config["tools"] = ["manage_level", "build_environment", "manage_geometry"]
                role_config["capabilities"]["terrain_generation"] = True
                role_config["capabilities"]["structure_placement"] = True
            elif role in ("vehicle_tuner", "physics"):
                role_config["tools"] = ["control_actor", "inspect", "manage_blueprint"]
                role_config["capabilities"]["vehicle_tuning"] = True
                role_config["capabilities"]["physics_testing"] = True
            elif role in ("asset_manager", "materials"):
                role_config["tools"] = ["manage_asset", "manage_material_authoring", "manage_texture"]
                role_config["capabilities"]["material_generation"] = True
                role_config["capabilities"]["texture_creation"] = True
            elif role in ("test_engineer", "qa"):
                role_config["tools"] = ["control_actor", "inspect", "system_control"]
                role_config["capabilities"]["test_execution"] = True
                role_config["capabilities"]["validation"] = True
            else:
                # General agent — full tool access
                role_config["tools"] = ["manage_level", "build_environment", "manage_geometry",
                                        "control_actor", "inspect", "manage_blueprint",
                                        "manage_asset", "manage_material_authoring", "manage_texture"]

            # If a task is provided, register it in the session context
            if task:
                role_config["current_task"] = {
                    "task_id": task.get("task_id"),
                    "description": task.get("description"),
                    "parameters": task.get("parameters", {}),
                }

            # Send agent session creation request to MCP server
            payload = {
                "jsonrpc": "2.0",
                "id": 100,
                "method": "agent/create_session",
                "params": {
                    "config": role_config,
                }
            }

            if self.session_id and self.cdn_key:
                payload["session"] = {
                    "sessionId": self.session_id,
                    "cdnKey": self.cdn_key,
                }

            response = self._request(payload, method=f"mcp_agent_create_{role}")

            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(f"mcp_create_agent_session_{role}", elapsed_time)

            if response is None or "error" in (response or {}):
                print(f"[MCP] Agent session creation failed for role '{role}'")
                return {}

            # Extract agent session info from response
            result = response.get("result", {})
            agent_session_info = {
                "sessionId": self.session_id,
                "cdnKey": self.cdn_key,
                "role": role,
                "config": role_config,
                "status": "active",
                "created_at": time_module.time(),
            }

            print(f"[MCP] Agent session created — Role: {role}, Session: {self.session_id}")
            return agent_session_info

        except Exception as e:
            elapsed_time = time_module.perf_counter() - start_time
            telemetry_collector.record_response_time(f"mcp_create_agent_session_{role}", elapsed_time)
            telemetry_collector.record_error(f"mcp_create_agent_session_{role}")
            print(f"[MCP] Error creating agent session for role '{role}': {e}")
            return {}


# ---------------------------------------------------------------------------
# Screenshot & Analysis Helpers
# ---------------------------------------------------------------------------

_screenshots_metadata = []


def _capture_and_save_screenshot(tool_response, prefix="shot", phase=None):
    """Save a base64 screenshot from MCP tool response to disk with metadata.

    Args:
        tool_response: Response dict with content array
        prefix: Filename prefix for saved images
        phase: Phase name for metadata (e.g., 'ground_capture', 'flight_capture')

    Returns:
        Dict with screenshot metadata or None on failure
    """
    import time as time_module
    
    timestamp = int(time_module.time())
    metadata = {
        "prefix": prefix,
        "phase": phase,
        "timestamp": timestamp,
        "filepath": None,
        "success": False
    }

    if not tool_response or "content" not in tool_response:
        return metadata

    for item in tool_response["content"]:
        if item.get("type") == "image":
            data = item.get("data", "")
            if not data:
                continue

            try:
                image_data = base64.b64decode(data)
                screenshots_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "..", "Screenshots"
                )
                os.makedirs(screenshots_dir, exist_ok=True)

                filepath = os.path.join(screenshots_dir, f"{prefix}_{timestamp}.png")
                with open(filepath, "wb") as f:
                    f.write(image_data)

                print(f"[SCREENSHOT] Saved {filepath}")
                metadata["filepath"] = filepath
                metadata["success"] = True
                _screenshots_metadata.append(metadata)
                return metadata
            except Exception as e:
                print(f"[SCREENSHOT] Failed to decode/save image: {e}")
                continue

        elif item.get("type") == "text":
            text = item.get("text", "")
            if "base64" in text.lower() or "data:image" in text:
                screenshots_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "..", "Screenshots"
                )
                os.makedirs(screenshots_dir, exist_ok=True)

                filepath = os.path.join(screenshots_dir, f"{prefix}_{timestamp}.png")
                with open(filepath, "w") as f:
                    f.write(text)
                print(f"[SCREENSHOT] Saved text representation to {filepath}")
                metadata["filepath"] = filepath
                metadata["success"] = True
                _screenshots_metadata.append(metadata)
                return metadata

    return metadata


def generate_combined_session_report(analysis_results=None):
    """Generate combined session report JSON linking screenshots to telemetry snapshots.

    Args:
        analysis_results: Dict with AI analysis results for ground/flight screenshots

    Returns:
        Dict containing the combined session report with screenshots and telemetry data
    """
    import time as time_module
    
    report_timestamp = int(time_module.time())
    
    # Extract screenshot metadata by phase
    ground_screenshots = [s for s in _screenshots_metadata if s.get("phase") == "ground_capture" or (not s.get("phase") and s.get("prefix") == "ground")]
    flight_screenshots = [s for s in _screenshots_metadata if s.get("phase") == "flight_capture" or (not s.get("phase") and s.get("prefix") == "flight")]
    
    # Generate telemetry snapshot
    telemetry_snapshot = export_metrics_to_json(telemetry_collector, include_timestamp=True)
    
    # Build combined session report
    report = {
        "report_generated_at": report_timestamp,
        "session_type": "automated_playtest_automation",
        "telemetry_snapshot": telemetry_snapshot,
        "screenshot_snapshots": {
            "ground_screenshots": ground_screenshots,
            "flight_screenshots": flight_screenshots,
            "total_ground_captured": len([s for s in _screenshots_metadata if s.get("prefix") == "ground" and s.get("success")]),
            "total_flight_captured": len([s for s in _screenshots_metadata if s.get("prefix") == "flight" and s.get("success")])
        },
        "ai_analysis_results": analysis_results or {"ground": None, "flight": None},
        "tdd_validation_criteria": {
            "physics_telemetry_available": bool(telemetry_snapshot.get("call_counts")),
            "screenshot_confirmation_available": bool(any(s.get("success") for s in _screenshots_metadata)),
            "ai_lift_off_confirmed": False
        }
    }
    
    # Check for lift-off confirmation from analysis results
    if analysis_results and isinstance(analysis_results, dict):
        flight_result = analysis_results.get("flight")
        if flight_result and isinstance(flight_result, dict):
            content = flight_result.get("content", "")
            reasoning_content = flight_result.get("reasoning_content", "")
            
            text = (content + " " + reasoning_content).lower()
            if any(keyword in text for keyword in ["lifted off", "in the air", "above ground", "wheels not touching"]):
                report["tdd_validation_criteria"]["ai_lift_off_confirmed"] = True
                
    # Save combined session report to file
    try:
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        report_filename = f"session_report_{report_timestamp}.json"
        report_filepath = os.path.join(reports_dir, report_filename)
        
        with open(report_filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        print(f"[REPORT] Generated combined session report: {report_filepath}")
    except Exception as e:
        print(f"[REPORT] Failed to save combined session report: {e}")
        
    return report


# ---------------------------------------------------------------------------

def _analyze_single_screenshot(filepath, prompt):
    """Send a single screenshot to LM Studio for analysis.
    
    Uses shared lmstudio_client.send_to_lmstudio() to eliminate duplicate HTTP code.

    Args:
        filepath: Path to the image file
        prompt: Analysis prompt string

    Returns:
        Analysis result dict or None on failure
    """
    import time as time_module
    
    telemetry_collector.record_call("lm_studio_screenshot_analysis")
    start_time = time_module.perf_counter()
    
    try:
        result = send_to_lmstudio(
            prompt=prompt,
            image_path=filepath,
            model_id=LM_STUDIO_MODEL,
            temperature=0.1,
            max_tokens=256,
            timeout=60
        )
        
        elapsed_time = time_module.perf_counter() - start_time
        telemetry_collector.record_response_time("lm_studio_screenshot_analysis", elapsed_time)
        
        if result:
            display_response(result)
            return result
        
        return None
    except Exception as e:
        elapsed_time = time_module.perf_counter() - start_time
        telemetry_collector.record_response_time("lm_studio_screenshot_analysis", elapsed_time)
        telemetry_collector.record_error("lm_studio_screenshot_analysis")
        print(f"[AI] Screenshot analysis failed: {e}")
        return None


def _analyze_screenshots(ground_path, flight_path):
    """Send ground and flight screenshots to LM Studio for analysis.

    Args:
        ground_path: Path to ground-level screenshot
        flight_path: Path to mid-flight screenshot

    Returns:
        Dict with 'ground' and 'flight' keys containing analysis results
    """
    results = {"ground": None, "flight": None}

    if ground_path:
        print(f"\n[AI] Analyzing ground screenshot: {ground_path}")
        prompt = (
            "Analyze this screenshot from a vehicle simulation. "
            "Confirm whether the vehicle's wheels are touching the ground surface. "
            "Describe the vehicle's position relative to the terrain."
        )
        results["ground"] = _analyze_single_screenshot(ground_path, prompt)

    if flight_path:
        print(f"\n[AI] Analyzing flight screenshot: {flight_path}")
        prompt = (
            "Analyze this screenshot from a vehicle simulation. "
            "Confirm whether the vehicle has achieved lift-off status and "
            "provide an approximate height above ground based on visual cues."
        )
        results["flight"] = _analyze_single_screenshot(flight_path, prompt)

    return results


# ---------------------------------------------------------------------------
# Main Workflow
# ---------------------------------------------------------------------------

def run_automated_test(client):
    """Orchestrate the full automated testing workflow.

    Args:
        client: MCPTestClient instance with active session

    Returns:
        Dict with test results including screenshots and analysis
    """
    import time as time_module
    
    print("\n" + "=" * 60)
    print("STARTING AUTOMATED TEST WORKFLOW")
    print("=" * 60)

    # Step 1: Start PIE via control_editor action play
    print("\n[WORKFLOW] Starting PIE...")
    pie_response = client.call_tool("control_editor", {"action": "play"})
    if not pie_response:
        print("[ERROR] Failed to start PIE")
        return {"success": False, "error": "PIE start failed"}

    # Step 2: Wait for world to load
    print("[WORKFLOW] Waiting 5s for world to load...")
    time_module.sleep(5)

    # Step 3: Capture ground-level screenshots (x2)
    print("\n[WORKFLOW] Capturing ground-level screenshots...")
    ground_metadata = []
    for i in range(2):
        shot_response = client.call_tool("control_editor", {
            "action": "screenshot",
            "mode": "full_editor_window",
            "returnBase64": True
        })
        meta = _capture_and_save_screenshot(shot_response, prefix="ground", phase="ground_capture")
        if meta and meta.get("success"):
            ground_metadata.append(meta)

    # Step 4: Toggle flight mode via system_control console command
    print("\n[WORKFLOW] Enabling flight mode...")
    flight_mode_resp = client.call_tool("system_control", {
        "console_command": "bFlightModeEnabled=True"
    })
    if not flight_mode_resp:
        print("[WARN] Flight mode toggle failed, continuing anyway...")

    # Step 5: Apply thrust via console command
    print("[WORKFLOW] Applying thrust...")
    thrust_resp = client.call_tool("system_control", {
        "console_command": "InputAction_Thrust=Pressed"
    })
    if not thrust_resp:
        print("[WARN] Thrust input failed, continuing anyway...")

    # Step 6: Wait for physics simulation
    print("[WORKFLOW] Waiting 3s for physics simulation...")
    time_module.sleep(3)

    # Step 7: Capture mid-flight screenshots (x3)
    print("\n[WORKFLOW] Capturing mid-flight screenshots...")
    flight_metadata = []
    for i in range(3):
        shot_response = client.call_tool("control_editor", {
            "action": "screenshot",
            "mode": "full_editor_window",
            "returnBase64": True
        })
        meta = _capture_and_save_screenshot(shot_response, prefix="flight", phase="flight_capture")
        if meta and meta.get("success"):
            flight_metadata.append(meta)

    # Step 8: Send first ground + first flight screenshot to LM Studio
    print("\n[WORKFLOW] Sending screenshots for AI analysis...")
    results = {
        "success": True, 
        "ground_screenshots": len([m for m in ground_metadata if m.get("success")]),
        "flight_screenshots": len([m for m in flight_metadata if m.get("success")])
    }

    ground_path = None
    flight_path = None
    
    for m in ground_metadata:
        if m.get("filepath"):
            ground_path = m["filepath"]
            break
            
    for m in flight_metadata:
        if m.get("filepath"):
            flight_path = m["filepath"]
            break

    analysis_results = {"ground": None, "flight": None}
    
    if ground_path and flight_path:
        analysis_results = _analyze_screenshots(ground_path, flight_path)
        results["analysis"] = analysis_results

    # Step 9: Stop PIE via control_editor action stop
    print("\n[WORKFLOW] Stopping PIE...")
    stop_response = client.call_tool("control_editor", {"action": "stop"})
    if not stop_response:
        print("[WARN] Failed to stop PIE — may need manual intervention")

    # Generate combined session report
    combined_report = generate_combined_session_report(analysis_results)
    results["session_report"] = combined_report

    print("\n" + "=" * 60)
    print("AUTOMATED TEST WORKFLOW COMPLETE")
    print("=" * 60)

    return results


def run_mcp_automated_test():
    """Entry point for MCP-based automated testing.

    Creates MCPTestClient, initializes session, runs workflow.
    Handles ImportError and exceptions gracefully.
    """
    try:
        client = MCPTestClient()

        print("\n[MCP] Attempting to connect to MCP server...")
        if not client.initialize_session():
            print("[ERROR] MCP session initialization failed — exiting")
            return {"success": False, "error": "MCP init failed"}

        run_automated_test(client)

    except ImportError as e:
        print(f"[WARN] Import error during MCP automation: {e}")
        print("[INFO] Exiting gracefully — existing scripts unaffected")
    except Exception as e:
        print(f"[ERROR] Unexpected error in MCP automation: {e}")
        print("[INFO] Exiting gracefully — existing scripts unaffected")


# ---------------------------------------------------------------------------
# Earth-Scale Landscape TES Integration (Wave 1 - Holodeck Convergence)
# ---------------------------------------------------------------------------

def run_earth_scale_tes_verification():
    """Run Screenshot TES verification for Earth-scale landscape features.
    
    Verifies:
    1. Seamless edge wrapping at landscape boundaries
    2. Flat-to-sphere morph formula (apparent_radius = actual_radius / distance)
    3. No pop, stutter, or visual tearing during transitions
    
    Returns analysis results from LM Studio AI-powered subjective evaluation.
    """
    try:
        # Import the TES earth scale analysis module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from tes_earth_scale_analysis import run_earth_scale_verification
        
        print("\n" + "=" * 60)
        print("TES EARTH-SCALE LANDSCAPE VERIFICATION (Holodeck Convergence)")
        print("=" * 60)
        
        results = run_earth_scale_verification()
        
        # Log results for MCP telemetry
        for test_name, result in results.items():
            if result:
                telemetry_collector.record_metric(f"tes_{test_name}", {
                    "result": str(result)[:256],  # Truncate long responses
                    "timestamp": time.time()
                })
        
        print("\n[TES] Earth-scale landscape verification complete.")
        return results
        
    except ImportError as e:
        print(f"[WARN] TES earth scale analysis module not available: {e}")
        return {"edge_wrapping": None, "flat_to_sphere_morph": None}
    except Exception as e:
        print(f"[ERROR] Unexpected error in TES verification: {e}")
        return {"edge_wrapping": None, "flat_to_sphere_morph": None}
