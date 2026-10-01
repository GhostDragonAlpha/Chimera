#!/usr/bin/env python3
"""MAT2-B07 adoption record: the R-FRM-02 acceptance + packet-to-forest
binding, the R-FRM-03 component/bond admission on the closed cross-record
agreement evidence, the per-row B06 readiness closure table, the TC-7
body-domain bind and the TC-12 rebind record.

Authorized by Captain decision #4 (ADOPT-WITH-AUTHORIZATIONS), message
msg-4def1f92578b44d9b57b381643eae245, items (7) and (8), plus the TC-7 note
("the runtime contract body domain (UNBOUND_dummy) binds to the adopted
assembly AS the B07 attempt outcome - the rebind rule TC-12 governs").

LAWS: this script emits records; it never flips a sealed row, never
qualifies a port, never admits mass, never authors a frame alignment, and
NEVER claims assembly_readiness = true. The certified 10.037998 kg walking
line is not touched and not invalidated. The MASSREG implied-BW escalation
stays at the walk tier and is cited, never re-litigated.

Run:  python -B adoption_record.py   (writes frame_bindings.json + adoption_record.json)
Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRIB = HERE.parent
CHECKOUT = CONTRIB.parents[2]
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
PREREQ = Path("E:/ChimeraWork/monkey-coordination/b07-prereqs")

B04_PATH = CONTRIB / "MAT2-B04" / "frame_forest.json"
B04_SHA256 = "156ef55722e1ecda3238f3733131eb707f209cb93531d0e133227b00ebba8203"
B05_PATH = CONTRIB / "MAT2-B05" / "mechanical_port_requirements.json"
B05_SHA256 = "ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d"
B06_RECEIPT_PATH = STORE / "MAT2-B06" / "numerical" / "assembly_readiness.json"
B06_RECEIPT_SHA256 = ("88fa5e2d599017f5c9bf69ac92d920f23334c221f4afe87ccdda"
                      "235f1fab2c71")
PRODUCER_PATH = PREREQ / "inputs" / "actual_monkey_fit@43b599a7.json"
PRODUCER_SHA256 = ("7b5d6345f6d56ec77c072aecefde2ae592e3bc3fc96b439e5eff1644"
                   "25834268")
MASSREG_PATH = CONTRIB / "MAT2-D-MASSREG" / "mass_register.json"
MASSREG_SHA256 = ("61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe"
                  "693cc7a")
DECISION_TABLE_PATH = (CONTRIB / "ONT-A02" / "reference"
                       / "ANATOMICAL_DECISION_TABLE.md")
A02_REPORT_PATH = CONTRIB / "MAT2-A02" / "REPORT.md"
READINESS_CLOSURE_PATH = STORE / "MAT2-B07" / "numerical" / "READINESS_CLOSURE.md"
PORT_QUALIFICATION_PATH = (STORE / "MAT2-B07" / "numerical"
                           / "PORT_QUALIFICATION.md")
RUNTIME_CONTRACT_PATH = (STORE / "MAT2-B07" / "numerical"
                         / "RUNTIME_CONTRACT.md")
MASS_AUDIT_RECEIPT_PATH = PREREQ / "numerical" / "mass_audit_receipt.json"
MASS_AUDIT_RECEIPT_SHA256 = ("3aea85bc7e07ebceb3d1f6f9e969fc9af14edc198620d2"
                             "8ef955da619d351922")
FITTING_RECEIPT_PATH = STORE / "MAT2-B07" / "numerical" / "fitting_receipt.json"
FITTING_RECEIPTS_MD_PATH = (STORE / "MAT2-B07" / "numerical"
                            / "FITTING_RECEIPTS.md")
MEASURED_SOURCES_PATH = (STORE / "MAT2-B07" / "numerical"
                         / "MEASURED_SOURCES.md")
ADMISSION_PROPOSAL_PATH = (STORE / "MAT2-B07" / "numerical"
                           / "ADMISSION_PROPOSAL.md")

OSIM_PATH = (CONTRIB / "MAT2-M02" / "data" / "macaque_arm"
             / "monkeyArm_current.osim")
OSIM_SHA256 = "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"

REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
CRITERIA_SHA256 = ("5393a5d7707c370ce5c8ea072512a2b053d0abfb1d36dc952d509"
                   "714150c77d2")
TASK_ID = "MAT2-B07"
SHORT_ID = "B07"
AUTH_MESSAGE_ID = "msg-4def1f92578b44d9b57b381643eae245"
CERTIFICATE_REPLICA = (Path("E:/ChimeraWork/pass3-integ/repo/tools/science_"
                            "funnel/validation/upgrade_gate_20260920")
                       / "certificate.json")

EXPECTED_ROOT_BODY = {"component_pelvis": "pelvis",
                      "component_thorax": "thorax",
                      "component_ulna": "ulna",
                      "component_ulna_l": "ulna_l"}
EXPECTED_UNRESOLVED = ["hand_l", "hand_r", "talus_l", "talus_r", "thorax",
                       "toes_l", "toes_r", "ulna", "ulna_l"]

REFUSAL_PIN = "input_pin_mismatch"
REFUSAL_BINDING = "binding_name_mismatch"
REFUSAL_AGREEMENT = "agreement_mismatch"
REFUSAL_CRITERIA = "criteria_pin_mismatch"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def pin(path, expected=None):
    digest = sha256_file(path)
    if expected is not None:
        require(digest == expected, REFUSAL_PIN + ":" + Path(path).name)
    return {"path": str(path).replace("\\", "/"), "sha256": digest}


def check_registry_criteria():
    require(REGISTRY.exists(), REFUSAL_CRITERIA + ":registry_missing")
    uri = "file:" + str(REGISTRY).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        row = con.execute("SELECT payload FROM state WHERE id='1'").fetchone()
    finally:
        con.close()
    require(row is not None, REFUSAL_CRITERIA + ":registry_empty")
    card = json.loads(row[0])["kanban"]["cards"].get(TASK_ID)
    require(card is not None, REFUSAL_CRITERIA + ":card_missing")
    require(card.get("criteria_sha256") == CRITERIA_SHA256,
            REFUSAL_CRITERIA + ":registry_value_drift")


def verify_cross_record_agreement(b04, producer):
    """READINESS_CLOSURE section 3.4, re-verified from pinned bytes: the B04
    unresolved set == the producer fit's unresolved set; counted mass 0.0."""
    b04_unresolved = sorted(u["body"] for u in b04["unresolved_bodies"])
    producer_unresolved = sorted(
        producer["admission"]["bodies"]["unresolved"])
    require(b04_unresolved == EXPECTED_UNRESOLVED,
            REFUSAL_AGREEMENT + ":b04_set:" + json.dumps(b04_unresolved))
    require(producer_unresolved == EXPECTED_UNRESOLVED,
            REFUSAL_AGREEMENT + ":producer_set:"
            + json.dumps(producer_unresolved))
    counted = b04["matter_boundary"]["counted_mass_kg"]
    require(counted == 0.0, REFUSAL_AGREEMENT + ":counted_mass_nonzero")
    return {"b04_unresolved": b04_unresolved,
            "producer_unresolved": producer_unresolved,
            "equal": True, "counted_mass_kg": counted}


def build_binding_rows(b04):
    frames = b04["frames"]
    rows = []
    fitted_by_body = {}
    for body, f in b04["fitted_frames"].items():
        require(f["coordinate_system"] == "anatomy_packet_fitted",
                REFUSAL_BINDING + ":coord_sys:" + body)
        fitted_by_body[f["body"]] = f["frame_id"]
    for comp in b04["components"]:
        cid = comp["component_id"]
        root_frame_id = comp["root_frame_id"]
        frame = frames.get(root_frame_id)
        require(frame is not None and frame.get("component_root") is True,
                REFUSAL_BINDING + ":root_frame_missing:" + cid)
        root_body = frame["body"]
        require(root_body == EXPECTED_ROOT_BODY[cid],
                REFUSAL_BINDING + ":" + cid + ":" + str(root_body))
        member_fitted = sorted(fitted_by_body[b] for b in comp["bodies"]
                               if b in fitted_by_body)
        rows.append({
            "component_id": cid,
            "authored_root_frame_id": root_frame_id,
            "authored_root_frame_body": root_body,
            "component_member_bodies": sorted(comp["bodies"]),
            "fitted_frames_bound_by_stable_name": member_fitted,
            "binding_rule": "stable name only (component root body == "
                            "authored root frame body); no transform is "
                            "authored; fitted frames remain placement-only",
            "b04_no_fusion_statement_carried": b04["no_fusion_statement"],
        })
    return rows


def authorization_items():
    return [
        {"item": 1, "ruling": "R-MASS-04",
         "text": "keep 5.262978509953907 kg uncounted pending density "
                 "validation AND rule the 11.777 kg pelvis quantity a "
                 "NON-PHYSICAL reference (the lawful default, matches the "
                 "producer exclusion). No validated-density admission path "
                 "opened.",
         "discharge": "closed_by_recorded_ruling",
         "evidence": "accounting half closed by the bit-exact mass audit "
                     "(numerical receipt " + MASS_AUDIT_RECEIPT_SHA256[:16]
                     + "...); the ruling text is recorded in "
                     "adoption_record.json"},
        {"item": 2, "ruling": "R-MASS-02",
         "text": "bone material density stays UNVALIDATED (register-honest); "
                 "MAT-03 admission only when a measured conditioned source "
                 "exists - no synthetic, no literature-typical promotion.",
         "discharge": "closed_by_recorded_ruling",
         "evidence": "the explicit ruling on the researched class scope is "
                     "recorded; no density value is admitted anywhere in "
                     "this attempt"},
        {"item": 3, "ruling": "R-MASS-03",
         "text": "carried-load mass for port weights must come from a NEW "
                 "validated source; the transported set is never promoted; "
                 "ports stay honestly refused (0/8).",
         "discharge": "refusal_stands",
         "evidence": "PORT_QUALIFICATION.md (honest refusal record) cited; "
                     "this attempt qualifies no port"},
        {"item": 4, "ruling": "R-OWN-02/03",
         "text": "the B07 attempt records the 14 hand-body mapping decisions "
                 "+ 31 forearm correspondences with distances as attempt "
                 "work.",
         "discharge": "closed_by_work_with_receipt",
         "evidence": "ownership_mappings.json (14 + 31 records, distances; "
                     "A05 law verified bit-exact 3/3 before emission)"},
        {"item": 5, "ruling": "R-OWN-04",
         "text": "the fitting lane for the 8 outside placements may be "
                 "dispatched under standard evidence discipline.",
         "discharge": "lane_evidence_delivered",
         "evidence": "lane wk-rown04-fitting landed measured fits for all "
                     "8 outside placements (FITTING_RECEIPTS.md + "
                     "fitting_receipt.json, store-pinned); integrated "
                     "here; NO fitted candidate is adopted and the sealed "
                     "outside statuses keep their exact per-axis excesses"},
        {"item": 6, "ruling": "R-OWN-05",
         "text": "the c17-stiffness lane completes measured "
                 "attachment-interface sources; lead admission ONLY on "
                 "measured sources.",
         "discharge": "lane_evidence_delivered",
         "evidence": "lane wk-rown05-stiffness delivered the measured "
                     "source matrix + the bounded admission questions "
                     "(MEASURED_SOURCES.md + ADMISSION_PROPOSAL.md, "
                     "store-pinned); integrated here; NOTHING is admitted "
                     "(the lane's own recommendation: admit nothing today; "
                     "the Lieutenant admits)"},
        {"item": 7, "ruling": "R-FRM-02",
         "text": "ulna-edge correspondence acceptance + packet-to-forest "
                 "binding proceed as attempt work.",
         "discharge": "closed_by_work_with_receipt",
         "evidence": "frame_bindings.json (acceptance + stable-name binding "
                     "table, verified from the pinned B04 bytes)"},
        {"item": 8, "ruling": "R-FRM-03",
         "text": "component/bond admission on the closed cross-record "
                 "agreement evidence half.",
         "discharge": "closed_by_recorded_ruling_with_work_receipt",
         "evidence": "frame_bindings.json part B (admission on the "
                     "re-verified agreement: same 9 unresolved bodies, "
                     "counted mass 0.0)"},
    ]


def per_row_table():
    """The sealed B06 receipt's 14 requirement rows with this attempt's
    closure evidence per row. Sealed statuses are NEVER flipped here."""
    rows = [
        {"requirement_id": "R-MASS-01", "domain": "mass",
         "sealed_status": "evaluated_satisfied_at_scope",
         "closure_class": "satisfied_row_untouched",
         "evidence": "counted set 0.0447023937544344 kg; pin re-verified",
         "statement": "untouched satisfied row"},
        {"requirement_id": "R-MASS-02", "domain": "mass",
         "sealed_status": "evaluated_gap",
         "closure_class": "closed_by_recorded_ruling",
         "evidence": "authorization item 2 (density stays UNVALIDATED; "
                     "MAT-03 admission only on a measured conditioned "
                     "source)",
         "statement": "the explicit lead ruling on the researched class "
                      "scope the gap demanded is now recorded; no density "
                      "is admitted"},
        {"requirement_id": "R-MASS-03", "domain": "mass",
         "sealed_status": "evaluated_gap",
         "closure_class": "refusal_stands",
         "evidence": "authorization item 3 + PORT_QUALIFICATION.md; the "
                     "carried-load mass needs a NEW validated source",
         "statement": "the honest refusal stands; no port weight is backed "
                      "by the transported set"},
        {"requirement_id": "R-MASS-04", "domain": "mass",
         "sealed_status": "evaluated_gap",
         "closure_class": "closed_by_recorded_ruling_with_work_receipt",
         "evidence": "authorization item 1 + the bit-exact mass audit "
                     "receipt (b07-prereqs)",
         "statement": "5.262978509953907 kg stays uncounted; the 11.777 kg "
                      "pelvis quantity is ruled a non-physical reference; "
                      "no density admission path is opened"},
        {"requirement_id": "R-OWN-01", "domain": "ownership",
         "sealed_status": "evaluated_satisfied_at_scope",
         "closure_class": "satisfied_row_untouched",
         "evidence": "owner+role over 48/26/22/6 records; pin re-verified",
         "statement": "untouched satisfied row"},
        {"requirement_id": "R-OWN-02", "domain": "ownership",
         "sealed_status": "evaluated_gap",
         "closure_class": "closed_by_work_with_receipt",
         "evidence": "ownership_mappings.json: 14 recorded assembly-mapping "
                     "decisions with distances",
         "statement": "the recorded mapping decision with distance the gap "
                      "demands now exists as attempt work under "
                      "authorization item 4"},
        {"requirement_id": "R-OWN-03", "domain": "ownership",
         "sealed_status": "evaluated_gap",
         "closure_class": "closed_by_work_with_receipt",
         "evidence": "ownership_mappings.json: 31 forearm correspondence "
                     "records with distances",
         "statement": "the recorded forearm correspondence the gap demands "
                      "now exists as attempt work under authorization "
                      "item 4"},
        {"requirement_id": "R-OWN-04", "domain": "ownership",
         "sealed_status": "evaluated_gap",
         "closure_class": "lane_evidence_delivered",
         "evidence": "lane wk-rown04-fitting (authorized, item 5): "
                     "measured fits for all 8 outside placements with "
                     "disclosed residuals (fitting_receipt.json + "
                     "FITTING_RECEIPTS.md, store-pinned)",
         "statement": "the authorized fitting experiment has RUN and its "
                      "measured correspondence evidence is integrated; the "
                      "sealed outside placements keep their exact per-axis "
                      "excesses; no fitted candidate is adopted and any "
                      "status flip is a lawful re-evaluation's act"},
        {"requirement_id": "R-OWN-05", "domain": "ownership",
         "sealed_status": "evaluated_gap",
         "closure_class": "lane_evidence_delivered",
         "evidence": "lane wk-rown05-stiffness (authorized, item 6): the "
                     "measured attachment-interface source matrix + the "
                     "bounded admission questions (MEASURED_SOURCES.md + "
                     "ADMISSION_PROPOSAL.md, store-pinned)",
         "statement": "the measured-source evidence half is delivered and "
                      "integrated; NOTHING is admitted (the lane's own "
                      "recommendation: admit nothing today); the lead "
                      "admission question is recorded for the Lieutenant"},
        {"requirement_id": "R-FRM-01", "domain": "frame",
         "sealed_status": "evaluated_satisfied_at_scope",
         "closure_class": "satisfied_row_untouched",
         "evidence": "four roots recomposed; pin re-verified",
         "statement": "untouched satisfied row"},
        {"requirement_id": "R-FRM-02", "domain": "frame",
         "sealed_status": "evaluated_gap",
         "closure_class": "closed_by_work_with_receipt",
         "evidence": "frame_bindings.json: ulna-edge correspondence "
                     "acceptance (U-STR, O1-resolved roll, radius "
                     "supersession consequence accepted) + the "
                     "packet-to-forest stable-name binding table",
         "statement": "the acceptance + binding authorization the gap "
                      "demands are recorded under authorization item 7; "
                      "no alignment is authored"},
        {"requirement_id": "R-FRM-03", "domain": "frame",
         "sealed_status": "evaluated_gap",
         "closure_class": "closed_by_recorded_ruling_with_work_receipt",
         "evidence": "frame_bindings.json part B: component/bond admission "
                     "on the re-verified cross-record agreement (same 9 "
                     "unresolved bodies; counted mass 0.0)",
         "statement": "the admission decision is recorded on the closed "
                      "agreement evidence under authorization item 8; "
                      "admission statuses carry through unchanged"},
        {"requirement_id": "R-PRT-01", "domain": "port",
         "sealed_status": "evaluated_gap",
         "closure_class": "refusal_stands",
         "evidence": "authorization item 3 + PORT_QUALIFICATION.md (0/8 "
                     "qualifiable, 24/24 waypoints refused, blockers "
                     "stack)",
         "statement": "the honest refusal is the lawful terminal state; "
                      "this attempt qualifies no port"},
        {"requirement_id": "R-PRT-02", "domain": "port",
         "sealed_status": "evaluated_satisfied_at_scope",
         "closure_class": "satisfied_row_untouched",
         "evidence": "declared pressure limits re-read on 8 ports; declared "
                     "never qualifies",
         "statement": "untouched satisfied row"},
    ]
    require(len(rows) == 14, "row_table_length:" + str(len(rows)))
    return rows


def named_reason():
    return (
        "ADOPT-WITH-AUTHORIZATIONS (Captain decision #4, docket "
        "proceed-as-recommended on the reconsideration packet). The Architect "
        "names why this assembly replaces the current body: (1) the "
        "campaign-level material-first architecture decision "
        "(MATERIAL_PLAN_ADOPTION.md, recorded at P01) selected the material "
        "assembly as the modernization path, and the reconsideration packet "
        "proved the remaining adoption distance was AUTHORIZATIONS, not "
        "evidence or effort; (2) actual limb load transmission is evidenced "
        "at limb scope (MAT2-M11 sealed DONE, PR #279, all gates green: "
        "tissue-to-bone-to-foot-to-ground transmission with activation-off, "
        "connection-removal and pressure-limit falsifiers fired and an energy "
        "ledger); (3) the runtime/training contract SHAPE exists as a bound "
        "specification (TC-1..TC-6 + the TC-12 rebind rule) with exactly one "
        "B07-specific slot open (TC-7 body domain, UNBOUND_dummy by design - "
        "filling it IS the adoption decision this record makes); (4) the "
        "decision-gated B06 readiness gaps now carry the Captain's 8-item "
        "authorization package and this attempt's work receipts (14+31 "
        "ownership mappings with distances, R-FRM-02 acceptance + binding, "
        "R-FRM-03 admission on the closed agreement evidence). The adoption "
        "is recorded as the BINDING TARGET for the runtime contract's body "
        "domain: the certified 10.037998 kg walking line continues untouched "
        "(conditional branch; TC-12 symmetric clause) and the adopted "
        "assembly is NOT runtime-qualified today - TC-8's measured inputs do "
        "not exist (0/8 ports, honest refusal stands), so 'before use' "
        "requalification stays gated on the named rebind prerequisites. "
        "Static export is not runtime qualification: this record claims no "
        "static export as qualification. The MASSREG two-systems "
        "classification and its implied-BW escalation belong to the walk "
        "tier and are cited, not re-litigated, here.")


def tc7_bind(adoption_pin_digest):
    return {
        "clause": "TC-7 BODY DOMAIN SLOT (RUNTIME_CONTRACT.md section 5)",
        "prior_state": "UNBOUND_dummy (P3 manifest body: status UNBOUND -- "
                       "binds automatically when the real actor exists); "
                       "domain_tag cpu-walk-scene/hind-pad-surrogate; "
                       "physics_build cpu-walk-scene-build-N",
        "bound_as": {
            "body_digest": "chimera.b07.adoption." + adoption_pin_digest[:32],
            "digest_law": "sha256 over the canonical pin list of the "
                          "adoption record (the sealed identities this "
                          "decision binds); computed, not invented",
            "domain_tag": "material-assembly/buffy02-lineage",
            "mass_line": "counted 0.0 kg; transported "
                         "17.039978509953905 kg deliberately non_consumed; "
                         "the certified walking body 10.037998 kg is "
                         "UNCHANGED in every scene/ledger",
            "qualification_state": "NOT runtime-qualified: TC-8 measured "
                                   "inputs absent (0/8 ports, honest "
                                   "refusal stands); drive table not "
                                   "re-declared (TC-3 re-declare pending "
                                   "from the assembly's own sealed sources)",
        },
        "status": "BOUND_AS_ADOPTION_TARGET_RECORD (the recorded adoption "
                  "decision; the runtime certificate re-issue for this body "
                  "is gated on the TC-12 prerequisites below and is NOT "
                  "fabricated by this attempt)",
    }


def tc12_rebind():
    return {
        "clause": "TC-12 THE ADOPTION REBIND RULE (BOUND as the rule; its "
                  "execution is the decision)",
        "rule_carried": "Adopting the material assembly MUST NOT silently "
                        "reuse the current contract: the body domain "
                        "rebinds (TC-7), actuation re-declares from the "
                        "assembly's own sealed sources (TC-3), port/law "
                        "inputs must exist or the assembly stays "
                        "unqualified (TC-8), a new certificate is issued "
                        "through the TC-6 gate, and the C09 anchor class "
                        "re-runs on every claimed backend (TC-5).",
        "executed_here": {
            "tc7_bind": "recorded above (the body domain slot value)",
            "c09_anchor_class_rerun": "executed in this attempt against the "
                                      "CERTIFIED CPU walk backend (the "
                                      "certified line's own anchors) - "
                                      "c09_anchor_rerun/ receipt; drift = "
                                      "anchor_drift refusal",
            "sealed_certificate_gate_validate": "the sealed upgrade-gate "
                                                "certificate re-validated "
                                                "UNCHANGED through the gate "
                                                "machinery (validate mode) "
                                                "as a machinery-intact "
                                                "screen; screens never gate",
        },
        "reissue_prerequisites_named": [
            "a runtime scene module executing the adopted assembly (none "
            "exists; creating one is the runtime lane's card outcome)",
            "TC-3: the adopted assembly's drive table re-declared from ITS "
            "own sealed sources (the current caps never transfer silently)",
            "TC-8: measured port/law inputs (patch area, areal stiffness, "
            "couple resistance, carried-load weights, bound frames) - the "
            "exact blockers of the honest refusal record",
            "then: a NEW certificate issued through the TC-6 gate over the "
            "adopted body and the C09 anchor class re-run on THAT body",
        ],
        "symmetric_clause": "the certified 10.037998 kg walking line is not "
                            "silently invalidated: its lineage and the "
                            "adopted-assembly lineage stay separate parallel "
                            "records; replacement of one with the other "
                            "remains a recorded decision that has NOT been "
                            "taken for runtime use",
    }


def main():
    check_registry_criteria()
    pins = {
        "b04_frames": pin(B04_PATH, B04_SHA256),
        "b05_ports": pin(B05_PATH, B05_SHA256),
        "b06_readiness_receipt": pin(B06_RECEIPT_PATH, B06_RECEIPT_SHA256),
        "producer_fit_43b599a7": pin(PRODUCER_PATH, PRODUCER_SHA256),
        "massreg_register": pin(MASSREG_PATH, MASSREG_SHA256),
        "ont_a02_decision_table": pin(DECISION_TABLE_PATH),
        "mat2_a02_report": pin(A02_REPORT_PATH),
        "readiness_closure": pin(READINESS_CLOSURE_PATH),
        "port_qualification": pin(PORT_QUALIFICATION_PATH),
        "runtime_contract": pin(RUNTIME_CONTRACT_PATH),
        "mass_audit_receipt": pin(MASS_AUDIT_RECEIPT_PATH,
                                  MASS_AUDIT_RECEIPT_SHA256),
        "osim_model": pin(OSIM_PATH, OSIM_SHA256),
        "rown04_fitting_receipt": pin(FITTING_RECEIPT_PATH),
        "rown04_fitting_receipts_md": pin(FITTING_RECEIPTS_MD_PATH),
        "rown05_measured_sources": pin(MEASURED_SOURCES_PATH),
        "rown05_admission_proposal": pin(ADMISSION_PROPOSAL_PATH),
    }
    b04 = json.loads(B04_PATH.read_text(encoding="utf-8"))
    producer = json.loads(PRODUCER_PATH.read_text(encoding="utf-8"))
    b05 = json.loads(B05_PATH.read_text(encoding="utf-8"))
    ports = b05["ports"]
    require(len(ports) == 8, "port_count:" + str(len(ports)))
    require(all(p["mechanical_qualification"] is False for p in ports),
            "port_state_drift: a port is not mechanically_unqualified")
    agreement = verify_cross_record_agreement(b04, producer)
    binding_rows = build_binding_rows(b04)
    prereg_sha = sha256_file(HERE / "PREREGISTRATION.md")

    frame_bindings = {
        "schema": "chimera.b07_frame_bindings.v1",
        "task_id": SHORT_ID,
        "card_id": TASK_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": prereg_sha,
        "authorization": {
            "authority": "OPERATIONAL_LEAD (Captain decision #4)",
            "message_id": AUTH_MESSAGE_ID,
            "items": ["(7) R-FRM-02 AUTHORIZED: ulna-edge correspondence "
                      "acceptance + packet-to-forest binding proceed as "
                      "attempt work.",
                      "(8) R-FRM-03 RULED: component/bond admission on the "
                      "closed cross-record agreement evidence half."],
        },
        "input_pins": pins,
        "r_frm_02": {
            "part_a_ulna_edge_correspondence": {
                "decision": "ACCEPTED by this attempt",
                "accepted_candidate": "U-STR (the sole provisional ulna "
                                      "candidate; U-ANA rejected, preserved "
                                      "as the failed alternative)",
                "basis": [
                    "architect decision 4 (ONT-A02 "
                    "ANATOMICAL_DECISION_TABLE.md addendum, pinned): U-STR "
                    "advances subject to (1) volar-side identification, "
                    "(2) palm-face identification, (3) primary radioulnar "
                    "evidence, then the B4 gate",
                    "MAT2-A02 reconciliation (pinned): the isolated U-STR "
                    "B4 diagnostic on the frozen candidate (U-STR + "
                    "O1-resolved roll): N3.gate_cells 10 PASS; in-model O1 "
                    "roll witnesses (ECU-P2, ANC-P2, TRIlat-P5) unanimous "
                    "NO-FLIP",
                    "Captain authorization item (7) lifts the acceptance "
                    "into this attempt's scope",
                ],
                "radius_supersession": {
                    "decision": "ACCEPTED as the correspondence's own "
                                "consequence",
                    "consequence": "uniform scale s 0.22170679566544982 -> "
                                   "0.20418868001006546 (-7.901478889180636 "
                                   "%); radius P re-anchors elbow_R -> "
                                   "ulna.P_d (+5.115804490107078 mm)",
                    "execution_status": "NOT executed here: the staged "
                                        "supersession record (ONT-A03) "
                                        "stays with its owning lane; no "
                                        "radius record is altered by this "
                                        "attempt",
                },
                "honesty_note": "the acceptance is a recorded decision on "
                                "sealed evidence; it alters no sealed "
                                "record and gates no port by itself (the "
                                "B05 frame rows stay blocked until the "
                                "lawful re-evaluation)",
            },
            "part_b_packet_to_forest_binding": {
                "decision": "AUTHORIZED AND RECORDED by this attempt",
                "binding_rows": binding_rows,
                "no_fusion_statement_carried":
                    b04["no_fusion_statement"],
                "check": "component root body == authored root frame body "
                         "verified from the pinned B04 bytes for all 4 "
                         "components (F4 binding_name_mismatch)",
            },
        },
        "r_frm_03": {
            "decision": "ADMITTED by this attempt on the closed agreement "
                        "evidence",
            "admitted": {
                "components": [c["component_id"] for c in b04["components"]],
                "component_count": len(b04["components"]),
                "bonds": {"count": len(b04["bonds"]),
                          "carried_status": "kinematically_preserved"},
                "containment_edges": len(b04["containment_edges"]),
            },
            "carried_unchanged": {
                "unresolved_bodies": EXPECTED_UNRESOLVED,
                "unresolved_count": len(EXPECTED_UNRESOLVED),
                "counted_mass_kg": agreement["counted_mass_kg"],
                "admission_statuses": "pelvis root_reference_frame_only; "
                                      "thorax/ulna/ulna_l geometry-mass "
                                      "unresolved; no mass is counted, "
                                      "promoted, or relabelled",
            },
            "agreement_evidence": agreement,
            "admission_scope": "placement assembly at B04 scope only; no "
                               "dynamics claim; no runtime claim",
        },
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B adoption_record.py"},
    }
    out_fb = HERE / "frame_bindings.json"
    out_fb.write_bytes(canonical(frame_bindings) + b"\n")

    adoption_digest = hashlib.sha256(canonical(
        sorted(pins.values(), key=lambda p: p["path"]))).hexdigest()
    adoption_record = {
        "schema": "chimera.b07_adoption_record.v1",
        "task_id": SHORT_ID,
        "card_id": TASK_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": prereg_sha,
        "governing_frame": {
            "captain_decision": "Captain decision #4 - "
                                "ADOPT-WITH-AUTHORIZATIONS (DEFER "
                                "msg-defer-b07-20260930 LIFTED)",
            "message_id": AUTH_MESSAGE_ID,
            "reconsideration_packet_sha256":
                "2cd5079ee40593370624e27e508b12765fc51aad3ccc175a966d036b949"
                "3db77",
            "card_starter_version": "v3",
        },
        "adoption_decision": {
            "kind": "ADOPT_WITH_AUTHORIZATIONS",
            "architect_named_reason": named_reason(),
            "decided_by": "recorded here per the Captain's plain words; "
                          "this attempt takes no rank beyond its "
                          "authorization package",
            "effective_scope": "the adopted assembly becomes the recorded "
                               "BINDING TARGET (TC-7) for the runtime "
                               "contract; no runtime body swap, no "
                               "certificate forgery, no readiness=true "
                               "claim, no port qualification",
        },
        "input_pins": pins,
        "authorization_package": authorization_items(),
        "readiness_closure_table": {
            "note": "closure EVIDENCE per row of the sealed B06 receipt "
                    "(14 rows); sealed statuses are never flipped here - "
                    "only a lawful re-evaluation inside a card flips a row",
            "assembly_readiness_claimed": False,
            "rows": per_row_table(),
            "honest_count": "4 satisfied rows untouched; of the 10 gaps: 3 "
                            "closed_by_work_with_receipt (R-OWN-02, "
                            "R-OWN-03, R-FRM-02), 3 closed_by_recorded_"
                            "ruling (R-MASS-02, R-MASS-04) or ruling with "
                            "work receipt (R-FRM-03), 2 refusal_stands "
                            "(R-MASS-03, R-PRT-01), 2 lane_evidence_"
                            "delivered (R-OWN-04, R-OWN-05; Amendment A1)",
        },
        "tc7_body_domain_bind": tc7_bind(adoption_digest),
        "tc12_rebind_record": tc12_rebind(),
        "massreg_citation": {
            "register_pin": pins["massreg_register"],
            "note": "the two-systems classification (scene vs "
                    "biological-reference) and the implied-BW "
                    "internally-inconsistent-female-band finding escalate to "
                    "the WALK TIER scene card per the sealed register; not "
                    "re-litigated and not consumed here",
        },
        "mass_law_carried": {
            "transported_uncounted_kg": 5.262978509953907,
            "pelvis_reference_kg": 11.777,
            "pelvis_class": "non-physical reference (root_ref_frame_"
                            "unscaled; producer excludes it from physical "
                            "admission)",
            "certified_walking_body_kg": 10.037998,
            "admitted_here": 0.0,
        },
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B adoption_record.py"},
    }
    out_ar = HERE / "adoption_record.json"
    out_ar.write_bytes(canonical(adoption_record) + b"\n")
    print("wrote", out_fb.name, "and", out_ar.name)
    print("binding rows:", len(binding_rows),
          "| agreement equal:", agreement["equal"],
          "| adoption pin digest:", adoption_digest[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
