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

# Which genomes may serve which kind of stud. A port is typed by WHAT FLOWS, so this is
# a physical claim, not a category: rock can bear load and take a footprint; it cannot
# conduct a fluid or radiate. Anything absent from a list is not admissible there.
KIND_ROLE = {
    'structural': ('metallic', 'wood', 'measured', 'mineral_dry', 'rock'),
    'substrate':  ('mineral_dry', 'measured', 'rock', 'wood'),
    'gravitational': ('measured', 'mineral_dry', 'metallic', 'rock', 'wood'),
    'energy':     (),        # nothing in the library emits yet -- an honest empty set
    'fluid':      (),
    'atmospheric': (),
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
          seed: int = 0, form: str = 'clump') -> Membrane:
    """A genome, expressed as a Lego brick: a membrane with physics and a mating stud.

    The brick carries its genome's MEASURED properties, so what attaches to a wall is
    matter with real density and roughness rather than a placeholder that looks right.
    """
    import json
    from pathlib import Path
    from core.progeny import load_genome

    g = load_genome(genome_name)
    f = g['features']
    lib_path = Path(__file__).resolve().parents[1] / 'docs/matter/matter_library.json'
    lib = json.loads(lib_path.read_text()) if lib_path.exists() else {'materials': {}}
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
    import json
    from pathlib import Path
    from core.progeny import load_genome, recombine

    p = host.ports.get(port_name)
    if p is None:
        raise KeyError(f'{host.name} has no port {port_name!r}; has {sorted(host.ports)}')

    root = Path(__file__).resolve().parents[1]
    genomes = json.loads((root / 'docs/matter/recovered_genomes.json').read_text())['genomes']
    lib = json.loads((root / 'docs/matter/matter_library.json').read_text())

    pool = admissible(p.kind, lib, genomes)
    if not pool:
        return []                       # the vocabulary cannot express this. Honest.

    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a, b = (pool[int(rng.integers(len(pool)))] for _ in range(2))
        child = recombine(load_genome(a), load_genome(b), n=1, seed=seed + i)[0]
        s = child['sampled']
        size = float(np.clip(p.size * (0.25 + 0.5 * s['_scale']), p.size * 0.15, p.size))
        out.append({
            'parents': (a, b),
            'inherited': child['inherited'],
            'size_m': round(size, 4),
            'aniso': round(float(s['aniso']), 4),
            'grain_m': round(float(s['size']), 6),
            'albedo': [round(float(s[c]), 3) for c in 'RGB'],
            'heritable': bool(load_genome(a).get('n_specimens')
                              and load_genome(b).get('n_specimens')),
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
