# DERIVATION.md — the elastic triangle, from the surface-energy milestone to a working constitutive law

Author: BIG PICKLE (BP), `tools/elastic_foundation/`. Inspector commit (this milestone, recorded
before any run): fresh isolated checkout of `GhostDragonAlpha/Chimera` at **`51cd7212`**
(`Keep the camera above the floor`), with `origin/astra/gait-capture` fetched and inspected at
**`cf2a0ae2`** (`Publish BP-A1: G01 nine-finding hardening pass + 25 named regression checks (62/62)`),
merge-base with the workspace HEAD `7cafb332`. All material, engine, shader and contract files are
READ-ONLY for this milestone. Nothing below claims GPU or DYAD results. CPU-only.

---

## 0. What this milestone is, and is not

The current surface law (`Chimera/docs/THE_SURFACE_ENERGY_TRANSLATION.md`, ASTRA 2026-09-06,
implemented by G01/GLM in `Chimera/tools/surface_energy_reference.py`) is **interfacial**, not
constitutive: `U = Σ_t γ_t A_t` with constant gamma minimizes current area. It holds no rest
shape and no in-plane metric — a diagonal stretch `diag(2, 1/2)` preserves area while changing the
sheet's metric by `diag(4, 1/4)` (the translation's own counterexample, prediction 5 there).

This milestone builds the **separate elastic constitutive law** for the same triangle substrate:
a rest shape, resistance to stretching and to shear, and conservative vertex forces. It is a
CPU reference + falsification battery + handoff contract. It does **not** implement rate
dependence, plasticity, fracture, bending, bulk, or contact. It does not claim to be a wooden cup.

**Decision — the constant-gamma law is ABSENT from this law.** They are different terms with
different reference frames (rest metric for elasticity, current area for the interfacial term).
The elastic law is derived and tested with surface energy off; combining them later is an additive
choice `U = U_el + U_surface` (section 9), with no prestress born here because rest energy is zero
by construction.

## 1. Chosen law: isotropic St. Venant–Kirchhoff (STVK) membrane, energy per reference area

Cross section of candidate formulations, all mechanically rotation-objective:

| Candidate | Rotation-objective? | Finite strain? | Compression robustness* | Cost of baseline |
|---|---|---|---|---|
| Linear Hooke `σ = C:ε_lin` | By small-strain fiat only | No | OK | Illegal here: ε_lin conflates finite rotations with strain (falsifier M4) |
| **STVK: `E = ½(C−I)`, `S = λ tr(E)I + 2μ E`** | Exact (C = FᵀF) | Yes | Weak (not polyconvex) | **Chosen** — closed-form forces, a linear stress–strain *in finite strain* in E |
| Compressible Neo-Hookean | Exact | Yes | Better (polyconvex) | Needs a `ln J` term and an implicit plane-stress `λ_3` solve; overkill for the CPU baseline and harder to transcribe |
| Co-rotational linear | Approximate | No | — | Rejects the task's finite-rotation requirement by construction |

*"Compression robustness" = the energy's behavior near `det F → 0⁺`. STVK is **not polyconvex
and not coercive in F** (Pascon 2019, following Holzapfel 2000): its tangent stiffness loses
positive-definiteness under strong compression. For a membrane of moderate strain this is the
standard engineering choice and it is the law this milestone implements, with the weakness named
as a domain boundary (section 6), not hidden. Neo-Hookean is the recorded upgrade path
(`WHAT_COMES_NEXT.md`).

**Primary sources, cited for the specific formulas used:**

1. H. Delingette, *"Triangular Springs for Modeling Non-Linear Membranes,"* IEEE TVCG 14(2), 2008 —
   the STVK *membrane* with plane-stress hypothesis, energy dependent on the metric `C`,
   `E = ½(C − I)`, `S = λ tr(E) I + μ E`, nominal stress `T = F·S`, per-triangle energy
   `W(TP) = A_P · W(G)`, nodal forces `F_i = −A_P · T · D_i` (a linear St. Venant–Kirchhoff
   membrane discretized on linear triangles — the exact element built here).
2. J. P. Pascon, *"Large deformation analysis of plane-stress hyperelastic problems via triangular
   membrane finite elements,"* Asian J. Civ. Eng. 20, 2019 (DOI 10.1007/s40091-019-00234-w) — the
   plane-stress condensation argument (`S_33 = 0` imposed on the 2D law) and the explicit warning
   that linear-elastic and STVK laws fail polyconvexity/coercivity, hence the domain bounds.
3. Yu. Vassilevskii, K. Lukankin, K. Syunyaev, *"Concise Formulas for Strain Analysis of Soft
   Biological Tissues,"* 2015 — the barycentric triangle picture: `F = [d₁ d₂][D₁ D₂]⁻¹`,
   constant on the triangle, `U_P = A_P · ψ(G)`, nodal forces summed over incident triangles.
4. P. S. Valvo, *"Symmetric stiffness matrices for isoparametric finite elements in nonlinear
   elasticity,"* Comput. Mech. 74, 2024 — STVK strain-energy density for the plane triangular
   element in plane stress, and the `ν → ½` incompressible-membrane limit.
5. J. Bonet & R. D. Wood, *Nonlinear Continuum Mechanics for Finite Element Analysis*, 2nd ed.,
   2008 — the `C = FᵀF`/`E`/`S = ∂W/∂E`/`P = F·S` chain used throughout.

## 2. Kinematics and conventions (locked)

- **Rest triangle** `(v0, v1, v2)`: rest positions `x0, x1, x2 ∈ ℝ³`, nondegenerate (section 6).
  Winding convention: the rest normal `n_rest = normalize((x1−x0)×(x2−x0))` is the reference
  orientation; faces are stored as quoted but evaluated exactly as indexed (see F10).
- **Rest tangent basis (per face, the declared geometric frame):**
  `t1 = normalize(x1−x0)`, `n = normalize((x1−x0)×(x2−x0))`, `t2 = cross(t1, n)`,
  basis matrix `X = [t1 t2] ∈ ℝ^{3×2}`.
- **Rest edge-coordinate matrix** `D = Xᵀ[x1−x0, x2−x0] ∈ ℝ^{2×2}` (columns = the two rest edge
  vectors expressed in the rest basis). `B = D⁻¹`. `det D = 2·A₀·(winding sign)`, so invertible
  exactly when the rest triangle is nondegenerate.
- **Current edges** `d1 = y1−y0`, `d2 = y2−y0` (current positions `y`).
- **In-plane deformation gradient** `F = [d1 d2]·B ∈ ℝ^{3×2}` — the position gradient on the rest
  tangent plane. This is **exactly** the object the surface reference exposes as the per-face
  pullback metric `C = JᵀJ` in `triangle_metric` (the same `C` object in the same rest frame), so a
  future combined elastic+surface GPU stage reads one metric. The reference deliberately exposed
  the metric without inventing a modulus; this law supplies the modulus.
- **Right Cauchy–Green**: `C = FᵀF ∈ ℝ^{2×2}`. **Green–Lagrange**: `E = ½(C − I₂)`.
- **Strain invariants** (2D): `I₁ = tr E = ½(tr C − 2)`, `I₂ = tr(E²)`.

Objective by construction: `F` is measured in the material (Lagrangian) frame, so any function of
`C = FᵀF` is invariant under current-configuration rotations and translations. Finite rotations
produce `C = I`, `E = 0`, zero stress — they are never conflated with strain (falsifier F2 + the
linear-strain mutation M4 deliberately fail to respect this).

## 3. Constitutive law, units, and thickness treatment

Energy **per reference area** (the membrane's reference is the 2D manifold; positions in any
consistent length unit, nominal meters):

```
W̄(E) = ½ λ̄₁ (tr E)² + μ̄₁ tr(E²)                 [force/length = Pa·m when lengths in m]
λ̄₁ = E·ν/(1−ν²)      (plane-stress reduced first constant)
μ̄₁ = E/(2(1+ν)) = G                               (shear modulus)
```

- **Per reference area is the primitive**; per reference volume `W̄/h` with thickness `h` is a
  diagnostic only (D unit test F6). This is the 2D plane-stress reduction: the law is written for
  the tangent plane and the through-thickness condition `S₃₃ = 0` is already absorbed in the
  reduced pair, which reproduces the **linear** plane-stress moduli
  `σ₁₁ = E/(1−ν²)(ε₁₁ + ν ε₂₂)`, `σ₂₂ = E/(1−ν²)(ν ε₁₁ + ε₂₂)`, `σ₁₂ = 2G ε₁₂`
  (classical thin-plate plane stress; the pair `(λ̄₁, μ̄₁)` is the standard plane-stress Lamé
  reduction — see Delingette (2008) Eq. 12-16 region and Valvo (2024) Appendix C).
- **Thickness treatment**: `h` is a declared material input used only for `w_per_volume` and the
  scaling law. The 2D law itself is thickness-independent per reference area (a plane-stress sheet
  of double thickness has the same per-area energy, half the per-volume energy). Bending, buckling
  and curved-shell stiffness are **not** implied by the 2D law (a curved assembly of these
  triangles resists only in-plane strain; see section 8 / `WHAT_COMES_NEXT.md`).
- **Per-triangle total energy**: `U_t = A₀_t · W̄_t` (J when positions in m), the `A_P·W(G)`
  integral of Delingette/Vassilevski for a constant `W̄`.

### Parameter admissibility (the pair must make the quadratic form positive-definite)

For the 2D isotropic quadratic on symmetric `E`: positive-definite iff `μ̄₁ > 0` and
`λ̄₁ + μ̄₁ > 0` (the 2D bulk). With `E > 0` this is equivalent to

```
E > 0,   h > 0,   ν ∈ (−1, ½)
```

`ν = ½⁻` is the incompressible-membrane limit (2D bulk → ∞); `ν → −1` is the zero-2D-bulk limit.
Anything outside these intervals is a **named refusal**, never clamped. The material library
(`Chimera/docs/matter/matter_library.json`) measures `E` for some materials but **nothing has a
measured Poisson ratio or a material direction** — so real-material ports `refuse` by name
(reason `POISSON_RATIO_NOT_MEASURED`); every numeric study here uses synthetic parameters declared
as synthetic (F7).

## 4. Stress and analytic vertex forces

`S = ∂W̄/∂E = λ̄₁ tr(E) I₂ + 2 μ̄₁ E` (PK2, in-plane), `P = ∂W̄/∂F = F·S` (nominal/PK1, 3×2).
For a conservative triangle energy `U = A₀·W̄`, the derivative `dW̄ = P : dF` with
`dF = [dy1 dy2]·B` gives, per current coordinate of the two edge vectors,

```
u_j := ∂W̄/∂d_j = P·(Bᵀ e_j)      (column j of P·Bᵀ  -- the shape-function-gradient, D⁻ᵀ e_j)
```

so the three **corner forces** (force ON each vertex = `−∂U/∂y`):

```
f₀ = +A₀·(u₁ + u₂)     f₁ = −A₀·u₁     f₂ = −A₀·u₂
```

These sum to zero per face (translational balance) and, because `W̄` depends only on `C`, generate
zero net torque from a constant strain field (falsifier F4). They coincide with
Delingette's `F_i = −A_P·T·D_i` and Vassilevski's Eq. (4.9) under the constant-strain element
(`D_i` there = the shape-function gradients, whose two-member set is exactly `Bᵀ e₁, Bᵀ e₂`).
The at-rest zero-stress identity and the finite-difference gradient check are falsifiers F1 and F3.

**Assembly**: vertex force = sum of incident corner forces, gathered in the same deterministic
CSR vertex→corner order as the surface reference (`build_vertex_corner_adjacency` order: vertex
ascending, face ascending, slot ascending), so the two laws can share one gather stage on GPU
(section F of `GPU_HANDOFF.md`).

## 5. What resists what (interpretation)

- **Resists stretching** through `tr(E)²` and `tr(E²)` (any `C ≠ I` costs energy; uniform
  extension at `F = a I` has `E₀₀ = ½(a²−1)` raising both).
- **Resists shear** through `tr(E²)` (the off-diagonal `C₁₂` term); the classic cross-metric
  counterexample `diag(2, ½)` costs `W̄ > 0` although `det C = 1` — the property the surface law
  was known to be blind to.
- **Remembers rest shape**: `W̄ = 0 ⟺ C = I₂` for admissible parameters (the quadratic form is
  positive-definite), so the rest triangle is exactly the strain-free state; there is no other zero
  of the energy, and no prestress (section 9).

## 6. Valid deformation domain and collapse/inversion behavior

- **Rest-side**: refusals at build for degenerate rest geometry (repeated vertex, collinear,
  `A₀ ≤ floor`), nonfinite positions, out-of-range indices — mirroring the surface reference's
  rejection names and its degeneracy floor `64·ε·max_edge²` (a geometric near-singularity gate,
  reused by convention from the translation; it gates where `B = D⁻¹` and the basis are trustworthy).
- **Current-side**: `det F = A_cur/A₀` (signed by winding) is reported per face. A current
  triangle with `A_cur ≤ 64·ε·max_edge_cur²` is **refused by name** (`COLLAPSED_TRIANGLE` /
  `NEAR_DEGENERATE`) — the honest result for an inverted-numerically or collapsed element, because
  below that floor the computed measures are not trustworthy. Nonfinite input or arithmetic →
  `NONFINITE_RESULT` refusal (same rule the reference earned; an overflowing magnitude is a
  refusal, never `inf` energy handed out).
- **Inverted but resolvable** (`det F < 0` with `|det F|` above the floor): the law returns a
  finite energy and flags `inverted=True`. Because `C = FᵀF` does not see orientation, a purely
  flipped element has the same in-plane energy as unflipped — correct for a **membrane** (no
  bending stiffness to prefer one side of the sheet), a defect for a **solid** (a wad of these
  triangles can pass through itself; volume/bending handles that, `WHAT_COMES_NEXT.md`).
- **STVK's soft compression**: the 2D law is not coercive as `det F → 0⁺` territory — the tangent
  stiffness can lose definiteness under strong compression (Pascon 2019's warning). The falsifier
  battery therefore does **not** certify the law below `det F` ≈ 0; it certifies: finite bounded
  energy everywhere admitted, exact rest zero, and correct analytic replies on the fixtures.
  Extreme-compression regimes that cannot physically exist for a sheet element are outside the
  declared domain, not patched by a filler.

## 7. Orthotropic extension — derived but REFUSED, not faked

The anisotropic continuation of the same energy in the material frame is (stated for the record —

```
W̄_ortho = ½ a₁₁ (E₁₁²) + a₁₂ E₁₁ E₂₂ + ½ a₂₂ (E₂₂²) + 2 c₆₆ E₁₂²      (in material axes)
```

with `a₁₁ = E₁₁/(1−ν₁₂ν₂₁)`, `a₂₂ = E₂₂/(1−ν₁₂ν₂₁)`, `a₁₂ = ν₁₂ E₂₂/(1−ν₁₂ν₂₁)`,
`c₆₆ = G₁₂`), but **it is not implemented** because the repo provides no defensible parameter set
and no material-direction transport. The named refusal (`reason = ORTHOTROPIC_UNSUPPORTED`) lists
the missing inputs: per-triangle material axes and their transport rule (the geometric
rest basis `(t1, t2)` is a *frame for computation*, not a *material frame*; nothing in the repo
declares fibre directions on a sheet), and the four parameters `E₁₁, E₂₂, ν₁₂, G₁₂` plus (for
solids) a thickness-direction rule. Refusing is cheaper and more honest than inventing a Poisson
ratio or an empirical `E₁₁/E₂₂` relationship, which is what a "defensible parameter set" would
require. The isotropic law is the implemented limit.

## 8. What a surface alone is not (kept out of scope, named)

A sheet of these triangles supplies in-plane elasticity for **one continuous layer**. It does not
supply: bending strength (billows and folds), bulk/Hookean volume behavior of a solid (needs a 3D
element or a 2D⇄3D bookkeeping), fracture (separation criteria, surface creation), or contact
(self/obstacle). A wooden cup needs all three plus a liquid coupling. Section G of
`WHAT_COMES_NEXT.md` lays out the dependency chain; none of it ships here. Most important for the
reader: **plane stress + thickness ≠ wood** — the "cup" claims start where this milestone ends.

## 9. Relation to the constant-gamma surface energy (explicit decision)

- The elastic law's energy has **no** interfacial term. `W̄ = 0` at `C = I`.
- The surface law has no rest shape and no modulus. The two are **additive**
  `U_total = U_el + U_surface` when combined later, each with its own parameters and reference
  (rest to current for elasticity, current area for gamma). Additive is not double-counting: the
  terms measure different physics (deformation vs. interface). The one real coupling to solve
  later is **prestress**: gamma-pulled configurations are no longer strain-free for the elastic
  law (whereas here rest = strain-free by construction), so a combined run's "rest" must be
  measured, not assumed.
- **Testing order honored**: all falsifiers exercise elasticity alone. No test in this milestone
  combines gamma with elasticity. The demo (E) contrasts the two on one fixture to *show* they
  disagree — it does not combine them.

## 10. Numbering and tolerances

Double-precision `ε = 2⁻⁵²`. Two budget classes, both **derived from the standard round-off model
before any run** (not inherited from the surface milestone's physics — only its machine-arithmetic
conventions coincide):

- **Algebraic invariance budget**: `512·ε` × a problem-scaled unit (energy scale, force scale)
  for exact identities (rest zero stress, rotation/translation invariance, net balance). Rationale:
  O(1) inner products in double precision — the same generic bound the reference derives for pure
  arithmetic, valid for any O(1) algebraic identity, engineering-law-independent.
- **Finite-difference budget**: central differences at `h* = ε^(1/3) ≈ 6.055e-6`, truncation
  `O(h²)` balanced against cancellation `O(ε/h)`; normalized-error limit `256·ε^(2/3) ≈ 4.3e-11`
  on O(1) fixtures, with a full `h` sweep and an on-the-record cancellation analysis (F3). This is
  the textbook optimal-step tradeoff, re-derived here, not blindly copied.

---

## 11. Amendment — sheet-level pullback frame (re-derivation, 2026-09-08)

Section 2 as originally written declared the rest tangent basis **per face**: each triangle had
its own `t1 = normalize(x1−x0)`. The falsification battery was run against that frame and **F11
fired**: for an affine pose the interior-residual leg of the affine patch test was NOT zero and —
worse — the deviation of the discrete equilibrium from the affine state did NOT vanish under
structured-grid refinement (`max_dev ≈ 0.042·h` with the ratio `dev/h` growing; non-convergent).

The continuum IBP exactly predicts zero interior residual for a constant PK1 field. The failure
was the frame choice: with per-face frames, adjacent triangles pull `C` back through DIFFERENT
conjugations, so element stresses across a shared edge are incompatible by an O(1) gauge offset
that self-similar meshes replicate at every scale. The energy (a trace-based invariant) is
unaffected — densities matched to `1e-16` even on the failing runs — but the discrete equilibrium
is not the continuum one. This is a falsifying result of the per-face frame membrane, taken
seriously: the frame was re-derived, not the falsifier weakened.

**FIX — one sheet-level frame for the whole mesh** (in force):

- `frame_n` = principal axis of the per-face rest normals (SVD), sign-oriented to the winding
  majority. Sign-robust against mixed-CW/CCW meshes.
- `frame_t1` = the first face's first rest edge `x1−x0` projected onto the tangent plane
  (degenerate-only fallback: the second edge). Because it is rest-DERIVED, the frame
  **co-rotates with the rest mesh**: rigidly re-placing the whole configuration leaves the strain
  coefficients IDENTICAL, not merely the energy and world forces (F7 coefficient leg, `dC ≈ 2e-16`).
- `frame_t2 = cross(frame_n, frame_t1)`. `D` and `B = D⁻¹` are the rest edge-coordinate matrix and
  its inverse **in this sheet frame** (all other formulas in Section 2 unchanged).
- NEW named refusal `nonflat_rest_sheet`: if any rest face's normal deviates more than
  `1e-9` rad from `frame_n`, the rest mesh is REFUSED — this is a flat-sheet law. The sheet frame
  on a flat mesh is the rest tangent plane; `F = [d1 d2]·B` then pulls every face of a uniform
  field back to the SAME coefficient tensor and the affine patch test passes at machine precision
  (`max |f|_interior ≈ 1e-16`, budget `ALG·scale_F`).

Consequences for the falsifier set: F7 (coefficient identity) and F11 (interior patch residual +
affine density exactness) hold as preregistered. Derivation §2's per-face-frame convention is
superseded by §11 for all runs after `run_20260908T224401Z_smoke2`.

## 12. Amendment — unit handling: the law has an implicit unit thickness (F8 re-scope)

Section 3 declares energy **per reference area** in a consistent length unit (nominal m). The
dimension is `force/length`, i.e. a **per-area modulus**. A true change of length unit by factor
`s` acts on a per-area modulus as `E' = E/s`, NOT `E/s²` — the naive length-scaled conversion is
off by the metric factor `s`. Because `h` enters only `w_per_volume`, the 2D law behaves as if
`h ≡ 1` (unit thickness, measured in inverse length units).

Consequence: the preregistered F8 ("rescale E for rescaled fixture") is exactly a unit-conversion
of the modulus and is NOT a well-posed transformation of this law. F8 now tests the 
coordinate re-scaling statement that IS exact: rest and current positions re-scaled by
`s ∈ {1000, 0.37}`, material untouched, one unit system → `U' = s²·U`, `f' = s·f`, `W̄` and `C`
invariant. Cross-unit modulus conversion is a limitation, documented, not tested.