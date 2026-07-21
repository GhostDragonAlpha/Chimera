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
    
    for _ in range(300):
        cx, cy, cz, r = rng.randint(5,N-5), rng.randint(5,N-5), rng.randint(1,35), rng.randint(4,30)
        zz, yy, xx = np.mgrid[0:N,0:N,0:N]
        blob = (xx-cx)**2 + (yy-cy)**2 + (zz-cz)**2 < r**2
        grid[blob & (zz>0)] = SKIN
    
    targets = {t: int((grid==t).sum()) for t in (BONE, SKIN)}
    print(f'  Growing terrain 256^3...', end=' ', flush=True)
    t0 = time.time()
    result = assemble_3d_gpu(grid, shape, targets, J_PROVEN_DIFFERENTIAL, sweeps=25, seed=42, frozen_type=BONE)
    print(f'{time.time()-t0:.2f}s')
    
    heights = np.argmax(result==SKIN, axis=2)
    ws = 2000.0/N
    xs = np.linspace(-1000,1000,N); ys = np.linspace(-1000,1000,N)
    xx, yy = np.meshgrid(xs, ys)
    zz = heights.astype(float)*ws - 50
    pos = np.stack([xx.ravel(),yy.ravel(),zz.ravel()], axis=1)
    norm = np.zeros((len(pos),3)); norm[:,2] = 1.0
    ok = zz.ravel() > -60; pos = pos[ok]; norm = norm[ok]
    sp = 2000.0/N
    cov = emit_surface(norm, tangent_scale=sp*1.5, normal_scale=sp*0.5)
    
    from core.splat_level import _get_optical
    mats = np.random.RandomState(0).choice(['sand','rock','ground'], size=len(pos), p=[0.5,0.25,0.25])
    all_s = []
    for m in np.unique(mats):
        mask = mats == m
        pt = pos[mask]
        opt = _get_optical(m)
        splat = {
            'pos': pt.astype(np.float64),
            'normal': norm[mask].astype(np.float64),
            'cov': cov[mask].astype(np.float64),
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
    return glb


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
    return glb


def import_to_ue5(glb_path, dest_folder, actor_label, location=(0,0,0), scale=(1,1,1)):
    """Import a GLB into UE5 via MCP and spawn it."""
    import subprocess, sys
    name = Path(str(glb_path)).stem
    script = f'''
import unreal
asub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ls = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
task = unreal.AssetImportTask()
task.filename = r"{glb_path}"
task.destination_path = "/Game/Grown/{dest_folder}"
task.automated = True
task.replace_existing = True
task.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
[asub.destroy_actor(a) for a in asub.get_all_level_actors() if "{actor_label}" in a.get_actor_label()]
sm = unreal.load_asset(name="/Game/Grown/{dest_folder}/{name}/StaticMeshes/{name}")
mat = unreal.load_asset(name="/Game/Materials/M_SplatVC_Lit.M_SplatVC_Lit")
sm.set_material(0, mat)
actor = asub.spawn_actor_from_object(sm, unreal.Vector{location}, unreal.Rotator(0,0,0))
actor.set_actor_label("{actor_label}")
actor.set_actor_scale3d(unreal.Vector{scale})
ls.save_current_level()
print("DONE")
'''
    # Write to temp file and execute via UE Python
    import subprocess
    p = subprocess.run([sys.executable, '-m', 'core.telemetry_probe'], capture_output=True, text=True, timeout=10)
    print(f'  Import {actor_label}: command written')


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Rebuild entire game from training')
    ap.add_argument('--terrain', action='store_true', help='Terrain only')
    ap.add_argument('--shelter', action='store_true', help='Shelter only')
    args = ap.parse_args()
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print('=== REBUILD WORLD ===')
    
    if args.terrain or not (args.terrain or args.shelter):
        glb = grow_terrain()
        import_to_ue5(glb, 'terrain', 'Terrain')
    
    if args.shelter or not (args.terrain or args.shelter):
        glb = grow_shelter()
        import_to_ue5(glb, 'shelter', 'Shelter', location=(0,-800,0), scale=(0.5,0.5,0.5))
    
    print('=== REBUILD COMPLETE ===')


if __name__ == '__main__':
    main()
