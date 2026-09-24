"""00 — FREEZE THE CANDIDATE DECLARATION (preregistration BEFORE evaluation).

Declares the isolated U-STR candidate exactly as I6 defined it
(ANATOMICAL_DECISION_TABLE.md §1, U-STR column) WITH the now-resolved roll per O1's
witness law, in the SAME record schema the B4 gate consumed for the known-good
(B4 receipts/01_known_good_records.json). Writes receipts/00_candidate_declaration.json
and nothing else. No test runs in this script.

THE ROLL CHOICE IS A DERIVATION, NOT A TASTE PICK (Rule 1):
  given (a) the frozen candidate set {ECU-P2, ANC-P2, TRIlat-P5} (I6/C3 §2.5),
        (b) O1's frozen witness law  az_target(q) = az_source(s) + 90 deg (mod 360),
        (c) the only existing target-side roll machinery — the shipped `_band_roll`
            extreme vertex (the same witness the radius edge consumes; reused here as
            DECLARED-DEPENDENT evidence, C3 §2.5) with measured azimuth -111.8652 deg
            (O1 receipt o1_combine_sign.json),
  the law demands az_source(s) = -111.8652 - 90 = -201.8652 = +158.1348 deg, and the
  declared set contains exactly ONE candidate within the tube-line measurement
  precision (+/-10 deg, C3-S2): TRIlat-P5 (residual 0.1535 deg; nearest alternative
  ANC-P2 at 17.553 deg, ECU-P2 at 63.612 deg — O1 receipt, error_no_flip column).
  The residual SELECTS the declared pair; it is NOT independent validation (the
  roll-ref site is circular for its own roll DOF — C3 §2.5, O1's caveat). The SIGN
  (no-flip) is unanimous over all three candidates and rests on the independent
  site-split + target-olecranon evidence chain (O1 §2/§4), not on this residual.
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
from mesh_target import MonkeyTarget  # noqa: E402


def az_of(v: np.ndarray, e1: np.ndarray, e2: np.ndarray) -> float:
    return float(np.degrees(np.arctan2(v @ e2, v @ e1)))


def section_basis(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """C3/O1 section basis: e1 = rejection of world +x off a-perp; e2 = a x e1."""
    x = np.array([1.0, 0.0, 0.0])
    e1 = x - a * (a @ x)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(a, e1)
    return e1, e2


def main() -> int:
    real = load_source(str(IC.XML_PATH))
    mt = MonkeyTarget(birth_path=str(IC.MESH_PATH), pack_path=str(IC.PACK_PATH))
    sw = global_site_positions(real)
    packet = IC.load_packet()

    # ---- exact target anchors (packet joint records, B4-E6 anchor gap 0.0)
    j_elbow_r = next(j for j in packet["joints"] if j["name"] == "elbow_flexion")
    j_elbow_l = next(j for j in packet["joints"] if j["name"] == "elbow_flexion_l")
    j_wrist_r = next(j for j in packet["joints"] if j["name"] == "wrist_dev_r")
    j_wrist_l = next(j for j in packet["joints"] if j["name"] == "wrist_dev_l")
    elbow_r = np.asarray(j_elbow_r["origin"], dtype=float)
    elbow_l = np.asarray(j_elbow_l["origin"], dtype=float)
    wrist_r = np.asarray(j_wrist_r["origin"], dtype=float)
    wrist_l = np.asarray(j_wrist_l["origin"], dtype=float)

    # the shipped target roll witness (the known-good radius edge's declared roll
    # target = the `_band_roll` extreme vertex; reused EXACTLY, no new number)
    kg = json.load(open(IC.B4 / "receipts" / "01_known_good_records.json", encoding="utf-8"))
    q_r = np.asarray(kg["records"]["radius"]["landmarks"]["roll"]["target"], dtype=float)
    q_l = np.asarray(kg["records"]["radius_l"]["landmarks"]["roll"]["target"], dtype=float)

    # ---- source side (XML facts via the snapshot's own intake)
    A_r = real.body_by_name["ulna"].pos_global.copy()
    D_r = real.body_by_name["radius"].pos_global.copy()
    A_l = real.body_by_name["ulna_l"].pos_global.copy()
    D_l = real.body_by_name["radius_l"].pos_global.copy()
    span_src_r = float(np.linalg.norm(D_r - A_r))
    span_src_l = float(np.linalg.norm(D_l - A_l))

    # ---- the I6 derived distal point: elbow + |ulna->radius| * body-scale, ON the
    # elbow->wrist axis toward the wrist (C1 §1.4 direction resolution: distal).
    d_r = span_src_r * IC.BODY_SCALE_RADIUS
    d_l = span_src_l * IC.BODY_SCALE_RADIUS
    a_t_r = (wrist_r - elbow_r) / np.linalg.norm(wrist_r - elbow_r)
    a_t_l = (wrist_l - elbow_l) / np.linalg.norm(wrist_l - elbow_l)
    Pd_r = elbow_r + d_r * a_t_r
    Pd_l = elbow_l + d_l * a_t_l

    # ---- ROLL DERIVATION from O1's law (pre-evaluation; see module docstring)
    a_src_r = (D_r - A_r) / span_src_r
    a_src_l = (D_l - A_l) / span_src_l
    e1_sr, e2_sr = section_basis(a_src_r)
    e1_sl, e2_sl = section_basis(a_src_l)
    e1_tr, e2_tr = section_basis(a_t_r)
    e1_tl, e2_tl = section_basis(a_t_l)

    az_q_r = az_of(q_r - elbow_r, e1_tr, e2_tr)
    az_q_l = az_of(q_l - elbow_l, e1_tl, e2_tl)
    residuals = {}
    for site_r, side in (("TRIlat-P5", "r"), ("ANC-P2", "r"), ("ECU-P2", "r"),
                         ("TRIlat_l-P5", "l"), ("ANC_l-P2", "l"), ("ECU_l-P2", "l")):
        s_pos = sw[site_r]
        A, a_src = (A_r, a_src_r) if side == "r" else (A_l, a_src_l)
        b = s_pos - A
        b = b - a_src * (a_src @ b)
        b /= np.linalg.norm(b)
        e1s, e2s = (e1_sr, e2_sr) if side == "r" else (e1_sl, e2_sl)
        az_b_src = az_of(b, e1s, e2s)
        # O1 law: az_target(q) must equal az_source(s) + 90 deg
        demanded = (az_b_src + 90.0) % 360.0
        az_q = az_q_r if side == "r" else az_q_l
        resid = (demanded - az_q) % 360.0
        resid = min(resid, 360.0 - resid)
        residuals[site_r] = {"az_source_b_deg": az_b_src,
                             "demanded_target_az_deg": demanded,
                             "witness_az_deg": az_q,
                             "residual_deg": resid}

    # the declared pair must be the law-consistent one, uniquely within noise
    sel_r = residuals["TRIlat-P5"]["residual_deg"]
    sel_l = residuals["TRIlat_l-P5"]["residual_deg"]
    others_r = [residuals[s]["residual_deg"] for s in ("ANC-P2", "ECU-P2")]
    ok_law = sel_r <= 1.0 and sel_l <= 1.0 and min(others_r) > 10.0

    print(C.verdict("roll derivation (O1 law + existing witness -> unique candidate)",
                    ok_law,
                    f"TRIlat-P5 residual {sel_r:.4f} deg / left {sel_l:.4f} deg; "
                    f"alternatives ANC {others_r[0]:.2f}, ECU {others_r[1]:.2f} deg "
                    f"(O1 receipt: 0.1535 / 17.553 / 63.612)"))

    # ---- records in the B4 known-good schema
    records = {}
    for body, A, D, P, Pd, Q, site, elbow, wrist, dlen in (
        ("ulna", A_r, D_r, elbow_r, Pd_r, q_r, "TRIlat-P5", elbow_r, wrist_r, d_r),
        ("ulna_l", A_l, D_l, elbow_l, Pd_l, q_l, "TRIlat_l-P5", elbow_l, wrist_l, d_l),
    ):
        records[body] = {
            "parent": "humerus" if body == "ulna" else "humerus_l",
            "scale_policy": "uniform",  # authored-uniform precedent (atf:239-259; I6 row)
            "coords": ["elbow_flexion"] if body == "ulna" else ["elbow_flexion_l"],
            "axial_unresolved": False,  # the candidate DECLARES the edge (was True)
            "axis_assumptions": {},
            "axis_measure_kind": {},
            "landmarks": {
                "prox": {"id": f"{body}.prox", "target": P.tolist(),
                         "source_resolution": f"body_origin:{body}",
                         "source": A.tolist()},
                "dist": {"id": f"{body}.dist", "target": Pd.tolist(),
                         "source_resolution": f"body_origin:{'radius' if body == 'ulna' else 'radius_l'}",
                         "source": D.tolist()},
                "roll": {"id": f"{body}.roll", "target": Q.tolist(),
                         "source_resolution": f"site:{site}",
                         "source": sw[site].tolist()},
            },
            "handedness": "preserve",
            "mirror_plane_normal": None,
            "implied_axial_scale": dlen / float(np.linalg.norm(D - A)),
            "provenance": {
                "P": "packet joint origin elbow_flexion(_l) (B4-E6 anchor gap 0.0)",
                "P_d": "I6 authored derived point: elbow + |src_D-src_A| * "
                       "0.22170679566544982 along unit(elbow->wrist), toward the wrist "
                       "(C1 §1.4 distal direction resolution)",
                "Q": "shipped `_band_roll` extreme vertex — the known-good radius "
                     "edge's own declared roll target, reused EXACTLY (B4 receipt 01); "
                     "DEPENDENT by reuse (C3 §2.5), declared as such",
                "roll_source_site": "TRIlat-P5 per O1's witness law (see derivation)",
            },
        }

    declaration = {
        "role": "M-A02diag — isolated U-STR B4 diagnostic (authorized; memo §5)",
        "authorization_verbatim":
            "Authorize the isolated U-STR B4 diagnostic without requiring the "
            "hand-scoped O2 gate to pass. This authorization is for source-kinematic "
            "fidelity diagnostics only. Retain the anatomical falsifier outcome from "
            "R1; do not relabel source convention as anatomical evidence. No "
            "production radius supersession, hand fit, or training-body change is "
            "authorized by that diagnostic. Preserve old radius and all failed "
            "alternatives. Return the existing B4 criteria, exact proposed radius "
            "effects and resulting defined/undefined tendon coverage. A diagnostic "
            "PASS does not close A03 or authorize mechanically qualified grasp.",
        "candidate_identity": "U-STR exactly as I6 defined it (P body_origin:ulna <-> "
                              "elbow; P_d body_origin:radius <-> derived 5.1158 mm "
                              "point; s_a = 0.2217 kinematic) WITH the resolved roll",
        "roll_choice": {
            "declared_source_site": {"ulna": "TRIlat-P5", "ulna_l": "TRIlat_l-P5"},
            "declared_target_witness": "the shipped `_band_roll` extreme vertex "
                                       "(reused from the known-good radius record)",
            "law": IC.O1_LAW,
            "law_source": "audits/O1_ulna_orientation/report.md §5; receipts/"
                          "o1_combine_sign.json",
            "selection_rule": "the law + the existing witness demand az_source = "
                              "+158.1348 deg; exactly one declared candidate lies "
                              "within the +/-10 deg tube-line precision (C3-S2)",
            "residual_deg": {"ulna": sel_r, "ulna_l": sel_l},
            "o1_receipted_residuals_deg": IC.O1_RESIDUALS_DEG,
            "sign_basis": "the SIGN (no-flip) is unanimous over all three candidates "
                          "(independent site-split + olecranon chain, O1 §2/§4); the "
                          "residual selects the pair and is NOT independent validation "
                          "(the roll-ref site is circular for its own roll DOF — C3 "
                          "§2.5, O1 caveat)",
            "witness_dependency": "DEPENDENT (the radius edge consumes the same "
                                  "witness); declared, not hidden",
            "shared_point_note": "TRIlat-P5 == TRIlong-P5 == TRImed-P5 (one authored "
                                 "point, C3-S1): the roll consumes the single TRI "
                                 "point; effective independent validators 8 points / "
                                 "10 site records",
        },
        "measured_residuals_all_candidates": residuals,
        "witness_azimuth_deg": {"right": az_q_r, "left": az_q_l},
        "records": records,
        "preregistration": {
            "prediction": "The declared U-STR candidate passes the EXISTING B4 gate "
                          "T1-T6 unchanged (T1 provenance: parent humerus, 10-site set, "
                          "dist body_origin:radius, TRIlat-P5 owned by ulna; T2: "
                          "spans 23.075 mm / 5.116 mm, roll witnesses >> 1e-9; T3: "
                          "right/left sides clean, det +1; T4: s = 0.221707 in the "
                          "humerus neighbor band, constructed frames exact, C1's "
                          "independent 10/10 re-placement reproduced; T5: "
                          "resolution-consistency count == 1; T6: process clean).",
            "falsifiers": [
                "F-T1: any claimed site/resolution/parent the XML does not place there",
                "F-T2: any declared landmark missing/non-finite, span <= 1e-12, or "
                "roll witness <= ROLL_EPS 1e-9",
                "F-T3: cross-side claim, det(Q) != +1 beyond 1e-12, negative scale "
                "under preserve",
                "F-T4: constructed-frame law violation, scale outside the factor-2 "
                "humerus neighbor band or [0.2, 5.0] envelope, or C1's independent "
                "10/10 region test NOT reproduced under the declared frame (any site "
                "leaving its demanded region)",
                "F-T5: resolution-consistency count != 1 (a second equally supported "
                "owner)",
                "F-T6: any utility number computed as evidence in the gate scripts",
                "F-ANAT (RETAINED, not re-litigated): R1's refutation stands — the "
                "re-anchor this candidate forces carries NO primary-anatomical "
                "support; its basis is source-kinematic convention only",
            ],
            "stop_rule": "Any fired falsifier stops the diagnostic and is reported "
                         "with numbers; no tolerance is weakened, no candidate is "
                         "repaired, no alternative is searched. The diagnostic ends "
                         "at the verdict + before/after + coverage tables.",
            "acceptance_criteria": "the EXISTING B4 T1-T6 protocol unchanged "
                                   "(challenge_protocol.md §2-§4, amendments A1-A5)",
        },
        "frozen_before_evaluation": True,
        "cpu_only": True,
        "baseline_read_only": True,
    }

    p = IC.save_receipt("00_candidate_declaration.json", declaration)
    print(f"declaration frozen: {p}")
    print(f"  P_d(right) = {Pd_r.tolist()}  (d = {d_r*1000:.4f} mm along axis)")
    print(f"  s_a = {records['ulna']['implied_axial_scale']:.12f}")
    return 0 if ok_law else 1


if __name__ == "__main__":
    raise SystemExit(main())
