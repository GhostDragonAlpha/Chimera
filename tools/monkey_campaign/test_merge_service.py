import unittest
from types import SimpleNamespace
from merge_service import queue,coordination_actionable

class Tests(unittest.TestCase):
    def test_accepted_only_is_not_worker_actionable(self):
        row={'requests':[],'prs':{'url':{'head_sha':'h','review':{'verdict':'ACCEPTED'}}},'worker_reviews':[dict(state='COMPLETE',verdict='PASS',pr_url='url',head_sha='h')]}
        self.assertFalse(coordination_actionable(row,True))
        self.assertTrue(coordination_actionable(row,False))
        row['prs']['url']['review']=None
        self.assertTrue(coordination_actionable(row,True))

    def test_queue_is_readonly_and_rejects_stale_approval_and_findings(self):
        c={'id':'T','state':'REVIEW','criteria_sha256':'criteria','messages':[], 'prs':{'url':{'head_sha':'h','review':{'verdict':'ACCEPTED','head_sha':'h','criteria_sha256':'criteria'}}}}
        r=SimpleNamespace(readonly=lambda:{'kanban':{'cards':{'T':c}}})
        self.assertEqual(len(queue(r)['ready_for_connected_lead']),1)
        c['prs']['url']['head_sha']='changed'
        self.assertEqual(queue(r)['ready_for_connected_lead'],[])
        c['prs']['url']['head_sha']='h';c['messages']=[{'status':'OPEN','author':'astra-codex','pr_url':'url'}]
        self.assertEqual(queue(r)['ready_for_connected_lead'],[])
        c['state']='DONE';self.assertEqual(queue(r)['blocked'],[])

if __name__=='__main__':unittest.main()
