"""Teddy skin: parametric body surface -> bound splat cloud (.splat).

Each surface sample of tools/teddy_body.py becomes a splat:
  - position: on the surface (optionally + normal*offset)
  - rotation: local z-axis aligned to the surface normal (thin axis OUT)
  - scale: (tan, tan, thin) — a disc tangent to the surface; fur mode makes
    needles along the normal instead (tapered-cylinder-as-splat)
  - color: median brown of the measured eqonly bear (v0; appearance
    optimization comes later)
"""
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
sys.path.insert(0, r"E:\PythonChimera\tools")
import cpp_bridge as cb  # noqa: E402
import teddy_body as tb  # noqa: E402


def _quat_from_z_to(n):
    """Quaternion (wxyz) rotating local +Z onto unit vector n. Vectorized."""
    n = np.asarray(n, float)
    z = np.tile([0.0, 0.0, 1.0], (len(n), 1))
    v = np.cross(z, n)
    c = n[:, 2:3]  # dot(z, n) = n_z
    w = 1.0 + c
    q = np.concatenate([w, v], axis=1)
    # handle n ~ -z (w ~ 0): pick any perpendicular
    bad = (np.abs(q).sum(1) < 1e-6)
    q[bad] = [0.0, 1.0, 0.0, 0.0]
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def build_skin(n_per_part=4000, disc_r=0.011, thin=0.004, alpha=0.95,
               color=None, seed=0):
    P, N, ids = tb.sample_surface(n_per_part=n_per_part, seed=seed)
    if color is None:
        d = cb.load_splat(r"E:/PythonChimera/models/genbear3/eqonly_med.splat")
        solid = d[d[:, 6] >= 0.5]
        color = np.median(solid[:, 3:6], axis=0)
    color = np.asarray(color, float)
    q = _quat_from_z_to(N)
    buf = np.zeros((len(P), 14), dtype=np.float64)
    buf[:, 0:3] = P
    buf[:, 3:6] = color
    buf[:, 6] = alpha
    buf[:, 7:10] = [disc_r, disc_r, thin]
    buf[:, 10:14] = q
    return buf


def build_fur(n_per_part=2500, strand_len=0.022, strand_r=0.0022, alpha=0.6,
              color=None, jitter_deg=12.0, seed=1):
    """Fur strands: needle splats rooted on the surface, axis ~ normal."""
    P, N, ids = tb.sample_surface(n_per_part=n_per_part, seed=seed)
    rng = np.random.default_rng(seed)
    if color is None:
        d = cb.load_splat(r"E:/PythonChimera/models/genbear3/eqonly_med.splat")
        solid = d[d[:, 6] >= 0.5]
        color = np.median(solid[:, 3:6], axis=0)
    color = np.asarray(color, float)
    # jitter the strand direction around the normal
    j = np.deg2rad(jitter_deg)
    t1 = np.cross(N, np.tile([0, 0, 1.0], (len(N), 1)))
    small = np.linalg.norm(t1, axis=1) < 1e-6
    t1[small] = np.cross(N[small], [1, 0, 0])
    t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
    t2 = np.cross(N, t1)
    a1 = rng.uniform(0, 2 * np.pi, len(N))
    a2 = rng.uniform(0, j, len(N))
    D = N + np.tan(a2)[:, None] * (np.cos(a1)[:, None] * t1 + np.sin(a1)[:, None] * t2)
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    center = P + 0.5 * strand_len * D
    q = _quat_from_z_to(D)
    buf = np.zeros((len(P), 14), dtype=np.float64)
    buf[:, 0:3] = center
    buf[:, 3:6] = color
    buf[:, 6] = alpha
    buf[:, 7:10] = [strand_r, strand_r, strand_len / 2]
    buf[:, 10:14] = q
    return buf


# ---------------------------------------------------------------------------
# GRAVITY SETTLE — the operator's model: every PART is a gravitational body.
# Each part's paint starts as an orb (spherical cloud) around it; the parts
# attract the particles (force ~ part mass / r^2), the union SDF collides
# them onto the surface, and mutual repulsion spreads them into an even
# coat. Positions at the end are physics equilibria, not samples.
#
# Derivations (no swept numbers):
#   particle budget per part  ~ part SURFACE AREA (coverage need scales r^2)
#   attraction force per part ~ part MASS (capture dynamics; mass ~ r^3)
#   target spacing s = sqrt(A_total / N)  ->  repulsion radius + disc radius
# ---------------------------------------------------------------------------
def _part_surface_area(part):
    if part["prim"] in ("ellipsoid", "sphere"):
        a, b, c = np.asarray(part["r"], float)
        p = 1.6075  # Knud Thomsen ellipsoid area approximation
        return 4.0 * np.pi * (((a * b) ** p + (a * c) ** p + (b * c) ** p) / 3.0) ** (1.0 / p)
    pa = np.asarray(part["a"], float)
    pb = np.asarray(part["b"], float)
    h = np.linalg.norm(pb - pa)
    r = part["r"][0]
    return 2.0 * np.pi * r * h + 4.0 * np.pi * r * r  # capsule: cylinder + caps


def _part_extent(part):
    """Bounding radius of the part around its centroid (orb init size)."""
    if part["prim"] in ("ellipsoid", "sphere"):
        return float(max(part["r"]))
    pa = np.asarray(part["a"], float)
    pb = np.asarray(part["b"], float)
    return 0.5 * float(np.linalg.norm(pb - pa)) + part["r"][0]


def _part_uv(part, x):
    """Surface coordinates of points x (M,3) on this part: (u, v).

    capsule:   u = axial t in [0,1],  v = angle around axis in [0, 2pi)
    ellipsoid: u = azimuth,           v = elevation (radians)
    Regions (bow tie etc.) are predicates over (part_id, u, v).
    """
    if part["prim"] == "capsule":
        pa = np.asarray(part["a"], float)
        pb = np.asarray(part["b"], float)
        ba = pb - pa
        h = np.linalg.norm(ba)
        ax = ba / h
        w = np.cross(ax, [1.0, 0, 0])
        if np.linalg.norm(w) < 1e-6:
            w = np.cross(ax, [0, 1.0, 0])
        w /= np.linalg.norm(w)
        v = np.cross(ax, w)
        rel = x - pa
        t = np.clip((rel @ ax) / h, 0.0, 1.0)
        rad = rel - (t * h)[:, None] * ax
        ang = np.arctan2(rad @ v, rad @ w) % (2 * np.pi)
        return np.stack([t, ang], axis=1)
    c = np.asarray(part["c"], float)
    r = np.asarray(part["r"], float)
    d = (x - c) / r
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    az = np.arctan2(d[:, 1], d[:, 0]) % (2 * np.pi)
    el = np.arcsin(np.clip(d[:, 2], -1.0, 1.0))
    return np.stack([az, el], axis=1)


def _part_normal(part, x, eps=1e-3):
    """Gradient of ONE part's SDF (unit). x (M,3) -> (M,3)."""
    g = np.zeros_like(x)
    for i in range(3):
        e = np.zeros(3)
        e[i] = eps
        g[:, i] = tb.sd_part(x + e, part) - tb.sd_part(x - e, part)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)


def settle_coat(target_n=60000, fall_steps=400, relax_steps=150, seed=0,
                damp=0.85, dt=0.02, repel_every=2, orb_margin=None, verbose=True):
    """Rain paint onto the body under per-part gravity. Returns
    (buf (M,14), part_id (M,), uv (M,2)) — geometry only, no appearance.

    Physics (v2, after v1's measured failures):
      - BINDING: each orb's particles belong to their HOME part. The forearm is
        the tractor for its own paint. (v1 ran free n-body capture; the torso's
        mass ate 43k/60k particles and small parts got zero.)
      - SURFACE ATTRACTION: force pulls toward the home part's NEAREST SURFACE
        POINT (from that part's own SDF) with magnitude GM*d/(d^2+soft^2) — a
        softened 1/d field that VANISHES at touchdown, like real gravity at the
        ground. (v1 pulled toward the centroid with 1/r^2; acceleration blew up
        near the center and 91% of particles tunneled inside the body.)
      - DISPLACEMENT CLAMP: per-step move <= 0.25 * thinnest part radius, so a
        particle can never jump across a part in one step.
      - RELAX: after touchdown, union-SDF collision + mutual repulsion evens the
        coat and ejects paint that landed where its home part is swallowed by
        the union (e.g. shoulder-in-torso).
    """
    from scipy.spatial import cKDTree

    rng = np.random.default_rng(seed)
    parts = tb.PARTS
    areas = np.array([_part_surface_area(p) for p in parts])
    masses = np.array([tb.part_mass(p)[0] for p in parts])
    cents = np.array([tb.part_mass(p)[1] for p in parts])

    # budget ~ area, with a floor so ears/muzzle still coat
    counts = np.maximum(200, np.round(target_n * areas / areas.sum()).astype(int))
    spacing = float(np.sqrt(areas.sum() / counts.sum()))
    r_min = float(min(min(p["r"]) for p in parts))
    max_step = 0.25 * r_min
    soft2 = (0.5 * spacing) ** 2
    touchdown = 0.5 * spacing
    r_repel = 0.9 * spacing

    # orb init: uniform-direction shell around each part centroid.
    # orb_margin=None: far drop (1.5x extent). With a fitted body the drop only
    # needs to clear the fit error: extent + fit margin (operator hypothesis:
    # shorter drop -> less drift -> tighter coat).
    P, home = [], []
    for i, part in enumerate(parts):
        d = rng.normal(size=(counts[i], 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        if orb_margin is None:
            rad = _part_extent(part) * 1.5 * (1.0 + 0.3 * rng.random(counts[i]))
        else:
            rad = _part_extent(part) + orb_margin * (0.8 + 0.4 * rng.random(counts[i]))
        P.append(cents[i] + d * rad[:, None])
        home += [i] * counts[i]
    P = np.vstack(P)
    home = np.asarray(home)
    V = np.zeros_like(P)

    GM = masses / masses.max()
    active = np.ones(len(P), bool)

    # ---- phase A: fall (bound, surface-attraction, clamped) ----------------
    for step in range(fall_steps):
        for i, part in enumerate(parts):
            m = active & (home == i)
            if not m.any():
                continue
            x = P[m]
            d = tb.sd_part(x, part)                     # signed dist to home part
            n = _part_normal(part, x)
            mag = GM[i] * np.abs(d) / (d * d + soft2)   # -> 0 at the surface
            F = -mag[:, None] * np.sign(d)[:, None] * n  # toward nearest surface pt
            Vn = damp * V[m] + dt * F
            sl = np.linalg.norm(Vn, axis=1, keepdims=True)
            Vn *= np.minimum(1.0, max_step / np.maximum(sl, 1e-9))
            P[m] += Vn
            V[m] = Vn
            # touchdown: freeze exactly on the home surface
            td = tb.sd_part(P[m], part) <= touchdown
            if td.any():
                idx = np.flatnonzero(m)[td]
                dd = tb.sd_part(P[idx], part)
                P[idx] -= dd[:, None] * _part_normal(part, P[idx])
                V[idx] = 0.0
                active[idx] = False
        if verbose and step % 100 == 0:
            print(f"  fall {step:4d}  airborne {int(active.sum())}")
        if not active.any():
            break

    # ---- phase B: relax on the union (collision + repulsion) ---------------
    for step in range(relax_steps):
        dist = tb.sdf(P)
        inside = dist < 0.0
        if inside.any():
            P[inside] -= dist[inside][:, None] * tb.normal(P[inside])
        if repel_every and step % repel_every == 0:
            tree = cKDTree(P)
            pairs = tree.query_pairs(r_repel, output_type="ndarray")
            if len(pairs):
                pa, pb = P[pairs[:, 0]], P[pairs[:, 1]]
                delta = pa - pb
                dl = np.linalg.norm(delta, axis=1, keepdims=True)
                push = 0.5 * (r_repel - dl) * delta / np.maximum(dl, 1e-9)
                np.add.at(P, pairs[:, 0], push)
                np.add.at(P, pairs[:, 1], -push)
                # pushing can bury a particle: re-eject
                dist = tb.sdf(P)
                inside = dist < -r_repel
                if inside.any():
                    P[inside] -= (dist[inside] + r_repel)[:, None] * tb.normal(P[inside])
        if verbose and step % 50 == 0:
            print(f"  relax {step:4d}  inside {int((tb.sdf(P) < 0).sum())}")

    # final exact projection + identity (part, uv, normal)
    for _ in range(3):
        dist = tb.sdf(P)
        n = tb.normal(P)
        P = P - dist[:, None] * n
    N = tb.normal(P)
    d_all = np.stack([tb.sd_part(P, p) for p in parts], axis=1)
    pid = d_all.argmin(1)
    uv = np.zeros((len(P), 2))
    for i, part in enumerate(parts):
        m = pid == i
        if m.any():
            uv[m] = _part_uv(part, P[m])

    disc_r = 0.62 * spacing  # slight overlap: diameter ~1.24x spacing
    q = _quat_from_z_to(N)
    buf = np.zeros((len(P), 14), dtype=np.float64)
    buf[:, 0:3] = P
    buf[:, 3:6] = [0.424, 0.267, 0.204]  # median fg brown; paint comes later
    buf[:, 6] = 0.95
    buf[:, 7:10] = [disc_r, disc_r, 0.35 * disc_r]
    buf[:, 10:14] = q
    if verbose:
        print(f"settled {len(P)} splats, spacing {spacing:.4f}, disc r {disc_r:.4f}")
        for i, part in enumerate(parts):
            print(f"  {part['name']:12s} budget {counts[i]:5d}  landed {(pid == i).sum():5d}")
    return buf, pid, uv


if __name__ == "__main__":
    if "--settle" in sys.argv:
        i = sys.argv.index("--settle")
        out = sys.argv[i + 1] if i + 1 < len(sys.argv) else r"models/triposplat/static/viewer/authbear4_coat.splat"
        n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 60000
        margin = float(sys.argv[sys.argv.index("--margin") + 1]) if "--margin" in sys.argv else None
        if "--parts" in sys.argv:  # fitted body override (JSON parts list)
            import json
            with open(sys.argv[sys.argv.index("--parts") + 1]) as f:
                tb.PARTS = json.load(f)
            print(f"parts override: {len(tb.PARTS)} fitted parts")
        buf, pid, uv = settle_coat(target_n=n, orb_margin=margin)
        cb.save_splat(out, buf)
        np.savez(out.replace(".splat", ".meta.npz"), part_id=pid, uv=uv)
        print(f"wrote {out}: {len(buf)} settled splats (+ .meta.npz part/uv labels)")
    else:
        out = sys.argv[1] if len(sys.argv) > 1 else r"models/triposplat/static/viewer/authbear0.splat"
        skin = build_skin()
        fur = build_fur()
        buf = np.vstack([skin, fur])
        cb.save_splat(out, buf)
        print(f"wrote {out}: {len(buf)} splats ({len(skin)} skin + {len(fur)} fur)")
