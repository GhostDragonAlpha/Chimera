"""terms — the terminology index, queryable.

WHY THIS EXISTS (operator, 2026-07-23): the vocabulary became load-bearing. This project
uses real terms from genetics, physics and cell biology LITERALLY -- an agent that reads
"recombination" as a figure of speech writes the wrong code, and a human reading "membrane"
as a synonym for "boundary object" misses why it is the primitive.

WHY IT IS QUERYABLE AND NOT JUST A DOC: a document an agent must read in full is a document
an agent skips. `python -m core.terms membrane` costs one line of context; reading
TERMINOLOGY.md costs several thousand tokens. The doc is the source of truth for a human;
this is the index a machine reaches into.

    python -m core.terms membrane          # one definition
    python -m core.terms --search band     # every term mentioning a word
    python -m core.terms --list            # every term, by section
    python -m core.terms --rebuild         # regenerate docs/terminology.json
    python -m core.terms --graph           # push terms into the DNA graph as nodes

THE PARSE IS DELIBERATELY DUMB. Terms are `**bold**` at the start of a line; sections are
`## N. NAME`. If a definition does not survive that rule it does not belong in the index,
which keeps the doc from drifting into prose that only a human can use.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/TERMINOLOGY.md'
INDEX = ROOT / 'docs/terminology.json'

_SECTION = re.compile(r'^##\s+(?:(\d+)\.\s*)?(.+?)\s*$')
_TERM = re.compile(r'^\*\*(.+?)\*\*\s*(?:\*\((.+?)\)\*\s*)?(?:—|--)\s*(.*)$')


def parse(doc: Path = DOC) -> dict:
    """Parse the markdown into {term: {...}}. The doc is the source of truth."""
    if not doc.exists():
        raise FileNotFoundError(f'no terminology at {doc}')

    terms: dict = {}
    section = 'preamble'
    current = None

    for line in doc.read_text(encoding='utf-8').splitlines():
        m = _SECTION.match(line)
        if m:
            section = m.group(2).strip()
            current = None
            continue

        m = _TERM.match(line)
        if m:
            name, alias, body = m.group(1).strip(), m.group(2), m.group(3).strip()
            key = name.lower()
            terms[key] = {
                'term': name,
                'aliases': [a.strip(' `*') for a in (alias or '').split('/') if a.strip()],
                'section': section,
                'definition': body,
                'code': [],
            }
            current = key
            continue

        if current is None:
            continue
        s = line.strip()
        if not s:
            continue
        if s.startswith('→') or s.startswith('->'):
            terms[current]['code'].append(s.lstrip('→->').strip())
        elif not s.startswith('#') and not s.startswith('>') and not s.startswith('|'):
            terms[current]['definition'] += ' ' + s

    for t in terms.values():
        t['definition'] = re.sub(r'\s+', ' ', t['definition']).strip()
    return terms


def rebuild() -> dict:
    terms = parse()
    INDEX.write_text(json.dumps(
        {'source': 'docs/TERMINOLOGY.md',
         'note': 'GENERATED. Edit the markdown, then run: python -m core.terms --rebuild',
         'count': len(terms), 'terms': terms}, indent=2), encoding='utf-8')
    return terms


def load() -> dict:
    """Terms from the JSON index, falling back to a live parse.

    Falls back rather than failing, because a stale index is worse than a slow one: an
    agent that gets a confidently wrong definition is in a worse position than one that
    waits 3 ms for the markdown to be re-read.
    """
    if INDEX.exists():
        try:
            return json.loads(INDEX.read_text(encoding='utf-8'))['terms']
        except Exception:
            pass
    return parse()


def get(word: str) -> dict | None:
    """One term. Matches the name, an alias, or a unique prefix."""
    terms = load()
    w = word.lower().strip()
    if w in terms:
        return terms[w]
    for t in terms.values():
        if w in [a.lower() for a in t['aliases']]:
            return t
    hits = [t for k, t in terms.items() if k.startswith(w)]
    if len(hits) == 1:
        return hits[0]
    return None


def search(word: str) -> list:
    """Every term whose name or definition mentions a word."""
    w = word.lower().strip()
    return [t for t in load().values()
            if w in t['term'].lower() or w in t['definition'].lower()]


GRAPH_DB = ROOT / 'docs/world/terminology.db'

# Cross-references: a definition that says **membrane** is CITING the term membrane. Those
# become edges, which is the whole reason to put this in a graph rather than a dictionary --
# a dictionary answers "what does X mean", a graph answers "what does X rest on".
_XREF = re.compile(r'\*\*(.+?)\*\*')

# Names that are also ordinary English. A match on these is not evidence of a citation.
_AMBIGUOUS = {'measure', 'domain', 'section', 'feature', 'mutation', 'pinned', 'margin',
              'objective', 'genome', 'splat', 'aspect', 'skin', 'serial number'}


def to_graph(db: Path = GRAPH_DB) -> dict:
    """Push terms into world_store as nodes, with an edge per cross-reference.

    ITS OWN DATABASE, deliberately. The DNA graph's `graphify_mutate` is a fixed enum of
    EVENT types (compilation, verification, discovery) with no slot for a definition, and
    filing 74 terms under `technical_discovery` would poison the query that means "what did
    we actually discover". A separate store keeps the one-writer rule intact -- the same
    discipline THE_ORDER.md finding 4 exists to enforce.
    """
    from core import world_store as ws

    terms = load()
    db.parent.mkdir(parents=True, exist_ok=True)
    con = ws.connect(str(db))

    rows = []
    for key, t in terms.items():
        rows.append((f'term:{key}', 'terminology', t['term'], None, None, None, {
            'definition': t['definition'],
            'section': t['section'],
            'code': t['code'],
            'aliases': t['aliases'],
            'source': 'docs/TERMINOLOGY.md',
        }))
    ws.add_nodes(con, rows)

    edges = []
    for key, t in terms.items():
        text = t['definition'].lower()
        refs = {m.strip().lower() for m in _XREF.findall(t['definition'])}   # bolded
        # ...plus plain-text mentions, which is where most real citations live: a definition
        # that explains something "in terms of the membrane" is resting on that term whether
        # or not it bolded it. Guarded, because a graph full of false edges is worse than a
        # sparse one -- short and ambiguous names (form, band, cell, gate, verb) match far
        # too much ordinary prose to be evidence of a citation.
        for other in terms:
            if other == key or len(other) < 6 or other in _AMBIGUOUS:
                continue
            if re.search(r'\b' + re.escape(other) + r'\b', text):
                refs.add(other)
        for ref in refs:
            if ref in terms and ref != key:
                edges.append((f'term:{key}', f'term:{ref}', 'references', None))
    if edges:
        ws.add_edges(con, edges)

    con.close()
    return {'nodes': len(rows), 'edges': len(edges), 'db': str(db)}


def _fmt(t: dict, width: int = 88) -> str:
    import textwrap
    head = t['term']
    if t['aliases']:
        head += '  (' + ', '.join(t['aliases']) + ')'
    out = [f'\n{head}', f'  [{t["section"]}]']
    out += ['  ' + l for l in textwrap.wrap(t['definition'], width - 2)]
    for c in t['code']:
        out.append(f'  -> {c}')
    return '\n'.join(out)


def _main() -> int:
    import argparse
    import sys

    # The doc is written in UTF-8 (arrows, em-dashes) and the Windows console defaults to
    # cp1252, which raises rather than degrading. Reconfigure instead of stripping the
    # characters from the source: the markdown is for humans and should stay readable.
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description='the terminology index')
    ap.add_argument('word', nargs='?', help='term to look up')
    ap.add_argument('--search', help='find every term mentioning this')
    ap.add_argument('--list', action='store_true', help='every term, by section')
    ap.add_argument('--rebuild', action='store_true', help='regenerate the JSON index')
    ap.add_argument('--graph', action='store_true', help='push terms into the DNA graph')
    a = ap.parse_args()

    if a.rebuild:
        t = rebuild()
        print(f'{len(t)} terms -> {INDEX}')
        return 0

    if a.graph:
        r = to_graph()
        print(f"{r['nodes']} terminology nodes + {r['edges']} reference edges -> {r['db']}")
        return 0

    if a.list:
        terms = load()
        by: dict = {}
        for t in terms.values():
            by.setdefault(t['section'], []).append(t['term'])
        for sec, names in by.items():
            print(f'\n{sec}')
            for n in names:
                print(f'    {n}')
        print(f'\n{len(terms)} terms.  python -m core.terms <word>')
        return 0

    if a.search:
        hits = search(a.search)
        if not hits:
            print(f'nothing mentions {a.search!r}')
            return 1
        print(f'{len(hits)} term(s) mention {a.search!r}:')
        for t in hits:
            print(_fmt(t))
        return 0

    if not a.word:
        ap.print_help()
        return 1

    t = get(a.word)
    if t is None:
        hits = search(a.word)
        if hits:
            print(f'no term {a.word!r}. Mentioned by: ' + ', '.join(h['term'] for h in hits[:8]))
        else:
            print(f'no term {a.word!r}. Try: python -m core.terms --list')
        return 1
    print(_fmt(t))
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
