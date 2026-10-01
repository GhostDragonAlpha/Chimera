"""eye.py -- the DYAD JUDGE's watch lane: standing senses first, labeled fallback, honest dark.

THE LADDER (tried in order, the lane that served is recorded on every report):

  1. "senses"   -- ChimeraEngine/senses.py, the project's standing dyad eye.
                   The permanent policy model (dyad_model_policy.json) must be
                   EXPLICITLY LOADED in LM Studio; senses.available() decides.
                   We never load, evict, or reconfigure anything (senses law).
                   Honors the ONE-IMAGE WALL: one image per call, N calls.
  2. "ollama-fallback" -- ONLY when the senses eye is dark. A clearly-labeled
                   direct call to the local Ollama server (default model
                   qwen3.8:latest, think:false, num_ctx sized per frame exactly
                   like senses' own ollama branch). This is NOT the permanent
                   DYAD eye and never pretends to be: every report and every
                   registry entry names the lane that served.
  3. "dark"     -- both down: semantic reads are skipped and recorded as
                   skipped; the pixel read (below) still measures, and the
                   judge's own witnessed description carries the semantics.

THE PIXEL READ is not an eye: it is the measured half of the dyadAnalysis --
mean |frame - baseline| inside the creature box per capture frame, threshold
derived from the pre-press baseline noise (mean + 6 sigma of that window, not
a taste constant), giving dent_visible frames and recovery time.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys_path = str(ROOT / "ChimeraEngine")
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

import senses  # noqa: E402  (the standing dyad perception; policy-enforced)

OLLAMA_URL = os.environ.get("CHIMERA_DYAD_JUDGE_OLLAMA", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("CHIMERA_DYAD_JUDGE_OLLAMA_MODEL", "qwen3.8")
FRAME_TOKENS = 86          # senses' measured per-frame cost at 384px
NUM_PREDICT = 512          # terse reads; a report, not an essay
READ_TIMEOUT = int(os.environ.get("CHIMERA_DYAD_JUDGE_READ_TIMEOUT", "240"))


def eye_status() -> dict:
    """Which lane will serve: senses / ollama-fallback / dark. Probes only."""
    if senses.available():
        return {"lane": "senses", "model": senses.dyad_model(), "reason": None}
    reason = None
    try:
        senses.available()
    except Exception as e:
        reason = f"{type(e).__name__}: {e}"
    # senses.available() swallows its failures; recover the reason for the record.
    try:
        from senses import DyadModelFailure  # noqa: F401
        try:
            senses._enforce_dyad_backend_policy()
            policy = senses._dyad_policy()
            senses._require_policy_model_loaded(policy)
        except Exception as e:
            reason = f"{getattr(e, 'reason', type(e).__name__)}: {e}"
    except Exception:
        pass
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=4) as r:
            tags = json.load(r)
        names = [m.get("name", "") for m in tags.get("models", [])]
        if any(n == OLLAMA_MODEL or n.split(":")[0] == OLLAMA_MODEL for n in names):
            return {"lane": "ollama-fallback", "model": OLLAMA_MODEL,
                    "reason": f"senses eye dark ({reason}); ollama fallback serving"}
        return {"lane": "dark", "model": None,
                "reason": f"senses eye dark ({reason}); ollama up but {OLLAMA_MODEL!r} absent"}
    except Exception as e:
        return {"lane": "dark", "model": None,
                "reason": f"senses eye dark ({reason}); ollama unreachable: {e}"}


def _b64(png: str) -> str:
    with open(png, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _shrink(png: str, workdir: Path, width: int = 768) -> str:
    """Downscale a capture frame for the eye: pixels speak, bytes travel.
    1440x900 captures re-encoded to 768px wide keep the HUD legible and cut the
    payload ~3.5x (same trick as dyad_scan's compact twin)."""
    out = workdir / (Path(png).stem + f"_s{width}.png")
    if out.exists():
        return str(out)
    from PIL import Image
    im = Image.open(png)
    h = round(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(out)
    return str(out)


def read_frame(png: str, prompt: str, status: dict, workdir: Path) -> dict:
    """ONE FRAME, ONE REPORT (the wall honored). Returns
    {report, lane, model, frame, elapsed_s} -- report None when the lane is dark
    or the read failed (recorded, never retried into a hallucinated answer)."""
    if status["lane"] == "dark":
        return {"report": None, "lane": "dark", "model": None, "frame": png,
                "elapsed_s": 0.0, "note": status["reason"]}
    small = _shrink(png, workdir)
    t0 = time.time()
    try:
        if status["lane"] == "senses":
            report = senses.watch_one(small, prompt)   # timeout decreed disabled upstream
            if report is None:
                raise RuntimeError("senses.watch_one returned None (eye failed mid-read)")
            return {"report": report, "lane": "senses", "model": status["model"],
                    "frame": png, "elapsed_s": round(time.time() - t0, 1)}
        # ollama-fallback: senses' own ollama request shape, one image, think:false
        num_ctx = FRAME_TOKENS + NUM_PREDICT + 512
        body = {"model": status["model"],
                "messages": [{"role": "user", "content": prompt, "images": [_b64(small)]}],
                "think": False, "stream": False,
                "options": {"num_ctx": num_ctx, "num_predict": NUM_PREDICT}}
        req = urllib.request.Request(OLLAMA_URL + "/api/chat",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as r:
            report = (json.load(r).get("message") or {}).get("content") or ""
        report = report.strip() or None
        return {"report": report, "lane": "ollama-fallback", "model": status["model"],
                "frame": png, "elapsed_s": round(time.time() - t0, 1)}
    except Exception as e:
        return {"report": None, "lane": status["lane"], "model": status.get("model"),
                "frame": png, "elapsed_s": round(time.time() - t0, 1),
                "error": f"{type(e).__name__}: {e}"}


DEFAULT_PROMPT = (
    "This is one frame from a timed screen recording of someone playing a web page. "
    "Answer tersely, three numbered lines:\n"
    "1. Is the creature/body on screen visibly DEFORMED anywhere (dent, squish, "
    "squashed silhouette) compared with a resting body? yes/no + where.\n"
    "2. Is a press or touch interaction in progress right now (hand/press indicator, "
    "depressed contact)? yes/no.\n"
    "3. What do the visible pressure/HUD numbers read?\n"
    "Do not guess at what the product is; describe only what the frame shows."
)


def pixel_read(frames: list[tuple[str, float]], press: dict, box: tuple[int, int, int, int]) -> dict:
    """The measured read. frames = [(path, t_ms)] in capture order; press =
    {down_ms, up_ms} (wall-clock ms epoch, from the session timeline) or {} when
    no press window was recorded. box = (x0, y0, x1, y1) creature region.

    Baseline = mean of frames strictly before press.down_ms (>=2). Signal m_i =
    mean |gray_i - gray_baseline| in box. Threshold = mean(sigma of baseline
    frames) + 6 * std(sigma of baseline frames) -- derived from the pre-press
    noise, not chosen. dent_visible = held frames with m_i >= threshold.
    recovery_ms = first time after up_ms where m_i < threshold and stays.
    """
    if len(frames) < 3:
        return {"error": "too few frames", "dent_visible_frames": None}
    from PIL import Image

    def gray(path):
        im = Image.open(path).convert("L").crop(box)
        return np.asarray(im, dtype=np.float32) / 255.0

    downs = [f for f, t in frames if press and t < press.get("down_ms", -1)]
    base_set = downs[-3:] if len(downs) >= 2 else [frames[0][0], frames[1][0]]
    base = np.mean([gray(f) for f in base_set], axis=0)
    base_scores = [float(np.mean(np.abs(gray(f) - base))) for f in base_set]
    thr = float(np.mean(base_scores) + 6.0 * np.std(base_scores)) if len(base_set) > 1 \
        else float(np.mean(base_scores) * 3.0)

    per = []
    for f, t in frames:
        m = float(np.mean(np.abs(gray(f) - base)))
        per.append({"frame": Path(f).name, "t_ms": t, "score": round(m, 5),
                    "above": bool(m >= thr)})
    out = {"threshold": round(thr, 5), "baseline_frames": [Path(f).name for f in base_set],
           "per_frame": per}
    if press:
        held = [p for p in per if press["down_ms"] <= p["t_ms"] <= press["up_ms"]]
        out["hold_frames"] = len(held)
        out["dent_visible_frames"] = sum(1 for p in held if p["above"])
        rec = None
        for p in per:
            if p["t_ms"] > press["up_ms"] and not p["above"]:
                rec = p["t_ms"] - press["up_ms"]
                break
        out["recovery_ms"] = rec          # None = never recovered inside the capture
        peak = max((p["score"] for p in held), default=None)
        out["hold_peak_score"] = round(peak, 5) if peak is not None else None
    return out
