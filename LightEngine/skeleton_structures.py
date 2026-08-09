"""
StandingHuman print builder (Lane A assembly).

Generates a cold-print point cloud for the standing human skeleton:
  - bones seated on a pinned ground plate,
  - cup joints that wrap child bone ends with a d_eq capture gap,
  - single-file taut ropes between bone anchors,
  - deterministic seeded jitter and a print-law check.

The builder is table-driven through LightEngine/skeleton_scaling.scale_skeleton().
If the scaling table's estimated grain count exceeds the 50 000 grain budget,
the builder refuses to print and returns a per-body breakdown.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from LightEngine import skeleton_scaling
from LightEngine.rope_network import (
    JOINT_CENTERS,
    VERTEBRAL_CENTERS,
    DERIVED_JOINT_CENTERS,
    DERIVED_VERTEBRAL_CENTERS,
    SACRUM_POSTERIOR,
    SACRUM_PROMONTORY,
    ILIUM_POSTERIOR,
    SPINOUS_OFFSET_X,
    SPINOUS_OFFSET_Z,
    get_rope_network,
)
from LightEngine.constants import R_WALL


# ---------------------------------------------------------------------------
# Print constants (inherited from the scaling lane)
# ---------------------------------------------------------------------------
D_EQ_LU = skeleton_scaling.D_EQ_LU
SPACING_LU = D_EQ_LU  # grain spacing is d_eq in the budget-first table.
BUDGET_GRAINS = skeleton_scaling.N_BUDGET
MIN_PAIR_DIST = 1e-6


def _budget_breakdown(
    total: int,
    breakdown: tuple[int, int, int, int],
    table: list[dict],
) -> str:
    """Return a human-readable grain budget breakdown."""
    bg, cg, rg, pg = breakdown
    lines = []
    lines.append("Grain budget breakdown (from scaling lane):")
    lines.append("-" * 60)
    lines.append(f"  bones : {bg:,}")
    lines.append(f"  cups  : {cg:,}")
    lines.append(f"  ropes : {rg:,}")
    lines.append(f"  plate : {pg:,}")
    lines.append("-" * 60)
    lines.append(f"  TOTAL : {total:,}")
    lines.append(f"  BUDGET: {BUDGET_GRAINS:,}")
    lines.append("")
    lines.append("Top bone consumers:")
    for row in sorted(table, key=lambda r: r["grain_count"], reverse=True)[:10]:
        lines.append(f"  {row['name']:<28s} {row['grain_count']:>8,}  ({row['rung']})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Body-plan frame helpers
# ---------------------------------------------------------------------------
def _mirror_y(p: tuple[float, float, float]) -> tuple[float, float, float]:
    return (p[0], -p[1], p[2])


def _scale_point(p: tuple[float, float, float], height_lu: float) -> np.ndarray:
    return np.array([p[0] * height_lu, p[1] * height_lu, p[2] * height_lu],
                    dtype=np.float64)


def _scale_xz(p: tuple[float, float], height_lu: float) -> np.ndarray:
    return np.array([p[0] * height_lu, 0.0, p[1] * height_lu], dtype=np.float64)


def _spinous(level: str, height_lu: float) -> np.ndarray:
    """Posterior spinous-process point for a vertebral level."""
    xz = VERTEBRAL_CENTERS[level]
    return np.array([
        (xz[0] + SPINOUS_OFFSET_X) * height_lu,
        0.0,
        (xz[1] + SPINOUS_OFFSET_Z) * height_lu,
    ], dtype=np.float64)


# ---------------------------------------------------------------------------
# Body plan: map scaling-table rows to anatomical instances.
# ---------------------------------------------------------------------------
# PATCH-UP FOOT (VERDICT 25, docs/JOINT_ATLAS.md, membrane written
# 2026-08-09 before the build).  The knife-edge legacy foot was measured
# 2026-08-09: per-foot polygon 1.8 cm wide (a single diagonal line),
# metatarsal_base at z = -1.8 cm BELOW the floor, arch inverted
# (tarsal +1.8 -> met_base -1.8 -> mtp 0.0 cm, never touching the
# keystone at z = 4.5 cm), foot length 24.3 cm (13.5% H) vs the 15.2% H
# datum.  The patch-up foot derives the CONTACT PATCH on the floor first,
# then grows the bones up from it.  All numbers below are derived, never
# swept; each carries its datum:
#   L      = 0.152 H         foot length datum (15.2% stature = 27.4 cm).
#   heel   = 0.26 * L behind the ankle   (VERDICT 7 calcaneus derivation)
#   toe    = 0.74 * L ahead of the ankle
#   ankle  = (0, +-0.060, 0.040) H   audit 2026-08-09: OK (4.0% H ~ 3.9%)
#   keystone = foot_arch_keystone at (0.020, +-0.040, 0.025) H (4.5 cm);
#             the tarsal joint IS the keystone, so the arch apex passes
#             through it (prediction (c)).
#   mtp    = 70% of foot length from the heel, ON the sole (the ball).
#   met_base = midpoint of the tarsal->mtp arch rod: unburied (z = 1.25%
#             H = 2.25 cm, in the "midfoot rides 2-4 cm above the sole"
#             datum band).
#   zone widths (repo datum, @H=1.8): hindfoot 7 / midfoot 6 / toes 5 cm
#             = 0.0389 / 0.0333 / 0.0278 H; the ball (MTP heads) uses the
#             widest zone 7 cm.
# The repo segment-span datums (tarsals 6% / metatarsals 8% / toes 5% H)
# are mutually inconsistent with L = 0.152 H (6+8+5 = 19% H > 15.2% H),
# so the spans are derived from the settled constraints instead: tarsals
# 2% H (pinned by the keystone x), metatarsals 4.7% H (tarsal->mtp),
# toes 4.6% H (mtp->toe, hits the 5% datum).  Recorded, not swept.
_PATCH_FOOT = {
    "foot_length_h": 0.152,
    "heel_frac": 0.26,
    "mtp_frac": 0.70,          # MTP line at 70% of L from the heel
    "ankle": (0.000, 0.060, 0.040),
    "keystone": (0.020, 0.040, 0.025),
    "w_heel_h": 0.0389,        # 7 cm @H=1.8 (repo datum)
    "w_mid_h": 0.0333,         # 6 cm @H=1.8 (repo datum)
    "w_toe_h": 0.0278,         # 5 cm @H=1.8 (repo datum)
}


def _joint_dict(height_lu: float, foot_style: str = "legacy",
                body_style: str = "legacy") -> dict[str, np.ndarray]:
    """Return all named joint centers in lu.

    foot_style="patch" (VERDICT 25) rebuilds the foot chain from the
    contact patch up (see _PATCH_FOOT); "legacy" (default) is the
    pre-VERDICT-25 geometry, bit-identical.

    body_style="derived" (RULE 27 build membrane, 2026-08-09) re-derives
    VERTEBRAL_CENTERS, JOINT_CENTERS, and limb offsets from bone-table
    fractions so every segment matches its ANATOMY-DATUM within ±2% of
    stature.  body_style="legacy" (default) is bit-identical to the
    pre-build geometry.
    """
    j: dict[str, np.ndarray] = {}

    # Mirrored limb joints — legacy or derived center set.
    jc_set = DERIVED_JOINT_CENTERS if body_style == "derived" else JOINT_CENTERS
    for key in ("ankle", "knee", "hip", "shoulder", "foot_arch_keystone"):
        left = jc_set[key]
        j[f"{key}_L"] = _scale_point(left, height_lu)
        j[f"{key}_R"] = _scale_point(_mirror_y(left), height_lu)

    # Vertebral body centers (midline) — legacy or derived.
    vc_set = DERIVED_VERTEBRAL_CENTERS if body_style == "derived" else VERTEBRAL_CENTERS
    for level, xz in vc_set.items():
        j[level] = _scale_xz(xz, height_lu)

    # Sacrum / pelvis arch reference points.
    j["sacrum_posterior"] = _scale_point(SACRUM_POSTERIOR, height_lu)
    j["sacrum_promontory"] = _scale_point(SACRUM_PROMONTORY, height_lu)
    j["ilium_posterior_L"] = _scale_point(ILIUM_POSTERIOR, height_lu)
    j["ilium_posterior_R"] = _scale_point(_mirror_y(ILIUM_POSTERIOR), height_lu)

    # Head (cranial vault center and suture/condyle region).
    j["skull_center"] = _scale_point((-0.020, 0.000, 0.950), height_lu)
    if body_style == "derived":
        # DERIVED-GEOMETRY: skull link covers full 0.12 H per bone table.
        # Suture at C1_z + skull length_fraction (0.12 H).
        c1_z = DERIVED_VERTEBRAL_CENTERS["C1"][1]
        j["skull_suture"] = _scale_point((-0.030, 0.000, c1_z + 0.120), height_lu)
    else:
        j["skull_suture"] = _scale_point((-0.030, 0.000, 0.985), height_lu)

    # Sternum.
    j["sternum_top"] = _scale_point((-0.005, 0.000, 0.885), height_lu)
    j["sternum_bottom"] = _scale_point((-0.005, 0.000, 0.775), height_lu)

    # Elbow / wrist / hand joints (approximate).
    for side in ("L", "R"):
        sgn = 1.0 if side == "L" else -1.0
        sh = j[f"shoulder_{side}"]
        if body_style == "derived":
            # DERIVED-GEOMETRY: upper arm 0.19 H, forearm 0.14 H per bone table.
            elbow = sh + np.array([0.015, 0.015 * sgn, -0.190]) * height_lu
            j[f"elbow_{side}"] = elbow
            wrist = elbow + np.array([0.015, 0.010 * sgn, -0.140]) * height_lu
            j[f"wrist_{side}"] = wrist
            # Hand: fold phantom tip into single link at ANSUR 0.110 H.
            # diag = sqrt(0.025^2 + 0.010^2 + z_drop^2) = 0.110 → z_drop ≈ -0.1067
            hand_z = -math.sqrt(0.110**2 - 0.025**2 - 0.010**2)
            hand = wrist + np.array([0.025, 0.010 * sgn, hand_z]) * height_lu
            j[f"hand_{side}"] = hand
        else:
            elbow = sh + np.array([0.015, 0.015 * sgn, -0.180]) * height_lu
            j[f"elbow_{side}"] = elbow
            wrist = elbow + np.array([0.015, 0.010 * sgn, -0.130]) * height_lu
            j[f"wrist_{side}"] = wrist
            hand = wrist + np.array([0.025, 0.010 * sgn, -0.060]) * height_lu
            hand_tip = hand + np.array([0.030, 0.005 * sgn, -0.050]) * height_lu
            j[f"hand_{side}"] = hand
            j[f"hand_tip_{side}"] = hand_tip

        # Foot chain.
        ankle = j[f"ankle_{side}"]
        if foot_style == "patch":
            # PATCH-UP FOOT (VERDICT 25): bones grow up from the contact
            # patch derived in _foot_patch_points.  H-fraction offsets in
            # the body-plan frame, scaled by height_lu like every joint.
            pf = _PATCH_FOOT
            L_h = pf["foot_length_h"]
            heel_x_h = -pf["heel_frac"] * L_h
            toe_x_h = (1.0 - pf["heel_frac"]) * L_h
            kx, ky, kz = pf["keystone"]
            tarsal = np.array([kx, ky * sgn, kz]) * height_lu
            mtp_x_h = heel_x_h + pf["mtp_frac"] * L_h
            mtp = np.array([mtp_x_h, 0.060 * sgn, 0.000]) * height_lu
            # met_base = midpoint of the tarsal->mtp arch rod (unburied).
            met_base = 0.5 * (tarsal + mtp)
            forefoot = np.array([toe_x_h, 0.060 * sgn, 0.000]) * height_lu
        else:
            tarsal = ankle + np.array([0.020, 0.005 * sgn, -0.030]) * height_lu
            met_base = ankle + np.array([0.035, 0.010 * sgn, -0.050]) * height_lu
            mtp = ankle + np.array([0.070, 0.010 * sgn, -0.040]) * height_lu
            forefoot = ankle + np.array([0.100, 0.010 * sgn, -0.035]) * height_lu
        j[f"tarsal_{side}"] = tarsal
        j[f"metatarsal_base_{side}"] = met_base
        j[f"mtp_{side}"] = mtp
        j[f"forefoot_{side}"] = forefoot

    # Rib sternal attachments: evenly spaced along the sternum.
    sternum_top = j["sternum_top"]
    sternum_bottom = j["sternum_bottom"]
    for n in range(1, 13):
        t = (n - 1) / 11.0
        pt = sternum_top + t * (sternum_bottom - sternum_top)
        pt[0] += 0.010 * height_lu
        j[f"rib_sternum_{n}"] = pt

    return j


def _body_instances(table: list[dict], height_lu: float,
                    foot_style: str = "legacy",
                    body_style: str = "legacy") -> list[dict]:
    """Expand the scaling table into concrete left/right body instances."""
    j = _joint_dict(height_lu, foot_style=foot_style, body_style=body_style)
    instances: list[dict] = []

    def add(name: str, prox_key: str, dist_key: str, row: dict) -> None:
        prox = j[prox_key]
        dist = j[dist_key]
        instances.append({
            "name": name,
            "row": row,
            "prox": prox,
            "dist": dist,
            "prox_type": row["prox"],
            "dist_type": row["dist"],
        })

    rows = {r["name"]: r for r in table}

    # Head.
    if "skull" in rows:
        add("skull", "skull_suture", "C1", rows["skull"])

    # Vertebrae C1-L5.
    levels = [f"C{i}" for i in range(1, 8)] + \
             [f"T{i}" for i in range(1, 13)] + \
             [f"L{i}" for i in range(1, 6)]
    for level in levels:
        key = f"vertebra {level}"
        if key not in rows:
            continue
        row = rows[key]
        idx = levels.index(level)
        prox_key = "skull_suture" if idx == 0 else levels[idx - 1]
        dist_key = "S1" if idx == len(levels) - 1 else levels[idx + 1]
        add(f"vertebra_{level}", prox_key, dist_key, row)

    # Sacrum.
    if "sacrum" in rows:
        add("sacrum", "S1", "sacrum_promontory", rows["sacrum"])

    # Ribs: one body per rib, paired.
    for n in range(1, 13):
        key = f"rib pair {n}"
        if key not in rows:
            continue
        row = rows[key]
        vert_level = f"T{min(n, 12)}"
        for side in ("L", "R"):
            sgn = 1.0 if side == "L" else -1.0
            sternal = j[f"rib_sternum_{n}"].copy()
            sternal[1] *= sgn
            key_sternal = f"rib_sternum_{side}_{n}"
            j[key_sternal] = sternal
            add(f"rib_{side}_{n}", vert_level, key_sternal, row)

    # Sternum.
    if "sternum" in rows:
        add("sternum", "sternum_top", "sternum_bottom", rows["sternum"])

    # Shoulder girdle and arms.
    for side in ("L", "R"):
        if "clavicle pair" in rows:
            add(f"clavicle_{side}", "sternum_top", f"shoulder_{side}",
                rows["clavicle pair"])
        if "scapula pair" in rows:
            anchor = f"rib_sternum_L_1" if side == "L" else f"rib_sternum_R_1"
            add(f"scapula_{side}", anchor, f"shoulder_{side}", rows["scapula pair"])
        if "humerus pair" in rows:
            add(f"humerus_{side}", f"shoulder_{side}", f"elbow_{side}",
                rows["humerus pair"])
        if "radius/ulna pair" in rows:
            add(f"radius_ulna_{side}", f"elbow_{side}", f"wrist_{side}",
                rows["radius/ulna pair"])
        if "hand mass" in rows:
            dist_key = f"hand_{side}" if body_style == "derived" else f"hand_tip_{side}"
            add(f"hand_{side}", f"wrist_{side}", dist_key,
                rows["hand mass"])

    # Pelvis and legs.
    for side in ("L", "R"):
        if "pelvis pair" in rows:
            add(f"pelvis_{side}", f"ilium_posterior_{side}", f"hip_{side}",
                rows["pelvis pair"])
        if "femur pair" in rows:
            add(f"femur_{side}", f"hip_{side}", f"knee_{side}",
                rows["femur pair"])
        if "patella pair" in rows:
            add(f"patella_{side}", f"knee_{side}", f"knee_{side}",
                rows["patella pair"])
        if "tibia pair" in rows:
            add(f"tibia_{side}", f"knee_{side}", f"ankle_{side}",
                rows["tibia pair"])
        if "fibula pair" in rows:
            add(f"fibula_{side}", f"knee_{side}", f"ankle_{side}",
                rows["fibula pair"])
        if "tarsals group" in rows:
            add(f"tarsals_{side}", f"ankle_{side}", f"tarsal_{side}",
                rows["tarsals group"])
        if "metatarsals group" in rows:
            add(f"metatarsals_{side}", f"tarsal_{side}", f"mtp_{side}",
                rows["metatarsals group"])
        if "forefoot mass" in rows:
            add(f"forefoot_{side}", f"mtp_{side}", f"forefoot_{side}",
                rows["forefoot mass"])

    return instances


# ---------------------------------------------------------------------------
# Geometry generators
# ---------------------------------------------------------------------------
def _orthonormal_basis(axis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return two unit vectors orthogonal to axis and each other."""
    axis = np.asarray(axis, dtype=np.float64)
    axis /= np.linalg.norm(axis)
    if abs(axis[2]) < 0.9:
        helper = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    else:
        helper = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    v = np.cross(axis, helper)
    v /= np.linalg.norm(v)
    w = np.cross(axis, v)
    w /= np.linalg.norm(w)
    return v, w


def _generate_square_rod(
    prox: np.ndarray,
    dist: np.ndarray,
    side_n: int,
    spacing: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return an ``side_n x side_n`` solid square rod from prox to dist.

    ``side_n = 2`` reproduces the scaling lane's rung (c) estimate (four
    grains per cross-section).  ``side_n = 3`` is the solid 3x3 upgrade used
    when the shrunken ground plate frees budget for the longest bones.
    """
    prox = np.asarray(prox, dtype=np.float64)
    dist = np.asarray(dist, dtype=np.float64)
    axis = dist - prox
    length = float(np.linalg.norm(axis))
    if length < 1e-12:
        return prox.reshape(1, -1)
    axis /= length
    v, w = _orthonormal_basis(axis)

    side_n = max(1, int(side_n))
    # Grid offsets centered on the bone axis; for side_n == 2 this is +/- half spacing.
    offsets = []
    for i in range(side_n):
        for j in range(side_n):
            off_v = (i - (side_n - 1) / 2.0) * spacing * v
            off_w = (j - (side_n - 1) / 2.0) * spacing * w
            offsets.append(off_v + off_w)

    n_layers = max(2, int(math.ceil(length / spacing)) + 1)
    t = np.linspace(0.0, 1.0, n_layers)
    centers = prox[None, :] + t[:, None] * (dist - prox)[None, :]

    pts = np.vstack([c[None, :] + off for c in centers for off in offsets])
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pts.shape)
    return pts + jitter


def _square_effective_radius(side_n: int, spacing: float) -> float:
    """Radius that encloses the corners of a square rod cross-section.

    Used for cup sizing: a spherical cup must clear the farthest corner of
    the child bone's end.
    """
    return 0.5 * side_n * spacing * math.sqrt(2.0)


def _generate_tapered_cylinder(
    prox: np.ndarray,
    dist: np.ndarray,
    r_prox: float,
    r_dist: float,
    solid_end_l: float,
    shell_l: float,
    spacing: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return lattice points inside a tapered hollow cylinder with solid ends.

    Used for rung (a) and rung (b) bones; rung (c) uses _generate_2x2_rod.
    """
    prox = np.asarray(prox, dtype=np.float64)
    dist = np.asarray(dist, dtype=np.float64)
    axis = dist - prox
    length = float(np.linalg.norm(axis))
    if length < 1e-12:
        return prox.reshape(1, -1)
    axis /= length

    end_scale = 1.1
    shaft_scale = 0.9
    r_prox *= end_scale
    r_dist *= end_scale

    v, w = _orthonormal_basis(axis)
    r_max = max(r_prox, r_dist) + spacing

    n_along = max(1, int(math.ceil(length / spacing)) + 2)
    n_rad = max(1, int(math.ceil(r_max / spacing)) + 2)

    t_vals = np.linspace(0.0, 1.0, n_along)
    rad_vals = np.arange(-n_rad, n_rad + 1) * spacing
    t, rv, rw = np.meshgrid(t_vals, rad_vals, rad_vals, indexing="ij")
    points = (
        prox[None, None, None, :]
        + t[..., None] * (dist - prox)[None, None, None, :]
        + rv[..., None] * v[None, None, None, :]
        + rw[..., None] * w[None, None, None, :]
    ).reshape(-1, 3)

    rel = points - prox
    t = np.einsum("ij,j->i", rel, axis) / length
    perp = rel - t[:, None] * length * axis
    r_perp = np.linalg.norm(perp, axis=1)
    r_allowed = r_prox * (1.0 - t) + r_dist * t

    inside = (t >= -1e-6) & (t <= 1.0 + 1e-6) & (r_perp <= r_allowed + 1e-6)
    solid_prox = t < (solid_end_l / length)
    solid_dist = t > (1.0 - solid_end_l / length)
    solid = solid_prox | solid_dist
    r_shaft = shaft_scale * r_allowed
    hollow = (~solid) & (r_perp < r_shaft - shell_l)
    keep = inside & (~hollow)

    pts = points[keep]
    if pts.size == 0:
        return (0.5 * (prox + dist)).reshape(1, -1)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pts.shape)
    return pts + jitter


def _generate_cup(
    center: np.ndarray,
    axis: np.ndarray,
    inner_r: float,
    shell_l: float,
    spacing: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return points for a hemispherical cup shell wrapping a bone end.

    The cup opens along -axis (toward the child ball that sits in the +axis
    direction).  The wall is one grain thick and extends past the equator.
    """
    center = np.asarray(center, dtype=np.float64)
    axis = np.asarray(axis, dtype=np.float64)
    axis /= np.linalg.norm(axis)

    outer_r = inner_r + shell_l
    box = outer_r + spacing
    n = max(1, int(math.ceil(box / spacing)) + 1)
    vals = np.arange(-n, n + 1) * spacing
    x, y, z = np.meshgrid(vals, vals, vals, indexing="ij")
    points = center + np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1)

    rel = points - center
    r = np.linalg.norm(rel, axis=1)
    z_loc = np.einsum("ij,j->i", rel, axis)

    in_shell = (r >= inner_r - 1e-6) & (r <= outer_r + 1e-6)
    in_hemi = z_loc >= -1e-6
    floor = (z_loc >= -shell_l - 1e-6) & (z_loc <= 1e-6) & (r <= outer_r + 1e-6)
    keep = (in_hemi & in_shell) | floor
    keep &= r >= inner_r - 1e-6

    pts = points[keep]
    if pts.size == 0:
        return np.zeros((0, 3), dtype=np.float64)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pts.shape)
    return pts + jitter


def _generate_rope(
    a: np.ndarray,
    b: np.ndarray,
    spacing: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return a single-file chain of grains from a to b at ~spacing."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    vec = b - a
    length = float(np.linalg.norm(vec))
    if length < 1e-12:
        return a.reshape(1, -1)
    n_links = max(2, int(round(length / spacing)) + 1)
    t = np.linspace(0.0, 1.0, n_links)
    pts = a[None, :] + t[:, None] * vec[None, :]
    jitter = rng.normal(0.0, R_WALL * 0.005, size=pts.shape)
    return pts + jitter


def _foot_patch_points(height_lu: float) -> dict[str, list[tuple[str, float, float]]]:
    """PATCH-UP FOOT (VERDICT 25): the contact patch derived on the floor
    FIRST -- every point z = 0 at birth, heel 26% of foot length behind
    the ankle, foot length to the 15.2% H datum, zone widths to the repo
    datums (hindfoot 7 / midfoot 6 / toes 5 cm @H=1.8).  10 points per
    foot (the membrane's <= 10).  Keys end in _L/_R for the contact-spec
    link owner map.
    """
    pf = _PATCH_FOOT
    L_h = pf["foot_length_h"]
    heel_x_h = -pf["heel_frac"] * L_h
    toe_x_h = (1.0 - pf["heel_frac"]) * L_h
    mtp_x_h = heel_x_h + pf["mtp_frac"] * L_h
    mid_x_h = 0.5 * (pf["keystone"][0] + mtp_x_h)  # tarsal->mtp rod midpoint
    w_heel = 0.5 * pf["w_heel_h"]
    w_mid = 0.5 * pf["w_mid_h"]
    w_ball = 0.5 * pf["w_heel_h"]   # MTP heads use the widest zone
    w_toe = 0.5 * pf["w_toe_h"]
    feet: dict[str, list[tuple[str, float, float]]] = {"L": [], "R": []}
    for side in ("L", "R"):
        sgn = 1.0 if side == "L" else -1.0
        yc = 0.060 * sgn
        raw = [
            (f"heel_lat_{side}", heel_x_h, yc + w_heel),
            (f"heel_med_{side}", heel_x_h, yc - w_heel),
            (f"heel_mid_{side}", heel_x_h, yc),
            (f"ankle_mid_{side}", 0.00000, yc),
            (f"mid_lat_{side}", mid_x_h, yc + w_mid),
            (f"mid_med_{side}", mid_x_h, yc - w_mid),
            (f"ball_lat_{side}", mtp_x_h, yc + w_ball),
            (f"ball_med_{side}", mtp_x_h, yc - w_ball),
            (f"toe_lat_{side}", toe_x_h, yc + w_toe),
            (f"toe_med_{side}", toe_x_h, yc - w_toe),
        ]
        feet[side] = [(k, x * height_lu, y * height_lu) for k, x, y in raw]
    return feet


def _foot_projection_joints(height_lu: float,
                            foot_style: str = "legacy") -> dict[str, list[tuple[str, float, float]]]:
    """Return projected (joint_key, x, y) foot contact points for each foot.

    foot_style="patch" (VERDICT 25) returns the independently derived
    contact patch (_foot_patch_points); "legacy" (default) projects the
    joint centers to z = 0, exactly as before.
    """
    if foot_style == "patch":
        return _foot_patch_points(height_lu)
    j = _joint_dict(height_lu)
    feet: dict[str, list[tuple[str, float, float]]] = {"L": [], "R": []}
    for side in ("L", "R"):
        for key in (
            f"ankle_{side}",
            f"tarsal_{side}",
            f"metatarsal_base_{side}",
            f"mtp_{side}",
            f"forefoot_{side}",
        ):
            p = j[key]
            feet[side].append((key, float(p[0]), float(p[1])))
        # CALCANEUS (2026-08-08, VERDICT 7): the human foot extends 26% of
        # its length BEHIND the ankle; this skeleton's polygon used to start
        # AT the ankle joint, so a balanced COM (0.6 cm forward of the
        # ankle) was born 6 mm from the polygon's rear edge and the refusal
        # gate fired at tick 43 (measured).  DERIVED-GEOMETRY: ankle-to-toe
        # is the other 74%, so heel_x = ankle_x - forefoot_x * 0.26/0.74;
        # the heel rides the ankle's y (rear-foot centerline).
        ankle = j[f"ankle_{side}"]
        toe_x = float(j[f"forefoot_{side}"][0]) - float(ankle[0])
        feet[side].append((f"calcaneus_{side}",
                           float(ankle[0]) - toe_x * (0.26 / 0.74),
                           float(ankle[1])))
    return feet


def _foot_projection_points(height_lu: float,
                            foot_style: str = "legacy") -> dict[str, list[tuple[float, float]]]:
    """Return projected (x, y) foot contact points for each foot.

    The plate only needs to cover the actual foot contact area.  The points
    are the scaled joint centers of the foot chain projected onto the ground
    plane (z = 0); foot_style="patch" (VERDICT 25) uses the independently
    derived contact patch instead.
    """
    keyed = _foot_projection_joints(height_lu, foot_style=foot_style)
    return {side: [(x, y) for _key, x, y in pts] for side, pts in keyed.items()}


def _generate_foot_pads(
    foot_points: dict[str, list[tuple[float, float]]],
    spacing: float,
    margin: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return two pinned rectangular foot pads, one per foot.

    Each pad is the axis-aligned bounding box of the foot contact points plus
    a one-grain margin.  The old full-support-polygon plate is replaced by
    these pads, freeing grains for bone resolution upgrades.
    """
    pads: list[np.ndarray] = []
    for side in ("L", "R"):
        pts = foot_points[side]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        min_x = min(xs) - margin
        max_x = max(xs) + margin
        min_y = min(ys) - margin
        max_y = max(ys) + margin

        nx = max(1, int(math.ceil((max_x - min_x) / spacing)))
        ny = max(1, int(math.ceil((max_y - min_y) / spacing)))
        gx = np.linspace(min_x, max_x, nx)
        gy = np.linspace(min_y, max_y, ny)
        px, py = np.meshgrid(gx, gy, indexing="ij")
        pad = np.stack([
            px.ravel(),
            py.ravel(),
            np.zeros(px.size, dtype=np.float64),
        ], axis=1)
        pads.append(pad)

    pts = np.vstack(pads)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pts.shape)
    jitter[:, 2] = 0.0
    return pts + jitter


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------
def build_skeleton(
    height_m: float = 1.80,
    mass_kg: float = 80.0,
    seed: int = 0,
    foot_style: str = "legacy",
    body_style: str = "legacy",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], dict[str, Any]]:
    """Build the StandingHuman print.

    Returns
    -------
    positions : (N, 3) float32 array
    velocities : (N, 3) float32 array
    pin_mask : (N,) bool array
    grain_ids : (N,) int32 array
    body_names : list of body names; grain_ids index into this list.
    derived : dict with per-body COMs, support polygon, joints, ropes, etc.

    foot_style="legacy" (default) is the pre-VERDICT-25 knife-edge foot;
    foot_style="patch" (VERDICT 25) rebuilds from the contact patch up.

    body_style="legacy" (default) is bit-identical to the pre-RULE27 geometry.
    body_style="derived" (RULE 27 build membrane) re-derives upper-body and
    spine geometry from bone-table fractions.
    """
    # New budget-first API returns (table, lam, total, breakdown, rc, cand_log).
    table, lam, total_estimated, breakdown, rc, _ = skeleton_scaling.scale_skeleton(
        height_m, mass_kg
    )
    if total_estimated > BUDGET_GRAINS:
        raise RuntimeError(
            f"StandingHuman print exceeds {BUDGET_GRAINS:,} grain budget: "
            f"estimated {total_estimated:,} grains.\n"
            f"{_budget_breakdown(total_estimated, breakdown, table)}"
        )

    height_lu = height_m / lam
    rng = np.random.default_rng(seed)
    spacing = SPACING_LU
    d_eq = D_EQ_LU

    instances = _body_instances(table, height_lu, foot_style=foot_style,
                                body_style=body_style)
    if not instances:
        raise RuntimeError("No body instances could be built from the scaling table.")

    # ------------------------------------------------------------------
    # Bone geometry helpers.
    # ------------------------------------------------------------------
    def _make_bone_points(inst: dict, side_n: int, rng_local: np.random.Generator) -> np.ndarray:
        """Generate points for one bone instance at the given square-rod side."""
        row = inst["row"]
        rung = row.get("rung", "a")
        prox = inst["prox_final"]
        dist = inst["dist_final"]
        if rung == "c":
            return _generate_square_rod(prox, dist, side_n, spacing, rng_local)
        D_lu = float(row["outer_diameter_lu"])
        r_base = 0.5 * D_lu
        return _generate_tapered_cylinder(
            prox, dist, r_base, r_base * 0.85,
            float(row["solid_end_lu"]), float(row["shell_thickness_lu"]),
            spacing, rng_local,
        )

    def _child_radius(inst: dict, side_n: int) -> float:
        """Effective radius of a bone end for cup sizing."""
        D_lu = float(inst["row"]["outer_diameter_lu"])
        rung = inst["row"].get("rung", "a")
        if rung == "c":
            return max(0.5 * D_lu, _square_effective_radius(side_n, spacing))
        return 0.5 * D_lu

    # Cup joints: parent bone end wraps child bone end.
    ball_cup_pairs = [
        ("pelvis_L", "dist", "femur_L", "prox", "hip_L"),
        ("pelvis_R", "dist", "femur_R", "prox", "hip_R"),
        ("scapula_L", "dist", "humerus_L", "prox", "shoulder_L"),
        ("scapula_R", "dist", "humerus_R", "prox", "shoulder_R"),
        ("vertebra_C1", "prox", "skull", "dist", "atlanto_occipital"),
    ]

    def _count_cups(side_n_by_name: dict[str, int], rng_local: np.random.Generator) -> int:
        """Return the total cup grain count for the current side_n map."""
        total = 0
        for parent_name, parent_end, child_name, child_end, _ in ball_cup_pairs:
            parent = next((i for i in instances if i["name"] == parent_name), None)
            child = next((i for i in instances if i["name"] == child_name), None)
            if parent is None or child is None:
                continue
            child_r = _child_radius(child, side_n_by_name.get(child_name, 2))
            if parent_end == "prox":
                cup_center = parent["prox_final"]
                axis = -parent["axis_unit"]
            else:
                cup_center = parent["dist_final"]
                axis = parent["axis_unit"]
            cup_pts = _generate_cup(
                cup_center, axis, child_r + d_eq, spacing, spacing, rng_local
            )
            total += int(cup_pts.shape[0])
        return total

    # ------------------------------------------------------------------
    # First pass: default 2x2 square rods (or hollow/solid for rung a/b).
    # ------------------------------------------------------------------
    body_names: list[str] = []
    coms: dict[str, np.ndarray] = {}

    for body_id, inst in enumerate(instances):
        prox = np.asarray(inst["prox"], dtype=np.float64)
        dist = np.asarray(inst["dist"], dtype=np.float64)
        axis = dist - prox
        cur_len = float(np.linalg.norm(axis))
        if cur_len > 1e-12:
            axis_unit = axis / cur_len
        else:
            axis_unit = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        inst["prox_final"] = prox
        inst["dist_final"] = dist
        inst["axis_unit"] = axis_unit
        inst["default_side_n"] = 2 if inst["row"].get("rung", "a") == "c" else 0
        body_names.append(inst["name"])

    # ------------------------------------------------------------------
    # Reallocate plate savings into bone resolution upgrades.
    #
    # The shrunken foot-pad plate frees thousands of grains.  Spend them on
    # the longest / most heavily loaded square-rod bones by upgrading whole
    # left/right groups to 3x3 solid rods, stopping before the budget.
    # ------------------------------------------------------------------
    side_n_by_name: dict[str, int] = {
        inst["name"]: inst["default_side_n"] for inst in instances
    }

    # Fixed-cost bodies (ropes + plate) can be counted once.
    rope_network = get_rope_network()
    rope_count = sum(
        max(2, int(round(float(np.linalg.norm(
            np.asarray(r["anchor_a_point"]) - np.asarray(r["anchor_b_point"])
        )) * height_lu / spacing)) + 1)
        for r in rope_network
    )
    foot_points = _foot_projection_points(height_lu)
    plate_pts_count = _generate_foot_pads(
        foot_points, spacing, d_eq, np.random.default_rng(0)
    ).shape[0]
    fixed_cost = rope_count + plate_pts_count

    count_rng = np.random.default_rng(seed + 9999)

    # Build upgrade groups from the scaling table row names (keeps L/R symmetric).
    groups: dict[str, list[dict]] = {}
    for inst in instances:
        groups.setdefault(inst["row"]["name"], []).append(inst)

    def _group_priority(group_instances: list[dict]) -> float:
        return sum(
            float(g["row"].get("length_lu", 0.0))
            * float(g["row"].get("design_load_kg", 1.0))
            for g in group_instances
        )

    sorted_groups = sorted(groups.values(), key=_group_priority, reverse=True)

    positions_list: list[np.ndarray] = [
        _make_bone_points(inst, side_n_by_name[inst["name"]], count_rng)
        for inst in instances
    ]

    SAFETY_GRAINS = 100
    for group in sorted_groups:
        upgradeable = [
            inst for inst in group
            if inst["default_side_n"] == 2 and side_n_by_name[inst["name"]] == 2
        ]
        if not upgradeable:
            continue

        # Try upgrading the whole group together.
        for inst in upgradeable:
            side_n_by_name[inst["name"]] = 3
            idx = instances.index(inst)
            positions_list[idx] = _make_bone_points(inst, 3, count_rng)

        bone_count = sum(p.shape[0] for p in positions_list)
        cup_count = _count_cups(side_n_by_name, count_rng)
        total = bone_count + cup_count + fixed_cost

        if total > BUDGET_GRAINS - SAFETY_GRAINS:
            # Revert.
            for inst in upgradeable:
                side_n_by_name[inst["name"]] = 2
                idx = instances.index(inst)
                positions_list[idx] = _make_bone_points(inst, 2, count_rng)

    # ------------------------------------------------------------------
    # Final bone geometry with the resolved side_n map and the main RNG.
    # ------------------------------------------------------------------
    positions_list = [
        _make_bone_points(inst, side_n_by_name[inst["name"]], rng)
        for inst in instances
    ]
    grain_ids_list: list[np.ndarray] = [
        np.full(p.shape[0], i, dtype=np.int32)
        for i, p in enumerate(positions_list)
    ]
    for inst, pts in zip(instances, positions_list):
        coms[inst["name"]] = pts.mean(axis=0)

    # ------------------------------------------------------------------
    # Generate cups for real, using the upgraded child radii.
    # ------------------------------------------------------------------
    joint_records: list[dict] = []
    for parent_name, parent_end, child_name, child_end, joint_name in ball_cup_pairs:
        parent = next((i for i in instances if i["name"] == parent_name), None)
        child = next((i for i in instances if i["name"] == child_name), None)
        if parent is None or child is None:
            continue

        child_r = _child_radius(child, side_n_by_name.get(child_name, 2))
        child_center = child["prox_final"] if child_end == "prox" else child["dist_final"]

        if parent_end == "prox":
            cup_center = parent["prox_final"]
            axis = -parent["axis_unit"]
        else:
            cup_center = parent["dist_final"]
            axis = parent["axis_unit"]

        inner_r = child_r + d_eq
        cup_pts = _generate_cup(
            cup_center, axis, inner_r, spacing, spacing, rng
        )
        if cup_pts.size == 0:
            continue

        parent_id = body_names.index(parent_name)
        cup_start = sum(p.shape[0] for p in positions_list)
        positions_list.append(cup_pts)
        grain_ids_list.append(np.full(cup_pts.shape[0], parent_id, dtype=np.int32))
        cup_end = cup_start + cup_pts.shape[0]
        joint_records.append({
            "name": joint_name,
            "parent": parent_name,
            "child": child_name,
            "cup_center": cup_center,
            "ball_center": child_center,
            "inner_r": inner_r,
            "cup_grains": cup_pts.shape[0],
            "cup_indices": (int(cup_start), int(cup_end)),
        })

    # ------------------------------------------------------------------
    # Generate ropes.
    # ------------------------------------------------------------------
    rope_records: list[dict] = []
    rope_id_start = len(body_names)
    for rope_idx, rope in enumerate(rope_network):
        a = np.asarray(rope["anchor_a_point"], dtype=np.float64) * height_lu
        b = np.asarray(rope["anchor_b_point"], dtype=np.float64) * height_lu
        pts = _generate_rope(a, b, spacing, rng)
        name = f"rope_{rope['name']}"
        body_names.append(name)
        positions_list.append(pts)
        grain_ids_list.append(np.full(pts.shape[0], rope_id_start + rope_idx,
                                      dtype=np.int32))
        rope_records.append({
            "name": rope["name"],
            "anchor_a": rope["anchor_a"],
            "anchor_b": rope["anchor_b"],
            "link_indices": (rope_id_start + rope_idx,),
            "n_grains": pts.shape[0],
        })

    # ------------------------------------------------------------------
    # Ground plate: two foot pads instead of the full support rectangle.
    # ------------------------------------------------------------------
    plate_pts = _generate_foot_pads(foot_points, spacing, d_eq, rng)
    plate_id = len(body_names)
    body_names.append("ground_plate")
    positions_list.append(plate_pts)
    grain_ids_list.append(np.full(plate_pts.shape[0], plate_id, dtype=np.int32))

    # ------------------------------------------------------------------
    # Assemble.
    # ------------------------------------------------------------------
    positions = np.vstack(positions_list).astype(np.float64)
    grain_ids = np.concatenate(grain_ids_list).astype(np.int32)
    velocities = np.zeros_like(positions)
    pin_mask = np.zeros(positions.shape[0], dtype=bool)
    pin_mask[grain_ids == plate_id] = True

    if positions.shape[0] > 1:
        diff = positions[:, None, :] - positions[None, :, :]
        r2 = np.einsum("ijk,ijk->ij", diff, diff)
        np.fill_diagonal(r2, np.inf)
        min_dist = float(np.sqrt(r2.min()))
        if min_dist <= MIN_PAIR_DIST:
            raise RuntimeError(
                f"StandingHuman print law violated: minimum pair distance "
                f"{min_dist:.3e} <= {MIN_PAIR_DIST:.3e}"
            )

    actual_total = positions.shape[0]
    if actual_total > BUDGET_GRAINS:
        breakdown_lines = [f"{n}: {int((grain_ids == i).sum())}"
                           for i, n in enumerate(body_names)]
        raise RuntimeError(
            f"StandingHuman actual grain count {actual_total:,} exceeds "
            f"{BUDGET_GRAINS:,} budget.\nPer-body counts:\n" +
            "\n".join(breakdown_lines)
        )

    # Support polygon from foot-bone distal endpoints at ground level.
    support_points = []
    for side in ("L", "R"):
        for bone in (f"tarsals_{side}", f"metatarsals_{side}",
                     f"forefoot_{side}"):
            inst = next((i for i in instances if i["name"] == bone), None)
            if inst is not None:
                p = inst["dist_final"].copy()
                p[2] = 0.0
                support_points.append(p)
    if not support_points:
        jd = _joint_dict(height_lu)
        for side in ("L", "R"):
            for key in (f"ankle_{side}", f"mtp_{side}", f"forefoot_{side}"):
                p = jd[key].copy()
                p[2] = 0.0
                support_points.append(p)
    support_polygon = np.vstack(support_points) if support_points else np.zeros((0, 3))

    # Per-body grain counts and upgrade record for the report.
    per_body_counts = {
        n: int((grain_ids == i).sum()) for i, n in enumerate(body_names)
    }
    upgrade_groups = sorted({
        inst["row"]["name"]
        for inst in instances
        if side_n_by_name[inst["name"]] >= 3
    })

    derived: dict[str, Any] = {
        "lam": lam,
        "height_lu": height_lu,
        "d_eq": d_eq,
        "spacing": spacing,
        "estimated_total": total_estimated,
        "actual_total": actual_total,
        "body_names": list(body_names),
        "coms": {k: v.astype(np.float32) for k, v in coms.items()},
        "support_polygon": support_polygon.astype(np.float32),
        "joints": joint_records,
        "ropes": rope_records,
        "n_bones": len(instances),
        "n_ropes": len(rope_network),
        "rung_counts": rc,
        "bone_resolution": dict(side_n_by_name),
        "upgrade_groups": upgrade_groups,
        "per_body_counts": per_body_counts,
        "plate_grains": int(plate_pts.shape[0]),
    }

    return (
        positions.astype(np.float32),
        velocities.astype(np.float32),
        pin_mask,
        grain_ids,
        body_names,
        derived,
    )
