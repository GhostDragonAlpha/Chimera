"""Parametric teddy body — the authored CAD-style solid.

A bear is a parts list of analytic primitives (ellipsoid / capsule / sphere).
Every part carries: geometry params, joint (parent, pivot, axis), and analytic
mass properties (volume, centroid; inertia for capsule/sphere/ellipsoid are
closed-form). The union is an SDF with smooth-blend (smin) so the CA lattice
can voxelize it and the fur field can root strands on the surface with exact
normals.

Numbers below are MEASURED from models/genbear3/eqonly_med.splat
(.tmp/eqonly_measure.json, k-means cluster PCA), symmetrized about x=0.03.
Units: scene units, bear height ~= 1.06.
"""
import json
import numpy as np

import teddy_catalog as tc

# Default assembled bear (slim segmented limbs, swappable via tc.assemble).
SPINE_X = tc.SPINE_X
PARTS = tc.assemble()

K_SMOOTH = 0.06  # smin blend radius between parts


# ---- SDF -------------------------------------------------------------------
def _sd_ellipsoid(p, c, r):
    """IQ's approximate ellipsoid SDF; p (...,3)."""
    r = np.asarray(r, float)
    k0 = np.linalg.norm((p - c) / r, axis=-1)
    k0 = np.maximum(k0, 1e-9)
    k1 = np.linalg.norm((p - c) / (r * r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def _sd_capsule(p, a, b, r):
    pa = p - a
    ba = np.asarray(b, float) - np.asarray(a, float)
    h = np.clip((pa @ ba) / (ba @ ba), 0.0, 1.0)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - r


def _sd_sphere(p, c, r):
    return np.linalg.norm(p - c, axis=-1) - r[0]


def sd_part(p, part):
    if part["prim"] == "ellipsoid":
        return _sd_ellipsoid(p, np.array(part["c"], float), part["r"])
    if part["prim"] == "sphere":
        return _sd_sphere(p, np.array(part["c"], float), part["r"])
    if part["prim"] == "capsule":
        return _sd_capsule(p, np.array(part["a"], float), np.array(part["b"], float), part["r"][0])
    raise ValueError(part["prim"])


def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def sdf(p):
    """Union SDF of all parts (smooth). p (...,3) -> (...,)."""
    d = sd_part(p, PARTS[0])
    for part in PARTS[1:]:
        d = _smin(d, sd_part(p, part), K_SMOOTH)
    return d


def normal(p, eps=1e-3):
    """SDF gradient by central differences; p (...,3) -> (...,3) unit."""
    g = np.zeros_like(p, dtype=float)
    for i in range(3):
        e = np.zeros(3)
        e[i] = eps
        g[..., i] = sdf(p + e) - sdf(p - e)
    n = np.linalg.norm(g, axis=-1, keepdims=True)
    return g / np.maximum(n, 1e-12)


# ---- analytic mass ---------------------------------------------------------
def part_mass(part, rho=1.0):
    """(mass, centroid). Overlap between parts ignored (plush tolerance)."""
    if part["prim"] in ("ellipsoid", "sphere"):
        r = np.asarray(part["r"], float)
        vol = 4.0 / 3.0 * np.pi * r.prod()
        return rho * vol, np.asarray(part["c"], float)
    a, b = np.asarray(part["a"], float), np.asarray(part["b"], float)
    h = np.linalg.norm(b - a)
    r = part["r"][0]
    vol = np.pi * r * r * h + 4.0 / 3.0 * np.pi * r**3
    return rho * vol, 0.5 * (a + b)


def body_mass(rho=1.0):
    ms = np.array([part_mass(p, rho) for p in PARTS], dtype=object)
    m = np.array([x[0] for x in ms])
    c = np.array([x[1] for x in ms])
    M = m.sum()
    return M, (m[:, None] * c).sum(0) / M


# ---- surface sampling (fur root field / frosting base) ---------------------
def sample_surface(n_per_part=3000, seed=0, shell=0.0):
    """Sample points on the visible outer surface of the union.

    Points are drawn on each primitive's own surface, then kept only if they
    are OUTSIDE every other part (not swallowed by the union). Returns
    (pts (M,3), normals (M,3), part_id (M,)).
    shell>0 offsets points outward along the normal (frosting mid-layer).
    """
    rng = np.random.default_rng(seed)
    pts, ids = [], []
    for pi, part in enumerate(PARTS):
        if part["prim"] in ("ellipsoid", "sphere"):
            c = np.asarray(part["c"], float)
            r = np.asarray(part["r"], float)
            d = rng.normal(size=(n_per_part * 2, 3))
            d /= np.linalg.norm(d, axis=1, keepdims=True)
            q = c + d * r  # gaussian-direction surface approx for ellipsoid
        else:  # capsule: cylinder body + caps
            a, b = np.asarray(part["a"], float), np.asarray(part["b"], float)
            r = part["r"][0]
            ba = b - a
            h = np.linalg.norm(ba)
            u = ba / h
            w = np.cross(u, [1, 0, 0])
            if np.linalg.norm(w) < 1e-6:
                w = np.cross(u, [0, 1, 0])
            w /= np.linalg.norm(w)
            v = np.cross(u, w)
            m = n_per_part * 2
            cap = rng.random(m) < (4 * np.pi * r * r / 2) / (2 * np.pi * r * h + 4 * np.pi * r * r)
            t = rng.random(m)
            th = rng.random(m) * 2 * np.pi
            cyl = a + (t * h)[:, None] * u + r * (np.cos(th)[:, None] * w + np.sin(th)[:, None] * v)
            # cap points: hemisphere on a or b
            d = rng.normal(size=(m, 3))
            d /= np.linalg.norm(d, axis=1, keepdims=True)
            side = rng.random(m) < 0.5
            d[side] = np.where((d[side] @ u)[:, None] > 0, -d[side], d[side])   # toward a
            d[~side] = np.where((d[~side] @ u)[:, None] < 0, -d[~side], d[~side])  # toward b
            caps = np.where(side[:, None], a, b) + r * d
            q = np.where(cap[:, None], caps, cyl)
        # keep only points on the OUTER surface of the union
        keep = np.ones(len(q), bool)
        for pj, other in enumerate(PARTS):
            if pj == pi:
                continue
            keep &= sd_part(q, other) > -K_SMOOTH * 0.5
        pts.append(q[keep])
        ids += [pi] * int(keep.sum())
    P = np.vstack(pts)
    N = normal(P)
    if shell:
        P = P + shell * N
    return P, N, np.asarray(ids)


if __name__ == "__main__":
    import sys
    M, C = body_mass()
    print(f"parts: {len(PARTS)}  total mass {M:.4f}  COM ({C[0]:+.3f},{C[1]:+.3f},{C[2]:+.3f})")
    for p in PARTS:
        m, c = part_mass(p)
        print(f"  {p['name']:12s} {p['prim']:9s} mass {m:.4f}  c=({c[0]:+.3f},{c[1]:+.3f},{c[2]:+.3f})")
    if "--sample" in sys.argv:
        P, N, ids = sample_surface()
        print(f"surface samples: {len(P)}")
        out = sys.argv[sys.argv.index("--sample") + 1] if sys.argv.index("--sample") + 1 < len(sys.argv) else ".tmp/teddy_body_surface.npz"
        np.savez(out, pts=P, normals=N, part_id=ids)
        with open(out.replace(".npz", "_parts.json"), "w") as f:
            json.dump(PARTS, f, indent=2)
        print(f"wrote {out}")
