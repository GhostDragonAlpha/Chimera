"""VTRANS final receipt builder: per-falsifier verdicts + measured rates + refusal taxonomy.
Deterministic: reads frozen reconciliation.json + laws.json + crops_manifest.json.
"""
import glob, json, os
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
rec = json.load(open(os.path.join(BASE, "reconciliation.json")))
laws = json.load(open(os.path.join(BASE, "laws.json")))
man = json.load(open(os.path.join(BASE, "crops_manifest.json")))

marker_classes = Counter(c.get("marker") or "" for c in rec["cells"] if c["verdict"] == "MARKER_AGREED")
verdicts = Counter(c["verdict"] for c in rec["cells"])

per_specimen_rows = Counter()
for r in laws["law_rows"]:
    per_specimen_rows[r["specimen"]] += 1

admitted_rows_by_muscle = sorted({r["muscle"] for r in laws["law_rows"] if r["law"] == "PASS"})

receipt = {
 "schema": "chimera.rule0.lane_receipt.v1",
 "lane": "vanhoof_transcription_20260920",
 "branch": "lane/vanhoof-transcription-20260920 @ base d374ab04",
 "agent": "GLM 5.3 (Agent: vtrans)",
 "prereg": "receipt.json in this directory (frozen; written before any pixel read)",
 "target_measured": {
  "sheet": "JOA-238-321-s002.tif sha256 cb9e91be3d2345182b6d2b956245b76905243d4bbf37fff79c3d96a802e5debe",
  "true_structure_measured": {
   "panel1": "header y14-114; 39 muscle rows APB..B (Thenar 4, Hypothenar 3, Intermediate 4, Flexor 6, Extensor 9, Rotator 4, Ext. Thumb 4, Upper arm 5); specimens Mm1-Mm4",
   "panel2": "header y1651-1734; 34 muscle rows APB..APL (no Upper arm group); specimens Mm5-Mm7",
   "row_start_correction": "rows start at y=114 (P1) / y=1734 (P2); the first prereg-pass assumption (rows at y232/1812) was corrected by mechanical cross-checks (text-blob scan, group-fill boundary, band crops) before any value was keyed from the misread bands",
   "cells_total": 774,
   "note_on_intake_1512": "the intake's 1512 = its 54x28 machinery grid MODEL of the page; the true table structure is 774 value positions; both counts are reported, nothing was forced"
  }
 },
 "double_entry": {
  "passA": "12/12 tiles, row-wise muscle-major, forward panel order, committed before pass B started",
  "passB": "12/12 tiles, column-wise animal-major, REVERSE panel order, produced without consulting pass A",
  "exact_agreement_rate_on_legible_numeric_cells": rec["agreement"]["exact_agreement_rate_on_legible_numeric"],
  "floor": 0.80, "floor_met": True,
  "cells_classified": rec["agreement"]["cells_total_classified"],
  "TENTATIVE": verdicts["TENTATIVE"], "DISPUTED": verdicts["DISPUTED"],
  "MARKER_AGREED": verdicts["MARKER_AGREED"], "BLANK_AGREED": verdicts["BLANK_AGREED"],
  "count_identity": "774 = 654 TENTATIVE + 105 MARKER_AGREED + 15 BLANK_AGREED (merged-cell covered positions); zero silent drops",
  "normalization_rules_declared": [
   "numeric comparison format-normalized (Decimal, 1.40==1.4); printed strings preserved",
   "markers compared as refusal CLASS (marker_absent / marker_absent_cfr / marker_damaged / marker_not_measured / marker_crossref_APB / marker_crossref_FDP): tile-edge cuts truncated some parenthetical crossref tails in one pass; both raw texts retained in pass files",
   "merged-cell anchor/covered role ignored for valueless block-spanning marker cells (no value semantics)"
  ]
 },
 "laws": {
  "constants_inherited_not_tuned": {"rho_kg_m3": 1060.0, "rel_tolerance": 0.02,
   "sources": "adapters_muscle.py MUSCLE_DENSITY_KG_M3 / LAW_TOLERANCE; admit_vanhoof.py; prereg receipt"},
  "pcsa_closure": "PCSA_pred = 943.3962 * mass_g / fl_mm; PASS iff |PCSA_table-PCSA_pred|/PCSA_pred <= 0.02",
  "n_checkable_rows": laws["n_checkable_rows"], "n_pass": laws["n_law_pass"],
  "law_pass_rate": laws["law_pass_rate"], "floor": 0.90, "floor_met": False,
  "deviation_percentiles": laws["law_dev_percentiles"],
  "implied_rho_g_cm3": laws["implied_rho_g_cm3"],
  "finding": "the source table's printed PCSA does NOT close against mass/(1060*FL) at 2%: only 19/218 rows pass (8.72%). Measured implied density median 1.1004 g/cm3 (IQR 1.095-1.115), i.e. the authors' own constant is ~1.10 g/cm3, and the residual spread (p5 1.2% .. p95 13.5%) indicates additional per-row effects (pennation or unrounded intermediates). The prereg's P-CLOSURE prediction (rounding-driven, median <1%) is MEASURED FALSE.",
  "not_runnable_laws": ["mass_additivity_dev (no belly/tendon mass columns)", "density law (no volume column)", "mtu additivity (no MTU/tendon columns)"],
  "auxiliary_signals": {"decimal_register": laws["decimal_register"],
                          "share_ratio_flags_count": len(laws["share_ratio_flags"]),
                          "note": "reported signals only, never admitters (prereg)"}
 },
 "stop_floor": {
  "preregistered": "admission proceeds only if agreement >= 0.80 AND law pass >= 0.90",
  "agreement_measured": 1.0, "agreement_floor_met": True,
  "law_pass_measured": laws["law_pass_rate"], "law_pass_floor_met": False,
  "F1_STOP_FIRED": laws["stop_floor"]["F1_STOP_FIRED"],
  "consequence": "ZERO admission. The honest result is reported: the double-entry vision transcription fully succeeded; the source table's own PCSA column fails the inherited closure law, so no cell can be ADMITTED under the preregistered instrument. A successor prereg would have to register the law against the source's own arithmetic (implied rho median 1.1004 g/cm3 + a tolerance sized from the measured residual distribution) -- that is a new registration, not this lane's tuning."
 },
 "refusal_taxonomy_counts": {
  "admitted": 0,
  "numeric_unadmitted_F1_stop": verdicts["TENTATIVE"],
  "law_row_fail_at_inherited_constants": laws["n_checkable_rows"] - laws["n_law_pass"],
  "law_row_pass_at_inherited_constants": laws["n_law_pass"],
  "marker_absent_cfr": marker_classes.get("marker_absent_cfr", 0),
  "marker_absent_plain": marker_classes.get("marker_absent", 0),
  "marker_crossref_APB": marker_classes.get("marker_crossref_APB", 0),
  "marker_crossref_FDP": marker_classes.get("marker_crossref_FDP", 0),
  "merged_cell_covered_positions": verdicts["BLANK_AGREED"],
  "blank_label_cell_note": "P2 conn row's muscle-label cell is blank in the source (blob-verified); the row's VALUES are present and transcribed; identity kept by position after FDP"
 },
 "falsifier_verdicts": {
  "F1_STOP_FLOOR": "FIRED -- law-pass floor missed: 0.0872 << 0.90 (agreement floor met at 1.0). STOP honored: zero admission, rates reported, constants not moved.",
  "F2_NO_GUESS": "HELD -- zero guessed numbers anywhere; every numeric cell carries both-pass agreement (654/654 exact); every non-numeric source marker is a named refusal.",
  "F3_PROVENANCE": "HELD -- every TENTATIVE value is keyed (muscle x specimen x field) with panel + tile crop sha256 (stamped from crops_manifest.json pins) + both pass values + legibility classes + law row verdict in laws.json/reconciliation.json.",
  "F4_DETERMINISM": "GREEN -- prep manifest, reconcile.py and laws.py each 3-run byte-identical (cmp-verified); the transcription passes are human-class reads and are NOT claimed deterministic (the laws and pins are the determinism, per prereg).",
  "F5_LANE_SCOPE": "HELD -- lane dir + out-of-repo staging only (E:/ChimeraWork/vanhoof2-staging/ holds derived PNG tiles; no image bytes committed); S1 never transcribed; no shared tooling touched.",
  "P_CLOSURE_PREDICTION": "MEASURED FALSE (median dev 3.8% vs predicted <1%) -- reported, not tuned around.",
  "P_AGREE_PREDICTION": "EXCEEDED (1.0 vs predicted 0.85-0.95).",
  "P_UNREADABLE_PREDICTION": "MEASURED BETTER THAN PREDICTED -- 0% of numeric cells unreadable at 2x zoom tiles; the intake's 4.8% machinery CONFIDENT rate reflected the OCR route, not human-class vision."
 },
 "artifacts": {
  "prereg": "receipt.json", "lane_record": "record.md",
  "prep": "prep_s2_panels.py + crops_manifest.json (12 tiles, pinned, 3-run byte-identical)",
  "transcriptions": "passA/*.json (12), passB/*.json (12), sha-stamped",
  "reconcile": "reconcile.py + reconciliation.json", "laws": "laws.py + laws.json",
  "staging_out_of_git": "E:/ChimeraWork/vanhoof2-staging/s2_tiles/*.png (re-derivable from the committed pinned TIFF + prep script + declared constants)"
 },
 "successor_scope_named": "re-register the closure law at the source's own arithmetic: (a) rho = 1.10 g/cm3 (measured implied median 1.1004, IQR 1.095-1.115) or the paper's stated constant if obtainable from the article PDFs (named-not-obtained by the intake); (b) tolerance sized from the measured residual distribution (p95 13.5%), or per-row pennation modeling; (c) the double-entry transcription in this lane (654 TENTATIVE values, 100% agreement) is the ready input -- no re-reading needed.",
 "no_records_admitted": 0
}

with open(os.path.join(BASE, "receipt_final.json"), "w", newline="\n") as f:
    json.dump(receipt, f, indent=1, sort_keys=True)
print(json.dumps(receipt["refusal_taxonomy_counts"], indent=1, sort_keys=True))
print("admitted rows by muscle (at inherited constants, NOT admitted):", admitted_rows_by_muscle)
print("checkable rows per specimen:", dict(sorted(per_specimen_rows.items())))
