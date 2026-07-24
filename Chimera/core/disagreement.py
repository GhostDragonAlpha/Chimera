"""disagreement — the Holy Ghost. Knowledge from where independent sources DISAGREE.

THE OPERATOR'S PRINCIPLE (this session): "new knowledge is learned just through communication
between complex systems of info." The studio has several systems that each produce an
arrangement of matter and each has its own ruler: the truck SCAN (reality, photographed), the
GROWN shaker (Cellular Potts physics), the PARAMETRIC emitter (a formula). Nobody had ever put
them on ONE ruler and listened for where they diverge.

    Where they AGREE, nothing is learned -- redundant confirmation.
    Where they DISAGREE, that gap is real information NEITHER SOURCE HELD ALONE:
      it names the characteristic BIAS of each system, and tells you which to trust per fact.

This is not averaging (that would hide the disagreement, which is the whole signal). It keeps
the divergence and attributes it. One source may be tagged TRUTH (a measurement of reality);
then a disagreement is a signed error and each other source gets a bias signature -- the facts
it systematically gets wrong. A simulator can only teach what it already believes, so this is
also how you find out what a simulator has WRONG, cheaply, without a new scan.

    python -m core.disagreement          # the three arrangement sources, concord + biases
"""
from __future__ import annotations

import numpy as np

# how much fractional spread across sources counts as CONCORD vs DISCORD. Fractional so it is
# scale-free -- clustering (~6) and alignment (~0.5) are judged on the same relative footing.
CONCORD_TOL = 0.12          # <=12% spread across sources -> they agree
DISCORD_TOL = 0.30          # >=30% -> a real disagreement worth attributing


def concord(sources: dict, facts, truth: str | None = None) -> dict:
    """Per fact: the values across sources, their relative spread, and (if a truth source is
    named) each source's signed deviation from it.

    sources: {source_name: {fact: value}}. truth: a key in sources whose value is reality.
    """
    names = list(sources)
    if len(names) < 2:
        raise ValueError('concord needs >= 2 sources -- one source cannot disagree with itself')

    out = {}
    for f in facts:
        vals = {s: float(sources[s][f]) for s in names if f in sources[s]}
        if len(vals) < 2:
            continue
        arr = np.array(list(vals.values()))
        centre = float(np.mean(np.abs(arr))) or 1e-9
        spread = float(arr.max() - arr.min()) / centre        # relative spread, scale-free
        rec = {'values': {s: round(v, 4) for s, v in vals.items()},
               'spread': round(spread, 3),
               'state': 'CONCORD' if spread <= CONCORD_TOL else
                        'DISCORD' if spread >= DISCORD_TOL else 'PARTIAL'}
        if truth and truth in vals:
            t = vals[truth]
            rec['deviation'] = {s: round((v - t) / (abs(t) or 1e-9), 3)
                                for s, v in vals.items() if s != truth}
        out[f] = rec
    return out


def source_biases(con: dict, truth: str) -> dict:
    """Each non-truth source's characteristic bias: the facts it systematically gets wrong,
    signed. This is the knowledge the disagreement produced -- what each simulator has WRONG."""
    biases: dict = {}
    for f, rec in con.items():
        for s, dev in rec.get('deviation', {}).items():
            if abs(dev) >= DISCORD_TOL:
                biases.setdefault(s, []).append(
                    (f, dev, 'too high' if dev > 0 else 'too low'))
    return biases


def report(sources: dict, facts, truth: str | None = None) -> str:
    con = concord(sources, facts, truth)
    lines = ['  ONE RULER, all sources -- where they agree (nothing learned) and disagree (real):',
             '']
    header = '  ' + f"{'fact':12} " + ' '.join(f'{s:>11}' for s in sources) + f"  {'spread':>7}  state"
    lines.append(header)
    for f, rec in con.items():
        vals = rec['values']
        cells = ' '.join('{:>11.3f}'.format(vals.get(s, float('nan'))) for s in sources)
        lines.append('  ' + f'{f:12} ' + cells + f"  {rec['spread']:>7.2f}  {rec['state']}")
    if truth:
        biases = source_biases(con, truth)
        lines += ['', f"  BIASES vs truth ({truth}) -- what each source systematically gets wrong:"]
        if not biases:
            lines.append('    (none above the discord threshold -- every source tracks reality)')
        for s, items in biases.items():
            for f, dev, dirn in items:
                lines.append(f"    {s:11} {f:12} {dev:+.0%}  {dirn}")
        lines += ['',
                  '  READ THE DISCORD, not the average: each bias is a lever -- fix that source',
                  '  on that fact, or trust the source that agrees with reality there instead.']
    return '\n'.join(lines)


def _arrangement_sources() -> tuple:
    """The three arrangement sources, measured on the four facts. truck = truth."""
    import json
    from pathlib import Path
    import core.trainables.arrangement as A
    import core.trainables.grown_arrangement as G

    facts = ('aspect', 'verticality', 'alignment', 'clustering')
    root = Path(__file__).resolve().parents[1]

    regions = [r for t in json.loads((root / 'docs/matter/arrangement_targets.json').read_text())
               ['targets'].values() for r in t.values()]
    truck = {k: float(np.mean([r[k] for r in regions])) for k in facts}

    pw = json.loads((root / 'docs/objectives/arrangement.trained.json').read_text())
    pg = pw.get('genome', pw); pg = pg.get('genome', pg)
    para = {k: float(A.measure(pg)[k]) for k in facts}

    gw = json.loads((root / 'docs/objectives/grown_arrangement.trained.json').read_text())
    gg = gw.get('genome', gw); gg = gg.get('genome', gg)
    grown = {k: float(G.measure(gg)[k]) for k in facts}

    return {'truck': truck, 'parametric': para, 'grown': grown}, facts, 'truck'


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    sources, facts, truth = _arrangement_sources()
    print(report(sources, facts, truth))
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
