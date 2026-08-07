"""StandingHuman bone scaling lane (Lane S).

Derives every bone group's length, hollow-tube cross-section, and grain budget
from ONE body plan, using only the Python standard library and math.

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

Every externally fixed number is marked ANATOMY-DATUM; all other numbers are
derived from those data and the compression law.
"""

import math

# ---------------------------------------------------------------------------
# Kernel / print constants
# ---------------------------------------------------------------------------
# d_eq = 0.0484 lu is the cushion equilibrium spacing measured in theCushionLaw
# lattice8eq print.  The printer lattice spacing is 0.05 lu.
D_EQ_LU = 0.0484
LATTICE_SPACING_LU = 0.05

# A one-grain shell means the wall thickness equals one lattice spacing.
SHELL_GRAINS = 1.0

# The smallest hollow tube that can be represented on a simple cubic lattice:
#   outer ring = 3 grains across,
#   wall       = 1 grain,
#   void       = 1 grain.
# Any smaller cross-section cannot be both hollow and 1-grain-thick.
MIN_HOLLOW_OUTER_GRAINS = 3.0

# ---------------------------------------------------------------------------
# ANATOMY-DATA and environmental constants
# ---------------------------------------------------------------------------
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

# Functional load case for the upper limb: a two-handed static hang/pull-up.
# The body is supported by two arms, so each arm side carries 0.5 * body weight.
ARM_DESIGN_LOAD_FRACTION = 0.5

# Functional load case for the mandible: chewing/bite load.  A working value
# of 25% body weight is used as a conservative masticatory design load; the
# maximum voluntary bite force is much higher, but sustained chewing lives here.
MANDIBLE_DESIGN_LOAD_FRACTION = 0.25

# Functional load case for the coccyx: seated contact load.
COCCYX_DESIGN_LOAD_FRACTION = 0.10

# Functional load case for the fibula: anatomically it carries ~1/6 of tibial
# load; 0.1 * body weight is a safe rounded design value.
FIBULA_DESIGN_LOAD_FRACTION = 0.10

# Functional load case for foot phalanges: toe-off during push-off carries a
# fraction of the foot's ground reaction; 0.25 * body weight is a rounded value.
FOOT_PHALANGES_DESIGN_LOAD_FRACTION = 0.25


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
    # Cervical C1-C7: 8% total -> ~1.143% each
    # Thoracic T1-T12: 16% total -> ~1.333% each
    # Lumbar L1-L5: 8% total -> 1.6% each
    cervical = 7
    thoracic = 12
    if index < cervical:
        return 0.08 / cervical
    if index < cervical + thoracic:
        return 0.16 / thoracic
    return 0.08 / (total - cervical - thoracic)


def _rib_load_fraction(pair_index, total_pairs=12):
    """Share of the rib-cage arch load carried by one rib pair.

    Derivation: the rib cage is treated as a distributed arch carrying
    RIB_CAGE_MASS_SHARE of body weight; equal share per pair.
    """
    return RIB_CAGE_MASS_SHARE / total_pairs


def _bone_definitions():
    """Return the full anatomical inventory as a list of bone dictionaries."""
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
    bones.append({
        "name": "mandible",
        # ANATOMY-DATUM: mandible length ~8% of stature.
        "length_fraction": 0.08,
        "load_fraction": MANDIBLE_DESIGN_LOAD_FRACTION,
        "prox": "saddle",
        "dist": "hinge",
        "moment": "bite force resolved by paired condylar compression + masseter/temporalis ropes",
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
            prox = "ball-cup"  # atlanto-occipital
            moment = "skull weight -> cervical compression stack"
        else:
            prox = "saddle"
            moment = "moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc"
        if region == "L" and num == 5:
            dist = "saddle"  # L5-S1
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
    bones.append({
        "name": "coccyx",
        # ANATOMY-DATUM: coccyx length ~3% of stature.
        "length_fraction": 0.03,
        "load_fraction": COCCYX_DESIGN_LOAD_FRACTION,
        "prox": "suture",
        "dist": "free",
        "moment": "seated contact load resolved through the sacrum; no cantilever outboard",
    })

    # Rib cage ----------------------------------------------------------------
    for pair in range(1, 13):
        bones.append({
            "name": f"rib pair {pair}",
            # ANATOMY-DATUM: average rib arc length ~18% of stature.
            "length_fraction": 0.18,
            "load_fraction": _rib_load_fraction(pair - 1),
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
        "load_fraction": ARM_DESIGN_LOAD_FRACTION,
        "prox": "saddle",
        "dist": "ball-cup",
        "moment": "suspension load resolved to sternum and scapula; no shaft capture",
    })
    bones.append({
        "name": "scapula pair",
        # ANATOMY-DATUM: scapula height ~9% of stature.
        "length_fraction": 0.09,
        "load_fraction": ARM_DESIGN_LOAD_FRACTION,
        "prox": "saddle",
        "dist": "ball-cup",
        "moment": "arm load resolved through rotator-cuff ropes to the thorax",
    })

    # Arm ----------------------------------------------------------------------
    bones.append({
        "name": "humerus pair",
        # ANATOMY-DATUM: humerus length ~19% of stature.
        "length_fraction": 0.19,
        "load_fraction": ARM_DESIGN_LOAD_FRACTION,
        "prox": "ball-cup",
        "dist": "hinge",
        "moment": "elbow load resolved by biceps/triceps ropes across the shoulder",
    })
    bones.append({
        "name": "radius/ulna pair",
        # ANATOMY-DATUM: forearm length ~14% of stature.
        "length_fraction": 0.14,
        "load_fraction": ARM_DESIGN_LOAD_FRACTION,
        "prox": "hinge",
        "dist": "saddle",
        "moment": "hand load resolved by forearm flexor/extensor ropes",
    })

    # Hand groups -------------------------------------------------------------
    bones.append({
        "name": "carpals group",
        # ANATOMY-DATUM: carpal block depth ~3% of stature.
        "length_fraction": 0.03,
        "load_fraction": ARM_DESIGN_LOAD_FRACTION,
        "prox": "saddle",
        "dist": "saddle",
        "moment": "wrist load resolved through ligament ropes to radius/ulna",
    })
    bones.append({
        "name": "metacarpals group",
        # ANATOMY-DATUM: metacarpal length ~7% of stature.
        "length_fraction": 0.07,
        "load_fraction": ARM_DESIGN_LOAD_FRACTION,
        "prox": "saddle",
        "dist": "hinge",
        "moment": "grip load resolved by digital flexor ropes",
    })
    bones.append({
        "name": "hand phalanges group",
        # ANATOMY-DATUM: phalanges length ~6% of stature.
        "length_fraction": 0.06,
        "load_fraction": ARM_DESIGN_LOAD_FRACTION,
        "prox": "hinge",
        "dist": "hinge",
        "moment": "grip contact load resolved by extensor/flexor ropes",
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

    # Foot groups -------------------------------------------------------------
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
        "name": "foot phalanges group",
        # ANATOMY-DATUM: toe phalanges length ~5% of stature.
        "length_fraction": 0.05,
        "load_fraction": FOOT_PHALANGES_DESIGN_LOAD_FRACTION,
        "prox": "hinge",
        "dist": "hinge",
        "moment": "push-off load resolved by digital flexor/extensor ropes",
    })

    return bones


# ---------------------------------------------------------------------------
def _derive_scale(bones, mass_kg):
    """Derive the lu-to-meter ratio from the smallest structurally required shell.

    Compression law for a hollow tube:
        required area A = F / sigma
        A = pi * t * (D - t)              (circular tube, wall thickness t)

    We print with the thinnest possible wall: one lattice grain,
    t = LATTICE_SPACING_LU * lambda.

    The smallest bone (minimum A) sets the scale.  It must be representable as
    the smallest hollow tube on a cubic lattice: outer diameter = 3 grains
    (1-grain wall + 1-grain void + 1-grain wall).  Therefore

        D_min = 3 * s * lambda
              = A_min / (pi * s * lambda) + s * lambda

    Solving for lambda (m/lu):

        lambda = sqrt( A_min / (2 * pi * s^2) )

    where s = LATTICE_SPACING_LU and A_min is the minimum required area.
    """
    sigma = BONE_COMPRESSIVE_STRENGTH_PA
    g = GRAVITY_MPS2
    s = LATTICE_SPACING_LU

    areas = []
    for b in bones:
        load_kg = b["load_fraction"] * mass_kg
        force_n = load_kg * g
        area_m2 = force_n / sigma
        areas.append(area_m2)

    a_min = min(areas)
    lu_to_m = math.sqrt(a_min / (2.0 * math.pi * s * s))
    return lu_to_m, areas


def _grain_count(D_lu, L_lu, s_len_lu, s):
    """Return (grain_count, shell_rule_failed).

    Derivation:
      - Midshaft is a hollow tube of length (L - 2*s_len).
        Volume = pi/4 * (D_out^2 - D_in^2) * L_mid.
        With D_in = D_out - 2*s and volume per grain = s^3,
        grains_mid = pi * (D_out - s) * L_mid / s^2.
      - Each solid end is a solid cylinder of diameter D_out and length s_len.
        grains_ends = 2 * (pi/4 * D_out^2 * s_len) / s^3
                    = (pi/2) * D_out^2 * s_len / s^3.

    Failure modes:
      - D_out < 3*s: a 1-grain wall with a void cannot be formed.
      - L_lu <= 2*s_len: there is no hollow midshaft; the bone must be solid.
    """
    min_outer = MIN_HOLLOW_OUTER_GRAINS * s
    if D_lu < min_outer:
        grains = math.ceil((math.pi / 4.0) * D_lu * D_lu * L_lu / (s * s * s))
        return grains, True

    s_len = min(s_len_lu, L_lu / 2.0)
    mid_lu = max(0.0, L_lu - 2.0 * s_len)
    if mid_lu <= 0.0:
        grains = math.ceil((math.pi / 4.0) * D_lu * D_lu * L_lu / (s * s * s))
        return grains, True

    grains_mid = math.ceil(math.pi * (D_lu - s) * mid_lu / (s * s))
    grains_ends = math.ceil((math.pi / 2.0) * D_lu * D_lu * s_len / (s * s * s))
    return grains_mid + grains_ends, False


def scale_skeleton(height_m=DEFAULT_HEIGHT_M, mass_kg=DEFAULT_MASS_KG):
    """Return the complete bone table for the given body plan.

    Returns a list of dictionaries, one per bone group, with keys:
        name, length_m, length_lu, outer_diameter_m, outer_diameter_lu,
        shell_thickness_m, shell_thickness_lu, solid_end_m, solid_end_lu,
        design_load_kg, grain_count, shell_fail,
        prox, dist, moment.
    """
    bones = _bone_definitions()
    lu_to_m, areas = _derive_scale(bones, mass_kg)
    s = LATTICE_SPACING_LU
    sigma = BONE_COMPRESSIVE_STRENGTH_PA
    g = GRAVITY_MPS2
    a_min = min(areas)

    table = []
    for b, area in zip(bones, areas):
        length_m = b["length_fraction"] * height_m
        length_lu = length_m / lu_to_m

        # Outer diameter from compression law (see _derive_scale).
        D_lu = s * (1.0 + 2.0 * area / a_min)
        D_m = D_lu * lu_to_m

        # 1-grain shell.
        shell_lu = s
        shell_m = s * lu_to_m

        # Solid end length = outer diameter; the cup/socket that captures the
        # end must be at least one diameter deep (derived from socket capture).
        solid_end_lu = D_lu
        solid_end_m = D_m

        design_load_kg = b["load_fraction"] * mass_kg
        grains, fail = _grain_count(D_lu, length_lu, solid_end_lu, s)

        table.append({
            "name": b["name"],
            "length_m": length_m,
            "length_lu": length_lu,
            "outer_diameter_m": D_m,
            "outer_diameter_lu": D_lu,
            "shell_thickness_m": shell_m,
            "shell_thickness_lu": shell_lu,
            "solid_end_m": solid_end_m,
            "solid_end_lu": solid_end_lu,
            "design_load_kg": design_load_kg,
            "grain_count": grains,
            "shell_fail": fail,
            "prox": b["prox"],
            "dist": b["dist"],
            "moment": b["moment"],
            "load_fraction": b["load_fraction"],
            "length_fraction": b["length_fraction"],
        })
    return table, lu_to_m


def render_markdown(table, lu_to_m, height_m, mass_kg):
    """Return a human-readable markdown table of the bone scaling results."""
    lines = []
    lines.append("# StandingHuman bone scaling table")
    lines.append("")
    lines.append(f"Body plan: height = {height_m:.2f} m, mass = {mass_kg:.1f} kg")
    lines.append(f"Lattice spacing = {LATTICE_SPACING_LU} lu")
    lines.append(f"d_eq = {D_EQ_LU} lu")
    lines.append(f"Bone compressive strength = {BONE_COMPRESSIVE_STRENGTH_PA:.3e} Pa (ANATOMY-DATUM)")
    lines.append(f"Lu-to-meter ratio = {lu_to_m:.6e} m/lu  (1 m = {1.0/lu_to_m:.2f} lu)")
    lines.append("")
    lines.append("Scale derivation:")
    lines.append("- Required area per bone A = (load_fraction * mass * g) / sigma.")
    lines.append("- Midshaft is a hollow tube with wall thickness = 1 grain = lattice spacing.")
    lines.append("- The smallest required area A_min sets the scale so that the smallest")
    lines.append("  hollow tube is exactly 3 grains across (1-grain wall + 1-grain void + 1-grain wall).")
    lines.append("")
    lines.append("The diameters below are structural minima from compressive strength; real bones")
    lines.append("are larger because of buckling margins, safety factors, and muscle attachment.")
    lines.append("")
    lines.append("| name | length (m) | length (lu) | D_out (m) | D_out (lu) | shell (lu) | solid end (lu) | design load (kg) | grains | prox | dist | moment resolution |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in table:
        prox = row["prox"]
        dist = row["dist"]
        if row["shell_fail"]:
            note = " [SHELL-FAIL]"
        else:
            note = ""
        lines.append(
            f"| {row['name']}{note} | "
            f"{row['length_m']:.4f} | {row['length_lu']:.3f} | "
            f"{row['outer_diameter_m']:.6f} | {row['outer_diameter_lu']:.3f} | "
            f"{row['shell_thickness_lu']:.2f} | {row['solid_end_lu']:.3f} | "
            f"{row['design_load_kg']:.2f} | {row['grain_count']:,} | "
            f"{prox} | {dist} | {row['moment']} |"
        )
    lines.append("")
    total = sum(r["grain_count"] for r in table)
    lines.append(f"**Total grain count:** {total:,}")
    lines.append("")
    top5 = sorted(table, key=lambda r: r["grain_count"], reverse=True)[:5]
    lines.append("**Top 5 grain consumers:**")
    for r in top5:
        lines.append(f"- {r['name']}: {r['grain_count']:,} grains")
    lines.append("")
    failures = [r["name"] for r in table if r["shell_fail"]]
    if failures:
        lines.append("**1-grain-shell rule failures at this scale:**")
        for name in failures:
            lines.append(f"- {name}")
    else:
        lines.append("**No 1-grain-shell rule failures at the derived scale.**")
    lines.append("")
    return "\n".join(lines)


def summary(table, lu_to_m):
    """Return a short text summary for console output."""
    total = sum(r["grain_count"] for r in table)
    top5 = sorted(table, key=lambda r: r["grain_count"], reverse=True)[:5]
    failures = [r["name"] for r in table if r["shell_fail"]]
    lines = []
    lines.append(f"lu-to-meter ratio = {lu_to_m:.6e} m/lu")
    lines.append(f"1 lattice spacing = {LATTICE_SPACING_LU * lu_to_m:.6e} m")
    lines.append(f"Total grain count = {total:,}")
    lines.append("")
    lines.append("Top 5 grain consumers:")
    for r in top5:
        lines.append(f"  {r['name']}: {r['grain_count']:,} grains")
    lines.append("")
    if failures:
        lines.append("1-grain-shell rule failures:")
        for name in failures:
            lines.append(f"  {name}")
    else:
        lines.append("No 1-grain-shell rule failures at the derived scale.")
    return "\n".join(lines)


def main():
    table, lu_to_m = scale_skeleton(DEFAULT_HEIGHT_M, DEFAULT_MASS_KG)
    md = render_markdown(table, lu_to_m, DEFAULT_HEIGHT_M, DEFAULT_MASS_KG)
    path = "docs/scratch/skeleton_scaling_table.md"
    with open(path, "w", encoding="ascii") as f:
        f.write(md)
    print(summary(table, lu_to_m))
    print(f"\nWrote table to {path}")


if __name__ == "__main__":
    main()
