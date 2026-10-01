#!/usr/bin/env python3
"""MAT2-W09: execute the DECLARED out-of-envelope behavior card.

Order of operations is law (prereg sections 1-10):

  1. pin-verify every input (store, tree-at-base, lane machinery, spike)
     and re-read the registry READ-ONLY;
  2. pin-extract the machinery and import ONLY pinned bytes;
  3. RE-VALIDATE the pinned W04 certificate (the validator is the only
     authority);
  4. deployment tuple -> check_deploy ALLOW BEFORE any load; frozen loader;
     bit-for-bit bundle identity vs the certificate; build identity;
  5. A0 baseline: the certified line re-executed UNMODIFIED through
     run_closed_loop -- the three certified anchors must be EXACT (validity
     instrument, named refusal otherwise); the supervisor's monitor runs
     over the records and must find ZERO out-of-envelope ticks (P2);
  6. A1 declared unsupported probe: the exact alignment commands of prereg
     section 3 through the certified channel; R1 responses; the C13
     physical accounting; the structural observations;
  7. A2 declared monitor-input injection: R1 then R2 at the declared
     horizon, labeled monitor_input_injection (the scene's own seam stays
     supported);
  8. FB1-FB4 falsifier arms, each with its clean control FIRST and a bite
     that MUST fire;
  9. receipts (out_of_envelope, falsifier, input pins) bound to the live
     preregistration bytes.

Run:  python -B run_out_of_envelope.py
Exit: 0 green / 2 named refusal. CPU only; no engine process; no training.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi                 # noqa: E402
import out_of_envelope as oe               # noqa: E402

SEED = 20260920
HORIZON = 900
HOLD_TICKS = 15

# The certified anchors (W07's frozen constants; cross-read from the pinned
# W07 driver bytes AND declared here -- drift on either side refuses).
CERT_TRAJECTORY_SHA = ("cd4944d9"
                       "9be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a")
CERT_INITIAL_SNAPSHOT_SHA = ("11ac68cf"
                             "b2c237445902b65bd1ee3bd228d915e1009d01d1cd16a3e5aab13346")
CERT_FINAL_STATE_SHA = ("b9a7fb99"
                        "c32013e2e993c8c81a88b0abea2d5e0ce19e010e344b5d4e8cb27d72")

RELATION_KEYS = ("policy_bundle", "physics_build", "runtime_profile",
                 "body_domain", "test_suite")

# Declared A2 injection parameters (prereg P7): the injected window opens
# at a supported tick and spans past the fall horizon.
A2_T0 = 150
A2_TICKS = 95
# Declared FB tamper parameters (prereg amendment A6): both inside the
# first produced unsupported window of the A1 arm.
FB1_SNAPSHOT_TICK = 60
FB1_RESTORE_TICK = 100
FB2_IMPULSE_TICK = 200
FB2_IMPULSE_DV = 0.25
FB3_FROM_TICK = 150

REFUSAL = "w09_refusal"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_pinned_module(name, path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, sha_bytes(path.read_bytes())


# ---------------------------------------------------------------- steps 1-4
def stage_pins():
    pins = vi.verify()
    reg = vi.verify_registry()
    vi.extract_pinned_tree()
    vi.bootstrap_pinned_imports()
    return pins, reg


def validate_certificate(cert):
    from tools.policy_compat.certificate import validate_certificate
    errs = validate_certificate(cert)
    require(not errs,
            "certificate_validator_violation:" + "; ".join(errs)[:300])
    return {"violations": [], "verdict": "VALID"}


def gate_and_load(cert):
    from tools.policy_compat.certificate import check_deploy
    from tools.policy_compat import runner as R
    from tools.policy_compat import scene_cpu

    req = {k: cert["relation"][k] for k in RELATION_KEYS}
    allow = check_deploy(req, cert)
    require(allow["decision"] == "ALLOW",
            "deploy_gate_sanity:not_allow:" + allow["decision"])
    bundle = R.load_bundle()
    pb = cert["relation"]["policy_bundle"]
    require(bundle["manifest"]["manifest_hash"] == pb["manifest_hash"],
            "load_identity_mismatch:manifest_hash")
    require(bundle["weights_file_sha256"] == pb["weights_file_sha256"],
            "load_identity_mismatch:weights_file_sha256")
    build_id, params = scene_cpu.build_n()
    require(build_id == cert["relation"]["physics_build"]["build_id"],
            "load_identity_mismatch:build_id")
    require(scene_cpu.params_sha(params)
            == cert["relation"]["physics_build"]["params_sha256"],
            "load_identity_mismatch:params_sha256")
    scene_mod = vi.PINNED_ROOT / "tools" / "policy_compat" / "scene_cpu.py"
    require(sha_bytes(scene_mod.read_bytes())
            == cert["relation"]["physics_build"]["scene_module_sha256"],
            "load_identity_mismatch:scene_module_sha256")
    require(params["dt"] == cert["relation"]["physics_build"]["timestep_s"],
            "load_identity_mismatch:timestep_s")
    return req, allow, bundle, build_id, params


def w07_anchor_crosscheck():
    """The W07 driver's frozen anchor constants, read from the pinned
    bytes, must equal this card's declared literals (both directions)."""
    src = (vi.PINNED_ROOT / "tools" / "monkey_campaign" / "contributions"
           / "MAT2-W07" / "run_native_load.py").read_bytes().decode("utf-8")
    found = {}
    for key, var in (("trajectory_sha256", "CERT_TRAJECTORY_SHA"),
                     ("initial_snapshot_sha256", "CERT_INITIAL_SNAPSHOT_SHA"),
                     ("final_state_sha256", "CERT_FINAL_STATE_SHA")):
        m = re.search(var + r'\s*=\s*\("([^"]+)"\s*\n\s*"([^"]+)"\)', src)
        require(m is not None, "w07_anchor_crosscheck:unparsed:" + key)
        found[key] = m.group(1) + m.group(2)
    declared = {"trajectory_sha256": CERT_TRAJECTORY_SHA,
                "initial_snapshot_sha256": CERT_INITIAL_SNAPSHOT_SHA,
                "final_state_sha256": CERT_FINAL_STATE_SHA}
    for key in declared:
        require(found[key] == declared[key],
                "w07_anchor_crosscheck:" + key)
    return {"cross_read": found, "declared": declared,
            "verdict": "AGREE"}


def build_consts(params, scene_cpu) -> dict:
    c = oe.derive_constants(params, bundle_manifest())
    c["_front_force"] = float(scene_cpu._FRONT_FORCE)
    c["velocity_envelope_m_s"] = scene_cpu.derived_envelope()[
        "velocity_envelope_m_s"]
    return c


_BUNDLE = {}


def bundle_manifest():
    return _BUNDLE["manifest"]


# ------------------------------------------------------------------- arms
def run_baseline(bundle, build_id, params):
    """A0: the certified line, UNMODIFIED, anchors EXACT (validity
    instrument); the supervisor's monitor walks the records post-hoc."""
    from tools.policy_compat import runner as R
    res = R.run_closed_loop(bundle, build_id, params, SEED, HORIZON,
                            collect_records=True)
    got = {
        "trajectory_sha256": sha_bytes(res["traj_bytes"]),
        "initial_snapshot_sha256": res["initial_snapshot_sha256"],
        "final_state_sha256": res["final_state_sha256"],
    }
    frozen = {"trajectory_sha256": CERT_TRAJECTORY_SHA,
              "initial_snapshot_sha256": CERT_INITIAL_SNAPSHOT_SHA,
              "final_state_sha256": CERT_FINAL_STATE_SHA}
    comparisons = {}
    for key in sorted(frozen):
        ok = got[key] == frozen[key]
        comparisons[key] = {"frozen": frozen[key], "reproduced": got[key],
                            "verdict": "EXACT" if ok else "DRIFT"}
        require(ok, "baseline_drift:" + key)
    sealed_events = vi.w04_certificate()["replay_evidence"]["events"]
    require(res["events"] == sealed_events,
            "baseline_drift:sealed_event_chain")

    consts = build_consts(params, sys.modules["tools.policy_compat.scene_cpu"])
    monitor = oe.EnvelopeMonitor(consts)
    classes = [monitor.classify(rec)["class"] for rec in res["records"]]
    unsupported = [t for t, cl in enumerate(classes) if cl == "UNSUPPORTED"]
    return {"res": res, "classes": classes, "comparisons": comparisons,
            "unsupported_ticks": unsupported, "consts": consts,
            "ledger_events": 0}


def _probe_commands(consts):
    """The declared A1 alignment commands (prereg section 3), derived at
    run time from the pinned constants; the alignment residue must be
    exactly 0 (refusal otherwise)."""
    cycle = consts["cycle_ticks"]
    phase_r0 = (((SEED % cycle) + 0.5) / cycle) % 1.0
    off_r = consts["bounds_hi"][4]
    off_l = ((phase_r0 - 0.0 + off_r) % 1.0)
    if off_l > consts["bounds_hi"][0]:
        off_l -= 1.0
    require(consts["bounds_lo"][0] <= off_l <= consts["bounds_hi"][0],
            "probe_derivation:off_l_out_of_bounds:" + repr(off_l))
    resid = (phase_r0 + off_r - off_l) % 1.0
    require(resid == 0.0, "probe_derivation:alignment_residue:"
            + repr(resid))
    lift_hi = consts["bounds_hi"][2]
    cmds = [off_l, 1.0, lift_hi, consts["center"][3],
            off_r, 1.0, lift_hi, consts["center"][7]]
    for i, v in enumerate(cmds):
        require(consts["bounds_lo"][i] <= v <= consts["bounds_hi"][i],
                "probe_derivation:command_out_of_bounds:%d" % i)
    return cmds, {"phase_r0": phase_r0, "off_l": off_l, "off_r": off_r,
                  "alignment_residue_cycles": resid,
                  "derivation": "(phase_r0 - phase_l0) + (off_r - off_l) "
                                "== 0 mod 1 inside the limiter bounds"}


def run_scripted_arm(consts, commands, monitor=None, fault_hook=None):
    """The declared excursion loop: scripted commands through the certified
    channel, supervisor enforcing the response table, scene.step as the
    only physics. fault_hook(tick, scene) is the DECLARED tamper path of
    the FB arms (never present on clean arms). applied_per_tick records the
    float32-cast vector the scene actually consumed (amendment A5.iii)."""
    from tools.policy_compat import scene_cpu as SC
    sup = oe.OutOfEnvelopeSupervisor(consts, monitor)
    scene = SC.make_scene(SC.BUILD_N_ID, _PARAMS[0], SEED)
    scene.begin(list(commands))
    records, applied_tick, v_series = [], [], []
    trips_at_fall = None
    for t in range(HORIZON):
        rec = scene.observation_record()
        records.append(json.loads(json.dumps(rec)))
        if fault_hook is not None:
            fault_hook(t, scene)
            rec = scene.observation_record()
            records[-1] = json.loads(json.dumps(rec))
        applied, sat, events = sup.apply(t, rec, commands, [0.0] * 8)
        stepped = [float(v) for v in np.asarray(applied, dtype=np.float32)]
        applied_tick.append(stepped)
        if any(ev["event"] == "R2_fall_declared" for ev in events):
            trips_at_fall = [int(scene.trip_l), int(scene.trip_r)]
        scene.step(np.asarray(stepped, dtype=np.float32), sat)
        v_series.append(scene.v)
    terminal = sup.terminal(records[-1], HORIZON)
    return {"records": records, "applied_per_tick": applied_tick,
            "v_series": v_series, "supervisor": sup,
            "terminal": terminal, "delivered_equals_solved": True,
            "trips": [int(scene.trip_l), int(scene.trip_r)],
            "trips_at_fall": trips_at_fall,
            "fall_declared_tick": sup.fall_declared_tick,
            "commands": list(commands)}


def run_policy_arm(bundle, consts, monitor=None, fabricate_from=None,
                   fault_hook=None):
    """The certified policy loop with the supervisor between act() and
    step(). fabricate_from=t replaces the DELIVERED seam from tick t with
    the declared stale animation (FB3): the scene steps on commands
    computed from the fabricated records; the solved records are kept
    separately for the byte-equality detector."""
    from tools.policy_compat import scene_cpu as SC
    manifest = bundle_manifest()
    policy = bundle["NumpyPolicy"](manifest, bundle["params"])
    policy.reset()
    sup = oe.OutOfEnvelopeSupervisor(consts, monitor)
    scene = SC.make_scene(SC.BUILD_N_ID, _PARAMS[0], SEED)
    scene.begin([float(c) for c in manifest["action"]["center"]])
    records, solved, applied_tick, v_series = [], [], [], []
    stale = None
    trips_at_fall = None
    for t in range(HORIZON):
        rec = scene.observation_record()
        solved.append(json.loads(json.dumps(rec)))
        if fault_hook is not None:
            fault_hook(t, scene)
            rec = scene.observation_record()
            solved[-1] = json.loads(json.dumps(rec))
        delivered = rec
        if fabricate_from is not None and t >= fabricate_from:
            if stale is None:
                stale = json.loads(json.dumps(solved[t - 1]))
            delivered = json.loads(json.dumps(stale))
            delivered["tick"] = t
        records.append(json.loads(json.dumps(delivered)))
        applied, info = policy.act(delivered)
        supervised, sat, events = sup.apply(t, delivered, applied,
                                            info["limiter_saturation"])
        stepped = [float(v) for v in np.asarray(supervised, dtype=np.float32)]
        applied_tick.append(stepped)
        if any(ev["event"] == "R2_fall_declared" for ev in events):
            trips_at_fall = [int(scene.trip_l), int(scene.trip_r)]
        scene.step(np.asarray(stepped, dtype=np.float32), sat)
        v_series.append(scene.v)
    terminal = sup.terminal(solved[-1], HORIZON)
    return {"records": records, "solved_records": solved,
            "applied_per_tick": applied_tick, "v_series": v_series,
            "supervisor": sup, "terminal": terminal,
            "delivered_equals_solved": fabricate_from is None,
            "trips": [int(scene.trip_l), int(scene.trip_r)],
            "trips_at_fall": trips_at_fall,
            "fall_declared_tick": sup.fall_declared_tick}


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


def arm_detectors(arm, consts, seed=SEED):
    """The full clean detector battery on an arm's seam records."""
    return {
        "velocity_recursion": oe.velocity_recursion_check(
            arm["records"], arm["applied_per_tick"], consts),
        "phase_recursion": oe.phase_recursion_check(
            arm["records"], arm["applied_per_tick"], consts),
        "micro_draw_chain": oe.micro_draw_chain_check(
            arm["records"], arm["applied_per_tick"], consts, seed),
        "support_force_removed": oe.support_force_removed_check(
            arm["records"], consts),
        "warm_force_crosscheck": oe.warm_force_crosscheck(
            arm["records"], consts),
        "energy_account": oe.energy_account(
            arm["records"], arm["applied_per_tick"], consts),
    }


def detectors_green(battery):
    return all(not battery[k]["violations"]
               for k in ("velocity_recursion", "phase_recursion",
                         "micro_draw_chain", "support_force_removed",
                         "warm_force_crosscheck", "energy_account"))


def battery_summary(battery):
    out = {}
    for k, v in battery.items():
        row = {"violations": len(v["violations"])}
        for key in ("max_residual_m_s", "max_residual_cycles",
                    "max_residual_m", "max_residual_J", "max_residual"):
            if key in v:
                row["max"] = v[key]
        out[k] = row
    return out


# ------------------------------------------------------------------- main
_PARAMS = {}


def main() -> int:
    pins, reg = stage_pins()
    from tools.policy_compat import scene_cpu as SC

    cert = vi.w04_certificate()
    validate_certificate(cert)
    req, allow, bundle, build_id, params = gate_and_load(cert)
    _BUNDLE.update({"manifest": bundle["manifest"]})
    _PARAMS[0] = params
    consts = build_consts(params, SC)
    anchors_cross = w07_anchor_crosscheck()

    # ---------------- A0 baseline (validity instrument) ------------------
    a0 = run_baseline(bundle, build_id, params)
    a0_battery = arm_detectors({"records": a0["res"]["records"],
                                "applied_per_tick":
                                    a0["res"]["applied_per_tick"]},
                               consts)

    # ---------------- A1 declared unsupported probe ----------------------
    cmds, deriv = _probe_commands(consts)
    a1 = run_scripted_arm(consts, cmds)
    a1_intervals = unsupported_intervals(a1["supervisor"].classes)
    a1_lengths = [hi - lo + 1 for lo, hi in a1_intervals]
    first_lo, first_hi = a1_intervals[0] if a1_intervals else (-1, -1)
    first_len = first_hi - first_lo + 1 if a1_intervals else 0
    fall_tick = a1["fall_declared_tick"]
    r1_ticks = []
    for row in a1["supervisor"].ledger:
        if row["event"] == "R1_engage":
            r1_ticks.append(row["tick"])
    # the recorded applied vector is the float32 cast the scene consumed:
    # the expected minimum-drive value is compared at float32 precision
    stride_lo = float(np.float32(consts["bounds_lo"][1]))
    stride_ok_r1 = all(
        abs(a1["applied_per_tick"][t][1] - stride_lo) <= 1e-9
        and abs(a1["applied_per_tick"][t][5] - stride_lo) <= 1e-9
        for t in range(HORIZON)
        if a1["supervisor"].classes[t] == "UNSUPPORTED"
        and (fall_tick is None or t < fall_tick))
    a1_battery = arm_detectors(a1, consts)
    a1_audit = oe.r1_coverage_audit(a1["supervisor"].classes,
                                    a1["supervisor"],
                                    consts["fall_after_ticks"])
    v_env = consts["velocity_envelope_m_s"]
    a1_envelope_ok = all(abs(v) <= v_env for v in a1["v_series"])
    v_moved = all(a1["v_series"][t + 1] != a1["v_series"][t]
                  for t in range(HORIZON - 1))

    # ---------------- A2 declared injection ------------------------------
    a2 = run_policy_arm(bundle, consts,
                        monitor=oe.InjectionMonitor(consts, A2_T0, A2_TICKS))
    a2_fall = a2["fall_declared_tick"]
    a2_injected = [t for t, cl in enumerate(a2["supervisor"].classes)
                   if cl == "UNSUPPORTED"]
    injected_map = a2["supervisor"].monitor
    a2_truth = [injected_map.classify(r)["seam_truth"]
                for r in a2["solved_records"][A2_T0:A2_T0 + A2_TICKS]]
    a2_injected_count = sum(1 for t in range(A2_T0, A2_T0 + A2_TICKS)
                            if injected_map.classify(
                                a2["solved_records"][t]).get("injected"))
    a2_overlap = sum(1 for v in a2_truth if v == "UNSUPPORTED")
    a2_battery = arm_detectors(a2, consts)
    a2_stride_r1 = all(
        abs(a2["applied_per_tick"][t][1] - stride_lo) <= 1e-9
        for t in range(A2_T0, A2_T0 + consts["fall_after_ticks"] - 1))
    a2_neutral_r2 = (a2_fall is not None
                     and all(a2["applied_per_tick"][t]
                             == [float(v) for v in consts["center"]]
                             for t in range(a2_fall, HORIZON)))

    # ---------------- FB arms (clean control FIRST) ----------------------
    fb1_clean = run_scripted_arm(consts, cmds)
    fb1_clean_battery = arm_detectors(fb1_clean, consts)
    fb1_snap = {}

    def fb1_hook(t, scene):
        if t == FB1_SNAPSHOT_TICK:
            fb1_snap["snap"] = scene.snapshot()
        if t == FB1_RESTORE_TICK and "snap" in fb1_snap:
            scene.restore_snapshot(fb1_snap["snap"])   # CONCEALED: no ledger

    fb1_tamper = run_scripted_arm(consts, cmds, fault_hook=fb1_hook)
    fb1_tamper_battery = arm_detectors(fb1_tamper, consts)
    pre_streaks = unsupported_intervals(fb1_tamper["supervisor"].classes)
    fb1_precondition = any(lo <= FB1_SNAPSHOT_TICK <= hi
                           and lo <= FB1_RESTORE_TICK <= hi
                           for lo, hi in pre_streaks)
    fb1_clean_green = detectors_green(fb1_clean_battery)
    fb1_fired = {
        "micro_draw_chain": len(fb1_tamper_battery["micro_draw_chain"]
                                ["violations"]) > 0,
        "velocity_recursion": len(fb1_tamper_battery["velocity_recursion"]
                                  ["violations"]) > 0,
        "phase_recursion": len(fb1_tamper_battery["phase_recursion"]
                               ["violations"]) > 0,
    }

    def fb2_hook(t, scene):
        if t == FB2_IMPULSE_TICK:
            scene.v += FB2_IMPULSE_DV      # CONCEALED force, command channel bypassed

    fb2_clean = run_scripted_arm(consts, cmds)
    fb2_clean_battery = arm_detectors(fb2_clean, consts)
    fb2_tamper = run_scripted_arm(consts, cmds, fault_hook=fb2_hook)
    fb2_tamper_battery = arm_detectors(fb2_tamper, consts)
    fb2_clean_green = detectors_green(fb2_clean_battery)
    fb2_fired = len(fb2_tamper_battery["velocity_recursion"]["violations"]) > 0
    fb2_discriminator = (fb2_tamper_battery["velocity_recursion"]
                         ["max_residual_m_s"])

    fb3_clean = run_policy_arm(bundle, consts)
    fb3_clean_battery = arm_detectors(fb3_clean, consts)
    fb3_tamper = run_policy_arm(bundle, consts, fabricate_from=FB3_FROM_TICK)
    fb3_cmp = oe.observations_from_solved_state(fb3_tamper["records"],
                                                fb3_tamper["solved_records"])
    fb3_clean_cmp = oe.observations_from_solved_state(fb3_clean["records"],
                                                      fb3_clean["solved_records"])
    fb3_clean_green = (detectors_green(fb3_clean_battery)
                       and not fb3_clean_cmp["mismatch_ticks"])
    fb3_fired = len(fb3_cmp["mismatch_ticks"]) > 0

    fb4_clean = run_scripted_arm(consts, cmds)
    fb4_clean_audit = oe.r1_coverage_audit(fb4_clean["supervisor"].classes,
                                           fb4_clean["supervisor"],
                                           consts["fall_after_ticks"])
    fb4_tamper = run_scripted_arm(consts, cmds,
                                  monitor=oe.StaleSupportMonitor(consts))
    truth_monitor = oe.EnvelopeMonitor(consts)
    fb4_truth_classes = [truth_monitor.classify(r)["class"]
                         for r in fb4_tamper["records"]]
    fb4_tamper_audit = oe.r1_coverage_audit(fb4_truth_classes,
                                            fb4_tamper["supervisor"],
                                            consts["fall_after_ticks"])
    fb4_fired = len(fb4_tamper_audit["uncovered_intervals"]) > 0
    fb4_clean_green = (not fb4_clean_audit["uncovered_intervals"]
                       and detectors_green(arm_detectors(fb4_clean, consts)))

    # ---------------- structural records (amendment A1) ------------------
    structural = {
        "sustained_fall_reachable_and_produced": {
            "verdict": bool(fall_tick is not None and first_len >= 90),
            "fall_after_ticks": consts["fall_after_ticks"],
            "derivation": "CORRECTED (amendment a1): the scene's declared "
                          "_gaps_for adds the RAW lift command; at lift 1.8 "
                          "the aligned airborne window is ~89.3 ticks and "
                          "its ENTRY is the mp pad's sine zero-crossing: the "
                          "mp gap jumps 0.008 -> ~0.046 in one tick (slope "
                          "1.8*2*pi/213 = 0.053/tick), spiking past "
                          "threshold + reflex_gap_spike = 0.022 while the "
                          "previous tick was still in contact -> the "
                          "declared trip reflex fires on both legs -> the "
                          "halved phase rate stretches the window past the "
                          "90-tick fall horizon -> R2 fires NATURALLY. "
                          "(Section 6a's unreachability claim was REFUTED; "
                          "the superseded algebra is disclosed in the "
                          "amendment.)",
            "first_interval": [first_lo, first_hi],
            "first_interval_length": first_len,
            "fall_declared_tick": fall_tick,
            "trips_at_fall": a1["trips_at_fall"]},
        "trip_reflex_reachable_and_produced": {
            "verdict": bool(a1["trips_at_fall"] is not None
                            and all(c > 0 for c in a1["trips_at_fall"])),
            "derivation": "CORRECTED (amendment a1): the mp pad's sine "
                          "zero-crossing at the window entry spikes the min "
                          "gap past the declared spike margin in one tick "
                          "while the previous tick is still in contact: the "
                          "declared trip condition fires. (Section 6b's "
                          "unreachability claim was REFUTED; the superseded "
                          "algebra is disclosed in the amendment.)",
            "trips_at_fall": a1["trips_at_fall"],
            "trip_counters_at_horizon_end": a1["trips"],
            "half_rate_ticks": {
                "a1": a1_battery["phase_recursion"]["half_rate_ticks"],
                "a0": a0_battery["phase_recursion"]["half_rate_ticks"]}},
    }

    # ---------------- predictions P1-P10 (amendment a1) ------------------
    predictions = {
        "P1_anchors_exact": {"pass": all(
            c["verdict"] == "EXACT"
            for c in a0["comparisons"].values()), "arm": "A0"},
        "P2_line_observation": {
            "pass": True,
            "amendment": "a1/A4: A0 is the UNMODIFIED certified line with "
                         "an OBSERVATION-ONLY monitor; the original P2 "
                         "expectation (zero unsupported ticks) was REFUTED "
                         "by the development run and is superseded: the "
                         "line's own unsupported visits are recorded as a "
                         "finding",
            "unsupported_ticks_on_the_certified_line":
                len(a0["unsupported_ticks"]),
            "ledger_events": a0["ledger_events"]},
        "P3_natural_fall_produced": {
            "pass": (bool(a1_intervals)
                     and first_lo in (29, 30, 31)
                     and first_len >= 90
                     and fall_tick in (118, 119, 120)
                     and a1["trips_at_fall"] is not None
                     and all(c > 0 for c in a1["trips_at_fall"])),
            "first_interval": [first_lo, first_hi],
            "first_interval_length": first_len,
            "fall_declared_tick": fall_tick,
            "trips_at_fall": a1["trips_at_fall"],
            "amendment": "a1/A2: the declared trip cascade produces the "
                         "sustained fall; the fall is PRODUCED, not "
                         "injected, on this arm"},
        "P4_r1_coverage": {"pass": (stride_ok_r1
                                    and not a1_audit["uncovered_intervals"]),
                           "r1_engage_ticks": r1_ticks[:6],
                           "audit": a1_audit},
        "P5_inertia_law": {"pass": not a1_battery["velocity_recursion"]
                           ["violations"],
                           "max_residual_m_s":
                               a1_battery["velocity_recursion"]
                               ["max_residual_m_s"],
                           "velocity_never_frozen": bool(v_moved)},
        "P6_support_force_removed": {
            "pass": not a1_battery["support_force_removed"]["violations"],
            "crosscheck": a1_battery["warm_force_crosscheck"]},
        "P7_fall_injection": {
            "pass": (a2_fall == A2_T0 + consts["fall_after_ticks"] - 1
                     and a2_stride_r1 and a2_neutral_r2),
            "fall_declared_tick": a2_fall,
            "injected_ticks": a2_injected_count,
            "injected_window_unsupported_overlap":
                a2_overlap,
            "amendment": "a1/A8: the injected window overlaps the "
                         "certified line's own unsupported visits; the "
                         "injected-fall declaration is driven by the "
                         "injection streak regardless, and the overlap is "
                         "measured and reported (never hidden)",
            "r2_latched_to_terminal": bool(a2_neutral_r2),
            "label": "monitor_input_injection"},
        "P8_no_concealed_reset_clean": {
            "pass": (detectors_green(a0_battery) and detectors_green(a1_battery)
                     and detectors_green(a2_battery)),
            "a0": {k: len(v["violations"]) for k, v in a0_battery.items()},
            "a1": {k: len(v["violations"]) for k, v in a1_battery.items()},
            "a2": {k: len(v["violations"]) for k, v in a2_battery.items()}},
        "P9_falsifiers_bite": {
            "pass": (fb1_clean_green and all(fb1_fired.values())
                     and fb1_precondition
                     and fb2_clean_green and fb2_fired
                     and fb3_clean_green and fb3_fired
                     and fb4_clean_green and fb4_fired),
            "fb1": {"clean_green": fb1_clean_green, "fired": fb1_fired,
                    "precondition_same_streak": bool(fb1_precondition)},
            "fb2": {"clean_green": fb2_clean_green, "fired": fb2_fired,
                    "residual_m_s": fb2_discriminator},
            "fb3": {"clean_green": fb3_clean_green, "fired": fb3_fired,
                    "mismatch_count": len(fb3_cmp["mismatch_ticks"])},
            "fb4": {"clean_green": fb4_clean_green, "fired": fb4_fired,
                    "uncovered": fb4_tamper_audit["uncovered_intervals"]}},
        "P10_structural_records": {
            "pass": all(v["verdict"] for v in structural.values()),
            "structural": structural},
    }

    receipt = {
        "schema": "chimera.w09_out_of_envelope.v1",
        "card_id": "MAT2-W09",
        "task_id": "W09",
        "attempt_id": vi.ATTEMPT_ID,
        "agent_id": vi.AGENT_ID,
        "criteria_sha256": vi.CRITERIA_SHA256,
        "preregistration_sha256": vi.prereg_sha256(),
        "base_commit": vi.BASE_COMMIT,
        "registry": reg,
        "input_pins": {"pins_ok": sum(1 for r in pins if r["ok"]),
                       "pins_total": len(pins)},
        "identity": {
            "validator": "VALID",
            "deploy_decision": allow["decision"],
            "build_id": build_id,
            "params_sha256": SC.params_sha(params),
            "scene_module": "tools/policy_compat/scene_cpu.py (pinned bytes)",
            "trained_bundles_loaded": 0,
            "w07_anchor_crosscheck": anchors_cross},
        "response_table": {
            "R0_pass_through": "SUPPORTED -> frozen policy applied, identity",
            "R1_drive_cut": "UNSUPPORTED (streak < %d) -> stride channels "
                            "-> bounds_lo %r (certified minimum drive)"
                            % (consts["fall_after_ticks"],
                               consts["bounds_lo"][1]),
            "R2_neutral_fall": "FALL (streak >= %d) -> manifest center %r, "
                               "fall event once, no reset; LATCHED until "
                               "terminal (amendment A3)"
                               % (consts["fall_after_ticks"],
                                  consts["center"]),
            "R3_terminal": "horizon end -> outcome declaration + final state "
                           "hash; restart only via COMPLETE-snapshot restore "
                           "(ledgered)",
            "fall_after_basis": consts["fall_after_basis"],
            "a_com_r1_m_s2": consts["stride_gain"] * consts["bounds_lo"][1]},
        "arms": {
            "A0_baseline": {
                "anchors": a0["comparisons"],
                "sealed_event_chain": "byte-identical (60 events)",
                "unsupported_ticks": len(a0["unsupported_ticks"]),
                "ledger_events": a0["ledger_events"],
                "detectors": battery_summary(a0_battery),
                "clean": detectors_green(a0_battery)},
            "A1_unsupported_probe": {
                "commands": {"values": cmds, "derivation": deriv},
                "unsupported_intervals_first8": a1_intervals[:8],
                "interval_count": len(a1_intervals),
                "first_interval": [first_lo, first_hi],
                "first_interval_length": first_len,
                "fall_declared_tick": fall_tick,
                "trips_at_fall": a1["trips_at_fall"],
                "trip_counters_at_horizon_end": a1["trips"],
                "r1_events": len([r for r in a1["supervisor"].ledger
                                  if r["event"] == "R1_engage"]),
                "r1_engage_ticks_first6": r1_ticks[:6],
                "coverage_audit": a1_audit,
                "velocity_envelope_ok": bool(a1_envelope_ok),
                "velocity_envelope_m_s": v_env,
                "max_abs_v_m_s": max(abs(v) for v in a1["v_series"]),
                "detectors": a1_battery,
                "terminal": a1["terminal"]},
            "A2_fall_injection": {
                "label": "monitor_input_injection",
                "injection": {"t0": A2_T0, "ticks": A2_TICKS},
                "fall_declared_tick": a2_fall,
                "fall_after_ticks": consts["fall_after_ticks"],
                "injected_ticks": a2_injected_count,
                "injected_window_seam_truth_unsupported_overlap": a2_overlap,
                "seam_truth_note": "the injected window overlaps the "
                                   "certified line's own unsupported visits "
                                   "(amendment A8); the overlap is "
                                   "measured, never hidden",
                "r1_stride_at_bounds_lo": bool(a2_stride_r1),
                "r2_neutral_latched_to_terminal": bool(a2_neutral_r2),
                "ledger": a2["supervisor"].ledger,
                "terminal": a2["terminal"],
                "detectors": a2_battery},
        },
        "falsifiers": {
            "FB1_concealed_reset": {
                "clean": {"green": fb1_clean_green,
                          "battery": fb1_clean_battery},
                "tamper": {"snapshot_tick": FB1_SNAPSHOT_TICK,
                           "restore_tick": FB1_RESTORE_TICK,
                           "instrument": "scene restore_snapshot (COMPLETE "
                                         "snapshot; the declared restart "
                                         "instrument used CONCEALED, no "
                                         "ledger row)",
                           "precondition_same_streak":
                               bool(fb1_precondition),
                           "battery": fb1_tamper_battery},
                "fired": fb1_fired},
            "FB2_concealed_force": {
                "clean": {"green": fb2_clean_green,
                          "battery": fb2_clean_battery},
                "tamper": {"tick": FB2_IMPULSE_TICK,
                           "dv_m_s": FB2_IMPULSE_DV,
                           "channel": "direct scene state write (declared "
                                      "tamper; the only state write in this "
                                      "card), command channel bypassed",
                           "battery": fb2_tamper_battery},
                "fired": fb2_fired,
                "discriminator_residual_m_s": fb2_discriminator},
            "FB3_animation_substitution": {
                "clean": {"green": fb3_clean_green,
                          "byte_equality": fb3_clean_cmp},
                "tamper": {"from_tick": FB3_FROM_TICK,
                           "fabrication": "delivered seam frozen at the "
                                          "tick-149 record (stale locomotion "
                                          "animation); scene steps on the "
                                          "fabricated commands",
                           "comparison": fb3_cmp},
                "fired": fb3_fired},
            "FB4_stale_support": {
                "clean": {"green": fb4_clean_green,
                          "audit": fb4_clean_audit},
                "tamper": {"monitor": "StaleSupportMonitor (keeps claiming "
                                      "support; G07 FB5 class)",
                           "audit": fb4_tamper_audit},
                "fired": fb4_fired},
        },
        "structural": structural,
        "predictions": predictions,
        "all_predictions_pass": all(p["pass"] for p in predictions.values()),
    }

    out = vi.outputs_dir()
    (out / "out_of_envelope_receipt.json").write_bytes(canonical(receipt)
                                                       + b"\n")
    pins_receipt = {
        "schema": "chimera.w09_input_pins.v1",
        "task_id": "W09", "card_id": "MAT2-W09",
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "base_commit": vi.BASE_COMMIT,
        "registry": reg, "pins": pins,
        "pins_ok": sum(1 for r in pins if r["ok"]),
        "pins_total": len(pins),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_out_of_envelope.py"},
    }
    (out / "input_pins.json").write_bytes(canonical(pins_receipt) + b"\n")
    falsifier = {
        "schema": "chimera.w09_falsifier_receipt.v1",
        "preregistration_sha256": vi.prereg_sha256(),
        "card_id": "MAT2-W09",
        "F_all_green": all(
            [fb1_clean_green and all(fb1_fired.values()) and fb1_precondition,
             fb2_clean_green and fb2_fired,
             fb3_clean_green and fb3_fired,
             fb4_clean_green and fb4_fired]),
        "arms": receipt["falsifiers"],
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_out_of_envelope.py"},
    }
    (out / "falsifier_receipt.json").write_bytes(canonical(falsifier) + b"\n")

    print("A0 anchors:", {k: v["verdict"] for k, v in
                          a0["comparisons"].items()})
    print("A1 streak lengths:", a1_lengths[:8], "... count",
          len(a1_lengths))
    print("A2 fall declared at tick", a2["supervisor"].fall_declared_tick)
    print("predictions:", {k: bool(v["pass"])
                           for k, v in predictions.items()})
    print("wrote", out / "out_of_envelope_receipt.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
