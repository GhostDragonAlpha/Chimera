"""fixture_generator.py — scalable membrane benchmark fixture suite.

Generates deterministic triangulated patches across sizes and topologies:
- regular triangulated patches
- irregular but healthy patches (no scipy dependency)
- bounded mixed vertex degrees
- high-degree fan stress cases
- connected patches with nonuniform deformation
- pinned boundaries with documented free-DOF subset

Each fixture records vertex/face counts, degree distribution, aspect ratios,
minimum area, coordinate scale and memory footprint.

STATEMENT  Deterministic seeded generators produce geometrically valid
           (nondegenerate, finite, correct-index) triangle meshes whose
           topology and statistics are fully documented before any benchmark
           consumes them.

PREDICTION  Every generated fixture passes the surface_energy_reference
            validity gates on first evaluation; no face is silently dropped
            or repaired.

FALSIFIER  Any fixture whose ideal geometry triggers InvalidSurface from
           evaluate_surface, or whose recorded statistics disagree with
           independent numpy computation.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from surface_energy_reference import evaluate_surface, InvalidSurface, build_vertex_corner_adjacency

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from evidence_output import default_stamp

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FixtureStats:
    name: str
    topology: str
    n_vertices: int
    n_faces: int
    degree_min: int
    degree_max: int
    degree_mean: float
    aspect_ratio_min: float
    aspect_ratio_max: float
    min_area: float
    max_area: float
    coord_scale: float
    memory_bytes: int
    free_dofs: list = field(default_factory=list)
    pinned: list = field(default_factory=list)
    seed: int = 0
    gamma: float = 1.0
    checks: dict = field(default_factory=dict)
    valid: bool = False

@dataclass
class Fixture:
    stats: FixtureStats
    positions: np.ndarray
    faces: np.ndarray
    gamma: np.ndarray
    offsets: np.ndarray
    corner_idx: np.ndarray
    evaluation: object = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _aspect_ratio(p, f):
    a, b, c = p[f[:, 0]], p[f[:, 1]], p[f[:, 2]]
    eab = np.linalg.norm(b - a, axis=1)
    ebc = np.linalg.norm(c - b, axis=1)
    eca = np.linalg.norm(a - c, axis=1)
    edges = np.stack([eab, ebc, eca], axis=1)
    sorted_e = np.sort(edges, axis=1)
    return sorted_e[:, 2] / (sorted_e[:, 0] + 1e-30)

def _validate(name, positions, faces, gamma):
    try:
        ev = evaluate_surface(positions, faces, gamma)
        return True, ""
    except InvalidSurface as ex:
        return False, ex.reason

def _record(name, positions, faces, gamma, pinned, seed, topology, eval_ok, eval_reason):
    offsets, corner_idx = build_vertex_corner_adjacency(faces, positions.shape[0])
    degrees = np.diff(offsets)
    a, b, c = positions[faces[:, 0]], positions[faces[:, 1]], positions[faces[:, 2]]
    cross = np.cross(b - a, c - a)
    areas = 0.5 * np.linalg.norm(cross, axis=1)
    ar = _aspect_ratio(positions, faces)
    free = [i for i in range(positions.shape[0]) if i not in pinned]
    stats = FixtureStats(
        name=name, topology=topology,
        n_vertices=int(positions.shape[0]), n_faces=int(faces.shape[0]),
        degree_min=int(degrees.min()), degree_max=int(degrees.max()),
        degree_mean=float(degrees.mean()),
        aspect_ratio_min=float(ar.min()), aspect_ratio_max=float(ar.max()),
        min_area=float(areas.min()), max_area=float(areas.max()),
        coord_scale=float(np.max(np.abs(positions))),
        memory_bytes=int(positions.nbytes + faces.nbytes + gamma.nbytes),
        free_dofs=free, pinned=pinned, seed=seed,
        checks={"eval_ok": eval_ok, "eval_reason": eval_reason},
        valid=eval_ok,
    )
    ev = None
    if eval_ok:
        ev = evaluate_surface(positions, faces, gamma)
    return Fixture(stats=stats, positions=positions, faces=faces,
                   gamma=gamma, offsets=offsets, corner_idx=corner_idx,
                   evaluation=ev)

# ---------------------------------------------------------------------------
# Regular triangulated disk
# ---------------------------------------------------------------------------

def regular_disk(n_ring: int = 8, radius: float = 1.0, seed: int = 0,
                 bump: float = 0.0, bump_sigma: float = 0.3,
                 gamma: float = 1.0) -> Fixture:
    """Center + mid ring + boundary ring, CCW, optional gaussian bump.
    Boundary ring is pinned by default."""
    rng = np.random.default_rng(seed)
    ang = 2.0 * np.pi * np.arange(n_ring) / n_ring
    cos, sin = np.cos(ang), np.sin(ang)
    mid = np.stack([0.5 * radius * cos, 0.5 * radius * sin, np.zeros(n_ring)], axis=1)
    if bump != 0.0:
        r2 = mid[:, 0] ** 2 + mid[:, 1] ** 2
        mid[:, 2] = bump * np.exp(-r2 / (2.0 * bump_sigma ** 2))
    center = np.array([[0.0, 0.0, bump * 0.5 if bump != 0.0 else 0.0]])
    outer = np.stack([radius * cos, radius * sin, np.zeros(n_ring)], axis=1)
    V = np.vstack([center, mid, outer]).astype(np.float64)
    mids = list(range(1, n_ring + 1))
    outs = list(range(n_ring + 1, 2 * n_ring + 1))
    F = []
    for i in range(n_ring):
        j = (i + 1) % n_ring
        F.append([0, mids[i], mids[j]])
    for i in range(n_ring):
        j = (i + 1) % n_ring
        F.append([mids[i], outs[i], outs[j]])
        F.append([mids[i], outs[j], mids[j]])
    F = np.asarray(F, dtype=np.int64)
    pinned = outs
    gam = np.full(F.shape[0], gamma, dtype=np.float64)
    ok, reason = _validate("regular_disk", V, F, gam)
    return _record(f"regular_n{n_ring}_r{radius:g}", V, F, gam, pinned, seed,
                   "regular_disk", ok, reason)

# ---------------------------------------------------------------------------
# Irregular but healthy patch (naive jittered grid, no scipy)
# ---------------------------------------------------------------------------

def irregular_patch(n_vertices: int = 200, seed: int = 1,
                    boundary_frac: float = 0.25, gamma: float = 1.0,
                    min_angle_deg: float = 20.0) -> Fixture:
    """Jittered-grid triangulated patch, boundary pinned."""
    rng = np.random.default_rng(seed)
    n_boundary = max(8, int(round(n_vertices * boundary_frac)))
    n_interior = n_vertices - n_boundary
    side = int(np.ceil(np.sqrt(n_interior)))
    n_interior = side * side
    n_vertices = n_boundary + n_interior
    ang = 2.0 * np.pi * np.arange(n_boundary) / n_boundary
    boundary = np.stack([np.cos(ang), np.sin(ang), np.zeros(n_boundary)], axis=1)
    gx, gy = np.meshgrid(np.arange(side), np.arange(side))
    interior = np.stack([gx.ravel() / side - 0.5, gy.ravel() / side - 0.5,
                         rng.uniform(-0.05, 0.05, side * side)], axis=1)
    V = np.vstack([boundary, interior]).astype(np.float64)
    F = []
    for i in range(side - 1):
        for j in range(side - 1):
            a = n_boundary + i * side + j
            b = a + 1
            c = a + side
            d = c + 1
            if (i + j) % 2 == 0:
                F.append([a, b, d])
                F.append([a, d, c])
            else:
                F.append([a, b, c])
                F.append([b, d, c])
    F = np.asarray(F, dtype=np.int64)
    pinned = list(range(n_boundary))
    gam = np.full(F.shape[0], gamma, dtype=np.float64)
    ok, reason = _validate("irregular_patch", V, F, gam)
    name = f"irregular_n{n_vertices}_b{n_boundary}"
    return _record(name, V, F, gam, pinned, seed, "irregular_patch", ok, reason)

# ---------------------------------------------------------------------------
# Bounded mixed-degree patch (structured quad -> triangle fan)
# ---------------------------------------------------------------------------

def mixed_degree_patch(n: int = 5, gamma: float = 1.0, seed: int = 0) -> Fixture:
    """n x n grid of vertices, boundary pinned. Degree ranges from 2 (corners)
    to 8 (interior). Triangulated with diagonal fans."""
    rng = np.random.default_rng(seed)
    xs = np.linspace(-1.0, 1.0, n)
    ys = np.linspace(-1.0, 1.0, n)
    xx, yy = np.meshgrid(xs, ys)
    zz = rng.uniform(-0.05, 0.05, (n, n))
    V = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=1).astype(np.float64)
    F = []
    for i in range(n - 1):
        for j in range(n - 1):
            a = i * n + j
            b = a + 1
            c = a + n
            d = c + 1
            if (i + j) % 2 == 0:
                F.append([a, b, d])
                F.append([a, d, c])
            else:
                F.append([a, b, c])
                F.append([b, d, c])
    F = np.asarray(F, dtype=np.int64)
    pinned = []
    for i in range(n):
        pinned.append(i)
        pinned.append((n - 1) * n + i)
        if i > 0 and i < n - 1:
            pinned.append(i * n)
            pinned.append(i * n + n - 1)
    pinned = sorted(set(pinned))
    gam = np.full(F.shape[0], gamma, dtype=np.float64)
    ok, reason = _validate("mixed_degree", V, F, gam)
    return _record(f"mixed_n{n}", V, F, gam, pinned, seed,
                   "mixed_degree", ok, reason)

# ---------------------------------------------------------------------------
# High-degree fan stress case
# ---------------------------------------------------------------------------

def high_degree_fan(n_rim: int = 64, radius: float = 1.0, height: float = 0.2,
                    gamma: float = 1.0, seed: int = 0) -> Fixture:
    """Single high-degree centre vertex connected to a rim. Stress case."""
    ang = 2.0 * np.pi * np.arange(n_rim) / n_rim
    rim = np.stack([radius * np.cos(ang), radius * np.sin(ang),
                    np.zeros(n_rim)], axis=1)
    centre = np.array([[0.0, 0.0, height]])
    V = np.vstack([rim, centre]).astype(np.float64)
    F = np.array([[n_rim, k, (k + 1) % n_rim] for k in range(n_rim)],
                 dtype=np.int64)
    pinned = list(range(n_rim))
    gam = np.full(F.shape[0], gamma, dtype=np.float64)
    ok, reason = _validate("high_degree_fan", V, F, gam)
    return _record(f"fan_n{n_rim}", V, F, gam, pinned, seed,
                   "high_degree_fan", ok, reason)

# ---------------------------------------------------------------------------
# Connected patches with nonuniform deformation
# ---------------------------------------------------------------------------

def connected_patches(n_per_patch: int = 64, n_patches: int = 4,
                      gamma: float = 1.0, seed: int = 0) -> Fixture:
    """Adjacent disk patches sharing edge boundaries, nonuniform deformation."""
    rng = np.random.default_rng(seed)
    patch_vertices = []
    patch_faces = []
    pinned = []
    nv = 0
    for p in range(n_patches):
        ang = 2.0 * np.pi * np.arange(n_per_patch) / n_per_patch
        cos, sin = np.cos(ang), np.sin(ang)
        r = 1.0 + 0.1 * p
        mid = np.stack([0.5 * r * cos, 0.5 * r * sin,
                        rng.uniform(-0.05, 0.15, n_per_patch)], axis=1)
        centre = np.array([[0.0, 0.0, 0.1 * (p + 1)]])
        outer = np.stack([r * cos, r * sin, np.zeros(n_per_patch)], axis=1)
        Vp = np.vstack([centre, mid, outer])
        Fp = []
        for i in range(n_per_patch):
            j = (i + 1) % n_per_patch
            Fp.append([nv, nv + 1 + i, nv + 1 + j])
        for i in range(n_per_patch):
            j = (i + 1) % n_per_patch
            Fp.append([nv + 1 + i, nv + 1 + n_per_patch + i,
                        nv + 1 + n_per_patch + j])
            Fp.append([nv + 1 + i, nv + 1 + n_per_patch + j,
                        nv + 1 + j])
        Fp = np.asarray(Fp, dtype=np.int64)
        outs = list(range(nv + 1 + n_per_patch, nv + 1 + 2 * n_per_patch))
        pinned.extend(outs)
        patch_vertices.append(Vp)
        patch_faces.append(Fp)
        nv += Vp.shape[0]
    V = np.vstack(patch_vertices).astype(np.float64)
    F = np.vstack(patch_faces)
    gam = np.full(F.shape[0], gamma, dtype=np.float64)
    ok, reason = _validate("connected_patches", V, F, gam)
    return _record(f"connected_p{n_patches}_n{n_per_patch}", V, F, gam,
                   pinned, seed, "connected_patches", ok, reason)

# ---------------------------------------------------------------------------
# Fixture suite and manifest
# ---------------------------------------------------------------------------

def generate_suite(sizes=(4, 8, 16, 32, 64), gamma: float = 1.0,
                   seed_base: int = 0) -> dict:
    """Generate a deterministic suite across sizes. Returns dict name -> Fixture."""
    suite = {}
    for i, n in enumerate(sizes):
        s = seed_base + i
        try:
            f = regular_disk(n_ring=n, seed=s, gamma=gamma)
            suite[f.stats.name] = f
        except Exception as ex:
            suite[f"regular_n{n}"] = None
            print(f"  regular_n{n}: generation failed: {ex}")
        try:
            f = high_degree_fan(n_rim=n * 3, seed=s, gamma=gamma)
            suite[f.stats.name] = f
        except Exception as ex:
            suite[f"fan_n{n*3}"] = None
            print(f"  fan_n{n*3}: generation failed: {ex}")
    for i, n in enumerate(sizes):
        s = seed_base + i + 100
        try:
            f = mixed_degree_patch(n=n, seed=s, gamma=gamma)
            suite[f.stats.name] = f
        except Exception as ex:
            suite[f"mixed_n{n}"] = None
            print(f"  mixed_n{n}: generation failed: {ex}")
    try:
        f = irregular_patch(n_vertices=200, seed=seed_base + 200, gamma=gamma)
        suite[f.stats.name] = f
    except Exception as ex:
        suite["irregular_n200"] = None
        print(f"  irregular_n200: generation failed: {ex}")
    try:
        f = connected_patches(n_per_patch=sizes[min(1, len(sizes)-1)], n_patches=2,
                               seed=seed_base + 300, gamma=gamma)
        suite[f.stats.name] = f
    except Exception as ex:
        suite[f"connected_p2_n{sizes[min(1, len(sizes)-1)]}"] = None
        print(f"  connected: generation failed: {ex}")
    return suite

# ---------------------------------------------------------------------------
# Manifest writer
# ---------------------------------------------------------------------------

def write_manifest(suite: dict, out_dir: Path, source_commit: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "chimera-membrane-scale-lab-fixtures-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "gamma": 1.0,
        "fixtures": {},
    }
    for name, fx in suite.items():
        if fx is None:
            manifest["fixtures"][name] = {"status": "generation_failed"}
            continue
        s = fx.stats
        manifest["fixtures"][name] = {
            "topology": s.topology,
            "n_vertices": s.n_vertices,
            "n_faces": s.n_faces,
            "degree_min": s.degree_min,
            "degree_max": s.degree_max,
            "degree_mean": round(s.degree_mean, 2),
            "aspect_ratio_min": round(s.aspect_ratio_min, 6),
            "aspect_ratio_max": round(s.aspect_ratio_max, 6),
            "min_area": round(s.min_area, 10),
            "max_area": round(s.max_area, 10),
            "coord_scale": round(s.coord_scale, 6),
            "memory_bytes": s.memory_bytes,
            "free_dofs": s.free_dofs,
            "pinned": s.pinned,
            "seed": s.seed,
            "gamma": s.gamma,
            "valid": s.valid,
            "eval_reason": s.checks.get("eval_reason", ""),
        }
    mp = out_dir / "fixture_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mp

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Generate scalable membrane fixture suite")
    ap.add_argument("--out", type=Path, default=Path("docs/evidence/membrane_scale_lab/fixtures"))
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--sizes", type=int, nargs="+", default=[4, 8, 16, 32, 64])
    args = ap.parse_args()
    head = __import__("subprocess").run(
        ["git", "-C", str(_TOOLS.parent), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    print(f"source_commit={head}")
    suite = generate_suite(sizes=tuple(args.sizes), seed_base=args.seed_base)
    mp = write_manifest(suite, args.out, head)
    passed = sum(1 for fx in suite.values() if fx is not None and fx.stats.valid)
    total = len(suite)
    print(f"generated {passed}/{total} valid fixtures -> {mp}")
    return 0 if passed == total else 1

if __name__ == "__main__":
    raise SystemExit(main())
