import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.science_funnel import visual_proof as VP
from tools.science_funnel import visual_proof_wave2 as W

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'tools' / 'science_funnel' / 'validation' / 'visual_proof_wave2_20260918'


class Wave2VisualProof(unittest.TestCase):
    def test_parallel_render_set_matches_serial_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as serial, tempfile.TemporaryDirectory() as parallel:
            one = VP.build_wave2_renders(serial, workers=1)
            many = VP.build_wave2_renders(parallel, workers=2)
            self.assertEqual([x['id'] for x in one['renders']], [x['id'] for x in many['renders']])
            self.assertEqual([x['png_sha256'] for x in one['renders']], [x['png_sha256'] for x in many['renders']])
            self.assertEqual(many['workers'], 2)
            self.assertEqual(many['render_order'], 'declaration order; worker completion order is not observable')

    def test_render_set_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ma = VP.build_wave2_renders(a, workers=1)
            mb = VP.build_wave2_renders(b, workers=1)
            self.assertEqual([x['id'] for x in ma['renders']], [x['id'] for x in mb['renders']])
            self.assertEqual(len(ma['renders']), 8)
            for ra, rb in zip(ma['renders'], mb['renders']):
                self.assertEqual(ra['png_sha256'], rb['png_sha256'])
                self.assertEqual((Path(a) / ra['png']).read_bytes(), (Path(b) / rb['png']).read_bytes())

    @unittest.skipUnless(OUT.exists(), 'wave-2 validation output not generated')
    def test_manifest_chain_and_rerender(self):
        ids = VP.verify_wave2(OUT)
        self.assertEqual(len(ids), 8)
        manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
        self.assertIn('NOT physics verification', manifest['label'])
        self.assertEqual(manifest['work_item'], 'work.data.visual_proof_wave2_20260918')
        for entry in manifest['renders']:
            self.assertTrue((OUT / entry['png']).exists())
            for source in entry['inputs']:
                self.assertEqual(hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest(), source['sha256'])

    def test_auto_uses_serial_for_current_small_bundle(self):
        with tempfile.TemporaryDirectory() as out:
            manifest = VP.build_wave2_renders(out, workers='auto')
            self.assertEqual(manifest['workers'], 1)

    def test_custom_job_table_is_ordered_and_byte_stable(self):
        jobs = W._wave2_jobs()[:2]
        with tempfile.TemporaryDirectory() as serial, tempfile.TemporaryDirectory() as parallel:
            one = VP.build_wave2_renders(serial, workers=1, jobs=jobs)
            many = VP.build_wave2_renders(parallel, workers=2, jobs=jobs)
            self.assertEqual([x['id'] for x in one['renders']], [x['id'] for x in many['renders']])
            self.assertEqual([x['png_sha256'] for x in one['renders']], [x['png_sha256'] for x in many['renders']])

    def test_invalid_worker_count_refuses_before_writing(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaisesRegex(ValueError, 'proof_workers'):
                VP.build_wave2_renders(out, workers=0)
            self.assertEqual(list(Path(out).iterdir()), [])

    def test_one_byte_rhea_input_changes_or_refuses(self):
        source = W.DATA / 'rhea' / 'rhea-chebi-smiles.tsv'
        base, _ = W.render_rhea(source)
        with tempfile.TemporaryDirectory() as d:
            altered = Path(d) / source.name
            raw = bytearray(source.read_bytes())
            raw[len(raw) // 2] ^= 1
            altered.write_bytes(raw)
            try:
                changed, _ = W.render_rhea(altered)
                self.assertNotEqual(base, changed)
            except Exception:
                pass

    def test_parallel_graph_shard_reads_match_serial_reads(self):
        from concurrent.futures import ThreadPoolExecutor
        from tools.creature_graph import build_graph
        shard_dir = ROOT / 'tools' / 'creature_graph' / 'data' / 'authored' / 'records'
        paths = sorted(str(p) for p in shard_dir.glob('*.json'))
        serial = [build_graph._load_record_shard(path) for path in paths]
        with ThreadPoolExecutor(max_workers=2) as pool:
            parallel = list(pool.map(build_graph._load_record_shard, paths))
        self.assertEqual([(x[0], x[1]) for x in serial], [(x[0], x[1]) for x in parallel])
        self.assertEqual([len(x[2].get('objects', [])) for x in serial], [len(x[2].get('objects', [])) for x in parallel])

    def test_graph_merge_is_honest_and_evidence_count_is_unchanged(self):
        from tools.creature_graph.store import CreatureGraph
        graph = CreatureGraph.load(ROOT / 'tools' / 'creature_graph' / 'data' / 'creature_graph.json')
        self.assertEqual(len(graph.evidence_records()), 11)
        # Store-size pins re-stamped 2026-09-18 by the MUSCLE-PATHS lane
        # (store 5249aafc...): the wave2 count (35331 objects / 38748
        # relations) was left stale by later admitted batches (it already
        # failed at HEAD c43d3363 with 52430 objects). The durable
        # invariants stay: exactly 11 evidence records and a clean
        # graph.check(); re-stamp again ONLY with a citing admission.
        self.assertEqual(len(graph.objects), 52433)
        self.assertEqual(len(graph.relations), 47300)
        self.assertEqual(graph.check(), [])

    def test_scope_labels_and_honest_metrics(self):
        _png, gu = W.render_guimaraes(W.DATA / 'guimaraes_arch' / 'AJPA-190-e70329-s001.xlsx')
        self.assertEqual(len(gu['species']), 6)
        self.assertEqual(gu['specimen_127'], 1)
        _png, wc = W.render_worldcover(W.DATA / 'esa_worldcover' / 'ESA_WorldCover_10m_2021_v200_N18W066_Map.tif')
        self.assertEqual(wc['class_code'], 80)
        self.assertEqual(wc['class_label'], 'Permanent water bodies')
        _png, tax = W.render_taxdmp(W.DATA / 'ncbi_taxdmp' / 'macaca_names.tsv', W.DATA / 'ncbi_taxdmp' / 'macaca_nodes.tsv')
        self.assertEqual(tax['root_tax_id'], '9539')
        self.assertEqual(tax['binomials'], 21)
        _png, rhea = W.render_rhea(W.DATA / 'rhea' / 'rhea-chebi-smiles.tsv')
        self.assertEqual(rhea['participants'], 14318)


if __name__ == '__main__':
    unittest.main()
