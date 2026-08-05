"""mirrors.py -- Stage 19: curved-mirror focusing. Stage 5's machinery pointed at reflection.

A caustic never cared whether the bend came from Snell or from a mirror -- it is the convergence
of a ray map, and the deposition instrument measures it either way. The only physics that changes
is the GAIN: refraction bends a vertical ray by (1 - eta) * slope (Stage 5), a mirror by
2 * slope (Stage 16's measured mirror gain). So the sine-mirror caustic condition is

    sin(k x*) = 1 / (2 D A k^2)          vs refraction's 1 / (D (1-eta) A k^2)

and the SAME surface over the SAME drop must place its mirror bands closer by exactly
(1 - eta)/2 -- a cross-stage identity connecting Stages 5, 16 and 19 with nothing new cited.

THE SPHERICAL MIRROR is the never-fitted classic: parallel rays off a concave cap of radius R
converge at R/2. The deposition histogram must put its on-axis peak there -- within an aperture
DERIVED from the instrument, not assumed: longitudinal spherical aberration is
dz ~ R a^2 / (2 (R^2 - a^2)) ~ a^2/(2R), so the aperture that keeps the blur under one cell is
a < sqrt(2 R cell). Open the aperture past it and the peak must WALK toward the mirror
(marginal rays focus short) -- the aberration is a measured prediction too, not an excuse.
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


def reflect_rays(d, nrm):
    """d - 2(d.n)n, vectorised, unit in = unit out."""
    d = np.asarray(d, dtype=np.float64)
    n = np.asarray(nrm, dtype=np.float64)
    n = n / np.linalg.norm(n, axis=1)[:, None]
    return d - 2.0 * np.einsum("ij,ij->i", d, n)[:, None] * n


def mirror_deposit(surf_pos, surf_nrm, light_dir, screen_z: float, origin, cell: float, shape):
    """Reflect the light's rays at every surface point and deposit on the screen plane.
    Conservation is by construction, exactly as Stage 5's refractive deposit."""
    l = np.asarray(light_dir, dtype=np.float64)
    l = l / np.linalg.norm(l)
    d0 = np.tile(-l, (len(surf_pos), 1))              # incident ray, travelling with the light
    d = reflect_rays(d0, surf_nrm)
    p = np.asarray(surf_pos, dtype=np.float64)
    dz = d[:, 2]
    live = np.abs(dz) > 1e-12
    s = (float(screen_z) - p[live, 2]) / dz[live]
    fwd = s > 0.0
    hx = p[live][fwd, 0] + d[live][fwd, 0] * s[fwd]
    hy = p[live][fwd, 1] + d[live][fwd, 1] * s[fwd]
    ny, nx = shape
    ix = np.floor((hx - float(origin[0])) / cell).astype(np.int64)
    iy = np.floor((hy - float(origin[1])) / cell).astype(np.int64)
    inb = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    hist = np.zeros(shape, dtype=np.float64)
    np.add.at(hist, (iy[inb], ix[inb]), 1.0)
    return hist, int(inb.sum())


def sine_mirror_zeros(amp: float, k: float, depth: float):
    """Analytic det-J zeros for the sine MIRROR -- and the SIGN is the physics. A mirror throws
    the ray to the OPPOSITE side of the normal, where refraction keeps it on the same side, so
    the floor map is X(x) = x - 2 D A k cos(kx) (minus, against refraction's plus) and the fold
    sits on the minus branch: sin(k x*) = -1/(2 D A k^2), i.e. x* in the second half-period.
    The first version carried refraction's sign and the deposition histogram refuted it -- the
    measured bands landed exactly on this branch. None when too weak to fold."""
    g = 2.0 * depth * amp * k * k
    if g < 1.0:
        return None
    s0 = math.asin(1.0 / g)
    xs = ((math.pi + s0) / k, (2.0 * math.pi - s0) / k)
    return [x - 2.0 * depth * amp * k * math.cos(k * x) for x in xs]


def derived_aperture(r_mirror: float, cell: float) -> float:
    """The aperture that keeps spherical aberration under one histogram cell: a < sqrt(2 R cell).
    Derived from dz ~ a^2/(2R); the instrument's resolution sets the mirror's usable width."""
    return math.sqrt(2.0 * float(r_mirror) * float(cell))


def spherical_cap(n_rays: int, r_mirror: float, aperture: float, seed: int = 5):
    """Sample a concave spherical cap (centre of curvature at origin, cap at z = -R) and return
    (positions, inward normals) for a parallel beam test."""
    rng = np.random.default_rng(seed)
    r = aperture * np.sqrt(rng.random(n_rays))
    ph = 2.0 * math.pi * rng.random(n_rays)
    x, y = r * np.cos(ph), r * np.sin(ph)
    z = -np.sqrt(np.clip(r_mirror ** 2 - x ** 2 - y ** 2, 0.0, None))
    pos = np.stack([x, y, z], axis=1)
    nrm = -pos / np.linalg.norm(pos, axis=1)[:, None]   # toward the centre of curvature
    return pos, nrm


def axial_focus(pos, nrm, n_z: int = 4000, z_lo: float = None, z_hi: float = None):
    """Where a parallel beam actually concentrates: reflect straight-down rays, then find the z
    that minimises the beam's RMS radius -- a direct measurement of the focal distance with no
    paraxial assumption smuggled in."""
    d = reflect_rays(np.tile(np.array([0.0, 0.0, -1.0]), (len(pos), 1)), nrm)
    p = np.asarray(pos, dtype=np.float64)
    if z_lo is None:
        z_lo = float(p[:, 2].max()) + 1e-9
    if z_hi is None:
        z_hi = 0.0
    zs = np.linspace(z_lo, z_hi, n_z)
    best_z, best_r = None, float("inf")
    for z in zs:
        s = (z - p[:, 2]) / d[:, 2]
        q = p[:, :2] + d[:, :2] * s[:, None]
        rr = float(np.sqrt((q ** 2).sum(axis=1).mean()))
        if rr < best_r:
            best_r, best_z = rr, float(z)
    return best_z, best_r
