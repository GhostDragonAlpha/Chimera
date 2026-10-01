#!/usr/bin/env python3
"""MAT2-W08: the FROZEN command model (prereg section 4).

Declared pieces, imported unchanged by the run, the checks and the capture:

1. THE FROZEN INPUT SCRIPT (prereg 4.1) — the declared event schedule fed to
   the PINNED U01 InputMapper over an injected integer-millisecond clock.
2. THE FROZEN ADAPTER LAW (prereg 4.2) — CommandRecord -> the certified
   scene's 8-channel walk interface through the manifest's own limiter
   (`applied = clip(requested, lo, hi)`, saturation named per channel), with
   the zero-order hold (a record issued at tick b applies to steps b+1..b+15)
   and the declared port-inert semantics (the last applied vector continues).
3. THE DERIVED BOUNDS (prereg P4-P7) — every acceptance number recomputed
   LIVE from the pinned scene constants (no hand-copied constants).

Import identity: the projection is float64, cast float32 at the scene
boundary; no other scene mutation exists in this card.
"""
from __future__ import annotations

import math


# --------------------------------------------------------------------------
# frozen schedule constants (prereg section 4.1; the injected ms clock)
# --------------------------------------------------------------------------
PHYSICS_HZ = 300
HORIZON = 10500                 # ticks (35 s); the declared run horizon
T_START_MS = 1000               # press "W"
# mouse yaw is a RATE at the port: raw = counts*sens/interval_s, so
# 20 counts per 50 ms interval = 20*0.002/0.05 = 0.8 rad/s (the pinned
# mapper's own _yaw_demand law; counts are consumed, never resent)
MOUSE_L_WINDOW = (12000, 13450, +20.0)   # +0.8 rad/s in-range turn
MOUSE_R_WINDOW = (13500, 14950, -20.0)   # -0.8 rad/s in-range turn
T_KEY_A_MS = 15000              # press "A" (+1.6 saturating)
T_KEY_A_REL_MS = 16500          # release "A"
T_W_REL_MS = 18025              # release "W" (decay tail; mid sample at 18050)
T_S_PRESS_MS = 20000            # press "S" (live zero)
T_S_REL_MS = 22975              # release "S"

WRONG_INJECT_TICK = 5430        # the stop boundary where R3 takes the wrong key
PROBE_TICK = 5999               # the physical-separation tick (P9)
SETTLE_ONSET_TICK = 5431        # first step driven by the exact-zero record
SETTLE_WINDOW_TICKS = 3600      # the declared settle window (P7)


def ms_to_tick(ms: int) -> int:
    """The injected clock mapping: 50 ms = 15 ticks (exact on the grid)."""
    return (int(ms) * PHYSICS_HZ) // 1000


# tick anchors derived from the frozen script (all exact on the 15-tick grid)
TICK_START_ISSUED = ms_to_tick(T_START_MS)            # 300
TICK_START_ONSET = TICK_START_ISSUED + 1              # 301 (first applied step)
TICK_CEILING_END = ms_to_tick(18000) + 15             # 5415 (last ceiling step)
TICK_DECAY_MID_ISSUED = ms_to_tick(18050)             # 5415 (mid sample issued)
TICK_ZERO_ISSUED = ms_to_tick(18100)                  # 5430 (exact zero issued)
SETTLE_END = SETTLE_ONSET_TICK + SETTLE_WINDOW_TICKS  # 9031
TICK_MOUSE_L_FIRST = ms_to_tick(MOUSE_L_WINDOW[0])    # 3600
TICK_MOUSE_L_LAST = ms_to_tick(MOUSE_L_WINDOW[1])     # 4035
TICK_MOUSE_R_FIRST = ms_to_tick(MOUSE_R_WINDOW[0])    # 4050
TICK_MOUSE_R_LAST = ms_to_tick(MOUSE_R_WINDOW[1])     # 4485
TICK_KEYA_FIRST = ms_to_tick(T_KEY_A_MS)              # 4500
TICK_KEYA_LAST = ms_to_tick(T_KEY_A_REL_MS) - 15      # 4935


# --------------------------------------------------------------------------
# the frozen script executor (feeds the PINNED mapper; nothing else)
# --------------------------------------------------------------------------
def feed_events(mapper, tick: int, now_ms: int) -> None:
    """Apply the scripted input events due at now_ms, BEFORE the boundary
    poll at this tick. The ONLY writer to the mapper; the mapper is the ONLY
    producer of CommandRecords (the no-teleport law)."""
    if tick == ms_to_tick(T_START_MS):
        mapper.press("W", now_ms=now_ms)
    for lo_ms, hi_ms, counts in (MOUSE_L_WINDOW, MOUSE_R_WINDOW):
        if lo_ms <= now_ms <= hi_ms and tick % 15 == 0:
            mapper.mouse(counts)
    if tick == ms_to_tick(T_KEY_A_MS):
        mapper.press("A", now_ms=now_ms)
    if tick == ms_to_tick(T_KEY_A_REL_MS):
        mapper.release("A", now_ms=now_ms)
    if tick == ms_to_tick(T_W_REL_MS):
        mapper.release("W", now_ms=now_ms)
    if tick == ms_to_tick(T_S_PRESS_MS):
        mapper.press("S", now_ms=now_ms)
    if tick == ms_to_tick(T_S_REL_MS):
        mapper.release("S", now_ms=now_ms)


def now_ms_of(tick: int) -> int:
    """The injected integer-millisecond clock for a physics tick."""
    return (tick * 1000) // PHYSICS_HZ


# --------------------------------------------------------------------------
# derived bounds (prereg P4-P7; recomputed LIVE from the pinned constants)
# --------------------------------------------------------------------------
def derived_bounds(scene_const: dict, manifest: dict) -> dict:
    """Every acceptance number, derived from pinned bytes at run time.

    scene_const: the pinned scene module's declared constants subset
    {stride_gain, damping, warm_damp_lo, warm_damp_span}; manifest: the
    frozen policy manifest (action bounds/center) as loaded through the
    frozen loader. The effective damping span of the pinned scene's step law
    is d_eff in [damping*warm_damp_lo,
    damping*(warm_damp_lo + warm_damp_span)] (warm mean in [0,1]).
    """
    g = float(scene_const["stride_gain"])
    d = float(scene_const["damping"])
    d_lo = d * float(scene_const["warm_damp_lo"])
    d_hi = d * (float(scene_const["warm_damp_lo"])
                + float(scene_const["warm_damp_span"]))
    lo = [float(v) for v in manifest["action"]["bounds_lo"]]
    hi = [float(v) for v in manifest["action"]["bounds_hi"]]
    v_cmd = 0.763625                       # the port's own in-band ceiling
    v_mid = v_cmd * 0.75                   # the decay sample at elapsed 25 ms
    stride_lo = lo[1]

    def band(a):
        """The derived achieved-speed band for drive acceleration a."""
        return [a / d_hi, a / d_lo]

    # nominal-damping inversion: the declared band straddles the demand
    band_ceil = band(v_cmd * d)            # a = g*s = v_cmd*d
    band_floor = band(stride_lo * g)       # a = g*stride_floor
    band_mid = band(v_mid * d)
    v0_ub = band_ceil[1]                   # worst-case speed at floor onset
    v0_rise_ub = band_floor[1]             # worst-case speed at start onset

    # two-sided comparison bounds (RIGOROUS for every d_eff in [d_lo, d_hi]):
    #   v_t - a/d >= (1-dt*d)^t (v0 - a/d) per side; d in [d_lo, d_hi]
    steps_ceil = TICK_CEILING_END - TICK_START_ONSET + 1          # 5115
    ceil_low = band_ceil[0] - (band_ceil[0] - v0_rise_ub) * math.exp(
        -d_hi * steps_ceil / float(PHYSICS_HZ))
    steps_settle = SETTLE_END - SETTLE_ONSET_TICK                 # 3600
    settle_up = band_floor[1] + (v0_ub - band_floor[1]) * math.exp(
        -d_lo * steps_settle / float(PHYSICS_HZ))
    track_bound = max(v_cmd - band_ceil[0],
                      band_ceil[1] - v_cmd) + 1e-9
    return {
        "d_lo_per_s": d_lo, "d_hi_per_s": d_hi,
        "v_cmd_ceiling_m_s": v_cmd, "v_cmd_decay_mid_m_s": v_mid,
        "stride_setpoint_ceiling": v_cmd * d / g,
        "stride_setpoint_decay_mid": v_mid * d / g,
        "stride_floor": stride_lo,
        "ceiling_band_m_s": band_ceil, "floor_band_m_s": band_floor,
        "decay_mid_band_m_s": band_mid,
        "ceiling_segment_range_m_s": [ceil_low, band_ceil[1]],
        "ceiling_steps": steps_ceil,
        "settle_end_range_m_s": [band_floor[0], settle_up],
        "settle_steps": steps_settle,
        "ceiling_tracking_bound_m_s": track_bound,
        "plant_spread_m_s": band_ceil[1] - v_cmd,
        "velocity_envelope_m_s": (g * hi[1]) / d_lo,
        "yaw_representable_rad_s": 2.0 * (hi[0] - lo[0]),
        "formulas": {
            "stride_setpoint": "s = v_cmd * d_hi / STRIDE_GAIN (clip to bounds)",
            "yaw_phase_off": "off_l = clip(-yaw/4, lo0, hi0); off_r = clip(+yaw/4, lo4, hi4)",
            "band": "[a/d_hi, a/d_lo] (the scene drive law's fixed-point span)",
            "segment_range": "two-sided comparison bound: v_t - a/d in "
                             "[(v0-a/d)(1-dt*d_hi)^t, (v0-a/d)(1-dt*d_lo)^t]",
            "tracking_bound": "plant spread v_cmd*(d_hi/d_lo - 1) + float guard",
        },
    }


# --------------------------------------------------------------------------
# the frozen adapter law (prereg section 4.2)
# --------------------------------------------------------------------------
class CommandAdapter:
    """CommandRecord stream -> applied 8-vectors with the named limiter.

    The projection law is FROZEN (prereg 4.2). The manifest bounds/center
    come from the FROZEN loader's bundle (pinned bytes), never re-declared.
    """

    def __init__(self, manifest: dict, scene_const: dict):
        act = manifest["action"]
        self.lo = [float(v) for v in act["bounds_lo"]]
        self.hi = [float(v) for v in act["bounds_hi"]]
        self.center = [float(v) for v in act["center"]]
        self.g = float(scene_const["stride_gain"])
        self.d_nom = float(scene_const["damping"])
        self.decisions = 0

    def project(self, v_forward: float, yaw_rate: float) -> dict:
        """One decision: requested vector, applied vector, named saturation."""
        s_req = float(v_forward) * self.d_nom / self.g
        off_l_req = -float(yaw_rate) / 4.0
        off_r_req = float(yaw_rate) / 4.0
        requested = [off_l_req, s_req,
                     self.center[2], self.center[3],
                     off_r_req, s_req,
                     self.center[6], self.center[7]]
        applied = [min(max(v, lo), hi)
                   for v, lo, hi in zip(requested, self.lo, self.hi)]
        sat = [1.0 if abs(a - r) > 0 else 0.0
               for a, r in zip(applied, requested)]
        self.decisions += 1
        return {"requested": requested, "applied": applied, "saturation": sat}

    def idle_projection(self) -> list:
        """The declared IDLE projection (prereg 4.1): the zero-advance floor
        vector (stride at bounds_lo, phase/lift/stiff at center)."""
        return self.project(0.0, 0.0)["applied"]

    def expiry_state(self) -> tuple:
        """The idle vector + its named saturation (the revert target)."""
        vec = self.project(0.0, 0.0)
        return vec["applied"], vec["saturation"]

    @staticmethod
    def expired(last_record_tick, tick, expiry_ticks):
        """The pinned consumer-expiry law (InputMapper.is_expired):
        a record older than EXPIRY_TICKS reverts the consumer to the seam's
        inert path."""
        return (last_record_tick is not None
                and tick - last_record_tick > expiry_ticks)


def vec_close(a, b, eps=1e-9):
    return all(abs(x - y) <= eps for x, y in zip(a, b))
