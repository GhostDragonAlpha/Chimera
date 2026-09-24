"""B5 verdict pass — frozen-rule comparison ONLY (no tolerance chosen here).

Reads derivation/derived_expectations.json (frozen BEFORE the exporter runs)
and receipts/run_l{k}_report.json (verbatim exporter stdout), and emits
per-level, per-quantity verdicts, level-vs-level verdicts, and the growth
characterization table. Writes receipts/verdicts.json.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, ".."))
LEVELS = ["l0", "l1", "l2", "l3"]
QUANT_LABELS = ["Ixx", "Iyy", "Izz", "Ixy", "Ixz", "Iyz"]


def load(level):
    with open(os.path.join(BASE, "receipts", f"run_{level}_report.json"), encoding="utf-8") as fh:
        report = json.load(fh)
    with open(os.path.join(BASE, "derivation", "derived_expectations.json"), encoding="utf-8") as fh:
        exp = json.load(fh)
    group = report["body_groups"][0]
    props = group["mass_properties"]
    inertia = props["inertia_tensor_about_com"]["value"]
    measured = {
        "mass": props["mass"]["value"],
        "volume": props["volume"]["value"],
        "com": props["center_of_mass"]["value"],
        "inertia6": [inertia[0][0], inertia[1][1], inertia[2][2],
                     inertia[0][1], inertia[0][2], inertia[1][2]],
        "full_inertia": inertia,
        "com_full": props["center_of_mass"]["value"],
    }
    gates = {
        "export_status": report["export_status"],
        "admission_status": report["admission_status"],
        "all_supplied_cells_assigned": report["all_supplied_cells_assigned"],
        "reason_codes": report["reason_codes"],
        "n_owned_cells": len(group["owned_cell_ids"]),
        "body_id": group["body_id"],
    }
    return report, group, measured, gates, exp


def main():
    lines = []
    verdicts = {"levels": {}, "gates": {}, "level_pairs": {}}
    ok_all = True

    def say(s=""):
        lines.append(s)
        print(s)

    say("B5 verdict pass — thresholds read from frozen derived_expectations.json")
    say("")
    for li, level in enumerate(LEVELS):
        report, group, m, gates, exp = load(level)
        lv = exp["levels"][level.upper()]
        t = lv["thresholds"]
        a_mass, a_vol = lv["analytic_mass_kg"], lv["analytic_volume_m3"]
        a_com = lv["analytic_com_m"]
        a_i = lv["analytic_inertia_kg_m2"]  # Ixx Iyy Izz Ixy Ixz Iyz
        assert t["n_cells"] == gates["n_owned_cells"], "level/cell-count mismatch"
        assert a_mass == exp["analytic"]["mass_kg"] and a_com == exp["analytic"]["com_m"]
        assert lv["exact_rational_check"]["mass_exact"] \
            and lv["exact_rational_check"]["inertia_exact"], "frozen oracle gate not green"

        g_ok = (gates["export_status"] == "complete"
                and gates["admission_status"] == "validation_only_admissible"
                and gates["all_supplied_cells_assigned"] is True)
        verdicts["gates"][level] = {**gates, "pass": g_ok}
        say(f"{level.upper()}  body={gates['body_id']} cells={gates['n_owned_cells']} "
            f"export={gates['export_status']} admission={gates['admission_status']} "
            f"all_assigned={gates['all_supplied_cells_assigned']} -> {'PASS' if g_ok else 'FAIL'}")

        rows = []
        for name, meas, ana, tol in (
                [("mass", m["mass"], a_mass, t["T_mass_kg"])]
                + [("volume", m["volume"], a_vol, t["T_volume_m3"])]
                + [(f"com[{axis}]", m["com"][axis], a_com[axis], t["T_com_m"])
                   for axis in range(3)]
                + [(lbl, m["inertia6"][i], a_i[i], t["T_inertia_kg_m2"])
                   for i, lbl in enumerate(QUANT_LABELS)]):
            delta = abs(meas - ana)
            ok = delta <= tol
            ok_all &= ok
            rows.append({"quantity": name, "measured": meas, "analytic": ana,
                         "abs_delta": delta, "frozen_T": tol,
                         "delta_over_T": delta / tol if tol else float("inf"),
                         "verdict": "PASS" if ok else "FAIL"})
        verdicts["levels"][level] = {"rows": rows, "measured": m}
        say(f"  {'quantity':10s} {'measured':>22s} {'analytic':>20s} "
            f"{'|delta|':>12s} {'frozen T':>12s} {'d/T':>10s} verdict")
        for r in rows:
            say(f"  {r['quantity']:10s} {r['measured']:22.17g} {r['analytic']:20.17g} "
                f"{r['abs_delta']:12.3e} {r['frozen_T']:12.3e} {r['delta_over_T']:10.2e} "
                f"{r['verdict']}")
        say()

    say("Level-vs-level (V2): |q_L - q_L'| <= T_L + T_L'")
    for i in range(len(LEVELS)):
        for j in range(i + 1, len(LEVELS)):
            a, b = LEVELS[i], LEVELS[j]
            ma, mb = verdicts["levels"][a]["measured"], verdicts["levels"][b]["measured"]
            ta = exp_levels_t(a)
            tb = exp_levels_t(b)
            pairs = ([("mass", ma["mass"], mb["mass"], ta["T_mass_kg"] + tb["T_mass_kg"])]
                     + [(f"com[{k}]", ma["com"][k], mb["com"][k],
                         ta["T_com_m"] + tb["T_com_m"]) for k in range(3)]
                     + [(lbl, ma["inertia6"][n], mb["inertia6"][n],
                         ta["T_inertia_kg_m2"] + tb["T_inertia_kg_m2"])
                        for n, lbl in enumerate(QUANT_LABELS)])
            worst = max(pairs, key=lambda r: abs(r[2] - r[1]) / r[3])
            n_fail = sum(1 for _, x, y, tol in pairs if abs(y - x) > tol)
            ok_all &= n_fail == 0
            verdicts["level_pairs"][f"{a}-{b}"] = {
                "n_quantities": len(pairs), "n_fail": n_fail,
                "worst_quantity": worst[0], "worst_delta": abs(worst[2] - worst[1]),
                "worst_tol": worst[3]}
            say(f"  {a}-{b}: {len(pairs)} quantities, {n_fail} outside frozen sum-bound; "
                f"worst {worst[0]} |d|={abs(worst[2]-worst[1]):.3e} vs {worst[3]:.3e}")

    say()
    say("Growth characterization (V3): measured max |delta| vs N (envelope is worst-case)")
    verdicts["growth"] = []
    for level in LEVELS:
        rows = verdicts["levels"][level]["rows"]
        worst = max(rows, key=lambda r: r["delta_over_T"])
        t = exp_levels_t(level)
        verdicts["growth"].append({"level": level.upper(), "n_cells": t["n_cells"],
                                   "worst_quantity": worst["quantity"],
                                   "worst_abs_delta": worst["abs_delta"],
                                   "worst_delta_over_T": worst["delta_over_T"]})
        say(f"  {level.upper()}: N={t['n_cells']:4d} worst {worst['quantity']:6s} "
            f"|d|={worst['abs_delta']:.3e}  d/T={worst['delta_over_T']:.2e}")

    verdicts["ALL_PASS"] = ok_all
    with open(os.path.join(BASE, "receipts", "verdicts.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(verdicts, fh, indent=1)
        fh.write("\n")
    say("")
    say(f"OVERALL (frozen falsifier): {'ALL PASS — falsifier never fired' if ok_all else 'FALSIFIER FIRED'}")
    with open(os.path.join(BASE, "receipts", "verdict_log.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


_cache = {}


def exp_levels_t(level):
    if not _cache:
        with open(os.path.join(BASE, "derivation", "derived_expectations.json"),
                  encoding="utf-8") as fh:
            _cache["exp"] = json.load(fh)
    return _cache["exp"]["levels"][level.upper()]["thresholds"]


if __name__ == "__main__":
    main()
