"""02 — T2 LANDMARK-SUFFICIENCY for the declared U-STR candidate (ulna + ulna_l).

Adapted invocation of the B4 T2 machinery (B4 scripts/03_t2_landmarks.py); procedure
and floors UNCHANGED:
 - source bone length > 1e-12 (degenerate floor);
 - target pair distinct: ||P_d - P|| > 1e-12 m;
 - roll witness: ||t|| > ROLL_EPS = 1e-9 (m) on BOTH sides of the declaration
   (source witness: rejection of the source roll site off the source axis;
    target witness: rejection of the declared Q off the declared edge);
 - scale policy consistent: uniform -> no width landmarks owed;
 - every declared landmark id resolves to a finite 3-vector.
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

    receipt = {"checks": []}
    ok_all = True
    for b in BODIES:
        lm = recs["records"][b]["landmarks"]
        A = np.asarray(lm["prox"]["source"], dtype=float)
        D = np.asarray(lm["dist"]["source"], dtype=float)
        Qs = np.asarray(lm["roll"]["source"], dtype=float)
        P = np.asarray(lm["prox"]["target"], dtype=float)
        P_d = np.asarray(lm["dist"]["target"], dtype=float)
        Q = np.asarray(lm["roll"]["target"], dtype=float)

        finite_ok = all(np.isfinite(x).all() for x in (A, D, Qs, P, P_d, Q))
        src_len = float(np.linalg.norm(D - A))
        tgt_len = float(np.linalg.norm(P_d - P))

        a_s = (D - A) / src_len
        t_src = (Qs - A) - a_s * (a_s @ (Qs - A))
        tnorm_src = float(np.linalg.norm(t_src))
        a_t = (P_d - P) / tgt_len
        t_tgt = (Q - P) - a_t * (a_t @ (Q - P))
        tnorm_tgt = float(np.linalg.norm(t_tgt))

        ok_src = src_len > C.DEGENERATE_FLOOR
        ok_tgt = tgt_len > C.DEGENERATE_FLOOR
        ok_roll = tnorm_src > C.ROLL_EPS and tnorm_tgt > C.ROLL_EPS
        policy = recs["records"][b]["scale_policy"]
        ok_policy = policy == "uniform"  # declared uniform: no width landmarks owed

        ok = ok_src and ok_tgt and ok_roll and ok_policy and finite_ok
        ok_all &= ok
        C.verdict(f"T2 landmark sufficiency ({b})", ok,
                  f"|src_D-src_A|={src_len:.6f} m  |P_d-P|={tgt_len:.6f} m  "
                  f"|t_roll| src={tnorm_src:.6f} m tgt={tnorm_tgt:.6f} m "
                  f"(> eps {C.ROLL_EPS:g})  policy={policy}  finite={finite_ok}")
        receipt["checks"].append({
            "check": f"T2 {b}", "ok": ok,
            "source_bone_len_m": src_len, "target_pair_len_m": tgt_len,
            "roll_t_norm_source_m": tnorm_src, "roll_t_norm_target_m": tnorm_tgt,
            "roll_eps": C.ROLL_EPS, "scale_policy": policy, "finite_landmarks": finite_ok,
        })

    receipt["ok"] = ok_all
    IC.save_receipt("02_t2_landmarks.json", receipt)
    print("T2 VERDICT:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
