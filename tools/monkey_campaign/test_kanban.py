"""Task-card concurrency and exact-head acceptance regressions; isolated stores only."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_slots import Registry
import kanban as k


def spec(tid, deps=()):
    return dict(id=tid, objective='Implement '+tid, falsifier='Incorrect result refuses',
                steps=['Implement and verify'], completion='Reviewed merged PR', depends_on=list(deps))


class KanbanTests(unittest.TestCase):
    def test_board_and_inbox_reads_never_open_a_write_transaction(self):
        self.init()
        before=self.registry.readonly()['revision']
        with patch.object(self.registry,'transaction',side_effect=AssertionError('write forbidden')):
            self.assertEqual(k.read(self.registry)['active_count'],10)
            self.assertEqual(k.read(self.registry,'T0')['id'],'T0')
        self.assertEqual(self.registry.readonly()['revision'],before)

    def test_submit_moves_worker_to_another_card_and_explicit_revisit_recovers_attempt(self):
        self.init()
        submitted=self.submission()
        other=k.join(self.registry,'worker')
        self.assertNotEqual(other['task_id'],submitted['task_id'])
        k.park(self.registry,dict(task_id=other['task_id'],attempt_id=other['attempt']['id'],agent_id='worker',
            checkpoint='saved own outputs',writes_stopped=True))
        revisit=k.join(self.registry,'worker','T0')
        self.assertEqual(revisit['attempt']['id'],submitted['attempt_id'])

    def test_operator_stop_preserves_legacy_work_and_no_clock_expiry(self):
        self.registry.clock=lambda:100
        self.registry.register(dict(agent_id='legacy',task_id='T0',ownership_reference='existing ownership',
            workspace='existing workspace',checkpoint='saved code',next_action='finish',phase='implement',
            instruction_revision='old',instruction_bundle_sha256='a'*64,adopt_existing=True))
        k.initialize(self.registry,[spec('T'+str(i)) for i in range(11)],k.LEAD,workers_stopped=True)
        snapshot=self.registry.snapshot()
        self.assertEqual(snapshot['registered_agents'],0)
        self.assertEqual(k.read(self.registry,'T0')['legacy_work'][0]['workspace'],'existing workspace')
        self.registry.clock=lambda:10**10
        self.assertEqual(k.read(self.registry)['active_count'],10)
        self.assertEqual(self.registry.snapshot()['registered_agents'],0)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.registry = Registry(Path(self.tmp.name))
        self.registry.initialize()

    def init(self, count=11, specs=None):
        return k.initialize(self.registry, specs or [spec('T'+str(i)) for i in range(count)], k.LEAD)

    def submission(self, agent='worker', task='T0', number=1, head='a'*40):
        packet = k.join(self.registry, agent, task)
        args = dict(task_id=task, agent_id=agent, attempt_id=packet['attempt']['id'],
                    criteria_sha256=packet['attempt']['criteria_sha256'],
                    pr_url=f'https://github.com/{k.REPO}/pull/{number}', head_sha=head)
        k.submit(self.registry, args)
        return args

    def approve(self, submission, **changes):
        args = dict(submission, actor=k.LEAD, verdict='ACCEPTED',
                    evidence_reference='independent checked evidence', body='Criteria verified')
        args.update(changes)
        return k.review(self.registry, args)

    def github(self, submission, **changes):
        result = dict(merged=True, html_url=submission['pr_url'], base={'ref':k.BASE},
                      head={'sha':submission['head_sha']}, merge_commit_sha='f'*40,
                      merged_at='2026-09-25T00:00:00Z')
        result.update(changes)
        return result

    def accept(self, submission, github=None):
        return k.accept_merge(self.registry, dict(submission, actor=k.LEAD),
                              github if github is not None else self.github(submission))

    def test_ten_cards_and_backlog_not_worker_capacity(self):
        state = self.init(15)
        self.assertEqual((state['active_count'], state['backlog_count']), (10, 5))
        with ThreadPoolExecutor(max_workers=12) as pool:
            packets = list(pool.map(lambda n:k.join(self.registry, 'agent-'+str(n), 'T0'), range(12)))
        self.assertEqual(len({p['attempt']['workspace'] for p in packets}), 12)
        self.assertEqual(len({p['attempt']['branch'] for p in packets}), 12)
        self.assertEqual(k.read(self.registry)['active_count'], 10)

    def test_rejected_review_follows_task_to_another_worker(self):
        self.init()
        submission = self.submission()
        self.approve(submission, verdict='CHANGES_REQUIRED', body='Fix collision penetration')
        packet = k.join(self.registry, 'replacement', 'T0')
        message = packet['task_inbox'][0]
        self.assertEqual(message['body'], 'Fix collision penetration')
        self.assertEqual(message['status'], 'OPEN')
        k.post(self.registry, dict(task_id='T0', author='replacement', body='Reproduced and fixed', reply_to=message['id']))
        self.assertEqual(k.read(self.registry, 'T0')['messages'][0]['status'], 'OPEN')
        with self.assertRaisesRegex(ValueError, 'unresolved_lead_feedback'):
            self.approve(submission)
        self.approve(submission, resolved_message_ids=[message['id']])
        self.assertEqual(k.read(self.registry, 'T0')['messages'][0]['status'], 'RESOLVED')

    def test_new_head_invalidates_review(self):
        self.init()
        submission = self.submission()
        self.approve(submission)
        changed = dict(submission, head_sha='b'*40)
        k.submit(self.registry, changed)
        self.assertIsNone(k.read(self.registry, 'T0')['prs'][submission['pr_url']]['review'])
        with self.assertRaisesRegex(ValueError, 'merged_head_not_approved'):
            self.accept(changed)
        with self.assertRaisesRegex(ValueError, 'review_head_changed'):
            self.approve(submission)

    def test_unmerged_wrong_url_base_and_unapproved_are_refused(self):
        self.init()
        submission = self.submission()
        cases = [({'merged':False}, 'github_merge_not_verified'),
                 ({'html_url':'https://github.com/other/repo/pull/1'}, 'github_merge_not_verified'),
                 ({'base':{'ref':'master'}}, 'wrong_merge_base')]
        for changes, error in cases:
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, error):
                self.accept(submission, self.github(submission, **changes))
        with self.assertRaisesRegex(ValueError, 'merged_head_not_approved'):
            self.accept(submission)
        self.assertNotEqual(k.read(self.registry, 'T0')['state'], 'DONE')

    def test_approved_merge_refills_once_and_retry_is_idempotent(self):
        self.init()
        submission = self.submission()
        self.approve(submission)
        result = self.accept(submission)
        self.assertEqual(result['state'], 'COMPLETED')
        self.assertEqual(result['board']['active_count'], 10)
        self.assertEqual(result['winner']['head_sha'], 'a'*40)
        self.assertEqual(result['winner']['merge_commit_sha'], 'f'*40)
        self.assertEqual(k.read(self.registry, 'T10')['slot'], k.read(self.registry, 'T0')['slot'])
        before = k.read(self.registry)
        self.assertEqual(self.accept(submission)['state'], 'ALREADY_COMPLETED')
        self.assertEqual(k.read(self.registry), before)

    def test_competing_acceptance_has_one_winner_one_refill(self):
        self.init(12)
        submissions = [self.submission('worker'+str(n), number=n+1, head=str(n+1)*40) for n in range(2)]
        for submission in submissions:
            self.approve(submission)
        def attempt(submission):
            try:
                return self.accept(submission)['state']
            except ValueError as error:
                return str(error)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, submissions))
        self.assertCountEqual(results, ['COMPLETED', 'another_pr_already_won'])
        state = k.read(self.registry)
        self.assertEqual(state['active_count'], 10)
        self.assertEqual(state['backlog_count'], 1)
        self.assertEqual(sum(c['state']=='DONE' for c in state['cards']), 1)

    def test_dependencies_do_not_refill_until_merged(self):
        specs = [spec('T0'), spec('T1', ['T0']), spec('T2', ['T1'])]
        self.init(specs=specs)
        self.assertEqual(k.read(self.registry)['active_count'], 1)
        submission = self.submission()
        self.approve(submission)
        self.assertEqual(k.read(self.registry)['backlog_count'], 2)
        self.accept(submission)
        state = k.read(self.registry)
        self.assertEqual((state['active_count'], state['backlog_count']), (1, 1))
        self.assertEqual(k.read(self.registry, 'T1')['state'], 'OPEN')


if __name__ == '__main__':
    unittest.main()
