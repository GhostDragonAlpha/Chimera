"""The hind-torque-book lane's falsifier tests (17 checks).

Run from the repo root:
  python -B -m unittest tools.science_funnel.validation.hind_torque_book_20260921.test_hind_torque_book
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

import derive_hind_torque_book as dh  # noqa: E402

RECEIPT = json.loads((HERE / "receipt.json").read_text(encoding="utf-8"))


def sha_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestTraceability(unittest.TestCase):
    """Falsifier (c): every number traces to a sha-verified input."""

    def test_01_all_pinned_inputs_verify(self):
        pins = RECEIPT["pre_registration"]["inputs_pinned"]
        self.assertGreaterEqual(len(pins), 7)
        for key, pin in pins.items():
            p = HERE / pin["path"] if pin["path"].startswith("inputs/") else REPO / pin["path"]
            self.assertTrue(p.exists(), f"{key}: {pin['path']} missing")
            self.assertEqual(sha_of(p), pin["sha256"], f"{key} sha drift")

    def test_02_pulley_deliverable_matches_pulley_lane_receipt(self):
        lane = json.loads((REPO / "tools/science_funnel/validation/pulley_rederivation_20260920/receipt.json")
                          .read_text(encoding="utf-8"))
        pinned = lane["measured"]["deliverable"]["sha256"]
        got = sha_of(REPO / "tools/science_funnel/validation/pulley_rederivation_20260920/pulley_arms_derivation.json")
        self.assertEqual(got, pinned)

    def test_03_book_embeds_input_shas(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        pins = RECEIPT["pre_registration"]["inputs_pinned"]
        for key, pin in pins.items():
            self.assertEqual(book["inputs_sha_verified"][key], pin["sha256"], key)

    def test_04_knee_cap_traces_to_arm_curves_and_okus(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        v = book["rederivation"]["knee_extension"]["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]
        self.assertEqual(v["trace"]["arms"]["sha256"],
                         RECEIPT["pre_registration"]["inputs_pinned"]["pulley_arms_derivation"]["sha256"])
        self.assertEqual(v["trace"]["forces"]["sha256"],
                         RECEIPT["pre_registration"]["inputs_pinned"]["derived_numbers_snapshot"]["sha256"])

    def test_05_mp_cap_traces_to_arm_curves_and_force_record(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        v = book["rederivation"]["mtp_flexion"]["variants"]["V2_S1_pcsa_sigma_deposit_arms"]
        self.assertEqual(v["trace"]["arms"]["sha256"],
                         RECEIPT["pre_registration"]["inputs_pinned"]["pulley_arms_derivation"]["sha256"])
        self.assertEqual(v["trace"]["forces"]["sha256"],
                         RECEIPT["pre_registration"]["inputs_pinned"]["muscle_path_geometry_snapshot"]["sha256"])

    def test_06_current_caps_trace_to_the_graph_contract(self):
        contract = json.loads((HERE / "inputs/gait_contract_drives.snapshot.json").read_text(encoding="utf-8"))
        caps = {d["coordinate"].rsplit("_", 1)[0]: d["torque_cap_N_m"] for d in contract["contract"]["drives"]}
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        self.assertEqual(book["rederivation"]["knee_extension"]["current_cap_N_m"], caps["knee_extension"])
        self.assertEqual(book["rederivation"]["mtp_flexion"]["current_cap_N_m"], caps["MP_dorsiflexion"])
        self.assertEqual(book["rederivation"]["ankle_context"]["current_cap_N_m"], caps["ankle_dorsiflexion"])


class TestAuditCompleteness(unittest.TestCase):
    """Falsifier (e): no cap unaccounted."""

    def test_07_audit_complete_flag(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        self.assertTrue(book["audit"]["completeness"]["complete"])
        self.assertEqual(book["audit"]["completeness"]["missing"], [])

    def test_08_required_counts(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        c = book["audit"]["completeness"]
        self.assertEqual(c["required_hind_numbers"], 8 * 5)
        self.assertEqual(c["required_fore_numbers"], 4 * 5)

    def test_09_audit_names_the_live_hind_caps(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        idx = {e["number"]: e for e in book["audit"]["entries"]}
        for coord, cap in (("hip_flexion_left", 11.2125), ("knee_extension_left", 6.6375),
                           ("ankle_dorsiflexion_left", 7.4), ("MP_dorsiflexion_left", 0.8875)):
            e = idx[f"drives.{coord}.torque_cap_N_m"]
            self.assertEqual(e["value"], cap)
            self.assertIn("1.25", " ".join(e["chain"]))

    def test_10_audit_names_the_rounding_split_and_falsified_amendment(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        s = json.dumps(book["audit"]["entries"])
        self.assertIn("ROUNDING SPLIT", s)
        self.assertIn("source_peaks_v1_RESTORED", s)
        self.assertIn("FALSIFIED", s)


class TestPreRegistration(unittest.TestCase):
    """Falsifier (a)/(b): pre-registered delta signs and bands."""

    def test_11_all_pre_registered_checks_held(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        v = book["falsifier_verdicts"]["pre_registered_delta_signs_and_bands"]
        self.assertTrue(v["summary"]["all_held"], v["summary"]["fired"])
        self.assertEqual(v["summary"]["fired"], [])

    def test_12_book_carries_the_receipts_bands_unedited(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        r = book["rederivation"]
        self.assertEqual(r["knee_extension"]["pre_registered"],
                         RECEIPT["pre_registered_delta_signs"]["knee_extension"])
        self.assertEqual(r["mtp_flexion"]["pre_registered"],
                         RECEIPT["pre_registered_delta_signs"]["MP_dorsiflexion_mtp_flexion"])
        self.assertEqual(r["ankle_context"]["pre_registered"],
                         RECEIPT["pre_registered_delta_signs"]["ankle_context_only"])

    def test_13_headline_deltas_measured(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        knee = book["rederivation"]["knee_extension"]["variants"]
        mp = book["rederivation"]["mtp_flexion"]["variants"]
        # V1_S1: measured forces x measured deposit arms EXCEED the doc caps
        self.assertGreater(knee["V1_S1_oku_walk_peaks_deposit_arms"]["ratio_vs_current"], 1.0)
        self.assertGreater(mp["V1_S1_oku_walk_peaks_deposit_arms_equal_split"]["ratio_vs_current"], 1.0)
        # S2 collapse: the k divergence gates consumption
        self.assertLess(knee["V1_S2_oku_peaks_si_matched_arms"]["ratio_vs_current"], 0.30)
        self.assertLess(mp["V1_S2_oku_peaks_si_matched_arms"]["ratio_vs_current"], 0.30)
        # V2 (PROVISIONAL) > V1 in both directions
        self.assertGreater(knee["V2_S1_pcsa_sigma_deposit_arms"]["cap_N_m"],
                           knee["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"])
        self.assertGreater(mp["V2_S1_pcsa_sigma_deposit_arms"]["cap_N_m"],
                           mp["V1_S1_oku_walk_peaks_deposit_arms_equal_split"]["cap_N_m"])

    def test_14_ankle_blocked_and_below_demand(self):
        book = json.loads((HERE / "hind_torque_book.json").read_text(encoding="utf-8"))
        ank = book["rederivation"]["ankle_context"]
        self.assertIn("BLOCKED", ank["verdict"])
        e = ank["context_envelopes"]
        self.assertLess(e["V1_oku_plantar_N_m"], e["oku_measured_walk_demand_peak_N_m"])
        self.assertLess(e["V2_pcsa_sigma_plantar_N_m"], e["oku_measured_walk_demand_peak_N_m"])


class TestDeterminism(unittest.TestCase):
    """Falsifier (d): two full derivations byte-identical."""

    def test_15_in_process_rerun_byte_identical(self):
        b1 = dh.derive()
        b2 = dh.derive()
        self.assertEqual(dh.canonical_json_bytes(b1), dh.canonical_json_bytes(b2))

    def test_16_subprocess_rerun_matches_deliverable_sha(self):
        book_sha = sha_of(HERE / "hind_torque_book.json")
        with tempfile.NamedTemporaryFile(suffix=".json", dir=str(HERE), delete=False) as tf:
            tmp = Path(tf.name)
        try:
            r = subprocess.run([sys.executable, "-B", str(HERE / "derive_hind_torque_book.py"),
                                "--out", str(tmp)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sha_of(tmp), book_sha)
        finally:
            tmp.unlink(missing_ok=True)


class TestBoundaries(unittest.TestCase):
    """Falsifier (f): the book, not the patch - no source changes outside the lane dir."""

    def test_17_git_status_clean_outside_the_lane_dir(self):
        r = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        outside = []
        for line in r.stdout.splitlines():
            path = line[3:].strip().strip('"').replace("\\", "/")
            if path.startswith("tools/science_funnel/validation/hind_torque_book_20260921"):
                continue
            outside.append(line)
        self.assertEqual(outside, [], f"changes outside the lane dir: {outside}")


if __name__ == "__main__":
    unittest.main()
