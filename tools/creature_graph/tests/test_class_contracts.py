"""Class-contract store and object-reference validation tests."""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from schema import validate_class_contracts, validate_object  # noqa: E402

CONTRACTS_PATH = os.path.join(os.path.dirname(HERE), 'data', 'authored',
                              'class_contracts.json')


class ClassContractStore(unittest.TestCase):
    def load(self):
        with open(CONTRACTS_PATH, encoding='utf-8') as stream:
            return json.load(stream)

    def test_authored_store_validates(self):
        registry = validate_class_contracts(self.load())
        self.assertTrue(len(registry) >= 4)
        for cid, contract in registry.items():
            self.assertTrue(contract['falsifier'].strip(), cid)
            self.assertTrue(contract['checks'], cid)

    def test_missing_falsifier_refuses(self):
        payload = self.load()
        payload['contracts'] = [dict(payload['contracts'][0], falsifier='  ')]
        with self.assertRaises(SystemExit):
            validate_class_contracts(payload)

    def test_unknown_apply_kind_refuses(self):
        payload = self.load()
        contract = dict(payload['contracts'][0])
        contract['applies_to'] = {'kinds': ['not_a_kind']}
        payload['contracts'] = [contract]
        with self.assertRaises(SystemExit):
            validate_class_contracts(payload)

    def test_object_class_contract_shape(self):
        good = {'id': 'x', 'kind': 'reference_entity', 'name': 'x', 'status': 'extracted',
                'provenance': {'source_id': 's'},
                'class_contract': {'class_id': 'batch.entity.external', 'version': 1}}
        self.assertEqual(validate_object(good), [])
        bad_version = copy.deepcopy(good)
        bad_version['class_contract'] = {'class_id': 'batch.entity.external', 'version': 'one'}
        self.assertTrue(validate_object(bad_version))
        missing_id = copy.deepcopy(good)
        missing_id['class_contract'] = {'version': 1}
        self.assertTrue(validate_object(missing_id))


if __name__ == '__main__':
    unittest.main()
