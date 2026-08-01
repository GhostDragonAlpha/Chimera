"""theAtmosphere -- THE LAW of air: what an atmosphere IS, and what any atmosphere must satisfy.

An atmosphere is gas that gravity keeps. That is the whole definition, and everything in this
membrane is a consequence of it:

    KEEPING: a gas stays if its molecules cannot reach escape speed thermally -- the Jeans
    parameter (escape energy / thermal energy) must be large; below ~6 the gas is gone in
    geological time. So a world's air is SELECTED: light gases leave, heavy ones stay.
    (This world's ledger: H2 at 3.0 and He at 4.2 are GONE; CH4 at 8.4 and everything
    heavier -- N2, O2, CO2, H2O -- is kept.)

    WEIGHING: kept gas has weight, so pressure IS the column's weight and density falls as
    e^{-z/H} with H = kT/mu g -- which is why an atmosphere HAS NO EDGE, it fades.

    COLOURING: the column scatters short light most (Rayleigh, lambda^-4), so any atmosphere
    over a star has a coloured sky and a reddened sunrise. The colour is forced by the
    column mass and the star's spectrum, never chosen.

    WEATHERING: air that is lifted cools at g/c_p; water falls out at the dewpoint, so
    clouds are not decoration -- they are the atmosphere's own condensation, and they stop
    at the tropopause where the cooling stops.

The INSTANCE of this law here is `aNitrogenAtmosphere` -- named by the class its own mean
molecule puts it in (29.0 g/mol -> N2). The classification of an atmosphere is its dominant
gas, computed from the scale height, never assigned.
"""
import math

from math import pi, sqrt, log

K_B = 1.380649e-23
M_U = 1.66053907e-27

JEANS_KEEP = 6.0           # escape-ratio threshold: below ~6 a gas is lost over geological time
                           # (the measured rule of thumb; Venus/Earth/Mars ledgers bracket it)


def derive(parent, free):
    """The law, stated against this world: does air exist here at all, and which gases make the cut?
    Everything the instance needs is handed down through this membrane -- the instance reads ONE
    parent, and this is it."""
    g = float(parent["g"]); R = float(parent["R"])
    escapes = parent.get("escape_ratios", {})
    kept = parent.get("gases_kept", [])

    # THE RETENTION LEDGER, checked: every kept gas must clear the Jeans bar, and the light ones
    # that did not make the list must fall under it. If a world's ledger violates this, the LAW
    # is wrong, not the ledger.
    kept_ratios = {gname: float(v) for gname, v in escapes.items() if gname in kept}
    lost_ratios = {gname: float(v) for gname, v in escapes.items() if gname not in kept}
    holds = (all(v > JEANS_KEEP for v in kept_ratios.values())
             and all(v < JEANS_KEEP for v in lost_ratios.values()))

    return {
        "extent_m": R,
        "duration_s": float(parent.get("day_s", 86400.0)),
        "g": g, "R": R,
        # the raw state of this world's air, handed to the instance
        "P_surface_bar": float(parent["P_surface_bar"]),
        "scale_height_m": float(parent["scale_height_m"]),
        "T_surface": float(parent["T_surface"]),
        "T_star_surface": float(parent.get("T_star_surface", 5772.0)),
        "S_earth": float(parent.get("S_earth", 1.0)),
        "day_s": float(parent.get("day_s", 86400.0)),
        "wind_surface_ms": float(parent.get("wind_surface_ms", 0.0)),
        "ocean_fraction": float(parent.get("ocean_fraction", 0.0)),
        "greenhouse_K": float(parent.get("greenhouse_K", 0.0)),
        # the law's own facts
        "jeans_keep_threshold": JEANS_KEEP,
        "gases_kept": kept,
        "escape_ratios": escapes,
        "kept_ratios": kept_ratios,
        "lost_ratios": lost_ratios,
        "retention_holds": bool(holds),
        "has_atmosphere": bool(kept),
    }


def emit(nums, t=1.0):
    """ONE DAY OF AIR: the terminator crossing, and the sky reddening where the path is long.

    WHAT WAS HERE, and one number in it was a lie about this membrane's own physics. The old emit
    scattered points to `z = -log(u) * 0.05` and called 0.05 the scale height -- but this membrane
    DERIVES `scale_height_m = 11312` on a radius of 5,256,133, which is 0.00215 of a radius.
    The drawn air was 23 TIMES THICKER than the law twelve lines above it. Dimensionally perfect,
    unit-perfect, and wrong by more than an order of magnitude: the class of error that only a
    RANGE can see, which is why folding.py carries regimes. It also ignored `t` entirely, under the
    boilerplate line four membranes in this tree shared, while declaring a movie 86,400 s long.

    WHAT IT DRAWS NOW.
      THE THICKNESS IS THE DERIVED ONE. H/R = 0.00215, so a planet's air really is a skin -- and
      to keep a skin visible the shell is drawn at a DECLARED exaggeration, published as
      `render_exaggeration`, which SCALES SOMETHING THAT EXISTS rather than minting a shell that
      does not. The density law is untouched: exp(-z/H) at the true H.
      THE DAY TURNS. The sun goes round once, because `duration_s` is this world's own day, and
      the lit crescent goes with it.
      THE COLOUR IS RAYLEIGH. Scattering goes as lambda^-4, so blue is thrown sideways out of the
      beam and what survives a long slant path is red. That single exponent gives a blue sky
      overhead and a red limb at the terminator with nothing else added -- and the reddening is
      strongest exactly where the day is ending, which is sunset, arriving unasked.

    LOCAL UNITS: 1.0 is the planet's radius.
    """
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, GLOW, AR, AB

    RAYLEIGH_TAU_550 = 0.0973    # Earth's measured Rayleigh optical depth at 550 nm, zenith
    EXPOSURE = 7.0               # LENS: how far the shutter is opened. Not a fact about the air.
    H_over_R = float(nums["scale_height_m"]) / float(nums["R"])
    EXAGGERATION = 12.0                 # DECLARED. See the docstring: it scales what exists.
    H = H_over_R * EXAGGERATION

    tt = float(t) % 1.0
    sun = np.array([math.cos(2.0 * math.pi * tt), math.sin(2.0 * math.pi * tt), 0.12],
                   dtype=np.float64)
    sun /= np.linalg.norm(sun)

    rng = np.random.default_rng(73)
    n = 12000
    d = fibonacci_sphere(n, jitter=0.9, seed=73)
    u = np.clip(rng.random(n), 1e-6, 1.0)
    z = -np.log(u) * H                              # exponential atmosphere, at the derived H
    P = d * (1.0 + z)[:, None]
    dens = np.exp(-z / max(H, 1e-9))

    # HOW MUCH AIR THE LIGHT CROSSED. Straight down it is one scale height; at a grazing angle it
    # is many, and that ratio is the airmass. Cheap and honest: 1/max(cos, floor).
    mu = P @ sun / np.maximum(np.linalg.norm(P, axis=1), 1e-9)
    lit_frac = np.clip(mu, 0.0, 1.0)
    airmass = 1.0 / np.clip(mu, 0.06, 1.0)

    # RAYLEIGH: optical depth goes as lambda^-4, so each band is extinguished by its own amount
    # over that path. Nothing here is a palette -- it is one exponent applied at three wavelengths.
    lam = np.array([615.0, 535.0, 465.0], np.float32)          # the render's R, G, B
    tau0 = RAYLEIGH_TAU_550 * (550.0 / lam) ** 4                # optical depth at zenith, per band
    trans = np.exp(-tau0[None, :] * airmass[:, None])           # what survives to the eye
    scattered = 1.0 - trans                                     # what the sky glows with
    # EXPOSURE, and it is a LENS not a fact. A bare atmospheric shell with no planet under it is
    # genuinely almost invisible -- tau of 0.1 at zenith means the sky scatters about a tenth of
    # what passes through it, which is why Earth's limb from orbit is a thin blue line and not a
    # glowing ball. The first render of this was physically right and visually nothing. So the
    # BRIGHTNESS is opened up and the RATIO BETWEEN BANDS -- which is the whole of the physics --
    # is left alone: lambda^-4 still decides the colour, exposure only decides how much of it
    # reaches the eye. Changing this number cannot change what colour the sky is.
    scattered = np.clip(scattered * EXPOSURE, 0.0, 1.0)

    # AND THE OTHER HALF, which the first version of this claimed and did not draw.  is
    # the light SCATTERED toward the eye, and at a grazing path every band saturates, so a shell
    # drawn from scattering alone goes WHITE at the limb -- which is what the render showed while
    # the docstring promised a red one. A sunset is not scattered light; it is the DIRECT BEAM,
    # surviving a long path, with its blue taken out of it. That is  itself -- the same
    # lambda^-4 read the other way round -- and it is what a low sun looks like.
    #
    # So both terms are drawn, weighted by how grazing the sightline is. The reddening is not a
    # colour anyone chose; it is what is LEFT after blue has been scattered away over 16 airmasses.
    graze = np.clip(1.0 - mu, 0.0, 1.0) ** 3
    col_rgb = scattered * (1.0 - graze)[:, None] + trans * EXPOSURE * 0.55 * graze[:, None]
    scattered = np.clip(col_rgb, 0.0, 1.0)

    b = blank(n)
    b[:, 0:3] = P
    col = (scattered * (0.25 + 0.75 * lit_frac)[:, None]).astype(np.float32)
    b[:, 16:19] = col
    b[:, AR:AB + 1] = col
    b[:, 19] = np.clip(0.55 * dens * (0.16 + 0.84 * lit_frac), 0.0, 1.0).astype(np.float32)
    b[:, 20] = surface_grain(n, radius=1.0 + H, cover=1.2)
    b[:, 11] = GLOW
    return b


def layout(nums):
    """WHAT IS CONTAINED HERE. theAtmosphere is the LAW -- what air is and what any air must
    satisfy. aNitrogenAtmosphere is the air that actually formed over this world -- named by the
    class its own mean molecule puts it in. It sits at the centre at full size: at this scale the
    membrane IS the air."""
    return {"aNitrogenAtmosphere": ((0.0, 0.0, 0.0), 1.0)}


def measure(nums):
    """The retention ledger must discriminate: kept gases above the Jeans bar, lost ones below it.
    If this fails, the law of keeping is wrong -- not the ledger."""
    kept = nums.get("kept_ratios", {})
    lost = nums.get("lost_ratios", {})
    return {"kept_above_threshold": all(v > JEANS_KEEP for v in kept.values()),
            "lost_below_threshold": all(v < JEANS_KEEP for v in lost.values()),
            "retention_holds": nums.get("retention_holds", False)}
