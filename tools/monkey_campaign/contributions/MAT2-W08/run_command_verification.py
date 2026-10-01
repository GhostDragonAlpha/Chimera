#!/usr/bin/env python3
"""MAT2-W08: the gated command-verification experiment (prereg sections 2-5).

Order is law: pins -> registry -> pin-extract -> re-validate the pinned W04
certificate -> deploy gate ALLOW -> frozen loader + bit-for-bit identity ->
build identity -> the pinned U01 port executes the frozen input script ->
the card-owned adapter projects each record -> the certified scene is
stepped OPEN-LOOP (the registered open-loop pattern) -> the frozen
predictions P1-P9 are evaluated with named variables -> the receipt is
emitted. Three full re-executions: R1 (clean), R2 (determinism zero-control)
and R3 (the wrong-command probe, P9).

Run:  python -B run_command_verification.py
Exit: 0 green / 2 named refusal / 1 failed prediction. CPU only; no engine
process; no training; no snapshot injection between runs.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi          # noqa: E402
import command_model as cm          # noqa: E402

RECEIPTS = HERE / "receipts"
CAPTURE_DIR = HERE / "capture"

SEED = 20260920                     # the certified scene seed (continuity)
HORIZON_R1 = cm.HORIZON             # 10500 ticks
HORIZON_R3 = cm.PROBE_TICK + 1      # 6000 ticks (the probe window)


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


# ---------------------------------------------------------------- stage 1-2
def stage_pins():
    pins = vi.verify()
    reg = vi.verify_registry()
    vi.extract_pinned_tree()
    vi.bootstrap_pinned_imports()
    return pins, reg


# ---------------------------------------------------------------- stage 3-5
def gate_and_load():
    from tools.policy_compat.certificate import (validate_certificate,  # pinned
                                                 check_deploy)
    from tools.policy_compat import runner as R        # pinned bytes
    from tools.policy_compat import scene_cpu          # pinned bytes

    cert = vi.w04_certificate()
    errs = validate_certificate(cert)
    require(not errs, "certificate_validator_violation:" + "; ".join(errs)[:300])
    rel = ("policy_bundle", "physics_build", "runtime_profile",
           "body_domain", "test_suite")
    req = {k: cert["relation"][k] for k in rel}
    allow = check_deploy(req, cert)
    require(allow["decision"] == "ALLOW",
            "deploy_gate_sanity:not_allow:" + allow["decision"])

    bundle = R.load_bundle()
    pb = cert["relation"]["policy_bundle"]
    for field, got, want in (
            ("manifest_hash", bundle["manifest"]["manifest_hash"], pb["manifest_hash"]),
            ("weights", bundle["manifest"]["policy"]["weights_sha256"], pb["weights_sha256"]),
            ("manifest_file_sha256", bundle["manifest_file_sha256"], pb["manifest_file_sha256"]),
            ("weights_file_sha256", bundle["weights_file_sha256"], pb["weights_file_sha256"]),
    ):
        require(got == want, "load_identity_mismatch:" + field)
    for field, got, want in (
            ("architecture", bundle["manifest"]["policy"]["architecture"], pb["architecture"]),
            ("activation", bundle["manifest"]["policy"]["activation"], pb["activation"]),
    ):
        require(got == want, "load_identity_mismatch:" + field)
    require(float(bundle["manifest"]["normalization"].get("clip", 8.0))
            == float(pb["normalization_clip"]),
            "load_identity_mismatch:normalization_clip")

    build_id, params = scene_cpu.build_n()
    phb = cert["relation"]["physics_build"]
    require(build_id == phb["build_id"], "load_identity_mismatch:build_id")
    require(scene_cpu.params_sha(params) == phb["params_sha256"],
            "load_identity_mismatch:params_sha256")
    scene_mod = vi.PINNED_ROOT / "tools" / "policy_compat" / "scene_cpu.py"
    require(sha_bytes(scene_mod.read_bytes()) == phb["scene_module_sha256"],
            "load_identity_mismatch:scene_module_sha256")
    require(params["dt"] == phb["timestep_s"],
            "load_identity_mismatch:timestep_s")

    scene_const = {k: params[k] for k in
                   ("stride_gain", "damping", "warm_damp_lo", "warm_damp_span")}
    bounds = cm.derived_bounds(scene_const, bundle["manifest"])
    gate = {
        "validator": {"violations": [], "verdict": "VALID"},
        "deploy_decision": allow["decision"],
        "bundle_identity": {"manifest_hash": pb["manifest_hash"],
                            "weights_sha256": pb["weights_sha256"],
                            "manifest_file_sha256": pb["manifest_file_sha256"],
                            "weights_file_sha256": pb["weights_file_sha256"],
                            "architecture": pb["architecture"],
                            "activation": pb["activation"],
                            "normalization_clip": pb["normalization_clip"]},
        "physics_build": {"build_id": build_id,
                          "params_sha256": scene_cpu.params_sha(params),
                          "scene_module_sha256": phb["scene_module_sha256"],
                          "timestep_s": params["dt"]},
    }
    return cert, req, allow, bundle, build_id, params, scene_const, bounds, gate


# ---------------------------------------------------------------- stage 6-7
class RecordingSink:
    """The no-teleport law's instrument: the ONLY thing the port can do."""

    def __init__(self):
        self.calls = []
        self.records = []

    def emit(self, record):
        self.calls.append(("emit", record))
        self.records.append(record)
        return len(self.records)


def run_commanded(adapter, build_id, params, *, wrong_override=False,
                  horizon=HORIZON_R1):
    """One FULL re-execution of the frozen commanded sequence.

    The pinned InputMapper produces the records; the frozen adapter projects;
    the certified scene steps. wrong_override=True replaces the record at the
    stop boundary (R3's declared wrong key) — the probe's only difference.
    """
    from tools.policy_compat import scene_cpu as SC      # pinned bytes
    from tools.science_funnel.typeb_export.command_record import (  # pinned
        COMMAND_RECORD_VERSION, V_MAX_IN_BAND_M_S)
    from tools.monkey_campaign.product.input_mapper import (  # pinned
        InputMapper, MockSink, V_MAX_IN_BAND_M_S as IM_V_MAX,
        OMEGA_MAX_RAD_S, INTERVAL_MS, EXPIRY_TICKS)

    require(V_MAX_IN_BAND_M_S == IM_V_MAX,
            "port_ceiling_disagreement:command_record_vs_input_mapper")
    scene = SC.make_scene(build_id, params, SEED)
    idle, idle_sat = adapter.expiry_state()
    scene.begin([float(c) for c in idle])
    sink = RecordingSink()
    mapper = InputMapper(sink, tick_source=lambda: _tick_holder[0])

    applied = [float(v) for v in idle]
    saturation = [0.0] * 8               # the machinery's begin() convention
    pending = None                       # (projection, apply_from_tick)
    last_record_tick = None              # the pinned consumer-expiry contract
    expired_ticks = []                   # ticks reverted to idle by expiry
    decisions = []                       # one row per projected record
    per_tick = []
    state_chain = []                     # per-tick scene.state_sha256()
    v_series = []
    x_series = []
    _tick_holder = [0]

    for t in range(horizon):
        _tick_holder[0] = t
        now_ms = cm.now_ms_of(t)
        if wrong_override and t == cm.WRONG_INJECT_TICK:
            # R3's declared WRONG-KEY script: the wrong operator presses W at
            # the stop boundary and holds it (the clean script's silence and
            # S segment never happen). Identical to R1 through tick 5429.
            mapper.press("W", now_ms=now_ms)
        elif not (wrong_override and t > cm.WRONG_INJECT_TICK):
            cm.feed_events(mapper, t, now_ms)
        emitted = mapper.tick(now_ms)
        if emitted:
            rec = emitted[-1]
            v_f, yaw = float(rec.v_forward), float(rec.yaw_rate)
            require(rec.record_version == COMMAND_RECORD_VERSION,
                    "port_record_version:" + repr(rec.record_version))
            require(0.0 <= v_f <= V_MAX_IN_BAND_M_S,
                    "port_v_out_of_band:" + repr(v_f))
            require(abs(yaw) <= OMEGA_MAX_RAD_S,
                    "port_yaw_out_of_band:" + repr(yaw))
            require(int(rec.issued_tick) == t,
                    "port_issued_tick:" + repr(rec.issued_tick) + ":" + str(t))
            proj = adapter.project(v_f, yaw)
            pending = (proj, t + 1)
            last_record_tick = t
            decisions.append({
                "issued_tick": t, "issued_ms": now_ms,
                "v_forward_m_s": v_f, "yaw_rate_rad_s": yaw,
                "requested": proj["requested"], "applied": proj["applied"],
                "saturation": proj["saturation"],
                "wrong_script": bool(wrong_override and t >= cm.WRONG_INJECT_TICK),
            })
        if pending is not None and t >= pending[1]:
            applied = [float(v) for v in pending[0]["applied"]]
            saturation = [float(s) for s in pending[0]["saturation"]]
            pending = None
        # the pinned expiry contract (is_expired: age > EXPIRY_TICKS): the
        # consumer reverts to the seam's inert path — here the declared idle
        # floor projection (identical to the zero-demand projection).
        if adapter.expired(last_record_tick, t, EXPIRY_TICKS):
            if applied != idle:
                applied = [float(v) for v in idle]
                saturation = [float(s) for s in idle_sat]
                expired_ticks.append(t)
        rec_pre = scene.observation_record()          # PRE-decision telemetry
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
            "state_sha256": ssha,
        })
    return {
        "per_tick": per_tick, "decisions": decisions, "state_chain": state_chain,
        "v_series": v_series, "x_series": x_series,
        "expiry_revert_ticks": expired_ticks,
        "sink_calls": [(c[0], str(c[1])) for c in sink.calls],
        "sink_records": [{"v_forward_m_s": float(r.v_forward),
                          "yaw_rate_rad_s": float(r.yaw_rate),
                          "issued_tick": int(r.issued_tick),
                          "source": str(r.source),
                          "record_version": int(r.record_version)}
                         for r in sink.records],
        "final_state_sha256": scene.state_sha256(),
        "adapter_decisions": adapter.decisions,
    }


# ---------------------------------------------------------------- stage 8
def evaluate(res1, res2, res3, bounds, gate):
    """The frozen predictions P2-P9 with named variables."""
    ev = {}
    pt1 = res1["per_tick"]
    v = res1["v_series"]

    # ---- P2 port seam laws (C12) -------------------------------------------
    recs = res1["sink_records"]
    require(recs, "port_no_records")
    v_vals = [r["v_forward_m_s"] for r in recs]
    y_vals = [abs(r["yaw_rate_rad_s"]) for r in recs]
    issued = [r["issued_tick"] for r in recs]
    seg_diffs = {b - a for a, b in zip(issued, issued[1:])
                 if b - a <= 60}
    contig = sorted(d for d in seg_diffs if d < 30)
    zero_rec = next(r for r in recs if r["v_forward_m_s"] == 0.0
                    and r["issued_tick"] >= cm.TICK_DECAY_MID_ISSUED)
    deadline_tick = (cm.ms_to_tick(cm.T_W_REL_MS + 100))
    silence_a = [r["issued_tick"] for r in recs
                 if cm.SETTLE_ONSET_TICK <= r["issued_tick"] < cm.ms_to_tick(20000)]
    silence_b = [r["issued_tick"] for r in recs if r["issued_tick"] > 6885]
    only_emits = all(c == "emit" for c, _ in res1["sink_calls"])
    ev["P2_port_seam_laws"] = {
        "record_count": len(recs),
        "v_forward_min_m_s": min(v_vals), "v_forward_max_m_s": max(v_vals),
        "yaw_abs_max_rad_s": max(y_vals),
        "contiguous_interval_diffs_ticks": sorted(set(contig)),
        "interval_law_exact": set(contig) == {15},
        "decay_zero_issued_tick": zero_rec["issued_tick"],
        "decay_deadline_tick_bound": deadline_tick,
        "decay_deadline_honored": zero_rec["issued_tick"] <= deadline_tick,
        "idle_silence_decay_to_S_ticks": silence_a,
        "idle_silence_after_S_ticks": silence_b,
        "sink_only_emits": only_emits,
        "no_teleport_law": only_emits,
    }
    p2 = ev["P2_port_seam_laws"]
    require(p2["interval_law_exact"], "prediction_failed:P2_interval_law")
    require(p2["v_forward_min_m_s"] >= 0.0 and p2["v_forward_max_m_s"] <= 0.763625,
            "prediction_failed:P2_v_band")
    require(p2["yaw_abs_max_rad_s"] <= 1.6, "prediction_failed:P2_yaw_bound")
    require(p2["decay_deadline_honored"], "prediction_failed:P2_decay_deadline")
    require(not silence_a and not silence_b, "prediction_failed:P2_idle_silence")
    require(p2["no_teleport_law"], "prediction_failed:P2_no_teleport")

    # ---- P3 projection bounds + named saturation ---------------------------
    dec = res1["decisions"]
    bad = []
    for d in dec:
        for ch, (req_c, app_c, sat_c) in enumerate(
                zip(d["requested"], d["applied"], d["saturation"])):
            lo_exp = [ -0.25, 0.2, 0.2, 0.5, -0.25, 0.2, 0.2, 0.5][ch]
            hi_exp = [0.25, 1.8, 1.8, 2.0, 0.25, 1.8, 1.8, 2.0][ch]
            if not (lo_exp - 1e-9 <= app_c <= hi_exp + 1e-9):
                bad.append((d["issued_tick"], ch))
            expect_sat = 1.0 if abs(app_c - req_c) > 0 else 0.0
            if sat_c != expect_sat:
                bad.append((d["issued_tick"], ch, "sat"))
    floor_rows = [d for d in dec if d["v_forward_m_s"] == 0.0]
    floor_sat_named = all(d["saturation"][1] == 1.0 and d["saturation"][5] == 1.0
                          for d in floor_rows)
    tkl_rows = [d for d in dec if cm.TICK_KEYA_FIRST <= d["issued_tick"]
                <= cm.TICK_KEYA_LAST]
    tkl_sat_named = all(d["saturation"][0] == 1.0 and d["saturation"][4] == 1.0
                        and d["v_forward_m_s"] > 0.0 for d in tkl_rows)
    ev["P3_projection_within_bounds"] = {
        "decisions": len(dec),
        "bounds_violations": bad,
        "floor_rows": len(floor_rows),
        "floor_stride_saturation_named_every_tick": floor_sat_named,
        "seam_max_yaw_rows": len(tkl_rows),
        "seam_max_yaw_saturation_named_every_tick": tkl_sat_named,
        "stride_floor": bounds["stride_floor"],
        "yaw_representable_rad_s": bounds["yaw_representable_rad_s"],
    }
    require(not bad, "prediction_failed:P3_bounds_or_saturation")
    require(floor_sat_named and tkl_sat_named, "prediction_failed:P3_named_saturation")

    # ---- P4 start tracking --------------------------------------------------
    idle_stride = res1["per_tick"][0]["applied_cmd"][1]
    onset = next(t for t in range(cm.TICK_START_ISSUED + 1, len(v))
                 if res1["per_tick"][t]["applied_cmd"][1] != idle_stride)
    band_lo, band_hi = bounds["ceiling_band_m_s"]
    entry = next((t for t in range(cm.TICK_START_ONSET, cm.TICK_CEILING_END + 1)
                  if band_lo <= v[t] <= band_hi), None)
    end_v = v[cm.TICK_CEILING_END]
    resid = abs(end_v - bounds["v_cmd_ceiling_m_s"])
    rise_ok = all(v[t + 1] >= v[t] - 1e-12
                  for t in range(cm.TICK_START_ONSET, cm.TICK_CEILING_END)
                  if v[t] < band_lo)
    range_lo, range_hi = bounds["ceiling_segment_range_m_s"]
    ev["P4_start_tracking"] = {
        "onset_latency_ticks": onset - cm.TICK_START_ISSUED,
        "onset_tick": onset,
        "band_entry_tick_measured": entry,
        "band_m_s": bounds["ceiling_band_m_s"],
        "segment_range_bound_m_s": bounds["ceiling_segment_range_m_s"],
        "v_at_segment_end_m_s": end_v,
        "v_in_derived_range": range_lo - 1e-12 <= end_v <= range_hi + 1e-12,
        "tracking_residual_m_s": resid,
        "tracking_bound_m_s": bounds["ceiling_tracking_bound_m_s"],
        "monotone_rise_below_band": rise_ok,
        "entry_tick_disclosure": "crossing time is warm-path dependent; "
                                 "recorded informationally (prereg P4)",
    }
    p4 = ev["P4_start_tracking"]
    require(p4["onset_latency_ticks"] <= 15, "prediction_failed:P4_onset")
    require(p4["v_in_derived_range"], "prediction_failed:P4_segment_range")
    require(resid <= bounds["ceiling_tracking_bound_m_s"],
            "prediction_failed:P4_tracking_residual")
    require(rise_ok, "prediction_failed:P4_monotone_rise")

    # ---- P5 turn exactness --------------------------------------------------
    def yaw_resid(first_tick, last_tick, expect):
        rows = []
        for t in range(first_tick, last_tick + 1):
            meas = pt1[t + 1]["yaw_rate_rad_s"]   # the record after the step
            rows.append(abs(meas - expect))
        return rows

    eps = 1e-6
    tl = yaw_resid(cm.TICK_MOUSE_L_FIRST + 1, cm.TICK_MOUSE_L_LAST + 15, +0.8)
    tr = yaw_resid(cm.TICK_MOUSE_R_FIRST + 1, cm.TICK_MOUSE_R_LAST + 15, -0.8)
    tkl = yaw_resid(cm.TICK_KEYA_FIRST + 1, cm.TICK_KEYA_LAST + 15, 1.0)
    sat_every = all(pt1[t]["saturation"][0] == 1.0 and pt1[t]["saturation"][4] == 1.0
                    for t in range(cm.TICK_KEYA_FIRST + 1, cm.TICK_KEYA_LAST + 16))
    ev["P5_turn_exactness"] = {
        "bound_rad_s": eps,
        "turn_left_residual_max_rad_s": max(tl),
        "turn_right_residual_max_rad_s": max(tr),
        "seam_max_achieved_rad_s": 1.0,
        "seam_max_residual_rad_s": max(tkl),
        "seam_max_saturation_named_every_tick": sat_every,
        "declared_saturation_residual_rad_s": 0.6,
    }
    require(max(tl) <= eps and max(tr) <= eps, "prediction_failed:P5_in_range_yaw")
    require(max(tkl) <= eps, "prediction_failed:P5_seam_max_yaw")
    require(sat_every, "prediction_failed:P5_seam_max_saturation")

    # ---- P6 decay step -------------------------------------------------------
    mid_v = [v[t] for t in range(cm.TICK_DECAY_MID_ISSUED + 1,
                                 cm.TICK_ZERO_ISSUED + 1)]
    strictly_down = all(b < a for a, b in zip(mid_v, mid_v[1:]))
    ev["P6_speed_step_decay"] = {
        "mid_block_ticks": len(mid_v),
        "mid_demand_m_s": bounds["v_cmd_decay_mid_m_s"],
        "v_at_block_start_m_s": mid_v[0], "v_at_block_end_m_s": mid_v[-1],
        "strictly_decreasing": strictly_down,
        "decay_mid_band_m_s": bounds["decay_mid_band_m_s"],
    }
    require(strictly_down, "prediction_failed:P6_monotone_decay")

    # ---- P7 stop floor settle ------------------------------------------------
    flo_lo, flo_hi = bounds["floor_band_m_s"]
    entry_f = next((t for t in range(cm.SETTLE_ONSET_TICK, HORIZON_R1)
                    if flo_lo <= v[t] <= flo_hi), None)
    down_ok = all(v[t + 1] <= v[t] + 1e-12
                  for t in range(cm.SETTLE_ONSET_TICK, HORIZON_R1 - 1)
                  if v[t] > flo_hi)
    never_below_lo = all(v[t] >= flo_lo - 1e-12
                         for t in range(cm.SETTLE_ONSET_TICK, HORIZON_R1))
    s_lo, s_hi = bounds["settle_end_range_m_s"]
    v_end = v[cm.SETTLE_END]
    tail_ok = all(s_lo - 1e-12 <= v[t] <= s_hi + 1e-12
                  for t in range(cm.SETTLE_END, HORIZON_R1))
    ev["P7_stop_floor_settle"] = {
        "floor_band_m_s": bounds["floor_band_m_s"],
        "settle_end_range_bound_m_s": bounds["settle_end_range_m_s"],
        "settle_end_tick": cm.SETTLE_END,
        "band_entry_tick_measured": entry_f,
        "v_at_settle_end_m_s": v_end,
        "v_in_derived_settle_range": s_lo - 1e-12 <= v_end <= s_hi + 1e-12,
        "tail_within_derived_range_through_horizon": tail_ok,
        "strictly_decreasing_above_band_top": down_ok,
        "never_below_band_low": never_below_lo,
        "v_settled_m_s": v[-1],
        "entry_tick_disclosure": "crossing time is warm-path dependent; "
                                 "recorded informationally (prereg P7)",
    }
    require(down_ok, "prediction_failed:P7_monotone_above_band")
    require(never_below_lo, "prediction_failed:P7_floor_invariant")
    require(s_lo - 1e-12 <= v_end <= s_hi + 1e-12,
            "prediction_failed:P7_settle_range")
    require(tail_ok, "prediction_failed:P7_settle_tail")

    # ---- P8 stability bars ---------------------------------------------------
    env = bounds["velocity_envelope_m_s"]
    xs = res1["x_series"]
    bad_env = [t for t, vv in enumerate(v) if abs(vv) > env]
    bad_contact = [t["tick"] for t in pt1 if t["contact_count"] < 2]
    bad_nan = [t["tick"] for t in pt1
               if not (np.isfinite(t["com_v_m_s"]) and np.isfinite(t["com_x_m"])
                       and all(np.isfinite(t["applied_cmd"]))
                       and all(np.isfinite(t["saturation"])))]
    bad_interv = [t["tick"] for t in pt1 if t["intervention_reason"] != "none"]
    bad_x = [t for t in range(1, len(xs)) if xs[t] < xs[t - 1] - 1e-15]
    bad_gap = [t["tick"] for t in pt1
               if any(g <= 0 for pair in t["pad_gaps"].values() for g in pair)]
    min_contact = min(t["contact_count"] for t in pt1)
    trip_vals = sorted(set([t["trip_l"] for t in pt1] + [t["trip_r"] for t in pt1]))
    trips_fired = any(x > 0 for x in trip_vals)
    ev["P8_stability_bars"] = {
        "velocity_envelope_m_s": env,
        "envelope_violation_ticks": bad_env,
        "contact_floor_min_observed": min_contact,
        "contact_floor_violation_ticks": bad_contact,
        "nonfinite_ticks": bad_nan,
        "intervention_violation_ticks": bad_interv,
        "x_decrease_ticks": bad_x,
        "nonpositive_gap_ticks": bad_gap,
        "trip_counter_values_observed": trip_vals,
        "trips_fired": trips_fired,
        "named_variable_note": "every bar per tick; a violation is a refusal",
    }
    require(not bad_env, "prediction_failed:P8_velocity_envelope")
    require(not bad_contact, "prediction_failed:P8_contact_floor")
    require(not bad_nan, "prediction_failed:P8_no_nan_inf")
    require(not bad_interv, "prediction_failed:P8_no_intervention")
    require(not bad_x, "prediction_failed:P8_no_reverse_slide")
    require(not bad_gap, "prediction_failed:P8_no_penetration")

    # ---- P9 wrong-command MUST FIRE -----------------------------------------
    ch1, ch2, ch3 = res1["state_chain"], res2["state_chain"], res3["state_chain"]
    inj = cm.WRONG_INJECT_TICK
    zero_ctrl = ch1 == ch2
    prefix_eq = ch3[:inj + 1] == ch1[:inj + 1]
    diverged_at = next((t for t in range(inj + 1, len(ch3))
                        if ch3[t] != ch1[t]), None)
    v3 = res3["v_series"]
    v3_probe = v3[cm.PROBE_TICK]
    v1_probe = v[cm.PROBE_TICK]
    v_prefix = v[inj]
    d_hi = bounds["d_hi_per_s"]
    d_lo = bounds["d_lo_per_s"]
    steps_probe = cm.PROBE_TICK - inj          # 568/569 steps post-injection
    import math as _math
    band_lo_ceiling = bounds["ceiling_band_m_s"][0]      # a/d_hi
    r3_low = band_lo_ceiling + (v_prefix - band_lo_ceiling) * _math.exp(
        -d_hi * steps_probe / 300.0)
    r1_up = flo_hi + (v_prefix - flo_hi) * _math.exp(-d_lo * steps_probe / 300.0)
    sep_ok = v3_probe >= r3_low and v1_probe <= r1_up and v3_probe > v1_probe
    ev["P9_wrong_command_response"] = {
        "injection_tick": inj,
        "zero_control_bit_identical": zero_ctrl,
        "prefix_identical_through_injection": prefix_eq,
        "first_divergent_tick": diverged_at,
        "divergence_detected": diverged_at == inj + 1,
        "v_prefix_shared_m_s": v_prefix,
        "probe_steps": steps_probe,
        "r3_lower_bound_m_s": r3_low,
        "r1_upper_bound_m_s": r1_up,
        "v_probe_wrong_run_m_s": v3_probe,
        "v_probe_clean_run_m_s": v1_probe,
        "physical_separation_proven": sep_ok,
        "ceiling_band_m_s": bounds["ceiling_band_m_s"],
    }
    require(zero_ctrl, "prediction_failed:P9_zero_control")
    require(prefix_eq, "prediction_failed:P9_prefix")
    require(diverged_at == inj + 1, "prediction_failed:P9_divergence")
    require(sep_ok, "prediction_failed:P9_physical_separation")
    return ev


def main() -> int:
    pins, reg = stage_pins()
    (cert, req, allow, bundle, build_id, params,
     scene_const, bounds, gate) = gate_and_load()

    from tools.policy_compat import scene_cpu as SC  # pinned bytes
    require(SC.params_sha(params) == gate["physics_build"]["params_sha256"],
            "build_drift")

    adapter = cm.CommandAdapter(bundle["manifest"], scene_const)
    res1 = run_commanded(adapter, build_id, params, horizon=HORIZON_R1)
    adapter2 = cm.CommandAdapter(bundle["manifest"], scene_const)
    res2 = run_commanded(adapter2, build_id, params, horizon=HORIZON_R1)
    adapter3 = cm.CommandAdapter(bundle["manifest"], scene_const)
    res3 = run_commanded(adapter3, build_id, params, wrong_override=True,
                         horizon=HORIZON_R3)

    ev = evaluate(res1, res2, res3, bounds, gate)

    # the command-verification table (prereg 4.3) — named variables only
    v = res1["v_series"]
    table = [
        {"command": "start_ceiling_hold", "issued_tick": cm.TICK_START_ISSUED,
         "tracking_residual_m_s": ev["P4_start_tracking"]["tracking_residual_m_s"],
         "tracking_bound_m_s": bounds["ceiling_tracking_bound_m_s"],
         "stability": "P8 bars green every tick",
         "wrong_command_probe": "onset latency %d <= 15" % ev["P4_start_tracking"]["onset_latency_ticks"]},
        {"command": "turn_left_in_range", "issued_ticks": [cm.TICK_MOUSE_L_FIRST, cm.TICK_MOUSE_L_LAST],
         "tracking_residual_rad_s": ev["P5_turn_exactness"]["turn_left_residual_max_rad_s"],
         "tracking_bound_rad_s": 1e-6,
         "stability": "P8 bars green; speed claim continues",
         "wrong_command_probe": "FB7 bite fires on mirrored sign"},
        {"command": "turn_right_in_range", "issued_ticks": [cm.TICK_MOUSE_R_FIRST, cm.TICK_MOUSE_R_LAST],
         "tracking_residual_rad_s": ev["P5_turn_exactness"]["turn_right_residual_max_rad_s"],
         "tracking_bound_rad_s": 1e-6,
         "stability": "P8 bars green",
         "wrong_command_probe": "FB7 bite fires on mirrored sign"},
        {"command": "turn_left_seam_max_saturating", "issued_ticks": [cm.TICK_KEYA_FIRST, cm.TICK_KEYA_LAST],
         "tracking_residual_rad_s": ev["P5_turn_exactness"]["seam_max_residual_rad_s"],
         "declared_saturation_residual_rad_s": 0.6,
         "stability": "P8 bars green; saturation named ch0/ch4",
         "wrong_command_probe": "n/a (saturating row is itself the named clip)"},
        {"command": "speed_step_decay_mid", "issued_tick": cm.TICK_DECAY_MID_ISSUED,
         "measured": {"v_start_m_s": ev["P6_speed_step_decay"]["v_at_block_start_m_s"],
                      "v_end_m_s": ev["P6_speed_step_decay"]["v_at_block_end_m_s"]},
         "stability": "P8 bars green; strictly decreasing",
         "wrong_command_probe": "P9 class at the stop boundary"},
        {"command": "stop_zero_advance_floor", "issued_tick": cm.TICK_ZERO_ISSUED,
         "v_at_settle_end_m_s": ev["P7_stop_floor_settle"]["v_at_settle_end_m_s"],
         "settle_end_range_bound_m_s": ev["P7_stop_floor_settle"]["settle_end_range_bound_m_s"],
         "floor_band_m_s": bounds["floor_band_m_s"],
         "stability": "P8 bars green; stride saturation named ch1/ch5",
         "wrong_command_probe": "P9 MUST-FIRE injected at this boundary"},
        {"command": "wrong_command_probe_R3", "injection_tick": cm.WRONG_INJECT_TICK,
         "zero_control_bit_identical": ev["P9_wrong_command_response"]["zero_control_bit_identical"],
         "first_divergent_tick": ev["P9_wrong_command_response"]["first_divergent_tick"],
         "physical_separation_proven": ev["P9_wrong_command_response"]["physical_separation_proven"],
         "stability": "n/a (probe arm)",
         "wrong_command_probe": "FIRED (the falsifier class executed)"},
    ]

    receipt = {
        "schema": "chimera.w08_command_verification.v1",
        "task_id": "W08",
        "card_id": "MAT2-W08",
        "attempt_id": vi.ATTEMPT_ID,
        "agent_id": vi.AGENT_ID,
        "base_sha256": vi.BASE_SHA,
        "criteria_sha256": vi.CRITERIA_SHA256,
        "preregistration_sha256": vi.prereg_sha256(),
        "registry": reg,
        "gate": gate,
        "seed": SEED,
        "horizons": {"R1_R2_ticks": HORIZON_R1, "R3_ticks": HORIZON_R3},
        "derived_bounds": bounds,
        "predictions": ev,
        "command_table": table,
        "runs": {
            "R1_final_state_sha256": res1["final_state_sha256"],
            "R2_final_state_sha256": res2["final_state_sha256"],
            "R3_final_state_sha256": res3["final_state_sha256"],
            "R1_chain_sha256": sha_bytes(
                json.dumps(res1["state_chain"], sort_keys=True).encode()),
            "R2_chain_sha256": sha_bytes(
                json.dumps(res2["state_chain"], sort_keys=True).encode()),
            "R1_records": len(res1["per_tick"]),
            "port_records": len(res1["sink_records"]),
            "adapter_decisions": res1["adapter_decisions"],
        },
        "named_missing": {
            "N1_vertical_fall_channel": "NAMED_MISSING (surrogate scope; "
                "trip channels measured: %s)" % ev["P8_stability_bars"]["trips_fired"],
            "N2_c09_ledger_and_settle_limits": "NAMED_MISSING for the C09 "
                "ledger/episode caps; P06 stability-settle-vy-ms 0.05 m/s "
                "quoted and NOT applicable to the declared bounded floor band "
                "(the plant's minimum advance exceeds it by declaration); "
                "P06 simulation-tick-hz 300 == the scene dt (verified)",
            "N3_product_engine_live_control_path": "carried NAMED_MISSING "
                "from the pinned spike evidence",
            "N4_trained_bundles": "BLOCK at the gate; nothing trained loaded",
        },
        "pins": {"count": len(pins)},
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_command_verification.py"},
        "pass": True,
    }

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / "command_verification_receipt.json").write_bytes(
        canonical(receipt) + b"\n")
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    (CAPTURE_DIR / "trace_commanded.json").write_bytes(
        canonical({
            "schema": "chimera.w08_commanded_trace.v1",
            "seed": SEED,
            "build_id": build_id,
            "derived_bounds": bounds,
            "per_tick": res1["per_tick"],
            "decisions": res1["decisions"],
            "sink_records": res1["sink_records"],
        }) + b"\n")
    print("PASS: all frozen predictions green")
    print("R1 final:", res1["final_state_sha256"][:16],
          "| zero-control identical:", ev["P9_wrong_command_response"]["zero_control_bit_identical"])
    print("table rows:", len(table))
    return 0


if __name__ == "__main__":
    sys.exit(main())
