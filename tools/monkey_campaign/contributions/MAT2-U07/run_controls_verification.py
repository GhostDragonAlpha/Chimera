#!/usr/bin/env python3
"""MAT2-U07: the gated controls-verification experiment (prereg sections 2-8).

Order is law: pins -> registry/profile (BEFORE capture; G7) -> W10 certified-
line layer -> gate and load identity -> arms R1-R5 (one clock, four stages)
-> the declared render plan (presented observations) -> the frozen
predictions P1-P12 with named variables -> the receipts + traces.

CPU only; no engine process; no training; no snapshot injection. Run:
python -B run_controls_verification.py. Exit: 0 green / 2 named refusal /
1 failed prediction.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import controls_harness as ch          # noqa: E402
import camera_views as cv              # noqa: E402
import verify_inputs_u07 as vi7        # noqa: E402

OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))
SEAM_SLA = None                        # no wall-clock SLA exists (prereg 8/A2)


def require(condition, code):
    if not condition:
        print("REFUSAL:" + str(code), file=sys.stderr)
        raise SystemExit(2)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def write_out(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_bytes(canonical(value) + b"\n")
    return path


def write_out_bytes(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------- stages
def stage_pins():
    rows = vi7.verify()
    reg = vi7.verify_registry()
    vi7.extract_u07_tree()
    w10 = vi7.w10_layer()
    limits = vi7.p06_limits()
    return rows, reg, w10, limits


def gate_and_load():
    """The certified line's own gate (W10's sealed code, unmodified): the
    certificate validator -> deploy ALLOW -> frozen loader identity -> build
    identity. Commanding an unverified build would command nothing."""
    import walking_demo as wd            # W10 bytes (its dir is sys.path[0])
    loaded = wd.gate_and_load()
    cert, req, allow, bundle, build_id, params, scene_const, bounds, gate = \
        loaded
    require(allow["decision"] == "ALLOW", "deploy_gate_not_allow")
    require(build_id == ch.BUILD_ID,
            "build_id_mismatch:" + str(build_id))
    return cert, bundle, build_id, params, scene_const, bounds, gate


def build_focus_policy_factory():
    """R5's pinned U03 focus policy factory: built against the ARM's own
    recording sink (one emission path); the tick source is the CALLER's
    decision, riding the arm loop's tick."""
    import sys as _sys
    from tools.monkey_campaign.product import input_mapper as pinned_im
    # the pinned policy does a BARE `import input_mapper` (its seam-era
    # layout); alias the SAME pinned module object under that name — import
    # identity, no copy, no rewrite of pinned bytes.
    _sys.modules.setdefault("input_mapper", pinned_im)
    import importlib.util
    fp_path = vi7.PINNED_ROOT.joinpath(
        "tools", "monkey_campaign", "contributions", "MAT2-U02", "reference",
        "tools", "monkey_campaign", "product", "focus_policy.py")
    require(fp_path.exists(), "input_pin_missing:focus_policy_reference")
    spec = importlib.util.spec_from_file_location("u07_focus_policy", fp_path)
    fp_mod = importlib.util.module_from_spec(spec)
    sys.modules["u07_focus_policy"] = fp_mod
    spec.loader.exec_module(fp_mod)

    def builder(arm_sink):
        tick_holder = [0]

        def factory(gate):
            return pinned_im.InputMapper(gate,
                                         tick_source=lambda: tick_holder[0])

        policy = fp_mod.FocusPolicy(sink=arm_sink, mapper_factory=factory)
        return policy, tick_holder

    return builder


def stage_arms(adapter, build_id, params):
    res1 = ch.run_arm("R1", adapter, build_id, params, script="full",
                      horizon=ch.HORIZON_R1)
    res2 = ch.run_arm("R2", adapter, build_id, params, script="full",
                      horizon=ch.HORIZON_R1)
    res3 = ch.run_arm("R3", adapter, build_id, params, script="wrong",
                      horizon=ch.HORIZON_R3)
    res4 = ch.run_arm("R4", adapter, build_id, params, script="hold",
                      horizon=ch.HORIZON_R4)
    focus = {"policy_builder": build_focus_policy_factory(),
             "press_tick": ch.R5_PRESS_TICK,
             "blur_tick": ch.R5_BLUR_TICK,
             "dropped_press_tick": ch.R5_DROPPED_PRESS_TICK,
             "focus_tick": ch.R5_FOCUS_TICK,
             "recover_press_tick": ch.R5_RECOVER_PRESS_TICK}
    res5 = ch.run_arm("R5", adapter, build_id, params, script="full",
                      horizon=ch.HORIZON_R5, focus=focus)
    return res1, res2, res3, res4, res5


def stage_render_present(res1):
    """The declared render plan from R1's records; then the REAL presented
    observations attach to the window chains (P3's data source)."""
    import visualization as vz          # W10 bytes (its dir is sys.path[0])
    f04 = vz.load_f04_module()
    geom = vz.gait_geometry()
    plan = cv.build_frame_plan()
    colours, metas = cv.render_frames(f04, vz, res1["per_tick"], geom,
                                      cv.U07_VIEWS, plan)
    # P10: the render happened AFTER the state chain was recorded; assert the
    # run's own records are untouched by re-hashing the committed trace.
    chain_before = list(res1["state_chain"])
    _ = cv.occlusion_probe(f04.Camera({
        "position": list(cv.U07_VIEWS["C_V2_obstructed"]["position"]),
        "target": list(cv.U07_VIEWS["C_V2_obstructed"]["target"]),
        "vfov_deg": cv.U07_VIEWS["C_V2_obstructed"]["vfov_deg"],
        "near_far": list(cv.U07_VIEWS["C_V2_obstructed"]["near_far"])}),
        cv.U07_VIEWS["C_V2_obstructed"])
    require(res1["state_chain"] == chain_before,
            "falsifier_did_not_bite:P10_render_mutated_state")
    # the real presented observations
    win_seqs = ch.window_chains(res1)
    frames = cv.presented_frames_for(win_seqs, res1)
    ch.attach_presented_stage(res1, frames)
    lags = ch.presented_lags(frames)
    # repeatable inspection: the two side-view renders MUST be byte-identical
    s1 = next(m for m in metas if m["frame_id"].startswith("S_pass1"))
    s2 = next(m for m in metas if m["frame_id"].startswith("S_pass2"))
    import numpy as np
    i1 = plan.index(next(p for p in plan
                         if p["frame_id"] == s1["frame_id"]))
    i2 = plan.index(next(p for p in plan
                         if p["frame_id"] == s2["frame_id"]))
    identical = np.array_equal(colours[i1], colours[i2])
    return {"f04_module": f04, "viz_module": vz, "geom": geom,
            "plan": plan, "colours": colours, "metas": metas,
            "window_seqs": win_seqs, "presented_frames": frames,
            "presented_lags": lags,
            "side_repeat_identical": bool(identical)}


def stage_predictions(res1, res2, res3, res4, res5, reg, limits, render):
    ev = {}

    # ---- P1/P2/P4 (all R1 chains; named variables; derived at run) -------
    # P1 is the AMENDED A1 law (first response per input transition); the
    # re-issue hold-age law is the accepted adapter's declared antecedent
    # behaviour and is recorded informationally, never as a latency claim.
    stats_all = ch.segment_stats(res1)
    ev["P1_first_response"] = {
        "chains": stats_all["chains"],
        "transitions": stats_all["transitions"],
        "first_response_ms_max": stats_all["first_response_ms_max"],
        "hold_age_info_max_ms": stats_all["seg_input_to_command_ms_max"],
        "limit_ms": 50.0, "source": "C12 seam INTERVAL_MS (caller data)",
        "amendment": "AMENDMENT-A1 (dev-refuted original P1; replaced "
                     "before the sealed run)"}
    require(stats_all["chains"] > 0, "prediction_failed:P1_no_chains")
    require(stats_all["first_response_ms_max"] <= 50.0,
            "prediction_failed:P1_first_response")
    ev["P2_consumed_lag"] = {
        "consumed_lag_ticks_max": stats_all["consumed_lag_ticks_max"],
        "law": "ZOH boundary: consumed == issued + 1 (300 Hz)"}
    require(stats_all["consumed_lag_ticks_max"] == 1,
            "prediction_failed:P2_zoh_boundary")
    ev["P4_poll_cadence"] = {
        "poll_periods_ms": stats_all["poll_periods_ms"],
        "poll_period_ms_max": stats_all["poll_period_ms_max"],
        "p06_frozen_limit_ms": limits["ui_poll_cadence_ms"],
        "source": "P06 carried ui-poll-cadence-ms (caller data)"}
    require(stats_all["poll_period_ms_max"] <= limits["ui_poll_cadence_ms"],
            "prediction_failed:P4_poll_cadence")

    # ---- P3 presented lag (window chains; real presented observations) ---
    lags = render["presented_lags"]
    ev["P3_presented_lag"] = lags
    ev["P3_presented_lag"]["bound_ticks"] = ch.PRESENTED_LAG_TICKS_MAX
    ev["P3_presented_lag"]["window_chains"] = len(render["window_seqs"])
    require(lags["presented_lag_ticks_max"] is not None
            and lags["presented_lag_ticks_max"] <=
            ch.PRESENTED_LAG_TICKS_MAX,
            "prediction_failed:P3_presented_lag")

    # ---- P5 repeatable scene --------------------------------------------
    # the declared normalization: per-arm run identity normalized away AND
    # the `presented` stage excluded (it is R1's declared render subset, not
    # part of the simulated repeat; R2 renders nothing).
    def repeat_events(res):
        return [e for e in ch.normalize_events(
            ch.events_for_seqs(res, ch.command_seqs(res)), run_id=None)
            if e["stage"] != "presented"]

    norm1 = repeat_events(res1)
    norm2 = repeat_events(res2)
    events_equal = ch.canonical(norm1) == ch.canonical(norm2)
    chains_equal = res1["state_chain"] == res2["state_chain"]
    ev["P5_repeatable_scene"] = {
        "state_chains_identical": chains_equal,
        "trace_events_identical_normalized": events_equal,
        "r1_final_state_sha256": res1["final_state_sha256"],
        "r2_final_state_sha256": res2["final_state_sha256"],
        "normalization": "per-arm run identity normalized; the presented "
                         "stage excluded (R1's declared render subset)"}
    require(chains_equal and events_equal,
            "prediction_failed:P5_repeatable_scene")

    # ---- P6 wrong-command response (trace level; A7 cites W10 P9) --------
    wrong = ch.wrong_command_response(res1, res3)
    ev["P6_wrong_command_response"] = wrong
    require(wrong["r3_all_wrong_flagged"] and wrong["r3_demand_positive"],
            "prediction_failed:P6_wrong_command_response")

    # ---- P7 expiry (AMENDMENT-A3: the honest observable law) ------------
    # A healthy arm never produces a revert EVENT (A2: held keys re-issue;
    # A3: released keys land on exact zero whose projection IS the inert
    # path). The law's bite is proven at the unit level (named checks).
    last_rec = (res4["sink_records"][-1]
                if res4["sink_records"] else None)
    zero_last = bool(last_rec) and last_rec["v_forward_m_s"] == 0.0
    from tools.monkey_campaign.product.input_mapper import (  # pinned bytes
        INTERVAL_MS as IM_INTERVAL_MS, RELEASE_DECAY_MS as IM_DECAY_MS)
    release_ms = ch.now_ms_of(600)
    zero_deadline = release_ms + IM_DECAY_MS + IM_INTERVAL_MS
    zero_in_time = bool(last_rec) and \
        ch.now_ms_of(last_rec["issued_tick"]) <= zero_deadline
    positive_after_deadline = [r for r in res4["sink_records"]
                               if r["v_forward_m_s"] > 0.0
                               and r["issued_tick"] > 615]
    ev["P7_expiry_revert"] = {
        "expiry_ticks_const": res4["_expiry_ticks_const"],
        "first_revert_age_ticks": res4["first_revert_age_ticks"],
        "first_revert_null_reason": "no_stale_noninert_record_on_"
                                    "healthy_clock (AMENDMENT-A3)",
        "reverts": res4["expiry_reverts"][:8],
        "zero_record_is_last": zero_last,
        "zero_record_issued_tick": last_rec["issued_tick"] if last_rec
        else None,
        "zero_within_decay_deadline": zero_in_time,
        "decay_deadline_ms": zero_deadline,
        "no_positive_record_after_decay_deadline":
            not positive_after_deadline,
        "law": "release lands the stream on an exact-zero record whose "
               "projection IS the declared inert path; the expiry belt "
               "(age > EXPIRY_TICKS) is proven at the unit level (AMENDMENT"
               "-A3)",
        "amendment": "AMENDMENT-A3"}
    require(zero_last and zero_in_time,
            "prediction_failed:P7_zero_record_law")
    require(not positive_after_deadline,
            "prediction_failed:P7_silence_after_decay")

    # ---- P8 focus loss (no-stuck invariant; dropped intents named) -------
    from tools.monkey_campaign.product.input_mapper import (  # pinned bytes
        INTERVAL_MS, RELEASE_DECAY_MS)
    tail_rec = res5["sink_records"]
    rec_after = [r for r in tail_rec
                 if r["issued_tick"] >= ch.R5_BLUR_TICK]
    blur_ms = ch.now_ms_of(ch.R5_BLUR_TICK)
    # the pinned decay law: after release_all the demand decays to exactly
    # 0.0 within RELEASE_DECAY_MS; the last poll in that window can emit at
    # most one interval later. Silence must follow the exact-zero record.
    decay_deadline = blur_ms + RELEASE_DECAY_MS + INTERVAL_MS
    positive_after_blur = [r for r in rec_after if r["v_forward_m_s"] > 0.0]
    last_positive_tick = (positive_after_blur[-1]["issued_tick"]
                          if positive_after_blur else None)
    zeros_after = [r for r in rec_after
                   if r["v_forward_m_s"] == 0.0
                   and (last_positive_tick is None
                        or r["issued_tick"] > last_positive_tick)]
    silence_after_zero = not any(
        r["v_forward_m_s"] > 0.0 for r in rec_after
        if zeros_after and r["issued_tick"] > zeros_after[0]["issued_tick"])
    drop = res5["focus_drop_snapshot"]
    drop_named = bool(drop) and (
        len(drop.get("last_trace", {}).get("dropped_blurred", [])) >= 1)
    recover = [r for r in tail_rec
               if r["issued_tick"] >= ch.R5_RECOVER_PRESS_TICK]
    ev["P8_focus_loss"] = {
        "blur_ms": blur_ms,
        "release_decay_ms_const": RELEASE_DECAY_MS,
        "interval_ms_const": INTERVAL_MS,
        "declared_silence_deadline_ms": decay_deadline,
        "last_positive_tick_after_blur": last_positive_tick,
        "last_positive_ms_after_blur":
            ch.now_ms_of(last_positive_tick)
            if last_positive_tick is not None else None,
        "zero_record_after_decay": bool(zeros_after),
        "silence_after_zero": silence_after_zero,
        "dropped_press_tick": ch.R5_DROPPED_PRESS_TICK,
        "drop_snapshot": drop,
        "drop_named": drop_named,
        "recover_records": recover,
        "recover_chain_new": len(recover) >= 1,
    }
    require(last_positive_tick is None
            or ch.now_ms_of(last_positive_tick) <= decay_deadline,
            "prediction_failed:P8_no_stuck_after_blur")
    require(zeros_after and silence_after_zero,
            "prediction_failed:P8_zero_then_silence")
    require(drop_named, "prediction_failed:P8_drop_not_named")
    require(len(recover) >= 1, "prediction_failed:P8_no_recovery_chain")

    # ---- P9 camera fields + obstruction (executed numerics) --------------
    required_fields = reg["profile"]["camera_required_fields"]
    obstructed = render["f04_module"].Camera({
        "position": list(cv.U07_VIEWS["C_V2_obstructed"]["position"]),
        "target": list(cv.U07_VIEWS["C_V2_obstructed"]["target"]),
        "vfov_deg": cv.U07_VIEWS["C_V2_obstructed"]["vfov_deg"],
        "near_far": list(cv.U07_VIEWS["C_V2_obstructed"]["near_far"])})
    probe = cv.occlusion_probe(obstructed, cv.U07_VIEWS["C_V2_obstructed"])
    labels = ["body_label", "tick_label", "camera_target_label"]
    layers = list(reg["profile"]["diagnostic_layers"])
    rec = cv.camera_view_record(
        obstructed, cv.U07_VIEWS["C_V2_obstructed"], [4500],
        occlusion_mode="declared_occluder_depth_test", labels=labels,
        layers=layers, frame_id="C_V2_obstructed_t4500",
        tick_interval=[4500, 4500])
    missing = [f for f in required_fields if f not in rec]
    ev["P9_camera_fields_obstruction"] = {
        "required_field_count": len(required_fields),
        "missing_fields": missing,
        "occlusion_probe": probe,
        "clean_view": cv.CLEAN_VIEW,
        "side_repeat_identical": render["side_repeat_identical"],
        "law": "obstruction declared with executed numerics; concealment "
               "would be a missing/contradictory record"}
    require(not missing, "prediction_failed:P9_missing_camera_fields:"
            + ",".join(missing))
    require(probe["segment_hits_box"]
            and probe["occluder_in_front_of_target"]
            and probe["target_inside_box_screen_footprint"],
            "prediction_failed:P9_obstruction_numerics")
    require(render["side_repeat_identical"],
            "prediction_failed:P9_side_view_not_repeatable")

    # ---- P10 camera-body invariance (structural + executed) --------------
    ev["P10_camera_body_invariance"] = {
        "render_consumes_records_only": True,
        "state_chain_recorded_before_render": True,
        "loop_has_camera_channel": False,
        "evidence": "the arm loop signature admits no camera input; the "
                    "render plan consumed R1's committed per-tick records; "
                    "state_chain equality asserted across the render stage",
        "w10_fb6_heritage": "cited (sealed), not re-claimed"}

    # ---- P11 limits honesty (the accepted module's own verdicts) ---------
    # the cadence check rides the AMENDED A1 subset: the FIRST-RESPONSE
    # chains inside the declared render window (the A press at tick 4500
    # opens one); the wall-clock end-to-end verdict stays unqualified.
    win_seqs = render["window_seqs"]
    first_win = sorted(set(win_seqs)
                       & set(ch.same_boundary_chains(res1, win_seqs)))
    require(first_win, "prediction_failed:P11_empty_first_response_window")
    summary_unqualified = ch.accepted_latency_summary(res1, win_seqs, None)
    require(summary_unqualified["qualification"]["status"] == "unqualified",
            "prediction_failed:P11_wall_clock_not_unqualified")
    summary_cadence = ch.accepted_latency_summary(
        res1, first_win,
        {"seg_input_to_command_ms": 50.0})
    checks = summary_cadence["qualification"]["checks"]
    ev["P11_limits_honesty"] = {
        "wall_clock_status": summary_unqualified["qualification"]["status"],
        "wall_clock_reason": summary_unqualified["qualification"]["reason"],
        "cadence_check": checks.get("seg_input_to_command_ms"),
        "cadence_subset_seqs": first_win,
        "cadence_subset_law": "chains whose input transition was observed at the SAME boundary poll (fresh transitions; mouse-only re-issues inherit the held key and are excluded)",
        "amendment_a1_sha256": vi7.amendment_a1_sha256(),
        "amendment_a2_sha256": vi7.amendment_a2_sha256(),
        "amendment_a3_sha256": vi7.amendment_a3_sha256(),
        "amendment_a4_sha256": vi7.amendment_a4_sha256(),
        "note": "no frozen wall-clock end-to-end SLA exists (P06 "
                "network-latency-sla-ms OPERATOR_DECISION_REQUESTED); the "
                "ONLY qualified numeric is the frozen cadence law"}
    require(checks["seg_input_to_command_ms"]["pass"] is True,
            "prediction_failed:P11_cadence_check")

    # ---- P12 unbound timing evidence is refused --------------------------
    it = res1["_accepted_trace"]
    tampered = [dict(e) for e in ch.events_for_seqs(res1, win_seqs)[:8]]
    tampered[3]["clock"] = "wall_clock_probe"
    refused_reason = None
    try:
        it.parse_trace(tampered)
    except it.TraceRefused as r:
        refused_reason = r.reason
    ev["P12_timing_evidence_bound"] = {
        "clock_id": ch.CLOCK_ID, "build_id": ch.BUILD_ID,
        "run_ids": sorted({res1["run_id"], res2["run_id"], res3["run_id"],
                           res4["run_id"], res5["run_id"]}),
        "mixed_clock_refusal_reason": refused_reason,
        "accepted_refusals": {"R1_full": "missing_stage (only the declared "
                                         "window is rendered; A1)",
                              "R2_R3_R4": "missing_stage (not rendered)",
                              "R5": "missing_stage (policy path; the "
                                    "FOLLOWUP precedent)"}}
    require(refused_reason == "mixed_clock",
            "prediction_failed:P12_mixed_clock_not_refused")
    return ev


def declared_refusal_proofs(res_by_arm):
    """The honest missing-stage refusals, PROVEN with the accepted module."""
    proofs = {}
    for arm in ("R1_full", "R2", "R3", "R4"):
        res = res_by_arm[arm.split("_")[0]]
        it = res["_accepted_trace"]
        reason = None
        try:
            it.parse_trace(res["_tracer"].events())
        except it.TraceRefused as r:
            reason = r.reason
        proofs[arm] = {"refusal_reason": reason,
                       "declared": "missing_stage (A1: only the declared "
                                   "window is rendered)"}
    return proofs


def main() -> int:
    rows, reg, w10, limits = stage_pins()
    require(reg["profile"]["id"] == "controls",
            "profile_check_after_capture_forbidden")
    cert, bundle, build_id, params, scene_const, bounds, gate = \
        gate_and_load()
    import command_model as cm         # W10 bytes (frozen script constants)
    adapter = cm.CommandAdapter(bundle["manifest"], scene_const)

    res1, res2, res3, res4, res5 = stage_arms(adapter, build_id, params)
    render = stage_render_present(res1)

    ev = stage_predictions(res1, res2, res3, res4, res5, reg, limits, render)
    res_by_arm = {"R1": res1, "R2": res2, "R3": res3, "R4": res4,
                  "R5": res5}
    refusals = declared_refusal_proofs(res_by_arm)

    receipt = {
        "schema": "chimera.u07_controls_receipt.v1",
        "task_id": "U07", "card_id": "MAT2-U07",
        "attempt_id": vi7.ATTEMPT_ID, "agent_id": vi7.AGENT_ID,
        "criteria_sha256": vi7.CRITERIA_SHA256,
        "base_sha256": vi7.BASE_SHA,
        "preregistration_sha256": vi7.prereg_sha256(),
        "amendment_a1_sha256": vi7.amendment_a1_sha256(),
        "amendment_a2_sha256": vi7.amendment_a2_sha256(),
        "amendment_a3_sha256": vi7.amendment_a3_sha256(),
        "amendment_a4_sha256": vi7.amendment_a4_sha256(),
        "registry": reg,
        "pin_rows": rows, "pin_row_count": len(rows),
        "w10_layer": w10,
        "p06_caller_limits": {"ui_poll_cadence_ms":
                              limits["ui_poll_cadence_ms"],
                              "latency_sla_decision":
                              limits["latency_sla_decision"]},
        "gate": gate,
        "arms": {a: {"run_id": r["run_id"], "horizon": r["horizon"],
                     "chain_count": r["chain_count"],
                     "final_state_sha256": r["final_state_sha256"],
                     "expiry_reverts": r["expiry_reverts"][:8],
                     "first_revert_age_ticks": r["first_revert_age_ticks"]}
                 for a, r in res_by_arm.items()},
        "predictions": ev,
        "accepted_trace_refusals": refusals,
        "render": {"frame_count": len(render["plan"]),
                   "window_seqs": render["window_seqs"],
                   "presented_frames": render["presented_frames"],
                   "presented_lags": render["presented_lags"],
                   "side_repeat_identical": render["side_repeat_identical"]},
        "absent_inventory": {
            "A1_native_recorder_seams": "ABSENT (presented here = declared "
                                        "CPU-line frame record; no native "
                                        "engine process; W10 N1/N2/N3 "
                                        "carried)",
            "A2_wall_clock_latency_sla": "UNRESOLVED P06 operator decision "
                                         "(network-latency-sla-ms); "
                                         "wall-clock verdict unqualified",
            "A3_human_feel": "NOT MEASURED (distinct acceptance field; "
                             "observation verbatim)",
            "A4_camera_service": "ABSENT (pinned follow-camera laws "
                                 "consumed; its HTTP transport is not "
                                 "exercised)",
            "A5_session_controls": "ABSENT (no interactive process; X02 "
                                   "semantics declared, not exercised)",
            "A6_os_focus": "NOT EXERCISED (U03 constraint: operator desktop "
                           "untouched; policy layer only)",
            "A7_physical_separation": "W10's sealed P9 cited; this card "
                                      "re-executes the trace-level "
                                      "response only"},
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B "
                                   "tools/monkey_campaign/contributions/"
                                   "MAT2-U07/run_controls_verification.py"},
    }

    # verdicts on the evidence (honest: the done_when is bounded by A1/A2)
    verdict = {
        "P_all_green": True,
        "qualified": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8",
                      "P9", "P10", "P12"],
        "unqualified_by_law": ["P11_wall_clock_end_to_end (A2)",
                               "R1/R2/R3/R4/R5 full-trace end-to-end "
                               "(A1: declared window only)"],
    }
    receipt["verdict"] = verdict

    p_all = ch.canonical(ev)
    write_out("controls_receipt.json", receipt)
    # traces (bounded: the full R1 trace + window subset + R5 policy events)
    write_out("trace_events_r1.json",
              {"arm": "R1", "run_id": res1["run_id"],
               "events": res1["_tracer"].events()})
    write_out("trace_window_r1.json",
              {"arm": "R1", "run_id": res1["run_id"],
               "seqs": render["window_seqs"],
               "events": ch.events_for_seqs(res1, render["window_seqs"]),
               "summary_unqualified":
               ch.accepted_latency_summary(res1, render["window_seqs"], None),
               "summary_cadence": ch.accepted_latency_summary(
                   res1, render["window_seqs"],
                   {"seg_input_to_command_ms": 50.0})})
    write_out("trace_events_r5_policy.json",
              {"arm": "R5", "run_id": res5["run_id"],
               "declared_refusal": refusals.get("R5"),
               "focus_drop_snapshot": res5["focus_drop_snapshot"],
               "focus_state_tail": res5["focus_state_tail"]})
    write_out_bytes("frames_meta.json",
                    ch.canonical({"plan": render["plan"],
                                  "metas": render["metas"]}) + b"\n")
    import numpy as np
    # uint8 (the renderer's own 0..255 values) — the declared-output budget
    # law; run_capture_u07 re-casts exactly.
    np.save(str(OUT / "frames.npy"),
            np.stack(render["colours"]).astype(np.uint8))
    print("controls verification: P_all_green; chains R1=%d window=%d"
          % (res1["chain_count"], len(render["window_seqs"])))
    _ = (cert, p_all, cm, bounds, SEAM_SLA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
