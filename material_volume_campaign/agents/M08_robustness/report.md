# M08 REPORT — numerical robustness of the material-volume exporter

**Campaign:** mvc-20260924 (worktree `E:/ChimeraWork/mvc-20260924`, branch
`material-volume-campaign-20260924`, base 3db8bc4e)
**Role:** M08 — separate CONDITIONING limits from IMPLEMENTATION defects, across the
DECLARED supported scales and shapes.
**Stop rule:** ladder complete (45/45 rungs executed once). FALSIFIER status: no error
exceeding a derived bound traces to the implementation — all three frozen-rule
DEFECT-CANDIDATEs are diagnosed below to harness, derivation, or fixture causes.
**Zero implementation defects found.**

Tested code: byte-identical copies (sha256-verified) of `tools/material_volume.py`,
`tools/material_volume_admission.py`, `tools/material_volume_body_export.py` in
`work/`, run with `PYTHONDONTWRITEBYTECODE=1`, Python 3.14.3, numpy 2.2.6, CPU-only.
This lane directly covers unverified rows **U2** (`scale_to_m != 1.0`), **U4**
(numerical stress: large coordinates, near-degenerate tets), and **U5** (uniform-scale
covariance at exporter level) of `Chimera/docs/matter/material_volume_export_verification_receipt.md`.

---

## 1. Integration model the code actually uses (quoted)

Both paths integrate EXACTLY (piecewise-polynomial moments), never quadrature —
`work/material_volume.py` `_geometry` (lines 344-384 of the copy):

```python
e = q[:, 1:, :] - q[:, :1, :]                    # three edges from v0 (float64)
scale = np.maximum.reduce(edge_lengths)          # max of all 6 edge norms
en = e / scale[:, None, None]
det_scaled = np.einsum("ij,ij->i", en[:, 0], np.cross(en[:, 1], en[:, 2]))
degenerate = np.abs(det_scaled) <= _DEGENERACY_REL   # 64.0 * EPS
volumes = (det_scaled / 6.0) * scale * scale * scale
centroids = q[:, 0] + np.sum(e, axis=1) / 4.0
```

`_mass_properties`: `m_t = rho_t V_t`, `com = origin + sum(m (c-origin))/M`,
`Q_t = (m_t/20) sum_i (x_i-c_t)(x_i-c_t)^T`, parallel-axis assembly. The exporter
`_integrate_cells` uses the same moments with a **raw** `np.linalg.det` (no scale
normalization) and `_body_mass_properties` applies `R^T(.-origin)`, `R^T I R`.
Doc corroboration (compiler doc, "Derivation"): barycentric moments
`E[lambda_i]=1/4`, `E[lambda_i lambda_j]=(1+delta_ij)/20`. **All error is therefore
float64 roundoff; every bound below is derived from the rounding of exactly these
operations** (full derivation: `PREREGISTRATION.md` section 2).

## 2. Declared-support quote table (the ladder lives inside this support)

| # | What | Declared where | Quote | Numeric limit |
|---|------|----------------|-------|---------------|
| D1 | coordinates | compiler doc, input contract | "Finite numeric `nV x 3` array, `nV >= 4`; no coincident distinct node positions and no unused nodes." | any finite float64; NO magnitude range declared |
| D2 | units | compiler doc | "`coordinate_unit` \| Exact string `m`" | meters only; "µm-scale mesh units" = µm-magnitude meter coordinates (in support) |
| D3 | cell shape gate | compiler doc | "a scale-normalized nondegeneracy gate `|det| / max_edge^3 > 64 * float64_epsilon`" | `> 1.4210854715202004e-14`; the ONLY declared shape limit — NO aspect-ratio max declared, so allowed aspect extends to this gate |
| D4 | orientation | compiler doc | "strictly positive signed determinant ... The compiler never reorders or repairs a cell." | det > 0 |
| D5 | density | compiler doc | "Density must be finite and positive" | any finite positive |
| D6 | scale_to_m | admission doc | "positive finite `scale_to_m`. Every input position is multiplied by this scale to obtain metres." | any positive finite float64; NO range declared |
| D7 | overflow | compiler doc | "arithmetic overflow/nonpositive computed volume is rejected" | named refusal `numeric_overflow` |
| D8 | SI identity | admission doc | "exact float64 hexadecimal SI-coordinate tetrahedra" | SI floats `p*scale` are the identity-bearing geometry |

## 3. Derived per-rung bounds (frozen; formulas, per-rung numbers in `fixtures/manifest.json`)

With `u = 2^-53 = 1.1102230246251565e-16`, `G = 64*eps = 1.4210854715202004e-14`,
`X` = max |SI coordinate|, `delta = |det|/max_edge^3` (exact):

- **Volume/mass:** `rel <= 20u + 12u/delta` — edges from v0 are Sterbenz-exact
  differences at ANY offset; `det_scaled`'s error is ABSOLUTE (`~kappa*u`, O(1) terms),
  so relative error grows as `u/delta` only where O(1) terms cancel to `delta`.
  Compact cells (delta ~ 0.354): bound 54u = 6.0e-15.
- **COM:** `|err|_inf <= 6u * max(X, s, 1)` (absolute, meters).
- **Inertia:** `rel <= 30u * (1 + X)` — det-free; degrades only via COM/offset error.
- **Cross-path (compiler vs exporter raw-det):** `dV <= 40u`, `dI <= 60u(1+X)`.
- **Twins:** power-of-two scale products are exact => bitwise-identical properties.
- **Metamorphic (doc: "V -> s^3 V, m -> s^3 m, I -> s^5 I"):** `<= 40u` / `<= 80u`
  plus exact-geometry deviation.
- **Authored frames:** `com_err <= 8u*max(1,|com|)`, `eI <= 60u`.

## 4. Frozen ladder + classification (45 rungs; full data in `receipts/ladder_results.json`, raw outputs in `receipts/raw/`)

### Class A — offset ladder (coupon at offset X, cell edge ~1)

| rung | X (m) | eV (rel) | eM (rel) | COM err (m) | eI (rel) | verdict |
|---|---|---|---|---|---|---|
| A0 | 0 | 0.0 | 0.0 | 0.0 | 4.97e-17 | PASS |
| A1 | 1e3 | 0.0 | 0.0 | 0.0 | 8.61e-17 | PASS |
| A2 | 1e6 | 0.0 | 0.0 | 0.0 | 4.06e-17 | PASS |
| A3 | 1e9 | 0.0 | 0.0 | 0.0 | 6.94e-16 | PASS |
| A4 | 1e12 | 0.0 | 0.0 | 0.0 | 6.42e-10 | PASS |
| A5 | 1e15 | 0.0 | 0.0 | 0.0 | 6.73e-04 | PASS |
| A7 | 1e16 | — | — | — | — | REFUSED-BY-CONTRACT (`duplicate_vertex_position`) |

**Conditioning characterized:** volume/mass are offset-INVARIANT (0.0 relative error up
to X = 1e15 — the scale-normalized-determinant + Sterbenz-exact-edge design, exactly as
derived); inertia error grows linearly in `u*X` (6.4e-10 at 1e12, 6.7e-4 at 1e15,
bound 30u(1+X) = 3.33 at 1e15). X = 1e16 is the representability horizon: ulp(1e16) = 2
collapses the 1 m cell and the compiler refuses with the declared reason. Export path
(A0x/A4x/A5x) agrees with the compiler **bitwise** (dV = dI = 0.0) at every offset.

### Class B — µm ladder (right tet, edge s at origin) — "small cells"

| rung | s (m) | eV | eM | COM err | eI | verdict |
|---|---|---|---|---|---|---|
| B0 | 1 | 0.0 | 0.0 | 0.0 | 1.80e-16 | PASS |
| B1 | 1e-2 | 1.59e-16 | 0.0 | 0.0 | 2.11e-16 | PASS |
| B2 | 1e-4 | 0.0 | 0.0 | 0.0 | 2.45e-16 | PASS |
| B3 | 1e-6 (µm) | 2.89e-16 | 1.93e-16 | 0.0 | 3.01e-16 | PASS |
| B4 | 1e-8 (nm) | 1.38e-16 | 0.0 | 0.0 | 3.35e-16 | PASS |
| B5 | 1e-10 | 1.31e-16 | 1.75e-16 | 0.0 | 1.71e-16 | PASS |

**No small-scale degradation** — error flat at ~1-3e-16 across 10 decades (scale-free
design). Metamorphic covariance (g) PASS at every rung: `V/s^3` matches B0 to
<= 3.3e-16, `I/s^5` to <= 2.3e-16 (U5 covered at exporter level via class E).

### Class C — flat/thin ladder (det = h, scale = sqrt(2), delta = h/2.828)

| rung | h | delta | eV | eI | verdict |
|---|---|---|---|---|---|
| C0 | 1 | 0.354 | 0.0 | 1.18e-16 | PASS |
| C1 | 1e-2 | 3.54e-3 | 0.0 | 1.19e-16 | PASS |
| C2 | 1e-6 | 3.54e-7 | 0.0 | 1.21e-16 | PASS |
| C3 | 1e-10 | 3.54e-11 | 0.0 | 2.03e-27 | PASS |
| C4 | 1e-13 | 2.49G | 1.89e-16 | 1.73e-16 | PASS |
| C5 | 5e-14 | 1.24G | 1.89e-16 | 1.73e-16 | PASS |
| C6 | 3e-14 | 0.746G | — | — | REFUSED-BY-CONTRACT (`degenerate_tetrahedron`) |
| C7 | 1e-14 | 0.249G | — | — | REFUSED-BY-CONTRACT (`degenerate_tetrahedron`) |

Flat cells stay EXACT down to delta = 1.24G — this family's determinant has no O(1)
cancellation, as the derivation predicted. The declared gate fired between 1.24G
(accept) and 0.746G (refuse), matching the derived ~10u absolute-tolerance boundary.

### Class S — near-degenerate-but-allowed sliver (generic O(1) cancellation; exact-delta bisection)

| rung | delta | eV = eM | eI | verdict |
|---|---|---|---|---|
| S0 | 2.5G | 1.245e-04 | 1.245e-04 | DEFECT-CANDIDATE(beyond-bound) -> **diagnosed: PASS** (see §6) |
| S1 | 1.2G | 7.844e-05 | 7.844e-05 | DEFECT-CANDIDATE(beyond-bound) -> **diagnosed: PASS** |
| S2 | 0.869G | — | — | REFUSED-BY-CONTRACT (`degenerate_tetrahedron`) |
| S3 | 0.499G | — | — | REFUSED-BY-CONTRACT (`degenerate_tetrahedron`) |

This is the family the `u/delta` law exists for: volume error is visible (1e-4 at the
gate boundary) yet 301x inside the frozen worst-case bound (`20u + 12u/delta` = 3.75e-2
at S0), and the gate boundary behaved within its derived ~10u absolute tolerance
(accept at 1.2G, refuse at 0.869G). COM/inertia shape-integrals stay exact (eI - eM
<= 6.7e-17).

### Class D — needle ladder ((0,0,0),(1e3,0,0),(500,w,0),(500,0,w), delta = (w/1e3)^2)

| rung | w | delta | eV | eI | verdict |
|---|---|---|---|---|---|
| D0 | 10 | 1e-4 | 0.0 | 8.7e-21 | PASS |
| D1 | 0.1 | 1e-8 | 2.67e-16 | 1.76e-16 | PASS |
| D2 | 1e-2 | 1e-10 | 2.08e-16 | 1.54e-16 | PASS |
| D3 | 1.5e-4 | 1.58G | 1.13e-16 | 1.10e-18 | PASS |
| D4 | 1.1e-4 | 0.851G | — | — | REFUSED-BY-CONTRACT (`degenerate_tetrahedron`) |
| D5 | 1e-4 | 0.704G | — | — | REFUSED-BY-CONTRACT (`degenerate_tetrahedron`) |

Needles (aspect 1e2..6.7e6 allowed by the gate) stay exact: their determinant's O(1)
terms cancel at exact zeros, so no `u/delta` blowup — again as derived.

### Class E — scale_to_m extremes (full admission+export path)

| rung | declaration | result | verdict |
|---|---|---|---|
| E1 | P=1, scale=1 | eV=0.0, eI=4.97e-17 | PASS |
| E2 | P=2^20, scale=2^-20 | bitwise-identical to E1 | PASS |
| E3 | P=2^-20, scale=2^20 | bitwise-identical to E1 | PASS |
| E4a | P=2^30, scale=2^30 (SI=2^60) | eV=5.50e-15, COM err 256 m, eI=5.47e-15 | PASS |
| E4b | P=2^40, scale=2^20 (SI=2^60) | bitwise-identical to E4a | PASS |
| E5 | P=1e6, scale=1e-6 | bitwise-identical to E1 | PASS |
| E6 | P=1, scale=1e6 (SI=1e6) | eV=1.34e-15, COM err 1.16e-10 (bound 2e-9), eI=1.46e-15 | PASS |
| E7 | P=1, scale=2^-60, ulp pair (invalid fixture, preserved) | refused `degenerate_tetrahedron` | DEFECT-CANDIDATE -> diagnosed: INVALID RUNG (§6) |
| E7b | ulp pair, scale=1e-310 (subnormal SI) | refused `duplicate_vertex_position` | REFUSED-BY-CONTRACT |
| E8 | scale=1e300 | refused `numeric_overflow` (export: blocked) | REFUSED-BY-CONTRACT |
| E1f | two authored frames (identity + 90-deg rotation, origin (3,-2,1)) | per-group COM err = 0.0 exactly, eI = 1.80e-16 both bodies; aggregate eV=eM=0.0 | PASS |

**U2 covered:** `scale_to_m != 1` paths (2^-20, 2^20, 2^40, 1e-6, 1e6, 1e300, 1e-310)
all behave as declared. Power-of-two and the tested decimal twins are **bitwise**
identical (stronger than the derived ulp-level bound). E7b establishes the only
reachable SI-collapse: distinct frame positions CAN map to one SI position — but only
in the subnormal SI regime (scale 1e-310); for normal SI values scaling by
(1+2^-52)-type frame differences shifts the product by >= 1 ulp, so collapse is
unreachable there. The implementation refuses the reachable case with the declared
reason `duplicate_vertex_position` before any geometry runs.
**E8** confirms the declared overflow refusal (D7): SI edges ~1e300 overflow
`scale^3`; admission reports `compiler_refusal: numeric_overflow`, export is `blocked`
with `reconstructed_mass_admission_required` — no garbage exported.

## 5. The conditioning map (objective answer)

- **Volume/mass:** conditioning-free across the entire declared support probed —
  0.0 to 2.9e-16 relative error for offsets 0..1e15, cell edges 1e-10..1e6 m, aspects
  up to 6.7e6, and near-gate flat/needle shapes. The ONLY volume error growth is the
  derived `kappa*u/delta` law for generic cancellation shapes (class S), bounded by
  ~10% at the declared gate and measured at 1.2e-4 (301x inside bound).
- **COM:** error tracks `u*X` (derived `6u*max(X,s,1)`): measured 0.0 up to X=1e15 on
  this fixture, 256 m at SI coordinates 2^60 (E4), 1.16e-10 at SI 1e6 — every rung
  inside bound with >= 3x margin.
- **Inertia:** error grows linearly in `u*X/D` for the offset class (5e-17 -> 6.4e-10
  -> 6.7e-4 at X = 0/1e12/1e15) and inherits mass error near the gate (S0/S1);
  det-free elsewhere (exact to 1e-16 for flat/needle/small classes).
- **Conditioning horizon:** X/s ~ 9e15 (A7): cells stop being representable; SI values
  below ~1e-307 (E7b): distinct positions collapse; delta within ~1 ulp-scale of the
  64eps gate: acceptance flips at ~10% of the gate value. Everything at the horizon is
  a declared, named refusal — never silent garbage.
- **Defects:** none. Every declared gate (D1/D3/D7) fired with its exact declared
  reason in every refusal case, and no accepted rung exceeded a bound that survives
  diagnosis.

## 6. Falsifier diagnoses (all three DEFECT-CANDIDATEs; frozen-rule verdicts preserved verbatim in receipts)

1. **S0, S1 (beyond-bound):** measured eV = eM = eI = 1.2449758459374786e-04 (S0) /
   7.8441066146859559e-05 (S1) — all three IDENTICAL to 14 digits. Inertia entries are
   homogeneous linear in the masses, so inertia inherits the mass relative error;
   the shape-integral error is eI - eM <= 6.7e-17. The volume error is 301x (S0) /
   995x (S1) inside the frozen volume bound. **Diagnosis: derivation omission** — the
   frozen inertia bound `30u(1+X)` omitted the mass-factor propagation term; corrected
   bound `B_I' = B_I + B_V` (mass linearity is exact in the model). No bound of any
   other rung was touched; no code change. Corrected verdict: **PASS** (the near-gate
   error growth the derivation predicted is present and bounded).
2. **E7 (refusal reason mismatch):** fixture-construction error — the ulp pair was
   placed collinear with a third vertex, so the cell has det = 0 in FRAME coordinates
   already (oracle-recorded delta = 0 before any scaling); additionally a
   power-of-two scale is exact, so it can never collapse distinct positions. The
   refusal `degenerate_tetrahedron` is correct declared behavior on a genuinely
   degenerate input. Run preserved as invalid; coverage completed by E7b (which the
   implementation passes with the exact declared reason).
3. **E1f (runner-internal, caught before classification):** the first harness compared
   group[0] (one cell) against the whole-coupon oracle — a harness bug, fixed in the
   runner before final receipts; the implementation's per-group outputs were exact
   (COM err = 0.0, eI = 1.8e-16) throughout.

## 7. Versioning transparency

- `PREREGISTRATION.md` frozen before any execution. One pre-execution correction is
  recorded in place (dimensional fix of the volume bound, caught in derivation
  self-check before fixture generation; no run had happened).
- Manifest snapshots: `receipts/manifest_v1_frozen_snapshot.json` (44 rungs, first
  run), `manifest_v3_snapshot.json`; live `fixtures/manifest.json` (85e1f263d408f8d4...)
  differs from v1 by the ADDED E7b rung only (verified programmatically: zero changed,
  zero removed v1 rungs). E7b was added to complete the declared collapse coverage
  after E7 was diagnosed invalid; its prediction was frozen before its (single) run.
- Receipts: `receipts/env.json` (versions + module hashes),
  `receipts/ladder_results.json` (per-rung measurements, bounds, verdicts,
  diagnoses, twin/cross-path/metamorphic/frame checks), `receipts/raw/*.json`
  (38 full compiler/exporter outputs). Fixtures: `fixtures/*.json` (v1 documents and
  manifest/partition/groups triples, all from the existing schemas).

## 8. Integrity

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty — no output, exit 0)
```

`tools/` and `Chimera/docs/matter/` untouched (read-only honored; module copies in
`work/` are sha256-identical to sources; no `__pycache__`/`.pyc` created in `tools/`).

## 9. Limitations (honest scope)

- Fixtures are analytic coupons/families (single tets and the doc's two-cell coupon);
  no anatomical mesh is tested (out of M08 scope, and none exists in the campaign).
- The sliver family probes cancellation near the gate with one generic O(1) geometry;
  other sliver geometries will vary within the frozen bound, not outside it (the bound
  is a worst case over 3-term cancellations with kappa <= 12).
- The overlap-SAT tolerance path and topological refusals are outside this lane's
  accuracy question and were not re-tested here.
- "Bitwise twin" comparisons cover the tested declarations; other (frame-position,
  scale) pairs may differ at ulp level within derived bounds (f).
