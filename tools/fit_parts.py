"""fit_parts.py -- fit analytic CAD primitives to a sectioned donor, one per region.

The operator's rule: the CAD element is the GENERALIZED shape of the part --
a teddy head is a sphere, an ear is a half-disc, a limb is a capsule. The
donor's lumps and holes do NOT carry over; the primitive is complete and
uniform by construction, and the coat is tiled onto it (spray_parts.py) with
relief clamped relative to the part's size.

Fits:
  ellipsoid  -- head, torso, snout, paws, feet, eyes, nose (centroid + PCA,
                radii at the p90 Mahalanobis bound of the region's splats)
  capsule    -- arms and legs: axis = skeleton bone (shoulder->wrist,
                hip->ankle), radius = median splat distance to the bone

Output: parts JSON {name, type, parent, params} + a viz .splat of the part
surfaces colored by region (inspect BEFORE any spray -- verification contract).

Usage:
  .venv-gs/Scripts/python.exe tools/fit_parts.py --splat models/co3d/co3d_34.splat \
      --labels models/co3d/bear34_labels.json --skel models/co3d/bear34_skeleton_solved.json \
      --out models/co3d/bear34_parts.json --viz models/co3d/bear34_parts.splat
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402
from label_regions import region_color  # noqa: E402

# region -> primitive recipe. Capsule bones name skeleton joints (2 per limb).
RECIPES = {
    "head": "ellipsoid", "torso": "ellipsoid", "snout": "ellipsoid",
    "ear_L": "ellipsoid", "ear_R": "ellipsoid",
    "paw_L": "ellipsoid", "foot_L": "ellipsoid", "foot_R": "ellipsoid",
    "eye_L": "ellipsoid", "eye_R": "ellipsoid", "nose": "ellipsoid",
    "arm_L": [("capsule", "shoulder_L", "elbow_L"), ("capsule", "elbow_L", "wrist_L")],
    "arm_R": [("capsule", "shoulder_R", "elbow_R"), ("capsule", "elbow_R", "wrist_R")],
    "leg_L": [("capsule", "hip_L", "knee_L"), ("capsule", "knee_L", "ankle_L")],
    "leg_R": [("capsule", "hip_R", "knee_R"), ("capsule", "knee_R", "ankle_R")],
}


def fit_ellipsoid(pts: np.ndarray):
    """Robust shell fit: splats are a SURFACE, so the median shell point must
    land ON the ellipsoid. Median center + trimmed PCA + radial rescale;
    contamination rods die in the trim."""
    c = np.median(pts, axis=0)
    d0 = np.linalg.norm(pts - c, axis=1)
    keep = d0 <= np.percentile(d0, 85)  # drop far outliers/static
    p = pts[keep]
    c = p.mean(0)
    cov = np.cov((p - c).T)
    eig, V = np.linalg.eigh(cov)
    r = np.sqrt(np.maximum(eig, 1e-12))
    for _ in range(4):  # rescale so the median shell point is on the surface
        q = np.sqrt(((((p - c) @ V) / r[None, :]) ** 2).sum(1))
        r = r * np.median(q)
    return {"center": c.tolist(), "axes": V.tolist(), "radii": r.tolist()}


def fit_capsule(pts: np.ndarray, p0: np.ndarray, p1: np.ndarray):
    axis = p1 - p0
    L = np.linalg.norm(axis)
    a = axis / L
    rel = pts - p0
    t = np.clip(rel @ a, 0, L)
    d = np.linalg.norm(rel - t[:, None] * a[None, :], axis=1)
    return {"p0": p0.tolist(), "p1": p1.tolist(), "radius": float(np.median(d))}


def sample_surface(name: str, part: dict, n: int, rng):
    """Uniform-ish surface samples + outward normals + frames + uv."""
    if part["type"] == "ellipsoid":
        c = np.array(part["center"]); V = np.array(part["axes"]); r = np.array(part["radii"])
        # gaussian directions -> sphere -> ellipsoid surface
        g = rng.normal(size=(n, 3))
        g /= np.linalg.norm(g, axis=1, keepdims=True)
        surf = c + (g * r[None, :]) @ V.T
        # normal of implicit ellipsoid in world space
        n_local = g / np.maximum(r[None, :], 1e-12)
        nw = n_local @ V.T
        nw /= np.linalg.norm(nw, axis=1, keepdims=True)
        u = (np.arctan2(g[:, 1], g[:, 0]) / (2 * np.pi)) % 1.0
        v = (g[:, 2] + 1.0) / 2.0
        return surf, nw, np.stack([u, v], 1)
    p0 = np.array(part["p0"]); p1 = np.array(part["p1"]); rad = part["radius"]
    a = p1 - p0
    L = np.linalg.norm(a); a /= L
    ref = np.array([0.0, 1.0, 0.0]) if abs(a[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    t1 = np.cross(a, ref); t1 /= np.linalg.norm(t1)
    t2 = np.cross(a, t1)
    t = rng.random(n)
    th = rng.random(n) * 2 * np.pi
    n_vec = np.cos(th)[:, None] * t1 + np.sin(th)[:, None] * t2
    surf = p0 + (t * L)[:, None] * a + rad * n_vec
    return surf, n_vec, np.stack([t, th / (2 * np.pi)], 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--splat", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--skel", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--viz", help="write a .splat of the primitive surfaces")
    ap.add_argument("--shells", help="inner-membrane npz -- primitives fit the MEMBRANE "
                                   "(zero of application = zero of extraction)")
    a = ap.parse_args()

    lab = json.loads(Path(a.labels).read_text())
    names = lab["regions"]
    skel = json.loads(Path(a.skel).read_text())["joints"]
    J = {n: np.array(j["pos"]) for n, j in skel.items()}

    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= 0.5]
    if lab.get("denoise"):
        from scipy.spatial import cKDTree
        shells = np.load(lab["shells"])
        keep = cKDTree(shells["outer"]).query(buf[:, 0:3])[0] <= lab["denoise"]
        buf = buf[keep]
    splat_lab = np.array(lab["splat_labels"])
    spos = buf[:, 0:3]

    inner_lab = None
    if a.shells:
        # label each inner-membrane point by its nearest labeled splat
        inner = np.load(a.shells)["inner"].astype(np.float64)
        from scipy.spatial import cKDTree
        inner_lab = splat_lab[cKDTree(spos).query(inner)[1]]
    # hard beads (eyes, nose) sit PROUD of the membrane -- their surface is
    # their own, keep the shell fit for them; fur-covered parts fit the membrane
    SHELL_FIT = {"eye_L", "eye_R", "nose"}

    hierarchy = lab.get("hierarchy", {})

    def seg_dist(pts: np.ndarray, p0: np.ndarray, p1: np.ndarray) -> np.ndarray:
        a = p1 - p0
        L2 = a @ a
        t = np.clip((pts - p0) @ a / max(L2, 1e-12), 0, 1)
        return np.linalg.norm(pts - (p0 + t[:, None] * a[None, :]), axis=1)

    parts = {}
    for i, name in enumerate(names):
        recipe = RECIPES.get(name)
        if recipe is None:
            continue
        pts = spos[splat_lab == i]
        if len(pts) < 20:
            print(f"{name}: only {len(pts)} splats -- skipped")
            continue
        if inner_lab is not None and name not in SHELL_FIT:
            mpts = inner[inner_lab == i]
            if len(mpts) >= 20:
                pts = mpts  # fit the membrane: application zero = extraction zero
        prims = []
        if recipe == "ellipsoid":
            prims.append({"type": "ellipsoid", **fit_ellipsoid(pts)})
        else:
            # split the region's splats across the bone segments (nearest wins)
            bones = [(j0, j1) for _, j0, j1 in recipe]
            dmat = np.stack([seg_dist(pts, J[j0], J[j1]) for j0, j1 in bones], 1)
            owner = dmat.argmin(1)
            for k, (j0, j1) in enumerate(bones):
                sub = pts[owner == k]
                if len(sub) < 10:
                    sub = pts  # degenerate split -- fit on everything
                prims.append({"type": "capsule", "bone": [j0, j1],
                              **fit_capsule(sub, J[j0], J[j1])})
        for p in prims:
            p["parent"] = hierarchy.get(name)
        parts[name] = prims

    Path(a.out).write_text(json.dumps({"splat": a.splat, "parts": parts}, indent=2))
    for n, prims in parts.items():
        for p in prims:
            if p["type"] == "ellipsoid":
                r = np.array(p["radii"]) * 1000
                print(f"{n:9s} ellipsoid radii(mm) {r.round(1)}")
            else:
                tag = ">".join(p["bone"])
                print(f"{n:9s} capsule {tag:24s} r={p['radius']*1000:.1f}mm")

    if a.viz:
        rng = np.random.default_rng(0)
        out = []
        for n, prims in parts.items():
            col = region_color(n, names.index(n) if n in names else 0)
            for p in prims:
                surf, _, _ = sample_surface(n, p, 3000, rng)
                b = np.zeros((len(surf), 14), dtype=np.float32)
                b[:, 0:3] = surf
                b[:, 3:6] = col
                b[:, 6] = 1.0
                b[:, 7:10] = 0.0015
                b[:, 10] = 1.0
                out.append(b)
        cb.save_splat(a.viz, np.concatenate(out))
        print("viz ->", a.viz)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
