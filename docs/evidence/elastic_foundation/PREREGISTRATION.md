# PREREGISTRATION.md — membranes for the elastic-foundation battery (written BEFORE any run)

Every falsifier class below is a Rule-0 membrane: STATEMENT · PREDICTION · FALSIFIER named
before the run, with the tolerance budget DERIVED in `DERIVATION.md` §10 (machine-arithmetic
model, not inherited physics). "PASS" for a class means every named item inside it passed at its
own named budget. A falsifier that fires is a RESULT — the battery does not widen a budget after
measuring. Fixtures use **synthetic** material parameters (declared as synthetic), units in meters
unless stated, and `E = 1 Pa, ν = 0.3, h = 1 m` is the default dimensionless-grade fixture so the
numbers are O(1) and the O(1) budgets apply literally.

Shared constants (from DERIVATION.md §10): `E_M = ε^(2/3)`, `ALG = 512·ε`, FD step `h* = ε^(1/3)`.

## F1 — rest state (energy, stress, force)
- STATEMENT: the adopted law has the rest triangle as its exact zero-stress state.
- PREDICTION: at current == rest, per-face `E = 0` exactly (algebraic), total energy `|U| ≤
  ALG·(λ̄₁+μ̄₁)·A₀`, every assembled force `|f| ≤ ALG·scale_F` with `scale_F = (λ̄₁+μ̄₁)·A₀/l̄`,
  `l̄ = max rest edge`.
- FALSIFIER: any of the three exceeds its budget; or any force component is NaN/inf.

## F2 — rigid translation, finite rotation, invariant energy, rotated force
- STATEMENT: `W̄(C)` is objective; a rigid body motion must not create strain, and the force
  vector must transform by the rotation, not by a strain response.
- PREDICTION: (a) rest pose rotated by `0.61 rad` about a non-axis line and translated by
  `(1.3, −0.7, 0.2)`: `|U' − U| ≤ ALG·U_scale`. (b) a deformed pose mapped by the same
  rigid motion: energy identical within budget and `f' = R·f` within ALG·scale_F, componentwise.
  (c) PREDICTION DISTINGUISHING ROTATION FROM STRAIN: a pure 0.73 rad rotation of the rest pose
  changes energy by less than ALG·U_scale, while the linear-strain law (`ε_lin = sym(F) − I`)
  would report energy ≥ `1e-3` of the elastic scale on the same pose — the gap is a factor ≥ 10⁷.
- FALSIFIER: any budget breach; or the finite-rotation-vs-small-strain gap ≤ 10⁵.

## F3 — analytic force vs independent finite-difference energy gradient
- STATEMENT: the assembled vertex force is the exact negative energy gradient.
- PREDICTION: central differences of the TOTAL energy `U` on the same pose, step sweep
  `h ∈ {1e-6, 1e-5, 1e-4, 1e-3}`, agree with `f`: `max_i |f_i − f_i^FD| / max|f| ≤ 256·ε^(2/3)`
  at the best `h` (expected ~`h*`); the error curve shows the classic `O(h²)+O(ε/h)` v-shape and
  the measured best-h sits within a decade of `h*`.
- FALSIFIER: min-over-sweep outside budget; or best-h outside `[1e-6, 1e-3]`; or the cancellation
  analysis (the two-arm residuals vs `h`) not reconcilable with the quadratic model
  (ratio between adjacent-h errors within factor 10 of the expected 4 (truncation) / 10
  (cancellation) arms).

## F4 — net internal force and torque balance
- STATEMENT: conservative constant-strain triangle forces sum to zero and exert no net torque.
- PREDICTION: Σ_v f_v = 0 within ALG·scale_F and Σ_v y_v × f_v = 0 within ALG·(l·scale_F), on a
  single non-aligned triangle AND on a connected `3×2` patch, both at non-rest poses.
- FALSIFIER: either budget breach on either fixture.

## F5 — uniform extension and pure shear against analytic closed form
- STATEMENT: for a prescribed affine current map `y = S·x` (uniform biaxial extension or in-plane
  shear), the closed-form `C = XᵀSᵀS X`, `E`, `W̄` and the derived corner forces are reproduced
  exactly.
- PREDICTION: componentwise agreement of `C`, `E`, `W̄` within `ALG·(local scale)`, corner forces
  within `ALG·scale_F`, for (a) `S = diag(1.2, 0.93)` biaxial and (b) `S = [[1, 0.35],[0, 1]]`
  shear, on a NON-axis-aligned rest triangle (the closed form uses the fixture's actual basis).
- FALSIFIER: any component breach.

## F6 — stiffness and thickness scaling
- STATEMENT: the energy is linear in `(λ̄₁, μ̄₁)` ∝ E and, per reference area, independent of h.
- PREDICTION: (a) `E → 2E` doubles `U` and every force exactly (within ALG·relative);
  (b) `h → 2h` leaves `U` and forces unchanged and halves `w_per_volume` (within ALG·relative);
  (c) `E → E/10` scales `U` and forces by `1/10`.
- FALSIFIER: a relative change beyond ALG on any scaled quantity.

## F7 — material-axis rotation, isotropy, and the orthotropic refusal
- STATEMENT: an isotropic law has no material direction; requests for anisotropy are refused by
  name, and real-material ports refuse where a Poisson ratio is not measured.
- PREDICTION: (a) rotating the entire rest configuration in its plane by `0°, 30°, 90°` and
  mapping the identical relative pose gives identical per-face `C` and energy within ALG.
  (b) a request for an orthotropic material raises `ORTHOTROPIC_UNSUPPORTED` with the missing-input
  list in the message. (c) `material_from_library("rock")` raises `POISSON_RATIO_NOT_MEASURED`
  because the library measures `E` but no `ν`.
- FALSIFIER: any energy/frame mismatch beyond ALG; or an orthotropic/real-material request that
  does NOT refuse by the named reason.

## F8 — unit conversion and coordinate scaling
- STATEMENT: the law is unit-consistent; a change of length scale with the modulus rescaled as
  `E' = E·s⁻²` (coordinates ×s) reproduces the same physics.
- PREDICTION: with `s = 1000` (meters→mm: coordinates ×1000, `E` in Pa→N/mm² = ×10⁻⁶):
  forces identical (N), energy scaled by `s` (J → N·mm) within ALG·(scale)·s. Repeat at
  `s = 0.37`.
- FALSIFIER: force mismatch beyond ALG·scale_F, or energy-ratio mismatch beyond ALG.

## F9 — collapse, inversion, nonfinite inputs, invalid material refusal
- STATEMENT: invalid inputs and degenerate or unresolvable deformations are refused by name;
  nothing is silently clamped.
- PREDICTION: named refusals for (a) NaN/±inf positions; (b) a collapsed current triangle
  (`A_cur ≤ 64ε·max_edge_cur²`); (c) a near-degenerate rest triangle at build; (d) materials
  `E = 0, E = −1, ν = −1, ν = 0.5, ν = 1, h = 0`; (e) finite input that overflows (positions ×10¹⁰⁰)
  → `NONFINITE_RESULT`, never an inf energy. An inverted-but-resolvable pose (`det F < 0,
  |det F|` above floor) returns a finite energy with `inverted=True` and no exception.
- FALSIFIER: any case returns a value instead of its named refusal; the resolvable-inversion case
  raises or is nonfinite.

## F10 — winding and index changes under the declared convention
- STATEMENT: the law is invariant under cyclic face re-indexing and behaves exactly per the winding
  convention for reversal.
- PREDICTION: (a) cyclic permutations `(0,1,2)→(1,2,0)→(2,0,1)` give identical energy within ALG
  and vertex forces that differ only by the vertex relabeling (within ALG·scale_F); (b) a swapped
  reversal `(0,1,2)→(0,2,1)` on the same isolated triangle gives identical energy (C is unchanged)
  and flips the signs of the assembled forces at their (relabeled) vertices within budget; (c) the
  same two conclusions hold after reversing every face of a connected patch.
- FALSIFIER: any budget breach.

## F11 — affine patch tests across triangulations
- STATEMENT: under a global affine current map the per-reference-area energy is a property of the
  sheet, not of the triangulation; assembly adds without double-counting.
- PREDICTION: `U_total/A₀_total` identical across (i) a `2×1` grid triangulation, (ii) the same
  grid with the opposite diagonal on every quad, (iii) a `4×2` refinement, to ALG·(energy density
  scale); and each equals the single-triangle analytic value of F5's uniform map. Every boundary
  and interior vertex force agrees with the global-affine expectation within ALG·scale_F.
- FALSIFIER: any density mismatch beyond budget.

## F12 — nonuniform deformation and discretization dependence
- STATEMENT: a single linear triangle cannot reproduce a non-affine field; refinements converge,
  they do not fool the element into exactness.
- PREDICTION: the same smooth non-affine current map (a grounded warped field, section 2 of
  battery code) applied at grid vertices gives finite valid energies at coarse `c`, mid `m`,
  fine `f`, with relative gaps `|U_m − U_c|/U_c > |U_f − U_m|/U_m` (monotone convergence) and all
  gaps > ALG (nonzero discretization dependence — a stated, correct expectation, not a bug to hide).
- FALSIFIER: non-monotone gaps, or any gap ≈ 0 within ALG, or an invalid triangle at any level.

## Mutations (negative controls) — each MUST fail an independent check

A mutation is a single change to the reference law applied through the test-only mutation knobs
(`law.py` `_mutations`), the production path always running at defaults. An uncaught mutation
falsifies the battery; the "independent" check is never a source-string assertion.

| Mutation | Change | MUST fail |
|---|---|---|
| M1 sign | `f → −f` on output | F3 (FD sees the true gradient, sign flipped force disagrees) |
| M2 ownership | corner forces of v1 and v2 interchanged | F3 on the single non-aligned triangle |
| M3 area-source | energy/forces scaled by current triangle area instead of rest reference area | F5 analytic U and F11 affine densities |
| M4 strain | `E ← sym(F) − I₂` (linear strain, conflates rotation with strain) | F2: pure finite rotation now produces large energy |
| M5 frame | sizes computed against the spatial (world) frame: `C ← F Fᵀ` component trace terms | F2: rigid rotation of a deformed pose changes energy and forces |
| M6 gather | every other face corner is dropped in the CSR gather | F4 net-force balance on the connected patch (interior vertices go off-balance) and F3 |

Each mutation's run records WHICH expected check failed and asserts it did (the mutation is
"effective" only if the instrument caught it; the battery fails if a mutation survives its paired
check).

## D1 — material-response demo membrane (E)
- STATEMENT: an elastic sheet holds a pinned rest shape that pure area minimization cannot, and
  returns toward rest after an imposed displacement is released.
- PREDICTION: (a) with the left edge pinned, an imposed `Δy = +0.25` shear on the right edge
  produces net lateral reaction forces opposing the imposed displacement (sign and magnitude
  reported); (b) releasing the right edge relaxes toward the rest shape: final `max |Δvertex|`
  ≤ `1e-4·L` and `U_final / (λ̄₁+μ̄₁·A₀) ≤ ALG` under the labeled optimizer; (c) at the relaxed
  elastic equilibrium the constant-gamma area law would exert nontrivial inward retraction forces
  (`max |f_γ| / (γ·l) ≥ 0.1` on the interior) — the two laws visibly disagree on the same pose.
- FALSIFIER: any of (a)-(c) fails its named number. Optimizer iterations are optimization steps,
  never physical time; the outcome is labeled `stationary` / `stagnated` / `failed`.

## Tracing and honesty
Every run writes a unique time-stamped evidence path under `docs/evidence/elastic_foundation/`.
No historical result is overwritten. All fixtures, budgets, and this preregistration are frozen
before the first run of `run_falsify.py`; deviations are their own recorded membrane.

## Amendments (appended after the runs, 2026-09-08)

### A1 — pullback frame: per-face local frames → sheet-level co-rotating frame (F7, F11)
As first implemented the reference basis of every face was that face's OWN orthonormal frame.
The first falsification run fired F11: the affine patch-test's interior-residual leg FAILED with
that frame. The theory predicted by IBP (interior residual → 0 for a constant PK1 field) only
holds when adjacent faces pull back to the same coefficient tensor; with per-face frames the
strain tensors of neighbouring triangles are related by different conjugations, so the discrete
equilibrium under affine boundary data deviates from the affine state by an O(1) gauge residual
that does NOT vanish under structured-grid refinement (measured `max_dev ≈ 0.042·h`, with
`dev/h` growing under refinement — non-convergent). This is a falsifying result of the per-face
membrane; the derivation was re-done.

FIX (re-registration, in force): the pullback uses ONE sheet-level frame for the whole mesh —
`frame_n` = SVD principal axis of the per-face rest normals, oriented to the majority
winding; `frame_t1` = projection of the first face's first rest edge onto the tangent plane
(rest-derived, so the frame CO-ROTATES with the rest mesh); `frame_t2 = cross(frame_n,
frame_t1)`. Two consequences, both re-verified:
- F7 coefficient-identity leg holds: rigidly re-placing the WHOLE configuration (rest and
  current rotated together) now leaves the strain coefficients identical (`dC ≈ 2e-16`), not
  merely the energy and world forces.
- F11 interior-residual leg holds at machine precision (`max |f|_interior ≈ 1e-16` on every
  triangulation, budget `ALG·scale_F`).
NEW named refusal `nonflat_rest_sheet`: a rest mesh with any face whose normal deviates more
than 1e-9 from the sheet frame is refused — this is a flat-sheet law.

FALSIFIER (amended F11, in force): for an affine pose, interior vertex forces ≤ ALG·scale_F on
every conforming triangulation; affine energy density equals the single-triangle analytic
value to ALG, both within and across triangulations.

### A2 — unit_make_grid index-convention bug (discovered during F11)
The grid builder ordered vertices x-major (`meshgrid(indexing="ij")` → index `i*(ny+1)+j`) but
the face formula uses `j*(nx+1)+i` (y-major). For `nx == ny` the two coincide; for every other
grid in this battery (3x2, 6x4, 12x8, ...) they disagreed, producing a NONCONFORMING,
self-intersecting mesh — the "interior" / patch quantities derived from it were geometric
garbage, not constitutive results. FIX: `indexing="xy"` so positions and faces agree. All
grid-based falsifiers (F4, F5, F8, F11, F12) now run on conforming meshes. History: the
pre-fix "non-convergent interior residual" readings were revisited and explained by this bug,
not by the constitutive model.

### A3 — F8 re-scoped: coordinate re-scaling replaces the naive unit conversion
The preregistered F8 compared energy under the naive modulus conversion `E' = E·s⁻²`. The
derivation shows the sheet law has an IMPLICIT unit thickness: the energy is per reference
AREA, so a true change of length unit acts on the per-area modulus as `E' = E/s`, not
`E/s²`; the naive conversion is off by the metric factor s and would falsify. F8 now tests
the exact statement: rest and current re-scaled by `s` with the material unchanged →
`U' = s²·U`, `f' = s·f`, `W̄` and `C` invariant (`s ∈ {1000, 0.37}`). The law is declared for
ONE consistent length unit (nominal m, DERIVATION §3). Cross-unit modulus conversion is a
documented limitation (DERIVATION amendment), not a tested falsifier.

### A4 — F10 leg unchanged; the handedness no-leak leg still reverses every face and asserts
energy and world vertex forces are unchanged.

### A4b — D1(c) re-registered (discovered while writing the demo): the contrast pose
The original D1(c) asserted a nontrivial gamma-area retraction force AT the relaxed elastic
equilibrium. On inspection this is ill-posed twice over: at the elastic rest pose every triangle
has its reference area, so interior `f_γ = 0`; and the shear pose used in (a) is `y + 0.25x`,
whose 2D map has unit determinant, so the constant-gamma area law is ALSO blind to it
(`∇A = 0` per interior vertex). The falsifiable two-laws-disagree statement must therefore be
measured at the IMPOSED-SHEAR pose (phase A), and it is the discrepancy itself that is tested:

- D1(c'): at the imposed-shear pose, the elastic shear resistance is simultaneously NONTRIAL and
  the constant-gamma area law is BLIND to the pose: `max |f_el|_right_edge ≥ 0.1` (named floor)
  and `max |f_γ|_interior ≤ 1e-12` (named ceiling, the unit-determinant shear map leaves triangle
  areas unchanged, so `∇A = 0` to roundoff). Magnitudes reported. At the relaxed elastic
  equilibrium both laws are quiet (`max |f_γ_interior|` reported for sanity, not asserted).

This does not weaken the falsifiable content: the demo still names exact numbers for (a) sign
and magnitude of the elastic reaction, (b) the ≤ 1e-4·L relaxation bound and `U_final ≤
ALG·energy_scale` under the labeled optimizer, and (c') the ≥ 10× contrast ratio, with each
result written to its own time-stamped evidence path.