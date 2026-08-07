"""
THE SPINE v2 run driver for LightEngine.

Standalone CLI:
    python LightEngine/demo_spine.py --ticks 8000 --tag spine_v2 [--control]

Writes:
    LightEngine/output/print_<tag>_log.txt  (or _control_log.txt)
    LightEngine/output/<tag>_begin.png / <tag>_end.png
"""

from __future__ import annotations

import sys
import os
import math
import time
import argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LightEngine import kernel, spine_structures
from LightEngine.constants import G, R_WALL, R_BOND, R_C, K_BOND, K_WALL, P_WALL, EPS, S_WALL, DT

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


def _min_pair_distance(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return float("inf")
    d = a[:, None, :] - b[None, :, :]
    return float(np.sqrt((d * d).sum(axis=2).min()))


def _union_find(n: int):
    parent = np.arange(n, dtype=np.int32)
    size = np.ones(n, dtype=np.int32)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
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
    roots = np.array([find(i) for i in range(n)])
    unique, sizes = np.unique(roots, return_counts=True)
    return len(unique), sizes


def _group_cluster_count(pos: np.ndarray, grain_ids: np.ndarray,
                         group_id: int, r_cut: float = R_C) -> int:
    idx = np.flatnonzero(grain_ids == group_id)
    if idx.size == 0:
        return 0
    return cluster_count_and_sizes(pos[idx], r_cut)[0]


def _draw_force_z(src: np.ndarray, dst: np.ndarray, eps: float = EPS) -> float:
    dpos = src[:, None, :] - dst[None, :, :]
    r2 = (dpos * dpos).sum(axis=2) + eps * eps
    fz = G * dpos[:, :, 2] / (r2 ** 1.5)
    return float(fz.sum())


def _rope_link_forces(pos: np.ndarray, grain_ids: np.ndarray,
                      rope_chain: np.ndarray) -> np.ndarray:
    rope = pos[grain_ids == 4].astype(np.float64)
    if rope.shape[0] < 2 or rope_chain.size < 2:
        return np.zeros(max(0, rope_chain.size - 1), dtype=np.float64)
    forces = np.zeros(rope_chain.size - 1, dtype=np.float64)
    for k in range(rope_chain.size - 1):
        i = rope_chain[k]
        j = rope_chain[k + 1]
        pi = rope[i]
        pj = rope[j]
        dpos = pj - pi
        r2 = float((dpos * dpos).sum())
        r = math.sqrt(r2)
        if r < 1e-12:
            forces[k] = 0.0
            continue
        u = dpos / r
        F = G * dpos / ((r2 + EPS * EPS) ** 1.5)
        if r < R_WALL:
            r_eff = math.sqrt(r2 + S_WALL * S_WALL)
            f_scalar = K_WALL * (R_WALL / r_eff) ** P_WALL / r_eff
            F -= f_scalar * u
        elif r <= R_BOND:
            f_scalar = K_BOND * (r - R_BOND) / (R_BOND * r)
            F += f_scalar * dpos
        forces[k] = float(np.dot(F, u))
    return forces


def _dump_frame(pos: np.ndarray, path: str, camera_pos=(25.0, 25.0, 25.0)):
    """Render the point set through ParticleEngine if available."""
    try:
        from ParticleEngine.gpu_pipeline import FullGPUPipeline
        from ParticleEngine.camera import FirstPersonCamera
    except Exception as e:
        print(f"[demo_spine] renderer not available: {e}")
        return

    try:
        from PIL import Image
    except Exception as e:
        print(f"[demo_spine] PIL not available: {e}")
        return

    n = pos.shape[0]
    pipe = FullGPUPipeline(bg=(0.01, 0.01, 0.05), base_scale=0.5)
    buffer = np.zeros((n, 28), dtype=np.float32)
    buffer[:, 0:3] = pos
    buffer[:, 3:6] = 0.0
    buffer[:, 6:9] = 0.0
    buffer[:, 9] = 1.0
    buffer[:, 10] = -1.0
    buffer[:, 11] = 3.0
    buffer[:, 16:19] = 0.9
    buffer[:, 19] = 0.9
    buffer[:, 20] = 0.04

    pipe.upload(buffer, term="light_seed")
    cam = FirstPersonCamera(
        position=camera_pos,
        yaw=math.atan2(-camera_pos[1], -camera_pos[0]),
        pitch=math.asin(-camera_pos[2] / max(np.linalg.norm(camera_pos), 1e-6)),
        fov=np.radians(60),
        near=0.1,
        far=1000.0,
    )
    params = cam.params(width=800, height=600)
    img = pipe.render_from_gpu(cam, params)
    Image.fromarray(img).save(path)


def _run_spine(pos, vel, pin_mask, grain_ids, derived, dt, ticks,
               tag, label):
    """Free-evolution spine protocol: pinned plate, sacrum base, saddle, droplet."""
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    plate_idx = np.flatnonzero(grain_ids == -1).astype(np.int32)
    sacrum_idx = np.flatnonzero(grain_ids == 0).astype(np.int32)
    saddle_idx = np.flatnonzero(grain_ids == 1).astype(np.int32)
    lumbar_idx = np.flatnonzero(grain_ids == 2).astype(np.int32)
    drop_idx = np.flatnonzero(grain_ids == 3).astype(np.int32)
    rope_idx = np.flatnonzero(grain_ids == 4).astype(np.int32)
    load_idx = np.flatnonzero(grain_ids == 5).astype(np.int32)

    muscle_face = lumbar_idx[derived["muscle_face_local"]]
    load_face = lumbar_idx[derived["load_face_local"]]
    saddle_top = saddle_idx[derived["saddle_top_local"]]
    lumbar_contact = lumbar_idx[derived["lumbar_contact_local"]]
    lumbar_side = lumbar_idx[derived["lumbar_side_local"]]
    lumbar_top = lumbar_idx[derived["lumbar_top_local"]]
    lintel = saddle_idx[derived["lintel_local"]]
    cheek_inner = saddle_idx[derived["cheek_inner_local"]]
    rope_chain = rope_idx[derived["rope_order_local"]]

    sacrum_bottom_local = derived["sacrum_bottom_local"]
    sacrum_bottom = sacrum_idx[sacrum_bottom_local]
    sacrum_top = sacrum_idx[derived["sacrum_top_local"]]
    sacrum_bottom0 = sim.pos[sacrum_bottom].copy()

    load_end_z0 = float(derived["load_end_z0"])
    d_eq = float(derived["d_eq"])
    theta_stop_muscle = float(derived.get("theta_stop_muscle", 0.0))
    theta_stop_load = float(derived.get("theta_stop_load", 0.0))

    plate_fz0 = _draw_force_z(sim.pos[plate_idx].astype(np.float64),
                              sim.pos[load_idx].astype(np.float64))
    acc_load_z0 = float(sim.acc[load_idx, 2].sum())
    print_contact = max(acc_load_z0 - plate_fz0, 1.0)

    sample_every = max(1, ticks // 40)

    metrics = {
        "tick": [],
        "load_gain": [],
        "angle": [],
        "gap": [],
        "lintel_gap": [],
        "cheek_gap": [],
        "plate_F": [],
        "contact": [],
        "clusters": [],
        "tip_to_drop": [],
        "apex_z": [],
        "rope_tension_frac": [],
        "rope_slack_frac": [],
        "rope_compression_frac": [],
        "rope_taut_links": [],
        "rope_max_compression": [],
        "sacrum_tilt": [],
        "base_migration": [],
    }

    def _sample(tick: int):
        plate_p = sim.pos[plate_idx].astype(np.float64)
        drop_p = sim.pos[drop_idx].astype(np.float64)
        saddle_p = sim.pos[saddle_idx].astype(np.float64)
        lumbar_p = sim.pos[lumbar_idx].astype(np.float64)
        load_p = sim.pos[load_idx].astype(np.float64)
        rope_p = sim.pos[rope_idx].astype(np.float64)

        load_c = lumbar_p[derived["load_face_local"]].mean(axis=0)
        muscle_c = lumbar_p[derived["muscle_face_local"]].mean(axis=0)
        load_gain = float(load_c[2] - load_end_z0)
        angle = float(math.degrees(math.atan2(
            load_c[2] - muscle_c[2], load_c[0] - muscle_c[0])))

        gap = _min_pair_distance(saddle_p[derived["saddle_top_local"]],
                                 lumbar_p[derived["lumbar_contact_local"]])
        lintel_gap = _min_pair_distance(saddle_p[derived["lintel_local"]],
                                        lumbar_p[derived["lumbar_top_local"]])
        cheek_gap = _min_pair_distance(saddle_p[derived["cheek_inner_local"]],
                                       lumbar_p[derived["lumbar_side_local"]])

        plate_force = float(np.abs(sim.acc[plate_idx, 2].sum()))
        plate_fz = _draw_force_z(plate_p, load_p)
        acc_load_z = float(sim.acc[load_idx, 2].sum())
        contact_ratio = (acc_load_z - plate_fz) / print_contact

        clusters = "/".join(str(_group_cluster_count(sim.pos, grain_ids, gid, R_C))
                            for gid in (0, 1, 2, 3, 4, 5))

        tip_to_drop = _min_pair_distance(lumbar_p[derived["muscle_face_local"]],
                                         drop_p)
        apex_z = float(drop_p[:, 2].max())

        link_forces = _rope_link_forces(sim.pos, grain_ids,
                                        derived["rope_order_local"])
        if link_forces.size > 0:
            rope_tension_frac = float(np.mean(link_forces > 0.5))
            rope_compression_frac = float(np.mean(link_forces < -0.5))
            rope_slack_frac = float(np.mean(np.abs(link_forces) <= 0.5))
            rope_taut_links = int(np.sum(link_forces > 0.5))
            rope_max_compression = float(np.maximum(-np.min(link_forces), 0.0))
        else:
            rope_tension_frac = rope_slack_frac = rope_compression_frac = 0.0
            rope_taut_links = 0
            rope_max_compression = 0.0

        bottom_c = sim.pos[sacrum_bottom].mean(axis=0)
        top_c = sim.pos[sacrum_top].mean(axis=0)
        vec = top_c - bottom_c
        sacrum_tilt = float(math.degrees(
            math.atan2(math.sqrt(vec[0] ** 2 + vec[1] ** 2), vec[2])))
        migration = float(np.max(np.linalg.norm(
            sim.pos[sacrum_bottom, :2] - sacrum_bottom0[:, :2], axis=1)))

        metrics["tick"].append(tick)
        metrics["load_gain"].append(load_gain)
        metrics["angle"].append(angle)
        metrics["gap"].append(gap)
        metrics["lintel_gap"].append(lintel_gap)
        metrics["cheek_gap"].append(cheek_gap)
        metrics["plate_F"].append(plate_force)
        metrics["contact"].append(contact_ratio)
        metrics["clusters"].append(clusters)
        metrics["tip_to_drop"].append(tip_to_drop)
        metrics["apex_z"].append(apex_z)
        metrics["rope_tension_frac"].append(rope_tension_frac)
        metrics["rope_slack_frac"].append(rope_slack_frac)
        metrics["rope_compression_frac"].append(rope_compression_frac)
        metrics["rope_taut_links"].append(rope_taut_links)
        metrics["rope_max_compression"].append(rope_max_compression)
        metrics["sacrum_tilt"].append(sacrum_tilt)
        metrics["base_migration"].append(migration)

        n_links = max(1, len(link_forces))
        print(f"[{label}] tick={tick:6d} | load_gain={load_gain:+.4f} | "
              f"angle={angle:7.2f}deg | "
              f"theta=[{math.degrees(theta_stop_load):7.2f},"
              f"{math.degrees(theta_stop_muscle):7.2f}]deg | "
              f"gap={gap:.4f} | lintel_gap={lintel_gap:.4f} | "
              f"cheek_gap={cheek_gap:.4f} | plate_F={plate_force:.2f} | "
              f"contact={contact_ratio:.3f} | clusters={clusters} | "
              f"tip_to_drop={tip_to_drop:.4f} | apex_z={apex_z:.4f} | "
              f"rope links T/S/C={rope_taut_links}/"
              f"{int(round(rope_slack_frac * n_links))}/"
              f"{int(round(rope_compression_frac * n_links))} "
              f"max_comp={rope_max_compression:.2f} | "
              f"sacrum_tilt={sacrum_tilt:.3f}deg | base_migration={migration:.4f}")

    print(f"\n[{label}] N={N} plate={len(plate_idx)} sacrum={len(sacrum_idx)} "
          f"saddle={len(saddle_idx)} lumbar={len(lumbar_idx)} "
          f"droplet={len(drop_idx)} rope={len(rope_idx)} load={len(load_idx)}")
    print(f"[{label}] dt={dt} ticks={ticks} sample_every={sample_every}\n")

    _dump_frame(sim.pos.copy(),
                os.path.join(OUTPUT_DIR, f"{label}_begin.png"))

    _sample(0)
    for tick in range(1, ticks + 1):
        sim.step(dt)
        if tick % sample_every == 0 or tick == ticks:
            _sample(tick)

    _dump_frame(sim.pos.copy(),
                os.path.join(OUTPUT_DIR, f"{label}_end.png"))
    return metrics


def _print_spine_verdict(metrics, derived: dict, label: str, control: bool):
    ticks = np.asarray(metrics["tick"], dtype=np.int32)
    load_gain = np.asarray(metrics["load_gain"], dtype=np.float64)
    angle = np.asarray(metrics["angle"], dtype=np.float64)
    gap = np.asarray(metrics["gap"], dtype=np.float64)
    lintel_gap = np.asarray(metrics["lintel_gap"], dtype=np.float64)
    cheek_gap = np.asarray(metrics["cheek_gap"], dtype=np.float64)
    plate_force = np.asarray(metrics["plate_F"], dtype=np.float64)
    contact_ratio = np.asarray(metrics["contact"], dtype=np.float64)
    sacrum_tilt = np.asarray(metrics["sacrum_tilt"], dtype=np.float64)
    base_migration = np.asarray(metrics["base_migration"], dtype=np.float64)
    rope_compression_frac = np.asarray(metrics["rope_compression_frac"],
                                       dtype=np.float64)
    rope_max_compression = np.asarray(metrics["rope_max_compression"],
                                      dtype=np.float64)

    d_eq = float(derived["d_eq"])
    s_wall = float(S_WALL)
    cap_hi = 2.0 * d_eq

    n = len(angle)
    last_n = max(1, int(round(0.20 * n)))
    settled_sign = int(np.sign(np.mean(angle[-last_n:])))

    R_true = float(derived.get("R_true", 0.0))
    if R_true > 1.0:
        predicted_sign = 1
    elif R_true < 1.0:
        predicted_sign = -1
    else:
        predicted_sign = 0
    balance_ok = (predicted_sign != 0 and settled_sign == predicted_sign)

    max_gain = float(load_gain.max())
    max_gain_idx = int(np.argmax(load_gain))
    max_gain_tick = int(ticks[max_gain_idx])

    if control:
        lift_ok = None
        hold_ok = max_gain <= 0.05
    else:
        lift_ok = max_gain >= 0.10
        hold_ok = None

    cluster_ok = all(all(part == "1" for part in s.split("/"))
                     for s in metrics["clusters"])

    mean_compression_frac = float(np.mean(rope_compression_frac))
    slack_ok = mean_compression_frac <= 0.20

    max_tilt = float(sacrum_tilt.max())
    max_migration = float(base_migration.max())
    frame_ok = (max_tilt <= 2.0) and (max_migration <= 0.5 * d_eq)

    gap_min = float(min(gap.min(), lintel_gap.min(), cheek_gap.min()))
    gap_max = float(max(gap.max(), lintel_gap.max(), cheek_gap.max()))
    capture_closed_ok = (gap_min >= s_wall) and (gap_max <= cap_hi)

    route = derived.get("route", "unknown")
    gate_passed = derived.get("gate_passed", False)

    print(f"\n[{label}] SPINE v2 FALSIFIERS (route={route}, gate_passed={gate_passed}):")
    if control:
        print(f"  (a) LIFT           : skipped (control)")
        print(f"  (b) HOLD           : {'PASS' if hold_ok else 'FAIL'}  "
              f"max load_gain={max_gain:.4f} at tick={max_gain_tick} (bar 0.0500)")
    else:
        print(f"  (a) LIFT           : {'PASS' if lift_ok else 'FAIL'}  "
              f"max load_gain={max_gain:.4f} at tick={max_gain_tick} (bar 0.1000)")
        print(f"  (b) HOLD           : skipped (main)")
    print(f"  (c) BALANCE        : {'PASS' if balance_ok else 'FAIL'}  "
          f"R_true={R_true:.3f} settled_sign={settled_sign} predicted={predicted_sign} "
          f"(last {last_n}/{n} samples)")
    print(f"  (d) INTEGRITY      : {'PASS' if cluster_ok else 'FAIL'}  "
          f"max clusters sacrum/saddle/lumbar/droplet/rope/load="
          f"{metrics['clusters'][-1]}")
    print(f"  (e) SLACK          : {'PASS' if slack_ok else 'FAIL'}  "
          f"mean rope compression fraction={mean_compression_frac:.2f} (bar 0.20)")
    print(f"  (f) FRAME          : {'PASS' if frame_ok else 'FAIL'}  "
          f"max sacrum_tilt={max_tilt:.3f}deg (bar 2.0) "
          f"max base_migration={max_migration:.4f} (bar {0.5*d_eq:.4f})")
    print(f"  (g) CAPTURE-CLOSED : {'PASS' if capture_closed_ok else 'FAIL'}  "
          f"capture gaps min={gap_min:.4f} max={gap_max:.4f} "
          f"band=[{s_wall:.4f}, {cap_hi:.4f}]")

    print(f"\n[{label}] ROPE TELEMETRY:")
    print(f"  min tip-to-droplet distance = {min(metrics['tip_to_drop']):.4f}")
    print(f"  droplet apex z range = [{min(metrics['apex_z']):.4f}, {max(metrics['apex_z']):.4f}]")
    print(f"  rope sign fractions: tension={np.mean(metrics['rope_tension_frac']):.2f} "
          f"slack={np.mean(metrics['rope_slack_frac']):.2f} "
          f"compression={mean_compression_frac:.2f}")
    print(f"  max taut links = {max(metrics['rope_taut_links'])} / {derived.get('n_rope', 0) - 1} "
          f"max compression magnitude = {max(rope_max_compression):.2f}")

    return {
        "lift_ok": lift_ok,
        "hold_ok": hold_ok,
        "balance_ok": balance_ok,
        "integrity_ok": cluster_ok,
        "slack_ok": slack_ok,
        "frame_ok": frame_ok,
        "capture_closed_ok": capture_closed_ok,
        "gate_passed": gate_passed,
        "route": route,
    }


def _run_one(control: bool, ticks: int, seed: int, tag: str) -> dict:
    pos, vel, pin_mask, grain_ids, derived = spine_structures.spine(
        control=control, seed=seed)
    N = pos.shape[0]
    dt = DT
    version = "control" if control else "main"
    label = f"{tag}_control" if control else tag
    log_name = f"print_{tag}_control_log.txt" if control else f"print_{tag}_log.txt"
    log_path = os.path.join(OUTPUT_DIR, log_name)

    n_rope = derived.get("n_rope", 0)
    route = derived.get("route", "unknown")
    gate_passed = derived.get("gate_passed", False)
    sacrum_ring_counts = derived.get("sacrum_ring_counts", [12] * 8)
    ring_desc = "/".join(str(n) for n in sacrum_ring_counts)

    print("=" * 70)
    print(f"THE KERNEL - SPINE v2 print run ({version})")
    print(f"N={N}, plate=6x6 ({derived['n_plate']} pinned), "
          f"sacrum=4x4x8 tapered solid-base column (rings {ring_desc}), "
          f"saddle=4x4x4+cheeks+lintel (PINNED), "
          f"lumbar=4x4x8 hollow tube, droplet=4^3 in well (PINNED), "
          f"load=4^3, rope=single-file x {n_rope} grains, route={route}, "
          f"seed={seed}, dt={dt}, ticks={ticks}, control={control}")
    print("-" * 70)
    print("STATEMENT: A bone's cross-section is its bending-moment diagram made solid")
    print("  -- the metaphysis carries the joint moment, the midshaft carries only")
    print("  axial load, so a tapered solid-to-hollow sacrum does not tear where v1 tore.")
    print("PREDICTION: The tapered sacrum stays ONE cluster both runs (v1 tore at tick 600);")
    print("  sacrum_tilt stays within 2deg; the downstream failures of v1 (capture gaps")
    print("  leaving the band) do not recur because the frame no longer leans.")
    print("FALSIFIERS:")
    print("  (a) LIFT      - main: lumbar far-end rises >= 0.10 lu")
    print("  (b) HOLD      - control: lumbar far-end rises <= 0.05 lu")
    print("  (c) BALANCE   - settled sign matches sign(R_true(0) - 1) both runs")
    print("  (d) INTEGRITY - one cluster each -- THE claim of this print")
    print("  (e) SLACK     - rope compression > 20% of samples = FAIL")
    print("  (f) FRAME     - sacrum axis stays within 2 deg of vertical,")
    print("                  base migration < 0.5*d_eq")
    print("  (g) CAPTURE-CLOSED - every capture gap stays within [S_WALL, 2*d_eq];")
    print("                       any lift-off escape = FAIL")
    print("THEORY-FALSIFIER: if the tapered sacrum still tears, the cushion kernel has no")
    print("  bending membrane at single-bone scale and the moment must go to TWO supports")
    print("  (the pelvis branches) -- record, do not patch.")
    print("=" * 70)
    print(f"\nDerived d_eq          = {derived['d_eq']:.5f}")
    print(f"Derived contact_x     = {derived['fulcrum_contact_point'][0]:.5f}")
    print(f"Derived R_true        = {derived['R_true']:.3f}")
    print(f"Derived theta_stop_muscle = {math.degrees(derived['theta_stop_muscle']):.2f} deg")
    print(f"Derived theta_stop_load   = {math.degrees(derived['theta_stop_load']):.2f} deg")
    print(f"Derived well_floor_z  = {derived['well_floor_z']:.5f}")
    print(f"Derived droplet_apex_z= {derived['droplet_apex_z']:.5f}")
    print(f"Derived n_rope        = {n_rope}")
    print(f"Derived lintel_bottom_z = {derived['lintel_bottom_z']:.5f}")
    print(f"Derived corner_rise   = {derived['corner_rise']:.5f}")

    # Taper derivation block
    F_tip = derived.get("F_tip", 0.0)
    M_max = derived.get("M_max", 0.0)
    extra_needed = derived.get("taper_extra_needed_base", 0.0)
    f_cushion = derived.get("taper_f_cushion", 0.0)
    lever_arm = derived.get("taper_arm_dim", 0.0)
    print(f"\nDerived sacrum taper (M(z) = F_tip * (H - z)):")
    print(f"  lumbar+load weight W        = {derived.get('taper_W', 0.0):.4f}")
    print(f"  lumbar+load COM x           = {derived.get('taper_x_com', 0.0):.4f}")
    print(f"  moment arm (COM - contact_x)= {derived.get('taper_arm', 0.0):.4f}")
    print(f"  sacrum height H             = {derived['sacrum_layers'] * derived['spacing']:.4f}")
    print(f"  derived F_tip               = {F_tip:.4f}")
    print(f"  derived M_max (base moment) = {M_max:.4f}")
    print(f"  cushion force scale         = {f_cushion:.4f}")
    print(f"  extra grains needed at base = {extra_needed:.4f} (budget [0, 4])")
    print(f"  ring grain counts (base->top)= {ring_desc}")
    if extra_needed >= 4.0:
        print("  TAPER NOTE: capacity check demands >=4 extra grains at base; using solid 4x4.")
    elif extra_needed <= 0.0:
        print("  TAPER NOTE: capacity check demands <=0 extra grains; using hollow shell.")
    else:
        print("  TAPER NOTE: normalized M(z)/M_max mapped linearly onto grain range [12, 16].")
    print()

    metrics = _run_spine(pos, vel, pin_mask, grain_ids, derived,
                         dt, ticks, tag, label)
    verdict = _print_spine_verdict(metrics, derived, label, control)
    print("=" * 70)
    return {"metrics": metrics, "derived": derived, "verdict": verdict}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Spine v2 print driver")
    parser.add_argument("--ticks", type=int, default=8000)
    parser.add_argument("--tag", type=str, default="spine_v2")
    parser.add_argument("--seed", type=int, default=20260807)
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args(argv)

    control = bool(args.control)
    label = f"{args.tag}_control" if control else args.tag
    log_name = f"print_{args.tag}_control_log.txt" if control else f"print_{args.tag}_log.txt"
    log_path = os.path.join(OUTPUT_DIR, log_name)

    tee = _Tee(log_path)
    old_stdout = sys.stdout
    sys.stdout = tee
    try:
        # Retry on CUDA OOM / memory contention without killing other processes.
        last_err = None
        for attempt in range(3):
            try:
                _run_one(control=control, ticks=args.ticks, seed=args.seed, tag=args.tag)
                break
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                is_oom = (
                    "cuda" in msg or
                    "out of memory" in msg or
                    "cumemalloc" in msg or
                    "runtimeerror" in msg and "memory" in msg
                )
                if is_oom and attempt < 2:
                    print(f"[demo_spine] CUDA/memory contention detected, "
                          f"waiting 60s before retry {attempt + 2}/3 ...")
                    time.sleep(60.0)
                    continue
                raise
        else:
            raise last_err if last_err else RuntimeError("spine v2 run failed")
    finally:
        sys.stdout = old_stdout
        tee.close()
    print(f"[demo_spine] log written to {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
