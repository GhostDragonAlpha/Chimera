"""
Base Agent — Core agent session with LMStudio client integration, MCP bridge,
message bus subscription, retry logic, and error reporting.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


try:
    from lmstudio_client import (
        send_to_lmstudio_async,
        ChatConversationManager,
        LmStudioClientError,
        ResourceError,
        NetworkError,
    )
except ImportError:
    send_to_lmstudio_async = None
    ChatConversationManager = None
    LmStudioClientError = Exception
    ResourceError = Exception
    NetworkError = Exception

try:
    from mcp_automation_client import MCPTestClient
except ImportError:
    MCPTestClient = None


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class AgentRole(Enum):
    """Roles available to specialized agents."""
    LEVEL_DESIGNER = "LEVEL_DESIGNER"
    VEHICLE_TUNER = "VEHICLE_TUNER"
    ASSET_MANAGER = "ASSET_MANAGER"
    TEST_ENGINEER = "TEST_ENGINEER"


class AgentStatus(Enum):
    """Lifecycle status of an agent session."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


@dataclass
class MessageEvent:
    """A message passed through the AgentMessageBus between agents."""
    sender_id: str
    recipient_id: Optional[str] = None  # None = broadcast
    content: str = ""
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MessageEvent":
        return cls(
            sender_id=d["sender_id"],
            recipient_id=d.get("recipient_id"),
            content=d.get("content", ""),
            metadata=d.get("metadata", {}),
            timestamp=d.get("timestamp", time.time()),
        )


# ---------------------------------------------------------------------------
# Message Bus
# ---------------------------------------------------------------------------


class AgentMessageBus:
    """Shared message bus for inter-agent communication.

    Agents subscribe to topics and receive messages via callbacks.
    Supports broadcast (recipient_id=None) and direct messaging.
    Thread-safe and async-compatible.
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._lock = asyncio.Lock() if send_to_lmstudio_async else None

    def subscribe(self, topic: str, callback: Callable[[MessageEvent], None] | Callable[[MessageEvent], None]) -> None:
        """Register a callback for messages on the given topic.

        Args:
            topic: Topic name (e.g., "coordinator", "level_designer")
            callback: Function that receives a MessageEvent
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

    def publish(self, event: MessageEvent) -> None:
        """Publish an event to all subscribers of the sender's topic.

        Also routes to specific recipients if recipient_id is set.
        """
        # Route to specific recipient if set
        if event.recipient_id:
            topic = f"agent:{event.recipient_id}"
            for cb in self._subscribers.get(topic, []):
                try:
                    if asyncio.iscoroutinefunction(cb):
                        asyncio.create_task(cb(event))
                    else:
                        cb(event)
                except Exception:
                    pass

        # Route to broadcast topic (sender's role-based topic)
        broadcast_topic = f"broadcast:{event.sender_id}"
        for cb in self._subscribers.get(broadcast_topic, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(event))
                else:
                    cb(event)
            except Exception:
                pass

    def publish_to_topic(self, topic: str, event: MessageEvent) -> None:
        """Publish directly to a specific topic."""
        for cb in self._subscribers.get(topic, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(event))
                else:
                    cb(event)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Base Agent Session
# ---------------------------------------------------------------------------


class AgentSession:
    """Base agent session with LMStudio client, MCP bridge, and message bus.

    Provides standard interface for task execution, status reporting,
    retry logic, and error handling. Subclasses override _execute_task_impl()
    to provide role-specific behavior.
    """

    def __init__(self, role: AgentRole, message_bus: Optional[AgentMessageBus] = None,
                 lmstudio_base_url: str = "http://localhost:1234",
                 mcp_url: str = "http://localhost:3000/mcp"):
        self.agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        self.role = role
        self.status = AgentStatus.IDLE
        self.message_bus = message_bus
        self.lmstudio_base_url = lmstudio_base_url
        self.mcp_url = mcp_url

        # LM Studio integration
        if ChatConversationManager:
            self.conversation = ChatConversationManager(max_tokens=8192, model_id=None)
        else:
            self.conversation = None

        # MCP bridge
        self.mcp_client: Optional[MCPTestClient] = None
        self._mcp_initialized = False

        # Task tracking
        self.current_task_id: Optional[str] = None
        self.task_result: Any = None
        self.error_message: Optional[str] = None
        self._retry_count = 0
        self.max_retries = 3
        self.backoff_base = 2.0

        # Progress callbacks registered by coordinator
        self._progress_callbacks: list[Callable] = []

    def register_progress_callback(self, callback: Callable) -> None:
        """Register a callback for progress reports to the coordinator."""
        self._progress_callbacks.append(callback)

    def _emit_progress(self, message: str, metadata: Optional[dict] = None) -> None:
        """Emit a progress update through the message bus and callbacks."""
        event = MessageEvent(
            sender_id=self.agent_id,
            content=message,
            metadata={**metadata, "role": self.role.value} if metadata else {"role": self.role.value},
        )

        # Publish to coordinator broadcast topic
        if self.message_bus:
            self.message_bus.publish(event)

        # Call registered callbacks directly
        for cb in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(event))
                else:
                    cb(event)
            except Exception:
                pass

    async def initialize_mcp(self) -> bool:
        """Initialize MCP session for tool access."""
        if not MCPTestClient or self._mcp_initialized:
            return True

        try:
            self.mcp_client = MCPTestClient(mcp_url=self.mcp_url)
            result = await asyncio.to_thread(self.mcp_client.initialize_session)
            if result:
                self._mcp_initialized = True
                self._emit_progress(f"MCP session initialized for {self.role.value}")
                return True
        except Exception as e:
            self._emit_progress(f"MCP init failed: {e}", {"error": str(e)})

        return False

    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> Optional[dict]:
        """Call an MCP tool through the bridge."""
        if not self.mcp_client or not self._mcp_initialized:
            init_ok = await self.initialize_mcp()
            if not init_ok:
                return None

        try:
            response = await asyncio.to_thread(self.mcp_client.call_tool, tool_name, arguments)
            return response
        except Exception as e:
            self._emit_progress(f"MCP tool '{tool_name}' failed: {e}", {"error": str(e)})
            return None

    async def call_mcp_tool_async(self, tool_name: str, arguments: dict) -> Optional[dict]:
        """Async MCP tool call."""
        if not self.mcp_client or not self._mcp_initialized:
            init_ok = await self.initialize_mcp()
            if not init_ok:
                return None

        try:
            response = await self.mcp_client.call_tool_async(tool_name, arguments)
            return response
        except Exception as e:
            self._emit_progress(f"MCP tool '{tool_name}' async failed: {e}", {"error": str(e)})
            return None

    async def query_lmstudio(self, prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> Optional[dict]:
        """Send a prompt to LM Studio for analysis."""
        if send_to_lmstudio_async is None or self.conversation is None:
            return None

        try:
            result = await asyncio.wait_for(
                send_to_lmstudio_async(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=120,
                ),
                timeout=130,
            )
            if result and 'error' not in result:
                assistant_content = result.get("content", "")
                self.conversation.add_assistant_message(assistant_content)
            return result
        except asyncio.TimeoutError:
            self._emit_progress(f"LM Studio query timed out", {"error": "timeout"})
            return None
        except Exception as e:
            self._emit_progress(f"LM Studio query failed: {e}", {"error": str(e)})
            return None

    async def execute_task(self, task_spec: dict) -> dict:
        """Execute a task with retry logic and error reporting.

        Args:
            task_spec: Dict with keys: 'task_id', 'description', 'parameters'

        Returns:
            Result dict with status, output, and timing info
        """
        self.status = AgentStatus.RUNNING
        self.current_task_id = task_spec.get("task_id", f"task-{uuid.uuid4().hex[:8]}")
        self.error_message = None
        self._retry_count = 0

        description = task_spec.get("description", "Unknown task")
        parameters = task_spec.get("parameters", {})

        self._emit_progress(f"[{self.role.value}] Starting task: {description}", {
            "task_id": self.current_task_id,
            "parameters": str(parameters)[:200],
        })

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await self._execute_task_impl(task_spec)
                self.task_result = result
                self.status = AgentStatus.IDLE
                self.current_task_id = None

                self._emit_progress(f"[{self.role.value}] Task {self.current_task_id or 'completed'} finished successfully", {
                    "task_id": task_spec.get("task_id"),
                    "attempt": attempt,
                })
                return {
                    "status": "success",
                    "agent_id": self.agent_id,
                    "role": self.role.value,
                    "task_id": task_spec.get("task_id"),
                    "result": result,
                    "attempts": attempt,
                }

            except Exception as e:
                last_error = e
                self.error_message = str(e)
                self._retry_count += 1

                if attempt < self.max_retries:
                    delay = self.backoff_base ** (attempt - 1)
                    self._emit_progress(f"[{self.role.value}] Attempt {attempt} failed, retrying in {delay:.1f}s...", {
                        "error": str(e),
                        "retry": attempt + 1,
                    })
                    await asyncio.sleep(delay)

        # All retries exhausted
        self.status = AgentStatus.FAILED
        self._emit_progress(f"[{self.role.value}] Task FAILED after {self.max_retries} attempts: {last_error}", {
            "error": str(last_error),
        })

        return {
            "status": "failed",
            "agent_id": self.agent_id,
            "role": self.role.value,
            "task_id": task_spec.get("task_id"),
            "error": str(last_error),
            "attempts": self.max_retries,
        }

    async def _execute_task_impl(self, task_spec: dict) -> Any:
        """Override in subclasses to implement role-specific task logic."""
        raise NotImplementedError(f"{self.role.value} agent must implement _execute_task_impl")

    def get_status(self) -> dict:
        """Return current agent status and metadata."""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "error_message": self.error_message,
            "retry_count": self._retry_count,
        }

    async def terminate(self) -> None:
        """Terminate the agent session and clean up resources."""
        self.status = AgentStatus.TERMINATED
        if self.mcp_client:
            try:
                await asyncio.to_thread(self.mcp_client.call_tool, "system_control", {"action": "shutdown"})
            except Exception:
                pass
        self._emit_progress(f"[{self.role.value}] Session terminated")
