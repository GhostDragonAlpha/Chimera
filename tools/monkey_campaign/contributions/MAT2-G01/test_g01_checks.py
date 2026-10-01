"""MAT2-G01 named checks (the executable done_when/falsifier battery).

Zero skips planned; every check executes. Run:
  python -B -m unittest test_g01_checks -v
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_feasibility as rf  # noqa: E402

CRITERIA = "c79a569f7259084e948d60058ccd850ccb671af30e61062c59295d152b9f0374"
ATTEMPT = "682fec627d7a413cb0fff77388436868"
BASE = "ced164735e5c2ff0a9662b04e7ffa28fd081f160"
READINGS = ("scene", "band_lo", "band_mid", "band_hi")


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class T01Identity(unittest.TestCase):
    def test_receipt_identity_fields(self):
        r = load("feasibility_receipt.json")
        self.assertEqual(r["schema"], "chimera.g01.feasibility.v1")
        self.assertEqual(r["card"], "MAT2-G01")
        self.assertEqual(r["task_id_short"], "G01")
        self.assertEqual(r["attempt_id"], ATTEMPT)
        self.assertEqual(r["criteria_sha256"], CRITERIA)
        self.assertEqual(r["base_commit"], BASE)
        self.assertEqual(r["done_when_verbatim"],
                         "Required force/moment support lies within reachable contacts "
                         "and actuator bounds for the declared trunk")

    def test_prereg_bytes_unchanged(self):
        r = load("feasibility_receipt.json")
        disk = hashlib.sha256((HERE / "PREREGISTRATION.md").read_bytes()).hexdigest()
        self.assertEqual(r["preregistration_sha256"], disk)
        self.assertEqual(r["preregistration_commit"], "023fd05f")


class T02Pins(unittest.TestCase):
    def test_all_pins_verified(self):
        r = load("feasibility_receipt.json")
        self.assertTrue(len(r["input_pins"]) >= 12)
        for p in r["input_pins"]:
            self.assertTrue(p["verified"], p["role"])
            self.assertEqual(len(p["sha256"]), 64)
            if p["kind"] == "repo":
                self.assertEqual(p["at_commit"], BASE)

    def test_pin_roles_complete(self):
        r = load("feasibility_receipt.json")
        roles = {p["role"] for p in r["input_pins"]}
        need = {"a09_grasp_package", "f03_checks", "f03_trunk_mesh",
                "w04_freeze_manifest", "d_massreg_register", "holodeck_catalog",
                "monkey_completion_map", "grasp_benchmark", "port_qualification",
                "repin_study", "w03_report", "c17_stiffness_sources"}
        self.assertTrue(need <= roles)


class T03CaseTableRecompute(unittest.TestCase):
    def test_case_rows_recompute_exactly(self):
        r = load("feasibility_receipt.json")
        d = r["derivation"]
        cap = d["capacity"]["capacity_N_std_g"]
        mu = d["capacity"]["mu_s"]
        n0 = d["capacity"]["press_operating_point_N"]
        w = d["body_readings"]
        rows = {(x["reading"], x["n_channels"]): x for x in d["case_table"]}
        self.assertEqual(len(rows), 12)
        for name in READINGS:
            for n in (1, 2, 3):
                row = rows[(name, n)]
                self.assertEqual(row["support_N"], n * cap)
                self.assertEqual(row["W_N"], w[name]["W_N"])
                self.assertEqual(row["friction_feasible"], n * cap >= w[name]["W_N"])
                self.assertEqual(row["required_press_per_channel_N"], w[name]["W_N"] / (n * mu))
                self.assertEqual(row["press_at_operating_point"],
                                 w[name]["W_N"] / (n * mu) <= n0)

    def test_weights_reproduce_register_literals(self):
        r = load("feasibility_receipt.json")
        d = r["derivation"]
        g = 9.80665
        self.assertEqual(d["body_readings"]["scene"]["mass_kg"], 10.037998)
        self.assertEqual(d["body_readings"]["scene"]["W_N"], 10.037998 * g)
        self.assertEqual(d["body_readings"]["band_lo"]["mass_kg"], 5.4)
        self.assertEqual(d["body_readings"]["band_mid"]["mass_kg"], 6.15)
        self.assertEqual(d["body_readings"]["band_hi"]["mass_kg"], 6.9)


class T04VerdictConsistency(unittest.TestCase):
    def test_detectors_green_on_clean_receipt(self):
        r = load("feasibility_receipt.json")
        self.assertEqual(rf._check_verdict_consistency(r), [])
        self.assertEqual(rf._check_claim_tracing(r), [])

    def test_frozen_summary_rows(self):
        r = load("feasibility_receipt.json")
        by_clause = {v["clause"]: v for v in r["derivation"]["verdicts"]}
        self.assertEqual(by_clause["single-channel static support (all readings)"]["verdict"],
                         "OUTSIDE")
        self.assertEqual(
            by_clause["reachable contacts (trunk-relative reach)"]["verdict"],
            "UNDECIDABLE-IN-RECORDS")
        self.assertEqual(by_clause["actuator-bounds qualification (any case)"]["verdict"],
                         "CONDITIONAL")
        self.assertEqual(by_clause["C20 vertical transfer (dynamic ascent)"]["verdict"],
                         "UNDECIDABLE-IN-RECORDS")
        self.assertEqual(r["derivation"]["overall"]["verdict"], "OUTSIDE-CONDITIONAL")

    def test_scene_split_rows(self):
        r = load("feasibility_receipt.json")
        by_clause = {v["clause"]: v for v in r["derivation"]["verdicts"]}
        self.assertEqual(by_clause["C19 case scene n=2 (scene system (register scene carve "
                                   "literal))"]["verdict"], "OUTSIDE")
        self.assertEqual(by_clause["C19 case scene n=3 (scene system (register scene carve "
                                   "literal))"]["verdict"], "WITHIN")
        self.assertEqual(by_clause["C19 case band_hi n=2 (biological-reference system, "
                                   "Turnquist band high)"]["verdict"], "WITHIN")


class T05NamedVariableGate(unittest.TestCase):
    def test_absent_slots_carry_no_synthetic_constant(self):
        r = load("feasibility_receipt.json")
        self.assertEqual(rf._check_named_variables(r), [])

    def test_variable_inventory(self):
        r = load("feasibility_receipt.json")
        names = set(r["derivation"]["named_variables"])
        self.assertEqual(names, {"x_reach", "x_press", "x_com", "x_trunk_strength",
                                 "x_share", "x_aperture", "x_sequence", "x_inertia",
                                 "x_trajectory", "x_losses"})
        for name, var in r["derivation"]["named_variables"].items():
            self.assertEqual(var["status"], "ABSENT", name)
            self.assertTrue(var["provenance_verbatim"], name)
            self.assertTrue(var["pins"], name)


class T06ClaimTracing(unittest.TestCase):
    def test_every_verdict_row_cites_pins(self):
        r = load("feasibility_receipt.json")
        self.assertEqual(rf._check_claim_tracing(r), [])
        known = {p["role"] for p in r["input_pins"]}
        for v in r["derivation"]["verdicts"]:
            self.assertTrue(set(v["citations"]) <= known, v["clause"])


class T07FalsifierReceipt(unittest.TestCase):
    def test_all_arms_bit_with_clean_controls(self):
        f = load("falsifier_receipt.json")
        self.assertTrue(f["all_caught"])
        self.assertTrue(f["clean_controls_all_green"])
        self.assertEqual(len(f["arms"]), 4)
        guards = {a["guard"] for a in f["arms"]}
        self.assertEqual(guards, {"g01_fb1_premature", "g01_fb2_premature",
                                  "g01_fb3_premature", "g01_fb4_premature"})
        for a in f["arms"]:
            self.assertTrue(a["clean_control"]["green"], a["arm"])
            self.assertTrue(a["caught"], a["arm"])


class T08Determinism(unittest.TestCase):
    def test_x2_byte_identity(self):
        a = (HERE / "feasibility_receipt.json").read_bytes()
        b = (HERE / "feasibility_receipt_rerun2.json").read_bytes()
        self.assertEqual(a, b)
        self.assertEqual(hashlib.sha256(a).hexdigest(),
                         "4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42")


class T09ReportLint(unittest.TestCase):
    def test_lint_passes_and_selftest_flags(self):
        for args in ([], ["--selftest"]):
            out = subprocess.run(
                [sys.executable, "-B", "lint_report_numbers.py"] + args,
                cwd=str(HERE), capture_output=True, text=True)
            self.assertEqual(out.returncode, 0,
                             f"lint {args} failed: {out.stdout}\n{out.stderr}")


class T10SpanWrap(unittest.TestCase):
    def test_span_and_wrap_recompute(self):
        r = load("feasibility_receipt.json")
        d = r["derivation"]
        tips = [e["position_m"] for e in r["declared_quantities"]["grasp_endpoints"]
                if e["role"] == "grasp_contact_endpoint"]
        best = max(math.dist(a, b) for i, a in enumerate(tips)
                   for b in tips[i + 1:])
        self.assertEqual(d["wrap_comparison"]["recorded_fingertip_span_m"], best)
        self.assertFalse(d["wrap_comparison"]["recorded_configuration_wraps"])
        self.assertEqual(d["geometry"]["declared_diameter_m"], 0.074)
        self.assertTrue(d["geometry"]["volume_consistency"])


class T11CapacityReproduction(unittest.TestCase):
    def test_capacity_bit_reproduces_from_operating_point(self):
        r = load("feasibility_receipt.json")
        cap = r["derivation"]["capacity"]
        s1 = r["declared_quantities"]["s1"]
        self.assertEqual(cap["mu_s"] * cap["jn_Ns"] / (r["declared_quantities"]["g_record"]
                                                       * cap["dt_s"]),
                         s1["grip_capacity_kg"])
        self.assertEqual(cap["press_operating_point_N"], 60.0)
        self.assertEqual(cap["capacity_N_record_g"], 36.0)
        self.assertEqual(cap["capacity_N_std_g"], 35.98770642201834)
        self.assertTrue(cap["benchmark_conversion_match"])


class T12DisclosureTables(unittest.TestCase):
    def test_pe_and_moment_templates_recompute(self):
        r = load("feasibility_receipt.json")
        d = r["derivation"]
        facet = d["moment_disclosures"]["s1_facet_height_m"]
        for name in READINGS:
            W = d["body_readings"][name]["W_N"]
            self.assertEqual(d["pe_line"][name]["full_trunk_J"], W * 1.158)
            self.assertEqual(d["moment_disclosures"]["root_moment_template_N_m"][name],
                             W * facet)
        self.assertEqual(d["moment_disclosures"]["demonstrated_case_external_moment"],
                         "zero (S1 static stick, S3 rest; rooted trunk)")


if __name__ == "__main__":
    unittest.main()
