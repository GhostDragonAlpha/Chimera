"""senses.py -- the DYAD's PERCEPTION (eye + ear + movie).

VISION + TEXT (the appearance dyad) ride on **Ollama's qwen3.8** -- already installed, the same
model the engine's `judge.py` uses. Images go over the OpenAI-compatible endpoint as base64 data
URLs. AUDIO (the sound dyad) still needs the Omni model on the dedicated llama-server; when that
server is down the ear is DARK -- an advisory FAIL, never a block (sound is additive).

The operator's rule stands unchanged: no vision model resident -> the eye is DARK -> a FAIL, never
a skip. `available()` probes the vision backend (Ollama), which is what gates the appearance dyad.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request

# VISION / TEXT backend -- Ollama's qwen3.8 (installed; the engine judge's model too).
VISION_URL = os.environ.get("CHIMERA_VISION_URL", "http://localhost:11434")
VISION_MODEL = os.environ.get("CHIMERA_VISION_MODEL", "qwen3.8")

# AUDIO backend -- the dedicated llama-server (the Omni model) for the ear only.
AUDIO_URL = os.environ.get("CHIMERA_SENSES_URL", "http://127.0.0.1:1235")

# The eye's answer budget. qwen3.8 is a REASONING model: with `think` on it burns the whole budget
# on `reasoning_content` and returns EMPTY `content`. We run it with thinking DISABLED (`think:false`)
# so the answer comes straight out -- then a small budget is plenty.
MAX_TOKENS = int(os.environ.get("CHIMERA_SENSES_MAX_TOKENS", "2048"))

# Measured vision-token cost of one frame at 384px (prompt_eval_count delta): 86 tokens. The
# context is sized EXACTLY to the frames + answer, so a 256K model is not hauled into VRAM for a
# movie. Re-measure if you change the frame resolution (see `_post`).
FRAME_TOKENS = int(os.environ.get("CHIMERA_SENSES_FRAME_TOKENS", "86"))


def available(timeout: float = 3.0) -> bool:
    """Is the vision backend up? (Ollama serving qwen3.8 -- the eye that gates the dyad.)"""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=timeout) as r:
            return getattr(r, "status", 200) == 200
    except Exception:
        return False


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _post(content, timeout: int, temperature: float = 0.2, max_tokens: int = MAX_TOKENS,
          endpoint: str = VISION_URL, model: str = VISION_MODEL):
    # content arrives as OpenAI-style parts (text + image_url). The native Ollama /api/chat wants
    # `content` as a string and `images` as a list of raw base64 (no data: prefix).
    text = ""
    images = []
    for p in content:
        if isinstance(p, dict) and p.get("type") == "text":
            text += p.get("text", "")
        elif isinstance(p, dict) and p.get("type") == "image_url":
            url = p["image_url"]["url"]
            images.append(url.split(",", 1)[1] if url.startswith("data:") else url)

    # Load the model with ONLY the context we need: num_ctx = frame tokens + answer + margin.
    # thinking disabled -> direct answer (no reasoning_content tower).
    num_ctx = max(4096, len(images) * FRAME_TOKENS + max_tokens + 512)
    body = {"model": model,
            "messages": [{"role": "user", "content": text, "images": images}],
            "think": False, "stream": False,
            "temperature": temperature,
            "options": {"num_ctx": num_ctx, "num_predict": max_tokens}}
    req = urllib.request.Request(endpoint + "/api/chat",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        msg = json.load(r)["message"]
        return msg.get("content") or ""


def see(png: str, prompt: str, timeout: int = 300) -> str | None:
    """EYE: qwen3.8 reads one image -> a term. None if the eye is dark (Ollama down / error)."""
    try:
        return (_post([{"type": "text", "text": prompt},
                       {"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(png)}}],
                      timeout) or "").strip() or None
    except Exception as e:
        print(f"[senses] see FAILED: {e}")
        return None


def watch(frames: list[str], prompt: str, timeout: int = 360) -> str | None:
    """MOVIE: qwen3.8 reads an ORDERED sequence of frames as video -> a term describing the
    unfolding. None if dark. (This is what lets the appearance dyad judge the MOVIE, not just the
    end still.)"""
    try:
        content = [{"type": "text", "text": prompt}]
        for p in frames:
            content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(p)}})
        return (_post(content, timeout) or "").strip() or None
    except Exception as e:
        print(f"[senses] watch FAILED: {e}")
        return None


def hear(wav: str, prompt: str, timeout: int = 300) -> str | None:
    """EAR: the Omni model on the dedicated llama-server listens to audio -> a term. None if the
    ear is dark. ADVISORY quality (llama.cpp audio is 'experimental') -- the operator is the
    authoritative ear. Requires the audio backend (llama-server) -- qwen3.8 cannot hear."""
    try:
        body = {"messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "input_audio", "input_audio": {"data": _b64(wav), "format": "wav"}}]}],
                "temperature": 0.2}
        req = urllib.request.Request(AUDIO_URL + "/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (json.load(r)["choices"][0]["message"].get("content") or "").strip() or None
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
    """The cross-reference (works for any sense): score how well the observed reading matches the
    physics's expected reading, 0.0 -> 1.0. Returns None on failure. Generic wording so vision AND
    audio both use it."""
    prompt = (f"A physics model predicts an observation should be:\n  \"{expected}\"\n\n"
              f"An independent observer, who did NOT see that prediction, described it as:\n  \"{observed}\"\n\n"
              f"Rate how well the observer's description ALIGNS with the physics prediction, as a single number "
              f"from 0.0 (no alignment) to 1.0 (perfect alignment). Output ONLY the number.")
    try:
        return _parse01(_post([{"type": "text", "text": prompt}], timeout, temperature=0.1))
    except Exception as e:
        print(f"[senses] align FAILED: {e}")
        return None
