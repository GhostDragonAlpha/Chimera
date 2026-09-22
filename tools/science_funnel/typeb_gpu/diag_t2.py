"""diag_t2.py -- T2 of PREREG_DIAG.md: the split kernels' compile + run census.

Stage 1: E=1 freefall (power=0/contact=0/gait=0), block=1: first-launch and
second-launch times per split kernel (compile vs exec separated), plus tick
counters readback.
Stage 2: PTX .local byte census per kernel (H2 evidence).
Stage 3: walk config (contact=1/power=1/gait=1), E=1: 120 ticks timed, the
tick counters + body y + fires read back (first behavior numbers).
Stage 4: the block ladder at batch (E in {1024, 4096} x block in {1, 32,
128}): 10 timed ticks each, env-steps/s reported (first throughput numbers).

Trailer Agent: GLM 5.3.
"""
import sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

T0 = time.perf_counter()

def say(msg):
    print(f'[{time.perf_counter()-T0:9.2f}s] {msg}', flush=True)

say(f'start argv={sys.argv[1:]}')
STAGES = sys.argv[1].split(',') if len(sys.argv) > 1 else ['1', '2', '3', '4']

import numpy as np
from numba import cuda
from walker_model import load_spec
from walker_numba import CF, CI
say('imports done')

spec = load_spec(str(HERE.parent.parent / '.tmp' / 'gait-walker' / 'scene.json'))
from walker_nb_split_env import GaitWalkEnv
from walker_numba_split import tick_plan_kernel, tick_integ_kernel, tick_post_kernel
say('split module imported (no compile yet -- lazy)')


def freefall(env):
    csti = env.d_csti.copy_to_host()
    csti[CI['power']] = 0; csti[CI['contact']] = 0; csti[CI['gait_enabled']] = 0
    env.d_csti.copy_to_device(csti)
    q0 = np.tile(spec.defaults, env.E)
    env.reset(q0=q0, v0=np.zeros(env.E * 18), touching0=np.zeros(env.E, np.int32))


def walkcfg(env):
    env.reset()


KERN = [('plan', tick_plan_kernel), ('integ', tick_integ_kernel), ('post', tick_post_kernel)]

if '1' in STAGES:
    env = GaitWalkEnv(spec, 1, reflex_level=0, block=1)
    freefall(env)
    say('E=1 freefall env ready')
    for name, k in KERN:
        t = time.perf_counter(); k[1, 1](*env._args(), env.a_rc); t_enqueue = time.perf_counter() - t
        t = time.perf_counter(); cuda.synchronize(); t_exec = time.perf_counter() - t
        t = time.perf_counter(); k[1, 1](*env._args(), env.a_rc); cuda.synchronize(); t2 = time.perf_counter() - t
        say(f'{name}: first-call(enqueue incl compile)={t_enqueue:.2f}s device-sync={t_exec:.3f}s second-call+sync={t2:.4f}s')
    st = env.status()
    say(f'after 2 ticks: ticks={st["ticks"][0]} refused={st["refused"][0]} collapsed={st["collapsed"][0]} rb={st["rb"][0]}')

if '2' in STAGES:
    import re
    for name, k in KERN:
        if not k.signatures:
            continue
        ptx = k.inspect_asm(k.signatures[-1])
        local_bytes = sum(int(m.group(1)) for m in re.finditer(r'\.local\s+\.align\s+\d+\s+\.b8\s+\S+\[(\d+)\]', ptx))
        regs = re.search(r'\.reg.*?%r<(\d+)', ptx)
        say(f'{name}: PTX {len(ptx)} chars, .local bytes/thread={local_bytes}')

if '3' in STAGES:
    env = GaitWalkEnv(spec, 1, reflex_level=1, block=1)
    walkcfg(env)
    say('E=1 walk env ready (compile paid on first step below)')
    t = time.perf_counter()
    env.step(1)
    cuda.synchronize()
    say(f'walk tick-0 (compile incl): {time.perf_counter()-t:.2f}s')
    t = time.perf_counter()
    for _ in range(120):
        env.step(1)
    cuda.synchronize()
    dt = time.perf_counter() - t
    st = env.status()
    say(f'walk 120 ticks: {dt:.3f}s ({dt/120*1e3:.2f} ms/tick) ticks={st["ticks"][0]} refused={st["refused"][0]}/{st["refused_class"][0]} collapsed={st["collapsed"][0]} rb(y={st["rb"][0][1]:.4f}) hind_fires={st["hind_tds"][0]} fore_td={st["fore_td_count"][0]}')

if '4' in STAGES:
    for E in (1024, 4096):
        for B in (1, 32, 128):
            try:
                env = GaitWalkEnv(spec, E, reflex_level=1, block=B)
                walkcfg(env)
                env.step(2); cuda.synchronize()
                t = time.perf_counter()
                env.step(10)
                cuda.synchronize()
                dt = time.perf_counter() - t
                st = env.status()
                say(f'ladder E={E} block={B}: {dt/10*1e3:.2f} ms/tick, {E*10/dt:.0f} env-steps/s, ticks={st["ticks"][0]} refused={int(st["refused"].sum())} collapsed={int(st["collapsed"].sum())}')
                del env
            except Exception as ex:
                say(f'ladder E={E} block={B}: FAILED {type(ex).__name__}: {ex}')

say('T2 DONE')
