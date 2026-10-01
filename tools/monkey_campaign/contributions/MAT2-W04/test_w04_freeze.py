#!/usr/bin/env python3
"""MAT2-W04 named-check suite — the executable done_when checks.

Runs under `python -B -m unittest discover -s . -p test_*.py` from the card
dir (the G12 gate re-runs it and parses executed/skipped). Every check reads
committed artifacts (or the sealed external pins) and refuses drift with named
codes. The falsifier bite arms (G1) each run their detector on the CLEAN
manifest first (premature guard <arm>_premature) and then on a scratch
tampered copy that MUST bite. Zero skips by design.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRIB = HERE.parent
CHECKOUT = CONTRIB.parents[2]
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
PASS3 = Path(r"E:/ChimeraWork/pass3-integ/repo")
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
WS = Path(r"E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W04"
          r"\d94341b2bd694bd2b725964040201398")
SCRATCH = WS / "scratch" / "suite"

TASK_ID = "W04"
CARD_ID = "MAT2-W04"
CRITERIA_SHA256 = ("cb66e8e9c24b6a838cb4e7b3dededef3c7c05fa72a77c9973a6ddb8b"
                   "7ff16e03")
CANDIDATE_BASE = "7ca4aceed57bd0471a185ea046436d74aa3b95a9"
BODY_DIGEST = "chimera.b07.adoption.240b457bc9612111173314b49f453b80"
DOMAIN_TAG = "material-assembly/buffy02-lineage"
OLD_COMPAT_KEY = ("9de019b7b9ef5e0ceff159558d8da726d678faafff28f12dab8d383b"
                  "97c21b40")
OBS_V2_SHA = ("e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0"
              "671c")
OBS_SECTION_SHA = ("3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3e"
                   "a1af63079")
TICK_COST_SHA = ("f87da957d62f3702d241d199ff417110a63af7ee4d264498a07208f10"
                 "d5f906e")

import make_freeze_manifest as FM  # noqa: E402 (the detectors under test)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_hex(b):
    return hashlib.sha256(b).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text("utf-8"))


MANIFEST = load("w04_freeze_manifest.json")
CERT = load("w04_certificate.json")
GATE = load("gate_reissue/w04_gate_receipt.json")
C09 = load("c09_reseal/c09_anchor_reseal.json")
CAPMAN = load("capture/capture_manifest.json")
CAPCTX = load("capture/capture_context.json")
CAPVAL = load("capture/capture_validation_receipt.json")


def cert_hash_of(cert):
    m = copy.deepcopy(cert)
    m.pop("cert_hash", None)
    return sha_hex(canonical(m))


def compat_key_of(relation):
    return sha_hex(canonical(relation))


def verify_chain(evidence):
    prev = sha_hex(("chain0:" + evidence["initial_snapshot_sha256"])
                   .encode("utf-8"))
    for ev in evidence["events"]:
        want = sha_hex(("%s:%s:%s:%s" % (prev, ev["tick"], ev["kind"],
                                         ev["state_sha256"]))
                       .encode("utf-8"))
        if want != ev["chain_sha256"]:
            return False
        prev = ev["chain_sha256"]
    return True


class W04FreezeIdentity(unittest.TestCase):
    def test_registry_identity(self):
        uri = "file:" + str(REGISTRY).replace("\\", "/") + "?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        try:
            row = con.execute("SELECT payload FROM state WHERE id='1'").fetchone()
        finally:
            con.close()
        card = json.loads(row[0])["kanban"]["cards"][CARD_ID]
        self.assertEqual(card["criteria_sha256"], CRITERIA_SHA256)
        task = card["spec"]["ontology_qualification"]["task"]
        self.assertEqual(task["verification_profile"]["id"], "anatomy")
        self.assertEqual(task["verification_profile"]["kind"],
                         "visible_static")
        self.assertEqual(MANIFEST["task_id"], TASK_ID)  # SHORT form

    def test_prereg_frozen_and_pinned(self):
        prereg_sha = sha_file(HERE / "PREREGISTRATION.md")
        self.assertEqual(MANIFEST["preregistration_sha256"], prereg_sha)
        self.assertEqual(C09["preregistration_sha256"], prereg_sha)
        self.assertEqual(GATE["preregistration_sha256"], prereg_sha)
        self.assertEqual(MANIFEST["candidate_base"], CANDIDATE_BASE)
        self.assertEqual(C09["candidate_base"], CANDIDATE_BASE)


class C09ResealChecks(unittest.TestCase):
    def test_anchor_class_exact(self):
        self.assertEqual(C09["schema"], "chimera.w04_c09_anchor_reseal.v1")
        self.assertEqual(C09["task_id"], TASK_ID)
        verdicts = {k: v["verdict"] for k, v in
                    C09["anchor_comparisons"].items()}
        self.assertEqual(len(verdicts), 9)
        self.assertTrue(all(v == "EXACT" for v in verdicts.values()), verdicts)
        self.assertEqual(verdicts["refused_tick"], "EXACT")
        self.assertEqual(verdicts["worst_ledger_J_rounded"], "EXACT")

    def test_c09_scope_and_lineage(self):
        self.assertIn("CERTIFIED 10.037998 kg walking line",
                      C09["object_replayed"])
        self.assertIn("NOT the adopted assembly", C09["object_replayed"])
        self.assertIn("STRUCTURALLY MISSING",
                      C09["adopted_assembly_anchor_status"])
        self.assertIn("BQ-1", C09["statement"])
        self.assertTrue(C09["runs"]["rerun_dump_identity"])

    def test_c09_scene_pin_resolves(self):
        scene_pin = C09["scene"]
        self.assertEqual(sha_file(scene_pin["path"]), scene_pin["sha256"])




class GateReissueChecks(unittest.TestCase):
    def test_certificate_self_identity(self):
        self.assertEqual(CERT["kind"], "policy_compat_certificate")
        self.assertEqual(CERT["cert_hash"], cert_hash_of(CERT))
        self.assertEqual(CERT["compat_key"], compat_key_of(CERT["relation"]))
        self.assertNotEqual(CERT["compat_key"], OLD_COMPAT_KEY)
        self.assertEqual(GATE["w04_cert_hash"], CERT["cert_hash"])
        self.assertEqual(GATE["w04_compat_key"], CERT["compat_key"])
        self.assertEqual(GATE["w04_certificate_sha256"],
                         sha_file(HERE / "w04_certificate.json"))

    def test_evidence_chain_and_monitors(self):
        ev = CERT["replay_evidence"]
        self.assertTrue(verify_chain(ev))
        self.assertTrue(ev["monitors"])
        for mon in ev["monitors"]:
            self.assertTrue(mon["pass"], mon["name"])

    def test_validator_and_deploy_decisions(self):
        self.assertEqual(GATE["validator"]["verdict"], "VALID")
        self.assertEqual(GATE["validator"]["violations"], [])
        d = GATE["deploy_checks"]
        self.assertEqual(d["matching_tuple"]["decision"], "ALLOW")
        self.assertEqual(d["foreign_build"]["decision"], "BLOCK")
        self.assertEqual(d["missing_certificate"]["decision"], "BLOCK")
        self.assertEqual(d["old_sealed_tuple_vs_w04_cert"]["decision"],
                         "BLOCK")
        self.assertEqual(d["w04_tuple_vs_old_sealed_cert"]["decision"],
                         "BLOCK")

    def test_injections_44_caught(self):
        inj = GATE["injections"]
        self.assertTrue(inj["all_caught"])
        self.assertEqual(inj["falsifier_summary"]["F1_silent_promotion"],
                         "CAUGHT")
        self.assertEqual(inj["falsifier_summary"]["F2_resume_drift"],
                         "CAUGHT")
        self.assertEqual(inj["falsifier_summary"]["F3_legacy_action_drift"],
                         "CAUGHT")
        names = ("I1_perturbed_state_hash", "I2_swapped_normalization_constant",
                 "I3_dropped_rng_from_restart_snapshot",
                 "I4_altered_action_mapping_entry")
        self.assertEqual(set(inj["injections"].keys()), set(names))
        for name in names:
            self.assertEqual(inj["injections"][name]["verdict"], "CAUGHT",
                             name)
        self.assertIn("rng_stream",
                      inj["injections"]["I3_dropped_rng_from_restart_snapshot"]
                      ["structural_refusal"])

    def test_clean_triple_byte_identical(self):
        triple = GATE["clean_triple"]
        self.assertTrue(triple["pass"])
        self.assertEqual(len(set(triple["bundle_sha256"])), 1)

    def test_body_domain_fill(self):
        bd = CERT["relation"]["body_domain"]
        self.assertEqual(bd["body_digest"], BODY_DIGEST)
        self.assertEqual(bd["domain_tag"], DOMAIN_TAG)
        self.assertIn("UNBOUND_dummy", bd["prior_state"])
        self.assertNotIn("UNBOUND_dummy", json.dumps(bd["body_digest"]))
        self.assertIn("NOT runtime-qualified", bd["qualification_state"])
        self.assertEqual(len(bd["rebind_prerequisites_still_open"]), 2)
        self.assertEqual(len(bd["mass_rulings"]), 3)
        self.assertIn("10.037998", bd["mass_line"])
        self.assertIn("0.0 kg", bd["mass_line"])

    def test_reusability_verdict_recorded(self):
        rv = GATE["reusability_verdict"]
        self.assertTrue(rv["verdict"].startswith("NOT REUSABLE"))
        self.assertIn("not a trained policy", rv["old_policy_bundle"])
        self.assertIn("NOT a trained policy",
                      MANIFEST["policy_artifact"]["p3_bundle_role"])
        self.assertIn("NO trained walking policy exists",
                      rv["trained_walking_policy"])

    def test_machinery_pins_sample(self):
        pins = GATE["machinery_pins"]
        self.assertGreaterEqual(len(pins), 30)
        import random
        rng = random.Random(20260930)
        for rel in rng.sample(sorted(pins), 4):
            self.assertEqual(sha_file(PASS3 / rel), pins[rel], rel)


class FreezeManifestChecks(unittest.TestCase):
    def test_schema_and_prereg(self):
        self.assertEqual(MANIFEST["schema"], "chimera.w04_training_manifest.v1")
        self.assertEqual(MANIFEST["profile_id"], "anatomy")
        FM.detect_body_domain(MANIFEST)  # FB1 clean control

    def test_dynamics_identity(self):
        dyn = MANIFEST["done_when_binding"]["exact_dynamics"]
        self.assertEqual(dyn["tick_hz"], 300)
        self.assertEqual(dyn["substeps"], 4)
        self.assertEqual(dyn["policy_hz"], 20)
        self.assertEqual(dyn["hold_ticks"], 15)
        pin = dyn["c09_reseal_receipt"]
        self.assertEqual(sha_file(Path(pin["path"])), pin["sha256"])

    def test_observation_binding(self):
        obs = MANIFEST["done_when_binding"]["observations_actions"]
        v2 = obs["observation_interface_v2"]
        sec = obs["normalization_section"]
        self.assertEqual(sha_file(Path(v2["path"])), v2["sha256"])
        self.assertEqual(v2["sha256"], OBS_V2_SHA)
        self.assertEqual(sha_file(Path(sec["path"])), sec["sha256"])
        self.assertEqual(sec["sha256"], OBS_SECTION_SHA)
        doc = json.loads(Path(v2["path"]).read_text("utf-8"))
        self.assertEqual(len(doc["fields"]), 80)
        self.assertEqual(doc["obs_schema_version"], 2)
        self.assertEqual(doc["legacy_dim"], 64)
        self.assertTrue(doc["privileged_forbidden"])
        self.assertIn("FIELDS[:64]", obs["interface"])

    def test_body_domain_slot(self):
        bd = MANIFEST["body_domain"]
        self.assertEqual(bd["clause"], "TC-7 (FC-1)")
        self.assertEqual(bd["bound_value"]["body_digest"], BODY_DIGEST)
        self.assertEqual(bd["bound_value"]["domain_tag"], DOMAIN_TAG)
        self.assertIn("adoption_record", bd)
        pin = bd["adoption_record"]
        self.assertEqual(sha_file(Path(pin["path"])), pin["sha256"])

    def test_mass_rulings_and_certified_line(self):
        rulings = {r["ruling"]: r["text"] for r in
                   MANIFEST["body_domain"]["mass_rulings"]}
        self.assertEqual(set(rulings),
                         {"R-MASS-04", "R-MASS-02", "R-MASS-03"})
        self.assertIn("5.262978509953907", rulings["R-MASS-04"])
        self.assertIn("11.777", rulings["R-MASS-04"])
        self.assertIn("NON-PHYSICAL", rulings["R-MASS-04"])
        self.assertIn("10.037998", rulings["R-MASS-03"])
        self.assertIn("UNCHANGED", rulings["R-MASS-03"])

    def test_ports_refusal(self):
        ports = MANIFEST["port_active_law_inputs"]
        self.assertEqual(ports["clause"], "TC-8 (FC-2; LT ruling BQ-5)")
        self.assertEqual(ports["status"], "UNQUALIFIED_BY_HONEST_REFUSAL")
        self.assertEqual(ports["ports_qualified"], 0)
        self.assertEqual(ports["ports_total"], 8)
        self.assertEqual(ports["measured_inputs_admitted"], [])
        identities = [r["identity"] for r in ports["refusals"]]
        self.assertIn("B05 0/8", identities)
        self.assertIn("R-OWN-05", identities)
        self.assertIn("R-PRT-01", identities)
        for ref in ports["refusals"]:
            self.assertEqual(sha_file(Path(ref["evidence"]["path"])),
                             ref["evidence"]["sha256"], ref["identity"])
        FM.detect_ports(MANIFEST)  # FB2 clean control

    def test_policy_slot_explicitly_unresolved(self):
        pol = MANIFEST["policy_artifact"]
        self.assertEqual(pol["status"], "EXPLICITLY_UNRESOLVED")
        self.assertFalse(pol["trained_walking_policy_exists"])
        self.assertIn("NOT a trained policy", pol["p3_bundle_role"])
        self.assertIn("5fb2b785", pol["p3_bundle_role"])
        rv = pol["reusability_verdict"]
        self.assertEqual(rv["instrument_executed"], True)
        self.assertEqual(sha_file(Path(rv["instrument_receipt"]["path"])),
                         rv["instrument_receipt"]["sha256"])
        FM.detect_policy_slot(MANIFEST)  # FB3 clean control

    def test_seeds_runbook_slot_shape(self):
        sr = MANIFEST["seeds_runbook_slot"]
        self.assertIn("FROZEN_SLOT_SHAPE", sr["slot_status"])
        self.assertIn("W05", sr["slot_status"])
        for field in ("seeds", "runbook_id", "acceptance_criteria"):
            self.assertIsNone(sr["declared_fields"][field]["value"])
            self.assertIn("W05", sr["declared_fields"][field]["owner"])
        laws = {lid["identity"] for lid in sr["governing_laws"]}
        self.assertEqual(laws, {"K01", "P04"})
        FM.detect_seeds_runbook(MANIFEST)  # FB4 clean control

    def test_claim_class_offline_trace_only(self):
        rp = MANIFEST["runtime_profile"]
        self.assertEqual(rp["claim_class"],
                         "offline/trace qualification at the 300 Hz tick "
                         "only; interactive real-time 300 Hz NOT satisfied")
        self.assertEqual(rp["interactive_realtime_300hz"], "NOT SATISFIED")
        cost = rp["cost_gap_citation"]
        self.assertEqual(cost["receipt_sha256"], TICK_COST_SHA)
        self.assertEqual(sha_file(Path(cost["receipt"]["path"])),
                         TICK_COST_SHA)
        self.assertEqual(cost["budget_ms_per_tick"], 3.333)
        self.assertEqual(cost["over_budget_x"], [13.7, 6.7])
        self.assertEqual(cost["verdict"], "COST-GAP FIRED (clause F1)")
        self.assertEqual(rp["training_throughput_bound_to"],
                         "P04 reservation discipline")
        FM.detect_claim_class(MANIFEST)  # FB5 clean control

    def test_actuation_never_transfers(self):
        act = MANIFEST["actuation_interface"]
        self.assertIn("RE_DECLARE_PENDING", act["status"])
        key = "certified_scene_caps_never_transfer"
        self.assertIn(key, act)
        self.assertIn("11.2125", act[key][0])
        self.assertIn("CERTIFIED 10.038 kg scene's drives only", act[key][0])

    def test_explicitly_unresolved_inventory(self):
        inv = MANIFEST["explicitly_unresolved_inventory"]
        joined = " | ".join(inv)
        for item in ("trained walking policy", "interactive playable walk",
                     "judgement_stride.json", "CT distribution",
                     "CoT denominator"):
            self.assertIn(item, joined)


class CaptureChecks(unittest.TestCase):
    def test_validator_structurally_valid(self):
        self.assertTrue(CAPVAL["structurally_valid"])
        self.assertEqual(CAPVAL["mode"], "CAMERA_METADATA_STRUCTURE_ONLY")
        self.assertFalse(CAPVAL["visual_acceptance"])
        self.assertEqual(CAPVAL["profile_id"], "anatomy")

    def test_one_state_hash_across_rows(self):
        hashes = {r["state_binding"]["sha256"] for r in CAPMAN["views"]}
        self.assertEqual(len(hashes), 1)
        (only,) = hashes
        self.assertEqual(only, MANIFEST["state_composite_sha256"])
        FM.detect_state_hashes({"views": CAPMAN["views"]})  # FB6 clean control

    def test_camera_required_fields_complete(self):
        profile = load_profile_from_registry()
        mapping = {"vertical_fov_or_orthographic_span":
                   ("orthographic_span",)}
        for row in CAPMAN["views"]:
            cam = row["camera"]
            for field in profile["camera_required_fields"]:
                keys = mapping.get(field, (field,))
                self.assertTrue(any(k in cam for k in keys),
                                (row["view_id"], field))

    def test_clean_pairs_and_layers(self):
        profile = load_profile_from_registry()
        pairs = {}
        layers_seen = set()
        for row in CAPMAN["views"]:
            pairs.setdefault(row["view_id"], []).append(row["mode"])
            if row["mode"] == "diagnostic":
                layers_seen.update(row["visibility"]["layers"])
            else:
                self.assertEqual(row["visibility"]["layers"], [])
                self.assertEqual(row["visibility"]["label_ids"], [])
        for view_id in profile["views"]:
            self.assertEqual(sorted(pairs[view_id]),
                             ["clean", "diagnostic"], view_id)
        for layer in profile["diagnostic_layers"]:
            self.assertIn(layer, layers_seen, layer)

    def test_capture_identity_concat(self):
        concat = hashlib.sha256()
        files = CAPMAN["sheet_layout"]["frame_files"]
        for name in sorted(files):
            concat.update((HERE / "capture" / name).read_bytes())
        self.assertEqual(concat.hexdigest(), CAPMAN["capture_sha256"])
        self.assertEqual(CAPCTX["capture_sha256"], CAPMAN["capture_sha256"])
        self.assertEqual(CAPCTX["subject_sha256"], CAPMAN["subject_sha256"])
        for name, sha in files.items():
            self.assertEqual(sha_file(HERE / "capture" / name), sha)

    def test_camera_numeric_consistency(self):
        import math
        for row in CAPMAN["views"]:
            for s in row["camera"]["samples"]:
                self.assertAlmostEqual(
                    s["distance_to_target"],
                    math.dist(s["position"], s["target"]), places=9)
                self.assertAlmostEqual(math.hypot(*s["orientation"]), 1.0,
                                       places=9)


class FalsifierBiteArms(unittest.TestCase):
    """G1: every arm passes its clean control first (premature guard), then
    bites a tampered copy. Tampered copies live in the attempt scratch."""

    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)

    def bite(self, arm, mutate, detector, expected_code):
        clean = copy.deepcopy(MANIFEST)
        try:
            detector(clean)
        except Exception as exc:  # pragma: no cover - premature guard
            self.fail(arm + "_premature: detector fired on the CLEAN manifest: "
                      + repr(exc))
        tampered = copy.deepcopy(MANIFEST)
        mutate(tampered)
        (SCRATCH / ("tampered_%s.json" % arm)).write_bytes(canonical(tampered))
        with self.assertRaises(FM.Refusal) as ctx:
            detector(tampered)
        code = getattr(ctx.exception, "code", str(ctx.exception))
        self.assertTrue(code.startswith(expected_code), (arm, code))
        self.assertNotIn("premature", code, arm)

    def test_fb1_body_domain_silent_reuse_bites(self):
        def mutate(m):
            m["body_domain"]["bound_value"]["body_digest"] = (
                "UNBOUND_dummy (P3 manifest body: status UNBOUND)")
            m["body_domain"]["bound_value"]["domain_tag"] = (
                "cpu-walk-scene/hind-pad-surrogate")
        self.bite("FB1", mutate, FM.detect_body_domain,
                  "w04_manifest_body_domain_unbound")

    def test_fb2_invented_port_constant_bites(self):
        def mutate(m):
            m["port_active_law_inputs"]["kappa_areal_n_m3"] = 100000.0
        self.bite("FB2", mutate, FM.detect_ports,
                  "w04_port_invented_constant")

    def test_fb3_trained_policy_claim_bites(self):
        def mutate(m):
            m["policy_artifact"]["status"] = "TRAINED_POLICY_BOUND"
        self.bite("FB3", mutate, FM.detect_policy_slot,
                  "w04_policy_trained_claim")

    def test_fb4_seed_value_encroachment_bites(self):
        def mutate(m):
            m["seeds_runbook_slot"]["declared_fields"]["seeds"]["value"] = [
                11, 22, 33]
        self.bite("FB4", mutate, FM.detect_seeds_runbook,
                  "w04_seed_value_encroachment")

    def test_fb5_realtime_claim_bites(self):
        def mutate(m):
            m["runtime_profile"]["interactive_realtime_300hz"] = "SATISFIED"
        self.bite("FB5", mutate, FM.detect_claim_class, "w04_realtime_claim")

    def test_fb6_toggle_state_hash_move_bites(self):
        def mutate(m):
            m["views"][0]["state_binding"]["sha256"] = "0" * 64
        self.bite("FB6", mutate, FM.detect_state_hashes,
                  "w04_toggle_state_hash_move")


def load_profile_from_registry():
    uri = "file:" + str(REGISTRY).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        row = con.execute("SELECT payload FROM state WHERE id='1'").fetchone()
    finally:
        con.close()
    card = json.loads(row[0])["kanban"]["cards"][CARD_ID]
    return card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]


if __name__ == "__main__":
    unittest.main()
