#!/usr/bin/env python3
"""MAT2-U07: the four-stage one-clock controls harness (prereg sections 2-3).

The frozen W08/W10 open-loop form, instrumented: the ACCEPTED SeamTracer
(I-U07-TRACE-FOLLOWUP adapter.py, PR #145 bytes, imported — never copied)
drives the pinned InputMapper on ONE injected integer-millisecond clock and
emits the two Python-observable stages; THIS harness attaches the two
declared native-stage observations of the certified CPU line through the
adapter's own `attach_native_stage` entry point (its designed extension
point for a live integrator):

    input -> command_emitted        <- emitted by the imported SeamTracer
    simulation_consumed             <- the scene.step that zero-order-holds
                                       the record (issued_tick + 1), a REAL
                                       observation of the certified line
    presented                       <- the declared CPU-line frame record of
                                       the records-only renderer for the
                                       declared render window (prereg 3;
                                       absent inventory A1 names the native
                                       engine piece that does NOT exist)

The loop body is W10's sealed run_commanded structure (feed_events law,
no-teleport RecordingSink, ZOH pending law, consumer-side expiry contract)
with camera/focus/policy state carrying NO channel into the physics:
scene.step(applied, saturation) is the only motion path (physics charter).

Headless, CPU-only, deterministic; numpy only at the scene boundary.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

CLOCK_ID = "injected_ms"
BUILD_ID = "cpu-walk-scene-build-N"
SEED = 20260920                     # the certified scene seed (continuity)
HORIZON_R1 = 10500                  # ticks (W10's declared R1 horizon)
HORIZON_R3 = 6000                   # W10's declared probe window
HORIZON_R4 = 1200                   # the expiry-hold arm
HORIZON_R5 = 2400                   # the focus-loss arm

# The declared render window (prereg section 3, camera arms): the bounded
# tick interval whose chains carry REAL presented events; stride 15 ticks =
# one frame per seam poll. Frozen BEFORE the run. Consumed ticks in this
# window are {4351, 4366, ..., 4651}; presentation frames at 4365..4665
# step 15 cover every one of them (f >= c; lag <= 15 ticks).
WINDOW = (4350, 4666)               # [W0, W1) consumed ticks
WINDOW_STRIDE = 15                  # ticks per presented frame
PRESENTED_LAG_TICKS_MAX = 300       # P3 bound (declared render bookkeeping)

R4_PRESS_TICK = 300                 # the expiry-hold press (on the grid)
R4_RELEASE_TICK = 600               # AMENDMENT-A2: release, then silence
R5_PRESS_TICK = 300
R5_BLUR_TICK = 600                  # now_ms 2000
R5_DROPPED_PRESS_TICK = 900         # now_ms 3000 (blurred; must be dropped)
R5_FOCUS_TICK = 1200                # now_ms 4000
R5_RECOVER_PRESS_TICK = 1500        # now_ms 5000 (a NEW chain)


def require(condition, code):
    if not condition:
        raise RuntimeError("REFUSAL:" + str(code))


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def now_ms_of(tick: int) -> int:
    """The injected integer-millisecond clock for a physics tick."""
    return (int(tick) * 1000) // 300


def load_accepted_modules():
    """Import the ACCEPTED trace module and adapter, never copies.

    Both load from THIS card's byte-verified pin extraction; the adapter's
    own identity assertions (ACCEPTED_SHA256 / PINNED_SHA256) run inside it.
    """
    import verify_inputs_u07 as vi7
    it = vi7.load_pinned_module(
        "u07_accepted_input_trace",
        ("tools", "monkey_campaign", "contributions", "I-U07-TRACE",
         "input_trace.py"))
    ad = vi7.load_pinned_module(
        "u07_accepted_adapter",
        ("tools", "monkey_campaign", "contributions", "I-U07-TRACE-FOLLOWUP",
         "adapter.py"))
    return it, ad


class RecordingSink:
    """The no-teleport law's instrument (W10's sealed form, verbatim role):
    the ONLY thing the port can do."""

    def __init__(self):
        self.calls = []
        self.records = []

    def emit(self, record):
        self.calls.append(("emit", str(record)))
        self.records.append(record)
        return len(self.records)


def projected_consumption_tick(issued_tick: int) -> int:
    """The ZOH boundary: a record issued at tick b applies to steps b+1.."""
    return issued_tick + 1


def run_arm(arm_id, adapter, build_id, params, *, script="full",
            horizon=HORIZON_R1, focus=None):
    """One commanded execution of the certified line, four-stage traced.

    script: "full" (R1/R2 frozen W08/W10 script), "wrong" (R3 wrong-key
    script, W10 semantics verbatim), "hold" (R4: one press, never released,
    no further input — the consumer expiry contract must revert).
    focus: R5 only — a dict carrying the FOCUS POLICY (pinned U03 layer);
    the policy owns press/release routing (blurred intents are dropped and
    named BY the policy).
    """
    from tools.policy_compat import scene_cpu as SC      # pinned bytes
    from tools.science_funnel.typeb_export.command_record import (  # pinned
        COMMAND_RECORD_VERSION, V_MAX_IN_BAND_M_S)
    from tools.monkey_campaign.product.input_mapper import (  # pinned
        OMEGA_MAX_RAD_S, EXPIRY_TICKS)
    import command_model as cm                           # W10 bytes, pinned

    it, ad = load_accepted_modules()
    run_id = "mat2-u07-controls/%s" % arm_id

    scene = SC.make_scene(build_id, params, SEED)
    idle, idle_sat = adapter.expiry_state()
    scene.begin([float(c) for c in idle])
    sink = RecordingSink()

    _now = {"ms": 0}
    if focus is not None:
        # R5: the pinned U03 policy owns the mapper (its own factory wiring);
        # the SeamTracer is NOT in this path — R5's accepted-format record is
        # emitted by the driver and its declared missing-stage refusal is the
        # honest latency state (the FOLLOWUP precedent).
        tracer = None
    else:
        tracer = ad.SeamTracer(clock=(lambda: _now["ms"]),
                               clock_name=CLOCK_ID, run=run_id,
                               build=build_id, sink=sink)

    applied = [float(v) for v in idle]
    saturation = [0.0] * 8
    pending = None                       # (projection, apply_from_tick, seq)
    last_record_tick = None
    expired_ticks = []                   # consumer-side expiry reverts
    first_revert_age = None
    last_revert_age = None
    decisions = []
    per_tick = []
    state_chain = []
    v_series = []
    x_series = []
    focus_drop_snapshot = None
    focus_state_tail = []

    for t in range(horizon):
        _now["ms"] = now_ms_of(t)
        now_ms = _now["ms"]
        prev_sink = len(sink.records)
        if focus is not None:
            # R5: the focus policy routes every intent; blurred presses are
            # dropped and named by the policy itself. The policy is built
            # HERE against THIS arm's recording sink (one emission path);
            # its mapper tick source rides THIS loop's tick.
            if "policy" not in focus:
                focus["policy"], focus["tick_holder"] = \
                    focus["policy_builder"](sink)
            if "tick_holder" in focus:
                focus["tick_holder"][0] = t
            if t == focus["press_tick"]:
                focus["policy"].press("W", now_ms=now_ms)
            elif t == focus["blur_tick"]:
                focus["policy"].on_blur(now_ms)
            elif t == focus["dropped_press_tick"]:
                focus["policy"].press("S", now_ms=now_ms)   # must be dropped
                focus_drop_snapshot = {
                    "tick": t, "now_ms": now_ms,
                    "state": focus["policy"].state,
                    "gate_stats": dict(focus["policy"].gate_stats),
                    "last_trace": {k: list(v) for k, v in
                                   focus["policy"].last_trace.items()}}
            elif t == focus["focus_tick"]:
                focus["policy"].on_focus(now_ms)
            elif t == focus["recover_press_tick"]:
                focus["policy"].press("S", now_ms=now_ms)   # a NEW chain
            emitted = focus["policy"].tick(now_ms)
            if t >= focus["recover_press_tick"]:
                focus_state_tail.append({
                    "tick": t, "state": focus["policy"].state,
                    "gate_stats": dict(focus["policy"].gate_stats)})
        elif script == "hold":
            # AMENDMENT-A2: the seam RE-ISSUES a held key at every poll, so
            # the expiry law guards the SILENT stream: press, RELEASE, then
            # silence; the last (exact-zero) record goes stale and the
            # consumer must revert at age 31.
            if t == R4_PRESS_TICK:
                tracer.press("W")
            elif t == R4_RELEASE_TICK:
                tracer.release("W")
        elif script == "wrong":
            if t == cm.WRONG_INJECT_TICK:
                # R3's declared WRONG-KEY script (W10 semantics verbatim):
                # the wrong operator presses W at the stop boundary and
                # holds it; identical to R1 through tick 5429.
                tracer.press("W")
            elif t > cm.WRONG_INJECT_TICK:
                pass  # the clean script's silence and S segment never happen
            else:
                _feed_events_traced(tracer, cm, t, now_ms)
        else:
            _feed_events_traced(tracer, cm, t, now_ms)

        if focus is not None:
            # The policy path's chain truth is the SINK (the expiry gate may
            # drop records the mapper emitted; a dropped record never opens a
            # consumed chain).
            emitted = sink.records[prev_sink:]
        else:
            emitted = tracer.tick()

        base = prev_sink
        for idx, rec in enumerate(emitted):
            v_f, yaw = float(rec.v_forward), float(rec.yaw_rate)
            require(rec.record_version == COMMAND_RECORD_VERSION,
                    "port_record_version:" + repr(rec.record_version))
            require(0.0 <= v_f <= V_MAX_IN_BAND_M_S,
                    "port_v_out_of_band:" + repr(v_f))
            require(abs(yaw) <= OMEGA_MAX_RAD_S,
                    "port_yaw_out_of_band:" + repr(yaw))
            require(int(rec.issued_tick) == t,
                    "port_issued_tick:" + repr(rec.issued_tick) + ":" + str(t))
            # the chains and the sink records are appended one-to-one, in
            # order, by the adapter's TraceSink hook: this record's sink
            # position IS its chain seq (asserted once at arm end).
            seq = base + idx
            proj = adapter.project(v_f, yaw)
            pending = (proj, projected_consumption_tick(t), seq)
            last_record_tick = t
            decisions.append({
                "issued_tick": t, "issued_ms": now_ms,
                "v_forward_m_s": v_f, "yaw_rate_rad_s": yaw,
                "requested": proj["requested"], "applied": proj["applied"],
                "saturation": proj["saturation"],
                "wrong_script": bool(script == "wrong"
                                     and t >= cm.WRONG_INJECT_TICK),
            })
        if pending is not None and t >= pending[1]:
            applied = [float(v) for v in pending[0]["applied"]]
            saturation = [float(s) for s in pending[0]["saturation"]]
            # REAL observation: this scene.step consumes the record issued
            # at t-1 — the certified line's ZOH boundary on the SAME clock.
            if tracer is not None:
                tracer.attach_native_stage(
                    pending[2], "simulation_consumed", now_ms_of(t),
                    {"consumed_tick": t, "issued_tick": t - 1,
                     "applied_head_m_s": float(applied[1])})
            pending = None
        if adapter.expired(last_record_tick, t, EXPIRY_TICKS):
            if applied != idle:
                applied = [float(v) for v in idle]
                saturation = [float(s) for s in idle_sat]
                age = t - int(last_record_tick)
                expired_ticks.append({"tick": t, "age_ticks": age,
                                      "last_record_tick":
                                      int(last_record_tick)})
                if first_revert_age is None:
                    first_revert_age = age
                last_revert_age = age
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

    if tracer is not None:
        n_chains = len(tracer.causal_pairs())
        require(n_chains == len(sink.records),
                "chain_sink_desync:" + str(n_chains) + ":"
                + str(len(sink.records)))
    else:
        n_chains = len(sink.records)
    return {
        "arm": arm_id, "run_id": run_id, "horizon": horizon,
        "per_tick": per_tick, "decisions": decisions,
        "state_chain": state_chain, "v_series": v_series,
        "x_series": x_series, "expiry_reverts": expired_ticks,
        "first_revert_age_ticks": first_revert_age,
        "last_revert_age_ticks": last_revert_age,
        "sink_records": [{"v_forward_m_s": float(r.v_forward),
                          "yaw_rate_rad_s": float(r.yaw_rate),
                          "issued_tick": int(r.issued_tick),
                          "source": str(r.source),
                          "record_version": int(r.record_version)}
                         for r in sink.records],
        "final_state_sha256": scene.state_sha256(),
        "chain_count": n_chains,
        "focus_drop_snapshot": focus_drop_snapshot,
        "focus_state_tail": focus_state_tail,
        "_tracer": tracer, "_accepted_trace": it, "_adapter_mod": ad,
        "_expiry_ticks_const": EXPIRY_TICKS,
    }


def _feed_events_traced(tracer, cm, tick: int, now_ms: int) -> None:
    """W10's frozen feed_events law, routed through the ACCEPTED tracer
    (the tracer reads its own one clock; the mapper is the only producer)."""
    if tick == cm.ms_to_tick(cm.T_START_MS):
        tracer.press("W")
    for lo_ms, hi_ms, counts in (cm.MOUSE_L_WINDOW, cm.MOUSE_R_WINDOW):
        if lo_ms <= now_ms <= hi_ms and tick % 15 == 0:
            tracer.mouse(counts)
    if tick == cm.ms_to_tick(cm.T_KEY_A_MS):
        tracer.press("A")
    if tick == cm.ms_to_tick(cm.T_KEY_A_REL_MS):
        tracer.release("A")
    if tick == cm.ms_to_tick(cm.T_W_REL_MS):
        tracer.release("W")
    if tick == cm.ms_to_tick(cm.T_S_PRESS_MS):
        tracer.press("S")
    if tick == cm.ms_to_tick(cm.T_S_REL_MS):
        tracer.release("S")


# ------------------------------------------------------------------ analysis
def normalize_events(events, run_id=None):
    """The declared P5 normalization: drop (or pin) the per-arm run field."""
    out = []
    for e in events:
        e = dict(e)
        if run_id is not None:
            e["run"] = run_id
        else:
            e.pop("run", None)
        out.append(e)
    return out


def command_seqs(res):
    """All chain seqs, from the public event list (never private state)."""
    return sorted({e["seq"] for e in res["_tracer"].events()
                   if e["stage"] == "command_emitted"})


def first_response_seqs(res, seqs=None):
    """The FIRST chain under each input transition (the amended P1 subset):
    for every transition_index, the smallest seq sharing it."""
    events = res["_tracer"].events()
    if seqs is not None:
        keep = set(seqs)
        events = [e for e in events if e["seq"] in keep]
    first = {}
    for e in events:
        if e["stage"] == "input":
            tidx = e["payload"].get("transition_index")
            if tidx is not None and tidx not in first:
                first[tidx] = e["seq"]
    return sorted(first.values())


def same_boundary_chains(res, seqs=None):
    """Chains whose input transition was observed at the SAME boundary poll
    (input.t == command_emitted.t): the fresh-transition subset. Mouse-only
    re-issues inherit the held key's older transition (the accepted
    adapter's declared antecedent law) and are excluded here."""
    events = res["_tracer"].events()
    if seqs is not None:
        keep = set(seqs)
        events = [e for e in events if e["seq"] in keep]
    by_seq = {}
    for e in events:
        by_seq.setdefault(e["seq"], {})[e["stage"]] = e
    fresh = []
    for seq in sorted(by_seq):
        st = by_seq[seq]
        if "input" in st and "command_emitted" in st \
                and st["input"]["t"] == st["command_emitted"]["t"]:
            fresh.append(seq)
    return sorted(set(fresh))


def window_chains(res):
    """The declared render window's chains: consumed event EXISTS (a real
    simulation_consumed observation) and its consumed tick is in [W0, W1)."""
    w0, w1 = WINDOW
    consumed = {}
    for e in res["_tracer"].events():
        if e["stage"] == "simulation_consumed":
            consumed[e["seq"]] = int(e["payload"]["consumed_tick"])
    return sorted(seq for seq, tick in consumed.items() if w0 <= tick < w1)


def attach_presented_stage(res, frames):
    """Attach the REAL presented observations: one per rendered frame.

    frames: list of {"seq", "consumed_tick", "presented_tick", "frame_id",
    "view"} produced by the render driver. presented_tick is the declared
    stride tick whose frame record contains that consumed tick.
    """
    tracer = res["_tracer"]
    for f in frames:
        tracer.attach_native_stage(int(f["seq"]), "presented",
                                   now_ms_of(int(f["presented_tick"])),
                                   {"frame_id": f["frame_id"],
                                    "view": f["view"],
                                    "presented_tick": int(f["presented_tick"]),
                                    "consumed_tick": int(f["consumed_tick"])})
    return frames


def events_for_seqs(res, seqs):
    keep = set(seqs)
    return [e for e in res["_tracer"].events() if e["seq"] in keep]


def segment_stats(res, seqs=None):
    """P1/P2/P4 variables over the requested chains (default: all chains).

    Every number here is derived from the accepted-format events; ticks are
    converted with the frozen 300 Hz law (1000/300 ms per tick); nothing is
    asserted to be a wall-clock. P1 is the AMENDED A1 law: the FIRST chain
    under each input transition must respond within INTERVAL_MS; re-issued
    chains share the antecedent (the accepted adapter's declared law) and
    their input->command distance is the hold age, recorded informationally.
    """
    events = res["_tracer"].events()
    if seqs is not None:
        keep = set(seqs)
        events = [e for e in events if e["seq"] in keep]
    by_seq = {}
    for e in events:
        by_seq.setdefault(e["seq"], {})[e["stage"]] = e
    seg_ic, first_by_transition, lags, polls = [], {}, [], []
    for seq in sorted(by_seq):
        st = by_seq[seq]
        if "input" in st and "command_emitted" in st:
            gap = st["command_emitted"]["t"] - st["input"]["t"]
            seg_ic.append(gap)
            tidx = st["input"]["payload"].get("transition_index")
            if tidx is not None:
                best = first_by_transition.get(tidx)
                if best is None or gap < best:
                    first_by_transition[tidx] = gap
        if "command_emitted" in st and "simulation_consumed" in st:
            issued = int(st["command_emitted"]["payload"]["issued_tick"])
            consumed = int(st["simulation_consumed"]["payload"]
                           ["consumed_tick"])
            lags.append(consumed - issued)
        if "command_emitted" in st:
            polls.append(st["command_emitted"]["t"])
    polls_sorted = sorted(polls)
    poll_periods = [b - a for a, b in zip(polls_sorted, polls_sorted[1:])
                    if b - a <= 60]
    first_responses = sorted(first_by_transition.values())
    return {"chains": len(by_seq),
            "seg_input_to_command_ms": seg_ic,
            "seg_input_to_command_ms_max": max(seg_ic) if seg_ic else None,
            "transitions": len(first_by_transition),
            "first_response_ms": first_responses,
            "first_response_ms_max": (max(first_responses)
                                      if first_responses else None),
            "consumed_lag_ticks": lags,
            "consumed_lag_ticks_max": max(lags) if lags else None,
            "poll_periods_ms": sorted(set(poll_periods)),
            "poll_period_ms_max": max(poll_periods) if poll_periods else None}


def presented_lags(frames):
    lags = [int(f["presented_tick"]) - int(f["consumed_tick"])
            for f in frames]
    return {"presented_lag_ticks": lags,
            "presented_lag_ticks_max": max(lags) if lags else None}


def accepted_latency_summary(res, seqs, limits):
    """The accepted module's own summary over the COMPLETE chains.

    `limits` is caller data (the P06 frozen laws) — never a default. A
    refused trace produces NO latency output (the accepted module's law).
    """
    it = res["_accepted_trace"]
    events = events_for_seqs(res, seqs)
    parsed = it.parse_trace(events)
    return it.summarize(parsed, limits=limits)


def wrong_command_response(res1, res3):
    """P6: the wrong-key script's trace-level response vs the baseline."""
    import command_model as cm
    cut_tick = cm.WRONG_INJECT_TICK
    r1_after = [d for d in res1["decisions"] if d["issued_tick"] >= cut_tick]
    r3_after = [d for d in res3["decisions"] if d["issued_tick"] >= cut_tick]
    r3_wrong = [d for d in r3_after if d["wrong_script"]]
    return {
        "cut_tick": cut_tick,
        "r1_records_after_cut": len(r1_after),
        "r1_max_v_after_cut_m_s": max((d["v_forward_m_s"]
                                       for d in r1_after), default=None),
        "r3_records_after_cut": len(r3_after),
        "r3_wrong_flagged": len(r3_wrong),
        "r3_min_v_after_cut_m_s": min((d["v_forward_m_s"]
                                       for d in r3_after), default=None),
        "r3_all_wrong_flagged": len(r3_wrong) == len(r3_after)
        and len(r3_after) > 0,
        "r3_demand_positive": bool(r3_wrong)
        and all(d["v_forward_m_s"] > 0.0 for d in r3_wrong),
    }
