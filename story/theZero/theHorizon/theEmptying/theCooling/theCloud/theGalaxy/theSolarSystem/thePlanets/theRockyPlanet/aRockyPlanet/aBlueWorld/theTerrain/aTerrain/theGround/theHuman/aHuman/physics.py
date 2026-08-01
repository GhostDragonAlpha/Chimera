"""aHuman -- the body theHuman's law says this planet requires: a person wearing what they must.

THE EDGE. The parent settled whether a body can live here and the answer was no, not unaided: at
0.52 bar this air would have to be 30.8% oxygen -- half again richer than Earth's -- and nothing in
the chain derives a composition. So the person carries their own air. The parent also settled that
0.52 bar is far above the Armstrong limit, which decides the KIND of suit: no pressure vessel, no
ballooned shell, just a sealed garment and a rebreather. That is why this figure can walk normally
where a Mars EVA suit would fight every step.

WHAT THIS MEMBRANE ADDS, and it is the only thing left to add: the suit's SHAPE. Its mass came from
metabolism upstream; its BULK comes from a thermal balance solved here, because how thick a coat has
to be is a fact about the temperature outside and the heat a body makes inside. That thickness is
then literally the radius added to every limb -- so the astronaut's silhouette is a measurement, and
if this world warmed up the suit would get thinner in the render without anyone redrawing it.

AND ITS MATERIALS ARE MEASURED TOO (F1, 2026-07-31): suit, visor and hardware albedos are sampled
from the hull material genomes (real scans, Construction/space_materials.py) instead of typed
literals; the head the helmet was derived around is now drawn inside it, wearing the parent's
measured skin (melanin filter over a blood-bearing dermis, story/skin_optics.py), showing through
the visor by the one declared number left -- VISOR_TRANSMIT, the operator's dial.

Contained in theHuman. It contains nothing yet: a helmet and a rebreather are the next chapters.
"""
from __future__ import annotations

import math

import numpy as np

# ── THERMAL PHYSIOLOGY. Measurements of a human and of fibrous insulation; they read the same in
# any story, which is what makes them legal literals rather than borrowed numbers.
Q_REST_W = 105.0            # metabolic heat, quiet standing (a person is a 100 W heater)
Q_WALK_W = 350.0            # ... and walking, which is why you overheat in a coat
K_INSUL_W_MK = 0.040        # fibrous/aerogel batting, still air
T_SKIN_C = 33.0             # comfortable mean skin temperature, not core
HELMET_CLEAR_M = 0.055      # visor standoff: room to turn the head and for gas to sweep the faceplate
HELMET_Z = 0.885            # neck top, in stature units -- emit() and derive() must agree on this
VISOR_HALF_ANGLE = 1.05     # radians of the helmet given over to the faceplate (~120 deg of view)
# THE ONE UNMEASURED NUMBER IN THE MATERIALS, DECLARED: how much light the visor passes. It is
# dark because its job is rejecting light, but a face the story derived lives behind it, and how
# visible that face is ends at a HUMAN terminal -- the operator rules with the render in hand.
# Everything else about the materials is measured (hull genomes / skin optics).
VISOR_TRANSMIT = 0.28

# Dempster's segment fractions of stature -- the same measured anthropometry the parent used.
THIGH_FRAC, SHANK_FRAC = 0.245, 0.246
UPPER_ARM_FRAC, FOREARM_FRAC = 0.186, 0.146
FOOT_LEN_FRAC = 0.152
# Bare limb radii as fractions of stature, from the same cadaver anthropometry.
R_THIGH, R_SHANK, R_ARM, R_FOREARM, R_TRUNK = 0.046, 0.032, 0.028, 0.023, 0.088

FREE = {
    # THE ONE FREE NUMBER HERE. How hard the person is working sets how much heat they must shed,
    # and therefore how thick the suit can be before it cooks them. Resting is the demanding case
    # for INSULATION (least heat to spare); walking is the demanding case for cooling.
    "exertion": {"lo": 0.0, "hi": 1.0, "default": 0.25,
                 "label": "how hard they are working", "unit": "rest -> walking"},
}


def insulation_thickness(T_air_C, Q_W, A_m2):
    """HOW THICK THE SUIT HAS TO BE, from conduction alone: d = k A dT / Q.

    A body is a heater of known power inside a bag of known conductivity, and the outside air is at a
    temperature the planet derived. For the coat to hold skin at comfort while shedding exactly the
    heat the person makes, there is only one thickness. Below it they cool; above it they cook.

    THIS IS WHY THE ASTRONAUT LOOKS BULKY, and the bulk is not a style choice -- warm the planet and
    the number shrinks. On a 9 C world at rest it comes out near a centimetre."""
    dT = max(T_SKIN_C - float(T_air_C), 0.0)
    if Q_W <= 0.0:
        return 0.0
    return K_INSUL_W_MK * float(A_m2) * dT / float(Q_W)


# THE MANUFACTURED SCANS -- the scans whose vocabulary a pressure garment is made of
# (painted metal, glass, rubber, fabric). Ground/wall/vegetation genomes are not a suit.
MANUFACTURED_SCANS = ("truck", "train", "bicycle", "nike", "plush")


def _pick_materials(lib):
    """WHICH MEASURED GENOME IS WHICH PART, by the same reasons the typed albedos claimed:
    the suit is a thermal instrument (brightest opaque genome), the visor rejects light (darkest),
    and hardware is what is neither (nearest mid-grey). 2026-07-31: now picked from the JOINT
    element codebook (story/data/material_genomes.json -- ONE k-means over 16 real scans,
    Construction/material_elements.py) restricted to the genomes the MANUFACTURED scans carry,
    so re-running the extraction re-picks honestly. The operator ratifies the mapping --
    taste terminates with him."""
    from matter import pick_genomes, genome_lum
    cands = pick_genomes(MANUFACTURED_SCANS)
    lum = {g["id"]: genome_lum(g) for g in cands}
    suit = max(lum, key=lum.get)
    visor = min(lum, key=lum.get)
    hardware = min((i for i in lum if i not in (suit, visor)), key=lambda i: abs(lum[i] - 0.5))
    return {"suit": suit, "visor": visor, "hardware": hardware}, lum


def leg_local(parent):
    """The hip height as a fraction of stature -- read from the parent, not restated."""
    return float(parent["leg_length_m"]) / float(parent["height_m"])


def derive(parent, free):
    if parent is None or "suit_class" not in parent:
        raise ValueError("aHuman requires theHuman as its parent")
    free = free or {}
    x = float(free.get("exertion", FREE["exertion"]["default"]))

    h = float(parent["height_m"])
    T_air_C = float(parent["T_surface"]) - 273.15
    # the heat this person is making, between the two measured endpoints
    Q = Q_REST_W + x * (Q_WALK_W - Q_REST_W)
    # THE BODY'S SURFACE AREA, READ FROM THE PARENT (DuBois on the ANSUR median: 2.01 m2) --
    # it used to be typed here as 1.83, the 70 kg "standard man", and the suit was sized on him.
    skin_area = float(parent["skin_area_m2"])
    d_insul = insulation_thickness(T_air_C, Q, skin_area)

    # THE SUIT'S SHAPE, all of it downstream of that one thickness
    r_thigh = R_THIGH * h + d_insul
    r_shank = R_SHANK * h + d_insul
    r_arm = R_ARM * h + d_insul
    r_forearm = R_FOREARM * h + d_insul
    r_trunk = R_TRUNK * h + d_insul
    # the helmet is the head plus the insulation plus room to see out of
    r_head_bare = 0.0665 * h
    r_helmet = r_head_bare + d_insul + HELMET_CLEAR_M

    # how much bigger the suit makes the person -- the number the render is judged against
    bulk_frac = (r_trunk / (R_TRUNK * h)) - 1.0

    # ── A THICK SUIT FORCES A WIDER STANCE, and it is a clearance calculation, not a style ──────
    # The bare skeleton hangs its hips 5.5% of stature apart and its shoulders at 8.5%. Add 12 mm of
    # insulation to every limb and those spacings STOP FITTING: two 14 cm thighs whose centres are
    # 11 cm apart are one column, and a shoulder at 15 cm inside a 17 cm trunk radius puts the arms
    # INSIDE the chest. Both were visible in the render as a fused stalk with a bar across it.
    #
    # So the separations are derived from the suit's own radii: tangent, plus a small gap so the
    # tubes do not scrape. This is why a suited person stands bow-legged and holds their arms out --
    # it is the same reason, and it is measurable rather than mimicked.
    hip_half = max(0.055 * h, r_thigh * 1.08)
    shoulder_half = max(0.085 * h, r_trunk + r_arm * 0.92)

    # ── AND THE LEGS HAVE TO SPLAY, because the hip cannot move ────────────────────────────────
    # A human hip puts its joints 0.055 of stature apart -- 9.8 cm here. A suited THIGH is 9.4 cm in
    # RADIUS. So the two thighs are 18.8 cm of meat trying to fit into a 19.6 cm gap: they clear by
    # eight millimetres, and the hip is bone, so widening it is not on offer.
    #
    # A body cannot widen its pelvis, so it angles the femur outward instead -- and that is not a
    # mannerism to be imitated, it is the only remaining degree of freedom. The angle follows from
    # asking for a real gap at the knee (one thigh radius) and seeing what tilt delivers it over the
    # thigh's length. It comes out near 5 degrees, and it is why every photograph of a suited person
    # walking shows them bow-legged.
    knee_half = r_thigh * 1.5
    splay_rad = math.asin(min(0.95, max(0.0, (knee_half - hip_half) / (THIGH_FRAC * h))))

    # ITS REAL SIZE, FROM THE SAME CONSTRUCTION emit() DRAWS. Stating `h + 2d + clearance` was a
    # plausible-looking sum and it disagreed with the body by 5 cm -- the render contradicting the
    # number it sits on. These two lines are the helmet crown and the boot sole as emit places them,
    # so the claim and the picture are the same arithmetic.
    top_local = HELMET_Z + 1.35 * (r_helmet / h)          # helmet centre sits 0.35r above neck top
    bottom_local = -(SHANK_FRAC + THIGH_FRAC - leg_local(parent)) - 1.75 * (r_shank / h)

    # ── THE MATERIALS, MEASURED RATHER THAN TYPED (F1, 2026-07-31) ─────────────────────────────
    # Three flat albedos used to live in emit() as literals with a reasoned comment each. The
    # reasons were sound; the numbers were picked. Now the same reasons pick among MEASURED
    # distributions: the joint element codebook extracted from 16 real 3DGS scans by
    # Construction/material_elements.py (the operator's rule: the game is made from the scans).
    from matter import material_genomes
    _lib = material_genomes()
    _picks, _lums = _pick_materials(_lib)
    _g = {g["id"]: g for g in _lib["genomes"]}

    def _mat_albedo(gid):
        f = _g[gid]["features"]
        return {"mean": [f["R"]["mean"], f["G"]["mean"], f["B"]["mean"]],
                "std": [f["R"]["std"], f["G"]["std"], f["B"]["std"]],
                "genome_id": gid, "fraction_of_library": _g[gid]["fraction"],
                "luminance": _lums[gid]}

    return {
        "extent_m": (top_local - bottom_local) * h,
        "crown_local": top_local,
        "sole_local": bottom_local,
        # ITS OWN DURATION: one stride, inherited. A suit that needs no pressure shell does not
        # change the gait's timing -- which is itself the parent's finding, not an assumption.
        "duration_s": float(parent["duration_s"]),

        "name": str(parent["suit_class"]),        # DERIVED: change the air and this label changes
        "class_reason": ("no pressure shell required -- above the Armstrong limit"
                         if not bool(parent["suit_needs_pressure_shell"])
                         else "pressure vessel required -- body fluids would boil"),

        # ── THE THERMAL SOLUTION, which is the whole of what this membrane adds ────────────────
        "T_air_C": T_air_C,
        "T_skin_C": T_SKIN_C,
        "dT_defended_K": max(T_SKIN_C - T_air_C, 0.0),
        "metabolic_W": Q,
        "exertion": x,
        "insulation_m": d_insul,
        "insulation_mm": d_insul * 1000.0,
        "bulk_over_bare": bulk_frac,             # how much wider the suit makes them

        # ── THE MATERIALS THE RENDER MUST WEAR (measured: hull genomes + the parent's skin) ────
        "suit_material": _mat_albedo(_picks["suit"]),
        "visor_material": _mat_albedo(_picks["visor"]),
        "hardware_material": _mat_albedo(_picks["hardware"]),
        "visor_transmission": VISOR_TRANSMIT,    # DECLARED, the operator's dial -- see the constant
        "materials_source": "story/data/material_genomes.json (16 real 3DGS scans; Construction/material_elements.py)",
        # THE SKIN, CARRIED DOWN: the face inside the helmet is the parent's derived skin, and
        # the walker's relight wraps light around it by the measured subsurface reach.
        "skin_albedo_rgb": [float(v) for v in parent["skin_albedo_rgb"]],
        "skin_sss_mfp_mm": [float(v) for v in parent["skin_sss_mfp_mm"]],
        "melanin_class": str(parent["melanin_class"]),
        "skin_area_m2": skin_area,

        # ── THE SHAPE THE RENDER MUST DRAW ────────────────────────────────────────────────────
        "r_thigh_m": r_thigh,
        "r_shank_m": r_shank,
        "r_arm_m": r_arm,
        "r_forearm_m": r_forearm,
        "r_trunk_m": r_trunk,
        "r_helmet_m": r_helmet,
        "r_head_m": r_head_bare,                 # the bare head INSIDE the helmet -- emit draws it
        "helmet_clearance_m": HELMET_CLEAR_M,
        "hip_half_m": hip_half,
        "shoulder_half_m": shoulder_half,
        "stance_width_m": 2.0 * hip_half,
        "shoulder_width_m": 2.0 * shoulder_half,
        "stance_forced_by_suit": hip_half > 0.055 * h,      # True = the suit, not the skeleton, sets it
        "knee_half_m": knee_half,
        "splay_deg": math.degrees(splay_rad),
        "thigh_gap_at_hip_m": 2.0 * hip_half - 2.0 * r_thigh,
        "thigh_gap_at_knee_m": 2.0 * knee_half - 2.0 * r_thigh,
        "legs_would_touch_without_splay": (2.0 * hip_half - 2.0 * r_thigh) < r_thigh,

        # carried on: the body, the world, the clock
        "height_m": h,
        "leg_length_m": float(parent["leg_length_m"]),
        "com_height_m": float(parent["com_height_m"]),
        "stride_m": float(parent["stride_m"]),
        # THE GAIT, CARRIED AS NUMBERS. This membrane does not know how to walk and must not learn:
        # restating the parent's leg_cycle here would be two gaits that agree until one is edited.
        "gait_cycle": [list(row) for row in parent["gait_cycle"]],
        # ...in EVERY measured direction (A3): the walker picks the table by where the body is
        # actually going, and each direction's own stride sets the phase so feet do not skate.
        "gait_cycles": {k: [list(row) for row in v]
                        for k, v in parent["gait_cycles"].items()},
        "gait_dir_stride_m": dict(parent["gait_dir_stride_m"]),
        "gait_samples": int(parent["gait_samples"]),
        # THE FOOT'S CONTACT GEOMETRY, CARRIED AS NUMBERS: the heel lever behind the ankle and
        # the ball pivot ahead of it are what the parent's hip-height table was solved against.
        # emit() draws the boot to the same law, so the hip it must not touch and the sole it
        # places are the same arithmetic (B1).
        "heel_lever_frac": float(parent["heel_lever_frac"]),
        "forefoot_lever_frac": float(parent["forefoot_lever_frac"]),
        "ankle_drop_frac": float(parent["ankle_drop_frac"]),
        "mass_kg": float(parent["mass_kg"]),
        "suit_mass_kg": float(parent["suit_mass_kg"]),
        "g": float(parent["g"]),
        "S_earth": float(parent["S_earth"]),
        "T_surface": float(parent["T_surface"]),
        "latitude_deg": float(parent["latitude_deg"]),
        "day_s": float(parent["day_s"]),
        "obliquity_deg": float(parent["obliquity_deg"]),
        "P_surface_bar": float(parent["P_surface_bar"]),
        "o2_fraction_needed": float(parent["o2_fraction_needed"]),
        "breathable_unaided": bool(parent["breathable_unaided"]),
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER
# ════════════════════════════════════════════════════════════════════════════════════════════════
GRAIN_LOCAL = 0.0135        # the grain this membrane draws with, in stature units (~24 mm)


def _tube(p0, p1, r0, r1, rings=None, per_ring=None, rng=None):
    """A limb as a SURFACE, not a smear.

    The parent draws its stick figure by jittering points around a bone axis, which is right for a
    diagram and wrong for a body: noise around a line reads as fog, because the silhouette is where
    the eye finds a shape and noise has no silhouette. This lays grains ON the tube's surface --
    rings of them around the axis -- so the edge is sharp and the limb reads as a volume.
    """
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    axis = p1 - p0
    L = np.linalg.norm(axis)
    if L < 1e-9:
        return np.zeros((0, 3)), np.zeros((0, 3))
    axis = axis / L
    # A GRAIN MUST BE BIGGER THAN ITS GAP -- the same law the terrain clipmap obeys, applied to a
    # tube. Fixed ring counts left the trunk with 81 mm between 24 mm grains, and the render came
    # back as a visible diamond mesh you could see through. Deriving the counts from the tube's own
    # circumference and length means a fat limb gets more grains than a thin one, automatically.
    step = GRAIN_LOCAL * 0.62                   # 0.62 of a grain: overlapping, so no gap survives
    if per_ring is None:
        per_ring = int(max(8, min(96, np.ceil(2.0 * np.pi * max(r0, r1) / step))))
    if rings is None:
        rings = int(max(3, min(64, np.ceil(L / step))))
    # any two directions perpendicular to the axis
    tmp = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(axis, tmp); e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)

    t = np.linspace(0.0, 1.0, rings)[:, None]
    ang = np.linspace(0.0, 2.0 * np.pi, per_ring, endpoint=False)[None, :]
    # stagger each ring so the grains do not line up into visible seams down the limb
    ang = ang + (np.arange(rings)[:, None] * (np.pi / per_ring))
    r = (r0 * (1 - t) + r1 * t)
    centre = p0[None, :] * (1 - t) + p1[None, :] * t
    off = (np.cos(ang)[:, :, None] * e1[None, None, :]
           + np.sin(ang)[:, :, None] * e2[None, None, :]) * r[:, :, None]
    pts = (centre[:, None, :] + off).reshape(-1, 3)
    nrm = off.reshape(-1, 3)
    nrm = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
    return pts, nrm


def _ball(c, r, n=None, seed=0):
    """A sphere closed at the same grain -- the count comes from its area, not from a guess."""
    if n is None:
        n = int(max(60, min(4000, np.ceil(4.0 * np.pi * (r / (GRAIN_LOCAL * 0.55)) ** 2))))
    d = np.random.default_rng(seed).normal(0.0, 1.0, (int(n), 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
    return np.asarray(c, float)[None, :] + d * r, d


def emit(nums, t=1.0, ground=None, cycle=None):
    """The suited body, in its own local units (1.0 = standing height), walking along +X.

    THE POSE IS THE PARENT'S PHYSICS; THE SKIN IS THIS MEMBRANE'S THERMAL SOLUTION. Every limb is
    a tube whose radius is the bare anthropometry plus the insulation solved above, so the figure's
    bulk is a temperature reading. The helmet is the head plus that same insulation plus the visor
    standoff -- and the faceplate is dark because a visor's job is to reject light, which is the
    only reason anything here is a different colour.

    `ground(lx, ly) -> local z` (B1, optional): the carved terrain under the body, in this same
    pre-CoM local frame. When it is given, every PLANTED foot is placed on it -- two-bone solve,
    the knee absorbs the difference, the hip keeps the parent's measured bob. When it is not
    given the pose is the parent's flat table exactly as before (the membrane's own demo view).

    `cycle` (A3, optional): the 48-row gait table to pose from, in the parent's row format --
    the walker hands in the table for the direction the body is actually moving (the parent's
    `gait_cycles`); None is the forward `gait_cycle`, exactly as before.
    """
    from matter import blank, lit, SOLID, AR, AG, AB, MAT as MATCOL

    tt = float(t)
    h = 1.0
    leg = float(nums["leg_length_m"]) / float(nums["height_m"])
    com_h = float(nums["com_height_m"]) / float(nums["height_m"])
    H = float(nums["height_m"])
    # radii in LOCAL units
    r_th = float(nums["r_thigh_m"]) / H
    r_sh = float(nums["r_shank_m"]) / H
    r_ar = float(nums["r_arm_m"]) / H
    r_fa = float(nums["r_forearm_m"]) / H
    r_tr = float(nums["r_trunk_m"]) / H
    r_hl = float(nums["r_helmet_m"]) / H
    hip_half = float(nums["hip_half_m"]) / H
    sh_half = float(nums["shoulder_half_m"]) / H
    splay = math.radians(float(nums["splay_deg"]))
    # THE CONTACT GEOMETRY, READ FROM THE PARENT: the heel lever behind the ankle and the ball
    # pivot ahead of it. The gait table's hip heights were solved against exactly these, so a
    # boot drawn and placed to the same law agrees with the hip it hangs from by construction.
    heel_lev = float(nums["heel_lever_frac"])
    ball_lev = float(nums["forefoot_lever_frac"])

    phase = 2.0 * math.pi * tt
    # ── THE POSE COMES FROM THE PARENT'S TABLE, indexed, not recomputed ───────────────────────
    # theHuman publishes 48 samples of the cycle: hip height, and per leg the hip angle, the KNEE
    # angle, the foot's pitch to the ground, the stance progress and whether the foot is planted.
    # Reading it is how this membrane walks with exactly the parent's ankle, knee and vault without
    # owning a second copy of any of them -- and the knee and the pitch are new here for exactly
    # that reason. This membrane used to rebuild both: `bend = sin(pi*u) * 0.85` for the knee and a
    # transcribed three-rocker formula for the boot. Both were copies of a law that has since been
    # replaced by measurement, and copies do not get updated. Now there is one gait in this story,
    # it belongs to the parent, it is 246 measured adults, and this membrane indexes it.
    GT = cycle if cycle is not None else nums["gait_cycle"]
    N = int(nums["gait_samples"])
    _row = GT[int(tt * N) % N]
    hip_z = float(_row[0])
    _legs = [(float(_row[1 + 5 * i]), float(_row[2 + 5 * i]), float(_row[3 + 5 * i]),
              float(_row[4 + 5 * i]), _row[5 + 5 * i] > 0.5) for i in (0, 1)]
    pts, nrms, mats = [], [], []

    def add(pn, kind):
        p, n = pn
        if len(p):
            pts.append(p); nrms.append(n); mats.append(np.full(len(p), kind))

    for side, _i in ((-1.0, 0), (1.0, 1)):
        th_hip, bend, _fp, _u, _planted = _legs[_i]
        # LATERAL IS Y, NOT X. This is the bug that made the derived stance invisible: the hip
        # offset was written on the X axis -- the SAME axis the leg swings along -- so the two legs
        # were separated fore-aft instead of side to side, and from the front they projected exactly
        # onto each other into one tapering column. The numbers were right and unused.
        #
        # The tell is camera-independent and damning: the figure measured 0.37 m across from the
        # FRONT and 0.97 m from the SIDE. A walking person is wider from the front. Everything about
        # the clearance calculation above was correct; it was being applied to the wrong axis.
        hip = np.array([0.0, hip_half * side, hip_z])
        # the femur carries the derived splay: it swings fore-aft in X-Z AND leans outward in Y, so
        # the knee sits further from the midline than the hip does and the two legs actually part.
        sp = math.sin(splay) * side
        cs = math.cos(splay)
        knee = hip + np.array([math.sin(th_hip) * cs, sp, -math.cos(th_hip) * cs]) * THIGH_FRAC
        th_kn = th_hip - bend
        # the shank comes back toward vertical -- a knee is not a hinge that keeps the tilt
        ankle = knee + np.array([math.sin(th_kn) * cs, sp * 0.25, -math.cos(th_kn) * cs]) * SHANK_FRAC
        # ── THE SOLE LANDS ON THE CARVED TERRAIN (B1) ─────────────────────────────────────────
        # Until now both boots were posed against a FLAT virtual floor at the walker's z: on any
        # slope the downhill boot ploughed through the ground while the uphill one floated. A
        # planted foot is not POSED, it is PLACED -- the terrain decides where the sole is, and
        # the KNEE absorbs the difference, because the hip is the parent's measured bob and the
        # CoM is nobody's to flatten. Two-bone analytic solve (law of cosines -- the standard
        # IK row of PHYSICS_SOFTWARE_MATH), clamped to the knee's measured range; what the leg
        # cannot reach, the sole honestly does not touch. Swing feet are the parent's pose --
        # the spec is about LANDING, and a foot in the air is not on any terrain.
        if ground is not None and _planted:
            drop = leg - (THIGH_FRAC + SHANK_FRAC)          # ankle-to-sole, the parent's figure
            # the boot's pitch is measured RELATIVE TO THE GROUND -- on a slope the ground
            # itself is pitched, so the sole reads the tilt under its two contact levers and
            # adds it, and the parent's rocker law survives on terrain.
            g_heel = float(ground(ankle[0] - math.cos(_fp) * heel_lev, ankle[1]))
            g_ball = float(ground(ankle[0] + math.cos(_fp) * ball_lev, ankle[1]))
            span = (heel_lev + ball_lev) * math.cos(_fp)
            if span > 1e-6:
                _fp = _fp + math.atan2(g_ball - g_heel, span)
            # THE CONTACT LAW IS THE PARENT'S OWN -- the same one the gait table's hip heights
            # were solved with (ankle_height in theHuman): the ankle sits drop*cos(p) above the
            # sole plane, plus a lever's rise over whichever of the heel (behind the ankle) or
            # the ball (ahead of it) is the low end. Pinning the HEEL through the whole stance
            # was the first B1 draft's bug: at push-off the heel must RISE and the ball carries
            # the body, or the toes go through the floor. The case analysis is the parent's --
            # the lower lever carries; no branch is written, the geometry already knows.
            cp, sp_ = math.cos(_fp), math.sin(_fp)
            hz = -heel_lev * sp_ - drop * cp                 # heel contact, relative to the ankle
            tz = ball_lev * sp_ - drop * cp                  # ball contact, relative to the ankle
            cx = ankle[0] + (-heel_lev * cp if hz < tz else ball_lev * cp)
            dz = (float(ground(cx, ankle[1])) - min(hz, tz)) - ankle[2]
            if abs(dz) > 1e-4:
                target = ankle + np.array([0.0, 0.0, dz])
                B_MIN, B_MAX = 0.035, 2.4      # the knee: 2 deg off straight .. 137 deg folded
                d_lo = math.sqrt(THIGH_FRAC**2 + SHANK_FRAC**2 + 2.0 * THIGH_FRAC * SHANK_FRAC * math.cos(B_MAX))
                d_hi = math.sqrt(THIGH_FRAC**2 + SHANK_FRAC**2 + 2.0 * THIGH_FRAC * SHANK_FRAC * math.cos(B_MIN))
                v = target - hip
                d_raw = float(np.linalg.norm(v))
                d = min(max(d_raw, d_lo), d_hi)
                u = v / (d_raw + 1e-12)
                ankle = hip + u * d
                # the knee stays on ITS OWN side of the hip->ankle line -- the bend direction
                # it already had; how MUCH it bends is the terrain's business, not which way.
                alpha = math.acos(min(1.0, max(-1.0,
                    (THIGH_FRAC**2 + d * d - SHANK_FRAC**2) / (2.0 * THIGH_FRAC * d))))
                perp = knee - hip - float(np.dot(knee - hip, u)) * u
                n_perp = float(np.linalg.norm(perp))
                if n_perp > 1e-9:
                    knee = hip + THIGH_FRAC * (math.cos(alpha) * u + math.sin(alpha) * perp / n_perp)
        add(_tube(hip, knee, r_th, r_sh * 1.15), 0)
        add(_tube(knee, ankle, r_sh * 1.15, r_sh), 0)
        # the boot: wider than the leg, because a sole spreads load -- the parent's foot_pressure.
        # THE BOOT'S PITCH IS READ, NOT REBUILT. It used to be a transcribed copy of the parent's
        # three-rocker formula, with the three fractions retyped here -- so the boot rolled by one
        # law while the leg above it moved by another, and they agreed only for as long as nobody
        # edited either. The parent now derives the pitch from three measured joint angles and
        # publishes it; the boot uses that number and cannot disagree with the leg it hangs from.
        # THE BOOT'S UNDERSIDE HAS TO LAND WHERE THE TABLE PUTS THE SOLE. Drawn as a fat tube hung
        # half its own radius below the ankle, the boot was 8.3% of stature thick against the 3.9%
        # the parent's gait assumes -- so it ploughed, and duty factor fell to 0.44 against the
        # parent's 0.58 on an identical pose. A suit thickens a boot outward, not downward: the axis
        # is placed so the underside sits exactly at the ankle drop the gait was solved with.
        _drop = leg - (THIGH_FRAC + SHANK_FRAC)         # ankle to sole, the parent's own figure
        _r_boot = r_sh * 1.25
        # the axis drop is measured along the foot's NORMAL, as the parent's contact law writes
        # it (drop*cos(p)): a vertical _lift leaves the lowest grain drop*(1-cos p) BELOW the
        # sole plane the IK placed -- 17.6 mm of plough at 42 deg of ground-relative pitch.
        _lift = np.array([0.0, 0.0, _r_boot - _drop * math.cos(_fp)])
        # AND THE BOOT HAS THE SHAPE THE CONTACT LAW ASSUMES (B1). The heel reaches BEHIND the
        # ankle by the parent's heel lever -- that is where initial contact lands -- and the
        # rigid part ends at the BALL, because the measured foot segment (mocap ankle->toe
        # marker) is the metatarsal heads, which is where push-off pivots. The toes beyond the
        # ball are their own segment: kept rigid with the foot they would be driven through the
        # floor at push-off, where a real forefoot flexes at the MTP joint and stays on the
        # ground. On terrain the toe reads the tilt under its own span; in the air (or on the
        # membrane's own flat demo view) it stays rigid with the foot, as measured.
        _d = np.array([math.cos(_fp), 0.0, math.sin(_fp)])
        heel_p = ankle - _d * heel_lev
        ball_p = ankle + _d * ball_lev
        toe_p = ankle + _d * FOOT_LEN_FRAC
        if ground is not None and _planted:
            _tp = math.atan2(float(ground(toe_p[0], toe_p[1])) - float(ground(ball_p[0], ball_p[1])),
                             max((FOOT_LEN_FRAC - ball_lev) * math.cos(_fp), 1e-6))
            if _tp > _fp:
                toe_p = ball_p + np.array([math.cos(_tp), 0.0, math.sin(_tp)]) * (FOOT_LEN_FRAC - ball_lev)
        add(_tube(heel_p + _lift, ball_p + _lift, _r_boot, r_sh * 0.9), 2)
        add(_tube(ball_p + _lift, toe_p + _lift, r_sh * 0.9, r_sh * 0.75), 2)

        sh = np.array([0.0, sh_half * side, hip_z + (0.82 - leg)])          # lateral is Y -- see the note above
        th_s = -0.55 * th_hip                          # counter to the leg on the same side
        elbow = sh + np.array([math.sin(th_s), 0.0, -math.cos(th_s)]) * UPPER_ARM_FRAC
        hand = elbow + np.array([math.sin(th_s * 1.4), 0.0, -math.cos(th_s * 1.4)]) * FOREARM_FRAC
        add(_tube(sh, elbow, r_ar * 1.1, r_fa * 1.1), 0)
        add(_tube(elbow, hand, r_fa * 1.1, r_fa * 0.9), 0)
        add(_ball(hand, r_fa * 1.05, seed=21 + int(side)), 2)      # glove

    # trunk, riding the CoM. The bob is the inverted pendulum vaulting the planted foot.
    # THE BOB IS READ OFF THE HIP now, not written -- see the note above.
    pelvis = np.array([0.0, 0.0, hip_z])
    chest = np.array([0.0, 0.0, hip_z + (0.80 - leg)])
    add(_tube(pelvis, chest, r_tr * 0.92, r_tr), 0)
    # THE REBREATHER, ON THE BACK. +X is the way they are walking, so -X is behind them -- and a
    # pack belongs behind a person for the same reason a rucksack does: it is the one place that is
    # not a joint. It is where the carried air lives, and the parent weighed it at 1.56 kg for an
    # eight-hour day. Drawn as an upright box, because a tank and a scrubber stack vertically.
    pack_x = -(r_tr + 0.055)
    for uy in (-0.042, 0.042):
        add(_tube(np.array([pack_x, uy, hip_z + (0.60 - leg)]), np.array([pack_x, uy, hip_z + (0.80 - leg)]),
                  0.050, 0.046), 2)
    neck = np.array([0.0, 0.0, hip_z + (0.855 - leg)])
    add(_tube(chest, neck, r_tr * 0.55, r_hl * 0.62), 0)

    # THE HEAD, INSIDE THE HELMET. The helmet exists because the head does -- the bare head's
    # radius is derived above, and the visor's standoff was sized for it -- so the head is drawn:
    # a body the derivation produced, wearing the parent's measured skin. It shows only through
    # the visor, and only as much as the visor transmits.
    r_hd = float(nums["r_head_m"]) / H
    hc = np.array([0.0, 0.0, hip_z + (HELMET_Z - leg) + r_hl * 0.35])
    hdp, hdn = _ball(hc, r_hd, seed=12)
    pts.append(hdp); nrms.append(hdn); mats.append(np.full(len(hdp), 3))

    # THE HELMET. A sphere, and the front of it is a visor.
    hp, hn = _ball(hc, r_hl, seed=11)
    face = hn[:, 0] > math.cos(VISOR_HALF_ANGLE)          # +X is the way they are walking
    pts.append(hp); nrms.append(hn); mats.append(np.where(face, 1, 0))

    P = np.concatenate(pts, axis=0)
    N = np.concatenate(nrms, axis=0)
    MAT = np.concatenate(mats, axis=0)

    n = len(P)
    b = blank(n)
    b[:, 0], b[:, 1] = P[:, 0], P[:, 1]
    b[:, 2] = P[:, 2] - com_h                            # centre the view on the centre of mass
    b[:, 21:24] = N

    # ── COLOUR. Four materials, each one MEASURED now (F1) ────────────────────────────────────
    # SUIT / VISOR / HARDWARE: albedo distributions recovered from real scans (the hull genomes,
    #   picked in derive() by the same reasons the old literals claimed -- the suit is a thermal
    #   instrument, the visor rejects light, hardware is neither). Sampled per grain with ONE
    #   luminance jitter shared across channels, so the surface mottles instead of confetti-ing.
    # SKIN (the head): the parent's measured skin -- a melanin filter over a blood-bearing dermis,
    #   not a tone anyone picked.
    rng = np.random.default_rng(7)                        # fixed: a pose renders the same every time
    alb = np.zeros((n, 3), np.float32)
    for kind, key in ((0, "suit_material"), (1, "visor_material"), (2, "hardware_material")):
        sel = MAT == kind
        m = nums[key]
        jit = rng.normal(0.0, 1.0, (int(sel.sum()), 1)).astype(np.float32)
        a = (np.array(m["mean"], np.float32)[None, :]
             + jit * np.array(m["std"], np.float32)[None, :])
        alb[sel] = np.clip(a, 0.0, 1.0)
    alb[MAT == 3] = np.array(nums["skin_albedo_rgb"], np.float32)

    sun = np.array([0.55, -0.72, 0.42], np.float32)
    sun /= np.linalg.norm(sun)
    lam = np.clip(N @ sun, 0.0, None)
    S = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S * lam + 0.13, e_ref=S, tone=0.45)
    # the visor also catches a hard highlight -- a curved dark surface with a bright sky in it
    spec = np.clip(N @ sun, 0.0, None) ** 24
    b[MAT == 1, 16:19] += (spec[MAT == 1, None] * 0.75).astype(np.float32)
    np.clip(b[:, 16:19], 0.0, 1.0, out=b[:, 16:19])

    # HAND OVER WHAT IT IS MADE OF. Third person carries this body onto the terrain and relights it
    # under the real sun; without the albedo travelling too, that relight collapsed suit, visor and
    # hardware into one pale tone -- three derived materials erased by a single hard-coded colour.
    b[:, AR:AB + 1] = alb
    b[:, MATCOL] = MAT.astype(np.float32)     # the material class travels: the relight shades per class
    b[:, 19] = 0.97
    # the visor passes what it does not reject -- DECLARED transmission, the operator's dial
    b[MAT == 1, 19] = 1.0 - float(nums["visor_transmission"])
    # a grain must close its own surface: the ring spacing is what sets it, not one global size
    b[:, 20] = GRAIN_LOCAL
    b[:, 11] = SOLID
    return b


def measure(nums):
    """Facts a reader can check without trusting the prose."""
    return {
        # the suit exists because the air fails, and by a stated margin
        "air_needs_o2_fraction": nums["o2_fraction_needed"],
        "breathable_unaided": nums["breathable_unaided"],
        "class": nums["name"],
        # the thermal solution is a real balance: conduction through d at dT equals metabolism
        "insulation_mm": nums["insulation_mm"],
        "conducted_W": (K_INSUL_W_MK * nums["skin_area_m2"] * nums["dT_defended_K"]
                        / max(nums["insulation_m"], 1e-9)),
        "metabolic_W": nums["metabolic_W"],
        "balance_closes": abs(
            (K_INSUL_W_MK * nums["skin_area_m2"] * nums["dT_defended_K"]
             / max(nums["insulation_m"], 1e-9)) - nums["metabolic_W"]) < 1e-6,
        # THE MATERIALS, CHECKED: the mapping must reproduce the ordering the reasons demand
        "suit_brighter_than_hardware": (nums["suit_material"]["luminance"]
                                        > nums["hardware_material"]["luminance"]),
        "hardware_brighter_than_visor": (nums["hardware_material"]["luminance"]
                                         > nums["visor_material"]["luminance"]),
        "three_distinct_genomes": len({nums["suit_material"]["genome_id"],
                                       nums["visor_material"]["genome_id"],
                                       nums["hardware_material"]["genome_id"]}) == 3,
        # and the skin is skin: red returns most, blue least -- the melanin/hemoglobin signature
        "skin_is_red_dominant": (nums["skin_albedo_rgb"][0] > nums["skin_albedo_rgb"][1]
                                 > nums["skin_albedo_rgb"][2]),
        "suit_is_bulkier_than_bare": nums["bulk_over_bare"] > 0.0,
        "no_pressure_shell": not nums["breathable_unaided"] and nums["insulation_m"] > 0.0,
    }
