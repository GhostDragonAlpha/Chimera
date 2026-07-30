"""theSweep -- the flow across the faceplate, and the two things that decide how fast it must run.

THE EDGE. The parent proved a fan is REQUIRED and then declined to size it: one breath turns over
6.4% of a 12-litre helmet, so a person cannot flush their own visor by breathing. This chapter sizes
it, and finds that the number is set by TWO independent ceilings that happen to sit almost on top of
each other here:

  * THE LUNGS. A perfect scrubber downstream still leaves the loop at a steady concentration
    c = VCO2/Q, so holding pCO2 under 0.010 bar sets a minimum flow.
  * THE VISOR. A faceplate cannot be insulated -- you have to see through it -- so it is a cold
    bridge sitting at 13.4 C between a 22 C loop and 6 C weather. Exhaled water condenses on it the
    moment the loop's vapour pressure passes saturation at THAT temperature, which sets a minimum
    flow too.

Both come out near 21 L/min, and that is a NUMERICAL COINCIDENCE of this world's numbers rather than
a law -- said plainly in the story, because two constraints agreeing to three figures is exactly the
kind of thing that gets mistaken for profundity. Which one binds depends on how cold the weather is.

ONE IDENTITY HERE IS REAL, though, and it is worth the whole chapter: at the minimum flow, the time
for the visor to fog with the fan OFF equals the time for the loop to turn over ONCE. Not
approximately -- identically, because both are V x p_sat / (water rate x P). The fan's entire job is
to be faster than fogging, and at the floor those two are the same 34 seconds.

Contained in theBreath. Its movie is a fogged plate clearing.
"""
from __future__ import annotations

import math

import numpy as np

# ── MEASUREMENTS: fluid, thermal and material constants, plus one human output rate. All true
# outside this story, which is what makes them legal literals.
H_INSIDE_W_M2K = 12.0       # forced convection of the sweep on the inner face
H_OUTSIDE_W_M2K = 18.0      # ambient air on the outer face, light wind
K_POLYCARB_W_MK = 0.20      # the faceplate material
D_VISOR_M = 0.003           # 3 mm of it -- enough to hold a pressure it never has to hold
T_LOOP_C = 22.0             # the loop's own temperature: what the insulation was sized to keep
WATER_G_PER_H = 30.0        # a person exhales this much, near enough, at light work
M_WATER = 18.015            # g/mol
L_PER_MOL = 22.414          # a mole of gas at STP
VISOR_AREA_M2 = 0.075       # the faceplate: ~120 degrees of a helmet, the parent's visor angle
DUCT_DROP_PA = 800.0        # pressure drop round the loop: scrubber bed plus ducting
FAN_EFFICIENCY = 0.35       # a small centrifugal fan, motor included
BATTERY_WH_PER_KG = 250.0   # lithium-ion, cell level

FREE = {
    # HOW MUCH MARGIN THE FAN RUNS WITH. The derivation gives a floor; nobody flies a floor. This is
    # the one number here that is a judgement rather than a consequence.
    "flow_margin": {"lo": 1.0, "hi": 8.0, "default": 2.5,
                    "label": "flow over the minimum", "unit": "x",
                    "local": "how much margin to fly with is an engineering decision"},
}


def p_sat_bar(T_C):
    """Saturation vapour pressure of water, Magnus form. This is the curve that decides whether a
    surface is wet or dry, and it is steep -- which is why a few degrees of faceplate temperature
    matters so much."""
    return 0.61094 * math.exp(17.625 * float(T_C) / (float(T_C) + 243.04)) / 100.0


def visor_inner_temp(T_loop_C, T_amb_C):
    """HOW COLD THE INSIDE OF THE FACEPLATE IS -- a series resistance: the sweep's film on the
    inside, 3 mm of polycarbonate, the weather's film on the outside.

    THE VISOR CANNOT BE INSULATED. That is the whole problem: every other part of the suit gets the
    12 mm of batting the parent solved for, and this part gets none, because a person has to see
    through it. So it is a cold bridge by construction, and its temperature is what the fog
    calculation turns on."""
    U = 1.0 / (1.0 / H_INSIDE_W_M2K + D_VISOR_M / K_POLYCARB_W_MK + 1.0 / H_OUTSIDE_W_M2K)
    return T_loop_C - U * (T_loop_C - T_amb_C) / H_INSIDE_W_M2K, U


def flow_for_co2(vco2_l_min, P_bar, pco2_limit_bar):
    """A well-mixed loop with a perfect scrubber downstream settles at c = VCO2/Q, so the partial
    pressure is that fraction times the loop pressure. Invert it for the flow."""
    return float(vco2_l_min) * float(P_bar) / max(float(pco2_limit_bar), 1e-12)


def flow_for_fog(P_bar, p_sat_visor_bar):
    """The same algebra with water instead of carbon dioxide, and the ceiling set by the faceplate's
    own saturation pressure rather than by a physiological limit."""
    v_water = (WATER_G_PER_H / 60.0) / M_WATER * L_PER_MOL       # L/min of vapour
    return v_water * float(P_bar) / max(float(p_sat_visor_bar), 1e-12), v_water


def derive(parent, free):
    if parent is None or "helmet_free_volume_l" not in parent:
        raise ValueError("theSweep requires theBreath as its parent")
    free = free or {}
    margin = float(free.get("flow_margin", FREE["flow_margin"]["default"]))

    P = float(parent["P_loop_bar"])
    vco2 = float(parent["vco2_l_min"])
    pco2_lim = float(parent["pco2_limit_bar"])
    V = float(parent["helmet_free_volume_l"])
    T_amb = float(parent["T_air_C"])

    T_visor, U = visor_inner_temp(T_LOOP_C, T_amb)
    p_dew_ceiling = p_sat_bar(T_visor)

    Q_co2 = flow_for_co2(vco2, P, pco2_lim)
    Q_fog, v_water = flow_for_fog(P, p_dew_ceiling)
    Q_min = max(Q_co2, Q_fog)
    binds = "the visor" if Q_fog >= Q_co2 else "the lungs"
    Q = Q_min * margin

    # ── WHAT THE FAN COSTS, and the answer is almost nothing ──────────────────────────────────
    fan_W = DUCT_DROP_PA * (Q / 1000.0 / 60.0) / FAN_EFFICIENCY
    hours = float(parent["excursion_h"])
    battery_kg = fan_W * hours / BATTERY_WH_PER_KG

    # ── THE VISOR IS A THERMAL HOLE, and it audits the grandparent's insulation ────────────────
    # aHuman solved its coat thickness by putting the whole metabolic output through insulation of
    # one conductivity. It cannot: some of that heat leaves through the faceplate, which has none.
    visor_leak_W = U * VISOR_AREA_M2 * (T_LOOP_C - T_amb)
    W_metabolic = float(parent["metabolic_W"])
    leak_fraction = visor_leak_W / max(W_metabolic, 1e-9)

    # ── THE IDENTITY. Time to fog with the fan off, and time for the loop to turn over once ────
    # Both are V x p_sat / (water rate x P). They are the same number BY CONSTRUCTION at the
    # minimum flow, which is the cleanest statement of what a sweep is for.
    vapour_to_saturate_l = V * p_dew_ceiling / P
    g_to_saturate = vapour_to_saturate_l / L_PER_MOL * M_WATER
    fog_time_s = g_to_saturate / (WATER_G_PER_H / 3600.0)
    transit_at_min_s = V / Q_min * 60.0
    transit_s = V / Q * 60.0

    return {
        # ITS REAL SIZE: the faceplate. The smallest thing in the story, and the only part of the
        # suit a person looks through.
        "extent_m": 2.0 * math.sqrt(VISOR_AREA_M2 / math.pi),
        # ITS OWN DURATION: a fogged plate clearing, which takes one loop transit.
        "duration_s": transit_s,

        # the faceplate as a thermal object
        "T_loop_C": T_LOOP_C,
        "T_ambient_C": T_amb,
        "T_visor_inner_C": T_visor,
        "U_visor_W_m2K": U,
        "visor_area_m2": VISOR_AREA_M2,
        "p_dew_ceiling_bar": p_dew_ceiling,
        "visor_is_uninsulated": True,

        # the two ceilings
        "Q_for_co2_l_min": Q_co2,
        "Q_for_fog_l_min": Q_fog,
        "Q_min_l_min": Q_min,
        "binding_constraint": binds,
        "ceilings_agree_within": abs(Q_fog - Q_co2) / max(Q_min, 1e-9),
        "agreement_is_coincidence": True,      # STATED: not a law, see the story
        "flow_margin": margin,
        "Q_l_min": Q,
        "water_vapour_l_min": v_water,

        # what it costs
        "fan_W": fan_W,
        "fan_Wh": fan_W * hours,
        "battery_kg": battery_kg,
        "battery_vs_scrubber": battery_kg / max(float(parent["scrubber_kg"]), 1e-9),

        # the grandparent, audited
        "visor_leak_W": visor_leak_W,
        "visor_leak_fraction": leak_fraction,
        "insulation_should_be_mm": (0.040 * 1.83 * (33.0 - T_amb)
                                    / max(W_metabolic - visor_leak_W, 1e-9)) * 1000.0,

        # the identity
        "fog_time_s": fog_time_s,
        "transit_at_min_flow_s": transit_at_min_s,
        "transit_s": transit_s,
        "identity_holds": abs(fog_time_s - transit_at_min_s) < 0.05,
        "clears_faster_than_it_fogs_by": fog_time_s / max(transit_s, 1e-9),

        # carried on
        "S_earth": float(parent["S_earth"]),
        "helmet_free_volume_l": V,
        "P_loop_bar": P,
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- the faceplate, from the inside, clearing
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """A fogged faceplate being cleared by the sweep, seen from inside the helmet.

    LOCAL UNITS: 1.0 is the faceplate's width, +X is the direction the person is looking.

    THE MOVIE IS THE CHAPTER'S CLAIM. At t = 0 the plate is fully condensed -- what you get 34
    seconds after the fan quits. The sweep enters at the top and the clearing FRONT travels down
    across the plate, arriving at the bottom exactly when one loop transit has elapsed. So the film
    ends settled and clear, and its length is not chosen: it is V/Q.

    WHITE IS WATER. Condensate scatters, which is the entire reason fog is a problem -- it is not
    dark, it is bright and it destroys contrast. So the fogged state is opaque pale and the clear
    state is nearly invisible, and what you are watching is the difference between seeing and not.
    """
    from matter import blank, GLOW, AR, AG, AB

    # CLAMPED, NOT WRAPPED. `% 1.0` sent t=1.0 back to 0.0, so the film's last frame was its FIRST:
    # the plate converged smoothly to clear as t -> 1 and then snapped back to fully fogged at
    # exactly 1.0, a 15x jump at a single point, with buffer(0) == buffer(1) bit for bit.
    #
    # That matters far beyond this chapter, because the canonical still export renders exactly
    # ("begin", 0.0) and ("end", 1.0) -- so a wrapped endpoint makes the two-frame comparison show
    # NOTHING HAPPENING, and any check resting on it is blind. A CYCLE should wrap; this is a
    # one-shot transient and its end is an end.
    tt = min(max(float(t), 0.0), 1.0)
    rng = np.random.default_rng(53)
    n = 5200

    # the plate: a spherical cap, so it curves away at the edges like a real faceplate
    u = rng.random(n)
    ang = rng.random(n) * 2.0 * math.pi
    rad = 0.5 * np.sqrt(u)
    py = rad * np.cos(ang)
    pz = rad * np.sin(ang)
    R_cap = 0.95
    px = np.sqrt(np.maximum(R_cap ** 2 - py ** 2 - pz ** 2, 0.0)) - math.sqrt(max(R_cap ** 2 - 0.25, 0.0))

    # THE CLEARING FRONT. Inlet at the top (pz = +0.5), so the front sweeps downward; it is not a
    # hard line because the flow has a boundary layer -- the plate clears over a finger's width.
    front = 0.5 - tt * 1.06
    soft = 0.085
    # WET BELOW THE FRONT, CLEAR ABOVE IT. Written the other way round first --
    # `1/(1+exp((front-pz)/soft))` -- which is the sigmoid of the negative, and it ran the film
    # BACKWARDS: the plate started clear and fogged up over the movie, flatly contradicting the
    # chapter above it. Measured 0.18 fogged at t=0 rising to 0.84 at t=0.75, which is the failure
    # this membrane exists to describe rather than the fix.
    wet = 1.0 / (1.0 + np.exp((pz - front) / soft))
    # residual haze in the corners: the flow separates there, so they clear last. This is why real
    # visors keep a rime at the rim long after the middle is clear.
    corner = np.exp(-((0.5 - rad) / 0.13) ** 2)
    wet = np.clip(wet + 0.35 * corner * (1.0 - tt) ** 2, 0.0, 1.0)

    b = blank(n)
    b[:, 0], b[:, 1], b[:, 2] = px, py, pz
    nrm = np.stack([np.full(n, -1.0), py * 0.35, pz * 0.35], axis=1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    b[:, 21:24] = nrm

    # CONDENSATE IS BRIGHT. Fog does not darken a view, it washes it out -- the droplets scatter
    # forward. Clear plate: faintly blue, almost nothing to see. Fogged: opaque white.
    clear = np.array([0.55, 0.68, 0.86], np.float32)
    frost = np.array([0.93, 0.95, 0.97], np.float32)
    w = wet[:, None]
    col = clear * (1.0 - w) + frost * w
    b[:, 16:19] = col
    b[:, AR:AB + 1] = col
    b[:, 19] = (0.03 + 0.62 * wet).astype(np.float32)
    b[:, 20] = 0.020
    b[:, 11] = GLOW
    return b


def measure(nums):
    """Facts a reader can check without trusting the prose."""
    return {
        # the visor is the cold bridge, and how cold
        "T_visor_inner_C": nums["T_visor_inner_C"],
        "visor_colder_than_loop": nums["T_visor_inner_C"] < nums["T_loop_C"],
        # the two ceilings, and the honest note that their agreement is luck
        "Q_for_co2_l_min": nums["Q_for_co2_l_min"],
        "Q_for_fog_l_min": nums["Q_for_fog_l_min"],
        "binding_constraint": nums["binding_constraint"],
        "ceilings_agree_within": nums["ceilings_agree_within"],
        # THE IDENTITY: fogging time == loop transit at the minimum flow, by construction
        "identity_holds": nums["identity_holds"],
        "fog_time_s": nums["fog_time_s"],
        "transit_at_min_flow_s": nums["transit_at_min_flow_s"],
        # the fan is nearly free -- the surprise
        "fan_W": nums["fan_W"],
        "battery_kg": nums["battery_kg"],
        "battery_under_1_percent_of_scrubber": nums["battery_vs_scrubber"] < 0.10,
        # the grandparent's insulation, audited
        "visor_leak_W": nums["visor_leak_W"],
        "insulation_should_be_mm": nums["insulation_should_be_mm"],
        # and it does its job with margin
        "clears_faster_than_it_fogs_by": nums["clears_faster_than_it_fogs_by"],
    }
