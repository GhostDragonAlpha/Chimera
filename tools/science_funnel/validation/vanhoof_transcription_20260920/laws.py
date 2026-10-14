"""VTRANS laws: pcsa_closure per (muscle, specimen) row-triple + reported signals + admission tiers.

Deterministic (F4): frozen input (reconciliation.json), canonical JSON, no randomness.
Constants INHERITED, not tuned (prereg): RHO_KG_M3 = 1060.0, LAW_TOLERANCE = 0.02
  (adapters_muscle.py / admit_vanhoof.py). PCSA_mm2_pred = 1e6*(mass_g/1000)/(1060*fl_mm/1000)
  = 943.3962 * mass_g / fl_mm.
Row law (pre-registered): checkable iff all three fields TENTATIVE (unmerged anchor values);
  PASS iff |PCSA_table - PCSA_pred| / PCSA_pred <= 0.02; FAIL otherwise; the verdict is JOINT
  for the row-triple (the funnel's own semantics: a law binds the row).
Signals (REPORTED, never admitters, per prereg):
  implied_rho_g_cm3 = 1000*mass_g/(PCSA_mm2*fl_mm) per checkable row (measured distribution);
  cross-animal share ratio: value / specimen-total within a field, flagged if >50% rel dev
  from the cross-specimen median share (generous cut declared in the prereg);
  decimal register: per (field) column, mode coverage of decimal places (intake F-REGISTER cut 0.80).
ADMISSION: per prereg stop floor, admission proceeds only if law pass >= 0.90 on checkable rows
  (agreement floor already met: 1.0 >= 0.80). If the floor is missed: ZERO admission, the
  measured rates are the finding (F1 STOP).
"""
import json, os, statistics
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
RHO_KG_M3 = 1060.0
LAW_TOLERANCE = 0.02
PCSA_FACTOR = 1e6 / RHO_KG_M3 / 1000.0 * 1000.0  # = 1e6/(1060*1000)*1000
# PCSA_mm2_pred = 1e6 * (mass_g/1000) / (1060.0 * fl_mm/1000) = 943.3962... * mass_g/fl_mm
PCSA_FACTOR = 943.3962264150943
SHARE_FLAG_REL = 0.50
REGISTER_CUT = 0.80
ADMIT_FLOOR_LAW_PASS = 0.90

def main():
    rec = json.load(open(os.path.join(BASE, "reconciliation.json")))
    cells = rec["cells"]
    # grid of TENTATIVE values keyed (muscle, specimen) -> field -> value
    grid = {}
    for c in cells:
        if c["verdict"] == "TENTATIVE":
            grid.setdefault((c["muscle"], c["specimen"]), {})[c["field"]] = c["value"]

    rows = []
    n_checkable = n_pass = 0
    implied_rhos = []
    for (m, s), fvs in sorted(grid.items()):
        if not all(k in fvs for k in ("mass_g", "fl_mm", "pcsa_mm2")):
            continue
        mass, fl, pcsa = (float(fvs["mass_g"]), float(fvs["fl_mm"]), float(fvs["pcsa_mm2"]))
        pred = PCSA_FACTOR * mass / fl
        dev = abs(pcsa - pred) / pred
        verdict = "PASS" if dev <= LAW_TOLERANCE else "FAIL"
        n_checkable += 1
        n_pass += verdict == "PASS"
        implied_rhos.append(1000.0 * mass / (pcsa * fl))
        rows.append({"muscle": m, "specimen": s, "mass_g": fvs["mass_g"], "fl_mm": fvs["fl_mm"],
                     "pcsa_mm2": fvs["pcsa_mm2"], "pcsa_pred": round(pred, 4),
                     "rel_dev": round(dev, 6), "implied_rho_g_cm3": round(1000.0*mass/(pcsa*fl), 4),
                     "law": verdict})

    law_pass_rate = (n_pass / n_checkable) if n_checkable else None

    # decimal register per field (over TENTATIVE numeric cells)
    reg = {}
    for field in ("mass_g", "fl_mm", "pcsa_mm2"):
        decs = defaultdict(int)
        tot = 0
        for c in cells:
            if c["verdict"] == "TENTATIVE" and c["field"] == field:
                v = c["value"]
                tot += 1
                decs[len(v.split(".")[1]) if "." in v else 0] += 1
        mode_dec, mode_n = max(decs.items(), key=lambda kv: kv[1])
        reg[field] = {"n": tot, "mode_decimals": mode_dec, "mode_coverage": round(mode_n / tot, 4) if tot else None,
                      "register_law": "holds" if (tot and mode_n / tot >= REGISTER_CUT) else "suspended_reported"}

    # cross-animal share ratio per (field): share = value / specimen-total
    share_flags = []
    for field in ("mass_g", "fl_mm", "pcsa_mm2"):
        totals = defaultdict(float)
        for c in cells:
            if c["verdict"] == "TENTATIVE" and c["field"] == field:
                totals[c["specimen"]] += float(c["value"])
        shares = defaultdict(list)
        for c in cells:
            if c["verdict"] == "TENTATIVE" and c["field"] == field:
                shares[c["muscle"]].append((c["specimen"], float(c["value"]) / totals[c["specimen"]]))
        for m, lst in sorted(shares.items()):
            med = statistics.median([sh for _, sh in lst])
            if med <= 0:
                continue
            for spec, sh in lst:
                if med > 0 and abs(sh - med) / med > SHARE_FLAG_REL:
                    share_flags.append({"muscle": m, "specimen": spec, "field": field,
                                        "share": round(sh, 5), "median_share": round(med, 5)})

    stop_floor = {"agreement_floor": 0.80, "agreement_measured": rec["agreement"]["exact_agreement_rate_on_legible_numeric"],
                  "law_pass_floor": ADMIT_FLOOR_LAW_PASS, "law_pass_measured": round(law_pass_rate, 4) if law_pass_rate is not None else None,
                  "agreement_floor_met": (rec["agreement"]["exact_agreement_rate_on_legible_numeric"] or 0) >= 0.80,
                  "law_pass_floor_met": law_pass_rate is not None and law_pass_rate >= ADMIT_FLOOR_LAW_PASS}
    stop_floor["F1_STOP_FIRED"] = not (stop_floor["agreement_floor_met"] and stop_floor["law_pass_floor_met"])

    out = {"constants": {"RHO_KG_M3": RHO_KG_M3, "LAW_TOLERANCE": LAW_TOLERANCE,
                          "PCSA_FACTOR": PCSA_FACTOR, "SHARE_FLAG_REL": SHARE_FLAG_REL,
                          "REGISTER_CUT": REGISTER_CUT},
           "law_rows": rows, "n_checkable_rows": n_checkable, "n_law_pass": n_pass,
           "law_pass_rate": round(law_pass_rate, 4) if law_pass_rate is not None else None,
           "law_dev_percentiles": {p: (round(sorted(r["rel_dev"] for r in rows)[min(len(rows)-1, int(p/100.0*len(rows)))], 6)
                                       if rows else None) for p in (5, 25, 50, 75, 95)},
           "implied_rho_g_cm3": {"n": len(implied_rhos),
                                  "min": round(min(implied_rhos), 4) if implied_rhos else None,
                                  "p25": round(statistics.quantiles(implied_rhos, n=4)[0], 4) if len(implied_rhos) >= 4 else None,
                                  "median": round(statistics.median(implied_rhos), 4) if implied_rhos else None,
                                  "p75": round(statistics.quantiles(implied_rhos, n=4)[2], 4) if len(implied_rhos) >= 4 else None,
                                  "max": round(max(implied_rhos), 4) if implied_rhos else None},
           "decimal_register": reg, "share_ratio_flags": share_flags,
           "stop_floor": stop_floor,
           "admission": {"admitted": 0 if stop_floor["F1_STOP_FIRED"] else None,
                          "note": "F1 STOP: zero admission, measured rates are the finding" if stop_floor["F1_STOP_FIRED"] else "proceeds"}}
    with open(os.path.join(BASE, "laws.json"), "w", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(json.dumps({k: out[k] for k in ("n_checkable_rows", "n_law_pass", "law_pass_rate",
                                           "law_dev_percentiles", "implied_rho_g_cm3",
                                           "decimal_register", "stop_floor")},
                     indent=1, sort_keys=True))

if __name__ == "__main__":
    main()
