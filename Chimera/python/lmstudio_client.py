"""
Shared LM Studio Client — Centralized HTTP client for LM Studio API calls.

All Chimera modules should import from this module instead of implementing
their own HTTP requests to LM Studio. Eliminates duplicate code across:
- screenshot_lmstudio_workflow.py
- play_test.py
- runtime_screenshot_playtest.py
- mcp_automation_client.py
- one_shot.py
- run_flight_physics.py
- run_screenshot_analysis.py
- ue_editor_automation.py

Enhanced with:
- Conversation history management (ChatConversationManager)
- System prompt templating (SystemPromptTemplate)
- Structured output parsing / JSON mode (parse_structured_output, JSONModeConfig)
- Context window management (ContextWindowManager)
- generate_code_from_prompt method for C++ and Blueprint code generation
"""

import asyncio
import gc
import json
import os
import re
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

import http.client
import threading
import time
import concurrent.futures

from config import (
    LM_STUDIO_BASE_URL,
    LM_STUDIO_CHAT_COMPLETIONS_ENDPOINT,
    LM_STUDIO_MODEL,
    LM_STUDIO_MODELS_ENDPOINT,
    logger,
)
from network_utils import check_lm_studio_health
from utils import RateLimiter

LM_STUDIO_RATE_LIMITER = RateLimiter(requests_per_second=2.0)
LM_STUDIO_ASYNC_SEMAPHORE = asyncio.Semaphore(5)  # Limit concurrent async LM Studio API requests


# ---------------------------------------------------------------------------
# Exception Classes
# ---------------------------------------------------------------------------

class LmStudioClientError(Exception):
    """Base exception for LM Studio Client."""
    pass


class LmStudioApiError(LmStudioClientError):
    """Exception raised for LM Studio API errors (HTTP 5xx, etc.)."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class NetworkError(LmStudioClientError):
    """Exception raised for network/connection errors."""
    pass


class ValidationError(LmStudioClientError):
    """Exception raised for validation errors (invalid parameters)."""
    pass


class ResourceError(LmStudioClientError):
    """Exception raised for resource errors (file not found, model not loaded, etc.)."""
    pass


# ---------------------------------------------------------------------------
# Conversation History Management
# ---------------------------------------------------------------------------

class ChatConversationManager:
    """Manages conversation history with system prompts and context window limits.

    Tracks messages across multiple turns, enforces context window size,
    and provides methods to append messages, retrieve history, and clear state.
    """

    def __init__(self, max_tokens: int = 8192, model_id: str | None = None):
        self.max_tokens = max_tokens
        self.model_id = model_id or LM_STUDIO_MODEL
        self.messages: list[dict] = []
        self.system_prompt: str | None = None

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt for the conversation.

        Args:
            prompt: System-level instruction text
        """
        self.system_prompt = prompt

    def add_user_message(self, content: str) -> None:
        """Append a user message to the conversation history.

        Args:
            content: User message text
        """
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Append an assistant message to the conversation history.

        Args:
            content: Assistant response text
        """
        self.messages.append({"role": "assistant", "content": content})

    def add_system_message(self, content: str) -> None:
        """Append a system message directly (bypasses set_system_prompt).

        Args:
            content: System message text
        """
        self.system_prompt = content

    def get_messages(self) -> list[dict]:
        """Return the full conversation history including system prompt.

        Returns:
            List of message dicts with role and content keys
        """
        result = []
        if self.system_prompt is not None:
            result.append({"role": "system", "content": self.system_prompt})
        result.extend(self.messages)
        return result

    def clear_history(self, keep_system: bool = True) -> None:
        """Clear conversation history while optionally preserving system prompt.

        Args:
            keep_system: If True, retain the system prompt after clearing
        """
        if keep_system and self.system_prompt is not None:
            self.messages = []
        else:
            self.messages = []
            self.system_prompt = None

    def estimate_token_count(self) -> int:
        """Rough token count estimate based on character length.

        Returns:
            Estimated number of tokens in the conversation history
        """
        total_chars = sum(len(msg.get("content", "")) for msg in self.messages)
        return max(1, total_chars // 4)

    def trim_to_context_window(self) -> None:
        """Trim oldest messages to fit within max_tokens limit.

        Removes messages from the beginning until estimated token count
        is under half of max_tokens (preserving headroom).
        """
        target_tokens = self.max_tokens // 2
        while self.estimate_token_count() > target_tokens and len(self.messages) > 1:
            self.messages.pop(0)

    def get_context_summary(self) -> dict:
        """Return summary of conversation state.

        Returns:
            Dict with message count, estimated tokens, and system prompt presence
        """
        return {
            "message_count": len(self.messages),
            "estimated_tokens": self.estimate_token_count(),
            "max_tokens": self.max_tokens,
            "has_system_prompt": self.system_prompt is not None,
            "system_prompt_length": len(self.system_prompt) if self.system_prompt else 0,
        }


# ---------------------------------------------------------------------------
# System Prompt Template Engine
# ---------------------------------------------------------------------------

class SystemPromptTemplate:
    """Template engine for generating system prompts with variable substitution.

    Supports Jinja2-style {{variable}} syntax and Python f-string style {variable}
    for flexible prompt construction.
    """

    def __init__(self, template: str):
        self.template = template

    @staticmethod
    def from_config(template_name: str) -> "SystemPromptTemplate":
        """Load a predefined system prompt template by name.

        Args:
            template_name: Name of the template to load

        Returns:
            SystemPromptTemplate instance

        Raises:
            ValidationError: If template_name is not recognized
        """
        templates = {
            "code_generation": (
                "You are a C++ and Unreal Engine Blueprint code generation assistant. "
                "Generate clean, well-documented code following UE best practices. "
                "Include necessary includes, proper naming conventions, and handle edge cases."
            ),
            "screenshot_analysis": (
                "You are an AI analyst reviewing vehicle simulation screenshots. "
                "Describe what you see objectively. Note physics behavior, visual cues, "
                "and any anomalies. Be concise but thorough."
            ),
            "blueprint_design": (
                "You are a Blueprint design consultant for Unreal Engine. "
                "Provide architectural advice on event graphs, component hierarchies, "
                "and property bindings. Explain your reasoning clearly."
            ),
            "general_assistant": (
                "You are a helpful assistant specialized in software engineering, "
                "Unreal Engine development, and game simulation systems."
            ),
        }

        if template_name not in templates:
            raise ValidationError(f"Unknown system prompt template: {template_name}. Available: {list(templates.keys())}")

        return SystemPromptTemplate(templates[template_name])

    def render(self, **kwargs) -> str:
        """Render the template with variable substitution.

        Supports both {{variable}} and {variable} syntax.

        Args:
            **kwargs: Variables to substitute into the template

        Returns:
            Rendered prompt string
        """
        result = self.template

        # Replace {{variable}} style
        for key, value in kwargs.items():
            placeholder = "{{" + str(key) + "}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # Replace {variable} style (only where not already replaced)
        try:
            result = result.format(**{k: str(v) for k, v in kwargs.items()})
        except (KeyError, IndexError, ValueError):
            pass  # Some placeholders may have been consumed by {{}} syntax

        return result


# ---------------------------------------------------------------------------
# Structured Output Parsing / JSON Mode
# ---------------------------------------------------------------------------

class JSONModeConfig:
    """Configuration for structured JSON output from LM Studio.

    Defines the expected schema and parsing behavior for model responses.
    """

    def __init__(self, schema: dict | None = None, strict_mode: bool = True):
        self.schema = schema
        self.strict_mode = strict_mode

    @staticmethod
    def create_analysis_config() -> "JSONModeConfig":
        """Create a JSON config for screenshot analysis results.

        Returns:
            JSONModeConfig with analysis schema
        """
        return JSONModeConfig(
            schema={
                "type": "object",
                "properties": {
                    "observation": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "details": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["observation"],
            },
            strict_mode=True,
        )

    @staticmethod
    def create_code_generation_config() -> "JSONModeConfig":
        """Create a JSON config for code generation results.

        Returns:
            JSONModeConfig with code generation schema
        """
        return JSONModeConfig(
            schema={
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["cpp", "blueprint"]},
                    "code": {"type": "string"},
                    "explanation": {"type": "string"},
                    "includes": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["language", "code"],
            },
            strict_mode=True,
        )


def parse_structured_output(response: dict | None, config: JSONModeConfig | None = None) -> dict | Any:
    """Parse a model response as structured data (JSON).

    Attempts to extract JSON from the response content. If config is provided,
    validates against the schema and returns typed results.

    Args:
        response: Dict with 'content' key from LM Studio API
        config: Optional JSONModeConfig for schema validation

    Returns:
        Parsed dict or list, or raw string if no JSON found
    """
    if not response or "content" not in response:
        return {}

    content = response.get("content", "")

    # Try to extract JSON block from markdown code fences
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if config and config.schema:
                return _validate_json_against_schema(parsed, config.schema)
            return parsed
        except (json.JSONDecodeError, KeyError):
            pass

    # Try to find JSON object anywhere in the content
    json_match = re.search(r'(\{[\s\S]*?\})', content, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if config and config.schema:
                return _validate_json_against_schema(parsed, config.schema)
            return parsed
        except (json.JSONDecodeError, KeyError):
            pass

    # No JSON found — return raw content wrapped in dict for consistency
    result = {"raw_content": content}
    if response.get("reasoning_content"):
        result["reasoning"] = response["reasoning_content"]
    return result


def _validate_json_against_schema(data: Any, schema: dict) -> Any:
    """Validate parsed JSON against a simple schema definition.

    Args:
        data: Parsed JSON data
        schema: Schema dict with type and property definitions

    Returns:
        Validated (and potentially filtered) data
    """
    if not isinstance(schema, dict):
        return data

    expected_type = schema.get("type")

    if expected_type == "object" and isinstance(data, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        for field in required:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Filter to only known properties
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
            # Skip unknown fields in strict mode
        return filtered

    return data


# ---------------------------------------------------------------------------
# Context Window Manager
# ---------------------------------------------------------------------------

class ContextWindowManager:
    """Manages context window size and token budget for conversations.

    Tracks cumulative token usage, enforces limits, and provides strategies
    for managing context overflow (trimming, summarization hints).
    """

    def __init__(self, max_tokens: int = 8192):
        self.max_tokens = max_tokens
        self.token_budget_remaining = max_tokens
        self.usage_log: list[dict] = []

    def estimate_request_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for a set of messages.

        Args:
            messages: List of message dicts with role and content keys

        Returns:
            Estimated total tokens
        """
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            total += max(1, len(content) // 4)
        return total + 8  # Base overhead for model headers

    def check_budget(self, estimated_tokens: int) -> bool:
        """Check if the request fits within remaining token budget.

        Args:
            estimated_tokens: Estimated tokens for the upcoming request

        Returns:
            True if budget allows, False if exceeded
        """
        if estimated_tokens > self.token_budget_remaining:
            return False
        return True

    def consume_tokens(self, actual_tokens: int) -> None:
        """Record token usage after a request completes.

        Args:
            actual_tokens: Actual tokens consumed by the response
        """
        self.token_budget_remaining -= actual_tokens
        entry = {
            "remaining": self.token_budget_remaining,
            "timestamp": time.time(),
        }
        self.usage_log.append(entry)

    def reset_budget(self) -> None:
        """Reset token budget to max_tokens."""
        self.token_budget_remaining = self.max_tokens
        self.usage_log.clear()

    def get_status(self) -> dict:
        """Return current context window status.

        Returns:
            Dict with remaining tokens, usage count, and budget info
        """
        return {
            "max_tokens": self.max_tokens,
            "remaining": self.token_budget_remaining,
            "usage_count": len(self.usage_log),
            "budget_exhausted": self.token_budget_remaining <= 0,
        }


# ---------------------------------------------------------------------------
# HTTP Helpers
# ---------------------------------------------------------------------------

@contextmanager
def _stream_http_response(response):
    """Context manager for streaming HTTP response with explicit memory cleanup.

    Reads response in chunks to manage memory for large payloads and ensures proper cleanup.
    """
    chunks = []
    try:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        data = b''.join(chunks).decode('utf-8') if chunks else ''
        yield data
    finally:
        # Explicit buffer cleanup for large payloads to prevent memory buildup
        if chunks:
            del chunks[:]
            del chunks
        # Ensure response is properly closed to free network resources
        try:
            response.close()
        except Exception:
            pass


class LmStudioConnectionPool:
    """HTTP connection pool for LM Studio API with connection reuse and semaphore-based limits."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        parsed = urllib.parse.urlparse(base_url)
        self.host = parsed.hostname or 'localhost'
        self.port = parsed.port or (443 if parsed.scheme == 'https' else 5173)

        self.pool: list[http.client.HTTPConnection] = []
        self.max_pool_size = 5
        self._semaphore = threading.Semaphore(self.max_pool_size)

    def get_connection(self, timeout: int = 30) -> http.client.HTTPConnection:
        """Get a connection from the pool or create a new one."""
        if not self._semaphore.acquire(timeout=timeout):
            raise NetworkError(f"Could not acquire connection semaphore within {timeout}s")
        if self.pool:
            return self.pool.pop()
        conn = http.client.HTTPConnection(self.host, self.port, timeout=timeout)
        return conn

    def return_connection(self, conn: http.client.HTTPConnection):
        """Return a connection to the pool for reuse."""
        try:
            try:
                if len(self.pool) < self.max_pool_size:
                    # Check if connection is still valid by checking its sock attribute
                    if hasattr(conn, 'sock') and conn.sock is not None:
                        try:
                            conn.sock.setblocking(True)
                        except Exception:
                            pass
                        self.pool.append(conn)
                        return
            except Exception:
                pass
            # Close connection if pool is full or connection is invalid
            try:
                conn.close()
            except Exception:
                pass
        finally:
            self._semaphore.release()

    def invalidate_connection(self, conn: http.client.HTTPConnection):
        """Invalidate and close a connection, do not return to pool. Releases semaphore."""
        try:
            try:
                conn.close()
            except Exception:
                pass
        finally:
            self._semaphore.release()

    def close_all(self):
        """Close all connections in the pool."""
        for conn in self.pool:
            try:
                conn.close()
            except Exception:
                pass
        self.pool.clear()

    def __del__(self):
        """Ensure all connections are closed when the pool is garbage collected."""
        self.close_all()


_LM_STUDIO_CONN_POOL = LmStudioConnectionPool(LM_STUDIO_BASE_URL)


def get_image_mime_type(image_path: str) -> str:
    """Determine the MIME type of an image file.

    Returns 'image/png' as fallback for unsupported or unrecognized formats.
    """
    mime_map = {
        'png': 'image/png',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
    }

    ext = Path(image_path).suffix.lower().lstrip('.')
    if ext in mime_map:
        # Verify with imghdr for format consistency
        try:
            with open(image_path, "rb") as f:
                img_type = imghdr.what(None, h=f.read())
            if img_type and img_type in mime_map:
                return mime_map[img_type]
        except Exception:
            pass

    # Fallback to extension-based mapping or default to PNG
    if ext and ext in mime_map:
        return mime_map[ext]

    return "image/png"


def _request_with_retry(request_func, max_retries=3, backoff_base=2):
    last_exception = None
    for attempt in range(max_retries):
        try:
            return request_func()
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and attempt < max_retries - 1:
                wait_time = backoff_base ** attempt
                logger.warning(f"HTTP {e.code} error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                last_exception = e
                time.sleep(wait_time)
                continue
            raise e
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                wait_time = backoff_base ** attempt
                logger.warning(f"URL Error ({e.reason}), retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                last_exception = e
                time.sleep(wait_time)
                continue
            raise e
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff_base ** attempt
                logger.warning(f"Request failed ({e}), retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                last_exception = e
                time.sleep(wait_time)
                continue
            raise e
    raise last_exception or Exception("Max retries exceeded")


# ---------------------------------------------------------------------------
# Core API Functions
# ---------------------------------------------------------------------------

def send_to_lmstudio(prompt: str, image_path: str | None = None, model_id: str | None = None, temperature: float = 0.3, max_tokens: int = 1024, timeout: int = 120) -> dict | None:
    """Send a prompt (optionally with an image) to LM Studio for analysis.

    Args:
        prompt: Text prompt for the model
        image_path: Optional path to an image file to include
        model_id: Model ID (defaults to config.py LM_STUDIO_MODEL)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response (> 0)
        timeout: Request timeout in seconds (> 0)

    Returns:
        Dict with 'content', 'reasoning_content', 'has_reasoning_dump', or None on failure

    According to H-3: An LM response containing its own reasoning dump ("Here's a thinking process")
    is a RETRY with a larger token budget, never a verdict — schema-validate before consuming.
    """
    if not isinstance(prompt, str):
        raise ValidationError("prompt must be a string")
    if image_path is not None and not isinstance(image_path, str):
        raise ValidationError("image_path must be a string or None")
    if model_id is not None and not isinstance(model_id, str):
        raise ValidationError("model_id must be a string or None")
    if not isinstance(temperature, float) or not (0.0 <= temperature <= 1.0):
        raise ValidationError(f"temperature must be a float between 0.0 and 1.0, got {temperature}")
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValidationError(f"max_tokens must be an integer > 0, got {max_tokens}")
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValidationError(f"timeout must be an integer > 0, got {timeout}")
    if model_id is None:
        model_id = LM_STUDIO_MODEL

    # Check LM Studio API health before making requests
    if not check_lm_studio_health(timeout=5):
        error_msg = "LM Studio API is not reachable or healthy. Ensure LM Studio is running and accessible."
        logger.error(error_msg)
        raise ResourceError(error_msg)

    # Enforce rate limiting for LM Studio API calls
    LM_STUDIO_RATE_LIMITER.acquire()

    # Check available models for vision support via LM Studio /v1/models API endpoint.
    logger.info(f"Sending request to LM Studio with model '{model_id}'")

    def fetch_models():
        conn = _LM_STUDIO_CONN_POOL.get_connection(timeout=10)
        try:
            parsed = urllib.parse.urlparse(LM_STUDIO_MODELS_ENDPOINT)
            path = parsed.path
            if parsed.query:
                path += '?' + parsed.query
            conn.request('GET', path, headers={'Accept': 'application/json'})
            resp = conn.getresponse()
            with _stream_http_response(resp) as data:
                models_data = json.loads(data)
                del data  # Explicit cleanup for large JSON payload string
                # Extract the 'models' array from the JSON response containing model metadata
                models_list = models_data.get('models', [])
                del models_data
                gc.collect()
                return models_list
        finally:
            _LM_STUDIO_CONN_POOL.return_connection(conn)

    try:
        models = _request_with_retry(fetch_models, max_retries=3, backoff_base=2)
    except Exception as e:
        logger.warning(f"Could not fetch LM Studio models (LM Studio may not be running or is unreachable at {LM_STUDIO_MODELS_ENDPOINT}): {e}")
        models = []

    # Check if model supports vision by iterating through available models.
    # Match against model 'key', 'display_name', or 'id' fields in the LM Studio API response.
    model_supports_vision = False
    for m in models:
        key = m.get('key', '')
        # Check if current model matches the requested model_id by key, display_name, or id
        if key == model_id or model_id in [m.get('display_name', ''), m.get('id', '')]:
            # Extract vision capability from the model's 'capabilities' object
            model_supports_vision = m.get('capabilities', {}).get('vision', False)
            break

    # Build message content for the chat completions API payload
    has_image = False
    image_b64 = None

    if image_path and Path(image_path).exists():
        try:
            # Verify file is readable
            if not os.access(Path(image_path), os.R_OK):
                logger.warning(f"Image file not readable: {image_path}")
                has_image = False
            else:
                # Chunked reading for large file operations to improve memory management
                image_b64_chunks = []
                try:
                    with open(image_path, "rb") as f:
                        while True:
                            chunk = f.read(8192)
                            if not chunk:
                                break
                            # Explicit buffer cleanup for base64 encoded chunks
                            b64_chunk = base64.b64encode(chunk).decode('utf-8')
                            image_b64_chunks.append(b64_chunk)
                            del b64_chunk  # Prevent intermediate buffer buildup
                    image_b64 = ''.join(image_b64_chunks)
                finally:
                    if image_b64_chunks:
                        del image_b64_chunks[:]
                    gc.collect()
                has_image = True
        except Exception:
            pass

    messages_content = []

    if has_image and model_supports_vision:
        mime_type = get_image_mime_type(image_path)
        messages_content.append({"type": "text", "text": prompt})
        messages_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}
        })
    else:
        text_prompt = prompt
        if not has_image:
            # Do not add screenshot note for text-only prompts to avoid empty messages_content
            pass
        elif not model_supports_vision:
            text_payload = f"\n\nNote: The current model '{model_id}' does not support vision/image analysis. Sending text-only prompt."
            text_prompt = text_prompt + text_payload
        
        messages_content.append({"type": "text", "text": text_prompt})

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": messages_content}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    def send_chat_request():
        request_data = json.dumps(payload).encode('utf-8')
        conn = _LM_STUDIO_CONN_POOL.get_connection(timeout=timeout)
        invalidate_conn = False
        response = None
        try:
            parsed = urllib.parse.urlparse(LM_STUDIO_CHAT_COMPLETIONS_ENDPOINT)
            path = parsed.path
            if parsed.query:
                path += '?' + parsed.query
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            conn.request('POST', path, body=request_data, headers=headers)
            response = conn.getresponse()

            if response.status == 200:
                with _stream_http_response(response) as resp_data:
                    result = json.loads(resp_data)
                    del resp_data  # Explicit cleanup for large JSON payload string
                    # Explicit cleanup for large JSON response objects
                    if not _validate_chat_completion_response(result):
                        logger.error("Invalid chat completion response structure from LM Studio API")
                        extracted_result = {"content": "", "reasoning_content": "", "has_reasoning_dump": False, "error": "Invalid response structure from LM Studio API"}
                        del result
                        gc.collect()
                        return extracted_result
                    extracted = _extract_response(result)
                    # H-3: If reasoning dump detected, retry with larger token budget
                    if extracted.get('has_reasoning_dump'):
                        logger.warning("LM response contains reasoning dump ('thinking process'). Retrying with larger token budget.")
                        del result
                        gc.collect()
                        # Retry with increased max_tokens (e.g., 4096)
                        # We need to re-send the request with larger token budget
                        pass
                    else:
                        del result
                        gc.collect()

                    return extracted
            else:
                error_text = response.read().decode('utf-8')
                logger.error(f"LM Studio API error: {response.status} - {error_text}")
                if response.status in (502, 503, 504):
                    invalidate_conn = True
                    raise LmStudioApiError(f"LM Studio API error: {response.status} - {error_text}", response.status)
                raise LmStudioApiError(f"LM Studio API error: {response.status} - {error_text}", response.status)
        finally:
            try:
                if response is not None:
                    response.close()
            except Exception:
                pass
            if invalidate_conn:
                _LM_STUDIO_CONN_POOL.invalidate_connection(conn)
            else:
                _LM_STUDIO_CONN_POOL.return_connection(conn)

    # H-3: Retry loop for reasoning dumps - retry with larger token budget when reasoning dump is detected
    current_max_tokens = max_tokens
    reasoning_dump_retries = 0
    max_reasoning_dump_retries = 2

    while True:
        try:
            result = _request_with_retry(send_chat_request, max_retries=3, backoff_base=2)
            if result is not None and 'error' not in result:
                # Check for reasoning dump
                has_reasoning_dump = result.get('has_reasoning_dump', False)
                if has_reasoning_dump and reasoning_dump_retries < max_reasoning_dump_retries:
                    reasoning_dump_retries += 1
                    current_max_tokens = min(current_max_tokens * 2, 4096)  # Double tokens, cap at 4096
                    logger.warning(f"LM response contains reasoning dump. Retry {reasoning_dump_retries}/{max_reasoning_dump_retries} with max_tokens={current_max_tokens}")

                    # Update the request to use larger token budget
                    def send_chat_request_retry():
                        # Re-build the chat request with updated max_tokens
                        return _build_chat_completion_payload(prompt, image_b64, has_image, model_id, temperature, current_max_tokens)

                    continue  # Retry with new payload function
                elif result is not None and 'error' in result:
                    logger.error(f"LM Studio returned error: {result.get('error')}")
                    return result
                else:
                    logger.info("Successfully received response from LM Studio API")
                    return result
        except urllib.error.HTTPError as e:
            error_msg = f"LM Studio HTTP error: {e.code} - {e.reason}. Check LM Studio logs for details."
            logger.error(error_msg)
            if e.fp:
                logger.error(f"Response body: {e.fp.read().decode()}")
            raise LmStudioApiError(error_msg, e.code)

        except urllib.error.URLError as e:
            error_msg = f"Failed to connect to LM Studio (URL Error): {e.reason}. Ensure LM Studio is running and accessible at {LM_STUDIO_BASE_URL}."
            logger.error(error_msg)
            raise NetworkError(error_msg)

        except Exception as e:
            error_msg = f"Failed to send analysis request to LM Studio: {e}. Check that LM Studio is running and the model '{model_id}' is loaded."
            logger.error(error_msg)
            raise ResourceError(error_msg)


def _validate_chat_completion_response(result: dict) -> bool:
    """Validate that the chat completion response has the expected structure.

    Args:
        result: JSON response from LM Studio API

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(result, dict):
        return False

    choices = result.get('choices')
    if not isinstance(choices, list) or len(choices) == 0:
        return False

    choice = choices[0]
    if not isinstance(choice, dict):
        return False

    # Check for message or delta field
    has_message = 'message' in choice and isinstance(choice['message'], (dict, str))
    has_delta = 'delta' in choice and isinstance(choice['delta'], (dict, str))

    if not has_message and not has_delta:
        return False

    return True


def _has_reasoning_dump(text: str) -> bool:
    """Check if text contains a reasoning dump like 'Here's a thinking process'.

    According to H-3: An LM response containing its own reasoning dump is a RETRY
    with a larger token budget, never a verdict — schema-validate before consuming.

    Args:
        text: Text to check for reasoning dumps

    Returns:
        True if reasoning dump detected, False otherwise
    """
    if not isinstance(text, str):
        return False

    # Check for common reasoning dump patterns
    patterns = [
        "here's a thinking process",
        "here is a thinking process",
        "thinking process:",
        "thinking process\n",
        "let me think",
        "step by step",
        "first, let me",
        "ok, i need to"
    ]

    text_lower = text.lower()
    for pattern in patterns:
        if pattern in text_lower:
            return True

    return False


def _extract_response(result: dict) -> dict:
    """Extract content and reasoning_content from LM Studio response.

    Handles both standard 'content' field and reasoning-based models (Qwen3.6)
    that return empty 'content' with reasoning in separate 'reasoning_content' field.
    Also handles variations like delta fields for streaming, and content as list of blocks.

    According to H-3: An LM response containing its own reasoning dump ("Here's a thinking process")
    is a RETRY with a larger token budget, never a verdict — schema-validate before consuming.

    Args:
        result: JSON response from LM Studio API

    Returns:
        Dict with extracted content, reasoning_content, and 'has_reasoning_dump' flag
    """
    try:
        choices = result.get('choices')
        if not isinstance(choices, list) or not choices:
            return {"content": "", "reasoning_content": "", "has_reasoning_dump": False}

        choice = choices[0]

        # Handle different message structures: 'message', 'delta' (streaming), or nested objects
        message = None
        if isinstance(choice, dict):
            message = choice.get('message') if 'message' in choice else choice.get('delta')

        content = ""
        reasoning_content = ""

        if isinstance(message, dict):
            # Try standard 'content' field first (can be string or list of content blocks)
            content_val = message.get('content')
            if isinstance(content_val, list):
                # Extract text from content blocks
                content_blocks = [block.get('text', '') for block in content_val if isinstance(block, dict) and block.get('type') == 'text']
                content = ''.join(content_blocks) if content_blocks else ''
            elif isinstance(content_val, str):
                content = content_val

            # Try 'reasoning_content' (used by some models like Qwen3.6)
            reasoning_content = message.get('reasoning_content', '') or ''
        elif isinstance(message, str):
            content = message

        # H-3: Check for reasoning dumps
        has_reasoning_dump = _has_reasoning_dump(content) or _has_reasoning_dump(reasoning_content)

        return {
            "content": content or "",
            "reasoning_content": reasoning_content or "",
            "has_reasoning_dump": has_reasoning_dump
        }

    except Exception as e:
        logger.error(f"Error extracting response: {e}")
        return {"content": "", "reasoning_content": "", "has_reasoning_dump": False}


def display_response(result: dict, prefix: str = "") -> None:
    """Display LM Studio response to console.

    Args:
        result: Dict with 'content' and/or 'reasoning_content' keys
        prefix: Optional string prefix for indentation
    """
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


def get_available_models() -> list:
    """Fetch list of available models from LM Studio.

    Returns:
        List of model dicts or empty list on failure
    """
    def fetch_models():
        conn = _LM_STUDIO_CONN_POOL.get_connection(timeout=10)
        try:
            parsed = urllib.parse.urlparse(LM_STUDIO_MODELS_ENDPOINT)
            path = parsed.path
            if parsed.query:
                path += '?' + parsed.query
            conn.request('GET', path, headers={'Accept': 'application/json'})
            resp = conn.getresponse()
            with _stream_http_response(resp) as data:
                models_data = json.loads(data)
                del data  # Explicit cleanup for large JSON payload string
                models_list = models_data.get('models', [])
                del models_data
                gc.collect()
                return models_list
        finally:
            _LM_STUDIO_CONN_POOL.return_connection(conn)

    try:
        return _request_with_retry(fetch_models, max_retries=3, backoff_base=2)
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return []


def get_vision_capable_models() -> list:
    """Get list of LLM models that support vision.

    Returns:
        List of vision-capable model dicts
    """
    models = get_available_models()
    return [m for m in models if m.get('capabilities', {}).get('vision', False)]


def auto_select_model() -> str | None:
    """Auto-select the best available model.

    Prefers loaded vision-capable LLM, then any loaded LLM, then first available.

    Returns:
        Model key string or None
    """
    logger.info("Auto-selecting LM Studio model...")
    models = get_available_models()
    for m in models:
        if m.get('type') == 'llm':
            is_loaded = bool(m.get('loaded_instances'))
            has_vision = m.get('capabilities', {}).get('vision', False)
            if is_loaded and has_vision:
                return m.get('key', '')
            elif has_vision:
                return m.get('key', '')
            elif is_loaded:
                return m.get('key', '')

    # Fallback to default
    return LM_STUDIO_MODEL


def send_to_lmstudio_concurrent(requests_list, max_workers=5, overall_timeout=None):
    """Send multiple prompts/images to LM Studio concurrently using a thread pool.

    Args:
        requests_list: List of dicts with keys: prompt, image_path (optional), model_id (optional),
                       temperature (optional), max_tokens (optional), timeout (optional)
        max_workers: Maximum number of concurrent threads
        overall_timeout: Overall timeout in seconds for all operations. If None, no overall timeout.

    Returns:
        List of results in the same order as input requests_list
    """
    results = [None] * len(requests_list)

    def _send_request(index, req):
        try:
            result = send_to_lmstudio(
                prompt=req.get('prompt', ''),
                image_path=req.get('image_path'),
                model_id=req.get('model_id'),
                temperature=req.get('temperature', 0.3),
                max_tokens=req.get('max_tokens', 1024),
                timeout=req.get('timeout', 120)
            )
            return index, result
        except Exception as e:
            logger.error(f"Error in concurrent request: {e}")
            return index, {"error": str(e)}

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    try:
        futures = [executor.submit(_send_request, i, req) for i, req in enumerate(requests_list)]

        if overall_timeout is not None:
            done, not_done = concurrent.futures.wait(futures, timeout=overall_timeout)
            for future in not_done:
                future.cancel()

            for future in done:
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Error getting concurrent result: {e}")
        else:
            for future in concurrent.futures.as_completed(futures):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Error getting concurrent result: {e}")
    finally:
        executor.shutdown(wait=False)

    return results


async def send_to_lmstudio_async(prompt: str, image_path: str | None = None, model_id: str | None = None, temperature: float = 0.3, max_tokens: int = 1024, timeout: int = 120) -> dict | None:
    """Send a prompt (optionally with an image) to LM Studio for analysis asynchronously.

    Uses asyncio.wait_for to enforce timeout on the synchronous send_to_lmstudio call.
    """
    if not isinstance(prompt, str):
        raise ValidationError("prompt must be a string")
    if image_path is not None and not isinstance(image_path, str):
        raise ValidationError("image_path must be a string or None")
    if model_id is not None and not isinstance(model_id, str):
        raise ValidationError("model_id must be a string or None")
    if not isinstance(temperature, float) or not (0.0 <= temperature <= 1.0):
        raise ValidationError(f"temperature must be a float between 0.0 and 1.0, got {temperature}")
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValidationError(f"max_tokens must be an integer > 0, got {max_tokens}")
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValidationError(f"timeout must be an integer > 0, got {timeout}")
    if model_id is None:
        model_id = LM_STUDIO_MODEL

    # Check LM Studio API health before making requests
    if not check_lm_studio_health(timeout=5):
        error_msg = "LM Studio API is not reachable or healthy. Ensure LM Studio is running and accessible."
        logger.error(error_msg)
        raise ResourceError(error_msg)

    # Enforce rate limiting for LM Studio API calls
    LM_STUDIO_RATE_LIMITER.acquire()

    async with LM_STUDIO_ASYNC_SEMAPHORE:
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    send_to_lmstudio,
                    prompt=prompt,
                    image_path=image_path,
                    model_id=model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                ),
                timeout=timeout
            )
            if result is not None and 'error' not in result:
                logger.info("Successfully received response from LM Studio API")
            return result
        except asyncio.TimeoutError:
            error_msg = f"LM Studio request timed out after {timeout} seconds."
            logger.error(error_msg)
            raise ResourceError(error_msg)
        except Exception:
            raise


# ---------------------------------------------------------------------------
# Enhanced LLM Integration Methods
# ---------------------------------------------------------------------------

def send_to_lmstudio_with_history(
    conversation_manager: ChatConversationManager,
    image_path: str | None = None,
    model_id: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    timeout: int = 120,
) -> dict | None:
    """Send a request using the conversation manager's full message history.

    Appends user messages to history, sends them all to LM Studio, then
    records the assistant response back into the conversation.

    Args:
        conversation_manager: ChatConversationManager instance with accumulated history
        image_path: Optional path to an image file
        model_id: Model ID override
        temperature: Sampling temperature
        max_tokens: Max tokens in response
        timeout: Request timeout in seconds

    Returns:
        Response dict or None on failure
    """
    messages = conversation_manager.get_messages()

    # Build the payload with full history
    def build_payload():
        if image_path and Path(image_path).exists():
            try:
                mime_type = get_image_mime_type(image_path)
                with open(image_path, "rb") as f:
                    image_b64 = base64.b64encode(f.read()).decode('utf-8')

                last_msg = messages[-1] if messages else None
                if last_msg and last_msg.get("role") == "user":
                    content = last_msg["content"]
                    # Append image to the last user message
                    new_content = [
                        {"type": "text", "text": content},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
                    ]
                    messages_copy = list(messages)
                    messages_copy[-1] = {"role": "user", "content": new_content}
                else:
                    image_msg = [{"type": "text", "text": f"Image attached: {image_path}"}]
                    image_msg.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}})
                    messages_copy = list(messages) + [{"role": "user", "content": image_msg}]
            except Exception:
                messages_copy = list(messages)
        else:
            messages_copy = list(messages)

        return {
            "model": model_id or LM_STUDIO_MODEL,
            "messages": messages_copy,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    payload = build_payload()

    def send_chat_request():
        request_data = json.dumps(payload).encode('utf-8')
        conn = _LM_STUDIO_CONN_POOL.get_connection(timeout=timeout)
        invalidate_conn = False
        response = None
        try:
            parsed = urllib.parse.urlparse(LM_STUDIO_CHAT_COMPLETIONS_ENDPOINT)
            path = parsed.path
            if parsed.query:
                path += '?' + parsed.query
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            conn.request('POST', path, body=request_data, headers=headers)
            response = conn.getresponse()

            if response.status == 200:
                with _stream_http_response(response) as resp_data:
                    result = json.loads(resp_data)
                    del resp_data
                    extracted = _extract_response(result)
                    del result
                    return extracted
            else:
                error_text = response.read().decode('utf-8')
                logger.error(f"LM Studio API error: {response.status} - {error_text}")
                if response.status in (502, 503, 504):
                    invalidate_conn = True
                    raise LmStudioApiError(f"LM Studio API error: {response.status} - {error_text}", response.status)
                raise LmStudioApiError(f"LM Studio API error: {response.status} - {error_text}", response.status)
        finally:
            try:
                if response is not None:
                    response.close()
            except Exception:
                pass
            if invalidate_conn:
                _LM_STUDIO_CONN_POOL.invalidate_connection(conn)
            else:
                _LM_STUDIO_CONN_POOL.return_connection(conn)

    try:
        result = _request_with_retry(send_chat_request, max_retries=3, backoff_base=2)
        if result is not None and 'error' not in result:
            # Record assistant response in conversation history
            assistant_content = result.get("content", "")
            conversation_manager.add_assistant_message(assistant_content)

            logger.info("Successfully received response from LM Studio API")
        return result
    except urllib.error.HTTPError as e:
        error_msg = f"LM Studio HTTP error: {e.code} - {e.reason}. Check LM Studio logs for details."
        logger.error(error_msg)
        raise LmStudioApiError(error_msg, e.code)
    except urllib.error.URLError as e:
        error_msg = f"Failed to connect to LM Studio (URL Error): {e.reason}. Ensure LM Studio is running and accessible at {LM_STUDIO_BASE_URL}."
        logger.error(error_msg)
        raise NetworkError(error_msg)
    except Exception as e:
        error_msg = f"Failed to send analysis request to LM Studio: {e}. Check that LM Studio is running and the model '{model_id or LM_STUDIO_MODEL}' is loaded."
        logger.error(error_msg)
        raise ResourceError(error_msg)


def generate_code_from_prompt(
    prompt: str,
    language: str = "cpp",
    system_template: str | None = None,
    model_id: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    timeout: int = 180,
) -> dict | None:
    """Generate C++ or Blueprint code snippets based on the prompt and MCP tool definitions.

    Uses a system prompt tailored for code generation to produce higher-quality output.
    Supports both C++ (.cpp/.h) and Unreal Blueprint (event graph / component hierarchy).

    Args:
        prompt: Description of the code to generate
        language: "cpp" or "blueprint" — target language
        system_template: Optional custom system prompt override
        model_id: Model ID override
        temperature: Lower for more deterministic code output
        max_tokens: Max tokens in response (higher for complex code)
        timeout: Request timeout in seconds

    Returns:
        Dict with keys: 'language', 'code' (str), 'explanation' (str), 'filename_hint' (str)
        or None on failure.
    """
    if language not in ("cpp", "blueprint"):
        raise ValidationError(f"language must be 'cpp' or 'blueprint', got '{language}'")

    # Build system prompt for code generation
    if system_template:
        system_prompt = system_template
    else:
        if language == "cpp":
            system_prompt = (
                "You are an expert C++ developer specializing in Unreal Engine 5. "
                "Generate production-quality code following UE coding standards. "
                "Include proper includes, UCLASS/USTRUCT annotations, UPROPERTY macros, "
                "and handle memory management correctly. Provide a brief explanation of the implementation."
            )
        else:
            system_prompt = (
                "You are an expert Unreal Engine Blueprint designer. "
                "Describe event graphs, component hierarchies, and property bindings clearly. "
                "Use standard UE naming conventions (CamelCase for Blueprints, bPrefix for booleans). "
                "Provide a textual description of the Blueprint structure that can be used for automation."
            )

    # Build enhanced prompt with language context
    if language == "cpp":
        enhanced_prompt = f"""Generate C++ code based on this request:

{prompt}

Requirements:
- Use Unreal Engine 5 C++ conventions (UCLASS, UPROPERTY, UFUNCTION)
- Include necessary headers (#include)
- Follow UE naming conventions (PascalCase for classes/functions, camelCase for variables)
- Handle nullptr checks and garbage collection considerations
- Provide the code in a single well-formatted block

Return your response as JSON with these fields:
{{"language": "cpp", "code": "...", "explanation": "...", "filename_hint": "..."}}"""
    else:
        enhanced_prompt = f"""Generate Blueprint design based on this request:

{prompt}

Requirements:
- Describe the Blueprint class hierarchy (parent classes, components)
- Detail event graph nodes and execution flow
- Specify property bindings and variable declarations
- Follow UE Blueprint naming conventions

Return your response as JSON with these fields:
{{"language": "blueprint", "code": "...", "explanation": "...", "filename_hint": "..."}}"""

    # Send request to LM Studio
    result = send_to_lmstudio(
        prompt=enhanced_prompt,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    if not result:
        return None

    # Parse structured output
    parsed = parse_structured_output(result)

    if isinstance(parsed, dict):
        code = parsed.get("code", "")
        explanation = parsed.get("explanation", "")
        filename_hint = parsed.get("filename_hint", f"Generated_{language}")

        return {
            "language": language,
            "code": code,
            "explanation": explanation,
            "filename_hint": filename_hint,
            "raw_response": result,
        }

    # Fallback: wrap raw content in expected format
    return {
        "language": language,
        "code": result.get("content", ""),
        "explanation": "",
        "filename_hint": f"Generated_{language}",
        "raw_response": result,
    }


# ---------------------------------------------------------------------------
# Async Enhanced Methods
# ---------------------------------------------------------------------------

async def send_to_lmstudio_with_history_async(
    conversation_manager: ChatConversationManager,
    image_path: str | None = None,
    model_id: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    timeout: int = 120,
) -> dict | None:
    """Async version of send_to_lmstudio_with_history.

    Args:
        conversation_manager: ChatConversationManager instance
        image_path: Optional path to an image file
        model_id: Model ID override
        temperature: Sampling temperature
        max_tokens: Max tokens in response
        timeout: Request timeout in seconds

    Returns:
        Response dict or None on failure
    """
    messages = conversation_manager.get_messages()

    def build_payload():
        if image_path and Path(image_path).exists():
            try:
                mime_type = get_image_mime_type(image_path)
                with open(image_path, "rb") as f:
                    image_b64 = base64.b64encode(f.read()).decode('utf-8')

                last_msg = messages[-1] if messages else None
                if last_msg and last_msg.get("role") == "user":
                    content = last_msg["content"]
                    new_content = [
                        {"type": "text", "text": content},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
                    ]
                    messages_copy = list(messages)
                    messages_copy[-1] = {"role": "user", "content": new_content}
                else:
                    image_msg = [{"type": "text", "text": f"Image attached: {image_path}"}]
                    image_msg.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}})
                    messages_copy = list(messages) + [{"role": "user", "content": image_msg}]
            except Exception:
                messages_copy = list(messages)
        else:
            messages_copy = list(messages)

        return {
            "model": model_id or LM_STUDIO_MODEL,
            "messages": messages_copy,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    payload = build_payload()

    async def send_chat_request():
        request_data = json.dumps(payload).encode('utf-8')
        conn = _LM_STUDIO_CONN_POOL.get_connection(timeout=timeout)
        invalidate_conn = False
        response = None
        try:
            parsed = urllib.parse.urlparse(LM_STUDIO_CHAT_COMPLETIONS_ENDPOINT)
            path = parsed.path
            if parsed.query:
                path += '?' + parsed.query
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            conn.request('POST', path, body=request_data, headers=headers)
            response = conn.getresponse()

            if response.status == 200:
                with _stream_http_response(response) as resp_data:
                    result = json.loads(resp_data)
                    del resp_data
                    extracted = _extract_response(result)
                    del result
                    return extracted
            else:
                error_text = response.read().decode('utf-8')
                logger.error(f"LM Studio API error: {response.status} - {error_text}")
                if response.status in (502, 503, 504):
                    invalidate_conn = True
                    raise LmStudioApiError(f"LM Studio API error: {response.status} - {error_text}", response.status)
                raise LmStudioApiError(f"LM Studio API error: {response.status} - {error_text}", response.status)
        finally:
            try:
                if response is not None:
                    response.close()
            except Exception:
                pass
            if invalidate_conn:
                _LM_STUDIO_CONN_POOL.invalidate_connection(conn)
            else:
                _LM_STUDIO_CONN_POOL.return_connection(conn)

    try:
        result = await asyncio.to_thread(_request_with_retry, send_chat_request, max_retries=3, backoff_base=2)
        if result is not None and 'error' not in result:
            assistant_content = result.get("content", "")
            conversation_manager.add_assistant_message(assistant_content)
            logger.info("Successfully received response from LM Studio API")
        return result
    except asyncio.TimeoutError:
        error_msg = f"LM Studio request timed out after {timeout} seconds."
        logger.error(error_msg)
        raise ResourceError(error_msg)
    except Exception as e:
        raise


def send_to_lmstudio_concurrent(requests_list, max_workers=5, overall_timeout=None):
    """Send multiple prompts/images to LM Studio concurrently using a thread pool.

    Args:
        requests_list: List of dicts with keys: prompt, image_path (optional), model_id (optional),
                       temperature (optional), max_tokens (optional), timeout (optional)
        max_workers: Maximum number of concurrent threads
        overall_timeout: Overall timeout in seconds for all operations. If None, no overall timeout.

    Returns:
        List of results in the same order as input requests_list
    """
    results = [None] * len(requests_list)

    def _send_request(index, req):
        try:
            result = send_to_lmstudio(
                prompt=req.get('prompt', ''),
                image_path=req.get('image_path'),
                model_id=req.get('model_id'),
                temperature=req.get('temperature', 0.3),
                max_tokens=req.get('max_tokens', 1024),
                timeout=req.get('timeout', 120)
            )
            return index, result
        except Exception as e:
            logger.error(f"Error in concurrent request: {e}")
            return index, {"error": str(e)}

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    try:
        futures = [executor.submit(_send_request, i, req) for i, req in enumerate(requests_list)]

        if overall_timeout is not None:
            done, not_done = concurrent.futures.wait(futures, timeout=overall_timeout)
            for future in not_done:
                future.cancel()

            for future in done:
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Error getting concurrent result: {e}")
        else:
            for future in concurrent.futures.as_completed(futures):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Error getting concurrent result: {e}")
    finally:
        executor.shutdown(wait=False)

    return results


async def send_to_lmstudio_async(prompt: str, image_path: str | None = None, model_id: str | None = None, temperature: float = 0.3, max_tokens: int = 1024, timeout: int = 120) -> dict | None:
    """Send a prompt (optionally with an image) to LM Studio for analysis asynchronously.

    Uses asyncio.wait_for to enforce timeout on the synchronous send_to_lmstudio call.
    """
    if not isinstance(prompt, str):
        raise ValidationError("prompt must be a string")
    if image_path is not None and not isinstance(image_path, str):
        raise ValidationError("image_path must be a string or None")
    if model_id is not None and not isinstance(model_id, str):
        raise ValidationError("model_id must be a string or None")
    if not isinstance(temperature, float) or not (0.0 <= temperature <= 1.0):
        raise ValidationError(f"temperature must be a float between 0.0 and 1.0, got {temperature}")
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValidationError(f"max_tokens must be an integer > 0, got {max_tokens}")
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValidationError(f"timeout must be an integer > 0, got {timeout}")
    if model_id is None:
        model_id = LM_STUDIO_MODEL

    # Check LM Studio API health before making requests
    if not check_lm_studio_health(timeout=5):
        error_msg = "LM Studio API is not reachable or healthy. Ensure LM Studio is running and accessible."
        logger.error(error_msg)
        raise ResourceError(error_msg)

    # Enforce rate limiting for LM Studio API calls
    LM_STUDIO_RATE_LIMITER.acquire()

    async with LM_STUDIO_ASYNC_SEMAPHORE:
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    send_to_lmstudio,
                    prompt=prompt,
                    image_path=image_path,
                    model_id=model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                ),
                timeout=timeout
            )
            if result is not None and 'error' not in result:
                logger.info("Successfully received response from LM Studio API")
            return result
        except asyncio.TimeoutError:
            error_msg = f"LM Studio request timed out after {timeout} seconds."
            logger.error(error_msg)
            raise ResourceError(error_msg)
        except Exception:
            raise
