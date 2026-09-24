"""B1 receipt: rebuild the ACTUAL correspondence (module copies, read-only) and print
exactly what is authored for ulna, ulna_l, hand_r, hand_l.

Also runs correspondence.collect_refusals to prove the anchor-only authorship is
ACCEPTED (refusals empty), and prints SEG_EVIDENCE vs UNRESOLVED membership.
Output -> receipts/correspondence_receipt.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

WORK = Path(__file__).resolve().parent.parent / "work"
sys.path.insert(0, str(WORK))

import actual_target_fit as atf  # noqa: E402  (ANCHOR is a local inside _build; UNRESOLVED/SEG_EVIDENCE are module-level)
from correspondence import collect_refusals  # noqa: E402
from intake import global_site_positions  # noqa: E402
from mesh_target import MonkeyTarget  # noqa: E402
from synthetic_fixtures import load_real  # noqa: E402

BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"
PACK = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"
OUT = Path(r"E:\PythonChimera\forearm_package\audits\B1_source_anatomy\receipts\correspondence_receipt.txt")

TARGETS = ["ulna", "ulna_l", "hand_r", "hand_l"]


def main() -> int:
    real = load_real()
    mt = MonkeyTarget(birth_path=BIRTH, pack_path=PACK)
    sw = global_site_positions(real)
    corr, notes = atf.build_correspondence_envelope(real, mt, sw)

    L = []
    L.append(f"correspondence note: {corr.note!r}")
    L.append(f"segments total: {len(corr.segments)}")
    L.append(f"landmarks total: {len(corr.landmarks)}")
    refusals = collect_refusals(corr, real)
    L.append(f"collect_refusals -> {len(refusals)} refusals (anchor-only authorship ACCEPTED)" if not refusals
             else f"collect_refusals -> REFUSALS: {refusals}")
    L.append("")

    seg_by = {s.source_body: s for s in corr.segments}
    for body in TARGETS:
        s = seg_by[body]
        L.append(f"### segment {body}")
        L.append(f"  parent={s.parent}")
        L.append(f"  proximal_landmark={s.proximal_landmark!r} -> {np.round(corr.landmarks[s.proximal_landmark], 4)}")
        L.append(f"  distal_landmark={s.distal_landmark!r} -> {np.round(corr.landmarks[s.distal_landmark], 4)}")
        d = float(np.linalg.norm(corr.landmarks[s.proximal_landmark] - corr.landmarks[s.distal_landmark]))
        L.append(f"  |prox - dist| = {d:.6e} m  (degenerate: distal anchor == proximal anchor)")
        L.append(f"  roll_ref={s.roll_ref!r} -> {np.round(corr.landmarks[s.roll_ref], 4)}")
        L.append(f"  coords={s.coords}")
        L.append(f"  axial_unresolved={s.axial_unresolved}")
        L.append(f"  axis_evidence={s.axis_evidence}")
        L.append(f"  axis_assumptions={s.axis_assumptions}")
        L.append(f"  scale_policy={s.scale_policy}")
        L.append(f"  source_landmarks: {corr.source_landmarks.get(f'{body}.prox')!r}, "
                 f"{corr.source_landmarks.get(f'{body}.dist')!r}, {corr.source_landmarks.get(f'{body}.roll')!r}")
        L.append(f"  note field: {notes.get(body)!r}")
        L.append(f"  body in atf.UNRESOLVED: {body in atf.UNRESOLVED}; in SEG_EVIDENCE: {body in atf.SEG_EVIDENCE}")
        L.append("")

    L.append("SEG_EVIDENCE keys (bodies with measured pack-pair evidence): " + str(sorted(atf.SEG_EVIDENCE)))
    L.append("UNRESOLVED set: " + str(sorted(atf.UNRESOLVED)))
    txt = "\n".join(L)
    OUT.write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
