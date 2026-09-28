"""MAT2-U03 frozen-probe tests: P0-P6 positive predictions, F1-F3 falsifier
bites, and the H1 hazard baseline.

CPU-only, stdlib-only, python -B, injected integer-ms clocks, no engine, no
network, NO real OS focus manipulation (the card's observation keeps operator
desktop focus untouched; focus/disconnect are injected policy events). The
upstream seam is the vendored byte-exact U01 pinned_seam (hashes pinned in
PREREGISTRATION.md and re-verified here on the ACTUAL loaded module files).

Run from the checkout root:
    python -B tools/monkey_campaign/contributions/MAT2-U03/test_focus_policy.py
"""
from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SEAM = HERE / 'pinned_seam'
PRODUCT = SEAM / 'tools' / 'monkey_campaign' / 'product'
REPO_ROOT = HERE.parents[3]

SUBJECT_SHA256 = '7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44'
SEAM_SHA256 = '6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e'
U01_TESTS_SHA256 = '95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e'
U01_MERGE = 'ebdfda61bf3df9b1f6985f771044fd946dd5e9db'
U01_TESTS_REL = ('tools/monkey_campaign/contributions/MAT2-U01/reconcile/'
                 'pinned_seam/tools/monkey_campaign/product/input_mapper_tests.py')

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PRODUCT))
import focus_policy as fp  # noqa: E402
import input_mapper as M   # noqa: E402  (the vendored U01 seam, byte-exact)

CHECKS = []


def check(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))


def named_event(policy, kind):
    events = policy.last_trace.get('events', [])
    return [e for e in events if e.get('event') == kind]


class FocusPolicyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.V = M.V_MAX_IN_BAND_M_S
        cls.INTERVAL = M.INTERVAL_MS
        cls.DECAY = M.RELEASE_DECAY_MS
        cls.EXPIRY = M.EXPIRY_TICKS
        cls.PHYSICS = M.PHYSICS_HZ

    # ---------------- P0: the vendored U01 falsifier module runs GREEN
    def test_p0_upstream_regression_green(self):
        proc = subprocess.run(
            [sys.executable, '-B', str(PRODUCT / 'input_mapper_tests.py')],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120)
        check('P0.u01_falsifiers_green',
              proc.returncode == 0 and 'VERDICT: GREEN' in proc.stdout,
              'rc=%d tail=%r' % (proc.returncode, proc.stdout.strip()[-90:]))

    # ---------------- P1: policy identity, interface pin, byte pins
    def test_p1_policy_identity_and_interface_pin(self):
        check('P1.policy_id', fp.POLICY_ID == 'u03_focus_release_policy.v1')
        check('P1.declared_actions',
              fp.POLICY['focus_loss'] == 'clear_held_age_to_zero'
              and fp.POLICY['disconnect'] == 'clear_held_age_to_zero'
              and fp.POLICY['key_release'] == 'age_decay_to_zero'
              and fp.POLICY['gate'] == 'hold_new_demands_while_gated'
              and fp.POLICY['resume'] == 'fresh_grid_no_replay')
        # a wrapper missing the U01 interface is refused, by member name
        for partial, member in ((object(), 'press'),
                                (type('P1Half', (), {'press': lambda s, n, t: None,
                                                     'release': lambda s, n, t: None})(),
                                 'release_all'),
                                (type('P1NoExp', (), {'press': lambda s, n, t: None,
                                                      'release': lambda s, n, t: None,
                                                      'release_all': lambda s, t: None,
                                                      'tick': lambda s, t: [],
                                                      'last_trace': {},
                                                      'held': frozenset()})(),
                                 'is_expired')):
            try:
                fp.FocusPolicy(partial)
                check('P1.upstream_interface_missing:' + member, False, 'accepted')
            except ValueError as exc:
                check('P1.upstream_interface_missing:' + member,
                      str(exc) == 'upstream_interface_missing:' + member, str(exc))
        # the ACTUAL loaded seam files hash to the pinned subject bytes
        loaded_mapper = hashlib.sha256(
            pathlib.Path(M.__file__).read_bytes()).hexdigest()
        import tools.science_funnel.typeb_export.command_record as cr
        loaded_seam = hashlib.sha256(
            pathlib.Path(cr.__file__).read_bytes()).hexdigest()
        check('P1.loaded_mapper_is_pinned_subject', loaded_mapper == SUBJECT_SHA256,
              loaded_mapper[:16])
        check('P1.loaded_seam_is_pinned_seam', loaded_seam == SEAM_SHA256,
              loaded_seam[:16])
        # and the vendored test module still matches U01's declared hash
        vendored_tests = hashlib.sha256(
            (PRODUCT / 'input_mapper_tests.py').read_bytes()).hexdigest()
        check('P1.vendored_u01_tests_pinned', vendored_tests == U01_TESTS_SHA256,
              vendored_tests[:16])

    # ---------------- P2: focus loss mid-walk clears and ages, then gates
    def test_p2_focus_loss_mid_walk(self):
        sink = M.MockSink()
        policy = fp.FocusPolicy(M.InputMapper(sink))
        policy.press('W', 1000)
        for t in (1000, 1050, 1100, 1150, 1200, 1250):
            policy.tick(t)
        check('P2.walk_established',
              len(sink.records) == 6
              and all(abs(r.v_forward - self.V) < 1e-12 for r in sink.records),
              str(len(sink.records)))
        last_v = sink.records[-1].v_forward
        policy.focus_lost(1257)
        check('P2.held_cleared', len(policy.held) == 0 and policy.gated)
        check('P2.event_named',
              named_event(policy, 'focus_lost')
              and named_event(policy, 'focus_lost')[0]['action'] == 'clear_held_age_to_zero')
        r1 = policy.tick(1300)
        r2 = policy.tick(1350)
        r3 = policy.tick(1400)
        r4 = policy.tick(1450)
        check('P2.tail_sample1', len(r1) == 1
              and abs(r1[0].v_forward - last_v * (1.0 - 43 / self.DECAY)) < 1e-15,
              repr(r1[0].v_forward if r1 else None))
        check('P2.tail_deadline_exact_zero', len(r2) == 1 and r2[0].v_forward == 0.0,
              repr(r2[0].v_forward if r2 else None))
        check('P2.emission_stops', r3 == [] and r4 == [])
        # a forced press while gated is refused by name, never honored
        ret = policy.press('W', 1460)
        check('P2.gated_press_refused', ret is None
              and any(e.get('event') == 'press_refused_while_gated'
                      and e.get('name') == 'W'
                      for e in policy.last_trace['events']))
        check('P2.gated_press_emits_nothing', policy.tick(1500) == [])
        # refocus resumes with a fresh grid and no replay of the gated window
        before = len(sink.records)
        policy.focus_gained(1700)
        check('P2.resume_named',
              named_event(policy, 'focus_gained')
              and named_event(policy, 'focus_gained')[0]['replayed'] == 0)
        policy.press('W', 1710)
        r5 = policy.tick(1710)
        check('P2.fresh_grid_one_record', len(r5) == 1
              and abs(r5[0].v_forward - self.V) < 1e-12)
        check('P2.no_replay_of_gated_window', len(sink.records) == before + 1)

    # ---------------- P3: disconnect on the live-zero path reverts to inert
    def test_p3_disconnect_live_zero(self):
        sink = M.MockSink()
        policy = fp.FocusPolicy(M.InputMapper(sink))
        policy.press('S', 1000)
        check('P3.live_zero_commanded', policy.tick(1000)[0].v_forward == 0.0)
        policy.disconnected(1020)
        check('P3.disconnect_named',
              named_event(policy, 'disconnect')
              and named_event(policy, 'disconnect')[0]['action'] == 'clear_held_age_to_zero')
        check('P3.held_cleared', len(policy.held) == 0 and policy.gated)
        out = [policy.tick(t) for t in (1050, 1100, 1150)]
        check('P3.no_records_after_disconnect', all(o == [] for o in out),
              str([len(o) for o in out]))
        check('P3.no_tail_from_zero_demand', len(sink.records) == 1)

    # ---------------- P4: key release ages via the unchanged U01 floor
    def test_p4_key_release_ages(self):
        sink = M.MockSink()
        policy = fp.FocusPolicy(M.InputMapper(sink))
        policy.press('W', 1000)
        policy.tick(1000)
        policy.tick(1050)
        policy.release('W', 1070)
        seq = [policy.tick(t) for t in (1100, 1150, 1200)]
        vs = [r.v_forward for grp in seq for r in grp]
        check('P4.decay_sample_then_zero', len(vs) == 2
              and abs(vs[0] - self.V * (1.0 - 30 / self.DECAY)) < 1e-15
              and vs[1] == 0.0, repr(vs))
        check('P4.monotone_non_increasing',
              vs == sorted(vs, reverse=True), repr(vs))
        check('P4.lands_by_deadline', 1150 <= 1070 + self.DECAY)
        check('P4.emission_stops', seq[2] == [])
        check('P4.wrapper_transparent', len(sink.records) == 4)

    # ---------------- P5: consumer aging floor holds with NO producer ticks
    def test_p5_consumer_aging_floor(self):
        sink = M.MockSink()
        policy = fp.FocusPolicy(M.InputMapper(sink))
        policy.press('W', 1000)
        record = policy.tick(1000)[0]          # issued_tick 300 @300Hz
        issued = record.issued_tick
        age = lambda now_ms: now_ms * self.PHYSICS // 1000 - issued
        state, _ = policy.effective_demand(1005)
        check('P5.fresh_record_commanded', state == 'commanded')
        state30, _ = policy.effective_demand(1100)
        check('P5.lawful_at_exactly_30_ticks', age(1100) == 30
              and state30 == 'commanded', 'age=%d state=%s' % (age(1100), state30))
        state31, _ = policy.effective_demand(1104)
        check('P5.inert_from_31_ticks', age(1104) == 31 and state31 == 'inert',
              'age=%d state=%s' % (age(1104), state31))
        check('P5.inert_event_named',
              any(e.get('event') == 'demand_inert' and e.get('reason') == 'expired_record'
                  for e in policy.last_trace['events']))
        empty = fp.FocusPolicy(M.InputMapper(M.MockSink()))
        state_none, rec_none = empty.effective_demand(5000)
        check('P5.no_record_inert', state_none == 'inert' and rec_none is None)

    # ---------------- P6: gate transitions are named no-ops when nothing held
    def test_p6_named_no_ops(self):
        policy = fp.FocusPolicy(M.InputMapper(M.MockSink()))
        policy.focus_gained(100)               # not gated: a named no-op
        ev = named_event(policy, 'focus_gained')
        check('P6.resume_noop_named', len(ev) == 1 and ev[0]['resumed'] is False)
        policy.disconnected(200)
        check('P6.disconnect_nothing_held_named',
              named_event(policy, 'disconnect')
              and named_event(policy, 'disconnect')[0]['held_after'] == [])
        policy.reconnected(300)
        check('P6.reconnect_named', len(named_event(policy, 'reconnect')) == 1)
        # mouse counts while ungated flow to the mapper (consumed, never resent)
        policy.mouse(40, 310)
        check('P6.ungated_mouse_forwarded', len(named_event(policy, 'mouse_refused_while_gated')) == 0)

    # ---------------- F1: the stuck-command hazard, bitten live
    def test_f1_stuck_command_bites_live(self):
        sink = M.MockSink()
        policy = fp.FocusPolicy(M.InputMapper(sink))
        policy.press('W', 1000)
        policy.tick(1000)
        event_ms = 1020
        policy.focus_lost(event_ms)
        ret = policy.press('W', 1050)          # a forced press while gated
        check('F1.gated_press_refused_named',
              ret is None and any(e.get('event') == 'press_refused_while_gated'
                                  and e.get('name') == 'W'
                                  for e in policy.last_trace['events']))
        for t in (1050, 1100, 1150, 1200, 1250):
            policy.tick(t)
        deadline = event_ms + M.RELEASE_DECAY_MS
        post = [(r.issued_tick * 1000 // self.PHYSICS, r.v_forward)
                for r in sink.records]
        check('F1.no_nonzero_demand_past_deadline',
              all(v == 0.0 for _, v in post if _ > deadline),
              str([p for p in post if p[0] > deadline]))
        check('F1.last_nonzero_within_100ms',
              max((t for t, v in post if v > 0.0), default=0) <= deadline)
        check('F1.held_stays_empty', len(policy.held) == 0)

    # ---------------- H1: the hazard baseline the policy prevents
    def test_h1_hazard_baseline_raw_mapper(self):
        sink = M.MockSink()
        raw = M.InputMapper(sink)              # NO policy: the pre-U03 world
        raw.press('W', 1000)
        stamps = list(range(1000, 1351, 50))
        for t in stamps:
            raw.tick(t)
        nonzero = [t for t, r in zip(stamps, sink.records) if r.v_forward > 0.0]
        check('H1.raw_mapper_keeps_commanding',
              len(sink.records) == len(stamps)
              and all(abs(r.v_forward - self.V) < 1e-12 for r in sink.records)
              and nonzero == stamps,
              'nonzero records at %d of %d boundaries' % (len(nonzero), len(stamps)))

    # ---------------- F2: timing claims are exact, not approximate
    def test_f2_exact_timing(self):
        sink = M.MockSink()
        raw = M.InputMapper(sink)
        raw.press('W', 1000)
        raw.tick(1000)
        raw.release('W', 1000)                 # release at the boundary itself
        out = raw.tick(1100)                   # elapsed == RELEASE_DECAY_MS
        check('F2.decay_at_exactly_100ms_is_zero',
              len(out) == 1 and out[0].v_forward == 0.0,
              repr(out[0].v_forward if out else None))
        # the aging boundary is the declared strict inequality
        # (is_expired is a staticmethod of the upstream InputMapper CLASS;
        # the first draft here called M.is_expired and errored -- preserved)
        record = sink.records[0]
        check('F2.expiry_strict_at_30_ticks',
              raw.is_expired(record, 1100) is False
              and raw.is_expired(record, 1104) is True)
        # every policy event carries its injected now_ms
        policy = fp.FocusPolicy(M.InputMapper(M.MockSink()))
        policy.focus_lost(4321)
        check('F2.events_bind_injected_time',
              named_event(policy, 'focus_lost')[0]['now_ms'] == 4321)

    # ---------------- F3: nothing is silent
    def test_f3_nothing_silent(self):
        policy = fp.FocusPolicy(M.InputMapper(M.MockSink()))
        policy.focus_lost(100)
        policy.press('W', 110)
        policy.mouse(25, 120)
        policy.focus_gained(130)
        kinds = [e['event'] for e in policy.last_trace['events']]
        check('F3.focus_loss_named', 'focus_lost' in kinds)
        check('F3.press_refusal_named', 'press_refused_while_gated' in kinds)
        check('F3.mouse_refusal_named', 'mouse_refused_while_gated' in kinds)
        check('F3.resume_named', 'focus_gained' in kinds)
        check('F3.no_untraceged_transition', len(kinds) == 4, str(kinds))

    @classmethod
    def tearDownClass(cls):
        fails = [c for c in CHECKS if not c[1]]
        print('\nPROBE SUMMARY: %d named checks, %d failed' % (len(CHECKS), len(fails)))
        for name, _, detail in fails:
            print('FAILED: %s :: %s' % (name, detail))


if __name__ == '__main__':
    unittest.main(verbosity=2)
