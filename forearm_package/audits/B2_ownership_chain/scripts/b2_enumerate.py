"""B2 evidence script: ownership chain of every tendon from source endpoints
through body lookup to length/moment-arm evaluation.

READ-ONLY on the baseline. Writes only into the B2 audit receipt directory.

Outputs (receipts/b2_ownership_receipt.json):
  - full tendon census (120): owners, unresolved multiset, comparable, earliest break
  - forearm-site identification + the 18-tendon / 16-tendon grasp-critical sets
  - per-tendon path tables for the 16: index -> site -> owner -> fitted status
  - partial evaluation inventory (longest finite subchain, finite arms from packet)
  - coordinate ownership per body + meaningful coordinates per tendon
  - counterfactual unlock: resolve exactly hand_r/hand_l/ulna/ulna_l
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(os.path.dirname(HERE), "work")
sys.path.insert(0, WORK)

BASE = r"E:\PythonChimera\forearm_package\baseline_snapshot"
RECEIPTS = os.path.join(os.path.dirname(HERE), "receipts")

from intake import load_source  # noqa: E402  (work/ copy, byte-identical to snapshot)

XML = os.path.join(BASE, "source_xml", "chimanoid.xml")
FIT = os.path.join(BASE, "runs", "actual_monkey_fit.json")
ADMISSION = os.path.join(BASE, "runs", "admission_actual_monkey.json")

D2_BODIES = {"ulna", "ulna_l", "hand_r", "hand_l"}


def main() -> int:
    ana = load_source(XML)
    fit = json.load(open(FIT, encoding="utf-8"))
    adm = json.load(open(ADMISSION, encoding="utf-8"))

    out: dict = {"inputs": {"xml": XML, "fit": FIT, "admission": ADMISSION}}

    # ---- 0. identities -------------------------------------------------------
    site_owner = {s.name: s.body for s in ana.sites}          # intake: direct parent body
    tendon_sites = {t.name: list(t.site_names) for t in ana.tendons}
    coord_owner = {j.name: j.body for j in ana.joints}        # direct <joint> children only
    unresolved_set = set(adm["admission"]["bodies"]["unresolved"])
    resolved_set = set(adm["admission"]["bodies"]["geometrically_resolved"])

    # cross-check admission vs the fit packet
    json_site_unres = {s["name"] for s in fit["sites"] if s.get("unresolved")}
    json_site_owner = {s["name"]: s["segment"] for s in fit["sites"]}
    json_unres_segs = sorted(x["body"] for x in fit["unresolved_segments"])
    json_res_segs = sorted(s["source_body"] for s in fit["segments"])
    owners_match = all(json_site_owner[n] == site_owner[n] for n in site_owner)
    out["identity_checks"] = {
        "n_bodies_intake": len(ana.bodies),
        "n_coords_intake": len(ana.joints),
        "n_tendons_intake": len(ana.tendons),
        "n_tendon_referenced_sites_intake": len([s for s in ana.sites if s.referenced_by]),
        "admission_unresolved": sorted(unresolved_set),
        "fit_packet_site_unresolved_count": len(json_site_unres),
        "site_owner_intake_vs_packet_match": bool(owners_match),
        "unresolved_bodies_admission_vs_packet_match": sorted(unresolved_set) == json_unres_segs,
        "resolved_bodies_admission_vs_packet_match": sorted(resolved_set) == json_res_segs,
        "packet_site_unresolved_owners": sorted({json_site_owner[n] for n in json_site_unres}),
    }

    # ---- 1. whole-census: comparability + unresolved multisets ---------------
    def chain_state(site_names):
        """Return per-tendon facts straight from packet + intake."""
        owners = [site_owner[s] for s in site_names]
        unres_idx = [i for i, o in enumerate(owners) if o in unresolved_set]
        packet = next(t for t in fit["tendons"] if t["sites"] == site_names)
        finite = [
            (s is not None and p is not None and np.all(np.isfinite(np.array(p, dtype=float))))
            for s, p in zip(tendon_sites[packet["name"]], packet["points"])
        ]
        comparable = all(finite)
        # longest run of consecutive finite sites
        best = cur = 0
        for f in finite:
            cur = cur + 1 if f else 0
            best = max(best, cur)
        finite_arms = [
            {"coord": a["coord"], "analytic": a["analytic"]}
            for a in packet["moment_arms"]
            if a["analytic"] is not None and np.isfinite(a["analytic"])
        ]
        return {
            "owners": owners,
            "unresolved_bodies": sorted({owners[i] for i in unres_idx}),
            "first_unresolved_index": (min(unres_idx) if unres_idx else None),
            "unresolved_indices": unres_idx,
            "comparable": comparable,
            "packet_rest_length": packet["rest_length"],
            "packet_status": packet["status"],
            "packet_points_finite": finite,
            "longest_finite_run": best,
            "n_path_sites": len(site_names),
            "n_finite_arms_in_packet": len(finite_arms),
            "finite_arms_in_packet": finite_arms,
        }

    census = {}
    for t in ana.tendons:
        census[t.name] = chain_state(list(t.site_names))

    comparable_names = sorted(n for n, c in census.items() if c["comparable"])
    breakdown: dict[str, int] = {}
    for n, c in census.items():
        if c["comparable"]:
            continue
        key = "+".join(c["unresolved_bodies"]) if c["unresolved_bodies"] else "none"
        breakdown[key] = breakdown.get(key, 0) + 1
    out["census"] = {
        "n_tendons": len(census),
        "n_comparable": len(comparable_names),
        "n_non_comparable": len(census) - len(comparable_names),
        "non_comparable_breakdown_by_unresolved_multiset": dict(sorted(breakdown.items())),
        "comparable_names": comparable_names,
    }

    # ---- 2. forearm sites + the 18/16 sets -----------------------------------
    # The packet (runs/attachment_candidates.json) covers exactly radius and
    # radius_l, 16 candidates each -> the wave-1 "32 forearm sites".
    att = json.load(open(os.path.join(BASE, "runs", "attachment_candidates.json"), encoding="utf-8"))
    packet_bodies = sorted(att["bodies"].keys())
    packet_sites = sorted(
        c["site_id"] for b in att["bodies"].values() for c in b["candidates"]
    )
    packet_site_set = set(packet_sites)
    forearm_bodies = ["radius", "ulna", "radius_l", "ulna_l"]
    forearm_sites = sorted(
        s.name for s in ana.sites if s.body in forearm_bodies and s.referenced_by
    )
    touching = sorted(
        n for n, t in tendon_sites.items() if any(site_owner[s] in forearm_bodies for s in t)
    )
    resolved_touching = [n for n in touching if census[n]["comparable"]]
    unresolved_touching = [n for n in touching if not census[n]["comparable"]]
    out["forearm_site_set"] = {
        "definition_broad": "sites owned by radius/ulna/radius_l/ulna_l (referenced by tendons)",
        "bodies": forearm_bodies,
        "n_sites": len(forearm_sites),
        "sites_by_body": {
            b: sorted(s.name for s in ana.sites if s.body == b and s.referenced_by)
            for b in forearm_bodies
        },
        "n_tendons_touching_broad": len(touching),
        "touching_tendons_broad": touching,
        "comparable_touching_broad": resolved_touching,
        "non_comparable_touching_broad": unresolved_touching,
        "attachment_packet_bodies": packet_bodies,
        "n_packet_radius_sites": len(packet_sites),
        "packet_radius_sites": packet_sites,
    }

    # tendon muscle prefix (strip _tendon) grouped
    fam: dict[str, list[str]] = {}
    for n in touching:
        fam.setdefault(n[: -len("_tendon")], []).append(n)
    out["forearm_site_set"]["muscle_families"] = {k: sorted(v) for k, v in sorted(fam.items())}

    # ---- 2b. the GRASP-CRITICAL set: tendons touching the 32 radius-side sites
    grasp = sorted(
        n for n, t in tendon_sites.items() if any(s in packet_site_set for s in t)
    )
    grasp_resolved = [n for n in grasp if census[n]["comparable"]]
    grasp_unresolved = [n for n in grasp if not census[n]["comparable"]]
    out["grasp_critical_set"] = {
        "definition": "tendons with >=1 path site among the 32 radius/radius_l attachment-candidate sites",
        "n_tendons": len(grasp),
        "tendons": grasp,
        "comparable": grasp_resolved,
        "non_comparable": grasp_unresolved,
        "sixteen": grasp_unresolved,
        "n_sixteen": len(grasp_unresolved),
        "families": {
            f: sorted(fam.get(f, []))
            for f in ["BRD", "ECRB", "ECRL", "ECU", "FCR", "FCU", "PT", "BIClong", "BICshort"]
        },
    }
    sixteen = sorted(grasp_unresolved)

    # ---- 3. per-tendon tables for the 16 (+ BRD contrast) --------------------
    # source-side rest lengths (full authored geometry is known for every tendon)
    from intake import global_site_positions

    src_world = global_site_positions(ana)
    src_rest = {
        t.name: float(sum(np.linalg.norm(src_world[t.site_names[i + 1]] - src_world[t.site_names[i]])
                          for i in range(len(t.site_names) - 1)))
        for t in ana.tendons
    }
    packet_tendon = {t["name"]: t for t in fit["tendons"]}
    packet_site = {s["name"]: s for s in fit["sites"]}

    def subtree(body: str) -> set[str]:
        return set(__import__("compiler").subtree_of(ana, body))

    tables = {}
    for name in sixteen + ["BRD_tendon", "BRD_l_tendon"]:
        t = tendon_sites[name]
        st = census[name]
        pt = packet_tendon[name]
        rows = []
        for i, sn in enumerate(t):
            ps = packet_site[sn]
            pos = ps["fitted_pos_global"]
            rows.append(
                {
                    "index": i,
                    "site": sn,
                    "owner_intake": site_owner[sn],
                    "owner_packet": ps["segment"],
                    "packet_unresolved_flag": bool(ps.get("unresolved")),
                    "packet_reason": ps.get("reason", ""),
                    "fitted_pos_global_null": pos is None,
                    "fitted_pos_global": pos,
                    "source_pos_local": ps["source_pos_local"],
                }
            )
        # meaningful coords: coords whose owner-body subtree contains >=1 path site
        meaningful = []
        for j in ana.joints:
            sub = subtree(j.body)
            hits = [i for i, sn in enumerate(t) if site_owner[sn] in sub]
            if hits:
                meaningful.append(
                    {
                        "coord": j.name,
                        "owner": j.body,
                        "owner_resolved": j.body not in unresolved_set,
                        "path_indices_in_subtree": hits,
                        "packet_arm_analytic": next(
                            a["analytic"] for a in pt["moment_arms"] if a["coord"] == j.name
                        ),
                    }
                )
        tables[name] = {
            "path": rows,
            "n_sites": len(t),
            "unresolved_bodies": st["unresolved_bodies"],
            "first_unresolved_index": st["first_unresolved_index"],
            "unresolved_indices": st["unresolved_indices"],
            "comparable": st["comparable"],
            "packet_rest_length": st["packet_rest_length"],
            "source_rest_length_m": round(src_rest[name], 9),
            "packet_status": st["packet_status"],
            "longest_finite_run": st["longest_finite_run"],
            "n_finite_arms_in_packet": st["n_finite_arms_in_packet"],
            "meaningful_coordinates": meaningful,
            "counterfactual_comparable_if_D2_only": set(st["unresolved_bodies"]) <= D2_BODIES,
        }
    out["per_tendon"] = tables

    # ---- 4. coordinate ownership table (grasp-relevant) ----------------------
    out["coordinate_ownership"] = {
        j.name: {
            "body": j.body,
            "type": j.joint_type,
            "body_resolved": j.body not in unresolved_set,
            "packet_joint_status": next(
                jj["status"] for jj in fit["joints"] if jj["name"] == j.name
            ),
        }
        for j in ana.joints
    }

    # ---- 5. counterfactual unlock sets ---------------------------------------
    def unlocked(bodies_resolved_extra: set[str]) -> dict:
        newly = unresolved_set - bodies_resolved_extra
        comp, still = [], []
        for name in sixteen:
            if set(census[name]["unresolved_bodies"]) <= bodies_resolved_extra:
                comp.append(name)
            else:
                still.append((name, census[name]["unresolved_bodies"]))
        return {
            "assumed_resolved": sorted(bodies_resolved_extra),
            "still_unresolved_everywhere": sorted(newly),
            "sixteen_become_comparable": sorted(comp),
            "n_become_comparable": len(comp),
            "sixteen_still_blocked": {n: b for n, b in still},
        }

    out["counterfactuals"] = {
        "D2_only (ulna,ulna_l,hand_r,hand_l)": unlocked(D2_BODIES),
        "D2_plus_thorax": unlocked(D2_BODIES | {"thorax"}),
        "thorax_only": unlocked({"thorax"}),
        "hand_only": unlocked({"hand_r", "hand_l"}),
        "ulna_only": unlocked({"ulna", "ulna_l"}),
        "all_nine_resolved": unlocked(unresolved_set),
    }

    # earliest-breaker census for the 16
    breaker: dict[str, list[str]] = {}
    for name in sixteen:
        st = census[name]
        b = st["owners"][st["first_unresolved_index"]]
        breaker.setdefault(b, []).append(name)
    out["earliest_breaker_census"] = breaker

    # ---- 6. packet-level finite-arm context (E-2 verification) ---------------
    all_finite_arms = []
    zero_arms = nonzero_arms = 0
    for t in fit["tendons"]:
        for a in t["moment_arms"]:
            if a["analytic"] is not None and np.isfinite(a["analytic"]):
                all_finite_arms.append((t["name"], a["coord"], a["analytic"]))
                if abs(a["analytic"]) < 1e-12:
                    zero_arms += 1
                else:
                    nonzero_arms += 1
    out["packet_arm_context"] = {
        "n_tendon_coord_pairs_total": sum(len(t["moment_arms"]) for t in fit["tendons"]),
        "n_finite_arms": len(all_finite_arms),
        "n_zero_finite_arms": zero_arms,
        "n_nonzero_finite_arms": nonzero_arms,
        "nonzero_examples": [
            {"tendon": n, "coord": c, "analytic": v}
            for n, c, v in all_finite_arms if abs(v) >= 1e-12
        ][:50],
    }

    os.makedirs(RECEIPTS, exist_ok=True)
    rp = os.path.join(RECEIPTS, "b2_ownership_receipt.json")
    with open(rp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o))
    print("wrote", rp)

    # ---- console summary ------------------------------------------------------
    print(json.dumps(out["identity_checks"], indent=1))
    print(json.dumps(out["census"]["non_comparable_breakdown_by_unresolved_multiset"], indent=1))
    print("comparable:", out["census"]["n_comparable"], "/", out["census"]["n_tendons"])
    print("forearm touching (broad):", out["forearm_site_set"]["n_tendons_touching_broad"],
          "unresolved:", out["forearm_site_set"]["n_sites"], "sites")
    print("grasp set:", out["grasp_critical_set"]["n_tendons"], out["grasp_critical_set"]["tendons"])
    print("sixteen:", sixteen)
    print("earliest breakers:", json.dumps(out["earliest_breaker_census"], indent=1))
    for k, v in out["counterfactuals"].items():
        print(k, "->", v["n_become_comparable"], "comparable; still blocked:", list(v["sixteen_still_blocked"]))
    print("finite arms packet-wide:", out["packet_arm_context"]["n_finite_arms"],
          "zero:", out["packet_arm_context"]["n_zero_finite_arms"],
          "nonzero:", out["packet_arm_context"]["n_nonzero_finite_arms"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
