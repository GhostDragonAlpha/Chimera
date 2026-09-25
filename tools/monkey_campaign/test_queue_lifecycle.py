"""End-to-end queue handoff and adversarial ownership checks, isolated from live state."""
import tempfile
import unittest
from pathlib import Path

from agent_slots import Registry
from task_queue import claim_next, finish, checkpoint, evidence, publish, rework


class QueueLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stamp = 100.0
        self.registry = Registry(self.root, clock=lambda: self.stamp)
        self.registry.initialize()
        self.registry.reconcile({'expected_registered_agents': 0,
                                 'live_inventory_reference': 'isolated fixture'})
        self.briefs = [self.brief('A'), self.brief('B', ['A'])]

    def brief(self, name, dependencies=None):
        return {'id': name, 'kind': 'bounded_diagnostic', 'objective': 'Fixture ' + name,
                'source_edit_allowed': False, 'gpu_allowed': False,
                'output_directory': str(self.root / 'task-results' / name),
                'steps': ['Read fixture evidence'], 'depends_on': dependencies or []}

    def claim(self, agent):
        return claim_next(self.registry, self.briefs, agent, 'fixture-1', 'a' * 64)

    def arguments(self, allocation, contents='durable fixture evidence'):
        slot = allocation['slot']
        path = Path(allocation['brief']['output_directory']) / 'report.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding='utf-8')
        return {'slot': slot['slot'], 'generation': slot['generation'],
                'agent_id': slot['agent_id'], 'worker_finished_confirmed': True,
                'report_path': str(path)}

    def submit_author(self):
        allocated = self.claim('author')
        arguments = self.arguments(allocated)
        result = finish(self.registry, arguments)
        self.assertEqual(result['state'], 'REVIEW')
        self.assertFalse(result['planning_acceptance_claimed'])
        return allocated, arguments

    def test_finish_review_accept_unlocks_successor_and_releases_both_slots(self):
        author, _ = self.submit_author()
        self.assertEqual(self.registry.snapshot()['registered_agents'], 0)
        reviewer = self.claim('independent')
        self.assertEqual(reviewer['brief']['review_of'], 'A')
        args = self.arguments(reviewer, 'Independent checks passed')
        args.update(verdict='PASS', reviewed_sha256=reviewer['brief']['submission']['raw_sha256'])
        self.assertEqual(finish(self.registry, args)['state'], 'ACCEPTED')
        self.assertEqual(self.registry.snapshot()['registered_agents'], 0)
        successor = self.claim('author')
        self.assertEqual(successor['brief']['id'], 'B')
        self.assertGreater(successor['slot']['generation'], author['slot']['generation'])

    def test_author_is_not_offered_own_review_or_dependent_task(self):
        self.submit_author()
        self.assertEqual(self.claim('author')['state'], 'NO_UNCLAIMED_AUTHORIZED_TASK')
        self.assertEqual(self.registry.snapshot()['registered_agents'], 0)

    def test_progress_memory_does_not_replace_assignment_authority(self):
        allocation=self.claim('author');slot=allocation['slot']
        self.registry.report(dict(agent_id='author',slot=slot['slot'],generation=slot['generation'],
            phase='derive',checkpoint='progress',last_action='read evidence',next_action='write report',
            instruction_revision='fixture-1',instruction_bundle_sha256='a'*64,memory={'facts':'new progress'}))
        recovered=self.claim('author')
        self.assertEqual(recovered['brief']['id'],'A')
        self.assertEqual(finish(self.registry,self.arguments(allocation))['state'],'REVIEW')

    def coordinator(self):
        self.registry.coordinator(dict(coordinator_id='fixture-coordinator',checkpoint='fixture',
            last_action='fixture',next_action='fixture',evidence_reference='fixture'))

    def test_rejected_review_requires_explicit_correction_then_preserves_evidence(self):
        self.coordinator(); self.submit_author()
        reviewer=self.claim('independent')
        args=self.arguments(reviewer,'Counterexample found')
        args.update(verdict='CHANGES_REQUIRED',reviewed_sha256=reviewer['brief']['submission']['raw_sha256'])
        finish(self.registry,args)
        self.assertEqual(self.claim('author')['state'],'NO_UNCLAIMED_AUTHORIZED_TASK')
        rework(self.registry,dict(coordinator_id='fixture-coordinator',task_id='A',correction='Address exact counterexample'))
        corrected=self.claim('author')
        self.assertEqual(corrected['brief']['correction'],'Address exact counterexample')
        self.assertIn('previous_review',corrected['brief'])

    def test_published_followup_and_builtin_collision(self):
        self.coordinator()
        b=self.brief('C')
        b.update(planning_ids=['W03'],falsifier='An unsupported result fails',completion='Reviewed evidence',
                 read_first=['fixture'],deliverables=['report.md'],max_new_output_bytes=1024)
        a={'coordinator_id':'fixture-coordinator','brief':b}
        catalog={'W03':{'scope':'core'}}
        with self.assertRaisesRegex(ValueError,'builtin_task_id_reserved'):
            publish(self.registry,a,catalog,['C'])
        publish(self.registry,a,catalog,['A','B'])
        self.claim('author')
        claimed=self.claim('another')
        self.assertEqual(claimed['brief']['id'],'C')

    def test_outside_evidence_refused_without_releasing_claim(self):
        assigned = self.claim('author')
        args = self.arguments(assigned)
        outside = self.root / 'outside.md'
        outside.write_text('outside', encoding='utf-8')
        args['report_path'] = str(outside)
        with self.assertRaisesRegex(ValueError, 'evidence_outside_assignment'):
            finish(self.registry, args)
        self.assertEqual(self.registry.snapshot()['diagnostic_claims']['A']['state'], 'CLAIMED')
        self.assertEqual(self.registry.snapshot()['registered_agents'], 1)

    def test_parent_traversal_cannot_escape_evidence_directory(self):
        root = self.root / 'assigned'
        root.mkdir()
        outside = self.root / 'outside.md'
        outside.write_text('outside', encoding='utf-8')
        with self.assertRaises(ValueError):
            evidence(root / '..' / 'outside.md', root)

    def test_mutated_submission_cannot_be_accepted(self):
        _, author_args = self.submit_author()
        reviewer = self.claim('independent')
        args = self.arguments(reviewer)
        args.update(verdict='PASS', reviewed_sha256=reviewer['brief']['submission']['raw_sha256'])
        Path(author_args['report_path']).write_text('changed after submission', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'submission_changed'):
            finish(self.registry, args)
        self.assertEqual(self.registry.snapshot()['diagnostic_claims']['A']['state'], 'REVIEW_CLAIMED')

    def test_expired_assignment_requires_explicit_checkpoint_before_resume(self):
        assigned = self.claim('author')
        args = self.arguments(assigned, 'Recover from this exact checkpoint')
        self.stamp = 3601.0
        with self.assertRaisesRegex(ValueError, 'assignment_expired'):
            finish(self.registry, args)
        self.assertEqual(self.claim('replacement')['state'], 'NO_UNCLAIMED_AUTHORIZED_TASK')
        checkpoint(self.registry, args)
        resumed = self.claim('replacement')
        self.assertEqual(resumed['brief']['id'], 'A')
        self.assertEqual(resumed['slot']['lease_state'], 'ACTIVE')
        self.assertEqual(resumed['brief']['recovery_checkpoint']['path'], args['report_path'])
        self.assertGreater(resumed['slot']['generation'], assigned['slot']['generation'])
        with self.assertRaisesRegex(ValueError, 'stale_or_wrong_agent_registration'):
            finish(self.registry, args)

    def test_stale_generation_cannot_finish_reused_slot(self):
        original, old_args = self.submit_author()
        reviewer = self.claim('independent')
        self.assertEqual(reviewer['slot']['slot'], original['slot']['slot'])
        forged = dict(old_args, agent_id='independent')
        with self.assertRaisesRegex(ValueError, 'stale_or_wrong_agent_registration'):
            finish(self.registry, forged)
        self.assertEqual(self.registry.snapshot()['registered_agents'], 1)


if __name__ == '__main__':
    unittest.main()
