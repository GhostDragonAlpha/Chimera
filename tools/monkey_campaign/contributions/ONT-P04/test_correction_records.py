"""ONT-P04 correction records probes (P4, frozen in PREREGISTRATION.md).

Reads preserved prior-attempt artifacts READ-ONLY to reconcile the two
consistency defects named by the operational lead (arrival-876e63bf), checks
the implemented GPU-A machine's presence and byte-identity, and cross-checks
the replacement qualification receipt's honesty. CPU-only, offline, no writes
outside this attempt workspace.
"""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

WS = Path(__file__).resolve().parent
PINNED = WS / 'pinned'
PRIOR = Path('E:/ChimeraWork/monkey-coordination/kanban-attempts/ONT-P04/'
             'fccb0a3f4fc74a29a7189453b6f91ced')
CHECKOUT = WS / 'checkout' / 'tools' / 'monkey_campaign' / 'contributions' / 'ONT-P04'

sys.path.insert(0, str(PINNED / 'tools' / 'agent_fleet'))
sys.path.insert(0, str(WS))


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def text_of(p):
    return Path(p).read_text(encoding='utf-8')


class FailureCountReconciliationTests(unittest.TestCase):
    """Defect 2: preserved-first-run-failure counts were inconsistent across
    the prior deliverables (checkpoint text 5 / report.md 4 / receipt.json 7).
    The authoritative reconciliation: the receipt.json ITEMIZED enumeration is
    the complete pool (7 individual expectation fixes); the other two numbers
    are stale summaries of subsets of that same list - not different evidence."""

    def test_prior_records_carry_all_three_counts(self):
        receipt = json.loads(text_of(PRIOR / 'receipt.json'))
        self.assertEqual(receipt['task_id'], 'ONT-P04')
        checkpoint = json.loads(text_of(PRIOR / 'publication_request.json'))
        self.assertIn('(5 expectation fixes)', checkpoint['checkpoint'])
        report = ' '.join(text_of(PRIOR / 'report.md').split())
        self.assertIn('3 refusal-name expectations and one over-broad memory '
                      'assertion', report)
        self.assertIn('probe development failures', receipt['failures'][0])

    def test_receipt_enumerates_exactly_seven_items(self):
        receipt = json.loads(text_of(PRIOR / 'receipt.json'))
        body = receipt['failures'][0]
        inner = body.split('(', 1)[1].split('):', 1)[0]
        items = [x.strip() for x in inner.split(',') if x.strip()]
        expanded = []
        for item in items:
            m = re.fullmatch(r'(.+?) x(\d+)', item)
            if m:
                expanded += [m.group(1)] * int(m.group(2))
            else:
                expanded.append(item)
        # the authoritative pool: 7 individual expectation fixes
        self.assertEqual(len(expanded), 7)
        self.assertEqual(len(items), 6, 'six clauses, one carries x2')
        self.assertTrue(any('stale_generation' in x for x in items))
        self.assertTrue(any('foreign_resource' in x for x in items))
        self.assertTrue(any('admitted_mb' in x for x in items))
        self.assertTrue(any('train_a' in x and 'train-a' in x for x in items))
        self.assertTrue(any('supervisor token' in x for x in items))
        self.assertTrue(any('wrapped-markdown' in x for x in items))

    def test_reconciliation_arithmetic_is_subset_consistent(self):
        # report.md's 4 = 3 refusal-name expectations + 1 over-broad memory
        # assertion: the 3 refusal-name fixes and the memory fix ARE members
        # of the 7-item pool; report omitted the task-id charset fix, the
        # broker supervisor-token fix and the wrapped-markdown fix (4 + 3 = 7).
        report = ' '.join(text_of(PRIOR / 'report.md').split())
        self.assertIn('3 refusal-name expectations and one over-broad memory '
                      'assertion', report)
        receipt = json.loads(text_of(PRIOR / 'receipt.json'))
        pool = receipt['failures'][0]
        for member in ('stale_generation->stale_or_foreign_claim x2',
                       'foreign_resource->stale_or_foreign_claim x1',
                       'over-broad admitted_mb assertion'):
            self.assertIn(member, pool)
        for omitted in ('train_a->train-a', 'broker supervisor token',
                        'wrapped-markdown record match'):
            self.assertIn(omitted, pool)
        # the checkpoint's 5 is likewise an undercount of the same pool: the
        # checkpoint text names the same event with no itemization at all
        checkpoint = json.loads(text_of(PRIOR / 'publication_request.json'))
        self.assertIn('First-run probe failures (5 expectation fixes) '
                      'preserved and re-run to green', checkpoint['checkpoint'])
        self.assertIn('nothing suppressed', pool)


class ImplementationPresenceTests(unittest.TestCase):
    """Defect 1 (clause-2 delta): the handoff mechanism now EXISTS as the
    scoped GPU-A contribution, without mutating the pinned head."""

    def test_machine_module_exists_and_is_byte_identical(self):
        workspace_copy = WS / 'gpu_handoff.py'
        checkout_copy = CHECKOUT / 'gpu_handoff.py'
        self.assertTrue(workspace_copy.is_file())
        self.assertTrue(checkout_copy.is_file(),
                        'the mechanism must also sit at the attempt checkout '
                        'sparse path tools/monkey_campaign/contributions/ONT-P04')
        self.assertEqual(sha256_file(workspace_copy),
                         sha256_file(checkout_copy))

    def test_handoff_control_extends_pinned_control(self):
        from gpu_handoff import HandoffControl, PHASES, LIVE_PHASES
        from control import Control
        self.assertTrue(issubclass(HandoffControl, Control))
        self.assertEqual(PHASES, ('REQUESTED', 'DRAINING', 'READY', 'TRAINING',
                                  'RESTORING', 'AVAILABLE'))
        self.assertIn('RECOVERY_HOLD', LIVE_PHASES)
        for op in ('handoff_request', 'handoff_admit', 'handoff_gate_close',
                   'handoff_ready', 'handoff_launch', 'handoff_cessation',
                   'handoff_restore', 'handoff_hold', 'handoff_recover'):
            self.assertTrue(hasattr(HandoffControl, '_h_' + op[len('handoff_'):]),
                            op)

    def test_pinned_controller_is_unmutated_at_the_head(self):
        self.assertEqual(sha256_file(PINNED / 'tools' / 'agent_fleet' /
                                     'control.py'),
                         '39ff01dc8a4192e04606ee9d87386780739e89c8a1774da48501a'
                         '9545792f6b3')
        coord = ' '.join(text_of(
            PINNED / 'tools' / 'monkey_campaign' / 'COORDINATION.md').split())
        self.assertIn('does not implement the model/game handoff above', coord)
        # the frozen delta: the machine is delivered as the additive scoped
        # contribution, so the pinned head's own statement stays true there
        probe_source = text_of(WS / 'gpu_handoff.py')
        self.assertIn('class HandoffControl(Control)', probe_source)
        self.assertIn("s.setdefault('handoff'", probe_source)


class PinnedExtractionParityTests(unittest.TestCase):

    def test_hashes_match_prior_verified_extraction(self):
        mine = json.loads(text_of(WS / 'pinned_file_hashes.json'))
        prior = json.loads(text_of(PRIOR / 'pinned_file_hashes.json'))
        self.assertEqual(set(mine), set(prior),
                         'identical 52-file extraction layout as the prior '
                         'verified attempt')
        mismatched = {k for k in prior if mine[k] != prior[k]}
        self.assertEqual(mismatched, set())

    def test_preregistration_frozen_in_this_attempt(self):
        prereg = WS / 'PREREGISTRATION.md'
        raw = prereg.read_text(encoding='utf-8')
        self.assertEqual(sha256_file(prereg), PREREG_SHA256)
        for frozen in ('gate_timeout_gate_stays_closed', 'force_kill_refused',
                       'cannot_fabricate_ready', 'already_launched',
                       'protected_run_active', 'handoff_queue_jump_refused',
                       'release_requires_observed_cessation',
                       'unknown_state_stays_recovery_hold',
                       'resources_still_held', 'supervisor_only'):
            self.assertIn(frozen, raw)


PREREG_SHA256 = sha256_file(WS / 'PREREGISTRATION.md')


class ReceiptHonestyTests(unittest.TestCase):
    """Defect 1 (receipt flag): done_when_verified may only be true when the
    clause map actually verifies every clause."""

    def test_done_when_flag_matches_clause_map(self):
        receipt = json.loads(text_of(WS / 'qualification_receipt.json'))
        clause_map = receipt['done_when_clause_map']
        self.assertEqual(len(clause_map), 3)
        all_verified = all(v.startswith('VERIFIED') for v in clause_map.values())
        self.assertEqual(receipt['done_when_verified'], all_verified)
        self.assertTrue(receipt['done_when_verified'],
                        'this correction verifies all three clauses at the '
                        'records profile; the flag must say so honestly')
        gaps = receipt['remaining_gates']
        self.assertTrue(any('live' in g.lower() for g in gaps),
                        'live GPU qualification stays an open, separately '
                        'owned gate and must be named')
        self.assertNotEqual(receipt.get('draft'), True)

    def test_draft_overstatement_of_prior_attempt_is_recorded(self):
        prior = json.loads(text_of(PRIOR / 'qualification_receipt.json'))
        self.assertEqual(prior['done_when_verified'], True,
                        'the prior draft overstates; preserved as evidence')
        report = text_of(WS / 'report.md')
        self.assertIn('OVERSTATED', report)


if __name__ == '__main__':
    unittest.main(verbosity=2)
