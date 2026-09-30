"""MAT2-M09 named checks for the X3 CPU-FIRST mirror clause.

The executable form of prereg X3's first requirement: kernel_mirror.py is
BITWISE-agreed with assembly.AssemblyRun on the frozen 90-tick fixture
(rows, state_hash chains, trajectories, declared-order block fold) before
any GPU work. The short fixture runs live in this suite; the full frozen
fixture runs via `python -B run_experiments.py mirror` (receipt:
mirror_rehearsal_receipt.json), asserted here when present.

Run:  python -B test_mirror_rehearsal.py
"""
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M05'), str(CONTRIB / 'MAT2-M06')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import assembly as asm  # noqa: E402
import kernel_mirror as km  # noqa: E402
import mirror_rehearsal as mr  # noqa: E402


class MirrorShortFixture(unittest.TestCase):
    def test_order_and_short_bitwise(self):
        self.assertEqual(asm.DECLARATION['order'],
                         km.MirrorWorld().declaration['order'])
        res = mr.run_rehearsal(12)
        self.assertEqual(res['findings'], [])
        self.assertEqual(res['worst_position_diff_m'], 0.0)
        self.assertEqual(res['worst_block_scalar_diff'], 0.0)
        self.assertTrue(res['rows_bitwise_identical'])
        self.assertTrue(res['state_hash_chains_identical'])


class MirrorFullReceipt(unittest.TestCase):
    def test_full_fixture_receipt(self):
        path = HERE / 'mirror_rehearsal_receipt.json'
        if not path.exists():
            self.skipTest('mirror_rehearsal_receipt.json not generated yet '
                          '(run: python -B run_experiments.py mirror)')
        receipt = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(receipt['schema'],
                         'chimera.m09_mirror_rehearsal.v1')
        self.assertEqual(receipt['fixture']['ticks'], asm.TICKS)
        self.assertEqual(receipt['findings'], [])
        self.assertEqual(receipt['worst_position_diff_m'], 0.0)
        self.assertTrue(receipt['rows_bitwise_identical'])
        self.assertTrue(receipt['state_hash_chains_identical'])
        self.assertTrue(receipt['X3_mirror_bitwise_agreed'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
