"""VLAW cross_specimen: the per-muscle summary the forearm/hand books consume.

Per muscle (all 35 source keys, the source's own structure -- merged rows included
under their printed labels) and per field (mass_g / fl_mm / pcsa_mm2): n animals
of Mm1-Mm7 measured, mean / min / max of the printed values, plus the row law
verdict counts riding along as conditions. Built from ALL 654 TENTATIVE cells of
the pinned reconciliation -- admitted and refused alike: the summary is the
source's extraction, not an admission filter. No smoothing, no imputation, no
outlier removal anywhere (prereg cross_specimen_summary_plan).

Deterministic (F4): frozen inputs only, canonical JSON + fixed-format CSV,
no randomness, no timestamps in derived artifacts.
"""
import json
import os
import statistics
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import laws_registered as L  # noqa: E402

FIELDS = ("mass_g", "fl_mm", "pcsa_mm2")
SPECIMENS = ["Mm1", "Mm2", "Mm3", "Mm4", "Mm5", "Mm6", "Mm7"]


def main():
    registration, rho = L.load_constants()
    rec, grid_sha = L.load_reconciliation_with_pins()
    rows = L.compute_rows(rec, rho)
    verdict = {(r["muscle"], r["specimen"]): r for r in rows}

    grid = {}
    group_of = {}
    for c in rec["cells"]:
        if c["verdict"] == "TENTATIVE":
            grid.setdefault(c["muscle"], {}).setdefault(c["specimen"], {})[c["field"]] = c["value"]

    # muscle groups ride along for the consumers (measured from the pass files'
    # group column; a mechanical read for identity, never for values)
    import glob
    for p in sorted(glob.glob(os.path.join(BASE, "..", "vanhoof_transcription_20260920", "passA", "*.json"))):
        for c in json.load(open(p))["cells"]:
            group_of.setdefault(c["m"], c["g"])

    summary = {}
    for m in sorted(grid):
        per_field = {}
        law_rows = law_pass = 0
        for s in SPECIMENS:
            if s in grid[m] and (m, s) in verdict:
                law_rows += 1
                law_pass += verdict[(m, s)]["law"] == "PASS"
        for f in FIELDS:
            vals = [float(grid[m][s][f]) for s in SPECIMENS if s in grid[m] and f in grid[m][s]]
            per_field[f] = {
                "n": len(vals),
                "mean": round(statistics.fmean(vals), 4) if vals else None,
                "min": min(vals) if vals else None,
                "max": max(vals) if vals else None,
                "specimens": [s for s in SPECIMENS if s in grid[m] and f in grid[m][s]],
            }
        summary[m] = {
            "muscle_group": group_of.get(m),
            "law_rows": law_rows, "law_pass_rows": law_pass,
            "fields": per_field,
        }

    out = {
        "schema": "chimera.rule0.cross_specimen_summary.v1",
        "lane": "vanhoof_law_20260920",
        "source": {"sheet": "JOA-238-321-s002", "doi": "10.1111/joa.13314", "pmcid": "PMC7812139",
                   "species": "Macaca mulatta adult (Mm1-Mm7)",
                   "tiff_sha256": "cb9e91be3d2345182b6d2b956245b76905243d4bbf37fff79c3d96a802e5debe"},
        "provenance": {"inputs": "pinned reconciliation.json (grid sha256 %s)" % grid_sha,
                       "constants": {"rho_g_cm3": rho, "route": registration["route"]},
                       "law_verdicts": "laws_registered.json; ride along as conditions, never a filter"},
        "discipline": "all 654 TENTATIVE cells summarized (admitted and refused alike); no smoothing, "
                      "no imputation, no outlier removal; merged/marker structure stays in the counts",
        "n_cells_summarized": sum(len(v) for mg in grid.values() for v in mg.values()),
        "muscles": summary,
    }
    with open(os.path.join(BASE, "cross_specimen_summary.json"), "w", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)

    lines = ["muscle,muscle_group,field,n,mean,min,max,law_pass_rows,law_rows"]
    for m in sorted(summary):
        g = summary[m]["muscle_group"] or ""
        for f in FIELDS:
            d = summary[m]["fields"][f]
            lines.append("%s,%s,%s,%d,%s,%s,%s,%d,%d" % (
                m, g, f, d["n"],
                "" if d["mean"] is None else "%.4f" % d["mean"],
                "" if d["min"] is None else ("%g" % d["min"]),
                "" if d["max"] is None else ("%g" % d["max"]),
                summary[m]["law_pass_rows"], summary[m]["law_rows"]))
    with open(os.path.join(BASE, "cross_specimen_summary.csv"), "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("muscles: %d, cells summarized: %d" % (len(summary), out["n_cells_summarized"]))
    for m in ("APB", "FDP", "FDS", "Bb", "conn. FDS-FDP"):
        if m in summary:
            print(m, json.dumps(summary[m]["fields"], sort_keys=True)[:220])


if __name__ == "__main__":
    main()
