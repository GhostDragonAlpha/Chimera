"""
3DGS splat I/O — reads standard .ply files from nerfstudio/polycam.

Standard 3DGS .ply format:
  x y z                          — position (3 floats)
  f_dc_0 f_dc_1 f_dc_2          — base color (3 floats)
  f_rest_*                       — spherical harmonics (up to 45 floats, optional)
  opacity                         — 1 float
  scale_0 scale_1 scale_2        — 3 floats (log scale)
  rot_0 rot_1 rot_2 rot_3        — quaternion (4 floats)
"""

import struct, numpy as np
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SplatCloud:
    """In-memory representation of a 3DGS splat cloud."""
    positions: np.ndarray        # (N, 3)
    colors: np.ndarray           # (N, 3) — base color (no SH for now)
    opacities: np.ndarray        # (N,)
    scales: np.ndarray           # (N, 3)
    rotations: np.ndarray        # (N, 4) — quaternions xyzw
    covariances_3x3: np.ndarray | None = None  # (N, 3, 3)

    @property
    def count(self) -> int:
        return len(self.positions)

    def to_dict(self) -> dict:
        return {
            "count": int(self.count),
            "positions_mean": self.positions.mean(axis=0).tolist(),
            "positions_std": self.positions.std(axis=0).tolist(),
            "extent": float(np.linalg.norm(
                self.positions.max(axis=0) - self.positions.min(axis=0))),
            "mean_opacity": float(self.opacities.mean()),
            "mean_scale": self.scales.mean(axis=0).tolist(),
        }


def load_ply(path: str) -> SplatCloud:
    """Load a standard 3DGS .ply file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {path}")

    with open(path, "rb") as f:
        # Read header
        header_lines = []
        line = f.readline().decode("utf-8", errors="replace")
        vertex_count = 0
        props = []

        while line.strip() != "end_header":
            header_lines.append(line)
            if line.startswith("element vertex"):
                vertex_count = int(line.split()[-1])
            elif line.startswith("property"):
                parts = line.split()
                props.append((parts[1], parts[2]))  # (type, name)
            line = f.readline().decode("utf-8", errors="replace")

        # Determine float size from format
        is_binary_little = any("binary_little_endian" in h for h in header_lines)
        float_size = 4  # float32

        # Build property map
        prop_indices = {}
        for i, (ptype, pname) in enumerate(props):
            prop_indices[pname] = i

        # Read vertex data
        if is_binary_little:
            row_size = len(props) * float_size
            data = np.frombuffer(f.read(), dtype=np.float32).reshape(-1, len(props))
        else:
            # ASCII fallback — slower
            rows = []
            for line in f.read().decode("utf-8", errors="replace").strip().split("\n"):
                if line.strip():
                    rows.append([float(v) for v in line.split()])
            data = np.array(rows, dtype=np.float32)

    n = min(vertex_count, len(data))

    # Extract known properties
    def get_col(name, default=0.0):
        if name in prop_indices:
            return data[:n, prop_indices[name]]
        return np.full(n, default, dtype=np.float32)

    x = get_col("x"); y = get_col("y"); z = get_col("z")
    positions = np.stack([x, y, z], axis=1)

    cr = get_col("f_dc_0"); cg = get_col("f_dc_1"); cb = get_col("f_dc_2")
    colors = np.stack([cr, cg, cb], axis=1)
    # INRIA 3DGS stores colour as the spherical-harmonic DC coefficient:
    #     rgb = 0.5 + C0 * f_dc      (C0 = 0.28209479177387814)   -- NOT sigmoid.
    # Verified by loading the SAME model (bonsai@7k) as .ply and .splat and matching the
    # colour distributions: sigmoid squashed the range (p10 0.143 vs the true 0.000).
    # See Construction/calibrate_formats.py.
    SH_C0 = 0.28209479177387814
    colors = np.clip(0.5 + SH_C0 * colors, 0.0, 1.0)

    opacities = sigmoid(get_col("opacity"))

    # Scales: convert from log-scale (standard 3DGS convention)
    sx = get_col("scale_0", -3.0); sy = get_col("scale_1", -3.0); sz = get_col("scale_2", -3.0)
    scales = np.exp(np.stack([sx, sy, sz], axis=1))

    rx = get_col("rot_0"); ry = get_col("rot_1"); rz = get_col("rot_2"); rw = get_col("rot_3")
    # Normalize quaternions
    rot = np.stack([rx, ry, rz, rw], axis=1)
    rot /= np.linalg.norm(rot, axis=1, keepdims=True) + 1e-12

    # Build covariance matrices
    cov = _build_covariances(scales, rot)

    return SplatCloud(
        positions=positions.astype(np.float32),
        colors=colors.astype(np.float32),
        opacities=opacities.astype(np.float32),
        scales=scales.astype(np.float32),
        rotations=rot.astype(np.float32),
        covariances_3x3=cov.astype(np.float32),
    )


def save_ply(cloud: SplatCloud, path: str):
    """Save a SplatCloud to a standard 3DGS .ply file."""
    n = cloud.count
    header = f"""ply
format binary_little_endian 1.0
element vertex {n}
property float x
property float y
property float z
property float f_dc_0
property float f_dc_1
property float f_dc_2
property float opacity
property float scale_0
property float scale_1
property float scale_2
property float rot_0
property float rot_1
property float rot_2
property float rot_3
end_header
"""
    with open(path, "wb") as f:
        f.write(header.encode())
        # Convert back: SH-DC inverse for colours, sigmoid inverse for opacity, log for scales
        colors = (np.clip(cloud.colors, 0.0, 1.0) - 0.5) / 0.28209479177387814   # inverse of the SH-DC decode
        opacities = inverse_sigmoid(np.clip(cloud.opacities, 0.001, 0.999))
        scales = np.log(np.maximum(cloud.scales, 1e-8))

        for i in range(n):
            f.write(struct.pack(
                "3f3ff3f4f",
                *cloud.positions[i],
                *colors[i],
                opacities[i],
                *scales[i],
                *cloud.rotations[i],
            ))


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Standard sigmoid for color/opacity conversion."""
    return 1.0 / (1.0 + np.exp(-x))


def inverse_sigmoid(x: np.ndarray) -> np.ndarray:
    """Inverse sigmoid."""
    x = np.clip(x, 1e-8, 1 - 1e-8)
    return np.log(x / (1.0 - x))


def _build_covariances(scales: np.ndarray, rotations: np.ndarray) -> np.ndarray:
    """Build 3×3 covariance matrices from scales and quaternions."""
    n = len(scales)
    cov = np.zeros((n, 3, 3), dtype=np.float32)
    s2 = scales ** 2

    qx, qy, qz, qw = rotations[:, 0], rotations[:, 1], rotations[:, 2], rotations[:, 3]
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz

    R = np.empty((n, 3, 3), dtype=np.float32)
    R[:, 0, 0] = 1 - 2*(yy + zz); R[:, 0, 1] = 2*(xy - wz); R[:, 0, 2] = 2*(xz + wy)
    R[:, 1, 0] = 2*(xy + wz); R[:, 1, 1] = 1 - 2*(xx + zz); R[:, 1, 2] = 2*(yz - wx)
    R[:, 2, 0] = 2*(xz - wy); R[:, 2, 1] = 2*(yz + wx); R[:, 2, 2] = 1 - 2*(xx + yy)

    return np.einsum('ijl,il,ikl->ijk', R, s2, R, dtype=np.float32)


def normalize_cloud(cloud: SplatCloud, target_extent: float = 1.0) -> SplatCloud:
    """Normalize a splat cloud to unit extent, centered at origin."""
    centroid = cloud.positions.mean(axis=0)
    positions = cloud.positions - centroid
    ext = np.linalg.norm(positions.max(axis=0) - positions.min(axis=0))
    if ext < 1e-8:
        ext = 1.0
    scale = target_extent / ext
    positions *= scale
    # Scale the covariance eigenvalues: cov' = scale² * cov
    if cloud.covariances_3x3 is not None:
        cov = cloud.covariances_3x3 * (scale ** 2)
    else:
        cov = None
    return SplatCloud(
        positions=positions.astype(np.float32),
        colors=cloud.colors,
        opacities=cloud.opacities,
        scales=cloud.scales * scale,
        rotations=cloud.rotations,
        covariances_3x3=cov,
    )
