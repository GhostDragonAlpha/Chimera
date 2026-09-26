import unittest,tempfile
from pathlib import Path
from agent_slots import Registry
from test_kanban import spec
import kanban as k
import review_lane as lane
import continuous_cycle as cycle

class Tests(unittest.TestCase):
    def test_old_rejection_routes_replacement_review_without_new_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            r=Registry(Path(folder));r.initialize();k.initialize(r,[spec('R5')],k.LEAD)
            with r.transaction() as s:
                b=s['kanban'];b.update(separate_review_lane=True,continuous_cycle=True)
                c=b['cards']['R5'];c.update(state='CHANGES_REQUESTED')
                c['attempts']={'old':{'agent_id':'author'},'new':{'agent_id':'author2'}}
                for n,aid,head in [(115,'old','a'*40),(126,'new','b'*40)]:
                    url='https://github.com/'+k.REPO+'/pull/'+str(n)
                    c['prs'][url]=dict(head_sha=head,attempt_id=aid,criteria_sha256=c['criteria_sha256'],review=None)
                oldurl=list(c['prs'])[0];newurl=list(c['prs'])[1]
                c['worker_reviews']=[dict(id='old-review',agent_id='reviewer',state='COMPLETE',verdict='CHANGES_REQUIRED',pr_url=oldurl,head_sha='a'*40,criteria_sha256=c['criteria_sha256'])]
                lane.corrections(b,c);k.refill(b)
                self.assertEqual(c['lane'],'REVIEW')
            # Minimal fixture attempts need state for the normal resume scan.
            with r.transaction() as s:
                for a in s['kanban']['cards']['R5']['attempts'].values():a['state']='PR_SUBMITTED'
            result=cycle.join(r,'reviewer')
            self.assertEqual(result['state'],'REVIEW_ASSIGNED')
            self.assertEqual(result['review']['pr_url'],newurl)
            self.assertEqual(len(k.read(r,'R5')['attempts']),2)
            with r.transaction() as s:
                c=s['kanban']['cards']['R5'];c['prs'][newurl]['review']={'verdict':'CHANGES_REQUIRED','head_sha':'b'*40}
                c['state']='CHANGES_REQUESTED';lane.corrections(s['kanban'],c);k.refill(s['kanban'])
                self.assertEqual(c['lane'],'DEVELOPMENT')

if __name__=='__main__':unittest.main()
