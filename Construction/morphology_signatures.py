"""Morphological signatures — the actual math, not the PCA triad.

For a cloud of points (one scene element) this computes a signature vector with REAL
descriptors, then reads a label off it. The point is to separate the cases that
'linear/planar/blob' cannot — above all TRUNK vs POST vs 5-GALLON BUCKET, which are
all 'vertical cylinders' until you measure taper, aspect and radial symmetry.

Signatures computed:
  PCA shape      linearity, planarity, sphericity, surface_variation   (Demantke/Pauly)
  verticality    |principal axis . gravity|
  taper          how much cross-section radius shrinks base->tip        (trunk vs post)
  radius_cv      variation of cross-section radius along the axis
  radial_sym     angular uniformity of the cross-section (is it a tube round an axis?)
  fractal_D      box-counting dimension  (foliage ~2.4-2.7, sheet ~2, line ~1)
  aspect         axial length / diameter                                (bucket is squat)

Run directly: validates on synthetic trunk / post / bucket / crown / wall / rock.
"""
import numpy as np
rng = np.random.default_rng(0)


def _rot(v, axis, ang):
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    return v * np.cos(ang) + np.cross(axis, v) * np.sin(ang) + axis * (axis @ v) * (1 - np.cos(ang))


def fractal_dim(pts, scales=(4, 8, 16, 32, 64)):
    p = pts - pts.min(0); p = p / (p.max() + 1e-9)
    counts = []
    for s in scales:
        q = np.clip((p * s).astype(np.int64), 0, s - 1)
        key = (q[:, 0] * s + q[:, 1]) * s + q[:, 2]
        counts.append(len(np.unique(key)))
    return float(np.polyfit(np.log(scales), np.log(counts), 1)[0])


def signature(pts):
    n = len(pts); c = pts.mean(0)
    d = pts - c
    _, s, vt = np.linalg.svd(d[rng.choice(n, min(20000, n), replace=False)], full_matrices=False)
    lam = s ** 2 / (s ** 2).sum()
    l1, l2, l3 = lam
    axis, e1, e2 = vt[0], vt[1], vt[2]
    up = np.array([0., 0., 1.])
    # cross-section: distance from the principal axis, binned along it
    t = d @ axis
    perp = d - np.outer(t, axis)
    r = np.linalg.norm(perp, axis=1)
    L = t.max() - t.min()
    edges = np.linspace(t.min(), t.max(), 11)
    bi = np.clip(np.digitize(t, edges) - 1, 0, 9)
    radii = np.array([r[bi == k].mean() for k in range(10) if (bi == k).any()])
    if radii[0] < radii[-1]: radii = radii[::-1]           # base = the fatter end
    taper = float((radii[0] - radii[-1]) / (radii[0] + 1e-9))
    radius_cv = float(radii.std() / (radii.mean() + 1e-9))
    # radial symmetry: is the cross-section wrapped uniformly around the axis?
    ang = np.arctan2(perp @ e2, perp @ e1)
    hist = np.histogram(ang, bins=16, range=(-np.pi, np.pi))[0].astype(float)
    hist /= hist.sum() + 1e-9
    radial_sym = float(1 - hist.std() / (1 / 16))          # ~1 tube, ~0 flat/one-sided
    diameter = 2 * r.mean() + 1e-9
    return dict(n=n, linearity=float((l1 - l2) / l1), planarity=float((l2 - l3) / l1),
                sphericity=float(l3 / l1), surf_var=float(l3),
                verticality=float(abs(axis @ up)), taper=taper, radius_cv=radius_cv,
                radial_sym=radial_sym, fractal=fractal_dim(pts), aspect=float(L / diameter))


def classify(s):
    lin, plan, sph, vert = s['linearity'], s['planarity'], s['sphericity'], s['verticality']
    taper, rsym, frac, asp = s['taper'], s['radial_sym'], s['fractal'], s['aspect']
    if rsym > 0.8 and lin > 0.85 and asp > 3.5:                 # an elongated tube around an axis
        return "TRUNK (tapered column)" if taper > 0.30 else "POST/PIPE (uniform column)"
    if sph > 0.6:                                               # very round, compact
        return "BLOB/ROCK/FRUIT (compact)"
    if asp < 2.5 and rsym > 0.4 and plan > 0.3:                 # squat round-section tub
        return "BUCKET/TANK (wide squat cylinder)"
    if sph < 0.06 and rsym < 0.4:                               # flat sheet, one-sided (not a tube)
        return "WALL/FLOOR (sheet)"
    # vegetation = the thing that is NOT a clean primitive: space-filling fractal, OR a
    # scattered branchy volume (elongated yet not radially symmetric = branches, not a tube)
    if frac > 2.15 or (sph > 0.12 and plan < 0.30 and rsym < 0.72 and asp < 5.0):
        return "FOLIAGE/CROWN (fractal volume)"
    return "unresolved"


# ---------------------------------------------------------------- validation
def _cyl(r0, r1, H, n=5000):
    z = rng.uniform(0, H, n); rr = r0 + (r1 - r0) * (z / H); a = rng.uniform(0, 2 * np.pi, n)
    return np.stack([rr * np.cos(a), rr * np.sin(a), z], 1) + rng.normal(0, 0.01, (n, 3))

def _plane(w, hgt, n=5000):
    return np.stack([rng.uniform(-w, w, n), rng.uniform(-hgt, hgt, n), rng.normal(0, 0.02, n)], 1)

def _sphere(R, n=5000):
    v = rng.normal(size=(n, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True); return v * R

def _crown(n_target=5000):
    pts, tips = [], []
    def branch(p, dvec, depth):
        if depth == 0:
            tips.append(p); return
        Ln = 1.6 * (0.72 ** (5 - depth)); q = p + dvec * Ln
        pts.extend(p + (q - p) * tt for tt in np.linspace(0, 1, 12))
        for _ in range(2 if depth > 1 else 3):
            ax = rng.normal(size=3); nd = _rot(dvec, ax, rng.uniform(0.35, 0.85))
            branch(q, nd / np.linalg.norm(nd), depth - 1)
    branch(np.array([0, 0, 0.]), np.array([0, 0, 1.]), 6)
    P = np.array(pts)
    leaves = [t + rng.normal(0, 0.32, (40, 3)) for t in tips]   # dense volumetric foliage puffs at the tips
    P = np.vstack([P] + leaves)
    return P + rng.normal(0, 0.04, P.shape)


if __name__ == "__main__":
    tests = {
        "trunk  (taper 1.0->0.25, H8)": _cyl(1.0, 0.25, 8),
        "post   (uniform 0.4, H8)":     _cyl(0.4, 0.4, 8),
        "bucket (uniform 1.2, H2)":     _cyl(1.2, 1.2, 2),
        "crown  (fractal branching)":   _crown(),
        "wall   (flat sheet)":          _plane(6, 4),
        "rock   (sphere)":              _sphere(1.5),
    }
    hdr = f"{'shape':32}{'lin':>5}{'plan':>6}{'sph':>6}{'vert':>6}{'taper':>7}{'r_cv':>6}{'rsym':>6}{'fracD':>7}{'aspect':>7}   => label"
    print(hdr); print("-" * len(hdr))
    for name, pts in tests.items():
        s = signature(pts)
        print(f"{name:32}{s['linearity']:5.2f}{s['planarity']:6.2f}{s['sphericity']:6.2f}"
              f"{s['verticality']:6.2f}{s['taper']:7.2f}{s['radius_cv']:6.2f}{s['radial_sym']:6.2f}"
              f"{s['fractal']:7.2f}{s['aspect']:7.2f}   => {classify(s)}")
