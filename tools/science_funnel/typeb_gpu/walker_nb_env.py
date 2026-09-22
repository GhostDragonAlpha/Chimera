"""walker_nb_env.py -- the batched numba-CUDA training environment wrapper.

Consumes walker_numba_gen (the generated kernels) and exposes the same
GaitWalkEnv API as the warp form. Trailer Agent: GLM 5.3.
"""
import math
import numpy as np
from numba import cuda
from walker_model import (WalkerSpec, T_CYCLE, DUTY_SAMPLED, K_TOUCH, ZETA, FS_HZ,
                          NB, NDRIVE, FOLD_BUDGET_TICKS, UNLOAD_TICKS, SINK_RATE_MAX)
from walker_numba import OF, OI, CF, CI, NI32
from walker_numba_gen import reset_kernel, tick_kernel


def build_model_arrays(spec: WalkerSpec):
    chain_ax_list, chain_off = [], [0]
    for b in range(spec.nbod):
        chain_ax_list += spec.body_slots[b]
        chain_off.append(len(chain_ax_list))
    spec.chain_ax = np.array(chain_ax_list, np.int32)
    spec.chain_off = np.array(chain_off, np.int32)
    mdl = np.zeros(900, np.float64)
    _exp = 0
    for name, off in OF.items():
        # tiling guard: every table's written length must equal its layout slot
        # (a mismatch silently stomps the NEXT table — the chain_ax 60-vs-104
        # class that broke fk_eval on the nvcc route, 2026-09-22)
        assert off == _exp, ('mdl layout mismatch', name, off, _exp)
        if name == 'ax_axis':
            v = np.concatenate([a['axis'] for a in spec.axes]).astype(np.float64)
        elif name == 'ax_slope':
            v = np.array([a['slope'] for a in spec.axes])
        elif name == 'ax_const':
            v = np.array([a['const'] for a in spec.axes])
        elif name == 'body_mass':
            v = spec.body_mass
        elif name == 'body_com':
            v = spec.body_com.reshape(-1)
        elif name == 'body_inertia':
            v = spec.body_inertia.reshape(-1)
        elif name == 'body_fp':
            v = spec.body_fp.reshape(-1)
        elif name == 'body_fc':
            v = spec.body_fc.reshape(-1)
        elif name == 'pt_local':
            v = spec.pt_local.reshape(-1)
        elif name == 'pt_radius':
            v = spec.pt_radius
        elif name in ('lower',):
            v = spec.lower
        elif name in ('upper',):
            v = spec.upper
        elif name == 'drive_cap':
            v = spec.drive_cap
        elif name == 'drive_damping':
            v = spec.drive_damping
        elif name == 'kp':
            v = spec.kp
        elif name == 'kd':
            v = spec.kd
        elif name == 'tab_hip':
            v = spec.tab_hip
        elif name == 'tab_knee':
            v = spec.tab_knee
        elif name == 'tab_ankle':
            v = spec.tab_ankle
        elif name == 'tab_mp':
            v = spec.tab_mp
        elif name == 'zeros4':
            v = spec.zeros
        elif name == 'vault':
            v = spec.trunk_vault
        elif name == 'fore_mount_local':
            v = np.concatenate([spec.fore_mount_local['fore_left'], spec.fore_mount_local['fore_right']])
        elif name == 'hind_mount':
            v = np.concatenate([spec.hind_mount['left'], spec.hind_mount['right']])
        mdl[off:off + len(v)] = v
        _exp += len(v)
    assert _exp <= mdl.size, ('mdl overflow', _exp, mdl.size)
    mdi = np.zeros(NI32, np.int32)
    _exp = 0
    for name, off in OI.items():
        assert off == _exp, ('mdi layout mismatch', name, off, _exp)
        if name == 'ax_rot':
            v = np.array([a['rot'] for a in spec.axes], np.int32)
        elif name == 'ax_slot':
            v = np.array([a['slot'] for a in spec.axes], np.int32)
        elif name == 'body_axoff':
            v = spec.body_axoff
        elif name == 'body_parent':
            v = spec.body_parent
        elif name == 'chain_off':
            v = spec.chain_off
        elif name == 'chain_ax':
            v = spec.chain_ax
        elif name == 'pt_body':
            v = spec.pt_body
        elif name == 'drive_coord':
            v = spec.drive_coord
        elif name == 'fore_coord':
            v = np.array(spec.fore_coord, np.int32).reshape(-1)
        elif name == 'hind_coord':
            v = np.array(spec.hind_coord, np.int32).reshape(-1)
        elif name == 'hind_drive':
            v = np.array(spec.hind_drive_idx, np.int32).reshape(-1)
        elif name == 'fore_drive':
            v = np.array(spec.fore_drive_idx, np.int32).reshape(-1)
        elif name == 'fore_heel_pt':
            v = np.array(spec.fore_heel_pt, np.int32)
        elif name == 'hind_heel_pt':
            v = np.array(spec.hind_heel_pt, np.int32)
        mdi[off:off + len(v)] = v
        _exp += len(v)
    assert _exp == NI32, ('mdi size mismatch', _exp, NI32)
    return mdl, mdi


class GaitWalkEnv:
    """The batched numba-CUDA walk environment (API = the warp form's)."""

    def __init__(self, spec: WalkerSpec, n_envs: int, device=0,
                 reflex_level: int = 1, collapse_y: float = 0.20):
        cuda.select_device(device)
        self.spec = spec
        self.E = int(n_envs)
        E = self.E
        f64 = np.float64
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
            self.a_q, self.a_v, self.a_work, self.a_last_torque,
            self.a_battery, self.a_battery_post, self.a_phi, self.a_touching,
            self.a_captured, self.a_settle, self.a_ik_branch, self.a_paw_target,
            self.a_paw_plant_y, self.a_swing_from, self.a_swing_to,
            self.a_fore_t, self.a_fore_stance, self.a_fore_cycle, self.a_fore_mode,
            self.a_fore_entry, self.a_fore_conv, self.a_fore_td_plant,
            self.a_fore_clamped, self.a_fore_replants, self.a_fore_td_count,
            self.a_hind_mode, self.a_hind_t, self.a_hind_from, self.a_hind_to,
            self.a_hind_plant_y, self.a_hind_ap, self.a_hind_mp, self.a_hind_branch,
            self.a_hind_held, self.a_hind_last_fire, self.a_hind_last_td,
            self.a_hind_fires, self.a_hind_tds, self.a_hind_xoff,
            self.a_height_latched, self.a_cmd_vx, self.a_cmd_live,
            self.a_cmd_first_tick, self.a_cmd_fires, self.a_ticks, self.a_adv_calls,
            self.a_refused, self.a_refused_class, self.a_collapsed)
        cuda.synchronize()

    def set_command(self, v, env_mask=None):
        if env_mask is None:
            self.a_cmd_vx.copy_to_device(np.full(self.E, float(v)))
            self.a_cmd_live.copy_to_device(np.ones(self.E, np.int32))

    def step(self, n=1, readback=False):
        for _ in range(n):
            tick_kernel[self.E, 1](
                self.d_mdl, self.d_mdi, self.d_cst, self.d_csti,
                self.a_q, self.a_v, self.a_work, self.a_last_torque,
                self.a_battery, self.a_battery_post, self.a_phi, self.a_touching,
                self.a_captured, self.a_settle, self.a_ik_branch, self.a_paw_target,
                self.a_paw_plant_y, self.a_swing_from, self.a_swing_to,
                self.a_fore_t, self.a_fore_stance, self.a_fore_cycle, self.a_fore_mode,
                self.a_fore_entry, self.a_fore_conv, self.a_fore_td_plant,
                self.a_fore_clamped, self.a_fore_replants, self.a_fore_td_count,
                self.a_hind_mode, self.a_hind_t, self.a_hind_from, self.a_hind_to,
                self.a_hind_plant_y, self.a_hind_ap, self.a_hind_mp, self.a_hind_branch,
                self.a_hind_held, self.a_hind_last_fire, self.a_hind_last_td,
                self.a_hind_fires, self.a_hind_tds, self.a_hind_xoff,
                self.a_height_latched, self.a_cmd_vx, self.a_cmd_live,
                self.a_cmd_first_tick, self.a_cmd_fires, self.a_ticks, self.a_adv_calls,
                self.a_refused, self.a_refused_class, self.a_collapsed, self.rb, self.rbi)
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
