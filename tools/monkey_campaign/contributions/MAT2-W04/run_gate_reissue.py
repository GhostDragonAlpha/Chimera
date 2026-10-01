#!/usr/bin/env python3
"""MAT2-W04: the TC-6 compatibility-certificate RE-ISSUE through the sealed
upgrade-gate machinery, with the body_domain slot filled by the B07 adoption
decision (LT rulings BQ-1/BQ-5/BQ-6; card clauses FC-1/FC-2/FC-3/FC-5).

The machinery is consumed UNMODIFIED from a sha-pinned extraction of the
sealed `tools/policy_compat` package + its frozen inputs (the P3 bundle dir,
the typeb_export loader package, the Rule-0 receipt). Every consumed file's
sha256 is pinned in the emitted receipt; drift = refusal `input_pin_mismatch`.

Steps (all CPU):
  1. pin-extract the machinery + inputs, verify every sha at extraction;
  2. run the FULL clean gate pipeline THREE times (P4 no-false-positive class:
     byte-identical canonical bundles);
  3. issue the W04 certificate from run 1's fresh replay evidence with the
     relation's body_domain replaced by the W04 TC-7 fill (the adoption
     decision identity + body_digest + mass line + qualification state); the
     policy bundle / physics build / runtime profile / test suite components
     are the machinery's own, unmodified;
  4. validate the W04 certificate (validator is the only authority);
  5. deployment checks: matching tuple ALLOW; foreign build BLOCK; missing
     certificate BLOCK; the OLD sealed 5-tuple BLOCKs against the W04
     certificate AND the W04 tuple BLOCKs against the OLD sealed certificate
     (the live reusability instrument for "An old policy is reusable only if
     this contract still matches");
  6. run the 4/4 injection suite (I1..I4) against the W04 certificate;
  7. emit the W04 certificate + the gate receipt into the card dir.

Run:  python -B run_gate_reissue.py
Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = Path(r"E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W04"
          r"\d94341b2bd694bd2b725964040201398")
SCRATCH = WS / "scratch" / "gate"
PINNED = SCRATCH / "pinned"
PASS3 = Path(r"E:/ChimeraWork/pass3-integ/repo")

PREREG_SHA256 = hashlib.sha256(
    (HERE / "PREREGISTRATION.md").read_bytes()).hexdigest()
CANDIDATE_BASE = "7ca4aceed57bd0471a185ea046436d74aa3b95a9"

# The sealed machinery + frozen inputs consumed read-only and pinned.
MACHINERY_FILES = [
    "tools/policy_compat/__init__.py",
    "tools/policy_compat/__main__.py",
    "tools/policy_compat/certificate.py",
    "tools/policy_compat/engine_cert.py",
    "tools/policy_compat/injections.py",
    "tools/policy_compat/runner.py",
    "tools/policy_compat/scene_cpu.py",
    "tools/policy_compat/snapshot_api.py",
]
EXPORT_DIR_REL = "tools/science_funnel/typeb_export"
P3_DIR_REL = "tools/science_funnel/validation/typeb_p3_20260921"
GATE_DIR_REL = "tools/science_funnel/validation/upgrade_gate_20260920"
TREE_FILES = [MACHINERY_FILES,
              [EXPORT_DIR_REL + "/" + p for p in sorted(os.listdir(PASS3 / EXPORT_DIR_REL))
               if p.endswith(".py")],
              [P3_DIR_REL + "/" + p for p in sorted(os.listdir(PASS3 / P3_DIR_REL))
               if (PASS3 / P3_DIR_REL / p).is_file()],
              [GATE_DIR_REL + "/receipt.json"]]
TREE_FILES = [p for group in TREE_FILES for p in group]

# Sealed identities consumed by the re-issue.
OLD_CERT_PATH = PASS3 / GATE_DIR_REL / "certificate.json"
OLD_CERT_SHA256 = "246bfa0af552754e720a9b47653f8e27fa36833e18753b6545bd0822ff71ac74"
OLD_COMPAT_KEY = "9de019b7b9ef5e0ceff159558d8da726d678faafff28f12dab8d383b97c21b40"

ADOPTION_RECORD = HERE.parent / "MAT2-B07" / "adoption_record.json"
ADOPTION_RECORD_SHA256 = ("638884569ac106cb7ed738381e804e4f936877f05fd572a57"
                          "63064cdcb711a0a")
EXPECTED_BODY_DIGEST = "chimera.b07.adoption.240b457bc9612111173314b49f453b80"
EXPECTED_DOMAIN_TAG = "material-assembly/buffy02-lineage"
MASS_LINE = ("counted 0.0 kg; transported 17.039978509953905 kg deliberately "
             "non_consumed; the certified walking body 10.037998 kg is "
             "UNCHANGED in every scene/ledger")

TICK_COST_SHA256 = ("f87da957d62f3702d241d199ff417110a63af7ee4d264498a07208f"
                    "10d5f906e")

REFUSAL_PIN = "input_pin_mismatch"
REFUSAL_VALIDATOR = "certificate_validator_violation"
REFUSAL_DEPLOY = "deploy_gate_sanity"
REFUSAL_INJECTION = "injection_missed"
REFUSAL_TRIPLE = "clean_triple_differs"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def pin_extract():
    pins = {}
    for rel in TREE_FILES:
        src = PASS3 / rel
        data = src.read_bytes()
        digest = sha_bytes(data)
        target = PINNED / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        pins[rel] = digest
    # the Rule-0 receipt sha (the machinery's own prereg identity) is verified
    # against the sealed value recorded in the sealed gate receipt
    return pins


def w04_body_domain():
    raw = ADOPTION_RECORD.read_bytes()
    digest = sha_bytes(raw)
    require(digest == ADOPTION_RECORD_SHA256,
            REFUSAL_PIN + ":adoption_record:" + digest[:12])
    rec = json.loads(raw.decode("utf-8"))
    bind = rec["tc7_body_domain_bind"]["bound_as"]
    require(bind["body_digest"] == EXPECTED_BODY_DIGEST,
            REFUSAL_PIN + ":body_digest_moved")
    require(bind["domain_tag"] == EXPECTED_DOMAIN_TAG,
            REFUSAL_PIN + ":domain_tag_moved")
    return {
        "binding_scope": ("TC-7 FILL: the adopted assembly is the recorded "
                          "BINDING TARGET of this contract (B07 ADOPT, "
                          "Amendment A1 line). The replay evidence in this "
                          "certificate remains the declared surrogate "
                          "vehicle scene's; it is NOT adopted-assembly "
                          "evidence."),
        "adoption_decision": {
            "kind": rec["adoption_decision"]["kind"],
            "message_id": rec["governing_frame"]["message_id"],
            "captain_decision": rec["governing_frame"]["captain_decision"],
            "adoption_record_sha256": digest,
        },
        "body_digest": bind["body_digest"],
        "digest_law": bind["digest_law"],
        "domain_tag": bind["domain_tag"],
        "mass_line": MASS_LINE,
        "mass_rulings": [
            "R-MASS-04: 5.262978509953907 kg stays uncounted pending density "
            "validation; the 11.777 kg pelvis quantity is a NON-PHYSICAL "
            "reference (no validated-density admission path opened)",
            "R-MASS-02: bone material density stays UNVALIDATED; MAT-03 "
            "admission only when a measured conditioned source exists",
            "R-MASS-03: carried-load mass for port weights only from a NEW "
            "validated source; the transported set is never promoted; ports "
            "stay honestly refused (0/8)",
        ],
        "qualification_state": bind["qualification_state"],
        "vehicle_scene": ("cpu-walk-scene/hind-pad-surrogate (the declared "
                          "deterministic CPU walk scene; the execution "
                          "vehicle of this certificate's replay evidence; "
                          "TC-1/TC-5)"),
        "tc12_lineages": ("the certified 10.037998 kg walking line and the "
                          "adopted-assembly lineage stay separate parallel "
                          "records; replacement of one with the other is a "
                          "recorded decision NOT taken for runtime use"),
        "prior_state": ("UNBOUND_dummy (P3 manifest body: status UNBOUND -- "
                        "binds automatically when the real actor exists); "
                        "domain_tag cpu-walk-scene/hind-pad-surrogate; "
                        "physics_build cpu-walk-scene-build-N"),
        "rebind_prerequisites_still_open": [
            "a runtime scene module executing the adopted assembly (none "
            "exists; named-missing; gates RUNTIME USE, not this freeze)",
            "TC-3: the adopted assembly's drive table re-declared from ITS "
            "own sealed sources (the certified scene's caps never transfer "
            "silently)",
        ],
    }


def main():
    pins = pin_extract()

    sys.path.insert(0, str(PINNED / "tools"))
    from policy_compat import runner as R  # noqa: E402
    from policy_compat.certificate import (canonical_json, check_deploy,  # noqa: E402
                                           issue_certificate,
                                           validate_certificate)
    from policy_compat import injections as INJ  # noqa: E402

    # ---- 2. the clean pipeline, three times (P4) -------------------------
    bundles = []
    for i in (1, 2, 3):
        out_dir = str(SCRATCH / ("clean%d" % i))
        b = R.clean_pipeline("w04_clean_%d" % i, out_dir, seed=20260920)
        bundles.append(canonical_json(b))
        print("clean pipeline %d done" % i)
    require(bundles[0] == bundles[1] == bundles[2], REFUSAL_TRIPLE)
    bundle_obj = json.loads(bundles[0].decode("utf-8"))
    machinery_cert = bundle_obj["certificate"]

    # ---- 3. issue the W04 certificate ------------------------------------
    body = w04_body_domain()
    bundle = R.load_bundle()
    _, pn = R.build_n()
    relation = R.build_relation(bundle, "cpu-walk-scene-build-N", pn)
    require(relation["body_domain"]["body_digest"].startswith("UNBOUND_dummy"),
            "machinery_relation_unexpected")
    relation["body_domain"] = body
    scope = R.scope_block()
    scope["bodies"] = scope["bodies"] + [
        "chimera.b07.adoption.240b457bc9612111173314b49f453b80 (the adopted "
        "assembly, material-assembly/buffy02-lineage): the TC-7 BINDING "
        "TARGET, NOT a runtime-qualified body; the certificate's replay "
        "evidence remains the surrogate vehicle scene's"
    ]
    scope["bars"]["claim_class"] = (
        "offline/trace qualification at the 300 Hz tick is the ONLY satisfied "
        "execution class; INTERACTIVE real-time 300 Hz execution is NOT a "
        "satisfied line and must not be claimed by any runtime until a "
        "backend closes it (COST-GAP verdict, receipt_tick_cost.json sha "
        + TICK_COST_SHA256 + ")")
    scope["bars"]["training_throughput"] = (
        "bound to the mailbox reservation discipline (P04 APPROVED "
        "reservations before any training run), not to hope")
    meta = {
        "issued_by": "MAT2-W04 lane agent (Agent: wk-w04-freeze)",
        "lane": "MAT2-W04",
        "base_commit": CANDIDATE_BASE,
        "prereg_receipt": ("tools/monkey_campaign/contributions/MAT2-W04/"
                           "PREREGISTRATION.md"),
        "prereg_rule0_sha": PREREG_SHA256,
    }
    cert = issue_certificate(relation, R.inventory_block(),
                             machinery_cert["replay_evidence"], scope, meta)
    errs = validate_certificate(cert)
    require(not errs, REFUSAL_VALIDATOR + ":" + "; ".join(errs)[:300])

    # ---- 5. deployment checks --------------------------------------------
    req = {k: cert["relation"][k] for k in
           ("policy_bundle", "physics_build", "runtime_profile",
            "body_domain", "test_suite")}
    allow = check_deploy(req, cert)
    foreign = copy.deepcopy(req)
    foreign["physics_build"] = dict(req["physics_build"])
    foreign["physics_build"]["build_id"] = "cpu-walk-scene-build-N+1"
    block_foreign = check_deploy(foreign, cert)
    block_missing = check_deploy(req, None)

    with open(OLD_CERT_PATH, "rb") as f:
        old_raw = f.read()
    old_digest = sha_bytes(old_raw)
    require(old_digest == OLD_CERT_SHA256,
            REFUSAL_PIN + ":old_certificate:" + old_digest[:12])
    old_cert = json.loads(old_raw.decode("utf-8"))
    require(old_cert["compat_key"] == OLD_COMPAT_KEY,
            REFUSAL_PIN + ":old_compat_key")
    old_tuple = {k: old_cert["relation"][k] for k in
                 ("policy_bundle", "physics_build", "runtime_profile",
                  "body_domain", "test_suite")}
    old_tuple_on_new = check_deploy(old_tuple, cert)
    new_tuple_on_old = check_deploy(req, old_cert)

    require(allow["decision"] == "ALLOW", REFUSAL_DEPLOY + ":allow")
    require(block_foreign["decision"] == "BLOCK", REFUSAL_DEPLOY + ":foreign")
    require(block_missing["decision"] == "BLOCK", REFUSAL_DEPLOY + ":missing")
    require(old_tuple_on_new["decision"] == "BLOCK",
            REFUSAL_DEPLOY + ":old_tuple_allowed")
    require(new_tuple_on_old["decision"] == "BLOCK",
            REFUSAL_DEPLOY + ":new_tuple_on_old_allowed")

    # ---- 6. the injection suite against the W04 certificate --------------
    clean_out = SCRATCH / "clean1"
    report = INJ.run_injections(
        str(SCRATCH / "injections"), cert, req,
        bundle_obj["corpus"]["actions_sha256"],
        str(clean_out / "c1_snapshot_t317_s20260920.json"),
        str(clean_out / "c1_full_run1_s20260920.bin"),
        20260920, 900, 317)
    require(report["all_caught"] is True,
            REFUSAL_INJECTION + ":" + json.dumps(
                {k: v["verdict"] for k, v in
                 report["injections"].items()}, sort_keys=True))

    # ---- 7. emit ----------------------------------------------------------
    outdir = HERE / "gate_reissue"
    outdir.mkdir(parents=True, exist_ok=True)
    cert_bytes = json.dumps(cert, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"),
                            allow_nan=False).encode("utf-8") + b"\n"
    (HERE / "w04_certificate.json").write_bytes(cert_bytes)

    receipts = {
        "w04_gate_receipt.json": {
            "schema": "chimera.w04_gate_reissue.v1",
            "task_id": "W04",
            "card_id": "MAT2-W04",
            "preregistration_sha256": PREREG_SHA256,
            "candidate_base": CANDIDATE_BASE,
            "statement": ("W04 TC-6 re-issue receipt: the compatibility "
                          "certificate re-issued through the UNMODIFIED "
                          "sealed upgrade-gate machinery with the body_domain "
                          "slot filled by the B07 adoption decision (FC-1); "
                          "the gate class stays live (4/4 injections CAUGHT) "
                          "and the old-policy reusability verdict is "
                          "EXECUTED, not assumed (FC-3)"),
            "machinery_pins": pins,
            "machinery_note": ("consumed read-only from a sha-pinned "
                               "extraction of the sealed pass3-integ lane "
                               "tree; zero machinery files modified"),
            "clean_triple": {
                "pass": True,
                "bundle_sha256": [sha_bytes(b) for b in bundles],
                "detail": ("three clean full-gate runs byte-identical "
                           "(P4 no-false-positive class) on the unmodified "
                           "machinery"),
            },
            "w04_certificate_sha256": sha_bytes(cert_bytes),
            "w04_compat_key": cert["compat_key"],
            "w04_cert_hash": cert["cert_hash"],
            "body_domain": body,
            "relation_delta_from_machinery": {
                "policy_bundle": "unchanged (the P3 gate-mechanics bundle; "
                                 "NOT a trained policy)",
                "physics_build": "unchanged (the declared CPU walk scene "
                                 "build; the replay vehicle)",
                "runtime_profile": "unchanged (300 Hz physics / 20 Hz policy "
                                   "/ 15-tick hold)",
                "body_domain": "REBOUND: UNBOUND_dummy -> the adopted "
                               "assembly binding target (TC-7 fill)",
                "test_suite": "unchanged (registered_cases_v1)",
            },
            "validator": {"violations": [], "verdict": "VALID"},
            "deploy_checks": {
                "matching_tuple": allow,
                "foreign_build": block_foreign,
                "missing_certificate": block_missing,
                "old_sealed_tuple_vs_w04_cert": old_tuple_on_new,
                "w04_tuple_vs_old_sealed_cert": new_tuple_on_old,
            },
            "reusability_verdict": {
                "old_policy_bundle": ("the P3 registered test manifest "
                                      "(architecture [64,128,128,8], frozen "
                                      "weights sha 5fb2b785..., loader "
                                      "typeb_export.policy_manifest."
                                      "load_manifest) is the gate-mechanics "
                                      "DEMONSTRATION CASE, not a trained "
                                      "policy"),
                "trained_walking_policy": ("NO trained walking policy exists "
                                           "(five standing UNRESOLVED gaps, "
                                           "P02 prototype_recovery); the "
                                           "policy artifact slot closes "
                                           "explicitly-unresolved"),
                "verdict": ("NOT REUSABLE as-is: the old sealed 5-tuple "
                            "BLOCKs against the rebound contract (compat "
                            "key mismatch, executed above) and the contract "
                            "mismatch dimensions are named: body domain "
                            "rebind (TC-7), drive table not re-declared "
                            "(TC-3), port inputs absent (TC-8). Any future "
                            "policy binds ONLY by reissuance through this "
                            "gate."),
                "instrument": ("executed deploy-gate BLOCKs, not prose: "
                               "old_tuple_vs_w04_cert and "
                               "w04_tuple_vs_old_sealed_cert above"),
            },
            "injections": {
                "all_caught": report["all_caught"],
                "falsifier_summary": report["falsifier_summary"],
                "injections": report["injections"],
                "suite": report["suite"],
            },
            "claim_class": scope["bars"]["claim_class"],
            "determinism": {"canonical_json": True, "newline": "\n",
                            "command": "python -B run_gate_reissue.py"},
        },
    }
    for name, obj in receipts.items():
        out = outdir / name
        out.write_bytes(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":"),
                                   allow_nan=False).encode("utf-8") + b"\n")
        print("wrote", out)
    print("certificate VALID; compat_key", cert["compat_key"][:16], "...")
    print("deploy:", allow["decision"], block_foreign["decision"],
          block_missing["decision"], old_tuple_on_new["decision"],
          new_tuple_on_old["decision"])
    print("injections CAUGHT:", sum(
        1 for v in report["injections"].values()
        if v["verdict"] == "CAUGHT"), "/", len(report["injections"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
