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
CURRENT_MASTER_FIXTURE = HERE / 'fixtures' / 'MASTER_CURRENT_EXCERPT_20260910.md'


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


def row_record(rid, text, section='THE BACKLOG', line=1,
               kind='table_row'):
    if kind == 'prose_mention':
        obs = {'kind': kind, 'section': section, 'line': line, 'text': text,
               'content_sha256': _sha(text)}
    else:
        cols = [c.strip() for c in text.strip().strip('|').split('|')]
        obs = {'kind': kind, 'section': section, 'line': line, 'columns': cols,
               'content_sha256': _sha(json.dumps(cols, ensure_ascii=False))}
    return {'plane': 'master_row', 'id': rid, 'observations': [obs]}


def payload(cards=(), rows=()):
    return {'schema': SCHEMA, 'cards': list(cards), 'master_rows': list(rows),
            'coverage': {'cards': len(cards), 'domains': 1,
                         'master_row_ids': len({r['id'] for r in rows}),
                         'master_row_observations': sum(
                             len(r['observations']) for r in rows),
                         'unresolved': [],
                         'structural_rows': 0,
                         'prose_mentions': [],
                         'campaign_prose_refs': []}}


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
        # gen-2 correction: the parser classifies EVERY pipe row in EVERY
        # section; the discovered-requirements table (backticked kebab-case
        # IDs) is captured, not counted into an opaque bucket.
        self.assertEqual(built['coverage']['master_row_ids'], 56)
        self.assertEqual(built['coverage']['master_row_observations'], 58)
        ids = {r['id'] for r in built['master_rows']}
        for required in ('demo-studio-state-01', 'math-contract-audit-01',
                         'fleet-slot-binding-01', 'studio-grid-depth-01',
                         'fleet-controller-upgrade-01', 'gov01-evidence-reconcile-01',
                         'L1', 'B1', 'H1'):
            self.assertIn(required, ids)
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
        new_row = self.call('catalogue_read', digest=d, plane='master_row',
                            id='demo-studio-state-01')
        obs = new_row['record']['observations'][0]
        self.assertEqual(obs['kind'], 'table_row')
        self.assertIn('no mesh loaded', ' '.join(obs['columns']))

    def test_unresolved_rows_carry_identifiable_provenance(self):
        # The only unresolved pipe rows in the canonical document are the
        # non-task actor-roster rows; each is REPORTED with section/line
        # provenance (identifiable classification), never silently dropped,
        # and none of them carries a task ID in its first cell.
        built = build_records()
        unresolved = built['coverage']['unresolved']
        self.assertTrue(unresolved, 'actor-roster rows must be reported')
        from master_catalogue import _cell_id
        for u in unresolved:
            self.assertIn('section', u)
            self.assertIn('line', u)
            self.assertIn('row', u)
            first_cell = u['row'].strip('|').split('|')[0].strip()
            self.assertIsNone(_cell_id(first_cell),
                              'a row with a recognizable task ID must never '
                              'land in unresolved: ' + u['row'][:80])

    def test_current_master_fixture_control(self):
        # Verbatim excerpt of the CURRENT canonical Master (the exact row
        # shapes the lead reviewed): discovered-requirements table with
        # backticked kebab IDs + em-dash qualifiers, legacy L-rows, and the
        # actor roster with campaign labels.
        rows, extra = parse_master_rows(
            CURRENT_MASTER_FIXTURE.read_text(encoding='utf-8'))
        for ident in ('engine-demo-01', 'demo-launcher-01', 'demo-evidence-01',
                      'demo-studio-state-01', 'gov01-evidence-reconcile-01',
                      'math-contract-audit-01', 'fleet-slot-binding-01',
                      'studio-grid-depth-01', 'fleet-controller-upgrade-01',
                      'L1'):
            self.assertIn(ident, rows, 'silent omission of ' + ident)
        self.assertEqual(rows['demo-studio-state-01']['observations'][0]['kind'],
                         'table_row')
        # Campaign labels in assignment-style actor rows are kept as
        # cell_reference observations with full provenance.
        for label in ('BP-ELASTIC-FOUNDATION', 'MUSE-ROBUSTNESS-01',
                      'DS-STATE-INTEGRITY-01', 'STEP-SCALE-01'):
            self.assertIn(label, rows)
            self.assertEqual(rows[label]['observations'][0]['kind'],
                             'cell_reference')
        # Task-less actor rows stay unresolved WITH provenance (identifiable,
        # not dropped): GLM, Local DYAD eye, Luna.
        unresolved_rows = [u['row'] for u in extra['unresolved']]
        self.assertEqual(len(unresolved_rows), 3)
        self.assertTrue(any('Luna' in u for u in unresolved_rows))
        self.assertTrue(any('Local DYAD eye' in u for u in unresolved_rows))
        # Prose lines naming controller task IDs are captured with kind.
        self.assertEqual(rows['master-catalogue-sync-01']
                         ['observations'][0]['kind'], 'prose_mention')
        # Structure rows are counted, never misread as data.
        self.assertGreaterEqual(extra['structural_rows'], 4)
        built = {'schema': SCHEMA,
                 'cards': [],
                 'master_rows': [rows[k] for k in sorted(rows)],
                 'coverage': {'cards': 0, 'domains': 0,
                              'master_row_ids': len(rows),
                              'master_row_observations': sum(
                                  len(r['observations']) for r in rows.values()),
                              'unresolved': extra['unresolved'],
                              'structural_rows': extra['structural_rows'],
                              'prose_mentions': extra['prose_mentions'],
                              'campaign_prose_refs':
                                  extra['campaign_prose_refs']}}
        self.assertEqual(validate_payload(built), [])

    def test_new_prefix_and_new_section_controls(self):
        # A brand-new kebab-case task ID in a brand-new section, in both the
        # discovered-requirements row shape and plain prose, must be captured
        # (no silent omission on future Master edits). A first cell outside
        # the documented ID grammars must remain VISIBLE as unresolved
        # provenance - classified, never dropped.
        text = ('## BRAND NEW SECTION (synthetic)\n\n'
                '| Task | Requirement and evidence | Next acceptance gate |\n'
                '|---|---|---|\n'
                '| `zeta-probe-07` — new discovered requirement | Synthetic '
                'new-prefix control row. | Falsifier must be stated. |\n'
                '| Not a task id | no leading ID here | visible as unresolved |\n\n'
                '### ANNEX (synthetic)\n\n'
                'Prose naming `omega-lab-02` in a brand-new prose section.\n')
        rows, extra = parse_master_rows(text)
        self.assertIn('zeta-probe-07', rows)
        self.assertEqual(rows['zeta-probe-07']['observations'][0]['kind'],
                         'table_row')
        self.assertIn('omega-lab-02', rows)
        self.assertEqual(rows['omega-lab-02']['observations'][0]['kind'],
                         'prose_mention')
        self.assertEqual(len(extra['unresolved']), 1)
        self.assertIn('Not a task id', extra['unresolved'][0]['row'])
        self.assertIn('BRAND NEW SECTION', extra['unresolved'][0]['section'])

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
                        id=sorted(c['id'] for c in built['cards'])[0])
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
    def test_parser_classification_units(self):
        # Proper markdown order: header row precedes its separator; data
        # rows follow. Structure rows are classified, never misread as data.
        text = ('## x\n\n'
                '### THE BACKLOG (maintained)\n\n'
                '| # | Item | Owner | State |\n'
                '| --- | --- | --- | --- |\n'
                '| B1 | skin | main | OPEN |\n'
                '| owner note | not a task |\n\n'
                '### OTHER SECTION\n\n'
                '| status only row |\n')
        rows, extra = parse_master_rows(text)
        self.assertEqual(list(rows), ['B1'])
        self.assertEqual(len(extra['unresolved']), 2)
        self.assertEqual(extra['structural_rows'], 2)  # separator + header
        self.assertEqual(rows['B1']['observations'][0]['columns'],
                         ['B1', 'skin', 'main', 'OPEN'])

    def test_validate_rejects_wrong_schema_and_missing_coverage(self):
        self.assertEqual(validate_payload({'schema': 'nope'}),
                         ['invalid_catalogue_payload'])
        p = payload(cards=[card_record('MATH-01')])
        p.pop('coverage')
        self.assertEqual(validate_payload(p), ['missing_catalogue_coverage'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
