"""A7 step 4 - baseline grasp consequences (FACTS ONLY, no recommendations).

Assembles, from the frozen packets alone:
  - the 18 tendons touching the 32 forearm sites: full ordered site list with
    owning bodies, stored L0 (null when the chain hits an unresolved body),
    muscle status in the packet;
  - the 32 sites' containment classes under BOTH recorded authorities
    (loop authority = FINAL per report 05 section 4-B; hull sampling = diagnostic);
  - independent count of the step_B baseline loop verdicts per side
    (report 05 section 4-B claims 6 inside / 1 tight / 7 outside / 2 ambiguous);
  - which chains cross toward the unresolved hand (what that limits is stated,
    from packet fields, not inferred).
Separation of claims is anchored on report 05 section 6 (what is NOT claimed).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\A7_paths\receipts")

FIT = json.loads((BASE / "runs" / "actual_monkey_fit.json").read_text(encoding="utf-8"))
CAND = json.loads((BASE / "runs" / "attachment_candidates.json").read_text(encoding="utf-8"))
EXP = json.loads((BASE / "runs" / "experiment_transverse_candidate.json").read_text(encoding="utf-8"))

site_rec = {s["name"]: s for s in FIT["sites"]}
tendon_by_name = {t["name"]: t for t in FIT["tendons"]}
muscle_by_tendon = {m["tendon"]: m for m in FIT["muscles"] if m.get("tendon")}

# containment from both recorded authorities
loop_verdict, hull_verdict = {}, {}
for body in ("radius", "radius_l"):
    for rec in CAND["bodies"][body]["candidates"]:
        loop_verdict[rec["site_id"]] = rec["skin_containment"]["loop"]["verdict"]
        hull_verdict[rec["site_id"]] = rec["skin_containment"]["hull_sampling_diagnostic"]["verdict"]

# independent recount of step_B baseline loop authority (experiment record)
stepB = EXP["step_B_baseline_loop_authority"]
recount = {}
for body, blk in stepB.items():
    vc = Counter(r["verdict"] for r in blk["per_site"].values())
    recount[body] = dict(vc)
    # cross-check the record's own counts
    for k, n in vc.items():
        key = {"inside": "n_inside", "inside_insufficient_clearance": "n_inside_insufficient_clearance",
               "outside": "n_outside", "unresolved": "n_unresolved"}[k]
        assert blk[key] == n, f"{body} {k}: record says {blk[key]}, recount {n}"

# candidates-packet loop verdicts vs experiment step_B per_site verdicts
verdict_mismatch = []
for body, blk in stepB.items():
    for site, r in blk["per_site"].items():
        if loop_verdict.get(site) != r["verdict"]:
            verdict_mismatch.append({"site": site, "candidates_packet": loop_verdict.get(site),
                                     "experiment_step_B": r["verdict"]})

# 32-site resolution status
res_status = []
for body in ("radius", "radius_l"):
    for rec in CAND["bodies"][body]["candidates"]:
        s = site_rec[rec["site_id"]]
        res_status.append({
            "site": rec["site_id"], "owning_body": s["segment"],
            "packet_resolved": s["fitted_pos_global"] is not None and not s.get("unresolved", False),
            "candidates_packet_resolved": rec["fitted"]["resolved"],
            "loop_verdict": loop_verdict[rec["site_id"]],
            "hull_diagnostic_verdict": hull_verdict[rec["site_id"]],
        })
n_resolved = sum(1 for r in res_status if r["packet_resolved"] and r["candidates_packet_resolved"])

# the 18 touching tendons
touch = sorted(t["name"] for t in FIT["tendons"] if any(s in loop_verdict for s in t["sites"]))
rows = []
for name in touch:
    t = tendon_by_name[name]
    m = muscle_by_tendon.get(name, {})
    fore_sites = [s for s in t["sites"] if s in loop_verdict]
    hand_bodies = sorted({site_rec[s]["segment"] for s in t["sites"]
                          if site_rec[s]["segment"] in ("hand_r", "hand_l")})
    ulna_bodies = sorted({site_rec[s]["segment"] for s in t["sites"]
                          if site_rec[s]["segment"] in ("ulna", "ulna_l")})
    rows.append({
        "tendon": name,
        "n_path_sites": len(t["sites"]),
        "path_sites_bodies": [site_rec[s]["segment"] for s in t["sites"]],
        "forearm_sites_among_32": fore_sites,
        "stored_L0_m": t["rest_length"],
        "packet_status": t["status"],
        "crosses_to_unresolved_hand": hand_bodies,
        "touches_unresolved_ulna": ulna_bodies,
        "muscle_status": m.get("status"),
        "muscle_rest_length": m.get("rest_length"),
        "n_moment_arms_all_nonfinite": all(
            ma["analytic"] is None for ma in t["moment_arms"]) if not t["moment_arms"] else all(
            ma["analytic"] is None for ma in t["moment_arms"]),
    })

receipt = {
    "stepB_recount_per_side": recount,
    "record_stepB_counts_match_recount": True,
    "candidates_vs_experiment_verdict_mismatches": verdict_mismatch,
    "n_32_sites_resolved_both_packets": n_resolved,
    "containment_class_counts_32": dict(Counter(r["loop_verdict"] for r in res_status)),
    "hull_diagnostic_counts_32": dict(Counter(r["hull_diagnostic_verdict"] for r in res_status)),
    "per_site": res_status,
    "touching_tendons": rows,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "step4_grasp_consequences_receipt.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in receipt.items() if k not in ("per_site", "touching_tendons")}, indent=1))
print("-- tendons touching the 32 --")
for r in rows:
    print(f"{r['tendon']}: n={r['n_path_sites']} bodies={r['path_sites_bodies']} "
          f"fore32={r['forearm_sites_among_32']} L0={r['stored_L0_m']} status={r['packet_status']} "
          f"muscle={r['muscle_status']}")
