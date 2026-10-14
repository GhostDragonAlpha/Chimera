# SEVEN-COORDINATE LIFT PACKET — v1

Lane: `lane/packet-author-20260918` (agent: GLM 5.3). Authored 2026-09-18 against base
commit `4b047609` (origin/master tip at authoring time).
Status: **AUTHORED — implementation owed by a senior native-solver lane.** No engine
implementation is contained here. The Python reference
(`tools/science_funnel/coupled_arm.py`, class `Assembly`) already derives `M(q)`,
gravity, bias and point Jacobians analytically for ALL SEVEN unlocked source
coordinates; this packet authors the native lift so every added coordinate is verified
against that reference as an independent oracle, with the qualified 2-coordinate mode
preserved as a frozen bit-exact control (RULE 0, falsifier named before any run).

Admission record: `work.dynamics.seven_coordinate_lift_packet`, admitted by
`tools/creature_graph/validation/admit_solver_packets_20260918.py` (idempotent) into
`tools/creature_graph/data/authored/project_program.json`, rebuilt by
`tools/creature_graph/build_graph.py`. Completeness is enforced by
`tools/science_funnel/check_packet.py` (exit 0 required over every `docs/packets/*.md`).

Recommended landing order: this packet FIRST, then `free_root_balance_v1.md` — the
seven-coordinate lift validates the shared generalized-row solver (S1 below) on the
FIXED root, where the Python oracle is strongest; the free-root packet then reuses the
same derivation. Each packet is self-contained; neither depends on the other's code.

---

## RULE 0 — ADMISSION

**STATEMENT (someone could disagree with this):** The native coupled dynamics can carry
all seven unlocked source coordinates — `shoulder_flexion, elbow_flexion,
radial_pronation, wrist_flexion, wrist_abduction, shoulder_adduction,
shoulder_rotation` of `model.anatomy.macaque_arm` — with per-drive actuator stores,
per-coordinate joint stops with a deterministic simultaneous-stop cascade, and the hand
contact on the full 7-row point Jacobian, while the qualified 2-coordinate scene runs
UNCHANGED (frozen bit-exact control) and every generalized quantity matches the Python
`Assembly` oracle to double-rounding tolerance.

**PREDICTION (not yet measured):** At any pose inside the source ranges, native
`M(q)` (7x7), `gravity` and `bias` agree with `Assembly(model, rates).mass_matrix /
gravity_force / bias_force` to `≤ 1e-12` relative; the hand point Jacobian agrees to
`≤ 1e-12` relative; a 7-drive rollout keeps `|balance_error_J| < 1e-5` and
`|store_balance_error_J| < 1e-5` on every status query; each coordinate driven into
each of its stops lands `≤ 1e-9` from the bound with the impulse ledger closing; the
stage-0 dispatch reproduces the qualified candidate bit-exactly.

**FALSIFIER (named before the run):** Any oracle mismatch beyond `1e-12` relative on
`M`/gravity/bias/Jacobian; any stage-0 status byte differing from the qualified
candidate; any coordinate clamped outside its range by more than `1e-9` or held by
anything but its stops; any per-drive store going negative, double-charging across
substeps, or spending while disabled; any ledger identity violation; any nondeterminism
across two identical runs — REFUTES the lift and the implementation is refused. The
source model's five ignored coordinates are not degrees of freedom by authoring
(`model.dynamics.coupled_arm` assumption 1); making them move without an admitted
revised contract would falsify the scene's own scope — the lift lands as a NEW record,
never by editing the qualified recipe.

---

## THE REFERENCE THE NATIVE SIDE MUST MATCH

`tools/science_funnel/coupled_arm.py::Assembly` (qualified as
`chimera.coupled_arm_reference.v1`): sorted unlocked coordinates (its own order —
the oracle permutation is part of the test fixture, S6), per-body sums

```
mass_matrix += m·jvᵀ·jv + jwᵀ·iw·jw        (iw = r·I·rᵀ)
gravity_force += jvᵀ·(m·g)
bias_force += jvᵀ·(m·acceleration) + jwᵀ·(iw·alpha + cross(omega, iw·omega))
potential -= m·dot(g, position)
point(body, local) -> (t·[p,1], [d_i·[p,1]]ᵀ)   (3xn Jacobian)
```

built from the SAME `pose_frames` ordered-transform convention the native `Model`
implements (`ChimeraEngine/engine/coupled_articulation.hpp` — the two are the same
math in two languages and the qualified arm already proved them equivalent at n=2).
The native `Model` constructor ALREADY accepts up to 7 selected unlocked coordinates
(`names.size() <= 7`, `"coupled_coordinate_capacity"`) and `evaluate` is n-generic:
the lift is a `CoupledDynamics`-layer work item, not a kinematics work item. The
qualified `CoupledDynamics` class stays byte-untouched (frozen control, S7).

Pinned recipe coordinate order for the new record
(`model.dynamics.coupled_arm7`, schema `chimera.coupled_scene7.v1`):

```
["shoulder_flexion", "elbow_flexion", "radial_pronation",
 "wrist_flexion", "wrist_abduction", "shoulder_adduction", "shoulder_rotation"]
```

Derivation of the order (not taste): it is kinematic chain depth order
(sternum→humerus→ulna→radius→hand), which (i) keeps the qualified pair as coordinates
`[0,1]` so stage comparisons are prefix expansions, (ii) gives the mass matrix minimal
bandwidth along the chain, and (iii) is a pinned permutation the oracle test applies to
the Python side (whose own order is `sorted()`); the physics is permutation-invariant,
the fixture pins the mapping in one place.

---

## DERIVATION (in the code's exact conventions)

### S1 — THE 7-ROW JOINT-STOP CASCADE

Stops are per-coordinate rows `±e_i`, armed in `rate()` iff the coordinate is within
`1e-10` of a bound and `|v_i| ≤ 1e-9` (the qualified `normals()` law, per row), always
armed at the localized wall in `impact()`. With 7 coordinates, MANY rows can be armed
at once (a scripted pose can park several joints on their bounds), so:

- Rate-level projection: the simultaneous armed-row set is solved by the generalized
  mass-metric projection derived in `free_root_balance_v1.md` §D6 (active-set loop with
  the same floors, tolerances and `Refusal("coupled_contact_row_budget")` cap) — the
  2-row qualified case is algebraically the same KKT solve, but the qualified path is
  NEVER rerouted (S7); the cascade only needs the general solver for n > 2 stages.
- Event-level CASCADE (the deterministic ordering law): when one `free_step` endpoint
  violates SEVERAL coordinate bounds in a substep, each violated coordinate is
  localized by its own 42-step bisection (as today, per coordinate); the EARLIEST
  crossing time wins; ties within `1e-12·h` break to the LOWEST recipe-coordinate
  index; exactly ONE stop impact is applied at that time; `advance` recurses on the
  remainder (depth `< 8`, `"coupled_impact_event_budget"` unchanged).
  Derivation of the tie rule: a tie means the bounds are hit within the bisection's
  own resolution `h/2^42`; any physical claim beyond that resolution is fiction, so
  the only requirement is REPRODUCIBILITY — pinned lowest-index ordering is
  compiler- and platform-stable, which is what the determinism falsifier (F4) tests.
  Note the qualified n=2 loop uses `t <= hit` (LAST index wins ties); the frozen path
  keeps exactly that byte-for-byte, and the n>2 path pins lowest-index — both
  deterministic, neither crosses the other.
- Stop + contact simultaneity is NOT a cascade priority question: rows enter one
  projection together (velocity-level floors in `impact()`, acceleration-level floors
  in `rate()`), exactly as the qualified code already does with its
  `rows`/`floors` vectors. The cascade only orders LOCALIZATION, never projection.

### S2 — PER-DRIVE ACTUATOR STORES

The qualified scene has ONE shared battery (`battery_ = 2.0 J`) and one combined
work-scaling bisection per substep. The 7-drive mode replaces it with PER-DRIVE stores
`battery_d`, one per authored drive stem — with the honest derivation of why:

- The qualified contract's assumption is "ideal capped actuator work consumes finite
  mechanical energy" per DRIVE hardware (`power`, `shoulder_drive`, `elbow_drive` are
  already per-drive flags; torque caps are per-drive). A shared store couples
  independent sources: adding a third drive would drain the same 2 J and change the
  qualified two-drive behavior — which the frozen control forbids. The qualified
  shared-battery semantics remain EXACTLY as-is on the frozen path; the new record
  (`coupled_scene7.v1`) pins per-drive stores, `battery_initial_J` per drive
  (2.0 J, the same derived capacity per source), and reports per-drive `battery_d`,
  `work_d`, `empty_events_d` plus totals.
- Per-substep accounting: each enabled+powered drive runs its own 40-step bisection
  scaling ITS `tau_d` so `work_d(substep) ≤ battery_d`
  (`require(battery_d >= 0, "coupled_negative_store")` per drive); braking per drive
  accumulates `brake_d`; a depletion increments `empty_events_d` once.
- Servo gains extend by the SAME formula, which is why it is a derivation and not a
  choice: `kp_d = M[d][d]·(2πf)²`, `kd_d = 2ζ·M[d][d]·(2πf)`, `damping_d = M[d][d]·decay`
  evaluated at `model_->defaults` — the qualified mass-normalized PD at the diagonal;
  the diagonal at n=7 is the same physical quantity per coordinate.
- Per-drive identities (falsifiable, F5): `battery_d ≥ 0` always; a disabled or
  unpowered drive spends exactly 0 and brakes 0; mechanical energy is GLOBAL, so the
  ledger closure stays the GLOBAL identity (`balance_error_J` with `work = Σ_d work_d`)
  — there is NO per-drive energy closure, and the packet refuses to fake one.

### S3 — HAND CONTACT WITH THE 7-ROW POINT JACOBIAN

`point(hand, local)` at n=7 returns `J_c ∈ R^{3x7}`; the contact machinery lifts
row-count-only:

- Contact row (normal): the Up row `J_n = {J_c[0][1], ..., J_c[6][1]} ∈ R^{1x7}`
  (the qualified `contact_row` is the n=2 case). Constraint `J_n·qdd + bias ≥ 0` while
  touching, floor `-contact_bias`, `contact_bias = vector(frames[hand].ddt, local, 1)[1]`.
- Touching band and gate: `kTouch = 1e-5`, `kSlip = 1e-9`,
  `gate = 1e-6 + 1e-3·Σ_i |v_i|` (joint-row 1-norm) — the band argument
  (`a·h²/2 ≈ 6.9e-6 m < kTouch` at `h = 1/1200 s`, settled `a ~ 20 m/s²`) is
  h- and acceleration-scale, DOF-independent; carried verbatim with its derivation.
- Friction: the qualified single-tangent solve at 7 rows (the 3D two-tangent cone
  generalization is the FREE-ROOT packet's D5; this packet lands on the fixed root
  with the qualified rotating-tangent semantics lifted to 7 rows — the closed forms
  `A, B, C, rn, rt, det = AC - B²`, stick test `|λ_t| ≤ μ·λ_n + 1e-12`, slide
  `den = A - s·μ·B > 1e-12`, `λ_n = rn/den`, `λ_t = -s·μ·λ_n`, at-rest sign fix
  `s = rt ≥ 0 ? -1 : +1` are row-count-parametric exactly as written in
  `coupled_dynamics.hpp::friction_solve`). Heat `-λ_t·slip_v ≥ 0` as qualified.
- Projection of joint-stop rows + contact row together: the S1 cascade's solver.

### S4 — STEPPING

Same RK4 + event splits at `h = dt/4 = 1/1200 s` (`substeps == 4` required), for the
same derived reasons as `free_root_balance_v1.md` §D9: servo `ω·h ≈ 0.0105` far inside
RK4's envelope, no new stiffness, event-localized stops/contacts, ledger quadrature
identities derived for this integrator, bit-exact frozen control incompatible with any
integrator change.

---

## S5 — STAGED QUALIFICATION LADDER (each stage = one commit, falsifiers first)

- **Stage 0 — frozen bit-exact control.** The generalized runtime compiled WITHOUT any
  new coordinate: dispatch to the qualified class verbatim (same construction as the
  free-root packet's D10). Falsifier F1: the complete qualified live check sequence
  (`qualify_coupled_live.py` command script) produces byte-identical status streams
  versus the qualified candidate's recorded receipts. Also: the qualified compiler
  (`coupled_scene.py`) and qualified class diff = zero.
- **Stage 1 — 3 coordinates** (`+ radial_pronation`). Offline oracle: for ≥ 100 pinned
  in-range poses (recorded seed, ≥ 1e-3 rad margin from bounds), native
  `evaluate(q, v, g)` vs `Assembly(model, rates)`:
  `M` (with the fixture permutation), `gravity_force`, `bias_force` each `≤ 1e-12`
  relative (norm-scaled); hand point + Jacobian `≤ 1e-12` relative. Live: the new
  drive moves its coordinate; stop lands `≤ 1e-9`; ledger `< 1e-5`.
- **Stage 2 — 5 coordinates** (`+ wrist_flexion, wrist_abduction`). Same oracle at
  5 rows + contact engaged (press, cone, heat accounts) with the 5-row Jacobian;
  mass-eigenvalue list matches `Assembly.record()['mass_eigenvalues']` ordering and
  values `≤ 1e-12` relative.
- **Stage 3 — 7 coordinates** (`+ shoulder_adduction, shoulder_rotation`). Full oracle
  at 7 rows; all seven drives move all seven coordinates; stops on EVERY coordinate
  driven into EVERY bound (14 landings, each `≤ 1e-9`); hand contact + friction as
  qualified; per-drive stores exercised (a drive disabled mid-rollout spends nothing);
  `mu = 0` reproduces the frictionless world bit-exactly (the qualified mu=0 control,
  lifted); final re-run of the Stage-0 F1 hash (the frozen path never regressed).
- A stage that fails its falsifiers STOPS the ladder; the next stage may not start.
  Each stage's commit message names the falsifiers run and their results.

## S6 — ORACLE FIXTURE (pinned, no sweep)

The pose set is GENERATED once by a recorded-seed PRNG (seed committed in the test
file), poses drawn inside `[lower + 1e-3, upper - 1e-3]` per coordinate, velocities
drawn in `[-2, 2]` rad/s; the fixture is REGENERATED deterministically, never
hand-edited, and committed as its output JSON with the seed for audit. The permutation
mapping (Python `sorted()` order ↔ pinned recipe order) is one declared list in the
fixture. Comparisons are relative to `max(1, ‖x‖_∞)` per quantity; failures print the
pose, the quantity, native vs oracle values.

## S7 — FROZEN CONTROL (bit-exact)

Same law as the free-root packet (its §D10, incorporated here by reference): the
qualified `CoupledDynamics` class and the qualified compiler keep their exact bytes;
the generalized n-coordinate solver lands in a NEW header (`coupled_multidynamics.hpp`)
and dispatches to the qualified class for the qualified recipe (stage 0). Bit-exactness
is a construction fact verified empirically by the F1 replay. Unification is a new
packet with its own falsifier, never a silent refactor.

---

## FALSIFIERS

- **F1 — stage-0 frozen control.** Byte-identical status streams vs the qualified
  candidate on the full qualified command script (ULP-zero). Any difference REFUTES.
- **F2 — oracle agreement.** At every fixture pose: `M`, `gravity`, `bias`, point
  Jacobian each `≤ 1e-12` relative vs `Assembly`. Any larger deviation REFUTES the
  lift (the native side is then NOT the source model's dynamics).
- **F3 — mass identities.** `M` SPD (the native `inverse_spd` Cholesky must succeed),
  symmetric within `1e-12`, eigenvalues match the oracle's eigvalsh list within
  `1e-12` relative at every fixture pose; any violation REFUTES the assembly.
- **F4 — stop cascade determinism and correctness.** All 14 coordinate-bound
  landings hold `|q_i - bound| ≤ 1e-9` with the ledger closing; a scripted near-tie
  (two bounds within `1e-12·h`) produces IDENTICAL state hashes across two runs and
  applies the lowest-index stop first (impulse ledger inspection). Nondeterminism or a
  wrong-row application REFUTES the cascade law.
- **F5 — per-drive stores.** `battery_d ≥ 0` always; disabled/unpowered drives spend
  exactly 0; each depletion counted once per drive; totals equal the per-drive sums.
  Any violation REFUTES the store extension.
- **F6 — ledger closure.** `|balance_error_J| < 1e-5` and `|store_balance_error_J| <
  1e-5` on every status query of every stage and falsifier run; a single violation
  REFUTES the lift.
- **F7 — hand contact honesty.** The qualified friction slice's checks (press, cone
  `|f_t| ≤ μ·λ_n + 1e-9`, hold, heat) must pass at 7 coordinates and `mu = 0` must
  reproduce the frictionless world bit-exactly; a cone violation, an unaccounted heat
  term, or a `mu = 0` divergence REFUTES the contact lift.
- **F8 — no regression.** The qualified 2-coordinate scene compiles and qualifies
  green (its own scripts untouched) at EVERY stage; a red qualified world REFUTES the
  whole ladder regardless of the new stages' health.
- **F9 — performance budget.** The budgets below are falsifiable claims; a measured
  violation REFUTES the packet's budget section.

---

## PERFORMANCE BUDGET

Same derivation shape as `free_root_balance_v1.md`: `evaluate` grows `O(n²)` per body
(n: 2 → 7 ⇒ 12.25x the mass term), `inverse_spd` 2³ → 7³ (~60x a negligible term),
stops add ≤ 7 rows to the projection. Protocol (mandatory): measure the mounted
qualified median first (`M_mounted`, 10⁴ ticks, qualification box), then:

- 7-coordinate median tick wall time `≤ 3·M_mounted` and `≤ 0.5 ms` absolute;
- oracle suite (100 poses x M/gravity/bias/J) total wall `≤ 60 s`;
- status() serialization `≤ 2·M_mounted_status`.

Exceeding a budget means the implementation loops or allocates per stage — fix the
implementation or supersede the packet with a derived revision; do not silently ship.

---

## STAGED FILE PLAN

- `ChimeraEngine/engine/coupled_multidynamics.hpp` (NEW) — the n-coordinate solver
  (n = recipe-driven, 2..7): S1 cascade + generalized projection, S2 per-drive stores,
  S3 contact at n rows; stage-gated by the recipe's coordinate list; dispatches to the
  qualified class at the qualified recipe (S7).
- `ChimeraEngine/engine/coupled_dynamics.hpp` (UNTOUCHED — zero diff, F1's guarantee).
- `ChimeraEngine/engine/coupled_articulation.hpp` (UNTOUCHED; already n-generic).
- `ChimeraEngine/engine/engine.cpp` — serve the new scene kind on the same routes;
  construct per recipe (qualified class or multidynamics class).
- `tools/science_funnel/coupled_scene7.py` (NEW) — compiler for
  `chimera.coupled_scene7.v1` (pinned 7-coordinate order, 7 drive stems, per-drive
  battery contract, hand recipe unchanged); sibling; `coupled_scene.py` UNTOUCHED.
- `tools/science_funnel/tests/test_coupled_arm7.py` (NEW) — S6 oracle fixture
  (recorded seed, permutation map, `1e-12` comparisons) + offline unit checks per
  stage; grows per stage, green at every stage.
- `tools/science_funnel/tests/qualify_coupled_live7.py` (NEW) — staged live checks:
  F4 cascade, F5 stores, F7 contact slice, F1 replay, per-stage command scripts.
- `tools/creature_graph/validation/admit_coupled_arm7_<date>.py` (NEW, implementing
  lane, BEFORE code) — Rule-0 record for `model.dynamics.coupled_arm7`.
- `tools/science_funnel/check_packet.py` (EXISTS — this lane) — stays exit-0 over
  this packet after any revision.

---

## NON-CLAIMS (honest scope)

No free root (that is `free_root_balance_v1.md`'s scope); the sternum stays mounted
exactly as qualified. No muscles: source muscle records remain
`force_runtime_ready: false` with their stated reasons; drives are ideal capped
torque sources with finite per-drive stores. No grasping, no tendon routing, no
ConditionalPathPoint dynamics, no whole animal, no GPU residency, no empirical
validation against a living animal. The lift does not touch the qualified recipe,
compiler, class, or its live checks.

---

## RULE-0 ADMISSION RECORD

- Record id: `work.dynamics.seven_coordinate_lift_packet` (kind `work`, status
  `specified`, falsifier status `untested` — nothing here has been measured yet).
- Admission script: `tools/creature_graph/validation/admit_solver_packets_20260918.py`
  (owns exactly this id; refuses foreign content).
- Rebuild: `python -B tools/creature_graph/build_graph.py` (evidence count must remain
  11; work count grows by exactly the packets this lane admits).

The implementing lane supersedes with revision 2 as stages land, filling
`acceptance_test` with measured results per stage — never editing this packet's
claims silently.
