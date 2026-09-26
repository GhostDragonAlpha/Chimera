import unittest,tempfile,hashlib
from pathlib import Path
from agent_slots import Registry
import kanban as k
import continuous_cycle as cycle
import review_lane as lane
from test_kanban import spec

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.r=Registry(Path(self.tmp.name));self.r.initialize()
        k.initialize(self.r,[spec('T'+str(i)) for i in range(13)]+[spec('DEPENDENT',['T0'])],k.LEAD)
        with self.r.transaction() as s:s['kanban'].update(separate_review_lane=True,continuous_cycle=True,branch_policy='TEN_PERSISTENT_SLOT_BRANCHES',operational_takeover=True)

    def submit(self):
        p=cycle.join(self.r,'author','T0');a=p['attempt']
        root=Path(a['workspace']);root.mkdir(parents=True);artifact=root/'receipt.json';artifact.write_text('{}')
        args=dict(task_id='T0',agent_id='author',attempt_id=a['id'],criteria_sha256=a['criteria_sha256'],checkpoint='Saved',writes_stopped=True,artifacts=[{'path':str(artifact),'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest()}])
        cycle.request_publication(self.r,args)
        return a,args

    def test_handoff_releases_capacity_without_completion_or_dependency_unlock(self):
        a,args=self.submit();b=self.r.readonly()['kanban'];c=b['cards']['T0']
        self.assertEqual(c['lane'],'REVIEW');self.assertIsNone(c['winner'])
        self.assertEqual(c['publication_branch'],'review/T0')
        self.assertEqual(b['cards']['T10']['slot'],c['slot'])
        self.assertEqual(k.summary(b)['active_count'],10)
        self.assertNotIn('DEPENDENT',b['cards'])
        before=k.digest(b);cycle.request_publication(self.r,args)
        self.assertEqual(before,k.digest(self.r.readonly()['kanban']))
        fresh=cycle.join(self.r,'fresh-worker')
        self.assertEqual(fresh['state'],'ASSIGNED');self.assertNotEqual(fresh['task_id'],'T0')

    def test_correction_waits_when_full_and_reuses_same_task(self):
        self.submit()
        with self.r.transaction() as s:
            b=s['kanban'];c=b['cards']['T0'];original=c['criteria_sha256']
            c['publication_requests'][0]['status']='PR_RECORDED';c['state']='CHANGES_REQUESTED'
            lane.corrections(b,c);k.refill(b)
            self.assertEqual(c['lane'],'CORRECTION_QUEUED')
            lane.detach(b,b['cards']['T1']);k.refill(b)
            self.assertEqual(c['lane'],'DEVELOPMENT');self.assertEqual(c['criteria_sha256'],original)
            self.assertEqual(k.summary(b)['active_count'],10)

    def test_older_attempt_checkpoints_instead_of_resuming_outside_slot(self):
        a,_=self.submit()
        with self.r.transaction() as s:s['kanban']['cards']['T0']['attempts'][a['id']]['state']='WORKING'
        self.assertEqual(cycle.join(self.r,'author','T0')['state'],'CHECKPOINT_FOR_COORDINATION')

    def test_merge_review_card_does_not_free_reused_development_slot(self):
        a,_=self.submit()
        args=dict(task_id='T0',agent_id='author',attempt_id=a['id'],criteria_sha256=a['criteria_sha256'],pr_url='https://github.com/'+k.REPO+'/pull/901',head_sha='a'*40)
        k.submit(self.r,args);k.review(self.r,dict(args,actor=k.LEAD,verdict='ACCEPTED',body='checked',evidence_reference='receipt'))
        gh=dict(merged=True,html_url=args['pr_url'],base={'ref':k.BASE},head={'sha':args['head_sha']},merge_commit_sha='f'*40)
        k.accept_merge(self.r,dict(args,actor=k.LEAD),gh)
        b=self.r.readonly()['kanban'];self.assertEqual(k.summary(b)['active_count'],10)
        self.assertEqual(b['cards']['T10']['state'],'OPEN')

if __name__=='__main__':unittest.main()
