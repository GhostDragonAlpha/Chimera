"""senses.py -- the DYAD's PERCEPTION (eye + ear + movie).

VISION + TEXT use the checked-in permanent DYAD policy. The operator's 2026-09-10
selection supersedes the older auto-follow rule for the DYAD only. Requests still
use core/lm_gateway's fair queue, but this module's freshly loaded private gateway
instance may not retarget the policy's exact model id. The intended id must already
be loaded; this module never loads, evicts, or reconfigures it.

AUDIO (the sound dyad) still needs the Omni model on the dedicated llama-server; when that
server is down the ear is DARK -- an advisory FAIL, never a block (sound is additive).

THE ONE-IMAGE WALL (2026-08-31, operator) remains: one picture per report.
The permanent eye is `qwen3.8-27b-nvfp4-mtp`; its loaded context is configured
by the operator and is not changed here.
A movie inlined as twelve 384px frames does not fit, and the failure is not a clean error:
it is a truncated read that looks like a verdict. The operator's rule: **one picture per
report.** N frames means N calls and N reports, aggregated afterwards.

So the wall is enforced HERE, in code, instead of living as a thing to remember. Its
historical environment control remains for compatibility; the default is one image.

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

import dyad_log   # every report lands in Saved/dyad/dyad_log.jsonl (operator decree 2026-09-03)

# VISION / TEXT backend selection is fixed for the DYAD. Environment variables
# may still configure the endpoint, but may not silently bypass model policy.
VISION_BACKEND = "lmstudio"
VISION_URL = os.environ.get("CHIMERA_VISION_URL", "http://localhost:11434")      # ollama lane
VISION_MODEL = os.environ.get("CHIMERA_VISION_MODEL", "qwen3.8")                 # ollama lane
LMSTUDIO_URL = os.environ.get("CHIMERA_LMSTUDIO_URL", "http://localhost:1234")   # decree lane

# AUDIO backend -- the dedicated llama-server (the Omni model) for the ear only.
AUDIO_URL = os.environ.get("CHIMERA_SENSES_URL", "http://127.0.0.1:1235")

# The historical answer request cap remains unchanged in this policy-only patch.
# LM Studio's loaded context is operator-owned (observed as 30,208 on
# 2026-09-10); senses does not load or reconfigure it.
#
# Previous budget was 2,600 (qwen3.8-flash-next era). The new model has 23x more
# context, and the operator wants every token used. Truncation at 60k is a LOST
# answer -- the eye was cut off mid-thought.
MAX_TOKENS = int(os.environ.get("CHIMERA_SENSES_MAX_TOKENS", "60000"))

# Measured vision-token cost of one frame at 384px (prompt_eval_count delta): 86 tokens. The
# context is sized EXACTLY to the frames + answer, so a 256K model is not hauled into VRAM for a
# movie. Re-measure if you change the frame resolution (see `_post`). (Ollama lane only.)
FRAME_TOKENS = int(os.environ.get("CHIMERA_SENSES_FRAME_TOKENS", "86"))

# ── THE EYE IS NAMED BY CHECKED-IN POLICY (operator decree 2026-09-10) ───────
#
# THE CONTEXT IS THE OPERATOR'S CALL, NOT OURS TO MANAGE. They set it — loaded
# by them, in LM Studio, at load time (a request cannot change it; the context
# is fixed when the model is loaded). We record what the server reports and never
# push a num_ctx at it: LM Studio owns the loaded context, and overriding it can
# trigger a reload, which is the eviction war core/lm_gateway exists to prevent.
#
# `type: vlm` is the whole ballgame — the model MUST accept images.
# The selected qwen3.8 id must accept images; can_see measures that separately.
SENSES_MODEL = "qwen3.8-27b-nvfp4-mtp"  # compatibility name; policy is authoritative
_DYAD_POLICY_FILE = Path(__file__).with_name("dyad_model_policy.json")
_ACTIVE_MODEL: str | None = None


class DyadModelFailure(RuntimeError):
    """Named failure of the permanent DYAD identity contract."""

    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason


class DyadModelReason:
    POLICY_MISSING = "dyad_model_policy_missing"
    POLICY_INVALID = "dyad_model_policy_invalid"
    POLICY_PERMANENT = "dyad_model_policy_permanent"
    BACKEND_FORBIDDEN = "dyad_backend_forbidden"
    MODEL_LIST_UNAVAILABLE = "dyad_loaded_model_list_unavailable"
    REQUIRED_MODEL_NOT_LOADED = "dyad_required_model_not_loaded"
    RESPONSE_MODEL_MISSING = "dyad_response_model_missing"
    RESPONSE_MODEL_WRONG = "dyad_response_model_wrong"


def _dyad_policy() -> dict:
    """Read and validate the checked-in policy afresh for every DYAD call."""
    try:
        payload = json.loads(_DYAD_POLICY_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise DyadModelFailure(
            DyadModelReason.POLICY_MISSING,
            f"permanent DYAD policy missing: {_DYAD_POLICY_FILE}",
        ) from e
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        raise DyadModelFailure(
            DyadModelReason.POLICY_INVALID,
            f"cannot read permanent DYAD policy {_DYAD_POLICY_FILE}: {e}",
        ) from e
    if not isinstance(payload, dict):
        raise DyadModelFailure(
            DyadModelReason.POLICY_INVALID, "permanent DYAD policy must be a JSON object"
        )
    required = {
        "schema": "chimera-dyad-model-policy-v1",
        "mode": "fixed",
    }
    for field, expected in required.items():
        if payload.get(field) != expected:
            raise DyadModelFailure(
                DyadModelReason.POLICY_INVALID,
                f"permanent DYAD policy {field!r} must equal {expected!r}",
            )
    for field in ("model_id", "model_relative_path"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise DyadModelFailure(
                DyadModelReason.POLICY_INVALID,
                f"permanent DYAD policy requires non-empty {field!r}",
            )
    return payload


def _enforce_dyad_backend_policy() -> None:
    requested = os.environ.get("CHIMERA_VISION_BACKEND", "lmstudio").strip().lower()
    if requested not in ("", "lmstudio"):
        raise DyadModelFailure(
            DyadModelReason.BACKEND_FORBIDDEN,
            f"permanent DYAD policy requires LM Studio; backend {requested!r} is forbidden",
        )


def _loaded_model_ids(timeout: float = 4.0) -> list[str]:
    """Return only explicitly loaded ids; never fall back to on-disk entries."""
    try:
        with urllib.request.urlopen(LMSTUDIO_URL + "/api/v0/models", timeout=timeout) as r:
            payload = json.load(r)
    except Exception as e:
        raise DyadModelFailure(
            DyadModelReason.MODEL_LIST_UNAVAILABLE,
            f"cannot verify loaded DYAD model through /api/v0/models: {e}",
        ) from e
    if not isinstance(payload, dict) or not isinstance(payload.get("data", []), list):
        raise DyadModelFailure(
            DyadModelReason.MODEL_LIST_UNAVAILABLE,
            "LM Studio /api/v0/models returned a malformed model list",
        )
    loaded = []
    for record in payload.get("data", []):
        if not isinstance(record, dict):
            continue
        if record.get("state") == "loaded" or record.get("status") == "loaded":
            model_id = record.get("id")
            if isinstance(model_id, str) and model_id and model_id not in loaded:
                loaded.append(model_id)
    return loaded


def _require_policy_model_loaded(policy: dict, timeout: float = 4.0) -> str:
    intended = policy["model_id"]
    loaded = _loaded_model_ids(timeout=timeout)
    if intended not in loaded:
        raise DyadModelFailure(
            DyadModelReason.REQUIRED_MODEL_NOT_LOADED,
            f"permanent DYAD model {intended!r} is not explicitly loaded; loaded={loaded!r}",
        )
    return intended


def dyad_model() -> str:
    """Return the permanent checked-in model id, read fresh every call."""
    global _ACTIVE_MODEL
    model_id = _dyad_policy()["model_id"]
    if model_id != _ACTIVE_MODEL:
        print(f"[senses] permanent dyad model: {model_id}", flush=True)
        _ACTIVE_MODEL = model_id
    return model_id


def set_dyad_model(name: str) -> None:
    """Refuse runtime alternatives; policy changes require an operator-owned code change."""
    intended = dyad_model()
    if (name or "").strip() != intended:
        raise DyadModelFailure(
            DyadModelReason.POLICY_PERMANENT,
            f"DYAD model is permanently {intended!r}; runtime pin/auto overrides are disabled",
        )
    print(f"[senses] permanent dyad model already set: {intended}", flush=True)
# Legacy compatibility value. It is not sent to LM Studio and does not describe
# or alter the operator-owned loaded context.
SENSES_CTX = int(os.environ.get("CHIMERA_SENSES_CTX", "60672"))

# A MINIMAL 8x8 PNG, inlined. Not for reading — for the capability probe: the
# smallest possible image that still proves the resident model ACCEPTS an image
# at all. See can_see().
_PROBE_PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGMUERFhwAaYsIoOWgkA"
                  "NXAATOBnBRAAAAAASUVORK5CYII=")
# The one-image ceiling is independent of the operator-owned loaded context.
# A breach is a refusal rather than a silently truncated multi-image report.
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
    """Is the permanent DYAD model explicitly loaded?"""
    try:
        _enforce_dyad_backend_policy()
        policy = _dyad_policy()
        return _require_policy_model_loaded(policy, timeout=timeout) == policy["model_id"]
    except DyadModelFailure:
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

    WHICH MODEL THIS TESTS — read this before trusting it: the checked-in DYAD
    policy names the exact model. The probe first requires that id to be explicitly
    loaded, disables resident retargeting on its private fair-gateway instance, and
    verifies the response's served id. A different resident therefore cannot turn
    into silent evidence for the permanent eye.

    Returns (True, served_id, None) if the eye sees, else (False, served_id, reason).
    A dyad whose eye cannot see is not a dyad — it is a monad with a delay.
    """
    try:
        _enforce_dyad_backend_policy()
        _require_policy_model_loaded(_dyad_policy(), timeout=min(timeout, 10))
    except DyadModelFailure as e:
        return False, None, f"{e.reason}: {e}"
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
    """The single model id RESIDENT in memory, when it is unambiguous.
    /api/v0/models is the only surface that distinguishes loaded from on-disk.
    Returns None for zero, multiple, malformed, or unreachable loaded records;
    it never promotes an on-disk id to resident status."""
    try:
        loaded = _loaded_model_ids(timeout=timeout)
        return loaded[0] if len(loaded) == 1 else None
    except DyadModelFailure:
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

    The historical CHIMERA_SENSES_MAX_IMAGES control remains, but the default is
    1 and a breach is an ERROR rather than a silent truncation. A movie that
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


def _clear_response_identity() -> None:
    global _SERVED, _FINISH
    _SERVED = None
    _FINISH = None


def _post(content, timeout: int, temperature: float = 0.2, max_tokens: int = MAX_TOKENS,
          endpoint: str = VISION_URL, model: str = VISION_MODEL):
    _clear_response_identity()
    _enforce_dyad_backend_policy()
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
    """Call the permanent, already-loaded DYAD model through the fair gateway."""
    # A failed new call must never inherit identity/completion proof from an old one.
    _clear_response_identity()
    policy = _dyad_policy()
    intended = _require_policy_model_loaded(policy)
    gw = _lm_gateway()
    # _lm_gateway() loads a private module instance on every call. Disable its
    # auto-retarget only for this DYAD request; other text clients retain the
    # canonical gateway's resident-adoption policy.
    gw.ADOPT_RESIDENT = False
    # max_tokens is sent unchanged from the historical DYAD protocol. This patch
    # does not alter LM Studio's operator-owned loaded context.
    #
    # num_ctx is deliberately NOT sent: LM Studio owns the loaded context, and
    # pushing one at it can trigger a reload.
    body = {"model": intended,
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
    served = payload.get("model") if isinstance(payload, dict) else None
    if not isinstance(served, str) or not served:
        raise DyadModelFailure(
            DyadModelReason.RESPONSE_MODEL_MISSING,
            "LM Studio response omitted the served model id",
        )
    if served != intended:
        raise DyadModelFailure(
            DyadModelReason.RESPONSE_MODEL_WRONG,
            f"permanent DYAD requested {intended!r} but response reports {served!r}",
        )
    try:
        choice = payload["choices"][0]
        answer = choice["message"].get("content") or ""
        finish = choice.get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError) as e:
        raise DyadModelFailure(
            DyadModelReason.RESPONSE_MODEL_MISSING,
            "LM Studio response omitted the DYAD answer envelope",
        ) from e
    global _SERVED, _FINISH
    _SERVED = served
    _FINISH = finish
    return answer


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
    success this project exists to kill. Truncation remains possible and is
    always retained in the report identity.
    """
    return _FINISH


# TIMEOUT DISABLED (operator decree 2026-09-02): "the model is very very slow so
# you have to wait a long long time and timeout should be disabled I will decide
# if we need to start over." A read waits FOREVER; the operator owns restarts.
# The legacy `timeout` arguments are accepted and ignored so no caller breaks.
READ_TIMEOUT_DISABLED = None


def ensure_eye() -> bool:
    """Verify the permanent DYAD model is loaded; never load or reconfigure it."""
    try:
        _enforce_dyad_backend_policy()
        policy = _dyad_policy()
        _require_policy_model_loaded(policy)
        return True
    except DyadModelFailure as e:
        print(f"[senses] ensure_eye FAILED [{e.reason}]: {e}")
        return False


def see(png: str, prompt: str, timeout: int = 300) -> str | None:
    """EYE: the resident model reads one image -> a term. None if the eye is dark.
    The timeout argument is accepted for compatibility and IGNORED (decree:
    timeouts disabled — the wait is unbounded; the operator decides about restarts)."""
    ensure_eye()
    t0 = time.time()
    try:
        out = (_post([{"type": "text", "text": prompt},
                      {"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(png)}}],
                     READ_TIMEOUT_DISABLED) or "").strip() or None
        dyad_log.append("see", model=dyad_model(), served=_last_served_model(),
                        prompt_chars=len(prompt or ""), n_images=1, image=png,
                        report=out, elapsed_s=time.time() - t0,
                        finish_reason=last_finish_reason())
        return out
    except ValueError:
        dyad_log.append("see", model=dyad_model(), prompt_chars=len(prompt or ""),
                        n_images=1, image=png, error="one-image wall breach",
                        elapsed_s=time.time() - t0)
        raise                      # the one-image wall: a guard that cannot be heard is not a guard
    except Exception as e:
        dyad_log.append("see", model=dyad_model(), prompt_chars=len(prompt or ""),
                        n_images=1, image=png, error=f"{type(e).__name__}: {e}",
                        elapsed_s=time.time() - t0)
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
    t0 = time.time()
    try:
        content = [{"type": "text", "text": prompt}]
        for p in frames:
            content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(p)}})
        out = (_post(content, READ_TIMEOUT_DISABLED) or "").strip() or None
        dyad_log.append("watch", model=dyad_model(), served=_last_served_model(),
                        prompt_chars=len(prompt or ""), n_images=len(frames),
                        image=(frames[0] if frames else ""), report=out,
                        elapsed_s=time.time() - t0, finish_reason=last_finish_reason())
        return out
    except ValueError:
        dyad_log.append("watch", model=dyad_model(), prompt_chars=len(prompt or ""),
                        n_images=len(frames), image=(frames[0] if frames else ""),
                        error="one-image wall breach", elapsed_s=time.time() - t0)
        raise                      # the one-image wall: see above
    except Exception as e:
        dyad_log.append("watch", model=dyad_model(), prompt_chars=len(prompt or ""),
                        n_images=len(frames), image=(frames[0] if frames else ""),
                        error=f"{type(e).__name__}: {e}", elapsed_s=time.time() - t0)
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
    t0 = time.time()
    try:
        body = {"messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "input_audio", "input_audio": {"data": _b64(wav), "format": "wav"}}]}],
                "temperature": 0.2}
        req = urllib.request.Request(AUDIO_URL + "/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = (json.load(r)["choices"][0]["message"].get("content") or "").strip() or None
        dyad_log.append("hear", model="omni(ear)", prompt_chars=len(prompt or ""),
                        image=wav, report=out, elapsed_s=time.time() - t0)
        return out
    except Exception as e:
        dyad_log.append("hear", model="omni(ear)", prompt_chars=len(prompt or ""),
                        image=wav, error=f"{type(e).__name__}: {e}",
                        elapsed_s=time.time() - t0)
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
