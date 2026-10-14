import unittest,tempfile,hashlib
from pathlib import Path
from agent_slots import Registry
import kanban as k
import continuous_cycle as cycle

class Cycle(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.r=Registry(Path(self.temp.name));self.r.initialize()
        k.initialize(self.r,[dict(id='T'+str(i),objective='work',steps=['verify'],falsifier='bad evidence',completion='verified merge',depends_on=[]) for i in range(11)],k.LEAD)
        with self.r.transaction() as s:
            s['kanban']['continuous_cycle']=True;s['kanban']['branch_policy']='TEN_PERSISTENT_SLOT_BRANCHES'
            for c in s['kanban']['cards'].values():c['publication_branch']='branch-'+str(c['slot'])
    def artifacts(self,workspace):
        p=Path(workspace)/'receipt.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'actual test evidence')
        return [{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]
    def submitted(self,n):
        p=k.join(self.r,'author'+str(n),'T'+str(n));a=p['attempt']
        req=dict(agent_id=a['agent_id'],task_id=p['task_id'],attempt_id=a['id'],criteria_sha256=a['criteria_sha256'],pr_url='https://github.com/'+k.REPO+'/pull/'+str(n+1),head_sha=str(n)*40)
        k.submit(self.r,req);return req
    def test_candidate_handoff_moves_on_and_idempotent(self):
        p=k.join(self.r,'worker');a=p['attempt']
        req=dict(agent_id='worker',task_id=p['task_id'],attempt_id=a['id'],criteria_sha256=a['criteria_sha256'],checkpoint='candidate ready',writes_stopped=True,artifacts=self.artifacts(a['workspace']))
        cycle.request_publication(self.r,req)
        self.assertEqual(cycle.request_publication(self.r,req)['state'],'PUBLICATION_ALREADY_REQUESTED')
        self.assertNotEqual(k.join(self.r,'worker')['task_id'],p['task_id'])
        self.assertEqual(k.read(self.r,p['task_id'])['prs'],{})
    def test_all_ten_prs_route_independent_review(self):
        for n in range(10):self.submitted(n)
        p=k.join(self.r,'author0');self.assertEqual(p['state'],'REVIEW_ASSIGNED');self.assertNotEqual(p['task_id'],'T0')
        self.assertEqual(k.read(self.r)['active_count'],10)
        v=p['review'];req=dict(agent_id='author0',task_id=p['task_id'],review_id=v['id'],head_sha=v['head_sha'],criteria_sha256=v['criteria_sha256'],verdict='PASS',body='verified',writes_stopped=True,artifacts=self.artifacts(v['workspace']))
        cycle.submit_review(self.r,req)
        self.assertIsNone(k.read(self.r,p['task_id'])['prs'][v['pr_url']]['review'])
        self.assertNotEqual(k.join(self.r,'author0')['task_id'],p['task_id'])
        self.assertNotEqual(k.read(self.r,p['task_id'])['state'],'DONE')
    def test_stale_review_refuses_and_routes_fresh(self):
        reqs=[self.submitted(n) for n in range(10)]
        p=k.join(self.r,'reviewer');v=p['review'];reqs[0]['head_sha']='f'*40;k.submit(self.r,reqs[0])
        with self.assertRaisesRegex(ValueError,'review_head_or_criteria_changed'):
            cycle.submit_review(self.r,dict(agent_id='reviewer',task_id=p['task_id'],review_id=v['id'],head_sha=v['head_sha'],criteria_sha256=v['criteria_sha256'],verdict='PASS',body='old',writes_stopped=True,artifacts=self.artifacts(v['workspace'])))
        self.assertEqual(k.join(self.r,'reviewer')['review']['head_sha'],'f'*40)
    def test_failed_review_reopens_correction(self):
        for n in range(10):self.submitted(n)
        p=k.join(self.r,'reviewer');v=p['review']
        cycle.submit_review(self.r,dict(agent_id='reviewer',task_id=p['task_id'],review_id=v['id'],head_sha=v['head_sha'],criteria_sha256=v['criteria_sha256'],verdict='CHANGES_REQUIRED',body='counterexample retained',writes_stopped=True,artifacts=self.artifacts(v['workspace'])))
        self.assertEqual(k.join(self.r,'replacement')['task_id'],p['task_id'])
    def test_explicit_other_task_requires_checkpoint(self):
        k.join(self.r,'w','T0')
        with self.assertRaisesRegex(ValueError,'checkpoint_active_work_before_switch'):k.join(self.r,'w','T1')
        self.assertEqual(k.join(self.r,'w','T0')['task_id'],'T0')
    def test_bad_artifact_hash_rolls_back(self):
        p=k.join(self.r,'w');a=p['attempt'];art=self.artifacts(a['workspace']);art[0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'artifact_hash_mismatch'):
            cycle.request_publication(self.r,dict(agent_id='w',task_id=p['task_id'],attempt_id=a['id'],criteria_sha256=a['criteria_sha256'],checkpoint='ready',writes_stopped=True,artifacts=art))
        self.assertEqual(k.read(self.r,p['task_id'])['attempts'][a['id']]['state'],'WORKING')

if __name__=='__main__':unittest.main()
