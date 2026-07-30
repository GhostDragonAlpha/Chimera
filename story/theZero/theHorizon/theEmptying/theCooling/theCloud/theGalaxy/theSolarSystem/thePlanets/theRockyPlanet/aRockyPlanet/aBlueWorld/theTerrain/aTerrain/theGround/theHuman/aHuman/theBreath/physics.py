"""theBreath -- the gas inside the suit, and what actually limits how long you can stay out.

THE EDGE. The parent established that this air cannot be trusted and that no pressure vessel is
needed. What it did NOT establish is what the person breathes instead. That is this chapter, and it
has one surprise in it: **the oxygen is not the problem.**

A sealed loop has two jobs -- put oxygen in and take carbon dioxide out -- and they are not
symmetric. Oxygen you carry as a compressed gas, which is dense and cheap. Carbon dioxide you must
chemically bind, one molecule of scrubber per molecule of gas, and that is heavy. So the CO2 side
runs out first, and by more than a factor of two. That is a real result in life-support engineering
and it falls straight out of stoichiometry here.

It also settles something operationally enormous that nobody asked for. Because the ambient pressure
is 0.52 bar, the loop can run AT ambient -- no differential at all -- so the tissue ratio on stepping
outside is below 1, and there is no prebreathe. On Earth an EVA from a 1 bar cabin into a 0.29 bar
suit has a ratio near 2.7 and costs hours of oxygen prebreathing to avoid the bends. Here you open
the door and walk out.

Contained in aHuman. Its movie is ONE BREATH.
"""
from __future__ import annotations

import math

import numpy as np

# ── RESPIRATORY PHYSIOLOGY AND CHEMISTRY. Measurements and stoichiometry: they read the same in any
# story, which is what makes them legal literals rather than borrowed numbers.
KJ_PER_L_O2 = 20.9          # energy released per litre of oxygen consumed (the caloric equivalent)
RQ = 0.85                   # respiratory quotient: litres of CO2 out per litre of O2 in, mixed diet
RHO_O2_G_L = 1.429          # density at STP
RHO_CO2_G_L = 1.977
PO2_SEA_LEVEL_BAR = 0.213   # what a person's lungs are built around: Earth at sea level
PO2_HYPOXIA_BAR = 0.16      # below this, consciousness goes
PO2_TOXIC_BAR = 0.50        # above this for hours, pulmonary oxygen toxicity
PCO2_LIMIT_BAR = 0.010      # comfortable ceiling in the loop (~7.6 mmHg); 0.02 brings headache
# LiOH: 2 LiOH + CO2 -> Li2CO3 + H2O. 47.9 g of LiOH per 44 g of CO2 is the ideal; packed beds
# achieve about half that in practice, because the bed channels and the outer grains cake first.
LIOH_KG_PER_KG_CO2 = 2.0
VENT_EQUIV = 25.0           # litres of air breathed per litre of O2 extracted
BREATHS_PER_MIN_REST = 13.0
TANK_BAR = 300.0            # storage pressure of the oxygen bottle

FREE = {
    # HOW LONG THEY MEAN TO BE OUTSIDE. Everything carried scales with this, and it is a plan, not
    # a physical constant -- which is exactly what a free number is.
    "excursion_h": {"lo": 0.5, "hi": 24.0, "default": 8.0,
                    "label": "hours outside", "unit": "h",
                    "local": "how long a person intends to stay out is a decision, not a law"},
}


def o2_consumption_l_min(metabolic_W):
    """Oxygen burned, from the heat produced. A body is a calorimeter: every litre of O2 it consumes
    liberates about 20.9 kJ, so a known wattage IS a known flow rate. Nothing about the suit here --
    this is the person."""
    return float(metabolic_W) / (KJ_PER_L_O2 * 1000.0) * 60.0


def loop_mix(P_loop_bar):
    """WHAT FRACTION OF THE LOOP MUST BE OXYGEN, and the window it has to sit inside.

    Aim for the partial pressure a person's lungs evolved around -- Earth at sea level, 0.213 bar --
    because then nothing about breathing feels different. The window is bounded below by hypoxia and
    above by oxygen toxicity, and both bounds are partial pressures, so both convert into fractions
    by dividing by the loop's total pressure. A thin loop needs a rich mix; that is the whole
    relationship, and it is why high-altitude flight uses oxygen masks."""
    P = max(float(P_loop_bar), 1e-9)
    return (PO2_SEA_LEVEL_BAR / P, PO2_HYPOXIA_BAR / P, PO2_TOXIC_BAR / P)


def tissue_ratio(P_from_bar, f_o2_from, P_to_bar):
    """THE BENDS, AS ONE NUMBER. Dissolved nitrogen does not care about total pressure, it cares
    about the nitrogen partial pressure it equilibrated at against the pressure it is suddenly asked
    to sit in. R = pN2(before) / P(after); below about 1.65 no prebreathe is needed."""
    pN2 = max(float(P_from_bar) * (1.0 - float(f_o2_from)), 0.0)
    return pN2 / max(float(P_to_bar), 1e-9)


def derive(parent, free):
    if parent is None or "r_helmet_m" not in parent:
        raise ValueError("theBreath requires aHuman as its parent")
    free = free or {}
    hours = float(free.get("excursion_h", FREE["excursion_h"]["default"]))

    P_amb = float(parent["P_surface_bar"])
    W = float(parent["metabolic_W"])

    # ── THE LOOP RUNS AT AMBIENT, and that is a finding, not a convenience ────────────────────
    # A suit only needs to hold pressure if the outside cannot supply it. Here it can: 0.52 bar is
    # eight times the Armstrong limit, so the garment seals against COMPOSITION rather than against
    # vacuum. Nothing balloons, no joint fights a differential, and the walk stays the parent's.
    P_loop = P_amb
    f_o2, f_o2_min, f_o2_max = loop_mix(P_loop)
    mix_is_possible = f_o2 <= 1.0

    # ── WHAT THE PERSON SPENDS ────────────────────────────────────────────────────────────────
    vo2 = o2_consumption_l_min(W)                    # L/min
    vco2 = RQ * vo2
    o2_kg = vo2 * RHO_O2_G_L / 1000.0 * 60.0 * hours
    co2_kg = vco2 * RHO_CO2_G_L / 1000.0 * 60.0 * hours
    scrubber_kg = co2_kg * LIOH_KG_PER_KG_CO2
    # the bottle: gas plus the vessel to hold it, at the same ratio theHuman used
    tank_kg = o2_kg * 3.5

    # ── WHICH ONE RUNS OUT FIRST ──────────────────────────────────────────────────────────────
    # This is the chapter's point. Oxygen is a gas you compress; CO2 is a solid you make. Binding a
    # kilo of exhaled carbon dioxide costs two kilos of lithium hydroxide, and no pressure helps.
    co2_limited = scrubber_kg > (o2_kg + tank_kg)
    consumables_kg = o2_kg + tank_kg + scrubber_kg

    # AND WHAT THE PARENT ALLOCATED. theHuman sized the same load from a per-day figure rather than
    # from stoichiometry; this membrane can check it, because it derived the chemistry.
    # NO DEFAULT. A 0.0 here would report the parent as having allocated MINUS eight kilograms of
    # stores, and then compute a negative endurance from it -- an audit of a number that was never
    # there, which is worse than no audit. The 8 kg is aHuman's own garment mass; the rest is stores.
    allocated = float(parent["suit_mass_kg"]) - 8.0
    shortfall_kg = consumables_kg - allocated
    endurance_on_allocation_h = (hours * allocated / consumables_kg) if consumables_kg > 0 else 0.0

    # ── STEPPING OUTSIDE ──────────────────────────────────────────────────────────────────────
    # Suppose the habitat runs the same loop at the same pressure -- then the ratio is the nitrogen
    # fraction itself, comfortably under 1, and there is nothing to decompress from.
    R = tissue_ratio(P_amb, f_o2, P_loop)
    R_earth_eva = tissue_ratio(1.013, 0.209, 0.29)   # the comparison, for scale: a real ISS EVA
    prebreathe_needed = R > 1.65

    # ── ONE BREATH ────────────────────────────────────────────────────────────────────────────
    ve = vo2 * VENT_EQUIV                            # minute ventilation, L/min
    f_breath = BREATHS_PER_MIN_REST * (1.0 + 0.35 * (W / 105.0 - 1.0))
    tidal_l = ve / max(f_breath, 1e-6)
    T_breath = 60.0 / max(f_breath, 1e-6)

    # the helmet's free volume -- what the sweep has to flush every breath
    r_in = float(parent["r_helmet_m"]) - float(parent["insulation_m"])
    v_helmet_l = (4.0 / 3.0 * math.pi * r_in ** 3) * 1000.0 * 0.55   # 0.55: a head is in the way
    flush_per_breath = tidal_l / max(v_helmet_l, 1e-9)

    return {
        # ITS REAL SIZE: the inside of a helmet. The smallest membrane in the story so far.
        "extent_m": 2.0 * r_in,
        # ITS OWN DURATION: one breath -- and it lands inside theHumanClock's band without being
        # geared, which is the second membrane in the whole story that can say that.
        "duration_s": T_breath,

        # the loop
        "P_ambient_bar": P_amb,
        "P_loop_bar": P_loop,
        "runs_at_ambient": True,
        "seals_against": "composition",
        "o2_fraction": f_o2,
        "o2_fraction_floor": f_o2_min,
        "o2_fraction_ceiling": min(f_o2_max, 1.0),
        "o2_partial_bar": f_o2 * P_loop,
        "mix_is_possible": mix_is_possible,
        "n2_fraction": 1.0 - f_o2,

        # the spend
        "metabolic_W": W,
        "vo2_l_min": vo2,
        "vco2_l_min": vco2,
        "excursion_h": hours,
        "o2_kg": o2_kg,
        "tank_kg": tank_kg,
        "co2_made_kg": co2_kg,
        "scrubber_kg": scrubber_kg,
        "consumables_kg": consumables_kg,

        # THE FINDING
        "co2_limited": co2_limited,
        "scrubber_over_oxygen": scrubber_kg / max(o2_kg + tank_kg, 1e-9),
        "parent_allocated_kg": allocated,
        "shortfall_kg": shortfall_kg,
        "endurance_on_allocation_h": endurance_on_allocation_h,

        # stepping outside
        "tissue_ratio": R,
        "tissue_ratio_earth_eva": R_earth_eva,
        "prebreathe_needed": prebreathe_needed,
        "prebreathe_ratio_limit": 1.65,

        # one breath
        "breaths_per_min": f_breath,
        "tidal_volume_l": tidal_l,
        "minute_ventilation_l": ve,
        "helmet_free_volume_l": v_helmet_l,
        "helmet_flushed_per_breath": flush_per_breath,
        "pco2_limit_bar": PCO2_LIMIT_BAR,

        # carried on
        "r_helmet_inner_m": r_in,
        "S_earth": float(parent["S_earth"]),
        "T_air_C": float(parent["T_air_C"]),
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- gas is matter, and this is the one membrane whose matter you cannot see through
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """The gas inside the helmet over one breath, coloured by how much carbon dioxide is in it.

    IN ITS OWN LOCAL UNITS: 1.0 is the helmet's inner diameter, and the origin is the middle of it.

    WHAT IS BEING DRAWN. Fresh mix enters at the top of the faceplate and sweeps DOWN across it --
    that is not decoration, it is what the sweep is for: a visor with still gas on it fogs, because
    a face is warm and wet and the plate is cold. The flow carries moisture away and takes exhaled
    CO2 with it, out at the chin to the scrubber. So on the exhale you can see the plume leave the
    mouth and get pulled across and out; on the inhale the plate clears.

    The colour IS the carbon dioxide partial pressure against the 0.010 bar ceiling this membrane
    derived -- pale where the gas is fresh, deepening where it is loaded. Nothing is stylised: if the
    scrubber were undersized the whole volume would sit dark, which is precisely the failure the
    numbers above say is waiting.
    """
    from matter import blank, GLOW, AR, AG, AB

    tt = float(t) % 1.0
    phase = 2.0 * math.pi * tt
    # exhale over the first 40% of the cycle, inhale over the rest -- expiration is the shorter half
    exhaling = tt < 0.40
    breath = math.sin(math.pi * (tt / 0.40)) if exhaling else 0.0

    rng = np.random.default_rng(31)
    n = 4200
    # fill the ball, biased to the shell so the volume reads as a volume and not a fog ball
    d = rng.normal(0.0, 1.0, (n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
    r = 0.5 * (rng.random(n) ** 0.45)
    P = d * r[:, None]

    # the sweep: a downward flow across the faceplate (+X is the way the person faces)
    # streamline coordinate s runs 0 at the inlet (top front) to 1 at the outlet (bottom front)
    front = np.clip(P[:, 0] / 0.5, -1.0, 1.0)
    height = np.clip(P[:, 2] / 0.5, -1.0, 1.0)
    s = np.clip((1.0 - height) * 0.5 + 0.25 * front, 0.0, 1.0)
    # gas advects along s with the cycle, so the pattern MOVES
    # AN INTEGER NUMBER OF TRANSITS PER CYCLE, or the loop does not close. This advected the field
    # by 1.6 transits per breath, so at t = 1 the pattern sat 0.6 of a transit away from where it
    # started and the movie popped 1.5x at the seam. A cyclic movie must return to its own first
    # frame; 2.0 makes it do so exactly, and two loop transits per breath is also what the parent's
    # own volumes say happens.
    travel = (s - tt * 2.0) % 1.0

    # the mouth: where CO2 enters, at the lower front
    mouth = np.array([0.34, 0.0, -0.12])
    dist = np.linalg.norm(P - mouth[None, :], axis=1)
    plume = np.exp(-(dist / 0.20) ** 2) * breath
    # loaded gas accumulates downstream of the mouth and is swept out
    carried = np.exp(-((travel - 0.55) / 0.28) ** 2) * 0.5 * (0.4 + 0.6 * breath)
    load = np.clip(plume + carried * (s > 0.35), 0.0, 1.4)

    # pCO2 in this parcel, against the ceiling the derivation set
    pco2_limit = float(nums["pco2_limit_bar"])
    pco2 = load * pco2_limit * 1.15

    b = blank(n)
    b[:, 0:3] = P
    # FRESH GAS IS PALE AND FAINT; LOADED GAS IS WARM AND OPAQUE. A gas you can see is a gas you
    # should not be breathing, which is the honest way round for this to read.
    fresh = np.array([0.62, 0.78, 0.95], np.float32)
    heavy = np.array([0.95, 0.62, 0.42], np.float32)
    f = np.clip(pco2 / pco2_limit, 0.0, 1.0)[:, None]
    col = fresh * (1.0 - f) + heavy * f
    b[:, 16:19] = col
    b[:, AR:AB + 1] = col
    # opacity tracks load: fresh mix is nearly invisible, which is what "breathable" looks like
    b[:, 19] = (0.035 + 0.30 * f[:, 0]).astype(np.float32)
    b[:, 20] = 0.052
    b[:, 11] = GLOW
    return b


def measure(nums):
    """Facts a reader can check without trusting the prose."""
    return {
        # the loop is possible at all
        "mix_is_possible": nums["mix_is_possible"],
        "o2_fraction": nums["o2_fraction"],
        "o2_inside_window": (nums["o2_fraction"] >= nums["o2_fraction_floor"]
                             and nums["o2_fraction"] <= nums["o2_fraction_ceiling"]),
        # THE CHAPTER'S CLAIM: carbon dioxide, not oxygen, is what runs out
        "co2_limited": nums["co2_limited"],
        "scrubber_over_oxygen": nums["scrubber_over_oxygen"],
        # THE PREDICTION IT WAS NEVER FITTED TO: no prebreathe, where Earth EVA needs hours
        "tissue_ratio": nums["tissue_ratio"],
        "prebreathe_needed": nums["prebreathe_needed"],
        "earth_eva_would_need_prebreathe": nums["tissue_ratio_earth_eva"] > 1.65,
        # the parent's allocation, audited
        "parent_allocation_short": nums["shortfall_kg"] > 0.0,
        "endurance_on_allocation_h": nums["endurance_on_allocation_h"],
        # its movie is human-scale without gearing
        "breath_in_human_band": 0.04 <= nums["duration_s"] <= 10.0,
        # the sweep actually turns the helmet over
        "helmet_flushed_per_breath": nums["helmet_flushed_per_breath"],
    }
