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
    """The matter of theAtmosphere the LAW: air as held gas -- a soft, edgeless glow hugging a
    world. The picture at this scale is the instance's own (the layout places it at identity):
    this emit exists so the membrane can stand alone while its instance is being grown."""
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, GLOW

    rng = np.random.default_rng(73)
    n = 12000
    d = fibonacci_sphere(n, jitter=0.9, seed=73)
    u = np.clip(rng.random(n), 1e-6, 1.0)
    z = -np.log(u) * 0.05                      # edgeless: density falls off with height
    b = blank(n)
    b[:, 0:3] = d * (1.0 + z)[:, None]
    dens = np.exp(-z / 0.05)
    b[:, 16:19] = np.array([0.45, 0.62, 1.0], np.float32)[None, :] * (0.3 + 0.7 * dens)[:, None]
    b[:, 19] = (0.10 * dens).astype(np.float32)
    b[:, 20] = surface_grain(n, radius=1.03, cover=1.2)
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
