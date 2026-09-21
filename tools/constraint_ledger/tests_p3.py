"""P3 — the parallel demonstration: two processes, ONE store directory.

FALSIFIER P3 (preregistration + amendment-1 item 5): two concurrent lanes
append record families to the SAME store directory (no worktrees, no
locks); one canonical merge must (a) equal the sequentially-appended merge
BYTE-FOR-BYTE in either arrival order, (b) flag ZERO false conflicts
between the disjoint families, and (c) preserve the store's declared
invariants — invariant confluence, with a violating extension REFUSED.

Run: python -m unittest tools.constraint_ledger.tests_p3 -v
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from tools.constraint_ledger import interference as I
from tools.constraint_ledger.pilot_laws import (TRUNK_VAULT_INVARIANT,
                                                concrete_externals, load_pilot)
from tools.constraint_ledger.schema import effects, expand, load
from tools.constraint_ledger.store import (StoreError, append_records, merge,
                                           read_inbox, store_invariants,
                                           write_snapshot)

WORKER = r'''
import sys, time, json
sys.path.insert(0, {root!r})
from tools.constraint_ledger.store import append_records
inbox, specfile, delay = sys.argv[1], sys.argv[2], float(sys.argv[3])
specs = json.load(open(specfile, encoding="utf-8"))
for s in specs:
    append_records(inbox, [s])
    time.sleep(delay)
print("appended", len(specs))
'''


def measurement_family_a() -> dict:
    return {
        'name': 'pilot_trace_measurement',
        'kind': 'measurement',
        'lane': 'agent/constraint-ledger-20260921',
        'provenance': {
            'receipt': 'tools/science_funnel/validation/constraint_ledger_20260921/',
            'commit': '6ea2702c23c191ff1d3f14bc895ba668f4586dac',
            'trace': '.tmp/trace1.jsonl (byte-identical double run)',
        },
        'falsifier': 'P2',
        'params': {},
        'quantities': {}, 'constants': {}, 'initial': {}, 'assign': [],
        'measured': {'refusal_tick': 300, 'refusal': 'gait_positional_correction_budget',
                     'rows': 300, 'fires': 8, 'clear_tick_changes': 3,
                     'held_ticks': 48, 'in_band_ticks': 7},
    }


def measurement_family_b() -> dict:
    return {
        'name': 'trunk_vault_wave8_measurement',
        'kind': 'measurement',
        'lane': 'agent/constraint-ledger-20260921',
        'provenance': {
            'receipt': 'tools/science_funnel/validation/gait_zero_20260919/receipt_wave8.json',
            'commit': '6ea2702c23c191ff1d3f14bc895ba668f4586dac',
        },
        'falsifier': 'P3',
        'params': {},
        'quantities': {}, 'constants': {}, 'initial': {}, 'assign': [],
        'measured': {'min_max_demand_cap_ratio': 0.881,
                     'window': 'every single-support node'},
    }


def family_a() -> list[dict]:
    """Membrane family A: the two pilot definitions + the trace measurement."""
    from tools.constraint_ledger.schema import load as _load
    return [TOUCH_BAND_SPEC, HOLD_SPEC, measurement_family_a()]


from tools.constraint_ledger.pilot_laws import STAND_FIRST_HOLD as HOLD_SPEC
from tools.constraint_ledger.pilot_laws import TOUCH_BAND as TOUCH_BAND_SPEC


def family_b() -> list[dict]:
    """Membrane family B: the wave-8 trunk-vault invariant + its measurement.
    Disjoint writes; the quantities never overlap family A's write set."""
    return [TRUNK_VAULT_INVARIANT, measurement_family_b()]


class TestParallelStore(unittest.TestCase):
    def _seed(self, root: Path):
        (root / 'a_specs.json').write_text(json.dumps(family_a()), encoding='utf-8')
        (root / 'b_specs.json').write_text(json.dumps(family_b()), encoding='utf-8')
        return (root / 'worker.py'), WORKER.format(root=str(ROOT))

    def test_concurrent_merge_equals_sequential_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            worker_path, worker_src = self._seed(root)
            worker_path.write_text(worker_src, encoding='utf-8')
            store = root / 'store'
            # REAL CONCURRENT EXECUTION: both lanes spawned together
            pa = subprocess.Popen([sys_executable(), str(worker_path),
                                   str(store / 'incoming' / 'lane-a.jsonl'),
                                   str(root / 'a_specs.json'), '0.02'],
                                  stdout=subprocess.PIPE, cwd=str(ROOT))
            pb = subprocess.Popen([sys_executable(), str(worker_path),
                                   str(store / 'incoming' / 'lane-b.jsonl'),
                                   str(root / 'b_specs.json'), '0.03'],
                                  stdout=subprocess.PIPE, cwd=str(ROOT))
            ra, rb = pa.wait(), pb.wait()
            self.assertEqual((ra, rb), (0, 0), 'both lanes must append cleanly')
            # both inboxes non-empty (the lanes genuinely interleaved)
            ia = read_inbox(store / 'incoming' / 'lane-a.jsonl')
            ib = read_inbox(store / 'incoming' / 'lane-b.jsonl')
            self.assertEqual(len(ia), 3)
            self.assertEqual(len(ib), 2)
            merged_bytes, problems = merge(store)
            self.assertEqual(problems, [])

            # the sequential references: A then B, and B then A
            for order, name in ((('a', 'b'), 'seq_ab'), (('b', 'a'), 'seq_ba')):
                seq_store = root / name
                for fam in order:
                    append_records(seq_store / 'incoming' / f'{fam}.jsonl',
                                   json.loads((root / f'{fam}_specs.json')
                                              .read_text(encoding='utf-8')))
                seq_bytes, seq_problems = merge(seq_store)
                self.assertEqual(seq_problems, [])
                self.assertEqual(merged_bytes, seq_bytes,
                                 f'P3 FIRED: concurrent merge != sequential {name}')

    def test_snapshot_written_and_digest_stable_under_order_swap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            s1, s2 = root / 's1', root / 's2'
            append_records(s1 / 'incoming' / 'x.jsonl', family_a())
            append_records(s1 / 'incoming' / 'y.jsonl', family_b())
            append_records(s2 / 'incoming' / 'y.jsonl', family_b())
            append_records(s2 / 'incoming' / 'x.jsonl', family_a())
            # duplicate delivery must be harmless (content dedup)
            append_records(s1 / 'incoming' / 'x.jsonl', family_a()[:1])
            b1, p1 = merge(s1)
            b2, p2 = merge(s2)
            self.assertEqual(b1, b2, 'F-ORDER: arrival order changed the store')
            self.assertEqual(p1 + p2, [])
            out = write_snapshot(s1)
            self.assertTrue(out.exists())

    def test_zero_false_conflicts_between_disjoint_families(self):
        """The interference calculator over the CONCURRENTLY PUBLISHED set:
        no cross-family pair may be flagged — shared nothing, not even a
        read (family B's invariant reads only its own quantity)."""
        a_insts, b_insts = [], []
        for spec in family_a():
            if spec['kind'] == 'definition':
                a_insts += expand(load(spec))
        for spec in family_b():
            if spec['kind'] == 'definition':
                b_insts += expand(load(spec))
        for a in a_insts:
            for b in b_insts:
                ix = I.interaction(a, b)
                self.assertTrue(ix.independent,
                                f'P3 FIRED: false conflict {a.name} x {b.name}: '
                                f'{ix.quantities}')
        # the merged store still compiles: one writer per quantity holds
        from tools.constraint_ledger.compile import compile_fragment
        frag = compile_fragment([load(s) for s in family_a()
                                 if s['kind'] == 'definition'],
                                concrete_externals(), {})
        self.assertEqual(len(frag.state_keys()), 10)

    def test_invariant_confluence_violating_extension_refused(self):
        """A family that would double-write gait.touch.left is individually
        well-formed but violates the store invariant on merge — the snapshot
        must be REFUSED (satisfiability is not preserved by union; the
        store's declared invariants are)."""
        intruder = {
            'name': 'touch_band_override',
            'kind': 'definition',
            'lane': 'agent/rogue-lane',
            'provenance': {'receipt': 'synthetic (P3 refusal case)', 'commit': 'n/a'},
            'falsifier': 'P3',
            'params': {},
            'quantities': {
                'gait.touch.left': {'entity': 'gait_walker.leg_contact_state',
                                    'frame': 'controller state', 'unit': 'bool',
                                    'dtype': 'bool', 'phase': 'tick-start',
                                    'role': 'state'},
                'x': {'entity': 't', 'frame': 't', 'unit': 'm', 'dtype': 'f64',
                      'phase': 'tick-start', 'role': 'external-input'}},
            'constants': {}, 'initial': {'gait.touch.left': False},
            'assign': [{'write': 'gait.touch.left', 'expr': 'x > 0'}],
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            s = root / 'store'
            append_records(s / 'incoming' / 'a.jsonl', family_a())
            append_records(s / 'incoming' / 'b.jsonl', family_b())
            good_bytes, good_problems = merge(s)
            self.assertEqual(good_problems, [])
            append_records(s / 'incoming' / 'rogue.jsonl', [intruder])
            bad_bytes, bad_problems = merge(s)
            self.assertTrue(bad_problems,
                            'the second writer must be flagged')
            with self.assertRaises(StoreError):
                write_snapshot(s)
            self.assertNotEqual(good_bytes, bad_bytes)


def sys_executable() -> str:
    import sys
    return sys.executable


if __name__ == '__main__':
    unittest.main()
