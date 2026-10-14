# PREREGISTRATION — P6 re-preregistration: the two-sided predicate (`p6_repreregistration_20260921`)

Lane `agent/p6-repreregistration-20260921`, base `427e9d0` (branch `agent/hip-pivot-proof-20260921`,
the proof head). Named successor of the voided §5-P6 predicate. This file is banked
(`preregistration.sha256`) BEFORE the two-arm contrast is re-run; so is the law-doc amendment block
it carries (`docs/THE_ARTICULATION_LAW.md` §5A, `law_amendment.sha256`). The prior lane's records are
consumed READ-ONLY and never edited: §5-P6 as written is VOID in the record forever. Nothing below is
chosen by taste: every number is committed, parsed, derived by a stated formula from committed
geometry, or a PREDICTION carrying its own falsifier.

---

## 1. THE PRIOR AND ITS VOID (the record, never edited away)

- The design's §5-P6 (`docs/THE_ARTICULATION_LAW.md`, §5, verbatim there and in the prior lane's
  `hip_pivot_proof_20260921/preregistration.md` §1): the null-pivot arm BREACHES the 3.0 mm cut at
  range extremes, and "if the null arm PASSES, the pivot derivation is doing no work and the
  design's pivot law is void."
- THE CLAUSE FIRED AS WRITTEN (2026-09-21): the null arm PASSED the one-sided cut — min gaps
  0.2093/0.0884 mm (hip 02) and 0.0467/0.1169 mm (hip 03) at the endpoints — while its femoral head
  LEFT THE SOCKET by 5.745805839276 mm (hip 02) and 3.945980865254 mm (hip 03). Verdict recorded in
  the prior lane's receipt (`P6_as_written_THE_TEETH: RED`), battery sha256
  `18f0ef0641cdcba610bb0a67109540220cfb3400bdff1eee2ae6451fb7d81c16`. The prior lane also BANKED,
  before its control ran, the derivation that predicted exactly this pass (its preregistration §6):
  the degeneracy is the PREDICATE's, not the pivot's.
- The measured discriminator the failed predicate could not carry: head-center displacement 0.0
  EXACTLY (real arm) vs 5.7458/3.9460 mm (null arm) — recorded in the same committed battery.

## 2. THE DERIVATION — the corrected predicate P6′ (zero new free numbers)

### 2.1 Why the one-sided cut is degenerate (restated from the banked derivation)

Let M be the recorded closest-points midpoint, w = on_0X − on_01 (|w| = the recorded refined gap
1.403/1.343 mm). For EVERY rotation about ANY axis through M the realized apposition-pair distance
is |w|·|cos(θ/2)| ≤ |w| < 3.0 mm. The pivot sits inside the apposition gap, so the global min gap
CANNOT leave the touching class for any θ — the cut cannot see ANY rotation about such a pivot,
including the rotation that swings the head out of the socket. A predicate that cannot fail cannot
be a tooth. P6′ fixes the predicate on two legs, each derived from committed data:

### 2.2 LEG 1 — the seat band is TWO-SIDED: g ∈ [tol_ip, cut]

- Upper edge: cut = 3.0 mm, the committed touching-class cut
  (`bone_identification_v3.json` `derived_cuts.joint_gap_mm`), unchanged.
- Lower edge: **tol_ip = specimen.resolution_um / 2 = 160 µm / 2 = 80 µm = 0.08 mm** — DERIVED: the
  committed CT sampling step is the definition's own field (`specimen.resolution_um = 160`); a
  triangulated isosurface localizes the true surface to HALF its sampling step (the crossing is
  bracketed by adjacent samples), so the shell's position uncertainty is ±(step/2). The law metric
  (symmetric min vertex-vertex) reads an UNSIGNED distance between sample points: a reading
  g < step/2 places the realizing samples closer than the surfaces' own localization — no such
  configuration can be CERTIFIED as not-through; the shells meet or cross inside the uncertainty
  band of the surface itself. A SEAT is certified only inside the band: within the touching class
  AND not through beyond the mesh's own localization. **Interpenetration beyond the tolerance
  (readings below tol_ip) is NOT a seat.**
- HONEST LIMIT, NAMED: between 0.08 mm and the decimation band ε (the median edges
  0.310857620079/0.302305969593 mm) the unsigned vertex metric cannot further separate through from
  near on this mesh class. The two arms' realized minima STRADDLE tol_ip (null 0.046718998681 below
  it; real 0.098475213606 above it) — the band carries the through-exclusion; the arms'
  discrimination is carried by LEG 2. A higher lower edge (the 0.16 mm step, or ε) would REFUSE the
  real arm's measured flexion-endpoint seats 0.098475213606/0.160824534903 — impingement-class
  proximity readings taken with the head CENTERED (displacement 0.0 exactly) — so no looser bound
  was available without tuning to the real arm's numbers; tol_ip is derived from the definition's
  committed resolution alone, before this lane measured anything.

### 2.3 LEG 2 — the head-center displacement band: ‖pose(c*) − c*‖ ≤ band_h = rms_residual_h

The registered fit's sphere (c*, r = 3.044128510081186 / 2.682250273052935 mm, RMS residual
η = 0.155477725893212 / 0.147474758014234 mm) IS the measured socket conjugate: the head was
scanned SEATED at the recorded law gap (1.44/1.49 mm), so c* is the seat center the cup wall was
measured against, and the pivot's measured radius+residual ARE the socket's geometry. The fit
localizes that center to its own residual scale η (the inlier surface pins the center to ~η; the
same no-margin discipline as the inlier band ε — and η lands at the sampling half-step class ε/2,
within 0.03% hip 02 and 2.4% hip 03: consistency, not input). The head is SEATED iff its center
stays at c* within the fit's own localization band:

- band_02 = 0.155477725893 mm, band_03 = 0.147474758014 mm (12-dp recorded; compared at full
  precision in the battery).

**A displacement beyond the band is a DISLOCATION**: the head-sphere has left the seat by more than
the measurement that recorded the seat can localize. No multiplier, no margin, nothing chosen.

### 2.4 THE PREDICATE P6′ and the range coverage

- An arm (real: fitted centers/axis; null: recorded midpoints/registered control axis) at hip h is
  SEATED at θ iff BOTH: (i) tol_ip ≤ g(θ) ≤ cut, and (ii) d(θ) = ‖pose(c*) − c*‖ ≤ band_h.
- The arm PASSES P6′ iff both clauses hold at EVERY θ of the closed cited range [−R, +R]
  (R = 2.0943950999999998 rad, parsed from the committed gait2392 record, sha
  `18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019`).
- RANGE COVERAGE (derived, no new numbers): the battery measures the derived grid
  {−R} ∪ {R·k/5 : k = −4..4} ∪ {+R} — the endpoints exact, the interior at the prior lane's
  REGISTERED probe fraction R/5 (its §5 sign probe), 11 poses per arm per hip. LEG 2 is additionally
  covered on the whole closed range analytically: real arm d ≡ 0 for every θ (a rotation about an
  axis through c* fixes c* — identity, float-exact); null arm d(θ) = 2·|c⊥|·sin(|θ|/2) is monotone
  in |θ| on [0, R] ⊂ [0, π], so the measured endpoints dominate the range. LEG 1 is carried by the
  grid (the gap map is continuous in θ; the endpoints are the committed extremes).
- The flexion sign s (curl-ward, the registered rule on the chain contacts pose.joint_01_15/17) is
  recomputed for labeling only; the grid is sign-symmetric.

### 2.5 The derived numbers, fixed before banking

tol_ip = 0.08 mm; cut = 3.0 mm; band_02 = 0.155477725893 mm; band_03 = 0.147474758014 mm;
R = 2.0943950999999998 rad; grid step R/5 = 0.41887901999999996 rad. REPRODUCTION GUARDS: this
lane re-derives the fits by the registered rule and requires exact equality with the committed
battery.json records at the recorded rounding (centers [58.481285783297, 40.201005541148,
43.245619125234] / [57.206718169476, 41.501776979145, 22.591386466803]; radii
3.044128510081/2.682250273053; RMS 0.155477725893/0.147474758014; inliers 599/533; median edges
0.310857620079/0.302305969593). Any drift = the lane is not running the registered derivation = VOID.

## 3. PREDICTIONS (both arms, banked BEFORE the re-run)

- **REAL ARM PASSES P6′ on both hips.** d == 0.0 EXACTLY (float equality) at every grid θ, both
  hips. Every grid seat reading inside the band [0.08, 3.0] mm. The three committed θ reproduce the
  committed readings exactly: hip 02 rest 1.438430430193 / hi 0.098475213606 / lo 0.861959512899;
  hip 03 rest 1.486366553653 / hi 0.160824534903 / lo 0.887240079415; the demo magnitude (R/5,
  in-grid) reproduces 2.14303796227/1.650134761681. Expected (soft tick, not load-bearing): the
  grid minima land at the flexion endpoints 0.098475213606/0.160824534903. Load-bearing margin:
  real-min/tol_ip = 0.098475213606/0.08 = 1.231.
- **NULL ARM FAILS P6′ on both hips.** The displacement band catches the excursions:
  d(±R) = 5.745805839276 mm (hip 02; 36.96× band_02) and 3.945980865254 mm (hip 03; 26.76×
  band_03), reproducing 2·|c⊥|·sin(|θ|/2) to ≤ 1e-9 mm at EVERY grid θ; d = 0 at rest. Hip 03
  ADDITIONALLY breaches the seat band at +R: 0.046718998681 < 0.08 (0.584× tol_ip). Hip 02's
  endpoint seats 0.209308648732/0.08843746898 sit above tol_ip (its FAIL is carried by the
  displacement band); its interior grid seats are recorded whichever way they land (L4-honest —
  the null arm's failure does not depend on them).
- **THE DISCRIMINATION** (the lane's headline falsifier): real PASS ∧ null FAIL per hip, on the
  corrected predicate. If the real arm fails any clause, or the null arm passes both clauses on
  either hip, the amendment FAILS and the design REMAINS VOID.
- **A1–A6 replica (re-verification, unchanged):** the committed battery script executed byte-
  identically from this lane's `replica/` directory: `hard_checks_pass` TRUE and EVERY recorded
  field equal to the committed battery.json (sha `18f0ef06...`) except EXACTLY ONE field —
  `preregistration_sha256`, which records THIS lane's banked preregistration. A1 rest identity,
  A2 seat, A3 cure at exactly cure·A, A4 bitwise mass, A5 named refusals, A6 untouched: all green,
  unchanged.
- **Determinism:** every battery's double run byte-identical (sorted keys, fixed rounding,
  timestamp-free).
- **Kernel gates:** `test_definition` 9/9, `test_glue` 8/8, `training_gate` PASS — unchanged.

## 4. THE BATTERY (protocol, fixed here)

- `p6_contrast.py`: imports the committed `hip_pivot_proof.py` module's registered primitives
  (inlier rule, Rodrigues, law metric, patch estimator) — ZERO re-derivation of the fit rule
  (F4 discipline). Re-derives fits/axis/sign/control constructions; verifies the reproduction
  guards (§2.5); evaluates P6′ on both arms on the grid; checks the banked predictions; records
  bands, margins, provenance; watched sha256s before == after (the committed definition, bins,
  osim, the three prior lanes' receipts, the prior lane's preregistration+amendments+battery.json,
  THIS preregistration, the amended law doc).
- `replica/hip_pivot_proof.py`: the committed script BYTE-IDENTICAL (sha-verified against the
  committed blob), run from `replica/` with THIS lane's preregistration.md beside it; writes
  `replica/battery.json`; diffed against the committed battery.json field-by-field.
- Determinism: each battery run TWICE; outputs byte-equal (L1).
- Gates: the repo's own, run unchanged (§3).

## 5. THIS LANE'S FALSIFIERS (named before the run)

- **L1 determinism:** any double-run byte drift in either battery → the lane is not
  checkout-invariant → VOID.
- **L2 identity/untouched:** any watched sha256 changes during a run → VOID (the committed
  skeleton and every prior receipt are read-only).
- **L3 gates:** any kernel gate red → VOID.
- **L4 honest arms:** both arms run exactly on the registered constructions (real: fitted centers
  and bilateral axis; null: recorded midpoints and the registered control axis), verdicts recorded
  whichever way they land; suppressing or retuning either arm is VOID by definition.
- **L5 the discrimination (headline):** the corrected predicate must PASS the real arm and FAIL
  the null arm on BOTH hips — else the amendment fails, the design REMAINS VOID AS WRITTEN, and
  this lane's receipt says so with the numbers.
- **L6 tolerance honesty:** if the REAL arm's seat readings fall below tol_ip anywhere on the
  grid, the half-voxel derivation is mis-derived → the amendment voids (banked margin: the real
  minimum clears tol_ip by 1.231×).

Trailer: Agent: GLM 5.3
