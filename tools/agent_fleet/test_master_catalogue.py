"""Master-catalogue import tests. Isolated temp registries ONLY - this suite
never touches the live registry (E:/ChimeraWork/control/state.sqlite)."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from control import Control, Refusal
from master_catalogue import (SCHEMA, build_records, parse_master_rows,
                              payload_digest, validate_payload)

BASE = 'a' * 40
HEAD = 'b' * 40
MERGED = 'c' * 40


def _sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def card_record(cid, deps=(), status='PROPOSED', domain='GOV'):
    raw = {'id': cid, 'domain': domain, 'status': status, 'title': 't-' + cid,
           'statement': 's', 'prediction': 'p', 'falsifier': 'f',
           'depends_on': list(deps)}
    return {'plane': 'card', 'id': cid, 'domain': domain, 'title': raw['title'],
            'status': status, 'depends_on': list(deps),
            'source': {'path': 'fixture', 'index': 0},
            'content_sha256': _sha(json.dumps(raw, sort_keys=True,
                                              ensure_ascii=False)),
            'card': raw}


def row_record(rid, text, section='THE BACKLOG', line=1):
    cols = [c.strip() for c in text.strip().strip('|').split('|')]
    return {'plane': 'master_row', 'id': rid,
            'observations': [{'section': section, 'line': line, 'columns': cols,
                              'content_sha256': _sha(json.dumps(
                                  cols, ensure_ascii=False))}]}


def payload(cards=(), rows=()):
    return {'schema': SCHEMA, 'cards': list(cards), 'master_rows': list(rows),
            'coverage': {'cards': len(cards), 'domains': 1,
                         'master_row_ids': len({r['id'] for r in rows}),
                         'master_row_observations': sum(
                             len(r['observations']) for r in rows),
                         'unresolved': [],
                         'pipe_rows_outside_scoped_sections': 0}}


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = Control(self.root / 'state.sqlite', 'super-secret',
                         'enroll-secret', self.root / 'slots')
        self.tokens = {}
        for aid in ('lead', 'standby', 'worker', 'other'):
            self.tokens[aid] = self.c.call('enroll', 'enroll-secret', agent=aid,
                label=aid)['result']['session_token']
            self.c.call('qualify', 'super-secret', agent=aid,
                capabilities=['cpu', 'docs'], max_tasks=5,
                can_lead=aid in ('lead', 'standby'),
                rank=10 if aid == 'lead' else 1, evidence='fixture qualification')
        self.c.call('offer_lead', self.tokens['lead'], epoch=0,
                    checkpoint='ready; no foreign work')
        self.c.call('elect', 'super-secret')

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, op, actor='lead', **p):
        return self.c.call(op, self.tokens.get(actor, actor), **p)['result']

    def snap(self):
        return self.call('snapshot')

    def epoch(self):
        return self.snap()['epoch']

    def imp(self, payload_body, digest=None, actor='lead', epoch=None):
        return self.call('catalogue_import', actor,
                         payload=payload_body, digest=digest,
                         epoch=self.epoch() if epoch is None else epoch,
                         evidence='fixture import evidence')

    def task(self, tid, **kw):
        p = dict(task=tid, epoch=self.epoch(), base=BASE,
                 scopes=['tools/labs/' + tid],
                 packet='statement / prediction / falsifier', kind='worker')
        p.update(kw)
        return self.call('create_task', **p)

    # --- prediction (a): full real-source coverage ------------------------
    def test_import_real_sources_full_coverage(self):
        built = build_records()
        self.assertEqual(built['coverage']['cards'], 240)
        self.assertEqual(built['coverage']['domains'], 40)
        self.assertEqual(built['coverage']['master_row_ids'], 41)
        self.assertEqual(built['coverage']['master_row_observations'], 41)
        self.assertFalse(built['coverage']['unresolved'],
                         'silent omission forbidden: unresolved must be empty')
        self.assertFalse(validate_payload(built))
        r = self.imp(built)
        self.assertEqual(r['coverage']['cards'], 240)
        d = r['digest']
        by_id = {c['id']: c for c in built['cards']}
        for cid, rec in by_id.items():
            got = self.call('catalogue_read', digest=d, plane='card', id=cid)
            self.assertEqual(got['record']['content_sha256'],
                             rec['content_sha256'], cid)
        l1 = self.call('catalogue_read', digest=d, plane='master_row', id='L1')
        self.assertTrue(l1['record']['observations'][0]['columns'][1]
                        .startswith('**The corpus**'))
        b2 = self.call('catalogue_read', digest=d, plane='master_row', id='B2')
        self.assertEqual(len(b2['record']['observations']), 1)
        self.assertTrue(b2['record']['observations'][0]['columns'][1]
                        .startswith('**ROM re-sweep'))

    # --- prediction (b): identical re-import is a no-op -------------------
    def test_reimport_identical_refused_and_state_unchanged(self):
        built = build_records()
        first = self.imp(built)
        after_first = json.dumps(self.snap(), sort_keys=True)
        events = self.call('events', since=0)['events']
        self.assertEqual(sum(e['kind'] == 'catalogue_import'
                             for e in events), 1)
        with self.assertRaisesRegex(Refusal, 'duplicate_catalogue_import'):
            self.imp(built, digest=first['digest'])
        self.assertEqual(after_first, json.dumps(self.snap(), sort_keys=True))
        events = self.call('events', since=0)['events']
        self.assertEqual(events[-1]['kind'], 'catalogue_import')
        self.assertEqual(sum(e['kind'] == 'catalogue_import'
                             for e in events), 1)

    # --- prediction (c): replace preserves live state, survives restart ---
    def test_reimport_after_change_preserves_live_state_and_restart(self):
        self.imp(payload(cards=[card_record('MATH-01')],
                         rows=[row_record('B1', 'B1 | skin | main | OPEN')]))
        self.task('w')
        t = self.call('claim', 'worker', task='w')
        self.call('resource_acquire', 'worker', task='w',
                  generation=t['generation'], resource='rtx4090')
        s1 = self.snap()
        v2 = payload(cards=[card_record('MATH-01'), card_record('MATH-02')],
                     rows=[row_record('B1', 'B1 | skin | main | UPDATED')])
        second = self.imp(v2, digest=self.snap()['catalogue']['import']['digest'])
        s2 = self.snap()
        self.assertNotEqual(second['digest'],
                            s2['catalogue']['imports'][0]['digest'])
        for key in ('tasks', 'resources', 'slots', 'agents'):
            self.assertEqual(s1[key], s2[key],
                             'live plane must be byte-identical across import')
        self.assertEqual(s2['catalogue']['import']['digest'], second['digest'])
        got = self.call('catalogue_read', digest=second['digest'],
                        plane='card', id='MATH-02')
        self.assertEqual(got['record']['id'], 'MATH-02')
        with self.assertRaisesRegex(Refusal, 'unknown_catalogue_id'):
            self.call('catalogue_read', digest=second['digest'],
                      plane='master_row', id='L1')
        c2 = Control(self.root / 'state.sqlite', 'super-secret',
                     'enroll-secret', self.root / 'slots')
        self.assertEqual(json.dumps(s2, sort_keys=True),
                         json.dumps(c2.call('snapshot',
                                            self.tokens['lead'])['result'],
                                    sort_keys=True))

    def test_stale_import_refused(self):
        first = self.imp(payload(cards=[card_record('MATH-01')]))
        with self.assertRaisesRegex(Refusal, 'stale_catalogue_import'):
            self.imp(payload(cards=[card_record('MATH-02')]))
        self.imp(payload(cards=[card_record('MATH-01'),
                                card_record('MATH-02')]),
                 digest=first['digest'])

    # --- prediction (d): negative controls, zero state mutation ----------
    def test_worker_and_stale_epoch_import_refused(self):
        built = payload(cards=[card_record('MATH-01')])
        with self.assertRaisesRegex(Refusal, 'stale_or_nonleader'):
            self.imp(built, actor='worker')
        with self.assertRaisesRegex(Refusal, 'stale_or_nonleader'):
            self.imp(built, epoch=self.epoch() + 1)
        self.assertIsNone(self.snap()['catalogue']['import'])

    def test_duplicate_cycle_malformed_empty_refused_without_mutation(self):
        before = json.dumps(self.snap(), sort_keys=True)
        dups = payload(cards=[card_record('MATH-01'), card_record('MATH-01')])
        with self.assertRaisesRegex(Refusal, 'duplicate_catalogue_id'):
            self.imp(dups)
        cyc = payload(cards=[card_record('MATH-01', deps=('MATH-02',)),
                             card_record('MATH-02', deps=('MATH-01',))])
        with self.assertRaisesRegex(Refusal, 'catalogue_dependency_cycle'):
            self.imp(cyc)
        unknown = payload(cards=[card_record('MATH-01', deps=('GHOST',))])
        with self.assertRaisesRegex(Refusal, 'catalogue_unknown_dependency'):
            self.imp(unknown)
        with self.assertRaisesRegex(Refusal, 'invalid_catalogue_payload'):
            self.imp('not even json')
        bad_row = payload(rows=[{'plane': 'master_row', 'id': 'B1',
                                 'observations': []}])
        with self.assertRaisesRegex(Refusal, 'malformed_master_row'):
            self.imp(bad_row)
        with self.assertRaisesRegex(Refusal, 'empty_catalogue_payload'):
            self.imp(payload())
        self.assertEqual(before, json.dumps(self.snap(), sort_keys=True))

    # --- prediction (e): snapshot carries summary only --------------------
    def test_snapshot_summary_only(self):
        built = build_records()
        r = self.imp(built)
        s = self.snap()
        self.assertEqual(s['catalogue']['import']['digest'], r['digest'])
        self.assertNotIn('payload', s['catalogue'])
        body = json.dumps(s)
        self.assertNotIn('"statement"', body)
        self.assertNotIn('THE corpus', body)
        got = self.call('catalogue_read', digest=r['digest'], plane='card',
                        id=by_id_first(built))
        self.assertIn('card', got['record'])

    # --- prediction (f): planning-only next candidates --------------------
    def test_next_candidates_planning_only_never_creates_tasks(self):
        self.imp(payload(cards=[
            card_record('MATH-01'), card_record('MATH-02', deps=('MATH-01',)),
            card_record('MATH-03', deps=('MATH-02',)),
            card_record('OLD', status='ACCEPTED')]))
        self.task('math-01')
        t = self.call('claim', 'lead', task='math-01')
        self.call('submit_review', 'lead', task='math-01',
                  generation=t['generation'], branch=t['branch'], head=HEAD,
                  evidence='fixture evidence')
        self.call('integration_request', task='math-01', head=HEAD,
                  branch=t['branch'], expected_base=BASE,
                  epoch=self.epoch(), review='fixture independent review')
        reqs = self.snap()['requests']
        rid = [k for k, v in reqs.items() if v['task'] == 'math-01'][0]
        self.call('ack_integration', 'super-secret', request=rid,
                  base_branch='astra/gait-capture', expected_base=BASE,
                  commit=MERGED, evidence='fixture publisher evidence')
        d = self.snap()['catalogue']['import']['digest']
        r = self.call('catalogue_next', digest=d)
        self.assertIn('PLANNING CANDIDATES ONLY', r['note'])
        self.assertIn('MATH-02', r['candidates'])
        self.assertNotIn('MATH-03', r['candidates'])
        self.assertNotIn('MATH-01', r['candidates'],
                         'a card realized as a live task must not be re-proposed')
        self.assertNotIn('OLD', r['candidates'])
        s = self.snap()
        self.assertNotIn('MATH-02', s['tasks'],
                         'next must never create live tasks')
        self.assertEqual(s['tasks']['math-01']['state'], 'INTEGRATED')
        with self.assertRaisesRegex(Refusal, 'unknown_catalogue_digest'):
            self.call('catalogue_next', digest='deadbeef')

    # --- catalogue plane is not the live plane ----------------------------
    def test_import_creates_no_live_tasks_or_claims(self):
        built = build_records()
        self.imp(built)
        s = self.snap()
        self.assertEqual(s['tasks'], {})
        self.assertEqual(s['resources'], {})

    # --- parser unit behaviors ---------------------------------------------
    def test_parser_reports_unresolved_and_outside_counts(self):
        text = ('## x\n\n'
                '### THE BACKLOG (maintained)\n\n'
                '| B1 | skin | main | OPEN |\n'
                '| --- | --- | --- | --- |\n'
                '| # | Item | Owner | State |\n'
                '| owner note | not a task |\n\n'
                '### OTHER SECTION\n\n'
                '| status only row |\n')
        rows, extra = parse_master_rows(text)
        self.assertEqual(list(rows), ['B1'])
        self.assertEqual(len(extra['unresolved']), 1)
        self.assertEqual(extra['outside'], 1)
        self.assertEqual(rows['B1']['observations'][0]['columns'],
                         ['B1', 'skin', 'main', 'OPEN'])

    def test_validate_rejects_wrong_schema_and_missing_coverage(self):
        self.assertEqual(validate_payload({'schema': 'nope'}),
                         ['invalid_catalogue_payload'])
        p = payload(cards=[card_record('MATH-01')])
        p.pop('coverage')
        self.assertEqual(validate_payload(p), ['missing_catalogue_coverage'])


def by_id_first(built):
    return sorted(c['id'] for c in built['cards'])[0]


if __name__ == '__main__':
    unittest.main(verbosity=2)
