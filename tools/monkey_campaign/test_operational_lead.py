from pathlib import Path
import tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from agent_slots import Registry
import kanban as k
import continuous_cycle as cycle
import operational_lead as op
from test_kanban import spec

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.r=Registry(Path(self.tmp.name));self.r.initialize();k.initialize(self.r,[spec('T0')],k.LEAD)
        with self.r.transaction() as s:
            b=s['kanban'];b.update(continuous_cycle=True,operational_takeover=True)
            c=b['cards']['T0'];c['publication_branch']='branch-1';c['state']='CHANGES_REQUESTED'
            c['attempts']['attempt']={'id':'attempt','agent_id':'author','state':'PUBLICATION_REQUESTED','criteria_sha256':c['criteria_sha256'],'workspace':str(Path(self.tmp.name)/'attempt')}
            c['publication_requests']=[dict(id='req',attempt_id='attempt',agent_id='author',status='PENDING',criteria_sha256=c['criteria_sha256'])]

    def test_takeover_and_no_duplicate_correction_draw(self):
        result=cycle.join(self.r,'coordinator');self.assertEqual(result['state'],'OPERATIONAL_LEAD_ASSIGNED')
        other=cycle.join(self.r,'other');self.assertEqual(other['state'],'AWAITING_LEAD_ACTION')
        self.assertEqual(len(k.read(self.r,'T0')['attempts']),1)
        role=result['operational_lead']
        op.release(self.r,dict(actor='coordinator',role_token=role['token'],checkpoint='saved',writes_stopped=True))
        self.assertEqual(cycle.join(self.r,'replacement')['state'],'OPERATIONAL_LEAD_ASSIGNED')

    def test_concurrent_claim_has_one_holder(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda who:cycle.join(self.r,who),['one','two']))
        self.assertEqual(sum(r['state']=='OPERATIONAL_LEAD_ASSIGNED' for r in results),1)

    def test_publication_independent_approval_and_merge(self):
        role=cycle.join(self.r,'author')['operational_lead']
        c=k.read(self.r,'T0');a=dict(actor='author',role_token=role['token'],task_id='T0',request_id='req',criteria_sha256=c['criteria_sha256'],pr_url='https://github.com/'+k.REPO+'/pull/123',head_sha='a'*40)
        gh=dict(html_url=a['pr_url'],state='open',head={'sha':a['head_sha'],'ref':'branch-1'},base={'ref':k.BASE})
        op.record_pr(self.r,a,gh)
        review=dict(a,verdict='ACCEPTED',body='verified',evidence_reference='receipt')
        with self.assertRaisesRegex(ValueError,'independent_review_required'):k.review(self.r,review)
        with self.r.transaction() as s:
            s['kanban']['cards']['T0']['worker_reviews']=[dict(state='COMPLETE',verdict='PASS',agent_id='independent',head_sha=a['head_sha'],criteria_sha256=a['criteria_sha256'],pr_url=a['pr_url'])]
        k.review(self.r,review)
        op.record_pr(self.r,a,gh) # retry preserves approval
        self.assertEqual(k.read(self.r,'T0')['prs'][a['pr_url']]['review']['verdict'],'ACCEPTED')
        gh.update(merged=True,merge_commit_sha='f'*40)
        self.assertEqual(k.accept_merge(self.r,a,gh)['state'],'COMPLETED')

    def test_role_does_not_grant_architecture(self):
        role=cycle.join(self.r,'worker')['operational_lead']
        with self.assertRaisesRegex(ValueError,'lead_action_required'):
            k.enqueue(self.r,dict(actor='worker',role_token=role['token'],spec=spec('UNAUTHORIZED')))
        with self.assertRaisesRegex(ValueError,'operational_lead_required'):
            op.release(self.r,dict(actor='impostor',role_token=role['token'],checkpoint='x',writes_stopped=True))

if __name__=='__main__':unittest.main()
