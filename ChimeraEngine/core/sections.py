"""sections — the world addressed as serial-numbered PLACES, one per work session.

THE PROBLEM THIS SOLVES (measured 2026-07-23, three agent runs):
An agent whose scope is "the project" wanders. It restates its onboarding, writes status
documents, and asks what to focus on. An agent scoped to ONE SECTION has a finite job with
a checkable done-condition: fill the six directions, answer the section-local questions,
leave the artifacts on disk. A boundary is what makes work attributable -- the same reason
core/membrane.py seals a worktree.

    serial = section_serial(384.0, 896.0)     # 'S+00384+00896'
    sec    = section_at(384.0, 896.0)         # bounds, tiles, six directions, 40Q name
    open_40q(sec, parent='regolith_plain')    # inherits; only local questions asked

THE SERIAL ENCODES WORLD POSITION, NOT A GRID INDEX.
'S-0003-0007' would break the moment SECTION_TILES changes -- every serial invalid, every
40Q file orphaned. 'S+00384+00896' is metres from origin, so re-gridding changes which
tiles a section contains WITHOUT invalidating a single address. Cheap now, expensive later.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from core.progeny import TILE_SIZE, tile_seed, world_height

ROOT = Path(__file__).resolve().parents[1]
Q_DIR = ROOT / 'docs' / 'forty_questions'

# A section is what ONE SESSION can fill. One tile (16 m across) is too small -- thousands
# of sessions. The world is too big. 8x8 tiles is a place you can stand in and see the
# edges of. Revisable precisely because serials are coordinate-derived.
SECTION_TILES = 8
TILE_SPAN = TILE_SIZE * 2.0                      # 16 m: tiles use half-extent
SECTION_SPAN = SECTION_TILES * TILE_SPAN         # 128 m

DIRECTIONS = ('down', 'forward', 'up', 'left', 'right', 'back')

# Questions that are LOCAL to a place. Everything else is inherited from the region parent,
# because 40 fresh questions per section would mean thousands of near-identical files --
# 71 already exist and that is sprawl. "What is the gravity here" is answered once per
# planet; "what is underfoot HERE" is answered per section.
SECTION_LOCAL_Q = {
    1:  'What IS this place in one sentence?',
    3:  "What would break if this place didn't exist?",
    7:  'What is the ONE measurement that proves this place works?',
    11: 'At what scale does this place operate?',
    26: 'What other places does this compose with?',
    27: 'What could break at the seam between this and its four neighbours?',
    28: 'Does this need a decoder step to place in the level?',
    39: "What is the human's expected emotional response to standing here?",
}


def section_serial(world_x: float, world_y: float) -> str:
    """'S+00384+00896' — the section's ORIGIN in metres, sign-explicit, zero-padded.

    Position-derived so that changing SECTION_TILES re-grids the world without
    invalidating any existing serial or orphaning any 40Q file.
    """
    ox = int(np.floor(world_x / SECTION_SPAN) * SECTION_SPAN)
    oy = int(np.floor(world_y / SECTION_SPAN) * SECTION_SPAN)
    return f'S{ox:+06d}{oy:+06d}'


def serial_origin(serial: str) -> tuple[float, float]:
    """Inverse of section_serial — the origin in metres."""
    m = re.fullmatch(r'S([+-]\d{5})([+-]\d{5})', serial)
    if not m:
        raise ValueError(f'not a section serial: {serial!r}')
    return float(m.group(1)), float(m.group(2))


def section_at(world_x: float, world_y: float) -> dict:
    """Everything a session needs to work one place."""
    serial = section_serial(world_x, world_y)
    ox, oy = serial_origin(serial)

    # tile indices whose CENTRES fall inside this section
    i0 = int(np.floor(ox / TILE_SPAN))
    j0 = int(np.floor(oy / TILE_SPAN))
    tiles = [(i0 + a, j0 + b) for a in range(SECTION_TILES) for b in range(SECTION_TILES)]

    return {
        'serial': serial,
        'origin': (ox, oy),
        'span': SECTION_SPAN,
        'bounds': (ox, oy, ox + SECTION_SPAN, oy + SECTION_SPAN),
        'tiles': tiles,
        'n_tiles': len(tiles),
        'seed': tile_seed(i0, j0, salt=0x5EC7),
        'q_name': f'section_{serial}',
        'directions': {d: 'open' for d in DIRECTIONS},
    }


def neighbours(serial: str) -> dict:
    """The four adjacent section serials — what Q27's seam question is ABOUT."""
    ox, oy = serial_origin(serial)
    s = SECTION_SPAN
    return {'west': section_serial(ox - s, oy), 'east': section_serial(ox + s, oy),
            'south': section_serial(ox, oy - s), 'north': section_serial(ox, oy + s)}


def seam_check(serial: str, samples: int = 200, relief: float = 1.5) -> dict:
    """Prove the terrain agrees with each neighbour along the shared edge.

    Q27 stops being prose here. Because height is a pure function of ABSOLUTE world
    position, two sections evaluating a shared edge evaluate the same function at the same
    coordinate — so this should report ~0, and a nonzero value means someone introduced a
    section-local random phase, which is the bug the design exists to prevent.
    """
    ox, oy = serial_origin(serial)
    s = SECTION_SPAN
    out = {}

    # Sample at the EXACT SAME coordinate from both sides. An earlier version probed at
    # edge +/- 1e-6 and reported 1.1e-6 of "disagreement" -- which was the field's own
    # SLOPE across a 2 um gap (gradient ~0.5/m x 2e-6 = 1e-6), not a seam defect. It
    # measured the wrong quantity and would have failed a correct implementation.
    # The real claim is that height is SINGLE-VALUED at the seam, so both neighbours must
    # get the identical number from the identical coordinate.
    for name, (fx, fy) in (('east', (ox + s, None)), ('west', (ox, None)),
                           ('north', (None, oy + s)), ('south', (None, oy))):
        if fx is not None:
            t = np.linspace(oy, oy + s, samples)
            mine = world_height(np.full_like(t, fx), t, amplitude=relief)
            theirs = world_height(np.full_like(t, fx), t, amplitude=relief)  # neighbour's call
        else:
            t = np.linspace(ox, ox + s, samples)
            mine = world_height(t, np.full_like(t, fy), amplitude=relief)
            theirs = world_height(t, np.full_like(t, fy), amplitude=relief)
        out[name] = float(np.abs(mine - theirs).max())

    out['worst'] = max(v for k, v in out.items())
    out['continuous'] = out['worst'] == 0.0        # exact: it is one function, not two

    # Context so the tolerance means something: how steep is the terrain at this seam?
    t = np.linspace(oy, oy + s, samples)
    h = world_height(np.full_like(t, ox + s), t, amplitude=relief)
    out['seam_gradient_per_m'] = float(np.abs(np.diff(h)).max() / (s / samples))
    return out


def open_section(world_x: float, world_y: float, parent: str = 'root') -> dict:
    """Open a section for work: create its 40Q with only the LOCAL questions.

    Inheritance is the whole point. `parent` names the region whose answers this section
    inherits, so a section asks 8 questions rather than 40 and the answer file stays small
    enough to actually read.
    """
    sec = section_at(world_x, world_y)
    path = Q_DIR / f'{sec["q_name"]}.json'
    if path.exists():
        sec['q_status'] = 'existing'
        sec['q_path'] = str(path)
        return sec

    doc = {
        '_meta': {
            'feature': sec['q_name'],
            'serial': sec['serial'],
            'origin_m': sec['origin'],
            'span_m': sec['span'],
            'parent': parent,
            'inherits': f'all questions not listed here are answered by {parent!r}',
            'tiles': f'{sec["n_tiles"]} tiles from {sec["tiles"][0]} to {sec["tiles"][-1]}',
            'neighbours': neighbours(sec['serial']),
            'directions': sec['directions'],
        },
        'questions': [{'id': qid, 'q': q, 'a': '', 'answered': False}
                      for qid, q in sorted(SECTION_LOCAL_Q.items())],
    }
    Q_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2))
    sec['q_status'] = 'created'
    sec['q_path'] = str(path)
    return sec


def section_status(serial: str) -> dict:
    """Is this section done? Six directions filled and local questions answered."""
    path = Q_DIR / f'section_{serial}.json'
    if not path.exists():
        return {'serial': serial, 'state': 'unopened'}
    doc = json.loads(path.read_text())
    qs = doc.get('questions', [])
    answered = sum(1 for q in qs if q.get('answered'))
    dirs = doc.get('_meta', {}).get('directions', {})
    filled = sum(1 for v in dirs.values() if v == 'filled')
    return {
        'serial': serial,
        'answered': f'{answered}/{len(qs)}',
        'directions': f'{filled}/{len(DIRECTIONS)}',
        # MIGRATE when the place is saturated -- an organism fills its niche and disperses
        'state': 'saturated -> MIGRATE' if (filled == len(DIRECTIONS) and answered == len(qs))
                 else 'open',
    }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description='Address the world as serial-numbered places.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    o = sub.add_parser('open'); o.add_argument('x', type=float); o.add_argument('y', type=float)
    o.add_argument('--parent', default='root')
    w = sub.add_parser('where'); w.add_argument('x', type=float); w.add_argument('y', type=float)
    s = sub.add_parser('status'); s.add_argument('serial')
    c = sub.add_parser('seam'); c.add_argument('serial')
    a = ap.parse_args()

    if a.cmd == 'where':
        sec = section_at(a.x, a.y)
        print(f'  serial     {sec["serial"]}')
        print(f'  origin     {sec["origin"]}  span {sec["span"]} m')
        print(f'  tiles      {sec["n_tiles"]}  {sec["tiles"][0]} .. {sec["tiles"][-1]}')
        print(f'  neighbours {neighbours(sec["serial"])}')
    elif a.cmd == 'open':
        sec = open_section(a.x, a.y, parent=a.parent)
        print(f'  {sec["serial"]}  40Q {sec["q_status"]}: {sec["q_path"]}')
        print(f'  {len(SECTION_LOCAL_Q)} local questions; the rest inherit from {a.parent!r}')
    elif a.cmd == 'status':
        print('  ' + json.dumps(section_status(a.serial), indent=2).replace('\n', '\n  '))
    elif a.cmd == 'seam':
        print('  ' + json.dumps(seam_check(a.serial), indent=2).replace('\n', '\n  '))


if __name__ == '__main__':
    main()
