"""test_render_pipeline.py -- the whole path, once per term: emit -> LOD -> upload -> render.

WHY IT EXISTS. Every defect this lane found in two batches was in the SEAM between two working
components, and none of them was visible from either side:

    the camera aimed away from the object      (orbit_proof, then demo -- both rendered background)
    body_radius in local units vs a distance in metres  (LOD collapsed every body to one splat)
    a fixed mip top rung                        (a 16x pop on the one term big enough to show it)
    xfrc_applied acting at the centre of mass   (a tip load half a segment short)

Each was found by a person looking at one thing. Nothing walked the whole path for every term and
asked the only question that catches a seam: DID A PICTURE COME OUT.

    python ChimeraEngine/test_render_pipeline.py          # all renderable terms
    python ChimeraEngine/test_render_pipeline.py --quick  # first 8
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa
import lod as LOD

W, H = 960, 540           # half res: this walks 42 terms and the question is "did it draw", not speed
FOV = 1.047
_BG = np.array([0.015, 0.015, 0.04], dtype=np.float32) * 255.0
_BG_MAX = float(_BG.max())          # 10.2 -- anything at or below this is bare background


def _aim(cam, dist):
    """Aim at the origin. NOT `atan2(-pos[1], pos[0])`, which is the bug this test exists to catch."""
    pos = (0.0, -dist, 0.0)
    cam.position = np.array(pos, dtype=np.float32)
    n = math.sqrt(sum(p * p for p in pos)) or 1.0
    fx, fy, fz = -pos[0] / n, -pos[1] / n, -pos[2] / n
    cam.yaw = math.atan2(fy, fx)
    cam.pitch = math.atan2(fz, math.hypot(fx, fy))


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    terms = sa.scene_terms()
    if "--quick" in argv:
        terms = terms[:8]
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, -3.0, 0.0))

    print(f"RENDER PIPELINE TEST -- {len(terms)} terms, emit -> LOD -> upload -> render")
    print(f"background max is {_BG_MAX:.1f}; a frame at or below it drew NOTHING")
    print("=" * 100)
    print(f"  {'term':<22s} {'n_base':>8s} {'n_lod':>8s} {'save':>6s} {'maxpx':>6s} "
          f"{'cover':>7s}  result")
    print("-" * 100)

    fails, rows = [], []
    for t in terms:
        buf = sa.scene_buffer(t)
        if buf is None or buf.ndim != 2 or buf.shape[0] == 0:
            print(f"  {t:<22s} {'-':>8s} {'-':>8s} {'-':>6s} {'-':>6s} {'-':>7s}  "
                  f"FAIL: scene_buffer returned {'None' if buf is None else 'empty'}")
            fails.append((t, "no buffer")); continue
        if buf.shape[1] != 28:
            print(f"  {t:<22s}  FAIL: shape {buf.shape}, expected (N,28)")
            fails.append((t, f"shape {buf.shape}")); continue

        R = LOD.body_radius(buf)
        dist = 2.8 * max(R, 1e-6)
        draw = buf
        if LOD.should_lod(buf):
            draw = LOD.lod_switch(buf, dist, H, FOV)
        _aim(cam, dist)
        pipe.upload(np.ascontiguousarray(draw, dtype=np.float32), term=t)
        img = pipe.render_from_gpu(cam, cam.params(W, H))
        mx = float(img.max())
        cov = float(((img.astype(np.float32) > _BG + 2.0).any(-1)).mean())
        save = 100.0 * (1.0 - draw.shape[0] / max(buf.shape[0], 1))

        why = []
        # THE ONE CHECK THAT CATCHES A SEAM: did a picture come out.
        if mx <= _BG_MAX:
            why.append("rendered NOTHING (max pixel == background)")
        # LOD may only ever REDUCE. A level with more grains than the base is a pyramid built wrong.
        if draw.shape[0] > buf.shape[0]:
            why.append(f"LOD grew the buffer {buf.shape[0]} -> {draw.shape[0]}")
        # A ZERO-EXTENT BODY IS EXEMPT FROM THE PICTURE CHECK, and saying so is not a loosened
        # bar -- theZero is r = 0, a point, and "a point projects to nothing" is the correct
        # answer rather than a failure. It is reported so the exemption is visible.
        if R <= 1e-9 and why:
            why = [w for w in why if "NOTHING" not in w] + ["zero-extent body (r=0) -- exempt"]

        ok = not [w for w in why if "exempt" not in w]
        rows.append((t, buf.shape[0], draw.shape[0], save, mx, cov, ok))
        print(f"  {t:<22s} {buf.shape[0]:>8d} {draw.shape[0]:>8d} {save:>5.1f}% {mx:>6.0f} "
              f"{100*cov:>6.2f}%  {'ok' if ok else 'FAIL: ' + '; '.join(why)}")
        if not ok:
            fails.append((t, "; ".join(why)))

    print("=" * 100)
    drew = sum(1 for r in rows if r[6])
    lodded = sum(1 for r in rows if r[3] > 0.5)
    print(f"  {drew}/{len(terms)} terms rendered a picture | {lodded} took a coarser LOD level "
          f"at default framing")
    if fails:
        print(f"  {len(fails)} FAILURES:")
        for t, w in fails:
            print(f"    {t}: {w}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
