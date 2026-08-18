"""sdf_grid.py — Sparse SDF hash grid. The single substrate for physics + rendering.

A membrane's shape IS a signed distance field. Not a mesh, not a convex hull.
The grid is sparse (hash map): only voxels near the surface exist.
Same grid answers: collision queries, surface extraction, deformation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np


@dataclass(frozen=True)
class VoxelKey:
    """Integer voxel coordinate. Hashable, usable as dict key."""
    x: int
    y: int
    z: int

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def offset(self, dx: int, dy: int, dz: int) -> "VoxelKey":
        return VoxelKey(self.x + dx, self.y + dy, self.z + dz)

    def neighbors(self) -> List["VoxelKey"]:
        """26-connected neighbors."""
        return [
            VoxelKey(self.x + dx, self.y + dy, self.z + dz)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            for dz in (-1, 0, 1)
            if not (dx == 0 and dy == 0 and dz == 0)
        ]


@dataclass
class SDFGrid:
    """Sparse hash grid storing (SDF value, material_id) per voxel.

    Only surface voxels (|sdf| < band) are stored. Interior = -inf, exterior = +inf.
    """
    voxel_size: float                    # world units per voxel
    band: float = 3.0                    # narrow band in voxel units
    _data: Dict[VoxelKey, Tuple[float, int]] = field(default_factory=dict)
    _material_names: List[str] = field(default_factory=list)

    # --- coordinate transforms ---
    def world_to_voxel(self, pos: np.ndarray) -> VoxelKey:
        v = np.floor(pos / self.voxel_size).astype(int)
        return VoxelKey(int(v[0]), int(v[1]), int(v[2]))

    def voxel_to_world(self, key: VoxelKey) -> np.ndarray:
        return np.array([key.x, key.y, key.z], dtype=float) * self.voxel_size

    def voxel_center_world(self, key: VoxelKey) -> np.ndarray:
        return (np.array([key.x, key.y, key.z], dtype=float) + 0.5) * self.voxel_size

    # --- material registry ---
    def register_material(self, name: str) -> int:
        if name not in self._material_names:
            self._material_names.append(name)
        return self._material_names.index(name)

    def material_id(self, name: str) -> int:
        return self._material_names.index(name)

    def material_name(self, mid: int) -> str:
        return self._material_names[mid]

    # --- core queries ---
    def get(self, key: VoxelKey) -> Tuple[float, int]:
        """Return (sdf, material_id). Missing = (+inf, 0 = void)."""
        return self._data.get(key, (float("inf"), 0))

    def sdf_at_key(self, key: VoxelKey) -> float:
        return self._data.get(key, (float("inf"), 0))[0]

    def set(self, key: VoxelKey, sdf: float, material_id: int = 0) -> None:
        if abs(sdf) <= self.band:
            self._data[key] = (float(sdf), int(material_id))
        elif key in self._data:
            del self._data[key]

    # --- trilinear sampling (physics + rendering both use this) ---
    def sample_trilinear(self, world_pos: np.ndarray) -> Tuple[float, int]:
        """Trilinear SDF + nearest material at world position."""
        v = world_pos / self.voxel_size
        x0, y0, z0 = np.floor(v).astype(int)
        x1, y1, z1 = x0 + 1, y0 + 1, z0 + 1
        fx, fy, fz = v - [x0, y0, z0]

        # fetch 8 corners
        vals = {}
        for dx, dy, dz in [(0,0,0),(1,0,0),(0,1,0),(1,1,0),
                           (0,0,1),(1,0,1),(0,1,1),(1,1,1)]:
            key = VoxelKey(x0+dx, y0+dy, z0+dz)
            vals[(dx,dy,dz)] = self.get(key)

        # trilinear on SDF
        def lerp(a, b, t): return a + (b - a) * t
        c00 = lerp(vals[(0,0,0)][0], vals[(1,0,0)][0], fx)
        c01 = lerp(vals[(0,1,0)][0], vals[(1,1,0)][0], fx)
        c10 = lerp(vals[(0,0,1)][0], vals[(1,0,1)][0], fx)
        c11 = lerp(vals[(0,1,1)][0], vals[(1,1,1)][0], fx)
        c0 = lerp(c00, c01, fy)
        c1 = lerp(c10, c11, fy)
        sdf = lerp(c0, c1, fz)

        # material = nearest corner with valid material
        mat = 0
        for dx, dy, dz in [(0,0,0),(1,0,0),(0,1,0),(1,1,0),
                           (0,0,1),(1,0,1),(0,1,1),(1,1,1)]:
            if vals[(dx,dy,dz)][1] != 0:
                mat = vals[(dx,dy,dz)][1]
                break

        return float(sdf), mat

    # --- gradient (central difference) = contact normal ---
    def gradient(self, world_pos: np.ndarray, eps: float = None) -> np.ndarray:
        """∇SDF at world_pos. Central difference, 6 samples."""
        if eps is None:
            eps = self.voxel_size * 0.5
        x, y, z = world_pos
        sdf_x_p, _ = self.sample_trilinear(np.array([x + eps, y, z]))
        sdf_x_m, _ = self.sample_trilinear(np.array([x - eps, y, z]))
        sdf_y_p, _ = self.sample_trilinear(np.array([x, y + eps, z]))
        sdf_y_m, _ = self.sample_trilinear(np.array([x, y - eps, z]))
        sdf_z_p, _ = self.sample_trilinear(np.array([x, y, z + eps]))
        sdf_z_m, _ = self.sample_trilinear(np.array([x, y, z - eps]))
        grad = np.array([
            (sdf_x_p - sdf_x_m) / (2 * eps),
            (sdf_y_p - sdf_y_m) / (2 * eps),
            (sdf_z_p - sdf_z_m) / (2 * eps),
        ])
        norm = np.linalg.norm(grad)
        return grad / (norm + 1e-8) if norm > 1e-8 else np.array([0.0, 0.0, 1.0])

    # --- surface extraction (for rendering: surface voxels → splats) ---
    def surface_voxels(self) -> List[Tuple[VoxelKey, float, int]]:
        """All voxels with |sdf| < band, sorted by |sdf| (closest to surface first)."""
        surf = [(k, v[0], v[1]) for k, v in self._data.items() if abs(v[0]) < self.band]
        surf.sort(key=lambda x: abs(x[1]))
        return surf

    # --- bounding box of occupied voxels ---
    def bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        if not self._data:
            return np.zeros(3), np.zeros(3)
        keys = list(self._data.keys())
        min_k = VoxelKey(min(k.x for k in keys), min(k.y for k in keys), min(k.z for k in keys))
        max_k = VoxelKey(max(k.x for k in keys), max(k.y for k in keys), max(k.z for k in keys))
        return self.voxel_to_world(min_k), self.voxel_to_world(max_k)

    # --- serialization (cached: the grid is static per shape) ---
    def _cached_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if getattr(self, "_arrays_cache", None) is None:
            if not self._data:
                self._arrays_cache = (np.zeros((0,3), np.int32),
                                      np.zeros(0, np.float32), np.zeros(0, np.int32))
            else:
                keys = np.array([[k.x, k.y, k.z] for k in self._data.keys()], dtype=np.int32)
                sdfs = np.array([v[0] for v in self._data.values()], dtype=np.float32)
                mats = np.array([v[1] for v in self._data.values()], dtype=np.int32)
                self._arrays_cache = (keys, sdfs, mats)
        return self._arrays_cache

    def to_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return cached (keys[N,3], sdfs[N], mats[N]) for GPU upload / point extraction."""
        return self._cached_arrays()

    @classmethod
    def from_arrays(cls, keys: np.ndarray, sdfs: np.ndarray, mats: np.ndarray,
                    voxel_size: float, band: float = 3.0) -> "SDFGrid":
        grid = cls(voxel_size=voxel_size, band=band)
        for (x, y, z), sdf, mat in zip(keys, sdfs, mats):
            grid._data[VoxelKey(int(x), int(y), int(z))] = (float(sdf), int(mat))
        return grid

    # --- dense volume packer (GPU upload unit) ---
    def to_dense_volume(self, pad_voxels: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Resample the sparse grid into a dense float32 volume over its AABB. Vectorized.

        Returns (volume[dx,dy,dz], origin_world[3], dims[3]). Voxels outside the stored
        band are filled with +far (exterior) so the GPU can trilinearly interpolate a
        defined field everywhere inside the AABB.
        """
        if not self._data:
            return np.zeros((1, 1, 1), np.float32), np.zeros(3, np.float32), np.array([1, 1, 1], np.int32)
        keys, sdfs, _mats = self.to_arrays()
        lo = keys.min(axis=0) - pad_voxels
        hi = keys.max(axis=0) + pad_voxels
        dims = (hi - lo + 1).astype(np.int32)
        vol = np.full(tuple(dims.tolist()), float(self.band * 4), dtype=np.float32)  # far = exterior
        ix = keys[:, 0] - lo[0]
        iy = keys[:, 1] - lo[1]
        iz = keys[:, 2] - lo[2]
        vol[ix, iy, iz] = sdfs
        origin = self.voxel_to_world(VoxelKey(int(lo[0]), int(lo[1]), int(lo[2])))
        return vol, origin.astype(np.float32), dims

    def world_positions(self, stride: int = 1) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Vectorized (N,3) world positions + sdf + mat of (subsampled) stored voxels.

        Used for both contact candidate points and renderer splats without a Python loop.
        """
        keys, sdfs, mats = self.to_arrays()
        if stride > 1 and keys.shape[0] > stride:
            idx = np.arange(0, keys.shape[0], stride)
            keys = keys[idx]; sdfs = sdfs[idx]; mats = mats[idx]
        # voxel center world = (key + 0.5) * voxel_size
        pos = (keys.astype(np.float64) + 0.5) * self.voxel_size
        return pos.astype(np.float32), sdfs.astype(np.float32), mats.astype(np.int32)

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)


# --- SDF primitives (capsule, sphere, box) for building grids ---
def capsule_sdf(p: np.ndarray, a: np.ndarray, b: np.ndarray, r: float) -> float:
    """SDF of capsule segment a->b with radius r."""
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0.0, 1.0)
    closest = a + t * ab
    return np.linalg.norm(p - closest) - r


def sphere_sdf(p: np.ndarray, c: np.ndarray, r: float) -> float:
    return np.linalg.norm(p - c) - r


def box_sdf(p: np.ndarray, center: np.ndarray, half_extents: np.ndarray) -> float:
    q = np.abs(p - center) - half_extents
    return np.linalg.norm(np.maximum(q, 0)) + min(max(q[0], max(q[1], q[2])), 0.0)


def smooth_min(a: float, b: float, k: float) -> float:
    """Polynomial smooth minimum (Quilez). k = blend distance."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return a * (1 - h) + b * h - k * h * (1 - h)


# --- Build SDFGrid from skeleton (terrarium bones) ---
def build_sdf_from_bones(bones: List, voxel_size: float, band: float = 3.0,
                         blend: float = 0.55) -> SDFGrid:
    """Convert terrarium Bone list → sparse SDF grid with smooth-min blending.

    Each bone = tapered capsule. Blended with polynomial smooth-min.
    Returns grid with material IDs stored as string keys ("void"/"bone"/"muscle"/"skin").
    """
    grid = SDFGrid(voxel_size=voxel_size, band=band)
    grid.register_material("void")
    bone_id = grid.register_material("bone")
    muscle_id = grid.register_material("muscle")
    skin_id = grid.register_material("skin")

    if not bones:
        return grid

    # Compute world bounds of skeleton
    all_pts = [p for b in bones for p in (b.p0, b.p1)]
    min_pt = np.min(all_pts, axis=0) - max(b.r0 for b in bones) - band * voxel_size
    max_pt = np.max(all_pts, axis=0) + max(b.r1 for b in bones) + band * voxel_size

    # Iterate voxel grid bounds
    min_v = np.floor(min_pt / voxel_size).astype(int)
    max_v = np.ceil(max_pt / voxel_size).astype(int)

    for b in bones:
        a = np.array(b.p0, float)
        c = np.array(b.p1, float)
        r0, r1 = b.r0, b.r1

        # Bounding box of this bone's influence
        bone_min = np.minimum(a, c) - max(r0, r1) - blend
        bone_max = np.maximum(a, c) + max(r0, r1) + blend
        vmin = np.maximum(np.floor(bone_min / voxel_size).astype(int), min_v)
        vmax = np.minimum(np.ceil(bone_max / voxel_size).astype(int), max_v)

        for xi in range(vmin[0], vmax[0] + 1):
            for yi in range(vmin[1], vmax[1] + 1):
                for zi in range(vmin[2], vmax[2] + 1):
                    key = VoxelKey(xi, yi, zi)
                    wc = grid.voxel_center_world(key)
                    # Tapered capsule SDF
                    ab = c - a
                    t = np.clip(np.dot(wc - a, ab) / np.dot(ab, ab), 0.0, 1.0)
                    closest = a + t * ab
                    r = r0 + (r1 - r0) * t
                    d = np.linalg.norm(wc - closest) - r

                    # Blend with existing
                    existing, _ = grid.get(key)
                    if existing == float("inf"):
                        blended = d
                    else:
                        blended = smooth_min(existing, d, blend * voxel_size)

                    # Material by depth: skin (surface) -> muscle -> bone (core)
                    # Simple heuristic: distance to centerline
                    if abs(blended) < voxel_size * 1.5:
                        mat = skin_id
                    elif abs(blended) < voxel_size * 3.0:
                        mat = muscle_id
                    else:
                        mat = bone_id

                    grid.set(key, blended, mat)

    return grid


# --- Deform grid via LBS (linear blend skinning on voxel lattice) ---
def deform_grid_lbs(grid: SDFGrid, bone_transforms: List[np.ndarray],
                    bone_weights: Dict[VoxelKey, List[Tuple[int, float]]],
                    rest_grid: SDFGrid) -> SDFGrid:
    """Deform SDF grid by warping voxel positions via LBS.

    bone_transforms: list of 4x4 world matrices per bone (rest -> current)
    bone_weights: voxel_key -> [(bone_idx, weight), ...] (sum weights = 1)
    rest_grid: undeformed grid (source of truth for SDF values)
    """
    deformed = SDFGrid(voxel_size=grid.voxel_size, band=grid.band)
    deformed._material_names = grid._material_names.copy()

    for key, (sdf, mat) in rest_grid._data.items():
        if key not in bone_weights:
            # Rigid: find nearest bone, use its transform
            continue
        wc = rest_grid.voxel_center_world(key)
        wc_h = np.array([wc[0], wc[1], wc[2], 1.0])
        new_pos = np.zeros(3)
        for bone_idx, w in bone_weights[key]:
            if bone_idx < len(bone_transforms):
                new_pos += w * (bone_transforms[bone_idx] @ wc_h)[:3]
        new_key = deformed.world_to_voxel(new_pos)
        deformed.set(new_key, sdf, mat)

    return deformed