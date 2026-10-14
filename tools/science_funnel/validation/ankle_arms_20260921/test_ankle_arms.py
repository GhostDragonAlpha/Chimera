"""The ankle-arms lane's falsifier tests.

Run from the repo root:
  python -B -m unittest tools.science_funnel.validation.ankle_arms_20260921.test_ankle_arms
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))

import derive_ankle_arms as D  # noqa: E402

RECEIPT = json.loads((HERE / "receipt.json").read_text(encoding="utf-8"))
PINS = RECEIPT["pre_registration"]["inputs_pinned"]


def sha_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def book_of() -> dict:
    return json.loads((HERE / "ankle_arms_book.json").read_text(encoding="utf-8"))


class TestTraceability(unittest.TestCase):
    """Falsifier (e): every number traces to a sha-verified input."""

    def test_01_all_pinned_inputs_verify(self):
        self.assertGreaterEqual(len(PINS), 8)
        for key, pin in PINS.items():
            p = REPO / pin["path"]
            self.assertTrue(p.exists(), f"{key}: {pin['path']} missing")
            self.assertEqual(sha_of(p), pin["sha256"], f"{key} sha drift")

    def test_02_imported_machinery_is_the_pinned_module(self):
        self.assertEqual(sha_of(Path(D.P.__file__)),
                         PINS["pulley_machinery"]["sha256"])

    def test_03_book_embeds_input_shas(self):
        book = book_of()
        for key, pin in PINS.items():
            self.assertEqual(book["inputs_sha_verified"][key], pin["sha256"], key)

    def test_04_si_rows_in_book_match_the_pinned_xlsx_reading(self):
        book = book_of()
        prior = RECEIPT["prior_reading"]["si2_anklefe_macaque_rows"]["rows_first_occurrence"]
        got = book["si2_comparison"]["rows"]
        self.assertEqual(set(got), set(prior))
        for m, p in prior.items():
            self.assertEqual(got[m]["si2_row"], p["row"], m)
            self.assertEqual(got[m]["si2_min"], p["min"], m)
            self.assertEqual(got[m]["si2_max"], p["max"], m)
            self.assertEqual(got[m]["jrange_deg"], list(p["jrange_deg"]), m)

    def test_05_cap_traces_model_si2_machinery_and_forces(self):
        book = book_of()
        v = book["cap_book"]["ankle_plantarflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]
        self.assertEqual(v["trace"]["arms"]["model"]["sha256"], PINS["model"]["sha256"])
        self.assertEqual(v["trace"]["arms"]["si2"]["sha256"], PINS["si2"]["sha256"])
        self.assertEqual(v["trace"]["arms"]["machinery"]["sha256"],
                         PINS["pulley_machinery"]["sha256"])
        self.assertEqual(v["trace"]["forces"]["oku"]["sha256"],
                         PINS["derived_numbers_snapshot"]["sha256"])
        self.assertEqual(v["trace"]["forces"]["record"]["sha256"],
                         PINS["muscle_path_geometry_snapshot"]["sha256"])

    def test_06_current_cap_and_demands_trace_to_pinned_snapshots(self):
        contract = json.loads((REPO / PINS["gait_contract_drives_snapshot"]["path"])
                              .read_text(encoding="utf-8"))
        caps = {d["coordinate"].rsplit("_", 1)[0]: d["torque_cap_N_m"]
                for d in contract["contract"]["drives"]}
        oku = json.loads((REPO / PINS["derived_numbers_snapshot"]["path"])
                         .read_text(encoding="utf-8"))
        t = oku["oku_before_alteration"]["torques"]["ankle"]
        book = book_of()
        self.assertEqual(book["cap_book"]["ankle_plantarflexion"]["current_cap_N_m"],
                         caps["ankle_dorsiflexion"])
        self.assertEqual(book["cap_book"]["ankle_plantarflexion"]["demand_peak_walk_N_m"],
                         abs(t["min_Nm"]))
        self.assertEqual(book["cap_book"]["ankle_dorsiflexion"]["demand_peak_walk_N_m"],
                         abs(t["max_Nm"]))


class TestRule0Gate(unittest.TestCase):
    """The k-gate at its third joint + the mining prior."""

    def test_07_k_gate_held_at_the_ankle(self):
        book = book_of()
        kg = book["si2_comparison"]["k_gate"]
        self.assertTrue(kg["k_ankle_inside_mtp_spread"])
        self.assertEqual(kg["k_used_for_S2"], 0.11975394)
        lo, hi = RECEIPT["prior_reading"]["k_gate_prior"]["mtp_class_spread"]
        self.assertGreaterEqual(kg["k_ankle_point_class_fitted"], lo)
        self.assertLessEqual(kg["k_ankle_point_class_fitted"], hi)

    def test_08_all_17_ankle_crossing_muscles_derived(self):
        book = book_of()
        self.assertEqual(len(book["arms"]), 17)
        self.assertEqual(set(book["arms"]),
                         set(book["si2_comparison"]["rows"]))
        self.assertIn("R_TP", book["arms"])
        self.assertIn("R_PL", book["arms"])

    def test_09_triceps_ordering_held(self):
        book = book_of()
        o = book["si2_comparison"]["triceps_ordering"]
        self.assertTrue(o["min_endpoint_held"])
        self.assertTrue(o["max_endpoint_held"])

    def test_10_wrap_activity_on_the_load_bearing_ankle_pulley(self):
        book = book_of()
        for m in D.MUST_ENGAGE:
            eng = book["arms"][m]["wrap_engaged_of_scanned"]["R_Ankle_Cylinder"]
            self.assertGreaterEqual(eng[0], 1, m)


class TestPreRegistration(unittest.TestCase):
    """Falsifier (c): the pre-registered signs/bands, read exactly as written."""

    def test_11_book_carries_the_receipts_pre_registration_unedited(self):
        book = book_of()
        self.assertEqual(book["falsifier_verdicts"]["pre_registered"]["summary"]
                         is not None, True)
        # the receipt itself still carries the pre-run blocks
        self.assertTrue(RECEIPT["pre_registration"]["written_before_first_arm_computation"])
        self.assertEqual(RECEIPT["pre_registered_delta_signs"]["ankle_plantarflexion"]
                         ["V1_S1"]["band_N_m"], [5.4, 6.9])

    def test_12_all_cap_sign_delta_sign_and_band_checks_held(self):
        book = book_of()
        v = book["falsifier_verdicts"]["pre_registered"]
        cap_checks = [k for k in v if k.startswith(("plantar_", "dorsal_",
                                                    "consumption_"))]
        self.assertGreaterEqual(len(cap_checks), 13)
        for k in cap_checks:
            self.assertNotEqual(v[k].get("verdict"), "FIRED", k)
        fired = v["summary"]["fired"]
        self.assertEqual(sorted(fired),
                         ["si_shape_sign_pattern", "si_shape_unit_verdict",
                          "si_shape_wrapped_rows_within_k_tolerance"])
        # the summary's all_held flag is consistent with its own fired list
        self.assertEqual(v["summary"]["all_held"], not fired)

    def test_13_si_shape_fires_are_exactly_the_three_recorded(self):
        book = book_of()
        v = book["falsifier_verdicts"]["pre_registered"]
        self.assertEqual(sorted(v["summary"]["fired"]),
                         ["si_shape_sign_pattern", "si_shape_unit_verdict",
                          "si_shape_wrapped_rows_within_k_tolerance"])
        # each fired entry carries its measured numbers (recorded, not tuned)
        for k in v["summary"]["fired"]:
            self.assertIn("measured", v[k], k)

    def test_14_fired_rows_are_exactly_the_ankle_cylinder_wrappers(self):
        book = book_of()
        fired = set(book["si2_miss_diagnosis"]["rows"])
        self.assertEqual(fired, {"R_FDL_TENDONII", "R_FDL_TENDONIII", "R_FDL_TENDONIV",
                                 "R_FHL", "R_TP"})
        # FDL V (ellipsoid) and every point-only row passed the k tolerance
        for m, r in book["si2_comparison"]["rows"].items():
            if m not in fired:
                self.assertTrue(r["endpoints"]["min"]["within_tol_k"], m)
                self.assertTrue(r["endpoints"]["max"]["within_tol_k"], m)

    def test_15_headline_caps_measured(self):
        book = book_of()
        p = book["cap_book"]["ankle_plantarflexion"]
        demand = p["demand_peak_walk_N_m"]
        v1 = p["V1_S1_oku_walk_peaks_deposit_arms"]
        # the unblocking claim: measured arms cover the walk demand the record
        # fell 3.7x short of; delta vs the doc cap NEGATIVE
        self.assertGreater(v1["cap_N_m"], demand)
        self.assertLess(v1["delta_N_m"], 0)
        self.assertLess(p["triceps_only_subenvelope_V1_S1"]["cap_N_m"], demand)
        # V2 (PROVISIONAL) > V1; S2 collapse
        self.assertGreater(p["V2_S1_pcsa_sigma_deposit_arms_PROVISIONAL"]["cap_N_m"],
                           v1["cap_N_m"])
        self.assertLess(p["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"], demand)
        self.assertLess(p["V2_S2_pcsa_sigma_si_matched_arms_PROVISIONAL"]["cap_N_m"],
                        demand)
        d = book["cap_book"]["ankle_dorsiflexion"]
        self.assertGreater(d["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
                           d["demand_peak_walk_N_m"])
        self.assertGreater(d["V2_S1_pcsa_sigma_deposit_arms_PROVISIONAL"]["cap_N_m"],
                           d["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"])

    def test_16_consumption_deltas_measured(self):
        book = book_of()
        sh = book["consumption_map"]["stance_hold_ankle_nodes"]
        self.assertEqual(sh["over_cap_nodes_before"], 0)
        self.assertEqual(sh["over_cap_nodes_after"], 6)
        h = book["consumption_map"]["height_law_ankle_chain_delta"]
        self.assertGreater(h["factor_V1_S1"], 0.73)
        self.assertLess(h["factor_V1_S1"], 0.94)
        self.assertGreater(h["factor_V2_S1_PROVISIONAL"], 1.0)
        ra = book["consumption_map"]["record_before_measured_after"]
        self.assertEqual(ra["record_straight_line_envelopes_N_m"]["V1"], 1.618881)
        self.assertGreater(ra["record_shortfall_vs_demand_x"]["V1"], 3.6)
        self.assertGreater(ra["measured_coverage_ratio_vs_demand"]["V1_S1"], 1.0)


class TestDeterminism(unittest.TestCase):
    """Falsifier (d): byte-identical derivations."""

    def test_17_in_process_rerun_byte_identical(self):
        b1 = D.derive()
        b2 = D.derive()
        self.assertEqual(D.canonical_json_bytes(b1), D.canonical_json_bytes(b2))

    def test_18_deliverable_matches_a_fresh_in_process_derivation(self):
        self.assertEqual(D.canonical_json_bytes(D.derive()),
                         (HERE / "ankle_arms_book.json").read_bytes())

    def test_19_subprocess_rerun_matches_deliverable_sha(self):
        book_sha = sha_of(HERE / "ankle_arms_book.json")
        with tempfile.NamedTemporaryFile(suffix=".json", dir=str(HERE),
                                         delete=False) as tf:
            tmp = Path(tf.name)
        try:
            r = subprocess.run([sys.executable, "-B", str(HERE / "derive_ankle_arms.py"),
                                "--out", str(tmp)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sha_of(tmp), book_sha)
        finally:
            tmp.unlink(missing_ok=True)


class TestBoundaries(unittest.TestCase):
    """Falsifier (f): the book, not the patch - no source changes outside the lane dir."""

    def test_20_git_status_clean_outside_the_lane_dir(self):
        r = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        outside = []
        for line in r.stdout.splitlines():
            path = line[3:].strip().strip('"').replace("\\", "/")
            if path.startswith("tools/science_funnel/validation/ankle_arms_20260921"):
                continue
            outside.append(line)
        self.assertEqual(outside, [], f"changes outside the lane dir: {outside}")


if __name__ == "__main__":
    unittest.main()
