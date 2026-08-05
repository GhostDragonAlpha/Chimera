"""interfaces.py -- Stage 18: multi-interface refraction and the curved floor. The LAST original
Part II item, and most of it was already built without knowing it.

THE TELESCOPING THEOREM, which is why Stage 4 survives intact. Across any stack of PARALLEL
interfaces, Snell's law chains: n1 sin(th1) = n2 sin(th2) = ... = nk sin(thk). The invariant
n sin(th) means the EXIT DIRECTION depends only on the first and last medium -- intermediate
layers bend the ray and then unbend it. So Stage 4's single-Snell kernel, fed eta = n_first /
n_final, is ANGLE-EXACT for any parallel stack. What a stack adds is only a LATERAL WALK-OFF:

    d_layer = t * sin(th1 - th2) / cos(th2)        (the classic slab displacement)

which accumulates per layer and never rotates. Its VISIBILITY is boundable the same way chain
depth was: a walk-off under one floor-grid cell cannot change which cell a ray reads, so a stack
is renderable by the existing kernel whenever sum(d) < cell -- derived, per scene, not assumed.

ICE COMES FREE, and it is the stage's never-fitted prediction. Lorentz-Lorenz is additive in
MASS, so a phase change costs nothing: water's molar refraction at ice's density (917 kg/m^3)
predicts n_ice = 1.3034 against the measured 1.31 -- 0.5%, with no ice constant cited anywhere.

THE CURVED FLOOR, which Stage 4 scoped out and aSaltOcean actually has (mean depth 2861 m,
deepest point 8582 m -- the plane was always an approximation). THE DECLARED MODEL is one
fixed-point step on the floor's own height field: intersect the mean plane, read that cell's
published height, re-intersect at that height, read the colour there. The residual is second
order in (floor slope x height deviation); the EXACT referee (analytic ray-sphere intersection)
measures what the step buys. On a flat floor the step recomputes identical numbers, so every
existing caller stays bit-identical -- the extension is invisible until a floor actually curves.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_STORY = _ROOT / "story"
if str(_STORY) not in sys.path:
    sys.path.insert(0, str(_STORY))

from ChimeraEngine.core.optics import refract_dir  # noqa: E402


def trace_stack(d0, n_stack, thicknesses):
    """The REFEREE: march a ray through parallel interfaces exactly. n_stack = [n1, n2, ...],
    thicknesses = [t2, ...] for the interior layers (first medium extends to the first surface,
    last medium is semi-infinite). Returns (exit_direction, lateral_offset_vector)."""
    d = np.asarray(d0, dtype=np.float64)
    d = d / np.linalg.norm(d)
    nrm = np.array([0.0, 0.0, 1.0])
    p = np.zeros(3)
    for i in range(len(n_stack) - 1):
        t = refract_dir(np.array([-d]), np.array([nrm]), n_stack[i] / n_stack[i + 1])[0]
        if not np.isfinite(t[2]):
            return None, None
        d = t
        if i + 1 < len(n_stack) - 1:
            s = thicknesses[i] / abs(d[2])
            p = p + d * s
    straight = np.asarray(d0, dtype=np.float64)
    straight = straight / np.linalg.norm(straight)
    drop = sum(thicknesses)
    p_straight = straight * (drop / abs(straight[2])) if drop > 0 else np.zeros(3)
    return d, (p - p_straight)[:2]


def snell_invariant(n, cos_theta):
    """n sin(theta) -- the quantity a parallel stack conserves."""
    return float(n) * math.sqrt(max(0.0, 1.0 - float(cos_theta) ** 2))


def slab_walkoff(t: float, n1: float, n2: float, cos_i: float) -> float:
    """The HORIZONTAL (floor-plane) displacement a slab of thickness t adds:
    t (tan th1 - tan th2). The textbook 'beam displacement' is the PERPENDICULAR offset,
    smaller by cos(th1) -- the conventions differ by a real factor and the horizontal one is the
    one that decides which floor CELL a ray reads, so it is the one the visibility bound needs.
    Stated because comparing across the two conventions silently costs a cos(theta)."""
    s1 = math.sqrt(max(0.0, 1.0 - cos_i * cos_i))
    s2 = (n1 / n2) * s1
    if s2 >= 1.0:
        return float("inf")
    th1, th2 = math.asin(min(1.0, s1)), math.asin(min(1.0, s2))
    return float(t) * (math.tan(th1) - math.tan(th2))


def max_invisible_slab(cell: float, n1: float, n2: float, cos_i: float) -> float:
    """The thickest slab whose walk-off stays under one grid cell -- the derived visibility
    bound, same discipline as the chain-depth bound. Below it the existing single-eta kernel
    is not merely angle-exact but CELL-exact."""
    d1 = slab_walkoff(1.0, n1, n2, cos_i)
    if d1 <= 0.0 or not math.isfinite(d1):
        return float("inf") if d1 == 0.0 else 0.0
    return float(cell) / d1


def bowl_floor(n_side: int, span: float, z_mean: float, sag: float):
    """A spherical-cap floor for the tests: z(x,y) = z_mean + sag*(1 - (r/r_max)^2) -- deepest at
    the rim (sag < 0 bulges down at centre when sag negative ... sign chosen by caller). Returns
    (positions (N,3), and the analytic sphere (centre_z, radius) for the exact referee)."""
    f = np.linspace(-span / 2, span / 2, n_side)
    fx, fy = np.meshgrid(f, f)
    r2 = fx ** 2 + fy ** 2
    r_max2 = 2.0 * (span / 2) ** 2
    z = z_mean + sag * (1.0 - r2 / r_max2)
    pos = np.stack([fx.ravel(), fy.ravel(), z.ravel()], axis=1)
    # The paraboloid z = z0 + sag - sag*r^2/rm2 osculates a sphere of radius R = rm2/(2*sag)
    R_osc = r_max2 / (2.0 * abs(sag)) if sag != 0 else float("inf")
    return pos, (z_mean + sag, R_osc)


def hit_paraboloid(p0, d, z_mean: float, sag: float, r_max2: float, iters: int = 60):
    """The EXACT curved-floor referee: intersect a ray with z = z_mean + sag(1 - r^2/rm2) by
    bisection on the signed height difference -- robust, no small-slope assumption anywhere."""
    p0 = np.asarray(p0, dtype=np.float64)
    d = np.asarray(d, dtype=np.float64)
    d = d / np.linalg.norm(d)

    def gap(s):
        q = p0 + d * s
        zf = z_mean + sag * (1.0 - (q[0] ** 2 + q[1] ** 2) / r_max2)
        return q[2] - zf

    lo, hi = 0.0, 1.0
    while gap(hi) > 0.0 and hi < 1e6:
        hi *= 2.0
    if gap(hi) > 0.0:
        return None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if gap(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return p0 + d * (0.5 * (lo + hi))


def plane_then_step(p0, d, z_mean: float, sag: float, r_max2: float):
    """THE DECLARED MODEL, host-side twin of the kernel's one fixed-point step: intersect the
    mean plane, read the floor height THERE, re-intersect at that height. Returns (hit_plane,
    hit_stepped) so the improvement is measurable, not asserted."""
    p0 = np.asarray(p0, dtype=np.float64)
    d = np.asarray(d, dtype=np.float64)
    d = d / np.linalg.norm(d)
    s0 = (z_mean - p0[2]) / d[2]
    h0 = p0 + d * s0
    z1 = z_mean + sag * (1.0 - (h0[0] ** 2 + h0[1] ** 2) / r_max2)
    s1 = (z1 - p0[2]) / d[2]
    return h0, p0 + d * s1
