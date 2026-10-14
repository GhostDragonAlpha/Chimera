"""L6 tests — infeasibility and named cores (lane agent/cl-L6-cores-20260921).

Falsifiers under test (preregistered BEFORE the machinery ran; see the module
docstring of l6_cores and the L6 receipt):
  F-CORE-UNSOUND     a reported core must be UNSAT by DIRECT conjunction in
                     the exact background (no activation literals) — a sat
                     or unknown core is fabricated and voids the lane;
  F-CORE-NONMINIMAL  every member of a claimed-minimal core must be
                     indispensable (core-minus-member is SAT);
  F-FALSE-CLEARANCE  no sealed-unsat fixture is ever reported feasible;
                     UNKNOWN IS NEVER CLEARANCE.

Run: python -m unittest tools.constraint_ledger.tests_l6 -v
"""
from __future__ import annotations

import unittest

from tools.constraint_ledger import l6_cores as L6
from tools.constraint_ledger.schema import load


class TripleFixture(unittest.TestCase):
    """The spec's demanded higher-order conflict: every pair satisfiable,
    the triple (x=y ^ y=z ^ x!=z) not."""

    def setUp(self):
        self.fix = next(f for f in L6.fixtures()
                        if f['name'] == 'l6_triple_eq_neq')
        self.recs = [load(s) for s in self.fix['records']]
        self.v = L6.check(self.recs, name=self.fix['name'])

    def test_unsat_with_core(self):
        self.assertEqual(self.v.status, 'unsat')
        self.assertEqual(self.v.core, self.fix['expect_core'])
        self.assertEqual(len(self.v.core), 3)

    def test_every_pair_satisfiable(self):
        # the higher-order property: each 2-subset is SAT (direct conjunction)
        ids = sorted(r.name for r in self.recs)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                self.assertEqual(
                    L6.direct_conjunction_status([ids[i], ids[j]], self.recs),
                    'sat', f'pair {ids[i]}+{ids[j]} must be satisfiable')

    def test_minimal_core_is_exactly_the_triple(self):
        # minimality is REAL: no 2-record core exists
        for m in self.v.core:
            subset = [x for x in self.v.core if x != m]
            self.assertEqual(L6.direct_conjunction_status(subset, self.recs),
                             'sat')

    def test_core_rechecks_unsat_without_activation_machinery(self):
        self.assertTrue(L6.core_is_sound(self.v.core, self.recs))


class SealedFixtures(unittest.TestCase):
    """Every sealed fixture is judged against its preregistered verdict."""

    def test_all_sealed_verdicts(self):
        for fix in L6.fixtures():
            recs = [load(s) for s in fix['records']]
            v = L6.check(recs, name=fix['name'])
            self.assertEqual(v.status, fix['expect'], fix['name'])
            if fix['expect'] == 'unsat':
                self.assertEqual(v.core, fix['expect_core'], fix['name'])
            else:
                self.assertIsNone(v.core, fix['name'])
                self.assertTrue(v.cleared, f'{fix["name"]} clearance must be '
                                           f'witness-checked')

    def test_sat_witness_survives_true_float64_evaluate(self):
        fix = next(f for f in L6.fixtures() if f['name'] == 'l6_sat_band')
        recs = [load(s) for s in fix['records']]
        v = L6.check(recs, name=fix['name'])
        self.assertTrue(v.witness_checked)
        self.assertEqual(sorted(v.witness), ['x', 'y'])

    def test_herring_noise_record_is_dropped(self):
        # the minimizer must drop the irrelevant record whatever the raw
        # solver core said (raw cores are NOT minimal in general)
        fix = next(f for f in L6.fixtures() if f['name'] == 'l6_herring')
        recs = [load(s) for s in fix['records']]
        v = L6.check(recs, name=fix['name'])
        self.assertNotIn('l6_herr_r1_noise', v.core)
        self.assertEqual(v.core, fix['expect_core'])

    def test_definition_records_lower_to_equations(self):
        # the four-record gap fixture: every 3-subset is SAT, all four UNSAT
        fix = next(f for f in L6.fixtures() if f['name'] == 'l6_def_gap')
        recs = [load(s) for s in fix['records']]
        v = L6.check(recs, name=fix['name'])
        self.assertEqual(v.core, fix['expect_core'])
        self.assertEqual(L6.direct_conjunction_status(v.core, recs), 'unsat')
        for m in v.core:
            subset = [x for x in v.core if x != m]
            self.assertEqual(L6.direct_conjunction_status(subset, recs), 'sat')

    def test_sealed_digests_are_stable(self):
        digests = {f['name']: L6.fixture_digest(f) for f in L6.fixtures()}
        self.assertEqual(len(set(digests.values())), len(digests))
        for fix in L6.fixtures():
            self.assertEqual(digests[fix['name']], L6.fixture_digest(fix))


class FalsifierHarness(unittest.TestCase):
    """The three preregistered falsifiers, run over EVERYTHING reported."""

    def setUp(self):
        self.payload = L6.run_all()

    def test_F_CORE_UNSOUND(self):
        f = self.payload['falsifiers']['F-CORE-UNSOUND']
        self.assertGreater(f['cores_rechecked'], 0)   # the harness really ran
        self.assertEqual(f['violations'], 0)
        for row in self.payload['fixtures']:
            if row.get('core') is not None:
                self.assertTrue(row['core_direct_conjunction_unsat'],
                                row['fixture'])

    def test_F_CORE_NONMINIMAL(self):
        f = self.payload['falsifiers']['F-CORE-NONMINIMAL']
        self.assertGreater(f['members_rechecked'], 0)
        self.assertEqual(f['violations'], 0)
        for row in self.payload['fixtures']:
            if row.get('core') is not None:
                self.assertTrue(row['every_member_indispensable'],
                                row['fixture'])

    def test_F_FALSE_CLEARANCE(self):
        f = self.payload['falsifiers']['F-FALSE-CLEARANCE']
        self.assertGreater(f['sealed_unsat_fixtures'], 0)
        self.assertEqual(f['false_clearances'], 0)
        self.assertEqual(f['unknown_clearance_attempts'], 0)

    def test_unknown_is_never_clearance(self):
        # the classification law, unit-pinned: only a witness-checked sat
        # clears; an unknown verdict is NOT feasible
        v = L6.Verdict(status='unknown', fixture='<pinned>')
        self.assertFalse(v.cleared)
        v2 = L6.Verdict(status='sat', fixture='<pinned>')
        self.assertFalse(v2.cleared)          # sat WITHOUT the bridge is not
        v2.witness_checked = True
        self.assertTrue(v2.cleared)

    def test_prediction_held_and_all_green(self):
        self.assertTrue(self.payload['prediction_held'])
        self.assertTrue(self.payload['falsifiers_all_green'])


class InteractionIdentity(unittest.TestCase):
    """sorted record IDs + background digest + assumptions + horizon are ALL
    hashed into the interaction identity."""

    def setUp(self):
        self.bg = 'd' * 64
        self.args = (['b', 'a'], self.bg, ['e2', 'e1'], 'single-state@0')

    def test_stable_and_canonical_in_core_and_assumption_order(self):
        a = L6.interaction_identity(*self.args)
        b = L6.interaction_identity(['a', 'b'], self.bg, ['e1', 'e2'],
                                    'single-state@0')
        self.assertEqual(a, b)
        self.assertEqual(a, L6.interaction_identity(*self.args, full=True)[:32])

    def test_every_input_changes_the_identity(self):
        base = L6.interaction_identity(*self.args)
        self.assertNotEqual(base, L6.interaction_identity(
            ['b', 'a', 'c'], self.bg, ['e1', 'e2'], 'single-state@0'))
        self.assertNotEqual(base, L6.interaction_identity(
            ['b', 'a'], 'e' * 64, ['e1', 'e2'], 'single-state@0'))
        self.assertNotEqual(base, L6.interaction_identity(
            ['b', 'a'], self.bg, ['e1', 'e2', 'e3'], 'single-state@0'))
        self.assertNotEqual(base, L6.interaction_identity(
            ['b', 'a'], self.bg, ['e1', 'e2'], 'single-state@1'))

    def test_reported_carry_their_identity(self):
        for fix in L6.fixtures():
            if fix['expect'] != 'unsat':
                continue
            recs = [load(s) for s in fix['records']]
            v = L6.check(recs, name=fix['name'])
            expect = L6.interaction_identity(
                v.core, L6.background_digest(L6.background_of(recs)),
                [r.name for r in recs], v.horizon)
            self.assertEqual(v.identity, expect, fix['name'])
            # a clearance names NOTHING
        fix = next(f for f in L6.fixtures() if f['expect'] == 'sat')
        recs = [load(s) for s in fix['records']]
        self.assertIsNone(L6.check(recs, name=fix['name']).identity)


if __name__ == '__main__':
    unittest.main()
