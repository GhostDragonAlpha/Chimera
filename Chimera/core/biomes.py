"""biomes — climate over the surface, built ON the line between PROGRAM, TRAIN, and HUMAN.

This module is deliberately split into the three tiers, so it doubles as the worked example of
"where is the line?":

  PROGRAM (the rules -- physics, TRUE, authored once):
      temperature_C()  falls with latitude and with altitude (lapse rate 6.5 C/km -- a physical
                       constant, not a knob).
      precipitation_mm() follows the Hadley structure: a wet equatorial belt, dry subtropics
                       (~30 deg), wet mid-latitudes, plus continentality (interiors dry because
                       ocean moisture cannot reach them) -- atmospheric physics, authored.
      classify()       the Whittaker structure: temperature x precipitation -> biome. WHICH
                       biomes exist and HOW they are ordered is science, authored.

  TRAIN (the numbers -- the free thresholds, with a machine-checkable objective):
      THRESHOLDS       where exactly forest becomes grassland becomes desert. A small parameter
                       vector. measure() reports FACTS (biome-area fractions); an objective would
                       say "match Earth's real fractions" -- physics, not taste. So this IS
                       trainable: cheap pure-function eval, physics objective. It is set here from
                       published Whittaker/Koppen values, and lands close to Earth already (see
                       measure()) -- training would refine it, not invent it.

  HUMAN (the taste -- what is better only in your eye):
      PALETTE          the colours, the mood. Which of the allowed biomes your art direction
                       actually wants, "lush" vs "harsh". Never derived from physics; the
                       preference loop / taste.json owns this. Marked, not trained.

Everything is a pure function of position over the whole-sphere surface -- the same planet gets
the same biomes, forever.
"""
from __future__ import annotations

from collections import deque

import numpy as np

# ============================ PROGRAM (the rules) ============================
# Physical constants. Not knobs -- these are measured facts about the world.

LAPSE_C_PER_M = 6.5e-3          # tropospheric lapse rate: air cools ~6.5 C per km climbed
T_EQUATOR_C = 28.0             # mean sea-level temperature at the equator
T_POLE_C = -25.0               # ...and at the poles


def temperature_C(lat_deg: float, elev_m: float, warmth: float = 0.0) -> float:
    """Surface temperature from latitude (insolation) and altitude (lapse rate). PROGRAM.

    Insolation falls with the COSINE of latitude (the sun's angle on the surface) -- so
    mid-latitudes stay mild (45 deg ~= 12 C, matching Earth's zonal mean), not frozen. The
    earlier latitude^1.15 curve dropped too fast and iced the mid-latitudes -- a LAW bug the
    biome measure() surfaced, fixed here rather than papered over by moving thresholds.

    `warmth` (deg C) shifts the whole climate up -- a GREENHOUSE world (Eocene/Carboniferous:
    forests to the poles, no ice) is Earth's own climate with warmth added, not a fantasy."""
    base = T_POLE_C + (T_EQUATOR_C - T_POLE_C) * np.cos(np.radians(lat_deg))
    return base + warmth - LAPSE_C_PER_M * max(elev_m, 0.0)


def precipitation_mm(lat_deg: float, ocean_prox: float, wetness: float = 1.0) -> float:
    """Annual precipitation from the Hadley circulation + continentality. PROGRAM.

    Wet equatorial belt (rising air, the ITCZ), dry subtropics near 30 deg (descending air --
    where Earth's deserts are), wet mid-latitudes (storm tracks), dry poles. Then scaled by how
    much ocean moisture can reach the point (interiors are dry -- the Gobi, not the coast).

    `wetness` scales the whole hydrological cycle -- a warmer world holds more water vapour and
    rains more (Clausius-Clapeyron), so a greenhouse Eden is wetter, not just hotter."""
    a = abs(lat_deg)
    itcz = 2400.0 * np.exp(-((a - 0.0) / 10.0) ** 2)        # equatorial rainbelt
    midlat = 850.0 * np.exp(-((a - 52.0) / 16.0) ** 2)      # mid-latitude storm track
    subtropical_dry = 0.30 + 0.70 * (1 - np.exp(-((a - 30.0) / 13.0) ** 2))  # 0.30 at 30 deg
    base = (140.0 + itcz + midlat) * subtropical_dry
    return float(base * (0.45 + 0.90 * ocean_prox) * wetness)   # continentality x climate wetness


# ============================ TRAIN (the numbers) ============================
# The free thresholds the rules leave open. measure() below reports the facts a trainer reads;
# the objective would be "match Earth's real biome-area fractions" -- physics, not taste.
# Set from published Whittaker/Koppen values; a training pass would refine, not invent.

THRESHOLDS = {          # <-- THE TRAINABLE VECTOR
    'ice_T': -8.0,      # below this mean-T: permanent ice
    'tundra_T': 2.0,    # below this: tundra (too cold for trees)
    'taiga_T': 8.0,     # below this (but above tundra): boreal forest
    'warm_T': 21.0,     # above this: tropical regime
    'desert_P': 240.0,  # below this precip: desert
    'grass_P': 620.0,   # below this (but above desert): grassland / steppe
    'forest_P': 1250.0, # above this in the warm regime: rainforest
}

# Earth's real land-biome area fractions -- the training TARGET (approx, terrestrial only).
EARTH_FRACTIONS = {
    'desert': 0.19, 'grassland': 0.20, 'savanna': 0.11, 'tropical_rainforest': 0.17,
    'temperate_forest': 0.13, 'taiga': 0.12, 'tundra': 0.08,
}


def classify(T: float, P: float, th: dict = THRESHOLDS) -> str:
    """Whittaker structure (PROGRAM) evaluated at the trained thresholds (TRAIN)."""
    if T < th['ice_T']:
        return 'ice'
    if T < th['tundra_T']:
        return 'tundra'
    if P < th['desert_P']:
        return 'desert'
    if T >= th['warm_T']:
        if P >= th['forest_P']:
            return 'tropical_rainforest'
        if P < th['grass_P']:
            return 'savanna'
        return 'tropical_seasonal_forest'
    if P < th['grass_P']:
        return 'grassland'
    if T < th['taiga_T']:
        return 'taiga'
    return 'temperate_forest'


# ============================ HUMAN (the taste) ==============================
# Colours and mood. Never derived from physics; the preference loop owns this. Marked, not trained.

PALETTE = {
    'ocean': (38, 90, 165), 'ice': (232, 238, 245), 'tundra': (150, 158, 140),
    'taiga': (54, 84, 68), 'temperate_forest': (58, 120, 60), 'grassland': (168, 168, 92),
    'desert': (208, 184, 120), 'savanna': (176, 158, 84),
    'tropical_seasonal_forest': (86, 150, 66), 'tropical_rainforest': (26, 96, 44),
}


# ============================ the surface classifier =========================


def _distance_to_ocean_cells(elev: np.ndarray) -> np.ndarray:
    """Multi-source BFS from every ocean cell -> continentality. PROGRAM (an algorithm)."""
    nlat, nlon = elev.shape
    dist = np.full(elev.shape, 1e9)
    dq = deque()
    for i, j in np.argwhere(elev <= 0):
        dist[i, j] = 0.0
        dq.append((i, j))
    while dq:
        i, j = dq.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, (j + dj) % nlon               # longitude wraps
            if 0 <= ni < nlat and dist[ni, nj] > dist[i, j] + 1:
                dist[ni, nj] = dist[i, j] + 1
                dq.append((ni, nj))
    return dist


def classify_surface(planet, nlat: int = 180, nlon: int = 360, th: dict = THRESHOLDS,
                     warmth: float = 0.0, wetness: float = 1.0):
    """Assign a biome to every land cell of the whole-sphere surface. Returns (biome grid,
    elevation grid). Ocean cells are 'ocean'. warmth/wetness shift the climate toward a
    greenhouse (lush) world; defaults are Earth."""
    elev = planet.onion.elevation_grid(nlat, nlon)
    lats = np.linspace(90, -90, nlat)
    dist = _distance_to_ocean_cells(elev)
    km_per_cell = (180.0 / nlat) * 111.0
    prox = np.exp(-(dist * km_per_cell) / 650.0)           # moisture reach ~650 km e-fold
    biome = np.empty(elev.shape, dtype=object)
    for i in range(nlat):
        for j in range(nlon):
            if elev[i, j] <= 0:
                biome[i, j] = 'ocean'
                continue
            T = temperature_C(lats[i], elev[i, j], warmth)
            P = precipitation_mm(lats[i], float(prox[i, j]), wetness)
            biome[i, j] = classify(T, P, th)
    return biome, elev


# Bounds each threshold may move within (the search space for the TRAIN tier).
_RANGE = {'ice_T': (-15.0, 0.0), 'tundra_T': (-2.0, 6.0), 'taiga_T': (4.0, 12.0),
          'warm_T': (17.0, 24.0), 'desert_P': (120.0, 400.0), 'grass_P': (450.0, 850.0),
          'forest_P': (950.0, 1600.0)}


def measure(planet, th: dict = THRESHOLDS, nlat: int = 120, nlon: int = 240) -> dict:
    """THE TRAINER'S EYES. Facts only: what fraction of LAND each biome covers (cos-lat area
    weighted), and the total mismatch against Earth. This is the objective a training pass would
    minimize -- physics, not taste. Its existence is what makes THRESHOLDS trainable."""
    biome, elev = classify_surface(planet, nlat, nlon, th)
    nlat, nlon = elev.shape
    w = np.cos(np.radians(np.linspace(90, -90, nlat)))[:, None] * np.ones((1, nlon))
    land = w * (elev > 0)
    land_tot = land.sum()
    frac = {}
    for i in range(nlat):
        for j in range(nlon):
            b = biome[i, j]
            if b != 'ocean':
                frac[b] = frac.get(b, 0.0) + land[i, j]
    frac = {k: v / land_tot for k, v in frac.items()}
    # aggregate the two tropical-forest classes to compare with Earth's single number
    comp = dict(frac)
    comp['tropical_rainforest'] = comp.get('tropical_rainforest', 0) + comp.pop('tropical_seasonal_forest', 0)
    mismatch = sum(abs(comp.get(k, 0.0) - v) for k, v in EARTH_FRACTIONS.items())
    return {'fractions': {k: round(v, 3) for k, v in sorted(frac.items(), key=lambda x: -x[1])},
            'earth_mismatch_L1': round(mismatch, 3), 'n_biomes': len(frac)}


def _valid(th: dict) -> dict:
    """Keep the threshold ORDERING sane (a rule, not a number): cold<cool<warm, dry<mid<wet.
    This is a PROGRAM constraint enforced ON the trained vector -- the search may not invert it."""
    t = dict(th)
    for a, b in (('ice_T', 'tundra_T'), ('tundra_T', 'taiga_T'), ('taiga_T', 'warm_T'),
                 ('desert_P', 'grass_P'), ('grass_P', 'forest_P')):
        if t[a] > t[b]:
            t[a], t[b] = t[b], t[a]
    return t


def train_thresholds(planet, iters: int = 220, seed: int = 0):
    """TRAIN the numbers. A search over THRESHOLDS minimizing the Earth-fraction mismatch --
    physics objective, no taste, no human turning the crank. This is what the trainer does; it
    is inline and coarse-grid here so the demo is fast. The LLM wrote the objective (match
    Earth) and the bounds; the SEARCH finds the values."""
    rng = np.random.default_rng(seed)
    best = _valid(dict(THRESHOLDS))
    m0 = best_m = measure(planet, best, 60, 120)['earth_mismatch_L1']
    for _ in range(iters):
        cand = dict(best)
        for k in cand:
            if rng.random() < 0.4:
                lo, hi = _RANGE[k]
                cand[k] = float(np.clip(cand[k] + rng.normal(0, 0.12) * (hi - lo), lo, hi))
        cand = _valid(cand)
        m = measure(planet, cand, 60, 120)['earth_mismatch_L1']
        if m < best_m:
            best, best_m = cand, m
    return best, m0, best_m


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    from core.planet_membrane import PlanetOnion

    ap = argparse.ArgumentParser(description='biomes over the surface (PROGRAM|TRAIN|HUMAN)')
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--train', action='store_true', help='TRAIN the thresholds (the numbers)')
    a = ap.parse_args()

    class _P:                                       # tiny adapter: biomes wants planet.onion
        def __init__(self, onion): self.onion = onion
    planet = _P(PlanetOnion.earthlike(seed=a.seed))

    m = measure(planet)
    print("  === biome-area fractions (the TRAIN tier's measure -- facts, not taste) ===")
    for k, v in m['fractions'].items():
        earth = EARTH_FRACTIONS.get(k.replace('tropical_seasonal_forest', 'tropical_rainforest'))
        tag = f"(Earth ~{earth:.2f})" if earth else ""
        print(f"    {k:26} {v*100:5.1f}% of land   {tag}")
    print(f"\n    L1 mismatch vs Earth: {m['earth_mismatch_L1']:.3f}  "
          f"<- a training pass minimizes THIS by nudging THRESHOLDS (physics objective)")

    if a.train:
        print("\n  === TRAIN the numbers: a search over THRESHOLDS (no human turning the crank) ===")
        learned, m0, m1 = train_thresholds(planet, iters=220, seed=a.seed)
        print(f"    mismatch {m0:.3f} -> {m1:.3f} over 220 evals")
        print("    learned thresholds (the search found these, not me):")
        for k in THRESHOLDS:
            print(f"      {k:10} {THRESHOLDS[k]:8.1f}  ->  {learned[k]:8.1f}")
        mf = measure(planet, learned)
        print(f"    biome fractions after training: "
              + ', '.join(f"{k} {v*100:.0f}%" for k, v in list(mf['fractions'].items())[:5]))
        print("    (PROGRAM built the mechanism; TRAIN set the numbers; PALETTE stays HUMAN)")

    if a.render:
        from pathlib import Path
        try:
            from PIL import Image
        except Exception:
            print('\n  (PIL absent -- skipping render)'); return 0
        biome, elev = classify_surface(planet, 360, 720)
        rgb = np.zeros((*elev.shape, 3), np.uint8)
        for i in range(elev.shape[0]):
            for j in range(elev.shape[1]):
                rgb[i, j] = PALETTE.get(biome[i, j], (255, 0, 255))
        # gentle relief shading on land so mountains read
        gy, gx = np.gradient(np.where(elev > 0, elev, 0))
        shade = np.clip(0.7 - (gx * 0.0006), 0.45, 1.0)[..., None]
        land = (elev > 0)[..., None]
        rgb = np.where(land, np.clip(rgb * shade, 0, 255).astype(np.uint8), rgb)
        out = Path('Saved/SplatEmit'); out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgb).save(out / 'biomes_map.png')
        # globe
        N = 400
        yy, xx = np.mgrid[0:N, 0:N]
        X = (xx - N / 2) / (N / 2); Y = (N / 2 - yy) / (N / 2)
        disc = X**2 + Y**2 <= 1
        Z = np.sqrt(np.clip(1 - X**2 - Y**2, 0, 1))
        latg = np.degrees(np.arcsin(np.clip(Y, -1, 1)))
        long = np.degrees(np.arctan2(X, Z)) % 360
        glr = np.zeros((N, N, 3), np.uint8)
        ii = np.clip(((90 - latg) / 180 * (elev.shape[0] - 1)), 0, elev.shape[0] - 1).astype(int)
        jj = np.clip((long / 360 * elev.shape[1]), 0, elev.shape[1] - 1).astype(int)
        glr[disc] = rgb[ii[disc], jj[disc]]
        Image.fromarray(glr).save(out / 'biomes_globe.png')
        print(f"\n  wrote {out}/biomes_map.png and biomes_globe.png")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
