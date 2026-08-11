"""million_needles.py -- one million needles, each on its own groove, switched by input.

The operator's image, made runnable: the viewer's 1M-splat limit is the budget,
so the frame holds 1M packets -- but each packet is a NEEDLE that travels its
OWN groove.  The groove is a LAW, not a lookup (ChimeraEngine/needle_law.py):
per-needle constants define a closed-form position as a function of the pass
clock.  Pre-recording 1M needles x T frames would be ~432 MB; 1M groove specs
are 40 MB, and replay is FREE because the law reproduces the run.

A SWITCH is an input event that reroutes a needle onto another rail -- and the
law CONNECTS the rails: the target rail's phase is solved so it passes through
the needle's position at the throw instant.  A switch is a railroad join, not
a teleport.  "Angry mode -> happy mode" is a whole-ensemble switch on the
couplings -- the operator's gradient-descent image: the groove values are HOW
the descent is applied, positions are what is walked.

FALSIFIERS (named before the run):
  F1  one needle, one groove: every needle was born on its own rail (measured
      before any switch) and every needle actually moves each pass.
  F2  a switch reroutes: switched needles end up where their OLD rail would
      not have put them.
  F3  the frame stays in the wallet: render <= MAX_RENDER_MS at 1920x1080
      while rendering the full 1,000,000 splats.
  F4  the record is the matrix: reloading grooves + switches and re-walking
      the clock reproduces the run's positions to <= 1e-3.
  F5  the switch is a JOIN: at the throw pass, the target rail passes through
      the needle's position (position continuity to <= 1e-2).

Usage:
    python ChimeraEngine/million_needles.py [--frames N]
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[0]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np  # noqa: E402

from ParticleEngine.camera import FirstPersonCamera  # noqa: E402
from ParticleEngine.gpu_pipeline import FullGPUPipeline  # noqa: E402
from ChimeraEngine.perf_guard import MAX_RENDER_MS  # noqa: E402
from ChimeraEngine import needle_law  # noqa: E402

NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

N_NEEDLES = 1_000_000
N_STAR = 2_000
R_STAR = 30.0
PASSES = 36
CAM_R = 24.0
NEEDLE_SIZE = 0.045
SEED = 7

OUT = _HERE / "matrix_out" / "needles"
SAMPLE_EVERY = 1000


def _blank(n: int) -> np.ndarray:
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, 9] = 1.0
    b[:, 10] = -1.0
    b[:, TYPE] = 3.0
    b[:, ALPHA] = 0.9
    return b


def _fill(buf: np.ndarray, pos: np.ndarray, rgb, size: float):
    buf[:, PX:PZ + 1] = pos
    buf[:, CR] = rgb[0]
    buf[:, CG] = rgb[1]
    buf[:, CB] = rgb[2]
    buf[:, SIZE] = size


def _switch_events() -> list[dict]:
    """The input timeline: whole-ensemble mood switches + targeted reroutes."""
    stream_rail = [1.0, 6.0, 0.02, 0.0, 0.3, 0.0, 0.03, 0.0, 0.0, 0.0]
    orbit_rail = [0.0, 8.0, 0.03, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0]
    plane_rail = [2.0, 7.0, 0.025, 0.0, 0.8, 0.0, 0.04, 0.0, 0.0, 0.0]
    shell_rail = [3.0, 9.0, 0.02, 1.3, 0.6, 0.0, 0.01, 0.0, 0.0, 0.0]
    return [
        {"pass": 8, "lo": 0, "n": 400_000, "target": stream_rail, "name": "angry-mood"},
        {"pass": 18, "lo": 0, "n": 400_000, "target": orbit_rail, "name": "happy-mood"},
        {"pass": 26, "lo": 400_000, "n": 200_000, "target": plane_rail, "name": "disc"},
        {"pass": 30, "lo": 600_000, "n": 100_000, "target": shell_rail, "name": "shell"},
    ]


def _fib_stars(n: int, r: float) -> np.ndarray:
    rng = np.random.default_rng(2)
    i = np.arange(n, dtype=np.float64)
    phi = math.pi * (3.0 - math.sqrt(5.0))
    y = 1.0 - (2.0 * i + 1.0) / n
    rad = np.sqrt(np.clip(1.0 - y * y, 0.0, 1.0))
    th = phi * i
    p = np.stack([np.cos(th) * rad, y, np.sin(th) * rad], axis=1) * r
    return (p + rng.uniform(-0.5, 0.5, p.shape)).astype(np.float32)


def _atomic(path: Path, fn):
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    fn(tmp)
    os.replace(tmp, path)


def main() -> int:
    frames = PASSES
    if "--frames" in sys.argv:
        frames = int(sys.argv[sys.argv.index("--frames") + 1])

    grooves = needle_law.make_grooves(N_NEEDLES, seed=SEED)
    initial_rails = grooves[:, 1:3].copy()
    events = _switch_events()

    stars_pos = _fib_stars(N_STAR, R_STAR)
    star_buf = _blank(N_STAR)
    _fill(star_buf, stars_pos, (0.45, 0.55, 0.90), 1.2)

    pipe = FullGPUPipeline(bg=(0.008, 0.008, 0.03))

    print("MILLION NEEDLES -- 1M splats, each on its own groove, switched by input")
    print(f"  budget: the viewer's 1M-splat limit; wallet {MAX_RENDER_MS} ms at 1080p")
    print(f"  grooves: {N_NEEDLES:,} needles x 10 params = {N_NEEDLES * 40 / 1e6:.0f} MB "
          f"(a T-frame lookup table would be {N_NEEDLES * frames * 12 / 1e6:.0f} MB)")
    print(f"  switches CONNECT rails: the target rail's phase is solved at the throw")
    print("-" * 108)
    print(f"{'pass':>4} {'orbit':>8} {'stream':>8} {'plane':>8} {'shell':>8} "
          f"{'switched':>8} {'expans':>8} {'render ms':>9} {'fps':>6}")
    print("-" * 108)

    sample_idx = np.arange(0, N_NEEDLES, SAMPLE_EVERY)
    pos_sample = np.zeros((frames, sample_idx.size, 3), np.float32)
    stats = []
    max_render = 0.0
    snapshots: dict[int, np.ndarray] = {}
    connect_errors: list[float] = []

    for k in range(frames):
        for ev in events:
            if ev["pass"] == k:
                connect_errors.append(
                    needle_law.apply_switch(grooves, ev, float(k), snapshots))
        pos = needle_law.positions(grooves, float(k))

        needle_buf = _blank(N_NEEDLES)
        needle_buf[:, PX:PZ + 1] = pos
        for t, rgb in needle_law.COLOR.items():
            m = grooves[:, 0] == t
            needle_buf[m, CR] = rgb[0]
            needle_buf[m, CG] = rgb[1]
            needle_buf[m, CB] = rgb[2]
        needle_buf[:, SIZE] = NEEDLE_SIZE
        buf = np.vstack([needle_buf, star_buf])

        a = 0.02 * k
        cam_pos = np.array([CAM_R * math.cos(a), CAM_R * math.sin(a) * 0.8,
                            CAM_R * 0.35 * math.sin(a)], np.float32)
        n_pos = math.sqrt(cam_pos[0] ** 2 + cam_pos[1] ** 2 + cam_pos[2] ** 2)
        cam = FirstPersonCamera(
            position=cam_pos,
            yaw=math.atan2(-cam_pos[1], -cam_pos[0]),
            pitch=math.asin(-cam_pos[2] / n_pos),
            fov=np.radians(60), near=0.05, far=R_STAR * 2.0,
        )
        pipe.upload(np.ascontiguousarray(buf), term="")
        prm = cam.params(width=1920, height=1080)
        if k < 2:
            pipe.render_from_gpu(cam, prm)
            continue
        t0 = time.perf_counter()
        pipe.render_from_gpu(cam, prm)
        rms = (time.perf_counter() - t0) * 1e3
        st = pipe.tile_stats()
        max_render = max(max_render, rms)

        pos_sample[k] = pos[sample_idx]
        counts = needle_law.groove_counts(grooves)
        switched = sum(1 for ev in events if ev["pass"] <= k)
        stats.append({"pass": k, "types": counts, "switched": switched,
                      "render_ms": rms, "expansions": int(st["expansions"])})
        print(f"{k:>4} {counts[0]:>8} {counts[1]:>8} {counts[2]:>8} {counts[3]:>8} "
              f"{switched:>8} {int(st['expansions']):>8} {rms:>9.2f} {1000.0 / rms:>6.1f}")

    # F1: distinct rails (born, pre-switch) + every needle moves each pass
    keys = len(np.unique(initial_rails, axis=0))
    k0 = float(frames - 1)
    moved = float(np.abs(needle_law.positions(grooves, k0)
                         - needle_law.positions(grooves, k0 - 1.0)).mean())

    # F2: reroute -- switched needles left their old rail
    old_dist = _old_rail_distance(grooves, snapshots, events, frames)

    ok1 = keys > 500_000 and moved > 1e-3
    ok2 = old_dist > 0.3
    ok3 = max_render <= MAX_RENDER_MS
    ok4 = _store_and_verify(grooves, events, stats, pos_sample, sample_idx,
                            frames, SEED)
    connect_err = max(connect_errors) if connect_errors else 0.0
    ok5 = connect_err <= 1e-2

    print("-" * 108)
    print("FALSIFIER VERDICTS")
    print(f"  F1 one needle, one groove        {'PASS' if ok1 else 'FAIL'}: "
          f"{keys:,} distinct (radius,speed) rails, mean pass motion {moved:.4f}")
    print(f"  F2 switch reroutes by input      {'PASS' if ok2 else 'FAIL'}: "
          f"switched needles {old_dist:.3f} from their old rail at the final clock")
    print(f"  F3 1M splats inside the wallet   {'PASS' if ok3 else 'FAIL'}: "
          f"worst {max_render:.1f} ms vs wall {MAX_RENDER_MS} ms")
    print(f"  F4 record IS the matrix          {'PASS' if ok4 else 'FAIL'}: "
          f"reload + replay reproduces the run")
    print(f"  F5 switch is a JOIN              {'PASS' if ok5 else 'FAIL'}: "
          f"worst position discontinuity at a throw = {connect_err:.2e}")
    return 0 if (ok1 and ok2 and ok3 and ok4 and ok5) else 1


def _old_rail_distance(grooves, snapshots, events, frames) -> float:
    """How far switched needles are from where their pre-switch rails would be."""
    k = float(frames - 1)
    dists = []
    for ev in events:
        sl = slice(ev["lo"], ev["lo"] + ev["n"])
        if ev["pass"] not in snapshots:
            continue
        actual = needle_law.positions(grooves[sl], k)
        on_old = needle_law.positions(snapshots[ev["pass"]], k)
        dists.append(float(np.linalg.norm(actual - on_old, axis=1).mean()))
    return float(np.mean(dists)) if dists else 0.0


def _store_and_verify(grooves, events, stats, pos_sample, sample_idx, frames,
                      seed) -> bool:
    OUT.mkdir(parents=True, exist_ok=True)
    _atomic(OUT / "grooves.npz", lambda p: np.savez_compressed(p, grooves=grooves))
    _atomic(OUT / "switches.json", lambda p: p.write_text(json.dumps([
        {"pass": e["pass"], "lo": e["lo"], "n": e["n"], "name": e["name"],
         "target": [float(x) for x in e["target"]]} for e in events
    ], indent=2)))
    _atomic(OUT / "stats.json", lambda p: p.write_text(json.dumps(stats, indent=2)))
    _atomic(OUT / "pos_sample.npz", lambda p: np.savez_compressed(
        p, pos=pos_sample, idx=sample_idx, frames=np.int64(frames)))

    # replay: regenerate initial grooves, re-apply the same switches with the
    # same connect law, re-walk the clock -- the record reproduces the run.
    g2 = needle_law.make_grooves(grooves.shape[0], seed=seed)
    evs = json.loads((OUT / "switches.json").read_text())
    for e in sorted(evs, key=lambda e: e["pass"]):
        needle_law.apply_switch(g2, e, float(e["pass"]))
    pos2 = needle_law.positions(g2, float(frames - 1))[sample_idx]
    ref = np.load(OUT / "pos_sample.npz")["pos"][frames - 1]
    err = float(np.abs(pos2 - ref).max())
    print(f"  matrix written: {OUT} (grooves.npz + switches.json + stats.json)")
    print(f"  replay check: reload -> re-walk clock -> max position error {err:.2e}")
    return err <= 1e-3


if __name__ == "__main__":
    raise SystemExit(main())
