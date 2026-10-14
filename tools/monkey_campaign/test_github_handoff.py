import unittest
from unittest.mock import patch
import verified_submission as v
import operational_lead as op
import continuous_cycle as cycle
from test_operational_lead import Tests as Existing

class IntakeTests(unittest.TestCase):
    def test_missing_or_wrong_head_cannot_mutate_registry(self):
        args={'pr_url':'https://github.com/GhostDragonAlpha/Chimera/pull/117','head_sha':'a'*40}
        with patch.object(v.kanban,'submit') as write:
            for remote in [{},{'state':'open','html_url':args['pr_url'],'head':{'sha':'b'*40}}]:
                with self.assertRaises(ValueError):v.submit(None,args,lambda _:remote)
            with self.assertRaises(OSError):v.submit(None,args,lambda _:(_ for _ in ()).throw(OSError('404')))
            write.assert_not_called()

class RoutingTests(Existing):
    def test_external_block_is_not_reassigned_until_queue_changes(self):
        role=cycle.join(self.r,'worker')['operational_lead']
        op.release(self.r,dict(actor='worker',role_token=role['token'],checkpoint='published; API unavailable',writes_stopped=True,defer_unchanged_queue=True,blocker_reason='No PR API credential in this harness'))
        self.assertNotEqual(cycle.join(self.r,'worker')['state'],'OPERATIONAL_LEAD_ASSIGNED')
        with self.r.transaction() as s:s['kanban']['cards']['T0']['publication_requests'][0]['id']='new-request'
        self.assertEqual(cycle.join(self.r,'worker')['state'],'OPERATIONAL_LEAD_ASSIGNED')

if __name__=='__main__':unittest.main()
