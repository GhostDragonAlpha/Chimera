# B6 PREREGISTRATION — analytic tensor checks (FROZEN before exporter execution)

Agent: B6 — material-volume campaign, worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`).
Stack under check (READ-ONLY): `tools/material_volume_body_export.py` (contract v0.9:
per-body full inertia tensor about COM, all 9 entries, off-diagonals preserved).

## 0. Rule-0 membrane

- **STATEMENT**: the exporter's mass-properties integration is correct mathematics —
  for exact polyhedral fixtures the exported full inertia tensor about the body COM
  must equal the independently derived exact value, be exactly symmetric, and have
  physically valid principal moments.
- **PREDICTION** (not yet measured at freeze time): for the three fixtures below the
  exported tensor equals the exact-fraction prediction entrywise to ≤1e-12 relative,
  symmetry is float-exact (≤1e-15 absolute), eigenvalues are real to ≤1e-12, strictly
  positive, and satisfy the triangle inequalities with the stated strictly positive
  margins.
- **FALSIFIER**: any check on any fixture measuring beyond its frozen bound below.
  A failing falsifier is preserved and classified (self-check first, then exporter
  defect if my derivation verifies). No tolerance is tuned after seeing data.
- **STOP RULE**: all fixtures × check families verdicted (3 bodies × {A, B, C} = 9
  verdict cells, each PASS or FAIL with numbers). No partial stops.

## 1. Frozen fixtures (schema `chimera.material_partition.v1` / `fitting_manifest.v1` / `rigid_body_cell_groups.v1`)

Domain frame `b6-domain` (right-handed, m, `scale_to_m = 1.0`). All coordinates are
integers or dyadic rationals — exact in float64; densities 1000/500/2000 kg/m³ exact.

SHA-256 (frozen):
- `fixtures/manifest.json`  = `0252f68c39f6c762e30a0689a5837f173aec7f14ac6ac3ca75a94c7df6845b3c`
- `fixtures/partition.json` = `286829c1232ba42e8e0d07e06f2ac17ba660f81eed125eb77d24cf302c5a3108`
- `fixtures/groups.json`    = `ad003c97f7c9f40d6be433ef4ac797ebabadb2134f245e0cd73e2ad46a9ccf40`

Fixture QA before freeze: standalone admission = `validation_only_admissible`,
0 reason codes, 3 connected components, total volume 17/6 m³
(`receipts/admission_prevalidation.json`). One earlier fixture draft was refused
(`duplicate_vertex_position`: the unit tetra shared positions with the asym body);
fix = translate unit tetra to x∈[−10,−9], frame origin (−10,0,0). Preserved in this
paragraph, not hidden.

### Fixture 1 — body `b6-body-unit-tetra` (single cell `cell-U1`, identity authored frame, origin (−10,0,0))
Vertices: u0=(−10,0,0), u1=(−9,0,0), u2=(−10,1,0), u3=(−10,0,1) (positive orientation);
ρ = 1000. Fully hand-derived closed form (§3.1).

### Fixture 2 — body `b6-body-asym` (asymmetric multi-cell, identity authored frame, origin (0,0,0))
3 tetrahedra glued face-to-face, mixed densities, genuinely populated off-diagonals:
- `cell-A1` = (r0,r1,r2,r3), r0=(0,0,0), r1=(2,0,0), r2=(0,1,0), r3=(0,0,1), ρ=1000, V=1/3
- `cell-A2` = (r4,r3,r2,r1), r4=(2,1,1), ρ=500, V=2/3 (shares face {r1,r2,r3} with A1)
- `cell-A3` = (r1,r4,r3,r5), r5=(4,1,1), ρ=2000, V=1/3 (shares face {r1,r3,r4} with A2)
Hand derivation §3.2.

### Fixture 3 — body `b6-body-rotated` (same assembly translated +100 in x, authored frame rotated)
Vertices s_i = r_i + (100,0,0), same per-cell densities; authored frame
`domain_from_body.rotation = [[0,1,0],[0,0,1],[1,0,0]]` (cyclic permutation, det=+1,
orthonormal — exact), `origin_m = (100,0,0)`. This exercises the frame transform
`I_body = Rᵀ I_domain R` and `com_body = Rᵀ(com_domain − origin)`.
Hand derivation §3.3.

## 2. Frozen tolerances and falsifier bounds (kg·m² unless stated)

**(a) SYMMETRY** — `max_ij |I_ij − I_ji| ≤ 1e-15` (absolute). Exact bit-equality is
recorded as a receipt but the falsifier bound is 1e-15. (Exporter symmetrizes via
`0.5(I+Iᵀ)` twice; JSON float round-trip is exact, so float-exact symmetry is the
expected outcome, not an assumption.)

**(b) PRINCIPAL MOMENTS** — on the exported 9-entry tensor:
1. realness: general eigensolver (`np.linalg.eigvals`), `max_i |Im λ_i| ≤ 1e-12` (absolute);
2. positivity: `min_i λ_i > 0` (strict);
3. triangle inequalities (cyclically, sorted λ1≤λ2≤λ3): `λ1+λ2−λ3 ≥ −1e-12` (universal
   physical bound, absolute), and — because all three fixtures are non-planar solids —
   additionally `λ1+λ2−λ3 > 0` strictly (fixture-specific bound; equality legal only
   for planar-degenerate bodies, which these are not);
4. `det(I) > 0`; plus consistency vs exact prediction `|det_exp − det_pred| ≤ 1e-12·det_pred`;
5. trace consistency: `|trace_exp − trace_pred| ≤ 1e-12·|trace_pred|` where
   `trace_pred = 2·Σ_i (tr J_i + m_i |d_i|²)` from per-cell data (§3.4);
6. eigenvalue agreement vs prediction (sorted): `|λ_exp − λ_pred| ≤ 1e-9` (absolute);
7. mass `|m_exp − m_pred| ≤ 1e-12·m_pred`; COM `‖com_exp − com_pred‖∞ ≤ 1e-12` m.

**(c) PARALLEL-AXIS RECOMBINATION** — recomputed independently (two float64
implementations owned by B6, not the exporter's code path; per-cell densities from
`cell_provenance`, geometry from partition vertices × scale):
- route C-origin: raw origin second moments `W = Σ m_i E_i[xxᵀ]`,
  `I = (tr W)δ − W − (tr(Mccᵀ))δ + Mccᵀ`, then authored-frame rotation;
- route B-cellwise: `Σ_i [(tr J_i)δ − J_i + m_i(d_i²δ − d_i d_iᵀ)]`, then rotation.
Bound per route and per body: `max_ij |I_recomb_ij − I_exported_ij| ≤ 1e-12 · max_ij |I_ij|`
(relative to tensor max-magnitude). Derivation of the bound: exact polyhedral
covariances (quadrature-verifiable to machine precision), dyadic coordinates, O(10³)
float64 operations ⇒ accumulated round-off ≲ 1e-13 relative; 1e-12 is the frozen
margin.

**Falsifier** = any measurement beyond its frozen bound. **Self-check policy**: on any
failure, first re-verify my derivation (exact-fraction cross-route assertions + the
quadrature cross-check in §3.5, both already on record); only then classify as
exporter-side defect, preserved with full numbers.

## 3. Derivations (hand formulas; exact arithmetic; frozen numbers)

Per-tetrahedron covariance about centroid, two algebraically independent forms:
- Route A (barycentric monomials; E[λᵢ²]=1/10, E[λᵢλⱼ]=1/20):
  `E[xxᵀ] = (1/20)Σ_i pᵢpᵢᵀ + (4/5)ccᵀ`, `Cov = E[xxᵀ] − ccᵀ`;
- Route B (centroid deviations): `Cov = (1/20)Σ_i qᵢqᵢᵀ`, `qᵢ = pᵢ − c`.
`I_cell = (tr J)δ − J`, `J = m·Cov`; body assembly by parallel axis
`I = Σ_i [I_cell,i + m_i(d_i²δ − d_i d_iᵀ)]`, `d_i = c_i − COM`.

### 3.1 Unit right tetra (body 1) — closed form by hand
V = 1/6, m = 500/3, c = (1/4,1/4,1/4). `E[x²]=1/10, E[xy]=1/20` over the standard
simplex ⇒ `Cov = (1/80)(3δ − (11−δ))`, i.e. diag 3/80, off −1/80 ⇒
`I = diag(25/2) + (25/12)(11−δ)`:
`I₁₁ = 25/2 = 12.5`, `I₁₂ = I₁₃ = I₂₃ = 25/12 ≈ 2.0833333333333335`.
Eigenvalues: `125/12, 125/12, 50/3`; margins: 25/6, 125/6, 125/6; det = 390625/216;
trace = 75/2. (These hand values independently match the shipped example report
`material_volume_body_export_example_report.json`: m=2 ⇒ diag 0.15, off 0.025.)

### 3.2 Asymmetric 3-cell body (body 2) — by hand, machine-exact evaluation
Per-cell covariances (exact): T1 `[[3/20,−1/40,−1/40],[−1/40,3/80,−1/80],[−1/40,−1/80,3/80]]`;
T2 `diag(1/5,1/20,1/20)` (all off-diagonals exactly 0); T3
`[[2/5,1/10,0],[1/10,1/20,1/40],[0,1/40,3/80]]`.
COM = (11/8, 7/16, 9/16); M = 4000/3. Exact body tensor (domain frame, identity body
frame = exported frame):
```
I_body = [[ 2275/12,   -525/4,    -675/4  ],
          [ -525/4,    25375/24,  -925/24 ],
          [ -675/4,    -925/24,   24575/24 ]]   (kg·m²)
```
Eigenvalues (float of exact matrix): 136.5956763206627, 1050.8126927400651,
1083.424964272605; margins 103.983…, 169.208…, 1997.642…; det = 4198796875/27 > 0;
trace = 13625/6.

### 3.3 Rotated body (body 3)
`I_body = Rᵀ I R` with the cyclic permutation R ⇒ exact entry permutation:
`diag(24575/24, 2275/12, 25375/24)`, `I₁₂ = I_zx = −675/4`, `I₁₃ = I_zy = −925/24`,
`I₂₃ = I_xy = −525/4`; `com_body = (9/16, 11/8, 7/16)`. Same eigenvalues/det/trace as body 2.

### 3.4 Trace identity (per-cell trace consistency)
`trace(I) = Σ_i [2·tr J_i + 2·m_i|d_i|²]` — for body 2: 2·(75+100+325) + 2·(7625/12)
= 13625/6 ✓ (asserted in exact arithmetic by `work/derive_b6.py`).

### 3.5 Derivation self-checks already on record (pre-execution)
`work/derive_b6.py` (exact `fractions.Fraction` arithmetic, no exporter input):
Route A == Route B exactly per cell; cellwise parallel-axis assembly == origin
second-moment assembly exactly; per-cell diag-sum identity `tr((tr J)δ − J) = 2 tr J`;
body trace identity. PLUS independent numeric Gauss–Legendre quadrature (exact for the
polynomial integrands) of all three asym cells and the assembly:
`receipts/quadrature_crosscheck.txt` — max |quad − exact| = 7.96e-12 abs
(7.5e-15 rel), mass rel err 1.9e-15, COM err 2.9e-15 m, eigenvalues equal to printed
precision. (Honest note: two hand-arithmetic slips in the §3.2 off-diagonals made
during drafting were caught by the exact arithmetic and corrected before freezing;
the frozen values above are the machine-exact evaluation of the hand-derived
formulas, triple-confirmed as described.)

### 3.6 Frozen predictions file
`prereg_predictions.json` sha256 =
`9aa4147c00b2e08d3b43e229ffabae0524524a6a26eed934eeded09247dad64b`.
The exporter has NOT been executed on these fixtures as of this freeze.

## 4. Execution plan (post-freeze)
1. Run `work/material_volume_body_export.py` (module copy; `PYTHONDONTWRITEBYTECODE=1`)
   once on the three fixture inputs → `receipts/export_report.json`.
2. `work/verify_b6.py` applies checks (a), (b), (c) per body against the frozen
   predictions and tolerances → `receipts/check_results.json` + verdict tables.
3. Verdicts: any bound violation = FAIL (falsifier fired); otherwise PASS with margins.
