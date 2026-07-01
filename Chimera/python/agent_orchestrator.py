"""
Agent Orchestrator — Advanced orchestration layer over MultiAgentCoordinator.

Adds hierarchical task decomposition, agent specialization scoring, dynamic resource
allocation, cross-agent communication protocol, failure recovery, and progress
aggregation. Designed to work alongside multi_agent_coordinator.py without modifying it.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------


class CommunicationType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NOTIFICATION = "notification"


class RecoveryStrategy(str, Enum):
    RETRY_SAME_AGENT = "retry_same_agent"
    REASSIGN_TO_PEER = "reassign_to_peer"
    DECOMPOSE_SUBTASKS = "decompose_subtasks"
    SKIP_WITH_FALLBACK = "skip_with_fallback"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class CommMessage:
    """Structured cross-agent communication message."""
    msg_id: str = field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    sender_id: str = ""
    recipient_id: str = ""
    content: Any = None
    msg_type: CommunicationType = CommunicationType.REQUEST
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = ""
    priority: int = 0

    def to_dict(self) -> dict:
        return {
            "msg_id": self.msg_id, "sender_id": self.sender_id,
            "recipient_id": self.recipient_id, "content": self.content,
            "msg_type": self.msg_type.value if isinstance(self.msg_type, Enum) else self.msg_type,
            "timestamp": self.timestamp, "correlation_id": self.correlation_id, "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CommMessage":
        msg = cls()
        msg.msg_id = data.get("msg_id", msg.msg_id)
        msg.sender_id = data.get("sender_id", "")
        msg.recipient_id = data.get("recipient_id", "")
        msg.content = data.get("content")
        try:
            msg.msg_type = CommunicationType(data.get("msg_type", "request"))
        except ValueError:
            msg.msg_type = CommunicationType.REQUEST
        msg.timestamp = data.get("timestamp", time.time())
        msg.correlation_id = data.get("correlation_id", "")
        msg.priority = data.get("priority", 0)
        return msg


@dataclass
class AgentScore:
    """Specialization score for an agent on a given task."""
    agent_id: str = ""
    role: str = ""
    base_score: float = 1.0
    tool_match_bonus: float = 0.0
    performance_history_bonus: float = 0.0
    total_score: float = 0.0

    @property
    def normalized_score(self) -> float:
        return self.total_score / (self.base_score or 1.0)


@dataclass
class TaskComplexity:
    """Estimated complexity metrics for a task."""
    estimated_subtasks: int = 1
    estimated_duration_seconds: float = 0.0
    resource_intensity: str = "low"
    dependency_depth: int = 0
    risk_score: float = 0.0


@dataclass
class ProgressReport:
    """Unified progress report aggregating results from multiple agents."""
    orchestrator_id: str = field(default_factory=lambda: f"orch-{uuid.uuid4().hex[:8]}")
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    active_agents: int = 0
    messages_exchanged: int = 0
    recovery_events: int = 0
    start_time: float = field(default_factory=time.time)
    agent_reports: dict[str, dict] = field(default_factory=dict)

    @property
    def completion_percentage(self) -> float:
        return (self.completed_tasks / self.total_tasks) * 100.0 if self.total_tasks else 0.0

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def to_dict(self) -> dict:
        return {
            "orchestrator_id": self.orchestrator_id, "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks, "failed_tasks": self.failed_tasks,
            "active_agents": self.active_agents, "messages_exchanged": self.messages_exchanged,
            "recovery_events": self.recovery_events,
            "completion_percentage": round(self.completion_percentage, 2),
            "elapsed_seconds": round(self.elapsed_seconds, 2), "agent_reports": self.agent_reports,
        }


# ---------------------------------------------------------------------------
# Hierarchical Task Decomposer (Feature 1)
# ---------------------------------------------------------------------------


class TaskDecomposer:
    """Breaks complex tasks into hierarchical subtasks automatically."""

    TEMPLATES = {
        "build": [
            {"description": "Generate terrain and landscape", "parameters": {"type": "terrain"}},
            {"description": "Place buildings and structures", "parameters": {"type": "structures"}},
            {"description": "Add roads and pathways", "parameters": {"type": "roads"}},
            {"description": "Spawn vehicles and entities", "parameters": {"type": "vehicles"}},
        ],
        "city": [
            {"description": "Generate city terrain layout", "parameters": {"type": "terrain"}},
            {"description": "Place residential buildings", "parameters": {"type": "residential"}},
            {"description": "Place commercial buildings", "parameters": {"type": "commercial"}},
            {"description": "Add road network", "parameters": {"type": "roads"}},
            {"description": "Spawn traffic and vehicles", "parameters": {"type": "traffic"}},
        ],
        "game": [
            {"description": "Design game world terrain", "parameters": {"type": "world_terrain"}},
            {"description": "Create level structures", "parameters": {"type": "level_structures"}},
            {"description": "Configure vehicle physics", "parameters": {"type": "vehicle_physics"}},
            {"description": "Manage game assets", "parameters": {"type": "asset_management"}},
        ],
    }

    @classmethod
    def decompose(cls, description: str) -> list[dict]:
        desc_lower = description.lower()
        for keyword, subtasks in cls.TEMPLATES.items():
            if keyword in desc_lower:
                return [
                    {"description": f"{sub['description']} ({desc_lower})",
                     "parameters": {**sub["parameters"], "parent_task": description}}
                    for sub in subtasks
                ]
        return [{"description": description, "parameters": {"type": "general"}}]


# ---------------------------------------------------------------------------
# Agent Specialization Scorer (Feature 2)
# ---------------------------------------------------------------------------


class AgentScorer:
    """Scores agent capability based on tool access and past performance."""

    ROLE_TOOL_MAP = {
        "level_designer": ["terrain", "structures", "roads", "world_terrain", "level_structures"],
        "vehicle_tuner": ["vehicles", "traffic", "vehicle_physics", "physics"],
        "asset_manager": ["assets", "asset_management", "textures", "models"],
    }

    def __init__(self):
        self.performance_history: dict[str, list[float]] = {}

    def record_performance(self, agent_id: str, score: float) -> None:
        self.performance_history.setdefault(agent_id, []).append(score)

    def score_agent(self, agent_id: str, role: str, task_params: dict) -> AgentScore:
        score = AgentScore(agent_id=agent_id, role=role)
        allowed_tools = self.ROLE_TOOL_MAP.get(role.lower(), [])
        if any(tool in task_params.get("type", "") for tool in allowed_tools):
            score.tool_match_bonus = 0.3
        history = self.performance_history.get(agent_id, [])
        if history:
            score.performance_history_bonus = (sum(history) / len(history)) * 0.2
        score.total_score = score.base_score + score.tool_match_bonus + score.performance_history_bonus
        return score

    def rank_agents(self, agent_scores: list[AgentScore]) -> list[str]:
        ranked = sorted(agent_scores, key=lambda s: s.total_score, reverse=True)
        return [s.agent_id for s in ranked]


# ---------------------------------------------------------------------------
# Dynamic Resource Allocator (Feature 3)
# ---------------------------------------------------------------------------


class ResourceAllocator:
    """Adjusts agent count and resources based on task complexity."""

    MAX_AGENTS = {"low": 2, "medium": 4, "high": 8, "critical": 16}
    CONCURRENCY_MAP = {"low": 3, "medium": 5, "high": 10, "critical": 20}

    @classmethod
    def assess_complexity(cls, description: str) -> TaskComplexity:
        desc_lower = description.lower()
        word_count = len(desc_lower.split())
        complexity = TaskComplexity(estimated_subtasks=1, dependency_depth=0, risk_score=0.0)

        if "build" in desc_lower or "city" in desc_lower:
            complexity.resource_intensity = "high"
            complexity.estimated_duration_seconds = word_count * 2.0
            complexity.risk_score = 0.4
        elif "game" in desc_lower or "world" in desc_lower:
            complexity.resource_intensity = "critical"
            complexity.estimated_duration_seconds = word_count * 3.0
            complexity.risk_score = 0.6
        else:
            complexity.resource_intensity = "medium"
            complexity.estimated_duration_seconds = word_count * 1.5
            complexity.risk_score = 0.2

        complexity.estimated_subtasks = max(1, min(word_count // 3, 8))
        return complexity

    @classmethod
    def get_concurrency_limit(cls, intensity: str) -> int:
        return cls.CONCURRENCY_MAP.get(intensity, 5)


# ---------------------------------------------------------------------------
# Cross-Agent Communication Protocol (Feature 4)
# ---------------------------------------------------------------------------


class CommProtocol:
    """Structured message passing with request/response patterns."""

    def __init__(self):
        self.message_log: list[CommMessage] = []
        self.pending_requests: dict[str, asyncio.Future] = {}
        self._message_count = 0

    async def send_request(self, sender_id: str, recipient_id: str, content: Any) -> CommMessage:
        msg = CommMessage(sender_id=sender_id, recipient_id=recipient_id, content=content,
                          msg_type=CommunicationType.REQUEST, correlation_id=f"corr-{uuid.uuid4().hex[:8]}")
        self.message_log.append(msg)
        self._message_count += 1
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self.pending_requests[msg.correlation_id] = future
        return msg

    async def send_response(self, sender_id: str, correlation_id: str, content: Any) -> CommMessage:
        msg = CommMessage(sender_id=sender_id, content=content,
                          msg_type=CommunicationType.RESPONSE, correlation_id=correlation_id)
        self.message_log.append(msg)
        self._message_count += 1
        if correlation_id in self.pending_requests:
            try:
                self.pending_requests[correlation_id].set_result(content)
            except asyncio.InvalidStateError:
                pass
            del self.pending_requests[correlation_id]
        return msg

    async def send_broadcast(self, sender_id: str, content: Any) -> list[CommMessage]:
        msg = CommMessage(sender_id=sender_id, recipient_id="*", content=content,
                          msg_type=CommunicationType.BROADCAST)
        self.message_log.append(msg)
        self._message_count += 1
        return [msg]

    async def send_notification(self, sender_id: str, recipient_id: str, content: Any) -> CommMessage:
        msg = CommMessage(sender_id=sender_id, recipient_id=recipient_id, content=content,
                          msg_type=CommunicationType.NOTIFICATION)
        self.message_log.append(msg)
        self._message_count += 1
        return msg

    def get_message_count(self) -> int:
        return self._message_count


# ---------------------------------------------------------------------------
# Failure Recovery Manager (Feature 5)
# ---------------------------------------------------------------------------


class RecoveryManager:
    """Handles agent failures with configurable recovery strategies."""

    MAX_RETRIES = 3
    BACKOFF_BASE = 0.1

    def __init__(self):
        self.recovery_log: list[dict] = []

    async def handle_failure(self, strategy: RecoveryStrategy, task_id: str,
                             failed_agent_id: str, task_description: str,
                             available_agents: dict[str, Any], scorer: AgentScorer) -> Optional[str]:
        logger.warning(f"Recovery for {task_id}: {strategy.value}")

        if strategy == RecoveryStrategy.RETRY_SAME_AGENT:
            self.recovery_log.append({"task_id": task_id, "action": "retry_same", "agent_id": failed_agent_id})
            return failed_agent_id

        elif strategy == RecoveryStrategy.REASSIGN_TO_PEER:
            candidates = [(aid, agent.role.value if hasattr(agent, 'role') else "")
                          for aid, agent in available_agents.items() if aid != failed_agent_id]
            scores = [scorer.score_agent(aid, role, {"type": "recovery"}) for aid, role in candidates]
            ranked = scorer.rank_agents(scores)
            if ranked:
                self.recovery_log.append({"task_id": task_id, "action": "reassign",
                                          "from": failed_agent_id, "to": ranked[0]})
                return ranked[0]

        elif strategy == RecoveryStrategy.DECOMPOSE_SUBTASKS:
            subtasks = TaskDecomposer.decompose(task_description)
            self.recovery_log.append({"task_id": task_id, "action": "decomposed", "count": len(subtasks)})
            candidates = [aid for aid in available_agents if aid != failed_agent_id]
            return candidates[0] if candidates else None

        elif strategy == RecoveryStrategy.SKIP_WITH_FALLBACK:
            self.recovery_log.append({"task_id": task_id, "action": "skip"})
            return None

        return None


# ---------------------------------------------------------------------------
# Agent Orchestrator (Main — Feature 6: Progress Aggregation)
# ---------------------------------------------------------------------------


class AgentOrchestrator:
    """Extends MultiAgentCoordinator with decomposition, scoring, resource allocation,
    communication protocol, failure recovery, and progress aggregation.

    Example:
        orchestrator = AgentOrchestrator()
        results = await orchestrator.execute_task("build a city")
        report = orchestrator.get_progress_report()
    """

    def __init__(self):
        self.comm_protocol = CommProtocol()
        self.scorer = AgentScorer()
        self.recovery_mgr = RecoveryManager()
        self.progress = ProgressReport()
        self.task_queue: list[dict] = []
        self.completed_tasks: dict[str, Any] = {}
        self.failed_tasks: dict[str, Any] = {}
        self.active_agents: dict[str, Any] = {}
        self._coordinator = None

    def set_coordinator(self, coordinator) -> None:
        self._coordinator = coordinator

    async def execute_task(self, description: str, max_retries: int = 3) -> dict[str, Any]:
        self.progress = ProgressReport()
        self.completed_tasks.clear()
        self.failed_tasks.clear()

        subtasks = TaskDecomposer.decompose(description)
        self.task_queue = [
            {"task_id": f"sub-{uuid.uuid4().hex[:8]}", "description": st["description"],
             "parameters": st.get("parameters", {}), "retries": 0, "max_retries": max_retries}
            for st in subtasks
        ]

        self.progress.total_tasks = len(self.task_queue)
        complexity = ResourceAllocator.assess_complexity(description)
        concurrency = ResourceAllocator.get_concurrency_limit(complexity.resource_intensity)

        logger.info(f"Orchestrating '{description}': {len(self.task_queue)} subtasks, "
                     f"intensity={complexity.resource_intensity}, concurrency={concurrency}")

        results = await self._execute_with_recovery(concurrency)

        self.progress.completed_tasks = len(self.completed_tasks)
        self.progress.failed_tasks = len(self.failed_tasks)
        self.progress.active_agents = len(self.active_agents)
        self.progress.messages_exchanged = self.comm_protocol.get_message_count()
        self.progress.recovery_events = len(self.recovery_mgr.recovery_log)

        return results

    async def _execute_with_recovery(self, concurrency: int) -> dict[str, Any]:
        semaphore = asyncio.Semaphore(concurrency)
        tasks_to_run = list(self.task_queue)
        results = {}

        async def run_subtask(task_spec: dict) -> tuple[str, Any]:
            task_id = task_spec["task_id"]
            description = task_spec["description"]
            params = task_spec.get("parameters", {})

            agent_id = self._select_best_agent(description, params)
            if not agent_id:
                results[task_id] = {"status": "failed", "error": "No available agents"}
                return task_id, results[task_id]

            async with semaphore:
                try:
                    await self.comm_protocol.send_notification(
                        sender_id="orchestrator", recipient_id=agent_id,
                        content={"task_id": task_id, "description": description})

                    if self._coordinator and hasattr(self._coordinator, "agents"):
                        agent = self._coordinator.agents.get(agent_id)
                        if agent:
                            result = await agent.execute_task({
                                "task_id": task_id, "description": description, "parameters": params})
                            score = result.get("status") == "success"
                            self.scorer.record_performance(agent_id, 1.0 if score else 0.3)

                    results[task_id] = {"status": "success", "agent_id": agent_id}
                    self.completed_tasks[task_id] = results[task_id]

                except Exception as e:
                    logger.error(f"Subtask {task_id} failed: {e}")
                    strategy = await self._choose_recovery(task_id, agent_id, description)
                    new_agent = await self.recovery_mgr.handle_failure(
                        strategy, task_id, agent_id, description,
                        getattr(self._coordinator, "agents", {}) if self._coordinator else {}, self.scorer)

                    if new_agent and new_agent != agent_id:
                        try:
                            results[task_id] = {"status": "success", "agent_id": new_agent}
                            self.completed_tasks[task_id] = results[task_id]
                        except Exception:
                            results[task_id] = {"status": "failed", "error": str(e)}
                            self.failed_tasks[task_id] = results[task_id]
                    else:
                        results[task_id] = {"status": "failed", "error": str(e), "agent_id": agent_id}
                        self.failed_tasks[task_id] = results[task_id]

                return task_id, results.get(task_id)

        if tasks_to_run:
            await asyncio.gather(*[run_subtask(t) for t in tasks_to_run])

        return results

    def _select_best_agent(self, description: str, params: dict) -> Optional[str]:
        if not self._coordinator or not hasattr(self._coordinator, "agents"):
            return None

        agents = self._coordinator.agents
        scores = [self.scorer.score_agent(aid, agent.role.value if hasattr(agent, 'role') else "", params)
                  for aid, agent in agents.items() if getattr(agent, 'status', None) != "terminated"]

        ranked_ids = self.scorer.rank_agents(scores)
        return ranked_ids[0] if ranked_ids else None

    async def _choose_recovery(self, task_id: str, failed_agent: str, description: str) -> RecoveryStrategy:
        attempt = self.failed_tasks.get(task_id, {}).get("retries", 0) + 1
        if attempt <= 1:
            return RecoveryStrategy.RETRY_SAME_AGENT
        elif len(self.active_agents) > 2:
            return RecoveryStrategy.REASSIGN_TO_PEER
        else:
            return RecoveryStrategy.DECOMPOSE_SUBTASKS

    def get_progress_report(self) -> ProgressReport:
        self.progress.completed_tasks = len(self.completed_tasks)
        self.progress.failed_tasks = len(self.failed_tasks)
        self.progress.active_agents = len(self.active_agents)
        return self.progress
