"""co8_dev41.py -- the tick-41 device drill driver (closeout-8): the d41 DLL
with the drill windows at 41, E=1, reflex_level=1, block=32. Device printf
comes on stdout; FULL dumps pair with the host walk. Trailer: Agent: GLM 5.3."""
import ctypes
import numpy as np
import walker_env_host as weh
from walker_env_host import WalkerEnvDLL, load_spec, _dp, _ip, _lp

_dll = ctypes.CDLL(str(weh.HERE / "walker_env_d41.dll"))
_dll.env_create.restype = ctypes.c_void_p
_dll.env_create.argtypes = [
    ctypes.c_int, ctypes.c_int,
    ctypes.POINTER(ctypes.c_double), ctypes.c_int,
    ctypes.POINTER(ctypes.c_int), ctypes.c_int,
    ctypes.POINTER(ctypes.c_double), ctypes.c_int,
    ctypes.POINTER(ctypes.c_int), ctypes.c_int,
    ctypes.POINTER(ctypes.c_double), ctypes.c_int,
    ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_double]
_dll.env_reset.restype = ctypes.c_int
_dll.env_reset.argtypes = [ctypes.c_void_p,
                           ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
                           ctypes.POINTER(ctypes.c_int)]
_dll.env_set_command.restype = ctypes.c_int
_dll.env_set_command.argtypes = [ctypes.c_void_p, ctypes.c_double]
_dll.env_step.restype = ctypes.c_int
_dll.env_step.argtypes = [ctypes.c_void_p, ctypes.c_int]
_dll.env_sync.restype = ctypes.c_int
_dll.env_sync.argtypes = [ctypes.c_void_p]
_dll.env_dbg_read.restype = ctypes.c_int
_dll.env_dbg_read.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 6
weh._dll = _dll

spec = load_spec()
env = WalkerEnvDLL(spec, 1, reflex_level=1, block=32)
env.reset()
q18 = np.zeros(18, np.float64); v18 = np.zeros(18, np.float64)
rc = np.zeros(1, np.int32); adv = np.zeros(1, np.int32); ref = np.zeros(1, np.int32); tk = np.zeros(1, np.int64)
for t in range(1, 44):
    env.step(1)
    dll = weh._dll
    dll.env_dbg_read(ctypes.c_void_p(env._h), _dp(q18), _dp(v18), _ip(rc), _ip(adv), _ip(ref), _lp(tk))
    print('FULL t=%d' % t + ''.join(' q%d=%.17g' % (i, q18[i]) for i in range(18))
          + ''.join(' v%d=%.17g' % (i, v18[i]) for i in range(18)), flush=True)
    if rc[0] != 0 or ref[0] != 0:
        print('REFUSED at tick %d rc=%d refused=%d adv=%d ticks=%d' % (t, rc[0], ref[0], adv[0], tk[0]))
        break
