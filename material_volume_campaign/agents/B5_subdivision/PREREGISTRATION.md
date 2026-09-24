# B5 PREREGISTRATION — subdivision coupon (FROZEN before first exporter run)

**Agent:** B5 (`B5_subdivision`) · **Campaign:** mvc-20260924 · **Worktree:**
`E:/ChimeraWork/mvc-20260924` (branch `material-volume-campaign-20260924`, base `3db8bc4e`)
**Frozen:** 2026-09-24, after G1/G2 gates, BEFORE the first exporter invocation (timeline §7).
**Resume note:** this is a retry after a transient provider failure; the only artifact that
survived the failure was `brief.md` (dir otherwise empty on resume). Everything below was
(re)built in this session; the brief itself was intact, so no brief reconstruction was needed.

---

## 1. Theory under test (Rule 0)

**STATEMENT:** One body's material split into more, smaller cells — same region, same
material, same density, explicit schema-legal regrouping (every partition cell proposed to a
single region; one body group owning every cell) — exports the SAME mass, COM, and full
inertia tensor, within float64 rounding of the exact integration model, at every subdivision
depth.

**PREDICTION (not yet measured):** for the fixture family of §4 (levels L0→L3, N = 6, 12, 96,
768 cells), every exported quantity q satisfies |q_measured − q_analytic| ≤ T_q(L) (§3), and
measured errors sit FAR below those worst-case envelopes (expected ~1e-16 relative, i.e. at or
near bit-exact for the dyadic coordinates used), because the exporter integrates exact
polynomial cell moments and only float64 summation can err.

**FALSIFIER (named before the run):** ANY quantity at ANY level with
|measured − analytic| > T_q(L) as frozen in `derivation/derived_expectations.json` (sha256
`58ad1c75…465091`). A falsifier firing is preserved with full numbers and classified
(defect vs characterization) in the report. **Stop rule:** all four levels verdicted.

## 2. Integration model the code actually uses (QUOTED)

The exporter consumes tetrahedral cells and integrates them with EXACT polyhedron moments —
there is NO quadrature. `Chimera/docs/matter/material_volume_compiler.md` §Derivation:

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
> … **Refining a homogeneous tet into a conforming tet subdivision preserves the integral
> (up to float64 summation roundoff).**

The body exporter implements exactly this algebra (`tools/material_volume_body_export.py`,
`_integrate_cells`, lines 233–278 of the frozen copy: `volumes = determinants / 6.0`,
`second_moments = (cell_masses/20.0) * einsum(local, local)`, parallel-axis via
`offsets = centroids - com`, final `np.sum(cell_inertia, axis=0)` and a `0.5*(I+I.T)`
symmetrization), and self-declares `"integration_model":
"piecewise_constant_density_over_owned_tetrahedral_cells"`. M08 already verified both compiler
and exporter integrate exactly (never quadrature). **Consequence (per the brief): this is the
exact-polyhedron branch — tolerance is float-rounding, NOT a quadrature-error law.** Because
in exact arithmetic a conforming subdivision of a region integrates to the SAME numbers,
level-vs-level and level-vs-analytic differences are pure float64 summation/rounding error,
and the frozen bounds below are worst-case envelopes of exactly that.

## 3. Derived error law and frozen bounds

**Per-cell chain (worst case):** 3×3 determinant by LU with partial pivoting
(≤ ~9·eps·cond; the Kuhn edge matrices have cond∞ ≤ 6, L0 anisotropic cond∞ ≤ 12 ⇒ ≤ ~108 ulps,
enveloped by K_TERM = 128), volume (÷6), mass (×ρ), centroid (÷4), central moments
(×1/20, outer products), parallel-axis products — bounded by **K_TERM = 128 ulps per cell
contribution** (u = 2.220446049250313e-16 per ulp).

**Accumulation (worst case, no assumption on numpy's summation order):** summing N cell
contributions sequentially errs ≤ (N−1) ulps of the sum of absolute contributions (holds for
any summation strategy: sequential, pairwise, or unrolled).

**Scale envelopes S_q** (sum of absolute contribution magnitudes, deliberately generous):
- mass: S = M = 192 kg; volume: S = V = 16 m^3.
- COM (per axis): S = box corner-to-corner diagonal √(4²+2²+2²) = √24 ≈ 4.899 m
  (the exporter's `reference`-offset numerator Σm_i·|c_i−ref| ≤ M·√24).
- inertia (each entry, off-diagonals included, since they cancel against ~O(m·ℓ²) terms):
  S = M·(diam(sub-box)² + 4·R²), R = half-diagonal of the coupon = √6 m
  (per-entry contribution ≤ m·trace-envelope + parallel-axis ≤ 2m·R²; the frozen S is ≥2.5×
  that pointwise envelope).

**FROZEN RULE (the only falsifier thresholds):**

> T_q(L) = 4 · (128 + N_L − 1) · 2.220446049250313e-16 · S_q

(GAMMA = 4, fixed safety factor; the raw envelopes already sit at ~1e-13–3e-12 relative, i.e.
the brief's "~1e-12 relative" float-rounding regime — the frozen T keeps every level's
threshold in that same regime. All values frozen in `derivation/derived_expectations.json`.)

| level | N (tets) | T_mass (kg) | T_vol (m³) | T_COM (m) | T_inertia (kg·m²) | T_inertia / I_max |
|---|---|---|---|---|---|---|
| L0 | 6 | 2.268e-11 | 1.891e-12 | 5.787e-13 | 1.089e-09 | 3.40e-12 |
| L1 | 12 | 2.370e-11 | 1.975e-12 | 6.048e-13 | 8.533e-10 | 2.67e-12 |
| L2 | 96 | 3.803e-11 | 3.169e-12 | 9.703e-13 | 1.027e-09 | 3.21e-12 |
| L3 | 768 | 1.526e-10 | 1.272e-11 | 3.894e-12 | 3.777e-09 | 1.18e-11 |

**Verdict rules (frozen):**
- V1 (level-vs-analytic, primary): each exported quantity vs the analytic box values (§4),
  per level, vs its T. Falsifier = any violation.
- V2 (level-vs-level): |q_L − q_L′| ≤ T_q(L) + T_q(L′) for all level pairs (same rule,
  triangle inequality); verdicted per quantity pair.
- V3 (growth characterization, non-falsifying): measured max error vs N is tabulated against
  the envelope; error hugging the envelope's growth = characterized conditioning; error
  EXCEEDING T = falsifier → defect-class finding.
- I1 (informational, non-falsifying): identity authored frame ⇒ transform is provably exact
  (R = I, origin = 0: every product/sum is exact), so exported body-frame values must equal
  the domain values bit-for-bit. A mismatch would be reported as an anomaly finding.
- Schema/admission gates: `export_status == "complete"`,
  `admission_status == "validation_only_admissible"`, `all_supplied_cells_assigned == true`
  for every level; refusal/blocked statuses are immediate findings.

## 4. Fixture family (frozen) and analytic expectations

ONE body (`subdiv-body`), ONE region/owner (`subdiv-region`/`subdiv-owner`), ONE material
(`tissue-uniform`, ρ = 12.0 kg/m³, source "B5 subdivision coupon fixture", conditions
"uniform"), authored frame identity (R = I, origin = 0). Coupon region: box
[0,4]×[0,2]×[0,2] m, tetrahedralized by the Kuhn (Freudenthal) triangulation (6 tets per
sub-box, main diagonal min-corner→max-corner; conforming across the grid). All coordinates
dyadic (exact in float64). Levels (the brief's "one box → 2×1×1 → 4×2×2", plus one deeper
level for the growth characterization):

| level | sub-box grid | sub-box edges (m) | tets N | vertices |
|---|---|---|---|---|
| L0 | 1×1×1 | 4×2×2 | 6 | 8 |
| L1 | 2×1×1 | 2×2×2 | 12 | 12 |
| L2 | 4×2×2 | 1×1×1 | 96 | 45 |
| L3 | 8×4×4 | 0.5×0.5×0.5 | 768 | 225 |

**Analytic expectations (exact, box formulas — independent of any tessellation):**
volume = 16 m³; mass = ρ·V = 192.0 kg; COM = (2.0, 1.0, 1.0) m;
I about COM (domain axes = body axes): Ixx = 128.0, Iyy = Izz = 320.0 kg·m²,
Ixy = Ixz = Iyz = 0.0 (symmetry).

**G1 (pre-freeze, PASSED):** the independent exact rational oracle
(`derivation/derive_oracle.py`, pure stdlib, imports nothing from tools/) integrates each
level's ACTUAL fixture cells with Fraction simplex moments and asserts EXACT equality with
the box formulas above — all four levels exact (volume, mass, COM, all six inertia entries).
The subdivision tessellations provably cover the identical region.

**G2 (pre-freeze, PASSED):** all 12 fixture documents validate against the SHIPPED schemas
(`tools/material_volume_admission_schema.json`, `tools/material_volume_body_export_schema.json`;
`receipts/validate_fixture.txt`, 12/12 PASS).

## 5. Execution protocol (frozen)

- tools/ and docs/ READ-ONLY; exporter + admission + compiler run from byte-identical copies
  in `work/` (sha256 §7), `PYTHONDONTWRITEBYTECODE=1`, CPU-only, no git writes.
- One exporter run per level: `python work/material_volume_body_export.py --manifest
  fixtures/l{k}_manifest.json --partition fixtures/l{k}_partition.json --groups
  fixtures/l{k}_groups.json`, stdout saved verbatim to `receipts/run_l{k}_report.json`.
- Verdicts computed by `work/verdict.py` reading ONLY the frozen expectations file and the
  saved receipts. No tolerance is chosen after seeing data.

## 6. Pre-freeze gate status (at freeze time)

- G1 exact rational oracle: 4/4 levels ALL EXACT (log: `derivation/derivation_log.txt`).
  (Oracle-side bug history, preserved: the first G1 run FAILED on all levels — the parallel-axis
  term in the ORACLE had a sign error (+m·d_a·d_b instead of m·(|d|²δ−d_a·d_b)); fixed in the
  oracle only; fixtures and their generator were untouched by that failure except the
  generator's own face-orientation assertion, which initially tested same- instead of
  opposite-orientation. No exporter code was consulted for either fix.)
- G2 shipped-schema validation: 12/12 PASS.
- G3 module copies byte-identical to READ-ONLY originals: 3/3 sha256 equal.

## 7. Frozen artifact hashes and freeze timeline

**sha256 (verbatim from `receipts/prereg_hashes.tmp`):**

```
fa1578d63cd006a8b6ff05a9df2c5cd195642b2e10055eef9944e8d6d7a82afa  fixtures/l0_groups.json
6534021e59e152080cd40917e517807ba916431217c15bb8ffd2b97e69b0d555  fixtures/l0_manifest.json
603e3654208ad44e2d42d3380ed9199515a6b1f6802d542f925a4be67aa95364  fixtures/l0_partition.json
6b89959a2e77093e46fd246ede51e29dec97a23d378eba69d33f8aee23e665e9  fixtures/l1_groups.json
d671dfc61e0d159233b9c7c27bcdefb0d3ad1f6cc671ec7d3d83cf6462c99f45  fixtures/l1_manifest.json
fc89039f7708b150fae4bfcf284ef80f17bb5d271ad1273911e24d7e534bde31  fixtures/l1_partition.json
93d498572cd3209cd32f33152abbebf75551a744132d5d24430064f0e88ee814  fixtures/l2_groups.json
6a363fde1a646a22b44273f3ac94d209dadb0daaf6e76bb11bcd84ebd311ca61  fixtures/l2_manifest.json
a0a9efec16a0bd4f1fe1c07a6b33e58c01b1e4e5a6cd23e573c82c38a371db1d  fixtures/l2_partition.json
cf8dfe88e8a8fde1b6303a9a68f640036e9c7610b6538033c827a7ce50c40c88  fixtures/l3_groups.json
9645fa817e3d9fe2d3a4d030f0dbaf08a46c8b2b2eb4060c6c097c32e45d9204  fixtures/l3_manifest.json
0d266e9930f7fd1a0da9a677fb35ad0ce4a802458087ea367b9c259c68e9884d  fixtures/l3_partition.json
58ad1c75ffcf79fd9c83162d4e24d627e5a7d58cabb40c49e476d696a2465091  derivation/derived_expectations.json
959d26c42da7d501f4527e286cb5d9470fcd369643e76973076f6c601db71750  derivation/derivation_log.txt
6d2817b7b4ea59213f90134b343a06579d92db998c1db7f27b0e89aff71799cf  work/material_volume.py
d6d4b0e010c0982f5c94dc880a2fec4ac50ea69af605ce80b7186745a5f7750d  work/material_volume_admission.py
04be88a7c62dc358c06aff29d3ac70244ae575298603712d2352d44853e018e7  work/material_volume_body_export.py
```

(Originals, for the G3 record: `tools/material_volume.py` = `6d2817b7…`,
`tools/material_volume_admission.py` = `d6d4b0e0…`, `tools/material_volume_body_export.py` =
`04be88a7…` — identical to the copies.)

**Timeline (filesystem mtimes, local):**

| step | artifact | time |
|---|---|---|
| fixtures written | `fixtures/l0_*…l3_*` | 14:51:55.992 – 14:51:56.042 |
| G1 oracle + derived bounds | `derivation/derived_expectations.json` | 14:54:07.071 |
| G2 schema gate | `receipts/validate_fixture.txt` | 14:54:32.422 |
| **PREREG FROZEN** | `PREREGISTRATION.md` (this file) | — |
| FIRST exporter contact | `receipts/run_l0_report.json` | AFTER freeze (§receipts timeline) |

The falsifier thresholds, family, and verdict rules above are frozen by this document; the
exporter had made NO contact with any fixture before this freeze.
