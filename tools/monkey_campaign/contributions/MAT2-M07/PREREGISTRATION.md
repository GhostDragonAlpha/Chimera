# MAT2-M07 PREREGISTRATION — frozen before implementation and before any measurement

Frozen: 2026-09-29Z, before authoring integrated_step.py, run_experiments.py,
test_integrated_step.py, render_run.py, make_capture.py, make_report.py, before
any experiment run, and before any capture code or frame exists.
Task: MAT2-M07 / planning id M07 — "Couple pressure, material and contact
through one physical step" (criteria sha256
ff18b443b97f2b3947cc993ff64175a9e848fc6d806ed90bd719fa2bd24e87b4, attempt
cc584d2e1e7c46de80bacbaf7ba12f77, arrival
arrival-52e028187826458d91d6ab8d6c1e7fb7).

done_when (verbatim): "One state owner integrates simultaneous
pressure/material/contact loads with declared ordering, time step and
iterative/substep convergence. Record external work, passive energy and
boundary reactions; test timestep refinement and disconnected-component
independence."

Card task falsifier (verbatim): "Separate passes overwrite motion, expose
mixed-tick state, or report stability only at one unexamined timestep."

Verification-profile falsifier (verbatim): "Unbound media, clipped load path,
hidden constraint/support, area-independent triangle forces, overlay-driven
motion, or unaccounted energy prevents acceptance."

Port contract (verbatim): "Same-tick force/constraint contributions -> one
updated physical snapshot with explicit synchronization."

## Base and reconciliation (read-only, done before this freeze)

- Canonical startup assigned slot branch-2, prepared checkout head
  c525b82c7c3ce0128565424764293a3c85811ab3 (origin/branch-2, 2026-09-24).
  The sealed line (origin/astra/gait-capture tip 18c3be78740349acbc6e0e5d507ecf2afce52e62
  = merge of PR #246) carries the MERGED winners of ALL FOUR declared
  dependencies of this card: MAT2-M03 (PR #243, merge e62e3c43),
  MAT2-M04 (PR #241, merge d83ee979), MAT2-M05 (PR #246, merge 18c3be78) and
  MAT2-M06 (PR #245, merge 30cd0f75). MAT2-M05 merged during this attempt's
  startup, exactly as the dispatch anticipated ("depend only on merged");
  this freeze is written against the post-merge tip. Per the dispatch, the
  local attempt branch was advanced to the scratch branch `m07-integration`
  at 18c3be78 (local-only, never pushed; branch-2 preserved untouched).
- Dependency input pins verified in this checkout before this freeze
  (frozen inputs; a mismatch at run time refuses `input_pin_drift`):
  - MAT2-M01/material_state.py sha256
    b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40
    (chimera.material_state.v1 validator, schema authority, UNMODIFIED use),
  - MAT2-M03/pressure_membrane.py sha256
    3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e
    (Membrane closure/area-scaled traction/lumping, PressureSource, icosphere
    builder, XPBD scaffold pattern with measured projection residual),
  - MAT2-M04/passive_response.py sha256
    68a696e1728066a3dce93db7b6c98f8bb4826322a84bbad20eeadf38350e326b
    (exact Maxwell exponential update + within-tick integrals + stored energy
    + check_ledger, all UNMODIFIED calls),
  - MAT2-M05/interface_exchange.py sha256
    295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9
    (interface reciprocity and substep/ledger discipline; declared contact
    penalty constants heritage; measured-residual bound pattern),
  - MAT2-M06/local_contact.py sha256
    1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc
    (sweep-and-prune candidate search, triangle-triangle closest features,
    impulse contact solve with Coulomb friction, anchor/ledger identity).
- Reconciled gap this card fills: M03 owns pressure on a CLOSED membrane as a
  standalone run; M04 owns passive material response on a PINNED gauge; M05
  owns one two-body interface with its own scaffold; M06 owns local contact
  between rigid shells with its own tick loop. No module on the sealed line
  advances pressure, material and contact loads on one owned state through a
  single declared step. M07 adds exactly that integrated step owner — nothing
  inside any upstream file is modified.

## Frozen statement

M07 implements ONE state owner, `IntegratedWorld`, whose `step()` is the only
writer of any physical state. The world owns N declared components (each a
pressurized closed membrane + a loose plate + a Maxwell material mount + its
own pinned ground), all their vertices/velocities, the Maxwell force history,
and the ledgers. Every tick executes the DECLARED order

    1. pressure  (M03 declared-source traction, area-scaled, lumped)
    2. material  (M04 Maxwell element, exact exponential update/integrals)
    3. contact   (M06 sweep candidates -> local gap -> impulse solve, GS)

at the DECLARED tick dt = 1/300 s (req.teddy_gpu_matter_kernel 300 Hz pin,
M03/M05 heritage) with N_SUB = 4 declared substeps per tick (each substep
executes the SAME declared order: pressure -> material -> contact), contact
Gauss-Seidel iterations to a DECLARED convergence gate (a final measurement
pass finds no active pair requiring |Jn| > 1e-12 N*s; iteration cap 32;
per-tick measured residual and iterations recorded; the gate refusal is
`convergence_gate_not_met`), and XPBD edge projection (8 iterations, M03
pattern, projection work kept in the MEASURED residual). Contact uses M06's
`solve_contact` VERBATIM (its declared constants, including its declared
BETA/DT bias rate, are upstream constants applied at this owner's tick —
recorded here so nothing is hidden); the candidate search is DECLARED to run
per component over that component's shells only (declared domain
decomposition), and any cross-component candidate contact is refused
`cross_component_contact` — the independence oracle (X2) proves bitwise that
this decomposition hides no channel. Gravity is a declared external load with
its impulse recorded per tick (M06 ledger pattern). The tick closes with ONE
updated physical snapshot (post-projection positions AND the velocities and
energies evaluated at that same configuration — the M05 correction-A1
end-of-tick snapshot rule), a per-component state hash, and the explicit
synchronization record (order digest, tick, substeps, iterations, residuals).

Every tick records, per component and world: external work (pressure work and
gravity work, trapezoid account per substep, M05 A1 pattern), passive energy
(Maxwell stored U via M04 `stored_energy`, dissipated Q via M04 exact
integrals, scaffold elastic U, each reported separately), boundary reactions
(ground-anchor impulse per tick; wall-anchor Maxwell reaction impulse per
tick; both included in the momentum ledger), the contact impulse pairs
(bitwise reciprocal), friction work (M06 W_f = KE removed), and the measured
energy residual R_tick (never hidden, never assumed away).

## Frozen declarations (constants of the law; all declared BEFORE measurement)

- Tick dt0 = 1/300 s; refinement family dt0/2 = 1/600, dt0/4 = 1/1200
  (halving chain; exactly the "timestep refinement" of the done_when).
- Substeps per tick N_SUB = 4 (dt_sub = dt/4); declared before measurement.
- Contact: M06 verbatim constants (thickness 0.002 m per side, slop 1e-5 m,
  margin 1e-5 m, beta 0.2 with M06's declared BETA/DT_M06 bias rate,
  restitution 0, friction pair rule = elementwise min; block mu (0.6, 0.4),
  plate-ground mu (0.7, 0.5) -> pair (0.6, 0.4)); Gauss-Seidel gate
  max |dJn| <= 1e-12 N*s or cap 32 iterations.
- Membranes: icosphere L1 radius R0 = 0.06 m, declared total mass 0.02 kg,
  XPBD compliance 1e-5 m/N, 8 iterations, no global damping (damping enters
  only through the declared Maxwell dashpot, whose dissipation is measured
  exactly).
- Pressure source (per membrane, M03 declared): delta_p schedule
  [60 Pa ticks 1..40, 0 Pa ticks 41..80] via M03's declared `with_delta_p`
  sibling-source pattern on a source with max_delta_p 5000 Pa, max flow
  1e-3 m^3/s (limits enforced by the UNMODIFIED M03 source refusals).
- Component rig geometry (per component, B translated +3.0 m in x): ground
  pad = horizontal 2-triangle pinned shell, midsurface z = -0.001 m, span
  0.30 m x 0.30 m; membrane icosphere centered at (0, 0, 0.062) (initial
  1 mm gap to its ground through the declared thicknesses; it settles by
  gravity); plate = vertical 2-triangle shell, midsurface plane x = 0.069,
  y in [-0.06, 0.06], z in [0.002, 0.122] (initial ground gap 0 exactly =
  touching within margin), standing to the +x side of the membrane; the
  initial membrane-to-plate gap is 0.007 m through the declared thicknesses
  and closes as the membrane inflates — the membrane presses the plate in
  +x ("a membrane pressing on a loose object moves both").
- Maxwell mount (per component, M04 declared): the plate is tied along +x to
  a fixed wall anchor at the plate's rest centroid by a Maxwell element,
  k = 20 N/m (E*A/L0 form declared directly as k), c = 8 N*s/m
  (tau = 0.4 s), axis +x; the element force on the plate is -F*xhat with F
  from M04's exact update; the wall feels the recorded +F*xhat reaction
  (boundary reaction, momentum-ledger external term of the plate).
- Friction declarations (per surface, M06 vocabulary; pair rule elementwise
  min): membrane (mu_s 0.5, mu_k 0.35), plate (mu_s 0.3, mu_k 0.2), ground
  (mu_s 0.7, mu_k 0.5); pairs: membrane-plate (0.3, 0.2), plate-ground
  (0.3, 0.2), membrane-ground (0.5, 0.35).
- Gravity g = 9.80665 m/s^2 along -z (M03's declared constant) as a declared
  external load on every free body; ground is a pinned shell per component
  (declared support, rendered and labeled — never hidden).
- Component separation: component A at x offset 0, component B at x offset
  +3.0 m (>= 10x the largest per-tick motion and 50x the contact margin);
  cross-component candidate pairs are refused `cross_component_contact`.
- Determinism: no RNG anywhere in the world, experiments or tests; no
  wall-clock anywhere; P-determinism is byte-identity of reruns.

## Frozen experiments and predictions (limits fixed before any run)

- X1 coupling run (the visible result): the declared two-tick-phase scenario
  (inflate ticks 1..40, relax 41..80) at dt0 on the TWO-component world.
  Frozen: the plate of component A moves (peak |x displacement| >= 1e-5 m)
  AND the membrane of component A moves (peak COM |z| change >= 1e-6 m) —
  "a membrane pressing on a loose object moves both through the same solved
  interaction"; every tick's ledger closes inside the declared residual bound
  (below); every contact impulse pair is bitwise reciprocal; the momentum
  ledger (m*dv == gravity + contact + anchors, per component per component
  per tick) closes within 1e-12 per component; the material sub-ledger
  |W_in - (dU + Q)| <= 1e-9 J per tick, checked by M04's UNMODIFIED
  `check_ledger`.
- X2 disconnected-component independence: joint two-component world vs the
  two solo single-component worlds, same dt0, same 80 ticks. Frozen: bitwise
  equality (max abs float difference == 0.0 exactly) of every recorded
  quantity of each component in the joint run against its solo run
  (positions, velocities, ledger rows, state hashes). This is the
  no-hidden-coupling proof; ANY nonzero difference fires
  `independence_violated`.
- X3 timestep refinement: the X1 scenario rerun at 1/300, 1/600, 1/1200 for
  the same simulated horizon (80/160/320 ticks). Frozen, per component:
  (a) STABILITY at every examined timestep: no NaN, max |v| <= 5 m/s, and
  |R_tick| <= 5e-2 * turnover + 1e-9 at every tick (turnover = |W_press| +
  |W_grav| + |W_in| + |W_contact_ke| + E_kin) — stability is NEVER claimed
  from a single unexamined timestep; the harness refuses a refinement set
  without >= 3 members including a strict halving (`refinement_set_invalid`).
  (b) CONVERGENCE of the smooth observable (membrane volume at the final
  tick): errors e(dt) against the 1/1200 reference decrease strictly across
  the chain e(1/300) > e(1/600) > e(1/1200), and the measured order
  p = log2(e(1/300)/e(1/600)) lies in [0.5, 1.6] (first-order integrator
  family). (c) CONVERGENCE of the event-ful observable (plate displacement,
  averaged over the final 20% of the horizon): e(1/300) > e(1/1200) and its
  measured order p in [0.3, 1.8] (discrete contact-activation ticks may dent
  the rate; the declared window is wider and is stated as such).
- P-order-declaration: the world records the declared order digest
  (sha256 of the canonical order/time/substep/convergence declaration) and
  every tick asserts it (`declared_order_mismatch` refusal otherwise); the
  executed phase sequence is recorded per tick (order_digest + phase marks).
- P-single-owner: the implementation contains exactly one writer method
  (`IntegratedWorld.step`); the world state (vertices, velocities, Maxwell F,
  ledgers) is private to the world; adapters expose read-only views; the test
  suite asserts the membrane/plate objects hold no step logic of their own.
- P-boundary-reactions: ground-anchor and wall-anchor impulses are recorded
  every tick; the momentum ledger closes with anchors included (1e-12); at
  the final tick the cumulative ground-anchor z-impulse is negative
  (support direction) with magnitude >= the cumulative gravity impulse on the
  block (the support carries at least the weight) — recorded, not tuned.
- P-determinism: run_experiments.py run twice -> experiment_trace.json and
  experiment_receipt.json BYTE-IDENTICAL.
- P-regression: the UNMODIFIED M03, M04, M05 and M06 suites re-run green in
  this checkout on the exact candidate revision (all four dependencies).
- P-input-pins: the five pinned dependency files re-hash to the frozen values
  above at run time (`input_pin_drift` refusal otherwise).

## Frozen falsifier arms (each bitten on a TAMPERED COPY, discarded after)

- F1 "hidden coupling / cross-wired components" (card falsifier +
  independence oracle): a tampered world copy that adds a hidden load term
  coupling component A's plate velocity into component B's plate load MUST
  fire the X2 independence oracle (`independence_violated`, nonzero
  trajectory difference); the untampered world stays bitwise green.
- F2 "ordering swap": a tampered copy that executes the declared order
  permuted (contact -> material -> pressure) MUST fire the declared-order
  digest check `declared_order_mismatch` AND produce a measurably different
  trajectory (both recorded), proving the declared order is physically
  meaningful and that the check bites.
- F3 "mixed-tick state": a tampered ledger row assembled from PRE-projection
  positions with POST-projection velocities (the exact "mixed-tick state"
  failure) MUST trip the residual gate (|R| beyond the declared bound) or
  the state-hash check.
- F4 "separate passes overwrite motion": a tampered copy where the contact
  stage rewrites plate positions from its own propagation (a second,
  uncoordinated pass over the state) MUST trip the residual/momentum ledger
  gates — the one-owner claim is enforced by the ledgers.
- F5 "iterative convergence gate is decorative": running the contact stage
  with the Gauss-Seidel gate disabled (single pass, no convergence loop) on
  the X1 scenario MUST produce a per-tick contact residual above the declared
  gate on at least one tick, firing `convergence_gate_not_met` — proving the
  gate measures something.
- Profile-falsifier arms: unbound media (every capture view binds the sha256
  of the committed solver trace); clipped load path (measured camera margins
  reported per view); hidden constraint/support (the pinned ground and the
  wall anchor are rendered and labeled in whole/side views); area-independent
  triangle forces (M03's area-scaled traction is the only traction path; the
  per-triangle pressure forces scale with current areas, recorded per tick);
  overlay-driven motion (fixed-bookmark cameras; geometry moves only per the
  sha-bound trace); unaccounted energy (X1 residual bound + F3 arm + M04
  sub-ledger).

## Frozen verification-profile probes and views (material, motion)

- Views (registry profile, read read-only from
  agent_slots.sqlite3 kanban.cards[MAT2-M07].spec.ontology_qualification.task
  .verification_profile): "whole experiment at fixed distance",
  "orthogonal side and front", "oblique close-up of the loaded interface";
  each rendered as a diagnostic/clean pair (clean_view_required true).
- Diagnostic layers: ALL FIVE registry layers carried in the diagnostic rows:
  stable membrane/triangle/port IDs; pressure and area-scaled force vectors;
  rest/current geometry and material directions; contact/bond state;
  energy/work and simulation tick.
- Capture: task_id SHORT form "M07"; solver states rendered ONLY from the
  committed experiment trace (replay asserted against trace scalars before
  assembly); single-artifact binding: ONE video file, capture_sha256 = that
  file's sha256, every view row an artifact_locator of kind video on it;
  cameras carry all registry camera_required_fields; validate_manifest runs
  with the profile object read read-only from the registry.
- Frozen capture scenario: the X1 coupling run (membrane inflates, presses
  the plate, plate slides against friction and stretches the Maxwell mount,
  then the pressure relaxes and the system settles) over its full tick range;
  the loaded-interface close-up binds the SAME trace.

## Applicability boundary (honest, frozen)

Offline CPU-only integrated-step experiment executable over pinned upstream
laws and authored small fixtures; not the native C++ engine, no GPU
residency, no live renderer, no runtime integration, no training. The
membrane is a lumped XPBD scaffold (M03 heritage), the plate a rigid shell
(M06 heritage kinematics), the mount a 1-D declared Maxwell element (M04) —
the integrated OWNER is the deliverable, not a new material law; no new
physical law is invented here, and none is needed by the done_when.

## Amendment A1 (frozen after the freeze commit 33238aba, BEFORE implementation and before any measurement)

- Correction of the declared energy-ledger accounts, derived during honest
  design (no measurement has run; M06's amendment precedent):
  (i) The material stage carries TWO declared accounts. The ELEMENT account
  (M04's own protocol, cumulative per component) closes exactly:
  W_in = v1x * int F dt == dU + Q within 1e-9, checked by M04's UNMODIFIED
  `check_ledger`, where v1x is the declared driver velocity (the plate's
  x velocity after the pressure stage — the declared order makes the material
  stage see that velocity). The WORLD work account uses the applied-impulse
  trapezoid W_mat_on_plate = -J * 0.5*(v_pre_x + v_post_x), exactly like
  every other applied load (M05 A1 pattern). The difference J^2/(2*m_plate)
  (driver-discretization) belongs to the MEASURED residual R, like the
  contact bias injection and the projection exchange — reported, never
  hidden.
  (ii) The X1 residual bound therefore gains the reservoir terms (M05 A1
  heritage), replacing the freeze's bare formula:
  |R_tick| <= 5e-2 * turnover + (U_mat + U_mat_prev + U_scaff +
  U_scaff_prev) + 1e-9, turnover = |W_press| + |W_grav| + |W_mat_on_plate| +
  |W_contact_ke| + E_kin. X3's stability clause (a) uses this same bound.
  (iii) The X1 momentum-ledger clause gains the declared material and
  projection terms: per body per tick,
  m*dv == gravity + contact + anchors + material impulse + projection_delta,
  all five right-hand terms recorded, within 1e-12 per component; the
  projection_delta is the measured velocity redefinition of the XPBD
  projection (M03/M05 keep its work in R). Pinned anchors remain exactly
  -(their received contact impulses). P-boundary-reactions is unchanged.
  Nothing else changes.

## Amendment A2 (frozen after Amendment A1, BEFORE implementation and before any measurement)

- Geometry corrections from honest derivation of the frozen scaffold
  compliance (no measurement has run): with XPBD compliance 1e-5 m/N the
  membrane is a stiff pressurized shell — it CANNOT inflate 7 mm to close
  the frozen 0.007 m membrane-to-plate gap, so that scenario would never
  make contact. Replaced, per the card's own visible result ("A membrane
  pressing on a loose object moves both through the same solved
  interaction"):
  (i) the plate's rest midsurface plane moves to x = 0.062 m so the initial
  membrane-to-plate gap is EXACTLY 0 (touching within the declared margin);
  the pressure resultant of the inflated membrane transmits through the
  M06 contact from tick 1;
  (ii) the plate's midsurface z-span is [0.001, 0.121] m so its initial
  ground gap is exactly 0 (the freeze's [0.002, 0.122] left a 1 mm drop);
  (iii) declared consequence: the membrane receives the -x contact reaction
  and slides on its own ground pad (declared pair friction (0.5, 0.35),
  threshold ~0.069 N, below the transmitted pressure resultant), while the
  plate slides +x against its ground friction and the Maxwell mount — both
  bodies move through the same solved interaction, which is exactly the
  frozen X1 claim. The X1/X3 frozen numbers and windows are unchanged.
  Nothing else changes.

## Amendment A3 (frozen before the frozen experiments X1-X3 were executed or reported)

Provenance, stated plainly: after the A2 commit, implementation smoke/debug
runs (single-component, up to 60 ticks) were run to make the integrated step
execute at all; no frozen experiment (X1 two-component 80-tick run, X2
independence comparison, X3 refinement chain) had been executed when this
amendment was frozen. The debugging surfaced one missing LEDGER term (not a
change to any frozen experiment, prediction, window or threshold):

- The XPBD projection's energy exchange (its kinetic-energy redefinition
  plus its scaffold-strain change per substep) is RECORDED as a first-class
  ledger term `projection_exchange_j` and enters the tick identity
  explicitly, replacing the A1 sentence that kept it inside the measured
  residual (the M03/M05 convention). Declared tick identity:
  E(t) - E(t-1) = W_press + W_grav + W_mat_on_plate - W_contact_ke_removed
                  + projection_exchange + R,
  with R now holding only the small declared Maxwell driver gap
  (impulse-vs-exponential account, J^2/(2*m_plate) scale) and round-off;
  |R| stays under the A1 bound. The momentum ledger already recorded the
  projection delta (A1 (iii)); this makes the energy side equally explicit.
  The contact term's sign is now written correctly as MINUS the measured
  contact KE removal (A1's turnover definition is unchanged).
- The contact Gauss-Seidel accumulation covers EVERY applied impulse of
  EVERY pass (the ledger and the reciprocity check must cover all applied
  impulses, not only the converged pass's records; the per-tick contact
  records remain those of the converged pass).
- M06's solve_contact returns tuple velocities; the world's adapters
  normalize them back to declared numpy arrays (write-through typing, not a
  law change). Nothing else changes.
