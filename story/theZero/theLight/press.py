"""press.py -- the record press for theLight.

Runs the master algorithm (the folded walk, pinned seed + rain), prints the
RULE 0 theory and the falsifier verdict, and dumps begin / mid / end frames
through THE SAME Chimera pipeline the HTTP viewer uses, so the offline record
matches the live view bit-for-bit in framing.

Usage:
    python story/theZero/theLight/press.py [--force]
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np  # noqa: E402

import physics  # noqa: E402

OUT_DIR = Path(_ROOT) / "ChimeraEngine" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

THEORY = """\
THE RECORD PLAYER MATRIX -- first record: theLight
  STATEMENT : 2000 identical points (32 pinned bond-shelf seed grains, 1968
              free grains on a shell at r_rain) integrated by ONE folded
              Barnes-Hut walk settle into a compact membrane body around the
              seed.  Walls and bonds are NOT authored: they are the modifier M
              awakening in the leaves wherever grains touch.
  PREDICTION: the rain falls purely under the draw (zero initial velocity);
              contact radiation lights only where grains touch and dissipates
              as the body packs; the settled body is bound (frac > 0.5),
              settled, and bounded inside the rain shell; the folded walk's
              resistance matches the two-pass referee to <= 1e-4.
  FALSIFIER : bound frac <= 0.5; late cluster-count CV >= 0.20; late bound
              swing >= 0.15; final radius >= r_rain; no radiation (M never
              awakened); fold vs referee > 1e-4.  Any one fires the verdict.
"""


def _dump_frame(buf: np.ndarray, nums: dict, png: Path):
    """Render a splat buffer through the Chimera GPU pipeline (the viewer's path)."""
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    from PIL import Image

    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    pipe.upload(np.ascontiguousarray(buf, dtype=np.float32), term="theLight")

    d = float(nums["extent_m"]) * 2.8
    el = 0.35
    az = -0.7
    ce = math.cos(el)
    pos = (d * ce * math.sin(az), -d * ce * math.cos(az), d * math.sin(el))
    n = math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2)
    cam = FirstPersonCamera(
        position=np.array(pos, dtype=np.float32),
        yaw=math.atan2(-pos[1], -pos[0]),
        pitch=math.asin(-pos[2] / n),
        fov=np.radians(60),
        near=0.05,
        far=200.0,
    )
    img = pipe.render_from_gpu(cam, cam.params(width=1280, height=720))
    Image.fromarray(img).save(png)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-press the record")
    args = ap.parse_args()

    print(THEORY)
    print("=" * 62)
    nums = physics.derive_commit()
    print(f"n_total={nums['n_total']}  n_seed={nums['n_seed']}  "
          f"r_rain={nums['r_rain_lu']} lu  dt={nums['dt']}  "
          f"ticks={nums['t_total_ticks']}  "
          f"window={nums['t_total_units']} tu = "
          f"{nums['t_ff_count']}x shell free-fall")
    print("=" * 62)

    t0 = time.time()
    physics._press(nums, force=args.force)
    print(f"record pressed -> {physics.RECORD_PATH.name}  "
          f"({time.time() - t0:.1f}s)")

    v = physics.verdict(nums)
    print("\nFALSIFIER VERDICT:", v["verdict"])
    for name, ok in zip(v["checks"], v["ok"]):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  final bound frac    = {v['final_bound_frac']}")
    print(f"  final radius        = {v['final_radius']} (r_rain {v['r_rain']})")
    print(f"  late cluster CV     = {v['late_cluster_cv']}")
    print(f"  late bound swing    = {v['late_bound_swing']}")
    print(f"  radiated energy     = {v['final_radiated_energy']}"
          f" (first impact t={v['first_impact_tick']})")
    print(f"  fold vs referee     = max resist {v['max_resist_rel']:.2e} / "
          f"global {v['max_global_rel']:.2e} over {v['checkpoints']} checkpoints")

    for t_, name in ((0.0, "begin"), (0.5, "mid"), (1.0, "end")):
        buf = physics.emit(nums, t_)
        png = OUT_DIR / f"theLight_{name}.png"
        _dump_frame(buf, nums, png)
        print(f"  {name:5s} frame  t={t_:.1f}  grains={buf.shape[0]:4d}  -> {png}")
    print("=" * 62)
    return 0 if v["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
