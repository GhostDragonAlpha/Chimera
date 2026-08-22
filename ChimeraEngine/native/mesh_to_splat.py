"""mesh_to_splat.py — extract a mesh to a point cloud and/or a 3DGS .splat cloud.

WHY (operator directive, 2026-08-19): "set up a technique where we extract and mesh objects
to point clouds." This is the MESH-DERIVED lane of the SOURCE step (exact geometry, legal
per the workflow's source rule) — the same construction marcelpadilla's mesh2splat used on
the koala, but TEXTURE-AWARE: when the mesh carries UVs + a texture image or vertex colors,
the splats get the TRUE color, not an LOD color code.

THEORY (Rule 0):
  STATEMENT  — one thin disk-Gaussian per area-uniform surface sample, oriented to the
               local (smooth) normal, reproduces a mesh under the 3DGS renderer: disk radius
               from the mean inter-sample spacing closes the surface; the thin axis IS the
               normal, so the cloud has no fake thickness.
  PREDICTION — a .splat of the koala mesh renders the same silhouette as koala_500k.splat.
  FALSIFIER  — if the render is holey or fat, the radius-from-spacing derivation is wrong.

Construction (mirrors the documented mesh2splat pipeline, padillasplats meta.json):
  area-uniform surface sampling (trimesh) -> barycentric UV -> texture/vertex color ->
  smooth normals -> disk scale (s, s, 0.1*s) with s = sqrt(2*area/n) (hex-packing closure)
  -> quaternion z->normal (shortest arc) -> cb.save_splat (raw-space inverse handled there).

Outputs BOTH: the point cloud (<out>.points.npy: xyz, rgb, normal) and the .splat.

Usage (from the repo root):
  python ChimeraEngine/native/mesh_to_splat.py models/koala/koala_mesh.obj \
      --n 500000 --out models/koala/koala_mesh2splat.splat
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
if str(_CHIMERA_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CHIMERA_ENGINE))

import cpp_bridge as cb          # noqa: E402


def _z_to_normal_quat(n: np.ndarray) -> np.ndarray:
    """Shortest-arc quaternion [w,x,y,z] rotating +z onto each unit normal n (n,3)."""
    z = np.array([0.0, 0.0, 1.0])
    dot = n @ z                                              # (n,)
    axis = np.cross(np.broadcast_to(z, n.shape), n)          # (n,3)
    w = 1.0 + dot
    q = np.concatenate([w[:, None], axis], axis=1)
    bad = np.linalg.norm(q, axis=1) < 1e-8                   # normal == -z: flip about x
    q[bad] = np.array([0.0, 1.0, 0.0, 0.0])
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def mesh_to_cloud(mesh_path: str, n: int, seed: int = 0, normalize: bool = True,
                  length: float = 1.0):
    """Mesh -> (points (n,3), rgb (n,3) in 0..1, normals (n,3)). Texture via UV if present,
    else vertex colors, else flat grey. Normalization: centered at the bbox center, longest
    axis scaled to --length (default 1.0 — MEASURED from the padillasplats artifact:
    koala_500k.splat spans z -0.5..+0.5; their meta.json text says "2.0", the bytes say 1.0)."""
    import trimesh
    mesh = trimesh.load(mesh_path, force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        raise SystemExit(f"{mesh_path}: not a single mesh ({type(mesh)})")
    if normalize:
        scale = length / float(mesh.extents.max())
        mesh.apply_translation(-mesh.bounds.mean(axis=0))
        mesh.apply_scale(scale)
        print(f"normalized: centered, longest axis -> {length} (scale x{scale:.5f})")
    pts, face_idx = trimesh.sample.sample_surface(mesh, n, seed=seed)

    # smooth (Phong) normals at the samples
    tri = mesh.triangles[face_idx]                           # (n,3,3)
    bary = trimesh.triangles.points_to_barycentric(tri, pts)  # (n,3)
    if mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(mesh.vertices):
        vn = mesh.vertex_normals[mesh.faces[face_idx]]       # (n,3,3)
        normals = np.einsum("nj,njk->nk", bary, vn)
        nrm = np.linalg.norm(normals, axis=1, keepdims=True)
        face_bad = (nrm[:, 0] < 1e-9)
        normals[face_bad] = mesh.face_normals[face_idx][face_bad]
    else:
        normals = mesh.face_normals[face_idx]
    normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)

    # color: texture (UV) > vertex colors > grey
    rgb = np.full((n, 3), 0.5)
    vis = mesh.visual
    if hasattr(vis, "uv") and vis.uv is not None and getattr(vis, "material", None) is not None \
            and getattr(vis.material, "baseColorTexture", None) is not None:
        from PIL import Image
        tex = np.asarray(vis.material.baseColorTexture.convert("RGB"), dtype=np.float32) / 255.0
        uv = np.einsum("nj,njk->nk", bary, vis.uv[mesh.faces[face_idx]])  # (n,2)
        h, w = tex.shape[:2]
        px = np.clip((uv[:, 0] * (w - 1)).round().astype(int), 0, w - 1)
        py = np.clip(((1.0 - uv[:, 1]) * (h - 1)).round().astype(int), 0, h - 1)  # UV v flips
        rgb = tex[py, px]
    elif hasattr(vis, "vertex_colors") and vis.vertex_colors is not None \
            and len(vis.vertex_colors) == len(mesh.vertices):
        vc = vis.vertex_colors[:, :3].astype(np.float32) / 255.0
        rgb = np.einsum("nj,njk->nk", bary, vc[mesh.faces[face_idx]])
    return pts, rgb, normals, float(mesh.area)


def cloud_to_buf14(pts: np.ndarray, rgb: np.ndarray, normals: np.ndarray,
                   area: float, thickness: float = 0.1) -> np.ndarray:
    """Points -> (n,14) splat buffer: thin disks, s = sqrt(2*area/n) (hex packing closes the
    surface), thin axis = the normal, alpha = 1."""
    n = len(pts)
    s = float(np.sqrt(2.0 * area / n))
    scale = np.tile(np.array([s, s, thickness * s]), (n, 1)).astype(np.float32)
    rot = _z_to_normal_quat(normals).astype(np.float32)
    alpha = np.ones((n, 1), dtype=np.float32)
    return np.concatenate([pts.astype(np.float32), rgb.astype(np.float32), alpha,
                           scale, rot], axis=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="mesh file (obj/glb/ply/stl — anything trimesh reads)")
    ap.add_argument("--n", type=int, default=500_000, help="number of surface samples")
    ap.add_argument("--out", required=True, help="output .splat path")
    ap.add_argument("--thickness", type=float, default=0.1, help="disk thin-axis fraction")
    ap.add_argument("--length", type=float, default=1.0,
                    help="normalize: longest axis length (1.0 = the padillasplats artifact scale)")
    a = ap.parse_args()

    pts, rgb, normals, area = mesh_to_cloud(a.target, a.n, length=a.length)
    buf = cloud_to_buf14(pts, rgb, normals, area, a.thickness)
    np.save(Path(a.out).with_suffix(".points.npy"),
            np.concatenate([pts, rgb, normals], axis=1).astype(np.float32))
    cb.save_splat(a.out, buf)
    print(f"mesh -> {a.n} samples (area {area:.4f}, disk s={np.sqrt(2.0 * area / a.n):.5f})")
    print(f"points -> {Path(a.out).with_suffix('.points.npy')}")
    print(f"splat  -> {a.out}")


if __name__ == "__main__":
    main()
