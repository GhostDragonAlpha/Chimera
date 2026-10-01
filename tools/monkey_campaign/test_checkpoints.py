import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import checkpoints as c

SCOPE = '1' * 64


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subject = self.artifact('subject.json', b'{"fixture":"synthetic identity, no real build"}')
        criteria = self.artifact('criteria.json', b'{"fixture":"frozen synthetic criteria"}')
        self.ctx = {'schema':'chimera.checkpoint_context.v1', 'scope_sha256':SCOPE,
                    'task_id':'W10', 'controller_task':'walking-scene', 'generation':3,
                    'subject_sha256':subject['sha256'], 'criteria_sha256':criteria['sha256'],
                    'run_id':'trial-1', 'worker_id':'worker-1', 'kind':'motion',
                    'required_gates':list(c.ORDER[:-1])}
        self.ctx_path = self.root/'context.json'
        self.pin_context()
        self.receipt = {'schema':'chimera.checkpoint_receipt.v1', 'context_sha256':self.pin,
                        **{k:self.ctx[k] for k in ('scope_sha256','task_id','controller_task','generation',
                           'subject_sha256','criteria_sha256','run_id')},
                        'subject_manifest':subject, 'criteria_manifest':criteria, 'gates':{}}
        for gate in self.ctx['required_gates']:
            self.add_gate(gate)

    def artifact(self, name, data=b'synthetic evidence, not an actual visual pass'):
        (self.root/name).write_bytes(data)
        return {'path':name, 'sha256':hashlib.sha256(data).hexdigest()}

    def pin_context(self):
        self.ctx_path.write_text(json.dumps(self.ctx), encoding='utf-8')
        self.pin = hashlib.sha256(self.ctx_path.read_bytes()).hexdigest()

    def add_gate(self, name):
        evidence = {role:self.artifact(name+'-'+role+'.txt') for role in c.REQUIRED_EVIDENCE[name]}
        if name == 'visual':
            evidence['capture'] = {**self.artifact('motion.mp4'), 'kind':'video'}
        self.receipt['gates'][name] = {'status':'pass', 'actor_id':'reviewer-1',
            'run_id':self.ctx['run_id'], 'subject_sha256':self.ctx['subject_sha256'],
            'tick_interval':[0,20], 'evidence':evidence}

    def run_check(self):
        path = self.root/'receipt.json'
        path.write_text(json.dumps(self.receipt), encoding='utf-8')
        return c.check_files(path, self.ctx_path, self.pin, SCOPE, self.root)

    def test_good_structure_requests_external_review_never_completion(self):
        before = copy.deepcopy(self.receipt)
        result = self.run_check()
        self.assertTrue(result['ready_for_controller_review'])
        self.assertFalse(result['goal_complete'])
        self.assertEqual(result['next_checkpoint'], 'controller_acceptance')
        self.assertEqual(self.receipt, before)
        self.assertIn('No pixels', result['limits'])

    def test_catalog_camera_manifest_required_and_checked(self):
        from test_visual_capture import fixture
        manifest, _, profile = fixture(motion=True)
        self.ctx['verification_profile_id'] = profile['id']
        self.pin_context()
        self.receipt['context_sha256'] = self.pin
        with self.assertRaisesRegex(ValueError, 'camera_manifest_required'):
            c.check(self.receipt, self.ctx, self.pin, SCOPE, self.root, profile)
        visual = self.receipt['gates']['visual']
        visual['tick_interval'] = self.receipt['gates']['runtime']['tick_interval'] = [10,20]
        manifest.update(task_id=self.ctx['task_id'], run_id=self.ctx['run_id'],
                        subject_sha256=self.ctx['subject_sha256'],
                        capture_sha256=visual['evidence']['capture']['sha256'])
        visual['evidence']['camera_manifest'] = self.artifact('camera.json', json.dumps(manifest).encode())
        result = c.check(self.receipt, self.ctx, self.pin, SCOPE, self.root, profile)
        self.assertTrue(result['ready_for_controller_review'])
        self.assertFalse(result['goal_complete'])
        manifest['views'][0]['camera']['samples'][0]['distance_to_target'] = 50
        visual['evidence']['camera_manifest'] = self.artifact('camera.json', json.dumps(manifest).encode())
        with self.assertRaisesRegex(ValueError, 'camera_target_distance_mismatch'):
            c.check(self.receipt, self.ctx, self.pin, SCOPE, self.root, profile)

    def test_catalog_visual_kind_cannot_be_downgraded(self):
        profile = {'id':'camera-check', 'kind':'final_playthrough'}
        with self.assertRaisesRegex(ValueError, 'catalog_checkpoint_kind_mismatch'):
            c.check(self.receipt, self.ctx, self.pin, SCOPE, self.root, profile)

    def test_first_missing_gate_is_next_action(self):
        for gate in self.ctx['required_gates']:
            with self.subTest(gate=gate):
                saved = self.receipt['gates'].pop(gate)
                out = self.run_check()
                self.assertEqual(out['next_checkpoint'], gate)
                self.assertFalse(out['ready_for_controller_review'])
                self.receipt['gates'][gate] = saved

    def test_visual_pass_does_not_override_physics_failure(self):
        self.receipt['gates']['numerical']['status'] = 'fail'
        out = self.run_check()
        self.assertEqual(out['next_checkpoint'], 'numerical')
        self.assertIn('Repair', out['next_action'])
        self.assertFalse(out['goal_complete'])

    def test_inconclusive_visual_stays_open(self):
        self.receipt['gates']['visual']['status'] = 'inconclusive'
        self.assertEqual(self.run_check()['next_checkpoint'], 'visual')

    def test_changed_capture_and_missing_report_refused(self):
        (self.root/'motion.mp4').write_bytes(b'changed bytes')
        with self.assertRaisesRegex(ValueError, 'evidence_hash_mismatch'):
            self.run_check()
        self.add_gate('visual')
        (self.root/'review-review.txt').unlink()
        with self.assertRaises(OSError):
            self.run_check()

    def test_wrong_identity_generation_scope_run_refused(self):
        for key, bad in [('scope_sha256','2'*64), ('generation',4), ('subject_sha256','3'*64),
                         ('criteria_sha256','4'*64), ('run_id','another-run'), ('controller_task','wrong')]:
            with self.subTest(key=key):
                old = self.receipt[key]
                self.receipt[key] = bad
                with self.assertRaisesRegex(ValueError, 'receipt_context_mismatch'):
                    self.run_check()
                self.receipt[key] = old

    def test_changed_exe_shader_scene_policy_manifest_refused(self):
        # Any changed bytes in the pinned candidate identity invalidate the receipt.
        for field in ('exe','shader','scene','policy'):
            with self.subTest(field=field):
                (self.root/'subject.json').write_text(json.dumps({field:'new'}))
                with self.assertRaisesRegex(ValueError, 'evidence_hash_mismatch'):
                    self.run_check()

    def test_mixed_gate_run_or_candidate_refused(self):
        gate = self.receipt['gates']['visual']
        for key, value in [('run_id','other'), ('subject_sha256','5'*64)]:
            old = gate[key]
            gate[key] = value
            with self.assertRaisesRegex(ValueError, 'stale_gate_identity'):
                self.run_check()
            gate[key] = old

    def test_still_image_or_single_tick_cannot_prove_motion(self):
        visual = self.receipt['gates']['visual']
        visual['evidence']['capture']['kind'] = 'image'
        with self.assertRaisesRegex(ValueError, 'motion_requires_recording'):
            self.run_check()
        visual['evidence']['capture']['kind'] = 'video'
        visual['tick_interval'] = [1,1]
        self.receipt['gates']['runtime']['tick_interval'] = [1,1]
        with self.assertRaisesRegex(ValueError, 'motion_interval_empty'):
            self.run_check()

    def test_capture_telemetry_interval_mismatch_refused(self):
        self.receipt['gates']['visual']['tick_interval'] = [0,19]
        with self.assertRaisesRegex(ValueError, 'capture_runtime_interval_mismatch'):
            self.run_check()

    def test_self_review_or_visual_na_refused(self):
        self.receipt['gates']['review']['actor_id'] = self.ctx['worker_id']
        with self.assertRaisesRegex(ValueError, 'independent_reviewer_required'):
            self.run_check()
        self.receipt['gates']['review']['actor_id'] = 'reviewer-1'
        self.receipt['gates']['visual']['status'] = 'N/A'
        with self.assertRaisesRegex(ValueError, 'invalid_gate_status'):
            self.run_check()

    def test_context_cannot_be_changed_to_skip_visual_gate(self):
        self.ctx['required_gates'].remove('visual')
        self.ctx_path.write_text(json.dumps(self.ctx))
        with self.assertRaisesRegex(ValueError, 'context_file_changed'):
            self.run_check()
        self.pin_context()
        self.receipt['context_sha256'] = self.pin
        with self.assertRaisesRegex(ValueError, 'required_checkpoint_waived'):
            self.run_check()

    def test_context_is_parsed_from_the_exact_hashed_buffer(self):
        self.receipt['gates'].pop('visual')
        replacement = copy.deepcopy(self.ctx)
        replacement.update(kind='offline', nonvisual_reason='unauthorized concurrent rewrite')
        replacement['required_gates'].remove('visual')
        original_loader = c.load_document
        def concurrent_rewrite(path):
            if Path(path).name == 'receipt.json':
                self.ctx_path.write_text(json.dumps(replacement))
            return original_loader(path)
        with patch.object(c, 'load_document', side_effect=concurrent_rewrite):
            out = self.run_check()
        self.assertEqual(out['next_checkpoint'], 'visual')
        self.assertFalse(out['ready_for_controller_review'])

    def test_nonvisual_work_needs_predeclared_reason(self):
        self.ctx['kind'] = 'offline'
        self.ctx['required_gates'] = ['implementation','review']
        self.receipt['gates'] = {g:self.receipt['gates'][g] for g in self.ctx['required_gates']}
        self.pin_context(); self.receipt['context_sha256'] = self.pin
        with self.assertRaisesRegex(ValueError, 'nonvisual_reason'):
            self.run_check()
        self.ctx['nonvisual_reason'] = 'Pure input parser; no user-visible behavior changed'
        self.pin_context(); self.receipt['context_sha256'] = self.pin
        self.assertTrue(self.run_check()['ready_for_controller_review'])

    def test_human_claim_is_not_authentication(self):
        self.ctx.update(kind='final_playthrough', required_gates=list(c.ORDER))
        self.pin_context(); self.receipt['context_sha256'] = self.pin
        self.assertEqual(self.run_check()['next_checkpoint'], 'human')
        self.add_gate('human')
        with self.assertRaisesRegex(ValueError, 'human_source_reference_required'):
            self.run_check()
        self.receipt['gates']['human'].update(source_kind='operator_message',source_reference='synthetic-test-only')
        out = self.run_check()
        self.assertFalse(out['goal_complete'])
        self.assertIn('Authenticate', out['next_action'])

    def test_evidence_path_escape_and_read_budget_refused(self):
        record = self.receipt['gates']['visual']['evidence']['capture']
        old = record['path']
        for name in ('../outside.mp4','C:/outside.mp4','/outside.mp4','file:stream','a/../motion.mp4'):
            record['path'] = name
            with self.subTest(path=name), self.assertRaises(ValueError):
                self.run_check()
        record['path'] = old
        with self.assertRaisesRegex(ValueError, 'read_budget'):
            c.evidence_hash(self.root,record,[1])

    def test_duplicate_keys_nonfinite_unknown_status_refused(self):
        path = self.root/'bad.json'
        for raw in ('{"gates":{},"gates":{}}','{"value":NaN}','{"value":1e999}'):
            path.write_text(raw)
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                c.load_document(path)
        self.receipt['gates']['visual']['status'] = 'looks_good'
        with self.assertRaisesRegex(ValueError, 'invalid_gate_status'):
            self.run_check()


if __name__ == '__main__':
    unittest.main(verbosity=2)
