# B5 — SUBDIVISION COUPON: report

**Agent:** B5 (`B5_subdivision`) · **Date:** 2026-09-24 · **Worktree:** `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`, base `3db8bc4e`; observed HEAD during session:
`024754f4` → `34f9af52`, shared worktree, no git writes by B5)

**VERDICT: PASS — conservation through subdivision PROVEN within the frozen float64 bounds.
44/44 level×quantity checks PASS, 60/60 level-vs-level checks PASS, 0 falsifiers fired. Worst
measured deviation 1.76e-12 kg·m² (~60 ulps of the quantity scale, ≥106× inside its frozen
bound). Classification: CHARACTERIZED CONDITIONING, zero exporter defects.**

**Resume note (transient provider failure):** the only artifact that survived was `brief.md`
(intact, followed exactly); the dir was otherwise empty, so fixtures/derivation/receipts were
(re)built this session. No brief reconstruction was required.

---

## 1. Question and family

The brief's property: **SUBDIVISION INVARIANCE** — one body's material split into more,
smaller cells (same region, same material, same density, explicit schema-legal regrouping)
must export the SAME mass, COM, and full inertia tensor. M02 proved multi-cell exactness at
fixed granularity; this coupon varies GRANULARITY itself: the identical box
[0,4]×[0,2]×[0,2] m, one region/owner, one material (ρ = 12.0 kg/m³), identity authored
frame, tetrahedralized by conforming Kuhn triangulation at four depths:

| level | grid (brief: 1 → 2×1×1 → 4×2×2) | sub-box edges | tets N | vertices |
|---|---|---|---|---|
| L0 | 1×1×1 | 4×2×2 | 6 | 8 |
| L1 | 2×1×1 | 2×2×2 | 12 | 12 |
| L2 | 4×2×2 | 1×1×1 | 96 | 45 |
| L3 | 8×4×4 | 0.5×0.5×0.5 | 768 | 225 |

Fixtures: `fixtures/l{0..3}_{manifest,partition,groups}.json` — all 12 validated against the
SHIPPED schemas before the freeze (`receipts/validate_fixture.txt`, 12/12 PASS). Every
partition cell carries `proposals: ["subdiv-region"]`; one body group owns every cell id;
the manifest and partition correspond exactly (same vertices/cells/regions/frame/authority).

## 2. Integration model the compiler actually uses (quoted; acceptance 1)

Exact polyhedron integration — no quadrature. `Chimera/docs/matter/material_volume_compiler.md`,
§Derivation, verbatim:

> For positively oriented tet vertices `x_i` (`i=0..3`),
> ```text
> V_t = det([x_1-x_0, x_2-x_0, x_3-x_0]) / 6
> m_t = rho_t V_t
> c_t = sum_i x_i / 4
> ```
> Uniform volume measure on a 3-simplex has barycentric moments `E[lambda_i]=1/4` and
> `E[lambda_i lambda_j]=(1 + delta_ij)/20`. Thus the central second-moment matrix and inertia
> tensor of one tet are
> ```text
> Q_t(c_t) = integral rho (x-c_t)(x-c_t)^T dV
>           = (m_t/20) sum_i (x_i-c_t)(x_i-c_t)^T
> I_t(c_t) = trace(Q_t) identity - Q_t
> ```
> For all resolved cells, `M = sum m_t`, `C = sum(m_t c_t)/M`, and the inertia about the total
> COM uses the parallel-axis identity
> ```text
> I_C = sum_t [ I_t(c_t) + m_t ( (d_t·d_t) identity - d_t d_t^T ) ],
>  d_t = c_t - C.
> ```
> … Refining a homogeneous tet into a conforming tet subdivision preserves the integral
> (up to float64 summation roundoff).

The exporter implements exactly this (`tools/material_volume_body_export.py::_
integrate_cells`, frozen copy sha256 `04be88a7…`) and self-declares `"integration_model":
"piecewise_constant_density_over_owned_tetrahedral_cells"`. **Branch of the brief's law
selection: exact polyhedron formulas ⇒ tolerance is float-rounding (~1e-12 relative); the
quadrature error law does not apply, because the integral is additive over the region and a
conforming subdivision preserves it exactly in real arithmetic.** The only error channel is
float64 rounding, so the derived bounds below are worst-case rounding envelopes.

### Derived per-level frozen bounds

Worst-case chain: per-cell contribution ≤ K_TERM = 128 ulps (3×3 LU det with cond∞ ≤ 6 —
≤12 for the L0 anisotropic box — enveloped at 108, plus ÷6, ×ρ, ×1/20, parallel-axis
products); accumulation over N cells ≤ (N−1) ulps of the sum of |contributions| (order-free
bound); u = 2.220446049250313e-16. Scales S_q: mass 192 kg, volume 16 m³, COM √24 ≈ 4.899 m
(corner-diagonal envelope of the exporter's reference-offset numerator), inertia per entry
M·(diam(sub-box)² + 4R²) with R = √6 m (half-diagonal; off-diagonal entries cancel against
O(m·ℓ²) terms, so their bound uses the same absolute scale). **Frozen rule:
T_q(L) = 4·(128 + N_L − 1)·u·S_q** — full derivation, constants, and rationale in
`PREREGISTRATION.md` (§3), values frozen in `derivation/derived_expectations.json`
(sha256 `58ad1c75…`):

| level | N | T_mass (kg) | T_vol (m³) | T_COM (m) | T_inertia (kg·m²) | T_I / I_max |
|---|---|---|---|---|---|---|
| L0 | 6 | 2.268e-11 | 1.891e-12 | 5.787e-13 | 1.089e-09 | 3.4e-12 |
| L1 | 12 | 2.370e-11 | 1.975e-12 | 6.048e-13 | 8.533e-10 | 2.7e-12 |
| L2 | 96 | 3.803e-11 | 3.169e-12 | 9.703e-13 | 1.027e-09 | 3.2e-12 |
| L3 | 768 | 1.526e-10 | 1.272e-11 | 3.894e-12 | 3.777e-09 | 1.2e-11 |

Every frozen threshold sits in the brief's "~1e-12 relative" float-rounding regime
(1.2e-13 – 1.2e-11 of the quantity scale).

**Pre-freeze analytic gate (G1):** the independent pure-stdlib exact rational oracle
(`derivation/derive_oracle.py`, Fraction simplex moments, imports nothing from tools/)
integrates each level's ACTUAL fixture cells and asserts exact equality with the closed-form
box values — volume 16 m³, mass 192 kg, COM (2,1,1) m, Ixx 128, Iyy = Izz 320, off-diagonals
0 — **all four levels ALL EXACT** (`derivation/derivation_log.txt`). The tessellations
provably cover the identical region before any exporter contact.

## 3. Execution receipts (acceptance 2)

Freeze discipline (filesystem mtimes, local): fixtures written 14:51:55.992–56.042 → G1
oracle+bounds 14:54:07.071 → G2 schema gate 14:54:32.422 → **PREREGISTRATION FROZEN
14:57:04.961** → first exporter contact **14:57:28.972**. The exporter never saw a fixture
before the freeze.

| run | receipt | mtime | exit | export_status | cells |
|---|---|---|---|---|---|
| L0 | `receipts/run_l0_report.json` | 14:57:28.972 | 0 | complete | 6 |
| L1 | `receipts/run_l1_report.json` | 14:57:29.404 | 0 | complete | 12 |
| L2 | `receipts/run_l2_report.json` | 14:57:31.189 | 0 | complete | 96 |
| L3 | `receipts/run_l3_report.json` | 14:57:51.208 | 0 | complete | 768 |

All runs: `export_status=complete`, `admission_status=validation_only_admissible`,
`all_supplied_cells_assigned=true` (the admission re-validated the full conforming complex —
manifold boundary, vertex links, pairwise SAT non-overlap — at every depth, including L3's
768 cells). Module copies byte-identical to the READ-ONLY originals (sha256 3/3 equal,
`receipts/prereg_hashes.tmp`); `PYTHONDONTWRITEBYTECODE=1`; CPU-only; no git writes.
Verdict pass: `receipts/verdict_log.txt`, machine-readable `receipts/verdicts.json`.

## 4. Level × quantity verdict tables (acceptance 3)

Analytic expectations (exact box formulas, independent of tessellation): mass = 192 kg,
volume = 16 m³, COM = (2,1,1) m, Ixx = 128, Iyy = Izz = 320, Ixy = Ixz = Iyz = 0.
d/T = measured deviation ÷ frozen bound (falsifier fires at d/T > 1).

**L0 (N=6) — 11/11 PASS**

| quantity | measured | analytic | \|Δ\| | frozen T | d/T | verdict |
|---|---|---|---|---|---|---|
| mass | 192.0 | 192 | 0.000e+00 | 2.268e-11 | 0.0e+00 | PASS |
| volume | 15.999999999999998 | 16 | 1.776e-15 | 1.891e-12 | 9.4e-04 | PASS |
| com[0..2] | 2, 1, 1 | 2, 1, 1 | 0 (all) | 5.787e-13 | 0.0e+00 | PASS ×3 |
| Ixx | 128.0 | 128 | 0.000e+00 | 1.089e-09 | 0.0e+00 | PASS |
| Iyy | 320.0 | 320 | 0.000e+00 | 1.089e-09 | 0.0e+00 | PASS |
| Izz | 320.0 | 320 | 0.000e+00 | 1.089e-09 | 0.0e+00 | PASS |
| Ixy, Ixz, Iyz | 0.0 (all) | 0 | 0 (all) | 1.089e-09 | 0.0e+00 | PASS ×3 |

**L1 (N=12) — 11/11 PASS**

| quantity | measured | \|Δ\| | frozen T | d/T | verdict |
|---|---|---|---|---|---|
| mass | 191.99999999999997 | 2.842e-14 | 2.370e-11 | 1.2e-03 | PASS |
| volume | 15.999999999999993 | 7.105e-15 | 1.975e-12 | 3.6e-03 | PASS |
| com[0..2] | 2, 1, 1 | 0 (all) | 6.048e-13 | 0.0e+00 | PASS ×3 |
| Ixx | 127.99999999999996 | 4.263e-14 | 8.533e-10 | 5.0e-05 | PASS |
| Iyy | 319.99999999999994 | 5.684e-14 | 8.533e-10 | 6.7e-05 | PASS |
| Izz | 320.0 | 0.000e+00 | 8.533e-10 | 0.0e+00 | PASS |
| Ixy | −3.553e-15 | 3.553e-15 | 8.533e-10 | 4.2e-06 | PASS |
| Ixz | −1.776e-15 | 1.776e-15 | 8.533e-10 | 2.1e-06 | PASS |
| Iyz | 0.0 | 0.000e+00 | 8.533e-10 | 0.0e+00 | PASS |

**L2 (N=96) — 11/11 PASS**

| quantity | measured | \|Δ\| | frozen T | d/T | verdict |
|---|---|---|---|---|---|
| mass | 192.0 | 0.000e+00 | 3.803e-11 | 0.0e+00 | PASS |
| volume | 16.0 | 0.000e+00 | 3.169e-12 | 0.0e+00 | PASS |
| com[0..2] | 2, 1, 1 | 0 (all) | 9.703e-13 | 0.0e+00 | PASS ×3 |
| Ixx | 127.99999999999994 | 5.684e-14 | 1.027e-09 | 5.5e-05 | PASS |
| Iyy | 320.00000000000051 | 5.116e-13 | 1.027e-09 | 5.0e-04 | PASS |
| Izz | 320.00000000000051 | 5.116e-13 | 1.027e-09 | 5.0e-04 | PASS |
| Ixy | −8.882e-15 | 8.882e-15 | 1.027e-09 | 8.7e-06 | PASS |
| Ixz | +2.220e-15 | 2.220e-15 | 1.027e-09 | 2.2e-06 | PASS |
| Iyz | +3.442e-15 | 3.442e-15 | 1.027e-09 | 3.4e-06 | PASS |

**L3 (N=768) — 11/11 PASS**

| quantity | measured | \|Δ\| | frozen T | d/T | verdict |
|---|---|---|---|---|---|
| mass | 192.00000000000003 | 2.842e-14 | 1.526e-10 | 1.9e-04 | PASS |
| volume | 16.000000000000004 | 3.553e-15 | 1.272e-11 | 2.8e-04 | PASS |
| com[0..2] | 2, 1, 1 | 0 (all) | 3.894e-12 | 0.0e+00 | PASS ×3 |
| Ixx | 128.00000000000171 | 1.705e-12 | 3.777e-09 | 4.5e-04 | PASS |
| Iyy | 319.99999999999915 | 8.527e-13 | 3.777e-09 | 2.3e-04 | PASS |
| Izz | 319.99999999999909 | 9.095e-13 | 3.777e-09 | 2.4e-04 | PASS |
| Ixy | −5.063e-14 | 5.063e-14 | 3.777e-09 | 1.3e-05 | PASS |
| Ixz | +9.881e-15 | 9.881e-15 | 3.777e-09 | 2.6e-06 | PASS |
| Iyz | +3.691e-15 | 3.691e-15 | 3.777e-09 | 9.8e-07 | PASS |

**Level-vs-level (V2 rule |q_L − q_L′| ≤ T_L + T_L′) — 60/60 PASS:** worst per pair —
l0–l1 mass 2.842e-14 vs 4.638e-11; l0–l2 Iyy 5.116e-13 vs 2.115e-09; l0–l3 Ixx 1.705e-12 vs
4.866e-09; l1–l2 mass 2.842e-14 vs 6.173e-11; l1–l3 Ixx 1.748e-12 vs 4.631e-09; l2–l3 Ixx
1.762e-12 vs 4.804e-09. Zero violations.

**Informational I1:** with the identity authored frame the transform chain (R = I, origin 0)
is provably exact; no anomaly observed — all exported body-frame values land at or within a
few ulps of the exact rationals.

## 5. Conditioning vs defect (acceptance 4)

**Classification: CHARACTERIZED CONDITIONING. No defect.**

- The law this branch predicts: subdivision preserves the integral EXACTLY in real
  arithmetic; residual error is pure float64 summation rounding, worst-case enveloped by
  T_q(L) = 4·(128+N−1)·u·S_q. **Measured behavior matches the law: every deviation is a few
  to ~60 ulps of its own quantity's scale** — worst mass error = 1 ulp of 192 kg (2.842e-14);
  worst volume error = 4 ulps of 16 m³ (7.1e-15); COM bit-exact (0.0) at ALL depths and all
  three axes (the exporter's reference-offset COM formulation + dyadic coordinates); worst
  tensor entry 1.705e-12 kg·m² ≈ 60 ulps of 128 (L3 Ixx); off-diagonals ≤ 5.06e-14 kg·m².
- **Growth (V3):** worst |Δ| per level 1.8e-15 → 7.1e-15 → 5.1e-13 → 1.7e-12 as N goes
  6 → 12 → 96 → 768. Absolute error grows with depth but ALWAYS as rounding-scale noise: the
  fraction d/T of the worst-case envelope stays flat at 5e-4…9e-3 (≥106× margin) across a
  128× increase in cell count — there is no divergence against the derived law, so the
  defect-class branch of the brief (subdivision error growing against the law) does NOT fire.
- Deviations are unsigned noise in mixed-sign accumulations (off-diagonal cancellations),
  exactly the channel the envelope was derived for. Mass — an all-positive sum — is
  bit-exact or 1 ulp even at N = 768.
- Consistency with prior lanes: M02 (multi-cell exactness at fixed granularity, 142/142
  exact-Fraction) and M08 (exact integration, conditioning separated from defects, zero
  implementation defects) — B5 extends both conclusions THROUGH subdivision depth.

**Preserved harness findings (not exporter defects, kept per preserve-failures law):**
(1) first G1 run FAILED all levels — the ORACLE's parallel-axis term had a sign error
(+m·d_a·d_b for m·(|d|²δ−d_a·d_b)); fixed in the oracle only, fixtures untouched.
(2) the fixture generator's face-orientation assertion initially tested same- instead of
opposite-orientation and stopped the build; the generated complexes were already conforming.
No tools/ or docs/ code was consulted or changed for either.

## 6. Integrity paste (acceptance 5)

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty — no output)
```

READ-ONLY stack untouched: exporter/admission/compiler copies in `work/` sha256-identical to
`tools/` originals (`04be88a7…`, `d6d4b0e0…`, `6d2817b7…`); all B5 writes confined to
`material_volume_campaign/agents/B5_subdivision/`.

## 7. Artifact index

- Frozen prereg: `PREREGISTRATION.md` (theory, quoted model, derived law, hashes, timeline)
- Fixtures: `fixtures/l{0..3}_{manifest,partition,groups}.json` (schema-valid, 12/12)
- Exact oracle + frozen bounds: `derivation/derive_oracle.py`,
  `derivation/derived_expectations.json`, `derivation/derivation_log.txt`
- Fixture generator: `work/gen_fixtures.py` (+ `work/gen_fixtures_log.txt`),
  schema gate `work/validate_fixture.py`, verdict pass `work/verdict.py`
- Receipts: `receipts/run_l{0..3}_report.json`, `receipts/verdicts.json`,
  `receipts/verdict_log.txt`, `receipts/validate_fixture.txt`, `receipts/timeline.txt`,
  `receipts/prereg_hashes.tmp`
- Module copies: `work/material_volume{,_admission,_body_export}.py` (sha256-verified)

**Stop rule status: all four levels verdicted. FALSIFIER: never fired. DONE.**
