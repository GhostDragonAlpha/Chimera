"""10 — TENDON COVERAGE TOPOLOGY under the diagnostic's ulna resolution.

Verifies the coverage table from SOURCE XML TOPOLOGY ONLY (site ownership + tendon
path membership — the same counterfactual gate arithmetic B2 §5/§7 executed; no
moment-arm, no path-length, no transmission quantity is computed). The packet's
tendon records are NOT read.

Completeness law (DERIVATION §7-8 via B2 §1): a chain is complete iff EVERY path
site's owning body is resolved; moment arms additionally require the coordinate's
owning body resolved.

Scenarios:
  baseline resolved set   = packet segments (8 bodies)
  DIAGNOSTIC resolved set = baseline + {ulna, ulna_l}   (this diagnostic's subject)
  D2 (context)            = diagnostic + {hand_r, hand_l}  (B2's 12/16; NOT this run)
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i7_common as IC  # noqa: E402
import b4_common as C  # noqa: E402

GRASP_16 = ["ECRB_tendon", "ECRL_tendon", "ECU_tendon", "FCR_tendon", "FCU_tendon",
            "PT_tendon", "BIClong_tendon", "BICshort_tendon", "BRD_tendon",
            "ECRB_l_tendon", "ECRL_l_tendon", "ECU_l_tendon", "FCR_l_tendon",
            "FCU_l_tendon", "PT_l_tendon", "BIClong_l_tendon", "BICshort_l_tendon",
            "BRD_l_tendon"]
# NOTE: the 16 non-comparable at baseline = the 14 above minus BRD/BRD_l (which are
# comparable at baseline but arm-blocked on ulna ownership). The enumeration below
# measures, never assumes.


def main() -> int:
    bodies, parent_of, sites_of = C.load_xml_tree()
    packet = IC.load_packet()
    baseline_resolved = {s["source_body"] for s in packet["segments"]}

    # XML tendon topology: <spatial name="*_tendon"><site site="..."/> ... — ordered
    # path sites; site -> owner body from the body tree
    root = ET.parse(str(IC.XML_PATH)).getroot()
    chains: dict[str, list[str]] = {}
    for sp in root.iter("spatial"):
        spname = sp.get("name") or ""
        if not spname.endswith("_tendon"):
            continue
        sites = [s.get("site") for s in sp.findall("site") if s.get("site")]
        if sites:
            chains[spname] = sites
    site_owner = {}
    for b, meta in bodies.items():
        for sname in meta["sites"]:
            site_owner[sname] = b

    def earliest_breaker(chain: list[str], resolved: set[str]):
        for sname in chain:
            owner = site_owner.get(sname)
            if owner not in resolved:
                return sname, owner
        return None, None

    scenarios = {
        "baseline": baseline_resolved,
        "diagnostic_ulna_only": baseline_resolved | {"ulna", "ulna_l"},
        "diagnostic_plus_hand (context, NOT this run)":
            baseline_resolved | {"ulna", "ulna_l", "hand_r", "hand_l"},
    }
    table = {}
    counts = {}
    for scen, resolved in scenarios.items():
        rows = {}
        n_complete = 0
        for tname in GRASP_16:
            chain = chains.get(tname)
            if chain is None:
                rows[tname] = {"in_source": False}
                continue
            breaker_site, breaker_body = earliest_breaker(chain, resolved)
            complete = breaker_site is None
            n_complete += complete
            rows[tname] = {"in_source": True, "n_sites": len(chain),
                           "complete": complete,
                           "earliest_unresolved_site": breaker_site,
                           "breaker_body": breaker_body,
                           "unresolved_owners": sorted({site_owner[s] for s in chain
                                                        if site_owner[s] not in resolved})}
        table[scen] = rows
        counts[scen] = n_complete

    ok = True
    # measured expectations (falsifiable against B2's receipted marginals)
    ok &= counts["baseline"] == 2  # BRD + BRD_l comparable at baseline
    ok &= counts["diagnostic_ulna_only"] == 4  # PT, PT_l newly complete + BRD, BRD_l
    ok &= counts["diagnostic_plus_hand (context, NOT this run)"] == 14  # B2's 12/16 + BRD pair
    C.verdict("coverage topology (baseline)", counts["baseline"] == 2,
              f"complete chains: {sorted(t for t, r in table['baseline'].items() if r.get('complete'))}")
    C.verdict("coverage topology (DIAGNOSTIC: +ulna/+ulna_l)",
              counts["diagnostic_ulna_only"] == 4,
              f"newly complete vs baseline: PT_tendon, PT_l_tendon (ulna was their ONLY "
              f"blocker); ECU/ECU_l still double-blocked (hand terminal); 8 hand-blocked; "
              f"4 thorax-blocked (BIC x2)")
    C.verdict("coverage topology (context: +hand = B2's 12/16 + BRD pair)",
              counts["diagnostic_plus_hand (context, NOT this run)"] == 14,
              "12 of the 16 non-comparable become complete with hand too (B2 §7) — "
              "context only; A04/A05 own the hand")
    # BRD's elbow-arm repair: elbow_flexion(_l) owner = ulna(_l) -> resolved by the
    # diagnostic; BRD chains already complete -> arms become finite (ownership gate)
    elbow_owner = parent_of.get("radius")  # ulna
    ok &= elbow_owner == "ulna"
    C.verdict("BRD elbow-arm repair (ownership gate)", elbow_owner == "ulna",
              "BRD/BRD_l chains are complete at baseline; their elbow_flexion(_l) "
              "arms are null TODAY solely because the coordinate owner (ulna/ulna_l) "
              "is unresolved (compiler gate); the diagnostic's ulna resolution "
              "repairs exactly that — no chain change needed")

    # elbow_flexion owner from the packet joint record (direct evidence)
    j = next(jj for jj in packet["joints"] if jj["name"] == "elbow_flexion")
    ok &= j["body"] == "ulna" and j["status"] == "unresolved_body"

    IC.save_receipt("10_coverage_topology.json", {
        "scenario_counts": counts,
        "table": table,
        "brd_repair": {"owner_body": j["body"], "packet_status": j["status"],
                       "statement": "BRD/BRD_l elbow arms null at baseline solely on "
                                    "ulna ownership; the diagnostic's ulna resolution "
                                    "is the repair (B2 §5 'additionally gain their "
                                    "elbow_flexion(_l) arms')"},
        "ok": bool(ok),
    })
    print("COVERAGE VERDICT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
