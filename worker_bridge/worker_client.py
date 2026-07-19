"""
PI Worker Bridge Client
=======================
HTTP client for controlling a second PI agent via the Worker Bridge.

Usage from main session:
    from worker_client import PiWorker

    worker = PiWorker("http://127.0.0.1:8888")
    resp = worker.prompt("List the files in C:\\")
    print(resp)

    resp = worker.bash("dir /s /b | head -20")
    print(resp)

    state = worker.get_state()
    print(state)

    worker.follow_up("Now do this other thing")
    worker.steer("Stop, redirect")
"""

import json
import time
import urllib.request
import urllib.error
from typing import Optional, Any


class PiWorker:
    """Lightweight HTTP client for the PI Worker Bridge REST API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8888"):
        self.base_url = base_url.rstrip("/")

    # ── low-level ──────────────────────────────────────────────────────

    def _request(self, method: str, path: str, body: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data else {},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code} from {method} {path}: {err_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Connection failed to {url}: {e.reason}")

    def _get(self, path: str) -> dict:
        return self._request("GET", path)

    def _post(self, path: str, body: dict = None) -> dict:
        return self._request("POST", path, body)

    # ── status ────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Check if the worker PI process is alive."""
        return self._get("/api/status")

    def is_alive(self) -> bool:
        try:
            return self.status().get("status") == "running"
        except RuntimeError:
            return False

    # ── prompt / steer / follow_up ────────────────────────────────────

    def prompt(self, message: str, images: list[str] = None) -> dict:
        """Send a prompt to the worker PI agent (fire-and-forget)."""
        body = {"message": message}
        if images:
            body["images"] = images
        return self._post("/api/prompt", body)

    def steer(self, message: str, images: list[str] = None) -> dict:
        """Interrupt the worker PI mid-run with a redirect."""
        body = {"message": message}
        if images:
            body["images"] = images
        return self._post("/api/steer", body)

    def follow_up(self, message: str, images: list[str] = None) -> dict:
        """Queue a follow-up message for after the worker finishes."""
        body = {"message": message}
        if images:
            body["images"] = images
        return self._post("/api/follow_up", body)

    def abort(self) -> dict:
        """Abort the currently running operation."""
        return self._post("/api/abort")

    # ── bash ──────────────────────────────────────────────────────────

    def bash(self, command: str, exclude_from_context: bool = None) -> dict:
        """Execute a bash command in the worker's shell."""
        body = {"command": command}
        if exclude_from_context is not None:
            body["excludeFromContext"] = exclude_from_context
        return self._post("/api/bash", body)

    def abort_bash(self) -> dict:
        return self._post("/api/abort_bash")

    # ── state & session ───────────────────────────────────────────────

    def get_state(self) -> dict:
        return self._get("/api/get_state")

    def get_messages(self) -> dict:
        return self._get("/api/get_messages")

    def get_entries(self, since: str = None) -> dict:
        path = "/api/get_entries"
        if since:
            path += f"?since={since}"
        return self._get(path)

    def get_tree(self) -> dict:
        return self._get("/api/get_tree")

    def get_commands(self) -> dict:
        return self._get("/api/get_commands")

    def get_session_stats(self) -> dict:
        return self._get("/api/get_session_stats")

    # ── model ─────────────────────────────────────────────────────────

    def get_available_models(self) -> dict:
        return self._get("/api/get_available_models")

    def cycle_model(self) -> dict:
        return self._post("/api/cycle_model")

    def set_thinking_level(self, level: str) -> dict:
        return self._post(f"/api/set_thinking_level?level={level}")

    def cycle_thinking_level(self) -> dict:
        return self._post("/api/cycle_thinking_level")

    def compact(self, instructions: str = None) -> dict:
        body = {}
        if instructions:
            body["customInstructions"] = instructions
        return self._post("/api/compact", body)

    # ── convenience ───────────────────────────────────────────────────

    def prompt_and_wait(self, message: str, poll_interval: float = 2.0,
                        timeout: float = 600.0) -> dict:
        """Send a prompt and wait until the agent settles (is_streaming=false)."""
        self.prompt(message)
        deadline = time.time() + timeout
        while time.time() < deadline:
            state = self.get_state()
            if not state.get("data", {}).get("isStreaming", True):
                return state
            time.sleep(poll_interval)
        raise TimeoutError(f"Agent did not settle within {timeout}s")
