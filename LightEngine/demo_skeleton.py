"""
THE STANDING HUMAN v1 run driver for LightEngine.

Standalone CLI:
    python LightEngine/demo_skeleton.py --ticks 8000 --tag skeleton_v1 [--cut-ropes]

Writes:
    LightEngine/output/print_skeleton_v1_log.txt  (or _control_log.txt)
"""

from __future__ import annotations

import sys
import os
import math
import time
import argparse
from typing import Any

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LightEngine import kernel, skeleton_structures
from LightEngine.constants import (
    G, R_WALL, R_BOND, R_C, K_BOND, K_WALL, P_WALL, EPS, S_WALL, DT,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class _Tee:
    """Write to a file and to the original stdout at the same time."""

    def __init__(self, path: str):
        self.file = open(path, "w", encoding="utf-8")
        self.stdout = sys.stdout

    def write(self, text: str) -> int:
        self.file.write(text)
        self.stdout.write(text)
        return len(text)

    def flush(self):
        self.file.flush()
        self.stdout.flush()

    def close(self):
        self.file.close()


def _convex_hull_xy(points: np.ndarray) -> np.ndarray:
    """Gift-wrapping convex hull in the xy plane. Returns vertices in CCW order."""
    pts = np.asarray(points, dtype=np.float64)
    if pts.shape[0] <= 3:
        return pts
    # find leftmost point
    start = int(np.argmin(pts[:, 0]))
    hull = []
    p = start
    while True:
        hull.append(p)
        q = (p + 1) % pts.shape[0]
        for r in range(pts.shape[0]):
            cross = (pts[q, 0] - pts[p, 0]) * (pts[r, 1] - pts[p, 1]) - \
                    (pts[q, 1] - pts[p, 1]) * (pts[r, 0] - pts[p, 0])
            if cross < 0:
                q = r
        p = q
        if p == start:
            break
    return pts[hull]


def _point_in_polygon_xy(p: np.ndarray, poly: np.ndarray) -> bool:
    """Ray-casting point-in-polygon test in the xy plane."""
    x, y = float(p[0]), float(p[1])
    inside = False
    n = poly.shape[0]
    for i in range(n):
        x1, y1 = float(poly[i, 0]), float(poly[i, 1])
        x2, y2 = float(poly[(i + 1) % n, 0]), float(poly[(i + 1) % n, 1])
        if ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
        ):
            inside = not inside
    return inside


def _polygon_margin_distance(p: np.ndarray, poly: np.ndarray) -> float:
    """Signed distance from p to polygon edges: positive inside, negative outside."""
    x, y = float(p[0]), float(p[1])
    min_dist = float("inf")
    n = poly.shape[0]
    for i in range(n):
        x1, y1 = float(poly[i, 0]), float(poly[i, 1])
        x2, y2 = float(poly[(i + 1) % n, 0]), float(poly[(i + 1) % n, 1])
        dx = x2 - x1
        dy = y2 - y1
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy + 1e-12)))
        px = x1 + t * dx
        py = y1 + t * dy
        d = math.hypot(x - px, y - py)
        # sign from cross product
        cross = dx * (y - y1) - dy * (x - x1)
        if cross < 0:
            d = -d
        min_dist = min(min_dist, d)
    return min_dist


def _union_find(n: int):
    parent = np.arange(n, dtype=np.int32)
    size = np.ones(n, dtype=np.int32)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra = find(a)
        rb = find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    return find, union


def _pairwise_r2(pos: np.ndarray, chunk: int = 512):
    pos64 = pos.astype(np.float64)
    n = pos64.shape[0]
    sq = np.einsum("ij,ij->i", pos64, pos64)
    for lo in range(0, n, chunk):
        hi = min(lo + chunk, n)
        r2 = sq[lo:hi, None] + sq[None, :] - 2.0 * (pos64[lo:hi] @ pos64.T)
        yield lo, hi, r2


def cluster_count_and_sizes(pos: np.ndarray, r_cut: float) -> tuple[int, np.ndarray]:
    n = pos.shape[0]
    find, union = _union_find(n)
    rc2 = r_cut * r_cut
    for lo, hi, r2 in _pairwise_r2(pos):
        ii, jj = np.nonzero(r2 <= rc2)
        ii = ii + lo
        keep = ii < jj
        for a, b in zip(ii[keep], jj[keep]):
            union(int(a), int(b))
    roots = np.array([find(i) for i in range(n)], dtype=np.int32)
    unique, sizes = np.unique(roots, return_counts=True)
    return len(unique), sizes


def _body_clusters(pos: np.ndarray, grain_ids: np.ndarray,
                   body_id: int, r_cut: float = R_C) -> int:
    idx = np.flatnonzero(grain_ids == body_id)
    if idx.size == 0:
        return 0
    return cluster_count_and_sizes(pos[idx], r_cut)[0]


def _body_com(pos: np.ndarray, grain_ids: np.ndarray, body_id: int) -> np.ndarray:
    idx = np.flatnonzero(grain_ids == body_id)
    if idx.size == 0:
        return np.zeros(3, dtype=np.float64)
    return pos[idx].mean(axis=0).astype(np.float64)


def _capture_gap(pos: np.ndarray, grain_ids: np.ndarray,
                 body_names: list[str], joint: dict) -> float:
    """Minimum cup-to-child-end distance for a ball-cup joint."""
    cup_start, cup_end = joint["cup_indices"]
    cup_pts = pos[cup_start:cup_end]
    child_id = body_names.index(joint["child"])
    ball_pts = pos[grain_ids == child_id]
    if cup_pts.size == 0 or ball_pts.size == 0:
        return float("nan")
    # Only child grains near the joint center participate.
    center = joint["ball_center"]
    end_radius = 2.0 * skeleton_structures.SPACING_LU
    near = np.linalg.norm(ball_pts - center, axis=1) <= end_radius
    ball_end_pts = ball_pts[near]
    if ball_end_pts.size == 0:
        ball_end_pts = ball_pts
    diff = ball_end_pts[:, None, :] - cup_pts[None, :, :]
    r = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))
    return float(r.min())


def _rope_state(pos: np.ndarray, grain_ids: np.ndarray,
                body_names: list[str], rope_name: str, spacing: float):
    """Classify rope chain segments as tension / slack / compression."""
    rid = body_names.index(rope_name)
    pts = pos[grain_ids == rid]
    if pts.shape[0] < 2:
        return {"t": 0, "s": 0, "c": 0, "max_comp": 0.0}
    diffs = np.diff(pts, axis=0)
    seg_len = np.linalg.norm(diffs, axis=1)
    t = int(np.sum(seg_len > spacing * 1.15))
    c = int(np.sum(seg_len < spacing * 0.85))
    s = int(seg_len.shape[0] - t - c)
    max_comp = float(np.maximum(spacing - seg_len.min(), 0.0) / spacing) if c else 0.0
    return {"t": t, "s": s, "c": c, "max_comp": max_comp}


def _derive_loaded_ropes(derived: dict) -> set[str]:
    """Heuristic loaded-rope set: vertical ropes under the COM corridor."""
    from LightEngine.rope_network import get_rope_network

    height_lu = float(derived["height_lu"])
    loaded: set[str] = set()
    for r in get_rope_network():
        a = np.asarray(r["anchor_a_point"], dtype=np.float64) * height_lu
        b = np.asarray(r["anchor_b_point"], dtype=np.float64) * height_lu
        dz = b[2] - a[2]
        mid = 0.5 * (a + b)
        span = float(np.linalg.norm(b - a))
        vertical_frac = abs(dz) / (span + 1e-12)
        # Loaded if it spans a vertical distance, is mostly vertical, and lies
        # under the central COM column.
        if span > 0.05 * height_lu and vertical_frac > 0.7 and abs(mid[1]) < 0.15 * height_lu:
            loaded.add(f"rope_{r['name']}")
    return loaded


def _run_skeleton(pos, vel, pin_mask, grain_ids, body_names, derived,
                  dt, ticks, tag, label, cut_ropes: bool):
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    d_eq = float(derived["d_eq"])
    spacing = float(derived["spacing"])
    height_lu = float(derived["height_lu"])
    support_poly = _convex_hull_xy(np.asarray(derived["support_polygon"], dtype=np.float64)[:, :2])

    plate_id = body_names.index("ground_plate")
    plate_mask = grain_ids == plate_id
    non_plate_mask = ~plate_mask
    bone_ids = [i for i, n in enumerate(body_names)
                if not n.startswith("rope_") and n != "ground_plate"]
    rope_names = [n for n in body_names if n.startswith("rope_")]
    loaded_ropes = _derive_loaded_ropes(derived)

    # Leg length for the control fall threshold.
    leg_len_lu = 0.0
    for key in ("femur pair", "tibia pair"):
        row = next((r for r in derived.get("_table", []) if r["name"] == key), None)
        if row is not None:
            leg_len_lu += float(row["length_lu"])
    if leg_len_lu <= 0.0:
        # Fallback using scaling fractions if the table is not present.
        leg_len_lu = (0.245 + 0.25) * height_lu
    delta_fail = leg_len_lu * math.sin(math.radians(12.0))

    sample_every = 1000
    verdict_window_start = 1200

    metrics: dict[str, Any] = {
        "tick": [],
        "com_x": [],
        "com_y": [],
        "com_z": [],
        "com_over_support": [],
        "com_margin": [],
        "head_z": [],
        "max_clusters": [],
        "worst_body": [],
        "worst_capture_gap": [],
        "worst_joint": [],
        "rope_t": [],
        "rope_s": [],
        "rope_c": [],
        "rope_max_comp": [],
        "rope_worst": [],
        "plate_F": [],
    }

    def _sample(tick: int):
        plate_p = sim.pos[plate_mask]
        non_plate_p = sim.pos[non_plate_mask]

        if non_plate_p.shape[0] > 0:
            com = non_plate_p.mean(axis=0)
        else:
            com = np.zeros(3, dtype=np.float64)
        com_xy = com[:2]

        if support_poly.shape[0] >= 3:
            inside = _point_in_polygon_xy(com_xy, support_poly)
            margin = _polygon_margin_distance(com_xy, support_poly)
        else:
            inside = False
            margin = float("nan")

        # head height
        skull_id = body_names.index("skull") if "skull" in body_names else None
        head_z = 0.0
        if skull_id is not None:
            head_z = float(sim.pos[grain_ids == skull_id, 2].max())

        # per-bone clusters
        max_clusters = 1
        worst_body = "none"
        for bid in bone_ids:
            n_clust = _body_clusters(sim.pos, grain_ids, bid, R_C)
            if n_clust > max_clusters:
                max_clusters = n_clust
                worst_body = body_names[bid]

        # capture gaps
        worst_gap = float("nan")
        worst_joint_name = "none"
        for joint in derived["joints"]:
            gap = _capture_gap(sim.pos, grain_ids, body_names, joint)
            if math.isnan(worst_gap) or gap < worst_gap:
                worst_gap = gap
                worst_joint_name = joint["name"]

        # rope summary
        rt = rs = rc = 0
        max_comp = 0.0
        worst_rope = "none"
        for rname in rope_names:
            st = _rope_state(sim.pos, grain_ids, body_names, rname, spacing)
            rt += st["t"]
            rs += st["s"]
            rc += st["c"]
            if st["max_comp"] > max_comp:
                max_comp = st["max_comp"]
                worst_rope = rname

        # plate vertical reaction proxy
        plate_F = float(np.abs(sim.acc[plate_mask, 2].sum())) if plate_mask.any() else 0.0

        metrics["tick"].append(tick)
        metrics["com_x"].append(float(com[0]))
        metrics["com_y"].append(float(com[1]))
        metrics["com_z"].append(float(com[2]))
        metrics["com_over_support"].append(inside)
        metrics["com_margin"].append(margin)
        metrics["head_z"].append(head_z)
        metrics["max_clusters"].append(max_clusters)
        metrics["worst_body"].append(worst_body)
        metrics["worst_capture_gap"].append(worst_gap)
        metrics["worst_joint"].append(worst_joint_name)
        metrics["rope_t"].append(rt)
        metrics["rope_s"].append(rs)
        metrics["rope_c"].append(rc)
        metrics["rope_max_comp"].append(max_comp)
        metrics["rope_worst"].append(worst_rope)
        metrics["plate_F"].append(plate_F)

        print(f"[{label}] tick={tick:6d} | "
              f"COM=({com[0]:.3f},{com[1]:.3f},{com[2]:.3f}) "
              f"com_over_support={inside} margin={margin:.3f} | "
              f"head_z={head_z:.3f} | "
              f"clusters=max{max_clusters} worst={worst_body} | "
              f"capture_gap={worst_gap:.4f} worst_joint={worst_joint_name} | "
              f"rope links T/S/C={rt}/{rs}/{rc} max_comp={max_comp:.3f} worst={worst_rope} | "
              f"plate_F={plate_F:.2f}")

    print(f"\n[{label}] N={N} bones={derived['n_bones']} ropes={derived['n_ropes']} "
          f"plate={int(plate_mask.sum())} cut_ropes={cut_ropes}")
    print(f"[{label}] dt={dt} ticks={ticks} sample_every={sample_every}")
    print(f"[{label}] support_polygon_pts={support_poly.shape[0]} "
          f"delta_fail={delta_fail:.3f} loaded_ropes={len(loaded_ropes)}\n")

    cut_done = False
    com_at_cut = None
    fall_detected = False
    fall_tick = None

    _sample(0)
    for tick in range(1, ticks + 1):
        sim.step(dt)

        if cut_ropes and tick == verdict_window_start and not cut_done:
            # Remove all rope grains from the integrator state.
            rope_mask = np.zeros(N, dtype=bool)
            for rname in rope_names:
                rope_mask |= grain_ids == body_names.index(rname)
            live = ~rope_mask
            old_to_new = np.full(N, -1, dtype=np.int32)
            old_to_new[live] = np.arange(int(live.sum()))
            com_at_cut = float(sim.pos[live].mean(axis=0)[2])
            pos2 = sim.pos[live].copy()
            vel2 = sim.vel[live].copy()
            pin2 = pin_mask[live].copy()
            grain_ids2 = grain_ids[live].copy()
            sim = kernel.VelocityVerlet(int(live.sum()))
            sim.set_state(pos2, vel2)
            sim.set_pin_mask(pin2)
            sim.compute_acceleration()
            grain_ids = grain_ids2
            body_names = list(body_names)  # keep same list; ids still valid
            N = sim.n
            plate_mask = grain_ids == plate_id
            non_plate_mask = ~plate_mask
            rope_names = []
            # Remap cup indices to the new compact positions array.
            for joint in derived["joints"]:
                cs, ce = joint["cup_indices"]
                if old_to_new[cs] >= 0 and old_to_new[ce - 1] >= 0:
                    joint["cup_indices"] = (int(old_to_new[cs]), int(old_to_new[ce - 1]) + 1)
            cut_done = True
            print(f"[{label}] CUT ROPES at tick={tick}; {int(rope_mask.sum())} rope grains removed; "
                  f"com_z at cut={com_at_cut:.3f}")

        if cut_done and com_at_cut is not None and tick <= verdict_window_start + 600:
            cur_com_z = float(sim.pos[non_plate_mask].mean(axis=0)[2])
            drop = com_at_cut - cur_com_z
            if drop > delta_fail and not fall_detected:
                fall_detected = True
                fall_tick = tick

        if tick % sample_every == 0 or tick == ticks:
            _sample(tick)

    metrics["fall_detected"] = fall_detected
    metrics["fall_tick"] = fall_tick
    metrics["com_at_cut"] = com_at_cut
    metrics["loaded_ropes"] = sorted(loaded_ropes)
    metrics["delta_fail"] = delta_fail
    return metrics


def _print_skeleton_verdict(metrics: dict, derived: dict, label: str,
                            cut_ropes: bool) -> dict:
    ticks = np.asarray(metrics["tick"], dtype=np.int32)
    d_eq = float(derived["d_eq"])
    s_wall = float(S_WALL)

    verdict_start = 1200
    in_window = ticks >= verdict_start
    window_idx = np.flatnonzero(in_window)
    has_window = window_idx.size > 0

    # (a) INTEGRITY
    if has_window:
        win_clusters = np.asarray(metrics["max_clusters"], dtype=np.int32)[window_idx]
        max_clusters = int(np.max(win_clusters))
    else:
        max_clusters = int(np.max(metrics["max_clusters"])) if metrics["max_clusters"] else 1
    integrity_ok = max_clusters == 1

    # (b) CAPTURE
    gaps = np.asarray(metrics["worst_capture_gap"], dtype=np.float64)
    capture_ok = True
    if has_window:
        win_gaps = gaps[window_idx]
        capture_ok = bool(np.all((win_gaps >= s_wall) & (win_gaps <= d_eq)))

    # (c) FRAME / COM over support polygon
    com_ok = True
    margin_min = float("nan")
    if has_window:
        margins = np.asarray(metrics["com_margin"], dtype=np.float64)[window_idx]
        com_ok = bool(np.all(margins >= 0.0))
        margin_min = float(margins.min())
    else:
        com_ok = None

    # (d) ROPE
    rope_c_total = sum(metrics["rope_c"]) if metrics["rope_c"] else 0
    rope_ok = rope_c_total == 0

    # (e) STAND / head height
    head_z0 = float(metrics["head_z"][0]) if metrics["head_z"] else 0.0
    delta_stand = head_z0 * math.tan(math.radians(2.0)) + d_eq
    stand_ok = True
    if has_window:
        head_vals = np.asarray(metrics["head_z"], dtype=np.float64)[window_idx]
        stand_ok = bool(np.all(np.abs(head_vals - head_z0) <= delta_stand))

    # (f) CONTROL / FALL
    control_ok = None
    if cut_ropes:
        control_ok = bool(metrics.get("fall_detected", False))

    def _status(ok):
        if ok is None:
            return "UNCHECKED"
        return "PASS" if ok else "FAIL"

    print(f"\n[{label}] STANDING HUMAN v1 FALSIFIERS:")
    print(f"  (a) INTEGRITY      : {_status(integrity_ok)}  "
          f"max clusters={max_clusters} worst={metrics['worst_body'][-1]}")
    print(f"  (b) CAPTURE        : {_status(capture_ok)}  "
          f"capture gap band=[{s_wall:.4f}, {d_eq:.4f}] "
          f"min={gaps.min():.4f} max={gaps.max():.4f}")
    margin_str = f"{margin_min:.4f}" if not math.isnan(margin_min) else "n/a"
    print(f"  (c) FRAME          : {_status(com_ok)}  "
          f"COM margin min={margin_str} (bar >= 0.0)")
    print(f"  (d) ROPE           : {_status(rope_ok)}  "
          f"total compression samples={rope_c_total}")
    print(f"  (e) STAND          : {_status(stand_ok)}  "
          f"head_z0={head_z0:.3f} band=+/-{delta_stand:.3f} "
          f"range=[{min(metrics['head_z']):.3f}, {max(metrics['head_z']):.3f}]")
    if cut_ropes:
        print(f"  (f) CONTROL (FALL) : {_status(control_ok)}  "
              f"fall_detected={metrics.get('fall_detected')} "
              f"fall_tick={metrics.get('fall_tick')} "
              f"delta_fail={metrics.get('delta_fail', 0.0):.3f}")
    else:
        print(f"  (f) CONTROL (FALL) : skipped (main)")

    # Worst-offender lists.
    print(f"\n[{label}] WORST OFFENDERS:")
    body_offenders: dict[str, int] = {}
    for name, cl in zip(metrics["worst_body"], metrics["max_clusters"]):
        if cl > 1:
            body_offenders[name] = max(body_offenders.get(name, 0), cl)
    top_bodies = sorted(body_offenders.items(), key=lambda x: -x[1])[:3]
    print("  bodies by max clusters:", ", ".join(f"{n}({c})" for n, c in top_bodies) or "none")

    joint_offenders: dict[str, float] = {}
    for name, gap in zip(metrics["worst_joint"], metrics["worst_capture_gap"]):
        if not math.isnan(gap):
            joint_offenders[name] = min(joint_offenders.get(name, float("inf")), gap)
    top_joints = sorted(joint_offenders.items(), key=lambda x: x[1])[:3]
    print("  joints by smallest capture gap:", ", ".join(f"{n}({g:.4f})" for n, g in top_joints) or "none")

    rope_offenders: dict[str, float] = {}
    for name, comp in zip(metrics["rope_worst"], metrics["rope_max_comp"]):
        if comp > 0.0:
            rope_offenders[name] = max(rope_offenders.get(name, 0.0), comp)
    top_ropes = sorted(rope_offenders.items(), key=lambda x: -x[1])[:3]
    print("  ropes by max compression:", ", ".join(f"{n}({c:.3f})" for n, c in top_ropes) or "none")

    print(f"\n[{label}] ROPE TELEMETRY:")
    print(f"  loaded rope set ({len(metrics.get('loaded_ropes', []))}): "
          f"{', '.join(metrics.get('loaded_ropes', []))}")
    print(f"  total link samples: T={sum(metrics['rope_t'])} S={sum(metrics['rope_s'])} "
          f"C={sum(metrics['rope_c'])}")
    print(f"  max rope compression = {max(metrics['rope_max_comp']):.3f}")

    return {
        "integrity_ok": integrity_ok,
        "capture_ok": capture_ok,
        "frame_ok": com_ok,
        "rope_ok": rope_ok,
        "stand_ok": stand_ok,
        "control_ok": control_ok,
    }


def _run_one(cut_ropes: bool, ticks: int, seed: int, tag: str) -> dict:
    pos, vel, pin_mask, grain_ids, body_names, derived = \
        skeleton_structures.build_skeleton(seed=seed)
    N = pos.shape[0]
    dt = DT
    version = "control" if cut_ropes else "main"
    label = f"{tag}_control" if cut_ropes else tag
    log_name = f"print_{tag}_control_log.txt" if cut_ropes else f"print_{tag}_log.txt"
    log_path = os.path.join(OUTPUT_DIR, log_name)

    print("=" * 70)
    print(f"THE KERNEL - STANDING HUMAN v1 print run ({version})")
    print(f"N={N}, bones={derived['n_bones']}, ropes={derived['n_ropes']}, "
          f"plate={derived['plate_grains']} pinned, seed={seed}, dt={dt}, "
          f"ticks={ticks}, cut_ropes={cut_ropes}")
    print("-" * 70)
    print("STATEMENT: The 206-bone skeleton stands because its printed geometry routes")
    print("  the whole body weight to the ground through bones in compression and")
    print("  ropes in tension. Standing is a property of the frame, not of any muscle.")
    print("PREDICTION: During the verdict window every bone stays one cluster and inside")
    print("  its derived positional band; every capture gap stays inside [S_WALL, d_eq];")
    print("  the COM projects inside the foot-bone support polygon; required ropes stay")
    print("  taut; the head height stays within the standing band.")
    print("FALSIFIERS:")
    print("  (a) INTEGRITY - per bone: no body splits into >=2 clusters in window")
    print("  (b) CAPTURE   - every cup/ball gap stays within [S_WALL, d_eq]")
    print("  (c) FRAME     - COM of non-ground grains stays over the support polygon")
    print("  (d) ROPE      - loaded ropes taut-or-slack, never compressed")
    print("  (e) STAND     - head height stays within print_z +/- H_head*tan(2deg)+d_eq")
    print("  (f) CONTROL   - cut ropes at tick 1200; FAIL if COM does not drop >")
    print("                  L_leg*sin(12deg) within 600 ticks")
    print("=" * 70)
    print(f"\nDerived d_eq       = {derived['d_eq']:.5f}")
    print(f"Derived spacing    = {derived['spacing']:.5f}")
    print(f"Derived height_lu  = {derived['height_lu']:.2f}")
    print(f"Derived lam        = {derived['lam']:.6e} m/lu")
    print(f"Derived total      = {derived['actual_total']}")
    print(f"Derived upgrade_groups = {', '.join(derived['upgrade_groups'])}")

    metrics = _run_skeleton(pos, vel, pin_mask, grain_ids, body_names, derived,
                            dt, ticks, tag, label, cut_ropes)
    verdict = _print_skeleton_verdict(metrics, derived, label, cut_ropes)
    print("=" * 70)
    return {"metrics": metrics, "derived": derived, "verdict": verdict}


def main(argv=None):
    parser = argparse.ArgumentParser(description="StandingHuman v1 print driver")
    parser.add_argument("--ticks", type=int, default=8000)
    parser.add_argument("--tag", type=str, default="skeleton_v1")
    parser.add_argument("--seed", type=int, default=20260807)
    parser.add_argument("--cut-ropes", action="store_true")
    args = parser.parse_args(argv)

    cut_ropes = bool(args.cut_ropes)
    label = f"{args.tag}_control" if cut_ropes else args.tag
    log_name = f"print_{args.tag}_control_log.txt" if cut_ropes else f"print_{args.tag}_log.txt"
    log_path = os.path.join(OUTPUT_DIR, log_name)

    tee = _Tee(log_path)
    old_stdout = sys.stdout
    sys.stdout = tee
    try:
        last_err = None
        for attempt in range(3):
            try:
                _run_one(cut_ropes=args.cut_ropes, ticks=args.ticks,
                         seed=args.seed, tag=args.tag)
                break
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                is_oom = (
                    "cuda" in msg or
                    "out of memory" in msg or
                    "cumemalloc" in msg or
                    ("runtimeerror" in msg and "memory" in msg)
                )
                if is_oom and attempt < 2:
                    print(f"[demo_skeleton] CUDA/memory contention detected, "
                          f"waiting 60s before retry {attempt + 2}/3 ...")
                    time.sleep(60.0)
                    continue
                raise
        else:
            raise last_err if last_err else RuntimeError("skeleton v1 run failed")
    finally:
        sys.stdout = old_stdout
        tee.close()
    print(f"[demo_skeleton] log written to {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
