# S3 — Reusable reduced response (mechanism factory)

Gate: GAME_PLAN_ACTION_RPG.md §13.1, row **S3 — reusable reduced response**
("Analytical reduction, table or fitted approximation with explicit validity
query | Held-out scales/geometries/load cases, conservation/passivity as
applicable, no silent extrapolation; measured benefit over the same detailed
workload").

Written 2026-10-18 by Maya (mechanism_factory increment). **CPU only**; no
engine boot, no GPU, no published file touched, nothing committed. S3 is a
REDUCED MODEL WITHIN the record's current admitted domain — no domain claim
is amended or extended.

**Preregistration frozen at 2026-10-18T07:04:46.414763+00:00** (sha256
`2ebcdae17638df9dbbf82d259febd1f4157d238efd953d5278a96b908b7c6c90`), BEFORE
any held-out solve. The prereg script imports no solver and runs no solve;
an earlier same-content run of it (results
`…/results/20261018-020445-895c6833`) crashed on a sympy type issue after
freezing an identical file and ran no solves. Final check evidence:
`D:/Chimera-Maintenance/Runtime/local-ai/math-tools/results/20261018-022904-ff40746f/result.json`
(script `checks_tmp/s3_reduced_response_check.py`, **PASS 53/53**). Receipt:
`s3_reduced_response_receipt_20261018T072919.936426Z.json`. One superseded
receipt (`…T072643.952456Z.json`, identical physics) is retained: its run
mis-implemented the preregistered benefit-ratio formula (divided by
repeats×cells instead of cells×median-per-query); the corrected run
re-measured, and the ratio changed from the wrongly-computed 75.8x to
7.4318e+04x. No physics number changed between the two runs.

---

## 1. The reduction artifact

One-dimensional map **η(Π)** for `assembly.star-k2` (the similarity law makes
the response 1-D even though the input space is (s, F)): Π = F/(γ·s·r₀),
η = z_apex/(s·r₀), r₀ = 1.0 wu (frozen recipe rim radius), so Π = F/s and
η = z_apex/s at γ = 1.

- **Data file:** `docs/evidence/mechanism_factory/s3_star_eta_pi_table_v1.json`
  (schema `chimera-mechanism-factory-s3-reduced-response-v1`, sha256
  `17b0ce5472ffd6d98e85c2b8a4e2e4b35d6cf85dafc14d43a25f52b1d0c16ee2`).
- **Nodes** (Π, η), taken digit-for-digit from the s = 1.0 reference rows of
  the pinned `load_domain_study_20261017.json` (sha
  `da16eccc8ca37957…`), all in-gate under the packet's 1e-6 N law:

  | Π    | η (wu, dimensionless)  | source cell status |
  |------|------------------------|--------------------|
  | 0.0  | 0.386956838052729      | stagnated, 9.79e-8 N |
  | 0.4  | 0.3366523561687648     | stationary, 5.3e-14 N |
  | 0.8  | 0.2843804870391736     | stagnated, 7.3e-7 N |
  | 1.2  | 0.2296675745291137     | stagnated, 4.6e-7 N |
  | 1.6  | 0.17205904840608507    | stagnated, 3.3e-7 N |
  | 2.0  | 0.11109764355919904    | stagnated, 2.7e-7 N |

  **Π = 0 inclusion decision:** the zero-load row IS tabulated (it is an
  already-measured in-gate cell), but the validity query accepts Π = 0
  **only at s = 1.0** — the F = 0 dilation argument (S0: the unloaded
  equilibrium scales exactly as x → s·x) is derived, not measured, off
  s = 1.0, and S3 does not convert a derivation into a measured claim.
- **Interpolation:** Fritsch–Carlson monotone cubic Hermite (PCHIP-equivalent,
  shape-preserving — overshoot is impossible on the strictly monotone node
  table). Selection was preregistered by worst interior-node
  leave-one-node-out error ON THE NODE SET ONLY (no solves): linear worst
  **1.676e-03** (at Π = 1.6; 17× over TOL_ETA — rejected) vs monotone-cubic
  worst **2.569e-04** (conservative: at LOO Π = 0.4 the cubic evaluates
  OUTSIDE the reduced node range and still wins at every interior node).
  Non-monotone splines were excluded a priori (overshoot risk). The
  dependency-free implementation agrees with `scipy.interpolate.
  PchipInterpolator` to max |diff| = **1.11e-16** over [0.4, 2.0].
- **Pins carried in the data file:** law_revision
  `ee9effcfbddad8d0…` (verified equal to current law bytes), solver
  `patch_equilibrium.py` `a0f4b9f9b289ef1e`, `composed_chain.py`
  `c3c0ae0a40b3ba04`, packet cap max_force_N = 2.0 (preregistered law,
  quoted, never widened), record valid_scales/valid_loads quoted unchanged,
  preregistration path + sha, study and S1 receipt shas.

## 2. Explicit validity query (no silent extrapolation)

Pure function `validity_query(scale, load_N, gamma) -> (valid, code, reason,
Pi, flags)` — no solve, no I/O — in `checks_tmp/s3_reduced_response_check.py`,
mirrored rule-for-rule in the data file's `validity_rules`. Ordered refusals:

| code | condition | reason (as returned) |
|---|---|---|
| 1 | non-finite / negative inputs | invalid_input |
| 2 | γ ≠ 1.0 | **S0 gap 6**: the γ axis is degenerate — the law maps γ into Π, but no cell off γ = 1.0 was ever measured, so the query refuses and says so |
| 3 | scale outside [0.75, 2.0] | outside the record's measured window |
| 4 | F > 2.0 N | packet cap `max_force_N = 2.0` (preregistered, never widened; the record's 2.5/3.0 N rows are s = 1.0-only and above the cap — S0 gap 2, noted, not resolved) |
| 5 | Π > 2.0 | outside the tabulated/measured invariance window |
| 6 | 0 < Π < 0.4 | unmeasured gap between the zero-load cell and the measured window |
| 7 | Π = 0 at s ≠ 1.0 | zero-load cell measured at s = 1.0 only |

Valid answers carry flags: `scale_interpolated` (s inside [0.75, 2.0] but not
a measured node {0.75, 1.0, 1.5, 2.0}), `zero_load_measured_cell`, and the
named caveats — **no self-intersection/ground-crossing refusal exists (S0
gap 3)** (within the valid window η ≥ 0.111, so the apex stays above the rim
plane; the observed 3.0 N crossing is outside the domain, and the query
cannot refuse a self-intersecting configuration because the law has no such
variable); **dynamics not excluded (S0 gap 7): quasistatic prediction only**.

**Probe results (receipt `probes`, all digit-for-digit):** refused —
(s=3.0, F=0.8)→3; (s=0.5, F=0.8)→3; (s=1.0, F=2.5 N)→4; (s=0.75, F=1.8 N,
Π=2.4)→5; (s=1.0, F=0.8, γ=1.2)→2; (s=1.0, F=0.2 N, Π=0.2)→6; (s=0.75,
F=0)→7. Accepted — (s=1.0, F=0)→0 with zero-load caveat; (s=1.1, F=0.8)→0
flagged `scale_interpolated`. Every fresh held-out cell was required to pass
its own validity query before its solve.

## 3. Held-out validation (the gate's core)

Preregistered: node set, scheme, metric (max |Δη| = |η_pred − η_meas| over
fresh cells), and threshold **T_S3 = 1e-4** (= S1's TOL_ETA; ≥ 545× the S1
stagnation floor 1.831e-07 — never below the noise floor). Fresh cells are
never-solved (s, F) pairs at measured scales, Π strictly between nodes;
cap-truncated designs ((1.5, 2.1), (2.0, 2.8), (1.5, 2.7), (2.0, 3.6)) were
recorded and never solved.

**Fresh cells (10 solves, all in-gate, residuals 1.9e-7 … 9.3e-7 N):**

| s | F [N] | Π | status | η measured | η predicted | Δη |
|---|---|---|---|---|---|---|
| 0.75 | 0.45 | 0.6 | stagnated | 0.310792604665556 | 0.310790825851044 | −1.779e-06 |
| 1.0 | 0.60 | 0.6 | stagnated | 0.310792604665556 | 0.310790825851044 | −1.779e-06 |
| 1.5 | 0.90 | 0.6 | stationary | 0.310792490220985 | 0.310790825851044 | −1.664e-06 |
| 0.75 | 0.75 | 1.0 | stagnated | 0.257357830805061 | 0.257356387382043 | −1.443e-06 |
| 1.0 | 1.00 | 1.0 | stagnated | 0.257357675366609 | 0.257356387382043 | −1.288e-06 |
| 1.5 | 1.50 | 1.0 | stagnated | 0.257357830805061 | 0.257356387382043 | −1.443e-06 |
| 0.75 | 1.05 | 1.4 | stagnated | 0.201253306850710 | 0.201252582022606 | −7.248e-07 |
| 1.0 | 1.40 | 1.4 | stagnated | 0.201253306850710 | 0.201252582022606 | −7.248e-07 |
| 0.75 | 1.35 | 1.8 | stagnated | 0.142027054555548 | 0.142003381543312 | **−2.367e-05** |
| 1.0 | 1.80 | 1.8 | stagnated | 0.142027054555548 | 0.142003381543312 | **−2.367e-05** |

**Worst fresh |Δη| = 2.3673e-05** at (s = 1.0, F = 1.8 N, Π = 1.8) — 4.2×
under T_S3, and digit-for-digit identical at s = 0.75 (the two cells agree
to 2e-17). Retained-cell free validation (7 already-measured S1 rows excluded
from the node set, zero new solves): |Δη| from **1.358e-06** to
**5.609e-06** at Π ∈ {0.5333, 0.6, 1.0, 1.0667, 1.3333} — all ≤ T_S3.

**Stagnation vs interpolation decomposition (prereg P7):**
- Empirical 2-solve solver noise = matched-Π spread among the fresh cells at
  the same Π: max **1.554e-07** (Π = 1.0, 3 scales), consistent with the S1
  floor 1.831e-07; at Π = 1.4 and 1.8 the fresh cells agree to ~1e-16.
- Per-cell residual-scaled bound u = res_held/s + res_node/1.0 (P =
  1/γ_max = 1 wu/N): worst cell u = **5.93e-07**.
- Therefore the worst |Δη| = 2.367e-05 is **≥ 97.5% interpolation error**
  (lower bound 2.308e-05) and ≤ 2.5% solver stagnation — reported honestly
  as a bound, not asserted to machine precision. Diagnostic: re-solving the
  worst cell with max_steps = 120000 (2× budget) moved η by exactly **0.0**
  — the 60k stagnation exit is not the error source.
- Node cells themselves carry S1's measured stagnation noise (the node η at
  Π = 0.8 differs from the S1 matched-grid η by 1.831e-07 — the floor).

## 4. Conservation / passivity

**Passivity is NOT APPLICABLE**: the reduced response is a static
equilibrium map — no dynamics, no energy storage, no time variable (the law
is quasistatic by construction, S0 gap 7). If dynamics enter later, what
WOULD apply: energy balance/passivity of the relaxation (the solver's
monotone descent already evidences the static half), and an inertia/
damping characterization before any transient claim. What WAS checked is a
**static consistency check, labeled as such (not conservation)**: η is
strictly decreasing in Π over the node table AND every fresh measured η
falls strictly between its bracketing node values (recorded PASS 10/10 in
the check run). No conservation law is claimed anywhere.

## 5. Measured benefit over the same detailed workload

Same 10-cell held-out workload, same machine, sequential:

- **Detailed path:** `build_star` + `solve_equilibrium` to convergence
  (max_steps = 60000, stagnation exit) — wall clock **includes the geometry
  build**; per cell 0.20–2.65 s; total **11.393 s**.
- **Reduced path:** validity query + table interpolation, median **15.33
  µs/query** (1000 repeats × 10 cells); whole workload **153.3 µs**.
- **Measured benefit ratio: 7.4318e+04×** (preregistered formula: total
  detailed wall / (median reduced × n_cells); no preregistered minimum —
  measured, not asserted).

## 6. Verdict

**S3 PASS, scoped exactly to the gate row.** Reduction: a reusable 1-D
η(Π) table + monotone-cubic interpolation with pins and exact domain.
Validity query: pure, explicit, refusing everything outside the measured
world, including the γ-degeneracy (gap 6) and the unmeasured (0, 0.4) gap.
Held-out: 10 fresh never-solved cells + 7 retained cells, worst |Δη|
2.367e-05 ≤ T_S3 = 1e-4, honestly decomposed (≥ 97.5% interpolation,
≤ 2.5% stagnation; noise floor 1.554e-07 vs S1's 1.831e-07). No silent
extrapolation (probe table). Passivity N/A stated, consistency check
labeled. Benefit measured at 7.43e4× on the identical workload.

**Named explicitly (not hidden):** (a) the reduction is valid ONLY at
γ = 1.0 — a γ-ray measurement (S0 gap 6) is the cheapest extension and was
not in scope; (b) the (0, 0.4) Π-gap and all Π > 2.0 are refused, so the
2.5/3.0 N load-domain rows stay out of the reduced model (packet cap, S0
gap 2 unresolved by S3 by design); (c) scale-interpolated predictions
(s ∉ {0.75, 1.0, 1.5, 2.0}) are flagged, not refused — the collapse was
measured at 4 discrete scales; (d) no self-intersection variable exists
(gap 3) — the query inherits that blindness, mitigated only by the fact
that η ≥ 0.111 over the whole valid window; (e) one superseded receipt
(…T072643) is retained on disk for its mis-computed benefit ratio; (f) the
worst-cell error (2.37e-05) is real interpolation error at the table's
current 0.4-wide node spacing — refining nodes would need NEW measurements,
which S3 does not make.

## 7. Reproduction

```
# prereg (freezes before any solve; already frozen)
math_check.py checks_tmp/s3_preregister_check.py
# main (10 fresh solves + probes + timing; ~30 s)
math_check.py checks_tmp/s3_reduced_response_check.py
```
Scripts: `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/checks_tmp/
s3_preregister_check.py`, `…/s3_reduced_response_check.py` (repo paths
inserted in-script). Evidence dirs: `…/results/20261018-020445-895c6833`
(prereg), `…/20261018-022904-ff40746f` (final). Artifacts:
`s3_preregistration_20261018T070446.414763Z.json`,
`s3_star_eta_pi_table_v1.json`,
`s3_reduced_response_receipt_20261018T072919.936426Z.json` (plus the
retained superseded receipt `…T072643.952456Z.json`), all under
`docs/evidence/mechanism_factory/`. Every number in this report is present
digit-for-digit in the receipt.
