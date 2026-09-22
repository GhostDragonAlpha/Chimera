"""diag_t1.py -- T1 of PREREG_DIAG.md: the compile-vs-execution discriminator.

Stage A: build env at E (default 1), configure freefall (power=0/contact=0/
gait_enabled=0, reflex 0), launch tick_kernel ONCE. Print timestamps at
launch-call return and at device completion. If the launch call itself
blocks the host for >HOST_BLOCK_S, print HOST-BLOCKED so the parent's
sampler attributes CPU vs SM activity.
Stage B (only if tick-0 returns): relaunch the SAME kernel in the SAME
process and time it -- <1 s = compile cost (H1 fired), slow = execution.
Stage C: dump the PTX and census the .local bytes/thread (H2 evidence).

Trailer Agent: GLM 5.3.
"""
import sys, time, threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

E = int(sys.argv[1]) if len(sys.argv) > 1 else 1
BLOCK = int(sys.argv[2]) if len(sys.argv) > 2 else 1
CONFIG = sys.argv[3] if len(sys.argv) > 3 else 'freefall'
TICKS = int(sys.argv[4]) if len(sys.argv) > 4 else 1

T0 = time.perf_counter()

def say(msg):
    print(f'[{time.perf_counter()-T0:9.2f}s] {msg}', flush=True)

say(f'start E={E} block={BLOCK} config={CONFIG} ticks={TICKS}')

import numpy as np
say('numpy imported')
from numba import cuda
say('numba.cuda imported')
from walker_model import load_spec
from walker_numba import CF, CI
from walker_nb_env import GaitWalkEnv
say('walker modules imported')

spec = load_spec(str(HERE.parent.parent / '.tmp' / 'gait-walker' / 'scene.json'))
env = GaitWalkEnv(spec, E, reflex_level=0)
say('env built')

if CONFIG == 'freefall':
    # the run_fullport.probe_freefall configuration
    csti = env.d_csti.copy_to_host()
    csti[CI['power']] = 0
    csti[CI['contact']] = 0
    csti[CI['gait_enabled']] = 0
    env.d_csti.copy_to_device(csti)
    q0 = np.tile(spec.defaults, E)
    env.reset(q0=q0, v0=np.zeros(E * 18), touching0=np.zeros(E, np.int32))
elif CONFIG == 'walk':
    env.reset()
say(f'config set ({CONFIG}); reset returned+synced')

grid = (E + BLOCK - 1) // BLOCK

# ---- Stage A: the first launch, timed at the three boundaries ----
say(f'FIRST LAUNCH entering (grid={grid} x block={BLOCK})')
t_launch0 = time.perf_counter()
done = threading.Event()

def launch():
    for k in range(TICKS):
        tick_kernel_call()

def tick_kernel_call():
    from walker_numba_gen import tick_kernel
    tick_kernel[grid, BLOCK](
        env.d_mdl, env.d_mdi, env.d_cst, env.d_csti,
        env.a_q, env.a_v, env.a_work, env.a_last_torque,
        env.a_battery, env.a_battery_post, env.a_phi, env.a_touching,
        env.a_captured, env.a_settle, env.a_ik_branch, env.a_paw_target,
        env.a_paw_plant_y, env.a_swing_from, env.a_swing_to,
        env.a_fore_t, env.a_fore_stance, env.a_fore_cycle, env.a_fore_mode,
        env.a_fore_entry, env.a_fore_conv, env.a_fore_td_plant,
        env.a_fore_clamped, env.a_fore_replants, env.a_fore_td_count,
        env.a_hind_mode, env.a_hind_t, env.a_hind_from, env.a_hind_to,
        env.a_hind_plant_y, env.a_hind_ap, env.a_hind_mp, env.a_hind_branch,
        env.a_hind_held, env.a_hind_last_fire, env.a_hind_last_td,
        env.a_hind_fires, env.a_hind_tds, env.a_hind_xoff,
        env.a_height_latched, env.a_cmd_vx, env.a_cmd_live,
        env.a_cmd_first_tick, env.a_cmd_fires, env.a_ticks, env.a_adv_calls,
        env.a_refused, env.a_refused_class, env.a_collapsed, env.rb, env.rbi)

th = threading.Thread(target=launch, daemon=True)
th.start()
th.join(timeout=90.0)
if th.is_alive():
    say('HOST-BLOCKED >90s in the launch call itself (compile suspected; parent must sample CPU/SM now)')
    th.join()
say(f'FIRST LAUNCH CALL RETURNED t={time.perf_counter()-t_launch0:.2f}s after call entry (enqueue done; compile done if it ever blocked)')

t_sync0 = time.perf_counter()
cuda.synchronize()
say(f'TICK-0 DEVICE COMPLETE t={time.perf_counter()-t_sync0:.2f}s after sync start')

# ---- Stage B: second launch, same process ----
t2 = time.perf_counter()
tick_kernel_call()
cuda.synchronize()
dt2 = time.perf_counter() - t2
say(f'SECOND LAUNCH+SYNC t={dt2:.3f}s  -> ' + ('COMPILE-COST CONFIRMED (H1)' if dt2 < 1.0 else 'EXECUTION SLOW TOO (H2/H3 alive)'))

# ---- Stage C: PTX local census ----
try:
    from walker_numba_gen import tick_kernel
    sig = tick_kernel.signatures[-1]
    ptx = tick_kernel.inspect_asm(sig)
    ptx_path = HERE.parent / 'validation' / 'typeb_gpu_fullport_20260921' / 'tick_ptx.ptx'
    ptx_path.write_text(ptx)
    import re
    local_bytes = 0
    n_local_arrays = 0
    for m in re.finditer(r'\.local\s+\.align\s+\d+\s+\.b8\s+\S+\[(\d+)\]', ptx):
        local_bytes += int(m.group(1)); n_local_arrays += 1
    say(f'PTX dumped ({len(ptx)} chars) -> {ptx_path.name}; .local arrays={n_local_arrays} bytes/thread={local_bytes}')
except Exception as ex:
    say(f'PTX census failed: {type(ex).__name__}: {ex}')

say('T1 DONE')
