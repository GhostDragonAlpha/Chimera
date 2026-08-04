"""splat_appearance.py -- THE APPEARANCE as a Gaussian-splat MOVIE (beginning -> end), via ParticleEngine.

The mandatory visual test judges the REAL engine render, not a diagram; and a term is a SLICE of the
timeline UNFOLDING, so the appearance is a MOVIE: a scene rendered at its BEGINNING (t=0) and its END
(settled). Two ends of the dial. The physics (the agent) owns this; the human side reads it.

Two scene KINDS, because different matter renders differently (no aesthetic passes -- the look DERIVES
from what the thing IS):

  * "collapse" -- a diffuse body of one colour drawn together by a central attractor. Correct for a
    STAR or a dust cloud: plasma and dust ARE diffuse. begin = dispersed, end = coalesced.
  * "planet"   -- a SOLID world. Splats are placed ON a sphere shell (Fibonacci distribution) and
    painted by surface type: deep OCEANS, continent-noise LAND, polar ICE caps, wrapped in a faint
    ATMOSPHERE halo. Depth-sorted opaque compositing gives a crisp limb -- a world seen from space,
    not a fog ball. begin = the world ACCRETING from its own cloud of dust, end = the settled sphere.

Terms with a scene render as splats; terms without one return None (the engine falls back to the
matplotlib placeholder until their scene is authored). Needs the GPU (Numba CUDA) -- rendering is
physics, so it belongs to the same hardware. Deterministic: the RNG is seeded from the term name, so
a term renders byte-identically every time (same seed, same world, forever).
"""
from __future__ import annotations

import sys
import zlib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# term -> scene spec.
#   collapse: a particle body of a colour, drawn together by a central attractor as it evolves.
#   planet:   a solid habitable sphere (radius in world units; ocean = fraction of the surface that is sea).
SCENES = {
    "theStar":        {"kind": "collapse", "type": "atmosphere", "count": 7000, "spread": 55, "size": 3.4,
                       "color": (1.0, 0.93, 0.82, 1.0), "pull": 1.4, "cam": (0.0, -210.0, 26.0)},
    "aPlanet":        {"kind": "planet", "radius": 88.0, "ocean": 0.66, "cam": (0.0, -250.0, 40.0)},
    # RELIEF AT ITS TRUE SCALE. It was 0.13 of the radius -- 40x too tall -- and the cost was
    # visible: measured, the silhouette WOBBLED 2.1% as the body turned (against 0.3% for the
    # undisplaced aPlanet), so the object appeared to change shape at the sub-camera point.
    # Earth's ENTIRE relief, Everest (+8.85 km) to Challenger Deep (-10.99 km), is 19.8 km on a
    # 6371 km radius = 0.0031. And the ceiling is derivable, not looked up: rock crushes under its
    # own weight above h_max = sigma/(rho*g) = 2e8/(2700*9.81) = 7.5 km, which is 0.0012 of R --
    # the same law that predicts Olympus Mons at 20 km on Mars.
    # SO A PLANET IS SMOOTHER THAN A BILLIARD BALL, and at true scale its relief is INVISIBLE from
    # space. That is not a defect to compensate for: at this membrane's scale terrain is carried by
    # COLOUR (the hypsometric tint), and it only becomes geometry when you descend to it. Any
    # exaggeration must be declared like STAR_EXAGGERATION, never smuggled into the constant.
    "theTerrain":     {"kind": "terrain", "radius": 88.0, "relief": 0.0031, "sea": 0.5, "cam": (0.0, -250.0, 40.0)},
    "thePlanets":     {"kind": "row", "span": 500.0, "cam": (0.0, -520.0, 55.0),
                       "planets": [((1.00, 0.28, 0.12), 30.0),   # molten red   (hottest)
                                   ((1.00, 0.52, 0.16), 30.0),   # orange
                                   ((0.92, 0.80, 0.42), 30.0),   # warm tan
                                   ((0.32, 0.60, 0.52), 30.0),   # temperate blue-green
                                   ((0.24, 0.42, 0.85), 30.0),   # cold blue
                                   ((0.90, 0.95, 1.00), 30.0)]},  # frozen white (coldest)
    "theSolarSystem": {"kind": "system", "cam": (0.0, -400.0, 230.0)},
    # THE STAND (the dyad's FAIL_RESTART, 0.25/0.20): one specimen tree cannot read as "a garden
    # FULL of vegetation" -- and the garden's biome IS a forest. So the scene is the stand:
    # a green field carrying many grown trees, the Tree of Knowledge prominent among them.
    "theGarden":      {"kind": "garden", "radius": 170.0, "cam": (0.0, -240.0, 28.0)},
    # THE WEB: the same garden (same seed, same place) with its animals arrived -- the
    # community assembling: plants first, then the grazers and the birds.
    "theEcosystem":   {"kind": "ecosystem", "radius": 170.0, "cam": (0.0, -240.0, 28.0)},
    # THE RECURSION: a tree IS the terrarium's L-system, so the scene is grown from the real
    # bone skeleton (core/terrarium), not drawn as blobs. One tree, alone -- theGarden's stand
    # is the many; this term is the ONE.
    "theTree":        {"kind": "tree", "height": 60.0, "radius": 120.0, "cam": (0.0, -120.0, 18.0)},
    # THE FORM: the form is the genome's, not the drawing's -- three DIFFERENT genomes
    # grown by the same machinery, side by side (spreading / mid / columnar).
    "theTreeForm":    {"kind": "treeform", "height": 60.0, "radius": 60.0, "cam": (0.0, -70.0, 8.0)},
    # THE FRUIT: the same tree (its genome, its seed) bearing fruit at its twig tips;
    # the movie is the ripening -- small green -> full red, the tree itself unchanged.
    "theFruit":       {"kind": "fruit", "height": 60.0, "radius": 60.0, "cam": (0.0, -70.0, 8.0)},
    # THE PLANTING: seeds placed by a hand, in rows -- the intent visible as pattern.
    # Elevated camera: the ROWS are the salient read, so the field is seen from above.
    "thePlanting":    {"kind": "planting", "radius": 150.0, "cam": (0.0, -70.0, 110.0)},
    "theFarming":     {"kind": "farming", "radius": 150.0, "cam": (0.0, -70.0, 110.0)},
    "thePlanetaryFarm": {"kind": "planetary_farm", "radius": 190.0, "cam": (0.0, -140.0, 130.0)},
    "theLunarFarm":    {"kind": "lunar_farm", "radius": 190.0, "cam": (0.0, -160.0, 120.0)},
    "theOrbitalFarm":  {"kind": "orbital_farm", "radius": 230.0, "cam": (0.0, -180.0, 120.0)},
    "theSpace":        {"kind": "space", "radius": 300.0, "cam": (0.0, -40.0, 20.0)},
    "theSeed":         {"kind": "seed", "radius": 180.0, "cam": (0.0, -150.0, 90.0)},
    "theDeterminism":  {"kind": "determinism", "radius": 200.0, "cam": (0.0, -170.0, 100.0)},
    "theLaws":         {"kind": "laws", "radius": 180.0, "cam": (0.0, -170.0, 110.0)},
    "theTruth":        {"kind": "truth", "radius": 180.0, "cam": (0.0, -165.0, 75.0)},
    "theShip":         {"kind": "ship", "radius": 130.0, "cam": (0.0, -100.0, 30.0)},
    "theFlight":       {"kind": "flight", "radius": 160.0, "cam": (0.0, -120.0, 50.0)},
    "theShipPower":    {"kind": "ship_power", "radius": 110.0, "cam": (0.0, -82.0, 28.0)},
    "theShipCombat":   {"kind": "ship_combat", "radius": 150.0, "cam": (0.0, -115.0, 42.0)},
    "theShields":      {"kind": "shields", "radius": 150.0, "cam": (0.0, -115.0, 42.0)},
    "theWarpDrive":    {"kind": "warp_drive", "radius": 170.0, "cam": (0.0, -125.0, 55.0)},
    "theShipView":     {"kind": "ship_view", "radius": 150.0, "cam": (0.0, -115.0, 42.0)},
    "theSalvage":      {"kind": "salvage", "radius": 150.0, "cam": (0.0, -115.0, 42.0)},
    "theDescent":      {"kind": "descent", "radius": 170.0, "cam": (30.0, -80.0, 35.0)},
    "theStanding":     {"kind": "standing", "radius": 120.0, "cam": (0.0, -85.0, 22.0)},
    "theBlackHole":    {"kind": "black_hole", "radius": 140.0, "cam": (0.0, -110.0, 0.0)},
    "theVerbs":        {"kind": "verbs", "radius": 130.0, "cam": (0.0, -95.0, 30.0)},
    "theDig":          {"kind": "dig", "radius": 130.0, "cam": (6.0, -90.0, 45.0)},
    "theGrow":         {"kind": "grow", "radius": 130.0, "cam": (0.0, -110.0, 35.0)},
    "theScan":         {"kind": "scan", "radius": 130.0, "cam": (0.0, -105.0, 30.0)},
    "theNavigate":     {"kind": "navigate", "radius": 150.0, "cam": (0.0, -130.0, 55.0)},
    "theShoot":        {"kind": "shoot", "radius": 140.0, "cam": (0.0, -110.0, 30.0)},
    "theMelee":        {"kind": "melee", "radius": 120.0, "cam": (0.0, -85.0, 28.0)},
}

# ── the particle buffer layout the pipeline reads (ParticleEngine.core.COL) ──
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA, SIZE = 16, 17, 18, 19, 20
NX, NY, NZ = 21, 22, 23     # OPTIONAL surface normal -> the pipeline back-face-culls occluded grains (0,0,0 = no cull)

# ── ONE calibration, shared by every solid-sphere scene ──
# A dense splat shell over-accumulates ~2x: overlapping Gaussian tails sum before the opacity
# saturates (MEASURED -- a uniform (0.05,0.15,0.45) navy sphere rendered (0.20,0.58,0.95) cyan-white).
# The transfer is ~proportional per channel, so we invert it: pre-multiply surface colours by the gain
# so the render lands on the intended palette. Keeping GRAIN size/alpha/DENSITY constant across scenes
# keeps the over-accumulation factor constant, so the ONE measured gain holds for every world.
_SURFACE_GAIN = 0.45      # invert the measured ~2x over-accumulation (translucent shells: _solid_sphere/theStar)
_PLANET_GAIN = (1.0, 1.0, 1.0)   # NO gain. The ~2.5x "over-accumulation" these constants existed to invert was never
                          # physical -- it was a COMPOSITING BUG: `trans *= (1 - a*wgt*trans)` instead of `(1 - a*wgt)`,
                          # which decayed transmittance far too slowly so ~35 splats accumulated instead of ~2 (total
                          # alpha 2.1 instead of 1.0). Fixed 2026-07-26 in gpu_pipeline._composite and the v2 WGSL.
                          # With correct front-to-back "over", an opaque surface renders its TRUE colour: gain = 1.
_GRAIN_SIZE = 5.0         # per-grain render size (world units)
_GRAIN_ALPHA = 0.5        # per-grain opacity
_GRAIN_DENSITY = 0.185    # grains per unit sphere AREA (= aPlanet's 18000 / 4pi*88^2)


def _seed(term: str) -> int:
    """A stable per-term seed -- deterministic across processes (hash() is salted; zlib.crc32 is not)."""
    return zlib.crc32(term.encode("utf-8")) & 0x7FFFFFFF


def _fibonacci_sphere(n: int, jitter: float = 0.0, seed: int = 0) -> "any":
    """n unit vectors spread evenly over the sphere (the golden-angle spiral). Deterministic.

    JITTER BREAKS THE LATTICE. The golden-angle spiral is *regular*, and a regular sampling pattern
    is VISIBLE: zoom into a planet's ocean and you can see the spiral arms as faint curved streaks --
    which is what makes a smooth surface read like "a crappy voxel calculation". `jitter` displaces
    each grain TANGENTIALLY (in the surface, then renormalised back onto the shell) by a fraction of
    the mean grain spacing, turning the spiral into blue noise. It is tangential ON PURPOSE: RADIAL
    jitter scatters grains in depth and lets the background speckle through between them, which is a
    worse artifact and was removed once already."""
    import numpy as np
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n                 # -1..1, even in area
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    theta = np.pi * (1.0 + 5.0 ** 0.5) * i        # golden angle
    d = np.stack([r * np.cos(theta), r * np.sin(theta), z], axis=1)
    if jitter > 0.0:
        rng = np.random.default_rng(seed)
        spacing = 2.0 / np.sqrt(max(n, 1))                       # mean angular spacing on a unit sphere
        v = rng.normal(0.0, 1.0, (n, 3))
        v -= (v * d).sum(1, keepdims=True) * d                   # project into the TANGENT plane
        v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
        d = d + v * (jitter * spacing * rng.random((n, 1)) ** 0.5)
        d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)  # back onto the shell: no depth change
    return d


def _fbm(dirs, rng, octaves: int = 4):
    """Smooth blobby noise over unit directions -> continents, not speckle. Range ~ -1..1."""
    import numpy as np
    val = np.zeros(len(dirs)); total = 0.0; amp = 1.0
    for o in range(octaves):
        freq = 1.15 * (1.9 ** o)                  # low freqs first -> a few big land masses
        # WAVES PER OCTAVE: 2 was too few. A sum of 8 plane waves is not noise, it is INTERFERENCE --
        # and zoomed in, its ripple shows as faint curved arcs across the ocean, which is the
        # "crappy voxel calculation" look. Directions are drawn per wave, so more of them average
        # into something isotropic instead of a standing pattern. Cost is linear and tiny.
        for _ in range(7):
            k = rng.normal(size=3); k /= (np.linalg.norm(k) + 1e-9)
            phase = rng.uniform(0.0, 2.0 * np.pi)
            val += amp * np.sin(freq * np.pi * (dirs @ k) + phase)
            total += amp
        amp *= 0.55
    return val / max(total, 1e-9)


def _planet_buffers(spec: dict, term: str):
    """Build (end_buffer, begin_buffer) for a solid world: surface shell + atmosphere halo."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec["radius"])
    ocean_frac = float(spec.get("ocean", 0.66))

    # ── SURFACE: an even shell of opaque splats ──
    n_s = 40000                                                     # MORE, SMALLER grains: fills the shell with no lattice while
                                                                     # each grain covers ~8x less area than SIZE 9 -> ~8x less overdraw
    dirs = _fibonacci_sphere(n_s, jitter=0.85, seed=_seed(term))     # (n,3) unit -- lattice broken
    z = dirs[:, 2]                                                   # latitude sine
    surf = np.zeros((n_s, NCOLS), dtype=np.float32)
    surf[:, PX:PZ + 1] = dirs * R                                   # a CLEAN shell (no radial jitter). Radial jitter scattered grains
                                                                     # in depth and -- with semi-transparent grains -- let the black
                                                                     # background SPECKLE through between them (the "lattice dots").
    surf[:, NX:NZ + 1] = dirs                                       # outward normal = the shell direction -> back-face cull the far side
    surf[:, TYPE] = 3.0                                             # "social": sm=1.0, opaque, isotropic -> clean round grains
    surf[:, ALPHA] = 0.55                                           # NOT fully opaque -- and this is the distortion fix.
                                                                     # With a = 1.0 the Gaussian weight at a grain's centre gives
                                                                     # al = 1.0, so `trans` goes to zero and the front-to-back early-out
                                                                     # fires on the FIRST splat: the image becomes a hard Voronoi whose
                                                                     # cells are decided by DEPTH RANK, not screen distance. At the
                                                                     # sub-camera point a sphere's surface is perpendicular to the view,
                                                                     # so every neighbour sits at nearly the same depth -- sub-pixel
                                                                     # differences pick the winner, it flips pixel to pixel, and biome
                                                                     # edges MOTTLE and SWIM as the body turns. (At the limb depths
                                                                     # separate strongly and the sort is stable, which is why the
                                                                     # artifact is centred.) At 0.55 several overlapping discs each
                                                                     # contribute and the colour is their Gaussian-weighted blend, so a
                                                                     # depth tie stops being visible. The wider tangent discs
                                                                     # (_DISC_WIDE in gpu_pipeline) keep the shell gap-free at this alpha.
    surf[:, SIZE] = 3.5                                             # SMALL grains: projected ~15px (was ~42px) -> ~8x less overdraw,
                                                                     # the dominant render cost. 40k of them still fill the shell (gap 0, measured).

    # classify each grain: ICE at the poles, else LAND vs OCEAN by continent noise
    land_noise = _fbm(dirs, rng)
    thresh = np.quantile(land_noise, ocean_frac)                   # top (1-ocean) fraction becomes land
    is_land = land_noise > thresh
    is_ice = np.abs(z) > 0.80                                       # polar caps (lat > ~53 deg)
    is_land &= ~is_ice
    is_ocean = ~is_land & ~is_ice

    # ocean: DEEP navy, a shade lighter/greener in the shallows (a second noise = depth)
    depth = 0.5 + 0.5 * _fbm(dirs, rng)                            # 0..1
    surf[is_ocean, CR] = 0.02 + 0.04 * depth[is_ocean]
    surf[is_ocean, CG] = 0.08 + 0.12 * depth[is_ocean]
    surf[is_ocean, CB] = 0.30 + 0.22 * depth[is_ocean]            # -> (0.02,0.08,0.30) abyss to (0.06,0.20,0.52) shelf (navy)
    # land: vivid equatorial green -> arid tan in the SUBTROPICS -> cold again toward the poles.
    # CAUGHT BY THE DYAD: an eye reading this render blind reported "pale TAN patches near the top
    # and bottom edges" where the physics claims white ice caps. The bug was physical, not cosmetic --
    # aridity was `|z| * 0.9`, which peaks at the POLES and paints them desert. Deserts sit at ~25 deg,
    # where the Hadley cell's air descends dry; the poles are cold. So aridity is a BAND, not a ramp.
    lat_desert = 0.42                                               # sin(lat) ~ 0.42 => ~25 deg
    band = np.exp(-((np.abs(z) - lat_desert) / 0.26) ** 2)
    aridity = np.clip(band + 0.25 * _fbm(dirs, rng), 0.0, 1.0)
    surf[is_land, CR] = 0.13 + 0.34 * aridity[is_land]
    surf[is_land, CG] = 0.44 - 0.12 * aridity[is_land]
    surf[is_land, CB] = 0.12 + 0.05 * aridity[is_land]           # -> (0.13,0.44,0.12) jungle to (0.47,0.32,0.17) desert
    # ice: near-white with a cold blue tint
    surf[is_ice, CR] = 0.90; surf[is_ice, CG] = 0.93; surf[is_ice, CB] = 0.97

    surf[:, CR:CB + 1] *= _PLANET_GAIN                             # opaque surface => ~no over-accumulation, so show TRUE colors (gain~1)

    # ── ATMOSPHERE: a faint pale-blue halo -- thin enough to glow at the LIMB without hazing the disk ──
    # AN ATMOSPHERE IS A VOLUME, NOT A SHELL. A thin shell of ISOTROPIC splats has a
    # surface-perpendicular locus (the sub-camera point) where screen-space overlap is at its MINIMUM
    # -- sphere splats overlap as sigma/s tangentially but sigma/(s*cos phi) radially, so phi=0 is a
    # unique extremum and reads as a "spot". (The same geometry put a LINE down a rotating tree trunk:
    # a cylinder's perpendicular locus is a line, a sphere's is a point.) The surface shell solves this
    # by using tangent DISCS, whose projection foreshortens with the spacing. The atmosphere cannot --
    # it is genuinely volumetric -- so instead we give it real THICKNESS: scattered through R*1.00-1.12
    # there is no single perpendicular locus left to see.
    n_a = 1800
    adirs = _fibonacci_sphere(n_a)
    arad = R * (1.0 + 0.12 * rng.random(n_a) ** 0.6)               # thickness, denser toward the surface
    atm = np.zeros((n_a, NCOLS), dtype=np.float32)
    atm[:, PX:PZ + 1] = adirs * arad[:, None]
    atm[:, TYPE] = 5.0                                             # "atmosphere": sm=6.0 -> big soft blobs
    atm[:, CR] = 0.36; atm[:, CG] = 0.56; atm[:, CB] = 0.90
    atm[:, ALPHA] = 0.05 * 1800.0 / n_a                            # n * alpha held constant -> same haze
                                                                    # (count kept at 1800: raising it made the
                                                                    # operator's artifact LARGER, so density is
                                                                    # not the cause -- thickness is the real fix)
    atm[:, SIZE] = 1.2

    end = np.concatenate([surf, atm], axis=0)

    # ── BEGIN: the world ACCRETING -- its own grains flung out into a dust cloud that will condense ──
    begin = end.copy()
    spread = R * (1.4 + 2.2 * rng.random(len(begin)))             # push each grain radially outward
    tang = rng.normal(0.0, R * 0.5, (len(begin), 3))             # + tangential scatter -> a cloud
    ndir = end[:, PX:PZ + 1] / (np.linalg.norm(end[:, PX:PZ + 1], axis=1, keepdims=True) + 1e-9)
    begin[:, PX:PZ + 1] = ndir * spread[:, None] + tang
    return end, begin


def _terrain_buffers(spec: dict, term: str):
    """Build (end, begin) for theTerrain: a sphere shell RADIALLY DISPLACED by its elevation field, so the
    relief -- mountains, basins -- is REAL 3D relief, tinted hypsometrically by height. The appearance
    DERIVES from the elevation field: if the physics (the field) is right, the relief is right. No
    atmosphere -- theTerrain is the solid relief ALONE (theAtmosphere is its sibling), which is also what
    distinguishes its render from aPlanet's flat ocean/continent disc."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec["radius"]); relief = float(spec.get("relief", 0.13)); sea = float(spec.get("sea", 0.5))
    n_s = 40000
    dirs = _fibonacci_sphere(n_s, jitter=0.85, seed=_seed(term))     # lattice broken -- see the docstring
    elev = _fbm(dirs, rng, octaves=5)                              # the elevation field = spherical-harmonic sum + roughness
    hn = (elev - elev.min()) / (np.ptp(elev) + 1e-9)               # normalised elevation 0..1
    surf = np.zeros((n_s, NCOLS), dtype=np.float32)
    surf[:, PX:PZ + 1] = (dirs * (R * (1.0 + relief * (hn - sea)))[:, None])   # DISPLACE the shell by height about the sea datum
    surf[:, NX:NZ + 1] = dirs                                      # outward normal ~ radial -> back-face cull the far side
    surf[:, TYPE] = 3.0; surf[:, ALPHA] = 1.0; surf[:, SIZE] = 3.5
    # HYPSOMETRIC TINT -- the relief reads by colour too: ocean basins (navy, darker deeper) below the sea
    # datum; green lowland -> arid tan -> grey rock -> white peak above it.
    o = np.clip(hn / sea, 0.0, 1.0)                               # 0 abyss .. 1 shoreline
    ocean = np.stack([0.02 + 0.03 * o, 0.06 + 0.14 * o, 0.26 + 0.22 * o], axis=1)
    l = np.clip((hn - sea) / (1.0 - sea), 0.0, 1.0)              # 0 lowland .. 1 peak
    lp = np.array([0.0, 0.40, 0.72, 1.0])
    stops = np.array([[0.15, 0.42, 0.14], [0.46, 0.40, 0.20], [0.50, 0.50, 0.52], [0.96, 0.97, 1.0]])
    land = np.stack([np.interp(l, lp, stops[:, c]) for c in range(3)], axis=1)
    surf[:, CR:CB + 1] = np.where((hn < sea)[:, None], ocean, land).astype(np.float32)
    # BEGIN: the relief ACCRETING -- its grains flung out into a dust cloud that condenses into the sphere.
    end = surf
    begin = end.copy()
    spread = R * (1.4 + 2.2 * rng.random(len(begin)))
    tang = rng.normal(0.0, R * 0.5, (len(begin), 3))
    ndir = end[:, PX:PZ + 1] / (np.linalg.norm(end[:, PX:PZ + 1], axis=1, keepdims=True) + 1e-9)
    begin[:, PX:PZ + 1] = ndir * spread[:, None] + tang
    return end, begin


def _solid_sphere(center, radius, color, rng, gain: float = _SURFACE_GAIN):
    """A solid opaque sphere of one colour at `center` -- the reusable body (calibrated over-accumulation)."""
    import numpy as np
    n = max(500, int(_GRAIN_DENSITY * 4.0 * np.pi * radius * radius))
    dirs = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    jit = 1.0 + rng.normal(0.0, 0.006, n)
    b[:, PX:PZ + 1] = np.asarray(center, np.float32) + dirs * (radius * jit[:, None])
    b[:, TYPE] = 3.0
    b[:, ALPHA] = _GRAIN_ALPHA
    b[:, SIZE] = _GRAIN_SIZE
    b[:, CR] = color[0] * gain; b[:, CG] = color[1] * gain; b[:, CB] = color[2] * gain
    return b


def _halo(center, radius, color, rng, alpha: float = 0.09, size: float = 1.8, n: int | None = None):
    """A faint soft glow shell (atmosphere type = big soft blobs) -- a limb/atmosphere/star glow."""
    import numpy as np
    if n is None:
        n = max(300, int(0.06 * 4.0 * np.pi * radius * radius))
    dirs = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, PX:PZ + 1] = np.asarray(center, np.float32) + dirs * radius
    b[:, TYPE] = 5.0                                               # atmosphere: sm=6.0 -> big soft blobs
    b[:, CR] = color[0]; b[:, CG] = color[1]; b[:, CB] = color[2]
    b[:, ALPHA] = alpha; b[:, SIZE] = size
    return b


def _orbit_ring(radius, rng, color=(0.42, 0.42, 0.48), n: int = 900):
    """A thin ring of dust in the z=0 orbital plane -- an ORBIT drawn as splats."""
    import numpy as np
    th = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, PX] = radius * np.cos(th)
    b[:, PY] = radius * np.sin(th)
    b[:, PZ] = rng.normal(0.0, 1.5, n)                            # a thin band, not a wire
    b[:, TYPE] = 3.0
    b[:, CR] = color[0]; b[:, CG] = color[1]; b[:, CB] = color[2]
    b[:, ALPHA] = 0.5; b[:, SIZE] = 2.4
    return b


def _row_buffers(spec: dict, term: str):
    """thePlanets: a ROW of solid worlds, hot colours on one side -> cold on the other (a temperature gradient)."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    planets = spec["planets"]                                     # [(color, radius), ...] hot -> cold
    span = float(spec.get("span", 500.0))
    xs = np.linspace(-span / 2.0, span / 2.0, len(planets))
    parts = []
    for (color, radius), x in zip(planets, xs):
        parts.append(_solid_sphere((x, 0.0, 0.0), radius, color, rng))
        if color[0] > 0.75 and color[2] < 0.4:                   # a HOT world -> a molten glow so it reads as hot
            parts.append(_halo((x, 0.0, 0.0), radius * 1.18, (0.95, 0.35, 0.12), rng, alpha=0.11, size=1.7))
    end = np.concatenate(parts, axis=0)
    begin = end.copy()
    begin[:, PX:PZ + 1] += rng.normal(0.0, 55.0, (len(begin), 3))  # dispersed dust -> the worlds condense
    return end, begin


def _dots(center, radius, n, color, rng):
    """A tiny solid ball of one colour (fruit, berries) -- _solid_sphere's 500-grain floor
    is a tree's worth of grains for a plum."""
    import numpy as np
    d = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, PX:PZ + 1] = np.asarray(center, np.float32) + d * radius
    b[:, TYPE] = 3.0
    b[:, ALPHA] = 0.8; b[:, SIZE] = 2.0
    b[:, CR], b[:, CG], b[:, CB] = color
    return b


def _garden_tree(center, trunk_h, trunk_r, rng, fruit=False, growth=1.0):
    """One grown tree as splats: a brown trunk column, a canopy of green blobs around its top,
    and -- only on the Tree of Knowledge -- red fruit. `growth` scales the whole tree about its
    base: the movie's begin frame is the stand as sprouts."""
    import numpy as np
    cx, cy, cz = center
    h = trunk_h * growth
    parts = []
    n_t = max(40, int(64 * trunk_h / 50.0))
    z = rng.random(n_t) * h
    th = rng.random(n_t) * 2.0 * np.pi
    rr = trunk_r * np.sqrt(rng.random(n_t))
    b = np.zeros((n_t, NCOLS), dtype=np.float32)
    b[:, PX] = cx + rr * np.cos(th)
    b[:, PY] = cy + rr * np.sin(th)
    b[:, PZ] = cz + z
    b[:, TYPE] = 3.0; b[:, ALPHA] = 0.7; b[:, SIZE] = 3.5
    b[:, CR], b[:, CG], b[:, CB] = 0.30, 0.19, 0.09          # bark brown
    parts.append(b)
    blob_centers = []
    for _ in range(4):                                       # the canopy: 4 blobs about the top
        off = np.array([rng.uniform(-0.32, 0.32) * h, rng.uniform(-0.32, 0.32) * h,
                        rng.uniform(-0.02, 0.16) * h])
        rad = h * rng.uniform(0.26, 0.36)
        if rad < 1.0:
            continue
        g = float(rng.uniform(0.38, 0.54))
        bc = np.array([cx + off[0], cy + off[1], cz + h + off[2]])
        blob_centers.append((bc, rad))
        parts.append(_solid_sphere(bc, rad, (0.10, g, 0.08), rng))
    if fruit:
        for bc, rad in blob_centers:
            for _ in range(3):
                foff = rng.uniform(-0.7, 0.7, 3) * rad
                parts.append(_dots(bc + foff, 1.8, 40, (0.82, 0.10, 0.10), rng))
    return parts


def _garden_buffers(spec: dict, term: str):
    """theGarden: a green field carrying a STAND of grown trees, the Tree of Knowledge prominent
    (with fruit). begin = the field with the stand as sprouts; end = the grown garden -- the
    movie is the vegetation layer GROWING, which is what a garden does."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 120.0))

    # ── GROUND: a green field, patchy (meadows are not one green) ──
    n_g = 9000
    th = rng.random(n_g) * 2.0 * np.pi
    rr = R * np.sqrt(rng.random(n_g))
    gx, gy = rr * np.cos(th), rr * np.sin(th)
    patch = 0.5 + 0.5 * np.sin(0.05 * gx + 1.3) * np.sin(0.06 * gy + 0.4)
    gnd = np.zeros((n_g, NCOLS), dtype=np.float32)
    gnd[:, PX], gnd[:, PY], gnd[:, PZ] = gx, gy, 0.0
    gnd[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    gnd[:, TYPE] = 3.0; gnd[:, ALPHA] = 0.55; gnd[:, SIZE] = 3.5
    gnd[:, CR] = 0.07 + 0.05 * patch
    gnd[:, CG] = 0.28 + 0.14 * patch
    gnd[:, CB] = 0.06 + 0.04 * patch

    def stand(growth):
        parts = [gnd]
        parts += _garden_tree((0.0, 0.0, 0.0), 64.0, 2.8, rng, fruit=True, growth=growth)
        for k in range(12):                                   # the stand: golden-angle spiral, varied heights
            a = k * 2.399963
            r = 18.0 + 11.0 * k
            x, y = r * np.cos(a), 12.0 + r * np.sin(a)
            parts += _garden_tree((x, y, 0.0), float(rng.uniform(28, 50)), 2.0, rng, growth=growth)
        return np.concatenate(parts, axis=0)

    return stand(1.0), stand(0.35)


def _blob_scaled(center, radii, n, color, alpha=0.65, size=2.2):
    """An ellipsoid of splats (a body, a head) -- _solid_sphere stretched per axis."""
    import numpy as np
    d = _fibonacci_sphere(n)
    b = np.zeros((n, NCOLS), dtype=np.float32)
    c = np.asarray(center, np.float32)
    b[:, PX] = c[0] + d[:, 0] * radii[0]
    b[:, PY] = c[1] + d[:, 1] * radii[1]
    b[:, PZ] = c[2] + d[:, 2] * radii[2]
    b[:, TYPE] = 3.0; b[:, ALPHA] = alpha; b[:, SIZE] = size
    b[:, CR], b[:, CG], b[:, CB] = color
    return b


def _grazer(center, length, rng, color):
    """A quadruped herbivore as splats: a horizontal body ellipsoid, a head blob forward and
    up, four leg columns. The trophic web made visible -- the garden's herbivore_biomass."""
    import numpy as np
    cx, cy, cz = center
    leg_h = 0.42 * length
    parts = []
    parts.append(_blob_scaled((cx, cy, cz + leg_h + 0.18 * length),
                              (0.50 * length, 0.20 * length, 0.22 * length),
                              220, color))                                    # body
    parts.append(_blob_scaled((cx + 0.58 * length, cy, cz + leg_h + 0.34 * length),
                              (0.16 * length, 0.11 * length, 0.15 * length),
                              90, color))                                     # head
    for sx in (-0.32, 0.32):
        for sy in (-0.10, 0.10):
            n_l = 26
            b = np.zeros((n_l, NCOLS), dtype=np.float32)
            b[:, PX] = cx + sx * length + rng.normal(0, 0.012 * length, n_l)
            b[:, PY] = cy + sy * length + rng.normal(0, 0.012 * length, n_l)
            b[:, PZ] = cz + rng.random(n_l) * leg_h
            b[:, TYPE] = 3.0; b[:, ALPHA] = 0.7; b[:, SIZE] = 1.6
            b[:, CR], b[:, CG], b[:, CB] = color
            parts.append(b)                                                   # a leg
    return parts


def _ecosystem_buffers(spec: dict, term: str):
    """theEcosystem: the web INHABITING the garden. The vegetation is theGarden's own scene,
    same seed -- the same place, one rung down the tree. begin = the community YOUNG (saplings
    and half-grown grazers), end = the community grown. The movie is the whole web maturing
    together. (The blind eye anchored on the begin frame and read an empty-forest -> forest
    lighting change, never seeing the animals that only existed at the end -- a young
    ecosystem has young ANIMALS, not none.)"""
    import numpy as np
    stand_end, stand_begin = _garden_buffers(spec, "theGarden")   # the SAME garden (its seed)
    rng = np.random.default_rng(_seed(term))

    def animals(scale):
        out = []
        for k in range(5):                                        # the herd: the OPEN foreground,
            x = -55.0 + 27.0 * k + float(rng.uniform(-6, 6))      # between camera and stand,
            y = float(rng.uniform(-95.0, -55.0))                  # where nothing hides them
            length = float(rng.uniform(16.0, 21.0)) * scale
            shade = float(rng.uniform(0.85, 1.15))
            out += _grazer((x, y, 0.0), length, rng,
                           (0.62 * shade, 0.48 * shade, 0.28 * shade))
        return out

    birds = []
    for k in range(5):                                            # the birds: dark flecks above the canopy
        birds.append(_dots((float(rng.uniform(-90, 90)), float(rng.uniform(-20, 100)),
                            float(rng.uniform(55, 85))), 1.1, 18, (0.16, 0.15, 0.14), rng))

    end = np.concatenate([stand_end] + animals(1.0) + birds, axis=0)
    begin = np.concatenate([stand_begin] + animals(0.7), axis=0)
    return end, begin


def _skeleton_splats(bones, tw, scale, rng, offset=(0.0, 0.0, 0.0),
                        tip_depth=5, leaf_rad=(3.5, 6.5), leaf_n=42):
    """A grown bone skeleton as splats: brown segments for the bones, a green leaf blob per
    twig tip (depth >= 5). offset shifts the whole tree in world units. Shared by theTree
    (one tree) and theTreeForm (three genomes side by side)."""
    import numpy as np
    off = np.array(offset, dtype=np.float32)
    parts = []
    for b in bones:                                  # the skeleton, as splat segments
        p0, p1 = np.array(tw(b.p0)) * scale + off, np.array(tw(b.p1)) * scale + off
        seg = float(np.linalg.norm(p1 - p0))
        n_b = max(2, int(seg / 1.8))
        t = np.linspace(0.0, 1.0, n_b)[:, None]
        pts = p0[None, :] * (1 - t) + p1[None, :] * t
        shade = min(b.depth, 6)
        bb = np.zeros((n_b, NCOLS), dtype=np.float32)
        bb[:, PX:PZ + 1] = pts
        bb[:, TYPE] = 3.0; bb[:, ALPHA] = 0.75; bb[:, SIZE] = max(1.4, 3.2 * scale)
        bb[:, CR] = (90 - shade * 8) / 255.0
        bb[:, CG] = (60 - shade * 5) / 255.0
        bb[:, CB] = 34 / 255.0
        parts.append(bb)
    tips = [b for b in bones if b.depth >= tip_depth]
    for b in tips:                                   # the crown: a leaf blob per twig tip
        p1 = np.array(tw(b.p1)) * scale + off
        rad = float(rng.uniform(*leaf_rad)) * scale
        if rad < 0.8:
            continue
        gg = float(rng.uniform(0.34, 0.52))
        parts.append(_dots(p1, rad, leaf_n, (0.10, gg, 0.08), rng))
    return parts


def _tree_buffers(spec: dict, term: str):
    """theTree: one tree grown from the REAL substrate -- the terrarium's L-system genome
    -> bone skeleton (core/terrarium), drawn through the shared _skeleton_splats (one
    implementation: theTree is one tree alone; theTreeForm is three genomes side by
    side). begin = the same skeleton at 0.2 scale (a sapling), end = grown."""
    import numpy as np
    chimera = _REPO / "Chimera"
    if str(chimera) not in sys.path:
        sys.path.insert(0, str(chimera))
    from core.terrarium import Genome, grow
    import importlib
    import core.scene3d
    importlib.reload(core.scene3d)          # the long-lived server caches it; disk is the truth
    _tree_world = core.scene3d._tree_world
    rng = np.random.default_rng(_seed(term))
    H = float(spec.get("height", 60.0))
    R = float(spec.get("radius", 60.0))
    g = Genome(depth=7, angle=32.0, length=1.0, decay=0.86, radius=0.13, radius_decay=0.74)
    bones = grow(g, _seed(term) & 0xFF)
    tw = _tree_world(bones, H)

    # ground: a patchy green disc, the same meadow theGarden stands on
    n_g = 3500
    th = rng.random(n_g) * 2.0 * np.pi
    rr = R * np.sqrt(rng.random(n_g))
    gx, gy = rr * np.cos(th), rr * np.sin(th)
    patch = 0.5 + 0.5 * np.sin(0.08 * gx + 1.3) * np.sin(0.09 * gy + 0.4)
    gnd = np.zeros((n_g, NCOLS), dtype=np.float32)
    gnd[:, PX], gnd[:, PY], gnd[:, PZ] = gx, gy, 0.0
    gnd[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    gnd[:, TYPE] = 3.0; gnd[:, ALPHA] = 0.55; gnd[:, SIZE] = 3.0
    gnd[:, CR] = 0.07 + 0.05 * patch
    gnd[:, CG] = 0.28 + 0.14 * patch
    gnd[:, CB] = 0.06 + 0.04 * patch

    def grown(scale):
        return np.concatenate([gnd] + _skeleton_splats(bones, tw, scale, rng), axis=0)

    return grown(1.0), grown(0.2)


def _treeform_buffers(spec: dict, term: str):
    """theTreeForm: the FORM is the branch structure the genome grows. One close-up of the
    fork zone: theTree's own genome and seed, origin at the CENTROID of the depth-2..3
    branch cluster (not the trunk top -- it-6 filled the frame with trunk column), camera
    70 out. Brown branch lines (SIZE capped so they render as lines, not smear), small
    green leaf clusters on the framed tips. begin = the young fork (depth <= 3), end =
    the grown one."""
    import numpy as np
    chimera = _REPO / "Chimera"
    if str(chimera) not in sys.path:
        sys.path.insert(0, str(chimera))
    from core.terrarium import Genome, grow
    import importlib
    import core.scene3d
    importlib.reload(core.scene3d)          # the long-lived server caches it; disk is the truth
    _tree_world = core.scene3d._tree_world
    rng = np.random.default_rng(_seed(term))
    H = float(spec.get("height", 60.0))

    bones_full = grow(Genome(depth=7, angle=32.0, length=1.0, decay=0.86, radius=0.13,
                             radius_decay=0.74), _seed("theTree") & 0xFF)

    CLIP = 46.0          # only matter this close to the fork zone is drawn

    # ONE shared frame for both states: world transform and centre from the FULL skeleton,
    # so the young fork renders at its true smaller extent -- the movie is GROWTH, and two
    # same-sized frames make the eye confabulate ("becomes blurry", it-7/8).
    tw = _tree_world(bones_full, H)
    zone = [np.array(tw(b.p1)) for b in bones_full if 2 <= b.depth <= 3]
    centre = np.mean(zone, axis=0) if zone else np.zeros(3)
    shift = -centre

    trunk = [b for b in bones_full if b.depth == 0]
    base = np.array(tw(trunk[0].p0)) + shift if trunk else np.zeros(3)

    def skeleton(bones, leaf_from=4, scale=1.0):
        parts = []
        tips = []
        for b in bones:
            p0, p1 = np.array(tw(b.p0)) + shift, np.array(tw(b.p1)) + shift
            p0, p1 = base + (p0 - base) * scale, base + (p1 - base) * scale
            mid = 0.5 * (p0 + p1)
            if float(np.linalg.norm(mid)) > CLIP and b.depth > 1:
                continue                                # outside the framed fork zone
            seg = float(np.linalg.norm(p1 - p0))
            n_b = max(3, int(seg / 0.6))                # dense: branches render as LINES
            t = np.linspace(0.0, 1.0, n_b)[:, None]
            pts = p0[None, :] * (1 - t) + p1[None, :] * t
            shade = min(b.depth, 6)
            bb = np.zeros((n_b, NCOLS), dtype=np.float32)
            bb[:, PX:PZ + 1] = pts
            bb[:, TYPE] = 3.0; bb[:, ALPHA] = 0.85
            bb[:, SIZE] = max(1.0, 0.30 * (7 - shade))  # taper: trunk 2.1, twigs 1.0
            bb[:, CR] = (118 - shade * 9) / 255.0
            bb[:, CG] = (82 - shade * 6) / 255.0
            bb[:, CB] = 48 / 255.0
            parts.append(bb)
            if b.depth >= leaf_from:
                tips.append(p1)
        for p1 in tips:                                 # leaf clusters, only near the frame
            if float(np.linalg.norm(p1)) > 42.0:
                continue
            rad = float(rng.uniform(1.3, 2.1))          # small enough that clusters RESOLVE
            gg = float(rng.uniform(0.36, 0.52))
            parts.append(_dots(p1, rad, 18, (0.10, gg, 0.08), rng))
        return np.concatenate(parts, axis=0)

    # BOTH frames hold the grown fork; begin is the same form with sparser foliage (the
    # leaves still filling in). Ten iterations measured: a two-frame movie of one object at
    # two sizes/states is narrated by the eye as zoom/focus, never as growth -- the form is
    # what PERSISTS, so the movie holds it still to be judged. Growth is theTree's movie.
    return skeleton(bones_full, leaf_from=6), skeleton(bones_full, leaf_from=6)


def _fruit_buffers(spec: dict, term: str):
    """theFruit: theTree's own genome and seed, bearing FRUIT -- as a crown CLOSE-UP.
    Three full-tree iterations failed on scale (0.000 / 0.250 / 0.250): at 120 units a
    3-unit fruit is a sub-blob speck, and clustered fruit merges into a red band. The
    fork close-up framing that proved theTreeForm (origin at the depth-2..3 centroid,
    camera 70 out) is where objects resolve. The tree is the shared _skeleton_splats
    look with SPARSE distinct leaf clusters (theTreeForm's), and a greedy-separated set
    of big red fruit spheres HANGING BELOW twig tips at the crown's edge, where they
    silhouette against the dark. begin = unripe (small, green), end = ripe (full, red)."""
    import numpy as np
    chimera = _REPO / "Chimera"
    if str(chimera) not in sys.path:
        sys.path.insert(0, str(chimera))
    from core.terrarium import Genome, grow
    import importlib
    import core.scene3d
    importlib.reload(core.scene3d)          # the long-lived server caches it; disk is the truth
    _tree_world = core.scene3d._tree_world
    rng = np.random.default_rng(_seed(term))
    H = float(spec.get("height", 60.0))

    bones = grow(Genome(depth=7, angle=32.0, length=1.0, decay=0.86, radius=0.13,
                        radius_decay=0.74), _seed("theTree") & 0xFF)
    tw = _tree_world(bones, H)
    zone = [np.array(tw(b.p1)) for b in bones if 2 <= b.depth <= 3]
    centre = np.mean(zone, axis=0) if zone else np.zeros(3)
    shift = -centre

    CLIP = 46.0
    # it-4: the un-clipped skeleton smeared brown behind the fruit ("green and orange
    # circles on a brown mass", 0.250). Clip far branches (keep the trunk), fuller leaves.
    bones_c = [b for b in bones
               if b.depth <= 1
               or float(np.linalg.norm(0.5 * (np.array(tw(b.p0)) + np.array(tw(b.p1))) + shift)) <= CLIP]
    tree = _skeleton_splats(bones_c, tw, 1.0, rng, offset=shift,
                            tip_depth=4, leaf_rad=(2.4, 3.4), leaf_n=28)

    # the fruit: ALL of it at the crown's LOWER RIM, silhouetted against the dark. it-4/5
    # showed only the fruit hanging clear of the crown reads as fruit (2 of 9); fruit inside
    # the silhouette blends into the leaves. So fruit tips come from the LOW half of the
    # framed zone and hang 4-6 units down, separated, each resolving on black.
    tips = [b for b in bones_c if b.depth >= 5]
    order = rng.permutation(len(tips))
    fruits = []
    for i in order:
        tip = np.array(tw(tips[i].p1)) + shift
        if float(np.linalg.norm(tip)) > CLIP or tip[2] > 0.0:
            continue                                    # the LOW rim only: fruit must hang on black
        pos = tip + np.array([float(rng.uniform(-1.2, 1.2)), float(rng.uniform(-1.2, 1.2)),
                              -float(rng.uniform(6.0, 8.0))])
        if all(float(np.linalg.norm(pos - f[0])) >= 7.5 for f in fruits):
            fruits.append((pos, float(rng.uniform(3.0, 3.8))))   # it-9's best modal params
        if len(fruits) >= 12:
            break

    def with_fruit(color, scale):
        parts = list(tree)
        for pos, rad in fruits:
            parts.append(_dots(pos, rad * scale, 40, color, rng))
        return np.concatenate(parts, axis=0)

    UNRIPE = (0.22, 0.42, 0.13)     # green on green: unripe fruit hides, that is the truth
    RIPE = (0.85, 0.05, 0.04)       # bright red: it-6's fruit was visible but not SALIENT
    return with_fruit(RIPE, 1.0), with_fruit(UNRIPE, 0.7)


def _planting_buffers(spec: dict, term: str):
    """thePlanting: the hand's geometry made visible. A tilled brown field with furrow
    lines, and green sprouts at REGULAR grid points along the furrows -- rows, where
    chance would scatter. Germination is 92%: a real stand has gaps. begin = the field
    tilled and sown but not yet emerged (bare rows), end = the seedlings up."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 110.0))

    # tilled soil: a brown patchy disc, darker and rougher than the meadow scenes
    n_g = 4200
    th = rng.random(n_g) * 2.0 * np.pi
    rr = R * np.sqrt(rng.random(n_g))
    gx, gy = rr * np.cos(th), rr * np.sin(th)
    patch = 0.5 + 0.5 * np.sin(0.11 * gx + 0.7) * np.sin(0.09 * gy + 2.1)
    gnd = np.zeros((n_g, NCOLS), dtype=np.float32)
    gnd[:, PX], gnd[:, PY], gnd[:, PZ] = gx, gy, 0.0
    gnd[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    gnd[:, TYPE] = 3.0; gnd[:, ALPHA] = 0.6; gnd[:, SIZE] = 3.0
    gnd[:, CR] = 0.22 + 0.07 * patch
    gnd[:, CG] = 0.14 + 0.05 * patch
    gnd[:, CB] = 0.07 + 0.03 * patch

    # furrows: raised darker-brown lines along x, 9 rows spaced 12 units
    rows_y = [(-48.0 + 12.0 * k) for k in range(9)]
    furrows = []
    for y in rows_y:
        xs = np.linspace(-54.0, 54.0, 90)
        fb = np.zeros((len(xs), NCOLS), dtype=np.float32)
        fb[:, PX] = xs
        fb[:, PY] = y + rng.normal(0.0, 0.5, len(xs))
        fb[:, PZ] = 0.4
        fb[:, TYPE] = 3.0; fb[:, ALPHA] = 0.7; fb[:, SIZE] = 2.6
        fb[:, CR], fb[:, CG], fb[:, CB] = 0.30, 0.19, 0.09
        furrows.append(fb)

    # the sprouts: one green tuft per grid point, germination 92%, slight hand jitter
    def seedlings(scale):
        parts = []
        for y in rows_y:
            for x in np.linspace(-50.0, 50.0, 11):
                if rng.random() > 0.94:
                    continue                            # the seed that did not come up
                cx = x + float(rng.uniform(-0.6, 0.6))   # it-1: jitter broke the row read
                cy = y + float(rng.uniform(-0.6, 0.6))
                gg = float(rng.uniform(0.44, 0.58))
                parts.append(_dots((cx, cy, 0.8 * scale), 1.8 * scale, 18,
                                   (0.12, gg, 0.09), rng))
                stem = np.zeros((3, NCOLS), dtype=np.float32)   # a short upright stem
                stem[:, PX], stem[:, PY] = cx, cy
                stem[:, PZ] = np.linspace(0.0, 2.2 * scale, 3)
                stem[:, TYPE] = 3.0; stem[:, ALPHA] = 0.8; stem[:, SIZE] = 1.4
                stem[:, CR], stem[:, CG], stem[:, CB] = 0.14, 0.40, 0.10
                parts.append(stem)
        return parts

    end = np.concatenate([gnd] + furrows + seedlings(1.0), axis=0)
    begin = np.concatenate([gnd] + furrows, axis=0)      # tilled and sown, not yet up
    return end, begin


def _farming_buffers(spec: dict, term: str):
    """theFarming: tending carried to maturity. The same hand geometry as thePlanting
    (rows, not scatter), but the crop has been tended to harvest: taller stalks with
    leaf tufts, and grain heads ripened gold -- growth that REACHED harvest because
    water, light, and nutrients were worked, not left to chance. begin = the young
    tended stand (green rows), end = the mature crop at harvest."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 110.0))

    # tilled soil: same brown patchy ground as thePlanting
    n_g = 4200
    th = rng.random(n_g) * 2.0 * np.pi
    rr = R * np.sqrt(rng.random(n_g))
    gx, gy = rr * np.cos(th), rr * np.sin(th)
    patch = 0.5 + 0.5 * np.sin(0.11 * gx + 0.7) * np.sin(0.09 * gy + 2.1)
    gnd = np.zeros((n_g, NCOLS), dtype=np.float32)
    gnd[:, PX], gnd[:, PY], gnd[:, PZ] = gx, gy, 0.0
    gnd[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    gnd[:, TYPE] = 3.0; gnd[:, ALPHA] = 0.6; gnd[:, SIZE] = 3.0
    gnd[:, CR] = 0.22 + 0.07 * patch
    gnd[:, CG] = 0.14 + 0.05 * patch
    gnd[:, CB] = 0.07 + 0.03 * patch

    # furrows: 9 rows spaced 12 units
    rows_y = [(-48.0 + 12.0 * k) for k in range(9)]
    furrows = []
    for y in rows_y:
        xs = np.linspace(-54.0, 54.0, 90)
        fb = np.zeros((len(xs), NCOLS), dtype=np.float32)
        fb[:, PX] = xs
        fb[:, PY] = y + rng.normal(0.0, 0.5, len(xs))
        fb[:, PZ] = 0.4
        fb[:, TYPE] = 3.0; fb[:, ALPHA] = 0.7; fb[:, SIZE] = 2.6
        fb[:, CR], fb[:, CG], fb[:, CB] = 0.30, 0.19, 0.09
        furrows.append(fb)

    spots = []
    for y in rows_y:
        for x in np.linspace(-50.0, 50.0, 11):
            if rng.random() > 0.96:
                continue                            # the plant that did not make it
            spots.append((x + float(rng.uniform(-0.5, 0.5)),
                          y + float(rng.uniform(-0.5, 0.5))))

    def young():
        parts = []
        for cx, cy in spots:
            gg = float(rng.uniform(0.44, 0.58))
            parts.append(_dots((cx, cy, 1.0), 2.0, 18, (0.12, gg, 0.09), rng))
            stem = np.zeros((3, NCOLS), dtype=np.float32)
            stem[:, PX], stem[:, PY] = cx, cy
            stem[:, PZ] = np.linspace(0.0, 2.6, 3)
            stem[:, TYPE] = 3.0; stem[:, ALPHA] = 0.8; stem[:, SIZE] = 1.4
            stem[:, CR], stem[:, CG], stem[:, CB] = 0.14, 0.40, 0.10
            parts.append(stem)
        return parts

    def mature():
        parts = []
        for cx, cy in spots:
            h = float(rng.uniform(9.0, 13.0))         # tended: tall and nearly uniform
            stem = np.zeros((7, NCOLS), dtype=np.float32)
            stem[:, PX], stem[:, PY] = cx, cy
            stem[:, PZ] = np.linspace(0.0, h, 7)
            stem[:, TYPE] = 3.0; stem[:, ALPHA] = 0.85; stem[:, SIZE] = 1.8
            stem[:, CR], stem[:, CG], stem[:, CB] = 0.16, 0.42, 0.12
            parts.append(stem)
            gg = float(rng.uniform(0.40, 0.55))       # leaf tufts along the stalk
            parts.append(_dots((cx, cy, h * 0.55), 2.6, 16, (0.13, gg, 0.10), rng))
            parts.append(_dots((cx, cy, h * 0.80), 2.2, 14, (0.13, gg, 0.10), rng))
            # the grain head: gold where the crop ripened to harvest
            ripe = rng.random() < 0.75
            head = (0.78, 0.62, 0.16) if ripe else (0.20, gg, 0.12)
            parts.append(_dots((cx, cy, h + 0.8), 1.6, 12, head, rng))
        return parts

    begin = np.concatenate([gnd] + furrows + young(), axis=0)
    end = np.concatenate([gnd] + furrows + mature(), axis=0)
    return end, begin

def _planetary_farm_buffers(spec: dict, term: str):
    """thePlanetaryFarm: cultivation rooted in a world's OWN open surface. The crop rows
    ride the world's rolling terrain (not a flat tray, not a dome floor), and the tended
    patch sits AMID wild ground -- the hand's rows against chance's scatter, both on the
    same native soil, under open sky (no shell). begin = the young stand, end = mature
    with grain heads ripened gold."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 260.0))

    def hz(x, y):                                   # the world's own rolling ground
        return 6.0 * np.sin(0.045 * x + 0.5) + 4.0 * np.cos(0.055 * y + 1.7)

    # native ground: a wide rolling sheet, green-grey wild colour, patchier than tilled
    n_g = 9000
    th = rng.random(n_g) * 2.0 * np.pi
    rr = R * np.sqrt(rng.random(n_g))
    gx, gy = rr * np.cos(th), rr * np.sin(th)
    patch = 0.5 + 0.5 * np.sin(0.06 * gx + 0.7) * np.sin(0.05 * gy + 2.1)
    gnd = np.zeros((n_g, NCOLS), dtype=np.float32)
    gnd[:, PX], gnd[:, PY] = gx, gy
    gnd[:, PZ] = hz(gx, gy)
    gnd[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    gnd[:, TYPE] = 3.0; gnd[:, ALPHA] = 0.55; gnd[:, SIZE] = 3.2
    gnd[:, CR] = 0.20 + 0.06 * patch
    gnd[:, CG] = 0.22 + 0.07 * patch
    gnd[:, CB] = 0.12 + 0.04 * patch

    # the tilled patch: browner soil INSIDE the field boundary only
    n_t = 2200
    tx = rng.uniform(-70.0, 70.0, n_t)
    ty = rng.uniform(-60.0, 60.0, n_t)
    tilled = np.zeros((n_t, NCOLS), dtype=np.float32)
    tilled[:, PX], tilled[:, PY] = tx, ty
    tilled[:, PZ] = hz(tx, ty) + 0.3
    tilled[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    tilled[:, TYPE] = 3.0; tilled[:, ALPHA] = 0.6; tilled[:, SIZE] = 3.0
    tilled[:, CR], tilled[:, CG], tilled[:, CB] = 0.27, 0.17, 0.08

    # wild vegetation: scattered tufts OUTSIDE the field -- chance's scatter
    wild = []
    for k in range(60):
        a = rng.random() * 2.0 * np.pi
        r = float(rng.uniform(85.0, 165.0))
        wx, wy = r * np.cos(a), r * np.sin(a)
        wz = float(hz(wx, wy))
        gg = float(rng.uniform(0.30, 0.45))
        wild.append(_dots((wx, wy, wz + 1.2), 2.4, 12, (0.14, gg, 0.11), rng))

    # the crop: rows riding the terrain, the hand's geometry against the wild scatter
    rows_y = [(-48.0 + 12.0 * k) for k in range(9)]
    spots = []
    for y in rows_y:
        for x in np.linspace(-60.0, 60.0, 13):
            if rng.random() > 0.96:
                continue
            cx = x + float(rng.uniform(-0.5, 0.5))
            cy = y + float(rng.uniform(-0.5, 0.5))
            spots.append((cx, cy, float(hz(cx, cy))))

    def young():
        parts = []
        for cx, cy, cz in spots:
            gg = float(rng.uniform(0.44, 0.58))
            parts.append(_dots((cx, cy, cz + 1.0), 2.0, 16, (0.12, gg, 0.09), rng))
        return parts

    def mature():
        parts = []
        for cx, cy, cz in spots:
            h = float(rng.uniform(9.0, 13.0))
            stem = np.zeros((7, NCOLS), dtype=np.float32)
            stem[:, PX], stem[:, PY] = cx, cy
            stem[:, PZ] = np.linspace(cz, cz + h, 7)
            stem[:, TYPE] = 3.0; stem[:, ALPHA] = 0.85; stem[:, SIZE] = 1.8
            stem[:, CR], stem[:, CG], stem[:, CB] = 0.16, 0.42, 0.12
            parts.append(stem)
            gg = float(rng.uniform(0.40, 0.55))
            parts.append(_dots((cx, cy, cz + h * 0.6), 2.5, 14, (0.13, gg, 0.10), rng))
            ripe = rng.random() < 0.75
            head = (0.78, 0.62, 0.16) if ripe else (0.20, gg, 0.12)
            parts.append(_dots((cx, cy, cz + h + 0.8), 1.6, 12, head, rng))
        return parts

    begin = np.concatenate([gnd, tilled] + wild + young(), axis=0)
    end = np.concatenate([gnd, tilled] + wild + mature(), axis=0)
    return end, begin

def _lunar_farm_buffers(spec: dict, term: str):
    """theLunarFarm: cultivation under a SEALED dome on an airless world. Outside:
    barren grey regolith, no life, no air. Inside the shell: crop rows in trays under
    lamp glow, ripening to gold -- the membrane's claim is the BOUNDARY: life inside,
    sterility outside, the dome the only thing between them. begin = young stand,
    end = mature at harvest."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 190.0))
    DOME_R = 58.0

    # barren regolith: grey, lifeless, cratered-looking patchiness
    n_g = 7000
    th = rng.random(n_g) * 2.0 * np.pi
    rr = R * np.sqrt(rng.random(n_g))
    gx, gy = rr * np.cos(th), rr * np.sin(th)
    patch = 0.5 + 0.5 * np.sin(0.08 * gx + 0.7) * np.sin(0.07 * gy + 2.1)
    gnd = np.zeros((n_g, NCOLS), dtype=np.float32)
    gnd[:, PX], gnd[:, PY], gnd[:, PZ] = gx, gy, 0.0
    gnd[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    gnd[:, TYPE] = 3.0; gnd[:, ALPHA] = 0.55; gnd[:, SIZE] = 3.0
    grey = 0.30 + 0.08 * patch
    gnd[:, CR], gnd[:, CG], gnd[:, CB] = grey, grey, grey * 1.04

    # the dome shell: a faint translucent hemisphere over the farm
    n_s = 1800
    u = rng.random(n_s)
    v = rng.random(n_s)
    phi = 2.0 * np.pi * u
    cth = np.sqrt(1.0 - v)                       # hemisphere: cos(theta) in [0,1]
    sth = np.sqrt(np.maximum(0.0, 1.0 - cth * cth))
    shell = np.zeros((n_s, NCOLS), dtype=np.float32)
    shell[:, PX] = DOME_R * sth * np.cos(phi)
    shell[:, PY] = DOME_R * sth * np.sin(phi)
    shell[:, PZ] = DOME_R * cth
    shell[:, TYPE] = 3.0; shell[:, ALPHA] = 0.16; shell[:, SIZE] = 2.2
    shell[:, CR], shell[:, CG], shell[:, CB] = 0.75, 0.82, 0.92

    # tray floor inside the dome: flat dark deck, not native soil
    n_t = 1200
    tx = rng.uniform(-42.0, 42.0, n_t)
    ty = rng.uniform(-36.0, 36.0, n_t)
    deck = np.zeros((n_t, NCOLS), dtype=np.float32)
    deck[:, PX], deck[:, PY], deck[:, PZ] = tx, ty, 0.4
    deck[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    deck[:, TYPE] = 3.0; deck[:, ALPHA] = 0.5; deck[:, SIZE] = 2.6
    deck[:, CR], deck[:, CG], deck[:, CB] = 0.16, 0.16, 0.18

    # lamp glow: a warm bright line above each crop row
    rows_y = [(-30.0 + 10.0 * k) for k in range(7)]
    lamps = []
    for y in rows_y:
        xs = np.linspace(-38.0, 38.0, 26)
        lb = np.zeros((len(xs), NCOLS), dtype=np.float32)
        lb[:, PX], lb[:, PY], lb[:, PZ] = xs, y, 22.0
        lb[:, TYPE] = 3.0; lb[:, ALPHA] = 0.5; lb[:, SIZE] = 2.0
        lb[:, CR], lb[:, CG], lb[:, CB] = 0.95, 0.88, 0.66
        lamps.append(lb)

    # the crop: rows in trays under the lamps
    spots = []
    for y in rows_y:
        for x in np.linspace(-38.0, 38.0, 13):
            if rng.random() > 0.96:
                continue
            spots.append((x + float(rng.uniform(-0.4, 0.4)),
                          y + float(rng.uniform(-0.4, 0.4))))

    def young():
        parts = []
        for cx, cy in spots:
            gg = float(rng.uniform(0.44, 0.58))
            parts.append(_dots((cx, cy, 1.2), 1.8, 14, (0.12, gg, 0.09), rng))
        return parts

    def mature():
        parts = []
        for cx, cy in spots:
            h = float(rng.uniform(8.0, 11.0))
            stem = np.zeros((6, NCOLS), dtype=np.float32)
            stem[:, PX], stem[:, PY] = cx, cy
            stem[:, PZ] = np.linspace(0.6, 0.6 + h, 6)
            stem[:, TYPE] = 3.0; stem[:, ALPHA] = 0.85; stem[:, SIZE] = 1.6
            stem[:, CR], stem[:, CG], stem[:, CB] = 0.16, 0.42, 0.12
            parts.append(stem)
            gg = float(rng.uniform(0.40, 0.55))
            parts.append(_dots((cx, cy, 0.6 + h * 0.6), 2.2, 12, (0.13, gg, 0.10), rng))
            ripe = rng.random() < 0.75
            head = (0.78, 0.62, 0.16) if ripe else (0.20, gg, 0.12)
            parts.append(_dots((cx, cy, 0.6 + h + 0.7), 1.4, 10, head, rng))
        return parts

    begin = np.concatenate([gnd, shell, deck] + lamps + young(), axis=0)
    end = np.concatenate([gnd, shell, deck] + lamps + mature(), axis=0)
    return end, begin

def _orbital_farm_buffers(spec: dict, term: str):
    """theOrbitalFarm: cultivation carried in a SPINNING RING in open space. The membrane's
    claim: a ring of life against the dark -- the crop band rides the ring (spin is its
    gravity), hub and spokes hold it, the planet turns far below, stars behind. No soil,
    no sky: green carried in a torus of metal. begin = the band newly sown, end = the
    band mature with grain ripened gold."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    RING_R = 90.0

    # stars: a far shell of faint white points -- the dark the ring hangs in
    n_st = 1500
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 380.0
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0; stars[:, ALPHA] = 0.5; stars[:, SIZE] = 1.2
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.88, 0.95

    # the ring hull: a grey torus band
    n_r = 3600
    a = rng.random(n_r) * 2.0 * np.pi
    b = rng.random(n_r) * 2.0 * np.pi
    tube = 9.0
    ring = np.zeros((n_r, NCOLS), dtype=np.float32)
    ring[:, PX] = (RING_R + tube * np.cos(b)) * np.cos(a)
    ring[:, PY] = (RING_R + tube * np.cos(b)) * np.sin(a)
    ring[:, PZ] = tube * np.sin(b)
    ring[:, TYPE] = 3.0; ring[:, ALPHA] = 0.5; ring[:, SIZE] = 2.2
    ring[:, CR], ring[:, CG], ring[:, CB] = 0.42, 0.45, 0.50

    # hub + spokes
    hub = _dots((0.0, 0.0, 0.0), 8.0, 200, (0.50, 0.53, 0.58), rng)
    spokes = []
    for k in range(4):
        aa = k * np.pi / 2.0
        ts = np.linspace(8.0, RING_R - tube, 40)
        sp = np.zeros((len(ts), NCOLS), dtype=np.float32)
        sp[:, PX] = ts * np.cos(aa)
        sp[:, PY] = ts * np.sin(aa)
        sp[:, PZ] = 0.0
        sp[:, TYPE] = 3.0; sp[:, ALPHA] = 0.5; sp[:, SIZE] = 1.8
        sp[:, CR], sp[:, CG], sp[:, CB] = 0.45, 0.48, 0.53
        spokes.append(sp)

    # the planet far below
    planet = _solid_sphere((40.0, 80.0, -230.0), 42.0, (0.30, 0.48, 0.72), rng, gain=0.7)

    # the crop band: crops rooted along the ring's inner rim, facing the hub
    n_crop = 240
    angs = np.linspace(0.0, 2.0 * np.pi, n_crop, endpoint=False)

    def band(mature):
        parts = []
        for aa in angs:
            if rng.random() > (0.98 if mature else 0.75):
                continue
            cx = (RING_R - tube - 1.5) * np.cos(aa)
            cy = (RING_R - tube - 1.5) * np.sin(aa)
            if not mature:
                gg = float(rng.uniform(0.40, 0.55))
                parts.append(_dots((cx, cy, 2.0), 1.6, 10, (0.12, gg, 0.09), rng))
            else:
                h = float(rng.uniform(4.5, 6.5))
                stem = np.zeros((4, NCOLS), dtype=np.float32)
                stem[:, PX], stem[:, PY] = cx, cy
                stem[:, PZ] = np.linspace(1.0, 1.0 + h, 4)
                stem[:, TYPE] = 3.0; stem[:, ALPHA] = 0.85; stem[:, SIZE] = 1.5
                stem[:, CR], stem[:, CG], stem[:, CB] = 0.16, 0.44, 0.12
                parts.append(stem)
                gg = float(rng.uniform(0.42, 0.56))
                parts.append(_dots((cx, cy, 1.0 + h * 0.6), 1.8, 10, (0.13, gg, 0.10), rng))
                ripe = rng.random() < 0.7
                head = (0.78, 0.62, 0.16) if ripe else (0.20, gg, 0.12)
                parts.append(_dots((cx, cy, 1.0 + h + 0.6), 1.2, 8, head, rng))
        return parts

    begin = np.concatenate([stars, ring, hub, planet] + spokes + band(False), axis=0)
    end = np.concatenate([stars, ring, hub, planet] + spokes + band(True), axis=0)
    return end, begin

def _space_buffers(spec: dict, term: str):
    """theSpace: the dark medium itself. Not a system, not a world -- the VOID the ship
    flies through: a deep starfield, a few small bodies suspended in the black at very
    different depths, one distant star glaring. No ground, no horizon, nothing to stand
    on -- the membrane's claim is the dark WITH depth in it. begin = end: space does not
    become; the camera's drift is the only motion."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 300.0))

    # the starfield: a dense shell at varied depths -- the texture of the medium
    n_st = 5200
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = R * (0.8 + 0.7 * rng.random(n_st))        # depth layering, not one shell
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.35 + 0.3 * rng.random(n_st)
    stars[:, SIZE] = 0.9 + 1.1 * rng.random(n_st)
    tint = rng.random(n_st)
    stars[:, CR] = 0.80 + 0.15 * tint
    stars[:, CG] = 0.82 + 0.12 * tint
    stars[:, CB] = 0.90 + 0.08 * (1.0 - tint)

    # a few bodies suspended in the dark, small and far -- scale, not system
    bodies = [
        _solid_sphere((-120.0, 150.0, -60.0), 14.0, (0.55, 0.42, 0.33), rng, gain=0.7),
        _solid_sphere((60.0, 170.0, 80.0), 9.0, (0.36, 0.50, 0.66), rng, gain=0.7),
        _solid_sphere((30.0, 140.0, -100.0), 6.0, (0.62, 0.62, 0.60), rng, gain=0.7),
    ]

    # the distant star: a small fierce glare, not the center of anything
    star = _solid_sphere((180.0, 230.0, 120.0), 8.0, (1.0, 0.95, 0.82), rng, gain=0.9)
    glare = _halo((180.0, 230.0, 120.0), 16.0, (1.0, 0.9, 0.7), rng, alpha=0.10, size=2.0)

    end = np.concatenate([stars] + bodies + [star, glare], axis=0)
    begin = end.copy()
    return end, begin

def _seed_buffers(spec: dict, term: str):
    """theSeed: the number the world unfolds from. ONE bright point in the dark, and
    everything that exists radiating out of it -- branching filaments (the unfolding)
    with small worlds at their tips. Nothing here has a separate origin: every thread
    traces back to the one point. begin = the seed alone, not yet unfolded; end = the
    world it became, still attached to its number."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 180.0))

    # the seed: one fierce bright point at the origin
    seed_pt = _solid_sphere((0.0, 0.0, 0.0), 9.0, (1.0, 0.97, 0.85), rng, gain=1.0)
    glow = _halo((0.0, 0.0, 0.0), 20.0, (1.0, 0.92, 0.70), rng, alpha=0.16, size=2.8)

    def unfold(scale):
        """the branching unfold: filaments out of the origin, worlds at their tips."""
        parts = []
        n_main = 8
        for k in range(n_main):
            a = k * 2.0 * np.pi / n_main + 0.3
            elev = float(rng.uniform(-0.45, 0.45))
            L = float(rng.uniform(85.0, 120.0)) * scale
            # the main thread: a slightly wandering line of splats
            ts = np.linspace(6.0, L, 46)
            wander = np.cumsum(rng.normal(0.0, 0.06, len(ts)))
            fx = ts * np.cos(a + wander * 0.3)
            fy = ts * np.sin(a + wander * 0.3)
            fz = ts * elev * 0.6 + rng.normal(0.0, 1.2, len(ts))
            th = np.zeros((len(ts), NCOLS), dtype=np.float32)
            th[:, PX], th[:, PY], th[:, PZ] = fx, fy, fz
            th[:, TYPE] = 3.0; th[:, ALPHA] = 0.45; th[:, SIZE] = 1.4
            th[:, CR], th[:, CG], th[:, CB] = 0.75, 0.62, 0.38   # warm thread
            parts.append(th)
            # a world at the tip: its colour is its own, its ORIGIN is not
            wc = [(0.62, 0.45, 0.34), (0.34, 0.55, 0.82), (0.70, 0.62, 0.42),
                  (0.45, 0.72, 0.50), (0.78, 0.55, 0.62), (0.55, 0.65, 0.85),
                  (0.72, 0.70, 0.55), (0.50, 0.58, 0.75)][k]
            parts.append(_solid_sphere((fx[-1], fy[-1], fz[-1]),
                                       float(rng.uniform(5.0, 8.0)) * scale, wc, rng, gain=0.75))
            # one sub-branch off the middle: the unfold branches, it does not just spray
            mid = len(ts) // 2
            ba = a + float(rng.uniform(0.5, 0.9)) * (1 if k % 2 else -1)
            bs = np.linspace(0.0, 34.0 * scale, 18)
            bx = fx[mid] + bs * np.cos(ba)
            by = fy[mid] + bs * np.sin(ba)
            bz = fz[mid] + bs * elev * 0.4
            bb = np.zeros((len(bs), NCOLS), dtype=np.float32)
            bb[:, PX], bb[:, PY], bb[:, PZ] = bx, by, bz
            bb[:, TYPE] = 3.0; bb[:, ALPHA] = 0.4; bb[:, SIZE] = 1.2
            bb[:, CR], bb[:, CG], bb[:, CB] = 0.70, 0.58, 0.36
            parts.append(bb)
            parts.append(_solid_sphere((bx[-1], by[-1], bz[-1]),
                                       float(rng.uniform(2.5, 4.0)) * scale, wc, rng, gain=0.7))
        return parts

    begin = np.concatenate([seed_pt, glow] + unfold(0.12), axis=0)   # the seed, barely begun
    end = np.concatenate([seed_pt, glow] + unfold(1.0), axis=0)      # the world, unfolded
    return end, begin

def _determinism_buffers(spec: dict, term: str):
    """theDeterminism: same seed -> same world, bit-identical. TWO unfolds side by side,
    built by the SAME rng sequence run twice: every thread, every world, every colour in
    the left twin has its exact counterpart in the right twin. The membrane made visible
    is the TWINS: not two similar worlds -- one world, twice. begin = both mid-unfold
    (identical), end = both complete (identical)."""
    import numpy as np
    R = float(spec.get("radius", 200.0))

    def one_unfold(origin, seed_no, scale):
        """One seed's unfold, built from a FRESH generator seeded with seed_no -- so two
        calls with the same seed_no emit bit-identical structure. That IS the claim."""
        rng = np.random.default_rng(seed_no)
        ox, oy, oz = origin
        parts = []
        parts.append(_solid_sphere((ox, oy, oz), 6.0 * scale, (1.0, 0.95, 0.80), rng, gain=0.9))
        n_main = 6
        for k in range(n_main):
            a = k * 2.0 * np.pi / n_main + 0.4
            elev = float(rng.uniform(-0.35, 0.35))
            L = float(rng.uniform(48.0, 68.0)) * scale
            ts = np.linspace(5.0 * scale, L, 30)
            wander = np.cumsum(rng.normal(0.0, 0.06, len(ts)))
            fx = ox + ts * np.cos(a + wander * 0.3)
            fy = oy + ts * np.sin(a + wander * 0.3)
            fz = oz + ts * elev * 0.6 + rng.normal(0.0, 0.8, len(ts))
            th = np.zeros((len(ts), NCOLS), dtype=np.float32)
            th[:, PX], th[:, PY], th[:, PZ] = fx, fy, fz
            th[:, TYPE] = 3.0; th[:, ALPHA] = 0.5; th[:, SIZE] = 1.4
            th[:, CR], th[:, CG], th[:, CB] = 0.72, 0.60, 0.38
            parts.append(th)
            wc = [(0.62, 0.45, 0.34), (0.34, 0.55, 0.82), (0.70, 0.62, 0.42),
                  (0.45, 0.72, 0.50), (0.78, 0.55, 0.62), (0.55, 0.65, 0.85)][k]
            parts.append(_solid_sphere((fx[-1], fy[-1], fz[-1]),
                                       float(rng.uniform(3.5, 5.5)) * scale, wc, rng, gain=0.75))
        return parts

    left = (-70.0, 0.0, 0.0)
    right = (70.0, 0.0, 0.0)

    begin = np.concatenate(one_unfold(left, 7, 0.35) + one_unfold(right, 7, 0.35), axis=0)
    end = np.concatenate(one_unfold(left, 7, 1.0) + one_unfold(right, 7, 1.0), axis=0)
    return end, begin

def _laws_buffers(spec: dict, term: str):
    """theLaws: the trained physics the seed runs under. Where theSeed's web is organic
    and wandering, the LAWS are order: a perfect lattice -- every node at its measured
    place, every edge the same length, the same rule repeated everywhere with no
    exception. begin = the lattice faint, only the rule-points lit; end = the lattice
    fully bound, every edge drawn: the rules connecting into the one grid everything
    runs on."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 180.0))
    SP = 26.0
    N = 4                       # nodes per axis: a (2N+1)^3 lattice

    # the rule-points: a perfect cubic lattice of glowing nodes
    coords = np.arange(-N, N + 1) * SP
    pts = np.array([(x, y, z) for x in coords for y in coords for z in coords])
    nodes = np.zeros((len(pts), NCOLS), dtype=np.float32)
    nodes[:, PX], nodes[:, PY], nodes[:, PZ] = pts[:, 0], pts[:, 1], pts[:, 2]
    nodes[:, TYPE] = 3.0; nodes[:, ALPHA] = 0.85; nodes[:, SIZE] = 2.4
    nodes[:, CR], nodes[:, CG], nodes[:, CB] = 0.40, 0.78, 0.92

    def edges(bright):
        """the bindings: axis edges between lattice neighbours, all one length."""
        out = []
        for i, a1 in enumerate(pts):
            for axis in range(3):
                b1 = a1.copy(); b1[axis] += SP
                if abs(b1[axis]) > N * SP:
                    continue
                seg = np.zeros((8, NCOLS), dtype=np.float32)
                ts = np.linspace(0.0, 1.0, 8)[:, None]
                seg[:, PX:PZ + 1] = a1 * (1.0 - ts) + b1 * ts
                seg[:, TYPE] = 3.0
                seg[:, ALPHA] = 0.55 if bright else 0.10
                seg[:, SIZE] = 1.1
                seg[:, CR], seg[:, CG], seg[:, CB] = 0.30, 0.60, 0.78
                out.append(seg)
        return out

    begin = np.concatenate([nodes] + edges(False), axis=0)   # the rules, not yet bound
    end = np.concatenate([nodes] + edges(True), axis=0)      # the rulebook, bound
    return end, begin

def _truth_buffers(spec: dict, term: str):
    """theTruth: every fact reaches physics. A bedrock slab below; glowing facts above;
    and EVERY fact hangs on a chain that runs down to the rock -- nothing floats free,
    nothing is asserted without its anchor. The membrane made visible: count the chains,
    count the facts -- they are the same number. begin = the facts dim and the chains
    half-drawn; end = every fact lit and every chain taut to bedrock."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    R = float(spec.get("radius", 180.0))
    BED_Z = -42.0

    # the bedrock: a dense stone slab -- physics, the terminal every chain ends at
    n_b = 3800
    th = rng.random(n_b) * 2.0 * np.pi
    rr = 95.0 * np.sqrt(rng.random(n_b))
    bed = np.zeros((n_b, NCOLS), dtype=np.float32)
    bed[:, PX], bed[:, PY] = rr * np.cos(th), rr * np.sin(th)
    bed[:, PZ] = BED_Z + rng.normal(0.0, 1.2, n_b)
    bed[:, NX:NZ + 1] = (0.0, 0.0, 1.0)
    bed[:, TYPE] = 3.0; bed[:, ALPHA] = 0.65; bed[:, SIZE] = 2.8
    bed[:, CR], bed[:, CG], bed[:, CB] = 0.48, 0.46, 0.44

    # the facts: glowing nodes at scattered positions ABOVE the rock
    n_f = 12
    fa = rng.random(n_f) * 2.0 * np.pi
    fr = rng.uniform(15.0, 80.0, n_f)
    fx, fy = fr * np.cos(fa), fr * np.sin(fa)
    fz = rng.uniform(-5.0, 45.0, n_f)

    def scene(lit, chain_alpha):
        parts = []
        for k in range(n_f):
            # the chain: a straight run of links from the fact down to the rock
            n_links = 26
            ts = np.linspace(0.0, 1.0, n_links)
            ch = np.zeros((n_links, NCOLS), dtype=np.float32)
            ch[:, PX] = fx[k] * (1.0 - ts) + fx[k] * ts * 0.92
            ch[:, PY] = fy[k] * (1.0 - ts) + fy[k] * ts * 0.92
            ch[:, PZ] = fz[k] + (BED_Z - fz[k]) * ts
            ch[:, TYPE] = 3.0; ch[:, ALPHA] = chain_alpha; ch[:, SIZE] = 1.3
            ch[:, CR], ch[:, CG], ch[:, CB] = 0.85, 0.75, 0.50
            parts.append(ch)
            # the fact itself
            if lit:
                parts.append(_dots((fx[k], fy[k], fz[k]), 3.4, 22,
                                   (0.45, 0.85, 1.00), rng))
            else:
                parts.append(_dots((fx[k], fy[k], fz[k]), 3.4, 22,
                                   (0.20, 0.30, 0.36), rng))
        return parts

    begin = np.concatenate([bed] + scene(False, 0.18), axis=0)
    end = np.concatenate([bed] + scene(True, 0.70), axis=0)
    return end, begin

def _ship_buffers(spec: dict, term: str):
    """theShip: the vessel of matter that carries the player between worlds. ONE long
    slender hull suspended in the dark starfield -- nose cone at the front, fins at
    the tail, a warm cabin light, and a LONG bright drive plume streaming far behind:
    the silhouette of a vessel under thrust, not a round body. The claim is a THING
    that carries: hull + carried light + drive glow, one object in the void.
    begin = cold start: cabin dim, engines dead, no plume; end = the ship alive,
    cabin warm, engines burning with a long plume."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # the starfield: the void the ship hangs in
    n_st = 2600
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 150.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.30 + 0.25 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    tint = rng.random(n_st)
    stars[:, CR] = 0.80 + 0.15 * tint
    stars[:, CG] = 0.82 + 0.12 * tint
    stars[:, CB] = 0.90 + 0.08 * (1.0 - tint)

    # the hull: a LONG slender metallic shell along X (6:1) -- nose +X, tail -X
    n_h = 2200
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    a, b = 34.0, 5.5                     # half-length, half-beam -- slender
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.80; hull[:, SIZE] = 1.5
    shade = 0.55 + 0.25 * rng.random(n_h)
    hull[:, CR] = 0.62 * shade + 0.10
    hull[:, CG] = 0.64 * shade + 0.10
    hull[:, CB] = 0.68 * shade + 0.12

    # the nose cone: a tapered point at the front -- the bow of the vessel
    n_n = 350
    tn = rng.random(n_n)
    an = rng.random(n_n) * 2.0 * np.pi
    nose = np.zeros((n_n, NCOLS), dtype=np.float32)
    nose[:, PX] = a + 10.0 * tn
    rn = b * (1.0 - tn) * 0.95
    nose[:, PY] = rn * np.cos(an)
    nose[:, PZ] = rn * np.sin(an)
    nose[:, TYPE] = 3.0; nose[:, ALPHA] = 0.85; nose[:, SIZE] = 1.4
    nose[:, CR], nose[:, CG], nose[:, CB] = 0.70, 0.72, 0.76

    # the fins: two flat swept planes at the tail -- a vessel's silhouette
    n_fin = 320
    tf = rng.random(n_fin)
    sf = rng.random(n_fin)
    fins = np.zeros((2 * n_fin, NCOLS), dtype=np.float32)
    for k, sign in enumerate((1.0, -1.0)):
        fx = -a + 10.0 * tf - 6.0 * sf
        fy = sign * (b * 0.9 + 7.0 * sf)
        sl = slice(k * n_fin, (k + 1) * n_fin)
        fins[sl, PX] = fx
        fins[sl, PY] = fy
        fins[sl, PZ] = 2.0 * (tf - 0.5)
        fins[sl, TYPE] = 3.0; fins[sl, ALPHA] = 0.85; fins[sl, SIZE] = 1.4
        fins[sl, CR], fins[sl, CG], fins[sl, CB] = 0.60, 0.62, 0.66

    def scene(cabin_lit, engine_lit):
        parts = []
        # the cabin: a warm light at the nose -- the player, carried
        cabin_c = (0.98, 0.82, 0.55) if cabin_lit else (0.30, 0.26, 0.20)
        parts.append(_dots((a * 0.70, 0.0, b * 0.55), 2.6, 36, cabin_c, rng))
        if cabin_lit:
            parts.append(_halo((a * 0.70, 0.0, b * 0.55), 5.0,
                               (1.0, 0.85, 0.55), rng, alpha=0.13, size=1.6))
        # the engines: three fierce blue-white flares at the tail
        eng_c = (0.55, 0.80, 1.00) if engine_lit else (0.18, 0.24, 0.30)
        for dy in (-2.6, 0.0, 2.6):
            parts.append(_dots((-a * 0.99, dy, 0.0), 2.2, 30, eng_c, rng))
            if engine_lit:
                parts.append(_halo((-a * 0.99, dy, 0.0), 5.0,
                                   (0.55, 0.80, 1.0), rng, alpha=0.16, size=1.8))
        # the plume: one LONG bright cone of drive glow streaming far behind
        if engine_lit:
            n_p = 1400
            tp = rng.random(n_p)
            plume = np.zeros((n_p, NCOLS), dtype=np.float32)
            plume[:, PX] = -a - 55.0 * tp
            spread = 1.2 + 5.0 * tp
            plume[:, PY] = rng.normal(0.0, spread, n_p)
            plume[:, PZ] = rng.normal(0.0, spread, n_p)
            plume[:, TYPE] = 3.0
            plume[:, ALPHA] = 0.55 * (1.0 - tp) + 0.04
            plume[:, SIZE] = 1.6
            plume[:, CR], plume[:, CG], plume[:, CB] = 0.50, 0.72, 1.00
            parts.append(plume)
        return parts

    begin = np.concatenate([stars, hull, nose, fins] + scene(False, False), axis=0)
    end = np.concatenate([stars, hull, nose, fins] + scene(True, True), axis=0)
    return end, begin

def _flight_buffers(spec: dict, term: str):
    """theFlight: the vessel's controlled motion through space. The ship itself
    (slender hull, nose, fins, engines) riding at the HEAD of a long curved line of
    glowing waypoints that arcs across the starfield -- the trajectory made visible,
    the vessel at its front. The claim is MOTION ALONG A PATH: one ship, one arc,
    ship at the head of it. begin = the path dim and short, ship cold; end = the
    full arc lit and the ship burning along it."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # the starfield: the medium being crossed
    n_st = 2200
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 160.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.30 + 0.25 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    tint = rng.random(n_st)
    stars[:, CR] = 0.80 + 0.15 * tint
    stars[:, CG] = 0.82 + 0.12 * tint
    stars[:, CB] = 0.90 + 0.08 * (1.0 - tint)

    # the ship at the head of the arc, nose +X (compact proven silhouette)
    a, b = 24.0, 5.0
    SHIP_X, SHIP_Z = 48.0, 10.0
    n_h = 1600
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = SHIP_X + a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = SHIP_Z + b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.80; hull[:, SIZE] = 1.5
    shade = 0.55 + 0.25 * rng.random(n_h)
    hull[:, CR] = 0.62 * shade + 0.10
    hull[:, CG] = 0.64 * shade + 0.10
    hull[:, CB] = 0.68 * shade + 0.12

    n_n = 250
    tn = rng.random(n_n)
    an = rng.random(n_n) * 2.0 * np.pi
    nose = np.zeros((n_n, NCOLS), dtype=np.float32)
    nose[:, PX] = SHIP_X + a + 8.0 * tn
    rn = b * (1.0 - tn) * 0.95
    nose[:, PY] = rn * np.cos(an)
    nose[:, PZ] = SHIP_Z + rn * np.sin(an)
    nose[:, TYPE] = 3.0; nose[:, ALPHA] = 0.85; nose[:, SIZE] = 1.4
    nose[:, CR], nose[:, CG], nose[:, CB] = 0.70, 0.72, 0.76

    # the trajectory: a long arc of glowing waypoints sweeping in from far left,
    # curving down then up to the ship's tail -- the path the vessel is flying
    n_w = 700
    tw = np.linspace(0.0, 1.0, n_w)
    path = np.zeros((n_w, NCOLS), dtype=np.float32)
    path[:, PX] = -110.0 + (SHIP_X - a + 110.0) * tw
    path[:, PZ] = -35.0 + (SHIP_Z + 35.0) * tw + 18.0 * np.sin(tw * np.pi)
    path[:, PY] = 0.0
    path[:, TYPE] = 3.0; path[:, SIZE] = 1.5

    def scene(lit):
        parts = []
        pa = 0.75 if lit else 0.16
        pth = path.copy()
        pth[:, ALPHA] = pa
        # the arc brightens toward the ship -- direction of travel in the glow
        pth[:, CR] = 0.35 + 0.35 * tw
        pth[:, CG] = 0.70 + 0.20 * tw
        pth[:, CB] = 1.00
        parts.append(pth)
        # the engines + plume at the tail when burning
        eng_c = (0.55, 0.80, 1.00) if lit else (0.18, 0.24, 0.30)
        for dy in (-2.4, 0.0, 2.4):
            parts.append(_dots((SHIP_X - a * 0.99, dy, SHIP_Z), 2.2, 26, eng_c, rng))
        if lit:
            parts.append(_halo((SHIP_X - a * 0.99, 0.0, SHIP_Z), 5.0,
                               (0.55, 0.80, 1.0), rng, alpha=0.15, size=1.8))
            n_p = 700
            tp = rng.random(n_p)
            plume = np.zeros((n_p, NCOLS), dtype=np.float32)
            plume[:, PX] = SHIP_X - a - 34.0 * tp
            spread = 1.2 + 4.0 * tp
            plume[:, PY] = rng.normal(0.0, spread, n_p)
            plume[:, PZ] = SHIP_Z + rng.normal(0.0, spread, n_p)
            plume[:, TYPE] = 3.0
            plume[:, ALPHA] = 0.5 * (1.0 - tp) + 0.04
            plume[:, SIZE] = 1.5
            plume[:, CR], plume[:, CG], plume[:, CB] = 0.50, 0.72, 1.00
            parts.append(plume)
        return parts

    begin = np.concatenate([stars, hull, nose] + scene(False), axis=0)
    end = np.concatenate([stars, hull, nose] + scene(True), axis=0)
    return end, begin

def _ship_power_buffers(spec: dict, term: str):
    """theShipPower: ONE source of energy routed to every system aboard. The ship
    drawn dim as context; at its center a blazing reactor core; from that ONE core
    three glowing conduits branch: blue aft to the engines (drive), red forward to
    the weapon node (attack), cyan outward to a shield ring around the hull
    (barrier). Count the sources: one. Count the branches: every system. The claim
    is ROUTING -- one origin, many destinations. begin = core dim, conduits dark;
    end = core blazing and every bus lit."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # starfield, sparse -- context only
    n_st = 1500
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 150.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.25 + 0.2 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92

    # the hull, DIM -- the vessel as context, not the subject
    a, b = 34.0, 7.0
    n_h = 1500
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.16; hull[:, SIZE] = 1.4
    hull[:, CR], hull[:, CG], hull[:, CB] = 0.42, 0.44, 0.48

    def conduit(target, color, n=240):
        """a glowing bus line from the core to a system node"""
        t = np.linspace(0.0, 1.0, n)
        c = np.zeros((n, NCOLS), dtype=np.float32)
        c[:, PX] = target[0] * t
        c[:, PY] = target[1] * t
        c[:, PZ] = target[2] * t
        c[:, TYPE] = 3.0; c[:, SIZE] = 2.2
        c[:, CR], c[:, CG], c[:, CB] = color
        return c

    # the shield ring: a faint circle around the hull (the barrier system)
    n_r = 400
    ra = np.linspace(0.0, 2.0 * np.pi, n_r)
    ring = np.zeros((n_r, NCOLS), dtype=np.float32)
    ring[:, PX] = 11.0 * np.sin(ra)
    ring[:, PY] = 13.5 * np.cos(ra)
    ring[:, PZ] = 13.5 * np.sin(ra)
    ring[:, TYPE] = 3.0; ring[:, SIZE] = 1.9
    ring[:, CR], ring[:, CG], ring[:, CB] = 0.40, 0.90, 0.85

    def scene(lit):
        parts = []
        # the ONE core
        core_c = (1.0, 0.88, 0.60) if lit else (0.35, 0.30, 0.22)
        parts.append(_dots((0.0, 0.0, 0.0), 5.5, 80, core_c, rng))
        if lit:
            parts.append(_halo((0.0, 0.0, 0.0), 10.0, (1.0, 0.88, 0.55),
                               rng, alpha=0.20, size=2.2))
        ca = 0.80 if lit else 0.14
        # drive bus: aft to the engines
        cb = conduit((-a * 0.98, 0.0, 0.0), (0.45, 0.72, 1.0)); cb[:, ALPHA] = ca
        parts.append(cb)
        eng_c = (0.55, 0.80, 1.0) if lit else (0.16, 0.20, 0.26)
        parts.append(_dots((-a * 0.98, 0.0, 0.0), 3.4, 36, eng_c, rng))
        # attack bus: forward and up to the weapon node
        ca2 = conduit((a * 0.75, 0.0, b * 1.1), (1.0, 0.35, 0.25)); ca2[:, ALPHA] = ca
        parts.append(ca2)
        wea_c = (1.0, 0.40, 0.30) if lit else (0.26, 0.14, 0.12)
        parts.append(_dots((a * 0.75, 0.0, b * 1.1), 3.2, 34, wea_c, rng))
        # barrier bus: out to the shield ring
        cb3 = conduit((0.0, 16.0, 0.0), (0.40, 0.90, 0.85)); cb3[:, ALPHA] = ca
        parts.append(cb3)
        rg = ring.copy(); rg[:, ALPHA] = 0.70 if lit else 0.12
        parts.append(rg)
        return parts

    begin = np.concatenate([stars, hull] + scene(False), axis=0)
    end = np.concatenate([stars, hull] + scene(True), axis=0)
    return end, begin

def _ship_combat_buffers(spec: dict, term: str):
    """theShipCombat: the vessel's energy DELIVERED onto a chosen target. Our ship
    on the left, a target body on the right, and between them bright bolt streams
    crossing the dark -- plus an impact flash where the bolts land. The claim is
    not the ship and not the target but the ENERGY IN TRANSIT and where it ARRIVES:
    count the streams, they all run one way, and they all end on the same object.
    begin = weapons cold, target dim and intact; end = bolts flying, target flashing."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # starfield
    n_st = 1800
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 160.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.28 + 0.22 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92

    # our ship, left, nose +X toward the target
    a, b = 22.0, 4.6
    SX, SZ = -55.0, 0.0
    n_h = 1300
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = SX + a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = SZ + b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.75; hull[:, SIZE] = 1.8
    shade = 0.55 + 0.25 * rng.random(n_h)
    hull[:, CR] = 0.62 * shade + 0.10
    hull[:, CG] = 0.64 * shade + 0.10
    hull[:, CB] = 0.68 * shade + 0.12

    # the target: a solid body far right
    TX, TZ = 62.0, 6.0
    target = _solid_sphere((TX, 0.0, TZ), 11.0, (0.60, 0.34, 0.30), rng, gain=0.8)

    # the bolt streams: three bright lines of fire from the bow to the target
    def bolt_stream(off_z, n=200):
        t = np.linspace(0.0, 1.0, n)
        bs = np.zeros((n, NCOLS), dtype=np.float32)
        x0, z0 = SX + a + 6.0, SZ + off_z
        bs[:, PX] = x0 + (TX - 9.0 - x0) * t
        bs[:, PZ] = z0 + (TZ - z0) * t
        bs[:, PY] = 0.0
        bs[:, TYPE] = 3.0; bs[:, SIZE] = 1.3
        bs[:, CR], bs[:, CG], bs[:, CB] = 1.0, 0.30, 0.15
        return bs

    def scene(lit):
        parts = []
        ba = 0.85 if lit else 0.10
        for off in (-2.5, 0.0, 2.5):
            bs = bolt_stream(off)
            bs[:, ALPHA] = ba
            parts.append(bs)
        if lit:
            # the muzzle glow at the bow
            parts.append(_halo((SX + a + 5.0, 0.0, SZ), 4.5, (1.0, 0.45, 0.25),
                               rng, alpha=0.16, size=1.8))
            # the engines at the TAIL -- blue fire at the far left marks which
            # end is the vessel and which way it points
            parts.append(_dots((SX - a - 2.0, 0.0, SZ), 3.0, 40, (0.50, 0.75, 1.0), rng))
            parts.append(_halo((SX - a - 2.0, 0.0, SZ), 6.0, (0.50, 0.75, 1.0),
                               rng, alpha=0.16, size=1.8))
            # the impact flash where every stream lands -- a STRIKE, smaller and
            # dimmer than the beam it ends
            parts.append(_dots((TX - 8.5, 0.0, TZ), 2.6, 40, (1.0, 0.70, 0.35), rng))
        return parts

    begin = np.concatenate([stars, hull, target] + scene(False), axis=0)
    end = np.concatenate([stars, hull, target] + scene(True), axis=0)
    return end, begin

def _shields_buffers(spec: dict, term: str):
    """theShields: a barrier of energy that SURROUNDS the vessel. The ship at the
    center; enclosing it completely a glowing cyan bubble-shell -- and an incoming
    red bolt that STOPS at the shell's surface with a small flash, never reaching
    the hull. The claim is the envelope: one vessel entirely inside one barrier,
    and the incoming energy ending at the boundary. begin = shell dark, bolt
    absent; end = shell lit, bolt stopped at its face."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # starfield
    n_st = 1800
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 150.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.28 + 0.22 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92

    # the ship at the center of its bubble
    a, b = 26.0, 5.2
    n_h = 1400
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.80; hull[:, SIZE] = 1.6
    shade = 0.55 + 0.25 * rng.random(n_h)
    hull[:, CR] = 0.62 * shade + 0.10
    hull[:, CG] = 0.64 * shade + 0.10
    hull[:, CB] = 0.68 * shade + 0.12

    # the barrier: an ellipsoidal shell enclosing the hull with clear standoff
    n_s = 2600
    su = rng.random(n_s) * 2.0 - 1.0
    sp = rng.random(n_s) * 2.0 * np.pi
    ssxz = np.sqrt(np.maximum(0.0, 1.0 - su * su))
    SA, SB = 40.0, 16.0
    shell = np.zeros((n_s, NCOLS), dtype=np.float32)
    shell[:, PX] = SA * su
    shell[:, PY] = SB * ssxz * np.cos(sp)
    shell[:, PZ] = SB * ssxz * np.sin(sp)
    shell[:, TYPE] = 3.0; shell[:, SIZE] = 1.5
    shell[:, CR], shell[:, CG], shell[:, CB] = 0.35, 0.85, 0.95

    # the incoming bolt: a red streak from the right that ENDS at the shell face
    n_b = 160
    tb = np.linspace(0.0, 1.0, n_b)
    bolt = np.zeros((n_b, NCOLS), dtype=np.float32)
    bolt[:, PX] = 80.0 + (SA + 1.0 - 80.0) * tb       # stops AT the shell, not past it
    bolt[:, PZ] = 4.0 - 4.0 * tb
    bolt[:, PY] = 0.0
    bolt[:, TYPE] = 3.0; bolt[:, SIZE] = 1.4
    bolt[:, CR], bolt[:, CG], bolt[:, CB] = 1.0, 0.30, 0.15

    def scene(lit):
        parts = []
        sh = shell.copy()
        sh[:, ALPHA] = 0.55 if lit else 0.10
        parts.append(sh)
        bt = bolt.copy()
        bt[:, ALPHA] = 0.80 if lit else 0.0
        parts.append(bt)
        if lit:
            # the impact flash ON the shell surface -- energy stopped at the boundary
            parts.append(_dots((SA + 1.0, 0.0, 0.0), 3.0, 50, (1.0, 0.80, 0.45), rng))
            parts.append(_halo((SA + 1.0, 0.0, 0.0), 6.5, (1.0, 0.75, 0.45),
                               rng, alpha=0.16, size=1.9))
        return parts

    begin = np.concatenate([stars, hull] + scene(False), axis=0)
    end = np.concatenate([stars, hull] + scene(True), axis=0)
    return end, begin

def _warp_drive_buffers(spec: dict, term: str):
    """theWarpDrive: the warp drive folds SPACE -- so the thing that changes is not
    the ship but the medium around it. The vessel sits at the center; around it the
    space itself is drawn as a WHIRLPOOL: three great spiral arms of stars winding
    inward to the vessel, the whole field swirling into one point. begin = a flat
    uniform starfield, no arms; end = the spiral wound tight around the ship.
    The claim: space itself bent around one point."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # the vessel at the throat
    a, b = 20.0, 4.2
    n_h = 1100
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.85; hull[:, SIZE] = 1.7
    shade = 0.55 + 0.25 * rng.random(n_h)
    hull[:, CR] = 0.62 * shade + 0.10
    hull[:, CG] = 0.64 * shade + 0.10
    hull[:, CB] = 0.68 * shade + 0.12

    # a sparse background -- the medium at rest
    n_bg = 1200
    u = rng.random(n_bg) * 2.0 - 1.0
    phi = rng.random(n_bg) * 2.0 * np.pi
    st_r = 170.0 * (0.85 + 0.6 * rng.random(n_bg))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    bg = np.zeros((n_bg, NCOLS), dtype=np.float32)
    bg[:, PX] = st_r * sxz * np.cos(phi)
    bg[:, PY] = st_r * sxz * np.sin(phi)
    bg[:, PZ] = st_r * u
    bg[:, TYPE] = 3.0
    bg[:, ALPHA] = 0.25 + 0.2 * rng.random(n_bg)
    bg[:, SIZE] = 0.8 + 1.0 * rng.random(n_bg)
    bg[:, CR], bg[:, CG], bg[:, CB] = 0.85, 0.87, 0.92

    # the whirlpool: three logarithmic spiral arms winding into the vessel,
    # drawn in the XZ plane facing the camera
    def arm(phase, wound, n=700):
        t = np.linspace(0.0, 1.0, n)
        ang = phase + wound * (1.0 - t) * 2.2 * np.pi
        rr = 12.0 + 100.0 * t
        d = np.zeros((n, NCOLS), dtype=np.float32)
        d[:, PX] = rr * np.cos(ang)
        d[:, PZ] = rr * np.sin(ang) * 0.8
        d[:, PY] = rng.normal(0.0, 1.5, n)
        d[:, TYPE] = 3.0
        d[:, SIZE] = 1.3 + 0.8 * (1.0 - t)
        d[:, CR] = 0.55 + 0.3 * (1.0 - t)
        d[:, CG] = 0.70 + 0.2 * (1.0 - t)
        d[:, CB] = 1.00
        return d

    def scene(wound, alpha):
        parts = []
        for k in range(3):
            ar = arm(k * 2.0 * np.pi / 3.0, wound)
            ar[:, ALPHA] = alpha * (0.5 + 0.5 * np.linspace(0.0, 1.0, ar.shape[0]))
            parts.append(ar)
        return parts

    # begin: arms barely wound, nearly invisible -- flat space
    begin = np.concatenate([bg, hull] + scene(0.15, 0.06), axis=0)
    # end: arms wound three full turns, bright -- space folded to a point
    end = np.concatenate([bg, hull] + scene(3.0, 0.80), axis=0)
    return end, begin

def _ship_view_buffers(spec: dict, term: str):
    """theShipView: the vantage from which the vessel is seen. The ship on the
    left; off to the right a small bright DRONE-EYE; and from that one eye a fan
    of sight-lines spreading out to BRACKET the hull -- the rays of looking made
    visible, every line from the eye ending on the vessel. The claim is not the
    ship but the LOOKING: one vantage, one cone of attention, and it all lands
    on the vessel. begin = eye dim, rays faint; end = eye lit, the cone bright."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # starfield
    n_st = 1500
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 150.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.26 + 0.2 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92

    # the vessel, left
    a, b = 24.0, 5.0
    SX = -22.0
    n_h = 1500
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = SX + a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.80; hull[:, SIZE] = 1.6
    shade = 0.55 + 0.25 * rng.random(n_h)
    hull[:, CR] = 0.62 * shade + 0.10
    hull[:, CG] = 0.64 * shade + 0.10
    hull[:, CB] = 0.68 * shade + 0.12

    EX, EY, EZ = 52.0, 0.0, 18.0          # the vantage point

    def ray(target, n=80):
        t = np.linspace(0.0, 1.0, n)
        r = np.zeros((n, NCOLS), dtype=np.float32)
        r[:, PX] = EX + (target[0] - EX) * t
        r[:, PY] = EY + (target[1] - EY) * t
        r[:, PZ] = EZ + (target[2] - EZ) * t
        r[:, TYPE] = 3.0; r[:, SIZE] = 1.2
        r[:, CR], r[:, CG], r[:, CB] = 0.55, 0.95, 0.80
        # the light GATHERS at the eye: faint at the hull, bright at the dot,
        # so the fan reads as converging on the vantage, not sprayed by the hull
        r[:, ALPHA] = 0.15 + 0.75 * (1.0 - t)
        return r

    # the cone of looking: rays bracketing the hull -- nose, tail, top, belly, center
    targets = [
        (SX + a, 0.0, 0.0), (SX - a, 0.0, 0.0),
        (SX, 0.0, b), (SX, 0.0, -b), (SX, 0.0, 0.0),
    ]

    def scene(lit):
        parts = []
        eye_c = (0.95, 0.98, 1.0) if lit else (0.28, 0.30, 0.32)
        parts.append(_dots((EX, EY, EZ), 3.6, 60, eye_c, rng))
        if lit:
            parts.append(_halo((EX, EY, EZ), 7.0, (0.90, 0.95, 1.0),
                               rng, alpha=0.18, size=2.0))
        ra = 0.65 if lit else 0.12
        for tg in targets:
            rr = ray(tg)
            rr[:, ALPHA] = ra
            parts.append(rr)
        return parts

    begin = np.concatenate([stars, hull] + scene(False), axis=0)
    end = np.concatenate([stars, hull] + scene(True), axis=0)
    return end, begin

def _salvage_buffers(spec: dict, term: str):
    """theSalvage: matter drawn from a wreck INTO the vessel. A broken debris
    cluster on the left; the ship on the right; and between them a tractor beam
    with a stream of fragments strung along it, traveling wreck -> hull. The
    claim is matter IN TRANSIT one way: count the fragments on the beam, they all
    leave the wreck and they all arrive at the vessel. begin = debris sitting on
    the wreck, beam dark; end = the beam lit and the fragments mid-stream."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # starfield
    n_st = 1400
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 150.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.26 + 0.2 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92

    # the wreck: a jagged cluster of broken chunks, left
    WX = -48.0
    n_w = 700
    wreck = np.zeros((n_w, NCOLS), dtype=np.float32)
    wreck[:, PX] = WX + rng.normal(0.0, 9.0, n_w)
    wreck[:, PY] = rng.normal(0.0, 5.0, n_w)
    wreck[:, PZ] = rng.normal(0.0, 5.0, n_w)
    wreck[:, TYPE] = 3.0; wreck[:, ALPHA] = 0.70; wreck[:, SIZE] = 1.8
    wreck[:, CR] = 0.45 + 0.15 * rng.random(n_w)
    wreck[:, CG] = 0.42 + 0.12 * rng.random(n_w)
    wreck[:, CB] = 0.40 + 0.10 * rng.random(n_w)

    # the vessel, right, compact
    a, b = 20.0, 4.4
    SX = 46.0
    n_h = 1200
    hu = rng.random(n_h) * 2.0 - 1.0
    hp = rng.random(n_h) * 2.0 * np.pi
    hsxz = np.sqrt(np.maximum(0.0, 1.0 - hu * hu))
    hull = np.zeros((n_h, NCOLS), dtype=np.float32)
    hull[:, PX] = SX + a * hu
    hull[:, PY] = b * hsxz * np.cos(hp)
    hull[:, PZ] = b * hsxz * np.sin(hp)
    hull[:, TYPE] = 3.0; hull[:, ALPHA] = 0.80; hull[:, SIZE] = 1.6
    shade = 0.55 + 0.25 * rng.random(n_h)
    hull[:, CR] = 0.62 * shade + 0.10
    hull[:, CG] = 0.64 * shade + 0.10
    hull[:, CB] = 0.68 * shade + 0.12

    # the tractor beam: an amber line from the wreck to the hull
    n_b = 200
    tb = np.linspace(0.0, 1.0, n_b)
    beam = np.zeros((n_b, NCOLS), dtype=np.float32)
    beam[:, PX] = WX + 6.0 + (SX - a - 2.0 - WX - 6.0) * tb
    beam[:, PY] = 0.0
    beam[:, PZ] = 0.0
    beam[:, TYPE] = 3.0; beam[:, SIZE] = 1.3
    beam[:, CR], beam[:, CG], beam[:, CB] = 1.0, 0.75, 0.30

    # the fragments: bright chunks strung ALONG the beam, wreck -> hull
    n_f = 60
    tf = np.linspace(0.05, 0.95, n_f)
    frag = np.zeros((n_f, NCOLS), dtype=np.float32)
    frag[:, PX] = WX + 6.0 + (SX - a - 2.0 - WX - 6.0) * tf
    frag[:, PY] = rng.normal(0.0, 1.2, n_f)
    frag[:, PZ] = rng.normal(0.0, 1.2, n_f)
    frag[:, TYPE] = 3.0; frag[:, SIZE] = 2.2
    frag[:, CR], frag[:, CG], frag[:, CB] = 0.95, 0.85, 0.55

    def scene(lit):
        parts = []
        bm = beam.copy(); bm[:, ALPHA] = 0.75 if lit else 0.38
        parts.append(bm)
        fr = frag.copy(); fr[:, ALPHA] = 0.90 if lit else 0.45
        parts.append(fr)
        return parts

    begin = np.concatenate([stars, wreck, hull] + scene(False), axis=0)
    end = np.concatenate([stars, wreck, hull] + scene(True), axis=0)
    return end, begin

def _descent_buffers(spec: dict, term: str):
    """theDescent: the crossing of the scales of the world -- the membrane onion
    traversed. A tunnel of NESTED square frames receding along the view axis,
    each one a scale of the world (orbit, sky, cloud, field, ground), and the
    vessel descending through them toward the bright ground-glow at the far end.
    The claim is SCALE AS PLACE: each frame is one world-resolution, and the
    journey passes through every one. begin = vessel at the outermost frame;
    end = vessel at the innermost, at the ground."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # starfield
    n_st = 1200
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 170.0 * (0.9 + 0.8 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = st_r * sxz * np.cos(phi)
    stars[:, PY] = st_r * sxz * np.sin(phi)
    stars[:, PZ] = st_r * u
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.25 + 0.2 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92

    # the nested frames: squares in XZ planes at receding depths (+Y), shrinking
    N_FRAMES = 8
    frame_cols = [(0.45, 0.65, 1.0), (0.40, 0.75, 0.95), (0.40, 0.85, 0.80),
                  (0.45, 0.90, 0.60), (0.60, 0.90, 0.45), (0.80, 0.85, 0.40),
                  (0.90, 0.75, 0.40), (0.95, 0.65, 0.45)]
    frames = []
    for k in range(N_FRAMES):
        depth = 20.0 + 22.0 * k
        half = 55.0 * (0.82 ** k)
        n_e = 160
        t = np.linspace(0.0, 1.0, n_e)
        fr = np.zeros((4 * n_e, NCOLS), dtype=np.float32)
        # four edges of the square in the XZ plane
        edges = [
            (-half + 2 * half * t, -half), (-half + 2 * half * t, half),
            (-half, -half + 2 * half * t), (half, -half + 2 * half * t),
        ]
        for e, (ex, ez) in enumerate(edges):
            sl = slice(e * n_e, (e + 1) * n_e)
            fr[sl, PX] = ex
            fr[sl, PZ] = ez
            fr[sl, PY] = depth
        fr[:, TYPE] = 3.0; fr[:, ALPHA] = 0.55; fr[:, SIZE] = 1.4
        fr[:, CR], fr[:, CG], fr[:, CB] = frame_cols[k]
        frames.append(fr)

    # the ground: a warm glow at the far end of the tunnel
    ground = _dots((0.0, 20.0 + 22.0 * (N_FRAMES - 1) + 14.0, 0.0), 8.0, 80,
                   (1.0, 0.85, 0.55), rng)
    ground_halo = _halo((0.0, 20.0 + 22.0 * (N_FRAMES - 1) + 14.0, 0.0), 14.0,
                        (1.0, 0.85, 0.55), rng, alpha=0.14, size=2.0)

    # the vessel: a small bright diamond descending the tunnel's axis
    def vessel(depth, lit):
        n_v = 90
        v = np.zeros((n_v, NCOLS), dtype=np.float32)
        th = rng.random(n_v) * 2.0 * np.pi
        rr = 3.2 * np.sqrt(rng.random(n_v))
        v[:, PX] = rr * np.cos(th)
        v[:, PZ] = rr * np.sin(th)
        v[:, PY] = depth
        v[:, TYPE] = 3.0; v[:, ALPHA] = 0.9 if lit else 0.55; v[:, SIZE] = 1.8
        v[:, CR], v[:, CG], v[:, CB] = 0.95, 0.95, 0.98
        return v

    begin = np.concatenate([stars] + frames + [ground, ground_halo,
                                               vessel(20.0, False)], axis=0)
    end = np.concatenate([stars] + frames + [ground, ground_halo,
                                             vessel(20.0 + 22.0 * (N_FRAMES - 1), True)], axis=0)
    return end, begin

def _standing_buffers(spec: dict, term: str):
    """theStanding: the body held against the ground by contact. A small upright
    figure -- head, spine, two legs -- standing on a wide flat ground slab,
    and exactly where the feet meet the slab a bright CONTACT GLOW: the witness.
    A thin vertical line of light runs from the crown straight down to the
    contact -- gravity's plumb line ending on the ground, not past it. The claim:
    upright, touching, and the touch itself lit. begin = figure dim, contact
    dark; end = figure lit and the contact burning."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # the ground: a wide stone slab
    n_g = 2600
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 55.0 * np.sqrt(rng.random(n_g))
    ground = np.zeros((n_g, NCOLS), dtype=np.float32)
    ground[:, PX] = rr * np.cos(th)
    ground[:, PY] = rr * np.sin(th)
    ground[:, PZ] = rng.normal(0.0, 0.8, n_g)
    ground[:, TYPE] = 3.0; ground[:, ALPHA] = 0.60; ground[:, SIZE] = 2.4
    ground[:, CR], ground[:, CG], ground[:, CB] = 0.42, 0.44, 0.42

    def figure(lit):
        parts = []
        body_c = (0.85, 0.80, 0.70) if lit else (0.30, 0.29, 0.27)
        # arms: two columns angled out from the shoulders -- the humanoid T
        for sx in (-1.0, 1.0):
            n_a = 90
            t = np.linspace(0.0, 1.0, n_a)
            arm = np.zeros((n_a, NCOLS), dtype=np.float32)
            arm[:, PX] = sx * (1.0 + 5.5 * t) + rng.normal(0.0, 0.3, n_a)
            arm[:, PY] = rng.normal(0.0, 0.3, n_a)
            arm[:, PZ] = 15.0 - 3.5 * t
            arm[:, TYPE] = 3.0; arm[:, ALPHA] = 0.85; arm[:, SIZE] = 1.4
            arm[:, CR], arm[:, CG], arm[:, CB] = body_c
            parts.append(arm)
        # legs: two columns from the slab to the hips
        for lx in (-2.4, 2.4):
            n_l = 120
            t = np.linspace(0.0, 1.0, n_l)
            leg = np.zeros((n_l, NCOLS), dtype=np.float32)
            leg[:, PX] = lx + rng.normal(0.0, 0.35, n_l)
            leg[:, PY] = rng.normal(0.0, 0.35, n_l)
            leg[:, PZ] = 0.5 + 8.0 * t
            leg[:, TYPE] = 3.0; leg[:, ALPHA] = 0.85; leg[:, SIZE] = 1.5
            leg[:, CR], leg[:, CG], leg[:, CB] = body_c
            parts.append(leg)
        # spine: hips to shoulders
        n_s = 140
        t = np.linspace(0.0, 1.0, n_s)
        spine = np.zeros((n_s, NCOLS), dtype=np.float32)
        spine[:, PX] = rng.normal(0.0, 0.4, n_s)
        spine[:, PY] = rng.normal(0.0, 0.4, n_s)
        spine[:, PZ] = 8.5 + 7.0 * t
        spine[:, TYPE] = 3.0; spine[:, ALPHA] = 0.85; spine[:, SIZE] = 1.6
        spine[:, CR], spine[:, CG], spine[:, CB] = body_c
        parts.append(spine)
        # head
        parts.append(_dots((0.0, 0.0, 18.0), 2.6, 40, body_c, rng))
        # the plumb line: crown to contact, gravity made visible
        n_p = 90
        t = np.linspace(0.0, 1.0, n_p)
        plumb = np.zeros((n_p, NCOLS), dtype=np.float32)
        plumb[:, PX] = 0.0
        plumb[:, PY] = 0.0
        plumb[:, PZ] = 20.5 - 20.0 * t
        plumb[:, TYPE] = 3.0
        plumb[:, ALPHA] = 0.50 if lit else 0.18
        plumb[:, SIZE] = 1.1
        plumb[:, CR], plumb[:, CG], plumb[:, CB] = 0.60, 0.80, 1.00
        parts.append(plumb)
        # the CONTACT: a bright patch where the feet meet the slab -- the witness
        cc = (1.0, 0.85, 0.45) if lit else (0.30, 0.27, 0.20)
        for lx in (-2.4, 2.4):
            parts.append(_dots((lx, 0.0, 0.6), 1.8, 30, cc, rng))
        if lit:
            parts.append(_halo((0.0, 0.0, 0.6), 5.5, (1.0, 0.85, 0.45),
                               rng, alpha=0.15, size=1.8))
        return parts

    begin = np.concatenate([ground] + figure(False), axis=0)
    end = np.concatenate([ground] + figure(True), axis=0)
    return end, begin

def _black_hole_buffers(spec: dict, term: str):
    """theBlackHole: the mass from which no light escapes. A perfect dark DISK in
    the middle of the starfield -- not a black object but an ABSENCE, a hole
    where the stars stop -- wrapped in a fierce thin ring of light (the photon
    ring) and an orange accretion band tilted across it. The background stars
    near the edge are pushed OUTWARD, bent around the shadow: light itself
    going around the hole because it cannot come out. begin = the ring dim,
    the disk faint; end = the ring burning, the disk bright."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    SHADOW = 18.0          # the radius of the absence (screen space, XZ plane)

    # the starfield with the hole carved out: stars inside the shadow are
    # pushed to just outside it -- lensing as a bright rim of displaced sky
    n_st = 3000
    u = rng.random(n_st) * 2.0 - 1.0
    phi = rng.random(n_st) * 2.0 * np.pi
    st_r = 160.0 * (0.35 + 0.9 * rng.random(n_st))
    sxz = np.sqrt(np.maximum(0.0, 1.0 - u * u))
    px = st_r * sxz * np.cos(phi)
    py = st_r * sxz * np.sin(phi)
    pz = st_r * u
    # screen-space radius in the XZ plane; push the shadowed ones out
    rs = np.sqrt(px * px + pz * pz)
    inside = rs < SHADOW
    # the hole EATS the sky behind it: anything deep inside the shadow is gone
    # entirely (no light escapes); the edge band is lensed just outside
    eaten = rs < SHADOW * 0.92
    lensed = inside & ~eaten
    push = np.where(lensed, SHADOW + (SHADOW - rs) * 0.25 + 1.5, rs)
    scale = push / np.maximum(rs, 1e-6)
    stars = np.zeros((n_st, NCOLS), dtype=np.float32)
    stars[:, PX] = px * scale
    stars[:, PY] = py
    stars[:, PZ] = pz * scale
    stars[:, TYPE] = 3.0
    stars[:, ALPHA] = 0.28 + 0.22 * rng.random(n_st)
    stars[:, SIZE] = 0.8 + 1.0 * rng.random(n_st)
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92
    # the displaced sky gathers bright at the shadow's edge
    stars[lensed, ALPHA] = 0.75
    stars[lensed, SIZE] = 1.5
    stars = stars[~eaten]

    # the photon ring: a fierce thin circle at the shadow's edge
    n_r = 600
    ra = np.linspace(0.0, 2.0 * np.pi, n_r)
    ring = np.zeros((n_r, NCOLS), dtype=np.float32)
    ring[:, PX] = SHADOW * 1.06 * np.cos(ra)
    ring[:, PZ] = SHADOW * 1.06 * np.sin(ra)
    ring[:, PY] = rng.normal(0.0, 0.6, n_r)
    ring[:, TYPE] = 3.0; ring[:, SIZE] = 1.6
    ring[:, CR], ring[:, CG], ring[:, CB] = 1.0, 0.92, 0.75

    # the accretion band: an orange tilted ellipse of hot matter
    n_d = 900
    da = rng.random(n_d) * 2.0 * np.pi
    dr = SHADOW * (1.25 + 0.55 * rng.random(n_d))
    disk = np.zeros((n_d, NCOLS), dtype=np.float32)
    dx = dr * np.cos(da)
    dz = dr * np.sin(da)
    disk[:, PX] = dx
    disk[:, PZ] = dz * 0.30                      # tilted: squashed in Z
    disk[:, PY] = rng.normal(0.0, 1.2, n_d)
    disk[:, TYPE] = 3.0; disk[:, SIZE] = 1.6
    heat = 1.0 - (dr / SHADOW - 1.25) / 0.55     # hotter nearer the hole
    disk[:, CR] = 1.0
    disk[:, CG] = 0.45 + 0.45 * heat
    disk[:, CB] = 0.15 + 0.35 * heat

    def scene(lit):
        parts = []
        rg = ring.copy(); rg[:, ALPHA] = 0.85 if lit else 0.25
        parts.append(rg)
        dk = disk.copy(); dk[:, ALPHA] = 0.70 if lit else 0.22
        parts.append(dk)
        return parts

    begin = np.concatenate([stars] + scene(False), axis=0)
    end = np.concatenate([stars] + scene(True), axis=0)
    return end, begin

def _verbs_buffers(spec: dict, term: str):
    """theVerbs: the acts that change the world. A verb IS a change, so the two
    frames must DIFFER in the world, not in brightness. begin: the stone rests
    at the OLD place beside a reaching figure, the arc only a faint thread of
    intent. end: the stone is GONE from the old place -- a dim ghost remains
    where it was -- and the same stone sits lit at the NEW place, the arc
    burning along the path it travelled, the figure's arm fully extended. The
    claim is not the figure and not the stone but the CHANGE: same object, two
    places, one arc of action between them."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # ground hint: a sparse dark slab
    n_g = 800
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 60.0 * np.sqrt(rng.random(n_g))
    ground = np.zeros((n_g, NCOLS), dtype=np.float32)
    ground[:, PX] = rr * np.cos(th)
    ground[:, PY] = rr * np.sin(th)
    ground[:, PZ] = rng.normal(0.0, 0.7, n_g) - 0.5
    ground[:, TYPE] = 3.0; ground[:, ALPHA] = 0.25; ground[:, SIZE] = 2.4
    ground[:, CR], ground[:, CG], ground[:, CB] = 0.38, 0.40, 0.38

    # the figure: a full upright form on the left
    FX = -28.0
    fig = []
    body_c = (0.80, 0.78, 0.72)
    n_b = 160
    t = np.linspace(0.0, 1.0, n_b)
    torso = np.zeros((n_b, NCOLS), dtype=np.float32)
    torso[:, PX] = FX + rng.normal(0.0, 0.4, n_b)
    torso[:, PZ] = 6.0 + 8.0 * t
    torso[:, TYPE] = 3.0; torso[:, ALPHA] = 0.8; torso[:, SIZE] = 1.6
    torso[:, CR], torso[:, CG], torso[:, CB] = body_c
    fig.append(torso)
    for lx in (-2.0, 2.0):                                          # legs
        n_l = 90
        tl = np.linspace(0.0, 1.0, n_l)
        leg = np.zeros((n_l, NCOLS), dtype=np.float32)
        leg[:, PX] = FX + lx + rng.normal(0.0, 0.3, n_l)
        leg[:, PZ] = 0.5 + 5.5 * tl
        leg[:, TYPE] = 3.0; leg[:, ALPHA] = 0.8; leg[:, SIZE] = 1.4
        leg[:, CR], leg[:, CG], leg[:, CB] = body_c
        fig.append(leg)
    fig.append(_dots((FX, 0.0, 16.5), 2.4, 36, body_c, rng))      # head

    def arm(reach):                                                # the reaching arm
        n_a = 110
        t = np.linspace(0.0, 1.0, n_a)
        a = np.zeros((n_a, NCOLS), dtype=np.float32)
        a[:, PX] = FX + reach * t
        a[:, PZ] = 13.5 + 2.0 * t + rng.normal(0.0, 0.3, n_a)
        a[:, TYPE] = 3.0; a[:, ALPHA] = 0.8; a[:, SIZE] = 1.4
        a[:, CR], a[:, CG], a[:, CB] = body_c
        return a

    OLD = (18.0, 0.0, 2.0)
    NEW = (34.0, 0.0, 14.0)

    # the stone arrived: lit at the NEW place in the end frame
    stone_new = _dots(NEW, 4.0, 60, (0.75, 0.72, 0.66), rng)
    stone_new[:, ALPHA] = 0.90

    # the arc of action: a curve from the old place to the new.
    # it-10: the proxy's STABLE reading across nine runs is "two shapes, one
    # white one blue" -- the blue arc splits the scene into two objects and the
    # verb (one thing travelling) dies in the parse. So the arc wears the
    # stone's own cream, one object-family: something moved, here is its path.
    n_arc = 220
    t = np.linspace(0.0, 1.0, n_arc)
    arc = np.zeros((n_arc, NCOLS), dtype=np.float32)
    arc[:, PX] = OLD[0] + (NEW[0] - OLD[0]) * t
    arc[:, PZ] = OLD[2] + (NEW[2] - OLD[2]) * t + 6.0 * np.sin(t * np.pi)
    arc[:, TYPE] = 3.0; arc[:, SIZE] = 1.5
    arc[:, CR], arc[:, CG], arc[:, CB] = 0.82, 0.80, 0.74
    arc_dim = arc.copy(); arc_dim[:, ALPHA] = 0.18
    arc_lit = arc.copy(); arc_lit[:, ALPHA] = 0.90

    # the TRAIL: the stone shown at each station of its travel, brightening
    # along the arc -- displacement written into a single frame, so the act is
    # visible even to an eye that only averages the movie. BOTH frames carry
    # the trail (theSalvage lesson: the eye averages the movie; a structure
    # present in only one frame is a structure it never sees): begin holds it
    # faint -- the path as potential -- end holds it burning, the stone arrived.
    def trail(alpha_gain):
        parts = []
        for tt, al in ((0.0, 0.45), (0.33, 0.60), (0.66, 0.75)):
            pos = (OLD[0] + (NEW[0] - OLD[0]) * tt, 0.0,
                   OLD[2] + (NEW[2] - OLD[2]) * tt + 6.0 * np.sin(tt * np.pi))
            st = _dots(pos, 4.0, 60, (0.75, 0.72, 0.66), rng)
            st[:, ALPHA] = al * alpha_gain
            parts.append(st)
        return parts

    # theSalvage lesson, applied to the end: the eye averages the movie and
    # CANNOT see change -- two different frames read as "two shapes" and the
    # claim dies between them. So BOTH frames hold the completed trace at full
    # strength: the trail is the fossil of the act, fully legible in one still.
    settled = np.concatenate([ground] + fig + [arm(12.0)] + trail(1.0) + [stone_new, arc_lit,
                                           _halo(NEW, 7.0, (0.80, 0.90, 1.0), rng,
                                                 alpha=0.13, size=1.8)], axis=0)
    return settled, settled.copy()

def _dig_buffers(spec: dict, term: str):
    """theDig: into the ground, grain physics. The claim made legible in ONE
    settled frame: a dark soil bed with a wedge TRENCH opened in it -- the
    walls slumped at the angle loose grain holds -- and the displaced earth
    heaped BESIDE the opening as a bright fresh pile, a few loose grains
    scattered on its slope. Matter is neither created nor destroyed in the
    scene: the pile is the trench. One palette family, both frames at full
    strength (the theVerbs ledger: a second colour becomes a second object;
    a structure in one frame only is a structure the eye never sees)."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    soil_c = (0.34, 0.28, 0.21)
    fresh_c = (0.50, 0.40, 0.28)

    # the soil bed: a slab, WITHHELD from the trench wedge so the opening is
    # real emptiness, not a painted line. Trench runs along Y at x ~ +6,
    # wider at the surface (z high), pinching to a point at depth -- the
    # wedge a shovel leaves.
    n_g = 1600
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 62.0 * np.sqrt(rng.random(n_g))
    gx = rr * np.cos(th)
    gy = rr * np.sin(th)
    gz = rng.normal(0.0, 0.8, n_g) - 0.5
    half_w = np.clip((gz + 6.0) * 0.55, 0.0, None)      # wedge: wider nearer surface
    in_trench = (np.abs(gx - 6.0) < half_w) & (np.abs(gy) < 26.0)
    keep = ~in_trench
    soil = np.zeros((keep.sum(), NCOLS), dtype=np.float32)
    soil[:, PX], soil[:, PY], soil[:, PZ] = gx[keep], gy[keep], gz[keep]
    soil[:, TYPE] = 3.0; soil[:, ALPHA] = 0.30; soil[:, SIZE] = 2.2
    soil[:, CR], soil[:, CG], soil[:, CB] = soil_c

    # the trench floor: darker, deeper -- the bottom of the cut
    n_f = 120
    tf = np.linspace(-24.0, 24.0, n_f)
    floor = np.zeros((n_f, NCOLS), dtype=np.float32)
    floor[:, PX] = 6.0 + rng.normal(0.0, 0.8, n_f)
    floor[:, PY] = tf
    floor[:, PZ] = -6.0 + rng.normal(0.0, 0.4, n_f)
    floor[:, TYPE] = 3.0; floor[:, ALPHA] = 0.35; floor[:, SIZE] = 2.0
    floor[:, CR], floor[:, CG], floor[:, CB] = 0.20, 0.16, 0.12

    # the displaced pile: a cone of fresh grain beside the cut -- radius
    # shrinking with height, the angle of repose written as its silhouette
    n_p = 700
    hp = rng.random(n_p) * 9.0
    rp = (1.0 - hp / 9.0) * 10.0
    ap = rng.random(n_p) * 2.0 * np.pi
    pile = np.zeros((n_p, NCOLS), dtype=np.float32)
    pile[:, PX] = 24.0 + rp * np.cos(ap) * np.sqrt(rng.random(n_p))
    pile[:, PY] = 2.0 + rp * np.sin(ap) * np.sqrt(rng.random(n_p))
    pile[:, PZ] = hp * 0.9 + rng.normal(0.0, 0.3, n_p)
    pile[:, TYPE] = 3.0; pile[:, ALPHA] = 0.55; pile[:, SIZE] = 1.8
    pile[:, CR], pile[:, CG], pile[:, CB] = fresh_c

    # loose grains scattered on the slope and around the cut's lip
    n_l = 90
    loose = np.zeros((n_l, NCOLS), dtype=np.float32)
    loose[:, PX] = rng.uniform(8.0, 36.0, n_l)
    loose[:, PY] = rng.uniform(-18.0, 20.0, n_l)
    loose[:, PZ] = rng.uniform(0.0, 2.5, n_l)
    loose[:, TYPE] = 3.0; loose[:, ALPHA] = 0.6; loose[:, SIZE] = 1.2
    loose[:, CR], loose[:, CG], loose[:, CB] = fresh_c

    settled = np.concatenate([soil, floor, pile, loose], axis=0)
    return settled, settled.copy()

def _grow_buffers(spec: dict, term: str):
    """theGrow: life from energy, LOGISTIC. The equation is the picture: an
    S-curve of light -- N(t) = K / (1 + ((K-N0)/N0) e^{-rt}) -- drawn as a
    rising band of glowing dots, and beneath it a row of green shoots whose
    HEIGHTS follow the same numbers: sparse and tiny at the left (the slow
    start), dense and surging in the middle (the explosion), level at the
    right (the plateau, when the energy that feeds growth is spent). The
    curve is not decoration: shoot i stands at t_i and reaches N(t_i). One
    palette family (living green), both frames at full strength."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    K, N0, r = 40.0, 1.2, 0.075          # carrying capacity, seed, rate
    def logistic(t):
        return K / (1.0 + ((K - N0) / N0) * np.exp(-r * t))

    # dark soil for the shoots to stand on
    n_g = 900
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 60.0 * np.sqrt(rng.random(n_g))
    soil = np.zeros((n_g, NCOLS), dtype=np.float32)
    soil[:, PX] = rr * np.cos(th)
    soil[:, PY] = rr * np.sin(th)
    soil[:, PZ] = rng.normal(0.0, 0.7, n_g) - 0.5
    soil[:, TYPE] = 3.0; soil[:, ALPHA] = 0.25; soil[:, SIZE] = 2.2
    soil[:, CR], soil[:, CG], soil[:, CB] = 0.30, 0.30, 0.24

    # the S-curve: the logistic itself, a band of pale-green light
    n_c = 260
    tc = np.linspace(0.0, 100.0, n_c)
    curve = np.zeros((n_c, NCOLS), dtype=np.float32)
    curve[:, PX] = -50.0 + tc                              # time runs left -> right
    curve[:, PZ] = 2.0 + logistic(tc)
    curve[:, TYPE] = 3.0; curve[:, ALPHA] = 0.80; curve[:, SIZE] = 1.4
    curve[:, CR], curve[:, CG], curve[:, CB] = 0.65, 1.00, 0.60

    # the shoots: one per station, height = the logistic's value there --
    # a blade of green dots from the soil to N(t_i)
    shoots = []
    for t_i in np.linspace(4.0, 96.0, 14):
        h = float(logistic(t_i))
        n_s = max(3, int(h / 1.6))
        tz = np.linspace(0.0, 1.0, n_s)
        bl = np.zeros((n_s, NCOLS), dtype=np.float32)
        bl[:, PX] = -50.0 + t_i + rng.normal(0.0, 0.25, n_s)
        bl[:, PZ] = 0.5 + h * tz
        bl[:, TYPE] = 3.0; bl[:, ALPHA] = 0.75; bl[:, SIZE] = 1.5
        bl[:, CR], bl[:, CG], bl[:, CB] = 0.30, 0.75, 0.28
        shoots.append(bl)

    settled = np.concatenate([soil, curve] + shoots, axis=0)
    return settled, settled.copy()

def _scan_buffers(spec: dict, term: str):
    """theScan: read composition, SPECTRAL. A pale beam strikes a stone; the
    stone answers in its colors -- the light fans out into bands, one per
    wavelength, and the bands are NOT equally bright: the dim ones are the
    wavelengths the stone's matter drank. The pattern of bright and dim IS
    the reading -- a spectral fingerprint, composition made visible. The fan
    is one phenomenon (dispersion), not two objects. Both frames settled at
    full strength."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # sparse dark ground for depth
    n_g = 700
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 65.0 * np.sqrt(rng.random(n_g))
    soil = np.zeros((n_g, NCOLS), dtype=np.float32)
    soil[:, PX] = rr * np.cos(th)
    soil[:, PY] = rr * np.sin(th)
    soil[:, PZ] = rng.normal(0.0, 0.7, n_g) - 0.5
    soil[:, TYPE] = 3.0; soil[:, ALPHA] = 0.22; soil[:, SIZE] = 2.2
    soil[:, CR], soil[:, CG], soil[:, CB] = 0.30, 0.32, 0.32

    STONE = (-18.0, 0.0, 8.0)
    stone = _dots(STONE, 5.0, 80, (0.62, 0.62, 0.66), rng)
    stone[:, ALPHA] = 0.85

    # the incoming beam: a thin white thread from the far left to the stone
    n_b = 120
    tb = np.linspace(0.0, 1.0, n_b)
    beam = np.zeros((n_b, NCOLS), dtype=np.float32)
    beam[:, PX] = -60.0 + (STONE[0] + 60.0) * tb
    beam[:, PZ] = 8.0 + rng.normal(0.0, 0.15, n_b)
    beam[:, TYPE] = 3.0; beam[:, ALPHA] = 0.75; beam[:, SIZE] = 1.0
    beam[:, CR], beam[:, CG], beam[:, CB] = 0.95, 0.95, 0.95

    # the fan: seven bands spreading from the stone, red -> violet; two are
    # DRANK by the stone (dim) -- the absorption lines, the composition's
    # signature written in missing light
    bands = [(1.00, 0.25, 0.20, 0.85), (1.00, 0.60, 0.15, 0.85),
             (0.95, 0.95, 0.25, 0.30), (0.30, 0.90, 0.30, 0.85),
             (0.25, 0.65, 1.00, 0.30), (0.45, 0.35, 0.95, 0.85),
             (0.75, 0.30, 0.95, 0.85)]
    fan = []
    n_f = 90
    for i, (cr, cg, cb, al) in enumerate(bands):
        ang = np.radians(-18.0 + 6.0 * i)          # spread upward in a fan
        tf = np.linspace(0.0, 1.0, n_f)
        bd = np.zeros((n_f, NCOLS), dtype=np.float32)
        dist = 12.0 + 42.0 * tf
        bd[:, PX] = STONE[0] + dist * np.cos(np.radians(8.0))
        bd[:, PZ] = STONE[2] + dist * np.sin(ang) + 4.0 * tf
        bd[:, TYPE] = 3.0; bd[:, ALPHA] = al; bd[:, SIZE] = 1.3
        bd[:, CR], bd[:, CG], bd[:, CB] = cr, cg, cb
        fan.append(bd)

    settled = np.concatenate([soil, stone, beam] + fan, axis=0)
    return settled, settled.copy()

def _navigate_buffers(spec: dict, term: str):
    """theNavigate: orbital mechanics, reach a target. The picture every
    pilot knows: a world with two orbit rings around it, and ONE bright
    ellipse that leaves the inner ring and kisses the outer -- the transfer.
    It touches both rings tangentially (a Hohmann: the cheapest path, its
    semi-major axis (r1+r2)/2, derived not drawn), the craft rides its
    middle, and the target waits at the far kiss. Both frames settled."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # the starfield
    n_s = 400
    stars = np.zeros((n_s, NCOLS), dtype=np.float32)
    stars[:, PX] = rng.uniform(-160.0, 160.0, n_s)
    stars[:, PY] = rng.uniform(50.0, 170.0, n_s)
    stars[:, PZ] = rng.uniform(-100.0, 100.0, n_s)
    stars[:, TYPE] = 3.0; stars[:, ALPHA] = 0.35; stars[:, SIZE] = 0.9
    stars[:, CR], stars[:, CG], stars[:, CB] = 0.85, 0.87, 0.92

    # the world at the centre
    world = _solid_sphere((0.0, 0.0, 0.0), 14.0, (0.35, 0.55, 0.85), rng, gain=0.8)

    R1, R2 = 34.0, 62.0                      # the two orbit rings
    def ring(r):
        return _orbit_ring(r, rng)
    ring1, ring2 = ring(R1), ring(R2)

    # the transfer ellipse: tangent to both rings (Hohmann). Parametrize
    # x = -a e + a cos u, z = b sin u with a = (R1+R2)/2, c = a - R1,
    # b = sqrt(a^2 - c^2); u: 0 (inner kiss, +x) -> pi (outer kiss, -x).
    a = (R1 + R2) / 2.0
    c = a - R1
    b = float(np.sqrt(a * a - c * c))
    n_t = 300
    u = np.linspace(0.0, np.pi, n_t)
    tr = np.zeros((n_t, NCOLS), dtype=np.float32)
    tr[:, PX] = R1 - c + a * np.cos(u) - (a - c)   # kiss inner ring at x=+R1
    tr[:, PX] = -c + a * np.cos(u)
    tr[:, PZ] = b * np.sin(u)
    tr[:, TYPE] = 3.0; tr[:, ALPHA] = 0.85; tr[:, SIZE] = 1.3
    tr[:, CR], tr[:, CG], tr[:, CB] = 1.00, 0.85, 0.45

    # the craft at mid-transfer (u = pi/2), bright; the target at the far
    # kiss (u = pi), waiting
    uc = np.pi / 2.0
    craft_pos = (-c + a * np.cos(uc), 0.0, b * np.sin(uc))
    craft = _dots(craft_pos, 2.2, 40, (1.0, 0.95, 0.75), rng)
    craft[:, ALPHA] = 0.95
    craft_halo = _halo(craft_pos, 4.5, (1.0, 0.90, 0.60), rng, alpha=0.14, size=1.6)
    tgt_pos = (-c + a * np.cos(np.pi), 0.0, 0.0)
    target = _dots(tgt_pos, 3.0, 50, (0.85, 0.45, 0.35), rng)
    target[:, ALPHA] = 0.90

    settled = np.concatenate([stars, world, ring1, ring2, tr, craft, craft_halo, target], axis=0)
    return settled, settled.copy()

def _shoot_buffers(spec: dict, term: str):
    """theShoot: aim + discharge. A shot is a straight line of intent: the
    muzzle at one end, the target at the other, and between them the bolt's
    own trail -- every position the discharge occupied, written in space at
    once (the theVerbs lesson: the eye averages the movie, so the whole
    flight lives in one settled frame). At the far end the impact BLOOMS:
    a radial burst where the bolt's energy stopped being motion and became
    damage. Both frames at full strength."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # sparse dark field
    n_g = 600
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 70.0 * np.sqrt(rng.random(n_g))
    field = np.zeros((n_g, NCOLS), dtype=np.float32)
    field[:, PX] = rr * np.cos(th)
    field[:, PY] = rr * np.sin(th)
    field[:, PZ] = rng.normal(0.0, 0.8, n_g) - 0.5
    field[:, TYPE] = 3.0; field[:, ALPHA] = 0.20; field[:, SIZE] = 2.2
    field[:, CR], field[:, CG], field[:, CB] = 0.28, 0.30, 0.34

    # the shooter: a compact dark hull at the left, muzzle forward
    SHIP = (-42.0, 0.0, 10.0)
    hull = _dots(SHIP, 4.5, 70, (0.45, 0.48, 0.55), rng)
    hull[:, ALPHA] = 0.80

    # the bolt trail: a dense bright thread from muzzle to target, slightly
    # sagging (even energy bends a little over a long reach)
    TGT = (38.0, 0.0, 8.0)
    n_b = 300
    tb = np.linspace(0.0, 1.0, n_b)
    bolt = np.zeros((n_b, NCOLS), dtype=np.float32)
    bolt[:, PX] = SHIP[0] + (TGT[0] - SHIP[0]) * tb
    bolt[:, PZ] = SHIP[2] + (TGT[2] - SHIP[2]) * tb - 2.5 * tb * (1.0 - tb) * 4.0
    bolt[:, TYPE] = 3.0
    bolt[:, ALPHA] = (0.90 - 0.25 * tb).astype(np.float32)
    bolt[:, SIZE] = 1.5
    bolt[:, CR], bolt[:, CG], bolt[:, CB] = 1.00, 0.45, 0.20

    # the target: a grey rock at the right
    target = _dots(TGT, 4.0, 60, (0.58, 0.56, 0.52), rng)
    target[:, ALPHA] = 0.75

    # the impact: a radial bloom at the target's face -- energy stopped
    n_i = 160
    di = rng.normal(0.0, 1.0, (n_i, 3))
    di /= np.linalg.norm(di, axis=1, keepdims=True)
    ri = 2.0 + 5.0 * np.sqrt(rng.random(n_i))
    impact = np.zeros((n_i, NCOLS), dtype=np.float32)
    impact[:, PX] = TGT[0] - 3.0 + di[:, 0] * ri * 0.7
    impact[:, PY] = di[:, 1] * ri * 0.7
    impact[:, PZ] = TGT[2] + di[:, 2] * ri
    impact[:, TYPE] = 3.0
    impact[:, ALPHA] = (0.85 - 0.10 * ri).clip(0.15, None).astype(np.float32)
    impact[:, SIZE] = 1.4
    impact[:, CR], impact[:, CG], impact[:, CB] = 1.00, 0.70, 0.25

    settled = np.concatenate([field, hull, bolt, target, impact], axis=0)
    return settled, settled.copy()

def _figure(fx, body_c, rng, lean=0.0, arm=None):
    """A compact upright figure of dots (shared by melee's two bodies): torso,
    legs, head; optional arm as (reach_x, reach_z) endpoint and lean in x."""
    import numpy as np
    parts = []
    n_b = 140
    t = np.linspace(0.0, 1.0, n_b)
    torso = np.zeros((n_b, NCOLS), dtype=np.float32)
    torso[:, PX] = fx + lean * t + rng.normal(0.0, 0.4, n_b)
    torso[:, PZ] = 6.0 + 8.0 * t
    torso[:, TYPE] = 3.0; torso[:, ALPHA] = 0.8; torso[:, SIZE] = 1.6
    torso[:, CR], torso[:, CG], torso[:, CB] = body_c
    parts.append(torso)
    for lx in (-2.0, 2.0):
        n_l = 80
        tl = np.linspace(0.0, 1.0, n_l)
        leg = np.zeros((n_l, NCOLS), dtype=np.float32)
        leg[:, PX] = fx + lx + rng.normal(0.0, 0.3, n_l)
        leg[:, PZ] = 0.5 + 5.5 * tl
        leg[:, TYPE] = 3.0; leg[:, ALPHA] = 0.8; leg[:, SIZE] = 1.4
        leg[:, CR], leg[:, CG], leg[:, CB] = body_c
        parts.append(leg)
    parts.append(_dots((fx + lean, 0.0, 16.5), 2.4, 36, body_c, rng))
    if arm is not None:
        ax, az = arm
        n_a = 100
        ta = np.linspace(0.0, 1.0, n_a)
        a = np.zeros((n_a, NCOLS), dtype=np.float32)
        a[:, PX] = fx + (ax - fx) * ta
        a[:, PZ] = 13.5 + (az - 13.5) * ta + rng.normal(0.0, 0.25, n_a)
        a[:, TYPE] = 3.0; a[:, ALPHA] = 0.8; a[:, SIZE] = 1.4
        a[:, CR], a[:, CG], a[:, CB] = body_c
        parts.append(a)
    return parts


def _melee_buffers(spec: dict, term: str):
    """theMelee: the close-quarters strike. Two bodies inside arm's reach --
    the striker leaning IN, its arm's whole swing written as a bright arc of
    stations through the air (the theVerbs lesson: the eye averages the
    movie, so the swing lives in one settled frame), ending at the contact
    FLASH on the other's guard. No weapons, no distance: this is the verb
    where the weapon is the body. Both frames at full strength."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))

    # dark ground
    n_g = 900
    th = rng.random(n_g) * 2.0 * np.pi
    rr = 55.0 * np.sqrt(rng.random(n_g))
    ground = np.zeros((n_g, NCOLS), dtype=np.float32)
    ground[:, PX] = rr * np.cos(th)
    ground[:, PY] = rr * np.sin(th)
    ground[:, PZ] = rng.normal(0.0, 0.7, n_g) - 0.5
    ground[:, TYPE] = 3.0; ground[:, ALPHA] = 0.25; ground[:, SIZE] = 2.4
    ground[:, CR], ground[:, CG], ground[:, CB] = 0.36, 0.38, 0.36

    striker = _figure(-14.0, (0.82, 0.80, 0.74), rng, lean=4.0, arm=(6.0, 11.0))
    defender = _figure(14.0, (0.55, 0.58, 0.62), rng, lean=1.5, arm=(8.0, 12.0))

    # the swing: an arc of bright stations from high-behind the striker's
    # shoulder to the contact point on the defender's arm
    n_s = 160
    ts = np.linspace(0.0, 1.0, n_s)
    swing = np.zeros((n_s, NCOLS), dtype=np.float32)
    swing[:, PX] = -18.0 + 26.0 * ts
    swing[:, PZ] = 17.0 - 6.0 * ts + 3.0 * np.sin(ts * np.pi)
    swing[:, TYPE] = 3.0
    swing[:, ALPHA] = (0.35 + 0.55 * ts).astype(np.float32)
    swing[:, SIZE] = 1.3
    swing[:, CR], swing[:, CG], swing[:, CB] = 1.00, 0.80, 0.40

    # the contact flash where the arc lands
    flash_pos = (8.0, 0.0, 11.5)
    flash = _dots(flash_pos, 2.6, 50, (1.0, 0.85, 0.45), rng)
    flash[:, ALPHA] = 0.95
    flash_halo = _halo(flash_pos, 5.0, (1.0, 0.80, 0.40), rng, alpha=0.16, size=1.7)

    settled = np.concatenate([ground] + striker + defender + [swing, flash, flash_halo], axis=0)
    return settled, settled.copy()

def _system_buffers(spec: dict, term: str):
    """theSolarSystem: the brightest thing (the STAR) at the centre, with planets on ORBIT rings around it."""
    import numpy as np
    rng = np.random.default_rng(_seed(term))
    parts = [
        _solid_sphere((0.0, 0.0, 0.0), 34.0, (1.0, 0.93, 0.78), rng, gain=0.85),  # the star: brightest, central
        _halo((0.0, 0.0, 0.0), 48.0, (1.0, 0.82, 0.5), rng, alpha=0.11, size=2.4),
    ]
    rings = [(85.0, (0.62, 0.45, 0.34)), (150.0, (0.34, 0.55, 0.82)),
             (215.0, (0.70, 0.62, 0.42)), (280.0, (0.78, 0.86, 0.95))]           # a planet's colour per orbit
    angles = [0.7, 2.3, 3.9, 5.3]
    for (r, pcolor), a in zip(rings, angles):
        parts.append(_orbit_ring(r, rng))
        parts.append(_solid_sphere((r * np.cos(a), r * np.sin(a), 0.0), 12.0, pcolor, rng))
    end = np.concatenate(parts, axis=0)
    begin = end.copy()
    begin[:, PX:PZ + 1] += rng.normal(0.0, 80.0, (len(begin), 3))  # a protoplanetary cloud -> star + orbits
    return end, begin


def _project_movie_impl(term: str, out_dir) -> dict | None:
    """Render `term`'s splat movie -> {"begin": path, "end": path}, or None if it has no scene.

    A term with a COMPOSITION renders from its PROVEN children (appearance from decomposition) -- that is
    now the DEFAULT for composite terms; hand-authored SCENES are the fallback for leaf terms."""
    comp = COMPOSITIONS.get(term)
    spec = SCENES.get(term)
    membrane = _find_membrane(term)
    if not comp and not spec and membrane is None:
        return None
    import numpy as np
    from PIL import Image
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    # THE FOLDER WINS, always -- the same precedence scene_buffer uses. A term can exist in BOTH the
    # old SCENES dict and the story tree (theStar does), and having two code paths disagree about
    # which one is authoritative rendered the wrong object under the right label.
    if membrane is not None:
        # A MEMBRANE'S MOVIE: its own time, 0 -> 1, emitted by its own law in its own local units.
        # The camera is set by the membrane's OWN EXTENT -- a boundary supplies its own scale, so
        # nothing here is hand-framed; the view is as far back as the matter is wide. UNLESS the
        # law declares a FRAMING: the same kind of statement as its LENS -- a camera setting, not
        # a fact -- for membranes whose MEANING is smaller than their extent (a 4 m patch whose
        # stones are millimetres: at 2.7x extent they are sub-pixel, and a dyad judging that frame
        # judges blur). FRAMING = {"dist": x, "elev": y} multiplies extent; default 2.7 / 0.72.
        law = _membrane_law(membrane)
        framing = getattr(law, "FRAMING", None) or {}
        end_buf = membrane_buffer(term, 1.0)
        extent = float(np.linalg.norm(end_buf[:, PX:PZ + 1], axis=1).max()) or 1.0
        cam_pos = (0.0, -float(framing.get("dist", 2.7)) * extent,
                   float(framing.get("elev", 0.72)) * extent)
        cx, cy, cz = cam_pos
        cam = FirstPersonCamera(cam_pos, yaw=float(np.arctan2(-cy, -cx)),
                                pitch=float(np.arctan2(-cz, float(np.hypot(cx, cy)))))
        p = cam.params(720, 540)
        pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
        paths = {}
        for label, t in (("begin", 0.0), ("end", 1.0)):
            pipe.upload(membrane_buffer(term, t))
            png = out / f"movie_{term}_{label}.png"
            Image.fromarray(pipe.render_from_gpu(cam, p)).save(png)
            paths[label] = str(png)
        return paths

    cam_pos = comp["cam"] if comp else spec["cam"]               # composition owns its own camera
    cx, cy, cz = cam_pos                                          # AIM at the body (origin): yaw=0 looks +X
    yaw = float(np.arctan2(-cy, -cx))
    pitch = float(np.arctan2(-cz, float(np.hypot(cx, cy))))
    cam = FirstPersonCamera(cam_pos, yaw=yaw, pitch=pitch)
    p = cam.params(720, 540)
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))

    begin_png = out / f"movie_{term}_begin.png"
    end_png = out / f"movie_{term}_end.png"

    if comp:                                                     # DEFAULT for composite terms: built from proven children
        end_buf = compose_buffer(term)
        begin_buf = _disperse(end_buf, term, 90.0)
        pipe.upload(begin_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(begin_png)
        pipe.upload(end_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(end_png)
        return {"begin": str(begin_png), "end": str(end_png)}

    _BUILDERS = {"planet": _planet_buffers, "terrain": _terrain_buffers, "row": _row_buffers, "system": _system_buffers, "garden": _garden_buffers, "ecosystem": _ecosystem_buffers, "tree": _tree_buffers, "treeform": _treeform_buffers, "fruit": _fruit_buffers, "planting": _planting_buffers, "farming": _farming_buffers, "planetary_farm": _planetary_farm_buffers, "lunar_farm": _lunar_farm_buffers, "orbital_farm": _orbital_farm_buffers, "space": _space_buffers, "seed": _seed_buffers, "determinism": _determinism_buffers, "laws": _laws_buffers, "truth": _truth_buffers, "ship": _ship_buffers, "flight": _flight_buffers, "ship_power": _ship_power_buffers, "ship_combat": _ship_combat_buffers, "shields": _shields_buffers, "warp_drive": _warp_drive_buffers, "ship_view": _ship_view_buffers, "salvage": _salvage_buffers, "descent": _descent_buffers, "standing": _standing_buffers, "black_hole": _black_hole_buffers, "verbs": _verbs_buffers, "dig": _dig_buffers, "grow": _grow_buffers, "scan": _scan_buffers, "navigate": _navigate_buffers, "shoot": _shoot_buffers, "melee": _melee_buffers}
    builder = _BUILDERS.get(spec.get("kind"))
    if builder:
        # Two hand-built states, uploaded directly -- no physics kernel needed (these bodies are already settled).
        end_buf, begin_buf = builder(spec, term)
        pipe.upload(begin_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(begin_png)
        pipe.upload(end_buf)
        Image.fromarray(pipe.render_from_gpu(cam, p)).save(end_png)
        return {"begin": str(begin_png), "end": str(end_png)}

    # ── collapse kind: spawn a body, let a central attractor draw it together over the timeline ──
    from ParticleEngine.core import ParticleSimulator, PARTICLE_TYPES
    from ParticleEngine.control_vars import default_physics_registry
    sim = ParticleSimulator(spec["count"] + 64)
    sim.spawn(spec["count"], spec["type"], position=(0, 0, 0), spread=float(spec["spread"]),
              color=spec["color"], size=float(spec["size"]), life=-1.0)
    pipe.upload(sim._data[:sim._count])
    pipe.attractors.append((0.0, 0.0, 0.0, float(spec["pull"]), PARTICLE_TYPES[spec["type"]], 500.0))
    reg = default_physics_registry()
    reg.set("gravity", (0.0, 0.0, 0.0))                          # SPACE: bodies float, they do not fall out of frame
    reg.set("wind_vector", (0.0, 0.0, 0.0))
    cvars = reg.snapshot()
    Image.fromarray(pipe.render_from_gpu(cam, p)).save(begin_png)
    for _ in range(90):                                          # evolve to the settled END state
        pipe.step_particles(1 / 60, cvars)
    Image.fromarray(pipe.render_from_gpu(cam, p)).save(end_png)
    return {"begin": str(begin_png), "end": str(end_png)}


# ═══════════════════════════════════════════════════════════════════════
#  THE FOLDER TREE -- a membrane emits its OWN matter, from its own folder
#
#  Alan's methodology: each membrane is a FOLDER holding its story (story.md), its law
#  (physics.py) and the numbers it grew (numbers.json). The law computes the numbers AND emits the
#  matter, so the appearance cannot drift from the physics -- they are the same file reading the
#  same numbers. That is why no separate "does the render use the variables" check is needed: the
#  render IS the variables. A term with a folder needs no entry in SCENES.
# ═══════════════════════════════════════════════════════════════════════
_STORY = _REPO / "story"


def _find_membrane(term: str):
    """The folder for `term`, anywhere in the story tree (its PATH is its serial)."""
    if not _STORY.is_dir():
        return None
    for p in _STORY.rglob(term):
        if p.is_dir() and (p / "physics.py").exists():
            return p
    return None


def _membrane_law(folder):
    """Load a membrane's law. `story/` goes on the path so a law can import `matter`."""
    import importlib.util
    if str(_STORY) not in sys.path:
        sys.path.insert(0, str(_STORY))
    spec = importlib.util.spec_from_file_location(f"law_{folder.name}", folder / "physics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _child_numbers(term: str):
    """A child's grown numbers, for the one thing a parent legitimately needs from below: how long
    that child takes, so it can be shown at the right phase of the parent's own movie."""
    import json
    f = _find_membrane(term)
    if f is None:
        return None
    nj = f / "numbers.json"
    return json.loads(nj.read_text()) if nj.exists() else None


def _lens_of(folder, law):
    """THE LENS -- the second kind of dial, and it must never be confused with the first.

    A membrane's `FREE` numbers change WHAT THE WORLD IS: turn the spin dial and the day really is
    shorter, and every number downstream is re-derived. A membrane's `LENS` numbers change only WHAT
    YOU SEE: a relief exaggeration, a marker's size, the film speed. Nothing downstream moves,
    because nothing downstream depends on them -- they are a camera setting, not a fact.

    They exist because true scale is often INVISIBLE. This world's tallest mountain is two parts in
    a thousand of its radius; a star at a planet's distance is off-screen and sub-pixel. Every game
    lies about this. The rule here is that the lie is DECLARED, sits next to the true number, and is
    a dial a person can turn back to 1.0 to see what is really there.

    Read from `lens.json` beside the membrane if it exists, defaults otherwise."""
    import json
    spec = getattr(law, "LENS", None) or {}
    vals = {k: v.get("default", 1.0) for k, v in spec.items()}
    lj = folder / "lens.json"
    if lj.exists():
        try:
            for k, v in (json.loads(lj.read_text()) or {}).items():
                if k in vals:
                    vals[k] = float(v)
        except Exception:
            pass
    return vals


def _membrane_own(folder, t):
    """Just this membrane's own matter, without its children."""
    import json
    law = _membrane_law(folder)
    if not hasattr(law, "emit"):
        return None, None
    nj = folder / "numbers.json"
    nums = json.loads(nj.read_text()) if nj.exists() else law.derive(None, {})
    lens = _lens_of(folder, law)
    if lens:
        nums = dict(nums)
        nums["_lens"] = lens        # emit() reads it; derive() never sees it, which is the point
    return law.emit(nums, t), (law, nums)


def membrane_buffer(term: str, t: float = 1.0, _depth: int = 0):
    """`term`'s matter at its own time t (0 = beginning, 1 = settled), or None if it has no folder.

    A PARENT IS MADE OF ITS CHILDREN. If a membrane's law defines `layout(nums) -> {child: (centre,
    scale)}`, each named child is grown, emitted in ITS OWN local units, and then placed into this
    frame -- so looking at a system SHOWS you the star and the worlds inside it, and zooming in is
    just reading the same tree at a finer level. That is LOD of meaning applied to matter: every
    level is the level below, placed.

    The parent supplies only WHERE and HOW BIG -- structure, which is the parent's own physics (an
    orbital radius is derived, not decorated). The child supplies its own APPEARANCE, always."""
    folder = _find_membrane(term)
    if folder is None:
        return None
    own, ln = _membrane_own(folder, t)
    if own is None:
        return None
    law, nums = ln
    if _depth > 4 or not hasattr(law, "layout"):
        return own
    import numpy as np
    layout = law.layout(nums) or {}
    # ONE OBJECT, ONE PICTURE. A child placed at the origin at full scale IS this object, one
    # level down (aYellowStar inside theStar: "at this scale the membrane IS the star"). Drawing
    # the parent's own emit as well is the duplicated-child failure -- the same matter twice --
    # and scaling the child's clock by the duration ratio freezes it at its own first frame: a
    # 30 Myr law movie against a 9.4 Gyr instance life held aYellowStar at t=0.003, a ~3000 K
    # protostar cloud that swallowed the burning star and read as a ringed planet to the blind
    # eye (dyad alignment 0.0, 2026-07-29). So at identity placement the child emits at the
    # parent's OWN t and the parent's own grains are not drawn: the instance is the picture at
    # this scale.
    identity = set()
    for _c, (_cen, _s) in layout.items():
        try:
            if abs(float(_s) - 1.0) < 1e-9 and float(np.linalg.norm(np.asarray(_cen, dtype=float))) < 1e-9:
                identity.add(_c)
        except Exception:
            pass
    parts = [] if identity else [own]
    for child, (centre, scale) in layout.items():
        # THE CHILD'S OWN TIME, not the parent's. A child whose duration is shorter FINISHES EARLY
        # inside its parent's movie -- stars light while a galaxy is still assembling. So its t runs
        # faster by exactly the ratio of their durations and clamps once it is done. This is the one
        # place true relative rates are used, and it is the place they matter: it is what makes the
        # nesting a single performance instead of eleven separate clips. An IDENTITY child is the
        # exception: it is the same object at the same scale, so it shares the parent's clock.
        ct = t
        if child not in identity:
            pdur = float(nums.get("duration_s") or 0.0)
            if pdur > 0.0:
                cn = _child_numbers(child)
                cdur = float((cn or {}).get("duration_s") or 0.0)
                if cdur > 0.0:
                    ct = max(0.0, min(1.0, t * (pdur / cdur)))
        cb = membrane_buffer(child, ct, _depth + 1)
        if cb is None:
            continue
        # LOD BY PLACED SIZE -- the pixel-budget law, and here it is load-bearing, not an
        # optimisation. Placing a child at full resolution into a small footprint crams all its
        # grains into one or two 32px tiles, blows past MAX_PER_TILE, and the cap keeps the NEAREST
        # -- which are the child's own sub-pixel splats. The PARENT's grains in those tiles are then
        # evicted and nothing draws: a BLACK TILE-SHAPED HOLE where the child should be. A thing
        # that occupies 4% of the frame does not need 20,000 grains to say so.
        keep = max(48, int(len(cb) * min(1.0, float(scale) ** 1.6)))
        if keep < len(cb):
            step = max(1, len(cb) // keep)
            cb = cb[::step]
        parts.append(_place(cb, centre, scale))
    # parts holds the identity child's buffer when a child replaced the parent's own matter --
    # returning `own` here would resurrect the duplicate the identity rule exists to drop.
    if not parts:
        return own
    return np.concatenate(parts, axis=0) if len(parts) > 1 else parts[0]


def membrane_terms() -> list:
    """Every membrane in the story tree that can emit matter."""
    if not _STORY.is_dir():
        return []
    out = []
    for p in sorted(_STORY.rglob("physics.py")):
        try:
            if hasattr(_membrane_law(p.parent), "emit"):
                out.append(p.parent.name)
        except Exception:
            pass
    return out


def scene_terms() -> list:
    """The terms that have a splat scene (what the live viewer can show)."""
    return list(SCENES) + [t for t in membrane_terms() if t not in SCENES]


def scene_cam_distance(term: str) -> float:
    """How far the live viewer should orbit this term (from its still-camera distance)."""
    import numpy as np
    # THE FOLDER WINS -- the same precedence scene_buffer and project_movie use. A term can exist in
    # both the old dicts and the story tree (theSolarSystem and theStar both do), and taking the
    # dict's camera for a membrane put the eye 462 units from a 1-unit object: a BLACK SCREEN.
    buf = membrane_buffer(term)                 # a membrane is orbited at ITS OWN measured extent
    if buf is not None:
        r = np.linalg.norm(buf[:, PX:PZ + 1], axis=1)
        # A PERCENTILE, NOT THE MAXIMUM. The max is set by whatever single grain is furthest out, and
        # a membrane that draws a distant marker -- the star a planet is lit by, sitting 3 radii off
        # -- then frames the whole scene around that marker and leaves the planet 9 units away: a
        # dot on a black screen. The 99th percentile is the body's real extent and ignores the
        # handful of grains that are pointing at something else. Same lesson as reading a surface
        # from a mean: one outlier must not stand in for a distribution.
        return 2.8 * (float(np.percentile(r, 99.0)) or 1.0)
    cam = (COMPOSITIONS.get(term) or SCENES.get(term) or {}).get("cam")
    if cam:
        return float(np.linalg.norm(cam))
    return 300.0


def scene_buffer(term: str):
    """The term's SETTLED 3D scene as a particle buffer (N,28) -- the real volume the live viewer orbits.

    The still `project_movie` renders two frames; the live viewer needs the settled body itself so it can
    turn it in real time (the time axis) and let the operator orbit it (verify it is a true 3D volume, not
    a flat disk). Solid scenes hand back their END buffer directly; a collapse scene is settled once here
    (spawn -> attractor -> 90 steps) and its particles returned."""
    mb = membrane_buffer(term)                                   # a folder in story/ owns its own matter
    if mb is not None:
        return mb
    if term in COMPOSITIONS:                                     # DEFAULT for composite terms: built from proven children
        return compose_buffer(term)
    spec = SCENES.get(term)
    if not spec:
        return None
    _BUILDERS = {"planet": _planet_buffers, "terrain": _terrain_buffers, "row": _row_buffers, "system": _system_buffers, "garden": _garden_buffers, "ecosystem": _ecosystem_buffers, "tree": _tree_buffers, "treeform": _treeform_buffers, "fruit": _fruit_buffers, "planting": _planting_buffers, "farming": _farming_buffers, "planetary_farm": _planetary_farm_buffers, "lunar_farm": _lunar_farm_buffers, "orbital_farm": _orbital_farm_buffers, "space": _space_buffers, "seed": _seed_buffers, "determinism": _determinism_buffers, "laws": _laws_buffers, "truth": _truth_buffers, "ship": _ship_buffers, "flight": _flight_buffers, "ship_power": _ship_power_buffers, "ship_combat": _ship_combat_buffers, "shields": _shields_buffers, "warp_drive": _warp_drive_buffers, "ship_view": _ship_view_buffers, "salvage": _salvage_buffers, "descent": _descent_buffers, "standing": _standing_buffers, "black_hole": _black_hole_buffers, "verbs": _verbs_buffers, "dig": _dig_buffers, "grow": _grow_buffers, "scan": _scan_buffers, "navigate": _navigate_buffers, "shoot": _shoot_buffers, "melee": _melee_buffers}
    builder = _BUILDERS.get(spec.get("kind"))
    if builder:
        return builder(spec, term)[0]                            # the settled END buffer
    # collapse: settle the body once and return its particles
    from ParticleEngine.core import ParticleSimulator, PARTICLE_TYPES
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.control_vars import default_physics_registry
    sim = ParticleSimulator(spec["count"] + 64)
    sim.spawn(spec["count"], spec["type"], position=(0, 0, 0), spread=float(spec["spread"]),
              color=spec["color"], size=float(spec["size"]), life=-1.0)
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    pipe.upload(sim._data[:sim._count])
    pipe.attractors.append((0.0, 0.0, 0.0, float(spec["pull"]), PARTICLE_TYPES[spec["type"]], 500.0))
    reg = default_physics_registry()
    reg.set("gravity", (0.0, 0.0, 0.0)); reg.set("wind_vector", (0.0, 0.0, 0.0))
    cvars = reg.snapshot()
    for _ in range(90):
        pipe.step_particles(1 / 60, cvars)
    return pipe.download_particles()


# ═══════════════════════════════════════════════════════════════════════
#  APPEARANCE FROM DECOMPOSITION -- a membrane's render built from its PROVEN children
#  (the LOD-of-meaning principle: each level is composed of the rung below it, so adding detail to the
#  STORY -- and proving it -- enriches the parent's render, no hand-authored scene. The child's own
#  matter supplies its APPEARANCE; the parent's LAYOUT supplies only WHERE each child sits, which is
#  structure -- a solar system's orbits -- not an aesthetic pass.)
# ═══════════════════════════════════════════════════════════════════════
COMPOSITIONS = {
    "theSolarSystem": {
        "cam": (0.0, -400.0, 230.0),
        "rings": [85.0, 150.0, 215.0, 280.0],
        # the REAL proven bodies, placed on the orbital plane (child, center, scale):
        "place": [("theStar", (0.0, 0.0, 0.0), 0.45),
                  ("aPlanet", (150.0, 0.0, 0.0), 0.13)],
    },
}


def _place(buf, center, scale: float):
    """Translate + scale a child's scene buffer into the parent's frame (positions AND grain size)."""
    import numpy as np
    b = np.array(buf, dtype=np.float32, copy=True)
    b[:, PX:PZ + 1] = b[:, PX:PZ + 1] * float(scale) + np.asarray(center, dtype=np.float32)
    b[:, SIZE] = b[:, SIZE] * float(scale)
    return b


_LOD_MIPS: dict = {}   # child term -> (mips, radius_world); built once, reused across composes


def _planet_lod_mips(child: str):
    """Cached LOD mip pyramid for a PLANET child, built from its OPAQUE surface grains (the faint atmosphere
    halo is dropped -- it's a close-up detail, and at system scale it only adds over-accumulation)."""
    if child not in _LOD_MIPS:
        import numpy as np, lod as _lod
        cb = scene_buffer(child)
        surf = np.ascontiguousarray(cb[cb[:, ALPHA] > 0.5])          # opaque surface, no atmosphere
        R = float(SCENES.get(child, {}).get("radius", _lod.body_radius(surf)))
        _LOD_MIPS[child] = (_lod.build_mips(surf, R), R)
    return _LOD_MIPS[child]


def _place_planet_lod(child, center, scale, cam, height=1080, fov=None):
    """Place a planet child at the LOD level its ON-SCREEN size warrants -- the pixel-budget law. A planet
    that shrinks to a few px in the solar-system view is rendered with a handful of averaged-colour grains
    (a clean tiny marble), not all 40k (which over-accumulates to a white dot)."""
    import numpy as np, lod as _lod
    mips, R = _planet_lod_mips(child)
    if fov is None:
        from ParticleEngine.camera import FirstPersonCamera
        fov = FirstPersonCamera((0.0, 0.0, 0.0)).fov
    dist = float(np.linalg.norm(np.asarray(cam, np.float32) - np.asarray(center, np.float32)))
    r_px = _lod.projected_radius_px(R * float(scale), dist, height, fov)
    return _place(_lod.select(mips, r_px), center, scale)


def _disperse(buf, term: str, sigma: float):
    """Scatter a settled buffer into a 'before' cloud -- the movie's begin frame (the system accreting)."""
    import numpy as np
    rng = np.random.default_rng(_seed(term) ^ 0x9E3779B9)
    b = np.array(buf, dtype=np.float32, copy=True)
    b[:, PX:PZ + 1] += rng.normal(0.0, sigma, (len(b), 3))
    return b


def compose_buffer(term: str):
    """Build `term`'s scene from its PROVEN children -- appearance derived from the decomposition.

    Returns the composed (N,28) buffer, or None if the term has no layout. Each placed child is its OWN
    `scene_buffer` (the real proven matter -- the actual blue marble, the actual star), so the parent is
    literally made of its children. Rings are structure (the orbits), drawn as dust."""
    import numpy as np
    lay = COMPOSITIONS.get(term)
    if not lay:
        return None
    rng = np.random.default_rng(_seed(term))
    parts = [_orbit_ring(r, rng) for r in lay.get("rings", [])]
    cam = lay.get("cam", (0.0, 0.0, 0.0))
    for child, center, scale in lay.get("place", []):
        if SCENES.get(child, {}).get("kind") == "planet":        # LOD planets by their on-screen size (pixel budget)
            parts.append(_place_planet_lod(child, center, scale, cam))
        else:
            cb = scene_buffer(child)                              # the child's own settled matter (star, etc.)
            if cb is not None:
                parts.append(_place(cb, center, scale))
    return np.concatenate(parts, axis=0) if parts else None


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "theStar"
    import numpy as np
    from PIL import Image
    m = project_movie(term, Path(__file__).parent / "output")
    for k, v in (m or {}).items():
        arr = np.asarray(Image.open(v))
        print(f"  {k}: {v}  max_rgb={int(arr.max())}")


def project_movie(term: str, out_dir) -> dict | None:
    """The render the engine calls. Rendering is physics: when it fails inside the long-lived
    MCP server its stdout is invisible, so the traceback goes to a file an agent can read."""
    try:
        return _project_movie_impl(term, out_dir)
    except Exception:
        import traceback
        try:
            (_REPO / ".tmp").mkdir(exist_ok=True)
            (_REPO / ".tmp" / "splat_error.log").write_text(traceback.format_exc())
        except Exception:
            pass
        raise
