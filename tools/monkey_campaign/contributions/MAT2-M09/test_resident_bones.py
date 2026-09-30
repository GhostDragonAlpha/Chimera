"""MAT2-M09 named checks for the resident GPU world (X3 arm).

Executable form of the X3 done_when clauses (run by batch_gates gate 5):
  P_bone_layout            the resident layout IS kernel_mirror's layout
  P_bone_single_writer     device state written only by the declared path
  P_gates_declared         the GPU world refuses through declared names
  P_vacuous_guard          the vacuous-comparison guard is self-tested
  P_modes_declared         the dispatch table carries exactly the
                           documented mode names (the mailbox law)
  SIM_short_oracle_agreement   the ACTUAL kernel code runs the first
                           ticks against the oracle under numba's CUDA
                           simulator (CPU-first; positions within the
                           frozen 1e-12 m window)
  X3_gpu_bank_receipts     the real-GPU receipts, when present, assert
                           the frozen windows (skipUnless present)

Run:  python -B test_resident_bones.py
"""
from __future__ import annotations

import os
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# The simulator env var must be set before numba's cuda submodule is
# imported anywhere in this process (unit tests share one interpreter).
os.environ.setdefault('NUMBA_ENABLE_CUDASIM', '1')

import run_experiments as rx  # noqa: E402

try:
    import resident_bones as rb
    _RB_AVAILABLE = True
except Exception:  # noqa: BLE001  (no numba / no display: CPU-only host)
    rb = None
    _RB_AVAILABLE = False


def load(name):
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(name + ' (run the experiment modes first)')
    return rx.json.loads(path.read_text(encoding='utf-8'))


@unittest.skipUnless(_RB_AVAILABLE, 'resident_bones importable '
                     '(numba present)')
class Layout(unittest.TestCase):
    def test_P_bone_layout_is_kernel_mirror(self):
        scan = rx.p_bone_layout()
        self.assertTrue(scan['ok'], scan)

    def test_P_bone_single_writer(self):
        scan = rx.p_bone_single_writer()
        self.assertTrue(scan['ok'], scan['violations'])

    def test_P_gates_declared(self):
        gates = rx.p_gates_declared()
        self.assertEqual(gates['count'], 10)
        self.assertIn('convergence_gate_not_met', gates['gate_codes'])
        self.assertIn('digest_chain_stale', gates['gate_codes'])
        self.assertIn('support_lost_or_hidden', gates['gate_codes'])

    def test_P_vacuous_guard(self):
        self.assertTrue(rx.vacuous_guard_selftest())
        with self.assertRaises(ValueError) as cm:
            rx.refuse_vacuous(0.0, 0.0)
        self.assertEqual(str(cm.exception), 'vacuous_comparison_refused')

    def test_P_modes_declared(self):
        import run_experiments
        src = (HERE / 'run_experiments.py').read_text(encoding='utf-8')
        for mode in ('main', 'rerun', 'compare', 'falsify', 'regression',
                     'mirror', 'gmain', 'grerun', 'gcompare'):
            self.assertIn(f"'{mode}': mode_", src)
            self.assertTrue(callable(getattr(run_experiments,
                                             f'mode_{mode}')),
                            mode)


@unittest.skipUnless(_RB_AVAILABLE, 'resident_bones importable '
                     '(numba present)')
class SimulatorAgreement(unittest.TestCase):
    def test_SIM_short_oracle_agreement(self):
        """The actual kernel code (CUDA simulator) against the sealed
        oracle: gates green, the digest chain self-consistent, and the
        16-row vertex snapshot inside the frozen 1e-12 m window."""
        import numpy as np
        import assembly as asm
        oracle = asm.AssemblyRun()
        gpu = rb.ResidentBonesWorld()
        try:
            for tick in range(3):
                oracle.step(tick)
                gpu.step_tick(tick)
                block = gpu.diagnostics()
                gpu.check_gates(block, tick)  # named refusals + digests
                xs = gpu.snapshot()
                dpos = max(
                    float(np.abs(xs[:8]
                                 - np.asarray(oracle.bone_a.x)).max()),
                    float(np.abs(xs[8:]
                                 - np.asarray(oracle.bone_b.x)).max()))
                self.assertLessEqual(dpos, 1e-12)
        finally:
            gpu.release()


def _receipts_present():
    return (HERE / 'gpu_receipt.json').exists() \
        and (HERE / 'gpu_determinism_receipt.json').exists()


@unittest.skipUnless(_receipts_present(),
                     'GPU bank receipts not present (run gmain/grerun/'
                     'gcompare on the GPU box first)')
class X3Receipts(unittest.TestCase):
    def test_X3_gpu_bank_windows(self):
        receipt = load('gpu_receipt.json')
        self.assertTrue(receipt['X3_pass'])
        self.assertLessEqual(receipt['worst_position_diff_m'],
                             receipt['windows']['position_m'])
        self.assertLessEqual(receipt['worst_scalar_relative_overall'],
                             receipt['windows']['scalar_relative'])
        self.assertTrue(receipt['telemetry']['within_budget'])
        self.assertTrue(receipt['digest_chain_green_every_tick'])
        self.assertTrue(receipt['position_within_window'])
        self.assertTrue(receipt['comparables_within_window'])
        self.assertEqual(receipt['exceeded_ticks'], [])
        self.assertTrue(receipt['p_bone_layout']['ok'])
        self.assertTrue(receipt['p_bone_single_writer']['ok'])
        self.assertTrue(receipt['oracle_trace_frozen']['matches'])

    def test_X3_determinism_byte_identity(self):
        receipt = load('gpu_determinism_receipt.json')
        self.assertTrue(receipt['X3_trace_byte_identical'])
        self.assertTrue(receipt['X3_receipt_byte_identical'])
        self.assertTrue(receipt['X3_runs_pass'])
        self.assertTrue(receipt['X3_pass'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
