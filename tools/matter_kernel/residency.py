"""B5 — the GPU-residency harness (preregistration 67aa80de).

Triangles are weights: membranes load ONCE, stay GPU-resident, compute
happens in place; Python issues intents and exits. Proof: read the
engine's cumulative frame counter, stay SILENT (zero HTTP) for T
seconds, read again. Frames advanced during silence = the engine
renders on its own; a stall or collapse = something needs Python per
frame (the 22 fps incident is the cited precedent).

Instrument: GET /studio_chrome — `pushes` is the cumulative frame
counter (ui.hpp ft_pushes_, incremented once per rendered frame),
`fps` the rolling rate, `ft_avg` the frame-time mean, `rec.calls` /
`rec.draws` the render-recorder liveness. The judge is pure; the
measurement talks to the live engine and counts its own calls.
"""
from __future__ import annotations

import json
import time
import urllib.request

FLOOR_FPS = 100.0     # 5x the 22 fps per-frame-Python incident
BUDGET_MS = 10.0      # 1/100 s, same floor expressed in time


class ResidencyRefused(Exception):
    """A named refusal: the harness never passes on a dead engine."""


def read_chrome(engine_url: str, timeout_s: float = 5.0) -> dict:
    """One GET /studio_chrome. Counts as ONE of the harness's calls."""
    try:
        with urllib.request.urlopen(
                engine_url.rstrip("/") + "/studio_chrome",
                timeout=timeout_s) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        raise ResidencyRefused(f"engine_down: {engine_url} unreachable "
                               f"({e})") from e


def judge(sample_t0: dict, sample_t1: dict, window_s: float) -> dict:
    """Pure judge: two /studio_chrome samples and the silent window.
    The COUNTER is the only clock (amendment 2026-09-13): rate and
    frame-time budget derive from pushes, which is exact and monotonic;
    the served fps/ft_avg fields are smoothed readouts, recorded but
    never judged. Refuses stalled frames or a silent recorder."""
    if window_s is None or not isinstance(window_s, (int, float)) \
            or window_s <= 0:
        raise ResidencyRefused(f"invalid_window: {window_s!r} must be "
                               f"positive seconds")
    for name, s in (("t0", sample_t0), ("t1", sample_t1)):
        for key in ("pushes", "fps", "ft_avg", "rec_calls", "rec_draws"):
            if key not in s:
                raise ResidencyRefused(
                    f"invalid_sample: {name} missing {key!r}")

    frames = sample_t1["pushes"] - sample_t0["pushes"]
    if frames <= 0:
        raise ResidencyRefused(
            f"stalled_frames: counter advanced {frames} during a "
            f"{window_s:.1f} s silent window — nothing rendered without "
            f"Python")
    rec_calls = sample_t1["rec_calls"] - sample_t0["rec_calls"]
    rec_draws = sample_t1["rec_draws"] - sample_t0["rec_draws"]
    if rec_calls <= 0 or rec_draws <= 0:
        raise ResidencyRefused(
            "recorder_stalled: the scene is not being re-drawn — "
            "residency means the resident scene KEEPS drawing")

    fps_counter = frames / window_s
    mean_frame_ms = window_s * 1000.0 / frames
    return {
        "resident": True,
        "frames_advanced": frames,
        "silent_window_s": window_s,
        "fps_counter": fps_counter,
        "fps_floor_ok": fps_counter >= FLOOR_FPS,
        "mean_frame_ms": mean_frame_ms,
        "budget_ok": mean_frame_ms <= BUDGET_MS,
        "reported_fps_t0": sample_t0["fps"],
        "reported_fps_t1": sample_t1["fps"],
        "reported_ft_avg_t0": sample_t0["ft_avg"],
        "reported_ft_avg_t1": sample_t1["ft_avg"],
        "rec_calls": rec_calls,
        "rec_draws": rec_draws,
        "derived_frames_min": FLOOR_FPS * window_s,
    }


def measure(engine_url: str, window_s: float = 10.0) -> dict:
    """The full honest window: read, SILENCE (zero HTTP), read.
    Exactly 2 calls — the harness proves its own silence."""
    t0 = read_chrome(engine_url)
    time.sleep(window_s)  # TOTAL SILENCE: no HTTP, no intents, nothing
    t1 = read_chrome(engine_url)
    out = judge(_flatten(t0), _flatten(t1), window_s)
    out["http_calls_made"] = 2
    out["engine_url"] = engine_url
    return out


def _flatten(s: dict) -> dict:
    rec = s.get("rec") or {}
    return {"pushes": s.get("pushes"), "fps": s.get("fps"),
            "ft_avg": s.get("ft_avg"),
            "rec_calls": rec.get("calls"), "rec_draws": rec.get("draws")}


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8107"
    window = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    print(json.dumps(measure(url, window), indent=1))
