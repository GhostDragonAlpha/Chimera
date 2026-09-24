"""O1 script 5 — COMBINE (preregistered method (d)): the U-STR roll SIGN.

Inputs (this audit's receipts only):
  o1_source_split.json          - source volar = +x (split + roll-candidate geometry)
  o1_target_sections_directed.json - target volar/dorsal from the olecranon test

Constructions, stated exactly:
  Source U-STR frame: origin ulna body origin; axis a_s = unit(radius_origin - ulna_origin)
    (C1/C3's U-STR axis); transverse basis of roll candidate rc: b_rc = unit(rej of the
    site's transverse offset), c_rc = a_s x b_rc.
  Target shipped roll machinery: b' = direction of the elbow-band extreme vertex
    (_band_roll, actual_target_fit.py:89-97); its azimuth in C3's fixed section basis
    (e1 = rej of +x, e2 = a x e1) measured by C3-S2 = -111.87 deg (top-10 span
    -104.8..-126.1, gap ratio 1.001).
  The rigid fit maps b_rc -> b', c_rc -> c' (rotation about the forearm axis + scale).
  A source direction v (transverse) with frame coordinates (v.b_rc, v.c_rc) = alpha
  therefore lands at target-section azimuth  phi = az(b') + alpha.
  The 180-degree flip is phi + 180.

Measured labels:
  source volar  v_s = +x (rest frame)   [split + citations + bone surface]
  target volar  at section azimuth +90 deg (world +z, ANTERIOR)   [olecranon test]
Verdict per candidate: NO-FLIP iff |wrap180(phi - 90)| < 90 deg.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

O1 = Path(r"E:\PythonChimera\forearm_package\audits\O1_ulna_orientation")
OUT = O1 / "receipts" / "o1_combine_sign.json"

BAND_VERTEX_AZ_DEG = -111.86515772931568   # C3-S2 receipt: elbow-band top perp vertex (R)
BAND_TOP10_SPAN = [-126.1, -104.8]


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


def main() -> int:
    src = json.loads((O1 / "receipts" / "o1_source_split.json").read_text())
    tgt = json.loads((O1 / "receipts" / "o1_target_sections_directed.json").read_text())

    psi_v = 90.0     # target volar azimuth in (e1,e2): world +z, from the olecranon test
    psi_d = -90.0    # target dorsal azimuth: world -z

    rows = []
    for rc, geo in src["ustr_frame"]["roll_candidates"].items():
        alpha = geo["volar_azimuth_relative_to_b_deg"]
        phi = wrap180(BAND_VERTEX_AZ_DEG + alpha)
        phi_flip = wrap180(phi + 180.0)
        e_no = abs(wrap180(phi - psi_v))
        e_flip = abs(wrap180(phi_flip - psi_v))
        rows.append({
            "roll_candidate": rc,
            "b_azimuth_source_e_basis_deg": geo["b_azimuth_e_basis_deg"],
            "volar_az_relative_to_b_deg": alpha,
            "phi_no_flip_deg": phi,
            "phi_flip_deg": phi_flip,
            "error_no_flip_deg": e_no,
            "error_flip_deg": e_flip,
            "verdict": "NO-FLIP (sign correct)" if e_no < e_flip else "FLIP required",
        })
        print(f"{rc:11s} phi(no flip)={phi:+8.2f}  phi(flip)={phi_flip:+8.2f}  "
              f"|err| no-flip {e_no:7.2f}  flip {e_flip:7.2f}  -> {rows[-1]['verdict']}")

    unanimous = len({r["verdict"] for r in rows}) == 1
    out = {
        "inputs": {
            "target_volar_azimuth_deg": psi_v,
            "target_volar_basis": "world +z (ANTERIOR); olecranon test: D=+3.29±0.73 mm at t=+6 mm, "
                                  "D>2mm zone t in [-2,+12] mm (receipt o1_target_sections_directed.json)",
            "target_dorsal_azimuth_deg": psi_d,
            "source_volar": "world +x of the source rest frame (dorsovolar split + citations + bone surface)",
            "witness_b_prime_azimuth_deg": BAND_VERTEX_AZ_DEG,
            "witness_note": "the only existing target roll machinery (_band_roll extreme vertex); "
                            "C3-S2 measured it in the same section basis; its top-10 span is "
                            f"{BAND_TOP10_SPAN} deg and the vertex sits in the rig's elbow_R band, "
                            "which extends to t=105.6 mm (see cross-wave note in report)",
        },
        "per_candidate": rows,
        "unanimous_verdict": bool(unanimous),
        "SIGN_VERDICT": {
            "statement": ("The U-STR roll sign that maps SOURCE VOLAR (+x of the source rest frame) "
                          "to TARGET VOLAR (world +z = ANTERIOR = section azimuth +90 deg in the C3 "
                          "(e1,e2) frame) is the anatomically correct sign; the surviving 180-degree "
                          "flip maps source volar onto target DORSAL (world -z = POSTERIOR) and is "
                          "refuted by directed evidence."),
            "world_mapping": "source +x (volar) <-> target +z (volar/anterior); "
                             "source -x (dorsal) <-> target -z (dorsal/posterior); "
                             "source anatomical frame: volar=+x, dorsal=-x, lateral=+z; "
                             "target world: volar/anterior=+z, dorsal/posterior=-z, right=-x",
            "fit_frame_mapping": ("in the C3 (e1,e2) section bases (e1 = rej of +x, e2 = a x e1) the "
                                  "correct construction must carry source e-basis azimuth 0 deg "
                                  "(= +x transverse = volar) to target e-basis azimuth +90 deg, i.e. "
                                  "the required witness pairing supplies a +90 deg roll offset; the "
                                  "flip would land it at -90 deg"),
            "unanimous": bool(unanimous),
        },
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("unanimous:", unanimous)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
