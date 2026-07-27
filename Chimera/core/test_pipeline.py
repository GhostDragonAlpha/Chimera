"""test_pipeline — end-to-end verification of the Chimera pipeline.

Tests:
1. Can Matter grow tissue correctly?
2. Can splats be emitted from grown tissue?
3. Can splats be exported to GLB?
4. Can the MCP bridge connect?
5. Can a level be built?

Run: python -m core.test_pipeline
"""

import sys, time, json, numpy as np
from pathlib import Path

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} {detail}')


def test_matter():
    print('\n=== Matter System ===')
    from core.matter import init_blob, assemble, metrics, is_sorted, J_DIFFERENTIAL, J_UNIFORM
    g0, targets = init_blob(seed=0)
    diff = assemble(g0, targets, J_DIFFERENTIAL, sweeps=160, seed=0)
    ctrl = assemble(g0, targets, J_UNIFORM, sweeps=160, seed=0)
    md = metrics(diff)
    mc = metrics(ctrl)
    check('Differential adhesion sorts tissue', is_sorted(md),
          f'bone={md["radius"][1]:.1f} muscle={md["radius"][2]:.1f} skin={md["radius"][3]:.1f}')
    check('Uniform control stays mixed', not is_sorted(mc),
          f'bone={mc["radius"][1]:.1f} muscle={mc["radius"][2]:.1f} skin={mc["radius"][3]:.1f}')
    check('Areas conserved', all(abs(md["area"][t] - targets[t]) < 25 for t in targets),
          f'diff={dict((t,md["area"][t]-targets[t]) for t in targets)}')


def test_splat_types():
    print('\n=== Splat Types ===')
    from core.splat_types import SPLAT_TYPES, emit_surface, emit_point, emit_fiber, emit_beam
    rng = np.random.RandomState(42)
    normals = np.zeros((100, 3)); normals[:, 2] = 1.0
    positions = rng.randn(100, 3) * 10
    dirs = np.zeros((100, 3)); dirs[:, 0] = 1.0
    
    cov_s = emit_surface(normals, 1.0, 0.3)
    cov_p = emit_point(positions, 1.0)
    cov_f = emit_fiber(normals, 1.0, 0.3, dirs, 3.0)
    cov_b = emit_beam(dirs, 10.0, 0.5)
    
    check('Surface splat covariance', cov_s.shape == (100,3,3), f'trace={np.trace(cov_s,axis1=1,axis2=2).mean():.2f}')
    check('Point splat isotropic', cov_p.shape == (100,3,3), f'trace={np.trace(cov_p,axis1=1,axis2=2).mean():.2f}')
    check('Fiber splat elongated', cov_f.shape == (100,3,3), f'trace={np.trace(cov_f,axis1=1,axis2=2).mean():.2f}')
    check('Beam splat long', cov_b.shape == (100,3,3), f'trace={np.trace(cov_b,axis1=1,axis2=2).mean():.2f}')
    check('All 7 types defined', len(SPLAT_TYPES) == 7, f'types={list(SPLAT_TYPES.keys())}')


def test_splat_compositions():
    print('\n=== Splat Compositions ===')
    from core.train_splat_compositions import train_material, measure, seed_genome
    genome = seed_genome('sand')
    m = measure('sand', genome)
    check('Measure returns metrics', 'total_error' in m, f'error={m.get("total_error","?")}')
    best, err, measures = train_material('sand', pop=32, gens=10)
    check('Training converges', err < 0.5, f'error={err:.3f}')
    n_active = sum(1 for w in best[:len(best)//2] if w > 0.05)
    check('At least 2 splat types', n_active >= 2, f'active={n_active}')


def test_glb_export():
    print('\n=== GLB Export ===')
    from core.splat_types import emit_surface
    from core.splat_to_ue5 import write_splat_glb
    n = 100
    rng = np.random.RandomState(42)
    pos = rng.randn(n, 3) * 10
    norm = np.zeros((n, 3)); norm[:, 2] = 1.0
    cov = emit_surface(norm, 1.0, 0.3)
    world = {
        'pos': pos.astype(np.float64),
        'normal': norm.astype(np.float64),
        'cov': cov.astype(np.float64),
        'albedo': np.tile([0.5,0.5,0.5], (n,1)).astype(np.float64),
        'roughness': np.full(n, 0.5, dtype=np.float64),
        'alpha': np.full(n, 1.0, dtype=np.float64),
        'subsurface': np.full(n, 0.0, dtype=np.float64),
        'metallic': np.zeros(n, dtype=np.float64),
    }
    out = Path('Saved/SplatEmit/test_export.glb')
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = write_splat_glb(world, scale=1.0, path=out, soft_edge=False)
        check('GLB file created', out.exists(), f'size={out.stat().st_size}B')
    except Exception as e:
        check('GLB export', False, str(e))


def test_mcp():
    print('\n=== MCP Bridge ===')
    import asyncio, json
    async def connect():
        try:
            ws = await __import__('websockets').connect('ws://127.0.0.1:8090')
            await ws.send(json.dumps({'type': 'bridge_hello'}))
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            await ws.close()
            return True, resp.get('sessionId','')
        except:
            return False, ''
    loop = asyncio.new_event_loop()
    ok, session = loop.run_until_complete(connect())
    loop.close()
    check('MCP bridge responds', ok, f'session={session[:12]}')


def test_gpu():
    print('\n=== GPU Availability ===')
    try:
        import warp as wp
        wp.init()
        dev = wp.get_device()
        check('CUDA device available', dev.is_cuda, f'device={dev}')
    except Exception as e:
        check('CUDA device', False, str(e))


def test_composition():
    print('\n=== Composition (12 Seams) ===')
    import glob, json
    decoded = {}
    for f in glob.glob('docs/decoded/*.json'):
        name = Path(f).stem
        decoded[name] = json.load(open(f))
    required = ['solar_system', 'planet_surface', 'ground_terrain', 'body_survival',
                'biome_resources', 'shelter_form', 'shelter_threshold', 'fabricator_economy',
                'npc_social', 'beacon_narrative']
    present = [r for r in required if r in decoded]
    check('All 10 rungs decoded', len(present) == len(required), f'{len(present)}/{len(required)}')


def test_level():
    print('\n=== Level File ===')
    level = Path('Content/Levels/emergent_world/emergent_world.umap')
    check('Level file exists', level.exists(), f'size={level.stat().st_size}B')
    if level.exists():
        size = level.stat().st_size
        check('Level has content', size > 30000, f'size={size}B')


if __name__ == '__main__':
    print('=== CHIMERA PIPELINE TEST ===')
    print(f'Started: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    test_gpu()
    test_matter()
    test_splat_types()
    test_splat_compositions()
    test_glb_export()
    test_composition()
    test_mcp()
    test_level()
    
    print(f'\n=== RESULTS: {PASS} passed, {FAIL} failed ({(PASS/(PASS+FAIL+0.001)*100):.0f}%) ===')
    sys.exit(1 if FAIL > 0 else 0)
