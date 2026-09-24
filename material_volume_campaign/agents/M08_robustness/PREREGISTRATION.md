# M08 PREREGISTRATION — numerical-robustness ladder (frozen before execution)

Written 2026-09-24, BEFORE any fixture is run through the copied modules.
After this file is written, only `fixtures/manifest.json` (mechanical materialization of
the rung parameters below, including exact achieved `delta = |det|/max_edge^3` values) is
generated; then `work/run_ladder.py` runs once. No bound or rung is edited after the first
run. Receipts keep raw outputs.

## 0. Integration model the code actually uses (quoted, not paraphrased)

Both paths integrate **exactly** (piecewise-polynomial moments), never quadrature:

Compiler `work/material_volume.py` `_geometry` (lines 344-384 of the source copy):

```python
e = q[:, 1:, :] - q[:, :1, :]                    # three edges from v0 (float64)
scale = np.maximum.reduce(edge_lengths)          # max of all 6 edge norms
en = e / scale[:, None, None]
det_scaled = np.einsum("ij,ij->i", en[:, 0], np.cross(en[:, 1], en[:, 2]))
...
degenerate = np.abs(det_scaled) <= _DEGENERACY_REL   # 64.0 * EPS
...
volumes = (det_scaled / 6.0) * scale * scale * scale
centroids = q[:, 0] + np.sum(e, axis=1) / 4.0
```

`_mass_properties` (lines 717-754): `m_t = rho_t V_t`, `C = sum(m c)/M`,
`com = origin + sum(m (c-origin))/M` (origin = vertex 0),
`Q_t = (m_t/20) * sum_i (x_i - c_t)(x_i - c_t)^T`,
`I_C = sum_t [ trace(Q_t) I - Q_t + m_t((d.d)I - d d^T) ], d_t = c_t - C`.

Exporter `work/material_volume_body_export.py` `_integrate_cells` (lines 233-278): same
moments, but a **raw determinant** (`np.linalg.det` on the transposed edge matrix, no
scale normalization) and `reference = tets[0, 0]`; `_body_mass_properties` (281-305):
`com_body = R^T (com_domain - origin)`, `I_body = R^T I_domain R`.

Doc corroboration (`Chimera/docs/matter/material_volume_compiler.md`, "Derivation"):
"Uniform volume measure on a 3-simplex has barycentric moments `E[lambda_i]=1/4` and
`E[lambda_i lambda_j]=(1 + delta_ij)/20`" and "Refining a homogeneous tet into a conforming
tet subdivision preserves the integral (up to float64 summation roundoff)."

**Therefore all error is float64 roundoff; the per-rung bounds below are derived from the
rounding behavior of exactly these operations. No statistical or fitted tolerance is used.**

## 1. Declared support (quote table) — the ladder lives inside this support

| # | What | Declared where | Quote | Numeric limit |
|---|------|----------------|-------|---------------|
| D1 | coordinates | compiler doc, input contract | "Finite numeric `nV x 3` array, `nV >= 4`; no coincident distinct node positions and no unused nodes." | any finite float64; NO magnitude range declared |
| D2 | units | compiler doc | "`coordinate_unit` \| Exact string `m`" | meters only; "µm-scale mesh units" = µm-magnitude meter coordinates (in support) |
| D3 | cell shape gate | compiler doc | "positive signed cell orientation (inverted cells are rejected, never flipped) and a scale-normalized nondegeneracy gate `|det| / max_edge^3 > 64 * float64_epsilon`" | `|det|/max_edge^3 > 1.4210854715202004e-14` — the ONLY declared shape limit; NO aspect-ratio max declared, so allowed aspect extends to the gate |
| D4 | orientation | compiler doc | "strictly positive signed determinant `det([v1-v0,v2-v0,v3-v0])`. The compiler never reorders or repairs a cell." | det > 0 |
| D5 | density | compiler doc | "Density must be finite and positive" | any finite positive |
| D6 | scale_to_m | admission doc | "positive finite `scale_to_m`. Every input position is multiplied by this scale to obtain metres." | any positive finite float64; NO range declared |
| D7 | overflow refusal | compiler doc | "arithmetic overflow/nonpositive computed volume is rejected" | named refusal `numeric_overflow` declared |
| D8 | SI identity | admission doc | "SHA-256 digests of sorted records of exact float64 hexadecimal SI-coordinate tetrahedra" | SI floats (`p*scale`) are the identity-bearing geometry — the oracle's obligation |

Anything outside (NaN, inf, det<=0, `|det|/max_edge^3 <= 64eps`, scale_to_m <= 0) is OUT
of scope and not tested except at its exact declared refusal boundary (rungs C7/C8/D5/D6/
A7/E7/E8 probe the declared boundary itself).

## 2. Derivation of the per-rung error bounds

Notation: `u = 2^-53 = 1.1102230246251565e-16` (unit roundoff), `eps = 2u`,
`G = 64*eps = 1.4210854715202004e-14` (D3 gate),
`X` = max |coordinate| of the SI fixture (offset from origin),
`s` = max edge, `D` = body extent (max |c_t - C|), `delta = |det|/max_edge^3` (exact),
`|.|_F` = Frobenius norm.

**(a) Volume/mass.** Edges `e_i = x_i - x_0` are differences of float64 inputs; when the
cell is small relative to its offset (|x_i|, |x_0| within a factor 2) the subtraction is
EXACT (Sterbenz) — no rounding enters the edges at any offset. `scale` carries rel err
<= 2u; `en_i` <= 3u. `det_scaled = en1.(en2 x en3)`: in en-space every term of the cross
and dot products is O(1), so the ABSOLUTE error of det_scaled is <= kappa*u with
kappa <= 12 for our 3-term cancellations — INDEPENDENT of delta. Its RELATIVE error is
therefore <= 6u for delta >> u (well-separated cancellations, e.g. axis-aligned thin/needle
families whose O(1) terms cancel exactly at zero) but up to kappa*u/delta when O(1) terms
with mixed signs sum to delta (the sliver family). Multiplying by `scale^3` adds <= 4u
relative. The exporter's raw `np.linalg.det` path is LU-based and scale-covariant, with
the same relative behavior on the same exact edges.
=> **bound V,M: rel_err <= 20u + 12u/delta.** Offset-independent by design; delta >= 1e-3
for compact rungs => bound ~ 54u; near-gate sliver rungs (delta = 2.5G, 1.2G) => bounds
3.8e-2 and 7.8e-2 — these are the rungs where visible error growth is EXPECTED.
[Correction record, pre-execution: an earlier draft of this line read "20u + 10u*G/delta",
which carries a spurious factor G — the determinant error is absolute (kappa*u), not
relative to G. Caught in derivation self-check BEFORE any fixture was generated or run;
no bound was edited after the first run (none had happened).]

**(b) COM.** `c_t = x_0 + sum(e)/4`: sum(e) has rel err u on O(s); adding x_0 rounds with
abs err <= u*X; the weighted mean adds u*X. Sum of three contributions <= 3u*max(X,s);
margin frozen at:
=> **bound COM: |err|_inf <= 6u * max(X, s, 1)** (meters, absolute).

**(c) Inertia (about body COM).** `local = x_i - c_t` is an exact subtraction carrying
c_t's abs error <= 2u*X => rel err <= 2uX/s => Q_t rel err <= 5uX/s. `d_t = c_t - C` is
exact subtraction carrying <= 6uX abs => parallel-axis term rel err <= 12uX/D. Weighted by
their contributions to I and combined:
=> **bound I: rel_err <= 30u * (1 + X)** (Frobenius-relative), X in meters.
At X=0 the bound is 30u regardless of shape (inertia uses no determinant).

**(d) Gate boundary (D3).** `det_scaled` is evaluated with abs err <= 10u = 1.1e-15 vs a
gate at G = 1.42e-14 (~8% of the gate). Predicted refusals therefore flip only within
~10% of the boundary; rungs are placed at delta >= 2.5G (accept), delta ~ 0.87G and below
(refuse). A refusal at delta in [1.1G, 2.5G] would be a DEFECT candidate (gate evaluated
with more error than derived); acceptance at delta <= 0.5G likewise.

**(e) Offset horizon.** A size-s cell at offset X requires ulp(X) << s. At X = 1e16,
ulp = 2 > s = 1: the intended cell is no longer representable as distinct float64
positions; predicted refusal is `duplicate_vertex_position` (D1). This characterizes the
declared-support conditioning horizon, not a defect.

**(f) scale_to_m mapping (D6/D8).** SI positions `p*scale` are one float multiply.
Power-of-two products are EXACT, so two declarations with bitwise-equal SI products feed
bitwise-identical pipelines => **predicted bitwise-identical reports (equal SHA-256 of
canonical JSON)** for twins E1/E2/E3 and E4a/E4b. Decimal-scale twins (1e6 * 1e-6) differ
by <= 1 ulp per coordinate => property differences <= input-quantization conditioning:
mass/volume rel <= 50u, inertia rel <= 80u.

**(g) Uniform-scale covariance (doc: "V -> s^3 V, m -> s^3 m, I -> s^5 I").** Metamorphic
check across the µm ladder (B): |V(s)/s^3 - V(1)|/V(1) <= 40u; |I(s)/s^5 - I(1)|/I(1)
<= 80u.

**(h) Cross-path consistency (compiler vs exporter raw-det path), same SI geometry:**
both det paths are derived independently => rel diff of V, M <= 40u; of I <= 60u*(1+X).
(Same-formula different-rounding agreement; a violation is a defect candidate in one path.)

**(i) Authored-frame mapping (exporter only).** Rotation is applied post-integration:
|com_body - R^T(c_exact - o)|_inf <= 8u*max(1,|c|); |I_body - R^T I_exact R|_F <= 60u * |I_exact|_F.

**Falsifier (frozen):** any ACCEPTED rung whose measured error exceeds its derived bound,
after checking the oracle and derivation, is a DEFECT candidate and is preserved. Any
refusal whose reason differs from the predicted declared reason is a DEFECT candidate.

## 3. Frozen ladder (all inside declared support D1-D6; refusals only at declared boundaries)

Common geometry: two-cell coupon from the doc's own examples for classes A and E
(`material_volume_body_export_*_example.json` shape); single right tetrahedron for B;
analytic families for C/D. All fixtures emitted in the existing schemas
(`chimera.material_volume.v1` document for the compiler path; `chimera.fitting_manifest.v1`
+ `chimera.material_partition.v1` + `chimera.rigid_body_cell_groups.v1` for the
admission+export path). Densities 12/6 (coupon) or 2/4 (bipyramid-style families), per the
doc examples. Oracle: exact rational (Fraction) evaluation of the same formulas on the
exact float64 SI coordinates — every fixture's `delta`, expected values, and per-rung
bounds are computed by the oracle at fixture-generation time and frozen in
`fixtures/manifest.json` before the run.

- **Class A — offset ladder (cancellation conditioning), coupon at offset X, s ~ 1:**
  X in {0, 1e3, 1e6, 1e9, 1e12, 1e15} accepted-path + X=1e16 predicted
  `duplicate_vertex_position` refusal (horizon, (e)).
  Bounds: V,M <= 20u+10uG/delta (~20u); COM <= 6u*max(X,s,1); I <= 30u(1+X).
  Predicted degradation: V/M flat; COM and I degrade linearly in u*X (X=1e15:
  COM err up to ~0.7 m, I rel err up to ~5e-3 — still within derived bounds).
- **Class B — µm ladder (small cells), right tet at origin scaled by s:**
  s in {1, 1e-2, 1e-4, 1e-6, 1e-8, 1e-10}. Predicted: FLAT error (~20u) at every rung
  (scale-free by design); metamorphic (g) holds. Underflow characterization: none of these
  volumes (< 1.7e-31) is near subnormal.
- **Class C — flat/thin ladder, friendly base (0,0,0),(1,0,0),(0,1,0),(0.5,0.5,h):**
  det = h exactly, scale = sqrt(2), delta = h/2.8284271247461903.
  h in {1, 1e-2, 1e-6, 1e-10, 1e-13, 5e-14} accepted; h in {3e-14, 1e-14} predicted
  `degenerate_tetrahedron` refusal (delta = 0.746G, 0.249G).
  Bounds: V,M per (a) with the rung delta (20u+12u/delta: 54u, 3.8e-13, 3.8e-9, 3.8e-5,
  3.8e-2, 7.5e-2); COM <= 6u*scale; I <= 30u (X=0, det-free). Derivation note (a): this
  friendly family's det has no O(1) cancellation, so measured eV is expected well BELOW
  the bound — the bound is the sliver-class worst case.
- **Class S — near-degenerate-but-allowed sliver (cancellation det), generic base
  (0,0,0),(1,0.3,0.7),(0.5,1,1),(0.9,0.4,eps2):** eps2 bisected so the EXACT delta hits
  {2.5G, 1.2G} (accepted; V-bound 20u+12u/delta => 3.8e-2, 7.8e-2) and {0.87G, 0.5G}
  (predicted `degenerate_tetrahedron` refusal). COM <= 6u*scale; I <= 30u.
  This is the rung family where the kappa*u/delta error growth must actually appear if the
  implementation matches the derivation (expected eV ~ 1e-3..1e-1, still inside bound).
- **Class D — needle ladder, (0,0,0),(1e3,0,0),(500,w,0),(500,0,w):**
  det = 1e3*w^2, scale = 1e3, delta = (w/1e3)^2.
  w in {10, 0.1, 1e-2, 1.5e-4} accepted (delta = 1e-4, 1e-8, 1e-10, 2.25e-14);
  w in {1.1e-4, 1e-4} predicted `degenerate_tetrahedron` refusal (0.851G, 0.704G).
  Bounds per (a) with rung delta (1.3e-11, 1.3e-7, 1.3e-5, 5.9e-2); COM <= 6u*1e3;
  I <= 30u. Like C, the needle's det cancels exactly at zero-term level, so measured eV
  is expected below bound; the sliver class carries the worst case.
- **Class E — scale_to_m extremes (admission+export path, coupon geometry):**
  - E1: P=1, scale=1 (SI reference). E2: P=2^20, scale=2^-20. E3: P=2^-20, scale=2^20.
    E2, E3 are BITWISE twins of E1 (f). E4a: P=2^30, scale=2^30; E4b: P=2^40, scale=2^20
    — both SI = 2^60, bitwise twins of each other (uniform-large, U5).
  - E5: P=1e6, scale=1e-6 (decimal µm declaration; twin of E1 within (f) bounds).
    E6: P=1, scale=1e6 (SI = 1e6; covariance (g) vs E1 within 40u/80u).
  - E7 (collapse): two coupon vertices 1 ulp apart at scale=2^-60 => SI positions collide
    => predicted admission refusal `duplicate_vertex_position`, export blocked.
  - E8 (overflow): scale=1e300 => SI edges ~1e300, scale^3 overflows => predicted
    compiler refusal `numeric_overflow` (D7), export blocked.
  - E1-frame2: identity-scale coupon, authored frame = example's rotated frame
    (origin (3,-2,1)) on body-A => authored-frame mapping check (i).
  Plus class-A export-path subset at X in {0, 1e12, 1e15} for cross-path (h).

Total: 6+1 + 6 + 8 + 4 + 6 + 10 = 41 rungs.

## 4. Classification rule (frozen)

- PASS (conditioning characterized): accepted rung, measured <= bound; or metamorphic/
  twin/cross-path check within its bound.
- REFUSED-BY-CONTRACT: refusal whose reason equals the predicted declared reason
  (D3/D7/D1 quote recorded per rung).
- DEFECT-CANDIDATE: accepted rung with measured > bound, or refusal with any other
  reason, or bitwise twins differing. Each gets a diagnosis section: oracle re-check,
  derivation re-check, and if it survives both, preserved as a defect with receipts.
- Stop rule: ladder complete (all 41 rungs executed once, no re-tuning).
