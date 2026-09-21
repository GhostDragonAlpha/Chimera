# AMENDMENT 1 — the inlier rule's minimum-inlier floor (preregistration 96ddb501...)

Banked BEFORE any seat number, cure number, control number, or pose number was measured
(run 1 crashed after recording the fits alone: no A2/A3/A4/A5/control/pose quantity exists
anywhere yet — `battery.json` of run 1 held only inputs, derivations, metric transfer, and the
two fit records). This amendment is justified SOLELY by those fit records, verbatim:

- **bond.joint_01_02 (bone_02):** the registered rule CONVERGED (fixed point, 72 iterations):
  r = 3.044128510081 mm, 599 inliers, RMS residual 0.155477725893 mm, max residual
  0.310489428534 mm ≤ band ε = 0.310857620079 mm, the recorded apposition point ON the cap
  (|c − on_02| = 3.172344444209 mm ≈ r), center on the pelvis side, radius inside the P0 band
  [1.5, 4.5] — but the registered minimum-inlier floor REFUSED it: n_min = ceil(2π·r²/q) = 676
  with q = 0.086237072414 mm²/vertex (the mesh's GLOBAL area quota) > 599 measured.
- **bond.joint_01_03 (bone_03):** the same rule PASSED the floor: r = 2.682250273053 mm,
  533 inliers ≥ n_min = 523 (q = 0.086547724483).

## DIAGNOSIS (from the refused fit's own numbers, no other measurement)

The floor's density proxy is wrong, not the cap. The registered floor demanded "a hemisphere
tiled at the mesh's own area quota", using the GLOBAL quota q = A_total/V_total. The measured
cap of hip 02 is SPARSER than the mesh average: 599 vertices over a hemisphere of
2π·3.0441² = 58.225 mm² is 10.29 vertices/mm² against the global 11.60 — the head cap is the
smoothest, least-curved surface class of the femur, and curvature-adaptive decimation gives it
FEWER vertices per mm² than the feature-rich average. The proxy therefore over-demands by
~13% on exactly the surface it is supposed to admit (hip 03 passed only marginally: 533 vs
523). Coverage and density were conflated; the anatomical claim is about COVERAGE.

## THE AMENDED FLOOR (same anatomical claim, direct form, still zero free numbers)

The femoral head is a hemispherical articular cap (Hartman & Straus 1933, the bond's own
anatomical reading). The floor is stated directly in AREA, no vertex-density assumption:

    A_set ≥ π·r_fit²

where A_set = the summed kernel-formula area of the fixed-point set's triangles (every corner
an inlier) and r_fit is the fit's radius. π·r² is HALF the hemisphere's area (2πr²): the band
ε legitimately trims the cap at the rim where the neck departs tangentially, so the floor
keeps a real anti-undersizing tooth (a mini-patch or a ring segment sits far below it) while
no longer depending on the cap's local sampling density. The rule still refuses on: cycle,
cap, degeneracy, A_set < π·r_fit², radius outside [1.5, 4.5] mm, subject-check failure.

## PRE-MEASURED DIAGNOSTIC OF THE AMENDED FLOOR (the run-1 fixed points, area recomputed)

- hip 02: A_set = 39.405 mm² ≥ π·r² = 29.112 mm² (coverage 0.677 of the hemisphere) — PASSES.
- hip 03: A_set = 30.850 mm² ≥ π·r² = 22.602 mm² (coverage 0.682) — PASSES.

The two coverages agree to 0.7% — the band rim trims both caps to the same fraction of a
hemisphere, which is what a genuine spherical cap boundary looks like.

## DISCIPLINE

- The ORIGINAL floor's numbers stay in the battery record for both hips
  (`n_min_quota`, `n_min_quota_ok`), never erased; hip 02's run-1 refusal at that floor is
  recorded here and in the receipt, verbatim.
- The amendment's justification is the fit's own density arithmetic above; NO seat, cure,
  control, or pose quantity existed when it was banked. Choosing rules by the seat outcome
  remains F4 and this lane still dies by its own receipt if it does it.
- Nothing else from the parent preregistration changes: seed, band, growth, subject checks,
  P0 band, axis, sign rule, range record, apposition area, battery protocol, falsifiers.

Trailer: Agent: GLM 5.3
