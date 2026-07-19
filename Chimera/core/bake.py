"""rung 2 — THE BAKE: grown voxel anatomy -> a UE5-importable multi-material mesh.

This is the boundary the whole Matter Model was built toward: where the cellular model
stops being a voxel array (core/limb.py) and becomes an asset Unreal Engine 5 renders.

    bricks (genotype)  ->  THE BAKE  ->  a Nanite-ready mesh + materials (phenotype)

Per docs/THE_MATTER_MODEL.md §4, the bake is per-TISSUE surface extraction, not one blob:
marching cubes on each tissue's occupancy field gives bone, muscle and skin as three
NESTED meshes with three materials. That is what the architecture wants — each tissue is
its own mesh, so the skin can hide the muscle until a cut reveals it (rung 4's
coalesce/fracture), and each is independently Nanite-able.

    skin   = the outer surface (tissue vs medium)  -> the visible character
    muscle = the muscle occupancy shell            -> revealed on a cut
    bone   = the bone occupancy solid              -> the core

A light Gaussian on the occupancy field before marching cubes turns stair-stepped voxels
into smooth surfaces at the 0.5 isolevel — the same move that lets a low-res field carry a
high-res look, which is exactly what Nanite then renders for pennies.

Headless and verifiable: it reports triangle counts, bounds and watertightness, and exports
a .glb (glTF binary — UE5's Interchange importer reads it and carries the materials). The
in-editor half (import + enable Nanite + Chaos Flesh) is core/bake_to_ue5.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy import ndimage
from skimage import measure
import trimesh

from core import limb
from core.matter import BONE, MEDIUM, MUSCLE, SKIN

# PBR base colours (linear RGBA, 0..1). The optical field of the brick (§2) becomes a UE5
# material here — this is why "shadows and everything" fall out: the renderer shadows a
# standard material like any other surface.
MATERIAL = {
    "skin":   (0.80, 0.62, 0.47, 1.0),
    "muscle": (0.69, 0.23, 0.24, 1.0),
    "bone":   (0.93, 0.91, 0.82, 1.0),
}


def _surface(field: np.ndarray, sigma: float):
    """Marching cubes on a smoothed occupancy field. Returns (verts, faces) or None if the
    tissue is too thin/absent to bound a surface."""
    if field.max() == 0:
        return None
    smooth = ndimage.gaussian_filter(field.astype(np.float32), sigma=sigma)
    if smooth.max() <= 0.5:                       # nothing crosses the isolevel
        return None
    try:
        verts, faces, _normals, _vals = measure.marching_cubes(smooth, level=0.5)
    except (ValueError, RuntimeError):
        return None
    return verts, faces


def bake(grid, shape, target_cm: float = 60.0, sigma: float = 0.9) -> trimesh.Scene:
    """Grown voxel anatomy -> a trimesh Scene of three materialed meshes, scaled to a
    sensible size in UE5 units (1 uu = 1 cm)."""
    long_axis = max(shape)
    scale = target_cm / long_axis

    layers = {
        "skin":   (grid != MEDIUM),               # the outer silhouette IS the visible skin
        "muscle": (grid == MUSCLE),
        "bone":   (grid == BONE),
    }
    scene = trimesh.Scene()
    for name, field in layers.items():
        out = _surface(field, sigma)
        if out is None:
            continue
        verts, faces = out
        verts = (verts - verts.mean(axis=0)) * scale      # centre + scale to cm
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
        mesh.visual = trimesh.visual.TextureVisuals(
            material=trimesh.visual.material.PBRMaterial(
                name=name,
                baseColorFactor=[int(255 * c) for c in MATERIAL[name][:3]] + [255],
                roughnessFactor=0.55 if name != "skin" else 0.7,
                metallicFactor=0.0))
        scene.add_geometry(mesh, geom_name=name)
    return scene


def stats(scene: trimesh.Scene) -> dict:
    out = {"meshes": {}, "total_tris": 0}
    for name, geom in scene.geometry.items():
        out["meshes"][name] = {
            "verts": int(len(geom.vertices)),
            "tris": int(len(geom.faces)),
            "watertight": bool(geom.is_watertight),
            "bounds_cm": [round(float(x), 1) for x in geom.extents],
        }
        out["total_tris"] += int(len(geom.faces))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweeps", type=int, default=70)
    ap.add_argument("--out", default="Content/Grown/limb.glb")
    ap.add_argument("--target-cm", type=float, default=60.0)
    a = ap.parse_args()

    _scaffold, fleshed, shape, _targets = limb.grow_limb(limb.bent_limb(),
                                                         sweeps=a.sweeps, seed=a.seed)
    scene = bake(fleshed, shape, target_cm=a.target_cm)
    s = stats(scene)

    print(f"\nBAKE — grown limb -> {len([g for g in scene.geometry])} materialed meshes:")
    for name, m in s["meshes"].items():
        print(f"  {name:<7} {m['tris']:>6,} tris  {m['verts']:>6,} verts  "
              f"watertight={str(m['watertight']):<5}  {m['bounds_cm']} cm")
    print(f"  TOTAL   {s['total_tris']:>6,} tris")

    ok = (len(scene.geometry) >= 2 and s["total_tris"] > 500
          and all(0 < m["tris"] < 5_000_000 for m in s["meshes"].values()))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    scene.export(str(out))
    print(f"\n  -> {out}  ({out.stat().st_size:,} bytes)")

    if ok:
        print("  BAKED. Three nested tissue meshes with materials, in a UE5-importable GLB.")
        print("  Next: core/bake_to_ue5.py imports it and enables Nanite in the live editor.")
        return 0
    print("  FAILED: the mesh is empty or degenerate — check the grown grid.")
    return 1


# ── GS Asset Resolution (Gaussian splatting bake pipeline) ────────────────────
# resolve_assets is MISSING per system context. The following implements the
# content-addressed asset resolver with Tarjan's SCC cycle detection,
# bake_index.json metadata caching, and v0/v1 .splatbin versioned schema.
#
# Incorporated from dialectical turns 1-3.

import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Any


class MissingAssetError(KeyError):
    """Raised by resolve_assets when an asset UUID is not found."""
    def __init__(self, uuid: str) -> None:
        self.uuid = uuid
        super().__init__(f"resolve_assets: asset '{uuid}' not found")


class CyclicAssetDependencyError(ValueError):
    """Raised by resolve_assets when Tarjan's SCC detects a cycle."""
    def __init__(self, cycle_members: list[str]) -> None:
        self.cycle_members = cycle_members
        members_str = " -> ".join(cycle_members)
        super().__init__(
            f"resolve_assets: cyclic dependency via Tarjan's SCC: {members_str}"
        )


SPLATBIN_MAGIC_V1 = b"SPL1"
BAKE_INDEX_FILE = "bake_index.json"


def _tarjan_scc(graph: dict[str, list[str]]) -> list[list[str]]:
    """Tarjan's SCC algorithm for cycle detection."""
    index_counter = 0
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    stack: list[str] = []
    result: list[list[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index_counter
        indices[node] = index_counter
        lowlink[node] = index_counter
        index_counter += 1
        stack.append(node)
        on_stack[node] = True
        for dep in graph.get(node, []):
            if dep not in indices:
                strongconnect(dep)
                lowlink[node] = min(lowlink[node], lowlink[dep])
            elif on_stack.get(dep, False):
                lowlink[node] = min(lowlink[node], indices[dep])
        if lowlink[node] == indices[node]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == node:
                    break
            result.append(scc)

    for node in graph:
        if node not in indices:
            strongconnect(node)
    return result


def assert_no_cycles(graph: dict[str, list[str]]) -> None:
    """Assert the asset dependency graph is acyclic (Tarjan's SCC)."""
    sccs = _tarjan_scc(graph)
    for scc in sccs:
        if len(scc) > 1 or (len(scc) == 1 and scc[0] in graph.get(scc[0], [])):
            raise CyclicAssetDependencyError(scc)


def compute_asset_uuid(payload: bytes) -> str:
    """v5 (SHA-1) content-derived UUID for an asset payload."""
    namespace_dns = bytes.fromhex("6ba7b8109dad11d180b400c04fd430c8")
    digest = hashlib.sha1(namespace_dns + payload).digest()
    hex_str = digest[:16].hex()
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


def read_splatbin_header(path: str | Path) -> dict[str, Any]:
    """Read .splatbin header, dispatching v0 (no magic) / v1 (magic \"SPL1\")."""
    path = Path(path)
    with open(path, "rb") as f:
        magic = f.read(4)
    if magic == SPLATBIN_MAGIC_V1:
        return _read_v1_header(path)
    # v0: first 4 bytes are splat_count uint32
    splat_count = struct.unpack("<I", magic)[0]
    return {"format_version": 0, "splat_count": splat_count}


def _read_v1_header(path: Path) -> dict[str, Any]:
    """Read v1 .splatbin header with batch metadata."""
    with open(path, "rb") as f:
        f.seek(4)
        num_batches = struct.unpack("<I", f.read(4))[0]
        batch_sizes = []
        batch_means = []
        for _ in range(num_batches):
            batch_sizes.append(struct.unpack("<I", f.read(4))[0])
            batch_means.append(list(struct.unpack("<fff", f.read(12))))
        midpoint = struct.unpack("<fff", f.read(12))
        splat_data = f.read()
    return {
        "format_version": 1,
        "splat_count": len(splat_data) // 70,
        "num_batches": num_batches,
        "batch_sizes": batch_sizes,
        "batch_means": batch_means,
        "midpoint_params": {"shift": midpoint[0], "scale": midpoint[1],
                             "logistic_center": midpoint[2]},
    }


def write_splatbin_atomic(
    payload: bytes,
    output_dir: str | Path,
    batch_metadata: dict[str, Any] | None = None,
    update_index: bool = True,
) -> str:
    """Write .splatbin with write-ahead log (.tmp -> fsync -> rename).

    Guarantees crash safety: a crash during write leaves either a complete
    previous version or no file, never a partial write.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    uuid = compute_asset_uuid(payload)
    final_path = output_path / f"{uuid}.splatbin"
    tmp_path = output_path / f"{uuid}.splatbin.tmp"

    header = bytearray(SPLATBIN_MAGIC_V1)
    if batch_metadata:
        bs = batch_metadata.get("batch_sizes", [])
        bm = batch_metadata.get("batch_means", [])
        mp = batch_metadata.get("midpoint_params", [0.0, 1.0, 0.5])
        header += struct.pack("<I", len(bs))
        for size, mean in zip(bs, bm):
            header += struct.pack("<I", size)
            header += struct.pack("<fff", mean[0], mean[1], mean[2])
        header += struct.pack("<fff", mp[0], mp[1], mp[2])
    else:
        header += struct.pack("<I", 0)
        header += struct.pack("<fff", 0.0, 1.0, 0.5)

    with open(tmp_path, "wb") as f:
        f.write(header)
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, final_path)

    if update_index:
        index_path = output_path / BAKE_INDEX_FILE
        tmp_idx = output_path / f"{BAKE_INDEX_FILE}.tmp"
        index = {}
        if index_path.exists():
            with open(index_path, encoding="utf-8") as f:
                index = json.load(f)
        with open(final_path, "rb") as f:
            prefix = f.read(4096)
        digest = hashlib.sha256(prefix).hexdigest()[:8]
        index[uuid] = {
            "payload_path": str(final_path),
            "content_digest": digest,
            "file_offset": 0,
            "size": final_path.stat().st_size,
        }
        with open(tmp_idx, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_idx, index_path)

    return uuid


def resolve_assets(
    uuids: set[str],
    bake_cache: str | Path = "bake_cache",
    asset_store: str | Path = "asset_store",
) -> dict[str, dict[str, Any]]:
    """Resolve asset UUIDs to their baked metadata.

    Resolution order:
    1. Local cache (bake_cache/) with .uuid sidecar
    2. Content-addressed store (asset_store/<uuid>/)
    3. MissingAssetError if absent from both

    Cycle detection via Tarjan's SCC is performed before any I/O.
    """
    bake_path = Path(bake_cache)
    store_path = Path(asset_store)
    index_path = bake_path / BAKE_INDEX_FILE

    # Load index if available
    index: dict[str, Any] = {}
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)

    # Build dependency graph
    graph: dict[str, list[str]] = {}
    for uuid in uuids:
        if uuid in index:
            graph[uuid] = index[uuid].get("deps", [])
        else:
            graph[uuid] = _extract_deps(uuid, bake_path, store_path)

    # Tarjan's SCC before any I/O
    assert_no_cycles(graph)

    # Topological resolve
    resolved: dict[str, dict[str, Any]] = {}
    remaining = set(uuids)
    while remaining:
        batch = {u for u in remaining if all(
            d in resolved for d in graph.get(u, []))}
        if not batch:
            raise RuntimeError(
                f"resolve_assets: {len(remaining)} assets stuck after cycle check")
        for uuid in sorted(batch):
            resolved[uuid] = _load_asset(
                uuid, bake_path, store_path, index.get(uuid))
        remaining -= batch

    return resolved


def _extract_deps(
    uuid: str, cache: Path, store: Path
) -> list[str]:
    """Extract dependency UUIDs from asset metadata."""
    # Check cache .deps.json sidecar
    for f in cache.iterdir() if cache.exists() else []:
        uuid_file = f.with_suffix(".uuid")
        if uuid_file.exists() and uuid_file.read_text(encoding="utf-8").strip() == uuid:
            deps_path = f.with_suffix(".deps.json")
            if deps_path.exists():
                with open(deps_path, encoding="utf-8") as dh:
                    return json.load(dh)
            return []
    # Check store metadata
    meta_path = store / uuid / "metadata.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f).get("dependencies", [])
    return []


def _load_asset(
    uuid: str, cache: Path, store: Path, index_entry: dict | None
) -> dict[str, Any]:
    """Load a single asset payload."""
    # Fast path via index
    if index_entry:
        pp = Path(index_entry.get("payload_path", ""))
        if pp.exists():
            with open(pp, "rb") as f:
                chk = hashlib.sha256(f.read(4096)).hexdigest()[:8]
            if chk == index_entry.get("content_digest", ""):
                hdr = read_splatbin_header(pp)
                return {"uuid": uuid, "payload_path": str(pp), **hdr}

    # Search cache
    if cache.exists():
        for f in cache.iterdir():
            uuid_path = f.with_suffix(".uuid")
            if uuid_path.exists() and uuid_path.read_text(encoding="utf-8").strip() == uuid:
                hdr = read_splatbin_header(f)
                return {"uuid": uuid, "payload_path": str(f), **hdr}

    # Search store
    store_file = store / uuid / "asset.splatbin"
    if store_file.exists():
        hdr = read_splatbin_header(store_file)
        return {"uuid": uuid, "payload_path": str(store_file), **hdr}

    raise MissingAssetError(uuid)


__all__ = [
    # Original bake functions
    "bake", "stats", "main",
    # GS asset resolution additions
    "resolve_assets", "write_splatbin_atomic", "read_splatbin_header",
    "compute_asset_uuid", "MissingAssetError", "CyclicAssetDependencyError",
    "assert_no_cycles",
]


if __name__ == "__main__":
    raise SystemExit(main())
