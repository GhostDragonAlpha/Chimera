"""Analytic coupon: hand-calculated destinations, not mapper-generated oracle."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from mapping_contract import canonical, check, digest


def coupon(root):
    def save(name, value):
        raw = canonical(value)
        (root / name).write_bytes(raw)
        return {'path': name, 'raw_sha256': digest(raw)}

    def node(key, parent, unit=None):
        return dict(id=key, name=key, parent=parent, kind='fixture', description='synthetic coupon',
                    boundary={'description': 'fixture only'}, physics={'status': 'unqualified'},
                    validation=dict(status='unqualified', statement='coupon', prediction='known point mapping', falsifier='wrong coordinates'),
                    ports=[] if unit is None else [dict(id='position', protocol='point-position-v1', unit=unit, description='point samples')],
                    sources=[], gaps=[])

    ontology = dict(schema='chimera.membrane_ontology.v1', revision=1, root='coupon', authority='test fixture',
                    nodes=[node('coupon', None), node('source', 'coupon', 'mm'), node('destination', 'coupon', 'm')])
    # Independent oracle: +90 degrees around Z, then add (1,2,3) metres.
    # Origin -> (1,2,3), +X metre -> (1,3,3), +Y metre -> (0,2,3),
    # +Z metre -> (1,2,4). Explicit literals avoid deriving both sides with code under test.
    src = [[0, 0, 0], [1000, 0, 0], [0, 1000, 0], [0, 0, 1000]]
    dst = [[1, 2, 3], [1, 3, 3], [0, 2, 3], [1, 2, 4]]
    def binding(key, unit, values):
        artifact = dict(schema='chimera.point_samples.v1', representation=key+'-fixture-v1',
                        frame=key+'-frame', unit=unit,
                        points=[dict(id=str(i), position=p) for i, p in enumerate(values)])
        return dict(node=key, port='position', representation=artifact['representation'], frame=artifact['frame'],
                    artifact=save(key+'.json', artifact))
    return dict(schema='chimera.point_mapping.v1', ontology=save('ontology.json', ontology),
                source=binding('source', 'mm', src), destination=binding('destination', 'm', dst),
                mapping=dict(kind='rigid_points_with_unit_conversion', rotation=[[0,-1,0],[1,0,0],[0,0,1]],
                             translation_destination_unit=[1,2,3], scale=0.001),
                validity=dict(source_min=[0,0,0], source_max=[1000,1000,1000], max_abs_error_destination_unit=1e-12),
                properties=dict(position='recomputed', unresolved=[]),
                oracle_basis='Four hand-calculated noncoplanar points; synthetic numerical coupon, no anatomy claim.')


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.contract = coupon(self.root)

    def run_check(self):
        raw = canonical(self.contract)
        path = self.root/'mapping.json'
        path.write_bytes(raw)
        return check(path, digest(raw))

    def change_artifact(self, side, mutate):
        ref = self.contract[side]['artifact']
        path = self.root/ref['path']
        doc = json.loads(path.read_bytes())
        mutate(doc)
        path.write_bytes(canonical(doc))
        ref['raw_sha256'] = digest(path.read_bytes())

    def test_analytic_coupon_and_no_readiness(self):
        receipt = self.run_check()
        self.assertEqual(receipt['status'], 'PASS')
        self.assertEqual(receipt['max_abs_error'], 0)
        self.assertFalse(receipt['mechanical_qualification_claimed'])
        self.assertFalse(receipt['runtime_readiness_claimed'])

    def test_deterministic_readonly_relocation(self):
        first = self.run_check()
        before = {p.name:p.read_bytes() for p in self.root.iterdir()}
        self.assertEqual(self.run_check(), first)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()}, before)
        with tempfile.TemporaryDirectory() as elsewhere:
            shutil.copytree(self.root, Path(elsewhere)/'copy')
            self.assertEqual(check(Path(elsewhere)/'copy/mapping.json', first['contract_raw_sha256']), first)

    def test_external_pin_protects_tolerance(self):
        old = self.run_check()['contract_raw_sha256']
        self.contract['validity']['max_abs_error_destination_unit'] = 100
        (self.root/'mapping.json').write_bytes(canonical(self.contract))
        with self.assertRaisesRegex(ValueError, 'contract_pin_mismatch'):
            check(self.root/'mapping.json', old)

    def test_artifact_drift(self):
        (self.root/'source.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'artifact_hash_mismatch'):
            self.run_check()

    def test_wrong_frame_representation_unit(self):
        for key, error in [('frame','frame_mismatch'),('representation','representation_mismatch'),('unit','point_unit_mismatch')]:
            with self.subTest(key=key):
                self.contract = coupon(self.root)
                self.change_artifact('destination', lambda d:d.update({key:'wrong'}))
                with self.assertRaisesRegex(ValueError, error): self.run_check()

    def test_wrong_scale(self):
        self.contract['mapping']['scale'] = 1
        with self.assertRaisesRegex(ValueError, 'unit_scale_mismatch'): self.run_check()

    def test_lossy_integer_refused_before_domain_check(self):
        # This rounds to 2**53 under float(), hiding a one-unit envelope breach.
        self.change_artifact('source', lambda d:d['points'][0].update(position=[2**53+1,0,0]))
        self.contract['validity']['source_max'] = [2**53,1000,1000]
        with self.assertRaisesRegex(ValueError, 'lossy_integer'):
            self.run_check()

    def test_wrong_rotation_or_translation_fails_numerically(self):
        for value in ('rotation','translation_destination_unit'):
            with self.subTest(value=value):
                self.contract = coupon(self.root)
                self.contract['mapping'][value] = [[0,1,0],[-1,0,0],[0,0,1]] if value=='rotation' else [0,0,0]
                self.assertEqual(self.run_check()['status'], 'FAIL')

    def test_improper_or_nonorthogonal_rotation(self):
        for matrix, error in [([[1,0,0],[0,1,0],[0,0,-1]],'rotation_not_proper'), ([[2,0,0],[0,1,0],[0,0,1]],'rotation_not_orthonormal')]:
            self.contract['mapping']['rotation'] = matrix
            with self.assertRaisesRegex(ValueError, error): self.run_check()

    def test_missing_endpoint(self):
        self.contract['destination']['port'] = 'absent'
        with self.assertRaisesRegex(ValueError, 'missing_endpoint_port'): self.run_check()

    def test_missing_or_duplicate_point(self):
        for duplicate in (False,True):
            self.contract = coupon(self.root)
            self.change_artifact('destination', lambda d:d['points'].append(copy.deepcopy(d['points'][0])) if duplicate else d['points'].pop())
            with self.assertRaisesRegex(ValueError, 'duplicate_point_id' if duplicate else 'point_correspondence_mismatch'): self.run_check()

    def test_outside_domain(self):
        self.contract['validity']['source_max'] = [900,1000,1000]
        with self.assertRaisesRegex(ValueError, 'outside_validity_envelope'): self.run_check()

    def test_unresolved_is_not_pass(self):
        self.contract['properties']['unresolved'] = ['frame landmark correspondence']
        self.assertEqual(self.run_check()['status'], 'UNQUALIFIED')

    def test_unsupported_quantity(self):
        self.contract['properties']['mass'] = 'preserved'
        with self.assertRaisesRegex(ValueError, 'invalid_fields:properties'): self.run_check()

    def test_no_escape(self):
        self.contract['source']['artifact']['path'] = '../source.json'
        with self.assertRaisesRegex(ValueError, 'unsafe_source_path'): self.run_check()

    def test_cli_and_duplicate_json(self):
        pin = self.run_check()['contract_raw_sha256']
        cli = [sys.executable,'-B',str(Path(__file__).with_name('mapping_contract.py')),str(self.root/'mapping.json'),'--expected-contract-sha256',pin]
        run = subprocess.run(cli, capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['status'],'PASS')
        raw = b'{"schema":1,"schema":2}'
        (self.root/'mapping.json').write_bytes(raw)
        cli[-1] = digest(raw)
        run = subprocess.run(cli,capture_output=True)
        self.assertEqual(run.returncode,2)
        self.assertIn('duplicate_json_key',json.loads(run.stdout)['reason'])


if __name__ == '__main__':
    unittest.main()
