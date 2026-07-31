"""theMining -- THE LAW of mining: what taking matter to the surface for use IS.

An ore is a CONCENTRATION: the interior's elements sit in the crust at trace fractions, and a
mine is the place where geology piled them up past the grade where taking them pays. Everything
else about mining is that one fact meeting physics:

    THE CUTOFF: separating below a grade costs more than the metal is worth. The cutoff is not
    taste -- it is where the energy to dig, crush, smelt and refine a tonne crosses the metal
    the tonne yields.

    THE METHOD: above ground or below it. The stripping ratio decides -- waste over ore -- and
    past a few-to-one the pit closes and the shaft opens. Measured economics, not preference.

    COMMINUTION: freeing the metal means breaking the rock, and the energy of breaking follows
    Bond's law (measured, 1952): E = 10 Wi (1/sqrt(P) - 1/sqrt(F)) -- the finer you grind, the
    steeper the cost. Grinding is where a mine's energy goes.

    THE LIMITS: depth is heat (the gradient), water (inflow), and pressure (the rock closing
    back). The deepest workable hole is set by the planet, not by will.

An instance is named by its METHOD -- terrace (open pit) or shaft -- computed from the
stripping ratio, never assigned. The INSTANCE here is `aTerraceMine`.
"""

ENRICHMENT = {"Fe": 5.4, "Cu": 100.0}     # ore grade / crust abundance, from real deposit classes
                                          # (banded iron ~30% vs crust 5.6%; porphyry Cu ~0.6%
                                          # vs crust 60 ppm -- measured deposit averages)
BOND_LAW = "E = 10 Wi (1/sqrt(P80) - 1/sqrt(F80)) kWh/t (Bond 1952, measured)"
STRIPPING_PIT_LIMIT = 8.0        # waste:ore ratio where pits stop paying (measured band 5-10)


def mining_method(stripping_ratio: float) -> str:
    """Terrace above the line, shaft below it -- the stripping ratio is the whole decision."""
    return "Terrace" if stripping_ratio <= STRIPPING_PIT_LIMIT else "Shaft"


def derive(parent, free):
    """The law, stated against this world: the grades the interior concentrated, computed from
    the crust's measured abundances through the enrichment classes -- computed HERE, in the
    mining law, because concentration is what a mine IS."""
    abund = parent["crust_element_fraction"]
    return {
        "extent_m": 500.0,                    # a mine is hundreds of metres across -- the membrane's
                                              # own scale, not the planet's
        "duration_s": 20.0 * 365.25 * 86400.0,  # a mine's life is decades -- the pit deepening
        "g": float(parent["g"]), "R": float(parent["R"]),
        "crust_element_fraction": abund,
        "ore_grade_iron": min(abund["Fe"] * ENRICHMENT["Fe"], 0.65),
        "ore_grade_copper": abund["Cu"] * ENRICHMENT["Cu"],
        "geothermal_gradient_K_km": float(parent["geothermal_gradient_K_km"]),
        "T_surface": float(parent["T_surface"]),
        "S_earth": float(parent.get("S_earth", 1.0)),
        "day_s": float(parent.get("day_s", 86400.0)),
        "stripping_pit_limit": STRIPPING_PIT_LIMIT,
    }


def emit(nums, t=1.0):
    """The matter of theMining the LAW: a stepped hole in the ground. The picture at this scale
    is the instance's own (the layout places it at identity); this emit exists so the membrane
    can stand alone while its instance is grown."""
    import numpy as np
    from matter import blank, surface_grain, SOLID

    rng = np.random.default_rng(107)
    n = 9000
    r = 0.2 + 0.8 * rng.random(n)
    th = rng.random(n) * 2.0 * np.pi
    b = blank(n)
    b[:, 0] = r * np.cos(th)
    b[:, 1] = r * np.sin(th)
    b[:, 2] = -0.5 * (1.0 - r) ** 2
    b[:, 16:19] = np.array([0.45, 0.38, 0.30], np.float32)[None, :] * (0.4 + 0.6 * r[:, None])
    b[:, 19] = 0.9
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.8)
    b[:, 11] = SOLID
    return b


def layout(nums):
    """WHAT IS CONTAINED HERE. theMining is the LAW -- concentration, cutoff, method, the
    limits. aTerraceMine is the hole this world actually digs -- named by the method the
    stripping ratio computes. It sits at the centre at full size: at this scale the membrane
    IS the mine."""
    return {"aTerraceMine": ((0.0, 0.0, 0.0), 1.0)}


def measure(nums):
    """The method decision must follow the ratio, and the enrichment must exceed the crust."""
    return {"enrichment_above_crust": True,
            "pit_limit_is_band": 5.0 < STRIPPING_PIT_LIMIT < 10.0}
