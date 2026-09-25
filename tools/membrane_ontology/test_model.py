"""Adversarial structural and source-identity checks (O1-O7); no physics claims."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from http.server import HTTPServer

from model import canonical, decode, digest, snapshot, validate
from serve import handler_for

HERE = Path(__file__).resolve().parent


class OntologyChecks(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((HERE / 'ontology.json').read_text(encoding='utf-8'))

    def by_id(self, key):
        return next(n for n in self.data['nodes'] if n['id'] == key)

    def refused(self, code):
        with self.assertRaisesRegex(ValueError, code):
            validate(self.data)

    def test_real_definition_and_connection_membership(self):
        before = canonical(self.data)
        n = validate(self.data)
        self.assertEqual(n['skeleton']['path'], ['monkey-game', 'creature', 'skeleton'])
        self.assertEqual(n['skeleton']['children'], ['bones', 'joints'])
        self.assertEqual(set(n['skeleton']['connections']), {'muscle-bone', 'skin-bone'})
        self.assertEqual(canonical(self.data), before)

    def test_duplicate_node(self):
        self.data['nodes'].append(deepcopy(self.data['nodes'][0]))
        self.refused('duplicate_node')

    def test_missing_parent(self):
        self.by_id('skin')['parent'] = 'absent'
        self.refused('missing_parent')

    def test_cycle(self):
        self.by_id('skeleton')['parent'] = 'bones'
        self.refused('containment_cycle')

    def test_multiple_roots(self):
        self.by_id('skin')['parent'] = None
        self.refused('root_count_or_identity')

    def test_missing_endpoint_node(self):
        self.by_id('drive')['endpoints'][0]['node'] = 'absent'
        self.refused('missing_endpoint_node')

    def test_missing_endpoint_port(self):
        self.by_id('drive')['endpoints'][0]['port'] = 'absent'
        self.refused('missing_endpoint_port')

    def test_duplicate_port(self):
        p = self.by_id('creature')['ports']
        p.append(deepcopy(p[0]))
        self.refused('duplicate_port')

    def test_duplicate_endpoint(self):
        e = self.by_id('drive')['endpoints']
        e[1] = deepcopy(e[0])
        self.refused('duplicate_connection_endpoint')

    def test_protocol_mismatch(self):
        self.by_id('player')['ports'][0]['protocol'] = 'different'
        self.refused('port_protocol_mismatch')

    def test_unit_mismatch(self):
        self.by_id('player')['ports'][0]['unit'] = 'cm/s,deg'
        self.refused('port_unit_mismatch')

    def test_valid_exposure(self):
        p = deepcopy(self.by_id('skeleton')['ports'][0])
        p['id'] = 'skeletal-attachment'
        p['delegates_to'] = {'node': 'skeleton', 'port': 'attachment'}
        self.by_id('creature')['ports'].append(p)
        self.assertIn('creature', validate(self.data))

    def test_exposure_outside_descendants(self):
        p = self.by_id('player')['ports'][0]
        p['delegates_to'] = {'node': 'creature', 'port': 'command'}
        self.refused('port_exposure_not_descendant')

    def test_self_exposure(self):
        self.by_id('player')['ports'][0]['delegates_to'] = {'node': 'player', 'port': 'command'}
        self.refused('port_exposure_not_descendant')

    def test_unsafe_source_paths(self):
        for path in ('../secret', '/secret', 'C:/secret', 'docs/../secret', 'docs\\secret', 'docs//secret'):
            with self.subTest(path=path):
                self.by_id('skin')['sources'] = [path]
                self.refused('unsafe_source_path')

    def test_matter_reference_does_not_duplicate_owner(self):
        self.by_id('skin')['matter_claims'] = [{'matter_id': 'skin-volume', 'role': 'owner'}]
        self.by_id('creature')['matter_claims'] = [{'matter_id': 'skin-volume', 'role': 'reference'}]
        self.assertEqual(len(validate(self.data)), len(self.data['nodes']))
        self.by_id('creature')['matter_claims'][0]['role'] = 'owner'
        self.refused('duplicate_matter_owner')

    def test_strict_json_and_fields(self):
        for raw in (b'{"schema":1,"schema":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                decode(raw)
        self.by_id('skin')['hidden_default'] = 1
        self.refused('invalid_node_fields')

    def test_snapshot_determinism_identity_and_missing_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'record.txt'
            source.write_bytes(b'actual source\r\n')
            for n in self.data['nodes']:
                n['sources'] = []
            self.by_id('skin')['sources'] = ['record.txt', 'missing.json']
            definition = root / 'ontology.json'
            definition.write_bytes(canonical(self.data))
            original = (source.read_bytes(), definition.read_bytes())
            a = snapshot(definition, root)
            b = snapshot(definition, root)
            self.assertEqual(canonical(a), canonical(b))
            self.assertEqual((source.read_bytes(), definition.read_bytes()), original)
            records = {r['path']: r for r in a['sources']}
            self.assertEqual(records['record.txt']['raw_sha256'], digest(original[0]))
            self.assertEqual(records['missing.json']['status'], 'missing')
            self.assertIsNone(records['missing.json']['raw_sha256'])
            claimed_hash = a.pop('snapshot_sha256')
            self.assertEqual(claimed_hash, digest(canonical(a)))
            source.write_bytes(b'changed')
            self.assertNotEqual(b['snapshot_sha256'], snapshot(definition, root)['snapshot_sha256'])

    def test_server_read_only_no_directory_or_source_serving(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            web = root / 'web'
            web.mkdir()
            (web / 'index.html').write_text('test page', encoding='utf-8')
            definition = root / 'ontology.json'
            definition.write_bytes(canonical(self.data))
            srv = HTTPServer(('127.0.0.1', 0), handler_for(root, definition, web))
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            base = 'http://127.0.0.1:' + str(srv.server_port)
            try:
                with urlopen(base + '/api/ontology') as r:
                    self.assertEqual(r.headers['Cache-Control'], 'no-store')
                    self.assertTrue(json.load(r)['checks']['structural_valid'])
                for req, status in ((Request(base + '/api/ontology', data=b'{}'), 405),
                                    (base + '/ontology.json', 404), (base + '/../ontology.json', 404)):
                    with self.assertRaises(HTTPError) as e:
                        urlopen(req)
                    self.assertEqual(e.exception.code, status)
                    e.exception.close()
                self.by_id('skin')['parent'] = 'missing'
                definition.write_bytes(canonical(self.data))
                with self.assertRaises(HTTPError) as e:
                    urlopen(base + '/api/ontology')
                self.assertEqual(e.exception.code, 422)
                self.assertIn('missing_parent', e.exception.read().decode())
                e.exception.close()
            finally:
                srv.shutdown()
                srv.server_close()
                thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
