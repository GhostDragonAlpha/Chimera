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
def _joint_dict(height_lu: float) -> dict[str, np.ndarray]:
    """Return all named joint centers in lu."""
    j: dict[str, np.ndarray] = {}

    # Mirrored limb joints.
    for key in ("ankle", "knee", "hip", "shoulder", "foot_arch_keystone"):
        left = JOINT_CENTERS[key]
        j[f"{key}_L"] = _scale_point(left, height_lu)
        j[f"{key}_R"] = _scale_point(_mirror_y(left), height_lu)

    # Vertebral body centers (midline).
    for level, xz in VERTEBRAL_CENTERS.items():
        j[level] = _scale_xz(xz, height_lu)

    # Sacrum / pelvis arch reference points.
    j["sacrum_posterior"] = _scale_point(SACRUM_POSTERIOR, height_lu)
    j["sacrum_promontory"] = _scale_point(SACRUM_PROMONTORY, height_lu)
    j["ilium_posterior_L"] = _scale_point(ILIUM_POSTERIOR, height_lu)
    j["ilium_posterior_R"] = _scale_point(_mirror_y(ILIUM_POSTERIOR), height_lu)

    # Head (cranial vault center and suture/condyle region).
    j["skull_center"] = _scale_point((-0.020, 0.000, 0.950), height_lu)
    j["skull_suture"] = _scale_point((-0.030, 0.000, 0.985), height_lu)

    # Sternum.
    j["sternum_top"] = _scale_point((-0.005, 0.000, 0.885), height_lu)
    j["sternum_bottom"] = _scale_point((-0.005, 0.000, 0.775), height_lu)

    # Elbow / wrist / hand joints (approximate).
    for side in ("L", "R"):
        sgn = 1.0 if side == "L" else -1.0
        sh = j[f"shoulder_{side}"]
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


def _body_instances(table: list[dict], height_lu: float) -> list[dict]:
    """Expand the scaling table into concrete left/right body instances."""
    j = _joint_dict(height_lu)
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
            add(f"hand_{side}", f"wrist_{side}", f"hand_tip_{side}",
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


def _generate_2x2_rod(
    prox: np.ndarray,
    dist: np.ndarray,
    spacing: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return a 2x2 square rod aligned from prox to dist.

    This matches the scaling lane's rung (c) estimate: four grains per
    cross-section, spaced by ``spacing`` along the bone axis.
    """
    prox = np.asarray(prox, dtype=np.float64)
    dist = np.asarray(dist, dtype=np.float64)
    axis = dist - prox
    length = float(np.linalg.norm(axis))
    if length < 1e-12:
        return prox.reshape(1, -1)
    axis /= length
    v, w = _orthonormal_basis(axis)

    # Offset vectors for the 2x2 square; each is half a spacing off-axis.
    half = 0.5 * spacing
    offsets = [
        half * v + half * w,
        half * v - half * w,
        -half * v + half * w,
        -half * v - half * w,
    ]

    n_layers = max(2, int(math.ceil(length / spacing)) + 1)
    t = np.linspace(0.0, 1.0, n_layers)
    centers = prox[None, :] + t[:, None] * (dist - prox)[None, :]

    pts = np.vstack([c[None, :] + off for c in centers for off in offsets])
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pts.shape)
    return pts + jitter


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


def _generate_ground_plate(
    height_lu: float,
    spacing: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return a pinned lattice plate sized to the standing support polygon.

    Matches the scaling lane's _plate_grains estimate: the support polygon is
    width_h = 0.12 H (lateral ankle separation) by length_h = 0.09 H
    (calcaneus to metatarsal base), plus a one-grain margin.
    """
    width_h, length_h = skeleton_scaling._support_polygon_size_h()
    margin = spacing
    width = width_h * height_lu + 2.0 * margin
    length = length_h * height_lu + 2.0 * margin
    nx = max(1, int(math.ceil(width / spacing)))
    ny = max(1, int(math.ceil(length / spacing)))

    xs = np.linspace(-0.5 * width, 0.5 * width, nx)
    ys = np.linspace(-0.5 * length, 0.5 * length, ny)
    px, py = np.meshgrid(xs, ys, indexing="ij")
    n = px.size
    pts = np.stack([
        px.ravel(),
        py.ravel(),
        np.zeros(n, dtype=np.float64),
    ], axis=1)
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

    instances = _body_instances(table, height_lu)
    if not instances:
        raise RuntimeError("No body instances could be built from the scaling table.")

    # ------------------------------------------------------------------
    # Generate bone points and cups.
    # ------------------------------------------------------------------
    positions_list: list[np.ndarray] = []
    grain_ids_list: list[np.ndarray] = []
    body_names: list[str] = []
    coms: dict[str, np.ndarray] = {}
    joint_records: list[dict] = []

    for body_id, inst in enumerate(instances):
        row = inst["row"]
        D_lu = float(row["outer_diameter_lu"])
        solid_end_l = float(row["solid_end_lu"])
        shell_l = float(row["shell_thickness_lu"])
        length_lu = float(row["length_lu"])
        rung = row.get("rung", "a")

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

        if rung == "c":
            pts = _generate_2x2_rod(prox, dist, spacing, rng)
        else:
            r_base = 0.5 * D_lu
            r_prox = r_base
            r_dist = r_base * 0.85
            pts = _generate_tapered_cylinder(
                prox, dist, r_prox, r_dist, solid_end_l, shell_l, spacing, rng
            )

        body_names.append(inst["name"])
        positions_list.append(pts)
        grain_ids_list.append(np.full(pts.shape[0], body_id, dtype=np.int32))
        coms[inst["name"]] = pts.mean(axis=0)

    # Cup joints: parent bone end wraps child bone end.
    ball_cup_pairs = [
        ("pelvis_L", "dist", "femur_L", "prox", "hip_L"),
        ("pelvis_R", "dist", "femur_R", "prox", "hip_R"),
        ("scapula_L", "dist", "humerus_L", "prox", "shoulder_L"),
        ("scapula_R", "dist", "humerus_R", "prox", "shoulder_R"),
        ("vertebra_C1", "prox", "skull", "dist", "atlanto_occipital"),
    ]

    for parent_name, parent_end, child_name, child_end, joint_name in ball_cup_pairs:
        parent = next((i for i in instances if i["name"] == parent_name), None)
        child = next((i for i in instances if i["name"] == child_name), None)
        if parent is None or child is None:
            continue

        child_r = 0.5 * float(child["row"]["outer_diameter_lu"])
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
    rope_network = get_rope_network()
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
    # Ground plate.
    # ------------------------------------------------------------------
    plate_pts = _generate_ground_plate(height_lu, spacing, rng)
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
    }

    return (
        positions.astype(np.float32),
        velocities.astype(np.float32),
        pin_mask,
        grain_ids,
        body_names,
        derived,
    )
