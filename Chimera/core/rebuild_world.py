"""rebuild_world — ONE COMMAND to regenerate the entire game from training.

Runs the full pipeline:
1. GPU terrain growth (Cellular Potts at 256^3)
2. Matter shelter growth (differential adhesion)
3. Splat emission for all elements
4. GLB export
5. MCP import into UE5
6. Level save

Usage:
    python -m core.rebuild_world           # full rebuild
    python -m core.rebuild_world --terrain  # terrain only
    python -m core.rebuild_world --shelter  # shelter only
"""

from __future__ import annotations

import asyncio
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'Saved' / 'SplatEmit'


def grow_terrain() -> Path:
    """Grow terrain via GPU Cellular Potts. Returns GLB path."""
    from core.matter_gpu import assemble_3d_gpu
    from core.matter import BONE, SKIN, J_PROVEN_DIFFERENTIAL
    from core.splat_types import emit_surface
    from core.splat_to_ue5 import write_splat_glb
    
    N = 256
    shape = (N, N, N)
    rng = np.random.RandomState(42)
    grid = np.zeros(shape, dtype=np.int16)
    grid[:, :, 0] = BONE
    
    # mgrid is CONSTANT — building it inside the loop allocated 3 x 256^3 int arrays 300
    # times over (~50 GB of churn) for a grid that never changes. Hoisted.
    zz, yy, xx = np.mgrid[0:N, 0:N, 0:N]
    above = zz > 0
    for _ in range(300):
        cx, cy, cz, r = rng.randint(5,N-5), rng.randint(5,N-5), rng.randint(1,35), rng.randint(4,30)
        blob = (xx-cx)**2 + (yy-cy)**2 + (zz-cz)**2 < r*r
        grid[blob & above] = SKIN
    
    targets = {t: int((grid==t).sum()) for t in (BONE, SKIN)}
    print(f'  Growing terrain 256^3...', end=' ', flush=True)
    t0 = time.time()
    result = assemble_3d_gpu(grid, shape, targets, J_PROVEN_DIFFERENTIAL, sweeps=25, seed=42, frozen_type=BONE)
    print(f'{time.time()-t0:.2f}s')
    
    # THE SURFACE IS THE TOP OF THE MATTER, NOT THE BOTTOM.
    # This was `np.argmax(result==SKIN, axis=2)`, which returns the FIRST (lowest) SKIN
    # voxel in each column, and 0 for any column containing no SKIN at all. Since the seed
    # blobs are sparse, most columns had none, defaulted to 0, and rendered as one flat
    # sheet with the few tall blobs floating above it, disconnected. Verified by looking at
    # the render. Take the highest SKIN instead, and emit nothing where there is no matter.
    is_skin = (result == SKIN)
    has_skin = is_skin.any(axis=2)
    heights = (N - 1) - np.argmax(is_skin[:, :, ::-1], axis=2)   # topmost SKIN per column

    ws = 2000.0/N
    xs = np.linspace(-1000,1000,N); ys = np.linspace(-1000,1000,N)
    xx, yy = np.meshgrid(xs, ys)
    zz = heights.astype(float)*ws - 50
    pos = np.stack([xx.ravel(),yy.ravel(),zz.ravel()], axis=1)
    norm = np.zeros((len(pos),3)); norm[:,2] = 1.0
    ok = has_skin.ravel()                       # no matter in this column -> no ground
    pos = pos[ok]; norm = norm[ok]
    print(f'  surface: {ok.sum():,} of {N*N:,} columns carry matter '
          f'({100*ok.mean():.0f}% coverage), height range '
          f'{zz.ravel()[ok].min():.0f}..{zz.ravel()[ok].max():.0f}')
    sp = 2000.0/N

    # Emit through the material's TRAINED splat composition rather than a bare
    # emit_surface. Before the composition link was closed this made no difference --
    # every material fell back to surface-only -- but now sand/rock carry trained
    # layer mixes and measured materials (cluster_*) can be used directly.
    from core.splat_level import _get_optical, _get_composition
    from core.splat_types import emit_fiber, emit_point, emit_shell, emit_beam, emit_cloud, emit_glow
    _EMIT = {'surface': lambda nrm, s: emit_surface(nrm, tangent_scale=sp*1.5*s, normal_scale=sp*0.5*s),
             'fiber':   lambda nrm, s: emit_fiber(nrm, tangent_scale=sp*1.5*s, normal_scale=sp*0.5*s,
                                                  fiber_dir=np.roll(nrm, 1, axis=1)),
             'point':   lambda nrm, s: emit_point(np.zeros_like(nrm), radius=sp*s),
             'shell':   lambda nrm, s: emit_shell(np.zeros_like(nrm), nrm, thickness=sp*0.2*s, spread=sp*s),
             'beam':    lambda nrm, s: emit_beam(nrm, length=sp*3.0*s, thickness=sp*0.3*s),
             'cloud':   lambda nrm, s: emit_cloud(np.zeros_like(nrm), radius=sp*2.0*s, alpha=0.1),
             'glow':    lambda nrm, s: emit_glow(np.zeros_like(nrm), radius=sp*s)}

    def _cov_for(material, nrm, seed=0):
        """Blend the material's trained layers across its splats, by weight."""
        layers = _get_composition(material)
        tot = sum(l['weight'] for l in layers) or 1.0
        pick = np.random.RandomState(seed).choice(
            len(layers), size=len(nrm), p=[l['weight']/tot for l in layers])
        out = np.zeros((len(nrm), 3, 3))
        for li, layer in enumerate(layers):
            sel = pick == li
            if not sel.any():
                continue
            fn = _EMIT.get(layer['type'], _EMIT['surface'])
            out[sel] = fn(nrm[sel], float(layer.get('scale', 1.0)))
        return out, layers

    mats = np.random.RandomState(0).choice(['sand','rock','ground'], size=len(pos), p=[0.5,0.25,0.25])
    all_s = []
    for m in np.unique(mats):
        mask = mats == m
        pt = pos[mask]
        opt = _get_optical(m)
        cov_m, layers = _cov_for(m, norm[mask])
        desc = ' + '.join(f"{l['type']}({l['weight']:.0%})" for l in layers)
        print(f'    {m:8} {int(mask.sum()):>7,} splats  [{desc}]')
        splat = {
            'pos': pt.astype(np.float64),
            'normal': norm[mask].astype(np.float64),
            'cov': cov_m.astype(np.float64),
            'albedo': np.tile(opt['albedo'], (len(pt), 1)).astype(np.float64),
            'roughness': np.full(len(pt), opt['roughness'], dtype=np.float64),
            'alpha': np.full(len(pt), opt['alpha'], dtype=np.float64),
            'subsurface': np.full(len(pt), opt['subsurface'], dtype=np.float64),
            'metallic': np.full(len(pt), opt.get('metallic', 0.0), dtype=np.float64),
        }
        all_s.append(splat)
    
    world = {k: np.concatenate([s[k] for s in all_s],axis=0) for k in all_s[0]}
    print(f'  {len(world["pos"]):,} splats')
    
    glb = OUT_DIR / 'terrain.glb'
    write_splat_glb(world, scale=1.0, path=glb, soft_edge=False)
    print(f'  GLB: {glb}')
    return glb, world


def grow_shelter() -> Path:
    """Grow shelter via Matter differential adhesion. Returns GLB path."""
    from core.matter import assemble_3d, init_limb_3d, J_DIFFERENTIAL_3D
    from core.splat_emit import emit_limb
    from core.splat_to_ue5 import write_splat_glb
    
    print(f'  Growing shelter...', end=' ', flush=True)
    t0 = time.time()
    g0, shape, targets = init_limb_3d(length=20, radius=40, cap=8, seed=42)
    diff = assemble_3d(g0, shape, targets, J_DIFFERENTIAL_3D, sweeps=40, seed=42)
    splats = emit_limb(diff)
    print(f'{time.time()-t0:.2f}s, {len(splats["pos"]):,} splats')
    
    glb = OUT_DIR / 'shelter.glb'
    write_splat_glb(splats, scale=1.0, path=glb, soft_edge=False)
    print(f'  GLB: {glb}')
    return glb, splats


def show(splats, label, n_views=6):
    """Render the grown splats so the operator can SEE them.

    Replaces import_to_ue5(), which built a UE Python script as a string, ran
    telemetry_probe, printed "command written", and executed nothing — it never worked,
    and Unreal is retired regardless. This rasterizes on the GPU instead.
    """
    from core.render_world import render_orbit
    out = OUT_DIR / f'{label.lower()}.png'
    try:
        return render_orbit(splats, out_path=out, n_views=n_views)
    except Exception as exc:                      # a render failure must not lose the build
        print(f'  render failed for {label}: {exc}')
        return None


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Rebuild entire game from training')
    ap.add_argument('--terrain', action='store_true', help='Terrain only')
    ap.add_argument('--shelter', action='store_true', help='Shelter only')
    args = ap.parse_args()
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print('=== REBUILD WORLD ===')
    
    rendered = []
    if args.terrain or not (args.terrain or args.shelter):
        glb, world = grow_terrain()
        p = show(world, 'Terrain')
        if p: rendered.append(p)

    if args.shelter or not (args.terrain or args.shelter):
        glb, splats = grow_shelter()
        p = show(splats, 'Shelter')
        if p: rendered.append(p)

    print('=== REBUILD COMPLETE ===')
    for p in rendered:
        print(f'  SEE IT: {p}')


if __name__ == '__main__':
    main()
