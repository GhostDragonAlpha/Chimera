"""diag_freefall.py -- raw-state freefall diagnostic on the DLL route.

freefall csti (power=0, contact=0, gait=0), q0=defaults, v0=0, touching0=0,
step 5 ticks one at a time, and dump env-0 q/v/rc/adv/refused/ticks per tick
via env_dbg_read. Decides between: advance never called (adv_calls),
advance refusing (rc), gravity not applied (v[4] never negative), or the
writeback not running (q/v bit-identical to reset). Trailer: Agent: GLM 5.3.
"""
import sys
import numpy as np
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from walker_model import load_spec
from walker_env_host import WalkerEnvDLL
from walker_numba import CI

spec = load_spec(str(HERE.parents[2] / '.tmp' / 'gait-walker' / 'scene.json'))
env = WalkerEnvDLL(spec, 1, reflex_level=0, block=32)
csti = env.d_csti.copy_to_host()
csti[CI['power']] = 0
csti[CI['contact']] = 0
csti[CI['gait_enabled']] = 0
env.d_csti.copy_to_device(csti)
env.reset(q0=spec.defaults, v0=np.zeros(18), touching0=np.zeros(1, np.int32))


def dbg():
    q = np.zeros(18)
    v = np.zeros(18)
    rc = np.zeros(1, np.int32)
    adv = np.zeros(1, np.int32)
    ref = np.zeros(1, np.int32)
    tk = np.zeros(1, np.int64)
    from walker_env_host import _dll, _dp, _ip, _lp
    import ctypes
    ok = _dll.env_dbg_read(ctypes.c_void_p(env._h), _dp(q), _dp(v), _ip(rc),
                           _ip(adv), _ip(ref), _lp(tk))
    assert ok
    return q, v, rc[0], adv[0], ref[0], tk[0]


q0, v0, rc, adv, ref, tk = dbg()
print(f"reset: q[3]={q0[3]:.9f} q[4]={q0[4]:.9f} v[3]={v0[3]:.9f} v[4]={v0[4]:.9f} rc={rc} adv={adv}")
for t in range(1, 101):
    env.step(1)
    q, v, rc, adv, ref, tk = dbg()
    if t > 12 and t % 10 != 0 and rc == 0 and ref == 0:
        continue
    print(f"tick {tk}: q[3]={q[3]:.12f} q[4]={q[4]:.12f} v[3]={v[3]:.12f} "
          f"v[4]={v[4]:.12f} rc={rc} adv={adv} refused={ref}")
print("expected: v[4] decreases by ~9.80665/300 per tick; q[4] drops; "
      "rc=0; adv grows")
