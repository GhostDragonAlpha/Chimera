"""
Standalone Gaussian Splat Rasterizer — no Unreal Engine required.

Implements the 3DGS rendering pipeline in pure Python + NumPy:
  1. Project 3D splats → 2D screen space (via camera module)
  2. Tile-based culling and sorting
  3. Per-pixel alpha-blended Gaussian accumulation

This produces a numpy array (H × W × 3) RGB image that can be
saved to disk or displayed with any image viewer.

Based on: "3D Gaussian Splatting for Real-Time Radiance Field Rendering"
(Kerbl et al., SIGGRAPH 2023).
"""

import numpy as np
from dataclasses import dataclass
from ParticleEngine.camera import CameraParams
from ParticleEngine.splat import SplatState


@dataclass
class RenderConfig:
    """Rasterizer configuration."""
    tile_size: int = 16          # pixels per tile
    blend_mode: str = "alpha"    # "alpha", "additive", "opaque"
    background: tuple = (0.01, 0.01, 0.05)  # dark space background
    skip_covariance: bool = False  # if True, render as points (faster, less accurate)


class SplatRasterizer:
    """
    Software Gaussian splat rasterizer.

    Usage:
        rast = SplatRasterizer()
        splats: SplatState = conv.convert(sim.snapshot())
        cam = FirstPersonCamera(...)
        params = cam.params(800, 600)

        # Full pipeline: project + render
        image = rast.render(splats, cam, params)

        # Or manually:
        rast.project(splats, cam, params)
        image = rast.composite()
    """

    def __init__(self, config: RenderConfig | None = None):
        self.config = config or RenderConfig()
        self._projected: "ProjectedSplats | None" = None

    def render(
        self,
        splats: SplatState,
        camera: "FirstPersonCamera",
        params: CameraParams,
    ) -> np.ndarray:
        """
        Full render: project splats → composite image.
        Returns: (H, W, 3) uint8 RGB image.
        """
        self.project(splats, camera, params)
        return self.composite(params)

    def project(
        self,
        splats: SplatState,
        camera: "FirstPersonCamera",
        params: CameraParams,
    ):
        """
        Project all splats to screen space. Results stored internally
        and used by composite().
        """
        n = splats.count
        if n == 0:
            self._projected = ProjectedSplats(
                screen_xy=np.empty((0, 2), dtype=np.float32),
                cov_2d=np.empty((0, 2, 2), dtype=np.float32),
                depth=np.empty(0, dtype=np.float32),
                colors=np.empty((0, 3), dtype=np.float32),
                opacities=np.empty(0, dtype=np.float32),
                valid=np.empty(0, dtype=bool),
                width=params.width,
                height=params.height,
            )
            return

        if self.config.skip_covariance or splats.covariances_3x3 is None:
            # Fast path: render as points with fixed screen-space radius
            screen_xy, depth, valid = camera.project_points(
                splats.positions, params.width, params.height
            )
            # Fixed 2×2 covariance (small point)
            cov_2d = np.zeros((n, 2, 2), dtype=np.float32)
            cov_2d[:, 0, 0] = 2.0
            cov_2d[:, 1, 1] = 2.0
        else:
            screen_xy, cov_2d, depth, valid = camera.project_covariance(
                splats.positions,
                splats.covariances_3x3,
                params.width,
                params.height,
            )

        self._projected = ProjectedSplats(
            screen_xy=screen_xy,
            cov_2d=cov_2d,
            depth=depth,
            colors=splats.colors.copy(),
            opacities=splats.opacities.ravel().copy(),
            valid=valid,
            width=params.width,
            height=params.height,
        )

    def composite(self, params: CameraParams) -> np.ndarray:
        """
        Composite all projected splats into a final image.
        Uses tile-based sorting and per-pixel alpha blending.
        Returns (H, W, 3) uint8 RGB.
        """
        if self._projected is None or self._projected.valid.sum() == 0:
            bg = np.array(self.config.background, dtype=np.float32)
            return (bg * 255).astype(np.uint8)

        p = self._projected
        valid_idx = np.where(p.valid)[0]

        # Sort by depth (back to front for correct alpha blending)
        depths = p.depth[valid_idx]
        sort_order = np.argsort(-depths)  # farthest first
        sorted_idx = valid_idx[sort_order]

        n_splats = len(sorted_idx)

        # Build composite buffers
        H, W = p.height, p.width
        canvas = np.zeros((H, W, 3), dtype=np.float32)
        canvas[:] = self.config.background
        remaining_transmittance = np.ones((H, W), dtype=np.float32)

        # Tile grid
        tile_sz = self.config.tile_size
        tiles_x = (W + tile_sz - 1) // tile_sz
        tiles_y = (H + tile_sz - 1) // tile_sz

        # Precompute inverse covariances and determinants
        covs_2d = p.cov_2d[sorted_idx]  # (M, 2, 2)
        # Clamp covariance values to prevent overflow
        covs_2d = np.clip(covs_2d, -1e6, 1e6)
        dets = covs_2d[:, 0, 0] * covs_2d[:, 1, 1] - covs_2d[:, 0, 1] * covs_2d[:, 1, 0]
        # Clamp determinants — detect singular covariances
        valid_det = dets > 1e-12
        if not valid_det.all():
            # Fix degenerate covariances by adding identity
            for idx in np.where(~valid_det)[0]:
                covs_2d[idx, 0, 0] += 5.0
                covs_2d[idx, 1, 1] += 5.0
                covs_2d[idx, 0, 1] = 0.0
                covs_2d[idx, 1, 0] = 0.0
            dets = covs_2d[:, 0, 0] * covs_2d[:, 1, 1] - covs_2d[:, 0, 1] * covs_2d[:, 1, 0]
        dets = np.maximum(dets, 1e-12)
        inv_covs = np.zeros_like(covs_2d)
        inv_covs[:, 0, 0] = covs_2d[:, 1, 1] / dets
        inv_covs[:, 0, 1] = -covs_2d[:, 0, 1] / dets
        inv_covs[:, 1, 0] = -covs_2d[:, 0, 1] / dets
        inv_covs[:, 1, 1] = covs_2d[:, 0, 0] / dets
        # Clamp inverse covariances
        inv_covs = np.clip(inv_covs, -1e4, 1e4)

        # 3-sigma radius for each splat (pixel radius)
        # The 2D Gaussian half-extent in pixels at 3σ
        trace = covs_2d[:, 0, 0] + covs_2d[:, 1, 1]
        det_clamped = np.maximum(dets, 1e-12)
        discriminant = np.maximum(trace**2 - 4 * det_clamped, 0)
        eig1 = 0.5 * (trace + np.sqrt(discriminant))
        radii = 3.0 * np.sqrt(np.clip(eig1, 0.01, 1e8))
        radii = np.clip(radii, 1, 5000)  # reasonable pixel radius

        centers = p.screen_xy[sorted_idx]

        # Clamp centers to screen
        cx = np.clip(centers[:, 0], 0, W - 1)
        cy = np.clip(centers[:, 1], 0, H - 1)

        # Tile assignment
        tile_ids_x = (cx.astype(int) // tile_sz).clip(0, tiles_x - 1)
        tile_ids_y = (cy.astype(int) // tile_sz).clip(0, tiles_y - 1)
        tile_ids = tile_ids_y * tiles_x + tile_ids_x

        # Assign each splat to tiles it covers
        splat_tiles = []
        for i in range(n_splats):
            r = int(np.ceil(radii[i]))
            r = min(r, max(W, H))  # cap radius
            tx_min = max(0, int((cx[i] - r) // tile_sz))
            tx_max = min(tiles_x - 1, int((cx[i] + r) // tile_sz))
            ty_min = max(0, int((cy[i] - r) // tile_sz))
            ty_max = min(tiles_y - 1, int((cy[i] + r) // tile_sz))

            tiles_covered = []
            for ty in range(ty_min, ty_max + 1):
                for tx in range(tx_min, tx_max + 1):
                    tiles_covered.append(ty * tiles_x + tx)
            splat_tiles.append(tiles_covered)

        # Build tile → splat mapping
        tile_to_splats = [[] for _ in range(tiles_x * tiles_y)]
        for i, tiles in enumerate(splat_tiles):
            for tid in tiles:
                tile_to_splats[tid].append(i)

        # Render each tile
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                tid = ty * tiles_x + tx
                if not tile_to_splats[tid]:
                    continue

                # Pixel range for this tile
                px_start = tx * tile_sz
                px_end = min(px_start + tile_sz, W)
                py_start = ty * tile_sz
                py_end = min(py_start + tile_sz, H)

                # Only process splats that cover this tile (already sorted by depth)
                tile_splats = tile_to_splats[tid]

                # Pixel grid
                px_range = np.arange(px_start, px_end, dtype=np.float32)
                py_range = np.arange(py_start, py_end, dtype=np.float32)
                px_grid, py_grid = np.meshgrid(px_range, py_range)  # (h, w)

                # For each splat in this tile (front-to-back)
                for si in tile_splats:
                    alpha = p.opacities[sorted_idx[si]]
                    if alpha < 0.001:
                        continue

                    color = p.colors[sorted_idx[si]]  # (3,)

                    # Distance from pixel center to splat center
                    r = radii[si]
                    dx = px_grid - centers[si, 0]
                    dy = py_grid - centers[si, 1]

                    # Early cull: skip pixels beyond 4-sigma radius
                    dist_sq = dx*dx + dy*dy
                    if dist_sq.min() > (r*1.5)**2:
                        continue

                    # Gaussian weight: exp(-0.5 * d^T * Σ^-1 * d)
                    inv_cov = inv_covs[si]
                    # Clamp inv_cov components to prevent overflow
                    ic00 = np.clip(inv_cov[0, 0], -1e6, 1e6)
                    ic01 = np.clip(inv_cov[0, 1], -1e6, 1e6)
                    ic11 = np.clip(inv_cov[1, 1], -1e6, 1e6)
                    # d^T * Σ^-1 * d = dx²*c00 + 2*dx*dy*c01 + dy²*c11
                    gauss_exp = (
                        dx * dx * ic00
                        + 2.0 * dx * dy * ic01
                        + dy * dy * ic11
                    )
                    # Clip to prevent exp overflow
                    gauss_exp = np.clip(gauss_exp, 0, 80)
                    weight = np.exp(-0.5 * gauss_exp)

                    # Zero out distant pixels
                    weight[dist_sq > (r*1.5)**2] = 0.0

                    if weight.max() < 0.001:
                        continue

                    # Alpha contribution
                    contrib = alpha * weight

                    # Update canvas
                    canvas_h = py_end - py_start
                    canvas_w = px_end - px_start
                    for c in range(3):
                        canvas[py_start:py_end, px_start:px_end, c] += (
                            color[c] * contrib * remaining_transmittance[py_start:py_end, px_start:px_end]
                        )
                    remaining_transmittance[py_start:py_end, px_start:px_end] *= (1.0 - contrib)

        # Clamp and convert to uint8
        canvas = np.clip(canvas, 0.0, 1.0)
        return (canvas * 255).astype(np.uint8)


@dataclass
class ProjectedSplats:
    """Intermediate representation after projection, before compositing."""
    screen_xy: np.ndarray     # (N, 2) pixel coordinates
    cov_2d: np.ndarray        # (N, 2, 2) 2D screen-space covariances
    depth: np.ndarray         # (N,) camera-space depth
    colors: np.ndarray         # (N, 3) RGB
    opacities: np.ndarray      # (N,) alpha values
    valid: np.ndarray          # (N,) bool — in frustum
    width: int
    height: int
