"""Finalize the cert-dryrun lane: F4 payload comparison + evidence copy.

Run after 3 pipeline passes: verifies the three canonical payloads are
byte-identical (F4), copies the lane's evidence artifacts into the lane dir
(large regenerable stderr traces excluded by size, shas recorded), and prints
the per-falsifier summary for the receipt append.
"""
import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, REPO := os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from tools.policy_compat import engine_cert as ec  # noqa: E402
from tools.policy_compat import snapshot_api  # noqa: E402

LANE_RUNS = os.path.join(ec.LANE, "runs")


def main() -> None:
    # ---- F4: the 3 canonical payloads must be byte-identical
    shas = {}
    for i in (1, 2, 3):
        p = os.path.join(ec.TMP, f"payload_run{i}.json")
        shas[i] = ec.sha256_hex(ec.rd(p))
    distinct = len(set(shas.values()))
    print("F4 payload shas:", {k: v[:16] for k, v in shas.items()}, "distinct:", distinct)
    if distinct != 1:
        raise SystemExit("F4 FIRED: the 3 pipeline payloads differ")

    payload = json.loads(ec.rd(os.path.join(ec.TMP, "payload_run1.json")).decode("utf-8"))
    run1 = os.path.join(ec.TMP, "runs", "run1")

    # ---- copy the evidence artifacts into the lane (regenerable giants excluded)
    keep = [
        "certificate.json", "tamper_report.json",
        "check1_report.json", "check2_report.json",
        "check3_engine_report.json", "check3_actor_report.json",
        # the walk of record (states/actions are the certificate's own evidence currency)
        "refA1.states.bin", "refA1.actions.bin", "refA1.snap_t150.bin",
        "refA1.manifest.json", "refA1.run.json", "refA1.stdout",
        # the fresh-process restore (the bit-identity continuation)
        "res.states.bin" if os.path.exists(os.path.join(run1, "res.states.bin")) else "resA.states.bin",
        "res.actions.bin" if os.path.exists(os.path.join(run1, "res.actions.bin")) else "resA.actions.bin",
        "res.run.json" if os.path.exists(os.path.join(run1, "res.run.json")) else "resA.run.json",
        # the forced-drop probes (verdict rows only; states are big)
        "drop_world_state.run.json", "drop_contact_warm_start.run.json",
        "drop_reflex_state.run.json", "drop_controller_history.run.json",
        # the engine action-replay refusal probe (the refusal message itself)
        "replay_probe_A_relative_actions_path.stderr",
        # RC-2 cross-build stdout (the F-G42 census rides it; stderr sha-only)
        "rc2A.stdout",
    ]
    copied = []
    for name in keep:
        src = os.path.join(run1, name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(LANE_RUNS, name))
            copied.append(name)
    print("copied:", len(copied), "artifacts")

    # ---- the excluded regenerable giants, recorded by sha
    excluded = {}
    for name in ("refA1.stderr", "refA2.stderr", "refB1.stderr",
                 "rc2A.stderr", "rc2B.stderr",
                 "replay_probe_A_relative_actions_path.stdout",
                 "replay_probe_B_nonexistent_absolute_path.stdout",
                 "replay_probe_B_nonexistent_absolute_path.stderr"):
        p = os.path.join(run1, name)
        if os.path.exists(p):
            excluded[name] = ec.sha256_hex(ec.rd(p))
    with open(os.path.join(LANE_RUNS, "excluded_stderr_shas.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(excluded, f, indent=2, sort_keys=True)
        f.write("\n")

    # ---- per-falsifier summary for the receipt
    cert = payload["certificate"]
    summary = {
        "compat_key": cert["compat_key"],
        "cert_hash": cert["cert_hash"],
        "deployment_class": cert["restart_state_inventory"]["deployment_class"],
        "build_id": cert["relation"]["physics_build"]["build_id"],
        "binary_stamp_bound": cert["relation"]["physics_build"]["binary_stamp_bound_to_evidence"],
        "scene_pin": cert["relation"]["physics_build"]["scene_pin_sha256"],
        "checkpoint_snapshot_sha256": cert["relation"]["physics_build"]["checkpoint_snapshot"]["file_sha256"],
        "f4_payload_sha256": shas[1],
        "check1": {k: payload["check1"][k] for k in
                   ("pass", "replay_byte_identical", "restore_bit_identity", "walk_face",
                    "ship_fence_legs", "forced_drops", "dump_nan_free", "checkpoint")},
        "check2": {k: payload["check2"][k] for k in
                   ("pass", "build_A_binary_sha256", "build_B_binary_sha256",
                    "binary_stamps_differ", "registered_cases")},
        "check3_engine": payload["check3_engine"],
        "check3_actor_pass": payload["check3_actor"]["pass"],
        "tamper_suite": payload["tamper_suite"],
        "deploy": {"allow": payload["deploy_allow"]["decision"],
                   "foreign": payload["deploy_block_foreign_build"]["decision"],
                   "missing": payload["deploy_block_missing_certificate"]["decision"]},
        "registry": {"verify": snapshot_api.verify_lane_proofs()[0],
                     "completeness": snapshot_api.check_registry_completeness()[0]},
    }
    with open(os.path.join(LANE_RUNS, "summary.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: summary[k] for k in
                      ("compat_key", "deployment_class", "build_id", "f4_payload_sha256")}, indent=1))
    print("FINALIZE DONE")


if __name__ == "__main__":
    main()
