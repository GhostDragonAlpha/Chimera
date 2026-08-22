"""f1_projective_bake.py -- bake the SDXL anchor photo onto the Hunyuan3D bear's texture.

WHY (Rule 0):
  STATEMENT  — the eye's "textureless clay / no eyes" verdict on f1_hunyuan_anchor03 is
               dominated by albedo loss in Hunyuan's multiview paint: the ANCHOR has
               strand-level fur, black eyes, black nose, dark paw pads; the painted
               2048 atlas washed all of that out. The mesh front is geometrically
               registered to the anchor (the shape was generated FROM it), so an
               orthographic projective bake restores the detail where the anchor sees it.
  PREDICTION — after the bake, the front render shows two dark eyes, a black nose,
               dark paw pads and fur strands; the eye's photo verdict improves.
  FALSIFIER  — if the re-judged splat still reads eyeless/smooth on the FRONT, the
               registration is wrong (head bow / pose mismatch), and this approach fails.

Method:
  1. Register: fit (scale, cx, cy) of a weak-perspective projection (world X,Y ->
     anchor u,v) by maximizing IoU between the mesh's projected silhouette and the
     anchor's alpha mask.
  2. Occlusion: rasterize a per-face depth map (nearest +Z wins) at anchor resolution.
  3. Bake: for every texel of every front-facing triangle (normal.z > 0.15), compute
     its 3D position by barycentric interpolation, project to the anchor, and if the
     texel is the visible surface there (depth within tol), blend the anchor color into
     the atlas with a facing-ratio weight.

Usage:  .venv-hy3d/Scripts/python.exe tools/f1_projective_bake.py
"""
from __future__ import annotations

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter

SRC = "models/genbear3/f1_hunyuan_anchor03_bear.glb"
DST_GLB = "models/genbear3/f1_hunyuan_anchor03_baked.glb"
DST_TEX = "models/genbear3/f1_basecolor_baked.png"
ANCHOR = "capture/genbear3/anchor_03_rgba_1024.png"  # 1024^2 rembg cutout of the SDXL anchor

DEPTH_TOL = 0.06      # normalized units: texel must be within this of the nearest surface
FACE_MIN = 0.15       # normal.z below this keeps the Hunyuan paint
FEATHER = 0.35        # normal.z range over which the blend weight ramps 0->1


def load():
    scene = trimesh.load(SRC)
    mesh = trimesh.util.concatenate(scene.dump())
    anchor = Image.open(ANCHOR).convert("RGBA")
    return mesh, anchor


def fit_projection(mesh: trimesh.Trimesh, anchor: Image.Image):
    """Fit u = s*x + cx, v = -s*y + cy by silhouette IoU (coarse-to-fine).

    Silhouette via vertex scatter + dilation (fast), not per-face fills.
    """
    A = np.asarray(anchor)
    amask = A[..., 3] > 128
    H, W = amask.shape
    verts = mesh.vertices

    def silhouette(s, cx, cy):
        u = np.clip((s * verts[:, 0] + cx).astype(int), 0, W - 1)
        v = np.clip((-s * verts[:, 1] + cy).astype(int), 0, H - 1)
        img = np.zeros((H, W), dtype=np.uint8)
        img[v, u] = 1
        return np.asarray(Image.fromarray(img).filter(ImageFilter.MaxFilter(21)), dtype=bool)

    def iou(s, cx, cy):
        m = silhouette(s, cx, cy)
        return (m & amask).sum() / max((m | amask).sum(), 1)

    best = (0.0, (640.0, W / 2, H / 2 - 40))
    for step in (80.0, 20.0, 5.0, 1.25):
        _, (bs, bcx, bcy) = best
        for ds in np.arange(-2, 3) * step:
            for dcx in np.arange(-2, 3) * step:
                for dcy in np.arange(-2, 3) * step:
                    score = iou(bs + ds, bcx + dcx, bcy + dcy)
                    if score > best[0]:
                        best = (score, (bs + ds, bcx + dcx, bcy + dcy))
    score, (s, cx, cy) = best
    print(f"[register] IoU={score:.3f}  s={s:.1f} cx={cx:.1f} cy={cy:.1f}")
    return s, cx, cy, score


def depth_map(mesh, s, cx, cy, W, H):
    """Nearest-z raster at anchor resolution, per-face flat depth. -1 = empty."""
    verts = mesh.vertices
    uv = np.stack([s * verts[:, 0] + cx, -s * verts[:, 1] + cy], axis=1)
    img = Image.new("F", (W, H), -1.0)
    dr = ImageDraw.Draw(img)
    order = np.argsort(verts[mesh.faces][:, :, 2].mean(axis=1))  # far first, near last
    for fi in order:
        f = mesh.faces[fi]
        p = uv[f]
        if (p[:, 0].max() < 0 or p[:, 0].min() >= W
                or p[:, 1].max() < 0 or p[:, 1].min() >= H):
            continue
        z = verts[f, 2].min()
        dr.polygon([tuple(q) for q in p], fill=float(z))
    return np.asarray(img)


def bake(mesh, anchor, s, cx, cy):
    tex = mesh.visual.material.baseColorTexture.copy().convert("RGB")
    TW, TH = tex.size
    tex_np = np.asarray(tex).astype(np.float32)
    wsum = np.zeros((TH, TW), dtype=np.float32)

    A = np.asarray(anchor.convert("RGB")).astype(np.float32)
    amask = np.asarray(anchor)[..., 3] > 128
    H, W = amask.shape
    depth = depth_map(mesh, s, cx, cy, W, H)

    verts = mesh.vertices
    uvs = mesh.visual.uv
    faces = mesh.faces
    fnorm = mesh.face_normals

    n_baked = 0
    for fi in range(len(faces)):
        nz = fnorm[fi, 2]
        if nz <= FACE_MIN:
            continue
        f = faces[fi]
        tuv = uvs[f]  # (3,2) in [0,1]
        px = np.stack([tuv[:, 0] * (TW - 1), (1.0 - tuv[:, 1]) * (TH - 1)], axis=1)
        x0, x1 = int(px[:, 0].min()), int(np.ceil(px[:, 0].max()))
        y0, y1 = int(px[:, 1].min()), int(np.ceil(px[:, 1].max()))
        if x1 <= x0 or y1 <= y0:
            continue
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, TW - 1), min(y1, TH - 1)
        gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        P = np.stack([gx.ravel(), gy.ravel()], axis=1).astype(np.float64)
        a, b, c = px
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (P[:, 0] - c[0]) + (c[0] - b[0]) * (P[:, 1] - c[1])) / den
        l2 = ((c[1] - a[1]) * (P[:, 0] - c[0]) + (a[0] - c[0]) * (P[:, 1] - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not inside.any():
            continue
        l1, l2, l3 = l1[inside], l2[inside], l3[inside]
        Pi = P[inside]
        pos = (l1[:, None] * verts[f[0]] + l2[:, None] * verts[f[1]]
               + l3[:, None] * verts[f[2]])
        au = s * pos[:, 0] + cx
        av = -s * pos[:, 1] + cy
        iu = np.clip(np.round(au).astype(int), 0, W - 1)
        iv = np.clip(np.round(av).astype(int), 0, H - 1)
        ok = amask[iv, iu]
        dz = depth[iv, iu]
        ok &= (dz >= 0) & (pos[:, 2] >= dz - DEPTH_TOL)
        if not ok.any():
            continue
        w = min(1.0, (nz - FACE_MIN) / FEATHER)
        ti = (Pi[ok, 1].astype(int), Pi[ok, 0].astype(int))
        col = A[iv[ok], iu[ok]]
        # max-blend: keep strongest coverage per texel
        cur = wsum[ti]
        take = w > cur
        if take.any():
            t0 = (ti[0][take], ti[1][take])
            wsum[t0] = w
            tex_np[t0] = col[take]
        n_baked += int(take.sum())

    print(f"[bake] texels baked: {n_baked}")
    out = Image.fromarray(np.clip(tex_np, 0, 255).astype(np.uint8))
    out.save(DST_TEX)
    return out


def main() -> None:
    import sys
    mesh, anchor = load()
    print(f"mesh {len(mesh.vertices)}v/{len(mesh.faces)}f, anchor {anchor.size}")
    if len(sys.argv) >= 4:
        # pre-fit transform (e.g. from the wider anisotropic search) — skip the fit
        s, cx, cy = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
        print(f"[register] using given transform s={s} cx={cx} cy={cy}")
    else:
        s, cx, cy, score = fit_projection(mesh, anchor)
        if score < 0.5:
            print("[register] IoU too low -- registration FAILED, refusing to bake")
            return
    new_tex = bake(mesh, anchor, s, cx, cy)
    mesh.visual.material.baseColorTexture = new_tex
    mesh.export(DST_GLB)
    print(f"[done] wrote {DST_GLB}")


if __name__ == "__main__":
    main()
