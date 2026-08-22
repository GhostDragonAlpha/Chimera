"""f1_eye_decals.py -- plant the anchor's eyes onto the bear mesh as texture decals.

WHY (Rule 0):
  STATEMENT  — the projective bake restored nose/mouth/pads but NOT the eyes: the anchor's
               eye pixels land on the curved muzzle/forehead boundary whose faces tilt away
               from the camera (normal.z < FACE_MIN), so the general bake skipped them.
               The anchor's eyes ARE visible surface, so a direct raycast decal puts them
               on whatever face the ray actually hits, no normal gate.
  PREDICTION — the front render shows two dark button eyes at the anchor's eye positions.
  FALSIFIER  — if the decals land on the muzzle side/ear/back (visible in the render),
               the anchor<->mesh registration is looser than the feature check suggested.

Method: find the two dark eye blobs in the anchor cutout (dark, in the face band,
symmetric about center), inverse-project to world XY, raycast from +Z, convert the hit to
UV, paint a soft dark button-eye disc (with a small highlight) in the atlas at the local
UV scale.

Usage:  .venv-hy3d/Scripts/python.exe tools/f1_eye_decals.py
"""
from __future__ import annotations

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter

SRC = "models/genbear3/f1_hunyuan_anchor03_baked.glb"
DST_GLB = "models/genbear3/f1_hunyuan_anchor03_baked.glb"  # in-place
DST_TEX = "models/genbear3/f1_basecolor_baked.png"
ANCHOR = "capture/genbear3/anchor_03_rgba_1024.png"

# registration used by the bake (from the silhouette fit)
S, CX, CY = 1024.5, 551.0, 526.0

EYE_DARK_MAX = 70        # luminance threshold for "eye" pixels
FACE_BAND = (0.22, 0.38)  # anchor v-fraction band where the eyes live
MIN_BLOB_PX = 40

# Measured on anchor_03_rgba_1024.png (crop x360 y240: pupils at +(105,62) and +(245,55)).
# Auto blob-detection caught ear/edge shadows instead -- these are verified by eye (mine).
EYES = [(465.0, 302.0), (605.0, 295.0)]


def raycast_front(mesh, wx, wy):
    """Nearest +Z hit of the vertical ray through (wx, wy) — vectorized Möller–Trumbore.
    No rtree in this venv, so no trimesh.ray. Returns (face_index, hit_point) or None."""
    tris = mesh.triangles  # (n,3,3)
    o = np.array([wx, wy, 10.0])
    d = np.array([0.0, 0.0, -1.0])
    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.zeros_like(det)
    inv[ok] = 1.0 / det[ok]
    tvec = o - tris[:, 0]
    ubary = np.einsum("ij,ij->i", tvec, p) * inv
    ok &= (ubary >= 0) & (ubary <= 1)
    q = np.cross(tvec, e1)
    vbary = np.einsum("ij,j->i", q, d) * inv
    ok &= (vbary >= 0) & (ubary + vbary <= 1)
    t = np.einsum("ij,ij->i", e2, q) * inv
    ok &= t > 0
    if not ok.any():
        return None
    idx = np.where(ok)[0]
    fi = idx[np.argmin(t[ok])]
    return fi, o + t[fi] * d


def main() -> None:
    scene = trimesh.load(SRC)
    mesh = trimesh.util.concatenate(scene.dump())
    anchor = Image.open(ANCHOR).convert("RGBA")
    A = np.asarray(anchor)
    eyes = EYES
    for u, v in eyes:
        lum = A[int(v), int(u), :3].mean()
        assert lum < EYE_DARK_MAX, f"anchor pixel at ({u},{v}) is not dark ({lum:.0f})"
    print(f"[eyes] using verified positions {eyes}")

    tex = Image.open(DST_TEX).convert("RGB")
    TW, TH = tex.size
    dr = ImageDraw.Draw(tex)

    for u, v in eyes:
        wx = (u - CX) / S
        wy = -(v - CY) / S
        res = raycast_front(mesh, wx, wy)
        if res is None:
            print(f"[eyes] no surface at anchor ({u:.0f},{v:.0f}) -- FAIL")
            continue
        fi, hit = res
        f = mesh.faces[fi]
        # barycentric -> UV
        tri_v = mesh.vertices[f]
        tri_uv = mesh.visual.uv[f]
        M = np.stack([tri_v[1] - tri_v[0], tri_v[2] - tri_v[0]], axis=1)  # 3x2
        lam, *_ = np.linalg.lstsq(M, hit - tri_v[0], rcond=None)
        l0 = 1 - lam.sum()
        uv = l0 * tri_uv[0] + lam[0] * tri_uv[1] + lam[1] * tri_uv[2]
        tx, ty = uv[0] * (TW - 1), (1 - uv[1]) * (TH - 1)
        # local UV scale: atlas px per world unit on this face
        duv = np.stack([tri_uv[1] - tri_uv[0], tri_uv[2] - tri_uv[0]], axis=1)
        dxyz = np.stack([tri_v[1] - tri_v[0], tri_v[2] - tri_v[0]], axis=0)
        scale = np.linalg.norm(duv[:, 0] * [TW, TH]) / max(np.linalg.norm(dxyz[0]), 1e-9)
        r = max(10.0, 0.013 * scale)  # eye ~0.013 world-units radius
        print(f"[eyes] face {fi} hit {np.round(hit,3)} -> atlas ({tx:.0f},{ty:.0f}) r={r:.0f}px")
        # soft dark disc + highlight (button eye)
        for rr, col in ((r, (12, 8, 6)), (r * 0.55, (5, 3, 3))):
            bbox = [tx - rr, ty - rr, tx + rr, ty + rr]
            dr.ellipse(bbox, fill=col)
        hr = r * 0.22
        dr.ellipse([tx - r * 0.35 - hr, ty - r * 0.35 - hr,
                    tx - r * 0.35 + hr, ty - r * 0.35 + hr], fill=(200, 200, 195))

    tex = tex.filter(ImageFilter.GaussianBlur(0.6))
    tex.save(DST_TEX)
    scene2 = trimesh.load(SRC)
    m2 = trimesh.util.concatenate(scene2.dump())
    m2.visual.material.baseColorTexture = tex
    m2.export(DST_GLB)
    print(f"[done] eyes painted, wrote {DST_GLB}")


if __name__ == "__main__":
    main()
