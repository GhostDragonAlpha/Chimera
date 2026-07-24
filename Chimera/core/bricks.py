"""bricks — a genome becomes a Lego brick, and an open stud gets filled.

THE GAP THIS CLOSES. Everything existed except the wire between them:

    work_queue()  said WHERE the world is unfinished   (an unfilled port)
    the genomes   said WHAT matter is available        (recovered + trained)
    the trainer   said WHICH candidate is feasible     (physics, ~30k evals/sec)
    ... and nothing turned an open stud into something attached to it.

So the loop stopped at "here is a to-do list" and a human had to build each item. That
is the labour this project exists to replace.

WHAT THIS DOES NOT DO, deliberately: it does not decide which candidate is GOOD. It
returns every candidate that is physically admissible, ranked by measurable facts, and
stops. NO REFERENCE, NO VERDICT -- taste is the operator's, and `preference_select`
is where it enters. The multiplier is not that the machine chooses; it is that the
operator chooses from eight measured options instead of authoring one from nothing.

    open = cell.open_ports()
    cands = propose(cell, 'down', n=8)      # eight admissible fillings, measured
    place(cell, 'down', cands[0])           # mate the chosen one; the stud is now filled
"""
from __future__ import annotations

import numpy as np

from core.membranes import Membrane, PORT_KINDS

# The library is read once. propose() and brick() each re-read two JSON files per call,
# which is 5.4 ms of file I/O for work that is pure arithmetic -- and a section is ~4,900
# cells, so it compounds into minutes of doing nothing.
_CACHE: dict = {}


def _library() -> tuple[dict, dict]:
    if 'lib' not in _CACHE:
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        _CACHE['gen'] = json.loads((root / 'docs/matter/recovered_genomes.json').read_text())['genomes']
        _CACHE['lib'] = json.loads((root / 'docs/matter/matter_library.json').read_text())
    return _CACHE['gen'], _CACHE['lib']

# Which genomes may serve which kind of stud. A port is typed by WHAT FLOWS, so this is
# a physical claim, not a category: rock can bear load and take a footprint; it cannot
# conduct a fluid or radiate. Anything absent from a list is not admissible there.
KIND_ROLE = {
    'structural': ('metallic', 'wood', 'measured', 'mineral_dry', 'rock'),
    'substrate':  ('mineral_dry', 'measured', 'rock', 'wood'),
    'gravitational': ('measured', 'mineral_dry', 'metallic', 'rock', 'wood'),
    'energy':     ('emissive',),   # the light family (core/emissive.py) now emits -- lasers,
                                   #   plasma, fire, engine glow. Served by propose()'s energy branch.
    'fluid':      ('liquid',),     # the liquid family (core/fluid.py): water, ocean, lava, mud.
    'atmospheric': ('atmosphere',),  # the medium family (core/atmosphere.py): earth/mars/titan
                                     #   skies, physical scattering. All four port kinds now full.
}


def _family(genome_name: str, lib: dict) -> str:
    mat = lib.get('materials', {}).get(genome_name, {})
    return str(mat.get('family', 'measured'))


def admissible(kind: str, lib: dict, genomes: dict) -> list:
    """Which genomes can legitimately fill a stud of this kind.

    An empty result is a RESULT, not a failure: it means the library cannot yet express
    anything that flows through that interface. That is the vocabulary gap made visible
    rather than papered over with a substitute.
    """
    if kind not in PORT_KINDS:
        raise ValueError(f'unknown port kind {kind!r}')
    ok = KIND_ROLE.get(kind, ())
    return [g for g in genomes if _family(g, lib) in ok or 'measured' in ok]


def brick(genome_name: str, size: float = 0.5, kind: str = 'structural',
          seed: int = 0, form: str = 'measured') -> Membrane:
    """A genome, expressed as a Lego brick: a membrane with physics and a mating stud.

    The brick carries its genome's MEASURED properties, so what attaches to a wall is
    matter with real density and roughness rather than a placeholder that looks right.
    """
    genomes, lib = _library()
    g = genomes[genome_name]
    f = g['features']
    mat = lib.get('materials', {}).get(genome_name, {})

    m = Membrane(genome_name, scale=size, serial=f'B-{genome_name}',
                 skin=max(size * 1e-3, 1e-4))
    m.prop(
        genome=genome_name,
        form=form,
        aniso=round(float(f['aniso']['mean']), 4),
        grain_m=round(float(f['size']['mean']), 6),
        albedo=[round(float(f[c]['mean']), 4) for c in 'RGB'],
        opacity=round(float(f['opacity']['mean']), 4),
        heritable=bool(g.get('n_specimens')),
        composition=[l['type'] for l in mat.get('splat_composition', {}).get('layers', [])],
    )
    # one stud, facing -Z so it mates with a downward-looking face by default
    m.port('mount', kind, at=[0.0, 0.0, size * 0.5], facing=[0.0, 0.0, 1.0], size=size)
    return m


def propose(host: Membrane, port_name: str, n: int = 8, seed: int = 0) -> list:
    """N admissible fillings for one open stud, each measured. Ranked, never chosen.

    Candidates are RECOMBINED from the library rather than picked from it, so what is
    offered includes matter that does not exist yet but could -- which is the point of
    keeping genomes as distributions instead of values.
    """
    from core.progeny import recombine

    p = host.ports.get(port_name)
    if p is None:
        raise KeyError(f'{host.name} has no port {port_name!r}; has {sorted(host.ports)}')

    # ENERGY flows light, not matter. It is served by the emissive family, not the material
    # library, because light has no albedo/roughness/metalness to recombine (core/emissive.py).
    if p.kind == 'energy':
        from core import emissive
        return emissive.propose(n=n, seed=seed)

    # FLUID flows liquid: translucent, tinted, pooling. Its own family for the same reason --
    # a liquid is not an opaque material surface (core/fluid.py).
    if p.kind == 'fluid':
        from core import fluid
        return fluid.propose(n=n, seed=seed)

    # ATMOSPHERIC flows the MEDIUM -- the physical sky, not a placeable blob. Served by the
    # atmosphere family, whose genome is the scattering coefficients (core/atmosphere.py).
    if p.kind == 'atmospheric':
        from core import atmosphere
        return atmosphere.atmosphere_propose(n=n, seed=seed)

    genomes, lib = _library()

    pool = admissible(p.kind, lib, genomes)
    if not pool:
        return []                       # the vocabulary cannot express this. Honest.

    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a, b = (pool[int(rng.integers(len(pool)))] for _ in range(2))
        child = recombine(genomes[a], genomes[b], n=1, seed=seed + i)[0]
        s = child['sampled']
        size = float(np.clip(p.size * (0.25 + 0.5 * s['_scale']), p.size * 0.15, p.size))
        out.append({
            'parents': (a, b),
            'inherited': child['inherited'],
            'size_m': round(size, 4),
            'aniso': round(float(s['aniso']), 4),
            'grain_m': round(float(s['size']), 6),
            'albedo': [round(float(s[c]), 3) for c in 'RGB'],
            'heritable': bool(genomes[a].get('n_specimens') and genomes[b].get('n_specimens')),
            'seed': child['seed'],
        })
    # ranked by MEASURABLE facts only: heritable first (it breeds true), then how well
    # the piece fills the stud it is going into. Never by preference.
    out.sort(key=lambda c: (-int(c['heritable']), -c['size_m'] / max(p.size, 1e-9)))
    return out


def place(host: Membrane, port_name: str, candidate: dict,
          kind: str | None = None) -> Membrane:
    """Mate a chosen candidate onto the stud. After this the port is no longer open."""
    p = host.ports[port_name]
    b = brick(candidate['parents'][0], size=candidate['size_m'],
              kind=kind or p.kind, seed=candidate['seed'])
    b.prop(recombined_from=list(candidate['parents']),
           inherited=candidate['inherited'],
           aniso=candidate['aniso'], albedo=candidate['albedo'])
    b.ports['mount'].facing = -np.asarray(p.facing, dtype=np.float64)
    b.ports['mount'].at = np.asarray(p.facing, dtype=np.float64) * (-candidate['size_m'] * 0.5)
    b.ports['mount'].size = p.size
    host.mate(port_name, b, 'mount')
    return b


def fill_report(host: Membrane) -> dict:
    """Where this membrane stands: filled, open, and whether it is ready to migrate."""
    open_names = [p.name for p in host.open_ports()]
    total = len(host.ports)
    return {
        'address': host.path(),
        'filled': total - len(open_names),
        'open': open_names,
        'state': 'saturated -> MIGRATE' if not open_names else 'open',
    }


def main() -> None:
    from core.membranes import universe, planet, section, cell

    u = universe()
    ground = planet(u, 'earth', origin=(1.496e11, 0, 0), relief=1.5)
    sec = section(ground, 384.0, 896.0)
    c = cell(sec, 24, 56, 0)

    print(f'=== an open stud: {c.path()} ===')
    print('  ' + str(fill_report(c)))

    print('\n=== eight admissible fillings for DOWN, measured and ranked ===')
    cands = propose(c, 'down', n=8)
    for i, x in enumerate(cands):
        h = 'heritable' if x['heritable'] else 'single-specimen'
        print(f"  {i}  {x['parents'][0][:18]:18} x {x['parents'][1][:18]:18} "
              f"size {x['size_m']:.3f}m  aniso {x['aniso']:.3f}  {h}")

    print('\n=== a stud the vocabulary cannot fill is reported, not faked ===')
    for k in ('energy', 'fluid', 'atmospheric'):
        c.port(f'test_{k}', k, at=[0, 0, 0], facing=[0, 0, 1], size=1.0)
        print(f'  {k:12} -> {len(propose(c, f"test_{k}", n=4))} candidates')

    print('\n=== place the chosen one; the stud closes ===')
    place(c, 'down', cands[0])
    r = fill_report(c)
    print(f"  filled {r['filled']}  open {[o for o in r['open'] if not o.startswith('test_')]}")
    for d, m in c.walk():
        if d:
            print('  ' + '  ' * d + f"{m.serial}  {m.properties.get('albedo')}  "
                  f"aniso={m.properties.get('aniso')}")


if __name__ == '__main__':
    main()


# ---------------------------------------------------------------------------
# DRIVING A WHOLE SECTION
#
# A section is 128 m and a cell is 1.83 m, so ~70x70 = 4,900 cells. Filling six studs on
# every one would be wrong, not just slow: a landscape is mostly ground with air above it.
# Occupancy is decided DETERMINISTICALLY from each cell's own coordinate seed, so the same
# section holds the same content forever and neighbouring sections never have to agree
# about anything -- the same property that made the terrain seams work.
# ---------------------------------------------------------------------------


def drive_section(ground, world_x: float, world_y: float,
                  density: float = 0.12, max_per_cell: int = 3,
                  seed: int = 0, verbose: bool = False) -> dict:
    """Fill an entire section. Returns the section membrane and what happened."""
    import time
    from core.membranes import section, cell, HUMAN_CELL
    from core.sections import SECTION_SPAN
    from core.progeny import tile_seed

    t0 = time.time()
    sec = section(ground, world_x, world_y)
    n_side = int(SECTION_SPAN / HUMAN_CELL)
    ox, oy = sec.origin[0], sec.origin[1]

    cells = occupied = placed = 0
    for i in range(n_side):
        for j in range(n_side):
            cells += 1
            gi, gj = int(ox / HUMAN_CELL) + i, int(oy / HUMAN_CELL) + j
            s = tile_seed(gi, gj, salt=seed)
            if (s % 10_000) / 10_000.0 >= density:
                continue                                    # empty ground here
            c = cell(sec, gi, gj, 0)
            occupied += 1
            n_studs = 1 + (s >> 7) % max_per_cell
            for k, port in enumerate([p.name for p in c.open_ports()][:n_studs]):
                cands = propose(c, port, n=3, seed=s + k)
                if cands:
                    place(c, port, cands[0])
                    placed += 1

    dt = time.time() - t0
    return {'section': sec, 'serial': sec.serial, 'cells': cells,
            'occupied': occupied, 'bricks': placed, 'seconds': round(dt, 2),
            'coverage': round(100.0 * occupied / max(cells, 1), 1)}


def to_splats(root, n_splats: int = 60) -> dict:
    """Turn every placed brick in a tree into renderable splats, at its world position."""
    from core.progeny import build_child, compose

    layers = []
    for _, m in root.walk():
        if not m.properties.get('genome'):
            continue
        spec = {'index': 0, 'seed': int(m.properties.get('seed', 0)) or abs(hash(m.serial)) % (1 << 30),
                'spread': 1.0, 'honest': True,
                'sampled': {'size': float(m.properties['grain_m']),
                            'aniso': float(m.properties['aniso']),
                            'R': m.properties['albedo'][0], 'G': m.properties['albedo'][1],
                            'B': m.properties['albedo'][2],
                            'opacity': float(m.properties.get('opacity', 0.9)),
                            '_scale': max(float(m.scale), 0.05), '_yaw': 0.0, '_lean': 0.0}}
        sp = build_child(spec, form=m.properties.get('form', 'measured'), n_splats=n_splats)
        sp['pos'] = sp['pos'] + m.to_world(np.zeros(3))
        layers.append(sp)
    return compose(*layers) if layers else {}
