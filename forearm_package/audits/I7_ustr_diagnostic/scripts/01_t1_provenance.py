"""01 — T1 SOURCE-PROVENANCE for the declared U-STR candidate (ulna + ulna_l).

Adapted invocation of the B4 T1 machinery (B4 scripts/02_t1_provenance.py) to the
declared candidate records; every identity relation and the procedure are UNCHANGED:
 (a) declared parent == XML parent (chain_conflict law); the packet's own record for
     the body (it sits in unresolved_segments — anchor-only, never fitted) is checked
     for provenance: present, no fabricated transform.
 (b) claimed site set == XML direct site set — full-body table (the candidate claims
     the body's own XML set; the packet's exported sites[*].segment sets must equal it).
 (c) source landmark resolutions: prox == body_origin:<body>; dist ==
     body_origin:<chain_child per XML>; roll site owned by {body, parent, child}.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i7_common as IC  # noqa: E402
import b4_common as C  # noqa: E402

BODIES = IC.CANDIDATE_BODIES


def main() -> int:
    bodies, parent_of, sites_of = C.load_xml_tree()
    packet = IC.load_packet()
    recs = IC.load_candidate()

    lines, receipt = [], {"checks": [], "adaptation": "packet record for the candidate "
        "bodies lives in unresolved_segments (anchor-only); the T1a packet leg asserts "
        "presence + no fabricated transform instead of a fitted-segment parent field"}

    # (a) parentage — declared vs XML; packet record = unresolved_segments entry
    unresolved = {u["body"]: u for u in packet["unresolved_segments"]}
    for b in BODIES:
        xml_parent = parent_of[b]
        rec_parent = recs["records"][b]["parent"]
        pkt = unresolved.get(b)
        ok_pkt = pkt is not None and pkt.get("reason", "").startswith("no fitted scale")
        ok = (xml_parent == rec_parent) and ok_pkt
        lines.append(C.verdict(f"T1a parent({b}) == XML parent", ok,
                       f"xml={xml_parent} declared={rec_parent}; packet record: "
                       f"unresolved_segments['{b}'] reason='{pkt.get('reason') if pkt else None}'"))
        receipt["checks"].append({"check": f"T1a parent {b}", "ok": ok,
                                  "xml": xml_parent, "declared": rec_parent,
                                  "packet_unresolved_reason": pkt.get("reason") if pkt else None})

    # (b) site ownership — full-body table (same as the known-good run)
    pkt_sites: dict[str, set] = {}
    for s in packet["sites"]:
        pkt_sites.setdefault(s["segment"], set()).add(s["name"])
    table, all_ok = {}, True
    for b, meta in bodies.items():
        xml_set = set(meta["sites"])
        pkt_set = pkt_sites.get(b, set())
        ok = xml_set == pkt_set
        all_ok &= ok
        table[b] = {"n_xml": len(xml_set), "n_packet": len(pkt_set), "equal": ok,
                    "xml_only": sorted(xml_set - pkt_set), "packet_only": sorted(pkt_set - xml_set)}
    lines.append(C.verdict("T1b claimed site set == XML site set (all 18 bodies)", all_ok,
                           "; ".join(f"{b}:{table[b]['n_xml']}=={table[b]['n_packet']}" for b in BODIES)))
    receipt["checks"].append({"check": "T1b site ownership (all bodies)", "ok": all_ok, "table": table})

    # (c) source landmark resolutions
    def chain_child(body):
        return next((n for n, m in bodies.items() if m["parent"] == body), None)

    res_ok_all = True
    for b in BODIES:
        lm = recs["records"][b]["landmarks"]
        prox_res = lm["prox"]["source_resolution"]
        dist_res = lm["dist"]["source_resolution"]
        roll_res = lm["roll"]["source_resolution"]
        child = chain_child(b)
        ok_prox = prox_res == f"body_origin:{b}"
        ok_dist = dist_res == f"body_origin:{child}"
        kind, _, sname = roll_res.partition(":")
        owner = next((bn for bn, meta in bodies.items() if sname in meta["sites"]), None)
        legal = {b, parent_of[b], child}
        ok_roll = kind == "site" and owner in legal
        res_ok = ok_prox and ok_dist and ok_roll
        res_ok_all &= res_ok
        lines.append(C.verdict(f"T1c source resolutions ({b})", res_ok,
                       f"prox={prox_res} dist={dist_res} roll={roll_res} "
                       f"(XML owner={owner}, legal={sorted(legal)})"))
        receipt["checks"].append({"check": f"T1c resolutions {b}", "ok": res_ok,
                                  "prox": prox_res, "dist": dist_res, "roll": roll_res,
                                  "roll_xml_owner": owner, "legal_owners": sorted(legal)})

    receipt["lines"] = lines
    IC.save_receipt("01_t1_provenance.json", receipt)
    ok_all = all(c["ok"] for c in receipt["checks"])
    print("T1 VERDICT:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
