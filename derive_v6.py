"""Derivation script for theLever v6: cheek geometry and alpha bisection."""
import numpy as np
from LightEngine import kernel, seed_structures
from LightEngine.seed_structures import TENDON_D_EQ, R_WALL

d = 0.05
d_eq = TENDON_D_EQ
seed = 20260806
rng = np.random.default_rng(seed)

length = 13
L = (length - 1) * d

fulcrum_side = 4
n_fulcrum_block = fulcrum_side ** 3
f_off = (np.arange(fulcrum_side, dtype=np.float64) - (fulcrum_side - 1) / 2.0) * d
fz = np.arange(fulcrum_side, dtype=np.float64) * d + d_eq
fulcrum_top_z = d_eq + (fulcrum_side - 1) * d
fulcrum_half_width = (fulcrum_side - 1) / 2.0 * d  # 0.075

# Tube dims
tube_outer_w = 0.20  # 4 grains
# spec: cheek height >= tube outer half-width (0.10) above perch
cheek_height = tube_outer_w / 2.0  # 0.10
# separation = tube width + d_eq per side => inner face y = tube_half + d_eq
tube_half_w = tube_outer_w / 2.0  # 0.10
cheek_inner_y = tube_half_w + d_eq  # 0.1484
# cheek one grain thick, centered at inner_y + d/2
cheek_y_center = cheek_inner_y + d / 2.0  # 0.1734
# number of cheek grains in z to reach height: n such that (n-1)*d >= cheek_height
n_cheek_z = int(np.ceil(cheek_height / d)) + 1  # 3

print(f"tube_outer_w={tube_outer_w}, tube_half_w={tube_half_w}")
print(f"cheek_height={cheek_height}, n_cheek_z={n_cheek_z}")
print(f"cheek_inner_y={cheek_inner_y}, cheek_y_center={cheek_y_center}")
print(f"gap tube side (y=0.10) to cheek inner={cheek_inner_y - tube_half_w}")

plate_side = 6
n_plate = plate_side * plate_side
p_off = (np.arange(plate_side, dtype=np.float64) - (plate_side - 1) / 2.0) * d
px, py = np.meshgrid(p_off, p_off, indexing="ij")
plate_pos = np.stack([px.ravel(), py.ravel(), np.zeros(n_plate)], axis=1)

load_side = 4
n_load = load_side ** 3
load_off = f_off
load_y = f_off

drop_side = 4
n_drop = drop_side ** 3
drop_off = (np.arange(drop_side, dtype=np.float64) - (drop_side - 1) / 2.0) * d
drop_z = np.arange(drop_side, dtype=np.float64) * d + d_eq


def build_tube():
    s = 4
    x_off = (np.arange(length, dtype=np.float64) - (length - 1) / 2.0) * d
    yz_off = (np.arange(s, dtype=np.float64) - (s - 1) / 2.0) * d
    gy, gz = np.meshgrid(yz_off, yz_off, indexing="ij")
    inner = (np.abs(gy) <= 0.5 * d + 1e-12) & (np.abs(gz) <= 0.5 * d + 1e-12)
    shell = ~inner
    y_shell = gy[shell]
    z_shell = gz[shell]
    n_ring = int(y_shell.size)
    x_all = np.repeat(x_off, n_ring)
    y_all = np.tile(y_shell, length)
    z_all = np.tile(z_shell, length)
    pos = np.stack([x_all, y_all, z_all], axis=1)
    return pos, n_ring, x_off


def _R_true_at_print(pos, grain_ids, cp, pin_mask):
    n = pos.shape[0]
    sim = kernel.VelocityVerlet(n)
    sim.set_state(pos.astype(np.float32), np.zeros_like(pos, dtype=np.float32))
    sim.set_pin_mask(pin_mask)
    acc = sim.compute_acceleration()
    pos64 = np.asarray(pos, dtype=np.float64)
    acc64 = np.asarray(acc, dtype=np.float64)
    cp = np.asarray(cp, dtype=np.float64)
    free = (grain_ids != -1) & (~pin_mask)
    r = pos64[free] - cp
    F = acc64[free]
    tau_z = r[:, 0] * F[:, 2] - r[:, 2] * F[:, 0]
    tau_pos = float(np.maximum(tau_z, 0.0).sum())
    tau_neg = float(np.maximum(-tau_z, 0.0).sum())
    if tau_neg <= 0.0:
        return float("inf"), tau_pos, tau_neg
    return tau_pos / tau_neg, tau_pos, tau_neg


def build_geometry(alpha: float, seed_override=None):
    rng_local = np.random.default_rng(seed_override if seed_override is not None else seed)
    lever_pos, n_ring, lever_x_off = build_tube()
    lever_bottom_z = fulcrum_top_z + d_eq
    lever_pos = lever_pos.copy()
    lever_pos[:, 2] += lever_bottom_z + fulcrum_half_width  # bottom face at lever_bottom_z
    lever_top_z = lever_bottom_z + (fulcrum_side - 1) * d

    muscle_end_x = float(lever_x_off[0])
    load_end_x = float(lever_x_off[-1])
    insertion_x = muscle_end_x + alpha * L

    drop_x = drop_off + insertion_x
    dx, dy, dz = np.meshgrid(drop_x, drop_off, drop_z, indexing="ij")
    droplet_pos = np.stack([dx.ravel(), dy.ravel(), dz.ravel()], axis=1)

    load_z = np.arange(load_side, dtype=np.float64) * d + lever_top_z + d_eq
    load_x = load_off + load_end_x
    lx, ly2, lz2 = np.meshgrid(load_x, load_y, load_z, indexing="ij")
    load_pos = np.stack([lx.ravel(), ly2.ravel(), lz2.ravel()], axis=1)

    cx_min = muscle_end_x + fulcrum_half_width
    cx_max = load_end_x - fulcrum_half_width

    # Build fulcrum block + cheeks (positions depend on contact_x later)
    # For now return components and a closure that assembles with contact_x and cheeks.

    n_total = n_plate + n_drop + n_fulcrum_block + 2 * (fulcrum_side * 1 * n_cheek_z) + lever_pos.shape[0] + n_load
    # grain ids: -1 plate, 0 droplet, 1 fulcrum (block+cheeks), 2 lever, 3 load
    grain_ids = np.empty(n_total, dtype=np.int32)
    grain_ids[:n_plate] = -1
    grain_ids[n_plate:n_plate + n_drop] = 0
    grain_ids[n_plate + n_drop:n_plate + n_drop + n_fulcrum_block + 2 * fulcrum_side * n_cheek_z] = 1
    grain_ids[n_plate + n_drop + n_fulcrum_block + 2 * fulcrum_side * n_cheek_z:
              n_plate + n_drop + n_fulcrum_block + 2 * fulcrum_side * n_cheek_z + lever_pos.shape[0]] = 2
    grain_ids[n_plate + n_drop + n_fulcrum_block + 2 * fulcrum_side * n_cheek_z + lever_pos.shape[0]:] = 3

    pin_mask = np.zeros(n_total, dtype=bool)
    pin_mask[:n_plate] = True
    pin_mask[n_plate + n_drop:
             n_plate + n_drop + n_fulcrum_block + 2 * fulcrum_side * n_cheek_z] = True

    def _build_no_jitter(contact_x: float):
        fx = f_off + contact_x
        fxg, fyg, fzg = np.meshgrid(fx, f_off, fz, indexing="ij")
        fulcrum_p = np.stack([fxg.ravel(), fyg.ravel(), fzg.ravel()], axis=1)
        # cheeks
        cx_grid = fx
        z_cheek_off = np.arange(n_cheek_z, dtype=np.float64) * d + d  # start one step above perch? or at perch?
        # spec: cheeks rise above perch; bottom at perch to capture. Use bottom at fulcrum_top_z + d/2?
        z_cheek_off = np.arange(n_cheek_z, dtype=np.float64) * d + d / 2.0
        cheek_z = fulcrum_top_z + z_cheek_off
        cheek_y = np.array([cheek_y_center, -cheek_y_center], dtype=np.float64)
        c_x, c_y, c_z = np.meshgrid(cx_grid, cheek_y, cheek_z, indexing="ij")
        cheeks_p = np.stack([c_x.ravel(), c_y.ravel(), c_z.ravel()], axis=1)
        pos = np.vstack([plate_pos, droplet_pos, fulcrum_p, cheeks_p, lever_pos, load_pos]).astype(np.float64)
        return pos

    tmp = _build_no_jitter(0.0)
    jitter = rng_local.normal(0.0, R_WALL * 0.01, size=tmp.shape)

    def _assemble(contact_x: float):
        pos = _build_no_jitter(contact_x)
        pos += jitter
        return pos

    def _ratio(cx: float):
        pos = _assemble(cx)
        cp = np.array([float(cx), 0.0, fulcrum_top_z], dtype=np.float64)
        return _R_true_at_print(pos, grain_ids, cp, pin_mask)

    return {
        "lever_pos": lever_pos,
        "droplet_pos": droplet_pos,
        "load_pos": load_pos,
        "grain_ids": grain_ids,
        "pin_mask": pin_mask,
        "assemble": _assemble,
        "ratio": _ratio,
        "muscle_end_x": muscle_end_x,
        "load_end_x": load_end_x,
        "cx_min": cx_min,
        "cx_max": cx_max,
        "n_total": n_total,
        "n_fulcrum": n_fulcrum_block + 2 * fulcrum_side * n_cheek_z,
    }


def check_alpha(alpha: float):
    geo = build_geometry(alpha)
    ratio = geo["ratio"]
    cx_min = geo["cx_min"]
    cx_max = geo["cx_max"]
    load_end_x = geo["load_end_x"]
    muscle_end_x = geo["muscle_end_x"]
    min_margin = 2.0 * d

    n = 49
    xs = np.linspace(cx_min, cx_max, n)
    Rs = np.array([ratio(x)[0] for x in xs])
    Rmin, Rmax = Rs.min(), Rs.max()

    # main target 2.0 reachable off-edge
    main_ok = False
    main_cx = None
    main_R = None
    if Rmin <= 2.0 <= Rmax:
        for i in range(n - 1):
            if (Rs[i] - 2.0) * (Rs[i + 1] - 2.0) > 0:
                continue
            lo, hi = xs[i], xs[i + 1]
            for _ in range(24):
                mid = 0.5 * (lo + hi)
                Rmid = ratio(mid)[0]
                if (Rmid - 2.0) * (Rs[i] - 2.0) <= 0:
                    hi = mid
                else:
                    lo = mid
            cx = 0.5 * (lo + hi)
            R = ratio(cx)[0]
            if load_end_x - cx >= min_margin and cx - muscle_end_x >= min_margin:
                main_ok = True
                main_cx = cx
                main_R = R
                break

    ctrl_ok = False
    ctrl_cx = None
    ctrl_R = None
    if Rmin <= 0.75 <= Rmax:
        for i in range(n - 1):
            if min(Rs[i], Rs[i + 1]) > 0.75 or max(Rs[i], Rs[i + 1]) < 0.75:
                continue
            lo, hi = xs[i], xs[i + 1]
            for _ in range(24):
                mid = 0.5 * (lo + hi)
                Rmid = ratio(mid)[0]
                if (Rmid - 0.75) * (Rs[i] - 0.75) <= 0:
                    hi = mid
                else:
                    lo = mid
            cx = 0.5 * (lo + hi)
            R = ratio(cx)[0]
            if 0.5 <= R <= 1.0 and (load_end_x - cx >= min_margin or cx - muscle_end_x >= min_margin):
                ctrl_ok = True
                ctrl_cx = cx
                ctrl_R = R
                break

    return {
        "alpha": alpha,
        "Rmin": Rmin,
        "Rmax": Rmax,
        "main_ok": main_ok,
        "main_cx": main_cx,
        "main_R": main_R,
        "ctrl_ok": ctrl_ok,
        "ctrl_cx": ctrl_cx,
        "ctrl_R": ctrl_R,
    }


def main():
    print("alpha\tRmin\tRmax\tmain_ok\tmain_R\tctrl_ok\tctrl_R")
    for alpha in np.linspace(0.0, 1.0, 21):
        res = check_alpha(round(alpha, 3))
        print(f"{res['alpha']:.3f}\t{res['Rmin']:.3f}\t{res['Rmax']:.3f}\t"
              f"{res['main_ok']}\t{res['main_R'] if res['main_R'] else '-'}\t"
              f"{res['ctrl_ok']}\t{res['ctrl_R'] if res['ctrl_R'] else '-'}")


if __name__ == "__main__":
    main()
