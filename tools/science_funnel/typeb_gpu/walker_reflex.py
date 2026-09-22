"""walker_reflex.py -- the deterministic reflex core, PYTHON side (TypeB Phase B).

The layer between observations and commands: a faithful mirror of
ChimeraEngine/engine/gait_controller.hpp's reflex machinery (the 9808dc94
bytes, through wave 38 + the typea adapter), consuming ONLY a per-tick
observation stream (q, v -- what an env's status exposes) and emitting
decisions + commands. Everything else (contact gaps, point positions, the
support chain, the fore/hind bookkeeping) is DERIVED here from q through the
committed walker_model.WalkerSpec FK mirror (the physics lane's 1-ulp anchor).

NEW FILE, this lane only: walker_nb_env.py / walker_gpu.py / postgen.py /
walker_numba_gen.py / gait_controller.hpp / cpu_probe.cpp are untouched.

REFLEX LEVELS (the task's gate):
  0  pure physics -- pass-through; no decision, no command, no state.
  1  touch + clocks -- wave-22 touch classes (any-point band +
     kReleaseBand hysteresis), the wave-16-disciplined contact-reset hybrid
     clock (T_CYCLE/DUTY/TOE_OFF semantics, offsets {0,0.5} applied ONCE at
     reset, dt/T_CYCLE advance, settle freeze), the wave-21 capture arming
     (its only mutation IS a clock: phi := CAPTURE_PHI).
  2  + holds/alternation -- the wave-27 height latch, the hind step law's
     full decision structure (wave-28 slot fire + gates (a)-(d), wave-29
     alternation + the wave-35 concentration repair, wave-31 band-entry
     completion, wave-32 min-form deadline, wave-33 stand-first arming read,
     wave-35/36 carrier waive + waive-ridden hand-off preservation, wave-37
     completion-tick graze yield AS SHIPPED, wave-38 stall-era-link calendar
     guard, the lift-first hold), and the fore stepping clock (waves
     13/14/15/20 arm/tau1/grid convergence, the wave-20/23/25 gate scopes,
     wave-23 thin-seat deferral + follow seat, wave-26 wait override,
     wave-24 pocket-hold arm, wave-12 planted-strut IK + capture).
  3  full -- + the typea adapter channel: commanded_target_velocity_x with
     zero-order-hold-at-tick-boundary semantics, v >= 0 domain, the authority
     law xoff = v_cmd*(DUTY_SAMPLED*T_CYCLE)/2 at BOTH plant sites (fore
     xoff, the hind fire), the census (calls, first tick). INERT WHEN UNUSED:
     with no command issued, level 3's decisions equal level 2's byte-for-byte.

Falsifiers this module is judged by (PREREG_PHASEB.md, frozen at db681031):
  F-REFLEX-TRACE-PARITY  -- decision stream vs the C++ GAIT_EVENT_TRACE bytes.
  F-REFLEX-LEVEL-MONOTONE -- levels only ADD decisions on identical feeds.
  F-REFLEX-SCOPE         -- this file is new; no tracked file modified.

Trailer Agent: GLM 5.3.
"""
import math
import numpy as np

from walker_model import (T_CYCLE, DUTY_SAMPLED, FS_HZ, ZETA, CAPTURE_PHI,
                          K_TOUCH, K_SLIP, K_RELEASE_BAND,
                          FOLD_BUDGET_TICKS, UNLOAD_TICKS)

# ── the controller's frozen constants NOT carried by walker_model ──
TOE_OFF = 0.68            # gait_controller.hpp Tables-adjacent constant
K_WALL_MARGIN = 0.0511    # wave 23 (the death's own deflection envelope)
K_DIVE_RATE_MAX = 0.004020  # wave 26 (the mined dive envelope)
K_WAIT_FLOOR = 2.0 * K_DIVE_RATE_MAX
PI = math.pi


def _clamp(x, lo, hi):
    return lo if x < lo else (hi if x > hi else x)


class AdapterChannel:
    """THE COMMAND CHANNEL (typea 20260921), mirrored from configure()/v_cmd().

    Zero-order hold at tick boundaries: the issue takes effect at the next
    tick and holds until replaced (value-only -- a re-issue of the same value
    is decision-identical, the receipt's F_ZOH_CLOCK). Declared domain: the
    plant law's own max(0,.) -- v >= 0, m/s, a number, never a bool. Census:
    every v_cmd() CALL while live counts (the plant-law consumptions), the
    first call's tick recorded. INERT WHEN UNUSED: max(0, measured v3).
    """

    def __init__(self):
        self.live = False
        self.vx = 0.0
        self.issued_tick = 0
        self.fires = 0
        self.first_fire = -1

    def issue(self, v, tick):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("gait_command_number")
        if not (float(v) >= 0.0):
            raise ValueError("gait_command_domain")
        self.live = True
        self.vx = float(v)
        self.issued_tick = tick

    def v_cmd(self, measured_v3, ticks):
        if self.live:
            self.fires += 1
            if self.first_fire < 0:
                self.first_fire = ticks
            return self.vx
        return max(0.0, measured_v3)

    def state(self):
        return {'live': self.live, 'vx': self.vx, 'issued_tick': self.issued_tick,
                'fires': self.fires, 'first_fire': self.first_fire}


class ReflexCore:
    """The full reflex decision machinery, gated by reflex_level 0..3."""

    def __init__(self, spec, reflex_level=3, power=True, contact=True,
                 gait_enabled=True, capture_enabled=True):
        self.spec = spec
        self.level = int(reflex_level)
        self.power = bool(power)
        self.contact = bool(contact)
        self.gait_enabled = bool(gait_enabled)
        self.capture_enabled = bool(capture_enabled)
        self.dt = spec.dt
        self.Tf = T_CYCLE / self.dt
        self.tair = math.ceil((T_CYCLE - DUTY_SAMPLED) / self.dt)  # 9 ticks
        self.swing_nominal = (1.0 - DUTY_SAMPLED) / self.dt
        self.settle_total = int(spec.settle_total)
        self.height_crit = float(spec.height_crit)
        self.height_floor = float(spec.height_floor)
        self.height_armed = bool(spec.height_hold_armed)
        self.mu = float(spec.mu)
        self.gravity = 9.80665
        self.lo = np.asarray(spec.lower, float)
        self.hi = np.asarray(spec.upper, float)
        self.events = []
        self.cmd = AdapterChannel()
        self._reset_state()

    # ── reset (mirrors GaitWalker::reset's reflex-relevant half) ──
    def _reset_state(self):
        s = self.spec
        self.ticks = 0
        self.phi = [s.start_phase_left, s.start_phase_right]
        self.settle_ticks = self.settle_total
        self.paws_captured = False
        self.capture_events = 0
        self.height_latched = False
        self.height_fire_tick = 0
        self.height_fire_margin = 0.0
        self.height_fires = 0
        # fore stepping clock (waves 12/13/14/15/20/23/24/25/26)
        self.fore = [dict(mode=0, t=0.0, stance=0.0, cycle=0.0, td=0,
                          entry=0, conv=0, td_plant=True,
                          target=[0.0, 0.0, 0.0], plant_y=0.0,
                          swing_from=[0.0, 0.0, 0.0], swing_to=[0.0, 0.0, 0.0],
                          replants=0, clamped=0, gate_holds=0,
                          wall_bound=0, wall_follows=0, wait_fires=0,
                          glide_hold=0, hold_last=0, hold_off=[0.0, 0.0, 0.0],
                          branch=-1, qerr=0.0, roundtrip=0.0, sat_ticks=0)
                     for _ in range(2)]
        # hind step law (waves 27..38)
        self.hind = [dict(mode=0, t=0.0, frm=[0.0, 0.0, 0.0], to=[0.0, 0.0, 0.0],
                          plant_y=0.0, ap=0.0, mp=0.0, branch=-1, xoff=0.0,
                          qerr=0.0, fires=0, tds=0, gated=0, clamped=0,
                          last_fire=0, last_td=0, held=False, clear_tick=-1,
                          hold_ticks=0, stall=0, alt=0, alt_due=0,
                          deadline=0, dl_unload=0, deadline_fires=0,
                          unload_fires=0, waive_fires=0, waive_first=-1,
                          waive_last=-1, guard_blocks=0, guard_first=-1,
                          graze_yields=0, graze_first=-1, handoff_restores=0,
                          alt_repairs=0, stand=False, stand_from=[0.0, 0.0, 0.0],
                          stand_y=0.0, stand_mp=0.0, stand_ticks=0)
                     for _ in range(2)]
        self.touching_prev = [False, False]
        self.cmd = AdapterChannel()
        self._g = None  # the current tick's derived geometry

    # ── geometry from q (the committed FK mirror; no engine access) ──
    def _fk_all(self, q):
        s = self.spec
        frames, jv, jw = s._fk(q)
        pw = []
        for k in range(s.npts):
            p = frames[s.pt_body[k]] @ np.append(s.pt_local[k], 1.0)
            pw.append(p)
        gmin_pair = []
        for k in range(s.npts):
            h = k - (k % 2)
            m = h + 1
            gh = pw[h][1] + s.pt_radius[h] - s.plane_model_y
            gm = pw[m][1] + s.pt_radius[m] - s.plane_model_y
            gmin_pair.append(min(gh, gm))
        return frames, jv, jw, pw, gmin_pair

    def _leg_touch(self, leg, gmin_pair):
        """THE TOUCH LAW (wave 22): pair-min gap <= kTouch -> touching;
        > kTouch+kReleaseBand -> released; inside the band the PREV holds."""
        s = self.spec
        prefix, legn = ("left", "left_") if leg == 0 else ("right", "right_")
        gmin = 1e300
        for k, nm in enumerate(s.pt_name):
            if nm.startswith(prefix):
                gmin = min(gmin, gmin_pair[k])
        if gmin <= K_TOUCH:
            return True, gmin
        if gmin > K_TOUCH + K_RELEASE_BAND:
            return False, gmin
        return self.touching_prev[leg], gmin

    def _point_world(self, body, local, frames):
        return frames[body] @ np.append(np.asarray(local, float), 1.0)

    def _sole_slips(self, q, v, frames, jv, jw, pw, gmin_pair):
        """Per-sole planar slip (the capture clause (iii) read), mirrors
        capture_reflex/status: J_pt = jv + jw x (p - com)."""
        s = self.spec
        slips = []
        for k in range(0, s.npts, 2):
            if not (self.contact and gmin_pair[k] <= K_TOUCH):
                slips.append(0.0)
                continue
            b = int(s.pt_body[k])
            p = pw[k][:3]
            com = frames[b][:3, :3] @ s.body_com[b] + frames[b][:3, 3]
            sx = 0.0
            sz = 0.0
            for i in range(s.n):
                jxi = jv[b][i] + np.cross(jw[b][i], p - com)
                sx += jxi[0] * v[i]
                sz += jxi[2] * v[i]
            slips.append(math.hypot(sx, sz))
        return slips

    # ── the tick ──
    def tick(self, q, v):
        """One decision tick over the observation (q, v). Returns the events."""
        if self.level <= 0:
            self.ticks += 1
            return []
        ev = []
        self._g = self._fk_all(q)
        frames, jv, jw, pw, gpair = self._g
        s = self.spec
        walking = self.gait_enabled and (self.settle_ticks <= 0)
        if self.settle_ticks > 0:
            self.settle_ticks -= 1
        # THE PLANT CAPTURE (wave 12) at the settle end
        if (not self.paws_captured and self.settle_total > 0
                and self.settle_ticks == 0 and walking and self.power
                and self.contact):
            for leg in range(2):
                self._capture_paw(leg, q, frames, pw, ev)
            self.paws_captured = True
            self._arm_fore_clock(q, v, frames, pw, ev)
        # 1) the clock (level 1)
        self._update_clock(q, walking, ev)
        # the fore stepping clock + the height latch + the hind law (level 2)
        if self.level >= 2:
            if walking and self.paws_captured:
                self._update_fore_clock(q, v, frames, pw, ev)
                self._height_latch(frames, ev)
            if walking and self.paws_captured and self.height_latched:
                self._hind_block(q, v, frames, pw, gpair, ev)
        # 2) the capture reflex (level 1: its only mutation is the clock)
        if self.level >= 1 and walking and self.capture_enabled:
            self._capture_reflex(q, v, frames, jv, jw, pw, gpair, ev)
        self.ticks += 1
        return ev

    # ── (1) the contact-reset hybrid clock (wave 16 discipline + wave 22) ──
    def _update_clock(self, q, walking, ev):
        for leg in range(2):
            touching, _ = self._leg_touch(leg, self._g[4])
            if walking:
                if touching and not self.touching_prev[leg]:
                    self.phi[leg] = 0.0
                    ev.append({'kind': 'clock_reset', 'leg': leg,
                               'tick': self.ticks})
                else:
                    self.phi[leg] = math.fmod(
                        self.phi[leg] + self.dt / T_CYCLE, 1.0)
            self.touching_prev[leg] = touching

    # ── the wave-21 capture arming (mutates the clock only) ──
    def _capture_reflex(self, q, v, frames, jv, jw, pw, gpair, ev):
        s = self.spec
        chain = self._monotone_chain(pw, gpair)
        com = np.zeros(3)
        mtot = float(np.sum(s.body_mass))
        for b in range(s.nbod):
            p = frames[b][:3, :3] @ s.body_com[b] + frames[b][:3, 3]
            com += s.body_mass[b] * p
        com /= mtot
        if len(chain) < 3:
            return
        vx, vz = v[3], v[5]
        v_bound = self.mu * self.gravity * (1.0 - CAPTURE_PHI) * T_CYCLE
        slips = self._sole_slips(q, v, frames, jv, jw, pw, gpair)
        if max(slips) > v_bound:
            return
        n = len(chain)
        side = 0
        violated = n
        for i in range(n):
            a = chain[i]
            b = chain[(i + 1) % n]
            cross = (b[0] - a[0]) * (com[2] - a[1]) - (b[1] - a[1]) * (com[0] - a[0])
            if abs(cross) < 1e-15:
                continue
            sg = 1 if cross > 0 else -1
            if side == 0:
                side = sg
            elif sg != side:
                violated = i
                break
        if violated >= n:
            return
        a = chain[violated]
        b = chain[(violated + 1) % n]
        ex = b[0] - a[0]
        ez = b[1] - a[1]
        nx, nz = ez, -ex
        nl = math.hypot(nx, nz)
        if nl < 1e-12:
            return
        nx /= nl
        nz /= nl
        cx = sum(p[0] for p in chain) / n
        cz = sum(p[1] for p in chain) / n
        if (cx - a[0]) * nx + (cz - a[1]) * nz < 0:
            nx = -nx
            nz = -nz
        if (vx * nx + vz * nz) <= 0:
            return
        for leg in range(2):
            # the capture's read is the FRESH any-point band (no hysteresis):
            # the C++ scans gap<=kTouch directly, not the wave-22 class.
            touching = False
            prefix = 'left' if leg == 0 else 'right'
            for k, nm in enumerate(s.pt_name):
                if nm.startswith(prefix) and gpair[k] <= K_TOUCH:
                    touching = True
            if not touching and self.phi[leg] >= TOE_OFF:
                self.phi[leg] = CAPTURE_PHI
                self.capture_events += 1
                ev.append({'kind': 'capture_jump', 'leg': leg,
                           'tick': self.ticks})
                return

    def _monotone_chain(self, pw, gpair):
        """THE TRUE HULL (wave 21): the Andrew monotone chain on the touching
        cloud, deterministic lexicographic order; mirrors support_state()."""
        s = self.spec
        cloud = []
        for k in range(s.npts):
            if self.contact and gpair[k] <= K_TOUCH:
                cloud.append((pw[k][0], pw[k][2]))
        if len(cloud) < 3:
            return []
        cloud = sorted(set(cloud))
        if len(cloud) < 3:
            return []
        h = [None] * (2 * len(cloud))
        k = 0
        for i in range(len(cloud)):
            while k >= 2 and (h[k - 1][0] - h[k - 2][0]) * (cloud[i][1] - h[k - 2][1]) - \
                    (h[k - 1][1] - h[k - 2][1]) * (cloud[i][0] - h[k - 2][0]) <= 0:
                k -= 1
            h[k] = cloud[i]
            k += 1
        t = k + 1
        for i in range(len(cloud) - 1, -1, -1):
            while k >= t and (h[k - 1][0] - h[k - 2][0]) * (cloud[i][1] - h[k - 2][1]) - \
                    (h[k - 1][1] - h[k - 2][1]) * (cloud[i][0] - h[k - 2][0]) <= 0:
                k -= 1
            h[k] = cloud[i]
            k += 1
        return h[:k - 1]

    # ── the planted-strut IK (wave 12) ──
    def _fore_ik(self, leg, q, frames, paw):
        s = self.spec
        T = frames[s.fore_mount_body]
        m = s.fore_mount_local['fore_left' if leg == 0 else 'fore_right']
        rx = paw[0] - T[0, 3]
        ry = paw[1] - T[1, 3]
        rz = paw[2] - T[2, 3]
        dx = T[0, 0] * rx + T[1, 0] * ry + T[2, 0] * rz - m[0]
        dy = T[0, 1] * rx + T[1, 1] * ry + T[2, 1] * rz - m[1]
        return self._fore_ik_solve(leg, q, dx, dy)

    def _fore_ik_at(self, leg, q, frames, paw):
        s = self.spec
        T = frames[s.fore_mount_body]
        m = s.fore_mount_local['fore_left' if leg == 0 else 'fore_right']
        rx = paw[0] - T[0, 3]
        ry = paw[1] - T[1, 3]
        rz = paw[2] - T[2, 3]
        dx = T[0, 0] * rx + T[1, 0] * ry + T[2, 0] * rz - m[0]
        dy = T[0, 1] * rx + T[1, 1] * ry + T[2, 1] * rz - m[1]
        return self._fore_ik_solve(leg, q, dx, dy)

    def _fore_ik_solve(self, leg, q, dx, dy):
        s = self.spec
        D = math.hypot(dx, dy)
        dmax = s.fore_L1 + s.fore_rho
        dmin = abs(s.fore_L1 - s.fore_rho)
        saturated = False
        if D > dmax * (1.0 - 1e-12) or D < dmin + 1e-9:
            saturated = True
            Dc = _clamp(D, dmin + 1e-9, dmax * (1.0 - 1e-12))
            dx *= Dc / D
            dy *= Dc / D
            D = Dc
        ca = (D * D + s.fore_L1 * s.fore_L1 - s.fore_rho * s.fore_rho) / (2.0 * D * s.fore_L1)
        th1 = math.atan2(dy, dx) + float(self.fore[leg]['branch']) * math.acos(_clamp(ca, -1.0, 1.0))
        q1 = th1 + PI / 2.0
        ex = dx - s.fore_L1 * math.cos(th1)
        ey = dy - s.fore_L1 * math.sin(th1)
        q2 = math.atan2(ey, ex) - q1 - s.fore_beta
        c1, c2 = s.fore_coord[leg]
        return dict(q1=q1, q2=q2, saturated=saturated, q1_raw=q1, q2_raw=q2,
                    c1=c1, c2=c2)

    def _fore_D_at(self, leg, frames, paw):
        s = self.spec
        T = frames[s.fore_mount_body]
        m = s.fore_mount_local['fore_left' if leg == 0 else 'fore_right']
        rx = paw[0] - T[0, 3]
        ry = paw[1] - T[1, 3]
        rz = paw[2] - T[2, 3]
        dx = T[0, 0] * rx + T[1, 0] * ry + T[2, 0] * rz - m[0]
        dy = T[0, 1] * rx + T[1, 1] * ry + T[2, 1] * rz - m[1]
        return math.hypot(dx, dy)

    def _clamp_fore_ik(self, leg, sol):
        s = self.spec
        c1, c2 = s.fore_coord[leg]
        sol['q1'] = _clamp(sol['q1_raw'], s.lower[c1], s.upper[c1])
        sol['q2'] = _clamp(sol['q2_raw'], s.lower[c2], s.upper[c2])
        return sol

    def _fore_wall_headroom(self, leg, q):
        s = self.spec
        c1, c2 = s.fore_coord[leg]
        h1 = min(q[c1] - s.lower[c1], s.upper[c1] - q[c1])
        h2 = min(q[c2] - s.lower[c2], s.upper[c2] - q[c2])
        return min(h1, h2)

    def _fore_target_headroom_at(self, leg, q, frames, paw):
        s = self.spec
        ik = self._fore_ik_at(leg, q, frames, paw)
        c1, c2 = s.fore_coord[leg]
        h1 = min(ik['q1_raw'] - s.lower[c1], s.upper[c1] - ik['q1_raw'])
        h2 = min(ik['q2_raw'] - s.lower[c2], s.upper[c2] - ik['q2_raw'])
        return min(h1, h2)

    def _fore_follow_seat(self, leg, q, frames):
        s = self.spec
        f = self.fore[leg]
        p = list(f['target'])
        px = list(p)
        px[0] += 1e-3
        py = list(p)
        py[0] -= 1e-3
        hr_p = self._fore_target_headroom_at(leg, q, frames, px)
        hr_m = self._fore_target_headroom_at(leg, q, frames, py)
        direction = 1.0 if hr_p >= hr_m else -1.0
        dmax = s.fore_L1 + s.fore_rho
        lo, hi = 0.0, 2.0 * dmax
        for _ in range(42):
            mid = (lo + hi) / 2
            t = list(p)
            t[0] += direction * mid
            if self._fore_D_at(leg, frames, t) < dmax:
                lo = mid
            else:
                hi = mid
        edge = (lo + hi) / 2
        te = list(p)
        te[0] += direction * edge
        if self._fore_target_headroom_at(leg, q, frames, te) < 2.0 * K_WALL_MARGIN:
            return te
        lo, hi = 0.0, edge
        for _ in range(42):
            mid = (lo + hi) / 2
            t = list(p)
            t[0] += direction * mid
            if self._fore_target_headroom_at(leg, q, frames, t) < 2.0 * K_WALL_MARGIN:
                lo = mid
            else:
                hi = mid
        out = list(p)
        out[0] += direction * ((lo + hi) / 2)
        return out

    def _fore_glide_held(self, leg):
        f = self.fore[leg]
        return f['glide_hold'] != 0 and f['t'] < f['hold_last'] and f['t'] + 1.0 < f['cycle']

    def _fore_amax(self, leg, frames):
        s = self.spec
        f = self.fore[leg]
        sh = self._point_world(s.fore_mount_body,
                               s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                               frames)
        h = max(0.0, sh[1] - f['plant_y'])
        d = s.fore_L1 + s.fore_rho
        a2 = d * d - h * h
        return math.sqrt(a2) if a2 > 0.0 else 0.0

    def _fore_env_ticks(self, leg, q, v, frames):
        s = self.spec
        f = self.fore[leg]
        sh = self._point_world(s.fore_mount_body,
                               s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                               frames)
        off = f['target'][0] - sh[0]
        amax = self._fore_amax(leg, frames)
        vv = max(0.0, v[3])
        if vv <= 1e-9:
            return 0.0
        return max(0.0, (amax + off - vv * self.dt) / vv / self.dt)

    def _fore_entry_stance_ticks(self, leg, q, v, frames):
        return max(0.0, self._fore_env_ticks(leg, q, v, frames)
                   - (math.ceil((T_CYCLE - DUTY_SAMPLED) / self.dt) + 1.0))

    def _fore_entry_stance_rearm(self, leg, q, v, frames):
        f = self.fore[leg]
        f['stance'] = max(0.0, self._fore_entry_stance_ticks(leg, q, v, frames))
        f['cycle'] = f['stance'] + math.ceil((T_CYCLE - DUTY_SAMPLED) / self.dt)

    def _v_cmd(self, v):
        return self.cmd.v_cmd(v[3], self.ticks)

    def _fore_xoff(self, v):
        return self._v_cmd(v) * (DUTY_SAMPLED * T_CYCLE) / 2.0

    def _capture_paw(self, leg, q, frames, pw, ev):
        s = self.spec
        f = self.fore[leg]
        heel = s.fore_heel_pt[leg]
        pwref = np.asarray(s.fore_paw_ref['fore_left' if leg == 0 else 'fore_right'],
                           float)
        pwv = frames[s.pt_body[heel]] @ np.append(pwref, 1.0)
        f['target'] = [float(pwv[0]), float(pwv[1]), float(pwv[2])]
        errs = []
        sols = []
        for b in (0, 1):
            f['branch'] = 1 if b == 0 else -1
            sol = self._clamp_fore_ik(leg, self._fore_ik(leg, q, frames, f['target']))
            c1, c2 = s.fore_coord[leg]
            errs.append(math.hypot(sol['q1'] - q[c1], sol['q2'] - q[c2]))
            sols.append(sol)
        f['branch'] = 1 if errs[0] <= errs[1] else -1
        ik = sols[0] if errs[0] <= errs[1] else sols[1]
        f['qerr'] = min(errs)
        # the closure round-trip (the wave-12 check)
        T = frames[s.fore_mount_body]
        m = s.fore_mount_local['fore_left' if leg == 0 else 'fore_right']
        q12 = ik['q1'] + ik['q2']
        r0, r1 = float(pwref[0]), float(pwref[1])
        ex = s.fore_L1 * math.sin(ik['q1']) + r0 * math.cos(q12) - r1 * math.sin(q12)
        ey = -s.fore_L1 * math.cos(ik['q1']) + r0 * math.sin(q12) + r1 * math.cos(q12)
        lx = m[0] + ex
        ly = m[1] + ey
        lz = m[2]
        fx = T[0, 0] * lx + T[0, 1] * ly + T[0, 2] * lz + T[0, 3]
        fy = T[1, 0] * lx + T[1, 1] * ly + T[1, 2] * lz + T[1, 3]
        f['roundtrip'] = math.hypot(fx - f['target'][0], fy - f['target'][1])
        ev.append({'kind': 'pawcap', 'leg': leg, 'tick': self.ticks,
                   'td': f['td'], 'paw': (f['target'][0], f['target'][1]),
                   'branch': f['branch'], 'qerr': f['qerr'],
                   'roundtrip': f['roundtrip']})

    def _arm_fore_clock(self, q, v, frames, pw, ev):
        s = self.spec
        tair = self.tair
        for leg in range(2):
            f = self.fore[leg]
            f['plant_y'] = f['target'][1]
            sh = self._point_world(s.fore_mount_body,
                                   s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                                   frames)
            off = f['target'][0] - sh[0]
            xoff = self._fore_xoff(v)
            amax = self._fore_amax(leg, frames)
            vv = max(0.0, v[3])
            tau1 = 0.0
            if off < 0.0 and vv > 1e-9:
                f['entry'] = 1
                tau1 = max(0.0, self._fore_entry_stance_ticks(leg, q, v, frames)) * self.dt
            elif xoff > 0.0 and vv > 1e-9:
                lift_wait = max(0.0, DUTY_SAMPLED - self.phi[leg]) * T_CYCLE + 0.25 * T_CYCLE
                tau_env = (amax + off - vv * self.dt) / vv
                if tau_env < 0.0:
                    tau_env = 0.0
                tau1 = min(lift_wait, tau_env)
            f['stance'] = tau1 / self.dt
            f['cycle'] = f['stance'] + (tair if f['entry'] else self.swing_nominal)
            f['t'] = 0.0
            f['mode'] = 0
            f['td'] = 0
            f['replants'] = 0
            f['clamped'] = 0
            f['conv'] = 0
            tau_env_ticks = max(0.0, (amax + off - vv * self.dt) / vv / self.dt) if vv > 1e-9 else -1.0
            ev.append({'kind': 'fore_arm', 'leg': leg, 'tick': self.ticks,
                       'offset0': off, 'xoff': xoff, 'amax': amax,
                       'stance': f['stance'], 'cycle': f['cycle'],
                       'entry': f['entry'], 'tau_env': tau_env_ticks})

    def _fore_converge(self, leg, q, v, frames, ev):
        s = self.spec
        f = self.fore[leg]
        Tf = self.Tf
        swing = self.swing_nominal
        slot0 = self.settle_total + (0.25 if leg == 0 else 0.75) * Tf
        now = float(self.ticks)
        slot = slot0
        while slot <= now + swing:
            slot += Tf
        d = slot - (now + Tf)
        if abs(d) <= 0.5:
            f['conv'] = 1
            f['stance'] = DUTY_SAMPLED / self.dt
            f['cycle'] = Tf
            ev.append({'kind': 'fore_converged', 'leg': leg, 'tick': self.ticks,
                       'slot': slot})
            return
        sh = self._point_world(s.fore_mount_body,
                               s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                               frames)
        off = f['target'][0] - sh[0]
        vv = max(0.0, v[3])
        env = -1.0
        if vv > 1e-9:
            env = (off + self._fore_amax(leg, frames) - vv * self.dt) / vv / self.dt
        smin = swing
        for k in range(1, 9):
            for w in (0, 1):
                step = (d - (Tf if w else 0.0)) / k
                st = DUTY_SAMPLED / self.dt + step
                if st < smin - 1e-9:
                    continue
                if step > 0.0 and (env < 0.0 or st > env + 1e-9):
                    continue
                f['stance'] = st
                f['cycle'] = st + swing
                if k == 1 and w == 0:
                    f['conv'] = 1
                ev.append({'kind': 'fore_converge', 'leg': leg, 'tick': self.ticks,
                           'slot': slot, 'k': k, 'w': w, 'stance': st,
                           'env': env, 'conv': f['conv']})
                return
        f['stance'] = DUTY_SAMPLED / self.dt
        f['cycle'] = Tf

    def _fore_glide_arm_hold(self, leg, q, frames, wall_bound, ev):
        s = self.spec
        f = self.fore[leg]
        f['glide_hold'] = 0
        f['hold_last'] = 0
        if not wall_bound:
            return
        n = int(f['cycle'] - f['stance'])
        if n < 2:
            return
        sh = self._point_world(s.fore_mount_body,
                               s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                               frames)
        p = list(f['target'])
        px = list(p)
        px[0] += 1e-3
        py = list(p)
        py[0] -= 1e-3
        direction = 1.0 if self._fore_target_headroom_at(leg, q, frames, px) >= \
            self._fore_target_headroom_at(leg, q, frames, py) else -1.0
        dmax = s.fore_L1 + s.fore_rho
        lo, hi = 0.0, 2.0 * dmax
        for _ in range(42):
            mid = (lo + hi) / 2
            t = list(p)
            t[0] += direction * mid
            if self._fore_D_at(leg, frames, t) < dmax:
                lo = mid
            else:
                hi = mid
        edge = list(p)
        edge[0] += direction * ((lo + hi) / 2)
        f['hold_off'] = [edge[0] - sh[0], edge[1] - sh[1], edge[2] - sh[2]]
        c1, c2 = s.fore_coord[leg]
        last = 0
        for k in range(1, n + 1):
            sfrac = float(k) / float(n)
            t = [f['swing_from'][i] + (f['swing_to'][i] - f['swing_from'][i]) * sfrac
                 for i in range(3)]
            ik = self._fore_ik_at(leg, q, frames, t)
            if (ik['q1_raw'] < s.lower[c1] or ik['q1_raw'] > s.upper[c1]
                    or ik['q2_raw'] < s.lower[c2] or ik['q2_raw'] > s.upper[c2]):
                last = k
        if last > 0:
            f['glide_hold'] = 1
            f['hold_last'] = last
        # the trace print sits AFTER the early returns: only a wall-bound arm
        # with a marchable span emits the [foreclk] hold line.
        ev.append({'kind': 'fore_hold', 'leg': leg, 'tick': self.ticks,
                   'armed': f['glide_hold'], 'last': f['hold_last'],
                   'off': tuple(f['hold_off'])})

    def _fore_lift_bytes(self, leg, q, v, frames, pw, wall_bound, ev, kind=None):
        """The three lift branches' shared bytes. The C++ prints its own
        [foreclk] line per branch (lift / deflift / waitfire), so the outer
        event is the CALLER's (kind=None for the deflift/waitfire paths)."""
        s = self.spec
        f = self.fore[leg]
        f['mode'] = 1
        if f['entry']:
            f['t'] = 0.0
        heel = s.fore_heel_pt[leg]
        pwv = frames[s.pt_body[heel]] @ np.append(
            np.asarray(s.fore_paw_ref['fore_left' if leg == 0 else 'fore_right'], float), 1.0)
        frm = [float(pwv[0]), float(pwv[1]), float(pwv[2])]
        sh = self._point_world(s.fore_mount_body,
                               s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                               frames)
        f['swing_from'] = frm
        xoff = self._fore_xoff(v)
        amax = self._fore_amax(leg, frames)
        if xoff > amax:
            xoff = amax
            f['clamped'] += 1
        f['swing_to'] = [sh[0] + xoff, f['plant_y'], frm[2]]
        self._fore_glide_arm_hold(leg, q, frames, wall_bound, ev)
        if kind is not None:
            ev.append({'kind': kind, 'leg': leg, 'tick': self.ticks,
                       'td': f['td'], 'entry': f['entry'],
                       'frm': (frm[0], frm[1]), 'to': (f['swing_to'][0], f['swing_to'][1]),
                       'xoff': xoff, 'v': v[3], 'wall_bound': 1 if wall_bound else 0})

    def _update_fore_clock(self, q, v, frames, pw, ev):
        s = self.spec
        Tf = self.Tf
        for leg in range(2):
            f = self.fore[leg]
            f['t'] += 1.0
            if f['mode'] == 1:
                sg = (f['t'] - f['stance']) / (f['cycle'] - f['stance'])
                sg = _clamp(sg, 0.0, 1.0)
                c = 2.0 * s.pt_radius[s.fore_heel_pt[leg]]
                if self._fore_glide_held(leg):
                    shh = self._point_world(s.fore_mount_body,
                                            s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                                            frames)
                    f['target'] = [shh[0] + f['hold_off'][0], shh[1] + f['hold_off'][1],
                                   shh[2] + f['hold_off'][2]]
                else:
                    f['target'] = [f['swing_from'][i] + (f['swing_to'][i] - f['swing_from'][i]) * sg
                                   for i in range(3)]
                    f['target'][1] += c * math.sin(PI * sg)
            if f['mode'] == 0 and f['t'] >= f['stance']:
                o = 1 - leg
                fo = self.fore[o]
                wall_bound = self._fore_wall_headroom(leg, q) <= K_WALL_MARGIN
                if wall_bound:
                    f['wall_bound'] += 1
                gated = False
                gated_b = False
                if f['entry']:
                    if fo['mode'] == 1 and not self._fore_glide_held(o):
                        gated = True
                    elif (fo['mode'] == 0 and fo['entry'] and fo['td_plant']
                          and fo['t'] < 1.0):
                        gated = True
                    elif fo['mode'] == 0 and fo['entry'] and fo['t'] >= fo['stance']:
                        o_prior = fo['t'] > f['t']
                        if fo['t'] == f['t']:
                            sha = self._point_world(s.fore_mount_body,
                                                    s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                                                    frames)
                            sho = self._point_world(s.fore_mount_body,
                                                    s.fore_mount_local['fore_left' if o == 0 else 'fore_right'],
                                                    frames)
                            o_prior = (fo['target'][0] - sho[0]) < (f['target'][0] - sha[0])
                        gated = o_prior
                    if gated:
                        f['gate_holds'] += 1
                thin_seat = self._fore_target_headroom_at(leg, q, frames, f['target']) < 2.0 * K_WALL_MARGIN
                due = f['t'] >= f['stance'] or wall_bound
                if not gated and due and (not thin_seat or not wall_bound):
                    self._fore_lift_bytes(leg, q, v, frames, pw, wall_bound, ev, 'fore_lift')
                elif not gated and due and thin_seat and wall_bound:
                    seat = self._fore_follow_seat(leg, q, frames)
                    if math.hypot(seat[0] - f['target'][0], seat[1] - f['target'][1]) < K_TOUCH:
                        self._fore_lift_bytes(leg, q, v, frames, pw, wall_bound, ev)
                    else:
                        f['target'] = seat
                        f['wall_follows'] += 1
                        f['td_plant'] = False
                        f['replants'] += 1
                        f['t'] = 0.0
                        self._fore_entry_stance_rearm(leg, q, v, frames)
                    ev.append({'kind': 'fore_deflift', 'leg': leg, 'tick': self.ticks,
                               'seat_hr': self._fore_target_headroom_at(leg, q, frames, f['target'])})
                elif gated and wall_bound and self._fore_wall_headroom(leg, q) < K_WAIT_FLOOR:
                    self._fore_lift_bytes(leg, q, v, frames, pw, wall_bound, ev)
                    f['wait_fires'] += 1
                    ev.append({'kind': 'fore_waitfire', 'leg': leg,
                               'tick': self.ticks,
                               'hr': self._fore_wall_headroom(leg, q),
                               'floor': K_WAIT_FLOOR,
                               'hold': f['glide_hold'], 'last': f['hold_last']})
                elif f['t'] >= f['cycle'] or f['t'] >= self._fore_env_ticks(leg, q, v, frames):
                    followed = False
                    if wall_bound and self._fore_target_headroom_at(leg, q, frames, f['target']) < 2.0 * K_WALL_MARGIN:
                        seat = self._fore_follow_seat(leg, q, frames)
                        if math.hypot(seat[0] - f['target'][0], seat[1] - f['target'][1]) < K_TOUCH:
                            self._capture_paw(leg, q, frames, pw, ev)
                        else:
                            f['target'] = seat
                            f['wall_follows'] += 1
                            followed = True
                    else:
                        self._capture_paw(leg, q, frames, pw, ev)
                    f['td_plant'] = False
                    f['replants'] += 1
                    f['t'] = 0.0
                    self._fore_entry_stance_rearm(leg, q, v, frames)
                    pwv = frames[s.pt_body[s.fore_heel_pt[leg]]] @ np.append(
                        np.asarray(s.fore_paw_ref['fore_left' if leg == 0 else 'fore_right'], float), 1.0)
                    ev.append({'kind': 'fore_inplace', 'leg': leg, 'tick': self.ticks,
                               'paw': (float(pwv[0]), float(pwv[1])),
                               'stance': f['stance'], 'entry': f['entry'],
                               'follow': followed})
            if f['t'] >= f['cycle']:
                self._capture_paw(leg, q, frames, pw, ev)
                f['replants'] += 1
                f['td'] += 1
                f['t'] = 0.0
                f['mode'] = 0
                f['td_plant'] = True
                f['glide_hold'] = 0
                f['hold_last'] = 0
                if f['entry']:
                    sh = self._point_world(s.fore_mount_body,
                                           s.fore_mount_local['fore_left' if leg == 0 else 'fore_right'],
                                           frames)
                    if f['target'][0] - sh[0] >= 0.0:
                        f['entry'] = 0
                if f['entry']:
                    self._fore_entry_stance_rearm(leg, q, v, frames)
                elif f['conv']:
                    f['stance'] = DUTY_SAMPLED / self.dt
                    f['cycle'] = Tf
                else:
                    self._fore_converge(leg, q, v, frames, ev)
                ev.append({'kind': 'fore_td', 'leg': leg, 'tick': self.ticks,
                           'td_count': f['td'], 'entry': f['entry'],
                           'stance': f['stance'], 'roundtrip': f['roundtrip']})

    def _height_latch(self, frames, ev):
        s = self.spec
        if not self.height_armed or self.height_latched:
            return
        shl = self._point_world(s.fore_mount_body, s.fore_mount_local['fore_left'], frames)[1]
        shr = self._point_world(s.fore_mount_body, s.fore_mount_local['fore_right'], frames)[1]
        shmin = shl if shl < shr else shr
        if shmin - self.height_crit <= self.height_floor:
            self.height_latched = True
            self.height_fire_tick = self.ticks
            self.height_fire_margin = shmin - self.height_crit
            self.height_fires += 1
            ev.append({'kind': 'height_latch', 'tick': self.ticks,
                       'margin': self.height_fire_margin})

    # ── the hind step law (waves 28..38) ──
    def _hind_off_col(self, phi):
        s = self.spec
        a1 = s.zeros[0] + _table_interp(s.tab_hip, phi)
        a2 = a1 + s.zeros[1] + _table_interp(s.tab_knee, phi)
        ap = a2 + s.zeros[2] + _table_interp(s.tab_ankle, phi)
        return s.hind_L1 * math.sin(a1) + s.hind_L2 * math.sin(a2) + s.hind_xm * math.cos(ap)

    def _hind_step_ik(self, hl, frames, tgt):
        s = self.spec
        h = self.hind[hl]
        T = frames[s.pelvis_row]
        rx = tgt[0] - T[0, 3]
        ry = tgt[1] - T[1, 3]
        rz = tgt[2] - T[2, 3]
        dx = T[0, 0] * rx + T[1, 0] * ry + T[2, 0] * rz
        dy = T[0, 1] * rx + T[1, 1] * ry + T[2, 1] * rz
        ap = h['ap']
        wx = dx - s.hind_xm * math.cos(ap)
        wy = dy - s.hind_xm * math.sin(ap)
        D = math.hypot(wx, wy)
        dmax = s.hind_L1 + s.hind_L2
        dmin = abs(s.hind_L1 - s.hind_L2)
        Dc = _clamp(D, dmin + 1e-9, dmax * (1.0 - 1e-12))
        ca = (Dc * Dc - s.hind_L1 * s.hind_L1 - s.hind_L2 * s.hind_L2) / (2.0 * s.hind_L1 * s.hind_L2)
        k = float(h['branch']) * math.acos(_clamp(ca, -1.0, 1.0))
        a1 = math.atan2(wy, wx) - math.atan2(-s.hind_L1 - s.hind_L2 * math.cos(k),
                                             s.hind_L2 * math.sin(k))
        return a1, k, ap - a1 - k

    def _hind_deadline(self, hl):
        o = 1 - hl
        ho = self.hind[o]
        if ho['last_td'] == 0:
            return 0, False
        fold = ho['last_td'] + (FOLD_BUDGET_TICKS - int(self.tair) - 1)
        if self.hind[hl]['last_td'] != 0:
            unload = ho['last_td'] + (UNLOAD_TICKS - 1)
            if unload < fold:
                return unload, True
        return fold, False

    def _hind_alt_due(self, hl):
        o = 1 - hl
        h = self.hind[hl]
        ho = self.hind[o]
        if ho['last_td'] == 0:
            return False
        if ho['last_fire'] < h['last_td'] and ho['last_td'] < h['last_td']:
            return False
        if ho['last_fire'] < h['last_td']:
            h['alt_repairs'] += 1
        if self.phi[hl] >= TOE_OFF:
            return False
        deadline, _ = self._hind_deadline(hl)
        wait = (TOE_OFF - self.phi[hl]) / (self.dt / T_CYCLE)
        return float(self.ticks) + wait > float(deadline)

    def _hind_stand_hold(self, hl):
        o = 1 - hl
        h = self.hind[hl]
        ho = self.hind[o]
        if ho['mode'] != 1:
            return False
        if h['last_td'] == 0:
            return False
        if not (ho['t'] >= 1.0):
            return False
        if not self.touching_prev[hl] or not self.touching_prev[o]:
            return False
        return True

    def _hind_block(self, q, v, frames, pw, gpair, ev):
        s = self.spec
        tair = float(self.tair)
        # the glide legs: the lift-first hold's release + the band-entry completion
        for hl in range(2):
            h = self.hind[hl]
            if h['mode'] != 1:
                continue
            g1 = gpair[s.hind_heel_pt[hl]]
            g2 = gpair[s.hind_mp_pt[hl]]
            gmin = g1 if g1 < g2 else g2
            if h['held']:
                if gmin > K_TOUCH + K_RELEASE_BAND:
                    h['held'] = False
                    h['clear_tick'] = self.ticks
                else:
                    h['hold_ticks'] += 1
                    h['stall'] += 1
            h['t'] += 1.0
            if h['t'] >= tair:
                if gmin <= K_TOUCH:
                    h['mode'] = 0
                    h['t'] = 0.0
                    h['held'] = False
                    h['last_td'] = self.ticks
                    h['tds'] += 1
                    ev.append({'kind': 'hind_td', 'leg': hl, 'tick': self.ticks,
                               'tds': h['tds']})
                else:
                    ev.append({'kind': 'hind_holdreturn', 'leg': hl,
                               'tick': self.ticks, 't': h['t'], 'pairmin': gmin})
        # the standing legs: the full decision structure
        for hl in range(2):
            o = 1 - hl
            h = self.hind[hl]
            ho = self.hind[o]
            if h['mode'] != 0:
                continue
            alt_due = self._hind_alt_due(hl)
            h['alt_due'] = 1 if alt_due else 0
            dl, is_unload = self._hind_deadline(hl)
            h['deadline'] = dl
            h['dl_unload'] = 1 if is_unload else 0
            if self._hind_stand_hold(hl):
                p1 = pw[s.hind_heel_pt[hl]]
                p2 = pw[s.hind_mp_pt[hl]]
                h['stand_from'] = [(p1[i] + p2[i]) / 2.0 for i in range(3)]
                h['stand_mp'] = q[s.hind_coord[hl][3]]
                if not h['stand']:
                    h['stand_y'] = h['stand_from'][1]
                    h['stand'] = True
                    ev.append({'kind': 'hind_standhold', 'leg': hl,
                               'tick': self.ticks,
                               'swing_stall': self.hind[o]['stall']})
                h['stand_ticks'] += 1
            else:
                h['stand'] = False
            live_slot = self.phi[hl] >= TOE_OFF and self.touching_prev[hl]
            alt_fire = bool(h['alt_due']) and self.touching_prev[hl]
            if (not self.touching_prev[hl] and h['alt_due'] != 0
                    and h['dl_unload'] != 0 and h['deadline'] > 0
                    and self.ticks == h['deadline']):
                h['graze_yields'] += 1
                if h['graze_first'] < 0:
                    h['graze_first'] = self.ticks
                alt_fire = True
            if not live_slot and not alt_fire:
                continue
            gated = False
            gated_b = False
            floor_gated = False
            live = 0
            if ho['mode'] == 1:
                gated = True
            elif ho['last_td'] + 1 > self.ticks:
                gated = True
                gated_b = True
            else:
                for l2 in range(2):
                    prefix = 'fore_left' if l2 == 0 else 'fore_right'
                    mn = 1e300
                    for k, nm in enumerate(s.pt_name):
                        if nm.startswith(prefix):
                            mn = min(mn, gpair[k])
                    if mn <= K_TOUCH:
                        live += 1
                mn = 1e300
                prefix = 'left_' if o == 0 else 'right_'
                for k, nm in enumerate(s.pt_name):
                    if nm.startswith(prefix):
                        mn = min(mn, gpair[k])
                if mn <= K_TOUCH:
                    live += 1
                if live < 2:
                    floor_gated = True
                if alt_fire and not gated and not floor_gated:
                    promised = False
                    if self.touching_prev[o]:
                        for l2 in range(2):
                            prefix = 'fore_left' if l2 == 0 else 'fore_right'
                            mn2 = 1e300
                            for k, nm in enumerate(s.pt_name):
                                if nm.startswith(prefix):
                                    mn2 = min(mn2, gpair[k])
                            if mn2 > K_TOUCH:
                                continue
                            ff = self.fore[l2]
                            if ((ff['mode'] == 0 and ff['stance'] - ff['t'] >= tair)
                                    or (ff['mode'] == 1 and self._fore_glide_held(l2)
                                        and ff['hold_last'] - ff['t'] >= tair)):
                                promised = True
                                break
                    if not promised:
                        floor_gated = True
            deadline_fire = (h['alt_due'] != 0 and h['deadline'] > 0
                             and self.ticks >= h['deadline'])
            if floor_gated and deadline_fire:
                floor_gated = False
                h['deadline_fires'] += 1
            waive_ridden = h['waive_last'] > int(ho['last_fire'])
            if gated_b and deadline_fire:
                if waive_ridden:
                    h['handoff_restores'] += 1
                else:
                    gated = False
                    gated_b = False
                    h['deadline_fires'] += 1
                    if h['dl_unload']:
                        h['unload_fires'] += 1
                    ev.append({'kind': 'hind_unloadgate', 'leg': hl,
                               'tick': self.ticks, 'dl': h['deadline'],
                               'cls': 'unload' if h['dl_unload'] else 'fold'})
            stall_era_link = (h['last_td'] != 0
                              and h['last_td'] - h['last_fire'] == tair)
            if (gated and not gated_b and not floor_gated and alt_fire
                    and h['dl_unload'] and deadline_fire and not ho['held']):
                if stall_era_link:
                    if h['guard_first'] < 0:
                        h['guard_first'] = self.ticks
                    h['guard_blocks'] += 1
                    ev.append({'kind': 'hind_guardblock', 'leg': hl,
                               'tick': self.ticks, 'dl': h['deadline'],
                               'link_td': h['last_td'],
                               'link_fire': h['last_fire']})
                else:
                    gated = False
                    h['waive_fires'] += 1
                    if h['waive_first'] < 0:
                        h['waive_first'] = self.ticks
                    h['waive_last'] = self.ticks
                    ev.append({'kind': 'hind_waivefire', 'leg': hl,
                               'tick': self.ticks, 'dl': h['deadline']})
            if gated or floor_gated:
                h['gated'] += 1
                continue
            # FIRE
            h['mode'] = 1
            h['t'] = 0.0
            h['alt'] = 0 if live_slot else 1
            h['held'] = True
            h['clear_tick'] = -1
            h['stall'] = 0
            h['fires'] += 1
            h['last_fire'] = self.ticks
            p1 = pw[s.hind_heel_pt[hl]]
            p2 = pw[s.hind_mp_pt[hl]]
            frm = [(p1[i] + p2[i]) / 2.0 for i in range(3)]
            h['frm'] = frm
            h['plant_y'] = frm[1]
            c0, c1, c2, c3 = s.hind_coord[hl]
            h['ap'] = q[c0] + q[c1] + q[c2]
            h['mp'] = q[c3]
            h['branch'] = 1 if q[c1] >= 0.0 else -1
            xoff = self._v_cmd(v) * (DUTY_SAMPLED * T_CYCLE) / 2.0
            hip = self._point_world(s.pelvis_row, s.hind_mount['left' if hl == 0 else 'right'], frames)
            hh = max(0.0, hip[1] - h['plant_y'])
            a2m = s.hind_L1 + s.hind_L2
            dxs = s.hind_xm * math.cos(h['ap'])
            dys = hh + s.hind_xm * math.sin(h['ap'])
            under = a2m * a2m - dys * dys
            xmax = dxs + (math.sqrt(under) if under > 0.0 else 0.0)
            if xoff > xmax:
                xoff = xmax
                h['clamped'] += 1
            h['xoff'] = xoff
            h['to'] = [hip[0] + xoff, h['plant_y'], frm[2]]
            qh, qk, qa = self._hind_step_ik(hl, frames, frm)
            h['qerr'] = max(abs(qh - q[c0]), max(abs(qk - q[c1]), abs(qa - q[c2])))
            ev.append({'kind': 'hind_fire', 'leg': hl, 'tick': self.ticks,
                       'phi': self.phi[hl],
                       'cls': 'slot' if h['alt'] == 0 else 'alt',
                       'frm': (frm[0], frm[1]),
                       'to': (h['to'][0], h['to'][1]),
                       'xoff': xoff, 'v': v[3], 'qerr': h['qerr'],
                       'ap': h['ap'], 'br': h['branch'], 'dl': h['deadline']})


def _table_interp(tab, phi):
    phi = phi - math.floor(phi)
    x = phi * 20.0
    k = int(x)
    if k >= 20:
        k = 19
    f = x - k
    return tab[k] * (1.0 - f) + tab[k + 1] * f
