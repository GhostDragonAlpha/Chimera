"""02 — T1 SOURCE-PROVENANCE against the known-good (radius + radius_l).

Checks (challenge_protocol.md T1):
 (a) declared parent == XML parent (chain_conflict law);
 (b) claimed site set (fit packet `sites[*]` with segment == body) == XML direct
     site set of the body — for the two claimed bodies and, for context, all bodies;
 (c) source landmark resolutions: prox == body_origin:<body>; dist ==
     body_origin:<chain_child per XML>; roll site owned by {body, parent, child}.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402

BODIES = ("radius", "radius_l")


def main() -> int:
    bodies, parent_of, sites_of = C.load_xml_tree()
    packet = C.load_packet()
    recs = json.load(open(C.RECEIPTS / "01_known_good_records.json", encoding="utf-8"))

    lines, receipt = [], {"checks": []}

    # (a) parentage — packet segments + declared records vs XML
    seg_by_body = {s["source_body"]: s for s in packet["segments"]}
    for b in BODIES:
        xml_parent = parent_of[b]
        pkt_parent = seg_by_body[b]["parent"]
        rec_parent = recs["records"][b]["parent"]
        ok = (xml_parent == pkt_parent == rec_parent)
        lines.append(C.verdict(f"T1a parent({b}) == XML parent", ok,
                       f"xml={xml_parent} packet={pkt_parent} declared={rec_parent}"))
        receipt["checks"].append({"check": f"T1a parent {b}", "ok": ok,
                                  "xml": xml_parent, "packet": pkt_parent, "declared": rec_parent})

    # (b) site ownership — full-body table
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
                           "; ".join(f"{b}:{table[b]['n_xml']}=={table[b]['n_packet']}"
                                     for b in BODIES)))
    receipt["checks"].append({"check": "T1b site ownership (all bodies)", "ok": all_ok, "table": table})

    # (c) source landmark resolutions
    def chain_child(body):
        for n, m in bodies.items():
            if m["parent"] == body:
                return n
        return None

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
        owner = None
        for bn, meta in bodies.items():
            if sname in meta["sites"]:
                owner = bn
                break
        legal = {b, parent_of[b], child}
        ok_roll = kind == "site" and owner in legal
        res_ok = ok_prox and ok_dist and ok_roll
        res_ok_all &= res_ok
        lines.append(C.verdict(f"T1c source resolutions ({b})", res_ok,
                       f"prox={prox_res} dist={dist_res} roll={roll_res} (XML owner={owner}, legal={sorted(legal)})"))
        receipt["checks"].append({"check": f"T1c resolutions {b}", "ok": res_ok,
                                  "prox": prox_res, "dist": dist_res, "roll": roll_res,
                                  "roll_xml_owner": owner, "legal_owners": sorted(legal)})

    receipt["lines"] = lines
    C.save_receipt("02_t1_provenance.json", receipt)
    print("T1 VERDICT:", "PASS" if all(c["ok"] for c in receipt["checks"]) else "FAIL")
    return 0 if all(c["ok"] for c in receipt["checks"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
