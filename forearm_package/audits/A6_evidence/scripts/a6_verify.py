#!/usr/bin/env python3
"""A6 evidence audit — independent re-derivation from the source XML and
cross-check of the attachment-candidates packet. Writes receipts JSON.

Checks:
  C1  XML pos verbatim == packet source_pos_local (float equality), all 32 sites
  C2  XML tendon path membership/index/role == packet tendon_membership, all 32
  C3  role consistency: first_endpoint <=> index 0, last_endpoint <=> index K-1
  C4  fitted_pos_global == t + R @ source_pos_local (packet's own R, t)
  C5  loop containment tally == admission lists (per side) == brief baseline 6/1/7/2
  C6  left/right source-pos mirror delta (source authorship fact, not fit)
  C7  body ownership of ALL sites on the 9 forearm tendons per side + fit
      resolution flag per site (adjacent-body impact on chain completeness)
"""
import json, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

BASE = Path("E:/PythonChimera/forearm_package/baseline_snapshot")
OUT = Path("E:/PythonChimera/forearm_package/audits/A6_evidence/receipts/a6_verify_receipt.json")

xml_path = BASE / "source_xml/chimanoid.xml"
cand_path = BASE / "runs/attachment_candidates.json"
fit_path = BASE / "runs/actual_monkey_fit.json"
adm_path = BASE / "runs/admission_actual_monkey.json"

raw = xml_path.read_bytes().decode("utf-8")
lines = raw.splitlines()
tree = ET.parse(xml_path)
root = tree.getroot()

# ---- body nesting: map each site element to nearest ancestor <body name=...>
def walk(elem, owner, out, line_of):
    for child in elem:
        tag = child.tag
        if tag == "body":
            walk(child, child.get("name"), out, line_of)
        elif tag == "site":
            nm = child.get("name")
            out[nm] = dict(owner=owner, pos_attr=child.get("pos"),
                           body_line=line_of.get("body:" + str(owner)))
        elif tag == "joint" and owner is not None:
            pass

# line numbers for body/site elements (1-based), by scanning raw lines
body_line = {}
site_line = {}
tendon_site_lines = {}
for i, ln in enumerate(lines, 1):
    m = re.search(r'<body name="([^"]+)"', ln)
    if m:
        body_line[m.group(1)] = i
    m = re.search(r'<site name="([^"]+)" pos="([^"]*)"', ln)
    if m:
        site_line[m.group(1)] = (i, m.group(2))
    m = re.search(r'<spatial name="([^"]+)"', ln)
    if m:
        cur_tendon = m.group(1)

# site ownership via ElementTree nesting
sites_owned = {}
def recurse(elem, owner):
    for ch in elem:
        if ch.tag == "body":
            recurse(ch, ch.get("name"))
        elif ch.tag == "site":
            sites_owned[ch.get("name")] = owner
        else:
            recurse(ch, owner)
recurse(root, None)

# tendon chains in document order
tendon_order = []   # (name, [site refs])
for sp in root.iter("spatial"):
    refs = [s.get("site") for s in sp.findall("site")]
    tendon_order.append((sp.get("name"), refs))

# the 32 target sites
RIGHT = ["BIClong-P11","BIClong-P9","BICshort-P6","BICshort-P8","BRD-P2","BRD-P3",
         "ECRB-P2","ECRB-P3","ECRL-P2","ECRL-P3","ECU-P5","FCR-P2","FCU-P2","FCU-P3",
         "PT-P3","PT-P5"]
LEFT = [s[:-1] + "_l" + s[-2:] if False else s.replace("-", "_l-", 1) if False else None for s in []]
LEFT = ["BIClong_l-P11","BIClong_l-P9","BICshort_l-P6","BICshort_l-P8","BRD_l-P2","BRD_l-P3",
        "ECRB_l-P2","ECRB_l-P3","ECRL_l-P2","ECRL_l-P3","ECU_l-P5","FCR_l-P2","FCU_l-P2","FCU_l-P3",
        "PT_l-P3","PT_l-P5"]
ALL32 = RIGHT + LEFT

# XML-derived membership for each of the 32
xml_member = {}
for nm in ALL32:
    mem = []
    for tname, refs in tendon_order:
        if nm in refs:
            idx = refs.index(nm)
            role = "first_endpoint" if idx == 0 else ("last_endpoint" if idx == len(refs)-1 else "waypoint")
            mem.append(dict(tendon=tname, index_in_path=idx, path_length=len(refs), role=role))
    xml_member[nm] = mem

cand = json.loads(cand_path.read_text())
fit = json.loads(fit_path.read_text())
adm = json.loads(adm_path.read_text())

receipt = dict(checks={}, rows=[], errors=[])

# C1 + C2 + C3 + C4
max_recon = 0.0
mismatch = []
rows = []
for body_key, body_name in (("radius", "radius"), ("radius_l", "radius_l")):
    B = cand["bodies"][body_key]
    R = np.array(B["local_to_world"]["R_source_local_to_target"], dtype=float)
    t = np.array(B["local_to_world"]["t_fitted_origin_m"], dtype=float)
    for c in B["candidates"]:
        nm = c["site_id"]
        xml_ln, xml_pos_str = site_line[nm]
        xml_pos = [float(v) for v in xml_pos_str.split()]
        pkt_pos = c["source_pos_local"]
        c1 = (xml_pos == pkt_pos)
        c2 = (xml_member[nm] == c["tendon_membership"])
        c3 = all(
            (m["role"] == "first_endpoint" and m["index_in_path"] == 0) or
            (m["role"] == "last_endpoint" and m["index_in_path"] == m["path_length"] - 1) or
            (m["role"] == "waypoint" and 0 < m["index_in_path"] < m["path_length"] - 1)
            for m in xml_member[nm])
        g = np.array(c["fitted"]["fitted_pos_global"], dtype=float)
        recon = t + R @ np.array(pkt_pos, dtype=float)
        err = float(np.max(np.abs(g - recon)))
        max_recon = max(max_recon, err)
        c4 = err < 1e-6
        lv = c["skin_containment"]["loop"]["verdict"]
        ld = c["skin_containment"]["loop"]["dist_to_loop_m"]
        hv = c["skin_containment"]["hull_sampling_diagnostic"]["verdict"]
        hd = c["skin_containment"]["hull_sampling_diagnostic"]["dist_to_hull_m"]
        owner = sites_owned[nm]
        ok = c1 and c2 and c3 and c4
        if not ok:
            mismatch.append(dict(site=nm, c1=c1, c2=c2, c3=c3, c4=c4, err=err))
        rows.append(dict(site=nm, xml_line=xml_ln, xml_pos=xml_pos_str, owner=owner,
                         body_line=body_line.get(owner), c1=c1, c2=c2, c3=c3,
                         recon_err_m=err, loop=lv, loop_dist_m=ld, hull=hv, hull_dist_m=hd,
                         membership=c["tendon_membership"]))
receipt["rows"] = rows
receipt["checks"]["C1_xml_pos_equal_packet"] = all(r["c1"] for r in rows)
receipt["checks"]["C2_membership_equal_packet"] = all(r["c2"] for r in rows)
receipt["checks"]["C3_role_index_consistent"] = all(r["c3"] for r in rows)
receipt["checks"]["C4_transform_reconstruction_max_err_m"] = max_recon
receipt["checks"]["C4_pass_1e-6"] = max_recon < 1e-6
receipt["mismatches"] = mismatch

# C5 containment tally vs admission
for body_key in ("radius", "radius_l"):
    tally = dict(inside=0, inside_insufficient_clearance=0, outside=0, unresolved=0)
    names = dict(inside=[], inside_insufficient_clearance=[], outside=[], unresolved=[])
    for c in cand["bodies"][body_key]["candidates"]:
        v = c["skin_containment"]["loop"]["verdict"]
        tally[v] += 1
        names[v].append(c["site_id"])
    adm_e = adm["envelope"][body_key]
    adm_sets = dict(
        inside=sorted(set(adm_e["loop_outside"]) ^ set(), ),  # placeholder, real below
    )
    loop_outside = set(adm_e["loop_outside"]); loop_tight = set(adm_e["loop_tight"])
    loop_amb = set(adm_e["loop_ambiguous"])
    all_names = {c["site_id"]: c["skin_containment"]["loop"]["verdict"]
                 for c in cand["bodies"][body_key]["candidates"]}
    derived_outside = {n for n, v in all_names.items() if v == "outside"}
    derived_tight = {n for n, v in all_names.items() if v == "inside_insufficient_clearance"}
    derived_amb = {n for n, v in all_names.items() if v == "unresolved"}
    derived_inside = {n for n, v in all_names.items() if v == "inside"}
    receipt["checks"][f"C5_{body_key}"] = dict(
        tally=tally,
        outside=sorted(derived_outside), tight=sorted(derived_tight),
        ambiguous=sorted(derived_amb), inside=sorted(derived_inside),
        matches_admission=(derived_outside == loop_outside and derived_tight == loop_tight
                           and derived_amb == loop_amb),
        brief_baseline_6_1_7_2=(len(derived_inside) == 6 and len(derived_tight) == 1
                                and len(derived_outside) == 7 and len(derived_amb) == 2))

# C6 mirror delta in SOURCE coordinates (authorship fact)
mirror = []
for r, l in zip(RIGHT, LEFT):
    pr = np.array([float(v) for v in site_line[r][1].split()])
    pl = np.array([float(v) for v in site_line[l][1].split()])
    mirrored = np.array([pr[0], pr[1], -pr[2]])
    mirror.append(dict(pair=[r, l], exact_mirror=bool(np.allclose(mirrored, pl, atol=0, rtol=0)),
                       delta_m=float(np.max(np.abs(mirrored - pl)))))
receipt["checks"]["C6_source_mirror"] = mirror
receipt["checks"]["C6_all_exact_mirrors"] = all(m["exact_mirror"] for m in mirror)

# C7 ownership + fit resolution of ALL sites on the 9 tendons x2 sides
tend_names = ["BIClong", "BICshort", "BRD", "ECRB", "ECRL", "ECU", "FCR", "FCU", "PT"]
fit_sites = {s["name"]: s for s in fit["sites"]}
chain = {}
for side, suf in (("right", ""), ("left", "_l")):
    for mname in tend_names:
        tn = f"{mname}{suf}_tendon"
        refs = dict(tendon_order)[tn]
        recs = []
        for ref in refs:
            recs.append(dict(site=ref, xml_owner=sites_owned[ref],
                             fit_resolved=(not fit_sites[ref]["unresolved"]) if ref in fit_sites else None))
        chain[tn] = recs
receipt["checks"]["C7_tendon_chains"] = chain
# summary: how many of the 9 tendons per side terminate on the radius vs continue to unresolved bodies
summary = {}
for tn, recs in chain.items():
    unresolved_sites = [r["site"] for r in recs if r["fit_resolved"] is False]
    owners = sorted({r["xml_owner"] for r in recs})
    summary[tn] = dict(n_sites=len(recs), owners=owners,
                       unresolved_site_count=len(unresolved_sites),
                       unresolved_sites=unresolved_sites,
                       terminus_site=recs[-1]["site"],
                       terminus_owner=recs[-1]["xml_owner"],
                       terminus_resolved=recs[-1]["fit_resolved"])
receipt["checks"]["C7_chain_summary"] = summary

OUT.write_text(json.dumps(receipt, indent=1))
print(json.dumps(receipt["checks"], indent=1, default=str)[:6000])
print(" mismatches:", mismatch)
print(" receipt ->", OUT)
