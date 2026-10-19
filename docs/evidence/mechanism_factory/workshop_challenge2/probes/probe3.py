import shutil, socket, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, 'tools/construction_packet')
sys.path.insert(0, 'tools')
import workshop_challenge2 as wc2
import workshop_challenge1 as wc1
import b2_scene_gen

EXE = wc1.EXE
native = HERE / 'native'
if native.exists():
    shutil.rmtree(native)
native.mkdir()
shutil.copy2(EXE, native / EXE.name)
shutil.copytree(EXE.parent / 'shaders', native / 'shaders', dirs_exist_ok=True)
with socket.socket() as s:
    assert s.connect_ex(('127.0.0.1', 8814)) != 0, 'port busy'
proc = subprocess.Popen([str(native / EXE.name), '8814',
                         str(HERE.resolve() / 'board.json'), '800', '600',
                         '--no-restore'], cwd=native)
eng = wc1.Engine(8814)
for _ in range(120):
    try:
        eng.get('/tick_state'); break
    except Exception:
        time.sleep(0.25)

def st():
    return eng.get('/tick_b2_state')
def part(s, pid):
    return next(p for p in s['parts'] if p['id'] == pid)

eng.post('/tick_b2_admit', wc1.scene_doc())

def pillar_yawed_doc(cx):
    """The kit pillar (square 120x120 footprint) YAWED 90 deg -- identical
    footprint, only pose_q and the local vertex order differ."""
    dx, h, dz = wc1.PILLAR['dx'], wc1.PILLAR['h'], wc1.PILLAR['dz']
    y0 = wc1.pillar_spawn_bottom()
    vs = [(-dx/2, -h/2, -dz/2), (dx/2, -h/2, -dz/2),
          (dx/2, -h/2, dz/2), (-dx/2, -h/2, dz/2),
          (-dx/2, h/2, -dz/2), (dx/2, h/2, -dz/2),
          (dx/2, h/2, dz/2), (-dx/2, h/2, dz/2)]
    ixx = wc1.M_PILLAR / 12 * (h*h + dz*dz)
    iyy = wc1.M_PILLAR / 12 * (dx*dx + dz*dz)
    izz = wc1.M_PILLAR / 12 * (dx*dx + h*h)
    k, c = b2_scene_gen.rung_constants(wc1.M_PILLAR, 4)
    return {"id": "pillar_y", "mass_kg": wc1.M_PILLAR,
            "com_local_m": [0.0]*3,
            "inertia_com_local_kg_m2": [ixx,0,0,0,iyy,0,0,0,izz],
            "vertices_local_m": [x for v in vs for x in v],
            "boundary_triangles": [i for f in b2_scene_gen.BOX_FACES for i in f],
            "pose_c_m": [cx, y0 + h/2, 0.0],
            "pose_q_wxyz": list(wc2.PIER_YAW_Q),
            "ground": {"k_n_per_m": k, "c_n_s_per_m": c},
            "mu": wc1.PILLAR['mu']}

pil_bot = wc1.pillar_spawn_bottom()
pil_top = pil_bot + wc1.PILLAR['h']
sink = wc1.M_CRATE * wc1.G / wc1._pair_kt(wc1.KT_CRATE, wc1.KT_PILLAR)
for name, sup in (('D pillar YAWED (square) ', pillar_yawed_doc(0.62)),
                  ('E pillar UNROTATED     ', wc1.pillar_doc())):
    eng.post('/tick_b2_clear')
    r = eng.post('/tick_b2_admit', wc1.scene_doc()); assert r.get('ok')
    r = eng.post('/tick_b2_place', sup); assert r.get('ok')
    r = eng.post('/tick_b2_place', wc1.crate_doc(chain='tower',
                                                 bottom_y=pil_top - sink))
    assert r.get('ok')
    s0 = st()
    sup_id = 'pillar_y' if 'pillar_y' in [p['id'] for p in s0['parts']] else 'pillar'
    sup0 = part(s0, sup_id)['com_m'][1]
    eng.post('/tick_b2_pause', {'on': False})
    rows = []
    for i in range(10):
        time.sleep(0.05)
        rows.append(round(part(st(), 'crate')['com_m'][1], 4))
    eng.post('/tick_b2_pause', {'on': True})
    print(f'{name}: sup_y0={sup0:.4f} crate {rows} -> '
          + ('HELD' if rows[-1] > sup0 + 0.05 else 'FELL THROUGH'))
proc.terminate()
try:
    proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    proc.kill()
