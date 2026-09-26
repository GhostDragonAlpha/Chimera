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
    def test_kanban_start_returns_card_and_inbox_without_worker_lease(self):
        import kanban
        kanban.initialize(self.registry,[dict(id='TASK',objective='Implement task',falsifier='wrong result',
            steps=['implement'],completion='Reviewed merged PR')],kanban.LEAD)
        kanban.post(self.registry,dict(task_id='TASK',author=kanban.LEAD,body='Fix the exact input case'))
        result=self.run_start('--arrival-id','kanban-worker')
        self.assertEqual(result['assignment']['task_id'],'TASK')
        self.assertEqual(result['assignment']['task_inbox'][0]['body'],'Fix the exact input case')
        self.assertEqual(self.registry.snapshot()['registered_agents'],0)
        self.assertIn('pr_submission_template',result)
        self.assertEqual(result['checkout']['branch'],'branch-1')
        self.assertEqual(result['working_directory'],str(self.root/'checkout'))

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
             patch.object(worker_start, 'prepare_checkout', return_value={'working_directory':str(self.root/'checkout'),'branch':'branch-1','state':'PREPARED'}), \
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


class RecoveryTests(StartupTests):
    def setup_card(self):
        import kanban
        kanban.initialize(self.registry,[dict(id='RECOVER',objective='Task',falsifier='wrong',steps=['work'],completion='merge')],kanban.LEAD)

    def test_broken_stdout_preserves_claim_and_identity(self):
        self.setup_card()
        import builtins
        def broken(*args,**kwargs):
            if kwargs.get('file') is worker_start.sys.stderr:
                return
            raise BrokenPipeError('consumer closed stdout')
        with patch.object(worker_start,'print',side_effect=broken,create=True):
            with self.assertRaises(BrokenPipeError):self.run_start('--arrival-id','cut-output')
        attempts=self.registry.readonly()['kanban']['cards']['RECOVER']['attempts']
        self.assertEqual(len(attempts),1)
        receipts=list((self.root/'startup-receipts').glob('*.json'))
        self.assertEqual(len(receipts),1)
        receipt=json.loads(receipts[0].read_text())
        self.assertEqual(receipt['arrival_id'],'cut-output')
        self.assertEqual(receipt['assignment_id'],next(iter(attempts)))
        result=self.run_start('--arrival-id','cut-output')
        self.assertEqual(result['assignment']['attempt']['id'],receipt['assignment_id'])
        self.assertEqual(len(self.registry.readonly()['kanban']['cards']['RECOVER']['attempts']),1)

    def test_missing_status_snapshot_does_not_block_startup(self):
        self.setup_card()
        (self.root/'STATUS.json').unlink(missing_ok=True)
        result=self.run_start('--arrival-id','sqlite-worker')
        self.assertEqual(result['registry_source'],'sqlite-readonly')
        self.assertTrue(result['task_claimed'])

    def test_receipt_does_not_persist_role_token(self):
        path=worker_start.save_recovery(self.root,'worker',{'state':'OPERATIONAL_LEAD_ASSIGNED','operational_lead':{'token':'secret-role'}},'astra-test')
        self.assertNotIn('secret-role',Path(path).read_text())


if __name__ == '__main__':
    unittest.main()
