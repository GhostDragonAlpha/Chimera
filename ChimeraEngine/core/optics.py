"""optics.py -- THE REFEREE for the specular pass, and the declared model it referees.

THE TWO-FORCE READER, light half (2026-08-05; theory: docs/THE_TWO_FORCES.md). The renderer's
specular term is computed per GRAIN in `ParticleEngine.gpu_pipeline._p2s` -- one grain is one
facet is one light slot -- in float32 on the GPU. This module is the SAME declared model,
implemented independently in float64 on the CPU, so the two can disagree. The current renderer is
Lambertian-only and cannot judge a capability it does not have, which is why the referee is BUILT
rather than assumed.

THE DECLARED MODEL (each piece named, so the kernel-vs-referee test is about implementation,
never about silent model drift):

    specular  = F * D * G / (4 * cos_v * cos_l)            Cook-Torrance geometry
    D         = exp(-tan^2(th_h)/s^2) / (pi s^2 cos^4 th_h) Beckmann -- a GAUSSIAN slope
                                                            distribution, which is exactly what
                                                            Cox-Munk measured on a wind-driven sea
                                                            and what aSaltOcean publishes as
                                                            surface_slope_mean
    F         = F0 + (1-F0)(1 - cos(v,h))^5                 Schlick's Fresnel; F0 comes from the
                                                            membrane's own density through
                                                            story.matter.refractive_index /
                                                            fresnel_f0 -- NEVER computed here
                                                            (one source of truth, ast-enforced by
                                                            ChimeraEngine/test_optics.py)
    G         = G1(cos_v) * G1(cos_l)                       separable Smith -- a declared model
                                                            choice (height-correlation ignored)
    G1(c)     = 1 / (1 + Lambda(a)),  a = 1/(s tan th)      EXACT Beckmann Lambda, no fitted
    Lambda(a) = (exp(-a^2)/(a sqrt(pi)) - erfc(a)) / 2      rational approximation anywhere

The grain's normal is the SMOOTH surface normal the emit derived (a sphere's radial, a terrain
cell's slope normal); s is SUB-grain slope spread, the membrane's own published statistic. There
is no double count: resolved geometry lives in the normals, unresolved geometry lives in s.

INPUT GATES, and why zero disables rather than defaults: a grain with SPEC_F0 == 0 or
SPEC_SLOPE == 0 has published nothing, and a fallback would be an assumption wearing a hat. The
kernel applies the same gates, so "no data" renders EXACTLY as before the pass existed.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

# The house idiom for reaching story/matter.py (walker.py:55): the story DIRECTORY goes on the
# path and `matter` is imported as itself. A plain `from story import matter` loses to
# ChimeraEngine/story.py whenever a script runs from inside ChimeraEngine/, because a regular
# module beats a namespace package no matter where each sits on sys.path.
_ROOT = Path(__file__).resolve().parents[2]
_STORY = _ROOT / "story"
if str(_STORY) not in sys.path:
    sys.path.insert(0, str(_STORY))

from matter import PX, PY, PZ, NX, NY, NZ, SPEC_F0, SPEC_SLOPE  # noqa: E402

# ── DERIVED CUTOFFS (mirrored in the kernel; same argument as gpu_pipeline.FOOTPRINT) ────────────
# EXP_CUTOFF: drop the lobe when tan^2/s^2 > 40. exp(-40) = 4.2e-18; with the largest prefactor
# 1/(pi s^2 ch^4) reachable at that t for s in [0.01, 1], D stays under ~1e-14 -- orders of
# magnitude below half a 0-255 quantisation step (1/510). Change the image depth and this tracks.
EXP_CUTOFF = 40.0
# A_CUTOFF: treat G1 as 1 when a = 1/(s tan th) > 6. Lambda(6) ~ 2e-17, below float32's own
# resolution of (1 + Lambda), so the early-out is exact at the precision the kernel computes in.
A_CUTOFF = 6.0

# ── PRE-REGISTERED TOLERANCES for kernel-vs-referee (WRITTEN BEFORE THE FIRST COMPARISON RAN) ────
# The kernel is ~25 float32 ops. The dominating term is the exponent: t = tan^2/s^2 <= 40 carries
# relative error ~1e-6 through ~10 ops -> absolute exponent error ~4e-4 -> relative error of D
# ~4e-4. F and G are O(1) with ~1e-5 relative each; CUDA's exp/erfc are within a few ulp of libm.
# Specular magnitudes for our membranes peak O(0.1-1) in colour units, so the expected worst-case
# disagreement is ~1e-4 absolute. The gates are set at 10x that headroom -- and far below any
# actual formula mismatch, which is O(10-100%):
EPS_KERNEL_MAX = 1e-3      # max |kernel - referee| over all grains, per channel
EPS_KERNEL_MED = 1e-4      # median |difference| over grains where the referee is nonzero

# ── PRE-REGISTERED CLOSURE TOLERANCES (Stage 0/3; stated before measuring) ───────────────────────
# n from density alone vs an independently sourced n: 1% (salinity adds refractivity slightly
# beyond its density effect; pure-water LL landed 0.05% from literature). F0 vs aSaltOcean's
# published sunglint_intensity: 5% (F0 is quadratic in (n-1), doubling the relative width).
EPS_N_REL = 0.01
EPS_F0_REL = 0.05

_erfc = np.vectorize(math.erfc)


def smith_g1(cos_t: np.ndarray, s: np.ndarray) -> np.ndarray:
    """G1 for Beckmann via the EXACT Lambda -- float64, vectorised. cos_t > 0 assumed (gated
    by the caller); s > 0 assumed (zero slope never reaches here -- the gate refuses it)."""
    cos_t = np.atleast_1d(np.asarray(cos_t, dtype=np.float64))
    s = np.broadcast_to(np.asarray(s, dtype=np.float64), cos_t.shape)
    sin2 = np.clip(1.0 - cos_t * cos_t, 0.0, None)
    tan_t = np.sqrt(sin2) / np.maximum(cos_t, 1e-300)
    g1 = np.ones_like(cos_t)
    live = tan_t > 0.0
    if np.any(live):
        a = 1.0 / (s[live] * tan_t[live])
        lam = np.zeros_like(a)
        small = a <= A_CUTOFF
        if np.any(small):
            asm = a[small]
            lam[small] = 0.5 * (np.exp(-asm * asm) / (asm * math.sqrt(math.pi)) - _erfc(asm))
        g1[live] = 1.0 / (1.0 + lam)
    return g1


def specular_reference(buf: np.ndarray, cam_pos, light_dir, light_rgb) -> np.ndarray:
    """The float64 referee: per-grain specular colour ADDITIONS for the declared model above.

    buf       (N, 28) grain buffer (story.matter layout)
    cam_pos   (3,) eye position, same frame as the buffer
    light_dir (3,) direction FROM the scene TOWARD the light (normalised here)
    light_rgb (3,) light colour, premultiplied by the same exposure lit() used

    Returns (N, 3) float64 -- zero rows wherever any gate refuses (no normal, no published F0 or
    slope, light or camera below the horizon). The kernel must agree within EPS_KERNEL_*.
    """
    b = np.asarray(buf, dtype=np.float64)
    n_grains = len(b)
    out = np.zeros((n_grains, 3), dtype=np.float64)

    p = b[:, [PX, PY, PZ]]
    nrm = b[:, [NX, NY, NZ]]
    f0 = b[:, SPEC_F0]
    s = b[:, SPEC_SLOPE]

    nn = np.linalg.norm(nrm, axis=1)
    l = np.asarray(light_dir, dtype=np.float64)
    l = l / np.linalg.norm(l)
    lr = np.asarray(light_rgb, dtype=np.float64)

    v = np.asarray(cam_pos, dtype=np.float64)[None, :] - p
    vn = np.linalg.norm(v, axis=1)

    live = (nn > 1e-6) & (f0 > 0.0) & (s > 0.0) & (vn > 0.0)
    if not np.any(live):
        return out
    i = np.where(live)[0]

    nh = nrm[i] / nn[i, None]
    vh = v[i] / vn[i, None]
    cos_v = np.einsum("ij,ij->i", nh, vh)
    cos_l = nh @ l
    face = (cos_v > 0.0) & (cos_l > 0.0)
    if not np.any(face):
        return out
    i = i[face]
    nh = nh[face]; vh = vh[face]
    cos_v = cos_v[face]; cos_l = cos_l[face]
    si = s[i]; f0i = f0[i]

    h = vh + l[None, :]
    h = h / np.linalg.norm(h, axis=1)[:, None]
    ch = np.einsum("ij,ij->i", nh, h)
    ok = ch > 0.0
    i = i[ok]; nh = nh[ok]; vh = vh[ok]
    cos_v = cos_v[ok]; cos_l = cos_l[ok]; si = si[ok]; f0i = f0i[ok]
    h = h[ok]; ch = ch[ok]

    ch2 = ch * ch
    t = (1.0 - ch2) / (ch2 * si * si)
    keep = t <= EXP_CUTOFF                      # the kernel's derived lobe cutoff, mirrored
    i = i[keep]; vh = vh[keep]; cos_v = cos_v[keep]; cos_l = cos_l[keep]
    si = si[keep]; f0i = f0i[keep]; h = h[keep]; ch = ch[keep]; ch2 = ch2[keep]; t = t[keep]
    if len(i) == 0:
        return out

    d = np.exp(-t) / (math.pi * si * si * ch2 * ch2)
    cvh = np.clip(np.einsum("ij,ij->i", vh, h), 0.0, 1.0)
    f = f0i + (1.0 - f0i) * (1.0 - cvh) ** 5
    g = smith_g1(cos_v, si) * smith_g1(cos_l, si)
    spec = f * d * g / (4.0 * cos_v * cos_l)

    out[i] = spec[:, None] * lr[None, :]
    return out
