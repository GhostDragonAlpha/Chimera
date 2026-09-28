"""dev_replay.py -- G3 fresh device tie-v2 replay, pinned co8_dev41.py protocol.

Drives walker_env_v2 (original registry-hash binary OR sergeant rebuild) for
43 ticks, E=1, reflex_level=1, block=32, printing FULL q/v state lines t=1..43
with %.17g -- the exact pinned format. Agent: arrival-db26712d6a264e4899c951f55b074d80
"""
import ctypes
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
RUN = HERE / "typeb_run" / "tools" / "science_funnel" / "typeb_gpu"
sys.path.insert(0, str(RUN))
import walker_env_host as weh
from walker_env_host import WalkerEnvDLL, load_spec, _dp, _ip, _lp

DLL = Path(sys.argv[1])
OUT = Path(sys.argv[2])

_dll = ctypes.CDLL(str(DLL))
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
lines = []
for t in range(1, 44):
    env.step(1)
    dll = weh._dll
    dll.env_dbg_read(ctypes.c_void_p(env._h), _dp(q18), _dp(v18), _ip(rc), _ip(adv), _ip(ref), _lp(tk))
    lines.append('FULL t=%d' % t + ''.join(' q%d=%.17g' % (i, q18[i]) for i in range(18))
                 + ''.join(' v%d=%.17g' % (i, v18[i]) for i in range(18)))
    if rc[0] != 0 or ref[0] != 0:
        lines.append('REFUSED at tick %d rc=%d refused=%d adv=%d ticks=%d' % (t, rc[0], ref[0], adv[0], tk[0]))
        break
OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print('wrote', OUT, len(lines), 'lines; dll=', DLL.name)
