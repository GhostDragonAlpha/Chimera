"""
Particle → Gaussian Splat conversion.

Every particle in the simulation carries enough state to derive a splat:
  Position  → splat center
  Size      → splat scale (isotropic or anisotropic from velocity)
  Color/Alpha → splat color + opacity
  Velocity  → optional anisotropic stretch direction
  Accumulation (prop0) → opacity multiplier (settled = more visible)

Output is a SplatState: contiguous NumPy arrays ready for a splat renderer
(Unreal Niagara with custom splat shader, vispy, or a standalone GPU path).

FORMAT (matches the 3DGS convention):
  positions:  N×3  float32  (xyz)
  scales:     N×3  float32  (sx, sy, sz) — diagonal of scaling matrix
  rotations:  N×4  float32  (qx, qy, qz, qw) — unit quaternions
  colors:     N×3  float32  (r, g, b) 0-1
  opacities:  N×1  float32  0-1
  type_ids:   N×1  int32    particle type (for type-specific rendering)

The covariance matrix Σ = R * diag(S²) * Rᵀ  (scaling, then rotation).
"""

import numpy as np
from dataclasses import dataclass
from ParticleEngine.core import ParticleState, COL, C_POS, C_COLOR, C_VEL, PARTICLE_TYPES


@dataclass
class SplatState:
    """Immutable snapshot of splats ready for rendering."""
    positions: np.ndarray         # N×3 float32
    scales: np.ndarray            # N×3 float32
    rotations: np.ndarray         # N×4 float32 (quaternions xyzw)
    colors: np.ndarray            # N×3 float32 (0-1)
    opacities: np.ndarray         # N×1 float32 (0-1)
    type_ids: np.ndarray          # N int32

    # Optional: full covariance matrices for direct shader upload
    covariances_3x3: np.ndarray | None = None

    @property
    def count(self) -> int:
        return len(self.positions)

    def centroid(self) -> np.ndarray:
        """Mean position of all splats."""
        return self.positions.mean(axis=0)

    def extent(self) -> float:
        """Max distance from centroid (for camera framing)."""
        c = self.centroid()
        return float(np.max(np.linalg.norm(self.positions - c, axis=1)))

    def summary(self) -> dict:
        return {
            "count": self.count,
            "centroid": self.centroid().tolist(),
            "extent": self.extent(),
            "mean_opacity": float(self.opacities.mean()),
            "mean_scale": self.scales.mean(axis=0).tolist(),
        }


class SplatConverter:
    """
    Converts ParticleState → SplatState each frame.

    Design: configurable per-type splat profiles that map particle
    properties to splat parameters. A "profile" is a dict defining
    how to derive scale, opacity, and anisotropy for each particle type.

    Usage:
        conv = SplatConverter(base_scale=0.5)
        # Configure per-type profiles
        conv.set_profile("dust", scale_mult=0.3, opacity_from="accumulation")
        conv.set_profile("sand", scale_mult=0.6, anisotropic=True)

        for frame in range(300):
            sim.step(dt, cvars)
            splats: SplatState = conv.convert(sim.snapshot())
            # splats now ready for renderer
    """

    def __init__(self, base_scale: float = 0.5):
        self.base_scale = base_scale
        self._profiles: dict[int, dict] = {}  # type_code → profile

    def set_profile(
        self,
        type_name: str,
        scale_mult: float = 1.0,
        opacity_from: str = "alpha",   # "alpha" | "accumulation" | "prop2"
        anisotropic: bool = False,
        anisotropy_strength: float = 2.0,
        color_mix: float = 1.0,         # how much to use particle color (0 = type default)
    ):
        """Register a splat rendering profile for a particle type."""
        code = PARTICLE_TYPES.get(type_name)
        if code is None:
            raise KeyError(f"Unknown particle type: {type_name}")
        self._profiles[code] = {
            "scale_mult": scale_mult,
            "opacity_from": opacity_from,
            "anisotropic": anisotropic,
            "anisotropy_strength": anisotropy_strength,
            "color_mix": color_mix,
        }

    def _default_profile(self, type_code: int) -> dict:
        """Return profile for a type, falling back to sensible defaults."""
        if type_code in self._profiles:
            return self._profiles[type_code]

        # Sensible defaults per known type
        type_name = {v: k for k, v in PARTICLE_TYPES.items()}.get(type_code, "unknown")
        defaults = {
            "dust":        {"scale_mult": 0.2,  "opacity_from": "accumulation", "anisotropic": False},
            "sand":        {"scale_mult": 0.4,  "opacity_from": "alpha",         "anisotropic": True},
            "water":       {"scale_mult": 0.3,  "opacity_from": "alpha",         "anisotropic": True},
            "social":      {"scale_mult": 1.0,  "opacity_from": "alpha",         "anisotropic": False},
            "resource":    {"scale_mult": 1.5,  "opacity_from": "alpha",         "anisotropic": False},
            "atmosphere":  {"scale_mult": 5.0,  "opacity_from": "alpha",         "anisotropic": False},
            "shellmite":   {"scale_mult": 0.8,  "opacity_from": "alpha",         "anisotropic": True},
            "weapon_glint":{"scale_mult": 0.05, "opacity_from": "alpha",         "anisotropic": True},
        }
        d = defaults.get(type_name, {"scale_mult": 0.5, "opacity_from": "alpha", "anisotropic": False})
        return {
            **d,
            "anisotropy_strength": 2.0,
            "color_mix": 1.0,
        }

    def convert(self, state: ParticleState) -> SplatState:
        """
        Transform a particle snapshot into a splat snapshot.
        Only active particles are converted.
        """
        active = state.active_mask
        if not active.any():
            # Return empty splat state
            return SplatState(
                positions=np.empty((0, 3), dtype=np.float32),
                scales=np.empty((0, 3), dtype=np.float32),
                rotations=np.empty((0, 4), dtype=np.float32),
                colors=np.empty((0, 3), dtype=np.float32),
                opacities=np.empty((0, 1), dtype=np.float32),
                type_ids=np.empty(0, dtype=np.int32),
            )

        data = state.data[active]
        n = len(data)
        types = data[:, COL["type"]].astype(np.int32)

        # ── Positions: direct copy ──
        positions = data[:, C_POS].astype(np.float32).copy()

        # ── Colors: direct copy ──
        colors = data[:, COL["cr"]:COL["cr"]+3].astype(np.float32).copy()

        # ── Opacities: depends on profile ──
        opacities = np.zeros((n, 1), dtype=np.float32)
        sizes = data[:, COL["size"]].copy()

        # Build per-type masks and apply profiles
        unique_types = np.unique(types)
        for tcode in unique_types:
            mask = types == tcode
            profile = self._default_profile(int(tcode))

            # Opacity
            if profile["opacity_from"] == "accumulation":
                # prop0 = accumulation factor → map to opacity
                acc = data[mask, COL["prop0"]]
                opacities[mask, 0] = np.clip(acc * 10.0, 0.01, 1.0)
            elif profile["opacity_from"] == "prop2":
                opacities[mask, 0] = np.clip(data[mask, COL["prop2"]], 0.0, 1.0)
            else:  # "alpha"
                opacities[mask, 0] = np.clip(data[mask, COL["alpha"]], 0.0, 1.0)

            # Color mix
            if profile["color_mix"] < 1.0:
                # Blend toward type-default color
                type_defaults = {
                    PARTICLE_TYPES["dust"]:        (0.7, 0.65, 0.55),
                    PARTICLE_TYPES["sand"]:        (0.85, 0.68, 0.38),
                    PARTICLE_TYPES["water"]:       (0.2, 0.5, 0.9),
                    PARTICLE_TYPES["atmosphere"]:  (0.6, 0.7, 0.9),
                }
                default = type_defaults.get(int(tcode), (0.5, 0.5, 0.5))
                mix = profile["color_mix"]
                colors[mask] = colors[mask] * mix + np.array(default) * (1 - mix)

        # ── Scales: from particle size × profile multiplier ──
        scales = np.zeros((n, 3), dtype=np.float32)
        for tcode in unique_types:
            mask = types == tcode
            profile = self._default_profile(int(tcode))
            mult = profile["scale_mult"] * self.base_scale
            base_scale = sizes[mask, np.newaxis] * mult

            if profile["anisotropic"]:
                # Stretch along velocity direction
                vels = data[mask, C_VEL]
                vel_mag = np.linalg.norm(vels, axis=1, keepdims=True) + 1e-8
                vel_dir = vels / vel_mag
                stretch = profile.get("anisotropy_strength", 2.0)

                # Scale: compressed perpendicular, stretched along velocity
                perp_scale = base_scale / np.sqrt(stretch)
                par_scale = base_scale * np.sqrt(stretch)

                # Start with isotropic and replace along velocity direction
                iso = np.repeat(base_scale, 3, axis=1)
                # The velocity-aligned axis gets par_scale, others get perp_scale
                for i in range(3):
                    iso[:, i] = (
                        par_scale[:, 0] * vel_dir[:, i] ** 2
                        + perp_scale[:, 0] * (1 - vel_dir[:, i] ** 2)
                    )
                scales[mask] = iso
            else:
                scales[mask] = np.repeat(base_scale, 3, axis=1)

        # ── Rotations: align Z to velocity direction (or identity) ──
        rotations = np.zeros((n, 4), dtype=np.float32)
        rotations[:, 3] = 1.0  # w=1, xyz=0 → identity quaternion

        for tcode in unique_types:
            mask = types == tcode
            profile = self._default_profile(int(tcode))
            if profile["anisotropic"]:
                vels = data[mask, C_VEL]
                mag = np.linalg.norm(vels, axis=1)
                moving = mag > 1e-6
                if moving.any():
                    moving_idx = np.where(mask)[0][moving]
                    dirs = vels[moving] / mag[moving, np.newaxis]
                    # Quaternion from Z-axis (0,0,1) to velocity direction
                    rotations[moving_idx] = _rotation_from_to(
                        np.array([0.0, 0.0, 1.0]), dirs
                    )

        # ── Covariance matrices (optional, for direct shader upload) ──
        cov3x3 = _build_covariances(scales, rotations)

        return SplatState(
            positions=positions,
            scales=scales,
            rotations=rotations,
            colors=colors,
            opacities=opacities,
            type_ids=types,
            covariances_3x3=cov3x3,
        )


# ═══════════════════════════════════════════════════════════════════
#  Geometry helpers
# ═══════════════════════════════════════════════════════════════════

def _rotation_from_to(src: np.ndarray, tgt: np.ndarray) -> np.ndarray:
    """
    Quaternion rotating `src` unit vector to `tgt` unit vector.
    src: (3,) reference direction
    tgt: (N, 3) target directions
    Returns: (N, 4) quaternions [x, y, z, w]
    """
    src = src / np.linalg.norm(src)
    # Cross product axis
    axis = np.cross(src, tgt)  # N×3
    # Dot product → cos(angle)
    d = np.clip(np.dot(tgt, src), -1.0, 1.0)  # N

    # For antiparallel case (d ≈ -1), pick arbitrary perpendicular axis
    antiparallel = d < -0.9999
    if antiparallel.any():
        # Find an axis perpendicular to src
        perp = np.array([1.0, 0.0, 0.0]) if abs(src[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        axis[antiparallel] = np.cross(src, perp)

    # Half-angle formula
    half_cos = np.sqrt((1.0 + d) / 2.0)       # cos(θ/2)
    half_sin = np.sqrt((1.0 - d) / 2.0)       # sin(θ/2)

    # Normalize axis
    axis_norm = np.linalg.norm(axis, axis=1, keepdims=True) + 1e-12
    axis = axis / axis_norm

    # Quaternion: w = cos(θ/2), xyz = axis * sin(θ/2)
    q = np.zeros((len(tgt), 4), dtype=np.float32)
    q[:, 0] = axis[:, 0] * half_sin
    q[:, 1] = axis[:, 1] * half_sin
    q[:, 2] = axis[:, 2] * half_sin
    q[:, 3] = half_cos

    # Handle small rotations (src ≈ tgt): identity quaternion
    small = d > 0.9999
    q[small] = [0, 0, 0, 1]

    return q


def _build_covariances(scales: np.ndarray, rotations: np.ndarray) -> np.ndarray:
    """
    Build 3×3 covariance matrices from scales and quaternions — fully vectorized.
    Σ = R * diag(S²) * Rᵀ

    scales: (N, 3) diagonal of scaling matrix
    rotations: (N, 4) quaternions (xyzw)
    Returns: (N, 3, 3) float32 covariance matrices
    """
    n = len(scales)
    s2 = scales ** 2  # (N, 3)

    # Quaternion → rotation matrix (vectorized, no per-particle loop)
    qx = rotations[:, 0]
    qy = rotations[:, 1]
    qz = rotations[:, 2]
    qw = rotations[:, 3]

    # Normalize
    inv_norm = 1.0 / np.sqrt(qx*qx + qy*qy + qz*qz + qw*qw)
    qx, qy, qz, qw = qx*inv_norm, qy*inv_norm, qz*inv_norm, qw*inv_norm

    # Pre-compute common terms
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz

    # Build rotation matrices R: (N, 3, 3)
    R = np.empty((n, 3, 3), dtype=np.float32)
    R[:, 0, 0] = 1.0 - 2.0 * (yy + zz)
    R[:, 0, 1] = 2.0 * (xy - wz)
    R[:, 0, 2] = 2.0 * (xz + wy)
    R[:, 1, 0] = 2.0 * (xy + wz)
    R[:, 1, 1] = 1.0 - 2.0 * (xx + zz)
    R[:, 1, 2] = 2.0 * (yz - wx)
    R[:, 2, 0] = 2.0 * (xz - wy)
    R[:, 2, 1] = 2.0 * (yz + wx)
    R[:, 2, 2] = 1.0 - 2.0 * (xx + yy)

    # Σ[i,j,k] = sum_l R[i,j,l] * s2[i,l] * R[i,k,l]
    # Using einsum: 'ijl,il,ikl->ijk'
    cov = np.einsum('ijl,il,ikl->ijk', R, s2, R, dtype=np.float32)
    return cov
