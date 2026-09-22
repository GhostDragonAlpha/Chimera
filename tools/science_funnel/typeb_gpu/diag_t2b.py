"""diag_t2b.py -- isolate the integ kernel's codegen sink.

Compiles minimal one-call kernels: fk_eval-only, advance-only, and
servo-only (the tick body minus advance), timing each compile separately.
Trailer Agent: GLM 5.3.
"""
import sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
T0 = time.perf_counter()

def say(msg):
    print(f'[{time.perf_counter()-T0:9.2f}s] {msg}', flush=True)

import numpy as np
from numba import cuda
from numba import float64, int32, int64
from walker_model import load_spec
from walker_numba import CF, CI
import walker_numba_split as W
say('split module imported')

spec = load_spec(str(HERE.parent.parent / '.tmp' / 'gait-walker' / 'scene.json'))
from walker_nb_split_env import GaitWalkEnv
env = GaitWalkEnv(spec, 1, reflex_level=0, block=1)
csti = env.d_csti.copy_to_host()
csti[CI['power']] = 0; csti[CI['contact']] = 0; csti[CI['gait_enabled']] = 0
env.d_csti.copy_to_device(csti)
q0 = np.tile(spec.defaults, 1)
env.reset(q0=q0, v0=np.zeros(18), touching0=np.zeros(1, np.int32))
say('env ready')

A = env._args()
(mdl, mdi, dcst, dcsti, a_q, a_v, a_work, a_lt, a_bat, a_batp, a_phi, a_tch,
 a_cap, a_set, a_ikb, a_pawt, a_pawy, a_swf, a_swt, a_ft, a_fst, a_fcy, a_fmo,
 a_fen, a_fcv, a_fdp, a_fcl, a_frp, a_ftd, a_hmo, a_ht, a_hfr, a_hto, a_hpy,
 a_hap, a_hmp, a_hbr, a_hhe, a_hlf, a_hlt2, a_hfi, a_htds, a_hxo, a_hl,
 a_cmdv, a_cmdl, a_cmdf, a_cmdft, a_tk, a_adv, a_ref, a_refc, a_col, rb, rbi) = A


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


@cuda.jit
def k_advance(mdl, mdi, cst, csti, q, v, w, out):
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
    inv = cuda.local.array(324, dtype=float64)
    free = cuda.local.array(18, dtype=float64)
    srq = cuda.local.array(18, dtype=float64)
    srv = cuda.local.array(18, dtype=float64)
    qa = cuda.local.array(18, dtype=float64); va = cuda.local.array(18, dtype=float64)
    qb = cuda.local.array(18, dtype=float64); vb = cuda.local.array(18, dtype=float64)
    qc = cuda.local.array(18, dtype=float64); vc = cuda.local.array(18, dtype=float64)
    qd = cuda.local.array(18, dtype=float64); vd = cuda.local.array(18, dtype=float64)
    qe = cuda.local.array(18, dtype=float64); ve = cuda.local.array(18, dtype=float64)
    we = cuda.local.array(18, dtype=float64)
    sq = cuda.local.array(576, dtype=float64)
    sh16 = cuda.local.array(16, dtype=float64)
    sdep = cuda.local.array(16, dtype=int32)
    scl = cuda.local.array(16, dtype=int32)
    o_q = cuda.local.array(18, dtype=float64)
    o_v = cuda.local.array(18, dtype=float64)
    o_w = cuda.local.array(18, dtype=float64)
    tau = cuda.local.array(18, dtype=float64)
    qq = cuda.local.array(18, dtype=float64)
    vv = cuda.local.array(18, dtype=float64)
    ww = cuda.local.array(18, dtype=float64)
    adv = cuda.local.array(1, dtype=int32)
    rc = cuda.local.array(1, dtype=int32)
    for i in range(18):
        qq[i] = q[i]; vv[i] = v[i]; ww[i] = w[i]; tau[i] = 0.0
    W.advance(qq, vv, ww, tau, cst[W.CF_dt] * float(0.25), mdl, cst, M, gv, bv, fr, frd, frdd,
              axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
              qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl,
              adv, rc, o_q, o_v, o_w, mdi, csti)
    out[0] = o_q[0] + rc[0]


d_q = cuda.to_device(np.zeros(18)); d_v = cuda.to_device(np.zeros(18))
d_w = cuda.to_device(np.zeros(18)); d_tau = cuda.to_device(np.zeros(18))
d_outM = cuda.to_device(np.zeros(2)); d_out = cuda.to_device(np.zeros(2))

say('compiling fk_eval-only kernel')
t = time.perf_counter()
k_fkeval[1, 1](mdl, mdi, dcst, dcsti, d_q, d_v, d_outM, d_outM)
cuda.synchronize()
say(f'fk_eval-only: compile+run {time.perf_counter()-t:.2f}s')

say('compiling advance-only kernel (never-inlined chain)')
t = time.perf_counter()
k_advance[1, 1](mdl, mdi, dcst, dcsti, d_q, d_v, d_w, d_out)
cuda.synchronize()
say(f'advance-only: compile+run {time.perf_counter()-t:.2f}s')

say('T2B DONE')
