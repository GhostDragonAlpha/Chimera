"""matter.py -- the buffer a membrane's law emits its matter into.

The Chimera Engine renders Gaussian splats: an (N, 28) array where each row is one grain of matter.
This is the only thing a folder needs to know about the renderer, so it lives once, here, and every
membrane's `physics.py` emits into it.

EVERY MEMBRANE WORKS IN ITS OWN LOCAL UNITS. A horizon is 2.3e-35 m and a planet is 6.4e6 m; if
both were emitted in metres one of them would be lost to float precision. But a boundary supplies a
local unit -- a coordinate cannot exceed its own membrane's extent -- so each law emits at radius ~1
in its own frame, and the parent scales its children when it composes them. Precision stops being
a problem the moment the membrane is the unit.
"""
from __future__ import annotations

import numpy as np

NCOLS = 28
PX, PY, PZ = 0, 1, 2
# GRAIN MASS -- the sim pipeline's own MASS column (col 9), adopted for matter. A grain is a
# Gaussian density packet: mass here + SIZE below fully determine its peak density (grain_density),
# and density is what the optics below READ. Optional: zero means "this emit carries no mass".
MASS = 9
TYPE = 11
# THE SPECULAR COLUMNS -- what a grain needs for light to REFLECT off it, both derived, never picked:
#   SPEC_F0     Fresnel reflectance at normal incidence = fresnel_f0(refractive_index(rho)) --
#               the membrane's own published density, pushed through Lorentz-Lorenz. Water lands on
#               the 2% every photographer knows without anyone typing it.
#   SPEC_SLOPE  RMS sub-grain slope (tan units) -- the membrane's own published surface statistic
#               (aSaltOcean: Cox-Munk surface_slope_mean; aTerrain: tan(mean_slope_deg)).
# THESE OVERLAY THE SIM PATH'S PROP0/PROP1 (some particle types read PROP0 as an opacity source).
# No collision is possible: the renderer reads them as specular inputs ONLY when a light has been
# explicitly set on the pipeline (set_light), which no sim demo does -- and zero in either column
# means "not published", which disables the term for that grain rather than inventing a default.
SPEC_F0, SPEC_SLOPE = 12, 13
# REFRACT (overlays the sim path's PROP2, which no current particle type reads): > 0 marks this
# grain as a refractive INTERFACE -- the renderer bends the view ray by Snell at the grain's own
# n (from its density) and shows the membrane-published floor through it, attenuated by the
# membrane's own absorption. Zero means opaque, exactly as before the pass existed.
REFRACT = 14
CR, CG, CB, ALPHA, SIZE = 16, 17, 18, 19, 20
NX, NY, NZ = 21, 22, 23        # optional outward normal -> the pipeline back-face-culls the far side
# THE ALBEDO A GRAIN IS MADE OF, as opposed to the colour it currently shows. A membrane that will be
# RELIT somewhere else (a body carried onto terrain, under that terrain's own sun) has to hand over
# what it is made of, not what it looked like in its own scene -- otherwise the relighting flattens
# every material into one. Optional: zero here means "no separate albedo, reuse the colour".
AR, AG, AB = 24, 25, 26
# WHAT KIND OF MATTER the grain is, as a class id (0/1/2/...): optional, for a relight that shades
# per material class (a visor is not shaded like a suit). The GPU pipeline never reads col 27 --
# it is a story-side convention, like the albedo columns.
MAT = 27

SOLID = 3.0                     # opaque, isotropic grain -- matter you can see the surface of
GLOW = 5.0                      # big soft blob -- light, plasma, a field

# THE SIZE YOU WRITE IS THE SIZE THAT RENDERS. That was not true until 2026-07-29.
#
# GLOW used to carry a hidden 6x multiplier in `gpu_pipeline._profile()`, so
# `paint(b, colour, alpha, 0.055, GLOW)` drew a 0.33 splat and no author could tell. It put seven
# membranes over the rasteriser's per-tile cap, silently invalidated both helpers below (they return
# the size you should ASK for, which was not the size that LANDED), and gave theStar a six-fold pop
# in grain size at t=0.8 where its type switched.
#
# It is gone. Every GLOW call in the tree was multiplied by 6 in the same commit, so the pictures did
# not move -- only the honesty did. **A membrane states its own grain size and is believed.**


def blank(n: int) -> np.ndarray:
    """n grains of nothing, ready to be given a place, a colour and a size."""
    return np.zeros((n, NCOLS), dtype=np.float32)


def grains_for(radius: float, extent: float, full: int = 900, floor: int = 16,
               screen_px: int = 1080, per_px: float = 0.5) -> int:
    """HOW MANY GRAINS A BODY DESERVES AT THIS FRAMING. The pixel-budget law, and it is a
    CORRECTNESS rule, not an optimisation.

    A thing that occupies one pixel does not need a thousand grains to say so -- and if you give it
    a thousand anyway they all land in the same 32-px tile, overrun the rasteriser's MAX_PER_TILE,
    and the cap evicts everything ELSE in that tile. The result is a BLACK, TILE-SHAPED HOLE next to
    the object: not a dim patch, a hard-edged rectangle on the tile grid, which is the tell.

    MEASURED, and this is what the law is written from: thePlanets drew each of eleven worlds with
    900 grains. At a framing 11.2 units across, the inner worlds are 0.0096 units in radius -- a
    QUARTER OF A PIXEL. Five of them within 36 px of screen centre put 4,801 splats into one tile
    that allows 4,096, and tile 989 (x 928-959, y 512-543) rendered as background.

    The same law is what the star above already obeys. It was written down there and not applied
    here, which is how a rule that is only prose gets broken twice.

    Grains scale with PROJECTED AREA -- a body twice as wide on screen deserves four times as many.
    The floor keeps a sub-pixel body visible as a dot; the cap stops a close one from exploding.

    `extent` is the membrane's own drawn extent (its 99th-percentile radius), and the 2.8 is the
    camera-distance rule the viewer uses, so this needs nothing the emit does not already know."""
    px_r = abs(float(radius)) / max(abs(float(extent)), 1e-12) * (screen_px / 2.0) / 2.8
    n = int(per_px * np.pi * px_r * px_r)
    return int(min(max(n, floor), full))


def surface_grain(n: int, radius: float = 1.0, cover: float = 0.58) -> float:
    """HOW BIG A GRAIN HAS TO BE TO CLOSE A SURFACE. Not a taste setting -- arithmetic.

    n grains spread over a sphere of radius r sit `sqrt(4*pi*r^2/n)` apart. A splat narrower than
    about half that spacing leaves gaps, and because there is nothing behind a planet, the gaps are
    BLACK: the ocean reads as loose grit floating in space instead of as water. Wider than the
    spacing and the surface goes soft and every feature blurs.

    So the grain is a CONSEQUENCE of how many you asked for, and computing it here means changing
    the count can never silently reopen the holes. The same rule inverted is the reason a shell must
    be sampled finely enough to be thinner than its own grains are wide -- an atmosphere drawn with
    coarse splats renders as a halo the planet does not have."""
    spacing = (4.0 * np.pi * radius * radius / max(n, 1)) ** 0.5
    return float(cover * spacing)


def fibonacci_sphere(n: int, jitter: float = 0.0, seed: int = 0) -> np.ndarray:
    """n unit vectors spread evenly over a sphere (the golden-angle spiral). Deterministic.

    JITTER BREAKS THE LATTICE. The golden-angle spiral is REGULAR, and a regular sampling pattern is
    visible -- zoom in and its arms read as faint curved streaks, which is what makes a smooth
    surface look like a crappy voxel calculation. This displaces each grain TANGENTIALLY (in the
    surface, then renormalised back onto the shell) by a fraction of the mean spacing, turning the
    spiral into blue noise. Tangential ON PURPOSE: radial jitter scatters grains in DEPTH and lets
    the background speckle through between them, which is a worse artifact."""
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    th = np.pi * (1.0 + 5.0 ** 0.5) * i
    d = np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)
    if jitter > 0.0:
        rng = np.random.default_rng(seed)
        spacing = 2.0 / np.sqrt(max(n, 1))
        v = rng.normal(0.0, 1.0, (n, 3))
        v -= (v * d).sum(1, keepdims=True) * d                   # into the TANGENT plane
        v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
        d = d + v * (jitter * spacing * rng.random((n, 1)) ** 0.5)
        d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)  # back onto the shell: no depth change
    return d


def paint(buf: np.ndarray, rgb, alpha: float, size: float, kind: float = SOLID) -> np.ndarray:
    buf[:, CR], buf[:, CG], buf[:, CB] = rgb
    buf[:, ALPHA] = alpha
    buf[:, SIZE] = size
    buf[:, TYPE] = kind
    return buf


def lit(albedo, irradiance, e_ref: float = 1.0, tone: float = 0.25):
    """A SPLAT IS A MEASUREMENT OF LIGHT, not a coloured object.

    What leaves a grain is `albedo * E / pi` -- the matter says what FRACTION it returns, the light
    says HOW MUCH arrives. So the same rock is brilliant near a star and near-black far from one,
    and neither is a different material.

        albedo     (3,) or (N,3)   the matter's response  -- this is the material DNA
        irradiance  scalar or (N,) W/m^2 arriving         -- this is the light
        e_ref                      irradiance treated as "correctly exposed"

    TONE, DECLARED: real irradiance spans thousands to one across a disk while a display spans about
    a hundred to one, so a curve is unavoidable -- exactly what a camera does. `tone` is that curve
    (0.25 = fourth root), and it is the ONE human parameter here. Everything else is measured."""
    import numpy as np
    a = np.asarray(albedo, dtype=np.float32)
    e = np.asarray(irradiance, dtype=np.float32)
    scale = np.clip(e / max(e_ref, 1e-30), 0.0, None) ** tone
    if a.ndim == 1:
        a = a[None, :]
    return np.clip(a * scale.reshape(-1, 1), 0.0, 1.0)


def blackbody_rgb(T: float) -> tuple:
    """A crude but honest colour for a temperature: the colour is a MEASUREMENT of the physics,
    never a choice. Cool -> red, ~5800 K -> white, very hot -> blue-white."""
    t = float(np.clip(T, 1000.0, 40000.0))
    if t < 5800.0:
        f = (t - 1000.0) / 4800.0
        return (1.0, 0.35 + 0.6 * f, 0.1 + 0.85 * f)
    f = min(1.0, (t - 5800.0) / 20000.0)
    return (1.0 - 0.35 * f, 1.0 - 0.15 * f, 1.0)


# ══ THE ONE SUN ═══════════════════════════════════════════════════════════════════════════════
# THE ONE SUN (2026-08-05; theory: docs/THE_TWO_FORCES.md, Stage 21). Every membrane used to type
# its own copy of where the light comes from -- 0.22 in one file, 0.12 in another, 0.30 in a third,
# some of them not even turning the same way -- so this world had as many suns as it had files.
# There is ONE star, and it is a reader like every other in this world: its place falls out of the
# world's own numbers, and a daylit emit reads it from here or it has no sun at all. A sun that is
# typed in two files is two suns; this is the only place one is ever made.
#
# The sun is two derived quantities and nothing else:
#   THE PHASE -- where the world has got to in its orbit, the shared clock `2*pi*t - 1.15`. The
#     1.15 offset is DECLARED and MEASURED, not guessed (aBlueWorld): the viewer's default eye sits
#     on -Y, and at ~1.15 rad the sun is ~65 deg off the eye, which puts the terminator across the
#     visible disk so a sphere reads as a sphere instead of a flat lit face.
#   THE DECLINATION -- the tilt projected onto the orbit, the whole of a season:
#     sin(decl) = sin(obliquity) * cos(phase). Zero at the equinoxes, the whole tilt at the
#     solstices, and past the poles it is polar day and polar night. It is the same projection the
#     human's chain derives for its own epoch (theHuman); this is its home now, so the space scenes,
#     the surface scenes and the ground can never disagree about where the sun is again.
SUN_PHASE_OFFSET_RAD = 1.15

# FILM FRAMING, and it is shared so no surface scene can drift from the others: the hour of the
# day-movie the surface scenes open on (t = 1.0). WHICH hour is a LENS choice, never a fact about
# the sun -- the sun's ELEVATION at that hour is the law's. It used to be typed in aTerrain AND
# theGround (two files, one number, the drift that was already inevitable); it is typed here once.
# aTerrain, theGround and the human chain standing on the ground all read the same opening hour, so
# zooming from terrain to ground to body never jumps the light.
SUN_OPEN_HOUR = 0.9


def sun_declination(tt, obliquity_deg):
    """The sun's height above the equator, RADIANS -- the ONE season number of the whole world.
    Every daylit scene shares it; nothing in this tree types a declination."""
    phase = 2.0 * np.pi * float(tt) - SUN_PHASE_OFFSET_RAD
    return float(np.arcsin(np.sin(np.radians(float(obliquity_deg))) * np.cos(phase)))


def sun_direction(tt, obliquity_deg):
    """The one sun as a direction in the planet's equatorial frame (unit vector) -- for scenes that
    look at the whole planet or a whole sky. An emit dots its surface normals against it."""
    phase = 2.0 * np.pi * float(tt) - SUN_PHASE_OFFSET_RAD
    decl = sun_declination(tt, obliquity_deg)
    v = np.array([np.sin(phase) * np.cos(decl),
                  -np.cos(phase) * np.cos(decl),
                  np.sin(decl)], dtype=np.float64)
    return v / np.linalg.norm(v)


def local_sun(tt, obliquity_deg, latitude_deg, hour_offset=0.0):
    """The one sun in a SURFACE scene's own frame (up = +z), unit vector. The azimuth sweeps with
    the scene's film; the elevation is the local-sky altitude -- the same declination projected
    onto the scene's latitude,
        sin(alt) = sin(decl)*sin(lat) + cos(decl)*cos(lat)*cos(hour)
    so noon is overhead only where the declination reaches the latitude (a tilted world's sun passes
    straight overhead on the way to the solstice, and has already started back down by it).
    `hour_offset` is FILM FRAMING -- the hour of the day-movie it opens on -- a LENS choice, never a
    fact about the sun."""
    decl = sun_declination(tt, obliquity_deg)
    hour = 2.0 * np.pi * float(tt) + float(hour_offset)
    lat = np.radians(float(latitude_deg))
    sin_alt = np.sin(decl) * np.sin(lat) + np.cos(decl) * np.cos(lat) * np.cos(hour)
    alt = np.arcsin(np.clip(sin_alt, -1.0, 1.0))
    v = np.array([np.cos(hour) * np.cos(alt),
                  np.sin(hour) * np.cos(alt),
                  np.sin(alt)], dtype=np.float64)
    return v / np.linalg.norm(v)


def sun_altitude_deg(tt, obliquity_deg, latitude_deg, hour_offset=0.0):
    """The ONE sun's elevation above the local horizon, DEGREES -- the number a day-lit membrane
    publishes so a reader can check the light it baked against the claim it wrote."""
    v = local_sun(tt, obliquity_deg, latitude_deg, hour_offset)
    return float(np.degrees(np.arcsin(float(v[2]))))


# ══ THE OPTICS OF MATTER: density → refractive index → reflection ═══════════════════════════════
# THE TWO-FORCE READER (2026-08-05; theory: docs/THE_TWO_FORCES.md). Light is not a new physics
# system in this world -- it is a third READER of the density field that gravity and mechanics
# already read. The bridge is Lorentz-Lorenz, which is electromagnetism and nothing else: a bound
# electron cloud polarises in the light's field, and summing that response over the number of
# molecules per volume -- the DENSITY -- gives the refractive index,
#
#     (n^2 - 1) / (n^2 + 2) = r * rho
#
# where r is the material's SPECIFIC REFRACTION (cm^3/g), a measured molecular constant that enters
# the way nuclear binding enters theStar: sourced, cited, never fitted. Everything downstream is a
# consequence: Fresnel reflectance from n, the sunglint from Fresnel. THE CHECK THAT THIS IS A
# DERIVATION AND NOT A STORY: seawater at aSaltOcean's own published 1026.95 kg/m^3 comes out
# n = 1.3437 against the 1.34 its physics sourced independently -- 0.3% from density alone, and
# aSaltOcean's published sunglint_intensity (0.0211) is fresnel_f0 of that n. Move the density and
# the glint moves; that is the slider test.

# Specific refraction r (cm^3/g), each a MEASURED constant restated through the law above:
#   water    : molar refraction R_M = 3.712 cm^3/mol (CRC) over M = 18.015 g/mol.
#   silicate : quartz's measured n = 1.548 at rho = 2.65 g/cm^3, inverted through Lorentz-Lorenz --
#              the same number mineralogy tables carry as its specific refraction (~0.120).
# A porous or salty material needs NO extra rule: refractivity is additive in mass, so bulk density
# already carries porosity (theGround's 1537 kg/m^3 regolith reflects LESS than solid rock, and
# that is the physics, not a style choice).
SPECIFIC_REFRACTION_CM3_G = {
    "water": 3.712 / 18.015,          # = 0.20605
    "silicate": 0.1198,
}

# DISPERSION -- n depends on wavelength, and the dependence is MEASURED, never picked. Literature
# water indices at the Fraunhofer lines (Hale & Querry / CRC): C 656.3 nm, D 589.3 nm, F 486.1 nm.
# Restated per colour channel through the same Lorentz-Lorenz form as everything else, so the
# density slider still moves all three together:
#     r_channel = r_D * [(n_c^2-1)/(n_c^2+2)] / [(n_D^2-1)/(n_D^2+2)]
WATER_N_BY_CHANNEL = {"R": 1.3311, "G": 1.3334, "B": 1.3371}


def dispersive_refraction(r_d_cm3_g: float, n_d: float, n_channel: float) -> float:
    """The channel's specific refraction implied by its measured index -- the sourced dispersion
    constant restated through the law (same move as the silicate entry above)."""
    ll = lambda n: (n * n - 1.0) / (n * n + 2.0)
    return float(r_d_cm3_g) * ll(float(n_channel)) / ll(float(n_d))


# BULK MODULUS -- what the OVERLAP-PRESSURE reader consumes (docs/THE_TWO_FORCES.md Stage 8):
# compressing matter costs energy at a rate the material itself publishes. Measured constants,
# cited (CRC): water 2.2 GPa; quartz ~37 GPa. These enter the way specific refraction does --
# the ONLY legal way a material constant enters this world.
BULK_MODULUS_PA = {
    "water": 2.2e9,
    "silicate": 3.7e10,
}

# SHEAR MODULUS -- the SECOND independent elastic constant, and an isotropic solid needs exactly
# two. Bulk modulus alone cannot give you a contact theory: Hertz needs Young's modulus and
# Poisson's ratio, and those follow from (B, G) and from nothing less. Measured, cited (CRC /
# Voigt-Reuss-Hill for alpha-quartz), entering the way every material constant does here.
#
# WATER IS DELIBERATELY ABSENT AND THAT IS THE POINT. A fluid has no shear modulus, so Hertzian
# contact -- an elastic-SOLID theory -- does not apply to it at all. `ChimeraEngine/core/hertz.py`
# refuses rather than substituting a number, because a missing constant is a scope boundary and a
# fallback would be an assumption wearing a hat.
SHEAR_MODULUS_PA = {
    "silicate": 4.4e10,
}


# THERMAL CONSTANTS -- what BULK viscoelastic loss is made of. Thermoelastic (Zener) damping is a
# real bulk mechanism and it is DERIVABLE: compressing matter warms it, the warm region conducts
# heat away, and the heat does not come back on the return stroke. That needs only a material's
# thermal expansion, heat capacity and conductivity -- measured constants, cited here the way B and
# G are (alpha-quartz, CRC ranges; conductivity is strongly anisotropic in quartz and this is a
# polycrystalline average). No membrane in this world publishes any of them, so unlike temperature
# they cannot be read.
#
# THE CONCLUSIONS DRAWN FROM THESE ARE TESTED FOR ROBUSTNESS rather than trusted:
# ChimeraEngine/test_viscoelastic.py varies each by 3x and checks the finding survives.
THERMAL_EXPANSION_PER_K = {"silicate": 1.2e-5}
SPECIFIC_HEAT_J_KG_K = {"silicate": 730.0}
THERMAL_CONDUCTIVITY_W_M_K = {"silicate": 6.5}


# COMPLEX REFRACTIVE INDICES -- what a METAL is, optically: n + ik per colour channel, measured
# (Johnson & Christy 1972 for copper; Rakic 1995 for aluminium), at the same R/G/B wavelengths the
# water dispersion table uses. A metal's COLOUR falls out of these -- copper reflects red far
# better than blue -- with nothing tuned; see ChimeraEngine/core/complex_fresnel.py.
COMPLEX_INDEX_RGB = {
    "aluminum": ((1.39, 7.65), (0.96, 6.69), (0.71, 5.72)),
    "copper": ((0.21, 3.67), (0.76, 2.46), (1.15, 2.50)),
}


def thermal_diffusivity(k_therm: float, rho: float, c_p: float) -> float:
    """D = k / (rho c_p) -- how fast a temperature difference spreads. It is what decides whether
    a load cycle is isothermal, adiabatic, or in the lossy middle between them."""
    return float(k_therm) / (float(rho) * float(c_p))


def youngs_modulus(B: float, G: float) -> float:
    """E = 9BG/(3B+G) -- derived, once the two independent constants are in hand."""
    return 9.0 * float(B) * float(G) / (3.0 * float(B) + float(G))


def poisson_ratio(B: float, G: float) -> float:
    """nu = (3B-2G)/(2(3B+G)). Quartz lands near 0.08 -- unusually low, and correct."""
    return (3.0 * float(B) - 2.0 * float(G)) / (2.0 * (3.0 * float(B) + float(G)))


def refractive_index(rho_kg_m3: float, r_cm3_g: float) -> float:
    """Lorentz-Lorenz: density in, refractive index out. Refuses an unphysical input rather than
    clamping it -- r*rho >= 1 has no real n, and a clamp here would be a fallback wearing a hat."""
    x = float(r_cm3_g) * (float(rho_kg_m3) / 1000.0)      # rho to g/cm^3, same unit system as r
    if not (0.0 <= x < 1.0):
        raise ValueError(f"refractive_index: r*rho = {x:.4f} is outside [0, 1) -- "
                         f"check the density ({rho_kg_m3} kg/m^3) or the specific refraction ({r_cm3_g})")
    return float(np.sqrt((1.0 + 2.0 * x) / (1.0 - x)))


def fresnel_f0(n: float) -> float:
    """Reflectance at normal incidence for a dielectric meeting vacuum/air: ((n-1)/(n+1))^2.
    Water's n = 1.34 lands on 0.0211 -- the 2% glint -- with nothing typed but the density."""
    n = float(n)
    return ((n - 1.0) / (n + 1.0)) ** 2


def grain_mass(rho_kg_m3: float, size: float) -> float:
    """The MASS column value that gives a Gaussian grain of this SIZE the stated peak density.
    A grain is a density packet rho(x) = rho0 * exp(-|x|^2 / (2 s^2)); integrating it gives
    M = rho0 * (2 pi)^(3/2) * s^3. The disc reshaping in the renderer is a screen-coverage device,
    not a matter property, so the matter's own shape here is the isotropic ball the emit asked for."""
    s = abs(float(size))
    return float(rho_kg_m3) * (2.0 * np.pi) ** 1.5 * s ** 3


def grain_density(mass: float, size: float) -> float:
    """The inverse of grain_mass: peak density of the packet, kg/m^3 in the membrane's own frame.
    This is THE one place density is computed from the buffer; any reader that wants a grain's
    density comes here (the one-source-of-truth test in ChimeraEngine/test_optics.py enforces it)."""
    s = abs(float(size))
    if s <= 0.0:
        raise ValueError("grain_density: a grain with zero SIZE has no volume to hold mass")
    return float(mass) / ((2.0 * np.pi) ** 1.5 * s ** 3)


def paint_specular(buf: np.ndarray, f0, slope) -> np.ndarray:
    """Write the specular columns. f0/slope are scalars or (N,) arrays -- typically ONE value per
    membrane, because they come from the membrane's own published numbers, not per-grain taste."""
    buf[:, SPEC_F0] = f0
    buf[:, SPEC_SLOPE] = slope
    return buf


# ══ THE MEASURED MATERIAL ELEMENTS ═══════════════════════════════════════════════════════════════
# THE OPERATOR'S RULE (2026-07-31, verbatim): the game is made from 3DGS objects -- "extract the
# shape and texture data", "extract certain elements and then train them all together". The elements
# are the genomes of `story/data/material_genomes.json`: ONE joint k-means codebook over 16 real
# captured scans (Construction/material_elements.py), so genome #k means the same material wherever
# it is read. A membrane NEVER types a material colour when a genome covers it; where no scan exists
# (ice, open water -- none in the collection) the constant stays and is FLAGGED, never quietly kept.
#
# These are APPEARANCE genomes: capture lighting is baked into R,G,B (that is what an albedo channel
# consumes here -- lit() re-lights them), and no roughness/metalness is recoverable from splat colour.

_GENOME_LIB = None


def material_genomes() -> dict:
    """The joint element codebook, loaded once. Walks up for story/data/material_genomes.json the
    way theHuman's side walks up for ANSUR -- measured data, one file, every membrane reads it."""
    global _GENOME_LIB
    if _GENOME_LIB is None:
        import json
        from pathlib import Path
        p = Path(__file__).resolve()
        for q in p.parents:
            f = q / "story" / "data" / "material_genomes.json"
            if f.exists():
                _GENOME_LIB = json.loads(f.read_text())
                break
        else:
            raise FileNotFoundError("material_genomes.json -- run Construction/material_elements.py")
    return _GENOME_LIB


def genome_share(g: dict, scans) -> float:
    """How much of a genome is carried by the named scans (its dominant_source fractions, summed)."""
    return float(sum(g.get("dominant_source", {}).get(s, 0.0) for s in scans))


def genome_rgb(g: dict) -> tuple:
    f = g["features"]
    return (f["R"]["mean"], f["G"]["mean"], f["B"]["mean"])


def genome_lum(g: dict) -> float:
    return sum(genome_rgb(g)) / 3.0


def sample_genome_rgb(g: dict, rng, n: int) -> np.ndarray:
    """n albedos DRAWN FROM THE MEASURED DISTRIBUTION (per-channel normal on the genome's own
    mean/std, clipped to its measured p10..p90) -- never the centroid repeated: a real material
    is a population, and the mottle IS the measurement."""
    f = g["features"]
    out = np.empty((n, 3), dtype=np.float32)
    for i, c in enumerate("RGB"):
        m, s = f[c]["mean"], f[c]["std"]
        out[:, i] = np.clip(rng.normal(m, max(s, 1e-4), n), f[c]["p10"], f[c]["p90"])
    return out


def pick_genomes(scans, min_share: float = 0.20, min_opacity: float = 0.85) -> list:
    """The genomes a set of scans CARRIES, for a membrane to map onto its roles. Mechanical,
    declared, and the operator ratifies the mapping -- taste terminates with him, never here."""
    lib = material_genomes()
    return [g for g in lib["genomes"]
            if genome_share(g, scans) >= min_share
            and g["features"]["opacity"]["mean"] >= min_opacity]
