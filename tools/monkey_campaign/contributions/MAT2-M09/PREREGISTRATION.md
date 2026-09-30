# MAT2-M09 PREREGISTRATION — frozen before implementation and before any measurement

Frozen: 2026-09-29Z, before authoring assembly.py, run_experiments.py,
test_assembly.py, kernel_mirror.py, resident_bones.py, render_run.py,
make_capture.py, make_report.py or lint_report_numbers.py; before any
experiment run, any GPU mailbox job for this card, and any capture code or
frame. Task: MAT2-M09 / planning id M09 — "Demonstrate loose bones assembled
by physical connective matter" (criteria sha256
803ca2d1cd6e410217fb9e3a2bdb8e29fbe291ae2fe685fcfb83f66b442dacc4, attempt
fa6dbcc82b2f4f4c9036bc6c8227b241, arrival agent id `chimera-worker`,
registry dispatch 2026-09-29, board 44/95, M08 closed as PR #267 at
b3490ecd).

done_when (verbatim): "Two independent bone shapes fall separately, are
constrained by authored ligament/capsule/contact material, and become
independent again when all connecting material is removed. Any reduced
constraints derive from those connections and vanish with them; no free
hidden anatomical hinge."

Card task falsifier (verbatim, registry spec.falsifier + ontology task):
"Unbound media, clipped load path, hidden constraint/support, area-independent
triangle forces, overlay-driven motion, or unaccounted energy prevents
acceptance." Ontology task falsifier (verbatim): "Removing tissue leaves an
unexplained skeletal constraint or joint-axis pose writer."

Port contract (verbatim): "Bone surfaces + tissue interfaces -> emergent
allowed motion and load transfer; reductions declare equivalent boundary
response."

## Base and reconciliation (read-only, done before this freeze)

- Canonical startup assigned slot branch-1, prepared checkout head
  c525b82c7c3ce0128565424764293a3c85811ab3 (origin/branch-1). The sealed line
  is origin/astra/gait-capture; the local attempt branch was re-pointed to
  b3490ecda8265468fea7e4a28a76fa7cc44a3cb8 (= merge of PR #267, the MAT2-M08
  winner), which carries the MERGED winners of every dependency:
  MAT2-M05 (explicit contact/bond/release interfaces), MAT2-M06 (local
  triangle contact, finite sliding) and MAT2-M08 (resident GPU passes) —
  the same base-advance move the sealed M08 freeze records.
- Dependency input pins verified in this checkout before this freeze (frozen
  inputs; a mismatch at run time refuses `input_pin_drift`):
  - MAT2-M01/material_state.py sha256
    b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40
    (chimera.material_state.v1 validator; schema authority; used UNMODIFIED),
  - MAT2-M03/pressure_membrane.py sha256
    3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e
    (Membrane closure/area/normal utilities for the bone scaffolds; used
    UNMODIFIED),
  - MAT2-M05/interface_exchange.py sha256
    295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9
    (the sealed contact/bond/release interface authority: bind/release
    status machine, bitwise post-release zero, refusal codes,
    reciprocity law, distribute-to-interface pattern; reused via declared
    subclasses — see law 4/5 — plus M05's scenario-class interface reuse),
  - MAT2-M06/local_contact.py sha256
    1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc
    (sweep-and-prune, triangle-triangle closest features, Coulomb
    stick/slip impulse solve, pinned-body anchor reactions, ledger
    identity; used UNMODIFIED — the contact material path).
- Reconciled gap this card fills: M05 proved TWO bodies can exchange
  contact/bond loads through IDENTIFIED interfaces and that release removes
  them bitwise; M06 proved LOCAL triangle contact with finite sliding;
  neither assembled a joint out of connective material between two FREE
  falling bones, and no module demonstrates that the resulting constraint
  reduction is DERIVED (exists only while the material exists). M09 adds
  exactly that demonstration — nothing inside any upstream file is modified.
- House standards attached at the candidate commit: IMPLEMENTER_CHECKLIST.md
  gates G1-G9 and TOOLKIT.md patterns P1-P9 (both cited in the PR body and
  the report).

## Frozen statement

Two bone-shaped XPBD scaffold bodies (declared DIFFERENT shapes and masses,
"bone_a" the rod and "bone_b" the tapered wedge) fall separately onto a
declared pinned ground (phase A), are assembled by AUTHORED connective
material — one ligament element and one capsule element created by explicit
bind calls between declared ports, plus the local triangle CONTACT material
between their head faces (M06, unmodified) — under a declared load schedule
(phase B), and become independent again when an explicit release removes ALL
bond-type connective material bitwise (phase C; remaining ground contact and
remaining incidental bone-bone contact stay physical, M05 law 4 heritage).
Every reduced constraint is DERIVED per tick from the active connection
elements into a declared restraint record; it is a MEASUREMENT ONLY (it
never applies force — AST-probed) and vanishes bitwise with the connections.
No joint, hinge, axis or pose-writer element exists anywhere in the module.

Upstream authority, reused verbatim and unmodified: M01 validator, M03
Membrane utilities, M06 local contact (all imported, hash-pinned). M05
heritage is reused at two declared granularities: (a) the interface DISCIPLINE
(bind/release status machine, named refusals, bitwise post-release zero,
e_release capture at the release tick, reciprocal load pairs applied at
identified ports, once-only inventory, distribute-to-interface vertex loads,
no-auto-bond guard) is inherited by declared subclasses of the sealed
`BondElement` — the subclasses override ONLY the direction/force/energy
methods for 3-D port geometry and inherit bind/release/refusals verbatim;
(b) M05's `ContactInterface`/`TwoBodyRun` remain the sealed two-body precedent
this card cites (not imported: M09's contact material is M06's local triangle
contact, per the card brief "M05 interfaces through M06 contacts").

## Frozen declarations (constants; declared BEFORE measurement)

Units: SI (m, N, Pa, kg, J, s). Gravity g = 9.80665 m/s^2 along -z (M03/M07
pin). Tick dt = 1/300 s (300 Hz pin); N_SUB = 4 substeps per tick (M07 pin).
All arithmetic float64; NO float atomics; no RNG; no wall-clock in trace or
receipt. Deterministic; byte-identical fresh reruns (X2).

1. Ground: pinned M06 shell body ("ground"), midsurface plane z = -0.001,
   rectangle 0.60 m (x) x 0.40 m (y) as two triangles (12 vertices form a
   2-triangle quad: corners (+-0.30, +-0.20, -0.001)), thickness 0.002 m,
   friction (mu_s, mu_k) = (0.7, 0.5). THE ground is the declared visible
   support of the whole rig; no bone is pinned, mounted or held by anything
   else (hidden-support falsifier arm FB3).
2. Bone A ("bone_a", the rod): closed pentahedron-prism, length 0.18 m along
   x from x = -0.24 to x = -0.06; head face at x = -0.06 is the trapezoid
   (y, z): (0, 0), (0.05, 0), (0.035, 0.03), (0, 0) relative to its face
   origin (y0, z0) = (-0.025, 0.040); tail face congruent at x = -0.24.
   8 vertices, 12 triangles (head 2, tail 2, sides 8; outward winding
   asserted by M03 closure). Head-face triangle areas (derived 0.5*|cross|):
   A1 = 7.5e-4 m^2, A2 = 5.25e-4 m^2 (UNEQUAL, ratio 10/7); face area
   1.275e-3 m^2; volume (prism) = 2.295e-4 m^3; mass 0.030 kg (declared
   demonstration matter, mass/8 per vertex). Scaffold friction (0.4, 0.3).
3. Bone B ("bone_b", the tapered wedge): head face at x = +0.06 (normal -x)
   is the trapezoid (y, z): (0, 0), (0.04, 0), (0.028, 0.024), (0, 0)
   relative to (y0, z0) = (-0.02, 0.022); tail face at x = +0.18 is the
   REDUCED trapezoid (0, 0), (0.028, 0), (0.02, 0.02), (0, 0) relative to
   (y0, z0) = (-0.014, 0.022). 8 vertices, 12 triangles. Head-face areas
   B1 = 4.8e-4, B2 = 3.36e-4 m^2 (ratio 10/7; face area 8.16e-4 m^2); tail
   face area 4.8e-4 m^2; volume (linear taper, closed form (A_head +
   A_tail)/2 * length) = 7.776e-5 m^3; mass 0.018 kg (mass/8 per vertex).
   DIFFERENT shape and mass from bone A (the "two independent bone shapes"
   clause). Scaffold friction (0.4, 0.3).
4. Initial state: both bones zero velocity, at the declared heights above
   the ground top surface (z = 0): bone A bottom z = 0.040 m, bone B bottom
   z = 0.022 m; 0.12 m head-to-head gap (face plane distance), 0 m overlap.
   Free fall under g with M06 local contact (thickness-inflated midsurfaces).
5. Declared schedule (one continuous 90-tick run, ticks 0..89):
   - ticks 0..44 phase A "loose": no connective material exists; the bones
     fall separately, contact the ground (B first — lower height), and
     settle. bond_count stays 0; bond forces bitwise 0 (T5).
   - tick 45 BIND (the authored assembly act, explicit): ligament L1 and
     capsule C1 are created ONLY by named bind() calls on declared ports.
     Port:head of each bone = the head-face centroid (material point, tracked
     by rest anchor + mean body translation — M05 correction A1 heritage).
     Port:capsule of each bone = the declared shank point 0.03 m behind its
     head face along the bone axis (head-face centroid -/+ (0.03, 0, 0)).
     L1 ("ligament:strap_l1", bone_a port:head <-> bone_b port:head): the
     sealed M05 bond interface subclassed; tension-only along the current
     port axis, rest length FROZEN AT BIND to the measured anchor distance
     (~0.12 m), k_t = 30 N/m, transverse shear restoring k_s = 40 N/m,
     transfers = 'force'. C1 ("capsule:sleeve_c1", bone_a port:capsule <->
     bone_b port:capsule): the sealed M05 bond interface subclassed with a
     declared BIDIRECTIONAL axial law (tension AND compression, k_c = 12 N/m,
     declared soft sleeve), transverse shear k_cs = 8 N/m, rest length frozen
     at bind (~0.18 m), transfers = 'force'.
   - ticks 45..54 approach: NO actuator; the ligament's own bind tension
     (~3.0 N derived: k_t * (0.12 - 0.02)) draws bone B toward bone A; the
     head faces meet and the M06 contact material first loads.
   - ticks 55..69 press: the faces rest loaded (contact impulses + capsule
     compression ~1.4 N derived at the contact pose; ligament slack bitwise).
   - ticks 70..79 pull: declared actuator on bone B, equal share per vertex,
     F = +3.0 N along +x (AWAY from A): contact opens (unilateral, no
     adhesion), the ligament engages (derived equilibrium ~0.137 m, tension
     ~3.5 N) and HOLDS the pulled bone — the assembled state constrains.
   - tick 80 RELEASE (explicit, the removal act): L1 and C1 released via the
     inherited sealed release() law — from this tick both contribute EXACTLY
     bitwise-zero force and energy; the stored elastic energy at the release
     tick is declared DISSIPATED by the release mechanism (E_diss_release,
     M05 law 4 heritage); both bond relations are REMOVED from the emitted
     material_state document (M01 re-validation bond_count 0).
   - ticks 80..89 independent: the SAME +3.0 N pull continues; nothing holds
     bone B (only ground friction + declared damping); the gap blows past the
     held equilibrium (T10 contrast).
   - Global declared damping on BOTH free bones: c_v = 120 1/s (velocity
     rescale per substep, M05 measured-dissipation discipline; declared
     demonstration medium; always in the ledger as E_diss_damping).
6. Contact material: M06 local triangle contact, UNMODIFIED — sweep-and-prune
   candidates over swept-inflated triangle AABBs, tri_tri_closest narrow
   phase, solve_contact normal + Coulomb stick/slip impulses (restitution 0,
   beta = 0.2, slop/margin 1e-5, thickness 0.002 m), pairwise mu = min rule,
   Gauss-Seidel over the active set to the declared 1e-12 N*s residual gate
   (cap 32), pinned-ground anchor reactions, per-tick ledger identity
   sum(m dv) = gravity + contact + element + actuator + anchor impulses
   (<= 1e-12). Bone triangles are contacted through declared port adapters
   (one port per bone surface triangle: the rigid cluster of its 3 vertices,
   mean-velocity view, write-through impulse — M07's MembranePort heritage,
   adapted to the bone scaffolds). Contact between bones and between each
   bone and the ground both flow through this one path (no special-case
   joint surface).
7. Derived restraint record (the "reduced constraints derive from those
   connections" clause — MEASUREMENT ONLY, never a force law): per tick, the
   3x3 relative-translation restraint matrix of the pair,
   K = sum over BOUND elements of their directional stiffness at the CURRENT
   port geometry — L1: k_t*[taut]*aa^T + k_s*(I - aa^T) with a = unit
   (anchorB - anchorA) and [taut] = 1 when the ligament is stretched past
   rest, else 0; C1: k_c*aa'^T + k_cs*(I - aa'^T); PLUS the contact
   restraint direction record (the current bone-bone contact normal and
   impulse scale when the faces are in contact). Reported per tick:
   matrix entries, eigenvalue count above the declared 1e-3 N/m threshold
   (restrained_direction_count), and per-element contributions. After the
   release tick the bond contributions are BITWISE zero matrices and the
   count is 0 (T6). An independent in-run recomputation (second code path,
   different summation order) must reproduce K to <= 1e-15 relative. The
   record never feeds any force (AST probe P-AST-restraint).
8. State documents: chimera.material_state.v1 (M01 validator, unmodified)
   emitted at the declared document ticks {0 (loose), 46 (bound), 70 (held),
   90-end bound-state final, 81 (released)}: two bone regions with ports,
   owner matter rows, direction records, declared laws (contact penalty
   N/A — M06 contact is declared in the law list; ligament; capsule),
   the bone-bone contact relation (M01 contact vocabulary state), and the
   bond relations (exactly L1+C1 when bound; absent when released). Bound
   docs validate with bond_count 2; the released doc validates with
   bond_count 0 while the contact relation persists; the loose doc validates
   with bond_count 0 and contact state per the actual gap.
9. Energy ledger per tick (M05 correction A1 discipline, adapted): per tick,
   W_act (trapezoid midpoint-velocity), W_lig, W_cap (trapezoid, per
   substep), Q_damp (measured KE loss of the damping rescale, both bones),
   contact stage measured work w_contact_ke = -(KE_after - KE_before) with
   the friction/impact decomposition recorded (M07 heritage), U_lig + U_cap
   (exact element energies), U_scaffold per bone (sum (|d|-rest)^2/(2*alpha),
   alpha = 1e-5 m/N, M05 heritage), E_diss_release at the release tick,
   E_mech = KE + U_lig + U_cap + U_scaffold(both), and the MEASURED residual
   R_tick = E_mech(t) - E_mech(t-1) - (W_act + W_lig + W_cap - Q_total)
   reported every tick, NEVER hidden, with the declared bound (M05 A1 form):
   |R_tick| <= U_lig(t) + U_lig(t-1) + U_cap(t) + U_cap(t-1)
   + U_scaff(t) + U_scaff(t-1) + 5e-2*turnover + 1e-9, where turnover =
   |W_act| + |W_lig| + |W_cap| + Q_total + KE. At a release tick the release
   account must close to 5% of the released energy:
   |R_tick| <= max(5e-2 * E_diss_release, 1e-12) (keeps FB6 biting).

## Frozen pinned predictions (stated before any run)

- T0 (M01 gates): the loose document validates with region_count 2,
  bond_count 0; the bound document validates with bond_count 2; the held
  and press documents validate; the released document validates with
  bond_count 0 and its contact relation persisting (all under M01's
  UNMODIFIED validate_material_state).
- T1 (geometry, derived identities): head/tail triangle areas bitwise equal
  to 0.5*|cross| of the declared coordinates (A: {7.5e-4, 5.25e-4} m^2,
  B head {4.8e-4, 3.36e-4}, B tail {2.8e-4, 2.0e-4} as decimal
  representations of the derived floats); both bones pass M03 closure
  (closed, oriented outward); volumes match the prism/taper closed forms
  within 1e-18 relative of the divergence-form computed volume; the two
  bones' masses and shapes differ (0.030 vs 0.018 kg; different vertex
  sets).
- T2 (reciprocity, bitwise): at EVERY tick, each ligament/capsule force
  pair is applied at the two port anchors as bitwise negatives; the summed
  contact impulses are bitwise-reciprocal (M06 records); the per-tick
  momentum ledger identity closes per body within 1e-12 N*s and the summed
  pair total is bitwise 0.
- T3 (element laws, exact): ligament tension = k_t*max(0, e) bitwise at
  declared probe extensions; capsule axial force = k_c*e signed (BOTH
  signs exercised: compression during press ticks, tension in element
  tests with declared inputs — M05's declared-absence heritage for signs
  the dynamic schedule does not visit); shear restoring forces bitwise
  k_s * transverse offset; stored energies exact to 1e-16 J.
- T4 (release, bitwise): at every tick >= 80, ligament AND capsule force
  magnitude == 0.0 and stored energy == 0.0 EXACTLY (bitwise, not
  tolerance); E_diss_release at tick 80 == U_lig(79) + U_cap(79) within
  1e-18 J; the tick-81 document re-validates with bond_count 0.
- T5 (no auto-bond / no adhesion): through ALL of phase A, bond_count is 0
  and bond forces are bitwise 0.0 despite decreasing bone-bone proximity;
  bind happens ONLY at tick 45 by the explicit calls; calling bind twice
  refuses `bond_already_bound`; releasing twice refuses
  `release_of_unbound_bond`; requesting force from a never-bound element
  refuses `bond_not_bound`; the explicit guard `refuse_auto_bond()` raises
  `auto_bond_refused`; after release the faces may re-approach ONLY through
  physical contact (no bond re-forms, ever).
- T6 (derived restraint): K reproduces the independent recomputation within
  1e-15 relative at every tick; during press, restrained_direction_count
  >= 1 (capsule axial + contact normal); during pull ticks 70..79, >= 1
  (ligament axial taut); at every tick >= 80 the bond contribution matrices
  are BITWISE zero and restrained_direction_count is 0 (remaining ground
  contact and any incidental face contact are reported as remaining-contact
  records, never as bond-derived restraint).
- T7 (dynamics bounds, derived then frozen): first bone-ground contact tick:
  bone B in [17, 24], bone A in [24, 31] (derived sqrt(2h/g), separate
  heights — the bones fall SEPARATELY, B before A by >= 3 ticks); first
  bone-bone contact tick in [46, 65] (bind-driven approach with declared
  damping, wide window, honest); during press (tick 69): bone-bone midsurface
  gap <= 1e-3 m and at least one tick in [55, 69] carries a positive normal
  contact impulse; during pull (tick 79): ligament tension > 1.0 N, bone-bone
  gap > 1e-3 m (contact opened, no adhesion) and gap < 0.10 m (HELD); at
  tick 89: gap > gap(79) + 0.02 m (blown past the held equilibrium —
  INDEPENDENT) with bond forces bitwise 0 on all of [80, 89]; max bone speed
  <= 4.0 m/s; no NaN/inf anywhere (refusal `nonfinite_state`).
- T8 (determinism): the full 90-tick run replayed twice produces
  byte-identical canonical JSON traces (equal sha256); the render replay
  asserts per-tick equality with the committed trace at 1e-15.
- T9 (energy ledger): |R_tick| within the declared law-9 bound at every
  tick; the release-tick account closes within max(5e-2 * E_diss_release,
  1e-12).
- T10 (held-then-independent, the visible_result clause): the assembled
  phase visibly HOLDS the pulled bone (ligament tension > 1.0 N at tick 79
  with the gap bounded < 0.10 m) and the released phase visibly frees it
  (gap(89) - gap(79) >= 0.02 m, bond_count 0, bond force bitwise 0);
  phase A shows the two bones falling separately (first-contact ticks
  differ by >= 3).

## Frozen falsifier arms (each bitten on a TAMPERED COPY, discarded after; each arm runs its CLEAN CONTROL FIRST in the same executable with a named premature guard)

- FB1 "hidden hinge survives removal" (card + ontology falsifier): tamper =
  a stale restraint edge survives the release (the released ligament keeps
  applying its restoring force — the M05-F1 heritage bite, and the exact
  "unexplained skeletal constraint" the ontology names). Probes that PASS
  clean must FAIL tampered: post-release bond-force bitwise zero becomes
  a residual >= 1e-3 N; the derived restraint matrix stays nonzero;
  gap(89) stays pinned near the held equilibrium (independence lost).
  Guard `m09_fb1_premature`.
- FB2 "unbound media" (profile falsifier): tamper = the rendered geometry
  is offset +0.05 m from the solver snapshot. The render binding assertion
  (rendered vertex arrays must reproduce the snapshot's own state scalars
  before any pixel is written) must refuse `render_unbound_to_state` on
  the tampered copy and pass clean. Guard `m09_fb2_premature`.
- FB3 "hidden support / clipped load path" (profile falsifier): tamper =
  the ground anchor reaction is dropped from the tick ledger while the
  bones rest on the ground. The M06 ledger identity must refuse
  `ledger_imbalance` on the tampered copy; the clean control closes every
  tick. Guard `m09_fb3_premature`.
- FB4 "area-independent triangle forces" (profile falsifier): tamper = the
  contact-patch load report distributes the load EQUALLY per contacted
  triangle instead of area-scaled (p * mean(a)). The probe requires the
  per-triangle ratio F1/F2 == area ratio 10/7 (within 1e-12) on the clean
  press fixture and detects the tamper (ratio 1.0, resultant point moved).
  Guard `m09_fb4_premature`.
- FB5 "overlay-driven motion" (profile falsifier): tamper = one frame's
  geometry is sourced from a scripted overlay timeline record instead of
  the solver snapshot. The frame-source identity check (every frame's
  source record must be the solver snapshot for that tick, bound by sha)
  must refuse `overlay_motion_detected` on the tampered copy and pass
  clean. Guard `m09_fb5_premature`.
- FB6 "unaccounted energy" (profile falsifier): tamper = E_diss_release is
  omitted from the ledger at the release tick. The release-tick residual
  bound must be exceeded on the tampered copy (M05-F6 heritage); clean
  control within bound. Guard `m09_fb6_premature`.

Tampered copies are constructed in-process from copies of the real objects;
no committed file is modified; every demonstration records the observed
tampered value next to the frozen bound in the receipt rows (P1 row shape:
value, declared tolerance, clean_control {metric_scope, value,
within_tolerance, guard}, bit).

## Frozen experiments (limits fixed before any run)

- X1 full-trajectory CPU run (the authoritative physics, CPU-FIRST): the
  90-tick three-phase scenario at dt = 1/300 s, N_SUB = 4, ALL gates armed
  (momentum ledger 1e-12, energy residual bound, nonfinite refusals,
  element refusal codes, M01 document validations at the declared ticks).
  Writes experiment_trace.json (per-tick rows: gap, contact state/impulses,
  element forces/energies, restraint record, ledger terms, residual,
  state_hash) and experiment_receipt.json (T0-T10 verdicts with values).
- X2 determinism: a second fresh run writes *_rerun2.json; compare mode
  verifies byte-identical trace and receipt (sha256 recorded) and writes
  determinism_receipt.json.
- X3 GPU confirmation (the M08 resident-pass dependency, CONFIRMS physics,
  never debugs it — submitted ONLY after X1/X2 are green): the M09 world
  exists first as kernel_mirror.py (pure numpy, identical statement order)
  validated BITWISE against the CPU world on the frozen fixture; the CUDA
  resident world is its mechanical transcription; the GPU bank runs the
  same 90-tick fixture with resident state and bounded commands/diagnostics
  (telemetry budget: <= 256 B/tick up, <= 1024 B/component/tick down, F1
  heritage), frozen windows: max position difference <= 1e-12 m, scalars
  <= 1e-9 relative (floor 1.0, vacuous identically-zero comparisons refused
  with the self-tested guard), declared-order digest every tick, byte-
  identical fresh reruns. All GPU work EXCLUSIVELY through the mailbox
  (E:/ChimeraWork/gpu-queue per PROTOCOL.md; forward-slash job JSONs; mode
  names verified against the runner's dispatch table; NEW job ids for every
  resubmit). If this worker's window ends before the CUDA transcription or
  its confirmation bank completes, the handoff DISCLOSES X3 as
  frozen-but-not-yet-measured with the mirror status recorded — never a
  silent gap.
- X4 regression: the UNMODIFIED M05 test suite (test_interface_exchange.py)
  and M06 test suite (test_local_contact.py) re-run green in this checkout
  at the exact candidate revision (regression_receipt.json).
- P-probes: P-input-pins (all four pinned hashes re-verified at run time);
  P-AST-restraint (AST scan: the restraint computation writes only its own
  record structure — no assignment to any body/element velocity, position
  or force attribute inside the restraint function); P-AST-no-joint (AST
  scan: no class/function whose name or docstring declares a hinge, joint
  axis, or pose writer — the ontology falsifier made executable);
  P-single-owner (the only writers of physical state are the declared run
  step methods — mirrored M08 probe adapted).

## Frozen verification-profile probes and views (material, motion)

- Views (registry profile object read READ-ONLY from agent_slots.sqlite3
  kanban.cards[MAT2-M09].spec.ontology_qualification.task
  .verification_profile): "whole experiment at fixed distance",
  "orthogonal side and front", "oblique close-up of the loaded interface";
  each rendered as a diagnostic/clean pair (clean_view_required true; clean
  rows carry zero labels, zero diagnostic layers, zero overlay pixels —
  the M05 leak lesson).
- Diagnostic layers (all five, in every diagnostic row): stable
  membrane/triangle/port IDs; pressure and area-scaled force vectors;
  rest/current geometry and material directions; contact/bond state;
  energy/work and simulation tick.
- Camera record: ALL 17 registry camera_required_fields on every view row
  (frame_id, coordinate_unit, position, orientation_convention_and_values,
  target, distance_to_target, projection, vertical_fov_or_orthographic_span,
  near_far_planes, aspect_ratio, viewport_resolution,
  camera_motion_or_bookmark_sequence, visibility_layers, label_ids,
  occlusion_or_xray_mode, state_or_tick_interval). Fixed bookmarks: the
  camera never moves; the SUBJECTS move (right-handed, metres, quaternion
  wxyz camera-to-frame, forward -Z / up +Y, near 0.01 / far 100,
  640x360 per viewport, aspect 16:9).
- Frozen cameras: whole — perspective, vertical_fov_degrees 40, position
  (-0.09, -0.62, 0.34) m, target (-0.03, 0.0, 0.03) m (between the bones;
  distance derived and recorded; whole-scene context); side — orthographic,
  span 0.55 m, position (-0.03, 2.0, 0.03) m looking along -y; front —
  orthographic, span 0.55 m, position (-0.03, 0.0, 2.0) m looking down -z
  (declared secondary with all 17 fields); close-up — perspective,
  vertical_fov_degrees 30, target = the midpoint between the head-face
  centroids, position = target + (0.16, -0.30, 0.22) m (the loaded joint
  interface; distance derived and recorded). Pixel budget: the ortho planes
  give 0.55 m / 360 px = 1.53 mm/px; the T10 release displacement
  (>= 0.02 m) is >= 13 px on the planes — visible motion is derived, not
  hoped for (M03 durable lesson).
- Capture ticks (12, frozen): 0, 10, 19, 27, 44, 45, 52, 60, 69, 79, 80, 89
  (falls, bind, first contact approach, press, end-of-press, held, release,
  independent). One video artifact (single-artifact binding, P8):
  capture_sha256 = the video file's sha256; every view row an
  artifact_locator of kind video on it; identical composite state hash on
  every view row (view toggles preserve the physical state hash);
  task_id SHORT form "M09" in manifest AND context; validate_manifest runs
  with THE registry profile object read read-only from the registry db
  (never hand-copied); registry profile snapshot + provenance written to
  evidence; criteria_sha256 identical across dispatch, registry card,
  this preregistration, and checks identity.
- Encoded-video gate (P4 heritage): decoded frames == committed stills at
  independently recomputable indices under the identity transform ONLY
  (explicit transform list identity/vflip/hflip; non-identity diffs > 0);
  pure-stdlib row-order test with a sensitivity guard; frames are the
  determinism unit.
- Report numbers (P2/P3 heritage): every number in report.md traceable to
  a bound artifact at its printed precision (lint_report_numbers.py with
  --selftest); every qualitative claim about measured or rendered reality
  produced by a probe receipt the generator requires fail-first with named
  refusal codes.

## Applicability boundary (honest, frozen)

An offline CPU experiment executable (plus its declared GPU confirmation
arm) over pinned upstream laws; not the native C++ engine runtime, not a
live renderer, no training. Bones are XPBD scaffold bodies (demonstration
scaffold): rotational dynamics are NOT modeled — twist/torsion restraint is
carried by the declared element laws and element tests (M05's declared
absence heritage), and the scaffold keeps each bone near-rigid through its
edge set. The render is a CPU rasterizer with painter's-algorithm depth
(declared occlusion_mode depth_tested) displaying solver state. The capsule
is a declared soft sleeve element (k_c = 12 N/m), not a biological
capsule model. Global damping c_v = 120 1/s is a declared demonstration
medium (always dissipated in the ledger). Contact friction is Coulomb
stick/slip per M06; no wear, no adhesion. Release dissipates stored
elastic energy by declaration (no snap-back whip modeled). Visual
acceptance of the capture remains with the independent reviewer;
validate_manifest is camera-metadata structure only.

No measured value is quoted in this preregistration; every number is either
an exact identity, a declared scenario constant, or a closed-form
derivation shown with its formula. The original bounds above are superseded
only by a pre-receipt CORRECTION/AMENDMENT recorded in this file with its
triggering observation, never by a silent edit.


## AMENDMENT A1 (pre-receipt, 2026-09-29Z; implementation bring-up, BEFORE the
## frozen receipt run — no receipt numbers were produced or relied on)

Each re-issued item records its triggering observation from the module
bring-up (all gates armed during bring-up, exactly as the CPU-FIRST
discipline requires):

1. DAMPING SCHEDULE (law 5 re-issue): the frozen uniform c_v = 120 1/s gave
   the free fall a 0.082 m/s terminal speed (observed: after 39 ticks the
   bones had fallen 27 mm of their 21-39 mm drops; first ground contact
   would land near tick 250, outside the 90-tick run — the separate-falls
   evidence needs a near-ideal free fall). Re-issued: c_v = 8.0 1/s for the
   loose phase (ticks 0..44; the sealed M05 value) and c_v = 120.0 1/s for
   the bound/released phases (ticks 45..89; the declared assembly medium).
   Always dissipated in the ledger either way.
2. LIGAMENT REST LENGTH (law 5 re-issue): the frozen "rest length frozen at
   bind" ligament produces ZERO bind force (rest = the bind distance), so
   nothing drives the assembly and the pull phase never engages it within
   its window (observed in the bring-up analysis). Re-issued: the ligament
   is a declared SHORT CHECK-REIN with rest length 0.02 m and k_t = 60 N/m
   (the sealed M05 stiffness): the bind act itself pulls the bones together
   (observed bind tension ~5.4 N), and the pull phase engages it after
   0.02 m of separation.
3. CAPSULE ANCHORS (law 5 re-issue): the frozen shank anchors (0.03 m
   behind each head face) make the compressed strut PRY THE JOINT OPEN
   (anchors pushed apart inside the bones) instead of passing load through
   the interface (observed in the bring-up force analysis). Re-issued: the
   capsule is a strut anchored AT the head-face ports (port:head, the same
   identified ports as the ligament), rest length frozen at bind; its
   declared bidirectional law (k_c = 12 N/m) now resists closure and passes
   load through the contact interface exactly like joint cartilage.
4. SCHEDULE (law 5 re-issue): with the honest press dynamics the frozen
   press window could not close the joint (triggering observation: press
   3.0 N over ticks 60..69 left a 12.7 mm head gap at tick 69 — the contact
   material never loaded; the closing crawl is set by the declared damping
   and the capsule's 1.44 N closing resistance). Re-issued: press ticks
   60..74 at 6.0 N toward bone_a; pull ticks 75..89 at 3.0 N away; RELEASE
   TICK 85 (was 80). Bring-up values at the re-issued constants: first
   bone-ground contact ticks bone_b 21, bone_a 30; first bone-bone contact
   tick 66; sustained loaded press ticks 66..74 (joint gap ~1e-3 m at
   tick 74); held at tick 84: ligament tension 1.73 N, contact OPEN (no
   adhesion), gap 0.048 m; release bitwise zero from tick 85; gap(89) -
   gap(84) = 0.0223 m (the released pair blows past the held gap).
5. RESIDUAL FORM (law 9 re-issue): the impact tick exposed the XPBD
   projection's kinetic-energy exchange (triggering observation: tick-30
   residual -7.9e-4 J against a 3.5e-4 J bound, with the scaffold
   reservoir at only 1.7e-6 J — the position-based projection discards
   the impact violation energy within the tick). Re-issued: the projection
   exchange Q_proj (per-tick KE change across the projection stage, both
   bones) is a MEASURED ledger term (M07 e_stab heritage): R = E_mech(t) -
   E_mech(t-1) - (W_act + W_lig + W_cap + W_grav) + Q_damp + Q_contact +
   Q_proj + E_diss_release; the bound form is unchanged. Also re-issued
   per the same bring-up tick: W_grav (gravity work) was missing from the
   frozen residual form and is added (the falling phase residual equals
   the missing gravity work otherwise).
6. CONTACT NARROW PHASE (law 6 declaration): canonical pair order (body_a
   carries the smaller body id) with DECLARED fallback normals for the
   dist == 0 overlap case (+x bone-bone, +z bone-ground): the sealed
   triangle-winding fallback was pair-order-dependent (triggering
   observation: deep-overlap resolution at the bind-driven approach could
   pick an order-dependent sign). Entries carry the BODY id so M06's
   sweep_prune excludes same-body pairs (triggering observation: holder
   indices made adjacent triangles of ONE bone contact each other).
7. MOMENTUM LEDGER (law 6 re-issue): the identity is enforced per body per
   substep over stages 1-3 with telescoping recorded deltas (m*(v4-v0) ==
   gravity + damping + element_actuator + contact impulses, <= 1e-12); the
   projection impulse is internal and pairwise (its work is the measured
   Q_proj). The FB3 anchor-consistency gate isolates the ground-transmitted
   impulse by subtracting the tracked bone-bone impulse total (triggering
   observation: the bone accumulators already contain it, so the frozen
   one-line form double-subtracted).
8. T0/T4/T7/T10 RE-ISSUE at the re-issued schedule: document ticks
   {0, 46, 70, 86, 89} with bond counts {0, 2, 2, 0, 0}; bitwise zero bond
   force and energy on ticks 85..89 with E_diss_release == U_lig(84) +
   U_cap(84); first bone-ground contact ticks bone_b in [17, 24], bone_a in
   [24, 31] (differ by >= 3); first bone-bone contact tick in [46, 74]; at
   tick 74 the joint contact is loaded (positive accumulated normal
   impulse) with joint gap <= 1e-3 m; at tick 84 the ligament tension
   exceeds 1.0 N with the joint contact OPEN and gap < 0.10 m; at tick 89
   the gap exceeds the tick-84 gap by >= 0.015 m with bond forces bitwise
   zero on all of [85, 89]; max bone speed <= 4.0 m/s; restrained
   direction count >= 1 on every bound tick and 0 with a BITWISE zero
   restraint matrix on every tick >= 85.


## AMENDMENT A2 (X3 status; correction round 2026-09-29Z, attempt
## fa6dbcc82b2f4f4c9036bc6c8227b241 — recorded BEFORE any GPU submission)

1. X3 CPU-FIRST MIRROR (measured, green): kernel_mirror.py is written and
   validated BITWISE against assembly.AssemblyRun on the frozen 90-tick
   fixture: every row value, both state_hash chains, all vertex
   trajectories/velocities and the declared-order diagnostic block fold
   agree with worst difference 0.0 (receipt mirror_rehearsal_receipt.json,
   schema chimera.m09_mirror_rehearsal.v1; the rehearsed oracle trace is
   sha256 273dbc4f8c73a6f5..., the frozen X2 trace itself). The mirror is
   the single transcription source for the resident CUDA world and fixes
   its declared layout (flat 16-row state, 26 contact entries, per-bone
   96-f64 diagnostic block, 5-f64 command block, the declared comparable
   slots). Triggering observations from the mirror bring-up, all caught by
   the bitwise rehearsal and none shipped: (a) the per-substep work/
   damping partials must fold in the oracle's interleaved substep-then-
   bone accumulation order — a bone-major fold diverged in the last bit
   from tick 6; (b) the port views must share the world's single state
   owner and the stages must write in place — private port views went
   stale at the first ground contact (tick 21) and missed the contact set
   entirely.
2. RESIDENT CUDA TRANSCRIPTION + CONFIRMATION BANK: NOT COMPLETED in this
   window; the started transcription was WITHDRAWN rather than committed
   untested (the GPU-only debug path makes an unvalidated kernel file on
   this physics branch a liability; M08 lane heritage). Per the X3
   disclosure clause the arm stays frozen-declared and NOT measured — a
   disclosed gap, never a silent one. No bound changed: the frozen
   windows (1e-12 m positions, 1e-9 relative scalars, telemetry budgets,
   declared-order digest, byte-identical fresh reruns) still govern the
   future bank exactly as frozen above.
3. CPU-FIRST LAW held: no GPU submission was made. The CPU baseline was
   re-verified byte-identical at this revision before any mirror work
   (X1 main run reproduced the committed trace/receipt bytes; X2 rerun
   byte-identical, sha256 273dbc4f8c73a6f5...).

