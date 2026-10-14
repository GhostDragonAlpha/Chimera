import tempfile
import unittest
from pathlib import Path
from agent_slots import Registry
from test_kanban import spec
import kanban as k
import continuous_cycle as cycle
from review_allocation import request_review


class Routing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.r = Registry(Path(self.tmp.name)); self.r.initialize()
        k.initialize(self.r, [spec('A'), spec('B')], k.LEAD)
        with self.r.transaction() as state:
            b = state['kanban']; b.update(continuous_cycle=True, separate_review_lane=True)
            for n, c in enumerate(b['cards'].values()):
                c.update(state='REVIEW', lane='REVIEW')
                c['attempts'] = {'a': dict(agent_id='author', state='PR_SUBMITTED')}
                c['prs'] = {'https://github.com/'+k.REPO+'/pull/'+str(900+n):
                            dict(head_sha=str(n)*40, attempt_id='a', review=None)}

    def test_uncovered_candidate_before_duplicate(self):
        first = cycle.join(self.r, 'r1'); second = cycle.join(self.r, 'r2')
        self.assertNotEqual(first['task_id'], second['task_id'])
        self.assertEqual(cycle.join(self.r, 'r3')['state'], 'AWAITING_LEAD_ACTION')

    def test_explicit_task_review_stays_on_requested_card(self):
        self.assertEqual(cycle.join(self.r, 'r1', 'B')['task_id'], 'B')

    def test_completed_pass_counts_as_coverage(self):
        p = cycle.join(self.r, 'r1')
        with self.r.transaction() as s:
            s['kanban']['cards'][p['task_id']]['worker_reviews'][0].update(state='COMPLETE', verdict='PASS')
        self.assertNotEqual(cycle.join(self.r, 'r2')['task_id'], p['task_id'])

    def test_accepted_review_is_not_resumed(self):
        p = cycle.join(self.r, 'r1')
        with self.r.transaction() as s:
            c = s['kanban']['cards'][p['task_id']]
            c['prs'][p['review']['pr_url']]['review'] = dict(verdict='ACCEPTED', head_sha=p['review']['head_sha'])
        self.assertNotEqual(cycle.join(self.r, 'r1')['task_id'], p['task_id'])
        self.assertEqual(self.r.readonly()['kanban']['cards'][p['task_id']]['worker_reviews'][0]['state'], 'STALE')

    def test_existing_excess_retires_only_callers_record(self):
        p = cycle.join(self.r, 'r1')
        with self.r.transaction() as s:
            c = s['kanban']['cards'][p['task_id']]
            c['worker_reviews'].append(dict(p['review'], id='extra', agent_id='r2'))
        self.assertNotEqual(cycle.join(self.r, 'r2')['task_id'], p['task_id'])
        self.assertEqual(self.r.readonly()['kanban']['cards'][p['task_id']]['worker_reviews'][0]['state'], 'WORKING')

    def test_new_implementation_does_not_duplicate_owned_work(self):
        with self.r.transaction() as state:
            for c in state['kanban']['cards'].values():
                c.update(state='OPEN', lane='DEVELOPMENT', prs={}, attempts={})
        first = cycle.join(self.r, 'w1'); second = cycle.join(self.r, 'w2')
        self.assertNotEqual(first['task_id'], second['task_id'])
        self.assertEqual(cycle.join(self.r, 'w3')['state'], 'AWAITING_LEAD_ACTION')
        self.assertEqual(cycle.join(self.r, 'w1')['state'], 'RESUME_ATTEMPT')

    def test_author_cannot_review(self):
        self.assertEqual(cycle.join(self.r, 'author')['state'], 'AWAITING_LEAD_ACTION')

    def test_lead_extra_review_requires_reason_and_exact_head(self):
        p = cycle.join(self.r, 'r1'); cycle.join(self.r, 'r2')
        args = dict(actor=k.LEAD, task_id=p['task_id'], pr_url=p['review']['pr_url'],
                    head_sha=p['review']['head_sha'], reason='Independent numerical oracle')
        with self.assertRaises(ValueError): request_review(self.r, dict(args, actor='worker'))
        with self.assertRaises(ValueError): request_review(self.r, dict(args, head_sha='f'*40))
        request_review(self.r, args)
        self.assertEqual(cycle.join(self.r, 'r3')['task_id'], p['task_id'])


if __name__ == '__main__': unittest.main()
