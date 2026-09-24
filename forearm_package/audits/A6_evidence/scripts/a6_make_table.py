#!/usr/bin/env python3
"""A6: generate table.md + table.csv (32-row evidence table) from the
verification receipt + the baseline packets. Cells are per-row specific."""
import json, re
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path("E:/PythonChimera/forearm_package/baseline_snapshot")
AUD = Path("E:/PythonChimera/forearm_package/audits/A6_evidence")
rec = json.load(open(AUD / "receipts/a6_verify_receipt.json"))
cand = json.loads((BASE / "runs/attachment_candidates.json").read_text())

raw = (BASE / "source_xml/chimanoid.xml").read_text()
lines = raw.splitlines()

# line of <spatial name="X"> and of each <site site="N"> within tendons
tendon_line = {}
siteref_line = {}
cur = None
for i, ln in enumerate(lines, 1):
    m = re.search(r'<spatial name="([^"]+)"', ln)
    if m:
        cur = m.group(1); tendon_line[cur] = i
    m = re.search(r'<site site="([^"]+)"', ln)
    if m and cur:
        siteref_line[m.group(1)] = i

site_line = {}
for i, ln in enumerate(lines, 1):
    m = re.search(r'<site name="([^"]+)" pos="([^"]*)"', ln)
    if m:
        site_line[m.group(1)] = (i, m.group(2))

by_site = {c["site_id"]: c for bk in ("radius", "radius_l") for c in cand["bodies"][bk]["candidates"]}
rowrec = {r["site"]: r for r in rec["rows"]}

SPECIAL_OUTSIDE = set()
for bk in ("radius", "radius_l"):
    for c in cand["bodies"][bk]["candidates"]:
        if c["skin_containment"]["loop"]["verdict"] in ("outside", "inside_insufficient_clearance", "unresolved"):
            SPECIAL_OUTSIDE.add(c["site_id"])

def fmt3(v):
    return "(" + ", ".join(f"{x:g}" for x in v) + ")"

csv_rows = [["site","xml_line","xml_pos_verbatim","owning_body","body_xml_line",
             "tendon","index_in_path","path_length","role","spatial_xml_line","siteref_xml_line",
             "source_evidence","fit_added","containment","proven","assumed"]]
md_rows = []

for bk, bodyline in (("radius", 608), ("radius_l", 748)):
    for c in cand["bodies"][bk]["candidates"]:
        nm = c["site_id"]
        r = rowrec[nm]
        mem = c["tendon_membership"][0]
        tn, idx, pl, role = mem["tendon"], mem["index_in_path"], mem["path_length"], mem["role"]
        pos = r["xml_pos"]
        owner = r["owner"]
        tline = tendon_line[tn]; sline = siteref_line[nm]
        pos_kind = ("path TERMINUS of the authored polyline (last entry)" if role == "last_endpoint"
                    else "path ORIGIN of the authored polyline (first entry)" if role == "first_endpoint"
                    else f"interior waypoint (entry {idx+1} of {pl})")
        src_ev = (f"XML line {r['xml_line']}: `<site name=\"{nm}\" pos=\"{pos}\">` exists inside `<body name=\"{owner}\">` "
                  f"(line {bodyline}); listed entry {idx} (0-based) of {pl} in `<spatial name=\"{tn}\">` (line {tline}; site ref line {sline}) "
                  f"— i.e. {pos_kind}. This is AUTHOR MODELING (path authorship), not measured anatomy.")
        fit_added = (f"fitted_pos_global {fmt3(c['fitted']['fitted_pos_global'])} m = t {fmt3(cand['bodies'][bk]['local_to_world']['t_fitted_origin_m'])} "
                     f"+ R@x, R from correspondence landmarks (authored/taste per DERIVATION §1; correspondence sha 52c92fe0…) "
                     f"+ uniform scale 0.22170680 (axial: evidence=axial_pair_length; transverse b,c: assumption, DERIVATION §4-5) "
                     f"+ authored roll_ref (roll_residual −90.0°); recon err {r['recon_err_m']:.2e} m.")
        loop = c["skin_containment"]["loop"]; hull = c["skin_containment"]["hull_sampling_diagnostic"]
        ld = f"{loop['dist_to_loop_m']:+.6f}" if loop["dist_to_loop_m"] is not None else "null"
        hd = f"{hull['dist_to_hull_m']:+.6f}" if hull["dist_to_hull_m"] is not None else "null"
        containment = (f"loop(authority)={loop['verdict']} d={ld} m n_loops={loop['n_loops']}; "
                       f"hull diagnostic={hull['verdict']} d={hd} m — GEOMETRIC ONLY: position of the FITTED point vs fitted target skin envelope; "
                       f"not attachment evidence in either direction.")
        proven = (f"existence + authored coordinates at XML line {r['xml_line']}; authored membership+order in {tn} ({pos_kind}); "
                  f"packet source_pos_local float-identical to XML (C1); role⇔index law (C3); "
                  f"fitted point = declared transform applied (C4, err {r['recon_err_m']:.2e} m); "
                  f"the FITTED point's signed position vs the fitted skin loop ({loop['verdict']}, d={ld} m).")
        assumed = ("that the authored site marks a real anatomical attachment (never measured here); anatomical meaning of path order beyond polyline authorship; "
                   "correspondence landmark placement (taste axis); transverse scale = axial (uniform assumption); "
                   "mass carriage |det S| (requires_density_validation); lengthrange rebaseline (homogeneous_path_scaling); "
                   "force/timeconst not carried (requires_physiological_rerun); any inference from containment to attachment.")
        if nm in SPECIAL_OUTSIDE:
            v = loop["verdict"]
            if v == "outside":
                containment += (" OUTSIDE-NESS IS A GEOMETRIC DIVERGENCE between source-authored coordinates as placed by the fit and the target envelope — "
                                "NOT evidence the anatomy is wrong, NOT evidence it is right.")
            elif v == "inside_insufficient_clearance":
                containment += (" TIGHT = inside but clearance below the 1 mm margin — a geometric margin statement only.")
            else:
                containment += (" AMBIGUOUS = section identification at wrist-level axial positions yielded multiple ownership-identified loops; "
                                "no bridging, no repair, no proximity choice — the packet refuses to resolve it by choice.")
        csv_rows.append([nm, r['xml_line'], f'"{pos}"', owner, bodyline, tn, idx, pl, role, tline, sline,
                         f'"{src_ev}"', f'"{fit_added}"', f'"{containment}"', f'"{proven}"', f'"{assumed}"'])
        md_rows.append((nm, r, pos, owner, bodyline, tn, idx, pl, role, tline, sline,
                        src_ev, fit_added, containment, proven, assumed))

# CSV
import csv
with open(AUD / "table.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(csv_rows)

# MD
out = []
out.append("# A6 — 32-Row Site Evidence Table (source evidence vs fit-added vs containment)\n")
out.append("Generated by `scripts/a6_make_table.py` from `baseline_snapshot/` only. Checks C1-C5 all PASS "
           "(receipts/a6_verify_receipt.json). Columns follow the brief. Every row resolves the SAME way, as preregistered:\n")
out.append("- **SOURCE EVIDENCE** = XML-authored existence, coordinates, tendon membership + order position (terminus vs interior). AUTHOR MODELING, not measured anatomy.\n")
out.append("- **FIT-ADDED** = correspondence landmarks (the declared taste axis, DERIVATION §1), scale policy, R,t placement.\n")
out.append("- **CONTAINMENT** = loop/hull verdicts: where the FITTED point sits relative to the FITTED target skin envelope. Geometric only.\n")
out.append("- Fit constants shared by all 32 rows: radius R,t and radius_l R,t from the packet's `local_to_world`; scale s = 0.22170679566544982 (all axes, both sides); "
           "roll_residual −90.0°; correspondence sha256 52c92fe0d207a59971d9765d10009fc4f1d94e0f0e38e2eea59a1d64be4a7df8.\n")
out.append("- Legend: C1 = XML pos == packet source_pos_local; C3 = role⇔index law; C4 = fitted_pos_global == t + R@x (max err 9.14e-10 m over 32 rows).\n")

cur_side = None
for (nm, r, pos, owner, bodyline, tn, idx, pl, role, tline, sline,
     src_ev, fit_added, containment, proven, assumed) in md_rows:
    side = "RIGHT (radius)" if owner == "radius" else "LEFT (radius_l)"
    if side != cur_side:
        out.append(f"\n## {side}\n")
        cur_side = side
    out.append(f"### {nm}\n")
    out.append(f"| field | value |")
    out.append(f"|---|---|")
    out.append(f"| XML pos verbatim | line {r['xml_line']}: `pos=\"{pos}\"` |")
    out.append(f"| owning body | `{owner}` (body element line {bodyline}) |")
    out.append(f"| tendon + path index | `{tn}` entry {idx} of {pl} (0-based; spatial line {tline}, site ref line {sline}) |")
    out.append(f"| role | `{role}` |")
    out.append(f"| SOURCE EVIDENCE | {src_ev} |")
    out.append(f"| FIT-ADDED | {fit_added} |")
    out.append(f"| CONTAINMENT | {containment} |")
    out.append(f"| PROVEN | {proven} |")
    out.append(f"| ASSUMED | {assumed} |")
    out.append("")
(AUD / "table.md").write_text("\n".join(out), encoding="utf-8")
print("wrote", AUD / "table.md", "and table.csv;", len(md_rows), "rows")
