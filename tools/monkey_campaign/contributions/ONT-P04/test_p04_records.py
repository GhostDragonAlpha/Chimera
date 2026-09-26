"""ONT-P04 records probes (records profile, offline).

Verifies the PUBLISHED CONTRACT RECORDS for the supervisor handoff at the
pinned head, and reconciles the planning observation. Reads only the
byte-exact extraction in ./pinned; no live system is touched.
"""
import json
import re
import unittest
from pathlib import Path

WS = Path(__file__).resolve().parent
PINNED = WS / 'pinned'
COORD = PINNED / 'tools' / 'monkey_campaign' / 'COORDINATION.md'
PREREG = PINNED / 'tools' / 'monkey_campaign' / 'GPU_HANDOFF_PREREGISTRATION.md'
RECEIPT = PINNED / 'GPU_HANDOFF_PUBLICATION_RECEIPT.untracked.json'
CONTROL = PINNED / 'tools' / 'agent_fleet' / 'control.py'


def text_of(p):
    return p.read_text(encoding='utf-8')


class HandoffContractRecordsTests(unittest.TestCase):
    """C2: the verified supervisor-handoff contract exists as records."""

    def test_coordination_carries_handoff_contract(self):
        raw = text_of(COORD)
        # line-wrapped markdown: compare on normalized whitespace
        doc = ' '.join(raw.split())
        self.assertIn('## GPU handoff: training can preempt gaming and local inference', doc)
        # the required handoff sequence and its failure rule
        self.assertIn('REQUESTED -> DRAINING -> READY -> TRAINING -> RESTORING -> AVAILABLE', doc)
        self.assertIn('RECOVERY_HOLD', doc)
        self.assertIn('it never fabricates READY', doc)
        # the three priority rules
        self.assertIn('retains the GPU until it completes', doc)
        self.assertIn('take priority over gaming and local-model inference', doc)
        self.assertIn('Multiple training requests serialize fairly', doc)
        self.assertIn('do not let arbitrary worker priority numbers jump the queue', doc)
        # supervisor independence from the model it unloads
        self.assertIn('must run independently of Bionic\'s/local model\'s ability', doc)
        # evidence and implementation queue
        self.assertIn('### Evidence found before implementation', doc)
        for item in ('**GPU-A, authority/state machine:**', '**GPU-B, Bionic/inference adapter:**',
                     '**GPU-C, Windows game adapter:**', '**GPU-D, independent recovery test:**'):
            self.assertIn(item, doc)

    def test_preregistration_record_is_frozen_and_bounded(self):
        doc = text_of(PREREG)
        for section in ('STATEMENT:', 'PREDICTION:', 'FALSIFIERS BEFORE IMPLEMENTATION:'):
            self.assertIn(section, doc)
        self.assertIn('one supervisor outside local-model inference', doc)
        self.assertIn('No live game interruption, model unload/reload, training launch,',
                      doc)

    def test_publication_receipt_states_specification_only(self):
        rec = json.loads(text_of(RECEIPT))
        self.assertEqual(rec.get('revision'), 'astra-0002')
        self.assertIn('Specification and implementation queue only', rec.get('deployment', ''))
        self.assertIn('no model unload', rec.get('deployment', ''))
        for key in ('bundle_sha256', 'scope_sha256'):
            self.assertRegex(rec.get(key, ''), r'^[0-9a-f]{64}$', key)

    def test_handoff_state_machine_is_not_implemented_at_this_head(self):
        """The honest applicability boundary: control.py at the pinned head has
        no REQUESTED/DRAINING/TRAINING/RESTORING handoff machine. The absence
        is named here so no downstream skill accepts a live-handoff claim."""
        src = text_of(CONTROL)
        for state in ('REQUESTED', 'DRAINING', 'RESTORING'):
            self.assertNotIn(state, src, state)
        self.assertNotIn('TRAINING', src)
        # while the supervisor authority primitives it extends ARE implemented
        self.assertIn("require(actor=='SUPERVISOR','supervisor_only')", src)
        self.assertIn('actual_process_drained_evidence', src)
        self.assertIn('Never replace a reservation', src)
        self.assertIn("'release_dyad_first'", src)
        self.assertIn("'resources_still_held'", src)


class PlanningObservationReconciliationTests(unittest.TestCase):
    """Reconciles 'Supervisor reported 8/8 passing; broker completion needs
    current receipt' for P04 in monkey_completion_map.json."""

    def test_observation_referent_is_named_not_invented(self):
        suites = sorted((PINNED / 'tools' / 'agent_fleet').glob('test_*.py'))
        eight = []
        for suite in suites:
            n = len(re.findall(r'^\s*def test_', text_of(suite), re.M))
            if n == 8:
                eight.append(suite.name)
        self.assertIn('test_run_queue.py', eight)
        self.assertIn('test_layer_guard.py', eight)
        # no current record names the supervisor suite behind the planning
        # observation; the gap is recorded, and this qualification is the
        # requested current receipt (report.md + receipt.json).
        coord = text_of(COORD)
        self.assertNotIn('8/8', coord)

    def test_p04_planning_record_matches_dispatched_card(self):
        import sys
        sys.path.insert(0, str(PINNED / 'tools' / 'monkey_campaign'))
        try:
            mapping = json.loads(text_of(
                PINNED / 'tools' / 'monkey_campaign' / 'monkey_completion_map.json'))
        except FileNotFoundError:
            self.skipTest('completion map not extracted; card packet is authoritative')
        p04 = next(t for t in mapping['tasks'] if t['id'] == 'P04')
        self.assertEqual(
            p04['done_when'],
            'Every launched job uses existing ownership/broker rules; admitted '
            'training may interrupt gaming and local inference through a verified '
            'supervisor handoff, while already-running protected training retains '
            'ownership until confirmed release')
        self.assertEqual(p04['implementation_state'], 'UNRECONCILED')
        self.assertEqual(p04['validation_state'], 'NOT_REVERIFIED_IN_THIS_REVIEW')


if __name__ == '__main__':
    unittest.main(verbosity=2)
