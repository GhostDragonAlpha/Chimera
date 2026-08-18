"""sdf_gpu.py — GPU-native SDF contact. The substrate's actual speed claim.

The CPU SDFBody contact solver walks every surface voxel in Python and pays ~15 us per
SDF query (8 dict lookups + trilinear). That is the wall: at 8k voxels x 2 substeps it is
seconds per step, which makes the whole unified-substrate idea pointless.

This module uploads each body's sparse grid, ONCE per shape-change, as a dense float32
volume (SDFGrid.to_dense_volume). Contact is then a CUDA kernel: for each candidate voxel
of body i we sample body j's volume (trilinear) in body j's local frame, read penetration
(-sdf) and the SDF gradient (contact normal), and resolve the constraint in parallel. No
per-voxel Python. The reference CPU solver in sdf_body.SDFWorld._solve_pair is kept as the
oracle for the Rule-0 falsifier (penetration must agree within 1e-3).

RULE 0 MEMBRANE
  STATEMENT  A sparse SDF grid uploaded once to the GPU answers contact for all candidate
             voxels in one parallel kernel, making SDF contact faster than the serial
             Python walk.
  PREDICTION At ~8k candidate voxels the GPU contact step is faster than the CPU step and
             yields identical penetration (|diff| < 1e-3).
  FALSIFIER  GPU step time >= CPU step time at equal voxel count, OR penetration differs
             from the CPU oracle by > 1e-3 -> the GPU substrate fails.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

try:
    import cupy as cp
    _HAVE_CUPY = True
except Exception:  # pragma: no cover
    _HAVE_CUPY = False

# numba.cuda is not used: the kernel is CUDA C, compiled via cupy.RawKernel.

# ---------------------------------------------------------------------------
# Device helpers
# ---------------------------------------------------------------------------

_SAMPLE_SRC = r"""
__device__ float trilinear(const float* vol, const int* dims,
                           float x, float y, float z, float far_val) {
    int dx = dims[0], dy = dims[1], dz = dims[2];
    if (dx <= 1 || dy <= 1 || dz <= 1) return far_val;
    int x0 = (int)floorf(x); int y0 = (int)floorf(y); int z0 = (int)floorf(z);
    float tx = x - x0, ty = y - y0, tz = z - z0;
    int x1 = x0 + 1, y1 = y0 + 1, z1 = z0 + 1;
    if (x0 < 0 || y0 < 0 || z0 < 0 || x1 >= dx || y1 >= dy || z1 >= dz) return far_val;
    int o000 = (x0*dy + y0)*dz + z0;
    int o100 = (x1*dy + y0)*dz + z0;
    int o010 = (x0*dy + y1)*dz + z0;
    int o110 = (x1*dy + y1)*dz + z0;
    int o001 = (x0*dy + y0)*dz + z1;
    int o101 = (x1*dy + y0)*dz + z1;
    int o011 = (x0*dy + y1)*dz + z1;
    int o111 = (x1*dy + y1)*dz + z1;
    float c00 = vol[o000]*(1-tx) + vol[o100]*tx;
    float c01 = vol[o010]*(1-tx) + vol[o110]*tx;
    float c10 = vol[o001]*(1-tx) + vol[o101]*tx;
    float c11 = vol[o011]*(1-tx) + vol[o111]*tx;
    float c0 = c00*(1-ty) + c01*ty;
    float c1 = c10*(1-ty) + c11*ty;
    return c0*(1-tz) + c1*tz;
}

__device__ float sample_sdf(const float* vol, const int* dims, const float* origin,
                            float vs, const float* R, const float* t,
                            float px, float py, float pz, float far_val) {
    float rx = px - t[0], ry = py - t[1], rz = pz - t[2];
    float lx = R[0]*rx + R[3]*ry + R[6]*rz;
    float ly = R[1]*rx + R[4]*ry + R[7]*rz;
    float lz = R[2]*rx + R[5]*ry + R[8]*rz;
    float vx = (lx - origin[0]) / vs;
    float vy = (ly - origin[1]) / vs;
    float vz = (lz - origin[2]) / vs;
    return trilinear(vol, dims, vx, vy, vz, far_val);
}

__device__ void sample_grad(const float* vol, const int* dims, const float* origin,
                            float vs, const float* R, const float* t,
                            float px, float py, float pz, float far_val, float* g) {
    float e = vs * 0.5f;
    float gx = sample_sdf(vol,dims,origin,vs,R,t, px+e,py,pz, far_val)
             - sample_sdf(vol,dims,origin,vs,R,t, px-e,py,pz, far_val);
    float gy = sample_sdf(vol,dims,origin,vs,R,t, px,py+e,pz, far_val)
             - sample_sdf(vol,dims,origin,vs,R,t, px,py-e,pz, far_val);
    float gz = sample_sdf(vol,dims,origin,vs,R,t, px,py,pz+e, far_val)
             - sample_sdf(vol,dims,origin,vs,R,t, px,py,pz-e, far_val);
    float n = sqrtf(gx*gx + gy*gy + gz*gz) + 1e-8f;
    g[0] = gx/n; g[1] = gy/n; g[2] = gz/n;
}
"""

_KERNEL_SRC = _SAMPLE_SRC + r"""
// One thread per candidate voxel of body i. Candidate points live on the GPU as
// BODY-LOCAL coordinates (constant for the body's shape); here we transform them to
// world with body i's current R_i/x_i uniforms, then sample body j's volume. This way
// the candidate set is uploaded ONCE per shape and never re-uploaded between substeps
// -- only the 12-float R_i/x_i uniforms change per substep.
extern "C" __global__ void contact_kernel(
        const float* local_pts, // [N,3] candidate points in body i LOCAL frame
        const int   N,
        const float* Ri,        // [9] body i R (world<-local, row-major)
        const float* xi,        // [3] body i world position
        const float* vol,       // body j dense SDF volume
        const int*   dims,      // [3]
        const float* origin,   // [3] body j volume world origin
        const float  vs,       // j voxel size
        const float* R,        // [9] body j R (world<-local, row-major)
        const float* t,        // [3] body j world position
        const float  far_val,
        float*       out_pen,  // [N] output penetration per candidate (>=0)
        float*       out_n     // [N,3] output contact normal per candidate
) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx >= N) return;
    // world = xi + Ri * local
    float lx0 = local_pts[idx*3+0], ly0 = local_pts[idx*3+1], lz0 = local_pts[idx*3+2];
    float px = xi[0] + Ri[0]*lx0 + Ri[3]*ly0 + Ri[6]*lz0;
    float py = xi[1] + Ri[1]*lx0 + Ri[4]*ly0 + Ri[7]*lz0;
    float pz = xi[2] + Ri[2]*lx0 + Ri[5]*ly0 + Ri[8]*lz0;
    float sdf = sample_sdf(vol, dims, origin, vs, R, t, px, py, pz, far_val);
    if (sdf >= 0.0f) {
        out_pen[idx] = 0.0f;
        out_n[idx*3+0] = 0.0f; out_n[idx*3+1] = 0.0f; out_n[idx*3+2] = 0.0f;
        return;
    }
    float g[3];
    sample_grad(vol, dims, origin, vs, R, t, px, py, pz, far_val, g);
    out_pen[idx] = -sdf;             // penetration depth
    out_n[idx*3+0] = g[0]; out_n[idx*3+1] = g[1]; out_n[idx*3+2] = g[2];
}
"""

# --- splat emission kernel: surface voxels -> render buffer, entirely on GPU ---
# Writes the 28-column splat buffer the renderer consumes, directly from the GPU-resident
# local_pts + material ids + transform. No host loop over voxels. NCOLS layout matches
# master_loop.py (PX..PZ=0..2, TYPE=11, CR..ALPHA=16..19, SIZE=20).
_EMIT_SRC = r"""
extern "C" __global__ void emit_splats_kernel(
        const float* local_pts,  // [N,3] body-local surface voxel coords
        const int*  mat_ids,     // [N]   material id per voxel
        const int   N,
        const float* Ri,         // [9] body i R (world<-local)
        const float* xi,         // [3] body i world position
        float vs,                // voxel size (splat footprint)
        const float* mat_rgba,   // [nmat*4] RGBA lookup
        int nmat,
        float* buf,              // [N,28] output splat buffer
        int ncols) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx >= N) return;
    float lx = local_pts[idx*3+0], ly = local_pts[idx*3+1], lz = local_pts[idx*3+2];
    float wx = xi[0] + Ri[0]*lx + Ri[3]*ly + Ri[6]*lz;
    float wy = xi[1] + Ri[1]*lx + Ri[4]*ly + Ri[7]*lz;
    float wz = xi[2] + Ri[2]*lx + Ri[5]*ly + Ri[8]*lz;
    int m = mat_ids[idx];
    if (m < 0 || m >= nmat) m = 0;
    int o = idx * ncols;
    buf[o+0] = wx; buf[o+1] = wy; buf[o+2] = wz;
    buf[o+9]  = 1.0f; buf[o+10] = -1.0f; buf[o+11] = 3.0f;
    buf[o+16] = mat_rgba[m*4+0];
    buf[o+17] = mat_rgba[m*4+1];
    buf[o+18] = mat_rgba[m*4+2];
    buf[o+19] = mat_rgba[m*4+3];
    buf[o+20] = vs * 1.2f;
}
"""


@dataclass
class GpuVolume:
    """A body's SDF uploaded to the GPU, plus its current world transform.

    `local_pts` holds the body's surface-voxel coordinates in the BODY-LOCAL frame and
    is uploaded ONCE per shape. The contact kernel transforms them to world each call
    using Ri/xi, so candidate data never crosses the PCIe bus between substeps.

    `d_Ri`/`d_xi` (body i transform) and `d_R`/`d_t` (body j transform) are persistent
    device buffers updated in place each substep -- no per-call allocation/upload.
    """
    d_vol: object
    d_dims: object
    d_origin: object
    local_pts: object
    vs: float
    far: float
    d_Ri: object = None      # persistent device buffer [9] (body i world<-local)
    d_xi: object = None      # persistent device buffer [3] (body i world pos)
    d_R: object = None       # persistent device buffer [9] (body j world<-local)
    d_t: object = None       # persistent device buffer [3] (body j world pos)
    d_mats: object = None
    d_render_pts: object = None   # [M,3] full-res body-local surface pts (stride 1)
    d_render_mats: object = None  # [M] material ids for render pts
    inv_mass: float = 0.0    # 0 for static (ground)

    def __post_init__(self):
        pass


class GpuSdfSolver:
    """Owns uploaded volumes and resolves pairwise SDF contact on the GPU (CUDA C via cupy)."""

    def __init__(self, contact_stiffness: float = 1e3, contact_damping: float = 20.0,
                 baumgarte: float = 0.2):
        if not _HAVE_CUPY:
            raise RuntimeError("cupy is required for the GPU SDF contact path")
        self.k = contact_stiffness
        self.c = contact_damping
        self.baumgarte = baumgarte
        self._kernel = cp.RawKernel(_KERNEL_SRC, "contact_kernel")
        self._emit_kernel = cp.RawKernel(_EMIT_SRC, "emit_splats_kernel")
        self.volumes: List[GpuVolume] = []
        # Material RGBA table (nmat x 4, row-major). Set via set_material_table.
        self.d_mat_rgba = None

    def upload_body(self, body, inv_mass: float, pad_voxels: int = 2, stride: int = 1) -> GpuVolume:
        vol, origin, dims = body.grid.to_dense_volume(pad_voxels=pad_voxels)
        # Local surface points: grid world positions minus the body's COM origin.
        pos, sdfs, mats = body.grid.world_positions(stride)
        local_pts = (pos - np.asarray(body.com_local, np.float32)).astype(np.float32)
        # Full-resolution (stride 1) point set for rendering -- decoupled from the contact
        # stride so the render buffer is never thinned by the contact candidate subsampling.
        rpos, _, rmts = body.grid.world_positions(1)
        render_pts = (rpos - np.asarray(body.com_local, np.float32)).astype(np.float32)
        far = float(body.grid.band * 4)
        gv = GpuVolume(
            d_vol=cp.asarray(np.ascontiguousarray(vol, np.float32)),
            d_dims=cp.asarray(np.ascontiguousarray(dims, np.int32)),
            d_origin=cp.asarray(np.ascontiguousarray(origin, np.float32)),
            local_pts=cp.asarray(np.ascontiguousarray(local_pts, np.float32)),
            d_mats=cp.asarray(np.ascontiguousarray(mats, np.int32)),
            d_render_pts=cp.asarray(np.ascontiguousarray(render_pts, np.float32)),
            d_render_mats=cp.asarray(np.ascontiguousarray(rmts, np.int32)),
            vs=float(body.grid.voxel_size),
            far=far,
            d_Ri=cp.zeros(9, np.float32),
            d_xi=cp.zeros(3, np.float32),
            d_R=cp.zeros(9, np.float32),
            d_t=cp.zeros(3, np.float32),
            inv_mass=inv_mass,
        )
        self.volumes.append(gv)
        return gv

    def set_material_table(self, rgba: np.ndarray) -> None:
        """rgba: (nmat, 4) float32 RGBA per material id. Uploaded once."""
        rgba = np.ascontiguousarray(rgba, np.float32)
        self.d_mat_rgba = cp.asarray(rgba)

    def emit_splat_buffer(self, body, vol: GpuVolume, ncols: int = 28) -> np.ndarray:
        """Render feed: emit the 28-col splat buffer from the GPU-resident local_pts.

        Syncs the body's CURRENT transform onto the GPU, then a single kernel writes the
        whole splat buffer (position + material RGBA + size) from local_pts. Returns a
        host numpy array (N, NCOLS) ready for the renderer. The per-voxel loop is on the
        GPU; only one contiguous download crosses the bus.
        """
        self._sync_transform(vol, body, "i")
        rpts = getattr(vol, "d_render_pts", None)
        N = rpts.shape[0] if rpts is not None else 0
        if N == 0 or self.d_mat_rgba is None:
            return np.zeros((0, ncols), np.float32)
        d_buf = cp.zeros((N, ncols), dtype=np.float32)
        threads = 256
        blocks = (N + threads - 1) // threads
        self._emit_kernel((blocks,), (threads,),
                          (rpts, vol.d_render_mats, N,
                           vol.d_Ri, vol.d_xi, vol.vs,
                           self.d_mat_rgba, self.d_mat_rgba.shape[0],
                           d_buf, ncols))
        return cp.asnumpy(d_buf)

    @staticmethod
    def _world_R(body) -> np.ndarray:
        from physics import quat_to_mat
        R = quat_to_mat(body.q)
        return np.ascontiguousarray(R, np.float32).reshape(9)

    def _sync_transform(self, gv: GpuVolume, body, which: str) -> None:
        """Update gv's persistent device transform buffer in place (no re-alloc)."""
        if getattr(body, "is_ground", False):
            R = np.eye(3, dtype=np.float32).reshape(9)
            t = np.array([0.0, getattr(body, "_plane_y", 0.0), 0.0], np.float32)
        else:
            R = self._world_R(body)
            t = np.ascontiguousarray(np.asarray(body.x, np.float32), np.float32)
        buf_R = gv.d_Ri if which == "i" else gv.d_R
        buf_t = gv.d_xi if which == "i" else gv.d_t
        buf_R.set(np.ascontiguousarray(R, np.float32))
        buf_t.set(np.ascontiguousarray(t, np.float32))

    def solve_pair(self, body_i, vol_i: GpuVolume, body_j, vol_j: GpuVolume,
                   dt: float) -> Optional[dict]:
        """Launch the contact kernel: body_i (GPU-local) candidates vs body_j volume.

        Candidate points are body i's LOCAL surface voxels (uploaded once); the kernel
        transforms them to world with body i's current transform. The deepest contact is
        reduced ON-GPU (cp.argmax) so only an int index crosses the bus back -- no full
        array download per substep.
        """
        self._sync_transform(vol_i, body_i, "i")   # body i transform -> device buffer
        self._sync_transform(vol_j, body_j, "j")   # body j transform -> device buffer
        N = vol_i.local_pts.shape[0]
        if N == 0:
            return None
        d_pen = cp.zeros(N, dtype=np.float32)
        d_n = cp.zeros((N, 3), dtype=np.float32)
        threads = 256
        blocks = (N + threads - 1) // threads
        self._kernel((blocks,), (threads,),
                     (vol_i.local_pts, N, vol_i.d_Ri, vol_i.d_xi,
                      vol_j.d_vol, vol_j.d_dims, vol_j.d_origin, vol_j.vs,
                      vol_j.d_R, vol_j.d_t, vol_j.far,
                      d_pen, d_n))
        # GPU-side reduction: only the deepest index comes back across the bus.
        idx = int(cp.argmax(d_pen).get())
        pen = float(d_pen[idx].get())
        if pen <= 0.0:
            return None
        nrm = d_n[idx].get()
        return {"pen": pen, "normal": nrm}

    def apply(self, body_i, vol_i, body_j, vol_j, contact, dt) -> None:
        """Resolve a single contact manifold by positional projection + normal damping."""
        if contact is None:
            return
        pen = contact["pen"]
        n = np.asarray(contact["normal"], dtype=np.float32)
        nn = np.linalg.norm(n)
        if nn < 1e-8:
            return
        n = n / nn
        wi = vol_i.inv_mass
        wj = vol_j.inv_mass
        wsum = wi + wj
        if wsum == 0:
            return
        # Resolve normal relative velocity: inelastic normal contact (no bounce, no drift).
        # Fully cancel the normal component, split by inverse mass.
        v_rel_n = float(np.dot(body_i.v - body_j.v, n))
        dv = -v_rel_n
        body_i.v += dv * n * (wi / wsum)
        body_j.v -= dv * n * (wj / wsum)
        # positional projection: push the two bodies apart along the normal.
        # body_i is the penetrator (its voxel is inside body_j); it moves along +n
        # (out of j's surface), body_j moves along -n. Ground (wj=0) stays put.
        corr = pen * self.baumgarte
        body_i.x += corr * n * (wi / wsum)
        body_j.x -= corr * n * (wj / wsum)
