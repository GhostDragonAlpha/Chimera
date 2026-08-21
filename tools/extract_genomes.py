"""extract_genomes.py -- per-region material genomes, measured relative to the core.

Every labeled margin splat is re-expressed in the LOCAL FRAME of its nearest
inner-core surface point: signed height h along the core's outward normal,
lateral offset (u, v) in the tangent plane, and its rotation quaternion
re-based into that frame. A genome is therefore PORTABLE: it can be re-grown
on any core carrying the same region label (THE_AUTHORED_PIPELINE.md,
Trainable COAT; sectioning per THE_SECTIONING_METHOD.md).

Falsifier for this stage: the (core point, frame, h, u, v) -> world decode
must be LOSSLESS. The tool reconstructs every splat position from its genome
record and refuses to write output if max position error > 0.5 mm.

Usage:
  .venv-gs/Scripts/python.exe tools/extract_genomes.py --splat models/co3d/co3d_34.splat \
      --shells models/co3d/bear34_shells.npz --labels models/co3d/bear34_labels.json \
      --outdir models/co3d/genomes
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402


def core_frames(shells) -> tuple[np.ndarray, np.ndarray]:
    """Outward normals + tangent frames at every inner-core point.

    Normals come from the gradient of the smoothed core occupancy grid
    (a level-set normal -- robust on a voxel solid), sign-checked to point
    toward the outer membrane.
    """
    from scipy import ndimage
    from scipy.spatial import cKDTree

    inner = shells["inner"]
    cell = float(shells["cell"])
    lo = shells["lo"].astype(np.float64)
    grid = shells["solid"]
    occ = np.zeros_like(grid, dtype=np.float64)
    ijk = np.rint((inner - lo) / cell).astype(int)
    occ[tuple(ijk.T)] = 1.0
    smooth = ndimage.gaussian_filter(occ, sigma=1.5)
    gx, gy, gz = np.gradient(smooth, cell)
    g_at = np.stack([
        gx[tuple(ijk.T)], gy[tuple(ijk.T)], gz[tuple(ijk.T)]
    ], axis=1)
    n = -g_at  # occupancy gradient points inward; outward is the negative
    norm = np.linalg.norm(n, axis=1, keepdims=True)
    bad = (norm[:, 0] < 1e-9)
    n = np.where(bad[:, None], np.array([0.0, 1.0, 0.0]), n / np.maximum(norm, 1e-12))
    # sign check: the outer membrane must lie along +n
    d_out = cKDTree(shells["outer"]).query(inner)[1]
    to_outer = shells["outer"][d_out] - inner
    flip = (np.einsum("ij,ij->i", n, to_outer) < 0)
    n[flip] *= -1
    # tangent frame
    ref = np.where(np.abs(n[:, 1:2]) < 0.9, np.array([0.0, 1.0, 0.0]), np.array([1.0, 0.0, 0.0]))
    t1 = np.cross(n, ref)
    t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
    t2 = np.cross(n, t1)
    return n, np.stack([t1, t2, n], axis=2)  # frames: (N,3,3), columns t1,t2,n


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aw, ax, ay, az = a.T
    bw, bx, by, bz = b.T
    return np.stack([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ], axis=1)


def frame_quat(frames: np.ndarray) -> np.ndarray:
    """Rotation matrix (columns t1,t2,n) -> quaternion (w,x,y,z)."""
    m = frames
    tr = m[:, 0, 0] + m[:, 1, 1] + m[:, 2, 2]
    q = np.empty((len(m), 4))
    s = np.sqrt(np.maximum(tr + 1.0, 1e-12)) * 2
    q[:, 0] = 0.25 * s
    q[:, 1] = (m[:, 2, 1] - m[:, 1, 2]) / s
    q[:, 2] = (m[:, 0, 2] - m[:, 2, 0]) / s
    q[:, 3] = (m[:, 1, 0] - m[:, 0, 1]) / s
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def quat_conj(q: np.ndarray) -> np.ndarray:
    out = q.copy()
    out[:, 1:] *= -1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--splat", required=True)
    ap.add_argument("--shells", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()

    lab = json.loads(Path(a.labels).read_text())
    names = lab["regions"]
    denoise = lab.get("denoise", 0.0)
    splat_lab = np.array(lab["splat_labels"])

    shells = np.load(a.shells)
    inner = shells["inner"].astype(np.float64)

    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= 0.5]
    if denoise:
        from scipy.spatial import cKDTree
        keep = cKDTree(shells["outer"]).query(buf[:, 0:3])[0] <= denoise
        buf = buf[keep]
    assert len(buf) == len(splat_lab), (len(buf), len(splat_lab))

    normals, frames = core_frames(shells)
    fq = frame_quat(frames)

    from scipy.spatial import cKDTree
    ctree = cKDTree(inner)
    spos = buf[:, 0:3]
    ci = ctree.query(spos)[1]

    d = spos - inner[ci]
    fr = frames[ci]
    h = np.einsum("ij,ij->i", d, fr[:, :, 2])
    u = np.einsum("ij,ij->i", d, fr[:, :, 0])
    v = np.einsum("ij,ij->i", d, fr[:, :, 1])
    q_local = quat_mul(quat_conj(fq[ci]), buf[:, 10:14])
    q_local /= np.linalg.norm(q_local, axis=1, keepdims=True)

    # FALSIFIER: decode must be lossless
    recon = inner[ci] + h[:, None] * fr[:, :, 2] + u[:, None] * fr[:, :, 0] + v[:, None] * fr[:, :, 1]
    err = np.linalg.norm(recon - spos, axis=1)
    print(f"lossless decode check: max err {err.max()*1000:.4f} mm, mean {err.mean()*1000:.4f} mm")
    if err.max() > 5e-4:
        print("REFUSED: genome encoding is not lossless")
        return 1

    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # Genome cleaning (measured on bear 34, session log 2026-08-21):
    #  - hard features (eyes, nose) are DARK beads; the chalk slab also catches the
    #    fur behind them -> keep only low-luminance splats in those regions.
    #  - static contamination survived denoise inside 4cm of the membrane ->
    #    clip heights at the measured physical relief bound (12 mm; margin p95=10.1).
    LUM_MAX = {"eye_L": 0.30, "eye_R": 0.30, "nose": 0.35}
    H_MAX = 0.012
    summary = {}
    for i, name in enumerate(names):
        m = splat_lab == i
        if not m.any():
            continue
        g = buf[m]
        gh, gu, gv = h[m], u[m], v[m]
        gci, gq = ci[m], q_local[m]
        keep = np.ones(len(g), dtype=bool)
        if name in LUM_MAX:
            keep &= (g[:, 3:6] @ np.array([0.299, 0.587, 0.114])) < LUM_MAX[name]
        keep &= gh <= H_MAX
        dropped = int((~keep).sum())
        g, gh, gu, gv = g[keep], gh[keep], gu[keep], gv[keep]
        gci, gq = gci[keep], gq[keep]
        sc = np.sort(g[:, 7:10], axis=1)
        aniso = sc[:, 2] / np.maximum(sc[:, 0], 1e-12)
        summary[name] = {
            "splats": int(len(g)), "dropped_outliers": dropped,
            "height_mm": {"p05": float(np.percentile(gh, 5)) * 1000,
                          "median": float(np.median(gh)) * 1000,
                          "p95": float(np.percentile(gh, 95)) * 1000},
            "scale_max_mm_median": float(np.median(sc[:, 2])) * 1000,
            "aniso_median": float(np.median(aniso)),
            "alpha_median": float(np.median(g[:, 6])),
            "color_mean": [float(x) for x in g[:, 3:6].mean(0)],
        }
        np.savez_compressed(
            outdir / f"{name}.npz",
            core_idx=gci, h=gh, u=gu, v=gv,
            q_local=gq,
            scale=g[:, 7:10], rgb=g[:, 3:6], alpha=g[:, 6],
        )
    (outdir / "summary.json").write_text(json.dumps({
        "splat": a.splat, "shells": a.shells, "labels": a.labels,
        "regions": summary, "hierarchy": lab["hierarchy"],
    }, indent=2))
    for name, s in summary.items():
        print(f"{name:9s} n={s['splats']:6d} h_med={s['height_mm']['median']:6.1f}mm "
              f"size={s['scale_max_mm_median']:5.2f}mm aniso={s['aniso_median']:5.1f} "
              f"a={s['alpha_median']:.2f}")
    print(f"-> {outdir}/<region>.npz + summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
