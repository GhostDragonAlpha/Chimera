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


if __name__ == "__main__":
    raise SystemExit(main())
