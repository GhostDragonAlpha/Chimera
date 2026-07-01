"""
MCP Client V2 — Enhanced MCP automation client with session persistence,
tool discovery caching, fluent batch builder, structured result parsing,
event subscriptions, and context manager support.

Replaces mcp_automation_client.py patterns with a modern, production-ready API.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import logging
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    ContextManager,
    Dict,
    List,
    Optional,
    Protocol,
    TypeVar,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class SessionState:
    """Persisted session state for auto-reconnect."""
    session_id: str | None = None
    cdn_key: str | None = None
    server_name: str = ""
    server_version: str = ""
    initialized_at: float = 0.0
    last_heartbeat: float = 0.0

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "cdn_key": self.cdn_key,
            "server_name": self.server_name,
            "server_version": self.server_version,
            "initialized_at": self.initialized_at,
            "last_heartbeat": self.last_heartbeat,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SessionState:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ToolInfo:
    """Cached tool metadata."""
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> ToolInfo:
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            input_schema=data.get("inputSchema", {}),
        )


@dataclass
class BatchStepResult:
    """Result of a single batch step."""
    label: str
    status: str  # "success" | "skipped" | "failed"
    response: dict | None = None
    attempts: int = 0
    error: str = ""


@dataclass
class EventSubscription:
    """Registered event subscription."""
    event_type: str
    callback: Callable[[dict], Any]
    subscription_id: str = field(default_factory=lambda: hashlib.md5(
        f"{time.time()}_{id(callback)}".encode()
    ).hexdigest())


# ---------------------------------------------------------------------------
# HTTP Transport Layer
# ---------------------------------------------------------------------------

class HTTPTTransport:
    """JSON-RPC over HTTP transport with timeout and retry support."""

    def __init__(self, url: str, timeout: int = 30, max_retries: int = 3):
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries

    def post(self, payload: dict, session_headers: dict | None = None) -> dict | None:
        """Send JSON-RPC POST and return parsed response."""
        for attempt in range(self.max_retries):
            try:
                data = json.dumps(payload).encode("utf-8")
                headers = {"Content-Type": "application/json"}
                if session_headers:
                    headers.update(session_headers)

                req = urllib.request.Request(
                    self.url, data=data, headers=headers, method="POST"
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                if "error" in result:
                    logger.warning("Server error: %s", result["error"])
                    return None
                return result

            except urllib.error.URLError as exc:
                logger.debug("Attempt %d failed: %s", attempt + 1, exc.reason)
                if attempt < self.max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))
            except TimeoutError:
                logger.warning("Request timed out after %ds", self.timeout)
                if attempt < self.max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))
            except Exception as exc:
                logger.error("Unexpected transport error: %s", exc)
                return None

        logger.error("Transport exhausted %d retries", self.max_retries)
        return None


# ---------------------------------------------------------------------------
# Session Manager with Auto-Reconnect & Persistence
# ---------------------------------------------------------------------------

class SessionManager:
    """Manages MCP session lifecycle with auto-reconnect and JSON persistence."""

    def __init__(self, transport: HTTPTTransport, cache_dir: str | Path = ".mcp_cache"):
        self.transport = transport
        self.cache_dir = Path(cache_dir)
        self.state = SessionState()
        self._lock = threading.Lock()
        self._cache_path = self.cache_dir / "session_state.json"

    # -- persistence --------------------------------------------------------

    def _save_state(self) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self._cache_path, "w") as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as exc:
            logger.warning("Failed to persist session state: %s", exc)

    def _load_state(self) -> bool:
        try:
            if self._cache_path.exists():
                with open(self._cache_path) as f:
                    data = json.load(f)
                self.state = SessionState.from_dict(data)
                return True
        except Exception as exc:
            logger.warning("Failed to load session state: %s", exc)
        return False

    # -- lifecycle ----------------------------------------------------------

    def initialize(self, client_name: str = "MCP Client V2") -> bool:
        """Initialize a new MCP session. Returns True on success."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-07",
                "capabilities": {},
                "clientInfo": {"name": client_name, "version": "2.0.0"},
            },
        }

        response = self.transport.post(payload)
        if not response or "session" not in response:
            return False

        session_info = response["session"]
        server_info = response.get("serverInfo", {})

        with self._lock:
            self.state.session_id = session_info.get("sessionId")
            self.state.cdn_key = session_info.get("cdnKey")
            self.state.server_name = server_info.get("name", "")
            self.state.server_version = server_info.get("version", "")
            self.state.initialized_at = time.time()
            self.state.last_heartbeat = time.time()

        self._save_state()
        logger.info(
            "Session initialized — Server: %s v%s",
            self.state.server_name,
            self.state.server_version,
        )
        return True

    def reconnect(self) -> bool:
        """Attempt to restore session from persisted state."""
        if not self._load_state():
            logger.warning("No cached state for reconnection")
            return False

        # Validate session by sending a lightweight ping
        payload = {
            "jsonrpc": "2.0",
            "id": 999,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-07",
                "capabilities": {},
                "clientInfo": {"name": self.state.server_name or "MCP Client V2", "version": "2.0.0"},
            },
        }

        response = self.transport.post(payload)
        if not response or "session" not in response:
            logger.warning("Reconnection failed — server rejected cached session")
            return False

        with self._lock:
            new_session = response["session"]
            self.state.session_id = new_session.get("sessionId")
            self.state.cdn_key = new_session.get("cdnKey")
            self.state.last_heartbeat = time.time()

        self._save_state()
        logger.info("Session reconnected — %s", self.state.session_id)
        return True

    def get_headers(self) -> dict | None:
        """Return session headers for authenticated requests."""
        with self._lock:
            if self.state.session_id and self.state.cdn_key:
                return {
                    "X-Session-Id": self.state.session_id,
                    "X-CDN-Key": self.state.cdn_key,
                }
        return None

    def reset(self) -> None:
        """Clear persisted session state."""
        with self._lock:
            self.state = SessionState()
        try:
            if self._cache_path.exists():
                self._cache_path.unlink()
        except Exception as exc:
            logger.warning("Failed to clear cache: %s", exc)


# ---------------------------------------------------------------------------
# Tool Discovery Cache
# ---------------------------------------------------------------------------

class ToolCache:
    """Local JSON cache for tool discovery results."""

    def __init__(self, transport: HTTPTTransport, cache_dir: str | Path = ".mcp_cache"):
        self.transport = transport
        self.cache_dir = Path(cache_dir)
        self._cache_path = self.cache_dir / "tool_cache.json"
        self._tools: dict[str, ToolInfo] = {}
        self._ttl_seconds: int = 300  # 5-minute cache TTL

    def _load(self) -> bool:
        try:
            if self._cache_path.exists():
                with open(self._cache_path) as f:
                    data = json.load(f)
                cached_at = data.get("cached_at", 0)
                if time.time() - cached_at > self._ttl_seconds:
                    return False
                for entry in data.get("tools", []):
                    info = ToolInfo.from_dict(entry)
                    self._tools[info.name] = info
                return True
        except Exception as exc:
            logger.warning("Failed to load tool cache: %s", exc)
        return False

    def _save(self) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "cached_at": time.time(),
                "tools": [t.__dict__ for t in self._tools.values()],
            }
            with open(self._cache_path, "w") as f:
                json.dump(payload, f, indent=2)
        except Exception as exc:
            logger.warning("Failed to save tool cache: %s", exc)

    def refresh(self, session_headers: dict | None = None) -> list[ToolInfo]:
        """Fetch tools from server and update local cache."""
        payload = {"jsonrpc": "2.0", "id": 98, "method": "tools/list"}
        if session_headers:
            payload["session"] = {
                "sessionId": session_headers.get("X-Session-Id"),
                "cdnKey": session_headers.get("X-CDN-Key"),
            }

        response = self.transport.post(payload)
        if not response or "result" not in response:
            return list(self._tools.values())

        tools_data = response["result"].get("tools", [])
        self._tools.clear()
        for tool in tools_data:
            info = ToolInfo.from_dict(tool)
            self._tools[info.name] = info

        self._save()
        logger.info("Tool cache refreshed — %d tools", len(self._tools))
        return list(self._tools.values())

    def get_all(self) -> list[ToolInfo]:
        """Return cached tools, refreshing if stale."""
        if not self._tools or time.time() - (self.cache_dir and Path(self._cache_path).stat().st_mtime or 0) > self._ttl_seconds:
            return []
        return list(self._tools.values())

    def get(self, name: str) -> ToolInfo | None:
        """Get a single tool by name."""
        return self._tools.get(name)


# ---------------------------------------------------------------------------
# Result Parser — Structured Python Objects
# ---------------------------------------------------------------------------

T = TypeVar("T")


class ResultParser:
    """Parse MCP tool responses into structured Python objects."""

    @staticmethod
    def extract_images(response: dict | None) -> list[bytes]:
        """Extract base64 image data from response content as raw bytes."""
        if not response or "content" not in response:
            return []

        images: list[bytes] = []
        for item in response["content"]:
            if item.get("type") == "image":
                try:
                    images.append(base64.b64decode(item["data"]))
                except Exception as exc:
                    logger.warning("Failed to decode image: %s", exc)
        return images

    @staticmethod
    def extract_text(response: dict | None) -> str:
        """Extract all text content from response."""
        if not response or "content" not in response:
            return ""

        parts: list[str] = []
        for item in response["content"]:
            if item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(parts)

    @staticmethod
    def parse_json(response: dict | None) -> Any:
        """Attempt to parse text content as JSON."""
        text = ResultParser.extract_text(response)
        if not text:
            return None
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Response text is not valid JSON")
            return None

    @staticmethod
    def save_images(images: list[bytes], prefix: str = "shot", directory: str | Path = ".screenshots") -> list[str]:
        """Save extracted images to disk. Returns file paths."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        paths: list[str] = []

        for i, img_data in enumerate(images):
            filepath = str(directory / f"{prefix}_{timestamp}_{i}.png")
            try:
                with open(filepath, "wb") as f:
                    f.write(img_data)
                paths.append(filepath)
                logger.debug("Saved image to %s", filepath)
            except Exception as exc:
                logger.warning("Failed to save image %d: %s", i, exc)

        return paths


# ---------------------------------------------------------------------------
# Event Subscription System
# ---------------------------------------------------------------------------

class EventBus:
    """Simple event bus for editor events with subscription management."""

    def __init__(self):
        self._subscriptions: dict[str, list[EventSubscription]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[dict], Any]) -> EventSubscription:
        """Register an event handler. Returns subscription ID."""
        sub = EventSubscription(event_type=event_type, callback=callback)
        with self._lock:
            self._subscriptions.setdefault(event_type, []).append(sub)
        logger.debug("Subscribed to '%s' — id=%s", event_type, sub.subscription_id)
        return sub

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription by ID. Returns True if found and removed."""
        with self._lock:
            for event_subs in self._subscriptions.values():
                for i, sub in enumerate(event_subs):
                    if sub.subscription_id == subscription_id:
                        event_subs.pop(i)
                        logger.debug("Unsubscribed %s", subscription_id)
                        return True
        return False

    def emit(self, event_type: str, data: dict) -> None:
        """Dispatch an event to all subscribers."""
        with self._lock:
            handlers = list(self._subscriptions.get(event_type, []))

        for sub in handlers:
            try:
                sub.callback(data)
            except Exception as exc:
                logger.warning("Event handler error (%s): %s", sub.subscription_id, exc)


# ---------------------------------------------------------------------------
# Batch Operation Builder — Fluent API
# ---------------------------------------------------------------------------

class BatchOperationBuilder:
    """Fluent builder for batch operations with conditional logic and callbacks."""

    def __init__(self, client: MCPClientV2):
        self._client = client
        self._steps: list[dict] = []

    def step(
        self,
        tool_name: str,
        arguments: dict | None = None,
        label: str | None = None,
        condition: Callable[[dict | None], bool] | None = None,
        on_success: Callable[[dict], Any] | None = None,
        on_failure: Callable[[dict | None], Any] | None = None,
    ) -> "BatchOperationBuilder":
        """Add a batch step. Returns self for chaining."""
        self._steps.append({
            "tool": tool_name,
            "arguments": arguments or {},
            "label": label or f"step_{len(self._steps)}_{tool_name}",
            "condition": condition,
            "on_success": on_success,
            "on_failure": on_failure,
        })
        return self

    def run(self, retry_count: int = 3, backoff_base: float = 2.0) -> dict[str, BatchStepResult]:
        """Execute all queued steps and return results."""
        results: dict[str, BatchStepResult] = {}

        for i, op in enumerate(self._steps):
            tool_name = op["tool"]
            arguments = op["arguments"]
            label = op["label"]
            condition = op.get("condition")
            on_success = op.get("on_success")
            on_failure = op.get("on_failure")

            logger.info(
                "Batch step %d/%d: '%s' (tool=%s)",
                i + 1, len(self._steps), label, tool_name,
            )

            attempt = 0
            last_response = None

            while attempt < retry_count:
                try:
                    response = self._client.call_tool(tool_name, arguments)
                    last_response = response

                    if condition is not None:
                        cond_result = condition(response)
                        logger.debug("Condition for '%s': %s", label, cond_result)

                        if cond_result:
                            if on_success and response is not None:
                                try:
                                    on_success(response)
                                except Exception as exc:
                                    logger.warning("on_success callback error: %s", exc)

                            results[label] = BatchStepResult(
                                label=label, status="success", response=response, attempts=attempt + 1
                            )
                            break
                        else:
                            results[label] = BatchStepResult(
                                label=label, status="skipped", reason="condition_not_met", attempts=attempt + 1
                            )
                            break

                    else:
                        if on_success and response is not None:
                            try:
                                on_success(response)
                            except Exception as exc:
                                logger.warning("on_success callback error: %s", exc)

                        results[label] = BatchStepResult(
                            label=label, status="success", response=response, attempts=attempt + 1
                        )
                        break

                except Exception as exc:
                    attempt += 1
                    delay = backoff_base * (2 ** (attempt - 1))
                    logger.warning("Error on '%s' (%d/%d): %s", label, attempt, retry_count, exc)

                    if attempt < retry_count:
                        time.sleep(delay)

            else:
                results[label] = BatchStepResult(
                    label=label, status="failed", reason="max_retries_exceeded", attempts=retry_count, error=str(last_response)
                )
                if on_failure:
                    try:
                        on_failure(last_response)
                    except Exception as exc:
                        logger.warning("on_failure callback error: %s", exc)

        success = sum(1 for r in results.values() if r.status == "success")
        skipped = sum(1 for r in results.values() if r.status == "skipped")
        failed = sum(1 for r in results.values() if r.status == "failed")
        logger.info("Batch complete — %d success, %d skipped, %d failed", success, skipped, failed)

        return results


# ---------------------------------------------------------------------------
# MCP Client V2 — Main Entry Point
# ---------------------------------------------------------------------------

class MCPClientV2:
    """Production-ready MCP client with session persistence, caching, events, and context manager."""

    def __init__(
        self,
        mcp_url: str = "http://localhost:3000/mcp",
        cache_dir: str | Path = ".mcp_cache",
        timeout: int = 30,
        auto_reconnect: bool = True,
    ):
        self.transport = HTTPTTransport(mcp_url, timeout=timeout)
        self.session_manager = SessionManager(self.transport, cache_dir)
        self.tool_cache = ToolCache(self.transport, cache_dir)
        self.event_bus = EventBus()
        self.parser = ResultParser()
        self.auto_reconnect = auto_reconnect
        self._active = False

    # -- context manager ----------------------------------------------------

    def __enter__(self) -> "MCPClientV2":
        """Enter context — initialize session."""
        try:
            if not self.session_manager.initialize():
                raise RuntimeError("Failed to initialize MCP session")
            self._active = True
        except Exception as exc:
            logger.error("Context enter failed: %s", exc)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context — clean shutdown."""
        self._active = False
        return False  # Do not suppress exceptions

    @contextmanager
    def session(self):
        """Context manager as a reusable session block."""
        self.__enter__()
        try:
            yield self
        finally:
            self.__exit__(None, None, None)

    # -- lifecycle ----------------------------------------------------------

    def is_active(self) -> bool:
        return self._active and self.session_manager.state.session_id is not None

    def ensure_session(self) -> bool:
        """Ensure an active session; reconnect if needed."""
        if self.is_active():
            return True

        if self.auto_reconnect:
            logger.info("No active session — attempting reconnection")
            if self.session_manager.reconnect():
                return True

        # Fresh init
        with self.session_manager._lock:
            self.session_manager.state = SessionState()

        if self.session_manager.initialize():
            return True

        logger.error("Session initialization failed")
        return False

    def call_tool(self, tool_name: str, arguments: dict) -> dict | None:
        """Call an MCP tool with session authentication."""
        if not self.ensure_session():
            logger.error("No active session for tool call: %s", tool_name)
            return None

        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000) & 0xFFFF,
            "method": "tools/call",
            "params": {"tool": tool_name, "arguments": arguments},
        }

        headers = self.session_manager.get_headers()
        if headers:
            payload["session"] = {
                "sessionId": headers.get("X-Session-Id"),
                "cdnKey": headers.get("X-CDN-Key"),
            }

        return self.transport.post(payload, session_headers=headers)

    # -- tool discovery -----------------------------------------------------

    def discover_tools(self, force_refresh: bool = False) -> list[ToolInfo]:
        """List available tools, using cache if fresh."""
        headers = self.session_manager.get_headers()

        if not force_refresh and (tools := self.tool_cache.get_all()):
            return tools

        return self.tool_cache.refresh(headers)

    def get_tool(self, name: str) -> ToolInfo | None:
        """Get a single tool from cache."""
        return self.tool_cache.get(name)

    # -- batch operations ---------------------------------------------------

    def batch(self) -> BatchOperationBuilder:
        """Create a new batch operation builder (fluent API)."""
        return BatchOperationBuilder(self)

    # -- event system -------------------------------------------------------

    def on(self, event_type: str, callback: Callable[[dict], Any]) -> EventSubscription:
        """Subscribe to an event type. Returns subscription ID."""
        return self.event_bus.subscribe(event_type, callback)

    def off(self, subscription_id: str) -> bool:
        """Unsubscribe by ID."""
        return self.event_bus.unsubscribe(subscription_id)

    def emit_event(self, event_type: str, data: dict) -> None:
        """Dispatch an event to subscribers."""
        self.event_bus.emit(event_type, data)


# ---------------------------------------------------------------------------
# Convenience Factory
# ---------------------------------------------------------------------------

def create_client(
    mcp_url: str = "http://localhost:3000/mcp",
    cache_dir: str | Path = ".mcp_cache",
    timeout: int = 30,
    auto_reconnect: bool = True,
) -> MCPClientV2:
    """Factory function to create a configured MCPClientV2 instance."""
    return MCPClientV2(
        mcp_url=mcp_url,
        cache_dir=cache_dir,
        timeout=timeout,
        auto_reconnect=auto_reconnect,
    )
