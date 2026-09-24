"""A7 step 3 - verification of the RECORDED effects of the failed, unapplied
Candidate C (transverse placement candidate, session 5).

Boundaries honored:
  - the candidate is DEAD; its optimum is NOT re-run, re-fit, or extended;
  - the recorded per-side (db_m, dc_m) are taken verbatim from the record and
    only used to recompute the SAME quantities the record computed
    (experiment_transverse_fit.py lines 373-408), from the frozen baseline
    packet + the frozen target mesh;
  - the baseline packet is never written.

Verifications:
  V1 record census: 120 deltas, 42 comparable, all non-comparable null;
  V2 recorded max |path_length_delta_m| == 0.90 mm at BRD (report 05 section 4-C);
  V3 top-10 table by |delta| (recorded);
  V4 independence: every comparable tendon with NO site among the 32 must carry
     delta exactly 0.0 (the candidate only moves the 32 forearm sites);
  V5 recomputation: rebuild candidate chains = baseline points + db*bu + dc*cu
     (frames rebuilt deterministically from the target mesh exactly as
     experiment_transverse_fit._side_frames does: joint_pos elbow/wrist +
     _band_roll + onb_from_points) and compare each recomputed delta to the
     recorded value.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(WORK))

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\A7_paths\receipts")

FIT = json.loads((BASE / "runs" / "actual_monkey_fit.json").read_text(encoding="utf-8"))
CAND = json.loads((BASE / "runs" / "attachment_candidates.json").read_text(encoding="utf-8"))
EXP = json.loads((BASE / "runs" / "experiment_transverse_candidate.json").read_text(encoding="utf-8"))


def pl(pts: list[list[float]]) -> float:
    """DERIVATION.md section 7 / compiler._pl, same summation order."""
    total = 0.0
    for i in range(len(pts) - 1):
        d = np.asarray(pts[i + 1], dtype=np.float64) - np.asarray(pts[i], dtype=np.float64)
        total += float(np.linalg.norm(d))
    return total


def main() -> None:
    from mesh_target import MonkeyTarget

    # target geometry: READ-ONLY loads from the snapshot's byte-identical copies
    mt = MonkeyTarget(
        birth_path=str(BASE / "inputs" / "monkey_birth.bin"),
        pack_path=str(BASE / "inputs" / "monkey_joints.bin"),
    )

    # side frames, exactly as experiment_transverse_fit._side_frames (lines 137-143):
    # q = _band_roll(mt, prox, P, P_d - P)  (actual_target_fit.py lines 89-97)
    # _, bu, cu = onb_from_points(P, P_d, q) (compiler.py lines 58-68)
    def _unit(v):
        n = np.linalg.norm(v)
        if n < 1e-15:
            raise ValueError("degenerate vector")
        return v / n

    def _band_roll(prox: str, P: np.ndarray, a: np.ndarray) -> np.ndarray:
        verts = mt.band_verts(prox)
        if len(verts) == 0:
            raise RuntimeError(f"joint {prox} has no vertices")
        rel = verts - P
        perp = rel - np.outer(rel @ a, a)
        d2 = (perp ** 2).sum(axis=1)
        return verts[int(np.argmax(d2))].copy()

    def onb_from_points(p0, p1, q):
        a = _unit(p1 - p0)
        t = (q - p0) - a * (a @ (q - p0))
        if np.linalg.norm(t) < 1e-9:
            raise RuntimeError("roll reference lies on the bone axis")
        b = _unit(t)
        c = np.cross(a, b)
        if abs(np.linalg.det(np.column_stack([a, b, c])) - 1.0) > 1e-9:
            raise RuntimeError("ONB not proper")
        return a, b, c

    frames = {}
    for body, (pj, wj) in (("radius", ("elbow_R", "wrist_R")), ("radius_l", ("elbow_L", "wrist_L"))):
        P = mt.joint_pos(pj)
        P_d = mt.joint_pos(wj)
        q = _band_roll(pj, P, P_d - P)
        _a, bu, cu = onb_from_points(P, P_d, q)
        frames[body] = {"a": (P_d - P) / np.linalg.norm(P_d - P), "bu": bu, "cu": cu}

    # the 32 movable sites and their side
    site_side: dict[str, str] = {}
    for body in ("radius", "radius_l"):
        for rec in CAND["bodies"][body]["candidates"]:
            site_side[rec["site_id"]] = body

    td = EXP["tendon_deltas"]
    # ---- V1 record census ------------------------------------------------------
    n_total = len(td)
    comp = {k: v for k, v in td.items() if v["comparable"]}
    non_null_violations = [k for k, v in td.items() if not v["comparable"] and v["path_length_delta_m"] is not None]
    null_violations = [k for k, v in td.items() if v["comparable"] and v["path_length_delta_m"] is None]

    # ---- V2 recorded max -------------------------------------------------------
    rec_max = max(comp.items(), key=lambda kv: abs(kv[1]["path_length_delta_m"]))
    rec_max_abs_mm = abs(rec_max[1]["path_length_delta_m"]) * 1000.0

    # ---- V3 top-10 recorded ----------------------------------------------------
    top10 = sorted(comp.items(), key=lambda kv: -abs(kv[1]["path_length_delta_m"]))[:10]

    # ---- V4 untouched-tendon deltas must be exactly 0 --------------------------
    touching = set()
    for t in FIT["tendons"]:
        if any(s in site_side for s in t["sites"]):
            touching.add(t["name"])
    untouched_nonzero = sorted(
        k for k, v in comp.items() if k not in touching and v["path_length_delta_m"] != 0.0
    )

    # ---- V5 recomputation of the same quantities -------------------------------
    sites_by_name = {s["name"]: s for s in FIT["sites"]}
    recomputed = {}
    worst = 0.0
    worst_name = None
    for t in FIT["tendons"]:
        rec = td.get(t["name"])
        if rec is None:
            raise RuntimeError(f"tendon {t['name']} missing from record")
        if not rec["comparable"]:
            continue
        base_pts, cand_pts = [], []
        ok = True
        for sn in t["sites"]:
            w = sites_by_name[sn]["fitted_pos_global"]
            if w is None:
                ok = False
                break
            w = np.asarray(w, dtype=np.float64)
            base_pts.append(w)
            body = site_side.get(sn)
            if body is not None:
                cd = EXP["step_C_candidate"][body]
                fr = frames[body]
                w = w + cd["db_m"] * fr["bu"] + cd["dc_m"] * fr["cu"]
            cand_pts.append(w)
        if not ok:
            continue
        d = round(pl(cand_pts) - pl(base_pts), 9)
        recomputed[t["name"]] = d
        diff = abs(d - rec["path_length_delta_m"])
        if diff > worst:
            worst, worst_name = diff, t["name"]

    my_max = max(recomputed.items(), key=lambda kv: abs(kv[1]))
    # recorded moment-arm deltas (session-5 claim: ~0, 1e-12 rounding floor)
    arm_vals = [v["moment_arm_max_abs_delta_m"] for v in comp.values()]
    arm_max = max((a for a in arm_vals if a is not None), default=None)
    arm_null = sum(1 for a in arm_vals if a is None)

    receipt = {
        "boundary": "candidate optimum NOT re-run; recorded (db_m, dc_m) used as-is to recompute the recorded quantities",
        "V1_census": {
            "n_deltas_record": n_total,
            "n_comparable_record": len(comp),
            "non_comparable_with_non_null_delta": non_null_violations,
            "comparable_with_null_delta": null_violations,
        },
        "V2_recorded_max": {
            "tendon": rec_max[0],
            "path_length_delta_m": rec_max[1]["path_length_delta_m"],
            "abs_mm": rec_max_abs_mm,
            "claim_report05_4C": "max |delta path length| = 0.90 mm (BRD)",
        },
        "V3_top10_recorded": [
            {"tendon": k, "delta_m": v["path_length_delta_m"], "abs_mm": abs(v["path_length_delta_m"]) * 1000.0}
            for k, v in top10
        ],
        "V4_untouched_nonzero": untouched_nonzero,
        "V5_recompute": {
            "n_recomputed": len(recomputed),
            "max_abs_diff_vs_record_m": worst,
            "worst_tendon": worst_name,
            "my_max_tendon": my_max[0],
            "my_max_abs_mm": abs(my_max[1]) * 1000.0,
        },
        "moment_arm_recorded": {"max_abs_delta_m": arm_max, "n_null": arm_null},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step3_candidate_effects_receipt.json").write_text(
        json.dumps(receipt, indent=1, default=float), encoding="utf-8"
    )
    print(json.dumps(receipt, indent=1, default=float))


if __name__ == "__main__":
    main()
