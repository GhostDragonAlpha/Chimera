"""
theSpine v1 structure printer for LightEngine.

A grounded two-vertebra frame: pinned plate, vertical sacrum, captured saddle
with cheeks+lintel, horizontal lumbar, anchored muscle droplet, single-file
rope tendon, and load block.  The full-arc static gate is evaluated honestly;
if muscle-dominance is unreachable the build records gate_passed=False and
falls back to the best-effort contact, exactly like theLeg v3.
"""

from __future__ import annotations

import math
import numpy as np

from LightEngine import kernel
from LightEngine.constants import (
    G, R_WALL, R_BOND, R_C, K_BOND, K_WALL, P_WALL, EPS, S_WALL, DT,
)

TENDON_D_EQ = 0.0484


def _draw_force_z(src: np.ndarray, dst: np.ndarray, eps: float = EPS) -> float:
    """Sum of the z-component of softened-DRAW force that src exerts on dst."""
    dpos = src[:, None, :] - dst[None, :, :]
    r2 = (dpos * dpos).sum(axis=2) + eps * eps
    fz = G * dpos[:, :, 2] / (r2 ** 1.5)
    return float(fz.sum())


def _R_true_at_print(pos: np.ndarray,
                     grain_ids: np.ndarray,
                     contact_point: np.ndarray,
                     pin_mask: np.ndarray) -> tuple[float, float, float]:
    """
    Kernel static torque ratio about the fulcrum contact point.
    Only FREE grains (not pinned, not the world plate) generate torque.
    Sign convention: muscle-side-down torque is positive.
    Returns (R_true, tau_pos, tau_neg).
    """
    acc = kernel.compute_forces(
        pos.astype(np.float32),
        np.zeros_like(pos, dtype=np.float32),
        use_cuda=False,
    )
    pos64 = np.asarray(pos, dtype=np.float64)
    acc64 = np.asarray(acc, dtype=np.float64)
    cp = np.asarray(contact_point, dtype=np.float64)

    free = (grain_ids != -1) & (~pin_mask)
    r = pos64[free] - cp
    F = acc64[free]
    tau_z = r[:, 0] * F[:, 2] - r[:, 2] * F[:, 0]

    tau_pos = float(np.maximum(tau_z, 0.0).sum())
    tau_neg = float(np.maximum(-tau_z, 0.0).sum())
    if tau_neg <= 0.0:
        R_true = float("inf")
    else:
        R_true = tau_pos / tau_neg
    return R_true, tau_pos, tau_neg


def _hollow_ring(side: int, d: float) -> np.ndarray:
    """Return the (n,2) cross-section of a one-grain-thick square shell."""
    off = (np.arange(side, dtype=np.float64) - (side - 1) / 2.0) * d
    gx, gy = np.meshgrid(off, off, indexing="ij")
    shell = ~((np.abs(gx) <= 0.5 * d + 1e-12) & (np.abs(gy) <= 0.5 * d + 1e-12))
    return np.stack([gx[shell], gy[shell]], axis=1)


def _min_pair_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Minimum distance between two point clouds."""
    if a.size == 0 or b.size == 0:
        return float("inf")
    d = a[:, None, :] - b[None, :, :]
    return float(np.sqrt((d * d).sum(axis=2).min()))


def spine(control: bool = False, seed: int = 0) -> tuple:
    """
    Build theSpine v1.

    Returns (positions, velocities, pin_mask, grain_ids, derived).
    Grain ids: plate=-1, sacrum=0, saddle=1, lumbar=2, droplet=3, rope=4,
    load=5.
    """
    rng = np.random.default_rng(seed)
    d = 0.05
    d_eq = TENDON_D_EQ
    s = 4
    n_ring = 12
    sacrum_layers = 8
    lumbar_layers = 8
    drop_side = 4
    margin = 0.10
    theta_max = math.radians(120.0)

    ring_xy = _hollow_ring(s, d)
    tube_half_width = (s - 1) / 2.0 * d
    L = (lumbar_layers - 1) * d

    # --- Pinned ground plate 6x6 at z = 0 ---
    plate_side = 6
    n_plate = plate_side * plate_side
    p_off = (np.arange(plate_side, dtype=np.float64)
             - (plate_side - 1) / 2.0) * d
    px, py = np.meshgrid(p_off, p_off, indexing="ij")
    plate_pos = np.stack([px.ravel(), py.ravel(),
                          np.zeros(n_plate, dtype=np.float64)], axis=1)

    # --- Sacrum: vertical 4x4x8 hollow tube ---
    sacrum_z0 = d_eq
    sacrum_z_off = np.arange(sacrum_layers, dtype=np.float64) * d + sacrum_z0
    sacrum_pos = np.zeros((sacrum_layers * n_ring, 3), dtype=np.float64)
    for i, z in enumerate(sacrum_z_off):
        lo = i * n_ring
        hi = lo + n_ring
        sacrum_pos[lo:hi, 0] = ring_xy[:, 0]
        sacrum_pos[lo:hi, 1] = ring_xy[:, 1]
        sacrum_pos[lo:hi, 2] = z
    n_sacrum = sacrum_pos.shape[0]
    sacrum_top_z = float(sacrum_z_off[-1])
    sacrum_bottom_z = float(sacrum_z_off[0])

    # --- Saddle block 4x4x4 on sacrum top ---
    f_off = (np.arange(s, dtype=np.float64) - (s - 1) / 2.0) * d
    block_bottom_z = sacrum_top_z + d_eq
    block_z_off = np.arange(s, dtype=np.float64) * d + block_bottom_z
    block_top_z = float(block_z_off[-1])

    # --- Cheeks and lintel (closed capture) ---
    cheek_y_center = tube_half_width + d_eq + d / 2.0
    corner_rise = (math.sqrt(2.0) - 1.0) * 0.10
    lintel_bottom_z = (block_top_z + d_eq) + (s - 1) * d + corner_rise + d_eq
    # cheek height: integer layers, stop short of lintel to avoid overlap
    n_cheek_z = max(3, int(math.floor((lintel_bottom_z - block_top_z) / d)) - 1)
    outer_y = cheek_y_center + d / 2.0
    n_lintel_y = max(4, 2 * int(math.ceil(outer_y / d)) + 1)

    # Droplet well floor chosen so the muscle-side stop is a reasonable angle.
    # attach point starts at the lumbar underside, exactly over the saddle top.
    lumbar_bottom_z = block_top_z + d_eq
    attach_z0 = lumbar_bottom_z - d_eq  # = block_top_z = saddle contact height
    target_attach_apex_sep = 0.10  # derived small-swing clearance
    droplet_apex_z = attach_z0 - target_attach_apex_sep
    well_floor_z = droplet_apex_z - (drop_side - 1) * d - d_eq
    muscle_tip_x = -0.30  # beside the sacrum base, outside its cross-section

    def _build_no_jitter(contact_x: float) -> np.ndarray:
        """Assemble all grains for a candidate contact_x."""
        # saddle block
        bx = f_off + contact_x
        bxg, byg, bzg = np.meshgrid(bx, f_off, block_z_off, indexing="ij")
        block_pos = np.stack([bxg.ravel(), byg.ravel(), bzg.ravel()], axis=1)

        # cheeks
        cheek_z_off = np.arange(n_cheek_z, dtype=np.float64) * d + block_top_z
        cxg, cyg, czg = np.meshgrid(
            bx, np.array([cheek_y_center]), cheek_z_off, indexing="ij")
        cheek_plus = np.stack([cxg.ravel(), cyg.ravel(), czg.ravel()], axis=1)
        cheek_minus = cheek_plus.copy()
        cheek_minus[:, 1] = -cheek_y_center
        cheek_pos = np.vstack([cheek_plus, cheek_minus])

        # lintel
        lintel_y_off = (np.arange(n_lintel_y, dtype=np.float64)
                        - (n_lintel_y - 1) / 2.0) * d
        lx, ly = np.meshgrid(bx, lintel_y_off, indexing="ij")
        lintel_pos = np.stack([
            lx.ravel(), ly.ravel(),
            np.full(lx.size, lintel_bottom_z, dtype=np.float64)
        ], axis=1)
        saddle_pos = np.vstack([block_pos, cheek_pos, lintel_pos])

        # lumbar: horizontal, near end at x=0, far end at x=L
        lumbar_pos = np.zeros((lumbar_layers * n_ring, 3), dtype=np.float64)
        x_off = np.arange(lumbar_layers, dtype=np.float64) * d
        for i, x in enumerate(x_off):
            lo = i * n_ring
            hi = lo + n_ring
            lumbar_pos[lo:hi, 0] = x
            lumbar_pos[lo:hi, 1] = ring_xy[:, 0]
            lumbar_pos[lo:hi, 2] = ring_xy[:, 1] + lumbar_bottom_z + tube_half_width
        lumbar_top_z = float(lumbar_pos[:, 2].max())

        # droplet pinned in well
        drop_off = (np.arange(drop_side, dtype=np.float64)
                    - (drop_side - 1) / 2.0) * d
        drop_x = drop_off + muscle_tip_x
        drop_z = np.arange(drop_side, dtype=np.float64) * d + well_floor_z + d_eq
        dx, dy, dz = np.meshgrid(drop_x, drop_off, drop_z, indexing="ij")
        droplet_pos = np.stack([dx.ravel(), dy.ravel(), dz.ravel()], axis=1)

        # load block resting on lumbar far end
        load_x = f_off + L
        load_z = np.arange(drop_side, dtype=np.float64) * d + lumbar_top_z + d_eq
        lx, ly, lz = np.meshgrid(load_x, f_off, load_z, indexing="ij")
        load_pos = np.stack([lx.ravel(), ly.ravel(), lz.ravel()], axis=1)

        # rope: single-file chain from droplet apex (+d_eq) to lumbar underside
        anchor = np.array([float(muscle_tip_x), 0.0,
                           float(droplet_apex_z + d_eq)], dtype=np.float64)
        attach0 = np.array([0.0, 0.0, float(attach_z0)], dtype=np.float64)
        span_vec = attach0 - anchor
        span_len = float(np.linalg.norm(span_vec))
        n_chain = max(2, int(np.floor(span_len / d)) + 1)
        chain_pos = anchor + np.linspace(0.0, 1.0, n_chain)[:, None] * span_vec

        return np.vstack([
            plate_pos, sacrum_pos, saddle_pos, lumbar_pos,
            droplet_pos, chain_pos, load_pos,
        ]).astype(np.float64)

    def _assemble(contact_x: float) -> tuple:
        pos0 = _build_no_jitter(contact_x)
        N = pos0.shape[0]
        # count each component by geometry
        n_block = s ** 3
        n_cheek = 2 * s * n_cheek_z
        n_lintel = s * n_lintel_y
        n_saddle = n_block + n_cheek + n_lintel
        n_lumbar = lumbar_layers * n_ring
        n_drop = drop_side ** 3
        # rope count from build
        n_rope = N - (n_plate + n_sacrum + n_saddle + n_lumbar + n_drop + drop_side ** 3)

        grain_ids = np.empty(N, dtype=np.int32)
        grain_ids[:n_plate] = -1
        grain_ids[n_plate:n_plate + n_sacrum] = 0
        grain_ids[n_plate + n_sacrum:n_plate + n_sacrum + n_saddle] = 1
        grain_ids[n_plate + n_sacrum + n_saddle:
                  n_plate + n_sacrum + n_saddle + n_lumbar] = 2
        grain_ids[n_plate + n_sacrum + n_saddle + n_lumbar:
                  n_plate + n_sacrum + n_saddle + n_lumbar + n_drop] = 3
        grain_ids[n_plate + n_sacrum + n_saddle + n_lumbar + n_drop:
                  n_plate + n_sacrum + n_saddle + n_lumbar + n_drop + n_rope] = 4
        grain_ids[n_plate + n_sacrum + n_saddle + n_lumbar + n_drop + n_rope:] = 5

        pin_mask = np.zeros(N, dtype=bool)
        pin_mask[:n_plate] = True
        # pin sacrum bottom face (z == sacrum_bottom_z)
        sacrum_start = n_plate
        sacrum_bottom_mask = np.abs(
            pos0[sacrum_start:sacrum_start + n_sacrum, 2] - sacrum_bottom_z) <= 1e-3
        pin_mask[sacrum_start:sacrum_start + n_sacrum][sacrum_bottom_mask] = True
        # saddle body (block + cheeks + lintel) pinned
        saddle_start = n_plate + n_sacrum
        pin_mask[saddle_start:saddle_start + n_saddle] = True
        # droplet pinned
        drop_start = n_plate + n_sacrum + n_saddle + n_lumbar
        pin_mask[drop_start:drop_start + n_drop] = True

        return pos0, grain_ids, pin_mask, n_saddle, n_rope

    # --- Derive end-stops ---
    def _derive_theta_muscle(contact_x: float) -> float:
        rel_x = -contact_x
        target_z = droplet_apex_z + d_eq
        dz = attach_z0 - target_z
        if contact_x <= 0.0:
            return theta_max
        ratio = dz / contact_x
        if ratio >= 1.0:
            return math.radians(90.0)
        return math.asin(max(0.0, ratio))

    def _z_of_point(rel: np.ndarray, theta: float, cp_z: float) -> float:
        c = math.cos(theta)
        s = math.sin(theta)
        return cp_z + rel[0] * s + rel[2] * c

    def _derive_theta_load(contact_x: float, n_samples: int = 101) -> float:
        cp = np.array([contact_x, 0.0, block_top_z], dtype=np.float64)
        # lintel gap as function of theta (over the captured near-end top)
        tmp_pos, gids, pmask, n_saddle, n_rope = _assemble(contact_x)
        lumbar_start = n_plate + n_sacrum + n_saddle
        lumbar_idx = np.arange(lumbar_start, lumbar_start + lumbar_layers * n_ring)
        lumbar_p = tmp_pos[lumbar_idx]
        order = np.argsort(lumbar_p[:, 0])
        muscle_local = order[:n_ring]
        top_mask = np.abs(lumbar_p[muscle_local, 2]
                          - lumbar_p[muscle_local, 2].max()) <= 1e-3
        rel_top = lumbar_p[muscle_local][top_mask] - cp
        saddle_start = n_plate + n_sacrum
        saddle_p = tmp_pos[saddle_start:saddle_start + n_saddle]
        lintel_mask = np.abs(saddle_p[:, 2] - lintel_bottom_z) <= 1e-3
        lintel_p = saddle_p[lintel_mask]

        load_start = n_plate + n_sacrum + n_saddle + lumbar_layers * n_ring + drop_side ** 3 + n_rope
        load_p = tmp_pos[load_start:]
        load_bottom_z0 = float(load_p[:, 2].min())
        rel_load = np.array([L - contact_x, 0.0, load_bottom_z0 - block_top_z])

        thetas = np.linspace(0.0, -theta_max, n_samples)
        for theta in thetas[1:]:
            # top corner max z
            rot_top = rel_top.copy()
            c = math.cos(theta)
            s = math.sin(theta)
            rot_top[:, 0] = rel_top[:, 0] * c - rel_top[:, 2] * s
            rot_top[:, 2] = rel_top[:, 0] * s + rel_top[:, 2] * c
            top_z_max = float((rot_top + cp).max(axis=0)[2])
            lintel_gap = lintel_bottom_z - top_z_max

            load_z = _z_of_point(rel_load, theta, block_top_z)
            load_gap = load_z - d_eq

            if lintel_gap <= d_eq or load_gap <= 0.0:
                return float(theta)
        return -theta_max

    # --- Full-arc gate ---
    def _full_arc_R_true(contact_x: float, n_theta: int = 25) -> dict:
        pos0, gids, pmask, n_saddle, n_rope = _assemble(contact_x)
        theta_muscle = _derive_theta_muscle(contact_x)
        theta_load = _derive_theta_load(contact_x)
        thetas = np.linspace(theta_load, theta_muscle, n_theta)
        cp = np.array([float(contact_x), 0.0, float(block_top_z)], dtype=np.float64)

        # component boundaries
        sacrum_start = n_plate
        saddle_start = n_plate + n_sacrum
        lumbar_start = saddle_start + n_saddle
        drop_start = lumbar_start + lumbar_layers * n_ring
        rope_start = drop_start + drop_side ** 3
        load_start = rope_start + n_rope

        lumbar_idx = np.arange(lumbar_start, lumbar_start + lumbar_layers * n_ring)
        load_idx = np.arange(load_start, load_start + drop_side ** 3)
        rope_idx = np.arange(rope_start, rope_start + n_rope)

        anchor = np.array([float(muscle_tip_x), 0.0,
                           float(droplet_apex_z + d_eq)], dtype=np.float64)
        rel_attach = np.array([-contact_x, 0.0, 0.0], dtype=np.float64)

        R_taut = np.empty(n_theta, dtype=np.float64)
        R_slack = np.empty(n_theta, dtype=np.float64)

        for i, theta in enumerate(thetas):
            pos = pos0.copy()
            c = math.cos(theta)
            s = math.sin(theta)

            # rotate lumbar and load about cp
            for idx in (lumbar_idx, load_idx):
                rel = pos[idx] - cp[None, :]
                rot = rel.copy()
                rot[:, 0] = rel[:, 0] * c - rel[:, 2] * s
                rot[:, 2] = rel[:, 0] * s + rel[:, 2] * c
                pos[idx] = rot + cp[None, :]

            attach = np.array([
                cp[0] + rel_attach[0] * c - rel_attach[2] * s,
                0.0,
                cp[2] + rel_attach[0] * s + rel_attach[2] * c,
            ], dtype=np.float64)

            # taut rope
            axis = attach - anchor
            Lr = float(np.linalg.norm(axis))
            if Lr < 1e-9:
                Lr = 1e-9
            for li in range(n_rope):
                t = li / max(1, n_rope - 1.0)
                pos[rope_idx[li]] = anchor + t * axis

            R_taut[i], _, _ = _R_true_at_print(pos, gids, cp, pmask)

            # slack rope: remove its pull
            pos_slack = pos.copy()
            pos_slack[rope_idx] = np.array([0.0, 0.0, 1e6], dtype=np.float64)
            R_slack[i], _, _ = _R_true_at_print(pos_slack, gids, cp, pmask)

        return {
            "theta_load": theta_load,
            "theta_muscle": theta_muscle,
            "thetas": thetas,
            "R_taut": R_taut,
            "R_slack": R_slack,
        }

    # --- Scan for gate ---
    cx_min = tube_half_width + 1e-9
    cx_max = L - margin
    n_contact = 101
    xs = np.linspace(cx_min, cx_max, n_contact)

    strict_ok = False
    chosen_cx = None
    chosen_trace = None
    chosen_route = None

    for cx in xs:
        trace = _full_arc_R_true(cx)
        if not control:
            if float(np.min(trace["R_taut"])) >= 1.0:
                strict_ok = True
                chosen_cx = float(cx)
                chosen_trace = trace
                chosen_route = "full-arc"
                break
        else:
            R0 = float(trace["R_slack"][0])
            if 0.5 <= R0 <= 1.0:
                strict_ok = True
                chosen_cx = float(cx)
                chosen_trace = trace
                chosen_route = "full-arc"
                break

    if not strict_ok:
        # best-effort fallback
        best_candidates = []
        for cx in xs:
            trace = _full_arc_R_true(cx)
            if control:
                R0 = float(trace["R_slack"][0])
                if 0.5 <= R0 <= 1.0:
                    cost = abs(R0 - 0.75)
                elif R0 < 0.5:
                    cost = 1.0 + (0.5 - R0)
                else:
                    cost = 1.0 + (R0 - 1.0)
                if trace["theta_muscle"] < math.radians(5.0):
                    cost += 10.0
            else:
                Rmin = float(np.min(trace["R_taut"]))
                cost = 1.0 - min(1.0, Rmin)
                if trace["theta_muscle"] < math.radians(5.0):
                    cost += 10.0
            best_candidates.append((cost, float(cx), trace))
        best = min(best_candidates, key=lambda x: x[0])
        chosen_cx = best[1]
        chosen_trace = best[2]
        chosen_route = "best-effort"

    if chosen_cx is None:
        raise RuntimeError("spine v1 gate failed unexpectedly")

    # --- Final assembly at chosen contact ---
    pos, grain_ids, pin_mask, n_saddle, n_rope = _assemble(chosen_cx)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter

    # boundaries
    saddle_start = n_plate + n_sacrum
    lumbar_start = saddle_start + n_saddle
    drop_start = lumbar_start + lumbar_layers * n_ring
    rope_start = drop_start + drop_side ** 3
    load_start = rope_start + n_rope

    # face indices for telemetry
    sacrum_idx = np.arange(n_plate, n_plate + n_sacrum)
    sacrum_bottom_local = np.flatnonzero(
        np.abs(pos[sacrum_idx, 2] - sacrum_bottom_z) <= 1e-3)
    sacrum_top_local = np.flatnonzero(
        np.abs(pos[sacrum_idx, 2] - sacrum_top_z) <= 1e-3)

    lumbar_idx = np.arange(lumbar_start, lumbar_start + lumbar_layers * n_ring)
    lumbar_order = np.argsort(pos[lumbar_idx, 0])
    muscle_face_local = lumbar_order[:n_ring].astype(np.int32)
    load_face_local = lumbar_order[-n_ring:].astype(np.int32)
    lumbar_bottom_z = float(pos[lumbar_idx, 2].min())
    lumbar_top_z = float(pos[lumbar_idx, 2].max())
    lumbar_contact_local = np.flatnonzero(
        np.abs(pos[lumbar_idx, 0] - chosen_cx) <= tube_half_width + 1e-3)
    lumbar_side_local = np.flatnonzero(
        np.abs(np.abs(pos[lumbar_idx, 1]) - tube_half_width) <= 1e-3)
    lumbar_top_local = np.flatnonzero(
        np.abs(pos[lumbar_idx, 2] - lumbar_top_z) <= 1e-3)

    saddle_p = pos[saddle_start:saddle_start + n_saddle]
    saddle_top_local = np.flatnonzero(
        np.abs(saddle_p[:, 2] - block_top_z) <= 1e-3)
    lintel_local = np.flatnonzero(
        np.abs(saddle_p[:, 2] - lintel_bottom_z) <= 1e-3)
    cheek_inner_local = np.flatnonzero(
        np.abs(np.abs(saddle_p[:, 1]) - cheek_y_center) <= 1e-3)

    drop_idx = np.arange(drop_start, drop_start + drop_side ** 3)
    rope_idx = np.arange(rope_start, rope_start + n_rope)
    load_idx = np.arange(load_start, load_start + drop_side ** 3)

    # rope order from anchor to attach
    anchor = np.array([float(muscle_tip_x), 0.0,
                       float(droplet_apex_z + d_eq)], dtype=np.float64)
    rope_order_local = np.argsort(
        np.linalg.norm(pos[rope_idx] - anchor[None, :], axis=1)
    ).astype(np.int32)

    muscle_c = pos[lumbar_idx][muscle_face_local].mean(axis=0)
    load_c = pos[lumbar_idx][load_face_local].mean(axis=0)

    fulcrum_contact_point = np.array([float(chosen_cx), 0.0, float(block_top_z)],
                                     dtype=np.float64)

    R_true_final = float(chosen_trace["R_taut"][0] if not control
                         else chosen_trace["R_slack"][0])

    # Print law check
    diff = pos[:, None, :] - pos[None, :, :]
    r2 = (diff * diff).sum(axis=2)
    np.fill_diagonal(r2, np.inf)
    min_pair_dist = float(np.sqrt(r2.min()))
    if min_pair_dist <= 1e-6:
        raise RuntimeError(
            f"spine v1 print law violated: min pair distance {min_pair_dist}")

    derived = {
        "control": bool(control),
        "route": chosen_route,
        "gate_passed": strict_ok,
        "contact_x": float(chosen_cx),
        "d_eq": d_eq,
        "spacing": d,
        "sacrum_layers": sacrum_layers,
        "lumbar_layers": lumbar_layers,
        "n_plate": n_plate,
        "n_sacrum": n_sacrum,
        "n_saddle": n_saddle,
        "n_block": s ** 3,
        "n_cheek": 2 * s * n_cheek_z,
        "n_lintel": s * n_lintel_y,
        "n_lumbar": lumbar_layers * n_ring,
        "n_droplet": drop_side ** 3,
        "n_rope": n_rope,
        "n_load": drop_side ** 3,
        "well_floor_z": float(well_floor_z),
        "droplet_apex_z": float(droplet_apex_z),
        "muscle_tip_x": float(muscle_tip_x),
        "sacrum_top_z": float(sacrum_top_z),
        "sacrum_bottom_z": float(sacrum_bottom_z),
        "block_top_z": float(block_top_z),
        "lumbar_bottom_z": float(lumbar_bottom_z),
        "lumbar_top_z": float(lumbar_top_z),
        "lintel_bottom_z": float(lintel_bottom_z),
        "cheek_y_center": float(cheek_y_center),
        "corner_rise": float(corner_rise),
        "fulcrum_contact_point": fulcrum_contact_point,
        "sacrum_start": n_plate,
        "saddle_start": saddle_start,
        "lumbar_start": lumbar_start,
        "drop_start": drop_start,
        "rope_start": rope_start,
        "load_start": load_start,
        "sacrum_bottom_local": sacrum_bottom_local.astype(np.int32),
        "sacrum_top_local": sacrum_top_local.astype(np.int32),
        "muscle_face_local": muscle_face_local,
        "load_face_local": load_face_local,
        "lumbar_contact_local": lumbar_contact_local.astype(np.int32),
        "lumbar_side_local": lumbar_side_local.astype(np.int32),
        "lumbar_top_local": lumbar_top_local.astype(np.int32),
        "saddle_top_local": saddle_top_local.astype(np.int32),
        "lintel_local": lintel_local.astype(np.int32),
        "cheek_inner_local": cheek_inner_local.astype(np.int32),
        "rope_order_local": rope_order_local,
        "R_true": R_true_final,
        "theta_stop_muscle": float(chosen_trace["theta_muscle"]),
        "theta_stop_load": float(chosen_trace["theta_load"]),
        "arc_trace": chosen_trace,
        "load_end_z0": float(load_c[2]),
        "plate_pos0": pos[:n_plate].copy(),
    }

    return pos.astype(np.float32), np.zeros_like(pos, dtype=np.float32), \
        pin_mask, grain_ids, derived
