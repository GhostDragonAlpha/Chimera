from copy import deepcopy
from pathlib import Path
import unittest

from ontology_plan import load_catalog, project
from execution_plan import build_plan
from integrity import content_digest

HERE = Path(__file__).resolve().parent


class OntologyPlanChecks(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(HERE / 'monkey_completion_map.json')

    def test_complete_deterministic_mapping_and_worker_projection(self):
        before = deepcopy(self.catalog)
        p = project(self.catalog)
        self.assertEqual((p['task_count'], p['selected_count'], len(p['checkpoints'])), (83, 76, 11))
        self.assertEqual(p, project(self.catalog))
        self.assertEqual(before, self.catalog)
        by = {t['id']: t for t in p['tasks']}
        for t in p['tasks']:
            for dep in t['depends_on']:
                self.assertLess(by[dep]['dependency_layer'], t['dependency_layer'])
        worker = build_plan(self.catalog)
        for t in worker['tasks']:
            self.assertEqual(t['ontology'], by[t['id']]['ontology'])
            self.assertEqual(t['verification_profile'], by[t['id']]['verification_profile'])
        self.assertFalse(any(t['selected'] for t in p['tasks'] if t['id'].startswith('B')))

    def test_browser_and_worker_share_exact_profiles_and_task_identities(self):
        import importlib.util
        path = HERE.parent / 'membrane_ontology'
        spec = importlib.util.spec_from_file_location('ontology_browser_test', path / 'model.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        snapshot = module.snapshot(path / 'ontology.json', HERE.parents[1], HERE / 'monkey_completion_map.json')
        browser = {t['id']:t for node in snapshot['nodes'] for t in node['tasks']}
        workers = {t['id']:t for t in build_plan(self.catalog)['tasks']}
        self.assertEqual(set(browser), set(workers))
        for tid in browser:
            self.assertEqual(browser[tid]['verification_profile'], workers[tid]['verification_profile'])
            self.assertEqual(browser[tid]['done_when'], workers[tid]['done_when'])

    def test_missing_mapping_unknown_connection_profile_and_checkpoint_refused(self):
        for field, bad in [('primary_membrane', 'absent'), ('connection_ids', ['creature']),
                           ('verification_profile', 'absent'), ('checkpoint_ids', ['absent'])]:
            c = deepcopy(self.catalog)
            c['tasks'][0]['ontology'][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                project(c)

    def test_camera_field_and_checkpoint_cycle_refused(self):
        c = deepcopy(self.catalog)
        c['ontology_contract']['visual_profiles'][1]['camera_required_fields'].remove('distance_to_target')
        with self.assertRaisesRegex(ValueError, 'camera_requirements_missing'):
            project(c)
        c = deepcopy(self.catalog)
        c['ontology_contract']['checkpoints'][0]['requires'] = ['V01']
        with self.assertRaisesRegex(ValueError, 'cycle'):
            project(c)

    def test_definition_drift_and_missing_reciprocal_mapping_refused(self):
        c = deepcopy(self.catalog)
        c['ontology_contract']['definition_raw_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'pin_mismatch'):
            project(c)
        c = deepcopy(self.catalog)
        c['tasks'][1]['ontology']['checkpoint_ids'] = []
        with self.assertRaisesRegex(ValueError, 'mapping_mismatch'):
            project(c)

    def test_early_port_checks_do_not_demand_later_skill(self):
        p = project(self.catalog)
        by = {t['id']: t for t in p['tasks']}
        for tid, pid in [('G02','attachment-fixture'), ('G03','tendon-pose-sweep'),
                         ('F04','contact-motion'), ('W03','parity-replay')]:
            self.assertEqual(by[tid]['verification_profile']['id'], pid)
            self.assertEqual(by[tid]['verification_profile']['kind'], 'motion')
        self.assertEqual(next(g for g in p['checkpoints'] if g['id']=='V02')['requires'], [])

    def test_amendment_reconstructs_previous_scope_without_changing_acceptance(self):
        receipt = load_catalog(HERE / 'SCOPE_AMENDMENT_ONTOLOGY_20260924.json')
        old = deepcopy(self.catalog)
        old.pop('ontology_contract')
        changes = {r['task_id']: r for r in receipt['dependency_changes']}
        for task in old['tasks']:
            task.pop('ontology')
            task.pop('dependency_reasons', None)
            if task['id'] in changes:
                task['depends_on'] = changes[task['id']]['before']
        self.assertEqual(content_digest(old), receipt['previous_scope_sha256'])
        self.assertEqual(content_digest(self.catalog), receipt['scope_sha256'])


if __name__ == '__main__':
    unittest.main()
