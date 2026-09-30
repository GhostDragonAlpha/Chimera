# MAT2-M11 PREREGISTRATION — reuse the same material rules in a loaded monkey limb

Attempt 8de1349ae67840fc8b8a15fb647c5e4a, arrival
arrival-f11f7489a821465ea2c014fea51698f8, criteria sha256
0588c4140a9968160cd640507e02a5b0cefefa6238ff3107de4c232f0d7ea72e (identical
across dispatch, registry card + attempt, this file, and checks.json identity).
Attempt branch branch-1 fast-forwarded (ancestor check first) to the sealed
line tip 362da5056f84b56b62a13cfb878dddb98538b18f (merge of PR #271, the
MAT2-M10 winner), which carries the merged winners of every declared
dependency (MAT2-M09, MAT2-M10, MAT2-B03, MAT2-B04, MAT2-B05) and the whole
M01-M08 law stack.

Composed against CARD_STARTER.md **v2** (2026-09-30, evidence-anchoring +
GPU-banking additions), house-standards/IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9), card-kit/ templates (generator trio + batch_gates),
format-spec/FORMAT_SPEC.md, codec-benchmark/CODEC_STANDARD.md.

This file was frozen and committed BEFORE the implementation existed and
BEFORE any M11 experiment ran. Amendments are separate commits on the
amendment chain (never squashed — the M10 lesson), each committed before the
receipts that cite it. Every window below is derived from declared constants
and pinned law inputs by the stated derivation; no window is tuned from an
M11 measurement. If a probe forces a window change, the amendment records the
triggering probe values and the derivation.

## 1. Frozen statement

One shape-parametric material law implementation — pressurized membrane
(M03 laws UNMODIFIED) + authored directional chord layout (M04's
effective_modulus law UNMODIFIED, called per member) + declared attachment
ties (M05 bond/tie law form, M05 imported UNMODIFIED) + penalty ground
contact (M05's pinned K_CONTACT_PA_PER_M law) — is exercised by ONE world
implementation (`LimbWorld`) on THREE declared shapes supplied purely as
geometry data:

1. `icosphere` — M03's icosphere L2 (R = 0.05 m), the M03/M10 lineage shape;
2. `cube` — M03's cube_grid (topologically and geometrically distinct:
   genus-0 quad-grid, flat faces, 90-degree corners);
3. `limb` — the SELECTED MONKEY LIMB tissue: a capped tube bladder erected
   between real endpoints of the pinned macaque arm (the B04 fitted frame
   chain), carrying the REAL B03 bone masses at REAL A06 attachment sites.

There is NO shape-specific motion code: the dynamics path (schedule,
substep, projection, contact, tie solve, ledger) is one code path with zero
branches on shape identity; shapes differ only in builder data. This is
audited (AST shape-branch audit, receipt X1a) and by run-identity (all three
runs record the same law-module sha and the same schedule function id).

The done_when (verbatim): "Demonstrate the same law implementation on two
distinct shapes without shape-specific motion code, then on the selected
monkey limb. Reconcile real mass/frames/attachments; show
tissue-to-bone-to-foot-to-ground load transmission, activation-off and
connection-removal controls."

### Limb assembly (the load path, all elements declared and inventoried)

- SHOULDER GUIDE (declared visible support, inventoried — never hidden):
  pins the tissue top pole in x,y and z. Its vertical reaction is AUDITED
  to be zero load-path: the guide holds position only against the declared
  lateral stiffness; the audited guide vertical force must stay within the
  declared window (gate X3d) — a violated audit is the FB4 bite. The applied
  load never touches the guide.
- TISSUE: the extending bladder (belt chord family = M10's measured
  prolate-extension direction; the SAME law code as the M10 braid, layout is
  authored data). Pressurized, it extends along the limb axis and pushes the
  distal chain against the ground.
- BONES (real mass): humerus, ulna, radius as declared point-mass rigid
  elements carried by the tissue through M05-form ties bound at REAL A06
  attachment sites (positions verbatim from the sha-pinned
  attachment_ownership.json; site-to-vertex binding = nearest rest vertex,
  recorded per site). No bone-bone joint is authored (B04 records the elbow
  bond unresolved_body; authoring it would be a guessed alignment — B04
  no_fusion_statement is honoured). Bone bone-masses are read from the
  pinned B03 matter entries at run time (never re-typed).
- FOOT (distal terminal): the hand region of the pinned arm. Declared
  status, carried honestly: B03 shell (open surface, zero counted mass,
  shell-volume claims refused by B03's sealed law) + B04 unresolved_body.
  The foot is a LAWFULLY EXPLICITLY-UNRESOLVED TERMINAL: real geometry
  (pinned hand mesh), zero counted mass, contact element at the REAL A06
  palm anchor position. This is the C17-debt resolution form required by the
  dispatch: real port inputs where real inputs exist (masses, frames,
  attachment sites), explicitly-unresolved terminals elsewhere, and a
  synthetic stand-in is REFUSED (audit + falsifier FB6).
- GROUND: M05-law penalty plane under the palm anchor
  (K_CONTACT_PA_PER_M = 1.0e5, pinned; never invented).
- LOAD: declared mass on an M05-form tie hanging from the tissue top pole
  (the body-weight surrogate; it loads the limb, not the guide).

### The two synthetic shapes use the SAME assembly

Icosphere/cube tissue in the same column assembly (top/bottom pole = min/max
axis vertex), same schedule, same load tie, same foot point mass, same
ground law. For the synthetic shapes the foot is the declared point mass
(the M10 declared load mass) with the same contact law — the assembly is
identical; only the tissue mesh differs.

## 2. Frozen input pins (verify_input_pins at every run; drift refuses)

| pin | sha256 |
|---|---|
| MAT2-M01/material_state.py | b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40 |
| MAT2-M03/pressure_membrane.py | 3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e |
| MAT2-M04/passive_response.py | 68a696e1728066a3dce93db7b6c98f8bb4826322a84bbad20eeadf38350e326b |
| MAT2-M05/interface_exchange.py | 295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9 |
| MAT2-B03/material_volume_input.json | 6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9ddc |
| MAT2-M02/monkey_arm_independent_meshes.json | 51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834 |
| MAT2-B04/frame_forest.json | 156ef55722e1ecda3238f3733131eb707f209cb93531d0e133227b00ebba8203 |
| MAT2-A06/attachment_ownership.json | f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c |
| MAT2-B05/mechanical_port_requirements.json | ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d |

All law imports are UNMODIFIED upstream modules. The M11 module composes
them; it does not edit them.

## 3. Declared constants (authored; engineering, labeled)

- Limb axis endpoints (real): top = fitted_humerus shoulder-side extent,
  bottom = the A06 palm anchor (real position, sha-pinned). The tissue tube
  axis is the segment between them; ring count 12, radial count 12 (derived:
  vertex budget <= icosphere L2's 162; membrane cost parity with shape 1).
- Tissue tube radius R_T = 0.012 m (authored engineering detail; ~1/12 of
  the arm span so the tube clears the bone extents; not tuned post-measure).
- T_WALL = 3.0e-3 m, E_FIBER = 1.0e8 Pa, E_TRANS = 1.0e6 Pa (pinned M03/M04
  scale carried from the sealed M10 card, itself carried from M03/M04).
- Chord cross-section A_CHORD = T_WALL^2 (M10 declared form).
- XPBD_ITERS = 8, XPBD_RELAX = 0.15, N_SUB = 16, DT = 1/300 s (M10 pinned
  integrator constants, carried unmodified).
- Damping: c_v = 2000.0 (near-critical ring decay, M10 A1), c_load = 4.0 1/s.
- Scaffold mass: icosphere/cube: 0.020 kg equal per vertex (M10 declared);
  limb: bone masses EXACTLY as pinned (humerus 2.250842664849005e-02 kg,
  ulna 1.0258339533412961e-02 kg, radius 9.10051480229847e-03 kg read from
  the pinned document at run time) + tissue mass 2.0e-3 kg equal per tissue
  vertex (declared; NOT a bone mass; never merged into B03's inventory).
- LOAD_M_KG = 0.050 kg (declared, ~2.2x humerus mass — an arm-scale load).
- Pressure: source limits carried from pinned M03 PressureSource form
  (MAX_DELTA_P_PA = 5000 Pa, MAX_FLOW = 1.0e-3 m3/s); work hold level
  DP_WORK_PA = 4000 Pa.
- Ground: K_CONTACT_PA_PER_M = 1.0e5 (M05 pinned law, imported constant);
  foot contact radius R_FOOT = 5.0e-3 m (authored engineering detail).

## 4. Schedule and phases (declared before any run)

PASCAL schedule on [0, TOTAL_TICKS), TOTAL_TICKS = 1500 at 300 Hz (5 s):

- P0_presettle  ticks 0-199:   p = 0 (limb settles onto the ground contact)
- A_rampup      ticks 200-399: ramp 0 -> 4000 Pa
- B_hold        ticks 400-1099: hold 4000 Pa (the loaded-transmission phase)
- C_poweroff    ticks 1100-1299: ramp to 0 (ACTIVATION OFF — control phase)
- D_settled_off ticks 1300-1499: settled at p = 0 (sag steady state)

Activation-off control measurement = phase D of the SAME run (power-off
behavior) PLUS a dedicated never-pressurized run (p = 0 throughout) whose
settled state is the off-control reference. Connection-removal control = a
dedicated run where the tissue-to-bone ties are released at tick 450
(declared, inside B_hold) via the M05 release law (release_of_unbound_bond
vocabulary); nothing else differs.

Frozen checkpoint ticks (measured quantities): SNAP_TICKS = (0, 300, 450,
700, 1000, 1100, 1200, 1350, 1499); measurement windows:
BASELINE_WINDOW = (100, 200) (presettle), LOADED_WINDOW = (1000, 1100)
(late hold), OFF_WINDOW = (1400, 1500) (settled off).

## 5. Frozen windows (derived from declared constants; never from M11 runs)

Let W = LOAD_M_KG * G (G = 9.80665; W = 0.4903 N), p_h = 4000 Pa,
A_col = declared tissue tube cross-section = pi * R_T^2 = 4.5239e-04 m^2
(pressure thrust scale p_h * A_col = 1.8096 N > 2*W — the actuator holds the
load with margin 3.69x at hold), k_c = K_CONTACT_PA_PER_M = 1.0e5 N/m,
x_floor = 1.0e-7 m (declared integrator positional identity floor; 10x
tighter than M10's 1e-6 settle criterion), rel = 0.05 (fractional window,
M03/M10 ledger heritage).

- X3a transmission identity: |F_contact_total - (W + W_carried)| <=
  rel*(W + W_carried) + k_c * x_floor. Derivation: force error sources are
  the contact-penalty error k_c * dx with the declared positional floor,
  plus the 5% ledger-class fractional allowance.
- X3b per-stage chain identity: |F_tissue_bottom - (F_contact - W_foot)| <=
  rel*F_contact + k_c * x_floor (stage-by-stage force bookkeeping through
  the foot; W_foot = declared foot mass * G = 0 for the limb — declared).
- X3c guide vertical audit: |F_guide_vertical| <= k_c * x_floor + 0.05*W
  (the guide carries NO vertical load path; a violated audit = hidden
  support).
- X4 activation-off: thrust(0) is bitwise zero by law (pressure force term
  p_i*A_i with p = 0); off-run sag >= 2x the loaded-run sag (derivation:
  off-state axial stiffness is the soft E_TRANS edge network k_off <
  p_h*A_col/span by the declared constants; the discriminator must separate
  by at least the loaded sag's own window) — precise pre-bank probe values
  recorded in Amendment A1 if the constant-derived 2x needs re-derivation.
- X5 connection-removal: after release, the released ties' force set is
  empty (M05 law: released ties return zero force, bitwise) and the bone
  trajectory departs the bound-run trajectory by >= the declared bite
  window 1.0e-3 m (M10 audit_bite heritage) within 100 ticks; the bound run
  must hold zero departure (clean control).
- Determinism: two fresh runs byte-identical (scoped AUGMENTATION_KEYS).
- Energy ledger: cumulative no-source gate |sum R| <= max(0.05*|W_press| +
  0.05*|W_grav|, 5.0e-4 J) (M03 T9 / M10 A1.8 heritage: raw constraint-solve
  exchange reported, not hidden; the cumulative gate is the binding claim).

## 6. Falsifier arms (P1: clean control FIRST, named premature guard, receipt rows)

Every arm: clean control on the untampered fixture runs FIRST and must pass
its declared window; the arm carries guard `<short>_fb<n>_premature`; the
receipt row embeds clean_control {metric_scope, value, within_tolerance,
guard} beside the tampered value and bit. Fixtures preflighted on CPU to
discriminate BEFORE any further spend.

- FB1 overlay-driven motion: a kinematic pose writer teleports the foot to
  the loaded pose (shape 'cube' fixture). Clean: motion audit deviation
  bitwise 0 (window 1e-9 m). Bite: deviation >= 1.0e-3 m.
- FB2 area-independent triangle forces: constant-per-triangle traction
  weighting replaces area-scaled traction. Clean: M03 traction identity
  |F_i|/A_i/p worst relative error within 1e-9 (window). Bite: >= 1e-6.
- FB3 clipped load path: the bone-tie reaction on the tissue anchor is
  dropped from the interface (reaction applied to the anchor but not
  transmitted to the chain). Clean: interface audit bitwise zero. Bite:
  reaction deviation >= 0.05*W or tip displacement >= 1e-4 m.
- FB4 hidden constraint/support: the shoulder guide is removed from the
  scene inventory while still active in the dynamics. Clean: inventory
  matches rendered/active subjects. Bite: support_missing_from_scene.
- FB5 unaccounted energy: one-way tie boost x2.0 (M10 FB3 heritage). Clean:
  state-determined force-law audit bitwise zero. Bite: law deviation >=
  0.05*W.
- FB6 synthetic port stand-in (the C17-debt falsifier): a tamper silently
  substitutes a synthetic bone mass (1.01x) for the pinned B03 mass in the
  limb assembly. Clean: assembly mass audit matches the pinned document
  bitwise. Bite: real_input_ledger mismatch refusal fires
  (synthetic_port_standin_refused:humerus).

## 7. Gate map (done_when clause -> named check)

| clause | gates |
|---|---|
| same law on two distinct shapes, no shape-specific motion code | X1a AST shape-branch audit (zero shape conditionals in the dynamics path; shapes = data), X1b run-identity receipts (same law sha + schedule id on all runs), X1c icosphere AND cube loaded runs both satisfy X3a with their own declared windows |
| then on the selected monkey limb | X2a real-mass audit (assembly masses == pinned B03 entries bitwise), X2b real-frame audit (assembly endpoints == B04 fitted frame chain + A06 palm anchor, sha-pinned), X2c real-attachment audit (every tie site == an A06 record verbatim; count and ids recorded), X2d port ledger carried from B05 (8 ports, lawful statuses; unresolved terminals named with their missing_evidence strings) |
| tissue-to-bone-to-foot-to-ground transmission | X3a/X3b/X3c above + contact active (penetration > 0, force > 0 in LOADED_WINDOW) |
| activation-off control | X4 (dedicated off run + power-off phases of the main runs) |
| connection-removal control | X5 (declared release run at tick 450) |
| pressure limits / power-off | X6: the four M03 named refusals fire (undeclared source, delta-p limit, negative absolute, flow limit); schedule returns to 0 |
| determinism / energy honesty | X7 scoped byte-identity; X8 cumulative ledger gate |
| unbound media / capture | capture section (below) + validator refusals |

## 8. Capture plan (material/motion profile; frozen before execution)

- Registry verification profile read READ-ONLY from
  E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3 (mode=ro URI;
  kanban.cards.MAT2-M11.spec.ontology_qualification.task.verification_profile).
  Required keys asserted; CANONICAL_LAYERS tripwire present (loud, never
  value-supplying). task_id SHORT form "M11" in manifest AND context.
- Views (registry): whole experiment at fixed distance; orthogonal side and
  front; oblique close-up of the loaded interface. Diagnostic/clean pairs
  per view (clean_view_required = true): clean rows carry ZERO labels,
  layers, overlays.
- Diagnostic layers (registry, all five): stable membrane/triangle/port IDs;
  pressure and area-scaled force vectors; rest/current geometry and material
  directions; contact/bond state; energy/work and simulation tick.
  Per-layer pixel presence: each declared layer, rendered alone, must place
  >= 1 pixel of its layer color in the frame (probe receipt; a layer with
  zero pixel presence fails capture validation).
- Codec: FFV1 -level 3 -g 1 -fflags +bitexact mkv via rawvideo pipe; ffmpeg
  version line recorded in the capture receipt; lossy fallback REMOVED
  (refuses, never falls back). Per-viewport offscreen renders + clipping;
  no cross-viewport leakage by construction; perspective depth sign
  conforms to the declared camera record (M10 F2 scar).
- Camera records: all 17 registry fields on every camera record (frame_id,
  coordinate_unit, position, orientation_convention_and_values, target,
  distance_to_target, projection, vertical_fov_or_orthographic_span,
  near_far_planes, aspect_ratio, viewport_resolution,
  camera_motion_or_bookmark_sequence, visibility_layers, label_ids,
  occlusion_or_xray_mode, state_or_tick_interval). Fixed bookmarks only.
- Camera-consistency gate (M10 permanent check): signed row-order check per
  perspective viewport (declared-above marker above the declared-below
  reference under the declared up), declared close-up content presence,
  zero tie-color leakage — recomputed from the committed stills by the
  named check suite.
- Bindings (P8): ONE video artifact; disk sha256 == manifest ==
  context == determinism record; every view row carries the same
  state_binding.sha256 (the canonical loaded-run trace sha) — view toggles
  preserve the physical state hash. Committed stills BMP at declared frame
  indices; P4 transform-list gate (identity 0 px; vflip/hflip/rot180 > 0)
  + stdlib row-order proof with sensitivity guard.
- Unbound media falsifier: a manifest bound to a WRONG trace sha must be
  refused by validate_manifest (named refusal recorded in the receipt).

## 9. Scope decision: CPU-only (declared)

No GPU submission is required by the done_when (all gates are CPU-measurable
and the campaign M10 precedent: CPU-only declared in prereg scope; the
resident-GPU path was qualified upstream by M08/M09). CPU-FIRST is thereby
satisfied trivially and honestly: the full-trajectory CPU run with ALL gates
armed is the only physics run. Should any gate force GPU work, an amendment
records the reason BEFORE the first GPU job and the gpu-queue PROTOCOL
applies (forward-slash JSONs, new ids, sequential banking, sanitizer first).

## 10. Honesty limits (declared now)

- The tissue is an engineering actuator bladder (M10 classification law
  applies: engineering_actuator unless biological equivalence is
  independently evidenced; it is not). No metabolism, no sarcomere
  hierarchy, no activation dynamics beyond the declared pressure schedule.
- Bones are declared point-mass elements with real masses; no bone inertia
  tensors are invented (B03 gives the aggregate arm inertia; the per-bone
  split is not authored).
- The elbow bond stays UNRESOLVED (B04); the limb assembly uses declared
  ties at real sites, not authored joints.
- The foot/hand terminal stays explicitly unresolved (B03 shell + B04
  unresolved body): real geometry, zero counted mass, named missing
  evidence (B05 ledger carried verbatim).
- The eight B05 anatomical ports remain mechanically UNQUALIFIED; this card
  carries their ledger and uses real attachment sites/masses/frames — it
  does not qualify the ports (that remains downstream V11/B06/B07 work).
- Independent visual judgment of imagery stays with review (visual_acceptance
  stays false in the validator receipt).

## 11. Execution order (frozen)

prereg commit (this file ONLY) -> probes if needed -> amendments (own
commits, before experiments) -> implementation -> CPU bank (all gates
armed; batch_gates 9/9 before any queue spend; none planned) -> named
checks -> capture -> generated report + lint -> push review/MAT2-M11 ->
PR (base astra/gait-capture) -> registry submit (args: task_id,
attempt_id, agent_id = arrival-f11f7489a821465ea2c014fea51698f8, pr_url,
head_sha, criteria_sha256; actor astra-codex) -> STOP (the Lieutenant owns
review/accept/merge).


## Amendment A1 (own commit; recorded BEFORE any bank/receipt)

Triggering probes (all on this attempt, CPU, pre-bank, recorded verbatim):
- P-A1.1 icosphere, schedule to 4000 Pa, 5.0 kg load on a single-pole tie,
  tension-only foot link: the column lifted off (top_z 0.036 -> 1.162 m,
  contact 0) because the thrust p*pi*R^2 = 31.4 N exceeded the load; the
  load tie's reaction was found NOT applied to the membrane (defect in the
  probed draft, fixed: the tie reaction now enters through the declared
  guide ring).
- P-A1.2 same at 4000 Pa with the reaction applied: the single-pole 49 N
  tie force punctured the shell (closure_negative_volume refusal from the
  UNMODIFIED M03 validator). Load introduction now distributes over the
  declared guide/bottom rings (probed fix, no refusal).
- P-A1.3 presettle identity: by tick 50 of P0 the per-tick residual r_tick
  -> -0.0000 J with q ~ 1e-4 J/tick (integrator + ledger identity verified
  in the constrained phase; the frozen ledger form is the M10 A1.8 form).

Architecture re-issue (recorded before any receipt is built): a STANCE
PUSH COLUMN cannot be demonstrated by a millimeter-stroke membrane
actuator under a point-compressive load (P-A1.1/P-A1.2). The card's
transmission demo is therefore re-issued as the HANGING BONE-CHAIN RIG,
entirely in the sealed M10 law forms:
- the vessel hangs from the declared overhead clamp (visible support,
  M10 heritage; the clamp never leaves the inventory),
- the BONE CHAIN hangs from the vessel's free pole through M05-form
  tension ties: tissue -> humerus -> ulna -> radius -> foot(hand), rest
  gaps declared; real B03 masses ride their chain elements; each bone
  carries a declared ground contact (penalty, K_CONTACT) for the released
  state,
- the belt (extension) layout drives the free pole DOWNWARD when
  pressurized: the pole push descends the chain, the foot presses the
  ground, and EVERY stage force is a measured tie tension (T1 tissue
  anchor, T2 humerus-ulna, T3 ulna-radius, T4 radius-foot) beside the
  measured contact force.

Gate re-derivation (all from statics of the declared rig, no measurement):
- X3 whole-system statics: F_clamp_z + sum(F_contacts) == W_total within
  rel 0.05 + k_c*x_floor in every settled window;
- X3-stage: F_contact == W_chain_below_foot_link - T4 (foot equilibrium),
  and T1 == W_chain - F_contact (chain top), each within the same window;
- X4 activation-off: at p = 0 all stage tensions carry weights only and
  the foot contact is bitwise 0 (the declared rest gap means the chain
  hangs free); at hold the measured F_contact > 0 == the transmitted
  thrust within window (the bitwise-0-vs-positive discriminator; the
  power-off phases must recover the p=0 state within the declared
  recovery window);
- X5 connection-removal: releasing T2 (declared tick 450) drops the distal
  chain onto its own bone contacts; the tissue-side measured chain loses
  the distal weights (T1 drops by W(ulna)+W(radius)+W(foot) within window)
  and the distal contacts pick them up; the departure bite stays 1e-3 m;
- X3c guide audit is reformed: the clamp is DECLARED; the audited identity
  is the whole-system statics above (a hidden support would violate it).

Constant re-issues (with derivations): DP_WORK_PA 4000 -> 1000 Pa;
M_LOAD_SYNTH_KG = 2.0, M_LOAD_LIMB_KG = 0.25 (compression-surrogate
loads; the rig uses the chain weights as the load path, these declared
loads remain as the hanging surrogates on the chain), foot inertial mass
0.010 kg declared per shape (B03 counted hand mass stays 0.0 bitwise),
C_FOOT = 200 1/s and C_BONE = 30 1/s (3.16x and 1.3x critical for the
declared foot-contact and bone-tie modes), ring load introduction,
bilateral strut REPLACED by the tension-only chain ties + per-bone
contacts (the strut draft is superseded by this re-issue).

Also recorded: site->world frame plumbing recovers each pinned blob
region's own admitted world_from_local transform and asserts reproduction
of the pinned world vertices to <=1e-12 (transform_mismatch refuses);
B04's no_fusion_statement is honoured (no fitted-frame alignment is
authored). The foot/hand remains an EXPLICITLY-UNRESOLVED TERMINAL with
the B05 blocked-input missing-evidence strings carried verbatim.
