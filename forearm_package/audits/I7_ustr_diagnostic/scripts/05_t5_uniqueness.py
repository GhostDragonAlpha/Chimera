"""05 — T5 UNIQUENESS for the declared U-STR candidate (ulna + ulna_l).

Adapted invocation of the B4 T5 machinery (B4 scripts/06_t5_uniqueness.py); metric
UNCHANGED (protocol §3-T5 as amended A5):

PRIMARY — resolution-consistency count: how many source bodies B' have an
XML-consistent landmark resolution that COINCIDES with the declared source
resolutions (prox = body_origin:B', dist = body_origin:chain_child(B') or the leaf
law, roll site owned by {B', parent, child})? Unique ownership iff count == 1 and
the supporter is the declared body.

FALLBACK — not applicable (the candidate declares full source resolutions); the
factor-2 implied-scale table is recorded as CONTEXT, never the gate.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i7_common as IC  # noqa: E402
import b4_common as C  # noqa: E402

sys.path.insert(0, str(IC.B4 / "work" / "modules"))
from intake import global_site_positions, load_source  # noqa: E402

EDGES = {"ulna": "ulna", "ulna_l": "ulna_l"}


def chain_child(B: str, bodies) -> str | None:
    return next((n for n, m in bodies.items() if m["parent"] == B), None)


def own_resolution(B: str, bodies, ana, sw) -> dict:
    A = ana.body_by_name[B].pos_global
    child = chain_child(B, bodies)
    if child is not None:
        dist = f"body_origin:{child}"
        D = ana.body_by_name[child].pos_global
    else:
        own = [s for s in ana.sites if s.body == B and s.referenced_by]
        if not own:
            return {"prox": f"body_origin:{B}", "dist": None, "span": float("inf"),
                    "roll_legal": set()}
        far = max(own, key=lambda s: np.linalg.norm(sw[s.name] - A))
        dist = f"site:{far.name}"
        D = sw[far.name]
    roll_legal = {B, bodies[B]["parent"], child} - {None}
    return {"prox": f"body_origin:{B}", "dist": dist,
            "span": float(np.linalg.norm(D - A)), "roll_legal": roll_legal}


def xml_owner_of_site(sname: str, bodies) -> str | None:
    return next((n for n, meta in bodies.items() if sname in meta["sites"]), None)


def main() -> int:
    recs = IC.load_candidate()
    bodies, parent_of, sites_of = C.load_xml_tree()
    real = load_source(str(IC.XML_PATH))
    sw = global_site_positions(real)

    receipt = {"edges": {}}
    ok_all = True
    for edge_name, declared in EDGES.items():
        lm = recs["records"][declared]["landmarks"]
        P = np.asarray(lm["prox"]["target"], dtype=float)
        P_d = np.asarray(lm["dist"]["target"], dtype=float)
        tgt_len = float(np.linalg.norm(P_d - P))
        declared_res = {
            "prox": lm["prox"]["source_resolution"],
            "dist": lm["dist"]["source_resolution"],
            "roll": lm["roll"]["source_resolution"],
        }
        declared_roll_site = declared_res["roll"].partition(":")[2]
        declared_roll_owner = xml_owner_of_site(declared_roll_site, bodies)
        s_decl = float(recs["records"][declared]["implied_axial_scale"])
        lo, hi = s_decl / C.SCALE_BAND_FACTOR, s_decl * C.SCALE_BAND_FACTOR

        supporters = []
        for B in bodies:
            if parent_of[B] is None:
                continue
            own = own_resolution(B, bodies, real, sw)
            if own["prox"] == declared_res["prox"] and own["dist"] == declared_res["dist"] \
                    and declared_roll_owner in own["roll_legal"]:
                supporters.append(B)
        count = len(supporters)
        primary_ok = count == 1 and supporters == [declared]

        table = {}
        for B in bodies:
            if parent_of[B] is None:
                continue
            own = own_resolution(B, bodies, real, sw)
            sB = tgt_len / own["span"] if own["span"] > C.DEGENERATE_FLOOR else float("inf")
            table[B] = {"s": sB, "own_dist": own["dist"], "in_band": lo <= sB <= hi}
        in_band_others = sorted(B for B, d in table.items() if d["in_band"] and B != declared)

        ok = primary_ok
        ok_all &= ok
        others = sorted(((B, d["s"]) for B, d in table.items() if B != declared and d["s"] > 0),
                        key=lambda kv: abs(np.log(kv[1] / s_decl)))
        nearest, s_near = others[0]
        C.verdict(f"T5 uniqueness ({declared} on its declared edge)", ok,
                  f"resolution-consistent supporters={supporters} (count={count}) "
                  f"| nearest scale alternative={nearest} s={s_near:.6f} "
                  f"({abs(np.log(s_near / s_decl)) / np.log(2):.2f} log2 away) "
                  f"| in-band others (context, not gate)={in_band_others}")
        receipt["edges"][edge_name] = {
            "declared": declared, "declared_resolutions": declared_res,
            "declared_roll_xml_owner": declared_roll_owner,
            "target_edge_len_m": tgt_len, "s_declared": s_decl,
            "resolution_supporters": supporters, "supporter_count": count,
            "primary_ok": primary_ok,
            "in_band_others_context": in_band_others,
            "nearest_scale_alternative": {"body": nearest, "s": s_near},
            "scale_table_context": table,
            "ok": ok,
        }

    receipt["ok"] = ok_all
    IC.save_receipt("05_t5_uniqueness.json", receipt)
    print("T5 VERDICT:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
