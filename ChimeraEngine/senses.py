"""senses.py -- the DYAD's PERCEPTION (eye + ear + movie).

VISION + TEXT ride on **LM STUDIO'S RESIDENT MODEL** by operator decree (2026-08-26): "Vision
Judge should be set to whatever the current model is loaded in LM Studio" -- adopted, never
pinned, routed through core/lm_gateway's fair queue (the single-endpoint law), which raises
NoModelLoaded when nothing is resident -> the eye is DARK -> a FAIL, never a skip. Requests go
over the OpenAI-compatible /v1/chat/completions as base64 data-URL image parts; context budget
is the server's own (60,672 at time of update), so no num_ctx math here. Set
CHIMERA_VISION_BACKEND=ollama to restore the retired qwen3.8 path (kept verbatim below).

AUDIO (the sound dyad) still needs the Omni model on the dedicated llama-server; when that
server is down the ear is DARK -- an advisory FAIL, never a block (sound is additive).

THE ONE-IMAGE WALL (2026-08-31, operator): the eye is whatever LM Studio has resident.
The current resident is `qwen3.8-27b-nvfp4-mtp` -- a fast VLM with 60,672 context.
A movie inlined as twelve 384px frames does not fit, and the failure is not a clean error:
it is a truncated read that looks like a verdict. The operator's rule: **one picture per
report.** N frames means N calls and N reports, aggregated afterwards.

So the wall is enforced HERE, in code, instead of living as a thing to remember. It is an
env-tunable ceiling rather than a hard-coded 1, because the model is ADOPTED, never pinned:
when a resident model has room for a batch, raise CHIMERA_SENSES_MAX_IMAGES and the lane
obeys. The ollama lane keeps sizing num_ctx to the frames it is given (that is what
FRAME_TOKENS is for), so it is exempt.

BUDGET (2026-09-02, operator): "no prompt to it will have more than 60,000 tokens in one
shot but you should try to fill up as much of that 60,000 as you can" -- the eye's answer
cap is 60,000 tokens. The model is VERY FAST with this quant, so elaborate, detailed
analysis is feasible. Truncation at 60k is a LOST answer.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.request
from pathlib import Path

# VISION / TEXT backend selection -- LM Studio resident model is the decree default.
VISION_BACKEND = os.environ.get("CHIMERA_VISION_BACKEND", "lmstudio").strip().lower()
VISION_URL = os.environ.get("CHIMERA_VISION_URL", "http://localhost:11434")      # ollama lane
VISION_MODEL = os.environ.get("CHIMERA_VISION_MODEL", "qwen3.8")                 # ollama lane
LMSTUDIO_URL = os.environ.get("CHIMERA_LMSTUDIO_URL", "http://localhost:1234")   # decree lane

# AUDIO backend -- the dedicated llama-server (the Omni model) for the ear only.
AUDIO_URL = os.environ.get("CHIMERA_SENSES_URL", "http://127.0.0.1:1235")

# The eye's answer budget. qwen3.8-27b-nvfp4-mtp is a REASONING model with a 60,672-token
# context window. The operator wants elaborate answers: fill as much of the 60k budget
# as possible. We cap at 60,000 tokens. This is the speed lever: more tokens = longer answer = more time.
# The model is VERY FAST with this quant, so the trade-off favors quality.
#
# Previous budget was 2,600 (qwen3.8-flash-next era). The new model has 23x more
# context, and the operator wants every token used. Truncation at 60k is a LOST
# answer -- the eye was cut off mid-thought.
MAX_TOKENS = int(os.environ.get("CHIMERA_SENSES_MAX_TOKENS", "60000"))

# Measured vision-token cost of one frame at 384px (prompt_eval_count delta): 86 tokens. The
# context is sized EXACTLY to the frames + answer, so a 256K model is not hauled into VRAM for a
# movie. Re-measure if you change the frame resolution (see `_post`). (Ollama lane only.)
FRAME_TOKENS = int(os.environ.get("CHIMERA_SENSES_FRAME_TOKENS", "86"))

# ── THE EYE IS NAMED AND HARD-CODED (operator decree 2026-09-02) ─────────────
#   CHIMERA SENSES MODEL = qwen3.8-27b-nvfp4-mtp   context 60,672 (operator)
#
# THE CONTEXT IS THE OPERATOR'S CALL, NOT OURS TO MANAGE. They set it — loaded
# by them, in LM Studio, at load time (a request cannot change it; the context
# is fixed when the model is loaded). We record what the server reports and never
# push a num_ctx at it: LM Studio owns the loaded context, and overriding it can
# trigger a reload, which is the eviction war core/lm_gateway exists to prevent.
#
# For the record, so the next agent does not re-derive it: the context is the
# dominant cost of a read. Loaded at 60,672, one 2560x1440 frame takes ~30-60s
# on this fast quant. A frame that size is ~3,771 prompt tokens (measured), the
# briefing is ~1,500 tokens, and the question ~500 tokens, so ~5,800 is what is
# actually needed as INPUT. The remaining ~55,000 tokens are the eye's answer
# budget — fill it with elaborate, detailed analysis.
#
# `type: vlm` is the whole ballgame — the model MUST accept images.
# qwen3.8-27b-nvfp4-mtp is a VLM (vision-language model) that accepts images
# and has a 60,672-token context. The operator chose it for speed + quality.
#
# The ceiling is the SERVER'S OWN reported loaded context (60,672), not a guess.
# It is a budget, not a licence: the one-image-per-call wall (MAX_IMAGES_PER_CALL)
# stays, because a report is ABOUT one picture — batching frames would make the
# eye describe a sequence instead of judging a frame. The headroom is there if
# a future decree wants it.
SENSES_MODEL = os.environ.get("CHIMERA_SENSES_MODEL", "qwen3.8-27b-nvfp4-mtp")

# 2026-09-03, operator decree (revised after the wrong-model incident): the dyad
# FOLLOWS THE OPERATOR'S LOADED MODEL. Precedence:
#   1. Saved/dyad_model.txt        — an EXPLICIT pin (one model id), only for
#                                    controlled A/B comparisons. Read fresh
#                                    every call. "auto"/blank = not pinned.
#   2. AUTO-FOLLOW (the default):  whatever vision model the operator has LOADED
#                                    in LM Studio right now (/api/v0/models,
#                                    state=="loaded", type vlm). The operator
#                                    loads GSQ RCO -> the dyad is GSQ RCO. They
#                                    load nvfp4-mtp -> the dyad follows. The dyad
#                                    NEVER asks the server to load or evict.
#   3. default (nvfp4-mtp)         — only reachable when nothing is loaded (the
#                                    on-demand path; eye_control refuses to load
#                                    over a resident model, so this cannot evict).
# Every identity change is logged once (the identity law: reports from different
# eyes are not comparable, so the change itself must be on the record).
_DYAD_MODEL_FILE = Path(__file__).resolve().parent.parent / "Saved" / "dyad_model.txt"
_ACTIVE_MODEL = SENSES_MODEL

def _pinned_model() -> str | None:
    """The explicit pin, if any. "auto"/blank/missing = not pinned."""
    try:
        if _DYAD_MODEL_FILE.exists():
            txt = _DYAD_MODEL_FILE.read_text(encoding="utf-8").strip()
            if txt and txt.lower() != "auto":
                return txt
    except OSError:
        pass
    return None

def _loaded_vlm() -> str | None:
    """The operator's loaded vision model, if any. Pure read; never loads."""
    try:
        with urllib.request.urlopen(LMSTUDIO_URL + "/api/v0/models", timeout=4) as r:
            models = json.load(r).get("data", [])
    except Exception:
        return None
    for m in models:
        if m.get("state") == "loaded" and m.get("type") == "vlm":
            return m.get("id")
    return None

def dyad_model() -> str:
    """The dyad's current eye: pin > loaded > default. Fresh every call."""
    global _ACTIVE_MODEL
    m = _pinned_model() or _loaded_vlm() or SENSES_MODEL
    if m != _ACTIVE_MODEL:
        print(f"[senses] dyad model switch: {_ACTIVE_MODEL} -> {m}", flush=True)
        _ACTIVE_MODEL = m
    return m

def set_dyad_model(name: str) -> None:
    """Write the pin ("" or "auto" = follow the loaded model). Verified against
    LM Studio's served list when reachable — a typo'd id is a silently dark eye."""
    _DYAD_MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    name = (name or "auto").strip()
    _DYAD_MODEL_FILE.write_text(name + "\n", encoding="utf-8")
    if name not in ("", "auto"):
        try:
            with urllib.request.urlopen(LMSTUDIO_URL + "/v1/models", timeout=3) as r:
                served = [m.get("id") for m in json.load(r).get("data", [])]
            if served and name not in served:
                print(f"[senses] WARNING: '{name}' not in LM Studio's served list: {served}", flush=True)
        except Exception:
            pass  # server down: the write stands; _post will name the miss
    print(f"[senses] dyad pin set to: {name or 'auto (follow the loaded model)'}", flush=True)
SENSES_CTX   = int(os.environ.get("CHIMERA_SENSES_CTX", "60672"))

# A MINIMAL 8x8 PNG, inlined. Not for reading — for the capability probe: the
# smallest possible image that still proves the resident model ACCEPTS an image
# at all. See can_see().
_PROBE_PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGMUERFhwAaYsIoOWgkA"
                  "NXAATOBnBRAAAAAASUVORK5CYII=")
# The resident model (qwen3.8-27b-nvfp4-mtp) has 60,672 context tokens. A movie
# inlined as twelve 384px frames does not fit, and the failure is not a clean
# error: it is a truncated read that looks like a verdict. 0 = no ceiling (use
# only when you know the resident model has the room). The ollama lane sizes
# num_ctx instead (see _post).
MAX_IMAGES_PER_CALL = int(os.environ.get("CHIMERA_SENSES_MAX_IMAGES", "1"))


def _lm_gateway():
    """Load the canonical gateway BY PATH -- immune to the dual-core shadowing: lm_gateway
    exists only under Chimera/core since A3 phase 1, and this module must import cleanly in
    non-wired processes too (spec_from_file_location binds no `core` package)."""
    import importlib.util
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "Chimera" / "core" / "lm_gateway.py"
    spec = importlib.util.spec_from_file_location("chimera_lm_gateway", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def available(timeout: float = 3.0) -> bool:
    """Is the vision backend up? Decree default probes LM Studio's resident-model list;
    the ollama lane keeps its old probe."""
    try:
        if VISION_BACKEND == "ollama":
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=timeout) as r:
                return getattr(r, "status", 200) == 200
        with urllib.request.urlopen(LMSTUDIO_URL + "/v1/models", timeout=timeout) as r:
            models = json.load(r).get("data", [])
            return len(models) > 0                      # a resident model = an open eye
    except Exception:
        return False


def can_see(timeout: int = 60):
    """Can the eye that will ACTUALLY SERVE take an image?

    `available()` only asks "is a model listed?", which is not the same question.
    A model can be on disk, answer text perfectly, and refuse every image — and
    when that happens a dyad run does not fail fast, it fails after however long
    it took to build and encode the frame. So: send the smallest image that is
    still an image, and let the server answer. LM Studio says so in one line:

      "The provided messages contain images, but <model> does not support image
       inputs."

    WHICH MODEL THIS TESTS — read this before trusting it: Chimera/core/lm_gateway
    ADOPTS THE RESIDENT model and rewrites every outgoing body at it
    (ADOPT_RESIDENT), deliberately, so two clients on one GPU cannot evict each
    other. So naming a model does not select it. This probe therefore reports on
    the model that is RESIDENT — which is exactly the one that will serve, i.e.
    the one that matters. `served` below is read back from the response, not
    assumed, so a decree that is not actually loaded is visible instead of silent.

    Returns (True, served_id, None) if the eye sees, else (False, served_id, reason).
    A dyad whose eye cannot see is not a dyad — it is a monad with a delay.
    """
    if not available(timeout=min(timeout, 10)):
        return False, None, "no model is resident (the eye is dark)"
    served = None
    reason = None
    # TRY MORE THAN ONCE. A 400 here is not proof of blindness: swapping the
    # resident model while a call is in flight makes LM Studio answer 400 with
    # "Engine protocol startup was aborted", and lm_gateway's own docstring says
    # to ride that out rather than fail the turn. Failing the first 400 cost a
    # whole scan on a perfectly good eye.
    #
    # But a refusal that NAMES the capability is final — retrying it would just
    # wait longer to learn the same thing.
    for attempt in range(3):
        try:
            raw = _post([{"type": "text", "text": "Reply with the single word: seen."},
                         {"type": "image_url",
                          "image_url": {"url": "data:image/png;base64," + _PROBE_PNG_B64}}],
                        timeout)
            served = _last_served_model()
            if not raw:
                reason = "the eye answered nothing"
                break
            return True, served, None
        except Exception as e:
            msg = str(e)
            if hasattr(e, "read"):                   # HTTPError carries the real reason
                try:
                    body = json.loads(e.read().decode("utf-8", "replace"))
                    msg = str(body.get("error", {}).get("message") or msg)
                except Exception:
                    pass
            reason = msg
            served = served or _last_served_model()
            if "does not support image" in msg or "image input" in msg:
                break                                # final: the eye genuinely cannot see
            if attempt < 2:
                time.sleep(5.0 * (attempt + 1))      # mid-handover; ride it out
    return False, served, reason


def resident_model(timeout: float = 8.0):
    """The model id RESIDENT in memory — the one the gateway will serve.
    /api/v0/models is the only surface that distinguishes loaded from on-disk.
    Returns None when it cannot be determined (and the caller must say so)."""
    try:
        with urllib.request.urlopen(LMSTUDIO_URL + "/api/v0/models", timeout=timeout) as r:
            payload = json.load(r)
        for m in payload.get("data", []):
            if m.get("state") == "loaded" or m.get("status") == "loaded":
                return m.get("id")
        ids = [m.get("id") for m in payload.get("data", [])]
        return ids[0] if ids else None
    except Exception:
        return None


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _count_images(content) -> int:
    if not isinstance(content, list):
        return 0
    return sum(1 for p in content
               if isinstance(p, dict) and p.get("type") == "image_url")


def _enforce_image_wall(content) -> None:
    """THE ONE-IMAGE WALL, raised before the request goes out.

    The resident model is ADOPTED, never pinned, so this is a ceiling that can be
    raised (CHIMERA_SENSES_MAX_IMAGES) rather than a hard ban -- but the default
    is 1, and a breach is an ERROR rather than a silent truncation. A movie that
    quietly loses its last eight frames still returns a confident-sounding
    verdict, which is the one failure mode an instrument must not have.

    Callers wanting a movie must loop: one call per frame, N reports, aggregated
    afterwards (see tools/dyad_scan.py's READS_PER_SHOT).
    """
    if MAX_IMAGES_PER_CALL <= 0:
        return
    n = _count_images(content)
    if n > MAX_IMAGES_PER_CALL:
        raise ValueError(
            f"senses: {n} images in one call, ceiling is {MAX_IMAGES_PER_CALL} "
            f"(CHIMERA_SENSES_MAX_IMAGES). The resident model's context cannot hold a "
            f"batch and would truncate silently -- loop one frame per call instead "
            f"(watch_one / see) and aggregate the reports.")


def _post(content, timeout: int, temperature: float = 0.2, max_tokens: int = MAX_TOKENS,
          endpoint: str = VISION_URL, model: str = VISION_MODEL):
    if VISION_BACKEND != "ollama":
        _enforce_image_wall(content)
        return _post_lmstudio(content, timeout, temperature, max_tokens)
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


def _post_lmstudio(content, timeout: int, temperature: float, max_tokens: int = MAX_TOKENS):
    """THE DECREE LANE: LM Studio's RESIDENT model over /v1/chat/completions, through the
    fair-queue gateway (single endpoint law; adopt-never-pin; NoModelLoaded = eye dark).
    Images pass as base64 data URLs -- the OpenAI parts format needs no reassembly here."""
    gw = _lm_gateway()
# max_tokens IS SENT HERE. The budget is 60,000 tokens — filling as much of
# the 60,672 context as possible. The model is fast (nvfp4 quant), so longer
# answers are feasible. Truncation at 60k is a LOST answer.
#
# num_ctx is deliberately NOT sent: LM Studio owns the loaded context
# (60,672, reported by /api/v0/models), and pushing a num_ctx at it can
# trigger a reload -- which is the eviction war core/lm_gateway exists to
# prevent. We cap what the eye may SAY, never what it may SEE.
    body = {"model": dyad_model(),    # named per call: override file > env > default.
                                     # A dyad whose eye changes identity between
                                     # readings produces reports that cannot be
                                     # compared, and comparison is the instrument.
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "temperature": temperature, "stream": False}
    req = urllib.request.Request(LMSTUDIO_URL + "/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    # timeout=None (decree: disabled) passes through untouched — urlopen waits forever
    resp = gw.lm_urlopen(req, timeout=timeout if timeout is None else max(timeout, 600),
                         agent="senses")
    payload = json.loads(resp.read())
    global _SERVED, _FINISH
    try:
        _SERVED = payload.get("model") or _SERVED
        choice = (payload.get("choices") or [{}])[0]
        _FINISH = choice.get("finish_reason") or _FINISH
    except Exception:
        pass
    return payload["choices"][0]["message"].get("content") or ""


_SERVED: str | None = None
_FINISH: str | None = None


def _last_served_model():
    """The model id from the most recent response — what actually served."""
    return _SERVED


def last_finish_reason():
    """Why the eye stopped talking.

    THIS IS THE TRUNCATION TELL. `finish_reason == "length"` means the report was
    cut off by max_tokens — mid-sentence, usually mid-word. A truncated report is
    a LOST report, and filing one as if it were complete is exactly the silent
    success this project exists to kill.    With the 60k budget, truncation is rare
    but still possible on very elaborate answers.
    """
    return _FINISH


# TIMEOUT DISABLED (operator decree 2026-09-02): "the model is very very slow so
# you have to wait a long long time and timeout should be disabled I will decide
# if we need to start over." A read waits FOREVER; the operator owns restarts.
# The legacy `timeout` arguments are accepted and ignored so no caller breaks.
READ_TIMEOUT_DISABLED = None


def ensure_eye() -> bool:
    """Light the eye WITHOUT touching the operator's loaded models. Laws:
    - the resolved eye (dyad_model()) already loaded -> True.
    - a DIFFERENT model is resident -> NEVER load (lms load can evict the
      operator's choice — measured 2026-09-03). Report honestly, stay dark.
    - NOTHING is resident -> load the resolved eye (the documented on-demand
      decree); nothing can be evicted because nothing is loaded."""
    try:
        import eye_control
        want = dyad_model()
        st = eye_control.status(want)          # the RESOLVED eye's state, not the default's
        if st.get("eye_state") == "loaded":
            return True
        resident = st.get("loaded") or []
        if resident:
            print(f"[senses] eye '{want}' is dark but {resident} is resident — "
                  f"NOT auto-loading (eviction risk). Load '{want}' yourself or "
                  f"clear the pin to follow the loaded model.", flush=True)
            return False
        print(f"[senses] eye dark, nothing resident — loading {want} on demand "
              f"(unbounded wait; the operator decides when to start over) ...", flush=True)
        r = eye_control.load(model=want)
        return bool(r.get("ok"))
    except Exception as e:
        print(f"[senses] ensure_eye FAILED: {e}")
        return False


def see(png: str, prompt: str, timeout: int = 300) -> str | None:
    """EYE: the resident model reads one image -> a term. None if the eye is dark.
    The timeout argument is accepted for compatibility and IGNORED (decree:
    timeouts disabled — the wait is unbounded; the operator decides about restarts)."""
    ensure_eye()
    try:
        return (_post([{"type": "text", "text": prompt},
                       {"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(png)}}],
                      READ_TIMEOUT_DISABLED) or "").strip() or None
    except ValueError:
        raise                      # the one-image wall: a guard that cannot be heard is not a guard
    except Exception as e:
        print(f"[senses] see FAILED: {e}")
        return None


def watch_one(png: str, prompt: str, timeout: int = 300) -> str | None:
    """ONE FRAME, ONE REPORT. The eye reads a single image -> a term. None if dark.
    Timeout argument ignored (decree: disabled)."""
    return see(png, prompt)


def watch(frames: list[str], prompt: str, timeout: int = 360) -> str | None:
    """MOVIE: an ORDERED sequence of frames read as video -> a term describing the
    unfolding. None if dark. Timeout ignored (decree: disabled)."""
    ensure_eye()
    try:
        content = [{"type": "text", "text": prompt}]
        for p in frames:
            content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(p)}})
        return (_post(content, READ_TIMEOUT_DISABLED) or "").strip() or None
    except ValueError:
        raise                      # the one-image wall: see above
    except Exception as e:
        print(f"[senses] watch FAILED: {e}")
        return None


def read_movie(frames: list[str], prompt: str, timeout: int = 300) -> list:
    """A movie the resident eye can actually read: ONE CALL PER FRAME, N reports back.

    [(frame_path, report_or_None), ...] in order. Nothing is aggregated and nothing is
    judged here -- aggregation is a decision about evidence (see tools/dyad_scan.py), and
    an instrument should hand back what it measured.

    This is the operator's rule made literal: "you can't give it more than one picture
    per report". 24 shots is 24 calls, and that is the cost of the eye being fast.
    """
    out = []
    for p in frames:
        out.append((p, watch_one(p, prompt, timeout=timeout)))
    return out


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
