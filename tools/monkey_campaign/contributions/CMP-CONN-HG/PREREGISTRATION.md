# PREREGISTRATION - wk-connection-handground / PKT-G3-CONNECTION-HANDGROUND

CHAIN STOP 1 (prereg draft for the pin). Written and sealed BEFORE the run code
exists (pairpath seal-chain law: prereg sealed alone first, then the code).

- worker lane: wk-connection-handground
- packet: E:/ChimeraWork/monkey-coordination/compiler-compile/packets/PKT-G3-CONNECTION-HANDGROUND.json
- packet criteria_sha256: 21ec15791b561cc5569a476826e3e9c8158404e2be3587a598e329a3275e10f4
- external contract: pc.hand_ground_contact.v1 v1.0.0,
  sha256 a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104 (FROZEN)
- subject: conn.hand_ground_contact.v1 - implement/verify the interaction ACROSS
  the ports (SEAM LAW ONLY)
- base (E:/PythonChimera, read-only for this lane): 7222729eca6e9f97f25061c8b1dc3d229bb703d8

## 1. Scope law

This lane implements the INTERACTION across pc.hand_ground_contact.v1: record
ownership, the pair rule, the release bars, the ledger closure. It does NOT
implement either membrane interior (membrane-hand/ and membrane-ground/ lanes
own those; interiors stay HIDDEN per the packet interior law) and NOT the
assembly verification (a later lane owns the pair RUN runtime scene; the
contract's pair_run obligation stays declared_pending).

All quantitative results are FIXTURE-BASED (packet fixture_rule): fx.mu_placeholders
(NB-01/NB-02), fx.press_actuation (NB-03), fx.equal_share_partition (NB-04) stay
NAMED PLACEHOLDERS / ABSENT-declared. Nothing is tuned; no integrated-qualification
claim is made; qualification language is refused.

Honest gate: none of the four acceptance checks T.CONN_counted_once /
T.CONN_friction_pair / T.CONN_release / T.CONN_ledger requires a membrane
IMPLEMENTATION - each requires only the frozen port shapes (the contract bytes),
the pinned M06 solver, and declared fixtures. If any check is found during
implementation to require an interior, it is declared BLOCKED with the named
prerequisite rather than improvised. No such requirement is known at prereg time.

## 2. Pinned inputs (all verified by sha256 at prereg time)

| role | path | sha256 |
| --- | --- | --- |
| pinned M06 solver (import-only) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-M06/source/local_contact.py | 1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc |
| port contract (frozen) | E:/ChimeraWork/monkey-coordination/compiler-compile/PORT_CONTRACT.hand_ground_contact.v1.json | a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104 |
| declaration decl.hand_ground.v1 | E:/ChimeraWork/monkey-coordination/compiler-declare/hand_ground_declaration.v1.json | a5a82d526f160be671837307419abc0f1c33a0f0636bd13220fb9b1797c3d773 |
| G04 receipt | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/numerical/experiment_receipt.json | 0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8 |
| G04 falsifier receipt (a2 release bars, latch) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/numerical/falsifier_receipt.json | 04ef594cb7aa856e3afcd9b767e75c5c0dc44206f4c3db16ce678a35886f7fb2 |
| G04 report (X2/X3/X4/X6) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/REPORT.md | dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8 |
| G07 report (accounted release) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G07/report/REPORT.md | 34a4a095e1f4b3e5c87160a77e399c5c27a38202c1ad3675b0bcbf70d4b956a1 |
| pairpath receipt (S-forms, jt sign, physlang refusal) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-D-PAIRPATH/numerical/pairpath_result.json | 3d3dfae1fe6bfb759045a450e7a66bc7b3fd2e670eb9ed925e06163fd65a03a9 |
| ABI of record | E:/ChimeraWork/monkey-coordination/mathspec/membrane_abi.py | 80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665 |
| graph runtime (per-connection writer scoping) | E:/ChimeraWork/monkey-coordination/mathspec/graph_runtime.py | c7a96b07dfe4da5056a5c9b39aefa3f3d178c3be01084c823dbd4a9084fc3860 |
| spec runtime (id scheme, CombineRefusal) | E:/ChimeraWork/monkey-coordination/mathspec/spec_runtime.py | 423fca7089fc28a39825c50eaee8b4968b4beebd778807cb32eaf2e95e2cbd31 |
| pinned combine_core | E:/ChimeraWork/monkey-coordination/mathspec/pinned_inputs/combine_core.py | 8bfe6949b6854341801106649423c100201c2ed7989c09e3aed0af3f4c860712 |
| A05 mutation record (hand frame + bounds) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json | 48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649 |
| F05 composed_meta (walk plane +0.004 m) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-F05/source/composed_meta.json | 8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce55fa3a42f7 |
| F05 terrain_meta (slope envelope 0.05 m/m) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-F05/source/terrain_meta.json | ff15fb1db3dcc128a531d21ef64d3ab62ae78190b64db36f70b5d273c1425681 |
| W03 scene (walk plane + friction identity) | E:/ChimeraWork/monkey-coordination/kanban-reviews/MAT2-W03/review-glm53flash-confirm-20260928/blobs/scene.json | f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342 |
| hand.vtp (declared trial contact surface) | E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp | a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6 |

Import law: the pinned solver and the mathspec substrate are IMPORTED, never
forked; every import hash-asserts its bytes and refuses by name
interface_pin_missing / interface_pin_drift (pairpath precedent). No
bond/weld/sticky construction is added anywhere in this lane (weld is a recorded
ZERO channel with FB1-only provenance).

## 3. The seam implementation (the coupling law across the ports)

One module (conn_seam.py) + one test driver (test_seam.py), stdlib-only,
CPU-only, deterministic (no RNG, no wall clock in the physics). Named refusals
only; nothing silently repaired; prereg windows are RECORDED verdicts.

a) PIN + CONFORMANCE GATE (at load, before anything runs): hash-assert every
   pinned input (table above); parse the FROZEN contract bytes and require the
   exact fields the seam consumes (refusal contract_field_mismatch on any
   drift): endpoints (membrane.hand.v1:port.grip_contact role a,
   membrane.ground.v1:port.walk_surface_contact role b); quantities jn/jt/
   press_channel_state with unit N*s; direction signs (jn inout, sign
   convention "jn >= 0 presses the surfaces together", jt inout "opposes the
   tangential tendency within the mu cone", pcs out "released = 0 N*s
   exactly"); state ownership (jn,jt owner membrane.ground.v1 single-writer;
   pcs owner membrane.hand.v1); timing (dt 0.005 s, 300 Hz, stage order
   pressure->material->contact, press_release_latch); consumed inputs (mu_s
   0.6 / mu_k 0.4 NAMED_PLACEHOLDER, walk_plane_height 0.004 m,
   slope_envelope 0.05 m/m); contract parameters (press 0.3 N*s/channel/tick,
   operating force 60 N by the DECLARED /dt conversion, release bar
   share_kg*1e-10, ledger identity m*dv == press+weld+gravity+contact+anchor
   window 1e-12); pair rules (elementwise_min, counted-once reciprocity,
   separation_removes_support); g convention record-g 9.81 with standard-g
   9.80665 cross-check. The walk-plane identity is cross-checked against the
   F05 composed_meta (+0.004 m) and the W03 recipe rows; the declaration's
   connection/law_params against the contract.

b) PORT FACES ON THE PROVEN ABI SUBSTRATE: a lane-declared seam spec document
   (chimera.conn_seam.spec.v1, derived 1:1 from the frozen contract; recorded
   with its sha) declaring the two port faces:
   - membrane.hand.v1 face: owned_state press_channel_state (N*s); ports:
     inputs jn, jt (connection_ref conn.hand_ground_contact.v1, unit N*s);
     outputs press_channel_state.
   - membrane.ground.v1 face: owned_state jn, jt (N*s); ports: outputs jn, jt.
   - connection conn.hand_ground_contact.v1: members both; exchange owner
     membrane.ground.v1.
   Both faces are validated with the PINNED membrane_abi.validate_built AND the
   PINNED graph_runtime.validate_built_graph (per-connection one-writer
   scoping): only the ground face exposes exchange_contribution() and it
   produces EXACTLY the seam's record ids under the ONE deterministic id scheme
   (spec_runtime.resolve_ids); a hand face exposing a writer is refused
   abi_exchange_writer_violation. Named refusals abi_* stay the substrate's.

c) TICK LOOP (the sealed G04/G07 direct-composition pattern over the pinned
   solver; lane-owned, as in the pairpath): stage order pressure -> material ->
   contact. Pressure stage: the hand-owned press channel state applies its
   declared per-tick impulse (fx.press_actuation: 0.3 N*s per channel/tick,
   3 channels; operating force 60 N by the DECLARED /dt conversion) to the
   trial hand body only. Material stage: DECLARED identity pass for this
   contract version (the contract exchanges only jn/jt/pcs across the seam; the
   ground material interface is interior) - recorded, never silent. Contact
   stage: lc.solve_tick writes the records ONCE (single writer), applies them
   bitwise +/- to both sides, and enforces its own ledger laws (fatal).
   Accounts: full-tick ledger closure, reciprocity, anchor reaction, pair
   per-record loss identity, per-tick rows recorded to the receipt.

d) SCENE (the pairpath build_scene form, cited; translation-only placements,
   A09 frame law, x_reach stays ABSENT - no transform composed): ground plateau
   at +0.004 m (declared walk plane, pinned body, fixture mu), trial hand
   surface from the pinned hand.vtp (palm-down on the plane; declared trial
   inertia = the sealed G04 scene pad share 10.037998/3 kg per the
   light-intermediate-body law; fixture mu on both sides at the fx.mu_placeholders
   pair values), declared load prop tetra (10.037998 kg, the certified scene
   line) resting on the hand dorsum. SITES: 3 press channels at the 3
   lowest-z hand triangles (the lawful n=3 scene reading).

e) DECLARED FIXTURES (all recorded per tick in the receipt rows):
   - fx.mu_placeholders: mu_s 0.6 / mu_k 0.4 on both sides (contract
     consumed_inputs; NB-01/NB-02; NAMED_PLACEHOLDER - every capacity-like
     number inherits them linearly; no capacity claim is made here).
   - fx.press_actuation: 0.3 N*s/channel/tick armed, released = exactly 0.0
     (NB-03 debt; AUTHORED_DECLARED; actuator_qualified false forever here).
   - fx.equal_share_partition: the trial share_kg = hand body mass
     (equal-share MODEL of the balance, NOT a measured partition; NB-04
     ABSENT debt) - used ONLY to scale the release bars.
   - fx.trial_hand_surface: the pinned hand.vtp geometry, translation-only
     (the sealed pairpath scene construction; not a membrane implementation).
   - fx.tangential_trigger: a declared lane-owned tangential test impulse
     (AUTHORED_DECLARED falsifier stimulus, pairpath drive-channel precedent)
     used ONLY to construct stick/slip triggers; recorded in its own ledger
     channel so the closure identity stays exact.
   - fx.separation_event: the pairpath S4 declared separation (press released
     AND the trial hand body removed from the solve at the declared tick).

## 4. Acceptance checks - each a run-time falsifier on a constructed trigger

Windows are the packet/contract windows; every window is enforced by a fatal
require in the run (a window miss fails the job; failures preserved, never
retried into green). Sealed upstream numbers are cited for comparison; the
sealed G04 scene numbers are NOT expected to bit-reproduce on this lane's
different fixture scene - the WINDOWS and LAWS are what this lane re-verifies.

### T.CONN_counted_once (pair_rules.counted_once_reciprocity; G04 X3, exact)
- Trigger: the support scenario (press armed, stack seated; hand-ground +
  prop-hand + prop-ground records present).
- Predictions (recorded verdicts, fatal windows):
  P1.1 each record applied bitwise equal/opposite: impulse_on_b ==
       -impulse_on_a bitwise, every record, every tick.
  P1.2 solver solve_contact invoked EXACTLY once per record (lane-instrumented
       call counter == record count, every tick) - written ONCE at the contact.
  P1.3 both side ledgers re-read from the SAME record list: contact[hand] and
       contact[ground] re-derived bitwise from the records; reciprocity sum
       residual == 0.0 (G04 X3 worst 0.0 N*s; law floor 1e-12).
  P1.4 ground anchor == -contact[ground] bitwise every tick (reaction
       RECORDED, worst 0.0 N*s).
  P1.5 seam store guard: a second write of a record id raises
       combine_double_state_write (substrate one-writer law enforced, not
       prose).
- Discriminator (clean control first): a tampered replay that applies the
  hand share of one record twice must move the reciprocity residual to the
  impulse scale (>> 1e-12) so the check can fail; recorded as
  tampered_bites=true.

### T.CONN_friction_pair (X2_friction_pair; windows 1e-9 / 1e-12)
- Trigger A (stick): press armed; a sub-cone tangential trigger impulse
  (jt_req <= mu_s_pair * jn on the seam records); after each arrest tick the
  post-arrest tangential relative speed at the seam <= 1e-12 m/s (G04 stick
  arrest bar 1e-12; sealed worst 1.3877787808120304e-17 m/s).
- Trigger B (slip): the trigger raised ABOVE the cone; every slipping seam
  record carries jt == mu_k_pair * that record's jn (per-record cap form);
  the per-tick tangential recursion matches the predicted
  dv = (J_trigger - sum(jt))/m within 1e-9 m/s and the closed-form
  displacement over the slip window within 1e-9 m (G04 slip worsts 4.45e-12
  m/s, 2.33e-13 m).
- Trigger C (zero-mu control): ground side mu=(0,0) so the PAIR mu =
  elementwise_min = 0; every seam record jt == 0.0 bitwise and the stack
  slides under full press; displacement matches the friction-free closed form
  within 1e-9 m. The observed displacement is recorded honestly (scene-
  specific; the sealed G04 control number 0.05150250000055512 m is its
  scene's sealed observation, cited upstream, not expected here).
- Discriminators: (i) the control discriminates a mu-bearing law from the
  observed zero-mu law: the friction-included closed form (mu_k 0.4) differs
  from the observed displacement by >> 1e-9 m (tampered_bites=true);
  (ii) a tampered record whose jt is replaced by mu_hand*jn (side mu instead
  of pair min) must violate the per-record cap re-derived from the DECLARED
  side values (min), so the check can fail.

### T.CONN_release (X4_release; share-scaled bars + exact zeros)
- Trigger: hold ticks (press armed, support), release tick R
  (press_channel_state -> released; press_release_latch ON: once released it
  stays released; re-arm refused without an explicit declared re-arm event),
  then the declared separation event fx.separation_event; free fall to a
  recorded transient landing.
- Predictions:
  P3.1 every post-release tick: the hand-side press ledger entries are
       exactly 0.0 (bitwise) - never a partial press.
  P3.2 on every separated tick: n_records == 0, W_contact == 0.0 J exactly,
       W_press == 0.0 J exactly (pairpath S4 P4.1 form).
  P3.3 release-tick bars share_kg*1e-10 (share_kg = the fx.equal_share_partition
       trial share, hand body mass): observed release-tick jn, jt (exact
       zeros at the constructed flat-plane separation) within the bars.
       DISCLOSED: the NONZERO noise-floor observation (G04 X4 worsts
       6.34e-11 / 2.54e-11 N*s) belongs to the proximity-bearing vertical
       grip seam; at the flat walk-plane seam the constructed separation
       yields exact zeros; the bars are verified as computed upper bounds.
  P3.4 free fall: per-tick recursion |v(k)-v(k-1)+G*DT| <= 1e-9 m/s;
       closed-form drop within 1e-9 m (G04 X4 window; sealed worst
       4.872630077201734e-13 m); landing recorded as a transient, never
       support.
- Discriminator: a tampered replay that keeps 0.5x press after release must
  break P3.1/P3.2 (residual at the press impulse scale) - tampered_bites=true.

### T.CONN_ledger (contract_parameters.ledger_identity; 1e-12 N*s)
- Trigger: every tick of every scenario above.
- Predictions:
  P4.1 m*dv == press + weld + gravity + contact + anchor on every body/tick,
       worst residual <= 1e-12 N*s (G04 X6 sealed worst 1.0013e-15; the weld
       channel is a recorded 0.0 with FB1-only provenance - no weld/sticky
       construction exists in this lane).
  P4.2 pair-per-record loss identity: both sides' tangential works +
       w_f_ke_J == 0 per record (reduced-mass cross-check, pairpath P5
       discipline) <= 1e-12 J (pairpath sealed worst 2.4e-17).
  P4.3 per-record cone law: |jt| <= mu_s_pair * jn on every record; slip
       records at the mu_k_pair cap.
- Discriminator (FB3 heritage): an unrecorded impulse injected into a
  tampered replay must fire ledger_imbalance - tampered_bites=true.

## 5. Contract-conformance table (every row enforced by code against the
   FROZEN contract bytes; refusal contract_field_mismatch)

| contract field | frozen value (bytes) | seam enforcement |
| --- | --- | --- |
| endpoints | hand.v1:port.grip_contact (a) / ground.v1:port.walk_surface_contact (b) | seam spec faces carry exactly these ids; validated by membrane_abi |
| jn | number, N*s per tick, MEASURED (G04 store pin) | per-record jn_Ns from the pinned solver; ledger class contact |
| jt | number, N*s, bounded by elementwise_min pair cone | per-record cone check P4.3 + pair rule (c) |
| press_channel_state | state, armed/released, out, hand-owned; released == 0 exactly | latch in the pressure stage; P3.1 |
| units | N*s per tick at fixed dt; 60 N = 0.3/0.005 DECLARED /dt | press stage applies 0.3 per channel; operating force recorded as 60.0 N derived |
| g_convention | record-g 9.81, std-g 9.80665 cross-check | solver constants used as pinned; std-g used only in recorded reference arithmetic |
| mu_s / mu_k | NAMED_PLACEHOLDER 0.6/0.4, source_side b, elementwise_min | fx.mu_placeholders on both faces; pair rule from the pinned solver; zero-mu control |
| walk_plane_height | 0.004 m (F05 flatten, single writer) | ground plateau placed at exactly +0.004 m; identity checked vs F05+W03 |
| slope_envelope_m_per_m | 0..0.05 | the fixture plane is inside the envelope; recorded |
| frames | macaque_arm_hand_mutation_frame (a) / earth_contract_local_frame (b); NO transform composed (x_reach ABSENT) | translation-only placements in the declared meter frames; no rotation/transform composed anywhere |
| state ownership | jn,jt: ground single-writer, readers hand+pair; pcs: hand single-writer, readers ground+pair | seam spec + validate_built(_graph) writer scoping; P1.2/P1.5 |
| timing | dt 0.005 s, 300 Hz, stage order pressure->material->contact, per-tick impulses, no cross-tick memory; latch press_release_latch | the tick loop declares all three stages; per-tick rows carry no cross-tick latch except pcs |
| valid ranges | pcs in {armed, released} (third state = structural fault); jn max = x_press ABSENT | the latch accepts only the two states (refusal pcs_state_invalid); no x_press value is invented |
| pair rules | elementwise_min / counted_once / separation_removes_support | T.CONN_friction_pair / T.CONN_counted_once / T.CONN_release |
| release_bar_ns | share_kg*1e-10 per release tick | P3.3 with the fx.equal_share_partition share |
| ledger_identity | m*dv == press+weld+gravity+contact+anchor, 1e-12 | P4.1 with weld recorded 0.0 (FB1-only) |
| x_press / x_share / x_reach | ABSENT (named) | never filled; fixtures declared; placement translation-only |

## 6. Declarations and refusals

- pair RUN (runtime scene co-instantiating both membranes): stays
  declared_pending, owed by the assembly packet; this lane records the
  physlang-v0 refusal (its derive_fixture cannot carry contact-pair scenes;
  pairpath precedent) and advances the pair-run obligation by the direct M06
  composition only.
- fixture_based = true for the whole result; no integrated-qualification
  claim; mu/capacity numbers inherit the placeholders linearly.
- The membranes' interiors are never imported, constructed, or imitated; the
  trial hand surface is declared geometry only.
- Windows and predictions in section 4 are preregistered BEFORE the run code
  exists (this file sealed alone first). Anything discovered later is recorded
  as an amendment, never silently re-labeled.
- Deviations, named debts encountered (NB-01..NB-04), and any NOT_RUN rows
  will be stated explicitly in the result; Sergeant review is requested
  through the Lieutenant (a worker never approves its own verification).
