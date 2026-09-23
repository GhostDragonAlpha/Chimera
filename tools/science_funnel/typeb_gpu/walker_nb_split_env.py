"""walker_nb_split_env.py -- the batched numba-CUDA env on the PHASE-SPLIT tick.

Identical GaitWalkEnv semantics to walker_nb_env.py; each step launches
  tick_plan_kernel -> tick_integ_kernel -> tick_post_kernel
on the same (default) stream, ordered, with a_rc carrying the integration
verdict. BLOCK controls threads/block (>=1; the H2 ladder varies it);
grid = ceil(E/BLOCK). The kernels' bounds guard makes the tail threads
no-ops. reset is untouched ([E,1], verbatim reset_kernel).
Trailer Agent: GLM 5.3.
"""
import math
import numpy as np
from numba import cuda
from walker_model import (WalkerSpec, T_CYCLE, DUTY_SAMPLED, K_TOUCH, ZETA, FS_HZ,
                          NB, NDRIVE, FOLD_BUDGET_TICKS, UNLOAD_TICKS, SINK_RATE_MAX)
from walker_numba import OF, OI, CF, CI
from walker_numba_split import reset_kernel, tick_plan_kernel, tick_integ_kernel, tick_post_kernel
from walker_nb_env import build_model_arrays


class GaitWalkEnv:
    """The batched numba-CUDA walk environment (phase-split tick)."""

    def __init__(self, spec: WalkerSpec, n_envs: int, device=0,
                 reflex_level: int = 1, collapse_y: float = 0.20, block: int = 32):
        cuda.select_device(device)
        self.spec = spec
        self.E = int(n_envs)
        self.block = int(block)
        self.grid = (self.E + self.block - 1) // self.block
        E = self.E
        z = lambda n: cuda.to_device(np.zeros(n, np.float64))
        zi = lambda n: cuda.to_device(np.zeros(n, np.int32))
        zl = lambda n: cuda.to_device(np.zeros(n, np.int64))
        self.a_q = z(E * 18); self.a_v = z(E * 18); self.a_work = z(E * 18)
        self.a_last_torque = z(E * 18)
        self.a_battery = z(E * 12); self.a_battery_post = z(E)
        self.a_phi = z(E * 2); self.a_touching = zi(E * 2)
        self.a_captured = zi(E); self.a_settle = zi(E)
        self.a_ik_branch = zi(E * 2); self.a_paw_target = z(E * 6)
        self.a_paw_plant_y = z(E * 2)
        self.a_swing_from = z(E * 6); self.a_swing_to = z(E * 6)
        self.a_fore_t = z(E * 2); self.a_fore_stance = z(E * 2)
        self.a_fore_cycle = z(E * 2); self.a_fore_mode = zi(E * 2)
        self.a_fore_entry = zi(E * 2); self.a_fore_conv = zi(E * 2)
        self.a_fore_td_plant = zi(E * 2); self.a_fore_clamped = zi(E * 2)
        self.a_fore_replants = zi(E * 2); self.a_fore_td_count = zi(E * 2)
        self.a_fore_glide_hold = zi(E * 2); self.a_fore_hold_last = zi(E * 2)
        self.a_fore_hold_off = z(E * 6)  # CLOSEOUT-8 pocket-clear hold
        self.a_hind_mode = zi(E * 2); self.a_hind_t = z(E * 2)
        self.a_hind_from = z(E * 6); self.a_hind_to = z(E * 6)
        self.a_hind_plant_y = z(E * 2); self.a_hind_ap = z(E * 2)
        self.a_hind_mp = z(E * 2); self.a_hind_branch = zi(E * 2)
        self.a_hind_held = zi(E * 2); self.a_hind_last_fire = zl(E * 2)
        self.a_hind_last_td = zl(E * 2); self.a_hind_fires = zi(E * 2)
        self.a_hind_tds = zi(E * 2); self.a_hind_xoff = z(E * 2)
        self.a_height_latched = zi(E)
        self.a_cmd_vx = z(E); self.a_cmd_live = zi(E)
        self.a_cmd_first_tick = zl(E); self.a_cmd_fires = zi(E)
        self.a_ticks = zl(E); self.a_adv_calls = zi(E)
        self.a_refused = zi(E); self.a_refused_class = zi(E)
        self.a_collapsed = zi(E)
        self.a_rc = zi(E)
        self.rb = z(E * 6); self.rbi = zi(E * 6)

        mdl, mdi = build_model_arrays(spec)
        self.d_mdl = cuda.to_device(mdl)
        self.d_mdi = cuda.to_device(mdi)
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
        self.d_cst = cuda.to_device(cst)
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
        self.d_csti = cuda.to_device(csti)
        self.collapse_y = collapse_y
        self._reset_store = cuda.to_device(spec.drive_store_floor)
        self._store_post = float(spec.store_post)

    def _args(self, with_obs=True):
        core = (self.d_mdl, self.d_mdi, self.d_cst, self.d_csti,
                self.a_q, self.a_v, self.a_work, self.a_last_torque,
                self.a_battery, self.a_battery_post, self.a_phi, self.a_touching,
                self.a_captured, self.a_settle, self.a_ik_branch, self.a_paw_target,
                self.a_paw_plant_y, self.a_swing_from, self.a_swing_to,
                self.a_fore_t, self.a_fore_stance, self.a_fore_cycle, self.a_fore_mode,
                self.a_fore_entry, self.a_fore_conv, self.a_fore_td_plant,
                self.a_fore_clamped, self.a_fore_replants, self.a_fore_td_count,
                self.a_fore_glide_hold, self.a_fore_hold_last, self.a_fore_hold_off,
                self.a_hind_mode, self.a_hind_t, self.a_hind_from, self.a_hind_to,
                self.a_hind_plant_y, self.a_hind_ap, self.a_hind_mp, self.a_hind_branch,
                self.a_hind_held, self.a_hind_last_fire, self.a_hind_last_td,
                self.a_hind_fires, self.a_hind_tds, self.a_hind_xoff,
                self.a_height_latched, self.a_cmd_vx, self.a_cmd_live,
                self.a_cmd_first_tick, self.a_cmd_fires, self.a_ticks, self.a_adv_calls,
                self.a_refused, self.a_refused_class, self.a_collapsed)
        return core + (self.rb, self.rbi) if with_obs else core

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
        qa = cuda.to_device(np.asarray(q0, np.float64))
        va = cuda.to_device(np.asarray(v0, np.float64))
        ta = cuda.to_device(np.asarray(touching0, np.int32))
        reset_kernel[self.E, 1](
            qa, va, ta, np.float64(spec.start_phase_left), np.float64(spec.start_phase_right),
            np.int32(spec.settle_total), self._reset_store, np.float64(self._store_post),
            *self._args(with_obs=False)[4:])
        cuda.synchronize()

    def set_command(self, v, env_mask=None):
        if env_mask is None:
            self.a_cmd_vx.copy_to_device(np.full(self.E, float(v)))
            self.a_cmd_live.copy_to_device(np.ones(self.E, np.int32))

    def step(self, n=1, readback=False):
        for _ in range(n):
            tick_plan_kernel[self.grid, self.block](*self._args(), self.a_rc)
            tick_integ_kernel[self.grid, self.block](*self._args(), self.a_rc)
            tick_post_kernel[self.grid, self.block](*self._args(), self.a_rc)
        if readback:
            cuda.synchronize()
            return self.status()
        return None

    def status(self):
        cuda.synchronize()
        return {'rb': self.rb.copy_to_host().reshape(self.E, 6),
                'rbi': self.rbi.copy_to_host().reshape(self.E, 6),
                'refused': self.a_refused.copy_to_host(),
                'refused_class': self.a_refused_class.copy_to_host(),
                'collapsed': self.a_collapsed.copy_to_host(),
                'ticks': self.a_ticks.copy_to_host(),
                'cmd_fires': self.a_cmd_fires.copy_to_host(),
                'cmd_first_tick': self.a_cmd_first_tick.copy_to_host(),
                'hind_tds': self.a_hind_tds.copy_to_host().reshape(self.E, 2),
                'fore_td_count': self.a_fore_td_count.copy_to_host().reshape(self.E, 2)}
