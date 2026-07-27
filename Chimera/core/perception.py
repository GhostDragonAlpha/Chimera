"""perception — PSYCHOPHYSICS: how much of a physical difference a person can actually see.

THE HIRE (2026-07-23). The operator: "we'll need all the ologies... we have an unlimited
budget for them." This is the first recruit on THE SPAN -- the column between the two
terminals, where emotion lives. Physics says what a thing IS; sociology says what a group
WANTS; psychophysics says how much of a physical change reaches a person at all. Without
it the studio has no way to answer "how precise does this need to be?" except by guessing.

WHAT IT FOUND ON DAY ONE. Converted into units a person can see, the four arrangement
bands measured off a real scan are wildly unequal:

    aspect        27.2 JNDs wide   obviously visible
    clustering     4.0             visible
    verticality    2.1             barely
    alignment      1.1             BELOW THRESHOLD -- the two ends look identical

`band_margin` is the MINIMUM over the four, so for a full day the objective was pinned at
0.196 by verticality and alignment -- the two facts nobody can see -- while aspect, 27 JNDs
wide and screaming, was never the constraint. The optimiser was spending its entire budget
on invisible precision. That is not a tuning error; it is the absence of an -ology.

    THE COLUMN RULE (core/spine.py): a JND is rigorously MEASURED and still does not hold
    in an empty universe, so everything here terminates at THE HUMAN, never at PHYSICS.

HONEST LIMITS, stated because the numbers look more precise than they are:
  - These constants come from lab studies using dot arrays and oriented gratings, NOT
    splat clouds. Treat them as order-of-magnitude.
  - Orientation discrimination varies enormously with stimulus: foveal grating thresholds
    reach ~0.5 deg, while the ~5 deg figure used here is for a harder, more natural task.
  - No viewing distance is fixed. Angular quantities (alignment, verticality) are
    distance-INVARIANT, so they are safe; a size threshold would not be.
  - THE RANKING IS ROBUST EVEN WHERE THE CONSTANTS ARE NOT. At a 2 deg orientation JND
    alignment is 2.9 and verticality 5.4; at 10 deg they are 0.6 and 1.1. Alignment stays
    smallest and aspect stays ~25x widest under every assumption in the literature range.
    The ORDER is what this module is for; the absolute JND counts are indicative.

SOURCES
  Weber fraction, numerosity, adults: reported range 0.10-0.28, group mean ~0.21.
    "Sensitivity to numerosity is not a unique visuospatial psychophysical predictor of
    mathematical ability", PMC3748346.
  Numerosity vs texture-density regimes: below ~0.3 dots/deg^2 thresholds rise with
    numerosity (constant Weber fraction); above it they rise only with sqrt(numerosity),
    i.e. RELATIVE discrimination improves for dense textures.
    "Mechanisms for perception of numerosity or texture-density are governed by
    crowding-like effects", Journal of Vision.
  Orientation discrimination threshold, adults: ~5.12 deg.
    "Sensitivity to numerosity ...", PMC3748346.
  Weber's law itself: dI/I = k. Fechner 1860.
"""
from __future__ import annotations

import numpy as np

# --- researched constants -------------------------------------------------------------
# Conservative choices inside each published range: a SMALLER Weber fraction and a SMALLER
# angular threshold both mean "people can see more than we assume", which biases the studio
# toward keeping precision rather than discarding it. If this module is wrong, it should be
# wrong in the direction that does not silently degrade the game.

W_NUMEROSITY = 0.15      # density / grouping. Range 0.10-0.28, mean ~0.21; 0.15 = a good
                         # discriminator, so we do not over-claim invisibility.
W_LENGTH = 0.05          # length and proportion. Conservative end of the usual few-percent.
ORIENT_JND_DEG = 5.12    # orientation discrimination, adults, natural task.

DENSE_TEXTURE_THRESHOLD = 0.3    # dots per deg^2; above this, numerosity gives way to
                                 # texture-density and thresholds grow only as sqrt(n).


def circular_sd_deg(resultant_length: float) -> float:
    """Mean resultant length (0..1) -> circular standard deviation, in degrees.

    An ALIGNMENT number is a coherence, not an angle, and a coherence cannot be compared
    to a degrees-based threshold. This is the conversion that makes them commensurable:
    for a von Mises distribution, sigma = sqrt(-2 ln R).
    """
    r = float(np.clip(resultant_length, 1e-9, 1.0 - 1e-9))
    return float(np.degrees(np.sqrt(-2.0 * np.log(r))))


def jnds_angular(lo: float, hi: float, kind: str = 'coherence') -> float:
    """How many just-noticeable-differences separate two angular quantities.

    kind='coherence'  the values are mean resultant lengths (alignment)
    kind='sine'       the values are the sine of an angle (verticality = mean |z|)
    """
    if kind == 'coherence':
        d = abs(circular_sd_deg(lo) - circular_sd_deg(hi))
    elif kind == 'sine':
        d = abs(np.degrees(np.arcsin(np.clip(hi, -1, 1)))
                - np.degrees(np.arcsin(np.clip(lo, -1, 1))))
    else:
        raise ValueError(f'unknown angular kind {kind!r}')
    return float(d / ORIENT_JND_DEG)


def jnds_ratio(lo: float, hi: float, weber: float = W_NUMEROSITY) -> float:
    """How many JNDs separate two quantities that obey Weber's law.

    Weber means the threshold scales WITH the stimulus, so the steps are multiplicative and
    the count is done in log space -- not (hi-lo)/jnd, which would be right only for a
    constant threshold and wrong everywhere Weber applies.
    """
    lo, hi = abs(float(lo)), abs(float(hi))
    if lo <= 0 or hi <= 0:
        return 0.0
    return float(abs(np.log(hi / lo)) / np.log(1.0 + weber))


# How each arrangement fact reaches a person. The mapping is the whole content of this
# module: a number is not visible or invisible in itself, only through the channel that
# carries it.
FACT_CHANNEL = {
    'aspect':      ('ratio', W_LENGTH),        # a proportion; Weber in length
    'clustering':  ('ratio', W_NUMEROSITY),    # grouping density; Weber in numerosity
    'verticality': ('sine', None),             # mean |z| of unit directions -> elevation
    'alignment':   ('coherence', None),        # resultant length -> angular spread
}


def band_jnds(fact: str, lo: float, hi: float) -> float:
    """How many JNDs wide a measured band is -- i.e. can a player tell its ends apart?"""
    ch = FACT_CHANNEL.get(fact)
    if ch is None:
        raise KeyError(f'no perceptual channel for {fact!r}; have {sorted(FACT_CHANNEL)}')
    kind, weber = ch
    if kind == 'ratio':
        return jnds_ratio(lo, hi, weber)
    return jnds_angular(lo, hi, kind)


def visibility(fact: str, lo: float, hi: float) -> dict:
    """A band, judged by whether a person could see the difference across it."""
    n = band_jnds(fact, lo, hi)
    if n > 8:
        verdict, note = 'OBVIOUS', 'the ends are plainly different'
    elif n > 2:
        verdict, note = 'VISIBLE', 'a person can tell the ends apart'
    elif n > 1.2:
        verdict, note = 'MARGINAL', 'near threshold; only some viewers, some of the time'
    else:
        verdict, note = 'INVISIBLE', 'the ends look the same -- optimising inside it is waste'
    return {'fact': fact, 'jnds': round(n, 2), 'verdict': verdict, 'note': note}


def perceptual_weights(bands: dict, floor: float = 0.05) -> dict:
    """Weight each fact by how much of it a person can actually see.

    THIS IS THE POINT OF THE MODULE. Normalising a band error by the band's own WIDTH (what
    the objective did all day) makes every fact equally important, which is a statement
    about arithmetic rather than about the world. Weighting by JND count says: spend the
    optimiser where a viewer will notice.

    A FLOOR, not a zero. An invisible fact still constrains what the matter physically IS,
    and a genome free to wander in an unseen dimension can drift somewhere that becomes
    visible under a different light, distance or neighbour. Perception decides PRIORITY, it
    does not get a veto over physics.
    """
    j = {k: band_jnds(k, lo, hi) for k, (lo, hi) in bands.items()}
    total = sum(j.values()) or 1.0
    w = {k: max(floor, v / total) for k, v in j.items()}
    s = sum(w.values())
    return {k: round(v / s, 4) for k, v in w.items()}


def _main() -> int:
    import argparse
    import json
    import sys
    from pathlib import Path
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    ap = argparse.ArgumentParser(description='psychophysics: what a person can actually see')
    ap.add_argument('--targets', default='docs/matter/arrangement_targets.json')
    a = ap.parse_args()

    p = Path(__file__).resolve().parents[1] / a.targets
    regions = [r for t in json.loads(p.read_text())['targets'].values() for r in t.values()]
    bands = {k: (min(r[k] for r in regions), max(r[k] for r in regions))
             for k in FACT_CHANNEL}

    print('\n  HOW WIDE IS EACH MEASURED BAND, IN UNITS A PERSON CAN SEE?\n')
    print(f'    {"fact":12} {"band":>18}   {"JNDs":>6}   verdict')
    rows = sorted((visibility(k, *v) for k, v in bands.items()),
                  key=lambda r: -r['jnds'])
    for r in rows:
        lo, hi = bands[r['fact']]
        print(f'    {r["fact"]:12} {lo:8.3f}..{hi:7.3f}   {r["jnds"]:6.1f}   '
              f'{r["verdict"]:9}  {r["note"]}')

    print('\n  WHERE THE OPTIMISER SHOULD SPEND ITS EFFORT:\n')
    w = perceptual_weights(bands)
    for k in sorted(w, key=lambda x: -w[x]):
        print(f'    {k:12} {w[k]:6.1%}   (equal weighting would give 25.0%)')
    print()
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
