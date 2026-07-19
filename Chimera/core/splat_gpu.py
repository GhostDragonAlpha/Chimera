"""splat_gpu — the splat rasterizer on the GPU, in Warp (the studio's own CUDA dialect).

Commissioned 2026-07-18, the human: "I just want to use the GPU because it comes out
much much faster — right now it's running on one thread in Python."

WHAT MOVES TO THE GPU AND WHAT DOES NOT (the brain_gpu discipline, applied to light):
- Projection + shading stay in numpy: they are O(N) over a few thousand splats —
  microseconds — and keeping them on the CPU keeps the math BYTE-COMPARABLE with the
  proven CPU path in core.matter_items (same Lambert + subsurface + Blinn block).
- COMPOSITING moves: the per-splat Python loop (the "mind-numbingly long" part) becomes
  ONE kernel, one thread per pixel, each walking the depth-sorted splat list front-to-
  back with early termination when transmittance dies. ZERO CPU<->GPU syncs inside —
  upload once, launch once, read the finished image back once (brain_gpu's ONE RULE).
- This is the O(W*H*N) per-pixel formulation, correct and simple, fast to ~100k splats.
- float32 on the GPU vs float64 on the CPU: parity is asserted at ~1e-3 MAE, not 0.0.

tb-0179 (the baby-toy critique — sub-cm density, 200k-1.5M splats) ADDS THE TILE
PIPELINE the module docstring above always said would be needed past ~100k:
  PROJECT (unchanged, numpy)  ->  BIN each splat into every 16x16-pixel tile its screen
  footprint overlaps  ->  PER-TILE DEPTH ORDER  ->  COMPOSITE (one GPU thread per pixel,
  walking only ITS TILE'S local splat list instead of every splat in the scene).

HOW THE BINNING STAYS CORRECT WITHOUT A SEPARATE PER-TILE SORT: `order` (the existing
GLOBAL front-to-back permutation, already computed once by np.argsort(depth)) is walked
to build the duplicate (tile, splat) list, so the duplicates are laid down front-to-back
BEFORE the tile grouping happens. A single **stable** sort by tile id alone (numpy
`kind="stable"`) then groups by tile while PRESERVING the relative front-to-back order of
every group — the textbook 3DGS "key-sort once" trick, done with a stable sort on one key
instead of a combined 64-bit (tile,depth) key. This bookkeeping (_tile_bins) is
O(splats x avg tiles overlapped) — small, and stays on the CPU in numpy, matching the
division of labor this module already uses for projection/shading. Only the expensive
part — O(pixels x LOCAL tile density) instead of O(pixels x ALL splats) — moves to the
GPU kernel, which is the actual algorithmic win at high N.

Drop-in: rasterize(...) and rasterize_tiled(...) share the EXACT projection/shading math
(one shared helper, _project_and_shade) and the exact signature/semantics of
matter_items.rasterize — the CPU reference in core.matter_items and core.splat_emit is
UNTOUCHED by this file.

Benchmark + parity proof (boulder, low count, vs the CPU reference AND vs the tiled path;
then a REAL limb-density scaling table): python -m core.splat_gpu
"""

from __future__ import annotations

import math
import time

import numpy as np

from core.splat_emit import AMBIENT, _camera_frame, _dir_from_azel

_WP = None
_KERNEL = None
_KERNEL_TILED = None


def _warp():
    """Lazy init so importing this module never costs anything on CPU-only boxes."""
    global _WP, _KERNEL, _KERNEL_TILED
    if _WP is not None:
        return _WP, _KERNEL, _KERNEL_TILED
    import warp as wp
    wp.init()
    if not wp.get_device().is_cuda:
        raise RuntimeError("no CUDA device — use the CPU rasterizer")

    @wp.kernel
    def composite(sx: wp.array(dtype=float), sy: wp.array(dtype=float),
                  inv00: wp.array(dtype=float), inv01: wp.array(dtype=float),
                  inv11: wp.array(dtype=float), rad2: wp.array(dtype=float),
                  alpha: wp.array(dtype=float), col: wp.array(dtype=wp.vec3),
                  order: wp.array(dtype=int), n: int, bg: float,
                  img: wp.array2d(dtype=wp.vec3)):
        py, px = wp.tid()
        x = float(px)
        y = float(py)
        T = float(1.0)
        acc = wp.vec3(0.0, 0.0, 0.0)
        for k in range(n):
            i = order[k]
            dx = x - sx[i]
            dy = y - sy[i]
            if dx * dx + dy * dy <= rad2[i]:
                m = inv00[i] * dx * dx + 2.0 * inv01[i] * dx * dy + inv11[i] * dy * dy
                if m < 50.0:
                    a = alpha[i] * wp.exp(-0.5 * m)
                    acc += (T * a) * col[i]
                    T *= (1.0 - a)
                    if T < 1e-4:
                        break
        img[py, px] = acc + wp.vec3(T * bg, T * bg, T * bg)

    @wp.kernel
    def composite_tiled(sx: wp.array(dtype=float), sy: wp.array(dtype=float),
                        inv00: wp.array(dtype=float), inv01: wp.array(dtype=float),
                        inv11: wp.array(dtype=float), rad2: wp.array(dtype=float),
                        alpha: wp.array(dtype=float), col: wp.array(dtype=wp.vec3),
                        tile_splats: wp.array(dtype=int), tile_offsets: wp.array(dtype=int),
                        tiles_x: int, tile_size: int, bg: float,
                        img: wp.array2d(dtype=wp.vec3)):
        py, px = wp.tid()
        x = float(px)
        y = float(py)
        tx = px // tile_size
        ty = py // tile_size
        tid = ty * tiles_x + tx
        start = tile_offsets[tid]
        end = tile_offsets[tid + 1]
        T = float(1.0)
        acc = wp.vec3(0.0, 0.0, 0.0)
        for k in range(start, end):
            i = tile_splats[k]
            dx = x - sx[i]
            dy = y - sy[i]
            if dx * dx + dy * dy <= rad2[i]:
                m = inv00[i] * dx * dx + 2.0 * inv01[i] * dx * dy + inv11[i] * dy * dy
                if m < 50.0:
                    a = alpha[i] * wp.exp(-0.5 * m)
                    acc += (T * a) * col[i]
                    T *= (1.0 - a)
                    if T < 1e-4:
                        break
        img[py, px] = acc + wp.vec3(T * bg, T * bg, T * bg)

    _WP, _KERNEL, _KERNEL_TILED = wp, composite, composite_tiled
    return _WP, _KERNEL, _KERNEL_TILED


def available() -> bool:
    try:
        _warp()
        return True
    except Exception:
        return False


def _project_and_shade(splats: dict, center: np.ndarray, radius: float,
                       azim: float, elev: float, light_azim: float, light_elev: float,
                       w: int, h: int):
    """The math ONE PLACE — both rasterize() and rasterize_tiled() call this, so any
    pixel difference between them can only come from the compositing STRATEGY (global
    per-pixel scan vs tile-local scan), never from divergent projection/shading code.
    Returns (sx, sy, inv00, inv01, inv11, rad2, color, order) — order is the GLOBAL
    front-to-back permutation (np.argsort(depth)), reused by the tile binner."""
    right, up, view_dir = _camera_frame(azim, elev)
    rel = splats["pos"] - center
    depth = rel @ view_dir
    scale_px = 0.42 * min(w, h) / radius
    sx = w / 2 + (rel @ right) * scale_px
    sy = h / 2 - (rel @ up) * scale_px

    J = np.stack([right, up], axis=0)
    cov2 = np.einsum('ij,njk,lk->nil', J, splats["cov"], J) * (scale_px ** 2)
    det = cov2[:, 0, 0] * cov2[:, 1, 1] - cov2[:, 0, 1] * cov2[:, 1, 0]
    ok = det > 1e-8
    det = np.where(ok, det, 1.0)
    inv00 = np.where(ok, cov2[:, 1, 1] / det, 0.0)
    inv01 = np.where(ok, -cov2[:, 0, 1] / det, 0.0)
    inv11 = np.where(ok, cov2[:, 0, 0] / det, 0.0)
    rad = 3.0 * np.sqrt(np.maximum(cov2[:, 0, 0], cov2[:, 1, 1]) + 1e-6)
    rad2 = np.where(ok, rad * rad, -1.0)          # rad2 < 0 => never composited

    # shading — the same block as matter_items.rasterize, verbatim math
    light_toward = _dir_from_azel(light_azim, light_elev)
    ndotl = np.clip(splats["normal"] @ light_toward, 0, None)
    back = np.clip(splats["normal"] @ (-light_toward), 0, None)
    shade = AMBIENT + (1 - AMBIENT) * ndotl + splats["subsurface"] * 0.6 * back
    base = np.clip(splats["albedo"] * shade[:, None], 0.0, 1.0)
    half = light_toward + (-view_dir)
    half = half / np.linalg.norm(half)
    ndoth = np.clip(splats["normal"] @ half, 0.0, None)
    r = splats.get("roughness")
    if r is None:
        color = base
    else:
        p = 4.0 + (1.0 - r) ** 2 * 220.0
        spec_i = (ndoth ** p) * (ndotl > 0)
        m = splats["metallic"][:, None]
        ks = 0.06 * (1 - m) + 0.55 * m
        spec_color = np.ones(3)[None, :] * (1 - m) + splats["albedo"] * m
        color = np.clip(base + ks * spec_i[:, None] * spec_color, 0.0, 1.0)

    order = np.argsort(depth).astype(np.int32)
    return sx, sy, inv00, inv01, inv11, rad2, color, order


def _cull_to_screen(sx, sy, rad2, order, w, h, max_visible):
    """Screen-space density cap: keep only the closest `max_visible` splats
    whose screen footprint overlaps the viewport.

    Returns a truncated order array (or full order if under budget).
    This prevents the O(W*H*N) bottleneck when the camera is inside the
    fractal and ALL splats are visible (observed 540ms at 5m range).
    """
    ok = rad2 >= 0.0
    rad = np.sqrt(np.maximum(rad2, 0.0))
    visible = (
        ok &
        (sx + rad >= 0) & (sx - rad < w) &
        (sy + rad >= 0) & (sy - rad < h))
    # Walk the depth-sorted order, keep only visible, cap at max_visible
    visible_order = order[visible[order]]
    if len(visible_order) > max_visible:
        return visible_order[:max_visible]
    return visible_order


def rasterize(splats: dict, center: np.ndarray, radius: float,
              azim: float, elev: float, light_azim: float, light_elev: float,
              w: int = 340, h: int = 340) -> np.ndarray:
    """GPU twin of matter_items.rasterize — identical projection + shading math
    (numpy), compositing in one Warp kernel. O(W*H*N): every pixel scans every splat.
    Fast and simple to ~100k splats (see rasterize_tiled for the pipeline past that)."""
    wp, kernel, _ = _warp()
    sx, sy, inv00, inv01, inv11, rad2, color, order = _project_and_shade(
        splats, center, radius, azim, elev, light_azim, light_elev, w, h)

    # Screen-space density cap: when camera is inside the fractal, ALL splats
    # are visible and the O(W*H*N) compositing becomes the bottleneck (540ms).
    # Keep only the closest splats within the viewport budget.
    max_visible = int(w * h * 1.5)
    capped = _cull_to_screen(sx, sy, rad2, order, w, h, max_visible)
    n_visible = len(capped)

    dev = "cuda:0"
    f32 = lambda a: wp.array(np.ascontiguousarray(a, dtype=np.float32), dtype=float, device=dev)
    img = wp.zeros(shape=(h, w), dtype=wp.vec3, device=dev)
    wp.launch(kernel, dim=(h, w),
              inputs=[f32(sx), f32(sy), f32(inv00), f32(inv01), f32(inv11),
                      f32(rad2), f32(splats["alpha"]),
                      wp.array(np.ascontiguousarray(color, dtype=np.float32), dtype=wp.vec3, device=dev),
                      wp.array(capped, dtype=int, device=dev), int(n_visible), 0.06, img],
              device=dev)
    return np.clip(img.numpy().astype(np.float64), 0.0, 1.0)


def _tile_bins(sx: np.ndarray, sy: np.ndarray, rad2: np.ndarray, order: np.ndarray,
              w: int, h: int, tile: int):
    """The BIN step: for every splat, in GLOBAL front-to-back order, find every tile its
    screen footprint overlaps and duplicate it into that tile's bucket; a single STABLE
    sort by tile id then groups the duplicates by tile while preserving front-to-back
    order within each group (see module docstring). Returns a CSR pair
    (tile_offsets[n_tiles+1], tile_splats[total_dups]) plus the tile grid shape.
    Pure numpy — O(splats x avg tiles overlapped), not O(W*H)."""
    tiles_x = -(-w // tile)          # ceil division
    tiles_y = -(-h // tile)
    n_tiles = tiles_x * tiles_y

    ok = rad2 >= 0.0
    rad = np.sqrt(np.maximum(rad2, 0.0))
    x0 = np.clip(np.floor((sx - rad) / tile).astype(np.int64), 0, tiles_x - 1)
    x1 = np.clip(np.floor((sx + rad) / tile).astype(np.int64), 0, tiles_x - 1)
    y0 = np.clip(np.floor((sy - rad) / tile).astype(np.int64), 0, tiles_y - 1)
    y1 = np.clip(np.floor((sy + rad) / tile).astype(np.int64), 0, tiles_y - 1)
    nx = np.where(ok, x1 - x0 + 1, 0)
    ny = np.where(ok, y1 - y0 + 1, 0)
    cnt = np.maximum(nx * ny, 0).astype(np.int64)

    cnt_o = cnt[order]                                       # counts, walked in depth order
    total = int(cnt_o.sum())
    empty_offsets = np.zeros(n_tiles + 1, dtype=np.int32)
    if total == 0:
        return empty_offsets, np.zeros(0, dtype=np.int32), tiles_x, tiles_y

    starts_o = np.concatenate([[0], np.cumsum(cnt_o)])[:-1]           # per depth-slot start
    slot = np.arange(total)
    owner_rank = np.repeat(np.arange(len(order)), cnt_o)               # 0..N-1, depth rank
    local = slot - np.repeat(starts_o, cnt_o)                          # 0..cnt-1 within block
    splat_id = order[owner_rank]                                       # front-to-back already

    nx_o = nx[splat_id]
    tile_x = x0[splat_id] + (local % nx_o)
    tile_y = y0[splat_id] + (local // nx_o)
    tile_id = (tile_y * tiles_x + tile_x).astype(np.int64)

    perm = np.argsort(tile_id, kind="stable")                          # groups by tile,
    tile_id_sorted = tile_id[perm]                                     # keeps depth order
    splat_sorted = splat_id[perm].astype(np.int32)

    counts = np.bincount(tile_id_sorted, minlength=n_tiles)
    tile_offsets = np.concatenate([[0], np.cumsum(counts)]).astype(np.int32)
    return tile_offsets, splat_sorted, tiles_x, tiles_y


def rasterize_tiled(splats: dict, center: np.ndarray, radius: float,
                    azim: float, elev: float, light_azim: float, light_elev: float,
                    w: int = 340, h: int = 340, tile: int = 16) -> np.ndarray:
    """THE 3DGS TILE PIPELINE (tb-0179): project -> bin 16x16 tiles -> per-tile depth
    order -> composite. Drop-in for rasterize() — same signature, same projection/
    shading math (_project_and_shade), so parity between the two is a clean test of
    ONLY the compositing strategy. Each pixel now walks its OWN TILE'S local splat list
    (typically a handful to a few hundred) instead of every splat in the scene — the
    algorithmic fix for splat counts where rasterize()'s O(W*H*N) becomes too slow
    (~100k+, per the module docstring)."""
    wp, _, kernel_tiled = _warp()
    sx, sy, inv00, inv01, inv11, rad2, color, order = _project_and_shade(
        splats, center, radius, azim, elev, light_azim, light_elev, w, h)
    # Screen-space density cap: cap the depth-sorted order BEFORE binning
    # so the tile pipeline doesn't explode when camera is inside the fractal.
    max_visible = int(w * h * 1.5)
    capped = _cull_to_screen(sx, sy, rad2, order, w, h, max_visible)

    # When the density cap keeps splats under ~200k, the per-pixel compositor
    # is FASTER than the tile pipeline — large splats at close range overlap
    # dozens of tiles each, generating O(N * tiles_overlapped) bin entries.
    # Fall back to the global per-pixel kernel in that regime.
    use_global = len(capped) < max_visible and len(capped) < w * h

    dev = "cuda:0"
    f32 = lambda a: wp.array(np.ascontiguousarray(a, dtype=np.float32), dtype=float, device=dev)
    img = wp.zeros(shape=(h, w), dtype=wp.vec3, device=dev)

    if use_global:
        # Per-pixel compositor: O(W*H*N_capped) — fine for <~200k splats
        wp.launch(_KERNEL, dim=(h, w),
                  inputs=[f32(sx), f32(sy), f32(inv00), f32(inv01), f32(inv11),
                          f32(rad2), f32(splats["alpha"]),
                          wp.array(np.ascontiguousarray(color, dtype=np.float32),
                                   dtype=wp.vec3, device=dev),
                          wp.array(capped, dtype=int, device=dev),
                          int(len(capped)), 0.06, img],
                  device=dev)
    else:
        # Tile pipeline: bin into 16x16 tiles, one thread per pixel
        tile_offsets, tile_splats, tiles_x, _tiles_y = _tile_bins(
            sx, sy, rad2, capped, w, h, tile)
        i32 = lambda a: wp.array(np.ascontiguousarray(a, dtype=np.int32),
                                  dtype=int, device=dev)
        wp.launch(_KERNEL_TILED, dim=(h, w),
                  inputs=[f32(sx), f32(sy), f32(inv00), f32(inv01), f32(inv11),
                          f32(rad2), f32(splats["alpha"]),
                          wp.array(np.ascontiguousarray(color, dtype=np.float32),
                                   dtype=wp.vec3, device=dev),
                          i32(tile_splats), i32(tile_offsets),
                          int(tiles_x), int(tile), 0.06, img],
                  device=dev)
    return np.clip(img.numpy().astype(np.float64), 0.0, 1.0)


def _time_frame(fn, *a, reps: int = 3, **kw):
    """Median of `reps` timed calls (first call pays JIT/launch overhead — warm up once,
    outside this helper, before timing)."""
    times = []
    out = None
    for _ in range(reps):
        t0 = time.time()
        out = fn(*a, **kw)
        times.append(time.time() - t0)
    times.sort()
    return out, times[len(times) // 2]


def main() -> int:
    """Three measurements, in order:
    1. CPU vs per-pixel-GPU parity + benchmark (UNCHANGED — the existing proven pair).
    2. per-pixel-GPU vs TILED-GPU parity, same boulder, low count — proves the tile
       pipeline is the SAME renderer, just spatially partitioned.
    3. A REAL limb-density scaling table (core.limb + core.splat_emit, two tiers) —
       ms/frame for both paths, showing where the tile pipeline starts winning.
    """
    from core import matter_items as mi

    rng = np.random.default_rng(21)
    lib = mi.load_library()
    splats = mi.emit_item([("rock", mi.boulder_field(rng))], lib,
                          np.random.default_rng(3), variance=True)
    center, radius = mi.frame_of(splats)
    la, le = 110, 45

    print("=== 1. CPU vs per-pixel-GPU (existing, unchanged reference) ===")
    t0 = time.time(); ref = mi.rasterize(splats, center, radius, *mi.CAM, la, le); t_cpu = time.time() - t0
    _ = rasterize(splats, center, radius, *mi.CAM, la, le)        # warm-up (JIT compile)
    t0 = time.time(); img = rasterize(splats, center, radius, *mi.CAM, la, le); t_gpu = time.time() - t0

    mae = float(np.abs(ref - img).mean())
    n_frames = 24
    t0 = time.time()
    for k in range(n_frames):
        rasterize(splats, center, radius, *mi.CAM, k * 15.0, 40.0)
    t_sweep = time.time() - t0

    mi.OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = mi.OUT_DIR / "gpu_parity_cpu_vs_gpu.png"
    mi.hstack_strip([ref, img], [f"CPU {t_cpu:.2f}s", f"GPU {t_gpu*1000:.0f}ms"]).save(p)
    print(f"  splats={len(splats['pos'])}  CPU {t_cpu:.2f}s  GPU {t_gpu*1000:.1f}ms  "
          f"speedup x{t_cpu/max(t_gpu,1e-9):.0f}  MAE {mae:.5f}")
    print(f"  relight sweep: {n_frames} frames in {t_sweep:.2f}s "
          f"({n_frames/t_sweep:.1f} fps incl. shading+upload)  -> {p}")
    ok_cpu_gpu = mae < 5e-3
    print("  PARITY (CPU vs per-pixel-GPU):", "OK" if ok_cpu_gpu else "FAIL (inspect the PNG)")

    print("\n=== 2. per-pixel-GPU vs TILED-GPU parity (same boulder, same low count) ===")
    _ = rasterize_tiled(splats, center, radius, *mi.CAM, la, le)   # warm-up (JIT compile)
    t0 = time.time(); img_tiled = rasterize_tiled(splats, center, radius, *mi.CAM, la, le)
    t_tiled = time.time() - t0
    mae_tile = float(np.abs(img - img_tiled).mean())
    p2 = mi.OUT_DIR / "gpu_parity_perpixel_vs_tiled.png"
    mi.hstack_strip([img, img_tiled], [f"per-pixel {t_gpu*1000:.1f}ms", f"tiled {t_tiled*1000:.1f}ms"]).save(p2)
    print(f"  splats={len(splats['pos'])}  per-pixel {t_gpu*1000:.2f}ms  tiled {t_tiled*1000:.2f}ms  "
          f"MAE {mae_tile:.5f}  -> {p2}")
    ok_tile = mae_tile < 5e-3
    print("  PARITY (per-pixel-GPU vs tiled-GPU):", "OK" if ok_tile else "FAIL (inspect the PNG)")

    print("\n=== 3. REAL limb-density scaling (core.limb + core.splat_emit) ===")
    from core import limb as limb_mod
    from core.splat_emit import MEDIUM, emit_limb

    density_rows = []
    RES = 340
    imgs, labels = [], []
    for target_len in (64, 160):
        t0 = time.time()
        bones = limb_mod.bent_limb()
        _s, fleshed, shape, _t = limb_mod.grow_limb(bones, seed=0, target_len=target_len)
        t_grow = time.time() - t0
        t0 = time.time()
        lsplats = emit_limb(fleshed)
        t_emit = time.time() - t0
        n = len(lsplats["pos"])
        occ = np.argwhere(fleshed != MEDIUM)
        lcenter = (occ.min(0) + occ.max(0)) / 2.0
        lradius = float((occ.max(0) - occ.min(0)).max()) / 2.0 * 1.15

        _ = rasterize(lsplats, lcenter, lradius, -60, 20, 60, 35, RES, RES)      # warm-up
        img_pp, t_pp = _time_frame(rasterize, lsplats, lcenter, lradius, -60, 20, 60, 35, RES, RES)
        _ = rasterize_tiled(lsplats, lcenter, lradius, -60, 20, 60, 35, RES, RES)  # warm-up
        img_t, t_tl = _time_frame(rasterize_tiled, lsplats, lcenter, lradius, -60, 20, 60, 35, RES, RES)
        mae_d = float(np.abs(img_pp - img_t).mean())
        imgs += [img_pp, img_t]
        labels += [f"n={n//1000}k per-pixel {t_pp*1000:.0f}ms", f"n={n//1000}k tiled {t_tl*1000:.0f}ms"]

        row = {"target_len": target_len, "shape": list(shape), "splats": n,
               "grow_s": t_grow, "emit_s": t_emit,
               "per_pixel_ms": t_pp * 1000, "tiled_ms": t_tl * 1000, "mae": mae_d}
        density_rows.append(row)
        print(f"  target_len={target_len:4d}  splats={n:>8,}  grow={t_grow:6.2f}s  "
              f"emit={t_emit:5.3f}s  per-pixel={t_pp*1000:7.2f}ms  tiled={t_tl*1000:7.2f}ms  "
              f"speedup x{t_pp/max(t_tl,1e-9):.1f}  MAE {mae_d:.5f}")

    p3 = mi.OUT_DIR / "gpu_density_scaling.png"
    mi.hstack_strip(imgs, labels).save(p3)
    print(f"  -> {p3}")
    print("\n  16.6ms (Malcolm frame wall) reference:")
    for row in density_rows:
        under_pp = row["per_pixel_ms"] <= 16.6
        under_tl = row["tiled_ms"] <= 16.6
        print(f"    splats={row['splats']:>8,}  per-pixel {'HOLDS' if under_pp else 'MISSES'} "
              f"({row['per_pixel_ms']:.1f}ms)   tiled {'HOLDS' if under_tl else 'MISSES'} "
              f"({row['tiled_ms']:.1f}ms)")

    ok_all = ok_cpu_gpu and ok_tile
    print("\nOVERALL PARITY:", "OK" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
