"""Reusable LM Studio client (OpenAI-compatible /v1/chat/completions).

LM Studio exposes an OpenAI-style API at http://localhost:1234/v1. This client
is the only place that talks to the network; the dyad harness stays pure.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable


DEFAULT_BASE = "http://localhost:1234/v1"
DEFAULT_MODEL = "qwen3.8-27b-nvfp4-mtp"


@dataclass
class Message:
    role: str
    content: str

    def as_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Agent:
    """A single persona talking to LM Studio. system_prompt defines its role."""

    name: str
    system_prompt: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE
    temperature: float = 0.7
    max_tokens: int = 1024

    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def reply(self, history: list[Message]) -> str:
        """Send the full conversation history + this agent's system prompt and
        return the assistant's text reply."""
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}]
            + [m.as_dict() for m in history],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._endpoint(),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()


def chat(
    system: str,
    history: Iterable[Message],
    *,
    name: str = "agent",
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """One-shot convenience wrapper."""
    return Agent(name, system, model=model, base_url=base_url, temperature=temperature, max_tokens=max_tokens).reply(list(history))
