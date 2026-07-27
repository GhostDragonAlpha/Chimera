"""grow — the GROW verb: seed -> mature, driven by energy, clocked by density.

The fourth verb, and the one that breaks the mould in the honest way. dig / thrust / balance
are driven by a player's INPUT (the button, the throttle, the trim). GROW is driven by the
FLOW OF ENERGY -- sun, water, time -- not a hand. You do not hold a plant to make it grow; you
supply the conditions and the dial advances itself. That is a real distinction, and the verb
primitive already carries it: a dial is whatever the world computes it from, and here the world
computes it from accumulated energy.

  IT IS A VERB          a membranes.Verb -- two states (seed, mature) + a dial the ENERGY flow
                        drives. seed = nothing, mature = full canopy; the between is derived.
  ITS CLOCK IS DENSITY  the density term appears a fourth time -- dense tissue grows SLOWER,
                        because there is more matter to build per unit volume. A tissue membrane
                        carries its relative density, so tissue.clock_rate() = sqrt(density), and
                        the growth rate goes as energy / clock_rate: light grass shoots up, dense
                        ironwood crawls. Real: balsa is fast and light, oak slow and dense.
  ITS CURVE IS LOGISTIC unlike the linear response of the mechanical verbs, growth is a SIGMOID
                        -- slow establishment, fast expansion, saturation at the canopy the
                        energy can support. dS/dt = r*S*(1-S). Same density term, different
                        dynamic.

The FORM the growth takes -- phyllotaxis, fractal branching -- is the terrarium's L-system
(core/terrarium.py); this verb is the MATURITY dynamics that drive it. Seed to canopy is a
dial, and the dial is energy over density.
"""
from __future__ import annotations

import numpy as np

from core.membranes import Membrane

# Tissue densities RELATIVE to the fastest, lightest growth (grass = 1). Denser = slower.
REF_TISSUE = 'grass'
TISSUE_DENSITY = {
    'grass': 1.0, 'moss': 0.8, 'fern': 1.4, 'vine': 1.2, 'softwood': 2.0, 'hardwood': 3.3,
    'ironwood': 4.5,
}
BASE_GROWTH = 0.35              # growth rate of the reference tissue at unit energy


def relative_density(tissue: str) -> float:
    return TISSUE_DENSITY.get(tissue, 1.0)


def tissue_membrane(tissue: str, scale: float = 1.0) -> Membrane:
    """A tissue membrane MADE OF a plant tissue, carrying its relative density so that
    tissue.clock_rate() is the density clock -- and a grow verb on it (seed -> mature)."""
    m = Membrane(tissue, scale=scale, serial=f'TISSUE-{tissue}')
    m.prop(density=relative_density(tissue), tissue=tissue)
    m.state('seed', maturity=0.0, height=0.0, mass=0.0, canopy=0.0)
    m.state('mature', maturity=1.0, height=1.0, mass=1.0, canopy=1.0)
    m.verb('grow', 'seed', 'mature')
    return m


def growth_rate(tissue: Membrane, energy: float = 1.0) -> float:
    """How fast maturity advances per tick: energy / clock_rate. Uses the membrane's OWN
    clock_rate() (= sqrt(density)) -- dense tissue builds slower. energy is the environment
    (sun, water) driving it, NOT input."""
    return BASE_GROWTH * energy / tissue.clock_rate()


def grow(tissue_name: str, energy: float = 1.0, ticks: int = 60, seed_size: float = 0.02) -> dict:
    """Grow from a seed under a constant energy supply. Logistic: slow start, fast middle,
    saturation. Returns the maturity curve and the tick it crossed 90% (time to canopy)."""
    tissue = tissue_membrane(tissue_name)
    r = growth_rate(tissue, energy)
    S = seed_size
    curve = [S]
    t90 = None
    for t in range(1, ticks + 1):
        S = S + r * S * (1.0 - S)                   # logistic step
        S = float(np.clip(S, 0.0, 1.0))
        curve.append(S)
        if t90 is None and S >= 0.9:
            t90 = t
    return {
        'tissue': tissue_name, 'relative_density': relative_density(tissue_name),
        'clock_rate': tissue.clock_rate(), 'growth_rate': r,
        'maturity': curve[-1], 'ticks_to_canopy': t90 if t90 is not None else ticks + 1,
        'curve': curve,
        'verb_state_at_maturity': tissue.apply('grow', curve[-1]),
    }


def _bar(v, width=28):
    n = int(round(v * width))
    return '#' * n + '.' * (width - n)


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='the grow verb: seed->mature, energy over density')
    ap.add_argument('--energy', type=float, default=1.0)
    ap.add_argument('--ticks', type=int, default=60)
    a = ap.parse_args()

    print("  === the grow verb: two states + a dial the ENERGY flow drives (not input) ===")
    t = tissue_membrane('hardwood')
    print(f"    verb 'grow' moves: {t.verbs['grow'].differs_in()}   lo=seed hi=mature")
    for d in (0.0, 0.5, 1.0):
        st = t.apply('grow', d)
        print(f"    maturity {d:>3} -> height {st['height']:.2f} canopy {st['canopy']:.2f}")

    print(f"\n  === the density clock, a FOURTH time: dense tissue grows slower ===")
    print(f"  {'tissue':10} {'rel.density':>11} {'clock=√ρ':>9} {'rate':>7} {'ticks->canopy':>14}")
    for tis in ('grass', 'fern', 'vine', 'softwood', 'hardwood', 'ironwood'):
        g = grow(tis, a.energy, a.ticks)
        print(f"    {tis:10} {g['relative_density']:>11.1f} {g['clock_rate']:>9.2f} "
              f"{g['growth_rate']:>7.3f} {g['ticks_to_canopy']:>14}")
    print("    ^ grass shoots up, ironwood crawls -- energy / sqrt(density), the same clock")

    print(f"\n  === the growth CURVE is a sigmoid (establish -> expand -> canopy) ===")
    for tis in ('grass', 'hardwood', 'ironwood'):
        g = grow(tis, a.energy, a.ticks)
        marks = [g['curve'][int(f * (len(g['curve']) - 1))] for f in (0, .25, .5, .75, 1.0)]
        print(f"    {tis:9} " + '  '.join(f"{m:.2f}" for m in marks) + f"   [{_bar(g['maturity'])}]")
    print("    (columns: t=0, 25%, 50%, 75%, 100% of the window)")

    print("\n    dig | thrust | balance | grow -- FOUR verbs, ONE density clock, pointed at")
    print("    material, motion, rotation, and life. grow is energy-driven; the rest, input.")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
