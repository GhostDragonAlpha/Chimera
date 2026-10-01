"""test_composite_bg_transmittance.py -- the _composite background falsifier.

REGRESSION (measured 2026-09-28, composition2 white-out investigation):
`_composite` used to pre-load the background at full strength
(`r, g, b = bg_r, bg_g, bg_b`) and never applied the residual transmittance to
it, so a pixel rendered at `bg + sum(c_i)` instead of the correct front-to-back
over `bg*trans_end + sum(c_i)`. With bg=(0,0,0) -- the pipeline default and the
value every in-repo gate rendered with -- the missing term is exactly zero and
the defect is INVISIBLE; with the shipped sky background (0.66, 0.75, 0.85)
every splat over a bright background clipped toward white (a dark-green ground
splat (0.287,0.378,0.173) landed at (0.947,1.128,1.023) -> (241,255,255),
measured). The fix adds the single term `bg * trans` at the output; this test
pins the three behaviours that must hold:

  1. an OPAQUE splat over a bright background renders at its own colour -- no clip;
  2. the residual transmittance scales the background (half-alpha splat -> half bg);
  3. with bg=(0,0,0) the output is the pure splat series -- the term the fix adds
     is exactly 0.0 there, which is why pre-fix black-background frames were
     already correct (byte-identity evidence: the pre/post comparison lives in
     the fixing lane's scratch bundle; this test pins the same closed form).

Method: one crafted TYPE=3 splat centred on the optical axis. At the frame
centre pixel the Gaussian weight is exactly 1 (ge=0) and the cpu_raster cosine
falloff is exactly 1 (t=0), so the expected value is footprint-independent and
the same numbers verify against the independent straight-alpha-over reference
in ChimeraEngine's sky-sun lane evidence. Float32 noise is bounded by +-1/255.

    python ParticleEngine/test_composite_bg_transmittance.py   # the gate
    python -m unittest ParticleEngine.test_composite_bg_transmittance -v
"""
from __future__ import annotations

import math
import os
import sys
import unittest

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

W = H = 256
FOV = math.radians(60.0)
BG_SKY = (0.66, 0.75, 0.85)          # the shipped sky background -- the case that clipped
BG_BLACK = (0.0, 0.0, 0.0)
COL_GROUND = (0.287, 0.378, 0.173)   # the measured composition2 ground splat
COL_GLASS = (0.0, 0.3, 0.0)

try:                                  # the gate is a GPU gate; say so loudly if there is none
    from numba import cuda
    _HAS_GPU = len(cuda.gpus) > 0
except Exception:                     # pragma: no cover - CPU-only host
    _HAS_GPU = False


def _centred_splat(depth_cm, world_size_cm, rgb, alpha):
    """One TYPE=3 splat on the optical axis of a yaw=0/pitch=0 camera at the origin.

    TYPE=3 is the composition buffers' disc type: size scale 1.0, opacity read
    from the ALPHA column, isotropic covariance. Zero normal -> no back-face cull.
    """
    row = np.zeros(28, np.float32)
    row[0] = depth_cm                                 # PX (camera looks along +x)
    row[11] = 3                                       # TYPE
    row[16], row[17], row[18] = rgb                   # CR, CG, CB
    row[19] = alpha                                   # ALPHA
    row[20] = world_size_cm                           # SIZE (cm, pre base_scale)
    return row.reshape(1, 28)


def _render(buf, bg):
    os.environ.setdefault("NUMBA_CACHE_DIR",
                          os.path.join(_HERE, "__pycache__", "numba_cache"))
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    pipe = FullGPUPipeline(bg=bg)
    pipe.upload(buf.astype(np.float32))
    cam = FirstPersonCamera(position=(0.0, 0.0, 0.0), yaw=0.0, pitch=0.0,
                            fov=FOV, far=100000.0)
    return pipe.render_from_gpu(cam, cam.params(W, H))


def _centre(img):
    return tuple(int(v) for v in img[H // 2, W // 2])


@unittest.skipUnless(_HAS_GPU, "no CUDA device: _composite is a GPU kernel, the gate cannot run")
class TestCompositeBackgroundTransmittance(unittest.TestCase):
    TOL = 1  # one output quantum: int() truncation of float32 arithmetic

    @classmethod
    def setUpClass(cls):
        cls.opaque = _centred_splat(2000.0, 720.0, COL_GROUND, 1.0)
        cls.half = _centred_splat(1000.0, 360.0, COL_GLASS, 0.5)

    def test_opaque_splat_over_bright_bg_does_not_clip(self):
        """The composition2 white-out, pinned: the opaque ground splat must render
        at its own colour over the shipped sky background, not bg + colour."""
        expected = tuple(round(c * 255.0) for c in COL_GROUND)     # bg*trans_end, trans_end == 0
        got = _centre(_render(self.opaque, BG_SKY))
        for ch, (g, e) in enumerate(zip(got, expected)):
            self.assertLessEqual(abs(g - e), self.TOL,
                                 f"channel {ch}: got {got}, expected {expected}")
        self.assertLess(max(got), 255, f"opaque splat clipped to white: {got}")

    def test_residual_transmittance_scales_the_background(self):
        """A half-alpha splat alone leaves the background at HALF strength behind it:
        final = cr*0.5 + bg*0.5 -- not bg + cr*0.5 (the pre-fix behaviour)."""
        expected = tuple(round(0.5 * c * 255.0 + 0.5 * b * 255.0)
                         for c, b in zip(COL_GLASS, BG_SKY))
        got = _centre(_render(self.half, BG_SKY))
        for ch, (g, e) in enumerate(zip(got, expected)):
            self.assertLessEqual(abs(g - e), self.TOL,
                                 f"channel {ch}: got {got}, expected {expected}")
        # and the defective value is far away -- this is what the fix must NOT regress to
        defective = tuple(round(0.5 * c * 255.0 + b * 255.0)
                          for c, b in zip(COL_GLASS, BG_SKY))
        self.assertTrue(any(abs(g - d) > 8 for g, d in zip(got, defective)),
                        f"output matches the unattenuated-background behaviour: {got}")

    def test_two_splats_full_occlusion_zeroes_the_background(self):
        """A half-alpha splat over an opaque one: trans_end == 0, so the background
        contributes nothing -- final = 0.5*(near + far), independent of bg."""
        buf = np.concatenate([_centred_splat(2000.0, 720.0, COL_GROUND, 1.0),
                              _centred_splat(1000.0, 360.0, (0.9, 0.2, 0.1), 0.5)])
        expected = tuple(round(0.5 * (a + b) * 255.0)
                         for a, b in zip((0.9, 0.2, 0.1), COL_GROUND))
        for bg in (BG_SKY, BG_BLACK):
            got = _centre(_render(buf, bg))
            for ch, (g, e) in enumerate(zip(got, expected)):
                self.assertLessEqual(abs(g - e), self.TOL,
                                     f"bg={bg} channel {ch}: got {got}, expected {expected}")

    def test_black_background_renders_the_pure_splat_series(self):
        """bg=(0,0,0): the term the fix adds is exactly 0.0, so the output must be
        the closed-form additive series -- the value the pre-fix kernel also
        produced (its defect was invisible at black). This is the compatibility
        pin behind the pre/post byte-identity evidence."""
        for buf, series in (
                (self.opaque, COL_GROUND),
                (self.half, tuple(0.5 * c for c in COL_GLASS))):
            expected = tuple(round(c * 255.0) for c in series)
            got = _centre(_render(buf, BG_BLACK))
            for ch, (g, e) in enumerate(zip(got, expected)):
                self.assertLessEqual(abs(g - e), self.TOL,
                                     f"channel {ch}: got {got}, expected {expected}")


if __name__ == "__main__":
    if not _HAS_GPU:
        print("SKIP (loud): no CUDA device -- _composite is a GPU kernel, the "
              "background-transmittance gate cannot run on this host.", flush=True)
        sys.exit(2)
    unittest.main(verbosity=2)
