import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
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
        self.assertEqual(result['plan']['approved_task_count'], 95)
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


class HandoffFlagTests(unittest.TestCase):
    """Regression coverage for the continuous-cycle handoff flags ported from the
    D-W03 lineage: --request-pr and --review-result must call the continuous_cycle
    library and, per the merged #228 gating, stop without dealing a card unless
    --take-next is explicit. The library module is untracked production
    infrastructure, so these tests inject a stub through sys.modules instead of
    importing it."""

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

    def _two_cards(self):
        import kanban
        kanban.initialize(self.registry,[dict(id='TASK',objective='Implement task',falsifier='wrong result',
            steps=['implement'],completion='Reviewed merged PR')],kanban.LEAD)
        kanban.enqueue(self.registry,{'actor':kanban.LEAD,'spec':dict(id='TASK2',objective='Second task',
            falsifier='wrong',steps=['work'],completion='merge')})

    def _stub(self,mark_requested=False):
        import kanban
        def side_effect(registry,data):
            if mark_requested:
                # Mirror the real library's essential transition: the attempt
                # stops being WORKING so the follow-up join can deal new work.
                with registry.transaction() as state:
                    for c in kanban.board(state)['cards'].values():
                        for a in c['attempts'].values():
                            if a['agent_id']==data['agent_id'] and a['state']=='WORKING':
                                a['state']='PUBLICATION_REQUESTED'
            return {'state':'PUBLICATION_REQUESTED','request_id':'publication-fixture'}
        return SimpleNamespace(
            request_publication=Mock(side_effect=side_effect),
            submit_review=Mock(return_value={'state':'REVIEW_RECORDED','next_action':'fixture poll'}))

    def _first_attempt(self):
        first=self.run_start('--arrival-id','cycler')
        return first['assignment']['attempt']['id']

    def _request_pr_args(self):
        path=self.root/'request_pr_args.json'
        path.write_text(json.dumps({'agent_id':'cycler','task_id':'TASK',
            'checkpoint':'candidate, base revision and verification preserved',
            'writes_stopped':True}),encoding='utf-8')
        return path

    def test_request_pr_calls_library_and_stops_without_dealing(self):
        self._two_cards();self._first_attempt()
        path=self._request_pr_args();stub=self._stub()
        with patch.dict(sys.modules,{'continuous_cycle':stub}):
            result=self.run_start('--arrival-id','cycler','--request-pr',str(path))
        stub.request_publication.assert_called_once()
        handed_registry,handed_args=stub.request_publication.call_args.args
        self.assertIsInstance(handed_registry,Registry)
        self.assertEqual(handed_args['agent_id'],'cycler')
        self.assertTrue(handed_args['writes_stopped'])
        self.assertEqual(result['handoff'],{'state':'PUBLICATION_REQUESTED','request_id':'publication-fixture'})
        self.assertEqual(result['assignment']['state'],'STOPPED_AFTER_HANDOFF')
        self.assertFalse(result['task_claimed'])
        self.assertEqual(self.registry.readonly()['kanban']['cards']['TASK2']['attempts'],{})

    def test_request_pr_with_take_next_deals_next_card(self):
        self._two_cards()
        first_attempt=self._first_attempt()
        path=self._request_pr_args();stub=self._stub(mark_requested=True)
        with patch.dict(sys.modules,{'continuous_cycle':stub}):
            result=self.run_start('--arrival-id','cycler','--request-pr',str(path),'--take-next')
        self.assertEqual(result['handoff']['state'],'PUBLICATION_REQUESTED')
        # Note: astra kanban.join deals by slot priority and (unlike the D-W03
        # continuous_cycle.join) has no PUBLICATION_REQUESTED exclusion, so the
        # dealt card can be TASK again under a fresh attempt. The gating contract
        # under test is that --take-next deals a new attempt instead of stopping.
        self.assertEqual(result['assignment']['state'],'ASSIGNED')
        self.assertTrue(result['task_claimed'])
        self.assertNotEqual(result['assignment']['attempt']['id'],first_attempt)

    def test_review_result_calls_library_and_stops_without_dealing(self):
        self._two_cards()
        path=self.root/'review_result_args.json'
        path.write_text(json.dumps({'agent_id':'cycler','task_id':'TASK','review_id':'review-fixture',
            'head_sha':'a'*64,'criteria_sha256':'b'*64,'verdict':'PASS',
            'body':'checks rerun in review workspace','writes_stopped':True}),encoding='utf-8')
        stub=self._stub()
        with patch.dict(sys.modules,{'continuous_cycle':stub}):
            result=self.run_start('--arrival-id','cycler','--review-result',str(path))
        stub.submit_review.assert_called_once()
        handed_registry,handed_args=stub.submit_review.call_args.args
        self.assertIsInstance(handed_registry,Registry)
        self.assertEqual(handed_args['verdict'],'PASS')
        self.assertEqual(result['handoff']['state'],'REVIEW_RECORDED')
        self.assertEqual(result['assignment']['state'],'STOPPED_AFTER_HANDOFF')
        self.assertFalse(result['task_claimed'])
        self.assertEqual(self.registry.readonly()['kanban']['cards']['TASK2']['attempts'],{})

    def test_handoff_identity_mismatch_refused(self):
        self._two_cards()
        path=self.root/'mismatch_args.json'
        path.write_text(json.dumps({'agent_id':'someone-else'}),encoding='utf-8')
        stub=self._stub()
        with patch.dict(sys.modules,{'continuous_cycle':stub}):
            with self.assertRaisesRegex(ValueError,'handoff_identity_mismatch'):
                self.run_start('--arrival-id','cycler','--request-pr',str(path))
        stub.request_publication.assert_not_called()

    def test_new_flags_require_existing_arrival_id(self):
        path=self._request_pr_args()
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'existing_arrival_id_required_for_handoff'):
                self.run_start('--request-pr',str(path))

    def test_check_rejects_new_handoff_flags(self):
        path=self._request_pr_args()
        for flag in ('--request-pr','--review-result'):
            with self.assertRaisesRegex(ValueError,'check_cannot_submit_handoff'):
                self.run_start('--check',flag,str(path))

    def test_new_flags_require_kanban(self):
        path=self._request_pr_args()
        for flag in ('--request-pr','--review-result'):
            with self.assertRaisesRegex(ValueError,'kanban_not_initialized'):
                self.run_start('--arrival-id','cycler',flag,str(path))


if __name__ == '__main__':
    unittest.main()


class ParkNoRedealTests(StartupTests):
    """Regression coverage for the allocator deal pathology (mailbox b7687a3f):
    park must not re-deal in the same call, and re-dealing after any handoff
    requires the explicit --take-next flag."""

    def _two_cards(self):
        import kanban
        kanban.initialize(self.registry,[dict(id='TASK',objective='Implement task',falsifier='wrong result',
            steps=['implement'],completion='Reviewed merged PR')],kanban.LEAD)
        kanban.enqueue(self.registry,{'actor':kanban.LEAD,'spec':dict(id='TASK2',objective='Second task',
            falsifier='wrong',steps=['work'],completion='merge')})

    def _park_first_card(self):
        first=self.run_start('--arrival-id','parker')
        attempt_id=first['assignment']['attempt']['id']
        park_args=self.root/'park_args.json'
        park_args.write_text(json.dumps({'agent_id':'parker','task_id':'TASK','attempt_id':attempt_id,
            'checkpoint':'writes stopped honestly','writes_stopped':True}),encoding='utf-8')
        result=self.run_start('--arrival-id','parker','--park',str(park_args))
        return result,attempt_id

    def test_park_does_not_redeal_next_card(self):
        self._two_cards()
        result,attempt_id=self._park_first_card()
        self.assertEqual(result['handoff']['state'],'PAUSED')
        self.assertEqual(result['assignment']['state'],'STOPPED_AFTER_HANDOFF')
        self.assertFalse(result['task_claimed'])
        board=self.registry.readonly()['kanban']
        self.assertEqual(board['cards']['TASK2']['attempts'],{})
        self.assertEqual(board['cards']['TASK']['attempts'][attempt_id]['state'],'PAUSED')

    def test_park_with_take_next_is_refused(self):
        self._two_cards()
        with self.assertRaisesRegex(ValueError,'park_checkpoint_do_not_redeal'):
            self.run_start('--arrival-id','parker','--park',str(self.root/'unused.json'),'--take-next')

    def test_plain_startup_after_park_still_claims_explicitly(self):
        self._two_cards()
        self._park_first_card()
        second=self.run_start('--arrival-id','parker')
        self.assertTrue(second['task_claimed'])
        self.assertIn(second['assignment']['task_id'],('TASK','TASK2'))


if __name__ == '__main__':
    unittest.main()
