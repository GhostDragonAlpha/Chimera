#!/usr/bin/env python3
"""MAT2-W07: LOAD the accepted walking policy (the frozen certified line) in
the native runtime and EXECUTE it consuming the certified observation/action
contract.

Order of operations is law (prereg section 2):

  1. pin-verify every input (W04 store records, W05/W06 merged in-tree
     bytes, the sealed lane machinery, the ingestion-spike evidence);
  2. pin-extract the machinery and import ONLY pinned bytes (zero
     machinery files modified);
  3. RE-VALIDATE the pinned W04 certificate (the validator is the only
     authority);
  4. build the deployment request tuple from the certificate's OWN
     relation and run check_deploy -- ALLOW is required BEFORE any load;
  5. ONLY THEN load the bundle through the FROZEN loader and require
     bit-for-bit bundle identity against the certificate's policy_bundle;
  6. verify the physics build identity (params sha, scene module sha,
     timestep);
  7. execute the loaded runtime (build N, seed 20260920, 900 ticks,
     collect_records) and require the three certified anchors EXACT plus
     the sealed event chain byte-identical;
  8. prove the runtime CONSUMES the certified contract: the 80-field v2
     observation interface (legacy 64-field consumer width), the frozen
     inference recipe recomputed independently at every decision tick --
     bit-exact against the runtime's applied commands --, the zero-order
     hold law, the actuation caps, the qualification bars;
  9. the pose-authority law: ACTION_REPLAY_REFUSED fires on a
     pre-recorded-action probe; the scene API has no pose-write channel;
     observations come from the solved state;
 10. the deploy gate's discrimination, executed in BOTH directions:
     trained-theta tuple BLOCK, foreign build BLOCK, missing certificate
     BLOCK;
 11. record the NAMED-MISSING outcome for the gated parts (the adopted
     assembly's runtime scene module, the TC-3 drive-table re-declaration,
     the product-engine live control path, the adopted-assembly C09
     re-run) -- never fabricate a load;
 12. emit receipts/native_load_receipt.json.

Run:  python -B run_native_load.py
Exit: 0 green / 2 named refusal. CPU only; no engine process; no training.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
import verify_inputs as vi

SEED = 20260920
HORIZON = 900
HOLD_TICKS = 15
DECISIONS_EXPECTED = 60

# The certified anchors (the W04 certificate's replay evidence; prereg P3).
CERT_TRAJECTORY_SHA = ("cd4944d9"
                       "9be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a")
CERT_INITIAL_SNAPSHOT_SHA = ("11ac68cf"
                             "b2c237445902b65bd1ee3bd228d915e1009d01d1cd16a3e5aab13346")
CERT_FINAL_STATE_SHA = ("b9a7fb99"
                        "c32013e2e993c8c81a88b0abea2d5e0ce19e010e344b5d4e8cb27d72")

RELATION_KEYS = ("policy_bundle", "physics_build", "runtime_profile",
                 "body_domain", "test_suite")


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
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, sha_bytes(path.read_bytes())


# ---------------------------------------------------------------- steps 1-2
def stage_pins():
    pins = vi.verify()
    reg = vi.verify_registry()
    vi.extract_pinned_tree()
    vi.bootstrap_pinned_imports()
    return pins, reg


# ---------------------------------------------------------------- step 3
def validate_certificate(cert):
    from tools.policy_compat.certificate import validate_certificate  # pinned bytes
    errs = validate_certificate(cert)
    require(not errs,
            "certificate_validator_violation:" + "; ".join(errs)[:300])
    return {"violations": [], "verdict": "VALID"}


# ---------------------------------------------------------------- steps 4-6
def gate_and_load(cert):
    from tools.policy_compat.certificate import check_deploy  # pinned bytes
    from tools.policy_compat import runner as R               # pinned bytes
    from tools.policy_compat import scene_cpu                 # pinned bytes

    req = {k: cert["relation"][k] for k in RELATION_KEYS}
    allow = check_deploy(req, cert)
    require(allow["decision"] == "ALLOW",
            "deploy_gate_sanity:not_allow:" + allow["decision"])

    # the load happens ONLY after the ALLOW
    bundle = R.load_bundle()
    pb = cert["relation"]["policy_bundle"]
    require(bundle["manifest"]["manifest_hash"] == pb["manifest_hash"],
            "load_identity_mismatch:manifest_hash")
    require(bundle["manifest_file_sha256"] == pb["manifest_file_sha256"],
            "load_identity_mismatch:manifest_file_sha256")
    require(bundle["manifest"]["policy"]["weights_sha256"]
            == pb["weights_sha256"],
            "load_identity_mismatch:weights_sha256")
    require(bundle["weights_file_sha256"] == pb["weights_file_sha256"],
            "load_identity_mismatch:weights_file_sha256")
    require(bundle["manifest"]["policy"]["architecture"] == pb["architecture"],
            "load_identity_mismatch:architecture")
    require(bundle["manifest"]["policy"]["activation"] == pb["activation"],
            "load_identity_mismatch:activation")
    require(float(bundle["manifest"]["normalization"].get("clip", 8.0))
            == float(pb["normalization_clip"]),
            "load_identity_mismatch:normalization_clip")

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


# ---------------------------------------------------------------- step 7
def execute(bundle, build_id, params):
    from tools.policy_compat import runner as R  # pinned bytes
    res = R.run_closed_loop(bundle, build_id, params, SEED, HORIZON,
                            collect_records=True)
    cert = vi.w04_certificate()
    got = {
        "trajectory_sha256": sha_bytes(res["traj_bytes"]),
        "initial_snapshot_sha256": res["initial_snapshot_sha256"],
        "final_state_sha256": res["final_state_sha256"],
    }
    frozen = {
        "trajectory_sha256": CERT_TRAJECTORY_SHA,
        "initial_snapshot_sha256": CERT_INITIAL_SNAPSHOT_SHA,
        "final_state_sha256": CERT_FINAL_STATE_SHA,
    }
    comparisons = {}
    for key in sorted(frozen):
        ok = got[key] == frozen[key]
        comparisons[key] = {"frozen": frozen[key], "reproduced": got[key],
                            "verdict": "EXACT" if ok else "DRIFT"}
        require(ok, "baseline_drift:" + key)
    sealed_events = cert["replay_evidence"]["events"]
    require(res["events"] == sealed_events,
            "baseline_drift:sealed_event_chain")
    return res, comparisons


# ---------------------------------------------------------------- step 8
def prove_contract_consumption(bundle, res):
    """The runtime consumes the certified observation/action contract:
    recompute every decision from the pinned interface + recipe and require
    bit-exact agreement with the runtime's own applied commands."""
    manifest = bundle["manifest"]
    from tools.policy_compat import scene_cpu as SC  # pinned bytes

    obs_path = (vi.PINNED_ROOT / "tools" / "science_funnel" / "typeb_export"
                / "observation_schema.py")
    obs, obs_sha = load_pinned_module("w07_observation_schema", obs_path)
    schema_identity = {
        "obs_schema_version": obs.OBS_SCHEMA_VERSION,
        "obs_dim": obs.OBS_DIM,
        "legacy_obs_dim": obs.LEGACY_OBS_DIM,
        "declared_field_count": len(obs.FIELDS),
        "declared_field_names_unique": len(set(obs.FIELD_NAMES)) == obs.OBS_DIM,
        "no_privileged_field": all(f["privileged"] is False
                                   for f in obs.FIELDS),
        "no_privileged_source": all(f["source"] not in obs.PRIVILEGED_SOURCES
                                    for f in obs.FIELDS),
        "groups": sorted({f["group"] for f in obs.FIELDS}),
        "module_sha256": obs_sha,
    }
    require(schema_identity["obs_schema_version"] == 2,
            "contract_interface:schema_version")
    require(schema_identity["obs_dim"] == 80,
            "contract_interface:obs_dim_not_80")
    require(schema_identity["legacy_obs_dim"] == 64,
            "contract_interface:legacy_dim_not_64")
    require(schema_identity["declared_field_count"] == 80,
            "contract_interface:field_count")
    require(schema_identity["no_privileged_field"]
            and schema_identity["no_privileged_source"],
            "contract_interface:privileged_field_present")
    # the certificate's declared consumer width: the P3 manifest's frozen
    # normalization arrays (the v1 consumer width of the v2 table)
    mean = np.asarray(manifest["normalization"]["mean"], dtype=np.float32)
    std = np.asarray(manifest["normalization"]["std"], dtype=np.float32)
    require(len(mean) == obs.LEGACY_OBS_DIM and len(std) == obs.LEGACY_OBS_DIM,
            "contract_interface:consumer_width")

    W = [np.ascontiguousarray(bundle["params"][f"W{i}"], dtype=np.float32)
         for i in range(len(manifest["policy"]["architecture"]) - 1)]
    b = [np.ascontiguousarray(bundle["params"][f"b{i}"], dtype=np.float32)
         for i in range(len(manifest["policy"]["architecture"]) - 1)]
    lo = np.asarray(manifest["action"]["bounds_lo"], dtype=np.float32)
    hi = np.asarray(manifest["action"]["bounds_hi"], dtype=np.float32)
    scale = np.asarray(manifest["action"]["scale"], dtype=np.float32)
    center = np.asarray(manifest["action"]["center"], dtype=np.float32)

    records = res["records"]
    applied_rt = res["applied_per_tick"]
    require(len(records) == HORIZON and len(applied_rt) == HORIZON,
            "contract_consumption:record_count")

    decision_ticks = [t for t in range(HORIZON) if t % HOLD_TICKS == 0]
    require(len(decision_ticks) == DECISIONS_EXPECTED,
            "contract_consumption:decision_count")
    require(all(np.array_equal(applied_rt[t], applied_rt[t - 1])
                for t in range(1, HORIZON) if t % HOLD_TICKS != 0),
            "contract_consumption:hold_law_broken")

    mismatches = []
    masked_zero_violations = 0
    mask_stats = {"mean": [], "frac_avail": []}
    sat_recomputed_last = np.zeros(8, dtype=np.float32)
    sat_report_mismatches = 0
    max_abs_applied = 0.0
    sat_counts = 0
    for t in decision_ticks:
        rec = dict(records[t])
        rec["is_decision_tick"] = True
        rec["hold_tick"] = t % HOLD_TICKS
        rec["ticks_since_reset"] = t
        rec["ticks_since_intervention"] = min(10 ** 6, 3000)
        prev_yaw = 0.0 if t == 0 else float(records[t - 1]["yaw_rate"])
        x, mask = obs.project_trace(rec, mean, std, {"yaw_rate": prev_yaw})
        # the declared unavailable-channel law: a masked channel is
        # mean-filled, hence exactly 0.0 in normalized space; never invented
        if not np.all(x[mask == 0.0] == np.float32(0.0)):
            masked_zero_violations += 1
        mask_stats["mean"].append(float(np.mean(mask)))
        mask_stats["frac_avail"].append(float(np.mean(mask > 0)))
        h = x
        for Wi, bi in zip(W, b):
            h = h @ Wi + bi
            h = np.tanh(h, out=h) if h.dtype == np.float32 else np.tanh(h)
            h = h.astype(np.float32, copy=False)
        raw = center + scale * h
        applied = np.clip(raw, lo, hi).astype(np.float32)
        if not np.array_equal(applied, np.asarray(applied_rt[t],
                                                  dtype=np.float32)):
            mismatches.append(t)
        sat = (np.abs(applied - raw) > 0).astype(np.float32)
        sat_recomputed_last = sat
        sat_counts += int(np.sum(sat > 0))
        max_abs_applied = max(max_abs_applied,
                              float(np.max(np.abs(applied))))
        # the record of tick t+1 (the same decision's held state) must carry
        # exactly this limiter saturation (the observation interface reports
        # the limiter faithfully)
        if t + 1 < HORIZON:
            rec_sat = np.asarray(records[t + 1]["limiter_saturation"],
                                 dtype=np.float32)
            if not np.array_equal(rec_sat, sat):
                sat_report_mismatches += 1
    require(not mismatches,
            "contract_consumption:recipe_mismatch@" + str(mismatches[:5]))
    require(masked_zero_violations == 0,
            "contract_consumption:masked_channel_not_mean_filled")
    require(sat_report_mismatches == 0,
            "contract_consumption:limiter_saturation_report_mismatch")

    # the qualification bars, measured on the loaded runtime's own records
    env = SC.derived_envelope()["velocity_envelope_m_s"]
    lo_eps = lo - 1e-6
    hi_eps = hi + 1e-6
    bars = {
        "bounds_honored": all(
            all(l <= c <= h for c, l, h in zip(applied, lo_eps, hi_eps))
            for applied in applied_rt),
        "no_nan_inf": (all(np.isfinite(res["v_series"]))
                       and all(np.all(np.isfinite(np.asarray(r["com_vel"],
                                                              dtype=np.float64)))
                               for r in records)),
        "no_intervention": all(r["intervention_reason"] == "none"
                               for r in records),
        "contact_floor": all(r["contact_count"] >= 2 for r in records),
        "availability_exact": all(
            set(r["available_groups"]) == set(SC.AVAILABLE_GROUPS)
            for r in records),
        "velocity_envelope": all(abs(v) <= env for v in res["v_series"]),
    }
    require(all(bars.values()),
            "qualification_bar_red:" + ",".join(k for k, v in bars.items()
                                                if not v))
    clock = manifest["action"]["clock"]
    require(clock["physics_hz"] == 300 and clock["policy_hz"] == 20
            and clock["hold_ticks"] == 15,
            "contract_clock:manifest_clock")
    require(clock["policy_hz"] * clock["hold_ticks"] == clock["physics_hz"],
            "contract_clock:arithmetic")
    # observations come from the solved state (no substitute telemetry):
    # the PRE-decision record of tick t carries the solved state at the
    # START of tick t (post step t-1; the sealed W06 tick convention)
    solved_v = [0.0] + list(res["v_series"][:HORIZON - 1])
    obs_from_solved = all(
        np.array_equal(np.asarray(r["com_vel"], dtype=np.float32),
                       np.asarray([solved_v[i], 0.0, 0.0],
                                  dtype=np.float32))
        for i, r in enumerate(records))
    require(obs_from_solved, "pose_authority:observation_not_solved_state")
    consumption = {
        "schema_identity": schema_identity,
        "consumer_width": int(len(mean)),
        "decision_ticks": len(decision_ticks),
        "recipe_recomputed_bit_exact_decisions": DECISIONS_EXPECTED
                                                  - len(mismatches),
        "recipe_mismatch_ticks": mismatches,
        "hold_law_held_ticks_verified": HORIZON - DECISIONS_EXPECTED,
        "masked_channels_mean_filled_violations": masked_zero_violations,
        "limiter_saturation_report_mismatches": sat_report_mismatches,
        "limiter_saturation_ticks": sat_counts,
        "max_abs_applied": max_abs_applied,
        "mask_stats": {"mean_min": min(mask_stats["mean"]),
                       "mean_max": max(mask_stats["mean"]),
                       "frac_avail_min": min(mask_stats["frac_avail"]),
                       "frac_avail_max": max(mask_stats["frac_avail"])},
        "bars": bars,
        "velocity_envelope_m_s": env,
        "clock": clock,
        "observations_from_solved_state": obs_from_solved,
    }
    return consumption


# ---------------------------------------------------------------- step 9
def prove_pose_authority(bundle, build_id, params, res):
    from tools.policy_compat import runner as R          # pinned bytes
    from tools.policy_compat import scene_cpu as SC      # pinned bytes

    # (i) structural: the stepping API accepts only bounded commands
    method_names = [n for n, _ in inspect.getmembers(SC.WalkScene,
                                                     inspect.isfunction)]
    require(not any("pose" in n.lower() for n in method_names),
            "pose_authority:pose_named_method_present")
    step_params = list(inspect.signature(SC.WalkScene.step).parameters)
    require(step_params == ["self", "applied", "saturation"],
            "pose_authority:step_signature:" + repr(step_params))
    # the snapshot path is the declared RESTART instrument, not a per-tick
    # pose authority: it is exercised only through restore_snapshot with a
    # COMPLETE inventory (named refusal otherwise) -- verified upstream by
    # CHECK 1's own resume equivalence; named here, not re-proven.

    # (ii) dynamic: an injected pre-recorded action stream is REFUSED
    refusal = None
    try:
        R.requalify(bundle, build_id, params, SEED, HORIZON,
                    precomputed_actions=res["applied_per_tick"])
    except R.PolicyCompatError as exc:
        refusal = str(exc)
    require(refusal is not None and "ACTION_REPLAY_REFUSED" in refusal,
            "pose_authority:action_replay_not_refused")
    return {
        "scene_public_methods": sorted(method_names),
        "step_signature": step_params,
        "pose_write_channel": "none",
        "action_replay_refusal": refusal,
        "snapshot_path_note": ("restore path is the declared restart "
                               "instrument (complete-inventory refusal, "
                               "CHECK 1 resume equivalence upstream); it "
                               "is not a per-tick pose authority"),
    }


# ---------------------------------------------------------------- step 10
def deploy_discrimination(cert, req):
    from tools.policy_compat.certificate import check_deploy  # pinned bytes

    foreign = copy.deepcopy(req)
    foreign["physics_build"] = dict(req["physics_build"])
    foreign["physics_build"]["build_id"] = "cpu-walk-scene-build-N+1"
    block_foreign = check_deploy(foreign, cert)
    block_missing = check_deploy(req, None)

    summary = json.loads((HERE.parent / "MAT2-W06" / "receipts"
                          / "evaluation_summary.json").read_bytes()
                         .decode("utf-8"))
    trained_shas = summary["deploy_treatment"]["trained_theta_npz_sha256"]
    w05_receipt = json.loads((HERE.parent / "MAT2-W05" / "receipts"
                              / "deploy_check_receipt.json").read_bytes()
                             .decode("utf-8"))
    require(w05_receipt["trained_theta_npz_sha256"]
            == {k: trained_shas[k] for k in w05_receipt["trained_theta_npz_sha256"]},
            "deploy_discrimination:trained_sha_source_disagree")
    trained_identity = sha_bytes(canonical({
        "trained_by": "MAT2-W05 walk1m-r1",
        "seeds": summary["seeds"],
        "weights": {k: trained_shas[k] for k in sorted(trained_shas)}}))
    trained_bundle = dict(req["policy_bundle"])
    trained_bundle.update({
        "manifest_hash": trained_identity,
        "weights_sha256": sha_bytes(canonical(
            {k: trained_shas[k] for k in sorted(trained_shas)})),
        "manifest_file_sha256": trained_identity,
        "weights_file_sha256": sha_bytes(canonical(
            {k: trained_shas[k] for k in sorted(trained_shas)})),
        "loader": "MAT2-W05 trained theta npz (float64; per-seed)",
    })
    req_trained = dict(req)
    req_trained["policy_bundle"] = trained_bundle
    block_trained = check_deploy(req_trained, cert)

    require(block_foreign["decision"] == "BLOCK",
            "deploy_discrimination:foreign_not_blocked")
    require(block_missing["decision"] == "BLOCK",
            "deploy_discrimination:missing_not_blocked")
    require(block_trained["decision"] == "BLOCK",
            "deploy_discrimination:trained_not_blocked")
    require(summary["deploy_treatment"]["trained_theta_tuple"] == "BLOCK",
            "deploy_discrimination:sealed_ruling_changed")
    require(summary["deploy_treatment"]["frozen_relation"] == "ALLOW",
            "deploy_discrimination:sealed_frozen_relation_changed")
    return {
        "matching_tuple": {"decision": "ALLOW"},
        "foreign_build": block_foreign,
        "missing_certificate": block_missing,
        "trained_bundle_tuple": block_trained,
        "trained_theta_npz_sha256": trained_shas,
        "sealed_cross_check": {
            "w06_deploy_treatment": {"frozen_relation": "ALLOW",
                                     "trained_theta_tuple": "BLOCK"},
            "w05_deploy_receipt_schema": w05_receipt["schema"]},
    }


# ---------------------------------------------------------------- step 11
def record_named_missing():
    cert = vi.w04_certificate()
    body = cert["relation"]["body_domain"]
    prereqs = list(body["rebind_prerequisites_still_open"])
    require(len(prereqs) == 2, "named_missing:prerequisite_count")

    # N1 re-check, kept able to fail: the pinned machinery's scene-module
    # inventory is exactly the certificate's declared surrogate scene module
    declared = cert["relation"]["physics_build"]["scene_module"]
    pinned_scene_files = sorted(
        p.relative_to(vi.PINNED_ROOT).as_posix()
        for p in (vi.PINNED_ROOT / "tools" / "policy_compat").glob("scene*.py"))
    require(pinned_scene_files == [declared],
            "named_missing:scene_inventory:" + repr(pinned_scene_files))
    in_tree_policy_compat = (HERE.parents[3] / "policy_compat")
    # HERE.parents: [... MAT2-W07, contributions, monkey_campaign, tools]
    in_tree_exists = in_tree_policy_compat.exists()

    # N3: the pinned spike evidence must still carry the two facts by name
    spike_text = " ".join((vi.SPIKE / "INGESTION_SPIKE.md").read_bytes()
                          .decode("utf-8").split())
    w2_text = " ".join((vi.SPIKE / "w2-engine-up" / "ENGINE_UP_RECEIPT.md")
                       .read_bytes().decode("utf-8").split())
    require("NO LIVE PATH" in spike_text,
            "named_missing:spike_no_live_path_absent")
    require("an upload, not a simulation" in w2_text,
            "named_missing:w2_upload_not_simulation_absent")

    # N4: the C09 anchor receipt, verified and carried (never re-issued)
    c09 = vi.c09_anchor_reseal()
    verdicts = {k: v["verdict"] for k, v in
                c09["anchor_comparisons"].items()}
    require(len(verdicts) == 9 and all(v == "EXACT" for v in verdicts.values()),
            "named_missing:c09_anchor_not_exact")

    return {
        "N1_adopted_assembly_scene_module": {
            "outcome": "NAMED_MISSING",
            "certificate_declaration": prereqs[0],
            "recheck": {
                "pinned_machinery_scene_modules": pinned_scene_files,
                "certificate_declared_scene_module": declared,
                "in_tree_tools_policy_compat_exists": in_tree_exists,
            },
            "action": ("NOT attempted; no load executed or fabricated on "
                       "the adopted assembly; the certified execution "
                       "vehicle stays the declared surrogate scene"),
        },
        "N2_tc3_drive_table": {
            "outcome": "NAMED_MISSING",
            "certificate_declaration": prereqs[1],
            "action": ("the adopted assembly's drive table is NOT "
                       "re-declared; the certified scene's caps are used "
                       "ONLY inside the declared surrogate scene and are "
                       "never presented as the assembly's"),
        },
        "N3_product_engine_live_control_path": {
            "outcome": "NAMED_MISSING",
            "evidence_pins": [r["path"] for r in vi.verify(
                [p for p in vi.PINS if p[0] == "spike"])],
            "facts": [
                "INGESTION_SPIKE.md: the W03/W04 walk physics has NO LIVE "
                "PATH in the native windowed engine (/gait_bin is a "
                "different CPG gait)",
                "ENGINE_UP_RECEIPT.md: a /skin_bin load is an upload, not "
                "a simulation (B=1 rest identity pose)",
            ],
            "action": ("the windowed-engine visual walk claim stays "
                       "absent; no engine process is started by this card"),
        },
        "N4_c09_anchors": {
            "outcome": "CARRIED_EXACT; adopted-assembly re-run "
                       "STRUCTURALLY MISSING (never re-issued here)",
            "anchor_verdicts": verdicts,
            "receipt_status_line": c09["adopted_assembly_anchor_status"],
        },
    }


# ---------------------------------------------------------------- main
def main() -> int:
    pins, reg = stage_pins()
    cert = vi.w04_certificate()
    validator = validate_certificate(cert)
    req, allow, bundle, build_id, params = gate_and_load(cert)
    res, anchors = execute(bundle, build_id, params)
    consumption = prove_contract_consumption(bundle, res)
    pose = prove_pose_authority(bundle, build_id, params, res)
    deploy = deploy_discrimination(cert, req)
    named = record_named_missing()

    receipt = {
        "schema": "chimera.w07_native_load.v1",
        "task_id": vi.TASK_SHORT,
        "card_id": vi.CARD_ID,
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "candidate_base": vi.CANDIDATE_BASE,
        "registry": reg,
        "statement": (
            "the ACCEPTED walking policy (the frozen certified line) was "
            "LOADED through the W04 compatibility certificate's deploy gate "
            "(ALLOW) into the certified native runtime (the sealed "
            "policy_compat machinery, declared CPU walk scene, build N) and "
            "EXECUTED consuming the certified observation/action contract "
            "bit-for-bit; the trained bundles BLOCK at the same gate; the "
            "gated adopted-assembly parts are recorded NAMED_MISSING, no "
            "load fabricated"),
        "certificate": {
            "path": str((vi.STORE / "MAT2-W04" / "numerical"
                         / "w04_certificate.json")).replace("\\", "/"),
            "sha256": pins[0]["sha256"],
            "cert_hash": cert["cert_hash"],
            "compat_key": cert["compat_key"],
            "validator": validator,
        },
        "load": {
            "order": "validate -> deploy gate ALLOW -> frozen loader -> "
                     "identity checks",
            "deploy_decision": allow["decision"],
            "deploy_reasons": allow["reasons"],
            "policy_bundle_identity": {
                "manifest_hash": cert["relation"]["policy_bundle"]["manifest_hash"],
                "weights_sha256": cert["relation"]["policy_bundle"]["weights_sha256"],
                "manifest_file_sha256": bundle["manifest_file_sha256"],
                "weights_file_sha256": bundle["weights_file_sha256"],
                "architecture": bundle["manifest"]["policy"]["architecture"],
                "activation": bundle["manifest"]["policy"]["activation"],
                "normalization_clip": bundle["manifest"]["normalization"].get("clip", 8.0),
                "loader": "typeb_export.policy_manifest.load_manifest (frozen)",
            },
            "physics_build": {
                "build_id": build_id,
                "params_sha256": params_sha(params),
                "scene_module": cert["relation"]["physics_build"]["scene_module"],
                "scene_module_sha256": cert["relation"]["physics_build"]["scene_module_sha256"],
                "timestep_s": params["dt"],
            },
            "trained_bundles_loaded": 0,
        },
        "execution": {
            "seed": SEED,
            "horizon_ticks": HORIZON,
            "anchor_comparisons": anchors,
            "sealed_event_chain_identical": True,
            "events_count": len(res["events"]),
        },
        "contract_consumption": consumption,
        "pose_authority": pose,
        "deploy_discrimination": deploy,
        "named_missing": named,
        "claim_class": cert["qualification_scope"]["bars"]["claim_class"],
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_native_load.py"},
    }
    outdir = HERE / "receipts"
    outdir.mkdir(parents=True, exist_ok=True)
    data = canonical(receipt) + b"\n"
    (outdir / "native_load_receipt.json").write_bytes(data)
    print("LOAD:", allow["decision"], "| anchors:",
          {k: v["verdict"] for k, v in anchors.items()})
    print("contract: %d/%d decisions bit-exact, %d hold ticks verified"
          % (consumption["recipe_recomputed_bit_exact_decisions"],
             consumption["decision_ticks"],
             consumption["hold_law_held_ticks_verified"]))
    print("deploy:", deploy["matching_tuple"]["decision"],
          deploy["foreign_build"]["decision"],
          deploy["missing_certificate"]["decision"],
          deploy["trained_bundle_tuple"]["decision"])
    print("named_missing:", {k: v["outcome"] for k, v in named.items()})
    print("wrote", outdir / "native_load_receipt.json")
    return 0


def params_sha(params: dict) -> str:
    import json as _json
    return hashlib.sha256(_json.dumps(
        params, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except vi.Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
