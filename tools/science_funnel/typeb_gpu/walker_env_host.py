"""walker_env_host.py -- ctypes host for walker_env.dll (the nvcc-compiled
phase-split walk environment).

Mirrors walker_nb_split_env.py's GaitWalkEnv semantics exactly: same cst/csti
setup, same reset touching computation, same set_command, same per-tick
plan -> integ -> post launches with a_rc carrying the verdict. The difference:
the kernels run from walker_kernels.cuh compiled by nvcc (no JIT), loaded as a
DLL. Trailer: Agent: GLM 5.3.
"""
import ctypes
import math
import time
import numpy as np
from pathlib import Path

from walker_model import (WalkerSpec, T_CYCLE, DUTY_SAMPLED, K_TOUCH, ZETA, FS_HZ,
                          NB, NDRIVE, FOLD_BUDGET_TICKS, UNLOAD_TICKS, SINK_RATE_MAX)
from walker_numba import OF, OI, CF, CI, NI32
from walker_nb_env import build_model_arrays

HERE = Path(__file__).parent
ROOT = HERE.parent.parent.parent  # repo root (typeb_gpu -> science_funnel -> tools -> root)
SCENE = ROOT / ".tmp" / "gait-walker" / "scene.json"

_u32 = ctypes.c_uint32
_dll = ctypes.CDLL(str(HERE / "walker_env.dll"))
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
_dll.env_csti_get.restype = ctypes.c_int
_dll.env_csti_get.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
_dll.env_csti_set.restype = ctypes.c_int
_dll.env_csti_set.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
_dll.env_read_xoff.restype = ctypes.c_int
_dll.env_read_xoff.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
_dll.env_dbg_read.restype = ctypes.c_int
_dll.env_dbg_read.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 6
_dll.env_free.argtypes = [ctypes.c_void_p]


def _dp(a):
    return a.ctypes.data_as(ctypes.POINTER(ctypes.c_double))


def _ip(a):
    return a.ctypes.data_as(ctypes.POINTER(ctypes.c_int))


def _lp(a):
    return a.ctypes.data_as(ctypes.POINTER(ctypes.c_longlong))


def build_env_arrays(spec: WalkerSpec, reflex_level: int = 1, collapse_y: float = 0.20):
    """The single source of truth for the env's device-config arrays.

    Returns (mdl, mdi, cst, csti, store_floor) exactly as env_create consumes
    them. walker_env_host.WalkerEnvDLL and dump_shim.py both call this so the
    host replay harness can never drift from the DLL's config again.
    """
    mdl, mdi = build_model_arrays(spec)
    assert mdl.shape[0] == 900 and mdi.shape[0] == NI32, (mdl.shape, mdi.shape, NI32)
    dt = spec.dt
    height_floor = 2.0 * SINK_RATE_MAX + SINK_RATE_MAX * (1.0 / (ZETA * 2.0 * math.pi * FS_HZ)) / dt
    cst = np.zeros(30, np.float64)
    cst[CF['plane_y']] = spec.plane_model_y
    cst[CF['gy']] = 9.80665
    cst[CF['dt']] = dt
    cst[CF['mu']] = spec.mu
    cst[CF['k_touch']] = K_TOUCH
    cst[CF['k_slip']] = 1e-9
    cst[CF['k_release']] = 1e-6
    cst[CF['t_cycle']] = T_CYCLE
    cst[CF['duty']] = DUTY_SAMPLED
    cst[CF['toe_off']] = 0.68
    cst[CF['capture_phi']] = 0.95
    cst[CF['kp_post']] = spec.kp_post
    cst[CF['kd_post']] = spec.kd_post
    cst[CF['store_post']] = spec.store_post
    cst[CF['height_crit']] = spec.height_crit
    cst[CF['height_floor']] = spec.height_floor
    cst[CF['fore_L1']] = spec.fore_L1
    cst[CF['fore_rho']] = spec.fore_rho
    cst[CF['fore_beta']] = spec.fore_beta
    cst[CF['hind_L1']] = spec.hind_L1
    cst[CF['hind_L2']] = spec.hind_L2
    cst[CF['hind_xm']] = spec.hind_xm
    cst[CF['fore_pose_sh']] = spec.fore_pose_sh
    cst[CF['fore_pose_el']] = spec.fore_pose_el
    cst[CF['collapse_y']] = collapse_y
    csti = np.zeros(20, np.int32)
    csti[CI['settle_total']] = spec.settle_total
    csti[CI['contact']] = 1 if spec.contact_enabled else 0
    csti[CI['power']] = 1
    csti[CI['gait_enabled']] = 1
    csti[CI['capture_enabled']] = 1
    csti[CI['posture_drive']] = 1
    csti[CI['drive_en']] = sum(1 << d for d in range(12) if spec.drive_enabled[d])
    csti[CI['reflex_level']] = reflex_level
    csti[CI['fold_budget']] = FOLD_BUDGET_TICKS
    csti[CI['unload_ticks']] = UNLOAD_TICKS
    csti[CI['tair']] = int(np.ceil((T_CYCLE - DUTY_SAMPLED) / dt))
    csti[CI['pelvis_row']] = spec.pelvis_row
    store_floor = np.ascontiguousarray(spec.drive_store_floor, np.float64)
    return mdl, mdi, cst, csti, store_floor


class WalkerEnvDLL:
    """The batched nvcc-CUDA walk environment (phase-split tick, DLL route)."""

    def __init__(self, spec: WalkerSpec, n_envs: int, reflex_level: int = 1,
                 collapse_y: float = 0.20, block: int = 32):
        self.spec = spec
        self.E = int(n_envs)
        self.block = int(block)
        E = self.E
        mdl, mdi, cst, csti, store_floor = build_env_arrays(spec, reflex_level, collapse_y)
        self.collapse_y = collapse_y
        self._h = _dll.env_create(
            E, self.block,
            _dp(np.ascontiguousarray(mdl, np.float64)), mdl.size,
            _ip(np.ascontiguousarray(mdi, np.int32)), mdi.size,
            _dp(cst), cst.size,
            _ip(csti), csti.size,
            _dp(store_floor), store_floor.size,
            float(spec.start_phase_left), float(spec.start_phase_right),
            int(spec.settle_total), float(spec.store_post))
        if not self._h:
            raise RuntimeError("env_create failed")

        self._rb = np.zeros(E * 6, np.float64)
        self._rbi = np.zeros(E * 6, np.int32)
        self._refused = np.zeros(E, np.int32)
        self._refused_class = np.zeros(E, np.int32)
        self._collapsed = np.zeros(E, np.int32)
        self._ticks = np.zeros(E, np.int64)
        self._cmd_fires = np.zeros(E, np.int32)
        self._cmd_first_tick = np.zeros(E, np.int64)
        self._hind_tds = np.zeros(E * 2, np.int32)
        self._fore_td_count = np.zeros(E * 2, np.int32)

    def reset(self, q0=None, v0=None, touching0=None):
        spec = self.spec
        if q0 is None:
            q, v, phi = spec.reset_state()
            q0 = np.tile(q, self.E)
            v0 = np.tile(v, self.E)
        if touching0 is None:
            frames, _, _ = spec._fk(np.asarray(q0)[:18])
            t0 = []
            for leg in range(2):
                gmin = 1e300
                for pt in range(2):
                    k = leg * 2 + pt
                    p = frames[spec.pt_body[k]] @ np.append(spec.pt_local[k], 1.0)
                    gmin = min(gmin, p[1] + spec.pt_radius[k] - spec.plane_model_y)
                t0.append(1 if gmin <= K_TOUCH else 0)
            touching0 = np.tile(np.array(t0, np.int32), self.E)
        ok = _dll.env_reset(ctypes.c_void_p(self._h),
                            _dp(np.ascontiguousarray(q0, np.float64)),
                            _dp(np.ascontiguousarray(v0, np.float64)),
                            _ip(np.ascontiguousarray(touching0, np.int32)))
        if not ok:
            raise RuntimeError("env_reset failed")

    def set_command(self, v, env_mask=None):
        if env_mask is None:
            if not _dll.env_set_command(ctypes.c_void_p(self._h), float(v)):
                raise RuntimeError("env_set_command failed")

    def step(self, n=1, readback=False):
        if not _dll.env_step(ctypes.c_void_p(self._h), int(n)):
            raise RuntimeError("env_step failed")
        # synchronous like the numba env's step + cuda.synchronize() pairing
        # (bars_fullport.py times step() around an explicit device sync)
        if not _dll.env_sync(ctypes.c_void_p(self._h)):
            raise RuntimeError("env_sync failed")
        if readback:
            return self.status()
        return None

    def status(self):
        if not _dll.env_sync(ctypes.c_void_p(self._h)):
            raise RuntimeError("env_sync failed")
        E = self.E
        ok = _dll.env_status(ctypes.c_void_p(self._h),
                             _dp(self._rb), _ip(self._rbi),
                             _ip(self._refused), _ip(self._refused_class),
                             _ip(self._collapsed), _lp(self._ticks),
                             _ip(self._cmd_fires), _lp(self._cmd_first_tick),
                             _ip(self._hind_tds), _ip(self._fore_td_count))
        if not ok:
            raise RuntimeError("env_status failed")
        return {'rb': self._rb.reshape(E, 6).copy(),
                'rbi': self._rbi.reshape(E, 6).copy(),
                'refused': self._refused.copy(),
                'refused_class': self._refused_class.copy(),
                'collapsed': self._collapsed.copy(),
                'ticks': self._ticks.copy(),
                'cmd_fires': self._cmd_fires.copy(),
                'cmd_first_tick': self._cmd_first_tick.copy(),
                'hind_tds': self._hind_tds.reshape(E, 2).copy(),
                'fore_td_count': self._fore_td_count.reshape(E, 2).copy()}

    # ---- device-array shims so the frozen bars_fullport.py probe code (which
    # was written against the numba env's d_csti / rb device arrays) runs
    # unchanged on the DLL route ----
    def _csti_get(self):
        a = np.zeros(20, np.int32)
        if not _dll.env_csti_get(ctypes.c_void_p(self._h), _ip(a)):
            raise RuntimeError("env_csti_get failed")
        return a

    def _csti_set(self, a):
        if not _dll.env_csti_set(ctypes.c_void_p(self._h), _ip(np.ascontiguousarray(a, np.int32))):
            raise RuntimeError("env_csti_set failed")

    class _ArrShim:
        def __init__(self, get, set):
            self._get, self._set = get, set
        def copy_to_host(self):
            return self._get()
        def copy_to_device(self, a):
            self._set(a)

    @property
    def d_csti(self):
        return WalkerEnvDLL._ArrShim(self._csti_get, self._csti_set)

    class _RbShim:
        def __init__(self, env):
            self._env = env
        def copy_to_host(self):
            return self._env._rb

    @property
    def rb(self):
        return WalkerEnvDLL._RbShim(self)

    def sync(self):
        if not _dll.env_sync(ctypes.c_void_p(self._h)):
            raise RuntimeError("env_sync failed")

    def read_xoff(self):
        a = np.zeros(self.E * 2, np.float64)
        if not _dll.env_read_xoff(ctypes.c_void_p(self._h), _dp(a)):
            raise RuntimeError("env_read_xoff failed")
        return a

    def __del__(self):
        try:
            if getattr(self, "_h", None):
                _dll.env_free(ctypes.c_void_p(self._h))
        except Exception:
            pass


def load_spec():
    scene = SCENE.read_text(encoding="utf-8")
    import json
    return WalkerSpec(json.loads(scene))


if __name__ == "__main__":
    # THE FIRST TICK at E=2: step(1) must return, then step(300) (the ship
    # horizon); print refused ticks and the status.
    spec = load_spec()
    env = WalkerEnvDLL(spec, n_envs=2, block=32)
    t0 = time.perf_counter()
    env.reset()
    t1 = time.perf_counter()
    print(f"reset ok in {t1 - t0:.3f}s")
    st = env.status()
    print("tick0 rb[:, :3] =", st['rb'][:, :3].tolist())
    print("tick0 ticks =", st['ticks'].tolist())

    t2 = time.perf_counter()
    env.step(1)
    st = env.status()
    t3 = time.perf_counter()
    print(f"FIRST TICK: step(1) returned in {(t3 - t2) * 1000:.1f} ms")
    print("post-tick1 ticks =", st['ticks'].tolist())
    print("post-tick1 refused =", st['refused'].tolist(),
          "class =", st['refused_class'].tolist())
    print("post-tick1 rb[:, :3] =", st['rb'][:, :3].tolist())

    t4 = time.perf_counter()
    env.step(300)
    st = env.status()
    t5 = time.perf_counter()
    dt300 = t5 - t4
    print(f"step(300): {dt300:.3f}s ({300 * 2 / dt300:.0f} env-steps/s at E=2)")
    print("post-300 ticks =", st['ticks'].tolist())
    print("post-300 refused =", st['refused'].tolist(),
          "class =", st['refused_class'].tolist(),
          "collapsed =", st['collapsed'].tolist())
    print("post-300 rb[:, :4] =", st['rb'][:, :4].tolist())
    print("post-300 hind_tds =", st['hind_tds'].tolist(),
          "fore_td_count =", st['fore_td_count'].tolist())
    print("post-300 cmd_fires =", st['cmd_fires'].tolist())
