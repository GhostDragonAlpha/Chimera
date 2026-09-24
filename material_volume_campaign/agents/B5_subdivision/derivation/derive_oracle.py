"""B5 independent expectation oracle + derived frozen bounds (pure stdlib).

Reads the generated fixture JSONs (NOT the generator code) and:

  G1 — integrates each level's tet complex with EXACT rational simplex moments
       (fractions.Fraction) and asserts exact equality against the analytic
       closed-form box values computed independently from the box formulas.
       This proves the subdivision tessellations cover the IDENTICAL region
       with correct orientation, in exact arithmetic, before any exporter run.

  G2 — derives the float64 error envelope of the exporter's exact-polyhedron
       integration chain and freezes per-level falsifier thresholds
           T_q(L) = GAMMA * (K_TERM + N_L - 1) * U * S_q
       for mass, volume, COM (per axis) and every inertia tensor entry.

Writes derivation/derived_expectations.json + derivation/derivation_log.txt.
Imports nothing from tools/.
"""
from __future__ import annotations

import json
import math
import os
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.normpath(os.path.join(HERE, "..", "fixtures"))

LEVELS = ["L0", "L1", "L2", "L3"]
DENSITY = Fraction(12)
BOX = (Fraction(4), Fraction(2), Fraction(2))  # Lx, Ly, Lz of the coupon region

# --- frozen derivation constants (see PREREGISTRATION.md) ---
U = 2.220446049250313e-16        # numpy float64 epsilon (per-ulp unit; >= unit roundoff)
K_TERM = 128                     # ulp budget of one cell's full contribution chain
GAMMA = 4                        # fixed safety factor on the worst-case envelope

# Analytic box values (exact rationals), from the closed-form box formulas.
ANALYTIC = {
    "volume_m3": BOX[0] * BOX[1] * BOX[2],
    "mass_kg": DENSITY * BOX[0] * BOX[1] * BOX[2],
    "com_m": tuple(b / 2 for b in BOX),
    "inertia_diag_kg_m2": tuple(
        DENSITY * BOX[0] * BOX[1] * BOX[2] / 12
        * ((BOX[(i + 1) % 3] ** 2 + BOX[(i + 2) % 3] ** 2))
        for i in range(3)),
}


def _det(corners):
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = corners
    return ((x1 - x0) * ((y2 - y0) * (z3 - z0) - (z2 - z0) * (y3 - y0))
            - (y1 - y0) * ((x2 - x0) * (z3 - z0) - (z2 - z0) * (x3 - x0))
            + (z1 - z0) * ((x2 - x0) * (y3 - y0) - (y2 - y0) * (x3 - x0)))


def exact_integrate(tet_json, density):
    """Exact rational mass/COM/inertia-about-COM of a tet complex (numpy's algebra)."""
    cells = []
    for row in tet_json:
        pos = [tuple(v) for v in row["positions"]]
        det = _det(pos)
        assert det > 0
        vol = det / 6
        mass = density * vol
        cent = tuple(sum(p[a] for p in pos) / 4 for a in range(3))
        q = [[sum((pos[i][a] - cent[a]) * (pos[i][b] - cent[b]) for i in range(4))
              * mass / 20 for b in range(3)] for a in range(3)]
        cells.append({"m": mass, "c": cent, "q": q})
    total_mass = sum(cell["m"] for cell in cells)
    com = tuple(sum(cell["m"] * cell["c"][a] for cell in cells) / total_mass
                for a in range(3))
    inertia = [[Fraction(0)] * 3 for _ in range(3)]
    for cell in cells:
        d = tuple(cell["c"][a] - com[a] for a in range(3))
        dd = sum(x * x for x in d)
        trace_q = sum(cell["q"][i][i] for i in range(3))
        for a in range(3):
            for b in range(3):
                inertia[a][b] += (trace_q * (1 if a == b else 0)
                                  - cell["q"][a][b]
                                  + cell["m"] * ((dd if a == b else 0) - d[a] * d[b]))
    return total_mass, com, inertia


def load_fixtures(level):
    with open(os.path.join(FIX, f"{level.lower()}_partition.json"), encoding="utf-8") as fh:
        partition = json.load(fh, parse_float=Fraction)
    verts = {row["vertex_id"]: tuple(row["position"]) for row in partition["vertices"]}
    tets = [{"positions": [verts[vid] for vid in row["vertex_ids"]]}
            for row in partition["cells"]]
    n_cells = len(tets)
    density = {m["material_id"]: m["density_kg_m3"] for m in partition["materials"]}
    # one region, one material — the coupon's single uniform material
    region = partition["regions"][0]
    rho = density[region["material_id"]]
    return n_cells, rho, tets


def subbox_edge(level):
    grid = {"L0": (1, 1, 1), "L1": (2, 1, 1), "L2": (4, 2, 2), "L3": (8, 4, 4)}[level]
    return tuple(b / g for b, g in zip(BOX, grid))


def derived_thresholds(level, n_cells):
    h = subbox_edge(level)
    diam2 = sum(x ** 2 for x in h)                       # sub-box corner-to-corner^2
    r_max2 = sum(b ** 2 for b in BOX) / 4                # (half diagonal of coupon)^2
    s_inertia = ANALYTIC["mass_kg"] * (diam2 + 4 * r_max2)
    s_com = math.sqrt(float(sum(b ** 2 for b in BOX)))   # max |c_i - reference| envelope, m
    k = K_TERM + n_cells - 1
    scale = GAMMA * k * U
    return {
        "n_cells": n_cells,
        "subbox_edges_m": [float(x) for x in h],
        "k_sum_minus_1": n_cells - 1,
        "k_total": k,
        "S_mass_kg": float(ANALYTIC["mass_kg"]),
        "S_volume_m3": float(ANALYTIC["volume_m3"]),
        "S_com_m": s_com,
        "S_inertia_kg_m2": float(s_inertia),
        "T_mass_kg": scale * float(ANALYTIC["mass_kg"]),
        "T_volume_m3": scale * float(ANALYTIC["volume_m3"]),
        "T_com_m": scale * s_com,
        "T_inertia_kg_m2": scale * float(s_inertia),
        "T_mass_relative_to_analytic": scale,
        "T_com_relative_to_Lx": scale * s_com / float(BOX[0]),
        "T_inertia_relative_to_Imax": scale * float(s_inertia)
                                       / float(max(ANALYTIC["inertia_diag_kg_m2"])),
    }


def main():
    log = []
    expectations = {"constants": {"u": U, "k_term": K_TERM, "gamma": GAMMA,
                                  "box_m": [float(b) for b in BOX],
                                  "density_kg_m3": float(DENSITY)},
                    "analytic": {"mass_kg": float(ANALYTIC["mass_kg"]),
                                 "volume_m3": float(ANALYTIC["volume_m3"]),
                                 "com_m": [float(c) for c in ANALYTIC["com_m"]],
                                 "inertia_diag_kg_m2": [float(x) for x
                                                        in ANALYTIC["inertia_diag_kg_m2"]],
                                 "inertia_offdiag_kg_m2": 0.0},
                    "levels": {}}

    def say(line):
        log.append(line)
        print(line)

    say("G1 — exact rational integration of each fixture vs closed-form box values")
    ok_all = True
    for level in LEVELS:
        n_cells, rho, tets = load_fixtures(level)
        mass, com, inertia = exact_integrate(tets, rho)
        checks = {
            "volume_exact": sum(_det(t["positions"]) / 6 for t in tets)
                            == ANALYTIC["volume_m3"],
            "mass_exact": mass == ANALYTIC["mass_kg"],
            "density_uniform": rho == DENSITY,
            "com_exact": com == ANALYTIC["com_m"],
            "inertia_exact": all(inertia[a][a] == ANALYTIC["inertia_diag_kg_m2"][a]
                                 for a in range(3))
                             and all(inertia[a][b] == 0
                                     for a in range(3) for b in range(3) if a != b),
        }
        ok_all &= all(checks.values())
        expectations["levels"][level] = {
            "n_cells": n_cells,
            "exact_rational_check": {k: bool(v) for k, v in checks.items()},
            "analytic_mass_kg": float(ANALYTIC["mass_kg"]),
            "analytic_volume_m3": float(ANALYTIC["volume_m3"]),
            "analytic_com_m": [float(c) for c in ANALYTIC["com_m"]],
            "analytic_inertia_kg_m2": [float(ANALYTIC["inertia_diag_kg_m2"][0]),
                                       float(ANALYTIC["inertia_diag_kg_m2"][1]),
                                       float(ANALYTIC["inertia_diag_kg_m2"][2]),
                                       0.0, 0.0, 0.0],  # Ixx, Iyy, Izz, Ixy, Ixz, Iyz
            "thresholds": derived_thresholds(level, n_cells),
        }
        say(f"  {level}: N={n_cells:4d} exact checks {checks}")
    say(f"  G1 VERDICT: {'ALL EXACT' if ok_all else 'FAILED'}")
    if not ok_all:
        raise SystemExit("G1 failed: fixture tessellation does not integrate exactly")

    say("")
    say("G2 — derived float64 envelopes (worst case) and frozen thresholds T = 4*(128+N-1)*U*S")
    for level in LEVELS:
        t = expectations["levels"][level]["thresholds"]
        say(f"  {level}: N={t['n_cells']:4d} k={t['k_total']:4d} "
            f"T_mass={t['T_mass_kg']:.3e} kg ({t['T_mass_relative_to_analytic']:.2e} rel) "
            f"T_com={t['T_com_m']:.3e} m ({t['T_com_relative_to_Lx']:.2e} of Lx) "
            f"T_I={t['T_inertia_kg_m2']:.3e} kg*m^2 ({t['T_inertia_relative_to_Imax']:.2e} of Imax)")

    with open(os.path.join(HERE, "derived_expectations.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(expectations, fh, indent=1)
        fh.write("\n")
    with open(os.path.join(HERE, "derivation_log.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(log) + "\n")
    print("wrote derived_expectations.json + derivation_log.txt")


if __name__ == "__main__":
    main()
