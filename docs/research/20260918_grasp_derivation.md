# 2026-09-18 — bounded grasp contract

## Rule-0 admission

**Statement.** A bounded grasp of the 2-coordinate arm is a reaction pair from a spherical hand proxy between two opposing parallel planes, with squeeze work charged to a finite actuator store and tangential reactions constrained by the pair Coulomb cone; it is not a claim that the pair alone immobilizes both joint coordinates.

**Prediction.** At the settled 20° shoulder / 20° elbow pre-study pose, the two plane-normal rows are exact negatives and therefore have rank one, while the independent normal/tangent rows have a nonzero mass-metric determinant; a capped catch will remove the normal closing speed, dissipate a nonnegative amount of kinetic energy, and charge no squeeze work unless the planes are actively closed.

**Falsifiers, named before implementation:**

1. A grasp that pulls the planes together without a store debit is not grasp (energy falsifier).
2. `|f_pair| <= mu * (lambda_n1 + lambda_n2)` must hold at every grasp state (Coulomb-cone falsifier).
3. Releasing one plane must return **exactly** the qualified frictionless/contact control bit-for-bit.
4. A zero-squeeze grasp must be bit-identical to the qualified friction world.

This document is a derivation and admission only. No runtime grasp behavior is implemented here.

## Qualified scope and references

The qualified baseline is the source-derived, fixed-root, two-coordinate native arm in `ChimeraEngine/engine/coupled_dynamics.hpp`. Its prior receipts are:

- `tools/science_funnel/validation/coupled_contact_20260917/receipt.json`
- `tools/science_funnel/validation/coupled_friction_20260917/receipt.json`

The friction receipt's independent review is authoritative for the known findings: the exact-rest slide-sign branch is a minor queued issue, the critical-`mu` hold/slide pair was not exercised, generalized-reaction and impact-cone assertions were not yet guarding assertions, and the live scope string still under-claimed friction. None of those findings is silently promoted to a grasp result.

The numerical pre-study uses `tools/science_funnel/coupled_arm.py`, which is a 7-coordinate analytic reference. The study selects the source shoulder-flexion and elbow-flexion rows from its 7-coordinate mass matrix and point Jacobian; it does not modify the reference or claim the other five coordinates are dynamically free.

## 1. Geometry and contact-row rank

Let `q = (q_s, q_e)` be the two live coordinates, `x(q)` the hand-proxy center in the plane's local frame, `r` the proxy radius, and `n = (0,1)` the world-Up normal. Place the parallel planes at `n·x = -d/2` and `n·x = +d/2`. Their signed nonpenetration gaps are

```
g_1(q) = n·x(q) + d/2 - r >= 0,
g_2(q) = d/2 - n·x(q) - r >= 0.
```

With `J = ∂x/∂q` (2×2 in this slice), define the Up row

```
a = nᵀ J = [∂x_y/∂q_s, ∂x_y/∂q_e].
```

The second plane's row is its negation, so the unilateral contact matrix is

```
G_pair = [ a ; -a ],       det(G_pair) = 0,       rank(G_pair) <= 1.
```

This is not a numerical accident. Two parallel planes acting on one spherical center measure the same scalar center displacement with opposite signs. If `a != 0`, both unilateral rows can be active as a **reaction pair**, but they span one direction in the two-dimensional joint space. Their generalized reaction is

```
tau_contact = aᵀ (lambda_n1 - lambda_n2),
λ_n1 >= 0, λ_n2 >= 0.
```

The sum `lambda_n1 + lambda_n2` is the internal squeeze load; it cancels from the net joint generalized force when the pair is symmetric. Consequently, this bounded pair does not by itself close both joint coordinates. A full two-DOF active set requires two independent effective rows `a` and `b` with

```
rank([a;b]) = 2  <=>  det([a;b]) = a_s b_e - a_e b_s != 0.
```

For the present parallel-plane geometry, the second independent row must come from another physical direction or contact feature (for example an in-plane/tangential condition); it cannot be manufactured by renaming `-a` as independent.

The rank-degenerate configurations are therefore:

- **all configurations for the exact opposing parallel-plane pair**, because `-a` is always collinear with `a`;
- **zero-row configurations**, where `a = 0`, so neither plane has first-order joint leverage;
- **near-zero-row configurations**, where `||a||` is small and the normal constraint is ill-conditioned in joint coordinates;
- **two-row degeneracies**, whenever a proposed second row `b` becomes collinear with `a` or either row loses its moment arm.

The pre-study's 20°/20° row was `a = [0.1626940956273763, 0.11994157771166769]` m/rad. Its opposing determinant was at most `8.20e-18` on the 81×81 workspace grid and its rank was one. The smallest normal-row norm on that grid was `0.025266417419960656` m/rad at approximately `(-15.1875°, 20°)`, which is a conditioning boundary, not a second independent grasp row.

For the independent normal/tangent worked basis, take `b = [∂x_x/∂q_s, ∂x_x/∂q_e]`. At 20°/20°:

```
J_(normal,tangent) =
[[0.1626940956, 0.1199415777],
 [0.2467495355, 0.1292879579]] m/rad.
```

The raw determinant is nonzero (`-0.008561...` to `-0.022044...` over the scanned workspace), so this is the valid two-row worked basis used below. The pair's second plane tangential row is anti-parallel to `b`; the pair cone uses the sum of the two normal multipliers.

## 2. Bounded squeeze/closure store

Let the closure coordinate be

```
δ = max(0, 2r - d),
```

and let `F_s >= 0` be the squeeze force magnitude. `δ` is zero at just-touching separation and positive only when the planes close against the proxy. The work done by the squeeze actuator is

```
W_s = ∫ F_s dδ.
```

Introduce the finite store `E_s`, with the same unit as the qualified arm's mechanical store, joules. The store law is one-way:

```
dE_s/dt = -F_s * max(dδ/dt, 0),
0 <= E_s <= E_cap,
```

and opening (`dδ/dt < 0`) returns **no** credit. The grasp contract therefore cannot hide a source of energy in the contact reaction. For a constant force over a closure increment, `ΔE_s = F_s Δδ`; for a compliant force law, the integral is used directly. A simple bounded envelope follows without tuning a force target:

```
F_s(δ) <= E_cap / δ       for δ > 0.
```

A separate actuator force ceiling may only lower this bound. In this pre-study `E_cap` is inherited, not selected: `E_cap = 2.0 J` from `battery_initial_J` in the qualified arm recipe. The work-only envelope is therefore 2000 N at 1 mm closure, 400 N at 5 mm, and 200 N at 10 mm. Those values are an energy envelope, not a claim that the future biological actuator can produce them.

A future implementation must debit the store on positive closure work and leave the debit in the ledger after release. Any path that closes `d` or increases the pair reaction while `E_s` is unchanged fails F1.

## 3. Stick KKT with anti-parallel friction rows

For one effective plane, let `a` be the normal row and `b` the tangent row. For the opposing plane, the corresponding oriented rows are `-a` and `-b`. The pair's net normal and tangential resultants can be represented by effective multipliers `Λ_n` and `F_t`, while the physical per-plane normal multipliers remain nonnegative:

```
Λ_n = λ_n1 + λ_n2,
|F_t| <= μ Λ_n.
```

With the two-coordinate mass matrix `M`, the mass-metric KKT matrix for the independent normal/tangent rows is

```
A = [ a M⁻¹ aᵀ   a M⁻¹ bᵀ ]
    [ b M⁻¹ aᵀ   b M⁻¹ bᵀ ]
  = [ A_nn A_nt ]
    [ A_nt A_tt ].
```

For a sticking target, the multiplier vector solves

```
A [Λ_n, F_t]ᵀ = rhs,
Λ_n >= 0,
|F_t| <= μ Λ_n.
```

The determinant factorizes as

```
det(A) = (a M⁻¹ aᵀ)(b M⁻¹ bᵀ) - (a M⁻¹ bᵀ)².
```

Because `M` is positive definite, this is positive exactly when the rows are independent in the mass metric. The KKT system decouples exactly when

```
A_nt = a M⁻¹ bᵀ = 0;
```

otherwise normal and tangential reactions are coupled even if the geometric rows look orthogonal in Euclidean coordinates. The anti-parallel rows from the second plane do not create a second independent row; they only change the sign convention used to assemble the pair resultant.

At 20°/20°, the selected two-coordinate mass-metric matrix was

```
A = [[8.7250336156, 7.6722443431],
     [7.6722443431, 8.3902272826]].
```

Using the worked acceleration floor `[1.0, 0.5]`, the KKT multipliers were

```
Λ_n(single effective row) = 0.3175433096,
F_t = -0.2307768068.
```

For the symmetric pair, `Λ_n(pair) = 0.6350866191`. With `μ = 0.50`, the cone limit is `0.3175433096`, so the stick example passes the pair cone. The off-diagonal `A_nt = 7.6722443431` is nonzero, so it does not decouple.

**Reading note (what the solved multiplier is, and what it is not).** The single-effective-row KKT solve returns the multiplier of the *net* normal row requirement: in the pair convention the generalized normal force is `aᵀ(λ_n1 - λ_n2)`, so the solved `Λ_n` is a net quantity, not the squeeze. The example's `Λ_n(pair) = 2 Λ_n(solved)` is therefore a **declared illustrative convention** (per-plane load equal to the solved value), used only to demonstrate the cone arithmetic; the receipt records it as `pair_total_normal`. In the contract itself the squeeze load `λ_n1 + λ_n2` is set by the squeeze store of section 2, never by the floor solve. The distinction is load-bearing: under the one-sided reading (`λ_n2 = 0`) the cone limit would be the tighter `μ·0.3175433096 = 0.1587716548`, which the worked `F_t = -0.2307768068` exceeds — that floor would *slide*, and telling those two regimes apart is exactly what the future active set must resolve at runtime.

## 4. Squeeze-catch impact and exact dissipation split

Let the pre-impact joint velocity be `qdot⁻`, with normal and tangent point velocities

```
v_n = a qdot⁻,
 v_t = b qdot⁻.
```

For an uncapped stick catch, solve the joint impulse pair

```
A [P_n, P_t]ᵀ = -[v_n, v_t]ᵀ.
```

This zeroes both effective point components when `A` is nonsingular. For a symmetric two-plane reaction pair, split `P_n` between the planes as `P_n1 + P_n2 = P_n` (equal halves in the symmetric study). The tangential impulses are oriented anti-parallel through the two plane rows, and their combined magnitude is capped by

```
|P_t| <= μ (P_n1 + P_n2).
```

If the uncapped tangential impulse violates the cap, set

```
P_t = clip(P_t*, -μ(P_n1+P_n2), +μ(P_n1+P_n2))
```

and re-solve the normal impulse with the exact cross-coupling:

```
P_n = (-v_n - A_nt P_t) / A_nn.
```

That re-solve is required: applying a normal impulse and then clipping tangential impulse sequentially can reopen the normal gap through `M⁻¹` cross-coupling.

Let `Δqdot = M⁻¹(aᵀP_n + bᵀP_t)` and `v̄ = [v_n, v_t] + 0.5 [a Δqdot, b Δqdot]`. The exact impulse-level energy split is

```
D_n = -P_n v̄_n,
D_t = -P_t v̄_t,
K⁻ - K⁺ = D_n + D_t,
K = 1/2 qdotᵀ M qdot.
```

The catch is admissible only when the split is nonnegative (within numerical tolerance). `D_t` is frictional dissipation; the squeeze-store debit is separate and is not silently folded into impact heat.

The worked capped catch used point velocities `v_n = -0.08 m/s` and `v_t = 0.03 m/s`, with `μ = 0.25`:

```
qdot⁻ = [ 1.6284375694, -2.8758766078 ] rad/s
uncapped [P_n, P_t] = [ 0.06285075377, -0.06104796960 ] N s
pair tangential cap = 0.03142537688 N s
capped [P_n, P_t] = [ 0.03680251380, -0.03142537688 ] N s
```

The normal post-catch point velocity was `-4.12e-17 m/s` (zero to numerical precision); the tangential point velocity remained `0.04869182380 m/s` because the Coulomb cap bound the catch. The energy ledger was

```
K⁻ = 0.003429749695 J
K⁺ = 0.000721189032 J
D_n = 0.001472100552 J
D_t = 0.001236460110 J
D_n + D_t = 0.002708560662 J = K⁻ - K⁺
```

The split closes to below `1e-12 J`. This is the requested exact dissipation accounting for the capped impulse, not a claim of runtime grasp support.

## Pre-study receipt

The reproducible numerical receipt is `tools/science_funnel/validation/grasp_contract_20260918/prestudy.json`, generated by `prestudy.py` using `E:\PythonChimera\.venv-hy3d\Scripts\python.exe`. Its scope is explicitly offline and its inputs are the qualified graph/model. The receipt reports the full squeeze envelope, rank scan, KKT matrix, cone result, catch impulses, and dissipation split.

## Future implementation boundary

The future implementation slice owns the grasp state, squeeze-store debit, pair contact rows, KKT active set, impact catch, cone checks, release/control identity checks, and their tests in the following files:

- `ChimeraEngine/engine/coupled_dynamics.hpp` (future implementation; **not edited by this lane**)
- `ChimeraEngine/engine/tests_coupled_arm/native.cpp` (future falsifier tests)
- `tools/science_funnel/coupled_scene.py` and its qualified receipts (future scene plumbing)
- `tools/science_funnel/tests/` coupled-arm qualification tests (future controls)
- `tools/science_funnel/validation/grasp_contract_20260918/` (this derivation and pre-study only)

Not implemented by this admission:

- no grasp runtime state or engine code;
- no changes to `coupled_dynamics.hpp`;
- no free-root, whole-animal, muscle, distributed-contact, rolling, wrapping, or GPU claim;
- no assertion that two opposing parallel planes immobilize both DOF;
- no implementation-level bit-identity result beyond the prior qualified controls;
- no promotion of the prior friction receipt's queued minor findings to passed behavior.

## Graph admission reference

The Rule-0 record admitted by `admit_work_record.py` is `work.creature.coupled_arm_grasp`, with source `source.operator.coupled_arm_grasp_20260918`. It carries this document, the pre-study receipt, both qualified receipt paths, base commit `4b047609c8f51782da10c9d63726f10ddb525cbc`, the owned future files, and the explicit `not_implemented` list.

Provenance of the base: the lane originally branched from origin/master at `fcaca2a5dd78cc92ea92bbe434050d4f857835ed`; after master moved (draco-decode and trainer-alignment lanes), the branch was rebased with upstream taken for the graph JSONs per the collision rule, and the idempotent admission script re-declared both records against the new base. The falsifiers, statement, and prediction are unchanged by the rebase; the pre-study numbers were re-run and reproduce bit-for-bit on the new base.
