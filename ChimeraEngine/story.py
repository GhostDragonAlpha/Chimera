"""story.py — READ the hierarchy as a story, so it can be WRITTEN like one.

    "You should be able to read the hierarchy the same way a human reads a story. That way you will
     be able to write the hierarchy the way an author writes a story!"   -- the operator, 2026-07-28

The pieces were already here and simply had no voice: `engine_state.json` holds the seed, the
parent/child hierarchy, each term's claim and the rounds of questioning that produced it. A story
nests act -> scene -> beat exactly as this nests membranes; you read it top-down with inherited
context (a depth-first traversal); and it discloses detail only at the level you stand on (LOD of
meaning). A term's SERIAL -- its path from the seed -- IS its compressed story, because each ancestor
is a clause that sets up the next.

    THE PAYOFF IS THE AUDIT. A chronicle says "this, then this." A STORY says each thing CAUSES the
    next. So a non-sequitur is not a stylistic complaint, it is a structural fault: a claim standing
    on nothing, a term introduced and never used (a Chekhov's gun), a conclusion that arrives
    unearned. `audit` reports exactly those, by reading.

Commands:
    python ChimeraEngine/story.py read   [--depth N] [--from TERM]   narrate the hierarchy
    python ChimeraEngine/story.py audit                              find the plot holes
    python ChimeraEngine/story.py path   TERM                        one term's serial, as a sentence
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / 'engine_state.json'

# how each status reads in narrative voice
VOICE = {
    'decided':     ('settled', 'The human decided it; it needs no further proof.'),
    'proven':      ('proven', None),
    'questioning': ('being questioned', 'It is under examination now.'),
    'open':        ('open', 'Nothing has been asked of it yet.'),
}
# the connective that carries a parent into its children
INTO = {
    'proven':      'and out of it come',
    'decided':     'and from it follow',
    'questioning': 'and it opens onto',
    'open':        'and it promises',
}


def load():
    d = json.loads(STATE.read_text())
    return d['seed'], d['hierarchy'], d.get('terms', {}), d.get('current')


def wrap(text, indent, width=94):
    out, line = [], ' ' * indent
    for w in text.split():
        if len(line) + len(w) + 1 > width:
            out.append(line); line = ' ' * indent + w
        else:
            line = (line + ' ' + w) if line.strip() else line + w
    if line.strip():
        out.append(line)
    return '\n'.join(out)


def narrate(node, H, T, depth, maxd, current, first=True):
    """Depth-first, told top-down: each level is a paragraph, its children the next scene."""
    info = H.get(node, {})
    st = info.get('status', 'open')
    term = T.get(node, {})
    claim = term.get('claim')
    label, aside = VOICE.get(st, ('open', None))
    ind = depth * 3
    here = '   <- we are here' if node == current else ''
    print()
    if first and depth == 0:
        print(wrap(f'The story begins with {node} — {label}.{here}', ind))
    else:
        print(wrap(f'{node} — {label}.{here}', ind))
    if claim:
        print(wrap(f'"{claim}"', ind + 3))
    elif aside and st != 'proven':
        print(wrap(aside, ind + 3))
    rounds = term.get('rounds') or []
    if rounds and depth < maxd:
        n = sum(len(r) for r in rounds)
        flat = [v for r in rounds for v in r]
        print(wrap(f'It was questioned in {len(rounds)} rounds, {n} variables: '
                   + ', '.join(flat[:8]) + ('…' if n > 8 else ''), ind + 3))
    kids = info.get('children') or []
    if not kids:
        return
    if depth >= maxd:
        print(wrap(f'({len(kids)} more within: ' + ', '.join(kids) + ')', ind + 3))
        return
    print(wrap(f'{INTO.get(st, "and within it")}: ' + ', '.join(kids) + '.', ind + 3))
    for k in kids:
        narrate(k, H, T, depth + 1, maxd, current, first=False)


def serial(node, H):
    path = [node]
    while H.get(path[-1], {}).get('parent'):
        path.append(H[path[-1]]['parent'])
    return list(reversed(path))


def audit(seed, H, T):
    """A plot hole IS a structural fault. Read for the ones a story would never survive."""
    guns, unearned, orphans, silent = [], [], [], []
    for name, info in H.items():
        st = info.get('status', 'open')
        kids = info.get('children') or []
        term = T.get(name, {})
        if st == 'open' and not kids:
            guns.append(name)                              # introduced, never used or opened
        if st == 'proven' and kids:
            if all(H.get(k, {}).get('status') == 'open' for k in kids):
                unearned.append(name)                      # proven, but everything inside is unexamined
        if st in ('proven', 'decided') and not term.get('claim'):
            silent.append(name)                            # asserted with no claim written down
        p = info.get('parent')
        if p and p not in H:
            orphans.append(name)
    for name in T:
        if name not in H:
            orphans.append(f'{name} (has a claim but no place in the hierarchy)')

    print('\nSTORY AUDIT — reading the hierarchy for the faults a story would not survive')
    print('=' * 92)
    def block(title, why, items):
        print(f'\n  {title}  [{len(items)}]')
        print(wrap(why, 4))
        for i in items[:14]:
            print(f'      - {i}')
        if len(items) > 14:
            print(f'      … and {len(items)-14} more')
    block("CHEKHOV'S GUNS", 'Introduced and never fired: named in the hierarchy, but nothing was '
          'ever asked of them and they open onto nothing. Every one is a promise the story has '
          'not kept.', guns)
    block('UNEARNED CONCLUSIONS', 'Marked proven, yet everything inside them is still open. The '
          'conclusion arrived before its scenes were written.', unearned)
    block('SILENT ASSERTIONS', 'Settled or proven, but no claim is written down — the story states '
          'an outcome without ever saying what it was.', silent)
    block('ORPHANS', 'A parent that does not exist, or a claim with no place in the tree — a scene '
          'with no act to belong to.', orphans)
    total = len(guns) + len(unearned) + len(silent) + len(orphans)
    print(f'\n  {total} structural faults. A hierarchy that reads well is one that derives well.')


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'read'
    seed, H, T, current = load()
    if cmd == 'audit':
        audit(seed, H, T); return 0
    if cmd == 'path':
        node = sys.argv[2]
        p = serial(node, H)
        print('\n  serial : ' + '/'.join(p))
        print('  as a sentence:')
        parts = []
        for i, n in enumerate(p):
            st = H.get(n, {}).get('status', 'open')
            parts.append(f'{n} ({st})')
        print(wrap('Within ' + ', within '.join(parts) + '.', 4))
        claim = T.get(node, {}).get('claim')
        if claim:
            print(wrap(f'And there: "{claim}"', 4))
        return 0
    depth = int(sys.argv[sys.argv.index('--depth') + 1]) if '--depth' in sys.argv else 2
    root = sys.argv[sys.argv.index('--from') + 1] if '--from' in sys.argv else seed
    n_open = sum(1 for v in H.values() if v.get('status') == 'open')
    print(f'\nTHE STORY SO FAR — {len(H)} membranes, {sum(1 for v in H.values() if v.get("status")=="proven")} '
          f'proven, {n_open} still open.   (depth {depth}; --depth to zoom)')
    print('=' * 92)
    narrate(root, H, T, 0, depth, current)
    print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
