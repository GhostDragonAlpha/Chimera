from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from agent_slots import Registry
from task_queue import claim_next

def brief(i):
    return {'id':str(i),'kind':'bounded_diagnostic','source_edit_allowed':False,'gpu_allowed':False,
            'output_directory':'fixture-only/'+str(i),'steps':['Read fixture receipt']}

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.r=Registry(self.t.name,clock=lambda:100);self.r.initialize()
        self.r.reconcile({'expected_registered_agents':0,'live_inventory_reference':'isolated fixture, no real workers'})
    def test_concurrent_claims_unique_and_capacity(self):
        with ThreadPoolExecutor(max_workers=12) as pool:
            results=list(pool.map(lambda i:claim_next(Registry(self.t.name,clock=lambda:100),[brief(k) for k in range(12)],str(i),'fixture','0'*64),range(12)))
        claimed=[r for r in results if r['state']=='ASSIGNED']
        self.assertEqual(len(claimed),10)
        self.assertEqual(len({r['brief']['id'] for r in claimed}),10)
        self.assertEqual(len({r['slot']['slot'] for r in claimed}),10)
    def test_repeat_recovers_and_expiry_does_not_reassign(self):
        claim_next(self.r,[brief(1)],'a','fixture','0'*64)
        self.assertEqual(claim_next(self.r,[brief(1)],'a','fixture','0'*64)['state'],'RECOVER_OWNED_ASSIGNMENT')
        self.r.clock=lambda:3600
        self.assertEqual(claim_next(self.r,[brief(1)],'b','fixture','0'*64)['state'],'NO_UNCLAIMED_AUTHORIZED_TASK')
        self.assertEqual(self.r.snapshot()['slots'][0]['lease_state'],'EXPIRED_RECOVERY_REQUIRED')
    def test_source_edits_refused(self):
        b=brief(1);b['source_edit_allowed']=True
        with self.assertRaisesRegex(ValueError,'authority_violation'):claim_next(self.r,[b],'a','fixture','0'*64)
        self.assertEqual(self.r.snapshot()['registered_agents'],0)

if __name__=='__main__':unittest.main()
