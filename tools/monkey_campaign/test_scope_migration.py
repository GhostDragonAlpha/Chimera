import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent_slots import Registry
import kanban
import ontology_queue as q
from scope_migration import migrate, historical_card

HERE=Path(__file__).resolve().parent

class ScopeMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.registry=Registry(Path(self.tmp.name));self.registry.initialize()
        self.s=self.registry.readonly()
        self.s['kanban']={'schema':'chimera.kanban.v1','cards':{'ONT-P01':{'id':'ONT-P01','slot':1,'state':'DONE','spec':{'planning_ids':['P01']},'criteria_sha256':'c'*64,'attempts':{'old':{'agent_id':'old-worker','state':'WORKING','workspace':'preserved'}},'prs':{'prior-pr':{'head_sha':'a'*40}},'messages':[],'winner':{'ontology_qualification':{'scope_sha256':'old'}}}},'backlog':[], 'ontology_scheduler':{'scope_sha256':'old'},'continuous_cycle':True,'separate_review_lane':True,'branch_policy':'TEN_PERSISTENT_SLOT_BRANCHES','operational_takeover':True,'operational_lead':{'agent_id':'stopped','token':'fixture-only'}}
        self.p=q.project(q.load_catalog(HERE/'monkey_completion_map.json'))
    def apply(self,s=None,**kw):
        s=self.s if s is None else s
        args=dict(actor='astra-codex',workers_stopped=True,expected_revision=s['revision'],archive_reference='isolated-backup');args.update(kw)
        with patch.object(q,'HERE',HERE):return migrate(s,self.p,**args)
    def test_archive_is_exact_and_old_done_does_not_unlock(self):
        old=copy.deepcopy(self.s['kanban']);self.apply()
        self.assertEqual(self.s['scope_archives']['old']['board'],old)
        self.assertEqual(set(self.s['kanban']['cards']),{'MAT2-P01'})
        self.assertEqual(self.s['kanban']['cards']['MAT2-P01']['state'],'OPEN')
        self.assertIsNone(self.s['kanban']['operational_lead'])
        self.assertEqual(historical_card(self.s,'ONT-P01')['card'],old['cards']['ONT-P01'])
        self.assertEqual(self.s['kanban']['cards']['MAT2-P01']['legacy_work'][0]['task_id'],'ONT-P01')
    def test_wrong_authority_stop_revision_refused_without_change(self):
        for kw in [dict(actor='worker'),dict(workers_stopped=False),dict(expected_revision=-1),dict(archive_reference='')]:
            s=copy.deepcopy(self.s)
            with self.assertRaises(ValueError):self.apply(s,**kw)
            self.assertEqual(s,self.s)
    def test_wrong_scope_qualification_cannot_unlock(self):
        spec={'depends_on':['X'],'ontology_qualification':{'scope_sha256':'new'}}
        b={'cards':{'X':{'state':'DONE','winner':{'ontology_qualification':{'scope_sha256':'old'}}}}}
        self.assertFalse(q.dependencies_satisfied(b,spec))
    def test_returning_identity_gets_new_task_and_stale_write_refuses(self):
        self.apply()
        with self.registry.transaction() as s:s.clear();s.update(copy.deepcopy(self.s))
        with patch.object(q,'HERE',HERE):packet=kanban.join(self.registry,'old-worker')
        self.assertEqual(packet['task_id'],'MAT2-P01');self.assertEqual(packet['state'],'ASSIGNED')
        with self.assertRaisesRegex(ValueError,'task_not_in_current_scope'):
            kanban.owned_attempt(self.s['kanban'],{'task_id':'ONT-P01'})
    def test_rollback_copy_keeps_prior_state(self):
        prior=copy.deepcopy(self.s);candidate=copy.deepcopy(prior);self.apply(candidate)
        self.assertNotEqual(candidate,prior)
        self.assertEqual(prior['kanban']['cards']['ONT-P01']['attempts']['old']['workspace'],'preserved')
        self.assertEqual(candidate['scope_archives']['old']['board'],prior['kanban'])
    def test_new_scope_qualified_merge_unblocks_next(self):
        self.apply();b=self.s['kanban'];first=b['cards']['MAT2-P01']
        first['state']='DONE';first['winner']={'ontology_qualification':{'scope_sha256':self.p['scope_sha256']}}
        with patch.object(q,'HERE',HERE):kanban.refill(b)
        self.assertIn('MAT2-P02',b['cards'])
    def test_previous_instruction_ack_requires_current_read(self):
        from instruction_state import inspect
        current=inspect(HERE.parents[1])
        ack=dict(schema='chimera.instruction_ack.v1',lead_id='astra-codex',revision=30,
                 revision_id='astra-0030',scope_sha256='01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6',
                 bundle_sha256='a'*64,coordinator_id='prior-worker',native_checkpoint='saved',
                 acknowledged_at_utc='2026-09-27T00:00:00+00:00')
        self.assertEqual(inspect(HERE.parents[1],ack)['state'],'UPDATED_READ_AND_ACK_REQUIRED')
        self.assertNotEqual(current['revision_id'],'astra-0030')

if __name__=='__main__':unittest.main()
