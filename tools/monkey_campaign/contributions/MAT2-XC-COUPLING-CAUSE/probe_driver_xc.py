#!/usr/bin/env python3
"""MAT2-XC-COUPLING-CAUSE: the arm driver (prereg section 1).

ONE scene-module identity (the W10 layer's pinned extraction, the sealed
X05 identity), ONE build id, ONE seed (20260920), the sealed window
(presented ticks 4365..4666 step 15; 21 rows), the sealed probe classes
VERBATIM (release W at T_in(n)=4351+(n-1); re-press +150 ticks SHORT /
+300 ticks LONG; BRAKE-DEEP +600 declared in the frozen prereg; the A2
S-press class press S at T_in / release at T_in+150).

THE TWO FORMS (arm group A — the harness-form gate):
- form 'full' (the X05/certified-line form): the certified feed_events
  law through the WHOLE horizon;
- form 'cut' (the a12/WK-LATENCY form, frozen in the committed
  WK-LATENCY preregistration: "bytes through tick 4350, then SILENCE
  (no input events)"): the same law through tick SCRIPT_CUT_TICK=4350,
  then the probe events ONLY.
The forms differ in EXACTLY the script gate; everything else is shared
code. The loop body is the certified W10 `run_commanded` structure (the
frozen feed_events law, the no-teleport RecordingSink, the ZOH pending
law, the consumer-side expiry contract) with the accepted SeamTracer
owning the command chains (the U07 four-stage form; imported, never
copied).

Headless, CPU-only, deterministic; numpy only at the scene boundary.
"""
from __future__ import annotations

PHYSICS_HZ = 300
SEED = 20260920                     # the certified scene seed (continuity)
HORIZON = 4800                      # ticks (prereg section 1)
SCRIPT_CUT_TICK = 4350              # the frozen WK-LATENCY cut law
WINDOW_FIRST_TICK = 4351            # T_in(1)

PRESENT_TICKS = list(range(4365, 4666, 15))      # 21 presentation frames

CLASS_REPRESS = {"BRAKE-SHORT": 150, "BRAKE-LONG": 300, "BRAKE-DEEP": 600}
E2_HOLD_TICKS = 150                 # the A2 class verbatim (SHORT depth)


def t_in(n):
    return WINDOW_FIRST_TICK + (n - 1)


def now_ms_of(tick):
    """The injected integer-millisecond clock for a physics tick."""
    return (int(tick) * 1000) // PHYSICS_HZ


class RecordingSink:
    """The no-teleport law's instrument (W10's sealed form, verbatim role):
    the ONLY thing the port can do."""

    def __init__(self):
        self.calls = []
        self.records = []

    def emit(self, record):
        self.calls.append(("emit", record))
        self.records.append(record)
        return len(self.records)


def probe_events_for(spec):
    """The declared probe schedule from the frozen spec.
    kind 'release-w': release W at t_in, press W at t_in+repress.
    kind 'press-s':   press S at t_in,  release S at t_in+hold."""
    if spec is None:
        return []
    kind = spec["kind"]
    t0 = spec["t_in"]
    if kind == "release-w":
        return [(t0, "release", "W"), (t0 + spec["repress"], "press", "W")]
    if kind == "press-s":
        return [(t0, "press", "S"), (t0 + spec["hold"], "release", "S")]
    raise ValueError("probe_kind_unknown:" + kind)


def run_arm(arm_id, adapter, build_id, params, *, form="full", probe=None,
            horizon=HORIZON):
    """One commanded execution of the certified line.

    form 'full': the certified feed_events law every tick (the X05 form).
    form 'cut':  the same law through tick 4350, SILENCE after (the
                 committed WK-LATENCY a12 law); probe events still fire.
    probe: None (CONTROL) or {"kind": ..., "t_in": ...} (prereg section 1).
    """
    import numpy as np
    from tools.policy_compat import scene_cpu as SC      # pinned bytes
    from tools.science_funnel.typeb_export.command_record import (  # pinned
        COMMAND_RECORD_VERSION, V_MAX_IN_BAND_M_S)
    from tools.monkey_campaign.product.input_mapper import (  # pinned
        InputMapper, V_MAX_IN_BAND_M_S as IM_V_MAX,
        OMEGA_MAX_RAD_S, EXPIRY_TICKS)
    import command_model as cm                           # W10 bytes, pinned
    it, ad = adapter["trace_modules"]

    run_id = "mat2-xc/%s" % arm_id
    scene = SC.make_scene(build_id, params, SEED)
    idle, idle_sat = adapter["expiry_state"]()
    scene.begin([float(c) for c in idle])
    sink = RecordingSink()
    tick_holder = [0]
    tracer = ad.SeamTracer(clock=(lambda: now_ms_of(tick_holder[0])),
                           clock_name="injected_ms", run=run_id,
                           build=build_id, sink=sink)

    applied = [float(v) for v in idle]
    saturation = [0.0] * 8
    pending = None
    last_record_tick = None
    expired_ticks = []
    decisions_count = 0
    per_tick = []
    state_chain = []
    events = []
    schedule = probe_events_for(probe)

    for t in range(horizon):
        tick_holder[0] = t
        now_ms = now_ms_of(t)
        if form == "full" or t <= SCRIPT_CUT_TICK:
            # the frozen W08/W10 script (cm law, routed through the
            # accepted tracer) — identical bytes in both forms through
            # tick 4350.
            if t == cm.ms_to_tick(cm.T_START_MS):
                tracer.press("W")
            for lo_ms, hi_ms, counts in (cm.MOUSE_L_WINDOW,
                                         cm.MOUSE_R_WINDOW):
                if lo_ms <= now_ms <= hi_ms and t % 15 == 0:
                    tracer.mouse(counts)
            if t == cm.ms_to_tick(cm.T_KEY_A_MS):
                tracer.press("A")
            if t == cm.ms_to_tick(cm.T_KEY_A_REL_MS):
                tracer.release("A")
            if t == cm.ms_to_tick(cm.T_W_REL_MS):
                tracer.release("W")
            if t == cm.ms_to_tick(cm.T_S_PRESS_MS):
                tracer.press("S")
            if t == cm.ms_to_tick(cm.T_S_REL_MS):
                tracer.release("S")
        # else: form 'cut', t > 4350 — SILENCE (the frozen a12 law).
        for ev_tick, ev_kind, key in schedule:
            if t == ev_tick:
                if ev_kind == "release":
                    tracer.release(key)
                else:
                    tracer.press(key)
                events.append({"probe": (probe or {}).get("kind"),
                               "event": ev_kind, "key": key,
                               "now_ms": now_ms, "tick": t})

        emitted = tracer.tick()
        for rec in emitted:
            v_f, yaw = float(rec.v_forward), float(rec.yaw_rate)
            if rec.record_version != COMMAND_RECORD_VERSION:
                raise RuntimeError("port_record_version")
            if not (0.0 <= v_f <= V_MAX_IN_BAND_M_S):
                raise RuntimeError("port_v_out_of_band:" + repr(v_f))
            if abs(yaw) > OMEGA_MAX_RAD_S:
                raise RuntimeError("port_yaw_out_of_band")
            if int(rec.issued_tick) != (now_ms * PHYSICS_HZ) // 1000:
                raise RuntimeError("port_issued_tick_law")
            proj = adapter["project"](v_f, yaw)
            pending = (proj, t + 1)
            last_record_tick = t
            decisions_count += 1
        if pending is not None and t >= pending[1]:
            applied = [float(v) for v in pending[0]["applied"]]
            saturation = [float(s) for s in pending[0]["saturation"]]
            pending = None
        if adapter["expired"](last_record_tick, t, EXPIRY_TICKS):
            if applied != idle:
                applied = [float(v) for v in idle]
                saturation = [float(s) for s in idle_sat]
                expired_ticks.append({"tick": t,
                                      "age_ticks": (t - int(last_record_tick)
                                                    if last_record_tick
                                                    is not None else -1)})
        rec_pre = scene.observation_record()
        scene.step(np.asarray(applied, dtype=np.float32),
                   np.asarray(saturation, dtype=np.float32))
        ssha = scene.state_sha256()
        state_chain.append(ssha)
        per_tick.append({
            "tick": t, "com_v_m_s": scene.v, "com_x_m": scene.x,
            "phase_left": rec_pre["phase_left"],
            "phase_right": rec_pre["phase_right"],
            "state_sha256": ssha})

    return {
        "arm": arm_id, "run_id": run_id, "form": form, "horizon": horizon,
        "window_rows": [r for r in per_tick if r["tick"] in PRESENT_TICKS],
        "state_chain_len": len(state_chain),
        "decision_count": decisions_count,
        "sink_record_count": len(sink.records),
        "expiry_reverts": expired_ticks,
        "probe_events": events,
        "final_state_sha256": scene.state_sha256(),
    }


def window_identity(rows_a, rows_b):
    """phase_identity_count + first_divergence_tick (prereg section 4)."""
    ident = 0
    first_div = None
    for ra, rb in zip(rows_a, rows_b):
        same = (ra["phase_left"] == rb["phase_left"]
                and ra["phase_right"] == rb["phase_right"])
        if same:
            ident += 1
        elif first_div is None:
            first_div = ra["tick"]
    return ident, first_div


def v_divergence_count(rows_a, rows_b):
    return sum(1 for ra, rb in zip(rows_a, rows_b)
               if ra["com_v_m_s"] != rb["com_v_m_s"])


def band(rows):
    vs = [r["com_v_m_s"] for r in rows]
    return {"min_com_v": min(vs), "com_v_series": vs}
