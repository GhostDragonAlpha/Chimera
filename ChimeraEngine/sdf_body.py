"""sdf_body.py — A membrane whose SHAPE IS AN SDF FIELD.

Replaces rigid Body (physics.py). The membrane IS the grid.
Physics acts on the grid; rendering reads the same grid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from core.sdf_grid import SDFGrid, VoxelKey, build_sdf_from_bones
from core.membranes import Membrane, Port, State, Verb
from physics import Actuator, thruster, quat_to_mat, quat_mul, quat_identity


@dataclass
class SDFBody:
    """A membrane with mass, inertia, and an SDF grid as its shape.

    The grid IS the collision shape, the render source, and the deformation target.
    No separate mesh, no convex hull, no GJK/EPA.
    """
    membrane: Membrane
    mass: float
    grid: SDFGrid                                  # THE SHAPE
    com_local: np.ndarray = field(default_factory=lambda: np.zeros(3))
    inertia_local: np.ndarray = field(default_factory=lambda: np.eye(3))
    x: np.ndarray = field(default_factory=lambda: np.zeros(3))       # world COM
    q: np.ndarray = field(default_factory=quat_identity)             # body -> world
    v: np.ndarray = field(default_factory=lambda: np.zeros(3))       # world linear vel
    w: np.ndarray = field(default_factory=lambda: np.zeros(3))       # BODY-frame ang vel
    actuators: List[Actuator] = field(default_factory=list)

    # Deformation state
    rest_grid: Optional[SDFGrid] = None            # undeformed reference
    bone_transforms: List[np.ndarray] = field(default_factory=list)  # per-bone 4x4
    voxel_bone_weights: Dict[VoxelKey, List[Tuple[int, float]]] = field(default_factory=dict)

    def __post_init__(self):
        self.inertia_local = np.asarray(self.inertia_local, float)
        self._inv_I = np.linalg.inv(self.inertia_local)
        if self.rest_grid is None:
            self.rest_grid = self.grid  # initially undeformed

    def add_actuator(self, act: Actuator) -> Actuator:
        self.actuators.append(act)
        self.membrane.ports[act.port.name] = act.port
        self.membrane.verbs[act.name] = act.verb
        return act

    def net_local(self) -> Tuple[np.ndarray, np.ndarray]:
        """Total (force, torque) in BODY frame from all actuators."""
        F = np.zeros(3)
        T = np.zeros(3)
        for a in self.actuators:
            f = a.local_force()
            r = a.port.at - self.com_local
            F += f
            T += np.cross(r, f)
        return F, T

    # --- SDF queries in world space ---
    def sdf_at_world(self, world_pos: np.ndarray) -> float:
        """SDF value at world position. Uses grid's trilinear sample."""
        if getattr(self, "is_ground", False):
            return float(world_pos[1] - self._plane_y)
        local = self.world_to_local(world_pos)
        return self.grid.sample_trilinear(local)[0]

    def grad_at_world(self, world_pos: np.ndarray) -> np.ndarray:
        """∇SDF (contact normal) at world position."""
        if getattr(self, "is_ground", False):
            return np.array([0.0, 1.0, 0.0])
        local = self.world_to_local(world_pos)
        grad_local = self.grid.gradient(local)
        # Rotate gradient to world frame
        R = quat_to_mat(self.q)
        return R @ grad_local

    def material_at_world(self, world_pos: np.ndarray) -> int:
        if getattr(self, "is_ground", False):
            return self.grid.material_id("void") if self.grid._material_names else 0
        local = self.world_to_local(world_pos)
        return self.grid.sample_trilinear(local)[1]

    # --- coordinate transforms ---
    def world_to_local(self, world_pos: np.ndarray) -> np.ndarray:
        R = quat_to_mat(self.q)
        return R.T @ (world_pos - self.x) + self.com_local

    def local_to_world(self, local_pos: np.ndarray) -> np.ndarray:
        R = quat_to_mat(self.q)
        return self.x + R @ (local_pos - self.com_local)

    def port_world(self, name: str) -> Tuple[np.ndarray, np.ndarray]:
        p = self.membrane.ports[name]
        R = quat_to_mat(self.q)
        pos = self.x + R @ (p.at - self.com_local)
        facing = R @ p.facing
        return pos, facing

    # --- dynamics step (rigid body part) ---
    def step_rigid(self, dt: float, gravity: np.ndarray = None) -> None:
        """Integrate rigid-body motion. Deformation handled separately."""
        if getattr(self, "is_ground", False):
            return  # static
        R = quat_to_mat(self.q)
        F_body, T_body = self.net_local()

        # Linear
        F_world = R @ F_body
        if gravity is not None:
            F_world += np.asarray(gravity, float) * self.mass
        self.v += (F_world / self.mass) * dt
        self.x += self.v * dt

        # Angular (Euler in body frame)
        wdot = self._inv_I @ (T_body - np.cross(self.w, self.inertia_local @ self.w))
        self.w += wdot * dt
        wq = np.array([self.w[0], self.w[1], self.w[2], 0.0])
        self.q += 0.5 * quat_mul(self.q, wq) * dt
        self.q /= (np.linalg.norm(self.q) + 1e-15)

    # --- deformation: update grid from bone transforms ---
    def update_deformation(self) -> None:
        """Warp grid via LBS from bone transforms. Call after skeleton moves."""
        if not self.bone_transforms or not self.rest_grid:
            return
        from core.sdf_grid import deform_grid_lbs
        self.grid = deform_grid_lbs(
            self.grid, self.bone_transforms, self.voxel_bone_weights, self.rest_grid
        )

    # --- vectorized world-point accessor (for contact candidates, no Python loop) ---
    def world_points(self, stride: int = 1) -> np.ndarray:
        """(N,3) world positions of (subsampled) stored voxels. Vectorized."""
        if getattr(self, "is_ground", False):
            return np.zeros((0, 3), np.float32)
        pos_local, _, _ = self.grid.world_positions(stride)
        rel = pos_local - self.com_local
        R = quat_to_mat(self.q)
        return (self.x[None, :] + (rel @ R.T)).astype(np.float32)

    # --- surface voxels for rendering ---
    def surface_voxels_world(self, stride: int = 1) -> List[Tuple[np.ndarray, float, int]]:
        """Surface voxels in world space: (world_pos, sdf, material_id).

        `stride` subsamples the stored voxels. Implemented vectorized (no Python loop)
        so the contact solver and renderer do not pay O(N_voxels) Python cost per step.
        """
        if getattr(self, "is_ground", False):
            return []  # ground is rendered as an analytic quad, not voxels
        pos_local, sdfs, mats = self.grid.world_positions(stride)
        # grid local coords -> relative to COM -> world
        rel = pos_local - self.com_local
        R = quat_to_mat(self.q)
        world = self.x[None, :] + (rel @ R.T)
        return [(world[i], float(sdfs[i]), int(mats[i])) for i in range(world.shape[0])]

    # --- momentum (for verification) ---
    def momentum(self) -> Tuple[np.ndarray, np.ndarray]:
        R = quat_to_mat(self.q)
        P = self.mass * self.v
        L = R @ (self.inertia_local @ self.w) + self.mass * np.cross(self.x, self.v)
        return P, L


@dataclass
class SDFWorld:
    """World of SDF bodies. Fixed-timestep step with contact solving."""
    bodies: List[SDFBody] = field(default_factory=list)
    gravity: Optional[np.ndarray] = None
    dt: float = 1/60
    substeps: int = 4
    contact_stiffness: float = 1e5
    contact_damping: float = 1e3
    contact_stride: int = 6           # subsample surface voxels for contact probing
    use_gpu: bool = False             # GPU-native SDF contact (cupy) when available

    def _ensure_gpu(self) -> None:
        if getattr(self, "_gpu", None) is not None:
            return
        from core.sdf_gpu import GpuSdfSolver
        solver = GpuSdfSolver(contact_stiffness=self.contact_stiffness)
        self._gpu = solver
        self._gpu_vols = []
        for b in self.bodies:
            inv = 0.0 if getattr(b, "is_ground", False) else 1.0 / b.mass
            self._gpu_vols.append(solver.upload_body(b, inv, stride=self.contact_stride))

    def _solve_contacts_gpu(self, dt: float) -> None:
        """GPU contact: each pair, body_i candidates vs body_j uploaded volume.

        Ground (analytic plane, no grid) is handled directly on the host: it's one
        plane, so the deepest penetration among the candidate points is a single numpy
        reduction — still no per-voxel Python SDF walk.
        """
        self._ensure_gpu()
        solver = self._gpu
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                bi, bj = self.bodies[i], self.bodies[j]
                vi, vj = self._gpu_vols[i], self._gpu_vols[j]

                if getattr(bj, "is_ground", False):
                    # analytic plane: sdf = y - plane_y
                    plane_y = getattr(bj, "_plane_y", 0.0)
                    pts = bi.world_points(self.contact_stride)
                    if pts.shape[0] == 0:
                        continue
                    ys = pts[:, 1] - plane_y
                    pen = float(np.max(-ys)) if (ys < 0).any() else 0.0
                    contact = {"pen": pen, "normal": np.array([0.0, 1.0, 0.0])} if pen > 0 else None
                    solver.apply(bi, vi, bj, vj, contact, dt)
                else:
                    # body-vs-body: candidate points already live on the GPU (local_pts);
                    # the kernel transforms them with body i's current transform.
                    if vol_i.local_pts.shape[0] == 0:
                        continue
                    contact = solver.solve_pair(bi, vi, bj, vj, dt)
                    solver.apply(bi, vi, bj, vj, contact, dt)

    def add_ground(self, half_extent: float = 50.0, y: float = 0.0) -> "SDFBody":
        """Add an infinite-mass ground plane at height `y` (SDF = y_world - y)."""
        from core.sdf_grid import SDFGrid
        g = SDFGrid(voxel_size=1.0, band=1e9)  # analytic plane; band disabled
        body = SDFBody(
            membrane=self._ground_membrane(),
            mass=float("inf"),
            grid=g,
            com_local=np.array([0.0, y, 0.0]),
        )
        body.is_ground = True  # type: ignore[attr-defined]
        body._plane_y = y      # type: ignore[attr-defined]
        self.bodies.append(body)
        return body

    @staticmethod
    def _ground_membrane():
        from core.membranes import Membrane
        return Membrane(name="ground", scale=1.0)

    def add(self, body: SDFBody) -> SDFBody:
        self.bodies.append(body)
        return body

    def step(self) -> None:
        dt_sub = self.dt / self.substeps
        for _ in range(self.substeps):
            # 1. Integrate rigid motion (skip static bodies)
            for b in self.bodies:
                if not getattr(b, "is_ground", False):
                    b.step_rigid(dt_sub, self.gravity)

            # 2. Solve contacts (SDF-based)
            if self.use_gpu:
                self._solve_contacts_gpu(dt_sub)
            else:
                self._solve_contacts(dt_sub)

            # 3. Update deformation from bone transforms (skip static)
            for b in self.bodies:
                if not getattr(b, "is_ground", False):
                    b.update_deformation()

    def _solve_contacts(self, dt: float) -> None:
        """XPBD-style contact solve using SDF queries.

        For each body pair: sample body A's SDF at body B's surface voxels (and vice versa).
        Penetration = -sdf (when sdf < 0). Normal = ∇SDF.
        """
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                bi, bj = self.bodies[i], self.bodies[j]
                self._solve_pair(bi, bj, dt)

    def _solve_pair(self, bi: SDFBody, bj: SDFBody, dt: float) -> None:
        """Stable SDF contact: reduce to the single deepest penetrating voxel, then
        project position out of penetration and cancel approaching normal velocity.

        Over-counts if every penetrating voxel emitted its own impulse (thousands of
        contacting voxels -> explosion). One manifold per pair is correct for a body
        resting on a surface and is stable at any stiffness.
        """
        wi = 0.0 if getattr(bi, "is_ground", False) else 1.0 / bi.mass
        wj = 0.0 if getattr(bj, "is_ground", False) else 1.0 / bj.mass
        wsum = wi + wj
        if wsum == 0:
            return

        # Find deepest penetration of bi's surface into bj (and vice versa).
        best = None  # (pen, normal, body_a, body_b) with a = penetrator
        for wp, sdf_i, _ in bi.surface_voxels_world(self.contact_stride):
            sdf_j = bj.sdf_at_world(wp)
            if sdf_j < 0:
                pen = -sdf_j
                n = bj.grad_at_world(wp)
                if best is None or pen > best[0]:
                    best = (pen, n, bi, bj)
        for wp, sdf_j, _ in bj.surface_voxels_world(self.contact_stride):
            sdf_i = bi.sdf_at_world(wp)
            if sdf_i < 0:
                pen = -sdf_i
                n = bi.grad_at_world(wp)
                if best is None or pen > best[0]:
                    best = (pen, n, bj, bi)

        if best is None:
            return
        pen, n, a, b = best
        nn = np.linalg.norm(n)
        if nn < 1e-8:
            return
        n = n / nn

        # Resolve normal relative velocity: inelastic normal contact (no bounce, no drift).
        # Fully cancel the normal component, split by inverse mass.
        v_rel_n = float(np.dot(a.v - b.v, n))
        dv = -v_rel_n
        a.v += dv * n * (wi / wsum)
        b.v -= dv * n * (wj / wsum)

        # Positional projection: push the two bodies apart along the normal.
        # `a` is the penetrator (its voxel is inside `b`); it moves along +n
        # (out of b's surface), `b` moves along -n. Ground (wj=0) stays put.
        corr = pen * 0.2  # baumgarte
        a.x += corr * n * (wi / wsum)
        b.x -= corr * n * (wj / wsum)


# --- Factory: build SDFBody from terrarium genome ---
def body_from_genome(genome, seed: int, voxel_size: float = 0.01,
                     mass_per_voxel: float = 100.0) -> SDFBody:
    """Create SDFBody from terrarium genome.

    Grows skeleton → builds SDF grid → computes mass/inertia from voxelized volume.
    """
    from core.terrarium import grow, Genome

    bones = grow(genome, seed)
    grid = build_sdf_from_bones(bones, voxel_size=voxel_size)

    # Estimate mass from voxel count (rough)
    n_voxels = len(grid)
    voxel_vol = voxel_size ** 3
    mass = n_voxels * voxel_vol * mass_per_voxel

    # Inertia approximation: box around grid
    min_w, max_w = grid.bounds()
    extents = (max_w - min_w) / 2
    com = (max_w + min_w) / 2

    # Box inertia
    x, y, z = extents
    I = np.diag([mass*(y*y+z*z)/12, mass*(x*x+z*z)/12, mass*(x*x+y*y)/12])

    membrane = Membrane(name="organism", scale=float(max(extents)))
    body = SDFBody(
        membrane=membrane,
        mass=mass,
        grid=grid,
        com_local=com,
        inertia_local=I,
    )
    body.rest_grid = grid  # initially undeformed

    # TODO: compute voxel_bone_weights for LBS deformation
    # For each voxel, find influencing bones + weights (inverse distance)

    return body