import concurrent.futures
import copy
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_workflow import GraphWorkflowControl, candidate, file_hash, unpack
from graph_workflow_runner import execute
from control import Control, Refusal
from creature_graph.store import CreatureGraph
from creature_graph.project_documents import absorb, verify
from creature_graph.graphify_projection import make_projection


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.graph = self.root / 'graph.json'
        g = CreatureGraph()
        self.work = {'id': 'work.test', 'name': 'Test work', 'kind': 'work',
                     'priority': 'P0', 'status': 'specified', 'dependencies': [],
                     'execution_workflow': {
                         'statement': 'A missing proof cannot pass the gate',
                         'prediction': 'Review refuses without every check',
                         'read_first': [],
                         'verifier_inputs': {'check.py': hashlib.sha256(b'raise SystemExit(0)').hexdigest()},
                         'checks': [{'id': 'behavior', 'falsifier': 'nonzero exit',
                                     'argv': [sys.executable, '-B', 'check.py'], 'timeout_s': 10}]}}
        g.add(copy.deepcopy(self.work))
        (self.root/'readme.md').write_text('fixture instructions', encoding='utf-8')
        self.docid = absorb(g, self.root, ['readme.md'], 'work.test')[0]['id']
        self.work['execution_workflow']['read_first'] = [self.docid]
        g.objects['work.test'] = copy.deepcopy(self.work)
        g.save(str(self.graph))
        auxiliary = None
        if self._testMethodName.startswith('test_auxiliary'):
            self.marker = 'NONDISCLOSED_CASE_94ae'
            source = 'raise SystemExit('+('1' if 'reject' in self._testMethodName else '0')+')'
            (self.root/'checker.py').write_text(source, encoding='utf-8')
            auxiliary = self.root/'b4b68031-692a-44a4-b0b1-4d667fb6b998.json'
            payload = {'objects': {self.marker: {'checks': [
                {'id': self.marker, 'argv': [sys.executable, '{verifier}/checker.py'], 'timeout_s': 10}],
                'verifier_inputs': {'checker.py': hashlib.sha256(source.encode()).hexdigest()}}},
                'relations': [{'src': self.marker, 'rel': 'verifies', 'dst': 'work.test'}]}
            auxiliary.write_text(json.dumps(payload), encoding='utf-8')
        self.c = GraphWorkflowControl(self.root/'db.sqlite', 'admin', 'enroll',
                                      self.root/'slots', graph_path=self.graph, auxiliary_path=auxiliary)
        self.tokens = {'SUPERVISOR': 'admin'}
        for agent in ('lead', 'worker'):
            self.tokens[agent] = self.c.call('enroll', 'enroll', agent=agent, label=agent)['result']['session_token']
            self.c.call('qualify', 'admin', agent=agent, capabilities=['cpu'], max_tasks=5,
                        can_lead=agent == 'lead', rank=1, evidence='test fixture')
        self.call('offer_lead', 'lead', epoch=0, checkpoint='fixture')
        self.call('elect', 'SUPERVISOR')

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, op, actor='lead', **args):
        return self.c.call(op, self.tokens[actor], **args)['result']

    def create(self, **kw):
        args = dict(task='unit', epoch=1, base='a'*40, scopes=['source'],
                    packet='graph-backed fixture', graph_work='work.test')
        args.update(kw)
        return self.call('create_task', **args)

    def git(self, *args):
        p = subprocess.run(['git', '-c', 'safe.directory='+self.repo.as_posix(),
                            '-C', str(self.repo), *args], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def ready(self, code=0):
        if code != 0:
            self.work['execution_workflow']['verifier_inputs']['check.py'] = hashlib.sha256(('raise SystemExit('+str(code)+')').encode()).hexdigest()
            snap = self.call('graph_snapshot')
            self.call('graph_apply', 'SUPERVISOR', epoch=1, expected_hash=snap['graph_hash'], objects=[self.work])
        self.create()
        self.claim = self.call('claim', 'worker', task='unit')
        self.repo = Path(self.claim['worktree'])
        self.repo.mkdir(parents=True)
        self.git('init')
        (self.repo/'README.md').write_text('fixture instructions', encoding='utf-8')
        (self.repo/'check.py').write_text('raise SystemExit('+str(code)+')', encoding='utf-8')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@local', 'commit', '-m', 'fixture')
        self.context = self.call('workflow_context', 'worker', task='unit')
        self.call('workflow_prepare', 'worker', task='unit', generation=self.claim['generation'],
                  input_hash=self.context['input_hash'], read_hashes={self.docid: file_hash(self.repo/'README.md')})

    def attest(self, code=None):
        receipt = execute(self.context, self.repo, self.root/('run'+str(len(list(self.root.glob('run*'))))))
        from auxiliary_graph import run
        aux = self.call('workflow_verifier_context', 'SUPERVISOR', task='unit')
        receipt['independent'] = run(aux, self.repo, self.root/('private'+str(len(list(self.root.glob('private*'))))))
        if code is not None:
            receipt['checks'][0]['exit_code'] = code
        return receipt, self.call('workflow_attest', 'SUPERVISOR', task='unit', receipt=receipt)

    def submit(self, head=None):
        return self.call('submit_review', 'worker', task='unit', generation=self.claim['generation'],
                         branch=self.claim['branch'], head=head or candidate(self.repo)['head'],
                         evidence='retained runner receipt')

    def test_science_provenance_atomic_and_immutable(self):
        snap = self.call('graph_snapshot')
        source = {'id': 'science.src', 'kind': 'source', 'name': 'source', 'status': 'extracted',
                  'science_funnel': {'bundle': 'fixture'}}
        assertion = {'id': 'science.value', 'kind': 'property_assertion', 'name': 'value',
                     'status': 'extracted', 'provenance': {'source_id': 'science.src'},
                     'science_funnel': {'record': 'fixture'}, 'value': 0}
        edge = {'src': 'science.value', 'rel': 'derived_from', 'dst': 'science.src', 'note': 'fixture'}
        args = dict(epoch=1, expected_hash=snap['graph_hash'], objects=[source, assertion], relations=[edge])
        first = self.call('graph_apply', **args)
        with self.assertRaisesRegex(Refusal, 'revision_conflict'):
            self.call('graph_apply', **args)
        args['expected_hash'] = first['graph_hash']
        self.assertEqual(self.call('graph_apply', **args)['graph_hash'], first['graph_hash'])
        assertion['value'] = 10
        with self.assertRaisesRegex(Refusal, 'science_version_immutable'):
            self.call('graph_apply', **args)

    def test_science_cannot_attach_verification_edges(self):
        snap = self.call('graph_snapshot')
        source = {'id': 'science.src', 'kind': 'source', 'name': 'source', 'status': 'extracted'}
        with self.assertRaisesRegex(Refusal, 'provenance_edges_only'):
            self.call('graph_apply', epoch=1, expected_hash=snap['graph_hash'], objects=[source],
                      relations=[{'src': 'work.test', 'rel': 'verified_by', 'dst': 'science.src', 'note': 'cheat'}])
        self.assertEqual(self.call('graph_snapshot')['graph_hash'], snap['graph_hash'])

    def test_real_funnel_to_serial_controller(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.science_funnel.pipeline import ingest
        from tools.science_funnel.graph import propose
        from tools.science_funnel.common import canonical, sha
        raw = b'id,subject,quantity,value,unit\na,synthetic,pressure,0,Pa\n'
        (self.root/'input.csv').write_bytes(raw)
        manifest = {'schema_version': '1.0.0', 'adapter': 'measurements_csv',
                    'source': {'id': 'fixture', 'release': '1', 'license': 'CC0', 'url': 'local:fixture'},
                    'artifacts': [{'id': 'input', 'path': 'input.csv', 'sha256': sha(raw)}]}
        path = self.root/'manifest.json'
        path.write_bytes(canonical(manifest))
        bundle = ingest(path, self.root/'bundles')
        snap = self.call('graph_snapshot')
        proposal = propose(bundle, unpack(snap['graph']))
        result = self.call('graph_apply', epoch=1, **proposal['payload'])
        self.assertEqual(result['graph_hash'], proposal['metadata']['candidate_graph_hash'])
        actual = unpack(self.call('graph_snapshot')['graph'])
        for obj in proposal['payload']['objects']:
            self.assertEqual(actual.get(obj['id']), obj)
            self.assertEqual(obj['status'], 'extracted')

    def test_test_weakening_refused(self):
        self.ready()
        (self.repo/'check.py').write_text('raise SystemExit(False)', encoding='utf-8')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@local', 'commit', '-m', 'weaken verifier')
        with self.assertRaisesRegex(Refusal, 'verifier_changed'):
            self.attest()

    def test_legacy_service_cannot_open_gated_database(self):
        with self.assertRaisesRegex(Refusal, 'graph_workflow_service_required'):
            Control(self.root/'db.sqlite', 'admin', 'enroll', self.root/'slots')

    def test_lead_cannot_weaken_own_acceptance(self):
        snap = self.call('graph_snapshot')
        obj = copy.deepcopy(self.work)
        obj['execution_workflow']['checks'][0]['falsifier'] = 'easier condition'
        with self.assertRaisesRegex(Refusal, 'independent_contract_approval_required'):
            self.call('graph_apply', epoch=1, expected_hash=snap['graph_hash'], objects=[obj])

    def test_auxiliary_hidden_from_workers(self):
        self.ready(); self.attest()
        for op, args in [('snapshot', {}), ('graph_snapshot', {}), ('workflow_view', {}), ('workflow_context', {'task': 'unit'})]:
            self.assertNotIn(self.marker, json.dumps(self.call(op, 'worker', **args)))
        with self.assertRaisesRegex(Refusal, 'trusted_verifier_only'):
            self.call('workflow_verifier_context', 'worker', task='unit')
        self.assertEqual(self.submit()['state'], 'REVIEW')

    def test_auxiliary_reject_blocks_public_green(self):
        self.ready(); _, result = self.attest()
        self.assertFalse(result['all_passed'])
        with self.assertRaisesRegex(Refusal, 'independent_checks_failed'):
            self.submit()

    def test_unknown_graph_work_refused(self):
        with self.assertRaisesRegex(Refusal, 'unknown_graph_work'):
            self.create(graph_work='work.missing')

    def test_checklist_required(self):
        snap = self.call('graph_snapshot')
        obj = copy.deepcopy(self.work); obj.pop('execution_workflow')
        self.call('graph_apply', 'SUPERVISOR', epoch=1, expected_hash=snap['graph_hash'], objects=[obj])
        with self.assertRaisesRegex(Refusal, 'checklist_missing'):
            self.create()

    def test_unique_work_claim(self):
        self.create()
        with self.assertRaisesRegex(Refusal, 'already_active'):
            self.create(task='duplicate')

    def test_missing_proof_refused(self):
        self.ready()
        with self.assertRaisesRegex(Refusal, 'proof_required'):
            self.submit()

    def test_worker_cannot_attest(self):
        self.ready()
        with self.assertRaisesRegex(Refusal, 'trusted_runner_only'):
            self.call('workflow_attest', 'worker', task='unit', receipt={})

    def test_failure_retained_but_review_refused(self):
        self.ready(3)
        _, result = self.attest()
        self.assertFalse(result['all_passed'])
        with self.assertRaisesRegex(Refusal, 'checks_failed'):
            self.submit()
        self.assertEqual(self.call('snapshot')['tasks']['unit']['workflow_history'][0]['checks'][0]['exit_code'], 3)

    def test_real_runner_to_review(self):
        self.ready()
        self.attest()
        self.assertEqual(self.submit()['state'], 'REVIEW')

    def test_different_candidate_refused(self):
        self.ready(); self.attest()
        with self.assertRaisesRegex(Refusal, 'candidate_mismatch'):
            self.submit('b'*40)

    def test_dirty_candidate_refused(self):
        self.ready(); self.attest()
        (self.repo/'check.py').write_text('raise SystemExit(9)', encoding='utf-8')
        with self.assertRaisesRegex(Refusal, 'candidate_not_clean'):
            self.submit()

    def test_tampered_artifact_refused(self):
        self.ready(); receipt, _ = self.attest()
        Path(receipt['checks'][0]['log']).write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(Refusal, 'evidence_changed'):
            self.submit()

    def test_graph_contract_change_refuses_old_proof(self):
        self.ready(); self.attest()
        snap = self.call('graph_snapshot')
        obj = copy.deepcopy(self.work); obj['execution_workflow']['prediction'] = 'new prediction'
        self.call('graph_apply', 'SUPERVISOR', epoch=1, expected_hash=snap['graph_hash'], objects=[obj])
        with self.assertRaisesRegex(Refusal, 'graph_inputs_changed'):
            self.submit()

    def test_serial_conflict_one_winner(self):
        snap = self.call('graph_snapshot')
        def update(i):
            obj = copy.deepcopy(self.work); obj['notes'] = str(i)
            try:
                self.call('graph_apply', epoch=1, expected_hash=snap['graph_hash'], objects=[obj])
                return True
            except Refusal:
                return False
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            self.assertEqual(sum(pool.map(update, [1, 2])), 1)

    def test_direct_promotion_refused(self):
        snap = self.call('graph_snapshot')
        obj = copy.deepcopy(self.work); obj['status'] = 'verified'
        with self.assertRaisesRegex(Refusal, 'promotion_requires'):
            self.call('graph_apply', epoch=1, expected_hash=snap['graph_hash'], objects=[obj])

    def test_document_roundtrip_and_projection(self):
        raw = b'# Exact bytes\r\n\xc3\xa9\r\n'
        (self.root/'note.md').write_bytes(raw)
        g = unpack(self.call('graph_snapshot')['graph'])
        receipt = absorb(g, self.root, ['note.md'], 'work.test')
        oid = receipt[0]['id']
        self.assertEqual(verify(g.get(oid)), raw)
        node = next(n for n in make_projection(g)['nodes'] if n['_authored_id'] == oid)
        self.assertEqual(node['record']['document'], g.get(oid)['document'])
        self.assertEqual(node['spatial'], {'anchored_to': 'work.test'})
        self.assertEqual(len(absorb(g, self.root, ['note.md'], 'work.test')), 1)
        self.assertEqual(len(g.objects), 3)

    def test_import_is_atomic_on_bad_path(self):
        (self.root/'note.md').write_text('retained')
        g = unpack(self.call('graph_snapshot')['graph'])
        before = g.graph_hash()
        with self.assertRaises(ValueError):
            absorb(g, self.root, ['note.md', 'missing.md'], 'work.test')
        self.assertEqual(before, g.graph_hash())

    def test_restart_does_not_reimport_old_file(self):
        snap = self.call('graph_snapshot')
        obj = copy.deepcopy(self.work); obj['notes'] = 'authoritative update'
        changed = self.call('graph_apply', epoch=1, expected_hash=snap['graph_hash'], objects=[obj])
        self.c = GraphWorkflowControl(self.root/'db.sqlite', 'admin', 'enroll', self.root/'slots', graph_path=self.graph)
        self.assertEqual(self.call('graph_snapshot')['graph_hash'], changed['graph_hash'])


if __name__ == '__main__':
    unittest.main()
