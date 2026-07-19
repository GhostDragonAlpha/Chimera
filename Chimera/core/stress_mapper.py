"""
stress_mapper — principal stress analysis on Cellular Potts tissue domains.

After assembly (matter_gpu.assemble_3d_gpu or matter.assemble_3d), this module
reads the lattice and computes:

  - Tissue interface normals (where different tissue types meet)
  - Load-bearing axes (bone-muscle-skin alignment under simulated gravity)
  - Shear-compression gradients (mechanical stress concentration)
  - High-curvature bone surface regions -> articulation candidates

Candidates are exported to limb.py as Bone objects — joint locations the
physics says should exist, not hand-placed.

Usage:
    from core.stress_mapper import find_articulations
    lattice = assemble_3d_gpu(...)  # or matter.assemble_3d(...)
    joints = find_articulations(lattice)
    # joints -> [(position, confidence, type), ...]
"""
from __future__ import annotations

import numpy as np

# Tissue type constants (from core.matter)
MEDIUM = 0
SKIN = 1
MUSCLE = 2
BONE = 3

# 6-connectivity offsets for gradient computation
_OFF6 = [(1, 0, 0), (-1, 0, 0),
         (0, 1, 0), (0, -1, 0),
         (0, 0, 1), (0, 0, -1)]

# 18-connectivity for fuller neighborhood analysis
_OFF18 = [(dz, dy, dx)
          for dz in (-1, 0, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
          if (abs(dz) + abs(dy) + abs(dx)) in (1, 2)]


# --- interface normals -------------------------------------------------------

def interface_normals(lattice: np.ndarray) -> np.ndarray:
    """Compute interface normal vectors for every cell.

    For each cell that has a neighbor of a different tissue type, compute
    the direction toward the interface as a normalized gradient.

    Returns (nz, ny, nx, 3) float array of unit vectors (zero for interior).
    """
    nz, ny, nx = lattice.shape
    normals = np.zeros((nz, ny, nx, 3), dtype=np.float64)

    for dz, dy, dx in _OFF6:
        rolled = np.roll(lattice, (-dz, -dy, -dx), axis=(0, 1, 2))
        diff = (lattice != rolled) & (lattice != MEDIUM)
        normals[diff, 0] += dz
        normals[diff, 1] += dy
        normals[diff, 2] += dx

    # Normalize
    mag = np.sqrt((normals ** 2).sum(axis=-1))
    nonzero = mag > 1e-8
    normals[nonzero] /= mag[nonzero, None]
    return normals


# --- load-bearing axes -------------------------------------------------------

def load_bearing_axes(lattice: np.ndarray, gravity: tuple = (0, -1, 0)
                      ) -> np.ndarray:
    """Compute load-bearing alignment per cell.

    For each bone cell, measure how the tissue column above it aligns with
    gravity. High alignment = load-bearing axis.

    Returns (nz, ny, nx) float array of load-bearing confidence (0-1).
    """
    nz, ny, nx = lattice.shape
    gz, gy, gx = gravity
    bearing = np.zeros((nz, ny, nx), dtype=np.float64)

    # For each bone cell, check alignment of bone column along gravity
    bone_mask = lattice == BONE
    bone_coords = np.argwhere(bone_mask)

    for z, y, x in bone_coords:
        # Trace along gravity direction
        count = 0
        cz, cy, cx = z + gz, y + gy, x + gx
        while 0 <= cz < nz and 0 <= cy < ny and 0 <= cx < nx:
            if lattice[cz, cy, cx] == BONE:
                count += 1
                cz += gz
                cy += gy
                cx += gx
            else:
                break
        # Normalize by max possible (lattice depth along that axis)
        max_depth = nz if gz else ny if gy else nx
        bearing[z, y, x] = min(count / max(max_depth, 1) * 10, 1.0)

    return bearing


# --- bone surface curvature --------------------------------------------------

def _bone_surface_curvature(lattice: np.ndarray) -> np.ndarray:
    """Compute surface curvature of the bone-skin/muscle interface.

    High curvature = potential articulation point (joint, tendon attachment).

    Returns (nz, ny, nx) float array of curvature magnitude.
    """
    nz, ny, nx = lattice.shape
    curvature = np.zeros((nz, ny, nx), dtype=np.float64)
    normals = interface_normals(lattice)

    bone_surface = (lattice == BONE)
    for dz, dy, dx in _OFF6:
        rolled_bone = np.roll(bone_surface, (-dz, -dy, -dx), axis=(0, 1, 2))
        rolled_n = np.roll(normals, (-dz, -dy, -dx), axis=(0, 1, 2))

        # Adjacent bone surface cells with diverging normals = curvature
        adj = bone_surface & rolled_bone
        ndot = (normals[adj] * rolled_n[adj]).sum(axis=-1)
        curvature[adj] += np.clip(1.0 - ndot, 0, 1.0)

    return curvature


# --- articulation finding ----------------------------------------------------

def _stress_gradient(lattice: np.ndarray) -> np.ndarray:
    """Compute per-cell stress gradient magnitude (0-1 normalized).

    For each bone surface cell, measure how much the interface normal
    changes across its neighborhood. High gradient = stress concentration."""
    normals = interface_normals(lattice)
    nz, ny, nx = lattice.shape
    grad = np.zeros((nz, ny, nx), dtype=np.float64)
    bone = lattice == BONE

    for dz, dy, dx in _OFF6:
        rolled_bone = np.roll(bone, (-dz, -dy, -dx), axis=(0, 1, 2))
        rolled_n = np.roll(normals, (-dz, -dy, -dx), axis=(0, 1, 2))
        adj = bone & rolled_bone
        ndiff = np.sum((normals[adj] - rolled_n[adj]) ** 2, axis=-1)
        grad[adj] += ndiff

    max_g = float(grad.max())
    if max_g > 1e-8:
        grad /= max_g
    return grad


def _consolidate(candidates: list, radius: float = 8.0,
                 max_vol_ratio: float = 3.0, min_volume: int = 50,
                 grad_threshold: float = 0.2) -> list:
    """Hierarchical consolidation of articulation candidates.

    Uses KDTree to merge nearby candidates where:
    - Distance < radius
    - Volume ratio < max_vol_ratio
    Drops clusters < min_volume unless gradient > grad_threshold."""
    from scipy.spatial import KDTree
    if not candidates:
        return []

    centers = np.array([c["center"] for c in candidates])
    tree = KDTree(centers)
    pairs = tree.query_pairs(r=radius)

    # Union-find
    parent = list(range(len(candidates)))
    def _find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def _union(a, b):
        ra, rb = _find(a), _find(b)
        if ra != rb:
            ca, cb = candidates[ra], candidates[rb]
            ratio = max(ca["size"], cb["size"]) / max(min(ca["size"], cb["size"]), 1)
            if ratio < max_vol_ratio:
                parent[ra] = rb

    for i, j in pairs:
        _union(i, j)

    groups = {}
    for i, c in enumerate(candidates):
        root = _find(i)
        if root not in groups:
            groups[root] = {"centers": [], "sizes": [], "types": set(),
                           "gradients": [], "total": 0}
        groups[root]["centers"].append(c["center"])
        groups[root]["sizes"].append(c["size"])
        groups[root]["types"].add(c["type"])
        groups[root]["gradients"].append(c.get("gradient", 0.5))
        groups[root]["total"] += c["size"]

    result = []
    for g in groups.values():
        if g["total"] < min_volume and np.mean(g["gradients"]) < grad_threshold:
            continue
        center = np.mean(g["centers"], axis=0).tolist()
        type_counts = {}
        for sz, t in zip(g["sizes"], g["types"]):
            type_counts[t] = type_counts.get(t, 0) + sz
        art_type = max(type_counts, key=type_counts.get)
        result.append({
            "center": [round(c, 1) for c in center],
            "volume": g["total"],
            "type": art_type,
            "gradation": round(float(np.mean(g["gradients"])), 3),
        })

    result.sort(key=lambda a: -a["volume"])
    return result


def find_articulations(lattice: np.ndarray,
                       min_curvature: float = 0.3,
                       min_bone_volume: int = 5,
                       gravity: tuple = (0, -1, 0)) -> list:
    """Find articulation points via two-pass stress analysis.

    1. Compute bone surface curvature + stress gradient
    2. Cluster hotspots, then consolidate via hierarchical KDTree merging

    Returns list of (center, volume, type, gradation) dicts."""
    nz, ny, nx = lattice.shape
    bone = lattice == BONE
    if bone.sum() < min_bone_volume:
        return []

    curvature = _bone_surface_curvature(lattice)
    gradient = _stress_gradient(lattice)
    hotspots = (curvature > min_curvature) & bone

    labeled, n_labels = _label_components(hotspots)
    if n_labels == 0:
        return []

    raw = []
    for label_id in range(1, n_labels + 1):
        mask = labeled == label_id
        coords = np.argwhere(mask)
        if len(coords) < min_bone_volume:
            continue
        center = coords.mean(axis=0).tolist()
        z, y, x = int(round(center[0])), int(round(center[1])), int(round(center[2]))
        art_type = "articulation"
        for dz, dy, dx in _OFF18:
            nz2, ny2, nx2 = z + dz, y + dy, x + dx
            if (0 <= nz2 < nz and 0 <= ny2 < ny and 0 <= nx2 < nx
                    and lattice[nz2, ny2, nx2] == MUSCLE):
                art_type = "tendon_anchor"
                break
        if len(coords) > 1000:
            art_type = "transition"
        raw.append({"center": center, "size": len(coords),
                     "type": art_type, "gradient": float(gradient[mask].mean())})

    return _consolidate(raw)


# --- component labeling (simple flood-fill) ----------------------------------

def _label_components(mask: np.ndarray) -> tuple:
    """Label connected components in a 3D binary mask (6-connectivity)."""
    from scipy import ndimage as ndi
    # 3D 6-connectivity: center + face neighbors
    struct = np.zeros((3, 3, 3), dtype=int)
    struct[1, 1, :] = 1; struct[1, :, 1] = 1; struct[:, 1, 1] = 1
    labeled, n = ndi.label(mask, structure=struct)
    return labeled, n


# --- export to limb format ---------------------------------------------------

def to_limb_bones(articulations: list) -> list:
    """Convert articulation candidates to limb.Bone objects.

    Each candidate becomes a Bone with:
      - parent: -1 (root, connected later)
      - p0/p1: at the articulation position (small extent)
      - r0/r1: proportional to confidence
      - depth: 0 (refined during integration)

    Returns a list suitable for limb.voxelize().
    """
    from core.terrarium import Bone

    if not articulations:
        return []

    bones = []
    # Scale factor: confidence -> radius
    for i, art in enumerate(articulations):
        z, y, x = art["pos"]
        r = max(art["confidence"] * 0.15, 0.03)
        parent = i - 1 if i > 0 else -1
        bones.append(Bone(
            parent=parent,
            p0=(x * 0.01, y * 0.01, z * 0.01),
            p1=(x * 0.01, y * 0.01, (z + 2) * 0.01),
            r0=r, r1=r,
            depth=0,
        ))

    return bones


# --- CLI ---------------------------------------------------------------------

def main():
    """Test the stress mapper on a sample limb."""
    from core import limb as limb_mod
    from core.matter_gpu import assemble_3d_gpu

    print("Growing limb...")
    bones = limb_mod.bent_limb()
    _s, fleshed, shape, _t = limb_mod.grow_limb(bones, seed=0, target_len=64)

    print(f"Assembling... lattice shape {fleshed.shape}")
    lattice = fleshed  # already assembled by grow_limb

    print("Computing interface normals...")
    normals = interface_normals(lattice)
    print(f"  Normals: {np.isfinite(normals).all()}")

    print("Computing load-bearing axes...")
    bearing = load_bearing_axes(lattice)
    print(f"  Max bearing: {bearing.max():.3f}")

    print("Finding articulations...")
    arts = find_articulations(lattice)
    print(f"  Found {len(arts)} articulation candidates:")
    for a in arts[:10]:
        print(f"    {a['type']:20s}  conf={a['confidence']:.2f}  "
              f"size={a['size']:4d}  pos={a['pos']}")

    bones_out = to_limb_bones(arts)
    print(f"\nExported {len(bones_out)} limb bones")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
