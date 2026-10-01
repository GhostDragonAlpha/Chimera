"""L7 tests — the evidence cache with semantic-dependency invalidation and
the replay-reuse certificate (agent/cl-L7-reuse-20260921).

FALSIFIER PROBES (preregistration, tools/science_funnel/validation/
cl_L7_20260921/preregistration.md):
  F-STALE-CERTIFICATE      fixtures (a) producer, (b) reset rule, (c) numeric
                           policy: one VALID verdict on any fires.
  F-UNJUSTIFIED-RERUN-SKIP a rerun waiver granted with any certificate
                           assumption not holding fires.
  F-OVER-INVALIDATE        fixture (d) metadata label: an INVALIDATED verdict
                           (or a silent drift) fires.

Fixtures run on the REAL pilot records (pilot_laws.load_pilot) and the REAL
registered substrate (scene f6844eea..., pilot trace eaff3238..., 302 lines,
refusal 300) for the certificate path.

Run: python -m unittest tools.constraint_ledger.tests_reuse -v
"""
from __future__ import annotations

import copy
import json
import struct
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from tools.constraint_ledger import reuse as R
from tools.constraint_ledger.pilot_laws import (TOUCH_BAND, STAND_FIRST_HOLD,
                                                concrete_externals, load_pilot)
from tools.constraint_ledger.schema import content_digest, load as load_rec
from tools.constraint_ledger.tests_p2 import bits_of, load_trace

SCENE = ROOT / '.tmp/gait-walker/scene.json'

HORIZON_PILOT = {'walk_ticks': 300, 'rows_expected': 301,
                 'stop': 'refusal gait_positional_correction_budget @ tick 300'}


def _scene_pin():
    """The REAL registered scene digest when the scene exists (the lane
    substrate); a stable pin otherwise."""
    import hashlib
    if SCENE.exists():
        return hashlib.sha256(SCENE.read_bytes()).hexdigest()
    return 'scene-pin'


def deps_of(touch_spec, hold_spec, **kw):
    """Dependency set over a two-record set given as SPECS (templates)."""
    recs = [load_rec(touch_spec), load_rec(hold_spec)]
    return R.compute_dependencies(
        recs,
        scene_digest=kw.pop('scene_digest', _scene_pin()),
        externals_digest=R.digest_of(concrete_externals()),
        horizon=kw.pop('horizon', HORIZON_PILOT),
        baseline=kw.pop('baseline', 'tree-pin'), **kw)


def pilot_specs():
    return copy.deepcopy(TOUCH_BAND), copy.deepcopy(STAND_FIRST_HOLD)


class TestClosure(unittest.TestCase):
    """P-CLOSURE: the producer closure of the two-law set is EXACTLY the two
    records, with the single same-tick composition edge named."""

    def test_closure_names_exactly_the_composition_edge(self):
        touch, hold = load_pilot()
        closure = R.producer_closure([touch, hold])
        self.assertEqual(sorted(closure), ['stand_first_hold', 'touch_band'])
        self.assertEqual(closure['touch_band'], [],
                         'the touch band reads no record-input')
        self.assertEqual(closure['stand_first_hold'],
                         ['gait.touch.left', 'gait.touch.right'],
                         'the hold law\'s record-input reads ARE the '
                         'composition edge to the touch producer')
        # the via quantities must be DECLARED record-input in the hold law
        from tools.constraint_ledger.schema import expand
        roles = {q.name: q.role for inst in expand(hold)
                 for q in inst.quantities.values()}
        for q in closure['stand_first_hold']:
            self.assertEqual(roles[q], 'record-input', q)

    def test_missing_producer_refuses_not_underapproximates(self):
        from tools.constraint_ledger.schema import load as _load
        consumer = _load({
            'name': 'orphan_consumer', 'kind': 'definition',
            'lane': 'test', 'provenance': {}, 'falsifier': 'test',
            'quantities': {
                'x.in': {'entity': 'e', 'frame': 'f', 'unit': '1',
                         'dtype': 'f64', 'phase': 'tick-start',
                         'role': 'record-input'},
                'x.out': {'entity': 'e', 'frame': 'f', 'unit': '1',
                          'dtype': 'f64', 'phase': 'tick-start',
                          'role': 'state'}},
            'initial': {'x.out': 0.0},
            'assign': [{'write': 'x.out', 'expr': 'x.in + 1'}],
        })
        with self.assertRaises(R.ReuseError) as ctx:
            R.producer_closure([consumer])
        self.assertIn('no producer', str(ctx.exception))


class TestFourFixtures(unittest.TestCase):
    """THE INVALIDATION FIXTURES. (a) producer, (b) reset rule, (c) numeric
    policy -> MUST invalidate. (d) irrelevant metadata label -> MUST NOT."""

    @classmethod
    def setUpClass(cls):
        cls.touch0, cls.hold0 = pilot_specs()
        cls.base = deps_of(cls.touch0, cls.hold0)

    def test_a_input_producer_change_invalidates(self):
        # (a1) a producer CONSTANT changes (kTouch 1e-5 -> 2e-5, the machinery
        # touch quantum): a semantic change to a producer of the set.
        a1 = copy.deepcopy(self.touch0)
        a1['constants']['kTouch']['value'] = 2e-5
        v = R.check_validity(self.base, deps_of(a1, self.hold0))
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertTrue(any('touch_band' in r and 'SEMANTIC' in r
                            for r in v.reasons), v.reasons)
        # (a2) a producer EXPRESSION changes (same-tick hold, not the latch):
        a2 = copy.deepcopy(self.touch0)
        a2['assign'][0]['expr'] = (
            'if gait.hind.pairmin_gap.{leg} < kTouch then true '
            'else if gait.hind.pairmin_gap.{leg} > kTouch + kReleaseBand '
            'then false else gait.touch.{leg}')
        v = R.check_validity(self.base, deps_of(a2, self.hold0))
        self.assertEqual(v.status, 'INVALIDATED', v.reasons)

    def test_b_reset_rule_change_invalidates(self):
        # (b1) the reset EVENT changes (a mid-run reset is a different rule).
        b1 = deps_of(self.touch0, self.hold0, reset_event={
            'event': {'reset': True}, 'at': 'configure, before tick 0',
            'extra': 'mid-run reset at tick 150'})
        self.assertNotEqual(b1.reset, self.base.reset)
        v = R.check_validity(self.base, b1)
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertTrue(any('reset' in r for r in v.reasons), v.reasons)
        # (b2) a declared INITIAL changes (anchor 0.0 -> 1.0 bits): the reset
        # rule's other half.
        b2h = copy.deepcopy(self.hold0)
        b2h['initial']['gait.hold.anchor_y.{leg}'] = 1.0
        v = R.check_validity(self.base, deps_of(self.touch0, b2h))
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertTrue(any('reset' in r for r in v.reasons), v.reasons)

    def test_c_numeric_policy_change_invalidates(self):
        # /fp:precise -> /fp:fast: the numeric policy is a dependency class.
        policy = dict(R.NUMERIC_POLICY_PILOT, fp_flags='/fp:fast')
        c = deps_of(self.touch0, self.hold0, numeric_policy=policy)
        self.assertNotEqual(c.numeric_policy, self.base.numeric_policy)
        v = R.check_validity(self.base, c)
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertTrue(any('numeric_policy' in r for r in v.reasons), v.reasons)

    def test_d_irrelevant_metadata_label_does_not_invalidate(self):
        # provenance receipt path + falsifier text + lane: citation, not
        # semantics. The FULL content digest MUST change (else this fixture
        # proves nothing) while the SEMANTIC digest is unchanged, and the
        # verdict MUST stay VALID with the drift RECORDED.
        d = copy.deepcopy(self.touch0)
        d['provenance']['receipt'] = 'elsewhere/receipt_renamed.json'
        d['provenance']['note'] = 'a relabeled citation'
        d['falsifier'] = 'P2 (relabeled)'
        d['lane'] = 'some/other-lane'
        drec = load_rec(d)
        self.assertNotEqual(content_digest(drec), self.base.records['touch_band']['content_sha'],
                            'fixture (d) must change the content digest')
        self.assertEqual(R.semantic_digest(drec),
                         self.base.records['touch_band']['semantic_sha'],
                         'fixture (d) must NOT change the semantic digest')
        v = R.check_validity(self.base, deps_of(d, self.hold0))
        self.assertEqual(v.status, 'VALID',
                         'F-OVER-INVALIDATE would fire: ' + str(v.reasons))
        self.assertEqual(v.reasons, [])
        self.assertEqual(len(v.identity_drift), 1, v.identity_drift)
        self.assertEqual(v.identity_drift[0]['record'], 'touch_band')
        self.assertEqual(v.identity_drift[0]['kind'], 'metadata-only')

    def test_horizon_and_domain_changes_invalidate(self):
        h = dict(HORIZON_PILOT, walk_ticks=150)
        v = R.check_validity(self.base, deps_of(self.touch0, self.hold0, horizon=h))
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertTrue(any('horizon' in r for r in v.reasons), v.reasons)
        v = R.check_validity(self.base, deps_of(self.touch0, self.hold0,
                                                scene_digest='scene-other'))
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertTrue(any('domain' in r for r in v.reasons), v.reasons)


class TestEvidenceCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = R.EvidenceCache(Path(self.tmp.name) / 'cache.jsonl')
        self.touch0, self.hold0 = pilot_specs()
        self.base = deps_of(self.touch0, self.hold0)

    def tearDown(self):
        self.tmp.cleanup()

    def test_put_lookup_miss_valid_stale_tamper(self):
        self.assertEqual(self.cache.lookup('k', self.base).status, 'MISS')
        self.cache.put('k', {'claim': 'S reproduces T bit-exact'}, self.base)
        v = self.cache.lookup('k', self.base)
        self.assertEqual(v.status, 'VALID')
        # a semantic change makes reuse STALE — the falsifier is named
        a = copy.deepcopy(self.touch0)
        a['constants']['kTouch']['value'] = 2e-5
        v = self.cache.lookup('k', deps_of(a, self.hold0))
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertEqual(v.falsifier, R.F_STALE_CERTIFICATE)
        # a metadata change keeps the cache VALID (drift noted, never silent:
        # the entry records full content digests so the drift is auditable)
        d = copy.deepcopy(self.touch0)
        d['provenance']['receipt'] = 'renamed.json'
        v = self.cache.lookup('k', deps_of(d, self.hold0))
        self.assertEqual(v.status, 'VALID')
        self.assertEqual(len(v.identity_drift), 1)
        # tampering with the sealed entry is caught (I3)
        p = Path(self.tmp.name) / 'cache.jsonl'
        e = json.loads(p.read_text().splitlines()[0])
        e['deps']['reset'] = '0' * 64
        p.write_text(json.dumps(e, sort_keys=True, separators=(',', ':')) + '\n')
        cache2 = R.EvidenceCache(p)
        v = cache2.lookup('k', self.base)
        self.assertEqual(v.status, 'INVALIDATED')
        self.assertIn('tampered', v.reasons[0])


class TestReplayReuseCertificate(unittest.TestCase):
    """The certificate over the REAL registered substrate, then the waiver
    gate: granted only while every assumption holds; otherwise the firing
    falsifier is NAMED."""

    @classmethod
    def setUpClass(cls):
        cls.meta, cls.rows = load_trace()   # regenerates scene/harness/trace
        cls.deps = deps_of(*pilot_specs())
        cls.ledger = build_real_replay_ledger(cls.rows)

    def test_ledger_complete_and_lossless_on_real_trace(self):
        ok, why = self.ledger.complete(HORIZON_PILOT)
        self.assertTrue(ok, why)
        self.assertGreater(self.ledger.rows, 0)
        self.assertGreater(self.ledger.boundary_outputs_checked, 0)
        self.assertGreater(self.ledger.state_transitions_checked, 0)
        self.assertGreater(self.ledger.bit_pairs_checked, 0)

    def _cert(self):
        return R.issue_certificate(self.deps, self.ledger, physics_pin(),
                                   determinism_pin(), HORIZON_PILOT)

    def test_certificate_issues_and_seals(self):
        cert = self._cert()
        self.assertTrue(cert.claim.startswith('same-trajectory-by-induction'))
        self.assertTrue(cert.induction.startswith('same-trajectory-by-induction'))
        self.assertEqual(cert.digest, cert.seal().digest)   # stable seal
        self.assertEqual(cert.digest, R.ReplayReuseCertificate(
            claim=cert.claim, deps=cert.deps, match=cert.match,
            physics=cert.physics, determinism=cert.determinism,
            induction=cert.induction).seal().digest)
        # the recorded assumptions are exactly the dependency classes
        self.assertIn('reset', cert.deps.canonical())
        self.assertIn('numeric_policy', cert.deps.canonical())
        self.assertIn('horizon', cert.deps.canonical())

    def test_issue_refuses_tampered_bit_and_lossy_ledger(self):
        # ONE flipped state-transition bit: the match is no longer complete.
        import dataclasses
        bad = dataclasses.replace(self.ledger)
        bad.mismatches = [{'tick': 17, 'quantity': 'gait.hold.anchor_y.left',
                           'expected_bits': self.ledger.bit_pairs_checked,
                           'actual_bits': self.ledger.bit_pairs_checked ^ 1}]
        with self.assertRaises(R.ReuseError) as ctx:
            R.issue_certificate(self.deps, bad, physics_pin(),
                                determinism_pin(), HORIZON_PILOT)
        self.assertIn('mismatch', str(ctx.exception))
        # a DECIMAL-only (lossy) ledger must refuse even with zero mismatches
        import dataclasses
        lossy = dataclasses.replace(self.ledger, lossless=False)
        with self.assertRaises(R.ReuseError) as ctx:
            R.issue_certificate(self.deps, lossy, physics_pin(),
                                determinism_pin(), HORIZON_PILOT)
        self.assertIn('lossless', str(ctx.exception))
        # determinism unmeasured must refuse
        with self.assertRaises(R.ReuseError) as ctx:
            R.issue_certificate(self.deps, self.ledger, physics_pin(),
                                {'double_run_byte_identical': False,
                                 'rng': 'none', 'env_or_clock_inputs': 'none'},
                                HORIZON_PILOT)
        self.assertIn('determinism', str(ctx.exception))

    def test_waiver_granted_while_assumptions_hold(self):
        cert = self._cert()
        w = R.grant_rerun_waiver(cert, deps_of(*pilot_specs()),
                                 physics_pin(), HORIZON_PILOT)
        self.assertTrue(w['granted'], w)
        self.assertIsNone(w['falsifier'])
        self.assertEqual(w['identity_drift'], [])

    def test_waiver_refused_on_dependency_drift_names_F_STALE(self):
        cert = self._cert()
        a = copy.deepcopy(TOUCH_BAND)
        a['constants']['kTouch']['value'] = 2e-5     # producer semantic change
        w = R.grant_rerun_waiver(cert, deps_of(a, STAND_FIRST_HOLD),
                                 physics_pin(), HORIZON_PILOT)
        self.assertFalse(w['granted'])
        self.assertEqual(w['falsifier'], R.F_STALE_CERTIFICATE, w)
        self.assertTrue(w['details'], w)
        # metadata-only drift does NOT break the waiver (semantics unchanged)
        # — it is RECORDED on the granted waiver, never silent
        d = copy.deepcopy(TOUCH_BAND)
        d['provenance']['receipt'] = 'renamed.json'
        w = R.grant_rerun_waiver(cert, deps_of(d, STAND_FIRST_HOLD),
                                 physics_pin(), HORIZON_PILOT)
        self.assertTrue(w['granted'], w)
        self.assertEqual(len(w['identity_drift']), 1, w)
        self.assertEqual(w['identity_drift'][0]['record'], 'touch_band')

    def test_waiver_refused_on_physics_or_determinism_names_F_SKIP(self):
        cert = self._cert()
        w = R.grant_rerun_waiver(
            cert, deps_of(*pilot_specs()),
            dict(physics_pin(), source_tree_digest='a-different-tree'),
            HORIZON_PILOT)
        self.assertFalse(w['granted'])
        self.assertEqual(w['falsifier'], R.F_UNJUSTIFIED_RERUN_SKIP, w)
        w = R.grant_rerun_waiver(
            cert, deps_of(*pilot_specs()), physics_pin(),
            dict(HORIZON_PILOT, walk_ticks=600))     # horizon not covered
        self.assertFalse(w['granted'])
        self.assertEqual(w['falsifier'], R.F_UNJUSTIFIED_RERUN_SKIP, w)
        # a hand-built "certificate" whose determinism was never measured:
        bad = R.ReplayReuseCertificate(
            claim=R.INDUCTION_CLAIM, deps=cert.deps, match=cert.match,
            physics=physics_pin(),
            determinism={'double_run_byte_identical': False, 'rng': '?',
                         'env_or_clock_inputs': '?'},
            induction=R.INDUCTION_CLAIM).seal()
        w = R.grant_rerun_waiver(bad, deps_of(*pilot_specs()),
                                 physics_pin(), HORIZON_PILOT)
        self.assertFalse(w['granted'])
        self.assertEqual(w['falsifier'], R.F_UNJUSTIFIED_RERUN_SKIP, w)


class TestEconomics(unittest.TestCase):
    """P-CERTIFICATE's cost half: the reuse decision must cost orders of
    magnitude less than a re-run. Measured here at µs scale; the re-run
    costs are measured in the lane experiment log (harness ~10.5 s; the
    operator's declared full-run verification ~10 min)."""

    def test_reuse_check_latency_measured(self):
        base = deps_of(*pilot_specs())
        cache = R.EvidenceCache(Path(tempfile.mkdtemp()) / 'c.jsonl')
        cache.put('k', {'claim': 'x'}, base)
        cur = deps_of(*pilot_specs())
        t0 = time.perf_counter()
        n = 2000
        for _ in range(n):
            v = cache.lookup('k', cur)
        dt = time.perf_counter() - t0
        self.assertEqual(v.status, 'VALID')
        per_us = dt / n * 1e6
        print(f'\n[L7 economics] dependency recompute + invalidation check: '
              f'{per_us:.0f} us/check ({n} checks in {dt*1e3:.0f} ms)')
        t0 = time.perf_counter()
        for _ in range(200):
            deps_of(*pilot_specs())
        dt2 = time.perf_counter() - t0
        print(f'[L7 economics] full closure computation: '
              f'{dt2/200*1e6:.0f} us/compute')
        # the reuse decision is at least 10^5x cheaper than the measured
        # ~10.5 s harness re-run and ~10^6x cheaper than the declared ~600 s
        # full-run verification (a bound, not a tuned threshold)
        self.assertLess(dt / n, 0.105,
                        'reuse check must not approach the harness re-run cost')


# ── helpers: the REAL replay ledger over the registered trace ───────────────
def physics_pin():
    import subprocess
    tree = subprocess.run(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    return {'source_tree_digest': tree,
            'numeric_policy_sha': R.digest_of(R.NUMERIC_POLICY_PILOT),
            'toolchain': 'g++ 15.2.0 (MinGW-Builds) -O2 -std=c++17 '
                         '(trace_harness.cpp, the observation instrument)'}


def determinism_pin():
    return {'double_run_byte_identical': True,     # measured in the lane log:
            'rng': 'none (no srand/rand/mt19937/random_device at the pin)',
            'env_or_clock_inputs': 'none in the trajectory'}


def _bundles(rows, j):
    prev_row, now_row = rows[j - 1], rows[j]
    prev, now = {}, {}
    for leg, name in ((0, 'left'), (1, 'right')):
        g0, g1 = prev_row['gaps'][2 * leg], prev_row['gaps'][2 * leg + 1]
        prev[f'gait.hind.pairmin_gap.{name}'] = min(g0, g1)
        prev[f'gait.hind.mode.{name}'] = int(prev_row['leg'][leg]['mode'])
        prev[f'gait.hind.t.{name}'] = float(prev_row['leg'][leg]['t'])
        prev[f'gait.hind.heel_y.{name}'] = prev_row['leg'][leg]['heel_y']
        prev[f'gait.hind.mp_y.{name}'] = prev_row['leg'][leg]['mp_y']
        now[f'gait.fire.{name}'] = (now_row['leg'][leg]['fires']
                                    > prev_row['leg'][leg]['fires'])
        now[f'gait.hind.phase.{name}'] = now_row['leg'][leg]['phase']
    prev.update(now)
    return prev, now


def build_real_replay_ledger(rows):
    """The P2 replay (compile.py machinery, UNCHANGED modules) with the
    match ledger counted: every boundary output + the float next-state
    transition BITS, inputs verified lossless by decimal<->bits round-trip."""
    from tools.constraint_ledger.compile import compile_fragment, outputs_of
    from tools.constraint_ledger.pilot_laws import concrete_externals, load_pilot
    touch, hold = load_pilot()
    frag = compile_fragment([touch, hold], concrete_externals(), {})
    state = dict(frag.initial)
    # the induction BASE: row 0 equals the declared reset/initial state
    r0 = rows[0]
    row0_ok = (r0['touch'] == [False, False]
               and all(leg['held'] == False and leg['clear_tick'] == -1
                       and leg['fire_class'] == 0
                       and leg['plant_y_bits'] == bits_of(0.0)
                       and leg['mode'] == 0 and leg['t'] == 0
                       for leg in r0['leg']))   # noqa: E712 (JSON ints 0/1)
    outputs = transitions = bit_pairs = 0
    mismatches = []

    def cmp(qname, got, want, j):
        nonlocal outputs
        outputs += 1
        if isinstance(want, bool):
            got = bool(got)
        if got != want:
            mismatches.append({'tick': j, 'quantity': qname,
                               'expected': want, 'actual': got})

    for j in range(1, len(rows)):
        row = rows[j]
        # inputs lossless? (decimal <-> bits round-trip on the consumed gaps)
        for k in range(4):
            bit_pairs += 1
            if bits_of(row['gaps'][k]) != row['gaps_bits'][k]:
                mismatches.append({'tick': j, 'quantity': f'gaps[{k}]',
                                   'loss': 'decimal does not round-trip'})
        prev, now = _bundles(rows, j)
        same, state = outputs_of(frag, state, prev, now, j - 1)
        cmp('gait.touch.left', same['gait.touch.left'], row['touch'][0], j)
        cmp('gait.touch.right', same['gait.touch.right'], row['touch'][1], j)
        for leg, name in ((0, 'left'), (1, 'right')):
            lg = row['leg'][leg]
            cmp(f'gait.hold.armed.{name}', same[f'gait.hold.armed.{name}'],
                bool(lg['held']), j)
            cmp(f'gait.hold.release_tick.{name}',
                same[f'gait.hold.release_tick.{name}'], lg['clear_tick'], j)
            cmp(f'gait.hold.fire_class.{name}',
                same[f'gait.hold.fire_class.{name}'], lg['fire_class'], j)
            # the float NEXT-STATE transition, BITS not decimals (the floor
            # anchor): a state transition, not an output
            transitions += 1
            bit_pairs += 1
            if bits_of(same[f'gait.hold.anchor_y.{name}']) != lg['plant_y_bits']:
                mismatches.append({'tick': j,
                                   'quantity': f'gait.hold.anchor_y.{name}',
                                   'expected_bits': lg['plant_y_bits'],
                                   'actual_bits': bits_of(
                                       same[f'gait.hold.anchor_y.{name}'])})
        if mismatches:
            break
    return R.ReplayMatchLedger(
        rows=len(rows), boundary_outputs_checked=outputs,
        state_transitions_checked=transitions, bit_pairs_checked=bit_pairs,
        mismatches=mismatches, lossless=True,
        row0_matches_declared_initial=row0_ok, horizon_covered=HORIZON_PILOT)


if __name__ == '__main__':
    unittest.main()
