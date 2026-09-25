"""test_failure_sequences.py -- I-R06-FAILURE-SEQUENCES: the regression suite.

Runs the eight cross-component sequences of failure_sequences.py against the
REAL pinned components (hash-bound at import via the extraction ledger), then
proves the detectors are not a rubber stamp with two DELIBERATELY-BROKEN
controls:

  CTRL-01 LatchingMapper      -- swallows speed-key releases (replayed through
                                 the IDENTICAL SEQ-01 step+check script; the
                                 runner must report FAIL with zombie records).
  CTRL-02 QuiesceIgnoringMapper -- swallows release_all (replayed through the
                                 IDENTICAL SEQ-02 script; the runner must
                                 report FAIL because the quiesce leaves the
                                 mapper holding the key).

The controls are stand-ins BY DESIGN and are used ONLY to prove detector
sensitivity (FS-3); no sequence under test ever uses them. Everything here is
a mocked boundary: injected integer-ms clock, recording sink, the pinned
module's own world doubles. No real device, process, or window is touched and
no device-loss certification is claimed.

stdlib unittest; the whole suite is bounded well under the 120 s card limit.
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import failure_sequences as fs   # noqa: E402  (binding happens on first use)


# ── the deliberately-broken controls (stand-ins; NEVER the system under test) ─
class LatchingMapper(fs.get_bound().InputMapper):
    """CTRL-01: a BROKEN mapper that swallows speed-key releases -- exactly the
    stuck-movement family the invariants exist to kill. Subclasses the REAL
    pinned InputMapper and rewires exactly one method, clearly labeled."""

    def release(self, name, now_ms):
        self.last_trace.setdefault("control_latched_release", []) \
            .append((name, int(now_ms)))
        return self.bindings.get(name)      # the key stays held: THE LATCH


class QuiesceIgnoringMapper(fs.get_bound().InputMapper):
    """CTRL-02: a BROKEN mapper that ignores release_all -- the pause quiesce
    would silently leave the key armed."""

    def release_all(self, now_ms):
        self.last_trace.setdefault("control_ignored_release_all", []) \
            .append(int(now_ms))
        return None                         # nothing released: THE LATCH


# ── the suite ─────────────────────────────────────────────────────────────────
class ImportBinding(unittest.TestCase):
    """FS-1: the runner must prove it drives the pinned bytes."""

    def test_binding_refuses_and_reports(self):
        bound = fs.get_bound()
        self.assertEqual(len(bound.binding_report), 4)
        for check in bound.binding_report:
            self.assertTrue(check.ok, "binding failed: %r" % check)
            self.assertEqual(len(check.sha256_actual), 64)
            self.assertEqual(len(check.git_blob_actual), 40)
            self.assertTrue(check.under_reference_root)
        # the frozen-constant identity law held at bind time:
        self.assertTrue(all(held for _label, held in bound.identity_checks))

    def test_binding_refuses_a_foreign_ledger_root(self):
        # a directory that is not the extraction must be refused, not guessed
        with self.assertRaises(fs.ImportBindingError):
            fs.bind_components(str(HERE))   # no reference/ + tools/ here

    def test_runner_refuses_a_corrupted_extraction(self):
        # a mutated copy of the pinned bytes must be REFUSED, not run (FS-1)
        import shutil
        import tempfile
        bound = fs.get_bound()
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "reference"
            shutil.copytree(bound.reference_root, tmp)
            victim = tmp / "tools" / "monkey_campaign" / "product" / "input_mapper.py"
            victim.write_bytes(victim.read_bytes() + b"\n# one mutated byte\n")
            with self.assertRaises(fs.ImportBindingError) as ctx:
                fs.bind_components(str(tmp))
            self.assertIn("IMPORT BINDING FAILED", str(ctx.exception))
            self.assertIn("input_mapper.py", str(ctx.exception))

    def test_bound_constants_are_the_pinned_numbers(self):
        b = fs.get_bound()
        self.assertEqual(b.RELEASE_DECAY_MS, 100)
        self.assertEqual(b.INTERVAL_MS, 50)
        self.assertEqual(b.VALID_MS, 100)
        self.assertEqual(b.EXPIRY_TICKS, 30)
        self.assertEqual(b.V_MAX_IN_BAND_M_S, 0.763625)
        self.assertEqual(b.OMEGA_MAX_RAD_S, 1.6)


class SequencesAgainstRealComponents(unittest.TestCase):
    """Each sequence: PASS expected against the real composed stack."""

    def setUp(self):
        self.bound = fs.get_bound()

    def _run(self, seq_id):
        result = fs.run_sequence(seq_id, bound=self.bound)
        self.assertTrue(
            result.passed,
            "%s failed against the REAL components:\n%s\nidentity=%r"
            % (seq_id, "\n".join(result.violations), result.component_identity))
        self.assertEqual(result.violations, [])
        self.assertIsNone(result.used_control_mapper)
        return result

    def test_seq01_release_stops_emission(self):
        result = self._run("SEQ-01")
        # the shape invariant (a) promises, read off the actual timeline:
        session = fs.SequenceSession(self.bound)
        fs.SEQUENCE_REGISTRY["SEQ-01"][1](session)          # the same steps
        post = [(t, rec.v_forward) for (t, rec) in session.sink.timeline
                if t > 1210]
        self.assertEqual(len(post), 2, "expected the two declared decay samples")
        self.assertLessEqual(post[0][0], 1210 + self.bound.RELEASE_DECAY_MS)
        self.assertEqual(post[0][1] > 0.0, True)
        self.assertEqual(post[1], (1300, 0.0), "second sample must be exact 0.0")
        self.assertTrue(result.passed)

    def test_seq02_pause_silences_locomotion(self):
        self._run("SEQ-02")

    def test_seq03_resume_fresh_grid_no_phantom(self):
        self._run("SEQ-03")

    def test_seq04_restart_and_exit_exactly_once(self):
        self._run("SEQ-04")

    def test_seq05_blur_mid_emission_decays_to_silence(self):
        self._run("SEQ-05")

    def test_seq06_disconnect_reconnect_no_zombie(self):
        self._run("SEQ-06")

    def test_seq07_mid_play_restart_is_named_noop(self):
        self._run("SEQ-07")

    def test_seq08_exit_from_attract_teardown_once(self):
        self._run("SEQ-08")

    def test_all_sequences_green_and_deterministic(self):
        first = fs.run_all(self.bound)
        second = fs.run_all(self.bound)
        for a, b in zip(first, second):
            self.assertTrue(a.passed, "%s failed: %r" % (a.seq_id, a.violations))
            self.assertEqual(a.seq_id, b.seq_id)
            self.assertEqual(a.violations, b.violations)      # bit-deterministic
            self.assertEqual(a.passed, b.passed)


class BrokenControls(unittest.TestCase):
    """FS-3: the detectors must FAIL bad behavior, not rubber-stamp it."""

    def setUp(self):
        self.bound = fs.get_bound()

    def test_ctrl01_latching_release_is_caught_by_seq01(self):
        session = fs.SequenceSession(
            self.bound, mapper_factory=lambda sink: LatchingMapper(sink))
        result = fs.run_sequence("SEQ-01", session=session, bound=self.bound)
        self.assertFalse(result.passed, "CTRL-01 was rubber-stamped: the runner "
                         "passed a mapper that latches released input")
        self.assertTrue(any(v.startswith("zombie") for v in result.violations),
                        "no zombie violation for the latch: %r" % result.violations)
        self.assertEqual(result.used_control_mapper, "LatchingMapper")
        # the failure preserves the minimal event sequence + source identity:
        self.assertTrue(result.events)
        self.assertEqual(result.events[0]["kind"], "key_down")
        self.assertTrue(result.component_identity["bound_modules"])

    def test_ctrl02_quiesce_ignoring_mapper_is_caught_by_seq02(self):
        session = fs.SequenceSession(
            self.bound, mapper_factory=lambda sink: QuiesceIgnoringMapper(sink))
        result = fs.run_sequence("SEQ-02", session=session, bound=self.bound)
        self.assertFalse(result.passed, "CTRL-02 was rubber-stamped: the runner "
                         "passed a mapper that ignores the pause quiesce")
        self.assertTrue(any("quiesce: mapper still holds" in v
                            for v in result.violations),
                        "no held-key violation for the quiesce-ignorer: %r"
                        % result.violations)
        self.assertEqual(result.used_control_mapper, "QuiesceIgnoringMapper")

    def test_controls_are_never_used_by_the_sequences_under_test(self):
        for seq_id in sorted(fs.SEQUENCE_REGISTRY):
            result = fs.run_sequence(seq_id, bound=self.bound)
            self.assertIsNone(result.used_control_mapper)


class SuiteBudget(unittest.TestCase):
    """The card's runtime budget, measured, not assumed."""

    def test_full_runner_finishes_far_under_the_budget(self):
        t0 = time.perf_counter()
        results = fs.run_all(fs.get_bound())
        elapsed = time.perf_counter() - t0
        self.assertEqual(len(results), 8)
        self.assertLess(elapsed, 120.0)          # the card limit
        self.assertLess(elapsed, 5.0,            # the prereg prediction
                        "runner took %.2fs -- prereg predicted <5s" % elapsed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
