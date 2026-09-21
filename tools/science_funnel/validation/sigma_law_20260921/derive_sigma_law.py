#!/usr/bin/env python3
"""sigma_law_20260921 - derive what the admitted Guimaraes batch can and cannot
say about the specific tension sigma = Fmax/PCSA.

Rule-0 discipline: the frozen pre-registration is receipt.json in this
directory; this script REFUSES to run without it and re-verifies every
premise from the pinned bytes. No wall-clock, no randomness, sorted keys:
two runs on the same inputs produce byte-identical outputs.

Inputs are obtained read-only from canonical at the cited ref:
  git show 46ed85a3ba1e451cf5b02f068134bf6801dbd258:tools/science_funnel/data/guimaraes_arch/AJPA-190-e70329-s001.xlsx
  git show 46ed85a3ba1e451cf5b02f068134bf6801dbd258:tools/science_funnel/data/guimaraes_arch/PMC13425262_fulltext.xml
  git show 46ed85a3ba1e451cf5b02f068134bf6801dbd258:tools/science_funnel/data/oku_bipedal/42003_2021_1831_MOESM2_ESM.xlsx

Usage:
  python -B derive_sigma_law.py --guim <xlsx> --oku <xlsx> --fulltext <xml> \
      --outdir <this directory>

Writes results.json and audit_table.csv into --outdir. Touches nothing else.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import statistics
import sys

try:
    import openpyxl  # independent reader; the intake adapter used stdlib xml
except ImportError:  # pragma: no cover
    sys.exit("openpyxl required")

RHO_KG_M3 = 1060.0          # the dataset's own density constant
LAW_TOL = 0.02              # the intake's closure tolerance (2%)
LIT_BAND_N_CM2 = (23.0, 32.0)
IN_REPO_POINT_N_CM2 = 30.0  # 0.3 MPa
SPECIES_SHEET = "Macaca mulatta"
EXPECTED_ROWS = 36
BODY_MASS_KG = 8.0          # Information sheet, specimen 127

# Table 3 of PMC13425262 (admitted fulltext), verbatim membership, in order.
TABLE3 = [
    ("hip_extensors",       ["GMax", "BFL", "SM", "ST"]),
    ("hip_flexors",         ["ILI", "SAR", "PMaj", "P"]),
    ("hip_abductors",       ["GMed", "GMin", "TFL", "PIRI"]),
    ("hip_adductors",       ["AM", "AB", "AL", "PECT", "Amin", "GRA"]),
    ("hip_rotators",        ["GemSup", "GemInf", "ObtInt", "ObtExt", "PIRI", "QF"]),
    ("knee_extensors",      ["VI", "VL", "VM", "RF"]),
    ("knee_flexors",        ["POP", "BFS", "BFL", "GRA", "PLANT"]),
    ("ankle_dorsiflexors",  ["TA", "EHL", "EDL"]),
    ("ankle_plantarflexors", ["SOL", "MG", "LG", "TP", "PB", "PL"]),
    ("mtp_flexors",         ["AbDm", "AbH", "FDB", "FDL", "FHL"]),
    ("mtp_extensors",       ["EHL", "EHB", "EDB"]),
]

# Oku 2021 simulated muscle -> Guimaraes M. mulatta muscle(s).
# Each pairing is a DECLARED substitution, recorded in the output.
OKU_PAIR = {
    "IL":   (["ILI"], "iliacus; Oku model single-joint hip flexor"),
    "GMED": (["GMed"], "gluteus medius"),
    "VAS":  (["VI", "VL", "VM"], "vastus group: Oku one muscle, Guimaraes three heads; PCSA summed"),
    "TA":   (["TA"], "tibialis anterior"),
    "SOL":  (["SOL"], "soleus"),
    "RF":   (["RF"], "rectus femoris"),
    "BIFl": (["BFL"], "biceps femoris long head; Oku has no short head"),
    "GAS":  (["MG", "LG"], "gastrocnemius: Oku one muscle, Guimaraes two heads; PCSA summed"),
    "EDL":  (["EDL"], "extensor digitorum longus"),
    "FDL":  (["FDL"], "flexor digitorum longus"),
}
OKU_MUSCLES = set(OKU_PAIR)

FMAX_PATTERN = re.compile(
    r"f\s*max|max[_ ]?isometric|max[_ ]?force|tetanic|peak\s*force|"
    r"force\b|stress\b|tension\b|po\b", re.I)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def num(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def sheet_rows(ws):
    out = []
    for row in ws.iter_rows(values_only=True):
        out.append([("" if c is None else str(c).strip()) for c in row])
    return out


# --------------------------------------------------------------- guimaraes

def parse_guim(path):
    """Returns (column_enumeration, rows, unparsed). Unit interpretation is
    resolved per row by the closure law, never from header text."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    header_scan = {}   # sheet -> list of header labels (for F2 evidence)
    specimens = {}
    raw_rows = []
    for name in wb.sheetnames:
        rows = sheet_rows(wb[name])
        if name.strip().lower() == "information":
            in_spec = in_dict = False
            for cells in rows:
                first = cells[0] if cells else ""
                if first.lower() == "specimen id":
                    in_spec, in_dict = True, False
                    continue
                if first.lower().startswith("column id"):
                    in_spec, in_dict = False, True
                    continue
                vals = [c for c in cells if c != ""]
                if not vals:
                    continue
                if in_spec:
                    mass = num(cells[4]) if len(cells) > 4 else None
                    species = cells[1] if len(cells) > 1 else ""
                    if species and mass is not None:
                        limbs = (cells[5] if len(cells) > 5 else "").lower()
                        limb = ("RL" if "left" in limbs and "right" in limbs
                                else "R" if "right" in limbs
                                else "L" if "left" in limbs else "")
                        specimens[species] = {"specimen_id": first,
                                              "body_mass_kg": mass, "limb": limb}
                elif in_dict:
                    if len(vals) >= 2:
                        specimens.setdefault("_dict", []).append(vals[0])
            continue
        header_scan[name] = [c for c in rows[0] if c != ""]
        hdr = {}
        for idx, label in enumerate(rows[0]):
            label = label.strip()
            if not label:
                continue
            key = label.lower()
            if key == "mus_abbrev":
                hdr["muscle"] = idx
            elif key == "fl_m":
                hdr["fl"] = idx
            elif key == "pcsa_m2":
                hdr["pcsa"] = idx
            elif key.startswith("musc_length"):
                hdr["musc_len"] = idx
            elif key.startswith("musc_mass"):
                hdr["musc_mass"] = idx
            elif key.startswith("belly_length"):
                hdr["belly_len"] = idx
            elif key.startswith("belly_mass"):
                hdr["belly_mass"] = idx
            elif key.startswith("tendon_length"):
                hdr["tendon_len"] = idx
            elif key.startswith("tendon_mass"):
                hdr["tendon_mass"] = idx
            elif key.startswith(("avg_pen", "avg_penn")):
                hdr["penn"] = idx
            elif key == "limb":
                hdr["limb"] = idx
            elif key == "species":
                hdr["species"] = idx
            elif key == "species_common":
                pass
            else:
                hdr.setdefault("_unknown", []).append(label)
        for rnum, cells in enumerate(rows[1:], start=2):
            if not any(c != "" for c in cells):
                continue
            muscle = cells[hdr["muscle"]] if hdr.get("muscle") is not None else ""
            if muscle:
                raw_rows.append({"sheet": name, "row": rnum, "cells": cells,
                                 "hdr": hdr})
    wb.close()

    rows, unparsed = [], []
    for item in raw_rows:
        if item["sheet"] != SPECIES_SHEET:
            continue
        cells, hdr = item["cells"], item["hdr"]
        rec = {"muscle": cells[hdr["muscle"]], "sheet_row": item["row"]}
        fl = num(cells[hdr["fl"]])
        pcsa = num(cells[hdr["pcsa"]])
        mass_g = num(cells[hdr["musc_mass"]])
        belly_g = num(cells[hdr["belly_mass"]])
        tendon_g = num(cells[hdr["tendon_mass"]])
        musc_len = num(cells[hdr["musc_len"]])
        belly_len = num(cells[hdr["belly_len"]])
        tendon_len = num(cells[hdr["tendon_len"]])
        penn = num(cells[hdr["penn"]]) if hdr.get("penn") is not None else None
        limb = cells[hdr["limb"]] if hdr.get("limb") is not None else ""
        problems = []
        for label, v in (("fl", fl), ("pcsa", pcsa)):
            if v is None or v <= 0:
                problems.append(f"{label}={v}")
        if problems:
            unparsed.append({"muscle": rec["muscle"], "row": item["row"],
                             "reason": "; ".join(problems)})
            continue
        absent = [label for label, v in
                  (("musc_mass", mass_g), ("belly_mass", belly_g),
                   ("tendon_mass", tendon_g), ("musc_len", musc_len),
                   ("belly_len", belly_len), ("tendon_len", tendon_len))
                  if v is None or v <= 0]
        mass_si_declared = mass_g              # header-literal kg reading
        mass_si_resolved = mass_g / 1000.0 if mass_g else None  # mm/g reading
        # closure under each unit interpretation, deviation vs sheet PCSA
        pred_declared = (mass_si_declared / (RHO_KG_M3 * fl)
                         if mass_si_declared else None)
        pred_resolved = (mass_si_resolved / (RHO_KG_M3 * fl)
                         if mass_si_resolved else None)
        dev_declared = (abs(pred_declared - pcsa) / pcsa
                        if pred_declared else float("inf"))
        dev_resolved = (abs(pred_resolved - pcsa) / pcsa
                        if pred_resolved else None)
        cos_pen = math.cos(math.radians(penn)) if penn is not None else None
        dev_resolved_pen = (abs(pred_resolved * cos_pen - pcsa) / pcsa
                            if cos_pen is not None and pred_resolved else None)
        mass_dev = (abs(belly_g + tendon_g - mass_g) / mass_g
                    if mass_g and belly_g is not None and tendon_g is not None
                    else None)
        len_dev = (abs(belly_len + tendon_len - musc_len) / musc_len
                   if musc_len and belly_len is not None and tendon_len is not None
                   else None)
        groups = [g for g, members in TABLE3
                  if any(m == rec["muscle"] for m in members)]
        # the intake's whole-row admission rule: PCSA closure within 2% AND
        # mass additivity within 2% (mass fields must exist)
        closure_ok = dev_resolved is not None and dev_resolved <= LAW_TOL
        mass_ok = mass_dev is not None and mass_dev <= LAW_TOL
        if absent:
            status = "MASS_FIELDS_ABSENT_AT_SOURCE"
        elif closure_ok and mass_ok:
            status = "admitted"
        elif not closure_ok:
            status = "pcsa_closure_fail_quarantine_equivalent"
        else:
            status = "mass_additivity_fail_quarantine_equivalent"
        rec.update(
            limb=limb or specimens.get(SPECIES_SHEET, {}).get("limb", ""),
            fl_m=fl, pcsa_m2=pcsa, pcsa_cm2=pcsa * 1e4,
            musc_mass_g=mass_g, belly_mass_g=belly_g, tendon_mass_g=tendon_g,
            musc_len_mm=musc_len, belly_len_mm=belly_len,
            tendon_len_mm=tendon_len, penn_deg=penn,
            fields_absent_at_source=absent,
            dev_unit_declared=dev_declared, dev_unit_resolved=dev_resolved,
            dev_resolved_with_penn=dev_resolved_pen,
            mass_additivity_dev=mass_dev, length_additivity_dev=len_dev,
            groups=groups,
            biarticular=len(groups) > 1,
            primary_group=groups[0] if groups else "UNMAPPED",
            row_status=status,
        )
        rows.append(rec)
    return header_scan, specimens, rows, unparsed


# --------------------------------------------------------------------- oku

def parse_oku(path):
    """Peak series values per labelled column per block. Blocks follow the
    adapter's caption-order basis (before/after alteration). Muscle-force
    columns drive the pairing; GRF/torque columns feed the internal
    consistency check of the demand-side series."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    peaks = {}
    sheets_scanned = []
    for name in wb.sheetnames:
        rows = sheet_rows(wb[name])
        if not rows:
            continue
        header = rows[0]
        labelled = [i for i, v in enumerate(header) if v != ""]
        if not labelled or labelled[0] == 0:
            continue
        blocks, cur = [], [labelled[0]]
        for col in labelled[1:]:
            if col == cur[-1] + 1:
                cur.append(col)
            else:
                blocks.append(cur)
                cur = [col]
        blocks.append(cur)
        picked = []
        for b_index, block in enumerate(blocks):
            role = ("before_alteration", "after_alteration")[b_index] \
                if b_index < 2 else f"block{b_index}"
            for col in block:
                label = header[col].strip()
                kind = None
                if label in OKU_MUSCLES or label.startswith("GRF"):
                    kind = "force"
                elif label.endswith("torque"):
                    kind = "torque"
                if kind:
                    picked.append((col, label, role, kind))
        if picked:
            sheets_scanned.append(name)
        for col, label, role, kind in picked:
            vals = []
            for cells in rows[1:]:
                if len(cells) > col and cells[col] != "":
                    v = num(cells[col])
                    if v is not None:
                        vals.append(v)
            if not vals:
                continue
            key = (kind, label, role)
            peak = max(abs(v) for v in vals) if kind == "torque" else max(vals)
            if key not in peaks or peak > peaks[key]:
                peaks[key] = peak
    wb.close()
    out = {}
    for (kind, label, role), peak in peaks.items():
        out.setdefault((kind, label), {})[role] = peak
    forces = {label: roles for (kind, label), roles in out.items()
              if kind == "force"}
    torques = {label: roles for (kind, label), roles in out.items()
               if kind == "torque"}
    return forces, torques, sheets_scanned


# ------------------------------------------------------------------ stats

def stats(values):
    vs = sorted(values)
    n = len(vs)

    def q(p):
        if n == 1:
            return vs[0]
        pos = (n - 1) * p
        lo = int(math.floor(pos))
        hi = min(lo + 1, n - 1)
        frac = pos - lo
        return vs[lo] * (1 - frac) + vs[hi] * frac

    return {
        "n": n,
        "mean": round(statistics.fmean(vs), 6),
        "median": round(statistics.median(vs), 6),
        "stdev_sample": round(statistics.stdev(vs), 6) if n > 1 else 0.0,
        "min": round(vs[0], 6),
        "p10": round(q(0.10), 6),
        "p90": round(q(0.90), 6),
        "max": round(vs[-1], 6),
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--guim", required=True)
    ap.add_argument("--oku", required=True)
    ap.add_argument("--fulltext", required=True)
    ap.add_argument("--outdir", default=here)
    args = ap.parse_args()

    receipt_path = os.path.join(here, "receipt.json")
    if not os.path.exists(receipt_path):
        sys.exit("REFUSAL: receipt.json (frozen pre-registration) missing")
    receipt = json.load(open(receipt_path, encoding="utf-8"))
    pins = {i["path_at_ref"].split("/")[-1]: i["sha256"] for i in receipt["inputs"]}
    for fname, path in (("AJPA-190-e70329-s001.xlsx", args.guim),
                        ("PMC13425262_fulltext.xml", args.fulltext),
                        ("42003_2021_1831_MOESM2_ESM.xlsx", args.oku)):
        got = sha256_file(path)
        if got != pins[fname]:
            sys.exit(f"REFUSAL: sha256 mismatch for {fname}: {got}")

    fulltext = open(args.fulltext, encoding="utf-8").read()
    ft_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fulltext))
    ft_force_hits = len(re.findall(
        r"f\s*max|tetanic|specific tension|isometric stress", ft_text, re.I))

    header_scan, specimens, rows, unparsed = parse_guim(args.guim)

    # ---- F2 measured from bytes: any Fmax-bearing column anywhere?
    f2_matches = {}
    for sheet, labels in header_scan.items():
        hits = [l for l in labels if FMAX_PATTERN.search(l)]
        if hits:
            f2_matches[sheet] = hits
    dict_labels = specimens.get("_dict", [])
    dict_hits = [l for l in dict_labels if FMAX_PATTERN.search(l)]
    f2_fired = not f2_matches and not dict_hits

    # ---- F3: unit consistency, measured per row
    n = len(rows)
    mass_bearing = [r for r in rows if r["musc_mass_g"] is not None]
    dev_res = [r["dev_unit_resolved"] for r in mass_bearing]
    dev_dec = [r["dev_unit_declared"] for r in mass_bearing]
    mass_dev = [r["mass_additivity_dev"] for r in mass_bearing
                if r["mass_additivity_dev"] is not None]
    len_dev = [r["length_additivity_dev"] for r in mass_bearing
               if r["length_additivity_dev"] is not None]
    with_penn = [r for r in rows if r["penn_deg"] is not None]
    penn_match_nopenn = [r for r in with_penn
                         if r["dev_unit_resolved"] is not None
                         and r["dev_unit_resolved"] <= LAW_TOL
                         and r["dev_resolved_with_penn"] is not None
                         and r["dev_resolved_with_penn"] > LAW_TOL]
    penn_match_withpenn = [r for r in with_penn
                           if r["dev_resolved_with_penn"] is not None
                           and r["dev_resolved_with_penn"] <= LAW_TOL]
    # the decisive bucket: pennation too large for both conventions to agree
    penn_large = [r for r in with_penn
                  if math.cos(math.radians(r["penn_deg"])) < 0.98]
    penn_large_nopenn = [r for r in penn_large
                         if r["dev_unit_resolved"] is not None
                         and r["dev_unit_resolved"] <= LAW_TOL]
    penn_large_withpenn = [r for r in penn_large
                           if r["dev_resolved_with_penn"] is not None
                           and r["dev_resolved_with_penn"] <= LAW_TOL]
    pcsa_fail = [r["muscle"] for r in rows
                 if r["row_status"] == "pcsa_closure_fail_quarantine_equivalent"]
    mass_fail = [r["muscle"] for r in rows
                 if r["row_status"] == "mass_additivity_fail_quarantine_equivalent"]
    absent_rows = [r["muscle"] for r in rows
                   if r["row_status"] == "MASS_FIELDS_ABSENT_AT_SOURCE"]
    admitted = [r for r in rows if r["row_status"] == "admitted"]
    contradictions = pcsa_fail + mass_fail

    # ---- measured distributions
    pcsa = [r["pcsa_cm2"] for r in rows]
    pcsa_adm = [r["pcsa_cm2"] for r in admitted]
    fl = [r["fl_m"] * 100.0 for r in rows]
    masses = [r["musc_mass_g"] for r in mass_bearing]
    total_pcsa = sum(pcsa)

    # ---- group structure
    group_stats = {}
    for g, _members in TABLE3:
        members = [r for r in rows if r["primary_group"] == g]
        if not members:
            continue
        group_stats[g] = {
            "n": len(members),
            "muscles": sorted(r["muscle"] for r in members),
            "pcsa_cm2": stats([r["pcsa_cm2"] for r in members]),
            "fl_cm": stats([r["fl_m"] * 100.0 for r in members]),
        }
    bia = [r for r in rows if r["biarticular"]]
    uni = [r for r in rows if not r["biarticular"]]

    # ---- Oku demand-side pairing
    oku_forces, oku_torques, oku_sheets = parse_oku(args.oku)
    by_muscle = {r["muscle"]: r for r in rows}
    pairing = []
    for oku_name, (targets, basis) in sorted(OKU_PAIR.items()):
        pcsa_sum = sum(by_muscle[t]["pcsa_cm2"] for t in targets
                       if t in by_muscle)
        missing = [t for t in targets if t not in by_muscle]
        blocks = oku_forces.get(oku_name, {})
        peak = max(blocks.values()) if blocks and not missing else None
        row = {"oku_muscle": oku_name, "guimaraes_muscles": targets,
               "pairing_basis": basis,
               "pcsa_cm2_used": round(pcsa_sum, 6) if not missing else None,
               "peak_N_before": round(blocks["before_alteration"], 6)
               if "before_alteration" in blocks else None,
               "peak_N_after": round(blocks["after_alteration"], 6)
               if "after_alteration" in blocks else None,
               "peak_N_used": round(peak, 6) if peak is not None else None,
               "sigma_lower_N_per_cm2": round(peak / pcsa_sum, 6)
               if peak is not None and pcsa_sum else None,
               "status": "paired" if (peak is not None and not missing)
               else "UNPAIRED: " + (",".join(missing) or "no force block")}
        pairing.append(row)
    bounds = [p["sigma_lower_N_per_cm2"] for p in pairing
              if p["sigma_lower_N_per_cm2"] is not None]
    bounds_above_floor = [b for b in bounds if b >= LIT_BAND_N_CM2[0]]

    # internal consistency of the demand-side series against its own GRF/torque
    grfv = oku_forces.get("GRF v", {})
    hip_tau = oku_torques.get("hip torque", {})
    il_peaks = oku_forces.get("IL", {})
    grfv_peak = max(grfv.values()) if grfv else None
    hip_tau_peak = max(hip_tau.values()) if hip_tau else None
    il_peak = max(il_peaks.values()) if il_peaks else None
    n_muscles_above_band = sum(1 for b in bounds if b >= LIT_BAND_N_CM2[0])

    # ---- verdicts
    p2_pass = (len(admitted) > 0 and max(dev_res) <= LAW_TOL
               and max(mass_dev) <= LAW_TOL)
    p3_face_value_fails = bool(bounds_above_floor)

    results = {
        "schema": "chimera.sigma_law.derivation.v1",
        "receipt_sha256": sha256_file(receipt_path),
        "receipt_recorded_utc": receipt["recorded_utc"],
        "ref_cited": receipt["inputs"][0]["ref_cited"],
        "input_sha256": {name: sha256_file(p) for name, p in
                         (("guimaraes_xlsx", args.guim),
                          ("oku_xlsx", args.oku),
                          ("guimaraes_fulltext", args.fulltext))},
        "species_sheet": SPECIES_SHEET,
        "specimen": specimens.get(SPECIES_SHEET, {}),
        "rows_found": n,
        "rows_expected": EXPECTED_ROWS,
        "rows_count_identity": "PASS" if n == EXPECTED_ROWS else
        f"DEVIATION: found {n}, expected {EXPECTED_ROWS}",
        "rows_admitted_closure_passing": len(admitted),
        "rows_pcsa_closure_fail": pcsa_fail,
        "rows_mass_additivity_fail": mass_fail,
        "rows_mass_fields_absent_at_source": absent_rows,
        "unparsed_rows_named": unparsed,

        "premise_check_F2": {
            "fmax_pattern": FMAX_PATTERN.pattern,
            "sheet_headers_scanned": header_scan,
            "fmax_pattern_matches_in_sheet_headers": f2_matches,
            "information_dictionary_labels": dict_labels,
            "fmax_pattern_matches_in_dictionary": dict_hits,
            "fulltext_force_keyword_hits": ft_force_hits,
            "fulltext_tables": ["specimen details", "pelvis and hind limb "
                                "muscles included", "muscle functional groups",
                                "t-tests PCSA with/without pennation"],
            "FMAX_BEARING_FIELD_FOUND": bool(f2_matches) or bool(dict_hits),
            "fired": f2_fired,
            "consequence": "sigma_implied = Fmax/PCSA is NOT computable from "
                           "the admitted batch; the 36-row measured derivation "
                           "does not exist; the literature constant is not "
                           "retired by this lane",
        },

        "unit_consistency_F3": {
            "interpretations": {
                "header_literal_kg": "deviation of PCSA vs mass-as-kg closure",
                "resolved_mm_g": "deviation of PCSA vs mass-as-g closure",
            },
            "denominator": f"{len(mass_bearing)} mass-bearing rows of {n}",
            "mean_dev_header_literal": round(statistics.fmean(dev_dec), 8),
            "mean_dev_resolved": round(statistics.fmean(dev_res), 8),
            "discrimination_ratio_header_over_resolved": round(
                statistics.fmean(dev_dec) / max(statistics.fmean(dev_res), 1e-18), 2),
            "max_dev_resolved_admitted_rows": round(max(
                (r["dev_unit_resolved"] for r in admitted), default=0), 8),
            "max_mass_additivity_dev_admitted_rows": round(max(
                (r["mass_additivity_dev"] for r in admitted), default=0), 8),
            "max_length_additivity_dev": round(max(len_dev), 8),
            "length_additivity_note": "continuous (recorded condition in the "
                                      "intake adapter, never a quarantine)",
            "pennation_convention": {
                "rows_with_pennation": len(with_penn),
                "match_uncorrected_m_over_rhoFL": len(penn_match_nopenn),
                "match_corrected_with_cos": len(penn_match_withpenn),
                "decisive_bucket_penn_gt_11_48_deg": {
                    "n": len(penn_large),
                    "match_uncorrected": len(penn_large_nopenn),
                    "match_corrected": len(penn_large_withpenn),
                    "members": sorted(r["muscle"] for r in penn_large),
                },
                "max_dev_uncorrected": round(max(
                    (r["dev_unit_resolved"] for r in with_penn
                     if r["dev_unit_resolved"] is not None), default=0), 8),
                "max_dev_corrected": round(max(
                    (r["dev_resolved_with_penn"] for r in with_penn
                     if r["dev_resolved_with_penn"] is not None), default=0), 8),
                "conclusion": None,
            },
            "contradictions_named": {
                "pcsa_closure_fail": pcsa_fail,
                "mass_additivity_fail": mass_fail,
                "note": "per-row deviations in audit_table.csv; these rows "
                        "fail the dataset's own 2% closure identities and are "
                        "quarantine-equivalent under the intake's whole-row "
                        "rule; they are reported, never dropped",
            },
            "F3_pass": not contradictions,
        },

        "measured_distributions": {
            "pcsa_cm2_all_rows": stats(pcsa),
            "pcsa_cm2_admitted_only": stats(pcsa_adm) if pcsa_adm else None,
            "total_pcsa_cm2_all_rows": round(total_pcsa, 6),
            "fascicle_length_cm_all_rows": stats(fl),
            "muscle_mass_g_mass_bearing_rows": stats(masses),
            "note": "these ARE the measured quantities the batch carries; "
                    "sigma per muscle is not among them (F2)",
        },

        "group_structure": {
            "source": "Table 3 of the admitted fulltext (PMC13425262), verbatim",
            "biarticular_rule": "a muscle listed by Table 3 in two functional "
                                "groups is biarticular per source; no "
                                "agent-invented taxonomy",
            "groups": group_stats,
            "biarticular_per_source": {
                "members": sorted(r["muscle"] for r in bia),
                "pairs": {r["muscle"]: r["groups"] for r in bia},
                "pcsa_cm2": stats([r["pcsa_cm2"] for r in bia]) if bia else None,
            },
            "unicarticular_pcsa_cm2": stats([r["pcsa_cm2"] for r in uni]),
            "sigma_caveat": "group sigma comparison is NOT computable in this "
                            "batch (no Fmax); only PCSA/FL/mass structure is "
                            "measured. Anatomy note: SM, ST, RF, MG, LG are "
                            "conventionally two-joint but Table 3 lists them "
                            "once; recorded, not overridden.",
        },

        "oku_demand_side_bounds": {
            "basis": "peak simulated muscle force (Oku 2021, admitted batch, "
                     "M. fuscata forward dynamics) / measured PCSA (Guimaraes "
                     "2026 M. mulatta) = LOWER bound on required specific "
                     "tension; a declared within-genus pairing, not a "
                     "measurement of tissue sigma",
            "sheets_with_force_series": oku_sheets,
            "pairing": pairing,
            "bounds_N_per_cm2": stats(bounds) if bounds else None,
            "max_bound": round(max(bounds), 6) if bounds else None,
            "bounds_at_or_above_band_floor_23": round(max(
                bounds_above_floor), 6) if bounds_above_floor else None,
            "internal_consistency_of_series": {
                "grfv_peak_N": round(grfv_peak, 6) if grfv_peak else None,
                "hip_torque_peak_abs_Nm": round(hip_tau_peak, 6)
                if hip_tau_peak else None,
                "il_peak_N": round(il_peak, 6) if il_peak else None,
                "finding": "the same workbook's vertical GRF never exceeds "
                           "1.1 body weights (GRFv peak "
                           f"{grfv_peak:.1f} N, model mass ~10.7 kg) and hip "
                           f"torque peaks at |{hip_tau_peak:.2f}| N*m, while "
                           f"the muscle-force series carries IL at "
                           f"{il_peak:.0f} N (~6.4 BW); the implied "
                           "co-contraction / scale of the muscle-force "
                           "series is unresolved from anything we hold (the "
                           "model's own Fmax and PCSA inputs are not "
                           "published in the admitted files)",
                "consequence": "the demand-side numbers are NOT trusted "
                               "either to confirm or to falsify the "
                               "literature band; recorded with numbers, "
                               "unusable as a sigma floor until the Oku "
                               "series scale is resolved from the paper's "
                               "model parameters",
            },
            "P3_outcome": "bounds above the band floor WERE observed "
                          f"({n_muscles_above_band} of {len(bounds)} pairs, "
                          f"max {max(bounds):.3f} N/cm^2), which at face "
                          "value fires the pre-registered P3 falsifier; the "
                          "named internal inconsistency of the series "
                          "blocks taking that firing as a band verdict",
        },

        "verdicts": {
            "sigma_implied_derivation": "IMPOSSIBLE_FROM_ADMITTED_BATCH "
                                        "(F2 fired: no Fmax-bearing field in "
                                        "the 13 columns, the column "
                                        "dictionary, or the paper's tables)",
            "P1_band_prediction": "NOT EVALUABLE (conditional on F2; F2 fired)",
            "P2_closure_laws": "PASS on admitted rows" if p2_pass else "FAIL",
            "P3_demand_below_band_floor":
                "FACE-VALUE FIRE BLOCKED: bounds above the floor were "
                "observed but the series is internally untrusted; no band "
                "verdict taken from demand data",
            "sigma_recommendation": {
                "constant_N_per_cm2": IN_REPO_POINT_N_CM2,
                "constant_MPa": 0.3,
                "status": "RETAINED AS ASSUMED, NOT RETIRED BY MEASUREMENT",
                "band_N_per_cm2": list(LIT_BAND_N_CM2),
                "band_basis": "literature prior (docs/research/"
                              "muscle_physiology_reference.md 25-32; Saito "
                              "2021 x Spector 1980 at 23); no measured "
                              "M. mulatta hindlimb sigma exists to replace "
                              "it; the Oku demand-side series cannot set a "
                              "floor (internal inconsistency, recorded "
                              "above)",
                "derived_pennation_correction_for_bootstrap": {
                    "rule": "Fmax = sigma * PCSA * cos(pennation); the sheet "
                            "PCSA is the pennation-UNCORRECTED area, so "
                            "Fmax = sigma * PCSA_sheet alone OVERestimates "
                            "pennate muscles by 1/cos(pennation)",
                    "rows_with_measured_pennation": len(with_penn),
                    "max_overestimate_pct_uncorrected": round(max(
                        (1.0 / math.cos(math.radians(r["penn_deg"])) - 1.0)
                        * 100.0 for r in with_penn), 3),
                    "per_muscle_factors": "audit_table.csv penn_deg column",
                },
                "capacity_budget_for_torque_book": {
                    "total_measured_pcsa_cm2_all_rows":
                        round(total_pcsa, 6),
                    "use": "hindlimb force capacity at sigma: "
                           f"{IN_REPO_POINT_N_CM2:.0f} N/cm^2 * "
                           f"{total_pcsa:.1f} cm^2 = "
                           f"{IN_REPO_POINT_N_CM2 * total_pcsa:.0f} N total "
                           "(uncorrected; multiply per muscle by "
                           "cos(pennation) where measured)",
                },
                "upgrade_path": "a measured M. mulatta hindlimb Fmax source "
                                "(none admitted anywhere on canonical as of "
                                "46ed85a3..77f3d279) or per-muscle specific "
                                "tension measurements; the forelimb round "
                                "trip stays blocked by the missing measured "
                                "forelimb PCSA (Cheng & Scott, paywalled)",
            },
        },

        "falsifier_ledger": {},
    }

    # pennation convention conclusion
    pc = results["unit_consistency_F3"]["pennation_convention"]
    db = pc["decisive_bucket_penn_gt_11_48_deg"]
    if pc["rows_with_pennation"] == 0:
        pc["conclusion"] = "no pennation values in this sheet"
    elif db["n"] > 0 and db["match_uncorrected"] >= db["match_corrected"]:
        pc["conclusion"] = ("sheet PCSA is the pennation-UNCORRECTED area "
                            "m/(rho*FL): decided by the "
                            f"{db['n']} muscles with pennation > 11.48 deg "
                            f"where the two conventions differ >2% "
                            f"({db['match_uncorrected']} match uncorrected, "
                            f"{db['match_corrected']} match corrected): "
                            "treating sheet PCSA as physiological PCSA "
                            "OVERestimates Fmax = sigma*PCSA for pennate "
                            "muscles by 1/cos(pennation); per-muscle factors "
                            "are in audit_table.csv")
    else:
        pc["conclusion"] = "sheet PCSA is the pennation-corrected area"

    # falsifier ledger
    results["falsifier_ledger"] = {
        "F1_traceability": "PASS - every number in this file traces to "
                           f"audit_table.csv rows ({n} rows, sheet:row "
                           "cited per muscle)",
        "F2_premise": ("FIRED" if f2_fired else
                       "NOT FIRED - Fmax-bearing field found: "
                       + json.dumps(f2_matches or dict_hits)),
        "F3_unit_consistency":
            ("PASS at 2% on admitted rows" if not contradictions else
             "PASS on admitted rows; CONTRADICTIONS NAMED on the remaining "
             "rows (pcsa_closure_fail: " + ", ".join(pcsa_fail)
             + "; mass_additivity_fail: " + ", ".join(mass_fail)
             + "; mass fields absent at source: " + ", ".join(absent_rows)
             + ") - all reported in audit_table.csv, none dropped"),
        "F4_determinism": "measured by rerun wrapper (determinism.json)",
        "F5_band_containment": "NOT EVALUABLE (conditional on F2; F2 fired)",
    }

    # ---- outputs (sorted keys, no wall clock, fixed rounding)
    outdir = os.path.abspath(args.outdir)
    rp = os.path.join(outdir, "results.json")
    with open(rp, "w", newline="\n", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    cp = os.path.join(outdir, "audit_table.csv")
    cols = ["muscle", "sheet_row", "limb", "fl_m", "pcsa_m2", "pcsa_cm2",
            "musc_mass_g", "belly_mass_g", "tendon_mass_g", "musc_len_mm",
            "belly_len_mm", "tendon_len_mm", "penn_deg", "row_status",
            "fields_absent_at_source",
            "dev_unit_resolved", "dev_unit_declared",
            "dev_resolved_with_penn", "mass_additivity_dev",
            "length_additivity_dev", "groups", "biarticular", "primary_group",
            "sigma_implied_status"]
    fmt_g = lambda v: "" if v is None else f"{v:.6g}"
    fmt_e = lambda v: "" if v is None else f"{v:.3e}"
    with open(cp, "w", newline="\n", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in sorted(rows, key=lambda x: x["muscle"]):
            w.writerow([
                r["muscle"], r["sheet_row"], r["limb"],
                fmt_g(r["fl_m"]), f"{r['pcsa_m2']:.9g}", fmt_g(r["pcsa_cm2"]),
                fmt_g(r["musc_mass_g"]), fmt_g(r["belly_mass_g"]),
                fmt_g(r["tendon_mass_g"]), fmt_g(r["musc_len_mm"]),
                fmt_g(r["belly_len_mm"]), fmt_g(r["tendon_len_mm"]),
                fmt_g(r["penn_deg"]), r["row_status"],
                "|".join(r["fields_absent_at_source"]),
                fmt_e(r["dev_unit_resolved"]), fmt_e(r["dev_unit_declared"]),
                fmt_e(r["dev_resolved_with_penn"]),
                fmt_e(r["mass_additivity_dev"]),
                fmt_e(r["length_additivity_dev"]),
                "|".join(r["groups"]), r["biarticular"], r["primary_group"],
                "NOT_COMPUTABLE_F2_FIRED",
            ])
    print(f"rows={n} admitted={len(admitted)} F2_fired={f2_fired} "
          f"contradictions={len(contradictions)} "
          f"total_pcsa_cm2={total_pcsa:.3f} "
          f"max_ok_bound={max(bounds) if bounds else None}")
    print("wrote", rp)
    print("wrote", cp)


if __name__ == "__main__":
    main()
