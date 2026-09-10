"""Canonical master catalogue: provenance-preserving import payload builder.

Projects the ENTIRE canonical catalogue - every card of
docs/roadmap/holodeck_tasks.json and every L*/B*/H* task row of
docs/THE_MASTER_LIST.md - into validated records for the controller's
catalogue plane. The catalogue is discoverable planning data only: it never
creates, claims, admits or mutates live tasks/claims/resources/slots.

No silent omissions: every parsed task row is kept (repeated observations of
the same ID accumulate as a list - history is preserved, never overwritten),
and pipe rows that do not resolve to a task ID inside the scoped sections are
counted in coverage.unresolved instead of being dropped.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = 'chimera-master-catalogue-v1'
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / 'docs/roadmap/holodeck_tasks.json'
DEFAULT_MASTER = ROOT / 'docs/THE_MASTER_LIST.md'
# Task-ID families found in the canonical document:
#  - legacy row codes: L1, B13b, H13b ...
#  - controller task IDs: kebab-case with a two-digit suffix
#    (demo-studio-state-01, gov01-evidence-reconcile-01, ...), possibly
#    backtick-quoted and followed by an em-dash qualifier in the same cell.
LEGACY_ID_RE = re.compile(r'[LBH][A-Za-z]?\d+[A-Za-z0-9-]*')
KEBAB_ID_RE = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*-\d{2}\b')
# Uppercase campaign/project labels (BP-ELASTIC-FOUNDATION,
# MUSE-ROBUSTNESS-01) - recorded as references, never as row identities.
CAMPAIGN_RE = re.compile(r'[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+')
# Structural table rows that carry no task content.
HEADER_CELLS = {'#', 'id', 'task', 'line'}


def _sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _cell_id(cell):
    """Extract a task ID from a table cell, or None.

    Handles backtick quoting and em-dash qualifiers
    ("`engine-demo-01` — reset-state correction" -> engine-demo-01).
    """
    head = re.split(r'[—–]| -- ', cell, maxsplit=1)[0]
    head = head.strip().strip('`').strip()
    if LEGACY_ID_RE.fullmatch(head):
        return head
    if KEBAB_ID_RE.fullmatch(head):
        return head
    return None


def payload_digest(payload):
    return _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def parse_master_rows(text):
    """Return ({id: row record}, coverage extras).

    EVERY pipe-table row in EVERY section is classified (task-bearing rows
    are not gated on specific section names); rows whose first cell yields a
    task ID (legacy L/B/H codes or backticked kebab-case controller IDs,
    em-dash qualifiers stripped) become observations keyed by that ID.
    Repeated rows of the same ID each become one observation; nothing is
    deduplicated. Non-task pipe rows and prose lines mentioning controller
    task IDs are reported with section/line provenance - never silently
    dropped:
      extras['unresolved']       pipe rows with no recognizable task ID
                                 (separator/header structure rows excluded)
      extras['structural_rows']  separator/header rows
      extras['prose_mentions']   non-table lines naming a task ID
      extras['campaign_prose_refs']  uppercase project labels in prose
    """
    lines = text.splitlines()

    def separator(cells):
        return bool(cells) and all(re.fullmatch(r':?-{3,}:?', c) for c in cells)

    # Markdown headers precede their separator: precompute which pipe rows
    # are headers so they are classified structurally, not as data.
    pipe_rows = []
    for lineno, raw in enumerate(lines, 1):
        line = raw.strip()
        if line.startswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            pipe_rows.append((lineno, cells, separator(cells)))
    header_lines = set()
    for i, (lineno, cells, sep) in enumerate(pipe_rows):
        if sep and i > 0 and not pipe_rows[i - 1][2]:
            header_lines.add(pipe_rows[i - 1][0])

    rows = {}
    unresolved = []
    structural = 0
    prose_mentions = []
    campaign_prose = []
    section = None

    def record(ident, observation):
        rows.setdefault(ident, {'plane': 'master_row', 'id': ident,
                                'observations': []})['observations'].append(
            observation)

    def campaign_refs(cells):
        found = []
        seen = set()
        for cell in cells:
            for m in CAMPAIGN_RE.finditer(cell):
                if m.group(0) not in seen:
                    seen.add(m.group(0))
                    found.append(m.group(0))
        return found

    for lineno, raw in enumerate(lines, 1):
        line = raw.strip()
        if line.startswith('#'):
            section = line
            continue
        if line.startswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if separator(cells) or lineno in header_lines or (
                    cells and cells[0].strip('` ').casefold() in HEADER_CELLS):
                structural += 1  # table structure, not a task row
                continue
            ident = _cell_id(cells[0]) if cells else None
            if ident is None:
                refs = campaign_refs(cells)
                if refs:
                    # Assignment-style row without a leading task ID: keep
                    # every campaign reference with full provenance.
                    for ref in refs:
                        record(ref, {'kind': 'cell_reference', 'section': section,
                                     'line': lineno, 'columns': cells,
                                     'content_sha256': _sha(json.dumps(
                                         cells, ensure_ascii=False))})
                else:
                    unresolved.append({'line': lineno, 'section': section,
                                       'row': line[:200]})
                continue
            record(ident, {'kind': 'table_row', 'section': section,
                           'line': lineno, 'columns': cells,
                           'content_sha256': _sha(json.dumps(
                               cells, ensure_ascii=False))})
            continue
        if line:
            # Prose: controller task IDs are cited backtick-quoted; capture
            # those by ID. Unbackticked hyphen-numbered candidates (dates,
            # figure/section numbers) are REPORTED in extras - visible and
            # classified, without polluting the catalogue ID set.
            for span in re.findall(r'`([^`]+)`', line):
                span = span.strip()
                if LEGACY_ID_RE.fullmatch(span) or KEBAB_ID_RE.fullmatch(span):
                    if re.search(r'\d{4}', span):
                        continue  # a dated reference, not a task ID
                    record(span, {'kind': 'prose_mention', 'section': section,
                                  'line': lineno, 'text': line[:200],
                                  'content_sha256': _sha(line)})
                    prose_mentions.append({'id': span, 'line': lineno})
            for m in KEBAB_ID_RE.finditer(line):
                cand = m.group(0)
                if re.search(r'\d{4}', cand):
                    continue
                if '`' + cand + '`' not in line:
                    campaign_prose.append({'id': cand, 'line': lineno,
                                           'class': 'prose_candidate'})
    extras = {'unresolved': unresolved, 'structural_rows': structural,
              'prose_mentions': prose_mentions,
              'campaign_prose_refs': campaign_prose}
    return rows, extras


def build_records(catalog_path=DEFAULT_CATALOG, master_path=DEFAULT_MASTER,
                  catalog_text=None, master_text=None):
    """Build the import payload from the canonical sources (read-only)."""
    catalog_text = (catalog_text if catalog_text is not None
                    else Path(catalog_path).read_text(encoding='utf-8'))
    master_text = (master_text if master_text is not None
                   else Path(master_path).read_text(encoding='utf-8'))
    try:
        data = json.loads(catalog_text)
    except ValueError as exc:
        raise ValueError('malformed_catalog_input: ' + str(exc))
    if not isinstance(data, dict):
        raise ValueError('malformed_catalog_input: root is not an object')
    cards = []
    for index, card in enumerate(data.get('tasks', [])):
        if not isinstance(card, dict):
            raise ValueError('malformed_catalog_input: card %d not an object' % index)
        cid = card.get('id')
        if not isinstance(cid, str) or not cid.strip():
            raise ValueError('malformed_catalog_input: card %d missing id' % index)
        cards.append({'plane': 'card', 'id': cid, 'domain': card.get('domain'),
                      'title': card.get('title'), 'status': card.get('status'),
                      'depends_on': card.get('depends_on', []),
                      'source': {'path': str(catalog_path), 'index': index},
                      'content_sha256': _sha(json.dumps(card, sort_keys=True,
                                                        ensure_ascii=False)),
                      'card': card})
    rows, extra = parse_master_rows(master_text)
    return {'schema': SCHEMA, 'cards': cards,
            'master_rows': [rows[k] for k in sorted(rows)],
            'coverage': {'cards': len(cards),
                         'domains': len(data.get('domains', [])),
                         'master_row_ids': len(rows),
                         'master_row_observations': sum(
                             len(r['observations']) for r in rows.values()),
                         'unresolved': extra['unresolved'],
                         'structural_rows': extra['structural_rows'],
                         'prose_mentions': extra['prose_mentions'],
                         'campaign_prose_refs': extra['campaign_prose_refs']}}


def validate_payload(payload):
    """Controller-side validation. Returns a list of named errors (empty=ok)."""
    if not isinstance(payload, dict) or payload.get('schema') != SCHEMA:
        return ['invalid_catalogue_payload']
    cards = payload.get('cards')
    rows = payload.get('master_rows')
    if not isinstance(cards, list) or not isinstance(rows, list):
        return ['invalid_catalogue_payload']
    if not cards and not rows:
        return ['empty_catalogue_payload']
    if not isinstance(payload.get('coverage'), dict):
        return ['missing_catalogue_coverage']
    errors = []
    by_id = set()
    row_ids = set()
    for c in cards:
        if (not isinstance(c, dict) or c.get('plane') != 'card'
                or not isinstance(c.get('id'), str) or not c['id']):
            errors.append('malformed_card_record')
            continue
        if c['id'] in by_id:
            errors.append('duplicate_catalogue_id:' + c['id'])
        by_id.add(c['id'])
        if (not isinstance(c.get('card'), dict)
                or not re.fullmatch('[0-9a-f]{64}', str(c.get('content_sha256', '')))):
            errors.append('malformed_card_record:' + c['id'])
    deps = {}
    for c in cards:
        if isinstance(c, dict) and isinstance(c.get('id'), str) and c['id'] in by_id:
            d = c.get('depends_on', [])
            if not isinstance(d, list):
                errors.append('malformed_card_record:' + c['id'])
            elif any(not isinstance(dep, str) for dep in d):
                errors.append('malformed_card_dependency:' + c['id'])
            else:
                deps[c['id']] = d
    for ident, d in deps.items():
        for dep in d:
            if dep not in deps:
                errors.append('catalogue_unknown_dependency:' + ident + '->' + str(dep))
    for r in rows:
        if (not isinstance(r, dict) or r.get('plane') != 'master_row'
                or not isinstance(r.get('id'), str) or not r['id']):
            errors.append('malformed_master_row')
            continue
        if r['id'] in row_ids:
            errors.append('duplicate_master_row_id:' + r['id'])
        row_ids.add(r['id'])
        obs = r.get('observations')
        if not isinstance(obs, list) or not obs:
            errors.append('malformed_master_row:' + r['id'])
            continue
        for o in obs:
            kind = o.get('kind') if isinstance(o, dict) else None
            ok_shape = (
                isinstance(o, dict) and type(o.get('line')) is int
                and re.fullmatch('[0-9a-f]{64}', str(o.get('content_sha256', '')))
                and ((kind in ('table_row', 'cell_reference')
                      and isinstance(o.get('columns'), list)
                      and bool(o['columns']))
                     or (kind == 'prose_mention'
                         and isinstance(o.get('text'), str) and o['text'])))
            if not ok_shape:
                errors.append('malformed_master_row:' + r['id'])
                break
    state = {}

    def visit(ident):
        if state.get(ident) == 1:
            errors.append('catalogue_dependency_cycle:' + ident)
            return
        if state.get(ident) == 2:
            return
        state[ident] = 1
        for dep in deps.get(ident, ()):
            if dep in deps:
                visit(dep)
        state[ident] = 2

    for ident in sorted(deps):
        visit(ident)
    return errors


def main(argv=None):
    """Read-only payload builder for the lead's import step. Emits the import
    arguments JSON (payload + digest) and a coverage summary. Performs no
    controller calls and writes nothing unless --out is given."""
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    p.add_argument('--master', type=Path, default=DEFAULT_MASTER)
    p.add_argument('--out', type=Path, default=None,
                   help='write {"payload":..., "digest":...} JSON here')
    a = p.parse_args(argv)
    built = build_records(catalog_path=a.catalog, master_path=a.master)
    errors = validate_payload(built)
    if errors:
        print('REFUSED: ' + ', '.join(errors[:5]), file=sys.stderr)
        return 2
    body = json.dumps(built, ensure_ascii=False)
    print('coverage: ' + json.dumps(built['coverage'], ensure_ascii=False))
    print('digest: ' + payload_digest(built))
    if a.out is not None:
        a.out.write_text(json.dumps({'payload': built,
                                     'digest': payload_digest(built)},
                                    ensure_ascii=False), encoding='utf-8')
        print('wrote ' + str(a.out))
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
