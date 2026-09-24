"""W3 failing-first regressions for the M13 reader repair.

FAILING-FIRST: the T-row tests (frozen conversion table, PREREGISTRATION.md)
FAILED against the unedited reader (uncaught numpy ValueError/TypeError,
CLI exit 1 — the B7-M13 finding); they demand the frozen named refusals.
The K-row tests pin every already-named refusal so the repair cannot move
one. Guard tests prove unexpected exceptions still propagate uncaught.
Golden tests prove valid output stays byte-identical (against the pre-edit
capture AND against B3's/M07's independent historical receipts).

Run: python tests/test_w3_reader_m13.py        (from impl/W3_reader_m13/)
     python -m unittest discover -s tests -t . also works.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
IMPL = HERE.parent
REPO = IMPL.parents[1].parent
TOOLS = REPO / "tools"
READER_PATH = TOOLS / "material_volume_body_export_reader.py"
BEFORE = IMPL / "receipts" / "before"
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(IMPL / "work"))
sys.path.insert(0, str(TOOLS))

import material_volume_body_export_reader as reader  # noqa: E402
from make_fixtures import READ_IN_PLACE  # noqa: E402

TENSOR_DETAIL = ("body_groups[1] mass_properties.inertia_tensor_about_com.value "
                 "is malformed: not a rectangular numeric array")
CENTER_DETAIL = ("body_groups[1] mass_properties.center_of_mass.value "
                 "is malformed: not a numeric array of length 3")
MASS_DETAIL = ("body_groups[1] mass_properties.mass.value "
               "is malformed: not a finite JSON number")

# Prereg T-rows: crash class -> frozen refusal. (fixture, expected stderr line)
CRASH_CASES = [
    ("b7_corrupt_m13", READ_IN_PLACE["b7_corrupt_m13"], TENSOR_DETAIL),
    ("t01_ragged_truncated_row", FIXTURES / "t01_ragged_truncated_row.json", TENSOR_DETAIL),
    ("t02_deep_ragged", FIXTURES / "t02_deep_ragged.json", TENSOR_DETAIL),
    ("t03_rect_string_entry", FIXTURES / "t03_rect_string_entry.json", TENSOR_DETAIL),
    ("t04_dict_value", FIXTURES / "t04_dict_value.json", TENSOR_DETAIL),
    ("t05_string_scalar", FIXTURES / "t05_string_scalar.json", TENSOR_DETAIL),
    ("t06_center_ragged", FIXTURES / "t06_center_ragged.json", CENTER_DETAIL),
    ("t07_center_string_entry", FIXTURES / "t07_center_string_entry.json", CENTER_DETAIL),
    ("t08_center_dict_value", FIXTURES / "t08_center_dict_value.json", CENTER_DETAIL),
    ("t09_center_string_scalar", FIXTURES / "t09_center_string_scalar.json", CENTER_DETAIL),
    ("t10_mass_null", FIXTURES / "t10_mass_null.json", MASS_DETAIL),
    ("t11_mass_string_bad", FIXTURES / "t11_mass_string_bad.json", MASS_DETAIL),
    ("t12_mass_list", FIXTURES / "t12_mass_list.json", MASS_DETAIL),
    ("t13_mass_dict", FIXTURES / "t13_mass_dict.json", MASS_DETAIL),
]

# Prereg K-rows: already-named refusals that must stay byte-identical.
KEPT_CASES = [
    ("k1_wrong_shape_2x2", FIXTURES / "k1_wrong_shape_2x2.json",
     "bad_export_report: body_groups[1] has invalid numeric properties"),
    ("k2_center_1x3", FIXTURES / "k2_center_1x3.json",
     "bad_export_report: body_groups[1] has invalid numeric properties"),
    ("k3_none_entries", FIXTURES / "k3_none_entries.json",
     "bad_export_report: body_groups[1] has invalid numeric properties"),
    ("k4_scalar_tensor", FIXTURES / "k4_scalar_tensor.json",
     "bad_export_report: body_groups[1] has invalid numeric properties"),
    ("k5_combo_wrongshape_badmass", FIXTURES / "k5_combo_wrongshape_badmass.json",
     "bad_export_report: body_groups[1] has invalid numeric properties"),
]

# Valid reports: reader must exit 0 with byte-identical stdout (pre-edit capture
# + independent historical receipts where they exist).
GOLDEN_CASES = [
    ("b7_valid_report", READ_IN_PLACE["b7_valid_report"], None),
    ("shipped_example_report", READ_IN_PLACE["shipped_example_report"], None),
    ("b3_rotcoupon_report", READ_IN_PLACE["b3_rotcoupon_report"],
     READ_IN_PLACE["b3_rotcoupon_summary_golden"]),
    ("b3_shipped_report", READ_IN_PLACE["b3_shipped_report"],
     READ_IN_PLACE["b3_shipped_summary_golden"]),
    ("m07_c1_report", READ_IN_PLACE["m07_c1_report"], None),
    ("m07_c2_report", READ_IN_PLACE["m07_c2_report"], None),
    ("m07_c3_report", READ_IN_PLACE["m07_c3_report"], None),
    ("m07_c4_report", READ_IN_PLACE["m07_c4_report"], None),
]

M07_PROBE_RECEIPTS = [
    ("probe-r1-reader", READ_IN_PLACE["m07_c1_report"]),
    ("probe-r2-reader", READ_IN_PLACE["m07_c3_report"]),
    ("probe-r3-reader", READ_IN_PLACE["m07_c4_report"]),
    ("probe-r4-reader", READ_IN_PLACE["m07_c2_report"]),
]


def run_cli(report_path):
    return subprocess.run([sys.executable, str(READER_PATH), str(report_path)],
                          cwd=str(REPO), capture_output=True)


def stderr_text(proc):
    """Decode stderr, normalizing the Windows text-mode \\r\\n artifact."""
    return proc.stderr.decode("utf-8").replace("\r\n", "\n")


class TestFrozenConversions(unittest.TestCase):
    """Prereg T-rows: the malformed-numeric class becomes named, located refusals."""

    def test_each_crash_shape_now_refused_with_frozen_line_and_exit_2(self):
        for name, path, detail in CRASH_CASES:
            with self.subTest(case=name):
                proc = run_cli(path)
                self.assertEqual(proc.returncode, 2, stderr_text(proc))
                self.assertEqual(proc.stdout, b"")
                self.assertEqual(stderr_text(proc), f"bad_export_report: {detail}\n")

    def test_conversions_raise_reader_refusal_type_in_process(self):
        for name, path, detail in CRASH_CASES:
            with self.subTest(case=name):
                report = json.loads(path.read_text(encoding="utf-8"))
                with self.assertRaises(ValueError) as caught:
                    reader.summarize_export_report(report)
                self.assertIsInstance(caught.exception, reader.exporter.ExportInputError)
                error = caught.exception
                self.assertEqual((error.reason, error.detail),
                                 ("bad_export_report", detail))


class TestKeptNamedRefusals(unittest.TestCase):
    """Prereg K-rows: already-named behavior pinned byte-for-byte (before vs after)."""

    def test_each_control_refusal_is_unchanged_from_before_capture(self):
        before = json.loads((BEFORE / "manifest.json").read_text(encoding="utf-8"))
        for name, path, line in KEPT_CASES:
            with self.subTest(case=name):
                proc = run_cli(path)
                record = before["cases"][name]
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.returncode, record["exit"])
                self.assertEqual(stderr_text(proc), line + "\n")
                self.assertEqual(
                    hashlib.sha256(proc.stderr).hexdigest(), record["stderr_sha256"],
                    f"{name}: refusal bytes changed vs pre-edit capture")

    def test_k6_m07_r5_blocked_group_refusal_unchanged(self):
        # Pinned against M07's own historical receipt bytes, not just W3's capture.
        receipts = REPO / "material_volume_campaign/agents/M07_ownership/receipts"
        proc = run_cli(READ_IN_PLACE["m07_r5_tampered"])
        self.assertEqual(proc.returncode,
                         int((receipts / "probe-r5-reader.exit").read_text().strip()))
        self.assertEqual(proc.stderr,
                         (receipts / "probe-r5-reader.stderr").read_bytes())


class TestUnexpectedStillUnexpected(unittest.TestCase):
    """Guard: only (TypeError, ValueError) at the three coercion sites is converted."""

    VALID = READ_IN_PLACE["b7_valid_report"]

    def test_injected_runtime_error_at_tensor_coercion_propagates(self):
        report = json.loads(self.VALID.read_text(encoding="utf-8"))
        with mock.patch.object(reader.np, "asarray",
                               side_effect=RuntimeError("injected programming error")):
            with self.assertRaises(RuntimeError):
                reader.summarize_export_report(report)

    def test_injected_runtime_error_at_finite_check_propagates(self):
        report = json.loads(self.VALID.read_text(encoding="utf-8"))
        with mock.patch.object(reader.math, "isfinite",
                               side_effect=RuntimeError("injected programming error")):
            with self.assertRaises(RuntimeError):
                reader.summarize_export_report(report)

    def test_injected_runtime_error_is_not_masked_into_a_refusal_type(self):
        report = json.loads(self.VALID.read_text(encoding="utf-8"))
        try:
            with mock.patch.object(reader.np, "asarray",
                                   side_effect=RuntimeError("injected")):
                reader.summarize_export_report(report)
        except RuntimeError:
            pass
        else:
            self.fail("RuntimeError was swallowed or converted")
        # The CLI must still crash loudly (traceback, exit 1), never exit 2.
        with mock.patch.object(reader.np, "asarray", side_effect=RuntimeError("injected")):
            with self.assertRaises(RuntimeError):
                reader.main([str(self.VALID)])

    def test_reader_source_has_no_blanket_catch(self):
        source = READER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("except:", source)
        self.assertNotIn("except Exception", source)
        self.assertNotIn("except BaseException", source)
        # Exactly the two preregistered narrow coercion helpers covering the
        # three sites (_as_float_array: both np.asarray sites; _as_number: mass).
        self.assertEqual(source.count("except (TypeError, ValueError)"), 2,
                         "the repair must add only the two narrow coercion catches")


class TestValidOutputGolden(unittest.TestCase):
    """Valid reports: exit 0, stdout byte-identical to pre-edit AND to history."""

    def _golden_digest(self, name):
        record = json.loads((BEFORE / "manifest.json").read_text(encoding="utf-8"))
        return record["cases"][name]

    def test_valid_stdout_identical_to_pre_edit_capture(self):
        for name, path, _receipt in GOLDEN_CASES:
            with self.subTest(case=name):
                proc = run_cli(path)
                record = self._golden_digest(name)
                self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
                self.assertEqual(proc.returncode, record["exit"])
                self.assertEqual(hashlib.sha256(proc.stdout).hexdigest(),
                                 record["stdout_sha256"],
                                 f"{name}: valid output changed vs pre-edit capture")
                self.assertEqual(len(proc.stdout), record["stdout_bytes"])

    def test_rotated_fixture_matches_b3_historical_summary_bytes(self):
        # Independent anchor: B3's round-trip receipt, produced long before W3.
        for name, path, receipt in GOLDEN_CASES:
            if receipt is None:
                continue
            with self.subTest(case=name):
                proc = run_cli(path)
                self.assertEqual(proc.returncode, 0)
                self.assertEqual(proc.stdout, receipt.read_bytes(),
                                 f"{name}: stdout differs from historical B3 summary bytes")

    def test_m07_probe_receipts_reproduce_byte_for_byte(self):
        receipts = REPO / "material_volume_campaign/agents/M07_ownership/receipts"
        for probe, report_path in M07_PROBE_RECEIPTS:
            with self.subTest(probe=probe):
                proc = run_cli(report_path)
                self.assertEqual(proc.returncode, 0)
                self.assertEqual(proc.stderr, b"")
                self.assertEqual(proc.stdout,
                                 (receipts / f"{probe}.json").read_bytes(),
                                 f"{probe}: stdout differs from M07 receipt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
