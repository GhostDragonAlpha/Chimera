"""{{CARD_FULL}} named checks - card-kit template (M08 pattern).

Each check reads the COMMITTED receipts and asserts the frozen claims, so
the suite is the executable form of the done_when clauses. The suite is what
independent review re-runs first; batch_gates.py runs it CPU-only.

THE LAW (M08, earned twice): receipt-semantics changes land TOGETHER with
the named check that asserts them, in the SAME change. If you add/rename a
receipt flag, the check that reads it lands in the same commit; if you
remove one, the stale check dies in the same commit. A stale named check is
a red suite - batch_gates catches it, but never ship knowing it is stale.

Naming: X<n>_<clause> for done_when executions, F<n>_... for falsifier
arms, P_... for probes (pins, single-writer, gates declared, vacuous guard,
regression). Check names are stable identifiers cited by report.md; do not
rename without updating the report generator.

FILL LIST: {{CARD_FULL}} + one class/check per clause, reading YOUR receipt
fields. Delete checks for arms the card does not declare.
Run:  python -B test_{{CARD_ID_LOWER}}_checks.py   (or unittest discover)
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

CARD_FULL = '{{CARD_FULL}}'
if CARD_FULL.startswith('{{'):
    raise SystemExit('test template is UNFILLED: replace the {{...}} '
                     'placeholders before running.')

# FILL: import your run_experiments module for the P_ probes:
# import run_experiments as rx


def load(name):
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(name + ' (run the experiment modes first)')
    return json.loads(path.read_text(encoding='utf-8'))


class X1Agreement(unittest.TestCase):
    """X1: the executable form of the agreement clause. Assert the frozen
    windows FROM the receipt, not re-measured (the receipt is the record;
    re-measurement is the modes' job)."""

    def test_X1_gpu_direct_reference_agreement(self):
        receipt = load('experiment_receipt.json')
        self.assertTrue(receipt['X1_pass'])
        self.assertTrue(receipt['position_within_window'])
        self.assertTrue(receipt['scalars_within_window'])
        self.assertTrue(receipt['telemetry']['within_budget'])
        self.assertLessEqual(receipt['worst_membrane_position_diff_m'],
                             receipt['windows']['position_m'])
        self.assertLessEqual(receipt['worst_plate_position_diff_m'],
                             receipt['windows']['position_m'])


class X2Determinism(unittest.TestCase):
    """X2 scoped verdict (M08 6ee1e8f6 lesson): the declared determinism
    unit is the TRACE; receipts legitimately differ by mode_main's declared
    augmentation keys. Assert the scoped gate, not full-file identity."""

    def test_X2_determinism_byte_identity(self):
        receipt = load('determinism_receipt.json')
        self.assertTrue(receipt['X2_trace_byte_identical'])
        self.assertTrue(receipt['X2_pass'])
        self.assertEqual(receipt['receipt_keys_only_in_rerun'], [])
        self.assertEqual(receipt['receipt_shared_keys_differing'], [])


class X3Profile(unittest.TestCase):
    def test_X3_residency_profile_within_budget(self):
        receipt = load('profile_receipt.json')
        self.assertTrue(receipt['residency_within_budget'])
        self.assertGreater(receipt['state_bytes_total'], 0)
        # residency sanity: per-tick traffic is bounded far below the
        # resident state it must not roundtrip
        self.assertLess(receipt['max_up_bytes_per_tick'],
                        receipt['state_bytes_total'])
        self.assertLess(receipt['max_down_bytes_per_tick'],
                        receipt['state_bytes_total'])


class Falsifiers(unittest.TestCase):
    """Every arm: the tamper BITES, the clean control PASSES, the arm is
    DISCRIMINATING (the tamper actually measured worse than production).
    FILL: one assert per arm from YOUR falsifier_receipt.json arms."""

    def test_F_all_arms_bite_with_clean_controls(self):
        receipt = load('falsifier_receipt.json')
        arms = receipt['arms']
        self.assertTrue(receipt['F_all_green'])
        for name, value in arms.items():
            if isinstance(value, bool):
                self.assertTrue(value, f'arm {name} is not green')


class Probes(unittest.TestCase):
    """P_ probes: structural properties of the candidate itself."""

    def test_P_input_pins(self):
        # rx.verify_input_pins()   # FILL: uncomment with the rx import
        raise unittest.SkipTest('FILL: import run_experiments as rx first')

    def test_P_single_writer(self):
        # scan = rx.p_single_writer()
        # self.assertTrue(scan['ok'], scan['violations'])
        raise unittest.SkipTest('FILL: import run_experiments as rx first')

    def test_P_vacuous_guard(self):
        # self.assertTrue(rx.vacuous_guard_selftest())
        raise unittest.SkipTest('FILL: import run_experiments as rx first')

    def test_P_regression_suite(self):
        receipt = load('regression_receipt.json')
        self.assertEqual(receipt['exit_code'], 0)
        self.assertTrue(receipt['P_regression_suite_green'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
