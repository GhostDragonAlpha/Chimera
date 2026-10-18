# S1 — Detailed multiscale reference (mechanism factory)

Gate: GAME_PLAN_ACTION_RPG.md §13.1, row **S1 — detailed multiscale
reference** ("Same mechanism at several physical scales and independently
varied mesh resolutions. Preregistered reference/convergence tests; scale
transfer distinguished from remeshing; matched and deliberately unmatched
regimes."). Also closes S0 gap 1 (§7 of `S0_mechanism_scale_contract.md`):
the scale × load cross-product admitted by `_in_domain` but measured
nowhere.

Written 2026-10-17 by Maya (mechanism_factory increment). CPU only; no
engine, no GPU; no published file touched. Receipt:
`s1_multiscale_receipt_20261017T231542.626384Z.json`. Check evidence:
`D:/Chimera-Maintenance/Runtime/local-ai/math-tools/results/20261017-181505-5ba68718/result.json`
(script `checks_tmp/s1_multiscale_reference_check.py`, sha256
`3a5b4f530f83fb5b…`, **PASS 15/15**).

---

## 1. Preregistration (quoted from the check script header, frozen before the grid was solved)

> **Mechanism:** assembly.star-k2 (composed_chain), constant-γ law
> γ = 1.0 J/wu². Reference row: the measured s = 1.0 loads 0.0–2.0 N of
> `load_domain_study_20261017.json`.
> Coordinates (derived in S0): Π = F/(γ·s·r₀) = F/s, η = z_apex/(s·r₀) = z_apex/s
> (r₀ = 1.0 wu). Exact similarity iff F scales as s.
>
> **T1** Every in-grid solve terminates in a named state with
> free_residual ≤ 1e-6 N (packet law; stagnated-with-residual-in-gate is a
> valid terminal state). Any out-of-gate solve fails S1.
> **T2** Matched-Π collapse tolerance **TOL_ETA = 1e-4** (dimensionless):
> |η(s, s·F_ref) − η_ref(F_ref)| ≤ TOL_ETA for every grid point.
> Justification: per-solve displacement bound = 1e-6 N × P = 1/γ_max =
> 1 wu/N = 1e-6 wu; η divides z by s·r₀ ≥ 0.75 wu, two independent solves
> ≤ ~2.7e-6 η-units; 1e-4 is a ≥ 37× margin (S0 used tol_z = 2e-5 wu on
> the patch).
> **T3** Unmatched controls (F = F_ref fixed, NOT scaled): deviation
> > 10·TOL_ETA = 1e-3 for EVERY point. A silently similar fixed-F
> comparison would falsify the S0 derivation.
> **T4** Reference determinism: re-solve (1.0, 0.8 N), apex_z must
> reproduce the study's 0.2843804870391736 wu within 1e-9 wu.
> **T5** Packet port cap: NO solve above F = 2.0 N; cells with F(s) > 2.0 N
> are excluded (recorded, never solved).
> **T6** Resolution axis at ONE Π point (patch fan, s = 1.0, F = 0.8 N):
> n_rim ∈ {200, 300}, offset REPORTED as the remeshing magnitude, not
> gated; binding cross-checks to the retained
> `scale_resolution_study_20261016T142810.182Z.json` cells (1e-9 wu at
> n_rim 200, 1e-6 wu at 300). No resolution-convergence claim.
> **T7** FAILED S1 = any T1 violation, any matched |Δη| > 1e-4, any
> unmatched deviation ≤ 1e-3, broken T4/T6 determinism, or any solve above
> the cap.

Honesty note: four wall-clock timing probes ((1.0, 0.8), (2.0, 1.6),
(2.0, 0.4), (0.75, 1.5)) were run before this file was written; no
tolerance was chosen from them (TOL_ETA follows from the S0 residual ×
compliance bound).

## 2. Results

All 27 solves in-gate (residuals 5.6e-14 … 9.6e-07 N); full digit-for-digit
grid in the receipt. Matched-Π grid (F = s·F_ref):

| s | F_ref → F(s) | Π | η | Δη vs η_ref | worst per scale |
|---|---|---|---|---|---|
| 0.75 | 0.4→0.300, 0.8→0.600, 1.2→0.900, 1.6→1.200, 2.0→1.500 | 0.4…2.0 | 0.336652356169 … 0.111097643559 | 8.1e-15, 1.831e-07, 8.3e-17, 1.1e-16, 9.7e-17 | **1.831e-07** |
| 1.5 | 0.4→0.600, 0.8→1.200, 1.2→1.800 | 0.4, 0.8, 1.2 | same η values as reference | 8.1e-15, 1.831e-07, 8.3e-17 | **1.831e-07** |
| 2.0 | 0.4→0.800, 0.8→1.600 | 0.4, 0.8 | 0.336652356169, 0.284380389258 | 0.0, 9.778e-08 | **9.778e-08** |

Truncated by the 2.0 N cap (excluded, not solved): (1.5, F 2.4 N),
(1.5, 3.0 N), (2.0, 2.4 N), (2.0, 3.2 N), (2.0, 4.0 N). Consequence: the
full 3-scale matched claim covers Π ∈ {0.4, 0.8}; Π = 1.2 is a 2-scale
claim (0.75, 1.5); Π ∈ {1.6, 2.0} are measured against the single scale
0.75 only.

Unmatched fixed-F controls: 15/15 deviate, min 1.696e-02 (s = 1.5, F = 0.4),
max 1.463e-01 (s = 2.0, F = 2.0) — all > 100× the 1e-3 floor. The matched
and unmatched grids share the diagonal cells where s·F_a = F_b (e.g.
(0.75, 1.2 N) is both the matched partner of η_ref(1.6) and an unmatched
point vs η_ref(1.2)); both roles are recorded.

Resolution contrast (patch, Π = 0.8): apex_z(n_rim 200) = −0.2633079630900263,
apex_z(300) = −0.26331954596416196 — both reproduce the retained study
cells within preregistered tolerances (200-cell to 0.0 exactly); remeshing
offset |Δη| = **1.158e-05** η-units, ~63× the worst matched-Π deviation but
still 8.6× under TOL_ETA.

## 3. Verdict

**S1 PASS.** η(Π) collapses across scales at matched Π within the
preregistered TOL_ETA = 1e-4 — worst |Δη| = 1.831e-07 (>540× margin) — and
deliberately-unmatched fixed-F points do NOT collapse (min deviation
1.696e-02, >169× the floor). No partial-break region: the matched deviations
sit at the solver's stagnation-noise floor (stagnated cells ~1.8e-07,
stationary cells ≤ 1e-13) uniformly over the measured Π range. Scale
transfer is distinguished from remeshing structurally: the star recipe pins
n_rim = 200 for every piece, so dilation is NOT remeshing (faces and vertex
count byte-identical across scales; only positions multiply by s) — and the
measured one-point remeshing offset (1.158e-05) is an order below TOL_ETA,
so even that residual discretization component cannot explain any matched
deviation.

**What it changes for the record's admitted Cartesian domain:** S0 gap 1 is
now measured, partially. The (scale × load) cross-product is filled with
in-gate measured cells at scales {0.75, 1.5, 2.0} × loads {0.3–1.8 N} on
the F ∝ s rays (matched), plus fixed-F columns {0.4–2.0 N} at each scale
(unmatched regime), all under the 1e-6 N law — but only up to the 2.0 N
packet cap: cells (1.5, >2.0 N) and (2.0, >1.6 N on the matched ray) remain
unmeasured, and the record's own `valid_loads_N` rows at 2.5/3.0 N are
still measured at s = 1.0 ONLY. So `_in_domain`'s Cartesian-product claim
is now *overclaimed only above the packet's 2.0 N cap and at (s > 1.0,
F > 2.0 N)*; within the packet's admitted domain the cross-product is
measured (25 new cells + 6 reference rows). The similarity law itself is
upgraded from "derived and verified at two patch points" to a measured
invariance of the star mechanism over Π ∈ [0.4, 2.0] — which also means
the record's fixed-N `valid_scales` family is now explicitly labeled (by
measurement, not just derivation) as Π-sweeps, not similarity points.
