"""VLAW laws_registered: re-run the pcsa_closure law pass at the REGISTERED constant.

Rule-0 discipline (prereg receipt.json in this directory, commit 038aebd8):
  * The ONE re-registered constant is rho from constants.json -- route stated_cited
    (the paper's own stated-and-used 0.0011 g/mm3 = 1.1 g/cm3). Tolerance 0.02, the
    0.90/0.80 floors, the law form, and the deviation-class bands (0.02 / 0.10) are
    INHERITED/pre-named: none of them is chosen from any pass rate (F2).
  * Byte-consumes the frozen reconciliation.json (654 TENTATIVE values are PINS, F3):
    file sha256 AND the canonical value-grid sha256 are verified against the prereg's
    pins before anything is computed. No image is ever read; no value is ever edited.
  * Deterministic (F4): frozen inputs only, canonical JSON output, no randomness,
    no timestamps in derived artifacts.

Outputs laws_registered.json: per-row verdicts at the registered constant, measured
pass rate vs the inherited 0.90 floor, deviation classes (descriptive, never
admitters), residual structure per muscle/specimen, named suspects (values named,
pin holds -- never changed), and the admission gate.
"""
import hashlib
import json
import os
import statistics
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))

PREREG_FILE = "receipt.json"
CONSTANTS_FILE = "constants.json"
RECONCILE_FILE = os.path.join("..", "vanhoof_transcription_20260920", "reconciliation.json")
LANDED_LAWS_FILE = os.path.join("..", "vanhoof_transcription_20260920", "laws.json")

LAW_TOLERANCE_INHERITED = 0.02
FLOOR_LAW_PASS_INHERITED = 0.90
FLOOR_AGREEMENT_INHERITED = 0.80
DEV_CLASS_MODERATE_MAX = 0.10   # descriptive band edge, pre-named in prereg
FIELDS = ("mass_g", "fl_mm", "pcsa_mm2")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_constants():
    path = os.path.join(BASE, CONSTANTS_FILE)
    if not os.path.isfile(path):
        raise SystemExit("REFUSAL: constants.json missing -- the law re-run refuses to "
                         "run without a prior constant registration (prereg work_plan step 2)")
    c = json.load(open(path))
    if c.get("schema") != "chimera.rule0.constant_registration.v1":
        raise SystemExit("REFUSAL: constants.json schema mismatch")
    route = c.get("route")
    if route not in ("stated_cited", "measured_declared"):
        raise SystemExit("REFUSAL: constants.json route must be stated_cited or measured_declared")
    const = c.get("constant") or {}
    rho = const.get("rho_g_cm3")
    if not isinstance(rho, (int, float)) or rho <= 0:
        raise SystemExit("REFUSAL: constants.json rho_g_cm3 must be a positive number")
    if const.get("rho_as_printed_in_source") is None or not (c.get("evidence") or {}).get("quotes_verbatim"):
        raise SystemExit("REFUSAL: constants.json lacks its evidence block (route a) or printed form")
    unchanged = c.get("unchanged_inherited_constants") or {}
    if unchanged.get("law_tolerance_rel") != LAW_TOLERANCE_INHERITED:
        raise SystemExit("REFUSAL: tolerance was re-sized -- prereg forbids this (F2)")
    if unchanged.get("floor_law_pass") != FLOOR_LAW_PASS_INHERITED or \
       unchanged.get("floor_agreement") != FLOOR_AGREEMENT_INHERITED:
        raise SystemExit("REFUSAL: floors were moved -- prereg forbids this (F2)")
    return c, float(rho)


def load_reconciliation_with_pins():
    prereg = json.load(open(os.path.join(BASE, PREREG_FILE)))
    pin = prereg["target"]["value_pin"]
    frozen = prereg["target"]["frozen_inputs"]
    rec_path = os.path.join(BASE, RECONCILE_FILE)
    got = sha256_file(rec_path)
    if got != frozen["reconciliation.json"]:
        raise SystemExit("REFUSAL: reconciliation.json sha256 %s != prereg pin" % got)
    rec = json.load(open(rec_path))
    tent = [(c["muscle"], c["specimen"], c["field"], c["value"])
            for c in rec["cells"] if c["verdict"] == "TENTATIVE"]
    tent.sort()
    blob = json.dumps(tent, separators=(",", ":"), sort_keys=True).encode("utf-8")
    grid_sha = hashlib.sha256(blob).hexdigest()
    if grid_sha != pin["sha256"]:
        raise SystemExit("REFUSAL: TENTATIVE value grid sha256 %s != prereg pin %s "
                         "(F3 NO-RETRANSCRIBE: the pins are absolute)" % (grid_sha, pin["sha256"]))
    if len(tent) != pin["n_cells"] or rec["agreement"]["TENTATIVE"] != pin["n_cells"]:
        raise SystemExit("REFUSAL: TENTATIVE count drift vs prereg pin")
    if rec["agreement"]["exact_agreement_rate_on_legible_numeric"] != 1.0:
        raise SystemExit("REFUSAL: landed double-entry agreement is not the pinned 1.0")
    return rec, grid_sha


def dev_class(dev):
    if dev <= LAW_TOLERANCE_INHERITED:
        return "law_pass"
    if dev <= DEV_CLASS_MODERATE_MAX:
        return "moderate_register_unrounded"
    return "large_per_row_structure"


def compute_rows(rec, rho_g_cm3):
    """The single verdict computation, shared by the law run and the admission
    driver (one math path; the admission driver re-derives and cross-checks)."""
    pcsa_factor = 1e6 / (rho_g_cm3 * 1000.0)  # mm2 pred per (g/mm): never a rounded literal
    grid = {}
    for c in rec["cells"]:
        if c["verdict"] == "TENTATIVE":
            grid.setdefault((c["muscle"], c["specimen"]), {})[c["field"]] = c["value"]
    rows = []
    for (m, s), fvs in sorted(grid.items()):
        if not all(k in fvs for k in FIELDS):
            continue
        mass, fl, pcsa = float(fvs["mass_g"]), float(fvs["fl_mm"]), float(fvs["pcsa_mm2"])
        pred = pcsa_factor * mass / fl
        dev = abs(pcsa - pred) / pred
        verdict = "PASS" if dev <= LAW_TOLERANCE_INHERITED else "FAIL"
        rows.append({"muscle": m, "specimen": s,
                     "mass_g": fvs["mass_g"], "fl_mm": fvs["fl_mm"], "pcsa_mm2": fvs["pcsa_mm2"],
                     "pcsa_pred_mm2": round(pred, 4), "rel_dev": round(dev, 6),
                     "implied_rho_g_cm3": round(1000.0 * mass / (pcsa * fl), 4),
                     "deviation_class": dev_class(dev), "law": verdict})
    return rows


def main():
    registration, rho_g_cm3 = load_constants()
    rec, grid_sha = load_reconciliation_with_pins()

    pcsa_factor = 1e6 / (rho_g_cm3 * 1000.0)  # mm2 pred per (g/mm): never a rounded literal

    rows = compute_rows(rec, rho_g_cm3)
    implied_rhos = [1000.0 * float(r["mass_g"]) / (float(r["pcsa_mm2"]) * float(r["fl_mm"]))
                    for r in rows]

    n_checkable = len(rows)
    n_pass = sum(1 for r in rows if r["law"] == "PASS")
    pass_rate = (n_pass / n_checkable) if n_checkable else None

    devs = sorted(r["rel_dev"] for r in rows)
    percentiles = {p: (round(devs[min(len(devs) - 1, int(p / 100.0 * len(devs)))], 6)
                       if devs else None) for p in (5, 25, 50, 75, 95)}

    per_muscle = {}
    for r in rows:
        d = per_muscle.setdefault(r["muscle"], {"n_rows": 0, "n_pass": 0, "rel_devs": []})
        d["n_rows"] += 1
        d["n_pass"] += r["law"] == "PASS"
        d["rel_devs"].append(r["rel_dev"])
    per_muscle_summary = {
        m: {"n_rows": d["n_rows"], "n_pass": d["n_pass"],
            "dev_p50": round(statistics.median(d["rel_devs"]), 6),
            "dev_max": round(max(d["rel_devs"]), 6)}
        for m, d in sorted(per_muscle.items())}

    per_specimen = {}
    for r in rows:
        d = per_specimen.setdefault(r["specimen"], {"n_rows": 0, "n_pass": 0, "rel_devs": []})
        d["n_rows"] += 1
        d["n_pass"] += r["law"] == "PASS"
        d["rel_devs"].append(r["rel_dev"])
    per_specimen_summary = {
        s: {"n_rows": d["n_rows"], "n_pass": d["n_pass"],
            "dev_p50": round(statistics.median(d["rel_devs"]), 6),
            "dev_max": round(max(d["rel_devs"]), 6)}
        for s, d in sorted(per_specimen.items())}

    class_counts = defaultdict(int)
    for r in rows:
        class_counts[r["deviation_class"]] += 1

    # named suspects: FAIL rows in the large band -- named with their values and
    # implied rho (F3: the values are named, the pin holds, nothing is changed)
    suspects = [{"muscle": r["muscle"], "specimen": r["specimen"],
                 "mass_g": r["mass_g"], "fl_mm": r["fl_mm"], "pcsa_mm2": r["pcsa_mm2"],
                 "rel_dev": r["rel_dev"], "implied_rho_g_cm3": r["implied_rho_g_cm3"]}
                for r in rows if r["law"] == "FAIL" and r["deviation_class"] == "large_per_row_structure"]

    # comparison against the landed inherited-constant run (frozen, sha-pinned)
    landed_path = os.path.normpath(os.path.join(BASE, LANDED_LAWS_FILE))
    landed = json.load(open(landed_path))
    landed_sha = sha256_file(landed_path)
    prereg = json.load(open(os.path.join(BASE, PREREG_FILE)))
    if landed_sha != prereg["target"]["frozen_inputs"]["laws.json_landed_inherited_run"]:
        raise SystemExit("REFUSAL: landed laws.json sha drift")
    landed_pass_rows = {(r["muscle"], r["specimen"]) for r in landed["law_rows"] if r["law"] == "PASS"}
    now_pass_rows = {(r["muscle"], r["specimen"]) for r in rows if r["law"] == "PASS"}

    gate_pass = pass_rate is not None and pass_rate >= FLOOR_LAW_PASS_INHERITED
    agreement = rec["agreement"]["exact_agreement_rate_on_legible_numeric"]

    # Gate semantics (prereg-faithful): the floors gate TUNING, not the pre-registered
    # tiers. F1 firing means: the headline claim (>= 90% at the registered constant) is
    # measured FALSE, reported as such; the constant/tolerance/floors are not moved; the
    # residual is reported as structure. Cell disposition itself is admission_tiers_original
    # (law-PASS rows ADMITTED, FAIL rows REFUSED row_closure_violation), which the prereg
    # registered unconditionally and the task envelope orders executed.

    out = {
        "schema": "chimera.rule0.law_reregistration.v1",
        "lane": "vanhoof_law_20260920",
        "run_note": "deterministic re-run of the landed 218-row law pass at the registered constant; "
                    "timestamps live in receipts, never in derived artifacts",
        "registered_constant": {
            "route": registration["route"],
            "rho_g_cm3": rho_g_cm3,
            "rho_as_printed_in_source": registration["constant"]["rho_as_printed_in_source"],
            "source_quote": "the density value of 0.0011 g/mm3 is used in the calculation of the "
                            "PCSA for all muscles in this study (Vanhoof et al. 2021, Methods 2.3)",
            "pcsa_factor_mm2_per_g_per_mm": pcsa_factor,
            "evidence_file": CONSTANTS_FILE,
        },
        "inherited_unchanged": {
            "law_tolerance_rel": LAW_TOLERANCE_INHERITED,
            "floor_law_pass": FLOOR_LAW_PASS_INHERITED,
            "floor_agreement": FLOOR_AGREEMENT_INHERITED,
            "law_form": "PCSA_pred = 1e6*(mass_g/1000)/(rho_g_cm3*fl_mm/1000); joint row verdict",
        },
        "input_pins_verified": {
            "reconciliation.json_sha256_ok": True,
            "tentative_grid_sha256": grid_sha,
            "n_tentative": rec["agreement"]["TENTATIVE"],
            "n_marker_agreed": rec["agreement"]["MARKER_AGREED"],
            "n_blank_agreed": rec["agreement"]["BLANK_AGREED"],
            "landed_laws_json_sha256": landed_sha,
            "no_image_read": True, "no_value_edited": True,
        },
        "law_rows": rows,
        "n_checkable_rows": n_checkable,
        "n_pass": n_pass,
        "law_pass_rate": round(pass_rate, 4) if pass_rate is not None else None,
        "dev_percentiles": percentiles,
        "implied_rho_g_cm3": {
            "n": len(implied_rhos),
            "min": round(min(implied_rhos), 4), "max": round(max(implied_rhos), 4),
            "p25": round(statistics.quantiles(implied_rhos, n=4)[0], 4),
            "median": round(statistics.median(implied_rhos), 4),
            "p75": round(statistics.quantiles(implied_rhos, n=4)[2], 4),
        },
        "deviation_classes": {
            "bands_declared_in_prereg": {
                "law_pass": "rel_dev <= 0.02",
                "moderate_register_unrounded": "0.02 < rel_dev <= 0.10",
                "large_per_row_structure": "rel_dev > 0.10"},
            "counts": dict(sorted(class_counts.items())),
            "role": "descriptive only -- never admitters (prereg admission_tiers_original)"},
        "residual_structure": {
            "per_muscle": per_muscle_summary,
            "per_specimen": per_specimen_summary,
            "note": "the source's own per-row inconsistencies (merged muscles: multi-belly sums per "
                    "the paper's stated rule; small intrinsic hand muscles whose density the paper did "
                    "not measure individually) are the source's truth: named, not repaired"},
        "named_suspects": {
            "definition": "FAIL rows in the large_per_row_structure band; their printed values and "
                          "implied density are named here -- the F3 pin holds, no value is changed, "
                          "no image is re-read; with double-entry agreement 1.0 a misread digit is "
                          "already weighed against",
            "count": len(suspects),
            "rows": suspects},
        "comparison_to_landed_inherited_run": {
            "landed_constant_rho_kg_m3": 1060.0,
            "landed_n_pass": landed["n_law_pass"],
            "landed_pass_rate": landed["law_pass_rate"],
            "registered_n_pass": n_pass,
            "registered_pass_rate": round(pass_rate, 4) if pass_rate is not None else None,
            "rows_passing_both": len(landed_pass_rows & now_pass_rows),
            "rows_passing_only_at_registered": len(now_pass_rows - landed_pass_rows),
            "rows_passing_only_at_inherited": len(landed_pass_rows - now_pass_rows),
        },
        "stop_floor": {
            "agreement_floor": FLOOR_AGREEMENT_INHERITED,
            "agreement_measured": agreement,
            "agreement_floor_met": agreement >= FLOOR_AGREEMENT_INHERITED,
            "law_pass_floor": FLOOR_LAW_PASS_INHERITED,
            "law_pass_measured": round(pass_rate, 4) if pass_rate is not None else None,
            "law_pass_floor_met": bool(gate_pass),
            "verdict": ("BOTH FLOORS MET -- the prereg's headline claim is measured TRUE; "
                        "tiers execute"
                        if (gate_pass and agreement >= FLOOR_AGREEMENT_INHERITED) else
                        "F1 LAW-STILL-FAILS (FIRED) -- the prereg's headline claim (>= 0.90 at "
                        "the registered constant) is measured FALSE at the rate above; reported "
                        "as the finding, never tuned away (constant, tolerance, floors unchanged); "
                        "the residual is per-row source inconsistency -- a data-quality finding "
                        "about the SOURCE (which muscles/animals deviate + deviation classes + "
                        "named suspects), not a tuning invitation. Cell disposition proceeds per "
                        "the prereg's pre-registered admission_tiers_original: cells of law-PASS "
                        "rows ADMITTED, cells of FAIL rows REFUSED row_closure_violation."),
        },
        "admission_gate": ("FLOORS_MET_TIERS_EXECUTE"
                           if (gate_pass and agreement >= FLOOR_AGREEMENT_INHERITED)
                           else "F1_FIRED_TIERS_EXECUTE_PER_PREREG"),
    }

    with open(os.path.join(BASE, "laws_registered.json"), "w", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(json.dumps({k: out[k] for k in ("n_checkable_rows", "n_pass", "law_pass_rate",
                                          "dev_percentiles", "implied_rho_g_cm3",
                                          "deviation_classes", "comparison_to_landed_inherited_run",
                                          "stop_floor", "admission_gate")}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
