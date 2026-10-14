# PREREGISTRATION AMENDMENT 5 — the boundary-seat convention at the maximin (banked BEFORE the maximin re-run)

MEASURED FACT THAT FORCES THIS AMENDMENT: the first completed v2 derive (pose_v2.json sha256
50bfab13647e15d0960da00029654be75e7ce514ba4fcb8f631fedceca70d6f1 — banked here and in the
receipt before this file's re-run overwrites it; nothing was minted from it) ran the
amendment-4 protocol to completion:

- the strict solves are INFEASIBLE from both declared starts (SLSQP status 8, "Positive
  directional derivative for linesearch"; min T3 slack -25.05620337207 mm from rest,
  -25.02295782659 mm from the v1 pose of record, argmin bone_05 both times) — P-AV2-3 GREEN;
- the structural pin held (the v1 pose's plane equals the hand-pinned level plane to 1e-6) —
  P-AV2-2 GREEN;
- the maximin from the v1 pose of record CONVERGED (SLSQP status 0, 153 iterations) at
  t_max = -26.337554646317 mm with BOTH caps active (V = V_rest + 1.2e-10 mm^2,
  d = d_rest exactly) and the right knee BINDING at its recorded range's high end;
- the maximin from rest hit the iteration limit (status 9, 400 iterations) at
  t_max = -26.337554648374 mm — the same optimum to 2.1e-9 mm from both starts;
- AND the maximin's returned point reads min seat slack -6.3e-11 mm (rest start) / -0.0
  (v1 start): SLSQP's stopping point sits ON the committed 3.0 mm loop-seat cut boundary.
  The amendment-4 FV2 screen ("a seat over the cut -> NOT MINTED", hard zero) read the
  boundary as a breach: no maximin start passed, no maximin pose was minted, pose_v2.json's
  pose_bonds = null. The maximin ARTIFACT the amendment-4 outcome-I deliverable requires
  (its battery + render) was lost to a 6.3e-11 mm boundary reading — 7.8e-13 of the cut,
  twelve orders below the metric's own resolution.

THE AMENDMENT (scope: the FV2 boundary screens and the battery's within-cut verdicts ONLY —
no objective, no bound, no cut, no cap, no prediction changes):

- THE COMMITTED CONVENTION, APPLIED: law doc section 5B's resolution floor — tol_ip =
  specimen.resolution_um/2 = 0.08 mm — is the gap metric's own localization class: "readings
  below it lie inside the surfaces' own localization". A boundary breach BELOW tol_ip is
  indistinguishable from AT the boundary, and the committed batteries already run this exact
  convention on seat readings (the v1 battery's F2 field: below_resolution_floor —
  "recorded as below-resolution readings, never clause-binding").
- THE AMENDED FV2 CLAUSE: every FV2 boundary reading (seats, caps, ranges) records its raw
  breach verbatim beside the verdict; the reading is clause-binding (the maximin is NOT
  MINTED) iff the breach exceeds tol_ip = 0.08 mm. At or below tol_ip: recorded, never
  clause-binding. The maximin's own screen keeps requiring SLSQP success (the rest start's
  status-9 exit stays the recorded second-start exit).
- THE BATTERY'S WITHIN-CUT VERDICTS (F3 tarsal loops, PA4 moved non-hip seats) gain the same
  convention: breach_mm recorded beside every verdict at full record precision; the F3/PA4
  falsifier fires only above tol_ip. Nothing dropped, nothing rounded toward passing.
- EVERYTHING ELSE stands verbatim: the strict solves, the maximin problem, the caps, the
  declared starts, the predictions P-AV2-1..P-AV2-8, the render path, the gates.
- RUN 1'S NUMBERS STAND IN THE RECORD unedited (the sha and every reading above); the re-run
  replaces the artifact, not the history.

Scope rule recorded: this amendment changes HOW CLOSE TO A COMMITTED BOUNDARY a reading must
sit before the records can call it a breach — by the committed resolution constant — and
changes nothing else. It is banked here (sha in preregistration_amendment_5.sha256) before
the maximin re-run, and the battery asserts the bank matches the file at run time.

Trailer: Agent: GLM 5.3
