import tempfile
import unittest
from pathlib import Path
from delivery import priority, report
from evidence_pack import collect


class Delivery(unittest.TestCase):
    def test_flat_ground_precedes_later_product(self):
        self.assertEqual(priority({'planning_ids': ['W03']}), 0)
        self.assertGreater(priority({'planning_ids': ['X05']}), 0)

    def test_component_merge_never_implies_runtime_integration(self):
        r = report({'cards': {'x': dict(id='x', spec={}, state='DONE',
                                       winner={'pr_url': 'fixture'}, worker_reviews=[])}})
        self.assertTrue(r['tasks'][0]['candidate_merged'])
        self.assertEqual(r['tasks'][0]['integration'], 'NOT_ESTABLISHED_BY_CARD_MERGE')
        self.assertIsNone(r['metrics']['agent_hours_per_integrated_feature'])

    def test_hash_pack_exact_bytes_and_no_alias_or_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p/'x').write_bytes(b'abc')
            self.assertEqual(collect(p, ['x'])[0]['sha256'],
                             'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
            with self.assertRaises(ValueError): collect(p, ['x', './x'])
            with self.assertRaises(ValueError): collect(p, ['../missing'])


if __name__ == '__main__': unittest.main()
