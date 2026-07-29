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


def project_movie(term: str, out_dir) -> dict | None:
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
        # nothing here is hand-framed; the view is as far back as the matter is wide.
        end_buf = membrane_buffer(term, 1.0)
        extent = float(np.linalg.norm(end_buf[:, PX:PZ + 1], axis=1).max()) or 1.0
        cam_pos = (0.0, -2.7 * extent, 0.72 * extent)
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

    _BUILDERS = {"planet": _planet_buffers, "terrain": _terrain_buffers, "row": _row_buffers, "system": _system_buffers}
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


def _membrane_own(folder, t):
    """Just this membrane's own matter, without its children."""
    import json
    law = _membrane_law(folder)
    if not hasattr(law, "emit"):
        return None, None
    nj = folder / "numbers.json"
    nums = json.loads(nj.read_text()) if nj.exists() else law.derive(None, {})
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
    parts = [own]
    for child, (centre, scale) in (law.layout(nums) or {}).items():
        cb = membrane_buffer(child, t, _depth + 1)
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
    return np.concatenate(parts, axis=0) if len(parts) > 1 else own


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
    cam = (COMPOSITIONS.get(term) or SCENES.get(term) or {}).get("cam")
    if cam:
        return float(np.linalg.norm(cam))
    buf = membrane_buffer(term)                 # a membrane is orbited at ITS OWN extent
    if buf is not None:
        return 2.8 * (float(np.linalg.norm(buf[:, PX:PZ + 1], axis=1).max()) or 1.0)
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
    _BUILDERS = {"planet": _planet_buffers, "terrain": _terrain_buffers, "row": _row_buffers, "system": _system_buffers}
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
