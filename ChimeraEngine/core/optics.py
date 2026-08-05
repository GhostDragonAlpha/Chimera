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

from matter import (PX, PY, PZ, NX, NY, NZ, SPEC_F0, SPEC_SLOPE,  # noqa: E402
                    REFRACT, CR, CG, CB)

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

# ── PRE-REGISTERED TOLERANCES for the LENSING CHAIN (Stages 4/5/7; written before any run) ───────
# Refraction hit points: pure geometry (a Snell bend and one plane intersection) in float32 vs
# float64 -- ~15 ops on O(1) quantities, expected ~1e-6; gate at 10x headroom in scene units.
EPS_HIT = 1e-4
# Transmitted colour: same float32-vs-float64 argument as EPS_KERNEL_MAX, same gate.
EPS_TRANS_MAX = 1e-3
# Grid-lookup fidelity: the kernel reads the floor through a cell grid; the true-nearest check may
# disagree only in the boundary band, whose width is the float error (~1e-5) against a cell of
# ~0.03 -- fraction ~0.1%. Gate: >= 99% of lit grains agree exactly.
EPS_GRID_AGREE = 0.99
# Caustic band positions: the deposit is a histogram, so a peak is located to one cell; gate at
# two cells to cover the band's own width.
EPS_CAUSTIC_CELLS = 2.0
# Bounce cap: K is DERIVED per receiver as the smallest prefix (sources ranked by upper-bound
# contribution) whose remaining tail bound is < 1% of the prefix -- so capped-vs-uncapped must
# agree within that same 1%, plus float slack.
EPS_BOUNCE_REL = 0.011
# Bounce cost linearity (the falsifier's own number): fit R^2 over an N sweep at the derived K.
EPS_BOUNCE_R2 = 0.9

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


# ═══ THE LENSING CHAIN (Stages 4/5/7): refraction, caustics, dispersion ══════════════════════════
# THE DECLARED MODEL. A refractive grain is an INTERFACE: the view ray bends by Snell at the
# grain's own density-derived n and continues straight to the membrane-published floor plane,
# where it picks up the floor's colour, attenuated by the membrane's own absorption over the
# refracted path length, weighted by the transmitted Fresnel fraction (1 - F(cos_v)) -- the
# energy the specular term did NOT reflect. Dispersion is the SAME pass with three measured
# indices instead of one (story matter.WATER_N_BY_CHANNEL); a caustic is the SAME refraction
# applied to the LIGHT's rays, deposited on the floor -- flux concentration emerges from the
# deposit density, and the analytic det-J referee checks where the bands must sit.
#
# THE SCOPE, stated: ONE interface, a PLANE floor published by the membrane. Multi-interface
# paths and curved floors are where the plane assumption breaks first -- that boundary is the
# falsifier's expected failure direction, on record in docs/THE_TWO_FORCES.md Part II.

def refract_dir(v_unit: np.ndarray, n_unit: np.ndarray, eta: float) -> np.ndarray:
    """Snell in vector form, float64, vectorised. v_unit points grain -> CAMERA; the incident
    ray is d = -v. Returns (N,3) refracted directions; rows are NaN where total internal
    reflection refuses transmission (an eta > 1 path only -- air-to-water never TIRs).

        t = eta*d + (eta*c1 - c2)*n,  c1 = n.v,  c2 = sqrt(1 - eta^2 (1 - c1^2))
    """
    v = np.asarray(v_unit, dtype=np.float64)
    n = np.asarray(n_unit, dtype=np.float64)
    d = -v
    c1 = np.einsum("ij,ij->i", n, v)
    k = 1.0 - eta * eta * (1.0 - c1 * c1)
    t = np.full_like(v, np.nan)
    ok = k >= 0.0
    c2 = np.sqrt(np.clip(k, 0.0, None))
    t[ok] = eta * d[ok] + (eta * c1[ok] - c2[ok])[:, None] * n[ok]
    t[ok] /= np.linalg.norm(t[ok], axis=1)[:, None]
    return t


def refraction_reference(buf: np.ndarray, cam_pos, eta_rgb, floor_z: float, absorb_rgb,
                         grid_origin, cell: float, grid_rgb: np.ndarray,
                         grid_has: np.ndarray):
    """The float64 referee for the refraction pass: per refractive grain, per colour channel:
    Snell -> exact plane hit -> the SAME cell lookup the kernel uses (in float64) -> Beer-Lambert
    over the refracted path -> (1 - F(cos_v)) energy split.

    Returns (adds, hits): adds (N,3) transmitted colour additions; hits (N,3,2) per-channel
    floor hit points, NaN where the chain refused (no interface flag, back-face, upward ray,
    off-grid, empty cell)."""
    b = np.asarray(buf, dtype=np.float64)
    n_grains = len(b)
    adds = np.zeros((n_grains, 3), dtype=np.float64)
    hits = np.full((n_grains, 3, 2), np.nan, dtype=np.float64)
    p = b[:, [PX, PY, PZ]]
    nrm = b[:, [NX, NY, NZ]]
    f0 = b[:, SPEC_F0]
    rf = b[:, REFRACT]

    nn = np.linalg.norm(nrm, axis=1)
    v = np.asarray(cam_pos, dtype=np.float64)[None, :] - p
    vn = np.linalg.norm(v, axis=1)
    live = (rf > 0.0) & (nn > 1e-6) & (vn > 0.0)
    if not np.any(live):
        return adds, hits
    i = np.where(live)[0]
    nh = nrm[i] / nn[i, None]
    vh = v[i] / vn[i, None]
    cosv = np.einsum("ij,ij->i", nh, vh)
    face = cosv > 0.0
    i = i[face]; nh = nh[face]; vh = vh[face]; cosv = cosv[face]
    if len(i) == 0:
        return adds, hits

    fr = f0[i] + (1.0 - f0[i]) * (1.0 - cosv) ** 5      # Fresnel of the VIEW ray (Schlick)
    trans_w = 1.0 - fr
    gx0, gy0 = float(grid_origin[0]), float(grid_origin[1])
    ny, nx = grid_has.shape
    pz = p[i]
    for c in range(3):
        t = refract_dir(vh, nh, float(eta_rgb[c]))
        down = np.isfinite(t[:, 2]) & (t[:, 2] < 0.0)
        s = np.full(len(i), np.nan)
        s[down] = (float(floor_z) - pz[down, 2]) / t[down, 2]
        ok = down & (s > 0.0)
        hx = pz[:, 0] + t[:, 0] * s
        hy = pz[:, 1] + t[:, 1] * s
        hits[i[ok], c, 0] = hx[ok]
        hits[i[ok], c, 1] = hy[ok]
        with np.errstate(invalid="ignore"):
            ix = np.floor((hx - gx0) / cell)
            iy = np.floor((hy - gy0) / cell)
        ix = np.nan_to_num(ix, nan=-1).astype(np.int64)
        iy = np.nan_to_num(iy, nan=-1).astype(np.int64)
        inb = ok & (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        idx = np.where(inb)[0]
        if len(idx) == 0:
            continue
        has = grid_has[iy[idx], ix[idx]] > 0
        idx = idx[has]
        if len(idx) == 0:
            continue
        tcol = grid_rgb[iy[idx], ix[idx], c].astype(np.float64)
        att = np.exp(-float(absorb_rgb[c]) * s[idx])
        adds[i[idx], c] = trans_w[idx] * att * tcol
    return adds, hits


def build_floor_grid(floor_buf: np.ndarray, cell: float):
    """Bin floor grains into the XY cell grid the kernel reads. Returns
    (origin_xy, cell, grid_rgb float32 (ny,nx,3), grid_has uint8 (ny,nx)). Where two grains land
    in one cell the last one wins -- the tests build floors one grain per cell on purpose."""
    b = np.asarray(floor_buf, dtype=np.float64)
    x, y = b[:, PX], b[:, PY]
    gx0 = float(x.min()) - cell * 0.5
    gy0 = float(y.min()) - cell * 0.5
    nx = int(np.ceil((float(x.max()) - gx0) / cell)) + 1
    ny = int(np.ceil((float(y.max()) - gy0) / cell)) + 1
    rgb = np.zeros((ny, nx, 3), dtype=np.float32)
    has = np.zeros((ny, nx), dtype=np.uint8)
    ix = np.floor((x - gx0) / cell).astype(np.int64)
    iy = np.floor((y - gy0) / cell).astype(np.int64)
    rgb[iy, ix, 0] = b[:, CR]
    rgb[iy, ix, 1] = b[:, CG]
    rgb[iy, ix, 2] = b[:, CB]
    has[iy, ix] = 1
    return (gx0, gy0), cell, rgb, has


def caustic_deposit(surf_pos: np.ndarray, surf_nrm: np.ndarray, light_dir, eta: float,
                    floor_z: float, grid_origin, cell: float, shape):
    """Stage 5: refract the LIGHT's rays at every surface grain and deposit unit energy on the
    floor grid. The caustic EMERGES from deposit density; nothing here knows what a band is.
    Conservation is by construction: hist.sum() == n_deposited exactly, because each ray
    deposits once or not at all -- a caustic is redistribution, never creation."""
    l = np.asarray(light_dir, dtype=np.float64)
    l = l / np.linalg.norm(l)                      # points TOWARD the light; incidence is -l
    n = np.asarray(surf_nrm, dtype=np.float64)
    n = n / np.linalg.norm(n, axis=1)[:, None]
    p = np.asarray(surf_pos, dtype=np.float64)
    t = refract_dir(np.broadcast_to(l, n.shape), n, eta)
    down = np.isfinite(t[:, 2]) & (t[:, 2] < 0.0)
    s = (float(floor_z) - p[down, 2]) / t[down, 2]
    ok = s > 0.0
    hx = p[down][ok, 0] + t[down][ok, 0] * s[ok]
    hy = p[down][ok, 1] + t[down][ok, 1] * s[ok]
    ny, nx = shape
    ix = np.floor((hx - float(grid_origin[0])) / cell).astype(np.int64)
    iy = np.floor((hy - float(grid_origin[1])) / cell).astype(np.int64)
    inb = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    hist = np.zeros(shape, dtype=np.float64)
    np.add.at(hist, (iy[inb], ix[inb]), 1.0)
    return hist, int(inb.sum())


def sine_caustic_zeros(amp: float, k: float, eta: float, depth: float):
    """The ANALYTIC referee for the sine-wave caustic (small slope): a surface with slope
    s(x) = A k cos(kx) bends a vertical ray by (1 - eta) s, so the floor map is
    X(x) = x + D (1-eta) A k cos(kx) and a caustic sits where dX/dx = 0:

        sin(k x*) = 1 / (D (1-eta) A k^2)

    Returns the floor X of the first-period band pair, or None when the geometry focuses too
    weakly to fold (argument > 1 -- no caustic exists, also an answer)."""
    g = depth * (1.0 - eta) * amp * k * k
    if g < 1.0:
        return None
    s0 = math.asin(1.0 / g)
    xs = (s0 / k, (math.pi - s0) / k)
    return [x + depth * (1.0 - eta) * amp * k * math.cos(k * x) for x in xs]


# ═══ STAGE 6: ONE-BOUNCE INTERREFLECTION (diffuse gather, budget-capped) ═════════════════════════
# THE DECLARED MODEL AND ITS SCOPE. One Lambertian bounce: emitting grain j sends radiance L_j to
# receiver i, which gains irradiance L_j cos(th_j) cos(th_i) A_j / (pi r^2) and re-emits through
# its own albedo exactly as lit() does (albedo * E / pi). SPECULAR-to-specular chains are NOT this
# stage -- stated in docs/THE_TWO_FORCES.md Part II. The cap K is DERIVED, never chosen: sources
# rank per receiver by the r^2 upper bound L_j A_j / (pi r^2) (cosines <= 1), and K is the
# smallest prefix whose remaining tail bound is under 1% of the prefix sum. The 1% IS the
# construction; EPS_BOUNCE_REL is that number plus float slack.

def _bounce_one(i, j, p, n, L, A, alb):
    d = p[j] - p[i]
    r2 = np.einsum("ij,ij->i", d, d)
    r = np.sqrt(np.maximum(r2, 1e-300))
    du = d / r[:, None]
    ci = np.clip(du @ n[i], 0.0, None)
    cj = np.clip(-np.einsum("ij,ij->i", n[j], du), 0.0, None)
    e = float(np.sum(L[j] * ci * cj * A[j] / (math.pi * np.maximum(r2, 1e-300))))
    return alb[i] * e / math.pi


def bounce_reference(pos, nrm, area, radiance, albedo):
    """Uncapped O(N^2) float64 referee. radiance (N,): each grain's emitted luminance (zero for
    non-emitters); area (N,); albedo (N,3). Returns (N,3) colour additions."""
    p = np.asarray(pos, np.float64)
    n = np.asarray(nrm, np.float64)
    n = n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-300)
    L = np.asarray(radiance, np.float64)
    A = np.asarray(area, np.float64)
    alb = np.asarray(albedo, np.float64)
    src = np.where(L > 0.0)[0]
    add = np.zeros((len(p), 3), np.float64)
    for i in range(len(p)):
        j = src[src != i]
        if len(j):
            add[i] = _bounce_one(i, j, p, n, L, A, alb)
    return add


def derive_bounce_cap(pos, radiance, area, frac: float = 0.01):
    """K per receiver, DERIVED: the smallest prefix of upper-bound-ranked sources whose remaining
    tail bound is < frac of the prefix sum. Returns the per-receiver source index lists."""
    p = np.asarray(pos, np.float64)
    L = np.asarray(radiance, np.float64)
    A = np.asarray(area, np.float64)
    src = np.where(L > 0.0)[0]
    lists = []
    for i in range(len(p)):
        j = src[src != i]
        if len(j) == 0:
            lists.append(j)
            continue
        d = p[j] - p[i]
        r2 = np.einsum("ij,ij->i", d, d)
        ub = L[j] * A[j] / (math.pi * np.maximum(r2, 1e-300))
        order = np.argsort(ub)[::-1]
        cum = np.cumsum(ub[order])
        tail = cum[-1] - cum
        need = tail < frac * np.maximum(cum, 1e-300)
        k = int(np.argmax(need)) + 1 if need.any() else len(j)
        lists.append(j[order[:k]])
    return lists


def bounce_gather_guaranteed(pos, nrm, area, radiance, albedo, frac: float = 0.01):
    """The gather with a CORRECT derived guarantee. The first cap construction compared the tail
    BOUND against the prefix BOUND, and grazing receivers refuted it (bounds use cos <= 1, so the
    actual dropped fraction can exceed frac when the kept actuals are cosine-suppressed). The
    honest rule is a-posteriori: walk sources in bound order, accumulate the ACTUAL energy, stop
    when the remaining tail bound is under frac of the actual gathered so far. Then

        dropped_actual <= tail_bound <= frac * kept_actual

    holds by construction -- the relative error is <= frac, provably, per receiver. Returns
    (adds, pairs_used). At near-uniform contribution spectra the rule keeps nearly every pair --
    that is the scene being hard, not the rule failing, and pairs_used says so out loud."""
    p = np.asarray(pos, np.float64)
    n = np.asarray(nrm, np.float64)
    n = n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-300)
    L = np.asarray(radiance, np.float64)
    A = np.asarray(area, np.float64)
    alb = np.asarray(albedo, np.float64)
    src = np.where(L > 0.0)[0]
    add = np.zeros((len(p), 3), np.float64)
    pairs = 0
    for i in range(len(p)):
        j = src[src != i]
        if len(j) == 0:
            continue
        d = p[j] - p[i]
        r2 = np.einsum("ij,ij->i", d, d)
        r = np.sqrt(np.maximum(r2, 1e-300))
        du = d / r[:, None]
        ci = np.clip(du @ n[i], 0.0, None)
        cj = np.clip(-np.einsum("ij,ij->i", n[j], du), 0.0, None)
        term = L[j] * A[j] / (math.pi * np.maximum(r2, 1e-300))
        order = np.argsort(term)[::-1]
        bound = term[order]
        actual = (term * ci * cj)[order]
        cum = np.cumsum(actual)
        tail = bound[::-1].cumsum()[::-1] - bound          # tail bound AFTER each prefix
        stop = tail <= frac * np.maximum(cum, 1e-300)
        k = int(np.argmax(stop)) + 1 if stop.any() else len(bound)
        pairs += k
        add[i] = alb[i] * float(cum[k - 1]) / math.pi
    return add, pairs


def bounce_gather(pos, nrm, area, radiance, albedo, lists):
    """The capped gather -- the same physics as the referee, over the derived prefix only.
    Cost is sum(K_i): linear in N at fixed source density, which is the Stage 6 cost claim."""
    p = np.asarray(pos, np.float64)
    n = np.asarray(nrm, np.float64)
    n = n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-300)
    L = np.asarray(radiance, np.float64)
    A = np.asarray(area, np.float64)
    alb = np.asarray(albedo, np.float64)
    add = np.zeros((len(p), 3), np.float64)
    for i, j in enumerate(lists):
        if len(j):
            add[i] = _bounce_one(i, j, p, n, L, A, alb)
    return add
