# PREREGISTRATION -- CMP-ASMB-HG / PKT-G3-ASSEMBLY-HANDGROUND (CHAIN STOP 1)

Lane: wk-pair-assembly (the wave capstone). Subject: `pair.hand_ground.v1`.
Sealed ALONE, BEFORE any run code of this lane existed (the prereg-sealed-
first law; the connection lane's ordering precedent). This document declares
the assembly plan, the acceptance checks as falsifiers, the pair_run
obligation disposition rule, the carried findings as requirements, and the
honest-absent inherited debts. Windows are fatal requires; failures are
preserved, never retried into green.

## 1. What is assembled (all published + review-closed)

| component | identity | published as |
| --- | --- | --- |
| HAND membrane | module 737cc658 (hand_membrane_v1.py), membrane.hand.v1 | astra PR #329 |
| GROUND membrane | module 1684d3b2 (membrane_ground.py), membrane.ground.v1 | astra PR #330 |
| CONNECTION | conn_seam.py 9b9a8285 (conn.hand_ground_contact.v1 seam law) | astra PR #331 |
| FROZEN CONTRACT | pc.hand_ground_contact.v1, sha256 a5431376... | compiler-compile |
| PACKET | PKT-G3-ASSEMBLY-HANDGROUND, criteria_sha256 cc65e2bce2f8ac8bf8de34382826ede1d4d60c4e8f799baba6be509bf659b239 | compiler-compile |

Precedent carried: the thermal three-membrane assembly matched an
exact-rational oracle BITWISE with the third membrane implemented BLIND by a
separate worker -- the graph runtime + generated wiring are proven. This lane
assembles the first PHYSICAL pair through the same machinery.

## 2. The assembly plan (the generator, never hand-wired)

1. The PAIR SPEC `spec/pair_hand_ground.spec.v1.json` (in-lane, frozen):
   members `[membrane.hand.v1, membrane.ground.v1]`, the ONE authoritative
   connection `conn.hand_ground_contact.v1` with exchange quantity_ref
   `q_jn` (unit N*s), owner `membrane.ground.v1` (contract state_ownership),
   consumed `press_channel_state` from membrane.hand.v1, declared transfer
   law (applied_by assembly), initial cases `armed_hold` / `released`,
   numerics dt 0.005 s (the contract's frozen tick). Every value is carried
   from the frozen contract bytes, the declaration, or the declared
   fixtures -- none invented.
2. The MANIFEST `abi_binding_manifest.pair_hand_ground.v1.json`
   (chimera.membrane_abi.binding_manifest.v1): binds each member to a thin
   in-lane ABI adapter (`adapter_pair_hand.py`, `adapter_pair_ground.py`)
   WRAPPING the published module bytes byte-exact (hash equality IS the
   no-edit proof; lane_of_record recorded per wraps row).
3. THE GENERATED WIRING: `graph_wiring_generate.generate_graph_wiring`
   (the ground lane's proven graph stage, 8637058f...) over the pair spec +
   manifest -> `generated/bindings.pair_hand_ground.v1.py` +
   `generated/assembly_wiring_graph.pair_hand_ground.v1.py`. Every run
   re-proves regeneration byte-identity from the frozen spec bytes.
4. CO-INSTANTIATION: through the GENERATED module's own path --
   require_assembly_inputs (byte gates), load_members (ABI conformance),
   `graph_runtime.validate_built_graph` on BOTH built members against the
   pair spec (per-connection ONE-writer scoping), contract groups 9/9 under
   the pinned PORT_CONTRACT_V2 validator, bindings placement
   (_verify_wiring), the pinned CombineScheduler store.
5. THE COMPOSITION (owned by this lane, labeled row-by-row in the receipt):
   (a) each member builds under ITS OWN published spec bytes (each module's
   frozen-input law intact; the adapter constructs the member's own
   SpecContext and refuses a drifted context by name);
   (b) the ONE identity translation: the ground's compiled exchange closure
   reads its declared consumed id (`state.press_channel_state.
   hand_fixture_stub.v1`, from the ground spec of record); the composition
   translates the hand's PUBLISHED press value into that slot -- nothing
   else;
   (c) the hand-face press publication + pad-side bookings (the transfer law
   is `applied_by: assembly` -- the ground spec's own words); the ground
   side's exchange record, jt record, refusal laws and ledger bookings run
   THE REAL MODULE'S OWN CODE (delegated compute).
6. THE PHYSICS PAIR RUN (the fixture clauses): the pairpath
   direct-M06-composition form at the pinned inputs (hand.vtp a06ea7e0...,
   A05 48b03759..., W03 f6844eea..., M06 local_contact 1cd662b3...,
   G04 grip_contact 0d637548..., declaration a5a82d52...), with the REAL
   hand membrane owning the press channel + release latch and the REAL
   ground membrane owning the walk-surface verdict gate; the pinned M06
   solver is the SEAM'S ONLY record writer (the ground side owns it).

## 3. The acceptance checks ARE the falsifiers (each fires on a constructed trigger)

| test_id | gate (fatal window) | constructed trigger that must make it FAIL |
| --- | --- | --- |
| T.ASMB_support | jn == press + weight stack (+ measured dp_stack_z) per tick, 1e-12 (steady-form transient reported) | a tampered replay that drops the weight term moves the residual by ~5.9e-3 N*s/tick >> 1e-12 |
| T.ASMB_propulsion_attribution | jt_ground_y > 0 on drive ticks; stack + body attribution identities 1e-12 | zero-mu control: jt_ground_y == 0.0 exactly (no traction-borne propulsion to attribute) |
| T.ASMB_slip | at reduced mu (0.12/0.08): per-record jt == mu_k * jn (measured-vs-measured); traction strictly < nominal | F2 EXECUTED TAMPERED REPLAY (below) |
| T.ASMB_zero_mu_control | ground mu (0,0): every record jt == 0.0 exactly; stack y-momentum stays <= 1e-12 | nominal-mu replay carries jt > 0 on the same drive schedule |
| T.ASMB_separation | separated fall ticks: no records, W_contact == W_press == 0.0 J exactly; free fall closed form 1e-9; landing = recorded transient | pressing-after-separation replay re-creates records (the release/latch refusal fires) |
| T.ASMB_ledger_classes | linear 1e-12; reciprocity bitwise 0.0; anchor reaction; pair-per-record loss 1e-12; energy 1e-12; replay 1e-12; continuity 1e-9; stored energy 1e-9; angular within per-tick bound m*2*vmax^2*dt (+1e-15); unmodeled_rotation_couple reported per tick, never dropped | an unrecorded impulse fires ledger_imbalance (G04 FB3 form) |
| T.ASMB_runtime_scene | the co-instantiated ABI scene through the GENERATED wiring; seam law + sealed falsifier pattern | a mutant hand face with an exchange writer is refused abi_exchange_writer_violation; a silent re-arm is refused ref.hand.latch_silent_rearm; a negative press record is refused ref.ground.jn_negative_press_record |

Every check must be able to FAIL: the receipt records each probe's bite.

## 4. F2 -- the EXECUTED tampered replay (carried finding, binding here)

At least one discriminator is an EXECUTED tampered replay through the FULL
pipeline (build -> step -> check), never an analytic magnitude. Declared arm:
re-run the T.ASMB_slip scenario end-to-end with the CHECKER's declared
kinetic pair-mu drifted by +1e-3 (0.081 vs 0.08). The per-record cap identity
then deviates by ~1.1e-3 N*s >> the measured-vs-measured window and the
check FAILS inside the tampered replay. The FAIL is RECORDED as the
discriminator (tampered_slip_replay), alongside the clean PASS. The clean
results are never mixed with the tampered arm.

## 5. F1 -- computed conformance counts (carried finding, binding here)

No conformance count is hardcoded. Every count (enforced contract rows,
probes, records, store applies, windows) is computed from the enforced list
or the observed store log at run time. The receipt carries the generator's
list, not a constant.

## 6. F3 -- the share_kg mantissa discipline (carried finding, binding here)

share_kg is COMPUTED as BODY_MASS_KG / 3.0 (= 3.3459993333333333 exactly, the
packet fx.trial_inertia double, hex 0x1.ac49b4c68d5f4p+1) -- never retyped as
a decimal literal. The release bar is share_kg * 1e-10. The receipt records
float.hex() of both so any retyping is visible. The anatomical 0.049 kg hand
segment mass stays RECORDED-only (declared separately, never the inertial
mass).

## 7. F4 -- the deviations array (carried finding, binding here)

Every deviation of this run from the packet/prereg expectations lands in
result.json's `deviations` array with the observed vs declared values.
Missing/skipped/unrun checks are stated explicitly in per_test_results
(NOT_RUN rows), never silent.

## 8. The pair_run obligation (currently declared_pending on all three components)

Disposition rule (declared BEFORE the run): the pair_run obligation is
discharged ONLY for what the sealed receipts actually prove:
- the fixture clauses (T.ASMB_support .. T.ASMB_ledger_classes) discharge
  the assembly-level pair RUN as a FIXTURE-BASED run (the packet's own
  evidence class: pairpath precedent);
- T.ASMB_runtime_scene discharges the co-instantiated runtime-scene clause
  ONLY if the generated wiring's own path builds and steps the pair with
  every falsifier biting; otherwise it is recorded NOT_RUN with the named
  refusal and the exact missing prerequisite -- never prose-success.
Whatever the outcome, `declared_pending` may only advance with a sealed
receipt pinned; the store/registry advance itself stays with the Lieutenant
(never by self-claim).

## 9. Honest-absent inherited (stays absent here)

- x_press ABSENT (NB-03): the press channel runs at the DECLARED fixture
  0.3 N*s/channel/tick; actuator_qualified false; no actuator claim.
- x_share ABSENT (NB-04): the equal-share partition scales the release bars
  only; no measured partition claimed.
- x_reach ABSENT (NB-05, C01 frame-composition verification owed):
  translation-only placements per the A09 frame law; no transform composed;
  no anatomical fit; the trial placement is the DECLARED trial placement.
- fx.mu_placeholders 0.6/0.4 (NB-01/NB-02, NAMED_PLACEHOLDER): every
  capacity-like number inherits them linearly; none claimed. The S3 reduced
  mu (0.12/0.08) and S3b zero mu are DECLARED falsifier values (the
  pairpath declared form), never re-pins.
- fixture_based = TRUE for every row; no integrated-qualification claim and
  no TRAINING_READY implication anywhere (the W09 unsupported-ticks finding
  governs that gate). PHYSICS_QUALIFIED is not claimed either.
- unmodeled_rotation_couple (~0.04, translation-only body line) is a named
  disclosure reported per tick, never dropped.

## 10. The physlang-v0 refusal law

The physlang-v0 refusal (present in the pairpath bytes) applies verbatim: if
the packet's physics language outruns the evidence (any derivation this lane
cannot carry from the pinned inputs), the refusal is named and the check is
recorded honestly -- the language is never forced. Declared candidate: none
at prereg time; any refusal discovered in-run is recorded per F4.

## 11. Resource law

All CPU execution through the campaign runner (NO_WORKTREES.md): seal/run
only, BUSY = retry with >= 10 s backoff (the R1 pad-layer job may hold a
slot; it is waited out, never preempted). Python C:/Python314/python.exe.
Outputs declared with --keep; undeclared files are disposable. Deviations,
refusals and failures are preserved.
