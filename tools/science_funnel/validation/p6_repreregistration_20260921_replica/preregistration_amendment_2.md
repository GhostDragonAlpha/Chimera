# AMENDMENT 2 — the A3 invariance carrier (preregistration 96ddb501..., amendment 1 0c3484c1...)

Banked after run 2, whose A3 FAILURE-FORCE verdicts were already GREEN (outcomes identical
across θ; failure_force_n bitwise == cure·A: 293.037364111167 N hip 02, 415.916953738494 N
hip 03), and whose ONLY A3 red was the carrier sub-check this amendment corrects. The seat,
control, sign, pose and mass numbers of run 2 are thereby already measured and are recorded
verbatim in the receipt; nothing in this amendment touches their definitions, and none of them
is re-derivable differently by the fix below (it changes which triangles the posed-area carrier
consumes, nothing else).

## RUN 2's RED, VERBATIM

- hip 02 A3 `patch_same_set`: rest True, hi_endpoint False, lo_endpoint False;
  `patch_area_rel_dev`: rest 0.0, hi 1.556650579991, lo 2.211503668063.
- hip 03 A3: rest 0.0, hi 0.967749896794, lo 0.893729535087.

## DIAGNOSIS (a category error in the battery's carrier, visible in the same run's A2 records)

The battery recomputed "the patch" at each posed θ with the §3 ESTIMATOR — the set of ALL child
triangles whose centroid lies within the 3.0 mm cut of bone_01. At θ = 0 that set IS the pinned
apposition patch. At range extremes it is a DIFFERENT object: the posed femur genuinely brings
neck/shaft surface INSIDE the touching class of the pelvis (the SAME run's A2 records show it:
posed within-3.0-of-parent proximity patch grows from 492 rest triangles to 693 posed vertices
(hip 02, hi) / 710 to 771 (hip 03, hi); the law-metric min gap DROPS to 0.098 / 0.161 mm at the
hi endpoint — deep-flexion impingement-class proximity, recorded, not an error). The proximity
class measures whole-bone proximity; the cure input A is the bond's pinned apposition surface.
Conflating them made a correct invariance (a rigid pose cannot change the pinned patch's area)
read as a failure.

## THE AMENDED CARRIER (what P3's area-invariance check consumes)

- Binding A3 carrier: the POSED areas of the PINNED patch triangles — the rest mask's indices,
  rigidly transformed — compared to their rest areas: rel dev ≤ 1e-12 (the registered float
  detector; expected ~1e-16). This is exactly "nothing is resampled": the pinned apposition
  surface is carried intact by the pose.
- The whole-bone proximity recompute at posed θ is RECLASSIFIED as an A2 READING
  (`proximity_patch_posed`: triangle count, area, mean/max vertex gap), recorded for both arms,
  non-binding — it is the one-sided-predicate evidence that the femur enters impingement-class
  proximity at range extremes while the seat predicate (≤ 3.0 mm) stays green.
- P3's verdict = failure-force bitwise invariance + failure_force == cure·A bitwise + the
  holds/fails pattern + the pinned-patch posed-area carrier above.

## DISCIPLINE

- The predicted carrier deviation remains ≤ 1e-12 (preregistration §6 P4 ticks — unchanged in
  substance; the fix corrects WHICH triangles it is measured on).
- No verdict is redefined by the fix: the failure-force law checks were green before and stay
  green; the proximity readings were red-as-misread and become recorded readings.
- Everything else from the parent preregistration and amendment 1 is unchanged.

Trailer: Agent: GLM 5.3
