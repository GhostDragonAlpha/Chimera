"""bars_fullport.py -- the frozen Phase-A/C falsifiers on the phase-split env.

Measures PREREG_FULLPORT.md's falsifiers against walker_numba_split:
  A  F-FULLPORT-PROBE-PARITY: freefall g vs 9.80665 (|err|<=0.01), stand
     60 ticks vs cpu_stand.txt (<1e-2 scaled max), NaN check.
  C1 F-FULLPORT-CLASS: nominal walk hind fire + fore lift by 150.
  C2 F-FULLPORT-SURVIVAL: N seeds, horizons, pass-100 fraction (>=0.8).
  C3 F-FULLPORT-THROUGHPUT: batch-1024 median eps of 3x300 (>=968), plus 4096.
  C4 F-FULLPORT-MEMORY: VRAM ceiling check.
Writes results JSON to the receipt dir. Trailer Agent: GLM 5.3.
"""
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
T0 = time.perf_counter()

def say(m):
    print(f'[{time.perf_counter()-T0:8.2f}s] {m}', flush=True)

from walker_model import load_spec, T_CYCLE, DUTY_SAMPLED

# --env dll: run the SAME frozen falsifiers on the nvcc-compiled walker_env.dll
# route (walker_env_host.WalkerEnvDLL) instead of the numba split env. The
# falsifier definitions (thresholds, seeds, horizons, scoring) are untouched;
# only the env implementation, the device sync and the VRAM probe swap.
USE_DLL = '--env' in sys.argv
if USE_DLL:
    from walker_env_host import WalkerEnvDLL as GaitWalkEnv

    def dev_sync():
        pass  # WalkerEnvDLL.step syncs the device before returning

    def vram_info():
        import subprocess
        q = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.free',
                            '--format=csv,noheader,nounits'],
                           capture_output=True, text=True).stdout.strip().splitlines()[0]
        used_mib, free_mib = [float(x) for x in q.split(',')]
        return (free_mib * 1048576.0, used_mib * 1048576.0)
else:
    from numba import cuda
    from walker_nb_split_env import GaitWalkEnv

    def dev_sync():
        cuda.synchronize()

    def vram_info():
        return cuda.current_context().get_memory_info()

OUT = HERE.parent / 'validation' / 'typeb_gpu_fullport_20260921'
_pos, _skip = [], False
for _a in sys.argv[1:]:
    if _skip:
        _skip = False
        continue
    if _a == '--env':
        _skip = True
        continue
    if not _a.startswith('--'):
        _pos.append(_a)
BLOCK = int(_pos[0]) if _pos else 32

spec = load_spec(str(HERE.parents[2] / '.tmp' / 'gait-walker' / 'scene.json'))
R = {'block': BLOCK}


def cpu_trace(name):
    rows = []
    for line in (OUT / f'cpu_{name}.txt').read_text().splitlines():
        if line.startswith('tick='):
            d = dict(kv.split('=') for kv in line.split()[1:])
            rows.append([float(d['q3']), float(d['q4']), float(d['v3'])])
    return np.array(rows)


say('== Phase A: probes ==')
env = GaitWalkEnv(spec, 1, reflex_level=0, block=BLOCK)
from walker_numba import CI as _CI
CI_power, CI_contact, CI_gait = _CI['power'], _CI['contact'], _CI['gait_enabled']
csti = env.d_csti.copy_to_host()
csti[CI_power] = 0; csti[CI_contact] = 0; csti[CI_gait] = 0
env.d_csti.copy_to_device(csti)
q0 = np.tile(spec.defaults, 1)
env.reset(q0=q0, v0=np.zeros(18), touching0=np.zeros(1, np.int32))
ys = []
t0 = time.perf_counter()
for t in range(100):
    env.step(1, readback=True)
    ys.append(env.rb.copy_to_host().reshape(1, 6)[0, 1])
say(f'freefall 100 ticks in {time.perf_counter()-t0:.2f}s')
ys = np.array(ys)
h = 1.0 / 300.0
accs = [(-ys[i+2] + 16*ys[i+1] - 30*ys[i] + 16*ys[i-1] - ys[i-2]) / (12*h*h)
        for i in range(2, len(ys)-2)]
g = float(np.mean(accs))
R['freefall'] = {'measured_g': g, 'err': abs(g - 9.80665),
                 'drop': float(ys[0] - ys[-1]),
                 'parity_pass': bool(abs(g - 9.80665) <= 0.01)}
say(f"freefall g={g:.6f} err={abs(g-9.80665):.2e} pass={R['freefall']['parity_pass']}")

csti = env.d_csti.copy_to_host()
csti[CI_power] = 1; csti[CI_contact] = 1; csti[CI_gait] = 0
env.d_csti.copy_to_device(csti)
env.reset()
trace = []
for t in range(60):
    env.step(1, readback=True)
    rb = env.rb.copy_to_host().reshape(1, 6)[0]
    trace.append([rb[0], rb[1], rb[2]])
st = np.array(trace)
cpu = cpu_trace('stand')
n = min(len(st), len(cpu))
diff = float(np.max(np.abs(st[:n] - cpu[:n]) / (1.0 + np.abs(cpu[:n])))) if n else None
R['stand'] = {'gpu_ticks': len(st), 'cpu_ticks': len(cpu), 'max_scaled_diff': diff,
              'parity_pass': bool(diff is not None and diff < 1e-2)}
say(f"stand max_scaled_diff={diff:.3e} pass={R['stand']['parity_pass']}")

say('== Phase C1: nominal class ==')
env1 = GaitWalkEnv(spec, 1, reflex_level=1, block=BLOCK)
csti = env1.d_csti.copy_to_host()
csti[_CI['reflex_level']] = 1
env1.d_csti.copy_to_device(csti)
env1.reset()
hind_fires = fore_lifts = 0
horizon, refused_class = 600, None
t0 = time.perf_counter()
for t in range(600):
    env1.step(1, readback=False)
    stt = env1.status()
    rbi = stt['rbi'][0]
    hind_fires = int(rbi[0] + rbi[1])
    fore_lifts = int(rbi[2] + rbi[3])
    if stt['refused'][0] or stt['collapsed'][0]:
        refused_class = int(stt['refused_class'][0]) if stt['refused'][0] else 9
        horizon = int(stt['ticks'][0])
        break
say(f'nominal walk {time.perf_counter()-t0:.1f}s: horizon={horizon} class={refused_class} hind={hind_fires} fore={fore_lifts}')
R['nominal'] = {'horizon': horizon, 'refused_class': refused_class,
                'hind_fires': hind_fires, 'fore_lifts': fore_lifts,
                'class_pass': bool(horizon < 600 or refused_class is not None)}

say('== Phase C2: survival ==')
N = 64
env64 = GaitWalkEnv(spec, N, reflex_level=1, block=BLOCK)
q_base, v_base, _ = spec.reset_state()
q0 = np.tile(q_base, N); v0 = np.tile(v_base, N)
for s in range(N):
    rng = np.random.Generator(np.random.PCG64(s))
    q = q0[s*18:(s+1)*18]; v = v0[s*18:(s+1)*18]
    for d in range(12):
        c = spec.drive_coord[d]
        q[c] += rng.uniform(-1, 1) * 1e-3
        v[c] += rng.uniform(-1, 1) * 1e-2
    v[3] *= (1.0 + rng.uniform(-1, 1) * 0.02)
env64.reset(q0=q0, v0=v0, touching0=np.zeros(N, np.int32))
horizons = np.full(N, 600, np.int64); classes = np.full(N, -1, np.int32)
alive = np.ones(N, bool)
t0 = time.perf_counter()
for t in range(600):
    env64.step(1, readback=False)
    stt = env64.status()
    ref = stt['refused']; col = stt['collapsed']; tk = stt['ticks']
    newly = np.where(alive & ((ref != 0) | (col != 0)))[0]
    for i in newly:
        horizons[i] = tk[i]
        classes[i] = int(stt['refused_class'][i]) if ref[i] else 9
        alive[i] = False
    if not alive.any():
        break
dt_surv = time.perf_counter() - t0
pass100 = int((horizons >= 100).sum())
R['survival'] = {'seeds': N, 'horizons': horizons.tolist(), 'classes': classes.tolist(),
                 'pass_100': pass100, 'median': float(np.median(horizons)),
                 'pass': bool(pass100 >= 0.8 * N), 'wall_s': dt_surv}
say(f"survival: pass_100={pass100}/{N} median={R['survival']['median']} wall={dt_surv:.1f}s pass={R['survival']['pass']}")

say('== Phase C3/C4: throughput + memory ==')
mem0 = vram_info()
tp = []
for B in (1024, 4096):
    envB = GaitWalkEnv(spec, B, reflex_level=1, block=BLOCK)
    envB.reset()
    envB.step(30); dev_sync()
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        envB.step(300)
        dev_sync()
        times.append(time.perf_counter() - t0)
    med = sorted(times)[1]
    stt = envB.status()
    eps = B * 300 / med
    tp.append({'batch': B, 'median_s': med, 'env_steps_per_s': eps,
               'ms_per_tick': med / 300 * 1e3, 'refused': int(stt['refused'].sum()),
               'collapsed': int(stt['collapsed'].sum())})
    say(f"batch {B}: {eps:.0f} eps ({tp[-1]['ms_per_tick']:.2f} ms/tick)")
    del envB
mem1 = vram_info()
R['throughput'] = tp
R['throughput_pass_1024'] = bool(tp[0]['env_steps_per_s'] >= 968)
R['memory'] = {'free_gb': mem1[0] / 1e9, 'used_gb': mem1[1] / 1e9,
               'marginal_mb_per_env': (mem1[1] - mem0[1]) / 1e6 / 4096}

OUT.mkdir(parents=True, exist_ok=True)
(OUT / f'bars_split_b{BLOCK}.json').write_text(json.dumps(R, indent=1))
say('BARS DONE -> ' + str(OUT / f'bars_split_b{BLOCK}.json'))
