"""senses.py -- the DYAD's PERCEPTION (eye + ear + movie).

VISION + TEXT ride on **LM STUDIO'S RESIDENT MODEL** by operator decree (2026-08-26): "Vision
Judge should be set to whatever the current model is loaded in LM Studio" -- adopted, never
pinned, routed through core/lm_gateway's fair queue (the single-endpoint law), which raises
NoModelLoaded when nothing is resident -> the eye is DARK -> a FAIL, never a skip. Requests go
over the OpenAI-compatible /v1/chat/completions as base64 data-URL image parts; context budget
is the server's own (68k at time of decree), so no num_ctx math here. Set
CHIMERA_VISION_BACKEND=ollama to restore the retired qwen3.8 path (kept verbatim below).

AUDIO (the sound dyad) still needs the Omni model on the dedicated llama-server; when that
server is down the ear is DARK -- an advisory FAIL, never a block (sound is additive).

THE ONE-IMAGE WALL (2026-08-31, operator): the eye is whatever LM Studio has resident, and
what is resident today is `dirk-qwen3.8-27b@iq4_xs` -- chosen because it fits in the GPU and
is therefore fast, and it pays for that with a SMALL context (~74k). A movie inlined as twelve
384px frames does not fit, and the failure is not a clean error: it is a truncated read that
looks like a verdict. The operator's rule: **one picture per report.** N frames means N calls
and N reports, aggregated afterwards.

So the wall is enforced HERE, in code, instead of living as a thing to remember. It is an
env-tunable ceiling rather than a hard-coded 1, because the model is ADOPTED, never pinned:
when a resident model has room for a batch, raise CHIMERA_SENSES_MAX_IMAGES and the lane
obeys. The ollama lane keeps sizing num_ctx to the frames it is given (that is what
FRAME_TOKENS is for), so it is exempt.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.request

# VISION / TEXT backend selection -- LM Studio resident model is the decree default.
VISION_BACKEND = os.environ.get("CHIMERA_VISION_BACKEND", "lmstudio").strip().lower()
VISION_URL = os.environ.get("CHIMERA_VISION_URL", "http://localhost:11434")      # ollama lane
VISION_MODEL = os.environ.get("CHIMERA_VISION_MODEL", "qwen3.8")                 # ollama lane
LMSTUDIO_URL = os.environ.get("CHIMERA_LMSTUDIO_URL", "http://localhost:1234")   # decree lane

# AUDIO backend -- the dedicated llama-server (the Omni model) for the ear only.
AUDIO_URL = os.environ.get("CHIMERA_SENSES_URL", "http://127.0.0.1:1235")

# The eye's answer budget. qwen3.8 is a REASONING model: with `think` on it burns the whole budget
# on `reasoning_content` and returns EMPTY `content`. We run it with thinking DISABLED (`think:false`)
# so the answer comes straight out -- then a small budget is plenty.
#
# THIS IS ALSO THE SPEED LEVER (2026-08-31). MAX_TOKENS was only ever sent on the
# OLLAMA lane; the LM Studio lane -- the one this studio actually runs -- sent no
# cap at all, so the server defaulted and the model was free to keep going. A
# 2560x1440 read was taking 480-500s. Asking for only the tokens a report needs
# is the difference: the report is ~1.1k tokens of prose, and every token past
# that is the eye talking itself into a longer answer nobody asked for.
MAX_TOKENS = int(os.environ.get("CHIMERA_SENSES_MAX_TOKENS", "1400"))

# Measured vision-token cost of one frame at 384px (prompt_eval_count delta): 86 tokens. The
# context is sized EXACTLY to the frames + answer, so a 256K model is not hauled into VRAM for a
# movie. Re-measure if you change the frame resolution (see `_post`). (Ollama lane only.)
FRAME_TOKENS = int(os.environ.get("CHIMERA_SENSES_FRAME_TOKENS", "86"))

# ── THE EYE IS NAMED AND HARD-CODED (operator decree 2026-08-31) ─────────────
#   CHIMERA SENSES MODEL = dirk-qwen3.8-27b        context ~16,000 (operator)
#
# THE CONTEXT IS THE OPERATOR'S CALL, NOT OURS TO MANAGE. They set it — "let's
# make 16,000 the standard size because I can fit all that on GPU" — and it is
# loaded by them, in LM Studio, at load time (a request cannot change it; the
# context is fixed when the model is loaded). We record what the server reports
# and never push a num_ctx at it: LM Studio owns the loaded context, and
# overriding it can trigger a reload, which is the eviction war
# core/lm_gateway exists to prevent.
#
# For the record, so the next agent does not re-derive it: the context is the
# dominant cost of a read. Loaded at 130,048, one 2560x1440 frame took 483s. The
# same frame at ~16,000 takes 56s. A frame that size is 3,771 prompt tokens
# (measured), a report is ~1,400, so ~5,200 is what is actually needed; 16,000
# is the operator's headroom, and it fits on their GPU. Slower or faster is
# theirs to choose — the instrument just reports what it saw.
# `type: vlm` is the whole ballgame — the previous candidate
# (qwen3.8-flash-next-reap-320) is `type: llm` and refuses images outright:
#   "The provided messages contain images, but qwen3.8-flash-next-reap-320 does
#    not support image inputs."
# A faster or stronger model is irrelevant to a dyad that cannot see.
#
# The ceiling is the SERVER'S OWN reported loaded context, not a guess and not the
# 75,000 of the earlier iq4_xs quant. It is a budget, not a licence: the
# one-image-per-call wall (MAX_IMAGES_PER_CALL) stays, because a report is ABOUT
# one picture — batching frames would make the eye describe a sequence instead of
# judging a frame. The headroom is there if a future decree wants it.
SENSES_MODEL = os.environ.get("CHIMERA_SENSES_MODEL", "dirk-qwen3.8-27b")
SENSES_CTX   = int(os.environ.get("CHIMERA_SENSES_CTX", "130048"))

# A MINIMAL 8x8 PNG, inlined. Not for reading — for the capability probe: the
# smallest possible image that still proves the resident model ACCEPTS an image
# at all. See can_see().
_PROBE_PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGMUERFhwAaYsIoOWgkA"
                  "NXAATOBnBRAAAAAASUVORK5CYII=")
# because the resident model's context is unknown to us and today's resident model
# (qwen3.8 iq4_xs, chosen to fit the GPU) has ~74k -- a 12-frame movie inlined into one request
# does not fit, and it fails by truncation rather than by error. 0 = no ceiling (use only when
# you know the resident model has the room). The ollama lane sizes num_ctx instead (see _post).
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
    # max_tokens IS SENT HERE. The budget existed but was only ever honoured on
    # the retired ollama lane, so the lane that actually runs had no ceiling and
    # the eye took 8 minutes to say what fits in 1.4k tokens.
    #
    # num_ctx is deliberately NOT sent: LM Studio owns the loaded context
    # (130,048, reported by /api/v0/models), and pushing a num_ctx at it can
    # trigger a reload -- which is the eviction war core/lm_gateway exists to
    # prevent. We cap what the eye may SAY, never what it may SEE.
    body = {"model": SENSES_MODEL,   # NAMED, not "resident" — see the decree above.
                                     # A dyad whose eye changes identity between
                                     # readings produces reports that cannot be
                                     # compared, and comparison is the instrument.
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "temperature": temperature, "stream": False}
    req = urllib.request.Request(LMSTUDIO_URL + "/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = gw.lm_urlopen(req, timeout=max(timeout, 600), agent="senses")
    payload = json.loads(resp.read())
    # Which model ACTUALLY served. Not assumed, not the one we asked for: the
    # gateway adopts the resident model, so the decree and the server can differ,
    # and a report is only comparable to another report from the same eye.
    global _SERVED
    try:
        _SERVED = payload.get("model") or _SERVED
    except Exception:
        pass
    return payload["choices"][0]["message"].get("content") or ""


_SERVED: str | None = None


def _last_served_model():
    """The model id from the most recent response — what actually served."""
    return _SERVED


def see(png: str, prompt: str, timeout: int = 300) -> str | None:
    """EYE: the resident model reads one image -> a term. None if the eye is dark."""
    try:
        return (_post([{"type": "text", "text": prompt},
                       {"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(png)}}],
                      timeout) or "").strip() or None
    except ValueError:
        raise                      # the one-image wall: a guard that cannot be heard is not a guard
    except Exception as e:
        print(f"[senses] see FAILED: {e}")
        return None


def watch_one(png: str, prompt: str, timeout: int = 300) -> str | None:
    """ONE FRAME, ONE REPORT. The eye reads a single image -> a term. None if dark.

    This is the shape the resident model can actually hold (see MAX_IMAGES_PER_CALL).
    Every harness in this repo used to fake it with `watch([one_path])`; it now has a
    name, because a movie is N of these and the difference between "a movie" and "one
    frame" is the difference between reading and confirming.
    """
    return see(png, prompt, timeout=timeout)


def watch(frames: list[str], prompt: str, timeout: int = 360) -> str | None:
    """MOVIE: an ORDERED sequence of frames read as video -> a term describing the
    unfolding. None if dark.

    On the adoptive (LM Studio) lane this RAISES when `frames` is longer than the
    per-call image ceiling: the frames would be inlined into one request and silently
    truncated. Loop with watch_one()/see() and aggregate the reports instead. The
    ollama lane still sizes num_ctx to the whole list, so it accepts a batch.
    """
    try:
        content = [{"type": "text", "text": prompt}]
        for p in frames:
            content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(p)}})
        return (_post(content, timeout) or "").strip() or None
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
