# PREREGISTRATION (DRAFT) — grasp-candidates: candidate family v2 program

Status: DRAFT (chain stop 1). The Lieutenant commits these bytes ALONE and
FIRST on the publication lineage; the committed file is the freeze. The
gated experiments below (the v2.1 screen/sweep and the contact-force
evaluation) run ONLY after that commit; the implementation package pins the
published prereg commit. Author self-review certifies nothing; Sergeant
review is requested through the Lieutenant.

Worker: wk-grasp-candidates. Lane: `E:/ChimeraWork/monkey-coordination/grasp-candidates/`.
Campaign clock 2026-09-29 (host 2026-10-03). NO_WORKTREES honored.

## 1. Identity chain (frozen inputs)

| pin | sha256 |
|---|---|
| CANDIDATE_FORMULATION.md (the v2.0 frozen screen law, authored BEFORE its run) | `0c24657de95068eb7499c3b9f140b8467f58e5ba6bcc94d02c69207341dbd1b1` |
| instrument_v2.py (merged verdict #323; byte-identical in-package copy; == FINAL seal `ee7c1a24bfb343519e3b03b7a62644d1`, manifest `beb077ed7ba78aa27abc163ce2e27cd8d3d4de4d442f584cbb05bb0df0c1c477`, job `dac7d830d1cf4daf83df2db4fec5f38a` PASSED) | `9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd` |
| instrument-v2 committed prereg bytes (input-gate authority for the reused instrument) | `897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf` |
| instrument-v2 lane declaration | `71e31cdd4122e20bfefdf343df28b0e01fc2a51e70cba11296924ca97ce991ea` |
| frozen control input table (light gate C1/C2/C3) | `d8aacc23b27e2caaf60304c0e9a4fe711ac51245c0ca3bf6d021d8f7b5164bf2` |
| grasp_screen.py (v2.0 screen implementation, sealed) | `6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e9e0ea` |
| v2.0 screen seal manifest | `c270429a9a0c1110eec6df47fb1045c4a3ed92bce6ff779b8140e27d2f966a4a` |
| v2.0 screen receipt | `065328e4942a0bb8794138a96966aa8a3267fcd15ce084b9fb0490dff76b19ec` |
| v2.0 screen report | `eeea10e9247fe97c2e305d686b71c96f2e5cb390de7466a61823157aadca4266` |
| v2.0 runner receipt (job `7b8e4127ca5c46a69bc1a8b3a18f2abc`, PASSED, slot 0, cleanup_verified true) | `e6fbc96c100013a83d9565553da7defea7f01a837d2795e3065a1790a27f4911` |
| base for the v2.0 package | `7222729eca6e9f97f25061c8b1dc3d229bb703d8` |

Inherited input pins (re-verified GREEN at the v2.0 run by the reused
instrument's own gate: prereg bytes, declaration, 14 inherited pins incl. the
A05 mutation structure + XML, hand.vtp, G01 trunk constants, GRASP_MECHANISMS
prefix identity, MONKEY_COMPLETION_MAP; 19/19 STL pins 1:1; scaled VTP AABB
identity) carry forward unchanged into v2.1.

## 2. Scope and honesty of THIS prereg

- The v2.0 CHEAP SCREEN is NOT a gated experiment: it is the dispatch-declared
  first deliverable ("the CANDIDATE FORMULATION + the cheap geometric
  screening, not an expensive sweep"). Its law was frozen in the
  hash-pinned CANDIDATE_FORMULATION.md BEFORE the run (the screen code pins
  that sha and refuses on drift). No sweep ran; no acceptance is claimed.
- GATED by THIS prereg commit: (a) the family v2.1 cheap screen, (b) any
  v2.1 exact sweep, (c) the contact-force evaluation on survivors. Nothing
  else runs under this prereg.
- Every result is feasibility-at-the-represented-geometry (T2 surfaces,
  T3 established contacts) under the merged instrument's frozen tolerances
  (tau = 1.0e-4 m, pi_c = 1.0e-3 m, R_joint = 5.0e-3 m; never enlarged, no
  pair removed, no post-hoc tuning). It is never a grasp-capacity or
  biological claim.

## 3. The taxonomy law (binding for every candidate of this program)

T1 JOINT ORIGINS (certified A05 q=0 body origins, FK at q; `fk_origin`) vs
T2 MESH SURFACES (19 pinned STLs scale 0.5384048132470733 + hand.vtp envelope
at their placement transforms) vs T3 CONTACT POINTS (Level-2-established
surface meetings within tau / pi_c only). Placements are constructed on T2;
passes are decided on T3; T1 anchors kinematics and the recorded chord only.
The v1 (GP1-CC3) failure class — T1 placed ON the cylinder (chord
0.0739999998849158 m ~ diameter, h_len 2.0635200292263314e-06 m; T2 followed
through the solid; >= 16/17 non-contact bones crossing, merged erratum E1) —
is the permanent negative control of this program. The chord between T1 tip
origins is RECORDED and gated by NOTHING (the v1
`chord_exceeds_diameter_placement_family_undefined` refusal stays abolished).

## 4. Family v2.0 (screened 2026-10-03, job `7b8e4127ca5c46a69bc1a8b3a18f2abc`):
## THE CHEAP REJECTION MAP — zero survivors, no sweep

Construction (formulation section 2): postures {q_c PRIMARY, q_zero CONTROL,
F1, F2, F3} x the sealed GP1-CC3 axis enumeration (720 theta x 2 mirrors,
axis identity vs `iv.placement_family` verified at run) x the SOLVED
mesh-tangency offset s* (larger-root envelope over the two tip meshes'
vertices). Screens: light gate C1/C2/C3 (GREEN in situ), sound S0 vertex
screens, S3 reach/bracket, S1 exact (never reached), T3-only contacts.

Result: 7,200 of 7,200 candidates REJECTED at the cheap screens; 0 S0
survivors; 0 exact S1 cells; the expensive sweep is NOT RUN.

| posture | T1 chord (m) | tip_deep | clearance | no_approach | bracket | survivors |
|---|---|---|---|---|---|---|
| q_c_PRIMARY | 0.0739999998849158 | 954 | 486 | 0 | 0 | 0 |
| q_zero_CONTROL | 0.05560023493843668 | 1032 | 408 | 0 | 0 | 0 |
| F1 (thx d4) | 0.07399999923615011 | 24 | 1416 | 0 | 0 | 0 |
| F2 (thx d5) | 0.07399999954408089 | 0 | 0 | 1440 | 0 | 0 |
| F3 (thx d2) | 0.0739999996051494 | 1336 | 0 | 0 | 104 | 0 |

Reading (declared classes, formulation section 3):

- S0_REJECT_TIP_DEEP (3,346/7,200; dominant at q_c, q_zero, F3): at the
  solved tangency the TIP'S OWN MESH folds deeper than pi_c into the trunk
  (q_c median first-proven depth 1.988e-3 m; minima sit at the pi_c boundary
  by construction of the threshold). A rigid curved fingertip surface pressed
  onto a 37 mm cylinder conforms only where the pad aligns tangentially; the
  perpendicular family cannot express that alignment.
- S0_REJECT_CLEARANCE (2,310/7,200; dominant at F1): FULL-HAND CLEARANCE
  fails — the opposing digit (distph2 at q_c/q_zero/F1) and the fifth
  metacarpal cross the solid at the tips' tangency offset (q_c minimum
  proven non-contact depth 1.048e-3 m, median 9.336e-3 m).
- S0_REJECT_NO_APPROACH (1,440/7,200; all of F2): the v2.0 SOLVED-OFFSET
  CONSTRUCTION cannot form a candidate (no tip vertex root at any offset).
  This rejects the construction at that axis; it is NOT a mesh-level
  impossibility proof (the class is defined on the vertex envelope).
- S3_REJECT_BRACKET (104/7,200; F3 only): solved offsets marginally outside
  the declared bracket (s* in [-1.0e-4, 0) m — the wrong side of the mirror).
- Coverage: per posture the class counts sum exactly to 1,440 (asserted at
  run, refuse otherwise). Determinism slice 40 cells byte-identical. Axis
  family identity 16 cells identical. Light gate C1 (zero flags, all CLEAR),
  C2 (TOUCHING, d = 0.0), C3 (GENUINE, 4.987e-3 m) GREEN.
- Control honesty: the q_zero CONTROL confirms the screen has no vacuous
  pass; its rejection profile resembles the certified postures, so it does
  NOT discriminate posture feasibility (all postures reject) — stated
  plainly.

CONSEQUENCE (branch law, formulation section 4): no sweep runs for v2.0.
This is the Captain-ordered cheap rejection BEFORE another expensive sweep.
The v2.0 rejection is at the REPRESENTED geometry of the certified posture
set, under the declared perpendicular-pinch construction only.

## 5. Family v2.1 (declared NOW; gated by THIS prereg's commit)

Motivated strictly by the recorded v2.0 rejection classes (no new freedom is
invented from results: the two missing placement DOF are structural, named
in the formulation as the v2.1 extension):

- PARAMETERS: theta (720, unchanged) x the axis TILT phi out of the
  perpendicular-to-chord plane, declared grid phi in
  {+60deg, +45deg, +30deg, +15deg} (two senses) = 8 values x mirror {0,1}:
  11,520 axes per posture; PLUS the two-contact offset solve: for each axis,
  a 1-D root find on the chord-direction offset tau_vh in [-0.05, +0.05] m
  (vertex upper-root envelopes of the two tip meshes equalized; bisection,
  40 iterations, vertex-level — cheap) giving the offset pair (s, tau_vh).
  The tips' T1 chord midpoint m remains the anchor; the chord stays recorded,
  ungated.
- POSTURES: q_c PRIMARY only in the first pass; the other four postures run
  ONLY if q_c yields >= 1 S0-survivor (declared CPU cap law).
- SCREENS: unchanged from the frozen formulation section 3 (same classes,
  same soundness law, same caps CAP_S1_PER_POSTURE = 96 and the 2.5 h S1
  budget, same tolerances). ONE NEW active gate, declared A PRIORI (the v2.0
  survivor set is empty, so no distribution informed it):
  pad-orientation cos > 0 (the tip's distal-extent direction faces the
  inward radial) — active at S1-survivor recording from v2.1 on.
- EXECUTION: same runner path, same in-situ light gate + input gate +
  coverage + determinism-slice requirements; declared CPU envelope for the
  whole v2.1 program <= 9 CPU-hour (the instrument lane's measured-envelope
  lesson applied BEFORE the run; excess is a finding, never normalized).

### Predictions (frozen now) and falsifiers

- P1 (reach): v2.1 produces >= 1 S0-survivor at q_c PRIMARY. FALSIFIED if
  the q_c S0-survivor count is 0 across the full declared grid.
- P2 (the tilt relieves the dominant failure): the TIP_DEEP share among
  reachable (non-no_approach) q_c axes drops below 50% (v2.0: 954/1440 =
  66.3%). FALSIFIED if the share stays >= 50%.
- P3 (exact feasibility is rare): exact S1 survivors at q_c <= 20.
  FALSIFIED if > 20 (the family would be tolerance-degenerate — a finding
  routed to the Lieutenant, never a tune).
- P4 (two-contact law): among exact survivors, BOTH declared tips are in the
  contact band (T3 established). FALSIFIED if any survivor carries a single
  established contact.
- PROGRAM FALSIFIER (the ladder law): if v2.1 rejects at the cheap screens
  with zero survivors, the declared next candidate is v2.2 (POSTURE
  VARIATION: cmc/mp flexion scan within the certified ranges at the v2.1
  placement solve — the remaining kinematic DOF), again cheap-screened
  BEFORE any sweep. If v2.2 also rejects, the candidate-family line for
  this hand is reported EXHAUSTED at the certified posture/placement space,
  and the honest finding stands: no lawful bone-level two-contact grasp of
  the 37 mm trunk was found at the represented geometry, and the structural
  causes are the pad-fold (TIP_DEEP) and opposing-digit clearance classes.

## 6. Contact-force evaluation plan (gated; survivors only)

On exact survivors only: the actuator-map frontier (actuator-map lane
revision-2 map of record, `run_actuator_map.py` sha256
`334ba389cb13e914135a2994d7e56cc1894941f55e86d5c443c23eb67df43e61`, MP cap
0.8875, posture-conditional tau(q, f)) applied to each survivor's T3
established contacts at THAT posture: the per-contact force the anatomy must
supply vs its capacity under the map's frozen quasi-static conventions.
Off-surface points are never inputs. Prediction P5: at least one survivor's
required contact forces lie within capacity at the pad contacts. FALSIFIED
if every survivor exceeds capacity somewhere (then the geometric family is
feasible but not holdable — a distinct, reportable outcome).

## 7. Honest-absent inventory (unchanged by any result above)

- Measured friction ABSENT (friction-r1r2 holds source-qualified literature
  bounds only); x_press ABSENT (no pressure-channel measurement; M03 is a
  declared parameter envelope); fingertip pads/soft tissue ABSENT (A2);
  species-true anatomy ABSENT (A05 hybrid disclosure; source-fidelity gap
  unquantified); C01 frame round-trip verification registered REQUIRED (A09).
- Consequently: feasibility-at-the-represented-geometry ONLY; no frictional,
  pressure, pad-level, or species-true grasp claim is made or testable here.

## 8. Evidence obligations

Sealed packages via `task_package.py seal|run` only; `--keep` for every
declared artifact; failures preserved; all sha256 into the lane EVIDENCE.md;
evidence anchored through anchor.py before registry reference; publication
through the one publication owner. Dev smokes are declared and carry no
results.
