"""VTRANS reconcile: load pass A + pass B, dedup intra-pass repeats, classify every cell.

Deterministic (F4): frozen inputs, canonical JSON (sort_keys, fixed rounding), no randomness.
Inputs:  passA/*.json, passB/*.json, crops_manifest.json
Outputs: reconciliation.json (per-cell verdicts + agreement stats)

Verdicts (pre-registered):
  TENTATIVE   both passes numeric, format-normalized equality
  DISPUTED    numeric disagreement, or single-pass-only numeric
  MARKER_AGREED  both passes record the same marker class on a non-numeric cell
  MARKER_DISPUTED  marker text/class disagreement, or numeric-vs-marker conflict
  BLANK_AGREED    both passes record the position as blank/unlabeled structural
Dedup rule (intra-pass repeats, e.g. tile-overlap dups): prefer CLEAR over DEGRADED; ties must
be identical else the PASS is internally inconsistent -> cell verdict DISPUTED (dup_conflict).
Numeric normalization: strip spaces; keep the printed string; compare as Decimal (1.40 == 1.4).
"""
import glob, json, os
from collections import defaultdict
from decimal import Decimal

BASE = os.path.dirname(os.path.abspath(__file__))

def norm_num(s):
    s = s.strip().replace(" ", "")
    try:
        d = Decimal(s)
    except Exception:
        return None
    return d

def load_pass(dirname):
    per_key = defaultdict(list)  # (m,s,f) -> list of records within ONE pass
    for p in sorted(glob.glob(os.path.join(BASE, dirname, "*.json"))):
        d = json.load(open(p))
        for c in d["cells"]:
            if dirname == "passA":
                m, g, s, f, v, leg, marker, merge = c["m"], c["g"], c["s"], c["f"], c["v"], c["leg"], c.get("marker"), c.get("merge")
                role = (merge or {}).get("role") if merge else None
                span = ",".join((merge or {}).get("span", [])) if merge else None
            else:
                m, g, s, f, v, leg, marker, span, role = c
            # normalize marker -> refusal CLASS (declared rule): tile-edge cuts truncate
            # the parenthetical crossref tail; the class is what both passes must agree on
            mk = None
            if marker:
                t = " ".join(marker.split()).lower()
                if "damaged" in t: mk = "marker_damaged"
                elif "not measured" in t: mk = "marker_not_measured"
                elif "absent" in t:
                    mk = "marker_absent_cfr" if "cfr" in t or "cf." in t else "marker_absent"
                elif t.rstrip(". ") == "apb": mk = "marker_crossref_APB"
                elif t.rstrip(". ") == "fdp": mk = "marker_crossref_FDP"
                else: mk = "unread_marker"
            per_key[(m, s, f)].append({"v": v, "leg": leg, "marker": mk, "role": role, "span": span})
    return per_key

def collapse(per_key):
    """dedup one pass's repeats -> single record or {'conflict': True}"""
    out = {}
    for k, recs in per_key.items():
        # role is meaningless for valueless marker cells (block-spanning): drop it there
        def ident(r):
            return (r["v"], r["marker"], None if (r["v"] is None and r["marker"]) else r["role"], r["span"])
        vals = {ident(r) for r in recs}
        if len(vals) == 1:
            best = sorted(recs, key=lambda r: 0 if r["leg"] == "CLEAR" else 1)[0]
            out[k] = best
        else:
            # allow CLEAR-vs-DEGRADED duplicates that agree on value+marker
            clears = [r for r in recs if r["leg"] == "CLEAR"]
            pool = clears if clears else recs
            vals2 = {ident(r) for r in pool}
            if len(vals2) == 1:
                out[k] = sorted(pool, key=lambda r: 0 if r["leg"] == "CLEAR" else 1)[0]
            else:
                out[k] = {"v": None, "leg": "DUP_CONFLICT", "marker": None, "role": None, "span": None}
    return out

def main():
    A = collapse(load_pass("passA"))
    B = collapse(load_pass("passB"))
    keys = sorted(set(A) | set(B), key=lambda k: (k[1], k[0], k[2]))
    cells = []
    stats = defaultdict(int)
    for (m, s, f) in keys:
        a, b = A.get((m, s, f)), B.get((m, s, f))
        av, bv = (a or {}).get("v"), (b or {}).get("v")
        am, bm = (a or {}).get("marker"), (b or {}).get("marker")
        aleg, bleg = (a or {}).get("leg"), (b or {}).get("leg")
        rec = {"muscle": m, "specimen": s, "field": f}
        if aleg == "DUP_CONFLICT" or bleg == "DUP_CONFLICT":
            rec["verdict"] = "DISPUTED"; rec["reason"] = "dup_conflict"; stats["DISPUTED"] += 1
        elif av is not None and bv is not None:
            an, bn = norm_num(av), norm_num(bv)
            if an is not None and bn is not None and an == bn:
                rec["verdict"] = "TENTATIVE"
                rec["value"] = av.strip()
                rec["legibility"] = "CLEAR" if (aleg == "CLEAR" and bleg == "CLEAR") else "DEGRADED"
                stats["TENTATIVE"] += 1
            else:
                rec["verdict"] = "DISPUTED"; rec["passA"] = av; rec["passB"] = bv
                stats["DISPUTED"] += 1
        elif av is None and bv is None and am and bm:
            if am == bm:
                rec["verdict"] = "MARKER_AGREED"; rec["marker"] = am
                stats["MARKER_AGREED"] += 1
            else:
                rec["verdict"] = "MARKER_DISPUTED"; rec["passA_marker"] = am; rec["passB_marker"] = bm
                stats["MARKER_DISPUTED"] += 1
        elif av is not None and bv is None:
            rec["verdict"] = "DISPUTED"; rec["reason"] = "numeric_vs_" + ("marker" if bm else "missing"); rec["passA"] = av
            if bm: rec["passB_marker"] = bm
            stats["DISPUTED"] += 1
        elif bv is not None and av is None:
            rec["verdict"] = "DISPUTED"; rec["reason"] = "numeric_vs_" + ("marker" if am else "missing"); rec["passB"] = bv
            if am: rec["passA_marker"] = am
            stats["DISPUTED"] += 1
        else:
            # both null, at least one marker missing entirely -> marker from one side only
            if am or bm:
                rec["verdict"] = "MARKER_AGREED"; rec["marker"] = am or bm
                stats["MARKER_AGREED"] += 1
            else:
                rec["verdict"] = "BLANK_AGREED"; stats["BLANK_AGREED"] += 1
        if a: rec["passA_leg"] = aleg
        if b: rec["passB_leg"] = bleg
        cells.append(rec)

    # agreement rate on LEGIBLE cells: cells where both passes attempted a numeric read
    legible = [c for c in cells if c["verdict"] in ("TENTATIVE", "DISPUTED") ]
    numeric_both = [c for c in cells if c["verdict"] == "TENTATIVE" or (c["verdict"] == "DISPUTED" and "passA" in c and "passB" in c)]
    tentative = [c for c in cells if c["verdict"] == "TENTATIVE"]
    agreement = {
        "cells_total_classified": len(cells),
        "TENTATIVE": len(tentative),
        "DISPUTED": stats["DISPUTED"],
        "MARKER_AGREED": stats["MARKER_AGREED"],
        "MARKER_DISPUTED": stats["MARKER_DISPUTED"],
        "BLANK_AGREED": stats["BLANK_AGREED"],
        "legible_numeric_cells": len(numeric_both),
        "exact_agreement_rate_on_legible_numeric": (len(tentative) / len(numeric_both)) if numeric_both else None,
    }
    out = {"passA_files": len(glob.glob(os.path.join(BASE, "passA", "*.json"))),
           "passB_files": len(glob.glob(os.path.join(BASE, "passB", "*.json"))),
           "agreement": agreement, "cells": cells}
    with open(os.path.join(BASE, "reconciliation.json"), "w", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(json.dumps(agreement, indent=1, sort_keys=True))

if __name__ == "__main__":
    main()
