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
import base64
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
        if cfg["scenario"] in ("PRESS", "CARRY") and (cfg.get("press") or cfg["scenario"] == "CARRY"):
            # EVENT visible latency (carry_start; the press was refused by
            # the engine's off-body guard on the stand-in capsule -- recorded
            # in the receipt as a substitution)
            # ts_e: the twin truth's own first-motion frame (B carries the
            # same event; machine-clock ts is shared). Visible at: the first
            # client render point whose rendered frame departs rest.
            import base64 as _b64
            import numpy as _np
            frames = load_truth_frames(d / f"truth_{name}.bin")   # own truth; the visual block loads its own later
            def _cent(arr_b64):
                f32 = _np.frombuffer(_b64.b64decode(arr_b64), dtype=_np.float32)
                return float(f32.reshape(-1, 9)[:, 0].mean())
            def _tcent(ts):
                t = rr.truth_at(frames, ts)
                return None if t is None else float(_np.asarray(t["pos"]).reshape(-1, 3)[:, 0].mean())
            smp = dump.get("samples", [])
            if smp:
                base_c = _cent(smp[0]["frame"])
                vis = next((x for x in smp if abs(_cent(x["frame"]) - base_c) > 0.002), None)
                te = None
                lo_c = _tcent(smp[0]["r"])
                if lo_c is not None:
                    for f in frames:
                        c = float(_np.asarray(f["pos"]).reshape(-1, 3)[:, 0].mean())
                        if abs(c - lo_c) > 0.002:
                            te = f["ts"]
                            break
                if vis is not None:
                    # the display age of the GOVERNING snapshot that first
                    # showed the event (authoritative A.ts), plus the
                    # detection bound (one snapshot interval, since the event
                    # could have happened any time inside it)
                    age = (vis["r"] - vis["a"]) / 1000.0
                    prev = max((x["a"] for x in smp if x["a"] < vis["a"]),
                               default=vis["a"])
                    timing[name]["event_latency"] = {
                        "event": "carry_start",
                        "ts_first_motion_snapshot_us": int(vis["a"]),
                        "age_at_first_render_ms": round(age, 2),
                        "detection_bound_one_interval_ms":
                            round((vis["a"] - prev) / 1000.0, 2),
                        "d_ms": (1.5 * 1000.0 / cfg["rate_nominal"])
                                + cfg.get("jhead_ms", 0)}
                    if te is not None:
                        timing[name]["event_latency"]["twin_onset_offset_ms"] =                             round((vis["r"] - te) / 1000.0, 2)
        if cfg["scenario"] == "PRESS":
            continue     # the event run contributes latency, not F2 visuals

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
        # THE METRIC INSTRUMENT: the numpy software rasterizer (the page's own
        # shader math; browser-free after the environment broke both browsers'
        # usable paths -- recorded in the receipt as an instrument substitution)
        import raster as _raster
        import base64 as _b64
        vp = _raster.camera_vp(data["camera"], data["target"])
        topo_idx = np.frombuffer(topo, dtype=np.uint32, offset=4)
        per_phase: dict = {}
        mads = []
        still_frames = {}
        for pr in data["pairs"]:
            fa = np.frombuffer(base64.b64decode(pr["a"]), dtype=np.float32).reshape(-1, 9)
            fb = np.frombuffer(base64.b64decode(pr["b"]), dtype=np.float32).reshape(-1, 9)
            ia = _raster.raster_frame(fa, vp, topo_idx)
            ib = _raster.raster_frame(fb, vp, topo_idx)
            m = _raster.mad_frames(ia, ib)
            ph = pr["phase"] or "?"
            per_phase.setdefault(ph, []).append(m["mad"])
            mads.append(m["mad"])
            still_frames[pr["i"]] = (ia, ib)
        res = {"pairs": [{"i": pr["i"], "t": pr["t"], "phase": pr["phase"],
                          "r": pr["r"], "mad": mads[j], "max": 0}
                         for j, pr in enumerate(data["pairs"])]}
        agg = {ph: {"n": len(v), "median_mad": round(statistics.median(v), 3),
                    "p95_mad": round(sorted(v)[int(0.95 * (len(v) - 1))], 3),
                    "max_mad": round(max(v), 3)} for ph, v in per_phase.items()}
        # name the worst sample's phase + save its still
        worst_i = max(range(len(mads)), key=lambda i: mads[i])
        worst_phase = res["pairs"][worst_i]["phase"]
        if a.stills and worst_i in still_frames:
            ia, ib = still_frames[worst_i]
            from PIL import Image
            side = np.concatenate([ia, ib], axis=1)
            Image.fromarray(side).save(d / f"still_{name}_worst_{worst_phase}.png")
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
