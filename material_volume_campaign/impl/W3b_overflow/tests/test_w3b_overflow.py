"""W3b failing-first regressions for F-R2-3 (out-of-range JSON integers).

FAILING-FIRST (prereg ../PREREGISTRATION.md, frozen before the edit): the two
T-row tests demand frozen named refusals for a 10**400 JSON integer literal at
the mass and inertia coercion sites; against the unedited reader they ERROR
with the uncaught OverflowError (CLI exit 1 + traceback) — the F-R2-3 escape.
Guard tests prove the widened conversion set stays exactly
(TypeError, ValueError, OverflowError) at the two coercion helpers and that
unexpected exception classes still propagate uncaught. The control test pins
the valid scaffold's exit 0 and its pre-edit stdout sha256, so valid output
must stay byte-identical.

W3's own suite (impl/W3_reader_m13/tests/) stays the owner of the T/K rows and
golden manifest; this file adds only the F-R2-3 rows, regenerated fixtures and
all, and is runnable from anywhere.

Run: python tests/test_w3b_overflow.py   (from impl/W3b_overflow/)
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
REPO = HERE.parents[3]
TOOLS = REPO / "tools"
READER_PATH = TOOLS / "material_volume_body_export_reader.py"
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(TOOLS))

import material_volume_body_export_reader as reader  # noqa: E402

MASS_DETAIL = ("body_groups[1] mass_properties.mass.value "
               "is malformed: not a finite JSON number")
TENSOR_DETAIL = ("body_groups[1] mass_properties.inertia_tensor_about_com.value "
                 "is malformed: not a rectangular numeric array")
MASS_LINE = f"bad_export_report: {MASS_DETAIL}\n"
TENSOR_LINE = f"bad_export_report: {TENSOR_DETAIL}\n"

HUGEINT_CASES = [
    ("w3b_v1_mass_hugeint", FIXTURES / "w3b_v1_mass_hugeint.json",
     MASS_LINE, MASS_DETAIL),
    ("w3b_v2_tensor_hugeint", FIXTURES / "w3b_v2_tensor_hugeint.json",
     TENSOR_LINE, TENSOR_DETAIL),
]

# Frozen single-diff property: each hugeint fixture differs from the valid
# control in exactly one JSON scalar, at this path.
FROZEN_DIFF_PATHS = {
    "w3b_v1_mass_hugeint.json": ".body_groups[1].mass_properties.mass.value",
    "w3b_v2_tensor_hugeint.json":
        ".body_groups[1].mass_properties.inertia_tensor_about_com.value[2][2]",
}

# Pre-edit golden (captured at HEAD 1afb552a, before the W3b edit): the valid
# control's stdout — valid output must stay byte-identical.
CONTROL_STDOUT_SHA256 = "3a18ed3335df7f6a01aaa8b71161d6a9567efa629cea415ef90e23bc5777fe97"
CONTROL_STDOUT_BYTES = 1643


def run_cli(report_path):
    return subprocess.run([sys.executable, str(READER_PATH), str(report_path)],
                          cwd=str(REPO), capture_output=True)


def stderr_text(proc):
    """Decode stderr, normalizing the Windows text-mode \\r\\n artifact."""
    return proc.stderr.decode("utf-8").replace("\r\n", "\n")


def single_diff_path(control_path, case_path):
    a = json.loads(control_path.read_text(encoding="utf-8"))
    b = json.loads(case_path.read_text(encoding="utf-8"))
    diffs = []

    def walk(path, x, y):
        if type(x) is not type(y):
            diffs.append(path)
        elif isinstance(x, dict):
            for key in set(x) | set(y):
                walk(f"{path}.{key}", x.get(key), y.get(key))
        elif isinstance(x, list):
            for i in range(max(len(x), len(y))):
                walk(f"{path}[{i}]",
                     x[i] if i < len(x) else None,
                     y[i] if i < len(y) else None)
        elif x != y:
            diffs.append(path)

    walk("", a, b)
    return diffs


class TestFrozenOverflowRefusals(unittest.TestCase):
    """The two failing-first rows: 10**400 literals become named refusals."""

    def test_each_hugeint_shape_refused_with_frozen_line_and_exit_2(self):
        for name, path, line, _detail in HUGEINT_CASES:
            with self.subTest(case=name):
                proc = run_cli(path)
                self.assertEqual(proc.returncode, 2, stderr_text(proc))
                self.assertEqual(proc.stdout, b"")
                self.assertEqual(stderr_text(proc), line)

    def test_each_hugeint_shape_raises_named_refusal_in_process(self):
        for name, path, _line, detail in HUGEINT_CASES:
            with self.subTest(case=name):
                report = json.loads(path.read_text(encoding="utf-8"))
                # Pre-edit this line lets the bare OverflowError escape (the
                # F-R2-3 crash, demonstrated verbatim in receipts/10_*).
                with self.assertRaises(ValueError) as caught:
                    reader.summarize_export_report(report)
                self.assertIsInstance(caught.exception,
                                      reader.exporter.ExportInputError)
                error = caught.exception
                self.assertEqual((error.reason, error.detail),
                                 ("bad_export_report", detail))


class TestControlScaffold(unittest.TestCase):
    """The valid control proves the scaffold is sound: exit 0, frozen bytes."""

    CONTROL = FIXTURES / "w3b_v0_valid_control.json"

    def test_valid_control_exits_zero_with_pre_edit_bytes(self):
        proc = run_cli(self.CONTROL)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(proc.stderr, b"")
        self.assertEqual(hashlib.sha256(proc.stdout).hexdigest(),
                         CONTROL_STDOUT_SHA256,
                         "valid output changed vs the pre-edit capture")
        self.assertEqual(len(proc.stdout), CONTROL_STDOUT_BYTES)

    def test_each_hugeint_fixture_differs_from_control_in_exactly_one_scalar(self):
        for name, path, _line, _detail in HUGEINT_CASES:
            with self.subTest(case=name):
                diffs = single_diff_path(self.CONTROL, path)
                self.assertEqual(diffs, [FROZEN_DIFF_PATHS[path.name]],
                                 "the hugeint must be the sole anomaly")


class TestUnexpectedStillUnexpected(unittest.TestCase):
    """Guards: only OverflowError joins the converted set, at the same sites."""

    VALID = FIXTURES / "w3b_v0_valid_control.json"

    def _control_report(self):
        return json.loads(self.VALID.read_text(encoding="utf-8"))

    def test_injected_runtime_error_at_tensor_coercion_propagates(self):
        with mock.patch.object(reader.np, "asarray",
                               side_effect=RuntimeError("injected programming error")):
            with self.assertRaises(RuntimeError):
                reader.summarize_export_report(self._control_report())

    def test_injected_key_error_at_tensor_coercion_propagates(self):
        with mock.patch.object(reader.np, "asarray",
                               side_effect=KeyError("injected programming error")):
            with self.assertRaises(KeyError):
                reader.summarize_export_report(self._control_report())

    def test_injected_runtime_error_at_mass_finite_check_propagates(self):
        with mock.patch.object(reader.math, "isfinite",
                               side_effect=RuntimeError("injected programming error")):
            with self.assertRaises(RuntimeError):
                reader.summarize_export_report(self._control_report())

    def test_source_pins_the_frozen_conversion_set(self):
        source = READER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("except:", source)
        self.assertNotIn("except Exception", source)
        self.assertNotIn("except BaseException", source)
        # W3's pinned two-tuple clauses remain, and OverflowError joins at
        # exactly the same two helpers — nowhere else.
        self.assertEqual(source.count("except (TypeError, ValueError)"), 2)
        self.assertEqual(source.count("except OverflowError"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
