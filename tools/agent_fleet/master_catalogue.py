"""Canonical master catalogue: provenance-preserving import payload builder.

Projects the ENTIRE canonical catalogue - every card of
docs/roadmap/holodeck_tasks.json and every L*/B*/H* task row of
docs/THE_MASTER_LIST.md - into validated records for the controller's
catalogue plane. The catalogue is discoverable planning data only: it never
creates, claims, admits or mutates live tasks/claims/resources/slots.

No silent omissions: every parsed task row is kept (repeated observations of
the same ID accumulate as a list - history is preserved, never overwritten),
pipe rows that do not resolve to a task ID are counted in coverage.unresolved
instead of being dropped, and the source document is partitioned EXHAUSTIVELY:
every line of the Master list lands in exactly one coverage.line_partition
class, with plain prose and unkeyed requirements retained verbatim (text +
sha256) so an unknown sentence or continuation line cannot vanish (lead
gen-5 finding: Master line 1825, a B7b requirement continuation, was dropped).

The payload carries a source_manifest per source (path, sha256, byte/line
counts, best-effort git commit) computed from the retained source text.
validate_payload RECOMPUTES those hashes from the submitted records, so a
supplied hash can never masquerade as proof against live files; whether the
manifest matches the CURRENT canonical sources is a separate admission gate
(coverage.version_pin reports the pinned revision explicitly).
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
      extras['unkeyed_requirements']  unkeyed requirement records (kept,
                                 classified, never dropped)
    Every line is additionally assigned to exactly one partition class in
    extras['line_partition'] (exhaustive no-silent-omission accounting; the
    classes sum to the line count of the source).
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
    unkeyed = []
    partition = {}  # lineno -> partition class (exhaustive over all lines)
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
            partition[lineno] = 'header'
            continue
        if line.startswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if separator(cells) or lineno in header_lines or (
                    cells and cells[0].strip('` ').casefold() in HEADER_CELLS):
                structural += 1  # table structure, not a task row
                partition[lineno] = 'structural'
                continue
            ident = _cell_id(cells[0]) if cells else None
            if ident is None:
                refs = campaign_refs(cells)
                if refs:
                    # Assignment-style row without a leading task ID: keep
                    # every campaign reference with full provenance.
                    partition[lineno] = 'cell_reference'
                    for ref in refs:
                        record(ref, {'kind': 'cell_reference', 'section': section,
                                     'line': lineno, 'columns': cells,
                                     'content_sha256': _sha(json.dumps(
                                         cells, ensure_ascii=False))})
                else:
                    unresolved.append({'line': lineno, 'section': section,
                                       'row': line[:200]})
                    partition[lineno] = 'unresolved'
                continue
            record(ident, {'kind': 'table_row', 'section': section,
                           'line': lineno, 'columns': cells,
                           'content_sha256': _sha(json.dumps(
                               cells, ensure_ascii=False))})
            partition[lineno] = 'task_row'
            continue
        # Every remaining line - blank, prose, anything - is exhaustively
        # partitioned. Prose is retained VERBATIM (text + sha256) in the
        # partition so no sentence or continuation line can silently vanish
        # (the lead's gen-5 falsifier: Master line 1825 was dropped).
        partition[lineno] = 'blank' if not line else 'prose'
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
            # Unkeyed REQUIREMENT prose (the lead's gen-4 finding): a bullet
            # stating a requirement, result or gate with no task ID key is
            # still content - keep it with section/line provenance, distinct
            # from prose that mentions a keyed ID. The Research Annex's
            # "Falsifier for us: ..." lines land here, as does any plain
            # requirement sentence elsewhere in the document.
            stripped = re.sub(r'`[^`]*`', '', line)  # ID-free view
            if re.match(r'^[-*]\s+', stripped) and len(stripped) > 40:
                unkeyed.append({'kind': 'unkeyed_requirement',
                                'section': section, 'line': lineno,
                                'text': line[:200],
                                'content_sha256': _sha(line)})
            elif re.search(r'\b(falsifier|must|require[ds]?|gate|falsif\w*)\b',
                           stripped, re.IGNORECASE) and len(stripped) > 40:
                unkeyed.append({'kind': 'unkeyed_requirement',
                                'section': section, 'line': lineno,
                                'text': line[:200],
                                'content_sha256': _sha(line)})
    extras = {'unresolved': unresolved, 'structural_rows': structural,
              'prose_mentions': prose_mentions,
              'campaign_prose_refs': campaign_prose,
              'unkeyed_requirements': unkeyed,
              'line_partition': partition}
    return rows, extras


def _git_commit(path):
    """Best-effort HEAD of the tree containing `path` (None outside a repo)."""
    import subprocess
    try:
        out = subprocess.run(['git', '-C', str(Path(path).parent), 'rev-parse',
                              'HEAD'], capture_output=True, text=True,
                             timeout=10)
        if out.returncode == 0:
            return out.stdout.strip() or None
    except (OSError, ValueError):
        pass
    return None


PARTITION_CLASSES = ('header', 'structural', 'task_row', 'cell_reference',
                     'unresolved', 'prose', 'blank')


def source_manifest(text, path, git_commit=None, retained=False):
    """Manifest computed FROM the retained source text (never supplied).

    The retained form is the LF-normalized reconstruction of the source
    ('\\n'.join(text.splitlines())) - the same normalization
    validate_payload applies to the submitted line partition, so hashes are
    comparable on both sides regardless of the file's trailing newline.
    """
    canonical = '\n'.join(text.splitlines())
    return {'path': str(path), 'sha256': _sha(canonical),
            'bytes': len(canonical.encode('utf-8')),
            'lines': len(text.splitlines()),
            'git_commit': git_commit, 'retained': bool(retained)}


def build_records(catalog_path=DEFAULT_CATALOG, master_path=DEFAULT_MASTER,
                  catalog_text=None, master_text=None):
    """Build the import payload from the canonical sources (read-only).

    Coverage counters are computed from the emitted records and the payload
    is VERSION-PINNED: source_versions carries path, sha256 and (best-effort)
    git HEAD for each source, so coverage is always relative to an exact
    source revision - never a universal claim.
    """
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
    # Exhaustive no-silent-omission accounting: EVERY line of the Master is
    # retained verbatim in exactly one partition class, so continuations and
    # unknown sentences cannot vanish (lead gen-5 falsifier: line 1825).
    classes = extra.pop('line_partition')
    master_lines = master_text.splitlines()
    partition = {n: {'class': cls, 'text': master_lines[n - 1],
                     'sha256': _sha(master_lines[n - 1])}
                 for n, cls in classes.items()}
    master_manifest = source_manifest(master_text, master_path,
                                      _git_commit(master_path), retained=True)
    catalog_manifest = source_manifest(catalog_text, catalog_path,
                                       _git_commit(catalog_path), retained=False)
    return {'schema': SCHEMA, 'cards': cards,
            'master_rows': [rows[k] for k in sorted(rows)],
            # source_versions (gen<=4) carried submitter-supplied hashes that
            # validate_payload could only trust - removed per the lead's
            # gen-5 finding. source_manifest is recomputed from the retained
            # source at validation time instead.
            'source_manifest': {'master': master_manifest,
                                'catalog': catalog_manifest},
            'coverage': {'cards': len(cards),
                         'domains': len({c['domain'] for c in cards
                                         if isinstance(c.get('domain'), str)}),
                         'master_row_ids': len(rows),
                         'master_row_observations': sum(
                             len(r['observations']) for r in rows.values()),
                         # Scalar counters carry COUNTS; the detailed records
                         # travel alongside in *_records fields so the
                         # validator can recompute every count from them.
                         'unresolved': len(extra['unresolved']),
                         'unresolved_records': extra['unresolved'],
                         'structural_rows': sum(
                             1 for e in partition.values()
                             if e['class'] == 'structural'),
                         'prose_mentions': len(extra['prose_mentions']),
                         'prose_mention_records': extra['prose_mentions'],
                         'campaign_prose_refs': len(extra['campaign_prose_refs']),
                         'campaign_prose_records': extra['campaign_prose_refs'],
                         'unkeyed_requirements': len(extra['unkeyed_requirements']),
                         'unkeyed_requirement_records': extra['unkeyed_requirements'],
                         'line_partition': partition,
                         'version_pin': {'master_sha256': master_manifest['sha256'],
                                         'catalog_sha256': catalog_manifest['sha256']}}}


def validate_payload(payload):
    """Controller-side validation. Returns a list of named errors (empty=ok).

    Nothing submitted is trusted except the records themselves: every
    coverage counter and every manifest hash is RECOMPUTED here from the
    submitted records (lead gen-4/gen-5 findings: forged counters and
    submitter-supplied source hashes were accepted). The manifest is required
    to be consistent with the retained source records; whether it matches the
    CURRENT canonical files is deliberately NOT decided here - that is a
    separate admission gate (coverage.version_pin surfaces the pinned sha).
    """
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
    # A supplied source_versions block is a gen<=4 artifact the validator can
    # only trust on faith - refuse it outright (lead gen-5 falsifier 1: a
    # removed/altered source_versions was accepted).
    if 'source_versions' in payload:
        return ['supplied_source_versions_refused']
    manifest = payload.get('source_manifest')
    if (not isinstance(manifest, dict)
            or not isinstance(manifest.get('master'), dict)):
        return ['missing_source_manifest']
    coverage = payload['coverage']
    partition = coverage.get('line_partition')
    if not isinstance(partition, dict):
        return ['missing_line_partition']
    # Recompute the master manifest from the retained verbatim partition.
    # The partition must be EXACTLY exhaustive over the manifest's claimed
    # line count; an empty partition is only honest when the payload carries
    # no master-plane records at all (cards-only imports - which admission
    # then rejects as not matching the current canonical Master).
    # JSON transport (HTTP body, state persistence) stringifies dict keys,
    # so accept string line numbers and coerce them - then demand exact
    # integer exhaustiveness.
    norm = {}
    for key, entry in partition.items():
        try:
            n = int(key)
        except (TypeError, ValueError):
            return ['malformed_line_partition']
        if n in norm:
            return ['malformed_line_partition']
        norm[n] = entry
    partition_lines = sorted(norm)
    claimed = manifest['master'].get('lines')
    if not isinstance(claimed, int) or claimed < 0:
        return ['source_manifest_consistency:lines']
    if partition_lines != list(range(1, claimed + 1)):
        return ['line_partition_not_exhaustive']
    if claimed == 0 and (rows or coverage.get('unresolved_records')
                         or coverage.get('unkeyed_requirement_records')
                         or coverage.get('prose_mention_records')
                         or coverage.get('campaign_prose_records')):
        return ['line_partition_not_exhaustive']
    rebuilt = []
    for n in partition_lines:
        entry = norm[n]
        if (not isinstance(entry, dict)
                or entry.get('class') not in PARTITION_CLASSES
                or not isinstance(entry.get('text'), str)
                or not re.fullmatch('[0-9a-f]{64}', str(entry.get('sha256', '')))
                or entry['sha256'] != _sha(entry['text'])):
            return ['malformed_line_partition']
        rebuilt.append(entry['text'])
    retained_text = '\n'.join(rebuilt)
    if manifest['master'].get('sha256') != _sha(retained_text):
        return ['source_manifest_hash_mismatch']
    for field in ('bytes', 'lines'):
        want = {'bytes': len(retained_text.encode('utf-8')),
                'lines': len(rebuilt)}[field]
        if manifest['master'].get(field) != want:
            return ['source_manifest_consistency:' + field]
    if manifest['master'].get('retained') is not True:
        return ['source_manifest_master_not_retained']
    # Coverage counters are RECOMPUTED from the records, never trusted from
    # the submitter (lead gen-4 finding: forged coverage counts were accepted;
    # gen-5 falsifier 2: coverage.domains=999 was accepted).
    partition = norm
    unres_records = coverage.get('unresolved_records')
    if not isinstance(unres_records, list):
        return ['missing_unresolved_records']
    for u in unres_records:
        if (not isinstance(u, dict) or type(u.get('line')) is not int
                or not isinstance(u.get('row'), str)):
            return ['malformed_coverage_unresolved']
    computed = {
        'cards': len([c for c in cards if isinstance(c, dict)]),
        'domains': len({c['domain'] for c in cards
                        if isinstance(c, dict)
                        and isinstance(c.get('domain'), str)}),
        'master_row_ids': len([r for r in rows if isinstance(r, dict)
                               and isinstance(r.get('id'), str)]),
        'master_row_observations': sum(
            len(r.get('observations') or []) for r in rows
            if isinstance(r, dict)),
        'unresolved': len(unres_records),
        'structural_rows': sum(
            1 for e in partition.values()
            if isinstance(e, dict) and e.get('class') == 'structural'),
        'prose_mentions': len([m for m in
                               coverage.get('prose_mention_records') or []
                               if isinstance(m, dict)]),
        'campaign_prose_refs': len([m for m in
                                    coverage.get('campaign_prose_records') or []
                                    if isinstance(m, dict)]),
        'unkeyed_requirements': len([u for u in
                                     coverage.get('unkeyed_requirement_records')
                                     or [] if isinstance(u, dict)]),
    }
    for key, want in computed.items():
        if coverage.get(key) != want:
            return ['coverage_mismatch:' + key]
    # version_pin must carry the pinned source digests and agree with the
    # recomputed manifest - historical source is distinguishable from current
    # canonical source only by stating the pin explicitly.
    pin = coverage.get('version_pin')
    if (not isinstance(pin, dict)
            or pin.get('master_sha256') != manifest['master'].get('sha256')
            or not re.fullmatch('[0-9a-f]{64}', str(pin.get('master_sha256', '')))):
        return ['missing_version_pin']
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
