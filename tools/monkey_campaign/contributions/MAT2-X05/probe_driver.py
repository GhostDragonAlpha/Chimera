#!/usr/bin/env python3
"""MAT2-X05: the probe driver (prereg section 3 — the certified
velocity-perturbation instrument, the sealed WK-LATENCY-20261002 attempt-12
classes VERBATIM, with a PROVEN state channel).

N = 10 pairs = BRAKE-SHORT x5 (n odd) / BRAKE-LONG x5 (n even):
  - the brake arm releases `W` at `T_in(n)`, re-presses at
    `T_in(n) + 150 ticks` (SHORT) / `T_in(n) + 300 ticks` (LONG) on the
    injected clock;
  - the CONTROL arm holds `W` (no extra events).
  Common script bytes through tick 4350, then per-arm; horizon 4800 ticks;
  `T_in(n) = 4351 + (n-1)`.

UNIT RECONCILIATION (recorded, not silent): the frozen prereg phrasing says
"re-press at +150 ms (SHORT) / +300 ms (LONG) on the injected clock"; the
SEALED attempt-12 probe_events (the class definition this card reuses
verbatim — driver_pair_P01/P02, byte-pinned) carry the re-press deltas as
exactly +150 / +300 TICKS (now_ms 14503 -> 15003 and 14506 -> 15506 on the
300 Hz injected clock). This driver reproduces the sealed deltas (the
"classes verbatim" law); the reconciliation is disclosed in every receipt
that cites the class.

The loop body is W10's sealed run_commanded structure (the frozen feed_events
law, the no-teleport RecordingSink, the ZOH pending law, the consumer-side
expiry contract) with the accepted SeamTracer owning the command chains (the
U07 four-stage form; imported, never copied).

Headless, CPU-only, deterministic; numpy only at the scene boundary.
"""
from __future__ import annotations

import numpy as np

PHYSICS_HZ = 300
SEED = 20260920                     # the certified scene seed (continuity)
HORIZON = 4800                      # ticks (prereg section 3)
N_PAIRS = 10
WINDOW_FIRST_TICK = 4351            # T_in(1)

PRESENT_TICKS = list(range(4365, 4666, 15))      # 21 presentation frames
DIAG_TICKS = [4365, 4500, 4650]                  # excluded from attribution
PRESENTED_LAG_MAX = 15                           # the U07 sealed law

SHORT_REPRESS_TICKS = 150
LONG_REPRESS_TICKS = 300


def t_in(n):
    return WINDOW_FIRST_TICK + (n - 1)


def pair_class(n):
    return "BRAKE-SHORT" if n % 2 == 1 else "BRAKE-LONG"


def repress_delta_ticks(cls):
    if cls == "BRAKE-SHORT":
        return SHORT_REPRESS_TICKS
    if cls == "BRAKE-LONG":
        return LONG_REPRESS_TICKS
    raise ValueError("pair_class_unknown:" + cls)


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


def run_arm(arm_id, adapter, build_id, params, *, brake=None, horizon=HORIZON):
    """One commanded execution of the certified line.

    brake: None (the CONTROL arm — holds W) or a dict {"t_in": int,
    "repress_tick": int} (the BRAKE arm: release W at t_in, re-press at
    repress_tick). Identical to the control script through tick t_in - 1
    (common script bytes through tick 4350; the earliest t_in is 4351).
    """
    from tools.policy_compat import scene_cpu as SC      # pinned bytes
    from tools.science_funnel.typeb_export.command_record import (  # pinned
        COMMAND_RECORD_VERSION, V_MAX_IN_BAND_M_S)
    from tools.monkey_campaign.product.input_mapper import (  # pinned
        InputMapper, V_MAX_IN_BAND_M_S as IM_V_MAX,
        OMEGA_MAX_RAD_S, EXPIRY_TICKS)
    import command_model as cm                           # W10 bytes, pinned
    import verify_inputs_x05 as vi5

    it, ad = vi5.load_accepted_trace_modules()
    run_id = "mat2-x05/%s" % arm_id

    scene = SC.make_scene(build_id, params, SEED)
    idle, idle_sat = adapter.expiry_state()
    scene.begin([float(c) for c in idle])
    sink = RecordingSink()
    tick_holder = [0]
    tracer = ad.SeamTracer(clock=(lambda: now_ms_of(tick_holder[0])),
                           clock_name="injected_ms", run=run_id,
                           build=build_id, sink=sink)

    applied = [float(v) for v in idle]
    saturation = [0.0] * 8
    pending = None                       # (projection, apply_from_tick, seq)
    last_record_tick = None
    expired_ticks = []
    decisions = []
    per_tick = []
    state_chain = []
    v_series = []
    x_series = []
    events = []

    for t in range(horizon):
        tick_holder[0] = t
        now_ms = now_ms_of(t)
        # the frozen W08/W10 script (cm law, routed through the accepted
        # tracer) — common bytes through tick 4350, unchanged after on the
        # control arm.
        if t == cm.ms_to_tick(cm.T_START_MS):
            tracer.press("W")
        for lo_ms, hi_ms, counts in (cm.MOUSE_L_WINDOW, cm.MOUSE_R_WINDOW):
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
        if brake is not None:
            if t == brake["t_in"]:
                tracer.release("W")
                events.append({"class": brake["cls"], "event": "release",
                               "key": "W", "now_ms": now_ms, "tick": t})
            elif t == brake["repress_tick"]:
                tracer.press("W")
                events.append({"class": brake["cls"], "event": "press",
                               "key": "W", "now_ms": now_ms, "tick": t})

        emitted = tracer.tick()
        base = len(sink.records) - len(emitted)
        for idx, rec in enumerate(emitted):
            v_f, yaw = float(rec.v_forward), float(rec.yaw_rate)
            if rec.record_version != COMMAND_RECORD_VERSION:
                raise RuntimeError("port_record_version")
            if not (0.0 <= v_f <= V_MAX_IN_BAND_M_S):
                raise RuntimeError("port_v_out_of_band:" + repr(v_f))
            if abs(yaw) > OMEGA_MAX_RAD_S:
                raise RuntimeError("port_yaw_out_of_band")
            # THE MAPPER'S OWN issued_tick LAW (pinned input_mapper._emit):
            # with the tracer path the mapper has no explicit tick_source,
            # so issued_tick = (now_ms * PHYSICS_HZ) // 1000. On the 15-tick
            # poll lattice this equals the loop tick exactly; the frozen
            # brake re-press events are OFF-GRID (now_ms 15003), so the
            # poll grid restarts off the lattice and the mapper's law then
            # reads one tick below the loop tick. The certified law is the
            # mapper's own; this check enforces IT, never the stricter
            # loop-tick identity.
            if int(rec.issued_tick) != (now_ms * PHYSICS_HZ) // 1000:
                raise RuntimeError("port_issued_tick_law")
            seq = base + idx
            proj = adapter.project(v_f, yaw)
            pending = (proj, t + 1, seq, int(rec.issued_tick), t)
            last_record_tick = t
            decisions.append({
                "issued_tick": int(rec.issued_tick),
                "emission_loop_tick": t, "issued_ms": now_ms,
                "v_forward_m_s": v_f, "yaw_rate_rad_s": yaw,
                "requested": proj["requested"], "applied": proj["applied"],
                "saturation": proj["saturation"],
                "brake_script": bool(brake is not None)})
        if pending is not None and t >= pending[1]:
            applied = [float(v) for v in pending[0]["applied"]]
            saturation = [float(s) for s in pending[0]["saturation"]]
            tracer.attach_native_stage(
                pending[2], "simulation_consumed", now_ms,
                {"consumed_tick": t,
                 "issued_tick": pending[3],
                 "emission_loop_tick": pending[4],
                 "applied_minus_emission_ticks": t - pending[4],
                 "applied_head_m_s": float(applied[1])})
            pending = None
        if adapter.expired(last_record_tick, t, EXPIRY_TICKS):
            if applied != idle:
                applied = [float(v) for v in idle]
                saturation = [float(s) for s in idle_sat]
                expired_ticks.append(t)
        rec_pre = scene.observation_record()
        scene.step(np.asarray(applied, dtype=np.float32),
                   np.asarray(saturation, dtype=np.float32))
        ssha = scene.state_sha256()
        v_series.append(scene.v)
        x_series.append(scene.x)
        state_chain.append(ssha)
        per_tick.append({
            "tick": t, "com_v_m_s": scene.v, "com_x_m": scene.x,
            "phase_left": rec_pre["phase_left"],
            "phase_right": rec_pre["phase_right"],
            "yaw_rate_rad_s": rec_pre["yaw_rate"],
            "contact_count": rec_pre["contact_count"],
            "foot_contacts": rec_pre["foot_contacts"],
            "foot_forces": rec_pre["foot_forces"],
            "pad_gaps": rec_pre["pad_gaps"],
            "intervention_reason": rec_pre["intervention_reason"],
            "applied_cmd": applied, "saturation": saturation,
            "trip_l": scene.trip_l, "trip_r": scene.trip_r,
            "state_sha256": ssha})

    n_chains = len(tracer.causal_pairs())
    if n_chains != len(sink.records):
        raise RuntimeError("chain_sink_desync")
    chain_events = tracer.events()
    return {
        "arm": arm_id, "run_id": run_id, "horizon": horizon,
        "per_tick": per_tick, "decisions": decisions,
        "state_chain": state_chain, "v_series": v_series,
        "x_series": x_series, "expiry_reverts": expired_ticks,
        "sink_records": [{"v_forward_m_s": float(r.v_forward),
                          "yaw_rate_rad_s": float(r.yaw_rate),
                          "issued_tick": int(r.issued_tick),
                          "source": str(r.source),
                          "record_version": int(r.record_version)}
                         for r in sink.records],
        "final_state_sha256": scene.state_sha256(),
        "chain_count": n_chains,
        "probe_events": events,
        "chain_events": chain_events,
        "_tracer": tracer,
    }


def seam_facts(res):
    """X-P9's named variables per chain (the L-P6 heritage form): the
    input -> command_emitted latency (<= 50.0 ms) and the consumed lag
    (exactly 1 tick: the zero-order-hold applies the record at the next
    tick boundary after its poll), from the accepted tracer's own event
    records. The mapper's issued_tick rides the record; where the frozen
    off-grid probe events restart the poll lattice off the 15-tick grid,
    the mapper's own issued_tick law reads one tick below the emission
    loop tick (disclosed; the ZOH law is unchanged)."""
    by_seq = {}
    for e in res["chain_events"]:
        by_seq.setdefault(e["seq"], {})[e["stage"]] = e
    facts = []
    for seq in sorted(by_seq):
        stages = by_seq[seq]
        if "input" not in stages or "command_emitted" not in stages:
            raise RuntimeError("seam_stage_missing:seq" + str(seq))
        emit_ms = float(stages["command_emitted"]["t"])
        input_ms = float(stages["input"]["t"])
        consumed = stages.get("simulation_consumed")
        payload = (consumed or {}).get("payload", {})
        consumed_tick = payload.get("consumed_tick")
        emission_loop = payload.get("emission_loop_tick")
        facts.append({
            "seq": int(seq),
            "input_t_ms": input_ms,
            "command_emitted_t_ms": emit_ms,
            "emit_minus_input_ms": emit_ms - input_ms,
            "consumed_tick": consumed_tick,
            "issued_tick": payload.get("issued_tick"),
            "emission_loop_tick": emission_loop,
            "issued_minus_emission_loop_ticks":
                (None if payload.get("issued_tick") is None
                 or emission_loop is None
                 else payload["issued_tick"] - emission_loop),
            "consumed_lag_ticks": (None if consumed_tick is None
                                   or emission_loop is None
                                   else consumed_tick - emission_loop),
        })
    return facts


def run_pair(n, adapter, build_id, params, *, with_control_repeat=True):
    """One brake pair: arms A (brake) + B (control). The CONTROL arm is
    re-executed (X-P1a determinism zero-control); both executions' chains
    are returned when with_control_repeat else only B1."""
    cls = pair_class(n)
    t0 = t_in(n)
    delta = repress_delta_ticks(cls)
    brake = {"t_in": t0, "repress_tick": t0 + delta, "cls": cls}
    a = run_arm("P%02d_%s_A" % (n, cls), adapter, build_id, params,
                brake=brake)
    b1 = run_arm("P%02d_%s_B" % (n, cls), adapter, build_id, params)
    b2 = run_arm("P%02d_%s_B2" % (n, cls), adapter, build_id, params)
    a["_tracer"] = None
    b1["_tracer"] = None
    b2["_tracer"] = None
    return {"n": n, "cls": cls, "t_in": t0,
            "repress_tick": t0 + delta,
            "repress_delta_ticks": delta, "A": a, "B": b1, "B2": b2}


def first_divergence(chain_a, chain_b):
    """The first index where two state chains differ (len(chain_a) if
    identical)."""
    for i, (x, y) in enumerate(zip(chain_a, chain_b)):
        if x != y:
            return i
    if len(chain_a) != len(chain_b):
        return min(len(chain_a), len(chain_b))
    return len(chain_a)
