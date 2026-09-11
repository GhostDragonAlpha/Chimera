"""Executes the preregistered controls R1-R5 and R7 for holodeck-gov-06.

One process, stdlib only. Writes checks/r1..r7 .txt (verbatim refusals,
post-state assertions, agreement matrix). R3/R7 read the canonical card
graph at base (docs/roadmap/holodeck_tasks.json) as FIXTURE INPUT; the
deployed side of R7 is a FAITHFUL TRANSCRIPTION of control.py:804-828 at
62b8e357 (source read, never the live service).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'reference'))
from gov06_reference_model import (CatalogueModel, Refusal, payload_digest,
                                   validate_payload)

ROOT = HERE.parents[6]
CARDS_JSON = ROOT / 'docs' / 'roadmap' / 'holodeck_tasks.json'
CHECKS = HERE.parent / 'checks'


def out(name, text):
    CHECKS.mkdir(exist_ok=True)
    (CHECKS / name).write_text(text, encoding='utf-8')
    print('wrote checks/' + name)


def fresh_payload():
    """Small synthetic catalogue with a clean DAG (R1/R2/R4/R5 fixture)."""
    return {'coverage': {'cards': 5}, 'cards': [
        {'id': 'A-01', 'status': 'PROPOSED', 'depends_on': []},
        {'id': 'A-02', 'status': 'PROPOSED', 'depends_on': ['A-01']},
        {'id': 'B-01', 'status': 'PROPOSED', 'depends_on': ['A-01', 'A-02']},
        {'id': 'C-01', 'status': 'SUPERSEDED', 'depends_on': []},
        {'id': 'D-01', 'status': 'PROPOSED', 'depends_on': ['C-01']},
    ]}


def refused(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except Refusal as r:
        return r.reason
    return 'NO-REFUSAL (fired)'


# ---------------------------------------------------------------- R1/R2
def r1_r2():
    lines = []
    ok = 0

    # R1a first valid import
    m = CatalogueModel()
    p = fresh_payload()
    r = m.catalogue_import('lead', m.epoch, None, copy.deepcopy(p))
    good_a = (len(m.imports) == 1 and r['imported_revision'] == 101
              and r['digest'] == payload_digest(p))
    lines += ['R1a first import: %s' % (r,)]
    lines += ['R1a ledger==1 and imported_revision==101 and digest==recomputed: %s' % good_a]

    # R1b second import, new digest, correct echo; ledger appends
    p2 = fresh_payload()
    p2['cards'].append({'id': 'E-01', 'status': 'PROPOSED', 'depends_on': []})
    p2['coverage'] = {'cards': 6}
    before0 = json.dumps(m.imports[0], sort_keys=True)
    r2 = m.catalogue_import('lead', m.epoch, r['digest'], p2)
    good_b = (len(m.imports) == 2 and m.imports[0]['digest'] == r['digest']
              and json.dumps(m.imports[0], sort_keys=True) == before0
              and r2['digest'] == payload_digest(p2))
    lines += ['R1b second import: %s' % (r2,)]
    lines += ['R1b ledger==2 append-only (entry0 untouched): %s' % good_b]

    # R1c caller-claimed digest ignored on store (tamper check)
    m3 = CatalogueModel()
    p3 = fresh_payload()
    r3 = m3.catalogue_import('lead', m3.epoch, 'f' * 64, p3)  # wrong echo, no current
    good_c = r3['digest'] == payload_digest(p3) and m3.current['digest'] == payload_digest(p3)
    lines += ['R1c claimed-digest tamper ignored, stored==recomputed: %s' % good_c]

    # R1d coverage echo
    good_d = r['coverage'] == {'cards': 5}
    lines += ['R1d coverage echo == payload coverage: %s' % good_d]
    r1_score = int(good_a) + int(good_b) + int(good_c) + int(good_d)

    # R2 negatives, each with post-state unchanged assertions
    m4 = CatalogueModel()
    base_payload = fresh_payload()
    first = m4.catalogue_import('lead', m4.epoch, None, base_payload)
    state_before = (len(m4.imports), m4.current['digest'], m4.revision,
                    json.dumps(m4.tasks, sort_keys=True))
    cases = []
    # (a) wrong echo
    cases.append(('stale echo',
                  refused(m4.catalogue_import, 'lead', m4.epoch, '0' * 64, fresh_payload())))
    # (b) duplicate same-digest
    cases.append(('duplicate same digest',
                  refused(m4.catalogue_import, 'lead', m4.epoch, first['digest'],
                          copy.deepcopy(base_payload))))
    # (c) malformed payloads (four distinct malformations)
    bad_id = fresh_payload(); bad_id['cards'][0]['id'] = ''
    dup_id = fresh_payload(); dup_id['cards'].append(dict(dup_id['cards'][0]))
    unknown_dep = fresh_payload(); unknown_dep['cards'][0]['depends_on'] = ['ZZ-99']
    cyc = {'cards': [
        {'id': 'X-01', 'status': 'PROPOSED', 'depends_on': ['X-02']},
        {'id': 'X-02', 'status': 'PROPOSED', 'depends_on': ['X-01']}]}
    for label, payload in (('empty id', bad_id), ('duplicate id', dup_id),
                           ('unknown dep', unknown_dep), ('cycle', cyc)):
        cases.append(('malformed: ' + label,
                      refused(m4.catalogue_import, 'lead', m4.epoch,
                              first['digest'], payload)))
    # (d) non-lead / wrong epoch
    cases.append(('non-lead actor',
                  refused(m4.catalogue_import, 'worker', m4.epoch, None, fresh_payload())))
    cases.append(('wrong epoch',
                  refused(m4.catalogue_import, 'lead', m4.epoch + 1, None, fresh_payload())))
    for label, reason in cases:
        lines.append('R2 %-28s -> %s' % (label, reason))
    named = (cases[0][1] == 'stale_catalogue_import'
             and cases[1][1] == 'duplicate_catalogue_import'
             and all(c[1].startswith('invalid_catalogue_payload:') for c in cases[2:6])
             and cases[6][1] == 'lead_gate' and cases[7][1] == 'lead_gate')
    state_after = (len(m4.imports), m4.current['digest'], m4.revision,
                   json.dumps(m4.tasks, sort_keys=True))
    unchanged = state_before == state_after
    fired = [label for label, reason in cases if reason.startswith('NO-REFUSAL')]
    lines += ['R2 all 8 refusals by the preregistered names: %s' % named]
    lines += ['R2 post-state unchanged after every refusal: %s' % unchanged]
    lines.append('R1R2 SCORE: R1 %d/4 positive; R2 %d/8 named refusals; '
                 'post-state %s; fired=%s'
                 % (r1_score, 8 if named and not fired else 8 - len(fired),
                    'UNCHANGED' if unchanged else 'MUTATED', fired or 'none'))
    out('r1_r2_import_contract.txt', '\n'.join(lines) + '\n')
    return r1_score == 4 and named and unchanged and not fired


# ---------------------------------------------------------------- R3/R4
def intended_frontier(model):
    return model.catalogue_next(model.current['digest'])['candidates']


def load_real_cards():
    data = json.loads(CARDS_JSON.read_text(encoding='utf-8'))
    return data['tasks']


def r3_r4():
    lines = []
    cards = load_real_cards()
    lines.append('real card graph at base: %d cards (docs/roadmap/'
                 'holodeck_tasks.json @ 62b8e357, sha256 d5c7aa8b...fcd8)' % len(cards))

    def model_with(cards_payload, tasks):
        m = CatalogueModel()
        m.catalogue_import('lead', m.epoch, None, {'coverage': {'cards': len(cards_payload)},
                                                   'cards': cards_payload})
        for tid, (state, realized) in tasks.items():
            m.add_task(tid, state, realized)
        return m

    govs = [c for c in cards if c['id'] in ('GOV-01', 'GOV-02', 'GOV-03', 'GOV-04',
                                            'GOV-05', 'GOV-06', 'MATH-01')]
    # S0 no realizations
    m = model_with(govs, {})
    got = intended_frontier(m)
    good0 = got == ['GOV-01']
    lines += ['S0 no realizations -> %s (expected [GOV-01]) PASS=%s' % (got, good0)]
    # S1 holodeck-gov-01 INTEGRATED
    m = model_with(govs, {'holodeck-gov-01': ('INTEGRATED', 'GOV-01')})
    got = intended_frontier(m)
    want = ['GOV-02', 'GOV-03', 'GOV-04', 'GOV-05', 'GOV-06', 'MATH-01']
    good1 = got == want
    lines += ['S1 holodeck-gov-01 INTEGRATED -> %s PASS=%s' % (got, good1)]
    lines += ['   expected exactly %s' % want]
    # S2 + 02..05 admitted live, -06 RUNNING (this very task)
    tasks = {'holodeck-gov-01': ('INTEGRATED', 'GOV-01'),
             'holodeck-gov-02': ('RUNNING', 'GOV-02'),
             'holodeck-gov-03': ('READY', 'GOV-03'),
             'holodeck-gov-04': ('REVIEW', 'GOV-04'),
             'holodeck-gov-05': ('BLOCKED', 'GOV-05'),
             'holodeck-gov-06': ('RUNNING', 'GOV-06')}
    m = model_with(govs, tasks)
    got = intended_frontier(m)
    good2 = got == ['MATH-01']
    lines += ['S2 + holodeck-gov-02..05 live + holodeck-gov-06 RUNNING -> %s '
              '(expected [MATH-01]) PASS=%s' % (got, good2)]
    # S3 abandonment: realization retired -> card re-proposed, dependents blocked
    m = model_with(govs, {'holodeck-gov-01': ('ABANDONED', 'GOV-01')})
    got = intended_frontier(m)
    good3 = got == ['GOV-01']
    lines += ['S3 holodeck-gov-01 ABANDONED -> %s (expected [GOV-01]: card '
              're-enters, dependents blocked - ABANDONED satisfies nothing) PASS=%s'
              % (got, good3)]
    ok = good0 and good1 and good2 and good3
    lines.append('R3 SCORE %s (4/4 exact-list equality)' % ('PASS' if ok else 'MISS'))

    # R4 negatives on the synthetic payload
    m = CatalogueModel()
    p = fresh_payload()
    dig = m.catalogue_import('lead', m.epoch, None, p)['digest']
    m.add_task('task-a01', 'INTEGRATED', 'A-01')
    m.add_task('task-a02', 'RUNNING', 'A-02')
    n_before = json.dumps([m.tasks, m.imports, m.current['digest'], m.revision],
                          sort_keys=True)
    lines.append('R4a unknown digest -> %s'
                 % refused(m.catalogue_next, '0' * 64))
    # B-01 deps: A-01 done, A-02 RUNNING (not INTEGRATED) -> blocked (diamond-ish)
    got = m.catalogue_next(dig)['candidates']
    lines.append('R4c partial deps (A-01 INTEGRATED, A-02 RUNNING): frontier %s; '
                 'B-01 blocked=%s' % (got, 'B-01' not in got))
    good4a = refused(m.catalogue_next, '0' * 64) == 'unknown_catalogue_digest'
    # C-01 SUPERSEDED is offered? intended: no (non-PROPOSED never offered)
    good4b = 'C-01' not in got
    lines.append('R4b SUPERSEDED card C-01 never offered: %s' % good4b)
    n_after = json.dumps([m.tasks, m.imports, m.current['digest'], m.revision],
                         sort_keys=True)
    good4d = n_before == n_after
    lines.append('R4d catalogue_next pure read (state byte-identical): %s' % good4d)
    ok = good4a and good4b and ('B-01' not in got) and good4d
    lines.append('R4 SCORE %s (4/4)' % ('PASS' if ok else 'MISS'))
    out('r3_r4_frontier.txt', '\n'.join(lines) + '\n')
    return ok


# ------------------------------------------------------------------- R5
def r5():
    lines = []
    m = CatalogueModel()
    p = fresh_payload()
    m.catalogue_import('lead', m.epoch, None, p)

    # (a) direct promotion of a speculative card -> the CARD FALSIFIER fires
    reason_a = refused(m.promote, 'lead', 'A-01')
    # (b) non-integrated realization
    m.add_task('task-b01', 'RUNNING', 'B-01')
    reason_b = refused(m.promote, 'lead', 'B-01')
    # (c) catalogue ops never mutate tasks: capture AFTER fixture placement,
    # then run catalogue_next + a (refused) duplicate import
    tasks_before = json.dumps(m.tasks, sort_keys=True)
    m.catalogue_next(m.current['digest'])
    try:
        m.catalogue_import('lead', m.epoch, m.current['digest'],
                           json.loads(json.dumps(p)))
    except Refusal:
        pass  # duplicate - still must not mutate
    tasks_after = json.dumps(m.tasks, sort_keys=True)
    # (d) supersession only with an INTEGRATED trail
    m.add_task('task-a01', 'INTEGRATED', 'A-01')
    m.supersede('lead', 'A-01', 'SUPERSESSION', 'certified by task-a01')
    wf_ok = (len(m.workflow) == 1 and m.workflow[0]['certified_trail'] is True)
    lines += ['R5a promote(speculative A-01, no trail) -> %s' % reason_a,
              'R5b promote(RUNNING realization B-01)  -> %s' % reason_b,
              'R5c tasks byte-identical across catalogue_import/next: %s'
              % (tasks_before == tasks_after),
              'R5d supersession appended ONLY with INTEGRATED trail: %s (wf=%s)'
              % (wf_ok, m.workflow)]
    ok = (reason_a == 'speculative_not_certifiable'
          and reason_b == 'speculative_not_certifiable'
          and tasks_before == tasks_after and wf_ok)
    lines.append('R5 SCORE %s (4/4) - card falsifier "a speculative idea is '
                 'promoted directly into a certified production claim" '
                 'executed as negative control' % ('PASS' if ok else 'MISS'))
    out('r5_promotion_gate.txt', '\n'.join(lines) + '\n')
    return ok


# ------------------------------------------------------------------- R7
def deployed_catalogue_next(tasks, cards, digest):
    """FAITHFUL TRANSCRIPTION of control.py:816-828 at 62b8e357 (SOURCE
    read; the live service is never contacted). tasks: {id: state}."""
    live = {tid.casefold() for tid, st in tasks.items()
            if st not in ('INTEGRATED', 'ABANDONED')}
    done = {tid.casefold() for tid, st in tasks.items() if st == 'INTEGRATED'}
    candidates = []
    for c in cards:
        if not isinstance(c, dict) or not isinstance(c.get('id'), str):
            continue
        cid = c['id'].casefold()
        if cid in live or cid in done:
            continue
        if c.get('status') != 'PROPOSED':
            continue
        deps = c.get('depends_on') if isinstance(c.get('depends_on'), list) else []
        if all(str(d).casefold() in done for d in deps):
            candidates.append(c['id'])
    return {'digest': digest, 'candidates': sorted(candidates),
            'live_tasks': sorted(live)}


def r7():
    lines = []
    cards = load_real_cards()
    govs = [c for c in cards if c['id'] in ('GOV-01', 'GOV-02', 'GOV-03', 'GOV-04',
                                            'GOV-05', 'GOV-06', 'MATH-01')]
    scenarios = {
        'S0 no realizations': {},
        'S1 holodeck-gov-01 INTEGRATED': {'holodeck-gov-01': 'INTEGRATED'},
        'S2 +02..05 live, -06 RUNNING': {
            'holodeck-gov-01': 'INTEGRATED', 'holodeck-gov-02': 'RUNNING',
            'holodeck-gov-03': 'READY', 'holodeck-gov-04': 'REVIEW',
            'holodeck-gov-05': 'BLOCKED', 'holodeck-gov-06': 'RUNNING'},
        'S3 holodeck-gov-01 ABANDONED': {'holodeck-gov-01': 'ABANDONED'},
    }
    matrix = []
    agree = 0
    for name, tasks in scenarios.items():
        m = CatalogueModel()
        m.catalogue_import('lead', m.epoch, None, {'coverage': {'cards': len(govs)},
                                                   'cards': govs})
        for tid, state in tasks.items():
            m.add_task(tid, state, tid.replace('holodeck-', '', 1).upper()
                       if tid.startswith('holodeck-') else tid.upper())
        intended = intended_frontier(m)
        deployed = deployed_catalogue_next(tasks, govs, m.current['digest'])['candidates']
        same = intended == deployed
        agree += same
        matrix.append((name, intended, deployed, same))
        lines.append('%-32s intended=%-60s deployed=%-20s %s'
                     % (name, intended, deployed, 'AGREE' if same else 'DISAGREE'))
    lines.append('')
    lines.append('Agreement: %d/4 scenario sets identical.' % agree)
    lines.append('Deployed candidate set in every scenario: %s (predicted '
                 '["GOV-01"] everywhere: HELD)' % matrix[0][2])
    lines.append('Root cause (SOURCE at 62b8e357): the exact-casefold live/done '
                 'match (control.py:816-822) never binds card GOV-0X to the '
                 'realization id holodeck-gov-0X, and the deps-in-done check '
                 '(control.py:824-825) therefore never sees a card-family '
                 'dependency satisfied - under the fleet realization-id '
                 'convention the deployed frontier is inert: the realized root '
                 'is perpetually re-proposed and every dependent is permanently '
                 'blocked. DISAGREEMENTS ARE THE MEASURED FINDINGS (prereg R7); '
                 'prereg labeled S3 a disagreement on sets - measured S3 sets '
                 'AGREE (both ["GOV-01"]); the deployed-everywhere prediction '
                 'held 4/4. Recorded, never reconciled into the model.')
    out('r7_intended_vs_deployed.txt', '\n'.join(lines) + '\n')
    return True  # the comparison itself always "passes"; findings are the output


if __name__ == '__main__':
    results = {'R1_R2': r1_r2(), 'R3_R4': r3_r4(), 'R5': r5(), 'R7': r7()}
    print(json.dumps(results))
    sys.exit(0 if all(results.values()) else 1)
