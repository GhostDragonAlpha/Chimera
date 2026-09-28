"""bars_one.py -- run the pinned bars_fullport battery against one DLL.

Usage: python -B bars_one.py <dll_path> <tag>
Mirrors co8_bars_v2.py's pinned invocation (--env dll 32); results JSON lands
in typeb_run/tools/science_funnel/validation/typeb_gpu_fullport_20260921/
bars_split_b32_<tag>.json via a post-run rename.
Agent: arrival-db26712d6a264e4899c951f55b074d80
"""
import ctypes
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "typeb_run" / "tools" / "science_funnel" / "typeb_gpu"
sys.path.insert(0, str(RUN))
import walker_env_host as weh
from walker_env_host import WalkerEnvDLL

DLL = Path(sys.argv[1])
TAG = sys.argv[2]

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

src = RUN.parents[0] / "validation" / "typeb_gpu_fullport_20260921" / "bars_split_b32.json"
dst = src.with_name(f"bars_split_b32_{TAG}.json")
shutil.move(str(src), str(dst))
print("BARS", TAG, "->", dst)
