"""sh_bake.py — bake full 3DGS SH (degree 3) view-dependent color into a single RGB.

WHY: the .splat format stores ONE rgb per splat (DC only). When the training data has
world-fixed lighting (front-lit bear, dark back), the trainer pushes the appearance
into the SH view-dependent terms and leaves DC near-white — so a DC-only conversion
renders as white/grey haze even though the model itself is fine (measured 2026-08-20:
train_out5 val renders bear-ish, converted .splat confetti).

RULE 0:
  STATEMENT  — for a Lambertian-ish object under fixed lighting, evaluating the full
               SH at each splat's OUTWARD direction (normalize(pos - centroid)) recovers
               the correct baked albedo-under-lighting (dark back, bright front).
  PREDICTION — the baked .splat rendered through gsplat matches the trainer's SH
               renders perceptually (bear colors, not white haze).
  FALSIFIER  — if the baked render is still haze/confetti, the haze lives in the
               geometry/alpha, not the color encoding; report honestly.

Usage (repo root):
  .venv-gs/Scripts/python.exe tools/sh_bake.py capture/sv3d_bear/train_out5/ply/point_cloud_29999.ply \
      --out models/genbear3/sv3d5_baked.splat
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))

import cpp_bridge as cb  # noqa: E402
from ply_to_splat import load_3dgs_ply  # noqa: E402  (geometry/alpha decode, header-driven)

C0 = 0.28209479177387814
C1 = 0.4886025119029199
C2 = [1.0925484305920792, -1.0925484305920792, 0.31539156525252005,
      -1.0925484305920792, 0.5462742152960396]
C3 = [-0.5900435899266435, 2.890611442640554, -0.4570457994644658, 0.3731763325901154,
      -0.4570457994644658, 1.445305721320277, -0.5900435899266435]


def load_ply_full(ply_path: str):
    """Header-driven read of ALL float props -> (props, array)."""
    with open(ply_path, "rb") as f:
        props, n = [], 0
        for line in iter(f.readline, b""):
            t = line.strip().split()
            if t[:2] == [b"element", b"vertex"]:
                n = int(t[2])
            elif t[:1] == [b"property"] and t[1] == b"float":
                props.append(t[2].decode())
            elif t[:1] == [b"end_header"]:
                break
        raw = np.fromfile(f, dtype=np.float32, count=n * len(props))
    return props, raw.reshape(n, len(props)).astype(np.float64)


def sh_eval(sh: np.ndarray, dirs: np.ndarray) -> np.ndarray:
    """sh: (N, K, 3) coefficients (K = (deg+1)^2); dirs: (N, 3) unit vectors.
    Returns (N, 3) rgb, pre-clamp, offset +0.5 — standard 3DGS SH eval."""
    x, y, z = dirs[:, 0], dirs[:, 1], dirs[:, 2]
    res = C0 * sh[:, 0]
    if sh.shape[1] > 1:
        res = (res - C1 * y[:, None] * sh[:, 1]
               + C1 * z[:, None] * sh[:, 2]
               - C1 * x[:, None] * sh[:, 3])
    if sh.shape[1] > 4:
        xx, yy, zz, xy, yz, xz = x * x, y * y, z * z, x * y, y * z, x * z
        res = (res + C2[0] * xy[:, None] * sh[:, 4]
               + C2[1] * yz[:, None] * sh[:, 5]
               + C2[2] * (2 * zz - xx - yy)[:, None] * sh[:, 6]
               + C2[3] * xz[:, None] * sh[:, 7]
               + C2[4] * (xx - yy)[:, None] * sh[:, 8])
    if sh.shape[1] > 9:
        xx, yy, zz, xy, yz, xz = x * x, y * y, z * z, x * y, y * z, x * z
        res = (res + C3[0] * (y * (3 * xx - yy))[:, None] * sh[:, 9]
               + C3[1] * (xy * z)[:, None] * sh[:, 10]
               + C3[2] * (y * (4 * yy - xx - zz))[:, None] * sh[:, 11]
               + C3[3] * (z * (2 * zz - 3 * xx - 3 * yy))[:, None] * sh[:, 12]
               + C3[4] * (x * (4 * xx - zz - yy))[:, None] * sh[:, 13]
               + C3[5] * (z * (xx - yy))[:, None] * sh[:, 14]
               + C3[6] * (x * (xx - 3 * yy))[:, None] * sh[:, 15])
    return res + 0.5


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ply")
    ap.add_argument("--out", required=True)
    ap.add_argument("--opacity-raw", action="store_true")
    ap.add_argument("--poses", default=None,
                    help="poses.json (SV3D rings): bake at the facing-weighted mean camera "
                         "direction instead of the raw outward direction")
    ap.add_argument("--bake-mode", choices=["facing", "median"], default="facing",
                    help="facing: single weighted-mean direction (can land BETWEEN cameras, "
                         "where SH3 is unsupervised and oscillates rainbow). median: evaluate "
                         "SH at every actual camera direction, per-channel median — robust to "
                         "unsupervised directions and view-inconsistent colors.")
    ap.add_argument("--cam-radius", type=float, default=1.899)
    ap.add_argument("--norm-transform", default=None,
                    help=".npy 4x4 gsplat normalization transform (PLY is in normalized frame)")
    a = ap.parse_args()

    props, v = load_ply_full(a.ply)
    col = {p: i for i, p in enumerate(props)}
    n_rest = sum(1 for p in props if p.startswith("f_rest"))
    k_total = 1 + n_rest // 3
    print(f"{len(v)} splats, {n_rest} f_rest props -> SH degree "
          f"{int(k_total ** 0.5) - 1} ({k_total} coeffs)")

    # geometry/alpha via the shared decoder (exp scales, sigmoid alpha, quats)
    buf = load_3dgs_ply(a.ply, opacity_raw=a.opacity_raw).astype(np.float64)

    # SH tensor: f_dc_0..2 then f_rest channel-major (gsplat writes (N,3,K)->(N,K*3))
    sh = np.zeros((len(v), k_total, 3))
    sh[:, 0, 0] = v[:, col["f_dc_0"]]
    sh[:, 0, 1] = v[:, col["f_dc_1"]]
    sh[:, 0, 2] = v[:, col["f_dc_2"]]
    for j in range(k_total - 1):
        sh[:, j + 1, 0] = v[:, col[f"f_rest_{j}"]]
        sh[:, j + 1, 1] = v[:, col[f"f_rest_{k_total - 1 + j}"]]
        sh[:, j + 1, 2] = v[:, col[f"f_rest_{2 * (k_total - 1) + j}"]]

    # outward bake direction, refined: mean of directions toward the cameras that
    # actually FACE this splat (dot(outward, dir_to_cam) > 0). Falls back to the
    # raw outward direction when no camera poses are supplied.
    center = np.median(buf[:, 0:3], axis=0)
    d = buf[:, 0:3] - center
    nrm = np.linalg.norm(d, axis=1, keepdims=True)
    d = np.where(nrm > 1e-9, d / np.maximum(nrm, 1e-9), np.array([[0.0, 0.0, 1.0]]))

    if a.poses:
        import json as _json
        import math as _math
        pdata = _json.loads(Path(a.poses).read_text())["poses"]
        # reconstruct camera centers with the same convention as sv3d_to_colmap
        # (y-up, C = r(cos el sin az, sin el, cos el cos az)); radius from --cam-radius
        cams = []
        for p in pdata:
            el, az = _math.radians(p["elevation_deg"]), _math.radians(p["azimuth_deg"])
            cams.append([_math.cos(el) * _math.sin(az), _math.sin(el),
                         _math.cos(el) * _math.cos(az)])
        cams = np.array(cams, dtype=np.float32) * a.cam_radius
        # BUT: the PLY lives in the NORMALIZED gsplat frame; bring cameras into it
        # via the parser transform if provided.
        if a.norm_transform:
            T = np.load(a.norm_transform).astype(np.float32)
            cams = (T[:3, :3] @ cams.T).T + T[:3, 3]
        # chunked (memory-bounded): facing-weighted mean camera direction per splat
        pos32 = buf[:, 0:3].astype(np.float32)
        d32 = d.astype(np.float32)
        d_out = np.empty_like(d32)
        CH = 4096
        for s in range(0, len(pos32), CH):
            e = min(s + CH, len(pos32))
            tc = cams[None, :, :] - pos32[s:e, None, :]            # (B, M, 3) f32
            tc /= np.linalg.norm(tc, axis=2, keepdims=True) + 1e-12
            fw = np.clip((tc * d32[s:e, None, :]).sum(axis=2), 0.0, None)  # (B, M)
            ws = fw.sum(axis=1, keepdims=True)
            db = np.where(ws > 1e-6,
                          (tc * fw[:, :, None]).sum(axis=1) / np.maximum(ws, 1e-12),
                          d32[s:e])
            dn = np.linalg.norm(db, axis=1, keepdims=True)
            d_out[s:e] = np.where(dn > 1e-9, db / np.maximum(dn, 1e-9), d32[s:e])
        d = d_out.astype(np.float64)

    rgb = np.clip(sh_eval(sh, d), 0.0, 1.0)
    if a.bake_mode == "median" and a.poses:
        # per-channel median over ALL actual camera directions (chunked; memory-bounded)
        outc = np.empty((len(sh), 3))
        CH = 2048
        for s in range(0, len(sh), CH):
            e = min(s + CH, len(sh))
            # direction from each splat to each camera (normalized frame)
            tc = cams[None, :, :] - buf[s:e, 0:3].astype(np.float32)[:, None, :]
            tc /= np.linalg.norm(tc, axis=2, keepdims=True) + 1e-12
            M = tc.shape[1]
            acc = np.empty((e - s, M, 3))
            for j in range(M):
                acc[:, j, :] = sh_eval(sh[s:e], tc[:, j, :].astype(np.float64))
            outc[s:e] = np.median(acc, axis=1)
        rgb = np.clip(outc + 0.0, 0.0, 1.0)
    buf[:, 3:6] = rgb

    if a.norm_transform:
        # gsplat exports the PLY in its NORMALIZED frame (rotation + scale, det can be
        # -1 = reflection). Bring the cloud back to the original y-up world so the
        # standard viewer/orient path applies. Points use the full map; quats use the
        # proper-rotation fold (Gaussians are axis-sign symmetric, so flipping one
        # local axis leaves the covariance unchanged).
        import scipy.spatial.transform as _st
        T = np.load(a.norm_transform)
        Rn, tn = T[:3, :3].astype(np.float64), T[:3, 3].astype(np.float64)
        sc = float(np.cbrt(abs(np.linalg.det(Rn))))
        Rr = Rn / sc
        buf[:, 0:3] = (buf[:, 0:3] - tn) @ Rr / sc
        buf[:, 7:10] /= sc
        # Quats: target per-splat world rotation W = Rr.T @ Qn. When det(Rr) < 0
        # (gsplat auto-orient included a mirror) W is improper and has no quaternion.
        # The covariance Sigma = Q S^2 Q^T is invariant to mirroring a LOCAL axis
        # (D = diag(1,1,-1): D S^2 D = S^2), so use W' = Rr.T @ Qn @ D — proper,
        # exact same covariance. (A GLOBAL fold Rr.T @ D — the old code — shears
        # every anisotropic splat; measured 2026-08-20: it turned the bear to mush.)
        Rt = Rr.T
        Qn = _st.Rotation.from_quat(buf[:, [11, 12, 13, 10]]).as_matrix()
        M = Rt[None] @ Qn
        if np.linalg.det(Rt) < 0:
            M = M @ np.diag([1.0, 1.0, -1.0])
        qxyzw = _st.Rotation.from_matrix(M).as_quat()
        buf[:, 10:14] = qxyzw[:, [3, 0, 1, 2]]
        print(f"unnormalized to original world (1/s = {1 / sc:.3f}, "
              f"det(R) = {np.linalg.det(Rr):.1f})")

    cb.save_splat(a.out, buf.astype(np.float32))
    print(f"baked {len(buf)} splats -> {a.out} "
          f"(rgb mean {rgb.mean(axis=0).round(3)}, min {rgb.min():.3f}, max {rgb.max():.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
