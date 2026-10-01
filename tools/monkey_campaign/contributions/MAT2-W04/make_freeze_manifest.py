#!/usr/bin/env python3
"""MAT2-W04: generate the frozen training manifest (the done_when binding).

w04_freeze_manifest.json binds, by file path + sha256 (no prose references):
  dynamics identity      TC-1/TC-5 (300 Hz tick, C09 re-sealed anchor class)
  body domain            FC-1  (the B07 adoption decision, digest, mass line)
  port/law inputs        FC-2  (the anchored honest refusal; BQ-5)
  policy artifact        FC-3  (explicitly-unresolved + reusability verdict)
  seeds/runbook slot     FC-4  (slot shape + K01/P04 law depth; BQ-3)
  runtime profile        FC-5  (offline/trace claim class; BQ-2)
  observation/action     TC-2  (schema version + table hashes)
  actuation              TC-3  (re-declare PENDING; caps never transfer)
  model revision, test suite slot, explicitly-unresolved inventory.

The module also exports the six FB detectors used by the named-check suite
(clean pass) and the falsifier bite arms (tampered copies must bite). Every
detector raises Refusal(<code>) — it can FAIL, and it refuses vacuous passes.

Run:  python -B make_freeze_manifest.py
Exit: 0 green / 2 named refusal. CPU only.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[3]
CONTRIB = HERE.parent
WS = Path(r"E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W04"
          r"\d94341b2bd694bd2b725964040201398")
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
PASS3 = Path(r"E:/ChimeraWork/pass3-integ/repo")
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

TASK_ID = "W04"
CARD_ID = "MAT2-W04"
CRITERIA_SHA256 = ("cb66e8e9c24b6a838cb4e7b3dededef3c7c05fa72a77c9973a6ddb8b"
                   "7ff16e03")
CANDIDATE_BASE = "7ca4aceed57bd0471a185ea046436d74aa3b95a9"

OBS_V2_PATH = (PASS3 / "tools/science_funnel/validation"
               / "policy_interface_freeze_20260920"
               / "observation_interface_v2.json")
OBS_V2_SHA = ("e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0"
              "671c")
OBS_SECTION_PATH = (PASS3 / "tools/science_funnel/validation"
                    / "obs_split_channels_20260921" / "obs_section_v2.json")
OBS_SECTION_SHA = ("3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3e"
                   "a1af63079")
TICK_COST_PATH = (PASS3 / "tools/science_funnel/validation"
                  / "tick_cost_attribution_20260920" / "receipt_tick_cost.json")
TICK_COST_SHA = ("f87da957d62f3702d241d199ff417110a63af7ee4d264498a07208f10"
                 "d5f906e")
PORT_QUAL_PATH = STORE / "MAT2-B07/numerical/PORT_QUALIFICATION.md"
PORT_QUAL_SHA = ("4818d4b03576f2821f75f49b2d54f8c01378763b1ad1441075dda267c"
                 "9ff3f00")
MEASURED_SOURCES_PATH = STORE / "MAT2-B07/numerical/MEASURED_SOURCES.md"
MEASURED_SOURCES_SHA = ("c181a0b5cdf01cb377abe32e0c18abec278ebd52b43c8d0a5d"
                        "0a4c631efb7574")
ADDITION_PATH = CONTRIB / "MAT2-B07" / "adoption_record.json"
ADDITION_SHA = ("638884569ac106cb7ed738381e804e4f936877f05fd572a5763064cdc"
                "b711a0a")
BODY_DIGEST = "chimera.b07.adoption.240b457bc9612111173314b49f453b80"
DOMAIN_TAG = "material-assembly/buffy02-lineage"

REFUSAL = "freeze_manifest_refused"


class Refusal(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(condition, code):
    if not condition:
        raise Refusal(code)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_registry():
    require(REGISTRY.exists(), REFUSAL + ":registry_missing")
    uri = "file:" + str(REGISTRY).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        row = con.execute("SELECT payload FROM state WHERE id='1'").fetchone()
    finally:
        con.close()
    require(row is not None, REFUSAL + ":registry_empty")
    state = json.loads(row[0])
    card = state["kanban"]["cards"][CARD_ID]
    require(card.get("criteria_sha256") == CRITERIA_SHA256,
            REFUSAL + ":criteria_pin_mismatch")
    profile = card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]
    require(profile["id"] == "anatomy" and profile["kind"] == "visible_static",
            REFUSAL + ":profile_identity")
    return card, profile


def require_pin(path, expected, code):
    got = sha_file(path)
    require(got == expected, "input_pin_mismatch:" + code + ":" + got[:12])
    return got


# ------------------------------------------------------------------ detectors
# Each detector can FAIL (raises Refusal with a named code). The named-check
# suite runs every detector on the CLEAN manifest (must pass); each falsifier
# bite arm runs it on a tampered copy (must bite).

def detect_body_domain(m):
    bd = m["body_domain"]
    bound = bd["bound_value"]
    require(bound["body_digest"] == BODY_DIGEST,
            "w04_manifest_body_domain_unbound")
    require(bound["domain_tag"] == DOMAIN_TAG,
            "w04_manifest_body_domain_unbound")
    require("UNBOUND_dummy" not in json.dumps(bound),
            "w04_manifest_body_domain_unbound")
    require(len(bd["mass_rulings"]) == 3 and
            all(r.startswith("R-MASS-") for r in
                [x["ruling"] for x in bd["mass_rulings"]]),
            "w04_mass_line_missing")
    certified = [r for r in bd["mass_rulings"]
                 if "10.037998" in r["text"]]
    require(certified, "w04_certified_line_invalidated")


def detect_ports(m):
    ports = m["port_active_law_inputs"]
    require(ports["status"] == "UNQUALIFIED_BY_HONEST_REFUSAL",
            "w04_port_qualified_without_admission")
    require(ports["ports_qualified"] == 0 and ports["ports_total"] == 8,
            "w04_port_qualified_without_admission")
    require(ports["measured_inputs_admitted"] == [],
            "w04_port_qualified_without_admission")
    # no invented constants: the refusal section carries NO numeric input
    # values besides the two counts already required above
    banned = ("kappa", "stiffness", "friction", "weight_value", "patch_area")
    for key in ports:
        if any(b in key.lower() for b in banned):
            raise Refusal("w04_port_invented_constant:" + key)
    require(len(ports["refusals"]) >= 3, "w04_refusal_record_missing")


def detect_policy_slot(m):
    pol = m["policy_artifact"]
    require(pol["status"] == "EXPLICITLY_UNRESOLVED",
            "w04_policy_trained_claim")
    require(pol["trained_walking_policy_exists"] is False,
            "w04_policy_trained_claim")
    require("NOT a trained policy" in pol["p3_bundle_role"],
            "w04_policy_trained_claim")
    verdict = pol["reusability_verdict"]
    require(verdict["verdict"].startswith("NOT REUSABLE"),
            "w04_reusability_verdict_missing")
    require(set(verdict["mismatch_dimensions"]) ==
            {"TC-7 body domain rebind", "TC-3 drive table not re-declared",
             "TC-8 port inputs absent"},
            "w04_reusability_verdict_missing")
    require(verdict["instrument_executed"] is True,
            "w04_reusability_verdict_missing")


def detect_seeds_runbook(m):
    sr = m["seeds_runbook_slot"]
    require(sr["slot_status"] == "FROZEN_SLOT_SHAPE_VALUES_STRUCTURALLY_"
                                 "DOWNSTREAM_W05",
            "w04_seed_value_encroachment")
    for field in ("seeds", "runbook_id", "acceptance_criteria"):
        require(field in sr["declared_fields"], "w04_seed_value_encroachment")
        require(sr["declared_fields"][field]["value"] is None,
                "w04_seed_value_encroachment")
        require("W05" in sr["declared_fields"][field]["owner"],
                "w04_seed_value_encroachment")
    laws = {lid["identity"] for lid in sr["governing_laws"]}
    require("K01" in laws and "P04" in laws, "w04_law_identity_missing")


def detect_claim_class(m):
    rp = m["runtime_profile"]
    require(rp["claim_class"] == ("offline/trace qualification at the 300 Hz "
                                  "tick only; interactive real-time 300 Hz "
                                  "NOT satisfied"),
            "w04_realtime_claim")
    require(rp["interactive_realtime_300hz"] == "NOT SATISFIED",
            "w04_realtime_claim")
    cost = rp["cost_gap_citation"]
    require(cost["receipt_sha256"] == TICK_COST_SHA, "input_pin_mismatch:"
            "tick_cost")
    require(cost["budget_ms_per_tick"] == 3.333
            and cost["over_budget_x"] == [13.7, 6.7]
            and cost["verdict"] == "COST-GAP FIRED (clause F1)",
            "w04_realtime_claim")
    require(rp["training_throughput_bound_to"] == "P04 reservation discipline",
            "w04_realtime_claim")


def detect_state_hashes(m):
    rows = m["views"]
    require(len(rows) >= 1, "w04_capture_rows_missing")
    hashes = {r["state_binding"]["sha256"] for r in rows}
    require(len(hashes) == 1, "w04_toggle_state_hash_move")


DETECTORS = {
    "FB1": ("w04_manifest_body_domain_unbound", detect_body_domain),
    "FB2": ("w04_port_invented_constant", detect_ports),
    "FB3": ("w04_policy_trained_claim", detect_policy_slot),
    "FB4": ("w04_seed_value_encroachment", detect_seeds_runbook),
    "FB5": ("w04_realtime_claim", detect_claim_class),
    "FB6": ("w04_toggle_state_hash_move", detect_state_hashes),
}


# ----------------------------------------------------------------- generator

def build_manifest():
    card, profile = load_registry()
    prereg_sha = sha_file(HERE / "PREREGISTRATION.md")
    c09 = json.loads((HERE / "c09_reseal" / "c09_anchor_reseal.json")
                     .read_text("utf-8"))
    c09_sha = sha_file(HERE / "c09_reseal" / "c09_anchor_reseal.json")
    require(c09["schema"] == "chimera.w04_c09_anchor_reseal.v1",
            REFUSAL + ":c09_schema")
    require(all(v["verdict"] == "EXACT" for v in
                c09["anchor_comparisons"].values()), REFUSAL + ":c09_drift")
    gate = json.loads((HERE / "gate_reissue" / "w04_gate_receipt.json")
                      .read_text("utf-8"))
    gate_sha = sha_file(HERE / "gate_reissue" / "w04_gate_receipt.json")
    require(gate["validator"]["verdict"] == "VALID", REFUSAL + ":cert_invalid")
    require(gate["injections"]["all_caught"] is True,
            REFUSAL + ":injections_missed")
    cert_sha = sha_file(HERE / "w04_certificate.json")
    require(cert_sha == gate["w04_certificate_sha256"],
            REFUSAL + ":cert_receipt_mismatch")

    obs_v2_sha = require_pin(OBS_V2_PATH, OBS_V2_SHA, "obs_v2")
    obs_section_sha = require_pin(OBS_SECTION_PATH, OBS_SECTION_SHA,
                                  "obs_section")
    tick_sha = require_pin(TICK_COST_PATH, TICK_COST_SHA, "tick_cost")
    portq_sha = require_pin(PORT_QUAL_PATH, PORT_QUAL_SHA, "port_qual")
    ms_sha = require_pin(MEASURED_SOURCES_PATH, MEASURED_SOURCES_SHA,
                         "measured_sources")
    add_sha = require_pin(ADDITION_PATH, ADDITION_SHA, "adoption_record")
    addition = json.loads(ADDITION_PATH.read_text("utf-8"))
    bind = addition["tc7_body_domain_bind"]["bound_as"]
    require(bind["body_digest"] == BODY_DIGEST,
            "input_pin_mismatch:body_digest")

    state_hash = hashlib.sha256(canonical_bytes({
        "adoption_record": add_sha,
        "b04_frames": sha_file(CONTRIB / "MAT2-B04" / "frame_forest.json"),
        "b05_ports": sha_file(CONTRIB / "MAT2-B05"
                              / "mechanical_port_requirements.json"),
        "b06_readiness": sha_file(STORE / "MAT2-B06" / "numerical"
                                  / "assembly_readiness.json"),
        "observation_interface_v2": obs_v2_sha,
        "obs_section_v2": obs_section_sha,
        "tick_cost_receipt": tick_sha,
        "port_qualification": portq_sha,
        "measured_sources": ms_sha,
        "c09_reseal": c09_sha,
        "gate_reissue_receipt": gate_sha,
        "w04_certificate": cert_sha,
        "preregistration": prereg_sha,
    })).hexdigest()

    manifest = {
        "schema": "chimera.w04_training_manifest.v1",
        "task_id": TASK_ID,
        "card_id": CARD_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": prereg_sha,
        "candidate_base": CANDIDATE_BASE,
        "profile_id": profile["id"],
        "done_when_binding": {
            "exact_dynamics": {
                "tick_hz": 300, "substeps": 4,
                "policy_hz": 20, "hold_ticks": 15,
                "anchor_class": "C09 re-sealed EXACT at the W04 revision "
                                "(certified CPU walk backend only; BQ-1)",
                "c09_reseal_receipt": pin(HERE / "c09_reseal"
                                          / "c09_anchor_reseal.json", c09_sha),
            },
            "observations_actions": {
                "interface": "policy_observation_interface v2 (80 fields; "
                             "OBS_SCHEMA_VERSION 2; FIELDS[:64] the frozen v1 "
                             "width replaying bitwise-identically)",
                "observation_interface_v2": pin(OBS_V2_PATH, obs_v2_sha),
                "normalization_section": pin(OBS_SECTION_PATH,
                                             obs_section_sha),
                "privileged_sources": "never occupy a slot "
                                      "(privileged_forbidden)",
            },
            "model_revision": {
                "candidate_base": CANDIDATE_BASE,
                "certified_anchor_source_revision": c09["source_revision"],
                "certificate_sha256": cert_sha,
                "certificate_compat_key": gate["w04_compat_key"],
                "certificate_cert_hash": gate["w04_cert_hash"],
            },
            "seeds_runbook": "frozen at slot shape + law identity (FC-4; "
                             "values structurally downstream, W05 wave 6; "
                             "BQ-3)",
        },
        "body_domain": {
            "clause": "TC-7 (FC-1)",
            "bound_value": {
                "body_digest": BODY_DIGEST,
                "domain_tag": DOMAIN_TAG,
                "adoption_decision_kind":
                    addition["adoption_decision"]["kind"],
                "adoption_message_id":
                    addition["governing_frame"]["message_id"],
                "qualification_state": bind["qualification_state"],
            },
            "adoption_record": pin(ADDITION_PATH, add_sha),
            "mass_rulings": [
                {"ruling": "R-MASS-04",
                 "text": "5.262978509953907 kg stays uncounted pending "
                         "density validation; the 11.777 kg pelvis quantity "
                         "is a NON-PHYSICAL reference"},
                {"ruling": "R-MASS-02",
                 "text": "bone material density stays UNVALIDATED; MAT-03 "
                         "admission only when a measured conditioned source "
                         "exists"},
                {"ruling": "R-MASS-03",
                 "text": "carried-load mass for port weights only from a NEW "
                         "validated source; the certified 10.037998 kg "
                         "walking line is UNCHANGED (TC-12 symmetric "
                         "clause)"},
            ],
            "tc12_lineages": "separate parallel records; no silent "
                             "replacement decision taken",
        },
        "port_active_law_inputs": {
            "clause": "TC-8 (FC-2; LT ruling BQ-5)",
            "status": "UNQUALIFIED_BY_HONEST_REFUSAL",
            "ports_qualified": 0,
            "ports_total": 8,
            "measured_inputs_admitted": [],
            "refusals": [
                {"identity": "B05 0/8",
                 "quote": "Eight ports missing parameters; source tendon "
                          "points are insufficient",
                 "evidence": pin(PORT_QUAL_PATH, portq_sha)},
                {"identity": "R-OWN-05",
                 "quote": "no attachment patch area/shape, areal stiffness, "
                          "couple resistance or weights exist in the pinned "
                          "sources; none is invented (24 refused waypoint "
                          "cells; measured-source matrix delivered, NOTHING "
                          "admitted; the Lieutenant admits)",
                 "evidence": pin(MEASURED_SOURCES_PATH, ms_sha)},
                {"identity": "R-PRT-01",
                 "quote": "authored requirements, declared laws and "
                          "demonstrated gate mechanics NEVER qualify a port",
                 "evidence": pin(PORT_QUAL_PATH, portq_sha)},
            ],
        },
        "policy_artifact": {
            "clause": "TC-9 (FC-3)",
            "status": "EXPLICITLY_UNRESOLVED",
            "trained_walking_policy_exists": False,
            "p3_bundle_role": ("the P3 registered test manifest "
                               "(architecture [64,128,128,8], frozen weights "
                               "sha 5fb2b785..., loader "
                               "typeb_export.policy_manifest.load_manifest) "
                               "is the gate-mechanics DEMONSTRATION CASE, "
                               "NOT a trained policy"),
            "reusability_verdict": {
                "verdict": gate["reusability_verdict"]["verdict"],
                "mismatch_dimensions": ["TC-7 body domain rebind",
                                        "TC-3 drive table not re-declared",
                                        "TC-8 port inputs absent"],
                "instrument_executed": True,
                "instrument_receipt": pin(HERE / "gate_reissue"
                                          / "w04_gate_receipt.json", gate_sha),
            },
        },
        "seeds_runbook_slot": {
            "clause": "TC-10 (FC-4; LT ruling BQ-3)",
            "slot_status": ("FROZEN_SLOT_SHAPE_VALUES_STRUCTURALLY_DOWNSTREAM"
                            "_W05"),
            "declared_fields": {
                "seeds": {"value": None,
                          "owner": "MAT2-W05 (wave 6, behind W04)"},
                "runbook_id": {"value": None,
                               "owner": "MAT2-W05 (wave 6, behind W04)"},
                "acceptance_criteria": {"value": None,
                                        "owner": "MAT2-W05 (wave 6, behind "
                                                 "W04)"},
            },
            "governing_laws": [
                {"identity": "K01",
                 "law": "Observations, actions, reward, termination, success "
                        "metrics, seeds, envelope and falsifiers approved "
                        "before training"},
                {"identity": "P04",
                 "law": "APPROVED reservations before any training run; "
                        "preregistration commits separately"},
            ],
        },
        "runtime_profile": {
            "clause": "TC-11 (FC-5; LT ruling BQ-2)",
            "physics_hz": 300, "policy_hz": 20, "hold_ticks": 15,
            "tick_budget_ms": 3.333,
            "claim_class": ("offline/trace qualification at the 300 Hz tick "
                            "only; interactive real-time 300 Hz NOT satisfied"),
            "interactive_realtime_300hz": "NOT SATISFIED",
            "cost_gap_citation": {
                "receipt": pin(TICK_COST_PATH, tick_sha),
                "receipt_sha256": tick_sha,
                "budget_ms_per_tick": 3.333,
                "full_loop_ms_receipt_era": 46.447,
                "full_loop_ms_receipt_machine_state": 23.26,
                "over_budget_x": [13.7, 6.7],
                "verdict": "COST-GAP FIRED (clause F1)",
                "residual": "97.1% step.integrate; fk.evaluate 87.9% of the "
                            "loop, 286.6 calls/tick",
                "gpu_split_note": "confirmed GPU-production split still 4.9x; "
                                  "GPU mailbox single-occupancy",
            },
            "training_throughput_bound_to": "P04 reservation discipline",
        },
        "actuation_interface": {
            "clause": "TC-3",
            "status": "RE_DECLARE_PENDING_FROM_THE_ASSEMBLY_OWN_SEALED_SOURCES",
            "certified_scene_caps_never_transfer": [
                "hip 11.2125 / knee 6.6375 / ankle 7.4 / MP 0.8875 N.m "
                "(hind); fore shoulder 4.229 / fore elbow 3.76 N.m are the "
                "CERTIFIED 10.038 kg scene's drives only"],
            "laws": ["no pose-writing", "no teleport",
                     "no force outside the capped channels",
                     "no human-norm torque substituted for this animal (C07)"],
        },
        "test_suite_slot": {
            "certificate_suite": gate["suite"] if "suite" in gate else
            "upgrade_gate_20260920/registered_cases_v1",
            "injections": "4/4 CAUGHT (I1..I4) on the W04 certificate",
            "named_checks": "test_w04_freeze.py (see checks_receipt.json for "
                            "the executed/skipped accounting)",
            "explicitly_unresolved": [
                {"item": "judgement_stride.json",
                 "disposition": ("carried explicitly-unresolved (BQ-4); "
                                 "owner unchanged, P02 lineage; does not "
                                 "gate this freeze")},
                {"item": "duty factor",
                 "disposition": ("NOT DERIVABLE in the sealed W03 trace (no "
                                 "contact records; recorded MISSING, not "
                                 "imputed)")},
                {"item": "CT distribution",
                 "disposition": ("BLOCKED FOR SHIP 066485ae — quoted, a "
                                 "separate record's ship decision; not "
                                 "W04's authority to repair")},
                {"item": "CoT denominator correction",
                 "disposition": ("needs lead-authorized NEW registration; "
                                 "owner unchanged; carried open")},
            ],
        },
        "explicitly_unresolved_inventory": [
            "trained walking policy (five standing gaps; P02 "
            "prototype_recovery) — closed explicitly-unresolved in FC-3",
            "interactive playable walk — declared NOT satisfied in FC-5; "
            "deliverable belongs to the M08 budget chain",
            "judgement_stride.json — carried explicitly-unresolved (BQ-4)",
            "CT distribution — BLOCKED FOR SHIP 066485ae (quoted; out of "
            "scope)",
            "CoT denominator — lead-authorized NEW registration (out of "
            "scope)",
        ],
        "views": [  # the frozen view plan; make_capture.py renders exactly these rows
            {"view_id": "whole-creature overview", "mode": "diagnostic",
             "state_binding": {"kind": "record", "sha256": state_hash}},
            {"view_id": "whole-creature overview", "mode": "clean",
             "state_binding": {"kind": "record", "sha256": state_hash}},
            {"view_id": "local attachment close-up", "mode": "diagnostic",
             "state_binding": {"kind": "record", "sha256": state_hash}},
            {"view_id": "local attachment close-up", "mode": "clean",
             "state_binding": {"kind": "record", "sha256": state_hash}},
            {"view_id": "orthogonal side view", "mode": "diagnostic",
             "state_binding": {"kind": "record", "sha256": state_hash}},
            {"view_id": "orthogonal side view", "mode": "clean",
             "state_binding": {"kind": "record", "sha256": state_hash}},
            {"view_id": "oblique view", "mode": "diagnostic",
             "state_binding": {"kind": "record", "sha256": state_hash}},
            {"view_id": "oblique view", "mode": "clean",
             "state_binding": {"kind": "record", "sha256": state_hash}},
        ],
        "state_composite_sha256": state_hash,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B make_freeze_manifest.py"},
    }
    # detector self-check on the CLEAN manifest (every arm must pass clean)
    for name, (code, fn) in sorted(DETECTORS.items()):
        fn(manifest)
    return manifest


def pin(path, sha):
    return {"path": str(path).replace("\\", "/"), "sha256": sha}


def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def main():
    try:
        manifest = build_manifest()
    except Refusal as exc:
        print("REFUSAL: " + exc.code, file=sys.stderr)
        return 2
    out = HERE / "w04_freeze_manifest.json"
    out.write_bytes(canonical_bytes(manifest) + b"\n")
    print("wrote", out)
    print("state_composite_sha256", manifest["state_composite_sha256"][:16],
          "...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
