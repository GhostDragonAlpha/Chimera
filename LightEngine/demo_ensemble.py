"""
THE ENSEMBLE — run a category of independent worlds in one batched CUDA context.

Reads a JSON spec file of worlds, builds each start via the existing generators,
integrates them together with EnsembleVerlet, and reports per-world metrics and
verdicts at the same derived observation window as demo_seed.py.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import math
import time
import numpy as np

from LightEngine import kernel, seed_structures
from LightEngine.demo_seed import (
    structureless_start,
    cluster_count_and_sizes,
    bound_mass_fraction,
    edge_sharpness,
    system_radius,
    shell_disk_metrics,
    core_bound_fraction,
    nearest_neighbor_distances,
    dump_frame,
    OUTPUT_DIR,
    BOX,
    DT,
    VEL_SIGMA,
    T_FF_COUNT,
    METRIC_R_INNER,
    METRIC_R_OUTER,
    COLLAPSE_MAX_CLUSTER_FRAC,
    DISPERSE_MAX_CLUSTER_FRAC,
    DISPERSE_RADIUS_GROWTH,
    FLICKER_CV_THRESHOLD,
    BOUND_MASS_PERSISTENCE,
    G,
    R_WALL,
    R_BOND,
    R_C,
)


# Default printed geometry, matching demo_seed.py / THE_PRINTER.md
R_SHELL = 4.0
R_DISK = 4.0
F_CORE = 0.5


def build_world(spec: dict, n: int):
    """Return (tag, positions, velocities) for one spec entry."""
    structure = spec.get("structure", "random")
    seed = int(spec.get("seed", 0))
    tag = spec.get("tag", f"{structure}_{seed}")

    if structure == "random":
        pos, vel = structureless_start(n, BOX, VEL_SIGMA, seed)
        actual_n = n
    elif structure == "core_shell":
        pos, vel = seed_structures.core_shell(n, f_core=F_CORE,
                                              r_shell=R_SHELL, seed=seed)
        actual_n = n
    elif structure == "disk":
        pos, vel = seed_structures.disk(n, f_core=F_CORE,
                                        r_disk=R_DISK, seed=seed)
        actual_n = n
    elif structure == "lattice":
        pos, vel = seed_structures.lattice(seed=seed)
        actual_n = pos.shape[0]
    else:
        raise ValueError(f"unknown structure '{structure}'")

    return tag, structure, pos, vel, actual_n


def _structure_persistence_metrics(pos, structure, n_core):
    """Return a dict of print-persistence metrics and a formatted suffix."""
    if structure in ("core_shell", "disk"):
        r_mean, r_std, z_disp = shell_disk_metrics(pos, n_core)
        core_bound = core_bound_fraction(pos, n_core, R_BOND)
        extra = (f" | shell_r={r_mean:.3f}±{r_std:.3f}"
                 f" | core_bound={core_bound:.3f}")
        metrics = {"shell_radius_mean": r_mean, "shell_radius_std": r_std,
                   "core_bound_frac": core_bound, "z_disp": z_disp}
        if structure == "disk":
            extra += f" | z_disp={z_disp:.3f}"
        return metrics, extra
    elif structure == "lattice":
        nn = nearest_neighbor_distances(pos)
        bond_ret = float(((nn >= R_WALL) & (nn <= R_C)).mean())
        extra = f" | bond_ret={bond_ret:.3f}"
        return {"bond_retention": bond_ret}, extra
    return {}, ""


def _world_verdict(metrics, N):
    """Standard falsifier verdict for one world (mirrors demo_seed.py)."""
    clusters = np.array(metrics["clusters"], dtype=np.float64)
    bound_fracs = np.array(metrics["bound_frac"], dtype=np.float64)
    radii = np.array(metrics["radius"], dtype=np.float64)
    final_max = metrics["max_cluster"][-1]
    final_bound = bound_fracs[-1]
    initial_radius = radii[0]
    final_radius = radii[-1]

    q = max(1, len(clusters) // 4)
    late_clusters = clusters[-q:]
    late_bound = bound_fracs[-q:]
    cluster_cv = float(late_clusters.std() / (late_clusters.mean() + 1e-12))
    bound_swing = float(late_bound.max() - late_bound.min())

    verdict = "PASS"
    reasons = []
    if final_max >= N * COLLAPSE_MAX_CLUSTER_FRAC:
        verdict = "COLLAPSE"
        reasons.append(f"max_cluster={final_max} >= {COLLAPSE_MAX_CLUSTER_FRAC*N:.0f}")
    if final_max <= N * DISPERSE_MAX_CLUSTER_FRAC and final_bound < 0.3:
        verdict = "DISPERSE"
        reasons.append(f"max_cluster={final_max} <= {DISPERSE_MAX_CLUSTER_FRAC*N:.0f} and bound_frac={final_bound:.3f}")
    if final_radius > initial_radius * DISPERSE_RADIUS_GROWTH:
        verdict = "DISPERSE"
        reasons.append(f"radius {final_radius:.3f} > {DISPERSE_RADIUS_GROWTH}x initial {initial_radius:.3f}")
    if cluster_cv > FLICKER_CV_THRESHOLD:
        verdict = "FLICKER"
        reasons.append(f"cluster_count CV={cluster_cv:.3f} > {FLICKER_CV_THRESHOLD}")
    if bound_swing > BOUND_MASS_PERSISTENCE:
        verdict = "FLICKER"
        reasons.append(f"bound_frac swing={bound_swing:.3f} > {BOUND_MASS_PERSISTENCE}")

    return verdict, reasons, final_max, final_bound, final_radius, cluster_cv, bound_swing


def main():
    import argparse
    parser = argparse.ArgumentParser(description="THE ENSEMBLE category run")
    parser.add_argument("--specs", type=str, required=True,
                        help="JSON file: list of {structure, seed, tag} worlds")
    parser.add_argument("--n", type=int, default=4096,
                        help="point count per non-lattice world (default 4096)")
    parser.add_argument("--tag", type=str, default="",
                        help="global prefix for output frames")
    args = parser.parse_args()

    with open(args.specs, "r") as f:
        specs = json.load(f)
    if not specs:
        raise ValueError("specs file is empty")

    # build worlds and enforce uniform N
    tags, structures, pos_list, vel_list = [], [], [], []
    actual_ns = []
    for spec in specs:
        tag, struct, pos, vel, actual_n = build_world(spec, args.n)
        tags.append(tag)
        structures.append(struct)
        pos_list.append(pos)
        vel_list.append(vel)
        actual_ns.append(actual_n)

    N = actual_ns[0]
    if any(n != N for n in actual_ns):
        raise ValueError(
            f"all worlds must share N; found {dict(zip(tags, actual_ns))}")

    W = len(specs)
    RHO_LOCAL = N / BOX ** 3
    T_FF = 1.0 / math.sqrt(G * RHO_LOCAL)
    TOTAL_TICKS = int(math.ceil(T_FF_COUNT * T_FF / DT))
    SAMPLE_EVERY = max(1, TOTAL_TICKS // 40)
    tag_prefix = f"{args.tag}_" if args.tag else ""

    print("=" * 70)
    print("THE ENSEMBLE — batched category run")
    print(f"W={W}, N={N}, dt={DT}, ticks={TOTAL_TICKS}, sample_every={SAMPLE_EVERY}")
    print(f"worlds: {', '.join(tags)}")
    print("=" * 70)

    # assemble and upload batch
    stacked_pos = np.stack(pos_list, axis=0)  # (W, N, 3)
    stacked_vel = np.stack(vel_list, axis=0)
    ens = kernel.EnsembleVerlet(W, N)
    ens.set_all(stacked_pos, stacked_vel)
    ens.compute_acceleration()

    # per-world metric storage
    metrics_per_world = [
        {"tick": [], "clusters": [], "max_cluster": [], "bound_frac": [],
         "edge": [], "radius": [], "radiated_energy": [], "radiated_power": [],
         "shell_radius_mean": [], "shell_radius_std": [], "core_bound_frac": [],
         "z_disp": [], "bond_retention": []}
        for _ in range(W)
    ]

    # initial frames
    for w in range(W):
        path = os.path.join(OUTPUT_DIR, f"{tag_prefix}{tags[w]}_frame_begin.png")
        dump_frame(ens.pos[w].copy(), path)

    t0 = time.perf_counter()
    for tick in range(1, TOTAL_TICKS + 1):
        ens.step(DT)
        if tick % SAMPLE_EVERY == 0 or tick == TOTAL_TICKS:
            ens.sync_from_device()
            for w in range(W):
                pos_w = ens.pos[w]
                n_clust, sizes = cluster_count_and_sizes(pos_w, R_C)
                bound_frac = bound_mass_fraction(pos_w, R_BOND)
                edge = edge_sharpness(pos_w, METRIC_R_INNER, METRIC_R_OUTER)
                rad = system_radius(pos_w)
                n_core = int(F_CORE * N) if structures[w] in ("core_shell", "disk") else 0
                persist, extra = _structure_persistence_metrics(pos_w, structures[w], n_core)

                mw = metrics_per_world[w]
                mw["tick"].append(tick)
                mw["clusters"].append(n_clust)
                mw["max_cluster"].append(int(sizes.max()))
                mw["bound_frac"].append(bound_frac)
                mw["edge"].append(edge)
                mw["radius"].append(rad)
                mw["radiated_energy"].append(float(ens.radiated_energy[w]))
                mw["radiated_power"].append(float(ens.last_radiated_power[w]))
                mw["shell_radius_mean"].append(persist.get("shell_radius_mean", 0.0))
                mw["shell_radius_std"].append(persist.get("shell_radius_std", 0.0))
                mw["core_bound_frac"].append(persist.get("core_bound_frac", 0.0))
                mw["z_disp"].append(persist.get("z_disp", 0.0))
                mw["bond_retention"].append(persist.get("bond_retention", 0.0))

                print(f"[{tags[w]:16s}] tick={tick:6d} | clusters={n_clust:4d} | "
                      f"max={sizes.max():4d} | bound={bound_frac:.3f} | "
                      f"edge={edge:.3f} | radius={rad:.3f} | "
                      f"E_rad={ens.radiated_energy[w]:.4f} | P_rad={ens.last_radiated_power[w]:.4f}"
                      f"{extra}")
        if tick == TOTAL_TICKS // 2:
            for w in range(W):
                path = os.path.join(OUTPUT_DIR, f"{tag_prefix}{tags[w]}_frame_mid.png")
                dump_frame(ens.pos[w].copy(), path)

    wall_time = time.perf_counter() - t0

    # final frames
    for w in range(W):
        path = os.path.join(OUTPUT_DIR, f"{tag_prefix}{tags[w]}_frame_end.png")
        dump_frame(ens.pos[w].copy(), path)

    # verdict blocks
    print("=" * 70)
    for w in range(W):
        mw = metrics_per_world[w]
        verdict, reasons, final_max, final_bound, final_radius, cluster_cv, bound_swing = \
            _world_verdict(mw, N)
        print(f"FALSIFIER VERDICT [{tags[w]}]: {verdict}")
        print(f"  final max cluster   = {final_max}")
        print(f"  final bound frac    = {final_bound:.4f}")
        print(f"  final radius        = {final_radius:.4f}")
        print(f"  cluster CV (late)   = {cluster_cv:.4f}")
        print(f"  bound swing (late)  = {bound_swing:.4f}")
        print(f"  radiated energy     = {mw['radiated_energy'][-1]:.4f}")
        if reasons:
            for r in reasons:
                print(f"    - {r}")
        else:
            print("    reasons: none — prediction held")

        if structures[w] in ("core_shell", "disk"):
            r_mean = mw.get("shell_radius_mean", [0.0])[-1]
            r_std = mw.get("shell_radius_std", [0.0])[-1]
            core_bound = mw.get("core_bound_frac", [0.0])[-1]
            r_target = R_SHELL if structures[w] == "core_shell" else R_DISK
            radius_ok = abs(r_mean - r_target) <= 0.50 * r_target
            print(f"  PRINT PERSISTENCE: shell_r={r_mean:.4f}±{r_std:.4f} "
                  f"target={r_target:.4f} {'PASS' if radius_ok else 'FAIL'}")
            print(f"                     core_bound={core_bound:.4f}")
            if structures[w] == "disk":
                z_disp = mw.get("z_disp", [0.0])[-1]
                z_ok = z_disp < 0.25 * R_DISK
                print(f"                     z_disp={z_disp:.4f} threshold={0.25*R_DISK:.4f} "
                      f"{'PASS' if z_ok else 'FAIL'}")
        elif structures[w] == "lattice":
            bond_ret = mw.get("bond_retention", [0.0])[-1]
            bond_ok = bond_ret > 0.50
            print(f"  PRINT PERSISTENCE: bond_ret={bond_ret:.4f} {'PASS' if bond_ok else 'FAIL'}")
        print("-" * 70)

    print(f"ENSEMBLE WALL TIME: {wall_time:.3f} s")
    print(f"PER-TICK AVERAGE:   {wall_time / TOTAL_TICKS * 1e3:.3f} ms/tick")
    print(f"OUTPUT: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
