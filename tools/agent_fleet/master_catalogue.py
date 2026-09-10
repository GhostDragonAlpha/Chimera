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
ROW_RE = re.compile(r'^\|\s*([LBH][A-Za-z]?\d+[A-Za-z0-9-]*)\s*\|')
TRACKED = ('THE LINES', 'THE BACKLOG', 'NEXT HARD QUEUE')


def _sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def payload_digest(payload):
    return _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def parse_master_rows(text):
    """Return ({id: row record}, {'unresolved': [...], 'outside': n}).

    Repeated rows of the same ID each become one observation; nothing is
    deduplicated. Rows inside the scoped sections that do not carry a task ID
    are reported as unresolved mappings. Rows outside the scoped sections are
    only counted (they are status tables, not task rows) - still not silent.
    """
    rows = {}
    unresolved = []
    outside = 0
    section = None

    def separator(cells):
        return bool(cells) and all(re.fullmatch(r':?-{3,}:?', c) for c in cells)

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith('#'):
            section = line
            continue
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if separator(cells) or (cells and cells[0] in ('#', 'ID', 'id', 'Id')):
            continue  # table structure, not a task row
        tracked = any(name in (section or '') for name in TRACKED)
        m = ROW_RE.match(line)
        if not m:
            if tracked:
                unresolved.append({'line': lineno, 'section': section,
                                   'row': line[:200]})
            else:
                outside += 1
            continue
        ident = m.group(1)
        columns = cells
        rows.setdefault(ident, {'plane': 'master_row', 'id': ident,
                                'observations': []})['observations'].append(
            {'section': section, 'line': lineno, 'columns': columns,
             'content_sha256': _sha(json.dumps(columns, ensure_ascii=False))})
    return rows, {'unresolved': unresolved, 'outside': outside}


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
                         'pipe_rows_outside_scoped_sections': extra['outside']}}


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
        obs = r.get('observations')
        if not isinstance(obs, list) or not obs:
            errors.append('malformed_master_row:' + r['id'])
            continue
        for o in obs:
            if (not isinstance(o, dict) or not isinstance(o.get('columns'), list)
                    or len(o['columns']) < 3 or type(o.get('line')) is not int):
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
