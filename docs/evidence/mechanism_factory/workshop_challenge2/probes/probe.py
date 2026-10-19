import json, shutil, socket, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, 'tools/construction_packet')
sys.path.insert(0, 'tools')
import workshop_challenge2 as wc2
import workshop_challenge1 as wc1

EXE = wc1.EXE
out = HERE
native = out / 'native'
if native.exists():
    shutil.rmtree(native)
native.mkdir()
shutil.copy2(EXE, native / EXE.name)
shutil.copytree(EXE.parent / 'shaders', native / 'shaders', dirs_exist_ok=True)
with socket.socket() as s:
    assert s.connect_ex(('127.0.0.1', 8812)) != 0, 'port busy'
proc = subprocess.Popen([str(native / EXE.name), '8812',
                         str(out.resolve() / 'board.json'), '800', '600',
                         '--no-restore'], cwd=native)
eng = wc1.Engine(8812)
for _ in range(120):
    try:
        eng.get('/tick_state'); break
    except Exception:
        time.sleep(0.25)

def st():
    return eng.get('/tick_b2_state')
def part(s, pid):
    return next(p for p in s['parts'] if p['id'] == pid)
def settle(t=20.0, v=5e-4):
    t0 = time.time()
    while time.time() - t0 < t:
        s = st()
        if all(p['speed_m_s'] < v for p in s['parts']):
            time.sleep(0.3)
            return st()
        time.sleep(0.05)
    return st()

eng.post('/tick_b2_admit', wc1.scene_doc())
eng.post('/tick_b2_pause', {'on': True})
# pier: full-chain analytic spawn directly on the analytic pad (build-style)
pad_top0 = wc1.PAD['h'] - wc1.RS
pier_bottom = (pad_top0 - wc2.M_PIER * wc1.G / wc1.KT_PAD
               - wc2.M_PIER * wc1.G / wc1._pair_kt(wc1.KT_PIER, wc1.KT_PAD))
r = eng.post('/tick_b2_place', wc2.pier_yawed_doc(pier_bottom))
print('pier place:', r)
# crate onto the SPAWNED pier at pair sink (build-style, analytic)
pier_top_spawn = pier_bottom + wc1.PIER['h']
sink = wc1.M_CRATE * wc1.G / wc1._pair_kt(wc1.KT_CRATE, wc1.KT_PIER)
r = eng.post('/tick_b2_place', wc1.crate_doc(chain='tower',
                                             bottom_y=pier_top_spawn - sink))
print('crate place:', r)
s0 = st()
print('paused crate com:', part(s0, 'crate')['com_m'])
print('paused pier  com:', part(s0, 'pier_rec')['com_m'])
eng.post('/tick_b2_pause', {'on': False})
for i in range(24):
    time.sleep(0.05)
    s = st()
    c = part(s, 'crate')['com_m']
    p = part(s, 'pier_rec')['com_m']
    print(f'  t+{(i+1)*0.05:.2f}s crate_y={c[1]:.4f} pier_y={p[1]:.4f} '
          f'crate_react={part(s, "crate")["reaction_n"]:.2f}')
eng.post('/tick_b2_pause', {'on': True})
proc.terminate()
try:
    proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    proc.kill()
