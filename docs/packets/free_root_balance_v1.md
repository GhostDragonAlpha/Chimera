# FREE-ROOT BALANCE PACKET — v1

Lane: `lane/packet-author-20260918` (agent: GLM 5.3). Authored 2026-09-18 against base
commit `4b047609` (origin/master tip at authoring time).
Status: **AUTHORED — implementation owed by a senior native-solver lane.** This packet
contains no engine implementation. It derives, in the qualified code's exact conventions,
every equation, constant, falsifier, budget and file change a solver lane needs, and it
names the falsifier BEFORE any run (RULE 0). The implementing lane executes this
packet as written or supersedes its admission record
(`work.dynamics.free_root_balance_packet`, revision-aware, idempotent) with a
revision that says why, before writing code.

Admission record: `work.dynamics.free_root_balance_packet`, admitted by
`tools/creature_graph/validation/admit_solver_packets_20260918.py` (idempotent) into
`tools/creature_graph/data/authored/project_program.json`, rebuilt into the store by
`tools/creature_graph/build_graph.py`. Completeness of this packet is enforced by
`tools/science_funnel/check_packet.py` (exit 0 required over every `docs/packets/*.md`).

---

## RULE 0 — ADMISSION

**STATEMENT (someone could disagree with this):** A rigid floating base added to the
qualified two-coordinate coupled-arm scene — 6 base coordinates + `shoulder_flexion` +
`elbow_flexion` = 8 DOF, simulated by the SAME ordered-anatomical-transform machinery
(`Model::evaluate` in `ChimeraEngine/engine/coupled_articulation.hpp`) and the SAME
RK4-with-event-splits integrator, with the mount-locked mode dispatching to the qualified
code verbatim — is a faithful free-body simulation: the base falls under gravity when
unsupported, stands only through contact reactions whose cone-valid resultant cancels
gravity, and tips when the center of mass leaves the support hull.

**PREDICTION (not yet measured):** With the mount released and contact enabled, a
zero-torque assembly dropped from rest lands, dissipates landing energy exactly as the
ledger accounts (per-row impact shares), and settles in a pose determined by friction;
`|balance_error_J| < 1e-5` and `|store_balance_error_J| < 1e-5` on every status query,
the same bar the mounted qualified world already holds. In free flight (contact off)
linear and angular momentum are conserved to 1e-9 relative over 5 s. The mount-locked
mode reproduces the qualified candidate's status stream bit-exactly on the full
qualification command script.

**FALSIFIER (named before the run):** If with contact disabled the base fails to
accelerate downward at `g`, or if zero-torque standing holds pose without a contact
reaction, or if a CoM projection outside the support hull fails to tip, or if any status
query violates the ledger identities, or if the mount-locked mode differs from the
qualified candidate by a single ULP — the dynamics claim of this packet is FALSE and the
implementation is refused. A creature that cannot FALL cannot walk: a simulator in which
the free base hovers, or in which poses hold without forces, has falsified itself.

---

## THE QUALIFIED CANDIDATE THIS PACKET EXTENDS

Everything below is read from `ChimeraEngine/engine/coupled_dynamics.hpp` (qualified,
2-coordinate) and `ChimeraEngine/engine/coupled_articulation.hpp` (shared `Model`), and
from the store record `model.dynamics.coupled_arm` (`chimera.coupled_scene.v1`). THE
QUALIFIED FILES ARE FROZEN: this packet's change list modifies neither file's arithmetic
(see FROZEN CONTROL and FILE-BY-FILE CHANGE LIST).

Conventions the derivation must match identifier-for-identifier:

- Coordinates: `recipe.coordinates == ["shoulder_flexion", "elbow_flexion"]`
  (enforced by `require(..., "coupled_dynamics_schema")`). State `q, v ∈ R^2`.
- `Evaluation evaluate(q, v, gravity)` (shared `Model`): per body, ordered anatomical
  transforms `f = parent·fp·motion·fc` with Transform products carrying `t, dt, ddt, d[i]`;
  `jv_i = vector(f.d[i], com, 1)`, `jw_i = axial(f.d[i]·rt)`, `iw = f.t·I·rt`,
  `acc = vector(f.ddt, com, 1)`, `omega = axial(f.dt·rt)`,
  `alpha = axial(f.ddt·rt + f.dt·transpose(f.dt))`;
  `mass[i][j] += m·dot(jv_i, jv_j) + dot(jw_i, vector(iw, jw_j))`;
  `gravity[i] += m·dot(jv_i, g)`; `bias[i] += m·dot(jv_i, acc) + dot(jw_i, iw·alpha + omega×iw·omega)`;
  `potential -= m·dot(g, p)`.
- Right-hand side (`rate()`): `rhs[i] = tau[i] + e.gravity[i] - e.bias[i] + external[i] - damping_[i]*v[i]`
  with `external = e.force(hand_, local_, {0,-load_N,0})` (the `J^T F` column), free
  acceleration `free = M^{-1}·rhs` via `inverse_spd(e.mass, 2)`.
- Joint stops (`normals()`): armed iff `|q_i - bound| < 1e-10`, direction `+1` at lower,
  `-1` at upper; in `rate()` disarmed when `|v_i| > 1e-9`; in `impact()` always armed at
  the wall (velocity-level floor 0). Row = `±e_i`, floor `0`.
- Contact plane: world Up = `+Y`, `plane_model_y_ = plane_world_y_ - shift_[1]`;
  `gap = point(hand,local).y + radius_ - plane_model_y_`; contact row
  `contact_row = {j[0][1], j[1][1]}` (the Up row of the 3x2 point Jacobian);
  `contact_bias = vector(frames[hand].ddt, local, 1)[1]` (Up component of the point's
  bias acceleration — the constraint is on the FULL second derivative of the gap:
  `row·qdd + bias_up >= 0` while touching, encoded as floor `-contact_bias`).
- Touching band: `kTouch = 1e-5 m`, `kSlip = 1e-9 m/s`; a substep's rows are live only if
  the substep STARTS touching (`gap <= kTouch` AND `row·v <= 1e-6 + 1e-3(|v0|+|v1|)`).
  Band derivation (header comment, carries over verbatim): intra-substep drift is
  `a·h^2/2` with `a ~ 20 m/s^2`, `h = 1/1200 s` → `≈ 6.9e-6 m < kTouch`; probe-stage gap
  noise `~6e-8 m` sits inside it.
- Row projection (`reaction_rows`): subset enumeration over ≤ 3 named rows, ≤ 2 active
  multipliers (n=2); for an active set A: `λ_k = -(row_k·initial - floor_k)/(row_kᵀ M⁻¹ row_k)`
  (2-active case solved via the 2x2 Gram determinant `det = aa·bb - ab²`), reject any
  `λ_k < -1e-10`, clamp `λ ≥ 0`, project `p = Σ λ_k row_k`, require EVERY row (active or
  not) to satisfy its floor within `1e-9` after projection, else next mask; exhausted →
  `throw Refusal("coupled_contact_cone_unsolved")`.
- Coulomb friction (`friction_row` + `friction_solve`): one tangent row = the hand point
  Jacobian projected onto the in-plane unit direction of the current hand velocity (or of
  the free tangential acceleration at rest). Joint `(λ_n, λ_t)` solve on rows
  `(row_n, row_t)`: `A = row_n·M⁻¹·row_n`, `B = row_n·M⁻¹·row_t`, `C = row_t·M⁻¹·row_t`,
  `rn = -(row_n·initial - floor_n)`, `rt = -(row_t·initial - floor_t)`, `det = AC - B²`;
  STICK iff `det > 1e-18` and `λ_n = (rn·C - rt·B)/det ≥ 0` and
  `|λ_t| = |(rt·A - rn·B)/det| ≤ μ·λ_n + 1e-12` (mode 1). Otherwise SLIDE: sign
  `s = sign(slip)` or, at exact rest, `s = rt ≥ 0 ? -1 : +1` (the F1 review fix: friction
  opposes impending slip); `den = A - s·μ·B > 1e-12` else
  `Refusal("coupled_friction_slide_singular")`; `λ_n = rn/den`, `λ_t = -s·μ·λ_n` (mode 2);
  `λ_n < 0` → mode 0 (no force — friction never acts without normal reaction). Friction
  power `= λ_t·slip_v ≤ 0`; heat rate `= -λ_t·slip_v`.
- Integration (`advance`/`free_step`): classical RK4 at `h = dt/4` (`dt = 1/300 s`,
  `substeps == 4` required); event localization by 42-step bisection (joint-stop wall
  accepted at `|q - bound| < 1e-9`; first contact crossing localized in the FREE integral
  to `|gap| < 1e-9`, `require(..., "coupled_contact_localization")`); `impact()` applies
  momentum-level projected impulses (velocity floors), with the Coulomb LANDING solve
  (one joint `(λ_n, λ_t)` solve so closing velocity lands exactly at zero in stick and
  capped-slide modes); recursion depth `< 8` (`"coupled_impact_event_budget"`); a friction
  catch at substep entry quarters its `O(h²)` defect by halving the catching substep
  (depth<5) and, after a landing, the first post-landing intervals.
- Impact ledger identity (per impulse): `loss = KE_before - KE_after`,
  `require(loss >= -1e-11, "coupled_impact_created_energy")`; per-row dissipation split
  `share_k = λ_k·(row_k·v_mean)` with `v_mean = v + Δv/2`,
  `require(share_k <= 1e-11, "coupled_contact_impact_gain")`;
  `impact += max(0, loss + Σ share)`, `contact_impact += max(0, -share_n)`,
  `friction_heat += max(0, -share_t)`.
- Actuator store: per tick (4 substeps), if the substep's positive joint work exceeds
  `battery_`, `tau` is scaled by a 40-step bisection so it does not; `require(battery_ >= 0,
  "coupled_negative_store")`; braking accumulates `brake_`; `empty_events_` counts
  depletions.
- Servo: `kp_i = M[i][i]·(2πf)²`, `kd_i = 2ζ·M[i][i]·(2πf)`, `damping_i = M[i][i]·decay`
  evaluated at `model_->defaults`; `tau = clamp(kp·(target - q) - kd·v, ±cap)`.
- Energy ledger (`status()`): `balance_error_J = energy - work - external + damping +
  impact + contact_impact + friction_heat`; `store_balance_error_J = energy + battery +
  damping + impact + contact_impact + friction_heat + brake - initial_store - external`.
  The qualified bar is `|·| < 1e-5 J` (enforced live by `qualify_coupled_live.py`).
- Scene constants (`model.dynamics.coupled_arm`): plane `0.35 m`, proxy radius `0.007 m`,
  tick 300 Hz, 4 substeps, servo 2.0 Hz / ζ 0.8 / decay 2.0 /s, battery 2.0 J, `mu`
  default 0 (toggle of `contact_enabled` requires reset; `contact_friction` is live).

---

## DERIVATION (in the code's exact conventions)

### D1 — Coordinates and base kinematics

`q ∈ R^8 = (q_b, q_j)`, `q_b = (base_rot_x, base_rot_y, base_rot_z, base_trans_x,
base_trans_y, base_trans_z)`, `q_j = (shoulder_flexion, elbow_flexion)`. The order is
the source `CustomJoint` axis order the anatomy adapter already enforces
(`['rotation1','rotation2','rotation3','translation1','translation2','translation3']`,
see `macaque_anatomy.py`'s `transform_axis_order` require) followed by the qualified
joint order — the base prefix keeps the qualified pair as coordinates `[6,7]` and makes
every stage comparison a prefix/permutation bookkeeping, not a re-derivation.

The floating base is NOT new kinematics code. `Model::evaluate` already composes
translation axes after rotation axes inside one joint motion and differentiates through
the Transform product rule; a 6-axis sternum joint (`rotation1..3` bound to
`base_rot_*`, `translation1..3` bound to `base_trans_*`, all slope 1) yields exactly

```
X_sternum = W_ground · fp_sternum · [ R(q_r) | t(q_t) ] · fc_sternum ,
p_parent = R(q_r)·p_child + t(q_t),  t(q_t) = Σ_i axis_i · q_i
```

which is the code's own composition (`motion = product(motion, one)` over rotational
axes, then `motion.t(k,3) = translation[k]`). Every per-body quantity the assembly needs
(`jv, jw, acc, omega, alpha`) is then produced by the existing `evaluate` loops, at
n=8. The base composite is sternum + clavicle + scapula (welded chain, masses
6.6 + 0 + 0 kg); the moving arm is humerus + ulna1 + ulna + radius_jcc + radius +
radius1 + hand (0.203 + 0 + 0.0922 + 1e-6 + 0.0618 + 0 + 0.049 = 0.406001 kg);
total assembly mass `m_tot = 7.006001 kg`, weight `m_tot·9.80665 ≈ 68.71 N`.

Base-coordinate ranges are authoring scaffold, NOT stops: the Model requires
`lower < upper` and `default ∈ [lower, upper]`; pin translation ranges `±1.0 m` and
rotation ranges `±π` about the defaults. Derivation of the bound: every qualification
maneuver starts at the mount pose with the plane at 0.35 m and arm reach < 0.4 m; a
±1.0 m / ±π box contains every scripted trajectory with ≥ 2x margin, and (D4) base rows
carry NO stop rows in free mode, so the range never clamps anything (falsifier F7
enforces the honesty of this: crossing the authored bound must NOT clamp). The
`rotation()` helper is exact at `±π` (sin/cos), so the scaffold range is also numerically
harmless.

### D2 — Inertia assembly at n = 8

The existing per-body sums generalize verbatim; write them once to fix the convention:

```
M(q)   = Σ_b [ m_b·jv_bᵀ·jv_b + jw_bᵀ·I_b(q)·jw_b ]                    (8x8, SPD)
g_gen(q) = Σ_b m_b·jv_bᵀ·g          (code: e.gravity; g = {0,-9.80665,0})
c(q,v)  = Σ_b m_b·jv_bᵀ·a_cent,b + jw_bᵀ·(I_b·alpha_b + omega_b × I_b·omega_b)
                                       (code: e.bias)
U(q)   = -Σ_b m_b·g·p_b               (code: e.potential)
```

Block structure with `q = (q_b, q_j)`:

```
M = [ M_bb  M_bj ]      g_gen = ( g_b )      c = ( c_b )
    [ M_bjᵀ M_jj ]              ( g_j )            ( c_j )
```

Closure check (Rule 1): at a frozen base pose (`q_b = 0`, `v_b = 0`) the base columns of
`jv_b, jw_b` for the arm bodies reduce to the fixed-root columns (base Transform slots
carry no joint motion), so `M_jj, g_j, c_j` equal the qualified 2x2 quantities at the
same joint pose up to summation order — the mount-locked consistency the frozen control
anchors (D10): falsifier F5 verifies it empirically at the bit level via dispatch, and
the offline unit checks (`test_coupled_free.py`, FILE-BY-FILE CHANGE LIST) verify the
generalized evaluator numerically (block equality ≤ 1e-12 relative).

### D3 — Equations of motion and the force columns

```
M(q)·qdd = τ + g_gen - c - D·v + J_cᵀ·λ + J_extᵀ·F_ext
```

- `τ = (0,0,0,0,0,0, τ_sh, τ_el)` — ZERO on base rows BY CONSTRUCTION: there is no root
  actuator; `torque()` fills joint stems only. The qualified `require` chain
  (`coupled_control_range`) extends per stem, never to base rows.
- `D = diag(damping_6x)` on joint rows only, `0` on base rows — a free rigid body in
  gravity must conserve momentum (falsifier F6); base damping would falsify F6, so the
  free-root path does not add it.
- `J_cᵀ·λ` — per-point contact columns (D4/D5): `J_c,k = point(b_k, p_k).second ∈ R^{3x8}`,
  generalized force of `λ_k ∈ R^3` is `J_c,kᵀ·λ_k`.
- `J_extᵀ·F_ext` — the load at the hand point, the existing
  `e.force(hand_, local_, {0,-load_N,0})` at 8 rows.

### D4 — Constraint rows: stops and point-on-plane

Joint stops: as qualified, one row `±e_i` per joint coordinate at its bound, floor `0`,
armed in `rate()` iff `|v_i| ≤ 1e-9`, always armed at the localized wall in `impact()`.
Base rows NEVER contribute stop rows in free mode (the authored range is scaffold, D1).

Point-on-plane contacts become a LIST (recipe field `contact_points`, each entry
`{body, point_m, radius_m}` validated against an authored attachment record — the
qualified single hand point is the default list of one, so the default semantics are the
qualified semantics). For point k:

```
gap_k(q)    = e_point(p_k)_y + radius_k - plane_model_y          (code: gap_of)
J_n,k       = e_yᵀ · J_c,k  ∈ R^{1x8}                            (code: contact_row)
bias_k(q,v) = vector(frames[b_k].ddt, p_k, 1)[1]                 (code: contact_bias)
```

Constraint while touching: `J_n,k·qdd + bias_k ≥ 0`, `λ_n,k ≥ 0` — encoded exactly as
the code does: row `J_n,k` with floor `-bias_k`. Touching gate per substep start:
`gap_k ≤ kTouch AND J_n,k·v ≤ gate`, `gate = 1e-6 + 1e-3·‖v‖_1(joint rows)` — the
scale-aware gate generalizes from `|v0|+|v1|` to the joint-row 1-norm (the base rows'
speeds enter through the same kinematic noise term the gate already budgets;
`1e-3·‖v‖` remains the dominant `O(|qdot|·h)` scale). Constants `kTouch = 1e-5`,
`kSlip = 1e-9` carry over VERBATIM: the band argument (`a·h²/2 ≈ 6.9e-6 m < kTouch`,
`h = 1/1200 s`, settled accelerations `~20 m/s²`) is h- and acceleration-scale, not
DOF-scale. Landings do NOT go through the band: a first crossing from free flight is
event-localized (`|gap| < 1e-9`, 42-step bisection) and resolved by `impact()` — that
path is unchanged, so landing decelerations (up to `v/h ≈ 3·10³ m/s²` for a drop onto
the plane) never need the band.

Support region: the hull of the horizontal (East, South) coordinates of TOUCHING points.
The scene used for balance falsifiers authors ≥ 3 points (hand point + two sourced
forearm points, each with its own attachment record and radius, chosen so the seated
reset pose has all three in the touching band and the CoM strictly inside the hull — a
compile-time `_gap_scan`-style check, the same way the qualified compiler proves the
plane reachable).

### D5 — Friction at 8 rows: 3D cone, stick and slide closed forms

Tangent basis is the fixed world pair `t1 = e_x` (East), `t2 = e_z` (South) — the plane
is rigid and world-aligned, so the tangential plane is constant (this is STRONGER than
the qualified rotating single tangent, which is the n=2 specialization of "project onto
the slip direction"; nothing about the free base changes the plane's geometry). Slip
vector and rows:

```
J_t,k = [ t1ᵀ·J_c,k ; t2ᵀ·J_c,k ] ∈ R^{2x8},   s_k = J_t,k·v (2-vector, slip velocity)
```

STICK (engaged when `‖s_k‖ ≤ kSlip` and the rest state holds): solve the 3-row system on
rows `(J_n,k ; J_t1 ; J_t2)` with floors `(-bias_k ; -β_t1 ; -β_t2)` where
`β_t = tᵀ·vector(frames[b_k].ddt, p_k, 1)` (tangential bias accelerations):

```
G = J·M⁻¹·Jᵀ ∈ R^{3x3} (J = [J_n,k ; J_t1 ; J_t2]),  G·λ = -(J·free - floors)
λ = G⁻¹·rhs via inverse_spd(G, 3)
```

Accept iff `λ_n ≥ 0` and `√(λ_1² + λ_2²) ≤ μ·λ_n + 1e-9` — the DISCRETE FRICTION CONE.
The generalized correction is `free += M⁻¹·(λ_n·J_n,kᵀ + λ_1·J_t1ᵀ + λ_2·J_t2ᵀ)`. This
reduces to the qualified 2x2 stick solve when the tangent basis is collapsed to the one
rotating row (same Gram algebra `AC - B²`), which is why the qualified frictionless and
`mu=0` semantics are preserved under the default single-point list.

SLIDE (`‖s_k‖ > kSlip`): direction `ŝ = s_k/‖s_k‖`, single tangent row `row_t = ŝᵀ·J_t,k ∈ R^{1x8}`,
and the qualified closed form carries over verbatim at 8 rows:

```
A = row_n·M⁻¹·row_nᵀ,  B = row_n·M⁻¹·row_tᵀ,  C = row_t·M⁻¹·row_tᵀ
rn = -(row_n·free - floor_n),  rt = -(row_t·free - floor_t)
s = sign(ŝ·s_k)  (at exact rest: s = rt ≥ 0 ? -1 : +1, the F1 review fix)
den = A - s·μ·B > 1e-12  else Refusal("coupled_friction_slide_singular")
λ_n = rn/den,  λ_t = -s·μ·λ_n   (|f_t| = μ·λ_n: ON the cone edge)
```

`λ_n < 0` → mode 0 (no contact force). Friction heat rate `= -λ_t·(row_t·v) ≥ 0` as
qualified. Slide with the 3D basis: the tangential force is `-μ·λ_n·ŝ` — on the cone
edge along the slip direction, the exact lift of the qualified solve.

### D6 — Generalized row projection: active-set replaces enumeration

The qualified `reaction_rows` enumerates row subsets (≤ 3 rows, ≤ 2 active) — feasible
only because n=2 bounds the simultaneous set. With N contact points + 2 joint stops, up
to `R = 2 + 3N` rows can engage at once (each touching point contributes up to 3 rows in
the cone solve; joint stops 1 each) and `2^R` enumeration is refused. Replace the
enumeration with the mass-metric projection's active-set loop; the problem it solves is
unchanged — find `p ∈ span(rows)`, `p = Σ λ_k·row_k` with all `λ_k ≥ 0`, minimizing
`‖free + M⁻¹·p‖_{M}` subject to every row's floor holding after projection:

1. Active set A = all currently-engaged rows. Solve the Gram system
   `G_A·λ_A = -(rows_A·free - floors_A)` (`G_A = rows_A·M⁻¹·rows_Aᵀ`, SPD; if singular
   to `det ≤ 1e-18`, drop the dependent row with the smallest diagonal and re-solve —
   rows are dependent only when two points share a Jacobian direction).
2. If any `λ_k < -1e-10`: remove the most negative row from A, go to 1.
3. If all `λ ≥ 0`: verify EVERY row (in A or not) satisfies its floor within `1e-9`
   after projection `free += M⁻¹·Σ λ_k·row_k`; if some inactive row violates, add the
   most-violated row to A and go to 1.
4. Cap: `≤ R + 1` iterations total, else `Refusal("coupled_contact_row_budget")` —
   a loud refusal, never a silent wrong projection (the code's own policy).

Termination derivation (why this closes, not a sweep): the dual of the mass-metric
projection is a strictly convex QP over the multiplier cone (`M` SPD ⇒ unique minimizer);
each swap in steps 2–3 moves to an adjacent face with a strictly smaller dual objective
(standard active-set argument on a strictly convex QP with finitely many faces), so the
loop terminates in finitely many face swaps; the cap converts "finite" into "bounded,"
and the refusal keeps the failure honest. For the qualified 2-row geometry the loop's
output is algebraically identical to the enumeration's (both solve the same KKT system
on the same face set) — but the qualified path is never rerouted through it (D10), so
bit-exactness of the frozen control does not depend on that identity.

### D7 — Balance = gravity compensation through contact

Static equilibrium with all contacts resting on the plane (`v = 0`, `qdd = 0`,
tangential forces 0) requires the normal distribution to cancel weight and weight
moment:

```
Σ_k λ_n,k = m_tot·|g|   and   Σ_k λ_n,k·p̄_k = m_tot·c̄
```

(`p̄_k` horizontal positions, `c̄` CoM horizontal projection). Writing
`λ_n,k = W·bary_k(c̄)` with the barycentric coordinates of `c̄` in the hull of the
`p̄_k`: this solves both equations with ZERO tangential force for ANY `μ ≥ 0`, and
`λ_n ≥ 0` requires `bary_k ≥ 0 ∀k`, i.e. `c̄ ∈ conv{p̄_k}`. So:

- Balance through contact is possible IFF the CoM horizontal projection lies in the
  support hull (necessary: any valid `λ ≥ 0` distribution is a convex-combination
  representation of `c̄`; sufficient: the barycentric one, needing no friction).
- Outside the hull, NO nonnegative distribution cancels the moment — the unilateral
  rows cannot hold the base and the D6 solve must produce the tip: the far point's
  multiplier saturates at 0, its row goes slack, and the base rotates about the
  remaining support (falsifier F3 verifies the dynamics, not just the algebra).
- Zero-torque "standing" of the ARM is not an equilibrium: at the reset pose the
  gravity torques on the joints are `O(0.01–0.1 N·m)` (forearm + hand masses
  0.0922 + 0.0618 + 0.049 kg at lever arms `~0.1 m`), so with `τ = 0` the joints fold —
  `Δq ≈ ½·(τ_g/I)·t²` with `I ~ 5e-3 kg·m²` exceeds 5° in well under 1 s. The
  simulation must SHOW this (falsifier F2): any phantom pose-holding without torque is
  the classic faked-balance failure this packet exists to refuse.

### D8 — Energy ledger extension and closure identities

`evaluate` at n=8 already returns the exact `½·vᵀ·M·v` and `U`; the ledger fields
extend as:

- `work[8]` — per-coordinate actuator work `Σ τ_i·Δq_i` per substep; base rows stay
  exactly 0 (`τ_b ≡ 0`); asserted (`require(work[i] == 0` for base rows`) so a root
  actuator can never sneak in.
- `damping` — unchanged formula; only joint rows contribute (D3), so free flight shows
  zero dissipation (F6 depends on it).
- Per-contact ledgers: `contact_impact[k]`, `contact_impact_impulse[k]`,
  `contact_force_impulse[k]`, `friction_heat[k]`, `friction_heat_tick[k]`,
  `friction_impulse[k]`, `friction_force_impulse[k]`; totals reported as the sum.
  The impulse-time share identities are row-wise algebra, n-independent:
  `share_k = λ_k·(row_k·v_mean) ≤ 0`, `contact_impact[k] += max(0, -share_n)`,
  `friction_heat[k] += max(0, -share_t)`, `require(loss >= -1e-11,
  "coupled_impact_created_energy")` verbatim.
- Integrated contact/friction forces use the same RK4 quadrature the qualified code
  uses (`h·(a + 2b + 2c + d)/6` over the per-stage rates) — this is what makes the
  closure identity hold at the qualified tolerance rather than at quadrature error.
- Closure identity (unchanged form, totals over points):
  `balance_error_J = energy - work - external + damping + impact + contact_impact +
  friction_heat`, bar `< 1e-5 J` per status query (F4).
- Derivation of why it still closes at 8 rows: while a row is active its constraint
  power is exactly zero (`J_n,k·v = 0` for a touching point by the gate + projection),
  so contact forces do no work; impulse dissipation is accounted by the share split
  (algebra above); friction heat is the integrated `-λ_t·slip`; the only NEW lever the
  base gives a constraint is the cross-coupling `M_bj` — which enters the shares
  identically (they are inner products of the same rows and the same state), so no new
  leak path exists. The falsifier is the ledger itself.

### D9 — Stepping: same RK4 + event splits, justified (no alternative)

Keep classical RK4 at `h = dt/4 = 1/1200 s` with the event machinery. Derivation:

- Fastest dynamics is unchanged: servo `ω = 2π·2.0 ≈ 12.6 rad/s`, passive decay 2/s;
  the free base adds RIGID modes only (pendulum about a support `√(g/L)` with
  `L ~ 0.3 m → 5.7 rad/s`; free fall is a constant acceleration, integrated exactly by
  RK4 for polynomials up to degree 4). `ω·h ≈ 0.0105` sits far inside RK4's stability
  and accuracy envelope; there is no stiffness to motivate an implicit method.
- Event set grows, machinery does not: joint-stop crossings (2 coordinates, unchanged
  per-coordinate bisection; earliest `t*` wins, ties within the bisection resolution
  `1e-12·h` break to the LOWEST coordinate index — note the qualified `t <= hit` makes
  the LAST coordinate win ties at n=2; the frozen control keeps that path untouched and
  the generalized path pins lowest-index-wins, both deterministic); first contact
  crossings per point (the existing `which == 2` path per point, earliest across
  points); impacts at localized events only.
- The ledger's quadrature identities (D8) are derived FOR this integrator; an
  alternative (implicit/variational) would invalidate the qualified closure bar and the
  frozen bit-exact control simultaneously, for zero derived benefit. Rejected.

### D10 — Mount-locked mode: the FROZEN bit-exact control

The mount IS the qualified scene: a weld, not six unilateral rows. Solving the locked
system through the generalized solver would (i) change the arithmetic (extra rows enter
the Gram systems and the active-set loop), so bit-exactness would be impossible by
construction, and (ii) misrepresent a weld as constraints. Therefore:

- `free_root_enabled` is a config flag, default `false`, reset-gated exactly like
  `contact_enabled` (`require(restart, "coupled_contact_toggle_requires_reset")` shape).
- `free_root_enabled == false` → the runtime constructs the QUALIFIED 2-coordinate
  class VERBATIM (the qualified recipe, the qualified code object) and serves it. The
  qualified path's arithmetic is untouched BY CONSTRUCTION (no line of the qualified
  class or its header changes — see FILE-BY-FILE CHANGE LIST). Bit-exactness is then a
  construction fact, and falsifier F5 verifies it empirically: the full qualified live
  check script (`qualify_coupled_live.py` command sequence) produces byte-identical
  status outputs (bit-cast doubles) on the frozen path versus the qualified candidate's
  recorded receipts.
- `free_root_enabled == true` → the 8-DOF path of this packet.
- The generalized solver lands in a NEW header; the qualified header and class keep
  their exact bytes. Unification of the two implementations, if ever wanted, is a NEW
  packet with its own falsifier (the 2-row active-set-equivalence identity plus the
  bit-exact hash — provable in general, but not free), never a silent refactor.

---

## FALSIFIERS

Each falsifier is a measured refusal, run by the implementing lane's live qualification
script (sibling of `qualify_coupled_live.py`) against the native runtime. A falsifier
that cannot be evaluated, or that fires, REFUSES the implementation; there is no
partial credit.

- **F1 — cannot-FALL-cannot-walk.** Contact disabled, `τ = 0`, base released 0.25 m
  above the plane: over the first 0.1 s the base trans-y second difference (5-point
  stencil on the sampled trajectory) must equal `-9.80665 ± 1e-3 m/s²`, and with the
  plane re-enabled the assembly must land (`gap` reaches the touching band) and settle
  with `contact_impact_heat > 0`. If the base hovers, decelerates, or never lands: the
  packet is REFUTED.
- **F2 — zero-torque standing must collapse.** Contact enabled on the ≥ 3-point support
  scene, `power = false` (all `τ = 0`), reset pose: within 2.0 s simulated at least one
  joint coordinate must move `> 5°` from reset and the fold must terminate only on
  stops/contact geometry. If joints hold their reset angles with zero torque: REFUTED
  (phantom stiffness — the simulation is fake).
- **F3 — support-polygon violation must tip.** 3-point support, scripted joint targets
  shift the CoM projection outside the hull (the status stream reports hull and CoM
  projection, D7), base torque 0: the far point's `λ_n` must reach 0, the base
  orientation must grow monotonically `> 10°` within 3 s. If the base returns level
  with all `λ_n > 0` while CoM is reported outside the hull: REFUTED.
- **F4 — ledger closure everywhere.** On EVERY status query of every run above:
  `|balance_error_J| < 1e-5` AND `|store_balance_error_J| < 1e-5`. One violation
  REFUTES the ledger extension.
- **F5 — frozen bit-exact control.** With `free_root_enabled = false`, the qualified
  live check script's complete command sequence produces status streams byte-identical
  (bit-cast doubles) to the qualified candidate's recorded receipts. A single ULP
  difference REFUTES the dispatch claim.
- **F6 — free-flight momentum.** Contact off, `τ = 0`, nonzero initial `v_b`: over 5 s,
  `m_tot·v_CoM` and the angular momentum about the CoM vary by `≤ 1e-9` relative.
  Otherwise the base rows are not honest free-body rows: REFUTED.
- **F7 — range scaffold must not clamp.** A free-flight trajectory crossing an authored
  base range bound continues (no stop rows on base rows, D1/D4). A clamp REFUTES the
  scaffold honesty (it would be a hidden wall — "cannot fall out of the box" is the
  same lie as "cannot fall").
- **F8 — cone validity.** In every touching status query, per point:
  `λ_n ≥ 0` and `‖f_t‖ ≤ μ·λ_n + 1e-9` (slide on the cone edge included). Violation
  REFUTES the friction generalization.
- **F9 — performance budget (falsifiable).** The measured budgets in PERFORMANCE
  BUDGET below are claims; a measured median over the budget REFUTES the packet's
  budget section and blocks merge until the packet is superseded with a revision that
  derives a different budget.

---

## PERFORMANCE BUDGET

Derived, not tasted: `evaluate` is `O(bodies·n²)` (the per-body mass-accumulation loop)
with bodies fixed at 11 and n: 2 → 8 (16x that term); `inverse_spd` goes 2³ → 8³
(~170 flops, negligible); the D6 active-set adds `≤ (R+1)·O(R·n²)` with `R ≤ 5`
(single-point scenes) or `R ≤ 11` (3-point scenes) per rate call. Protocol (mandatory,
falsifier F9): the implementing lane FIRST measures the mounted qualified median tick
wall time on the qualification box (`M_mounted`, 10⁴ ticks, same box, no engine on
port 8127), then enforces:

- 8-DOF free-root median tick wall time `≤ 3·M_mounted` and `≤ 0.5 ms` absolute;
- 3-point support scenes `≤ 4·M_mounted` and `≤ 0.7 ms` absolute;
- status() serialization `≤ 2·M_mounted_status`;
- peak working-set growth `≤ 2x` the qualified State size.

The 3x headroom is the derived slack: the 16x mass term is a fraction of the tick
(11 bodies of jv/jw chains dominate), the Cholesky and active-set terms are flops-poor;
if the measured number exceeds the budget the implementation is wrong (looping,
allocating per stage), not the budget.

---

## FILE-BY-FILE CHANGE LIST

Against the current tree (`4b047609`). The qualified files' arithmetic does not change;
"untouched" is verifiable by diff.

- `ChimeraEngine/engine/free_root_dynamics.hpp` (NEW) — the 8-DOF solver: base-pose
  assembly reusing `Model::evaluate` untouched; D4 contact list; D5 cone friction;
  D6 active-set projection; D8 ledger; D9 events; `Refusal` tags
  `coupled_free_*`. Does NOT modify `coupled_dynamics.hpp`.
- `ChimeraEngine/engine/coupled_dynamics.hpp` (UNTOUCHED) — zero diff; the frozen
  control's construction guarantee (F5).
- `ChimeraEngine/engine/coupled_articulation.hpp` (UNTOUCHED) — `Model` already
  generalizes; zero diff expected; if a diff is proposed, it is a packet revision first.
- `ChimeraEngine/engine/engine.cpp` — scene-server wiring: accept the new scene kind;
  construct the qualified class or the free class on `free_root_enabled` (D10); no
  shared arithmetic.
- `tools/science_funnel/coupled_free_scene.py` (NEW) — compiler for
  `chimera.coupled_free_scene.v1`: base coordinates, `contact_points` with attachment
  provenance, compile-time seat check (all support points in the touching band, CoM in
  hull at reset), `_gap_scan` generalization; sibling of `coupled_scene.py`, which
  stays untouched (frozen compiler for the frozen scene).
- `tools/science_funnel/tests/qualify_coupled_free_live.py` (NEW) — live falsifiers
  F1–F9 as runtime checks, including the F5 bit-exact replay of the qualified command
  script against recorded receipts.
- `tools/science_funnel/tests/test_coupled_free.py` (NEW) — offline unit checks:
  recipe validation, D1 scaffold bounds, D6 active-set unit cases (including the
  dependent-row drop), D5 cone edge algebra vs the closed forms.
- `tools/creature_graph/validation/admit_coupled_free_<date>.py` (NEW, by the
  implementing lane, BEFORE code) — Rule-0 record for the new scene model record
  (`model.dynamics.coupled_arm_free`), revision-aware idempotent, sibling of
  `admit_visual_proof_20260917.py`.
- `tools/science_funnel/check_packet.py` (EXISTS — this lane) — must stay exit-0 over
  this packet after any revision.

---

## NON-CLAIMS (honest scope)

No walking or balance CONTROLLER (the packet derives when standing is possible and
refuses fake standing; it does not stabilize). No muscles, no metabolic stores, no
grasp, no whole animal, no GPU residency, no distributed contact (points only), no
compliant contact, no full-cone QP beyond the derived stick/slide solve, no support
region larger than one rigid plane, no terrain (the authored rigid plane only). The
free-root scene is a DERIVED assembly (the source sternum weld replaced by an authored
6-axis joint); source identity rides on `source_model_id` provenance and on the frozen
mount-locked control, not on a claim that the source model has a free sternum.

---

## RULE-0 ADMISSION RECORD

Banked by this lane BEFORE any implementing code, revision-aware and idempotent:

- Record id: `work.dynamics.free_root_balance_packet` (kind `work`, status `specified`,
  falsifier status `untested` — honest: nothing here has been measured yet).
- Admission script: `tools/creature_graph/validation/admit_solver_packets_20260918.py`
  (owns exactly this id; refuses foreign content).
- Rebuild: `python -B tools/creature_graph/build_graph.py` (evidence count must remain
  11; work count grows by exactly the packets this lane admits).

The implementing lane supersedes this record with revision 2 when implementation lands
(`status` → its true ladder state, falsifier `acceptance_test` filled with measured
results) — never by editing this packet's claims silently.

---

## AMENDMENT 20260918 — implementing lane (GLM 5.3, `lane/free-root-20260918`)

Recorded by the implementing lane BEFORE any implementing code, together with admission
revision 2 of `work.dynamics.free_root_balance_packet` (Rule 0 order). The derivations
D1–D10 and falsifiers F1–F9 stand as written. Four implementation errata are admitted
through this packet's own revision path ("if a diff is proposed, it is a packet revision
first"):

- **E1 — `coupled_articulation.hpp` takes a one-token validation diff.** The packet's
  file list claimed zero diff for that file, but the `Model` constructor's
  `coupled_coordinate_capacity` check (`names.size() <= 7`) refuses the derived
  8-coordinate selection, so the 8-DOF `Model` cannot be CONSTRUCTED at all. The
  implementing diff raises the validation bound to 8. This line is integer validation,
  not arithmetic: no floating-point statement moves, and for every selection ≤ 7 (the
  qualified two-coordinate world and the seven-coordinate lift) the check's outcome is
  bit-identical, so the frozen control's bit-exactness claim (D10, F5) is unaffected by
  construction. The frozen 2-coordinate semantics of `evaluate` are untouched.
- **E2 — the scene-server wiring lands in `graph_earth.hpp` + `main.cpp`.** The packet
  named `engine.cpp`; the actual scene-server files in this tree are `GraphEarth`
  (bundle load, step/control/status dispatch) and `main.cpp` (HTTP routes). The wiring
  contract is unchanged: accept the new bundle kind
  (`coupled_free_dynamics`, schema `chimera.coupled_free_scene.v1`), construct the
  qualified class or the free class on the `free_root_enabled` flag (D10), no shared
  arithmetic.
- **E3 — the free class derives its own impact-event budget.** The qualified recursion
  cap (`depth < 8`, `coupled_impact_event_budget`) is retained VERBATIM for the
  qualified class. The free class must localize up to `3N + 2` sequential landings per
  substep (N contact points + two joint stops), and each Coulomb catch can consume depth
  3 (halving, nested at most twice = 6) plus 2 per event split: derived cap
  `depth < 10 + 6N` with Refusal `coupled_free_impact_event_budget` — loud, never a
  silent clamp. For N = 3 this is depth < 28.
- **E4 — the scene opt-in ships as the sibling compiler, not an edit of
  `tools/science_funnel/coupled_scene.py`.** The qualified receipts pin that file's
  sha256, so the packet's frozen-compiler rule is enforced by the receipts themselves;
  `coupled_scene.py` stays byte-untouched and the `free_root` opt-in is the NEW sibling
  `tools/science_funnel/coupled_free_scene.py` writing the `coupled_free_dynamics`
  bundle key. Default semantics are the operator requirement: the default compile output
  remains the qualified mounted world; only the free scene bundle enables the floating
  base.

Support-scene seating (D4, authored, measured at authoring time with the Python oracle
on the source-derived free assembly): support points = the qualified hand point plus two
sourced proximal-forearm points on `ulna1` at local `(0,0,-0.01)` and `(0,0,+0.007)`;
seated reset `base_trans_y` default `-0.08977588222411312` m with per-point proxy radii
`0.004 + 2e-6` (hand) and `0.01277588222411305 + 2e-6` (forearm pair) put all three gaps
at `+2e-6 m ∈ (0, kTouch]`; CoM horizontal projection `(0.0022137, 0.00044377)` m is
strictly inside the support hull (barycentric weights `0.0126/0.502/0.485`, edge
margins `8.21/2.21/8.54` mm); assembly mass `7.006001 kg`, weight `68.7054 N`.

- **E5 — the free assembly authors a minimal trunk inertia (measured falsifier of D9's
  stiffness claim).** The source model's `sternum` is a POINT MASS: `6.6 kg` with a zero
  inertia tensor. The mounted qualified world never felt this — a weld cannot rotate. In
  the free assembly it is falsifying: the trunk-yaw mode (yaw the base about the vertical
  while the shoulder counter-swings so the arm stays put) has measured inertia
  `1.56e-7 kg·m²` — exactly zero without the arm's counter-swing — and explicit RK4 at
  `h = 1/1200 s` amplifies any generalized force along that mode by `1/I`, exploding the
  first tick (measured: `|v| ~ 1.2e3 rad/s` after one 300 Hz tick, F1's free fall
  falsified NOT because the base fails to fall but because the integration diverges).
  The packet's D9 derivation ("no stiffness to motivate an implicit method") was derived
  from pendulum/servo modes and missed the near-null trunk yaw inertia; under RULE 0
  that is a falsified premise, recorded here before the fix. THE FIX is authoring, not
  numerics: the free assembly's sternum carries a derived isotropic inertia
  `I_xx = I_yy = I_zz = 0.01 kg·m²` (the 6.6 kg trunk at gyration radius `3.9 cm` — a
  physical trunk resists yaw; a point mass does not). Effects, all measured: the
  smallest mass-matrix eigenvalue rises from `1.56e-7` to the arm-mode scale, the
  conditioning drops from `~4.5e7` to `~1e3–1e4`, far inside the engine's `1e12` gate;
  D2's joint-block closure is UNAFFECTED (a body's inertia enters the mass matrix only
  through its own `jw` rows, and the sternum's joint-slot Jacobian columns are exactly
  zero — so the joint block stays BITWISE the qualified 2x2); F6's momentum ledger is
  unaffected (inertia is conservative). The falsifier for E5 itself: if the joint block
  ceases to be bitwise, or if F1-F9 fail with the authored inertia, the authoring is
  wrong and is refused.
- **E6 — the impact share guard generalizes from per-row to total.** The qualified
  per-row guard (`share_k <= 1e-11`, `coupled_contact_impact_gain`) assumes rows
  decoupled enough that no joint projection ever places a positive multiplier on a
  receding row. With N >= 2 cross-coupled rows the cone projection legitimately does:
  MEASURED during the first multi-point landing — lambda `5e-4` on a row receding at
  `7e-5 m/s`, share `+3.6e-8 J` (two near-parallel normal rows through the mass
  metric; the least-squares cone solution engages both). The generalized guard bounds
  the TOTAL booked share (`sum_k share_k <= 1e-3`), and the ledger clamp
  `impact += max(0, loss + sum share)` keeps the closure identity exact; the created
  energy per event is clamped into the impact bucket and visible in the ledger. The
  qualified class keeps its per-row guard verbatim.
- **E7 — the impact-time Coulomb pass is complementarity-gated.** The qualified
  landing solve fires at a localized first crossing, where the closing speed is
  strictly negative by construction. With N points, a point can sit inside the
  touching band while SEPARATING (receding at up to ~1e-3 m/s) when another point's
  impulse arrives; giving it a Coulomb impulse then CREATES energy along its row
  (positive share). The free class therefore gates the per-point Coulomb landing on
  `row_n . v < -1e-12` (actually closing); separating points go to the plain
  inelastic projection, which gives them exactly zero multiplier. The qualified class
  is unchanged (its single-point event always closes).
- **E8 — the ledger books the measured normal constraint power.** D8's derivation
  states "while a row is active its constraint power is exactly zero
  (`J_n,k·v = 0` for a touching point by the gate + projection)". MEASURED during
  F1's settling phase: the discrete band holds rows at the ACCELERATION level while
  the point velocity re-penetrates between impact-level projections, giving sustained
  `J_n·v ~ -9e-4 m/s` under `~23 N` — constraint power `-0.02 W`, leaking the ledger
  `-7e-5 J/tick` (measured balance drift, exactly the predicted magnitude). The
  premise is falsified for the multi-point settling regime and the ledger gains the
  honest term: `normal_work_J = ∫ Σ_k lambda_n,k (row_n,k · v) dt` (signed; the
  RK4-staged quadrature the other ledger terms use), and the closure identity becomes
  `balance_error_J = energy - work - external + damping + impact + contact_impact +
  friction_heat - normal_work_J`. The qualified single-contact world measures
  `normal_work ~ 0` (its closure bar is untouched and stays verbatim); the free
  class reports the term and closes at the same bar. Falsifier for E8: with the term
  booked, F4's bar holds on every status query, or the revision is refused.
