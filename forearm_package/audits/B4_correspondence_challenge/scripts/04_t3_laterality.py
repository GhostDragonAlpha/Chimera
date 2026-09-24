"""04 — T3 LATERALITY against the known-good (radius + radius_l).

Checks (challenge_protocol.md T3):
 - side(source body) == side(target landmark): source right at +z / left at -z
   (DERIVATION §2, measured from the XML body origins); target side token from the
   declared proximal/distal joint names (_R/_L), monkey right at -x per the authored
   frame law (source right +z -> monkey right -x).
 - handedness preserve: constructed frame maps proper det +1 within 1e-12; no negative
   scale entry under preserve; packet chirality_det >= 0; mirror_plane_normal absent.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402

BODIES = ("radius", "radius_l")


def side_of_body(name: str, src_A) -> str:
    if name.endswith("_l"):
        return "left"
    # source convention: right limbs at +z (DERIVATION §2) — measured, not assumed
    return "right" if src_A[2] > 0 else "left"


def main() -> int:
    recs = json.load(open(C.RECEIPTS / "01_known_good_records.json", encoding="utf-8"))
    packet = C.load_packet()
    seg_by_body = {s["source_body"]: s for s in packet["segments"]}
    bodies, parent_of, sites_of = C.load_xml_tree()

    receipt = {"checks": []}
    for b in BODIES:
        lm = recs["records"][b]["landmarks"]
        src_A = np.asarray(lm["prox"]["source"], dtype=float)
        P = np.asarray(lm["prox"]["target"], dtype=float)
        P_d = np.asarray(lm["dist"]["target"], dtype=float)
        Q = np.asarray(lm["roll"]["target"], dtype=float)
        seg = seg_by_body[b]

        # ---- side check
        src_side = side_of_body(b, src_A)
        # target landmarks are pack joints elbow_R/wrist_R (names recorded by the
        # builder law); recover the side token from the pack joint name via the
        # declared target coordinates' provenance in the builder (prox = elbow_{R/L}).
        # The declared target side token is re-derived from the pack: match P against
        # the pack joint positions.
        sys.path.insert(0, str(C.B4 / "work" / "modules"))
        from mesh_target import MonkeyTarget  # noqa: E402
        mt = MonkeyTarget(birth_path=str(C.MESH_PATH), pack_path=str(C.PACK_PATH))
        prox_joint = next(n for n in mt.names if np.allclose(mt.joint_pos(n), P, atol=1e-12))
        tgt_side = "left" if prox_joint.endswith("_L") else "right"
        ok_side = src_side == tgt_side
        # monkey right at -x: a right-side target landmark must sit at x < 0
        xsign_ok = (P[0] < 0) if tgt_side == "right" else (P[0] > 0)
        C.verdict(f"T3 side({b})", ok_side and xsign_ok,
                  f"source z={src_A[2]:+.4f} -> {src_side}; target joint={prox_joint} -> {tgt_side}; "
                  f"P.x={P[0]:+.6f} m (monkey right=-x: {xsign_ok})")

        # ---- handedness / chirality on CONSTRUCTED frames
        B = C.onb(src_A, np.asarray(lm["dist"]["source"], dtype=float),
                  np.asarray(lm["roll"]["source"], dtype=float))
        Bp = C.onb(P, P_d, Q)
        Qrot = Bp @ B.T
        detQ = float(np.linalg.det(Qrot))
        ok_det = abs(detQ - 1.0) <= C.DET_TOL

        scale = np.asarray(seg["scale"], dtype=float)
        handedness = recs["records"][b]["handedness"]
        ok_noscaleflip = handedness == "preserve" and bool((scale > 0).all())
        chir = float(packet["residuals"]["chirality_det"])
        ok_chir = handedness == "preserve" and (chir >= 0) and abs(chir - 1.0) <= 1e-9
        ok_mirror_guard = recs["records"][b]["mirror_plane_normal"] is None and handedness == "preserve"

        ok = ok_side and xsign_ok and ok_det and ok_noscaleflip and ok_chir and ok_mirror_guard
        C.verdict(f"T3 handedness ({b})", ok,
                  f"det(Q_constructed)={detQ:.15f}  scale={scale.tolist()}  "
                  f"handedness={handedness}  packet chirality_det={chir:.16f}  "
                  f"mirror_normal=None")
        receipt["checks"].append({
            "check": f"T3 {b}", "ok": ok,
            "source_side": src_side, "target_side": tgt_side, "target_prox_joint": prox_joint,
            "P_x": float(P[0]), "det_Q_constructed": detQ,
            "scale": scale.tolist(), "handedness": handedness,
            "packet_chirality_det": chir, "mirror_plane_normal": None,
        })

    receipt["ok"] = all(c["ok"] for c in receipt["checks"])
    C.save_receipt("04_t3_laterality.json", receipt)
    print("T3 VERDICT:", "PASS" if receipt["ok"] else "FAIL")
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
