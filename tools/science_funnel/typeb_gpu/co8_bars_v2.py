"""co8_bars.py -- closeout-8: run bars_fullport against walker_env_v2.dll
(the post-hold-port production build; the main walker_env.dll name is locked
by a concurrent lane at run time -- swapped in after). Trailer: Agent: GLM 5.3.
"""
import ctypes
import sys
import walker_env_host as weh

_dll = ctypes.CDLL(str(weh.HERE / "walker_env_v2.dll"))
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
_dll.env_status.restype = ctypes.c_int
_dll.env_status.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 10
_dll.env_dbg_read.restype = ctypes.c_int
_dll.env_dbg_read.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 6
_dll.env_read_xoff.restype = ctypes.c_int
_dll.env_read_xoff.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_dll.env_csti_get.restype = ctypes.c_int
_dll.env_csti_get.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_dll.env_csti_set.restype = ctypes.c_int
_dll.env_csti_set.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
weh._dll = _dll

sys.argv = ["bars_fullport.py", "--env", "dll", "32"]
import bars_fullport  # noqa: E402  (runs the frozen falsifiers)
