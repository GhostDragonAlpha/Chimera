"""The DECLARED deterministic CPU walk scene (the lane's physics of record).

This is a SURROGATE, declared as such in the frozen prereg (receipt.json,
"scope_and_honesty_declared_in_advance"): the C++ engine is out of this lane's
scope; the certificate binds CONTENT HASHES (this module's sha + the params'
canonical sha), so the format and every check transfer to the real engine build
unchanged. Every constant below is declared in the prereg BEFORE any run --
declared, not swept (Rule 1): the clock mirrors the banked wave-38 walk
(cycle_ticks=213, dt=1/300 = the manifest's physics_hz=300); the drive constants
derive from the frozen P3 manifest's own action bounds.

Closed loop per tick t:
  record  = scene.observation_record()      # PRE-decision state of tick t
  applied = policy.act(record)              # frozen actor, zero-order hold
  scene.step(applied)                       # physics advances on the command

Determinism: the trajectory is a pure function of (params, build id, seed,
command stream). One PCG64 draw per tick feeds the micro-terrain height -- by
declaration trajectory-visible, so a dropped RNG state cannot resume silently
(F2's instrument). The contact warm-start cache is trajectory-visible through
the declared effective-damping coupling (a dropped cache must move the future:
warm resets to 0 on a dropped cache while it rides near 1.0 in contact, a
~10% damping step, orders above float32 resolution).

Build identity: BUILD_N is the reference; BUILD_N1 = the prereg's declared 1%
damping delta. Nothing else moves between builds.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

SCENE_VERSION = "cpu-walk-scene/1.0.0"

# ---- declared constants (prereg "declared_scene_constants"; none tuned) ----
DT = 1.0 / 300.0                     # the manifest's physics_hz = 300
CYCLE_TICKS = 213                    # the banked wave-38 gait clock
STRIDE_GAIN = 0.55                   # m/s^2 per unit stride command
LIFT_GAIN = 0.06                     # m per unit lift command
GROUND_CLEARANCE = 0.008             # m
DAMPING = 0.35                       # 1/s velocity decay
CONTACT_THRESHOLD = 0.012            # m
MP_PHASE_OFFSET = 0.08               # cycles, heel->MP shape offset
MICRO_TERRAIN_AMP = 1e-4             # m, one PCG64 draw per tick
REFLEX_TRIP_TICKS = 90               # ticks
REFLEX_GAP_SPIKE = 0.01              # m above threshold while loaded
WARM_RISE = 0.1                      # per contact tick
WARM_DECAY_AIR = 0.98                # per airborne tick
WARM_DAMP_LO = 0.95                  # effective damping floor (warm == 0)
WARM_DAMP_SPAN = 0.1                 # effective damping span (warm 0 -> 1)

DELTA_DECLARED = 0.01                # the prereg's build N -> N+1 damping delta
STRIDE_AMP_HI = 1.8                  # from the frozen manifest action bounds_hi

BUILD_N_ID = "cpu-walk-scene-build-N"
BUILD_N1_ID = "cpu-walk-scene-build-N+1"
BUILD_N1_DELTA_NOTE = "damping_1 = damping * 1.01 (the prereg's declared delta)"


def build_params() -> dict:
    return {
        "stride_gain": STRIDE_GAIN,
        "lift_gain": LIFT_GAIN,
        "ground_clearance": GROUND_CLEARANCE,
        "damping": DAMPING,
        "contact_threshold": CONTACT_THRESHOLD,
        "mp_phase_offset": MP_PHASE_OFFSET,
        "micro_terrain_amp": MICRO_TERRAIN_AMP,
        "reflex_trip_ticks": REFLEX_TRIP_TICKS,
        "reflex_gap_spike": REFLEX_GAP_SPIKE,
        "warm_rise": WARM_RISE,
        "warm_decay_air": WARM_DECAY_AIR,
        "warm_damp_lo": WARM_DAMP_LO,
        "warm_damp_span": WARM_DAMP_SPAN,
        "cycle_ticks": CYCLE_TICKS,
        "dt": DT,
    }


def params_sha(params: dict) -> str:
    return hashlib.sha256(
        json.dumps(params, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def build_n() -> tuple[str, dict]:
    return BUILD_N_ID, build_params()


def build_n1() -> tuple[str, dict]:
    p = build_params()
    p["damping"] = p["damping"] * 1.01   # the declared delta, exact float
    return BUILD_N1_ID, p


def derived_envelope() -> dict:
    """The pre-derived envelope + open-loop cross-build margin (Rule 1: DERIVED,
    not chosen; the prereg amendment 2026-09-20 pre-data corrected the baseline
    to the declared warm-start damping FLOOR -- the original draft used the
    nominal damping and no run had happened).

    Drive: v_{t+1} = (1 - dt*d_eff) v_t + dt*a, d_eff in [DAMPING*0.95, DAMPING]
    (warm in [0,1]); a in [0, a_max], a_max = STRIDE_GAIN * STRIDE_AMP_HI.

    Envelope: v is contracted toward a/d_eff, so |v_t| <= max(0, a_max/d_lo)
    with d_lo = DAMPING*WARM_DAMP_LO -- the fixed-point bound V.

    Open-loop cross-build margin (identical pinned command streams, build N+1
    scaling every d_eff by (1+delta)):
        Delta_{t+1} = (1-dt*d'_t) Delta_t - dt*(d'_t-d_t) v_t
                    = (1-dt*d'_t) Delta_t - dt*delta*d_t v_t
        => |Delta_H| <= [dt*delta*d_hi*V] * (1-(1-dt*d_lo')^H)/(dt*d_lo')
                      <= delta*d_hi*V/d_lo' = delta*V/(1.01*0.95)
    (d_lo' = 1.01*d_lo), horizon-independent.
    """
    a_max = STRIDE_GAIN * STRIDE_AMP_HI
    d_lo = DAMPING * WARM_DAMP_LO
    v_env = a_max / d_lo
    margin = DELTA_DECLARED * v_env / (1.01 * WARM_DAMP_LO)
    return {
        "a_max_m_s2": a_max,
        "d_lo_per_s": d_lo,
        "d_hi_per_s": DAMPING,
        "velocity_envelope_m_s": v_env,
        "delta_declared": DELTA_DECLARED,
        "openloop_crossbuild_margin_m_s": margin,
        "derivation": (
            "v_{t+1}=(1-dt*d_eff)v_t+dt*a; d_eff in [d*0.95, d] (the declared "
            "warm-start coupling), a in [0, STRIDE_GAIN*stride_amp_hi=0.99]; "
            "envelope V = a_max/d_lo = 0.99/(0.35*0.95) = "
            f"{v_env!r} m/s (contraction fixed point); build N+1 scales every "
            "d_eff by 1.01, so Delta_{t+1} = (1-dt*d'_t)Delta_t - dt*0.01*d_t*v_t "
            "and the geometric sum over ANY horizon gives "
            "max|Delta_v| <= delta*V/(1.01*0.95) = 0.01*"
            f"{v_env!r}/0.9595 = {margin!r} m/s"),
    }


AVAILABLE_GROUPS = ["gait_phase", "contact_aggregate", "contact_per_foot",
                    "contact_force", "body_velocity", "prev_requested_cmd",
                    "prev_applied_cmd", "limiter_saturation", "intervention",
                    "command_clock", "sensor_health", "phase_dynamics"]

_FRONT_FORCE = 0.25  # declared nominal fore-foot support (N_bw_frac)


def _gaps_for(params: dict, phase: float, phase_off: float, lift_amp: float,
              micro: float) -> tuple[float, float]:
    """Heel/MP pad gaps for one leg at its offset-included effective phase.
    THE single gap formula -- the record and the physics both call this."""
    eff = (phase + phase_off) % 1.0
    swing_h = max(0.0, float(np.sin(2.0 * np.pi * eff)))
    eff_mp = (eff - params["mp_phase_offset"]) % 1.0
    swing_m = max(0.0, float(np.sin(2.0 * np.pi * eff_mp)))
    g_h = params["ground_clearance"] + lift_amp * swing_h + micro
    g_m = params["ground_clearance"] + lift_amp * swing_m + micro
    return g_h, g_m


class WalkScene:
    """Deterministic closed-loop CPU walk scene with a COMPLETE snapshot."""

    def __init__(self, params: dict, seed: int, build_id: str):
        self.params = params
        self.seed = int(seed)
        self.build_id = build_id
        # body_state
        self.v = 0.0
        self.x = 0.0
        self.phase_l = 0.0
        self.phase_r = 0.5             # declared half-cycle offset (P3 slice convention)
        # contact_warm_start_cache (trajectory-visible by declaration)
        self.warm_l = 0.0
        self.warm_r = 0.0
        self.contact_l = 0
        self.contact_r = 0
        # reflex_state
        self.trip_l = 0
        self.trip_r = 0
        # rng_stream
        self._rng = np.random.Generator(np.random.PCG64(self.seed))
        # world_state
        self.draws_consumed = 0
        self._last_micro = 0.0
        # held command state
        center = [0.0, 1.0, 1.0, 1.25, 0.0, 1.0, 1.0, 1.25]  # the manifest center
        self._held = center
        self._sat = [0.0] * 8
        self._phase_off_l, self._phase_off_r = center[0], center[4]
        self._lift_l, self._lift_r = center[2], center[6]
        self.tick = 0

    # -------------------------------------------------- observation record
    def observation_record(self) -> dict:
        """The PRE-decision telemetry record of the CURRENT tick (pure read;
        identical bytes before and after a snapshot round-trip)."""
        p = self.params
        g_hl, g_ml = _gaps_for(p, self.phase_l, self._phase_off_l, self._lift_l,
                               self._last_micro)
        g_hr, g_mr = _gaps_for(p, self.phase_r, self._phase_off_r, self._lift_r,
                               self._last_micro)
        contact_l = int(min(g_hl, g_ml) < p["contact_threshold"])
        contact_r = int(min(g_hr, g_mr) < p["contact_threshold"])
        return {
            "tick": self.tick,
            "phase_left": (self.phase_l + self._phase_off_l) % 1.0,
            "phase_right": (self.phase_r + self._phase_off_r) % 1.0,
            "phase_frac": ((self.phase_l + self._phase_off_l
                            + self.phase_r + self._phase_off_r) / 2.0) % 1.0,
            "phase_rate": 1.0 / p["cycle_ticks"],
            "contact_count": 4 + contact_l + contact_r,
            "foot_contacts": [1.0, 1.0, 1.0, 1.0,
                              float(contact_l), float(contact_r)],
            "foot_forces": [_FRONT_FORCE, _FRONT_FORCE, _FRONT_FORCE, _FRONT_FORCE,
                            (_FRONT_FORCE * self.warm_l if contact_l else 0.0),
                            (_FRONT_FORCE * self.warm_r if contact_r else 0.0)],
            "com_vel": [self.v, 0.0, 0.0],
            "yaw_rate": 2.0 * (self._phase_off_r - self._phase_off_l),
            "requested_cmd": [float(c) for c in self._held],
            "applied_cmd": [float(c) for c in self._held],
            "limiter_saturation": [float(s) for s in self._sat],
            "intervention_reason": "none",
            "freq_scale": 1.0,
            "available_groups": list(AVAILABLE_GROUPS),
            "pad_gaps": {"hl": [g_hl, g_ml], "hr": [g_hr, g_mr]},
            "pad_pair_ordering": {"hl": "heel_mp", "hr": "heel_mp"},
        }

    # ------------------------------------------------------------- stepping
    def step(self, applied: np.ndarray, saturation: np.ndarray) -> list[float]:
        """Advance one tick on the applied 8-command vector. Returns the fixed-
        order state vector (the per-tick hash input for the evidence chain)."""
        p = self.params
        cmd = [float(c) for c in applied]
        self._held = cmd
        self._sat = [float(s) for s in saturation]
        self._phase_off_l, self._phase_off_r = cmd[0], cmd[4]
        self._lift_l, self._lift_r = cmd[2], cmd[6]

        micro = float(self._rng.uniform(-p["micro_terrain_amp"], p["micro_terrain_amp"]))
        self._last_micro = micro
        self.draws_consumed += 1

        g_hl, g_ml = _gaps_for(p, self.phase_l, cmd[0], cmd[2], micro)
        g_hr, g_mr = _gaps_for(p, self.phase_r, cmd[4], cmd[6], micro)
        new_contact_l = int(min(g_hl, g_ml) < p["contact_threshold"])
        new_contact_r = int(min(g_hr, g_mr) < p["contact_threshold"])

        # reflex: a gap spike while loaded trips the leg (halved phase rate)
        if self.contact_l and min(g_hl, g_ml) > p["contact_threshold"] + p["reflex_gap_spike"] \
                and self.trip_l == 0:
            self.trip_l = int(p["reflex_trip_ticks"])
        if self.contact_r and min(g_hr, g_mr) > p["contact_threshold"] + p["reflex_gap_spike"] \
                and self.trip_r == 0:
            self.trip_r = int(p["reflex_trip_ticks"])

        # warm-start cache: rises on contact, decays airborne (trajectory-visible)
        self.warm_l = min(1.0, self.warm_l + p["warm_rise"]) if new_contact_l \
            else self.warm_l * p["warm_decay_air"]
        self.warm_r = min(1.0, self.warm_r + p["warm_rise"]) if new_contact_r \
            else self.warm_r * p["warm_decay_air"]
        self.contact_l, self.contact_r = new_contact_l, new_contact_r

        # drive: com speed on the mean stride command; damping modulated by the
        # warm-start cache (the declared trajectory-visible coupling)
        d_eff = p["damping"] * (p["warm_damp_lo"]
                                + p["warm_damp_span"] * 0.5 * (self.warm_l + self.warm_r))
        a_com = p["stride_gain"] * 0.5 * (cmd[1] + cmd[5])
        self.v += p["dt"] * (a_com - d_eff * self.v)
        self.x += p["dt"] * self.v

        # phase advance (a reflex trip halves that leg's rate)
        rate_l = 0.5 if self.trip_l > 0 else 1.0
        rate_r = 0.5 if self.trip_r > 0 else 1.0
        if self.trip_l > 0:
            self.trip_l -= 1
        if self.trip_r > 0:
            self.trip_r -= 1
        self.phase_l = (self.phase_l + rate_l / p["cycle_ticks"]) % 1.0
        self.phase_r = (self.phase_r + rate_r / p["cycle_ticks"]) % 1.0

        self.tick += 1
        return self.state_vector()

    # ------------------------------------------------------ state canonical
    def state_vector(self) -> list[float]:
        """The fixed-order numeric state (the per-tick hash input)."""
        return [self.v, self.x, self.phase_l, self.phase_r,
                self.warm_l, self.warm_r,
                float(self.contact_l), float(self.contact_r),
                float(self.trip_l), float(self.trip_r),
                float(self.draws_consumed), self._last_micro]

    def state_sha256(self) -> str:
        b = np.asarray(self.state_vector(), dtype="<f8").tobytes()
        b += f"|tick={self.tick}|seed={self.seed}|build={self.build_id}|ps={self.params_sha()}".encode()
        return hashlib.sha256(b).hexdigest()

    def params_sha(self) -> str:
        return params_sha(self.params)

    # ------------------------------------------------------------ snapshot
    _INVENTORY_KEYS = ("body_state", "contact_warm_start_cache", "reflex_state",
                       "held_command", "rng_stream", "world_state", "tick")

    def snapshot(self) -> dict:
        """The COMPLETE scene snapshot: every registered inventory item.
        decision_phase + controller_history live in the POLICY snapshot
        (runner.policy_snapshot); the tick here is the scene's own clock."""
        st = self._rng.bit_generator.state
        return {
            "scene_version": SCENE_VERSION,
            "build_id": self.build_id,
            "params_sha256": self.params_sha(),
            "seed": self.seed,
            "body_state": {"v": repr(self.v), "x": repr(self.x),
                           "phase_l": repr(self.phase_l), "phase_r": repr(self.phase_r)},
            "contact_warm_start_cache": {"warm_l": repr(self.warm_l),
                                         "warm_r": repr(self.warm_r),
                                         "contact_l": self.contact_l,
                                         "contact_r": self.contact_r},
            "reflex_state": {"trip_l": self.trip_l, "trip_r": self.trip_r},
            "held_command": {"held": [repr(c) for c in self._held],
                             "saturation": [repr(s) for s in self._sat],
                             "phase_off_l": repr(self._phase_off_l),
                             "phase_off_r": repr(self._phase_off_r),
                             "lift_l": repr(self._lift_l), "lift_r": repr(self._lift_r)},
            "rng_stream": {"bit_generator": st["bit_generator"],
                           "state": str(st["state"]["state"]),
                           "inc": str(st["state"]["inc"]),
                           "has_uint32": st["has_uint32"],
                           "uinteger": st["uinteger"]},
            "world_state": {"draws_consumed": self.draws_consumed,
                            "last_micro": repr(self._last_micro)},
            "tick": self.tick,
        }

    def _missing_inventory(self, snap: dict) -> list[str]:
        return [k for k in self._INVENTORY_KEYS if k not in snap]

    def restore_snapshot(self, snap: dict) -> None:
        """Restore from a COMPLETE snapshot. ANY missing registered inventory
        item is a named refusal (F2's structural detection layer)."""
        missing = self._missing_inventory(snap)
        if missing:
            raise SnapshotError(
                "REFUSED: restart snapshot INCOMPLETE -- missing registered "
                f"inventory items: {missing} (only a complete snapshot may resume)")
        if snap.get("params_sha256") != self.params_sha() or \
                snap.get("build_id") != self.build_id:
            raise SnapshotError(
                "REFUSED: snapshot build mismatch: snapshot "
                f"{snap.get('build_id')}/{str(snap.get('params_sha256'))[:16]}... != "
                f"this build {self.build_id}/{self.params_sha()[:16]}...")
        b = snap["body_state"]
        self.v, self.x = float(b["v"]), float(b["x"])
        self.phase_l, self.phase_r = float(b["phase_l"]), float(b["phase_r"])
        w = snap["contact_warm_start_cache"]
        self.warm_l, self.warm_r = float(w["warm_l"]), float(w["warm_r"])
        self.contact_l, self.contact_r = int(w["contact_l"]), int(w["contact_r"])
        self.trip_l, self.trip_r = int(snap["reflex_state"]["trip_l"]), int(snap["reflex_state"]["trip_r"])
        h = snap["held_command"]
        self._held = [float(c) for c in h["held"]]
        self._sat = [float(s) for s in h["saturation"]]
        self._phase_off_l, self._phase_off_r = float(h["phase_off_l"]), float(h["phase_off_r"])
        self._lift_l, self._lift_r = float(h["lift_l"]), float(h["lift_r"])
        r = snap["rng_stream"]
        self._rng.bit_generator.state = {
            "bit_generator": r["bit_generator"],
            "state": {"state": int(r["state"]), "inc": int(r["inc"])},
            "has_uint32": int(r["has_uint32"]), "uinteger": int(r["uinteger"])}
        self._last_micro = float(snap["world_state"]["last_micro"])
        self.draws_consumed = int(snap["world_state"]["draws_consumed"])
        self.tick = int(snap["tick"])

    def forced_restore_snapshot(self, snap: dict) -> list[str]:
        """The PROBE path (F2 dynamic detection): restore while TOLERATING
        missing inventory items (each missing item reverts to its fresh-run
        default -- the WRONG value mid-run). Returns the missing names. The
        caller proves the omission by comparing the forced continuation against
        the uninterrupted reference bytes."""
        missing = self._missing_inventory(snap)
        patched = dict(snap)
        fresh = np.random.PCG64(self.seed).state
        defaults = {
            "rng_stream": {"bit_generator": "PCG64",
                           "state": str(fresh["state"]["state"]),
                           "inc": str(fresh["state"]["inc"]),
                           "has_uint32": fresh["has_uint32"],
                           "uinteger": fresh["uinteger"]},
            "contact_warm_start_cache": {"warm_l": "0.0", "warm_r": "0.0",
                                         "contact_l": 0, "contact_r": 0},
            "body_state": {"v": "0.0", "x": "0.0", "phase_l": "0.0", "phase_r": "0.5"},
            "reflex_state": {"trip_l": 0, "trip_r": 0},
            "held_command": {"held": ["0.0"] * 8, "saturation": ["0.0"] * 8,
                             "phase_off_l": "0.0", "phase_off_r": "0.0",
                             "lift_l": "0.0", "lift_r": "0.0"},
            "world_state": {"draws_consumed": 0, "last_micro": "0.0"},
            "tick": 0,
        }
        for k in missing:
            patched[k] = defaults[k]
        self.restore_snapshot(patched)
        return missing


class SnapshotError(Exception):
    """A restart snapshot that violates the registered inventory."""


def make_scene(build_id: str, params: dict, seed: int) -> WalkScene:
    return WalkScene(params=params, seed=seed, build_id=build_id)


def canonical_snapshot_bytes(snap: dict) -> bytes:
    return json.dumps(snap, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
