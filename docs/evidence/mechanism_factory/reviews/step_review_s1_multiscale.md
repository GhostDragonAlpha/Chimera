# Step review — S1 multiscale reference

Verdict: PASS (one nuance, one minor prose correction).

## 1. Reproduction

Ran the pinned check script (sha256 3a5b4f530f83fb5b66180d7d453a808420881a2e2035de1d7f0d08f7001766e8) via the Strata venv python on 2026-10-18. All 27 in-grid solves terminated in-gate (residuals 5.6e-14 … 9.6e-07 N). Results match Maya's receipt `s1_multiscale_receipt_20261017T231542.626384Z.json` digit-for-digit:

- Worst matched-Pi |Δη| = 1.8305783322514202e-07 at (s=0.75, F=0.6 N) and (s=1.5, F=1.2 N); 9.778133114313192e-08 at (s=2.0, F=1.6 N).
- Unmatched controls: min deviation 1.696263e-02 (s=1.5, F=0.4 N), max 1.462601e-01 (s=2.0, F=2.0 N).
- T4 determinism: apex_z(1.0, 0.8 N) reproduced to 0.0 vs study 0.2843804870391736 wu.
- T6 patch cross-checks: n_rim=200 exact (0.0), n_rim=300 exact (0.0) vs retained study.
- Remeshing offset |Δη| = 1.158287e-05.

Overall: PASS.

## 2. Preregistration freeze

The check script's birth and modify times are both 2026-10-17 18:14:43 CDT, approximately one minute before the receipt timestamp (18:15:42 CDT). The script sha256 matches the recorded hash. The four wall-clock timing probes were run before the file was written, per the header, and no tolerance was chosen from them. Verdict: preregistration is genuinely frozen.

## 3. Tolerance justification — physics check

Arithmetic:
- Compliance: γ = 1.0 J/wu². Since 1 J = 1 N·wu, γ = 1 N/wu, so P = 1/γ = 1 wu/N. Correct.
- Per-solve displacement bound: packet `max_free_residual_N` = 1e-6 (S0 contract notes this is a displacement in wu, mislabeled as N) × 1 wu/N = 1e-6 wu. Correct.
- eta uncertainty per solve: 1e-6 wu / (s·r₀) ≤ 1e-6 / 0.75 = 1.333e-6.
- Two independent solves: ≤ 2.666e-6 eta-units.
- TOL_ETA = 1e-4 gives margin 37.5×. Correct.

Physics assessment: The argument assumes the solver's `free_residual` bounds displacement error via constant compliance P = 1/γ_max. For the constant-γ law with geometric nonlinearity (normal recomputed from current geometry), this is a tangent-stiffness linearization. S0 verified it empirically on the patch (measured deviations 0.0 at double precision for similarity cases). The assumption is acceptable within this codebase's conventions.

## 4. S1 gate ruling

PASS. The gate requirements from GAME_PLAN_ACTION_RPG.md §13.1 are satisfied:

- Preregistered reference/convergence tests: T1–T7 are preregistered in the script header before the grid ran.
- Scale transfer distinguished from remeshing: The star recipe pins n_rim=200, so dilation yields byte-identical faces (topology unchanged). The one-point resolution contrast (patch fan, n_rim=200 vs 300) measures the remeshing offset quantitatively and shows it is an order of magnitude below TOL_ETA, so it cannot explain any matched deviation.
- Matched and deliberately unmatched regimes: Matched-Pi collapse passes (worst |Δη| = 1.83e-7 << TOL_ETA); unmatched fixed-F controls all deviate > 1e-3 (min 1.696e-2).

Resolution axis: honest deferral, not a gate miss. T6 explicitly preregisters the one-point contrast as "reported remeshing magnitude only; no resolution-convergence claim." The S0 contract already acknowledges that the resolution ladder does not reach the 1e-6 wu displacement tolerance. The structural byte-identity argument plus the quantitative offset suffice to distinguish scale transfer from remeshing.

## 5. Domain-read ruling

PASS, with nuance. The characterization "measured within the packet cap, overclaimed above it" is correct in spirit:

- Within the 2.0 N packet cap: the matched rays (F = s·F_ref) and unmatched fixed-F columns are measured at scales {0.75, 1.5, 2.0}. This partially fills the Cartesian product claimed by `_in_domain`.
- Above the cap: the record's `valid_loads_N` includes 2.5/3.0 N, but these are measured at s=1.0 only (from the load-domain study). Cells at s > 1.0 with F > 2.0 N are truncated and never solved.

Nuance: "Measured within the packet cap" should be read as "measured at the preregistered ray and column points within the cap", not "the full Cartesian product is filled." Points such as (s=0.75, F=0.0) or (s=2.0, F=0.6) are not measured.

Minor prose correction: The report states "(2.0, >1.0 N on the matched ray) remain unmeasured." This is incorrect; the matched ray at s=2.0 includes F=1.6 N, which is measured. The correct statement is "(2.0, >1.6 N on the matched ray)" or simply "(2.0, >2.0 N)". The receipt's `coverage_note` correctly states "Pi in {1.6, 2.0} vs the single scale 0.75 (others truncated by the 2.0 N cap)."

## 6. Per-claim verdicts

| Claim | Verdict | Evidence |
|---|---|---|
| 1. Preregistration frozen | PASS | Script mtime 18:14:43 < receipt 18:15:42; sha256 unchanged |
| 2. Matched-Pi collapse at every scale | PASS | Worst |Δη| = 1.83e-7 (s=0.75, 1.5), 9.78e-8 (s=2.0); all << TOL_ETA=1e-4 |
| 3. Unmatched controls 15/15 do NOT collapse | PASS | Min 1.696e-2, max 1.463e-1; all > 169× 1e-3 floor |
| 4. Reference determinism | PASS | apex_z(1.0, 0.8) reproduced to 0.0 vs study 0.2843804870391736 |
| 5. Cap truncation recorded, never solved | PASS | 5 cells truncated; 3-scale claim covers Π∈{0.4,0.8}, 2-scale Π=1.2, 1-scale Π∈{1.6,2.0} |
| 6. Remeshing separation | PASS | Star recipe pins n_rim=200 (dilation); one-point contrast reported, offset 1.158e-5; honest deferral |
| 7. Domain read | PASS (nuanced) | Measured at rays/columns within cap; overclaimed above cap (2.5/3.0 N only at s=1.0; s>1.0, F>2.0 N truncated) |

Review path: `docs/evidence/mechanism_factory/reviews/step_review_s1_multiscale.md`
