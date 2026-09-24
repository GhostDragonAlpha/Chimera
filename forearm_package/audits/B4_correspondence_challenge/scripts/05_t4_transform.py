"""05 — T4 TRANSFORM-EXPLAINABILITY against the known-good (radius + radius_l).

Rebuilds L = B' diag(s) B^T from the DECLARED landmarks alone, with the same
construction the fit uses (DERIVATION 5.1), and compares against the packet:
 - rebuilt frame B' vs packet frame_basis (packet tier 1e-9);
 - rebuilt scale (axial evidence + authored uniform transverse, per declaration)
   vs packet scale (1e-9);
 - rebuilt rotation L vs packet rotation (1e-9);
 - landmark reconstruction x' = P + L(x - A) of the segment's own source sites vs the
   packet's recorded fitted_pos_global (1e-6 m step-A bound);
 - orthonormality of REBUILT frames <= 1e-12 (constructed tier);
 - det(Q) = +1 within 1e-12 after construction;
 - scale plausibility: within factor 2 of the ipsilateral proximal neighbor's axial
   evidence scale, and inside the packet aspect-policy magnitude band [0.2, 5.0].
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402

BODIES = ("radius", "radius_l")
NEIGHBOR = {"radius": "humerus", "radius_l": "humerus_l"}


def main() -> int:
    recs = json.load(open(C.RECEIPTS / "01_known_good_records.json", encoding="utf-8"))
    packet = C.load_packet()
    seg_by_body = {s["source_body"]: s for s in packet["segments"]}
    sites_pkt = {}
    for s in packet["sites"]:
        sites_pkt.setdefault(s["segment"], {})[s["name"]] = (
            np.asarray(s["fitted_pos_global"], dtype=float),
            np.asarray(s["source_pos_local"], dtype=float),
        )
    sys.path.insert(0, str(C.B4 / "work" / "modules"))
    from intake import global_site_positions, load_source  # noqa: E402
    real = load_source(str(C.XML_PATH))
    sw = global_site_positions(real)

    receipt = {"checks": []}
    ok_all = True
    for b in BODIES:
        lm = recs["records"][b]["landmarks"]
        A = np.asarray(lm["prox"]["source"], dtype=float)
        D = np.asarray(lm["dist"]["source"], dtype=float)
        Qs = np.asarray(lm["roll"]["source"], dtype=float)
        P = np.asarray(lm["prox"]["target"], dtype=float)
        P_d = np.asarray(lm["dist"]["target"], dtype=float)
        Qt = np.asarray(lm["roll"]["target"], dtype=float)
        seg = seg_by_body[b]

        B = C.onb(A, D, Qs)
        Bp = C.onb(P, P_d, Qt)

        # scale from DECLARED policy: axial evidence; b/c authored uniform = axial
        s_axial = float(np.linalg.norm(P_d - P) / np.linalg.norm(D - A))
        scale = np.array([s_axial, s_axial, s_axial])  # authored uniform transverse (declared)

        L = Bp @ np.diag(scale) @ B.T
        G = Bp @ B.T          # RIGID part — this is what the packet records as `rotation`
        Qrot = Bp @ B.T
        detQ = float(np.linalg.det(Qrot))
        detL = float(np.linalg.det(L))

        pkt_Bp = np.asarray(seg["frame_basis"], dtype=float)
        pkt_scale = np.asarray(seg["scale"], dtype=float)
        pkt_rot = np.asarray(seg["rotation"], dtype=float)

        d_Bp = float(np.max(np.abs(Bp - pkt_Bp)))
        d_scale = float(np.max(np.abs(scale - pkt_scale)))
        d_G = float(np.max(np.abs(G - pkt_rot)))
        ortho_B = float(np.max(np.abs(B.T @ B - np.eye(3))))
        ortho_Bp = float(np.max(np.abs(Bp.T @ Bp - np.eye(3))))

        # landmark reconstruction of the segment's own source sites (packet tier)
        rec_res = []
        for name, (fit_pos, src_loc) in sites_pkt[b].items():
            pred = P + L @ src_loc
            rec_res.append((name, float(np.linalg.norm(pred - fit_pos))))
        worst = max(rec_res, key=lambda x: x[1])

        # plausibility
        nb_scale = float(seg_by_body[NEIGHBOR[b]]["scale"][0])
        band_lo, band_hi = nb_scale / C.SCALE_BAND_FACTOR, nb_scale * C.SCALE_BAND_FACTOR
        in_band = band_lo <= s_axial <= band_hi
        ab = packet["meta"]["aspect_bounds"]
        in_policy = ab["min_magnitude"] <= float(np.max(scale)) <= ab["max_magnitude"]

        checks = {
            "frame_basis": d_Bp <= C.ORTHO_PACKET,
            "scale": d_scale <= 1e-9,
            "rigid_rotation_G": d_G <= C.ORTHO_PACKET,
            "ortho_constructed": max(ortho_B, ortho_Bp) <= C.ORTHO_CONSTRUCTED,
            "det_Q": abs(detQ - 1.0) <= C.DET_TOL,
            "det_L_is_s3": abs(detL - s_axial**3) <= 1e-12,
            "reconstruction_1e-6m": worst[1] <= C.RECON_TOL_M,
            "neighbor_band": in_band,
            "aspect_policy": in_policy,
        }
        ok = all(checks.values())
        ok_all &= ok
        C.verdict(f"T4 transform explainability ({b})", ok,
                  f"dBp={d_Bp:.2e} dScale={d_scale:.2e} dG={d_G:.2e} "
                  f"ortho={max(ortho_B, ortho_Bp):.2e} detQ={detQ:.15f} "
                  f"recon_worst={worst[0]}:{worst[1]:.2e} m ({len(rec_res)} sites) "
                  f"s={s_axial:.12f} vs nbr({NEIGHBOR[b]})={nb_scale:.6f} "
                  f"band=[{band_lo:.6f},{band_hi:.6f}]")
        receipt["checks"].append({
            "check": f"T4 {b}", "ok": ok, "subchecks": checks,
            "rebuilt_scale": scale.tolist(), "packet_scale": pkt_scale.tolist(),
            "max_abs_diff": {"frame_basis": d_Bp, "scale": d_scale,
                             "rigid_G_vs_packet_rotation": d_G},
            "orthonormality_constructed": max(ortho_B, ortho_Bp),
            "det_Q": detQ, "det_L": detL, "s_cubed": s_axial**3,
            "reconstruction_worst": {"site": worst[0], "err_m": worst[1],
                                     "n_sites": len(rec_res)},
            "plausibility": {"neighbor": NEIGHBOR[b], "neighbor_axial": nb_scale,
                             "band": [band_lo, band_hi], "in_band": in_band,
                             "aspect_policy": in_policy},
        })

    receipt["ok"] = ok_all
    C.save_receipt("05_t4_transform.json", receipt)
    print("T4 VERDICT:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
