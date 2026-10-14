"""Trainer-spine repair tests (work.data.trainer_spine_repair_20260917).

Covers the four repaired membranes:
  A. model_auditor.audit_run returns ONE honest shape at every history length
     (the short-history dict used to lack 'stuck_metrics' and train_loop
     crashed with a KeyError on every run shorter than 5 generations);
  B. beat_generator trains through train_and_audit even at short history
     (the latent auditor KeyError recorded in batch/train.py);
  C. pref_selftest.seed accepts the documented protocol's rng, and domains
     that violate the protocol are refused HONESTLY (DomainRefusal), never a
     bare internal TypeError;
  D. the batch exercise runs erisaid_mirror PLUS pref_selftest and records
     both runs in the receipt dict.

All Chimera-side imports are fast, deterministic, CPU-only fixtures.
"""
import inspect
import random
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CHIMERA = str(REPO_ROOT / 'Chimera')
if CHIMERA not in sys.path:
    sys.path.insert(0, CHIMERA)

from core.model_auditor import audit_run                 # noqa: E402
from core.train_loop import DomainRefusal, train_and_audit  # noqa: E402


def _history(gens: int) -> list:
    return [{'metric_a': 0.5, 'metric_b': 1.0} for _ in range(gens)]


def _moving_history(gens: int) -> list:
    """Metrics that genuinely move (delta > the 0.01 stuck threshold)."""
    return [{'metric_a': i * 0.1, 'metric_b': 1.0 + i * 0.1}
            for i in range(gens)]


AUDIT_KEYS = {'generations', 'total_metrics', 'stuck_metrics', 'stuck_rate',
              'recommendation', 'stuck'}
# train_loop returns a REDUCED audit subset (the spine's own contract)
REDUCED_AUDIT_KEYS = {'stuck_metrics', 'stuck_rate', 'recommendation', 'stuck'}


class AuditShortHistoryShape(unittest.TestCase):
    """A: one shape at every history length; short history claims NOTHING."""

    def test_short_history_carries_the_full_shape(self):
        for gens in (0, 1, 3, 4):
            audit = audit_run(_history(gens), generations=gens)
            self.assertTrue(AUDIT_KEYS <= set(audit), gens)
            self.assertEqual(audit['stuck_metrics'], 0)
            self.assertEqual(audit['stuck'], [])
            self.assertEqual(audit['stuck_rate'], 0.0)
            # honesty: a missing audit must not read as a clean bill of health
            self.assertIn('Not enough history', audit['recommendation'])
            self.assertNotIn('All metrics moving', audit['recommendation'])

    def test_short_history_keeps_the_recorded_message_key(self):
        audit = audit_run(_history(2), generations=2)
        self.assertEqual(audit['message'], 'Not enough history for audit')

    def test_full_shape_unchanged_at_or_above_five_generations(self):
        audit = audit_run(_moving_history(5), generations=5)
        self.assertTrue(AUDIT_KEYS <= set(audit))
        self.assertEqual(audit['stuck_metrics'], 0)
        self.assertIn('All metrics moving', audit['recommendation'])

    def test_constant_metrics_are_still_detected_as_stuck(self):
        audit = audit_run(_history(5), generations=5)
        self.assertEqual(audit['stuck_metrics'], 2)
        self.assertIn('MODEL BUGS DETECTED', audit['recommendation'])

    def test_train_loop_short_history_completes(self):
        """The recorded crash: train_and_audit(..., gens<5) raised
        KeyError: 'stuck_metrics' before the repair."""
        result = train_and_audit('pref_selftest', pop=6, gens=3)
        self.assertEqual(result['domain'], 'pref_selftest')
        self.assertEqual(result['generations'], 3)
        self.assertEqual(result['audit']['stuck_metrics'], 0)
        self.assertIn('Not enough history', result['audit']['recommendation'])


class BeatGeneratorAuditPath(unittest.TestCase):
    """B: beat_generator trains and survives its audit at any history length."""

    def test_beat_generator_short_history(self):
        result = train_and_audit('beat_generator', pop=6, gens=3)
        self.assertEqual(result['audit']['stuck_metrics'], 0)
        self.assertIn('Not enough history', result['audit']['recommendation'])

    def test_beat_generator_full_audit(self):
        result = train_and_audit('beat_generator', pop=6, gens=5)
        self.assertTrue(REDUCED_AUDIT_KEYS <= set(result['audit']))
        self.assertIn(result['audit']['stuck_metrics'], range(0, 5))
        self.assertTrue(result['best_genome']['beats'])


class PrefSelftestProtocol(unittest.TestCase):
    """C: the fixture speaks the documented seed(rng) protocol."""

    def test_seed_accepts_the_protocol_rng(self):
        import core.trainables.pref_selftest as fixture
        self.assertEqual(fixture.seed(random.Random(7)), {'a': 0.5, 'b': 0.5})

    def test_seed_is_a_deterministic_fixed_point(self):
        import core.trainables.pref_selftest as fixture
        self.assertEqual(fixture.seed(), fixture.seed(random.Random(1)))
        self.assertEqual(fixture.seed(random.Random(2)),
                         fixture.seed(random.Random(3)))

    def test_protocol_signature_binds_positionally(self):
        import core.trainables.pref_selftest as fixture
        inspect.signature(fixture.seed).bind(None)  # the protocol's seed(rng)
        inspect.signature(fixture.mutate).bind({}, random.Random(0))
        inspect.signature(fixture.measure).bind({})

    def test_protocol_violation_is_an_honest_refusal(self):
        """A noncompliant domain must refuse with a named cause, never leak the
        bare TypeError from the call site. All live domains were aligned
        2026-09-18, so the probe is exercised through a stub module."""
        import types
        from core.train_loop import _require_protocol
        stub = types.SimpleNamespace()  # defines nothing: every probe refuses
        with self.assertRaises(DomainRefusal) as caught:
            _require_protocol(stub, 'stub_domain')
        self.assertEqual(caught.exception.code, 'domain_protocol_violation')
        self.assertIn('stub_domain', caught.exception.detail)
        self.assertIn('seed(rng)', caught.exception.detail)

    def test_creature_now_completes_under_the_protocol(self):
        """creature.seed() was aligned 2026-09-18: it must complete (the old
        protocol refusal is gone -- pin the new truth, not the stale one)."""
        result = train_and_audit('creature', pop=6, gens=3)
        self.assertIn('best_score', result)


class BatchExercise(unittest.TestCase):
    """D: the exercise runs the canonical domain plus the unblocked fixture."""

    def test_exercise_domains_recorded(self):
        from tools.science_funnel.batch.train import EXERCISE_DOMAINS
        self.assertEqual(EXERCISE_DOMAINS, ('erisaid_mirror', 'pref_selftest'))

    def test_exercise_runs_both_domains_and_records_receipt(self):
        from tools.science_funnel.batch.train import exercise
        receipt = exercise()
        self.assertTrue(receipt['completed'])
        self.assertEqual(receipt['domains'], ['erisaid_mirror', 'pref_selftest'])
        self.assertEqual(set(receipt['runs']), {'erisaid_mirror', 'pref_selftest'})
        for domain, run in receipt['runs'].items():
            self.assertEqual(run['domain'], domain, domain)
            self.assertEqual(run['exit_code'], 0, run['output_tail'])
            self.assertTrue(run['completed'], domain)
            self.assertTrue(run['output_sha256'], domain)
        # the wiring proof is the exit code: train_and_audit ran to completion
        # in the child (it used to crash before the repair). The audit DICT
        # contract is asserted in-process below, where the full result exists
        # (the receipt keeps only a 2000-char output tail for humans).
        erisaid = train_and_audit('erisaid_mirror', pop=6, gens=5)
        self.assertTrue(REDUCED_AUDIT_KEYS <= set(erisaid['audit']))

    def test_exercise_single_domain_filter_still_works(self):
        from tools.science_funnel.batch.train import exercise
        receipt = exercise(domains=('pref_selftest',))
        self.assertTrue(receipt['completed'])
        self.assertEqual(receipt['domains'], ['pref_selftest'])


class SweepHarness(unittest.TestCase):
    """The sweep classifies honestly; proven here on known outcomes."""

    def test_sweep_classifies_completed_refused_and_protocol(self):
        from tools.science_funnel.sweep_trainer_spine import sweep_module
        python = sys.executable
        completed = sweep_module(python, 'pref_selftest', 120)
        self.assertEqual(completed['outcome'], 'completed', completed)
        completed = sweep_module(python, 'creature', 120)
        self.assertEqual(completed['outcome'], 'completed', completed)
        refused = sweep_module(python, 'arrangement', 300)
        self.assertEqual(refused['outcome'], 'refused', refused)

    def test_sweep_child_survives_missing_gpu_dependency(self):
        """Whatever the GPU flavor does here (warp present: it refuses honestly
        on its missing measure(); warp absent: refused_env at import), the
        outcome must never be an internal spine crash."""
        from tools.science_funnel.sweep_trainer_spine import sweep_module
        record = sweep_module(sys.executable, 'bigbang_gpu', 300)
        self.assertIn(record['outcome'], ('refused_env', 'refused', 'completed'),
                      record)
        if record['outcome'] == 'refused':
            self.assertEqual(record['exc_type'], 'DomainRefusal', record)


if __name__ == '__main__':
    unittest.main()
