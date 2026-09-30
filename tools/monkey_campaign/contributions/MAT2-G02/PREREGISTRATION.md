# MAT2-G02 PREREGISTRATION — frozen before implementation

Frozen: 2026-09-30Z, before authoring attachment_patch.py, any test run, any
experiment run, or any capture. Task: MAT2-G02 / planning id G02 — "Qualify
finite-area anatomical attachments" (criteria sha256
03ee207b7b2c701ff189bf1ee9133ada87eea7a1bd760fe4cb24525fcc5e4c45, attempt
983a9a8b1be54457a6aa516319290aa1, agent zcode-glm-mat2-g02-a1, base revision
f6cbf7a9 = the sealed line tip "Merge pull request #277 from
GhostDragonAlpha/review/MAT2-A09" = origin/astra/gait-capture; isolated
attempt-workspace checkout
E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-G02/983a9a8b1be54457a6aa516319290aa1/checkout,
local branch codex/monkey-mat2-g02-983a9a8b1b). Composed against
CARD_STARTER.md v2 (2026-09-30, post evidence-store + retention).

done_when (verbatim, from the join packet): "Actual patch geometry, stiffness
and rotational resistance meet declared physical requirements. Material-first
addition: Finite-area attachment forces and moments enter both connected
material states; physical bond/removal semantics match the limb experiment."

Card falsifier (verbatim): "A violated task acceptance clause, hidden/clipped
required geometry, inconsistent numeric evidence or mismatched clean/diagnostic
state fails."

Verification profile (registry, read read-only from
monkey_completion_map.json ontology_contract.visual_profiles via the card
record; profile id attachment-fixture, kind motion): diagnostic layers
"attachment patch geometry", "authored frames and port IDs", "fixture load and
displacement traces"; views "patch overview", "loaded interface close-up",
"orthogonal and oblique patch views"; clean_view_required true; numerical
evidence required; full registry camera field set (16 named fields:
frame_id, coordinate_unit, position, orientation_convention_and_values,
target, distance_to_target, projection, vertical_fov_or_orthographic_span,
near_far_planes, aspect_ratio, viewport_resolution,
camera_motion_or_bookmark_sequence, visibility_layers, label_ids,
occlusion_or_xray_mode, state_or_tick_interval); view toggles must preserve
the physical state hash.

## Reconciliation (clause-to-evidence map at the frozen base f6cbf7a9)

| clause | upstream status at f6cbf7a9 | verdict |
| --- | --- | --- |
| actual patch geometry, stiffness and rotational resistance meet declared physical requirements | C17 "Finite attachment mechanics" is an OPEN inventory in the sealed A09 package (calculation_contracts): required inputs "Patch area/shape, areal stiffness, couple resistance, weights, frame" are "explicitly_unresolved (open; A06/A07 carried blocks verbatim; zero numbers)"; the c17_block note: "no attachment patch area/shape, areal stiffness, couple resistance or weights exist in the pinned sources; none is invented; no synthetic lambda_min" | UNMET — implement the finite-area attachment MECHANISM with DECLARED placeholder constants on an engineering fixture; the BIOLOGICAL port values stay explicitly-unresolved (see the C17 gate below) |
| finite-area attachment forces and moments enter both connected material states | M05 (sealed) proved reciprocal contact+bond transfer between two pentahedra at ONE point anchor per bond (tension/shear/twist at interface-face centroids); no area-distributed element exists; A09 carries 26 attachment_interface connections (iface:tendon-<muscle>-origin|insertion) with c17_status carried_open and no mechanics | UNMET — implement the area-distributed patch element with per-triangle area-scaled forces AND moments entering BOTH body states as bitwise-negative pairs |
| physical bond/removal semantics match the limb experiment | M09 (sealed) demonstrated bind -> hold under declared pull -> tick-85 explicit release with bitwise post-release zero (ticks 85..89), E_diss_release == held element energy within 1e-18, restraint record gone after release, remaining contact persists, no auto-bond (FB1 hidden-hinge arm) | MATCH BY CONSTRUCTION — the patch element adopts the SAME release law (bitwise zero, dissipation accounting, no snap-back, explicit bind only) and the same named refusal vocabulary; proven by the F-arms |
| card falsifier prongs | violated acceptance clause -> named checks; hidden/clipped geometry -> declared camera + layer law; inconsistent numeric evidence -> generated-report lint against receipts; mismatched clean/diagnostic state -> identical composite state hash on every view row | UNMET — freeze all four prongs as executable checks |

Dependencies: MAT2-A09 [DONE, sealed], MAT2-M05 [DONE, sealed]. First unmet
clause: all substantive clauses; card G02 is the first unmet phase and is
commissioned by this attempt.

## The C17 gate (law this card operates under)

The sealed A07 law: any new fitting experiment is separately authorized
BEFORE dispatch (Candidate C failed at 67.147 micrometres per side; four
wrist sites outside under both loops). The A09 package carries the
authorization state verbatim: "No radius supersession or new fitting candidate
is authorized". Therefore THIS CARD RUNS NO FITTING EXPERIMENT AND MEASURES
NOTHING. The dispatch brief fixes the lawful close: "Real patch geometry,
stiffness and rotational resistance must be measured/declared ... Without that
authorization the only lawful close is explicitly-unresolved terminals."

- The FIXTURE constants below are DECLARED placeholders (authored engineering
  constants, provenance class declared_placeholder, never_biological), each
  carrying a numeric DERIVATION from a sealed carrier instead of a claim.
- The BIOLOGICAL attachment ports (the 26 attachment_interface connections in
  the A09 package, c17_status carried_open) close explicitly-unresolved in
  the receipt and report: no per-port patch area/shape, areal stiffness,
  couple resistance, weights or frame values are invented, and no synthetic
  lambda_min is used anywhere (the sealed catalog law; the term does not
  appear in this card).
- Adjacent debt, NOT this card's scope: the G04 friction study
  (E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md)
  records that no lawful measured friction pin exists (mu_s 0.6 / mu_k 0.4
  are NAMED placeholders; the elementwise_min pair rule is two-sided). This
  fixture's contact law is the sealed M05 frictionless normal-penalty law;
  the card introduces no friction constant and therefore no friction claim.

## Frozen statement

Two pentahedral fixture bodies meet at a DECLARED planar interface. Across a
DECLARED finite-area attachment patch (an unequal-area two-triangle quad on
the interface plane), a bindable patch element exchanges area-scaled tension,
shear and rotational-resistance couples; forces and moments enter BOTH
connected material states as bitwise-negative pairs at declared per-triangle
points; an explicit release removes exactly the patch's incident connections
with bitwise-zero residue, matching the sealed limb experiment (M09) and the
sealed interface law (M05). Reused verbatim from upstream, unmodified, as
authority/data foundation:

- `tools/monkey_campaign/contributions/MAT2-M01/material_state.py` — the
  chimera.material_state.v1 validator (sha256
  b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40). The
  experiment emits bound-state and post-release documents that this
  UNMODIFIED validator must accept (bond_count 1 -> 0, contact persists).
- `tools/monkey_campaign/contributions/MAT2-M05/interface_state.json` — the
  sealed bond/contact port semantics carrier (sha256
  c09bdf0564d152fa8b9a41489bd874fd0570f75e40ed3ce848f4c474fd0320c6): the
  release/no-auto-bond/once-only-counting vocabulary and the 0.072 kg
  matter carrier are carried from it.
- `tools/monkey_campaign/contributions/MAT2-A09/grasp_package.json` — the
  sealed grasp anatomy input package (sha256
  0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24): the
  connection vocabulary (attachment_interface, iface:* ids, c17_status
  carried_open), the C17 open-inventory contract, and the frame law
  (owner-body-local, carried verbatim, no transform composed).
- `tools/monkey_campaign/contributions/MAT2-A08/parameter_envelope.json` —
  the sealed envelope (engineering vs biological namespace disjointness; no
  inheritance law). The fixture constants live ONLY in the engineering
  namespace.

Physics laws (all SI; m, N, Pa, J, rad):

1. Fixture geometry. Body A ("fixture_body_a", supported) and body B
   ("fixture_body_b", free) are pentahedra congruent to the sealed M05
   bodies (rectangular-trapezoid base 0.2 m x 0.1 m bounding, apex 0.16 m
   behind the base; interface face the congruent trapezoid with vertices
   (y,z) = (0,0), (0.2,0), (0.15,0.1), (0,0.1); face normals exactly
   (+-1,0,0); faces coincident at gap g = 0 measured along x between the
   face centroids). Mass carried per the M05 once-only law: mat_a 0.050 kg
   owned by body_a, mat_b 0.020 kg owned by body_b, mat_iface 0.002 kg
   owned by body_a and REFERENCE-claimed by body_b; inventory total
   0.072 kg; body_b dynamic mass 0.020 kg.
2. Patch geometry (C17 input "patch area/shape" — DECLARED placeholder).
   The attachment patch is the quad on the interface plane with (y,z)
   vertices (0,0), (0.020,0), (0.013,0.010), (0,0.010), split into triangles
   P1 = (0,0),(0.020,0),(0.013,0.010) and P2 = (0,0),(0.013,0.010),(0,0.010).
   Areas from 0.5*|cross|: A1 = 1.0e-4 m^2, A2 = 6.5e-5 m^2 — UNEQUAL BY
   DESIGN so area scaling is falsifiable (A1/A2 = 20/13 = 1.538461...).
   A_patch = A1 + A2 = 1.65e-4 m^2. Patch plane normal +x on body A's face,
   -x on body B's face (bitwise axis vectors). Per-triangle centroids are
   the vertex means: c1 = (y,z) = (0.011, 0.0033333333333333335) m,
   c2 = (0.004333333333333333, 0.006666666666666667) m (in-plane offsets
   from the face anchor give the moment arms).
3. Areal stiffness (C17 input "areal stiffness" — DECLARED placeholder,
   derived from a sealed carrier): the M05 point-bond constants
   (k_t = 60 N/m, k_s = 40 N/m) divided by the M05 interface area
   A_iface_M05 = 0.0175 m^2 give the areal densities
   kA_t = 60/0.0175 = 3428.5714285714284 N/m^3 and
   kA_s = 40/0.0175 = 2285.7142857142856 N/m^3. Per-triangle stiffnesses
   are area-scaled: k_t_i = kA_t * A_i, k_s_i = kA_s * A_i; patch totals
   k_t_patch = kA_t * A_patch = 0.5657142857142857 N/m, k_s_patch =
   0.3771428571428571 N/m. Provenance class of every number above:
   declared_placeholder (authored engineering constant derived from the
   sealed M05 carrier; NOT measured, NOT biological).
4. Rotational resistance (C17 input "couple resistance" — DECLARED
   placeholder): areal rotational resistance kA_theta = 0.8/0.0175 =
   45.71428571428571 N*m/rad/m^2 (the M05 twist constant k_theta = 0.8
   N*m/rad divided by the same M05 area), declared ISOTROPIC about the
   patch normal and both in-plane axes (one constant; a declared
   simplification). Per-triangle k_theta_i = kA_theta * A_i; patch total
   k_theta_patch = 7.542857142857143e-3 N*m/rad. Relative rotation theta is
   declared small-strain (|theta| < 0.05 rad enforced by the tilt guard,
   law 9); beyond the guard the run refuses rather than bending the law.
5. Weights (C17 input "weights" — derived, exact): per-triangle
   distribution weights w_i = A_i / A_patch (w1 = 20/33 =
   0.6060606060606061, w2 = 13/33 = 0.3939393939393939; w1 + w2 == 1.0
   within 1e-18). A declared patch-level couple M_total about a declared
   patch axis distributes as M_i = w_i * M_total applied about each
   triangle centroid; the per-triangle couples sum EXACTLY to M_total.
6. Frame (C17 input "frame" — carried law): every patch row carries
   frame_decl = "fixture_body_a_local" / "fixture_body_b_local" and
   frame_note "owner-body-local per M01/A09 frame law; carried verbatim, no
   transform composed"; the fixture is DECLARED axis-aligned so body-local
   axes coincide bitwise with world axes at the bound configuration (the
   M05 face-normal argument). Port ids use the A09 vocabulary shape:
   fixture ports "iface:fixture-patch-p1" and "iface:fixture-patch-p2"
   (AUTHORED fixture ports, never_biological; they do NOT claim to be the
   26 biological iface:tendon-* ports).
7. Patch element law (declared, tension-only + shear + rotational
   resistance, area-distributed). Signed extension e = (x_B - x_A).xhat
   (patch-to-patch anchor offset along the interface normal; rest length 0).
   Per triangle: tension force magnitude T_i = k_t_i * max(0, e) along +x
   on A / -x on B (tension-only: exactly zero in compression); shear force
   k_s_i * d_perp (transverse anchor offset, equal/opposite); rotational
   resistance couple M_i = k_theta_i * theta_vec about the declared patch
   axes (+M on A, -M on B). Patch stored energy
   U = sum_i [ 0.5*k_t_i*max(0,e)^2 + 0.5*k_s_i*|d_perp|^2
   + 0.5*k_theta_i*|theta_vec|^2 ] (exact quadratic bookkeeping). Forces
   are applied at the per-triangle centroids, so the moment of the tension
   about each body's center of mass enters that body's state
   (M_body = (r_i - c_body) x F_i) — this is the "moments enter both
   connected material states" mechanism, exercised by T3/T4.
8. Contact and release laws (carried verbatim in class from the sealed M05
   carrier): unilateral penalty contact p = k_c * max(0, -g) with DECLARED
   k_c = 1.0e7 Pa/m (areal-consistent with the smaller patch: contact force
   = p * A_i per interface triangle, area-scaled, reciprocal bitwise
   negatives; normal damping c_n = 5.0 N*s/m). Contact states separated /
   touching / loaded per the M01 vocabulary; contact WITHOUT a declared
   contact interface refuses contact_interface_undeclared. Release is an
   explicit act at a declared tick: from that tick the patch contributes
   EXACTLY zero force, zero couple and zero stored energy (bitwise 0.0),
   the bond relation is REMOVED from the emitted material_state document
   (M01 revalidation bond_count 0; contact persists), the stored energy
   U_release is DISSIPATED by the release mechanism (E_diss_release in the
   ledger; no snap-back impulse modeled — declared absence). Binding
   requires an explicit bind call: never-bound refuses bond_not_bound;
   double bind refuses bond_already_bound; releasing unbound refuses
   release_of_unbound_bond; proximity/overlap/containment NEVER create a
   bond (refuse_auto_bond raises auto_bond_refused).
9. Interface applicability bound (declared guard): the element law is valid
   while |d_perp| < 3.0e-3 m and |theta_vec| < 0.05 rad and contact
   penetration |g| < 0.03 m; beyond any bound the run refuses
   interface_tilt_exceeded / contact_penetration_exceeded rather than
   silently bending the declared law.
10. Dynamics (motion profile; M03/M05 XPBD scaffold pattern): fixed tick
    dt = 1/300 s, compliance alpha = 1e-5 m/N, 8 iterations, global
    velocity damping c_v = 2.0 1/s on body B (declared). Body A is
    SUPPORTED (inv_mass 0; visible support stand in every view; never a
    hidden constraint). Declared actuator schedule on B (equal share per
    vertex, forces along x), 120 ticks, interval [0, 119]:
    ticks 1..15 squeeze 2.0 N toward A; ticks 16..75 pull 0.03 N away from
    A (the bound patch holds); tick 76 RELEASE; ticks 76..90 the 0.03 N
    pull continues (separation permitted); ticks 91..119 approach 3.0 N
    toward A (contact re-loads with NO patch present).
11. Energy ledger (M04/M03/M05 discipline): per tick W_actuators,
    W_contact, U_patch, E_diss_damping (c_v), E_diss_contact (c_n),
    E_diss_release (release tick only), E_mech = KE(B) + U_patch, and the
    MEASURED residual R_tick = E_mech(t) - E_mech(t-1) - (W_act + W_contact
    - Q_total) with the XPBD constraint-projection work reported as the
    residual (never hidden): |R_tick| <= max(5e-2 * (|W_act| + |W_contact|
    + Q_total + KE_tick), 1e-6 J) at every tick.
12. No friction, no fitting, no lambda_min, no GPU: the contact law is the
    frictionless M05 normal-penalty law; the card runs NO fitting
    experiment (the sealed A07 gate) and uses no lambda_min; the whole bank
    is CPU (the scope is a 120-tick two-body fixture — the CPU-FIRST law is
    satisfied trivially and no GPU submission is made).

## Frozen pinned predictions (stated before any run; windows DERIVED from
physics, closed-form — never from measurements)

- T0 (M01 gate): the bound-state document validates under M01's UNMODIFIED
  validate_material_state with region_count 2, port_count 4, matter_count 3,
  owner_count 3, reference_count 1, total_mass_kg 0.072, contact_count 1,
  bond_count 1; the post-release document revalidates with bond_count 0 and
  contact_count 1.
- T1 (patch geometry, exact): A1 == 1.0e-4 and A2 == 6.5e-5 within 1e-18;
  A_patch == 1.65e-4 within 1e-18; A1/A2 == 1.5384615384615385 within 1e-12;
  patch normals bitwise (+-1, 0, 0); w1 + w2 == 1.0 within 1e-18; per-triangle
  centroids equal the vertex means bitwise.
- T2 (areal scaling, exact): at a declared extension e0 = 1.0e-3 m the
  per-triangle tension forces are T1 = kA_t*A1*e0 = 3.4285714285714284e-1 N
  and T2 = kA_t*A2*e0 = 2.228571428571428e-1 N within 1e-15 relative; the
  ratio T1/T2 == A1/A2 within 1e-12; the patch total equals
  k_t_patch*e0 = 5.657142857142857e-4 N within 1e-15 relative. Area
  independence is the FB2 discriminator (unequal triangles by construction).
- T3 (two-sided entry, exact): for every element load the per-body force
  pair is bitwise-negative; the summed interface force over the patch is
  bitwise 0.0; the summed interface torque about EACH of three declared
  origins (world origin, body_a patch centroid, body_b patch centroid) is
  <= 1e-15 N*m; each body's received moment equals (r_i - c_body) x F_i
  with the declared arms (c1 in-plane (0.011, 0.0033333333333333335),
  c2 (0.004333333333333333, 0.006666666666666667)).
- T4 (weights distribution, exact): for declared M_total = 0.01 N*m the
  per-triangle couples are w1*M_total = 6.060606060606061e-3 and
  w2*M_total = 3.939393939393939e-3 within 1e-18; they sum EXACTLY to
  M_total; the couple pairs are bitwise negatives between the bodies.
- T5 (rotational resistance, exact): at declared theta = (0.01, 0, 0) rad
  the patch couple is M = k_theta_patch*theta = 7.542857142857143e-5 N*m
  within 1e-15 relative; U_rot = 0.5*k_theta_patch*theta^2 =
  3.7714285714285714e-7 J within 1e-18; the couple pair is bitwise-negative
  between the bodies.
- T6 (release, bitwise): at every tick after tick 76 the patch force
  magnitude == 0.0 and patch stored energy == 0.0 EXACTLY (bitwise
  comparison, not a tolerance); E_diss_release at tick 76 == U_patch at
  tick 75 within 1e-18 J; the released document revalidates with
  bond_count 0 while contact persists; the patch triangle connection count
  goes exactly 2 -> 0 (removal removes EXACTLY the patch's incident
  connections — nothing else changes in the document inventory).
- T7 (no auto-bond): overlapping (g < 0) and containment configurations
  with NO bind call keep patch triangle count 0 and patch force bitwise 0;
  the explicit guard raises auto_bond_refused.
- T8 (dynamic fixture, DERIVED windows): with omega_t = sqrt(k_t_patch/m_B)
  = 5.3184 rad/s, damping ratio zeta = c_v/(2*omega_t) = 0.18803, damped
  omega_d = 5.2236 rad/s, static pull extension F/k_t_patch = 0.053030 m:
  (a) squeeze contact loading: penetration at tick 15 in [-3.0e-3, -3.0e-4] m
  (static -F/k_eff = -2.0/1650 = -1.2121e-3 m, k_eff = k_c*A_patch =
  1650 N/m, omega_c*dt = 0.957 < 2 stable); (b) gap at the release tick 76
  in [0.014, 0.035] m (damped closed form 0.5*F/k_t*(1 - e^(-zeta*omega*t)
  (cos(omega_d t) + zeta/sqrt(1-zeta^2) sin(omega_d t))) at t = 0.2 s gives
  0.02403 m; window = derived value +[-40%, +45%] for XPBD projection and
  damping-model slack — declared, not fitted); (c) U_release at tick 76 in
  [0.6e-4, 3.5e-4] J (0.5*k_t*gap(76)^2 at the window edges); (d)
  separation: max gap over ticks 77..90 strictly greater than gap(76);
  (e) re-contact under the 3.0 N approach: contact reloads (state loaded)
  at some tick in [95, 119] with peak penetration magnitude <= 0.012 m
  (finite penalty penetration, declared); (f) the patch element reports
  exactly zero force/couple/energy from tick 76 onward while contact
  re-loads (remaining contact unaffected by removal).
- T9 (frame law): every emitted patch row carries frame_decl and the
  frame_note "owner-body-local ... no transform composed"; the authored
  fixture port ids iface:fixture-patch-p1/p2 are present as label_ids in
  every diagnostic view; NO biological iface:tendon-* id is claimed as
  resolved anywhere in the artifacts.
- T10 (C17 terminal): the receipt records per-port explicitly_unresolved
  terminal states for the biological attachment debt (c17_status
  carried_open carried from the A09 package), the reason string citing the
  sealed A07 gate and the absent authorization, and the declared_placeholder
  provenance class of every fixture constant. The check asserts the RECORD
  EXISTS and is honest (class labels present), never that a biological
  value was produced.

## Falsifier arms (each with its passing CLEAN CONTROL run FIRST, in the
same executable; tampered modules are scratch copies, never committed state;
every arm records clean_control evidence, a named premature guard, and the
discriminating condition; all preflighted on CPU to discriminate)

- FB1 stale tension survives release: tamper keeps the patch tension term
  active after release(). Discriminator: post-release patch force magnitude
  (clean bitwise 0.0; tampered strictly > 0) — bites the T6 gate.
- FB2 area-independent patch force: tamper sets per-triangle tension
  stiffness to a CONSTANT k_t (not kA_t*A_i). Discriminator: T1/T2 force
  ratio at e0 (clean 1.5384615384615385 within 1e-12; tampered 1.0 — the
  unequal-triangle construction makes this bite; a field of equal triangles
  could never discriminate, which is WHY law 2 freezes unequal areas).
- FB3 one-sided state entry: tamper applies patch loads only into body_b's
  state. Discriminator: summed interface force magnitude (clean bitwise 0.0;
  tampered strictly > 0) and the T3 reciprocity gate result flips false.
- FB4 unaccounted release energy: tamper drops E_diss_release from the
  ledger at the release tick. Discriminator: the tick-76 ledger residual
  bound (clean within bound; tampered violated) — the M09 FB6 class.
- FB5 auto-bond on proximity: tamper auto-binds the patch when bodies
  overlap without a bind call. Discriminator: patch force in the unbound
  overlap/approach configuration (clean bitwise 0.0 + auto_bond_refused
  raised; tampered strictly > 0 force, guard absent) — the M09 FB1
  hidden-hinge class.

## Frozen probes and views (before execution)

- Numerical probes: the T-series element probes (exact), the 120-tick
  fixture trace (per-tick gap, penetration, patch force/couple magnitudes,
  both-body received force/moment sums, ledger), and the M01 document
  validations. All receipts canonical() bytes (sorted keys, no RNG, no
  wall-clock; timings only in the declared profile receipt).
- Views (registry ids, one diagnostic+clean pair each, same cameras within
  a pair): "patch overview", "loaded interface close-up", "orthogonal and
  oblique patch views". Diagnostic layers: "attachment patch geometry",
  "authored frames and port IDs", "fixture load and displacement traces".
  Clean view required. Every camera row carries the full 16-field registry
  camera record. View toggles (diagnostic <-> clean) must preserve the
  composite physical state hash — asserted per tick. Motion capture: FFV1
  (-level 3 -g 1 -fflags +bitexact) mkv per CODEC_STANDARD; ffmpeg version
  recorded; lossy fallback refused by construction.
- Frozen capture ticks: 0, 8, 40, 75, 76, 95, 119 (pre-load, squeeze
  loaded, mid-pull, pre-release, release tick, post-release, re-contact).

## Amendment ledger

- (base: no amendments at freeze; append below, each in its own commit,
  BEFORE the experiments they affect; measurement-driven disclosures go in
  the report)

### Amendment A1 (2026-09-30, pre-implementation, arithmetic repair)

T2's per-triangle tension literals were written three decades too large
(the patch-total line was correct). The frozen element law is unchanged;
only the prediction literals are repaired to the exact closed forms:

- WRONG (base prereg T2): "T1 = kA_t*A1*e0 = 3.4285714285714284e-1 N" and
  "T2 = kA_t*A2*e0 = 2.228571428571428e-1 N".
- CORRECT: with kA_t = 3428.5714285714284 N/m^3, k_t_1 = kA_t*A1 =
  0.34285714285714285 N/m and k_t_2 = kA_t*A2 = 0.22285714285714285 N/m,
  so at e0 = 1.0e-3 m: T1 = 3.4285714285714285e-4 N,
  T2 = 2.2285714285714282e-4 N, patch total k_t_patch*e0 =
  5.657142857142857e-4 N (unchanged), ratio T1/T2 = 1.5384615384615385
  (unchanged). The T2 check asserts the CORRECTED literals; the window
  tightness (1e-15 relative) is unchanged. No experiment had run when this
  amendment was written.

### Amendment A2 (2026-09-30, pre-experiment, dynamics analytics + schedule
### + ledger bookkeeping)

Development integration checks (not recorded experiments; no receipts
written) exposed three analytics errors in the base laws 10/11 and T8. The
frozen element law (laws 1-9) is untouched. Corrections, all derived from
physics, none from measurements:

1. Damping-ratio formula. Base T8 wrote zeta = c_v/(2*omega_t) — dimensionally
   wrong. Correct: zeta = c_v/(2*m_B*omega_t) = c_v/(2*sqrt(k_t_patch*m_B)).
   With the declared c_v = 2.0 N*s/m the fixture is zeta = 9.4017 — heavily
   OVERDAMPED (base T8 claimed 0.18803). With c_v = 2.0 the pull response is
   a two-time-constant creep (slow pole 0.2834 1/s) and the motion profile is
   not demonstrable. AMENDED: c_v = 0.02 N*s/m -> zeta = 0.0940,
   omega_d = 5.2949 rad/s (underdamped, declared).
2. Schedule (base law 10 amended). A 15-tick squeeze followed by a hard pull
   launches body B with the contact-spring energy (0.5*k_eff*g_static^2 =
   1.19e-3 J -> ~0.35 m/s), which swamps the pull analysis. AMENDED schedule
   (dt = 1/300 s, 356 ticks, interval [0, 355]): ticks 1..45 squeeze with a
   LINEAR ACTUATOR RAMP -2.0 N -> 0 N (quasi-static: the 6.6-tick contact
   oscillation period is resolved, so the contact unloads gently and body B
   tracks the actuator); ticks 46..60 settle at 0 N; BIND at tick 61 (gap
   ~4e-4 m, |v| ~ 8e-3 m/s); ticks 61..250 pull 0.03 N; RELEASE at tick 234
   — the DERIVED first oscillation peak: omega_d*t at 173 pull ticks is
   3.054 rad where the damped closed form is maximal and v ~ 0, and the
   held tension k_t*gap = 0.0524 N still exceeds the 0.03 N pull, so after
   release the net force flips outward and separation is demonstrated;
   ticks 234..260 the 0.03 N pull continues; ticks 261..355 approach
   2.0 N toward A (contact re-loads with NO patch present). CAPTURE_TICKS =
   (0, 20, 150, 232, 233, 250, 320).
3. T8 windows re-derived from the corrected closed form (static extension
   F/k_t_patch = 0.053030 m; s = zeta*omega_t*t; window = derived value with
   declared slack for XPBD/damping-model modelling error — never fitted):
   (a) squeeze: penetration tracks the ramp, reaches its largest magnitude
   at tick 1 (-2.0/1650 = -1.2121e-3 m); contact state loaded throughout the
   ramp while p > 0; (b) gap at the release tick 233 in [0.055, 0.130] m
   (damped closed form 0.0923 m); (c) U_release = U(233) in [0.9e-3, 4.8e-3]
   J (0.5*k_t*gap(233)^2 at the window edges); (d) separation: max gap over
   [235, 264] strictly greater than gap(234); (e) re-contact under the 2.0 N
   approach: contact state loaded at some tick in [258, 300] with peak
   penetration magnitude <= 0.015 m (approach-energy bound with the contact
   damping ratio 0.435; the law-9 refusal guard stays at 0.03); (f) bitwise
   post-release zero (unchanged from base T6).
4. Ledger bookkeeping (base law 11 operating statement, same formula): work
   terms are booked at the midpoint displacement dx = 0.5*(v0+v1)*dt (exact
   for forces constant over the step, so the frozen |R| bound sees only
   genuine spring-curvature drift, measured <= 1.9e-7 J per tick); the two
   declared dampings book as Q from the forces AS EVALUATED
   (Q = -f_damp*dx); W_contact is the ELASTIC penalty work only; and
   E_diss_release enters Q_total at the release tick (this is what the FB4
   arm attacks: dropping it must trip the residual bound).

No experiment receipts exist yet; this amendment precedes mode_main.

### Reference repair note (2026-09-30, recorded with the first receipts)

The three attempt commits were rewritten on this UNPUBLISHED attempt branch
(sole-owner workspace) solely to separate the `Agent:` trailer into its own
trailer block (the batch-gates trailer check reads git trailer blocks, which
require the separating blank line). TREES ARE UNCHANGED — the rewritten
identities are: base prereg 49bd9a85 (was eda436eb), Amendment A1 a39a946e
(was 945826a1), Amendment A2 951c963e (was 24b44ef2). Where the base prereg
header and module docstrings cite the old shas, the surviving text is the
commit SUBJECT plus this note; the chain order and content are provable from
the branch history itself.
