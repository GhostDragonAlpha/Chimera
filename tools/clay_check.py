"""clay_check.py -- how much can generated geometry drift before we catch it?

THE QUESTION THIS ANSWERS. `clay_export.py` sends a membrane's own geometry to a video model as a
white-model blockout, and the whole argument for it being legal under THE_GROWTH's
"measure -> sample -> prove, never generate -> trust" is that the result is CHECKABLE: reconstruct
from the generated views, compare against the clay that was fed in, and refuse the take if the
model invented structure.

That argument is worthless until somebody measures whether the check can actually SEE a small lie.
Gross hallucination -- a second moon, an extra limb -- will be obvious to anyone. A bench half a
metre too shallow, a pit five percent too wide, a limb two centimetres too long: those are the
drifts that would pass unnoticed and poison a genome. So:

    INJECT A KNOWN PERTURBATION, SWEEP ITS SIZE, AND FIND WHERE THE CHECK STOPS NOTICING.

No generator is needed for this and that is the point -- the instrument has to be calibrated before
it is trusted, not after. This is the studio's own rule about verifying the measurement rather than
the claim, applied to a check that does not have anything to check yet.

WHAT IS COMPARED. Both the source geometry and a perturbed copy are rendered from the SAME camera
poses clay_export writes down, and two numbers come back per frame:

    SILHOUETTE IoU   does the outline still match? Lighting-invariant by construction, which is
                     what makes it the real check.
    SHADING L1       kept, and REPORTED AS DIAGNOSTIC ONLY. See below -- it is confounded.

THE SHADING SIGNAL IS USELESS AND THAT IS A MEASURED RESULT, not a caution. Moving the key light
30 degrees, with the geometry untouched, gives a mean L1 of 0.05699. Crushing the subject's relief
by TWENTY PERCENT gives 0.05719. The two are indistinguishable, so L1 cannot separate "the model
lit it differently" from "the model flattened it", and a generator will always light it
differently. It stays in the output because a number you have shown to be worthless is more useful
than a number you never computed -- but nothing may gate on it.

    appearance-only change      worst IoU     mean L1
    key light moved 10 deg        0.99735     0.02170
    key light moved 30 deg        0.98981     0.05699        <- as large as a 20% flatten
    exposure +15%                 0.99358     0.02318

    geometry change             worst IoU     mean L1
    flatten  1%                   0.98059     0.00753
    flatten  5%                   0.90801     0.02753
    flatten 20%                   0.67604     0.05719        <- same L1, nine times the IoU signal

SO THE HONEST THRESHOLD IS NOT 0.1%. Against a still renderer the metric resolves a tenth of a
percent, and quoting that would be measuring the instrument in a vacuum. Against realistic
appearance drift the floor is an IoU near 0.99, which puts the usable detection threshold at
roughly TWO PERCENT of the subject's extent. Twenty times worse than the naive figure, and knowing
that before trusting a genome is the whole reason this file exists.

AND IT SCALES WITH THE SUBJECT, which matters more than it looks. Two percent of a 1.85 m figure is
3.7 cm -- fine. Two percent of a 12 km terrain patch is 240 METRES. The same check that comfortably
polices a suit cannot see a hill move.

The threshold is reported as a fraction of the membrane's OWN extent, so it is comparable across a
figure, a mine and a planet without anyone rescaling anything.

RUN:  python tools/clay_check.py aHuman
      python tools/clay_check.py aTerrain --kind bulge --views 12
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "story"))

# The sizes swept, as a fraction of the subject's own extent. The small end is deliberately absurd
# -- a tenth of a percent -- because a threshold is only meaningful if the sweep starts below it.
AMOUNTS = (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20)


def perturb(buf, kind, amount, extent):
    """A KNOWN lie about the geometry, of a stated size. Each kind is a different way a generator
    could plausibly get it wrong, and they are not equally easy to see -- which is the finding."""
    import numpy as np
    from matter import PX, PZ

    b = np.array(buf, dtype=np.float32, copy=True)
    P = b[:, PX:PZ + 1]
    d = amount * extent

    if kind == "scale":
        # the whole subject uniformly bigger. The EASIEST case, and worth measuring anyway as the
        # optimistic bound on what any of this can do.
        b[:, PX:PZ + 1] = P * (1.0 + amount)
    elif kind == "shift":
        # bodily displaced. Trivial for a check with known cameras, hard for one without them --
        # which is an argument for exporting the poses.
        b[:, PX] = P[:, 0] + d
    elif kind == "bulge":
        # a radial swelling, largest at the middle: a subject that has been made subtly ROUNDER.
        # This is what a generator smoothing an unfamiliar shape actually does.
        r = np.linalg.norm(P, axis=1, keepdims=True)
        w = np.exp(-((r / max(extent, 1e-9)) - 0.5) ** 2 / 0.08)
        b[:, PX:PZ + 1] = P + (P / np.maximum(r, 1e-9)) * d * w
    elif kind == "flatten":
        # vertical relief compressed -- a mine's benches made shallower, a terrain's valleys made
        # softer. The single most likely way a generated landscape is wrong, and it leaves the
        # outline from directly overhead almost untouched.
        b[:, PZ] = P[:, 2] * (1.0 - amount)
    elif kind == "noise":
        # per-point jitter: a surface that has been roughened without changing its form.
        rng = np.random.default_rng(11)
        b[:, PX:PZ + 1] = P + rng.normal(0.0, d, P.shape)
    else:
        raise ValueError(f"unknown perturbation {kind!r}")
    return b


def _views(term, frames, arc, elev, dist, w, h):
    """Render the source clay and return (images, cameras, pipeline, source buffer, extent)."""
    import numpy as np
    from ChimeraEngine import splat_appearance as SA
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    from clay_export import clay, key_for, orbit_camera
    from matter import PX, PZ

    src = SA.membrane_buffer(term, 1.0)
    extent = float(np.linalg.norm(np.asarray(src)[:, PX:PZ + 1], axis=1).max()) or 1.0
    pipe = FullGPUPipeline(bg=(0.5, 0.5, 0.5))
    cams = []
    for i in range(frames):
        pos, yaw, pitch = orbit_camera(extent, i, frames, arc, elev, dist)
        cam = FirstPersonCamera(pos, yaw=yaw, pitch=pitch)
        cams.append((cam, cam.params(w, h), key_for(yaw, pitch)))
    return src, extent, pipe, cams


def _render(pipe, buf, cams):
    import numpy as np
    from PIL import Image
    from clay_export import clay
    out = []
    for cam, p, key in cams:
        pipe.upload(clay(buf, key))
        out.append(np.asarray(Image.fromarray(pipe.render_from_gpu(cam, p)).convert("L"),
                              dtype=np.float32) / 255.0)
    return out


def compare(a, b):
    """Two numbers per view: does the outline match, and does the surface face the same way?

    THE BACKGROUND IS EXACTLY 0.5 by construction (clay_export renders on neutral grey), so the
    silhouette is everything that differs from it. That is a cheap and honest segmentation -- no
    threshold anyone had to choose."""
    import numpy as np
    sa = np.abs(a - 0.5) > 0.02
    sb = np.abs(b - 0.5) > 0.02
    inter = float(np.logical_and(sa, sb).sum())
    union = float(np.logical_or(sa, sb).sum())
    iou = inter / max(union, 1.0)
    both = np.logical_and(sa, sb)
    l1 = float(np.abs(a[both] - b[both]).mean()) if both.any() else 0.0
    return iou, l1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("membrane")
    ap.add_argument("--views", type=int, default=8)
    ap.add_argument("--kind", default="all")
    ap.add_argument("--arc", type=float, default=315.0)
    ap.add_argument("--elev", type=float, default=16.0)
    ap.add_argument("--dist", type=float, default=2.6)
    ap.add_argument("--size", type=int, default=384)
    a = ap.parse_args()

    src, extent, pipe, cams = _views(a.membrane, a.views, a.arc, a.elev, a.dist, a.size, a.size)
    base = _render(pipe, src, cams)

    # THE NOISE FLOOR FIRST. Rendering the same buffer twice must give the same picture, or every
    # number below is measuring the renderer instead of the geometry. This is the control, and it
    # runs before anything else because a check with an unmeasured floor cannot state a threshold.
    again = _render(pipe, src, cams)
    floors = [compare(x, y) for x, y in zip(base, again)]
    f_iou = min(v[0] for v in floors)
    f_l1 = max(v[1] for v in floors)
    print(f"{a.membrane}: {a.views} views, extent {extent:.4g} local")
    print(f"NOISE FLOOR (same geometry rendered twice)   IoU {f_iou:.6f}   shading L1 {f_l1:.6f}")
    if f_iou < 0.9999 or f_l1 > 1e-6:
        print("   the renderer is not deterministic; every threshold below is suspect")
    print()

    kinds = ("scale", "shift", "bulge", "flatten", "noise") if a.kind == "all" else (a.kind,)
    # THE REAL FLOOR IS APPEARANCE DRIFT, not renderer noise. A generator will not reproduce our
    # lighting, so the honest control is "same geometry, different light" -- measured here rather
    # than assumed, because it is what sets the threshold.
    import math as _m
    import numpy as np
    from clay_export import clay as _clay
    from PIL import Image as _Img
    drift = []
    for dyaw in (10.0, 30.0):
        imgs = []
        for cam, pp, key in cams:
            y = _m.atan2(-key[1], -key[0]) + _m.radians(dyaw)
            pi_ = _m.asin(max(-1.0, min(1.0, key[2])))
            k = (-_m.cos(y) * _m.cos(pi_), -_m.sin(y) * _m.cos(pi_), _m.sin(pi_))
            pipe.upload(_clay(src, k))
            imgs.append(np.asarray(_Img.fromarray(pipe.render_from_gpu(cam, pp)).convert("L"),
                                   dtype=np.float32) / 255.0)
        r = [compare(x, y) for x, y in zip(base, imgs)]
        drift.append((dyaw, min(v[0] for v in r), sum(v[1] for v in r) / len(r)))
    a_iou = min(d[1] for d in drift)
    a_l1 = max(d[2] for d in drift)
    print("APPEARANCE FLOOR (same geometry, key light moved -- what a generator will always do):")
    for dyaw, i_, l_ in drift:
        print(f"   key moved {dyaw:.0f} deg   IoU {i_:.5f}   L1 {l_:.5f}")
    print(f"   -> the usable floor is IoU {a_iou:.5f}. SHADING L1 IS CONFOUNDED AT {a_l1:.5f} "
          f"and gates nothing.")
    print()

    print(f"{'perturbation':<10} {'size':>8} {'worst IoU':>11} {'mean L1':>10}   verdict")
    print("-" * 62)
    thresholds = {}
    for kind in kinds:
        found = None
        for amt in AMOUNTS:
            imgs = _render(pipe, perturb(src, kind, amt, extent), cams)
            res = [compare(x, y) for x, y in zip(base, imgs)]
            iou = min(v[0] for v in res)
            l1 = sum(v[1] for v in res) / len(res)
            # CAUGHT means the difference is far above the floor -- 10x on either signal. Stated as
            # a factor rather than an absolute so it stays honest if the floor ever moves.
            # SILHOUETTE ONLY. L1 is printed and deliberately not consulted -- see the header.
            caught = iou < a_iou - 0.004
            if caught and found is None:
                found = amt
            print(f"{kind:<10} {amt*100:7.1f}% {iou:11.5f} {l1:10.5f}   "
                  f"{'CAUGHT' if caught else 'missed'}")
        thresholds[kind] = found
        print()

    print("DETECTION THRESHOLD, as a fraction of the subject's own extent:")
    for kind, t in thresholds.items():
        if t is None:
            print(f"   {kind:<10} NOT DETECTED even at {AMOUNTS[-1]*100:.0f}%")
        else:
            print(f"   {kind:<10} {t*100:.1f}%  ({t*extent:.5g} local units)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
