"""analyze.py -- offline analysis for the thin-client pilot (no eyeballs).

Per browser run:
  1. twin alignment: estimate the scenario-trigger phase offset delta (B's
     timeline lags A's) by grid-searching the shift that minimizes the RMSE
     between the client engine's root_y series and the twin truth's root_y.
  2. phase classification on the client's render points (LAUNCH / DESCENT /
     LANDING / CARRY / PRE_PRESS / PRESS_RECOVERY / PRE-FALL idle).
  3. replay: render each sampled client frame vs the twin truth at the same
     render point through the page's own shader text; MAD per sample.
  4. aggregate per phase + per run; save stills for the worst sample.
  5. frame-time table from the rAF log (the F4 budget: p95 <= 16.7 ms).
  6. press-event visible latency from the snapshot stream (R13).

Usage: python analyze.py --dir .tmp/suite [--runs name,name] [--stills]
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

import replay_runner as rr

BUDGET_MAD = 2.0          # BUDGET-VIS (prereg)
BUDGET_FRAME_MS = 16.7    # BUDGET-RT  (prereg)


def load_truth_frames(path: Path) -> list[dict]:
    return rr.load_truth(str(path))


def truth_root_y_at(frames: list[dict], ts_us: int) -> float | None:
    lo = hi = None
    for f in frames:
        if f["ts"] <= ts_us:
            lo = f
        if f["ts"] > ts_us:
            hi = f
            break
    if lo is None and hi is None:
        return None
    if lo is None:
        return hi["root_y"]
    if hi is None or hi["ts"] == lo["ts"]:
        return lo["root_y"]
    a = (ts_us - lo["ts"]) / (hi["ts"] - lo["ts"])
    return (1 - a) * lo["root_y"] + a * hi["root_y"]


def estimate_shift(snaps: list[dict], frames: list[dict],
                   span_ms: int = 80) -> tuple[int, float]:
    """grid-search shift (us) with B sampled at ts - shift minimizing RMSE
    against A's root_y series. Positive shift = B lags A."""
    ts = np.array([s["ts"] for s in snaps], dtype=np.int64)
    ry = np.array([s["root_y"] for s in snaps], dtype=np.float64)
    # use the MOVING part when possible (largest variance window is the fall)
    best = (0, float("inf"))
    for shift_us in range(-span_ms * 1000, span_ms * 1000 + 1, 500):
        vals = []
        for t, y in zip(ts[::7], ry[::7]):
            v = truth_root_y_at(frames, int(t) - shift_us)
            if v is not None:
                vals.append((v - y) * (v - y))
        if len(vals) < 10:
            continue
        rmse = (sum(vals) / len(vals)) ** 0.5
        if rmse < best[1]:
            best = (shift_us, rmse)
    return best


def classify_fall(frames: list[dict], shift: int, r: int) -> str:
    """phase of a render point, from the truth's own root curve."""
    y = truth_root_y_at(frames, r - shift)
    if y is None:
        return "NO-TRUTH"
    return y  # numeric; the caller buckets


def fall_phase_of(y: float, peak: float) -> str:
    if y > 0.9 * peak:
        return "LAUNCH"
    if y >= 0.05:
        return "DESCENT"
    return "LANDING"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--runs", default=None)
    ap.add_argument("--stills", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir)
    suite = json.loads((d / "suite_summary.json").read_text(encoding="utf-8"))
    topo = (d / "topology.bin").read_bytes()
    names = a.runs.split(",") if a.runs else list(suite["runs"].keys())

    visual: dict = {}
    timing: dict = {}
    for name in names:
        cfg = suite["runs"][name]
        dump = json.loads((d / f"dump_{name}.json").read_text(encoding="utf-8"))
        raf = dump["raf"]
        if not raf:
            continue
        # ── frame time (instrumentation; client clock drives the stopwatch) ──
        dts = [(raf[i + 1]["t"] - raf[i]["t"]) for i in range(len(raf) - 1)]
        dts.sort()
        long_frames = sum(1 for x in dts if x > 25.0)
        timing[name] = {"n_frames": len(dts),
                        "median_ms": round(dts[len(dts) // 2], 2),
                        "p95_ms": round(dts[int(0.95 * len(dts))], 2),
                        "p99_ms": round(dts[int(0.99 * len(dts))], 2),
                        "max_ms": round(dts[-1], 1),
                        "long_frames_gt25ms": long_frames,
                        "trace": cfg["trace"], "rate": cfg["rate_nominal"]}
        if cfg["scenario"] == "PRESS" and cfg.get("press"):
            # ── press-event visible latency (server-timeline arithmetic) ──
            snaps = dump["snaps"]
            ev = next((s for s in snaps if s.get("dimple", 0) > 1e-4), None)
            if ev is not None:
                nxt = snaps[snaps.index(ev) + 1] if snaps.index(ev) + 1 < len(snaps) else None
                crossings = [f for f in raf if f["r"] and f["r"] >= ev["ts"]]
                if crossings:
                    t_render = crossings[0]["t"]
                    w_e = ev["arrival"] - (snaps[snaps.index(ev)]["ts"] - ev["ts"]) / 1000.0
                    latency = t_render - ev["arrival"] + \
                        ((nxt["ts"] - ev["ts"]) / 1000.0 if nxt else 0)
                    timing[name]["press"] = {
                        "ts_event_us": ev["ts"],
                        "age_at_first_render_ms": (crossings[0]["r"] - ev["ts"]) / 1000.0,
                        "latency_est_ms": round(latency, 2),
                        "d_ms": 50.0}
        if cfg["scenario"] == "PRESS":
            continue     # post-press truth has no dimple (press is A-only)

        # ── visual error via the replay instrument ────────────────────
        truth_path = d / f"truth_{name}.bin"
        if not truth_path.exists() or not dump.get("samples"):
            continue
        frames = load_truth_frames(truth_path)
        snaps = dump["snaps"]
        shift, rmse = estimate_shift(snaps, frames)

        # truth curve scale for phase bucketing
        tys = [f["root_y"] for f in frames]
        peak = max(tys)
        cfg_shift = None
        pairs_meta = []
        for smp in dump["samples"]:
            if cfg["scenario"] == "FALL":
                y = truth_root_y_at(frames, smp["r"] - shift)
                if y is None:
                    phase = "NO-TRUTH"
                else:
                    phase = fall_phase_of(y, peak)
            else:                     # CARRY: one phase, bounded delta note
                phase = "CARRY"
            pairs_meta.append(phase)
        still_idx = []
        if a.stills:
            order = sorted(range(len(dump["samples"])),
                           key=lambda i: -i)  # replaced after mads known
            still_idx = list(range(min(3, len(dump["samples"]))))
        data = rr.build_data(dump, frames, topo, -shift,  # B sampled at r-shift
                             {i: ph for i, ph in enumerate(pairs_meta)}, still_idx)
        if not data["pairs"]:
            continue
        res = rr.run_replay(data)
        per_phase: dict = {}
        mads = []
        for p in res["pairs"]:
            ph = p["phase"] or "?"
            per_phase.setdefault(ph, []).append(p["mad"])
            mads.append(p["mad"])
        agg = {ph: {"n": len(v), "median_mad": round(statistics.median(v), 3),
                    "p95_mad": round(sorted(v)[int(0.95 * (len(v) - 1))], 3),
                    "max_mad": round(max(v), 3)} for ph, v in per_phase.items()}
        # name the worst sample's phase + save its still
        worst_i = max(range(len(mads)), key=lambda i: mads[i])
        worst_phase = res["pairs"][worst_i]["phase"]
        if a.stills:
            worst_data = rr.build_data(
                dump, frames, topo, -shift,
                {i: ph for i, ph in enumerate(pairs_meta)}, [worst_i])
            res_w = rr.run_replay(worst_data)
            for st in res_w["stills"]:
                import base64
                (d / f"still_{name}_worst_{worst_phase}.png").write_bytes(
                    base64.b64decode(st["pngB64"]))
        visual[name] = {"shift_us": shift, "shift_rmse_m": round(rmse, 9),
                        "peak_root_y": round(peak, 3),
                        "per_phase": agg,
                        "worst": {"pair": worst_i, "phase": worst_phase,
                                  "mad": round(mads[worst_i], 3)},
                        "overall": {"median_mad": round(statistics.median(mads), 3),
                                    "p95_mad": round(sorted(mads)[int(0.95 * (len(mads) - 1))], 3),
                                    "max_mad": round(max(mads), 3),
                                    "budget": BUDGET_MAD}}
        print(name, json.dumps(visual[name]["overall"]),
              "worst:", worst_phase, flush=True)

    (d / "visual_error.json").write_text(json.dumps(visual, indent=1))
    (d / "frame_time.json").write_text(json.dumps(timing, indent=1))
    print("ANALYZE-DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
