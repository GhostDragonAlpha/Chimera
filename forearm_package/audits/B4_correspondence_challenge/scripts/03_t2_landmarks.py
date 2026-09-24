"""03 — T2 LANDMARK-SUFFICIENCY against the known-good (radius + radius_l).

Checks (challenge_protocol.md T2):
 - source bone length > 1e-12 (degenerate floor);
 - target pair distinct: ||P_d - P|| > 1e-12 m;
 - roll witness: ||t|| > ROLL_EPS = 1e-9 (m), t = rejection of (Q - P) off the axis;
 - scale policy consistent: uniform -> no width landmarks needed; aspect -> declared.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402

BODIES = ("radius", "radius_l")


def main() -> int:
    recs = json.load(open(C.RECEIPTS / "01_known_good_records.json", encoding="utf-8"))
    packet = C.load_packet()
    seg_by_body = {s["source_body"]: s for s in packet["segments"]}

    receipt = {"checks": []}
    for b in BODIES:
        lm = recs["records"][b]["landmarks"]
        A = np.asarray(lm["prox"]["source"], dtype=float)
        D = np.asarray(lm["dist"]["source"], dtype=float)
        P = np.asarray(lm["prox"]["target"], dtype=float)
        P_d = np.asarray(lm["dist"]["target"], dtype=float)
        Q = np.asarray(lm["roll"]["target"], dtype=float)

        src_len = float(np.linalg.norm(D - A))
        tgt_len = float(np.linalg.norm(P_d - P))
        a = (P_d - P) / tgt_len
        t = (Q - P) - a * (a @ (Q - P))
        tnorm = float(np.linalg.norm(t))

        ok_src = src_len > C.DEGENERATE_FLOOR
        ok_tgt = tgt_len > C.DEGENERATE_FLOOR
        ok_roll = tnorm > C.ROLL_EPS
        policy = recs["records"][b]["scale_policy"]
        ok_policy = policy == "uniform"  # known-good: uniform (no width landmarks owed)

        ok = ok_src and ok_tgt and ok_roll and ok_policy
        C.verdict(f"T2 landmark sufficiency ({b})", ok,
                  f"|src_D-src_A|={src_len:.6f} m  |P_d-P|={tgt_len:.6f} m  "
                  f"|t_roll|={tnorm:.6f} m (> {C.ROLL_EPS:g})  policy={policy}")
        receipt["checks"].append({
            "check": f"T2 {b}", "ok": ok,
            "source_bone_len_m": src_len, "target_pair_len_m": tgt_len,
            "roll_t_norm_m": tnorm, "roll_eps": C.ROLL_EPS,
            "scale_policy": policy,
            "packet_scale": seg_by_body[b]["scale"],
        })

    receipt["ok"] = all(c["ok"] for c in receipt["checks"])
    C.save_receipt("03_t2_landmarks.json", receipt)
    print("T2 VERDICT:", "PASS" if receipt["ok"] else "FAIL")
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
