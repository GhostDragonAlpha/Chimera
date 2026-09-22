"""diag_dll_walk.py -- step the DLL env (E=1, nominal config) tick by tick,
dumping FULL q/v lines in the same format as host_loop/cp_probe dumps so the
three implementations (C++ reference, host replay, GPU DLL) can be diffed.
Trailer Agent: GLM 5.3.
"""
import ctypes
import sys
import numpy as np
import walker_env_host as weh
from walker_env_host import WalkerEnvDLL, load_spec, _dp, _ip, _lp

TICKS = int(sys.argv[1]) if len(sys.argv) > 1 else 60

dll = weh._dll

spec = load_spec()
env = WalkerEnvDLL(spec, 1, reflex_level=1, block=32)
env.reset()

q18 = np.zeros(18, np.float64)
v18 = np.zeros(18, np.float64)
rc = np.zeros(1, np.int32)
adv = np.zeros(1, np.int32)
ref = np.zeros(1, np.int32)
tk = np.zeros(1, np.int64)

for t in range(1, TICKS + 1):
    env.step(1)
    dll.env_dbg_read(ctypes.c_void_p(env._h), _dp(q18), _dp(v18),
                     _ip(rc), _ip(adv), _ip(ref), _lp(tk))
    print('FULL t=%d' % t + ''.join(' q%d=%.17g' % (i, q18[i]) for i in range(18))
          + ''.join(' v%d=%.17g' % (i, v18[i]) for i in range(18)), flush=True)
    if rc[0] != 0 or ref[0] != 0:
        print('REFUSED at tick %d rc=%d refused=%d adv=%d ticks=%d' % (t, rc[0], ref[0], adv[0], tk[0]))
        break
