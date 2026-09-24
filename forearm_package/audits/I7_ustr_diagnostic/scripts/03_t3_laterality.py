"""03 — T3 LATERALITY for the declared U-STR candidate (ulna + ulna_l).

Adapted invocation of the B4 T3 machinery (B4 scripts/04_t3_laterality.py); procedure
and tolerances UNCHANGED:
 - side(source body) == side(target landmark): global source z > 0 -> right
   (unmarked names are right per the suffix law), target joint token _R/_L with
   monkey right at -x (the authored frame law);
 - handedness preserve: constructed frame maps proper, det(Q) = +1 within 1e-12;
   declared uniform positive scale (no negative entry = no mirror semantics);
   mirror_plane_normal absent.
 ADAPTATION (declared): the packet `chirality_det` leg of the known-good run records
 the RECORDED fit's chirality; the candidate has no recorded fit — ulna is
 anchor-only in the packet, and that absence is the candidate's premise. The gate leg
 is the CONSTRUCTED det(Q), which the known-good run also asserted (same 1e-12
 tolerance). The packet's global chirality_det is recorded as context only.
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
    recs = IC.load_candidate()
    packet = IC.load_packet()
    sys.path.insert(0, str(IC.B4 / "work" / "modules"))
    from mesh_target import MonkeyTarget  # noqa: E402
    mt = MonkeyTarget(birth_path=str(IC.MESH_PATH), pack_path=str(IC.PACK_PATH))

    receipt = {"checks": [], "adaptation": "chirality gate leg = constructed det(Q) "
               "(1e-12); packet chirality_det recorded as context (no recorded fit "
               "exists for an anchor-only body)"}
    ok_all = True
    for b in BODIES:
        lm = recs["records"][b]["landmarks"]
        src_A = np.asarray(lm["prox"]["source"], dtype=float)
        src_D = np.asarray(lm["dist"]["source"], dtype=float)
        src_Q = np.asarray(lm["roll"]["source"], dtype=float)
        P = np.asarray(lm["prox"]["target"], dtype=float)
        P_d = np.asarray(lm["dist"]["target"], dtype=float)
        Q = np.asarray(lm["roll"]["target"], dtype=float)

        # ---- side check
        src_side = "left" if b.endswith("_l") else ("right" if src_A[2] > 0 else "left")
        prox_joint = next(n for n in mt.names if np.allclose(mt.joint_pos(n), P, atol=1e-12))
        tgt_side = "left" if prox_joint.endswith("_L") else "right"
        ok_side = src_side == tgt_side
        xsign_ok = (P[0] < 0) if tgt_side == "right" else (P[0] > 0)
        C.verdict(f"T3 side({b})", ok_side and xsign_ok,
                  f"source z={src_A[2]:+.4f} -> {src_side}; target joint={prox_joint} "
                  f"-> {tgt_side}; P.x={P[0]:+.6f} m (monkey right=-x: {xsign_ok})")

        # ---- handedness / chirality on CONSTRUCTED frames
        B = C.onb(src_A, src_D, src_Q)
        Bp = C.onb(P, P_d, Q)
        Qrot = Bp @ B.T
        detQ = float(np.linalg.det(Qrot))
        ok_det = abs(detQ - 1.0) <= C.DET_TOL

        s_ax = float(np.linalg.norm(P_d - P) / np.linalg.norm(src_D - src_A))
        scale = np.array([s_ax, s_ax, s_ax])
        handedness = recs["records"][b]["handedness"]
        ok_noscaleflip = handedness == "preserve" and bool((scale > 0).all())
        chir = float(packet["residuals"]["chirality_det"])  # context only
        ok_mirror_guard = recs["records"][b]["mirror_plane_normal"] is None and handedness == "preserve"

        ok = ok_side and xsign_ok and ok_det and ok_noscaleflip and ok_mirror_guard
        ok_all &= ok
        C.verdict(f"T3 handedness ({b})", ok,
                  f"det(Q_constructed)={detQ:.15f}  declared scale={scale.round(12).tolist()} "
                  f"handedness={handedness}  mirror_normal=None  "
                  f"(packet chirality_det={chir:.16f} — context, recorded fit)")
        receipt["checks"].append({
            "check": f"T3 {b}", "ok": ok,
            "source_side": src_side, "target_side": tgt_side, "target_prox_joint": prox_joint,
            "P_x": float(P[0]), "det_Q_constructed": detQ,
            "declared_scale": scale.tolist(), "handedness": handedness,
            "packet_chirality_det_context": chir, "mirror_plane_normal": None,
        })

    receipt["ok"] = ok_all
    IC.save_receipt("03_t3_laterality.json", receipt)
    print("T3 VERDICT:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
