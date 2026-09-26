import json
from pathlib import Path
import tempfile
import unittest
from integrity import ALGORITHM,content_digest,strict_load,verify_catalog


class IntegrityTests(unittest.TestCase):
    def test_semantic_json_formatting(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'map.json';lock=Path(d)/'lock.json'
            data={'tasks':[{'id':'W01','depends_on':['P01'],'goal':'walk'}]}
            digest=content_digest(data)
            p.write_text(json.dumps(data,indent=2),encoding='utf-8')
            lock.write_text(json.dumps({'algorithm':ALGORITHM,'scope_sha256':digest}),encoding='utf-8')
            self.assertTrue(verify_catalog(p,lock,digest,True)[1]['external_digest_checked'])
            p.write_bytes(json.dumps(data,indent=4).replace('\n','\r\n').encode())
            self.assertEqual(verify_catalog(p,lock,digest,True)[0],data)
            data['tasks'][0]['goal']='claim walking without proof'
            p.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'APPROVED_LIST_CHANGED'):verify_catalog(p,lock,digest,True)
            lock.write_text(json.dumps({'algorithm':ALGORITHM,'scope_sha256':content_digest(data)}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'TRUST_ANCHOR_MISMATCH'):verify_catalog(p,lock,digest,True)

    def test_no_colocated_lock_authentication(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'map.json';lock=Path(d)/'lock.json';p.write_text('{}')
            lock.write_text(json.dumps({'algorithm':ALGORITHM,'scope_sha256':content_digest({})}))
            with self.assertRaisesRegex(ValueError,'TRUST_ANCHOR_REQUIRED'):verify_catalog(p,lock,require_anchor=True)
            self.assertFalse(verify_catalog(p,lock)[1]['external_digest_checked'])

    def test_duplicate_keys_and_nonfinite_numbers_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.json'
            for text in ['{"scope":1,"scope":2}','{"value":NaN}','{"value":Infinity}']:
                p.write_text(text)
                with self.subTest(text=text),self.assertRaises(ValueError):strict_load(p)

    def test_dependency_and_scope_changes_change_digest(self):
        baseline={'scope':'core','depends_on':['W01']}
        self.assertNotEqual(content_digest(baseline),content_digest({'scope':'later','depends_on':['W01']}))
        self.assertNotEqual(content_digest(baseline),content_digest({'scope':'core','depends_on':[]}))


if __name__=='__main__':unittest.main(verbosity=2)
