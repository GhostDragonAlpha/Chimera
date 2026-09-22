"""diag_t2c.py -- verify inline='never' actually emits a call (not inlined).

Compiles the fk_eval-only kernel (3s class), dumps its LLVM IR, greps for
`call` instructions into fk_eval vs an inlined body. Also dumps the
advance-caller IR if the advance-only kernel ever lands (skipped here).
Trailer Agent: GLM 5.3.
"""
import sys, time, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
T0 = time.perf_counter()

def say(m):
    print(f'[{time.perf_counter()-T0:7.2f}s] {m}', flush=True)

import numpy as np
from numba import cuda, float64, int32, int64
from walker_model import load_spec
from walker_numba import CF, CI
import walker_numba_split as W
say('module imported')

spec = load_spec(str(HERE.parent.parent / '.tmp' / 'gait-walker' / 'scene.json'))
from walker_nb_split_env import GaitWalkEnv
env = GaitWalkEnv(spec, 1, reflex_level=0, block=1)
csti = env.d_csti.copy_to_host()
csti[CI['power']] = 0; csti[CI['contact']] = 0; csti[CI['gait_enabled']] = 0
env.d_csti.copy_to_device(csti)
env.reset(q0=np.tile(spec.defaults, 1), v0=np.zeros(18), touching0=np.zeros(1, np.int32))
say('env ready')

mdl, mdi, dcst, dcsti = env.d_mdl, env.d_mdi, env.d_cst, env.d_csti
d_q = cuda.to_device(np.zeros(18)); d_v = cuda.to_device(np.zeros(18))
d_outM = cuda.to_device(np.zeros(2))


@cuda.jit
def k_fkeval(mdl, mdi, cst, csti, q, v, outM, outPTP):
    M = cuda.local.array(324, dtype=float64)
    gv = cuda.local.array(18, dtype=float64)
    bv = cuda.local.array(18, dtype=float64)
    fr = cuda.local.array(224, dtype=float64)
    frd = cuda.local.array(224, dtype=float64)
    frdd = cuda.local.array(224, dtype=float64)
    axw = cuda.local.array(54, dtype=float64)
    axpiv = cuda.local.array(54, dtype=float64)
    axdir = cuda.local.array(54, dtype=float64)
    ptp = cuda.local.array(24, dtype=float64)
    ptJ = cuda.local.array(216, dtype=float64)
    ptcop = cuda.local.array(12, dtype=float64)
    ptbias = cuda.local.array(12, dtype=float64)
    qq = cuda.local.array(18, dtype=float64)
    vv = cuda.local.array(18, dtype=float64)
    for i in range(18):
        qq[i] = q[i]
        vv[i] = v[i]
    pot = W.fk_eval(qq, vv, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
    outM[0] = pot
    outPTP[0] = ptp[0]


t = time.perf_counter()
k_fkeval[1, 1](mdl, mdi, dcst, dcsti, d_q, d_v, d_outM, d_outM)
cuda.synchronize()
say(f'fk_eval-only compile+run {time.perf_counter()-t:.2f}s')

llvm = k_fkeval.inspect_asm(k_fkeval.signatures[-1])
calls = re.findall(r'call\s+[^@\n]*@([\w.]+)\(', llvm)
from collections import Counter
cnt = Counter(calls)
say(f'LLVM {len(llvm)} chars; call targets: {dict(cnt)}')
say(f"contains fk_eval call: {'fk_eval' in cnt}")
