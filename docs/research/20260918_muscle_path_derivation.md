# Muscle Path Derivation - Macaque Arm + Hindlimb (MUSCLE-PATHS lane, 2026-09-18)

Branch: `lane/muscle-paths-20260918` (from `origin/master` at `c43d3363`).
Work record: `work.creature.muscle_path_geometry` (Rule-0 admission, this branch).
Deliverable: `tools/science_funnel/validation/muscle_paths_20260918/muscle_path_geometry.json`
(schema `chimera.muscle_path_geometry.v1`, admitted as `model.creature.muscle_path_geometry`).
Receipt: `tools/science_funnel/validation/muscle_paths_20260918/receipt.json`.

## What this lane bridges

The graph held PCSA/fascicle/pennation numbers (Guimaraes 2026, batch-verified
2026-09-17) and a 39-muscle OpenSim arm model with path records, but nothing
that turns "we have architecture data" into "we can compute muscle torque at a
pose". This lane derives that bridge: paths -> moment arms -> per-muscle force
capability -> joint torque envelopes, at two declared poses per limb, with
every estimate and every failure recorded.

## RULE 0 - the membranes, stated before the run

### ARM membrane

- **STATEMENT.** Via-point-resolved straight paths plus analytic cylinder
  wrapping reproduce the source model's moving-length behaviour; every
  non-cylinder wrap contact (ellipsoid/torus) leaves the straight length a
  declared lower bound with per-contact error bounded by `r_eff*(pi-2)`.
- **PREDICTION (was unmeasured).** At every pose, for every muscle whose
  resolved path has NO active wrap contact, `|r_geometric - (-dL/dq)|` is zero
  up to finite-difference error (declared tolerance 1e-6 m); wrapped muscles
  carry the fd-virtual-work arm as authoritative with the geometric arm
  advisory (the tangent exit point slides on the obstacle as q changes). No
  resolved path endpoint lies inside a wrap cylinder.
- **FALSIFIER.** A straight-path tolerance violation, an endpoint inside a wrap
  cylinder, or a conditional-point length jump > 5 mm marks the record false
  for that muscle.
- **MEASURED OUTCOME.** HELD. Worst straight-path `|r_geo - r_fd|` =
  **4.3e-10 m** (39 muscles x 7 coordinates x 2 poses; central differences,
  step 1e-4 rad, topology frozen per base pose). Conditional jump measured
  **1.0e-4 m** (bound 5e-3). One cylinder wrap ACTIVE at the derived poses
  (anconeus around `ELBOW_ANC`, arc 1.862 rad); its fd arm (-3.6 mm) vs static
  perpendicular distance (-7.9 mm) difference is the contact-slide term, kept
  visible, fd authoritative. Endpoint-inside never occurred (it raises).
  29 wrap references stay non-cylinder (ellipsoid/torus) and are recorded as
  UNRESOLVED with conservative bounds (14 contacting segments across the two
  poses). Three cylinders (`ELBOW_EXTENSOR`, `ELBOW_ANC`, `BICEPS_SUP`) are
  implemented analytically; the triceps/biceps cylinders are out of contact at
  both derived poses - the source via points already route those paths, and
  their straight arms land at 11-27 mm, in line with the wrapped expectation.

### HINDLIMB membrane

- **STATEMENT.** Straight-line paths built from Oku 2021 Table 1 segment
  lengths (thigh 0.163 m, shank 0.182 m, foot 0.074 m, phalanges 0.045 m;
  pinned fulltext) plus Guimaraes Table 3 functional groups put enough
  physiological cross-sectional area around each walking joint to cover the
  Oku 2021 walking torques under a derived specific tension.
- **PREDICTION (was unmeasured).** Envelope/required-torque ratio >= 1 at hip,
  knee and ankle after mass adjustment (8 kg mulatta vs 10.038 kg fuscata
  model; torque ~ mass at fixed posture).
- **FALSIFIER.** Any joint direction whose conservative envelope (worst side
  across the two poses) misses coverage by more than the declared 25% moment
  -arm uncertainty marks the estimated paths false for that direction.
- **MEASURED OUTCOME.** Split verdict, recorded as measured:
  - HELD: hip extension ratio **17.9**, hip flexion **2.6**, knee flexion
    **4.6**, ankle dorsiflexion **108.6**, ankle plantarflexion **0.82**
    (marginal: inside the declared 25% uncertainty, outside ideal coverage).
  - **FALSIFIED: knee extension (ratio 0.00) and mtp flexion (ratio 0.00).**
    Cause, measured not assumed: at the walking pose (49 deg knee flexion) the
    straight quad lines pass 0.1-4 mm from the knee axis - the patella is what
    maintains that arm, and a straight-line proxy has no patella; likewise the
    FDL/FHL lines pass dorsal to the metatarsal heads where the real tendons
    wrap plantar pulleys. Consequence recorded in the deliverable: these two
    directions MUST NOT be used for force claims until via-pulley paths are
    derived. This is exactly the repo's standing law - no unresolved path is
    silently promoted to a functioning actuator.

## Method (derivation chain)

1. ARM PATHS: `macaque_anatomy.parse_source()` (sha-pinned `.osim`, revision
   `4fb7dddeec06a0df9525c18f37234a824cb1b5b1`) gives body-fixed attachment
   points, the one conditional via point (`flex_digit_profundus-P2`, active on
   `radial_pronation` in [-1.5708, 0.35238]) and 40 `PathWrap` references -
   the same source-transform model `coupled_arm.py` consumes. World paths at a
   pose come from the strict `pose_frames()`. Conditional semantics: active
   inside the recorded range, straight bypass outside.
2. CYLINDER WRAPPING: exact tangent construction in the plane perpendicular to
   the cylinder axis (Z of the wrap frame), quadrant rule honoured
   (`ELBOW_ANC` is `-x`), arcs limited to <= pi, endpoint-inside raises.
   A 90-degree basis bug (angle basis vs atan2 basis) was found by the
   pipeline's own zero-wrap-events signal and fixed before the run was
   accepted - the zero-event output was impossible given miss distances below
   radius, which is precisely how a falsifier should fire.
3. MOMENT ARMS, twice: (a) signed perpendicular distance from the joint axis
   (world origin + instantaneous axis composed through prior joint axes at the
   current pose - multi-axis CustomJoints included) to the joint-spanning
   segment's line of action; (b) `-dL/dq` by central differences with the base
   pose's wrap/conditional topology frozen so the derivative differentiates
   smooth geometry, not contact-state switches. Straight paths: equal to
   4.3e-10 m. Wrapped paths: fd (virtual work) authoritative.
4. ARM FORCES: the model's own `max_isometric_force` (N, 39/39 records) ->
   torque = fd arm x force; envelope = signed sum per coordinate.
5. HINDLIMB PATHS: sagittal 2D linkage, plantigrade neutral; walking =
   Oku mid-stance (x=0.50 of cycle, before alteration: hip -0.027 rad, knee
   flexion 0.860 rad, foot flat by closure - Oku's raw ankle reading is NOT
   applied because its anatomical zero is not published). All 30 admitted
   mulatta muscles get estimated attachment landmarks (segment, u, v) from
   their Table 3 functional group; every landmark is listed in the deliverable
   and is an estimate, not a measurement. A muscle contributes moment ONLY
   about joints its attachments straddle (no cross-joint line-of-action
   fiction). Calcaneal insertions sit BEHIND the ankle (negative foot u);
   the first draft put them anterior - fixed as an anatomical error before
   accepting the run.
6. SPECIFIC TENSION, derived not chosen: least squares through the origin of
   mass-adjusted Oku Table 2 Fmax against matched Guimaraes PCSA sums
   (IL->ILI, GMED->GMed, VAS->VI+VL+VM, TA->TA, SOL->SOL, GAS->MG+LG,
   EDL->EDL, FDL->FDL; forces x 8.0/10.038). Result **1.281 MPa
   (128.1 N/cm2)** with per-group implied tensions published (0.31-5.29 MPa
   spread) - wide, visible, and a reason to treat absolute forces as coarse.
7. COVERAGE: required torque = Oku signed peak x mass ratio; capability =
   worst (smallest) envelope side across the two poses, read on the matching
   side of the flexion-positive convention; Oku sign map (hip flexion+,
   knee extension+, ankle dorsi+) handled explicitly.

## Poses

- ARM neutral: source model defaults (elbow 90 deg flexed).
- ARM "walking": midpoint of every unlocked coordinate range - a taste-free
  surrogate for a quadrupedal support pose, not a recorded stance (unknown).
- HINDLIMB neutral: plantigrade standing (all joint angles 0).
- HINDLIMB walking: Oku 2021 mid-stance values as above.

## Validation cross-checks (task step 5)

- The OpenSim file exposes no computed moment arms (static model XML), so the
  arm cross-check is internal and exact: geometric perpendicular distance vs
  kinematic `-dL/dq`, agreement 4.3e-10 m on all straight paths, both poses.
  Physiological spot checks hold: biceps elbow arm +27 mm (flexion+),
  triceps -12 mm, ECU +8 mm, anconeus wrapped fd -3.6 mm.
- Hindlimb cross-check is the Oku torque coverage above (split verdict).

## Assumptions and unknowns (all also in the deliverable)

- Non-cylinder wrap contacts unresolved (bounds only); wrapped arms carry the
  slide-term caveat.
- Arm "walking" pose is a range-midpoint surrogate.
- Hindlimb landmarks are anatomical estimates; straight-line proxy has NO
  patella and NO mtp pulley - measured to be fatal exactly there.
- Specific tension is a derived slope over 8 groups of one specimen vs another
  species' simulation Fmax; residuals wide; published.
- Oku is simulation output for Macaca fuscata; mass adjustment assumes torque
  scales with body mass at fixed posture.
- 49 Guimaraes rows quarantine under the dataset's own closure laws (6 of
  them mulatta: rows 4, 8, 9, 11, 21, 23); nothing dropped silently.
- No activation dynamics, no tendon compliance, no force-length/velocity, no
  time integration, no runtime actuation, no biological verification.

## Replay

```bash
E:\PythonChimera\.venv-hy3d\Scripts\python.exe -m tools.science_funnel.validation.muscle_paths_20260918.derive_muscle_paths --output tools/science_funnel/validation/muscle_paths_20260918
E:\PythonChimera\.venv-hy3d\Scripts\python.exe -m tools.science_funnel.validation.muscle_paths_20260918.qualify_muscle_paths
E:\PythonChimera\.venv-hy3d\Scripts\python.exe -m unittest tools.science_funnel.tests.test_muscle_paths
```

Byte-determinism is tested (`test_derivation_is_byte_deterministic`).
