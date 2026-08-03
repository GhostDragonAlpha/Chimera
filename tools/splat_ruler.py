"""splat_ruler.py -- THE SPLAT->SCREEN-PIXEL INSTRUMENT (docs/THE_VEGETATION_GEOMETRY.md,
membrane 3's named falsifier successor).

Three object-level membranes fired in one day (grain contiguity, cylinder normals,
ball-chain tube) and the tuft STILL renders as a blob with no internal structure.
The pre-committed next artifact is not a fourth membrane but the INSTRUMENT: render
known geometry at a known distance through the real pipeline and measure what one
splat actually paints.

The scene, all at y=0, camera 5.0 m back at (0,-5,0.5) facing +y, 1920x1080,
vfov 60 deg (the pipeline's defaults -- nothing chosen for this scene):

  RED   vertical tube: 19 grains, SIZE 0.02, spacing 0.0194 m -- the tuft's own
        blade, rebuilt exactly (predicted height: focal*0.35/5 = 65 px + footprint)
  WHITE horizontal ruler bar: 1.000 m of grains -- the pinhole reference
        (predicted: focal_x*1.0/5 = 187.1 px, focal_x = 540/tan(30 deg) = 935.3)
  GREEN one isolated grain, SIZE 0.02 -- the footprint of ONE ball, measured.

Prints predicted vs measured for each, and the implied FOOTPRINT FACTOR: how many
multiples of s (= SIZE * base_scale) one ball's visible diameter really is. If the
factor x s exceeds the tuft's inter-blade spacing (0.046 m), the blob is ARITHMETIC,
not a bug: blades cannot resolve at that width, and every legibility membrane must
derive against the MEASURED mapping, not the nominal one.

    python tools/splat_ruler.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))                    # ParticleEngine is a repo-root package
sys.path.insert(0, str(REPO / "ChimeraEngine"))
sys.path.insert(0, str(REPO / "story"))          # matter.py lives here (the live path gets
                                                 # it via walker.py; the instrument stands alone)

import numpy as np  # noqa: E402

D = 5.0                     # camera distance, m -- the instrument's own constant
W, H = 1920, 1080
FOCAL = (H / 2.0) / np.tan(np.radians(30.0))   # 935.3 px at vfov 60


def build_scene():
    from matter import blank, SOLID
    grains = []

    # RED tube: the tuft's blade, exactly (19 grains, spacing 0.0194, SIZE 0.02)
    n_t = 19
    t = blank(n_t)
    t[:, 0] = 0.0
    t[:, 1] = 0.0
    t[:, 2] = 0.5 - 0.175 + np.arange(n_t) * (0.35 / (n_t - 1))
    t[:, 16:19] = (1.0, 0.0, 0.0)

    # WHITE ruler bar: 1.000 m along x at z=0.10
    n_b = 51
    bar = blank(n_b)
    bar[:, 0] = -0.5 + np.arange(n_b) * (1.0 / (n_b - 1))
    bar[:, 1] = 0.0
    bar[:, 2] = 0.10
    bar[:, 16:19] = (1.0, 1.0, 1.0)

    # GREEN single grain at x=0, z=0.9
    one = blank(1)
    one[0, 0] = 0.0
    one[0, 1] = 0.0
    one[0, 2] = 0.90
    one[0, 16:19] = (0.0, 1.0, 0.0)

    b = np.vstack([t, bar, one])
    b[:, 19] = 0.95                       # ALPHA
    b[:, 20] = 0.02                       # SIZE -- the tuft's own _BLADE_W
    b[:, 11] = SOLID
    b[:, 21:24] = 0.0                     # the tube membrane's zero normal
    return b


def measure(img, mask, name, pred_px):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        print(f"  {name:26s} NOT VISIBLE")
        return None
    w_px = xs.max() - xs.min() + 1
    h_px = ys.max() - ys.min() + 1
    print(f"  {name:26s} measured {w_px:4d} x {h_px:4d} px   predicted {pred_px:6.1f} px")
    return w_px, h_px


def run(base_scale):
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    pipe = FullGPUPipeline(base_scale=base_scale)
    cam = FirstPersonCamera((0.0, -D, 0.5), yaw=np.pi / 2.0, pitch=0.0)
    pipe.upload(build_scene())
    img = pipe.render_from_gpu(cam, cam.params(W, H))
    r, g_, bl = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
    s_eff = 0.02 * base_scale
    print(f"base_scale {base_scale}  (s = SIZE x base_scale = {s_eff:.3f} m, "
          f"nominal screen sigma {FOCAL * s_eff / D:.2f} px)")
    measure(img, (r > 120) & (g_ < 100) & (bl < 100), "red tube (0.35 m)", FOCAL * 0.35 / D)
    measure(img, (r > 150) & (g_ > 150) & (bl > 150), "white bar (1.000 m)", FOCAL * 1.0 / D)
    m = measure(img, (g_ > 120) & (r < 100) & (bl < 100), "green single grain", 0.0)
    if m:
        dia = max(m)
        factor = dia / (FOCAL * s_eff / D)
        print(f"  -> FOOTPRINT FACTOR: one ball's diameter = {factor:.1f} x s "
              f"({dia} px = {dia * D / FOCAL:.3f} m at {D} m)")
        print(f"  -> tuft inter-blade spacing 0.046 m = {FOCAL * 0.046 / D:.1f} px at {D} m: "
              f"{'blades MERGE (the blob is arithmetic)' if dia * D / FOCAL > 0.046 else 'blades RESOLVABLE'}")


def main() -> int:
    for bs in (0.5, 1.0):
        run(bs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
