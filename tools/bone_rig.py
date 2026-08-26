"""bone_rig.py — BONE-RIG controller: bones tell triangles what to do.

RULE 0 MEMBRANE (theDeterminism S3 architecture):
  STATEMENT  determinism = ROM extremities + CA-filled interior harnessed by a bone rig
  PREDICTION the triangle mesh's deformation is fully determined by the rig pose
             (skinning is a pure function of rig + weights); no triangle moves
             independently of the rig
  FALSIFIER  a triangle vertex moves without a corresponding rig change, or the
             interior violates the rig's ROM

The rig (MuJoCo bodies) is the single authority — triangles never self-author.
Linear blend skinning:
    v = SUM_b  w_b * (R_b * x_local + t_b)

where R_b, t_b come from the bone's delta transform (current @ inv(rest)),
x_local is the vertex rest-pose position, and w_b are skinning weights
that sum to 1 per vertex.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


def _mat4(xpos, xmat) -> np.ndarray:
    """Build a 4x4 world matrix from MuJoCo xpos (3,) and xmat (9,) flat."""
    T = np.eye(4, dtype=float)
    T[:3, :3] = np.asarray(xmat, dtype=float).reshape(3, 3)
    T[:3, 3] = np.asarray(xpos, dtype=float)
    return T


def _inv4(T: np.ndarray) -> np.ndarray:
    """Inverse of a 4x4 rigid-body transform (analytic, not np.linalg.inv)."""
    R = T[:3, :3]
    t = T[:3, 3]
    Ri = R.T
    Ti = np.eye(4, dtype=float)
    Ti[:3, :3] = Ri
    Ti[:3, 3] = -Ri @ t
    return Ti


# ---------------------------------------------------------------------------
# BoneRig
# ---------------------------------------------------------------------------
@dataclass
class BoneRig:
    """MuJoCo bodies as bones, triangle mesh skinned via LBS.

    The rig is the single authority.  A triangle vertex moves ONLY when the
    rig moves.  The CA interior is slaved to the rig's ROM.
    """
    m: object                                       # mujoco.MjModel
    d: object                                       # mujoco.MjData
    bone_names: List[str]

    # --- set by build_mesh / bind ---
    vertices_rest: Optional[np.ndarray] = None      # (N,3) rest-pose vertex positions
    faces: Optional[np.ndarray] = None              # (F,3) triangle indices
    weights: Optional[np.ndarray] = None            # (N,K) skinning weights, sum=1

    _rest_T: Optional[np.ndarray] = None            # (K,4,4) rest-pose world matrices
    _rest_inv: Optional[np.ndarray] = None          # (K,4,4) inverse rest-pose matrices

    # --- CA interior (minimal stub) ---
    _interior_rest: Optional[np.ndarray] = None     # (M,3) rest-pose interior points
    _interior_weights: Optional[np.ndarray] = None  # (M,K) interior skinning weights

    # -- helpers --

    @property
    def bone_ids(self) -> List[int]:
        import mujoco
        return [mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, n)
                for n in self.bone_names]

    # -- lifecycle --

    def bind(self) -> None:
        """Capture rest-pose bone transforms.  Call after mj_forward at qpos0."""
        import mujoco
        mujoco.mj_forward(self.m, self.d)
        ids = self.bone_ids
        K = len(ids)
        self._rest_T = np.empty((K, 4, 4))
        for k, bid in enumerate(ids):
            self._rest_T[k] = _mat4(self.d.xpos[bid], self.d.xmat[bid])
        self._rest_inv = np.array([_inv4(T) for T in self._rest_T])

    def bone_transforms(self) -> np.ndarray:
        """Read current bone world transforms from MuJoCo.  Returns (K,4,4)."""
        ids = self.bone_ids
        K = len(ids)
        T = np.empty((K, 4, 4))
        for k, bid in enumerate(ids):
            T[k] = _mat4(self.d.xpos[bid], self.d.xmat[bid])
        return T

    # -- mesh --

    def load_external_mesh(self, vertices: np.ndarray, faces: np.ndarray,
                           radius: float = 0.15) -> None:
        """Load an external triangle mesh (e.g., the real teddy) and compute
        skinning weights from vertex-to-bone distances."""
        import mujoco
        mujoco.mj_forward(self.m, self.d)
        self.vertices_rest = np.asarray(vertices, dtype=float).copy()
        self.faces = np.asarray(faces, dtype=int).copy()
        ids = self.bone_ids
        K = len(ids)
        bone_pos = np.array([self.d.xpos[bid] for bid in ids])
        N = len(self.vertices_rest)
        self.weights = np.zeros((N, K))
        for i in range(N):
            for k in range(K):
                self.weights[i, k] = 1.0 / (np.linalg.norm(self.vertices_rest[i] - bone_pos[k]) + 1e-6)
            self.weights[i] /= self.weights[i].sum()
        self._build_interior(bone_pos, radius)

    def build_mesh(self, n_rings: int = 3, n_segs: int = 8,
                   radius: float = 0.15) -> None:
        """Build a tube mesh around the bone chain and assign skinning weights."""
        import mujoco
        mujoco.mj_forward(self.m, self.d)

        ids = self.bone_ids
        K = len(ids)
        bone_pos = np.array([self.d.xpos[bid] for bid in ids])   # (K,3)

        # --- vertices: one ring per bone ---
        verts: list[np.ndarray] = []
        for k in range(K):
            center = bone_pos[k]
            if k < K - 1:
                direction = bone_pos[k + 1] - bone_pos[k]
            else:
                direction = bone_pos[k] - bone_pos[k - 1]
            d_hat = direction / (np.linalg.norm(direction) + 1e-12)
            up = np.array([0.0, 0.0, 1.0]) if abs(d_hat[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
            u = np.cross(d_hat, up);  u /= np.linalg.norm(u) + 1e-12
            v = np.cross(d_hat, u);  v /= np.linalg.norm(v) + 1e-12
            for seg in range(n_segs):
                a = 2.0 * math.pi * seg / n_segs
                verts.append(center + radius * (math.cos(a) * u + math.sin(a) * v))

        self.vertices_rest = np.array(verts)                          # (K*n_segs, 3)

        # --- faces: connect adjacent rings ---
        faces: list[tuple] = []
        for k in range(K - 1):
            ba = k * n_segs
            bb = (k + 1) * n_segs
            for seg in range(n_segs):
                s0, s1 = seg, (seg + 1) % n_segs
                faces.append((ba + s0, bb + s0, bb + s1))
                faces.append((ba + s0, bb + s1, ba + s1))
        self.faces = np.array(faces, dtype=int)

        # --- skinning weights: inverse-distance, normalised per vertex ---
        N = len(verts)
        self.weights = np.zeros((N, K))
        for i in range(N):
            for k in range(K):
                self.weights[i, k] = 1.0 / (np.linalg.norm(verts[i] - bone_pos[k]) + 1e-6)
            self.weights[i] /= self.weights[i].sum()

        # --- CA interior ---
        self._build_interior(bone_pos, radius)

    # -- CA interior (minimal stub) --

    def _build_interior(self, bone_pos: np.ndarray, radius: float) -> None:
        """Fill a voxel grid inside the mesh; every interior point is slaved to the rig."""
        lo = bone_pos.min(axis=0) - radius
        hi = bone_pos.max(axis=0) + radius
        K = len(bone_pos)
        interior: list[np.ndarray] = []
        int_weights: list[np.ndarray] = []
        res = 6

        def _seg_dist(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
            """Distance from point p to line segment a-b."""
            ab = b - a
            t = float(np.clip(np.dot(p - a, ab) / (np.dot(ab, ab) + 1e-12), 0.0, 1.0))
            return float(np.linalg.norm(p - (a + t * ab)))

        for x in np.linspace(lo[0], hi[0], res):
            for y in np.linspace(lo[1], hi[1], res):
                for z in np.linspace(lo[2], hi[2], res):
                    p = np.array([x, y, z])
                    # distance to nearest bone SEGMENT, not just bone position
                    min_d = float("inf")
                    for k in range(K - 1):
                        min_d = min(min_d, _seg_dist(p, bone_pos[k], bone_pos[k + 1]))
                    min_d = min(min_d, min(np.linalg.norm(p - bone_pos[k]) for k in range(K)))
                    if min_d < radius * 0.7:
                        interior.append(p)
                        w = np.array([1.0 / (np.linalg.norm(p - bone_pos[k]) + 1e-6)
                                      for k in range(K)])
                        w /= w.sum()
                        int_weights.append(w)
        self._interior_rest = np.array(interior) if interior else np.zeros((0, 3))
        self._interior_weights = np.array(int_weights) if int_weights else np.zeros((0, K))

    # -- skinning (the core) --

    def skin(self) -> np.ndarray:
        """LBS: v = SUM_b w_b * (R_b * x_local + t_b).  Returns (N,3).

        This is a PURE FUNCTION of the rig pose and the weights.  No
        triangle moves independently of the rig.
        """
        if self.vertices_rest is None or self._rest_inv is None:
            raise ValueError("call build_mesh() then bind() before skin()")
        T_curr = self.bone_transforms()
        K = len(self.bone_names)
        N = len(self.vertices_rest)
        skinned = np.empty((N, 3))
        for i in range(N):
            v = np.zeros(3)
            for b in range(K):
                delta = T_curr[b] @ self._rest_inv[b]
                R_b = delta[:3, :3]
                t_b = delta[:3, 3]
                v += self.weights[i, b] * (R_b @ self.vertices_rest[i] + t_b)
            skinned[i] = v
        return skinned

    def skin_interior(self) -> np.ndarray:
        """LBS-skin the CA interior points.  Returns (M,3)."""
        if self._interior_rest is None or len(self._interior_rest) == 0:
            return np.zeros((0, 3))
        T_curr = self.bone_transforms()
        K = len(self.bone_names)
        M = len(self._interior_rest)
        skinned = np.empty((M, 3))
        for i in range(M):
            v = np.zeros(3)
            for b in range(K):
                delta = T_curr[b] @ self._rest_inv[b]
                R_b = delta[:3, :3]
                t_b = delta[:3, 3]
                v += self._interior_weights[i, b] * (R_b @ self._interior_rest[i] + t_b)
            skinned[i] = v
        return skinned

    # -- ROM (range of motion) --

    def rom_extremities(self) -> Dict[str, Tuple[float, float]]:
        """Read joint ROM from the MuJoCo model.  {joint_name: (lo_rad, hi_rad)}."""
        import mujoco
        rom: Dict[str, Tuple[float, float]] = {}
        for j in range(self.m.njnt):
            if self.m.jnt_limited[j]:
                name = mujoco.mj_id2name(self.m, mujoco.mjtObj.mjOBJ_JOINT, j)
                if name:
                    rom[name] = (float(self.m.jnt_range[j][0]),
                                 float(self.m.jnt_range[j][1]))
        return rom

    def rom_envelope(self) -> Tuple[np.ndarray, np.ndarray]:
        """Bounding box of every bone position reachable within the ROM.

        Sweeps each limited joint to its extremes and reads d.xpos.
        Returns (min_corner[3], max_corner[3]).
        """
        import mujoco
        ids = self.bone_ids
        all_pos: list[np.ndarray] = []
        qpos0 = np.array(self.d.qpos)

        for j in range(self.m.njnt):
            if self.m.jnt_limited[j]:
                lo, hi = float(self.m.jnt_range[j][0]), float(self.m.jnt_range[j][1])
                for val in (lo, hi):
                    self.d.qpos[:] = qpos0
                    self.d.qpos[int(self.m.jnt_qposadr[j])] = val
                    mujoco.mj_forward(self.m, self.d)
                    for bid in ids:
                        all_pos.append(self.d.xpos[bid].copy())

        # include rest pose
        self.d.qpos[:] = qpos0
        mujoco.mj_forward(self.m, self.d)
        for bid in ids:
            all_pos.append(self.d.xpos[bid].copy())

        # restore
        self.d.qpos[:] = qpos0
        mujoco.mj_forward(self.m, self.d)

        pts = np.array(all_pos)
        return pts.min(axis=0), pts.max(axis=0)

    def interior_within_rom(self, mesh_radius: float = 0.15) -> bool:
        """Check that all skinned interior points stay within the ROM envelope.

        The envelope is expanded by `mesh_radius` to account for the fact that
        interior points live inside the mesh surface, offset from the bones.
        At rest the offset is at most 0.7*radius; under LBS the bone rotation
        sweeps that offset through the full envelope + radius band.
        """
        interior = self.skin_interior()
        if len(interior) == 0:
            return True
        lo, hi = self.rom_envelope()
        return bool(np.all(interior >= lo - mesh_radius)
                    and np.all(interior <= hi + mesh_radius))
