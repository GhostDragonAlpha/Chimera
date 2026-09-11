"""Master-catalogue import tests. Isolated temp registries ONLY - this suite
never touches the live registry (E:/ChimeraWork/control/state.sqlite)."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from control import Control, Refusal
from master_catalogue import (SCHEMA, build_records, main as master_catalogue_main,
                              parse_master_rows, payload_digest, source_manifest,
                              validate_payload)

BASE = 'a' * 40
HEAD = 'b' * 40
MERGED = 'c' * 40
# gen-5: the verbatim current-Master fixture is committed alongside the
# parser so the no-silent-omission control is pinned to an exact source
# revision (the same revision the live import reads).
CURRENT_MASTER_FIXTURE = (HERE.parent.parent / 'docs' / 'evidence' / 'agent_fleet'
                          / 'MASTER_CATALOGUE_SYNC'
                          / 'MASTER_CURRENT_EXCERPT_20260910.md')


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


def payload(cards=(), rows=(), master_text=None, catalog_text=None):
    """Build a minimal VALID payload around the given records.

    The payload shape is the gen-5 contract: source_manifest (no supplied
    source_versions) plus an exhaustive verbatim line_partition from which
    the validator recomputes the manifest hash and every counter.
    """
    partition = {}
    if master_text is None:
        # Honest default: retain a synthetic master line per row record so
        # the manifest/retention contract holds for every fixture payload.
        lines = []
        for r in rows:
            obs = r.get('observations') or []
            if not obs:
                # Malformed records must still be transportable to the
                # validator - that is exactly what the negative controls test.
                lines.append(str(r.get('id') or 'unidentifiable-row'))
                continue
            o = obs[0]
            lines.append(o.get('text') if o.get('kind') == 'prose_mention'
                         else ' | '.join(o.get('columns') or [r.get('id')]))
        master_text = '\n'.join(lines)
    for n, textline in enumerate(master_text.splitlines(), 1):
        partition[n] = {'class': 'prose', 'text': textline,
                        'sha256': _sha(textline)}
    if not rows and master_text is None:
        # No master-plane records: an empty partition is the honest shape.
        partition = {}
    if catalog_text is None:
        # gen-6/7 contract: catalog_text must be exact JSON bytes matching
        # validator rebuild. source_manifest(catalog) requires canonical=False.
        catalog_text = json.dumps({'tasks': [c['card'] for c in cards]},
                                   ensure_ascii=False)
    manifest = {'catalog': source_manifest(catalog_text, 'fixture',
                                           None, retained=True, canonical=False),
                'master': source_manifest(master_text, 'fixture',
                                          None, retained=bool(rows or
                                                              master_text is not None))}
    payload_body = {'schema': SCHEMA, 'cards': list(cards), 'master_rows': list(rows),
            'source_manifest': manifest,
            'coverage': {'cards': len(cards),
                         'domains': len({c['domain'] for c in cards}),
                         'master_row_ids': len({r['id'] for r in rows}),
                         'master_row_observations': sum(
                             len(r['observations']) for r in rows),
                         'unresolved': 0,
                         'unresolved_records': [],
                         'structural_rows': 0,
                         'prose_mentions': 0,
                         'prose_mention_records': [],
                         'campaign_prose_refs': 0,
                         'campaign_prose_records': [],
                         'unkeyed_requirements': 0,
                         'unkeyed_requirement_records': [],
                         'line_partition': partition,
                         'version_pin': {
                             'master_sha256': manifest['master']['sha256'],
                             'catalog_sha256': manifest['catalog']['sha256']}}}
    payload_body['catalog_text'] = catalog_text
    # gen-7 contract: each card record claims its EXACT enumeration position.
    for i, c in enumerate(cards):
        c['source'] = {'path': 'fixture', 'index': i}
    return payload_body


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
        # gen-5 correction: source_versions (submitter-supplied hashes) is
        # GONE; source_manifest is computed from the retained source and the
        # validator recomputes its hash from the verbatim line partition.
        self.assertNotIn('source_versions', built)
        sm = built['source_manifest']
        self.assertEqual(sm['master']['path'].endswith('THE_MASTER_LIST.md'), True)
        self.assertRegex(sm['master']['git_commit'] or '', r'^[0-9a-f]{40}$')
        self.assertRegex(sm['master']['sha256'], r'^[0-9a-f]{64}$')
        self.assertTrue(sm['master']['retained'])
        # gen-6: the catalog JSON text is ALSO retained verbatim and its
        # manifest hash is recomputed by the validator.
        self.assertTrue(sm['catalog']['retained'])
        # repinned to measured builder output (CATALOGUE_REPIN_02, base
        # f9ef0ebe): the 2026-09-11 second-wave doc merges (PR #49 Master
        # maintenance amendment + PR #50 evidence) grew the corpus past the
        # 76/96 pins left by CATALOGUE_REPIN at d012b4b1.
        self.assertEqual(built['coverage']['master_row_ids'], 97)
        self.assertEqual(built['coverage']['master_row_observations'], 142)
        ids = {r['id'] for r in built['master_rows']}
        for required in ('demo-studio-state-01', 'math-contract-audit-01',
                         'fleet-slot-binding-01', 'studio-grid-depth-01',
                         'fleet-controller-upgrade-01', 'gov01-evidence-reconcile-01',
                         'L1', 'B1', 'H1'):
            self.assertIn(required, ids)
        self.assertFalse(validate_payload(built))
        # gen-5: the EXHAUSTIVE partition retains every line verbatim.
        part = built['coverage']['line_partition']
        self.assertEqual(sorted(part), list(range(1, len(part) + 1)))
        # the lead's exact falsifier: Master line 1825 (the plain-prose B7b
        # requirement continuation) must be retained, not dropped.
        self.assertEqual(part[1825]['class'], 'prose')
        self.assertIn('B7b', part[1825]['text'])
        self.assertIn('B7b', json.dumps(built['coverage']['unkeyed_requirement_records']))
        # gen-4: unkeyed requirement prose (e.g. the plain B7b requirement
        # lines and Research Annex falsifier bullets - no keyed ID) is
        # preserved with provenance/classification, never dropped.
        unkeyed_text = json.dumps(built['coverage']['unkeyed_requirement_records'])
        self.assertIn('B7b', unkeyed_text,
                      'the plain B7b requirement prose must be preserved')
        self.assertTrue(built['coverage']['unkeyed_requirements'],
                        'annex/honest-negative requirement bullets must be kept')
        for u in built['coverage']['unkeyed_requirement_records']:
            self.assertIn('line', u)
            self.assertIn('section', u)
            self.assertEqual(u['kind'], 'unkeyed_requirement')
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
        unresolved = built['coverage']['unresolved_records']
        self.assertTrue(unresolved, 'actor-roster rows must be reported')
        self.assertEqual(built['coverage']['unresolved'], len(unresolved))
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
        built = payload(rows=[rows[k] for k in sorted(rows)],
                        master_text=CURRENT_MASTER_FIXTURE.read_text(
                            encoding='utf-8'))
        self.assertEqual(validate_payload(built), [])

    def test_new_section_requirement_row_and_prose_mention_unresolved_visible(self):
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
        row_dups = payload(
            cards=[card_record('MATH-01')],
            rows=[row_record('B1', 'B1 | skin | main | OPEN'),
                  row_record('B1', 'B1 | skin | main | OPEN2')]
        )
        # gen-5: the validator recomputes coverage from the records, so the
        # duplicate-row payload must declare the HONEST count (2) or the
        # forged-count check fires first. With the honest count, the
        # duplicate-ID structural check is what fires.
        row_dups['coverage']['master_row_ids'] = 2
        row_dups['coverage']['master_row_observations'] = 2
        self.assertIn('duplicate_master_row_id:B1',
                      validate_payload(row_dups))
        cyc = payload(cards=[card_record('MATH-01', deps=('MATH-02',)),
                             card_record('MATH-02', deps=('MATH-01',))])
        with self.assertRaisesRegex(Refusal, 'catalogue_dependency_cycle'):
            self.imp(cyc)
        unknown = payload(cards=[card_record('MATH-01', deps=('GHOST',))])
        with self.assertRaisesRegex(Refusal, 'catalogue_unknown_dependency'):
            self.imp(unknown)
        bad_dep = payload(cards=[card_record('MATH-01', deps=({},))])
        self.assertIn('malformed_card_dependency:MATH-01',
                      validate_payload(bad_dep))
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

    def test_forged_coverage_counts_refused(self):
        # gen-4 lead finding: coverage counts were trusted from the submitter.
        # The validator now recomputes them from the records.
        good = payload(cards=[card_record('MATH-01'), card_record('MATH-02')],
                       rows=[row_record('B1', 'B1 | x | y | z')])
        self.assertEqual(validate_payload(good), [])
        forged = json.loads(json.dumps(good))
        forged['coverage']['cards'] = 240
        self.assertEqual(validate_payload(forged), ['coverage_mismatch:cards'])
        forged2 = json.loads(json.dumps(good))
        forged2['coverage']['master_row_observations'] = 99
        self.assertEqual(validate_payload(forged2),
                         ['coverage_mismatch:master_row_observations'])
        forged3 = json.loads(json.dumps(good))
        forged3['coverage']['unresolved'] = 'nothing to see'
        self.assertEqual(validate_payload(forged3),
                         ['coverage_mismatch:unresolved'])
        forged4 = json.loads(json.dumps(good))
        forged4['coverage']['unresolved'] = 1
        forged4['coverage']['unresolved_records'] = [{'no': 'provenance'}]
        self.assertEqual(validate_payload(forged4),
                         ['malformed_coverage_unresolved'])

    # --- gen-5 lead falsifiers, mirrored exactly --------------------------
    def test_gen5_supplied_source_versions_refused(self):
        # Falsifier 1: build_records() no longer emits source_versions, and
        # validate_payload refuses any supplied version block outright - a
        # submitter hash can never masquerade as proof against live files.
        built = build_records()
        self.assertNotIn('source_versions', built)
        forged = json.loads(json.dumps(built))
        forged['source_versions'] = {'master': {'sha256': 'f' * 64}}
        self.assertEqual(validate_payload(forged),
                         ['supplied_source_versions_refused'])
        # Manifest hash is RECOMPUTED from the retained partition, so an
        # altered manifest hash cannot pass.
        forged2 = json.loads(json.dumps(built))
        forged2['source_manifest']['master']['sha256'] = 'f' * 64
        self.assertEqual(validate_payload(forged2),
                         ['source_manifest_hash_mismatch'])
        missing = json.loads(json.dumps(built))
        missing.pop('source_manifest')
        self.assertEqual(validate_payload(missing), ['missing_source_manifest'])

    def test_gen5_forged_domain_count_refused(self):
        # Falsifier 2: coverage.domains=999 was accepted; the count is now
        # recomputed from the card records.
        built = payload(cards=[card_record('MATH-01', domain='GOV'),
                               card_record('MATH-02', domain='SIM')])
        self.assertEqual(built['coverage']['domains'], 2)
        forged = json.loads(json.dumps(built))
        forged['coverage']['domains'] = 999
        self.assertEqual(validate_payload(forged),
                         ['coverage_mismatch:domains'])
        forged2 = json.loads(json.dumps(built))
        forged2['coverage']['unkeyed_requirements'] = 999
        self.assertEqual(validate_payload(forged2),
                         ['coverage_mismatch:unkeyed_requirements'])
        no_pin = json.loads(json.dumps(built))
        no_pin['coverage'].pop('version_pin')
        self.assertEqual(validate_payload(no_pin), ['missing_version_pin'])

    def test_gen6_catalog_manifest_is_verified(self):
        # Lead gen-6 finding: the catalog entry of the manifest (hash and
        # git_commit) could be altered without rejection because the
        # validator never checked it against retained source.
        built = payload(cards=[card_record('MATH-01')])
        self.assertEqual(validate_payload(built), [])
        self.assertTrue(built['source_manifest']['catalog']['retained'])
        # altered catalog hash is refused
        forged = json.loads(json.dumps(built))
        forged['source_manifest']['catalog']['sha256'] = 'f' * 64
        self.assertEqual(validate_payload(forged),
                         ['source_manifest_catalog_hash_mismatch'])
        # altered version_pin catalog sha is refused
        forged2 = json.loads(json.dumps(built))
        forged2['coverage']['version_pin']['catalog_sha256'] = 'e' * 64
        self.assertEqual(validate_payload(forged2), ['missing_version_pin'])
        # a tampered catalog_text is refused: the manifest hash (recomputed
        # from the submitted text) fires first, and the card records would
        # no longer reproduce from it either.
        forged3 = json.loads(json.dumps(built))
        catalog = json.loads(forged3['catalog_text'])
        catalog['tasks'][0]['status'] = 'READY'
        forged3['catalog_text'] = json.dumps(catalog)
        self.assertEqual(validate_payload(forged3),
                         ['source_manifest_catalog_hash_mismatch'])
        # missing catalog text with cards present is refused
        forged4 = json.loads(json.dumps(built))
        forged4.pop('catalog_text')
        self.assertEqual(validate_payload(forged4), ['missing_catalog_text'])
        # git_commit fields are format-constrained (null or full hex sha)
        forged5 = json.loads(json.dumps(built))
        forged5['source_manifest']['catalog']['git_commit'] = 'not-a-sha'
        self.assertEqual(validate_payload(forged5), ['malformed_git_commit'])
        # an honest full-sha git_commit passes
        ok = json.loads(json.dumps(built))
        ok['source_manifest']['catalog']['git_commit'] = 'a' * 40
        ok['source_manifest']['master']['git_commit'] = 'b' * 40
        self.assertEqual(validate_payload(ok), [])

    def test_gen7_digest_is_transport_reproducible(self):
        # The controller recomputes payload_digest on the RECEIVED JSON body.
        # JSON round-trips stringify dict keys (line_partition is keyed by
        # int line numbers in memory), so the digest must be computed over
        # the round-tripped form or every transported payload fails the
        # digest gate. Falsifier: any in-memory vs round-tripped digest
        # mismatch on the real payload.
        built = build_records()
        self.assertEqual(payload_digest(built),
                         payload_digest(json.loads(json.dumps(built))))

    def test_gen7_catalog_consistency_counterexamples(self):
        # Lead gen-7 counterexample 1: `if cards:` skipped catalog
        # reconstruction for an empty submitted list, so all cards could be
        # omitted while catalog_text.tasks remained nonempty.
        built = payload(cards=[card_record('MATH-01')],
                        rows=[row_record('B1', 'B1 | x | y | z')])
        empty = json.loads(json.dumps(built))
        empty['cards'] = []
        empty['coverage']['cards'] = 0
        empty['coverage']['domains'] = 0
        self.assertEqual(validate_payload(empty), ['catalog_cards_mismatch'])
        # a fully-empty payload still cannot smuggle a hidden catalog: the
        # emptiness guard refuses it outright.
        bare = payload(cards=[])
        self.assertEqual(validate_payload(bare), ['empty_catalogue_payload'])
        # an honest empty-cards payload carries the empty-tasks JSON text
        # (always-rebuild contract), and a fully-empty import is still
        # refused by the preregistered vacuity gate - independently of the
        # catalog-text check.
        ok_empty = payload(cards=[])
        self.assertEqual(ok_empty['catalog_text'], json.dumps({'tasks': []},
                                                              ensure_ascii=False))
        self.assertEqual(validate_payload(ok_empty),
                         ['empty_catalogue_payload'])
        # counterexample 2: catalog manifest bytes/lines were alterable.
        forged = json.loads(json.dumps(built))
        forged['source_manifest']['catalog']['bytes'] = 1
        self.assertEqual(validate_payload(forged),
                         ['source_manifest_consistency:bytes'])
        forged2 = json.loads(json.dumps(built))
        forged2['source_manifest']['catalog']['lines'] = 99
        self.assertEqual(validate_payload(forged2),
                         ['source_manifest_consistency:lines'])
        # counterexample 3: arbitrary/duplicate source indices passed.
        forged3 = json.loads(json.dumps(built))
        forged3['cards'][0]['source']['index'] = 999
        self.assertEqual(validate_payload(forged3),
                         ['catalog_cards_mismatch'])
        pair = payload(cards=[card_record('MATH-01'), card_record('MATH-02')])
        self.assertEqual(validate_payload(pair), [])
        dup = json.loads(json.dumps(pair))
        dup['cards'][1]['source']['index'] = 0  # duplicate of card 0
        self.assertEqual(validate_payload(dup), ['catalog_cards_mismatch'])

    def test_gen5_exhaustive_partition_no_silent_omissions(self):
        # Falsifier 3: dropping or tampering with ANY line - specifically the
        # lead's B7b continuation at Master line 1825 - is refused; every
        # line must be retained verbatim with a consistent hash.
        built = build_records()
        part = built['coverage']['line_partition']
        # 2780 lines at the current canonical Master (measured via the
        # builder at base f9ef0ebe, CATALOGUE_REPIN_02); the count is
        # descriptive - exhaustiveness is what the validator enforces,
        # independent of any frozen total.
        self.assertEqual(len(part), 2780)
        dropped = json.loads(json.dumps(built))
        dropped['coverage']['line_partition'].pop('1825')  # JSON-stringified
        self.assertEqual(validate_payload(dropped),
                         ['line_partition_not_exhaustive'])
        tampered = json.loads(json.dumps(built))
        tampered['coverage']['line_partition']['1825'] = {
            'class': 'prose', 'text': 'tampered', 'sha256': _sha('tampered')}
        self.assertEqual(validate_payload(tampered),
                         ['source_manifest_hash_mismatch'])
        # a partition with self-inconsistent hashes is refused
        bad_hash = json.loads(json.dumps(built))
        bad_hash['coverage']['line_partition']['10']['sha256'] = '0' * 64
        self.assertEqual(validate_payload(bad_hash),
                         ['malformed_line_partition'])
        # an unknown partition class is refused
        bad_class = json.loads(json.dumps(built))
        bad_class['coverage']['line_partition']['10']['class'] = 'mystery'
        self.assertEqual(validate_payload(bad_class),
                         ['malformed_line_partition'])

    def test_unkeyed_requirement_capture_control(self):
        text = ('## 9 - RESEARCH ANNEX (concepts)\n\n'
                '- **External concept entry.** Some approach description with'
                ' enough length to qualify as content in the record.\n'
                '  Falsifier for us: any rule that cannot be written as a'
                ' discrete operator is a smell, not a law.\n'
                'Short.\n')
        rows, extra = parse_master_rows(text)
        self.assertEqual(len(extra['unkeyed_requirements']), 2)
        kinds = {u['kind'] for u in extra['unkeyed_requirements']}
        self.assertEqual(kinds, {'unkeyed_requirement'})
        texts = ' '.join(u['text'] for u in extra['unkeyed_requirements'])
        self.assertIn('Falsifier for us', texts)
        self.assertNotIn('Short.', texts)

    def test_new_prefix_and_new_section_controls(self):
        # No-silent-omission control: a brand-new backticked controller ID in
        # prose and a brand-new table row in a brand-new section must BOTH be
        # captured with their own provenance, whatever section they live in.
        text = ('## 99 - FRESH SECTIONS (proposed)\n\n'
                'A brand-new task `zeta-probe-07` is proposed here, and a '
                'brand-new section carries its own table.\n\n'
                '### NEW LAB\n\n'
                '| # | Item | Owner | State |\n'
                '| --- | --- | --- | --- |\n'
                '| omega-lab-02 | new thing | nobody | OPEN |\n')
        rows, extra = parse_master_rows(text)
        self.assertIn('zeta-probe-07', rows)
        self.assertIn('omega-lab-02', rows)
        # distinct provenance: the prose candidate is a mention, the fresh
        # section's row is a table_row - they must not be conflated.
        self.assertEqual(rows['zeta-probe-07']['observations'][0]['kind'],
                         'prose_mention')
        self.assertEqual(rows['omega-lab-02']['observations'][0]['kind'],
                         'table_row')
        self.assertEqual(rows['omega-lab-02']['observations'][0]['section'],
                         '### NEW LAB')
        self.assertEqual(extra['unresolved'], [])
        # and a row with no recognizable ID in a fresh section is reported,
        # never silently dropped.
        text2 = ('### ANOTHER NEW SECTION\n\n'
                 '| not-a-task | just a row |\n')
        _, extra2 = parse_master_rows(text2)
        self.assertEqual(len(extra2['unresolved']), 1)
        self.assertEqual(extra2['unresolved'][0]['section'],
                         '### ANOTHER NEW SECTION')


    def test_cli_stdout_survives_ascii_console_and_writes_out_first(self):
        # Fresh-system falsifier 2026-09-10 (gen 11, glm53-fresh-01): on a
        # cp1252 Windows console, main() crashed with UnicodeEncodeError while
        # printing the ensure_ascii=False coverage summary (the canonical
        # Master contains arrows), and the --out import artifact was never
        # written - MIGRATION.md step 1 failed verbatim. Contract: the
        # artifact is written FIRST, the console summary never raises, and
        # stdout stays decodable on a host whose stdout encoding is ASCII.
        cards = [card_record('A1'), card_record('A2', deps=('A1',))]
        # Explicit source FILES: main() reads from the given paths (the
        # defaults resolve to the canonical repo documents). The master text
        # contains U+2192, the exact character class that killed the original
        # run on a cp1252 console.
        catalog_path = self.root / 'catalog.json'
        catalog_path.write_text(
            json.dumps({'tasks': [c['card'] for c in cards]},
                       ensure_ascii=False), encoding='utf-8')
        master_path = self.root / 'master.md'
        master_text = ('# T\n\n- arrow \u2192 test line with enough length to be\n'
                       '  content in the record.\n\n| `A1` | x |\n| `A2` | y |\n')
        master_path.write_text(master_text, encoding='utf-8')
        out_path = self.root / 'import_args.json'
        monkey_stdout = io.StringIO()
        real_stdout, sys.stdout = sys.stdout, monkey_stdout
        try:
            rc = master_catalogue_main(['--catalog', str(catalog_path),
                                        '--master', str(master_path),
                                        '--out', str(out_path)])
        finally:
            sys.stdout = real_stdout
        self.assertEqual(rc, 0)
        text = monkey_stdout.getvalue()
        # Summary must survive an ASCII-only stream and stay decodable.
        text.encode(monkey_stdout.encoding or 'ascii')
        # The deliverable exists, carries a matching digest, and keeps the
        # verbatim Unicode arrow that a naive console print would have lost.
        written = json.loads(out_path.read_text(encoding='utf-8'))
        self.assertIn('digest: ' + payload_digest(written['payload']), text)
        self.assertEqual(written['payload']['coverage']['cards'], 2)
        self.assertIn('\u2192', json.dumps(written['payload'], ensure_ascii=False))


if __name__ == '__main__':
    unittest.main(verbosity=2)
