"""senses.py -- the DYAD's PERCEPTION: one Omni model (eye + ear + movie) on a dedicated llama-server.

Both messengers perceive through here: `human_messenger` (vision) and `sound_messenger` (audio). One Omni
model -- `qwen2.5-omni`, served by llama-server -- SEES images, HEARS audio, and WATCHES ordered frame
sequences (video). One model, every sense; the operator's LM Studio is left free for their own dev agent.

Endpoint: the DEDICATED llama-server (127.0.0.1:1235 by default; `CHIMERA_SENSES_URL` overrides), NOT LM
Studio. This server is ours alone, so there is no gateway queue. Server down = the sense is DARK = a FAIL --
the same honest outcome the operator's rules demand for a dark eye. LM Studio can't feed audio to an omni
model (it wires the mmproj for vision only); llama-server's `init_audio` does -- which is why the senses
live here. Launch: `ChimeraEngine/serve_senses.*` (omni GGUF on GPU + mmproj on CPU).
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request

SENSES_URL = os.environ.get("CHIMERA_SENSES_URL", "http://127.0.0.1:1235")
# The eye's token budget. qwen2.5-omni-7b answers inside 512; a REASONING vision model
# (qwen-agentworld-35b) spends its budget on `reasoning_content` first and returns an EMPTY
# `content` when the budget runs out -- the eye reads nothing and the dyad fails dark. 4096
# gives the reasoning tower room to finish AND answer; override per setup.
MAX_TOKENS = int(os.environ.get("CHIMERA_SENSES_MAX_TOKENS", "8192"))


def available(timeout: float = 3.0) -> bool:
    """Is the senses server up? (A dark server is a FAIL, not an error to swallow.)"""
    try:
        with urllib.request.urlopen(f"{SENSES_URL}/health", timeout=timeout) as r:
            return getattr(r, "status", 200) == 200
    except Exception:
        return False


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _post(content, timeout: int, temperature: float = 0.2, max_tokens: int = MAX_TOKENS):
    body = {"messages": [{"role": "user", "content": content}],
            "temperature": temperature, "max_tokens": max_tokens}
    req = urllib.request.Request(f"{SENSES_URL}/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def see(png: str, prompt: str, timeout: int = 300) -> str | None:
    """EYE: the omni model reads one image -> a term. None if the eye is dark (server down / error)."""
    try:
        return (_post([{"type": "text", "text": prompt},
                       {"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(png)}}],
                      timeout) or "").strip() or None
    except Exception as e:
        print(f"[senses] see FAILED: {e}")
        return None


def watch(frames: list[str], prompt: str, timeout: int = 360) -> str | None:
    """MOVIE: the omni model reads an ORDERED sequence of frames as video -> a term describing the unfolding.
    None if dark. (This is what lets the appearance dyad judge the MOVIE, not just the end still.)"""
    try:
        content = [{"type": "text", "text": prompt}]
        for p in frames:
            content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(p)}})
        return (_post(content, timeout) or "").strip() or None
    except Exception as e:
        print(f"[senses] watch FAILED: {e}")
        return None


def hear(wav: str, prompt: str, timeout: int = 300) -> str | None:
    """EAR: the omni model listens to audio -> a term. None if the ear is dark. ADVISORY quality
    (llama.cpp audio is 'experimental') -- the operator is the authoritative ear."""
    try:
        return (_post([{"type": "text", "text": prompt},
                       {"type": "input_audio", "input_audio": {"data": _b64(wav), "format": "wav"}}],
                      timeout) or "").strip() or None
    except Exception as e:
        print(f"[senses] hear FAILED: {e}")
        return None


def _parse01(text: str):
    for tok in re.findall(r"\d+(?:\.\d+)?", text or ""):
        v = float(tok)
        if 0.0 <= v <= 1.0:
            return v
    return None


def align(expected: str, observed: str, timeout: int = 240):
    """The cross-reference (works for any sense): score how well the observed reading matches the physics's
    expected reading, 0.0 -> 1.0. Returns None on failure. Generic wording so vision AND audio both use it."""
    prompt = (f"A physics model predicts an observation should be:\n  \"{expected}\"\n\n"
              f"An independent observer, who did NOT see that prediction, described it as:\n  \"{observed}\"\n\n"
              f"Rate how well the observer's description ALIGNS with the physics prediction, as a single number "
              f"from 0.0 (no alignment) to 1.0 (perfect alignment). Output ONLY the number.")
    try:
        return _parse01(_post([{"type": "text", "text": prompt}], timeout, temperature=0.1))
    except Exception as e:
        print(f"[senses] align FAILED: {e}")
        return None
