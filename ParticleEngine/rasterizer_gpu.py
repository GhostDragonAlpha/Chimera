"""
GPU-accelerated Gaussian Splat Rasterizer — Numba CUDA.

Per-pixel parallel compositing. 9× faster than CPU at 400×300.
"""

import numpy as np
from numba import cuda
import math

TILE_SIZE = 16
MAX_PER_TILE = 1024


@cuda.jit
def _composite_kernel(
    pos_x, pos_y, ic00, ic01, ic11,
    col_r, col_g, col_b, opa, radii,
    tile_ids, tile_offsets,
    canvas_r, canvas_g, canvas_b,
    w, h, tiles_x, n_tiles,
    bg_r, bg_g, bg_b,
):
    px = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    py = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    if px >= w or py >= h:
        return

    r, g, b = bg_r, bg_g, bg_b
    trans = 1.0

    tx = px // TILE_SIZE
    ty = py // TILE_SIZE
    tid = ty * tiles_x + tx

    if tid >= n_tiles:
        canvas_r[py, px] = r; canvas_g[py, px] = g; canvas_b[py, px] = b
        return

    start = tile_offsets[tid]
    end = tile_offsets[tid + 1]

    for si in range(start, end):
        i = tile_ids[si]
        if i < 0:
            break
        alpha = opa[i]
        if alpha < 0.0001:
            continue

        dx = float(px) - pos_x[i]
        dy = float(py) - pos_y[i]

        r2 = radii[i] * radii[i] * 2.25
        if dx*dx + dy*dy > r2:
            continue

        gexp = dx*dx * ic00[i] + 2.0*dx*dy * ic01[i] + dy*dy * ic11[i]
        if gexp > 20.0:
            continue
        wgt = math.exp(-0.5 * gexp)
        if wgt < 0.001:
            continue

        c = alpha * wgt * trans
        r += col_r[i] * c
        g += col_g[i] * c
        b += col_b[i] * c
        trans *= (1.0 - c)
        if trans < 0.01:
            break

    canvas_r[py, px] = max(0.0, min(1.0, r))
    canvas_g[py, px] = max(0.0, min(1.0, g))
    canvas_b[py, px] = max(0.0, min(1.0, b))


class GPUSplatRasterizer:
    def __init__(self, bg=(0.01, 0.01, 0.05)):
        self.bg = bg

    def render(self, splats, camera, params):
        from ParticleEngine.splat import SplatState
        from ParticleEngine.camera import FirstPersonCamera, CameraParams
        from ParticleEngine.publisher import jit_covariance_to_inv, jit_build_tiles

        # Project
        screen_xy, cov_2d, depth, valid = camera.project_covariance(
            splats.positions, splats.covariances_3x3, params.width, params.height)

        v = np.where(valid)[0]
        if len(v) == 0:
            bg = np.array(self.bg, dtype=np.float32)
            return (np.tile(bg, (params.height, params.width, 1)) * 255).astype(np.uint8)

        # Sort by depth (back to front)
        order = v[np.argsort(-depth[v])]
        n = len(order)

        pos = screen_xy[order].astype(np.float32)
        cov = cov_2d[order].astype(np.float32)
        col = splats.colors[order].astype(np.float32)
        opa = splats.opacities.ravel()[order].astype(np.float32)

        # JIT: inverse covariances + radii (was 3ms, now sub-ms)
        cov_flat = cov.ravel()
        ic00, ic01, ic11, radii = jit_covariance_to_inv(cov_flat, n)

        # JIT: build tiles (was 40ms Python, now ~5ms)
        tiles_x = (params.width + TILE_SIZE - 1) // TILE_SIZE
        tiles_y = (params.height + TILE_SIZE - 1) // TILE_SIZE
        n_tiles = tiles_x * tiles_y
        cx = np.clip(pos[:,0].astype(np.int32), 0, params.width-1)
        cy = np.clip(pos[:,1].astype(np.int32), 0, params.height-1)
        tile_ids, offsets = jit_build_tiles(cx, cy, radii, tiles_x, tiles_y, n, TILE_SIZE)

        # Upload
        d = lambda a: cuda.to_device(a.astype(np.float32))
        di = lambda a: cuda.to_device(a.astype(np.int32))

        d_pos_x = d(pos[:,0]); d_pos_y = d(pos[:,1])
        d_ic00 = d(ic00); d_ic01 = d(ic01); d_ic11 = d(ic11)
        d_cr = d(col[:,0]); d_cg = d(col[:,1]); d_cb = d(col[:,2])
        d_opa = d(opa); d_radii = d(radii)
        d_tids = di(tile_ids); d_toff = di(offsets)

        cr = cuda.device_array((params.height, params.width), dtype=np.float32)
        cg = cuda.device_array((params.height, params.width), dtype=np.float32)
        cb = cuda.device_array((params.height, params.width), dtype=np.float32)

        # Launch
        block = (16, 16)
        grid = ((params.width+15)//16, (params.height+15)//16)

        _composite_kernel[grid, block](
            d_pos_x, d_pos_y, d_ic00, d_ic01, d_ic11,
            d_cr, d_cg, d_cb, d_opa, d_radii,
            d_tids, d_toff, cr, cg, cb,
            params.width, params.height, tiles_x, n_tiles,
            self.bg[0], self.bg[1], self.bg[2],
        )
        cuda.synchronize()

        r = cr.copy_to_host(); g = cg.copy_to_host(); b = cb.copy_to_host()
        canvas = np.stack([r, g, b], axis=2)
        canvas = np.clip(canvas, 0, 1)
        return (canvas * 255).astype(np.uint8)
