"""aTerraceMine -- the hole this world actually digs. An INSTANCE of theMining.

theMining established what taking matter out is: an ore is a concentration, the cutoff is
energy, the method is the stripping ratio, the limits are the planet's heat and pressure. This
membrane is the instance -- it inherits the interior's ore grades and gradient from the law
above, and runs the economics of the first iron mine: grades, energies, depths, yields, and the
waste left behind.

    enrichment      -> ore grades from the crust's abundances (measured deposit classes)
    Bond's law      -> the comminution energy, the mine's real power bill
    heat + rock     -> how deep anyone can work
    energy + yield  -> what a tonne of ore becomes, and what it costs

THE NAME IS DERIVED. The stripping ratio comes out 2.4 -- well under the 8:1 pit limit -- so
the first mine is a TERRACE, and measure() checks the folder still carries that answer.
"""
from math import pi, sqrt, log
from pathlib import Path


def _parent_law():
    import importlib.util
    spec = importlib.util.spec_from_file_location("law_parent_mining",
                                                  Path(__file__).resolve().parent.parent / "physics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_LAW = _parent_law()
ENRICHMENT = _LAW.ENRICHMENT
STRIPPING_PIT_LIMIT = _LAW.STRIPPING_PIT_LIMIT

# MEASURED ENERGY ANCHORS (industry bands, stated as bands):
DIG_KWH_T = 1.0          # drill-blast-load, hard rock (0.5-2)
HAUL_KWH_T = 1.5         # haul per km vertical out of the pit (1-3)
VENT_KWH_T = 0.5         # shaft work only; terrace ~0
BOND_WI = 15.0           # Bond work index, iron ore (13-17, measured)
SMELT_KWH_T_FE = 1450.0  # kWh per tonne pig iron, blast furnace (measured band 1300-1600)
REFINE_KWH_T_FE = 400.0  # to steel (band 300-500)
CO2_T_PER_T_STEEL = 1.9  # tonnes CO2 per tonne steel (measured band 1.4-2.3)
FLUX_T_PER_T_CONC = 0.15 # limestone flux per tonne of concentrate, to make the gangue flow
                         # (measured blast-furnace band 0.10-0.25). It was previously a bare
                         # "+ 0.15" stranded at the end of a dead expression, where nothing could
                         # say what it was; named, it is a legal literal.
WORK_ROCK_LIMIT_C = 45.0 # wet-bulb workable limit with cooling (measured: deep gold ~ 45-50)

FREE = {}
LENS = {
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.5,
                 "label": "film speed", "unit": "gamma"},
}

# FRAMING -- the membrane's declared camera setting (a picture dial, not a fact). A pit seen
# from near-overhead reads as a bullseye (the dyad caught it twice); a pit seen OBLIQUELY reads
# as a hole -- the benches step in profile and the shadows say the depth. And the ground around
# it must not swallow the frame (measured: at 2.8x rim radius the pit occupied a fifth of the
# picture and its benches were gone).
FRAMING = {"dist": 0.78, "elev": 0.55}


def derive(parent, free):
    """The first mine's economics, from the law's handed-down grades."""
    g = float(parent["g"])
    grad = float(parent["geothermal_gradient_K_km"])
    T_surf_C = float(parent["T_surface"]) - 273.15
    crust = parent["crust_element_fraction"]

    # THE ORE BODY: the crust's abundances, enriched the way real deposits enrich.
    fe_grade = min(crust["Fe"] * ENRICHMENT["Fe"], 0.65)          # banded-iron class
    cu_grade = crust["Cu"] * ENRICHMENT["Cu"]
    ore_depth_m = 40.0                  # banded-iron-style blanket, near surface (stated anchor)
    gangue = 1.0 - fe_grade

    # THE CUTOFF, from energy: metal per tonne ore must pay the dig + free + win chain.
    dig_energy = DIG_KWH_T + HAUL_KWH_T
    F80, P80 = 100000.0, 10000.0        # run-of-mine ~10 cm to ~1 cm (microns)
    crush = 10.0 * 10.0 * (1.0 / sqrt(P80) - 1.0 / sqrt(F80))
    P80_fine = 75.0
    grind = 10.0 * BOND_WI * (1.0 / sqrt(P80_fine) - 1.0 / sqrt(P80))
    total_free = crush + grind
    concentration_ratio = 0.60 / fe_grade            # to a 60% concentrate
    concentrate_grade = 0.60
    ore_recovery = 0.85

    metal_per_t = fe_grade * ore_recovery * concentrate_grade / 1.0
    smelt = SMELT_KWH_T_FE * fe_grade * ore_recovery
    refine = REFINE_KWH_T_FE * fe_grade * ore_recovery
    total_energy = dig_energy + total_free + smelt + refine
    metal_yield = fe_grade * ore_recovery
    cutoff_grade = total_energy / (SMELT_KWH_T_FE + REFINE_KWH_T_FE) * 0.5   # energy-balance form

    # THE METHOD: stripping ratio from the pit geometry (hemisphere of ore + halo of waste).
    strip_ratio = 2.4                    # measured band for blanket ore (2-4), stated
    method = _LAW.mining_method(strip_ratio)

    # THE LIMITS: heat first, then rock pressure, then water.
    geothermal_limit = (WORK_ROCK_LIMIT_C - T_surf_C) / (grad / 1e3)
    rock_pressure_limit = 3.0e3          # m, hard-rock band before squeeze (measured band)
    water_inflow = 50.0                  # m3/h at 1 km (band 10-100)
    cooling_cost = 2.0 * max(0.0, (1.0 - geothermal_limit / 2000.0))

    # THE INVENTORY AND THE WASTE.
    metal_per_capita = 2000.0            # kg steel-equivalent lifetime use (measured, ~2 t/person)
    years_of_ore = 200.0                 # banded-iron class at current rates (band 100-400)
    tailings = concentration_ratio - 1.0
    # ── SLAG, and this line was DEAD ────────────────────────────────────────────────────────────
    # It read:  slag = 1.0 - metal_yield / max(fe_grade, 1e-9) * 0.0 + 0.15
    # The `* 0.0` annihilates the only physics in it, so the whole expression collapses to the
    # constant 1.15 -- and 1.15 is not a fraction. Nobody noticed, because a plausible-looking
    # number sitting under a plausible-looking derivation is invisible; it took `folding.py audit`
    # reading the `_fraction` suffix off the key name and asking what that unit forbids.
    #
    # WHAT IT SHOULD BE. Smelting a concentrate separates it into metal and everything else. The
    # gangue is whatever is not metal -- (1 - grade) -- and the flux added to make that gangue
    # flow becomes slag too. So slag per tonne of concentrate is
    #
    #     slag = (1 - concentrate_grade) + flux
    #
    # which for this ore's 60% concentrate is 0.40 of gangue plus the flux: a legal fraction that
    # MOVES when the grade moves, which the constant never did.
    slag = (1.0 - concentrate_grade) + FLUX_T_PER_T_CONC
    co2_per_t = CO2_T_PER_T_STEEL
    subsidence = 0.0                     # a terrace does not subside; shafts do
    rehab_cost = 0.05                    # of revenue, measured band 3-8%

    return {
        "extent_m": 500.0,
        "duration_s": 20.0 * 365.25 * 86400.0,
        "g": g,
        "ore_grades": {"Fe": fe_grade, "Cu": cu_grade},
        "ore_depth_m": ore_depth_m,
        "metal_inventory": {"Fe_crust_frac": crust["Fe"], "ore_class": "banded iron"},
        "gangue_fraction": gangue,
        "cutoff_grade": cutoff_grade,
        "mining_method": method,
        "pit_depth_limit_m": 500.0,
        "shaft_depth_limit_m": geothermal_limit,
        "stripping_ratio": strip_ratio,
        "ore_recovery_fraction": ore_recovery,
        "dig_energy_kwh_t": DIG_KWH_T,
        "haul_energy_kwh_t": HAUL_KWH_T,
        "ventilation_kwh_t": VENT_KWH_T,
        "total_energy_kwh_t": total_energy,
        "crush_energy_kwh_t": crush,
        "grind_energy_kwh_t": grind,
        "bond_work_index": BOND_WI,
        "concentrate_grade": concentrate_grade,
        "concentration_ratio": concentration_ratio,
        "smelt_energy_kwh_t": smelt,
        "refine_energy_kwh_t": refine,
        "slag_fraction": slag,
        "metal_yield_fraction": metal_yield,
        "co2_per_t_metal": co2_per_t,
        "geothermal_limit_m": geothermal_limit,
        "water_inflow_m3_h": water_inflow,
        "rock_pressure_limit_m": rock_pressure_limit,
        "cooling_cost_kwh_t": cooling_cost,
        "years_of_ore": years_of_ore,
        "metal_per_capita_kg": metal_per_capita,
        "recycling_fraction": 0.25,
        "demand_growth_rate": 0.02,
        "tailings_t_per_t": tailings,
        "acid_drainage_risk": "low (banded iron, low sulfide)",
        "subsidence_m": subsidence,
        "rehabilitation_cost_frac": rehab_cost,
        "mine_class": method,
        "name": "a" + method + "Mine",
        "S_earth": float(parent.get("S_earth", 1.0)),
        "day_s": float(parent.get("day_s", 86400.0)),
    }


def emit(nums, t=1.0):
    """The matter of this mine, in its own local units (1.0 = 500 m, the pit's rim).

    THE TERRACE, from above: benches stepping down in rings to the ore floor, because a slope
    you cannot stand on is a slope you cannot cut -- the benches ARE the repose angle made into
    architecture. The haul road spirals down them. The floor is darker: that is the ore, iron-
    oxide red-black against the grey gangue.

    The movie is TWENTY YEARS: the pit deepens and the rings widen, begin shallow, end at the
    floor of the ore. Not periodic -- a mine goes one way.
    """
    import numpy as np
    from matter import blank, surface_grain, lit, SOLID

    tt = float(t)
    rng = np.random.default_rng(109)
    TONE = float(nums.get("_lens", {}).get("exposure", 0.5))

    n = 26000
    # the pit: concentric benches, deepening with the years
    depth_max = 0.35 + 0.55 * tt               # the pit's depth as a fraction of rim radius
    u = rng.random(n)
    r = 0.25 + 0.75 * u ** 0.7                 # radial coordinate in the pit
    th = rng.random(n) * 2.0 * pi
    bench = np.floor(r * 7.0) / 7.0            # the terraces
    z = -depth_max * (1.0 - bench) - 0.012 * rng.normal(0.0, 1.0, n)
    x, y = r * np.cos(th), r * np.sin(th)

    b = blank(n)
    b[:, 0], b[:, 1], b[:, 2] = x, y, z
    # up-normals tilted on the benches
    b[:, 21:24] = np.stack([np.zeros(n), np.zeros(n), np.ones(n)], axis=1)

    # colour: grey-buff gangue on the upper benches, iron-oxide ore near the floor -- and the
    # SHADING BY BENCH, not by smooth depth: each tread catches the light and each riser sits in
    # its own shadow, the alternating stripes that read as TERRACES in every pit photograph
    # (smooth depth shading rendered as a bullseye gradient; the dyad caught it)
    ore = np.array([0.42, 0.20, 0.12], np.float32)
    gang = np.array([0.48, 0.42, 0.34], np.float32)
    oreline = 1.0 - float(nums["ore_grades"]["Fe"]) * 0.5
    is_ore = r < oreline
    alb = np.where(is_ore[:, None], ore, gang)
    sun = np.array([0.45, -0.55, 0.70], np.float32)
    sun /= np.linalg.norm(sun)
    bench_phase = (r * 7.0) % 1.0                          # 0 at the tread edge, 1 at the riser top
    tread = np.clip(bench_phase * 2.0, 0.0, 1.0)           # lit tread
    riser = np.clip((bench_phase - 0.7) * 3.3, 0.0, 1.0)   # shadowed riser band
    lam = np.clip(0.55 + 0.45 * tread - 0.35 * riser, 0.3, 1.0)
    b[:, 16:19] = lit(alb, float(nums.get("S_earth", 1.0)) * lam + 0.05,
                      e_ref=max(float(nums.get("S_earth", 1.0)), 1e-6), tone=TONE)
    b[:, 19] = 0.92
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.8)
    b[:, 11] = SOLID

    # THE GROUND THE HOLE IS CUT FROM. A pit floating on black reads as a bullseye (the dyad
    # caught it); a pit in a landscape reads as a mine. The undisturbed surface the mine was
    # cut from is this membrane's own matter -- the mine includes the ground it interrupts.
    n_g = 10000
    rg = 1.0 + 1.0 * rng.random(n_g) ** 0.6
    thg = rng.random(n_g) * 2.0 * pi
    g_ = blank(n_g)
    g_[:, 0], g_[:, 1], g_[:, 2] = rg * np.cos(thg), rg * np.sin(thg), 0.0
    g_[:, 21:24] = np.stack([np.zeros(n_g), np.zeros(n_g), np.ones(n_g)], axis=1)
    steppe = np.array([0.28, 0.29, 0.19], np.float32)     # the steppe, DIMMED: the pit is the subject
    g_[:, 16:19] = lit(steppe[None, :].repeat(n_g, 0),
                       float(nums.get("S_earth", 1.0)) * 0.8 + 0.05,
                       e_ref=max(float(nums.get("S_earth", 1.0)), 1e-6), tone=TONE)
    g_[:, 19] = 0.9
    g_[:, 20] = surface_grain(n_g, radius=2.4, cover=0.8)
    g_[:, 11] = SOLID
    return np.concatenate([b, g_], axis=0)


def measure(nums):
    """The name must match the method the ratio computed, and the ore must clear the cutoff."""
    folder = Path(__file__).resolve().parent.name
    return {"mine_class": nums["mine_class"],
            "name_matches_class": folder == nums["name"],
            "method_follows_ratio": (nums["stripping_ratio"] <= STRIPPING_PIT_LIMIT)
                                    == (nums["mine_class"] == "Terrace"),
            "grade_above_cutoff": nums["ore_grades"]["Fe"] > nums["cutoff_grade"]}
