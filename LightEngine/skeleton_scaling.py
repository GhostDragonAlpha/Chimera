"""StandingHuman bone scaling lane (Lane S) -- budget-first revision.

Derives the printable bone table under the kernel's 50 000-grain budget.
Uses only the Python standard library and math.

Settled laws encoded (from docs/THE_CATEGORIES.md verdicts):
- Bone is a COMPRESSION-ONLY member; tension lives only in ropes.
- Midshaft is a hollow tube with a 1-grain-thick shell (theLever v5).
- Ends are SOLID over a length equal to the outer diameter, because the
  metaphysis carries joint moments and a shell-only cantilever tears at the
  base (theSpine v1/v2).
- No cantilevers: every transverse moment resolves into a compression pair,
  an arch, or a rope.
- Joints capture the bone END (ball-and-cup / saddle / hinge), never a box
  around the shaft (theSocket v1).

Budget input:
- N_BUDGET = 50 000 grains, derived from LightEngine/output/bench_kernel_report.md
  (feasible 8000-tick print on RTX 4090, steps/sec predicts ~467 s wall-clock).
"""

import math

# ---------------------------------------------------------------------------
# Kernel / print constants
# ---------------------------------------------------------------------------
# d_eq = 0.0484 lu is the cushion equilibrium spacing measured in theCushionLaw
# lattice8eq print.  The grain spacing is uniform and equal to d_eq.
D_EQ_LU = 0.0484

# The smallest hollow tube that can be represented on a simple cubic lattice:
#   outer ring = 3 grains across,
#   wall       = 1 grain,
#   void       = 1 grain.
MIN_HOLLOW_OUTER_GRAINS = 3.0

# The smallest solid compression member that is not rope-class:
#   2 x 2 grains across (the sheet line proved a 1x1 rod is rope-class).
MIN_SOLID_GRAINS = 2.0

# ---------------------------------------------------------------------------
# Budget and anatomy data
# ---------------------------------------------------------------------------
# Kernel budget for a single 8000-tick print on current hardware.
# Source: LightEngine/output/bench_kernel_report.md verdict table.
N_BUDGET = 50000  # derived from benchmark, not chosen

# Human cortical bone longitudinal compressive strength.
# Measured fact: ~170 MPa (Carter & Hayes 1977; Reilly & Burstein 1975).
BONE_COMPRESSIVE_STRENGTH_PA = 170.0e6  # ANATOMY-DATUM

# Standard gravity.
GRAVITY_MPS2 = 9.80665  # ANATOMY-DATUM

# Standard test body plan.
DEFAULT_HEIGHT_M = 1.80
DEFAULT_MASS_KG = 80.0

# Anthropometric segment mass fractions, standing.
HEAD_MASS_FRACTION = 0.07   # ANATOMY-DATUM: head ~7% body mass (Winter 2009).
ARM_MASS_FRACTION = 0.10    # ANATOMY-DATUM: both arms ~10% body mass.
TRUNK_MASS_FRACTION = 0.50  # ANATOMY-DATUM: trunk above pelvis ~50% body mass.

# Rib cage is an arch; it carries the fraction of the trunk mass that is not
# resolved straight down the vertebral column.  30% of body mass is a measured
# upper-bound for the thoracic wall load in quiet standing.
RIB_CAGE_MASS_SHARE = 0.30  # ANATOMY-DATUM

# Per-side arm mass (the arms' mass moves COM even when unloaded).
ARM_MASS_PER_SIDE = ARM_MASS_FRACTION / 2.0  # 0.05

# Segment masses within one arm (Winter 2009, per side):
# upper arm ~5.4% of total body mass -> 0.027 per side?  Wait: both arms 10%,
# so one arm 5%.  Of that, upper arm ~54%, forearm ~32%, hand ~14%.
# We use rounded fractions that sum to the per-arm mass.
UPPER_ARM_MASS_FRACTION = 0.027  # ANATOMY-DATUM
FOREARM_MASS_FRACTION = 0.016    # ANATOMY-DATUM
HAND_MASS_FRACTION = 0.006       # ANATOMY-DATUM
# clavicle + scapula carry the suspended arm mass.
SHOULDER_GIRDLE_MASS_FRACTION = ARM_MASS_PER_SIDE  # 0.05

# Functional load case for the fibula: anatomically ~1/6 of tibial load.
FIBULA_DESIGN_LOAD_FRACTION = 0.10  # derived rounded value

# Functional load case for foot phalanges/forefoot: push-off fraction.
FOREFOOT_DESIGN_LOAD_FRACTION = 0.25  # derived rounded value


# ---------------------------------------------------------------------------
def _vertebral_load_fraction(index, total=24):
    """Cumulative axial load down the C1-L5 stack.

    Derivation: C1 carries only the head.  L5 carries head + arms + trunk.
    Linear interpolation between those two endpoints is the simplest continuous
    load path for a vertical compression stack.
    """
    top = HEAD_MASS_FRACTION
    bottom = HEAD_MASS_FRACTION + ARM_MASS_FRACTION + TRUNK_MASS_FRACTION
    return top + (bottom - top) * index / (total - 1.0)


def _vertebral_length_fraction(index, total=24):
    """Length fraction for an individual vertebra.

    Derivation: total vertebral column (C1-S1) is ~32% of stature.  The C1-L5
    portion is split as cervical 8%, thoracic 16%, lumbar 8% of stature.
    """
    cervical = 7
    thoracic = 12
    if index < cervical:
        return 0.08 / cervical
    if index < cervical + thoracic:
        return 0.16 / thoracic
    return 0.08 / (total - cervical - thoracic)


def _bone_definitions():
    """Return the standing-frame bone inventory.

    Scope derivation:
    - Standing load path: skull -> vertebrae -> sacrum -> pelvis -> femur ->
      patella -> tibia/fibula -> foot arches.
    - Support polygon / COM: foot bones must be present; tarsals and metatarsals
      keep the longitudinal arch, while the toes are grouped as "forefoot" because
      their individual structural role is below the budget and only their combined
      mass shifts the support polygon.
    - Rib cage / sternum: shape the thorax and carry thoracic wall load; kept as
      cage groups.
    - Arm chain: clavicle, scapula, humerus, radius/ulna.  Hands are grouped as
      "hand mass" because individual carpals/metacarpals/phalanges are below the
      budget and only their combined COM matters for standing balance.
    - Mandible and coccyx are OUT: they are not on the standing load path and do
      not affect the support polygon at this budget.
    """
    bones = []

    # Head --------------------------------------------------------------------
    bones.append({
        "name": "skull",
        # ANATOMY-DATUM: skull front-to-back length ~12% of stature.
        "length_fraction": 0.12,
        "load_fraction": HEAD_MASS_FRACTION,
        "prox": "suture",
        "dist": "ball-cup",
        "moment": "head weight resolved through the cervical stack; no cantilever",
    })

    # Vertebrae C1-L5 ---------------------------------------------------------
    for i in range(24):
        if i < 7:
            region = "C"
            num = i + 1
        elif i < 19:
            region = "T"
            num = i - 6
        else:
            region = "L"
            num = i - 18
        name = f"vertebra {region}{num}"
        if i == 0:
            prox = "ball-cup"
            moment = "skull weight -> cervical compression stack"
        else:
            prox = "saddle"
            moment = "moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc"
        if region == "L" and num == 5:
            dist = "saddle"
            moment = "upper-body load -> sacral arch compression"
        else:
            dist = "saddle"
        bones.append({
            "name": name,
            "length_fraction": _vertebral_length_fraction(i),
            "load_fraction": _vertebral_load_fraction(i),
            "prox": prox,
            "dist": dist,
            "moment": moment,
        })

    # Pelvic girdle / spine base ----------------------------------------------
    bones.append({
        "name": "sacrum",
        # ANATOMY-DATUM: sacral length ~6% of stature.
        "length_fraction": 0.06,
        "load_fraction": HEAD_MASS_FRACTION + ARM_MASS_FRACTION + TRUNK_MASS_FRACTION,
        "prox": "saddle",
        "dist": "ball-cup",
        "moment": "lumbar load resolved into the two pelvic columns (the pelvic arch)",
    })

    # Rib cage ----------------------------------------------------------------
    for pair in range(1, 13):
        bones.append({
            "name": f"rib pair {pair}",
            # ANATOMY-DATUM: average rib arc length ~18% of stature.
            "length_fraction": 0.18,
            "load_fraction": RIB_CAGE_MASS_SHARE / 12.0,
            "prox": "hinge",
            "dist": "hinge",
            "moment": "thoracic wall load resolved as an arch between vertebra and sternum",
        })
    bones.append({
        "name": "sternum",
        # ANATOMY-DATUM: sternum length ~9% of stature.
        "length_fraction": 0.09,
        "load_fraction": 0.10,
        "prox": "saddle",
        "dist": "suture",
        "moment": "rib-cage arch compression resolved through the costal cartilages",
    })

    # Shoulder girdle ---------------------------------------------------------
    bones.append({
        "name": "clavicle pair",
        # ANATOMY-DATUM: clavicle length ~5% of stature.
        "length_fraction": 0.05,
        "load_fraction": SHOULDER_GIRDLE_MASS_FRACTION,
        "prox": "saddle",
        "dist": "ball-cup",
        "moment": "arm mass resolved to sternum and scapula; no shaft capture",
    })
    bones.append({
        "name": "scapula pair",
        # ANATOMY-DATUM: scapula height ~9% of stature.
        "length_fraction": 0.09,
        "load_fraction": SHOULDER_GIRDLE_MASS_FRACTION,
        "prox": "saddle",
        "dist": "ball-cup",
        "moment": "arm mass resolved through rotator-cuff ropes to the thorax",
    })

    # Arm ----------------------------------------------------------------------
    bones.append({
        "name": "humerus pair",
        # ANATOMY-DATUM: humerus length ~19% of stature.
        "length_fraction": 0.19,
        "load_fraction": UPPER_ARM_MASS_FRACTION,
        "prox": "ball-cup",
        "dist": "hinge",
        "moment": "elbow load resolved by biceps/triceps ropes across the shoulder",
    })
    bones.append({
        "name": "radius/ulna pair",
        # ANATOMY-DATUM: forearm length ~14% of stature.
        "length_fraction": 0.14,
        "load_fraction": FOREARM_MASS_FRACTION,
        "prox": "hinge",
        "dist": "saddle",
        "moment": "hand mass resolved by forearm flexor/extensor ropes",
    })

    # Hand grouped as one mass body -------------------------------------------
    bones.append({
        "name": "hand mass",
        # ANATOMY-DATUM: hand length ~6% of stature.
        "length_fraction": 0.06,
        "load_fraction": HAND_MASS_FRACTION,
        "prox": "saddle",
        "dist": "hinge",
        "moment": "individual hand bones are below budget; only combined COM is retained",
    })

    # Pelvis ------------------------------------------------------------------
    bones.append({
        "name": "pelvis pair",
        # ANATOMY-DATUM: ilium length ~14% of stature.
        "length_fraction": 0.14,
        "load_fraction": (HEAD_MASS_FRACTION + ARM_MASS_FRACTION + TRUNK_MASS_FRACTION) / 2.0,
        "prox": "saddle",
        "dist": "ball-cup",
        "moment": "spine load resolved into the two femoral columns (the pelvic arch)",
    })

    # Leg ----------------------------------------------------------------------
    bones.append({
        "name": "femur pair",
        # ANATOMY-DATUM: femur length ~24.5% of stature.
        "length_fraction": 0.245,
        "load_fraction": 0.5,
        "prox": "ball-cup",
        "dist": "hinge",
        "moment": "hip-to-knee load resolved by hip abductor/adductor ropes",
    })
    bones.append({
        "name": "patella pair",
        # ANATOMY-DATUM: patella thickness ~3% of stature.
        "length_fraction": 0.03,
        "load_fraction": 0.5,
        "prox": "saddle",
        "dist": "saddle",
        "moment": "sesamoid in quadriceps rope; knee moment resolved by patellar tendon rope",
    })
    bones.append({
        "name": "tibia pair",
        # ANATOMY-DATUM: tibia length ~25% of stature.
        "length_fraction": 0.25,
        "load_fraction": 0.5,
        "prox": "hinge",
        "dist": "hinge",
        "moment": "knee-to-ankle load resolved by Achilles and collateral ropes",
    })
    bones.append({
        "name": "fibula pair",
        # ANATOMY-DATUM: fibula length ~22% of stature.
        "length_fraction": 0.22,
        "load_fraction": FIBULA_DESIGN_LOAD_FRACTION,
        "prox": "hinge",
        "dist": "hinge",
        "moment": "lateral malleolus load resolved by interosseous membrane rope",
    })

    # Foot groups ---------------------------------------------------------------
    bones.append({
        "name": "tarsals group",
        # ANATOMY-DATUM: tarsal block length ~6% of stature.
        "length_fraction": 0.06,
        "load_fraction": 0.5,
        "prox": "hinge",
        "dist": "saddle",
        "moment": "ankle reaction resolved into the plantar arch",
    })
    bones.append({
        "name": "metatarsals group",
        # ANATOMY-DATUM: metatarsal length ~8% of stature.
        "length_fraction": 0.08,
        "load_fraction": 0.5,
        "prox": "saddle",
        "dist": "hinge",
        "moment": "arch load resolved by plantar ligament ropes",
    })
    bones.append({
        "name": "forefoot mass",
        # ANATOMY-DATUM: toe phalanges length ~5% of stature.
        "length_fraction": 0.05,
        "load_fraction": FOREFOOT_DESIGN_LOAD_FRACTION,
        "prox": "hinge",
        "dist": "hinge",
        "moment": "individual toe bones are below budget; only combined push-off COM is retained",
    })

    return bones


# ---------------------------------------------------------------------------
def _rope_lengths_m(height_m):
    """Return physical rope lengths from LightEngine/rope_network.py."""
    # Import here so the scaling module can be imported even if rope_network
    # has side effects; it does not.  Make sure the project root is on sys.path
    # when this file is run as a script from inside LightEngine/.
    import os
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from LightEngine.rope_network import build_rope_network

    ropes = build_rope_network()
    lengths = []
    for r in ropes:
        a = r["anchor_a_point"]
        b = r["anchor_b_point"]
        length_h = math.sqrt(
            (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
        )
        lengths.append(length_h * height_m)
    return lengths


def _support_polygon_size_h():
    """Return (width_h, length_h) of the standing support polygon.

    Derivation from LightEngine/rope_network.py foot contacts:
      - lateral extent: ankle joints at y = +/- 0.060 H
      - A-P extent: calcaneus at x = -0.020 H to metatarsal base at x = +0.070 H
    """
    width_h = 2.0 * 0.060
    length_h = 0.070 - (-0.020)
    return width_h, length_h


# ---------------------------------------------------------------------------
def _bone_rung(A_i, lam):
    """Return the highest fidelity rung for bone area A_i at scale lam.

    Derivation:
      - rung (a): hollow tube, outer diameter >= 3 grains.
        D_lu = A_i/(pi * d_eq * lam^2) + d_eq >= 3 * d_eq
        => lam^2 <= A_i / (2 * pi * d_eq^2)
        => physical grain size g_m = d_eq * lam <= sqrt(A_i / (2*pi))
      - rung (b): solid square rod of derived area, side >= 2 grains.
        a_lu = sqrt(A_i)/lam >= 2 * d_eq
        => lam^2 <= A_i / (4 * d_eq^2)
        => g_m <= sqrt(A_i / 4)
      - rung (c): 2x2 solid rod (overbuilt).
    """
    d = D_EQ_LU
    lam_a = math.sqrt(A_i / (2.0 * math.pi)) / d
    lam_b = math.sqrt(A_i / 4.0) / d
    if lam <= lam_a:
        return "a"
    if lam <= lam_b:
        return "b"
    return "c"


def _bone_grains(A_i, L_m, lam):
    """Return (grain_count, D_m, rung) for one bone at scale lam."""
    d = D_EQ_LU
    g_m = d * lam
    rung = _bone_rung(A_i, lam)

    if rung == "a":
        # Hollow tube: D_m = A/(pi * g_m) + g_m.
        D_m = A_i / (math.pi * g_m) + g_m
        solid_m = D_m
        if L_m <= 2.0 * solid_m:
            vol = (math.pi / 4.0) * D_m * D_m * L_m
        else:
            mid_m = L_m - 2.0 * solid_m
            vol_mid = math.pi * g_m * (D_m - g_m) * mid_m
            vol_ends = 2.0 * (math.pi / 4.0) * D_m * D_m * solid_m
            vol = vol_mid + vol_ends
        grains = math.ceil(vol / (g_m ** 3))
    elif rung == "b":
        # Solid square rod of derived area A_i.
        D_m = 2.0 * math.sqrt(A_i / math.pi)  # equivalent diameter for cup sizing
        vol = A_i * L_m
        grains = math.ceil(vol / (g_m ** 3))
    else:
        # Rung (c): 2x2 solid rod.
        D_m = 2.0 * g_m
        grains = math.ceil(4.0 * L_m / g_m)

    return grains, D_m, rung


def _cup_grains(D_m, lam):
    """Estimate grains for one socket cup wrapping a bone end.

    Derivation: cup is a half-spherical shell of outer radius R = D_m/2 + g_m
    and wall thickness g_m (one grain).  Volume = 2*pi*R^2*g_m.
    Grains = volume / g_m^3 = 2*pi*R^2 / g_m^2.
    """
    g_m = D_EQ_LU * lam
    R = D_m / 2.0 + g_m
    return math.ceil(2.0 * math.pi * R * R / (g_m * g_m))


def _plate_grains(lam, height_m):
    """Ground plate grains covering the support polygon plus one-grain margin."""
    g_m = D_EQ_LU * lam
    width_h, length_h = _support_polygon_size_h()
    margin_m = g_m
    width_m = width_h * height_m + 2.0 * margin_m
    length_m = length_h * height_m + 2.0 * margin_m
    nx = math.ceil(width_m / g_m)
    ny = math.ceil(length_m / g_m)
    return nx * ny


def _total_budget(lam, bones, areas, lengths, rope_lengths_m, height_m):
    """Return (total, bone_grains, cup_grains, rope_grains, plate_grains, rung_counts)."""
    g_m = D_EQ_LU * lam
    bone_grains = 0
    cup_grains = 0
    rung_counts = {"a": 0, "b": 0, "c": 0}

    for A_i, L_m in zip(areas, lengths):
        ng, D_m, rung = _bone_grains(A_i, L_m, lam)
        bone_grains += ng
        cup_grains += 2 * _cup_grains(D_m, lam)
        rung_counts[rung] += 1

    rope_grains = sum(math.ceil(l / g_m) for l in rope_lengths_m)
    plate_grains = _plate_grains(lam, height_m)
    total = bone_grains + cup_grains + rope_grains + plate_grains
    return total, bone_grains, cup_grains, rope_grains, plate_grains, rung_counts


# ---------------------------------------------------------------------------
def _candidate_lams(bones, areas):
    """Return sorted lambda breakpoints where any bone changes rung."""
    points = set()
    for A_i in areas:
        lam_a = math.sqrt(A_i / (2.0 * math.pi)) / D_EQ_LU
        lam_b = math.sqrt(A_i / 4.0) / D_EQ_LU
        points.add(lam_a)
        points.add(lam_b)
    points.add(max(points) * 1.0e-6)  # avoid zero
    return sorted(points)


def derive_budget_scale(bones, mass_kg, height_m, budget):
    """Find the coarsest scale that fits the budget with maximum fidelity.

    Strategy:
      1. Build all rung-transition lambdas.
      2. Evaluate total N at each candidate lambda.
      3. The first lambda with total N <= budget has the highest structural
         fidelity (most rung-a / rung-b bones) that the budget allows.
      4. Binary-search near that breakpoint to land just under budget.

    Returns (lam, total, breakdown, rung_counts, candidate_log).
    """
    sigma = BONE_COMPRESSIVE_STRENGTH_PA
    g = GRAVITY_MPS2
    areas = [b["load_fraction"] * mass_kg * g / sigma for b in bones]
    lengths = [b["length_fraction"] * height_m for b in bones]
    rope_lengths = _rope_lengths_m(height_m)

    candidates = _candidate_lams(bones, areas)
    candidate_log = []
    for lam in candidates:
        total, bg, cg, rg, pg, rc = _total_budget(
            lam, bones, areas, lengths, rope_lengths, height_m
        )
        candidate_log.append((lam, total, bg, cg, rg, pg, rc))

    # Find the first candidate that fits.
    chosen_lam = None
    for lam, total, bg, cg, rg, pg, rc in candidate_log:
        if total <= budget:
            chosen_lam = lam
            break

    if chosen_lam is None:
        # Even the coarsest transition point does not fit; binary search upward.
        lo = candidates[-1]
        hi = lo * 100.0
        for _ in range(80):
            mid = (lo + hi) / 2.0
            total, *_ = _total_budget(mid, bones, areas, lengths, rope_lengths, height_m)
            if total <= budget:
                hi = mid
            else:
                lo = mid
        chosen_lam = hi
    else:
        # Binary search between the previous breakpoint and chosen_lam to land
        # as close to the budget as possible without exceeding it.
        idx = candidates.index(chosen_lam)
        if idx == 0:
            lo = chosen_lam * 0.1
        else:
            lo = candidates[idx - 1]
        hi = chosen_lam
        for _ in range(60):
            mid = (lo + hi) / 2.0
            total, *_ = _total_budget(mid, bones, areas, lengths, rope_lengths, height_m)
            if total <= budget:
                hi = mid
            else:
                lo = mid
        chosen_lam = hi

    total, bg, cg, rg, pg, rc = _total_budget(
        chosen_lam, bones, areas, lengths, rope_lengths, height_m
    )
    return chosen_lam, total, (bg, cg, rg, pg), rc, candidate_log, areas, lengths, rope_lengths


# ---------------------------------------------------------------------------
def scale_skeleton(height_m=DEFAULT_HEIGHT_M, mass_kg=DEFAULT_MASS_KG):
    """Return the budget-resolved bone table.

    Returns a tuple:
        table, lam, total, breakdown, rung_counts, candidate_log
    where table is a list of dictionaries, one per bone group.
    """
    bones = _bone_definitions()
    lam, total, breakdown, rc, cand_log, areas, lengths, rope_lengths = derive_budget_scale(
        bones, mass_kg, height_m, N_BUDGET
    )

    table = []
    for b, A_i, L_m in zip(bones, areas, lengths):
        grains, D_m, rung = _bone_grains(A_i, L_m, lam)
        g_m = D_EQ_LU * lam
        D_lu = D_m / g_m * D_EQ_LU
        length_lu = L_m / g_m * D_EQ_LU

        if rung == "a":
            shell_lu = D_EQ_LU
            solid_end_lu = D_lu
        elif rung == "b":
            shell_lu = 0.0
            solid_end_lu = length_lu
        else:
            shell_lu = 0.0
            solid_end_lu = length_lu

        design_load_kg = b["load_fraction"] * mass_kg
        table.append({
            "name": b["name"],
            "length_m": L_m,
            "length_lu": length_lu,
            "outer_diameter_m": D_m,
            "outer_diameter_lu": D_lu,
            "shell_thickness_lu": shell_lu,
            "solid_end_lu": solid_end_lu,
            "design_load_kg": design_load_kg,
            "grain_count": grains,
            "rung": rung,
            "prox": b["prox"],
            "dist": b["dist"],
            "moment": b["moment"],
        })

    return table, lam, total, breakdown, rc, cand_log


# ---------------------------------------------------------------------------
def render_markdown(table, lam, total, breakdown, rung_counts, candidate_log,
                    height_m, mass_kg):
    """Return a human-readable markdown table of the budget-resolved scaling."""
    lines = []
    lines.append("# StandingHuman bone scaling table (budget-first)")
    lines.append("")
    lines.append(f"Body plan: height = {height_m:.2f} m, mass = {mass_kg:.1f} kg")
    lines.append(f"Kernel budget N_BUDGET = {N_BUDGET:,} grains")
    lines.append(f"Budget source: LightEngine/output/bench_kernel_report.md")
    lines.append(f"d_eq (grain spacing) = {D_EQ_LU} lu")
    lines.append(f"Bone compressive strength = {BONE_COMPRESSIVE_STRENGTH_PA:.3e} Pa (ANATOMY-DATUM)")
    lines.append("")
    g_m = lam * D_EQ_LU
    lines.append(f"**Resolved scale:** {lam:.6e} m/lu  (1 m = {1.0/lam:.2f} lu)")
    lines.append(f"**Physical grain spacing:** {g_m:.6e} m")
    lines.append("")
    lines.append("## Scale derivation")
    lines.append("")
    lines.append("The iteration is over the lu-to-meter scale `lambda`.  For each candidate")
    lines.append("scale, every bone is assigned to the highest fidelity rung it can still resolve:")
    lines.append("")
    lines.append("- rung (a): hollow tube + solid ends, requires outer diameter >= 3 grains.")
    lines.append("- rung (b): solid rod of the derived compression area, minimum 2x2 grains.")
    lines.append("- rung (c): 2x2 solid rod; structural area is overbuilt.")
    lines.append("")
    lines.append("The chosen scale is the coarsest one that brings the total (bones + cups + ropes + plate)")
    lines.append("under the kernel budget while keeping every bone on its highest possible rung.")
    lines.append("")
    lines.append("## Candidate scale scan")
    lines.append("")
    lines.append("| lambda (m/lu) | grain (m) | total | bones | cups | ropes | plate | rungs (a/b/c) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    # Drop unphysical tiny scales that overflow the estimate; keep the rest.
    displayed = [(lam_c, tot, bg, cg, rg, pg, rc) for (lam_c, tot, bg, cg, rg, pg, rc) in candidate_log if tot <= 1e12]
    for lam_c, tot, bg, cg, rg, pg, rc in displayed:
        rc_str = f"{rc['a']}/{rc['b']}/{rc['c']}"
        lines.append(
            f"| {lam_c:.4e} | {lam_c * D_EQ_LU:.4e} | {tot:,} | "
            f"{bg:,} | {cg:,} | {rg:,} | {pg:,} | {rc_str} |"
        )
    # Append the final resolved candidate.
    rc_final = rung_counts
    lines.append(
        f"| **{lam:.4e}** | **{lam * D_EQ_LU:.4e}** | **{total:,}** | "
        f"**{breakdown[0]:,}** | **{breakdown[1]:,}** | **{breakdown[2]:,}** | **{breakdown[3]:,}** | "
        f"**{rc_final['a']}/{rc_final['b']}/{rc_final['c']}** |"
    )
    lines.append("")
    lines.append("## Final budget breakdown")
    lines.append("")
    bg, cg, rg, pg = breakdown
    lines.append(f"- Bones: {bg:,} grains")
    lines.append(f"- Joint cups: {cg:,} grains")
    lines.append(f"- Ropes (43 from rope_network.py): {rg:,} grains")
    lines.append(f"- Ground plate: {pg:,} grains")
    lines.append(f"- **Total: {total:,} grains**")
    lines.append("")
    lines.append(f"Rung counts: (a) = {rung_counts['a']}, (b) = {rung_counts['b']}, (c) = {rung_counts['c']}")
    lines.append("")
    lines.append("## Bone table")
    lines.append("")
    lines.append("| name | length (m) | length (lu) | D_out (m) | D_out (lu) | shell (lu) | solid end (lu) | design load (kg) | grains | rung | prox | dist | moment resolution |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in table:
        prox = row["prox"]
        dist = row["dist"]
        shell = f"{row['shell_thickness_lu']:.2f}" if row["rung"] == "a" else "solid"
        lines.append(
            f"| {row['name']} | "
            f"{row['length_m']:.4f} | {row['length_lu']:.3f} | "
            f"{row['outer_diameter_m']:.6f} | {row['outer_diameter_lu']:.3f} | "
            f"{shell} | {row['solid_end_lu']:.3f} | "
            f"{row['design_load_kg']:.2f} | {row['grain_count']:,} | "
            f"{row['rung']} | {prox} | {dist} | {row['moment']} |"
        )
    lines.append("")
    return "\n".join(lines)


def summary(table, lam, total, breakdown, rung_counts):
    """Return a short text summary for console output."""
    bg, cg, rg, pg = breakdown
    lines = []
    lines.append(f"Resolved scale = {lam:.6e} m/lu  (1 m = {1.0/lam:.2f} lu)")
    lines.append(f"Physical grain spacing = {lam * D_EQ_LU:.6e} m")
    lines.append(f"Total grains = {total:,} (budget {N_BUDGET:,})")
    lines.append(f"  bones = {bg:,}")
    lines.append(f"  joint cups = {cg:,}")
    lines.append(f"  ropes = {rg:,}")
    lines.append(f"  plate = {pg:,}")
    lines.append(f"Rung counts: (a) hollow = {rung_counts['a']}, (b) solid-area = {rung_counts['b']}, (c) 2x2 = {rung_counts['c']}")
    rung_b = [r["name"] for r in table if r["rung"] == "b"]
    rung_c = [r["name"] for r in table if r["rung"] == "c"]
    if rung_b:
        lines.append("Rung (b) groups: " + ", ".join(rung_b))
    if rung_c:
        lines.append("Rung (c) groups: " + ", ".join(rung_c))
    return "\n".join(lines)


def main():
    table, lam, total, breakdown, rc, cand_log = scale_skeleton(
        DEFAULT_HEIGHT_M, DEFAULT_MASS_KG
    )
    md = render_markdown(
        table, lam, total, breakdown, rc, cand_log, DEFAULT_HEIGHT_M, DEFAULT_MASS_KG
    )
    path = "docs/scratch/skeleton_scaling_table.md"
    with open(path, "w", encoding="ascii") as f:
        f.write(md)
    print(summary(table, lam, total, breakdown, rc))
    print(f"\nWrote table to {path}")


if __name__ == "__main__":
    main()
