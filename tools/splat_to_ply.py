#!/usr/bin/env python
"""splat_to_ply.py -- convert TripoSplat .splat (32-byte) -> standard Inria 3DGS .ply.

For the MLSLabsRenderer UE plugin (imports standard PLY, sh_degree=0 supported).
Frame handling: our canonical frame is +Y up / face +Z (right-handed); Unreal is
Z up / X forward. We apply the CYCLIC permutation p_ue = (p.z, p.x, p.y) -- a
proper rotation (det +1, no mirror; the BERLIN print is the visual falsifier).
Rotations conjugate R_ue = P R P^T; scales permute to match.

PLY field conventions (Inria): f_dc = (c - 0.5) / 0.28209479 ; opacity = logit(a);
scale = ln(s); rot = normalized [w,x,y,z].

  .venv-gs/Scripts/python.exe tools/splat_to_ply.py <in.splat> <out.ply>
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

C0 = 0.28209479
# canon -> UE permutation matrix: p_ue = P @ p_canon  (x_ue=z, y_ue=x, z_ue=y)
P = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=np.float64)


def quat_to_mat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q.T
    return np.stack([
        np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
        np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
        np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1),
    ], axis=-2)


def mat_to_quat(m: np.ndarray) -> np.ndarray:
    t = m[:, 0, 0] + m[:, 1, 1] + m[:, 2, 2]
    q = np.zeros((len(m), 4))
    big = t > 0
    s = np.sqrt(np.maximum(t[big] + 1, 1e-12)) * 2
    q[big] = np.stack([0.25 * s, (m[big, 2, 1] - m[big, 1, 2]) / s,
                       (m[big, 0, 2] - m[big, 2, 0]) / s,
                       (m[big, 1, 0] - m[big, 0, 1]) / s], axis=1)
    for i in np.where(~big)[0]:
        j = int(np.argmax([m[i, 0, 0], m[i, 1, 1], m[i, 2, 2]]))
        k, l = (j + 1) % 3, (j + 2) % 3
        s = np.sqrt(max(m[i, j, j] - m[i, k, k] - m[i, l, l] + 1, 1e-12)) * 2
        q[i, 0] = (m[i, l, k] - m[i, k, l]) / s
        q[i, j + 1] = 0.25 * s
        q[i, k + 1] = (m[i, k, j] + m[i, j, k]) / s
        q[i, l + 1] = (m[i, l, j] + m[i, j, l]) / s
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def main() -> int:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    # frame: "ue" permutes canonical -> UE Z-up; "yup" pre-rotates Rx(180) so that
    # after MLSLabs' own Rx(-90) import rotation the bear lands upright (measured
    # empirically: plugin maps canon +Y -> -Z, canon +Z -> +Y). Proper rotation, no mirror.
    frame = sys.argv[3] if len(sys.argv) > 3 else "ue"
    RX180 = np.diag([1.0, -1.0, -1.0])
    Pm = RX180 if frame == "yup" else P
    perm = [0, 1, 2] if frame == "yup" else [2, 0, 1]
    b = np.fromfile(src, dtype=np.uint8)
    n = b.size // 32
    a = b[: n * 32].reshape(n, 32)
    pos = a[:, 0:12].copy().view(np.float32).reshape(n, 3).astype(np.float64)
    scale = a[:, 12:24].copy().view(np.float32).reshape(n, 3).astype(np.float64)
    rgba = a[:, 24:28].astype(np.float64) / 255.0
    rot = (a[:, 28:32].astype(np.float64) - 128.0) / 128.0
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)

    pos_ue = pos @ Pm.T
    R_ue = np.einsum("ij,njk,lk->nil", Pm, quat_to_mat(rot), Pm)  # P R P^T
    rot_ue = mat_to_quat(R_ue)
    scale_ue = scale[:, perm]

    rgb = np.clip(rgba[:, :3], 0, 1)
    f_dc = (rgb - 0.5) / C0
    opacity = np.log(np.clip(rgba[:, 3], 1e-4, 1 - 1e-4)
                     / (1 - np.clip(rgba[:, 3], 1e-4, 1 - 1e-4)))
    log_scale = np.log(np.clip(scale_ue, 1e-8, None))

    header = (
        "ply\nformat binary_little_endian 1.0\n"
        f"element vertex {n}\n"
        "property float x\nproperty float y\nproperty float z\n"
        "property float nx\nproperty float ny\nproperty float nz\n"
        "property float f_dc_0\nproperty float f_dc_1\nproperty float f_dc_2\n"
        "property float opacity\n"
        "property float scale_0\nproperty float scale_1\nproperty float scale_2\n"
        "property float rot_0\nproperty float rot_1\nproperty float rot_2\nproperty float rot_3\n"
        "end_header\n"
    )
    out = np.zeros((n, 17), dtype=np.float32)
    out[:, 0:3] = pos_ue
    out[:, 3:6] = 0.0
    out[:, 6:9] = f_dc
    out[:, 9] = opacity
    out[:, 10:13] = log_scale
    out[:, 13:17] = rot_ue
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(out.astype("<f4").tobytes())
    print(f"WROTE {dst}: {n} splats ({dst.stat().st_size / 1e6:.1f} MB), UE frame (X fwd, Z up)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
