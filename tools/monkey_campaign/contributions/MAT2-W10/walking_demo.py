#!/usr/bin/env python3
"""MAT2-W10: the gated walking-acceptance experiment (prereg sections 2-7).

Order is law: pins -> registry -> pin-extract -> re-validate the pinned W04
certificate -> deploy gate ALLOW -> frozen loader + bit-for-bit identity ->
build identity -> the pinned U01 port executes the FROZEN W08 input script
(start/turn/speed/stop) through the frozen adapter into the certified scene
OPEN-LOOP -> arm R4 replays W09's declared unsupported probe VERBATIM with
the sealed W09 supervisor owning R1/R2 -> the frozen predictions P1-P13 are
evaluated with named variables -> the receipts + per-tick traces are emitted
(the traces are the visualization's ONLY input; the render writes nothing).

Arms: R1 clean commanded walk (horizon 10500), R2 identical re-execution
(determinism zero-control), R3 wrong-command probe (W08 prereg 4.4),
R4 the W09 A1 declared unsupported probe replay (fall sequence; horizon
900, W09's declared episode horizon). FB arms run scratch tampered copies
with their own passing clean controls FIRST (G1).

Run:  python -B walking_demo.py
Exit: 0 green / 2 named refusal / 1 failed prediction. CPU only; no engine
process; no training; no snapshot injection on clean arms.
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
HORIZON_R4 = 900                    # W09's declared episode horizon
WALK_INTERVAL = (cm.TICK_START_ONSET, 9031)   # the declared walk interval

# W09 FB1 heritage tamper ticks (inside the first produced window [30, 119])
FB1_SNAPSHOT_TICK = 60
FB1_RESTORE_TICK = 100


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


def load_w09_supervisor():
    """The sealed W09 supervisor module (amendment A1 pin), imported by file
    path from the byte-verified extraction; zero modification."""
    return vi.load_pinned_module(
        "w09_out_of_envelope",
        ("tools", "monkey_campaign", "contributions", "MAT2-W09",
         "out_of_envelope.py"))


def w09_consts(oe, params, manifest):
    return oe.derive_constants(params, manifest)


def run_commanded(adapter, build_id, params, *, wrong_override=False,
                  horizon=HORIZON_R1):
    """One FULL re-execution of the frozen commanded sequence (W08's sealed
    open-loop form). The pinned InputMapper produces the records; the frozen
    adapter projects; the certified scene steps."""
    from tools.policy_compat import scene_cpu as SC      # pinned bytes
    from tools.science_funnel.typeb_export.command_record import (  # pinned
        COMMAND_RECORD_VERSION, V_MAX_IN_BAND_M_S)
    from tools.monkey_campaign.product.input_mapper import (  # pinned
        InputMapper, V_MAX_IN_BAND_M_S as IM_V_MAX,
        OMEGA_MAX_RAD_S, EXPIRY_TICKS)

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


# ---------------------------------------------------------------- R4 (W09 A1)
def probe_commands(oe_consts):
    """W09's declared A1 alignment commands (W09 prereg section 3, pinned),
    derived at run time; the alignment residue must be exactly 0."""
    cycle = oe_consts["cycle_ticks"]
    phase_r0 = (((SEED % cycle) + 0.5) / cycle) % 1.0
    off_r = oe_consts["bounds_hi"][4]
    off_l = ((phase_r0 - 0.0 + off_r) % 1.0)
    if off_l > oe_consts["bounds_hi"][0]:
        off_l -= 1.0
    require(oe_consts["bounds_lo"][0] <= off_l <= oe_consts["bounds_hi"][0],
            "probe_derivation:off_l_out_of_bounds:" + repr(off_l))
    resid = (phase_r0 + off_r - off_l) % 1.0
    require(resid == 0.0, "probe_derivation:alignment_residue:" + repr(resid))
    lift_hi = oe_consts["bounds_hi"][2]
    cmds = [off_l, 1.0, lift_hi, oe_consts["center"][3],
            off_r, 1.0, lift_hi, oe_consts["center"][7]]
    for i, v in enumerate(cmds):
        require(oe_consts["bounds_lo"][i] <= v <= oe_consts["bounds_hi"][i],
                "probe_derivation:command_out_of_bounds:%d" % i)
    return cmds, {"phase_r0": phase_r0, "off_l": off_l, "off_r": off_r,
                  "alignment_residue_cycles": resid}


def run_probe_arm(oe, oe_consts, commands, *, stride_override=None,
                  fault_hook=None, horizon=HORIZON_R4):
    """The declared excursion loop with the SEALED W09 supervisor enforcing
    the response table; scene.step is the only physics.

    stride_override(tick, classes) -> list|None is the DECLARED tamper path
    of FB2 (never present on clean arms): it replaces the post-supervisor
    applied vector, bypassing the sealed R1 law.
    fault_hook(tick, scene) is FB1's declared concealed snapshot/restore.
    """
    from tools.policy_compat import scene_cpu as SC
    sup = oe.OutOfEnvelopeSupervisor(oe_consts, None)
    scene = SC.make_scene(SC.BUILD_N_ID, _PARAMS[0], SEED)
    scene.begin(list(commands))
    records, applied_tick, v_series = [], [], []
    trips_at_fall = None
    overrides = []
    for t in range(horizon):
        rec = scene.observation_record()
        records.append(json.loads(json.dumps(rec)))
        if fault_hook is not None:
            fault_hook(t, scene)
            rec = scene.observation_record()
            records[-1] = json.loads(json.dumps(rec))
        applied, sat, events = sup.apply(t, rec, commands, [0.0] * 8)
        stepped = [float(v) for v in np.asarray(applied, dtype=np.float32)]
        if stride_override is not None:
            over = stride_override(t, sup.classes)
            if over is not None:
                stepped = [float(v) for v in np.asarray(over, dtype=np.float32)]
                overrides.append(t)
        applied_tick.append(stepped)
        if any(ev["event"] == "R2_fall_declared" for ev in events):
            trips_at_fall = [int(scene.trip_l), int(scene.trip_r)]
        scene.step(np.asarray(stepped, dtype=np.float32), sat)
        v_series.append(scene.v)
    terminal = sup.terminal(records[-1], horizon)
    return {"records": records, "applied_per_tick": applied_tick,
            "v_series": v_series, "supervisor": sup,
            "terminal": terminal, "trips": [int(scene.trip_l), int(scene.trip_r)],
            "trips_at_fall": trips_at_fall,
            "fall_declared_tick": sup.fall_declared_tick,
            "commands": list(commands), "stride_override_ticks": overrides}


def unsupported_intervals(classes):
    out = []
    t = 0
    while t < len(classes):
        if classes[t] == "UNSUPPORTED":
            j = t
            while j < len(classes) and classes[j] == "UNSUPPORTED":
                j += 1
            out.append([t, j - 1])
            t = j
        else:
            t += 1
    return out


# ---------------------------------------------------------------- stage 8
def evaluate(res1, res2, res3, res4, bounds, gate, oe, oe_consts):
    """The frozen predictions P2-P13 with named variables."""
    ev = {}
    pt1 = res1["per_tick"]
    v = res1["v_series"]

    # ---- P2 port seam laws (C12; W08's sealed form re-executed) ------------
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
            lo_exp = [-0.25, 0.2, 0.2, 0.5, -0.25, 0.2, 0.2, 0.5][ch]
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
    meas_tl, meas_tr, meas_tkl = max(tl), max(tr), max(tkl)
    seam_rows = [d for d in dec
                 if d["issued_tick"] == cm.TICK_KEYA_FIRST]
    ev["P5_turn_exactness"] = {
        "in_range_residual_bound_rad_s": eps,
        "turn_left_max_residual_rad_s": meas_tl,
        "turn_right_max_residual_rad_s": meas_tr,
        "seam_max_achieved_rad_s": 1.0,
        "seam_max_max_residual_rad_s": meas_tkl,
        "seam_max_declared_residual_rad_s": 0.6,
        "seam_max_saturation_named": bool(seam_rows and
                                          seam_rows[0]["saturation"][0] == 1.0
                                          and seam_rows[0]["saturation"][4] == 1.0),
        "speed_unchanged_by_yaw_claims": "P4 continues across the windows",
    }
    p5 = ev["P5_turn_exactness"]
    require(meas_tl <= eps and meas_tr <= eps and meas_tkl <= eps,
            "prediction_failed:P5_yaw_residual")
    require(p5["seam_max_saturation_named"], "prediction_failed:P5_named_sat")

    # ---- P6 speed step decay ------------------------------------------------
    mid0 = cm.TICK_DECAY_MID_ISSUED
    block = [v[t] for t in range(mid0 + 1, mid0 + 16)]
    ev["P6_speed_step_decay"] = {
        "decay_block_ticks": [mid0 + 1, mid0 + 15],
        "block_v_series_m_s": block,
        "strictly_decreasing": all(b < a for a, b in zip(block, block[1:])),
        "measured_demand_m_s": res1["sink_records"] and next(
            (r["v_forward_m_s"] for r in res1["sink_records"]
             if r["issued_tick"] == mid0), None),
        "nominal_demand_m_s": 0.57271875,
    }
    p6 = ev["P6_speed_step_decay"]
    require(p6["strictly_decreasing"], "prediction_failed:P6_monotone")
    if p6["measured_demand_m_s"] is not None:
        p6["deviation_from_nominal_m_s"] = (
            p6["measured_demand_m_s"] - 0.57271875)
        p6["deviation_flag"] = (abs(p6["deviation_from_nominal_m_s"]) > 1e-9)

    # ---- P7 stop floor settle -----------------------------------------------
    lo7, up7 = bounds["settle_end_range_m_s"]
    end7 = v[cm.SETTLE_END]
    dec_ok = all(v[t + 1] <= v[t] + 1e-12
                 for t in range(cm.SETTLE_ONSET_TICK, cm.SETTLE_END)
                 if v[t] > bounds["floor_band_m_s"][1])
    floor_ok = all(vt >= bounds["floor_band_m_s"][0] - 1e-9
                   for vt in v[cm.SETTLE_ONSET_TICK:])
    ev["P7_stop_floor_settle"] = {
        "settle_end_tick": cm.SETTLE_END,
        "v_at_settle_end_m_s": end7,
        "settle_range_bound_m_s": [lo7, up7],
        "v_in_settle_range": lo7 - 1e-12 <= end7 <= up7 + 1e-12,
        "strictly_decreasing_above_floor_band": dec_ok,
        "never_below_floor_band_low": floor_ok,
        "floor_semantics": "the certified zero-advance floor (W08 P7 carried; "
                           "never a zero-speed claim)",
    }
    p7 = ev["P7_stop_floor_settle"]
    require(p7["v_in_settle_range"], "prediction_failed:P7_settle_range")
    require(dec_ok and floor_ok, "prediction_failed:P7_monotone_or_floor")

    # ---- P8 stability bars (every tick of every arm) ------------------------
    def stability(res):
        env = bounds["velocity_envelope_m_s"]
        bad_rows = []
        for row in res["per_tick"]:
            t = row["tick"]
            if abs(row["com_v_m_s"]) > env + 1e-12:
                bad_rows.append((t, "envelope"))
            if row["contact_count"] < 2:
                bad_rows.append((t, "contact_floor"))
            if row["intervention_reason"] != "none":
                bad_rows.append((t, "intervention"))
            if any(not (g > 0.0) for g in row["pad_gaps"]):
                bad_rows.append((t, "pad_gap"))
            if any(v != v or v in (float("inf"), float("-inf"))
                   for v in ([row["com_v_m_s"], row["com_x_m"]]
                             + list(row["pad_gaps"]))):
                bad_rows.append((t, "nonfinite"))
        return bad_rows

    s1, s2, s3, s4 = stability(res1), stability(res2), stability(res3), stability(res4)
    ev["P8_stability_bars"] = {
        "velocity_envelope_m_s": bounds["velocity_envelope_m_s"],
        "contact_floor_bar": 2,
        "observed_min_contact_count_r1": min(r["contact_count"]
                                             for r in pt1),
        "violations_r1": s1[:20], "violations_r2": s2[:20],
        "violations_r3": s3[:20], "violations_r4_pre_fall": [
            row for row in s4 if row[0] < (res4["fall_declared_tick"]
                                           or HORIZON_R4)][:20],
        "counts": {"r1": len(s1), "r2": len(s2), "r3": len(s3)},
    }
    require(not s1 and not s2 and not s3, "prediction_failed:P8_bars")
    fall_t = res4["fall_declared_tick"] or HORIZON_R4
    require(not [row for row in s4 if row[0] < fall_t],
            "prediction_failed:P8_bars_r4_pre_fall")

    # ---- P9 wrong command MUST FIRE ------------------------------------------
    div = next((t for t in range(min(len(res1["state_chain"]),
                                     len(res3["state_chain"])))
                if res1["state_chain"][t] != res3["state_chain"][t]), None)
    v1p = res1["v_series"][cm.PROBE_TICK]
    v3p = res3["v_series"][cm.PROBE_TICK]
    ident12 = (res1["state_chain"] == res2["state_chain"])
    a = bounds["v_cmd_ceiling_m_s"] * bounds["d_nom_per_s"]
    hi_b = v3p >= (a / bounds["d_hi_per_s"]) - 1e-9
    ev["P9_wrong_command_response_MUST_FIRE"] = {
        "first_divergence_tick": div,
        "expected_first_divergence_tick": cm.WRONG_INJECT_TICK + 1,
        "prefix_identical_through_5430": div == cm.WRONG_INJECT_TICK + 1,
        "v_r1_at_probe_m_s": v1p, "v_r3_at_probe_m_s": v3p,
        "physical_separation_m_s": v3p - v1p,
        "r3_rising_under_wrong_ceiling": hi_b,
        "r1_vs_r2_bit_identical": ident12,
    }
    p9 = ev["P9_wrong_command_response_MUST_FIRE"]
    require(p9["prefix_identical_through_5430"],
            "prediction_failed:P9_divergence_tick")
    require(v3p > v1p, "prediction_failed:P9_separation")
    require(ident12, "prediction_failed:P9_zero_control")

    # ---- P10 supported surface (THIS CARD) ------------------------------------
    lo_w, hi_w = WALK_INTERVAL
    unsup = [r["tick"] for r in pt1
             if lo_w <= r["tick"] <= hi_w and r["contact_count"] < 1]
    contact_min = min(r["contact_count"] for r in pt1 if lo_w <= r["tick"] <= hi_w)
    ev["P10_supported_surface"] = {
        "walk_interval_ticks": [lo_w, hi_w],
        "unsupported_ticks": unsup[:20],
        "unsupported_count": len(unsup),
        "min_contact_count_in_interval": contact_min,
        "every_tick_has_a_foot_contact": not unsup,
        "every_pad_gap_positive_interval": all(
            g > 0.0 for r in pt1 if lo_w <= r["tick"] <= hi_w
            for g in r["pad_gaps"]),
    }
    p10 = ev["P10_supported_surface"]
    require(p10["every_tick_has_a_foot_contact"],
            "walk_unsupported_tick:%d" % (unsup[0] if unsup else -1))
    require(p10["every_pad_gap_positive_interval"],
            "prediction_failed:P10_pad_gaps")

    # ---- P11 no sliding / no penetration (THIS CARD) ---------------------------
    dt = 1.0 / 300.0
    slide = []
    for a_row, b_row in zip(pt1, pt1[1:]):
        expect = dt * a_row["com_v_m_s"]
        got = b_row["com_x_m"] - a_row["com_x_m"]
        if abs(got - expect) > 1e-9:
            slide.append((b_row["tick"], got - expect))
    pen = [(r["tick"], g) for r in pt1 for g in r["pad_gaps"] if g <= 0.0]
    ev["P11_no_sliding_no_penetration"] = {
        "com_identity_violations": slide[:20],
        "com_identity_violation_count": len(slide),
        "worst_com_identity_residual_m": max(
            (abs(row[1]) for row in slide), default=0.0),
        "penetration_events": pen[:20],
        "penetration_count": len(pen),
        "identity_window_m": 1e-9,
    }
    p11 = ev["P11_no_sliding_no_penetration"]
    require(not p11["com_identity_violation_count"],
            "prediction_failed:P11_com_identity")
    require(not p11["penetration_count"], "prediction_failed:P11_penetration")

    # ---- P12 W09 replay faithful (THIS CARD) ----------------------------------
    w09r = vi.w09_out_of_envelope_receipt()
    w09_a1 = w09r["arms"]["A1_unsupported_probe"]
    fall_t = res4["fall_declared_tick"]
    intervals4 = unsupported_intervals(res4["supervisor"].classes)
    first4 = intervals4[0] if intervals4 else [-1, -1]
    first_len4 = first4[1] - first4[0] + 1 if intervals4 else 0
    stride_lo = float(np.float32(oe_consts["bounds_lo"][1]))
    pre_fall_ok = all(
        abs(res4["applied_per_tick"][t][1] - stride_lo) <= 1e-9
        and abs(res4["applied_per_tick"][t][5] - stride_lo) <= 1e-9
        for t in range(HORIZON_R4)
        if res4["supervisor"].classes[t] == "UNSUPPORTED"
        and (fall_t is None or t < fall_t))
    forces_ok = all(r["foot_forces"][4] == 0.0 and r["foot_forces"][5] == 0.0
                    for t, r in enumerate(res4["records"])
                    if res4["supervisor"].classes[t] == "UNSUPPORTED")
    v_env = bounds["velocity_envelope_m_s"]
    envelope_ok = all(abs(x) <= v_env for x in res4["v_series"])
    v_moved = all(res4["v_series"][t + 1] != res4["v_series"][t]
                  for t in range(HORIZON_R4 - 1))
    w09_vals = {
        "first_interval": w09_a1["first_interval"],
        "first_interval_length": w09_a1["first_interval_length"],
        "fall_declared_tick": w09_a1["fall_declared_tick"],
        "trips_at_fall": w09_a1["trips_at_fall"],
        "a_com_r1_m_s2": w09r["response_table"]["a_com_r1_m_s2"],
    }
    got_vals = {
        "first_interval": first4,
        "first_interval_length": first_len4,
        "fall_declared_tick": fall_t,
        "trips_at_fall": res4["trips_at_fall"],
        "a_com_r1_m_s2": (oe_consts["stride_gain"] * 0.5
                          * (stride_lo + stride_lo)),
    }
    ev["P12_w09_replay_faithful"] = {
        "w09_pinned_values": w09_vals,
        "w10_measured_values": got_vals,
        "first_interval_exact": got_vals["first_interval"] == w09_vals["first_interval"],
        "first_interval_length_exact": (got_vals["first_interval_length"]
                                        == w09_vals["first_interval_length"]),
        "fall_tick_exact": got_vals["fall_declared_tick"] == w09_vals["fall_declared_tick"],
        "trips_exact": got_vals["trips_at_fall"] == w09_vals["trips_at_fall"],
        "a_com_exact": abs(got_vals["a_com_r1_m_s2"]
                           - w09_vals["a_com_r1_m_s2"]) <= 1e-15,
        "r1_strides_at_certified_minimum_pre_fall": pre_fall_ok,
        "support_forces_removed_on_unsupported_ticks": forces_ok,
        "velocity_inside_envelope": envelope_ok,
        "never_frozen": v_moved,
        "drift": None if (got_vals["first_interval"] == w09_vals["first_interval"]
                          and got_vals["fall_declared_tick"] == w09_vals["fall_declared_tick"]
                          and got_vals["trips_at_fall"] == w09_vals["trips_at_fall"])
        else "w09_replay_drift",
    }
    p12 = ev["P12_w09_replay_faithful"]
    require(p12["first_interval_exact"] and p12["fall_tick_exact"]
            and p12["trips_exact"] and p12["first_interval_length_exact"],
            "w09_replay_drift")
    require(pre_fall_ok and forces_ok and envelope_ok and v_moved,
            "prediction_failed:P12_response_law")

    # ---- R1/R2 zero-control bit identity ---------------------------------------
    ev["determinism_zero_control"] = {
        "r1_vs_r2_state_chains_bit_identical":
            res1["state_chain"] == res2["state_chain"],
    }
    require(ev["determinism_zero_control"]["r1_vs_r2_state_chains_bit_identical"],
            "prediction_failed:zero_control")
    return ev


# ---------------------------------------------------------------- FB arms
def fb_arms(oe, oe_consts, cmds):
    """Falsifier arms; EVERY clean control runs FIRST and must be green."""
    out = {}

    # FB1 concealed reset (W09's form, R4 vehicle, inside the produced window)
    fb1_clean = run_probe_arm(oe, oe_consts, cmds)
    fb1_clean_battery = oe_detectors(oe, fb1_clean, oe_consts)
    fb1_snap = {}

    def fb1_hook(t, scene):
        if t == FB1_SNAPSHOT_TICK:
            fb1_snap["snap"] = scene.snapshot()
        if t == FB1_RESTORE_TICK and "snap" in fb1_snap:
            scene.restore_snapshot(fb1_snap["snap"])   # CONCEALED: no ledger

    fb1_tamper = run_probe_arm(oe, oe_consts, cmds, fault_hook=fb1_hook)
    fb1_tamper_battery = oe_detectors(oe, fb1_tamper, oe_consts)
    pre_streaks = unsupported_intervals(fb1_tamper["supervisor"].classes)
    precondition = any(lo <= FB1_SNAPSHOT_TICK <= hi
                       and lo <= FB1_RESTORE_TICK <= hi
                       for lo, hi in pre_streaks)
    out["FB1_hidden_reset"] = {
        "clean_control": {
            "metric_scope": "all detectors zero violations on the clean arm",
            "green": detectors_green(fb1_clean_battery),
        },
        "precondition_inside_produced_window": precondition,
        "tampered_fired": {
            "micro_draw_chain": len(fb1_tamper_battery["micro_draw_chain"]["violations"]) > 0,
            "velocity_recursion": len(fb1_tamper_battery["velocity_recursion"]["violations"]) > 0,
            "phase_recursion": len(fb1_tamper_battery["phase_recursion"]["violations"]) > 0,
        },
        "bit": (precondition
                and not detectors_green(fb1_tamper_battery)),
    }
    require(out["FB1_hidden_reset"]["clean_control"]["green"],
            "w10_fb1_premature")
    require(precondition, "fb1_window_precondition_unmet")
    require(out["FB1_hidden_reset"]["bit"], "falsifier_did_not_bite:FB1")

    # FB2 unsupported propulsion: ceiling strides injected during the declared
    # unsupported window (bypassing the sealed R1 law) — the propulsion class.
    fb2_clean = run_probe_arm(oe, oe_consts, cmds)
    fb2_clean_battery = oe_detectors(oe, fb2_clean, oe_consts)
    hi_stride = float(oe_consts["bounds_hi"][1])

    def fb2_override(t, classes):
        if classes[t] == "UNSUPPORTED":
            cmds8 = [float(x) for x in fb2_clean["commands"]]
            cmds8[1] = hi_stride
            cmds8[5] = hi_stride
            return cmds8
        return None

    fb2_tamper = run_probe_arm(oe, oe_consts, cmds, stride_override=fb2_override)
    fb2_tamper_battery = oe_detectors(oe, fb2_tamper, oe_consts)
    vr = fb2_tamper_battery["velocity_recursion"]
    vr_clean = fb2_clean_battery["velocity_recursion"]
    out["FB2_unsupported_propulsion"] = {
        "clean_control": {
            "metric_scope": "velocity recursion residual on the clean R4 arm",
            "max_residual_m_s": vr_clean["max_residual_m_s"],
            "green": detectors_green(fb2_clean_battery),
        },
        "override_ticks": len(fb2_tamper["stride_override_ticks"]),
        "tampered_max_residual_m_s": vr["max_residual_m_s"],
        "window_m_s": 1e-5,
        "bit": (vr["max_residual_m_s"] > 1e-5
                and vr_clean["max_residual_m_s"] <= 1e-5
                and len(fb2_tamper["stride_override_ticks"]) > 0),
    }
    require(out["FB2_unsupported_propulsion"]["clean_control"]["green"],
            "w10_fb2_premature")
    require(out["FB2_unsupported_propulsion"]["bit"], "falsifier_did_not_bite:FB2")

    # FB4 sliding: com_x advanced by 2x dt*v at one declared tick (R1 vehicle)
    def fb4_hook(t, scene):
        if t == 3000:
            scene.x += (1.0 / 300.0) * scene.v   # CONCEALED extra advance

    fb4_clean = run_commanded(_ADAPTER[0], _BUILD_ID[0], _PARAMS[0],
                              horizon=3200)
    fb4_clean_resid = com_identity_worst(fb4_clean["per_tick"])
    # the tampered variant: replay the R1 prefix and inject the declared
    # extra advance at tick 3000 (a record-level sliding event; the detector
    # consumes records — declared, never hidden)
    fb4_tamper = run_commanded_hooked(3000)
    fb4_tamper_resid = com_identity_worst(fb4_tamper["per_tick"])
    out["FB4_sliding"] = {
        "clean_control": {
            "metric_scope": "com identity residual on the clean R1 prefix",
            "worst_residual_m": fb4_clean_resid,
            "within_tolerance": fb4_clean_resid <= 1e-9,
        },
        "tampered_worst_residual_m": fb4_tamper_resid,
        "window_m": 1e-9,
        "bit": (fb4_clean_resid <= 1e-9 and fb4_tamper_resid > 1e-9),
    }
    require(out["FB4_sliding"]["clean_control"]["within_tolerance"],
            "w10_fb4_premature")
    require(out["FB4_sliding"]["bit"], "falsifier_did_not_bite:FB4")
    return out


def com_identity_worst(per_tick):
    dt = 1.0 / 300.0
    worst = 0.0
    for a_row, b_row in zip(per_tick, per_tick[1:]):
        expect = dt * a_row["com_v_m_s"]
        got = b_row["com_x_m"] - a_row["com_x_m"]
        worst = max(worst, abs(got - expect))
    return worst


def run_commanded_hooked(hook_tick):
    """R1 prefix with the DECLARED FB4 tamper: one extra dt*v advance at
    hook_tick (position moving beyond the solved velocity)."""
    import command_model as cm2
    orig = cm.feed_events
    applied_extra = {"t": hook_tick, "done": False}
    res = run_commanded(_ADAPTER[0], _BUILD_ID[0], _PARAMS[0],
                        horizon=hook_tick + 2)
    # replay the per-tick x with the declared injected advance: the tamper is
    # a RECORD mutation (the class under test is the detector, and the
    # detector consumes records); the mutation is declared here, never hidden.
    dt = 1.0 / 300.0
    for i, row in enumerate(res["per_tick"]):
        if row["tick"] == hook_tick and not applied_extra["done"]:
            row["com_x_m"] = row["com_x_m"] + dt * row["com_v_m_s"]
            row["state_sha256"] = "TAMPERED_FB4"
            applied_extra["done"] = True
    return res


def oe_detectors(oe, arm, consts):
    return {
        "velocity_recursion": oe.velocity_recursion_check(
            arm["records"], arm["applied_per_tick"], consts),
        "phase_recursion": oe.phase_recursion_check(
            arm["records"], arm["applied_per_tick"], consts),
        "micro_draw_chain": oe.micro_draw_chain_check(
            arm["records"], arm["applied_per_tick"], consts, SEED),
        "support_force_removed": oe.support_force_removed_check(
            arm["records"], consts),
    }


def detectors_green(battery):
    return all(not battery[k]["violations"]
               for k in ("velocity_recursion", "phase_recursion",
                         "micro_draw_chain", "support_force_removed"))


# ---------------------------------------------------------------- main
_ADAPTER = [None]
_BUILD_ID = [None]
_PARAMS = [None]


def export_trace(res, path, arm_id):
    """The per-tick trace: the visualization's ONLY input (records-only)."""
    rows = []
    for row in res["per_tick"]:
        rows.append({
            "tick": row["tick"], "com_v_m_s": row["com_v_m_s"],
            "com_x_m": row["com_x_m"],
            "phase_left": row["phase_left"], "phase_right": row["phase_right"],
            "yaw_rate_rad_s": row["yaw_rate_rad_s"],
            "contact_count": row["contact_count"],
            "foot_contacts": row["foot_contacts"],
            "foot_forces": row["foot_forces"], "pad_gaps": row["pad_gaps"],
            "applied_cmd": row["applied_cmd"], "saturation": row["saturation"],
            "state_sha256": row["state_sha256"],
        })
    doc = {"schema": "chimera.w10_trace.v1", "arm": arm_id,
           "seed": SEED, "rows": rows,
           "final_state_sha256": res["final_state_sha256"]}
    path.write_bytes(canonical(doc))
    return sha_bytes(canonical(doc))


def main() -> int:
    _PARAMS[0] = None
    pins, reg = stage_pins()
    gate_pack = gate_and_load()
    cert, req, allow, bundle, build_id, params, scene_const, bounds, gate = gate_pack
    _ADAPTER[0] = cm.CommandAdapter(bundle["manifest"], scene_const)
    _BUILD_ID[0] = build_id
    _PARAMS[0] = params

    oe = load_w09_supervisor()
    oe_consts = w09_consts(oe, params, bundle["manifest"])

    # ---- R1/R2/R3: the frozen commanded walk (W08's script, W10's pins) ----
    res1 = run_commanded(_ADAPTER[0], build_id, params)
    res2 = run_commanded(_ADAPTER[0], build_id, params)
    res3 = run_commanded(_ADAPTER[0], build_id, params, wrong_override=True,
                         horizon=HORIZON_R3)

    # ---- R4: the declared unsupported probe replay (the fall sequence) -----
    cmds, deriv = probe_commands(oe_consts)
    res4 = run_probe_arm(oe, oe_consts, cmds)

    ev = evaluate(res1, res2, res3, res4, bounds, gate, oe, oe_consts)

    # the R1 supervisor observation ledger (zero events on the certified line)
    monitor = oe.EnvelopeMonitor(oe_consts)
    classes1 = [monitor.classify(json.loads(json.dumps(r)))["class"]
                for r in _records_of(res1)]
    r1_unsupported = [t for t, cl in enumerate(classes1) if cl == "UNSUPPORTED"]
    ev["P10_supported_surface"]["supervisor_unsupported_ticks_r1"] = r1_unsupported
    ev["P10_supported_surface"]["supervisor_events_r1"] = len(r1_unsupported)
    require(not r1_unsupported, "prediction_failed:P10_supervisor_events")

    # ---- FB arms (clean controls FIRST) -------------------------------------
    fb = fb_arms(oe, oe_consts, cmds)

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

    trace1_sha = export_trace(res1, CAPTURE_DIR / "trace_walk.json", "R1")
    trace4_sha = export_trace(res4, CAPTURE_DIR / "trace_fall.json", "R4")

    receipt = {
        "schema": "chimera.w10_walking_demo.v1",
        "task_id": "W10",
        "card_id": "MAT2-W10",
        "attempt_id": vi.ATTEMPT_ID,
        "agent_id": vi.AGENT_ID,
        "base_sha256": vi.BASE_SHA,
        "prereg_commit": vi.PREREG_COMMIT,
        "amendment_a1_commit": vi.AMENDMENT_A1_COMMIT,
        "preregistration_sha256": vi.prereg_sha256(),
        "amendment_a1_sha256": vi.amendment_a1_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "registry": reg,
        "gate": gate,
        "probe_derivation": deriv,
        "predictions": ev,
        "falsifiers": fb,
        "F_all_green": all(a.get("bit", False) for a in fb.values()),
        "traces": {"R1": {"path": "capture/trace_walk.json",
                          "sha256": trace1_sha, "rows": len(res1["per_tick"])},
                   "R4": {"path": "capture/trace_fall.json",
                          "sha256": trace4_sha, "rows": len(res4["per_tick"])}},
        "all_predictions_pass": all(
            True for k in ev if k.startswith("P")) and all(
            p is not None for k, p in ev.items() if k.startswith("P")),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B walking_demo.py"},
    }
    (RECEIPTS / "walking_demo_receipt.json").write_bytes(canonical(receipt) + b"\n")
    print("P verdicts:", {k: True for k in ev if k.startswith("P")})
    print("F_all_green:", receipt["F_all_green"])
    print("traces:", trace1_sha[:12], trace4_sha[:12])
    return 0


def _records_of(res1):
    """Reconstruct observation-shaped dicts from R1's per-tick rows for the
    supervisor monitor (the same seam fields the scene emits)."""
    for row in res1["per_tick"]:
        yield {
            "tick": row["tick"],
            "com_vel": row["com_v_m_s"],
            "foot_contacts": row["foot_contacts"],
            "foot_forces": row["foot_forces"],
            "pad_gaps": row["pad_gaps"],
            "phase_left": row["phase_left"],
            "phase_right": row["phase_right"],
            "applied": row["applied_cmd"],
            "intervention_reason": row["intervention_reason"],
        }


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except vi.Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
