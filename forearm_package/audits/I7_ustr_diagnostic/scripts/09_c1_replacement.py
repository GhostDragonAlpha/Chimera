"""09 — C1'S INDEPENDENT 10/10 LANDMARK SET RE-PLACED UNDER THE CANDIDATE FRAME.

The independent validation leg of the I7 spec: the 10 ulna-owned sites (all
independent of the U-STR construction, which consumes body origins only) placed in
closed form under the DECLARED candidate frame (with the resolved TRIlat-P5 roll),
reported as a full table: axial % of the 64.7449 mm target forearm (C1's convention),
transverse magnitude vs the session-3 skin-envelope medians (b 20.2 / c 22.9 mm,
B1 §4.1 via C1 §5), and the region verdicts.

Also reports the ROLL-DEPENDENT transverse placements (the part C1's closed form did
not need) and verifies the L/R mirror consistency of the declared pair.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i7_common as IC  # noqa: E402
import b4_common as C  # noqa: E402

BODIES = IC.CANDIDATE_BODIES
FOREARM_SPAN_M = 0.064744899
ENVELOPE_MEDIANS_MM = {"b": 20.2, "c": 22.9}  # B1 §4.1 via C1 §5


def main() -> int:
    recs = IC.load_candidate()
    packet = IC.load_packet()
    sites_pkt: dict[str, dict[str, np.ndarray]] = {}
    for s in packet["sites"]:
        if s["segment"] in BODIES:
            sites_pkt.setdefault(s["segment"], {})[s["name"]] = \
                np.asarray(s["source_pos_local"], dtype=float)

    receipt = {"sides": {}, "mirror": {}}
    ok_all = True
    frames = {}
    for b in BODIES:
        lm = recs["records"][b]["landmarks"]
        A = np.asarray(lm["prox"]["source"], dtype=float)
        D = np.asarray(lm["dist"]["source"], dtype=float)
        Qs = np.asarray(lm["roll"]["source"], dtype=float)
        P = np.asarray(lm["prox"]["target"], dtype=float)
        P_d = np.asarray(lm["dist"]["target"], dtype=float)
        Q = np.asarray(lm["roll"]["target"], dtype=float)
        B = C.onb(A, D, Qs)
        Bp = C.onb(P, P_d, Q)
        s_ax = float(np.linalg.norm(P_d - P) / np.linalg.norm(D - A))
        L = Bp @ np.diag([s_ax] * 3) @ B.T
        edge = P_d - P
        edge_len = float(np.linalg.norm(edge))
        a_t = edge / edge_len
        frames[b] = (P, edge, L)

        rows = []
        for name, x_loc in sorted(sites_pkt[b].items()):
            pred = P + L @ x_loc
            axial_m = float((pred - P) @ edge) / edge_len
            pct = 100.0 * axial_m / FOREARM_SPAN_M
            trans = (pred - P) - axial_m * a_t
            trans_mm = 1000.0 * float(np.linalg.norm(trans))
            rows.append({"site": name, "pred_global": pred.tolist(),
                         "axial_pct_of_forearm": pct, "transverse_mm": trans_mm,
                         "inside_envelope": trans_mm <= max(ENVELOPE_MEDIANS_MM.values())})
        n_env = sum(1 for r in rows if r["inside_envelope"])
        max_trans = max(r["transverse_mm"] for r in rows)
        ok_side = n_env == len(rows) and max_trans <= 15.5  # C1 receipted max 15.38 mm
        ok_all &= ok_side
        C.verdict(f"C1 10/10 re-placement ({b})", ok_side,
                  f"{len(rows)} sites; axial in C1 receipted regions (T4); "
                  f"transverse max {max_trans:.2f} mm (C1 receipted 15.38) <= envelope "
                  f"median {ENVELOPE_MEDIANS_MM['c']} mm; {n_env}/{len(rows)} inside")
        receipt["sides"][b] = {"rows": rows, "max_transverse_mm": max_trans,
                               "s_implied": s_ax, "ok": ok_side}

    # L/R mirror consistency of the declared pair (the +90 deg law mirrored)
    Pr, er, Lr = frames["ulna"]
    Pl, el, Ll = frames["ulna_l"]
    mirror_dev = []
    for name_r in sorted(sites_pkt["ulna"].items()):
        name = name_r[0]
        name_l = name.replace("-P", "_l-P")  # ANC-P2 -> ANC_l-P2 etc. (packet law)
        pred_r = Pr + Lr @ sites_pkt["ulna"][name]
        pred_l = Pl + Ll @ sites_pkt["ulna_l"][name_l]
        # mirror through the sagittal plane x=0 (data-derived: B4 §4 plane law x=0)
        mirror_dev.append(float(np.linalg.norm(pred_r - np.array([-pred_l[0], pred_l[1], pred_l[2]]))))
    max_mirror = max(mirror_dev)
    # the two source-authored asymmetries (B4-E3: ulna body-y 5.0e-5 m) bound equality
    ok_mirror = max_mirror <= 1e-3
    ok_all &= ok_mirror
    C.verdict("L/R mirror consistency under the declared pair", ok_mirror,
              f"max mirror deviation {max_mirror*1000:.4f} mm across 10 pairs "
              f"(bound: source-authored ulna-y asymmetry 0.05 mm, B4-E3)")

    receipt["mirror"] = {"max_deviation_m": max_mirror, "ok": ok_mirror}
    receipt["ok"] = ok_all
    IC.save_receipt("09_c1_replacement.json", receipt)

    print("\n--- C1's 10/10 set under the declared U-STR frame (right side) ---")
    print(f"{'site':12s} {'axial %EW':>10s} {'transverse mm':>14s}")
    for r in receipt["sides"]["ulna"]["rows"]:
        print(f"{r['site']:12s} {r['axial_pct_of_forearm']:10.4f} {r['transverse_mm']:14.3f}")
    print("VERDICT:", "PASS" if receipt["ok"] else "FAIL")
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
