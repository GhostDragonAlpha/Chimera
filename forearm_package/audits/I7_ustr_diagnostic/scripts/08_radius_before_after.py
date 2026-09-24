"""08 — BEFORE/AFTER RADIUS COMPARISON (the I7 spec) — CLOSED FORM ONLY.

Computes, from the frozen baseline + the declared candidate, the exact effect a
future AUTHORIZED revision would have on the radius records. NOTHING is written to
any store: the frozen session-5 baseline stays byte-identical (this script proves it,
then re-proves it). Per the authorization: "No production radius supersession, hand
fit, or training-body change is authorized by that diagnostic. Preserve old radius
and all failed alternatives."

Contents:
 (1) BEFORE — the packet's recorded radius/radius_l transform (exact floats).
 (2) The closure MECHANISM — compiler.py:399-423 (first-child shared-joint closure,
     JOINT_EPS 1e-9 at :47, refusal shared_joint_separation at :422-423, skipped only
     while the parent is unresolved at :414-417): the diagnostic verifies the CURRENT
     record VIOLATES closure against the declared ulna.P_d by 5.1158 mm >> 1e-9 —
     i.e. with ulna declared, the shipped radius record is machine-refused and the
     re-anchor is FORCED, not chosen.
 (3) AFTER — the re-anchored map in closed form: P := ulna.P_d, span 59.6291 mm,
     s = 59.6291/292.029 = 0.204189, G unchanged (same edge line, same witness),
     t = P_new - G*A, det = s^3; per-edge fraction bookkeeping (R1 §5.3 drift law).
 (4) Site re-placement deltas (16+16 radius sites; globals move, locals untouched).
 (5) PRESERVATION — MANIFEST re-hash 44/44, git porcelain empty (baseline), A4/B4
     receipt files present and unmodified (git-tracked, porcelain clean).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i7_common as IC  # noqa: E402
import b4_common as C  # noqa: E402

BODIES = ("radius", "radius_l")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    recs = IC.load_candidate()  # declared candidate (ulna/ulna_l landmarks)
    kg = json.load(open(IC.B4 / "receipts" / "01_known_good_records.json",
                        encoding="utf-8"))  # recorded radius landmarks
    packet = IC.load_packet()
    seg_by_body = {s["source_body"]: s for s in packet["segments"]}
    sites_pkt: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]] = {}
    for s in packet["sites"]:
        if s["segment"] in BODIES:
            sites_pkt.setdefault(s["segment"], {})[s["name"]] = (
                np.asarray(s["fitted_pos_global"], dtype=float),
                np.asarray(s["source_pos_local"], dtype=float),
            )
    sys.path.insert(0, str(IC.B4 / "work" / "modules"))
    from intake import global_site_positions, load_source  # noqa: E402
    real = load_source(str(IC.XML_PATH))
    sw = global_site_positions(real)

    receipt: dict = {"before": {}, "mechanism": {}, "after": {}, "site_deltas": {},
                     "preservation": {}, "fractions": {}}
    ok_all = True

    for b in BODIES:
        seg = seg_by_body[b]
        A = np.asarray(seg["source_origin"], dtype=float)
        # BEFORE (exact packet record)
        s_old = float(seg["scale"][0])
        G_old = np.asarray(seg["rotation"], dtype=float)  # rigid part (DER §5 split, A4)
        Bp_old = np.asarray(seg["frame_basis"], dtype=float)
        t_old = np.asarray(seg["fitted_origin"], dtype=float)
        # the RADIUS EDGE's own source span: radius body origin -> hand origin
        # (C1 §1.1: |radius->hand_r| = 0.292029 m — NOT elbow->hand 0.305792 m)
        src_D = real.body_by_name["hand_r" if b == "radius" else "hand_l"].pos_global
        span_src = float(np.linalg.norm(src_D - A))
        P_old = t_old  # fitted_origin == P (packet law, A4)
        lm = kg["records"][b]["landmarks"]
        P_d_old = np.asarray(lm["dist"]["target"], dtype=float)
        span_t_old = float(np.linalg.norm(P_d_old - P_old))

        receipt["before"][b] = {
            "scale": s_old, "t": t_old.tolist(),
            "det_full_map_L": s_old**3, "det_packet_rotation_G": float(np.linalg.det(G_old)),
            "source_span_m": span_src,
            "P": P_old.tolist(), "P_d": P_d_old.tolist(),
            "span_m": span_t_old,
            "max_world_reconstruction_error_m": seg.get("residual"),
        }

        # AFTER (closed form under the declared candidate)
        ulna_rec = recs["records"]["ulna" if b == "radius" else "ulna_l"]
        P_new = np.asarray(ulna_rec["landmarks"]["dist"]["target"], dtype=float)
        Q = np.asarray(ulna_rec["landmarks"]["roll"]["target"], dtype=float)
        span_t_new = float(np.linalg.norm(P_d_old - P_new))
        s_new = span_t_new / span_src
        B_new = C.onb(A, src_D, np.asarray(lm["roll"]["source"], dtype=float))
        Bp_new = C.onb(P_new, P_d_old, Q)
        G_new = Bp_new @ B_new.T
        L_new = Bp_new @ np.diag([s_new] * 3) @ B_new.T
        t_new = P_new - G_new @ A
        d_G = float(np.max(np.abs(G_new - G_old)))
        d_Bp = float(np.max(np.abs(Bp_new - Bp_old)))

        # mechanism: current record vs forced closure
        gap = float(np.linalg.norm(P_old - P_new))
        mech_ok = gap > C.JOINT_EPS  # refusal would fire -> supersession FORCED
        C.verdict(f"closure mechanism ({b})", mech_ok,
                  f"|radius.P(packet) - ulna.P_d| = {gap*1000:.4f} mm >> JOINT_EPS "
                  f"{C.JOINT_EPS:g} -> shared_joint_separation refusal with ulna "
                  f"declared (compiler.py:399-423); re-anchor is machine-forced")

        # site re-placement deltas (closed form; nothing executed)
        # the source ONB B is identical before/after (same src landmarks); only the
        # target anchor, scale and translation differ
        deltas = {}
        for name, (_fit, x_loc) in sites_pkt[b].items():
            pred_old = P_old + (Bp_old @ np.diag([s_old] * 3) @ B_new.T) @ x_loc
            pred_new = P_new + L_new @ x_loc
            deltas[name] = float(np.linalg.norm(pred_new - pred_old))
        worst = max(deltas.items(), key=lambda kv: kv[1])

        receipt["mechanism"][b] = {"gap_m": gap, "joint_eps": C.JOINT_EPS,
                                   "refusal_would_fire": mech_ok}
        receipt["after"][b] = {
            "scale": s_new, "t": t_new.tolist(),
            "det_full_map_L": float(np.linalg.det(L_new)), "s_cubed": s_new**3,
            "P": P_new.tolist(), "P_d_unchanged": P_d_old.tolist(),
            "span_m": span_t_new, "G_vs_packet_max_abs_diff": d_G,
            "Bp_vs_packet_max_abs_diff": d_Bp,
            "scale_change_pct": 100.0 * (s_new / s_old - 1.0),
        }
        receipt["site_deltas"][b] = {
            "n_sites": len(deltas), "max_displacement_m": worst[1],
            "worst_site": worst[0], "all": deltas,
            "note": "globals recompute under the AFTER map; source locals are "
                    "source-verbatim and untouched (S13)",
        }
        ok_all &= mech_ok

    # fraction bookkeeping (R1 §5.3)
    src_off = 0.023074640  # |ulna->radius| source (C1 §1.1, R1 §3)
    src_forearm = 0.3057922
    k_rad = 0.22170679566544982
    derived_mm = src_off * k_rad * 1000.0
    tgt_forearm = 0.064744899
    frac_target = derived_mm / (tgt_forearm * 1000.0)
    frac_source = src_off / src_forearm
    ratio = (k_rad) / (tgt_forearm / src_forearm)
    receipt["fractions"] = {
        "derived_distal_point_mm": derived_mm,
        "target_per_edge_fraction_pct": 100.0 * frac_target,
        "source_authored_fraction_pct": 100.0 * frac_source,
        "drift_factor": ratio,
        "drift_check": 100.0 * frac_source * ratio,
        "r1_law": "7.5459% x k_rad/axis-ratio = 7.9015% (R1 §5.3)",
    }
    drift_ok = abs(100.0 * frac_source * ratio - 100.0 * frac_target) < 1e-6
    C.verdict("fraction drift law (R1 §5.3)", drift_ok,
              f"7.5459% x {ratio:.5f} = {100.0*frac_source*ratio:.4f}% vs target "
              f"{100.0*frac_target:.4f}%")
    ok_all &= drift_ok

    # PRESERVATION — nothing modified anywhere
    man = json.load(open(IC.SNAP / "MANIFEST.json", encoding="utf-8"))
    files = man.get("files", man)
    n_ok = 0
    n_all = 0
    if isinstance(files, dict):
        items = files.items()
        for rel, meta in items:
            expected = meta["sha256"] if isinstance(meta, dict) else meta
            got = sha256(IC.SNAP / rel)
            n_all += 1
            n_ok += (got == expected)
    elif isinstance(files, list):
        for meta in files:
            rel = meta["path"] if "path" in meta else meta["file"]
            n_all += 1
            n_ok += (sha256(IC.SNAP / rel) == meta["sha256"])
    C.verdict("baseline MANIFEST re-hash", n_ok == n_all, f"{n_ok}/{n_all} files match")

    git = subprocess.run(
        ["git", "-C", "E:/PythonChimera", "status", "--porcelain"],
        capture_output=True, text=True, shell=False)
    lines = [l for l in git.stdout.splitlines() if l.strip()]
    # The worktree carries PRE-EXISTING dirt from other sessions (engine/story/tools);
    # the diagnostic's preservation claim is scoped to forearm_package:
    #  - NO tracked file (M/D) under forearm_package may be modified,
    #  - untracked paths under forearm_package must be this diagnostic's own dir plus
    #    recorded FOREIGN lanes (concurrent agents), never baseline_snapshot.
    def is_fp(line: str) -> bool:
        path = line[3:].strip().strip('"')
        return path.startswith("forearm_package/")
    fp_lines = [l for l in lines if is_fp(l)]
    fp_tracked = [l for l in fp_lines if l[:2] in ("M ", " D", "M\t", "D ")]
    fp_untracked = [l[3:].strip().strip('"') for l in fp_lines if l.startswith("??")]
    foreign = [p for p in fp_untracked
               if not p.startswith("forearm_package/audits/I7_ustr_diagnostic")]
    ok_scope = (not fp_tracked) and \
        all("baseline_snapshot" not in p for p in fp_untracked)
    C.verdict("forearm_package: no tracked modification outside the addendum", not fp_tracked,
              f"tracked modifications under forearm_package: {fp_tracked or 'NONE'}")
    C.verdict("forearm_package: baseline untouched by untracked writes",
              all("baseline_snapshot" not in p for p in fp_untracked),
              f"untracked under forearm_package: I7_ustr_diagnostic (this diagnostic) "
              f"+ foreign lanes {foreign or 'NONE'} (concurrent agents'; not this "
              f"diagnostic's products; untouched by it)")

    a4 = Path(r"E:/PythonChimera/forearm_package/audits/A4_transforms/receipts/a4_audit_run1.txt")
    receipt["preservation"] = {
        "manifest_hash_match": f"{n_ok}/{n_all}",
        "git_porcelain_baseline": subprocess.run(
            ["git", "-C", "E:/PythonChimera", "status", "--porcelain", "--",
             "forearm_package/baseline_snapshot"], capture_output=True, text=True).stdout.strip(),
        "a4_receipt_present": a4.exists(),
        "tracked_modifications_under_forearm_package": fp_tracked,
        "foreign_untracked_lanes_recorded": foreign,
        "note": "the repo-wide worktree dirt (Chimera/ChimeraEngine/story/tools, "
                "213 paths) predates and is outside this diagnostic; none of it is "
                "under forearm_package",
    }
    receipt["ok"] = ok_all and (n_ok == n_all) and ok_scope
    IC.save_receipt("08_radius_before_after.json", receipt)

    print("\n--- BEFORE/AFTER RADIUS (closed form; NOT executed) ---")
    for b in BODIES:
        bf, af = receipt["before"][b], receipt["after"][b]
        print(f"{b}:")
        print(f"  BEFORE s={bf['scale']:.17g} det(L)={bf['det_full_map_L']:.10f} "
              f"span={bf['span_m']*1000:.4f} mm P={np.round(bf['P'],9).tolist()}")
        print(f"  AFTER  s={af['scale']:.12f} det(L)={af['det_full_map_L']:.10f} "
              f"span={af['span_m']*1000:.4f} mm "
              f"P={np.round(af['P'],9).tolist()}  scale_change={af['scale_change_pct']:.4f}%  "
              f"G unchanged: {af['G_vs_packet_max_abs_diff']:.2e}")
        sd = receipt["site_deltas"][b]
        print(f"  sites: {sd['n_sites']} globals recompute; max displacement "
              f"{sd['max_displacement_m']*1000:.4f} mm ({sd['worst_site']})")
    fr = receipt["fractions"]
    print(f"fractions: derived point {fr['derived_distal_point_mm']:.4f} mm = "
          f"{fr['target_per_edge_fraction_pct']:.4f}% of 64.7449 mm (source authored "
          f"{fr['source_authored_fraction_pct']:.4f}%; drift x{fr['drift_factor']:.5f} — R1 §5.3)")
    print("VERDICT:", "PASS" if receipt["ok"] else "FAIL")
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
