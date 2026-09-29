# MAT2-M05 report — explicit contact, bond and release physical interfaces

Task MAT2-M05 / planning id M05, criteria sha256 0a93a04afbb63c9767fd0e2c988c33d4d40742e03a1dd613bf93d0e9a9f3d461.
Attempt 45bc250a82894954b7f7cd61bfae410c, arrival arrival-3cb83ace592841a3a5ef7a8ab5757148, base revision e62e3c43533d4b27b98cf14ed28099000ba8a827 (sealed line
origin/astra/gait-capture carrying merged MAT2-M01..M04, B03, B04),
isolated local branch-2 checkout. Preregistration frozen before implementation
(PREREGISTRATION.md; corrections A1-A4 pre-receipt, first failures preserved in
the correction text).

## What was implemented

`interface_exchange.py` — two pentahedron bodies meet at a DECLARED planar
interface and exchange loads ONLY through identified interfaces (M01 region
ports): a declared unilateral penalty contact (pressure p = k_c * max(0, -g),
k_c = 1.0e5 Pa/m; per-triangle traction area-scaled and bitwise reciprocal)
and a declared tension/shear/twist bond element (k_t = 60 N/m, k_s = 40 N/m,
k_theta = 0.8 N*m/rad, transfers = force_moment) bound between declared port
pairs. Release removes ALL bond restoring forces bitwise (force and stored
energy exactly 0.0, not small), dissipates the bond's stored elastic
energy as a reported ledger term, and permits separation except for
remaining contact (the run ends contact-loaded with the bond absent).
Bonds are created ONLY by an explicit bind; proximity, overlap and
containment never bond (named refusal `auto_bond_refused`). Shared faces
are counted once in the combined inventory and matter mass is counted once
via M01 owner/reference roles. Every interface transfer is equal/opposite
in loads AND moments, checked per tick from three origins.

Upstream authority reused verbatim, unmodified: M01 `material_state.py`
(validator sha256 b6b009713daa4b31...),
M03 `pressure_membrane.py` (closure/lumping/XPBD scaffold pattern, sha256
3dd64f6465430380...), M04 `passive_response.py` (strain-gate/ledger
discipline as style reference).

## Verification (receipt: qualification_receipt.json, 19 of 19 checks PASS)

- T0 M01 gate: the bound revision validates with region_count 2, port_count 4,
  matter_count 3, owner_count 3, reference_count 1, total_mass 0.072 kg,
  contact_count 1, bond_count 1; the released revision re-validates with
  bond_count 0 while the contact relation persists.
- T1 geometry: interface triangles 1.000e-02 / 7.500e-03 m^2 (derived 0.5*|cross| of the
  declared coordinates), shared face 1.750e-02 m^2, body volumes 9.333e-04 m^3,
  normals bitwise +-x, anchors bitwise coincident at gap 0.
- T2 contact reciprocity at 0.5 mm penetration: traction pairs bitwise
  negative, per-triangle force ratio 1.333333333333 (area ratio 4/3), net force
  bitwise zero, torque worst 0.000e+00 N*m.
- T3 bond element: never-bound refuses `bond_not_bound`; tension at e=0.024 m
  1.440e+00 N (k_t*e within 1e-15 relative); twist couple 8.000e-02 N*m; energy
  identity within 1e-16 J; compression exact zeros.
- T4 release: bond force and stored energy bitwise 0.0 at all 13 post-release
  ticks; E_diss_release = 1.840e-03 J equals the bond energy at the previous tick
  (within 1e-18 J); the released document re-validates with bond_count 0.
- T5 no auto-bond: overlap and containment keep bond_count 0; the guard
  raises `auto_bond_refused`.
- T6 once-only inventory: total area = A_rest(a) + A_rest(b) - A_iface
  (1.143e-01 m^2), total mass 0.072 kg with the reference claim not re-counted.
- T7 per-tick reciprocity: summed interface force bitwise zero at all 24
  ticks; torque within the derived couple bound (worst ratio 9.094e-01, tick 20).
- T8 determinism: no stochastic inputs (no seed needed, none used); replayed
  trace canonical sha256 6af3ec6effe95682cf0283e809c9be58c012337fc90169bda959193e3c43a24f equal at both runs.
- T9 dynamics: gap at release tick 1.217e-02 m (bound [0.008, 0.020]), pull-phase
  peak 2.376e-02 m (bound [0.015, 0.045]), post-release peak 3.016e-02 m, max penetration
  -5.907e-03 m, max speed 3.890e+00 m/s, final state loaded with the bond absent;
  |R_tick| within the declared reservoir bound at every tick (worst ratio
  5.879e-01, tick 20), transverse anchor offset worst 2.041e-13 m.
- T10 held-then-separated: bond tension over ticks 7-10 = [0.017, 0.111, 0.264, 0.47] N
  (monotone rising); post-release peak exceeds the release-tick gap by
  1.799e-02 m.

## Falsifier proof (each bite on a tampered copy, observed values in the receipt)

- F1 hidden hinge after removal (card falsifier): real code bitwise zero at
  all post-release ticks; the stale-force tamper leaves 1.506e+00 N
  (detected by the same probe).
- F2 spatial neighbor automatically bonded (card falsifier): real bond_count
  0 with no bind; the tamper carries bond_count 1.
- F3 non-reciprocal transfer: real net 0.000e+00 (bitwise 0); tamper 4.375e-01 N.
- F4 shared double-count: re-own trips `duplicate_matter_owner`; the reference
  double-count shifts mass by exactly 2.000e-03 kg.
- F5 area-independent forces: real per-triangle ratio 1.333333333333 (4/3); tamper
  ratio 1.000000000000 (detected).
- F6 unaccounted energy: dropping the 1.840e-03 J release dissipation leaves
  residual 1.840e-03 J > release bound 9.198e-05 J (bites).

## Visual capture (material/motion profile; task_id "M05")

- 24 frames (2560x840), 1 tick = 1/300 s simulated replayed at 1 video
  second (slow motion x300, declared in every footer); top row diagnostic
  viewports [whole | side | front | close-up] carrying the packet's five
  diagnostic layers, middle row clean (same cameras, no overlays), bottom
  gap / contact-force / bond-tension / energy traces.
- Video: E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-M05\45bc250a82894954b7f7cd61bfae410c\capture\capture\capture_mat2_m05_interface_20260928.mkv (attempt workspace),
  sha256 cfc58c5eced1960b2b2c4641662d25baa65f8e8cfeb315b4a411583c0cbcdab5, h264 2560x840, 24 s; the tick-13 decoded frame matches the
  source frame (mean abs pixel diff 1.49, lossy yuv420 only).
- Manifest: chimera.visual_capture_manifest.v1, task_id "M05" (SHORT form),
  profile_id material, profile object READ READ-ONLY from the registry
  (E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3),
  subject_sha256 = sha256(interface_state.json) = c09bdf0564d152fa8b9a41489bd874fd0570f75e40ed3ce848f4c474fd0320c6,
  state_binding = sha256(interface_trace.json) = 2e1a2f483f69c162af43e15e9800ab259b303492d466a85346238db01865d45e,
  capture_sha256 = the mkv sha256 (single on-disk artifact).
  `visual_capture.validate_manifest` returned structurally_valid=True (6 views,
  diagnostic+clean pairs, fixed_bookmark cameras with fully declared fields,
  required subject visibility declared).
- Pixels inspected (not inferred from filenames): tick 3 shows the squeeze
  (contact loaded, equal/opposite area-scaled arrows), tick 10 the held
  phase (bond strap + tension arrow T=0.47 N), tick 13 the release (strap
  gone, "bond RELEASED", separation 23.76 mm), tick 21 the re-loaded contact
  with NO bond ("proximity never bonds"), clean rows clean.

## Honest limits

- XPBD edge constraints are a demonstration scaffold, not a qualified constitutive
  model; body B is integrated as translational vertex masses — rotational body
  dynamics are NOT modeled; the bond twist/shear couples are exercised as exact
  element laws under declared inputs and the moment transfer is proven by exact
  reciprocity, not by a tumbling body.
- Contact is a declared unilateral penalty law with finite penetration (peak
  -5.907e-03 m under the 6 N approach); no friction cone, no adhesion.
- The bond is tension-only along its axis with declared linear shear/twist; no
  strength-based failure criterion is modeled beyond the explicit release, and
  the release dissipates the bond energy by declaration (no snap-back whip).
- Body A is a declared fixed support (visible stand) — never a hidden constraint.
- The renderer is a CPU rasterizer with painter's-algorithm depth (declared
  occlusion_mode depth_tested); it displays solver state, not a GPU render.
- Visual acceptance of the capture remains with the independent reviewer;
  validate_manifest is camera-metadata structure only.

## Corrections issued before the receipt (all pre-receipt, documented in
PREREGISTRATION.md with the triggering observations)

A1 re-issued port kinematics (material-point anchors after the deformed-
centroid anchor tripped the tilt guard), fixed an actuator-direction bug,
added the second base diagonal, per-substep projection, trapezoid work,
scaffold strain reservoir, 32 substeps, c_n 5->12 N*s/m, c_v 2->8 1/s,
schedule (release tick 11, approach from 14) and the reservoir-based residual
bound with the 5%-of-release rule (kept falsifier F6 biting). A2 fixed tick
indexing, re-issued the torque bound as the derived couple product, and
named the never-bound refusal. A3 re-issued two below-one-ulp bounds (T1
areas against the derived closed form; T3 energy 1e-16 J). A4 fixed the
degenerate axis-aligned plane cameras and the pixel budget.

## Durable lessons

1. An interface ledger over a position-based (XPBD) solver must carry the
   constraint-solve artifact honestly: the residual scale is the reservoir it
   exchanges with, NOT a fraction of turnover — four bound shapes were
   falsified by bring-up before the reservoir form closed every tick.
2. Equal/opposite force pairs at slightly different points are a real net
   couple, not an error: the per-tick torque check had to be bounded by the
   measured transverse port offset times the pair force (derived), or an honest
   run looks dishonest.
3. Ports are material points: anchoring interface geometry to a deforming
   face centroid wobbles under one-sided loads and can trip guards; rest anchor
   + mean body translation is stable and honest.
