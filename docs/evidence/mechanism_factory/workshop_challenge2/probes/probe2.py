import json, shutil, socket, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, 'tools/construction_packet')
sys.path.insert(0, 'tools')
import workshop_challenge2 as wc2
import workshop_challenge1 as wc1

EXE = wc1.EXE
native = HERE / 'native'
if native.exists():
    shutil.rmtree(native)
native.mkdir()
shutil.copy2(EXE, native / EXE.name)
shutil.copytree(EXE.parent / 'shaders', native / 'shaders', dirs_exist_ok=True)
with socket.socket() as s:
    assert s.connect_ex(('127.0.0.1', 8813)) != 0, 'port busy'
proc = subprocess.Popen([str(native / EXE.name), '8813',
                         str(HERE.resolve() / 'board.json'), '800', '600',
                         '--no-restore'], cwd=native)
eng = wc1.Engine(8813)
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

def trial(name, support_doc, support_id, crate_bottom, yawed):
    eng.post('/tick_b2_clear')
    r = eng.post('/tick_b2_admit', wc1.scene_doc())
    assert r.get('ok')
    r = eng.post('/tick_b2_place', support_doc)
    assert r.get('ok'), (name, r)
    r = eng.post('/tick_b2_place', wc1.crate_doc(chain='tower',
                                                 bottom_y=crate_bottom))
    assert r.get('ok'), (name, r)
    s0 = st()
    c0 = part(s0, 'crate')['com_m'][1]
    sup0 = part(s0, support_id)['com_m'][1]
    eng.post('/tick_b2_pause', {'on': False})
    rows = []
    for i in range(10):
        time.sleep(0.05)
        s = st()
        rows.append(round(part(s, 'crate')['com_m'][1], 4))
    eng.post('/tick_b2_pause', {'on': True})
    held = rows[-1] > sup0 + 0.05   # crate still on top of the support?
    print(f'{name}: crate com paused={c0:.4f} trace={rows} -> '
          f'{"HELD" if held else "FELL THROUGH"}')

pad_top0 = wc1.PAD['h'] - wc1.RS
# A) yawed pier (analytic full-chain spawn on the pad), crate at the
#    challenge-1 6.71 mm depth instead of the 2.37 mm pair sink
pier_bottom = (pad_top0 - wc2.M_PIER * wc1.G / wc1.KT_PAD
               - wc2.M_PIER * wc1.G / wc1._pair_kt(wc1.KT_PIER, wc1.KT_PAD))
pier_top = pier_bottom + wc1.PIER['h']
trial('A yawed-pier crate@6.71mm', wc2.pier_yawed_doc(pier_bottom),
      'pier_rec', pier_top - 0.00671, True)
# B) challenge-1 pillar (analytic spawn), crate at a SHALLOW 2.37 mm depth
pil_bot = wc1.pillar_spawn_bottom()
pil_top = pil_bot + wc1.PILLAR['h']
trial('B pillar crate@2.37mm ', wc1.pillar_doc(), 'pillar',
      pil_top - 0.00237, False)
# C) control: pillar + crate at the proven 6.71 mm pair sink
trial('C pillar crate@6.71mm ', wc1.pillar_doc(), 'pillar',
      pil_top - wc1.M_CRATE * wc1.G / wc1._pair_kt(wc1.KT_CRATE, wc1.KT_PILLAR),
      False)
proc.terminate()
try:
    proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    proc.kill()
