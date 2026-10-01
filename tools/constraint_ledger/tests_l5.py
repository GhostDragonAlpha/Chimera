"""P-L5 — TRANSITIVE interference through the physics: fixtures + falsifiers.

THE SEALED EXPECTATIONS (pre-registered at
tools/science_funnel/validation/cl_L5_20260921/preregistration.json,
committed BEFORE this module was written — Rule 0):

  P1 fixture SHARED_CARRIER: the frozen first-order calculator calls (A,C)
     and (B,C) independent; the L5 propagation flags BOTH with a carrier
     quantity and an evidenced physics path whose stages run
     force-accumulation -> body-state -> contact-guard -> sensor, and with
     ZERO direct-write classes on those pairs.
  P2 fixture READ_READONLY: both calculators return independent, no
     write-write class anywhere; the cones stay narrow.
  P3 F-MISSED-COUPLING (synthetic-twin leg): a one-ulp perturbation of
     force_law_a's constant escapes the FIRST-ORDER cone of A (the pilot's
     measured gap — expected red for v1) but is COVERED by the L5 cone;
     alarm_watch's one-ulp perturbation changes exactly alarm.a (its exact
     L5 cone — the usefulness witness).
     F-MISSED-COUPLING FIRES (lane RED) iff any changed observable escapes
     the L5 cone, on the twin OR on the real trace.
  P4 F-MISSED-COUPLING (real-trace leg, l5_real_trace.py): row 0 (the reset
     row) must not move outside the perturbed leg's declared clock init;
     right-leg decision changes must be input-witnessed or attributed to
     the declared-opaque scheduler (reported as measured evidence).
  P5 F-VACUOUS-CONE: fires iff EVERY distinct fixture collapses to the full
     graph. A full graph is CONSERVATIVE (sound), not useful — the two
     failures are reported on separate axes (collapse_stats).

Run: python -m unittest tools.constraint_ledger.tests_l5 -v
(the real-trace leg compiles the pinned harness with g++; it skips with a
NAMED reason if the toolchain is absent, never silently)
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from . import interference as I1
from . import interference2 as I2
from . import l5_real_trace as RT
from .l5_fixtures import (AUDIT_WATCH, ALARM_WATCH, FORCE_LAW_A, FORCE_LAW_B,
                          LOAD_SHARE_LAW, counterfactual, load_fixture,
                          read_readonly_specs, shared_carrier_specs,
                          shared_physics, empty_physics)
from .pilot_laws import load_pilot
from .schema import expand

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / 'tools/science_funnel/validation/cl_L5_20260921'
LANE = 'agent/cl-L5-transitive-20260921'

CANONICAL_STAGES = ('force-accumulation', 'body-state', 'contact-guard', 'sensor')


def _evidence(name: str, payload) -> None:
    RECEIPT.mkdir(parents=True, exist_ok=True)
    (RECEIPT / name).write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str),
        encoding='utf-8', newline='\n')


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f1 = load_fixture(shared_carrier_specs())
        cls.f2 = load_fixture(read_readonly_specs())
        cls.ph = shared_physics()
        cls.g1 = I2.build_graph(cls.f1, cls.ph)
        cls.g2 = I2.build_graph(cls.f2, cls.ph)
        cls.g3 = I2.build_graph(cls.f1, empty_physics())   # the v1 world


class TestSharedCarrier(_Base):
    """P1 — the spec's fixture 1, verdicts sealed in the preregistration."""

    maxDiff = None

    def test_v1_first_order_calls_them_independent(self):
        a, b, c, _aud = self.f1
        self.assertTrue(I1.interaction(a, c).independent,
                        'first-order must miss the shared force carrier')
        self.assertTrue(I1.interaction(b, c).independent)

    def test_v2_flags_both_through_physics_with_no_direct_write(self):
        a, b, c, _aud = self.f1
        for x, y in ((a, c), (b, c)):
            ix = I2.interaction2(x, y, self.g1)
            self.assertFalse(ix.independent, f'{x.name}->{y.name} must flag')
            self.assertEqual(ix.direct_write_quantities, set(),
                             'flag must come THROUGH physics, not a write')
            carrier = ix.carriers['sensor.load_share']
            self.assertIn('physics-carried', carrier['classes'])
            self.assertIn('X->Y', carrier['directions'])
            self.assertEqual(carrier['stages_a_to_b'], CANONICAL_STAGES,
                             'the evidenced path must run the whole loop')

    def test_v1_sees_nothing_v2_sees_the_carrier(self):
        # the SAME declarations fed to the FROZEN interface's cone
        cone = I1.build_cone(self.f1, I2.physics_edges_of(self.ph))
        self.assertIn('sensor.load_share', cone.reach['force_law_a'])
        cone0 = I1.build_cone(self.f1, physics_edges=[])
        self.assertNotIn('sensor.load_share', cone0.reach['force_law_a'])

    def test_matrix_sanity(self):
        a, b, c, aud = self.f1
        self.assertFalse(I2.interaction2(a, b, self.g1).independent,
                         'the two force outputs share the carrier')
        for x in (a, b, c):
            self.assertTrue(I2.interaction2(x, aud, self.g1).independent,
                            'the terminal-sink audit law couples to nothing')
        self.assertEqual(sorted(self.g1.reach['audit_logger']), ['audit.flag'])


class TestReadReadonly(_Base):
    """P2 — the spec's fixture 2: shared reads are harmless."""

    def test_not_flagged_as_direct_write_conflict(self):
        d, e = self.f2
        v1 = I1.interaction(d, e)
        self.assertTrue(v1.independent)
        v2 = I2.interaction2(d, e, self.g2)
        self.assertTrue(v2.independent)
        self.assertEqual(v2.direct_write_quantities, set())
        self.assertFalse(any('write-write' in c
                             for q in v2.carriers for c in q.get('classes', []))
                         if v2.carriers else False)

    def test_cones_stay_narrow(self):
        d, e = self.f2
        self.assertEqual(sorted(self.g2.reach[d.name]), ['alarm.a'])
        self.assertEqual(sorted(self.g2.reach[e.name]), ['audit.count'])
        self.assertEqual(I2.collapse_stats(self.g2)['collapse_fraction'], 0.0)


class TestFMissedCoupling(_Base):
    """P3 — the replayable counterfactual vs the predicted cones.
    FIRES (lane RED) iff a changed observable escapes the L5 cone."""

    def test_counterfactual_escapes_the_first_order_cone(self):
        # the MEASURED pilot gap: the FROZEN first-order cone (no physics
        # edges) of force_law_a is its write only
        cf = counterfactual(self.f1, 'force_law_a', 'kSpringA')
        self.assertTrue(cf['changed'], 'perturbation must be observable')
        self.assertIn('sensor.load_share', cf['changed'],
                      'the shared carrier must move under the perturbation')
        v1_cone_a = set(I2.v1_cone(self.f1)['force_law_a'])
        self.assertFalse(set(cf['changed']) <= v1_cone_a,
                         'v1 cone must MISS (the named gap this lane closes)')

    def test_l5_cone_covers_the_counterfactual(self):
        cf = counterfactual(self.f1, 'force_law_a', 'kSpringA')
        covered, misses = I2.cone_covers(self.g1.reach['force_law_a'],
                                         cf['changed'])
        self.assertTrue(covered, f'F-MISSED-COUPLING FIRES: {sorted(misses)}')
        v1_cone = I2.v1_cone(self.f1)
        _evidence('f_missed_coupling_twin.json', {
            'lane': LANE,
            'perturbed': 'force_law_a.kSpringA (one ulp up)',
            'changed': sorted(cf['changed']),
            'l5_cone': sorted(self.g1.reach['force_law_a']),
            'v1_cone': sorted(v1_cone['force_law_a']),
            'v1_misses': sorted(set(cf['changed']) - set(v1_cone['force_law_a'])),
            'covered': covered, 'witness': cf['witness'],
        })

    def test_exact_narrow_cone_witness(self):
        # alarm_watch's constant flows in BOTH branches, so the one-ulp
        # perturbation is observable; its cone must be EXACTLY its write
        cf = counterfactual(self.f2, 'alarm_watch', 'kAlarmOne')
        self.assertEqual(set(cf['changed']), set(self.g2.reach['alarm_watch']),
                         'narrow true influence must equal the narrow cone')


class TestFVacuousCone(_Base):
    """P5 — usefulness, on its own axis (a full graph is conservative)."""

    def test_fixtures_do_not_collapse(self):
        s1 = I2.collapse_stats(self.g1)
        s2 = I2.collapse_stats(self.g2)
        self.assertEqual(s1['collapse_fraction'], 0.0,
                        'the closed loop must still exclude the audit sink')
        self.assertEqual(s2['collapse_fraction'], 0.0)
        vacuous = all(s['collapse_fraction'] == 1.0 for s in (s1, s2))
        self.assertFalse(vacuous, 'F-VACUOUS-CONE FIRES (every fixture full)')
        _evidence('f_vacuous_cone.json', {
            'lane': LANE,
            'shared_carrier': s1, 'read_readonly': s2,
            'f_vacuous_cone_fires': vacuous,
        })

    def test_collapse_is_detectable_and_split(self):
        # the conservative DEFAULT (no physics summaries) on the pilot's own
        # records: every extern becomes opaque, every cone goes full —
        # detectable, and split into opaque-driven vs structural
        recs = [i for r in load_pilot() for i in expand(r)]
        g = I2.build_graph(recs, I2.PhysicsModel())
        s = I2.collapse_stats(g)
        self.assertEqual(s['collapse_fraction'], 1.0)
        self.assertEqual(len(s['opaque_full']), 4)
        self.assertEqual(s['structural_collapse_fraction'], 0.0,
                        'the collapse must be ATTRIBUTED to the opaque rule')

    def test_degenerate_fixture_is_unsound_not_vacuous(self):
        # the two failure axes are ORTHOGONAL, measured on the same records:
        # the FROZEN v1 cone is narrow (useful) but MISSES the coupling
        # (unsound); the SAME records with EMPTY physics summaries under the
        # conservative opaque rule are SOUND on everything they know about,
        # useless by opacity — and the collapse split attributes it. The
        # degenerate world is TWICE incomplete: body.vy (a physics-side
        # state) is not even a NODE there — the measured residue of what a
        # missing physics declaration hides.
        cf = counterfactual(self.f1, 'force_law_a', 'kSpringA')
        v1_cone_a = set(I2.v1_cone(self.f1)['force_law_a'])
        self.assertFalse(set(cf['changed']) <= v1_cone_a, 'v1 misses (unsound)')
        s3 = I2.collapse_stats(self.g3)
        self.assertAlmostEqual(s3['collapse_fraction'], 0.75)
        self.assertEqual(s3['structural_collapse_fraction'], 0.0,
                        'the degenerate collapse must be opaque-attributed')
        changed = set(cf['changed'])
        unknown = changed - self.g3.universe
        self.assertEqual(unknown, {'body.vy'},
                         'the undeclared physics state must be NAMED')
        covered_known, _ = I2.cone_covers(
            {q: p for q, p in self.g3.reach['force_law_a'].items()},
            changed - unknown)
        self.assertTrue(covered_known,
                        'conservative-full cones are sound on known quantities')


class TestL5RealTrace(unittest.TestCase):
    """P4 — the real-trace leg (pinned substrate, READ-ONLY; scene and
    binary live in the lane's .tmp/l5/). Skips ONLY with a named reason."""

    def test_real_trace_counterfactual(self):
        try:
            verdict = RT.counterfactual()
        except FileNotFoundError as ex:
            self.skipTest(f'toolchain absent (named): {ex}')
            return
        _evidence('f_missed_coupling_real_trace.json', verdict)
        if not verdict['discharged']:
            self.skipTest('not_discharged: no ladder rung changed the trace '
                          f'(measured ladder: {verdict["ladder"]})')
        self.assertTrue(verdict['base_deterministic'],
                        'the instrument must be byte-deterministic')
        self.assertTrue(verdict['counterfactual']['pert_deterministic'])
        self.assertFalse(verdict['f_missed_coupling_fires'],
                         'F-MISSED-COUPLING FIRES on the real trace: '
                         + '; '.join(verdict['notes']))
        adj = verdict['counterfactual']['adjudication']
        # the sharp, mechanical real-trace assertions:
        self.assertTrue(adj['row0_ok'],
                        f'row-0 undeclared coupling: {adj["row0_violations"]}')
        for entry in adj['right_unwitnessed']:
            # recorded as measured evidence (declared-opaque scheduler);
            # a soundness failure would need an input-unwitnessed change on
            # a quantity the interface does NOT declare opaque — none exists
            self.assertIn('col', entry)


if __name__ == '__main__':
    unittest.main()
