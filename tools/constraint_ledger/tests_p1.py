"""P1 — the interference calculator against HAND-DERIVED ground truth.

FALSIFIER P1 (preregistration): any calculator verdict disagreeing with the
ground truth below fires. THE GROUND TRUTH IS SEALED: the expected verdicts
were fixed when this file was written, BEFORE the calculator was ever run
against them. A later hand-edit of a verdict to match calculator output is a
violation of the pre-registration.

Run: python -m unittest tools.constraint_ledger.tests_p1 -v
"""
from __future__ import annotations

import unittest

from . import interference as I
from .compile import compile_fragment, outputs_of
from .pilot_laws import load_pilot
from .schema import RecordError, expand, load

LANE = 'agent/constraint-ledger-20260921'


def rec(name, writes, delayed=(), same=(), kind='definition', quantities=None,
        initial=None, constants=None):
    """Synthetic record builder: `writes` = (target, expr) pairs."""
    quantities = dict(quantities or {})
    assigns = [{'write': w, 'expr': src} for w, src in writes]
    for w, _ in writes:
        if w not in quantities:
            quantities[w] = {'entity': 't', 'frame': 't', 'unit': '1',
                             'dtype': 'f64', 'phase': 'tick-start', 'role': 'state'}
    for q in list(delayed) + list(same):
        if q not in quantities:
            quantities[q] = {'entity': 't', 'frame': 't', 'unit': '1',
                             'dtype': 'f64', 'phase': 'tick-start',
                             'role': 'external-input'}
    initial = dict(initial or {})
    for w, _ in writes:
        initial.setdefault(w, 0.0)
    return load({
        'name': name, 'kind': kind, 'lane': LANE,
        'provenance': {'receipt': 'synthetic (P1 suite)', 'commit': 'n/a'},
        'falsifier': 'P1', 'params': {}, 'quantities': quantities,
        'assign': assigns, 'constants': constants or {}, 'initial': initial,
    })


def verdict(ix: I.Interaction) -> tuple:
    """Structured verdict: ('independent',) or ('potential', quantities,
    classes, directions)."""
    if ix.independent:
        return ('independent',)
    return ('potential',
            tuple(sorted(ix.quantities.items())),
            tuple(sorted(set(ix.quantities.values()))),
            tuple(sorted({d for ds in ix.directions.values() for d in ds})))


# ── the sealed ground truth (hand-derived, BEFORE any calculator run) ──────
# Law (amendment-1 item 3): independent(X,Y) iff
#   W_X ∩ (R_Y ∪ W_Y) = ∅  AND  W_Y ∩ (R_X ∪ W_X) = ∅.
# Shared reads never appear. Classes: write-write | combinational (now:)
# | stateful (delayed).
TRUTH_DISJOINT = ('independent',)
TRUTH_RW = ('potential', (('a', 'stateful'),), ('stateful',), ('X->Y',))
TRUTH_WW = ('potential', (('a', 'write-write'),), ('write-write',), ('X<->Y',))
TRUTH_INDEPENDENT2 = ('independent',)


class TestP1GroundTruth(unittest.TestCase):
    maxDiff = None

    def test_c01_disjoint(self):
        # X: writes a reads b | Y: writes c reads d.
        x = rec('x', [('a', 'b')], delayed=['b'])
        y = rec('y', [('c', 'd')], delayed=['d'])
        self.assertEqual(verdict(I.interaction(x, y)), TRUTH_DISJOINT)

    def test_c02_read_write_one_direction(self):
        # X writes a; Y reads a (delayed). W_X hits R_Y only.
        x = rec('x', [('a', 'b')], delayed=['b'])
        y = rec('y', [('c', 'a')], delayed=['a'])
        ix = I.interaction(x, y)
        self.assertEqual(verdict(ix), TRUTH_RW)
        self.assertEqual(ix.directions, {'a': ['X->Y']})

    def test_c03_write_write(self):
        x = rec('x', [('a', 'b')], delayed=['b'])
        y = rec('y', [('a', 'c')], delayed=['c'])
        self.assertEqual(verdict(I.interaction(x, y)), TRUTH_WW)

    def test_c04_shared_reads_harmless(self):
        # both read a, writes disjoint → independent (amendment-1 item 3)
        x = rec('x', [('b', 'a')], delayed=['a'])
        y = rec('y', [('c', 'a')], delayed=['a'])
        self.assertEqual(verdict(I.interaction(x, y)), TRUTH_INDEPENDENT2)

    def test_c05_transitive_alias_via_shared_quantity(self):
        # X writes a; Z reads a writes r; Y reads r.
        # [X,Y] DIRECT = 0; the alias travels X→Z→Y (cone depth 2).
        x = rec('x', [('a', 'm')], delayed=['m'])
        z = rec('z', [('r', 'a')], delayed=['a'])
        y = rec('y', [('c', 'r')], delayed=['r'])
        self.assertEqual(verdict(I.interaction(x, y)), TRUTH_DISJOINT)
        self.assertNotEqual(verdict(I.interaction(x, z)), TRUTH_DISJOINT)
        self.assertNotEqual(verdict(I.interaction(z, y)), TRUTH_DISJOINT)
        cone = I.build_cone([x, y, z], physics_edges=[])
        self.assertIn('c', cone.reach['x'],
                      'X must transitively reach Y through the shared chain')

    def test_c06_self_stateful_hysteresis(self):
        # a hysteresis law reads its own previous write: never independent
        # of itself (the wave-22 touch law's own shape)
        x = rec('x', [('a', 'if b > 0 then a else 0')], delayed=['b'],
                quantities={'a': {'entity': 't', 'frame': 't', 'unit': '1',
                                  'dtype': 'f64', 'phase': 'tick-start',
                                  'role': 'state'}})
        ix = I.interaction(x, x)
        self.assertEqual(ix.quantities, {'a': 'stateful'})

    def test_c07_parameterized_overlap_one_leg_only(self):
        # P writes touch.{leg} for both legs; Q reads touch.left only.
        # Expanded: Q×P[left] potential, Q×P[right] independent.
        p = load({
            'name': 'p', 'kind': 'definition', 'lane': LANE,
            'provenance': {'receipt': 'synthetic', 'commit': 'n/a'},
            'falsifier': 'P1', 'params': {'leg': ['left', 'right']},
            'quantities': {
                'touch.{leg}': {'entity': 't', 'frame': 't', 'unit': 'bool',
                                'dtype': 'bool', 'phase': 'tick-start',
                                'role': 'state'},
                'g.{leg}': {'entity': 't', 'frame': 't', 'unit': 'm',
                            'dtype': 'f64', 'phase': 'tick-start',
                            'role': 'external-input'}},
            'assign': [{'write': 'touch.{leg}', 'expr': 'g.{leg} > 0'}],
            'constants': {}, 'initial': {'touch.{leg}': False},
        })
        q = rec('q', [('out', 'touch.left')],
                quantities={'touch.left': {'entity': 't', 'frame': 't',
                                           'unit': 'bool', 'dtype': 'bool',
                                           'phase': 'tick-start',
                                           'role': 'external-input'}})
        insts = expand(p)
        left = next(i for i in insts if 'left' in i.name)
        right = next(i for i in insts if 'right' in i.name)
        # P1-3 CORRECTION (fired-falsifier report): Q reads touch.left with a
        # BARE (delayed) read, so the definition's class is 'stateful' with
        # the producer->reader direction Y->X (P writes, Q reads). The
        # original sealed assertion said combinational X->Y — that class
        # belongs to a now: read, which this fixture does not use.
        self.assertEqual(I.interaction(q, left).quantities,
                         {'touch.left': 'stateful'})
        self.assertEqual(I.interaction(q, left).directions,
                         {'touch.left': ['Y->X']})
        self.assertTrue(I.interaction(q, right).independent)

    def test_c08_now_is_combinational_c09_prev_is_stateful(self):
        x = rec('x', [('a', 'g')], delayed=['g'])
        y_now = rec('y_now', [('out', 'now:a')], same=['a'])
        y_prev = rec('y_prev', [('out2', 'a')], delayed=['a'])
        self.assertEqual(I.interaction(x, y_now).quantities,
                         {'a': 'combinational'})
        self.assertEqual(I.interaction(x, y_prev).quantities,
                         {'a': 'stateful'})

    def test_c10_physics_edge_transitive(self):
        # X writes tau; Y reads body.q — direct pair independent; the
        # REGISTERED physics edge (law → force → body state) couples them in
        # the cone; WITHOUT the edge the cone must not claim it (usefulness).
        x = rec('x', [('tau.left', 'g')], delayed=['g'])
        y = rec('y', [('c', 'body.q')], delayed=['body.q'])
        self.assertEqual(verdict(I.interaction(x, y)), TRUTH_DISJOINT)
        cone = I.build_cone([x, y], physics_edges=[('tau.left', 'body.q')])
        self.assertIn('body.q', cone.reach['x'])
        cone0 = I.build_cone([x, y], physics_edges=[])
        self.assertNotIn('body.q', cone0.reach['x'])

    def test_c11_both_ways_overlap(self):
        # X writes a reads b; Y writes b reads a — potential both directions.
        # P1-2 CORRECTION (fired-falsifier report, recorded 2026-09-21): the
        # SEALED expectation originally said a is 'write-write'. That was a
        # clerical error in the hand derivation, provable from the published
        # definition BEFORE the calculator ran: W_X∩W_Y = {a}∩{b} = ∅ (X
        # writes a, Y writes b) — no write-write exists; each side's write is
        # read DELAYED by the other, so both quantities are 'stateful' with
        # opposite directions. The definition is authoritative; the truth is
        # corrected TO the definition, never the calculator to the typo.
        x = rec('x', [('a', 'b')], delayed=['b'])
        y = rec('y', [('b', 'a')], delayed=['a'])
        ix = I.interaction(x, y)
        self.assertEqual(ix.quantities, {'a': 'stateful', 'b': 'stateful'})
        self.assertEqual(ix.directions['a'], ['X->Y'])
        self.assertEqual(ix.directions['b'], ['Y->X'])

    def test_c14_unknown_external_steers_conservatively(self):
        # X reads the OPAQUE quantity solver_out (unknown-code write) and
        # writes tau; Y reads tau; Z is disjoint. Truth (hand-derived from
        # the conservatism rule, amendment-1 item 3): X and Y are externally
        # steered; Z is not — and the pairwise set test is unchanged.
        x = rec('x', [('tau', 'solver_out')], delayed=['solver_out'])
        y = rec('y', [('c', 'tau')], delayed=['tau'])
        z = rec('z', [('d', 'w')], delayed=['w'])
        self.assertTrue(I.interaction(x, z).independent)
        cone = I.build_cone([x, y, z], physics_edges=[],
                            externals=['solver_out'])
        self.assertIn('x', cone.externally_steered)
        self.assertIn('y', cone.externally_steered,
                      'steering propagates down the read graph')
        self.assertNotIn('z', cone.externally_steered)

    def test_c12_invariants_conjoin_not_conflict(self):
        # two invariant-kind records over one quantity: no write effects →
        # never a write conflict; invariants CONJOIN (both must hold)
        inv = lambda n: load({
            'name': n, 'kind': 'invariant', 'lane': LANE,
            'provenance': {'receipt': 'synthetic', 'commit': 'n/a'},
            'falsifier': 'P1', 'params': {},
            'quantities': {'q': {'entity': 't', 'frame': 't', 'unit': '1',
                                 'dtype': 'f64', 'phase': 'decision',
                                 'role': 'external-input'}},
            'assign': [], 'constants': {}, 'initial': {},
            'invariant_expr': 'q <= 1'})
        self.assertTrue(I.interaction(inv('i1'), inv('i2')).independent)

    def test_c13_the_pilot_pair_names_exactly_the_touch_to_hold_edge(self):
        """THE REAL COMPOSITION on the shipped laws: the wave-22 touch record
        writes gait.touch.{leg}; the stand-first hold's arming predicate
        now:-reads it. Both delayed-read the pair-min gaps — read/read,
        harmless. Legs never cross-interact. [X,Y] == [Y,X] as a named term."""
        touch, hold = load_pilot()
        t_l = next(i for i in expand(touch) if 'left' in i.name)
        t_r = next(i for i in expand(touch) if 'right' in i.name)
        h_l = next(i for i in expand(hold) if 'left' in i.name)
        h_r = next(i for i in expand(hold) if 'right' in i.name)
        ix = I.interaction(t_l, h_l)
        self.assertEqual(ix.quantities, {'gait.touch.left': 'combinational'})
        self.assertEqual(ix.directions, {'gait.touch.left': ['X->Y']})
        ix_r = I.interaction(h_l, t_l)   # order-free: same named term
        self.assertEqual(ix_r.quantities, {'gait.touch.left': 'combinational'})
        self.assertEqual(ix_r.directions, {'gait.touch.left': ['Y->X']})
        for a, b in ((t_l, h_r), (h_l, t_r), (t_l, t_r), (h_l, h_r)):
            self.assertTrue(I.interaction(a, b).independent,
                            f'{a.name} x {b.name} must be independent')


# ── fragment rules (amendment-1 item 4): the compiler must REFUSE ─────────
class TestFragmentRules(unittest.TestCase):
    def _externals(self, names):
        return {n: {'entity': 't', 'frame': 't', 'unit': '1', 'dtype': 'f64',
                    'phase': 'tick-start', 'role': 'external-input'}
                for n in names}

    def test_ambiguous_writer_refused(self):
        a = rec('a', [('q', 'g')], delayed=['g'])
        b = rec('b', [('q', 'h')], delayed=['h'])
        with self.assertRaises(RecordError):
            compile_fragment([a, b], self._externals(['g', 'h']), {})

    def test_instantaneous_cycle_refused(self):
        a = rec('a', [('p', 'now:q')], same=['q'])
        b = rec('b', [('q', 'now:p')], same=['p'])
        with self.assertRaises(RecordError):
            compile_fragment([a, b], self._externals([]), {})

    def test_unspecified_initial_refused(self):
        spec = {
            'name': 'nostate', 'kind': 'definition', 'lane': LANE,
            'provenance': {'receipt': 'synthetic', 'commit': 'n/a'},
            'falsifier': 'P1', 'params': {},
            'quantities': {'s': {'entity': 't', 'frame': 't', 'unit': '1',
                                 'dtype': 'f64', 'phase': 'tick-start',
                                 'role': 'state'}},
            'assign': [{'write': 's', 'expr': 's + 1'}],
            'constants': {}, 'initial': {},
        }
        with self.assertRaises(RecordError):
            load(spec)

    def test_undeclared_read_refused(self):
        # the refusal fires at REGISTRATION (load-time declaration check)
        with self.assertRaises(RecordError):
            rec('a', [('q', 'ghost')], delayed=[])

    def test_write_to_external_refused(self):
        a = rec('a', [('g', '1')], delayed=[])
        with self.assertRaises(RecordError):
            compile_fragment([a], self._externals(['g']), {})

    def test_pilot_fragment_compiles_and_orders_touch_first(self):
        """The dependency edge (touch writes → hold now-reads) must order the
        touch record FIRST in the deterministic tick order — a property of
        the record SET, not of list order or append history."""
        from .pilot_laws import EXTERN_DECLS
        touch, hold = load_pilot()
        ext = {k: v for k, v in EXTERN_DECLS.items()}
        for pair in ([touch, hold], [hold, touch]):
            frag = compile_fragment(pair, ext, {})
            idx = lambda frag_, tag: next(i for i, n in enumerate(frag_.order_report)
                                          if n.startswith(tag))
            self.assertLess(idx(frag, 'touch_band'), idx(frag, 'stand_first_hold'),
                            'the touch record must precede the hold in every '
                            'leg group (the declared same-tick dependency)')
        frag = compile_fragment([touch, hold], ext, {})
        self.assertEqual(len(frag.state_keys()), 10)  # 2 touch + 8 hold states


# ── witness search (fixture-based commutativity discharge) ────────────────
class TestWitnessSearch(unittest.TestCase):
    @staticmethod
    def _e(names):
        return {n: {'entity': 't', 'frame': 't', 'unit': '1', 'dtype': 'f64',
                    'phase': 'tick-start', 'role': 'external-input'}
                for n in names}

    def test_order_sensitive_pair_yields_witness(self):
        # X: a := (g > 0.5);  Y: out := a (the value X just wrote). The two
        # staged updates in the swapped order read the STALE a — a concrete
        # commutativity witness, the discharge the interference verdict
        # demands before any independence claim (Servois-style, fixture-based).
        def step_x(s):
            out = dict(s)
            out['a'] = s['g'] > 0.5
            return out

        def step_y(s):
            out = dict(s)
            out['out'] = s['a']
            return out

        fixtures = [{'g': 0.4, 'a': False, 'out': 0.0},
                    {'g': 0.6, 'a': False, 'out': 0.0},
                    {'g': 0.6, 'a': True, 'out': 0.0}]
        observe = lambda s: (s['a'], s['out'])
        w = I.commutativity_witness(step_x, step_y, fixtures, observe)
        self.assertIsNotNone(w, 'an order-sensitive pair must yield a witness')
        # and the witnessed divergence names the tick where the orders differ
        self.assertNotEqual(w['obs_x_after_y'], w['obs_y_after_x'])

    def test_independent_pair_has_no_witness(self):
        x = rec('x', [('a', 'g')], delayed=['g'])
        y = rec('y', [('b', 'h')], delayed=['h'])
        fx = compile_fragment([x], self._e(['g']), {})
        fy = compile_fragment([y], self._e(['h']), {})
        fixtures = [{'g': 1.0, 'h': 2.0, 'a': 0.0, 'b': 0.0},
                    {'g': 3.0, 'h': 4.0, 'a': 9.0, 'b': 9.0}]

        def step_x(s):
            same, st = outputs_of(fx, {k: s[k] for k in fx.state_keys()}, s, s, 0)
            out = dict(s)
            out.update(st)
            out['a'] = same['a']
            return out

        def step_y(s):
            same, st = outputs_of(fy, {k: s[k] for k in fy.state_keys()}, s, s, 0)
            out = dict(s)
            out.update(st)
            out['b'] = same['b']
            return out

        w = I.commutativity_witness(step_x, step_y, fixtures,
                                    lambda s: (s['a'], s['b']))
        self.assertIsNone(w, 'independent records must commute on every fixture')


if __name__ == '__main__':
    unittest.main()
