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
  For MILLIONS of terrain splats the known upgrade is the 3DGS tile-binning pipeline
  (project -> bin -> per-tile sort -> composite) — stated here so nobody mistakes this
  rung for that one. Not built until rung C's grain counts demand it.
- float32 on the GPU vs float64 on the CPU: parity is asserted at ~1e-3 MAE, not 0.0.

Drop-in: rasterize(...) has the exact signature/semantics of matter_items.rasterize.
Benchmark + parity proof: python -m core.splat_gpu
"""

from __future__ import annotations

import math
import time

import numpy as np

from core.splat_emit import AMBIENT, _camera_frame, _dir_from_azel

_WP = None
_KERNEL = None


def _warp():
    """Lazy init so importing this module never costs anything on CPU-only boxes."""
    global _WP, _KERNEL
    if _WP is not None:
        return _WP, _KERNEL
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

    _WP, _KERNEL = wp, composite
    return _WP, _KERNEL


def available() -> bool:
    try:
        _warp()
        return True
    except Exception:
        return False


def rasterize(splats: dict, center: np.ndarray, radius: float,
              azim: float, elev: float, light_azim: float, light_elev: float,
              w: int = 340, h: int = 340) -> np.ndarray:
    """GPU twin of matter_items.rasterize — identical projection + shading math
    (numpy), compositing in one Warp kernel."""
    wp, kernel = _warp()

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
    dev = "cuda:0"
    f32 = lambda a: wp.array(np.ascontiguousarray(a, dtype=np.float32), dtype=float, device=dev)
    img = wp.zeros(shape=(h, w), dtype=wp.vec3, device=dev)
    wp.launch(kernel, dim=(h, w),
              inputs=[f32(sx), f32(sy), f32(inv00), f32(inv01), f32(inv11),
                      f32(rad2), f32(splats["alpha"]),
                      wp.array(np.ascontiguousarray(color, dtype=np.float32), dtype=wp.vec3, device=dev),
                      wp.array(order, dtype=int, device=dev), int(len(order)), 0.06, img],
              device=dev)
    return np.clip(img.numpy().astype(np.float64), 0.0, 1.0)


def main() -> int:
    """Parity + benchmark: same boulder, CPU vs GPU, numbers + a side-by-side PNG."""
    from core import matter_items as mi

    rng = np.random.default_rng(21)
    lib = mi.load_library()
    splats = mi.emit_item([("rock", mi.boulder_field(rng))], lib,
                          np.random.default_rng(3), variance=True)
    center, radius = mi.frame_of(splats)
    la, le = 110, 45

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
    print(f"splats={len(splats['pos'])}  CPU {t_cpu:.2f}s  GPU {t_gpu*1000:.1f}ms  "
          f"speedup x{t_cpu/max(t_gpu,1e-9):.0f}  MAE {mae:.5f}")
    print(f"relight sweep: {n_frames} frames in {t_sweep:.2f}s "
          f"({n_frames/t_sweep:.1f} fps incl. shading+upload)  -> {p}")
    ok = mae < 5e-3
    print("PARITY:", "OK" if ok else "FAIL (inspect the PNG)")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
