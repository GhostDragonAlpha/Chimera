"""
AI Agent v2 — Enhanced LM Studio client for Chimera project.

Extends lmstudio_client.py with:
- Multi-turn conversation with token counting and context trimming
- Structured JSON output parsing with schema validation
- C++ code generation following Chimera patterns (CHIMERA_API, UCLASS)
- Blueprint node graph generation as Python data structures
- System prompt templates for common tasks
- Offline mode with local response caching

All classes/functions are importable standalone or alongside lmstudio_client.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Imports from lmstudio_client (fallback if unavailable)
# ---------------------------------------------------------------------------

try:
    from config import LM_STUDIO_BASE_URL, LM_STUDIO_CHAT_COMPLETIONS_ENDPOINT, LM_STUDIO_MODEL, logger
    from network_utils import check_lm_studio_health
    from utils import RateLimiter
except ImportError:
    LM_STUDIO_BASE_URL = "http://localhost:5173"
    LM_STUDIO_CHAT_COMPLETIONS_ENDPOINT = "/v1/chat/completions"
    LM_STUDIO_MODEL = ""

    class _FallbackLogger:
        def debug(self, m, *a): logging.debug(m % a) if a else logging.debug(m)
        def info(self, m, *a): logging.info(m % a) if a else logging.info(m)
        def warning(self, m, *a): logging.warning(m % a) if a else logging.warning(m)
        def error(self, m, *a): logging.error(m % a) if a else logging.error(m)

    logger = _FallbackLogger()

    class RateLimiter:
        def __init__(self, requests_per_second: float = 2.0): self._delay = 1.0 / max(requests_per_second, 0.1)
        def acquire(self): time.sleep(self._delay)


# ---------------------------------------------------------------------------
# Exception Classes
# ---------------------------------------------------------------------------

class LmStudioClientError(Exception): pass
class LmStudioApiError(LmStudioClientError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

class NetworkError(LmStudioClientError): pass
class ValidationError(LmStudioClientError): pass
class ResourceError(LmStudioClientError): pass


# ---------------------------------------------------------------------------
# Multi-Turn Conversation Manager with Token Counting & Context Trimming
# ---------------------------------------------------------------------------

class ChatConversationManager:
    """Manages conversation history, token estimation, and context window trimming."""

    def __init__(self, max_tokens: int = 8192, model_id: str | None = None):
        self.max_tokens = max_tokens
        self.model_id = model_id or LM_STUDIO_MODEL
        self.messages: list[dict] = []
        self.system_prompt: str | None = None

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def add_system_message(self, content: str) -> None:
        self.system_prompt = content

    def get_messages(self) -> list[dict]:
        result = []
        if self.system_prompt is not None:
            result.append({"role": "system", "content": self.system_prompt})
        result.extend(self.messages)
        return result

    def clear_history(self, keep_system: bool = True) -> None:
        if keep_system and self.system_prompt is not None:
            self.messages = []
        else:
            self.messages = []
            self.system_prompt = None

    def estimate_token_count(self) -> int:
        total_chars = sum(len(msg.get("content", "")) for msg in self.messages)
        return max(1, total_chars // 4)

    def trim_to_context_window(self) -> None:
        target_tokens = self.max_tokens // 2
        while self.estimate_token_count() > target_tokens and len(self.messages) > 1:
            self.messages.pop(0)

    def get_context_summary(self) -> dict:
        return {
            "message_count": len(self.messages),
            "estimated_tokens": self.estimate_token_count(),
            "max_tokens": self.max_tokens,
            "has_system_prompt": self.system_prompt is not None,
        }


# ---------------------------------------------------------------------------
# System Prompt Templates for Common Tasks
# ---------------------------------------------------------------------------

class SystemPromptTemplate:
    """Pre-built templates for code review, bug fix, feature add, and more."""

    TEMPLATES = {
        "code_review": (
            "You are an expert C++ code reviewer specializing in Unreal Engine 5. "
            "Review the provided code for correctness, performance, memory safety, "
            "and adherence to UE best practices. Highlight specific issues with line references.\n"
            "Provide: (1) Summary of findings, (2) Detailed issues by severity, "
            "(3) Suggested fixes."
        ),
        "bug_fix": (
            "You are a C++ debugger for Unreal Engine projects. Analyze the bug report "
            "or error log and identify root causes. Provide step-by-step fix instructions "
            "with code snippets. Consider race conditions, GC issues, and nullptr dereferences."
        ),
        "feature_add": (
            "You are a C++ feature developer for Unreal Engine 5. Design and implement "
            "new functionality following UE patterns: UCLASS/USTRUCT annotations, "
            "CHIMERA_API macros, proper UPROPERTY configuration, and event-driven architecture."
        ),
        "code_generation": (
            "You are a C++ and Blueprint code generation assistant for Unreal Engine. "
            "Generate clean, well-documented code following UE best practices with "
            "proper macros, annotations, and memory management."
        ),
        "blueprint_design": (
            "You are a Blueprint design consultant. Provide architectural advice on "
            "event graphs, component hierarchies, and property bindings with clear reasoning."
        ),
        "screenshot_analysis": (
            "You are an AI analyst reviewing vehicle simulation screenshots. Describe "
            "physics behavior, visual cues, and anomalies concisely but thoroughly."
        ),
    }

    def __init__(self, template: str):
        self.template = template

    @classmethod
    def from_config(cls, template_name: str) -> "SystemPromptTemplate":
        if template_name not in cls.TEMPLATES:
            raise ValidationError(f"Unknown template: {template_name}. Available: {list(cls.TEMPLATES.keys())}")
        return cls(cls.TEMPLATES[template_name])

    def render(self, **kwargs) -> str:
        result = self.template
        for key, value in kwargs.items():
            placeholder = "{{" + str(key) + "}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        try:
            result = result.format(**{k: str(v) for k, v in kwargs.items()})
        except (KeyError, IndexError, ValueError):
            pass
        return result


# ---------------------------------------------------------------------------
# Structured Output Parsing with Schema Validation
# ---------------------------------------------------------------------------

class JSONModeConfig:
    """Configuration for structured JSON output and schema validation."""

    def __init__(self, schema: dict | None = None, strict_mode: bool = True):
        self.schema = schema
        self.strict_mode = strict_mode

    @classmethod
    def create_analysis_config(cls) -> "JSONModeConfig":
        return cls(
            schema={
                "type": "object",
                "properties": {
                    "observation": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "details": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["observation"],
            },
        )

    @classmethod
    def create_code_generation_config(cls) -> "JSONModeConfig":
        return cls(
            schema={
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["cpp", "blueprint"]},
                    "code": {"type": "string"},
                    "explanation": {"type": "string"},
                    "filename_hint": {"type": "string"},
                },
                "required": ["language", "code"],
            },
        )


def parse_structured_output(response: dict | None, config: JSONModeConfig | None = None) -> dict | Any:
    """Extract and validate JSON from model responses against optional schemas."""
    if not response or "content" not in response:
        return {}

    content = response.get("content", "")

    # Try markdown code fences first
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if config and config.schema:
                return _validate_json_against_schema(parsed, config.schema)
            return parsed
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: find JSON object anywhere in content
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if config and config.schema:
                return _validate_json_against_schema(parsed, config.schema)
            return parsed
        except (json.JSONDecodeError, KeyError):
            pass

    result = {"raw_content": content}
    if response.get("reasoning_content"):
        result["reasoning"] = response["reasoning_content"]
    return result


def _validate_json_against_schema(data: Any, schema: dict) -> Any:
    """Validate parsed JSON against a simple schema definition."""
    if not isinstance(schema, dict):
        return data

    expected_type = schema.get("type")

    if expected_type == "object" and isinstance(data, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field in required:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        filtered = {}
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")

                if expected_type == "string" and not isinstance(value, str):
                    raise ValidationError(f"Field {key} must be a string")
                elif expected_type == "number":
                    if not isinstance(value, (int, float)):
                        raise ValidationError(f"Field {key} must be a number")

                filtered[key] = value
        return filtered

    return data


# ---------------------------------------------------------------------------
# C++ Code Generation — Chimera Project Patterns
# ---------------------------------------------------------------------------

class CppCodeGenerator:
    """Generate C++ header/source files following Chimera/UE project patterns."""

    COMMON_INCLUDES = [
        "#include \"Core.h\"",
        "#include \"CoreTypes.h\"",
        "#include \"GameFramework/Actor.h\"",
        "#include \"Components/SceneComponent.h\"",
        "#include \"Engine/World.h\"",
        "#include \"CHIMERA_API.h\"",
    ]

    @staticmethod
    def generate_header(
        class_name: str,
        base_class: str = "AActor",
        properties: list[dict] | None = None,
        functions: list[dict] | None = None,
    ) -> dict[str, str]:
        """Generate a C++ header file (.h) with UCLASS annotations and CHIMERA_API macros."""
        props = properties or []
        funcs = functions or []

        lines = [
            f"#pragma once",
            "",
            "#include \"CoreMinimal.h\"",
            f"#include \"{base_class}.h\"",
            "#include \"CHIMERA_API.h\"",
            f"#include \"{class_name.replace('A', '').replace('U', '')}.generated.h\"",
            "",
        ]

        lines.append(f"/// @brief Chimera module class: {class_name}")
        lines.append(f"CHIMERA_API({class_name})")
        lines.append(f"class {class_name} : public {base_class}")
        lines.append("{")
        lines.append("\tGENERATED_BODY()")
        lines.append("};")

        return {f"{class_name.lower()}.h": "\n".join(lines)}

    @staticmethod
    def generate_source(
        class_name: str,
        functions: list[dict] | None = None,
        constructor_body: str = "",
    ) -> dict[str, str]:
        """Generate a C++ source file (.cpp) with implementation."""
        funcs = functions or []
        lines = [
            f"#include \"{class_name.replace('A', '').replace('U', '')}.h\"",
            "",
        ]

        # Constructor
        lines.append(f"{class_name}::{class_name}(const FObjectInitializer& obj)")
        lines.append("{")
        if constructor_body:
            for line in constructor_body.splitlines():
                lines.append(f"\t{line}")
        else:
            lines.append("\tSuper::ConstructorScript();")
        lines.append("}")

        # Function implementations
        for func in funcs:
            name = func.get("name", "")
            ret_type = func.get("return_type", "void")
            params = func.get("params", [])

            param_str = ", ".join(
                f"{p.get('type', 'int')} {p.get('name', 'param')}" for p in params
            ) if params else ""

            lines.append("")
            lines.append(f"{ret_type} {class_name}::{name}({param_str})")
            lines.append("{")
            lines.append("\t// TODO: implement")
            lines.append("}")

        return {f"{class_name.lower()}.cpp": "\n".join(lines)}


# ---------------------------------------------------------------------------
# Blueprint Node Graph Generation
# ---------------------------------------------------------------------------

class BlueprintNode:
    """Represents a single Blueprint graph node."""

    def __init__(self, node_type: str, name: str = "", outputs: dict | None = None, inputs: dict | None = None):
        self.node_type = node_type
        self.name = name or node_type
        self.outputs = outputs or {}
        self.inputs = inputs or {}

    def to_dict(self) -> dict:
        return {
            "node_type": self.node_type,
            "name": self.name,
            "outputs": self.outputs,
            "inputs": self.inputs,
        }


class BlueprintGraph:
    """Represents a complete Blueprint node graph as a Python data structure."""

    def __init__(self, blueprint_name: str = "BP_Chimera", parent_class: str = "Actor"):
        self.blueprint_name = blueprint_name
        self.parent_class = parent_class
        self.nodes: list[BlueprintNode] = []
        self.variables: dict[str, dict] = {}

    def add_node(self, node: BlueprintNode) -> None:
        """Add a node to the graph."""
        self.nodes.append(node)

    def add_variable(self, name: str, var_type: str, default: Any = None) -> None:
        """Declare a Blueprint variable."""
        self.variables[name] = {"type": var_type, "default": default}

    def to_dict(self) -> dict:
        return {
            "blueprint_name": self.blueprint_name,
            "parent_class": self.parent_class,
            "variables": self.variables,
            "nodes": [n.to_dict() for n in self.nodes],
        }


class BlueprintGenerator:
    """Generate Blueprint node graphs from prompts or programmatic specs."""

    @staticmethod
    def create_event_graph(
        blueprint_name: str = "BP_Chimera",
        parent_class: str = "Actor",
        events: list[dict] | None = None,
        variables: dict[str, dict] | None = None,
    ) -> BlueprintGraph:
        """Create a Blueprint event graph from structured specs."""
        graph = BlueprintGraph(blueprint_name, parent_class)

        if variables:
            for name, spec in variables.items():
                graph.add_variable(name, spec.get("type", "float"), spec.get("default"))

        events = events or []
        for event_spec in events:
            event_node = BlueprintNode(
                node_type=event_spec.get("event", "EventBeginPlay"),
                name=f"Exec_{event_spec.get('event', 'Unknown')}",
            )
            graph.add_node(event_node)

            for step in event_spec.get("nodes", []):
                child = BlueprintNode(
                    node_type=step.get("type", "Function"),
                    name=step.get("name", ""),
                    inputs=step.get("inputs", {}),
                    outputs=step.get("outputs", {}),
                )
                graph.add_node(child)

        return graph


# ---------------------------------------------------------------------------
# Offline Response Cache
# ---------------------------------------------------------------------------

class OfflineCache:
    """Local JSON cache for LM Studio responses when offline."""

    def __init__(self, cache_dir: str | None = None):
        self.cache_dir = Path(cache_dir or os.path.join(os.getcwd(), ".ai_agent_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, prompt: str, model_id: str, temperature: float) -> str:
        raw = f"{prompt}|{model_id}|{temperature}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, prompt: str, model_id: str, temperature: float) -> dict | None:
        key = self._cache_key(prompt, model_id, temperature)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                logger.warning(f"Corrupt cache entry for key {key}")
                return None
        return None

    def put(self, prompt: str, model_id: str, temperature: float, response: dict) -> None:
        key = self._cache_key(prompt, model_id, temperature)
        path = self.cache_dir / f"{key}.json"
        try:
            with open(path, "w") as f:
                json.dump(response, f, default=str)
        except OSError as e:
            logger.warning(f"Failed to write cache entry: {e}")

    def clear(self) -> None:
        for p in self.cache_dir.glob("*.json"):
            try:
                p.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Unified AI Agent Interface
# ---------------------------------------------------------------------------

class AIAgent:
    """High-level agent combining conversation, code generation, and offline caching."""

    def __init__(self, model_id: str | None = None, max_tokens: int = 8192):
        self.conversation = ChatConversationManager(max_tokens=max_tokens, model_id=model_id)
        self.cache = OfflineCache()
        self.model_id = model_id or LM_STUDIO_MODEL

    def chat(self, user_message: str, temperature: float = 0.3) -> dict | None:
        """Send a message and receive a response, maintaining conversation history."""
        from lmstudio_client import send_to_lmstudio as _send
        self.conversation.add_user_message(user_message)
        self.conversation.trim_to_context_window()

        messages = self.conversation.get_messages()
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)

        try:
            result = _send(prompt, model_id=self.model_id, temperature=temperature)
            if result and result.get("content"):
                self.conversation.add_assistant_message(result["content"])
            return result
        except Exception as e:
            logger.warning(f"Chat failed (offline): {e}")
            cached = self.cache.get(user_message, self.model_id, temperature)
            if cached:
                self.conversation.add_assistant_message(cached.get("content", ""))
                return cached
            raise

    def generate_cpp(self, class_name: str, **kwargs) -> dict[str, str]:
        """Generate C++ header and source files for a Chimera class."""
        header = CppCodeGenerator.generate_header(class_name, **kwargs)
        source = CppCodeGenerator.generate_source(class_name, **kwargs)
        return {**header, **source}

    def generate_blueprint(self, blueprint_name: str, events: list[dict], variables: dict | None = None) -> BlueprintGraph:
        """Generate a Blueprint node graph from structured specs."""
        return BlueprintGenerator.create_event_graph(blueprint_name, "Actor", events, variables)

    def get_system_prompt(self, template_name: str, **kwargs) -> str:
        """Get a rendered system prompt template."""
        template = SystemPromptTemplate.from_config(template_name)
        return template.render(**kwargs)


# ---------------------------------------------------------------------------
# Legacy Compatibility Functions (from lmstudio_client)
# ---------------------------------------------------------------------------

def display_response(result: dict, prefix: str = "") -> None:
    """Display LM Studio response to console."""
    if not result:
        print(f"{prefix}No response")
        return
    content = result.get('content', '')
    reasoning_content = result.get('reasoning_content', '')
    if content:
        print(f"{prefix}AI Analysis: {content}")
    elif reasoning_content:
        print(f"{prefix}AI Reasoning: {reasoning_content}")
    error = result.get('error')
    if error:
        print(f"{prefix}[ERROR] {error}")
