import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import worker_start
from agent_slots import Registry
from suggestion_box import SuggestionBox


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = Registry(self.root)
        self.registry.initialize()
        self.registry.reconcile({'expected_registered_agents':0,
            'live_inventory_reference':'isolated startup fixture'})
        SuggestionBox(self.root).initialize()

    def run_start(self, *args):
        output = io.StringIO()
        with patch.object(worker_start, 'DEFAULT_ROOT', self.root), \
             patch('sys.argv', ['worker_start.py', *args]), \
             patch.object(worker_start.subprocess, 'run', return_value=SimpleNamespace(
                 returncode=0, stdout='{"current":"theMeaning"}', stderr='')), \
             contextlib.redirect_stdout(output):
            worker_start.main()
        return json.loads(output.getvalue())

    def test_start_reads_real_plan_and_claims_once(self):
        result = self.run_start('--arrival-id', 'startup-fixture')
        self.assertEqual(result['plan']['approved_task_count'], 83)
        self.assertTrue(result['task_claimed'])
        self.assertEqual(result['assignment']['state'], 'ASSIGNED')
        self.assertTrue(result['assignment']['brief']['steps'])
        self.assertEqual(self.registry.snapshot()['registered_agents'], 1)
        again = self.run_start('--arrival-id', 'startup-fixture')
        self.assertEqual(again['assignment']['state'], 'RECOVER_OWNED_ASSIGNMENT')
        self.assertEqual(self.registry.snapshot()['registered_agents'], 1)

    def test_check_does_not_claim_or_file_arrival(self):
        result = self.run_start('--check')
        self.assertFalse(result['task_claimed'])
        self.assertEqual(self.registry.snapshot()['registered_agents'], 0)
        self.assertEqual(SuggestionBox(self.root).listing()['questions'], [])

    def test_successful_assignment_does_not_file_blocking_question(self):
        self.run_start('--arrival-id','ordinary-worker')
        self.assertEqual(SuggestionBox(self.root).listing()['questions'], [])

    def test_orientation_failure_cannot_claim(self):
        with patch.object(worker_start,'DEFAULT_ROOT',self.root), \
             patch('sys.argv',['worker_start.py','--arrival-id','failed-orient']), \
             patch.object(worker_start.subprocess,'run',return_value=SimpleNamespace(
                 returncode=1,stdout='',stderr='fixture orient failure')):
            with self.assertRaisesRegex(ValueError,'orientation_failed'):
                worker_start.main()
        self.assertEqual(self.registry.snapshot()['registered_agents'],0)


if __name__ == '__main__':
    unittest.main()
