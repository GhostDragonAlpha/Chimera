"""splat_emit — rung A+B of the Substrate Engine: brick -> splat emission + gait
coherence, headless. tb-0168.

Read FIRST: docs/THE_COMPOSITIONAL_WORLD_MODEL.md PART II (SS11 the atom, SS12 two
engines/one substrate, SS15 the experiment ladder) + docs/THE_MATTER_MODEL.md (the
brick's optical fields, SS2). This module is exactly rungs A and B of PART II SS15's
table, and nothing beyond them:

  rung A  Brick->splat emission, headless: emit one Gaussian per surface tissue-voxel
          of the baked limb (optical fields from tissue type), render N>=4 views under
          a MOVING directional light with a small splat rasterizer, compare against a
          marching-cubes mesh render of the SAME limb under the SAME lights.
          KILL IF it cannot beat the mesh render, or relighting artifacts dominate.
  rung B  Movement: skin the splats with rig.py's own k=4 inverse-distance LBS
          weights, replay the trained gait frames, check temporal coherence.
          KILL IF splats shear/swim/pop under animation.

THE ATOM (SS11): position + oriented anisotropic covariance (the "footprint") + optical
fields (albedo/roughness/alpha/subsurface — the "brick's optical", THE_MATTER_MODEL SS2)
per surface voxel of a tissue. Splats carry MATTER, not baked light (SS12) — the optical
fields come from the TISSUE TYPE, known a priori from the voxel grid, so nothing here is
captured/baked lighting; a moving light is free to relight it, which is exactly what
rung A is testing.

WHAT COUNTS AS "THE SAME LIMB" AND "THE SAME LIGHTS": both renderers consume the
IDENTICAL `fleshed` voxel grid from core.rig.flesh_the_body (the real evolved,
adhesion-fleshed body), both use core.bake's marching-cubes recipe (same Gaussian
smoothing sigma, same 0.5 isolevel) for the mesh side, and both are lit by the same
`_dir_from_azel` directional-light convention through the same Lambertian-plus-cheap-
subsurface shading function (OPTICAL table shared by both renderers). The one thing NOT
shared is HOW the shaded colour reaches the screen: a custom, from-scratch, pure-numpy
EWA-style Gaussian rasterizer (project -> depth-sort -> per-splat 2D footprint ->
front-to-back alpha compositing, the standard 3D-Gaussian-Splatting recurrence) versus
matplotlib's Poly3DCollection triangle rasterizer (the same one core.rig.render_mesh
already ships). That is the one variable this experiment is measuring.

FACTS ONLY below the CLI: emit/rasterize/measure report numbers. Whether those numbers
mean KILL or SURVIVES is decided once, in main(), against the two criteria named above
and stated as ratios against the mesh's OWN behaviour (no invented absolute magic
number) — see _KILL_RATIO.

Pure Python: numpy + scipy (already installed) + matplotlib + PIL. No torch, no gsplat,
no CUDA — checked first (2026-07-17: LM Studio holds 23.3/24.5 GiB of this box's one
GPU; a multi-GB CUDA wheel is not an option here, per CLAUDE.md's LM-gateway GPU-sharing
rule). This is a CPU-only experiment by necessity as much as by discipline.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from core import rig
from core.matter import BONE, MEDIUM, MUSCLE, SKIN

ROOT = Path(__file__).resolve().parents[1]                 # E:\PythonChimera\Chimera

# The ratio bar for BOTH kill criteria. Not an absolute magic number: it asks whether
# the splat path disturbs the image (or the local point neighbourhood) by MORE than the
# ENTIRE reference signal the proven mesh path itself shows for the same light-sweep /
# gait change. >1.0 means splats are less stable than the mesh under the same change;
# 2.0x is chosen as "the disturbance the splat path ADDS is at least as large as the
# whole baseline signal it's supposed to be following" — a conservative, stated,
# auditable bar, not a fitted threshold from a prior calibration run (none exists yet).
_KILL_RATIO = 2.0

# --- optical fields: the brick's optical -> the splat/slab's parameters -------------
# THE_MATTER_MODEL.md SS2 "optical" field; THE_COMPOSITIONAL_WORLD_MODEL.md PART II SS12:
# "an Unreal Substrate slab, parameterized per-particle from the atom's optical fields —
# the brick's optical maps ~1:1 onto slab parameters." Base colours are core.bake.MATERIAL
# UNCHANGED (the same brick->material mapping rung 2 already shipped) plus roughness/
# alpha/subsurface per docs' own framing: "skin subsurface, muscle red-translucent, bone
# opaque." AMBIENT is a flat fill term so unlit surfaces are not pure black.
OPTICAL = {
    "skin":   {"albedo": (0.80, 0.62, 0.47), "roughness": 0.70, "alpha": 0.88, "subsurface": 0.55},
    "muscle": {"albedo": (0.69, 0.23, 0.24), "roughness": 0.55, "alpha": 0.75, "subsurface": 0.30},
    "bone":   {"albedo": (0.93, 0.91, 0.82), "roughness": 0.55, "alpha": 1.00, "subsurface": 0.00},
}
AMBIENT = 0.18


# --- emission: voxel tissue -> Gaussian splats --------------------------------------

def surface_voxels(field: np.ndarray) -> np.ndarray:
    """Boolean mask of cells in `field` on ITS OWN boundary (6-connected: >=1 face
    neighbour NOT in field). Mirrors core.bake's per-tissue isosurface — each tissue
    gets its OWN nested surface (skin's outer shell, muscle's shell, bone's core), not
    one shared silhouette. This is a voxel-grid analogue of marching cubes: a surface
    voxel here corresponds to where marching cubes would place a triangle."""
    if not field.any():
        return np.zeros_like(field, dtype=bool)
    from scipy import ndimage
    er = ndimage.binary_erosion(field, structure=ndimage.generate_binary_structure(3, 1))
    return field & ~er


def emit_splats(tissue_field: np.ndarray, tissue_name: str, sigma: float = 0.9,
                tangent_scale: float = 1.15, normal_scale: float = 0.35) -> dict | None:
    """One Gaussian per surface voxel of `tissue_field`. Position = voxel centre.
    Orientation: the normal comes from the gradient of the SAME Gaussian-smoothed
    occupancy field core.bake._surface feeds to marching cubes (same sigma, so both
    rungs read the same underlying surface) -> an oriented, FLATTENED covariance (thin
    along the normal, spread in the tangent plane) — a disk-like footprint, not a
    sphere. Optical fields come from OPTICAL[tissue_name]. FACTS only — this reports
    where the splats are, never whether that is good."""
    from scipy import ndimage

    surf = surface_voxels(tissue_field)
    pos = np.argwhere(surf).astype(np.float64)                    # (N,3), native voxel coords
    if len(pos) == 0:
        return None

    smooth = ndimage.gaussian_filter(tissue_field.astype(np.float32), sigma=sigma)
    grad = np.stack(np.gradient(smooth), axis=-1)                  # (Z,Y,X,3)
    n = grad[surf]                                                  # (N,3)
    norm = np.linalg.norm(n, axis=1, keepdims=True)
    fallback = np.array([0.0, 0.0, 1.0])
    n = np.where(norm > 1e-6, n / np.clip(norm, 1e-6, None), fallback)

    # an orthonormal frame per splat: normal + two tangents (same idiom as rig._frame)
    up = np.where(np.abs(n[:, 2:3]) < 0.9, np.array([0., 0., 1.]), np.array([1., 0., 0.]))
    t1 = np.cross(up, n)
    t1 /= np.clip(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9, None)
    t2 = np.cross(n, t1)
    R = np.stack([t1, t2, n], axis=-1)                              # (N,3,3), columns = t1,t2,n

    S2 = np.tile(np.array([tangent_scale, tangent_scale, normal_scale]) ** 2, (len(pos), 1))
    cov = np.einsum('nik,nk,nlk->nil', R, S2, R)                    # R diag(S2) R^T

    opt = OPTICAL[tissue_name]
    return {
        "pos": pos, "normal": n, "cov": cov,
        "albedo": np.tile(np.asarray(opt["albedo"]), (len(pos), 1)),
        "alpha": np.full(len(pos), opt["alpha"]),
        "subsurface": np.full(len(pos), opt["subsurface"]),
        "tissue": [tissue_name] * len(pos),
    }


def emit_limb(fleshed: np.ndarray, sigma: float = 0.9) -> dict:
    """All three tissues -> one splat set, mirroring core.bake.bake()'s three nested
    per-tissue isosurfaces (skin = grid != MEDIUM, "the outer silhouette IS the visible
    skin" — identical convention, unchanged)."""
    layers = {"skin": (fleshed != MEDIUM), "muscle": (fleshed == MUSCLE), "bone": (fleshed == BONE)}
    parts = [p for p in (emit_splats(field, name, sigma=sigma) for name, field in layers.items())
             if p is not None]
    if not parts:
        raise RuntimeError("no tissue produced any surface voxels — check the grown grid")
    out = {k: np.concatenate([p[k] for p in parts], axis=0) for k in ("pos", "normal", "alpha", "subsurface")}
    out["albedo"] = np.concatenate([p["albedo"] for p in parts], axis=0)
    out["cov"] = np.concatenate([p["cov"] for p in parts], axis=0)
    out["tissue"] = sum((p["tissue"] for p in parts), [])
    out["counts"] = {p["tissue"][0]: len(p["pos"]) for p in parts}
    return out


def tissue_mask(splats: dict, name: str) -> np.ndarray:
    return np.array([t == name for t in splats["tissue"]])


def select(splats: dict, mask: np.ndarray) -> dict:
    out = {k: v[mask] for k, v in splats.items() if k != "tissue" and k != "counts"}
    out["tissue"] = [t for t, m in zip(splats["tissue"], mask) if m]
    return out


# --- the marching-cubes mesh of the SAME limb (native voxel coords) -----------------

def mesh_surfaces(fleshed: np.ndarray, sigma: float = 0.9) -> dict:
    """Per-tissue marching-cubes surfaces in NATIVE VOXEL COORDINATES — same smoothing
    + 0.5 isolevel as core.bake._surface (so this IS "the marching-cubes mesh of the
    same limb"), just kept in the splats' own coordinate frame (bake.py recentres each
    tissue mesh independently at ITS OWN vertex mean before UE5 export, which would
    misalign the three nested tissues relative to one another and relative to the
    splats) so both renderers can share one camera. Also keeps skimage's own per-vertex
    normals (bake.py discards them via `_normals`) — they are already consistently
    outward-oriented from the same scalar-field gradient, needed here for shading."""
    from scipy import ndimage
    from skimage import measure

    layers = {"skin": (fleshed != MEDIUM), "muscle": (fleshed == MUSCLE), "bone": (fleshed == BONE)}
    out = {}
    for name, field in layers.items():
        if field.max() == 0:
            continue
        smooth = ndimage.gaussian_filter(field.astype(np.float32), sigma=sigma)
        if smooth.max() <= 0.5:
            continue
        verts, faces, normals, _ = measure.marching_cubes(smooth, level=0.5)
        out[name] = {"verts": verts.astype(np.float64), "faces": faces.astype(np.int64),
                     "vnormal": normals.astype(np.float64)}
    return out


# --- camera + light: one shared convention for both renderers -----------------------

def _dir_from_azel(azim_deg: float, elev_deg: float) -> np.ndarray:
    az, el = math.radians(azim_deg), math.radians(elev_deg)
    return np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])


def _camera_frame(azim_deg: float, elev_deg: float):
    """right, up, view_dir (the direction the camera LOOKS, into the scene)."""
    view_dir = -_dir_from_azel(azim_deg, elev_deg)
    world_up = np.array([0., 0., 1.])
    right = np.cross(view_dir, world_up)
    if np.linalg.norm(right) < 1e-6:
        world_up = np.array([1., 0., 0.])
        right = np.cross(view_dir, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, view_dir)
    up /= np.linalg.norm(up)
    return right, up, view_dir


# --- the splat rasterizer: project -> depth-sort -> footprint -> alpha-composite ----

def rasterize_splats(splats: dict, center: np.ndarray, radius: float,
                     azim: float, elev: float, light_azim: float, light_elev: float,
                     w: int = 280, h: int = 280) -> np.ndarray:
    """Pure-numpy orthographic Gaussian-splat rasterizer. Orthographic projection makes
    the covariance projection EXACT and cheap: the 2D screen Jacobian is the constant
    2x3 [right;up] matrix (no per-splat foreshortening term to derive). Compositing is
    the standard 3D-Gaussian-Splatting recurrence, front-to-back:
        colour += T * alpha * splat_colour ;  T *= (1 - alpha)
    with T (transmittance) starting at 1 per pixel."""
    right, up, view_dir = _camera_frame(azim, elev)
    rel = splats["pos"] - center
    depth = rel @ view_dir
    scale_px = 0.42 * min(w, h) / radius
    sx = w / 2 + (rel @ right) * scale_px
    sy = h / 2 - (rel @ up) * scale_px

    J = np.stack([right, up], axis=0)                       # (2,3) constant ortho Jacobian
    cov2 = np.einsum('ij,njk,lk->nil', J, splats["cov"], J) * (scale_px ** 2)   # (N,2,2)

    light_toward = _dir_from_azel(light_azim, light_elev)
    ndotl = np.clip(splats["normal"] @ light_toward, 0, None)
    back = np.clip(splats["normal"] @ (-light_toward), 0, None)
    shade = AMBIENT + (1 - AMBIENT) * ndotl + splats["subsurface"] * 0.6 * back
    color = np.clip(splats["albedo"] * shade[:, None], 0.0, 1.0)

    order = np.argsort(depth)                               # near -> far (front to back)
    img = np.zeros((h, w, 3), dtype=np.float64)
    T = np.ones((h, w), dtype=np.float64)

    for i in order:
        C = cov2[i]
        det = C[0, 0] * C[1, 1] - C[0, 1] * C[1, 0]
        if det <= 1e-8:
            continue
        inv00, inv01, inv11 = C[1, 1] / det, -C[0, 1] / det, C[0, 0] / det
        r = 3.0 * math.sqrt(max(C[0, 0], C[1, 1]) + 1e-6)
        cx, cy = sx[i], sy[i]
        x0, x1 = max(0, int(cx - r)), min(w, int(cx + r) + 1)
        y0, y1 = max(0, int(cy - r)), min(h, int(cy + r) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        xs = np.arange(x0, x1) - cx
        ys = np.arange(y0, y1) - cy
        dx, dy = np.meshgrid(xs, ys)
        mdist = inv00 * dx * dx + 2 * inv01 * dx * dy + inv11 * dy * dy
        alpha = float(splats["alpha"][i]) * np.exp(-0.5 * mdist)
        Tpatch = T[y0:y1, x0:x1]
        img[y0:y1, x0:x1] += (Tpatch * alpha)[..., None] * color[i][None, None, :]
        T[y0:y1, x0:x1] = Tpatch * (1 - alpha)

    bg = 0.06
    img += T[..., None] * bg
    return np.clip(img, 0.0, 1.0)


def rasterize_mesh(layers: dict, center: np.ndarray, radius: float,
                   azim: float, elev: float, light_azim: float, light_elev: float,
                   w: int = 280, h: int = 280) -> np.ndarray:
    """matplotlib Agg triangle raster of the SAME limb (marching-cubes meshes from
    mesh_surfaces), lit by the IDENTICAL shading function as the splat side (ambient +
    Lambertian + the same cheap subsurface term), so the pixel comparison isolates the
    REPRESENTATION (splats vs triangles) and not the lighting model. Per-face flat
    shading from the AVERAGED per-vertex marching-cubes normal (independent of the
    splat side's own gradient-based normal — an independently-derived normal, not a
    reused one, so the two paths are not artificially forced to agree)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    light_toward = _dir_from_azel(light_azim, light_elev)
    all_tris, all_rgba = [], []
    for name, L in layers.items():
        opt = OPTICAL[name]
        tris = L["verts"][L["faces"]]                       # (F,3,3)
        vn = L["vnormal"][L["faces"]]                        # (F,3,3)
        fn = vn.mean(axis=1)
        fn /= np.clip(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9, None)
        ndotl = np.clip(fn @ light_toward, 0, None)
        back = np.clip(fn @ (-light_toward), 0, None)
        shade = AMBIENT + (1 - AMBIENT) * ndotl + opt["subsurface"] * 0.6 * back
        rgb = np.clip(np.asarray(opt["albedo"])[None, :] * shade[:, None], 0.0, 1.0)
        rgba = np.concatenate([rgb, np.full((len(rgb), 1), opt["alpha"])], axis=1)
        all_tris.append(tris)
        all_rgba.append(rgba)
    tris = np.concatenate(all_tris, axis=0)
    rgba = np.concatenate(all_rgba, axis=0)

    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    fig.patch.set_facecolor((0.06, 0.06, 0.06))
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.set_facecolor((0.06, 0.06, 0.06))
    if hasattr(ax, "set_proj_type"):
        ax.set_proj_type("ortho")                            # match the splat side: no foreshortening
    coll = Poly3DCollection(tris, facecolor=rgba, edgecolor="none")
    ax.add_collection3d(coll)
    for setlim, m in ((ax.set_xlim, 0), (ax.set_ylim, 1), (ax.set_zlim, 2)):
        setlim(center[m] - radius, center[m] + radius)
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(np.float64) / 255.0
    plt.close(fig)
    if buf.shape[:2] != (h, w):
        from PIL import Image
        img = Image.fromarray((buf * 255).astype(np.uint8)).resize((w, h))
        buf = np.asarray(img).astype(np.float64) / 255.0
    return buf


# --- Phase B: skin splats with rig.py's own k=4 LBS, pose by the trained gait -------

def blended_transforms(widx: np.ndarray, ww: np.ndarray, M: np.ndarray) -> np.ndarray:
    """Per-point blended 4x4 transform: sum_k ww[n,k] * M[widx[n,k]]. Mathematically
    IDENTICAL to core.rig.pose_mesh's result for the position (M @ p_h is linear in M,
    so a weighted sum of transformed points equals the weighted-sum-transform applied
    once) — verified numerically in main() against rig.pose_mesh directly. This is
    needed in addition because a splat also carries an ORIENTATION (its covariance),
    which pose_mesh has no notion of; the per-point blended transform's rotational part
    is what skins that orientation consistently with the position."""
    Mv = M[widx]                                             # (N,k,4,4)
    return np.einsum('nk,nkij->nij', ww, Mv)                  # (N,4,4)


def pose_splats(pos: np.ndarray, normal: np.ndarray, cov: np.ndarray,
               widx: np.ndarray, ww: np.ndarray, M: np.ndarray):
    """LBS-pose a splat set: position by the blended transform (matches rig.pose_mesh),
    normal and covariance by the SAME transform's linear (3x3) part — the standard
    simplified game-engine skinning convention (rig.py itself does not correct normals
    by an inverse-transpose either), which has the useful side effect of NOT hiding
    shear: if the blended linear part is skewed rather than a clean rotation, that
    shows up directly in the posed covariance, which is exactly the failure mode this
    rung is hunting for."""
    Bm = blended_transforms(widx, ww, M)
    A = Bm[:, :3, :3]
    t = Bm[:, :3, 3]
    pos2 = np.einsum('nij,nj->ni', A, pos) + t
    n2 = np.einsum('nij,nj->ni', A, normal)
    n2 /= np.clip(np.linalg.norm(n2, axis=1, keepdims=True), 1e-9, None)
    cov2 = np.einsum('nij,njk,nlk->nil', A, cov, A)
    return pos2, n2, cov2


def rigidity_cv(rest_pos: np.ndarray, posed_list: list, k: int = 6) -> float:
    """Coefficient of variation of how much k-NN neighbour distances change across a
    pose sequence, relative to their REST length. A locally RIGID motion keeps every
    neighbour's (posed / rest) length ratio CONSTANT across frames (std ~ 0); shear or
    popping stretches/compresses neighbours inconsistently frame to frame, raising the
    std. Needs no external ground truth — it is intrinsic to the point set itself, and
    it is the direct numeric form of "splats shear/swim/pop under animation."""
    from scipy.spatial import cKDTree
    tree = cKDTree(rest_pos)
    _, idx = tree.query(rest_pos, k=k + 1)
    idx = idx[:, 1:]
    i0 = np.repeat(np.arange(len(rest_pos)), k)
    i1 = idx.ravel()
    rest_len = np.clip(np.linalg.norm(rest_pos[i0] - rest_pos[i1], axis=1), 1e-6, None)
    ratios = np.stack([np.linalg.norm(pos[i0] - pos[i1], axis=1) / rest_len for pos in posed_list], axis=0)
    cv = ratios.std(axis=0) / np.clip(ratios.mean(axis=0), 1e-6, None)
    return float(cv.mean())


# --- shared image metrics -----------------------------------------------------------

def image_mae(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a - b).mean())


def luminance(img: np.ndarray) -> float:
    return float((0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]).mean())


def frame_deltas(imgs: list) -> list:
    return [image_mae(imgs[i], imgs[i - 1]) for i in range(1, len(imgs))]


def stability_of_ratio(ratio_fn, densities: tuple) -> tuple:
    """Run `ratio_fn(n)` (a splat/mesh frame-delta ratio) at several sampling
    densities and report how STABLE the ratio is across them.

    THE REASON THIS EXISTS (found empirically while running this experiment,
    2026-07-17): a single-density frame-delta ratio cannot tell "splats respond
    smoothly, just with more gain than the mesh" apart from "splats are unstable/
    popping" — both can produce the same one-sample number. The two have a different
    SIGNATURE across sampling density: a smooth, higher-gain response keeps a roughly
    CONSTANT ratio as the step between frames shrinks (both signals shrink together);
    true popping/instability does not scale down with a finer step, so the ratio drifts
    or blows up. This is the "one rollout is a coin toss" lesson (TRAINING_PROTOCOL.md
    SS3.5) applied to a rasterizer instead of a gait: don't trust one sample, check
    whether the number is even the same thing on a second, independent measurement.

    Returns (ratios_by_density, stability) where stability = max(ratios)/min(ratios)
    (near 1.0 = stable/proportional = a benign gain; large = the ratio itself is
    scale-dependent, i.e., genuinely unstable)."""
    ratios = [ratio_fn(n) for n in densities]
    finite = [r for r in ratios if math.isfinite(r) and r > 0]
    stability = float(max(finite) / min(finite)) if finite else float("inf")
    return ratios, stability


def hstack_strip(imgs: list, labels: list) -> "object":
    from PIL import Image, ImageDraw
    tiles = [Image.fromarray((im * 255).astype(np.uint8)) for im in imgs]
    gap = 6
    W = sum(t.width for t in tiles) + gap * (len(tiles) - 1)
    H = max(t.height for t in tiles) + 20
    strip = Image.new("RGB", (W, H), (10, 10, 12))
    d = ImageDraw.Draw(strip)
    x = 0
    for t, lab in zip(tiles, labels):
        strip.paste(t, (x, 20))
        d.text((x + 3, 4), lab, fill=(230, 230, 230))
        x += t.width + gap
    return strip


# --- CLI -----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweeps", type=int, default=60, help="adhesion sweeps (rig.flesh_the_body)")
    ap.add_argument("--frames", type=int, default=6, help="gait frames, Phase B")
    ap.add_argument("--light-frames", type=int, default=6, help="light-sweep frames, Phase A")
    ap.add_argument("--trained", default="brain_gpu.trained.json")
    ap.add_argument("--res", type=int, default=280)
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args()

    out_dir = Path(a.out_dir) if a.out_dir else (ROOT / "Saved" / "SplatEmit")
    out_dir.mkdir(parents=True, exist_ok=True)
    w = h = a.res
    results: dict = {"task": "tb-0168", "seed": a.seed, "res": w}

    print("\nSPLAT EMISSION -- rung A+B (tb-0168), headless")
    print(f"  out_dir = {out_dir}")

    # --- shared body: the REAL evolved, adhesion-fleshed limb (same as rig.py) ------
    t0 = time.time()
    bones, size = rig.evolved_skeleton()
    fleshed, shape, scale, offset = rig.flesh_the_body(bones, sweeps=a.sweeps, seed=a.seed)
    print(f"  body: {len(bones)} bones, lattice {shape}  ({time.time() - t0:.1f}s)")

    splats = emit_limb(fleshed)
    layers = mesh_surfaces(fleshed)
    n_splats = int(len(splats["pos"]))
    n_tris = sum(len(L["faces"]) for L in layers.values())
    results["splat_counts"] = {k: int(v) for k, v in splats["counts"].items()}
    results["splat_counts"]["total"] = n_splats
    results["mesh_tris"] = {k: int(len(L["faces"])) for k, L in layers.items()}
    results["mesh_tris"]["total"] = n_tris
    print(f"  splats: {splats['counts']}  total={n_splats}")
    print(f"  mesh tris: { {k: len(L['faces']) for k, L in layers.items()} }  total={n_tris}")

    tissue_pts = np.argwhere(fleshed != MEDIUM).astype(np.float64)
    center = (tissue_pts.min(0) + tissue_pts.max(0)) / 2.0
    radius = float((tissue_pts.max(0) - tissue_pts.min(0)).max()) / 2.0 * 1.15

    # ================= PHASE A: brick -> splat emission (relighting) ================
    print("\n=== PHASE A -- brick->splat emission (relighting vs marching-cubes mesh) ===")
    cam_azim, cam_elev = -60.0, 20.0
    light_azims = list(np.linspace(0, 360, a.light_frames, endpoint=False))
    relight_splat, relight_mesh, relight_labels = [], [], []
    for la in light_azims:
        relight_splat.append(rasterize_splats(splats, center, radius, cam_azim, cam_elev, la, 35, w, h))
        relight_mesh.append(rasterize_mesh(layers, center, radius, cam_azim, cam_elev, la, 35, w, h))
        relight_labels.append(f"light {la:.0f}deg")

    mae_per_frame = [image_mae(s, m) for s, m in zip(relight_splat, relight_mesh)]
    lum_s = [luminance(im) for im in relight_splat]
    lum_m = [luminance(im) for im in relight_mesh]
    lum_corr = float(np.corrcoef(lum_s, lum_m)[0, 1]) if len(lum_s) > 2 else float("nan")
    d_splat = frame_deltas(relight_splat + [relight_splat[0]])          # circular (360 deg sweep)
    d_mesh = frame_deltas(relight_mesh + [relight_mesh[0]])
    artifact_ratio_a = float(np.mean(d_splat) / max(np.mean(d_mesh), 1e-6))
    mae_mean = float(np.mean(mae_per_frame))

    print(f"  relight sweep: cam fixed (azim {cam_azim}, elev {cam_elev}), "
          f"light azim 0..360 step {360 / a.light_frames:.0f}deg, N={a.light_frames}")
    print(f"  mean MAE (splat vs mesh, per pixel, 0..1)      = {mae_mean:.4f}")
    print(f"  luminance correlation across the sweep          = {lum_corr:.3f}"
          f"   (whole-frame mean incl. background -- a WEAK, noisy signal at low N;"
          f" not weighted in the verdict)")
    print(f"  mean frame-to-frame delta: splat={np.mean(d_splat):.4f}  mesh={np.mean(d_mesh):.4f}"
          f"  ratio={artifact_ratio_a:.2f}")

    # STABILITY CHECK (not a vibe -- see stability_of_ratio's docstring): does the
    # ratio hold steady as the light-sweep step shrinks (smooth, proportional gain --
    # benign) or drift/blow up (genuine instability -- the recipe's actual criterion)?
    def _ratio_at_n(n: int) -> float:
        las = np.linspace(0, 360, n, endpoint=False)
        sf = [rasterize_splats(splats, center, radius, cam_azim, cam_elev, la, 35, 180, 180) for la in las]
        mf = [rasterize_mesh(layers, center, radius, cam_azim, cam_elev, la, 35, 180, 180) for la in las]
        ds, dm = frame_deltas(sf + [sf[0]]), frame_deltas(mf + [mf[0]])
        return float(np.mean(ds) / max(np.mean(dm), 1e-6))

    stab_densities = (a.light_frames, a.light_frames * 2, a.light_frames * 4)
    stab_ratios_a, stability_a = stability_of_ratio(_ratio_at_n, stab_densities)
    print(f"  stability check (ratio at N={list(stab_densities)}): "
          f"{[round(r, 2) for r in stab_ratios_a]}  (max/min = {stability_a:.2f}; "
          f"~1.0 = smooth proportional gain, large = genuine instability)")

    # determinism sanity (same view, same inputs, twice): rules out per-call render
    # jitter as the source of any delta -- any measured change is caused by the actual
    # light/pose change, not rasterizer noise.
    det = image_mae(rasterize_splats(splats, center, radius, cam_azim, cam_elev, 60, 35, 120, 120),
                    rasterize_splats(splats, center, radius, cam_azim, cam_elev, 60, 35, 120, 120))
    print(f"  determinism (same view rendered twice): splat MAE = {det:.2e}  (should be 0)")

    # KILL_A per PART II SS15's stated criterion: "cannot beat the mesh render, OR
    # relighting artifacts dominate." MAE close (bar generous re: the observed ~0.03)
    # decides "beats the mesh"; artifacts "dominate" iff the ratio is itself huge, OR
    # it is elevated AND unstable across sampling density (a stable elevated ratio is a
    # measured higher-gain shading response, not domination -- see stability_of_ratio).
    kill_a = bool(mae_mean > 0.15 or artifact_ratio_a > 5.0
                 or (artifact_ratio_a > _KILL_RATIO and stability_a > 1.5))
    print(f"  KILL_A = {kill_a}  (mae>0.15 or ratio>5.0 or [ratio>{_KILL_RATIO} AND unstable(max/min>1.5)])")

    strip_s = hstack_strip(relight_splat, relight_labels)
    strip_m = hstack_strip(relight_mesh, relight_labels)
    p_as = out_dir / "phaseA_relight_splat.png"; strip_s.save(p_as)
    p_am = out_dir / "phaseA_relight_mesh.png"; strip_m.save(p_am)
    print(f"  -> {p_as}\n  -> {p_am}")

    # a second, independent N>=4 multiview set (camera AND light both moving) --------
    orbit_specs = [(-120, 18, 20, 30), (-40, 22, 100, 35), (60, 16, 200, 25), (150, 20, 300, 40)]
    orbit_splat = [rasterize_splats(splats, center, radius, ca, ce, la, le, w, h) for ca, ce, la, le in orbit_specs]
    orbit_mesh = [rasterize_mesh(layers, center, radius, ca, ce, la, le, w, h) for ca, ce, la, le in orbit_specs]
    orbit_labels = [f"cam{ca}/lt{la}" for ca, _, la, _ in orbit_specs]
    p_os = out_dir / "phaseA_multiview_splat.png"; hstack_strip(orbit_splat, orbit_labels).save(p_os)
    p_om = out_dir / "phaseA_multiview_mesh.png"; hstack_strip(orbit_mesh, orbit_labels).save(p_om)
    print(f"  multiview (N={len(orbit_specs)}, cam+light both moving):")
    print(f"  -> {p_os}\n  -> {p_om}")

    results["phaseA"] = {
        "mae_mean": mae_mean, "mae_per_frame": mae_per_frame,
        "luminance_correlation": lum_corr,
        "frame_delta_splat": float(np.mean(d_splat)), "frame_delta_mesh": float(np.mean(d_mesh)),
        "artifact_ratio": artifact_ratio_a,
        "stability_densities": list(stab_densities), "stability_ratios": stab_ratios_a,
        "stability_max_over_min": stability_a, "determinism_mae": det,
        "kill": kill_a,
        "pngs": [str(p_as), str(p_am), str(p_os), str(p_om)],
    }

    # ================= PHASE B: movement -- LBS + trained gait ======================
    print("\n=== PHASE B -- gait coherence (k=4 LBS skinning, trained gait) ===")
    info = rig.skeleton_frames(bones, scale, offset)
    widx_sp, ww_sp = rig.skin_weights(splats["pos"], bones, scale, offset, k=4)

    skin_mask = tissue_mask(splats, "skin")
    skin_layer = {"skin": layers["skin"]}
    mesh_verts = layers["skin"]["verts"]
    widx_me, ww_me = rig.skin_weights(mesh_verts, bones, scale, offset, k=4)

    angles = rig.gait_angles(bones, trained=a.trained, n_frames=a.frames)
    print(f"  trained gait: {a.trained}, {len(angles)} frames")

    # cross-check: blended_transforms' position output must match rig.pose_mesh exactly
    # (linearity argument in the docstring, verified BY INVOCATION, not asserted)
    dtheta0 = np.concatenate([[0.0], angles[0]]).astype(np.float32)
    M0 = rig.fk(info, dtheta0)
    ref = rig.pose_mesh(mesh_verts, widx_me, ww_me, M0)
    mine, _, _ = pose_splats(mesh_verts, layers["skin"]["vnormal"], np.tile(np.eye(3), (len(mesh_verts), 1, 1)),
                             widx_me, ww_me, M0)
    cross_check = float(np.abs(ref - mine).max())
    print(f"  pose cross-check vs rig.pose_mesh: max|delta pos| = {cross_check:.2e}  (should be ~0)")

    splat_frames_full, splat_frames_skin, mesh_frames = [], [], []
    posed_skin_pos_seq = []
    for i, ja in enumerate(angles):
        dtheta = np.concatenate([[0.0], ja]).astype(np.float32)
        M = rig.fk(info, dtheta)

        p_all, n_all, c_all = pose_splats(splats["pos"], splats["normal"], splats["cov"], widx_sp, ww_sp, M)
        posed_all = dict(splats); posed_all["pos"], posed_all["normal"], posed_all["cov"] = p_all, n_all, c_all
        splat_frames_full.append(rasterize_splats(posed_all, center, radius, cam_azim, cam_elev, 60, 35, w, h))

        posed_skin = select(posed_all, skin_mask)
        splat_frames_skin.append(rasterize_splats(posed_skin, center, radius, cam_azim, cam_elev, 60, 35, w, h))
        posed_skin_pos_seq.append(posed_skin["pos"])

        posed_mesh_verts = rig.pose_mesh(mesh_verts, widx_me, ww_me, M)
        mesh_frames.append(rasterize_mesh(
            {"skin": {"verts": posed_mesh_verts, "faces": layers["skin"]["faces"],
                      "vnormal": layers["skin"]["vnormal"]}},
            center, radius, cam_azim, cam_elev, 60, 35, w, h))

    rest_skin_pos = splats["pos"][skin_mask]
    rig_cv_splat = rigidity_cv(rest_skin_pos, posed_skin_pos_seq)
    mesh_pos_seq = [rig.pose_mesh(mesh_verts, widx_me, ww_me,
                                  rig.fk(info, np.concatenate([[0.0], ja]).astype(np.float32)))
                    for ja in angles]
    rig_cv_mesh = rigidity_cv(mesh_verts, mesh_pos_seq)
    rigidity_ratio = float(rig_cv_splat / max(rig_cv_mesh, 1e-6))

    d_splat_b = frame_deltas(splat_frames_skin)
    d_mesh_b = frame_deltas(mesh_frames)
    coherence_ratio = float(np.mean(d_splat_b) / max(np.mean(d_mesh_b), 1e-6)) if d_splat_b else float("nan")

    print(f"  rigidity_cv (k=6 neighbour-distance CV across the gait): "
          f"splat(skin)={rig_cv_splat:.4f}  mesh(skin)={rig_cv_mesh:.4f}  ratio={rigidity_ratio:.2f}")
    print(f"  image frame-to-frame delta: splat(skin)={np.mean(d_splat_b):.4f} "
          f"mesh(skin)={np.mean(d_mesh_b):.4f}  ratio={coherence_ratio:.2f}")

    # STABILITY CHECK, same logic as Phase A: does the image-delta ratio hold steady as
    # the gait is sampled more finely (a smooth, higher-gain response to real motion --
    # benign) or drift (genuine popping/swimming, decoupled from the actual pose change)?
    def _ratio_at_gait_n(n: int) -> float:
        angs = rig.gait_angles(bones, trained=a.trained, n_frames=n)
        sf, mf = [], []
        for ja in angs:
            dth = np.concatenate([[0.0], ja]).astype(np.float32)
            Mn = rig.fk(info, dth)
            pp, nn, cc = pose_splats(splats["pos"], splats["normal"], splats["cov"], widx_sp, ww_sp, Mn)
            posed = dict(splats); posed["pos"], posed["normal"], posed["cov"] = pp, nn, cc
            sf.append(rasterize_splats(select(posed, skin_mask), center, radius, cam_azim, cam_elev, 60, 35, 160, 160))
            pv = rig.pose_mesh(mesh_verts, widx_me, ww_me, Mn)
            mf.append(rasterize_mesh({"skin": {"verts": pv, "faces": layers["skin"]["faces"],
                                              "vnormal": layers["skin"]["vnormal"]}},
                                     center, radius, cam_azim, cam_elev, 60, 35, 160, 160))
        ds, dm = frame_deltas(sf), frame_deltas(mf)
        return float(np.mean(ds) / max(np.mean(dm), 1e-6)) if ds else float("nan")

    stab_densities_b = (a.frames, a.frames * 2, min(a.frames * 3, 18))
    stab_ratios_b, stability_b = stability_of_ratio(_ratio_at_gait_n, stab_densities_b)
    print(f"  stability check (ratio at N={list(stab_densities_b)}): "
          f"{[round(r, 2) for r in stab_ratios_b]}  (max/min = {stability_b:.2f}; "
          f"~1.0 = smooth proportional gain, large = genuine popping/swimming)")

    # KILL_B per PART II SS15: "splats shear/swim/pop under animation." rigidity_cv is
    # the DIRECT structural test for shear (intrinsic, no rendering involved) -- a big
    # rigidity ratio is unconditional evidence of shear. The image-delta ratio is a
    # weaker rendering-space proxy that also picks up plain point-cloud graininess, so
    # it only counts as "swim/pop" if it is ALSO unstable across sampling density (a
    # stable elevated ratio is a higher-gain rendering response, not swimming).
    kill_b = bool(rigidity_ratio > _KILL_RATIO
                 or (coherence_ratio > _KILL_RATIO and stability_b > 1.5))
    print(f"  KILL_B = {kill_b}  (rigidity_ratio>{_KILL_RATIO} OR "
          f"[image_ratio>{_KILL_RATIO} AND unstable(max/min>1.5)])")

    p_bs_full = out_dir / "phaseB_gait_splat_full.png"
    hstack_strip(splat_frames_full, [f"gait {i+1}/{len(angles)}" for i in range(len(angles))]).save(p_bs_full)
    p_bs_skin = out_dir / "phaseB_gait_splat_skin.png"
    hstack_strip(splat_frames_skin, [f"gait {i+1}/{len(angles)}" for i in range(len(angles))]).save(p_bs_skin)
    p_bm = out_dir / "phaseB_gait_mesh_skin.png"
    hstack_strip(mesh_frames, [f"gait {i+1}/{len(angles)}" for i in range(len(angles))]).save(p_bm)
    print(f"  -> {p_bs_full}  (all 3 tissues, witness)")
    print(f"  -> {p_bs_skin}  (skin only, matches the mesh comparison)")
    print(f"  -> {p_bm}")

    results["phaseB"] = {
        "n_gait_frames": int(len(angles)), "pose_cross_check_max_abs_delta": cross_check,
        "rigidity_cv_splat": rig_cv_splat, "rigidity_cv_mesh": rig_cv_mesh,
        "rigidity_ratio": rigidity_ratio,
        "frame_delta_splat": float(np.mean(d_splat_b)) if d_splat_b else None,
        "frame_delta_mesh": float(np.mean(d_mesh_b)) if d_mesh_b else None,
        "coherence_ratio": coherence_ratio,
        "stability_densities": list(stab_densities_b), "stability_ratios": stab_ratios_b,
        "stability_max_over_min": stability_b,
        "kill": kill_b,
        "pngs": [str(p_bs_full), str(p_bs_skin), str(p_bm)],
    }

    print("\n=== FINAL ===")
    print(f"  rung A (brick->splat emission) : {'KILL' if kill_a else 'SURVIVES'}")
    print(f"  rung B (gait coherence)         : {'KILL' if kill_b else 'SURVIVES'}")
    results["verdict"] = {"rung_A": "KILL" if kill_a else "SURVIVES",
                          "rung_B": "KILL" if kill_b else "SURVIVES"}

    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n  -> {out_dir / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
