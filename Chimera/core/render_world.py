"""render_world — see the grown world. The replacement for the dead UE import step.

`rebuild_world.py` used to end with `import_to_ue5()`, which built a UE Python script as a
string, ran `telemetry_probe`, printed "command written", and executed nothing. That step
never worked, and Unreal is retired regardless.

This renders the emitted splats directly on the GPU — the same soft-Gaussian scatter
rasterizer proven in Construction/gpu_render_torch.py (9 views of 48k splats in 120 ms on
the 4090), made reusable instead of hardcoded to one scan.

    from core.render_world import render_orbit
    render_orbit(splats, out_path='Saved/SplatEmit/world.png', n_views=6)

Rule: the operator must be able to SEE the output. A world that renders to nothing is
indistinguishable from a world that failed to build.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np

# a single key light, slightly above and to the side; enough to read form
_LIGHT_DIR = np.array([0.45, -0.35, 0.82], dtype=np.float32)
_LIGHT_DIR = _LIGHT_DIR / np.linalg.norm(_LIGHT_DIR)
_AMBIENT = 0.35


def _rasterize(means, col, op, cov, nrm, eye, target, up_hint, W, H, sigma, K, dev, torch):
    """Scatter ANISOTROPIC Gaussian footprints for one camera. Normalized accumulation.

    Each splat is projected to a 2D screen-space covariance and scattered as an oriented
    ellipse. The earlier version used one circular kernel for every splat, which meant
    `surface(63%) + cloud(29%) + beam(8%)` rendered identically to `surface(100%)` — the
    entire trained-composition pipeline was invisible at the last step. Splat SHAPE is the
    thing being trained, so the renderer has to draw it.
    """
    fwd = target - eye
    fwd = fwd / (np.linalg.norm(fwd) + 1e-9)
    right = np.cross(fwd, up_hint)
    right = right / (np.linalg.norm(right) + 1e-9)
    down = np.cross(fwd, right)

    R = torch.tensor(np.stack([right, down, fwd], 0), device=dev, dtype=torch.float32)
    et = torch.tensor(eye, device=dev, dtype=torch.float32)

    cam = (means - et) @ R.T
    z = cam[:, 2].clamp(min=1e-3)
    f = 0.5 * H / np.tan(np.deg2rad(30.0))
    x = (cam[:, 0] / z) * f + W * 0.5
    y = (cam[:, 1] / z) * f + H * 0.5

    vis = (z > 0.05) & (x > -K) & (x < W + K) & (y > -K) & (y < H + K)
    if not bool(vis.any()):
        return np.zeros((H, W, 3), dtype=np.uint8)

    xi = x[vis].long()
    yi = y[vis].long()
    c = col[vis]
    a = op[vis]

    # SHADING. The splats carry normals and the renderer was ignoring them, so every
    # surface returned raw albedo and the geometry read as a flat swatch. A Lambert term
    # plus a little ambient is enough to make form legible -- without N.L you cannot see
    # which way anything faces, which defeats the point of training splat ORIENTATION.
    if nrm is not None:
        L = torch.tensor(_LIGHT_DIR, device=dev, dtype=torch.float32)
        ndl = (nrm[vis] @ L).clamp(min=0.0)
        shade = (_AMBIENT + (1.0 - _AMBIENT) * ndl).unsqueeze(1)
        c = c * shade

    if cov is not None:
        # world covariance -> camera -> screen.  Sigma_cam = R Sigma_w R^T, then the 2x2
        # image block scaled by (f/z)^2.  A small isotropic blur keeps thin splats from
        # collapsing below one pixel and makes the inverse well-conditioned.
        Sw = cov[vis]
        Sc = torch.einsum('ij,njk,lk->nil', R, Sw, R)
        s = (f / z[vis]) ** 2
        a11 = Sc[:, 0, 0] * s + sigma ** 2
        a12 = Sc[:, 0, 1] * s
        a22 = Sc[:, 1, 1] * s + sigma ** 2
        det = (a11 * a22 - a12 * a12).clamp(min=1e-9)
        i11, i12, i22 = a22 / det, -a12 / det, a11 / det     # inverse 2x2
    else:
        i11 = i22 = torch.full_like(a, 1.0 / sigma ** 2)
        i12 = torch.zeros_like(a)

    dxo, dyo = torch.meshgrid(torch.arange(-K, K + 1), torch.arange(-K, K + 1), indexing="ij")
    off = torch.stack([dxo.flatten(), dyo.flatten()], 1).to(dev)

    cbuf = torch.zeros(W * H, 3, device=dev)
    wbuf = torch.zeros(W * H, device=dev)
    for k in range(off.shape[0]):
        dx = off[k, 0].float()
        dy = off[k, 1].float()
        # per-splat elliptical weight: exp(-0.5 * d^T Sigma^-1 d)
        gw = torch.exp(-0.5 * (i11 * dx * dx + 2.0 * i12 * dx * dy + i22 * dy * dy))
        px = xi + off[k, 0]
        py = yi + off[k, 1]
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H) & (gw > 1e-4)
        if not bool(ok.any()):
            continue
        idx = (py[ok] * W + px[ok])
        w = a[ok] * gw[ok]
        cbuf.index_add_(0, idx, c[ok] * w[:, None])
        wbuf.index_add_(0, idx, w)

    img = (cbuf / wbuf.clamp(min=1e-8)[:, None]).reshape(H, W, 3)
    return (img.clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)


def render_orbit(splats: dict, out_path='Saved/SplatEmit/world.png', n_views: int = 6,
                 W: int = 512, H: int = 512, sigma: float = 1.2, elev_deg: float = 25.0,
                 max_splats: int = 1_500_000) -> Path:
    """Render N orbit views of a splat cloud and write one montage PNG.

    splats: dict with 'pos' (N,3) and, if present, 'albedo' (N,3) and 'alpha' (N,).
            Anything emitted by core.splat_level / core.splat_emit works directly.
    """
    import torch
    from PIL import Image

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    K = int(np.ceil(3 * sigma))

    # CAMERA-RELATIVE, and the order matters. Positions are read as float64 and the scene
    # centre is subtracted BEFORE any cast to float32. Casting first -- which this did --
    # destroys precision at planet scale: at Earth's radius float32 resolves 0.500 m
    # (measured), so every position jitters by half a metre and geometry z-fights.
    # After subtraction the numbers are small and float32 is exact enough for the GPU.
    pos64 = np.asarray(splats['pos'], dtype=np.float64)
    n = len(pos64)
    if n == 0:
        raise ValueError("no splats to render")
    if n > max_splats:                       # keep the scatter loop bounded
        sel = np.random.default_rng(0).choice(n, max_splats, replace=False)
        pos64 = pos64[sel]
    else:
        sel = np.arange(n)

    world_centre = pos64.mean(0)                          # float64
    pos = (pos64 - world_centre).astype(np.float32)       # camera-relative, then cast

    rgb = np.asarray(splats.get('albedo', np.full((n, 3), 0.7)), dtype=np.float32)[sel]
    opac = np.asarray(splats.get('alpha', np.ones(n)), dtype=np.float32)[sel]

    means = torch.tensor(pos, device=dev)
    col = torch.tensor(np.clip(rgb, 0, 1), device=dev, dtype=torch.float32)
    op = torch.tensor(np.clip(opac, 0, 1), device=dev, dtype=torch.float32)

    cov = splats.get('cov')
    if cov is not None:
        cov = torch.tensor(np.asarray(cov, dtype=np.float32)[sel], device=dev)

    nrm = splats.get('normal')
    if nrm is not None:
        nv = np.asarray(nrm, dtype=np.float32)[sel]
        nv = nv / (np.linalg.norm(nv, axis=1, keepdims=True) + 1e-9)
        nrm = torch.tensor(nv, device=dev)

    ctr = pos.mean(0)          # ~0 by construction: we are already camera-relative
    radius = float(np.linalg.norm(pos - ctr, axis=1).max()) * 2.2 + 1e-3
    up_hint = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    if dev == "cuda":
        torch.cuda.synchronize()
    t0 = time.time()
    frames = []
    for i in range(n_views):
        th = 2 * np.pi * i / n_views
        el = np.deg2rad(elev_deg)
        eye = ctr + radius * np.array([np.cos(th) * np.cos(el),
                                       np.sin(th) * np.cos(el),
                                       np.sin(el)], dtype=np.float32)
        frames.append(_rasterize(means, col, op, cov, nrm, eye.astype(np.float32),
                                 ctr.astype(np.float32), up_hint, W, H, sigma, K, dev, torch))
    if dev == "cuda":
        torch.cuda.synchronize()
    dt = time.time() - t0

    cols = min(3, n_views)
    rows = int(np.ceil(n_views / cols))
    sheet = np.zeros((rows * H, cols * W, 3), dtype=np.uint8)
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * H:(r + 1) * H, c * W:(c + 1) * W] = fr

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sheet).save(out)
    dev_name = torch.cuda.get_device_name(0) if dev == "cuda" else "CPU"
    print(f'  rendered {n_views} views of {len(pos):,} splats in {dt*1000:.0f} ms on {dev_name}')
    print(f'  -> {out}')
    return out
